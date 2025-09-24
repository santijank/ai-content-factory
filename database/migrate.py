#!/usr/bin/env python3
"""
Database Migration Runner
Simplified interface for running database migrations
"""

import os
import sys
import logging
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from init_database import DatabaseInitializer

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main migration runner"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Database Migration Runner')
    parser.add_argument('command', choices=['init', 'migrate', 'reset', 'status', 'cleanup'], 
                       help='Migration command to run')
    parser.add_argument('--config', help='Configuration file path')
    parser.add_argument('--force', action='store_true', help='Force operation without confirmation')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without executing')
    
    args = parser.parse_args()
    
    try:
        db_init = DatabaseInitializer(args.config)
        
        if args.command == 'init':
            logger.info("Initializing database...")
            if args.dry_run:
                logger.info("DRY RUN: Would initialize database with all migrations")
            else:
                db_init.initialize_database()
                
        elif args.command == 'migrate':
            logger.info("Running migrations...")
            if args.dry_run:
                logger.info("DRY RUN: Would run pending migrations")
                # Show pending migrations
                db_init.connection = db_init.connect_main()
                applied = set(db_init.get_applied_migrations())
                
                migrations_path = Path(__file__).parent / 'migrations'
                all_migrations = [f.stem for f in sorted(migrations_path.glob('*.sql'))]
                pending = [m for m in all_migrations if m not in applied]
                
                if pending:
                    logger.info(f"Pending migrations: {', '.join(pending)}")
                else:
                    logger.info("No pending migrations")
                    
                db_init.connection.close()
            else:
                db_init.connection = db_init.connect_main()
                db_init.create_migration_table()
                db_init.run_migrations()
                db_init.connection.close()
                
        elif args.command == 'reset':
            if not args.force:
                confirm = input("This will DELETE ALL DATA. Are you sure? (yes/no): ")
                if confirm.lower() != 'yes':
                    logger.info("Reset cancelled")
                    return
                    
            logger.info("Resetting database...")
            if args.dry_run:
                logger.info("DRY RUN: Would reset entire database")
            else:
                db_init.reset_database()
                
        elif args.command == 'status':
            logger.info("Checking migration status...")
            db_init.connection = db_init.connect_main()
            
            applied = db_init.get_applied_migrations()
            migrations_path = Path(__file__).parent / 'migrations'
            all_migrations = [f.stem for f in sorted(migrations_path.glob('*.sql'))]
            pending = [m for m in all_migrations if m not in applied]
            
            logger.info(f"Applied migrations ({len(applied)}):")
            for migration in applied:
                logger.info(f"  ✓ {migration}")
                
            if pending:
                logger.info(f"Pending migrations ({len(pending)}):")
                for migration in pending:
                    logger.info(f"  ○ {migration}")
            else:
                logger.info("All migrations are up to date!")
                
            db_init.connection.close()
            
        elif args.command == 'cleanup':
            logger.info("Running database cleanup...")
            if args.dry_run:
                logger.info("DRY RUN: Would run cleanup functions")
            else:
                db_init.connection = db_init.connect_main()
                cursor = db_init.connection.cursor()
                
                # Run cleanup functions
                cursor.execute("SELECT cleanup_old_trends(30)")
                trends_cleaned = cursor.fetchone()[0]
                logger.info(f"Cleaned up {trends_cleaned} old trends")
                
                cursor.execute("SELECT expire_old_opportunities(72)")
                opportunities_expired = cursor.fetchone()[0] 
                logger.info(f"Expired {opportunities_expired} old opportunities")
                
                cursor.execute("SELECT cleanup_old_uploads(180)")
                uploads_cleaned = cursor.fetchone()[0]
                logger.info(f"Cleaned up {uploads_cleaned} old uploads")
                
                cursor.execute("SELECT cleanup_old_performance_metrics(365)")
                metrics_cleaned = cursor.fetchone()[0]
                logger.info(f"Cleaned up {metrics_cleaned} old performance metrics")
                
                db_init.connection.commit()
                db_init.connection.close()
                
                logger.info("Database cleanup completed")
                
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)
        
    logger.info("Migration operation completed successfully")

if __name__ == '__main__':
    main()