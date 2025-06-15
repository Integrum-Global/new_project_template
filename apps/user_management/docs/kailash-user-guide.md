# Kailash User Management Guide

**Complete guide for Kailash SDK developers building user management systems**

## 🎯 Introduction

This guide shows Kailash SDK developers how to leverage the User Management app as both a reference implementation and a foundation for building enterprise user management systems.

### What You'll Learn
- How to use Kailash SDK patterns for user management
- Enterprise-grade authentication and authorization
- Real-time workflow orchestration
- Performance optimization techniques
- Security best practices

## 🏗️ Architecture Overview

### Pure Kailash SDK Implementation
```python
# No custom orchestration - 100% SDK patterns
from kailash.middleware import AgentUIMiddleware, create_gateway
from kailash.runtime.local import LocalRuntime
from kailash.nodes.data import AsyncSQLDatabaseNode
from kailash.nodes.admin import UserManagementNode
from kailash.nodes.security import ABACPermissionEvaluatorNode
```

### Key Design Principles
1. **Workflow-First**: All business logic in workflows
2. **SDK-Native**: No custom orchestration code
3. **Async-by-Default**: All operations are non-blocking
4. **Enterprise-Ready**: SSO, MFA, ABAC, audit logging
5. **Performance-Optimized**: <100ms response times

## 🔧 Core SDK Components Used

### Runtime & Middleware
```python
# Unified runtime with enterprise features
runtime = LocalRuntime(
    enable_async=True,
    enable_cycles=True,
    enable_monitoring=True,
    enable_security=True,
    max_concurrency=10,
    user_context=user_context
)

# Agent UI for workflow orchestration
agent_ui = AgentUIMiddleware(
    max_sessions=1000,
    session_timeout_minutes=30,
    enable_persistence=True,
    enable_metrics=True
)
```

### Essential Nodes
```python
# User management operations
UserManagementNode(
    name="user_manager",
    operation="create_user",
    validation_rules=["email_unique", "password_strength"]
)

# Advanced permission checking
ABACPermissionEvaluatorNode(
    name="permission_checker",
    policy_engine="ai_enhanced",
    evaluation_timeout=15  # 15ms target
)

# Enterprise authentication
SSOAuthenticationNode(
    name="sso_auth",
    providers=["saml", "oauth2", "oidc"],
    mfa_required=True
)

# Async database operations
AsyncSQLDatabaseNode(
    name="db_operations",
    connection_string=settings.DATABASE_URL,
    pool_size=20
)
```

## 📋 Workflow Patterns

### 1. User Creation Workflow

```python
from kailash.workflow import WorkflowBuilder

def create_user_workflow():
    builder = WorkflowBuilder("user_creation_enterprise")
    
    # Step 1: Validate user data
    builder.add_node("PythonCodeNode", "validate_user_data", {
        "name": "data_validator",
        "code": """
# Comprehensive validation
valid = True
errors = []

# Email validation
import re
email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
if not user_data.get('email') or not re.match(email_pattern, user_data['email']):
    valid = False
    errors.append("Valid email is required")

# Name validation
if not user_data.get('first_name'):
    valid = False
    errors.append("First name is required")

# Department validation
valid_departments = ['Engineering', 'Sales', 'Marketing', 'HR', 'Finance']
if user_data.get('department') not in valid_departments:
    valid = False
    errors.append(f"Department must be one of: {', '.join(valid_departments)}")

result = {
    "result": {
        "valid": valid,
        "errors": errors,
        "user_data": user_data if valid else None
    }
}
"""
    })
    
    # Step 2: Check permissions
    builder.add_node("ABACPermissionEvaluatorNode", "check_permissions", {
        "name": "permission_evaluator",
        "resource": "users",
        "action": "create",
        "require_context": ["user_role", "department"]
    })
    
    # Step 3: Create user record
    builder.add_node("UserManagementNode", "create_user", {
        "name": "user_creator",
        "operation": "create",
        "auto_generate_id": True,
        "hash_password": True
    })
    
    # Step 4: Setup SSO
    builder.add_node("SSOAuthenticationNode", "setup_sso", {
        "name": "sso_configurator",
        "provider": "saml",
        "auto_provision": True
    })
    
    # Step 5: Setup MFA
    builder.add_node("MultiFactorAuthNode", "setup_mfa", {
        "name": "mfa_configurator",
        "methods": ["totp", "sms"],
        "require_backup_codes": True
    })
    
    # Step 6: Audit logging
    builder.add_node("AuditLogNode", "log_audit", {
        "name": "audit_logger",
        "event_type": "user_created",
        "severity": "INFO",
        "include_user_data": True
    })
    
    # Step 7: Send notification
    builder.add_node("PythonCodeNode", "send_notification", {
        "name": "notification_sender",
        "code": """
# Send welcome notification
notification_data = {
    "type": "user_created",
    "user_id": user_result.get("user_id"),
    "email": user_result.get("email"),
    "sso_enabled": sso_result.get("success", False),
    "mfa_enabled": mfa_result.get("success", False)
}

result = {"result": notification_data}
"""
    })
    
    # Connect workflow steps
    builder.add_connection("validate_user_data", "result", "check_permissions", "validation_result")
    builder.add_connection("check_permissions", "allowed", "create_user", "permission_granted")
    builder.add_connection("create_user", "user_result", "setup_sso", "user_data")
    builder.add_connection("create_user", "user_result", "setup_mfa", "user_data")
    builder.add_connection("setup_sso", "sso_result", "log_audit", "sso_data")
    builder.add_connection("setup_mfa", "mfa_result", "log_audit", "mfa_data")
    builder.add_connection("create_user", "user_result", "send_notification", "user_result")
    builder.add_connection("setup_sso", "sso_result", "send_notification", "sso_result")
    builder.add_connection("setup_mfa", "mfa_result", "send_notification", "mfa_result")
    
    return builder.build()
```

