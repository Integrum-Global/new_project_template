"""
Unit tests for Multi-Tenant Manager.
"""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest
from nexus.enterprise.multi_tenant import (
    MultiTenantManager,
    Tenant,
    TenantQuota,
    TenantUsage,
)


class TestMultiTenantManager:
    """Test MultiTenantManager class."""

    @pytest.fixture
    def manager(self):
        """Create a multi-tenant manager instance."""
        return MultiTenantManager()

    def test_initialization(self, manager):
        """Test manager initialization."""
        assert manager.isolation_level == "strict"
        assert isinstance(manager.default_quotas, TenantQuota)
        assert manager.default_quotas.workflows == 100
        assert len(manager._tenants) == 0
        assert len(manager._usage) == 0

    def test_create_tenant(self, manager):
        """Test creating a tenant."""
        tenant = manager.create_tenant(name="Test Corp", description="Test tenant")

        assert tenant.name == "Test Corp"
        assert tenant.description == "Test tenant"
        assert tenant.tenant_id.startswith("tenant_")
        assert tenant.is_active is True
        assert tenant.isolation_level == "strict"
        assert isinstance(tenant.quotas, TenantQuota)

        # Check storage
        assert tenant.tenant_id in manager._tenants
        assert tenant.tenant_id in manager._usage

    def test_create_tenant_custom_settings(self, manager):
        """Test creating tenant with custom settings."""
        custom_quotas = {
            "workflows": 500,
            "executions_per_day": 50000,
            "storage_mb": 10240,
        }

        tenant = manager.create_tenant(
            name="Enterprise Corp",
            description="Enterprise tenant",
            isolation_level="moderate",
            quotas=custom_quotas,
            metadata={"plan": "enterprise"},
        )

        assert tenant.isolation_level == "moderate"
        assert tenant.quotas.workflows == 500
        assert tenant.quotas.executions_per_day == 50000
        assert tenant.quotas.storage_mb == 10240
        assert tenant.metadata["plan"] == "enterprise"

    def test_get_tenant(self, manager):
        """Test getting a tenant by ID."""
        tenant = manager.create_tenant(name="Get Test")
        tenant_id = tenant.tenant_id

        # Get existing tenant
        retrieved = manager.get_tenant(tenant_id)
        assert retrieved is not None
        assert retrieved.name == "Get Test"

        # Get non-existent tenant
        retrieved = manager.get_tenant("nonexistent")
        assert retrieved is None

    def test_list_tenants(self, manager):
        """Test listing tenants."""
        # Create multiple tenants
        tenant1 = manager.create_tenant(name="Tenant 1")
        tenant2 = manager.create_tenant(name="Tenant 2")
        tenant3 = manager.create_tenant(name="Tenant 3")

        # Deactivate one
        tenant2.is_active = False

        # List all
        all_tenants = manager.list_tenants()
        assert len(all_tenants) == 3

        # List active only
        active_tenants = manager.list_tenants(is_active=True)
        assert len(active_tenants) == 2
        assert all(t.is_active for t in active_tenants)

        # List inactive only
        inactive_tenants = manager.list_tenants(is_active=False)
        assert len(inactive_tenants) == 1
        assert not inactive_tenants[0].is_active

    def test_update_tenant(self, manager):
        """Test updating tenant information."""
        tenant = manager.create_tenant(name="Update Test")
        tenant_id = tenant.tenant_id

        # Update tenant
        updated = manager.update_tenant(
            tenant_id,
            {
                "name": "Updated Name",
                "description": "Updated description",
                "is_active": False,
                "metadata": {"updated": True},
            },
        )

        assert updated.name == "Updated Name"
        assert updated.description == "Updated description"
        assert updated.is_active is False
        assert updated.metadata["updated"] is True
        assert updated.updated_at > updated.created_at

        # Try to update non-existent
        with pytest.raises(ValueError):
            manager.update_tenant("nonexistent", {})

    def test_delete_tenant(self, manager):
        """Test deleting a tenant."""
        tenant = manager.create_tenant(name="Delete Test")
        tenant_id = tenant.tenant_id

        # Delete tenant
        result = manager.delete_tenant(tenant_id)
        assert result is True

        # Check it's gone
        assert manager.get_tenant(tenant_id) is None
        assert tenant_id not in manager._tenants
        assert tenant_id not in manager._usage

        # Delete non-existent
        result = manager.delete_tenant("nonexistent")
        assert result is False

    def test_delete_tenant_with_resources(self, manager):
        """Test deleting tenant with resources."""
        tenant = manager.create_tenant(name="Resource Test")
        tenant_id = tenant.tenant_id

        # Register some resources
        manager.register_resource("workflow1", "workflow", tenant_id)
        manager.register_resource("workflow2", "workflow", tenant_id)

        # Try to delete without force
        with pytest.raises(ValueError, match="has 2 resources"):
            manager.delete_tenant(tenant_id, force=False)

        # Delete with force
        result = manager.delete_tenant(tenant_id, force=True)
        assert result is True
        assert "workflow1" not in manager._resources
        assert "workflow2" not in manager._resources

    def test_register_resource(self, manager):
        """Test registering resources."""
        tenant = manager.create_tenant(name="Resource Test")
        tenant_id = tenant.tenant_id

        # Register workflow resource
        manager.register_resource("workflow1", "workflow", tenant_id)

        # Check registration
        assert "workflow1" in manager._resources
        assert manager._resources["workflow1"]["type"] == "workflow"
        assert manager._resources["workflow1"]["tenant_id"] == tenant_id

        # Check usage tracking
        usage = manager.get_usage(tenant_id)
        assert usage.workflows == 1

        # Register system resource
        manager.register_resource("system1", "workflow", None)
        assert manager._resources["system1"]["tenant_id"] == "system"

    def test_get_resource_tenant(self, manager):
        """Test getting resource tenant."""
        tenant = manager.create_tenant(name="Resource Test")
        tenant_id = tenant.tenant_id

        # Register resources
        manager.register_resource("tenant_resource", "workflow", tenant_id)
        manager.register_resource("system_resource", "workflow", None)

        # Get tenant for resources
        assert manager.get_resource_tenant("tenant_resource") == tenant_id
        assert (
            manager.get_resource_tenant("system_resource") == "system"
        )  # System resources now return "system"
        assert manager.get_resource_tenant("nonexistent") is None

    def test_validate_access(self, manager):
        """Test tenant access validation."""
        tenant1 = manager.create_tenant(name="Tenant 1")
        tenant2 = manager.create_tenant(name="Tenant 2")

        # Same tenant access
        assert manager.validate_access(tenant1.tenant_id, tenant1.tenant_id) is True

        # Cross-tenant access
        assert manager.validate_access(tenant1.tenant_id, tenant2.tenant_id) is False

        # System access
        assert manager.validate_access(tenant1.tenant_id, "system") is True

        # Resource access
        manager.register_resource("resource1", "workflow", tenant1.tenant_id)
        assert (
            manager.validate_access(tenant1.tenant_id, tenant1.tenant_id, "resource1")
            is True
        )
        assert (
            manager.validate_access(tenant1.tenant_id, tenant2.tenant_id, "resource1")
            is False
        )

    def test_check_quota(self, manager):
        """Test quota checking."""
        tenant = manager.create_tenant(
            name="Quota Test", quotas={"workflows": 5, "executions_per_day": 100}
        )
        tenant_id = tenant.tenant_id

        # Check workflow quota
        allowed, details = manager.check_quota(tenant_id, "workflow", 3)
        assert allowed is True
        assert details["allowed"] is True
        assert details["limit"] == 5

        # Use some quota
        manager.track_usage(tenant_id, "workflow", 3)

        # Check again
        allowed, details = manager.check_quota(tenant_id, "workflow", 3)
        assert allowed is False  # Would exceed limit (3 + 3 > 5)

        # Check execution quota
        allowed, details = manager.check_quota(tenant_id, "execution", 50)
        assert allowed is True

        # Check non-existent tenant
        allowed, details = manager.check_quota("nonexistent", "workflow", 1)
        assert allowed is False
        assert details["error"] == "Tenant not found"

    def test_track_usage(self, manager):
        """Test usage tracking."""
        tenant = manager.create_tenant(name="Usage Test")
        tenant_id = tenant.tenant_id

        # Track various usage
        manager.track_usage(tenant_id, "workflow", 2)
        manager.track_usage(tenant_id, "execution", 10)
        manager.track_usage(tenant_id, "api_call", 50)
        manager.track_usage(tenant_id, "session", 5)

        # Get usage
        usage = manager.get_usage(tenant_id)
        assert usage.workflows == 2
        assert usage.executions_today == 10
        assert usage.api_calls_this_hour == 50
        assert usage.active_sessions == 5
        assert isinstance(usage.last_updated, datetime)

    def test_reset_usage(self, manager):
        """Test resetting usage counters."""
        tenant = manager.create_tenant(name="Reset Test")
        tenant_id = tenant.tenant_id

        # Track usage
        manager.track_usage(tenant_id, "execution", 100)
        manager.track_usage(tenant_id, "api_call", 200)

        # Reset execution only
        manager.reset_usage(tenant_id, "execution")
        usage = manager.get_usage(tenant_id)
        assert usage.executions_today == 0
        assert usage.api_calls_this_hour == 200

        # Reset all
        manager.reset_usage(tenant_id)
        usage = manager.get_usage(tenant_id)
        assert usage.executions_today == 0
        assert usage.api_calls_this_hour == 0

    @pytest.mark.asyncio
    async def test_health_check(self, manager):
        """Test health check."""
        # Create some tenants
        manager.create_tenant(name="Active 1")
        manager.create_tenant(name="Active 2")
        inactive = manager.create_tenant(name="Inactive")
        manager.update_tenant(inactive.tenant_id, {"is_active": False})

        # Register some resources
        manager.register_resource("r1", "workflow", None)
        manager.register_resource("r2", "workflow", None)

        health = await manager.health_check()

        assert health["healthy"] is True
        assert health["total_tenants"] == 3
        assert health["active_tenants"] == 2
        assert health["total_resources"] == 2
        assert health["isolation_level"] == "strict"

    def test_tenant_model(self):
        """Test Tenant model."""
        tenant = Tenant(
            tenant_id="test123", name="Test Tenant", description="Test description"
        )

        assert tenant.tenant_id == "test123"
        assert tenant.name == "Test Tenant"
        assert tenant.is_active is True
        assert tenant.isolation_level == "strict"
        assert isinstance(tenant.quotas, TenantQuota)

        # Test to_dict
        tenant_dict = tenant.to_dict()
        assert tenant_dict["tenant_id"] == "test123"
        assert tenant_dict["name"] == "Test Tenant"
        assert "quotas" in tenant_dict

    def test_quota_model(self):
        """Test TenantQuota model."""
        quota = TenantQuota(workflows=200, storage_mb=2048)

        assert quota.workflows == 200
        assert quota.storage_mb == 2048
        assert quota.executions_per_day == 10000  # Default

        quota_dict = quota.to_dict()
        assert quota_dict["workflows"] == 200
        assert quota_dict["storage_mb"] == 2048
