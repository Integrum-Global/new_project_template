"""
MCP Gateway - Main orchestrator for the MCP application.

This module contains the main gateway class that orchestrates
all MCP services and provides the primary interface for the application.
"""

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

from kailash.middleware import create_gateway
from kailash.nodes.admin.audit_log import EnterpriseAuditLogNode
from kailash.runtime.local import LocalRuntime

from .models import MCPServer, MCPTool, ServerStatus, ToolExecution
from .registry import MCPRegistry
from .security import MCPSecurityManager
from .services import MCPService

logger = logging.getLogger(__name__)


class MCPGateway:
    """
    Main gateway orchestrator for MCP operations.

    Coordinates between all services and provides the primary
    interface for MCP server management, tool discovery, and execution.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the MCP Gateway."""
        self.config = config or {}
        self.runtime = LocalRuntime()

        # Initialize core services
        self.registry = MCPRegistry(config=self.config)
        self.security = MCPSecurityManager(config=self.config.get("security", {}))
        self.service = MCPService(runtime=self.runtime, config=self.config)

        # Audit logging
        try:
            from kailash.nodes.admin.audit_log import EnterpriseAuditLogNode

            self.audit_node = EnterpriseAuditLogNode(
                connection_string=self.config.get("database_url")
            )
        except ImportError:
            logger.warning(
                "EnterpriseAuditLogNode not available - audit logging disabled"
            )
            self.audit_node = None
        except Exception as e:
            logger.warning(f"Could not initialize audit log node: {e}")
            self.audit_node = None

        # Server tracking
        self._servers: Dict[str, MCPServer] = {}
        self._active_connections: Dict[str, Any] = {}

        # Background tasks
        self._monitor_task: Optional[asyncio.Task] = None

    async def initialize(self):
        """Initialize the gateway and all services."""
        logger.info("Initializing MCP Gateway")

        # Initialize registry
        await self.registry.initialize()

        # Load existing servers from registry into local cache
        existing_servers = await self.registry.list_servers()
        for server in existing_servers:
            self._servers[server.id] = server

        logger.info(f"Loaded {len(existing_servers)} existing servers from registry")

        # Start monitoring
        if self.config.get("enable_monitoring", True):
            self._monitor_task = asyncio.create_task(self._monitor_servers())

        logger.info("MCP Gateway initialized successfully")

    async def register_server(
        self, server_config: Dict[str, Any], user_id: Optional[str] = None
    ) -> str:
        """
        Register a new MCP server.

        Args:
            server_config: Server configuration
            user_id: User ID for audit logging

        Returns:
            Server ID
        """
        # Validate configuration
        if not self._validate_server_config(server_config):
            raise ValueError("Invalid server configuration")

        # Check permissions
        if not await self.security.can_register_server(user_id, server_config):
            raise PermissionError("User not authorized to register server")

        # Create server model
        server = MCPServer(
            id=str(uuid.uuid4()),
            name=server_config["name"],
            transport=server_config["transport"],
            config=server_config,
            status=ServerStatus.REGISTERED,
            created_at=datetime.now(timezone.utc),
            owner_id=user_id,
            description=server_config.get("description"),
            tags=server_config.get("tags", []),
            auto_start=server_config.get("auto_start", False),
            timeout=server_config.get("timeout", 30),
        )

        # Register in registry
        await self.registry.register_server(server)

        # Store locally
        self._servers[server.id] = server

        # Audit log
        await self._audit_log(
            "server_registered", user_id, {"server_id": server.id, "name": server.name}
        )

        # Auto-start if configured
        if server_config.get("auto_start", False):
            await self.start_server(server.id, user_id)

        return server.id

    async def start_server(
        self, server_id: str, user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Start an MCP server.

        Args:
            server_id: Server ID
            user_id: User ID for audit logging

        Returns:
            Start result
        """
        server = self._servers.get(server_id)
        if not server:
            raise ValueError(f"Server {server_id} not found")

        # Check permissions
        if not await self.security.can_manage_server(user_id, server_id):
            raise PermissionError("User not authorized to manage server")

        # Start the server
        try:
            connection = await self.service.start_server(server)
            self._active_connections[server_id] = connection

            # Update status
            server.status = ServerStatus.RUNNING
            server.started_at = datetime.now(timezone.utc)
            await self.registry.update_server(server)

            # Discover tools
            tools = await self.discover_tools(server_id, user_id)

            # Audit log
            await self._audit_log(
                "server_started",
                user_id,
                {"server_id": server_id, "tools_discovered": len(tools)},
            )

            return {
                "success": True,
                "server_id": server_id,
                "status": "running",
                "tools_available": len(tools),
            }

        except Exception as e:
            logger.error(f"Failed to start server {server_id}: {e}")
            server.status = ServerStatus.ERROR
            server.error_message = str(e)
            await self.registry.update_server(server)
            raise

    async def stop_server(
        self, server_id: str, user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Stop an MCP server."""
        server = self._servers.get(server_id)
        if not server:
            raise ValueError(f"Server {server_id} not found")

        # Check permissions
        if not await self.security.can_manage_server(user_id, server_id):
            raise PermissionError("User not authorized to manage server")

        # Stop the server
        connection = self._active_connections.get(server_id)
        if connection:
            await self.service.stop_server(server, connection)
            del self._active_connections[server_id]

        # Update status
        server.status = ServerStatus.STOPPED
        server.stopped_at = datetime.now(timezone.utc)
        await self.registry.update_server(server)

        # Audit log
        await self._audit_log("server_stopped", user_id, {"server_id": server_id})

        return {"success": True, "server_id": server_id, "status": "stopped"}

    async def discover_tools(
        self, server_id: str, user_id: Optional[str] = None
    ) -> List[MCPTool]:
        """
        Discover tools from an MCP server.

        Args:
            server_id: Server ID
            user_id: User ID for permissions

        Returns:
            List of discovered tools
        """
        server = self._servers.get(server_id)
        if not server:
            raise ValueError(f"Server {server_id} not found")

        # Check permissions
        if not await self.security.can_access_server(user_id, server_id):
            raise PermissionError("User not authorized to access server")

        # Get connection
        connection = self._active_connections.get(server_id)
        if not connection:
            raise RuntimeError(f"Server {server_id} is not running")

        # Discover tools
        tools = await self.service.discover_tools(server, connection)

        # Register tools
        for tool in tools:
            await self.registry.register_tool(server_id, tool)

        # Cache discovery
        server.last_discovery = datetime.now(timezone.utc)
        server.tool_count = len(tools)
        await self.registry.update_server(server)

        return tools

    async def execute_tool(
        self,
        server_id: str,
        tool_name: str,
        parameters: Dict[str, Any],
        user_id: Optional[str] = None,
        execution_options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute a tool on an MCP server.

        Args:
            server_id: Server ID
            tool_name: Tool name
            parameters: Tool parameters
            user_id: User ID for permissions
            execution_options: Additional execution options

        Returns:
            Execution result
        """
        server = self._servers.get(server_id)
        if not server:
            raise ValueError(f"Server {server_id} not found")

        # Check permissions
        if not await self.security.can_execute_tool(user_id, server_id, tool_name):
            raise PermissionError("User not authorized to execute tool")

        # Get tool
        tool = await self.registry.get_tool(server_id, tool_name)
        if not tool:
            raise ValueError(f"Tool {tool_name} not found on server {server_id}")

        # Validate parameters
        if not self._validate_tool_parameters(tool, parameters):
            raise ValueError("Invalid tool parameters")

        # Get connection
        connection = self._active_connections.get(server_id)
        if not connection:
            raise RuntimeError(f"Server {server_id} is not running")

        # Create execution record
        execution = ToolExecution(
            id=str(uuid.uuid4()),
            server_id=server_id,
            tool_name=tool_name,
            parameters=parameters,
            user_id=user_id,
            started_at=datetime.now(timezone.utc),
        )

        try:
            # Execute tool
            result = await self.service.execute_tool(
                server, connection, tool, parameters, execution_options or {}
            )

            # Update execution record
            execution.completed_at = datetime.now(timezone.utc)
            execution.result = result
            execution.status = "completed"

            # Audit log
            await self._audit_log(
                "tool_executed",
                user_id,
                {
                    "server_id": server_id,
                    "tool_name": tool_name,
                    "execution_id": execution.id,
                },
            )

            return {
                "success": True,
                "execution_id": execution.id,
                "result": result,
                "duration_ms": (
                    execution.completed_at - execution.started_at
                ).total_seconds()
                * 1000,
            }

        except Exception as e:
            # Update execution record
            execution.completed_at = datetime.now(timezone.utc)
            execution.error = str(e)
            execution.status = "failed"

            # Audit log
            await self._audit_log(
                "tool_execution_failed",
                user_id,
                {
                    "server_id": server_id,
                    "tool_name": tool_name,
                    "execution_id": execution.id,
                    "error": str(e),
                },
                severity="high",
            )

            raise

    async def list_servers(
        self, user_id: Optional[str] = None, filters: Optional[Dict[str, Any]] = None
    ) -> List[MCPServer]:
        """List MCP servers with optional filters."""
        # Get servers from registry
        servers = await self.registry.list_servers(filters)

        # Filter by permissions
        if user_id:
            servers = [
                s
                for s in servers
                if await self.security.can_access_server(user_id, s.id)
            ]

        return servers

    async def get_server_status(
        self, server_id: str, user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get detailed server status."""
        server = self._servers.get(server_id)
        if not server:
            raise ValueError(f"Server {server_id} not found")

        # Check permissions
        if not await self.security.can_access_server(user_id, server_id):
            raise PermissionError("User not authorized to access server")

        # Get connection status
        connection = self._active_connections.get(server_id)
        is_connected = connection is not None

        # Get health status if running
        health = None
        if is_connected:
            health = await self.service.check_health(server, connection)

        return {
            "server_id": server_id,
            "name": server.name,
            "status": server.status.value,
            "connected": is_connected,
            "health": health,
            "tool_count": server.tool_count,
            "last_discovery": (
                server.last_discovery.isoformat() if server.last_discovery else None
            ),
            "created_at": server.created_at.isoformat(),
            "started_at": server.started_at.isoformat() if server.started_at else None,
            "error_message": server.error_message,
        }

    async def _monitor_servers(self):
        """Monitor server health and status."""
        while True:
            try:
                for server_id, connection in list(self._active_connections.items()):
                    server = self._servers.get(server_id)
                    if server:
                        # Check health
                        health = await self.service.check_health(server, connection)

                        # Update status if unhealthy
                        if not health.get("healthy", True):
                            server.status = ServerStatus.UNHEALTHY
                            await self.registry.update_server(server)

                            # Log issue
                            logger.warning(
                                f"Server {server_id} is unhealthy: {health.get('error')}"
                            )

            except Exception as e:
                logger.error(f"Error monitoring servers: {e}")

            # Wait before next check
            await asyncio.sleep(self.config.get("monitor_interval", 60))

    def _validate_server_config(self, config: Dict[str, Any]) -> bool:
        """Validate server configuration."""
        required = ["name", "transport"]
        if not all(k in config for k in required):
            return False

        # Validate transport-specific config
        transport = config["transport"]
        if transport == "stdio":
            if "command" not in config:
                return False
        elif transport == "http":
            if "url" not in config:
                return False

        return True

    def _validate_tool_parameters(
        self, tool: MCPTool, parameters: Dict[str, Any]
    ) -> bool:
        """Validate tool parameters against schema."""
        # TODO: Implement JSON schema validation
        # For now, just check required parameters
        if hasattr(tool, "required_params"):
            for param in tool.required_params:
                if param not in parameters:
                    return False
        return True

    async def _audit_log(
        self,
        event_type: str,
        user_id: Optional[str],
        details: Dict[str, Any],
        severity: str = "low",
    ):
        """Log audit event."""
        try:
            if self.audit_node:
                # Try to use the runtime to execute the audit node properly
                try:
                    if hasattr(self.runtime, "execute_node_async"):
                        await self.runtime.execute_node_async(
                            self.audit_node,
                            {
                                "operation": "log_event",
                                "event_type": f"mcp_{event_type}",
                                "severity": severity,
                                "user_id": user_id,
                                "details": details,
                            },
                        )
                    else:
                        # Fallback to synchronous execution if execute_async not available
                        if hasattr(self.audit_node, "execute_async"):
                            result = await self.audit_node.execute_async(
                                {
                                    "operation": "log_event",
                                    "event_type": f"mcp_{event_type}",
                                    "severity": severity,
                                    "user_id": user_id,
                                    "details": details,
                                }
                            )
                        else:
                            # Skip audit logging if node doesn't support the expected interface
                            logger.info(
                                f"Audit event: {event_type} for user {user_id}, severity: {severity}, details: {details}"
                            )
                except Exception as audit_error:
                    # If audit node fails, log the event and continue
                    logger.warning(f"Audit node execution failed: {audit_error}")
                    logger.info(
                        f"Audit event: {event_type} for user {user_id}, severity: {severity}"
                    )
            else:
                # Fallback to simple logging
                logger.info(
                    f"Audit event: {event_type} for user {user_id}, severity: {severity}"
                )
        except Exception as e:
            logger.error(f"Failed to log audit event: {e}")
            # Always log the event even if audit fails
            logger.info(
                f"Audit event: {event_type} for user {user_id}, severity: {severity}"
            )

    async def shutdown(self):
        """Shutdown the gateway and all services."""
        logger.info("Shutting down MCP Gateway")

        # Cancel background tasks
        if self._monitor_task and not self._monitor_task.done():
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass

        # Stop all servers
        for server_id in list(self._active_connections.keys()):
            try:
                await self.stop_server(server_id)
            except Exception as e:
                logger.error(f"Error stopping server {server_id}: {e}")

        # Shutdown services
        await self.registry.shutdown()

        logger.info("MCP Gateway shutdown complete")