### 2. Authentication Workflow with Risk Assessment

```python
def create_authentication_workflow():
    builder = WorkflowBuilder("user_authentication_enterprise")
    
    # Step 1: Risk assessment
    builder.add_node("BehaviorAnalysisNode", "assess_risk", {
        "name": "risk_assessor",
        "factors": ["device_id", "ip_address", "location", "time_pattern"],
        "ml_model": "user_behavior_v2",
        "risk_threshold": 0.7
    })
    
    # Step 2: Threat detection
    builder.add_node("ThreatDetectionNode", "threat_detection", {
        "name": "threat_detector",
        "check_patterns": ["brute_force", "credential_stuffing", "anomalous_location"],
        "real_time_feeds": True
    })
    
    # Step 3: Authentication
    builder.add_node("EnterpriseAuthProviderNode", "authenticate", {
        "name": "authenticator",
        "providers": ["local", "sso", "ldap"],
        "fallback_order": ["sso", "ldap", "local"],
        "require_mfa_threshold": 0.5
    })
    
    # Step 4: Session management
    builder.add_node("SessionManagementNode", "create_session", {
        "name": "session_manager",
        "token_type": "jwt",
        "session_timeout": 3600,
        "refresh_token": True
    })
    
    # Step 5: Security event logging
    builder.add_node("SecurityEventNode", "log_event", {
        "name": "security_logger",
        "event_types": ["login_success", "login_failure", "high_risk_login"],
        "include_context": True
    })
    
    # Connect authentication flow
    builder.add_connection("assess_risk", "risk_score", "threat_detection", "risk_context")
    builder.add_connection("threat_detection", "threat_assessment", "authenticate", "security_context")
    builder.add_connection("authenticate", "auth_result", "create_session", "user_data")
    builder.add_connection("assess_risk", "risk_score", "log_event", "risk_data")
    builder.add_connection("authenticate", "auth_result", "log_event", "auth_data")
    
    return builder.build()
```

### 3. Permission Check Workflow

