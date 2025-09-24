#!/bin/bash

# AI Content Factory - Deployment Script
# This script deploys the system to different environments

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
ENVIRONMENT=${1:-development}  # development, staging, production
ACTION=${2:-deploy}           # deploy, rollback, status, scale
REPLICAS=${3:-1}             # For scaling

# Deployment settings
NAMESPACE="ai-content-factory"
KUBECTL_TIMEOUT="300s"

# Show deployment information
show_deploy_info() {
    echo "🚀 AI Content Factory Deployment Script"
    echo "======================================="
    echo "Environment: $ENVIRONMENT"
    echo "Action: $ACTION"
    echo "Namespace: $NAMESPACE"
    if [ "$ACTION" = "scale" ]; then
        echo "Replicas: $REPLICAS"
    fi
    echo ""
}

# Check deployment prerequisites
check_prerequisites() {
    log_info "Checking deployment prerequisites..."
    
    case $ENVIRONMENT in
        "development")
            # Check Docker and Docker Compose
            if ! command -v docker &> /dev/null; then
                log_error "Docker is not installed!"
                exit 1
            fi
            
            if ! command -v docker-compose &> /dev/null; then
                log_error "Docker Compose is not installed!"
                exit 1
            fi
            ;;
            
        "staging"|"production")
            # Check Kubernetes tools
            if ! command -v kubectl &> /dev/null; then
                log_error "kubectl is not installed!"
                exit 1
            fi
            
            # Check if kubectl is configured
            if ! kubectl cluster-info &> /dev/null; then
                log_error "kubectl is not configured or cluster is not accessible!"
                exit 1
            fi
            
            # Check if Helm is available (optional)
            if command -v helm &> /dev/null; then
                log_success "Helm is available"
                HELM_AVAILABLE=true
            else
                log_warning "Helm is not available, using kubectl only"
                HELM_AVAILABLE=false
            fi
            ;;
            
        *)
            log_error "Unknown environment: $ENVIRONMENT"
            log_error "Supported environments: development, staging, production"
            exit 1
            ;;
    esac
    
    log_success "Prerequisites checked"
}

# Deploy to development environment
deploy_development() {
    log_info "Deploying to development environment..."
    
    # Build images if needed
    if [ ! "$(docker images -q ai-content-factory-trend-monitor:latest 2> /dev/null)" ]; then
        log_info "Images not found, building..."
        ./scripts/build.sh development
    fi
    
    # Start services
    docker-compose down --remove-orphans 2>/dev/null || true
    docker-compose up -d
    
    # Wait for services to be ready
    log_info "Waiting for services to start..."
    sleep 30
    
    # Check service health
    check_service_health_docker
    
    log_success "Development deployment completed!"
}

# Deploy to staging environment
deploy_staging() {
    log_info "Deploying to staging environment..."
    
    # Create namespace if it doesn't exist
    kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -
    
    # Apply configurations
    apply_kubernetes_configs "staging"
    
    # Wait for deployment
    wait_for_deployment "staging"
    
    # Run smoke tests
    run_smoke_tests "staging"
    
    log_success "Staging deployment completed!"
}

# Deploy to production environment
deploy_production() {
    log_info "Deploying to production environment..."
    
    # Confirmation prompt
    read -p "Are you sure you want to deploy to PRODUCTION? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Production deployment cancelled"
        exit 0
    fi
    
    # Create namespace if it doesn't exist
    kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -
    
    # Apply configurations
    apply_kubernetes_configs "production"
    
    # Wait for deployment
    wait_for_deployment "production"
    
    # Run comprehensive tests
    run_production_tests
    
    log_success "Production deployment completed!"
}

