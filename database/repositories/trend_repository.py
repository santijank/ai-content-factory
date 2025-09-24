"""
Enhanced Trend Repository
Provides database operations for trend data with advanced querying capabilities
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json

import psycopg2
from psycopg2.extras import RealDictCursor, Json
from psycopg2 import sql

# Import models
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from trend_monitor.models.trend_data import TrendData, TrendSource, TrendCategory

logger = logging.getLogger(__name__)

class TrendRepository:
    """Repository for trend data operations"""
    
    def __init__(self, connection=None, connection_string=None):
        self.connection = connection
        self.connection_string = connection_string
        self._owned_connection = connection is None
        
    def _get_connection(self):
        """Get database connection"""
        if self.connection:
            return self.connection
        elif self.connection_string:
            return psycopg2.connect(self.connection_string)
        else:
            # Use environment variables
            import os
            return psycopg2.connect(
                host=os.environ.get('DB_HOST', 'localhost'),
                port=int(os.environ.get('DB_PORT', 5432)),
                database=os.environ.get('DB_NAME', 'content_factory'),
                user=os.environ.get('DB_USER', 'postgres'),
                password=os.environ.get('DB_PASSWORD', 'postgres')
            )
    
    def save_trend(self, trend: TrendData) -> bool:
        """Save a single trend to database"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            insert_sql = """
                INSERT INTO trends (
                    id, source, topic, keywords, popularity_score, growth_rate,
                    category, region, collected_at, raw_data
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                ON CONFLICT (id) DO UPDATE SET
                    popularity_score = EXCLUDED.popularity_score,
                    growth_rate = EXCLUDED.growth_rate,
                    updated_at = CURRENT_TIMESTAMP,
                    raw_data = EXCLUDED.raw_data
            """
            
            cursor.execute(insert_sql, (
                trend.id,
                trend.source.value,
                trend.topic,
                Json(trend.keywords),
                trend.popularity_score,
                trend.growth_rate,
                trend.category.value,
                trend.region,
                trend.collected_at,
                Json(trend.raw_data or {})
            ))
            
            if self._owned_connection:
                conn.commit()
                conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving trend: {e}")
            if self._owned_connection and conn:
                conn.rollback()
                conn.close()
            return False
    
    def save_trends_batch(self, trends: List[TrendData]) -> int:
        """Save multiple trends in a batch"""
        if not trends:
            return 0
            
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            insert_sql = """
                INSERT INTO trends (
                    id, source, topic, keywords, popularity_score, growth_rate,
                    category, region, collected_at, raw_data
                ) VALUES %s
                ON CONFLICT (id) DO UPDATE SET
                    popularity_score = EXCLUDED.popularity_score,
                    growth_rate = EXCLUDED.growth_rate,
                    updated_at = CURRENT_TIMESTAMP,
                    raw_data = EXCLUDED.raw_data
            """
            
            # Prepare data for batch insert
            values = []
            for trend in trends:
                values.append((
                    trend.id,
                    trend.source.value,
                    trend.topic,
                    Json(trend.keywords),
                    trend.popularity_score,
                    trend.growth_rate,
                    trend.category.value,
                    trend.region,
                    trend.collected_at,
                    Json(trend.raw_data or {})
                ))
            
            psycopg2.extras.execute_values(cursor, insert_sql, values)
            
            saved_count = cursor.rowcount
            
            if self._owned_connection:
                conn.commit()
                conn.close()
            
            logger.info(f"Saved {saved_count} trends in batch")
            return saved_count
            
        except Exception as e:
            logger.error(f"Error saving trends batch: {e}")
            if self._owned_connection and conn:
                conn.rollback()
                conn.close()
            return 0
    
    def get_trends(self,
                   source: Optional[str] = None,
                   category: Optional[str] = None,
                   region: Optional[str] = None,
                   since: Optional[datetime] = None,
                   until: Optional[datetime] = None,
                   min_popularity_score: float = 0.0,
                   limit: int = 100,
                   order_by: str = 'popularity_score',
                   order_desc: bool = True) -> List[TrendData]:
        """Get trends with flexible filtering"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Build WHERE clause dynamically
            where_conditions = []
            params = []
            
            if source:
                where_conditions.append("source = %s")
                params.append(source)
            
            if category:
                where_conditions.append("category = %s")
                params.append(category)
                
            if region:
                where_conditions.append("region = %s")
                params.append(region)
                
            if since:
                where_conditions.append("collected_at >= %s")
                params.append(since)
                
            if until:
                where_conditions.append("collected_at <= %s")
                params.append(until)
                
            if min_popularity_score > 0:
                where_conditions.append("popularity_score >= %s")
                params.append(min_popularity_score)
            
            # Build ORDER BY clause
            valid_order_fields = ['popularity_score', 'collected_at', 'growth_rate', 'topic']
            if order_by not in valid_order_fields:
                order_by = 'popularity_score'
                
            order_direction = 'DESC' if order_desc else 'ASC'
            
            # Construct query
            base_query = "SELECT * FROM trends"
            
            if where_conditions:
                where_clause = " WHERE " + " AND ".join(where_conditions)
            else:
                where_clause = ""
                
            order_clause = f" ORDER BY {order_by} {order_direction}"
            limit_clause = f" LIMIT {limit}"
            
            query = base_query + where_clause + order_clause + limit_clause
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            if self._owned_connection:
                conn.close()
            
            # Convert to TrendData objects
            trends = []
            for row in rows:
                trend = TrendData(
                    id=row['id'],
                    source=TrendSource(row['source']),
                    topic=row['topic'],
                    keywords=row['keywords'] or [],
                    popularity_score=row['popularity_score'],
                    growth_rate=row['growth_rate'],
                    category=TrendCategory(row['category']),
                    region=row['region'],
                    collected_at=row['collected_at'],
                    raw_data=row['raw_data']
                )
                trends.append(trend)
            
            return trends
            
        except Exception as e:
            logger.error(f"Error getting trends: {e}")
            if self._owned_connection and conn:
                conn.close()
            return []
    
    def get_trend_by_id(self, trend_id: str) -> Optional[TrendData]:
        """Get a specific trend by ID"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("SELECT * FROM trends WHERE id = %s", (trend_id,))
            row = cursor.fetchone()
            
            if self._owned_connection:
                conn.close()
            
            if row:
                return TrendData(
                    id=row['id'],
                    source=TrendSource(row['source']),
                    topic=row['topic'],
                    keywords=row['keywords'] or [],
                    popularity_score=row['popularity_score'],
                    growth_rate=row['growth_rate'],
                    category=TrendCategory(row['category']),
                    region=row['region'],
                    collected_at=row['collected_at'],
                    raw_data=row['raw_data']
                )
            return None
            
        except Exception as e:
            logger.error(f"Error getting trend by ID: {e}")
            if self._owned_connection and conn:
                conn.close()
            return None
    
    def get_top_trends(self, 
                       since: Optional[datetime] = None,
                       limit: int = 10,
                       category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get aggregated top trends across sources"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            if since is None:
                since = datetime.utcnow() - timedelta(hours=24)
            
            # Use the database function for aggregated top trends
            if category:
                cursor.execute("""
                    SELECT topic, sources, max_popularity_score, avg_popularity_score,
                           mention_count, keywords, category, latest_collection
                    FROM (
                        SELECT 
                            topic,
                            array_agg(DISTINCT source) as sources,
                            MAX(popularity_score) as max_popularity_score,
                            AVG(popularity_score) as avg_popularity_score,
                            COUNT(*) as mention_count,
                            array_agg(DISTINCT keyword) as keywords,
                            category,
                            MAX(collected_at) as latest_collection,
                            ROW_NUMBER() OVER (ORDER BY MAX(popularity_score) DESC) as rn
                        FROM trends t,
                             LATERAL unnest(t.keywords) as keyword
                        WHERE collected_at >= %s AND category = %s
                        GROUP BY topic, category
                    ) ranked
                    WHERE rn <= %s
                    ORDER BY max_popularity_score DESC
                """, (since, category, limit))
            else:
                cursor.execute("""
                    SELECT topic, sources, max_popularity_score, avg_popularity_score,
                           mention_count, keywords, category, latest_collection
                    FROM (
                        SELECT 
                            topic,
                            array_agg(DISTINCT source) as sources,
                            MAX(popularity_score) as max_popularity_score,
                            AVG(popularity_score) as avg_popularity_score,
                            COUNT(*) as mention_count,
                            array_agg(DISTINCT keyword) as keywords,
                            category,
                            MAX(collected_at) as latest_collection,
                            ROW_NUMBER() OVER (ORDER BY MAX(popularity_score) DESC) as rn
                        FROM trends t,
                             LATERAL unnest(t.keywords) as keyword
                        WHERE collected_at >= %s
                        GROUP BY topic, category
                    ) ranked
                    WHERE rn <= %s
                    ORDER BY max_popularity_score DESC
                """, (since, limit))
            
            rows = cursor.fetchall()
            
            if self._owned_connection:
                conn.close()
            
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Error getting top trends: {e}")
            if self._owned_connection and conn:
                conn.close()
            return []
    
    def search_trends(self, 
                      search_term: str,
                      hours_back: int = 168,
                      limit: int = 20) -> List[Dict[str, Any]]:
        """Full-text search for trends"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Use the database search function
            cursor.execute("""
                SELECT * FROM search_trends(%s, %s, %s)
            """, (search_term, hours_back, limit))
            
            rows = cursor.fetchall()
            
            if self._owned_connection:
                conn.close()
            
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Error searching trends: {e}")
            if self._owned_connection and conn:
                conn.close()
            return []
    
    def get_collection_stats(self, 
                           since: Optional[datetime] = None) -> Dict[str, Any]:
        """Get trend collection statistics"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            if since is None:
                since = datetime.utcnow() - timedelta(hours=24)
            
            # Get overall stats
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_trends,
                    COUNT(DISTINCT source) as sources_active,
                    COUNT(DISTINCT category) as categories_found,
                    COUNT(DISTINCT region) as regions_covered,
                    AVG(popularity_score) as avg_popularity,
                    MAX(popularity_score) as max_popularity,
                    MIN(collected_at) as earliest_collection,
                    MAX(collected_at) as latest_collection
                FROM trends 
                WHERE collected_at >= %s
            """, (since,))
            
            overall_stats = cursor.fetchone()
            
            # Get stats by source
            cursor.execute("""
                SELECT 
                    source,
                    COUNT(*) as count,
                    AVG(popularity_score) as avg_score,
                    MAX(popularity_score) as max_score
                FROM trends 
                WHERE collected_at >= %s
                GROUP BY source
                ORDER BY count DESC
            """, (since,))
            
            source_stats = cursor.fetchall()
            
            # Get stats by category
            cursor.execute("""
                SELECT 
                    category,
                    COUNT(*) as count,
                    AVG(popularity_score) as avg_score
                FROM trends 
                WHERE collected_at >= %s
                GROUP BY category
                ORDER BY count DESC
            """, (since,))
            
            category_stats = cursor.fetchall()
            
            if self._owned_connection:
                conn.close()
            
            return {
                'overall': dict(overall_stats) if overall_stats else {},
                'by_source': [dict(row) for row in source_stats],
                'by_category': [dict(row) for row in category_stats],
                'period': {
                    'since': since.isoformat(),
                    'hours': (datetime.utcnow() - since).total_seconds() / 3600
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            if self._owned_connection and conn:
                conn.close()
            return {}
    
    def delete_old_trends(self, retention_days: int = 30) -> int:
        """Delete old trends based on retention policy"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Use the database cleanup function
            cursor.execute("SELECT cleanup_old_trends(%s)", (retention_days,))
            deleted_count = cursor.fetchone()[0]
            
            if self._owned_connection:
                conn.commit()
                conn.close()
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error deleting old trends: {e}")
            if self._owned_connection and conn:
                conn.rollback()
                conn.close()
            return 0
    
    def get_trending_keywords(self, 
                             limit: int = 20,
                             min_mentions: int = 2) -> List[Dict[str, Any]]:
        """Get most frequently mentioned keywords across trends"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                SELECT 
                    keyword,
                    COUNT(*) as mention_count,
                    AVG(popularity_score) as avg_popularity,
                    array_agg(DISTINCT source) as sources,
                    array_agg(DISTINCT category) as categories
                FROM trends t,
                     LATERAL unnest(t.keywords) as keyword
                WHERE 
                    collected_at >= CURRENT_TIMESTAMP - INTERVAL '24 hours'
                    AND keyword != ''
                    AND LENGTH(keyword) > 2
                GROUP BY keyword
                HAVING COUNT(*) >= %s
                ORDER BY mention_count DESC, avg_popularity DESC
                LIMIT %s
            """, (min_mentions, limit))
            
            rows = cursor.fetchall()
            
            if self._owned_connection:
                conn.close()
            
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Error getting trending keywords: {e}")
            if self._owned_connection and conn:
                conn.close()
            return []
    
    def get_trend_growth_analysis(self, 
                                 hours_back: int = 24) -> List[Dict[str, Any]]:
        """Analyze trend growth patterns"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                SELECT 
                    topic,
                    source,
                    category,
                    MIN(collected_at) as first_seen,
                    MAX(collected_at) as last_seen,
                    COUNT(*) as mention_count,
                    MIN(popularity_score) as initial_score,
                    MAX(popularity_score) as peak_score,
                    MAX(popularity_score) - MIN(popularity_score) as score_growth,
                    AVG(growth_rate) FILTER (WHERE growth_rate IS NOT NULL) as avg_growth_rate
                FROM trends
                WHERE collected_at >= CURRENT_TIMESTAMP - (%s || ' hours')::INTERVAL
                GROUP BY topic, source, category
                HAVING COUNT(*) > 1
                ORDER BY score_growth DESC, peak_score DESC
                LIMIT 50
            """, (hours_back,))
            
            rows = cursor.fetchall()
            
            if self._owned_connection:
                conn.close()
            
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Error getting trend growth analysis: {e}")
            if self._owned_connection and conn:
                conn.close()
            return []