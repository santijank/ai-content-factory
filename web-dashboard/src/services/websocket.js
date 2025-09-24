/**
 * WebSocket Service
 * Real-time communication service สำหรับ AI Content Factory web dashboard
 */

class WebSocketService {
    constructor() {
        this.ws = null;
        this.wsUrl = process.env.REACT_APP_WS_URL || 'ws://localhost:5000/ws';
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectInterval = 1000; // Start with 1 second
        this.maxReconnectInterval = 30000; // Max 30 seconds
        this.reconnectDecay = 1.5; // Exponential backoff multiplier
        
        // Event listeners
        this.eventListeners = new Map();
        
        // Connection state
        this.isConnected = false;
        this.isConnecting = false;
        this.shouldReconnect = true;
        
        // Message queue for offline messages
        this.messageQueue = [];
        this.maxQueueSize = 100;
        
        // Heartbeat
        this.heartbeatInterval = null;
        this.heartbeatTimeout = null;
        this.heartbeatIntervalTime = 30000; // 30 seconds
        this.heartbeatTimeoutTime = 5000; // 5 seconds
        
        // Statistics
        this.stats = {
            connectTime: null,
            messagesSent: 0,
            messagesReceived: 0,
            reconnectCount: 0,
            lastError: null
        };
        
        console.log('WebSocket Service initialized');
    }
    
    /**
     * Connect to WebSocket server
     */
    connect() {
        if (this.isConnected || this.isConnecting) {
            console.log('WebSocket already connected or connecting');
            return;
        }
        
        this.isConnecting = true;
        console.log(`Connecting to WebSocket: ${this.wsUrl}`);
        
        try {
            this.ws = new WebSocket(this.wsUrl);
            this.setupEventHandlers();
        } catch (error) {
            console.error('Failed to create WebSocket connection:', error);
            this.isConnecting = false;
            this.handleConnectionError(error);
        }
    }
    
