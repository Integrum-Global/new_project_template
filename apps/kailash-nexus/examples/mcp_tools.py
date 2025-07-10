#!/usr/bin/env python3
"""
Nexus MCP Tools Example

Demonstrates MCP channel with enterprise tools and marketplace integration.
"""

import asyncio

from kailash_nexus import create_application

from kailash.workflow.builder import WorkflowBuilder


async def main():
    """Run MCP example."""

    # Create application
    app = create_application(
        name="Nexus MCP Demo",
        channels={
            "mcp": {"enabled": True, "port": 8765},
            "api": {"enabled": False},
            "cli": {"enabled": False},
        },
        features={
            "marketplace": {"enabled": True},
            "authentication": {"enabled": True},
            "multi_tenant": {"enabled": True},
        },
    )

    await app.start()

    # Populate marketplace with some items
    for i in range(5):
        workflow = WorkflowBuilder()
        workflow.add_node(
            "PythonCodeNode", "process", {"code": f"result = 'Workflow {i} executed'"}
        )

        app.register_workflow(f"demo/workflow-{i}", workflow.build())

        app.marketplace.publish(
            workflow_id=f"demo/workflow-{i}",
            publisher_id="demo_publisher",
            name=f"Demo Workflow {i}",
            description=f"Example workflow number {i}",
            categories=["demo", "example"],
            tags=["test", f"v{i}"],
            price=0.0,
        )

    # Feature some items
    items, _ = app.marketplace.search(limit=3)
    for item in items[:2]:
        app.marketplace.feature_item(item.item_id, True)

    # Get MCP channel wrapper
    mcp = app.mcp_channel

    # Register custom workflow tool
    data_processor = WorkflowBuilder()
    data_processor.add_node(
        "PythonCodeNode",
        "analyze",
        {
            "code": """
import json
data = json.loads(input_data)
result = {
    'total_items': len(data.get('items', [])),
    'summary': f"Processed {len(data.get('items', []))} items"
}
"""
        },
    )

    mcp.register_workflow_tool(
        "analyze_data",
        data_processor.build(),
        {
            "description": "Analyze JSON data",
            "parameters": {
                "input_data": {"type": "string", "description": "JSON data to analyze"}
            },
        },
    )

    print("Nexus MCP Demo")
    print("=" * 50)

    # List available tools
    tools = mcp.get_tools()
    print("\nAvailable MCP tools:")
    for tool in tools:
        print(f"  - {tool['name']} v{tool['version']}: {tool['description']}")

    # Simulate tool calls
    print("\nSimulating tool usage:")
    print("-" * 50)

    # Search marketplace
    print("\n1. Searching marketplace...")
    search_result = await mcp._marketplace_search_tool({"query": "demo", "limit": 3})
    print(f"Found {len(search_result['results'])} items")
    for item in search_result["results"]:
        print(
            f"  - {item['name']} ({item['rating']} stars, {item['installs']} installs)"
        )

    # Get tenant info
    print("\n2. Getting tenant info...")
    mcp.mcp_channel.session_data["tenant_id"] = "demo_tenant"
    tenant_result = await mcp._tenant_info_tool({})
    print(f"Current tenant: {tenant_result.get('error', 'Demo Tenant')}")

    # Get tool usage
    print("\n3. Tool usage statistics:")
    usage = mcp.get_tool_usage()
    print(f"  Total tools: {usage['total_tools']}")
    print(f"  Total calls: {usage['total_calls']}")
    print(f"  Success rate: {usage['success_rate']:.1%}")

    # Show featured items
    print("\n4. Featured marketplace items:")
    featured = app.marketplace.get_featured(limit=3)
    for item in featured:
        print(f"  - ⭐ {item.name}")

    print("\n✅ MCP server running on port 8765")
    print("Connect with an MCP client to interact with tools")

    # Keep running
    try:
        await asyncio.sleep(60)
    except KeyboardInterrupt:
        pass

    await app.stop()


if __name__ == "__main__":
    asyncio.run(main())
