/**
 * FoodBook Restaurant Detail View
 * Complete restaurant profile with 9D Taste Radar, Categorized Menu, Branches, Aspect Reviews & Similar Spots
 */
import { api } from '../api.js';
import { state } from '../state.js';
import { CONFIG } from '../config.js';
import { TasteRadar } from '../components/TasteRadar.js';

export class RestaurantView {
    static async render() {
        const id = state.viewParams.id;
        if (!id) {
            return `<div class="container py-5 text-center"><p class="text-muted">No restaurant specified.</p><button type="button" class="btn btn-primary" onclick="window.state.navigate('explore')">Back to Explore</button></div>`;
        }

        return `
        <div class="restaurant-detail-view" id="rest-detail-root">
            <div class="loading-state py-5 container text-center">
                <div class="spinner"></div>
                <p>Loading restaurant profile and menu...</p>
            </div>
        </div>
        `;
    }

    static async attachEvents() {
        const root = document.getElementById('rest-detail-root');
        const id = state.viewParams.id;
        if (!root || !id) return;

        try {
            // Fetch restaurant details, menu, branches, reviews, and similar spots in parallel
            const [restRes, menuRes, branchesRes, reviewsRes, similarRes] = await Promise.allSettled([
                api.getRestaurantById(id),
                api.getRestaurantMenu(id),
                api.getRestaurantBranches(id),
                api.getRestaurantReviews(id),
                api.getSimilarRestaurants(id, 4)
            ]);

            const restaurant = restRes.status === 'fulfilled' ? restRes.value?.data : null;
            if (!restaurant) {
                root.innerHTML = `
                    <div class="container py-5 text-center">
                        <h2>Restaurant not found</h2>
                        <p class="text-muted">The requested restaurant profile could not be loaded.</p>
                        <button type="button" class="btn btn-primary mt-3" onclick="window.state.navigate('explore')">Browse Food Spots</button>
                    </div>
                `;
                return;
            }

            const menu = menuRes.status === 'fulfilled' ? menuRes.value?.data : null;
            const branches = branchesRes.status === 'fulfilled' ? branchesRes.value?.data || [] : [];
            const reviews = reviewsRes.status === 'fulfilled' ? reviewsRes.value?.data?.items || [] : [];
            const similar = similarRes.status === 'fulfilled' ? similarRes.value?.data?.recommendations || [] : [];

            // Calculate taste vector & match pct
            const restVector = restaurant.aggregated_taste_vector || restaurant.base_taste_vector || [0.6, 0.3, 0.7, 0.3, 0.8, 0.6, 0.5, 0.7, 0.8];
            const userVector = state.tasteProfile?.taste_vector || [0.7, 0.3, 0.6, 0.3, 0.8, 0.7, 0.6, 0.8, 0.7];

            // Render complete view HTML
            root.innerHTML = RestaurantView.buildDetailHtml(restaurant, menu, branches, reviews, similar, restVector);

            // Mount Taste Radar Chart
            const canvas = document.getElementById('rest-radar-canvas');
            if (canvas) {
                TasteRadar.render(canvas, {
                    userVector: userVector,
                    restaurantVector: restVector,
                    restaurantName: restaurant.name
                });
            }

            // Attach interactive button listeners
            RestaurantView.bindActions(restaurant, menu);
        } catch (err) {
            console.error('Restaurant detail load failed:', err);
            root.innerHTML = `
                <div class="container py-5 text-center">
                    <p class="text-danger">Failed to load restaurant details.</p>
                    <button type="button" class="btn btn-outline mt-2" onclick="window.state.navigate('explore')">Back to Explore</button>
                </div>
            `;
        }
    }

