from flask import Flask, jsonify, render_template, request
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any
import os
import sys

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../'))

from monitoring.dashboard.performance_dashboard import PerformanceDashboard
from monitoring.dashboard.metrics_collector import MetricsCollector, MetricLevel
from monitoring.dashboard.alert_manager import AlertManager
from database.models.base import get_db_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'monitoring-secret-key')

# Initialize monitoring components
db_config = get_db_config()

# Performance dashboard
performance_dashboard = PerformanceDashboard(db_config)

# Metrics collector
metrics_config = {
    'buffer_size': 10000,
    'collection_interval': 30,
    'content_engine_url': os.getenv('CONTENT_ENGINE_URL', 'http://localhost:5001'),
    'platform_manager_url': os.getenv('PLATFORM_MANAGER_URL', 'http://localhost:5002'),
    'trend_monitor_url': os.getenv('TREND_MONITOR_URL', 'http://localhost:5003')
}
metrics_collector = MetricsCollector(metrics_config)

# Alert manager
alert_config = {
    'evaluation_interval': 30,
    'notification_channels': {
        'email': {
            'from_email': os.getenv('ALERT_EMAIL_FROM', 'alerts@aicontentfactory.com'),
            'to_emails': [os.getenv('ALERT_EMAIL_TO', 'admin@aicontentfactory.com')],
            'smtp_server': os.getenv('SMTP_SERVER', 'localhost'),
            'smtp_port': int(os.getenv('SMTP_PORT', '587')),
            'username': os.getenv('SMTP_USERNAME'),
            'password': os.getenv('SMTP_PASSWORD'),
            'use_tls': True
        },
        'slack': {
            'webhook_url': os.getenv('SLACK_WEBHOOK_URL')
        },
        'webhook': {
            'url': os.getenv('ALERT_WEBHOOK_URL'),
            'headers': {'Content-Type': 'application/json'},
            'timeout': 10
        }
    }
}
alert_manager = AlertManager(alert_config)

# Start monitoring services
metrics_collector.start_collection()
alert_manager.start_monitoring()

@app.route('/')
def index():
    """Main monitoring dashboard"""
    return render_template('monitoring_dashboard.html')

