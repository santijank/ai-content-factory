"""
Platform Manager Service
จัดการการอัปโหลดเนื้อหาไปยัง platforms ต่างๆ อัตโนมัติ
"""

import os
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import asdict

from flask import Flask, request, jsonify
from flask_cors import CORS
import asyncpg

from services.platform_manager import PlatformManager
from models.platform_type import PlatformType
from models.upload_metadata import UploadMetadata, UploadResult
from utils.config_manager import ConfigManager
from utils.content_optimizer import ContentOptimizer

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Global variables
platform_manager = None
db_pool = None
config = None

async def init_database():
    """Initialize database connection pool"""
    global db_pool
    
    try:
        database_url = os.getenv(
            'DATABASE_URL', 
            'postgresql://admin:password@localhost:5432/content_factory'
        )
        
        db_pool = await asyncpg.create_pool(
            database_url,
            min_size=2,
            max_size=10,
            command_timeout=60
        )
        
        logger.info("Database connection pool initialized")
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise

async def init_platform_manager():
    """Initialize platform manager"""
    global platform_manager, config
    
    try:
        config = ConfigManager()
        platform_manager = PlatformManager(config)
        
        # Test platform connections
        await platform_manager.test_connections()
        
        logger.info("Platform Manager initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize Platform Manager: {str(e)}")
        raise

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "platform-manager",
        "timestamp": datetime.now().isoformat(),
        "platforms_available": platform_manager.get_available_platforms() if platform_manager else []
    })