```python
def create_permission_check_workflow():
    builder = WorkflowBuilder("permission_check_enterprise")
    
    # Step 1: Get user context
    builder.add_node("PythonCodeNode", "get_user_context", {
        "name": "context_gatherer",
        "code": """
# Gather comprehensive user context
user_context = {
    "id": permission_data.get("user_id"),
    "roles": [],  # Will be populated from database
    "department": "",
    "clearance_level": 0,
    "location": permission_data.get("context", {}).get("location"),
    "time": permission_data.get("context", {}).get("time", "now")
}

result = {"result": {"user_context": user_context}}
"""
    })
    
    # Step 2: ABAC evaluation with AI
    builder.add_node("ABACPermissionEvaluatorNode", "evaluate_permission", {
        "name": "abac_evaluator",
        "policy_engine": "ai_enhanced",
        "include_reasoning": True,
        "evaluation_timeout": 15,  # 15ms target
        "cache_results": True
    })
    
    # Step 3: Format response
    builder.add_node("PythonCodeNode", "format_response", {
        "name": "response_formatter",
        "code": """
# Format standardized permission response
response = {
    "allowed": evaluation_result.get("allowed", False),
    "reason": evaluation_result.get("reason", ""),
    "applicable_policies": evaluation_result.get("policies_applied", []),
    "user_id": permission_data.get("user_id"),
    "resource": permission_data.get("resource"),
    "action": permission_data.get("action"),
    "timestamp": "2024-01-20T10:30:00Z",
    "evaluation_time_ms": evaluation_result.get("evaluation_time_ms", 0)
}

result = {"result": response}
"""
    })
    
    # Connect permission flow
    builder.add_connection("get_user_context", "result", "evaluate_permission", "user_context")
    builder.add_connection("evaluate_permission", "evaluation_result", "format_response", "evaluation_result")
    
    return builder.build()
```

## 🎛️ API Integration Patterns

### 1. REST API with Workflow Integration

```python
# apps/user_management/api/routes/users.py
from fastapi import APIRouter, HTTPException, Depends
from kailash.middleware import get_agent_ui

router = APIRouter()

@router.post("/users/")
async def create_user(
    user_data: UserCreateSchema,
    agent_ui: AgentUIMiddleware = Depends(get_agent_ui)
):
    """Create user with enterprise workflow."""
    
    # Create session for workflow execution
    session_id = await agent_ui.create_session("user_creation")
    
    try:
        # Execute user creation workflow
        execution_id = await agent_ui.execute_workflow_template(
            session_id,
            "user_creation_enterprise",
            inputs={"user_data": user_data.dict()}
        )
        
        # Wait for completion with timeout
        result = await agent_ui.wait_for_execution(
            session_id, 
            execution_id, 
            timeout=30
        )
        
        # Extract user data from workflow result
        user_result = result["outputs"]["create_user"]["user_result"]
        return UserResponseSchema(**user_result)
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
```

### 2. Real-time Updates with WebSocket

```python
# apps/user_management/api/routes/websocket.py
from fastapi import WebSocket, WebSocketDisconnect
from kailash.middleware import RealtimeMiddleware

class UserManagementWebSocket:
    def __init__(self):
        self.realtime = RealtimeMiddleware()
        self.connections = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.connections.append(websocket)
        
        # Subscribe to user events
        await self.realtime.subscribe("user_events", self.broadcast_event)
    
    async def broadcast_event(self, event_data):
        """Broadcast user events to all connected clients."""
        for connection in self.connections:
            try:
                await connection.send_json(event_data)
            except:
                self.connections.remove(connection)

@router.websocket("/ws/users")
async def websocket_endpoint(websocket: WebSocket):
    ws_manager = UserManagementWebSocket()
    await ws_manager.connect(websocket)
    
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
```

## 🔒 Security Implementation

### 1. Enterprise Authentication Stack

