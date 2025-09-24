#!/usr/bin/env python3
"""
Data Migration Script for AI Content Factory
ใช้สำหรับ migrate ข้อมูลระหว่าง database versions และ environments
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime
from typing import Dict, List, Any, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
import yaml

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.utils.logger import setup_logger
from shared.utils.error_handler import ErrorHandler
from database.repositories.trend_repository import TrendRepository
from database.repositories.opportunity_repository import OpportunityRepository
from database.repositories.content_repository import ContentRepository

class DataMigrator:
    """Main class for handling data migrations"""
    
    def __init__(self, config_path: str = None):
        self.logger = setup_logger("data_migrator")
        self.error_handler = ErrorHandler()
        self.config = self._load_config(config_path)
        self.source_conn = None
        self.target_conn = None
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load migration configuration"""
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        
        # Default configuration
        return {
            'source_db': {
                'host': os.getenv('SOURCE_DB_HOST', 'localhost'),
                'port': int(os.getenv('SOURCE_DB_PORT', 5432)),
                'database': os.getenv('SOURCE_DB_NAME', 'content_factory_old'),
                'user': os.getenv('SOURCE_DB_USER', 'admin'),
                'password': os.getenv('SOURCE_DB_PASSWORD', 'password')
            },
            'target_db': {
                'host': os.getenv('TARGET_DB_HOST', 'localhost'),
                'port': int(os.getenv('TARGET_DB_PORT', 5432)),
                'database': os.getenv('TARGET_DB_NAME', 'content_factory'),
                'user': os.getenv('TARGET_DB_USER', 'admin'),
                'password': os.getenv('TARGET_DB_PASSWORD', 'password')
            },
            'migration_settings': {
                'batch_size': 1000,
                'backup_before_migration': True,
                'verify_after_migration': True,
                'log_level': 'INFO'
            }
        }
    
    def connect_databases(self):
        """Establish connections to source and target databases"""
        try:
            # Source database connection
            self.source_conn = psycopg2.connect(**self.config['source_db'])
            self.logger.info("Connected to source database")
            
            # Target database connection
            self.target_conn = psycopg2.connect(**self.config['target_db'])
            self.logger.info("Connected to target database")
            
        except Exception as e:
            self.logger.error(f"Database connection failed: {str(e)}")
            raise
    
    def disconnect_databases(self):
        """Close database connections"""
        if self.source_conn:
            self.source_conn.close()
            self.logger.info("Disconnected from source database")
        
        if self.target_conn:
            self.target_conn.close()
            self.logger.info("Disconnected from target database")
    
    def create_backup(self, tables: List[str] = None) -> str:
        """Create backup of target database before migration"""
        if not self.config['migration_settings']['backup_before_migration']:
            return None
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"backup_before_migration_{timestamp}.sql"
        backup_path = os.path.join("database/backup", backup_file)
        
        # Ensure backup directory exists
        os.makedirs(os.path.dirname(backup_path), exist_ok=True)
        
        try:
            # Create pg_dump command
            db_config = self.config['target_db']
            cmd = [
                'pg_dump',
                f"--host={db_config['host']}",
                f"--port={db_config['port']}",
                f"--username={db_config['user']}",
                f"--dbname={db_config['database']}",
                '--no-password',
                '--verbose',
                '--clean',
                '--no-acl',
                '--no-owner',
                f"--file={backup_path}"
            ]
            
            if tables:
                for table in tables:
                    cmd.extend(['--table', table])
            
            # Set password environment variable
            env = os.environ.copy()
            env['PGPASSWORD'] = db_config['password']
            
            import subprocess
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.logger.info(f"Backup created successfully: {backup_path}")
                return backup_path
            else:
                self.logger.error(f"Backup failed: {result.stderr}")
                return None
                
        except Exception as e:
            self.logger.error(f"Backup creation failed: {str(e)}")
            return None
    
    def migrate_trends(self) -> bool:
        """Migrate trends data"""
        try:
            self.logger.info("Starting trends migration...")
            
            # Get data from source
            with self.source_conn.cursor(cursor_factory=RealDictCursor) as source_cur:
                source_cur.execute("""
                    SELECT * FROM trends 
                    ORDER BY collected_at DESC
                """)
                trends_data = source_cur.fetchall()
            
            self.logger.info(f"Found {len(trends_data)} trends to migrate")
            
            # Insert into target
            with self.target_conn.cursor() as target_cur:
                batch_size = self.config['migration_settings']['batch_size']
                
                for i in range(0, len(trends_data), batch_size):
                    batch = trends_data[i:i + batch_size]
                    
                    for trend in batch:
                        target_cur.execute("""
                            INSERT INTO trends (
                                id, source, topic, keywords, popularity_score,
                                growth_rate, category, region, collected_at, raw_data
                            ) VALUES (
                                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                            ) ON CONFLICT (id) DO UPDATE SET
                                popularity_score = EXCLUDED.popularity_score,
                                growth_rate = EXCLUDED.growth_rate,
                                raw_data = EXCLUDED.raw_data
                        """, (
                            trend['id'], trend['source'], trend['topic'],
                            json.dumps(trend['keywords']) if trend['keywords'] else None,
                            trend['popularity_score'], trend['growth_rate'],
                            trend['category'], trend['region'],
                            trend['collected_at'],
                            json.dumps(trend['raw_data']) if trend['raw_data'] else None
                        ))
                    
                    self.target_conn.commit()
                    self.logger.info(f"Migrated batch {i//batch_size + 1}/{(len(trends_data)-1)//batch_size + 1}")
            
            self.logger.info("Trends migration completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Trends migration failed: {str(e)}")
            self.target_conn.rollback()
            return False
    
    def migrate_opportunities(self) -> bool:
        """Migrate content opportunities data"""
        try:
            self.logger.info("Starting opportunities migration...")
            
            with self.source_conn.cursor(cursor_factory=RealDictCursor) as source_cur:
                source_cur.execute("""
                    SELECT * FROM content_opportunities 
                    ORDER BY created_at DESC
                """)
                opportunities_data = source_cur.fetchall()
            
            self.logger.info(f"Found {len(opportunities_data)} opportunities to migrate")
            
            with self.target_conn.cursor() as target_cur:
                batch_size = self.config['migration_settings']['batch_size']
                
                for i in range(0, len(opportunities_data), batch_size):
                    batch = opportunities_data[i:i + batch_size]
                    
                    for opp in batch:
                        target_cur.execute("""
                            INSERT INTO content_opportunities (
                                id, trend_id, suggested_angle, estimated_views,
                                competition_level, production_cost, estimated_roi,
                                priority_score, status, created_at
                            ) VALUES (
                                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                            ) ON CONFLICT (id) DO UPDATE SET
                                status = EXCLUDED.status,
                                priority_score = EXCLUDED.priority_score
                        """, (
                            opp['id'], opp['trend_id'], opp['suggested_angle'],
                            opp['estimated_views'], opp['competition_level'],
                            opp['production_cost'], opp['estimated_roi'],
                            opp['priority_score'], opp['status'], opp['created_at']
                        ))
                    
                    self.target_conn.commit()
                    self.logger.info(f"Migrated batch {i//batch_size + 1}/{(len(opportunities_data)-1)//batch_size + 1}")
            
            self.logger.info("Opportunities migration completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Opportunities migration failed: {str(e)}")
            self.target_conn.rollback()
            return False
    
    def migrate_content_items(self) -> bool:
        """Migrate content items data"""
        try:
            self.logger.info("Starting content items migration...")
            
            with self.source_conn.cursor(cursor_factory=RealDictCursor) as source_cur:
                source_cur.execute("""
                    SELECT * FROM content_items 
                    ORDER BY created_at DESC
                """)
                content_data = source_cur.fetchall()
            
            self.logger.info(f"Found {len(content_data)} content items to migrate")
            
            with self.target_conn.cursor() as target_cur:
                batch_size = self.config['migration_settings']['batch_size']
                
                for i in range(0, len(content_data), batch_size):
                    batch = content_data[i:i + batch_size]
                    
                    for content in batch:
                        target_cur.execute("""
                            INSERT INTO content_items (
                                id, opportunity_id, title, description,
                                content_plan, production_status, assets,
                                cost_breakdown, created_at, completed_at
                            ) VALUES (
                                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                            ) ON CONFLICT (id) DO UPDATE SET
                                production_status = EXCLUDED.production_status,
                                completed_at = EXCLUDED.completed_at
                        """, (
                            content['id'], content['opportunity_id'],
                            content['title'], content['description'],
                            json.dumps(content['content_plan']) if content['content_plan'] else None,
                            content['production_status'],
                            json.dumps(content['assets']) if content['assets'] else None,
                            json.dumps(content['cost_breakdown']) if content['cost_breakdown'] else None,
                            content['created_at'], content['completed_at']
                        ))
                    
                    self.target_conn.commit()
                    self.logger.info(f"Migrated batch {i//batch_size + 1}/{(len(content_data)-1)//batch_size + 1}")
            
            self.logger.info("Content items migration completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Content items migration failed: {str(e)}")
            self.target_conn.rollback()
            return False
    
    def verify_migration(self) -> bool:
        """Verify migration data integrity"""
        if not self.config['migration_settings']['verify_after_migration']:
            return True
            
        try:
            self.logger.info("Starting migration verification...")
            
            verification_results = {}
            
            # Verify trends count
            with self.source_conn.cursor() as source_cur:
                source_cur.execute("SELECT COUNT(*) FROM trends")
                source_trends_count = source_cur.fetchone()[0]
            
            with self.target_conn.cursor() as target_cur:
                target_cur.execute("SELECT COUNT(*) FROM trends")
                target_trends_count = target_cur.fetchone()[0]
            
            verification_results['trends'] = {
                'source_count': source_trends_count,
                'target_count': target_trends_count,
                'match': source_trends_count == target_trends_count
            }
            
            # Verify opportunities count
            with self.source_conn.cursor() as source_cur:
                source_cur.execute("SELECT COUNT(*) FROM content_opportunities")
                source_opp_count = source_cur.fetchone()[0]
            
            with self.target_conn.cursor() as target_cur:
                target_cur.execute("SELECT COUNT(*) FROM content_opportunities")
                target_opp_count = target_cur.fetchone()[0]
            
            verification_results['opportunities'] = {
                'source_count': source_opp_count,
                'target_count': target_opp_count,
                'match': source_opp_count == target_opp_count
            }
            
            # Log verification results
            all_verified = True
            for table, results in verification_results.items():
                if results['match']:
                    self.logger.info(f"✅ {table}: {results['target_count']} records migrated successfully")
                else:
                    self.logger.error(f"❌ {table}: Source={results['source_count']}, Target={results['target_count']}")
                    all_verified = False
            
            return all_verified
            
        except Exception as e:
            self.logger.error(f"Migration verification failed: {str(e)}")
            return False
    
    def run_migration(self, tables: List[str] = None) -> bool:
        """Run complete migration process"""
        try:
            # Connect to databases
            self.connect_databases()
            
            # Create backup
            backup_path = self.create_backup(tables)
            if backup_path:
                self.logger.info(f"Backup created at: {backup_path}")
            
            # Run migrations
            migration_results = {}
            
            if not tables or 'trends' in tables:
                migration_results['trends'] = self.migrate_trends()
            
            if not tables or 'content_opportunities' in tables:
                migration_results['opportunities'] = self.migrate_opportunities()
            
            if not tables or 'content_items' in tables:
                migration_results['content_items'] = self.migrate_content_items()
            
            # Verify migration
            verification_passed = self.verify_migration()
            
            # Summary
            all_successful = all(migration_results.values()) and verification_passed
            
            if all_successful:
                self.logger.info("🎉 Migration completed successfully!")
            else:
                self.logger.error("❌ Migration completed with errors")
                for table, success in migration_results.items():
                    status = "✅" if success else "❌"
                    self.logger.info(f"{status} {table}: {'Success' if success else 'Failed'}")
            
            return all_successful
            
        except Exception as e:
            self.logger.error(f"Migration process failed: {str(e)}")
            return False
        finally:
            self.disconnect_databases()

def main():
    """Main function with CLI interface"""
    parser = argparse.ArgumentParser(description="AI Content Factory Data Migration Tool")
    parser.add_argument('--config', '-c', help='Path to migration config file')
    parser.add_argument('--tables', '-t', nargs='+', 
                       choices=['trends', 'content_opportunities', 'content_items'],
                       help='Specific tables to migrate (default: all)')
    parser.add_argument('--dry-run', '-d', action='store_true',
                       help='Show what would be migrated without actually doing it')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = 'DEBUG' if args.verbose else 'INFO'
    logger = setup_logger("migration_main", level=log_level)
    
    if args.dry_run:
        logger.info("🔍 DRY RUN MODE - No actual migration will be performed")
        # Here you would implement dry run logic
        return
    
    # Run migration
    migrator = DataMigrator(args.config)
    success = migrator.run_migration(args.tables)
    
    if success:
        logger.info("Migration completed successfully! 🎉")
        sys.exit(0)
    else:
        logger.error("Migration failed! ❌")
        sys.exit(1)

if __name__ == "__main__":
    main()