    /**
     * Setup WebSocket event handlers
     */
    setupEventHandlers() {
        if (!this.ws) return;
        
        this.ws.onopen = (event) => {
            console.log('WebSocket connected');
            this.isConnected = true;
            this.isConnecting = false;
            this.reconnectAttempts = 0;
            this.reconnectInterval = 1000;
            this.stats.connectTime = new Date();
            
            // Send authentication if token exists
            this.authenticate();
            
            // Process queued messages
            this.processMessageQueue();
            
            // Start heartbeat
            this.startHeartbeat();
            
            // Emit connect event
            this.emit('connect', { timestamp: new Date() });
        };
        
        this.ws.onmessage = (event) => {
            try {
                const message = JSON.parse(event.data);
                this.stats.messagesReceived++;
                this.handleMessage(message);
            } catch (error) {
                console.error('Error parsing WebSocket message:', error);
                console.log('Raw message:', event.data);
            }
        };
        
        this.ws.onclose = (event) => {
            console.log('WebSocket connection closed', event.code, event.reason);
            this.isConnected = false;
            this.isConnecting = false;
            
            // Stop heartbeat
            this.stopHeartbeat();
            
            // Emit disconnect event
            this.emit('disconnect', { 
                code: event.code, 
                reason: event.reason,
                timestamp: new Date()
            });
            
            // Attempt reconnection if needed
            if (this.shouldReconnect && !event.wasClean) {
                this.scheduleReconnect();
            }
        };
        
        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.stats.lastError = error;
            this.emit('error', { error, timestamp: new Date() });
            this.handleConnectionError(error);
        };
    }
    
    /**
     * Authenticate with server
     */
    authenticate() {
        const token = localStorage.getItem('auth_token');
        if (token) {
            this.send('auth', { token });
        }
    }
    
    /**
     * Handle incoming messages
     */
    handleMessage(message) {
        const { type, data, id } = message;
        
        console.log('Received WebSocket message:', type, data);
        
        // Handle system messages
        switch (type) {
            case 'pong':
                this.handlePong();
                break;
                
            case 'auth_success':
                console.log('WebSocket authentication successful');
                this.emit('authenticated', data);
                break;
                
            case 'auth_failed':
                console.error('WebSocket authentication failed:', data);
                this.emit('auth_failed', data);
                break;
                
            case 'error':
                console.error('Server error:', data);
                this.emit('server_error', data);
                break;
                
            default:
                // Emit custom event
                this.emit(type, data, id);
                break;
        }
    }
    
    /**
     * Send message to server
     */
    send(type, data = {}, id = null) {
        const message = {
            type,
            data,
            id: id || this.generateId(),
            timestamp: new Date().toISOString()
        };
        
        if (this.isConnected && this.ws.readyState === WebSocket.OPEN) {
            try {
                this.ws.send(JSON.stringify(message));
                this.stats.messagesSent++;
                console.log('Sent WebSocket message:', type, data);
            } catch (error) {
                console.error('Error sending WebSocket message:', error);
                this.queueMessage(message);
            }
        } else {
            console.log('WebSocket not connected, queueing message:', type);
            this.queueMessage(message);
        }
        
        return message.id;
    }
    
    /**
     * Queue message for later sending
     */
    queueMessage(message) {
        if (this.messageQueue.length >= this.maxQueueSize) {
            console.warn('Message queue full, removing oldest message');
            this.messageQueue.shift();
        }
        
        this.messageQueue.push(message);
    }
    
    /**
     * Process queued messages
     */
    processMessageQueue() {
        console.log(`Processing ${this.messageQueue.length} queued messages`);
        
        while (this.messageQueue.length > 0 && this.isConnected) {
            const message = this.messageQueue.shift();
            try {
                this.ws.send(JSON.stringify(message));
                this.stats.messagesSent++;
            } catch (error) {
                console.error('Error sending queued message:', error);
                // Re-queue the message
                this.messageQueue.unshift(message);
                break;
            }
        }
    }
    
    /**
     * Start heartbeat to keep connection alive
     */
    startHeartbeat() {
        this.stopHeartbeat(); // Clear any existing heartbeat
        
        this.heartbeatInterval = setInterval(() => {
            if (this.isConnected && this.ws.readyState === WebSocket.OPEN) {
                this.send('ping', { timestamp: Date.now() });
                
                // Set timeout for pong response
                this.heartbeatTimeout = setTimeout(() => {
                    console.warn('Heartbeat timeout, closing connection');
                    this.ws.close();
                }, this.heartbeatTimeoutTime);
            }
        }, this.heartbeatIntervalTime);
    }
    
    /**
     * Stop heartbeat
     */
    stopHeartbeat() {
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
            this.heartbeatInterval = null;
        }
        
        if (this.heartbeatTimeout) {
            clearTimeout(this.heartbeatTimeout);
            this.heartbeatTimeout = null;
        }
    }
    
    /**
     * Handle pong response
     */
    handlePong() {
        if (this.heartbeatTimeout) {
            clearTimeout(this.heartbeatTimeout);
            this.heartbeatTimeout = null;
        }
    }
    
    /**
     * Handle connection errors
     */
    handleConnectionError(error) {
        this.isConnected = false;
        this.isConnecting = false;
        this.stats.lastError = error;
    }
    
    /**
     * Schedule reconnection attempt
     */
    scheduleReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error('Max reconnection attempts reached');
            this.emit('max_reconnect_attempts', { attempts: this.reconnectAttempts });
            return;
        }
        
        this.reconnectAttempts++;
        this.stats.reconnectCount++;
        
        console.log(`Scheduling reconnection attempt ${this.reconnectAttempts} in ${this.reconnectInterval}ms`);
        
        setTimeout(() => {
            if (this.shouldReconnect && !this.isConnected && !this.isConnecting) {
                console.log(`Reconnection attempt ${this.reconnectAttempts}`);
                this.emit('reconnecting', { attempt: this.reconnectAttempts });
                this.connect();
            }
        }, this.reconnectInterval);
        
        // Exponential backoff
        this.reconnectInterval = Math.min(
            this.reconnectInterval * this.reconnectDecay,
            this.maxReconnectInterval
        );
    }
    
    /**
     * Disconnect from WebSocket
     */
    disconnect() {
        console.log('Manually disconnecting WebSocket');
        this.shouldReconnect = false;
        
        if (this.ws) {
            this.ws.close(1000, 'Manual disconnect');
        }
        
        this.stopHeartbeat();
    }
    
    /**
     * Add event listener
     */
    on(event, callback) {
        if (!this.eventListeners.has(event)) {
            this.eventListeners.set(event, []);
        }
        
        this.eventListeners.get(event).push(callback);
        
        // Return unsubscribe function
        return () => {
            this.off(event, callback);
        };
    }
    
    /**
     * Remove event listener
     */
    off(event, callback) {
        const listeners = this.eventListeners.get(event);
        if (listeners) {
            const index = listeners.indexOf(callback);
            if (index !== -1) {
                listeners.splice(index, 1);
            }
        }
    }
    
    /**
     * Emit event to listeners
     */
    emit(event, ...args) {
        const listeners = this.eventListeners.get(event);
        if (listeners) {
            listeners.forEach(callback => {
                try {
                    callback(...args);
                } catch (error) {
                    console.error(`Error in event listener for ${event}:`, error);
                }
            });
        }
    }
    
    /**
     * Generate unique message ID
     */
    generateId() {
        return Date.now().toString(36) + Math.random().toString(36).substr(2);
    }
    
    /**
     * Get connection status
     */
    getStatus() {
        return {
            isConnected: this.isConnected,
            isConnecting: this.isConnecting,
            shouldReconnect: this.shouldReconnect,
            reconnectAttempts: this.reconnectAttempts,
            queuedMessages: this.messageQueue.length,
            stats: { ...this.stats }
        };
    }
    
    /**
     * Clear message queue
     */
    clearQueue() {
        this.messageQueue = [];
    }
    
    /**
     * Reset reconnection attempts
     */
    resetReconnection() {
        this.reconnectAttempts = 0;
        this.reconnectInterval = 1000;
        this.shouldReconnect = true;
    }
}

