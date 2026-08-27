import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["app"] == "FoodBook Backend API"
    assert data["status"] == "online"


@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient):
    response = await client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"


@pytest.mark.asyncio
async def test_list_restaurants(client: AsyncClient):
    response = await client.get("/api/restaurants")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    data = json_data["data"]
    assert "items" in data
    assert "total" in data
    assert len(data["items"]) >= 1
    # Verify restaurant fields
    first = data["items"][0]
    assert "id" in first
    assert "name" in first
    assert "slug" in first
    assert "cuisines" in first


@pytest.mark.asyncio
async def test_get_restaurant_by_slug(client: AsyncClient):
    response = await client.get("/api/restaurants/slug/cheezious")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    data = json_data["data"]
    assert data["name"] == "Cheezious"
    assert data["slug"] == "cheezious"
    assert "branches" in data
    assert "menu_categories" in data


@pytest.mark.asyncio
async def test_nearby_restaurants(client: AsyncClient):
    # Lahore coordinates (near Johar Town)
    response = await client.get("/api/branches/nearby?latitude=31.4697&longitude=74.2728&radius_meters=50000")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    data = json_data["data"]
    assert isinstance(data, list)
    assert len(data) >= 1
    assert "distance_meters" in data[0]


@pytest.mark.asyncio
async def test_restaurants_nearby_endpoint(client: AsyncClient):
    # Test /api/restaurants/nearby with lat/lon aliases
    response = await client.get("/api/restaurants/nearby?lat=31.4697&lon=74.2728&radius_meters=50000")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    data = json_data["data"]
    assert isinstance(data, list)
    assert len(data) >= 1
    assert "distance_meters" in data[0]


@pytest.mark.asyncio
async def test_get_restaurant_by_id(client: AsyncClient):
    cheezious_id = "11111111-1111-1111-1111-111111111111"
    response = await client.get(f"/api/restaurants/{cheezious_id}")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    data = json_data["data"]
    assert data["id"] == cheezious_id
    assert "branches" in data
    assert "menu_categories" in data
    assert isinstance(data["branches"], list)
    assert isinstance(data["menu_categories"], list)


@pytest.mark.asyncio
async def test_restaurant_reviews_endpoint(client: AsyncClient):
    cheezious_id = "11111111-1111-1111-1111-111111111111"
    response = await client.get(f"/api/reviews/restaurant/{cheezious_id}")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    assert "items" in json_data["data"]


@pytest.mark.asyncio
async def test_restaurant_menu(client: AsyncClient):
    # Cheezious ID from seed data
    cheezious_id = "11111111-1111-1111-1111-111111111111"
    response = await client.get(f"/api/restaurants/{cheezious_id}/menu")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    data = json_data["data"]
    assert data["restaurant_id"] == cheezious_id
    assert "categories" in data
    assert len(data["categories"]) >= 1
    assert "items" in data["categories"][0]


@pytest.mark.asyncio
async def test_public_collections(client: AsyncClient):
    response = await client.get("/api/collections")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    assert "items" in json_data["data"]


@pytest.mark.asyncio
async def test_search_endpoint(client: AsyncClient):
    response = await client.get("/api/search?q=pizza&cuisine=Fast Food")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    data = json_data["data"]
    assert "restaurants" in data
    assert "menu_items" in data
    assert data["total_matches"] >= 1


@pytest.mark.asyncio
async def test_recommendations_endpoint(client: AsyncClient):
    # Test similar to Cheezious
    cheezious_id = "11111111-1111-1111-1111-111111111111"
    response = await client.get(f"/api/recommendations/similar/{cheezious_id}")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    data = json_data["data"]
    assert "recommendations" in data
    assert "total_recommendations" in data


@pytest.mark.asyncio
async def test_not_found_exception(client: AsyncClient):
    response = await client.get("/api/restaurants/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
    json_data = response.json()
    assert json_data["success"] is False
    assert "error_code" in json_data
    assert "NOT_FOUND" in json_data["error_code"]


@pytest.mark.asyncio
async def test_unauthorized_exception(client: AsyncClient):
    response = await client.get("/api/users/me")
    assert response.status_code == 401
    json_data = response.json()
    assert json_data["success"] is False
    assert json_data["error_code"] == "UNAUTHORIZED"


@pytest.mark.asyncio
async def test_spa_html_serving(client: AsyncClient):
    response = await client.get("/", headers={"Accept": "text/html,application/xhtml+xml"})
    assert response.status_code == 200
    assert "FoodBook" in response.text
    assert "<main id=\"main-root\">" in response.text


@pytest.mark.asyncio
async def test_spa_static_files(client: AsyncClient):
    css_res = await client.get("/css/style.css")
    assert css_res.status_code == 200
    assert "--primary" in css_res.text

    js_res = await client.get("/js/app.js")
    assert js_res.status_code == 200
    assert "App" in js_res.text

