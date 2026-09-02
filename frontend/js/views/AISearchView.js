/**
 * FoodBook Conversational AI Food Finder View
 * Natural Language Query Parsing + 9D Vector Ranked Results
 */
import { api } from '../api.js';
import { state } from '../state.js';
import { HomeView } from './HomeView.js';

export class AISearchView {
    static async render() {
        const initialQuery = state.viewParams.q || "";

        return `
        <div class="ai-search-view container py-5">
            <div class="ai-search-header text-center mb-5">
                <div class="badge-ai mb-2">✨ AI Conversational Discovery</div>
                <h1 class="ai-title">Ask FoodBook in Natural Language</h1>
                <p class="ai-subtitle">
                    Type what you crave in your own words. Our NLP & 9D Flavor Engine extracts cuisines, spice preferences, 
                    price constraints, and taste aspects to find the ideal spot.
                </p>
            </div>

            <!-- SEARCH PROMPT BOX -->
            <div class="ai-prompt-box mb-5">
                <form id="ai-search-form" class="ai-form">
                    <div class="ai-input-wrapper">
                        <span class="ai-input-icon">✨</span>
                        <input type="text" id="ai-search-input" class="ai-text-input" 
                            placeholder="e.g. 'I want a cozy cafe with creamy spicy pasta under 1500 in Gulberg'..." 
                            value="${initialQuery}" required autocomplete="off">
                        <button type="submit" class="btn btn-primary ai-submit-btn" id="ai-search-btn">
                            <span class="btn-text">Find Food</span>
                            <span class="btn-spinner" style="display: none;">Analyzing...</span>
                        </button>
                    </div>
                </form>

                <!-- PROMPT SUGGESTION CHIPS -->
                <div class="prompt-suggestions mt-3 text-center">
                    <span class="text-muted small">Try asking:</span>
                    <div class="prompt-chips-list mt-2">
                        <button class="prompt-chip" data-q="Super cheesy and crispy pizza under 1800">
                            🍕 "Super cheesy and crispy pizza under 1800"
                        </button>
                        <button class="prompt-chip" data-q="Smoky and spicy chicken tikka karahi for dinner">
                            🔥 "Smoky and spicy chicken tikka karahi"
                        </button>
                        <button class="prompt-chip" data-q="Cozy aesthetic cafe with rich desserts under 1200">
                            ☕ "Cozy cafe with rich desserts under 1200"
                        </button>
                        <button class="prompt-chip" data-q="Authentic Pakistani BBQ within 5km">
                            🍢 "Authentic Pakistani BBQ within 5km"
                        </button>
                    </div>
                </div>
            </div>

            <!-- AI PARSED INTENT BOX (Rendered on search) -->
            <div id="ai-intent-breakdown" class="ai-intent-card mb-5" style="display: none;">
                <!-- Populated dynamically -->
            </div>

            <!-- RESULTS GRID -->
            <div class="ai-results-section">
                <div class="section-header" id="ai-results-header" style="display: none;">
                    <div>
                        <h2 class="section-title">AI Ranked Recommendations</h2>
                        <p class="section-subtitle" id="ai-results-subtitle">Matches tailored to your prompt analysis.</p>
                    </div>
                </div>

                <div class="restaurants-grid" id="ai-results-grid">
                    ${!initialQuery ? `
                        <div class="empty-state-box col-span-full text-center py-5">
                            <div class="empty-icon">🤖</div>
                            <h3>What are you craving today?</h3>
                            <p class="text-muted">Type any sentence describing your hunger, taste, or budget above to start searching!</p>
                        </div>
                    ` : `
                        <div class="loading-state col-span-full">
                            <div class="spinner"></div>
                            <p>Analyzing flavor parameters and querying restaurants...</p>
                        </div>
                    `}
                </div>
            </div>
        </div>
        `;
    }

