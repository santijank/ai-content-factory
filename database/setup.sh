#!/bin/bash

# Database Setup Script for AI Content Factory
# This script sets up the complete database environment

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
DB_HOST=${DB_HOST:-localhost}
DB_PORT=${DB_PORT:-5432}
DB_NAME=${DB_NAME:-content_factory}
DB_USER=${DB_USER:-postgres}
DB_PASSWORD=${DB_PASSWORD:-postgres}

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Functions
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

check_dependencies() {
    log_info "Checking dependencies..."
    
    # Check if PostgreSQL client is installed
    if ! command -v psql &> /dev/null; then
        log_error "PostgreSQL client (psql) is not installed"
        exit 1
    fi
    
    # Check if Python is installed
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is not installed"
        exit 1
    fi
    
    # Check if pip is installed
    if ! command -v pip3 &> /dev/null; then
        log_error "pip3 is not installed"
        exit 1
    fi
    
    log_success "All dependencies are installed"
}

check_postgres_connection() {
    log_info "Checking PostgreSQL connection..."
    
    if PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d postgres -c "SELECT 1;" &> /dev/null; then
        log_success "PostgreSQL connection successful"
        return 0
    else
        log_error "Cannot connect to PostgreSQL server"
        log_error "Please check your database connection settings:"
        log_error "  Host: $DB_HOST"
        log_error "  Port: $DB_PORT"
        log_error "  User: $DB_USER"
        return 1
    fi
}

install_python_dependencies() {
    log_info "Installing Python dependencies..."
    
    if [ -f "$SCRIPT_DIR/../requirements.txt" ]; then
        pip3 install -r "$SCRIPT_DIR/../requirements.txt"
        log_success "Python dependencies installed"
    else
        log_warning "requirements.txt not found, skipping Python dependencies"
    fi
}

create_database() {
    log_info "Creating database if it doesn't exist..."
    
    # Check if database exists
    DB_EXISTS=$(PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='$DB_NAME'")
    
    if [ "$DB_EXISTS" = "1" ]; then
        log_warning "Database '$DB_NAME' already exists"
    else
        PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d postgres -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;"
        log_success "Database '$DB_NAME' created successfully"
    fi
}

run_migrations() {
    log_info "Running database migrations..."
    
    cd "$SCRIPT_DIR"
    
    if [ -f "init_database.py" ]; then
        python3 init_database.py
        log_success "Database migrations completed"
    else
        log_error "Migration script not found"
        return 1
    fi
}

create_database_user() {
    local username=$1
    local password=$2
    local permissions=$3
    
    log_info "Creating database user: $username"
    
    USER_EXISTS=$(PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d postgres -tAc "SELECT 1 FROM pg_user WHERE usename='$username'")
    
    if [ "$USER_EXISTS" = "1" ]; then
        log_warning "User '$username' already exists"
    else
        PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d postgres -c "CREATE USER $username WITH PASSWORD '$password';"
        
        # Grant permissions
        case $permissions in
            "readonly")
                PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "GRANT CONNECT ON DATABASE $DB_NAME TO $username;"
                PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "GRANT USAGE ON SCHEMA public TO $username;"
                PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "GRANT SELECT ON ALL TABLES IN SCHEMA public TO $username;"
                PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO $username;"
                ;;
            "readwrite")
                PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "GRANT CONNECT ON DATABASE $DB_NAME TO $username;"
                PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "GRANT USAGE ON SCHEMA public TO $username;"
                PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO $username;"
                PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO $username;"
                PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO $username;"
                ;;
        esac
        
        log_success "User '$username' created with '$permissions' permissions"
    fi
}

setup_monitoring() {
    log_info "Setting up database monitoring..."
    
    # Create monitoring user
    create_database_user "monitor_user" "monitor_pass" "readonly"
    
    # Enable pg_stat_statements if available
    PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "CREATE EXTENSION IF NOT EXISTS pg_stat_statements;" 2>/dev/null || log_warning "pg_stat_statements extension not available"
    
    log_success "Database monitoring setup completed"
}

create_backup_script() {
    log_info "Creating backup script..."
    
    cat > "$SCRIPT_DIR/backup.sh" << EOF
#!/bin/bash
# Automated database backup script
# Generated by setup.sh

BACKUP_DIR="\${BACKUP_DIR:-/tmp/db_backups}"
DATE=\$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="\$BACKUP_DIR/${DB_NAME}_\$DATE.sql"

# Create backup directory if it doesn't exist
mkdir -p "\$BACKUP_DIR"

# Create backup
echo "Creating backup: \$BACKUP_FILE"
PGPASSWORD=$DB_PASSWORD pg_dump -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME > "\$BACKUP_FILE"

# Compress backup
gzip "\$BACKUP_FILE"

echo "Backup completed: \$BACKUP_FILE.gz"

# Clean up old backups (keep last 7 days)
find "\$BACKUP_DIR" -name "${DB_NAME}_*.sql.gz" -mtime +7 -delete
EOF

    chmod +x "$SCRIPT_DIR/backup.sh"
    log_success "Backup script created: $SCRIPT_DIR/backup.sh"
}

