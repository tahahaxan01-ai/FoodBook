"""
Conversational Search AI

Converts a free-text query like:
  "I want spicy cheesy pizza under Rs. 1500 near Johar Town"
into a SearchQueryParsed struct the recommendation/filter layer can consume.

Two implementations are provided behind the same interface:
  - parse_query_rule_based(): zero-dependency regex/keyword extraction. Good
    enough for demoing the feature today and for a fallback when no LLM key
    is configured.
  - parse_query_llm(): calls an LLM with a strict JSON-only prompt for much
    better recall on messy phrasing. This is the one to use in production —
    swap it in by pointing the API layer at this function instead once you
    wire up an API key.

Both return the same schema, so the rest of the app never needs to know
which one is active.
"""
import re
import json
from app.models.schemas import SearchQueryParsed

CUISINES = ["pizza", "pakistani", "chinese", "italian", "bbq", "fast food",
            "desi", "continental", "biryani", "burger", "sushi", "thai"]

SPICE_HIGH = ["spicy", "hot", "extra spicy"]
SPICE_LOW = ["mild", "not spicy", "less spicy"]

DINE_MODES = {
    "dine-in": ["dine in", "dine-in", "sit down", "eat in"],
    "takeaway": ["takeaway", "take away", "pickup", "to go"],
    "delivery": ["delivery", "deliver", "order online"],
}


def parse_query_rule_based(query: str) -> SearchQueryParsed:
    lower = query.lower()

    cuisine = next((c for c in CUISINES if c in lower), None)

    budget_match = re.search(r"(?:rs\.?|pkr|under|below)\s*[:\-]?\s*(\d{2,6})", lower)
    max_budget = float(budget_match.group(1)) if budget_match else None

    spice_level = None
    if any(w in lower for w in SPICE_HIGH):
        spice_level = "high"
    elif any(w in lower for w in SPICE_LOW):
        spice_level = "low"

    dine_mode = None
    for mode, keywords in DINE_MODES.items():
        if any(kw in lower for kw in keywords):
            dine_mode = mode
            break

    location_match = re.search(r"(?:near|in|around)\s+([a-zA-Z\s]+?)(?:$|,|\.|under|for)", lower)
    location = location_match.group(1).strip().title() if location_match else None

    return SearchQueryParsed(
        cuisine=cuisine,
        max_budget=max_budget,
        spice_level=spice_level,
        location=location,
        dine_mode=dine_mode,
        raw_query=query,
    )


LLM_SYSTEM_PROMPT = """You convert a food-search query into JSON only, no prose.
Schema:
{
  "cuisine": string|null,
  "max_budget": number|null,
  "spice_level": "low"|"medium"|"high"|null,
  "location": string|null,
  "dine_mode": "dine-in"|"takeaway"|"delivery"|null
}
Return ONLY the JSON object, nothing else."""


def parse_query_llm(query: str, call_llm) -> SearchQueryParsed:
    """
    call_llm: a function (system_prompt: str, user_prompt: str) -> str
    Pass in your Anthropic/OpenAI client wrapper here. Kept generic so this
    module has no hard dependency on a specific SDK.
    """
    raw = call_llm(LLM_SYSTEM_PROMPT, query)
    try:
        cleaned = raw.strip().strip("`").replace("json\n", "", 1)
        data = json.loads(cleaned)
    except (json.JSONDecodeError, AttributeError):
        # graceful fallback so a flaky LLM call never breaks search entirely
        return parse_query_rule_based(query)

    return SearchQueryParsed(
        cuisine=data.get("cuisine"),
        max_budget=data.get("max_budget"),
        spice_level=data.get("spice_level"),
        location=data.get("location"),
        dine_mode=data.get("dine_mode"),
        raw_query=query,
    )
