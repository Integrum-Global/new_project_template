#!/bin/bash
set -euo pipefail

# Nexus Production Health Check Script
# Comprehensive health monitoring for production deployment

# Configuration
NAMESPACE="${NAMESPACE:-nexus-production}"
TIMEOUT="${TIMEOUT:-30}"
VERBOSE="${VERBOSE:-false}"

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

# Health check results
declare -a HEALTH_CHECKS=()
OVERALL_HEALTH="healthy"

# Add health check result
add_check_result() {
    local component="$1"
    local status="$2"
    local message="$3"

    HEALTH_CHECKS+=("$component|$status|$message")

    if [[ "$status" != "healthy" && "$OVERALL_HEALTH" == "healthy" ]]; then
        OVERALL_HEALTH="$status"
    elif [[ "$status" == "critical" ]]; then
        OVERALL_HEALTH="critical"
    fi
}

# Check if kubectl is available and connected
check_kubectl() {
    if ! command -v kubectl &> /dev/null; then
        add_check_result "kubectl" "critical" "kubectl not found"
        return 1
    fi

    if ! kubectl cluster-info &> /dev/null; then
        add_check_result "kubectl" "critical" "Cannot connect to cluster"
        return 1
    fi

    add_check_result "kubectl" "healthy" "Connected to cluster"
}

# Check Nexus application pods
check_nexus_app() {
    log_info "Checking Nexus application pods..."

    local pods_output
    if ! pods_output=$(kubectl get pods -n "$NAMESPACE" -l app=nexus --no-headers 2>/dev/null); then
        add_check_result "nexus-app" "critical" "Cannot get pod information"
        return 1
    fi

    if [[ -z "$pods_output" ]]; then
        add_check_result "nexus-app" "critical" "No Nexus pods found"
        return 1
    fi

    local total_pods=0
    local running_pods=0
    local ready_pods=0

    while IFS= read -r line; do
        if [[ -n "$line" ]]; then
            total_pods=$((total_pods + 1))

            # Extract status and ready count
            local status=$(echo "$line" | awk '{print $3}')
            local ready=$(echo "$line" | awk '{print $2}')

            if [[ "$status" == "Running" ]]; then
                running_pods=$((running_pods + 1))
            fi

            # Check if pod is ready (format: ready/total)
            if [[ "$ready" =~ ^([0-9]+)/([0-9]+)$ ]]; then
                local ready_count=${BASH_REMATCH[1]}
                local total_count=${BASH_REMATCH[2]}
                if [[ "$ready_count" == "$total_count" ]]; then
                    ready_pods=$((ready_pods + 1))
                fi
            fi

            if [[ "$VERBOSE" == "true" ]]; then
                echo "  Pod: $(echo "$line" | awk '{print $1}') Status: $status Ready: $ready"
            fi
        fi
    done <<< "$pods_output"

    if [[ $running_pods -eq $total_pods && $ready_pods -eq $total_pods ]]; then
        add_check_result "nexus-app" "healthy" "$running_pods/$total_pods pods running and ready"
    elif [[ $running_pods -gt 0 ]]; then
        add_check_result "nexus-app" "warning" "$running_pods/$total_pods pods running, $ready_pods/$total_pods ready"
    else
        add_check_result "nexus-app" "critical" "No pods running"
    fi
}

# Check PostgreSQL
check_postgres() {
    log_info "Checking PostgreSQL..."

    local postgres_output
    if ! postgres_output=$(kubectl get pods -n "$NAMESPACE" -l app.kubernetes.io/name=nexus-postgres --no-headers 2>/dev/null); then
        add_check_result "postgres" "warning" "Cannot get PostgreSQL pod information"
        return 1
    fi

    if [[ -z "$postgres_output" ]]; then
        add_check_result "postgres" "warning" "PostgreSQL pods not found"
        return 1
    fi

    local running_count=0
    local total_count=0

    while IFS= read -r line; do
        if [[ -n "$line" ]]; then
            total_count=$((total_count + 1))
            local status=$(echo "$line" | awk '{print $3}')
            if [[ "$status" == "Running" ]]; then
                running_count=$((running_count + 1))
            fi
        fi
    done <<< "$postgres_output"

    if [[ $running_count -eq $total_count && $total_count -gt 0 ]]; then
        add_check_result "postgres" "healthy" "$running_count/$total_count PostgreSQL instances running"
    elif [[ $running_count -gt 0 ]]; then
        add_check_result "postgres" "warning" "$running_count/$total_count PostgreSQL instances running"
    else
        add_check_result "postgres" "critical" "PostgreSQL not running"
    fi
}

