import pytest
from httpx import AsyncClient
import uuid
import time


@pytest.mark.asyncio
async def test_auth_signup_login_profile_flow(client: AsyncClient):
    # Generate unique test user
    uid = uuid.uuid4().hex[:8]
    test_email = f"foodbook_test_{uid}@gmail.com"
    test_password = "TestPassword123!"
    test_name = f"Test User {uid}"

    # 1. Sign Up
    signup_res = await client.post(
        "/api/auth/signup",
        json={
            "email": test_email,
            "password": test_password,
            "full_name": test_name
        }
    )
    assert signup_res.status_code in [201, 200]
    signup_data = signup_res.json()
    assert signup_data["success"] is True
    token_data = signup_data["data"]
    access_token = token_data.get("access_token")
    assert access_token is not None

    headers = {"Authorization": f"Bearer {access_token}"}

    # 2. Login
    login_res = await client.post(
        "/api/auth/login",
        json={
            "email": test_email,
            "password": test_password
        }
    )
    assert login_res.status_code == 200
    login_data = login_res.json()
    assert login_data["success"] is True
    assert "access_token" in login_data["data"]

    # 3. Get Me
    me_res = await client.get("/api/auth/me", headers=headers)
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["success"] is True
    assert me_data["data"]["email"] == test_email

    # 4. Get User Profile
    profile_res = await client.get("/api/users/me", headers=headers)
    assert profile_res.status_code == 200
    profile_data = profile_res.json()
    assert profile_data["success"] is True

    # 5. Update Profile
    update_res = await client.put(
        "/api/users/me",
        json={"full_name": f"{test_name} Updated"},
        headers=headers
    )
    assert update_res.status_code == 200
    assert update_res.json()["data"]["full_name"] == f"{test_name} Updated"

    # 6. Get Taste Profile (both /api/taste-profile/me and /api/users/me/taste-profile)
    taste_res = await client.get("/api/taste-profile/me", headers=headers)
    assert taste_res.status_code == 200
    taste_data = taste_res.json()
    assert taste_data["success"] is True
    assert len(taste_data["data"]["taste_vector"]) == 9

    taste_user_res = await client.get("/api/users/me/taste-profile", headers=headers)
    assert taste_user_res.status_code == 200
    assert len(taste_user_res.json()["data"]["taste_vector"]) == 9

    # 7. Update Taste Profile
    new_vector = [0.8, 0.2, 0.7, 0.3, 0.9, 0.6, 0.4, 0.8, 0.7]
    update_taste_res = await client.put(
        "/api/users/me/taste-profile",
        json={
            "taste_vector": new_vector,
            "preferred_cuisines": ["Pakistani", "BBQ", "Pizza"],
            "dietary_restrictions": ["Halal"],
            "budget_level": "moderate"
        },
        headers=headers
    )
    assert update_taste_res.status_code == 200
    updated_taste = update_taste_res.json()["data"]
    assert updated_taste["taste_vector"] == new_vector
    assert "Pakistani" in updated_taste["preferred_cuisines"]

    # 8. Save Restaurant
    cheezious_id = "11111111-1111-1111-1111-111111111111"
    save_res = await client.post(f"/api/restaurants/{cheezious_id}/save", headers=headers)
    assert save_res.status_code in [201, 200]
    assert save_res.json()["success"] is True

    # 9. List Saved Restaurants
    saved_list_res = await client.get("/api/users/me/saved-restaurants", headers=headers)
    assert saved_list_res.status_code == 200
    saved_items = saved_list_res.json()["data"]["items"]
    assert any(s["restaurant_id"] == cheezious_id for s in saved_items)

    # 10. Unsave Restaurant
    unsave_res = await client.delete(f"/api/restaurants/{cheezious_id}/save", headers=headers)
    assert unsave_res.status_code == 200
    assert unsave_res.json()["success"] is True

    # 11. Create Review (POST /api/reviews)
    review_res = await client.post(
        "/api/reviews",
        json={
            "restaurant_id": cheezious_id,
            "overall_rating": 4.5,
            "review_text": "The pizza was very cheesy and creamy, but slightly too salty.",
            "dish_ratings": []
        },
        headers=headers
    )
    assert review_res.status_code == 201
    review_data = review_res.json()["data"]
    review_id = review_data["id"]
    assert review_data["overall_rating"] == 4.5
    assert "cheesy" in review_data["extracted_aspects"] or review_data["extracted_aspects"] is not None

    # 12. Get My Reviews (both /api/users/me/reviews and /api/reviews/me)
    my_reviews_res = await client.get("/api/users/me/reviews", headers=headers)
    assert my_reviews_res.status_code == 200
    assert len(my_reviews_res.json()["data"]["items"]) >= 1

    my_reviews_alias_res = await client.get("/api/reviews/me", headers=headers)
    assert my_reviews_alias_res.status_code == 200
    assert len(my_reviews_alias_res.json()["data"]["items"]) >= 1

    # 13. Delete Review
    del_review_res = await client.delete(f"/api/reviews/{review_id}", headers=headers)
    assert del_review_res.status_code == 200
    assert del_review_res.json()["success"] is True

    # 14. Create Collection
    col_res = await client.post(
        "/api/collections",
        json={
            "title": f"My Favorite Food Spots {uid}",
            "description": "Curated collection of great places in Lahore",
            "is_public": True
        },
        headers=headers
    )
    assert col_res.status_code == 201
    col_data = col_res.json()["data"]
    col_id = col_data["id"]

    # 15. Add Item to Collection
    add_item_res = await client.post(
        f"/api/collections/{col_id}/items",
        json={"restaurant_id": cheezious_id},
        headers=headers
    )
    assert add_item_res.status_code == 200
    assert len(add_item_res.json()["data"]["items"]) >= 1

    # 16. Get Collection Detail
    col_detail_res = await client.get(f"/api/collections/{col_id}")
    assert col_detail_res.status_code == 200
    assert col_detail_res.json()["data"]["title"] == f"My Favorite Food Spots {uid}"

    # 17. Delete Collection
    del_col_res = await client.delete(f"/api/collections/{col_id}", headers=headers)
    assert del_col_res.status_code == 200
    assert del_col_res.json()["success"] is True
