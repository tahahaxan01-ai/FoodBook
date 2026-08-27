"""
FoodBook OpenStreetMap (OSM) Restaurant Seeder (Alias entrypoint)
"""
import asyncio
from backend.scripts.seed_osm_data import seed_restaurants_from_osm

if __name__ == "__main__":
    asyncio.run(seed_restaurants_from_osm())
