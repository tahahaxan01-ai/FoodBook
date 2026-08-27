/**
 * FoodBook Authentication Module
 * Manages Supabase Auth credentials & session state
 */
import { api } from './api.js';
import { state } from './state.js';

export class AuthManager {
    static async signup(email, password, fullName) {
        try {
            const res = await api.signup(email, password, fullName);
            if (res.success && res.data) {
                const { user, access_token } = res.data;
                state.setUser(user, access_token);
                state.notify('toast', {
                    type: 'success',
                    message: `Welcome to FoodBook, ${user.full_name || 'Foodie'}! 🎉`
                });
                return { success: true, user };
            }
            throw new Error(res.message || 'Signup failed');
        } catch (err) {
            console.error('Signup error:', err);
            state.notify('toast', {
                type: 'error',
                message: err.message || 'Signup error. Please check your details.'
            });
            return { success: false, error: err.message };
        }
    }

    static async login(email, password) {
        try {
            const res = await api.login(email, password);
            if (res.success && res.data) {
                const { user, access_token } = res.data;
                state.setUser(user, access_token);
                state.notify('toast', {
                    type: 'success',
                    message: `Welcome back, ${user.full_name || user.email}! 🍽️`
                });
                return { success: true, user };
            }
            throw new Error(res.message || 'Login failed');
        } catch (err) {
            console.error('Login error:', err);
            state.notify('toast', {
                type: 'error',
                message: err.message || 'Invalid email or password.'
            });
            return { success: false, error: err.message };
        }
    }

    static async logout() {
        api.setToken(null);
        state.setUser(null, null);
        state.notify('toast', {
            type: 'info',
            message: 'You have been logged out.'
        });
        state.navigate('home');
    }
}
