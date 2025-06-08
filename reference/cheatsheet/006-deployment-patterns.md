# Deployment Patterns - Production Solutions

Production deployment patterns and configurations for Kailash-based solutions.

## 🐳 Docker Deployment

### Basic Docker Setup
```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY data/ ./data/
COPY config/ ./config/

# Set environment variables
ENV PYTHONPATH=/app/src
ENV KAILASH_LOG_LEVEL=INFO

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run application
CMD ["python", "-m", "solutions.main"]
```

### Docker Compose for Development
```yaml
# docker-compose.yml
version: '3.8'

services:
  kailash-solution:
    build: .
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/kailash_db
      - REDIS_URL=redis://redis:6379
      - API_TOKEN=${API_TOKEN}
    ports:
      - "8000:8000"
    depends_on:
      - db
      - redis
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs

  db:
    image: postgres:15
    environment:
      POSTGRES_DB: kailash_db
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

## ☁️ Cloud Deployment

### AWS ECS Deployment
```json
{
  "family": "kailash-solution",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::account:role/kailashTaskRole",
  "containerDefinitions": [
    {
      "name": "kailash-app",
      "image": "your-account.dkr.ecr.region.amazonaws.com/kailash-solution:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "KAILASH_ENV",
          "value": "production"
        }
      ],
      "secrets": [
        {
          "name": "DATABASE_URL",
          "valueFrom": "arn:aws:secretsmanager:region:account:secret:kailash-db-url"
        },
        {
          "name": "API_TOKEN",
          "valueFrom": "arn:aws:secretsmanager:region:account:secret:api-token"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/kailash-solution",
          "awslogs-region": "us-west-2",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

### Kubernetes Deployment
```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: kailash-solution
  labels:
    app: kailash-solution
spec:
  replicas: 3
  selector:
    matchLabels:
      app: kailash-solution
  template:
    metadata:
      labels:
        app: kailash-solution
    spec:
      containers:
      - name: kailash-app
        image: your-registry/kailash-solution:latest
        ports:
        - containerPort: 8000
        env:
        - name: KAILASH_ENV
          value: "production"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: kailash-secrets
              key: database-url
        - name: API_TOKEN
          valueFrom:
            secretKeyRef:
              name: kailash-secrets
              key: api-token
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10

---
apiVersion: v1
kind: Service
metadata:
  name: kailash-solution-service
spec:
  selector:
    app: kailash-solution
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8000
  type: LoadBalancer
```

## 📊 Monitoring and Observability

### Health Check Implementation
```python
# src/health.py
from fastapi import FastAPI
from kailash.runtime import LocalRuntime
import psutil
import asyncio

app = FastAPI()

@app.get("/health")
async def health_check():
    """Basic health check endpoint"""
    try:
        # Check runtime status
        runtime = LocalRuntime()
        runtime_status = runtime.get_status()
        
        # Check system resources
        memory_percent = psutil.virtual_memory().percent
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Check database connectivity
        db_status = await check_database()
        
        status = {
            "status": "healthy",
            "runtime": runtime_status,
            "system": {
                "memory_percent": memory_percent,
                "cpu_percent": cpu_percent
            },
            "database": db_status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Determine overall health
        if memory_percent > 90 or cpu_percent > 90:
            status["status"] = "degraded"
        if not db_status["connected"]:
            status["status"] = "unhealthy"
            
        return status
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

async def check_database():
    """Check database connectivity"""
    try:
        # Implement database ping
        return {"connected": True, "response_time_ms": 5}
    except:
        return {"connected": False, "error": "Connection failed"}
```

### Logging Configuration
```python
# src/logging_config.py
import logging
import json
from datetime import datetime

class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
            
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 
                          'pathname', 'filename', 'module', 'lineno', 
                          'funcName', 'created', 'msecs', 'relativeCreated', 
                          'thread', 'threadName', 'processName', 'process',
                          'exc_info', 'exc_text', 'stack_info']:
                log_entry[key] = value
                
        return json.dumps(log_entry)

def setup_logging():
    """Configure production logging"""
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Console handler with JSON formatting
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(JsonFormatter())
    logger.addHandler(console_handler)
    
    # Configure Kailash logging
    kailash_logger = logging.getLogger('kailash')
    kailash_logger.setLevel(logging.INFO)
```

## 🔒 Security Configuration

### Production Security Setup
```python
# src/security_config.py
from kailash.security import SecurityConfig
from kailash.access_control import AccessControlManager

def setup_production_security():
    """Configure security for production deployment"""
    
    # Security configuration
    security_config = SecurityConfig(
        encryption_key="${ENCRYPTION_KEY}",
        enable_input_validation=True,
        enable_output_sanitization=True,
        max_execution_time=300,  # 5 minutes
        max_memory_usage="1GB",
        allowed_file_types=[".csv", ".json", ".txt"],
        sandbox_mode=True
    )
    
    # Access control
    access_control = AccessControlManager(
        jwt_secret="${JWT_SECRET}",
        jwt_algorithm="HS256",
        session_timeout=3600,  # 1 hour
        require_mfa=True
    )
    
    return security_config, access_control
```

### Environment Variables Template
```bash
# .env.production
# Database
DATABASE_URL=postgresql://user:password@db-host:5432/production_db

# API Keys
API_TOKEN=your-production-api-token
EXTERNAL_API_KEY=external-service-key

# Security
ENCRYPTION_KEY=your-32-byte-encryption-key
JWT_SECRET=your-jwt-secret-key

# Monitoring
LOG_LEVEL=INFO
METRICS_ENDPOINT=https://metrics.your-company.com

# Feature Flags
ENABLE_CACHING=true
ENABLE_RATE_LIMITING=true
MAX_CONCURRENT_WORKFLOWS=10
```

## 🚀 CI/CD Pipeline

### GitHub Actions Deployment
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    - name: Run tests
      run: pytest tests/
    - name: Validate workflows
      run: python scripts/validate_workflows.py

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
    - uses: actions/checkout@v3
    
    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v2
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: us-west-2
    
    - name: Build and push Docker image
      run: |
        aws ecr get-login-password | docker login --username AWS --password-stdin $ECR_REGISTRY
        docker build -t $ECR_REGISTRY/kailash-solution:$GITHUB_SHA .
        docker push $ECR_REGISTRY/kailash-solution:$GITHUB_SHA
        docker tag $ECR_REGISTRY/kailash-solution:$GITHUB_SHA $ECR_REGISTRY/kailash-solution:latest
        docker push $ECR_REGISTRY/kailash-solution:latest
    
    - name: Deploy to ECS
      run: |
        aws ecs update-service \
          --cluster production-cluster \
          --service kailash-solution \
          --force-new-deployment
```

## 📋 Best Practices

### ✅ Production Deployment Checklist
- [ ] Environment variables configured (no hardcoded secrets)
- [ ] Health checks implemented
- [ ] Structured logging configured
- [ ] Monitoring and alerting set up
- [ ] Resource limits defined (CPU, memory)
- [ ] Security configuration enabled
- [ ] Database migrations tested
- [ ] Backup and recovery procedures documented
- [ ] Load testing completed
- [ ] Rollback procedure defined

### ❌ Avoid in Production
- Hardcoded credentials or API keys
- Debug mode enabled
- Excessive logging (performance impact)
- Missing resource limits
- Unencrypted data transmission
- Single points of failure
- Untested deployment scripts

## 🔗 Related Patterns

- **[Environment Variables](016-environment-variables.md)** - Configuration management
- **[Integration Patterns](005-integration-patterns.md)** - External system integration
- **[Workflow as REST API](015-workflow-as-rest-api.md)** - API deployment