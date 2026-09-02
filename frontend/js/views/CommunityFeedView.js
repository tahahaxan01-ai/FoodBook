/**
 * FoodBook Community Feed View
 * Social feed of user posts (photos + experiences) with likes and comments
 */
import { api } from '../api.js';
import { state } from '../state.js';

export class CommunityFeedView {
    static async render() {
        return `
        <div class="community-view container py-5">
            <div class="collections-header mb-5">
                <div class="header-text">
                    <span class="badge-ai mb-2">📸 Community Feed</span>
                    <h1 class="collections-title">Foodie Experiences</h1>
                    <p class="text-muted">See what fellow foodies in Lahore are eating, loving, and sharing right now.</p>
                </div>
                <div class="header-action">
                    <button class="btn btn-primary" id="btn-create-post-trigger">
                        + Share Experience
                    </button>
                </div>
            </div>

            <div class="community-feed-list" id="community-feed-list">
                <div class="loading-state text-center py-5">
                    <div class="spinner"></div>
                    <p>Loading community feed...</p>
                </div>
            </div>
        </div>
        `;
    }

    static async attachEvents() {
        const createBtn = document.getElementById('btn-create-post-trigger');
        if (createBtn) {
            createBtn.addEventListener('click', () => {
                state.notify('openPostComposerModal');
            });
        }

        state.subscribe('postCreated', () => {
            CommunityFeedView.loadFeed();
        });

        await CommunityFeedView.loadFeed();
    }

    static async loadFeed() {
        const container = document.getElementById('community-feed-list');
        if (!container) return;

        try {
            const res = await api.getFeedPosts();
            const posts = res?.data?.items || res?.data || [];

            if (posts.length === 0) {
                container.innerHTML = `
                    <div class="empty-state-box text-center py-5">
                        <div class="empty-icon">📸</div>
                        <h3>No posts yet</h3>
                        <p class="text-muted">Be the first to share a food experience with the community!</p>
                        <button class="btn btn-primary mt-3" onclick="window.state.notify('openPostComposerModal')">Share Experience</button>
                    </div>
                `;
                return;
            }

            container.innerHTML = posts.map(post => CommunityFeedView.renderPostCard(post)).join('');
            CommunityFeedView.attachPostEvents(container);
        } catch (err) {
            container.innerHTML = `<p class="text-danger text-center py-5">Failed to load community feed.</p>`;
        }
    }

    static renderPostCard(post) {
        const user = post.user || {};
        const initial = (user.full_name || user.email || 'F')[0].toUpperCase();
        const timeAgo = post.created_at ? new Date(post.created_at).toLocaleDateString() : 'Recent';
        const isLiked = !!post.is_liked_by_user;
        const likesCount = post.likes_count || 0;
        const commentsCount = post.comments_count || 0;

        return `
        <div class="post-card content-card mb-4" data-post-id="${post.id}">
            <div class="post-card-header">
                <div class="reviewer-avatar">${initial}</div>
                <div class="post-header-text">
                    <div class="reviewer-name">${user.full_name || 'Foodie'}</div>
                    <div class="review-date">${timeAgo}</div>
                </div>
                ${post.restaurant ? `
                    <a href="#restaurant/${post.restaurant.id}" class="post-restaurant-tag">📍 ${post.restaurant.name}</a>
                ` : ''}
            </div>

            <img src="${post.image_url}" alt="Food post" class="post-card-image" loading="lazy">

            <p class="post-caption mt-3">${post.caption || ''}</p>

            <div class="post-actions-row mt-3">
                <button type="button" class="post-action-btn like-btn ${isLiked ? 'active' : ''}" data-post-id="${post.id}" data-liked="${isLiked}">
                    <span class="like-icon">${isLiked ? '❤️' : '🤍'}</span>
                    <span class="like-count">${likesCount}</span>
                </button>
                <button type="button" class="post-action-btn comment-toggle-btn" data-post-id="${post.id}">
                    <span>💬</span>
                    <span class="comment-count">${commentsCount}</span>
                </button>
            </div>

            <div class="post-comments-section" id="comments-section-${post.id}" style="display: none;">
                <div class="post-comments-list" id="comments-list-${post.id}"></div>
                <form class="post-comment-form" data-post-id="${post.id}">
                    <input type="text" class="form-control post-comment-input" placeholder="Write a comment..." maxlength="300" required>
                    <button type="submit" class="btn btn-primary btn-sm">Post</button>
                </form>
            </div>
        </div>
        `;
    }