// =============================================================================
// SPECIFIC EVENT HANDLERS FOR AI CONTENT FACTORY
// =============================================================================

class AIContentFactoryWebSocket extends WebSocketService {
    constructor() {
        super();
        
        // Setup specific event handlers
        this.setupFactoryEventHandlers();
    }
    
    setupFactoryEventHandlers() {
        // Trend collection events
        this.on('trend_collection_started', (data) => {
            console.log('Trend collection started:', data);
        });
        
        this.on('trend_collection_completed', (data) => {
            console.log('Trend collection completed:', data);
        });
        
        this.on('new_trends_available', (data) => {
            console.log('New trends available:', data);
        });
        
        // Content generation events
        this.on('content_generation_started', (data) => {
            console.log('Content generation started:', data);
        });
        
        this.on('content_generation_progress', (data) => {
            console.log('Content generation progress:', data);
        });
        
        this.on('content_generation_completed', (data) => {
            console.log('Content generation completed:', data);
        });
        
        // Upload events
        this.on('upload_started', (data) => {
            console.log('Upload started:', data);
        });
        
        this.on('upload_progress', (data) => {
            console.log('Upload progress:', data);
        });
        
        this.on('upload_completed', (data) => {
            console.log('Upload completed:', data);
        });
        
        this.on('upload_failed', (data) => {
            console.error('Upload failed:', data);
        });
        
        // System events
        this.on('system_alert', (data) => {
            console.warn('System alert:', data);
        });
        
        this.on('quota_warning', (data) => {
            console.warn('Quota warning:', data);
        });
        
        this.on('service_status_change', (data) => {
            console.log('Service status change:', data);
        });
    }
    
    // =============================================================================
    // SPECIFIC METHODS FOR AI CONTENT FACTORY
    // =============================================================================
    
    /**
     * Subscribe to trend updates
     */
    subscribeTrends(categories = []) {
        this.send('subscribe_trends', { categories });
    }
    
    /**
     * Subscribe to content generation updates
     */
    subscribeContentGeneration(contentIds = []) {
        this.send('subscribe_content_generation', { content_ids: contentIds });
    }
    
    /**
     * Subscribe to upload progress
     */
    subscribeUploads(uploadIds = []) {
        this.send('subscribe_uploads', { upload_ids: uploadIds });
    }
    
    /**
     * Subscribe to system notifications
     */
    subscribeSystemNotifications() {
        this.send('subscribe_system_notifications', {});
    }
    
    /**
     * Request real-time analytics
     */
    requestRealtimeAnalytics(metrics = ['views', 'engagement']) {
        this.send('request_realtime_analytics', { metrics });
    }
    
    /**
     * Send user activity
     */
    sendUserActivity(activity) {
        this.send('user_activity', activity);
    }
    
    /**
     * Request system status
     */
    requestSystemStatus() {
        this.send('request_system_status', {});
    }
}

// Create singleton instance
const websocketService = new AIContentFactoryWebSocket();

// Auto-connect when service is imported
if (typeof window !== 'undefined') {
    // Only auto-connect in browser environment
    websocketService.connect();
    
    // Handle page visibility changes
    document.addEventListener('visibilitychange', () => {
        if (document.visibilityState === 'visible' && !websocketService.isConnected) {
            websocketService.resetReconnection();
            websocketService.connect();
        }
    });
    
    // Handle online/offline events
    window.addEventListener('online', () => {
        if (!websocketService.isConnected) {
            websocketService.resetReconnection();
            websocketService.connect();
        }
    });
    
    window.addEventListener('offline', () => {
        console.log('Browser went offline');
    });
}

// Export default instance
export default websocketService;

// Named exports for convenience
export {
    WebSocketService,
    AIContentFactoryWebSocket
};