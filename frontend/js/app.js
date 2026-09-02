/**
 * FoodBook Main Application Router & Entrypoint
 */
import { state } from './state.js';
import { Navbar } from './components/Navbar.js';
import { Footer } from './components/Footer.js';
import { AuthModal } from './components/AuthModal.js';
import { ReviewModal } from './components/ReviewModal.js';
import { CollectionModal } from './components/CollectionModal.js';
import { PostComposerModal } from './components/PostComposerModal.js';

// Views
import { HomeView } from './views/HomeView.js';
import { ExploreView } from './views/ExploreView.js';
import { RestaurantView } from './views/RestaurantView.js';
import { OnboardingView } from './views/OnboardingView.js';
import { ProfileView } from './views/ProfileView.js';
import { CollectionsView } from './views/CollectionsView.js';
import { AISearchView } from './views/AISearchView.js';
import { OwnerDashboardView } from './views/OwnerDashboardView.js';
import { CommunityFeedView } from './views/CommunityFeedView.js';

class App {
    static async init() {
        // Render static chrome shell (Navbar, Modals, Footer, Toast container)
        document.getElementById('nav-root').innerHTML = Navbar.render();
        document.getElementById('footer-root').innerHTML = Footer.render();
        document.getElementById('modals-root').innerHTML = `
            ${AuthModal.render()}
            ${ReviewModal.render()}
            ${CollectionModal.render()}
            ${PostComposerModal.render()}
            <div id="toast-container" class="toast-container"></div>
        `;

        // Attach shell events
        Navbar.attachEvents();
        AuthModal.attachEvents();
        ReviewModal.attachEvents();
        CollectionModal.attachEvents();
        PostComposerModal.attachEvents();

        // Subscribe to global toast notifications
        state.subscribe('toast', (data) => {
            App.showToast(data.message, data.type || 'info');
        });

        // Re-render Navbar on auth changes, theme changes, or location changes
        state.subscribe('authChanged', () => {
            document.getElementById('nav-root').innerHTML = Navbar.render();
            Navbar.attachEvents();
        });

        state.subscribe('themeChanged', () => {
            document.getElementById('nav-root').innerHTML = Navbar.render();
            Navbar.attachEvents();
        });

        state.subscribe('locationChanged', () => {
            document.getElementById('nav-root').innerHTML = Navbar.render();
            Navbar.attachEvents();
        });

        state.subscribe('forceRenderRoute', () => {
            App.handleRoute();
        });

        state.subscribe('savedRestaurantsChanged', () => {
            const count = state.savedRestaurantIds.size;
            const badge = document.querySelector('.badge-counter');
            if (badge) {
                badge.textContent = count;
                badge.style.display = count > 0 ? 'inline-block' : 'none';
            }
        });

        // Initialize state (auth token & geolocation & theme)
        await state.init();

        // Handle URL hash changes
        window.addEventListener('hashchange', () => {
            App.handleRoute();
        });

        // Initial route
        App.handleRoute();
    }

    static async handleRoute() {
        const hash = window.location.hash.slice(1) || 'home';
        const parts = hash.split('/');
        const viewName = parts[0] || 'home';
        const paramId = parts[1] || null;

        let cleanViewName = viewName;
        let queryParams = {};
        if (viewName.includes('?')) {
            const [v, q] = viewName.split('?');
            cleanViewName = v;
            const searchParams = new URLSearchParams(q);
            for (const [key, value] of searchParams.entries()) {
                queryParams[key] = value;
            }
        }

        const params = { id: paramId, ...queryParams, ...state.viewParams };
        state.currentView = cleanViewName;
        state.viewParams = params;

        const main = document.getElementById('main-root');
        main.innerHTML = `
            <div class="view-loader py-5 text-center">
                <div class="spinner"></div>
            </div>
        `;

        try {
            switch (cleanViewName) {
                case 'home':
                    main.innerHTML = await HomeView.render();
                    await HomeView.attachEvents();
                    break;
                case 'explore':
                    main.innerHTML = await ExploreView.render();
                    await ExploreView.attachEvents();
                    break;
                case 'restaurant':
                    main.innerHTML = await RestaurantView.render();
                    await RestaurantView.attachEvents();
                    break;
                case 'onboarding':
                    main.innerHTML = await OnboardingView.render();
                    await OnboardingView.attachEvents();
                    break;
                case 'profile':
                    main.innerHTML = await ProfileView.render();
                    await ProfileView.attachEvents();
                    break;
                case 'collections':
                    main.innerHTML = await CollectionsView.render();
                    await CollectionsView.attachEvents();
                    break;
                case 'community':
                    main.innerHTML = await CommunityFeedView.render();
                    await CommunityFeedView.attachEvents();
                    break;
                case 'ai-search':
                    main.innerHTML = await AISearchView.render();
                    await AISearchView.attachEvents();
                    break;
                case 'owner':
                    main.innerHTML = await OwnerDashboardView.render();
                    await OwnerDashboardView.attachEvents();
                    break;
                default:
                    main.innerHTML = await HomeView.render();
                    await HomeView.attachEvents();
                    break;
            }

            // Update active state in Desktop Navbar
            document.querySelectorAll('.nav-link').forEach(link => {
                const href = link.getAttribute('href')?.slice(1);
                link.classList.toggle('active', href === cleanViewName);
            });

            // Update active state in Mobile Bottom Bar
            document.querySelectorAll('.bottom-nav-item').forEach(link => {
                const href = link.getAttribute('href')?.slice(1);
                link.classList.toggle('active', href === cleanViewName);
            });
        } catch (err) {
            console.error('Routing error:', err);
            main.innerHTML = `
                <div class="container py-5 text-center">
                    <p class="text-danger">Failed to render view.</p>
                    <button type="button" class="btn btn-primary mt-2" onclick="window.state.navigate('home')">Go Home</button>
                </div>
            `;
        }
    }

    static showToast(message, type = 'info') {
        const container = document.getElementById('toast-container');
        if (!container) return;

        const toast = document.createElement('div');
        toast.className = `toast-item toast-${type} animate-toast`;
        
        const icons = {
            success: '✅',
            error: '⚠️',
            info: 'ℹ️'
        };

        toast.innerHTML = `
            <span class="toast-icon">${icons[type] || 'ℹ️'}</span>
            <span class="toast-msg">${message}</span>
        `;

        container.appendChild(toast);

        setTimeout(() => {
            toast.classList.add('toast-fade-out');
            setTimeout(() => toast.remove(), 300);
        }, 3500);
    }
}

// Global exposure for event callbacks
window.state = state;

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    App.init();
});
