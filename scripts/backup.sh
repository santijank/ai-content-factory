#!/bin/bash

# AI Content Factory - Backup and Restore Script
# This script handles database backups, file backups, and system restoration

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Configuration
ACTION=${1:-backup}         # backup, restore, list, cleanup, schedule
BACKUP_NAME=${2:-}          # For restore operations
ENVIRONMENT=${3:-development}

# Backup configuration
BACKUP_BASE_DIR="backups"
BACKUP_RETENTION_DAYS=30
MAX_BACKUP_SIZE="10G"

# Database configuration
DB_HOST=${DB_HOST:-localhost}
DB_PORT=${DB_PORT:-5432}
DB_NAME=${DB_NAME:-content_factory}
DB_USER=${DB_USER:-admin}
DB_PASSWORD=${DB_PASSWORD:-}

# Directories to backup
BACKUP_DIRS=(
    "data/uploads"
    "config"
    "logs"
    ".env"
)

# Load environment variables if .env exists
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Create timestamped backup name
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DEFAULT_BACKUP_NAME="backup_${TIMESTAMP}"

# Show backup information
show_backup_info() {
    echo "💾 AI Content Factory Backup System"
    echo "==================================="
    echo "Action: $ACTION"
    echo "Environment: $ENVIRONMENT"
    echo "Backup Directory: $BACKUP_BASE_DIR"
    if [ ! -z "$BACKUP_NAME" ]; then
        echo "Backup Name: $BACKUP_NAME"
    fi
    echo ""
}

# Check backup prerequisites
check_prerequisites() {
    log_info "Checking backup prerequisites..."
    
    # Check if required tools are available
    if ! command -v pg_dump &> /dev/null; then
        log_error "pg_dump is not installed!"
        exit 1
    fi
    
    if ! command -v tar &> /dev/null; then
        log_error "tar is not installed!"
        exit 1
    fi
    
    if ! command -v gzip &> /dev/null; then
        log_error "gzip is not installed!"
        exit 1
    fi
    
    # Create backup directories
    mkdir -p "$BACKUP_BASE_DIR"/{database,files,full}
    
    # Check available disk space
    available_space=$(df "$BACKUP_BASE_DIR" | tail -1 | awk '{print $4}')
    required_space=1048576  # 1GB in KB
    
    if [ "$available_space" -lt "$required_space" ]; then
        log_warning "Low disk space available for backups"
        log_warning "Available: $(($available_space / 1024))MB, Recommended: 1GB+"
    fi
    
    log_success "Prerequisites checked"
}

# Check database connectivity
check_database_connection() {
    log_info "Checking database connection..."
    
    export PGPASSWORD="$DB_PASSWORD"
    
    if psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1;" > /dev/null 2>&1; then
        log_success "Database connection successful"
    else
        log_error "Cannot connect to database!"
        return 1
    fi
}

# Create database backup
backup_database() {
    local backup_name=${1:-$DEFAULT_BACKUP_NAME}
    local backup_file="$BACKUP_BASE_DIR/database/${backup_name}_database.sql"
    
    log_info "Creating database backup: $backup_name"
    
    # Create database dump
    pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" \
            --verbose --clean --no-acl --no-owner \
            -f "$backup_file" "$DB_NAME"
    
    if [ $? -eq 0 ]; then
        # Compress backup
        gzip "$backup_file"
        local compressed_file="${backup_file}.gz"
        
        # Get backup size
        local backup_size=$(du -h "$compressed_file" | cut -f1)
        
        log_success "Database backup created: ${compressed_file} (${backup_size})"
        
        # Create metadata file
        create_backup_metadata "$backup_name" "database" "$compressed_file"
        
        return 0
    else
        log_error "Database backup failed!"
        return 1
    fi
}

# Create files backup
backup_files() {
    local backup_name=${1:-$DEFAULT_BACKUP_NAME}
    local backup_file="$BACKUP_BASE_DIR/files/${backup_name}_files.tar.gz"
    
    log_info "Creating files backup: $backup_name"
    
    # Prepare list of files to backup
    local files_to_backup=""
    for dir in "${BACKUP_DIRS[@]}"; do
        if [ -e "$dir" ]; then
            files_to_backup="$files_to_backup $dir"
        else
            log_warning "Directory/file not found: $dir"
        fi
    done
    
    if [ -z "$files_to_backup" ]; then
        log_warning "No files to backup"
        return 0
    fi
    
    # Create tar backup
    tar -czf "$backup_file" $files_to_backup 2>/dev/null
    
    if [ $? -eq 0 ]; then
        local backup_size=$(du -h "$backup_file" | cut -f1)
        
        log_success "Files backup created: $backup_file (${backup_size})"
        
        # Create metadata file
        create_backup_metadata "$backup_name" "files" "$backup_file"
        
        return 0
    else
        log_error "Files backup failed!"
        return 1
    fi
}

