/**
 * FoodBook Collections View
 * Browse public community guides or view items in a specific curated collection
 */
import { api } from '../api.js';
import { state } from '../state.js';
import { HomeView } from './HomeView.js';

export class CollectionsView {
    static async render() {
        const collectionId = state.viewParams.id;

        if (collectionId) {
            return `
            <div class="collections-view container py-5" id="collection-detail-container">
                <div class="loading-state text-center py-5">
                    <div class="spinner"></div>
                    <p>Loading curated collection...</p>
                </div>
            </div>
            `;
        }

        return `
        <div class="collections-view container py-5">
            <div class="collections-header mb-5">
                <div class="header-text">
                    <span class="badge-ai mb-2">📚 Community Guides</span>
                    <h1 class="collections-title">Curated Food Collections</h1>
                    <p class="text-muted">Explore themed dining routes, budget guides, and culinary bucket lists handpicked by foodies in Lahore.</p>
                </div>
                <div class="header-action">
                    <button class="btn btn-primary" id="btn-create-col-trigger">
                        + Create Food Collection
                    </button>
                </div>
            </div>

            <!-- COMMUNITY COLLECTIONS GRID -->
            <div class="collections-grid" id="community-collections-grid">
                <div class="loading-state col-span-full">
                    <div class="spinner"></div>
                    <p>Loading community collections...</p>
                </div>
            </div>
        </div>
        `;
    }

    static async attachEvents() {
        const collectionId = state.viewParams.id;

        if (collectionId) {
            CollectionsView.loadCollectionDetail(collectionId);
        } else {
            CollectionsView.loadAllCollections();
            const createBtn = document.getElementById('btn-create-col-trigger');
            if (createBtn) {
                createBtn.addEventListener('click', () => {
                    state.notify('openCreateCollectionModal');
                });
            }
        }
    }

    static async loadAllCollections() {
        const container = document.getElementById('community-collections-grid');
        if (!container) return;

        try {
            const res = await api.getCollections(true);
            const collections = res?.data || [];

            if (collections.length === 0) {
                container.innerHTML = `
                    <div class="empty-state-box col-span-full text-center py-5">
                        <h3>No community collections found</h3>
                        <p class="text-muted">Be the first to curate a themed food collection for Lahore!</p>
                        <button class="btn btn-primary mt-3" onclick="window.state.notify('openCreateCollectionModal')">Create Collection</button>
                    </div>
                `;
                return;
            }

            container.innerHTML = collections.map(col => `
                <div class="collection-card" data-col-id="${col.id}">
                    <div class="col-header-bg">
                        <span class="col-emoji">🍽️</span>
                    </div>
                    <div class="col-body">
                        <h3 class="col-title">${col.title}</h3>
                        <p class="col-desc">${col.description || 'Curated food selection for dining lovers.'}</p>
                        <div class="col-footer">
                            <span class="col-places-count">📍 ${col.items_count || 0} spots included</span>
                            <span class="col-explore-link">Explore Collection →</span>
                        </div>
                    </div>
                </div>
            `).join('');

            container.querySelectorAll('.collection-card').forEach(card => {
                card.addEventListener('click', () => {
                    const id = card.getAttribute('data-col-id');
                    state.navigate('collections', { id });
                });
            });
        } catch (err) {
            container.innerHTML = `<p class="text-danger col-span-full">Failed to load collections.</p>`;
        }
    }

    static async loadCollectionDetail(id) {
        const container = document.getElementById('collection-detail-container');
        if (!container) return;

        try {
            const res = await api.getCollectionById(id);
            const col = res?.data;

            if (!col) {
                container.innerHTML = `
                    <div class="text-center py-5">
                        <h3>Collection not found</h3>
                        <a href="#collections" class="btn btn-primary mt-3">Back to Collections</a>
                    </div>
                `;
                return;
            }

            const items = col.items || [];

            container.innerHTML = `
                <div class="collection-detail-header mb-5">
                    <a href="#collections" class="back-link mb-3 d-inline-block">← Back to All Collections</a>
                    <h1 class="col-hero-title">${col.title}</h1>
                    <p class="col-hero-desc text-muted">${col.description || 'Curated food selection by the FoodBook community.'}</p>
                    <div class="col-meta-row mt-2">
                        <span>Created by ${col.user?.full_name || 'FoodBook Curator'}</span> • 
                        <span>${items.length} ${items.length === 1 ? 'place' : 'places'}</span>
                    </div>
                </div>

                <div class="collection-items-container">
                    ${items.length > 0 ? `
                        <div class="restaurants-grid">
                            ${items.map(item => {
                                const r = item.restaurant || {};
                                return HomeView.renderStandardRestaurantCard(r);
                            }).join('')}
                        </div>
                    ` : `
                        <div class="empty-state-box text-center py-5">
                            <p class="text-muted">No restaurants added to this collection yet.</p>
                            <a href="#explore" class="btn btn-primary mt-2">Find Food Spots to Add</a>
                        </div>
                    `}
                </div>
            `;

            HomeView.attachCardEvents(container);
        } catch (err) {
            container.innerHTML = `<p class="text-danger">Failed to load collection details.</p>`;
        }
    }
}
