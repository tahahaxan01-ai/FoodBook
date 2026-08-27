/**
 * FoodBook Global State Store
 */
import { api } from './api.js';
import { CONFIG } from './config.js';

class StateStore {
    constructor() {
        this.user = null;
        this.tasteProfile = null;
        this.savedRestaurantIds = new Set();
        this.currentLocation = { ...CONFIG.DEFAULT_LOCATION };
        this.hasLocationPermission = false;
        this.currentView = 'home';
        this.viewParams = {};
        this.theme = localStorage.getItem('foodbook_theme') || 'dark';
        this.listeners = new Map();
    }

    subscribe(event, callback) {
        if (!this.listeners.has(event)) {
            this.listeners.set(event, []);
        }
        this.listeners.get(event).push(callback);
        return () => {
            const list = this.listeners.get(event) || [];
            this.listeners.set(event, list.filter(cb => cb !== callback));
        };
    }

    notify(event, data) {
        const list = this.listeners.get(event) || [];
        list.forEach(cb => {
            try {
                cb(data);
            } catch (err) {
                console.error(`Error in state listener [${event}]:`, err);
            }
        });
    }

    async init() {
        // Apply theme immediately
        this.setTheme(this.theme);

        // 1. Try to load authenticated user
        const token = api.getToken();
        if (token) {
            try {
                const userRes = await api.getMe();
                if (userRes?.success && userRes.data) {
                    this.user = userRes.data;
                    await this.loadTasteProfile();
                    await this.loadSavedRestaurants();
                    this.notify('authChanged', this.user);
                } else {
                    api.setToken(null);
                }
            } catch (err) {
                console.warn('Session check failed or expired, clearing token.');
                api.setToken(null);
                this.user = null;
                this.notify('authChanged', null);
            }
        }

        // 2. Request user location silently if possible
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                (pos) => {
                    this.currentLocation = {
                        name: "Your Live Location",
                        latitude: pos.coords.latitude,
                        longitude: pos.coords.longitude
                    };
                    this.hasLocationPermission = true;
                    this.notify('locationChanged', this.currentLocation);
                },
                () => {
                    this.hasLocationPermission = false;
                },
                { timeout: 5000 }
            );
        }
    }

    setTheme(theme) {
        this.theme = theme;
        localStorage.setItem('foodbook_theme', theme);
        document.documentElement.setAttribute('data-theme', theme);
        this.notify('themeChanged', theme);
    }

    toggleTheme() {
        const newTheme = this.theme === 'dark' ? 'light' : 'dark';
        this.setTheme(newTheme);
        return newTheme;
    }

    setLocation(loc) {
        this.currentLocation = { ...loc };
        this.notify('locationChanged', this.currentLocation);
    }

    setUser(user, token) {
        this.user = user;
        if (token) api.setToken(token);
        if (user) {
            this.loadTasteProfile();
            this.loadSavedRestaurants();
        } else {
            this.tasteProfile = null;
            this.savedRestaurantIds.clear();
        }
        this.notify('authChanged', this.user);
    }

    async loadTasteProfile() {
        if (!this.user) return null;
        try {
            const res = await api.getTasteProfile();
            if (res?.success && res.data) {
                this.tasteProfile = res.data;
                this.notify('tasteProfileChanged', this.tasteProfile);
                return this.tasteProfile;
            }
        } catch (err) {
            console.debug('No taste profile loaded yet:', err);
        }
        return null;
    }

    async loadSavedRestaurants() {
        if (!this.user) return;
        try {
            const res = await api.getSavedRestaurants();
            if (res?.success && res.data?.items) {
                this.savedRestaurantIds = new Set(res.data.items.map(item => item.restaurant_id));
                this.notify('savedRestaurantsChanged', this.savedRestaurantIds);
            }
        } catch (err) {
            console.debug('Error loading saved restaurants:', err);
        }
    }

    isRestaurantSaved(restaurantId) {
        return this.savedRestaurantIds.has(restaurantId);
    }

    async toggleSaveRestaurant(restaurantId) {
        if (!this.user) {
            this.notify('requireAuth', { action: 'save_restaurant', id: restaurantId });
            return false;
        }

        const isCurrentlySaved = this.savedRestaurantIds.has(restaurantId);
        try {
            if (isCurrentlySaved) {
                await api.unsaveRestaurant(restaurantId);
                this.savedRestaurantIds.delete(restaurantId);
                this.notify('toast', { type: 'info', message: 'Removed from saved places' });
            } else {
                await api.saveRestaurant(restaurantId);
                this.savedRestaurantIds.add(restaurantId);
                this.notify('toast', { type: 'success', message: 'Saved to your food spots! ⭐' });
            }
            this.notify('savedRestaurantsChanged', this.savedRestaurantIds);
            return !isCurrentlySaved;
        } catch (err) {
            this.notify('toast', { type: 'error', message: err.message || 'Failed to update saved restaurant' });
            return isCurrentlySaved;
        }
    }

    navigate(view, params = {}) {
        this.currentView = view;
        this.viewParams = params;
        
        let hash = `#${view}`;
        if (params.id) hash += `/${params.id}`;
        
        // Setting location.hash directly will trigger window hashchange event
        if (window.location.hash !== hash) {
            window.location.hash = hash;
        } else {
            // If already on the same hash, notify explicitly to re-render
            this.notify('forceRenderRoute', { view, params });
        }
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
}

export const state = new StateStore();
