#!/bin/bash

# AI Content Factory - Build Script
# This script builds all Docker images and prepares the system for deployment

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
BUILD_ENV=${1:-development}  # development, staging, production
NO_CACHE=${2:-false}
PUSH_IMAGES=${3:-false}

# Docker registry settings (for production)
DOCKER_REGISTRY=${DOCKER_REGISTRY:-"localhost:5000"}
IMAGE_TAG=${IMAGE_TAG:-"latest"}

# Build options
BUILD_OPTS=""
if [ "$NO_CACHE" = "true" ]; then
    BUILD_OPTS="--no-cache"
fi

# Show build information
show_build_info() {
    echo "🔨 AI Content Factory Build Script"
    echo "=================================="
    echo "Environment: $BUILD_ENV"
    echo "No Cache: $NO_CACHE"
    echo "Push Images: $PUSH_IMAGES"
    echo "Docker Registry: $DOCKER_REGISTRY"
    echo "Image Tag: $IMAGE_TAG"
    echo ""
}

# Check Docker availability
check_docker() {
    log_info "Checking Docker availability..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed!"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running!"
        exit 1
    fi
    
    log_success "Docker is available"
}

# Clean up old images and containers
cleanup() {
    log_info "Cleaning up old containers and images..."
    
    # Stop and remove containers
    docker-compose down --remove-orphans 2>/dev/null || true
    
    # Remove dangling images
    if [ "$NO_CACHE" = "true" ]; then
        log_info "Removing dangling images..."
        docker image prune -f
        
        # Remove unused volumes
        docker volume prune -f
        
        log_success "Cleanup completed"
    fi
}

# Build Python dependencies
build_python_deps() {
    log_info "Building Python dependencies..."
    
    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        log_info "Creating Python virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install/update dependencies
    if [ -f requirements.txt ]; then
        pip install -r requirements.txt
        log_success "Python dependencies updated"
    fi
    
    # Freeze current dependencies
    pip freeze > requirements-frozen.txt
    log_success "Dependencies frozen to requirements-frozen.txt"
}

# Build Node.js dependencies (for web dashboard)
build_node_deps() {
    if [ -d "web-dashboard" ] && [ -f "web-dashboard/package.json" ]; then
        log_info "Building Node.js dependencies..."
        
        cd web-dashboard
        
        # Install dependencies
        npm ci
        
        # Build production bundle
        if [ "$BUILD_ENV" = "production" ]; then
            npm run build
            log_success "Production web bundle created"
        fi
        
        cd ..
        log_success "Node.js dependencies built"
    else
        log_warning "Web dashboard not found, skipping Node.js build"
    fi
}

# Build individual service
build_service() {
    local service_name=$1
    local dockerfile_path=$2
    local context_path=${3:-$service_name}
    
    log_info "Building $service_name..."
    
    # Full image name
    local image_name="ai-content-factory-${service_name}"
    if [ "$PUSH_IMAGES" = "true" ]; then
        image_name="${DOCKER_REGISTRY}/${image_name}:${IMAGE_TAG}"
    fi
    
    # Build image
    if [ -f "$dockerfile_path" ]; then
        docker build $BUILD_OPTS \
            -t "$image_name" \
            -f "$dockerfile_path" \
            "$context_path"
        
        log_success "Built $service_name successfully"
        
        # Tag for local use if pushing to registry
        if [ "$PUSH_IMAGES" = "true" ]; then
            docker tag "$image_name" "ai-content-factory-${service_name}:latest"
        fi
    else
        log_error "Dockerfile not found: $dockerfile_path"
        return 1
    fi
}

# Build all Docker images
build_images() {
    log_info "Building Docker images..."
    
    # Services to build
    declare -A services=(
        ["trend-monitor"]="trend-monitor/Dockerfile"
        ["content-engine"]="content-engine/Dockerfile"
        ["platform-manager"]="platform-manager/Dockerfile"
        ["monitoring"]="monitoring/Dockerfile"
    )
    
    # Build each service
    for service in "${!services[@]}"; do
        if [ -d "$service" ]; then
            build_service "$service" "${services[$service]}"
        else
            log_warning "Service directory not found: $service"
        fi
    done
    
    # Build using docker-compose for consistency
    log_info "Building with docker-compose..."
    
    if [ "$BUILD_ENV" = "production" ]; then
        docker-compose -f docker-compose.yml -f docker-compose.prod.yml build $BUILD_OPTS
    else
        docker-compose build $BUILD_OPTS
    fi
    
    log_success "All images built successfully"
}

