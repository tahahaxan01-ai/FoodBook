/**
 * FoodBook Navbar Component with Dark/Light Theme Switcher & Area Selector Modal
 */
import { state } from '../state.js';
import { AuthManager } from '../auth.js';
import { CONFIG } from '../config.js';

export class Navbar {
    static render() {
        const user = state.user;
        const savedCount = state.savedRestaurantIds.size;
        const locationName = state.currentLocation?.name || "Gulberg, Lahore";
        const isDark = state.theme === 'dark';

        return `
        <header class="navbar-container">
            <div class="navbar-inner container">
                <!-- Brand Logo -->
                <a href="#home" class="brand-logo" id="nav-brand">
                    <span class="logo-icon">🍽️</span>
                    <span class="brand-text">Food<span class="brand-highlight">Book</span></span>
                </a>

                <!-- Location Selector (Opens Area Modal) -->
                <div class="location-badge" id="nav-location-btn" title="Choose your area in Lahore">
                    <i class="location-icon">📍</i>
                    <span class="location-text" id="nav-location-text">${locationName}</span>
                    <span class="location-arrow">▾</span>
                </div>

                <!-- Desktop Navigation Links -->
                <nav class="nav-links">
                    <a href="#home" class="nav-link ${state.currentView === 'home' ? 'active' : ''}">Discover</a>
                    <a href="#explore" class="nav-link ${state.currentView === 'explore' ? 'active' : ''}">Restaurants</a>
                    <a href="#ai-search" class="nav-link ${state.currentView === 'ai-search' ? 'active' : ''}">
                        <span class="sparkle">✨</span> AI Food Finder
                    </a>
                    <a href="#collections" class="nav-link ${state.currentView === 'collections' ? 'active' : ''}">Collections</a>
                    <a href="#community" class="nav-link ${state.currentView === 'community' ? 'active' : ''}">Community</a>
                </nav>

                <!-- Action Controls -->
                <div class="nav-actions">
                    <!-- Dark / Light Theme Toggle Button -->
                    <button class="icon-btn theme-toggle-btn" id="nav-theme-toggle-btn" title="Toggle Dark/Light Mode">
                        <span id="theme-toggle-icon">${isDark ? '☀️' : '🌙'}</span>
                    </button>

                    <!-- Quick Search Trigger Button -->
                    <button class="icon-btn search-trigger" id="nav-search-btn" title="Quick Search">
                        <span>🔍</span>
                    </button>

                    ${user ? `
                        <!-- Saved Places Shortcut -->
                        <button class="icon-btn saved-btn" id="nav-saved-btn" title="Saved Restaurants">
                            <span>❤️</span>
                            ${savedCount > 0 ? `<span class="badge-counter">${savedCount}</span>` : ''}
                        </button>

                        <!-- User Profile Dropdown -->
                        <div class="user-menu-wrapper">
                            <button class="user-avatar-btn" id="nav-user-menu-btn">
                                <span class="user-avatar-initial">${(user.full_name || user.email || 'U')[0].toUpperCase()}</span>
                                <span class="user-name-label">${(user.full_name || user.email).split(' ')[0]}</span>
                                <span class="dropdown-chevron">▾</span>
                            </button>
                            <div class="user-dropdown-menu" id="nav-user-dropdown" style="display: none;">
                                <div class="dropdown-header">
                                    <div class="dropdown-user-name">${user.full_name || 'Foodie'}</div>
                                    <div class="dropdown-user-email">${user.email}</div>
                                </div>
                                <hr class="dropdown-divider">
                                <a href="#profile" class="dropdown-item">
                                    <span>👤</span> My Profile & Taste Radar
                                </a>
                                <a href="#onboarding" class="dropdown-item">
                                    <span>🎛️</span> Edit Taste Preferences
                                </a>
                                <a href="#collections" class="dropdown-item">
                                    <span>📚</span> My Food Collections
                                </a>
                                <a href="#owner" class="dropdown-item">
                                    <span>🏪</span> Restaurant Owner Portal
                                </a>
                                <hr class="dropdown-divider">
                                <button class="dropdown-item text-danger" id="nav-logout-btn">
                                    <span>🚪</span> Sign Out
                                </button>
                            </div>
                        </div>
                    ` : `
                        <!-- Auth CTA Buttons -->
                        <button class="btn btn-outline btn-sm" id="nav-login-btn">Sign In</button>
                        <button class="btn btn-primary btn-sm" id="nav-signup-btn">Get Started</button>
                    `}

                    <!-- Mobile Hamburger Toggle -->
                    <button class="mobile-menu-btn" id="nav-mobile-toggle" aria-label="Toggle navigation">
                        <span></span>
                        <span></span>
                        <span></span>
                    </button>
                </div>
            </div>

            <!-- Mobile Drawer Menu -->
            <div class="mobile-drawer" id="nav-mobile-drawer" style="display: none;">
                <div class="mobile-drawer-inner">
                    <div class="mobile-drawer-header mb-3">
                        <div class="d-flex align-items-center justify-content-between">
                            <strong>Menu</strong>
                            <button class="btn btn-sm btn-outline" id="mobile-theme-toggle-btn">
                                <span>${isDark ? '☀️ Light Mode' : '🌙 Dark Mode'}</span>
                            </button>
                        </div>
                    </div>
                    <a href="#home" class="mobile-nav-link">🏠 Discover</a>
                    <a href="#explore" class="mobile-nav-link">🍴 Restaurants & Map</a>
                    <a href="#ai-search" class="mobile-nav-link">✨ AI Food Finder</a>
                    <a href="#collections" class="mobile-nav-link">📚 Food Collections</a>
                    <a href="#community" class="mobile-nav-link">📸 Community Feed</a>
                    ${user ? `
                        <a href="#profile" class="mobile-nav-link">👤 My Profile & Taste Radar</a>
                        <a href="#onboarding" class="mobile-nav-link">🎛️ Taste Preferences</a>
                        <a href="#owner" class="mobile-nav-link">🏪 Restaurant Portal</a>
                        <button class="btn btn-outline btn-block mt-3" id="mobile-logout-btn">Sign Out</button>
                    ` : `
                        <div class="mobile-auth-btns mt-3">
                            <button class="btn btn-outline btn-block mb-2" id="mobile-login-btn">Sign In</button>
                            <button class="btn btn-primary btn-block" id="mobile-signup-btn">Get Started</button>
                        </div>
                    `}
                </div>
            </div>
        </header>

        <!-- LOCATION / AREA SELECTOR MODAL -->
        <div class="modal-overlay" id="location-modal-overlay" style="display: none;">
            <div class="modal-card location-modal-card">
                <button class="modal-close-btn" id="location-modal-close" aria-label="Close">✕</button>
                <div class="modal-header mb-3">
                    <div class="header-icon">📍</div>
                    <div>
                        <h3 class="modal-title">Select Your Area</h3>
                        <p class="modal-subtitle">Choose your area in Lahore for accurate nearby restaurant & radius discovery.</p>
                    </div>
                </div>

                <div class="modal-body">
                    <!-- GPS Auto Detect Option -->
                    <button type="button" class="btn btn-primary btn-block mb-4" id="btn-gps-detect">
                        <span>📡 Auto-Detect My Live GPS Location</span>
                    </button>

                    <p class="form-label mb-2">Or pick a popular Lahore area:</p>
                    <div class="areas-grid" id="areas-grid-container">
                        ${CONFIG.LAHORE_AREAS.map(area => `
                            <button type="button" class="area-item-btn ${state.currentLocation?.name === area.name ? 'active' : ''}" 
                                data-name="${area.name}" 
                                data-lat="${area.latitude}" 
                                data-lon="${area.longitude}">
                                <span class="area-icon">${area.icon}</span>
                                <span class="area-name">${area.name}</span>
                            </button>
                        `).join('')}
                    </div>
                </div>
            </div>
        </div>

        <!-- MOBILE BOTTOM FLOATING NAVIGATION BAR (Modern App Bar) -->
        <nav class="mobile-bottom-nav">
            <a href="#home" class="bottom-nav-item ${state.currentView === 'home' ? 'active' : ''}">
                <span class="bottom-nav-icon">🏠</span>
                <span class="bottom-nav-label">Home</span>
            </a>
            <a href="#explore" class="bottom-nav-item ${state.currentView === 'explore' ? 'active' : ''}">
                <span class="bottom-nav-icon">🍴</span>
                <span class="bottom-nav-label">Explore</span>
            </a>
            <a href="#ai-search" class="bottom-nav-item ${state.currentView === 'ai-search' ? 'active' : ''}">
                <span class="bottom-nav-icon">✨</span>
                <span class="bottom-nav-label">AI Finder</span>
            </a>
            <a href="#collections" class="bottom-nav-item ${state.currentView === 'collections' ? 'active' : ''}">
                <span class="bottom-nav-icon">📚</span>
                <span class="bottom-nav-label">Guides</span>
            </a>
            <a href="#community" class="bottom-nav-item ${state.currentView === 'community' ? 'active' : ''}">
                <span class="bottom-nav-icon">📸</span>
                <span class="bottom-nav-label">Feed</span>
            </a>
            <a href="#profile" class="bottom-nav-item ${state.currentView === 'profile' ? 'active' : ''}">
                <span class="bottom-nav-icon">👤</span>
                <span class="bottom-nav-label">Profile</span>
            </a>
        </nav>
        `;
    }

