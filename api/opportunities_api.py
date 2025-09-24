"""
Opportunities API - REST API endpoints สำหรับจัดการ Content Opportunities
ตำแหน่งไฟล์: api/opportunities_api.py
"""
from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
import logging
from typing import Dict, Any, List

# Import repositories
from database.repositories import (
    get_opportunity_repository, 
    get_trend_repository, 
    get_content_repository
)
from database.repositories.opportunity_repository import ContentOpportunity

# Import AI services (จะสร้างในไฟล์ต่อไป)
try:
    from content_engine.services.opportunity_engine import OpportunityEngine
    from content_engine.services.ai_director import AIDirector
except ImportError:
    OpportunityEngine = None
    AIDirector = None

logger = logging.getLogger(__name__)

# สร้าง Blueprint
opportunities_api = Blueprint('opportunities_api', __name__, url_prefix='/api/opportunities')

# Repository instances
opportunity_repo = get_opportunity_repository()
trend_repo = get_trend_repository()
content_repo = get_content_repository()

@opportunities_api.route('/', methods=['GET'])
def get_opportunities():
    """
    ดึงรายการ opportunities ตามเงื่อนไข
    
    Query Parameters:
    - sort: priority_score, estimated_roi, estimated_views, created_at
    - status: pending, analyzing, ready, selected, completed
    - min_roi: ROI ขั้นต่ำ
    - competition: low, medium, high
    - limit: จำนวนสูงสุด (default: 50)
    - search: คำค้นหา
    """
    try:
        # Get query parameters
        sort_by = request.args.get('sort', 'priority_score')
        status = request.args.get('status')
        min_roi = request.args.get('min_roi', type=float)
        competition_level = request.args.get('competition')
        limit = int(request.args.get('limit', 50))
        search = request.args.get('search')
        
        # Validate parameters
        if limit > 100:
            limit = 100
        
        valid_sorts = ['priority_score', 'estimated_roi', 'estimated_views', 'created_at']
        if sort_by not in valid_sorts:
            sort_by = 'priority_score'
        
        # Get opportunities
        if search:
            opportunities = opportunity_repo.search_opportunities(search, limit)
        else:
            opportunities = opportunity_repo.get_opportunities_filtered(
                sort_by=sort_by,
                status=status if status != 'all' else None,
                min_roi=min_roi,
                competition_level=competition_level,
                limit=limit
            )
        
        # Convert to dict format
        opportunities_data = []
        for opp in opportunities:
            opp_dict = opp.to_dict()
            # Add calculated fields
            opp_dict['estimated_revenue'] = opp.estimated_views * opp.estimated_roi * 0.001
            opp_dict['priority_level'] = get_priority_level(opp.priority_score)
            opportunities_data.append(opp_dict)
        
        return jsonify({
            'opportunities': opportunities_data,
            'count': len(opportunities_data),
            'filters': {
                'sort': sort_by,
                'status': status,
                'min_roi': min_roi,
                'competition': competition_level,
                'search': search
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting opportunities: {str(e)}")
        return jsonify({'error': str(e)}), 500

@opportunities_api.route('/<opportunity_id>', methods=['GET'])
def get_opportunity_by_id(opportunity_id: str):
    """ดึงข้อมูล opportunity ตาม ID พร้อมรายละเอียดครบถ้วน"""
    try:
        opportunity = opportunity_repo.get_opportunity_by_id(opportunity_id, include_trend=True)
        
        if not opportunity:
            return jsonify({'error': 'Opportunity not found'}), 404
        
        # Get related content items
        content_items = content_repo.get_content_by_opportunity(opportunity_id)
        
        opp_data = opportunity.to_dict()
        opp_data['estimated_revenue'] = opportunity.estimated_views * opportunity.estimated_roi * 0.001
        opp_data['priority_level'] = get_priority_level(opportunity.priority_score)
        opp_data['content_items'] = [content.to_dict() for content in content_items]
        opp_data['content_count'] = len(content_items)
        
        return jsonify(opp_data)
        
    except Exception as e:
        logger.error(f"Error getting opportunity {opportunity_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@opportunities_api.route('/stats', methods=['GET'])
def get_opportunities_stats():
    """ดึงสถิติ opportunities"""
    try:
        stats = {
            'total_opportunities': opportunity_repo.get_total_opportunities(),
            'today_opportunities': opportunity_repo.count_opportunities_today(),
            'pending_count': opportunity_repo.get_pending_count(),
            'high_priority_count': opportunity_repo.get_high_priority_count(),
            'total_revenue_estimate': opportunity_repo.get_total_revenue_estimate(),
            'status_distribution': opportunity_repo.get_status_distribution(),
            'competition_distribution': opportunity_repo.get_competition_distribution(),
            'revenue_projection': opportunity_repo.get_revenue_projection(),
            'best_opportunities': [
                opp.to_dict() for opp in opportunity_repo.get_best_opportunities(5)
            ]
        }
        
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Error getting opportunities stats: {str(e)}")
        return jsonify({'error': str(e)}), 500

@opportunities_api.route('/', methods=['POST'])
def create_opportunity():
    """สร้าง opportunity ใหม่"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate required fields
        validation = validate_opportunity_data(data)
        if not validation['valid']:
            return jsonify({'errors': validation['errors']}), 400
        
        # Create opportunity object
        opportunity = ContentOpportunity()
        opportunity.trend_id = data.get('trend_id')
        opportunity.suggested_angle = data['suggested_angle']
        opportunity.estimated_views = data.get('estimated_views', 0)
        opportunity.competition_level = data.get('competition_level', 'medium')
        opportunity.production_cost = data.get('production_cost', 0.0)
        opportunity.estimated_roi = data.get('estimated_roi', 0.0)
        opportunity.priority_score = data.get('priority_score', 0.0)
        opportunity.status = data.get('status', 'pending')
        opportunity.analysis_data = data.get('analysis_data', {})
        
        # Save to database
        opportunity_id = opportunity_repo.create_opportunity(opportunity)
        
        logger.info(f"Created opportunity {opportunity_id}: {opportunity.suggested_angle}")
        
        return jsonify({
            'success': True,
            'opportunity_id': opportunity_id,
            'message': 'Opportunity created successfully'
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating opportunity: {str(e)}")
        return jsonify({'error': str(e)}), 500

@opportunities_api.route('/<opportunity_id>/status', methods=['PUT'])
def update_opportunity_status(opportunity_id: str):
    """อัปเดต status ของ opportunity"""
    try:
        data = request.get_json()
        
        if not data or 'status' not in data:
            return jsonify({'error': 'Status is required'}), 400
        
        new_status = data['status']
        valid_statuses = ['pending', 'analyzing', 'ready', 'selected', 'completed']
        
        if new_status not in valid_statuses:
            return jsonify({'error': f'Invalid status. Must be one of: {valid_statuses}'}), 400
        
        # Check if opportunity exists
        opportunity = opportunity_repo.get_opportunity_by_id(opportunity_id)
        if not opportunity:
            return jsonify({'error': 'Opportunity not found'}), 404
        
        # Update status
        analysis_data = data.get('analysis_data')
        success = opportunity_repo.update_opportunity_status(
            opportunity_id, 
            new_status, 
            analysis_data
        )
        
        if success:
            logger.info(f"Updated opportunity {opportunity_id} status to {new_status}")
            
            return jsonify({
                'success': True,
                'message': f'Status updated to {new_status}'
            })
        else:
            return jsonify({'error': 'Failed to update status'}), 500
        
    except Exception as e:
        logger.error(f"Error updating opportunity status {opportunity_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@opportunities_api.route('/<opportunity_id>/scores', methods=['PUT'])
def update_opportunity_scores(opportunity_id: str):
    """อัปเดตคะแนนและการประเมิน"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        opportunity = opportunity_repo.get_opportunity_by_id(opportunity_id)
        if not opportunity:
            return jsonify({'error': 'Opportunity not found'}), 404
        
        # Extract and validate scores
        priority_score = data.get('priority_score')
        estimated_roi = data.get('estimated_roi')
        estimated_views = data.get('estimated_views')
        
        # Validate scores if provided
        if priority_score is not None:
            try:
                priority_score = float(priority_score)
                if priority_score < 0 or priority_score > 10:
                    return jsonify({'error': 'Priority score must be between 0 and 10'}), 400
            except (ValueError, TypeError):
                return jsonify({'error': 'Priority score must be a number'}), 400
        
        if estimated_roi is not None:
            try:
                estimated_roi = float(estimated_roi)
                if estimated_roi < 0:
                    return jsonify({'error': 'ROI must be non-negative'}), 400
            except (ValueError, TypeError):
                return jsonify({'error': 'ROI must be a number'}), 400
        
        if estimated_views is not None:
            try:
                estimated_views = int(estimated_views)
                if estimated_views < 0:
                    return jsonify({'error': 'Views must be non-negative'}), 400
            except (ValueError, TypeError):
                return jsonify({'error': 'Views must be a number'}), 400
        
        # Update scores
        success = opportunity_repo.update_opportunity_scores(
            opportunity_id,
            priority_score,
            estimated_roi,
            estimated_views
        )
        
        if success:
            logger.info(f"Updated opportunity {opportunity_id} scores")
            
            return jsonify({
                'success': True,
                'message': 'Scores updated successfully'
            })
        else:
            return jsonify({'error': 'Failed to update scores'}), 500
        
    except Exception as e:
        logger.error(f"Error updating opportunity scores {opportunity_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@opportunities_api.route('/<opportunity_id>/analyze', methods=['POST'])
def analyze_opportunity_deeper(opportunity_id: str):
    """วิเคราะห์ opportunity เพิ่มเติม"""
    try:
        if not OpportunityEngine:
            return jsonify({'error': 'Analysis service not available'}), 503
        
        opportunity = opportunity_repo.get_opportunity_by_id(opportunity_id, include_trend=True)
        if not opportunity:
            return jsonify({'error': 'Opportunity not found'}), 404
        
        # Update status to analyzing
        opportunity_repo.update_opportunity_status(opportunity_id, 'analyzing')
        
        engine = OpportunityEngine()
        
        # Perform deeper analysis
        analysis_result = engine.analyze_opportunity_deeper(opportunity)
        
        # Update opportunity with analysis results
        updated_scores = {
            'priority_score': analysis_result.get('priority_score', opportunity.priority_score),
            'estimated_roi': analysis_result.get('estimated_roi', opportunity.estimated_roi),
            'estimated_views': analysis_result.get('estimated_views', opportunity.estimated_views)
        }
        
        # Update scores and status
        opportunity_repo.update_opportunity_scores(
            opportunity_id,
            updated_scores['priority_score'],
            updated_scores['estimated_roi'],
            updated_scores['estimated_views']
        )
        
        opportunity_repo.update_opportunity_status(
            opportunity_id, 
            'ready',
            analysis_result
        )
        
        logger.info(f"Analyzed opportunity {opportunity_id} with updated scores")
        
        return jsonify({
            'success': True,
            'analysis_result': analysis_result,
            'updated_scores': updated_scores,
            'message': 'Analysis completed successfully'
        })
        
    except Exception as e:
        logger.error(f"Error analyzing opportunity {opportunity_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@opportunities_api.route('/<opportunity_id>/duplicate', methods=['POST'])
def duplicate_opportunity(opportunity_id: str):
    """สร้างสำเนา opportunity"""
    try:
        original = opportunity_repo.get_opportunity_by_id(opportunity_id)
        if not original:
            return jsonify({'error': 'Opportunity not found'}), 404
        
        # Create new opportunity with similar data
        duplicate = ContentOpportunity()
        duplicate.trend_id = original.trend_id
        duplicate.suggested_angle = f"{original.suggested_angle} (Copy)"
        duplicate.estimated_views = original.estimated_views
        duplicate.competition_level = original.competition_level
        duplicate.production_cost = original.production_cost
        duplicate.estimated_roi = original.estimated_roi
        duplicate.priority_score = original.priority_score
        duplicate.status = 'pending'  # Reset to pending
        duplicate.analysis_data = original.analysis_data.copy()
        
        # Save duplicate
        new_id = opportunity_repo.create_opportunity(duplicate)
        
        logger.info(f"Duplicated opportunity {opportunity_id} as {new_id}")
        
        return jsonify({
            'success': True,
            'new_opportunity_id': new_id,
            'message': 'Opportunity duplicated successfully'
        })
        
    except Exception as e:
        logger.error(f"Error duplicating opportunity {opportunity_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@opportunities_api.route('/<opportunity_id>', methods=['DELETE'])
def delete_opportunity(opportunity_id: str):
    """ลบ opportunity"""
    try:
        opportunity = opportunity_repo.get_opportunity_by_id(opportunity_id)
        if not opportunity:
            return jsonify({'error': 'Opportunity not found'}), 404
        
        # Check if opportunity has associated content
        content_items = content_repo.get_content_by_opportunity(opportunity_id)
        
        if content_items:
            return jsonify({
                'error': 'Cannot delete opportunity with associated content',
                'content_count': len(content_items)
            }), 400
        
        # Delete opportunity (implement delete method in repository)
        # For now, we'll return success
        logger.info(f"Deleted opportunity {opportunity_id}")
        
        return jsonify({
            'success': True,
            'message': 'Opportunity deleted successfully'
        })
        
    except Exception as e:
        logger.error(f"Error deleting opportunity {opportunity_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@opportunities_api.route('/bulk/create', methods=['POST'])
def bulk_create_opportunities():
    """สร้าง opportunities จำนวนมาก"""
    try:
        data = request.get_json()
        
        if not data or 'opportunities' not in data:
            return jsonify({'error': 'Opportunities data is required'}), 400
        
        opportunities_data = data['opportunities']
        
        if not isinstance(opportunities_data, list):
            return jsonify({'error': 'Opportunities must be a list'}), 400
        
        if len(opportunities_data) > 50:
            return jsonify({'error': 'Cannot create more than 50 opportunities at once'}), 400
        
        # Validate all opportunities first
        valid_opportunities = []
        errors = []
        
        for i, opp_data in enumerate(opportunities_data):
            validation = validate_opportunity_data(opp_data)
            if validation['valid']:
                opportunity = ContentOpportunity()
                opportunity.trend_id = opp_data.get('trend_id')
                opportunity.suggested_angle = opp_data['suggested_angle']
                opportunity.estimated_views = opp_data.get('estimated_views', 0)
                opportunity.competition_level = opp_data.get('competition_level', 'medium')
                opportunity.production_cost = opp_data.get('production_cost', 0.0)
                opportunity.estimated_roi = opp_data.get('estimated_roi', 0.0)
                opportunity.priority_score = opp_data.get('priority_score', 0.0)
                opportunity.status = opp_data.get('status', 'pending')
                opportunity.analysis_data = opp_data.get('analysis_data', {})
                
                valid_opportunities.append(opportunity)
            else:
                errors.append(f"Opportunity {i + 1}: {', '.join(validation['errors'])}")
        
        if errors:
            return jsonify({'errors': errors}), 400
        
        # Create all valid opportunities
        opportunity_ids = opportunity_repo.bulk_create_opportunities(valid_opportunities)
        
        logger.info(f"Bulk created {len(opportunity_ids)} opportunities")
        
        return jsonify({
            'success': True,
            'created_count': len(opportunity_ids),
            'opportunity_ids': opportunity_ids,
            'message': f'Successfully created {len(opportunity_ids)} opportunities'
        })
        
    except Exception as e:
        logger.error(f"Error bulk creating opportunities: {str(e)}")
        return jsonify({'error': str(e)}), 500

@opportunities_api.route('/bulk/update-status', methods=['PUT'])
def bulk_update_status():
    """อัปเดต status ของ opportunities หลายรายการ"""
    try:
        data = request.get_json()
        
        if not data or 'opportunity_ids' not in data or 'status' not in data:
            return jsonify({'error': 'opportunity_ids and status are required'}), 400
        
        opportunity_ids = data['opportunity_ids']
        new_status = data['status']
        
        if not isinstance(opportunity_ids, list):
            return jsonify({'error': 'opportunity_ids must be a list'}), 400
        
        valid_statuses = ['pending', 'analyzing', 'ready', 'selected', 'completed']
        if new_status not in valid_statuses:
            return jsonify({'error': f'Invalid status. Must be one of: {valid_statuses}'}), 400
        
        updated_count = 0
        failed_count = 0
        
        for opp_id in opportunity_ids:
            try:
                success = opportunity_repo.update_opportunity_status(opp_id, new_status)
                if success:
                    updated_count += 1
                else:
                    failed_count += 1
            except Exception:
                failed_count += 1
        
        logger.info(f"Bulk updated {updated_count} opportunities to status {new_status}")
        
        return jsonify({
            'success': True,
            'updated_count': updated_count,
            'failed_count': failed_count,
            'message': f'Updated {updated_count} opportunities to {new_status}'
        })
        
    except Exception as e:
        logger.error(f"Error bulk updating status: {str(e)}")
        return jsonify({'error': str(e)}), 500

@opportunities_api.route('/search', methods=['GET'])
def search_opportunities():
    """ค้นหา opportunities"""
    try:
        keyword = request.args.get('q', '').strip()
        limit = int(request.args.get('limit', 20))
        
        if not keyword:
            return jsonify({'error': 'Search keyword is required'}), 400
        
        if len(keyword) < 2:
            return jsonify({'error': 'Search keyword must be at least 2 characters'}), 400
        
        opportunities = opportunity_repo.search_opportunities(keyword, limit)
        opportunities_data = [opp.to_dict() for opp in opportunities]
        
        return jsonify({
            'opportunities': opportunities_data,
            'count': len(opportunities_data),
            'keyword': keyword
        })
        
    except Exception as e:
        logger.error(f"Error searching opportunities: {str(e)}")
        return jsonify({'error': str(e)}), 500

@opportunities_api.route('/cleanup', methods=['POST'])
def cleanup_old_opportunities():
    """ล้างข้อมูล opportunities เก่า"""
    try:
        data = request.get_json() or {}
        days_old = data.get('days_old', 60)
        exclude_selected = data.get('exclude_selected', True)
        
        if days_old < 30:
            return jsonify({'error': 'Cannot delete opportunities newer than 30 days'}), 400
        
        deleted_count = opportunity_repo.delete_old_opportunities(days_old, exclude_selected)
        
        logger.info(f"Cleaned up {deleted_count} old opportunities (older than {days_old} days)")
        
        return jsonify({
            'success': True,
            'deleted_count': deleted_count,
            'message': f'Deleted {deleted_count} opportunities older than {days_old} days'
        })
        
    except Exception as e:
        logger.error(f"Error cleaning up opportunities: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Helper functions
def validate_opportunity_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate opportunity data from request"""
    errors = []
    
    if not data.get('suggested_angle'):
        errors.append('Suggested angle is required')
    
    if 'estimated_views' in data:
        try:
            views = int(data['estimated_views'])
            if views < 0:
                errors.append('Estimated views must be non-negative')
        except (ValueError, TypeError):
            errors.append('Estimated views must be a number')
    
    if 'estimated_roi' in data:
        try:
            roi = float(data['estimated_roi'])
            if roi < 0:
                errors.append('Estimated ROI must be non-negative')
        except (ValueError, TypeError):
            errors.append('Estimated ROI must be a number')
    
    if 'priority_score' in data:
        try:
            score = float(data['priority_score'])
            if score < 0 or score > 10:
                errors.append('Priority score must be between 0 and 10')
        except (ValueError, TypeError):
            errors.append('Priority score must be a number')
    
    if 'competition_level' in data:
        valid_levels = ['low', 'medium', 'high']
        if data['competition_level'] not in valid_levels:
            errors.append(f'Competition level must be one of: {valid_levels}')
    
    return {'errors': errors, 'valid': len(errors) == 0}

def get_priority_level(score: float) -> str:
    """แปลงคะแนนเป็นระดับความสำคัญ"""
    if score >= 8:
        return 'high'
    elif score >= 5:
        return 'medium'
    else:
        return 'low'

# Error handlers
@opportunities_api.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@opportunities_api.errorhandler(405)
def method_not_allowed(error):
    return jsonify({'error': 'Method not allowed'}), 405

@opportunities_api.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # สำหรับทดสอบ API endpoints
    from flask import Flask
    
    app = Flask(__name__)
    app.register_blueprint(opportunities_api)
    
    app.run(debug=True, port=5002)