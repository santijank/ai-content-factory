/**
 * API Service
 * Central API service สำหรับ AI Content Factory web dashboard
 */

class APIService {
    constructor() {
        this.baseURL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';
        this.timeout = 30000; // 30 seconds
        this.retryAttempts = 3;
        this.retryDelay = 1000; // 1 second
        
        // Request interceptor for authentication
        this.defaultHeaders = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        };
        
        // Add auth token if available
        const token = localStorage.getItem('auth_token');
        if (token) {
            this.defaultHeaders['Authorization'] = `Bearer ${token}`;
        }
    }
    
    /**
     * Generic HTTP request method with retry logic
     */
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            method: 'GET',
            headers: { ...this.defaultHeaders },
            timeout: this.timeout,
            ...options
        };
        
        // Add auth token from storage if not already present
        const currentToken = localStorage.getItem('auth_token');
        if (currentToken && !config.headers['Authorization']) {
            config.headers['Authorization'] = `Bearer ${currentToken}`;
        }
        
        for (let attempt = 1; attempt <= this.retryAttempts; attempt++) {
            try {
                console.log(`API Request [${attempt}/${this.retryAttempts}]: ${config.method} ${url}`);
                
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), this.timeout);
                
                const response = await fetch(url, {
                    ...config,
                    signal: controller.signal
                });
                
                clearTimeout(timeoutId);
                
                // Handle different response types
                if (!response.ok) {
                    const errorData = await this.handleErrorResponse(response);
                    throw new Error(errorData.message || `HTTP ${response.status}: ${response.statusText}`);
                }
                
                // Parse response
                const contentType = response.headers.get('content-type');
                if (contentType && contentType.includes('application/json')) {
                    return await response.json();
                } else if (contentType && contentType.includes('text/')) {
                    return await response.text();
                } else {
                    return await response.blob();
                }
                
            } catch (error) {
                console.error(`API Request failed [${attempt}/${this.retryAttempts}]:`, error);
                
                // Don't retry for certain errors
                if (error.name === 'AbortError' || 
                    error.message.includes('401') || 
                    error.message.includes('403') ||
                    attempt === this.retryAttempts) {
                    throw error;
                }
                
                // Wait before retry
                await this.delay(this.retryDelay * attempt);
            }
        }
    }
    
    /**
     * Handle error responses
     */
    async handleErrorResponse(response) {
        try {
            const errorData = await response.json();
            return errorData;
        } catch {
            return {
                message: `HTTP ${response.status}: ${response.statusText}`,
                status: response.status
            };
        }
    }
    
    /**
     * Delay utility for retry logic
     */
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
    
    /**
     * Set authentication token
     */
    setAuthToken(token) {
        localStorage.setItem('auth_token', token);
        this.defaultHeaders['Authorization'] = `Bearer ${token}`;
    }
    
    /**
     * Clear authentication token
     */
    clearAuthToken() {
        localStorage.removeItem('auth_token');
        delete this.defaultHeaders['Authorization'];
    }
    
    // =============================================================================
    // TREND ANALYSIS ENDPOINTS
    // =============================================================================
    
    /**
     * Get current trending topics
     */
    async getTrends(params = {}) {
        const queryParams = new URLSearchParams({
            limit: 20,
            source: 'all',
            region: 'global',
            ...params
        });
        
        return this.request(`/trends?${queryParams}`);
    }
    
    /**
     * Analyze specific trend
     */
    async analyzeTrend(trendId) {
        return this.request(`/trends/${trendId}/analyze`, {
            method: 'POST'
        });
    }
    
    /**
     * Get trend history
     */
    async getTrendHistory(trendId, timeframe = '7d') {
        return this.request(`/trends/${trendId}/history?timeframe=${timeframe}`);
    }
    
    /**
     * Trigger trend collection manually
     */
    async collectTrends(sources = ['youtube', 'google']) {
        return this.request('/trends/collect', {
            method: 'POST',
            body: JSON.stringify({ sources })
        });
    }
    
    // =============================================================================
    // CONTENT OPPORTUNITIES ENDPOINTS
    // =============================================================================
    
    /**
     * Get content opportunities
     */
    async getOpportunities(params = {}) {
        const queryParams = new URLSearchParams({
            limit: 10,
            status: 'active',
            sort_by: 'priority_score',
            ...params
        });
        
        return this.request(`/opportunities?${queryParams}`);
    }
    
    /**
     * Generate opportunities from trends
     */
    async generateOpportunities(trendIds) {
        return this.request('/opportunities/generate', {
            method: 'POST',
            body: JSON.stringify({ trend_ids: trendIds })
        });
    }
    
    /**
     * Get opportunity details
     */
    async getOpportunityDetails(opportunityId) {
        return this.request(`/opportunities/${opportunityId}`);
    }
    
    /**
     * Update opportunity status
     */
    async updateOpportunityStatus(opportunityId, status) {
        return this.request(`/opportunities/${opportunityId}/status`, {
            method: 'PATCH',
            body: JSON.stringify({ status })
        });
    }
    
    /**
     * Rate opportunity (user feedback)
     */
    async rateOpportunity(opportunityId, rating, feedback = '') {
        return this.request(`/opportunities/${opportunityId}/rate`, {
            method: 'POST',
            body: JSON.stringify({ rating, feedback })
        });
    }
    
    // =============================================================================
    // CONTENT GENERATION ENDPOINTS
    // =============================================================================
    
    /**
     * Generate content from opportunity
     */
    async generateContent(opportunityId, options = {}) {
        return this.request('/content/generate', {
            method: 'POST',
            body: JSON.stringify({
                opportunity_id: opportunityId,
                quality_tier: 'balanced',
                platforms: ['youtube', 'tiktok'],
                ...options
            })
        });
    }
    
    /**
     * Get content items
     */
    async getContentItems(params = {}) {
        const queryParams = new URLSearchParams({
            limit: 20,
            status: 'all',
            sort_by: 'created_at',
            ...params
        });
        
        return this.request(`/content?${queryParams}`);
    }
    
    /**
     * Get content item details
     */
    async getContentDetails(contentId) {
        return this.request(`/content/${contentId}`);
    }
    
    /**
     * Update content item
     */
    async updateContent(contentId, updates) {
        return this.request(`/content/${contentId}`, {
            method: 'PATCH',
            body: JSON.stringify(updates)
        });
    }
    
    /**
     * Delete content item
     */
    async deleteContent(contentId) {
        return this.request(`/content/${contentId}`, {
            method: 'DELETE'
        });
    }
    
    /**
     * Generate content variations
     */
    async generateContentVariations(contentId, variationType = 'platform') {
        return this.request(`/content/${contentId}/variations`, {
            method: 'POST',
            body: JSON.stringify({ variation_type: variationType })
        });
    }
    
    // =============================================================================
    // PLATFORM MANAGEMENT ENDPOINTS
    // =============================================================================
    
    /**
     * Get connected platforms
     */
    async getConnectedPlatforms() {
        return this.request('/platforms');
    }
    
    /**
     * Connect platform account
     */
    async connectPlatform(platform, credentials) {
        return this.request('/platforms/connect', {
            method: 'POST',
            body: JSON.stringify({
                platform,
                credentials
            })
        });
    }
    
    /**
     * Disconnect platform
     */
    async disconnectPlatform(platform) {
        return this.request(`/platforms/${platform}/disconnect`, {
            method: 'DELETE'
        });
    }
    
    /**
     * Upload content to platforms
     */
    async uploadToPlatforms(contentId, platforms, scheduleTime = null) {
        return this.request('/platforms/upload', {
            method: 'POST',
            body: JSON.stringify({
                content_id: contentId,
                platforms,
                schedule_time: scheduleTime
            })
        });
    }
    
    /**
     * Get upload status
     */
    async getUploadStatus(uploadId) {
        return this.request(`/uploads/${uploadId}/status`);
    }
    
    /**
     * Get platform analytics
     */
    async getPlatformAnalytics(platform, timeframe = '7d') {
        return this.request(`/platforms/${platform}/analytics?timeframe=${timeframe}`);
    }
    
    // =============================================================================
    // PERFORMANCE & ANALYTICS ENDPOINTS
    // =============================================================================
    
    /**
     * Get dashboard analytics
     */
    async getDashboardAnalytics(timeframe = '7d') {
        return this.request(`/analytics/dashboard?timeframe=${timeframe}`);
    }
    
    /**
     * Get content performance
     */
    async getContentPerformance(contentId) {
        return this.request(`/analytics/content/${contentId}`);
    }
    
    /**
     * Get trend performance
     */
    async getTrendPerformance(trendId) {
        return this.request(`/analytics/trends/${trendId}`);
    }
    
    /**
     * Get platform comparison
     */
    async getPlatformComparison(timeframe = '30d') {
        return this.request(`/analytics/platforms/compare?timeframe=${timeframe}`);
    }
    
    /**
     * Get ROI analysis
     */
    async getROIAnalysis(timeframe = '30d') {
        return this.request(`/analytics/roi?timeframe=${timeframe}`);
    }
    
    // =============================================================================
    // USER & SETTINGS ENDPOINTS
    // =============================================================================
    
    /**
     * Get user profile
     */
    async getUserProfile() {
        return this.request('/user/profile');
    }
    
    /**
     * Update user profile
     */
    async updateUserProfile(updates) {
        return this.request('/user/profile', {
            method: 'PATCH',
            body: JSON.stringify(updates)
        });
    }
    
    /**
     * Get user settings
     */
    async getUserSettings() {
        return this.request('/user/settings');
    }
    
    /**
     * Update user settings
     */
    async updateUserSettings(settings) {
        return this.request('/user/settings', {
            method: 'PATCH',
            body: JSON.stringify(settings)
        });
    }
    
    /**
     * Get API usage statistics
     */
    async getAPIUsage() {
        return this.request('/user/api-usage');
    }
    
    // =============================================================================
    // SYSTEM & HEALTH ENDPOINTS
    // =============================================================================
    
    /**
     * Get system health
     */
    async getSystemHealth() {
        return this.request('/system/health');
    }
    
    /**
     * Get service status
     */
    async getServiceStatus() {
        return this.request('/system/services/status');
    }
    
    /**
     * Get error logs
     */
    async getErrorLogs(limit = 50) {
        return this.request(`/system/logs/errors?limit=${limit}`);
    }
    
    // =============================================================================
    // FILE UPLOAD UTILITIES
    // =============================================================================
    
    /**
     * Upload file with progress tracking
     */
    async uploadFile(file, onProgress = null) {
        const formData = new FormData();
        formData.append('file', file);
        
        return new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest();
            
            // Track upload progress
            if (onProgress) {
                xhr.upload.addEventListener('progress', (e) => {
                    if (e.lengthComputable) {
                        const percentComplete = (e.loaded / e.total) * 100;
                        onProgress(percentComplete);
                    }
                });
            }
            
            xhr.addEventListener('load', () => {
                if (xhr.status >= 200 && xhr.status < 300) {
                    resolve(JSON.parse(xhr.responseText));
                } else {
                    reject(new Error(`Upload failed: ${xhr.statusText}`));
                }
            });
            
            xhr.addEventListener('error', () => {
                reject(new Error('Upload failed'));
            });
            
            xhr.open('POST', `${this.baseURL}/upload`);
            
            // Add auth header if available
            const token = localStorage.getItem('auth_token');
            if (token) {
                xhr.setRequestHeader('Authorization', `Bearer ${token}`);
            }
            
            xhr.send(formData);
        });
    }
    
    // =============================================================================
    // BATCH OPERATIONS
    // =============================================================================
    
    /**
     * Batch process opportunities
     */
    async batchProcessOpportunities(opportunityIds, action) {
        return this.request('/opportunities/batch', {
            method: 'POST',
            body: JSON.stringify({
                opportunity_ids: opportunityIds,
                action
            })
        });
    }
    
    /**
     * Batch upload content
     */
    async batchUploadContent(contentIds, platforms) {
        return this.request('/content/batch-upload', {
            method: 'POST',
            body: JSON.stringify({
                content_ids: contentIds,
                platforms
            })
        });
    }
    
    // =============================================================================
    // REAL-TIME NOTIFICATIONS
    // =============================================================================
    
    /**
     * Get recent notifications
     */
    async getNotifications(limit = 20) {
        return this.request(`/notifications?limit=${limit}`);
    }
    
    /**
     * Mark notification as read
     */
    async markNotificationRead(notificationId) {
        return this.request(`/notifications/${notificationId}/read`, {
            method: 'PATCH'
        });
    }
    
    /**
     * Mark all notifications as read
     */
    async markAllNotificationsRead() {
        return this.request('/notifications/mark-all-read', {
            method: 'PATCH'
        });
    }
}

