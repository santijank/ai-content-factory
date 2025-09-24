#!/usr/bin/env python3
"""
Database initialization and migration script
Creates all necessary tables and indexes for the AI Content Factory system
"""

import os
import sys
import logging
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import yaml

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DatabaseInitializer:
    """Initialize and migrate database"""
    
    def __init__(self, config_path: str = None):
        self.config = self._load_config(config_path)
        self.migrations_path = Path(__file__).parent / 'migrations'
        self.connection = None
        
    def _load_config(self, config_path: str = None) -> dict:
        """Load database configuration"""
        # Default configuration
        default_config = {
            'database': {
                'host': os.environ.get('DB_HOST', 'localhost'),
                'port': int(os.environ.get('DB_PORT', 5432)),
                'database': os.environ.get('DB_NAME', 'content_factory'),
                'user': os.environ.get('DB_USER', 'postgres'),
                'password': os.environ.get('DB_PASSWORD', 'postgres'),
                'admin_database': 'postgres'  # For creating database
            }
        }
        
        # Load from config file if provided
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    file_config = yaml.safe_load(f)
                    if file_config and 'database' in file_config:
                        default_config['database'].update(file_config['database'])
                        logger.info(f"Loaded database config from {config_path}")
            except Exception as e:
                logger.warning(f"Failed to load config from {config_path}: {e}")
        
        return default_config
    
    def connect_admin(self):
        """Connect to admin database (for creating main database)"""
        try:
            db_config = self.config['database'].copy()
            db_config['database'] = db_config['admin_database']
            
            connection = psycopg2.connect(**{k: v for k, v in db_config.items() if k != 'admin_database'})
            connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            return connection
        except Exception as e:
            logger.error(f"Failed to connect to admin database: {e}")
            raise
    
    def connect_main(self):
        """Connect to main application database"""
        try:
            db_config = self.config['database'].copy()
            db_config.pop('admin_database', None)
            
            connection = psycopg2.connect(**db_config)
            return connection
        except Exception as e:
            logger.error(f"Failed to connect to main database: {e}")
            raise
    
    def create_database_if_not_exists(self):
        """Create main database if it doesn't exist"""
        admin_conn = None
        try:
            admin_conn = self.connect_admin()
            cursor = admin_conn.cursor()
            
            db_name = self.config['database']['database']
            
            # Check if database exists
            cursor.execute(
                "SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s",
                (db_name,)
            )
            
            if cursor.fetchone():
                logger.info(f"Database '{db_name}' already exists")
            else:
                # Create database
                cursor.execute(
                    sql.SQL("CREATE DATABASE {} OWNER {}").format(
                        sql.Identifier(db_name),
                        sql.Identifier(self.config['database']['user'])
                    )
                )
                logger.info(f"Created database '{db_name}'")
            
            cursor.close()
            
        finally:
            if admin_conn:
                admin_conn.close()
    
    def create_migration_table(self):
        """Create migrations tracking table"""
        try:
            cursor = self.connection.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    id SERIAL PRIMARY KEY,
                    migration_name VARCHAR(255) NOT NULL UNIQUE,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    checksum VARCHAR(64)
                )
            """)
            
            # Create index
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_schema_migrations_name 
                ON schema_migrations(migration_name)
            """)
            
            self.connection.commit()
            logger.info("Created schema_migrations table")
            
        except Exception as e:
            logger.error(f"Failed to create migration table: {e}")
            self.connection.rollback()
            raise
    
    def get_applied_migrations(self):
        """Get list of applied migrations"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                "SELECT migration_name FROM schema_migrations ORDER BY migration_name"
            )
            return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get applied migrations: {e}")
            return []
    
    def apply_migration(self, migration_file: Path):
        """Apply a single migration file"""
        try:
            migration_name = migration_file.stem
            
            # Check if already applied
            cursor = self.connection.cursor()
            cursor.execute(
                "SELECT 1 FROM schema_migrations WHERE migration_name = %s",
                (migration_name,)
            )
            
            if cursor.fetchone():
                logger.info(f"Migration {migration_name} already applied, skipping")
                return True
            
            # Read migration file
            with open(migration_file, 'r', encoding='utf-8') as f:
                migration_sql = f.read()
            
            if not migration_sql.strip():
                logger.warning(f"Migration {migration_name} is empty, skipping")
                return True
            
            # Apply migration
            logger.info(f"Applying migration: {migration_name}")
            
            # Execute migration SQL
            cursor.execute(migration_sql)
            
            # Record migration as applied
            import hashlib
            checksum = hashlib.md5(migration_sql.encode()).hexdigest()
            
            cursor.execute("""
                INSERT INTO schema_migrations (migration_name, checksum)
                VALUES (%s, %s)
            """, (migration_name, checksum))
            
            self.connection.commit()
            logger.info(f"Successfully applied migration: {migration_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to apply migration {migration_file.name}: {e}")
            self.connection.rollback()
            raise
    
    def run_migrations(self):
        """Run all pending migrations"""
        if not self.migrations_path.exists():
            logger.warning(f"Migrations directory {self.migrations_path} not found")
            return
        
        # Get migration files
        migration_files = sorted([
            f for f in self.migrations_path.glob('*.sql')
            if f.is_file()
        ])
        
        if not migration_files:
            logger.info("No migration files found")
            return
        
        applied_migrations = set(self.get_applied_migrations())
        pending_migrations = [
            f for f in migration_files
            if f.stem not in applied_migrations
        ]
        
        if not pending_migrations:
            logger.info("All migrations are up to date")
            return
        
        logger.info(f"Found {len(pending_migrations)} pending migrations")
        
        for migration_file in pending_migrations:
            try:
                self.apply_migration(migration_file)
            except Exception as e:
                logger.error(f"Migration failed: {migration_file.name}")
                raise
        
        logger.info("All migrations completed successfully")
    
    def create_indexes(self):
        """Create additional indexes for performance"""
        indexes = [
            # Trends table indexes
            "CREATE INDEX IF NOT EXISTS idx_trends_source ON trends(source)",
            "CREATE INDEX IF NOT EXISTS idx_trends_collected_at ON trends(collected_at DESC)",
            "CREATE INDEX IF NOT EXISTS idx_trends_popularity_score ON trends(popularity_score DESC)",
            "CREATE INDEX IF NOT EXISTS idx_trends_category ON trends(category)",
            "CREATE INDEX IF NOT EXISTS idx_trends_region ON trends(region)",
            "CREATE INDEX IF NOT EXISTS idx_trends_topic_text ON trends USING gin(to_tsvector('english', topic))",
            
            # Content opportunities indexes
            "CREATE INDEX IF NOT EXISTS idx_opportunities_trend_id ON content_opportunities(trend_id)",
            "CREATE INDEX IF NOT EXISTS idx_opportunities_priority_score ON content_opportunities(priority_score DESC)",
            "CREATE INDEX IF NOT EXISTS idx_opportunities_status ON content_opportunities(status)",
            "CREATE INDEX IF NOT EXISTS idx_opportunities_created_at ON content_opportunities(created_at DESC)",
            
            # Content items indexes
            "CREATE INDEX IF NOT EXISTS idx_content_opportunity_id ON content_items(opportunity_id)",
            "CREATE INDEX IF NOT EXISTS idx_content_production_status ON content_items(production_status)",
            "CREATE INDEX IF NOT EXISTS idx_content_created_at ON content_items(created_at DESC)",
            
            # Uploads indexes
            "CREATE INDEX IF NOT EXISTS idx_uploads_content_id ON uploads(content_id)",
            "CREATE INDEX IF NOT EXISTS idx_uploads_platform ON uploads(platform)",
            "CREATE INDEX IF NOT EXISTS idx_uploads_uploaded_at ON uploads(uploaded_at DESC)",
            
            # Performance metrics indexes
            "CREATE INDEX IF NOT EXISTS idx_performance_upload_id ON performance_metrics(upload_id)",
            "CREATE INDEX IF NOT EXISTS idx_performance_measured_at ON performance_metrics(measured_at DESC)",
            "CREATE INDEX IF NOT EXISTS idx_performance_views ON performance_metrics(views DESC)",
            "CREATE INDEX IF NOT EXISTS idx_performance_revenue ON performance_metrics(revenue DESC)",
        ]
        
        try:
            cursor = self.connection.cursor()
            
            for index_sql in indexes:
                try:
                    cursor.execute(index_sql)
                    logger.debug(f"Created index: {index_sql.split()[5]}")  # Extract index name
                except Exception as e:
                    logger.warning(f"Failed to create index: {e}")
            
            self.connection.commit()
            logger.info("Created performance indexes")
            
        except Exception as e:
            logger.error(f"Failed to create indexes: {e}")
            self.connection.rollback()
    
    def create_functions_and_triggers(self):
        """Create database functions and triggers"""
        functions_sql = """
        -- Function to update updated_at timestamp
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql';
        
        -- Function to calculate trend popularity percentile
        CREATE OR REPLACE FUNCTION calculate_trend_percentile(score FLOAT)
        RETURNS INTEGER AS $$
        BEGIN
            RETURN (
                SELECT PERCENTILE_CONT(score) WITHIN GROUP (ORDER BY popularity_score)
                FROM trends
                WHERE collected_at >= CURRENT_TIMESTAMP - INTERVAL '24 hours'
            )::INTEGER;
        END;
        $$ language 'plpgsql';
        
        -- Function to get trending topics by category
        CREATE OR REPLACE FUNCTION get_trending_by_category(
            category_name VARCHAR DEFAULT 'all',
            hours_back INTEGER DEFAULT 24,
            limit_count INTEGER DEFAULT 10
        )
        RETURNS TABLE (
            topic VARCHAR,
            popularity_score FLOAT,
            growth_rate FLOAT,
            source VARCHAR,
            collected_at TIMESTAMP
        ) AS $$
        BEGIN
            RETURN QUERY
            SELECT t.topic, t.popularity_score, t.growth_rate, t.source, t.collected_at
            FROM trends t
            WHERE 
                (category_name = 'all' OR t.category = category_name)
                AND t.collected_at >= CURRENT_TIMESTAMP - (hours_back || ' hours')::INTERVAL
            ORDER BY t.popularity_score DESC
            LIMIT limit_count;
        END;
        $$ language 'plpgsql';
        """
        
        try:
            cursor = self.connection.cursor()
            cursor.execute(functions_sql)
            self.connection.commit()
            logger.info("Created database functions and triggers")
            
        except Exception as e:
            logger.error(f"Failed to create functions: {e}")
            self.connection.rollback()
    
    def seed_initial_data(self):
        """Seed database with initial reference data"""
        seed_data = {
            # Add any initial data here if needed
            'platform_types': [
                'youtube', 'tiktok', 'instagram', 'facebook', 'twitter', 'linkedin'
            ],
            'content_statuses': [
                'pending', 'in_progress', 'completed', 'published', 'archived'
            ]
        }
        
        logger.info("Initial data seeding completed (no data to seed currently)")
    
    def initialize_database(self):
        """Complete database initialization"""
        try:
            logger.info("Starting database initialization...")
            
            # Step 1: Create database if needed
            self.create_database_if_not_exists()
            
            # Step 2: Connect to main database
            self.connection = self.connect_main()
            
            # Step 3: Create migration tracking table
            self.create_migration_table()
            
            # Step 4: Run migrations
            self.run_migrations()
            
            # Step 5: Create additional indexes
            self.create_indexes()
            
            # Step 6: Create functions and triggers
            self.create_functions_and_triggers()
            
            # Step 7: Seed initial data
            self.seed_initial_data()
            
            logger.info("Database initialization completed successfully!")
            
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise
        finally:
            if self.connection:
                self.connection.close()
    
    def reset_database(self):
        """Reset database (DROP and recreate all tables)"""
        try:
            admin_conn = self.connect_admin()
            cursor = admin_conn.cursor()
            
            db_name = self.config['database']['database']
            
            # Terminate existing connections
            cursor.execute(f"""
                SELECT pg_terminate_backend(pid)
                FROM pg_stat_activity
                WHERE datname = '{db_name}' AND pid <> pg_backend_pid()
            """)
            
            # Drop and recreate database
            cursor.execute(f"DROP DATABASE IF EXISTS {db_name}")
            cursor.execute(f"CREATE DATABASE {db_name}")
            
            admin_conn.close()
            
            logger.info(f"Reset database '{db_name}' successfully")
            
            # Re-initialize
            self.initialize_database()
            
        except Exception as e:
            logger.error(f"Failed to reset database: {e}")
            raise

def main():
    """Main function for command line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Database initialization and migration')
    parser.add_argument('--config', help='Configuration file path')
    parser.add_argument('--reset', action='store_true', help='Reset database (destructive)')
    parser.add_argument('--migrate-only', action='store_true', help='Run migrations only')
    parser.add_argument('--create-only', action='store_true', help='Create database only')
    
    args = parser.parse_args()
    
    try:
        db_init = DatabaseInitializer(args.config)
        
        if args.reset:
            confirm = input("This will DELETE ALL DATA. Are you sure? (yes/no): ")
            if confirm.lower() == 'yes':
                db_init.reset_database()
            else:
                logger.info("Database reset cancelled")
                
        elif args.create_only:
            db_init.create_database_if_not_exists()
            logger.info("Database creation completed")
            
        elif args.migrate_only:
            db_init.connection = db_init.connect_main()
            db_init.create_migration_table()
            db_init.run_migrations()
            db_init.connection.close()
            logger.info("Migrations completed")
            
        else:
            db_init.initialize_database()
            
    except Exception as e:
        logger.error(f"Operation failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()