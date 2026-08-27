/**
 * FoodBook Explore & Restaurant Discovery View
 * Features Multi-Filter Search + Interactive Map Toggle + Radius Distance Filtering
 */
import { api } from '../api.js';
import { state } from '../state.js';
import { CONFIG } from '../config.js';
import { HomeView } from './HomeView.js';

export class ExploreView {
    static async render() {
        const initialSearch = state.viewParams.search || "";
        const initialCuisine = state.viewParams.cuisine || "";
        const locationName = state.currentLocation?.name || "Gulberg, Lahore";

        return `
        <div class="explore-view container py-4">
            <!-- EXPLORE HEADER -->
            <div class="explore-header mb-4">
                <div>
                    <h1 class="explore-title">Discover Food Spots</h1>
                    <p class="text-muted">Explore verified restaurants near <strong>${locationName}</strong> with 9D flavor profiles.</p>
                </div>

                <!-- VIEW MODE TOGGLE (GRID VS MAP) -->
                <div class="view-mode-toggle">
                    <button type="button" class="toggle-btn active" id="view-mode-grid" data-mode="grid">
                        <span>🍱</span> Grid
                    </button>
                    <button type="button" class="toggle-btn" id="view-mode-map" data-mode="map">
                        <span>🗺️</span> Map
                    </button>
                </div>
            </div>

            <!-- SEARCH & FILTERS BAR -->
            <div class="filters-panel mb-4">
                <div class="filters-main-row">
                    <!-- Search Input -->
                    <div class="search-input-box">
                        <span class="search-icon">🔍</span>
                        <input type="text" id="explore-search-input" class="form-control" 
                            placeholder="Search by restaurant name, dish, or area..." value="${initialSearch}">
                    </div>

                    <!-- Cuisine Dropdown Filter -->
                    <div class="filter-dropdown-box">
                        <select id="explore-cuisine-filter" class="form-control">
                            <option value="">All Cuisines</option>
                            ${CONFIG.CUISINES.map(c => `
                                <option value="${c.name}" ${initialCuisine.toLowerCase() === c.name.toLowerCase() ? 'selected' : ''}>
                                    ${c.icon} ${c.name}
                                </option>
                            `).join('')}
                        </select>
                    </div>

                    <!-- Budget Filter -->
                    <div class="filter-dropdown-box">
                        <select id="explore-budget-filter" class="form-control">
                            <option value="">Any Budget</option>
                            <option value="800">Under Rs. 800</option>
                            <option value="1500">Under Rs. 1,500</option>
                            <option value="3000">Under Rs. 3,000</option>
                        </select>
                    </div>

                    <!-- Rating Filter -->
                    <div class="filter-dropdown-box">
                        <select id="explore-rating-filter" class="form-control">
                            <option value="">Any Rating</option>
                            <option value="4.0">⭐ 4.0 & Above</option>
                            <option value="4.5">⭐ 4.5 & Above</option>
                        </select>
                    </div>

                    <!-- Distance Radius Filter -->
                    <div class="filter-dropdown-box">
                        <select id="explore-radius-filter" class="form-control">
                            <option value="">Distance (All)</option>
                            <option value="5000">Within 5 km</option>
                            <option value="10000">Within 10 km</option>
                            <option value="25000">Within 25 km</option>
                        </select>
                    </div>
                </div>

                <!-- QUICK CUISINE CHIPS -->
                <div class="quick-cuisine-row mt-3">
                    <span class="quick-label">Quick filter:</span>
                    <div class="quick-chips">
                        <button type="button" class="quick-chip ${!initialCuisine ? 'active' : ''}" data-cuisine="">All</button>
                        ${CONFIG.CUISINES.slice(0, 7).map(c => `
                            <button type="button" class="quick-chip ${initialCuisine.toLowerCase() === c.name.toLowerCase() ? 'active' : ''}" data-cuisine="${c.name}">
                                ${c.icon} ${c.name}
                            </button>
                        `).join('')}
                    </div>
                </div>
            </div>

            <!-- CONTENT WRAPPER (GRID VS MAP) -->
            <div class="explore-content-wrapper">
                <!-- GRID CONTAINER -->
                <div id="explore-grid-container" class="restaurants-grid">
                    <div class="loading-state col-span-full">
                        <div class="spinner"></div>
                        <p>Loading food spots...</p>
                    </div>
                </div>

                <!-- MAP CONTAINER -->
                <div id="explore-map-container" class="explore-map-box" style="display: none;">
                    <div class="map-layout">
                        <div class="map-sidebar" id="map-sidebar-list">
                            <!-- Populated with nearby spots -->
                        </div>
                        <div class="map-viewport" id="leaflet-map-element">
                            <!-- Leaflet.js mounted here -->
                        </div>
                    </div>
                </div>
            </div>
        </div>
        `;
    }

