/**
 * FoodBook Authentication Modal (Sign In / Sign Up)
 */
import { AuthManager } from '../auth.js';
import { state } from '../state.js';

export class AuthModal {
    static render() {
        return `
        <div class="modal-overlay" id="auth-modal-overlay" style="display: none;">
            <div class="modal-card auth-modal-card">
                <button class="modal-close-btn" id="auth-modal-close" aria-label="Close modal">✕</button>

                <!-- Modal Header / Tabs -->
                <div class="auth-header">
                    <div class="auth-brand">
                        <span class="logo-icon">🍽️</span>
                        <span class="brand-text">Food<span class="brand-highlight">Book</span></span>
                    </div>
                    <div class="auth-tabs">
                        <button class="auth-tab-btn active" id="auth-tab-login" data-tab="login">Sign In</button>
                        <button class="auth-tab-btn" id="auth-tab-signup" data-tab="signup">Create Account</button>
                    </div>
                </div>

                <div class="modal-body">
                    <!-- Error / Alert banner -->
                    <div class="alert-banner alert-danger" id="auth-error-banner" style="display: none;"></div>

                    <!-- LOGIN FORM -->
                    <form class="auth-form" id="login-form">
                        <p class="auth-subtitle">Welcome back! Sign in to access your personalized taste recommendations.</p>

                        <div class="form-group">
                            <label class="form-label" for="login-email">Email Address</label>
                            <div class="input-with-icon">
                                <span class="input-icon">✉️</span>
                                <input type="email" id="login-email" class="form-control" placeholder="name@example.com" required autocomplete="email">
                            </div>
                        </div>

                        <div class="form-group">
                            <div class="form-label-row">
                                <label class="form-label" for="login-password">Password</label>
                            </div>
                            <div class="input-with-icon">
                                <span class="input-icon">🔒</span>
                                <input type="password" id="login-password" class="form-control" placeholder="••••••••" required autocomplete="current-password">
                            </div>
                        </div>

                        <button type="submit" class="btn btn-primary btn-block btn-lg" id="login-submit-btn">
                            <span class="btn-text">Sign In to FoodBook</span>
                            <span class="btn-spinner" style="display: none;">⏳ Signing in...</span>
                        </button>
                    </form>

                    <!-- SIGNUP FORM -->
                    <form class="auth-form" id="signup-form" style="display: none;">
                        <p class="auth-subtitle">Create your account to train your 9D Food Taste Profile and get tailored recommendations.</p>

                        <div class="form-group">
                            <label class="form-label" for="signup-name">Full Name</label>
                            <div class="input-with-icon">
                                <span class="input-icon">👤</span>
                                <input type="text" id="signup-name" class="form-control" placeholder="e.g. Ali Ahmed" required autocomplete="name">
                            </div>
                        </div>

                        <div class="form-group">
                            <label class="form-label" for="signup-email">Email Address</label>
                            <div class="input-with-icon">
                                <span class="input-icon">✉️</span>
                                <input type="email" id="signup-email" class="form-control" placeholder="name@example.com" required autocomplete="email">
                            </div>
                        </div>

                        <div class="form-group">
                            <label class="form-label" for="signup-password">Password</label>
                            <div class="input-with-icon">
                                <span class="input-icon">🔒</span>
                                <input type="password" id="signup-password" class="form-control" placeholder="Minimum 6 characters" required minlength="6" autocomplete="new-password">
                            </div>
                        </div>

                        <button type="submit" class="btn btn-primary btn-block btn-lg" id="signup-submit-btn">
                            <span class="btn-text">Create FoodBook Account</span>
                            <span class="btn-spinner" style="display: none;">⏳ Creating account...</span>
                        </button>
                    </form>

                    <!-- Security note -->
                    <div class="auth-footer-note mt-3 text-center">
                        <small class="text-muted">Secured with bank-grade encryption.</small>
                    </div>

                </div>
            </div>
        </div>
        `;
    }

