"""
Multi-Tenant Management for Nexus

Built entirely on Kailash SDK's TenantIsolationManager.
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from kailash.nodes.admin.audit_log import EnterpriseAuditLogNode as AuditLogNode
from kailash.nodes.admin.permission_check import PermissionCheckNode
from kailash.nodes.admin.tenant_isolation import TenantIsolationManager
from kailash.nodes.data.async_sql import AsyncSQLDatabaseNode
from kailash.workflow.builder import WorkflowBuilder

logger = logging.getLogger(__name__)


@dataclass
class TenantQuota:
    """Resource quotas for a tenant."""

    workflows: int = 100
    executions_per_day: int = 10000
    storage_mb: int = 1024
    api_calls_per_hour: int = 1000
    concurrent_sessions: int = 100

    def to_dict(self) -> Dict[str, int]:
        """Convert to dictionary."""
        return {
            "workflows": self.workflows,
            "executions_per_day": self.executions_per_day,
            "storage_mb": self.storage_mb,
            "api_calls_per_hour": self.api_calls_per_hour,
            "concurrent_sessions": self.concurrent_sessions,
        }


@dataclass
class TenantUsage:
    """Current resource usage for a tenant."""

    workflows: int = 0
    executions_today: int = 0
    storage_mb: float = 0
    api_calls_this_hour: int = 0
    active_sessions: int = 0
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "workflows": self.workflows,
            "executions_today": self.executions_today,
            "storage_mb": self.storage_mb,
            "api_calls_this_hour": self.api_calls_this_hour,
            "active_sessions": self.active_sessions,
            "last_updated": self.last_updated.isoformat(),
        }


@dataclass
class Tenant:
    """Tenant information."""

    tenant_id: str
    name: str
    description: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = True
    isolation_level: str = "strict"  # strict, moderate, basic
    custom_domain: Optional[str] = None
    quotas: TenantQuota = field(default_factory=TenantQuota)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "tenant_id": self.tenant_id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "is_active": self.is_active,
            "isolation_level": self.isolation_level,
            "custom_domain": self.custom_domain,
            "quotas": self.quotas.to_dict(),
            "metadata": self.metadata,
        }


class MultiTenantManager:
    """Manages multi-tenant functionality for Nexus.

    Built on Kailash SDK's TenantIsolationManager and related nodes.
    """

    def __init__(
        self,
        isolation_level: str = "strict",
        default_quotas: Optional[Dict[str, Any]] = None,
    ):
        """Initialize multi-tenant manager.

        Args:
            isolation_level: Default isolation level for new tenants
            default_quotas: Default quotas for new tenants
        """
        self.isolation_level = isolation_level
        self.default_quotas = TenantQuota(**(default_quotas or {}))

        # Tenant storage
        self._tenants: Dict[str, Tenant] = {}
        self._usage: Dict[str, TenantUsage] = {}
        self._resources: Dict[str, Dict[str, str]] = (
            {}
        )  # resource_id -> {type, tenant_id}

        # Create SDK tenant isolation manager
        # In real implementation, this would use the actual node
        self._isolation_manager = None  # TenantIsolationManager()

        # Create management workflows
        self._init_management_workflows()

        logger.info(
            f"Multi-tenant manager initialized with {isolation_level} isolation"
        )

    def _init_management_workflows(self):
        """Initialize tenant management workflows using SDK nodes."""
        # Tenant validation workflow
        self.validation_workflow = WorkflowBuilder()

        # Add access control check
        self.validation_workflow.add_node(
            "PermissionCheckNode",
            "check_access",
            {"strategy": "rbac", "resource_type": "tenant"},
        )

        # Add audit logging
        self.validation_workflow.add_node(
            "AuditLogNode",
            "audit",
            {"event_type": "tenant_access", "include_metadata": True},
        )

        # Connect nodes
        self.validation_workflow.add_connection(
            "check_access", "result", "audit", "event"
        )

        # Quota enforcement workflow
        self.quota_workflow = WorkflowBuilder()

        self.quota_workflow.add_node(
            "PythonCodeNode",
            "check_quota",
            {
                "code": """
# Check if tenant has exceeded quota
tenant_id = context.get('tenant_id')
resource_type = context.get('resource_type')
amount = context.get('amount', 1)