    static async attachEvents() {
        const form = document.getElementById('ai-search-form');
        const input = document.getElementById('ai-search-input');
        const promptChips = document.querySelectorAll('.prompt-chip');
        const initialQuery = state.viewParams.q;

        async function executeAISearch(queryText) {
            if (!queryText) return;

            const grid = document.getElementById('ai-results-grid');
            const intentBox = document.getElementById('ai-intent-breakdown');
            const resultsHeader = document.getElementById('ai-results-header');
            const submitBtn = document.getElementById('ai-search-btn');

            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.querySelector('.btn-text').style.display = 'none';
                submitBtn.querySelector('.btn-spinner').style.display = 'inline-block';
            }

            grid.innerHTML = `
                <div class="loading-state col-span-full">
                    <div class="spinner"></div>
                    <p>Analyzing flavor parameters and ranking matching spots...</p>
                </div>
            `;

            try {
                // Rule-based / NLP prompt parsing
                const queryLower = queryText.toLowerCase();

                // 1. Detect Cuisines
                const detectedCuisines = [];
                if (queryLower.includes('pizza')) detectedCuisines.push('Pizza');
                if (queryLower.includes('burger')) detectedCuisines.push('Burger');
                if (queryLower.includes('bbq') || queryLower.includes('tikka') || queryLower.includes('karahi')) {
                    detectedCuisines.push('Pakistani', 'BBQ');
                }
                if (queryLower.includes('pasta') || queryLower.includes('italian')) detectedCuisines.push('Italian');
                if (queryLower.includes('chinese') || queryLower.includes('chowmein')) detectedCuisines.push('Chinese');
                if (queryLower.includes('cafe') || queryLower.includes('coffee') || queryLower.includes('dessert')) detectedCuisines.push('Cafe');

                // 2. Detect Budget
                let budgetConstraint = null;
                const budgetMatch = queryLower.match(/under\s+(\d+)/i) || queryLower.match(/rs\.?\s*(\d+)/i) || queryLower.match(/(\d+)\s*rs/i);
                if (budgetMatch) {
                    budgetConstraint = parseFloat(budgetMatch[1]);
                }

                // 3. Detect Taste Aspects -> both display tags AND a real 9D taste
                // vector [spicy, sweet, salty, sour, umami, smoky, creamy, crispy, rich]
                // so the ranking engine actually uses what was typed, not just cuisine/budget.
                const detectedAspects = [];
                const tasteVector = [0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5];
                if (queryLower.includes('spicy') || queryLower.includes('chili') || queryLower.includes('hot')) {
                    detectedAspects.push('🌶️ High Spice');
                    tasteVector[0] = 0.9;
                }
                if (queryLower.includes('mild') || queryLower.includes('not spicy')) tasteVector[0] = 0.15;
                if (queryLower.includes('creamy') || queryLower.includes('cheesy') || queryLower.includes('butter')) {
                    detectedAspects.push('🧀 Creamy / Cheesy');
                    tasteVector[6] = 0.9;
                }
                if (queryLower.includes('smoky') || queryLower.includes('bbq') || queryLower.includes('charcoal')) {
                    detectedAspects.push('🔥 Smoky Aroma');
                    tasteVector[5] = 0.9;
                }
                if (queryLower.includes('crispy') || queryLower.includes('crunchy')) {
                    detectedAspects.push('🍟 Crispy Texture');
                    tasteVector[7] = 0.9;
                }
                if (queryLower.includes('sweet') || queryLower.includes('sugar') || queryLower.includes('dessert')) {
                    detectedAspects.push('🍯 Sweetness');
                    tasteVector[1] = 0.9;
                }
                if (queryLower.includes('rich') || queryLower.includes('buttery') || queryLower.includes('indulgent')) tasteVector[8] = 0.85;
                const hasTasteSignal = detectedAspects.length > 0;

                // Render Intent Card
                intentBox.innerHTML = `
                    <div class="intent-card-inner">
                        <div class="intent-title-row">
                            <h4>🤖 AI Extracted Query Parameters</h4>
                        </div>
                        <div class="intent-tags-list mt-2">
                            <div class="intent-tag">
                                <strong>Cuisines:</strong> ${detectedCuisines.length > 0 ? detectedCuisines.join(', ') : 'Any Match'}
                            </div>
                            <div class="intent-tag">
                                <strong>Budget:</strong> ${budgetConstraint ? 'Max Rs. ' + budgetConstraint : 'Flexible'}
                            </div>
                            <div class="intent-tag">
                                <strong>Flavor Notes:</strong> ${detectedAspects.length > 0 ? detectedAspects.join(' • ') : 'Standard Balance'}
                            </div>
                        </div>
                    </div>
                `;
                intentBox.style.display = 'block';

                // Fetch recommendations from backend, powered by the real 9D taste
                // vector + cuisine + location signal extracted above.
                const customRequest = {
                    preferred_cuisines: detectedCuisines.length > 0 ? detectedCuisines : ["Pakistani"],
                    max_budget: budgetConstraint,
                    taste_vector: hasTasteSignal ? tasteVector : undefined,
                    latitude: state.currentLocation?.latitude,
                    longitude: state.currentLocation?.longitude,
                    limit: 8
                };

                const res = await api.postCustomRecommendations(customRequest);
                const recs = res?.data?.recommendations || [];

                if (resultsHeader) resultsHeader.style.display = 'flex';

                if (recs.length === 0) {
                    grid.innerHTML = `
                        <div class="empty-state-box col-span-full text-center py-5">
                            <h3>No exact matches for this prompt</h3>
                            <p class="text-muted">Try adjusting your budget or asking for a broader cuisine.</p>
                        </div>
                    `;
                } else {
                    grid.innerHTML = recs.map(item => HomeView.renderRecommendationCard(item)).join('');
                    HomeView.attachCardEvents(grid);
                }
            } catch (err) {
                console.error('AI search failed:', err);
                grid.innerHTML = `<p class="text-danger col-span-full">AI Search service error. Please try again.</p>`;
            } finally {
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.querySelector('.btn-text').style.display = 'inline-block';
                    submitBtn.querySelector('.btn-spinner').style.display = 'none';
                }
            }
        }

        if (form) {
            form.addEventListener('submit', (e) => {
                e.preventDefault();
                const q = input.value.trim();
                executeAISearch(q);
            });
        }

        promptChips.forEach(chip => {
            chip.addEventListener('click', () => {
                const q = chip.getAttribute('data-q');
                if (input) input.value = q;
                executeAISearch(q);
            });
        });

        if (initialQuery) {
            executeAISearch(initialQuery);
        }
    }
}