    static attachEvents() {
        const overlay = document.getElementById('auth-modal-overlay');
        const closeBtn = document.getElementById('auth-modal-close');
        const tabLogin = document.getElementById('auth-tab-login');
        const tabSignup = document.getElementById('auth-tab-signup');
        const loginForm = document.getElementById('login-form');
        const signupForm = document.getElementById('signup-form');
        const errorBanner = document.getElementById('auth-error-banner');

        function openModal(tab = 'login') {
            if (!overlay) return;
            overlay.style.display = 'flex';
            if (errorBanner) errorBanner.style.display = 'none';
            switchTab(tab);
        }

        function closeModal() {
            if (!overlay) return;
            overlay.style.display = 'none';
            if (errorBanner) errorBanner.style.display = 'none';
        }

        function switchTab(tab) {
            if (tab === 'login') {
                tabLogin?.classList.add('active');
                tabSignup?.classList.remove('active');
                if (loginForm) loginForm.style.display = 'block';
                if (signupForm) signupForm.style.display = 'none';
            } else {
                tabSignup?.classList.add('active');
                tabLogin?.classList.remove('active');
                if (signupForm) signupForm.style.display = 'block';
                if (loginForm) loginForm.style.display = 'none';
            }
            if (errorBanner) errorBanner.style.display = 'none';
        }

        if (closeBtn) closeBtn.addEventListener('click', closeModal);
        if (overlay) {
            overlay.addEventListener('click', (e) => {
                if (e.target === overlay) closeModal();
            });
        }

        if (tabLogin) tabLogin.addEventListener('click', () => switchTab('login'));
        if (tabSignup) tabSignup.addEventListener('click', () => switchTab('signup'));

        // Listen for global openAuthModal event
        state.subscribe('openAuthModal', (data) => {
            openModal(data?.tab || 'login');
        });

        state.subscribe('requireAuth', () => {
            openModal('login');
        });

        // Handle Login Submission
        if (loginForm) {
            loginForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                const email = document.getElementById('login-email').value.trim();
                const password = document.getElementById('login-password').value;
                const submitBtn = document.getElementById('login-submit-btn');

                if (!email || !password) return;

                submitBtn.disabled = true;
                submitBtn.querySelector('.btn-text').style.display = 'none';
                submitBtn.querySelector('.btn-spinner').style.display = 'inline-block';
                if (errorBanner) errorBanner.style.display = 'none';

                const res = await AuthManager.login(email, password);
                submitBtn.disabled = false;
                submitBtn.querySelector('.btn-text').style.display = 'inline-block';
                submitBtn.querySelector('.btn-spinner').style.display = 'none';

                if (res.success) {
                    closeModal();
                    // If user has no taste profile trained yet, route to onboarding
                    if (!state.tasteProfile?.taste_vector || state.tasteProfile.taste_vector.every(v => v === 0.5)) {
                        state.navigate('onboarding');
                    } else {
                        state.navigate('home');
                    }
                } else {
                    if (errorBanner) {
                        errorBanner.textContent = res.error || 'Failed to sign in. Please check your credentials.';
                        errorBanner.style.display = 'block';
                    }
                }
            });
        }

        // Handle Signup Submission
        if (signupForm) {
            signupForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                const fullName = document.getElementById('signup-name').value.trim();
                const email = document.getElementById('signup-email').value.trim();
                const password = document.getElementById('signup-password').value;
                const submitBtn = document.getElementById('signup-submit-btn');

                if (!email || !password || !fullName) return;

                submitBtn.disabled = true;
                submitBtn.querySelector('.btn-text').style.display = 'none';
                submitBtn.querySelector('.btn-spinner').style.display = 'inline-block';
                if (errorBanner) errorBanner.style.display = 'none';

                const res = await AuthManager.signup(email, password, fullName);
                submitBtn.disabled = false;
                submitBtn.querySelector('.btn-text').style.display = 'inline-block';
                submitBtn.querySelector('.btn-spinner').style.display = 'none';

                if (res.success) {
                    closeModal();
                    // New user directly directed to Onboarding to build their 9D taste profile!
                    state.navigate('onboarding');
                } else {
                    if (errorBanner) {
                        errorBanner.textContent = res.error || 'Failed to create account.';
                        errorBanner.style.display = 'block';
                    }
                }
            });
        }
    }
}