create_restore_script() {
    log_info "Creating restore script..."
    
    cat > "$SCRIPT_DIR/restore.sh" << EOF
#!/bin/bash
# Database restore script
# Generated by setup.sh

if [ "\$#" -ne 1 ]; then
    echo "Usage: \$0 <backup_file.sql.gz>"
    exit 1
fi

BACKUP_FILE="\$1"

if [ ! -f "\$BACKUP_FILE" ]; then
    echo "Backup file not found: \$BACKUP_FILE"
    exit 1
fi

echo "WARNING: This will drop and recreate the database '$DB_NAME'"
read -p "Are you sure you want to continue? (yes/no): " -r
if [[ ! \$REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "Restore cancelled"
    exit 1
fi

# Drop existing database
echo "Dropping existing database..."
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d postgres -c "DROP DATABASE IF EXISTS $DB_NAME;"

# Create new database
echo "Creating new database..."
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d postgres -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;"

# Restore from backup
echo "Restoring from backup..."
if [[ "\$BACKUP_FILE" == *.gz ]]; then
    gunzip -c "\$BACKUP_FILE" | PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME
else
    PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME < "\$BACKUP_FILE"
fi

echo "Restore completed successfully"
EOF

    chmod +x "$SCRIPT_DIR/restore.sh"
    log_success "Restore script created: $SCRIPT_DIR/restore.sh"
}

run_tests() {
    log_info "Running database tests..."
    
    # Test basic connectivity
    if PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT COUNT(*) FROM schema_migrations;" &> /dev/null; then
        log_success "Database connectivity test passed"
    else
        log_error "Database connectivity test failed"
        return 1
    fi
    
    # Test table creation
    TABLES=$(PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -tAc "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE';")
    
    if [ "$TABLES" -ge 5 ]; then
        log_success "Database tables test passed ($TABLES tables found)"
    else
        log_error "Database tables test failed (only $TABLES tables found)"
        return 1
    fi
    
    # Test functions
    FUNCTIONS=$(PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -tAc "SELECT COUNT(*) FROM information_schema.routines WHERE routine_schema='public';")
    
    if [ "$FUNCTIONS" -ge 5 ]; then
        log_success "Database functions test passed ($FUNCTIONS functions found)"
    else
        log_warning "Database functions test: only $FUNCTIONS functions found"
    fi
    
    log_success "All database tests completed"
}

print_summary() {
    echo ""
    log_success "=== Database Setup Complete ==="
    echo ""
    echo "Database Configuration:"
    echo "  Host: $DB_HOST"
    echo "  Port: $DB_PORT"
    echo "  Database: $DB_NAME"
    echo "  User: $DB_USER"
    echo ""
    echo "Available Scripts:"
    echo "  Backup: $SCRIPT_DIR/backup.sh"
    echo "  Restore: $SCRIPT_DIR/restore.sh"
    echo "  Migrate: python3 $SCRIPT_DIR/migrate.py"
    echo ""
    echo "Connection String:"
    echo "  postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME"
    echo ""
}

# Main execution
main() {
    local command=${1:-"full"}
    
    case $command in
        "check")
            log_info "Running dependency and connection checks..."
            check_dependencies
            check_postgres_connection
            ;;
        "init")
            log_info "Initializing database..."
            check_dependencies
            check_postgres_connection
            create_database
            run_migrations
            ;;
        "users")
            log_info "Setting up database users..."
            check_postgres_connection
            create_database_user "app_user" "app_password" "readwrite"
            create_database_user "readonly_user" "readonly_password" "readonly"
            ;;
        "monitor")
            log_info "Setting up monitoring..."
            check_postgres_connection
            setup_monitoring
            ;;
        "scripts")
            log_info "Creating utility scripts..."
            create_backup_script
            create_restore_script
            ;;
        "test")
            log_info "Running tests..."
            check_postgres_connection
            run_tests
            ;;
        "backup")
            log_info "Creating backup..."
            if [ -f "$SCRIPT_DIR/backup.sh" ]; then
                "$SCRIPT_DIR/backup.sh"
            else
                log_error "Backup script not found. Run '$0 scripts' first."
            fi
            ;;
        "full")
            log_info "Running full database setup..."
            check_dependencies
            install_python_dependencies
            check_postgres_connection
            create_database
            run_migrations
            create_database_user "app_user" "app_password" "readwrite"
            create_database_user "readonly_user" "readonly_password" "readonly"
            setup_monitoring
            create_backup_script
            create_restore_script
            run_tests
            print_summary
            ;;
        "help")
            echo "Usage: $0 [command]"
            echo ""
            echo "Commands:"
            echo "  full     - Complete database setup (default)"
            echo "  check    - Check dependencies and connection"
            echo "  init     - Initialize database and run migrations"
            echo "  users    - Create database users"
            echo "  monitor  - Setup monitoring"
            echo "  scripts  - Create backup/restore scripts"
            echo "  test     - Run database tests"
            echo "  backup   - Create database backup"
            echo "  help     - Show this help message"
            echo ""
            echo "Environment Variables:"
            echo "  DB_HOST     - Database host (default: localhost)"
            echo "  DB_PORT     - Database port (default: 5432)"
            echo "  DB_NAME     - Database name (default: content_factory)"
            echo "  DB_USER     - Database user (default: postgres)"
            echo "  DB_PASSWORD - Database password (default: postgres)"
            ;;
        *)
            log_error "Unknown command: $command"
            log_info "Use '$0 help' for usage information"
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"