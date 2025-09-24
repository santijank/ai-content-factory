#!/usr/bin/env python3
"""
System Cleanup Script for AI Content Factory
ใช้สำหรับทำความสะอาดระบบ ลบไฟล์เก่า ทำความสะอาด database และ cache
"""

import os
import sys
import shutil
import logging
import argparse
import tempfile
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
import redis
import yaml

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.utils.logger import setup_logger
from shared.utils.error_handler import ErrorHandler

class SystemCleaner:
    """Main class for system cleanup operations"""
    
    def __init__(self, config_path: str = None):
        self.logger = setup_logger("system_cleaner")
        self.error_handler = ErrorHandler()
        self.config = self._load_config(config_path)
        self.db_conn = None
        self.redis_conn = None
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load cleanup configuration"""
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        
        # Default configuration
        return {
            'database': {
                'host': os.getenv('DB_HOST', 'localhost'),
                'port': int(os.getenv('DB_PORT', 5432)),
                'database': os.getenv('DB_NAME', 'content_factory'),
                'user': os.getenv('DB_USER', 'admin'),
                'password': os.getenv('DB_PASSWORD', 'password')
            },
            'redis': {
                'host': os.getenv('REDIS_HOST', 'localhost'),
                'port': int(os.getenv('REDIS_PORT', 6379)),
                'db': int(os.getenv('REDIS_DB', 0))
            },
            'cleanup_settings': {
                'trends_retention_days': 30,
                'failed_content_retention_days': 7,
                'temp_files_retention_hours': 24,
                'log_files_retention_days': 14,
                'backup_files_retention_days': 30,
                'cache_clear_patterns': ['trend_*', 'content_*', 'upload_*']
            },
            'directories': {
                'temp_dir': '/tmp/content-factory',
                'log_dir': 'logs',
                'backup_dir': 'database/backup',
                'cache_dir': 'cache',
                'generated_content_dir': 'generated_content'
            }
        }
    
    def connect_services(self):
        """Connect to database and Redis"""
        try:
            # Database connection
            self.db_conn = psycopg2.connect(**self.config['database'])
            self.logger.info("Connected to database")
            
            # Redis connection
            try:
                self.redis_conn = redis.Redis(**self.config['redis'])
                self.redis_conn.ping()
                self.logger.info("Connected to Redis")
            except Exception as e:
                self.logger.warning(f"Redis connection failed: {str(e)} - continuing without Redis cleanup")
                self.redis_conn = None
                
        except Exception as e:
            self.logger.error(f"Service connection failed: {str(e)}")
            raise
    
    def disconnect_services(self):
        """Disconnect from services"""
        if self.db_conn:
            self.db_conn.close()
            self.logger.info("Disconnected from database")
        
        if self.redis_conn:
            self.redis_conn.close()
            self.logger.info("Disconnected from Redis")
    
    def cleanup_old_trends(self) -> Dict[str, int]:
        """Clean up old trend data"""
        try:
            self.logger.info("Starting trends cleanup...")
            
            retention_days = self.config['cleanup_settings']['trends_retention_days']
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            with self.db_conn.cursor() as cursor:
                # Get count before deletion
                cursor.execute("""
                    SELECT COUNT(*) FROM trends 
                    WHERE collected_at < %s
                """, (cutoff_date,))
                old_trends_count = cursor.fetchone()[0]
                
                if old_trends_count == 0:
                    self.logger.info("No old trends to clean up")
                    return {'trends_deleted': 0}
                
                # Delete old trends (this will cascade to related opportunities)
                cursor.execute("""
                    DELETE FROM trends 
                    WHERE collected_at < %s
                """, (cutoff_date,))
                
                self.db_conn.commit()
                
                self.logger.info(f"Cleaned up {old_trends_count} old trends (older than {retention_days} days)")
                return {'trends_deleted': old_trends_count}
                
        except Exception as e:
            self.logger.error(f"Trends cleanup failed: {str(e)}")
            self.db_conn.rollback()
            return {'trends_deleted': 0}
    
    def cleanup_failed_content(self) -> Dict[str, int]:
        """Clean up failed content items"""
        try:
            self.logger.info("Starting failed content cleanup...")
            
            retention_days = self.config['cleanup_settings']['failed_content_retention_days']
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            with self.db_conn.cursor() as cursor:
                # Get count of failed content
                cursor.execute("""
                    SELECT COUNT(*) FROM content_items 
                    WHERE production_status = 'failed' 
                    AND created_at < %s
                """, (cutoff_date,))
                failed_count = cursor.fetchone()[0]
                
                if failed_count == 0:
                    self.logger.info("No failed content to clean up")
                    return {'failed_content_deleted': 0}
                
                # Delete failed content items
                cursor.execute("""
                    DELETE FROM content_items 
                    WHERE production_status = 'failed' 
                    AND created_at < %s
                """, (cutoff_date,))
                
                self.db_conn.commit()
                
                self.logger.info(f"Cleaned up {failed_count} failed content items (older than {retention_days} days)")
                return {'failed_content_deleted': failed_count}
                
        except Exception as e:
            self.logger.error(f"Failed content cleanup failed: {str(e)}")
            self.db_conn.rollback()
            return {'failed_content_deleted': 0}
    
    def cleanup_temp_files(self) -> Dict[str, int]:
        """Clean up temporary files"""
        try:
            self.logger.info("Starting temporary files cleanup...")
            
            retention_hours = self.config['cleanup_settings']['temp_files_retention_hours']
            cutoff_time = datetime.now() - timedelta(hours=retention_hours)
            
            cleaned_files = 0
            freed_space = 0
            
            temp_dirs = [
                self.config['directories']['temp_dir'],
                tempfile.gettempdir() + '/content-factory',
                self.config['directories']['cache_dir']
            ]
            
            for temp_dir in temp_dirs:
                if not os.path.exists(temp_dir):
                    continue
                    
                self.logger.info(f"Cleaning directory: {temp_dir}")
                
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        
                        try:
                            # Check file modification time
                            file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                            
                            if file_mtime < cutoff_time:
                                file_size = os.path.getsize(file_path)
                                os.remove(file_path)
                                cleaned_files += 1
                                freed_space += file_size
                                
                        except Exception as e:
                            self.logger.warning(f"Could not delete {file_path}: {str(e)}")
                
                # Remove empty directories
                for root, dirs, files in os.walk(temp_dir, topdown=False):
                    for dir_name in dirs:
                        dir_path = os.path.join(root, dir_name)
                        try:
                            if not os.listdir(dir_path):  # Empty directory
                                os.rmdir(dir_path)
                        except Exception:
                            pass  # Directory might not be empty or accessible
            
            freed_space_mb = freed_space / (1024 * 1024)
            self.logger.info(f"Cleaned up {cleaned_files} backup files, freed {freed_space_mb:.2f} MB")
            
            return {
                'backup_files_deleted': cleaned_files,
                'backup_space_freed_mb': round(freed_space_mb, 2)
            }
            
        except Exception as e:
            self.logger.error(f"Backup files cleanup failed: {str(e)}")
            return {'backup_files_deleted': 0, 'backup_space_freed_mb': 0}
    
    def cleanup_redis_cache(self) -> Dict[str, int]:
        """Clean up Redis cache"""
        if not self.redis_conn:
            self.logger.info("Redis not available, skipping cache cleanup")
            return {'cache_keys_deleted': 0}
        
        try:
            self.logger.info("Starting Redis cache cleanup...")
            
            cache_patterns = self.config['cleanup_settings']['cache_clear_patterns']
            total_deleted = 0
            
            for pattern in cache_patterns:
                try:
                    # Get keys matching pattern
                    keys = self.redis_conn.keys(pattern)
                    
                    if keys:
                        # Delete keys
                        deleted_count = self.redis_conn.delete(*keys)
                        total_deleted += deleted_count
                        self.logger.info(f"Deleted {deleted_count} cache keys matching pattern: {pattern}")
                    
                except Exception as e:
                    self.logger.warning(f"Could not clean cache pattern {pattern}: {str(e)}")
            
            self.logger.info(f"Total cache keys deleted: {total_deleted}")
            return {'cache_keys_deleted': total_deleted}
            
        except Exception as e:
            self.logger.error(f"Redis cache cleanup failed: {str(e)}")
            return {'cache_keys_deleted': 0}
    
    def cleanup_generated_content(self) -> Dict[str, int]:
        """Clean up old generated content files"""
        try:
            self.logger.info("Starting generated content cleanup...")
            
            content_dir = self.config['directories']['generated_content_dir']
            
            if not os.path.exists(content_dir):
                self.logger.info("Generated content directory does not exist")
                return {'content_files_deleted': 0}
            
            # Get content items that are published and older than 7 days
            cutoff_date = datetime.now() - timedelta(days=7)
            
            with self.db_conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT assets FROM content_items 
                    WHERE production_status = 'published' 
                    AND completed_at < %s
                    AND assets IS NOT NULL
                """, (cutoff_date,))
                
                published_content = cursor.fetchall()
            
            cleaned_files = 0
            freed_space = 0
            
            for content in published_content:
                if not content['assets']:
                    continue
                    
                try:
                    assets = content['assets']
                    if isinstance(assets, str):
                        import json
                        assets = json.loads(assets)
                    
                    # Delete asset files
                    for asset_type, asset_path in assets.items():
                        if isinstance(asset_path, str) and os.path.exists(asset_path):
                            try:
                                file_size = os.path.getsize(asset_path)
                                os.remove(asset_path)
                                cleaned_files += 1
                                freed_space += file_size
                            except Exception as e:
                                self.logger.warning(f"Could not delete asset {asset_path}: {str(e)}")
                                
                except Exception as e:
                    self.logger.warning(f"Could not process content assets: {str(e)}")
            
            freed_space_mb = freed_space / (1024 * 1024)
            self.logger.info(f"Cleaned up {cleaned_files} generated content files, freed {freed_space_mb:.2f} MB")
            
            return {
                'content_files_deleted': cleaned_files,
                'content_space_freed_mb': round(freed_space_mb, 2)
            }
            
        except Exception as e:
            self.logger.error(f"Generated content cleanup failed: {str(e)}")
            return {'content_files_deleted': 0, 'content_space_freed_mb': 0}
    
    def cleanup_orphaned_records(self) -> Dict[str, int]:
        """Clean up orphaned database records"""
        try:
            self.logger.info("Starting orphaned records cleanup...")
            
            orphaned_records = {}
            
            with self.db_conn.cursor() as cursor:
                # Clean up opportunities without trends
                cursor.execute("""
                    DELETE FROM content_opportunities 
                    WHERE trend_id NOT IN (SELECT id FROM trends)
                """)
                orphaned_opportunities = cursor.rowcount
                orphaned_records['orphaned_opportunities'] = orphaned_opportunities
                
                # Clean up content items without opportunities
                cursor.execute("""
                    DELETE FROM content_items 
                    WHERE opportunity_id NOT IN (SELECT id FROM content_opportunities)
                """)
                orphaned_content = cursor.rowcount
                orphaned_records['orphaned_content'] = orphaned_content
                
                # Clean up uploads without content items
                cursor.execute("""
                    DELETE FROM uploads 
                    WHERE content_id NOT IN (SELECT id FROM content_items)
                """)
                orphaned_uploads = cursor.rowcount
                orphaned_records['orphaned_uploads'] = orphaned_uploads
                
                # Clean up performance metrics without uploads
                cursor.execute("""
                    DELETE FROM performance_metrics 
                    WHERE upload_id NOT IN (SELECT id FROM uploads)
                """)
                orphaned_metrics = cursor.rowcount
                orphaned_records['orphaned_metrics'] = orphaned_metrics
                
                self.db_conn.commit()
                
                total_orphaned = sum(orphaned_records.values())
                self.logger.info(f"Cleaned up {total_orphaned} orphaned records")
                
                return orphaned_records
                
        except Exception as e:
            self.logger.error(f"Orphaned records cleanup failed: {str(e)}")
            self.db_conn.rollback()
            return {
                'orphaned_opportunities': 0,
                'orphaned_content': 0,
                'orphaned_uploads': 0,
                'orphaned_metrics': 0
            }
    
    def optimize_database(self) -> Dict[str, Any]:
        """Optimize database performance"""
        try:
            self.logger.info("Starting database optimization...")
            
            optimization_results = {}
            
            with self.db_conn.cursor() as cursor:
                # Vacuum and analyze tables
                tables = ['trends', 'content_opportunities', 'content_items', 'uploads', 'performance_metrics']
                
                for table in tables:
                    try:
                        # Get table size before optimization
                        cursor.execute(f"SELECT pg_size_pretty(pg_total_relation_size('{table}'))")
                        size_before = cursor.fetchone()[0]
                        
                        # Vacuum and analyze
                        cursor.execute(f"VACUUM ANALYZE {table}")
                        
                        # Get table size after optimization
                        cursor.execute(f"SELECT pg_size_pretty(pg_total_relation_size('{table}'))")
                        size_after = cursor.fetchone()[0]
                        
                        optimization_results[table] = {
                            'size_before': size_before,
                            'size_after': size_after
                        }
                        
                        self.logger.info(f"Optimized table {table}: {size_before} -> {size_after}")
                        
                    except Exception as e:
                        self.logger.warning(f"Could not optimize table {table}: {str(e)}")
                
                # Update table statistics
                cursor.execute("ANALYZE")
                
                self.db_conn.commit()
                
                self.logger.info("Database optimization completed")
                return optimization_results
                
        except Exception as e:
            self.logger.error(f"Database optimization failed: {str(e)}")
            return {}
    
    def generate_cleanup_report(self, results: Dict[str, Any]) -> str:
        """Generate cleanup summary report"""
        report_lines = [
            "=" * 60,
            "AI CONTENT FACTORY - SYSTEM CLEANUP REPORT",
            "=" * 60,
            f"Cleanup Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "DATABASE CLEANUP:",
            f"  • Old trends deleted: {results.get('trends_deleted', 0)}",
            f"  • Failed content deleted: {results.get('failed_content_deleted', 0)}",
            f"  • Orphaned opportunities: {results.get('orphaned_opportunities', 0)}",
            f"  • Orphaned content items: {results.get('orphaned_content', 0)}",
            f"  • Orphaned uploads: {results.get('orphaned_uploads', 0)}",
            f"  • Orphaned metrics: {results.get('orphaned_metrics', 0)}",
            "",
            "FILE SYSTEM CLEANUP:",
            f"  • Temp files deleted: {results.get('temp_files_deleted', 0)}",
            f"  • Log files deleted: {results.get('log_files_deleted', 0)}",
            f"  • Backup files deleted: {results.get('backup_files_deleted', 0)}",
            f"  • Content files deleted: {results.get('content_files_deleted', 0)}",
            "",
            "SPACE FREED:",
            f"  • Temp files: {results.get('space_freed_mb', 0)} MB",
            f"  • Log files: {results.get('log_space_freed_mb', 0)} MB",
            f"  • Backup files: {results.get('backup_space_freed_mb', 0)} MB",
            f"  • Content files: {results.get('content_space_freed_mb', 0)} MB",
            f"  • Total: {results.get('space_freed_mb', 0) + results.get('log_space_freed_mb', 0) + results.get('backup_space_freed_mb', 0) + results.get('content_space_freed_mb', 0)} MB",
            "",
            "CACHE CLEANUP:",
            f"  • Redis keys deleted: {results.get('cache_keys_deleted', 0)}",
            "",
            "=" * 60
        ]
        
        return "\n".join(report_lines)
    
    def run_full_cleanup(self, skip_categories: List[str] = None) -> Dict[str, Any]:
        """Run complete system cleanup"""
        skip_categories = skip_categories or []
        results = {}
        
        try:
            self.connect_services()
            
            self.logger.info("🧹 Starting full system cleanup...")
            
            # Database cleanup
            if 'database' not in skip_categories:
                results.update(self.cleanup_old_trends())
                results.update(self.cleanup_failed_content())
                results.update(self.cleanup_orphaned_records())
            
            # File system cleanup
            if 'filesystem' not in skip_categories:
                results.update(self.cleanup_temp_files())
                results.update(self.cleanup_log_files())
                results.update(self.cleanup_backup_files())
                results.update(self.cleanup_generated_content())
            
            # Cache cleanup
            if 'cache' not in skip_categories:
                results.update(self.cleanup_redis_cache())
            
            # Database optimization
            if 'optimization' not in skip_categories:
                optimization_results = self.optimize_database()
                results['database_optimization'] = optimization_results
            
            # Generate report
            report = self.generate_cleanup_report(results)
            self.logger.info(f"\n{report}")
            
            # Save report to file
            report_file = f"cleanup_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report)
            
            self.logger.info(f"📊 Cleanup report saved to: {report_file}")
            self.logger.info("✅ System cleanup completed successfully!")
            
            return results
            
        except Exception as e:
            self.logger.error(f"System cleanup failed: {str(e)}")
            raise
        finally:
            self.disconnect_services()

