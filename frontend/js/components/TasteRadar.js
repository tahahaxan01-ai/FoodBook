/**
 * FoodBook Taste Radar Chart Component
 * Visualizes 9-dimensional taste vectors using Chart.js
 */
import { CONFIG } from '../config.js';

export class TasteRadar {
    /**
     * @param {HTMLCanvasElement} canvas
     * @param {Object} options
     * @param {Array<number>} options.userVector
     * @param {Array<number>} options.restaurantVector
     * @param {string} options.restaurantName
     */
    static render(canvas, options = {}) {
        if (!canvas) return null;

        // Destroy existing chart if present
        if (canvas._chartInstance) {
            canvas._chartInstance.destroy();
        }

        const labels = CONFIG.TASTE_DIMENSIONS.map(d => `${d.emoji} ${d.name}`);
        const datasets = [];

        if (options.restaurantVector && options.restaurantVector.length === 9) {
            datasets.push({
                label: options.restaurantName || "Restaurant Taste Profile",
                data: options.restaurantVector.map(v => Math.round(v * 100)),
                backgroundColor: "rgba(255, 87, 34, 0.25)",
                borderColor: "#FF5722",
                borderWidth: 2.5,
                pointBackgroundColor: "#FF5722",
                pointBorderColor: "#FFFFFF",
                pointRadius: 4,
                pointHoverRadius: 6
            });
        }

        if (options.userVector && options.userVector.length === 9) {
            datasets.push({
                label: "Your Taste Profile",
                data: options.userVector.map(v => Math.round(v * 100)),
                backgroundColor: "rgba(59, 130, 246, 0.20)",
                borderColor: "#3B82F6",
                borderWidth: 2,
                pointBackgroundColor: "#3B82F6",
                pointBorderColor: "#FFFFFF",
                pointRadius: 3.5,
                pointHoverRadius: 5
            });
        }

        // If no vectors provided, show neutral baseline
        if (datasets.length === 0) {
            datasets.push({
                label: "Baseline Taste",
                data: [50, 50, 50, 50, 50, 50, 50, 50, 50],
                backgroundColor: "rgba(156, 163, 175, 0.2)",
                borderColor: "#9CA3AF",
                borderWidth: 1.5
            });
        }

        const ctx = canvas.getContext('2d');
        const chart = new Chart(ctx, {
            type: 'radar',
            data: {
                labels,
                datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    r: {
                        angleLines: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.08)'
                        },
                        pointLabels: {
                            font: {
                                size: 12,
                                family: "'Plus Jakarta Sans', sans-serif",
                                weight: '600'
                            },
                            color: '#E2E8F0'
                        },
                        ticks: {
                            display: false,
                            stepSize: 20,
                            min: 0,
                            max: 100
                        },
                        suggestedMin: 0,
                        suggestedMax: 100
                    }
                },
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: '#CBD5E1',
                            font: {
                                family: "'Plus Jakarta Sans', sans-serif",
                                size: 12,
                                weight: '500'
                            },
                            padding: 16,
                            usePointStyle: true
                        }
                    },
                    tooltip: {
                        backgroundColor: '#1E293B',
                        titleColor: '#F8FAFC',
                        bodyColor: '#CBD5E1',
                        borderColor: '#334155',
                        borderWidth: 1,
                        padding: 10,
                        callbacks: {
                            label: function (context) {
                                return `${context.dataset.label}: ${context.raw}% intensity`;
                            }
                        }
                    }
                },
                animation: {
                    duration: 1000,
                    easing: 'easeOutQuart'
                }
            }
        });

        canvas._chartInstance = chart;
        return chart;
    }
}