    static attachPostEvents(container) {
        // Like toggle
        container.querySelectorAll('.like-btn').forEach(btn => {
            btn.addEventListener('click', async () => {
                if (!state.user) {
                    state.notify('requireAuth', { action: 'like_post' });
                    return;
                }
                const postId = btn.getAttribute('data-post-id');
                const isLiked = btn.getAttribute('data-liked') === 'true';
                const countEl = btn.querySelector('.like-count');
                const iconEl = btn.querySelector('.like-icon');
                const newLiked = !isLiked;
                const currentCount = parseInt(countEl.textContent, 10) || 0;

                // Optimistic update
                btn.setAttribute('data-liked', String(newLiked));
                btn.classList.toggle('active', newLiked);
                iconEl.textContent = newLiked ? '❤️' : '🤍';
                countEl.textContent = newLiked ? currentCount + 1 : Math.max(0, currentCount - 1);

                try {
                    if (newLiked) {
                        await api.likePost(postId);
                    } else {
                        await api.unlikePost(postId);
                    }
                } catch (err) {
                    // Revert on failure
                    btn.setAttribute('data-liked', String(isLiked));
                    btn.classList.toggle('active', isLiked);
                    iconEl.textContent = isLiked ? '❤️' : '🤍';
                    countEl.textContent = currentCount;
                    state.notify('toast', { type: 'error', message: err.message || 'Failed to update like' });
                }
            });
        });

        // Comment toggle
        container.querySelectorAll('.comment-toggle-btn').forEach(btn => {
            btn.addEventListener('click', async () => {
                const postId = btn.getAttribute('data-post-id');
                const section = document.getElementById(`comments-section-${postId}`);
                if (!section) return;

                const isVisible = section.style.display !== 'none';
                if (isVisible) {
                    section.style.display = 'none';
                    return;
                }

                section.style.display = 'block';
                await CommunityFeedView.loadComments(postId);
            });
        });

        // Comment submit
        container.querySelectorAll('.post-comment-form').forEach(form => {
            form.addEventListener('submit', async (e) => {
                e.preventDefault();
                if (!state.user) {
                    state.notify('requireAuth', { action: 'add_comment' });
                    return;
                }
                const postId = form.getAttribute('data-post-id');
                const input = form.querySelector('.post-comment-input');
                const text = input.value.trim();
                if (!text) return;

                const submitBtn = form.querySelector('button[type="submit"]');
                submitBtn.disabled = true;

                try {
                    await api.addPostComment(postId, text);
                    input.value = '';
                    await CommunityFeedView.loadComments(postId);

                    const countEl = container.querySelector(`.comment-toggle-btn[data-post-id="${postId}"] .comment-count`);
                    if (countEl) {
                        countEl.textContent = (parseInt(countEl.textContent, 10) || 0) + 1;
                    }
                } catch (err) {
                    state.notify('toast', { type: 'error', message: err.message || 'Failed to post comment' });
                } finally {
                    submitBtn.disabled = false;
                }
            });
        });
    }

    static async loadComments(postId) {
        const list = document.getElementById(`comments-list-${postId}`);
        if (!list) return;

        list.innerHTML = `<div class="loading-state py-2"><div class="spinner"></div></div>`;

        try {
            const res = await api.getPostComments(postId);
            const comments = res?.data?.items || res?.data || [];

            if (comments.length === 0) {
                list.innerHTML = `<p class="text-muted small py-2">No comments yet. Be the first to reply!</p>`;
                return;
            }

            list.innerHTML = comments.map(c => `
                <div class="post-comment-item">
                    <div class="reviewer-avatar comment-avatar">${(c.user?.full_name || 'F')[0].toUpperCase()}</div>
                    <div class="post-comment-body">
                        <span class="post-comment-author">${c.user?.full_name || 'Foodie'}</span>
                        <span class="post-comment-text">${c.text}</span>
                    </div>
                </div>
            `).join('');
        } catch (err) {
            list.innerHTML = `<p class="text-danger small py-2">Failed to load comments.</p>`;
        }
    }
}
