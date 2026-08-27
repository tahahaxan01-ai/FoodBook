/**
 * FoodBook Home / Landing View
 */
import { api } from '../api.js';
import { state } from '../state.js';
import { CONFIG } from '../config.js';

export class HomeView {
    static async render() {
        return `
        <div class="home-view">
            <!-- HERO & PROMO SECTION -->
            <section class="hero-section">
                <div class="hero-bg-shapes">
                    <div class="glow-orb orb-1"></div>
                    <div class="glow-orb orb-2"></div>
                </div>

                <div class="container hero-content text-center">
                    <div class="hero-badge animate-fade-in">
                        <span class="sparkle">✨</span> AI-Powered Personalized Food Discovery
                    </div>

                    <h1 class="hero-title animate-fade-in-up">
                        Discover Food That Matches <br>
                        <span class="gradient-text">YOUR Unique Taste.</span>
                    </h1>

                    <p class="hero-subtitle animate-fade-in-up delay-1">
                        Find top dining spots and authentic dishes tailored to your <strong>9-dimensional flavor profile</strong>.
                    </p>

                    <!-- SEARCH BAR -->
                    <div class="hero-search-box animate-fade-in-up delay-2">
                        <div class="search-input-wrapper">
                            <span class="search-icon">🔍</span>
                            <input type="text" id="hero-search-input" class="hero-search-input" 
                                placeholder="Search by food, cuisine, or try: 'creamy spicy pasta under 1500'...">
                        </div>
                        <button class="btn btn-primary hero-search-btn" id="hero-search-submit">
                            <span>Explore Food</span>
                        </button>
                    </div>

                    <!-- POPULAR CUISINE PILLS -->
                    <div class="hero-cuisines-row animate-fade-in-up delay-3">
                        <span class="cuisines-label">Popular Cuisines:</span>
                        <div class="cuisine-chips-list">
                            ${CONFIG.CUISINES.slice(0, 8).map(c => `
                                <button class="cuisine-pill" data-cuisine="${c.name}">
                                    <span class="pill-icon">${c.icon}</span>
                                    <span class="pill-name">${c.name}</span>
                                </button>
                            `).join('')}
                        </div>
                    </div>
                </div>
            </section>

            <!-- SPECIAL OFFERS & PROMO BANNER CAROUSEL (Mobile & Desktop App Look) -->
            <section class="container mb-5">
                <div class="offers-carousel">
                    <div class="offer-banner-card banner-green">
                        <div class="offer-text">
                            <span class="offer-badge">SPECIAL OFFER</span>
                            <h3 class="offer-heading">30% DISCOUNT</h3>
                            <p class="offer-sub">Exclusive dine-in deals at top Lahore spots!</p>
                            <a href="#explore" class="btn btn-sm btn-white mt-2">Explore Deals →</a>
                        </div>
                        <div class="offer-emoji">🍔</div>
                    </div>

                    <div class="offer-banner-card banner-orange">
                        <div class="offer-text">
                            <span class="offer-badge">FLAVOR MATCH</span>
                            <h3 class="offer-heading">9D TASTE QUIZ</h3>
                            <p class="offer-sub">Tune your spice, creaminess & smoke preferences</p>
                            <a href="#onboarding" class="btn btn-sm btn-white mt-2">Start Quiz →</a>
                        </div>
                        <div class="offer-emoji">🎯</div>
                    </div>
                </div>
            </section>

            <!-- PERSONALIZED RECOMMENDATIONS SECTION -->
            <section class="home-section container" id="home-recommendations-section">
                <div class="section-header">
                    <div>
                        <div class="section-badge">🎯 Tailored For You</div>
                        <h2 class="section-title">Personalized Taste Matches</h2>
                        <p class="section-subtitle">Ranked by 9D vector cosine similarity & cuisine preferences.</p>
                    </div>
                    <a href="#explore" class="section-link">View All Spots →</a>
                </div>

                <div class="restaurants-grid" id="home-recs-grid">
                    <div class="loading-state">
                        <div class="spinner"></div>
                        <p>Generating personalized recommendations...</p>
                    </div>
                </div>
            </section>

            <!-- POPULAR IN LAHORE SECTION -->
            <section class="home-section container">
                <div class="section-header">
                    <div>
                        <div class="section-badge">🔥 Trending Spots</div>
                        <h2 class="section-title">Popular Restaurants in Lahore</h2>
                        <p class="section-subtitle">Top verified dining establishments with rich taste profiles.</p>
                    </div>
                    <a href="#explore" class="section-link">Explore Map & List →</a>
                </div>

                <div class="restaurants-grid" id="home-trending-grid">
                    <div class="loading-state">
                        <div class="spinner"></div>
                        <p>Loading Lahore food spots...</p>
                    </div>
                </div>
            </section>

            <!-- COMMUNITY COLLECTIONS SECTION -->
            <section class="home-section container">
                <div class="section-header">
                    <div>
                        <div class="section-badge">📚 Curated Guides</div>
                        <h2 class="section-title">FoodBook Community Collections</h2>
                        <p class="section-subtitle">Handpicked food routes curated by local foodies.</p>
                    </div>
                    <a href="#collections" class="section-link">Browse All Guides →</a>
                </div>

                <div class="collections-grid" id="home-collections-grid">
                    <div class="loading-state">
                        <div class="spinner"></div>
                        <p>Loading collections...</p>
                    </div>
                </div>
            </section>

            <!-- CTA SECTION -->
            <section class="home-cta-section container mb-5">
                <div class="cta-banner">
                    <div class="cta-content">
                        <h2 class="cta-title">Ready to discover your true food taste?</h2>
                        <p class="cta-subtitle">Set up your 9-dimensional taste preferences and unlock hyper-personalized food recommendations today.</p>
                        <a href="#onboarding" class="btn btn-primary btn-lg">Set Up Your Taste Profile 🚀</a>
                    </div>
                </div>
            </section>
        </div>
        `;
    }

