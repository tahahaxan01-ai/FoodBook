/**
 * FoodBook Footer Component
 */
export class Footer {
    static render() {
        return `
        <footer class="footer-container">
            <div class="footer-inner container">
                <div class="footer-grid">
                    <!-- Brand column -->
                    <div class="footer-col brand-col">
                        <div class="footer-brand">
                            <span class="logo-icon">🍽️</span>
                            <span class="brand-text">Food<span class="brand-highlight">Book</span></span>
                        </div>
                        <p class="footer-desc">
                            AI-Powered Personalized Food Discovery for Pakistan. Discover restaurants matching your individual 9-dimensional taste profile.
                        </p>
                        <div class="footer-social-links">
                            <a href="#" class="social-icon" title="Instagram">📸</a>
                            <a href="#" class="social-icon" title="Twitter">🐦</a>
                            <a href="#" class="social-icon" title="Facebook">👍</a>
                            <a href="#" class="social-icon" title="GitHub">💻</a>
                        </div>
                    </div>

                    <!-- Quick Discovery -->
                    <div class="footer-col">
                        <h4 class="footer-heading">Taste Discovery</h4>
                        <ul class="footer-links">
                            <li><a href="#explore">Lahore Restaurants</a></li>
                            <li><a href="#ai-search">AI Conversational Search</a></li>
                            <li><a href="#onboarding">Taste Profile Quiz</a></li>
                            <li><a href="#collections">Curated Food Guides</a></li>
                            <li><a href="#explore?cuisine=Fast Food">Top Fast Food Spots</a></li>
                            <li><a href="#explore?cuisine=BBQ">Best BBQ in Town</a></li>
                        </ul>
                    </div>

                    <!-- Supported Cuisines -->
                    <div class="footer-col">
                        <h4 class="footer-heading">Cuisines</h4>
                        <div class="footer-tags">
                            <span class="footer-tag">Fast Food</span>
                            <span class="footer-tag">Pakistani</span>
                            <span class="footer-tag">Desi</span>
                            <span class="footer-tag">BBQ</span>
                            <span class="footer-tag">Chinese</span>
                            <span class="footer-tag">Italian</span>
                            <span class="footer-tag">Turkish</span>
                            <span class="footer-tag">Cafes</span>
                            <span class="footer-tag">Street Food</span>
                            <span class="footer-tag">Desserts</span>
                        </div>
                    </div>

                    <!-- Platform & Partners -->
                    <div class="footer-col">
                        <h4 class="footer-heading">Platform</h4>
                        <ul class="footer-links">
                            <li><a href="#owner">Restaurant Owners Portal</a></li>
                            <li><a href="#explore">Interactive Map Discovery</a></li>
                            <li><a href="#onboarding">9D Flavor Vectors</a></li>
                            <li><a href="#home">Privacy & Security</a></li>
                        </ul>
                    </div>
                </div>

                <div class="footer-bottom">
                    <p class="copyright-text">
                        © ${new Date().getFullYear()} FoodBook Platform. Built for Food-Tech Innovation.
                    </p>
                    <div class="footer-bottom-links">
                        <span>Powered by AI/ML Recommender & Modern Food Discovery Engine</span>
                    </div>
                </div>
            </div>
        </footer>
        `;
    }
}