def main():
    """Main function with CLI interface"""
    parser = argparse.ArgumentParser(description="AI Content Factory System Cleanup Tool")
    parser.add_argument('--config', '-c', help='Path to cleanup config file')
    parser.add_argument('--skip', '-s', nargs='+',
                       choices=['database', 'filesystem', 'cache', 'optimization'],
                       help='Categories to skip during cleanup')
    parser.add_argument('--dry-run', '-d', action='store_true',
                       help='Show what would be cleaned without actually doing it')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = 'DEBUG' if args.verbose else 'INFO'
    logger = setup_logger("cleanup_main", level=log_level)
    
    if args.dry_run:
        logger.info("🔍 DRY RUN MODE - No actual cleanup will be performed")
        # Here you would implement dry run logic
        return
    
    # Run cleanup
    cleaner = SystemCleaner(args.config)
    
    try:
        results = cleaner.run_full_cleanup(args.skip)
        logger.info("System cleanup completed successfully! 🎉")
        sys.exit(0)
    except Exception as e:
        logger.error(f"System cleanup failed: {str(e)} ❌")
        sys.exit(1)

if __name__ == "__main__":
    main()024)
            self.logger.info(f"Cleaned up {cleaned_files} temporary files, freed {freed_space_mb:.2f} MB")
            
            return {
                'temp_files_deleted': cleaned_files,
                'space_freed_mb': round(freed_space_mb, 2)
            }
            
        except Exception as e:
            self.logger.error(f"Temporary files cleanup failed: {str(e)}")
            return {'temp_files_deleted': 0, 'space_freed_mb': 0}
    
    def cleanup_log_files(self) -> Dict[str, int]:
        """Clean up old log files"""
        try:
            self.logger.info("Starting log files cleanup...")
            
            retention_days = self.config['cleanup_settings']['log_files_retention_days']
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            log_dir = self.config['directories']['log_dir']
            
            if not os.path.exists(log_dir):
                self.logger.info("Log directory does not exist")
                return {'log_files_deleted': 0}
            
            cleaned_files = 0
            freed_space = 0
            
            for file in os.listdir(log_dir):
                if not file.endswith('.log'):
                    continue
                    
                file_path = os.path.join(log_dir, file)
                
                try:
                    file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                    
                    if file_mtime < cutoff_date:
                        file_size = os.path.getsize(file_path)
                        os.remove(file_path)
                        cleaned_files += 1
                        freed_space += file_size
                        
                except Exception as e:
                    self.logger.warning(f"Could not delete log file {file_path}: {str(e)}")
            
            freed_space_mb = freed_space / (1024 * 1024)
            self.logger.info(f"Cleaned up {cleaned_files} log files, freed {freed_space_mb:.2f} MB")
            
            return {
                'log_files_deleted': cleaned_files,
                'log_space_freed_mb': round(freed_space_mb, 2)
            }
            
        except Exception as e:
            self.logger.error(f"Log files cleanup failed: {str(e)}")
            return {'log_files_deleted': 0, 'log_space_freed_mb': 0}
    
    def cleanup_backup_files(self) -> Dict[str, int]:
        """Clean up old backup files"""
        try:
            self.logger.info("Starting backup files cleanup...")
            
            retention_days = self.config['cleanup_settings']['backup_files_retention_days']
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            backup_dir = self.config['directories']['backup_dir']
            
            if not os.path.exists(backup_dir):
                self.logger.info("Backup directory does not exist")
                return {'backup_files_deleted': 0}
            
            cleaned_files = 0
            freed_space = 0
            
            for file in os.listdir(backup_dir):
                if not (file.endswith('.sql') or file.endswith('.dump')):
                    continue
                    
                file_path = os.path.join(backup_dir, file)
                
                try:
                    file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                    
                    if file_mtime < cutoff_date:
                        file_size = os.path.getsize(file_path)
                        os.remove(file_path)
                        cleaned_files += 1
                        freed_space += file_size
                        
                except Exception as e:
                    self.logger.warning(f"Could not delete backup file {file_path}: {str(e)}")
            
            freed_space_mb = freed_space / (1024 * 1