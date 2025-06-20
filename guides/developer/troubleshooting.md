# Project Troubleshooting Guide

Common issues, solutions, and debugging strategies specific to this client project template.

## 🎯 Quick Diagnosis

### Problem Categories

| Symptom | Likely Category | Quick Check |
|---------|----------------|-------------|
| Apps won't start | [Environment Setup](#environment-setup-issues) | Check `.env` file and dependencies |
| Cross-app calls failing | [Multi-App Coordination](#multi-app-coordination-issues) | Verify service discovery and networking |
| Workflows not executing | [SDK Integration](#sdk-integration-issues) | Check Kailash SDK configuration |
| Database errors | [Database Connectivity](#database-connectivity-issues) | Test database connections |
| Deployment failures | [Deployment Issues](#deployment-issues) | Check Docker/Kubernetes configurations |
| Performance problems | [Performance Issues](#performance-issues) | Monitor resource usage and bottlenecks |

## 🔧 Environment Setup Issues

### Problem: "Cannot import kailash" Error

**Symptoms:**
```bash
ImportError: No module named 'kailash'
ModuleNotFoundError: No module named 'kailash'
```

**Solutions:**
```bash
# 1. Verify Kailash SDK installation
pip list | grep kailash

# 2. Install/reinstall Kailash SDK
pip install kailash --upgrade

# 3. For development installation
pip install -e .

# 4. Check Python path
python -c "import sys; print(sys.path)"

# 5. Virtual environment issues
which python
which pip
source venv/bin/activate  # Activate virtual environment
```

### Problem: Environment Variables Not Loading

**Symptoms:**
```bash
KeyError: 'DATABASE_URL'
AttributeError: 'NoneType' object has no attribute...
```

**Solutions:**
```bash
# 1. Check .env file exists
ls -la .env

# 2. Copy from template if missing
cp .env.template .env

# 3. Verify .env file format
cat .env
# Should have: KEY=value (no spaces around =)

# 4. Check environment loading in app
python -c "import os; print(os.getenv('DATABASE_URL'))"

# 5. Restart application after .env changes
```

### Problem: Database Connection Fails

**Symptoms:**
```bash
sqlalchemy.exc.OperationalError: could not connect to server
psycopg2.OperationalError: FATAL: database does not exist
```

**Solutions:**
```bash
# 1. Check database is running
docker ps | grep postgres

# 2. Start database if needed
docker-compose up -d postgres

# 3. Verify connection string format
echo $DATABASE_URL
# Should be: postgresql://user:password@host:port/database

# 4. Test direct connection
psql $DATABASE_URL

# 5. Check database exists
psql -h localhost -U postgres -l

# 6. Create database if missing
createdb -h localhost -U postgres your_database_name
```

## 🔄 Multi-App Coordination Issues

### Problem: Cross-App Workflows Fail

**Symptoms:**
```bash
ConnectionError: Unable to connect to service
TimeoutError: Request timed out
KeyError: 'expected_data_field'
```

**Diagnosis:**
```bash
# 1. Check service discovery
curl http://localhost:8000/api/v1/discovery

# 2. Verify app health endpoints
curl http://localhost:8001/health  # user_management
curl http://localhost:8002/health  # analytics
curl http://localhost:8003/health  # document_processor

# 3. Check gateway routing
curl http://localhost:8000/api/v1/tools

# 4. Verify network connectivity
docker network ls
docker network inspect client-project_default
```

**Solutions:**
```bash
# 1. Restart gateway service
docker-compose restart gateway

# 2. Check app registration
# Verify manifest.yaml files in each app

# 3. Update service URLs in environment
# Check GATEWAY_URL, USER_MANAGEMENT_URL, etc.

# 4. Verify data contracts
# Check data mapping in cross-app workflows
```

### Problem: Event-Driven Coordination Not Working

**Symptoms:**
```bash
# Events published but not received
# Cross-app state inconsistency
# Missing data synchronization
```

**Diagnosis:**
```bash
# 1. Check message queue status
docker-compose logs redis
curl http://localhost:6379/ping

# 2. Verify event publishing
# Check application logs for event publication

# 3. Test event consumption
# Check consumer logs for event processing

# 4. Validate event format
# Ensure event schemas match between publisher and consumer
```

**Solutions:**
```bash
# 1. Restart message queue
docker-compose restart redis

# 2. Clear event queue if corrupted
redis-cli FLUSHALL

# 3. Verify event handlers are registered
# Check solutions/shared_services/messaging.py

# 4. Add event logging for debugging
# Temporarily add debug logging to event handlers
```

## 🛠️ SDK Integration Issues

### Problem: Workflow Execution Fails

**Symptoms:**
```bash
WorkflowExecutionError: Node 'xyz' failed to execute
NodeConfigurationError: Missing required parameter
RuntimeError: Workflow runtime not configured
```

**Diagnosis:**
```bash
# 1. Check SDK version
python -c "import kailash; print(kailash.__version__)"

# 2. Verify node configuration
# Check node parameter definitions

# 3. Test runtime configuration
python -c "
from kailash.runtime import LocalRuntime
runtime = LocalRuntime()
print('Runtime configured successfully')
"

# 4. Validate workflow definition
# Check workflow node connections and data mapping
```

**Solutions:**
```bash
# 1. Update SDK to latest version
pip install kailash --upgrade

# 2. Check node parameter requirements
# Refer to sdk-users/nodes/node-selection-guide.md

# 3. Fix runtime configuration
# Ensure LocalRuntime has proper settings

# 4. Validate workflow syntax
# Test workflow execution with simple inputs

# 5. Check for SDK breaking changes
# Review sdk-users/migration-guides/ for version updates
```

### Problem: Custom Nodes Not Working

**Symptoms:**
```bash
AttributeError: Node 'CustomNode' not found
ImportError: cannot import name 'CustomNode'
TypeError: CustomNode() missing required parameters
```

**Diagnosis:**
```bash
# 1. Check custom node registration
# Verify node is properly imported and registered

# 2. Validate node inheritance
# Ensure custom node inherits from proper base class

# 3. Check parameter definition
# Verify get_parameters() method implementation

# 4. Test node isolation
python -c "
from apps.my_app.nodes.custom_node import CustomNode
node = CustomNode()
print('Node imports successfully')
"
```

**Solutions:**
```bash
# 1. Fix node inheritance
# Ensure custom node follows SDK patterns

# 2. Correct parameter definition
# Follow examples in sdk-users/templates/nodes/

# 3. Register node properly
# Add to workflow builder node registry

# 4. Check naming convention
# Ensure node name ends with "Node"
```

## 💾 Database Connectivity Issues

### Problem: Database Migration Fails

**Symptoms:**
```bash
alembic.util.exc.CommandError: Can't locate revision
psycopg2.errors.DuplicateTable: relation already exists
sqlalchemy.exc.IntegrityError: duplicate key violation
```

**Diagnosis:**
```bash
# 1. Check migration history
alembic history

# 2. Verify current database state
alembic current

# 3. Check migration files
ls -la migrations/versions/

# 4. Test database connection
alembic check
```

**Solutions:**
```bash
# 1. Reset migration state
alembic stamp head

# 2. Create new migration
alembic revision --autogenerate -m "description"

# 3. Force migration (use with caution)
alembic upgrade head --sql  # Review SQL first
alembic upgrade head

# 4. Manual database cleanup if needed
# Connect to database and fix conflicts manually
```

### Problem: Connection Pool Exhaustion

**Symptoms:**
```bash
sqlalchemy.exc.TimeoutError: QueuePool limit exceeded
psycopg2.pool.PoolError: connection pool exhausted
```

**Diagnosis:**
```bash
# 1. Check pool configuration
python -c "
from sqlalchemy import create_engine
engine = create_engine('your_db_url')
print(f'Pool size: {engine.pool.size()}')
print(f'Checked out: {engine.pool.checkedout()}')
"

# 2. Monitor database connections
# Check active connections in database
```

**Solutions:**
```bash
# 1. Increase pool size
# Update database configuration:
# pool_size=20, max_overflow=30

# 2. Fix connection leaks
# Ensure proper session cleanup in code

# 3. Implement connection pooling
# Use proper context managers for database sessions

# 4. Monitor and alert on pool usage
# Add metrics collection for pool status
```

## 🚢 Deployment Issues

### Problem: Docker Build Fails

**Symptoms:**
```bash
Error: failed to solve: process "/bin/sh -c pip install -r requirements.txt" did not complete successfully
ModuleNotFoundError during container build
Permission denied: '/app/some-file'
```

**Diagnosis:**
```bash
# 1. Check Dockerfile syntax
docker build --no-cache -t test-build .

# 2. Verify base image
docker pull python:3.11-slim

# 3. Check file permissions
ls -la Dockerfile requirements.txt

# 4. Test requirements.txt
pip install -r requirements.txt
```

**Solutions:**
```bash
# 1. Fix Dockerfile issues
# Ensure proper layer ordering and caching

# 2. Update requirements.txt
# Pin specific versions for reproducible builds

# 3. Fix permission issues
# Use proper USER directive in Dockerfile

# 4. Clear Docker cache
docker system prune -f
docker build --no-cache -t your-app .
```

### Problem: Kubernetes Deployment Fails

**Symptoms:**
```bash
Pod status: CrashLoopBackOff
Pod status: ImagePullBackOff
Service endpoints not ready
```

**Diagnosis:**
```bash
# 1. Check pod status
kubectl get pods -n client-project

# 2. Check pod logs
kubectl logs deployment/user-management -n client-project

# 3. Describe problematic pods
kubectl describe pod pod-name -n client-project

# 4. Check service endpoints
kubectl get endpoints -n client-project
```

**Solutions:**
```bash
# 1. Fix image pull issues
# Verify image exists and access credentials

# 2. Fix application startup
# Check environment variables and health checks

# 3. Adjust resource limits
# Update CPU/memory requests and limits

# 4. Fix service configuration
# Verify service selectors and ports

# 5. Check namespace and RBAC
kubectl auth can-i create pods --namespace client-project
```

### Problem: Service Discovery Not Working

**Symptoms:**
```bash
# Gateway can't find apps
# Apps can't communicate with each other
# Health checks failing
```

**Diagnosis:**
```bash
# 1. Check service registration
kubectl get services -n client-project

# 2. Test DNS resolution
kubectl run -it --rm debug --image=busybox --restart=Never -- nslookup user-management.client-project.svc.cluster.local

# 3. Check gateway configuration
kubectl logs deployment/gateway -n client-project

# 4. Verify app health endpoints
kubectl exec -it deployment/user-management -n client-project -- curl localhost:8000/health
```

**Solutions:**
```bash
# 1. Fix service definitions
# Ensure correct selectors and ports

# 2. Update gateway routing
# Verify service URLs in gateway configuration

# 3. Fix DNS resolution
# Check cluster DNS configuration

# 4. Restart discovery components
kubectl rollout restart deployment/gateway -n client-project
```

## ⚡ Performance Issues

### Problem: Slow Workflow Execution

**Symptoms:**
```bash
# Workflows taking longer than expected
# High CPU/memory usage during execution
# Timeouts in cross-app communication
```

**Diagnosis:**
```bash
# 1. Profile workflow execution
# Add timing logs to workflow steps

# 2. Check resource usage
docker stats
kubectl top pods -n client-project

# 3. Monitor database performance
# Check slow query logs

# 4. Analyze network latency
# Test cross-app communication timing
```

**Solutions:**
```bash
# 1. Optimize workflow design
# Parallelize independent operations
# Cache frequently accessed data

# 2. Tune database queries
# Add appropriate indexes
# Optimize query patterns

# 3. Scale horizontally
# Increase replica count
kubectl scale deployment user-management --replicas=5 -n client-project

# 4. Optimize container resources
# Adjust CPU/memory limits
# Use performance profiling tools
```

### Problem: High Memory Usage

**Symptoms:**
```bash
# Containers getting OOMKilled
# Slow garbage collection
# Memory leaks over time
```

**Diagnosis:**
```bash
# 1. Monitor memory usage
docker stats --format "table {{.Container}}\t{{.MemUsage}}\t{{.MemPerc}}"

# 2. Profile memory usage
# Use memory profiling tools

# 3. Check for memory leaks
# Monitor memory usage over time

# 4. Analyze workflow memory patterns
# Check for large data structures in workflows
```

**Solutions:**
```bash
# 1. Optimize data handling
# Process data in chunks
# Clear large objects after use

# 2. Adjust container limits
# Increase memory limits if justified
# Set appropriate requests

# 3. Optimize Python memory usage
# Use generators instead of lists
# Implement proper garbage collection

# 4. Consider memory-efficient alternatives
# Use streaming for large data processing
```

## 🔍 Debugging Strategies

### Systematic Debugging Approach

**Step 1: Isolate the Problem**
```bash
# 1. Identify the failing component
# App-level, solutions-level, or infrastructure?

# 2. Check recent changes
git log --oneline -10

# 3. Verify environment consistency
# Compare working vs non-working environments
```

**Step 2: Gather Information**
```bash
# 1. Collect logs
docker-compose logs service-name
kubectl logs deployment/service-name -n client-project

# 2. Check system resources
docker stats
kubectl top nodes
kubectl top pods -n client-project

# 3. Test components in isolation
# Test individual apps separately
# Test cross-app communication
```

**Step 3: Test Hypotheses**
```bash
# 1. Minimal reproduction case
# Create simplest test that reproduces the issue

# 2. Change one variable at a time
# Systematic elimination of potential causes

# 3. Use known-good configurations
# Revert to last known working state if needed
```

### Logging and Monitoring

**Enhanced Logging for Debugging:**
```python
# Add to workflow nodes for debugging
import logging
logging.basicConfig(level=logging.DEBUG)

# Add correlation IDs for cross-app tracing
import uuid
correlation_id = str(uuid.uuid4())

# Log at decision points
logger.info(f"Workflow step X completed", extra={
    "correlation_id": correlation_id,
    "workflow_name": self.name,
    "step": "data_processing",
    "duration_ms": elapsed_time
})
```

**Health Check Debugging:**
```bash
# Create comprehensive health check endpoint
@app.get("/health/detailed")
def detailed_health():
    return {
        "status": "healthy",
        "database": check_database_connection(),
        "redis": check_redis_connection(),
        "external_apis": check_external_dependencies(),
        "workflows": check_workflow_health(),
        "timestamp": datetime.utcnow().isoformat()
    }
```

## 📞 Getting Additional Help

### Internal Resources

**Project-Specific:**
1. Check other apps' `mistakes/` folders for similar issues
2. Review project ADRs for architectural context
3. Consult with solutions architect for cross-app issues

**SDK-Related:**
1. Review `sdk-users/developer/07-troubleshooting.md`
2. Check `sdk-users/validation/common-mistakes.md`
3. Search `sdk-users/workflows/` for working examples

### External Resources

**Community Support:**
- Kailash SDK GitHub Issues
- Project team Slack/Discord channels
- Internal knowledge base

**Escalation Path:**
1. **App Issues**: App lead → Solutions architect
2. **Cross-App Issues**: Solutions architect → Project lead
3. **Infrastructure Issues**: DevOps engineer → Infrastructure team
4. **SDK Issues**: Project lead → Kailash team

### Documentation Improvements

**When You Solve an Issue:**
```bash
# 1. Document the solution
echo "## Issue: Description" >> mistakes/000-master.md
echo "**Cause**: What caused it" >> mistakes/000-master.md
echo "**Solution**: How to fix it" >> mistakes/000-master.md
echo "**Prevention**: How to avoid it" >> mistakes/000-master.md

# 2. Update troubleshooting guide if applicable
# Add common issues to this guide

# 3. Consider architectural improvements
# If systemic issue, create ADR for long-term fix
```

---

**This troubleshooting guide covers the most common issues you'll encounter in this client project template. When you solve new issues, please document them here to help the entire team.**