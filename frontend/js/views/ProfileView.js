/**
 * FoodBook User Profile View
 * Displays user 9D Taste Radar, Saved Restaurants, Personal Reviews, and Collections
 */
import { api } from '../api.js';
import { state } from '../state.js';
import { CONFIG } from '../config.js';
import { TasteRadar } from '../components/TasteRadar.js';

export class ProfileView {
    static async render() {
        const user = state.user;
        if (!user) {
            return `
            <div class="container py-5 text-center">
                <div class="empty-icon mb-3">👤</div>
                <h2>Sign in to view your profile</h2>
                <p class="text-muted">Access your personalized taste radar, saved dining spots, and reviews.</p>
                <button class="btn btn-primary mt-3" onclick="window.state.notify('openAuthModal', {tab: 'login'})">Sign In</button>
            </div>
            `;
        }

        const activeTab = state.viewParams.tab || 'taste';

        return `
        <div class="profile-view container py-5">
            <!-- PROFILE HEADER -->
            <div class="profile-header-card mb-4">
                <div class="profile-user-info">
                    <div class="profile-avatar-large">
                        <span>${(user.full_name || user.email || 'U')[0].toUpperCase()}</span>
                    </div>
                    <div class="profile-text">
                        <h2 class="profile-name">${user.full_name || 'Foodie'}</h2>
                        <p class="profile-email text-muted">${user.email}</p>
                        <div class="profile-badges mt-2">
                            <span class="badge-pill">🍽️ Food Explorer</span>
                            <span class="badge-pill">📍 Lahore, Pakistan</span>
                            <span class="badge-pill">⭐ ${state.savedRestaurantIds.size} Saved Spots</span>
                        </div>
                    </div>
                </div>

                <div class="profile-actions">
                    <a href="#onboarding" class="btn btn-primary">
                        <span>🎛️</span> Edit Taste Preferences
                    </a>
                </div>
            </div>

            <!-- TABS NAVIGATION -->
            <div class="profile-tabs-bar mb-4">
                <button class="profile-tab-btn ${activeTab === 'taste' ? 'active' : ''}" data-tab="taste">
                    <span>🎯</span> 9D Taste Radar
                </button>
                <button class="profile-tab-btn ${activeTab === 'saved' ? 'active' : ''}" data-tab="saved">
                    <span>❤️</span> Saved Restaurants (${state.savedRestaurantIds.size})
                </button>
                <button class="profile-tab-btn ${activeTab === 'reviews' ? 'active' : ''}" data-tab="reviews">
                    <span>✍️</span> My Reviews
                </button>
                <button class="profile-tab-btn ${activeTab === 'collections' ? 'active' : ''}" data-tab="collections">
                    <span>📚</span> My Collections
                </button>
            </div>

            <!-- TAB CONTENT PANELS -->
            <div class="profile-tab-content" id="profile-tab-content">
                <div class="loading-state text-center py-4">
                    <div class="spinner"></div>
                    <p>Loading profile details...</p>
                </div>
            </div>
        </div>
        `;
    }

