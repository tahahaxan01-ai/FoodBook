/**
 * FoodBook Aspect-Based Review Modal Component
 * Submits multi-attribute review and triggers AI taste vector extraction
 */
import { api } from '../api.js';
import { state } from '../state.js';

export class ReviewModal {
    static render() {
        return `
        <div class="modal-overlay" id="review-modal-overlay" style="display: none;">
            <div class="modal-card review-modal-card">
                <button class="modal-close-btn" id="review-modal-close" aria-label="Close modal">✕</button>

                <div class="modal-header">
                    <div class="header-icon">✍️</div>
                    <div>
                        <h3 class="modal-title" id="review-modal-title">Write a Taste Review</h3>
                        <p class="modal-subtitle" id="review-modal-subtitle">Share your authentic food experience to improve recommendations for everyone.</p>
                    </div>
                </div>

                <div class="modal-body">
                    <form id="review-form">
                        <input type="hidden" id="review-restaurant-id">

                        <!-- Overall Star Rating -->
                        <div class="form-group text-center mb-4">
                            <label class="form-label mb-2">Overall Experience</label>
                            <div class="star-rating-picker" id="star-picker">
                                <span class="star-item" data-value="1">★</span>
                                <span class="star-item" data-value="2">★</span>
                                <span class="star-item" data-value="3">★</span>
                                <span class="star-item" data-value="4">★</span>
                                <span class="star-item" data-value="5">★</span>
                            </div>
                            <div class="rating-label-display" id="star-rating-label">Select your rating</div>
                            <input type="hidden" id="review-overall-rating" value="5">
                        </div>

                        <!-- Written Review Text -->
                        <div class="form-group">
                            <label class="form-label" for="review-text">
                                Your Detailed Food Experience
                                <span class="badge-ai-micro">AI Aspect Analyzed</span>
                            </label>
                            <textarea id="review-text" class="form-control" rows="4" 
                                placeholder="e.g. The pizza was super cheesy, creamy, and loaded with smoky chicken, but it was a bit too salty. Service was swift!" required></textarea>
                            <div class="ai-live-aspects mt-2" id="ai-live-aspects" style="display: none;">
                                <span class="ai-tag-label">🤖 Detected Aspects:</span>
                                <span class="ai-aspect-chips" id="ai-aspect-chips"></span>
                            </div>
                        </div>

                        <!-- Multi-Dimension Ratings Grid -->
                        <div class="form-group">
                            <label class="form-label">Key Dimension Breakdown</label>
                            <div class="dimension-rating-grid">
                                <div class="dim-rating-item">
                                    <span class="dim-name">👅 Taste Quality</span>
                                    <div class="dim-options" data-dim="taste">
                                        <button type="button" class="dim-chip active" data-score="5">Amazing</button>
                                        <button type="button" class="dim-chip" data-score="3">Average</button>
                                        <button type="button" class="dim-chip" data-score="1">Poor</button>
                                    </div>
                                </div>
                                <div class="dim-rating-item">
                                    <span class="dim-name">🌶️ Spice Level</span>
                                    <div class="dim-options" data-dim="spice">
                                        <button type="button" class="dim-chip" data-score="5">Fiery High</button>
                                        <button type="button" class="dim-chip active" data-score="3">Moderate</button>
                                        <button type="button" class="dim-chip" data-score="1">Mild</button>
                                    </div>
                                </div>
                                <div class="dim-rating-item">
                                    <span class="dim-name">🍛 Portion Size</span>
                                    <div class="dim-options" data-dim="portion">
                                        <button type="button" class="dim-chip active" data-score="5">Generous</button>
                                        <button type="button" class="dim-chip" data-score="3">Decent</button>
                                        <button type="button" class="dim-chip" data-score="1">Small</button>
                                    </div>
                                </div>
                                <div class="dim-rating-item">
                                    <span class="dim-name">💰 Value for Money</span>
                                    <div class="dim-options" data-dim="value">
                                        <button type="button" class="dim-chip active" data-score="5">Great Value</button>
                                        <button type="button" class="dim-chip" data-score="3">Fair</button>
                                        <button type="button" class="dim-chip" data-score="1">Overpriced</button>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- Specific Dish Rating (Optional) -->
                        <div class="form-group" id="dish-select-group" style="display: none;">
                            <label class="form-label" for="review-dish-select">Specific Dish Highlighted</label>
                            <select id="review-dish-select" class="form-control">
                                <option value="">Select dish tried (optional)...</option>
                            </select>
                        </div>

                        <div class="modal-actions mt-4">
                            <button type="button" class="btn btn-outline" id="review-cancel-btn">Cancel</button>
                            <button type="submit" class="btn btn-primary" id="review-submit-btn">
                                <span class="btn-text">Publish Review & AI Analysis</span>
                                <span class="btn-spinner" style="display: none;">Analyzing & Posting...</span>
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
        `;
    }

