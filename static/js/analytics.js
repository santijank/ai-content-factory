// Analytics JavaScript
class Analytics {
    constructor() {
        this.currentTimeRange = '7d';
        this.charts = {};
        this.init();
    }

    init() {
        this.loadAnalyticsData();
        this.initializeCharts();
        this.setupEventListeners();
        console.log('Analytics dashboard initialized');
    }

    setupEventListeners() {
        // Auto-refresh every 5 minutes
        setInterval(() => {
            this.loadAnalyticsData();
        }, 300000);
    }

    async loadAnalyticsData() {
        try {
            await Promise.all([
                this.loadKPIs(),
                this.loadPerformanceData(),
                this.loadPlatformData(),
                this.loadContentPerformance(),
                this.loadCategoryData(),
                this.loadHourlyData(),
                this.loadAIMetrics(),
                this.loadRecommendations()
            ]);
        } catch (error) {
            console.error('Error loading analytics data:', error);
        }
    }

    async loadKPIs() {
        try {
            const response = await fetch(`/api/analytics/kpis?timeRange=${this.currentTimeRange}`);
            const kpis = await response.json();

            document.getElementById('total-views').textContent = this.formatNumber(kpis.total_views || 0);
            document.getElementById('total-engagement').textContent = this.formatNumber(kpis.total_engagement || 0);
            document.getElementById('average-roi').textContent = (kpis.average_roi || 0).toFixed(1) + 'x';
            document.getElementById('total-spent').textContent = '฿' + this.formatNumber(kpis.total_spent || 0);

            // Update growth indicators
            this.updateGrowthIndicator('views-growth', kpis.views_growth || 0);
            this.updateGrowthIndicator('engagement-growth', kpis.engagement_growth || 0);
            this.updateGrowthIndicator('roi-growth', kpis.roi_growth || 0);
            this.updateGrowthIndicator('spent-growth', kpis.spent_growth || 0);

        } catch (error) {
            console.error('Error loading KPIs:', error);
        }
    }

    updateGrowthIndicator(elementId, growthPercentage) {
        const element = document.getElementById(elementId);
        const isPositive = growthPercentage >= 0;
        
        element.className = `text-xs ${isPositive ? 'text-success' : 'text-danger'}`;
        element.innerHTML = `
            <i class="fas fa-arrow-${isPositive ? 'up' : 'down'}"></i> 
            ${isPositive ? '+' : ''}${growthPercentage.toFixed(1)}% from last period
        `;
    }

    async loadPerformanceData() {
        try {
            const response = await fetch(`/api/analytics/performance?timeRange=${this.currentTimeRange}`);
            const data = await response.json();

            this.updatePerformanceChart(data);
        } catch (error) {
            console.error('Error loading performance data:', error);
        }
    }

    async loadPlatformData() {
        try {
            const response = await fetch(`/api/analytics/platforms?timeRange=${this.currentTimeRange}`);
            const data = await response.json();

            this.updatePlatformChart(data);
            this.updatePlatformStats(data);
        } catch (error) {
            console.error('Error loading platform data:', error);
        }
    }

    async loadContentPerformance() {
        try {
            const response = await fetch(`/api/analytics/content-performance?timeRange=${this.currentTimeRange}&limit=20`);
            const content = await response.json();

            this.updateContentPerformanceTable(content);
        } catch (error) {
            console.error('Error loading content performance:', error);
        }
    }

    async loadCategoryData() {
        try {
            const response = await fetch(`/api/analytics/categories?timeRange=${this.currentTimeRange}`);
            const data = await response.json();

            this.updateCategoryChart(data);
        } catch (error) {
            console.error('Error loading category data:', error);
        }
    }

    async loadHourlyData() {
        try {
            const response = await fetch(`/api/analytics/hourly?timeRange=${this.currentTimeRange}`);
            const data = await response.json();

            this.updateHourlyChart(data);
        } catch (error) {
            console.error('Error loading hourly data:', error);
        }
    }

    async loadAIMetrics() {
        try {
            const response = await fetch(`/api/analytics/ai-metrics?timeRange=${this.currentTimeRange}`);
            const metrics = await response.json();

            this.updateAIMetricsCircles(metrics);
        } catch (error) {
            console.error('Error loading AI metrics:', error);
        }
    }

