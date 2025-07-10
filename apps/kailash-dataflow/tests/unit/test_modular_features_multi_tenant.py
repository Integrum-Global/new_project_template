"""
Unit Tests: Modular DataFlow Multi-Tenant Support

Tests for the new modular multi-tenant feature.
"""

from typing import Any, Dict, Optional
from unittest.mock import MagicMock, patch

import pytest
from dataflow.core import Environment
from dataflow.core.config import DataFlowConfig
from dataflow.core.engine import DataFlow
from dataflow.features.multi_tenant import MultiTenantManager


class TestTenantConfig:
    """Test tenant configuration."""

    def test_tenant_config_defaults(self):
        """Test default tenant configuration."""
        config = DataFlowConfig()

        # Test multi-tenant configuration defaults
        assert config.security.multi_tenant is False
        assert config.security.tenant_isolation_strategy == "schema"
        assert config.security.audit_enabled is True

    def test_tenant_config_custom_values(self):
        """Test custom tenant configuration."""
        config = DataFlowConfig()
        config.security.multi_tenant = True
        config.security.tenant_isolation_strategy = "database"
        config.security.audit_enabled = False

        assert config.security.multi_tenant is True
        assert config.security.tenant_isolation_strategy == "database"
        assert config.security.audit_enabled is False

    def test_tenant_config_validation(self):
        """Test tenant configuration validation."""
        # Valid configuration with PostgreSQL
        config = DataFlowConfig()
        config.security.multi_tenant = True
        config.database.url = "postgresql://localhost/test"
        issues = config.validate()
        assert len(issues) == 0

        # Test with SQLite (should have validation issues)
        config.database.url = "sqlite:///test.db"
        issues = config.validate()
        assert len(issues) > 0
        assert any("multi-tenant" in issue.lower() for issue in issues)


class TestTenantContext:
    """Test tenant context management."""

    def test_tenant_context_initialization(self):
        """Test tenant context initialization."""
        config = DataFlowConfig()
        config.security.multi_tenant = True
        dataflow_instance = DataFlow(config=config)
        mt_manager = MultiTenantManager(dataflow_instance)

        # Create a tenant
        result = mt_manager.create_tenant(
            "tenant_456", "ACME Corp", {"tier": "enterprise", "region": "us-west"}
        )

        assert result["success"] is True
        assert result["tenant"]["tenant_id"] == "tenant_456"
        assert result["tenant"]["name"] == "ACME Corp"
        assert result["tenant"]["metadata"]["tier"] == "enterprise"
        assert result["tenant"]["metadata"]["region"] == "us-west"

    def test_tenant_context_permissions(self):
        """Test tenant context permission management."""
        config = DataFlowConfig()
        config.security.multi_tenant = True
        dataflow_instance = DataFlow(config=config)
        mt_manager = MultiTenantManager(dataflow_instance)

        # Create a tenant
        result = mt_manager.create_tenant("tenant_789", "Test Corp")

        assert result["success"] is True
        # Test tenant access validation
        assert mt_manager.validate_tenant_access("tenant_789", "tenant_789") is True
        assert mt_manager.validate_tenant_access("tenant_789", "other_tenant") is False

    def test_tenant_context_resource_limits(self):
        """Test tenant context resource limits."""
        config = DataFlowConfig()
        config.security.multi_tenant = True
        dataflow_instance = DataFlow(config=config)
        mt_manager = MultiTenantManager(dataflow_instance)

        # Create tenant with metadata
        result = mt_manager.create_tenant(
            "tenant_limits",
            "Limited Corp",
            {"max_records": 10000, "max_queries_per_hour": 1000},
        )

        assert result["success"] is True
        tenant_info = mt_manager.get_tenant("tenant_limits")
        assert tenant_info["metadata"]["max_records"] == 10000
        assert tenant_info["metadata"]["max_queries_per_hour"] == 1000


class TestMultiTenantManager:
    """Test MultiTenantManager functionality."""

    def test_tenant_manager_initialization(self):
        """Test MultiTenantManager initialization."""
        config = DataFlowConfig()
        config.security.multi_tenant = True
        dataflow_instance = DataFlow(config=config)
        mt_manager = MultiTenantManager(dataflow_instance)

        assert mt_manager.dataflow == dataflow_instance
        assert mt_manager._tenants == {}
        assert mt_manager._current_tenant is None

    def test_create_tenant(self):
        """Test tenant creation."""
        config = DataFlowConfig()
        config.security.multi_tenant = True
        dataflow_instance = DataFlow(config=config)
        mt_manager = MultiTenantManager(dataflow_instance)

        result = mt_manager.create_tenant(
            "test_tenant", "Test Corporation", {"tier": "premium"}
        )

        assert result["success"] is True
        assert result["tenant"]["tenant_id"] == "test_tenant"
        assert result["tenant"]["name"] == "Test Corporation"
        assert result["tenant"]["metadata"]["tier"] == "premium"

    def test_tenant_context_switching(self):
        """Test tenant context switching."""
        config = DataFlowConfig()
        config.security.multi_tenant = True
        dataflow_instance = DataFlow(config=config)
        mt_manager = MultiTenantManager(dataflow_instance)

        # Create tenants
        mt_manager.create_tenant("tenant1", "Tenant One")
        mt_manager.create_tenant("tenant2", "Tenant Two")

        # Switch to tenant1
        result = mt_manager.set_current_tenant("tenant1")
        assert result["success"] is True
        assert mt_manager.get_current_tenant() == "tenant1"

        # Switch to tenant2
        result = mt_manager.set_current_tenant("tenant2")
        assert result["success"] is True
        assert mt_manager.get_current_tenant() == "tenant2"

    def test_delete_tenant(self):
        """Test tenant deletion."""
        config = DataFlowConfig()
        config.security.multi_tenant = True
        dataflow_instance = DataFlow(config=config)
        mt_manager = MultiTenantManager(dataflow_instance)

        # Create and delete tenant
        mt_manager.create_tenant("delete_me", "Delete Me")
        result = mt_manager.delete_tenant("delete_me")

        assert result["success"] is True
        assert result["deleted_tenant"]["tenant_id"] == "delete_me"
        assert mt_manager.get_tenant("delete_me") is None

    def test_data_isolation(self):
        """Test data isolation functionality."""
        config = DataFlowConfig()
        config.security.multi_tenant = True
        dataflow_instance = DataFlow(config=config)
        mt_manager = MultiTenantManager(dataflow_instance)

        # Create tenant and test data isolation
        mt_manager.create_tenant("isolation_test", "Isolation Test")
        mt_manager.set_current_tenant("isolation_test")

        test_data = {"name": "Test User", "email": "test@example.com"}
        isolated_data = mt_manager.isolate_data(test_data)

        assert isolated_data["tenant_id"] == "isolation_test"
        assert isolated_data["name"] == "Test User"
        assert isolated_data["email"] == "test@example.com"