    static attachEvents() {
        const overlay = document.getElementById('review-modal-overlay');
        const closeBtn = document.getElementById('review-modal-close');
        const cancelBtn = document.getElementById('review-cancel-btn');
        const form = document.getElementById('review-form');
        const starPicker = document.getElementById('star-picker');
        const starRatingInput = document.getElementById('review-overall-rating');
        const starLabelDisplay = document.getElementById('star-rating-label');
        const reviewTextArea = document.getElementById('review-text');
        const liveAspectsContainer = document.getElementById('ai-live-aspects');
        const liveAspectChips = document.getElementById('ai-aspect-chips');

        const ratingLabels = {
            1: "1.0 - Disappointing",
            2: "2.0 - Below Average",
            3: "3.0 - Good",
            4: "4.0 - Very Good",
            5: "5.0 - Outstanding Food Experience!"
        };

        function setStars(value) {
            starRatingInput.value = value;
            starLabelDisplay.textContent = ratingLabels[value] || `${value}.0 Stars`;
            const stars = starPicker.querySelectorAll('.star-item');
            stars.forEach((s, idx) => {
                if (idx < value) {
                    s.classList.add('selected');
                } else {
                    s.classList.remove('selected');
                }
            });
        }

        // Star picker click & hover
        if (starPicker) {
            const stars = starPicker.querySelectorAll('.star-item');
            stars.forEach(star => {
                star.addEventListener('click', () => {
                    const val = parseInt(star.getAttribute('data-value'), 10);
                    setStars(val);
                });
            });
            setStars(5);
        }

        // Dimension buttons toggle
        document.querySelectorAll('.dim-options .dim-chip').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const parent = btn.closest('.dim-options');
                parent.querySelectorAll('.dim-chip').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
            });
        });

        // Live Aspect Extraction preview as user types
        const TASTE_KEYWORDS = [
            'cheesy', 'creamy', 'spicy', 'smoky', 'crispy', 'crunchy', 'tender', 'juicy',
            'sweet', 'salty', 'sour', 'tangy', 'rich', 'buttery', 'mild', 'hot', 'greasy', 'savory'
        ];

        if (reviewTextArea) {
            reviewTextArea.addEventListener('input', () => {
                const text = reviewTextArea.value.toLowerCase();
                const found = TASTE_KEYWORDS.filter(k => text.includes(k));
                if (found.length > 0) {
                    liveAspectChips.innerHTML = found.map(f => `<span class="aspect-chip-badge">✨ ${f}</span>`).join(' ');
                    liveAspectsContainer.style.display = 'block';
                } else {
                    liveAspectsContainer.style.display = 'none';
                }
            });
        }

        function closeModal() {
            if (overlay) overlay.style.display = 'none';
        }

        if (closeBtn) closeBtn.addEventListener('click', closeModal);
        if (cancelBtn) cancelBtn.addEventListener('click', closeModal);
        if (overlay) {
            overlay.addEventListener('click', (e) => {
                if (e.target === overlay) closeModal();
            });
        }

        // Listen for openReviewModal event
        state.subscribe('openReviewModal', (data) => {
            if (!state.user) {
                state.notify('requireAuth', { action: 'write_review' });
                return;
            }

            if (!overlay) return;
            document.getElementById('review-restaurant-id').value = data.restaurantId || '';
            document.getElementById('review-modal-title').textContent = `Review ${data.restaurantName || 'Restaurant'}`;
            reviewTextArea.value = '';
            liveAspectsContainer.style.display = 'none';
            setStars(5);

            // Populate dishes dropdown if menu items provided
            const dishSelect = document.getElementById('review-dish-select');
            const dishGroup = document.getElementById('dish-select-group');
            if (data.menuItems && data.menuItems.length > 0 && dishSelect && dishGroup) {
                dishSelect.innerHTML = `<option value="">Select dish tried (optional)...</option>` +
                    data.menuItems.map(d => `<option value="${d.id}">${d.name} (${d.price_pkr ? 'Rs. ' + d.price_pkr : ''})</option>`).join('');
                dishGroup.style.display = 'block';
            } else if (dishGroup) {
                dishGroup.style.display = 'none';
            }

            overlay.style.display = 'flex';
        });

        // Submit Review Form
        if (form) {
            form.addEventListener('submit', async (e) => {
                e.preventDefault();
                const restaurantId = document.getElementById('review-restaurant-id').value;
                const overallRating = parseFloat(document.getElementById('review-overall-rating').value) || 5.0;
                const reviewText = reviewTextArea.value.trim();
                const dishId = document.getElementById('review-dish-select')?.value || null;
                const submitBtn = document.getElementById('review-submit-btn');

                if (!restaurantId || !reviewText) {
                    state.notify('toast', { type: 'error', message: 'Please provide review text.' });
                    return;
                }

                submitBtn.disabled = true;
                submitBtn.querySelector('.btn-text').style.display = 'none';
                submitBtn.querySelector('.btn-spinner').style.display = 'inline-block';

                try {
                    const dishRatings = [];
                    if (dishId) {
                        dishRatings.push({
                            menu_item_id: dishId,
                            rating: overallRating,
                            comment: reviewText.slice(0, 100)
                        });
                    }

                    const payload = {
                        restaurant_id: restaurantId,
                        overall_rating: overallRating,
                        review_text: reviewText,
                        dish_ratings: dishRatings
                    };

                    const res = await api.createReview(payload);
                    submitBtn.disabled = false;
                    submitBtn.querySelector('.btn-text').style.display = 'inline-block';
                    submitBtn.querySelector('.btn-spinner').style.display = 'none';

                    if (res?.success) {
                        state.notify('toast', {
                            type: 'success',
                            message: 'Review published! AI has updated restaurant flavor vectors. 🌟'
                        });
                        closeModal();
                        state.notify('reviewCreated', res.data);
                    } else {
                        throw new Error(res?.message || 'Failed to submit review');
                    }
                } catch (err) {
                    submitBtn.disabled = false;
                    submitBtn.querySelector('.btn-text').style.display = 'inline-block';
                    submitBtn.querySelector('.btn-spinner').style.display = 'none';
                    state.notify('toast', { type: 'error', message: err.message || 'Error publishing review.' });
                }
            });
        }
    }
}