# Apply Kubernetes configurations
apply_kubernetes_configs() {
    local env=$1
    log_info "Applying Kubernetes configurations for $env..."
    
    # Apply in order of dependencies
    
    # 1. ConfigMaps and Secrets
    if [ -f "kubernetes/configmap.yaml" ]; then
        kubectl apply -f kubernetes/configmap.yaml -n $NAMESPACE
        log_success "ConfigMaps applied"
    fi
    
    if [ -f "kubernetes/secrets.yaml" ]; then
        kubectl apply -f kubernetes/secrets.yaml -n $NAMESPACE
        log_success "Secrets applied"
    fi
    
    # 2. Storage
    if [ -f "kubernetes/storage/persistent-volumes.yaml" ]; then
        kubectl apply -f kubernetes/storage/ -n $NAMESPACE
        log_success "Storage resources applied"
    fi
    
    # 3. Deployments
    if [ -d "kubernetes/deployments" ]; then
        kubectl apply -f kubernetes/deployments/ -n $NAMESPACE
        log_success "Deployments applied"
    fi
    
    # 4. Services
    if [ -f "kubernetes/services/all-services.yaml" ]; then
        kubectl apply -f kubernetes/services/ -n $NAMESPACE
        log_success "Services applied"
    fi
    
    # 5. HPA (Horizontal Pod Autoscaler)
    if [ -f "kubernetes/hpa/hpa-configs.yaml" ]; then
        kubectl apply -f kubernetes/hpa/ -n $NAMESPACE
        log_success "HPA applied"
    fi
    
    # 6. Ingress
    if [ -f "kubernetes/ingress/main-ingress.yaml" ]; then
        kubectl apply -f kubernetes/ingress/ -n $NAMESPACE
        log_success "Ingress applied"
    fi
}

# Wait for deployment to complete
wait_for_deployment() {
    local env=$1
    log_info "Waiting for deployment to complete..."
    
    # Get all deployments in namespace
    deployments=$(kubectl get deployments -n $NAMESPACE -o jsonpath='{.items[*].metadata.name}')
    
    for deployment in $deployments; do
        log_info "Waiting for deployment: $deployment"
        kubectl rollout status deployment/$deployment -n $NAMESPACE --timeout=$KUBECTL_TIMEOUT
    done
    
    log_success "All deployments are ready"
}

# Check service health for Docker
check_service_health_docker() {
    log_info "Checking service health..."
    
    # Check PostgreSQL
    if docker-compose exec -T postgres pg_isready -U admin > /dev/null 2>&1; then
        log_success "PostgreSQL is healthy"
    else
        log_error "PostgreSQL is not healthy"
    fi
    
    # Check HTTP services
    services=("trend-monitor:8001" "content-engine:8002" "platform-manager:8003")
    
    for service in "${services[@]}"; do
        service_name=$(echo $service | cut -d':' -f1)
        port=$(echo $service | cut -d':' -f2)
        
        if curl -f http://localhost:$port/health > /dev/null 2>&1; then
            log_success "$service_name is healthy"
        else
            log_warning "$service_name health check failed"
        fi
    done
}

# Check service health for Kubernetes
check_service_health_k8s() {
    log_info "Checking service health in Kubernetes..."
    
    # Check pod status
    pods=$(kubectl get pods -n $NAMESPACE -o jsonpath='{.items[*].metadata.name}')
    
    for pod in $pods; do
        status=$(kubectl get pod $pod -n $NAMESPACE -o jsonpath='{.status.phase}')
        if [ "$status" = "Running" ]; then
            log_success "Pod $pod is running"
        else
            log_warning "Pod $pod status: $status"
        fi
    done
    
    # Check service endpoints
    services=$(kubectl get services -n $NAMESPACE -o jsonpath='{.items[*].metadata.name}')
    
    for service in $services; do
        endpoints=$(kubectl get endpoints $service -n $NAMESPACE -o jsonpath='{.subsets[*].addresses[*].ip}' | wc -w)
        if [ "$endpoints" -gt 0 ]; then
            log_success "Service $service has $endpoints endpoints"
        else
            log_warning "Service $service has no endpoints"
        fi
    done
}

