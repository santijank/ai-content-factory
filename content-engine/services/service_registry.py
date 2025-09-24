// web-dashboard/src/App.js
import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import Trends from './pages/Trends';
import Opportunities from './pages/Opportunities';
import Content from './pages/Content';
import Analytics from './pages/Analytics';
import Settings from './pages/Settings';
import { ApiService } from './services/api';
import { WebSocketService } from './services/websocket';
import './App.css';

function App() {
  const [systemHealth, setSystemHealth] = useState(null);
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    initializeApp();
    setupWebSocket();
    
    return () => {
      WebSocketService.disconnect();
    };
  }, []);

  const initializeApp = async () => {
    try {
      setLoading(true);
      
      // Get initial system health
      const health = await ApiService.getSystemHealth();
      setSystemHealth(health);
      
      // Get initial notifications
      const notifs = await ApiService.getNotifications();
      setNotifications(notifs);
      
    } catch (error) {
      console.error('Failed to initialize app:', error);
      addNotification('error', 'Failed to connect to server');
    } finally {
      setLoading(false);
    }
  };

  const setupWebSocket = () => {
    WebSocketService.connect('ws://localhost:8000/ws');
    
    WebSocketService.onMessage('health_update', (data) => {
      setSystemHealth(data);
    });
    
    WebSocketService.onMessage('notification', (data) => {
      addNotification(data.type, data.message);
    });
    
    WebSocketService.onMessage('trends_update', (data) => {
      addNotification('info', `New trends detected: ${data.count} opportunities`);
    });
    
    WebSocketService.onMessage('content_complete', (data) => {
      addNotification('success', `Content creation completed: ${data.title}`);
    });
  };

  const addNotification = (type, message) => {
    const notification = {
      id: Date.now(),
      type,
      message,
      timestamp: new Date()
    };
    
    setNotifications(prev => [notification, ...prev.slice(0, 9)]);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
      setNotifications(prev => prev.filter(n => n.id !== notification.id));
    }, 5000);
  };

  const getHealthStatusIcon = () => {
    if (!systemHealth) return '⚪';
    
    switch (systemHealth.overall_status) {
      case 'healthy': return '🟢';
      case 'degraded': return '🟡';
      case 'unhealthy': return '🔴';
      default: return '⚪';
    }
  };

  if (loading) {
    return (
      <div className="loading-screen">
        <div className="loading-spinner"></div>
        <h2>🚀 Loading AI Content Factory...</h2>
        <p>Initializing systems and checking connections...</p>
      </div>
    );
  }

  return (
    <Router>
      <div className="app">
        <header className="app-header">
          <div className="header-left">
            <h1>🤖 AI Content Factory</h1>
            <div className="system-health">
              <span className="health-icon">{getHealthStatusIcon()}</span>
              <span className="health-text">
                {systemHealth ? systemHealth.overall_status : 'Unknown'}
              </span>
            </div>
          </div>
          
          <nav className="main-nav">
            <Link to="/" className="nav-link">📊 Dashboard</Link>
            <Link to="/trends" className="nav-link">📈 Trends</Link>
            <Link to="/opportunities" className="nav-link">💡 Opportunities</Link>
            <Link to="/content" className="nav-link">🎬 Content</Link>
            <Link to="/analytics" className="nav-link">📊 Analytics</Link>
            <Link to="/settings" className="nav-link">⚙️ Settings</Link>
          </nav>
        </header>

        <main className="app-main">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/trends" element={<Trends />} />
            <Route path="/opportunities" element={<Opportunities />} />
            <Route path="/content" element={<Content />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </main>

        <NotificationPanel 
          notifications={notifications}
          onClose={(id) => setNotifications(prev => prev.filter(n => n.id !== id))}
        />
      </div>
    </Router>
  );
}