@app.route('/platforms', methods=['GET'])
def get_platforms():
    """Get available platforms and their status"""
    try:
        if not platform_manager:
            return jsonify({"error": "Platform manager not initialized"}), 500
            
        platforms_status = platform_manager.get_platforms_status()
        
        return jsonify({
            "success": True,
            "platforms": platforms_status,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting platforms: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/upload', methods=['POST'])
def upload_content():
    """Upload content to specified platforms"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        # Validate required fields
        required_fields = ['content_path', 'platforms', 'metadata']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            return jsonify({
                "error": f"Missing required fields: {missing_fields}"
            }), 400
        
        # Extract data
        content_path = data['content_path']
        platforms = data['platforms']
        metadata_dict = data['metadata']
        
        # Validate content file exists
        if not os.path.exists(content_path):
            return jsonify({"error": f"Content file not found: {content_path}"}), 400
        
        # Create metadata object
        upload_metadata = UploadMetadata(
            title=metadata_dict.get('title', 'Untitled'),
            description=metadata_dict.get('description', ''),
            tags=metadata_dict.get('tags', []),
            category=metadata_dict.get('category', 'Entertainment'),
            thumbnail_path=metadata_dict.get('thumbnail_path'),
            privacy=metadata_dict.get('privacy', 'public'),
            scheduled_time=metadata_dict.get('scheduled_time'),
            custom_fields=metadata_dict.get('custom_fields', {})
        )
        
        # Start upload process
        upload_task_id = f"upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Schedule async upload
        asyncio.create_task(
            process_upload_async(
                upload_task_id,
                content_path,
                platforms,
                upload_metadata
            )
        )
        
        return jsonify({
            "success": True,
            "task_id": upload_task_id,
            "message": "Upload process started",
            "platforms": platforms,
            "estimated_time": len(platforms) * 30  # seconds
        })
        
    except Exception as e:
        logger.error(f"Error in upload endpoint: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/upload/status/<task_id>', methods=['GET'])
async def get_upload_status(task_id: str):
    """Get upload status for a task"""
    try:
        async with db_pool.acquire() as conn:
            # Get upload records for this task
            uploads = await conn.fetch("""
                SELECT 
                    platform,
                    platform_id,
                    url,
                    metadata,
                    uploaded_at,
                    status
                FROM uploads 
                WHERE task_id = $1
                ORDER BY uploaded_at DESC
            """, task_id)
            
            upload_results = []
            for upload in uploads:
                upload_results.append({
                    "platform": upload['platform'],
                    "platform_id": upload['platform_id'],
                    "url": upload['url'],
                    "status": upload['status'],
                    "uploaded_at": upload['uploaded_at'].isoformat() if upload['uploaded_at'] else None,
                    "metadata": upload['metadata']
                })
            
            return jsonify({
                "success": True,
                "task_id": task_id,
                "uploads": upload_results,
                "total_uploads": len(upload_results)
            })
            
    except Exception as e:
        logger.error(f"Error getting upload status: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/upload/batch', methods=['POST'])
def upload_batch():
    """Upload multiple content items"""
    try:
        data = request.get_json()
        
        if not data or 'items' not in data:
            return jsonify({"error": "No items provided"}), 400
        
        items = data['items']
        batch_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Validate all items first
        for i, item in enumerate(items):
            required_fields = ['content_path', 'platforms', 'metadata']
            missing_fields = [field for field in required_fields if field not in item]
            
            if missing_fields:
                return jsonify({
                    "error": f"Item {i}: Missing required fields: {missing_fields}"
                }), 400
            
            if not os.path.exists(item['content_path']):
                return jsonify({
                    "error": f"Item {i}: Content file not found: {item['content_path']}"
                }), 400
        
        # Schedule batch upload
        asyncio.create_task(
            process_batch_upload_async(batch_id, items)
        )
        
        return jsonify({
            "success": True,
            "batch_id": batch_id,
            "message": "Batch upload process started",
            "total_items": len(items),
            "estimated_time": len(items) * 60  # seconds
        })
        
    except Exception as e:
        logger.error(f"Error in batch upload: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/content/optimize', methods=['POST'])
def optimize_content():
    """Optimize content for specific platform"""
    try:
        data = request.get_json()
        
        required_fields = ['content_path', 'platform']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            return jsonify({
                "error": f"Missing required fields: {missing_fields}"
            }), 400
        
        content_path = data['content_path']
        platform = data['platform']
        
        if not os.path.exists(content_path):
            return jsonify({"error": f"Content file not found: {content_path}"}), 400
        
        # Optimize content
        optimizer = ContentOptimizer()
        optimized_path = optimizer.optimize_for_platform(content_path, platform)
        
        return jsonify({
            "success": True,
            "original_path": content_path,
            "optimized_path": optimized_path,
            "platform": platform,
            "optimizations_applied": optimizer.get_last_optimizations()
        })
        
    except Exception as e:
        logger.error(f"Error optimizing content: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/analytics/uploads', methods=['GET'])
async def get_upload_analytics():
    """Get upload analytics"""
    try:
        # Get query parameters
        days = request.args.get('days', 7, type=int)
        platform = request.args.get('platform')
        
        async with db_pool.acquire() as conn:
            # Base query
            base_query = """
                SELECT 
                    platform,
                    COUNT(*) as total_uploads,
                    COUNT(CASE WHEN url IS NOT NULL THEN 1 END) as successful_uploads,
                    COUNT(CASE WHEN url IS NULL THEN 1 END) as failed_uploads,
                    AVG(EXTRACT(EPOCH FROM (uploaded_at - created_at))) as avg_upload_time
                FROM uploads 
                WHERE uploaded_at >= NOW() - INTERVAL '%s days'
            """
            
            params = [days]
            
            if platform:
                base_query += " AND platform = $2"
                params.append(platform)
            
            base_query += " GROUP BY platform ORDER BY total_uploads DESC"
            
            results = await conn.fetch(base_query, *params)
            
            analytics = []
            for row in results:
                analytics.append({
                    "platform": row['platform'],
                    "total_uploads": row['total_uploads'],
                    "successful_uploads": row['successful_uploads'],
                    "failed_uploads": row['failed_uploads'],
                    "success_rate": (row['successful_uploads'] / row['total_uploads'] * 100) if row['total_uploads'] > 0 else 0,
                    "avg_upload_time_seconds": row['avg_upload_time']
                })
            
            return jsonify({
                "success": True,
                "period_days": days,
                "analytics": analytics,
                "generated_at": datetime.now().isoformat()
            })
            
    except Exception as e:
        logger.error(f"Error getting analytics: {str(e)}")
        return jsonify({"error": str(e)}), 500

async def process_upload_async(
    task_id: str,
    content_path: str,
    platforms: List[str],
    metadata: UploadMetadata
):
    """Process upload asynchronously"""
    try:
        logger.info(f"Starting upload task {task_id} for platforms: {platforms}")
        
        # Upload to each platform
        upload_results = await platform_manager.upload_content(
            content_path, platforms, metadata
        )
        
        # Store results in database
        async with db_pool.acquire() as conn:
            for platform, result in upload_results.items():
                await conn.execute("""
                    INSERT INTO uploads (
                        task_id, content_path, platform, platform_id, 
                        url, metadata, status, uploaded_at, created_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """, 
                task_id,
                content_path,
                platform,
                result.platform_id if result.success else None,
                result.url if result.success else None,
                json.dumps(asdict(result)),
                'success' if result.success else 'failed',
                datetime.now() if result.success else None,
                datetime.now()
                )
        
        logger.info(f"Upload task {task_id} completed")
        
    except Exception as e:
        logger.error(f"Error in upload task {task_id}: {str(e)}")
        
        # Record failure
        async with db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO uploads (
                    task_id, content_path, status, metadata, created_at
                ) VALUES ($1, $2, $3, $4, $5)
            """, 
            task_id,
            content_path,
            'failed',
            json.dumps({"error": str(e)}),
            datetime.now()
            )

async def process_batch_upload_async(batch_id: str, items: List[Dict]):
    """Process batch upload asynchronously"""
    try:
        logger.info(f"Starting batch upload {batch_id} with {len(items)} items")
        
        for i, item in enumerate(items):
            task_id = f"{batch_id}_item_{i}"
            
            # Create metadata object
            metadata_dict = item['metadata']
            upload_metadata = UploadMetadata(
                title=metadata_dict.get('title', f'Batch Item {i+1}'),
                description=metadata_dict.get('description', ''),
                tags=metadata_dict.get('tags', []),
                category=metadata_dict.get('category', 'Entertainment'),
                thumbnail_path=metadata_dict.get('thumbnail_path'),
                privacy=metadata_dict.get('privacy', 'public'),
                scheduled_time=metadata_dict.get('scheduled_time'),
                custom_fields=metadata_dict.get('custom_fields', {})
            )
            
            # Process individual upload
            await process_upload_async(
                task_id,
                item['content_path'],
                item['platforms'],
                upload_metadata
            )
            
            # Small delay between uploads to avoid rate limits
            await asyncio.sleep(5)
        
        logger.info(f"Batch upload {batch_id} completed")
        
    except Exception as e:
        logger.error(f"Error in batch upload {batch_id}: {str(e)}")

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    import asyncio
    
    async def startup():
        """Initialize all services"""
        await init_database()
        await init_platform_manager()
        
        logger.info("Platform Manager Service started successfully")
    
    # Run startup in event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(startup())
    
    # Start Flask app
    app.run(
        host='0.0.0.0',
        port=int(os.getenv('PORT', 5003)),
        debug=os.getenv('DEBUG', 'False').lower() == 'true'
    )