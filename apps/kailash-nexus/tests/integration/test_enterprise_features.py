"""
Integration tests for Enterprise Features.

Tests the interaction between authentication, multi-tenancy, and marketplace
with real infrastructure.
"""

import asyncio
import sys
from pathlib import Path

import pytest

# Add paths
sdk_root = Path(__file__).parent.parent.parent.parent.parent / "src"
sys.path.insert(0, str(sdk_root))
sdk_tests = Path(__file__).parent.parent.parent.parent.parent / "tests"
sys.path.insert(0, str(sdk_tests))
nexus_src = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(nexus_src))

import os

from nexus.core.application import create_application
from nexus.enterprise.auth import EnterpriseAuthManager
from nexus.enterprise.multi_tenant import MultiTenantManager
from nexus.marketplace.registry import MarketplaceRegistry

from kailash.workflow.builder import WorkflowBuilder

# Import test utilities from local utils directory
sys.path.insert(0, str(Path(__file__).parent.parent / "utils"))
from docker_config import ensure_docker_services


@pytest.mark.integration
@pytest.mark.requires_docker
class TestEnterpriseIntegration:
    """Integration tests for enterprise features."""

    @pytest.fixture(scope="class")
    async def docker_services(self):
        """Ensure Docker services are available."""
        services_available = await ensure_docker_services()
        if not services_available:
            pytest.skip("Docker services not available")
        yield

    @pytest.fixture
    def enterprise_app(self, docker_services):
        """Create enterprise application for testing."""
        app = create_application(
            name="Enterprise Integration Test",
            channels={
                "api": {"enabled": False},
                "cli": {"enabled": False},
                "mcp": {"enabled": False},
            },
            features={
                "authentication": {
                    "enabled": True,
                    "providers": [
                        {"type": "local", "config": {"name": "Local Auth"}},
                        {"type": "ldap", "config": {"name": "LDAP"}},
                    ],
                    "mfa": {"required": False},
                },
                "multi_tenant": {
                    "enabled": True,
                    "isolation": "strict",
                    "default_quotas": {"workflows": 50, "executions_per_day": 1000},
                },
                "marketplace": {"enabled": True},
            },
        )
        # Components will be initialized during application use
        yield app
        # Cleanup handled by application

    @pytest.mark.asyncio
    async def test_auth_tenant_integration(self, enterprise_app):
        """Test authentication and tenant management integration."""
        auth_manager = enterprise_app.auth_manager
        tenant_manager = enterprise_app.tenant_manager

        # Create a tenant
        tenant = tenant_manager.create_tenant(
            name="Test Corporation", description="Integration test tenant"
        )

        # Authenticate a user
        token = await auth_manager.authenticate(
            {"username": "corp_user", "password": "secure_pass"}
        )
        assert token is not None

        # Validate tenant access
        assert (
            tenant_manager.validate_access(
                tenant.tenant_id, "system"  # System user can access any tenant
            )
            is True
        )

        # Check quota for tenant
        allowed, details = tenant_manager.check_quota(tenant.tenant_id, "workflow", 5)
        assert allowed is True
        assert details["limit"] == 50

        # Track some usage
        tenant_manager.track_usage(tenant.tenant_id, "workflow", 3)
        tenant_manager.track_usage(tenant.tenant_id, "execution", 100)

        # Verify usage tracking
        usage = tenant_manager.get_usage(tenant.tenant_id)
        assert usage.workflows == 3
        assert usage.executions_today == 100

        # Test quota enforcement
        allowed, details = tenant_manager.check_quota(
            tenant.tenant_id, "workflow", 50  # Would exceed limit
        )
        assert allowed is False

    @pytest.mark.asyncio
    async def test_marketplace_tenant_integration(self, enterprise_app):
        """Test marketplace and tenant integration."""
        tenant_manager = enterprise_app.tenant_manager
        marketplace = enterprise_app.marketplace

        # Create publisher tenant
        publisher_tenant = tenant_manager.create_tenant(
            name="Publisher Corp", description="Workflow publisher"
        )

        # Create consumer tenant
        consumer_tenant = tenant_manager.create_tenant(
            name="Consumer Corp", description="Workflow consumer"
        )

        # Create and register a workflow
        workflow = WorkflowBuilder()
        workflow.add_node(
            "HTTPRequestNode",
            "fetch",
            {"url": "https://api.example.com/data", "method": "GET"},
        )
        workflow.add_node(
            "PythonCodeNode",
            "process",
            {
                "code": """
# Process the API response
result = {
    'processed': True,
    'data_count': len(data.get('items', [])),
    'tenant_id': context.get('tenant_id')
}
"""
            },
        )
        workflow.add_connection("fetch", "response", "process", "data")

        enterprise_app.register_workflow("corp/data-processor", workflow.build())

        # Publish to marketplace
        item = marketplace.publish(
            workflow_id="corp/data-processor",
            publisher_id=publisher_tenant.tenant_id,
            name="Corporate Data Processor",
            description="Process external API data",
            version="1.0.0",
            price=99.99,
            categories=["enterprise", "data"],
            tags=["api", "processing", "corporate"],
        )

        # Verify publication
        assert item.publisher_id == publisher_tenant.tenant_id
        assert item.name == "Corporate Data Processor"
        assert item.price == 99.99

        # Consumer installs the workflow
        install_result = marketplace.install(
            item_id=item.item_id,
            user_id="consumer_user",
            tenant_id=consumer_tenant.tenant_id,
        )
        assert install_result["success"] is True

        # Track usage for consumer tenant
        tenant_manager.track_usage(consumer_tenant.tenant_id, "workflow", 1)

        # Add review from consumer
        review = marketplace.add_review(
            item_id=item.item_id,
            user_id="consumer_user",
            rating=5,
            comment="Excellent workflow! Saved us hours of processing time.",
        )
        assert review.rating == 5
        assert review.is_verified_install is True

        # Check marketplace stats
        assert item.stats.total_installs == 1
        assert item.stats.total_reviews == 1
        assert item.stats.average_rating == 5.0

    @pytest.mark.asyncio
    async def test_auth_marketplace_integration(self, enterprise_app):
        """Test authentication and marketplace integration."""
        auth_manager = enterprise_app.auth_manager
        marketplace = enterprise_app.marketplace

        # Create API key for marketplace access
        api_key = auth_manager.generate_api_key(
            app_name="Marketplace Client",
            permissions=["marketplace:read", "marketplace:install"],
            expires_in_days=30,
        )

        # Validate API key
        app_info = auth_manager.validate_api_key(api_key)
        assert app_info is not None
        assert app_info["app_name"] == "Marketplace Client"
        assert "marketplace:read" in app_info["permissions"]

        # Authenticate user for marketplace activities
        token = await auth_manager.authenticate(
            {"username": "marketplace_user", "password": "market_pass"}
        )

        # Create a simple workflow for marketplace
        workflow = WorkflowBuilder()
        workflow.add_node(
            "PythonCodeNode", "hello", {"code": "result = f'Hello from {name}!'"}
        )

        enterprise_app.register_workflow("simple/greeting", workflow.build())

        # Publish with authenticated user context
        item = marketplace.publish(
            workflow_id="simple/greeting",
            publisher_id=token.user_id,
            name="Simple Greeting",
            description="A simple greeting workflow",
            price=0.0,
            tags=["simple", "demo"],
        )

        # Search marketplace
        results, total = marketplace.search(query="greeting")
        assert total >= 1
        assert any(r.name == "Simple Greeting" for r in results)

        # Install with API key authentication context
        install_result = marketplace.install(
            item_id=item.item_id, user_id="api_client", tenant_id=None
        )
        assert install_result["success"] is True

        # Revoke API key
        key_id = list(auth_manager._api_keys.keys())[0]
        auth_manager.revoke_api_key(key_id)

        # Verify key is revoked
        app_info = auth_manager.validate_api_key(api_key)
        assert app_info is None

    @pytest.mark.asyncio
    async def test_full_enterprise_workflow(self, enterprise_app):
        """Test complete enterprise workflow scenario."""
        auth_manager = enterprise_app.auth_manager
        tenant_manager = enterprise_app.tenant_manager
        marketplace = enterprise_app.marketplace

        # Step 1: Setup enterprise tenant
        enterprise_tenant = tenant_manager.create_tenant(
            name="Global Enterprise Inc",
            description="Large enterprise customer",
            quotas={
                "workflows": 1000,
                "executions_per_day": 100000,
                "storage_mb": 10240,
                "api_calls_per_hour": 50000,
            },
            metadata={"plan": "enterprise", "industry": "finance"},
        )

        # Step 2: Authenticate enterprise admin
        admin_token = await auth_manager.authenticate(
            {"username": "enterprise_admin", "password": "enterprise_secure_123"}
        )
        assert admin_token.user_id == "enterprise_admin"

        # Step 3: Create enterprise workflow
        enterprise_workflow = WorkflowBuilder()
        enterprise_workflow.add_node(
            "AsyncSQLDatabaseNode",
            "query_db",
            {
                "host": "localhost",
                "port": 5434,
                "database": "kailash_test",
                "user": "test_user",
                "password": "test_password",
                "query": "SELECT * FROM financial_data WHERE date >= %s",
                "parameters": ["2024-01-01"],
            },
        )
        enterprise_workflow.add_node(
            "LLMAgentNode",
            "analyze",
            {
                "model": "gpt-4",
                "prompt": "Analyze this financial data for compliance: {data}",
            },
        )
        enterprise_workflow.add_node(
            "AuditLogNode",
            "audit",
            {"event_type": "financial_analysis", "compliance_required": True},
        )

        # Connect the workflow
        enterprise_workflow.add_connection("query_db", "result", "analyze", "data")
        enterprise_workflow.add_connection("analyze", "response", "audit", "event")

        # Register workflow
        enterprise_app.register_workflow(
            "enterprise/financial-analysis", enterprise_workflow.build()
        )

        # Step 4: Publish to private marketplace
        financial_item = marketplace.publish(
            workflow_id="enterprise/financial-analysis",
            publisher_id=enterprise_tenant.tenant_id,
            name="Financial Compliance Analyzer",
            description="AI-powered financial data analysis for compliance",
            version="1.0.0",
            price=999.99,
            categories=["finance", "compliance", "enterprise"],
            tags=["ai", "finance", "compliance", "audit"],
            is_public=False,  # Private enterprise workflow
        )

        # Step 5: Feature the workflow for enterprise customers
        marketplace.feature_item(financial_item.item_id, True)
        marketplace.verify_item(financial_item.item_id, True)

        # Step 6: Track enterprise usage
        for _ in range(10):
            tenant_manager.track_usage(enterprise_tenant.tenant_id, "execution", 100)
            tenant_manager.track_usage(enterprise_tenant.tenant_id, "api_call", 500)

        # Step 7: Generate API keys for departments
        departments = ["trading", "risk", "compliance"]
        api_keys = {}

        for dept in departments:
            key = auth_manager.generate_api_key(
                app_name=f"Enterprise {dept.title()} Dept",
                permissions=[f"{dept}:read", f"{dept}:execute", "marketplace:read"],
                expires_in_days=90,
            )
            api_keys[dept] = key

        # Step 8: Verify enterprise setup
        # Check tenant status
        usage = tenant_manager.get_usage(enterprise_tenant.tenant_id)
        assert usage.executions_today == 1000
        assert usage.api_calls_this_hour == 5000

        # Check quota compliance
        allowed, details = tenant_manager.check_quota(
            enterprise_tenant.tenant_id, "execution", 10000
        )
        assert allowed is True  # Well within limits

        # Check marketplace item
        assert financial_item.is_featured is True
        assert financial_item.is_verified is True
        assert financial_item.stats.trending_score > 0

        # Check API keys
        assert len(api_keys) == 3
        for dept, key in api_keys.items():
            app_info = auth_manager.validate_api_key(key)
            assert app_info is not None
            assert f"{dept}:read" in app_info["permissions"]

        # Step 9: Health check for enterprise components
        health = await enterprise_app.health_check()
        assert health["tenants"]["total_tenants"] >= 1
        assert health["marketplace"]["total_items"] >= 1
        assert health["auth"]["active_api_keys"] >= 3

    @pytest.mark.asyncio
    async def test_performance_and_scaling(self, enterprise_app):
        """Test performance with multiple tenants and workflows."""
        tenant_manager = enterprise_app.tenant_manager
        marketplace = enterprise_app.marketplace

        # Create multiple tenants
        tenants = []
        for i in range(5):
            tenant = tenant_manager.create_tenant(
                name=f"Tenant {i}", description=f"Performance test tenant {i}"
            )
            tenants.append(tenant)

        # Create multiple workflows and marketplace items
        workflows = []
        items = []

        for i in range(10):
            # Create workflow
            workflow = WorkflowBuilder()
            workflow.add_node(
                "PythonCodeNode",
                "process",
                {"code": f"result = 'Workflow {i} executed'"},
            )
            workflow_built = workflow.build()

            enterprise_app.register_workflow(f"perf/workflow-{i}", workflow_built)
            workflows.append(workflow_built)

            # Publish to marketplace
            item = marketplace.publish(
                workflow_id=f"perf/workflow-{i}",
                publisher_id=tenants[i % len(tenants)].tenant_id,
                name=f"Performance Workflow {i}",
                description=f"Performance test workflow {i}",
                price=float(i * 10),
                categories=["performance", "test"],
                tags=[f"perf{i}", "test"],
            )
            items.append(item)

        # Simulate usage across tenants
        for tenant in tenants:
            for _ in range(20):
                tenant_manager.track_usage(tenant.tenant_id, "execution", 10)
                tenant_manager.track_usage(tenant.tenant_id, "api_call", 100)

        # Install workflows across tenants
        for i, item in enumerate(items[:5]):  # Install first 5 items
            for j, tenant in enumerate(tenants):
                if i != j % len(tenants):  # Don't install own workflows
                    marketplace.install(
                        item_id=item.item_id,
                        user_id=f"user_{j}",
                        tenant_id=tenant.tenant_id,
                    )

        # Add reviews
        for i, item in enumerate(items[:3]):  # Review first 3 items
            for j in range(2):  # 2 reviews per item
                marketplace.add_review(
                    item_id=item.item_id,
                    user_id=f"reviewer_{i}_{j}",
                    rating=4 + (j % 2),  # Alternate between 4 and 5
                    comment=f"Review {j} for workflow {i}",
                )

        # Verify performance metrics
        # Check tenant usage
        for tenant in tenants:
            usage = tenant_manager.get_usage(tenant.tenant_id)
            assert usage.executions_today == 200  # 20 * 10
            assert usage.api_calls_this_hour == 2000  # 20 * 100

        # Check marketplace stats
        total_installs = sum(item.stats.total_installs for item in items)
        assert total_installs >= 20  # 5 items * 4 cross-tenant installs

        reviewed_items = [item for item in items if item.stats.total_reviews > 0]
        assert len(reviewed_items) == 3

        # Search performance
        results, total = marketplace.search(query="performance", limit=5)
        assert len(results) == 5
        assert total == 10

        # List operations performance
        all_tenants = tenant_manager.list_tenants()
        assert len(all_tenants) >= 5

        featured_items = marketplace.get_featured(limit=10)
        assert len(featured_items) == 0  # None featured in this test
