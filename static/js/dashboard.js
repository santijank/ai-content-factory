// Dashboard JavaScript
class Dashboard {
    constructor() {
        this.init();
        this.loadDashboardData();
        this.setupEventListeners();
        this.startAutoRefresh();
    }

    init() {
        console.log('Dashboard initialized');
        this.showToast('Welcome to AI Content Factory!', 'success');
    }

    setupEventListeners() {
        // Refresh data every 30 seconds
        setInterval(() => {
            this.loadDashboardData();
        }, 30000);

        // Handle window resize
        window.addEventListener('resize', () => {
            this.handleResize();
        });
    }

    async loadDashboardData() {
        try {
            await Promise.all([
                this.loadStats(),
                this.loadTrends(),
                this.loadOpportunities(),
                this.loadRecentContent()
            ]);
        } catch (error) {
            console.error('Error loading dashboard data:', error);
            this.showToast('Error loading dashboard data', 'error');
        }
    }

    async loadStats() {
        try {
            const response = await fetch('/api/stats');
            const stats = await response.json();
            
            document.getElementById('trends-count').textContent = stats.trends_today || 0;
            document.getElementById('opportunities-count').textContent = stats.opportunities_count || 0;
            document.getElementById('content-count').textContent = stats.content_today || 0;
            document.getElementById('cost-today').textContent = `฿${stats.cost_today || 0}`;
        } catch (error) {
            console.error('Error loading stats:', error);
        }
    }

    async loadTrends() {
        try {
            const response = await fetch('/api/trends?limit=10');
            const trends = await response.json();
            
            const container = document.getElementById('trends-list');
            container.innerHTML = '';
            
            if (trends.length === 0) {
                container.innerHTML = '<p class="text-muted text-center">No trends available. Click "Collect Trends" to get started.</p>';
                return;
            }
            
            trends.forEach(trend => {
                const trendElement = this.createTrendElement(trend);
                container.appendChild(trendElement);
            });
        } catch (error) {
            console.error('Error loading trends:', error);
        }
    }

    createTrendElement(trend) {
        const div = document.createElement('div');
        div.className = 'trend-item fade-in';
        div.onclick = () => this.showTrendDetails(trend);
        
        const scoreClass = this.getScoreClass(trend.popularity_score);
        
        div.innerHTML = `
            <div class="trend-title">${trend.topic}</div>
            <div class="trend-meta">
                <span class="trend-score ${scoreClass}">Score: ${trend.popularity_score}/10</span>
                <span class="ms-2">
                    <i class="fas fa-chart-line"></i> ${trend.growth_rate}% growth
                </span>
                <span class="ms-2">
                    <i class="fas fa-tag"></i> ${trend.category}
                </span>
            </div>
        `;
        
        return div;
    }

    getScoreClass(score) {
        if (score >= 7) return 'score-high';
        if (score >= 4) return 'score-medium';
        return 'score-low';
    }

    async loadOpportunities() {
        try {
            const response = await fetch('/api/opportunities?limit=5');
            const opportunities = await response.json();
            
            const container = document.getElementById('opportunities-list');
            container.innerHTML = '';
            
            if (opportunities.length === 0) {
                container.innerHTML = '<p class="text-muted text-center">No opportunities available. Analyze trends to generate opportunities.</p>';
                return;
            }
            
            opportunities.forEach(opportunity => {
                const opportunityElement = this.createOpportunityElement(opportunity);
                container.appendChild(opportunityElement);
            });
        } catch (error) {
            console.error('Error loading opportunities:', error);
        }
    }

    createOpportunityElement(opportunity) {
        const div = document.createElement('div');
        div.className = 'opportunity-item fade-in';
        div.onclick = () => this.selectOpportunity(opportunity);
        
        div.innerHTML = `
            <div class="opportunity-title">${opportunity.suggested_angle}</div>
            <div class="opportunity-description">${opportunity.description || 'No description available'}</div>
            <div class="opportunity-metrics">
                <div class="metric">
                    <span class="metric-label">ROI:</span>
                    <span class="metric-value">${opportunity.estimated_roi}x</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Competition:</span>
                    <span class="metric-value">${opportunity.competition_level}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Views:</span>
                    <span class="metric-value">${this.formatNumber(opportunity.estimated_views)}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Cost:</span>
                    <span class="metric-value">฿${opportunity.production_cost}</span>
                </div>
            </div>
        `;
        
        return div;
    }

    async loadRecentContent() {
        try {
            const response = await fetch('/api/content?limit=10');
            const content = await response.json();
            
            const tbody = document.getElementById('content-table-body');
            tbody.innerHTML = '';
            
            if (content.length === 0) {
                tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">No content created yet.</td></tr>';
                return;
            }
            
            content.forEach(item => {
                const row = this.createContentRow(item);
                tbody.appendChild(row);
            });
        } catch (error) {
            console.error('Error loading content:', error);
        }
    }

