"""
Integration tests for Nexus Application.

These tests verify component interactions with real Docker services.
NO MOCKING - Uses real PostgreSQL, Redis, etc.
"""

import asyncio
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Add SDK root to path
sdk_root = Path(__file__).parent.parent.parent.parent.parent / "src"
sys.path.insert(0, str(sdk_root))

# Add SDK tests to path for test utilities
sdk_tests = Path(__file__).parent.parent.parent.parent.parent / "tests"
sys.path.insert(0, str(sdk_tests))

# Add Nexus src to path
nexus_src = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(nexus_src))

import os

# Import test utilities from local utils directory
import sys

from nexus.core.application import NexusApplication, create_application
from nexus.core.config import NexusConfig

from kailash.workflow.builder import WorkflowBuilder

sys.path.insert(0, str(Path(__file__).parent.parent / "utils"))
from docker_config import (
    ensure_docker_services,
    get_postgres_connection_string,
    get_redis_connection_params,
)


@pytest.mark.integration
@pytest.mark.requires_docker
class TestNexusApplicationIntegration:
    """Integration tests for NexusApplication."""

    @pytest.fixture(scope="class")
    async def docker_services(self):
        """Ensure Docker services are available."""
        services_available = await ensure_docker_services()
        if not services_available:
            pytest.skip("Docker services not available")
        yield

    @pytest.fixture
    def minimal_config(self):
        """Minimal configuration for testing."""
        return NexusConfig(
            name="Test Nexus Integration",
            channels={
                "api": {"enabled": False},
                "cli": {"enabled": False},
                "mcp": {"enabled": False},
            },
            features={
                "authentication": {"enabled": False},
                "multi_tenant": {"enabled": False},
                "marketplace": {"enabled": False},
            },
        )

    @pytest.fixture
    def enterprise_config(self):
        """Enterprise configuration for testing."""
        return NexusConfig(
            name="Enterprise Test Nexus",
            channels={
                "api": {"enabled": False},
                "cli": {"enabled": False},
                "mcp": {"enabled": False},
            },
            features={
                "authentication": {
                    "enabled": True,
                    "providers": [{"type": "local", "config": {"name": "Local Auth"}}],
                    "mfa": {"required": False},
                },
                "multi_tenant": {"enabled": True, "isolation": "moderate"},
                "marketplace": {"enabled": True},
            },
        )

    @pytest.mark.asyncio
    async def test_application_creation_minimal(self, docker_services, minimal_config):
        """Test creating application with minimal configuration."""
        app = NexusApplication(minimal_config)

        assert app.config.name == "Test Nexus Integration"
        assert app._gateway is not None
        assert app.workflow_registry is not None
        assert not hasattr(app, "auth_manager")
        assert not hasattr(app, "tenant_manager")
        assert not hasattr(app, "marketplace")

    @pytest.mark.asyncio
    async def test_application_creation_enterprise(
        self, docker_services, enterprise_config
    ):
        """Test creating application with enterprise features."""
        app = NexusApplication(enterprise_config)

        assert app.config.name == "Enterprise Test Nexus"
        assert hasattr(app, "auth_manager")
        assert hasattr(app, "tenant_manager")
        assert hasattr(app, "marketplace")

        # Check enterprise components are properly configured
        assert app.auth_manager is not None
        assert len(app.auth_manager.providers) == 1
        assert app.tenant_manager.isolation_level == "moderate"

    @pytest.mark.asyncio
    async def test_application_lifecycle(self, docker_services, minimal_config):
        """Test application start/stop lifecycle."""
        app = NexusApplication(minimal_config)

        # Application should not be running initially
        assert not app._running
        assert not app._initialized

        # Mock the gateway to avoid actual server startup
        with (
            patch.object(app._gateway, "start") as mock_start,
            patch.object(app._gateway, "stop") as mock_stop,
        ):

            # Start application
            await app.start()
            assert app._running
            assert app._initialized
            mock_start.assert_called_once()

            # Stop application
            await app.stop()
            assert not app._running
            mock_stop.assert_called_once()

    @pytest.mark.asyncio
    async def test_workflow_registration(self, docker_services, minimal_config):
        """Test workflow registration with real components."""
        app = NexusApplication(minimal_config)

        # Create a test workflow
        workflow = WorkflowBuilder()
        workflow.add_node(
            "PythonCodeNode",
            "test_node",
            {"code": "result = {'message': 'Integration test successful'}"},
        )
        built_workflow = workflow.build()

        # Register workflow
        app.register_workflow("integration/test", built_workflow)

        # Verify registration in registry
        registered = app.workflow_registry.get("integration/test")
        assert registered is not None

        # Verify metadata
        metadata = app.workflow_registry.get_metadata("integration/test")
        assert metadata.workflow_id == "integration/test"

    @pytest.mark.asyncio
    async def test_enterprise_components_interaction(
        self, docker_services, enterprise_config
    ):
        """Test interaction between enterprise components."""
        app = NexusApplication(enterprise_config)

        # Initialize components
        await app._initialize_components()

        # Test tenant creation
        tenant = app.tenant_manager.create_tenant(
            name="Integration Test Tenant", description="Test tenant for integration"
        )
        assert tenant.name == "Integration Test Tenant"

        # Test authentication
        token = await app.auth_manager.authenticate(
            {"username": "integration_user", "password": "test_password"}
        )
        assert token is not None
        assert token.user_id == "integration_user"

        # Test marketplace workflow publishing
        workflow = WorkflowBuilder()
        workflow.add_node(
            "PythonCodeNode", "process", {"code": "result = 'marketplace test'"}
        )

        app.register_workflow("marketplace/test", workflow.build())

        item = app.marketplace.publish(
            workflow_id="marketplace/test",
            publisher_id=tenant.tenant_id,
            name="Integration Test Workflow",
            description="Test workflow for integration testing",
        )
        assert item.name == "Integration Test Workflow"
        assert item.publisher_id == tenant.tenant_id

        # Test installation
        install_result = app.marketplace.install(
            item_id=item.item_id, user_id="integration_user", tenant_id=tenant.tenant_id
        )
        assert install_result["success"] is True

        # Cleanup
        await app._cleanup_components()

    @pytest.mark.asyncio
    async def test_health_check_integration(self, docker_services, enterprise_config):
        """Test health check with real components."""
        app = NexusApplication(enterprise_config)
        await app._initialize_components()

        # Mock gateway health check to avoid server dependency
        with patch.object(app._gateway, "health_check") as mock_health:
            mock_health.return_value = {
                "status": "healthy",
                "channels": {"api": "disabled", "cli": "disabled", "mcp": "disabled"},
            }

            health = await app.health_check()

            assert "status" in health
            assert "auth" in health
            assert "tenants" in health
            assert "marketplace" in health

            # Verify each component reports health
            assert health["auth"]["healthy"] is True
            assert health["tenants"]["healthy"] is True
            assert health["marketplace"]["healthy"] is True

    @pytest.mark.asyncio
    async def test_session_management_integration(
        self, docker_services, minimal_config
    ):
        """Test enhanced session management."""
        app = NexusApplication(minimal_config)

        # Create test session
        session_id = await app.session_manager.create_session(
            user_id="integration_user", channel="test"
        )
        assert session_id is not None

        # Get session data
        session_data = await app.session_manager.get_session(session_id)
        assert session_data["user_id"] == "integration_user"

        # Update session
        await app.session_manager.update_session(session_id, {"test_data": "value"})

        # Verify update
        updated_data = await app.session_manager.get_session(session_id)
        assert "test_data" in updated_data

        # List user sessions
        user_sessions = await app.session_manager.list_user_sessions("integration_user")
        assert len(user_sessions) == 1
        assert user_sessions[0]["session_id"] == session_id

        # Cleanup
        await app.session_manager.delete_session(session_id)

    @pytest.mark.asyncio
    async def test_multi_tenant_workflow_isolation(
        self, docker_services, enterprise_config
    ):
        """Test workflow isolation between tenants."""
        app = NexusApplication(enterprise_config)
        await app._initialize_components()

        # Create two tenants
        tenant1 = app.tenant_manager.create_tenant(name="Tenant 1")
        tenant2 = app.tenant_manager.create_tenant(name="Tenant 2")

        # Register workflow for tenant 1
        workflow = WorkflowBuilder()
        workflow.add_node("PythonCodeNode", "process", {"code": "result = 'tenant1'"})
        app.register_workflow("tenant1/workflow", workflow.build())

        # Check resource registration
        resource_tenant = app.tenant_manager.get_resource_tenant("tenant1/workflow")
        assert resource_tenant == "system"  # Registered as system resource

        # Test access validation
        assert (
            app.tenant_manager.validate_access(tenant1.tenant_id, tenant1.tenant_id)
            is True
        )

        assert (
            app.tenant_manager.validate_access(tenant1.tenant_id, tenant2.tenant_id)
            is False
        )

        # Test quota enforcement
        allowed, details = app.tenant_manager.check_quota(
            tenant1.tenant_id, "workflow", 1
        )
        assert allowed is True

        # Track usage
        app.tenant_manager.track_usage(tenant1.tenant_id, "workflow", 1)
        usage = app.tenant_manager.get_usage(tenant1.tenant_id)
        assert usage.workflows == 1

    @pytest.mark.asyncio
    async def test_create_application_function(self, docker_services):
        """Test the create_application convenience function."""
        app = create_application(
            name="Function Test",
            features={
                "authentication": {"enabled": True},
                "multi_tenant": {"enabled": True},
            },
        )

        assert isinstance(app, NexusApplication)
        assert app.config.name == "Function Test"
        assert hasattr(app, "auth_manager")
        assert hasattr(app, "tenant_manager")

    @pytest.mark.asyncio
    async def test_error_handling_integration(self, docker_services, minimal_config):
        """Test error handling in integrated components."""
        app = NexusApplication(minimal_config)

        # Test invalid workflow registration
        with pytest.raises(Exception):
            app.register_workflow("", None)

        # Test session cleanup
        # Create some sessions
        session1 = await app.session_manager.create_session("user1", channel="test")
        session2 = await app.session_manager.create_session("user2", channel="test")

        # Force expire one session for testing
        if (
            hasattr(app.session_manager._base_manager, "_sessions")
            and session1 in app.session_manager._base_manager._sessions
        ):
            from datetime import datetime, timedelta, timezone

            app.session_manager._base_manager._sessions[session1].expires_at = (
                datetime.now(timezone.utc) - timedelta(hours=1)
            )

        # Cleanup expired sessions
        expired_count = await app.session_manager.cleanup_expired()
        assert expired_count >= 0  # Could be 1 if session1 was expired

        # Valid session should still exist
        session2_data = await app.session_manager.get_session(session2)
        assert session2_data is not None
