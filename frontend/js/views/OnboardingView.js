/**
 * FoodBook Interactive 9D Taste Profile Onboarding Wizard
 */
import { api } from '../api.js';
import { state } from '../state.js';
import { CONFIG } from '../config.js';
import { TasteRadar } from '../components/TasteRadar.js';

export class OnboardingView {
    static async render() {
        const existingTaste = state.tasteProfile;
        const currentVector = existingTaste?.taste_vector || [0.7, 0.3, 0.6, 0.3, 0.8, 0.7, 0.6, 0.8, 0.7];
        const selectedCuisines = new Set(existingTaste?.preferred_cuisines || ["Fast Food", "Pakistani", "BBQ"]);
        const selectedDietary = new Set(existingTaste?.dietary_restrictions || ["Halal"]);
        const budget = existingTaste?.budget_level || "moderate";

        return `
        <div class="onboarding-view container py-5">
            <div class="onboarding-header text-center mb-5">
                <div class="badge-ai mb-2">🎯 9-Dimensional Flavor Engine</div>
                <h1 class="onboarding-title">Build Your Personal Food Taste Profile</h1>
                <p class="onboarding-subtitle">
                    Customize your flavor preferences. FoodBook's AI recommender matches these vectors with restaurant menus to find food you will genuinely love.
                </p>
            </div>

            <div class="onboarding-grid">
                <!-- LEFT COLUMN: CONTROLS & SLIDERS -->
                <div class="onboarding-controls">
                    <!-- SECTION 1: PREFERRED CUISINES -->
                    <div class="quiz-card mb-4">
                        <h3 class="quiz-section-title">1. What cuisines do you enjoy most?</h3>
                        <p class="text-muted small mb-3">Select 2 or more to boost matching recommendations.</p>
                        <div class="cuisines-selector-grid" id="onboarding-cuisines">
                            ${CONFIG.CUISINES.map(c => `
                                <button type="button" class="cuisine-select-btn ${selectedCuisines.has(c.name) ? 'selected' : ''}" data-cuisine="${c.name}">
                                    <span class="cuisine-btn-icon">${c.icon}</span>
                                    <span class="cuisine-btn-text">${c.name}</span>
                                </button>
                            `).join('')}
                        </div>
                    </div>

                    <!-- SECTION 2: 9D TASTE SLIDERS -->
                    <div class="quiz-card mb-4">
                        <div class="quiz-header-row">
                            <h3 class="quiz-section-title">2. Tune Your 9 Flavor Dimensions</h3>
                            <button type="button" class="btn btn-sm btn-outline" id="preset-spicy-desi">🍛 Spice & BBQ Preset</button>
                        </div>
                        <p class="text-muted small mb-4">Drag the sliders from Mild (0%) to Intense (100%).</p>

                        <div class="sliders-list" id="taste-sliders-container">
                            ${CONFIG.TASTE_DIMENSIONS.map((dim, idx) => {
                                const val = currentVector[idx] !== undefined ? currentVector[idx] : 0.5;
                                const pct = Math.round(val * 100);
                                return `
                                <div class="slider-row" data-index="${idx}">
                                    <div class="slider-info">
                                        <span class="slider-label">
                                            <span class="slider-emoji">${dim.emoji}</span>
                                            <strong>${dim.name}</strong>
                                        </span>
                                        <span class="slider-desc">${dim.desc}</span>
                                    </div>
                                    <div class="slider-control-box">
                                        <input type="range" class="taste-range-input" min="0" max="100" value="${pct}" data-index="${idx}">
                                        <span class="slider-val-badge" id="val-badge-${idx}">${pct}%</span>
                                    </div>
                                </div>
                                `;
                            }).join('')}
                        </div>
                    </div>

                    <!-- SECTION 3: DIETARY & BUDGET -->
                    <div class="quiz-card mb-4">
                        <h3 class="quiz-section-title">3. Dietary Preferences & Budget</h3>
                        
                        <div class="form-group mt-3">
                            <label class="form-label">Dietary Restrictions</label>
                            <div class="chips-list" id="dietary-chips">
                                ${['Halal', 'Vegetarian', 'Vegan', 'Gluten-Free', 'Dairy-Free', 'Nut-Free'].map(d => `
                                    <button type="button" class="filter-chip ${selectedDietary.has(d) ? 'active' : ''}" data-diet="${d}">
                                        ${d}
                                    </button>
                                `).join('')}
                            </div>
                        </div>

                        <div class="form-group mt-4">
                            <label class="form-label">Dining Budget Preference</label>
                            <div class="budget-options-row" id="budget-options">
                                <button type="button" class="budget-btn ${budget === 'budget' ? 'active' : ''}" data-budget="budget">
                                    <span class="budget-icon">💵</span>
                                    <strong>Budget</strong>
                                    <small>Under Rs. 800</small>
                                </button>
                                <button type="button" class="budget-btn ${budget === 'moderate' ? 'active' : ''}" data-budget="moderate">
                                    <span class="budget-icon">💳</span>
                                    <strong>Moderate</strong>
                                    <small>Rs. 800 - 2,500</small>
                                </button>
                                <button type="button" class="budget-btn ${budget === 'fine_dining' ? 'active' : ''}" data-budget="fine_dining">
                                    <span class="budget-icon">💎</span>
                                    <strong>Fine Dining</strong>
                                    <small>Rs. 2,500+</small>
                                </button>
                            </div>
                        </div>
                    </div>

                    <!-- SAVE CTA -->
                    <div class="quiz-cta-row">
                        <button type="button" class="btn btn-primary btn-lg btn-block" id="save-taste-profile-btn">
                            <span class="btn-text">Save Taste Profile & Explore Matches 🚀</span>
                            <span class="btn-spinner" style="display: none;">Saving...</span>
                        </button>
                    </div>
                </div>

                <!-- RIGHT COLUMN: LIVE RADAR PREVIEW -->
                <div class="onboarding-preview-sidebar">
                    <div class="radar-preview-card sticky-sidebar">
                        <div class="preview-header">
                            <span class="radar-live-indicator">● LIVE PREVIEW</span>
                            <h4 class="preview-title">Your 9D Taste Radar</h4>
                            <p class="text-muted small">Watch your flavor footprint evolve in real-time.</p>
                        </div>
                        <div class="radar-canvas-box">
                            <canvas id="onboarding-radar-canvas"></canvas>
                        </div>
                        <div class="radar-hints mt-3">
                            <div class="hint-item">
                                <span class="hint-dot" style="background:#3B82F6"></span>
                                <span>Higher points indicate stronger flavor preference</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        `;
    }