// Notification Panel Component
const NotificationPanel = ({ notifications, onClose }) => {
  if (notifications.length === 0) return null;

  return (
    <div className="notification-panel">
      {notifications.map(notification => (
        <div 
          key={notification.id} 
          className={`notification ${notification.type}`}
        >
          <div className="notification-content">
            <span className="notification-icon">
              {notification.type === 'success' && '✅'}
              {notification.type === 'error' && '❌'}
              {notification.type === 'warning' && '⚠️'}
              {notification.type === 'info' && 'ℹ️'}
            </span>
            <span className="notification-message">{notification.message}</span>
          </div>
          <button 
            className="notification-close"
            onClick={() => onClose(notification.id)}
          >
            ✕
          </button>
        </div>
      ))}
    </div>
  );
};

export default App;

// web-dashboard/src/services/api.js
export class ApiService {
  static baseURL = 'http://localhost:8000/api';

  static async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      },
      ...options
    };

    if (config.body && typeof config.body === 'object') {
      config.body = JSON.stringify(config.body);
    }

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        return await response.json();
      }
      
      return await response.text();
      
    } catch (error) {
      console.error(`API request failed: ${endpoint}`, error);
      throw error;
    }
  }

  // System APIs
  static async getSystemHealth() {
    return this.request('/system/health');
  }

  static async getNotifications() {
    return this.request('/notifications');
  }

  // Trends APIs
  static async getTrends(params = {}) {
    const query = new URLSearchParams(params).toString();
    return this.request(`/trends?${query}`);
  }

  static async collectTrends() {
    return this.request('/trends/collect', { method: 'POST' });
  }

  static async getTrendSources() {
    return this.request('/trends/sources');
  }

  // Opportunities APIs
  static async getOpportunities(params = {}) {
    const query = new URLSearchParams(params).toString();
    return this.request(`/opportunities?${query}`);
  }

  static async generateOpportunities() {
    return this.request('/opportunities/generate', { method: 'POST' });
  }

  static async selectOpportunity(opportunityId) {
    return this.request(`/opportunities/${opportunityId}/select`, { method: 'POST' });
  }

  // Content APIs
  static async getContentItems(params = {}) {
    const query = new URLSearchParams(params).toString();
    return this.request(`/content?${query}`);
  }

  static async createContent(opportunityId, config = {}) {
    return this.request('/content/create', {
      method: 'POST',
      body: { opportunity_id: opportunityId, ...config }
    });
  }

  static async getContentPlan(contentId) {
    return this.request(`/content/${contentId}/plan`);
  }

  static async uploadContent(contentId, platforms) {
    return this.request(`/content/${contentId}/upload`, {
      method: 'POST',
      body: { platforms }
    });
  }

  // Analytics APIs
  static async getAnalytics(params = {}) {
    const query = new URLSearchParams(params).toString();
    return this.request(`/analytics?${query}`);
  }

  static async getPerformanceMetrics() {
    return this.request('/analytics/performance');
  }

  static async getCostAnalysis(dateRange = '7d') {
    return this.request(`/analytics/costs?range=${dateRange}`);
  }

  // Platform APIs
  static async getPlatformStatus() {
    return this.request('/platforms/status');
  }

  static async updatePlatformConfig(platform, config) {
    return this.request(`/platforms/${platform}/config`, {
      method: 'PUT',
      body: config
    });
  }
}

// web-dashboard/src/services/websocket.js
export class WebSocketService {
  static ws = null;
  static listeners = new Map();
  static reconnectAttempts = 0;
  static maxReconnectAttempts = 5;

