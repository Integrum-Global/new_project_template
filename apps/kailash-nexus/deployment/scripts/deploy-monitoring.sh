#!/bin/bash

# Nexus Monitoring Stack Deployment Script
# This script deploys the complete monitoring stack for Nexus production environment

set -euo pipefail

# Configuration
NAMESPACE="nexus-production"
KUBECTL_CMD="kubectl"
DEPLOYMENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
KUBE_DIR="${DEPLOYMENT_DIR}/kubernetes"

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

    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed or not in PATH"
        exit 1
    fi

    # Check cluster connectivity
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi

    # Check namespace
    if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
        log_warning "Namespace $NAMESPACE does not exist. Creating..."
        kubectl create namespace "$NAMESPACE"
    fi

    log_success "Prerequisites check passed"
}

# Deploy RBAC and security policies
deploy_rbac() {
    log_info "Deploying RBAC and security policies..."

    kubectl apply -f "${KUBE_DIR}/rbac.yaml"
    kubectl apply -f "${KUBE_DIR}/security-policies.yaml"
    kubectl apply -f "${KUBE_DIR}/network-policies.yaml"

    log_success "RBAC and security policies deployed"
}

# Deploy Prometheus
deploy_prometheus() {
    log_info "Deploying Prometheus..."

    kubectl apply -f "${KUBE_DIR}/monitoring-enhanced.yaml"

    # Wait for Prometheus to be ready
    log_info "Waiting for Prometheus to be ready..."
    kubectl wait --for=condition=available --timeout=300s deployment/prometheus -n "$NAMESPACE"

    log_success "Prometheus deployed and ready"
}

# Deploy Alertmanager
deploy_alertmanager() {
    log_info "Deploying Alertmanager..."

    kubectl apply -f "${KUBE_DIR}/alertmanager.yaml"

    # Wait for Alertmanager to be ready
    log_info "Waiting for Alertmanager to be ready..."
    kubectl wait --for=condition=available --timeout=300s deployment/alertmanager -n "$NAMESPACE"

    log_success "Alertmanager deployed and ready"
}

# Deploy Loki stack
deploy_loki() {
    log_info "Deploying Loki logging stack..."

    kubectl apply -f "${KUBE_DIR}/loki-stack.yaml"

    # Wait for Loki to be ready
    log_info "Waiting for Loki to be ready..."
    kubectl wait --for=condition=ready --timeout=300s pod -l app=loki -n "$NAMESPACE"

    log_success "Loki stack deployed and ready"
}

# Deploy Grafana
deploy_grafana() {
    log_info "Deploying Grafana with dashboards..."

    # Deploy Grafana configuration and dashboards
    kubectl apply -f "${KUBE_DIR}/grafana-dashboards.yaml"

    # Wait for Grafana to be ready (it's part of monitoring-enhanced.yaml)
    log_info "Waiting for Grafana to be ready..."
    kubectl wait --for=condition=available --timeout=300s deployment/grafana -n "$NAMESPACE"

    log_success "Grafana deployed and ready"
}

# Verify monitoring stack
verify_deployment() {
    log_info "Verifying monitoring stack deployment..."

    # Check all pods are running
    log_info "Checking pod status..."
    kubectl get pods -n "$NAMESPACE" -l 'component in (prometheus,grafana,alertmanager,loki,promtail)'

    # Check services
    log_info "Checking services..."
    kubectl get services -n "$NAMESPACE" -l 'component in (prometheus,grafana,alertmanager,loki)'

    # Test Prometheus targets
    log_info "Testing Prometheus connectivity..."
    if kubectl exec -n "$NAMESPACE" deployment/prometheus -- wget -q -O- http://localhost:9090/-/healthy &> /dev/null; then
        log_success "Prometheus is healthy"
    else
        log_warning "Prometheus health check failed"
    fi

    # Test Grafana connectivity
    log_info "Testing Grafana connectivity..."
    if kubectl exec -n "$NAMESPACE" deployment/grafana -- wget -q -O- http://localhost:3000/api/health &> /dev/null; then
        log_success "Grafana is healthy"
    else
        log_warning "Grafana health check failed"
    fi

    # Test Alertmanager connectivity
    log_info "Testing Alertmanager connectivity..."
    if kubectl exec -n "$NAMESPACE" deployment/alertmanager -- wget -q -O- http://localhost:9093/-/healthy &> /dev/null; then
        log_success "Alertmanager is healthy"
    else
        log_warning "Alertmanager health check failed"
    fi

    # Test Loki connectivity
    log_info "Testing Loki connectivity..."
    if kubectl exec -n "$NAMESPACE" statefulset/loki -- wget -q -O- http://localhost:3100/ready &> /dev/null; then
        log_success "Loki is healthy"
    else
        log_warning "Loki health check failed"
    fi
}

