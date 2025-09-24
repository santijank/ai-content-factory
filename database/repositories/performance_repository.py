"""
Performance Repository
Handles performance metrics and analytics data
"""

import logging
from datetime import datetime, date
from typing import Dict, Any, List, Optional
from sqlalchemy import func, and_, desc, asc, extract
from sqlalchemy.orm import sessionmaker

from database.models.base import get_db_session
from database.models.performance_metrics import PerformanceMetrics
from database.models.uploads import Uploads
from database.models.content_items import ContentItems

logger = logging.getLogger(__name__)

class PerformanceRepository:
    """Repository for performance metrics and analytics"""
    
    def __init__(self):
        self.Session = sessionmaker(bind=get_db_session().bind)
    
    def get_aggregated_metrics(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """Get aggregated performance metrics for a date range"""
        try:
            with self.Session() as session:
                result = session.query(
                    func.sum(PerformanceMetrics.views).label('total_views'),
                    func.sum(PerformanceMetrics.likes + PerformanceMetrics.comments + PerformanceMetrics.shares).label('total_engagement'),
                    func.avg(PerformanceMetrics.revenue / PerformanceMetrics.cost).label('average_roi'),
                    func.sum(PerformanceMetrics.cost).label('total_cost'),
                    func.sum(PerformanceMetrics.revenue).label('total_revenue'),
                    func.count(PerformanceMetrics.id).label('total_content')
                ).filter(
                    and_(
                        PerformanceMetrics.measured_at >= start_date,
                        PerformanceMetrics.measured_at <= end_date
                    )
                ).first()
                
                return {
                    'total_views': result.total_views or 0,
                    'total_engagement': result.total_engagement or 0,
                    'average_roi': float(result.average_roi or 0),
                    'total_cost': float(result.total_cost or 0),
                    'total_revenue': float(result.total_revenue or 0),
                    'total_content': result.total_content or 0
                }
                
        except Exception as e:
            logger.error(f"Error getting aggregated metrics: {e}")
            return {
                'total_views': 0,
                'total_engagement': 0,
                'average_roi': 0.0,
                'total_cost': 0.0,
                'total_revenue': 0.0,
                'total_content': 0
            }
    
    def get_daily_metrics(self, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """Get daily performance metrics for a date range"""
        try:
            with self.Session() as session:
                results = session.query(
                    func.date(PerformanceMetrics.measured_at).label('date'),
                    func.sum(PerformanceMetrics.views).label('total_views'),
                    func.sum(PerformanceMetrics.likes + PerformanceMetrics.comments + PerformanceMetrics.shares).label('total_engagement'),
                    func.count(PerformanceMetrics.id).label('content_count'),
                    func.sum(PerformanceMetrics.cost).label('total_cost'),
                    func.sum(PerformanceMetrics.revenue).label('total_revenue')
                ).filter(
                    and_(
                        PerformanceMetrics.measured_at >= start_date,
                        PerformanceMetrics.measured_at <= end_date
                    )
                ).group_by(
                    func.date(PerformanceMetrics.measured_at)
                ).order_by(
                    func.date(PerformanceMetrics.measured_at)
                ).all()
                
                daily_metrics = []
                for result in results:
                    daily_metrics.append({
                        'date': result.date,
                        'total_views': result.total_views or 0,
                        'total_engagement': result.total_engagement or 0,
                        'content_count': result.content_count or 0,
                        'total_cost': float(result.total_cost or 0),
                        'total_revenue': float(result.total_revenue or 0)
                    })
                
                return daily_metrics
                
        except Exception as e:
            logger.error(f"Error getting daily metrics: {e}")
            return []
    
    def get_platform_metrics(self, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """Get performance metrics grouped by platform"""
        try:
            with self.Session() as session:
                results = session.query(
                    Uploads.platform,
                    func.sum(PerformanceMetrics.views).label('total_views'),
                    func.sum(PerformanceMetrics.likes + PerformanceMetrics.comments + PerformanceMetrics.shares).label('total_engagement'),
                    func.avg((PerformanceMetrics.likes + PerformanceMetrics.comments + PerformanceMetrics.shares) * 100.0 / PerformanceMetrics.views).label('engagement_rate'),
                    func.count(PerformanceMetrics.id).label('content_count'),
                    func.avg(PerformanceMetrics.revenue / PerformanceMetrics.cost).label('average_roi')
                ).join(
                    Uploads, PerformanceMetrics.upload_id == Uploads.id
                ).filter(
                    and_(
                        PerformanceMetrics.measured_at >= start_date,
                        PerformanceMetrics.measured_at <= end_date
                    )
                ).group_by(
                    Uploads.platform
                ).all()
                
                platform_metrics = []
                for result in results:
                    platform_metrics.append({
                        'platform': result.platform,
                        'total_views': result.total_views or 0,
                        'total_engagement': result.total_engagement or 0,
                        'engagement_rate': float(result.engagement_rate or 0),
                        'content_count': result.content_count or 0,
                        'average_roi': float(result.average_roi or 0)
                    })
                
                return platform_metrics
                
        except Exception as e:
            logger.error(f"Error getting platform metrics: {e}")
            return []
    
    def get_content_performance(self, start_date: date, end_date: date, limit: int = 20, sort_by: str = 'views') -> List[Dict[str, Any]]:
        """Get individual content performance"""
        try:
            with self.Session() as session:
                # Define sort column
                sort_columns = {
                    'views': desc(PerformanceMetrics.views),
                    'engagement': desc(PerformanceMetrics.likes + PerformanceMetrics.comments + PerformanceMetrics.shares),
                    'roi': desc(PerformanceMetrics.revenue / PerformanceMetrics.cost),
                    'date': desc(PerformanceMetrics.measured_at)
                }
                
                sort_column = sort_columns.get(sort_by, desc(PerformanceMetrics.views))
                
                results = session.query(
                    PerformanceMetrics,
                    ContentItems.title,
                    ContentItems.description,
                    Uploads.platform,
                    Uploads.uploaded_at
                ).join(
                    Uploads, PerformanceMetrics.upload_id == Uploads.id
                ).join(
                    ContentItems, Uploads.content_id == ContentItems.id
                ).filter(
                    and_(
                        PerformanceMetrics.measured_at >= start_date,
                        PerformanceMetrics.measured_at <= end_date
                    )
                ).order_by(sort_column).limit(limit).all()
                
                content_performance = []
                for result in results:
                    metrics, title, description, platform, uploaded_at = result
                    
                    total_engagement = (metrics.likes or 0) + (metrics.comments or 0) + (metrics.shares or 0)
                    engagement_rate = (total_engagement * 100.0 / metrics.views) if metrics.views > 0 else 0
                    roi = (metrics.revenue / metrics.cost) if metrics.cost > 0 else 0
                    
                    content_performance.append({
                        'content_id': metrics.upload_id,
                        'title': title or 'Untitled',
                        'platform': platform or 'Unknown',
                        'category': 'General',  # Would need to add category to ContentItems model
                        'views': metrics.views or 0,
                        'likes': metrics.likes or 0,
                        'comments': metrics.comments or 0,
                        'shares': metrics.shares or 0,
                        'engagement_rate': engagement_rate,
                        'roi': roi,
                        'cost': float(metrics.cost or 0),
                        'revenue': float(metrics.revenue or 0),
                        'published_at': uploaded_at or metrics.measured_at
                    })
                
                return content_performance
                
        except Exception as e:
            logger.error(f"Error getting content performance: {e}")
            return []
    
    def get_category_metrics(self, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """Get performance metrics by content category"""
        try:
            with self.Session() as session:
                # This assumes ContentItems has a category field
                # If not, we'd need to add it to the model
                results = session.query(
                    func.coalesce(ContentItems.category, 'General').label('category'),
                    func.count(PerformanceMetrics.id).label('content_count'),
                    func.avg(PerformanceMetrics.views).label('avg_views'),
                    func.avg(PerformanceMetrics.likes + PerformanceMetrics.comments + PerformanceMetrics.shares).label('avg_engagement'),
                    func.avg(PerformanceMetrics.revenue / PerformanceMetrics.cost).label('avg_roi'),
                    func.sum(PerformanceMetrics.cost).label('total_cost')
                ).join(
                    Uploads, PerformanceMetrics.upload_id == Uploads.id
                ).join(
                    ContentItems, Uploads.content_id == ContentItems.id
                ).filter(
                    and_(
                        PerformanceMetrics.measured_at >= start_date,
                        PerformanceMetrics.measured_at <= end_date
                    )
                ).group_by(
                    func.coalesce(ContentItems.category, 'General')
                ).all()
                
                category_metrics = []
                for result in results:
                    category_metrics.append({
                        'category': result.category,
                        'content_count': result.content_count or 0,
                        'avg_views': float(result.avg_views or 0),
                        'avg_engagement': float(result.avg_engagement or 0),
                        'avg_roi': float(result.avg_roi or 0),
                        'total_cost': float(result.total_cost or 0)
                    })
                
                return category_metrics
                
        except Exception as e:
            logger.error(f"Error getting category metrics: {e}")
            return []
    
    def get_hourly_success_rate(self, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """Get success rate by hour of day"""
        try:
            with self.Session() as session:
                results = session.query(
                    extract('hour', Uploads.uploaded_at).label('hour'),
                    func.avg(
                        func.case(
                            [(PerformanceMetrics.views > 1000, 100)],
                            else_=0
                        )
                    ).label('success_rate')
                ).join(
                    Uploads, PerformanceMetrics.upload_id == Uploads.id
                ).filter(
                    and_(
                        PerformanceMetrics.measured_at >= start_date,
                        PerformanceMetrics.measured_at <= end_date
                    )
                ).group_by(
                    extract('hour', Uploads.uploaded_at)
                ).all()
                
                hourly_success = []
                for result in results:
                    hourly_success.append({
                        'hour': int(result.hour),
                        'success_rate': float(result.success_rate or 0)
                    })
                
                return hourly_success
                
        except Exception as e:
            logger.error(f"Error getting hourly success rate: {e}")
            return []
    
    def get_best_posting_hours(self, start_date: date, end_date: date, limit: int = 3) -> List[int]:
        """Get the best hours for posting content"""
        try:
            with self.Session() as session:
                results = session.query(
                    extract('hour', Uploads.uploaded_at).label('hour'),
                    func.avg(PerformanceMetrics.views).label('avg_views')
                ).join(
                    Uploads, PerformanceMetrics.upload_id == Uploads.id
                ).filter(
                    and_(
                        PerformanceMetrics.measured_at >= start_date,
                        PerformanceMetrics.measured_at <= end_date
                    )
                ).group_by(
                    extract('hour', Uploads.uploaded_at)
                ).order_by(
                    desc('avg_views')
                ).limit(limit).all()
                
                return [int(result.hour) for result in results]
                
        except Exception as e:
            logger.error(f"Error getting best posting hours: {e}")
            return [12, 18, 20]  # Default hours
    
    def get_platform_roi(self, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """Get ROI by platform"""
        try:
            with self.Session() as session:
                results = session.query(
                    Uploads.platform,
                    func.avg(PerformanceMetrics.revenue / PerformanceMetrics.cost).label('roi'),
                    func.sum(PerformanceMetrics.revenue).label('total_revenue'),
                    func.sum(PerformanceMetrics.cost).label('total_cost')
                ).join(
                    Uploads, PerformanceMetrics.upload_id == Uploads.id
                ).filter(
                    and_(
                        PerformanceMetrics.measured_at >= start_date,
                        PerformanceMetrics.measured_at <= end_date,
                        PerformanceMetrics.cost > 0
                    )
                ).group_by(
                    Uploads.platform
                ).all()
                
                platform_roi = []
                for result in results:
                    platform_roi.append({
                        'platform': result.platform,
                        'roi': float(result.roi or 0),
                        'total_revenue': float(result.total_revenue or 0),
                        'total_cost': float(result.total_cost or 0)
                    })
                
                return platform_roi
                
        except Exception as e:
            logger.error(f"Error getting platform ROI: {e}")
            return []
    
    def get_category_performance(self, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """Get performance by category for recommendations"""
        try:
            with self.Session() as session:
                results = session.query(
                    func.coalesce(ContentItems.category, 'General').label('category'),
                    func.avg(PerformanceMetrics.views).label('avg_views'),
                    func.avg(PerformanceMetrics.likes + PerformanceMetrics.comments + PerformanceMetrics.shares).label('avg_engagement'),
                    func.count(PerformanceMetrics.id).label('content_count')
                ).join(
                    Uploads, PerformanceMetrics.upload_id == Uploads.id
                ).join(
                    ContentItems, Uploads.content_id == ContentItems.id
                ).filter(
                    and_(
                        PerformanceMetrics.measured_at >= start_date,
                        PerformanceMetrics.measured_at <= end_date
                    )
                ).group_by(
                    func.coalesce(ContentItems.category, 'General')
                ).having(
                    func.count(PerformanceMetrics.id) >= 3  # At least 3 pieces of content
                ).all()
                
                category_performance = []
                for result in results:
                    category_performance.append({
                        'category': result.category,
                        'avg_views': float(result.avg_views or 0),
                        'avg_engagement': float(result.avg_engagement or 0),
                        'content_count': result.content_count or 0
                    })
                
                return category_performance
                
        except Exception as e:
            logger.error(f"Error getting category performance: {e}")
            return []
    
    def create_performance_metric(self, metric_data: Dict[str, Any]) -> Optional[PerformanceMetrics]:
        """Create a new performance metric record"""
        try:
            with self.Session() as session:
                metric = PerformanceMetrics(
                    upload_id=metric_data['upload_id'],
                    views=metric_data.get('views', 0),
                    likes=metric_data.get('likes', 0),
                    comments=metric_data.get('comments', 0),
                    shares=metric_data.get('shares', 0),
                    revenue=metric_data.get('revenue', 0.0),
                    cost=metric_data.get('cost', 0.0),
                    measured_at=metric_data.get('measured_at', datetime.now())
                )
                
                session.add(metric)
                session.commit()
                session.refresh(metric)
                
                logger.info(f"Created performance metric for upload {metric.upload_id}")
                return metric
                
        except Exception as e:
            logger.error(f"Error creating performance metric: {e}")
            return None
    
    def update_performance_metric(self, upload_id: str, updates: Dict[str, Any]) -> bool:
        """Update performance metrics for an upload"""
        try:
            with self.Session() as session:
                metric = session.query(PerformanceMetrics).filter_by(upload_id=upload_id).first()
                
                if not metric:
                    # Create new metric if doesn't exist
                    updates['upload_id'] = upload_id
                    self.create_performance_metric(updates)
                    return True
                
                # Update existing metric
                for key, value in updates.items():
                    if hasattr(metric, key):
                        setattr(metric, key, value)
                
                metric.measured_at = datetime.now()
                session.commit()
                
                logger.info(f"Updated performance metric for upload {upload_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error updating performance metric: {e}")
            return False
    
    def get_performance_by_upload(self, upload_id: str) -> Optional[PerformanceMetrics]:
        """Get performance metrics for a specific upload"""
        try:
            with self.Session() as session:
                return session.query(PerformanceMetrics).filter_by(upload_id=upload_id).first()
                
        except Exception as e:
            logger.error(f"Error getting performance for upload {upload_id}: {e}")
            return None
    
    def delete_performance_metrics(self, upload_id: str) -> bool:
        """Delete performance metrics for an upload"""
        try:
            with self.Session() as session:
                deleted_count = session.query(PerformanceMetrics).filter_by(upload_id=upload_id).delete()
                session.commit()
                
                logger.info(f"Deleted {deleted_count} performance metrics for upload {upload_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error deleting performance metrics: {e}")
            return False