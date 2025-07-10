# Nexus Production Operations Runbook

## 🚨 Emergency Procedures

### Critical System Down
1. **Check Health Status**
   ```bash
   curl -f http://localhost:8000/health
   kubectl get pods -n nexus-production
   ```

2. **View Recent Logs**
   ```bash
   kubectl logs -n nexus-production deployment/nexus-app --tail=100
   ```

3. **Restart Services**
   ```bash
   kubectl rollout restart deployment/nexus-app -n nexus-production
   ```

4. **Escalation**
   - Slack: #nexus-alerts
   - PagerDuty: Nexus Production
   - On-call: +1-555-0123

### High Error Rate (>5%)
1. **Check Metrics Dashboard**
   - Grafana: http://monitoring.company.com/d/nexus-overview
   - Look for error rate spike patterns

2. **Investigate Root Cause**
   ```bash
   # Check error logs
   kubectl logs -n nexus-production deployment/nexus-app | grep ERROR

   # Check database connectivity
   kubectl exec -n nexus-production deployment/nexus-app -- python -c "
   from nexus import create_application
   app = create_application()
   print(app.health_check())
   "
   ```

3. **Immediate Actions**
   - Scale up if resource constrained
   - Restart if memory leak suspected
   - Rollback if recent deployment caused issue

### Database Connection Issues
1. **Check Database Status**
   ```bash
   kubectl get pods -n nexus-production -l app=postgresql
   kubectl exec -n nexus-production postgres-0 -- pg_isready
   ```

2. **Connection Pool Status**
   ```bash
   # Check pool metrics in Grafana
   # Prometheus query: nexus_database_connections_active
   ```

3. **Recovery Actions**
   ```bash
   # Restart connection pool
   kubectl rollout restart deployment/nexus-app -n nexus-production

   # Scale database if needed
   kubectl scale statefulset postgres -n nexus-production --replicas=3
   ```

## 📊 Monitoring & Alerting

### Key Metrics to Monitor

#### Application Metrics
- **Response Time**: p95 < 200ms, p99 < 500ms
- **Error Rate**: < 1% for critical endpoints
- **Throughput**: requests per second by channel
- **Active Sessions**: concurrent user sessions

#### Infrastructure Metrics
- **CPU Usage**: < 80% average
- **Memory Usage**: < 85% of allocated
- **Database Connections**: < 80% of pool size
- **Disk Usage**: < 85% of available space

#### Business Metrics
- **Workflow Executions**: successful vs failed
- **Channel Usage**: API vs CLI vs MCP distribution
- **Tenant Activity**: operations per tenant
- **Marketplace Activity**: searches, installs, publications

### Alert Configuration

#### Critical Alerts (PagerDuty)
```yaml
# prometheus/alerts/critical.yml
groups:
  - name: nexus.critical
    rules:
      - alert: NexusDown
        expr: up{job="nexus-app"} == 0
        for: 30s
        labels:
          severity: critical
        annotations:
          summary: "Nexus application is down"

      - alert: HighErrorRate
        expr: rate(nexus_errors_total[5m]) > 0.05
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"

      - alert: DatabaseDown
        expr: nexus_database_connections_active == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Database connection lost"
```

#### Warning Alerts (Slack)
```yaml
  - name: nexus.warning
    rules:
      - alert: HighResponseTime
        expr: histogram_quantile(0.95, nexus_channel_request_duration_seconds_bucket) > 0.2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High response time detected"

      - alert: HighMemoryUsage
        expr: nexus_memory_usage_bytes / (1024^3) > 0.8
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage"
```

### Dashboard Configuration

#### Executive Dashboard
- Overall system health status
- Key business metrics (workflows executed, active users)
- Error rate trends
- Performance summary

#### Operations Dashboard
- Infrastructure health (CPU, memory, disk)
- Application metrics (response times, throughput)
- Database performance
- Recent alerts and incidents

#### Developer Dashboard
- Code deployment status
- Error details and stack traces
- Performance profiling data
- API usage analytics

## 🔄 Deployment Procedures

### Standard Deployment
1. **Pre-deployment Checks**
   ```bash
   # Verify staging environment
   ./scripts/validate-staging.sh

   # Run security scan
   python scripts/security/scan.py --fail-on-high

   # Run performance tests
   python scripts/performance/load_test.py --duration 300
   ```

