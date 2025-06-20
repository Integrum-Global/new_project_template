# Deployment Guide

Complete guide for deploying client project applications using the template's infrastructure patterns.

## 🎯 Deployment Overview

This template provides multiple deployment strategies designed for different environments and use cases:

- **Development**: Local Docker Compose for rapid development
- **Staging**: Kubernetes cluster for testing and validation  
- **Production**: Enterprise-grade Kubernetes with monitoring and scaling
- **Centralized Gateway**: Unified API gateway with service discovery

## 🚀 Quick Deployment Options

### Option 1: Centralized Deployment (Recommended)

**Start entire platform with one command:**
```bash
# Start all services with unified gateway
./deployment/scripts/start.sh

# Verify deployment
curl http://localhost:8000/api/v1/discovery
curl http://localhost:8000/api/v1/tools
curl http://localhost:8000/docs

# Stop all services
./deployment/scripts/stop.sh
```

### Option 2: Individual App Deployment

**Deploy specific applications:**
```bash
# User Management App
cd apps/user_management
docker build -t user-management .
docker run -p 8001:8000 user-management

# Analytics App  
cd apps/analytics
docker build -t analytics .
docker run -p 8002:8000 analytics

# Document Processor App
cd apps/document_processor
docker build -t document-processor .
docker run -p 8003:8000 document-processor
```

## 🐳 Docker Deployment

### Development Environment

**Docker Compose Configuration:**
```yaml
# deployment/docker/docker-compose.yml
version: '3.8'

services:
  # Enterprise Gateway
  gateway:
    build: 
      context: ../../
      dockerfile: deployment/docker/services/Dockerfile.enhanced_gateway
    ports:
      - "8000:8000"
    environment:
      - DISCOVERY_ENABLED=true
      - APPS_CONFIG_PATH=/app/deployment/apps.json
    depends_on:
      - postgres
      - redis
    volumes:
      - ../../:/app
      - ./config:/app/config

  # Individual Applications
  user-management:
    build: 
      context: ../../apps/user_management
      dockerfile: ../../deployment/docker/services/Dockerfile.user_management
    ports:
      - "8001:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@postgres:5432/user_mgmt
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis

  analytics:
    build:
      context: ../../apps/analytics
      dockerfile: ../../deployment/docker/services/Dockerfile.analytics
    ports:
      - "8002:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@postgres:5432/analytics
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis

  document-processor:
    build:
      context: ../../apps/document_processor
      dockerfile: ../../deployment/docker/services/Dockerfile.document_processor
    ports:
      - "8003:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@postgres:5432/documents
      - REDIS_URL=redis://redis:6379
      - STORAGE_PATH=/app/data/documents
    depends_on:
      - postgres
      - redis
    volumes:
      - ../../data/documents:/app/data/documents

  # Infrastructure Services
  postgres:
    image: postgres:15
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
      - POSTGRES_MULTIPLE_DATABASES=user_mgmt,analytics,documents
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init-db.sql:/docker-entrypoint-initdb.d/init-multiple-databases.sh

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  # Monitoring Stack (Optional)
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./config/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
      - ./config/grafana:/etc/grafana/provisioning

volumes:
  postgres_data:
  redis_data:
  prometheus_data:
  grafana_data:
```

**Starting Development Environment:**
```bash
# Full development stack
cd deployment/docker
docker-compose up -d

# Check service health
docker-compose ps
docker-compose logs gateway

# Scale specific services
docker-compose up -d --scale user-management=2

# Stop environment
docker-compose down
```

### Production Docker Configuration

**Production Compose File:**
```yaml
# deployment/docker/docker-compose.prod.yml
version: '3.8'

services:
  gateway:
    image: your-registry/gateway:${VERSION}
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
    environment:
      - ENV=production
      - LOG_LEVEL=info
    secrets:
      - database_url
      - redis_url
      - jwt_secret

  user-management:
    image: your-registry/user-management:${VERSION}
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
    environment:
      - ENV=production
    secrets:
      - database_url
      - redis_url

  # ... other services with production configurations

secrets:
  database_url:
    external: true
  redis_url:
    external: true
  jwt_secret:
    external: true

networks:
  default:
    driver: overlay
    attachable: true
```

## ☸️ Kubernetes Deployment

### Namespace and Infrastructure

**Create Kubernetes Namespace:**
```yaml
# deployment/kubernetes/infrastructure/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: client-project
  labels:
    app.kubernetes.io/name: client-project
    app.kubernetes.io/component: namespace
```

