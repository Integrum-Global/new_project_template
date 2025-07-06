"""
Tests for MCP Gateway

This module tests the core gateway functionality.
"""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest
import pytest_asyncio

from apps.mcp_platform.core.core.gateway import MCPGateway
from apps.mcp_platform.core.core.models import MCPServer, MCPTool, ServerStatus
from apps.mcp_platform.core.core.registry import MCPRegistry
from apps.mcp_platform.core.core.security import MCPSecurityManager


@pytest_asyncio.fixture
async def gateway():
    """Create a test gateway instance."""
    config = {
        "database_url": "sqlite:///:memory:",
        "enable_monitoring": False,
        "security": {"require_authentication": False},
    }
    gateway = MCPGateway(config=config)
    await gateway.initialize()
    yield gateway
    await gateway.shutdown()


@pytest.fixture
def mock_server():
    """Create a mock MCP server."""
    return MCPServer(
        id="test-server-1",
        name="Test Server",
        transport="stdio",
        config={"command": "echo", "args": ["test"]},
        status=ServerStatus.REGISTERED,
    )


@pytest.fixture
def mock_tool():
    """Create a mock MCP tool."""
    return MCPTool(
        name="test_tool",
        description="A test tool",
        server_id="test-server-1",
        input_schema={"type": "object", "properties": {"input": {"type": "string"}}},
    )


