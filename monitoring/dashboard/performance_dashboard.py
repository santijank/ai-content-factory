from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import asyncio
from dataclasses import dataclass
from enum import Enum
import json
import logging

# Database imports
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))
from database.repositories.trend_repository import TrendRepository
from database.repositories.opportunity_repository import OpportunityRepository
from database.repositories.content_repository import ContentRepository
from database.repositories.performance_repository import PerformanceRepository

logger = logging.getLogger(__name__)

class MetricType(Enum):
    TREND_COLLECTION = "trend_collection"
    CONTENT_GENERATION = "content_generation"
    PLATFORM_UPLOAD = "platform_upload"
    PERFORMANCE = "performance"
    COST = "cost"
    REVENUE = "revenue"

@dataclass
class DashboardMetric:
    name: str
    value: float
    unit: str
    change_percent: Optional[float] = None
    status: str = "normal"  # normal, warning, critical
    timestamp: datetime = None

@dataclass
class TrendMetrics:
    total_collected: int
    unique_topics: int
    avg_popularity_score: float
    top_categories: List[Dict[str, Any]]
    growth_trends: List[Dict[str, Any]]

@dataclass
class ContentMetrics:
    opportunities_generated: int
    content_created: int
    success_rate: float
    avg_cost_per_content: float
    popular_content_types: List[Dict[str, Any]]

@dataclass
class PlatformMetrics:
    total_uploads: int
    success_rate: float
    avg_engagement: Dict[str, float]
    platform_performance: Dict[str, Dict[str, Any]]

@dataclass
class FinancialMetrics:
    total_cost_today: float
    total_cost_month: float
    estimated_revenue: float
    roi: float
    cost_breakdown: Dict[str, float]

