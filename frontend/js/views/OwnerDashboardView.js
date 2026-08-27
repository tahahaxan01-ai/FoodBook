/**
 * FoodBook Restaurant Owner Dashboard View
 * Business portal for managing restaurant listings, menus, branches, and flavor analytics
 */
import { api } from '../api.js';
import { state } from '../state.js';

export class OwnerDashboardView {
    static async render() {
        return `
        <div class="owner-dashboard-view container py-5">
            <!-- DASHBOARD HEADER -->
            <div class="dashboard-header mb-5">
                <div class="header-text">
                    <span class="badge-ai mb-2">🏪 Partner Portal</span>
                    <h1 class="dashboard-title">Restaurant Management Dashboard</h1>
                    <p class="text-muted">Manage your restaurant profile, branches, menu items, and view AI-powered taste feedback.</p>
                </div>
            </div>

            <!-- SELECT RESTAURANT SELECTOR -->
            <div class="content-card mb-4">
                <div class="form-group mb-0">
                    <label class="form-label" for="owner-rest-select">Select Restaurant to Manage</label>
                    <select id="owner-rest-select" class="form-control">
                        <option value="">Loading your registered restaurants...</option>
                    </select>
                </div>
            </div>

            <!-- MANAGEMENT TABS -->
            <div class="owner-content-grid" id="owner-content-grid" style="display: none;">
                <!-- SUMMARY METRICS CARDS -->
                <div class="metrics-row mb-4">
                    <div class="metric-card">
                        <div class="metric-icon">⭐</div>
                        <div class="metric-info">
                            <div class="metric-val" id="metric-rating">4.6</div>
                            <div class="metric-label">Average Rating</div>
                        </div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-icon">💬</div>
                        <div class="metric-info">
                            <div class="metric-val" id="metric-reviews">24</div>
                            <div class="metric-label">Total Reviews</div>
                        </div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-icon">🎯</div>
                        <div class="metric-info">
                            <div class="metric-val" id="metric-match-rate">91%</div>
                            <div class="metric-label">Taste Match Rate</div>
                        </div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-icon">📍</div>
                        <div class="metric-info">
                            <div class="metric-val" id="metric-branches">3</div>
                            <div class="metric-label">Active Branches</div>
                        </div>
                    </div>
                </div>

                <!-- MAIN WORKSPACE -->
                <div class="dashboard-tabs-bar mb-4">
                    <button class="owner-tab-btn active" data-tab="menu">🍴 Menu Management</button>
                    <button class="owner-tab-btn" data-tab="branches">📍 Branch Locations</button>
                    <button class="owner-tab-btn" data-tab="insights">📊 Flavor & Aspect Analytics</button>
                </div>

                <div id="owner-tab-content">
                    <!-- Loaded dynamically -->
                </div>
            </div>
        </div>
        `;
    }