class TestMCPGateway:
    """Test MCP Gateway functionality."""

    @pytest.mark.asyncio
    async def test_gateway_initialization(self, gateway):
        """Test gateway initializes correctly."""
        assert gateway is not None
        assert isinstance(gateway.registry, MCPRegistry)
        assert isinstance(gateway.security, MCPSecurityManager)
        assert gateway._servers == {}
        assert gateway._active_connections == {}

    @pytest.mark.asyncio
    async def test_register_server(self, gateway):
        """Test server registration."""
        server_config = {
            "name": "test-server",
            "transport": "stdio",
            "command": "echo",
            "args": ["hello"],
        }

        server_id = await gateway.register_server(server_config)

        assert server_id is not None
        assert server_id in gateway._servers
        server = gateway._servers[server_id]
        assert server.name == "test-server"
        assert server.status == ServerStatus.REGISTERED

    @pytest.mark.asyncio
    async def test_register_server_invalid_config(self, gateway):
        """Test server registration with invalid config."""
        # Missing required field
        server_config = {"transport": "stdio"}

        with pytest.raises(ValueError, match="Invalid server configuration"):
            await gateway.register_server(server_config)

    @pytest.mark.asyncio
    async def test_register_server_with_permissions(self, gateway):
        """Test server registration with permission check."""
        # Enable authentication
        gateway.security.config["require_authentication"] = True

        server_config = {"name": "test-server", "transport": "stdio", "command": "echo"}

        # Mock permission check to fail
        with patch.object(gateway.security, "can_register_server", return_value=False):
            with pytest.raises(PermissionError):
                await gateway.register_server(server_config, user_id="test-user")

    @pytest.mark.asyncio
    async def test_start_server(self, gateway, mock_server):
        """Test starting a server."""
        # Add server to gateway
        gateway._servers[mock_server.id] = mock_server

        # Mock the service start_server method
        mock_connection = Mock()
        with patch.object(
            gateway.service, "start_server", return_value=mock_connection
        ):
            with patch.object(gateway, "discover_tools", return_value=[]):
                result = await gateway.start_server(mock_server.id)

        assert result["success"] is True
        assert result["status"] == "running"
        assert mock_server.status == ServerStatus.RUNNING
        assert mock_server.id in gateway._active_connections

    @pytest.mark.asyncio
    async def test_start_nonexistent_server(self, gateway):
        """Test starting a server that doesn't exist."""
        with pytest.raises(ValueError, match="Server .* not found"):
            await gateway.start_server("nonexistent-id")

    @pytest.mark.asyncio
    async def test_stop_server(self, gateway, mock_server):
        """Test stopping a server."""
        # Setup server and connection
        gateway._servers[mock_server.id] = mock_server
        mock_connection = Mock()
        gateway._active_connections[mock_server.id] = mock_connection
        mock_server.status = ServerStatus.RUNNING

        # Mock the service stop_server method
        with patch.object(gateway.service, "stop_server", return_value=None):
            result = await gateway.stop_server(mock_server.id)

        assert result["success"] is True
        assert result["status"] == "stopped"
        assert mock_server.status == ServerStatus.STOPPED
        assert mock_server.id not in gateway._active_connections

    @pytest.mark.asyncio
    async def test_discover_tools(self, gateway, mock_server, mock_tool):
        """Test tool discovery."""
        # Setup server and connection
        gateway._servers[mock_server.id] = mock_server
        mock_connection = Mock()
        gateway._active_connections[mock_server.id] = mock_connection

        # Mock service discover_tools
        with patch.object(gateway.service, "discover_tools", return_value=[mock_tool]):
            tools = await gateway.discover_tools(mock_server.id)

        assert len(tools) == 1
        assert tools[0].name == "test_tool"
        assert mock_server.tool_count == 1

    @pytest.mark.asyncio
    async def test_execute_tool(self, gateway, mock_server, mock_tool):
        """Test tool execution."""
        # Setup server, connection, and tool
        gateway._servers[mock_server.id] = mock_server
        mock_connection = Mock()
        gateway._active_connections[mock_server.id] = mock_connection

        # Mock registry get_tool
        with patch.object(gateway.registry, "get_tool", return_value=mock_tool):
            # Mock service execute_tool
            mock_result = {"output": "test result"}
            with patch.object(
                gateway.service, "execute_tool", return_value=mock_result
            ):
                result = await gateway.execute_tool(
                    mock_server.id, "test_tool", {"input": "test"}
                )

        assert result["success"] is True
        assert result["result"] == mock_result
        assert "execution_id" in result
        assert "duration_ms" in result

    @pytest.mark.asyncio
    async def test_execute_tool_server_not_running(
        self, gateway, mock_server, mock_tool
    ):
        """Test tool execution when server is not running."""
        # Setup server but no connection
        gateway._servers[mock_server.id] = mock_server

        with patch.object(gateway.registry, "get_tool", return_value=mock_tool):
            with pytest.raises(RuntimeError, match="Server .* is not running"):
                await gateway.execute_tool(
                    mock_server.id, "test_tool", {"input": "test"}
                )

    @pytest.mark.asyncio
    async def test_list_servers(self, gateway, mock_server):
        """Test listing servers."""
        # Add server to registry
        await gateway.registry.register_server(mock_server)

        servers = await gateway.list_servers()

        assert len(servers) >= 1
        assert any(s.id == mock_server.id for s in servers)

    @pytest.mark.asyncio
    async def test_list_servers_with_filters(self, gateway):
        """Test listing servers with filters."""
        # Add multiple servers
        server1 = MCPServer(
            id="server-1",
            name="Server 1",
            transport="stdio",
            config={},
            status=ServerStatus.RUNNING,
            tags=["prod", "api"],
        )
        server2 = MCPServer(
            id="server-2",
            name="Server 2",
            transport="http",
            config={},
            status=ServerStatus.STOPPED,
            tags=["dev", "test"],
        )

        await gateway.registry.register_server(server1)
        await gateway.registry.register_server(server2)

        # Filter by status
        running_servers = await gateway.list_servers(filters={"status": "running"})
        assert len(running_servers) == 1
        assert running_servers[0].id == "server-1"

        # Filter by transport
        http_servers = await gateway.list_servers(filters={"transport": "http"})
        assert len(http_servers) == 1
        assert http_servers[0].id == "server-2"

        # Filter by tags
        prod_servers = await gateway.list_servers(filters={"tags": ["prod"]})
        assert len(prod_servers) == 1
        assert prod_servers[0].id == "server-1"

    @pytest.mark.asyncio
    async def test_get_server_status(self, gateway, mock_server):
        """Test getting server status."""
        # Setup server and connection
        gateway._servers[mock_server.id] = mock_server
        mock_connection = Mock()
        gateway._active_connections[mock_server.id] = mock_connection

        # Mock health check
        health = {"healthy": True, "response_time_ms": 50}
        with patch.object(gateway.service, "check_health", return_value=health):
            status = await gateway.get_server_status(mock_server.id)

        assert status["server_id"] == mock_server.id
        assert status["name"] == mock_server.name
        assert status["connected"] is True
        assert status["health"] == health

    @pytest.mark.asyncio
    async def test_monitor_servers(self, gateway, mock_server):
        """Test server monitoring."""
        # Enable monitoring
        gateway.config["enable_monitoring"] = True
        gateway.config["monitor_interval"] = 0.1  # Fast interval for testing

        # Setup server and connection
        gateway._servers[mock_server.id] = mock_server
        mock_connection = Mock()
        gateway._active_connections[mock_server.id] = mock_connection
        mock_server.status = ServerStatus.RUNNING

        # Mock health check to return unhealthy
        health = {"healthy": False, "error": "Connection lost"}
        with patch.object(gateway.service, "check_health", return_value=health):
            # Start monitoring
            monitor_task = asyncio.create_task(gateway._monitor_servers())

            # Wait a bit for monitoring to run
            await asyncio.sleep(0.2)

            # Cancel monitoring
            monitor_task.cancel()
            try:
                await monitor_task
            except asyncio.CancelledError:
                pass

        # Check that server status was updated
        assert mock_server.status == ServerStatus.UNHEALTHY

    @pytest.mark.asyncio
    async def test_audit_logging(self, gateway):
        """Test audit logging."""
        # Mock audit node if not available
        if gateway.audit_node is None:
            # Create a mock audit node
            gateway.audit_node = Mock()
            gateway.audit_node.execute = AsyncMock(return_value={"success": True})

        # Mock audit node execution
        with patch.object(
            gateway.audit_node, "execute", return_value={"success": True}
        ) as mock_execute:
            await gateway._audit_log(
                "test_event", "test-user", {"detail": "test"}, severity="low"
            )

            # Verify audit node was called
            mock_execute.assert_called_once()
            call_args = mock_execute.call_args[0][0]
            assert call_args["operation"] == "log_event"
            assert call_args["event_type"] == "mcp_test_event"
            assert call_args["user_id"] == "test-user"