    static async attachEvents() {
        let currentMode = 'grid';
        let mapInstance = null;
        let mapMarkers = [];

        const gridContainer = document.getElementById('explore-grid-container');
        const mapContainer = document.getElementById('explore-map-container');
        const gridBtn = document.getElementById('view-mode-grid');
        const mapBtn = document.getElementById('view-mode-map');
        const searchInput = document.getElementById('explore-search-input');
        const cuisineFilter = document.getElementById('explore-cuisine-filter');
        const budgetFilter = document.getElementById('explore-budget-filter');
        const ratingFilter = document.getElementById('explore-rating-filter');
        const radiusFilter = document.getElementById('explore-radius-filter');

        async function fetchFilteredRestaurants() {
            const search = searchInput?.value?.trim() || null;
            const cuisine = cuisineFilter?.value || null;
            const maxBudget = budgetFilter?.value || null;
            const minRating = ratingFilter?.value || null;
            const radius = radiusFilter?.value || null;

            gridContainer.innerHTML = `
                <div class="loading-state col-span-full">
                    <div class="spinner"></div>
                    <p>Filtering dining spots...</p>
                </div>
            `;

            try {
                let items = [];

                // If radius filter selected, query nearby endpoint with current location
                if (radius && state.currentLocation?.latitude) {
                    const res = await api.getNearbyRestaurants(
                        state.currentLocation.latitude,
                        state.currentLocation.longitude,
                        parseInt(radius, 10),
                        maxBudget ? parseFloat(maxBudget) : null
                    );
                    items = (res?.data || []).map(n => ({
                        id: n.restaurant_id,
                        name: n.restaurant_name,
                        cuisines: n.cuisines || ['Fast Food', 'Pakistani'],
                        avg_rating: n.avg_rating || 4.5,
                        avg_price_per_person: n.avg_price_per_person,
                        city: n.city || 'Lahore',
                        distance_meters: n.distance_meters,
                        cover_image_url: null,
                        latitude: n.latitude,
                        longitude: n.longitude,
                        branch_name: n.branch_name,
                        address: n.address
                    }));
                } else {
                    const params = {};
                    if (search) params.search = search;
                    if (cuisine) params.cuisine = cuisine;
                    if (maxBudget) params.max_price = maxBudget;
                    if (minRating) params.min_rating = minRating;
                    params.limit = 40;

                    const res = await api.getRestaurants(params);
                    items = res?.data?.items || [];
                }

                renderGrid(items);
                if (currentMode === 'map') {
                    renderMap(items);
                }
            } catch (err) {
                console.error('Filter fetch error:', err);
                gridContainer.innerHTML = `
                    <div class="empty-state-box col-span-full">
                        <p class="text-danger">Failed to fetch restaurants. Please try again.</p>
                    </div>
                `;
            }
        }

        function renderGrid(items) {
            if (!gridContainer) return;
            if (items.length === 0) {
                gridContainer.innerHTML = `
                    <div class="empty-state-box col-span-full">
                        <div class="empty-icon">🔍</div>
                        <h3>No spots match your filters</h3>
                        <p class="text-muted">Try changing your location area, expanding your distance radius, or clearing cuisine filters.</p>
                    </div>
                `;
                return;
            }

            gridContainer.innerHTML = items.map(r => HomeView.renderStandardRestaurantCard(r)).join('');
            HomeView.attachCardEvents(gridContainer);
        }

        function renderMap(items) {
            const mapElem = document.getElementById('leaflet-map-element');
            const sidebarList = document.getElementById('map-sidebar-list');
            if (!mapElem) return;

            const centerLat = state.currentLocation.latitude || 31.5204;
            const centerLon = state.currentLocation.longitude || 74.3587;

            if (!mapInstance) {
                mapInstance = L.map('leaflet-map-element').setView([centerLat, centerLon], 13);
                L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                    attribution: '© OpenStreetMap contributors'
                }).addTo(mapInstance);
            } else {
                mapInstance.setView([centerLat, centerLon], 13);
            }

