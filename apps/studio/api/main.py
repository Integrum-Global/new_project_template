"""
Enterprise Studio API - SDK Gateway Integration

Uses the Kailash SDK's complete middleware stack and FastAPI app instead of manual orchestration:
- create_gateway() provides complete enterprise FastAPI application
- Built-in session management, real-time communication, and authentication
- Embedded SQLAlchemy with middleware repositories
- Pre-built endpoints for workflows, executions, and system management
- Enterprise security, monitoring, and compliance features
- No manual FastAPI orchestration - use SDK's complete app
"""

import logging
from typing import Any, Dict, Optional

# Import SDK gateway - provides complete FastAPI app
try:
    from kailash.middleware import create_gateway

    SDK_GATEWAY_AVAILABLE = True
except ImportError:
    SDK_GATEWAY_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.error("SDK gateway not available - cannot proceed without core middleware")

from ..core.config import StudioConfig, get_config
from ..core.security import SecurityService

logger = logging.getLogger(__name__)

# Global configuration
config: StudioConfig = get_config()

# Global services
security_service: SecurityService = None
gateway: Optional[Any] = None


def create_studio_gateway():
    """Create enterprise Studio API using SDK's complete gateway instead of manual FastAPI orchestration."""
    global security_service, gateway

    if not SDK_GATEWAY_AVAILABLE:
        raise RuntimeError(
            "SDK gateway not available - cannot create Studio API without core middleware"
        )

    logger.info("🚀 Creating Enterprise Kailash Studio API using SDK Gateway")
    logger.info(f"📊 Environment: {config.environment.value}")
    logger.info(f"🔒 Security Level: {config.security.level.value}")

    # Initialize security service for additional enterprise features
    security_service = SecurityService()

    # Create complete enterprise gateway with supported features
    # The APIGateway only accepts specific parameters
    gateway = create_gateway(
        title="Enterprise Kailash Studio API",
        description="Advanced enterprise API for Kailash Workflow Studio with comprehensive middleware stack",
        version="2.0.0",
        cors_origins=config.cors_origins,
        enable_docs=config.enable_api_docs,
        enable_auth=config.enable_auth,
        database_url=(
            config.get_database_url() if config.sdk.use_database_nodes else None
        ),
        max_sessions=config.middleware.max_concurrent_sessions,
    )

    # Store additional configuration on the gateway for use by routes
    gateway.studio_config = {
        "ai_config": (
            {
                "default_provider": config.ai.default_provider,
                "default_model": config.ai.default_model,
                "enable_streaming": config.ai.enable_streaming,
                "enable_function_calling": config.ai.enable_function_calling,
                "max_tokens": config.ai.max_tokens,
                "temperature": config.ai.temperature,
                "top_p": config.ai.top_p,
                "frequency_penalty": config.ai.frequency_penalty,
                "presence_penalty": config.ai.presence_penalty,
            }
            if config.ai.enable_ai_chat
            else None
        ),
        "security_config": {
            "level": config.security.level.value,
            "jwt_secret_key": config.security.jwt_secret_key,
            "jwt_algorithm": config.security.jwt_algorithm,
            "jwt_expire_minutes": config.security.jwt_expire_minutes,
            "api_key_enabled": config.security.api_key_enabled,
            "api_key_header": config.security.api_key_header,
            "session_timeout_minutes": config.security.session_timeout_minutes,
            "max_login_attempts": config.security.max_login_attempts,
            "lockout_duration_minutes": config.security.lockout_duration_minutes,
            "mfa_enabled": config.security.mfa_enabled,
            "enable_audit_logging": config.security.enable_audit_logging,
            "enable_threat_detection": config.security.enable_threat_detection,
            "enable_behavior_analysis": config.security.enable_behavior_analysis,
            "compliance_frameworks": config.security.compliance_frameworks,
            "data_retention_days": config.security.data_retention_days,
        },
        "execution_config": {
            "max_concurrent_executions": config.execution.max_concurrent_executions,
            "max_concurrent_per_tenant": config.execution.max_concurrent_per_tenant,
            "default_timeout_seconds": config.execution.default_timeout_seconds,
            "max_timeout_seconds": config.execution.max_timeout_seconds,
            "cleanup_interval_minutes": config.execution.cleanup_interval_minutes,
            "retain_completed_days": config.execution.retain_completed_days,
            "retain_failed_days": config.execution.retain_failed_days,
            "enable_resource_monitoring": config.execution.enable_resource_monitoring,
            "max_memory_mb": config.execution.max_memory_mb,
            "max_cpu_percent": config.execution.max_cpu_percent,
            "enable_auto_scaling": config.execution.enable_auto_scaling,
            "enable_execution_queue": config.execution.enable_execution_queue,
            "queue_max_size": config.execution.queue_max_size,
            "priority_levels": config.execution.priority_levels,
        },
        "monitoring_config": {
            "enabled": config.monitoring.enabled,
            "metrics_enabled": config.monitoring.metrics_enabled,
            "health_check_enabled": config.monitoring.health_check_enabled,
            "performance_monitoring_enabled": config.monitoring.performance_monitoring_enabled,
            "log_level": config.monitoring.log_level.value,
            "log_format": config.monitoring.log_format,
            "enable_structured_logging": config.monitoring.enable_structured_logging,
            "enable_request_logging": config.monitoring.enable_request_logging,
            "enable_error_tracking": config.monitoring.enable_error_tracking,
            "enable_performance_profiling": config.monitoring.enable_performance_profiling,
            "metrics_port": config.monitoring.metrics_port,
            "health_check_path": config.monitoring.health_check_path,
            "metrics_path": config.monitoring.metrics_path,
            "prometheus_enabled": config.monitoring.prometheus_enabled,
            "error_threshold_rate": config.monitoring.error_threshold_rate,
            "response_time_threshold_ms": config.monitoring.response_time_threshold_ms,
        },
        "middleware_config": {
            "realtime_enabled": config.middleware.realtime_enabled,
            "websocket_heartbeat_interval": config.middleware.websocket_heartbeat_interval,
            "sse_retry_timeout": config.middleware.sse_retry_timeout,
        },
    }

    logger.info("✅ SDK Gateway created with complete enterprise middleware stack")
    logger.info(f"🏢 Components available: {list(gateway.__dict__.keys())}")

    # Add custom Studio-specific endpoints to the SDK's FastAPI app if needed
    _add_studio_custom_endpoints(gateway)

    # Store references for external access
    gateway.security_service = security_service
    gateway.config = config

    logger.info("🎉 Enterprise Kailash Studio API ready")

    return gateway


