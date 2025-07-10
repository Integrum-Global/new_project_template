#!/bin/bash
set -euo pipefail

# Nexus Production Deployment Script
# This script deploys the Nexus platform to production Kubernetes cluster
#
# REQUIRED ENVIRONMENT VARIABLES:
#   DB_USERNAME     - Database username
#   DB_PASSWORD     - Database password
#   DB_HOST         - Database host
#   DB_NAME         - Database name
#
# OPTIONAL ENVIRONMENT VARIABLES:
#   DB_PORT         - Database port (default: 5432)
#   REDIS_HOST      - Redis host (default: redis)
#   REDIS_PORT      - Redis port (default: 6379)
#   REDIS_DB        - Redis database number (default: 0)
#   NAMESPACE       - Kubernetes namespace (default: nexus-production)
#   ENVIRONMENT     - Environment name (default: production)
#   CONTEXT         - Kubernetes context (default: nexus-production)
#   HELM_TIMEOUT    - Helm operation timeout (default: 600s)
#
# USAGE:
#   export DB_USERNAME="nexus_user"
#   export DB_PASSWORD="your-secure-password"
#   export DB_HOST="prod-postgres.example.com"
#   export DB_NAME="nexus_production"
#   ./deploy-production.sh

# Configuration
NAMESPACE="${NAMESPACE:-nexus-production}"
ENVIRONMENT="${ENVIRONMENT:-production}"
CONTEXT="${CONTEXT:-nexus-production}"
HELM_TIMEOUT="${HELM_TIMEOUT:-600s}"

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

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check required tools
    local tools=("kubectl" "helm" "docker")
    for tool in "${tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            log_error "$tool is required but not installed"
            exit 1
        fi
    done

    # Check kubectl context
    if ! kubectl config current-context | grep -q "$CONTEXT"; then
        log_error "kubectl context must be set to '$CONTEXT'"
        log_info "Current context: $(kubectl config current-context)"
        exit 1
    fi

    # Check cluster connectivity
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi

    log_success "Prerequisites check passed"
}

# Create namespace if it doesn't exist
create_namespace() {
    log_info "Creating namespace '$NAMESPACE'..."

    if kubectl get namespace "$NAMESPACE" &> /dev/null; then
        log_warning "Namespace '$NAMESPACE' already exists"
    else
        kubectl create namespace "$NAMESPACE"
        kubectl label namespace "$NAMESPACE" app=nexus environment="$ENVIRONMENT"
        log_success "Namespace '$NAMESPACE' created"
    fi
}

# Deploy secrets
deploy_secrets() {
    log_info "Deploying secrets..."

    # Validate required environment variables
    local required_vars=("DB_USERNAME" "DB_PASSWORD" "DB_HOST" "DB_NAME")
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var}" ]]; then
            log_error "Required environment variable $var is not set"
            log_error "Please set: DB_USERNAME, DB_PASSWORD, DB_HOST, DB_NAME, REDIS_HOST"
            exit 1
        fi
    done

    # Check if secrets already exist
    if kubectl get secret nexus-secrets -n "$NAMESPACE" &> /dev/null; then
        log_warning "Secret 'nexus-secrets' already exists, skipping creation"
    else
        # Create secrets from environment variables (SECURE)
        kubectl create secret generic nexus-secrets \
            --from-literal=database-url="postgresql://${DB_USERNAME}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT:-5432}/${DB_NAME}" \
            --from-literal=redis-url="redis://${REDIS_HOST:-redis}:${REDIS_PORT:-6379}/${REDIS_DB:-0}" \
            --from-literal=secret-key="$(openssl rand -base64 32)" \
            -n "$NAMESPACE"

        log_success "Secrets created from environment variables"
    fi
}

# Deploy PostgreSQL
deploy_postgres() {
    log_info "Deploying PostgreSQL cluster..."

    # Check if CNPG operator is installed
    if ! kubectl get crd clusters.postgresql.cnpg.io &> /dev/null; then
        log_warning "CloudNativePG operator not found, installing..."
        kubectl apply -f https://raw.githubusercontent.com/cloudnative-pg/cloudnative-pg/release-1.18/releases/cnpg-1.18.0.yaml

        # Wait for operator to be ready
        kubectl wait --for=condition=Available deployment/cnpg-controller-manager -n cnpg-system --timeout=300s
    fi

    # Deploy PostgreSQL cluster
    kubectl apply -f ../kubernetes/postgres-cluster.yaml

    # Wait for cluster to be ready
    log_info "Waiting for PostgreSQL cluster to be ready..."
    kubectl wait --for=condition=Ready cluster/nexus-postgres -n "$NAMESPACE" --timeout=600s

    log_success "PostgreSQL cluster deployed successfully"
}

# Deploy Redis
deploy_redis() {
    log_info "Deploying Redis cluster..."

    # Check if Redis operator is installed
    if ! kubectl get crd redisclusters.redis.redis.opstreelabs.in &> /dev/null; then
        log_warning "Redis operator not found, installing..."
        kubectl apply -f https://raw.githubusercontent.com/OT-CONTAINER-KIT/redis-operator/master/config/crd/bases/redis.redis.opstreelabs.in_redisclusters.yaml
        kubectl apply -f https://raw.githubusercontent.com/OT-CONTAINER-KIT/redis-operator/master/config/manager/manager.yaml

        # Wait for operator to be ready
        sleep 30
    fi

    # Deploy Redis cluster
    kubectl apply -f ../kubernetes/redis-cluster.yaml

    log_success "Redis cluster deployment initiated"
}