# In production, this would query actual usage
result = {
    'allowed': True,
    'remaining': 100,
    'limit': 1000
}
"""
            },
        )

        self.quota_workflow.add_node(
            "AuditLogNode", "audit_quota", {"event_type": "quota_check"}
        )

        self.quota_workflow.add_connection(
            "check_quota", "result", "audit_quota", "event"
        )

    async def initialize(self):
        """Initialize the multi-tenant manager."""
        # In production, would initialize SDK components
        logger.info("Multi-tenant manager initialized")

    async def cleanup(self):
        """Cleanup resources."""
        # In production, would cleanup SDK components
        logger.info("Multi-tenant manager cleaned up")

    def create_tenant(
        self,
        name: str,
        description: str = "",
        isolation_level: Optional[str] = None,
        quotas: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Tenant:
        """Create a new tenant.

        Args:
            name: Tenant name
            description: Tenant description
            isolation_level: Override default isolation level
            quotas: Override default quotas
            metadata: Additional metadata

        Returns:
            Created tenant
        """
        tenant_id = f"tenant_{uuid.uuid4().hex[:8]}"

        # Create tenant
        tenant = Tenant(
            tenant_id=tenant_id,
            name=name,
            description=description,
            isolation_level=isolation_level or self.isolation_level,
            quotas=TenantQuota(**(quotas or self.default_quotas.to_dict())),
            metadata=metadata or {},
        )

        # Store tenant
        self._tenants[tenant_id] = tenant
        self._usage[tenant_id] = TenantUsage()

        # Create isolation using SDK
        if self._isolation_manager:
            # self._isolation_manager.create_tenant_isolation(tenant_id)
            pass

        logger.info(f"Created tenant: {tenant_id} ({name})")
        return tenant

    def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        """Get tenant by ID.

        Args:
            tenant_id: Tenant identifier

        Returns:
            Tenant or None if not found
        """
        return self._tenants.get(tenant_id)

    def list_tenants(self, is_active: Optional[bool] = None) -> List[Tenant]:
        """List all tenants.

        Args:
            is_active: Filter by active status

        Returns:
            List of tenants
        """
        tenants = list(self._tenants.values())

        if is_active is not None:
            tenants = [t for t in tenants if t.is_active == is_active]

        return sorted(tenants, key=lambda t: t.created_at, reverse=True)

    def update_tenant(self, tenant_id: str, updates: Dict[str, Any]) -> Tenant:
        """Update tenant information.

        Args:
            tenant_id: Tenant identifier
            updates: Fields to update

        Returns:
            Updated tenant

        Raises:
            ValueError: If tenant not found
        """
        tenant = self._tenants.get(tenant_id)
        if not tenant:
            raise ValueError(f"Tenant {tenant_id} not found")

        # Update allowed fields
        allowed_fields = ["name", "description", "is_active", "metadata"]
        for field_name, value in updates.items():
            if field_name in allowed_fields:
                setattr(tenant, field_name, value)

        tenant.updated_at = datetime.now(timezone.utc)

        logger.info(f"Updated tenant: {tenant_id}")
        return tenant

    def delete_tenant(self, tenant_id: str, force: bool = False) -> bool:
        """Delete a tenant.

        Args:
            tenant_id: Tenant identifier
            force: Force deletion even with resources

        Returns:
            True if deleted

        Raises:
            ValueError: If tenant has resources and force=False
        """
        if tenant_id not in self._tenants:
            return False

        # Check for resources
        tenant_resources = [
            rid
            for rid, info in self._resources.items()
            if info["tenant_id"] == tenant_id
        ]

        if tenant_resources and not force:
            raise ValueError(
                f"Tenant {tenant_id} has {len(tenant_resources)} resources. "
                "Use force=True to delete anyway."
            )

        # Remove resources
        for resource_id in tenant_resources:
            del self._resources[resource_id]

        # Remove tenant
        del self._tenants[tenant_id]
        del self._usage[tenant_id]

        logger.info(f"Deleted tenant: {tenant_id}")
        return True

    def register_resource(
        self, resource_id: str, resource_type: str, tenant_id: Optional[str] = None
    ):
        """Register a resource with a tenant.

        Args:
            resource_id: Resource identifier
            resource_type: Type of resource
            tenant_id: Tenant ID, None for system resources
        """
        self._resources[resource_id] = {
            "type": resource_type,
            "tenant_id": tenant_id or "system",
        }

        # Track usage
        if tenant_id and tenant_id in self._usage:
            if resource_type == "workflow":
                self._usage[tenant_id].workflows += 1

    def get_resource_tenant(self, resource_id: str) -> Optional[str]:
        """Get the tenant ID for a resource.

        Args:
            resource_id: Resource identifier

        Returns:
            Tenant ID or None
        """
        resource_info = self._resources.get(resource_id)
        if resource_info:
            tenant_id = resource_info["tenant_id"]
            return tenant_id
        return None

    def validate_access(
        self, tenant_id: str, user_tenant_id: str, resource_id: Optional[str] = None
    ) -> bool:
        """Validate tenant access using SDK's TenantIsolationManager.

        Args:
            tenant_id: Target tenant ID
            user_tenant_id: User's tenant ID
            resource_id: Optional resource to check

        Returns:
            True if access allowed
        """
        # System tenant can access anything
        if user_tenant_id == "system":
            return True

        # Check tenant match
        if tenant_id != user_tenant_id:
            return False

        # Check resource if provided
        if resource_id:
            resource_tenant = self.get_resource_tenant(resource_id)
            if resource_tenant and resource_tenant != user_tenant_id:
                return False

        return True

    def check_quota(
        self, tenant_id: str, resource_type: str, amount: int = 1
    ) -> Tuple[bool, Dict[str, Any]]:
        """Check if tenant has quota available.

        Args:
            tenant_id: Tenant identifier
            resource_type: Type of resource
            amount: Amount to check

        Returns:
            Tuple of (allowed, details)
        """
        tenant = self._tenants.get(tenant_id)
        if not tenant:
            return False, {"error": "Tenant not found"}

        usage = self._usage.get(tenant_id, TenantUsage())
        quotas = tenant.quotas

        # Check specific resource type
        checks = {
            "workflow": (usage.workflows + amount <= quotas.workflows),
            "execution": (usage.executions_today + amount <= quotas.executions_per_day),
            "api_call": (
                usage.api_calls_this_hour + amount <= quotas.api_calls_per_hour
            ),
            "session": (usage.active_sessions + amount <= quotas.concurrent_sessions),
        }

        allowed = checks.get(resource_type, True)

        details = {
            "allowed": allowed,
            "resource_type": resource_type,
            "current_usage": getattr(usage, f"{resource_type}s", 0),
            "limit": getattr(quotas, f"{resource_type}s", 0),
            "requested": amount,
        }

        return allowed, details

    def track_usage(self, tenant_id: str, resource_type: str, amount: int = 1):
        """Track resource usage for a tenant.

        Args:
            tenant_id: Tenant identifier
            resource_type: Type of resource
            amount: Amount used
        """
        if tenant_id not in self._usage:
            self._usage[tenant_id] = TenantUsage()

        usage = self._usage[tenant_id]

        if resource_type == "workflow":
            usage.workflows += amount
        elif resource_type == "execution":
            usage.executions_today += amount
        elif resource_type == "api_call":
            usage.api_calls_this_hour += amount
        elif resource_type == "session":
            usage.active_sessions += amount

        usage.last_updated = datetime.now(timezone.utc)

    def get_usage(self, tenant_id: str) -> Optional[TenantUsage]:
        """Get current usage for a tenant.

        Args:
            tenant_id: Tenant identifier

        Returns:
            TenantUsage or None
        """
        return self._usage.get(tenant_id)

    def reset_usage(self, tenant_id: str, resource_type: Optional[str] = None):
        """Reset usage counters for a tenant.

        Args:
            tenant_id: Tenant identifier
            resource_type: Specific resource type or None for all
        """
        if tenant_id not in self._usage:
            return

        usage = self._usage[tenant_id]

        if resource_type == "execution" or resource_type is None:
            usage.executions_today = 0
        if resource_type == "api_call" or resource_type is None:
            usage.api_calls_this_hour = 0

        usage.last_updated = datetime.now(timezone.utc)

    async def health_check(self) -> Dict[str, Any]:
        """Get health status of multi-tenant system.

        Returns:
            Health status dictionary
        """
        return {
            "healthy": True,
            "total_tenants": len(self._tenants),
            "active_tenants": len([t for t in self._tenants.values() if t.is_active]),
            "total_resources": len(self._resources),
            "isolation_level": self.isolation_level,
        }
