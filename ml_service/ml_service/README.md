# FoodBook ML Service

Implements Sheharyar's assigned tasks: Taste Profile, Taste Extraction, NLP,
Aspect-Based Sentiment, Restaurant Similarity, Recommendation Engine,
Collaborative Filtering, Hybrid Recommendation, Match Score, Explainability,
Conversational Search AI, and Model Evaluation.

## Status: working v1 (tested), not v2

Everything here runs and is tested (`pytest tests/ -v` → 6/6 passing) using
transparent, explainable heuristics instead of trained models. This is a
deliberate MVP choice — see "Upgrade path" below.

## Structure
```
app/
  models/schemas.py       # shared data contracts (Restaurant, TasteProfile, etc.)
  core/
    taste_profile.py      # Taste Profile + Taste Extraction
    aspect_sentiment.py   # NLP + Aspect-Based Sentiment
    recommender.py        # Restaurant Similarity, Rec Engine, Collaborative
                           #   Filtering, Hybrid, Match Score, Explainability
    search_ai.py           # Conversational Search AI (rule-based + LLM-ready)
    evaluation.py          # Precision@K, Recall@K, NDCG@K
  main.py                 # FastAPI endpoints wiring it all together
tests/test_pipeline.py    # end-to-end smoke tests
```

## Run it
```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
pytest tests/ -v
```

## What's real vs. stubbed

| Component | v1 approach | Why |
|---|---|---|
| Taste Profile | weighted average over interactions | fully explainable, no cold-start training needed |
| Aspect Sentiment | lexicon + clause splitting | zero-dependency, runs anywhere, good enough to demo |
| Restaurant Similarity | cosine similarity over cuisine/tag vectors | standard content-based approach, cheap to compute |
| Collaborative Filtering | user-based CF over shared ratings | correct approach, but **needs real interaction volume** — expect it to return little/nothing until you have enough users rating things |
| Hybrid | weighted blend, defaults to 70% content / 30% CF | protects against CF's cold-start weakness early on |
| Conversational Search | regex/keyword extraction, with an LLM-based function ready to swap in | rule-based ships today; LLM version in `search_ai.parse_query_llm()` needs only a `call_llm` function passed in |
| Model Evaluation | Precision@K / Recall@K / NDCG@K, pure functions | set this up now so future model changes are measured, not guessed |

## Upgrade path (v2, once you have real data)
- Swap `parse_query_rule_based` → `parse_query_llm` in `main.py` once an LLM
  API key is wired up.
- Replace lexicon-based sentiment with a trained/pretrained ABSA model —
  interface (`analyze_review(review) -> ReviewAnalysis`) stays the same.
- Once you have enough interaction data, lower `content_weight` in
  `hybrid_scores()` so collaborative filtering carries more weight.
- Build a labeled eval set (which restaurants each test user actually liked)
  and run `evaluate_recommendations()` before/after any model change.
