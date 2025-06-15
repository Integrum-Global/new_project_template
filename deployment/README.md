# Deployment Configuration

Centralized deployment configurations for all MCP server applications.

## 🎯 Philosophy

**Separation of Concerns:**
- `apps/` → Application code and business logic only
- `deployment/` → How to run and deploy applications
- `infrastructure/` → Environment setup and provisioning

## 📁 Structure

```
deployment/
├── docker/                    # Docker-based deployment
│   ├── docker-compose.yml    # Complete platform stack
│   ├── docker-compose.prod.yml
│   └── services/             # Individual service Dockerfiles
├── kubernetes/               # Kubernetes manifests
│   ├── infrastructure/       # Shared services (DB, Redis, Gateway)
│   └── apps/                # Application deployments
├── helm/                     # Helm charts
│   ├── Chart.yaml           # Umbrella chart
│   └── charts/              # Per-app sub-charts
└── scripts/                  # Deployment automation
```

## 🚀 Quick Start

### Docker Deployment
```bash
# Start the complete platform
cd deployment/docker
docker-compose up -d

# Scale specific services
docker-compose up -d --scale user-management=3

# Production deployment
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Kubernetes Deployment
```bash
# Deploy infrastructure first
kubectl apply -f kubernetes/infrastructure/

# Deploy applications
kubectl apply -f kubernetes/apps/

# Or use Helm
helm install mcp-platform ./helm/
```

## 🔧 Configuration

All apps are configured via:
1. **Environment variables** (per deployment type)
2. **ConfigMaps/Secrets** (Kubernetes)
3. **App manifests** (capabilities and metadata)

## 📊 Benefits

✅ **Consistency**: Single deployment patterns across all apps
✅ **Efficiency**: Shared infrastructure, no duplication
✅ **Scalability**: Easy to add new apps
✅ **Operations**: Centralized monitoring and management
✅ **Environment Parity**: Same deployment across dev/staging/prod