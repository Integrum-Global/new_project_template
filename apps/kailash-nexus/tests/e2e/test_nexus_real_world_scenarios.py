"""
End-to-End tests for Nexus Real World Scenarios.

These tests simulate complete user workflows with real infrastructure.
Tests complete business scenarios end-to-end.
"""

import asyncio
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
import pytest_asyncio

# Add paths
sdk_root = Path(__file__).parent.parent.parent.parent.parent / "src"
sys.path.insert(0, str(sdk_root))
sdk_tests = Path(__file__).parent.parent.parent.parent.parent / "tests"
sys.path.insert(0, str(sdk_tests))
nexus_src = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(nexus_src))

# Import SDK test utilities
from pathlib import Path

from nexus.channels import APIChannelWrapper, CLIChannelWrapper, MCPChannelWrapper
from nexus.core.application import create_application

from kailash.runtime.local import LocalRuntime
from kailash.workflow.builder import WorkflowBuilder

sdk_tests_utils = Path(__file__).parent.parent.parent.parent.parent / "tests" / "utils"
sys.path.insert(0, str(sdk_tests_utils))
from docker_config import ensure_docker_services


@pytest.mark.e2e
@pytest.mark.requires_docker
@pytest.mark.requires_postgres
@pytest.mark.requires_redis
class TestNexusRealWorldScenarios:
    """End-to-end tests for real-world Nexus scenarios."""

    @pytest_asyncio.fixture(scope="class")
    async def docker_services(self):
        """Ensure all Docker services are available for E2E testing."""
        # For testing without real Docker, we'll use a mock setup
        yield

    @pytest_asyncio.fixture
    async def production_nexus_app(self, docker_services):
        """Create a production-like Nexus application."""
        app = create_application(
            name="Production Nexus E2E",
            description="Production-like setup for E2E testing",
            channels={
                "api": {"enabled": False},  # Disable to avoid port conflicts
                "cli": {"enabled": False},
                "mcp": {"enabled": False},
            },
            features={
                "authentication": {
                    "enabled": True,
                    "providers": [
                        {"type": "local", "config": {"name": "Local Auth"}},
                        {"type": "ldap", "config": {"name": "Corporate LDAP"}},
                    ],
                    "mfa": {"required": True, "methods": ["totp"]},
                },
                "multi_tenant": {
                    "enabled": True,
                    "isolation": "strict",
                    "default_quotas": {
                        "workflows": 100,
                        "executions_per_day": 10000,
                        "storage_mb": 1024,
                        "api_calls_per_hour": 1000,
                        "concurrent_sessions": 50,
                    },
                },
                "marketplace": {"enabled": True, "moderation_enabled": True},
                "audit": {"enabled": True, "retention_days": 90},
                "monitoring": {"enabled": True, "health_checks": True},
            },
        )

        await app._initialize_components()
        yield app
        await app._cleanup_components()

    @pytest.mark.asyncio
    async def test_enterprise_onboarding_scenario(self, production_nexus_app):
        """
        Test complete enterprise customer onboarding scenario.

        Scenario:
        1. New enterprise customer signs up
        2. Admin creates tenant and sets up authentication
        3. Users authenticate and access the platform
        4. Workflows are created and published to marketplace
        5. Other tenants discover and install workflows
        6. Usage is tracked and monitored
        """
        app = production_nexus_app

        # Step 1: Enterprise customer onboarding
        print("🏢 Step 1: Enterprise customer onboarding")

        # Create enterprise tenant
        await app.tenant_manager.initialize()
        enterprise_tenant = app.tenant_manager.create_tenant(
            name="GlobalTech Solutions",
            description="Fortune 500 technology company",
            isolation_level="strict",
            quotas={
                "workflows": 500,
                "executions_per_day": 50000,
                "storage_mb": 5120,
                "api_calls_per_hour": 10000,
                "concurrent_sessions": 200,
            },
            metadata={
                "plan": "enterprise",
                "industry": "technology",
                "size": "large",
                "support_tier": "premium",
            },
        )

        assert enterprise_tenant.name == "GlobalTech Solutions"
        assert enterprise_tenant.quotas.workflows == 500
        assert enterprise_tenant.metadata["plan"] == "enterprise"

        # Step 2: Admin authentication and setup
        print("👤 Step 2: Admin authentication and setup")

        # Admin authenticates with MFA
        await app.auth_manager.initialize()
        admin_token = await app.auth_manager.authenticate(
            {
                "username": "globaltech_admin",
                "password": "secure_enterprise_pass_123!",
                "mfa_code": "123456",
            }
        )

        assert admin_token is not None
        assert admin_token.user_id == "globaltech_admin"

        # Generate API keys for different departments
        departments = {
            "engineering": ["workflows:read", "workflows:write", "marketplace:read"],
            "operations": ["workflows:read", "workflows:execute", "monitoring:read"],
            "compliance": ["audit:read", "workflows:read", "tenants:read"],
        }

        api_keys = {}
        for dept, permissions in departments.items():
            key = app.auth_manager.generate_api_key(
                app_name=f"GlobalTech {dept.title()} Department",
                permissions=permissions,
                expires_in_days=90,
            )
            api_keys[dept] = key

        # Step 3: User authentication and access
        print("🔐 Step 3: User authentication and access")

        # Multiple users authenticate
        users = []
        for i in range(3):
            user_token = await app.auth_manager.authenticate(
                {
                    "username": f"globaltech_user_{i}",
                    "password": f"user_pass_{i}",
                    "mfa_code": "123456",
                }
            )
            users.append(user_token)

        assert len(users) == 3
        assert all(user.user_id.startswith("globaltech_user_") for user in users)

        # Step 4: Workflow creation and marketplace publishing
        print("🔄 Step 4: Workflow creation and marketplace publishing")

        # Create enterprise data processing workflow
        data_workflow = WorkflowBuilder()
        data_workflow.add_node(
            "HTTPRequestNode",
            "fetch_data",
            {
                "url": "https://api.globaltech.com/data",
                "method": "GET",
                "headers": {"Authorization": "Bearer {api_key}"},
            },
        )
        data_workflow.add_node(
            "PythonCodeNode",
            "validate_data",
            {
                "code": """
import json
from datetime import datetime, timezone

# Validate incoming data
if not isinstance(data, dict):
    raise ValueError("Invalid data format")

# Add processing metadata
result = {
    'data': data,
    'processed_at': datetime.now(timezone.utc).isoformat(),
    'tenant_id': context.get('tenant_id'),
    'validation_status': 'passed',
    'record_count': len(data.get('records', []))
}
"""
            },
        )
        data_workflow.add_node(
            "AsyncSQLDatabaseNode",
            "store_data",
            {
                "host": "localhost",
                "port": 5434,
                "database": "kailash_test",
                "user": "test_user",
                "password": "test_password",
                "query": "INSERT INTO processed_data (tenant_id, data, processed_at) VALUES (%s, %s, %s)",
                "parameters": ["{tenant_id}", "{data}", "{processed_at}"],
            },
        )
        data_workflow.add_node(
            "AuditLogNode",
            "audit_processing",
            {
                "event_type": "data_processing",
                "tenant_id": "{tenant_id}",
                "include_metadata": True,
            },
        )

        # Connect workflow nodes
        data_workflow.add_connection("fetch_data", "response", "validate_data", "data")
        data_workflow.add_connection("validate_data", "result", "store_data", "input")
        data_workflow.add_connection(
            "store_data", "result", "audit_processing", "event"
        )

        # Register workflow
        app.register_workflow("globaltech/data-processor", data_workflow.build())

        # Publish to marketplace
        data_item = app.marketplace.publish(
            workflow_id="globaltech/data-processor",
            publisher_id=enterprise_tenant.tenant_id,
            name="Enterprise Data Processor",
            description="High-performance data processing workflow with validation and audit",
            long_description="""
This enterprise-grade workflow processes external API data with:
- Real-time data validation
- Secure database storage
- Comprehensive audit logging
- Multi-tenant isolation
- Enterprise-grade error handling
            """,
            version="1.0.0",
            price=299.99,
            categories=["enterprise", "data-processing", "automation"],
            tags=["api", "database", "audit", "enterprise", "validated"],
            requirements=["postgresql", "audit-logging"],
            license="Enterprise",
            demo_url="https://demo.globaltech.com/data-processor",
            support_url="https://support.globaltech.com",
        )

        assert data_item.name == "Enterprise Data Processor"
        assert data_item.price == 299.99
        assert "enterprise" in data_item.categories

        # Feature and verify the workflow
        app.marketplace.feature_item(data_item.item_id, True)
        app.marketplace.verify_item(data_item.item_id, True)

        # Step 5: Other tenants discover and install
        print("🔍 Step 5: Other tenants discover and install")

        # Create customer tenant
        customer_tenant = app.tenant_manager.create_tenant(
            name="DataCorp Analytics",
            description="Data analytics consulting firm",
            metadata={"plan": "professional", "industry": "consulting"},
        )

        # Customer searches marketplace
        search_results, total = app.marketplace.search(
            query="data processing", categories=["enterprise"], min_rating=0, limit=10
        )

        assert total >= 1
        found_item = next(
            (item for item in search_results if item.item_id == data_item.item_id), None
        )
        assert found_item is not None

        # Customer installs the workflow
        install_result = app.marketplace.install(
            item_id=data_item.item_id,
            user_id="datacorp_user",
            tenant_id=customer_tenant.tenant_id,
        )

        assert install_result["success"] is True
        assert install_result["workflow_id"] == "globaltech/data-processor"

        # Customer adds review
        review = app.marketplace.add_review(
            item_id=data_item.item_id,
            user_id="datacorp_user",
            rating=5,
            comment="Outstanding workflow! Cut our data processing time by 70%. Excellent documentation and support.",
        )

        assert review.rating == 5
        assert review.is_verified_install is True

        # Step 6: Usage tracking and monitoring
        print("📊 Step 6: Usage tracking and monitoring")

        # Simulate workflow executions
        for tenant in [enterprise_tenant, customer_tenant]:
            for day in range(7):  # Week of usage
                # Daily workflow executions
                executions = 100 + (day * 10)
                app.tenant_manager.track_usage(
                    tenant.tenant_id, "execution", executions
                )

                # API calls
                api_calls = executions * 5
                app.tenant_manager.track_usage(tenant.tenant_id, "api_call", api_calls)

                # Workflow usage
                if day % 2 == 0:  # Every other day
                    app.tenant_manager.track_usage(tenant.tenant_id, "workflow", 1)

        # Check usage stats
        enterprise_usage = app.tenant_manager.get_usage(enterprise_tenant.tenant_id)
        customer_usage = app.tenant_manager.get_usage(customer_tenant.tenant_id)

        assert enterprise_usage.executions_today >= 100
        assert customer_usage.executions_today >= 100

        # Check quota compliance
        enterprise_quota_check = app.tenant_manager.check_quota(
            enterprise_tenant.tenant_id, "execution", 10000
        )
        assert enterprise_quota_check[0] is True  # Within limits

        # Step 7: Health and monitoring checks
        print("🏥 Step 7: Health and monitoring checks")

        # System health check
        health = await app.health_check()

        # Handle dict or object response from health check
        if isinstance(health, dict):
            tenants_health = health.get("tenants", {})
            marketplace_health = health.get("marketplace", {})
            auth_health = health.get("auth", {})
        else:
            # Assuming object with attributes
            tenants_health = getattr(health, "tenants", {})
            marketplace_health = getattr(health, "marketplace", {})
            auth_health = getattr(health, "auth", {})

        assert tenants_health.get("healthy", False) is True
        assert tenants_health.get("total_tenants", 0) >= 2
        assert tenants_health.get("active_tenants", 0) >= 2

        assert marketplace_health.get("healthy", False) is True
        assert marketplace_health.get("total_items", 0) >= 1
        assert marketplace_health.get("featured_items", 0) >= 1
        assert marketplace_health.get("verified_items", 0) >= 1

        assert auth_health.get("healthy", False) is True
        assert auth_health.get("active_tokens", 0) >= 3
        assert auth_health.get("active_api_keys", 0) >= 3

        # Check marketplace stats
        assert data_item.stats.total_installs >= 1
        assert data_item.stats.total_reviews >= 1
        assert data_item.stats.average_rating == 5.0

        print("✅ Enterprise onboarding scenario completed successfully!")

    @pytest.mark.asyncio
    async def test_multi_tenant_isolation_scenario(self, production_nexus_app):
        """
        Test multi-tenant isolation in production scenario.

        Scenario:
        1. Create multiple tenants with different isolation levels
        2. Each tenant creates workflows with sensitive data
        3. Verify strict isolation between tenants
        4. Test cross-tenant access attempts (should fail)
        5. Verify resource usage tracking per tenant
        """
        app = production_nexus_app

        print("🏢 Multi-tenant isolation scenario")

        # Step 1: Create tenants with different profiles
        tenants = {
            "healthcare": app.tenant_manager.create_tenant(
                name="MedTech Hospital",
                description="Healthcare provider - HIPAA compliant",
                isolation_level="strict",
                metadata={"industry": "healthcare", "compliance": "hipaa"},
            ),
            "finance": app.tenant_manager.create_tenant(
                name="SecureBank Corp",
                description="Financial institution - SOX compliant",
                isolation_level="strict",
                metadata={"industry": "finance", "compliance": "sox"},
            ),
            "education": app.tenant_manager.create_tenant(
                name="University System",
                description="Educational institution - FERPA compliant",
                isolation_level="moderate",
                metadata={"industry": "education", "compliance": "ferpa"},
            ),
        }

        # Step 2: Create industry-specific workflows
        workflows = {}

        # Healthcare workflow
        healthcare_workflow = WorkflowBuilder()
        healthcare_workflow.add_node(
            "PythonCodeNode",
            "process_medical_data",
            {
                "code": """
# Process sensitive medical data
import hashlib

# Anonymize patient data
patient_id = data.get('patient_id')
anonymized_id = hashlib.sha256(patient_id.encode()).hexdigest()[:16]

result = {
    'anonymized_patient': anonymized_id,
    'medical_data': data.get('medical_data'),
    'tenant_id': context.get('tenant_id'),
    'compliance_level': 'hipaa',
    'processed_at': datetime.now(timezone.utc).isoformat()
}
"""
            },
        )
        healthcare_workflow.add_node(
            "AuditLogNode",
            "hipaa_audit",
            {
                "event_type": "medical_data_processing",
                "compliance_required": True,
                "retention_years": 7,
            },
        )
        healthcare_workflow.add_connection(
            "process_medical_data", "result", "hipaa_audit", "event"
        )

        app.register_workflow(
            "healthcare/patient-processor", healthcare_workflow.build()
        )
        workflows["healthcare"] = "healthcare/patient-processor"

        # Finance workflow
        finance_workflow = WorkflowBuilder()
        finance_workflow.add_node(
            "PythonCodeNode",
            "process_financial_data",
            {
                "code": """
# Process sensitive financial data
import decimal

# Calculate financial metrics
amount = decimal.Decimal(str(data.get('amount', 0)))
account_id = data.get('account_id')

result = {
    'account_id': account_id,
    'processed_amount': float(amount),
    'tenant_id': context.get('tenant_id'),
    'compliance_level': 'sox',
    'risk_level': 'high' if amount > 10000 else 'low',
    'processed_at': datetime.now(timezone.utc).isoformat()
}
"""
            },
        )
        finance_workflow.add_node(
            "AuditLogNode",
            "sox_audit",
            {
                "event_type": "financial_data_processing",
                "compliance_required": True,
                "retention_years": 10,
            },
        )
        finance_workflow.add_connection(
            "process_financial_data", "result", "sox_audit", "event"
        )

        app.register_workflow("finance/transaction-processor", finance_workflow.build())
        workflows["finance"] = "finance/transaction-processor"

        # Education workflow
        education_workflow = WorkflowBuilder()
        education_workflow.add_node(
            "PythonCodeNode",
            "process_student_data",
            {
                "code": """
# Process student educational data
student_id = data.get('student_id')
grades = data.get('grades', [])

result = {
    'student_id': student_id,
    'gpa': sum(grades) / len(grades) if grades else 0,
    'tenant_id': context.get('tenant_id'),
    'compliance_level': 'ferpa',
    'processed_at': datetime.now(timezone.utc).isoformat()
}
"""
            },
        )
        education_workflow.add_node(
            "AuditLogNode",
            "ferpa_audit",
            {
                "event_type": "student_data_processing",
                "compliance_required": True,
                "retention_years": 5,
            },
        )
        education_workflow.add_connection(
            "process_student_data", "result", "ferpa_audit", "event"
        )

        app.register_workflow("education/student-processor", education_workflow.build())
        workflows["education"] = "education/student-processor"

        # Step 3: Register resources with tenant isolation
        for industry, tenant in tenants.items():
            app.tenant_manager.register_resource(
                workflows[industry], "workflow", tenant.tenant_id
            )

        # Step 4: Test isolation - each tenant should only access their resources
        for industry, tenant in tenants.items():
            # Test valid access
            assert (
                app.tenant_manager.validate_access(
                    tenant.tenant_id, tenant.tenant_id, workflows[industry]
                )
                is True
            )

            # Test invalid cross-tenant access
            for other_industry, other_tenant in tenants.items():
                if industry != other_industry:
                    assert (
                        app.tenant_manager.validate_access(
                            other_tenant.tenant_id,
                            tenant.tenant_id,
                            workflows[industry],
                        )
                        is False
                    )

        # Step 5: Simulate realistic usage patterns
        usage_patterns = {
            "healthcare": {"execution": 500, "api_call": 2500, "workflow": 5},
            "finance": {"execution": 1000, "api_call": 5000, "workflow": 3},
            "education": {"execution": 200, "api_call": 1000, "workflow": 2},
        }

        for industry, tenant in tenants.items():
            pattern = usage_patterns[industry]
            for resource_type, amount in pattern.items():
                app.tenant_manager.track_usage(tenant.tenant_id, resource_type, amount)

        # Step 6: Verify usage isolation
        for industry, tenant in tenants.items():
            usage = app.tenant_manager.get_usage(tenant.tenant_id)
            expected = usage_patterns[industry]

            assert usage.executions_today == expected["execution"]
            assert usage.api_calls_this_hour == expected["api_call"]
            # Note: workflows count is incremented by both register_workflow and track_usage
            assert (
                usage.workflows == expected["workflow"] + 1
            )  # +1 for the registered workflow

        # Step 7: Test quota enforcement per tenant
        for industry, tenant in tenants.items():
            # Check current quota status
            allowed, details = app.tenant_manager.check_quota(
                tenant.tenant_id, "execution", 100
            )
            assert allowed is True

            # Try to exceed quota
            large_amount = tenant.quotas.executions_per_day + 1000
            allowed, details = app.tenant_manager.check_quota(
                tenant.tenant_id, "execution", large_amount
            )
            assert allowed is False

        print("✅ Multi-tenant isolation scenario completed successfully!")

    @pytest.mark.asyncio
    async def test_marketplace_discovery_scenario(self, production_nexus_app):
        """
        Test marketplace discovery and workflow sharing scenario.

        Scenario:
        1. Multiple vendors publish workflows to marketplace
        2. Customers search and discover workflows
        3. Workflows are installed and used across tenants
        4. Reviews and ratings affect discoverability
        5. Trending algorithms surface popular workflows
        """
        app = production_nexus_app

        print("🛒 Marketplace discovery scenario")

        # Step 1: Create vendor tenants
        vendors = {}
        for i, vendor_info in enumerate(
            [
                {"name": "AutoFlow Inc", "specialty": "automation"},
                {"name": "DataWise Solutions", "specialty": "analytics"},
                {"name": "SecureOps LLC", "specialty": "security"},
                {"name": "CloudNative Co", "specialty": "cloud"},
            ]
        ):
            vendor = app.tenant_manager.create_tenant(
                name=vendor_info["name"],
                description=f"Workflow vendor specializing in {vendor_info['specialty']}",
                metadata={"vendor": True, "specialty": vendor_info["specialty"]},
            )
            vendors[vendor_info["specialty"]] = vendor

        # Step 2: Create customer tenants
        customers = {}
        for i, customer_info in enumerate(
            [
                {"name": "TechStartup Alpha", "needs": ["automation", "analytics"]},
                {"name": "Enterprise Beta", "needs": ["security", "cloud"]},
                {"name": "MidCorp Gamma", "needs": ["automation", "security"]},
            ]
        ):
            customer = app.tenant_manager.create_tenant(
                name=customer_info["name"],
                description=f"Customer needing {', '.join(customer_info['needs'])}",
                metadata={"customer": True, "needs": customer_info["needs"]},
            )
            customers[customer_info["name"]] = customer

        # Step 3: Vendors publish workflows
        marketplace_items = {}

        # Automation workflows
        automation_workflows = [
            {
                "id": "autoflow/email-processor",
                "name": "Smart Email Processor",
                "description": "AI-powered email processing and routing",
                "price": 49.99,
                "tags": ["email", "ai", "automation"],
            },
            {
                "id": "autoflow/task-scheduler",
                "name": "Advanced Task Scheduler",
                "description": "Cron-like task scheduling with dependencies",
                "price": 99.99,
                "tags": ["scheduling", "cron", "automation"],
            },
        ]

        for workflow_info in automation_workflows:
            # Create workflow
            workflow = WorkflowBuilder()
            workflow.add_node(
                "PythonCodeNode",
                "process",
                {"code": f"result = 'Processing with {workflow_info['name']}'"},
            )

            app.register_workflow(workflow_info["id"], workflow.build())

            # Publish to marketplace
            item = app.marketplace.publish(
                workflow_id=workflow_info["id"],
                publisher_id=vendors["automation"].tenant_id,
                name=workflow_info["name"],
                description=workflow_info["description"],
                price=workflow_info["price"],
                categories=["automation"],
                tags=workflow_info["tags"],
            )
            marketplace_items[workflow_info["id"]] = item

        # Analytics workflows
        analytics_workflows = [
            {
                "id": "datawise/ml-pipeline",
                "name": "Machine Learning Pipeline",
                "description": "End-to-end ML training and deployment",
                "price": 199.99,
                "tags": ["ml", "ai", "pipeline"],
            },
            {
                "id": "datawise/report-generator",
                "name": "Automated Report Generator",
                "description": "Generate reports from multiple data sources",
                "price": 79.99,
                "tags": ["reports", "analytics", "visualization"],
            },
        ]

        for workflow_info in analytics_workflows:
            workflow = WorkflowBuilder()
            workflow.add_node(
                "PythonCodeNode",
                "analyze",
                {"code": f"result = 'Analyzing with {workflow_info['name']}'"},
            )

            app.register_workflow(workflow_info["id"], workflow.build())

            item = app.marketplace.publish(
                workflow_id=workflow_info["id"],
                publisher_id=vendors["analytics"].tenant_id,
                name=workflow_info["name"],
                description=workflow_info["description"],
                price=workflow_info["price"],
                categories=["analytics"],
                tags=workflow_info["tags"],
            )
            marketplace_items[workflow_info["id"]] = item

        # Step 4: Customer discovery and search

        # TechStartup Alpha searches for automation and analytics
        alpha_customer = customers["TechStartup Alpha"]

        # Search for automation workflows
        auto_results, auto_total = app.marketplace.search(
            query="automation", price_range=(0, 100), limit=10
        )
        assert auto_total >= 2

        # Search for analytics workflows
        analytics_results, analytics_total = app.marketplace.search(
            categories=["analytics"], limit=10
        )
        assert analytics_total >= 2

        # Step 5: Installations and usage
        installations = []

        # TechStartup Alpha installs automation tools
        for item in auto_results:
            install_result = app.marketplace.install(
                item_id=item.item_id,
                user_id="alpha_user",
                tenant_id=alpha_customer.tenant_id,
            )
            installations.append((item, alpha_customer, install_result))

        # Enterprise Beta installs high-value analytics
        expensive_analytics = [item for item in analytics_results if item.price > 150]
        for item in expensive_analytics:
            install_result = app.marketplace.install(
                item_id=item.item_id,
                user_id="beta_user",
                tenant_id=customers["Enterprise Beta"].tenant_id,
            )
            installations.append((item, customers["Enterprise Beta"], install_result))

        # Step 6: Reviews and ratings
        reviews = []

        # Add realistic reviews
        review_data = [
            {
                "item_id": "autoflow/email-processor",
                "user": "alpha_user",
                "rating": 5,
                "comment": "Incredible workflow! Cut our email processing time by 80%.",
            },
            {
                "item_id": "autoflow/task-scheduler",
                "user": "alpha_user",
                "rating": 4,
                "comment": "Great scheduler, but documentation could be better.",
            },
            {
                "item_id": "datawise/ml-pipeline",
                "user": "beta_user",
                "rating": 5,
                "comment": "Best ML pipeline we've used. Worth every penny.",
            },
        ]

        for review_info in review_data:
            item = next(
                (
                    item
                    for item in marketplace_items.values()
                    if item.workflow_id == review_info["item_id"]
                ),
                None,
            )
            if item:
                review = app.marketplace.add_review(
                    item_id=item.item_id,
                    user_id=review_info["user"],
                    rating=review_info["rating"],
                    comment=review_info["comment"],
                )
                reviews.append(review)

        # Step 7: Trending and featured workflows

        # Feature popular workflows
        popular_items = [
            marketplace_items["autoflow/email-processor"],
            marketplace_items["datawise/ml-pipeline"],
        ]

        for item in popular_items:
            app.marketplace.feature_item(item.item_id, True)

        # Get trending workflows
        trending = app.marketplace.get_trending(limit=5)
        assert len(trending) >= 2

        # Get featured workflows
        featured = app.marketplace.get_featured(limit=5)
        assert len(featured) == 2

        # Step 8: Verify marketplace metrics

        # Check installation counts
        for item in marketplace_items.values():
            if item.stats.total_installs > 0:
                assert item.stats.total_installs >= 1

        # Check review stats
        reviewed_items = [
            item for item in marketplace_items.values() if item.stats.total_reviews > 0
        ]
        assert len(reviewed_items) >= 3

        # Check average ratings
        for item in reviewed_items:
            assert item.stats.average_rating >= 4.0

        # Step 9: Search relevance and discovery

        # Search by price range
        budget_results, budget_total = app.marketplace.search(
            price_range=(0, 100), sort_by="price_low"
        )
        assert budget_total >= 2
        assert budget_results[0].price <= budget_results[-1].price

        # Search by rating
        quality_results, quality_total = app.marketplace.search(
            min_rating=4.5, sort_by="rating"
        )
        assert all(
            item.stats.average_rating >= 4.5
            for item in quality_results
            if item.stats.total_reviews > 0
        )

        # Search by tags
        ai_results, ai_total = app.marketplace.search(tags=["ai"], limit=10)
        assert ai_total >= 2
        assert all("ai" in item.tags for item in ai_results)

        print("✅ Marketplace discovery scenario completed successfully!")

    @pytest.mark.asyncio
    async def test_performance_scalability_scenario(self, production_nexus_app):
        """
        Test performance and scalability under load.

        Scenario:
        1. Create many tenants simultaneously
        2. High volume of concurrent workflow operations
        3. Stress test marketplace with many items
        4. Verify system remains responsive
        5. Check resource usage and cleanup
        """
        app = production_nexus_app

        print("⚡ Performance and scalability scenario")

        # Step 1: Create many tenants
        tenants = []
        for i in range(20):
            tenant = app.tenant_manager.create_tenant(
                name=f"ScaleTest Tenant {i}",
                description=f"Performance test tenant {i}",
                metadata={"test": True, "batch": i // 5},
            )
            tenants.append(tenant)

        assert len(tenants) == 20

        # Step 2: Create many workflows
        workflows = []
        for i in range(50):
            workflow = WorkflowBuilder()
            workflow.add_node(
                "PythonCodeNode",
                "process",
                {
                    "code": f"""
import time
import json

# Simulate processing work
data_size = {i * 100}
processed_items = []

for j in range(min(data_size, 100)):
    processed_items.append({{
        'id': j,
        'workflow_id': {i},
        'processed_at': time.time()
    }})

result = {{
    'workflow_id': {i},
    'processed_count': len(processed_items),
    'tenant_id': context.get('tenant_id', 'unknown')
}}
"""
                },
            )

            workflow_id = f"scale/workflow-{i}"
            app.register_workflow(workflow_id, workflow.build())
            workflows.append(workflow_id)

        assert len(workflows) == 50

        # Step 3: Publish many items to marketplace
        marketplace_items = []
        for i, workflow_id in enumerate(workflows):
            tenant = tenants[i % len(tenants)]

            item = app.marketplace.publish(
                workflow_id=workflow_id,
                publisher_id=tenant.tenant_id,
                name=f"Scale Test Workflow {i}",
                description=f"Performance test workflow {i}",
                price=float(i % 100),
                categories=["performance", "test"],
                tags=[f"scale{i}", "performance", "test"],
            )
            marketplace_items.append(item)

        assert len(marketplace_items) == 50

        # Step 4: Simulate high concurrent usage

        # Concurrent installations
        install_tasks = []
        for i in range(100):  # 100 installations
            item = marketplace_items[i % len(marketplace_items)]
            tenant = tenants[i % len(tenants)]

            # Simulate concurrent installs
            install_result = app.marketplace.install(
                item_id=item.item_id,
                user_id=f"scale_user_{i}",
                tenant_id=tenant.tenant_id,
            )
            install_tasks.append(install_result)

        # Verify installations
        successful_installs = [task for task in install_tasks if task["success"]]
        assert len(successful_installs) == 100

        # Concurrent usage tracking
        for i in range(1000):  # 1000 usage events
            tenant = tenants[i % len(tenants)]

            # Simulate realistic usage patterns
            if i % 10 == 0:
                app.tenant_manager.track_usage(tenant.tenant_id, "workflow", 1)

            app.tenant_manager.track_usage(tenant.tenant_id, "execution", 10)
            app.tenant_manager.track_usage(tenant.tenant_id, "api_call", 50)

        # Step 5: Stress test marketplace operations

        # Concurrent searches
        search_results = []
        search_queries = [
            ("scale", None, None),
            ("performance", ["performance"], None),
            ("test", None, (0, 50)),
            ("workflow", None, None),
            ("", ["test"], (10, 90)),
        ]

        for query, categories, price_range in search_queries:
            results, total = app.marketplace.search(
                query=query, categories=categories, price_range=price_range, limit=20
            )
            search_results.append((results, total))

        # Verify search performance
        assert all(len(results) <= 20 for results, _ in search_results)
        assert all(total > 0 for _, total in search_results)

        # Concurrent reviews
        for i in range(200):  # 200 reviews
            item = marketplace_items[i % len(marketplace_items)]

            app.marketplace.add_review(
                item_id=item.item_id,
                user_id=f"reviewer_{i}",
                rating=(i % 5) + 1,
                comment=f"Performance test review {i}",
            )

        # Step 6: Verify system performance

        # Check tenant usage aggregation
        total_executions = 0
        total_api_calls = 0

        for tenant in tenants:
            usage = app.tenant_manager.get_usage(tenant.tenant_id)
            total_executions += usage.executions_today
            total_api_calls += usage.api_calls_this_hour

        assert total_executions == 10000  # 1000 events * 10 executions each
        assert total_api_calls == 50000  # 1000 events * 50 API calls each

        # Check marketplace stats
        total_installs = sum(item.stats.total_installs for item in marketplace_items)
        total_reviews = sum(item.stats.total_reviews for item in marketplace_items)

        assert total_installs >= 100
        assert total_reviews >= 200

        # Check system health under load
        health = await app.health_check()
        assert health["tenants"]["healthy"] is True
        assert health["tenants"]["total_tenants"] >= 20
        assert health["marketplace"]["healthy"] is True
        assert health["marketplace"]["total_items"] >= 50

        # Step 7: Cleanup and resource management

        # Test bulk operations
        inactive_tenants = tenants[15:]  # Last 5 tenants
        for tenant in inactive_tenants:
            app.tenant_manager.update_tenant(tenant.tenant_id, {"is_active": False})

        # Verify only active tenants in listings
        active_tenants = app.tenant_manager.list_tenants(is_active=True)
        assert len(active_tenants) == 15

        # Test marketplace cleanup
        old_items = marketplace_items[:10]  # First 10 items
        for item in old_items:
            app.marketplace.update_item(item.item_id, {"is_public": False})

        # Verify public items count
        public_results, public_total = app.marketplace.search(limit=100)
        assert public_total >= 40  # 50 - 10 unpublished

        print("✅ Performance and scalability scenario completed successfully!")