    createContentRow(item) {
        const tr = document.createElement('tr');
        tr.className = 'fade-in';
        
        const statusBadge = this.getStatusBadge(item.status);
        const platformIcon = this.getPlatformIcon(item.platform);
        const performance = this.formatPerformance(item.performance);
        
        tr.innerHTML = `
            <td>
                <div class="fw-semibold">${item.title}</div>
                <small class="text-muted">${item.description?.substring(0, 50) || ''}...</small>
            </td>
            <td>${statusBadge}</td>
            <td>${platformIcon}</td>
            <td>${this.formatDate(item.created_at)}</td>
            <td>${performance}</td>
            <td>
                <div class="btn-group btn-group-sm">
                    <button class="btn btn-outline-primary" onclick="dashboard.viewContent('${item.id}')">
                        <i class="fas fa-eye"></i>
                    </button>
                    <button class="btn btn-outline-secondary" onclick="dashboard.editContent('${item.id}')">
                        <i class="fas fa-edit"></i>
                    </button>
                </div>
            </td>
        `;
        
        return tr;
    }

    getStatusBadge(status) {
        const statusClasses = {
            'pending': 'status-pending',
            'processing': 'status-processing',
            'completed': 'status-completed',
            'failed': 'status-failed'
        };
        
        const className = statusClasses[status] || 'status-pending';
        return `<span class="status-badge ${className}">${status}</span>`;
    }

    getPlatformIcon(platform) {
        const icons = {
            'youtube': '<i class="fab fa-youtube text-danger"></i> YouTube',
            'tiktok': '<i class="fab fa-tiktok text-dark"></i> TikTok',
            'instagram': '<i class="fab fa-instagram text-primary"></i> Instagram',
            'facebook': '<i class="fab fa-facebook text-primary"></i> Facebook'
        };
        
        return icons[platform] || '<i class="fas fa-globe"></i> Unknown';
    }