  static connect(url) {
    try {
      this.ws = new WebSocket(url);
      
      this.ws.onopen = () => {
        console.log('🔌 WebSocket connected');
        this.reconnectAttempts = 0;
      };
      
      this.ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          this.handleMessage(message);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };
      
      this.ws.onclose = () => {
        console.log('🔌 WebSocket disconnected');
        this.handleReconnect();
      };
      
      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
      
    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
    }
  }

  static handleMessage(message) {
    const { type, data } = message;
    
    if (this.listeners.has(type)) {
      const callbacks = this.listeners.get(type);
      callbacks.forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error(`Error in WebSocket message handler for ${type}:`, error);
        }
      });
    }
  }

  static handleReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = Math.pow(2, this.reconnectAttempts) * 1000; // Exponential backoff
      
      console.log(`🔄 Attempting to reconnect in ${delay/1000}s (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
      
      setTimeout(() => {
        this.connect(this.ws.url);
      }, delay);
    } else {
      console.error('❌ Max reconnection attempts reached');
    }
  }

  static onMessage(type, callback) {
    if (!this.listeners.has(type)) {
      this.listeners.set(type, []);
    }
    this.listeners.get(type).push(callback);
  }

  static send(type, data) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type, data }));
    } else {
      console.warn('WebSocket not connected, cannot send message');
    }
  }

  static disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.listeners.clear();
    this.reconnectAttempts = 0;
  }
}

// web-dashboard/public/index.html
export const indexHtml = `
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <link rel="icon" href="%PUBLIC_URL%/favicon.ico" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <meta name="theme-color" content="#000000" />
  <meta name="description" content="AI Content Factory - Automated content creation system" />
  <title>🤖 AI Content Factory</title>
  <style>
    /* Loading screen styles */
    .loading-screen {
      display: flex;
      flex-direction: column;
      justify-content: center;
      align-items: center;
      height: 100vh;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }
    
    .loading-spinner {
      width: 50px;
      height: 50px;
      border: 3px solid rgba(255,255,255,0.3);
      border-top: 3px solid white;
      border-radius: 50%;
      animation: spin 1s linear infinite;
      margin-bottom: 20px;
    }
    
    @keyframes spin {
      0% { transform: rotate(0deg); }
      100% { transform: rotate(360deg); }
    }
  </style>
</head>
<body>
  <noscript>You need to enable JavaScript to run this app.</noscript>
  <div id="root">
    <div class="loading-screen">
      <div class="loading-spinner"></div>
      <h2>🚀 Loading AI Content Factory...</h2>
      <p>Please wait while we initialize the system...</p>
    </div>
  </div>
</body>
</html>
`;

// web-dashboard/package.json
export const packageJson = {
  "name": "ai-content-factory-dashboard",
  "version": "1.0.0",
  "description": "React dashboard for AI Content Factory system",
  "private": true,
  "dependencies": {
    "@testing-library/jest-dom": "^5.16.4",
    "@testing-library/react": "^13.3.0",
    "@testing-library/user-event": "^13.5.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.8.0",
    "react-scripts": "5.0.1",
    "recharts": "^2.5.0",
    "date-fns": "^2.29.3",
    "lodash": "^4.17.21",
    "web-vitals": "^2.1.4"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject",
    "lint": "eslint src --ext .js,.jsx",
    "lint:fix": "eslint src --ext .js,.jsx --fix"
  },
  "eslintConfig": {
    "extends": [
      "react-app",
      "react-app/jest"
    ]
  },
  "browserslist": {
    "production": [
      ">0.2%",
      "not dead",
      "not op_mini all"
    ],
    "development": [
      "last 1 chrome version",
      "last 1 firefox version",
      "last 1 safari version"
    ]
  },
  "devDependencies": {
    "eslint": "^8.0.0"
  }
};

// web-dashboard/src/App.css
export const appCSS = `
/* Global Styles */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
  background-color: #f5f7fa;
  color: #2d3748;
  line-height: 1.6;
}

.app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

/* Header Styles */
.app-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 1rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.header-left h1 {
  font-size: 1.5rem;
  font-weight: 700;
}

.system-health {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.25rem 0.75rem;
  background: rgba(255,255,255,0.1);
  border-radius: 20px;
  font-size: 0.875rem;
}

.health-icon {
  font-size: 1rem;
}

.main-nav {
  display: flex;
  gap: 1rem;
}

.nav-link {
  color: white;
  text-decoration: none;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  transition: all 0.2s ease;
  font-weight: 500;
}

.nav-link:hover {
  background: rgba(255,255,255,0.15);
  transform: translateY(-1px);
}

.nav-link.active {
  background: rgba(255,255,255,0.2);
}

