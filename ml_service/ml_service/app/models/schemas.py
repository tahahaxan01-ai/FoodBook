"""
Pydantic schemas shared across the ml_service.
These define the contracts between your ML code and the backend/API layer.
"""
from typing import Optional
from pydantic import BaseModel, Field


class Review(BaseModel):
    review_id: str
    user_id: str
    restaurant_id: str
    text: str
    rating: Optional[float] = None  # overall star rating if given


class AspectSentiment(BaseModel):
    aspect: str
    sentiment: str  # "positive" | "negative" | "neutral"
    score: float    # -1.0 .. 1.0
    evidence: str    # the snippet of text that triggered this


class ReviewAnalysis(BaseModel):
    review_id: str
    overall_sentiment: str
    aspects: list[AspectSentiment]


class Restaurant(BaseModel):
    restaurant_id: str
    name: str
    cuisine: list[str] = Field(default_factory=list)
    price_band: int = 2          # 1=cheap .. 4=expensive
    avg_spice_level: float = 0.5  # 0..1
    tags: list[str] = Field(default_factory=list)   # e.g. ["cheesy","bbq","family"]
    lat: Optional[float] = None
    lon: Optional[float] = None


class UserInteraction(BaseModel):
    user_id: str
    restaurant_id: str
    rating: Optional[float] = None
    liked: bool = False
    saved: bool = False
    aspect_scores: dict[str, float] = Field(default_factory=dict)


class TasteProfile(BaseModel):
    user_id: str
    cuisine_weights: dict[str, float] = Field(default_factory=dict)
    aspect_weights: dict[str, float] = Field(default_factory=dict)  # taste, spice, cheese, etc.
    price_band_pref: float = 2.0
    tag_weights: dict[str, float] = Field(default_factory=dict)


class RecommendationRequest(BaseModel):
    user_id: str
    top_k: int = 10
    max_budget: Optional[float] = None
    location_bias: Optional[tuple[float, float]] = None


class Recommendation(BaseModel):
    restaurant_id: str
    name: str
    match_score: float           # 0..100, the "92% Taste Match"
    explanation: str
    source: str                  # "content" | "collaborative" | "hybrid"


class SearchQueryParsed(BaseModel):
    cuisine: Optional[str] = None
    max_budget: Optional[float] = None
    spice_level: Optional[str] = None   # "low"|"medium"|"high"
    location: Optional[str] = None
    dine_mode: Optional[str] = None     # "dine-in"|"takeaway"|"delivery"
    raw_query: str = ""
