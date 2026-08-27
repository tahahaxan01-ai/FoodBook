"""
FoodBook OpenStreetMap (OSM) Overpass API Data Seeder
=====================================================
Fetches real-world restaurant entities for cities like Lahore via Overpass API:
- Extracts names, cuisines, address fields, and city metadata.
- Extracts latitude & longitude geo-coordinates.
- Formats PostGIS GEOGRAPHY(POINT, 4326) objects.
- Populates 'restaurants', 'restaurant_branches', and initial 'menu_categories' / 'menu_items'.
- Tests and verifies the 'get_nearby_restaurants' PostGIS RPC function.
"""

import sys
import os
import re
import json
import asyncio
import httpx
import logging
from typing import List, Dict, Any, Optional

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))

from app.core.config import settings
from app.core.database import db

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("foodbook.osm_seeder")

OVERPASS_SERVERS = [
    "https://overpass-api.de/api/interpreter",
    "https://lz4.overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter"
]

# Cuisine and taste vector heuristics
CUISINE_TASTE_PROFILES = {
    "pakistani": [0.80, 0.15, 0.75, 0.30, 0.85, 0.70, 0.40, 0.60, 0.85],
    "bbq": [0.75, 0.20, 0.80, 0.25, 0.90, 0.90, 0.35, 0.70, 0.80],
    "pizza": [0.60, 0.25, 0.70, 0.35, 0.75, 0.30, 0.90, 0.65, 0.80],
    "fast food": [0.65, 0.30, 0.75, 0.25, 0.75, 0.30, 0.80, 0.85, 0.75],
    "burger": [0.60, 0.30, 0.75, 0.30, 0.80, 0.45, 0.80, 0.80, 0.80],
    "chinese": [0.65, 0.40, 0.70, 0.60, 0.85, 0.25, 0.35, 0.70, 0.65],
    "cafe": [0.20, 0.70, 0.30, 0.30, 0.50, 0.30, 0.80, 0.60, 0.70],
    "italian": [0.45, 0.30, 0.65, 0.40, 0.80, 0.25, 0.85, 0.55, 0.75],
    "desi": [0.85, 0.15, 0.80, 0.30, 0.90, 0.75, 0.45, 0.60, 0.90],
    "default": [0.55, 0.40, 0.60, 0.35, 0.65, 0.40, 0.60, 0.60, 0.65]
}


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    text = re.sub(r"^-+|-+$", "", text)
    return text


def map_osm_cuisine(tags: Dict[str, Any]) -> List[str]:
    cuisines = set()
    raw_cuisine = tags.get("cuisine", "").lower()
    amenity = tags.get("amenity", "").lower()

    if raw_cuisine:
        for c in re.split(r"[,;/_]+", raw_cuisine):
            c_clean = c.strip()
            if c_clean:
                cuisines.add(c_clean.capitalize())

    if amenity == "fast_food":
        cuisines.add("Fast Food")
    elif amenity == "cafe":
        cuisines.add("Cafe")
    elif amenity == "restaurant" and not cuisines:
        cuisines.add("Pakistani")

    # Name-based heuristics for Pakistani brands
    name_lower = tags.get("name", "").lower()
    if "pizza" in name_lower:
        cuisines.add("Pizza")
        cuisines.add("Fast Food")
    if "burger" in name_lower:
        cuisines.add("Burger")
        cuisines.add("Fast Food")
    if "bbq" in name_lower or "tikka" in name_lower or "karahi" in name_lower or "kabab" in name_lower:
        cuisines.add("Pakistani")
        cuisines.add("BBQ")
        cuisines.add("Desi")
    if "coffee" in name_lower or "cafe" in name_lower or "chai" in name_lower:
        cuisines.add("Cafe")

    return list(cuisines) if cuisines else ["Pakistani", "Desi"]


def calculate_taste_vector(cuisines: List[str]) -> List[float]:
    for c in cuisines:
        c_lower = c.lower()
        if c_lower in CUISINE_TASTE_PROFILES:
            return CUISINE_TASTE_PROFILES[c_lower]
    return CUISINE_TASTE_PROFILES["default"]


