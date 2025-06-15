# Multi-App Deployment Guide

Comprehensive guide for deploying multiple Kailash applications using Docker and Kubernetes with automatic discovery and orchestration.

## 🎯 Overview

This deployment system automatically discovers apps in the `apps/` directory and generates appropriate Docker and Kubernetes configurations for seamless multi-app deployment.

### Key Features

✅ **Dynamic App Discovery** - Automatically finds and deploys all apps with `manifest.yaml`  
✅ **Multi-Platform Support** - Docker, Kubernetes, or both simultaneously  
✅ **Environment Management** - Development, staging, and production configurations  
✅ **Health Monitoring** - Built-in health checks and monitoring stack  
✅ **Service Mesh** - Automatic service discovery and load balancing  
✅ **Security** - Secrets management and access control

## 📁 Structure

```
deployment/
├── docker/                           # Docker deployment
│   ├── docker-compose.dynamic.yml    # Base infrastructure services
│   ├── Dockerfile.template           # Universal app Dockerfile
│   └── services/                     # Generated app-specific Dockerfiles
├── kubernetes/                       # Kubernetes deployment
│   ├── infrastructure/               # Shared services (DB, Redis, etc.)
│   └── apps/                        # Generated app manifests
├── scripts/
│   ├── deploy-apps.py                # Dynamic deployment generator
│   └── deploy.sh                     # Main deployment script
└── helm/                            # Helm charts (optional)
```

## 🚀 Quick Start

### Prerequisites

**For Docker:**
- Docker Engine 20.10+
- Docker Compose 2.0+

**For Kubernetes:**
- kubectl 1.24+
- Kubernetes cluster (local or cloud)

**For Both:**
- Python 3.11+
- Apps with `manifest.yaml` files

### 1. Verify App Configuration

Ensure your apps have proper manifest files:

```yaml
# apps/my-app/manifest.yaml
name: my-app
version: 1.0.0
type: api  # or 'mcp' or 'hybrid'
description: My awesome application

capabilities:
  api:
    enabled: true
    port: 8000
    framework: fastapi

dependencies:
  required: []
  optional:
    - postgres
    - redis

deployment:
  enabled: true
  health_check: /health
  environment:
    - LOG_LEVEL=INFO
    - API_HOST=0.0.0.0
```

### 2. Deploy with Docker

```bash
# Deploy all apps (development)
./deployment/scripts/deploy.sh

# Deploy specific apps
./deployment/scripts/deploy.sh -a user-management,analytics

# Deploy to production
./deployment/scripts/deploy.sh -e production

# Dry run (generate configs only)
./deployment/scripts/deploy.sh -d
```

### 3. Deploy with Kubernetes

```bash
# Deploy to Kubernetes (development)
./deployment/scripts/deploy.sh -m kubernetes

# Deploy to production cluster
./deployment/scripts/deploy.sh -m kubernetes -e production

# Deploy with both Docker and Kubernetes
./deployment/scripts/deploy.sh -m both
```

### 4. Check Deployment Status

```bash
# View deployment status
./deployment/scripts/deploy.sh status

# Docker services
docker-compose -f deployment/docker/docker-compose.generated.yml ps

# Kubernetes services
kubectl get all -n kailash-platform
```

## 🐳 Docker Deployment

### Architecture

The Docker deployment creates:

- **Infrastructure Services**: PostgreSQL, Redis, Prometheus, Grafana
- **API Gateway**: Central routing and load balancing
- **App Services**: One container per app
- **Monitoring**: Built-in metrics and observability

### Service Discovery

Apps are automatically registered with the gateway:

```python
# Automatic service registration
GET http://localhost:8080/api/v1/services
{
  "services": [
    {"name": "my-app", "url": "http://my-app:8000", "health": "healthy"},
    {"name": "analytics", "url": "http://analytics:8001", "health": "healthy"}
  ]
}
```

## ☸️ Kubernetes Deployment

### Architecture

The Kubernetes deployment creates:

- **Namespace**: `kailash-platform` for resource isolation
- **Infrastructure**: PostgreSQL, Redis with persistent storage
- **Applications**: Deployment, Service, ConfigMap, Secrets per app
- **Ingress**: External traffic routing
- **HPA**: Horizontal Pod Autoscaling

### Scaling

Automatically configured Horizontal Pod Autoscaler:

```bash
# Manual scaling
kubectl scale deployment my-app --replicas=3 -n kailash-platform

# Auto-scaling based on CPU/memory
kubectl get hpa -n kailash-platform
```

## 🔧 Advanced Configuration

### Environment-Specific Settings

```bash
# Development (default)
./deployment/scripts/deploy.sh -e development

# Staging
./deployment/scripts/deploy.sh -e staging

# Production (enhanced security, monitoring)
./deployment/scripts/deploy.sh -e production
```

### Custom App Selection

```bash
# Deploy specific apps only
./deployment/scripts/deploy.sh -a "user-management,analytics,document-processor"

# Exclude template apps automatically
# (any app directory starting with '_' is ignored)
```

## 📊 Monitoring & Observability

### Built-in Stack

**Prometheus** (`http://localhost:9090`)
- Metrics collection from all apps
- Custom dashboards and alerts
- Service discovery integration

**Grafana** (`http://localhost:3000`)
- Pre-configured dashboards
- App performance metrics
- Infrastructure monitoring

### Health Checks

All apps automatically get:

```yaml
# Kubernetes liveness probe
livenessProbe:
  httpGet:
    path: /health
    port: http
  initialDelaySeconds: 30
  periodSeconds: 10

# Docker health check
HEALTHCHECK --interval=30s --timeout=10s \
  CMD curl -f http://localhost:8000/health || exit 1
```

## 🔒 Security

### Secrets Management

**Docker**: Environment variables and files
```bash
# Set secure passwords
export POSTGRES_PASSWORD=secure_random_password
export REDIS_PASSWORD=another_secure_password
```

**Kubernetes**: Native secrets
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: database-secret
  namespace: kailash-platform
type: Opaque
data:
  username: <base64-encoded>
  password: <base64-encoded>
  url: <base64-encoded>
```

## 🛠 Troubleshooting

### Common Issues

**App Not Starting**
```bash
# Check logs
docker-compose -f deployment/docker/docker-compose.generated.yml logs my-app
kubectl logs deployment/my-app -n kailash-platform

# Check health
curl http://localhost:8080/api/v1/services
kubectl get pods -n kailash-platform
```

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
./deployment/scripts/deploy.sh -e development

# Dry run to check generated configs
./deployment/scripts/deploy.sh -d
```

### Cleanup

```bash
# Clean up Docker deployment
./deployment/scripts/deploy.sh cleanup

# Or manually
docker-compose -f deployment/docker/docker-compose.generated.yml down -v

# Clean up Kubernetes deployment
kubectl delete namespace kailash-platform
```

## 📚 Integration Examples

### Adding a New App

1. **Create app structure**:
```bash
cp -r apps/_template apps/my-new-app
cd apps/my-new-app
```

2. **Configure manifest**:
```yaml
# apps/my-new-app/manifest.yaml
name: my-new-app
type: api
capabilities:
  api:
    enabled: true
    port: 8002
```

3. **Deploy automatically**:
```bash
./deployment/scripts/deploy.sh  # Discovers and deploys new app
```

## 🎯 Best Practices

### Development Workflow

1. **Local Development**: Use Docker for fast iteration
2. **Testing**: Deploy to Kubernetes staging environment
3. **Production**: Multi-zone Kubernetes with monitoring

### Security Checklist

- ✅ Use secrets for sensitive data
- ✅ Enable TLS for external traffic
- ✅ Implement proper RBAC
- ✅ Regular security updates
- ✅ Network policies for isolation

---

**Next Steps**: 
- Set up your first app with `apps/_template`
- Configure monitoring dashboards
- Implement CI/CD integration
- Scale to production requirements