    static attachEvents() {
        // Theme toggler
        const themeBtn = document.getElementById('nav-theme-toggle-btn');
        const mobileThemeBtn = document.getElementById('mobile-theme-toggle-btn');
        const themeIcon = document.getElementById('theme-toggle-icon');

        function toggleThemeAction() {
            const newTheme = state.toggleTheme();
            if (themeIcon) themeIcon.textContent = newTheme === 'dark' ? '☀️' : '🌙';
            if (mobileThemeBtn) mobileThemeBtn.innerHTML = `<span>${newTheme === 'dark' ? '☀️ Light Mode' : '🌙 Dark Mode'}</span>`;
            state.notify('toast', { type: 'info', message: `Switched to ${newTheme.toUpperCase()} theme` });
        }

        if (themeBtn) themeBtn.addEventListener('click', toggleThemeAction);
        if (mobileThemeBtn) mobileThemeBtn.addEventListener('click', toggleThemeAction);

        // Location Modal Open
        const locBtn = document.getElementById('nav-location-btn');
        const locOverlay = document.getElementById('location-modal-overlay');
        const locClose = document.getElementById('location-modal-close');
        const gpsDetectBtn = document.getElementById('btn-gps-detect');

        function openLocModal() {
            if (locOverlay) locOverlay.style.display = 'flex';
        }

        function closeLocModal() {
            if (locOverlay) locOverlay.style.display = 'none';
        }

        if (locBtn) locBtn.addEventListener('click', openLocModal);
        if (locClose) locClose.addEventListener('click', closeLocModal);
        if (locOverlay) {
            locOverlay.addEventListener('click', (e) => {
                if (e.target === locOverlay) closeLocModal();
            });
        }

        // GPS Auto-detect
        if (gpsDetectBtn) {
            gpsDetectBtn.addEventListener('click', () => {
                if (navigator.geolocation) {
                    gpsDetectBtn.disabled = true;
                    gpsDetectBtn.innerHTML = `<span>⏳ Detecting your GPS coordinates...</span>`;
                    navigator.geolocation.getCurrentPosition(
                        (pos) => {
                            state.setLocation({
                                name: "Your Live Location",
                                latitude: pos.coords.latitude,
                                longitude: pos.coords.longitude
                            });
                            state.hasLocationPermission = true;
                            state.notify('toast', { type: 'success', message: 'Location updated to your GPS coordinates! 📍' });
                            closeLocModal();
                        },
                        (err) => {
                            state.notify('toast', { type: 'info', message: 'Could not access GPS. Please pick an area below.' });
                            gpsDetectBtn.disabled = false;
                            gpsDetectBtn.innerHTML = `<span>📡 Auto-Detect My Live GPS Location</span>`;
                        },
                        { timeout: 6000 }
                    );
                }
            });
        }

        // Area button clicks
        document.querySelectorAll('.area-item-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const name = btn.getAttribute('data-name');
                const lat = parseFloat(btn.getAttribute('data-lat'));
                const lon = parseFloat(btn.getAttribute('data-lon'));

                state.setLocation({
                    name: name,
                    latitude: lat,
                    longitude: lon
                });

                document.querySelectorAll('.area-item-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');

                const locText = document.getElementById('nav-location-text');
                if (locText) locText.textContent = name;

                state.notify('toast', { type: 'success', message: `Location set to ${name}! 📍` });
                closeLocModal();
            });
        });

        // Search trigger
        const searchBtn = document.getElementById('nav-search-btn');
        if (searchBtn) {
            searchBtn.addEventListener('click', () => {
                state.navigate('explore');
            });
        }

        // Saved button
        const savedBtn = document.getElementById('nav-saved-btn');
        if (savedBtn) {
            savedBtn.addEventListener('click', () => {
                state.navigate('profile', { tab: 'saved' });
            });
        }

        // User dropdown menu toggle
        const userMenuBtn = document.getElementById('nav-user-menu-btn');
        const userDropdown = document.getElementById('nav-user-dropdown');
        if (userMenuBtn && userDropdown) {
            userMenuBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                userDropdown.style.display = userDropdown.style.display === 'none' ? 'block' : 'none';
            });

            document.addEventListener('click', () => {
                userDropdown.style.display = 'none';
            });
        }

        // Logout
        const logoutBtn = document.getElementById('nav-logout-btn');
        if (logoutBtn) logoutBtn.addEventListener('click', () => AuthManager.logout());
        const mobileLogoutBtn = document.getElementById('mobile-logout-btn');
        if (mobileLogoutBtn) mobileLogoutBtn.addEventListener('click', () => AuthManager.logout());

        // Auth modals trigger
        const loginBtn = document.getElementById('nav-login-btn');
        const signupBtn = document.getElementById('nav-signup-btn');
        const mobileLoginBtn = document.getElementById('mobile-login-btn');
        const mobileSignupBtn = document.getElementById('mobile-signup-btn');

        if (loginBtn) loginBtn.addEventListener('click', () => state.notify('openAuthModal', { tab: 'login' }));
        if (signupBtn) signupBtn.addEventListener('click', () => state.notify('openAuthModal', { tab: 'signup' }));
        if (mobileLoginBtn) mobileLoginBtn.addEventListener('click', () => state.notify('openAuthModal', { tab: 'login' }));
        if (mobileSignupBtn) mobileSignupBtn.addEventListener('click', () => state.notify('openAuthModal', { tab: 'signup' }));

        // Mobile drawer toggle
        const mobileToggle = document.getElementById('nav-mobile-toggle');
        const mobileDrawer = document.getElementById('nav-mobile-drawer');
        if (mobileToggle && mobileDrawer) {
            mobileToggle.addEventListener('click', () => {
                mobileDrawer.style.display = mobileDrawer.style.display === 'none' ? 'block' : 'none';
            });
        }
    }
}
