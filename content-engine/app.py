"""
AI Content Factory - Content Engine Application
Main Flask application for content generation and management

This is the core service that handles:
- Content opportunity analysis
- AI-powered content generation
- Service tier management
- API endpoints for the system
"""

import asyncio
import logging
import traceback
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from werkzeug.exceptions import HTTPException

# Import our modules
from models import (
    QualityTier, 
    tier_manager,
    get_service_config,
    ContentOpportunity,
    TrendData,
    ContentAngle,
    ROIEstimate,
    OpportunityMetrics,
    rank_opportunities,
    filter_opportunities
)
from utils import (
    setup_logging,
    get_config,
    get_config_section,
    ConfigurationError,
    ServiceError,
    ValidationError,
    cache_get,
    cache_set
)
from services.ai_director import AIDirector
from services.trend_analyzer import TrendAnalyzer
from services.opportunity_engine import OpportunityEngine
from services.content_pipeline import ContentPipeline
from services.content_generator import ContentGenerator

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Global variables
ai_director = None
trend_analyzer = None
opportunity_engine = None
content_pipeline = None
content_generator = None
logger = None

def create_app(config_path: str = None) -> Flask:
    """
    Create and configure Flask application
    
    Args:
        config_path: Optional path to configuration file
        
    Returns:
        Configured Flask application
    """
    global ai_director, trend_analyzer, opportunity_engine, content_pipeline, content_generator, logger
    
    # Setup logging
    logger = setup_logging(
        level=get_config("logging.level", "INFO"),
        log_file=get_config("logging.file"),
        format_string=get_config("logging.format")
    )
    
    # Configure Flask app
    app.config['SECRET_KEY'] = get_config("app.secret_key", "dev-secret-key")
    app.config['DEBUG'] = get_config("app.debug", False)
    app.config['TESTING'] = False
    
    # Initialize services
    try:
        logger.info("Initializing AI Content Factory services...")
        
        # Initialize AI Director
        ai_director = AIDirector()
        logger.info("AI Director initialized")
        
        # Initialize Trend Analyzer
        trend_analyzer = TrendAnalyzer()
        logger.info("Trend Analyzer initialized")
        
        # Initialize Opportunity Engine
        opportunity_engine = OpportunityEngine(ai_director)
        logger.info("Opportunity Engine initialized")
        
        # Initialize Content Pipeline
        content_pipeline = ContentPipeline()
        logger.info("Content Pipeline initialized")
        
        # Initialize Content Generator
        content_generator = ContentGenerator(ai_director)
        logger.info("Content Generator initialized")
        
        logger.info("All services initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize services: {str(e)}")
        logger.error(traceback.format_exc())
        raise
    
    # Register error handlers
    register_error_handlers()
    
    # Register API routes
    register_api_routes()
    
    logger.info(f"AI Content Factory started on {get_config('app.host', 'localhost')}:{get_config('app.port', 5000)}")
    
    return app

