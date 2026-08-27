"""
FastAPI entrypoint for the ml_service microservice.

Run locally:
    uvicorn app.main:app --reload --port 8001

This is intentionally a thin layer: all real logic lives in app/core/*.
Storage is in-memory (dicts) for now — swap _DB for real DB calls once the
`database` service/schema is ready; the function signatures in core/ already
take plain data structures so that swap won't require touching core logic.
"""
from fastapi import FastAPI, HTTPException
from app.models.schemas import (
    Review, Restaurant, UserInteraction, RecommendationRequest,
    Recommendation, SearchQueryParsed, TasteProfile,
)
from app.core.aspect_sentiment import analyze_review
from app.core.taste_profile import build_taste_profile
from app.core.recommender import recommend
from app.core.search_ai import parse_query_rule_based
from app.core.evaluation import evaluate_recommendations

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
