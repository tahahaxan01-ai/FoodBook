/**
 * FoodBook API Client
 * Connects frontend directly to the FastAPI Backend
 */
import { CONFIG } from './config.js';

class ApiClient {
    constructor() {
        this.baseUrl = CONFIG.API_BASE_URL;
        this.token = localStorage.getItem('foodbook_token') || null;
    }

    setToken(token) {
        this.token = token;
        if (token) {
            localStorage.setItem('foodbook_token', token);
        } else {
            localStorage.removeItem('foodbook_token');
        }
    }

    getToken() {
        return this.token || localStorage.getItem('foodbook_token');
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const headers = {
            'Content-Type': 'application/json',
            ...(options.headers || {})
        };

        const token = this.getToken();
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        try {
            const response = await fetch(url, {
                ...options,
                headers
            });

            if (response.status === 401) {
                // Token expired or invalid
                console.warn('Unauthorized request to', endpoint);
            }

            const data = await response.json().catch(() => null);

            if (!response.ok) {
                const errorMessage = data?.detail || data?.message || `HTTP error ${response.status}`;
                const error = new Error(errorMessage);
                error.status = response.status;
                error.data = data;
                throw error;
            }

            return data;
        } catch (error) {
            console.error(`API Request Error [${endpoint}]:`, error);
            throw error;
        }
    }

    // --- Authentication ---
    async signup(email, password, full_name) {
        return this.request('/auth/signup', {
            method: 'POST',
            body: JSON.stringify({ email, password, full_name })
        });
    }

    async login(email, password) {
        const res = await this.request('/auth/login', {
            method: 'POST',
            body: JSON.stringify({ email, password })
        });
        if (res?.data?.access_token) {
            this.setToken(res.data.access_token);
        }
        return res;
    }

    async getMe() {
        return this.request('/auth/me');
    }

    // --- User Profile & Taste Vector ---
    async getUserProfile() {
        return this.request('/users/me');
    }

    async updateUserProfile(profileData) {
        return this.request('/users/me', {
            method: 'PUT',
            body: JSON.stringify(profileData)
        });
    }

    async getTasteProfile() {
        return this.request('/taste-profile/me');
    }

    async updateTasteProfile(tasteData) {
        return this.request('/users/me/taste-profile', {
            method: 'PUT',
            body: JSON.stringify(tasteData)
        });
    }

    // --- Restaurants & Discovery ---
    async getRestaurants(params = {}) {
        const query = new URLSearchParams();
        if (params.cuisine) query.append('cuisine', params.cuisine);
        if (params.search) query.append('search', params.search);
        if (params.min_price) query.append('min_price', params.min_price);
        if (params.max_price) query.append('max_price', params.max_price);
        if (params.min_rating) query.append('min_rating', params.min_rating);
        if (params.limit) query.append('limit', params.limit);
        if (params.offset) query.append('offset', params.offset);

        const qs = query.toString() ? `?${query.toString()}` : '';
        return this.request(`/restaurants${qs}`);
    }

    async getRestaurantById(id) {
        return this.request(`/restaurants/${id}`);
    }

    async getRestaurantBranches(id) {
        return this.request(`/restaurants/${id}/branches`);
    }

    async getRestaurantMenu(id) {
        return this.request(`/restaurants/${id}/menu`);
    }

    async getNearbyRestaurants(lat, lon, radius = 10000, max_budget = null) {
        const query = new URLSearchParams({
            latitude: lat,
            longitude: lon,
            radius_meters: radius
        });
        if (max_budget) query.append('max_budget', max_budget);
        return this.request(`/restaurants/nearby?${query.toString()}`);
    }

    // --- Recommendations (AI/ML) ---
    async getRecommendations(params = {}) {
        const query = new URLSearchParams();
        if (params.latitude) query.append('latitude', params.latitude);
        if (params.longitude) query.append('longitude', params.longitude);
        if (params.max_budget) query.append('max_budget', params.max_budget);
        if (params.radius_meters) query.append('radius_meters', params.radius_meters);
        if (params.limit) query.append('limit', params.limit || 10);

        const qs = query.toString() ? `?${query.toString()}` : '';
        return this.request(`/recommendations${qs}`);
    }

