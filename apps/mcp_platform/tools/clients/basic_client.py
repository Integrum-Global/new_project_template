#!/usr/bin/env python3
"""Basic MCP Client - Simple client to interact with MCP server."""

import asyncio
import logging
from typing import Any, Dict

from kailash.mcp_server import MCPClient
from kailash.mcp_server.errors import (
    ConnectionError,
    ToolExecutionError,
    ToolNotFoundError,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class BasicMCPClient:
    """Basic MCP client for interacting with MCP servers."""

    def __init__(
        self, name: str = "basic-client", server_url: str = "mcp://localhost:8080"
    ):
        self.name = name
        self.server_url = server_url
        self.client = MCPClient(name)
        self.connected = False

    async def connect(self):
        """Connect to MCP server."""
        try:
            await self.client.connect(self.server_url)
            self.connected = True
            logger.info(f"Connected to {self.server_url}")

            # Discover available tools
            tools = await self.client.list_tools()
            logger.info(f"Available tools: {list(tools.keys())}")

        except ConnectionError as e:
            logger.error(f"Failed to connect: {e}")
            raise

    async def disconnect(self):
        """Disconnect from MCP server."""
        if self.connected:
            await self.client.disconnect()
            self.connected = False
            logger.info("Disconnected from server")

    async def call_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool on the MCP server."""
        if not self.connected:
            raise ConnectionError("Not connected to server")

        try:
            result = await self.client.call_tool(tool_name, params)
            return result
        except ToolNotFoundError:
            logger.error(f"Tool '{tool_name}' not found on server")
            raise
        except ToolExecutionError as e:
            logger.error(f"Tool execution failed: {e}")
            raise

    async def demo_math_tools(self):
        """Demonstrate math tools."""
        logger.info("\n=== Math Tools Demo ===")

        # Basic arithmetic
        result = await self.call_tool("add", {"a": 10, "b": 5})
        logger.info(f"10 + 5 = {result['result']}")

        result = await self.call_tool("multiply", {"a": 7, "b": 8})
        logger.info(f"7 * 8 = {result['result']}")

        # Calculate with operation
        if "calculate" in await self.client.list_tools():
            result = await self.call_tool(
                "calculate", {"a": 16, "b": 4, "operation": "divide"}
            )
            logger.info(f"16 / 4 = {result['result']}")

            # Factorial
            result = await self.call_tool("factorial", {"n": 5})
            logger.info(f"5! = {result['result']}")

            # Fibonacci
            result = await self.call_tool("fibonacci", {"n": 10})
            logger.info(f"First 10 Fibonacci numbers: {result['sequence']}")

    async def demo_string_tools(self):
        """Demonstrate string tools."""
        logger.info("\n=== String Tools Demo ===")

        text = "Hello, MCP World!"

        result = await self.call_tool("uppercase", {"text": text})
        logger.info(f"Uppercase: {result['result']}")

        result = await self.call_tool("lowercase", {"text": text})
        logger.info(f"Lowercase: {result['result']}")

        result = await self.call_tool("reverse", {"text": text})
        logger.info(f"Reversed: {result['result']}")

    async def demo_utility_tools(self):
        """Demonstrate utility tools."""
        logger.info("\n=== Utility Tools Demo ===")

        # Echo
        result = await self.call_tool("echo", {"message": "Testing MCP!"})
        logger.info(f"Echo response: {result}")

        # Server info
        result = await self.call_tool("get_info", {})
        logger.info(f"Server info: {result}")

        # Advanced tools (if available)
        tools = await self.client.list_tools()

        if "datetime_now" in tools:
            result = await self.call_tool(
                "datetime_now", {"format": "%Y-%m-%d %H:%M:%S"}
            )
            logger.info(f"Current time: {result['datetime']}")

        if "uuid_generate" in tools:
            result = await self.call_tool("uuid_generate", {"version": 4})
            logger.info(f"Generated UUID: {result['uuid']}")

        if "hash_data" in tools:
            result = await self.call_tool(
                "hash_data", {"data": "Hello MCP", "algorithm": "sha256"}
            )
            logger.info(f"SHA256 hash: {result['hash']}")

    async def demo_resources(self):
        """Demonstrate resource access."""
        logger.info("\n=== Resources Demo ===")

        try:
            # Get server configuration resource
            config = await self.client.get_resource("server_config")
            logger.info(f"Server configuration: {config}")

            # Get other resources
            resources = await self.client.list_resources()
            logger.info(f"Available resources: {list(resources.keys())}")

            for resource_name in resources:
                try:
                    data = await self.client.get_resource(resource_name)
                    logger.info(f"Resource '{resource_name}': {data}")
                except Exception as e:
                    logger.error(f"Failed to get resource '{resource_name}': {e}")

        except Exception as e:
            logger.error(f"Resource access failed: {e}")


async def interactive_mode(client: BasicMCPClient):
    """Run client in interactive mode."""
    logger.info("\n=== Interactive Mode ===")
    logger.info("Type 'help' for available commands, 'quit' to exit")

    while True:
        try:
            command = input("\nMCP> ").strip()

            if command == "quit":
                break
            elif command == "help":
                print("Available commands:")
                print("  tools         - List available tools")
                print("  resources     - List available resources")
                print("  call <tool>   - Call a tool (will prompt for parameters)")
                print("  get <resource> - Get a resource")
                print("  quit          - Exit")
            elif command == "tools":
                tools = await client.client.list_tools()
                for name, info in tools.items():
                    print(f"  {name}: {info.get('description', 'No description')}")
            elif command == "resources":
                resources = await client.client.list_resources()
                for name, info in resources.items():
                    print(f"  {name}: {info.get('description', 'No description')}")
            elif command.startswith("call "):
                tool_name = command[5:].strip()
                tools = await client.client.list_tools()

                if tool_name not in tools:
                    print(f"Unknown tool: {tool_name}")
                    continue

                # Get parameters
                tool_info = tools[tool_name]
                params = {}

                if "parameters" in tool_info:
                    print(f"Parameters for {tool_name}:")
                    for param_name, param_info in tool_info["parameters"].items():
                        value = input(f"  {param_name}: ")
                        # Try to parse as JSON, fallback to string
                        try:
                            import json

                            params[param_name] = json.loads(value)
                        except:
                            params[param_name] = value

                try:
                    result = await client.call_tool(tool_name, params)
                    print(f"Result: {result}")
                except Exception as e:
                    print(f"Error: {e}")

            elif command.startswith("get "):
                resource_name = command[4:].strip()
                try:
                    data = await client.client.get_resource(resource_name)
                    print(f"Resource data: {data}")
                except Exception as e:
                    print(f"Error: {e}")
            else:
                print(f"Unknown command: {command}")

        except KeyboardInterrupt:
            break
        except Exception as e:
            logger.error(f"Error: {e}")


async def main():
    """Run the basic MCP client demo."""
    import sys

    # Get server URL from command line or use default
    server_url = sys.argv[1] if len(sys.argv) > 1 else "mcp://localhost:8080"

    client = BasicMCPClient(server_url=server_url)

    try:
        # Connect to server
        await client.connect()

        # Run demos
        await client.demo_math_tools()
        await client.demo_string_tools()
        await client.demo_utility_tools()
        await client.demo_resources()

        # Interactive mode
        await interactive_mode(client)

    except Exception as e:
        logger.error(f"Client error: {e}")
    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
