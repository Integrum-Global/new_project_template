#!/usr/bin/env python3
"""
Basic MCP Platform Integration Example

This example demonstrates how to use the consolidated MCP platform
for basic server management and tool execution.
"""

from apps.mcp_platform import BasicMCPServer, MCPRegistry, MCPService
from kailash import create_gateway


# Example 1: Basic MCP Server Setup
def basic_server_example():
    """Set up a basic MCP server with tools."""

    # Create a basic MCP server
    server = BasicMCPServer(
        name="math-tools", description="Basic mathematical operations"
    )

    # Register tools
    @server.tool("add")
    async def add_numbers(a: float, b: float) -> dict:
        """Add two numbers."""
        return {"result": a + b}

    @server.tool("multiply")
    async def multiply_numbers(a: float, b: float) -> dict:
        """Multiply two numbers."""
        return {"result": a * b}

    return server


# Example 2: MCP Registry Usage
def registry_example():
    """Use MCP Registry to manage multiple servers."""

    # Create registry
    registry = MCPRegistry()

    # Register servers
    math_server = basic_server_example()
    registry.register_server("math", math_server)

    # Create another server
    text_server = BasicMCPServer(
        name="text-tools", description="Text manipulation tools"
    )

    @text_server.tool("uppercase")
    async def to_uppercase(text: str) -> dict:
        """Convert text to uppercase."""
        return {"result": text.upper()}

    registry.register_server("text", text_server)

    # List all registered servers
    servers = registry.list_servers()
    print("Registered servers:", servers)

    return registry


# Example 3: Gateway Integration
async def gateway_integration_example():
    """Integrate MCP servers with Kailash gateway."""

    # Create gateway with MCP support
    gateway = await create_gateway(
        title="MCP Platform Demo",
        enable_mcp=True,
        mcp_config={"registry": registry_example(), "auto_discover": True},
    )

    # The gateway now exposes MCP servers through REST API
    # Available endpoints:
    # - GET /mcp/servers - List all servers
    # - GET /mcp/servers/{server_id}/tools - List server tools
    # - POST /mcp/servers/{server_id}/tools/{tool_name} - Execute tool

    return gateway


# Example 4: Direct Tool Execution
async def direct_execution_example():
    """Execute MCP tools directly."""

    # Create a service for direct execution
    service = MCPService()

    # Register a server
    server = basic_server_example()
    service.add_server(server)

    # Execute tools
    result1 = await service.execute_tool("math-tools", "add", {"a": 5, "b": 3})
    print(f"5 + 3 = {result1['result']}")

    result2 = await service.execute_tool("math-tools", "multiply", {"a": 4, "b": 7})
    print(f"4 × 7 = {result2['result']}")

    return service


if __name__ == "__main__":
    import asyncio

    # Run examples
    print("MCP Platform Basic Integration Examples")
    print("=" * 50)

    # Example 1: Basic server
    print("\n1. Basic Server:")
    server = basic_server_example()
    print(f"   Created server: {server.name}")
    print(f"   Tools: {list(server.list_tools().keys())}")

    # Example 2: Registry
    print("\n2. Registry:")
    registry = registry_example()

    # Example 3: Direct execution
    print("\n3. Direct Execution:")
    asyncio.run(direct_execution_example())

    print("\n✓ Examples completed!")
