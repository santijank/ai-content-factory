#!/usr/bin/env python3
"""
Database Backup Script for AI Content Factory
ใช้สำหรับสำรองข้อมูล database แบบอัตโนมัติ พร้อม compression และ retention policy
"""

import os
import sys
import shutil
import gzip
import logging
import argparse
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import psycopg2
import boto3
from botocore.exceptions import ClientError
import yaml
import schedule
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.utils.logger import setup_logger
from shared.utils.error_handler import ErrorHandler

class DatabaseBackup:
    """Main class for database backup operations"""
    
    def __init__(self, config_path: str = None):
        self.logger = setup_logger("database_backup")
        self.error_handler = ErrorHandler()
        self.config = self._load_config(config_path)
        self.db_conn = None
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load backup configuration"""
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
            'backup_settings': {
                'local_backup_dir': 'database/backup',
                'backup_format': 'custom',  # custom, plain, tar
                'compression_level': 6,
                'retention_days': 30,
                'max_local_backups': 10,
                'backup_name_format': 'content_factory_backup_{timestamp}',
                'include_tables': [],  # Empty means all tables
                'exclude_tables': [],
                'verify_backup': True
            },
            's3_settings': {
                'enabled': False,
                'bucket_name': os.getenv('BACKUP_S3_BUCKET', ''),
                'region': os.getenv('AWS_REGION', 'us-east-1'),
                'access_key': os.getenv('AWS_ACCESS_KEY_ID', ''),
                'secret_key': os.getenv('AWS_SECRET_ACCESS_KEY', ''),
                'storage_class': 'STANDARD_IA',  # STANDARD, STANDARD_IA, GLACIER
                'encryption': True
            },
            'notification_settings': {
                'enabled': False,
                'smtp_host': os.getenv('SMTP_HOST', ''),
                'smtp_port': int(os.getenv('SMTP_PORT', 587)),
                'smtp_user': os.getenv('SMTP_USER', ''),
                'smtp_password': os.getenv('SMTP_PASSWORD', ''),
                'from_email': os.getenv('BACKUP_FROM_EMAIL', ''),
                'to_emails': os.getenv('BACKUP_TO_EMAILS', '').split(','),
                'notify_on_success': True,
                'notify_on_failure': True
            },
            'schedule_settings': {
                'enabled': False,
                'daily_time': '02:00',
                'weekly_day': 'sunday',
                'weekly_time': '03:00',
                'monthly_day': 1,
                'monthly_time': '04:00'
            }
        }
    
    def create_backup_directory(self) -> str:
        """Create and return backup directory path"""
        backup_dir = self.config['backup_settings']['local_backup_dir']
        os.makedirs(backup_dir, exist_ok=True)
        return backup_dir
    
    def generate_backup_filename(self, backup_type: str = 'manual') -> str:
        """Generate backup filename with timestamp"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        name_format = self.config['backup_settings']['backup_name_format']
        
        filename = name_format.format(
            timestamp=timestamp,
            type=backup_type,
            date=datetime.now().strftime('%Y%m%d')
        )
        
        # Add appropriate extension based on format
        backup_format = self.config['backup_settings']['backup_format']
        if backup_format == 'custom':
            filename += '.dump'
        elif backup_format == 'plain':
            filename += '.sql'
        elif backup_format == 'tar':
            filename += '.tar'
        
        return filename
    
    def create_pg_dump(self, output_file: str) -> bool:
        """Create PostgreSQL dump using pg_dump"""
        try:
            db_config = self.config['database']
            backup_settings = self.config['backup_settings']
            
            # Build pg_dump command
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
                '--no-owner'
            ]
            
            # Add format option
            backup_format = backup_settings['backup_format']
            if backup_format == 'custom':
                cmd.extend(['--format=custom'])
                cmd.extend([f"--compress={backup_settings['compression_level']}"])
            elif backup_format == 'tar':
                cmd.extend(['--format=tar'])
            elif backup_format == 'plain':
                cmd.extend(['--format=plain'])
            
            # Add table inclusion/exclusion
            if backup_settings['include_tables']:
                for table in backup_settings['include_tables']:
                    cmd.extend(['--table', table])
            
            for table in backup_settings['exclude_tables']:
                cmd.extend(['--exclude-table', table])
            
            # Add output file
            cmd.extend(['--file', output_file])
            
            # Set environment variables
            env = os.environ.copy()
            env['PGPASSWORD'] = db_config['password']
            
            # Run pg_dump
            self.logger.info(f"Starting database backup to {output_file}")
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                # Get file size
                file_size = os.path.getsize(output_file) / (1024 * 1024)  # MB
                self.logger.info(f"Backup completed successfully. Size: {file_size:.2f} MB")
                return True
            else:
                self.logger.error(f"pg_dump failed: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Backup creation failed: {str(e)}")
            return False
    
    def compress_backup(self, backup_file: str) -> str:
        """Compress backup file using gzip"""
        try:
            compressed_file = backup_file + '.gz'
            
            with open(backup_file, 'rb') as f_in:
                with gzip.open(compressed_file, 'wb', compresslevel=9) as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Remove original file
            os.remove(backup_file)
            
            # Log compression ratio
            original_size = os.path.getsize(backup_file) if os.path.exists(backup_file) else 0
            compressed_size = os.path.getsize(compressed_file)
            compression_ratio = (1 - compressed_size / max(original_size, 1)) * 100
            
            self.logger.info(f"Backup compressed. Ratio: {compression_ratio:.1f}%")
            return compressed_file
            
        except Exception as e:
            self.logger.error(f"Backup compression failed: {str(e)}")
            return backup_file
    
    def verify_backup(self, backup_file: str) -> bool:
        """Verify backup integrity"""
        if not self.config['backup_settings']['verify_backup']:
            return True
            
        try:
            self.logger.info("Verifying backup integrity...")
            
            # For custom format, use pg_restore to verify
            if backup_file.endswith('.dump') or backup_file.endswith('.dump.gz'):
                cmd = ['pg_restore', '--list']
                
                if backup_file.endswith('.gz'):
                    # For compressed files, we need to decompress first or use zcat
                    result = subprocess.run(['zcat', backup_file], capture_output=True)
                    if result.returncode != 0:
                        self.logger.error("Failed to read compressed backup file")
                        return False
                    
                    # Pipe to pg_restore
                    result = subprocess.run(
                        cmd, 
                        input=result.stdout, 
                        capture_output=True, 
                        text=False
                    )
                else:
                    cmd.append(backup_file)
                    result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    self.logger.info("✅ Backup verification successful")
                    return True
                else:
                    self.logger.error(f"❌ Backup verification failed: {result.stderr}")
                    return False
            
            # For other formats, just check if file is readable
            else:
                if os.path.exists(backup_file) and os.path.getsize(backup_file) > 0:
                    self.logger.info("✅ Backup file exists and has content")
                    return True
                else:
                    self.logger.error("❌ Backup file is missing or empty")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Backup verification failed: {str(e)}")
            return False
    
    def upload_to_s3(self, backup_file: str) -> bool:
        """Upload backup to Amazon S3"""
        s3_config = self.config['s3_settings']
        
        if not s3_config['enabled']:
            return True
            
        try:
            self.logger.info("Uploading backup to S3...")
            
            # Initialize S3 client
            s3_client = boto3.client(
                's3',
                region_name=s3_config['region'],
                aws_access_key_id=s3_config['access_key'],
                aws_secret_access_key=s3_config['secret_key']
            )
            
            # Prepare S3 key
            s3_key = f"database-backups/{os.path.basename(backup_file)}"
            
            # Upload parameters
            extra_args = {
                'StorageClass': s3_config['storage_class']
            }
            
            if s3_config['encryption']:
                extra_args['ServerSideEncryption'] = 'AES256'
            
            # Upload file
            s3_client.upload_file(
                backup_file,
                s3_config['bucket_name'],
                s3_key,
                ExtraArgs=extra_args
            )
            
            self.logger.info(f"✅ Backup uploaded to S3: s3://{s3_config['bucket_name']}/{s3_key}")
            return True
            
        except ClientError as e:
            self.logger.error(f"S3 upload failed: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"S3 upload error: {str(e)}")
            return False
    
    def cleanup_old_backups(self) -> Dict[str, int]:
        """Remove old backup files based on retention policy"""
        try:
            backup_dir = self.config['backup_settings']['local_backup_dir']
            retention_days = self.config['backup_settings']['retention_days']
            max_backups = self.config['backup_settings']['max_local_backups']
            
            if not os.path.exists(backup_dir):
                return {'deleted_files': 0, 'freed_space_mb': 0}
            
            # Get all backup files with their timestamps
            backup_files = []
            for file in os.listdir(backup_dir):
                if any(file.endswith(ext) for ext in ['.sql', '.dump', '.tar', '.gz']):
                    file_path = os.path.join(backup_dir, file)
                    file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                    file_size = os.path.getsize(file_path)
                    
                    backup_files.append({
                        'path': file_path,
                        'mtime': file_mtime,
                        'size': file_size
                    })
            
            # Sort by modification time (newest first)
            backup_files.sort(key=lambda x: x['mtime'], reverse=True)
            
            deleted_files = 0
            freed_space = 0
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            for i, backup_file in enumerate(backup_files):
                should_delete = False
                
                # Delete if older than retention period
                if backup_file['mtime'] < cutoff_date:
                    should_delete = True
                    reason = f"older than {retention_days} days"
                
                # Delete if exceeds max backup count (keep newest)
                elif i >= max_backups:
                    should_delete = True
                    reason = f"exceeds max backup count ({max_backups})"
                
                if should_delete:
                    try:
                        os.remove(backup_file['path'])
                        deleted_files += 1
                        freed_space += backup_file['size']
                        self.logger.info(f"Deleted old backup: {os.path.basename(backup_file['path'])} ({reason})")
                    except Exception as e:
                        self.logger.warning(f"Could not delete {backup_file['path']}: {str(e)}")
            
            freed_space_mb = freed_space / (1024 * 1024)
            
            if deleted_files > 0:
                self.logger.info(f"Cleanup completed: {deleted_files} files deleted, {freed_space_mb:.2f} MB freed")
            else:
                self.logger.info("No old backups to clean up")
            
            return {
                'deleted_files': deleted_files,
                'freed_space_mb': round(freed_space_mb, 2)
            }
            
        except Exception as e:
            self.logger.error(f"Backup cleanup failed: {str(e)}")
            return {'deleted_files': 0, 'freed_space_mb': 0}
    
    def send_notification(self, backup_result: Dict[str, Any]):
        """Send email notification about backup status"""
        notification_config = self.config['notification_settings']
        
        if not notification_config['enabled']:
            return
            
        # Check if we should send notification
        if backup_result['success'] and not notification_config['notify_on_success']:
            return
        if not backup_result['success'] and not notification_config['notify_on_failure']:
            return
        
        try:
            # Prepare email content
            status = "✅ SUCCESS" if backup_result['success'] else "❌ FAILED"
            subject = f"AI Content Factory Backup {status} - {datetime.now().strftime('%Y-%m-%d')}"
            
            body = f"""
AI Content Factory Database Backup Report

Status: {status}
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Database: {self.config['database']['database']}

Backup Details:
- File: {backup_result.get('backup_file', 'N/A')}
- Size: {backup_result.get('file_size_mb', 0):.2f} MB
- Duration: {backup_result.get('duration_seconds', 0):.1f} seconds
- S3 Upload: {'✅' if backup_result.get('s3_uploaded', False) else '❌'}

Cleanup Results:
- Old backups deleted: {backup_result.get('cleanup_results', {}).get('deleted_files', 0)}
- Space freed: {backup_result.get('cleanup_results', {}).get('freed_space_mb', 0):.2f} MB

{backup_result.get('error_message', '') if not backup_result['success'] else ''}

Best regards,
AI Content Factory Backup System
"""
            
            # Create email message
            msg = MIMEMultipart()
            msg['From'] = notification_config['from_email']
            msg['To'] = ', '.join(notification_config['to_emails'])
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            with smtplib.SMTP(notification_config['smtp_host'], notification_config['smtp_port']) as server:
                server.starttls()
                server.login(notification_config['smtp_user'], notification_config['smtp_password'])
                
                text = msg.as_string()
                server.sendmail(
                    notification_config['from_email'],
                    notification_config['to_emails'],
                    text
                )
            
            self.logger.info("📧 Backup notification sent successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to send notification: {str(e)}")
    
    def create_backup(self, backup_type: str = 'manual') -> Dict[str, Any]:
        """Create a complete backup with all steps"""
        start_time = datetime.now()
        backup_result = {
            'success': False,
            'backup_file': None,
            'file_size_mb': 0,
            'duration_seconds': 0,
            's3_uploaded': False,
            'cleanup_results': {},
            'error_message': ''
        }
        
        try:
            self.logger.info(f"🚀 Starting {backup_type} database backup...")
            
            # Create backup directory
            backup_dir = self.create_backup_directory()
            
            # Generate backup filename
            backup_filename = self.generate_backup_filename(backup_type)
            backup_file = os.path.join(backup_dir, backup_filename)
            
            # Create database dump
            if not self.create_pg_dump(backup_file):
                backup_result['error_message'] = "Database dump creation failed"
                return backup_result
            
            # Compress backup if needed
            if self.config['backup_settings']['backup_format'] == 'plain':
                backup_file = self.compress_backup(backup_file)
            
            # Verify backup
            if not self.verify_backup(backup_file):
                backup_result['error_message'] = "Backup verification failed"
                return backup_result
            
            # Get file size
            file_size_mb = os.path.getsize(backup_file) / (1024 * 1024)
            
            # Upload to S3
            s3_uploaded = self.upload_to_s3(backup_file)
            
            # Cleanup old backups
            cleanup_results = self.cleanup_old_backups()
            
            # Calculate duration
            duration = (datetime.now() - start_time).total_seconds()
            
            # Update results
            backup_result.update({
                'success': True,
                'backup_file': os.path.basename(backup_file),
                'file_size_mb': round(file_size_mb, 2),
                'duration_seconds': round(duration, 1),
                's3_uploaded': s3_uploaded,
                'cleanup_results': cleanup_results
            })
            
            self.logger.info(f"✅ Backup completed successfully in {duration:.1f} seconds")
            
        except Exception as e:
            backup_result['error_message'] = str(e)
            self.logger.error(f"❌ Backup failed: {str(e)}")
        
        finally:
            # Send notification
            self.send_notification(backup_result)
            
        return backup_result
    
    def restore_backup(self, backup_file: str, target_db: str = None) -> bool:
        """Restore database from backup file"""
        try:
            self.logger.info(f"🔄 Starting database restore from {backup_file}")
            
            if not os.path.exists(backup_file):
                self.logger.error(f"Backup file not found: {backup_file}")
                return False
            
            db_config = self.config['database'].copy()
            if target_db:
                db_config['database'] = target_db
            
            # Build pg_restore command
            cmd = [
                'pg_restore',
                f"--host={db_config['host']}",
                f"--port={db_config['port']}",
                f"--username={db_config['user']}",
                f"--dbname={db_config['database']}",
                '--no-password',
                '--verbose',
                '--clean',
                '--no-acl',
                '--no-owner'
            ]
            
            # Handle compressed files
            if backup_file.endswith('.gz'):
                # For compressed files, use zcat to decompress
                zcat_process = subprocess.Popen(['zcat', backup_file], stdout=subprocess.PIPE)
                
                # Set environment variables
                env = os.environ.copy()
                env['PGPASSWORD'] = db_config['password']
                
                # Run pg_restore with zcat output as input
                result = subprocess.run(
                    cmd + ['--format=custom'],
                    stdin=zcat_process.stdout,
                    env=env,
                    capture_output=True,
                    text=True
                )
                zcat_process.stdout.close()
                zcat_process.wait()
                
            else:
                cmd.append(backup_file)
                
                # Set environment variables
                env = os.environ.copy()
                env['PGPASSWORD'] = db_config['password']
                
                # Determine format based on file extension
                if backup_file.endswith('.sql'):
                    # For SQL files, use psql instead
                    cmd = [
                        'psql',
                        f"--host={db_config['host']}",
                        f"--port={db_config['port']}",
                        f"--username={db_config['user']}",
                        f"--dbname={db_config['database']}",
                        '--no-password',
                        '--file', backup_file
                    ]
                
                result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.logger.info("✅ Database restore completed successfully")
                return True
            else:
                self.logger.error(f"❌ Database restore failed: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Database restore failed: {str(e)}")
            return False
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """List available backup files"""
        try:
            backup_dir = self.config['backup_settings']['local_backup_dir']
            
            if not os.path.exists(backup_dir):
                return []
            
            backups = []
            for file in os.listdir(backup_dir):
                if any(file.endswith(ext) for ext in ['.sql', '.dump', '.tar', '.gz']):
                    file_path = os.path.join(backup_dir, file)
                    file_stat = os.stat(file_path)
                    
                    backups.append({
                        'filename': file,
                        'path': file_path,
                        'size_mb': round(file_stat.st_size / (1024 * 1024), 2),
                        'created': datetime.fromtimestamp(file_stat.st_mtime),
                        'age_days': (datetime.now() - datetime.fromtimestamp(file_stat.st_mtime)).days
                    })
            
            # Sort by creation time (newest first)
            backups.sort(key=lambda x: x['created'], reverse=True)
            return backups
            
        except Exception as e:
            self.logger.error(f"Failed to list backups: {str(e)}")
            return []
    
    def setup_scheduled_backups(self):
        """Setup scheduled backup jobs"""
        schedule_config = self.config['schedule_settings']
        
        if not schedule_config['enabled']:
            self.logger.info("Scheduled backups are disabled")
            return
        
        # Daily backup
        if schedule_config.get('daily_time'):
            schedule.every().day.at(schedule_config['daily_time']).do(
                self.create_backup, 'daily'
            )
            self.logger.info(f"Daily backup scheduled at {schedule_config['daily_time']}")
        
        # Weekly backup
        if schedule_config.get('weekly_day') and schedule_config.get('weekly_time'):
            getattr(schedule.every(), schedule_config['weekly_day'].lower()).at(
                schedule_config['weekly_time']
            ).do(self.create_backup, 'weekly')
            self.logger.info(f"Weekly backup scheduled on {schedule_config['weekly_day']} at {schedule_config['weekly_time']}")
        
        # Monthly backup
        if schedule_config.get('monthly_day') and schedule_config.get('monthly_time'):
            # Note: schedule library doesn't support monthly directly
            # This would need a more sophisticated scheduler
            self.logger.info("Monthly backups require manual setup or cron job")
        
        self.logger.info("🕐 Backup scheduler initialized")
    
    def run_scheduler(self):
        """Run the backup scheduler"""
        self.setup_scheduled_backups()
        
        self.logger.info("🔄 Backup scheduler started. Press Ctrl+C to stop.")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            self.logger.info("⏹️ Backup scheduler stopped")

def main():
    """Main function with CLI interface"""
    parser = argparse.ArgumentParser(description="AI Content Factory Database Backup Tool")
    parser.add_argument('action', choices=['backup', 'restore', 'list', 'cleanup', 'schedule'],
                       help='Action to perform')
    parser.add_argument('--config', '-c', help='Path to backup config file')
    parser.add_argument('--type', '-t', default='manual',
                       choices=['manual', 'daily', 'weekly', 'monthly'],
                       help='Backup type (default: manual)')
    parser.add_argument('--file', '-f', help='Backup file path (for restore)')
    parser.add_argument('--target-db', help='Target database name (for restore)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = 'DEBUG' if args.verbose else 'INFO'
    logger = setup_logger("backup_main", level=log_level)
    
    # Initialize backup system
    backup_system = DatabaseBackup(args.config)
    
    try:
        if args.action == 'backup':
            result = backup_system.create_backup(args.type)
            if result['success']:
                logger.info("Backup completed successfully! 🎉")
                print(f"Backup file: {result['backup_file']}")
                print(f"Size: {result['file_size_mb']} MB")
                sys.exit(0)
            else:
                logger.error("Backup failed! ❌")
                sys.exit(1)
        
        elif args.action == 'restore':
            if not args.file:
                logger.error("Backup file is required for restore")
                sys.exit(1)
            
            success = backup_system.restore_backup(args.file, args.target_db)
            if success:
                logger.info("Restore completed successfully! 🎉")
                sys.exit(0)
            else:
                logger.error("Restore failed! ❌")
                sys.exit(1)
        
        elif args.action == 'list':
            backups = backup_system.list_backups()
            if backups:
                print("\n📋 Available Backups:")
                print("-" * 80)
                print(f"{'Filename':<40} {'Size (MB)':<10} {'Created':<20} {'Age (days)':<10}")
                print("-" * 80)
                for backup in backups:
                    print(f"{backup['filename']:<40} {backup['size_mb']:<10} {backup['created'].strftime('%Y-%m-%d %H:%M'):<20} {backup['age_days']:<10}")
            else:
                print("No backup files found")
        
        elif args.action == 'cleanup':
            result = backup_system.cleanup_old_backups()
            logger.info(f"Cleanup completed: {result['deleted_files']} files deleted, {result['freed_space_mb']} MB freed")
        
        elif args.action == 'schedule':
            backup_system.run_scheduler()
            
    except Exception as e:
        logger.error(f"Operation failed: {str(e)} ❌")
        sys.exit(1)

if __name__ == "__main__":
    main()