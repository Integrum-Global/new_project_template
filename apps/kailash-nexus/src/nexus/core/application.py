"""
Nexus Application - Main application built on Kailash SDK NexusGateway.

This application provides enterprise features on top of the SDK's NexusGateway.
"""

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from kailash.nexus import create_nexus as sdk_create_nexus
from kailash.nexus.gateway import NexusConfig as SDKNexusConfig
from kailash.nexus.gateway import NexusGateway
from kailash.nodes.admin.audit_log import EnterpriseAuditLogNode as AuditLogNode
from kailash.nodes.admin.permission_check import PermissionCheckNode
from kailash.nodes.admin.tenant_isolation import TenantIsolationManager
from kailash.nodes.admin.user_management import UserManagementNode
from kailash.nodes.auth.mfa import MultiFactorAuthNode
from kailash.workflow import Workflow
from kailash.workflow.builder import WorkflowBuilder

from ..channels import APIChannelWrapper, CLIChannelWrapper, MCPChannelWrapper
from ..enterprise.auth import EnterpriseAuthManager
from ..enterprise.backup import BackupManager
from ..enterprise.disaster_recovery import DisasterRecoveryManager
from ..enterprise.multi_tenant import MultiTenantManager
from ..marketplace.registry import MarketplaceRegistry
from ..monitoring.metrics import HealthMonitor, MetricsCollector
from .config import NexusConfig
from .registry import WorkflowRegistry
from .session import EnhancedSessionManager

logger = logging.getLogger(__name__)