async def query_overpass_lahore() -> List[Dict[str, Any]]:
    """
    Fetch restaurant, fast_food, and cafe nodes in Lahore bounding box from OSM Overpass API.
    Lahore Bounding Box: min_lat=31.38, min_lon=74.18, max_lat=31.62, max_lon=74.48
    """
    query = """
    [out:json][timeout:25];
    (
      node["amenity"="restaurant"](31.38,74.18,31.62,74.48);
      node["amenity"="fast_food"](31.38,74.18,31.62,74.48);
      node["amenity"="cafe"](31.38,74.18,31.62,74.48);
    );
    out body 40;
    """

    for server in OVERPASS_SERVERS:
        logger.info(f"Querying OpenStreetMap Overpass API server: {server} ...")
        try:
            async with httpx.AsyncClient(timeout=25.0) as client:
                res = await client.post(server, data={"data": query})
                if res.status_code == 200:
                    data = res.json()
                    elements = data.get("elements", [])
                    logger.info(f"Successfully retrieved {len(elements)} OSM nodes from {server}")
                    return elements
        except Exception as e:
            logger.warning(f"Failed to fetch from {server}: {e}")

    logger.warning("Overpass online query failed or timed out. Using high-quality curated Lahore fallback dataset.")
    return get_curated_lahore_osm_dataset()


def get_curated_lahore_osm_dataset() -> List[Dict[str, Any]]:
    """
    Curated dataset of authentic Lahore food landmarks with precise GPS coordinates.
    """
    return [
        {
            "id": 101,
            "lat": 31.5126,
            "lon": 74.3436,
            "tags": {
                "name": "Haveli Restaurant",
                "amenity": "restaurant",
                "cuisine": "pakistani;bbq;mughlai",
                "addr:street": "Fort Road Food Street",
                "addr:city": "Lahore",
                "addr:suburb": "Walled City",
                "phone": "+92 42 37637865"
            }
        },
        {
            "id": 102,
            "lat": 31.5098,
            "lon": 74.3512,
            "tags": {
                "name": "Bundu Khan Restaurant",
                "amenity": "restaurant",
                "cuisine": "pakistani;bbq;desi",
                "addr:street": "Gulberg III",
                "addr:city": "Lahore",
                "addr:suburb": "Gulberg",
                "phone": "+92 42 111444444"
            }
        },
        {
            "id": 103,
            "lat": 31.4697,
            "lon": 74.2728,
            "tags": {
                "name": "Cheezious",
                "amenity": "fast_food",
                "cuisine": "pizza;fast_food;burger",
                "addr:street": "Johar Town, G1 Market",
                "addr:city": "Lahore",
                "addr:suburb": "Johar Town",
                "phone": "+92 42 111446699"
            }
        },
        {
            "id": 104,
            "lat": 31.5142,
            "lon": 74.3485,
            "tags": {
                "name": "Monal Lahore",
                "amenity": "restaurant",
                "cuisine": "pakistani;bbq;continental",
                "addr:street": "Park and Ride Plaza, Liberty Roundabout",
                "addr:city": "Lahore",
                "addr:suburb": "Gulberg",
                "phone": "+92 42 35789988"
            }
        },
        {
            "id": 105,
            "lat": 31.5165,
            "lon": 74.3501,
            "tags": {
                "name": "Cafe Aylanto",
                "amenity": "restaurant",
                "cuisine": "italian;mediterranean;cafe",
                "addr:street": "12 C-1 MM Alam Road",
                "addr:city": "Lahore",
                "addr:suburb": "Gulberg III",
                "phone": "+92 42 35751886"
            }
        },
        {
            "id": 106,
            "lat": 31.4721,
            "lon": 74.2695,
            "tags": {
                "name": "Howdy Johar Town",
                "amenity": "fast_food",
                "cuisine": "burger;fast_food;steaks",
                "addr:street": "PIA Main Boulevard",
                "addr:city": "Lahore",
                "addr:suburb": "Johar Town",
                "phone": "+92 42 111146939"
            }
        },
        {
            "id": 107,
            "lat": 31.5358,
            "lon": 74.3168,
            "tags": {
                "name": "Warid Butt Karahi",
                "amenity": "restaurant",
                "cuisine": "pakistani;desi",
                "addr:street": "Lakshmi Chowk",
                "addr:city": "Lahore",
                "addr:suburb": "Lakshmi Chowk",
                "phone": "+92 42 37234852"
            }
        },
        {
            "id": 108,
            "lat": 31.4820,
            "lon": 74.3030,
            "tags": {
                "name": "Baituti Lebanese Restaurant",
                "amenity": "restaurant",
                "cuisine": "lebanese;mediterranean;middle_eastern",
                "addr:street": "Model Town Link Road",
                "addr:city": "Lahore",
                "addr:suburb": "Model Town",
                "phone": "+92 42 35170099"
            }
        },
        {
            "id": 109,
            "lat": 31.5204,
            "lon": 74.3541,
            "tags": {
                "name": "Salt'n Pepper Village",
                "amenity": "restaurant",
                "cuisine": "pakistani;buffet;desi;bbq",
                "addr:street": "B-3, 103 MM Alam Road",
                "addr:city": "Lahore",
                "addr:suburb": "Gulberg",
                "phone": "+92 42 35750735"
            }
        },
        {
            "id": 110,
            "lat": 31.4789,
            "lon": 74.3721,
            "tags": {
                "name": "Gloria Jean's Coffees DHA",
                "amenity": "cafe",
                "cuisine": "cafe;coffee;bakery;dessert",
                "addr:street": "Y Block Market, Phase 3 DHA",
                "addr:city": "Lahore",
                "addr:suburb": "DHA",
                "phone": "+92 42 35742611"
            }
        },
        {
            "id": 111,
            "lat": 31.4812,
            "lon": 74.3789,
            "tags": {
                "name": "Broadway Pizza DHA",
                "amenity": "fast_food",
                "cuisine": "pizza;fast_food",
                "addr:street": "Commercial Area, Sector Z, Phase 3 DHA",
                "addr:city": "Lahore",
                "addr:suburb": "DHA",
                "phone": "+92 42 111339339"
            }
        },
        {
            "id": 112,
            "lat": 31.5178,
            "lon": 74.3472,
            "tags": {
                "name": "Mandarin Kitchen",
                "amenity": "restaurant",
                "cuisine": "chinese;asian;thai",
                "addr:street": "Building 23-T, MM Alam Road",
                "addr:city": "Lahore",
                "addr:suburb": "Gulberg",
                "phone": "+92 42 35755100"
            }
        }
    ]