```python
# apps/user_management/core/security.py
from kailash.nodes.security import (
    SSOAuthenticationNode,
    MultiFactorAuthNode,
    BehaviorAnalysisNode,
    ThreatDetectionNode
)

class EnterpriseSecurityStack:
    def __init__(self):
        self.sso_providers = {
            "saml": SSOAuthenticationNode(provider="saml"),
            "oauth2": SSOAuthenticationNode(provider="oauth2"),
            "oidc": SSOAuthenticationNode(provider="oidc")
        }
        
        self.mfa = MultiFactorAuthNode(
            methods=["totp", "sms", "email", "hardware_token"]
        )
        
        self.behavior_analysis = BehaviorAnalysisNode(
            ml_model="enterprise_v3",
            risk_factors=["location", "device", "time", "behavior"]
        )
        
        self.threat_detection = ThreatDetectionNode(
            detection_rules=["brute_force", "credential_stuffing", "account_takeover"],
            real_time_feeds=True
        )
    
    async def authenticate_user(self, credentials, context):
        """Complete enterprise authentication flow."""
        
        # Risk assessment
        risk_score = await self.behavior_analysis.assess_risk(
            user_id=credentials.get("user_id"),
            context=context
        )
        
        # Threat detection
        threats = await self.threat_detection.check_threats(
            credentials=credentials,
            context=context
        )
        
        # Determine authentication method
        if risk_score > 0.7 or threats:
            # High risk - require strongest authentication
            auth_result = await self.sso_providers["saml"].authenticate(credentials)
            if auth_result.get("success"):
                mfa_result = await self.mfa.verify(
                    user_id=auth_result["user_id"],
                    methods=["totp", "hardware_token"]
                )
                return {"success": mfa_result.get("success"), "method": "sso_mfa"}
        else:
            # Standard authentication
            for provider in ["sso", "local"]:
                auth_result = await self.authenticate_with_provider(provider, credentials)
                if auth_result.get("success"):
                    return auth_result
        
        return {"success": False, "reason": "Authentication failed"}
```

### 2. ABAC Permission System

```python
# Advanced ABAC implementation
from kailash.nodes.security import ABACPermissionEvaluatorNode

class AdvancedABACSystem:
    def __init__(self):
        self.evaluator = ABACPermissionEvaluatorNode(
            policy_engine="ai_enhanced",
            operators=[
                "equals", "not_equals", "greater_than", "less_than",
                "in_list", "not_in_list", "contains", "regex_match",
                "before_date", "after_date", "time_between",
                "distance_within", "in_region"
            ]
        )
    
    async def check_permission(self, user_id, resource, action, context=None):
        """AI-enhanced permission checking."""
        
        permission_request = {
            "user_id": user_id,
            "resource": resource,
            "action": action,
            "context": context or {},
            "timestamp": datetime.now().isoformat()
        }
        
        result = await self.evaluator.evaluate(permission_request)
        
        return {
            "allowed": result.get("allowed", False),
            "reason": result.get("reason", ""),
            "ai_reasoning": result.get("ai_reasoning", ""),
            "policies_applied": result.get("policies_applied", []),
            "evaluation_time_ms": result.get("evaluation_time_ms", 0)
        }
    
    async def create_dynamic_policy(self, policy_data):
        """Create ABAC policy with AI assistance."""
        
        # AI-enhanced policy creation
        enhanced_policy = await self.evaluator.enhance_policy(policy_data)
        
        return {
            "policy_id": enhanced_policy.get("id"),
            "rules": enhanced_policy.get("rules"),
            "ai_recommendations": enhanced_policy.get("recommendations")
        }
```

## 📊 Performance Optimization

### 1. Database Layer Optimization

```python
# apps/user_management/core/repositories.py
from kailash.nodes.data import AsyncSQLDatabaseNode
from kailash.workflow import WorkflowBuilder

class OptimizedUserRepository:
    def __init__(self):
        self.runtime = LocalRuntime(enable_async=True)
    
    async def execute_query(self, query: str, params: dict = None) -> list:
        """Execute optimized database query."""
        
        workflow = WorkflowBuilder("query_workflow")
        workflow.add_node("AsyncSQLDatabaseNode", "db_query", {
            "name": "query_executor",
            "connection_string": settings.DATABASE_URL,
            "query": query,
            "parameters": params,
            "pool_size": 20,  # Connection pooling
            "query_timeout": 30,
            "enable_cache": True,
            "cache_ttl": 300  # 5 minute cache
        })
        
        built_workflow = workflow.build()
        results, _ = await self.runtime.execute(built_workflow, parameters={})
        
        return results["db_query"]["rows"]
    
    async def get_user_with_permissions(self, user_id: str):
        """Get user with all permissions in single optimized query."""
        
        query = """
        SELECT 
            u.*,
            array_agg(DISTINCT r.name) as roles,
            array_agg(DISTINCT p.name) as permissions
        FROM users u
        LEFT JOIN user_roles ur ON u.id = ur.user_id
        LEFT JOIN roles r ON ur.role_id = r.id
        LEFT JOIN role_permissions rp ON r.id = rp.role_id
        LEFT JOIN permissions p ON rp.permission_id = p.id
        WHERE u.id = $1
        GROUP BY u.id
        """
        
        result = await self.execute_query(query, {"user_id": user_id})
        return result[0] if result else None
```

