from flask import Flask, jsonify, request
from flask_cors import CORS
import asyncio
import logging
from datetime import datetime, timedelta
import os
from services.trend_collector import TrendCollector
from models.trend_data import TrendData
import sys
sys.path.append('../database')
from repositories.trend_repository import TrendRepository

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Initialize services
trend_collector = TrendCollector()
trend_repo = TrendRepository()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "trend-monitor",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    })

@app.route('/collect-trends', methods=['POST'])
def collect_trends():
    """Manual trigger for trend collection"""
    try:
        logger.info("Starting manual trend collection...")
        
        # Run async trend collection
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            trends_data = loop.run_until_complete(trend_collector.collect_all_trends())
            
            # Save to database
            saved_count = 0
            for trend_data in trends_data:
                try:
                    trend_repo.save_trend(trend_data)
                    saved_count += 1
                except Exception as e:
                    logger.error(f"Error saving trend {trend_data.topic}: {e}")
            
            logger.info(f"Collected and saved {saved_count} trends")
            
            return jsonify({
                "status": "success",
                "message": f"Successfully collected {len(trends_data)} trends",
                "saved_count": saved_count,
                "timestamp": datetime.utcnow().isoformat(),
                "trends_preview": [
                    {
                        "topic": trend.topic,
                        "source": trend.source,
                        "popularity_score": trend.popularity_score
                    } for trend in trends_data[:5]  # Show first 5
                ]
            })
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error in trend collection: {e}")
        return jsonify({
            "status": "error",
            "message": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }), 500

@app.route('/trends', methods=['GET'])
def get_trends():
    """Get recent trends with optional filtering"""
    try:
        # Get query parameters
        source = request.args.get('source')  # youtube, google, twitter, reddit
        limit = int(request.args.get('limit', 50))
        hours = int(request.args.get('hours', 24))  # Last N hours
        min_score = float(request.args.get('min_score', 0))
        
        # Calculate time filter
        since = datetime.utcnow() - timedelta(hours=hours)
        
        # Get trends from database
        trends = trend_repo.get_trends(
            source=source,
            since=since,
            limit=limit,
            min_popularity_score=min_score
        )
        
        # Format response
        trends_data = []
        for trend in trends:
            trends_data.append({
                "id": str(trend.id),
                "topic": trend.topic,
                "source": trend.source,
                "keywords": trend.keywords,
                "popularity_score": trend.popularity_score,
                "growth_rate": trend.growth_rate,
                "category": trend.category,
                "region": trend.region,
                "collected_at": trend.collected_at.isoformat(),
                "raw_data": trend.raw_data
            })
        
        return jsonify({
            "status": "success",
            "count": len(trends_data),
            "filters": {
                "source": source,
                "hours": hours,
                "min_score": min_score,
                "limit": limit
            },
            "trends": trends_data
        })
        
    except Exception as e:
        logger.error(f"Error getting trends: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/trends/sources', methods=['GET'])
def get_trend_sources():
    """Get available trend sources and their status"""
    try:
        sources_status = trend_collector.get_sources_status()
        
        return jsonify({
            "status": "success",
            "sources": sources_status,
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting sources status: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/trends/stats', methods=['GET'])
def get_trend_stats():
    """Get trend collection statistics"""
    try:
        # Get stats for last 24 hours
        since = datetime.utcnow() - timedelta(hours=24)
        stats = trend_repo.get_collection_stats(since=since)
        
        return jsonify({
            "status": "success",
            "period": "last_24_hours",
            "stats": stats,
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting trend stats: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/trends/top', methods=['GET'])
def get_top_trends():
    """Get top trending topics across all sources"""
    try:
        limit = int(request.args.get('limit', 10))
        hours = int(request.args.get('hours', 6))  # Last 6 hours for fresh trends
        
        since = datetime.utcnow() - timedelta(hours=hours)
        
        # Get top trends by popularity score
        top_trends = trend_repo.get_top_trends(
            since=since,
            limit=limit
        )
        
        trends_data = []
        for trend in top_trends:
            trends_data.append({
                "topic": trend.topic,
                "sources": trend.sources,  # List of sources mentioning this trend
                "max_popularity_score": trend.max_popularity_score,
                "avg_popularity_score": trend.avg_popularity_score,
                "mention_count": trend.mention_count,
                "keywords": trend.keywords,
                "category": trend.category,
                "latest_collection": trend.latest_collection.isoformat()
            })
        
        return jsonify({
            "status": "success",
            "period_hours": hours,
            "count": len(trends_data),
            "top_trends": trends_data,
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting top trends: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/trends/auto-collect', methods=['POST'])
def toggle_auto_collection():
    """Toggle automatic trend collection"""
    try:
        action = request.json.get('action')  # 'start' or 'stop'
        interval_minutes = int(request.json.get('interval_minutes', 30))
        
        if action == 'start':
            # This would integrate with a scheduler like Celery or APScheduler
            # For now, we'll just return a success message
            message = f"Auto-collection started with {interval_minutes} minute intervals"
            logger.info(message)
        elif action == 'stop':
            message = "Auto-collection stopped"
            logger.info(message)
        else:
            return jsonify({
                "status": "error",
                "message": "Action must be 'start' or 'stop'"
            }), 400
        
        return jsonify({
            "status": "success",
            "message": message,
            "action": action,
            "interval_minutes": interval_minutes if action == 'start' else None,
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error toggling auto-collection: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

if __name__ == '__main__':
    # Environment setup
    port = int(os.environ.get('PORT', 5001))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    logger.info(f"Starting Trend Monitor Service on port {port}")
    logger.info(f"Debug mode: {debug}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)