class NexusApplication:
    """
    Enterprise application built on Kailash SDK's NexusGateway.

    Provides additional enterprise features:
    - Multi-tenant management
    - Workflow marketplace
    - Enterprise authentication
    - Enhanced monitoring
    - Production deployment patterns
    """

    def __init__(self, config: Optional[NexusConfig] = None):
        """Initialize Nexus Application with enterprise features.

        Args:
            config: Application configuration
        """
        self.config = config or NexusConfig()

        # Convert to SDK config
        sdk_config = self._create_sdk_config()

        # Create underlying SDK Nexus Gateway
        self._gateway = NexusGateway(sdk_config)

        # Enterprise components (all using Kailash SDK)
        self._init_enterprise_components()

        # Application state
        self._initialized = False
        self._running = False

        logger.info(f"Nexus Application initialized: {self.config.name}")

    def _create_sdk_config(self) -> SDKNexusConfig:
        """Convert application config to SDK config."""
        return SDKNexusConfig(
            name=self.config.name,
            description=self.config.description,
            version=self.config.version,
            enable_api=self.config.channels.api.enabled,
            enable_cli=self.config.channels.cli.enabled,
            enable_mcp=self.config.channels.mcp.enabled,
            api_host=self.config.channels.api.host,
            api_port=self.config.channels.api.port,
            api_cors_origins=self.config.channels.api.cors_origins,
            mcp_host=self.config.channels.mcp.host,
            mcp_port=self.config.channels.mcp.port,
            session_timeout=self.config.features.session.timeout,
            enable_health_monitoring=self.config.features.monitoring.health_checks,
        )

    def _init_enterprise_components(self):
        """Initialize enterprise components using Kailash SDK nodes."""
        # Enhanced session management
        self.session_manager = EnhancedSessionManager(
            base_manager=self._gateway.session_manager,
            multi_tenant=self.config.features.multi_tenant.enabled,
            create_workflows=False,
        )

        # Workflow registry with marketplace
        self.workflow_registry = WorkflowRegistry()
        if self.config.features.marketplace.enabled:
            self.marketplace = MarketplaceRegistry()

        # Multi-tenant management
        if self.config.features.multi_tenant.enabled:
            self.tenant_manager = MultiTenantManager(
                isolation_level=self.config.features.multi_tenant.isolation,
                default_quotas=self.config.features.multi_tenant.default_quotas,
            )

        # Enterprise authentication
        if self.config.features.authentication.enabled:
            self.auth_manager = EnterpriseAuthManager(
                providers=self.config.features.authentication.providers,
                mfa_config=self.config.features.authentication.mfa,
            )

        # Backup and disaster recovery
        self.backup_manager = BackupManager(self)
        self.disaster_recovery = DisasterRecoveryManager(self)

        # Monitoring and metrics
        if self.config.features.monitoring.enabled:
            self.metrics_collector = MetricsCollector(
                enable_prometheus=self.config.features.monitoring.prometheus_enabled,
                metrics_port=self.config.features.monitoring.metrics_port,
            )
            self.health_monitor = HealthMonitor(self.metrics_collector)

            # Set application info
            self.metrics_collector.set_app_info(
                version=self.config.version,
                environment=self.config.deployment.environment,
            )

            # Register health checks
            self._register_health_checks()
        else:
            self.metrics_collector = None
            self.health_monitor = None

        # Create enterprise workflows
        self._create_enterprise_workflows()

    def _create_enterprise_workflows(self):
        """Create built-in enterprise workflows using SDK components."""
        # User management workflow
        user_mgmt = WorkflowBuilder()
        user_mgmt.add_node("UserManagementNode", "user_ops", {})
        user_mgmt.add_node("AuditLogNode", "audit", {})
        user_mgmt.add_connection("user_ops", "result", "audit", "event")
        self.register_workflow("system/user-management", user_mgmt.build())

        # Tenant isolation workflow
        if self.config.features.multi_tenant.enabled:
            tenant_flow = WorkflowBuilder()
            tenant_flow.add_node(
                "PythonCodeNode",
                "validate_tenant",
                {
                    "code": """
# Tenant validation using TenantIsolationManager
from kailash.nodes.admin.tenant_isolation import TenantIsolationManager
manager = TenantIsolationManager()
result = {
    'valid': manager.validate_tenant_access(tenant_id, user_id),
    'tenant_id': tenant_id
}
"""
                },
            )
            tenant_flow.add_node(
                "PermissionCheckNode", "enforce_access", {"strategy": "rbac"}
            )
            tenant_flow.add_connection(
                "validate_tenant", "result", "enforce_access", "context"
            )
            self.register_workflow("system/tenant-isolation", tenant_flow.build())

        # MFA authentication workflow
        if self.config.features.authentication.mfa.required:
            mfa_flow = WorkflowBuilder()
            mfa_flow.add_node(
                "MultiFactorAuthNode",
                "mfa_verify",
                {"methods": self.config.features.authentication.mfa.methods},
            )
            mfa_flow.add_node(
                "AuditLogNode", "mfa_audit", {"event_type": "mfa_authentication"}
            )
            mfa_flow.add_connection("mfa_verify", "result", "mfa_audit", "event")
            self.register_workflow("system/mfa-auth", mfa_flow.build())

    def register_workflow(self, workflow_id: str, workflow: Workflow):
        """Register a workflow with the application.

        Args:
            workflow_id: Unique workflow identifier
            workflow: Workflow instance
        """
        # Register with registry
        # Validate inputs
        if not workflow_id:
            raise ValueError("Workflow ID cannot be empty")
        if workflow is None:
            raise ValueError("Workflow cannot be None")

        # Register with gateway
        self._gateway.register_workflow(workflow_id, workflow)

        # Register with registry
        self.workflow_registry.register(workflow_id, workflow)

        # Apply tenant isolation if enabled
        if hasattr(self, "tenant_manager"):
            self.tenant_manager.register_resource(workflow_id, "workflow")

        # Record metrics if enabled
        if self.metrics_collector:
            self.metrics_collector.record_tenant_operation(
                tenant_id=getattr(self, "_current_tenant_id", "default"),
                operation="workflow_registration",
                status="success",
            )

        logger.info(f"Registered workflow: {workflow_id}")

    async def start(self):
        """Start the Nexus application."""
        if self._running:
            logger.warning("Nexus application already running")
            return

        logger.info("Starting Nexus application...")

        # Initialize components
        await self._initialize_components()

        # Start gateway
        await self._gateway.start()

        # Wrap channels with enterprise features
        self._wrap_channels()

        self._running = True
        logger.info("Nexus application started successfully")

    async def _initialize_components(self):
        """Initialize all enterprise components."""
        # Initialize auth if enabled
        if hasattr(self, "auth_manager"):
            await self.auth_manager.initialize()

        # Initialize tenant manager if enabled
        if hasattr(self, "tenant_manager"):
            await self.tenant_manager.initialize()

        # Initialize marketplace if enabled
        if hasattr(self, "marketplace"):
            await self.marketplace.initialize()

        # Initialize monitoring if enabled
        if self.metrics_collector:
            await self.metrics_collector.start_metrics_server()
            logger.info("Metrics collection initialized")

        self._initialized = True

    async def stop(self):
        """Stop the Nexus application."""
        if not self._running:
            return

        logger.info("Stopping Nexus application...")

        # Stop gateway
        await self._gateway.stop()

        # Cleanup components
        await self._cleanup_components()

        self._running = False
        logger.info("Nexus application stopped")

    async def _cleanup_components(self):
        """Cleanup enterprise components."""
        if hasattr(self, "auth_manager"):
            await self.auth_manager.cleanup()

        if hasattr(self, "tenant_manager"):
            await self.tenant_manager.cleanup()

        if hasattr(self, "marketplace"):
            await self.marketplace.cleanup()

    async def health_check(self) -> Dict[str, Any]:
        """Get application health status.

        Returns:
            Health status dictionary
        """
        if self.health_monitor:
            # Use comprehensive health monitoring
            health = await self.health_monitor.run_health_checks()
        else:
            # Fall back to basic health check
            health = await self._gateway.health_check()

        # Add enterprise component health
        if hasattr(self, "auth_manager"):
            health["auth"] = await self.auth_manager.health_check()

        if hasattr(self, "tenant_manager"):
            health["tenants"] = await self.tenant_manager.health_check()

        if hasattr(self, "marketplace"):
            health["marketplace"] = await self.marketplace.health_check()

        # Add metrics summary
        if self.metrics_collector:
            health["metrics"] = self.metrics_collector.get_metrics_summary()

        return health

    def _register_health_checks(self):
        """Register health check functions."""
        if not self.health_monitor:
            return

        # Database health check
        async def database_health():
            try:
                # Check database connectivity via gateway
                result = await self._gateway.health_check()
                return {"healthy": result.get("status") == "healthy", "details": result}
            except Exception as e:
                return {"healthy": False, "error": str(e)}

        self.health_monitor.register_health_check("database", database_health, 30)

        # Application health check
        async def application_health():
            return {
                "healthy": self._running and self._initialized,
                "running": self._running,
                "initialized": self._initialized,
                "config_name": self.config.name,
            }

        self.health_monitor.register_health_check("application", application_health, 15)

        # Enterprise components health check
        if hasattr(self, "auth_manager"):

            async def auth_health():
                try:
                    result = await self.auth_manager.health_check()
                    return {
                        "healthy": result.get("status") == "healthy",
                        "details": result,
                    }
                except Exception as e:
                    return {"healthy": False, "error": str(e)}

            self.health_monitor.register_health_check("authentication", auth_health, 60)

    def get_metrics_endpoint(self) -> Optional[str]:
        """Get metrics endpoint URL if metrics are enabled.

        Returns:
            Metrics endpoint URL or None
        """
        if self.metrics_collector and self.metrics_collector.enable_prometheus:
            return f"http://localhost:{self.metrics_collector.metrics_port}/metrics"
        return None

    def _wrap_channels(self):
        """Wrap SDK channels with enterprise features."""
        # Wrap API channel
        if hasattr(self._gateway, "_channels") and self._gateway._channels.get("api"):
            self.api_channel = APIChannelWrapper(
                api_channel=self._gateway._channels["api"],
                multi_tenant_manager=getattr(self, "tenant_manager", None),
                auth_manager=getattr(self, "auth_manager", None),
            )

        # Wrap CLI channel
        if hasattr(self._gateway, "_channels") and self._gateway._channels.get("cli"):
            self.cli_channel = CLIChannelWrapper(
                cli_channel=self._gateway._channels["cli"],
                multi_tenant_manager=getattr(self, "tenant_manager", None),
                auth_manager=getattr(self, "auth_manager", None),
            )

        # Wrap MCP channel
        if hasattr(self._gateway, "_channels") and self._gateway._channels.get("mcp"):
            self.mcp_channel = MCPChannelWrapper(
                mcp_channel=self._gateway._channels["mcp"],
                multi_tenant_manager=getattr(self, "tenant_manager", None),
                auth_manager=getattr(self, "auth_manager", None),
                marketplace_registry=getattr(self, "marketplace", None),
            )

    def create_api_client(self, **kwargs):
        """Create an API client for the application."""
        return self._gateway.create_api_client(**kwargs)

    def create_cli_interface(self, **kwargs):
        """Create a CLI interface for the application."""
        return (
            self._gateway._channels.get("cli")
            if hasattr(self._gateway, "_channels")
            else None
        )

    def create_mcp_client(self, **kwargs):
        """Create an MCP client for the application."""
        return self._gateway.create_mcp_client(**kwargs)

    async def run_forever(self):
        """Run the application until interrupted."""
        await self.start()
        try:
            # Keep running until stopped
            await self._gateway.wait_for_shutdown()
        finally:
            await self.stop()


def create_application(**kwargs) -> NexusApplication:
    """Create a Nexus application instance.

    This is the main entry point for the application.

    Args:
        **kwargs: Configuration options

    Returns:
        NexusApplication instance
    """
    config = NexusConfig(**kwargs)
    return NexusApplication(config)