# Deploy monitoring stack
deploy_monitoring() {
    log_info "Deploying monitoring stack..."

    # Create monitoring namespace
    kubectl create namespace nexus-monitoring --dry-run=client -o yaml | kubectl apply -f -

    # Deploy Prometheus and Grafana
    kubectl apply -f ../kubernetes/monitoring.yaml

    # Wait for Prometheus to be ready
    log_info "Waiting for monitoring stack to be ready..."
    kubectl wait --for=condition=Available deployment/prometheus -n nexus-monitoring --timeout=300s
    kubectl wait --for=condition=Available deployment/grafana -n nexus-monitoring --timeout=300s

    log_success "Monitoring stack deployed successfully"
}

# Build and push Docker image
build_and_push_image() {
    local image_tag="${IMAGE_TAG:-$(git rev-parse --short HEAD)}"
    local registry="${REGISTRY:-nexus}"
    local image_name="$registry:$image_tag"

    log_info "Building Docker image: $image_name"

    # Build image
    docker build -t "$image_name" ../../

    # Push to registry (if configured)
    if [[ -n "${PUSH_IMAGE:-}" ]]; then
        log_info "Pushing image to registry..."
        docker push "$image_name"
        log_success "Image pushed successfully"
    fi

    # Update deployment with new image
    sed -i.bak "s|image: nexus:production|image: $image_name|g" ../kubernetes/nexus-production.yaml

    echo "$image_name"
}

# Deploy Nexus application
deploy_nexus() {
    log_info "Deploying Nexus application..."

    # Deploy the application
    kubectl apply -f ../kubernetes/nexus-production.yaml

    # Wait for deployment to be ready
    log_info "Waiting for Nexus deployment to be ready..."
    kubectl wait --for=condition=Available deployment/nexus-app -n "$NAMESPACE" --timeout=600s

    # Check if all pods are running
    kubectl get pods -n "$NAMESPACE" -l app=nexus

    log_success "Nexus application deployed successfully"
}

# Verify deployment
verify_deployment() {
    log_info "Verifying deployment..."

    # Check all pods are running
    local failed_pods
    failed_pods=$(kubectl get pods -n "$NAMESPACE" --no-headers | grep -v Running | wc -l)

    if [[ $failed_pods -gt 0 ]]; then
        log_error "Some pods are not running:"
        kubectl get pods -n "$NAMESPACE"
        return 1
    fi

    # Check services
    kubectl get services -n "$NAMESPACE"

    # Test health endpoint
    log_info "Testing application health..."
    if kubectl port-forward -n "$NAMESPACE" service/nexus-service 8080:80 &> /dev/null &
    then
        local port_forward_pid=$!
        sleep 5

        if curl -f http://localhost:8080/health &> /dev/null; then
            log_success "Health check passed"
        else
            log_warning "Health check failed"
        fi

        kill $port_forward_pid 2>/dev/null || true
    fi

    log_success "Deployment verification completed"
}

# Rollback function
rollback() {
    log_warning "Rolling back deployment..."

    # Rollback to previous version
    kubectl rollout undo deployment/nexus-app -n "$NAMESPACE"
    kubectl rollout status deployment/nexus-app -n "$NAMESPACE"

    log_info "Rollback completed"
}

# Cleanup function
cleanup() {
    log_info "Cleaning up temporary files..."
    # Restore original deployment file if backup exists
    if [[ -f ../kubernetes/nexus-production.yaml.bak ]]; then
        mv ../kubernetes/nexus-production.yaml.bak ../kubernetes/nexus-production.yaml
    fi
}

# Main deployment function
main() {
    local start_time
    start_time=$(date +%s)

    log_info "Starting Nexus production deployment..."
    log_info "Environment: $ENVIRONMENT"
    log_info "Namespace: $NAMESPACE"
    log_info "Context: $CONTEXT"

    # Trap for cleanup
    trap cleanup EXIT

    # Deployment steps
    check_prerequisites
    create_namespace
    deploy_secrets

    # Deploy infrastructure components
    deploy_postgres
    deploy_redis
    deploy_monitoring

    # Build and deploy application
    local image_name
    image_name=$(build_and_push_image)
    deploy_nexus

    # Verify deployment
    verify_deployment

    local end_time
    end_time=$(date +%s)
    local duration=$((end_time - start_time))

    log_success "Deployment completed successfully in ${duration}s"
    log_info "Application image: $image_name"

    # Display access information
    echo ""
    log_info "Access Information:"
    echo "  Nexus API: kubectl port-forward -n $NAMESPACE service/nexus-service 8080:80"
    echo "  Grafana: kubectl port-forward -n nexus-monitoring service/grafana-service 3000:3000"
    echo "  Prometheus: kubectl port-forward -n nexus-monitoring service/prometheus-service 9090:9090"
}

# Handle command line arguments
case "${1:-deploy}" in
    deploy)
        main
        ;;
    rollback)
        rollback
        ;;
    verify)
        verify_deployment
        ;;
    *)
        echo "Usage: $0 {deploy|rollback|verify}"
        exit 1
        ;;
esac
