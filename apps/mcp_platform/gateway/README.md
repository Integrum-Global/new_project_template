# MCP Enterprise Gateway

A production-grade enterprise gateway demonstrating advanced MCP patterns for secure, scalable, and monitored tool orchestration in enterprise environments.

## Overview

This application showcases enterprise-grade MCP integration with:
- Multi-tenant support with isolation
- Advanced authentication and authorization
- API rate limiting and quotas
- Comprehensive audit logging
- High availability and failover
- Enterprise monitoring and alerting
- Compliance and governance features

## Features

- **Security First**: OAuth2/OIDC, API keys, mTLS support
- **Multi-tenancy**: Complete tenant isolation with resource limits
- **Scalability**: Horizontal scaling, load balancing, caching
- **Observability**: Metrics, tracing, logging, health checks
- **Compliance**: GDPR, SOC2, audit trails, data retention
- **High Availability**: Clustering, failover, disaster recovery

## Architecture

```
mcp_enterprise_gateway/
├── gateway/
│   ├── core/               # Core gateway functionality
│   ├── auth/               # Authentication & authorization
│   ├── routing/            # Request routing & load balancing
│   ├── middleware/         # Gateway middleware
│   └── admin/              # Admin API & UI
├── services/
│   ├── tenant/             # Tenant management
│   ├── billing/            # Usage tracking & billing
│   ├── audit/              # Audit logging
│   └── compliance/         # Compliance tools
├── infrastructure/
│   ├── monitoring/         # Monitoring stack
│   ├── security/           # Security configurations
│   └── deployment/         # Deployment configs
└── clients/
    ├── sdk/                # Client SDKs
    ├── cli/                # CLI tools
    └── dashboard/          # Web dashboard
```

## Quick Start

### 1. Prerequisites

- Docker & Docker Compose
- Kubernetes cluster (for production)
- PostgreSQL 14+
- Redis 7+
- SSL certificates

### 2. Configuration

```bash
# Copy and configure environment
cp .env.example .env
cp config/gateway.example.yaml config/gateway.yaml

# Generate certificates
./scripts/generate-certs.sh
```

### 3. Run with Docker Compose

```bash
# Development mode
docker-compose up -d

# Production mode
docker-compose -f docker-compose.prod.yml up -d
```

### 4. Deploy to Kubernetes

```bash
# Create namespace
kubectl create namespace mcp-gateway

# Apply configurations
kubectl apply -f k8s/

# Check status
kubectl get pods -n mcp-gateway
```

## Usage Examples

### Basic Authentication

```python
from mcp_enterprise_gateway import GatewayClient

# API Key authentication
client = GatewayClient(
    base_url="https://gateway.example.com",
    api_key="your-api-key"
)

# OAuth2 authentication
client = GatewayClient(
    base_url="https://gateway.example.com",
    oauth_config={
        "client_id": "your-client-id",
        "client_secret": "your-secret",
        "token_url": "https://auth.example.com/token"
    }
)
```

### Tool Execution

```python
# Execute MCP tool with automatic retry and circuit breaking
result = await client.execute_tool(
    "data_processor",
    action="transform",
    params={
        "input": "s3://bucket/data.csv",
        "operations": ["clean", "aggregate"]
    }
)
```

### Multi-tenant Usage

```python
# Tenant-specific client
tenant_client = client.for_tenant("tenant-123")

# Execute with tenant isolation
result = await tenant_client.execute_tool(
    "analytics",
    params={"query": "SELECT * FROM sales"}
)
```

## Enterprise Features

### 1. Authentication & Authorization

```yaml
auth:
  providers:
    - type: oauth2
      issuer: https://auth.company.com
      audience: mcp-gateway
    - type: api_key
      header: X-API-Key
    - type: mtls
      ca_cert: /certs/ca.pem

  rbac:
    roles:
      - name: admin
        permissions: ["*"]
      - name: developer
        permissions: ["tools:execute", "tools:list"]
      - name: viewer
        permissions: ["tools:list"]
```

### 2. Rate Limiting

```yaml
rate_limiting:
  default:
    requests_per_minute: 60
    burst: 100

  tiers:
    - name: bronze
      requests_per_minute: 100
      requests_per_day: 10000
    - name: silver
      requests_per_minute: 500
      requests_per_day: 100000
    - name: gold
      requests_per_minute: 2000
      requests_per_day: unlimited
```

### 3. Multi-tenancy

```yaml
tenancy:
  isolation: strict
  resource_limits:
    cpu: 4
    memory: 8Gi
    storage: 100Gi

  data_separation:
    strategy: database_per_tenant
    encryption: per_tenant_key
```

### 4. Monitoring & Alerting