@app.route('/api/metrics')
async def get_metrics():
    """Get comprehensive metrics"""
    try:
        time_range = request.args.get('time_range', 'today')
        metrics = await performance_dashboard.get_metrics(time_range)
        return jsonify(metrics)
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/metrics/summary')
def get_metrics_summary():
    """Get metrics summary from collector"""
    try:
        minutes = int(request.args.get('minutes', 5))
        summary = metrics_collector.get_metrics_summary(minutes)
        return jsonify(summary)
    except Exception as e:
        logger.error(f"Error getting metrics summary: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/system/overview')
def get_system_overview():
    """Get system overview"""
    try:
        overview = metrics_collector.get_system_overview()
        return jsonify(overview)
    except Exception as e:
        logger.error(f"Error getting system overview: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/alerts')
def get_alerts():
    """Get current alerts"""
    try:
        level = request.args.get('level', 'warning')
        if level == 'all':
            alerts = alert_manager.get_active_alerts()
        else:
            from monitoring.dashboard.alert_manager import AlertSeverity
            severity = AlertSeverity(level)
            alerts = alert_manager.get_active_alerts(severity)
        
        # Convert alerts to JSON-serializable format
        alerts_json = []
        for alert in alerts:
            alerts_json.append({
                'id': alert.id,
                'rule_name': alert.rule_name,
                'metric_name': alert.metric_name,
                'severity': alert.severity.value,
                'status': alert.status.value,
                'message': alert.message,
                'current_value': alert.current_value,
                'threshold': alert.threshold,
                'first_triggered': alert.first_triggered.isoformat(),
                'last_triggered': alert.last_triggered.isoformat(),
                'acknowledged_at': alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
                'acknowledged_by': alert.acknowledged_by
            })
        
        return jsonify(alerts_json)
    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/alerts/<alert_id>/acknowledge', methods=['POST'])
def acknowledge_alert(alert_id):
    """Acknowledge an alert"""
    try:
        data = request.get_json() or {}
        acknowledged_by = data.get('acknowledged_by', 'web_user')
        
        success = alert_manager.acknowledge_alert(alert_id, acknowledged_by)
        
        if success:
            return jsonify({'success': True, 'message': 'Alert acknowledged'})
        else:
            return jsonify({'error': 'Alert not found'}), 404
            
    except Exception as e:
        logger.error(f"Error acknowledging alert: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/alerts/history')
def get_alert_history():
    """Get alert history"""
    try:
        hours = int(request.args.get('hours', 24))
        severity = request.args.get('severity')
        
        if severity:
            from monitoring.dashboard.alert_manager import AlertSeverity
            severity_enum = AlertSeverity(severity)
            history = alert_manager.get_alert_history(hours, severity_enum)
        else:
            history = alert_manager.get_alert_history(hours)
        
        # Convert to JSON
        history_json = []
        for alert in history:
            history_json.append({
                'id': alert.id,
                'rule_name': alert.rule_name,
                'metric_name': alert.metric_name,
                'severity': alert.severity.value,
                'status': alert.status.value,
                'message': alert.message,
                'first_triggered': alert.first_triggered.isoformat(),
                'resolved_at': alert.resolved_at.isoformat() if alert.resolved_at else None,
                'duration_seconds': (alert.resolved_at - alert.first_triggered).total_seconds() if alert.resolved_at else None
            })
        
        return jsonify(history_json)
    except Exception as e:
        logger.error(f"Error getting alert history: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/alerts/statistics')
def get_alert_statistics():
    """Get alert statistics"""
    try:
        hours = int(request.args.get('hours', 24))
        stats = alert_manager.get_alert_statistics(hours)
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error getting alert statistics: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/trends/analysis')
async def get_trend_analysis():
    """Get detailed trend analysis"""
    try:
        days = int(request.args.get('days', 7))
        analysis = await performance_dashboard.get_trend_analysis(days)
        return jsonify(analysis)
    except Exception as e:
        logger.error(f"Error getting trend analysis: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/performance/roi')
async def get_roi_by_platform():
    """Get ROI by platform"""
    try:
        roi_data = await performance_dashboard.calculate_roi_by_platform()
        return jsonify(roi_data)
    except Exception as e:
        logger.error(f"Error getting ROI data: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/metrics/export')
def export_metrics():
    """Export metrics in various formats"""
    try:
        format_type = request.args.get('format', 'json')
        hours = int(request.args.get('hours', 1))
        
        since = datetime.now() - timedelta(hours=hours)
        exported_data = metrics_collector.export_metrics(format_type, since)
        
        if format_type == 'json':
            return jsonify(exported_data)
        elif format_type == 'prometheus':
            return exported_data, 200, {'Content-Type': 'text/plain'}
        else:
            return jsonify({'error': 'Unsupported format'}), 400
            
    except Exception as e:
        logger.error(f"Error exporting metrics: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/metrics/prometheus')
def prometheus_metrics():
    """Prometheus metrics endpoint"""
    try:
        metrics_data = metrics_collector.export_metrics('prometheus')
        return metrics_data, 200, {'Content-Type': 'text/plain; charset=utf-8'}
    except Exception as e:
        logger.error(f"Error generating Prometheus metrics: {e}")
        return f"# Error generating metrics: {e}", 500, {'Content-Type': 'text/plain'}

@app.route('/health')
def health_check():
    """Health check endpoint"""
    try:
        health_info = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'services': {
                'metrics_collector': metrics_collector.is_running,
                'alert_manager': alert_manager.is_running,
                'performance_dashboard': True
            },
            'version': '1.0.0'
        }
        return jsonify(health_info)
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/config/alerts')
def get_alert_config():
    """Get alert configuration"""
    try:
        config = alert_manager.export_config()
        # Remove sensitive information
        if 'notification_channels' in config:
            for channel_name, channel in config['notification_channels'].items():
                if 'config' in channel and 'password' in channel['config']:
                    channel['config']['password'] = '***'
                if 'config' in channel and 'webhook_url' in channel['config']:
                    channel['config']['webhook_url'] = '***'
        
        return jsonify(config)
    except Exception as e:
        logger.error(f"Error getting alert config: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/config/alerts', methods=['POST'])
def update_alert_config():
    """Update alert configuration"""
    try:
        config_data = request.get_json()
        alert_manager.import_config(config_data)
        return jsonify({'success': True, 'message': 'Configuration updated'})
    except Exception as e:
        logger.error(f"Error updating alert config: {e}")
        return jsonify({'error': str(e)}), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

# WebSocket support for real-time updates
try:
    from flask_socketio import SocketIO, emit
    
    socketio = SocketIO(app, cors_allowed_origins="*")
    
    @socketio.on('connect')
    def on_connect():
        print('Client connected')
        emit('status', {'message': 'Connected to monitoring service'})
    
    @socketio.on('disconnect')
    def on_disconnect():
        print('Client disconnected')
    
    @socketio.on('subscribe_metrics')
    def on_subscribe_metrics():
        """Subscribe to real-time metrics updates"""
        # This would typically start a background task to send updates
        emit('metrics_subscribed', {'message': 'Subscribed to metrics updates'})
    
    # Background task to send real-time updates
    def background_thread():
        import time
        while True:
            time.sleep(30)  # Send updates every 30 seconds
            try:
                overview = metrics_collector.get_system_overview()
                socketio.emit('system_update', overview)
                
                alerts = alert_manager.get_active_alerts()
                if alerts:
                    alert_data = [
                        {
                            'id': alert.id,
                            'severity': alert.severity.value,
                            'message': alert.message,
                            'timestamp': alert.last_triggered.isoformat()
                        }
                        for alert in alerts[:5]  # Send only top 5 alerts
                    ]
                    socketio.emit('alerts_update', alert_data)
                    
            except Exception as e:
                logger.error(f"Error in background thread: {e}")
    
    # Start background thread for real-time updates
    import threading
    background_task = threading.Thread(target=background_thread, daemon=True)
    background_task.start()
    
except ImportError:
    logger.warning("Flask-SocketIO not available, real-time updates disabled")
    socketio = None

# Cleanup on shutdown
import atexit

def cleanup():
    """Cleanup function called on shutdown"""
    try:
        metrics_collector.stop_collection()
        alert_manager.stop_monitoring()
        logger.info("Monitoring services stopped")
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")

atexit.register(cleanup)

if __name__ == '__main__':
    port = int(os.getenv('MONITORING_PORT', 8080))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Starting monitoring service on port {port}")
    
    if socketio:
        socketio.run(app, host='0.0.0.0', port=port, debug=debug)
    else:
        app.run(host='0.0.0.0', port=port, debug=debug)