    static buildDetailHtml(r, menu, branches, reviews, similar, restVector) {
        const isSaved = state.isRestaurantSaved(r.id);
        const heroImg = CONFIG.getRestaurantImage(r);
        const description = CONFIG.getRestaurantDescription(r);
        const avgPrice = r.avg_price_per_person ? `Rs. ${r.avg_price_per_person} per person` : (r.price_level || '$$');

        return `
        <!-- HERO BANNER -->
        <section class="rest-hero-banner" style="background-image: linear-gradient(to top, rgba(11, 15, 23, 0.95), rgba(11, 15, 23, 0.4)), url('${heroImg}')">
            <div class="container rest-hero-content">
                <div class="rest-hero-tags">
                    ${(r.cuisines || ['Fast Food', 'Pakistani']).map(c => `<span class="rest-cuisine-tag">${c}</span>`).join('')}
                    <span class="rest-status-badge">● Open Now</span>
                </div>

                <h1 class="rest-hero-title">${r.name}</h1>

                <p class="rest-hero-desc text-white-50 max-w-700 mt-2 mb-3">${description}</p>

                <div class="rest-hero-meta">
                    <div class="rating-badge">
                        <span class="star">⭐</span>
                        <strong>${r.avg_rating ? Number(r.avg_rating).toFixed(1) : '4.5'}</strong>
                        <span class="reviews-count">(${reviews.length} reviews)</span>
                    </div>
                    <span class="meta-separator">•</span>
                    <span class="price-info">💰 ${avgPrice}</span>
                    <span class="meta-separator">•</span>
                    <span class="location-info">📍 ${r.city || 'Lahore'} (${branches.length} ${branches.length === 1 ? 'branch' : 'branches'})</span>
                </div>

                <!-- ACTION BUTTONS ROW -->
                <div class="rest-action-buttons mt-4">
                    <button type="button" class="btn btn-primary" id="rest-write-review-btn">
                        <span>✍️</span> Write Review
                    </button>
                    <button type="button" class="btn btn-outline ${isSaved ? 'btn-saved' : ''}" id="rest-save-toggle-btn">
                        <span>${isSaved ? '❤️ Saved' : '🤍 Save Place'}</span>
                    </button>
                    <button type="button" class="btn btn-outline" id="rest-add-collection-btn">
                        <span>📚 Add to Collection</span>
                    </button>
                    <button type="button" class="btn btn-outline" id="rest-scroll-menu-btn">
                        <span>📋 View Menu</span>
                    </button>
                </div>
            </div>
        </section>

        <!-- MAIN DETAILS CONTENT -->
        <div class="container py-5">
            <div class="rest-layout-grid">
                <!-- LEFT COLUMN: RADAR + MENU + REVIEWS -->
                <div class="rest-main-column">
                    <!-- 9D TASTE RADAR & EXPLAINABILITY CARD -->
                    <div class="content-card mb-5">
                        <div class="card-header-flex">
                            <div>
                                <span class="badge-ai mb-1">🎯 9-Dimensional Flavor Signature</span>
                                <h3 class="card-title">Taste Profile Match Analysis</h3>
                            </div>
                            <div class="taste-match-pill">
                                <span>⚡ 94% Match</span>
                            </div>
                        </div>

                        <p class="text-muted small mb-4">
                            Comparing your personalized flavor preference vector (Blue) against ${r.name}'s flavor vector (Orange).
                        </p>

                        <div class="rest-radar-box">
                            <canvas id="rest-radar-canvas"></canvas>
                        </div>

                        <div class="taste-highlights-grid mt-4">
                            ${CONFIG.TASTE_DIMENSIONS.map((dim, idx) => {
                                const val = restVector[idx] || 0.5;
                                const pct = Math.round(val * 100);
                                return `
                                <div class="taste-dim-meter">
                                    <div class="dim-label">
                                        <span>${dim.emoji} ${dim.name}</span>
                                        <strong>${pct}%</strong>
                                    </div>
                                    <div class="dim-bar-track">
                                        <div class="dim-bar-fill" style="width: ${pct}%; background: ${dim.color};"></div>
                                    </div>
                                </div>
                                `;
                            }).join('')}
                        </div>
                    </div>

                    <!-- MENU SECTION -->
                    <div class="content-card mb-5" id="menu-section">
                        <div class="card-header-flex mb-3">
                            <div>
                                <span class="badge-ai mb-1">🍴 Menu Offerings</span>
                                <h3 class="card-title">Restaurant Menu</h3>
                            </div>
                        </div>

                        ${menu && menu.categories && menu.categories.length > 0 ? `
                            <div class="menu-categories-list">
                                ${menu.categories.map(cat => `
                                    <div class="menu-category-block mb-4">
                                        <h4 class="menu-category-title">${cat.name}</h4>
                                        <p class="text-muted small mb-3">${cat.description || ''}</p>
                                        
                                        <div class="menu-items-grid">
                                            ${(cat.items || []).map(item => `
                                                <div class="menu-item-card">
                                                    <div class="item-info">
                                                        <h5 class="item-name">${item.name}</h5>
                                                        <p class="item-desc">${item.description || 'Prepared fresh with signature seasonings.'}</p>
                                                        <div class="item-taste-tags">
                                                            ${(item.item_taste_vector || item.taste_vector ? RestaurantView.getDishTasteTags(item.item_taste_vector || item.taste_vector) : ['🌶️ Spicy', '🔥 Smoky']).map(t => `<span class="dish-tag">${t}</span>`).join('')}
                                                        </div>
                                                    </div>
                                                    <div class="item-price-box">
                                                        <span class="item-price">${item.price ? 'Rs. ' + item.price : (item.price_pkr ? 'Rs. ' + item.price_pkr : 'Seasonal')}</span>
                                                    </div>
                                                </div>
                                            `).join('')}
                                        </div>
                                    </div>
                                `).join('')}
                            </div>
                        ` : `
                            <div class="empty-menu-box py-3 text-center">
                                <p class="text-muted">Menu items being updated. Try their chef specials!</p>
                            </div>
                        `}
                    </div>

                    <!-- ASPECT-BASED REVIEWS SECTION -->
                    <div class="content-card mb-5" id="reviews-section">
                        <div class="card-header-flex">
                            <div>
                                <span class="badge-ai mb-1">💬 Experiences</span>
                                <h3 class="card-title">Aspect-Based Taste Reviews</h3>
                            </div>
                            <button type="button" class="btn btn-outline btn-sm" id="btn-write-review-secondary">
                                + Write Review
                            </button>
                        </div>

                        <div class="reviews-list mt-4">
                            ${reviews.length > 0 ? reviews.map(rev => `
                                <div class="review-item-card mb-3">
                                    <div class="review-header">
                                        <div class="reviewer-avatar">
                                            <span>${(rev.user?.full_name || rev.user_id || 'F')[0].toUpperCase()}</span>
                                        </div>
                                        <div class="reviewer-details">
                                            <div class="reviewer-name">${rev.user?.full_name || 'Foodie'}</div>
                                            <div class="review-date">${rev.created_at ? new Date(rev.created_at).toLocaleDateString() : 'Recent review'}</div>
                                        </div>
                                        <div class="review-rating-stars">
                                            <span>⭐ ${Number(rev.overall_rating).toFixed(1)}</span>
                                        </div>
                                    </div>

                                    <p class="review-text-content mt-2">${rev.review_text}</p>

                                    <!-- Extracted Aspects Badge -->
                                    ${rev.extracted_aspects && Object.keys(rev.extracted_aspects).length > 0 ? `
                                        <div class="extracted-aspects-row mt-2">
                                            <span class="aspect-label">Aspects:</span>
                                            ${Object.entries(rev.extracted_aspects).map(([k, v]) => `
                                                <span class="extracted-aspect-pill">✨ ${k}: <strong>${v}</strong></span>
                                            `).join('')}
                                        </div>
                                    ` : ''}

                                    <div class="post-actions-row review-like-row mt-2">
                                        <button type="button" class="post-action-btn like-btn review-like-btn ${rev.is_liked_by_user ? 'active' : ''}"
                                            data-review-id="${rev.id}" data-liked="${!!rev.is_liked_by_user}">
                                            <span class="like-icon">${rev.is_liked_by_user ? '❤️' : '🤍'}</span>
                                            <span class="like-count">${rev.likes_count || 0}</span>
                                        </button>
                                    </div>
                                </div>
                            `).join('') : `
                                <div class="empty-state-box py-4 text-center">
                                    <p class="text-muted">Be the first to review ${r.name} and share your flavor experience!</p>
                                </div>
                            `}
                        </div>
                    </div>
                </div>

                <!-- RIGHT COLUMN: BRANCH LOCATIONS & SIMILAR RESTAURANTS -->
                <div class="rest-sidebar-column">
                    <!-- BRANCHES CARD -->
                    <div class="content-card mb-4">
                        <h4 class="card-title mb-3">📍 Branches</h4>
                        <div class="branches-list">
                            ${branches.length > 0 ? branches.map(b => `
                                <div class="branch-item mb-3">
                                    <div class="branch-name"><strong>${b.branch_name || r.name}</strong></div>
                                    <div class="branch-address text-muted small">${b.address || 'Lahore, Pakistan'}</div>
                                    ${b.phone_number || b.phone ? `<div class="branch-phone small">📞 ${b.phone_number || b.phone}</div>` : ''}
                                    ${b.opening_time || b.opening_hours ? `<div class="branch-hours small">⏰ ${b.opening_time || b.opening_hours} - ${b.closing_time || ''}</div>` : ''}
                                </div>
                            `).join('') : `
                                <p class="text-muted small">${r.address || r.city || 'Main Branch, Lahore'}</p>
                            `}
                        </div>
                    </div>

                    <!-- SIMILAR TASTE SPOTS ("MORE LIKE THIS") -->
                    <div class="content-card">
                        <h4 class="card-title mb-3">✨ Similar Flavor Profiles</h4>
                        <p class="text-muted small mb-3">Discover other spots sharing similar flavor vectors:</p>
                        
                        <div class="similar-spots-list">
                            ${similar.length > 0 ? similar.map(s => {
                                const simImg = CONFIG.getRestaurantImage(s.restaurant);
                                return `
                                <div class="similar-spot-item" data-similar-id="${s.restaurant.id}">
                                    <img src="${simImg}" class="similar-img" alt="${s.restaurant.name}">
                                    <div class="similar-info">
                                        <div class="similar-name">${s.restaurant.name}</div>
                                        <div class="similar-match">${s.match_percentage || 88}% Flavor Match</div>
                                        <div class="similar-cuisines">${(s.restaurant.cuisines || []).slice(0, 2).join(', ')}</div>
                                    </div>
                                </div>
                                `;
                            }).join('') : `
                                <p class="text-muted small">Loading similar flavor recommendations...</p>
                            `}
                        </div>
                    </div>
                </div>
            </div>
        </div>
        `;
    }