/* Main Content */
.app-main {
  flex: 1;
  padding: 2rem;
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
}

/* Loading Screen */
.loading-screen {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  text-align: center;
}

.loading-spinner {
  width: 50px;
  height: 50px;
  border: 3px solid rgba(255,255,255,0.3);
  border-top: 3px solid white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* Notification Panel */
.notification-panel {
  position: fixed;
  top: 80px;
  right: 1rem;
  z-index: 1000;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  max-width: 400px;
}

.notification {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  backdrop-filter: blur(10px);
  animation: slideIn 0.3s ease-out;
}

.notification.success {
  background: rgba(72, 187, 120, 0.9);
  color: white;
}

.notification.error {
  background: rgba(245, 101, 101, 0.9);
  color: white;
}

.notification.warning {
  background: rgba(237, 137, 54, 0.9);
  color: white;
}

.notification.info {
  background: rgba(66, 153, 225, 0.9);
  color: white;
}

.notification-content {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex: 1;
}

.notification-close {
  background: none;
  border: none;
  color: inherit;
  font-size: 1.2rem;
  cursor: pointer;
  padding: 0.25rem;
  border-radius: 4px;
  opacity: 0.7;
  transition: opacity 0.2s ease;
}

.notification-close:hover {
  opacity: 1;
  background: rgba(255,255,255,0.2);
}

@keyframes slideIn {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

/* Card Styles */
.card {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  border: 1px solid #e2e8f0;
  transition: all 0.2s ease;
}

.card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

.card h3 {
  margin-bottom: 1rem;
  color: #2d3748;
  font-size: 1.25rem;
  font-weight: 600;
}

/* Button Styles */
.btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 8px;
  font-weight: 500;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s ease;
  text-decoration: none;
}

.btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.btn-primary:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.btn-secondary {
  background: #edf2f7;
  color: #4a5568;
}

.btn-secondary:hover {
  background: #e2e8f0;
}

.btn-success {
  background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
  color: white;
}

.btn-success:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(72, 187, 120, 0.4);
}

