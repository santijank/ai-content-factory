"""
Opportunity Repository - จัดการข้อมูล Content Opportunities
ตำแหน่งไฟล์: database/repositories/opportunity_repository.py
"""
import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from database.models.base import BaseRepository, BaseModel

class ContentOpportunity(BaseModel):
    """Model สำหรับ Content Opportunity data"""
    
    def __init__(self):
        super().__init__()
        self.trend_id = None
        self.suggested_angle = None
        self.estimated_views = 0
        self.competition_level = 'medium'  # low, medium, high
        self.production_cost = 0.0
        self.estimated_roi = 0.0
        self.priority_score = 0.0
        self.status = 'pending'  # pending, analyzing, ready, selected, completed
        self.analysis_data = {}
        self.trend = None  # จะถูก populate ในบาง methods

class OpportunityRepository(BaseRepository):
    """Repository สำหรับจัดการ Content Opportunities"""
    
    def create_opportunity(self, opportunity_data: ContentOpportunity) -> str:
        """สร้าง opportunity ใหม่"""
        opportunity_id = self.generate_id()
        
        query = """
            INSERT INTO content_opportunities (
                id, trend_id, suggested_angle, estimated_views, competition_level,
                production_cost, estimated_roi, priority_score, status, 
                analysis_data, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        now = datetime.now()
        params = (
            opportunity_id,
            opportunity_data.trend_id,
            opportunity_data.suggested_angle,
            opportunity_data.estimated_views,
            opportunity_data.competition_level,
            opportunity_data.production_cost,
            opportunity_data.estimated_roi,
            opportunity_data.priority_score,
            opportunity_data.status,
            json.dumps(opportunity_data.analysis_data) if opportunity_data.analysis_data else None,
            now,
            now
        )
        
        self.execute_query(query, params)
        return opportunity_id
    
    def get_opportunity_by_id(self, opportunity_id: str, include_trend: bool = True) -> Optional[ContentOpportunity]:
        """ดึง opportunity ตาม ID"""
        if include_trend:
            query = """
                SELECT o.*, t.topic as trend_topic, t.source as trend_source, 
                       t.category as trend_category, t.popularity_score as trend_popularity
                FROM content_opportunities o
                LEFT JOIN trends t ON o.trend_id = t.id
                WHERE o.id = ?
            """
        else:
            query = "SELECT * FROM content_opportunities WHERE id = ?"
        
        results = self.execute_query(query, (opportunity_id,), fetch=True)
        
        if results:
            return self._row_to_opportunity(results[0], include_trend)
        return None
    
    def get_opportunities_filtered(self, sort_by: str = 'priority_score', 
                                 status: str = None, min_roi: float = None,
                                 competition_level: str = None, limit: int = 50) -> List[ContentOpportunity]:
        """ดึง opportunities ที่กรองแล้ว"""
        query = """
            SELECT o.*, t.topic as trend_topic, t.source as trend_source,
                   t.category as trend_category, t.popularity_score as trend_popularity
            FROM content_opportunities o
            LEFT JOIN trends t ON o.trend_id = t.id
            WHERE 1=1
        """
        params = []
        
        if status:
            query += " AND o.status = ?"
            params.append(status)
        
        if min_roi is not None:
            query += " AND o.estimated_roi >= ?"
            params.append(min_roi)
        
        if competition_level:
            query += " AND o.competition_level = ?"
            params.append(competition_level)
        
        # Sorting
        valid_sorts = ['priority_score', 'estimated_roi', 'estimated_views', 'created_at']
        if sort_by not in valid_sorts:
            sort_by = 'priority_score'
        
        query += f" ORDER BY o.{sort_by} DESC"
        
        if limit:
            query += " LIMIT ?"
            params.append(limit)
        
        results = self.execute_query(query, tuple(params), fetch=True)
        return [self._row_to_opportunity(row, include_trend=True) for row in results]
    
    def get_best_opportunities(self, limit: int = 5, days_back: int = 7) -> List[ContentOpportunity]:
        """ดึง opportunities ที่ดีที่สุด"""
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        query = """
            SELECT o.*, t.topic as trend_topic, t.source as trend_source,
                   t.category as trend_category, t.popularity_score as trend_popularity
            FROM content_opportunities o
            LEFT JOIN trends t ON o.trend_id = t.id
            WHERE o.created_at >= ? AND o.status IN ('ready', 'pending')
            ORDER BY o.priority_score DESC, o.estimated_roi DESC
            LIMIT ?
        """
        
        results = self.execute_query(query, (cutoff_date, limit), fetch=True)
        return [self._row_to_opportunity(row, include_trend=True) for row in results]
    
    def get_opportunities_by_trend(self, trend_id: str) -> List[ContentOpportunity]:
        """ดึง opportunities ของ trend นั้นๆ"""
        query = """
            SELECT o.*, t.topic as trend_topic, t.source as trend_source,
                   t.category as trend_category, t.popularity_score as trend_popularity
            FROM content_opportunities o
            LEFT JOIN trends t ON o.trend_id = t.id
            WHERE o.trend_id = ?
            ORDER BY o.priority_score DESC
        """
        
        results = self.execute_query(query, (trend_id,), fetch=True)
        return [self._row_to_opportunity(row, include_trend=True) for row in results]
    
    def count_opportunities_today(self) -> int:
        """นับ opportunities วันนี้"""
        today = datetime.now().date()
        query = """
            SELECT COUNT(*) as count FROM content_opportunities 
            WHERE DATE(created_at) = ?
        """
        results = self.execute_query(query, (today,), fetch=True)
        return results[0]['count'] if results else 0
    
    def get_total_opportunities(self) -> int:
        """นับ opportunities ทั้งหมด"""
        query = "SELECT COUNT(*) as count FROM content_opportunities"
        results = self.execute_query(query, fetch=True)
        return results[0]['count'] if results else 0
    
    def get_pending_count(self) -> int:
        """นับ opportunities ที่รอการดำเนินการ"""
        query = """
            SELECT COUNT(*) as count FROM content_opportunities 
            WHERE status IN ('pending', 'ready')
        """
        results = self.execute_query(query, fetch=True)
        return results[0]['count'] if results else 0
    
    def get_high_priority_count(self, threshold: float = 7.0) -> int:
        """นับ opportunities ที่มี priority สูง"""
        query = """
            SELECT COUNT(*) as count FROM content_opportunities 
            WHERE priority_score >= ?
        """
        results = self.execute_query(query, (threshold,), fetch=True)
        return results[0]['count'] if results else 0
    
    def get_total_revenue_estimate(self) -> float:
        """คำนวณรายได้คาดการณ์รวม"""
        query = """
            SELECT SUM(estimated_views * estimated_roi * 0.001) as total_revenue
            FROM content_opportunities 
            WHERE status IN ('ready', 'pending')
        """
        results = self.execute_query(query, fetch=True)
        return float(results[0]['total_revenue']) if results and results[0]['total_revenue'] else 0.0
    
    def get_revenue_projection(self, days_ahead: int = 30) -> Dict[str, Any]:
        """คำนวณการคาดการณ์รายได้"""
        query = """
            SELECT 
                competition_level,
                COUNT(*) as opportunity_count,
                AVG(estimated_roi) as avg_roi,
                SUM(estimated_views) as total_estimated_views,
                SUM(estimated_views * estimated_roi * 0.001) as projected_revenue
            FROM content_opportunities 
            WHERE status IN ('ready', 'pending')
            GROUP BY competition_level
        """
        
        results = self.execute_query(query, fetch=True)
        
        projection = {
            'by_competition': {},
            'total_opportunities': 0,
            'total_projected_revenue': 0.0,
            'average_roi': 0.0
        }
        
        total_opps = 0
        total_revenue = 0.0
        total_roi = 0.0
        
        for row in results:
            level = row['competition_level']
            projection['by_competition'][level] = {
                'count': row['opportunity_count'],
                'avg_roi': float(row['avg_roi']) if row['avg_roi'] else 0.0,
                'total_views': row['total_estimated_views'] or 0,
                'projected_revenue': float(row['projected_revenue']) if row['projected_revenue'] else 0.0
            }
            
            total_opps += row['opportunity_count']
            total_revenue += float(row['projected_revenue']) if row['projected_revenue'] else 0.0
            total_roi += float(row['avg_roi']) if row['avg_roi'] else 0.0
        
        projection['total_opportunities'] = total_opps
        projection['total_projected_revenue'] = total_revenue
        projection['average_roi'] = total_roi / len(results) if results else 0.0
        
        return projection
    
    def update_opportunity_status(self, opportunity_id: str, status: str, 
                                analysis_data: Dict[str, Any] = None) -> bool:
        """อัปเดต status ของ opportunity"""
        query = """
            UPDATE content_opportunities 
            SET status = ?, updated_at = ?
        """
        params = [status, datetime.now()]
        
        if analysis_data:
            query += ", analysis_data = ?"
            params.append(json.dumps(analysis_data))
        
        query += " WHERE id = ?"
        params.append(opportunity_id)
        
        try:
            rows_affected = self.execute_query(query, tuple(params))
            return rows_affected > 0
        except Exception as e:
            print(f"Error updating opportunity status: {str(e)}")
            return False
    
    def update_opportunity_scores(self, opportunity_id: str, priority_score: float = None,
                                estimated_roi: float = None, estimated_views: int = None) -> bool:
        """อัปเดตคะแนนและการประเมิน"""
        updates = []
        params = []
        
        if priority_score is not None:
            updates.append("priority_score = ?")
            params.append(priority_score)
        
        if estimated_roi is not None:
            updates.append("estimated_roi = ?")
            params.append(estimated_roi)
        
        if estimated_views is not None:
            updates.append("estimated_views = ?")
            params.append(estimated_views)
        
        if not updates:
            return False
        
        updates.append("updated_at = ?")
        params.append(datetime.now())
        params.append(opportunity_id)
        
        query = f"""
            UPDATE content_opportunities 
            SET {', '.join(updates)}
            WHERE id = ?
        """
        
        try:
            rows_affected = self.execute_query(query, tuple(params))
            return rows_affected > 0
        except Exception as e:
            print(f"Error updating opportunity scores: {str(e)}")
            return False
    
    def search_opportunities(self, keyword: str, limit: int = 20) -> List[ContentOpportunity]:
        """ค้นหา opportunities ตาม keyword"""
        query = """
            SELECT o.*, t.topic as trend_topic, t.source as trend_source,
                   t.category as trend_category, t.popularity_score as trend_popularity
            FROM content_opportunities o
            LEFT JOIN trends t ON o.trend_id = t.id
            WHERE o.suggested_angle LIKE ? OR t.topic LIKE ?
            ORDER BY o.priority_score DESC
            LIMIT ?
        """
        search_term = f"%{keyword}%"
        results = self.execute_query(query, (search_term, search_term, limit), fetch=True)
        return [self._row_to_opportunity(row, include_trend=True) for row in results]
    
    def get_opportunities_by_competition(self, competition_level: str) -> List[ContentOpportunity]:
        """ดึง opportunities ตามระดับการแข่งขัน"""
        query = """
            SELECT o.*, t.topic as trend_topic, t.source as trend_source,
                   t.category as trend_category, t.popularity_score as trend_popularity
            FROM content_opportunities o
            LEFT JOIN trends t ON o.trend_id = t.id
            WHERE o.competition_level = ?
            ORDER BY o.priority_score DESC
        """
        
        results = self.execute_query(query, (competition_level,), fetch=True)
        return [self._row_to_opportunity(row, include_trend=True) for row in results]
    
    def bulk_create_opportunities(self, opportunities_data: List[ContentOpportunity]) -> List[str]:
        """สร้าง opportunities หลายรายการพร้อมกัน"""
        if not opportunities_data:
            return []
        
        query = """
            INSERT INTO content_opportunities (
                id, trend_id, suggested_angle, estimated_views, competition_level,
                production_cost, estimated_roi, priority_score, status, 
                analysis_data, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        now = datetime.now()
        params_list = []
        opportunity_ids = []
        
        for opp_data in opportunities_data:
            opp_id = self.generate_id()
            opportunity_ids.append(opp_id)
            
            params = (
                opp_id,
                opp_data.trend_id,
                opp_data.suggested_angle,
                opp_data.estimated_views,
                opp_data.competition_level,
                opp_data.production_cost,
                opp_data.estimated_roi,
                opp_data.priority_score,
                opp_data.status,
                json.dumps(opp_data.analysis_data) if opp_data.analysis_data else None,
                now,
                now
            )
            params_list.append(params)
        
        self.execute_many(query, params_list)
        return opportunity_ids
    
    def delete_old_opportunities(self, days_old: int = 60, exclude_selected: bool = True) -> int:
        """ลบ opportunities เก่า"""
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        query = """
            DELETE FROM content_opportunities 
            WHERE created_at < ?
        """
        params = [cutoff_date]
        
        if exclude_selected:
            query += " AND status NOT IN ('selected', 'completed')"
        
        return self.execute_query(query, tuple(params))
    
    def get_status_distribution(self) -> Dict[str, int]:
        """นับจำนวนตาม status"""
        query = """
            SELECT status, COUNT(*) as count 
            FROM content_opportunities 
            GROUP BY status 
            ORDER BY count DESC
        """
        results = self.execute_query(query, fetch=True)
        return {row['status']: row['count'] for row in results}
    
    def get_competition_distribution(self) -> Dict[str, int]:
        """นับจำนวนตามระดับการแข่งขัน"""
        query = """
            SELECT competition_level, COUNT(*) as count 
            FROM content_opportunities 
            GROUP BY competition_level 
            ORDER BY count DESC
        """
        results = self.execute_query(query, fetch=True)
        return {row['competition_level']: row['count'] for row in results}
    
    def _row_to_opportunity(self, row: Dict[str, Any], include_trend: bool = False) -> ContentOpportunity:
        """แปลง database row เป็น ContentOpportunity object"""
        opportunity = ContentOpportunity()
        opportunity.id = row['id']
        opportunity.trend_id = row['trend_id']
        opportunity.suggested_angle = row['suggested_angle']
        opportunity.estimated_views = row['estimated_views'] or 0
        opportunity.competition_level = row['competition_level']
        opportunity.production_cost = float(row['production_cost']) if row['production_cost'] else 0.0
        opportunity.estimated_roi = float(row['estimated_roi']) if row['estimated_roi'] else 0.0
        opportunity.priority_score = float(row['priority_score']) if row['priority_score'] else 0.0
        opportunity.status = row['status']
        opportunity.analysis_data = json.loads(row['analysis_data']) if row['analysis_data'] else {}
        opportunity.created_at = row['created_at']
        opportunity.updated_at = row['updated_at']
        
        # Add trend information if available
        if include_trend and 'trend_topic' in row:
            opportunity.trend = {
                'topic': row['trend_topic'],
                'source': row['trend_source'],
                'category': row['trend_category'],
                'popularity_score': float(row['trend_popularity']) if row['trend_popularity'] else 0.0
            }
        
        return opportunity