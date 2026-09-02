# 🍽️ FoodBook — AI-Driven Dining Discovery & Spatial Recommendation System

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?logo=fastapi)
![Supabase](https://img.shields.io/badge/Supabase-PostgreSQL-3ECF8E?logo=supabase)
![PostGIS](https://img.shields.io/badge/PostGIS-Spatial%20Search-4169E1?logo=postgresql)
![License](https://img.shields.io/badge/License-MIT-green)
![PRs Welcome](https://img.shields.io/badge/PRs-Welcome-brightgreen)

> **FoodBook** is an AI-powered food discovery platform that goes beyond generic restaurant ratings by understanding **what you personally like to eat** and recommending restaurants and dishes based on your individual taste profile, location, budget, and food experiences.

Instead of asking **"What restaurant is popular?"**, FoodBook answers:

### 🎯 *"What food will I personally enjoy?"*

---

## ✨ Key Features

### 🧠 AI Taste Matching

FoodBook represents users, restaurants, dishes, and food experiences using a **9-dimensional taste vector**:

```text
[Spicy, Sweet, Salty, Sour, Umami, Smoky, Creamy, Crispy, Rich]
```

User preferences evolve through onboarding, reviews, ratings, and interactions, enabling personalized restaurant and dish recommendations.

### 📍 Spatial Restaurant Discovery

Find restaurants based on real-time geographic distance using:

* PostgreSQL + PostGIS
* `GEOGRAPHY(POINT, 4326)`
* `ST_DWithin`
* `ST_Distance`
* Supabase RPC functions

This enables queries such as:

> "Find restaurants within 5 km of my current location."

### 🗺️ Free Automated Restaurant Seeding

FoodBook can automatically discover restaurant data through the **OpenStreetMap Overpass API**, reducing dependency on expensive commercial Places APIs and paid Google Maps data services.

### 💬 Aspect-Based Review Analysis

FoodBook processes user reviews beyond simple star ratings.

For example:

> "The food was creamy and smoky, but too salty and the portion was small."

The system can extract meaningful aspects such as:

* Taste
* Spice
* Portion
* Service
* Ambiance
* Value
* Taste characteristics

These insights can contribute to continuously improving restaurant taste profiles.

### 🔐 Secure Authentication & RLS

Built around Supabase security features including:

* Supabase JWT authentication
* PostgreSQL Row Level Security (RLS)
* Protected API endpoints
* User-specific data access
* Role/ownership-based operations

---

# 🏗️ System Architecture

```text
                         ┌──────────────────────┐
                         │       USER           │
                         │ Web / Mobile Client  │
                         └──────────┬───────────┘
                                    │
                                    ▼
                    ┌────────────────────────────┐
                    │     Next.js / React        │
                    │        Frontend            │
                    └────────────┬───────────────┘
                                 │ REST API
                                 ▼
                    ┌────────────────────────────┐
                    │       FastAPI Backend      │
                    │                            │
                    │ • Authentication           │
                    │ • Restaurant Discovery     │
                    │ • Reviews                  │
                    │ • Taste Profiles           │
                    │ • Spatial Queries          │
                    │ • Recommendations          │
                    └────────────┬───────────────┘
                                 │
                    ┌────────────┴─────────────┐
                    ▼                          ▼
        ┌─────────────────────┐     ┌─────────────────────┐
        │      Supabase       │     │   OSM Overpass API  │
        │                     │     │                     │
        │ PostgreSQL          │     │ Restaurant Discovery│
        │ PostGIS             │     │ & Data Seeding      │
        │ Authentication      │     └─────────────────────┘
        │ Row Level Security  │
        └──────────┬──────────┘
                   │
                   ▼
        ┌─────────────────────┐
        │ Taste & Review Data │
        │                     │
        │ User Taste Vectors  │
        │ Restaurant Vectors  │
        │ Menu Data           │
        │ Reviews / Aspects   │
        └─────────────────────┘
```

---

# 🧩 Core Recommendation Flow

```text
User Preferences
       │
       ▼
9-Dimension Taste Profile
       │
       ▼
Restaurant & Dish Taste Vectors
       │
       ▼
Location + Budget + Cuisine Filters
       │
       ▼
Review / Aspect Analysis
       │
       ▼
Taste Similarity & Ranking
       │
       ▼
Personalized Recommendations
```

FoodBook combines **taste similarity + spatial proximity + user preferences + review intelligence** to produce more meaningful recommendations.

---

# 📁 Project Structure

```text
FoodBook/
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── core/
│   │
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── app/
│   ├── components/
│   ├── lib/
│   ├── public/
│   └── package.json
│
├── scripts/
│   └── seed_osm_restaurants.py
│
├── tests/
│   ├── test_users.py
│   ├── test_restaurants.py
│   ├── test_reviews.py
│   └── test_nearby.py
│
├── .gitignore
└── README.md
```

---

# 🚀 Quick Start

## 1️⃣ Clone the Repository

```bash
git clone https://github.com/your-username/FoodBook.git
cd FoodBook
```

> Replace `your-username/FoodBook` with the actual repository URL.

---

## 2️⃣ Backend Setup

Navigate to the backend:

```bash
cd backend
```

Create a virtual environment:

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

### macOS / Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## 3️⃣ Configure Environment Variables

Create a `.env` file inside the backend directory:

```env
SUPABASE_URL=your_supabase_project_url
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key
```

⚠️ **Never commit your `.env` file or Supabase service-role key to GitHub.**

The service-role key should only be used in trusted server-side environments.

---

## 4️⃣ Seed Restaurant Data

FoodBook supports automated restaurant discovery through OpenStreetMap's Overpass API.

From the project root:

```bash
python scripts/seed_osm_restaurants.py
```

The script discovers available restaurant data and inserts it into the FoodBook database.

---

## 5️⃣ Start the Backend

From the backend directory:

```bash
uvicorn app.main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

FastAPI interactive documentation:

```text
http://127.0.0.1:8000/docs
```

---

## 6️⃣ Run Tests

From the project root:

```bash
pytest
```

Run with detailed output:

```bash
pytest -v
```

---

# 🔌 API Overview

FoodBook exposes REST APIs that connect the frontend with authentication, restaurant data, reviews, spatial discovery, and personalized functionality.

| Method   | Endpoint                      | Description                        | Auth        |
| -------- | ----------------------------- | ---------------------------------- | ----------- |
| `GET`    | `/api/users`                  | Get authenticated user information | 🔐 Required |
| `GET`    | `/api/users/me/taste-profile` | Retrieve user's taste profile      | 🔐 Required |
| `PUT`    | `/api/users/me/taste-profile` | Update taste preferences           | 🔐 Required |
| `GET`    | `/api/restaurants`            | Browse restaurants                 | Optional    |
| `GET`    | `/api/restaurants/{id}`       | Get restaurant details             | Optional    |
| `GET`    | `/api/restaurants/nearby`     | Find restaurants within a radius   | Optional    |
| `GET`    | `/api/restaurants/{id}/menu`  | Retrieve restaurant menu           | Optional    |
| `GET`    | `/api/reviews`                | Retrieve reviews                   | Optional    |
| `POST`   | `/api/reviews`                | Create a restaurant review         | 🔐 Required |
| `PUT`    | `/api/reviews/{id}`           | Update user's review               | 🔐 Required |
| `DELETE` | `/api/reviews/{id}`           | Delete user's review               | 🔐 Required |

> **Interactive API documentation:** Once the backend is running, visit `/docs` to explore and test available endpoints through Swagger UI.

---

# 📍 Spatial Search

FoodBook uses **PostGIS** to perform efficient geographic queries.

Restaurant branches are stored as:

```sql
GEOGRAPHY(POINT, 4326)
```

Nearby searches use spatial operations such as:

```sql
ST_DWithin()
ST_Distance()
```

This allows FoodBook to efficiently answer queries such as:

```text
Find restaurants within 5 km
↓
Apply cuisine filter
↓
Apply budget filter
↓
Calculate distance
↓
Rank suitable restaurants
```

---

# 🧠 Taste Intelligence

FoodBook's recommendation system uses a common taste representation across users, restaurants, dishes, and reviews.

### Taste Dimensions

| Dimension | Example Preference |
| --------- | ------------------ |
| 🌶️ Spicy | Mild → Very Spicy  |
| 🍬 Sweet  | Low → High         |
| 🧂 Salty  | Low → High         |
| 🍋 Sour   | Low → High         |
| 🍜 Umami  | Low → High         |
| 🔥 Smoky  | Low → High         |
| 🥛 Creamy | Low → High         |
| 🥨 Crispy | Low → High         |
| 🍛 Rich   | Low → High         |

This allows FoodBook to compare what a user likes with the characteristics of available food.

---

# 💡 Example Recommendation

Imagine a user enjoys:

```text
Spicy     → 0.85
Creamy    → 0.80
Crispy    → 0.75
Smoky     → 0.65
```

FoodBook can identify restaurants or dishes with similar profiles.

Instead of simply returning:

> ⭐ 4.7 — Restaurant X

FoodBook can provide:

> **92% Taste Match**

**Why?**

* Similar spice level 🌶️
* Similar creamy profile 🥛
* Similar crispiness 🥨
* Within your budget 💰
* 2.1 km away 📍

This is the core difference between FoodBook and traditional restaurant discovery platforms.

---

# 🛡️ Security

FoodBook follows a security-first approach using:

* Supabase Authentication
* JWT-based authentication
* PostgreSQL Row Level Security
* Server-side secret management
* Input validation with Pydantic
* Ownership validation
* Protected endpoints

Sensitive credentials should always be stored using environment variables.

```text
.env
```

should never be committed to the repository.

---

# 🧪 Testing

FoodBook uses **Pytest** for backend testing.

Tests cover critical functionality including:

* User operations
* Restaurant retrieval
* Spatial discovery
* Reviews
* Authentication
* API behavior

Run:

```bash
pytest -v
```

---

# 🤝 Contributing

Contributions are welcome!

### Development Workflow

1. Fork the repository.
2. Create a feature branch.

```bash
git checkout -b feature/your-feature
```

3. Make your changes.
4. Add or update tests.
5. Run the test suite.

```bash
pytest
```

6. Commit your changes.

```bash
git commit -m "Add your feature"
```

7. Push your branch.

```bash
git push origin feature/your-feature
```

8. Open a Pull Request.

Please keep contributions focused, documented, and consistent with the existing architecture.

---

# 📄 License

This project is licensed under the **MIT License**.

You are free to use, modify, and distribute this project according to the terms of the license.

---

# 👥 Team

### FoodBook Team

**Taha** — Backend, Database & Supabase Integration
**Shehryar** — AI/ML & Recommendation System
**Huzaifa** — Frontend & Application Development

---

# 🌟 Vision

FoodBook aims to transform restaurant discovery from:

> **"What is popular?"**

into:

> **"What will I personally enjoy?"**

By combining **AI/ML, personalized taste profiles, review intelligence, spatial search, and community experiences**, FoodBook creates a more meaningful way to discover food.

### 🍽️ FoodBook

**Discover Food That Matches Your Taste.**
