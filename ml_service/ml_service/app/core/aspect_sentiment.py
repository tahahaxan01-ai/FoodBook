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