class TestMCPGatewayIntegration:
    """Integration tests for MCP Gateway."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_full_server_lifecycle(self, gateway):
        """Test complete server lifecycle from registration to deletion."""
        # Register server
        server_config = {
            "name": "lifecycle-test",
            "transport": "stdio",
            "command": "echo",
            "args": ["test"],
            "tags": ["test"],
            "description": "Lifecycle test server",
        }

        server_id = await gateway.register_server(server_config, user_id="test-user")
        assert server_id is not None

        # Get server status
        status = await gateway.get_server_status(server_id)
        assert status["status"] == "registered"

        # List servers
        servers = await gateway.list_servers()
        assert any(s.id == server_id for s in servers)

        # Note: Actual start/stop would require a real MCP server process
        # For integration testing, you would need to mock or provide a test server

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_concurrent_operations(self, gateway):
        """Test concurrent server operations."""
        # Register multiple servers concurrently
        server_configs = [
            {
                "name": f"concurrent-test-{i}",
                "transport": "stdio",
                "command": "echo",
                "args": [f"server-{i}"],
            }
            for i in range(5)
        ]

        # Register all servers concurrently
        tasks = [
            gateway.register_server(config, user_id="test-user")
            for config in server_configs
        ]
        server_ids = await asyncio.gather(*tasks)

        assert len(server_ids) == 5
        assert len(set(server_ids)) == 5  # All unique IDs

        # Verify all servers are registered
        servers = await gateway.list_servers()
        registered_ids = {s.id for s in servers}
        assert all(sid in registered_ids for sid in server_ids)