2. **Blue-Green Deployment**
   ```bash
   # Deploy to green environment
   kubectl apply -f deployment/k8s/green/ -n nexus-production

   # Wait for health check
   kubectl wait --for=condition=ready pod -l app=nexus,version=green -n nexus-production

   # Run smoke tests
   ./scripts/smoke-test.sh http://nexus-green.nexus-production.svc.cluster.local:8000

   # Switch traffic
   kubectl patch service nexus-app -n nexus-production -p '{"spec":{"selector":{"version":"green"}}}'

   # Monitor for 5 minutes
   sleep 300

   # Scale down blue if successful
   kubectl scale deployment nexus-app-blue -n nexus-production --replicas=0
   ```

3. **Rollback Procedure**
   ```bash
   # Switch back to blue
   kubectl patch service nexus-app -n nexus-production -p '{"spec":{"selector":{"version":"blue"}}}'

   # Scale up blue environment
   kubectl scale deployment nexus-app-blue -n nexus-production --replicas=3

   # Verify rollback
   curl -f http://nexus-app.nexus-production.svc.cluster.local:8000/health
   ```

### Emergency Hotfix Deployment
1. **Fast-track Process**
   ```bash
   # Skip staging, deploy directly with monitoring
   kubectl set image deployment/nexus-app nexus=nexus:hotfix-v1.2.3 -n nexus-production

   # Monitor deployment
   kubectl rollout status deployment/nexus-app -n nexus-production

   # Validate immediately
   ./scripts/smoke-test.sh http://nexus-app.nexus-production.svc.cluster.local:8000
   ```

## 📈 Scaling Procedures

### Horizontal Scaling
```bash
# Scale application pods
kubectl scale deployment nexus-app -n nexus-production --replicas=6

# Scale database (if using cloud provider)
# AWS RDS example:
aws rds modify-db-cluster --db-cluster-identifier nexus-prod --scaling-configuration \
  MinCapacity=2,MaxCapacity=8,AutoPause=false

# Scale Redis cache
kubectl scale statefulset redis-cluster -n nexus-production --replicas=6
```

### Vertical Scaling
```yaml
# deployment/k8s/nexus-app.yaml
resources:
  requests:
    memory: "1Gi"      # Increased from 512Mi
    cpu: "1000m"       # Increased from 500m
  limits:
    memory: "2Gi"      # Increased from 1Gi
    cpu: "2000m"       # Increased from 1000m
```

### Auto-scaling Configuration
```yaml
# deployment/k8s/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: nexus-app-hpa
  namespace: nexus-production
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: nexus-app
  minReplicas: 3
  maxReplicas: 20
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
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 100
        periodSeconds: 15
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60
```

## 🔧 Maintenance Procedures

### Database Maintenance
1. **Backup Verification**
   ```bash
   # Check backup status
   kubectl get cronjobs -n nexus-production

   # Verify latest backup
   aws s3 ls s3://nexus-backups/database/ --recursive | tail -5

   # Test restore (in staging)
   ./scripts/test-restore.sh s3://nexus-backups/database/nexus-backup-20241210-120000.sql
   ```

2. **Index Optimization**
   ```sql
   -- Run during low-traffic hours
   VACUUM ANALYZE;
   REINDEX DATABASE nexus_production;

   -- Check for unused indexes
   SELECT schemaname, tablename, attname, n_distinct, most_common_vals
   FROM pg_stats
   WHERE schemaname = 'public'
   ORDER BY n_distinct DESC;
   ```

3. **Connection Pool Tuning**
   ```bash
   # Monitor connection patterns
   kubectl exec -n nexus-production postgres-0 -- psql -c "
   SELECT state, count(*)
   FROM pg_stat_activity
   WHERE datname = 'nexus_production'
   GROUP BY state;
   "

   # Adjust pool size in config
   kubectl patch configmap nexus-config -n nexus-production --patch='
   data:
     database.pool_size: "20"
     database.max_overflow: "30"
   '
   ```

### Log Management
1. **Log Rotation**
   ```bash
   # Configure log retention
   kubectl patch configmap fluent-bit-config -n logging --patch='
   data:
     fluent-bit.conf: |
       [SERVICE]
           Log_Level    info
           Daemon       off
           HTTP_Server  On
           HTTP_Listen  0.0.0.0
           HTTP_Port    2020
           storage.path /var/log/flb-storage/
           storage.max_chunks_up 128
   '
   ```

2. **Log Analysis**
   ```bash
   # Top error patterns
   kubectl logs -n nexus-production deployment/nexus-app --since=1h | \
     grep ERROR | \
     cut -d' ' -f4- | \
     sort | uniq -c | sort -nr | head -10

   # Performance bottlenecks
   kubectl logs -n nexus-production deployment/nexus-app --since=1h | \
     grep "response_time" | \
     awk '{print $NF}' | \
     sort -n | tail -20
   ```