# Push images to registry (for production)
push_images() {
    if [ "$PUSH_IMAGES" = "true" ]; then
        log_info "Pushing images to registry..."
        
        # Login to registry if credentials are provided
        if [ ! -z "$DOCKER_USERNAME" ] && [ ! -z "$DOCKER_PASSWORD" ]; then
            echo "$DOCKER_PASSWORD" | docker login "$DOCKER_REGISTRY" -u "$DOCKER_USERNAME" --password-stdin
        fi
        
        # Push all images
        docker-compose push
        
        log_success "Images pushed to registry"
    fi
}

# Generate build information
generate_build_info() {
    log_info "Generating build information..."
    
    # Create build info file
    cat > build-info.json << EOF
{
    "build_time": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "build_env": "$BUILD_ENV",
    "git_commit": "$(git rev-parse HEAD 2>/dev/null || echo 'unknown')",
    "git_branch": "$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo 'unknown')",
    "builder": "$(whoami)@$(hostname)",
    "docker_version": "$(docker --version)",
    "images": [
EOF
    
    # Add image information
    first=true
    for image in $(docker images --format "{{.Repository}}:{{.Tag}}" | grep "ai-content-factory"); do
        if [ "$first" = true ]; then
            first=false
        else
            echo "," >> build-info.json
        fi
        echo "        \"$image\"" >> build-info.json
    done
    
    cat >> build-info.json << EOF
    ]
}
EOF
    
    log_success "Build information saved to build-info.json"
}

# Run tests after build
run_tests() {
    if [ -f "tests/run_tests.py" ]; then
        log_info "Running tests..."
        
        source venv/bin/activate
        python tests/run_tests.py
        
        log_success "Tests completed"
    else
        log_warning "No test runner found, skipping tests"
    fi
}

# Verify build
verify_build() {
    log_info "Verifying build..."
    
    # Check if all required images exist
    required_images=("trend-monitor" "content-engine" "platform-manager")
    
    for image in "${required_images[@]}"; do
        if docker images | grep -q "ai-content-factory-${image}"; then
            log_success "Image ai-content-factory-${image} exists"
        else
            log_error "Image ai-content-factory-${image} not found!"
            exit 1
        fi
    done
    
    # Test image functionality (basic)
    log_info "Testing image functionality..."
    
    # Start a test container to verify it works
    if docker run --rm ai-content-factory-trend-monitor:latest python -c "print('Image works')" > /dev/null 2>&1; then
        log_success "Basic image functionality verified"
    else
        log_warning "Could not verify image functionality"
    fi
}

# Show build summary
show_summary() {
    echo ""
    log_success "🎉 Build completed successfully!"
    echo ""
    echo "📊 Build Summary:"
    echo "  • Environment: $BUILD_ENV"
    echo "  • Images built: $(docker images | grep ai-content-factory | wc -l)"
    echo "  • Build time: $(cat build-info.json | grep build_time | cut -d'"' -f4)"
    echo ""
    echo "🚀 Next Steps:"
    if [ "$BUILD_ENV" = "production" ]; then
        echo "  • Deploy to production: ./scripts/deploy.sh production"
        echo "  • Monitor deployment: kubectl get pods"
    else
        echo "  • Start services: docker-compose up -d"
        echo "  • View logs: docker-compose logs -f"
        echo "  • Access dashboard: http://localhost:5000"
    fi
    echo ""
    echo "🛠  Useful Commands:"
    echo "  • Rebuild: ./scripts/build.sh $BUILD_ENV true"
    echo "  • Clean rebuild: ./scripts/build.sh $BUILD_ENV true"
    echo "  • Deploy: ./scripts/deploy.sh $BUILD_ENV"
}

# Main build function
main() {
    show_build_info
    check_docker
    cleanup
    build_python_deps
    build_node_deps
    build_images
    push_images
    generate_build_info
    run_tests
    verify_build
    show_summary
}

# Handle script interruption
trap 'log_error "Build interrupted!"; exit 1' INT TERM

# Run main function
main "$@"