def register_error_handlers():
    """Register error handlers for the application"""
    
    @app.errorhandler(ValidationError)
    def handle_validation_error(e):
        return jsonify({
            "error": "Validation Error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }), 400
    
    @app.errorhandler(ConfigurationError)
    def handle_config_error(e):
        return jsonify({
            "error": "Configuration Error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500
    
    @app.errorhandler(ServiceError)
    def handle_service_error(e):
        return jsonify({
            "error": "Service Error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }), 502
    
    @app.errorhandler(HTTPException)
    def handle_http_exception(e):
        return jsonify({
            "error": e.name,
            "message": e.description,
            "code": e.code,
            "timestamp": datetime.now().isoformat()
        }), e.code
    
    @app.errorhandler(Exception)
    def handle_general_exception(e):
        logger.error(f"Unhandled exception: {str(e)}")
        logger.error(traceback.format_exc())
        
        return jsonify({
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
            "timestamp": datetime.now().isoformat()
        }), 500

def register_api_routes():
    """Register all API routes"""
    
    # Health check endpoint
    @app.route('/health', methods=['GET'])
    def health_check():
        """Health check endpoint"""
        try:
            # Check service health
            services_status = {
                "ai_director": ai_director is not None,
                "trend_analyzer": trend_analyzer is not None,
                "opportunity_engine": opportunity_engine is not None,
                "content_pipeline": content_pipeline is not None,
                "content_generator": content_generator is not None
            }
            
            all_healthy = all(services_status.values())
            
            return jsonify({
                "status": "healthy" if all_healthy else "degraded",
                "timestamp": datetime.now().isoformat(),
                "services": services_status,
                "version": get_config("app.version", "1.0.0")
            }), 200 if all_healthy else 503
            
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return jsonify({
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }), 503
    
    # Configuration endpoints
    @app.route('/api/config/tiers', methods=['GET'])
    def get_tier_configuration():
        """Get available quality tiers and their configurations"""
        try:
            service_type = request.args.get('service_type', 'text_ai')
            
            tier_configs = {}
            for tier in QualityTier:
                config = get_service_config(service_type, tier)
                if config:
                    tier_configs[tier.value] = config.to_dict()
            
            return jsonify({
                "service_type": service_type,
                "tiers": tier_configs,
                "default_tier": get_config("services.default_tier", "budget")
            })
            
        except Exception as e:
            logger.error(f"Error getting tier configuration: {str(e)}")
            raise ServiceError(f"Failed to get tier configuration: {str(e)}")
    
    # Trend analysis endpoints
    @app.route('/api/trends/analyze', methods=['POST'])
    def analyze_trends():
        """Analyze trends and generate opportunities"""
        try:
            data = request.get_json()
            
            if not data or 'trends' not in data:
                raise ValidationError("Request must contain 'trends' data")
            
            trends_data = data['trends']
            tier = data.get('tier', get_config("services.default_tier", "budget"))
            
            # Validate tier
            quality_tier = QualityTier.from_string(tier)
            
            # Analyze trends
            logger.info(f"Analyzing {len(trends_data)} trends with {tier} tier")
            
            opportunities = []
            for trend_data in trends_data:
                try:
                    # Create TrendData object
                    trend = TrendData(
                        topic=trend_data['topic'],
                        source=trend_data.get('source', 'unknown'),
                        keywords=trend_data.get('keywords', []),
                        popularity_score=trend_data.get('popularity_score', 5.0),
                        growth_rate=trend_data.get('growth_rate', 1.0),
                        region=trend_data.get('region', 'TH'),
                        category=trend_data.get('category'),
                        search_volume=trend_data.get('search_volume'),
                        competition_level=trend_data.get('competition_level', 'medium')
                    )
                    
                    # Generate opportunity
                    opportunity = asyncio.run(
                        opportunity_engine.generate_opportunity(trend, quality_tier)
                    )
                    
                    if opportunity:
                        opportunities.append(opportunity.to_dict())
                        
                except Exception as e:
                    logger.warning(f"Failed to analyze trend '{trend_data.get('topic', 'unknown')}': {str(e)}")
                    continue
            
            # Rank opportunities
            opportunity_objects = [ContentOpportunity.from_dict(opp) for opp in opportunities]
            ranked_opportunities = rank_opportunities(opportunity_objects)
            
            result = {
                "total_analyzed": len(trends_data),
                "opportunities_generated": len(opportunities),
                "tier_used": tier,
                "analysis_timestamp": datetime.now().isoformat(),
                "opportunities": [opp.to_dict() for opp in ranked_opportunities[:20]]  # Top 20
            }
            
            # Cache results
            cache_key = f"trends_analysis_{hash(str(trends_data))}"
            cache_set(cache_key, result, ttl=3600)  # Cache for 1 hour
            
            logger.info(f"Generated {len(opportunities)} opportunities from {len(trends_data)} trends")
            
            return jsonify(result)
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error analyzing trends: {str(e)}")
            raise ServiceError(f"Failed to analyze trends: {str(e)}")
    
    # Content generation endpoints
    @app.route('/api/content/generate', methods=['POST'])
    def generate_content():
        """Generate content from opportunity"""
        try:
            data = request.get_json()
            
            if not data:
                raise ValidationError("Request body is required")
            
            # Handle different input types
            if 'opportunity_id' in data:
                # Generate from existing opportunity
                opportunity_id = data['opportunity_id']
                # In a real implementation, you'd load from database
                raise ValidationError("Opportunity loading from database not yet implemented")
                
            elif 'opportunity' in data:
                # Generate from opportunity data
                opportunity = ContentOpportunity.from_dict(data['opportunity'])
                
            elif 'topic' in data:
                # Generate from simple topic
                topic = data['topic']
                tier = data.get('tier', get_config("services.default_tier", "budget"))
                
                # Create simple trend data
                trend = TrendData(
                    topic=topic,
                    source='manual',
                    keywords=[topic],
                    popularity_score=7.0,
                    growth_rate=1.2,
                    region='TH'
                )
                
                # Generate opportunity
                quality_tier = QualityTier.from_string(tier)
                opportunity = asyncio.run(
                    opportunity_engine.generate_opportunity(trend, quality_tier)
                )
                
            else:
                raise ValidationError("Request must contain 'opportunity_id', 'opportunity', or 'topic'")
            
            # Get generation parameters
            tier = data.get('tier', get_config("services.default_tier", "budget"))
            content_type = data.get('content_type', 'educational')
            target_platforms = data.get('target_platforms', ['youtube'])
            
            # Generate content
            logger.info(f"Generating content for topic: {opportunity.trend_data.topic}")
            
            content_plan = asyncio.run(
                content_generator.generate_content_plan(
                    opportunity=opportunity,
                    tier=QualityTier.from_string(tier),
                    content_type=content_type,
                    target_platforms=target_platforms
                )
            )
            
            result = {
                "opportunity_id": opportunity.id,
                "topic": opportunity.trend_data.topic,
                "content_plan": content_plan,
                "tier_used": tier,
                "generation_timestamp": datetime.now().isoformat(),
                "estimated_cost": get_service_config('text_ai', tier).estimate_cost(len(str(content_plan)))
            }
            
            logger.info(f"Content generated successfully for topic: {opportunity.trend_data.topic}")
            
            return jsonify(result)
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error generating content: {str(e)}")
            raise ServiceError(f"Failed to generate content: {str(e)}")
    
    # Content pipeline endpoints
    @app.route('/api/content/pipeline/status', methods=['GET'])
    def get_pipeline_status():
        """Get content pipeline status"""
        try:
            status = {
                "active_jobs": 0,  # Would be from a job queue
                "pending_jobs": 0,
                "completed_jobs_today": 0,
                "failed_jobs_today": 0,
                "pipeline_health": "healthy",
                "last_job_completed": None,
                "average_processing_time": "2.5 minutes",
                "timestamp": datetime.now().isoformat()
            }
            
            return jsonify(status)
            
        except Exception as e:
            logger.error(f"Error getting pipeline status: {str(e)}")
            raise ServiceError(f"Failed to get pipeline status: {str(e)}")
    
    # Service management endpoints
    @app.route('/api/services/status', methods=['GET'])
    def get_services_status():
        """Get status of all AI services"""
        try:
            # Check service availability
            services_status = {}
            
            # Check text AI services
            text_ai_services = {}
            for tier in QualityTier:
                config = get_service_config('text_ai', tier)
                if config:
                    text_ai_services[tier.value] = {
                        "service": config.service_name,
                        "available": True,  # Would check actual service
                        "cost_per_unit": config.cost_per_unit,
                        "quality_score": config.quality_score
                    }
            
            services_status['text_ai'] = text_ai_services
            
            # Check audio AI services
            audio_ai_services = {}
            for tier in QualityTier:
                config = get_service_config('audio_ai', tier)
                if config:
                    audio_ai_services[tier.value] = {
                        "service": config.service_name,
                        "available": True,  # Would check actual service
                        "cost_per_unit": config.cost_per_unit,
                        "quality_score": config.quality_score
                    }
            
            services_status['audio_ai'] = audio_ai_services
            
            # Check image AI services
            image_ai_services = {}
            for tier in QualityTier:
                config = get_service_config('image_ai', tier)
                if config:
                    image_ai_services[tier.value] = {
                        "service": config.service_name,
                        "available": True,  # Would check actual service
                        "cost_per_unit": config.cost_per_unit,
                        "quality_score": config.quality_score
                    }
            
            services_status['image_ai'] = image_ai_services
            
            return jsonify({
                "services": services_status,
                "default_tier": get_config("services.default_tier", "budget"),
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error getting services status: {str(e)}")
            raise ServiceError(f"Failed to get services status: {str(e)}")
    
    # Cost estimation endpoints
    @app.route('/api/costs/estimate', methods=['POST'])
    def estimate_costs():
        """Estimate costs for content generation"""
        try:
            data = request.get_json()
            
            if not data:
                raise ValidationError("Request body is required")
            
            requests = data.get('requests', [])
            if not requests:
                raise ValidationError("'requests' array is required")
            
            # Calculate costs
            cost_breakdown = tier_manager.estimate_total_cost(requests)
            
            return jsonify({
                "cost_breakdown": cost_breakdown,
                "currency": "THB",
                "timestamp": datetime.now().isoformat()
            })
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error estimating costs: {str(e)}")
            raise ServiceError(f"Failed to estimate costs: {str(e)}")
    
    # Dashboard endpoint
    @app.route('/', methods=['GET'])
    def dashboard():
        """Main dashboard page"""
        try:
            # Get basic stats
            stats = {
                "total_opportunities": 0,  # Would be from database
                "opportunities_today": 0,
                "content_generated_today": 0,
                "total_cost_today": 0.0,
                "active_tier": get_config("services.default_tier", "budget"),
                "services_healthy": True
            }
            
            return render_template('dashboard.html', stats=stats)
            
        except Exception as e:
            logger.error(f"Error loading dashboard: {str(e)}")
            return f"Dashboard error: {str(e)}", 500

def run_app():
    """Run the Flask application"""
    host = get_config("app.host", "localhost")
    port = get_config("app.port", 5000)
    debug = get_config("app.debug", False)
    
    app.run(host=host, port=port, debug=debug, threaded=True)

if __name__ == '__main__':
    # Create the app
    create_app()
    
    # Run the application
    run_app()