.btn-danger {
  background: linear-gradient(135deg, #f56565 0%, #e53e3e 100%);
  color: white;
}

.btn-danger:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(245, 101, 101, 0.4);
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

/* Grid Layouts */
.grid {
  display: grid;
  gap: 1.5rem;
}

.grid-2 {
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
}

.grid-3 {
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
}

.grid-4 {
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
}

/* Status Indicators */
.status-indicator {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 500;
}

.status-healthy {
  background: #c6f6d5;
  color: #22543d;
}

.status-degraded {
  background: #faf089;
  color: #744210;
}

.status-error {
  background: #fed7d7;
  color: #742a2a;
}

/* Responsive Design */
@media (max-width: 768px) {
  .app-header {
    flex-direction: column;
    gap: 1rem;
    padding: 1rem;
  }
  
  .main-nav {
    flex-wrap: wrap;
    justify-content: center;
  }
  
  .app-main {
    padding: 1rem;
  }
  
  .notification-panel {
    right: 0.5rem;
    left: 0.5rem;
    max-width: none;
  }
  
  .grid-2,
  .grid-3,
  .grid-4 {
    grid-template-columns: 1fr;
  }
}

/* Utility Classes */
.text-center { text-align: center; }
.text-right { text-align: right; }
.text-sm { font-size: 0.875rem; }
.text-lg { font-size: 1.125rem; }
.text-xl { font-size: 1.25rem; }

.text-gray-600 { color: #718096; }
.text-gray-800 { color: #2d3748; }
.text-green-600 { color: #38a169; }
.text-red-600 { color: #e53e3e; }
.text-blue-600 { color: #3182ce; }

.mb-2 { margin-bottom: 0.5rem; }
.mb-4 { margin-bottom: 1rem; }
.mb-6 { margin-bottom: 1.5rem; }

.mt-2 { margin-top: 0.5rem; }
.mt-4 { margin-top: 1rem; }
.mt-6 { margin-top: 1.5rem; }

.flex { display: flex; }
.flex-col { flex-direction: column; }
.items-center { align-items: center; }
.justify-between { justify-content: space-between; }
.justify-center { justify-content: center; }

.gap-2 { gap: 0.5rem; }
.gap-4 { gap: 1rem; }

.p-2 { padding: 0.5rem; }
.p-4 { padding: 1rem; }
.px-4 { padding-left: 1rem; padding-right: 1rem; }
.py-2 { padding-top: 0.5rem; padding-bottom: 0.5rem; }

.rounded { border-radius: 0.375rem; }
.rounded-lg { border-radius: 0.5rem; }

.shadow { box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
.shadow-lg { box-shadow: 0 4px 12px rgba(0,0,0,0.15); }

.border { border: 1px solid #e2e8f0; }
.border-t { border-top: 1px solid #e2e8f0; }

.bg-white { background-color: white; }
.bg-gray-50 { background-color: #f7fafc; }
.bg-gray-100 { background-color: #edf2f7; }
`;

// web-dashboard/src/pages/Dashboard.js
export const dashboardPage = `
import React, { useState, useEffect } from 'react';
import { ApiService } from '../services/api';
import TrendCard from '../components/TrendCard';
import OpportunityCard from '../components/OpportunityCard';
import ContentCard from '../components/ContentCard';
import PerformanceChart from '../components/PerformanceChart';
import './Dashboard.css';

const Dashboard = () => {
  const [dashboardData, setDashboardData] = useState({
    trends: [],
    opportunities: [],
    recentContent: [],
    metrics: {},
    loading: true
  });

  useEffect(() => {
    loadDashboardData();
    
    // Refresh every 30 seconds
    const interval = setInterval(loadDashboardData, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadDashboardData = async () => {
    try {
      const [trends, opportunities, content, metrics] = await Promise.all([
        ApiService.getTrends({ limit: 5, sort: 'popularity_desc' }),
        ApiService.getOpportunities({ limit: 5, sort: 'score_desc' }),
        ApiService.getContentItems({ limit: 5, sort: 'created_desc' }),
        ApiService.getPerformanceMetrics()
      ]);

      setDashboardData({
        trends: trends.items || [],
        opportunities: opportunities.items || [],
        recentContent: content.items || [],
        metrics: metrics || {},
        loading: false
      });

    } catch (error) {
      console.error('Failed to load dashboard data:', error);
      setDashboardData(prev => ({ ...prev, loading: false }));
    }
  };

  const handleCollectTrends = async () => {
    try {
      await ApiService.collectTrends();
      loadDashboardData(); // Refresh data
    } catch (error) {
      console.error('Failed to collect trends:', error);
    }
  };

  const handleGenerateOpportunities = async () => {
    try {
      await ApiService.generateOpportunities();
      loadDashboardData(); // Refresh data
    } catch (error) {
      console.error('Failed to generate opportunities:', error);
    }
  };

  if (dashboardData.loading) {
    return (
      <div className="dashboard-loading">
        <div className="loading-spinner"></div>
        <p>Loading dashboard data...</p>
      </div>
    );
  }

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>📊 Dashboard</h1>
        <p className="text-gray-600">Welcome to AI Content Factory control center</p>
      </header>

      {/* Quick Actions */}
      <section className="quick-actions">
        <button 
          className="btn btn-primary"
          onClick={handleCollectTrends}
        >
          📈 Collect New Trends
        </button>
        <button 
          className="btn btn-secondary"
          onClick={handleGenerateOpportunities}
        >
          💡 Generate Opportunities
        </button>
        <button className="btn btn-success">
          🎬 Create Content
        </button>
      </section>

      {/* Metrics Overview */}
      <section className="metrics-overview grid grid-4">
        <div className="metric-card">
          <div className="metric-icon">📈</div>
          <div className="metric-content">
            <h3>{dashboardData.metrics.trends_collected || 0}</h3>
            <p>Trends Collected Today</p>
          </div>
        </div>
        
        <div className="metric-card">
          <div className="metric-icon">💡</div>
          <div className="metric-content">
            <h3>{dashboardData.metrics.opportunities_generated || 0}</h3>
            <p>Opportunities Generated</p>
          </div>
        </div>
        
        <div className="metric-card">
          <div className="metric-icon">🎬</div>
          <div className="metric-content">
            <h3>{dashboardData.metrics.content_created || 0}</h3>
            <p>Content Created</p>
          </div>
        </div>
        
        <div className="metric-card">
          <div className="metric-icon">💰</div>
          <div className="metric-content">
            <h3>\${dashboardData.metrics.total_cost || 0}</h3>
            <p>Total Cost Today</p>
          </div>
        </div>
      </section>

      {/* Main Content Grid */}
      <div className="dashboard-grid">
        {/* Latest Trends */}
        <section className="dashboard-section">
          <div className="section-header">
            <h2>📈 Latest Trends</h2>
            <a href="/trends" className="section-link">View All</a>
          </div>
          <div className="trends-list">
            {dashboardData.trends.length > 0 ? (
              dashboardData.trends.map(trend => (
                <TrendCard key={trend.id} trend={trend} compact />
              ))
            ) : (
              <div className="empty-state">
                <p>No trends collected yet</p>
                <button className="btn btn-primary" onClick={handleCollectTrends}>
                  Collect Trends Now
                </button>
              </div>
            )}
          </div>
        </section>

        {/* Top Opportunities */}
        <section className="dashboard-section">
          <div className="section-header">
            <h2>💡 Top Opportunities</h2>
            <a href="/opportunities" className="section-link">View All</a>
          </div>
          <div className="opportunities-list">
            {dashboardData.opportunities.length > 0 ? (
              dashboardData.opportunities.map(opportunity => (
                <OpportunityCard key={opportunity.id} opportunity={opportunity} compact />
              ))
            ) : (
              <div className="empty-state">
                <p>No opportunities available</p>
                <button className="btn btn-primary" onClick={handleGenerateOpportunities}>
                  Generate Opportunities
                </button>
              </div>
            )}
          </div>
        </section>

        {/* Recent Content */}
        <section className="dashboard-section">
          <div className="section-header">
            <h2>🎬 Recent Content</h2>
            <a href="/content" className="section-link">View All</a>
          </div>
          <div className="content-list">
            {dashboardData.recentContent.length > 0 ? (
              dashboardData.recentContent.map(content => (
                <ContentCard key={content.id} content={content} compact />
              ))
            ) : (
              <div className="empty-state">
                <p>No content created yet</p>
                <a href="/opportunities" className="btn btn-primary">
                  Create First Content
                </a>
              </div>
            )}
          </div>
        </section>

        {/* Performance Chart */}
        <section className="dashboard-section chart-section">
          <div className="section-header">
            <h2>📊 Performance Overview</h2>
            <a href="/analytics" className="section-link">View Details</a>
          </div>
          <PerformanceChart data={dashboardData.metrics.chart_data} />
        </section>
      </div>
    </div>
  );
};

export default Dashboard;
`;

console.log("✅ สร้างไฟล์หลักที่จำเป็นแล้ว 4 ไฟล์:");
console.log("1. main.py - Main Application Orchestrator");
console.log("2. shared/utils/logger.py - Advanced Logging System"); 
console.log("3. shared/models/service_status.py - Service Health Models");
console.log("4. shared/utils/cache.py - Advanced Caching System");
console.log("5. content-engine/services/service_registry.py - Complete Service Registry");
console.log("6. React Web Dashboard - Complete Application Structure");
console.log("\n🚀 ระบบพร้อมสำหรับการใช้งานแล้ว! ควรสร้างไฟล์ต่อไปนี้ในลำดับถัดไป:");
console.log("- Complete API endpoints (api/content_api.py, api/platform_api.py)");
console.log("- Missing database models (uploads.py, performance_metrics.py)");
console.log("- N8N workflows ที่เหลือ");
console.log("- Kubernetes deployment files");