# Display access information
display_access_info() {
    log_info "Monitoring stack deployed successfully!"
    echo ""
    log_info "Access Information:"
    echo ""

    # Get LoadBalancer IPs if available
    GRAFANA_IP=$(kubectl get service grafana -n "$NAMESPACE" -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "")
    PROMETHEUS_IP=$(kubectl get service prometheus -n "$NAMESPACE" -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "")
    ALERTMANAGER_IP=$(kubectl get service alertmanager -n "$NAMESPACE" -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "")

    if [ -n "$GRAFANA_IP" ]; then
        echo "📊 Grafana: http://$GRAFANA_IP:3000"
    else
        echo "📊 Grafana: kubectl port-forward -n $NAMESPACE service/grafana 3000:3000"
    fi

    if [ -n "$PROMETHEUS_IP" ]; then
        echo "🔍 Prometheus: http://$PROMETHEUS_IP:9090"
    else
        echo "🔍 Prometheus: kubectl port-forward -n $NAMESPACE service/prometheus 9090:9090"
    fi

    if [ -n "$ALERTMANAGER_IP" ]; then
        echo "🚨 Alertmanager: http://$ALERTMANAGER_IP:9093"
    else
        echo "🚨 Alertmanager: kubectl port-forward -n $NAMESPACE service/alertmanager 9093:9093"
    fi

    echo ""
    log_info "Default Credentials:"
    echo "Grafana: admin / change-me-in-production"
    echo ""
    log_warning "Remember to:"
    echo "1. Change default passwords"
    echo "2. Configure SMTP settings in Alertmanager"
    echo "3. Update Slack webhook URLs"
    echo "4. Review and customize alert rules"
    echo "5. Set up SSL certificates for production"
}

# Cleanup function
cleanup() {
    log_info "Cleaning up monitoring stack..."

    kubectl delete -f "${KUBE_DIR}/loki-stack.yaml" --ignore-not-found=true
    kubectl delete -f "${KUBE_DIR}/alertmanager.yaml" --ignore-not-found=true
    kubectl delete -f "${KUBE_DIR}/grafana-dashboards.yaml" --ignore-not-found=true
    kubectl delete -f "${KUBE_DIR}/monitoring-enhanced.yaml" --ignore-not-found=true

    log_success "Monitoring stack cleaned up"
}

# Main deployment function
deploy_monitoring_stack() {
    log_info "Starting Nexus monitoring stack deployment..."

    check_prerequisites
    deploy_rbac
    deploy_prometheus
    deploy_alertmanager
    deploy_loki
    deploy_grafana

    # Wait a bit for everything to settle
    log_info "Waiting for all components to stabilize..."
    sleep 30

    verify_deployment
    display_access_info

    log_success "Nexus monitoring stack deployment completed!"
}

# Script usage
usage() {
    echo "Usage: $0 [deploy|cleanup|verify|help]"
    echo ""
    echo "Commands:"
    echo "  deploy   - Deploy the complete monitoring stack"
    echo "  cleanup  - Remove the monitoring stack"
    echo "  verify   - Verify the current deployment"
    echo "  help     - Show this help message"
    echo ""
    echo "Environment variables:"
    echo "  NAMESPACE - Kubernetes namespace (default: nexus-production)"
    echo ""
    echo "Examples:"
    echo "  $0 deploy"
    echo "  NAMESPACE=nexus-dev $0 deploy"
    echo "  $0 cleanup"
}

# Main script logic
case "${1:-deploy}" in
    deploy)
        deploy_monitoring_stack
        ;;
    cleanup)
        cleanup
        ;;
    verify)
        check_prerequisites
        verify_deployment
        ;;
    help|--help|-h)
        usage
        ;;
    *)
        log_error "Unknown command: $1"
        usage
        exit 1
        ;;
esac
