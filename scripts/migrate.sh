#!/bin/bash

# AI Content Factory - Database Migration Script
# This script handles database migrations and schema updates

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
ACTION=${1:-migrate}        # migrate, rollback, status, reset, seed
TARGET_VERSION=${2:-latest} # For specific version migrations
ENVIRONMENT=${3:-development}

# Database configuration
DB_HOST=${DB_HOST:-localhost}
DB_PORT=${DB_PORT:-5432}
DB_NAME=${DB_NAME:-content_factory}
DB_USER=${DB_USER:-admin}
DB_PASSWORD=${DB_PASSWORD:-}

# Migration settings
MIGRATION_DIR="database/migrations"
SEED_DIR="database/seeds"
BACKUP_DIR="database/backups"

# Load environment variables if .env exists
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Show migration information
show_migration_info() {
    echo "🗄️  AI Content Factory Database Migration"
    echo "========================================"
    echo "Action: $ACTION"
    echo "Target Version: $TARGET_VERSION"
    echo "Environment: $ENVIRONMENT"
    echo "Database: $DB_HOST:$DB_PORT/$DB_NAME"
    echo "User: $DB_USER"
    echo ""
}

# Check migration prerequisites
check_prerequisites() {
    log_info "Checking migration prerequisites..."
    
    # Check if PostgreSQL client is available
    if ! command -v psql &> /dev/null; then
        log_error "PostgreSQL client (psql) is not installed!"
        exit 1
    fi
    
    # Check if Python is available for migration scripts
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is not installed!"
        exit 1
    fi
    
    # Check migration directory
    if [ ! -d "$MIGRATION_DIR" ]; then
        log_error "Migration directory not found: $MIGRATION_DIR"
        exit 1
    fi
    
    # Create backup directory if it doesn't exist
    mkdir -p "$BACKUP_DIR"
    
    log_success "Prerequisites checked"
}

# Check database connectivity
check_database_connection() {
    log_info "Checking database connection..."
    
    # Set PGPASSWORD for non-interactive connection
    export PGPASSWORD="$DB_PASSWORD"
    
    # Test connection
    if psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1;" > /dev/null 2>&1; then
        log_success "Database connection successful"
    else
        log_error "Cannot connect to database!"
        log_error "Please check your database configuration and ensure the database is running"
        exit 1
    fi
}

# Wait for database to be ready
wait_for_database() {
    log_info "Waiting for database to be ready..."
    
    max_attempts=30
    attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1;" > /dev/null 2>&1; then
            log_success "Database is ready"
            return 0
        fi
        
        log_info "Attempt $attempt/$max_attempts - Database not ready yet, waiting..."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    log_error "Database did not become ready within timeout"
    exit 1
}

# Create migration tracking table
create_migration_table() {
    log_info "Creating migration tracking table..."
    
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" << EOF
CREATE TABLE IF NOT EXISTS schema_migrations (
    version VARCHAR(255) PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    applied_by VARCHAR(255) DEFAULT CURRENT_USER,
    checksum VARCHAR(255)
);
EOF
    
    log_success "Migration tracking table ready"
}

# Get applied migrations
get_applied_migrations() {
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT version FROM schema_migrations ORDER BY version;" | tr -d ' '
}

# Get available migrations
get_available_migrations() {
    if [ -d "$MIGRATION_DIR" ]; then
        find "$MIGRATION_DIR" -name "*.sql" -type f | sort | xargs -I {} basename {} .sql
    fi
}

# Calculate file checksum
calculate_checksum() {
    local file=$1
    if [ -f "$file" ]; then
        md5sum "$file" | cut -d' ' -f1
    fi
}

# Apply single migration
apply_migration() {
    local migration_file=$1
    local version=$(basename "$migration_file" .sql)
    
    log_info "Applying migration: $version"
    
    # Calculate checksum
    local checksum=$(calculate_checksum "$migration_file")
    
    # Check if migration is already applied
    local applied=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM schema_migrations WHERE version = '$version';" | tr -d ' ')
    
    if [ "$applied" = "1" ]; then
        log_warning "Migration $version already applied, skipping..."
        return 0
    fi
    
    # Create backup before applying migration
    create_backup "before_$version"
    
    # Apply migration in transaction
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" << EOF
BEGIN;

-- Apply migration
\i $migration_file

-- Record migration
INSERT INTO schema_migrations (version, checksum) VALUES ('$version', '$checksum');

COMMIT;
EOF
    
    if [ $? -eq 0 ]; then
        log_success "Migration $version applied successfully"
    else
        log_error "Migration $version failed!"
        exit 1
    fi
}

# Run migrations
run_migrations() {
    log_info "Running database migrations..."
    
    # Get applied and available migrations
    applied_migrations=$(get_applied_migrations)
    available_migrations=$(get_available_migrations)
    
    if [ -z "$available_migrations" ]; then
        log_warning "No migration files found"
        return 0
    fi
    
    # Apply migrations
    for migration in $available_migrations; do
        migration_file="$MIGRATION_DIR/${migration}.sql"
        
        if [ "$TARGET_VERSION" != "latest" ] && [ "$migration" \> "$TARGET_VERSION" ]; then
            log_info "Stopping at target version: $TARGET_VERSION"
            break
        fi
        
        # Check if migration needs to be applied
        if echo "$applied_migrations" | grep -q "^$migration$"; then
            log_info "Migration $migration already applied, skipping..."
        else
            apply_migration "$migration_file"
        fi
    done
    
    log_success "All migrations completed"
}