    async getSimilarRestaurants(restaurantId, limit = 6) {
        return this.request(`/recommendations/similar/${restaurantId}?limit=${limit}`);
    }

    async postCustomRecommendations(requestData) {
        return this.request('/recommendations', {
            method: 'POST',
            body: JSON.stringify(requestData)
        });
    }

    // --- Reviews ---
    async getRestaurantReviews(restaurantId, limit = 20) {
        return this.request(`/reviews/restaurant/${restaurantId}?limit=${limit}`);
    }

    async createReview(reviewData) {
        return this.request('/reviews', {
            method: 'POST',
            body: JSON.stringify(reviewData)
        });
    }

    async deleteReview(reviewId) {
        return this.request(`/reviews/${reviewId}`, {
            method: 'DELETE'
        });
    }

    async getMyReviews() {
        return this.request('/reviews/me');
    }

    // --- Saved Restaurants ---
    async getSavedRestaurants() {
        return this.request('/users/me/saved-restaurants');
    }

    async saveRestaurant(restaurantId) {
        return this.request(`/restaurants/${restaurantId}/save`, {
            method: 'POST'
        });
    }

    async unsaveRestaurant(restaurantId) {
        return this.request(`/restaurants/${restaurantId}/save`, {
            method: 'DELETE'
        });
    }

    // --- Collections ---
    async getCollections(isPublic = true) {
        return this.request(`/collections?is_public=${isPublic}`);
    }

    async getCollectionById(id) {
        return this.request(`/collections/${id}`);
    }

    async createCollection(collectionData) {
        return this.request('/collections', {
            method: 'POST',
            body: JSON.stringify(collectionData)
        });
    }

    async addItemToCollection(collectionId, restaurantId, notes = "") {
        return this.request(`/collections/${collectionId}/items`, {
            method: 'POST',
            body: JSON.stringify({ restaurant_id: restaurantId, notes })
        });
    }

    async removeItemFromCollection(collectionId, restaurantId) {
        return this.request(`/collections/${collectionId}/items/${restaurantId}`, {
            method: 'DELETE'
        });
    }

    async deleteCollection(collectionId) {
        return this.request(`/collections/${collectionId}`, {
            method: 'DELETE'
        });
    }

    // --- Search & Conversational AI ---
    async search(keyword, cuisine = null, limit = 20) {
        const query = new URLSearchParams({ q: keyword, limit });
        if (cuisine) query.append('cuisine', cuisine);
        return this.request(`/search?${query.toString()}`);
    }

    // --- Community Feed (Posts) ---
    async getFeedPosts(limit = 20, offset = 0) {
        return this.request(`/posts?limit=${limit}&offset=${offset}`);
    }

    async createPost(postData) {
        return this.request('/posts', {
            method: 'POST',
            body: JSON.stringify(postData)
        });
    }

    async deletePost(postId) {
        return this.request(`/posts/${postId}`, {
            method: 'DELETE'
        });
    }

    async likePost(postId) {
        return this.request(`/posts/${postId}/like`, {
            method: 'POST'
        });
    }

    async unlikePost(postId) {
        return this.request(`/posts/${postId}/like`, {
            method: 'DELETE'
        });
    }

    // --- Comments (Posts & Reviews) ---
    async getPostComments(postId) {
        return this.request(`/posts/${postId}/comments`);
    }

    async addPostComment(postId, text) {
        return this.request(`/posts/${postId}/comments`, {
            method: 'POST',
            body: JSON.stringify({ text })
        });
    }

    async deletePostComment(postId, commentId) {
        return this.request(`/posts/${postId}/comments/${commentId}`, {
            method: 'DELETE'
        });
    }

    async likeReview(reviewId) {
        return this.request(`/reviews/${reviewId}/like`, {
            method: 'POST'
        });
    }

    async unlikeReview(reviewId) {
        return this.request(`/reviews/${reviewId}/like`, {
            method: 'DELETE'
        });
    }
}

export const api = new ApiClient();
