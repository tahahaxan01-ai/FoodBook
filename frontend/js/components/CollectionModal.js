/**
 * FoodBook Collection Modal Component
 * Create new curated collections and add restaurants to collections
 */
import { api } from '../api.js';
import { state } from '../state.js';

export class CollectionModal {
    static render() {
        return `
        <div class="modal-overlay" id="collection-modal-overlay" style="display: none;">
            <div class="modal-card collection-modal-card">
                <button class="modal-close-btn" id="collection-modal-close" aria-label="Close modal">✕</button>

                <div class="modal-header">
                    <div class="header-icon">📚</div>
                    <div>
                        <h3 class="modal-title" id="col-modal-title">Create Food Collection</h3>
                        <p class="modal-subtitle">Curate your favorite dining spots and share with the FoodBook community.</p>
                    </div>
                </div>

                <div class="modal-body">
                    <!-- MODE 1: CREATE COLLECTION -->
                    <form id="create-collection-form">
                        <div class="form-group">
                            <label class="form-label" for="col-title">Collection Title</label>
                            <input type="text" id="col-title" class="form-control" placeholder="e.g. Best Late-Night BBQ Spots in Gulberg" required maxlength="100">
                        </div>

                        <div class="form-group">
                            <label class="form-label" for="col-desc">Description</label>
                            <textarea id="col-desc" class="form-control" rows="3" placeholder="Tell foodies what makes this curated list special..."></textarea>
                        </div>

                        <div class="form-group">
                            <label class="checkbox-label">
                                <input type="checkbox" id="col-is-public" checked>
                                <span class="checkbox-text">Make this collection public for community discovery</span>
                            </label>
                        </div>

                        <div class="modal-actions mt-4">
                            <button type="button" class="btn btn-outline" id="col-cancel-btn">Cancel</button>
                            <button type="submit" class="btn btn-primary" id="col-submit-btn">
                                <span class="btn-text">Create Collection</span>
                                <span class="btn-spinner" style="display: none;">Creating...</span>
                            </button>
                        </div>
                    </form>

                    <!-- MODE 2: ADD TO EXISTING COLLECTION -->
                    <div id="add-to-collection-view" style="display: none;">
                        <input type="hidden" id="add-col-restaurant-id">
                        <p class="text-muted mb-3">Choose which of your collections to add this restaurant to:</p>
                        <div class="user-collections-list" id="user-collections-picker">
                            <div class="loading-spinner">Loading your collections...</div>
                        </div>
                        <div class="modal-actions mt-4">
                            <button type="button" class="btn btn-outline" id="add-col-close-btn">Close</button>
                            <button type="button" class="btn btn-primary" id="add-col-new-btn">+ New Collection</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        `;
    }

