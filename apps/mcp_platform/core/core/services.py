"""
MCP Service - Core business logic for MCP operations.

This module provides the main service layer for MCP server management,
tool discovery, and execution.
"""

import asyncio
import json
import logging
import os
import subprocess
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

import aiohttp
import websockets

from kailash.runtime.local import LocalRuntime

# Import MCP components with fallbacks for testing
try:
    from kailash.mcp_server.client import MCPClient
    from kailash.mcp_server.protocol import ProtocolManager
    from kailash.mcp_server.transports import (
        EnhancedStdioTransport,
        StreamableHTTPTransport,
    )
except ImportError:
    # Mock classes for testing when MCP components are not available
    class MCPClient:
        def __init__(self, transport, protocol):
            self.transport = transport
            self.protocol = protocol

        async def initialize(self):
            pass

        async def close(self):
            pass

        async def list_tools(self):
            return []

        async def call_tool(self, name, arguments):
            return {"result": "mock_result"}

    class ProtocolManager:
        pass

    class EnhancedStdioTransport:
        def __init__(self, stdin, stdout):
            self.stdin = stdin
            self.stdout = stdout

        async def close(self):
            pass

    class StreamableHTTPTransport:
        def __init__(self, url, headers=None, session=None):
            self.url = url
            self.headers = headers or {}
            self.session = session

        async def close(self):
            pass


from .models import MCPResource, MCPServer, MCPTool, TransportType

logger = logging.getLogger(__name__)


class MCPConnection:
    """Represents an active connection to an MCP server."""

    def __init__(
        self,
        server: MCPServer,
        client: MCPClient,
        transport: Any,
        process: Optional[subprocess.Popen] = None,
    ):
        self.server = server
        self.client = client
        self.transport = transport
        self.process = process
        self.connected_at = datetime.now(timezone.utc)
        self.last_health_check = None
        self.is_healthy = True

    async def close(self):
        """Close the connection."""
        try:
            if self.client:
                await self.client.close()
            if self.transport:
                await self.transport.close()
            if self.process:
                self.process.terminate()
                await asyncio.sleep(0.5)
                if self.process.poll() is None:
                    self.process.kill()
        except Exception as e:
            logger.error(f"Error closing connection: {e}")


