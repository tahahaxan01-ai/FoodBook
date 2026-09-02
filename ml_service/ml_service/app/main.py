"""
FastAPI entrypoint for the ml_service microservice.

Run locally:
    uvicorn app.main:app --reload --port 8001

This is intentionally a thin layer: all real logic lives in app/core/*.
Storage is in-memory (dicts) for now — swap _DB for real DB calls once the
`database` service/schema is ready; the function signatures in core/ already
take plain data structures so that swap won't require touching core logic.
"""
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from app.models.schemas import (
    Review, Restaurant, UserInteraction, RecommendationRequest,
    Recommendation, SearchQueryParsed, TasteProfile,
)
from app.core.aspect_sentiment import analyze_review, extract_taste_vector_and_aspects
from app.core.taste_profile import build_taste_profile
from app.core.recommender import recommend
from app.core.search_ai import parse_query_rule_based
from app.core.evaluation import evaluate_recommendations
from app.core.database import db
from app.core.vector_recommender import recommend_from_database

app = FastAPI(title="FoodBook ML Service", version="0.1.0")

# --- in-memory demo store (replace with real DB access) ---
_restaurants: dict[str, Restaurant] = {}
_interactions: list[UserInteraction] = []
_reviews: list[Review] = []


@app.post("/restaurants")
def add_restaurant(restaurant: Restaurant):
    _restaurants[restaurant.restaurant_id] = restaurant
    return {"status": "ok"}


@app.post("/interactions")
def add_interaction(interaction: UserInteraction):
    _interactions.append(interaction)
    return {"status": "ok"}


@app.post("/reviews/analyze")
def analyze(review: Review):
    """NLP + Aspect-Based Sentiment endpoint."""
    return analyze_review(review)


@app.get("/users/{user_id}/taste-profile", response_model=TasteProfile)
def get_taste_profile(user_id: str):
    return build_taste_profile(user_id, _interactions, _restaurants)


@app.post("/recommendations", response_model=list[Recommendation])
def get_recommendations(req: RecommendationRequest):
    profile = build_taste_profile(req.user_id, _interactions, _restaurants)
    if not profile.cuisine_weights and not profile.tag_weights:
        raise HTTPException(
            status_code=404,
            detail="No taste signal yet for this user — need at least one rating/like/save.",
        )
    return recommend(
        profile=profile,
        restaurants=list(_restaurants.values()),
        interactions=_interactions,
        top_k=req.top_k,
        max_budget=req.max_budget,
    )


@app.get("/search/parse", response_model=SearchQueryParsed)
def parse_search(q: str):
    """Conversational Search AI endpoint — rule-based v1."""
    return parse_query_rule_based(q)


@app.post("/evaluate")
def evaluate(recommendations: dict[str, list[str]], relevant: dict[str, list[str]], k: int = 10):
    relevant_sets = {u: set(r) for u, r in relevant.items()}
    return evaluate_recommendations(recommendations, relevant_sets, k=k)


# --- Real, database-backed endpoints consumed by the FoodBook backend ---
# (the endpoints above operate on the in-memory demo store; these read
# live data straight from Supabase and are what production traffic hits)

class DbRecommendationRequest(BaseModel):
    user_id: Optional[str] = None
    taste_vector: Optional[List[float]] = None
    preferred_cuisines: Optional[List[str]] = Field(default_factory=list)
    dietary_restrictions: Optional[List[str]] = Field(default_factory=list)
    max_budget: Optional[float] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    radius_meters: Optional[int] = 15000
    limit: Optional[int] = 10


@app.post("/recommend")
async def recommend_live(req: DbRecommendationRequest):
    """
    Hybrid content + collaborative-filtering recommendations computed
    live against Supabase. This is the endpoint the FoodBook backend calls;
    it degrades gracefully (empty list) if no database is configured so the
    backend's built-in fallback can still take over.
    """
    if not db.is_connected:
        return {"user_id": req.user_id, "total_recommendations": 0, "recommendations": [], "model_version": "unavailable"}

    vector = req.taste_vector if req.taste_vector and len(req.taste_vector) == 9 else [0.5] * 9
    return await recommend_from_database(
        taste_vector=vector,
        preferred_cuisines=req.preferred_cuisines or [],
        max_budget=req.max_budget,
        latitude=req.latitude,
        longitude=req.longitude,
        radius_meters=req.radius_meters or 15000,
        limit=req.limit or 10,
        user_id=req.user_id,
    )


class ExtractAspectsRequest(BaseModel):
    text: str


@app.post("/extract-aspects")
def extract_aspects(req: ExtractAspectsRequest):
    """
    NLP aspect + 9D taste-vector extraction from free-text review content.
    Consumed by the backend when a review is submitted with review_text.
    """
    aspects, vector = extract_taste_vector_and_aspects(req.text or "")
    return {"aspects": aspects, "taste_vector": vector}


class ParseSearchRequest(BaseModel):
    query: str


@app.post("/search/parse-query")
def parse_search_query(req: ParseSearchRequest):
    """Same conversational parser as GET /search/parse, as a POST for the backend to call."""
    return parse_query_rule_based(req.query)
