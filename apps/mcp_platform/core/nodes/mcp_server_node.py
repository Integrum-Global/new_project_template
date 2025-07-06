"""
MCP Server Node

Custom Kailash node for MCP server management operations.
"""

import logging
import subprocess
from datetime import datetime
from typing import Any, Dict, Optional

from kailash.mcp_server.client import MCPClient
from kailash.mcp_server.protocol import MCPProtocol
from kailash.mcp_server.transports import StdioTransport
from kailash.node import Node
from kailash.node.parameter import NodeParameter, ParameterType

logger = logging.getLogger(__name__)


class MCPServerNode(Node):
    """
    Node for MCP server lifecycle management.

    Supports operations:
    - start_server: Start an MCP server
    - stop_server: Stop an MCP server
    - check_health: Check server health
    - discover_tools: Discover available tools
    - get_info: Get server information
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the MCP server node."""
        self.config = config or {}
        self.default_timeout = self.config.get("timeout", 30)

        # Active server connections
        self._connections = {}

        super().__init__()

    def get_parameters(self) -> Dict[str, NodeParameter]:
        """Define node parameters."""
        return {
            "operation": NodeParameter(
                name="operation",
                type=ParameterType.STRING,
                required=True,
                description="Operation to perform",
                allowed_values=[
                    "start_server",
                    "stop_server",
                    "check_health",
                    "discover_tools",
                    "get_info",
                ],
            ),
            "server_config": NodeParameter(
                name="server_config",
                type=ParameterType.DICT,
                required=False,
                description="Server configuration for start operation",
            ),
            "server_id": NodeParameter(
                name="server_id",
                type=ParameterType.STRING,
                required=False,
                description="Server ID for operations on existing servers",
            ),
            "timeout": NodeParameter(
                name="timeout",
                type=ParameterType.INTEGER,
                required=False,
                default=30,
                description="Operation timeout in seconds",
            ),
        }

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the MCP server operation."""
        operation = context.get("operation")

        try:
            if operation == "start_server":
                return await self._start_server(context)
            elif operation == "stop_server":
                return await self._stop_server(context)
            elif operation == "check_health":
                return await self._check_health(context)
            elif operation == "discover_tools":
                return await self._discover_tools(context)
            elif operation == "get_info":
                return await self._get_info(context)
            else:
                return {"success": False, "error": f"Unknown operation: {operation}"}

        except Exception as e:
            logger.error(f"Error in MCP server operation: {e}")
            return {"success": False, "error": str(e), "operation": operation}

    async def _start_server(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Start an MCP server."""
        config = context.get("server_config", {})

        if not config:
            return {"success": False, "error": "Server configuration required"}

        # Extract configuration
        server_id = config.get("id", str(datetime.utcnow().timestamp()))
        transport = config.get("transport", "stdio")

        if transport != "stdio":
            return {
                "success": False,
                "error": f"Transport {transport} not supported by this node",
            }

        # Build command
        command = [config["command"]]
        if "args" in config:
            command.extend(config["args"])

        # Set environment
        import os

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
            text=False,
        )

        # Create MCP client
        transport = StdioTransport(process.stdin, process.stdout)
        protocol = MCPProtocol()
        client = MCPClient(transport, protocol)

        # Initialize connection
        await client.initialize()

        # Store connection
        self._connections[server_id] = {
            "process": process,
            "client": client,
            "transport": transport,
            "config": config,
            "started_at": datetime.utcnow(),
        }

        return {
            "success": True,
            "server_id": server_id,
            "status": "running",
            "pid": process.pid,
            "started_at": self._connections[server_id]["started_at"].isoformat(),
        }

    async def _stop_server(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Stop an MCP server."""
        server_id = context.get("server_id")

        if not server_id:
            return {"success": False, "error": "Server ID required"}

        if server_id not in self._connections:
            return {"success": False, "error": f"Server {server_id} not found"}

        connection = self._connections[server_id]

        try:
            # Close MCP client
            await connection["client"].close()

            # Close transport
            await connection["transport"].close()

            # Terminate process
            process = connection["process"]
            process.terminate()

            # Wait for termination
            import asyncio

            await asyncio.sleep(0.5)

            if process.poll() is None:
                # Force kill if still running
                process.kill()

            # Remove from connections
            del self._connections[server_id]

            return {"success": True, "server_id": server_id, "status": "stopped"}

        except Exception as e:
            return {
                "success": False,
                "error": f"Error stopping server: {e}",
                "server_id": server_id,
            }

    async def _check_health(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Check health of an MCP server."""
        server_id = context.get("server_id")

        if not server_id:
            return {"success": False, "error": "Server ID required"}

        if server_id not in self._connections:
            return {"success": False, "error": f"Server {server_id} not found"}

        connection = self._connections[server_id]

        try:
            # Try to list tools as health check
            start_time = datetime.utcnow()

            import asyncio

            await asyncio.wait_for(connection["client"].list_tools(), timeout=5.0)

            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000

            # Check process status
            process = connection["process"]
            is_running = process.poll() is None

            return {
                "success": True,
                "server_id": server_id,
                "healthy": is_running,
                "response_time_ms": response_time,
                "pid": process.pid if is_running else None,
                "uptime_seconds": (
                    datetime.utcnow() - connection["started_at"]
                ).total_seconds(),
            }

        except Exception as e:
            return {
                "success": True,
                "server_id": server_id,
                "healthy": False,
                "error": str(e),
            }

    async def _discover_tools(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Discover tools available on an MCP server."""
        server_id = context.get("server_id")

        if not server_id:
            return {"success": False, "error": "Server ID required"}

        if server_id not in self._connections:
            return {"success": False, "error": f"Server {server_id} not found"}

        connection = self._connections[server_id]

        try:
            # Get tools from server
            tools_response = await connection["client"].list_tools()

            tools = []
            for tool_data in tools_response.get("tools", []):
                tools.append(
                    {
                        "name": tool_data["name"],
                        "description": tool_data.get("description", ""),
                        "input_schema": tool_data.get("inputSchema", {}),
                        "metadata": tool_data.get("metadata", {}),
                    }
                )

            return {
                "success": True,
                "server_id": server_id,
                "tool_count": len(tools),
                "tools": tools,
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Error discovering tools: {e}",
                "server_id": server_id,
            }

    async def _get_info(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Get information about an MCP server."""
        server_id = context.get("server_id")

        if not server_id:
            # Return info about all servers
            servers = []
            for sid, conn in self._connections.items():
                process = conn["process"]
                is_running = process.poll() is None

                servers.append(
                    {
                        "server_id": sid,
                        "status": "running" if is_running else "stopped",
                        "pid": process.pid if is_running else None,
                        "started_at": conn["started_at"].isoformat(),
                        "config": conn["config"],
                    }
                )

            return {"success": True, "total_servers": len(servers), "servers": servers}

        if server_id not in self._connections:
            return {"success": False, "error": f"Server {server_id} not found"}

        connection = self._connections[server_id]
        process = connection["process"]
        is_running = process.poll() is None

        info = {
            "success": True,
            "server_id": server_id,
            "status": "running" if is_running else "stopped",
            "pid": process.pid if is_running else None,
            "started_at": connection["started_at"].isoformat(),
            "uptime_seconds": (
                datetime.utcnow() - connection["started_at"]
            ).total_seconds(),
            "config": connection["config"],
        }

        # Try to get server capabilities
        if is_running:
            try:
                # Get tools count
                tools_response = await connection["client"].list_tools()
                info["tool_count"] = len(tools_response.get("tools", []))

                # Get resources count
                try:
                    resources_response = await connection["client"].list_resources()
                    info["resource_count"] = len(
                        resources_response.get("resources", [])
                    )
                except:
                    info["resource_count"] = 0

            except Exception as e:
                info["capabilities_error"] = str(e)

        return info

    async def cleanup(self):
        """Cleanup when node is destroyed."""
        # Stop all servers
        for server_id in list(self._connections.keys()):
            await self._stop_server({"server_id": server_id})