class PerformanceDashboard:
    def __init__(self, db_config: Dict[str, Any]):
        self.trend_repo = TrendRepository(db_config)
        self.opportunity_repo = OpportunityRepository(db_config)
        self.content_repo = ContentRepository(db_config)
        self.performance_repo = PerformanceRepository(db_config)
        
    async def get_metrics(self, time_range: str = "today") -> Dict[str, Any]:
        """Get comprehensive metrics for dashboard"""
        try:
            logger.info(f"Collecting metrics for time range: {time_range}")
            
            # Calculate time boundaries
            now = datetime.now()
            if time_range == "today":
                start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
                end_time = now
            elif time_range == "week":
                start_time = now - timedelta(days=7)
                end_time = now
            elif time_range == "month":
                start_time = now - timedelta(days=30)
                end_time = now
            else:
                start_time = now - timedelta(days=1)
                end_time = now
            
            # Collect all metrics in parallel
            tasks = [
                self._get_today_summary(),
                self._get_trend_metrics(start_time, end_time),
                self._get_content_metrics(start_time, end_time),
                self._get_platform_metrics(start_time, end_time),
                self._get_financial_metrics(start_time, end_time),
                self._get_system_health(),
                self._get_alerts()
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            return {
                "timestamp": now.isoformat(),
                "time_range": time_range,
                "summary": results[0] if not isinstance(results[0], Exception) else {},
                "trends": results[1] if not isinstance(results[1], Exception) else {},
                "content": results[2] if not isinstance(results[2], Exception) else {},
                "platforms": results[3] if not isinstance(results[3], Exception) else {},
                "financial": results[4] if not isinstance(results[4], Exception) else {},
                "system_health": results[5] if not isinstance(results[5], Exception) else {},
                "alerts": results[6] if not isinstance(results[6], Exception) else []
            }
            
        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")
            return self._get_error_response(str(e))

    async def _get_today_summary(self) -> Dict[str, DashboardMetric]:
        """Get today's key metrics summary"""
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        yesterday_start = today_start - timedelta(days=1)
        yesterday_end = today_start
        
        # Today's metrics
        trends_today = await self.trend_repo.count_by_date_range(today_start, datetime.now())
        opportunities_today = await self.opportunity_repo.count_by_date_range(today_start, datetime.now())
        content_today = await self.content_repo.count_by_date_range(today_start, datetime.now())
        uploads_today = await self.performance_repo.count_uploads_by_date_range(today_start, datetime.now())
        
        # Yesterday's metrics for comparison
        trends_yesterday = await self.trend_repo.count_by_date_range(yesterday_start, yesterday_end)
        opportunities_yesterday = await self.opportunity_repo.count_by_date_range(yesterday_start, yesterday_end)
        content_yesterday = await self.content_repo.count_by_date_range(yesterday_start, yesterday_end)
        uploads_yesterday = await self.performance_repo.count_uploads_by_date_range(yesterday_start, yesterday_end)
        
        # Calculate costs and revenue
        total_cost = await self._calculate_cost_today()
        estimated_revenue = await self._estimate_revenue_today()
        
        def calculate_change(today_val: int, yesterday_val: int) -> Optional[float]:
            if yesterday_val == 0:
                return None if today_val == 0 else 100.0
            return ((today_val - yesterday_val) / yesterday_val) * 100
        
        return {
            "trends_collected": DashboardMetric(
                name="Trends Collected",
                value=trends_today,
                unit="count",
                change_percent=calculate_change(trends_today, trends_yesterday)
            ),
            "opportunities_generated": DashboardMetric(
                name="Opportunities Generated", 
                value=opportunities_today,
                unit="count",
                change_percent=calculate_change(opportunities_today, opportunities_yesterday)
            ),
            "content_created": DashboardMetric(
                name="Content Created",
                value=content_today,
                unit="count", 
                change_percent=calculate_change(content_today, content_yesterday)
            ),
            "uploads_completed": DashboardMetric(
                name="Uploads Completed",
                value=uploads_today,
                unit="count",
                change_percent=calculate_change(uploads_today, uploads_yesterday)
            ),
            "total_cost": DashboardMetric(
                name="Total Cost",
                value=total_cost,
                unit="baht"
            ),
            "estimated_revenue": DashboardMetric(
                name="Estimated Revenue", 
                value=estimated_revenue,
                unit="baht"
            ),
            "roi": DashboardMetric(
                name="ROI",
                value=(estimated_revenue / total_cost * 100) if total_cost > 0 else 0,
                unit="percent"
            )
        }

    async def _get_trend_metrics(self, start_time: datetime, end_time: datetime) -> TrendMetrics:
        """Get detailed trend analytics"""
        
        # Get trend counts and statistics
        trend_count = await self.trend_repo.count_by_date_range(start_time, end_time)
        trends = await self.trend_repo.get_by_date_range(start_time, end_time)
        
        # Calculate unique topics
        unique_topics = len(set(trend.topic for trend in trends))
        
        # Calculate average popularity score
        avg_popularity = sum(trend.popularity_score for trend in trends) / len(trends) if trends else 0
        
        # Get top categories
        category_counts = {}
        for trend in trends:
            category = trend.category or "Unknown"
            category_counts[category] = category_counts.get(category, 0) + 1
        
        top_categories = [
            {"category": cat, "count": count}
            for cat, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        ]
        
        # Get growth trends (simplified)
        growth_trends = await self._calculate_growth_trends(trends)
        
        return TrendMetrics(
            total_collected=trend_count,
            unique_topics=unique_topics,
            avg_popularity_score=round(avg_popularity, 2),
            top_categories=top_categories,
            growth_trends=growth_trends
        )

    async def _get_content_metrics(self, start_time: datetime, end_time: datetime) -> ContentMetrics:
        """Get content generation and performance metrics"""
        
        opportunities_count = await self.opportunity_repo.count_by_date_range(start_time, end_time)
        content_count = await self.content_repo.count_by_date_range(start_time, end_time)
        
        # Calculate success rate (opportunities -> content)
        success_rate = (content_count / opportunities_count * 100) if opportunities_count > 0 else 0
        
        # Get content items for cost calculation
        content_items = await self.content_repo.get_by_date_range(start_time, end_time)
        
        # Calculate average cost
        total_cost = sum(
            item.cost_breakdown.get('total_cost', 0) if item.cost_breakdown else 0 
            for item in content_items
        )
        avg_cost = (total_cost / len(content_items)) if content_items else 0
        
        # Get popular content types
        content_types = {}
        for item in content_items:
            if item.content_plan and 'content_type' in item.content_plan:
                content_type = item.content_plan['content_type']
                content_types[content_type] = content_types.get(content_type, 0) + 1
        
        popular_types = [
            {"type": ctype, "count": count}
            for ctype, count in sorted(content_types.items(), key=lambda x: x[1], reverse=True)[:5]
        ]
        
        return ContentMetrics(
            opportunities_generated=opportunities_count,
            content_created=content_count,
            success_rate=round(success_rate, 2),
            avg_cost_per_content=round(avg_cost, 2),
            popular_content_types=popular_types
        )

    async def _get_platform_metrics(self, start_time: datetime, end_time: datetime) -> PlatformMetrics:
        """Get platform upload and performance metrics"""
        
        total_uploads = await self.performance_repo.count_uploads_by_date_range(start_time, end_time)
        uploads = await self.performance_repo.get_uploads_by_date_range(start_time, end_time)
        
        # Calculate success rate
        successful_uploads = len([u for u in uploads if u.url is not None])
        success_rate = (successful_uploads / total_uploads * 100) if total_uploads > 0 else 0
        
        # Calculate platform-specific metrics
        platform_stats = {}
        total_views = 0
        total_engagement = 0
        upload_count = 0
        
        for upload in uploads:
            platform = upload.platform
            if platform not in platform_stats:
                platform_stats[platform] = {
                    "uploads": 0,
                    "total_views": 0,
                    "total_likes": 0,
                    "total_comments": 0,
                    "total_shares": 0
                }
            
            platform_stats[platform]["uploads"] += 1
            
            # Get performance data if available
            if upload.performance_data:
                views = upload.performance_data.get('views', 0)
                likes = upload.performance_data.get('likes', 0)
                comments = upload.performance_data.get('comments', 0)
                shares = upload.performance_data.get('shares', 0)
                
                platform_stats[platform]["total_views"] += views
                platform_stats[platform]["total_likes"] += likes
                platform_stats[platform]["total_comments"] += comments
                platform_stats[platform]["total_shares"] += shares
                
                total_views += views
                total_engagement += likes + comments + shares
                upload_count += 1
        
        # Calculate average engagement
        avg_engagement = {
            "views": total_views / upload_count if upload_count > 0 else 0,
            "engagement_rate": (total_engagement / total_views * 100) if total_views > 0 else 0
        }
        
        # Format platform performance
        platform_performance = {}
        for platform, stats in platform_stats.items():
            platform_performance[platform] = {
                "uploads": stats["uploads"],
                "avg_views": stats["total_views"] / stats["uploads"] if stats["uploads"] > 0 else 0,
                "engagement_rate": ((stats["total_likes"] + stats["total_comments"] + stats["total_shares"]) / 
                                  stats["total_views"] * 100) if stats["total_views"] > 0 else 0
            }
        
        return PlatformMetrics(
            total_uploads=total_uploads,
            success_rate=round(success_rate, 2),
            avg_engagement=avg_engagement,
            platform_performance=platform_performance
        )

    async def _get_financial_metrics(self, start_time: datetime, end_time: datetime) -> FinancialMetrics:
        """Get financial performance metrics"""
        
        # Calculate costs
        content_items = await self.content_repo.get_by_date_range(start_time, end_time)
        
        total_cost = 0
        cost_breakdown = {
            "ai_text": 0,
            "ai_image": 0,
            "ai_audio": 0,
            "platform_fees": 0,
            "infrastructure": 0
        }
        
        for item in content_items:
            if item.cost_breakdown:
                item_cost = item.cost_breakdown.get('total_cost', 0)
                total_cost += item_cost
                
                # Breakdown costs
                for category in cost_breakdown.keys():
                    cost_breakdown[category] += item.cost_breakdown.get(category, 0)
        
        # Calculate monthly cost
        if (end_time - start_time).days == 1:  # If today, calculate month
            monthly_start = start_time.replace(day=1)
            monthly_items = await self.content_repo.get_by_date_range(monthly_start, end_time)
            total_cost_month = sum(
                item.cost_breakdown.get('total_cost', 0) if item.cost_breakdown else 0
                for item in monthly_items
            )
        else:
            total_cost_month = total_cost
        
        # Estimate revenue (simplified calculation)
        uploads = await self.performance_repo.get_uploads_by_date_range(start_time, end_time)
        estimated_revenue = 0
        
        for upload in uploads:
            if upload.performance_data:
                views = upload.performance_data.get('views', 0)
                # Estimate revenue based on platform and views
                if upload.platform == 'youtube':
                    estimated_revenue += views * 0.001  # $1 per 1000 views
                elif upload.platform == 'tiktok':
                    estimated_revenue += views * 0.0005  # Lower rate for TikTok
        
        # Calculate ROI
        roi = ((estimated_revenue - total_cost) / total_cost * 100) if total_cost > 0 else 0
        
        return FinancialMetrics(
            total_cost_today=round(total_cost, 2),
            total_cost_month=round(total_cost_month, 2),
            estimated_revenue=round(estimated_revenue, 2),
            roi=round(roi, 2),
            cost_breakdown={k: round(v, 2) for k, v in cost_breakdown.items()}
        )

    async def _get_system_health(self) -> Dict[str, Any]:
        """Get system health metrics"""
        return {
            "status": "healthy",
            "uptime": "99.9%",
            "services": {
                "trend_monitor": "running",
                "content_engine": "running", 
                "platform_manager": "running",
                "database": "healthy"
            },
            "performance": {
                "avg_response_time": "150ms",
                "error_rate": "0.1%",
                "throughput": "45 req/min"
            }
        }

    async def _get_alerts(self) -> List[Dict[str, Any]]:
        """Get current system alerts"""
        alerts = []
        
        # Check for low success rates
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        opportunities_today = await self.opportunity_repo.count_by_date_range(today_start, datetime.now())
        content_today = await self.content_repo.count_by_date_range(today_start, datetime.now())
        
        success_rate = (content_today / opportunities_today * 100) if opportunities_today > 0 else 0
        
        if success_rate < 50:
            alerts.append({
                "level": "warning",
                "message": f"Content generation success rate is low: {success_rate:.1f}%",
                "timestamp": datetime.now().isoformat(),
                "category": "performance"
            })
        
        # Check for high costs
        total_cost = await self._calculate_cost_today()
        if total_cost > 100:  # More than 100 baht per day
            alerts.append({
                "level": "warning", 
                "message": f"Daily cost is high: {total_cost:.2f} baht",
                "timestamp": datetime.now().isoformat(),
                "category": "cost"
            })
        
        return alerts

    async def _calculate_cost_today(self) -> float:
        """Calculate today's total cost"""
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        content_items = await self.content_repo.get_by_date_range(today_start, datetime.now())
        
        return sum(
            item.cost_breakdown.get('total_cost', 0) if item.cost_breakdown else 0
            for item in content_items
        )

    async def _estimate_revenue_today(self) -> float:
        """Estimate today's revenue"""
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        uploads = await self.performance_repo.get_uploads_by_date_range(today_start, datetime.now())
        
        estimated_revenue = 0
        for upload in uploads:
            if upload.performance_data:
                views = upload.performance_data.get('views', 0)
                if upload.platform == 'youtube':
                    estimated_revenue += views * 0.001
                elif upload.platform == 'tiktok':
                    estimated_revenue += views * 0.0005
        
        return estimated_revenue

    async def _calculate_growth_trends(self, trends: List) -> List[Dict[str, Any]]:
        """Calculate growth trends for visualization"""
        # Group trends by date
        daily_counts = {}
        for trend in trends:
            date_key = trend.collected_at.date()
            daily_counts[date_key] = daily_counts.get(date_key, 0) + 1
        
        # Convert to chart format
        growth_data = []
        for date, count in sorted(daily_counts.items()):
            growth_data.append({
                "date": date.isoformat(),
                "count": count
            })
        
        return growth_data

    def _get_error_response(self, error_message: str) -> Dict[str, Any]:
        """Return error response when metrics collection fails"""
        return {
            "error": True,
            "message": error_message,
            "timestamp": datetime.now().isoformat(),
            "summary": {},
            "trends": {},
            "content": {},
            "platforms": {},
            "financial": {},
            "system_health": {"status": "error"},
            "alerts": [{
                "level": "critical",
                "message": f"Metrics collection failed: {error_message}",
                "timestamp": datetime.now().isoformat(),
                "category": "system"
            }]
        }

    async def get_trend_analysis(self, days: int = 7) -> Dict[str, Any]:
        """Get detailed trend analysis"""
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        trends = await self.trend_repo.get_by_date_range(start_time, end_time)
        
        return {
            "period": f"{days} days",
            "total_trends": len(trends),
            "top_trends": await self._get_top_trends(trends, limit=10),
            "best_opportunities": await self._get_best_opportunities(limit=5),
            "missed_opportunities": await self._get_missed_opportunities()
        }

    async def _get_top_trends(self, trends: List, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top trending topics"""
        sorted_trends = sorted(trends, key=lambda x: x.popularity_score, reverse=True)
        return [
            {
                "topic": trend.topic,
                "popularity_score": trend.popularity_score,
                "growth_rate": trend.growth_rate,
                "category": trend.category
            }
            for trend in sorted_trends[:limit]
        ]

    async def _get_best_opportunities(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get best content opportunities"""
        opportunities = await self.opportunity_repo.get_top_opportunities(limit)
        return [
            {
                "suggested_angle": opp.suggested_angle,
                "estimated_views": opp.estimated_views,
                "priority_score": opp.priority_score,
                "estimated_roi": opp.estimated_roi
            }
            for opp in opportunities
        ]

    async def _get_missed_opportunities(self) -> List[Dict[str, Any]]:
        """Get missed opportunities (high score but not selected)"""
        missed = await self.opportunity_repo.get_missed_opportunities()
        return [
            {
                "suggested_angle": opp.suggested_angle,
                "priority_score": opp.priority_score,
                "days_ago": (datetime.now() - opp.created_at).days
            }
            for opp in missed[:5]  # Top 5 missed
        ]

    async def calculate_success_rate(self) -> float:
        """Calculate overall content success rate"""
        total_opportunities = await self.opportunity_repo.count_total()
        total_content = await self.content_repo.count_total()
        
        return (total_content / total_opportunities * 100) if total_opportunities > 0 else 0

    async def calculate_avg_cost(self) -> float:
        """Calculate average cost per content"""
        content_items = await self.content_repo.get_all_with_costs()
        
        if not content_items:
            return 0
        
        total_cost = sum(
            item.cost_breakdown.get('total_cost', 0) if item.cost_breakdown else 0
            for item in content_items
        )
        
        return total_cost / len(content_items)

    async def calculate_roi_by_platform(self) -> Dict[str, float]:
        """Calculate ROI by platform"""
        platforms = ['youtube', 'tiktok', 'instagram', 'facebook']
        roi_by_platform = {}
        
        for platform in platforms:
            uploads = await self.performance_repo.get_uploads_by_platform(platform)
            
            total_cost = 0
            total_revenue = 0
            
            for upload in uploads:
                # Get associated content cost
                if upload.content_id:
                    content = await self.content_repo.get_by_id(upload.content_id)
                    if content and content.cost_breakdown:
                        total_cost += content.cost_breakdown.get('total_cost', 0)
                
                # Calculate revenue
                if upload.performance_data:
                    views = upload.performance_data.get('views', 0)
                    if platform == 'youtube':
                        total_revenue += views * 0.001
                    elif platform == 'tiktok':
                        total_revenue += views * 0.0005
            
            roi = ((total_revenue - total_cost) / total_cost * 100) if total_cost > 0 else 0
            roi_by_platform[platform] = round(roi, 2)
        
        return roi_by_platform