def _add_studio_custom_endpoints(gateway):
    """Add Studio-specific custom endpoints to the SDK's FastAPI app."""

    # The SDK gateway already provides:
    # - /health - Health checks
    # - /api/sessions - Session management
    # - /api/workflows - Workflow creation and management
    # - /api/executions - Execution tracking and control
    # - /api/schemas/nodes - Node discovery and schemas
    # - /ws - WebSocket real-time communication
    # - /events - Server-Sent Events
    # - /api/stats - System statistics
    # - /api/webhooks - Webhook management

    # Import and add PRD-compliant routes
    from .routes import add_studio_routes

    add_studio_routes(gateway)

    # Add Studio-specific information endpoint
    @gateway.app.get("/api/studio/info", tags=["Studio"])
    async def studio_info():
        """Get Studio-specific information and capabilities."""
        return {
            "name": "Enterprise Kailash Studio API",
            "version": "2.0.0",
            "environment": config.environment.value,
            "studio_features": {
                "visual_workflow_builder": True,
                "real_time_execution": True,
                "ai_powered_generation": config.ai.enable_ai_chat,
                "enterprise_security": True,
                "multi_tenant": config.multi_tenant_enabled,
                "compliance_monitoring": bool(config.security.compliance_frameworks),
                "performance_monitoring": config.monitoring.enabled,
                "code_export": True,
                "template_library": True,
                "ai_chat": True,  # Now implemented!
            },
            "frontend_integration": {
                "cors_configured": True,
                "websocket_endpoint": "/ws",
                "sse_endpoint": "/events",
                "api_base": "/api",
                "authentication": "jwt" if config.enable_auth else "none",
            },
            "sdk_integration": {
                "using_sdk_gateway": True,
                "embedded_sqlalchemy": True,
                "middleware_repositories": True,
                "sdk_nodes_only": True,
                "manual_orchestration": False,
            },
        }

    # Add Studio configuration endpoint for frontend
    @gateway.app.get("/api/studio/config", tags=["Studio"])
    async def studio_config():
        """Get Studio configuration for frontend initialization."""
        return {
            "environment": config.environment.value,
            "features": {
                "authentication": config.enable_auth,
                "real_time": config.middleware.realtime_enabled,
                "ai_chat": config.ai.enable_ai_chat,
                "multi_tenant": config.multi_tenant_enabled,
                "api_docs": config.enable_api_docs,
            },
            "limits": {
                "max_concurrent_executions": config.execution.max_concurrent_executions,
                "execution_timeout_seconds": config.execution.default_timeout_seconds,
                "max_concurrent_sessions": config.middleware.max_concurrent_sessions,
                "session_timeout_minutes": config.security.session_timeout_minutes,
            },
            "endpoints": {
                "workflows": "/api/workflows",
                "executions": "/api/executions",
                "nodes": "/api/nodes/types",  # PRD-compliant endpoint
                "chat": "/api/chat",  # New AI chat endpoint
                "sessions": "/api/sessions",
                "websocket": "/ws",
                "events": "/events",
                "health": "/health",
                "stats": "/api/stats",
            },
        }

    logger.info("📋 Studio-specific endpoints added to SDK gateway")


# Create the application instance using SDK gateway
app = None


def get_app():
    """Get the FastAPI app instance from SDK gateway."""
    global app
    if app is None:
        gateway = create_studio_gateway()
        app = gateway.app
        app.gateway = gateway  # Store reference to gateway
    return app


# For direct access to the FastAPI app
app = get_app()


if __name__ == "__main__":
    """Run the Studio API server using SDK gateway."""
    gateway = create_studio_gateway()

    logger.info(
        f"🚀 Starting Enterprise Kailash Studio API on {config.host}:{config.port}"
    )
    logger.info(f"📊 Environment: {config.environment.value}")
    logger.info(f"🔒 Security Level: {config.security.level.value}")
    logger.info(f"🏢 Multi-tenant: {config.multi_tenant_enabled}")
    logger.info(f"🔗 Frontend CORS: {config.cors_origins}")

    # Run using SDK gateway's built-in server
    gateway.run(
        host=config.host,
        port=config.port,
        workers=config.workers if not config.reload else 1,
        reload=config.reload,
        log_level="debug" if config.debug else "info",
        access_log=config.monitoring.enable_request_logging,
    )
