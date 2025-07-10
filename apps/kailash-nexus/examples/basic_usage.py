#!/usr/bin/env python3
"""
Basic Nexus Application Usage Example

Demonstrates:
- Creating a Nexus application
- Registering workflows
- Publishing to marketplace
- Multi-tenant operations
- Authentication
"""

import asyncio
import logging

from kailash_nexus import create_application

from kailash.nodes.data.python_code import PythonCodeNode
from kailash.workflow.builder import WorkflowBuilder

logging.basicConfig(level=logging.INFO)


async def main():
    """Demonstrate Nexus application usage."""

    # 1. Create application with enterprise features
    app = create_application(
        name="Enterprise Nexus Demo",
        description="Demonstration of Nexus enterprise features",
        features={
            "authentication": {
                "enabled": True,
                "providers": [
                    {"type": "local", "name": "Local Auth"},
                    {"type": "ldap", "name": "Corporate LDAP"},
                ],
            },
            "multi_tenant": {"enabled": True, "isolation": "strict"},
            "marketplace": {"enabled": True},
        },
    )

    # 2. Start the application
    await app.start()
    print("✅ Nexus application started")

    # 3. Create a tenant
    tenant = app.tenant_manager.create_tenant(
        name="Acme Corp",
        description="Enterprise customer",
        quotas={"workflows": 1000, "executions_per_day": 50000},
    )
    print(f"✅ Created tenant: {tenant.name} ({tenant.tenant_id})")

    # 4. Create and register a workflow
    workflow = WorkflowBuilder()
    workflow.add_node(
        "HTTPRequestNode",
        "fetch_data",
        {"url": "https://api.example.com/data", "method": "GET"},
    )

    # Use .from_function() for SDK compliance
    def process_data(data):
        """Process fetched data."""
        from datetime import datetime

        return {
            "processed": True,
            "items": len(data.get("items", [])),
            "timestamp": datetime.utcnow().isoformat(),
        }

    workflow.add_node(
        "PythonCodeNode", "process_data", PythonCodeNode.from_function(process_data)
    )
    workflow.add_connection("fetch_data", "response", "process_data", "data")

    # Register workflow
    app.register_workflow("custom/data-processor", workflow.build())
    print("✅ Registered workflow: custom/data-processor")

    # 5. Publish to marketplace
    item = app.marketplace.publish(
        workflow_id="custom/data-processor",
        publisher_id=tenant.tenant_id,
        name="Data Processor Pro",
        description="Advanced data processing workflow",
        price=0.0,  # Free
        categories=["data", "automation"],
        tags=["api", "processing", "enterprise"],
    )
    print(f"✅ Published to marketplace: {item.name} ({item.item_id})")

    # 6. Authenticate a user
    auth_token = await app.auth_manager.authenticate(
        {"username": "demo_user", "password": "demo_pass"}
    )
    if auth_token:
        print(f"✅ User authenticated: {auth_token.user_id}")

    # 7. Search marketplace
    results, total = app.marketplace.search(query="data", categories=["automation"])
    print(f"✅ Found {total} marketplace items")

    # 8. Install from marketplace
    if results:
        install_result = app.marketplace.install(
            item_id=results[0].item_id, user_id="demo_user", tenant_id=tenant.tenant_id
        )
        print(f"✅ Installed: {install_result['workflow_id']}")

    # 9. Add a review
    review = app.marketplace.add_review(
        item_id=item.item_id,
        user_id="demo_user",
        rating=5,
        comment="Excellent workflow! Saved us hours of work.",
    )
    print(f"✅ Added review: {review.rating} stars")

    # 10. Check health
    health = await app.health_check()
    print(f"✅ Health check: {health['status']}")

    # 11. Check tenant usage
    usage = app.tenant_manager.get_usage(tenant.tenant_id)
    print(f"✅ Tenant usage - Workflows: {usage.workflows}")

    # Keep running for a bit to demonstrate
    print("\n🚀 Application running... Press Ctrl+C to stop")
    try:
        await asyncio.sleep(60)
    except KeyboardInterrupt:
        pass

    # Stop application
    await app.stop()
    print("✅ Application stopped")


if __name__ == "__main__":
    asyncio.run(main())