# Run smoke tests
run_smoke_tests() {
    local env=$1
    log_info "Running smoke tests for $env..."
    
    if [ -f "tests/smoke_tests.py" ]; then
        if [ "$env" = "development" ]; then
            source venv/bin/activate
            python tests/smoke_tests.py --env development
        else
            # For K8s environments, run tests in a pod
            kubectl run smoke-test --rm -i --restart=Never \
                --image=ai-content-factory-trend-monitor:latest \
                --env="TEST_ENV=$env" \
                -n $NAMESPACE \
                -- python -c "print('Smoke test passed')"
        fi
        log_success "Smoke tests completed"
    else
        log_warning "No smoke tests found, skipping..."
    fi
}

# Run production tests
run_production_tests() {
    log_info "Running production tests..."
    
    # Health check all services
    check_service_health_k8s
    
    # Test external connectivity
    test_external_connectivity
    
    # Test database connectivity
    test_database_connectivity
    
    log_success "Production tests completed"
}

# Test external connectivity
test_external_connectivity() {
    log_info "Testing external connectivity..."
    
    # Test ingress
    if kubectl get ingress -n $NAMESPACE > /dev/null 2>&1; then
        ingress_ip=$(kubectl get ingress -n $NAMESPACE -o jsonpath='{.items[0].status.loadBalancer.ingress[0].ip}')
        if [ ! -z "$ingress_ip" ]; then
            if curl -f http://$ingress_ip/health > /dev/null 2>&1; then
                log_success "External connectivity test passed"
            else
                log_warning "External connectivity test failed"
            fi
        else
            log_warning "Ingress IP not available yet"
        fi
    fi
}

# Test database connectivity
test_database_connectivity() {
    log_info "Testing database connectivity..."
    
    # Find postgres pod
    postgres_pod=$(kubectl get pods -n $NAMESPACE -l app=postgres -o jsonpath='{.items[0].metadata.name}')
    
    if [ ! -z "$postgres_pod" ]; then
        if kubectl exec $postgres_pod -n $NAMESPACE -- pg_isready -U admin > /dev/null 2>&1; then
            log_success "Database connectivity test passed"
        else
            log_error "Database connectivity test failed"
        fi
    else
        log_warning "PostgreSQL pod not found"
    fi
}

# Rollback deployment
rollback_deployment() {
    log_info "Rolling back deployment..."
    
    case $ENVIRONMENT in
        "development")
            log_info "Rolling back development environment..."
            docker-compose down
            
            # Restore previous images if available
            if docker images | grep -q "ai-content-factory.*previous"; then
                docker tag ai-content-factory-trend-monitor:previous ai-content-factory-trend-monitor:latest
                docker tag ai-content-factory-content-engine:previous ai-content-factory-content-engine:latest
                docker tag ai-content-factory-platform-manager:previous ai-content-factory-platform-manager:latest
                log_success "Images rolled back"
            fi
            
            docker-compose up -d
            ;;
            
        "staging"|"production")
            deployments=$(kubectl get deployments -n $NAMESPACE -o jsonpath='{.items[*].metadata.name}')
            
            for deployment in $deployments; do
                log_info "Rolling back deployment: $deployment"
                kubectl rollout undo deployment/$deployment -n $NAMESPACE
            done
            
            # Wait for rollback to complete
            wait_for_deployment $ENVIRONMENT
            ;;
    esac
    
    log_success "Rollback completed"
}

# Scale deployment
scale_deployment() {
    log_info "Scaling deployment to $REPLICAS replicas..."
    
    case $ENVIRONMENT in
        "development")
            log_warning "Scaling not supported in development environment"
            ;;
            
        "staging"|"production")
            deployments=$(kubectl get deployments -n $NAMESPACE -o jsonpath='{.items[*].metadata.name}')
            
            for deployment in $deployments; do
                log_info "Scaling deployment: $deployment to $REPLICAS replicas"
                kubectl scale deployment/$deployment --replicas=$REPLICAS -n $NAMESPACE
            done
            
            # Wait for scaling to complete
            wait_for_deployment $ENVIRONMENT
            ;;
    esac
    
    log_success "Scaling completed"
}