    static async attachEvents() {
        // Search submit
        const searchInput = document.getElementById('hero-search-input');
        const searchBtn = document.getElementById('hero-search-submit');

        function triggerSearch() {
            const val = searchInput?.value?.trim();
            if (val) {
                if (val.split(' ').length > 2 || val.includes('under') || val.includes('near') || val.includes('creamy') || val.includes('spicy')) {
                    state.navigate('ai-search', { q: val });
                } else {
                    state.navigate('explore', { search: val });
                }
            } else {
                state.navigate('explore');
            }
        }

        if (searchBtn) searchBtn.addEventListener('click', triggerSearch);
        if (searchInput) {
            searchInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') triggerSearch();
            });
        }

        // Cuisine pills click
        document.querySelectorAll('.cuisine-pill').forEach(pill => {
            pill.addEventListener('click', () => {
                const cuisine = pill.getAttribute('data-cuisine');
                state.navigate('explore', { cuisine });
            });
        });

        // Load dynamic data in parallel
        HomeView.loadRecommendations();
        HomeView.loadTrendingRestaurants();
        HomeView.loadCollections();
    }

    static async loadRecommendations() {
        const container = document.getElementById('home-recs-grid');
        if (!container) return;

        try {
            const loc = state.currentLocation;
            const res = await api.getRecommendations({
                latitude: loc.latitude,
                longitude: loc.longitude,
                limit: 6
            });

            const recs = res?.data?.recommendations || [];

            if (recs.length === 0) {
                container.innerHTML = `
                    <div class="empty-state-box col-span-full">
                        <div class="empty-icon">🍽️</div>
                        <h3>No recommendations yet</h3>
                        <p class="text-muted">Take our 60-second taste quiz to train your recommendation engine!</p>
                        <a href="#onboarding" class="btn btn-primary mt-3">Start Taste Quiz</a>
                    </div>
                `;
                return;
            }

            container.innerHTML = recs.map(item => HomeView.renderRecommendationCard(item)).join('');
            HomeView.attachCardEvents(container);
        } catch (err) {
            console.error('Failed to load recommendations:', err);
            container.innerHTML = `
                <div class="empty-state-box col-span-full">
                    <p class="text-muted">Explore our trending food spots below.</p>
                </div>
            `;
        }
    }

    static async loadTrendingRestaurants() {
        const container = document.getElementById('home-trending-grid');
        if (!container) return;

        try {
            const res = await api.getRestaurants({ limit: 6 });
            const list = res?.data?.items || [];

            if (list.length === 0) {
                container.innerHTML = `<p class="text-muted col-span-full">No restaurants found.</p>`;
                return;
            }

            container.innerHTML = list.map(r => HomeView.renderStandardRestaurantCard(r)).join('');
            HomeView.attachCardEvents(container);
        } catch (err) {
            container.innerHTML = `<p class="text-danger col-span-full">Failed to load food spots.</p>`;
        }
    }

    static async loadCollections() {
        const container = document.getElementById('home-collections-grid');
        if (!container) return;

        try {
            const res = await api.getCollections(true);
            const collections = (res?.data || []).slice(0, 4);

            if (collections.length === 0) {
                container.innerHTML = `
                    <div class="col-card-sample" onclick="window.state.navigate('collections')">
                        <div class="col-card-banner">🍢 BBQ & Karahi</div>
                        <div class="col-card-body">
                            <h4>Best Desi Spots in Lahore</h4>
                            <p class="text-muted">Bundu Khan, Monal, Haveli & more</p>
                        </div>
                    </div>
                    <div class="col-card-sample" onclick="window.state.navigate('collections')">
                        <div class="col-card-banner">🍔 Fast Food Craze</div>
                        <div class="col-card-body">
                            <h4>Cheesy Crust & Burgers</h4>
                            <p class="text-muted">Cheezious, Howdy, Johnny & Jugnu</p>
                        </div>
                    </div>
                `;
                return;
            }

            container.innerHTML = collections.map(col => `
                <div class="collection-card" data-col-id="${col.id}">
                    <div class="col-header-bg">
                        <span class="col-emoji">📚</span>
                    </div>
                    <div class="col-body">
                        <h4 class="col-title">${col.title}</h4>
                        <p class="col-desc">${col.description || 'Curated food selection.'}</p>
                        <div class="col-footer">
                            <span class="col-places-count">${col.items_count || 0} spots</span>
                            <span class="col-explore-link">Explore Guide →</span>
                        </div>
                    </div>
                </div>
            `).join('');

            container.querySelectorAll('.collection-card').forEach(card => {
                card.addEventListener('click', () => {
                    const colId = card.getAttribute('data-col-id');
                    state.navigate('collections', { id: colId });
                });
            });
        } catch (err) {
            console.debug('Collections load note:', err);
        }
    }

    static renderRecommendationCard(item) {
        const r = item.restaurant;
        const matchPct = item.match_percentage || 90;
        const reasons = item.reasons || ["High taste profile match"];
        const isSaved = state.isRestaurantSaved(r.id);
        const distanceStr = item.distance_meters 
            ? `${(item.distance_meters / 1000).toFixed(1)} km away` 
            : (r.city || "Lahore");

        const heroImg = CONFIG.getRestaurantImage(r);
        const desc = CONFIG.getRestaurantDescription(r);

        return `
        <div class="restaurant-card rec-card animate-card" data-id="${r.id}">
            <div class="card-img-wrapper">
                <img src="${heroImg}" alt="${r.name}" class="card-img" loading="lazy">
                
                <!-- 9D Match Badge -->
                <div class="taste-match-badge">
                    <span class="badge-icon">⚡</span>
                    <span class="badge-pct">${matchPct}% Match</span>
                </div>

                <!-- Save Action Button -->
                <button class="save-bookmark-btn ${isSaved ? 'saved' : ''}" data-rest-id="${r.id}" title="Save Restaurant" aria-label="Save Restaurant">
                    <span>${isSaved ? '❤️' : '🤍'}</span>
                </button>
            </div>

            <div class="card-body">
                <div class="card-title-row">
                    <h3 class="restaurant-name">${r.name}</h3>
                    <div class="restaurant-rating">
                        <span class="star-icon">⭐</span>
                        <span class="rating-val">${r.avg_rating ? Number(r.avg_rating).toFixed(1) : '4.5'}</span>
                    </div>
                </div>

                <div class="card-meta-row">
                    <span class="cuisine-tags">${(r.cuisines || ['Fast Food', 'Pakistani']).slice(0, 2).join(' • ')}</span>
                    <span class="meta-dot">•</span>
                    <span class="price-range">${r.avg_price_per_person ? 'Rs. ' + r.avg_price_per_person : '$$'}</span>
                    <span class="meta-dot">•</span>
                    <span class="distance-tag">📍 ${distanceStr}</span>
                </div>

                <p class="card-desc">${desc.slice(0, 85)}...</p>

                <!-- Explainability Reasons Banner -->
                <div class="rec-reasons-box">
                    <span class="reason-icon">💡</span>
                    <span class="reason-text">${reasons[0]}</span>
                </div>

                <div class="card-footer-actions">
                    <button type="button" class="btn btn-outline btn-sm btn-block view-details-btn" data-id="${r.id}">
                        View Profile & Menu
                    </button>
                </div>
            </div>
        </div>
        `;
    }

    static renderStandardRestaurantCard(r) {
        const isSaved = state.isRestaurantSaved(r.id);
        const heroImg = CONFIG.getRestaurantImage(r);
        const desc = CONFIG.getRestaurantDescription(r);

        return `
        <div class="restaurant-card animate-card" data-id="${r.id}">
            <div class="card-img-wrapper">
                <img src="${heroImg}" alt="${r.name}" class="card-img" loading="lazy">
                <button class="save-bookmark-btn ${isSaved ? 'saved' : ''}" data-rest-id="${r.id}" title="Save Restaurant" aria-label="Save Restaurant">
                    <span>${isSaved ? '❤️' : '🤍'}</span>
                </button>
            </div>

            <div class="card-body">
                <div class="card-title-row">
                    <h3 class="restaurant-name">${r.name}</h3>
                    <div class="restaurant-rating">
                        <span class="star-icon">⭐</span>
                        <span class="rating-val">${r.avg_rating ? Number(r.avg_rating).toFixed(1) : '4.5'}</span>
                    </div>
                </div>

                <div class="card-meta-row">
                    <span class="cuisine-tags">${(r.cuisines || ['Fast Food', 'Pakistani']).slice(0, 2).join(' • ')}</span>
                    <span class="meta-dot">•</span>
                    <span class="price-range">${r.avg_price_per_person ? 'Rs. ' + r.avg_price_per_person : '$$'}</span>
                    <span class="meta-dot">•</span>
                    <span class="distance-tag">📍 ${r.city || 'Lahore'}</span>
                </div>

                <p class="card-desc">${desc.slice(0, 85)}...</p>

                <div class="card-footer-actions">
                    <button type="button" class="btn btn-outline btn-sm btn-block view-details-btn" data-id="${r.id}">
                        View Profile & Menu
                    </button>
                </div>
            </div>
        </div>
        `;
    }

    static attachCardEvents(container) {
        // View details click
        container.querySelectorAll('.view-details-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                const id = btn.getAttribute('data-id');
                state.navigate('restaurant', { id });
            });
        });

        container.querySelectorAll('.restaurant-card').forEach(card => {
            card.addEventListener('click', (e) => {
                if (e.target.closest('.save-bookmark-btn') || e.target.closest('.view-details-btn')) return;
                const id = card.getAttribute('data-id');
                state.navigate('restaurant', { id });
            });
        });

        // Save bookmark click
        container.querySelectorAll('.save-bookmark-btn').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                e.preventDefault();
                e.stopPropagation();
                const id = btn.getAttribute('data-rest-id');
                const nowSaved = await state.toggleSaveRestaurant(id);
                btn.classList.toggle('saved', nowSaved);
                btn.querySelector('span').textContent = nowSaved ? '❤️' : '🤍';
            });
        });
    }
}