### 2. Caching Strategy

```python
# apps/user_management/core/cache.py
from kailash.middleware import CacheMiddleware

class UserManagementCache:
    def __init__(self):
        self.cache = CacheMiddleware(
            backend="redis",
            default_ttl=3600
        )
        
        # Define cache layers
        self.cache_layers = {
            "user_profiles": {"ttl": 3600},  # 1 hour
            "permissions": {"ttl": 900},     # 15 minutes
            "sessions": {"ttl": 7200},       # 2 hours
            "abac_results": {"ttl": 300},    # 5 minutes
            "search_results": {"ttl": 180}   # 3 minutes
        }
    
    async def get_user_permissions(self, user_id: str):
        """Cached permission lookup."""
        
        cache_key = f"permissions:{user_id}"
        cached_result = await self.cache.get(cache_key)
        
        if cached_result:
            return cached_result
        
        # Fetch from database
        permissions = await self.fetch_user_permissions(user_id)
        
        # Cache with appropriate TTL
        await self.cache.set(
            cache_key, 
            permissions, 
            ttl=self.cache_layers["permissions"]["ttl"]
        )
        
        return permissions
    
    async def invalidate_user_cache(self, user_id: str):
        """Invalidate all cache entries for a user."""
        
        patterns = [
            f"user:{user_id}:*",
            f"permissions:{user_id}",
            f"sessions:{user_id}:*"
        ]
        
        for pattern in patterns:
            await self.cache.delete_pattern(pattern)
```

## 🔄 Real-time Features

### 1. Workflow Event Streaming

```python
# apps/user_management/core/events.py
from kailash.middleware import EventStreamMiddleware

class UserManagementEvents:
    def __init__(self):
        self.event_stream = EventStreamMiddleware()
        
        # Define event types
        self.event_types = {
            "user_created": {"priority": "normal", "retention": "7d"},
            "user_updated": {"priority": "normal", "retention": "7d"},
            "user_deleted": {"priority": "high", "retention": "30d"},
            "authentication_success": {"priority": "low", "retention": "1d"},
            "authentication_failure": {"priority": "high", "retention": "30d"},
            "permission_denied": {"priority": "high", "retention": "30d"},
            "security_threat": {"priority": "critical", "retention": "90d"}
        }
    
    async def emit_user_event(self, event_type: str, data: dict):
        """Emit user management event."""
        
        event = {
            "type": event_type,
            "data": data,
            "timestamp": datetime.now().isoformat(),
            "source": "user_management"
        }
        
        await self.event_stream.emit(event_type, event)
    
    async def subscribe_to_events(self, event_types: list, callback):
        """Subscribe to specific event types."""
        
        for event_type in event_types:
            await self.event_stream.subscribe(event_type, callback)
```

### 2. Real-time Dashboard Updates

```python
# Real-time dashboard with WebSocket
class UserManagementDashboard:
    def __init__(self):
        self.events = UserManagementEvents()
        self.metrics = {}
    
    async def start_monitoring(self):
        """Start real-time monitoring."""
        
        # Subscribe to all user events
        await self.events.subscribe_to_events(
            ["user_created", "user_updated", "authentication_success"],
            self.update_metrics
        )
    
    async def update_metrics(self, event):
        """Update dashboard metrics in real-time."""
        
        event_type = event.get("type")
        
        if event_type == "user_created":
            self.metrics["total_users"] = self.metrics.get("total_users", 0) + 1
        elif event_type == "authentication_success":
            self.metrics["active_sessions"] = self.metrics.get("active_sessions", 0) + 1
        
        # Broadcast updated metrics to WebSocket clients
        await self.broadcast_metrics()
    
    async def broadcast_metrics(self):
        """Broadcast metrics to connected dashboards."""
        
        metrics_event = {
            "type": "metrics_update",
            "data": self.metrics,
            "timestamp": datetime.now().isoformat()
        }
        
        await self.events.emit_user_event("dashboard_update", metrics_event)
```

## 🧪 Testing Patterns

### 1. Workflow Testing