**PostgreSQL Deployment:**
```yaml
# deployment/kubernetes/infrastructure/postgres.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: client-project
spec:
  serviceName: postgres
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:15
        ports:
        - containerPort: 5432
        env:
        - name: POSTGRES_USER
          value: postgres
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: password
        - name: POSTGRES_MULTIPLE_DATABASES
          value: user_mgmt,analytics,documents
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
  volumeClaimTemplates:
  - metadata:
      name: postgres-storage
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 20Gi

---
apiVersion: v1
kind: Service
metadata:
  name: postgres
  namespace: client-project
spec:
  selector:
    app: postgres
  ports:
  - port: 5432
    targetPort: 5432
  type: ClusterIP
```

**Redis Deployment:**
```yaml
# deployment/kubernetes/infrastructure/redis.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: client-project
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        ports:
        - containerPort: 6379
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"

---
apiVersion: v1
kind: Service
metadata:
  name: redis
  namespace: client-project
spec:
  selector:
    app: redis
  ports:
  - port: 6379
    targetPort: 6379
  type: ClusterIP
```

### Application Deployments

**User Management App:**
```yaml
# deployment/kubernetes/apps/user-management/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: user-management
  namespace: client-project
  labels:
    app: user-management
    component: backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: user-management
  template:
    metadata:
      labels:
        app: user-management
    spec:
      containers:
      - name: user-management
        image: your-registry/user-management:${VERSION}
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: database-secrets
              key: user-mgmt-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: redis-secrets
              key: url
        - name: JWT_SECRET
          valueFrom:
            secretKeyRef:
              name: jwt-secrets
              key: secret
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 15
          periodSeconds: 5

---
apiVersion: v1
kind: Service
metadata:
  name: user-management
  namespace: client-project
spec:
  selector:
    app: user-management
  ports:
  - port: 8000
    targetPort: 8000
  type: ClusterIP

---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: user-management-hpa
  namespace: client-project
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: user-management
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

**Gateway Deployment:**
```yaml
# deployment/kubernetes/infrastructure/gateway.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: gateway
  namespace: client-project
spec:
  replicas: 2
  selector:
    matchLabels:
      app: gateway
  template:
    metadata:
      labels:
        app: gateway
    spec:
      containers:
      - name: gateway
        image: your-registry/gateway:${VERSION}
        ports:
        - containerPort: 8000
        env:
        - name: DISCOVERY_ENABLED
          value: "true"
        - name: USER_MANAGEMENT_URL
          value: "http://user-management:8000"
        - name: ANALYTICS_URL
          value: "http://analytics:8000"
        - name: DOCUMENT_PROCESSOR_URL
          value: "http://document-processor:8000"
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"

---
apiVersion: v1
kind: Service
metadata:
  name: gateway
  namespace: client-project
spec:
  selector:
    app: gateway
  ports:
  - port: 8000
    targetPort: 8000
  type: LoadBalancer

---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: gateway-ingress
  namespace: client-project
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/enable-cors: "true"
spec:
  tls:
  - hosts:
    - api.yourclient.com
    secretName: gateway-tls
  rules:
  - host: api.yourclient.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: gateway
            port:
              number: 8000
```

### Deployment Scripts

**Kubernetes Deployment Script:**
```bash
#!/bin/bash
# deployment/scripts/deploy.sh

set -e

# Configuration
NAMESPACE="client-project"
VERSION=${VERSION:-"latest"}
ENVIRONMENT=${ENVIRONMENT:-"staging"}

echo "Deploying Client Project to Kubernetes..."
echo "Environment: $ENVIRONMENT"
echo "Version: $VERSION"
echo "Namespace: $NAMESPACE"

# Create namespace
kubectl apply -f deployment/kubernetes/infrastructure/namespace.yaml

# Deploy infrastructure
echo "Deploying infrastructure..."
kubectl apply -f deployment/kubernetes/infrastructure/

# Wait for infrastructure to be ready
echo "Waiting for infrastructure..."
kubectl wait --for=condition=available --timeout=300s deployment/postgres -n $NAMESPACE
kubectl wait --for=condition=available --timeout=300s deployment/redis -n $NAMESPACE

