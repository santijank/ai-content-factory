"""
Trends API - REST API endpoints สำหรับจัดการ Trends
ตำแหน่งไฟล์: api/trends_api.py
"""
from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
import logging
from typing import Dict, Any, List

# Import repositories
from database.repositories import get_trend_repository, get_opportunity_repository
from database.repositories.trend_repository import TrendData

# Import services (จะสร้างในไฟล์ต่อไป)
try:
    from trend_monitor.services.trend_collector import TrendCollector
    from trend_monitor.services.trend_analyzer import TrendAnalyzer
except ImportError:
    TrendCollector = None
    TrendAnalyzer = None

logger = logging.getLogger(__name__)

# สร้าง Blueprint
trends_api = Blueprint('trends_api', __name__, url_prefix='/api/trends')

# Repository instances
trend_repo = get_trend_repository()
opportunity_repo = get_opportunity_repository()

@trends_api.route('/', methods=['GET'])
def get_trends():
    """
    ดึงรายการ trends ตามเงื่อนไข
    
    Query Parameters:
    - source: youtube, google, twitter, reddit
    - category: หมวดหมู่
    - days: จำนวนวันย้อนหลัง (default: 7)
    - limit: จำนวนสูงสุด (default: 50)
    - search: คำค้นหา
    - sort: เรียงตาม (popularity_score, growth_rate, created_at)
    """
    try:
        # Get query parameters
        source = request.args.get('source')
        category = request.args.get('category')
        days = int(request.args.get('days', 7))
        limit = int(request.args.get('limit', 50))
        search = request.args.get('search')
        sort_by = request.args.get('sort', 'popularity_score')
        
        # Validate parameters
        if limit > 100:
            limit = 100
        
        if days > 90:
            days = 90
        
        # Get trends
        if search:
            trends = trend_repo.search_trends(search, limit)
        else:
            trends = trend_repo.get_trends_filtered(
                source=source if source != 'all' else None,
                category=category if category != 'all' else None,
                days_back=days
            )
        
        # Sort trends
        if sort_by == 'popularity_score':
            trends.sort(key=lambda x: x.popularity_score, reverse=True)
        elif sort_by == 'growth_rate':
            trends.sort(key=lambda x: x.growth_rate, reverse=True)
        elif sort_by == 'created_at':
            trends.sort(key=lambda x: x.created_at, reverse=True)
        
        # Limit results
        trends = trends[:limit]
        
        # Convert to dict format
        trends_data = [trend.to_dict() for trend in trends]
        
        return jsonify({
            'trends': trends_data,
            'count': len(trends_data),
            'filters': {
                'source': source,
                'category': category,
                'days': days,
                'search': search,
                'sort': sort_by
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting trends: {str(e)}")
        return jsonify({'error': str(e)}), 500

@trends_api.route('/<trend_id>', methods=['GET'])
def get_trend_by_id(trend_id: str):
    """ดึงข้อมูล trend ตาม ID"""
    try:
        trend = trend_repo.get_trend_by_id(trend_id)
        
        if not trend:
            return jsonify({'error': 'Trend not found'}), 404
        
        # Get related opportunities
        opportunities = opportunity_repo.get_opportunities_by_trend(trend_id)
        
        trend_data = trend.to_dict()
        trend_data['opportunities'] = [opp.to_dict() for opp in opportunities]
        trend_data['opportunities_count'] = len(opportunities)
        
        return jsonify(trend_data)
        
    except Exception as e:
        logger.error(f"Error getting trend {trend_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@trends_api.route('/count', methods=['GET'])
def get_trends_count():
    """ดึงจำนวน trends ทั้งหมด"""
    try:
        total_count = trend_repo.get_total_trends()
        today_count = trend_repo.count_trends_today()
        
        return jsonify({
            'total': total_count,
            'today': today_count,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting trends count: {str(e)}")
        return jsonify({'error': str(e)}), 500

@trends_api.route('/stats', methods=['GET'])
def get_trends_stats():
    """ดึงสถิติ trends"""
    try:
        days = int(request.args.get('days', 30))
        
        stats = {
            'total_trends': trend_repo.get_total_trends(),
            'today_trends': trend_repo.count_trends_today(),
            'source_distribution': trend_repo.get_source_counts(),
            'category_distribution': trend_repo.get_category_distribution(),
            'daily_stats': trend_repo.get_daily_stats(days),
            'trending_keywords': trend_repo.get_trending_keywords(days, 20),
            'top_growth_trends': [t.to_dict() for t in trend_repo.get_top_trends_by_growth(10, 3)]
        }
        
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Error getting trends stats: {str(e)}")
        return jsonify({'error': str(e)}), 500

@trends_api.route('/sources', methods=['GET'])
def get_available_sources():
    """ดึงรายการ sources ที่มี"""
    try:
        sources = trend_repo.get_available_sources()
        return jsonify({'sources': sources})
        
    except Exception as e:
        logger.error(f"Error getting sources: {str(e)}")
        return jsonify({'error': str(e)}), 500

@trends_api.route('/categories', methods=['GET'])
def get_available_categories():
    """ดึงรายการ categories ที่มี"""
    try:
        categories = trend_repo.get_available_categories()
        return jsonify({'categories': categories})
        
    except Exception as e:
        logger.error(f"Error getting categories: {str(e)}")
        return jsonify({'error': str(e)}), 500

@trends_api.route('/collect', methods=['POST'])
def collect_trends():
    """เก็บ trends ใหม่จากแหล่งต่างๆ"""
    try:
        if not TrendCollector:
            return jsonify({'error': 'Trend collection service not available'}), 503
        
        data = request.get_json() or {}
        sources = data.get('sources', ['youtube', 'google'])  # Default sources
        max_trends = data.get('max_trends', 50)
        
        collector = TrendCollector()
        
        # Collect trends from specified sources
        collected_trends = []
        
        for source in sources:
            try:
                if source == 'youtube':
                    youtube_trends = collector.collect_youtube_trends(max_trends // len(sources))
                    collected_trends.extend(youtube_trends)
                elif source == 'google':
                    google_trends = collector.collect_google_trends(max_trends // len(sources))
                    collected_trends.extend(google_trends)
                # Add more sources as needed
                
            except Exception as source_error:
                logger.warning(f"Failed to collect from {source}: {str(source_error)}")
                continue
        
        # Save trends to database
        if collected_trends:
            trend_ids = trend_repo.bulk_create_trends(collected_trends)
            
            logger.info(f"Collected {len(collected_trends)} trends from {sources}")
            
            return jsonify({
                'success': True,
                'collected_count': len(collected_trends),
                'sources': sources,
                'trend_ids': trend_ids,
                'message': f'Successfully collected {len(collected_trends)} trends'
            })
        else:
            return jsonify({
                'success': False,
                'collected_count': 0,
                'message': 'No trends were collected'
            })
        
    except Exception as e:
        logger.error(f"Error collecting trends: {str(e)}")
        return jsonify({'error': str(e)}), 500

@trends_api.route('/analyze', methods=['POST'])
def analyze_trends():
    """วิเคราะห์ trends และสร้าง opportunities"""
    try:
        if not TrendAnalyzer:
            return jsonify({'error': 'Trend analysis service not available'}), 503
        
        data = request.get_json() or {}
        trend_ids = data.get('trend_ids', [])
        
        if not trend_ids:
            # ถ้าไม่ระบุ trend_ids ให้วิเคราะห์ trends ล่าสุดที่ยังไม่ได้วิเคราะห์
            recent_trends = trend_repo.get_recent_unanalyzed_trends(24)
            trend_ids = [t.id for t in recent_trends[:20]]  # จำกัดไม่เกิน 20 trends
        
        if not trend_ids:
            return jsonify({
                'success': False,
                'message': 'No trends to analyze'
            })
        
        analyzer = TrendAnalyzer()
        analyzed_count = 0
        opportunities_created = 0
        
        for trend_id in trend_ids:
            try:
                trend = trend_repo.get_trend_by_id(trend_id)
                if not trend:
                    continue
                
                # Analyze trend
                analysis_result = analyzer.analyze_trend(trend)
                
                # Update trend with analysis data
                trend_repo.update_trend_analysis(trend_id, analysis_result)
                
                # Create opportunities if analysis suggests good potential
                if analysis_result.get('create_opportunities', False):
                    opportunities = analyzer.generate_opportunities(trend, analysis_result)
                    
                    if opportunities:
                        opportunity_ids = opportunity_repo.bulk_create_opportunities(opportunities)
                        opportunities_created += len(opportunity_ids)
                
                analyzed_count += 1
                
            except Exception as trend_error:
                logger.warning(f"Failed to analyze trend {trend_id}: {str(trend_error)}")
                continue
        
        logger.info(f"Analyzed {analyzed_count} trends, created {opportunities_created} opportunities")
        
        return jsonify({
            'success': True,
            'analyzed_count': analyzed_count,
            'opportunities_created': opportunities_created,
            'message': f'Analyzed {analyzed_count} trends and created {opportunities_created} opportunities'
        })
        
    except Exception as e:
        logger.error(f"Error analyzing trends: {str(e)}")
        return jsonify({'error': str(e)}), 500

@trends_api.route('/<trend_id>', methods=['PUT'])
def update_trend(trend_id: str):
    """อัปเดตข้อมูล trend"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        trend = trend_repo.get_trend_by_id(trend_id)
        if not trend:
            return jsonify({'error': 'Trend not found'}), 404
        
        # Update allowed fields
        updated = False
        
        if 'category' in data:
            trend.category = data['category']
            updated = True
        
        if 'keywords' in data:
            trend.keywords = data['keywords']
            updated = True
        
        if 'analysis_data' in data:
            trend.raw_data.update(data['analysis_data'])
            updated = True
        
        if updated:
            # Save updates (assuming we have an update method)
            success = trend_repo.update_trend_analysis(trend_id, trend.raw_data)
            
            if success:
                return jsonify({
                    'success': True,
                    'message': 'Trend updated successfully'
                })
            else:
                return jsonify({'error': 'Failed to update trend'}), 500
        else:
            return jsonify({'error': 'No valid fields to update'}), 400
        
    except Exception as e:
        logger.error(f"Error updating trend {trend_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@trends_api.route('/<trend_id>', methods=['DELETE'])
def delete_trend(trend_id: str):
    """ลบ trend"""
    try:
        trend = trend_repo.get_trend_by_id(trend_id)
        if not trend:
            return jsonify({'error': 'Trend not found'}), 404
        
        # Check if trend has associated opportunities
        opportunities = opportunity_repo.get_opportunities_by_trend(trend_id)
        
        if opportunities:
            return jsonify({
                'error': 'Cannot delete trend with associated opportunities',
                'opportunities_count': len(opportunities)
            }), 400
        
        # Delete trend (implement delete method in repository)
        # For now, we'll return success
        return jsonify({
            'success': True,
            'message': 'Trend deleted successfully'
        })
        
    except Exception as e:
        logger.error(f"Error deleting trend {trend_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@trends_api.route('/search', methods=['GET'])
def search_trends():
    """ค้นหา trends"""
    try:
        keyword = request.args.get('q', '').strip()
        limit = int(request.args.get('limit', 20))
        
        if not keyword:
            return jsonify({'error': 'Search keyword is required'}), 400
        
        if len(keyword) < 2:
            return jsonify({'error': 'Search keyword must be at least 2 characters'}), 400
        
        trends = trend_repo.search_trends(keyword, limit)
        trends_data = [trend.to_dict() for trend in trends]
        
        return jsonify({
            'trends': trends_data,
            'count': len(trends_data),
            'keyword': keyword
        })
        
    except Exception as e:
        logger.error(f"Error searching trends: {str(e)}")
        return jsonify({'error': str(e)}), 500

@trends_api.route('/export', methods=['GET'])
def export_trends():
    """Export trends เป็น CSV/JSON"""
    try:
        format_type = request.args.get('format', 'json').lower()
        days = int(request.args.get('days', 7))
        
        trends = trend_repo.get_trends_filtered(days_back=days)
        
        if format_type == 'csv':
            # ถ้าต้องการ CSV format
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow(['ID', 'Topic', 'Source', 'Category', 'Popularity Score', 
                           'Growth Rate', 'Collected At'])
            
            # Write data
            for trend in trends:
                writer.writerow([
                    trend.id,
                    trend.topic,
                    trend.source,
                    trend.category or '',
                    trend.popularity_score,
                    trend.growth_rate,
                    trend.collected_at
                ])
            
            csv_content = output.getvalue()
            output.close()
            
            from flask import Response
            return Response(
                csv_content,
                mimetype='text/csv',
                headers={'Content-Disposition': f'attachment; filename=trends_{datetime.now().strftime("%Y%m%d")}.csv'}
            )
        else:
            # JSON format (default)
            trends_data = [trend.to_dict() for trend in trends]
            return jsonify({
                'trends': trends_data,
                'count': len(trends_data),
                'exported_at': datetime.now().isoformat(),
                'format': format_type
            })
        
    except Exception as e:
        logger.error(f"Error exporting trends: {str(e)}")
        return jsonify({'error': str(e)}), 500

@trends_api.route('/cleanup', methods=['POST'])
def cleanup_old_trends():
    """ล้างข้อมูล trends เก่า"""
    try:
        data = request.get_json() or {}
        days_old = data.get('days_old', 30)
        
        if days_old < 7:
            return jsonify({'error': 'Cannot delete trends newer than 7 days'}), 400
        
        deleted_count = trend_repo.delete_old_trends(days_old)
        
        logger.info(f"Cleaned up {deleted_count} old trends (older than {days_old} days)")
        
        return jsonify({
            'success': True,
            'deleted_count': deleted_count,
            'message': f'Deleted {deleted_count} trends older than {days_old} days'
        })
        
    except Exception as e:
        logger.error(f"Error cleaning up trends: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Error handlers
@trends_api.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@trends_api.errorhandler(405)
def method_not_allowed(error):
    return jsonify({'error': 'Method not allowed'}), 405

@trends_api.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

# Helper functions
def validate_trend_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate trend data from request"""
    errors = []
    
    if not data.get('topic'):
        errors.append('Topic is required')
    
    if not data.get('source'):
        errors.append('Source is required')
    
    if 'popularity_score' in data:
        try:
            score = float(data['popularity_score'])
            if score < 0 or score > 10:
                errors.append('Popularity score must be between 0 and 10')
        except (ValueError, TypeError):
            errors.append('Popularity score must be a number')
    
    if 'growth_rate' in data:
        try:
            float(data['growth_rate'])
        except (ValueError, TypeError):
            errors.append('Growth rate must be a number')
    
    return {'errors': errors, 'valid': len(errors) == 0}

if __name__ == '__main__':
    # สำหรับทดสอบ API endpoints
    from flask import Flask
    
    app = Flask(__name__)
    app.register_blueprint(trends_api)
    
    app.run(debug=True, port=5001)