    static attachEvents() {
        const overlay = document.getElementById('collection-modal-overlay');
        const closeBtn = document.getElementById('collection-modal-close');
        const cancelBtn = document.getElementById('col-cancel-btn');
        const addColCloseBtn = document.getElementById('add-col-close-btn');
        const form = document.getElementById('create-collection-form');
        const addToColView = document.getElementById('add-to-collection-view');
        const addColNewBtn = document.getElementById('add-col-new-btn');

        function closeModal() {
            if (overlay) overlay.style.display = 'none';
        }

        if (closeBtn) closeBtn.addEventListener('click', closeModal);
        if (cancelBtn) cancelBtn.addEventListener('click', closeModal);
        if (addColCloseBtn) addColCloseBtn.addEventListener('click', closeModal);
        if (overlay) {
            overlay.addEventListener('click', (e) => {
                if (e.target === overlay) closeModal();
            });
        }

        if (addColNewBtn) {
            addColNewBtn.addEventListener('click', () => {
                addToColView.style.display = 'none';
                form.style.display = 'block';
                document.getElementById('col-modal-title').textContent = 'Create Food Collection';
            });
        }

        // Open create modal
        state.subscribe('openCreateCollectionModal', () => {
            if (!state.user) {
                state.notify('requireAuth', { action: 'create_collection' });
                return;
            }
            if (!overlay) return;
            form.style.display = 'block';
            addToColView.style.display = 'none';
            document.getElementById('col-modal-title').textContent = 'Create Food Collection';
            document.getElementById('col-title').value = '';
            document.getElementById('col-desc').value = '';
            overlay.style.display = 'flex';
        });

        // Open add to collection modal
        state.subscribe('openAddToCollectionModal', async (data) => {
            if (!state.user) {
                state.notify('requireAuth', { action: 'add_to_collection' });
                return;
            }
            if (!overlay) return;
            form.style.display = 'none';
            addToColView.style.display = 'block';
            document.getElementById('col-modal-title').textContent = `Add to Collection`;
            document.getElementById('add-col-restaurant-id').value = data.restaurantId;
            overlay.style.display = 'flex';

            const picker = document.getElementById('user-collections-picker');
            picker.innerHTML = '<div class="loading-state"><div class="spinner"></div><p>Loading your collections...</p></div>';

            try {
                const res = await api.getCollections(false); // get user collections
                const collections = res?.data || [];
                if (collections.length === 0) {
                    picker.innerHTML = `
                        <div class="empty-state py-3">
                            <p class="text-muted">You haven't created any collections yet.</p>
                        </div>
                    `;
                } else {
                    picker.innerHTML = collections.map(col => `
                        <div class="col-picker-item" data-col-id="${col.id}">
                            <div class="col-picker-info">
                                <h5 class="col-picker-title">${col.title}</h5>
                                <span class="col-picker-count">${col.items_count || 0} places saved</span>
                            </div>
                            <button type="button" class="btn btn-sm btn-outline col-add-action-btn" data-col-id="${col.id}">
                                Add +
                            </button>
                        </div>
                    `).join('');

                    // Attach add item listeners
                    picker.querySelectorAll('.col-add-action-btn').forEach(btn => {
                        btn.addEventListener('click', async (e) => {
                            const colId = btn.getAttribute('data-col-id');
                            btn.disabled = true;
                            btn.textContent = 'Adding...';
                            try {
                                await api.addItemToCollection(colId, data.restaurantId);
                                btn.textContent = '✓ Added!';
                                btn.classList.remove('btn-outline');
                                btn.classList.add('btn-success');
                                state.notify('toast', { type: 'success', message: 'Added restaurant to collection! 📚' });
                            } catch (err) {
                                btn.disabled = false;
                                btn.textContent = 'Add +';
                                state.notify('toast', { type: 'error', message: err.message || 'Failed to add' });
                            }
                        });
                    });
                }
            } catch (err) {
                picker.innerHTML = '<p class="text-danger">Failed to load collections.</p>';
            }
        });

        // Submit create collection form
        if (form) {
            form.addEventListener('submit', async (e) => {
                e.preventDefault();
                const title = document.getElementById('col-title').value.trim();
                const description = document.getElementById('col-desc').value.trim();
                const isPublic = document.getElementById('col-is-public').checked;
                const submitBtn = document.getElementById('col-submit-btn');

                if (!title) return;

                submitBtn.disabled = true;
                submitBtn.querySelector('.btn-text').style.display = 'none';
                submitBtn.querySelector('.btn-spinner').style.display = 'inline-block';

                try {
                    const res = await api.createCollection({ title, description, is_public: isPublic });
                    submitBtn.disabled = false;
                    submitBtn.querySelector('.btn-text').style.display = 'inline-block';
                    submitBtn.querySelector('.btn-spinner').style.display = 'none';

                    if (res?.success) {
                        state.notify('toast', { type: 'success', message: `Collection "${title}" created! 🎉` });
                        closeModal();
                        state.notify('collectionCreated', res.data);
                    } else {
                        throw new Error(res?.message || 'Failed to create collection');
                    }
                } catch (err) {
                    submitBtn.disabled = false;
                    submitBtn.querySelector('.btn-text').style.display = 'inline-block';
                    submitBtn.querySelector('.btn-spinner').style.display = 'none';
                    state.notify('toast', { type: 'error', message: err.message || 'Error creating collection.' });
                }
            });
        }
    }
}