```python
# tests/unit/test_workflows.py
import pytest
from kailash.runtime.local import LocalRuntime
from apps.user_management.workflows.registry import WorkflowRegistry

class TestUserWorkflows:
    @pytest.fixture
    async def test_runtime(self):
        return LocalRuntime(enable_async=True, debug=True)
    
    @pytest.mark.asyncio
    async def test_user_creation_workflow(self, test_runtime):
        """Test user creation workflow with valid data."""
        
        # Create workflow
        registry = WorkflowRegistry()
        workflow = await registry.get_workflow("user_creation_enterprise")
        
        # Test data
        user_data = {
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
            "department": "Engineering"
        }
        
        # Execute workflow
        results, run_id = await test_runtime.execute(
            workflow,
            parameters={"user_data": user_data}
        )
        
        # Verify results
        assert results["validate_user_data"]["result"]["valid"] is True
        assert results["create_user"]["user_result"]["email"] == user_data["email"]
        assert results["setup_sso"]["sso_result"]["success"] is True
```

### 2. API Testing

```python
# tests/integration/test_api_endpoints.py
import pytest
from httpx import AsyncClient
from apps.user_management.main import app

class TestUserAPI:
    @pytest.mark.asyncio
    async def test_create_user_endpoint(self):
        """Test user creation endpoint."""
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/users/",
                json={
                    "email": "test@example.com",
                    "first_name": "Test",
                    "last_name": "User"
                },
                headers={"Authorization": "Bearer test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["email"] == "test@example.com"
```

## 📚 Best Practices

### 1. Workflow Design
- Keep workflows focused on single business processes
- Use clear, descriptive node names
- Include comprehensive error handling
- Add audit logging to all critical operations

### 2. Performance Optimization
- Use AsyncSQLDatabaseNode for all database operations
- Implement intelligent caching strategies
- Monitor workflow execution times
- Optimize query patterns

### 3. Security Implementation
- Always use ABAC for permission checking
- Implement comprehensive audit logging
- Use enterprise authentication methods
- Monitor for security threats in real-time

### 4. Error Handling
- Implement graceful degradation
- Provide meaningful error messages
- Log all errors with context
- Use circuit breakers for external services

## 🚀 Production Deployment

### 1. Configuration Management

```python
# apps/user_management/config.py
from pydantic import BaseSettings

class Settings(BaseSettings):
    # Database
    database_url: str
    redis_url: str = "redis://localhost:6379"
    
    # Security
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expiration: int = 3600
    
    # Enterprise features
    enable_sso: bool = True
    enable_mfa: bool = True
    enable_audit_logging: bool = True
    
    # Performance
    max_concurrency: int = 10
    session_timeout_minutes: int = 30
    cache_ttl_seconds: int = 300
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
```

### 2. Monitoring & Observability

```python
# apps/user_management/core/monitoring.py
from kailash.middleware import MetricsMiddleware

class UserManagementMonitoring:
    def __init__(self):
        self.metrics = MetricsMiddleware(
            enable_prometheus=True,
            enable_custom_metrics=True
        )
        
        # Define custom metrics
        self.user_metrics = {
            "user_creation_time": "histogram",
            "authentication_success_rate": "gauge",
            "permission_check_time": "histogram",
            "active_sessions": "gauge"
        }
    
    async def track_user_operation(self, operation: str, duration: float):
        """Track user operation metrics."""
        
        await self.metrics.record_histogram(
            f"user_operation_{operation}_duration",
            duration,
            labels={"operation": operation}
        )
    
    async def get_health_status(self):
        """Get system health status."""
        
        return {
            "status": "healthy",
            "services": {
                "database": await self.check_database(),
                "redis": await self.check_redis(),
                "workflows": await self.check_workflows()
            },
            "metrics": await self.get_current_metrics()
        }
```

## 📞 Support & Community

### Getting Help
- **Documentation**: Complete guides and API reference
- **GitHub Issues**: Bug reports and feature requests
- **Discord**: Real-time community support
- **Stack Overflow**: Technical questions with `kailash-sdk` tag

### Contributing
- **Workflow Templates**: Share reusable workflow patterns
- **Security Enhancements**: Contribute security improvements
- **Performance Optimizations**: Submit performance improvements
- **Documentation**: Help improve guides and examples

---

**Ready to build enterprise user management with Kailash?** Start with our [Quick Start Guide](../README.md)