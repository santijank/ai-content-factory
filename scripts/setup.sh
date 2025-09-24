#!/bin/bash

# AI Content Factory - Setup Script
# This script sets up the entire development environment

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

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        log_error "This script should not be run as root!"
        exit 1
    fi
}

# Check system requirements
check_requirements() {
    log_info "Checking system requirements..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is not installed. Please install Python 3.8+ first."
        exit 1
    fi
    
    # Check Node.js (for web dashboard)
    if ! command -v node &> /dev/null; then
        log_warning "Node.js is not installed. Web dashboard may not work properly."
    fi
    
    # Check Git
    if ! command -v git &> /dev/null; then
        log_error "Git is not installed. Please install Git first."
        exit 1
    fi
    
    log_success "All requirements checked!"
}

# Setup environment variables
setup_environment() {
    log_info "Setting up environment variables..."
    
    # Copy example env file if .env doesn't exist
    if [ ! -f .env ]; then
        if [ -f .env.example ]; then
            cp .env.example .env
            log_success "Created .env file from .env.example"
        else
            log_error ".env.example file not found!"
            exit 1
        fi
    else
        log_info ".env file already exists, skipping..."
    fi
    
    # Generate random passwords if not set
    if ! grep -q "POSTGRES_PASSWORD=" .env || grep -q "POSTGRES_PASSWORD=$" .env; then
        POSTGRES_PASSWORD=$(openssl rand -base64 32)
        sed -i "s/POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=${POSTGRES_PASSWORD}/" .env
        log_success "Generated random PostgreSQL password"
    fi
    
    if ! grep -q "N8N_PASSWORD=" .env || grep -q "N8N_PASSWORD=$" .env; then
        N8N_PASSWORD=$(openssl rand -base64 16)
        sed -i "s/N8N_PASSWORD=.*/N8N_PASSWORD=${N8N_PASSWORD}/" .env
        log_success "Generated random N8N password"
    fi
    
    # Create directories for data persistence
    mkdir -p data/postgres
    mkdir -p data/n8n
    mkdir -p data/uploads
    mkdir -p logs
    
    log_success "Environment setup completed!"
}

# Setup Python virtual environment
setup_python_env() {
    log_info "Setting up Python environment..."
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        log_success "Created Python virtual environment"
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install requirements
    if [ -f requirements.txt ]; then
        pip install -r requirements.txt
        log_success "Installed Python dependencies"
    else
        log_warning "requirements.txt not found, skipping Python dependencies"
    fi
    
    log_success "Python environment setup completed!"
}

# Setup Node.js environment (for web dashboard)
setup_node_env() {
    if command -v node &> /dev/null; then
        log_info "Setting up Node.js environment..."
        
        cd web-dashboard
        
        # Install dependencies
        if [ -f package.json ]; then
            npm install
            log_success "Installed Node.js dependencies"
        else
            log_warning "package.json not found in web-dashboard directory"
        fi
        
        cd ..
        log_success "Node.js environment setup completed!"
    else
        log_warning "Node.js not found, skipping web dashboard setup"
    fi
}

# Initialize database
init_database() {
    log_info "Initializing database..."
    
    # Start PostgreSQL container
    docker-compose up -d postgres
    
    # Wait for PostgreSQL to be ready
    log_info "Waiting for PostgreSQL to be ready..."
    sleep 10
    
    # Run database migrations
    if [ -f database/migrate.py ]; then
        source venv/bin/activate
        python database/migrate.py
        log_success "Database migrations completed"
    else
        log_warning "Migration script not found, skipping..."
    fi
    
    log_success "Database initialization completed!"
}

# Build Docker images
build_images() {
    log_info "Building Docker images..."
    
    # Build all services
    docker-compose build
    
    log_success "Docker images built successfully!"
}

# Start services
start_services() {
    log_info "Starting all services..."
    
    # Start all services
    docker-compose up -d
    
    # Wait for services to be ready
    log_info "Waiting for services to start..."
    sleep 15
    
    # Check service health
    check_service_health
    
    log_success "All services started successfully!"
}

# Check service health
check_service_health() {
    log_info "Checking service health..."
    
    # Check PostgreSQL
    if docker-compose exec postgres pg_isready -U admin > /dev/null 2>&1; then
        log_success "PostgreSQL is running"
    else
        log_error "PostgreSQL is not responding"
    fi
    
    # Check other services (basic container check)
    services=("trend-monitor" "content-engine" "platform-manager" "n8n")
    
    for service in "${services[@]}"; do
        if docker-compose ps | grep -q "${service}.*Up"; then
            log_success "${service} is running"
        else
            log_warning "${service} may not be running properly"
        fi
    done
}

# Setup N8N workflows
setup_n8n_workflows() {
    log_info "Setting up N8N workflows..."
    
    # Wait for N8N to be ready
    sleep 20
    
    # Import workflows if available
    if [ -d "n8n-workflows" ] && [ -f "n8n-workflows/import-workflows.sh" ]; then
        bash n8n-workflows/import-workflows.sh
        log_success "N8N workflows imported"
    else
        log_warning "N8N workflow import script not found"
    fi
}

# Display setup information
display_info() {
    log_success "🎉 AI Content Factory setup completed!"
    echo ""
    echo "📊 Service URLs:"
    echo "  • Main Dashboard: http://localhost:5000"
    echo "  • N8N Workflows: http://localhost:5678"
    echo "  • Web Dashboard: http://localhost:3000 (if Node.js is installed)"
    echo "  • Monitoring: http://localhost:9090"
    echo ""
    echo "🔐 Default Credentials:"
    echo "  • N8N: admin / $(grep N8N_PASSWORD .env | cut -d'=' -f2)"
    echo "  • PostgreSQL: admin / $(grep POSTGRES_PASSWORD .env | cut -d'=' -f2)"
    echo ""
    echo "📝 Next Steps:"
    echo "  1. Visit the dashboard at http://localhost:5000"
    echo "  2. Configure your API keys in the .env file"
    echo "  3. Import N8N workflows if not done automatically"
    echo "  4. Start collecting trends and generating content!"
    echo ""
    echo "🛠  Useful Commands:"
    echo "  • View logs: docker-compose logs -f"
    echo "  • Stop services: docker-compose down"
    echo "  • Restart services: docker-compose restart"
    echo "  • Update system: ./scripts/build.sh && docker-compose up -d"
}

# Main setup function
main() {
    echo "🚀 AI Content Factory Setup Script"
    echo "=================================="
    
    check_root
    check_requirements
    setup_environment
    setup_python_env
    setup_node_env
    build_images
    init_database
    start_services
    setup_n8n_workflows
    display_info
}

# Handle script interruption
trap 'log_error "Setup interrupted! Run: docker-compose down to clean up"; exit 1' INT TERM

# Run main function
main "$@"