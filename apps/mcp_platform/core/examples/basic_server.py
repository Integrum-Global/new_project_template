"""
Basic MCP Server Example

This example demonstrates how to create and manage a basic MCP server.
"""

import asyncio
import logging

from apps.mcp_platform.core.config.settings import MCPConfig
from apps.mcp_platform.core.core.gateway import MCPGateway

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Run basic MCP server example."""

    # Initialize configuration
    config = MCPConfig()

    # Create MCP gateway
    gateway = MCPGateway(
        config={"database_url": config.DATABASE_URL, "enable_monitoring": True}
    )

    # Initialize gateway
    await gateway.initialize()

    try:
        # Example 1: Register a filesystem MCP server
        logger.info("=== Registering Filesystem Server ===")

        fs_config = {
            "name": "filesystem-demo",
            "transport": "stdio",
            "command": "npx",
            "args": ["@modelcontextprotocol/server-filesystem", "/tmp"],
            "auto_start": True,
            "tags": ["demo", "filesystem"],
            "description": "Demo filesystem MCP server",
        }

        # Register the server
        server_id = await gateway.register_server(fs_config, user_id="demo-user")
        logger.info(f"Registered server: {server_id}")

        # Example 2: Start the server (if not auto-started)
        logger.info("=== Starting Server ===")
        start_result = await gateway.start_server(server_id, user_id="demo-user")
        logger.info(f"Server start result: {start_result}")

        # Example 3: Discover available tools
        logger.info("=== Discovering Tools ===")
        tools = await gateway.discover_tools(server_id, user_id="demo-user")
        logger.info(f"Discovered {len(tools)} tools:")
        for tool in tools[:5]:  # Show first 5 tools
            logger.info(f"  - {tool.name}: {tool.description}")

        # Example 4: Execute a tool
        if tools:
            logger.info("=== Executing Tool ===")
            first_tool = tools[0]

            # Example parameters (adjust based on actual tool)
            tool_params = {"path": "/tmp"}

            result = await gateway.execute_tool(
                server_id, first_tool.name, tool_params, user_id="demo-user"
            )
            logger.info(f"Tool execution result: {result}")

        # Example 5: Check server health
        logger.info("=== Checking Server Health ===")
        status = await gateway.get_server_status(server_id, user_id="demo-user")
        logger.info(f"Server status: {status}")

        # Example 6: List all servers
        logger.info("=== Listing All Servers ===")
        servers = await gateway.list_servers(user_id="demo-user")
        for server in servers:
            logger.info(f"  - {server.name} ({server.id}): {server.status.value}")

        # Keep server running for a bit
        logger.info("Server is running. Press Ctrl+C to stop...")
        await asyncio.sleep(60)

    except KeyboardInterrupt:
        logger.info("Stopping example...")

    finally:
        # Example 7: Stop the server
        logger.info("=== Stopping Server ===")
        stop_result = await gateway.stop_server(server_id, user_id="demo-user")
        logger.info(f"Server stop result: {stop_result}")

        # Shutdown gateway
        await gateway.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