# Create full system backup
backup_full_system() {
    local backup_name=${1:-$DEFAULT_BACKUP_NAME}
    local full_backup_dir="$BACKUP_BASE_DIR/full/$backup_name"
    
    log_info "Creating full system backup: $backup_name"
    
    # Create backup directory
    mkdir -p "$full_backup_dir"
    
    # Backup database
    if check_database_connection; then
        backup_database "$backup_name"
        cp "$BACKUP_BASE_DIR/database/${backup_name}_database.sql.gz" "$full_backup_dir/"
    else
        log_warning "Skipping database backup due to connection issues"
    fi
    
    # Backup files
    backup_files "$backup_name"
    cp "$BACKUP_BASE_DIR/files/${backup_name}_files.tar.gz" "$full_backup_dir/" 2>/dev/null || true
    
    # Backup Docker volumes (if in Docker environment)
    if command -v docker &> /dev/null && docker ps > /dev/null 2>&1; then
        backup_docker_volumes "$backup_name" "$full_backup_dir"
    fi
    
    # Create system info
    create_system_info "$full_backup_dir"
    
    # Create full backup archive
    local full_backup_file="$BACKUP_BASE_DIR/full/${backup_name}_full.tar.gz"
    tar -czf "$full_backup_file" -C "$BACKUP_BASE_DIR/full" "$backup_name"
    
    # Remove temporary directory
    rm -rf "$full_backup_dir"
    
    local backup_size=$(du -h "$full_backup_file" | cut -f1)
    log_success "Full system backup created: $full_backup_file (${backup_size})"
    
    # Create metadata file
    create_backup_metadata "$backup_name" "full" "$full_backup_file"
}

# Backup Docker volumes
backup_docker_volumes() {
    local backup_name=$1
    local backup_dir=$2
    
    log_info "Backing up Docker volumes..."
    
    # Get list of volumes used by our services
    local volumes=$(docker-compose config --volumes 2>/dev/null || echo "")
    
    if [ ! -z "$volumes" ]; then
        mkdir -p "$backup_dir/volumes"
        
        for volume in $volumes; do
            log_info "Backing up volume: $volume"
            
            # Create volume backup
            docker run --rm \
                -v "$volume:/data:ro" \
                -v "$backup_dir/volumes:/backup" \
                alpine:latest \
                tar -czf "/backup/${volume}.tar.gz" -C /data . 2>/dev/null || true
        done
        
        log_success "Docker volumes backed up"
    else
        log_warning "No Docker volumes found to backup"
    fi
}

# Create system information
create_system_info() {
    local backup_dir=$1
    local info_file="$backup_dir/system_info.txt"
    
    log_info "Creating system information..."
    
    cat > "$info_file" << EOF
AI Content Factory System Backup Information
============================================
Backup Date: $(date)
Hostname: $(hostname)
User: $(whoami)
OS: $(uname -a)
Python Version: $(python3 --version 2>/dev/null || echo "Not available")
Docker Version: $(docker --version 2>/dev/null || echo "Not available")
Docker Compose Version: $(docker-compose --version 2>/dev/null || echo "Not available")

Environment Variables:
$(grep -v "PASSWORD\|SECRET\|KEY" .env 2>/dev/null || echo "No .env file found")

Running Services:
$(docker-compose ps 2>/dev/null || echo "Docker Compose not running")

Database Tables:
$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "\dt" 2>/dev/null || echo "Database not accessible")
EOF
    
    log_success "System information created"
}

# Create backup metadata
create_backup_metadata() {
    local backup_name=$1
    local backup_type=$2
    local backup_file=$3
    local metadata_file="$BACKUP_BASE_DIR/${backup_name}_metadata.json"
    
    local file_size=$(stat -c%s "$backup_file" 2>/dev/null || echo "0")
    local file_hash=$(md5sum "$backup_file" 2>/dev/null | cut -d' ' -f1 || echo "unknown")
    
    cat > "$metadata_file" << EOF
{
    "backup_name": "$backup_name",
    "backup_type": "$backup_type",
    "created_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "environment": "$ENVIRONMENT",
    "file_path": "$backup_file",
    "file_size": $file_size,
    "file_hash": "$file_hash",
    "database": {
        "host": "$DB_HOST",
        "port": "$DB_PORT",
        "name": "$DB_NAME",
        "user": "$DB_USER"
    },
    "system": {
        "hostname": "$(hostname)",
        "os": "$(uname -s)",
        "user": "$(whoami)"
    }
}
EOF
}