async def seed_restaurants_from_osm():
    """
    Main ingestion pipeline:
    1. Query OSM Overpass API.
    2. Extract entities and geo-coordinates.
    3. Construct PostGIS POINT(lng lat) geography objects.
    4. Upsert into Supabase 'restaurants' & 'restaurant_branches'.
    5. Execute PostGIS 'get_nearby_restaurants' RPC to verify spatial indexing.
    """
    logger.info("==================================================")
    logger.info("FoodBook OpenStreetMap (OSM) Overpass Data Seeder")
    logger.info(f"Target Database: {settings.SUPABASE_URL}")
    logger.info("==================================================")

    elements = await query_overpass_lahore()
    logger.info(f"Processing {len(elements)} OpenStreetMap food spots...")

    seeded_restaurants = 0
    seeded_branches = 0

    for elem in elements:
        tags = elem.get("tags", {})
        name = tags.get("name") or tags.get("name:en")
        if not name or len(name.strip()) < 2:
            continue

        name = name.strip()
        lat = elem.get("lat")
        lon = elem.get("lon")

        if lat is None or lon is None:
            continue

        base_slug = slugify(name)
        if not base_slug:
            continue

        cuisines = map_osm_cuisine(tags)
        taste_vector = calculate_taste_vector(cuisines)

        # Estimate average price per person in PKR
        avg_price = 1200.0
        if "fast_food" in tags.get("amenity", "") or "Pizza" in cuisines:
            avg_price = 950.0
        elif "Cafe" in cuisines:
            avg_price = 750.0
        elif "Italian" in cuisines or "Continental" in cuisines:
            avg_price = 2200.0

        # Address construction
        street = tags.get("addr:street") or tags.get("street") or ""
        suburb = tags.get("addr:suburb") or tags.get("addr:neighbourhood") or tags.get("suburb") or ""
        city = tags.get("addr:city") or "Lahore"
        phone = tags.get("phone") or tags.get("contact:phone") or ""

        address_parts = [p for p in [street, suburb, city] if p]
        full_address = ", ".join(address_parts) if address_parts else f"{name}, {city}, Pakistan"
        branch_name = suburb or "Main Branch"

        # 1. Check if restaurant already exists by slug
        try:
            existing = await db.select("restaurants", filters={"slug": f"eq.{base_slug}"}, single=True)
            if existing:
                restaurant_id = existing["id"]
                logger.info(f"[EXISTING] Restaurant: {name} (ID: {restaurant_id})")
            else:
                # Insert Restaurant
                restaurant_data = {
                    "name": name,
                    "slug": base_slug,
                    "cuisines": cuisines,
                    "avg_price_per_person": avg_price,
                    "base_taste_vector": taste_vector,
                    "aggregated_taste_vector": taste_vector,
                    "avg_rating": round(4.0 + (elem.get("id", 100) % 10) * 0.08, 1),
                    "review_count": 5 + (elem.get("id", 100) % 25),
                    "is_active": True
                }
                res = await db.insert("restaurants", restaurant_data)
                restaurant_id = res[0]["id"]
                seeded_restaurants += 1
                logger.info(f"[CREATED] Restaurant: {name} (ID: {restaurant_id})")

            # 2. Insert Branch with PostGIS POINT(lng lat) coordinates
            existing_branches = await db.select(
                "restaurant_branches",
                filters={"restaurant_id": f"eq.{restaurant_id}"}
            ) or []

            branch_point_wkt = f"POINT({lon} {lat})"

            if not existing_branches:
                branch_data = {
                    "restaurant_id": restaurant_id,
                    "branch_name": branch_name,
                    "address": full_address,
                    "city": city,
                    "location": branch_point_wkt,
                    "phone_number": phone or "+92 42 111000111",
                    "opening_time": "11:00:00",
                    "closing_time": "01:00:00"
                }
                await db.insert("restaurant_branches", branch_data)
                seeded_branches += 1
                logger.info(f"   -> [CREATED] Branch: '{branch_name}' @ ({lat}, {lon})")
            else:
                logger.info(f"   -> [EXISTS] Branch: '{existing_branches[0].get('branch_name')}'")

            # 3. Ensure Menu Categories & Items exist for this restaurant
            existing_categories = await db.select("menu_categories", filters={"restaurant_id": f"eq.{restaurant_id}"})
            if not existing_categories:
                cat_res = await db.insert("menu_categories", {
                    "restaurant_id": restaurant_id,
                    "name": "Popular Specials",
                    "display_order": 1
                })
                cat_id = cat_res[0]["id"]

                item_name = f"{name} Signature Platter" if "Pakistani" in cuisines else f"{name} Special Combo"
                await db.insert("menu_items", {
                    "restaurant_id": restaurant_id,
                    "category_id": cat_id,
                    "name": item_name,
                    "description": f"House special preparation with authentic spices and fresh ingredients.",
                    "price": avg_price,
                    "item_taste_vector": taste_vector,
                    "is_available": True
                })

        except Exception as e:
            logger.error(f"Error seeding restaurant {name}: {e}")

    logger.info("==================================================")
    logger.info(f"OSM Seeding Complete: {seeded_restaurants} new restaurants, {seeded_branches} new branches.")
    logger.info("==================================================")

    # 4. Verify Spatial Radius Queries with PostGIS RPC
    logger.info("\nVerifying PostGIS 'get_nearby_restaurants' RPC function with live coordinates...")
    try:
        test_lat = 31.4697
        test_lon = 74.2728
        test_radius = 25000  # 25km

        rpc_res = await db.rpc("get_nearby_restaurants", params={
            "user_lat": test_lat,
            "user_lon": test_lon,
            "radius_meters": test_radius
        })

        logger.info(f"Found {len(rpc_res or [])} restaurants near ({test_lat}, {test_lon}) within {test_radius}m:")
        for idx, r in enumerate((rpc_res or [])[:6], start=1):
            dist_km = round(r.get("distance_meters", 0.0) / 1000, 2)
            logger.info(f"   {idx}. {r.get('restaurant_name')} ({r.get('branch_name')}) - {dist_km} km away | Price: PKR {r.get('avg_price_per_person')}")

    except Exception as e:
        logger.error(f"Error running PostGIS RPC test: {e}")

    await db.close()


if __name__ == "__main__":
    asyncio.run(seed_restaurants_from_osm())
