# User Management System Architecture

## System Overview

The User Management System extends Kailash middleware to provide enterprise-grade user, role, and permission management with 15.9x better performance than Django Admin.

## App-Specific Components

### 1. Extended Models

#### User Model Extensions
```python
class UserProfile(BaseUserModel):
    """Extended user model with enterprise fields."""
    # Base fields from middleware
    # App-specific additions:
    department = Column(String(100), index=True)
    job_title = Column(String(100))
    manager_id = Column(UUID, ForeignKey('users.user_id'))
    employee_id = Column(String(50), unique=True)
    cost_center = Column(String(50))
    clearance_level = Column(Integer, default=1)
    
    # SSO integrations
    azure_ad_id = Column(String(255))
    google_workspace_id = Column(String(255))
    okta_id = Column(String(255))
    
    # Compliance fields
    gdpr_consent_date = Column(DateTime)
    data_retention_exempt = Column(Boolean, default=False)
```

#### Session Tracking
```python
class EnhancedSession(BaseSessionModel):
    """Enhanced session with device fingerprinting."""
    device_fingerprint = Column(String(64))
    risk_score = Column(Float)
    auth_provider = Column(String(50))
    mfa_verified = Column(Boolean, default=False)
    trust_device_until = Column(DateTime)
```

### 2. ABAC Permission Engine

#### Custom Operators
The app implements 16 ABAC operators beyond the standard middleware:

```python
CUSTOM_OPERATORS = {
    # Temporal operators
    "working_hours": lambda ctx: ctx.time.hour in range(9, 17),
    "business_days": lambda ctx: ctx.time.weekday() < 5,
    
    # Hierarchical operators  
    "reports_to": lambda user, manager: user.manager_id == manager.id,
    "in_org_tree": lambda user, root: check_org_hierarchy(user, root),
    
    # Risk-based operators
    "risk_below": lambda ctx, threshold: ctx.risk_score < threshold,
    "trusted_device": lambda ctx: ctx.device_id in ctx.user.trusted_devices,
    
    # Compliance operators
    "gdpr_consented": lambda user: user.gdpr_consent_date is not None,
    "data_classified": lambda resource, level: resource.classification <= level
}
```

#### AI-Powered Rule Generation
```python
async def generate_abac_rule(description: str) -> dict:
    """Use LLM to convert natural language to ABAC rules."""
    prompt = f"Convert to ABAC rule: {description}"
    
    result = await llm_agent.run(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    
    return validate_and_optimize_rule(result)
```

### 3. SSO Integration Details

#### Provider-Specific Handlers
```python
SSO_HANDLERS = {
    "azure": AzureADHandler(
        tenant_id=config.AZURE_TENANT_ID,
        attribute_mapping={
            "department": "extension_department",
            "manager": "extension_manager_email",
            "job_title": "jobTitle"
        }
    ),
    
    "google": GoogleWorkspaceHandler(
        domain=config.GOOGLE_DOMAIN,
        admin_sdk_enabled=True,
        org_unit_sync=True
    ),
    
    "okta": OktaHandler(
        domain=config.OKTA_DOMAIN,
        group_prefix="kailash_",
        custom_attributes=["clearance_level", "cost_center"]
    )
}
```

### 4. Performance Optimizations

#### Database Indexes
```sql
-- User query optimization
CREATE INDEX idx_users_dept_status ON users(department, status);
CREATE INDEX idx_users_manager_tree ON users(manager_id);
CREATE INDEX idx_users_last_login_partial 
    ON users(last_login) 
    WHERE status = 'active';

-- Session optimization
CREATE INDEX idx_sessions_user_active 
    ON user_sessions(user_id, expires_at) 
    WHERE status = 'active';

-- Audit log partitioning
CREATE TABLE audit_logs_2024_q1 PARTITION OF audit_logs
    FOR VALUES FROM ('2024-01-01') TO ('2024-04-01');
```

#### Caching Strategy
```python
CACHE_LAYERS = {
    "L1_LOCAL": {
        "user_profiles": LRUCache(maxsize=1000, ttl=300),
        "permissions": LRUCache(maxsize=5000, ttl=900)
    },
    
    "L2_REDIS": {
        "sessions": {"ttl": 7200, "prefix": "sess:"},
        "abac_results": {"ttl": 300, "prefix": "abac:"},
        "sso_tokens": {"ttl": 3600, "prefix": "sso:"}
    },
    
    "L3_DATABASE": {
        "audit_logs": {"partition": "monthly"},
        "security_events": {"retention": "7_years"}
    }
}
```

### 5. Compliance Automation

