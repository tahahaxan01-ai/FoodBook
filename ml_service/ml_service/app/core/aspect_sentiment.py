"""
NLP + Aspect-Based Sentiment Analysis

v1 approach: lexicon + dependency-free rule matching. This is deliberately NOT a
trained transformer model yet — for an MVP you want something that:
  - runs with zero GPU / model download requirements
  - is fully explainable (you can show *why* it tagged a sentence negative)
  - is easy to demo today

Upgrade path (v2, once you have labeled review data):
  - Fine-tune / use a pretrained ABSA model (e.g. a DeBERTa or BERT ABSA checkpoint)
  - Or call an LLM with a structured-output prompt (fast to build, costs per-call)
  Both slot into the same `analyze_review()` interface below, so swapping the
  implementation later doesn't require touching callers.
"""
import re
from app.models.schemas import Review, ReviewAnalysis, AspectSentiment

# aspect -> keywords that indicate the sentence is *about* this aspect
ASPECT_KEYWORDS = {
    "taste": ["taste", "tasty", "flavor", "flavour", "delicious", "bland"],
    "spice": ["spicy", "spice", "hot", "mild"],
    "cheese": ["cheese", "cheesy"],
    "crust": ["crust", "base", "dough"],
    "portion": ["portion", "size", "quantity", "small", "large", "big"],
    "presentation": ["presentation", "look", "plating", "appearance"],
    "service": ["service", "staff", "waiter", "waitress", "delivery time", "server"],
    "ambiance": ["ambiance", "ambience", "vibe", "atmosphere", "seating", "decor"],
    "value": ["price", "value", "worth", "expensive", "cheap", "overpriced"],
}

POSITIVE_WORDS = {
    "delicious", "great", "amazing", "good", "excellent", "loved", "love",
    "fresh", "perfect", "friendly", "fast", "generous", "tasty", "awesome",
    "best", "nice", "warm", "crispy",
}
NEGATIVE_WORDS = {
    "oily", "bland", "cold", "slow", "rude", "bad", "terrible", "worst",
    "small", "overpriced", "expensive", "soggy", "burnt", "stale", "poor",
    "disappointing", "dry",
}
NEGATIONS = {"not", "n't", "no", "never", "isn't", "wasn't", "didn't"}


def _split_clauses(text: str) -> list[str]:
    # split on common contrast/clause boundaries so "delicious but too oily"
    # becomes two separately-scored clauses
    parts = re.split(r"[.!?]|,\s*but\b|\bbut\b|\band\b|;", text, flags=re.IGNORECASE)
    return [p.strip() for p in parts if p.strip()]


def _score_clause(clause: str) -> float:
    words = re.findall(r"[a-zA-Z']+", clause.lower())
    score = 0.0
    negate = False
    for w in words:
        if w in NEGATIONS:
            negate = True
            continue
        if w in POSITIVE_WORDS:
            score += -1.0 if negate else 1.0
        elif w in NEGATIVE_WORDS:
            score += 1.0 if negate else -1.0
        negate = False
    # squash to -1..1
    if score > 0:
        return min(1.0, score / 2)
    if score < 0:
        return max(-1.0, score / 2)
    return 0.0


# aspect (from ASPECT_KEYWORDS above) -> 9D taste-vector index it informs.
# Only aspects with a direct taste meaning map here; portion/presentation/
# service/ambiance/value are about the experience, not flavor, so they stay
# out of the taste vector on purpose.
ASPECT_TO_TASTE_DIM = {
    "spice": 0,   # spicy
    "cheese": 6,  # creamy
    "crust": 7,   # crispy
}

# Straightforward keyword hits for the taste dimensions aspect-clauses don't
# cover (sweet, salty, sour, umami, smoky, rich) — same idea as ASPECT_KEYWORDS
# above, just indexed straight onto the 9D vector.
TASTE_DIM_KEYWORDS = {
    1: ["sweet", "sugary", "syrupy"],           # sweet
    2: ["salty", "salted"],                      # salty
    3: ["sour", "tangy", "citrusy", "vinegary"],  # sour
    4: ["umami", "savory", "savoury", "broth", "meaty"],  # umami
    5: ["smoky", "smokey", "charcoal", "charred", "bbq"],  # smoky
    8: ["rich", "heavy", "indulgent", "buttery"],  # rich
}


def extract_taste_vector_and_aspects(text: str) -> tuple[dict[str, str], list[float]]:
    """
    Turn free-text review text into a 9D taste vector + a simple aspect
    label map, for review creation and AI search query parsing to reuse.

    Builds on `analyze_review`'s clause-level sentiment (so "not very spicy"
    correctly pulls spice DOWN, not up) and layers in direct keyword hits
    for the taste dimensions that aren't one of the ASPECT_KEYWORDS aspects.
    """
    vector = [0.5] * 9
    aspects: dict[str, str] = {}

    analysis = analyze_review(Review(review_id="adhoc", user_id="adhoc", restaurant_id="adhoc", text=text))
    for a in analysis.aspects:
        dim = ASPECT_TO_TASTE_DIM.get(a.aspect)
        if dim is not None:
            # sentiment score is -1..1; map onto 0..1 around a 0.5 baseline
            vector[dim] = round(max(0.0, min(1.0, 0.5 + a.score * 0.5)), 2)
        aspects[a.aspect] = a.sentiment

    lower = text.lower()
    for dim, keywords in TASTE_DIM_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            vector[dim] = 0.8

    return aspects, vector


def analyze_review(review: Review) -> ReviewAnalysis:
    clauses = _split_clauses(review.text)
    aspects: list[AspectSentiment] = []

    for clause in clauses:
        lower = clause.lower()
        matched_aspects = [
            aspect for aspect, kws in ASPECT_KEYWORDS.items()
            if any(kw in lower for kw in kws)
        ]
        if not matched_aspects:
            continue
        score = _score_clause(clause)
        sentiment = "positive" if score > 0.15 else "negative" if score < -0.15 else "neutral"
        for aspect in matched_aspects:
            aspects.append(AspectSentiment(
                aspect=aspect,
                sentiment=sentiment,
                score=round(score, 3),
                evidence=clause,
            ))

    if aspects:
        overall_score = sum(a.score for a in aspects) / len(aspects)
    elif review.rating is not None:
        overall_score = (review.rating - 3) / 2
    else:
        overall_score = 0.0

    overall = "positive" if overall_score > 0.15 else "negative" if overall_score < -0.15 else "neutral"

    return ReviewAnalysis(
        review_id=review.review_id,
        overall_sentiment=overall,
        aspects=aspects,
    )