    static async attachEvents() {
        if (!state.user) return;

        const contentContainer = document.getElementById('profile-tab-content');
        const tabBtns = document.querySelectorAll('.profile-tab-btn');
        let currentTab = state.viewParams.tab || 'taste';

        function switchTab(tab) {
            currentTab = tab;
            tabBtns.forEach(b => {
                b.classList.toggle('active', b.getAttribute('data-tab') === tab);
            });

            if (tab === 'taste') ProfileView.renderTasteTab(contentContainer);
            else if (tab === 'saved') ProfileView.renderSavedTab(contentContainer);
            else if (tab === 'reviews') ProfileView.renderReviewsTab(contentContainer);
            else if (tab === 'collections') ProfileView.renderCollectionsTab(contentContainer);
        }

        tabBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                const tab = btn.getAttribute('data-tab');
                switchTab(tab);
            });
        });

        // Initial tab render
        switchTab(currentTab);
    }

    static async renderTasteTab(container) {
        const taste = state.tasteProfile;
        const vector = taste?.taste_vector || [0.7, 0.3, 0.6, 0.3, 0.8, 0.7, 0.6, 0.8, 0.7];
        const cuisines = taste?.preferred_cuisines || ["Pakistani", "BBQ", "Pizza"];
        const dietary = taste?.dietary_restrictions || ["Halal"];
        const budget = taste?.budget_level || "moderate";

        container.innerHTML = `
        <div class="taste-tab-grid">
            <div class="content-card">
                <div class="card-header-flex mb-3">
                    <h3 class="card-title">Your 9D Flavor Vector</h3>
                    <a href="#onboarding" class="btn btn-sm btn-outline">Update Vectors</a>
                </div>
                <div class="profile-radar-box">
                    <canvas id="profile-radar-canvas"></canvas>
                </div>
            </div>

            <div class="content-card">
                <h3 class="card-title mb-4">Preference Summary</h3>
                
                <div class="pref-block mb-3">
                    <label class="text-muted small">Preferred Cuisines</label>
                    <div class="chips-list mt-1">
                        ${cuisines.map(c => `<span class="filter-chip active">${c}</span>`).join('')}
                    </div>
                </div>

                <div class="pref-block mb-3">
                    <label class="text-muted small">Dietary Guidelines</label>
                    <div class="chips-list mt-1">
                        ${dietary.map(d => `<span class="filter-chip active">${d}</span>`).join('')}
                    </div>
                </div>

                <div class="pref-block mb-3">
                    <label class="text-muted small">Budget Level</label>
                    <div class="mt-1"><strong>${budget.toUpperCase()}</strong></div>
                </div>

                <div class="dimension-breakdown-list mt-4">
                    <h4 class="small text-muted mb-2">Dimension Breakdown</h4>
                    ${CONFIG.TASTE_DIMENSIONS.map((dim, idx) => `
                        <div class="dim-row small py-1">
                            <span>${dim.emoji} ${dim.name}</span>
                            <strong>${Math.round((vector[idx] || 0.5) * 100)}%</strong>
                        </div>
                    `).join('')}
                </div>
            </div>
        </div>
        `;

        const canvas = document.getElementById('profile-radar-canvas');
        if (canvas) {
            TasteRadar.render(canvas, {
                userVector: vector,
                restaurantVector: null,
                restaurantName: "Your Palate"
            });
        }
    }

    static async renderSavedTab(container) {
        container.innerHTML = `<div class="loading-state"><div class="spinner"></div><p>Loading saved restaurants...</p></div>`;
        try {
            const res = await api.getSavedRestaurants();
            const items = res?.data?.items || [];

            if (items.length === 0) {
                container.innerHTML = `
                    <div class="empty-state-box text-center py-5">
                        <div class="empty-icon">🤍</div>
                        <h3>No saved places yet</h3>
                        <p class="text-muted">Click the heart icon on any restaurant to save it to your personal food list.</p>
                        <a href="#explore" class="btn btn-primary mt-3">Discover Spots</a>
                    </div>
                `;
                return;
            }

            container.innerHTML = `
                <div class="restaurants-grid">
                    ${items.map(item => `
                        <div class="restaurant-card" data-id="${item.restaurant_id}">
                            <div class="card-img-wrapper">
                                <img src="${CONFIG.getRestaurantImage(item.restaurant)}" class="card-img" alt="${item.restaurant?.name || 'Restaurant'}">
                                <button class="save-bookmark-btn saved" data-rest-id="${item.restaurant_id}" title="Remove">
                                    <span>❤️</span>
                                </button>
                            </div>
                            <div class="card-body">
                                <h3 class="restaurant-name">${item.restaurant?.name || 'Restaurant'}</h3>
                                <p class="card-meta-row">${(item.restaurant?.cuisines || []).join(' • ')}</p>
                                <button class="btn btn-outline btn-sm btn-block mt-2" onclick="window.state.navigate('restaurant', {id: '${item.restaurant_id}'})">
                                    View Profile & Menu
                                </button>
                            </div>
                        </div>
                    `).join('')}
                </div>
            `;

            container.querySelectorAll('.save-bookmark-btn').forEach(btn => {
                btn.addEventListener('click', async (e) => {
                    e.stopPropagation();
                    const id = btn.getAttribute('data-rest-id');
                    await state.toggleSaveRestaurant(id);
                    ProfileView.renderSavedTab(container);
                });
            });
        } catch (err) {
            container.innerHTML = `<p class="text-danger">Failed to load saved restaurants.</p>`;
        }
    }

    static async renderReviewsTab(container) {
        container.innerHTML = `<div class="loading-state"><div class="spinner"></div><p>Loading your reviews...</p></div>`;
        try {
            const res = await api.getMyReviews();
            const reviews = res?.data?.items || [];

            if (reviews.length === 0) {
                container.innerHTML = `
                    <div class="empty-state-box text-center py-5">
                        <div class="empty-icon">✍️</div>
                        <h3>You haven't written any reviews yet</h3>
                        <p class="text-muted">Rate your food experiences to help the community and improve your taste AI model.</p>
                        <a href="#explore" class="btn btn-primary mt-3">Find Places to Review</a>
                    </div>
                `;
                return;
            }

            container.innerHTML = `
                <div class="reviews-list">
                    ${reviews.map(rev => `
                        <div class="review-item-card content-card mb-3">
                            <div class="review-header">
                                <div>
                                    <h4 class="reviewer-name">${rev.restaurant?.name || 'Restaurant Review'}</h4>
                                    <div class="review-date">${rev.created_at ? new Date(rev.created_at).toLocaleDateString() : 'Recent'}</div>
                                </div>
                                <div class="review-rating-stars">
                                    <span>⭐ ${Number(rev.overall_rating).toFixed(1)}</span>
                                </div>
                            </div>
                            <p class="review-text-content mt-2">${rev.review_text}</p>
                            <div class="review-footer-row mt-3">
                                <button class="btn btn-sm btn-outline text-danger delete-rev-btn" data-rev-id="${rev.id}">
                                    Delete Review
                                </button>
                            </div>
                        </div>
                    `).join('')}
                </div>
            `;

            container.querySelectorAll('.delete-rev-btn').forEach(btn => {
                btn.addEventListener('click', async () => {
                    const id = btn.getAttribute('data-rev-id');
                    if (confirm("Are you sure you want to delete this review?")) {
                        try {
                            await api.deleteReview(id);
                            state.notify('toast', { type: 'info', message: 'Review deleted.' });
                            ProfileView.renderReviewsTab(container);
                        } catch (err) {
                            state.notify('toast', { type: 'error', message: 'Failed to delete review' });
                        }
                    }
                });
            });
        } catch (err) {
            container.innerHTML = `<p class="text-danger">Failed to load reviews.</p>`;
        }
    }

    static async renderCollectionsTab(container) {
        container.innerHTML = `<div class="loading-state"><div class="spinner"></div><p>Loading collections...</p></div>`;
        try {
            const res = await api.getCollections(false);
            const collections = res?.data || [];

            container.innerHTML = `
                <div class="collections-tab-wrapper">
                    <div class="card-header-flex mb-4">
                        <h3>Your Curated Collections</h3>
                        <button class="btn btn-primary" onclick="window.state.notify('openCreateCollectionModal')">
                            + Create New Collection
                        </button>
                    </div>

                    ${collections.length > 0 ? `
                        <div class="collections-grid">
                            ${collections.map(col => `
                                <div class="collection-card" onclick="window.location.hash='#collections/${col.id}'">
                                    <div class="col-header-bg">
                                        <span class="col-emoji">📚</span>
                                    </div>
                                    <div class="col-body">
                                        <h4 class="col-title">${col.title}</h4>
                                        <p class="col-desc">${col.description || 'Curated food selection'}</p>
                                        <div class="col-footer">
                                            <span class="col-places-count">${col.items_count || 0} spots</span>
                                            <span class="col-explore-link">View List →</span>
                                        </div>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    ` : `
                        <div class="empty-state-box text-center py-5">
                            <div class="empty-icon">📚</div>
                            <h3>No collections created yet</h3>
                            <p class="text-muted">Create collections like "Best Late Night Burgers" or "Family Dinner Spots".</p>
                            <button class="btn btn-primary mt-3" onclick="window.state.notify('openCreateCollectionModal')">
                                Create Your First Collection
                            </button>
                        </div>
                    `}
                </div>
            `;
        } catch (err) {
            container.innerHTML = `<p class="text-danger">Failed to load collections.</p>`;
        }
    }
}
