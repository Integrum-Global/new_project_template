"""
Application startup and initialization
"""

from kailash.middleware import (
    AgentUIMiddleware,
    RealtimeMiddleware,
    AIChatMiddleware,
    MiddlewareAuthManager,
    MiddlewareAccessControlManager
)
from kailash.nodes.auth import EnterpriseAuthProviderNode
from kailash.nodes.data import AsyncSQLDatabaseNode
from kailash.runtime.local import LocalRuntime

from apps.user_management.config import settings
from apps.user_management.workflows.registry import WorkflowRegistry


# Global instances
agent_ui = None
realtime = None
ai_chat = None
auth_manager = None
access_control = None
enterprise_auth = None
db_node = None
runtime = None
workflow_registry = None


async def initialize_application():
    """Initialize all application components."""
    global agent_ui, realtime, ai_chat, auth_manager, access_control
    global enterprise_auth, db_node, runtime, workflow_registry
    
    print("📡 Initializing application components...")
    
    # 1. Setup Agent-UI Middleware
    agent_ui = AgentUIMiddleware(
        max_sessions=settings.MAX_SESSIONS,
        session_timeout_minutes=settings.SESSION_TIMEOUT_MINUTES,
        enable_persistence=True,
        enable_metrics=settings.ENABLE_METRICS,
        enable_audit_logging=settings.ENABLE_AUDIT_LOGGING
    )
    
    # 2. Setup Enterprise Authentication
    enterprise_auth = EnterpriseAuthProviderNode(
        name="user_mgmt_auth",
        enabled_methods=["sso", "directory", "mfa", "passwordless", "social", "api_key", "jwt"],
        primary_method="sso",
        fallback_methods=["directory", "mfa"],
        sso_config={
            "providers": settings.SSO_PROVIDERS,
            "saml_settings": {
                "entity_id": settings.SAML_ENTITY_ID,
                "sso_url": settings.SAML_SSO_URL
            }
        },
        directory_config={
            "directory_type": "ldap",
            "connection_config": {
                "server": settings.LDAP_SERVER,
                "base_dn": settings.LDAP_BASE_DN
            },
            "auto_provisioning": settings.LDAP_AUTO_PROVISIONING
        },
        risk_assessment_enabled=settings.ENABLE_RISK_ASSESSMENT,
        adaptive_auth_enabled=settings.ENABLE_ADAPTIVE_AUTH,
        fraud_detection_enabled=settings.ENABLE_FRAUD_DETECTION,
        compliance_mode=settings.COMPLIANCE_MODE
    )
    
    # 3. Setup Access Control
    access_control = MiddlewareAccessControlManager(
        strategy="hybrid",  # RBAC + ABAC
        enable_caching=settings.ENABLE_CACHING,
        cache_ttl=settings.CACHE_TTL,
        audit_enabled=settings.ENABLE_AUDIT_LOGGING
    )
    
    # 4. Setup Database Node
    db_node = AsyncSQLDatabaseNode(
        name="user_mgmt_db",
        connection_string=settings.DATABASE_URL,
        pool_size=settings.DATABASE_POOL_SIZE,
        max_overflow=settings.DATABASE_MAX_OVERFLOW,
        echo=False
    )
    
    # 5. Setup Runtime
    runtime = LocalRuntime(
        debug=False,
        enable_async=True,
        enable_monitoring=settings.ENABLE_METRICS,
        enable_security=True,
        enable_audit=settings.ENABLE_AUDIT_LOGGING
    )
    
    # 6. Setup Real-time Middleware
    realtime = RealtimeMiddleware(agent_ui)
    
    # 7. Setup AI Chat
    ai_chat = AIChatMiddleware(
        agent_ui,
        enable_vector_search=True,
        vector_database_url=settings.DATABASE_URL
    )
    
    # 8. Setup Workflow Registry
    workflow_registry = WorkflowRegistry(agent_ui)
    await workflow_registry.register_all_workflows()
    
    print("✅ All components initialized successfully!")