```yaml
monitoring:
  metrics:
    - prometheus
    - datadog

  tracing:
    provider: jaeger
    sampling_rate: 0.1

  alerts:
    - name: high_error_rate
      condition: error_rate > 0.05
      action: pagerduty
    - name: slow_response
      condition: p95_latency > 2s
      action: slack
```

### 5. Compliance

```yaml
compliance:
  standards:
    - GDPR
    - SOC2
    - HIPAA

  data_retention:
    audit_logs: 7_years
    api_logs: 90_days
    metrics: 13_months

  encryption:
    at_rest: AES-256
    in_transit: TLS 1.3
```

## API Reference

### Gateway API

```
# Health check
GET /health

# Tool execution
POST /api/v1/tools/{tool_name}/execute
{
  "action": "process",
  "params": {...},
  "options": {
    "timeout": 30,
    "retry": 3
  }
}

# List available tools
GET /api/v1/tools

# Get tool details
GET /api/v1/tools/{tool_name}
```

### Admin API

```
# Tenant management
POST /api/v1/admin/tenants
GET /api/v1/admin/tenants
GET /api/v1/admin/tenants/{tenant_id}
PUT /api/v1/admin/tenants/{tenant_id}
DELETE /api/v1/admin/tenants/{tenant_id}

# User management
POST /api/v1/admin/users
GET /api/v1/admin/users
PUT /api/v1/admin/users/{user_id}/roles

# Usage analytics
GET /api/v1/admin/usage
GET /api/v1/admin/usage/tenant/{tenant_id}
```

## Client SDKs

### Python SDK

```python
from mcp_enterprise_gateway import Gateway, Tool

# Initialize gateway
gateway = Gateway(
    url="https://gateway.example.com",
    auth={"api_key": "xxx"}
)

# Define custom tool
@gateway.tool("custom_processor")
class CustomProcessor(Tool):
    async def execute(self, data: dict) -> dict:
        # Process data
        return {"result": "processed"}

# Use the tool
result = await gateway.tools.custom_processor(data={"input": "test"})
```

### JavaScript/TypeScript SDK

```typescript
import { Gateway } from '@mcp/enterprise-gateway';

const gateway = new Gateway({
  url: 'https://gateway.example.com',
  auth: { apiKey: 'xxx' }
});

// Execute tool
const result = await gateway.tools.execute('data_processor', {
  action: 'transform',
  params: { input: 'data.csv' }
});
```

## CLI Usage

```bash
# Configure CLI
mcp-gateway config set url https://gateway.example.com
mcp-gateway auth login

# Execute tools
mcp-gateway tools list
mcp-gateway tools execute data_processor --params '{"input": "data.csv"}'

# Admin operations
mcp-gateway admin tenants list
mcp-gateway admin tenants create --name "New Tenant"
mcp-gateway admin usage --tenant tenant-123
```

## Production Deployment

### 1. High Availability Setup

```yaml
# k8s/gateway-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mcp-gateway
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
```

### 2. Load Balancing

```yaml
# k8s/gateway-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: mcp-gateway
spec:
  type: LoadBalancer
  sessionAffinity: ClientIP
```

### 3. Auto-scaling

```yaml
# k8s/gateway-hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: mcp-gateway
spec:
  minReplicas: 3
  maxReplicas: 20
  targetCPUUtilizationPercentage: 70
```

### 4. Monitoring Stack

- **Prometheus**: Metrics collection
- **Grafana**: Dashboards and visualization
- **Jaeger**: Distributed tracing
- **ELK Stack**: Log aggregation

### 5. Security Hardening

- Network policies
- Pod security policies
- Secret management (Vault)
- Regular security scanning

## Performance Optimization

1. **Caching Strategy**
   - Redis for session cache
   - CDN for static assets
   - Tool result caching

2. **Database Optimization**
   - Connection pooling
   - Read replicas
   - Query optimization

3. **Resource Management**
   - CPU/Memory limits
   - Request queuing
   - Circuit breakers

## Troubleshooting

### Common Issues

1. **Authentication Failures**
   - Check token expiration
   - Verify CORS settings
   - Review audit logs

2. **Performance Issues**
   - Check rate limits
   - Monitor resource usage
   - Review slow query logs

3. **Tool Execution Errors**
   - Check tool availability
   - Verify permissions
   - Review error logs

### Debug Mode

```bash
# Enable debug logging
export GATEWAY_LOG_LEVEL=DEBUG

# Enable request tracing
export GATEWAY_TRACE_REQUESTS=true

# Run with verbose output
mcp-gateway --verbose
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

## License

Enterprise License - see [LICENSE](LICENSE) for details.