    async loadRecommendations() {
        try {
            const response = await fetch(`/api/analytics/recommendations?timeRange=${this.currentTimeRange}`);
            const recommendations = await response.json();

            this.updateRecommendations(recommendations);
        } catch (error) {
            console.error('Error loading recommendations:', error);
        }
    }

    initializeCharts() {
        this.initPerformanceChart();
        this.initPlatformChart();
        this.initCategoryChart();
        this.initHourlyChart();
        this.initAIMetricsCircles();
    }

    initPerformanceChart() {
        const ctx = document.getElementById('performanceChart').getContext('2d');
        
        this.charts.performance = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'Views',
                        data: [],
                        borderColor: '#007bff',
                        backgroundColor: 'rgba(0, 123, 255, 0.1)',
                        tension: 0.1,
                        yAxisID: 'y'
                    },
                    {
                        label: 'Engagement',
                        data: [],
                        borderColor: '#28a745',
                        backgroundColor: 'rgba(40, 167, 69, 0.1)',
                        tension: 0.1,
                        yAxisID: 'y1'
                    }
                ]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'top',
                    }
                },
                scales: {
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: {
                            display: true,
                            text: 'Views'
                        }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        title: {
                            display: true,
                            text: 'Engagement'
                        },
                        grid: {
                            drawOnChartArea: false,
                        },
                    }
                }
            }
        });
    }

    initPlatformChart() {
        const ctx = document.getElementById('platformChart').getContext('2d');
        
        this.charts.platform = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: [],
                datasets: [{
                    data: [],
                    backgroundColor: [
                        '#FF6384',
                        '#36A2EB',
                        '#FFCE56',
                        '#4BC0C0',
                        '#9966FF'
                    ],
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }

    initCategoryChart() {
        const ctx = document.getElementById('categoryChart').getContext('2d');
        
        this.charts.category = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: [],
                datasets: [{
                    label: 'Average Views',
                    data: [],
                    backgroundColor: 'rgba(54, 162, 235, 0.6)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Average Views'
                        }
                    }
                }
            }
        });
    }

    initHourlyChart() {
        const ctx = document.getElementById('hourlyChart').getContext('2d');
        
        this.charts.hourly = new Chart(ctx, {
            type: 'line',
            data: {
                labels: Array.from({length: 24}, (_, i) => `${i}:00`),
                datasets: [{
                    label: 'Success Rate (%)',
                    data: [],
                    borderColor: '#17a2b8',
                    backgroundColor: 'rgba(23, 162, 184, 0.1)',
                    tension: 0.3,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        title: {
                            display: true,
                            text: 'Success Rate (%)'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Hour of Day'
                        }
                    }
                }
            }
        });
    }

    initAIMetricsCircles() {
        const canvases = ['prediction-accuracy', 'trend-success', 'content-quality', 'automation-efficiency'];
        
        canvases.forEach(canvasId => {
            const ctx = document.getElementById(canvasId).getContext('2d');
            
            this.charts[canvasId] = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    datasets: [{
                        data: [0, 100],
                        backgroundColor: ['#28a745', '#e9ecef'],
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: false,
                    maintainAspectRatio: false,
                    cutout: '70%',
                    plugins: {
                        legend: {
                            display: false
                        },
                        tooltip: {
                            enabled: false
                        }
                    }
                }
            });
        });
    }

    updatePerformanceChart(data) {
        if (!this.charts.performance || !data.timeline) return;

        this.charts.performance.data.labels = data.timeline.map(item => 
            new Date(item.date).toLocaleDateString('th-TH', { month: 'short', day: 'numeric' })
        );
        this.charts.performance.data.datasets[0].data = data.timeline.map(item => item.views);
        this.charts.performance.data.datasets[1].data = data.timeline.map(item => item.engagement);
        
        this.charts.performance.update();
    }

    updatePlatformChart(data) {
        if (!this.charts.platform || !data.platforms) return;

        this.charts.platform.data.labels = data.platforms.map(p => p.name);
        this.charts.platform.data.datasets[0].data = data.platforms.map(p => p.views);
        
        this.charts.platform.update();
    }

    updatePlatformStats(data) {
        const container = document.getElementById('platform-stats');
        
        if (!data.platforms) {
            container.innerHTML = '<p class="text-muted">No platform data available</p>';
            return;
        }

        const statsHtml = data.platforms.map(platform => `
            <div class="d-flex justify-content-between align-items-center mb-2">
                <span><i class="fab fa-${platform.name.toLowerCase()}"></i> ${platform.name}</span>
                <div>
                    <span class="badge bg-primary">${this.formatNumber(platform.views)} views</span>
                    <span class="badge bg-success">${platform.engagement_rate}% eng</span>
                </div>
            </div>
        `).join('');

        container.innerHTML = statsHtml;
    }

    updateContentPerformanceTable(content) {
        const tbody = document.getElementById('performance-table-body');
        
        if (!content || content.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted">No performance data available</td></tr>';
            return;
        }

        const rows = content.map(item => `
            <tr>
                <td>
                    <div class="fw-semibold">${item.title}</div>
                    <small class="text-muted">${item.category}</small>
                </td>
                <td>
                    <i class="fab fa-${item.platform.toLowerCase()}"></i>
                    ${item.platform}
                </td>
                <td>${this.formatNumber(item.views)}</td>
                <td>
                    ${this.formatNumber(item.likes + item.comments + item.shares)}
                    <br><small class="text-muted">${item.engagement_rate}%</small>
                </td>
                <td>
                    <span class="badge ${item.roi >= 2 ? 'bg-success' : item.roi >= 1 ? 'bg-warning' : 'bg-danger'}">
                        ${item.roi.toFixed(1)}x
                    </span>
                </td>
                <td>฿${item.cost}</td>
                <td>฿${item.revenue.toFixed(2)}</td>
                <td>${this.formatDate(item.published_at)}</td>
            </tr>
        `).join('');

        tbody.innerHTML = rows;
    }

    updateCategoryChart(data) {
        if (!this.charts.category || !data.categories) return;

        this.charts.category.data.labels = data.categories.map(c => c.name);
        this.charts.category.data.datasets[0].data = data.categories.map(c => c.avg_views);
        
        this.charts.category.update();
    }

    updateHourlyChart(data) {
        if (!this.charts.hourly || !data.hourly_success) return;

        this.charts.hourly.data.datasets[0].data = data.hourly_success;
        this.charts.hourly.update();
    }

    updateAIMetricsCircles(metrics) {
        const metricsData = {
            'prediction-accuracy': metrics.prediction_accuracy || 85,
            'trend-success': metrics.trend_success_rate || 72,
            'content-quality': metrics.content_quality_score || 68,
            'automation-efficiency': metrics.automation_efficiency || 91
        };

        Object.entries(metricsData).forEach(([canvasId, percentage]) => {
            if (this.charts[canvasId]) {
                this.charts[canvasId].data.datasets[0].data = [percentage, 100 - percentage];
                this.charts[canvasId].update();

                // Add percentage text overlay
                const canvas = document.getElementById(canvasId);
                const container = canvas.parentElement;
                
                let textOverlay = container.querySelector('.percentage-text');
                if (!textOverlay) {
                    textOverlay = document.createElement('div');
                    textOverlay.className = 'percentage-text position-absolute';
                    textOverlay.style.cssText = `
                        top: 50%; left: 50%; 
                        transform: translate(-50%, -50%);
                        font-weight: bold; font-size: 18px;
                        color: #495057; pointer-events: none;
                    `;
                    container.style.position = 'relative';
                    container.appendChild(textOverlay);
                }
                
                textOverlay.textContent = `${percentage}%`;
            }
        });
    }

    updateRecommendations(recommendations) {
        const container = document.getElementById('recommendations-list');
        
        if (!recommendations || recommendations.length === 0) {
            container.innerHTML = '<p class="text-muted">No recommendations available at this time.</p>';
            return;
        }

        const recommendationsHtml = recommendations.map((rec, index) => `
            <div class="alert alert-${this.getRecommendationAlertType(rec.priority)} alert-dismissible fade show" role="alert">
                <div class="d-flex align-items-start">
                    <div class="flex-shrink-0 me-3">
                        <i class="fas ${this.getRecommendationIcon(rec.type)} fa-lg"></i>
                    </div>
                    <div class="flex-grow-1">
                        <h6 class="alert-heading">${rec.title}</h6>
                        <p class="mb-2">${rec.description}</p>
                        <div class="d-flex justify-content-between align-items-center">
                            <small class="text-muted">
                                <i class="fas fa-chart-line me-1"></i>
                                Expected Impact: ${rec.expected_impact}
                            </small>
                            <div>
                                <button type="button" class="btn btn-sm btn-outline-primary" onclick="analytics.applyRecommendation(${index})">
                                    Apply
                                </button>
                                <button type="button" class="btn btn-sm btn-outline-secondary ms-1" onclick="analytics.dismissRecommendation(${index})">
                                    Dismiss
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `).join('');

        container.innerHTML = recommendationsHtml;
    }

    getRecommendationAlertType(priority) {
        switch (priority) {
            case 'high': return 'danger';
            case 'medium': return 'warning';
            case 'low': return 'info';
            default: return 'info';
        }
    }

    getRecommendationIcon(type) {
        switch (type) {
            case 'trend': return 'fa-trending-up';
            case 'optimization': return 'fa-cog';
            case 'timing': return 'fa-clock';
            case 'content': return 'fa-edit';
            case 'platform': return 'fa-share-alt';
            default: return 'fa-lightbulb';
        }
    }

    // Utility functions
    formatNumber(num) {
        if (num >= 1000000) {
            return (num / 1000000).toFixed(1) + 'M';
        }
        if (num >= 1000) {
            return (num / 1000).toFixed(1) + 'K';
        }
        return num.toString();
    }

    formatDate(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diffMs = now - date;
        const diffDays = Math.floor(diffMs / 86400000);

        if (diffDays === 0) {
            return 'Today';
        } else if (diffDays === 1) {
            return 'Yesterday';
        } else if (diffDays < 7) {
            return `${diffDays}d ago`;
        } else {
            return date.toLocaleDateString('th-TH');
        }
    }

    // Action functions
    async applyRecommendation(index) {
        try {
            const response = await fetch('/api/recommendations/apply', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ recommendation_index: index })
            });

            const result = await response.json();
            
            if (result.success) {
                this.showToast('Recommendation applied successfully!', 'success');
                await this.loadRecommendations();
            } else {
                throw new Error(result.error);
            }
        } catch (error) {
            console.error('Error applying recommendation:', error);
            this.showToast('Failed to apply recommendation', 'error');
        }
    }

    async dismissRecommendation(index) {
        try {
            const response = await fetch('/api/recommendations/dismiss', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ recommendation_index: index })
            });

            const result = await response.json();
            
            if (result.success) {
                await this.loadRecommendations();
            } else {
                throw new Error(result.error);
            }
        } catch (error) {
            console.error('Error dismissing recommendation:', error);
        }
    }

    showToast(message, type = 'info') {
        // Create toast if it doesn't exist
        let toastContainer = document.querySelector('.toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
            document.body.appendChild(toastContainer);
        }

        const toast = document.createElement('div');
        toast.className = 'toast';
        toast.innerHTML = `
            <div class="toast-header">
                <strong class="me-auto">
                    <i class="fas ${type === 'success' ? 'fa-check-circle text-success' : 'fa-info-circle text-info'}"></i>
                    ${type.charAt(0).toUpperCase() + type.slice(1)}
                </strong>
                <button type="button" class="btn-close" data-bs-dismiss="toast"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        `;

        toastContainer.appendChild(toast);
        
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
        
        // Remove toast element after it's hidden
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    }
}

// Global functions for HTML onclick events
function setTimeRange(range) {
    // Update button states
    document.querySelectorAll('.btn-group .btn').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');
    
    // Update analytics
    analytics.currentTimeRange = range;
    analytics.loadAnalyticsData();
}

function sortContent(sortBy) {
    // Update dropdown text
    const dropdown = document.querySelector('.dropdown-toggle');
    dropdown.innerHTML = `<i class="fas fa-sort"></i> Sort by ${sortBy.charAt(0).toUpperCase() + sortBy.slice(1)}`;
    
    // Reload content with sort parameter
    analytics.loadContentPerformance(sortBy);
}

// Initialize analytics when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    window.analytics = new Analytics();
});