# Rollback migration
rollback_migration() {
    log_info "Rolling back migration..."
    
    if [ "$TARGET_VERSION" = "latest" ]; then
        log_error "Please specify a target version for rollback"
        exit 1
    fi
    
    # Get current applied migrations
    applied_migrations=$(get_applied_migrations | tail -r)
    
    for migration in $applied_migrations; do
        if [ "$migration" \> "$TARGET_VERSION" ]; then
            log_info "Rolling back migration: $migration"
            
            # Check if rollback file exists
            rollback_file="$MIGRATION_DIR/${migration}_down.sql"
            
            if [ -f "$rollback_file" ]; then
                # Create backup before rollback
                create_backup "before_rollback_$migration"
                
                # Apply rollback
                psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" << EOF
BEGIN;

-- Apply rollback
\i $rollback_file

-- Remove from migration tracking
DELETE FROM schema_migrations WHERE version = '$migration';

COMMIT;
EOF
                
                if [ $? -eq 0 ]; then
                    log_success "Rollback $migration completed"
                else
                    log_error "Rollback $migration failed!"
                    exit 1
                fi
            else
                log_error "Rollback file not found: $rollback_file"
                log_error "Manual rollback required for migration: $migration"
                exit 1
            fi
        fi
    done
    
    log_success "Rollback completed to version: $TARGET_VERSION"
}

# Show migration status
show_migration_status() {
    log_info "Migration Status"
    echo "================"
    
    applied_migrations=$(get_applied_migrations)
    available_migrations=$(get_available_migrations)
    
    echo "Available Migrations:"
    for migration in $available_migrations; do
        if echo "$applied_migrations" | grep -q "^$migration$"; then
            echo "  ✅ $migration (applied)"
        else
            echo "  ⏳ $migration (pending)"
        fi
    done
    
    echo ""
    echo "Database Info:"
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "\dt"
    
    echo ""
    echo "Migration History:"
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT * FROM schema_migrations ORDER BY applied_at DESC LIMIT 10;"
}

# Create database backup
create_backup() {
    local backup_name=${1:-$(date +%Y%m%d_%H%M%S)}
    local backup_file="$BACKUP_DIR/${backup_name}.sql"
    
    log_info "Creating database backup: $backup_name"
    
    pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" > "$backup_file"
    
    if [ $? -eq 0 ]; then
        log_success "Backup created: $backup_file"
        
        # Compress backup
        gzip "$backup_file"
        log_success "Backup compressed: ${backup_file}.gz"
    else
        log_error "Backup failed!"
        exit 1
    fi
}

# Reset database
reset_database() {
    log_warning "This will completely reset the database!"
    read -p "Are you sure? Type 'yes' to continue: " confirmation
    
    if [ "$confirmation" != "yes" ]; then
        log_info "Database reset cancelled"
        exit 0
    fi
    
    log_info "Resetting database..."
    
    # Create backup before reset
    create_backup "before_reset"
    
    # Drop all tables
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" << EOF
-- Drop all tables
DO \$\$ DECLARE
    r RECORD;
BEGIN
    FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = current_schema()) LOOP
        EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
    END LOOP;
END \$\$;
EOF
    
    # Run all migrations from scratch
    run_migrations
    
    log_success "Database reset completed"
}

# Seed database with sample data
seed_database() {
    log_info "Seeding database with sample data..."
    
    if [ ! -d "$SEED_DIR" ]; then
        log_warning "Seed directory not found: $SEED_DIR"
        return 0
    fi
    
    # Run seed files
    for seed_file in "$SEED_DIR"/*.sql; do
        if [ -f "$seed_file" ]; then
            seed_name=$(basename "$seed_file")
            log_info "Running seed: $seed_name"
            
            psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$seed_file"
            
            if [ $? -eq 0 ]; then
                log_success "Seed $seed_name completed"
            else
                log_error "Seed $seed_name failed!"
            fi
        fi
    done
    
    log_success "Database seeding completed"
}

# Validate database schema
validate_schema() {
    log_info "Validating database schema..."
    
    # Check required tables exist
    required_tables=("trends" "content_opportunities" "content_items" "uploads" "performance_metrics")
    
    for table in "${required_tables[@]}"; do
        count=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = '$table';" | tr -d ' ')
        
        if [ "$count" = "1" ]; then
            log_success "Table $table exists"
        else
            log_error "Table $table is missing!"
        fi
    done
    
    log_success "Schema validation completed"
}

# Main migration function
main() {
    show_migration_info
    check_prerequisites
    
    # For Docker environments, wait for database
    if [ "$ENVIRONMENT" = "development" ] || [ "$ENVIRONMENT" = "docker" ]; then
        wait_for_database
    else
        check_database_connection
    fi
    
    create_migration_table
    
    case $ACTION in
        "migrate")
            run_migrations
            validate_schema
            ;;
            
        "rollback")
            rollback_migration
            ;;
            
        "status")
            show_migration_status
            ;;
            
        "reset")
            reset_database
            ;;
            
        "seed")
            seed_database
            ;;
            
        "backup")
            create_backup
            ;;
            
        "validate")
            validate_schema
            ;;
            
        *)
            log_error "Unknown action: $ACTION"
            log_error "Supported actions: migrate, rollback, status, reset, seed, backup, validate"
            exit 1
            ;;
    esac
}

# Handle script interruption
trap 'log_error "Migration interrupted!"; exit 1' INT TERM

# Run main function
main "$@"