### Certificate Management
1. **Certificate Renewal**
   ```bash
   # Check certificate expiry
   kubectl get certificates -n nexus-production

   # Force renewal if needed
   kubectl delete certificaterequest --all -n nexus-production
   kubectl annotate certificate nexus-tls cert-manager.io/issue-temporary-certificate- -n nexus-production
   ```

2. **TLS Configuration Update**
   ```yaml
   # deployment/k8s/ingress.yaml
   metadata:
     annotations:
       cert-manager.io/cluster-issuer: "letsencrypt-prod"
       nginx.ingress.kubernetes.io/ssl-protocols: "TLSv1.2 TLSv1.3"
       nginx.ingress.kubernetes.io/ssl-ciphers: "ECDHE-ECDSA-AES128-GCM-SHA256,ECDHE-RSA-AES128-GCM-SHA256"
   ```

## 🎯 Performance Optimization

### Application Tuning
1. **Connection Pool Optimization**
   ```python
   # config.py adjustments
   database_config = DatabaseConfig(
       pool_size=20,           # Increased from 10
       max_overflow=30,        # Increased from 20
       pool_timeout=30,        # Connection timeout
       pool_recycle=3600,      # Recycle connections hourly
       pool_pre_ping=True      # Validate connections
   )
   ```

2. **Caching Strategy**
   ```python
   # Enable Redis caching
   cache_config = CacheConfig(
       enabled=True,
       redis_url="redis://redis-cluster:6379/0",
       default_ttl=300,        # 5 minutes
       session_ttl=1800,       # 30 minutes
       workflow_cache_ttl=60   # 1 minute
   )
   ```

3. **Async Optimization**
   ```python
   # Increase async worker pool
   worker_config = WorkerConfig(
       max_workers=50,         # Increased from 20
       worker_timeout=30,      # Task timeout
       queue_size=1000,        # Task queue size
       batch_size=10          # Batch processing
   )
   ```

### Database Optimization
1. **Query Performance**
   ```sql
   -- Enable slow query logging
   ALTER SYSTEM SET log_min_duration_statement = 1000;  -- Log queries > 1s
   ALTER SYSTEM SET log_statement = 'all';
   SELECT pg_reload_conf();

   -- Analyze query patterns
   SELECT query, calls, total_time, mean_time, rows
   FROM pg_stat_statements
   ORDER BY total_time DESC
   LIMIT 10;
   ```

2. **Index Management**
   ```sql
   -- Create performance indexes
   CREATE INDEX CONCURRENTLY idx_workflows_status_created
   ON workflows(status, created_at)
   WHERE status IN ('running', 'pending');

   CREATE INDEX CONCURRENTLY idx_sessions_tenant_active
   ON sessions(tenant_id, is_active, last_activity)
   WHERE is_active = true;
   ```

### Infrastructure Optimization
1. **Resource Allocation**
   ```yaml
   # deployment/k8s/nexus-app.yaml
   resources:
     requests:
       memory: "1Gi"
       cpu: "1000m"
     limits:
       memory: "2Gi"
       cpu: "2000m"

   # Add resource quotas
   resourceQuota:
     hard:
       requests.cpu: "10"
       requests.memory: "20Gi"
       limits.cpu: "20"
       limits.memory: "40Gi"
   ```

2. **Network Optimization**
   ```yaml
   # Service mesh configuration
   apiVersion: networking.istio.io/v1beta1
   kind: DestinationRule
   metadata:
     name: nexus-app
   spec:
     host: nexus-app
     trafficPolicy:
       connectionPool:
         tcp:
           maxConnections: 100
         http:
           http1MaxPendingRequests: 50
           maxRequestsPerConnection: 10
   ```

## 📞 Contact Information

### On-Call Rotation
- **Primary**: DevOps Team (+1-555-0123)
- **Secondary**: Platform Team (+1-555-0124)
- **Escalation**: Engineering Manager (+1-555-0125)

### Communication Channels
- **Slack**: #nexus-alerts (critical), #nexus-ops (general)
- **Email**: nexus-ops@company.com
- **PagerDuty**: Nexus Production Service

### Vendor Contacts
- **Cloud Provider**: AWS Support (Enterprise)
- **Monitoring**: Datadog Support
- **Database**: PostgreSQL Professional Services

---

**Last Updated**: 2024-12-10
**Next Review**: 2024-12-24
**Document Owner**: Platform Engineering Team