// Create singleton instance
const apiService = new APIService();

// Export individual methods for easier importing
export const {
    // Core methods
    request,
    setAuthToken,
    clearAuthToken,
    
    // Trends
    getTrends,
    analyzeTrend,
    getTrendHistory,
    collectTrends,
    
    // Opportunities
    getOpportunities,
    generateOpportunities,
    getOpportunityDetails,
    updateOpportunityStatus,
    rateOpportunity,
    
    // Content
    generateContent,
    getContentItems,
    getContentDetails,
    updateContent,
    deleteContent,
    generateContentVariations,
    
    // Platforms
    getConnectedPlatforms,
    connectPlatform,
    disconnectPlatform,
    uploadToPlatforms,
    getUploadStatus,
    getPlatformAnalytics,
    
    // Analytics
    getDashboardAnalytics,
    getContentPerformance,
    getTrendPerformance,
    getPlatformComparison,
    getROIAnalysis,
    
    // User
    getUserProfile,
    updateUserProfile,
    getUserSettings,
    updateUserSettings,
    getAPIUsage,
    
    // System
    getSystemHealth,
    getServiceStatus,
    getErrorLogs,
    
    // Utilities
    uploadFile,
    batchProcessOpportunities,
    batchUploadContent,
    getNotifications,
    markNotificationRead,
    markAllNotificationsRead
} = apiService;

// Export default instance
export default apiService;