class MCPService:
    """
    Core service for MCP operations.

    Handles server lifecycle, tool discovery, and execution.
    """

    def __init__(self, runtime: LocalRuntime, config: Optional[Dict[str, Any]] = None):
        """Initialize the MCP service."""
        self.runtime = runtime
        self.config = config or {}

        # Connection pool
        self._connections: Dict[str, MCPConnection] = {}

        # HTTP session for HTTP transport
        self._http_session: Optional[aiohttp.ClientSession] = None

    async def start_server(self, server: MCPServer) -> MCPConnection:
        """
        Start an MCP server and establish connection.

        Args:
            server: Server to start

        Returns:
            Active connection
        """
        logger.info(f"Starting MCP server: {server.name}")

        # Create transport based on type
        if server.transport == "stdio":
            connection = await self._start_stdio_server(server)
        elif server.transport == "http":
            connection = await self._start_http_server(server)
        elif server.transport == "sse":
            connection = await self._start_sse_server(server)
        elif server.transport == "websocket":
            connection = await self._start_websocket_server(server)
        else:
            raise ValueError(f"Unsupported transport: {server.transport}")

        # Store connection
        self._connections[server.id] = connection

        # Initialize the connection
        await connection.client.initialize()

        logger.info(f"MCP server started: {server.name}")
        return connection

    async def _start_stdio_server(self, server: MCPServer) -> MCPConnection:
        """Start STDIO transport server."""
        config = server.config

        # Build command
        command = [config["command"]]
        if "args" in config:
            command.extend(config["args"])

        # Set environment
        env = dict(os.environ)
        if "environment" in config:
            env.update(config["environment"])

        # Start process
        process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            text=False,  # Use binary mode
        )

        # Create transport and client
        transport = EnhancedStdioTransport(process.stdin, process.stdout)
        protocol = ProtocolManager()
        client = MCPClient(transport, protocol)

        return MCPConnection(server, client, transport, process)

    async def _start_http_server(self, server: MCPServer) -> MCPConnection:
        """Start HTTP transport server."""
        config = server.config

        # Create HTTP session if needed
        if not self._http_session:
            self._http_session = aiohttp.ClientSession()

        # Create transport and client
        transport = StreamableHTTPTransport(
            url=config["url"],
            headers=config.get("headers", {}),
            session=self._http_session,
        )
        protocol = ProtocolManager()
        client = MCPClient(transport, protocol)

        # Test connection
        try:
            await transport.connect()
        except Exception as e:
            raise RuntimeError(f"Failed to connect to HTTP server: {e}")

        return MCPConnection(server, client, transport)

    async def _start_sse_server(self, server: MCPServer) -> MCPConnection:
        """Start SSE transport server."""
        # TODO: Implement SSE transport
        raise NotImplementedError("SSE transport not yet implemented")

    async def _start_websocket_server(self, server: MCPServer) -> MCPConnection:
        """Start WebSocket transport server."""
        # TODO: Implement WebSocket transport
        raise NotImplementedError("WebSocket transport not yet implemented")

    async def stop_server(self, server: MCPServer, connection: MCPConnection):
        """Stop an MCP server."""
        logger.info(f"Stopping MCP server: {server.name}")

        # Close connection
        await connection.close()

        # Remove from pool
        if server.id in self._connections:
            del self._connections[server.id]

        logger.info(f"MCP server stopped: {server.name}")

    async def discover_tools(
        self, server: MCPServer, connection: MCPConnection
    ) -> List[MCPTool]:
        """
        Discover available tools from an MCP server.

        Args:
            server: Server to query
            connection: Active connection

        Returns:
            List of discovered tools
        """
        logger.info(f"Discovering tools on server: {server.name}")

        try:
            # Get tools from server
            tools_response = await connection.client.list_tools()

            # Convert to MCPTool models
            tools = []
            for tool_data in tools_response.get("tools", []):
                tool = MCPTool(
                    name=tool_data["name"],
                    description=tool_data.get("description", ""),
                    server_id=server.id,
                    input_schema=tool_data.get("inputSchema", {}),
                    discovered_at=datetime.utcnow(),
                )

                # Set additional metadata if available
                if "metadata" in tool_data:
                    metadata = tool_data["metadata"]
                    tool.category = metadata.get("category")
                    tool.tags = metadata.get("tags", [])
                    tool.version = metadata.get("version")
                    tool.timeout = metadata.get("timeout", 120)
                    tool.cache_enabled = metadata.get("cache_enabled", False)
                    tool.cache_ttl = metadata.get("cache_ttl", 3600)
                    tool.rate_limit = metadata.get("rate_limit")
                    tool.required_permissions = metadata.get("required_permissions", [])

                tools.append(tool)

            logger.info(f"Discovered {len(tools)} tools on server: {server.name}")
            return tools

        except Exception as e:
            logger.error(f"Error discovering tools: {e}")
            raise

    async def discover_resources(
        self, server: MCPServer, connection: MCPConnection
    ) -> List[MCPResource]:
        """Discover available resources from an MCP server."""
        logger.info(f"Discovering resources on server: {server.name}")

        try:
            # Get resources from server
            resources_response = await connection.client.list_resources()

            # Convert to MCPResource models
            resources = []
            for resource_data in resources_response.get("resources", []):
                resource = MCPResource(
                    uri=resource_data["uri"],
                    name=resource_data.get("name", resource_data["uri"]),
                    server_id=server.id,
                    description=resource_data.get("description"),
                    mime_type=resource_data.get("mimeType"),
                    created_at=datetime.utcnow(),
                )

                # Set additional metadata if available
                if "metadata" in resource_data:
                    metadata = resource_data["metadata"]
                    resource.size_bytes = metadata.get("size")
                    resource.cache_enabled = metadata.get("cache_enabled", True)
                    resource.cache_ttl = metadata.get("cache_ttl", 3600)
                    resource.access_permissions = metadata.get("permissions", [])

                resources.append(resource)

            logger.info(
                f"Discovered {len(resources)} resources on server: {server.name}"
            )
            return resources

        except Exception as e:
            logger.error(f"Error discovering resources: {e}")
            raise

    async def execute_tool(
        self,
        server: MCPServer,
        connection: MCPConnection,
        tool: MCPTool,
        parameters: Dict[str, Any],
        options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute a tool on an MCP server.

        Args:
            server: Server hosting the tool
            connection: Active connection
            tool: Tool to execute
            parameters: Tool parameters
            options: Execution options

        Returns:
            Execution result
        """
        logger.info(f"Executing tool {tool.name} on server {server.name}")

        options = options or {}
        start_time = datetime.utcnow()

        try:
            # Set timeout
            timeout = options.get("timeout", tool.timeout)

            # Execute tool with timeout
            result = await asyncio.wait_for(
                connection.client.call_tool(tool.name, parameters), timeout=timeout
            )

            # Calculate duration
            duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

            # Process result
            if result.get("success", True):
                logger.info(
                    f"Tool {tool.name} executed successfully in {duration_ms:.2f}ms"
                )
                return {
                    "success": True,
                    "result": result.get("result", result),
                    "duration_ms": duration_ms,
                }
            else:
                error = result.get("error", "Unknown error")
                logger.error(f"Tool {tool.name} execution failed: {error}")
                return {"success": False, "error": error, "duration_ms": duration_ms}

        except asyncio.TimeoutError:
            duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            logger.error(f"Tool {tool.name} execution timed out after {timeout}s")
            return {
                "success": False,
                "error": f"Tool execution timed out after {timeout} seconds",
                "duration_ms": duration_ms,
            }
        except Exception as e:
            duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            logger.error(f"Error executing tool {tool.name}: {e}")
            return {"success": False, "error": str(e), "duration_ms": duration_ms}

    async def get_resource(
        self, server: MCPServer, connection: MCPConnection, resource_uri: str
    ) -> Dict[str, Any]:
        """Get a resource from an MCP server."""
        logger.info(f"Getting resource {resource_uri} from server {server.name}")

        try:
            result = await connection.client.read_resource(resource_uri)

            return {
                "success": True,
                "uri": resource_uri,
                "content": result.get("content"),
                "mime_type": result.get("mimeType"),
                "metadata": result.get("metadata", {}),
            }

        except Exception as e:
            logger.error(f"Error getting resource {resource_uri}: {e}")
            return {"success": False, "error": str(e), "uri": resource_uri}

    async def check_health(
        self, server: MCPServer, connection: MCPConnection
    ) -> Dict[str, Any]:
        """Check health of an MCP server."""
        try:
            # Try to get server info or list tools as health check
            start_time = datetime.utcnow()

            # Use a simple operation with timeout
            await asyncio.wait_for(connection.client.list_tools(), timeout=5.0)

            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000

            # Update connection health status
            connection.last_health_check = datetime.utcnow()
            connection.is_healthy = True

            return {
                "healthy": True,
                "response_time_ms": response_time,
                "checked_at": connection.last_health_check.isoformat(),
            }

        except Exception as e:
            # Mark as unhealthy
            connection.is_healthy = False
            connection.last_health_check = datetime.utcnow()

            return {
                "healthy": False,
                "error": str(e),
                "checked_at": connection.last_health_check.isoformat(),
            }

    async def batch_execute_tools(
        self, executions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Execute multiple tools in parallel.

        Args:
            executions: List of execution requests, each containing:
                - server_id: Server ID
                - tool_name: Tool name
                - parameters: Tool parameters

        Returns:
            List of execution results
        """
        tasks = []

        for execution in executions:
            server_id = execution["server_id"]
            tool_name = execution["tool_name"]
            parameters = execution["parameters"]

            # Get connection
            connection = self._connections.get(server_id)
            if not connection:
                tasks.append(
                    asyncio.create_task(
                        self._return_error(f"Server {server_id} not connected")
                    )
                )
                continue

            # Create execution task
            task = asyncio.create_task(
                self._execute_with_metadata(
                    connection, tool_name, parameters, execution.get("options", {})
                )
            )
            tasks.append(task)

        # Execute all tasks in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(
                    {"success": False, "error": str(result), "execution_index": i}
                )
            else:
                result["execution_index"] = i
                processed_results.append(result)

        return processed_results

    async def _execute_with_metadata(
        self,
        connection: MCPConnection,
        tool_name: str,
        parameters: Dict[str, Any],
        options: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute tool with metadata."""
        # TODO: Get tool from registry
        tool = MCPTool(name=tool_name, description="", server_id=connection.server.id)

        result = await self.execute_tool(
            connection.server, connection, tool, parameters, options
        )

        result["server_id"] = connection.server.id
        result["tool_name"] = tool_name

        return result

    async def _return_error(self, error: str) -> Dict[str, Any]:
        """Return error result."""
        return {"success": False, "error": error}

    def get_connection_stats(self) -> Dict[str, Any]:
        """Get statistics about active connections."""
        total_connections = len(self._connections)
        healthy_connections = sum(1 for c in self._connections.values() if c.is_healthy)

        server_stats = {}
        for server_id, connection in self._connections.items():
            uptime = (datetime.utcnow() - connection.connected_at).total_seconds()
            server_stats[server_id] = {
                "connected_at": connection.connected_at.isoformat(),
                "uptime_seconds": uptime,
                "is_healthy": connection.is_healthy,
                "last_health_check": (
                    connection.last_health_check.isoformat()
                    if connection.last_health_check
                    else None
                ),
            }

        return {
            "total_connections": total_connections,
            "healthy_connections": healthy_connections,
            "unhealthy_connections": total_connections - healthy_connections,
            "servers": server_stats,
        }

    async def cleanup(self):
        """Cleanup resources."""
        # Close all connections
        for connection in list(self._connections.values()):
            try:
                await connection.close()
            except Exception as e:
                logger.error(f"Error closing connection: {e}")

        self._connections.clear()

        # Close HTTP session
        if self._http_session:
            await self._http_session.close()
            self._http_session = None
