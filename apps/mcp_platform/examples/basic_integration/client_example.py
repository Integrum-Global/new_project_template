"""MCP client example for connecting to Kailash MCP servers.

This example demonstrates how to create MCP clients that can discover and
interact with Kailash workflow servers, enabling distributed AI processing.

Features demonstrated:
- MCP client configuration and connection
- Service discovery for Kailash servers
- Tool execution with authentication
- Resource access and configuration
- Error handling and retry logic
"""

import asyncio
import json
import logging
import time
from typing import Any, Dict, List, Optional

from kailash.mcp_server import MCPClient, discover_mcp_servers, get_mcp_client
from kailash.mcp_server.auth import APIKeyAuth

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class KailashMCPClient:
    """Client for interacting with Kailash MCP servers."""

    def __init__(self, api_key: str = "user_key_456"):
        """Initialize the MCP client with authentication."""
        self.api_key = api_key
        self.clients: Dict[str, MCPClient] = {}
        self.discovered_servers: List[Dict[str, Any]] = []

    async def discover_kailash_servers(self) -> List[Dict[str, Any]]:
        """Discover available Kailash MCP servers."""
        try:
            # Discover servers with workflow capabilities
            servers = await discover_mcp_servers(capability="workflows")

            # Filter for Kailash servers (by convention or metadata)
            kailash_servers = []
            for server in servers:
                server_info = {
                    "name": server.name,
                    "transport": server.transport,
                    "capabilities": server.capabilities,
                    "metadata": getattr(server, "metadata", {}),
                }

                # Check if it's a Kailash server
                if (
                    "kailash" in server.name.lower()
                    or "workflows" in server.capabilities
                ):
                    kailash_servers.append(server_info)

            self.discovered_servers = kailash_servers
            logger.info(f"Discovered {len(kailash_servers)} Kailash servers")
            return kailash_servers

        except Exception as e:
            logger.error(f"Server discovery failed: {e}")
            return []

    async def connect_to_server(
        self, server_config: Dict[str, Any]
    ) -> Optional[MCPClient]:
        """Connect to a specific MCP server."""
        try:
            # Create client configuration with authentication
            client_config = {
                "name": f"client_{server_config['name']}",
                "transport": server_config.get("transport", "http"),
                "url": server_config.get("url", "http://localhost:8080"),
                "auth": {"type": "api_key", "key": self.api_key, "header": "X-API-Key"},
            }

            # Create and connect client
            client = MCPClient(client_config)
            await client.connect()

            self.clients[server_config["name"]] = client
            logger.info(f"Connected to server: {server_config['name']}")
            return client

        except Exception as e:
            logger.error(f"Failed to connect to {server_config['name']}: {e}")
            return None

    async def execute_text_analysis(
        self,
        text: str,
        analysis_type: str = "sentiment",
        server_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Execute text analysis on a Kailash server."""
        try:
            # Get client for the server
            if server_name and server_name in self.clients:
                client = self.clients[server_name]
            else:
                # Use any available client with workflow capability
                client = await self._get_workflow_client()
                if not client:
                    return {"error": "No workflow servers available"}

            # Execute text analysis tool
            result = await client.call_tool(
                "execute_text_analysis", {"text": text, "analysis_type": analysis_type}
            )

            logger.info(f"Text analysis completed: {analysis_type}")
            return result

        except Exception as e:
            logger.error(f"Text analysis failed: {e}")
            return {"error": str(e), "text": text, "analysis_type": analysis_type}

    async def process_data_file(
        self,
        file_path: str,
        operation: str = "analyze",
        server_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Process a data file using Kailash workflows."""
        try:
            # Get client for the server
            if server_name and server_name in self.clients:
                client = self.clients[server_name]
            else:
                client = await self._get_workflow_client()
                if not client:
                    return {"error": "No workflow servers available"}

            # Execute data processing tool
            result = await client.call_tool(
                "process_data_file", {"file_path": file_path, "operation": operation}
            )

            logger.info(f"Data processing completed: {operation}")
            return result

        except Exception as e:
            logger.error(f"Data processing failed: {e}")
            return {"error": str(e), "file_path": file_path, "operation": operation}

    async def get_available_workflows(
        self, server_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get list of available workflows from a server."""
        try:
            # Get client for the server
            if server_name and server_name in self.clients:
                client = self.clients[server_name]
            else:
                client = await self._get_workflow_client()
                if not client:
                    return {"error": "No workflow servers available"}

            # Get workflow list
            result = await client.call_tool("list_available_workflows")
            return result

        except Exception as e:
            logger.error(f"Failed to get workflows: {e}")
            return {"error": str(e)}

    async def get_server_configuration(
        self, server_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get server configuration and settings."""
        try:
            # Get client for the server
            if server_name and server_name in self.clients:
                client = self.clients[server_name]
            else:
                client = await self._get_workflow_client()
                if not client:
                    return {"error": "No workflow servers available"}

            # Get server settings resource
            settings = await client.read_resource("config://server/settings")
            return settings

        except Exception as e:
            logger.error(f"Failed to get server configuration: {e}")
            return {"error": str(e)}

    async def get_usage_documentation(
        self, server_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get API usage documentation from server."""
        try:
            # Get client for the server
            if server_name and server_name in self.clients:
                client = self.clients[server_name]
            else:
                client = await self._get_workflow_client()
                if not client:
                    return {"error": "No workflow servers available"}

            # Get usage documentation resource
            docs = await client.read_resource("docs://api/usage")
            return docs

        except Exception as e:
            logger.error(f"Failed to get documentation: {e}")
            return {"error": str(e)}

    async def _get_workflow_client(self) -> Optional[MCPClient]:
        """Get any client that supports workflows."""
        # Try to get a client with workflow capability
        try:
            client = await get_mcp_client("workflows")
            if client:
                return client
        except Exception:
            pass

        # Fallback to any connected client
        if self.clients:
            return next(iter(self.clients.values()))

        return None

    async def batch_text_analysis(
        self, texts: List[str], analysis_type: str = "sentiment"
    ) -> List[Dict[str, Any]]:
        """Process multiple texts in batch."""
        results = []

        # Process texts concurrently
        tasks = [self.execute_text_analysis(text, analysis_type) for text in texts]

        completed_results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, result in enumerate(completed_results):
            if isinstance(result, Exception):
                results.append(
                    {
                        "error": str(result),
                        "text": texts[i],
                        "analysis_type": analysis_type,
                    }
                )
            else:
                results.append(result)

        return results

    async def disconnect_all(self):
        """Disconnect from all servers."""
        for server_name, client in self.clients.items():
            try:
                await client.disconnect()
                logger.info(f"Disconnected from {server_name}")
            except Exception as e:
                logger.error(f"Error disconnecting from {server_name}: {e}")

        self.clients.clear()


async def demo_client_usage():
    """Demonstrate MCP client usage with Kailash servers."""
    # Create client
    client = KailashMCPClient(api_key="user_key_456")

    try:
        # Discover servers
        print("🔍 Discovering Kailash MCP servers...")
        servers = await client.discover_kailash_servers()
        print(f"Found {len(servers)} servers:")
        for server in servers:
            print(f"  - {server['name']}: {server['capabilities']}")

        # Connect to a server (or use service discovery)
        if servers:
            print(f"\n🔌 Connecting to {servers[0]['name']}...")
            connected_client = await client.connect_to_server(servers[0])
            if not connected_client:
                print("❌ Failed to connect to server")
                return
        else:
            # For demo, create a mock server configuration
            mock_server = {
                "name": "kailash-demo-server",
                "transport": "http",
                "url": "http://localhost:8080",
            }
            print("\n🔌 Connecting to demo server...")
            connected_client = await client.connect_to_server(mock_server)

        # Get available workflows
        print("\n📋 Getting available workflows...")
        workflows = await client.get_available_workflows()
        print(f"Available workflows: {json.dumps(workflows, indent=2)}")

        # Execute text analysis
        print("\n🔤 Executing text analysis...")
        text_result = await client.execute_text_analysis(
            "This product is absolutely fantastic! I love it.", "sentiment"
        )
        print(f"Text analysis result: {json.dumps(text_result, indent=2)}")

        # Process data file (example)
        print("\n📊 Processing data file...")
        data_result = await client.process_data_file(
            "/example/data/sales.csv", "analyze"
        )
        print(f"Data processing result: {json.dumps(data_result, indent=2)}")

        # Batch processing example
        print("\n📦 Batch text analysis...")
        texts = [
            "Great product!",
            "Terrible experience.",
            "It's okay, nothing special.",
        ]
        batch_results = await client.batch_text_analysis(texts, "sentiment")
        print(f"Batch results: {json.dumps(batch_results, indent=2)}")

        # Get server configuration
        print("\n⚙️ Getting server configuration...")
        config = await client.get_server_configuration()
        print(f"Server config: {json.dumps(config, indent=2)}")

    except Exception as e:
        logger.error(f"Demo failed: {e}")

    finally:
        # Clean up connections
        await client.disconnect_all()
        print("\n✅ Demo completed")


if __name__ == "__main__":
    asyncio.run(demo_client_usage())