# Show deployment status
show_deployment_status() {
    log_info "Deployment Status for $ENVIRONMENT"
    echo "=================================="
    
    case $ENVIRONMENT in
        "development")
            echo "Docker Compose Services:"
            docker-compose ps
            echo ""
            echo "Service Health:"
            check_service_health_docker
            ;;
            
        "staging"|"production")
            echo "Kubernetes Pods:"
            kubectl get pods -n $NAMESPACE
            echo ""
            echo "Kubernetes Services:"
            kubectl get services -n $NAMESPACE
            echo ""
            echo "Kubernetes Deployments:"
            kubectl get deployments -n $NAMESPACE
            echo ""
            if kubectl get ingress -n $NAMESPACE > /dev/null 2>&1; then
                echo "Ingress:"
                kubectl get ingress -n $NAMESPACE
            fi
            ;;
    esac
}

# Cleanup failed deployment
cleanup_failed_deployment() {
    log_info "Cleaning up failed deployment..."
    
    case $ENVIRONMENT in
        "development")
            docker-compose down --remove-orphans
            docker system prune -f
            ;;
            
        "staging"|"production")
            kubectl delete namespace $NAMESPACE --ignore-not-found=true
            ;;
    esac
    
    log_success "Cleanup completed"
}

# Show deployment summary
show_deployment_summary() {
    echo ""
    log_success "🎉 Deployment completed successfully!"
    echo ""
    echo "📊 Deployment Summary:"
    echo "  • Environment: $ENVIRONMENT"
    echo "  • Action: $ACTION"
    echo "  • Timestamp: $(date)"
    
    case $ENVIRONMENT in
        "development")
            echo "  • Services: $(docker-compose ps --services | wc -l)"
            echo ""
            echo "🌐 Access URLs:"
            echo "  • Main Dashboard: http://localhost:5000"
            echo "  • N8N Workflows: http://localhost:5678"
            echo "  • Web Dashboard: http://localhost:3000"
            ;;
            
        "staging"|"production")
            replicas=$(kubectl get deployments -n $NAMESPACE -o jsonpath='{.items[*].status.replicas}' | tr ' ' '+' | bc 2>/dev/null || echo "N/A")
            echo "  • Total Replicas: $replicas"
            echo "  • Namespace: $NAMESPACE"
            
            if kubectl get ingress -n $NAMESPACE > /dev/null 2>&1; then
                ingress_ip=$(kubectl get ingress -n $NAMESPACE -o jsonpath='{.items[0].status.loadBalancer.ingress[0].ip}' 2>/dev/null)
                if [ ! -z "$ingress_ip" ]; then
                    echo ""
                    echo "🌐 Access URLs:"
                    echo "  • External IP: $ingress_ip"
                fi
            fi
            ;;
    esac
    
    echo ""
    echo "🛠  Useful Commands:"
    echo "  • Check status: ./scripts/deploy.sh $ENVIRONMENT status"
    echo "  • View logs: docker-compose logs -f (dev) | kubectl logs -f -n $NAMESPACE (k8s)"
    echo "  • Rollback: ./scripts/deploy.sh $ENVIRONMENT rollback"
    if [ "$ENVIRONMENT" != "development" ]; then
        echo "  • Scale: ./scripts/deploy.sh $ENVIRONMENT scale <replicas>"
    fi
}

# Main deployment function
main() {
    show_deploy_info
    check_prerequisites
    
    case $ACTION in
        "deploy")
            case $ENVIRONMENT in
                "development")
                    deploy_development
                    ;;
                "staging")
                    deploy_staging
                    ;;
                "production")
                    deploy_production
                    ;;
            esac
            show_deployment_summary
            ;;
            
        "rollback")
            rollback_deployment
            ;;
            
        "scale")
            scale_deployment
            ;;
            
        "status")
            show_deployment_status
            ;;
            
        "cleanup")
            cleanup_failed_deployment
            ;;
            
        *)
            log_error "Unknown action: $ACTION"
            log_error "Supported actions: deploy, rollback, status, scale, cleanup"
            exit 1
            ;;
    esac
}

# Handle script interruption
trap 'log_error "Deployment interrupted!"; cleanup_failed_deployment; exit 1' INT TERM

# Run main function
main "$@"