    static attachEvents() {
        const canvas = document.getElementById('onboarding-radar-canvas');
        const sliders = document.querySelectorAll('.taste-range-input');
        const saveBtn = document.getElementById('save-taste-profile-btn');
        const presetDesiBtn = document.getElementById('preset-spicy-desi');

        function getCurrentVector() {
            const vector = [];
            sliders.forEach(slider => {
                const val = parseFloat(slider.value) / 100.0;
                vector.push(val);
            });
            return vector;
        }

        function updateRadar() {
            const vec = getCurrentVector();
            TasteRadar.render(canvas, {
                userVector: vec,
                restaurantVector: null,
                restaurantName: "Your Palate"
            });
        }

        updateRadar();

        // Sliders change
        sliders.forEach(slider => {
            slider.addEventListener('input', () => {
                const idx = slider.getAttribute('data-index');
                const badge = document.getElementById(`val-badge-${idx}`);
                if (badge) badge.textContent = `${slider.value}%`;
                updateRadar();
            });
        });

        // Preset Spicy Desi
        if (presetDesiBtn) {
            presetDesiBtn.addEventListener('click', () => {
                const desiPreset = [85, 20, 75, 30, 90, 85, 45, 70, 90];
                sliders.forEach((slider, i) => {
                    slider.value = desiPreset[i];
                    const badge = document.getElementById(`val-badge-${i}`);
                    if (badge) badge.textContent = `${desiPreset[i]}%`;
                });
                updateRadar();
                state.notify('toast', { type: 'info', message: 'Applied Spicy & Smoky Desi preset!' });
            });
        }

        // Cuisine selection toggle
        document.querySelectorAll('.cuisine-select-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                btn.classList.toggle('selected');
            });
        });

        // Dietary chips toggle
        document.querySelectorAll('#dietary-chips .filter-chip').forEach(btn => {
            btn.addEventListener('click', () => {
                btn.classList.toggle('active');
            });
        });

        // Budget toggle
        document.querySelectorAll('#budget-options .budget-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('#budget-options .budget-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
            });
        });

        // Save Button Submit
        if (saveBtn) {
            saveBtn.addEventListener('click', async () => {
                if (!state.user) {
                    state.notify('requireAuth', { action: 'save_taste_profile' });
                    return;
                }

                const selectedCuisines = Array.from(document.querySelectorAll('.cuisine-select-btn.selected'))
                    .map(b => b.getAttribute('data-cuisine'));
                const selectedDietary = Array.from(document.querySelectorAll('#dietary-chips .filter-chip.active'))
                    .map(b => b.getAttribute('data-diet'));
                const selectedBudget = document.querySelector('#budget-options .budget-btn.active')?.getAttribute('data-budget') || 'moderate';
                const tasteVector = getCurrentVector();

                saveBtn.disabled = true;
                saveBtn.querySelector('.btn-text').style.display = 'none';
                saveBtn.querySelector('.btn-spinner').style.display = 'inline-block';

                try {
                    const payload = {
                        taste_vector: tasteVector,
                        preferred_cuisines: selectedCuisines.length > 0 ? selectedCuisines : ["Fast Food", "Pakistani"],
                        dietary_restrictions: selectedDietary,
                        budget_level: selectedBudget
                    };

                    const res = await api.updateTasteProfile(payload);
                    saveBtn.disabled = false;
                    saveBtn.querySelector('.btn-text').style.display = 'inline-block';
                    saveBtn.querySelector('.btn-spinner').style.display = 'none';

                    if (res?.success) {
                        state.tasteProfile = res.data;
                        state.notify('tasteProfileChanged', res.data);
                        state.notify('toast', {
                            type: 'success',
                            message: 'Taste Profile updated! Recommendations refreshed. 🎯'
                        });
                        state.navigate('home');
                    } else {
                        throw new Error(res?.message || 'Failed to save taste profile');
                    }
                } catch (err) {
                    saveBtn.disabled = false;
                    saveBtn.querySelector('.btn-text').style.display = 'inline-block';
                    saveBtn.querySelector('.btn-spinner').style.display = 'none';
                    state.notify('toast', { type: 'error', message: err.message || 'Error updating taste profile' });
                }
            });
        }
    }
}
