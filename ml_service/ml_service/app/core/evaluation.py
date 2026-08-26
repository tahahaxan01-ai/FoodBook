"""
Model Evaluation: Precision@K, Recall@K, NDCG@K.

Set this up EARLY, before you tune the recommender further — otherwise you're
just guessing whether changes help. You need a held-out set of
(user, restaurants_they_actually_liked) pairs to evaluate against; this can
start as a manually curated test set of ~20-30 users before you have enough
real interaction data.
"""
import math


def precision_at_k(recommended: list[str], relevant: set[str], k: int) -> float:
    top_k = recommended[:k]
    if not top_k:
        return 0.0
    hits = sum(1 for r in top_k if r in relevant)
    return hits / len(top_k)


def recall_at_k(recommended: list[str], relevant: set[str], k: int) -> float:
    if not relevant:
        return 0.0
    top_k = recommended[:k]
    hits = sum(1 for r in top_k if r in relevant)
    return hits / len(relevant)


def dcg_at_k(recommended: list[str], relevant: set[str], k: int) -> float:
    dcg = 0.0
    for i, item in enumerate(recommended[:k]):
        rel = 1.0 if item in relevant else 0.0
        dcg += rel / math.log2(i + 2)  # +2 because rank i starts at 0
    return dcg


def ndcg_at_k(recommended: list[str], relevant: set[str], k: int) -> float:
    dcg = dcg_at_k(recommended, relevant, k)
    ideal_recommended = list(relevant)[:k]
    idcg = dcg_at_k(ideal_recommended, relevant, k)
    if idcg == 0:
        return 0.0
    return dcg / idcg


def evaluate_recommendations(
    all_recommendations: dict[str, list[str]],   # user_id -> ranked restaurant_ids
    all_relevant: dict[str, set[str]],            # user_id -> ground-truth liked restaurants
    k: int = 10,
) -> dict[str, float]:
    """Average Precision@K / Recall@K / NDCG@K across all evaluated users."""
    precisions, recalls, ndcgs = [], [], []

    for user_id, recommended in all_recommendations.items():
        relevant = all_relevant.get(user_id, set())
        if not relevant:
            continue
        precisions.append(precision_at_k(recommended, relevant, k))
        recalls.append(recall_at_k(recommended, relevant, k))
        ndcgs.append(ndcg_at_k(recommended, relevant, k))

    n = len(precisions) or 1
    return {
        "precision_at_k": round(sum(precisions) / n, 4),
        "recall_at_k": round(sum(recalls) / n, 4),
        "ndcg_at_k": round(sum(ndcgs) / n, 4),
        "num_users_evaluated": len(precisions),
        "k": k,
    }