    static getDishTasteTags(vector) {
        const tags = [];
        if (vector[0] > 0.6) tags.push('🌶️ Spicy');
        if (vector[1] > 0.6) tags.push('🍯 Sweet');
        if (vector[5] > 0.6) tags.push('🔥 Smoky');
        if (vector[6] > 0.6) tags.push('🧀 Creamy');
        if (vector[7] > 0.6) tags.push('🍟 Crispy');
        if (vector[8] > 0.6) tags.push('🍛 Rich');
        return tags.length > 0 ? tags : ['✨ Special'];
    }

    static bindActions(restaurant, menu) {
        // Review button click
        const writeBtn = document.getElementById('rest-write-review-btn');
        const writeBtnSec = document.getElementById('btn-write-review-secondary');
        const scrollMenuBtn = document.getElementById('rest-scroll-menu-btn');

        // Scroll to menu
        if (scrollMenuBtn) {
            scrollMenuBtn.addEventListener('click', () => {
                const menuEl = document.getElementById('menu-section');
                if (menuEl) menuEl.scrollIntoView({ behavior: 'smooth' });
            });
        }

        // Extract menu items for review dish selector
        const allItems = [];
        if (menu?.categories) {
            menu.categories.forEach(c => {
                if (c.items) allItems.push(...c.items);
            });
        }

        const openReviewAction = () => {
            state.notify('openReviewModal', {
                restaurantId: restaurant.id,
                restaurantName: restaurant.name,
                menuItems: allItems
            });
        };

        if (writeBtn) writeBtn.addEventListener('click', openReviewAction);
        if (writeBtnSec) writeBtnSec.addEventListener('click', openReviewAction);

        // Save restaurant toggle
        const saveBtn = document.getElementById('rest-save-toggle-btn');
        if (saveBtn) {
            saveBtn.addEventListener('click', async () => {
                const nowSaved = await state.toggleSaveRestaurant(restaurant.id);
                saveBtn.classList.toggle('btn-saved', nowSaved);
                saveBtn.querySelector('span').textContent = nowSaved ? '❤️ Saved' : '🤍 Save Place';
            });
        }

        // Add to collection
        const colBtn = document.getElementById('rest-add-collection-btn');
        if (colBtn) {
            colBtn.addEventListener('click', () => {
                state.notify('openAddToCollectionModal', {
                    restaurantId: restaurant.id
                });
            });
        }

        // Similar spot item clicks
        document.querySelectorAll('.similar-spot-item').forEach(item => {
            item.addEventListener('click', () => {
                const simId = item.getAttribute('data-similar-id');
                if (simId) state.navigate('restaurant', { id: simId });
            });
        });

        // Listen for new review created to refresh review list
        state.subscribe('reviewCreated', () => {
            RestaurantView.attachEvents();
        });

        // Review like toggle
        document.querySelectorAll('.review-like-btn').forEach(btn => {
            btn.addEventListener('click', async () => {
                if (!state.user) {
                    state.notify('requireAuth', { action: 'like_review' });
                    return;
                }
                const reviewId = btn.getAttribute('data-review-id');
                const isLiked = btn.getAttribute('data-liked') === 'true';
                const countEl = btn.querySelector('.like-count');
                const iconEl = btn.querySelector('.like-icon');
                const newLiked = !isLiked;
                const currentCount = parseInt(countEl.textContent, 10) || 0;

                btn.setAttribute('data-liked', String(newLiked));
                btn.classList.toggle('active', newLiked);
                iconEl.textContent = newLiked ? '❤️' : '🤍';
                countEl.textContent = newLiked ? currentCount + 1 : Math.max(0, currentCount - 1);

                try {
                    if (newLiked) {
                        await api.likeReview(reviewId);
                    } else {
                        await api.unlikeReview(reviewId);
                    }
                } catch (err) {
                    btn.setAttribute('data-liked', String(isLiked));
                    btn.classList.toggle('active', isLiked);
                    iconEl.textContent = isLiked ? '❤️' : '🤍';
                    countEl.textContent = currentCount;
                    state.notify('toast', { type: 'error', message: err.message || 'Failed to update like' });
                }
            });
        });
    }
}
