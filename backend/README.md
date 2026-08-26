# FoodBook Backend API 🍲

AI-Powered Personalized Food Discovery & Recommendation Backend for Pakistan built with FastAPI, Supabase (PostgreSQL + PostGIS), and OpenStreetMap (OSM).

---

## 🌟 Key Features

1. **User Authentication & Management (`/api/auth`, `/api/users`)**
   - Supabase Auth integration (email/password signup, login, JWT token issuance).
   - Profile management and personal 9-dimensional taste vectors `FLOAT[9]` (`[spicy, sweet, salty, sour, umami, smoky, creamy, crispy, rich]`).
   - Budget preferences (`avg_price_per_person` / budget tiers) and dietary restrictions (`Halal`, `Vegetarian`, etc.).

2. **Geospatial Discovery & Spatial Search (`/api/restaurants`, `/api/branches`)**
   - PostGIS spatial point queries (`SRID=4326; POINT(lon lat)`).
   - Stored procedure RPC `get_nearby_restaurants` calculating real-time distances within customizable radii (`radius_meters`).
   - Detailed restaurant profiles with branch coordinates, categorised menus, dish taste vectors, and aggregated ratings.

3. **Aspect-Based Reviews & Ratings (`/api/reviews`)**
   - Multi-dimensional review submission with dish-specific ratings.
   - Text sentiment and taste aspect extraction with seamless AI/ML service fallback.
   - Author-protected deletion and paginated retrieval.

4. **Community Collections & Bookmarks (`/api/collections`, `/api/saved-restaurants`)**
   - Curated community guides and user food collections.
   - Fast bookmarking and personalized favorite lists.

5. **AI Recommendation Engine (`/api/recommendations`)**
   - Cosine similarity matching against restaurant aggregated taste vectors.
   - Proximity weighting and cuisine preference bonuses.
   - "More like this" restaurant similarity discovery (`/api/recommendations/similar/{id}`).

---

## 🚀 Setup & Installation

### Prerequisites
- Python 3.10+
- Supabase project URL and API Service Role Key

### 1. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Create a `.env` file in the `backend/` root directory:
```env
SUPABASE_URL=https://<your-project-id>.supabase.co
SUPABASE_SERVICE_ROLE_KEY=<your-service-role-key>
SUPABASE_ANON_KEY=<your-anon-key>
RECOMMENDATION_SERVICE_URL=http://localhost:8001
ENVIRONMENT=development
DEBUG=True
CORS_ORIGINS=["*"]
```

### 3. Seed OpenStreetMap (OSM) Data
Populate real restaurants, branches with PostGIS points, and signature menus in Lahore:
```bash
python scripts/seed_osm_data.py
```

### 4. Run Development Server
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
Interactive Swagger API documentation will be live at `http://localhost:8000/docs`.

---

## 🧪 Testing

Execute all automated unit and integration tests:
```bash
python -m pytest -v
```