# List available backups
list_backups() {
    log_info "Available backups:"
    echo ""
    
    # List all backup types
    for backup_type in database files full; do
        local backup_dir="$BACKUP_BASE_DIR/$backup_type"
        
        if [ -d "$backup_dir" ] && [ "$(ls -A "$backup_dir" 2>/dev/null)" ]; then
            echo "📁 $backup_type backups:"
            
            for backup_file in "$backup_dir"/*; do
                if [ -f "$backup_file" ]; then
                    local filename=$(basename "$backup_file")
                    local file_size=$(du -h "$backup_file" | cut -f1)
                    local file_date=$(stat -c %y "$backup_file" 2>/dev/null | cut -d' ' -f1 || echo "unknown")
                    
                    echo "  • $filename ($file_size, $file_date)"
                fi
            done
            echo ""
        fi
    done
    
    # Show metadata files
    if ls "$BACKUP_BASE_DIR"/*_metadata.json > /dev/null 2>&1; then
        echo "📋 Backup metadata:"
        for metadata_file in "$BACKUP_BASE_DIR"/*_metadata.json; do
            local backup_name=$(basename "$metadata_file" _metadata.json)
            local created_at=$(grep '"created_at"' "$metadata_file" | cut -d'"' -f4)
            local backup_type=$(grep '"backup_type"' "$metadata_file" | cut -d'"' -f4)
            
            echo "  • $backup_name ($backup_type, $created_at)"
        done
    fi
}

# Restore database
restore_database() {
    local backup_name=$1
    local backup_file="$BACKUP_BASE_DIR/database/${backup_name}_database.sql.gz"
    
    if [ ! -f "$backup_file" ]; then
        log_error "Database backup file not found: $backup_file"
        return 1
    fi
    
    log_warning "This will overwrite the current database!"
    read -p "Are you sure you want to restore database from $backup_name? (y/N): " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Database restore cancelled"
        return 0
    fi
    
    log_info "Restoring database from: $backup_name"
    
    # Create a backup of current database before restore
    log_info "Creating backup of current database..."
    backup_database "before_restore_$(date +%Y%m%d_%H%M%S)"
    
    # Restore database
    gunzip -c "$backup_file" | psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME"
    
    if [ $? -eq 0 ]; then
        log_success "Database restored successfully"
    else
        log_error "Database restore failed!"
        return 1
    fi
}

# Restore files
restore_files() {
    local backup_name=$1
    local backup_file="$BACKUP_BASE_DIR/files/${backup_name}_files.tar.gz"
    
    if [ ! -f "$backup_file" ]; then
        log_error "Files backup file not found: $backup_file"
        return 1
    fi
    
    log_warning "This will overwrite current files!"
    read -p "Are you sure you want to restore files from $backup_name? (y/N): " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Files restore cancelled"
        return 0
    fi
    
    log_info "Restoring files from: $backup_name"
    
    # Create backup of current files
    log_info "Creating backup of current files..."
    backup_files "before_restore_$(date +%Y%m%d_%H%M%S)"
    
    # Restore files
    tar -xzf "$backup_file" -C .
    
    if [ $? -eq 0 ]; then
        log_success "Files restored successfully"
    else
        log_error "Files restore failed!"
        return 1
    fi
}

# Restore full system
restore_full_system() {
    local backup_name=$1
    local backup_file="$BACKUP_BASE_DIR/full/${backup_name}_full.tar.gz"
    
    if [ ! -f "$backup_file" ]; then
        log_error "Full backup file not found: $backup_file"
        return 1
    fi
    
    log_warning "This will restore the entire system!"
    read -p "Are you sure you want to restore full system from $backup_name? (y/N): " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Full system restore cancelled"
        return 0
    fi
    
    log_info "Restoring full system from: $backup_name"
    
    # Extract backup
    local temp_dir="/tmp/restore_$"
    mkdir -p "$temp_dir"
    tar -xzf "$backup_file" -C "$temp_dir"
    
    # Restore database
    if [ -f "$temp_dir/$backup_name/${backup_name}_database.sql.gz" ]; then
        cp "$temp_dir/$backup_name/${backup_name}_database.sql.gz" "$BACKUP_BASE_DIR/database/"
        restore_database "$backup_name"
    fi
    
    # Restore files
    if [ -f "$temp_dir/$backup_name/${backup_name}_files.tar.gz" ]; then
        cp "$temp_dir/$backup_name/${backup_name}_files.tar.gz" "$BACKUP_BASE_DIR/files/"
        restore_files "$backup_name"
    fi
    
    # Restore Docker volumes
    if [ -d "$temp_dir/$backup_name/volumes" ]; then
        restore_docker_volumes "$temp_dir/$backup_name/volumes"
    fi
    
    # Cleanup
    rm -rf "$temp_dir"
    
    log_success "Full system restore completed"
}

# Restore Docker volumes
restore_docker_volumes() {
    local volumes_dir=$1
    
    log_info "Restoring Docker volumes..."
    
    for volume_backup in "$volumes_dir"/*.tar.gz; do
        if [ -f "$volume_backup" ]; then
            local volume_name=$(basename "$volume_backup" .tar.gz)
            
            log_info "Restoring volume: $volume_name"
            
            # Create volume if it doesn't exist
            docker volume create "$volume_name" >/dev/null 2>&1 || true
            
            # Restore volume data
            docker run --rm \
                -v "$volume_name:/data" \
                -v "$volumes_dir:/backup:ro" \
                alpine:latest \
                sh -c "cd /data && tar -xzf /backup/${volume_name}.tar.gz" 2>/dev/null || true
        fi
    done
    
    log_success "Docker volumes restored"
}

# Cleanup old backups
cleanup_old_backups() {
    log_info "Cleaning up old backups (older than $BACKUP_RETENTION_DAYS days)..."
    
    local deleted_count=0
    
    # Cleanup database backups
    while IFS= read -r -d '' file; do
        rm "$file"
        deleted_count=$((deleted_count + 1))
        log_info "Deleted: $(basename "$file")"
    done < <(find "$BACKUP_BASE_DIR" -name "*.gz" -type f -mtime +$BACKUP_RETENTION_DAYS -print0 2>/dev/null)
    
    # Cleanup metadata files
    while IFS= read -r -d '' file; do
        rm "$file"
        deleted_count=$((deleted_count + 1))
        log_info "Deleted: $(basename "$file")"
    done < <(find "$BACKUP_BASE_DIR" -name "*_metadata.json" -type f -mtime +$BACKUP_RETENTION_DAYS -print0 2>/dev/null)
    
    if [ $deleted_count -eq 0 ]; then
        log_info "No old backups found to cleanup"
    else
        log_success "Cleaned up $deleted_count old backup files"
    fi
}

# Schedule automatic backups
schedule_backups() {
    log_info "Setting up automatic backup schedule..."
    
    # Create cron job for daily backups
    local cron_job="0 2 * * * $(pwd)/scripts/backup.sh backup"
    local cron_cleanup="0 3 * * 0 $(pwd)/scripts/backup.sh cleanup"
    
    # Add to crontab
    (crontab -l 2>/dev/null; echo "$cron_job"; echo "$cron_cleanup") | crontab -
    
    log_success "Automatic backups scheduled:"
    log_success "  • Daily backup at 2:00 AM"
    log_success "  • Weekly cleanup at 3:00 AM on Sundays"
}

# Show backup summary
show_backup_summary() {
    echo ""
    log_success "📊 Backup Summary"
    echo "=================="
    
    # Show disk usage
    local total_backup_size=$(du -sh "$BACKUP_BASE_DIR" 2>/dev/null | cut -f1 || echo "0")
    echo "Total backup size: $total_backup_size"
    
    # Count backups by type
    for backup_type in database files full; do
        local count=$(ls "$BACKUP_BASE_DIR/$backup_type"/* 2>/dev/null | wc -l || echo "0")
        echo "$backup_type backups: $count"
    done
    
    echo ""
    echo "🛠  Useful Commands:"
    echo "  • List backups: ./scripts/backup.sh list"
    echo "  • Restore: ./scripts/backup.sh restore <backup_name>"
    echo "  • Cleanup: ./scripts/backup.sh cleanup"
}

# Main backup function
main() {
    show_backup_info
    check_prerequisites
    
    case $ACTION in
        "backup")
            if [ -z "$BACKUP_NAME" ]; then
                BACKUP_NAME=$DEFAULT_BACKUP_NAME
            fi
            
            if check_database_connection; then
                backup_full_system "$BACKUP_NAME"
            else
                log_warning "Database not available, creating files-only backup"
                backup_files "$BACKUP_NAME"
            fi
            
            show_backup_summary
            ;;
            
        "restore")
            if [ -z "$BACKUP_NAME" ]; then
                log_error "Please specify backup name to restore"
                list_backups
                exit 1
            fi
            
            restore_full_system "$BACKUP_NAME"
            ;;
            
        "list")
            list_backups
            ;;
            
        "cleanup")
            cleanup_old_backups
            ;;
            
        "schedule")
            schedule_backups
            ;;
            
        *)
            log_error "Unknown action: $ACTION"
            log_error "Supported actions: backup, restore, list, cleanup, schedule"
            exit 1
            ;;
    esac
}

# Handle script interruption
trap 'log_error "Backup operation interrupted!"; exit 1' INT TERM

# Run main function
main "$@"