    formatPerformance(performance) {
        if (!performance) return '<span class="text-muted">-</span>';
        
        const views = this.formatNumber(performance.views || 0);
        const likes = this.formatNumber(performance.likes || 0);
        
        return `
            <div>
                <small><i class="fas fa-eye"></i> ${views}</small><br>
                <small><i class="fas fa-heart"></i> ${likes}</small>
            </div>
        `;
    }

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
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);

        if (diffMins < 60) {
            return `${diffMins}m ago`;
        } else if (diffHours < 24) {
            return `${diffHours}h ago`;
        } else if (diffDays < 7) {
            return `${diffDays}d ago`;
        } else {
            return date.toLocaleDateString();
        }
    }

    // Action functions
    async collectTrends() {
        this.showLoading('Collecting Trends', 'Gathering trending topics from multiple sources...');
        
        try {
            const response = await fetch('/api/collect-trends', {
                method: 'POST'
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showToast(`Collected ${result.count} new trends!`, 'success');
                await this.loadTrends();
                await this.loadStats();
            } else {
                throw new Error(result.error);
            }
        } catch (error) {
            console.error('Error collecting trends:', error);
            this.showToast('Failed to collect trends', 'error');
        } finally {
            this.hideLoading();
        }
    }

    async analyzeOpportunities() {
        this.showLoading('Analyzing Opportunities', 'AI is analyzing trends and generating content opportunities...');
        
        try {
            const response = await fetch('/api/analyze-opportunities', {
                method: 'POST'
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showToast(`Generated ${result.count} new opportunities!`, 'success');
                await this.loadOpportunities();
                await this.loadStats();
            } else {
                throw new Error(result.error);
            }
        } catch (error) {
            console.error('Error analyzing opportunities:', error);
            this.showToast('Failed to analyze opportunities', 'error');
        } finally {
            this.hideLoading();
        }
    }

    async generateContent() {
        // Check if there are selected opportunities
        const selectedOpportunities = await this.getSelectedOpportunities();
        
        if (selectedOpportunities.length === 0) {
            this.showToast('Please select at least one opportunity first', 'warning');
            window.location.href = '/opportunities';
            return;
        }

        this.showLoading('Generating Content', 'AI is creating content based on selected opportunities...');
        
        try {
            const response = await fetch('/api/generate-content', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    opportunity_ids: selectedOpportunities.map(o => o.id)
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showToast(`Generated ${result.count} content items!`, 'success');
                await this.loadRecentContent();
                await this.loadStats();
            } else {
                throw new Error(result.error);
            }
        } catch (error) {
            console.error('Error generating content:', error);
            this.showToast('Failed to generate content', 'error');
        } finally {
            this.hideLoading();
        }
    }

    async uploadContent() {
        const readyContent = await this.getReadyContent();
        
        if (readyContent.length === 0) {
            this.showToast('No content ready for upload', 'warning');
            window.location.href = '/content';
            return;
        }

        this.showLoading('Uploading Content', 'Uploading content to selected platforms...');
        
        try {
            const response = await fetch('/api/upload-content', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    content_ids: readyContent.map(c => c.id)
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showToast(`Uploaded ${result.count} content items!`, 'success');
                await this.loadRecentContent();
                await this.loadStats();
            } else {
                throw new Error(result.error);
            }
        } catch (error) {
            console.error('Error uploading content:', error);
            this.showToast('Failed to upload content', 'error');
        } finally {
            this.hideLoading();
        }
    }

    async getSelectedOpportunities() {
        try {
            const response = await fetch('/api/opportunities?status=selected');
            return await response.json();
        } catch (error) {
            console.error('Error getting selected opportunities:', error);
            return [];
        }
    }

    async getReadyContent() {
        try {
            const response = await fetch('/api/content?status=ready');
            return await response.json();
        } catch (error) {
            console.error('Error getting ready content:', error);
            return [];
        }
    }

    // Filter functions
    filterTrends(category) {
        const trends = document.querySelectorAll('.trend-item');
        
        trends.forEach(trend => {
            if (category === 'all') {
                trend.style.display = 'block';
            } else {
                const trendCategory = trend.querySelector('.trend-meta').textContent;
                trend.style.display = trendCategory.includes(category) ? 'block' : 'none';
            }
        });
    }

    // Detail functions
    showTrendDetails(trend) {
        const modal = new bootstrap.Modal(document.getElementById('trendModal') || this.createTrendModal());
        
        // Populate modal with trend details
        document.getElementById('trendModalTitle').textContent = trend.topic;
        document.getElementById('trendModalBody').innerHTML = `
            <div class="row">
                <div class="col-md-6">
                    <h6>Popularity Score</h6>
                    <div class="progress mb-3">
                        <div class="progress-bar" style="width: ${trend.popularity_score * 10}%">${trend.popularity_score}/10</div>
                    </div>
                </div>
                <div class="col-md-6">
                    <h6>Growth Rate</h6>
                    <p class="h4 text-success">${trend.growth_rate}%</p>
                </div>
            </div>
            <div class="row">
                <div class="col-md-6">
                    <h6>Category</h6>
                    <p>${trend.category}</p>
                </div>
                <div class="col-md-6">
                    <h6>Source</h6>
                    <p>${trend.source}</p>
                </div>
            </div>
            <div class="row">
                <div class="col-12">
                    <h6>Keywords</h6>
                    <p>${Array.isArray(trend.keywords) ? trend.keywords.join(', ') : 'N/A'}</p>
                </div>
            </div>
        `;
        
        modal.show();
    }

    selectOpportunity(opportunity) {
        window.location.href = `/opportunities/${opportunity.id}`;
    }

    viewContent(contentId) {
        window.location.href = `/content/${contentId}`;
    }

    editContent(contentId) {
        window.location.href = `/content/${contentId}/edit`;
    }

    // UI Helper functions
    showLoading(title, message) {
        document.getElementById('loading-message').textContent = title;
        document.getElementById('loading-detail').textContent = message;
        
        const modal = new bootstrap.Modal(document.getElementById('loadingModal'));
        modal.show();
    }

    hideLoading() {
        const modal = bootstrap.Modal.getInstance(document.getElementById('loadingModal'));
        if (modal) {
            modal.hide();
        }
    }

    showToast(message, type = 'info') {
        const toast = document.getElementById('liveToast');
        const toastTitle = document.getElementById('toast-title');
        const toastMessage = document.getElementById('toast-message');
        
        const icons = {
            'success': 'fas fa-check-circle text-success',
            'error': 'fas fa-exclamation-circle text-danger',
            'warning': 'fas fa-exclamation-triangle text-warning',
            'info': 'fas fa-info-circle text-info'
        };
        
        toastTitle.innerHTML = `<i class="${icons[type] || icons.info}"></i> ${type.charAt(0).toUpperCase() + type.slice(1)}`;
        toastMessage.textContent = message;
        
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
    }

    createTrendModal() {
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.id = 'trendModal';
        modal.innerHTML = `
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="trendModalTitle">Trend Details</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body" id="trendModalBody">
                        <!-- Content will be populated here -->
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                        <button type="button" class="btn btn-primary" onclick="dashboard.analyzeOpportunities()">Analyze Opportunities</button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        return modal;
    }

    handleResize() {
        // Handle responsive layout changes
        console.log('Window resized');
    }

    startAutoRefresh() {
        // Start auto-refresh for real-time updates
        console.log('Auto-refresh started');
    }
}

// Global functions
function collectTrends() {
    dashboard.collectTrends();
}

function analyzeOpportunities() {
    dashboard.analyzeOpportunities();
}

function generateContent() {
    dashboard.generateContent();
}

function uploadContent() {
    dashboard.uploadContent();
}

function filterTrends(category) {
    dashboard.filterTrends(category);
}

// Initialize dashboard when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    window.dashboard = new Dashboard();
});