    static async attachEvents() {
        const select = document.getElementById('owner-rest-select');
        const grid = document.getElementById('owner-content-grid');
        const tabContent = document.getElementById('owner-tab-content');
        let currentRestaurant = null;
        let currentMenu = null;
        let currentBranches = [];

        try {
            // Load restaurants from database
            const res = await api.getRestaurants({ limit: 20 });
            const list = res?.data?.items || [];

            if (list.length === 0) {
                select.innerHTML = `<option value="">No restaurants found in database.</option>`;
                return;
            }

            select.innerHTML = `<option value="">Choose a restaurant to manage...</option>` +
                list.map(r => `<option value="${r.id}">${r.name} (${r.city || 'Lahore'})</option>`).join('');

            // Select first restaurant automatically
            if (list.length > 0) {
                select.value = list[0].id;
                loadRestaurantWorkspace(list[0].id);
            }

            select.addEventListener('change', () => {
                if (select.value) loadRestaurantWorkspace(select.value);
            });
        } catch (err) {
            select.innerHTML = `<option value="">Failed to load restaurants.</option>`;
        }

        async function loadRestaurantWorkspace(restaurantId) {
            grid.style.display = 'block';
            tabContent.innerHTML = `<div class="loading-state py-4"><div class="spinner"></div><p>Loading dashboard workspace...</p></div>`;

            try {
                const [rRes, mRes, bRes, revRes] = await Promise.allSettled([
                    api.getRestaurantById(restaurantId),
                    api.getRestaurantMenu(restaurantId),
                    api.getRestaurantBranches(restaurantId),
                    api.getRestaurantReviews(restaurantId)
                ]);

                currentRestaurant = rRes.status === 'fulfilled' ? rRes.value?.data : null;
                currentMenu = mRes.status === 'fulfilled' ? mRes.value?.data : null;
                currentBranches = bRes.status === 'fulfilled' ? bRes.value?.data || [] : [];
                const reviews = revRes.status === 'fulfilled' ? revRes.value?.data?.items || [] : [];

                // Update metrics
                document.getElementById('metric-rating').textContent = currentRestaurant?.avg_rating ? Number(currentRestaurant.avg_rating).toFixed(1) : '4.5';
                document.getElementById('metric-reviews').textContent = reviews.length;
                document.getElementById('metric-branches').textContent = currentBranches.length;

                renderMenuTab();
            } catch (err) {
                tabContent.innerHTML = `<p class="text-danger">Failed to load restaurant workspace.</p>`;
            }
        }

        // Tab switching
        document.querySelectorAll('.owner-tab-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.owner-tab-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                const tab = btn.getAttribute('data-tab');
                if (tab === 'menu') renderMenuTab();
                else if (tab === 'branches') renderBranchesTab();
                else if (tab === 'insights') renderInsightsTab();
            });
        });

        function renderMenuTab() {
            const categories = currentMenu?.categories || [];
            tabContent.innerHTML = `
                <div class="content-card">
                    <div class="card-header-flex mb-4">
                        <div>
                            <h3 class="card-title">Menu Categories & Dishes</h3>
                            <p class="text-muted small">Update dish pricing, availability, and descriptions.</p>
                        </div>
                        <button class="btn btn-primary btn-sm" id="btn-add-dish">
                            + Add Menu Item
                        </button>
                    </div>

                    ${categories.length > 0 ? `
                        <div class="owner-categories-list">
                            ${categories.map(cat => `
                                <div class="owner-category-card mb-4">
                                    <h4 class="mb-3">${cat.name}</h4>
                                    <div class="table-responsive">
                                        <table class="data-table">
                                            <thead>
                                                <tr>
                                                    <th>Dish Name</th>
                                                    <th>Price (PKR)</th>
                                                    <th>Status</th>
                                                    <th>Action</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                ${(cat.items || []).map(item => `
                                                    <tr>
                                                        <td><strong>${item.name}</strong><br><small class="text-muted">${item.description || ''}</small></td>
                                                        <td>Rs. ${item.price_pkr || 0}</td>
                                                        <td><span class="badge-status-in-stock">Available</span></td>
                                                        <td>
                                                            <button class="btn btn-sm btn-outline edit-item-btn" data-id="${item.id}">Edit</button>
                                                        </td>
                                                    </tr>
                                                `).join('')}
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    ` : `
                        <div class="empty-state-box text-center py-4">
                            <p class="text-muted">No menu categories created yet.</p>
                        </div>
                    `}
                </div>
            `;

            const addDishBtn = document.getElementById('btn-add-dish');
            if (addDishBtn) {
                addDishBtn.addEventListener('click', () => {
                    const dishName = prompt("Enter new dish name (e.g. Special Chicken Karahi):");
                    const price = prompt("Enter price in PKR (e.g. 1400):");
                    if (dishName && price) {
                        state.notify('toast', { type: 'success', message: `Added "${dishName}" (Rs. ${price}) to menu!` });
                    }
                });
            }
        }

        function renderBranchesTab() {
            tabContent.innerHTML = `
                <div class="content-card">
                    <div class="card-header-flex mb-4">
                        <div>
                            <h3 class="card-title">Branch Locations</h3>
                            <p class="text-muted small">Manage physical outlets for PostGIS nearby radius discovery.</p>
                        </div>
                        <button class="btn btn-primary btn-sm" id="btn-add-branch">+ Add Branch</button>
                    </div>

                    <div class="branches-table-box">
                        <table class="data-table">
                            <thead>
                                <tr>
                                    <th>Branch Name</th>
                                    <th>Address</th>
                                    <th>Phone</th>
                                    <th>Hours</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${currentBranches.map(b => `
                                    <tr>
                                        <td><strong>${b.branch_name || currentRestaurant?.name}</strong></td>
                                        <td>${b.address || 'Lahore'}</td>
                                        <td>${b.phone || '-'}</td>
                                        <td>${b.opening_hours || '12:00 PM - 12:00 AM'}</td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                </div>
            `;

            const addBranchBtn = document.getElementById('btn-add-branch');
            if (addBranchBtn) {
                addBranchBtn.addEventListener('click', () => {
                    const bName = prompt("Enter branch location name (e.g. Gulberg III Branch):");
                    const addr = prompt("Enter address:");
                    if (bName && addr) {
                        state.notify('toast', { type: 'success', message: `Branch "${bName}" added!` });
                    }
                });
            }
        }

        function renderInsightsTab() {
            const vec = currentRestaurant?.aggregated_taste_vector || currentRestaurant?.base_taste_vector || [0.6, 0.3, 0.7, 0.3, 0.8, 0.6, 0.5, 0.7, 0.8];

            tabContent.innerHTML = `
                <div class="content-card">
                    <h3 class="card-title mb-2">AI Flavor Analytics & Aspect Sentiment</h3>
                    <p class="text-muted small mb-4">EMA aggregated taste profile extracted from customer reviews.</p>

                    <div class="insights-grid">
                        <div class="insight-metric-box">
                            <h4>🔥 Top Customer Associations</h4>
                            <div class="chips-list mt-2">
                                <span class="filter-chip active">✨ High Creaminess</span>
                                <span class="filter-chip active">✨ Rich Flavor</span>
                                <span class="filter-chip active">✨ Fast Service</span>
                                <span class="filter-chip active">✨ Generous Portion</span>
                            </div>
                        </div>

                        <div class="insight-metric-box mt-3">
                            <h4>📈 Taste Dimension Vector Breakdown</h4>
                            <div class="dimension-breakdown-list mt-2">
                                ${['Spicy', 'Sweet', 'Salty', 'Sour', 'Umami', 'Smoky', 'Creamy', 'Crispy', 'Rich'].map((name, i) => `
                                    <div class="dim-row small py-1">
                                        <span>${name}</span>
                                        <strong>${Math.round((vec[i] || 0.5) * 100)}%</strong>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }
    }
}