# Deploy applications
echo "Deploying applications..."
for app_dir in deployment/kubernetes/apps/*/; do
    app_name=$(basename "$app_dir")
    echo "Deploying $app_name..."
    
    # Replace version placeholder
    find "$app_dir" -name "*.yaml" -exec sed -i "s/\${VERSION}/$VERSION/g" {} \;
    
    kubectl apply -f "$app_dir"
    
    # Wait for deployment
    kubectl wait --for=condition=available --timeout=300s deployment/$app_name -n $NAMESPACE
done

# Verify deployment
echo "Verifying deployment..."
kubectl get pods -n $NAMESPACE
kubectl get services -n $NAMESPACE
kubectl get ingress -n $NAMESPACE

echo "Deployment completed successfully!"

# Get external access information
GATEWAY_IP=$(kubectl get service gateway -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
if [ -n "$GATEWAY_IP" ]; then
    echo "Gateway accessible at: http://$GATEWAY_IP:8000"
    echo "API Documentation: http://$GATEWAY_IP:8000/docs"
else
    echo "Gateway service is not yet available. Check service status with:"
    echo "kubectl get service gateway -n $NAMESPACE"
fi
```

## 🎛️ Helm Deployment

**Helm Chart Structure:**
```
deployment/helm/
├── Chart.yaml
├── values.yaml
├── values-prod.yaml
├── values-staging.yaml
└── templates/
    ├── _helpers.tpl
    ├── gateway/
    │   ├── deployment.yaml
    │   ├── service.yaml
    │   └── ingress.yaml
    ├── apps/
    │   ├── user-management/
    │   ├── analytics/
    │   └── document-processor/
    └── infrastructure/
        ├── postgres.yaml
        ├── redis.yaml
        └── secrets.yaml
```

**Chart.yaml:**
```yaml
# deployment/helm/Chart.yaml
apiVersion: v2
name: client-project
description: A Helm chart for Client Project Template
type: application
version: 0.1.0
appVersion: "1.0"

dependencies:
- name: postgresql
  version: 12.1.9
  repository: https://charts.bitnami.com/bitnami
  condition: postgresql.enabled
- name: redis
  version: 17.4.3
  repository: https://charts.bitnami.com/bitnami
  condition: redis.enabled
```

**values.yaml:**
```yaml
# deployment/helm/values.yaml
global:
  imageRegistry: your-registry.com
  imageTag: latest
  namespace: client-project

gateway:
  enabled: true
  replicaCount: 2
  image:
    repository: gateway
    tag: latest
  service:
    type: LoadBalancer
    port: 8000
  ingress:
    enabled: true
    hostname: api.yourclient.com
    tls: true

apps:
  userManagement:
    enabled: true
    replicaCount: 3
    image:
      repository: user-management
      tag: latest
    autoscaling:
      enabled: true
      minReplicas: 2
      maxReplicas: 10
      targetCPUUtilizationPercentage: 70

  analytics:
    enabled: true
    replicaCount: 2
    image:
      repository: analytics
      tag: latest

  documentProcessor:
    enabled: true
    replicaCount: 2
    image:
      repository: document-processor
      tag: latest

postgresql:
  enabled: true
  auth:
    postgresPassword: "your-secure-password"
    database: client_project
  primary:
    persistence:
      size: 20Gi

redis:
  enabled: true
  auth:
    enabled: false
  master:
    persistence:
      size: 8Gi

monitoring:
  prometheus:
    enabled: true
  grafana:
    enabled: true
    adminPassword: "admin"
```

**Helm Deployment Commands:**
```bash
# Install with Helm
helm install client-project deployment/helm/ \
    --namespace client-project \
    --create-namespace \
    --values deployment/helm/values-staging.yaml

# Upgrade deployment
helm upgrade client-project deployment/helm/ \
    --namespace client-project \
    --values deployment/helm/values-staging.yaml

# Rollback if needed
helm rollback client-project 1 --namespace client-project

# Uninstall
helm uninstall client-project --namespace client-project
```

## 📊 Monitoring and Observability

### Prometheus Monitoring

**Prometheus Configuration:**
```yaml
# deployment/docker/config/prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'gateway'
    static_configs:
      - targets: ['gateway:8000']
    metrics_path: '/metrics'

  - job_name: 'user-management'
    static_configs:
      - targets: ['user-management:8000']
    metrics_path: '/metrics'

  - job_name: 'analytics'
    static_configs:
      - targets: ['analytics:8000']
    metrics_path: '/metrics'

  - job_name: 'document-processor'
    static_configs:
      - targets: ['document-processor:8000']
    metrics_path: '/metrics'

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']
```

### Grafana Dashboards

**Application Dashboard JSON:**
```json
{
  "dashboard": {
    "title": "Client Project - Application Metrics",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{service}} - {{method}}"
          }
        ]
      },
      {
        "title": "Response Time",
        "type": "graph", 
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total{status=~\"4..|5..\"}[5m])",
            "legendFormat": "{{service}} - errors"
          }
        ]
      }
    ]
  }
}
```

## 🔐 Security and Secrets Management

### Kubernetes Secrets

**Create Secrets:**
```bash
# Database secrets
kubectl create secret generic database-secrets \
    --from-literal=user-mgmt-url="postgresql://user:pass@postgres:5432/user_mgmt" \
    --from-literal=analytics-url="postgresql://user:pass@postgres:5432/analytics" \
    --from-literal=documents-url="postgresql://user:pass@postgres:5432/documents" \
    --namespace client-project

# JWT secrets
kubectl create secret generic jwt-secrets \
    --from-literal=secret="your-super-secure-jwt-secret" \
    --namespace client-project

# Redis secrets
kubectl create secret generic redis-secrets \
    --from-literal=url="redis://redis:6379" \
    --namespace client-project
```

**Using External Secret Management:**
```yaml
# For production, use external secret management
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: vault-secret-store
  namespace: client-project
spec:
  provider:
    vault:
      server: "https://vault.company.com"
      path: "secret"
      version: "v2"
      auth:
        kubernetes:
          mountPath: "kubernetes"
          role: "client-project"
```

## 🚀 CI/CD Pipeline Integration

### GitLab CI Example

```yaml
# .gitlab-ci.yml
stages:
  - build
  - test
  - deploy-staging
  - deploy-production

variables:
  REGISTRY: your-registry.com
  NAMESPACE_STAGING: client-project-staging
  NAMESPACE_PROD: client-project-prod

build:
  stage: build
  script:
    - docker build -t $REGISTRY/gateway:$CI_COMMIT_SHA .
    - docker build -t $REGISTRY/user-management:$CI_COMMIT_SHA apps/user_management/
    - docker build -t $REGISTRY/analytics:$CI_COMMIT_SHA apps/analytics/
    - docker build -t $REGISTRY/document-processor:$CI_COMMIT_SHA apps/document_processor/
    - docker push $REGISTRY/gateway:$CI_COMMIT_SHA
    - docker push $REGISTRY/user-management:$CI_COMMIT_SHA
    - docker push $REGISTRY/analytics:$CI_COMMIT_SHA
    - docker push $REGISTRY/document-processor:$CI_COMMIT_SHA

deploy-staging:
  stage: deploy-staging
  script:
    - helm upgrade --install client-project deployment/helm/ \
        --namespace $NAMESPACE_STAGING \
        --create-namespace \
        --set global.imageTag=$CI_COMMIT_SHA \
        --values deployment/helm/values-staging.yaml
  environment:
    name: staging
    url: https://staging-api.yourclient.com
  only:
    - develop

deploy-production:
  stage: deploy-production
  script:
    - helm upgrade --install client-project deployment/helm/ \
        --namespace $NAMESPACE_PROD \
        --create-namespace \
        --set global.imageTag=$CI_COMMIT_SHA \
        --values deployment/helm/values-prod.yaml
  environment:
    name: production
    url: https://api.yourclient.com
  when: manual
  only:
    - main
```

## 📋 Deployment Checklist

### Pre-Deployment
- [ ] Environment variables configured
- [ ] Secrets created and validated
- [ ] Database migrations ready
- [ ] Infrastructure requirements met
- [ ] SSL certificates obtained (production)
- [ ] Monitoring and logging configured

### Deployment
- [ ] Infrastructure deployed successfully
- [ ] Applications deployed and healthy
- [ ] Database migrations applied
- [ ] Health checks passing
- [ ] Service discovery working
- [ ] Load balancing configured

### Post-Deployment
- [ ] End-to-end tests passing
- [ ] Monitoring alerts configured
- [ ] Backup procedures tested
- [ ] Documentation updated
- [ ] Team notified of deployment
- [ ] Rollback plan confirmed

## 🆘 Troubleshooting

### Common Issues

**Service Discovery Problems:**
```bash
# Check service registration
kubectl get services -n client-project
kubectl describe service gateway -n client-project

# Check DNS resolution
kubectl run -it --rm debug --image=busybox --restart=Never -- nslookup gateway.client-project.svc.cluster.local
```

**Database Connection Issues:**
```bash
# Check database connectivity
kubectl exec -it deployment/user-management -n client-project -- curl postgres:5432

# Check database credentials
kubectl get secret database-secrets -n client-project -o yaml
```

**Performance Issues:**
```bash
# Check resource usage
kubectl top pods -n client-project
kubectl describe hpa -n client-project

# Check application logs
kubectl logs deployment/gateway -n client-project --tail=100
```

### Recovery Procedures

**Application Rollback:**
```bash
# Helm rollback
helm rollback client-project 1 --namespace client-project

# Kubernetes rollback
kubectl rollout undo deployment/user-management -n client-project
```

**Database Recovery:**
```bash
# Restore from backup
kubectl exec -it postgres-0 -n client-project -- pg_restore -d client_project /backups/latest.sql
```

---

**This deployment guide provides comprehensive strategies for deploying your client project from development to production. Choose the deployment method that best fits your infrastructure requirements and operational capabilities.**