# Check Redis
check_redis() {
    log_info "Checking Redis..."

    local redis_output
    if ! redis_output=$(kubectl get pods -n "$NAMESPACE" -l app.kubernetes.io/name=nexus-redis --no-headers 2>/dev/null); then
        add_check_result "redis" "warning" "Cannot get Redis pod information"
        return 1
    fi

    if [[ -z "$redis_output" ]]; then
        add_check_result "redis" "warning" "Redis pods not found"
        return 1
    fi

    local running_count=0
    local total_count=0

    while IFS= read -r line; do
        if [[ -n "$line" ]]; then
            total_count=$((total_count + 1))
            local status=$(echo "$line" | awk '{print $3}')
            if [[ "$status" == "Running" ]]; then
                running_count=$((running_count + 1))
            fi
        fi
    done <<< "$redis_output"

    if [[ $running_count -eq $total_count && $total_count -gt 0 ]]; then
        add_check_result "redis" "healthy" "$running_count/$total_count Redis instances running"
    elif [[ $running_count -gt 0 ]]; then
        add_check_result "redis" "warning" "$running_count/$total_count Redis instances running"
    else
        add_check_result "redis" "warning" "Redis not running"
    fi
}

# Check services
check_services() {
    log_info "Checking services..."

    local services=("nexus-service")
    local healthy_services=0

    for service in "${services[@]}"; do
        if kubectl get service "$service" -n "$NAMESPACE" &>/dev/null; then
            # Check if service has endpoints
            local endpoints
            if endpoints=$(kubectl get endpoints "$service" -n "$NAMESPACE" -o jsonpath='{.subsets[*].addresses[*].ip}' 2>/dev/null) && [[ -n "$endpoints" ]]; then
                healthy_services=$((healthy_services + 1))
                if [[ "$VERBOSE" == "true" ]]; then
                    echo "  Service $service: healthy (endpoints: $(echo "$endpoints" | wc -w))"
                fi
            else
                if [[ "$VERBOSE" == "true" ]]; then
                    echo "  Service $service: no endpoints"
                fi
            fi
        else
            if [[ "$VERBOSE" == "true" ]]; then
                echo "  Service $service: not found"
            fi
        fi
    done

    if [[ $healthy_services -eq ${#services[@]} ]]; then
        add_check_result "services" "healthy" "$healthy_services/${#services[@]} services have endpoints"
    elif [[ $healthy_services -gt 0 ]]; then
        add_check_result "services" "warning" "$healthy_services/${#services[@]} services have endpoints"
    else
        add_check_result "services" "critical" "No services have endpoints"
    fi
}

# Check ingress
check_ingress() {
    log_info "Checking ingress..."

    if kubectl get ingress nexus-ingress -n "$NAMESPACE" &>/dev/null; then
        add_check_result "ingress" "healthy" "Ingress configured"
    else
        add_check_result "ingress" "warning" "Ingress not found"
    fi
}

# Test application endpoints
test_endpoints() {
    log_info "Testing application endpoints..."

    # Port forward to test endpoints
    local port_forward_pid=""
    local test_port=8080

    # Start port forward in background
    kubectl port-forward -n "$NAMESPACE" service/nexus-service $test_port:80 &>/dev/null &
    port_forward_pid=$!

    # Wait for port forward to establish
    sleep 3

    # Test health endpoint
    if curl -f -s --connect-timeout 5 "http://localhost:$test_port/health" &>/dev/null; then
        add_check_result "health-endpoint" "healthy" "Health endpoint responding"
    else
        add_check_result "health-endpoint" "warning" "Health endpoint not responding"
    fi

    # Test API endpoint
    if curl -f -s --connect-timeout 5 "http://localhost:$test_port/api/v1/workflows" &>/dev/null; then
        add_check_result "api-endpoint" "healthy" "API endpoint responding"
    else
        add_check_result "api-endpoint" "warning" "API endpoint not responding"
    fi

    # Clean up port forward
    if [[ -n "$port_forward_pid" ]]; then
        kill "$port_forward_pid" 2>/dev/null || true
    fi
}

# Check monitoring stack
check_monitoring() {
    log_info "Checking monitoring stack..."

    # Check Prometheus
    if kubectl get pods -n nexus-monitoring -l app=prometheus --no-headers 2>/dev/null | grep -q Running; then
        add_check_result "prometheus" "healthy" "Prometheus running"
    else
        add_check_result "prometheus" "warning" "Prometheus not running"
    fi

    # Check Grafana
    if kubectl get pods -n nexus-monitoring -l app=grafana --no-headers 2>/dev/null | grep -q Running; then
        add_check_result "grafana" "healthy" "Grafana running"
    else
        add_check_result "grafana" "warning" "Grafana not running"
    fi
}

# Check resource usage
check_resources() {
    log_info "Checking resource usage..."

    local high_cpu_pods=0
    local high_memory_pods=0

    # Get pod metrics (requires metrics-server)
    if kubectl top pods -n "$NAMESPACE" --no-headers 2>/dev/null | while read -r line; do
        local cpu=$(echo "$line" | awk '{print $2}' | sed 's/m$//')
        local memory=$(echo "$line" | awk '{print $3}' | sed 's/Mi$//')

        # Check for high CPU (>800m = 80% of 1 core limit)
        if [[ "$cpu" =~ ^[0-9]+$ ]] && [[ $cpu -gt 800 ]]; then
            high_cpu_pods=$((high_cpu_pods + 1))
        fi

        # Check for high memory (>800Mi out of 1Gi limit)
        if [[ "$memory" =~ ^[0-9]+$ ]] && [[ $memory -gt 800 ]]; then
            high_memory_pods=$((high_memory_pods + 1))
        fi
    done; then
        if [[ $high_cpu_pods -eq 0 && $high_memory_pods -eq 0 ]]; then
            add_check_result "resources" "healthy" "Resource usage normal"
        else
            add_check_result "resources" "warning" "High resource usage detected (CPU: $high_cpu_pods, Memory: $high_memory_pods pods)"
        fi
    else
        add_check_result "resources" "warning" "Cannot get resource metrics"
    fi
}

# Print health check results
print_results() {
    echo ""
    echo "==================== HEALTH CHECK RESULTS ===================="
    echo ""

    for check in "${HEALTH_CHECKS[@]}"; do
        IFS='|' read -r component status message <<< "$check"

        case "$status" in
            "healthy")
                printf "%-20s ${GREEN}✓ HEALTHY${NC}   %s\n" "$component" "$message"
                ;;
            "warning")
                printf "%-20s ${YELLOW}⚠ WARNING${NC}   %s\n" "$component" "$message"
                ;;
            "critical")
                printf "%-20s ${RED}✗ CRITICAL${NC}  %s\n" "$component" "$message"
                ;;
        esac
    done

    echo ""
    echo "==================== OVERALL STATUS ===================="

    case "$OVERALL_HEALTH" in
        "healthy")
            echo -e "Status: ${GREEN}HEALTHY${NC} - All systems operational"
            exit 0
            ;;
        "warning")
            echo -e "Status: ${YELLOW}WARNING${NC} - Some components have issues"
            exit 1
            ;;
        "critical")
            echo -e "Status: ${RED}CRITICAL${NC} - Critical components failing"
            exit 2
            ;;
    esac
}

# Main health check function
main() {
    log_info "Starting Nexus production health check..."
    log_info "Namespace: $NAMESPACE"
    log_info "Timeout: ${TIMEOUT}s"
    echo ""

    # Run all health checks
    check_kubectl || exit 3
    check_nexus_app
    check_postgres
    check_redis
    check_services
    check_ingress
    test_endpoints
    check_monitoring
    check_resources

    # Print results
    print_results
}

# Handle command line arguments
case "${1:-check}" in
    check)
        main
        ;;
    app)
        check_kubectl || exit 3
        check_nexus_app
        print_results
        ;;
    database)
        check_kubectl || exit 3
        check_postgres
        print_results
        ;;
    monitoring)
        check_kubectl || exit 3
        check_monitoring
        print_results
        ;;
    endpoints)
        check_kubectl || exit 3
        test_endpoints
        print_results
        ;;
    *)
        echo "Usage: $0 {check|app|database|monitoring|endpoints}"
        echo ""
        echo "Commands:"
        echo "  check      - Run complete health check (default)"
        echo "  app        - Check only application pods"
        echo "  database   - Check only database components"
        echo "  monitoring - Check only monitoring stack"
        echo "  endpoints  - Test only application endpoints"
        exit 1
        ;;
esac