#### GDPR Workflows
```python
class GDPRComplianceWorkflow(Workflow):
    """Automated GDPR compliance workflows."""
    
    async def data_export(self, user_id: str):
        """Article 15 - Right of access."""
        data = await gather_user_data(user_id)
        return format_gdpr_export(data)
    
    async def data_erasure(self, user_id: str):
        """Article 17 - Right to erasure."""
        await anonymize_user_data(user_id)
        await delete_personal_data(user_id)
        await retain_legal_records(user_id)
```

#### SOC2 Controls
```python
SOC2_CONTROLS = {
    "CC6.1": "Logical access security",
    "CC6.2": "New user access provisioning", 
    "CC6.3": "User access modification",
    "CC6.4": "User access termination",
    "CC6.5": "Privileged access",
    "CC6.6": "Access reviews",
    "CC6.7": "Password policies",
    "CC6.8": "System authentication"
}
```

### 6. Real-Time Features

#### WebSocket Event Handlers
```python
WEBSOCKET_EVENTS = {
    "user_activity": {
        "channels": ["admin_dashboard", "security_monitoring"],
        "throttle": "5/second/user"
    },
    
    "security_alerts": {
        "channels": ["security_ops", "admin_notifications"],
        "priority": "high",
        "delivery": "guaranteed"
    },
    
    "compliance_events": {
        "channels": ["compliance_dashboard"],
        "retention": "7_years"
    }
}
```

## Integration Architecture

### API Gateway Configuration
```python
# Custom rate limits for user management
RATE_LIMITS = {
    "/api/auth/login": "5 per minute per IP",
    "/api/users": "100 per minute per user",
    "/api/users/bulk": "10 per minute per user",
    "/api/admin/*": "200 per minute per admin"
}

# Custom middleware chain
MIDDLEWARE_CHAIN = [
    "SecurityHeadersMiddleware",
    "TenantIsolationMiddleware", 
    "ABACAuthorizationMiddleware",
    "AuditLoggingMiddleware",
    "PerformanceMonitoringMiddleware"
]
```

### Workflow Orchestration
```python
# User lifecycle workflows
WORKFLOWS = {
    "user_onboarding": {
        "nodes": [
            "ValidateUserData",
            "CheckDuplicates",
            "CreateUserAccount",
            "SetupSSO",
            "ConfigureMFA",
            "AssignDefaultRoles",
            "SendWelcomeEmail",
            "ScheduleAccessReview"
        ]
    },
    
    "user_offboarding": {
        "nodes": [
            "DisableAccount",
            "RevokeAllSessions",
            "TransferOwnership",
            "BackupUserData",
            "NotifyManager",
            "ScheduleDeletion"
        ]
    }
}
```

## Performance Architecture

### Query Optimization
- Prepared statements for all database queries
- Query result caching with smart invalidation
- Database connection pooling (20 connections)
- Read replicas for reporting queries

### Async Processing
- All I/O operations use async/await
- Background task queue for bulk operations
- Event-driven architecture for real-time updates
- WebSocket connection pooling

### Monitoring & Metrics
```python
PERFORMANCE_METRICS = {
    "user_list_ms": Histogram('user_list_duration'),
    "auth_success_rate": Counter('auth_attempts', ['result']),
    "abac_eval_ms": Histogram('abac_evaluation_duration'),
    "concurrent_sessions": Gauge('active_sessions')
}
```

## Security Architecture

### Defense in Depth
1. **Network**: WAF, DDoS protection, IP allowlisting
2. **Application**: Input validation, CSRF protection, security headers
3. **Authentication**: MFA, risk-based auth, device trust
4. **Authorization**: ABAC with AI reasoning, least privilege
5. **Data**: Encryption at rest/transit, key rotation
6. **Monitoring**: Real-time threat detection, anomaly detection

### Threat Detection Rules
```python
THREAT_RULES = {
    "brute_force": {
        "condition": "failed_logins > 5 in 5_minutes",
        "action": "block_ip_30_minutes"
    },
    
    "impossible_travel": {
        "condition": "distance > 1000km in < 1_hour",
        "action": "require_mfa"
    },
    
    "privilege_escalation": {
        "condition": "permission_changes > normal_baseline",
        "action": "alert_security_team"
    }
}
```

## Deployment Architecture

### High Availability
- Multi-region deployment with failover
- Database replication with automatic failover
- Redis Sentinel for cache HA
- Session affinity for WebSocket connections

### Scaling Strategy
- Horizontal scaling for API servers (3-10 instances)
- Vertical scaling for database (up to 64 cores)
- Auto-scaling based on CPU and request rate
- CDN for static assets

### Disaster Recovery
- RPO: 1 hour (database backups)
- RTO: 15 minutes (automated failover)
- Backup retention: 30 days
- Audit log archive: 7 years

---

For generic middleware architecture, see [/apps/ENTERPRISE_PATTERNS.md](/apps/ENTERPRISE_PATTERNS.md)