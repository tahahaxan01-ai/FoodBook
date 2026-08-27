"""
Taste Profile + Taste Extraction

Core idea: a user's taste profile is a weighted vector over three spaces:
  1. cuisine_weights   -> which cuisines they gravitate to
  2. aspect_weights     -> which review aspects they care about / rate highly
                           (taste, spice, cheese, crust, portion, service, ambiance, value)
  3. tag_weights         -> free-form tags pulled from restaurants they liked

We build this from UserInteraction history + ReviewAnalysis output (aspect sentiment).
No training required for v1 — this is a transparent, explainable weighted-average model,
which is exactly what you want early (v1 must be explainable to support the
"Recommended because you liked X" feature).
"""
from collections import defaultdict
from app.models.schemas import (
    TasteProfile, UserInteraction, Restaurant, ReviewAnalysis, Review
)

ASPECT_KEYS = [
    "taste", "spice", "cheese", "crust", "portion",
    "presentation", "service", "ambiance", "value",
]


def build_taste_profile(
    user_id: str,
    interactions: list[UserInteraction],
    restaurants_by_id: dict[str, Restaurant],
    review_analyses: list[ReviewAnalysis] | None = None,
) -> TasteProfile:
    """
    Aggregate a user's interaction + review history into a TasteProfile.

    interactions: rows of (user, restaurant, rating/liked/saved/aspect_scores)
    restaurants_by_id: lookup so we can pull cuisine/tags/price for liked restaurants
    review_analyses: optional NLP output (see nlp/aspect_sentiment.py) to enrich
                      aspect_weights beyond explicit star ratings
    """
    cuisine_weights: dict[str, float] = defaultdict(float)
    tag_weights: dict[str, float] = defaultdict(float)
    aspect_weights: dict[str, float] = defaultdict(float)
    price_samples: list[float] = []
    total_weight = 0.0

    for inter in interactions:
        if inter.user_id != user_id:
            continue

        restaurant = restaurants_by_id.get(inter.restaurant_id)
        if restaurant is None:
            continue

        # signal strength: explicit rating > like > save > mere view
        signal = 0.0
        if inter.rating is not None:
            # normalize a 1-5 rating to a -1..1 signal (3 = neutral)
            signal += (inter.rating - 3) / 2
        if inter.liked:
            signal += 1.0
        if inter.saved:
            signal += 0.5

        if signal <= 0:
            # don't let disliked restaurants pull the profile toward them;
            # negative signal is handled separately (e.g. down-weighting) in v2
            continue

        total_weight += signal
        price_samples.append(restaurant.price_band)

        for cuisine in restaurant.cuisine:
            cuisine_weights[cuisine] += signal
        for tag in restaurant.tags:
            tag_weights[tag] += signal

        for aspect, score in inter.aspect_scores.items():
            aspect_weights[aspect] += score * signal

    # fold in NLP-derived aspect sentiment (from written reviews) if provided
    if review_analyses:
        for analysis in review_analyses:
            for a in analysis.aspects:
                aspect_weights[a.aspect] += a.score

    # normalize everything to sum to 1 within each group (so weights are comparable %s)
    def _normalize(d: dict[str, float]) -> dict[str, float]:
        total = sum(abs(v) for v in d.values())
        if total == 0:
            return dict(d)
        return {k: round(v / total, 4) for k, v in d.items()}

    price_pref = sum(price_samples) / len(price_samples) if price_samples else 2.0

    return TasteProfile(
        user_id=user_id,
        cuisine_weights=_normalize(cuisine_weights),
        aspect_weights=_normalize(aspect_weights),
        tag_weights=_normalize(tag_weights),
        price_band_pref=round(price_pref, 2),
    )
