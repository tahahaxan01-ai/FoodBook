/**
 * FoodBook Community Post Composer Modal
 * Share a food experience (photo + caption) with the community, optionally tagging a restaurant
 */
import { api } from '../api.js';
import { state } from '../state.js';

export class PostComposerModal {
    static render() {
        return `
        <div class="modal-overlay" id="post-modal-overlay" style="display: none;">
            <div class="modal-card post-modal-card">
                <button class="modal-close-btn" id="post-modal-close" aria-label="Close modal">✕</button>

                <div class="modal-header">
                    <div class="header-icon">📸</div>
                    <div>
                        <h3 class="modal-title">Share a Food Experience</h3>
                        <p class="modal-subtitle">Post a photo and your story with the FoodBook community.</p>
                    </div>
                </div>

                <div class="modal-body">
                    <form id="post-form">
                        <div class="form-group">
                            <label class="form-label" for="post-image-url">Photo URL</label>
                            <input type="url" id="post-image-url" class="form-control" placeholder="https://..." required>
                            <div class="post-image-preview mt-2" id="post-image-preview" style="display: none;">
                                <img id="post-image-preview-img" alt="Preview">
                            </div>
                        </div>

                        <div class="form-group">
                            <label class="form-label" for="post-caption">Caption</label>
                            <textarea id="post-caption" class="form-control" rows="3"
                                placeholder="What did you eat? How was it?" required maxlength="500"></textarea>
                        </div>

                        <div class="form-group post-tag-group">
                            <label class="form-label" for="post-restaurant-search">Tag a Restaurant (optional)</label>
                            <input type="text" id="post-restaurant-search" class="form-control" placeholder="Search restaurant name...">
                            <input type="hidden" id="post-restaurant-id">
                            <div class="post-tag-results" id="post-tag-results" style="display: none;"></div>
                            <div class="post-tag-selected" id="post-tag-selected" style="display: none;"></div>
                        </div>

                        <div class="modal-actions mt-4">
                            <button type="button" class="btn btn-outline" id="post-cancel-btn">Cancel</button>
                            <button type="submit" class="btn btn-primary" id="post-submit-btn">
                                <span class="btn-text">Share Post</span>
                                <span class="btn-spinner" style="display: none;">Posting...</span>
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
        `;
    }

    static attachEvents() {
        const overlay = document.getElementById('post-modal-overlay');
        const closeBtn = document.getElementById('post-modal-close');
        const cancelBtn = document.getElementById('post-cancel-btn');
        const form = document.getElementById('post-form');
        const imageInput = document.getElementById('post-image-url');
        const imagePreview = document.getElementById('post-image-preview');
        const imagePreviewImg = document.getElementById('post-image-preview-img');
        const restaurantSearch = document.getElementById('post-restaurant-search');
        const restaurantIdInput = document.getElementById('post-restaurant-id');
        const tagResults = document.getElementById('post-tag-results');
        const tagSelected = document.getElementById('post-tag-selected');

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

        if (imageInput) {
            imageInput.addEventListener('input', () => {
                const url = imageInput.value.trim();
                if (url) {
                    imagePreviewImg.src = url;
                    imagePreview.style.display = 'block';
                } else {
                    imagePreview.style.display = 'none';
                }
            });
        }

        function clearRestaurantTag() {
            restaurantIdInput.value = '';
            tagSelected.style.display = 'none';
            tagSelected.innerHTML = '';
            restaurantSearch.value = '';
        }

        let searchDebounce = null;
        if (restaurantSearch) {
            restaurantSearch.addEventListener('input', () => {
                const q = restaurantSearch.value.trim();
                clearTimeout(searchDebounce);
                if (q.length < 2) {
                    tagResults.style.display = 'none';
                    return;
                }
                searchDebounce = setTimeout(async () => {
                    try {
                        const res = await api.getRestaurants({ search: q, limit: 6 });
                        const items = res?.data?.items || res?.data || [];
                        if (items.length === 0) {
                            tagResults.innerHTML = `<div class="post-tag-empty">No restaurants found</div>`;
                        } else {
                            tagResults.innerHTML = items.map(r => `
                                <div class="post-tag-option" data-id="${r.id}" data-name="${r.name}">${r.name}</div>
                            `).join('');
                        }
                        tagResults.style.display = 'block';

                        tagResults.querySelectorAll('.post-tag-option').forEach(opt => {
                            opt.addEventListener('click', () => {
                                restaurantIdInput.value = opt.getAttribute('data-id');
                                const name = opt.getAttribute('data-name');
                                tagSelected.innerHTML = `
                                    <span class="filter-chip active">📍 ${name}
                                        <button type="button" class="tag-remove-btn" id="post-tag-remove">✕</button>
                                    </span>
                                `;
                                tagSelected.style.display = 'block';
                                restaurantSearch.value = '';
                                tagResults.style.display = 'none';
                                document.getElementById('post-tag-remove').addEventListener('click', clearRestaurantTag);
                            });
                        });
                    } catch (err) {
                        tagResults.style.display = 'none';
                    }
                }, 300);
            });
        }

        state.subscribe('openPostComposerModal', () => {
            if (!state.user) {
                state.notify('requireAuth', { action: 'create_post' });
                return;
            }
            if (!overlay) return;
            form.reset();
            imagePreview.style.display = 'none';
            clearRestaurantTag();
            overlay.style.display = 'flex';
        });

        if (form) {
            form.addEventListener('submit', async (e) => {
                e.preventDefault();
                const imageUrl = imageInput.value.trim();
                const caption = document.getElementById('post-caption').value.trim();
                const restaurantId = restaurantIdInput.value || null;
                const submitBtn = document.getElementById('post-submit-btn');

                if (!imageUrl || !caption) return;

                submitBtn.disabled = true;
                submitBtn.querySelector('.btn-text').style.display = 'none';
                submitBtn.querySelector('.btn-spinner').style.display = 'inline-block';

                try {
                    const res = await api.createPost({
                        image_url: imageUrl,
                        caption,
                        restaurant_id: restaurantId
                    });
                    submitBtn.disabled = false;
                    submitBtn.querySelector('.btn-text').style.display = 'inline-block';
                    submitBtn.querySelector('.btn-spinner').style.display = 'none';

                    if (res?.success) {
                        state.notify('toast', { type: 'success', message: 'Post shared with the community! 🎉' });
                        closeModal();
                        state.notify('postCreated', res.data);
                    } else {
                        throw new Error(res?.message || 'Failed to share post');
                    }
                } catch (err) {
                    submitBtn.disabled = false;
                    submitBtn.querySelector('.btn-text').style.display = 'inline-block';
                    submitBtn.querySelector('.btn-spinner').style.display = 'none';
                    state.notify('toast', { type: 'error', message: err.message || 'Error sharing post.' });
                }
            });
        }
    }
}
