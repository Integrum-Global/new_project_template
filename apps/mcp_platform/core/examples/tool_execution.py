"""
Tool Execution Example

This example demonstrates various tool execution patterns including
single execution, batch execution, and caching.
"""

import asyncio
import logging

from apps.mcp_platform.core.core.gateway import MCPGateway
from apps.mcp_platform.core.nodes.tool_executor_node import ToolExecutorNode
from kailash.runtime.local import LocalRuntime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Run tool execution examples."""

    # Initialize components
    gateway = MCPGateway()
    runtime = LocalRuntime()

    await gateway.initialize()

    try:
        # First, set up a test server
        server_config = {
            "name": "test-tools-server",
            "transport": "stdio",
            "command": "python",
            "args": ["-m", "example_mcp_server"],  # Your MCP server module
            "auto_start": True,
        }

        server_id = await gateway.register_server(server_config, user_id="demo-user")
        await gateway.start_server(server_id, user_id="demo-user")

        # Discover tools
        tools = await gateway.discover_tools(server_id, user_id="demo-user")
        logger.info(f"Available tools: {[t.name for t in tools]}")

        if not tools:
            logger.warning("No tools discovered. Make sure your MCP server is running.")
            return

        # Example 1: Simple tool execution
        logger.info("=== Example 1: Simple Tool Execution ===")

        tool_name = tools[0].name
        result = await gateway.execute_tool(
            server_id, tool_name, {"input": "test data"}, user_id="demo-user"
        )
        logger.info(f"Result: {result}")

        # Example 2: Tool execution with custom node
        logger.info("=== Example 2: Using Tool Executor Node ===")

        executor_node = ToolExecutorNode(
            {"timeout": 30, "retry_attempts": 3, "cache_results": True}
        )

        # Get MCP client from gateway
        connection = gateway._active_connections.get(server_id)
        if connection:
            node_result = await runtime.execute_node_async(
                executor_node,
                {
                    "operation": "execute",
                    "mcp_client": connection.client,
                    "tool_name": tool_name,
                    "parameters": {"input": "cached test data"},
                },
            )
            logger.info(f"Node result: {node_result}")

            # Execute again to test caching
            node_result2 = await runtime.execute_node_async(
                executor_node,
                {
                    "operation": "execute",
                    "mcp_client": connection.client,
                    "tool_name": tool_name,
                    "parameters": {"input": "cached test data"},
                },
            )
            logger.info(f"Cached result: {node_result2}")

        # Example 3: Batch tool execution
        logger.info("=== Example 3: Batch Tool Execution ===")

        if len(tools) >= 3:
            batch_executions = [
                {
                    "server_id": server_id,
                    "tool_name": tools[0].name,
                    "parameters": {"input": f"batch test {i}"},
                }
                for i in range(3)
            ]

            # Using gateway batch execution
            batch_results = await gateway.service.batch_execute_tools(batch_executions)
            logger.info(f"Batch results: {len(batch_results)} executions completed")

        # Example 4: Tool validation
        logger.info("=== Example 4: Tool Parameter Validation ===")

        if connection:
            validation_result = await runtime.execute_node_async(
                executor_node,
                {
                    "operation": "validate",
                    "tool_name": tool_name,
                    "parameters": {"invalid_param": "test", "another_param": 123},
                    "tool_schema": tools[0].input_schema if tools else {},
                },
            )
            logger.info(f"Validation result: {validation_result}")

        # Example 5: Parallel batch execution with error handling
        logger.info("=== Example 5: Parallel Batch with Error Handling ===")

        if connection and len(tools) >= 2:
            mixed_executions = [
                {"tool_name": tools[0].name, "parameters": {"input": "valid data"}},
                {
                    "tool_name": "non_existent_tool",  # This will fail
                    "parameters": {"input": "test"},
                },
                {
                    "tool_name": tools[1].name if len(tools) > 1 else tools[0].name,
                    "parameters": {"input": "more data"},
                },
            ]

            batch_result = await runtime.execute_node_async(
                executor_node,
                {
                    "operation": "batch_execute",
                    "mcp_client": connection.client,
                    "executions": mixed_executions,
                    "parallel": True,
                },
            )

            logger.info("Batch execution summary:")
            logger.info(f"  Total: {batch_result['total']}")
            logger.info(f"  Successful: {batch_result['successful']}")
            logger.info(f"  Failed: {batch_result['failed']}")

        # Example 6: Tool execution with timeout
        logger.info("=== Example 6: Tool Execution with Timeout ===")

        timeout_result = await gateway.execute_tool(
            server_id,
            tool_name,
            {"input": "timeout test", "delay": 5},  # Assuming tool supports delay
            user_id="demo-user",
            execution_options={"timeout": 2},  # 2 second timeout
        )
        logger.info(f"Timeout test result: {timeout_result}")

    finally:
        # Cleanup
        logger.info("Cleaning up...")
        await gateway.stop_server(server_id, user_id="demo-user")
        await gateway.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