            // Clear old markers
            mapMarkers.forEach(m => mapInstance.removeLayer(m));
            mapMarkers = [];

            // Add center location marker
            const userMarker = L.marker([centerLat, centerLon], {
                title: state.currentLocation.name
            }).addTo(mapInstance).bindPopup(`<b>📍 ${state.currentLocation.name}</b>`);
            mapMarkers.push(userMarker);

            // Populate sidebar & markers
            if (sidebarList) {
                sidebarList.innerHTML = items.map(item => `
                    <div class="map-sidebar-item" data-id="${item.id}">
                        <div class="sidebar-item-title"><strong>${item.name}</strong></div>
                        <div class="sidebar-item-meta text-muted small">
                            <span>⭐ ${item.avg_rating || '4.5'}</span> • 
                            <span>${(item.cuisines || ['Fast Food']).slice(0, 2).join(', ')}</span>
                            ${item.distance_meters ? ` • <span>${(item.distance_meters / 1000).toFixed(1)} km</span>` : ''}
                        </div>
                    </div>
                `).join('');

                sidebarList.querySelectorAll('.map-sidebar-item').forEach(el => {
                    el.addEventListener('click', () => {
                        const id = el.getAttribute('data-id');
                        state.navigate('restaurant', { id });
                    });
                });
            }

            // Add markers for restaurants
            items.forEach(r => {
                const lat = r.latitude || (centerLat + (Math.random() - 0.5) * 0.05);
                const lon = r.longitude || (centerLon + (Math.random() - 0.5) * 0.05);

                const marker = L.marker([lat, lon]).addTo(mapInstance)
                    .bindPopup(`
                        <div class="leaflet-popup-card">
                            <h4>${r.name}</h4>
                            <p>${(r.cuisines || []).join(', ')}</p>
                            <p>⭐ ${r.avg_rating || '4.5'} | ${r.avg_price_per_person ? 'Rs. ' + r.avg_price_per_person : '$$'}</p>
                            <button type="button" class="btn btn-primary btn-sm btn-block" onclick="window.state.navigate('restaurant', {id: '${r.id}'})">View Profile</button>
                        </div>
                    `);
                mapMarkers.push(marker);
            });
        }

        // View mode toggles
        if (gridBtn && mapBtn) {
            gridBtn.addEventListener('click', () => {
                currentMode = 'grid';
                gridBtn.classList.add('active');
                mapBtn.classList.remove('active');
                gridContainer.style.display = 'grid';
                mapContainer.style.display = 'none';
            });

            mapBtn.addEventListener('click', () => {
                currentMode = 'map';
                mapBtn.classList.add('active');
                gridBtn.classList.remove('active');
                gridContainer.style.display = 'none';
                mapContainer.style.display = 'block';
                setTimeout(() => {
                    if (mapInstance) mapInstance.invalidateSize();
                    fetchFilteredRestaurants();
                }, 150);
            });
        }

        // Filter event listeners with debounce
        let debounceTimer = null;
        if (searchInput) {
            searchInput.addEventListener('input', () => {
                clearTimeout(debounceTimer);
                debounceTimer = setTimeout(fetchFilteredRestaurants, 350);
            });
        }

        [cuisineFilter, budgetFilter, ratingFilter, radiusFilter].forEach(el => {
            if (el) el.addEventListener('change', fetchFilteredRestaurants);
        });

        // Quick cuisine chips
        document.querySelectorAll('.quick-chip').forEach(chip => {
            chip.addEventListener('click', () => {
                document.querySelectorAll('.quick-chip').forEach(c => c.classList.remove('active'));
                chip.classList.add('active');
                const cuisine = chip.getAttribute('data-cuisine');
                if (cuisineFilter) cuisineFilter.value = cuisine;
                fetchFilteredRestaurants();
            });
        });

        // Listen for location changes
        state.subscribe('locationChanged', () => {
            fetchFilteredRestaurants();
        });

        // Initial load
        fetchFilteredRestaurants();
    }
}
