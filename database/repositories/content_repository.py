"""
Content Repository - จัดการข้อมูล Content Items
ตำแหน่งไฟล์: database/repositories/content_repository.py
"""
import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from database.models.base import BaseRepository, BaseModel

class ContentItem(BaseModel):
    """Model สำหรับ Content Item data"""
    
    def __init__(self):
        super().__init__()
        self.opportunity_id = None
        self.title = None
        self.description = None
        self.content_plan = {}
        self.production_status = 'pending'  # pending, generating, completed, failed, uploaded
        self.assets = {}  # links to generated files
        self.cost_breakdown = {}
        self.quality_tier = 'budget'  # budget, balanced, premium
        self.target_platforms = []
        self.completed_at = None
        self.opportunity = None  # จะถูก populate ในบาง methods
        self.uploads = []  # upload records

class ContentRepository(BaseRepository):
    """Repository สำหรับจัดการ Content Items"""
    
    def create_content_item(self, content_data: ContentItem) -> str:
        """สร้าง content item ใหม่"""
        content_id = self.generate_id()
        
        query = """
            SELECT 
                u.platform,
                COUNT(DISTINCT c.id) as total_content,
                COUNT(DISTINCT CASE WHEN u.upload_status = 'completed' THEN c.id END) as successful_uploads,
                AVG(pm.views) as avg_views,
                AVG(pm.likes) as avg_likes,
                AVG(pm.comments) as avg_comments,
                AVG(pm.shares) as avg_shares,
                SUM(pm.revenue) as total_revenue
            FROM content_items c
            LEFT JOIN uploads u ON c.id = u.content_id
            LEFT JOIN performance_metrics pm ON u.id = pm.upload_id
            GROUP BY u.platform
            ORDER BY total_content DESC
        """
        
        results = self.execute_query(query, fetch=True)
        
        performance = {}
        for row in results:
            if not row['platform']:
                continue
                
            platform = row['platform']
            total = row['total_content'] or 0
            successful = row['successful_uploads'] or 0
            
            performance[platform] = {
                'total_content': total,
                'successful_uploads': successful,
                'success_rate': (successful / total * 100) if total > 0 else 0,
                'avg_views': int(row['avg_views']) if row['avg_views'] else 0,
                'avg_likes': int(row['avg_likes']) if row['avg_likes'] else 0,
                'avg_comments': int(row['avg_comments']) if row['avg_comments'] else 0,
                'avg_shares': int(row['avg_shares']) if row['avg_shares'] else 0,
                'total_revenue': float(row['total_revenue']) if row['total_revenue'] else 0.0
            }
        
        return performance
    
    def get_success_metrics(self) -> Dict[str, Any]:
        """ดึงข้อมูลความสำเร็จโดยรวม"""
        query = """
            SELECT 
                COUNT(*) as total_content,
                SUM(CASE WHEN production_status = 'completed' THEN 1 ELSE 0 END) as completed_content,
                SUM(CASE WHEN production_status = 'failed' THEN 1 ELSE 0 END) as failed_content,
                AVG(CASE WHEN completed_at IS NOT NULL 
                    THEN (julianday(completed_at) - julianday(created_at)) * 24 
                    ELSE NULL END) as avg_production_hours
            FROM content_items
        """
        
        results = self.execute_query(query, fetch=True)
        
        if results:
            row = results[0]
            total = row['total_content'] or 0
            completed = row['completed_content'] or 0
            failed = row['failed_content'] or 0
            
            return {
                'total_content': total,
                'completed_content': completed,
                'failed_content': failed,
                'in_progress': total - completed - failed,
                'success_rate': (completed / total * 100) if total > 0 else 0,
                'failure_rate': (failed / total * 100) if total > 0 else 0,
                'avg_production_hours': float(row['avg_production_hours']) if row['avg_production_hours'] else 0
            }
        
        return {
            'total_content': 0,
            'completed_content': 0,
            'failed_content': 0,
            'in_progress': 0,
            'success_rate': 0,
            'failure_rate': 0,
            'avg_production_hours': 0
        }
    
    def update_content_status(self, content_id: str, status: str, 
                            assets: Dict[str, Any] = None) -> bool:
        """อัปเดต status ของ content"""
        query = """
            UPDATE content_items 
            SET production_status = ?, updated_at = ?
        """
        params = [status, datetime.now()]
        
        if status == 'completed':
            query += ", completed_at = ?"
            params.append(datetime.now())
        
        if assets:
            query += ", assets = ?"
            params.append(json.dumps(assets))
        
        query += " WHERE id = ?"
        params.append(content_id)
        
        try:
            rows_affected = self.execute_query(query, tuple(params))
            return rows_affected > 0
        except Exception as e:
            print(f"Error updating content status: {str(e)}")
            return False
    
    def update_content_plan(self, content_id: str, content_plan: Dict[str, Any]) -> bool:
        """อัปเดต content plan"""
        query = """
            UPDATE content_items 
            SET content_plan = ?, updated_at = ?
            WHERE id = ?
        """
        
        try:
            rows_affected = self.execute_query(query, (
                json.dumps(content_plan),
                datetime.now(),
                content_id
            ))
            return rows_affected > 0
        except Exception as e:
            print(f"Error updating content plan: {str(e)}")
            return False
    
    def search_content(self, keyword: str, limit: int = 20) -> List[ContentItem]:
        """ค้นหา content ตาม keyword"""
        query = """
            SELECT c.*, o.suggested_angle as opp_angle, o.estimated_roi as opp_roi,
                   t.topic as trend_topic, t.source as trend_source
            FROM content_items c
            LEFT JOIN content_opportunities o ON c.opportunity_id = o.id
            LEFT JOIN trends t ON o.trend_id = t.id
            WHERE c.title LIKE ? OR c.description LIKE ? OR o.suggested_angle LIKE ?
            ORDER BY c.created_at DESC
            LIMIT ?
        """
        search_term = f"%{keyword}%"
        results = self.execute_query(query, (search_term, search_term, search_term, limit), fetch=True)
        return [self._row_to_content(row, include_opportunity=True) for row in results]
    
    def get_content_by_opportunity(self, opportunity_id: str) -> List[ContentItem]:
        """ดึง content ของ opportunity นั้นๆ"""
        query = """
            SELECT c.*, o.suggested_angle as opp_angle, o.estimated_roi as opp_roi,
                   t.topic as trend_topic, t.source as trend_source
            FROM content_items c
            LEFT JOIN content_opportunities o ON c.opportunity_id = o.id
            LEFT JOIN trends t ON o.trend_id = t.id
            WHERE c.opportunity_id = ?
            ORDER BY c.created_at DESC
        """
        
        results = self.execute_query(query, (opportunity_id,), fetch=True)
        return [self._row_to_content(row, include_opportunity=True) for row in results]
    
    def get_content_by_quality_tier(self, quality_tier: str) -> List[ContentItem]:
        """ดึง content ตาม quality tier"""
        query = """
            SELECT c.*, o.suggested_angle as opp_angle, o.estimated_roi as opp_roi,
                   t.topic as trend_topic, t.source as trend_source
            FROM content_items c
            LEFT JOIN content_opportunities o ON c.opportunity_id = o.id
            LEFT JOIN trends t ON o.trend_id = t.id
            WHERE c.quality_tier = ?
            ORDER BY c.created_at DESC
        """
        
        results = self.execute_query(query, (quality_tier,), fetch=True)
        return [self._row_to_content(row, include_opportunity=True) for row in results]
    
    def get_recent_completed_content(self, days_back: int = 7, limit: int = 10) -> List[ContentItem]:
        """ดึง content ที่เสร็จล่าสุด"""
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        query = """
            SELECT c.*, o.suggested_angle as opp_angle, o.estimated_roi as opp_roi,
                   t.topic as trend_topic, t.source as trend_source
            FROM content_items c
            LEFT JOIN content_opportunities o ON c.opportunity_id = o.id
            LEFT JOIN trends t ON o.trend_id = t.id
            WHERE c.production_status = 'completed' 
            AND c.completed_at >= ?
            ORDER BY c.completed_at DESC
            LIMIT ?
        """
        
        results = self.execute_query(query, (cutoff_date, limit), fetch=True)
        return [self._row_to_content(row, include_opportunity=True) for row in results]
    
    def delete_failed_content(self, days_old: int = 7) -> int:
        """ลบ content ที่ failed และเก่าแล้ว"""
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        query = """
            DELETE FROM content_items 
            WHERE production_status = 'failed' 
            AND created_at < ?
        """
        
        return self.execute_query(query, (cutoff_date,))
    
    def get_status_distribution(self) -> Dict[str, int]:
        """นับจำนวนตาม production status"""
        query = """
            SELECT production_status, COUNT(*) as count 
            FROM content_items 
            GROUP BY production_status 
            ORDER BY count DESC
        """
        results = self.execute_query(query, fetch=True)
        return {row['production_status']: row['count'] for row in results}
    
    def get_quality_tier_distribution(self) -> Dict[str, int]:
        """นับจำนวนตาม quality tier"""
        query = """
            SELECT quality_tier, COUNT(*) as count 
            FROM content_items 
            GROUP BY quality_tier 
            ORDER BY count DESC
        """
        results = self.execute_query(query, fetch=True)
        return {row['quality_tier']: row['count'] for row in results}
    
    def _get_uploads_for_content(self, content_id: str) -> List[Dict[str, Any]]:
        """ดึงข้อมูล uploads ของ content"""
        query = """
            SELECT u.*, 
                   AVG(pm.views) as avg_views,
                   AVG(pm.likes) as avg_likes,
                   SUM(pm.revenue) as total_revenue
            FROM uploads u
            LEFT JOIN performance_metrics pm ON u.id = pm.upload_id
            WHERE u.content_id = ?
            GROUP BY u.id
            ORDER BY u.uploaded_at DESC
        """
        
        results = self.execute_query(query, (content_id,), fetch=True)
        
        uploads = []
        for row in results:
            upload = {
                'id': row['id'],
                'platform': row['platform'],
                'platform_id': row['platform_id'],
                'url': row['url'],
                'upload_status': row['upload_status'],
                'uploaded_at': row['uploaded_at'],
                'metadata': json.loads(row['metadata']) if row['metadata'] else {},
                'performance': {
                    'views': int(row['avg_views']) if row['avg_views'] else 0,
                    'likes': int(row['avg_likes']) if row['avg_likes'] else 0,
                    'revenue': float(row['total_revenue']) if row['total_revenue'] else 0.0
                }
            }
            uploads.append(upload)
        
        return uploads
    
    def _row_to_content(self, row: Dict[str, Any], include_opportunity: bool = False) -> ContentItem:
        """แปลง database row เป็น ContentItem object"""
        content = ContentItem()
        content.id = row['id']
        content.opportunity_id = row['opportunity_id']
        content.title = row['title']
        content.description = row['description']
        content.content_plan = json.loads(row['content_plan']) if row['content_plan'] else {}
        content.production_status = row['production_status']
        content.assets = json.loads(row['assets']) if row['assets'] else {}
        content.cost_breakdown = json.loads(row['cost_breakdown']) if row['cost_breakdown'] else {}
        content.quality_tier = row['quality_tier']
        content.target_platforms = json.loads(row['target_platforms']) if row['target_platforms'] else []
        content.created_at = row['created_at']
        content.completed_at = row['completed_at']
        content.updated_at = row['updated_at']
        
        # Add opportunity information if available
        if include_opportunity and 'opp_angle' in row:
            content.opportunity = {
                'suggested_angle': row['opp_angle'],
                'estimated_roi': float(row['opp_roi']) if row['opp_roi'] else 0.0,
                'trend': {
                    'topic': row['trend_topic'],
                    'source': row['trend_source']
                } if 'trend_topic' in row else None
            }
        
        return content
            INSERT INTO content_items (
                id, opportunity_id, title, description, content_plan, 
                production_status, assets, cost_breakdown, quality_tier,
                target_platforms, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        now = datetime.now()
        params = (
            content_id,
            content_data.opportunity_id,
            content_data.title,
            content_data.description,
            json.dumps(content_data.content_plan) if content_data.content_plan else None,
            content_data.production_status,
            json.dumps(content_data.assets) if content_data.assets else None,
            json.dumps(content_data.cost_breakdown) if content_data.cost_breakdown else None,
            content_data.quality_tier,
            json.dumps(content_data.target_platforms) if content_data.target_platforms else None,
            now,
            now
        )
        
        self.execute_query(query, params)
        return content_id
    
    def get_content_by_id(self, content_id: str, include_opportunity: bool = True, 
                         include_uploads: bool = True) -> Optional[ContentItem]:
        """ดึง content ตาม ID"""
        if include_opportunity:
            query = """
                SELECT c.*, o.suggested_angle as opp_angle, o.estimated_roi as opp_roi,
                       t.topic as trend_topic, t.source as trend_source
                FROM content_items c
                LEFT JOIN content_opportunities o ON c.opportunity_id = o.id
                LEFT JOIN trends t ON o.trend_id = t.id
                WHERE c.id = ?
            """
        else:
            query = "SELECT * FROM content_items WHERE id = ?"
        
        results = self.execute_query(query, (content_id,), fetch=True)
        
        if results:
            content = self._row_to_content(results[0], include_opportunity)
            
            if include_uploads:
                content.uploads = self._get_uploads_for_content(content_id)
            
            return content
        return None
    
    def get_content_filtered(self, status: str = None, platform: str = None,
                           quality_tier: str = None, days_back: int = None,
                           limit: int = 50) -> List[ContentItem]:
        """ดึง content ที่กรองแล้ว"""
        query = """
            SELECT c.*, o.suggested_angle as opp_angle, o.estimated_roi as opp_roi,
                   t.topic as trend_topic, t.source as trend_source
            FROM content_items c
            LEFT JOIN content_opportunities o ON c.opportunity_id = o.id
            LEFT JOIN trends t ON o.trend_id = t.id
            WHERE 1=1
        """
        params = []
        
        if status:
            query += " AND c.production_status = ?"
            params.append(status)
        
        if platform:
            query += " AND c.target_platforms LIKE ?"
            params.append(f"%{platform}%")
        
        if quality_tier:
            query += " AND c.quality_tier = ?"
            params.append(quality_tier)
        
        if days_back:
            cutoff_date = datetime.now() - timedelta(days=days_back)
            query += " AND c.created_at >= ?"
            params.append(cutoff_date)
        
        query += " ORDER BY c.created_at DESC"
        
        if limit:
            query += " LIMIT ?"
            params.append(limit)
        
        results = self.execute_query(query, tuple(params), fetch=True)
        return [self._row_to_content(row, include_opportunity=True) for row in results]
    
    def count_content_today(self) -> int:
        """นับ content วันนี้"""
        today = datetime.now().date()
        query = """
            SELECT COUNT(*) as count FROM content_items 
            WHERE DATE(created_at) = ?
        """
        results = self.execute_query(query, (today,), fetch=True)
        return results[0]['count'] if results else 0
    
    def get_total_content(self) -> int:
        """นับ content ทั้งหมด"""
        query = "SELECT COUNT(*) as count FROM content_items"
        results = self.execute_query(query, fetch=True)
        return results[0]['count'] if results else 0
    
    def get_published_count(self) -> int:
        """นับ content ที่ publish แล้ว"""
        query = """
            SELECT COUNT(DISTINCT c.id) as count 
            FROM content_items c
            INNER JOIN uploads u ON c.id = u.content_id
            WHERE u.upload_status = 'completed'
        """
        results = self.execute_query(query, fetch=True)
        return results[0]['count'] if results else 0
    
    def get_in_progress_count(self) -> int:
        """นับ content ที่กำลังทำ"""
        query = """
            SELECT COUNT(*) as count FROM content_items 
            WHERE production_status IN ('pending', 'generating')
        """
        results = self.execute_query(query, fetch=True)
        return results[0]['count'] if results else 0
    
    def get_available_platforms(self) -> List[str]:
        """ดึงรายการ platforms ที่มี"""
        query = """
            SELECT DISTINCT target_platforms 
            FROM content_items 
            WHERE target_platforms IS NOT NULL
        """
        results = self.execute_query(query, fetch=True)
        
        platforms = set()
        for row in results:
            if row['target_platforms']:
                try:
                    platform_list = json.loads(row['target_platforms'])
                    platforms.update(platform_list)
                except:
                    pass
        
        return sorted(list(platforms))
    
    def get_available_statuses(self) -> List[str]:
        """ดึงรายการ statuses ที่มี"""
        query = """
            SELECT DISTINCT production_status 
            FROM content_items 
            WHERE production_status IS NOT NULL
            ORDER BY production_status
        """
        results = self.execute_query(query, fetch=True)
        return [row['production_status'] for row in results]
    
    def get_success_rate(self) -> float:
        """คำนวณอัตราความสำเร็จ"""
        query = """
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN production_status = 'completed' THEN 1 ELSE 0 END) as completed
            FROM content_items
        """
        results = self.execute_query(query, fetch=True)
        
        if results and results[0]['total'] > 0:
            return (results[0]['completed'] / results[0]['total']) * 100
        return 0.0
    
    def get_average_views(self) -> int:
        """คำนวณ average views"""
        query = """
            SELECT AVG(pm.views) as avg_views
            FROM performance_metrics pm
            INNER JOIN uploads u ON pm.upload_id = u.id
            INNER JOIN content_items c ON u.content_id = c.id
            WHERE pm.views > 0
        """
        results = self.execute_query(query, fetch=True)
        return int(results[0]['avg_views']) if results and results[0]['avg_views'] else 0
    
    def get_roi_by_platform(self) -> Dict[str, Dict[str, Any]]:
        """คำนวณ ROI ตาม platform"""
        query = """
            SELECT 
                u.platform,
                COUNT(DISTINCT c.id) as content_count,
                AVG(pm.views) as avg_views,
                AVG(pm.likes) as avg_likes,
                AVG(pm.revenue) as avg_revenue,
                SUM(pm.revenue) as total_revenue
            FROM content_items c
            INNER JOIN uploads u ON c.id = u.content_id
            LEFT JOIN performance_metrics pm ON u.id = pm.upload_id
            WHERE u.upload_status = 'completed'
            GROUP BY u.platform
        """
        
        results = self.execute_query(query, fetch=True)
        
        roi_data = {}
        for row in results:
            platform = row['platform']
            roi_data[platform] = {
                'content_count': row['content_count'],
                'avg_views': int(row['avg_views']) if row['avg_views'] else 0,
                'avg_likes': int(row['avg_likes']) if row['avg_likes'] else 0,
                'avg_revenue': float(row['avg_revenue']) if row['avg_revenue'] else 0.0,
                'total_revenue': float(row['total_revenue']) if row['total_revenue'] else 0.0,
                'roi': 0.0  # จะคำนวณด้านล่าง
            }
            
            # คำนวณ ROI แบบง่าย (revenue / estimated cost)
            if roi_data[platform]['content_count'] > 0:
                avg_cost = 50  # ค่าเฉลี่ยต้นทุน (สามารถปรับได้)
                if avg_cost > 0:
                    roi_data[platform]['roi'] = roi_data[platform]['avg_revenue'] / avg_cost
        
        return roi_data
    
    def get_platform_performance(self) -> Dict[str, Any]:
        """ดึงข้อมูล performance ตาม platform"""
        query = """