# Kailash Nexus - Tier 1 & Tier 2 Tests

## Overview
This document defines Tier 1 (unit) and Tier 2 (integration) tests derived from the Tier 3 E2E tests. These tests ensure individual components and their integrations work correctly before full E2E validation.

## Test Organization

Following the Kailash SDK test organization policy:
- **Tier 1 Location**: `apps/kailash-nexus/tests/unit/`
- **Tier 2 Location**: `apps/kailash-nexus/tests/integration/`
- **Naming**:
  - Unit: `test_unit_{component}_{function}.py`
  - Integration: `test_integration_{feature}_{scenario}.py`

## Tier 1: Unit Tests

### 1. Core Application Components

#### Test 1.1: Nexus Application Core
```python
# tests/unit/test_unit_nexus_application.py
import pytest
from unittest.mock import Mock, AsyncMock
from kailash_nexus.core.application import NexusApplication

class TestNexusApplication:
    """Unit tests for core Nexus application."""

    @pytest.mark.unit
    @pytest.mark.tier1
    async def test_application_initialization(self):
        """Test Nexus application initializes with correct defaults."""
        app = NexusApplication()

        assert app.name == "nexus"
        assert app.channels == {}
        assert app.config is not None
        assert app.state == "initialized"

    @pytest.mark.unit
    @pytest.mark.tier1
    async def test_channel_registration(self):
        """Test channel registration and management."""
        app = NexusApplication()
        mock_channel = Mock()

        app.register_channel("api", mock_channel)

        assert "api" in app.channels
        assert app.channels["api"] == mock_channel

    @pytest.mark.unit
    @pytest.mark.tier1
    async def test_configuration_loading(self):
        """Test configuration loading and validation."""
        config = {
            "name": "test-nexus",
            "channels": {"api": {"enabled": True}},
            "features": {"multi_tenant": True}
        }

        app = NexusApplication(config=config)

        assert app.name == "test-nexus"
        assert app.config["features"]["multi_tenant"] == True
```

#### Test 1.2: Session Management
```python
# tests/unit/test_unit_session_management.py
import pytest
from kailash_nexus.core.session import SessionManager, Session

class TestSessionManagement:
    """Unit tests for session management."""

    @pytest.mark.unit
    @pytest.mark.tier1
    def test_session_creation(self):
        """Test session creation with metadata."""
        manager = SessionManager()

        session = manager.create_session(
            user_id="user123",
            metadata={"channel": "api", "tenant": "tenant1"}
        )

        assert session.id is not None
        assert session.user_id == "user123"
        assert session.metadata["tenant"] == "tenant1"
        assert session.is_active == True

    @pytest.mark.unit
    @pytest.mark.tier1
    def test_session_isolation(self):
        """Test sessions are properly isolated."""
        manager = SessionManager()

        session1 = manager.create_session("user1", {"tenant": "A"})
        session2 = manager.create_session("user2", {"tenant": "B"})

        # Verify isolation
        assert session1.id != session2.id
        assert manager.get_session(session1.id).metadata["tenant"] == "A"
        assert manager.get_session(session2.id).metadata["tenant"] == "B"

    @pytest.mark.unit
    @pytest.mark.tier1
    async def test_session_expiration(self):
        """Test session expiration handling."""
        manager = SessionManager(ttl=1)  # 1 second TTL

        session = manager.create_session("user123")
        assert session.is_active == True

        await asyncio.sleep(1.1)

        expired_session = manager.get_session(session.id)
        assert expired_session is None
```

### 2. Channel Components

#### Test 2.1: API Channel
```python
# tests/unit/test_unit_api_channel.py
import pytest
from unittest.mock import Mock
from kailash_nexus.channels.api import APIChannel
from kailash.servers.gateway import EnterpriseWorkflowServer

class TestAPIChannel:
    """Unit tests for API channel."""

    @pytest.mark.unit
    @pytest.mark.tier1
    def test_api_channel_creation(self):
        """Test API channel initialization."""
        mock_server = Mock(spec=EnterpriseWorkflowServer)
        channel = APIChannel(server=mock_server)

        assert channel.type == "api"
        assert channel.server == mock_server
        assert channel.is_ready == False

    @pytest.mark.unit
    @pytest.mark.tier1
    async def test_api_request_routing(self):
        """Test request routing to workflows."""
        mock_server = Mock(spec=EnterpriseWorkflowServer)
        mock_server.execute_workflow = AsyncMock(return_value={"result": "success"})

        channel = APIChannel(server=mock_server)

        result = await channel.route_request(
            method="POST",
            path="/workflows/test-workflow/execute",
            body={"input": "data"}
        )

        assert result["result"] == "success"
        mock_server.execute_workflow.assert_called_once()
```

#### Test 2.2: CLI Channel
```python
# tests/unit/test_unit_cli_channel.py
import pytest
from kailash_nexus.channels.cli import CLIChannel, CommandParser

class TestCLIChannel:
    """Unit tests for CLI channel."""

    @pytest.mark.unit
    @pytest.mark.tier1
    def test_command_parsing(self):
        """Test CLI command parsing."""
        parser = CommandParser()

        # Test workflow execution command
        args = parser.parse("nexus execute my-workflow --input='{\"key\":\"value\"}'")

        assert args.command == "execute"
        assert args.workflow == "my-workflow"
        assert args.input == {"key": "value"}

    @pytest.mark.unit
    @pytest.mark.tier1
    def test_command_validation(self):
        """Test command validation."""
        parser = CommandParser()

        # Valid command
        assert parser.validate("nexus list workflows") == True

        # Invalid command
        with pytest.raises(ValueError):
            parser.parse("nexus invalid-command")
```

#### Test 2.3: MCP Channel
```python
# tests/unit/test_unit_mcp_channel.py
import pytest
from unittest.mock import Mock
from kailash_nexus.channels.mcp import MCPChannel
from kailash.middleware.mcp import MiddlewareMCPServer

class TestMCPChannel:
    """Unit tests for MCP channel."""

    @pytest.mark.unit
    @pytest.mark.tier1
    def test_tool_registration(self):
        """Test MCP tool registration from workflows."""
        mock_server = Mock(spec=MiddlewareMCPServer)
        channel = MCPChannel(server=mock_server)

        # Register workflow as tool
        channel.register_workflow_as_tool(
            workflow_id="data-processor",
            description="Process data",
            parameters={"data": {"type": "string"}}
        )

        assert "workflow_data-processor" in channel.registered_tools

    @pytest.mark.unit
    @pytest.mark.tier1
    async def test_tool_discovery(self):
        """Test tool discovery response."""
        channel = MCPChannel()
        channel.registered_tools = {
            "tool1": {"description": "Tool 1"},
            "tool2": {"description": "Tool 2"}
        }

        tools = await channel.discover_tools()

        assert len(tools) == 2
        assert any(t["name"] == "tool1" for t in tools)
```

### 3. Enterprise Feature Components

#### Test 3.1: Multi-Tenant Manager
```python
# tests/unit/test_unit_multi_tenant.py
import pytest
from kailash_nexus.enterprise.multi_tenant import TenantManager, Tenant

class TestMultiTenantManager:
    """Unit tests for multi-tenant management."""

    @pytest.mark.unit
    @pytest.mark.tier1
    def test_tenant_creation(self):
        """Test tenant creation with isolation."""
        manager = TenantManager()

        tenant = manager.create_tenant(
            name="test-tenant",
            config={
                "isolation": "strict",
                "quotas": {"workflows": 10}
            }
        )

        assert tenant.id is not None
        assert tenant.name == "test-tenant"
        assert tenant.config["isolation"] == "strict"

    @pytest.mark.unit
    @pytest.mark.tier1
    def test_tenant_isolation_enforcement(self):
        """Test tenant isolation is enforced."""
        manager = TenantManager()

        tenant1 = manager.create_tenant("tenant1")
        tenant2 = manager.create_tenant("tenant2")

        # Create resource in tenant1
        resource = manager.create_resource(tenant1.id, "workflow", {"name": "test"})

        # Verify tenant2 cannot access
        with pytest.raises(PermissionError):
            manager.access_resource(resource.id, tenant_id=tenant2.id)
```

#### Test 3.2: Authentication Manager
```python
# tests/unit/test_unit_authentication.py
import pytest
from kailash_nexus.enterprise.auth import AuthenticationManager

class TestAuthenticationManager:
    """Unit tests for authentication."""

    @pytest.mark.unit
    @pytest.mark.tier1
    def test_api_key_generation(self):
        """Test API key generation and validation."""
        auth_manager = AuthenticationManager()

        # Generate API key
        api_key = auth_manager.generate_api_key(
            app_name="test-app",
            permissions=["read", "write"]
        )

        assert api_key is not None
        assert len(api_key) >= 32

        # Validate API key
        auth_context = auth_manager.validate_api_key(api_key)
        assert auth_context["app_name"] == "test-app"
        assert "read" in auth_context["permissions"]

    @pytest.mark.unit
    @pytest.mark.tier1
    def test_jwt_token_validation(self):
        """Test JWT token generation and validation."""
        auth_manager = AuthenticationManager(secret="test-secret")

        # Generate token
        token = auth_manager.generate_jwt(
            user_id="user123",
            claims={"role": "admin"}
        )

        # Validate token
        claims = auth_manager.validate_jwt(token)
        assert claims["user_id"] == "user123"
        assert claims["role"] == "admin"
```

## Tier 2: Integration Tests

### 1. Channel Integration Tests

#### Test 1.1: API-CLI Integration
```python
# tests/integration/test_integration_api_cli.py
import pytest
from kailash_nexus import create_nexus

class TestAPICLIIntegration:
    """Integration tests for API and CLI channels."""

    @pytest.mark.integration
    @pytest.mark.tier2
    async def test_workflow_creation_via_cli_execution_via_api(self):
        """Test workflow created via CLI can be executed via API."""
        # Start Nexus with both channels
        nexus = await create_nexus(
            enable_api=True,
            enable_cli=True,
            test_mode=True
        )

        # Create workflow via CLI
        cli_result = await nexus.cli.execute(
            "create workflow test-integration --template=echo"
        )
        workflow_id = cli_result["workflow_id"]

        # Execute via API
        api_client = nexus.create_api_client()
        api_result = await api_client.execute_workflow(
            workflow_id,
            {"message": "Hello from API"}
        )

        assert api_result["result"]["echo"] == "Hello from API"

        # Verify execution visible in CLI
        history = await nexus.cli.execute("history --workflow=" + workflow_id)
        assert len(history["executions"]) == 1
        assert history["executions"][0]["channel"] == "api"
```

#### Test 1.2: MCP-API Integration
```python
# tests/integration/test_integration_mcp_api.py
import pytest
from kailash_nexus import create_nexus

class TestMCPAPIIntegration:
    """Integration tests for MCP and API channels."""

    @pytest.mark.integration
    @pytest.mark.tier2
    async def test_mcp_tool_execution_tracked_via_api(self):
        """Test MCP tool executions are visible via API."""
        nexus = await create_nexus(
            enable_api=True,
            enable_mcp=True,
            test_mode=True
        )

        # Register workflow
        workflow = await nexus.register_workflow(
            "data-analyzer",
            create_test_workflow()
        )

        # Execute via MCP
        mcp_client = nexus.create_mcp_client()
        mcp_result = await mcp_client.execute_tool(
            f"workflow_{workflow.id}",
            {"data": "test-data"}
        )

        # Check execution via API
        api_client = nexus.create_api_client()
        executions = await api_client.get_workflow_executions(workflow.id)

        assert len(executions) == 1
        assert executions[0]["channel"] == "mcp"
        assert executions[0]["status"] == "completed"
```

### 2. Enterprise Integration Tests

#### Test 2.1: Multi-Tenant Session Integration
```python
# tests/integration/test_integration_multi_tenant_session.py
import pytest
from kailash_nexus import create_nexus

class TestMultiTenantSessionIntegration:
    """Integration tests for multi-tenant sessions."""

    @pytest.mark.integration
    @pytest.mark.tier2
    @pytest.mark.enterprise
    async def test_tenant_session_isolation_across_channels(self):
        """Test tenant sessions are isolated across all channels."""
        nexus = await create_nexus(
            enable_api=True,
            enable_cli=True,
            enable_mcp=True,
            multi_tenant=True
        )

        # Create two tenants
        tenant1 = await nexus.create_tenant("tenant1")
        tenant2 = await nexus.create_tenant("tenant2")

        # Create sessions for each tenant
        session1 = await nexus.create_session(
            user="user1@tenant1",
            tenant_id=tenant1.id
        )
        session2 = await nexus.create_session(
            user="user2@tenant2",
            tenant_id=tenant2.id
        )

        # Deploy workflow in tenant1
        workflow = await nexus.deploy_workflow(
            "tenant1-workflow",
            session_id=session1.id
        )

        # Verify tenant2 cannot access via any channel
        # API
        api_client2 = nexus.create_api_client(session_id=session2.id)
        with pytest.raises(PermissionError):
            await api_client2.execute_workflow(workflow.id)

        # CLI
        with pytest.raises(PermissionError):
            await nexus.cli.execute(
                f"execute {workflow.id}",
                session_id=session2.id
            )

        # MCP
        mcp_client2 = nexus.create_mcp_client(session_id=session2.id)
        tools = await mcp_client2.discover_tools()
        assert f"workflow_{workflow.id}" not in [t["name"] for t in tools]
```

#### Test 2.2: Authentication Integration
```python
# tests/integration/test_integration_authentication.py
import pytest
from kailash_nexus import create_nexus

class TestAuthenticationIntegration:
    """Integration tests for authentication across channels."""

    @pytest.mark.integration
    @pytest.mark.tier2
    @pytest.mark.enterprise
    async def test_sso_authentication_flow(self):
        """Test SSO authentication works across all channels."""
        nexus = await create_nexus(
            enable_api=True,
            enable_cli=True,
            enable_mcp=True,
            auth_provider="mock_sso"
        )

        # Simulate SSO login
        sso_token = await nexus.auth.sso_login(
            username="test@example.com",
            provider="okta"
        )

        # Verify token works across channels
        # API
        api_client = nexus.create_api_client(auth={"sso": sso_token})
        api_result = await api_client.whoami()
        assert api_result["user"] == "test@example.com"

        # CLI
        cli_result = await nexus.cli.execute(
            "whoami",
            auth={"sso": sso_token}
        )
        assert cli_result["user"] == "test@example.com"

        # MCP
        mcp_client = nexus.create_mcp_client(auth={"sso": sso_token})
        mcp_session = await mcp_client.connect()
        assert mcp_session["authenticated"] == True
```

### 3. Performance Integration Tests

#### Test 3.1: Load Distribution
```python
# tests/integration/test_integration_load_distribution.py
import pytest
import asyncio
from kailash_nexus import create_nexus

class TestLoadDistribution:
    """Integration tests for load distribution."""

    @pytest.mark.integration
    @pytest.mark.tier2
    @pytest.mark.performance
    async def test_concurrent_channel_load(self):
        """Test system handles concurrent load across channels."""
        nexus = await create_nexus(
            enable_api=True,
            enable_cli=True,
            enable_mcp=True,
            workers=4
        )

        # Create test workflow
        workflow = await nexus.register_workflow(
            "load-test",
            create_load_test_workflow()
        )

        # Generate concurrent load
        async def api_load():
            client = nexus.create_api_client()
            for _ in range(100):
                await client.execute_workflow(workflow.id)

        async def cli_load():
            for _ in range(100):
                await nexus.cli.execute(f"execute {workflow.id}")

        async def mcp_load():
            client = nexus.create_mcp_client()
            for _ in range(100):
                await client.execute_tool(f"workflow_{workflow.id}")

        # Run concurrently
        start_time = asyncio.get_event_loop().time()
        await asyncio.gather(
            api_load(),
            cli_load(),
            mcp_load()
        )
        duration = asyncio.get_event_loop().time() - start_time

        # Verify performance
        assert duration < 30  # 300 requests in 30 seconds

        # Check all executions completed
        stats = await nexus.get_execution_stats()
        assert stats["total"] == 300
        assert stats["failed"] == 0
```

## Test Utilities

### Common Test Fixtures
```python
# tests/conftest.py
import pytest
from kailash.workflow.builder import WorkflowBuilder

@pytest.fixture
def echo_workflow():
    """Simple echo workflow for testing."""
    builder = WorkflowBuilder()
    builder.add_node("PythonCodeNode", "echo", {
        "code": "result = {'echo': input_data.get('message', 'Hello')}"
    })
    return builder.build()

@pytest.fixture
def complex_workflow():
    """Complex multi-node workflow for testing."""
    builder = WorkflowBuilder()
    builder.add_node("HTTPRequestNode", "fetch", {
        "url": "https://api.example.com/data"
    })
    builder.add_node("PythonCodeNode", "process", {
        "code": "result = {'processed': len(data)}"
    })
    builder.add_connection("fetch", "response", "process", "data")
    return builder.build()
```

## Coverage Requirements

### Unit Test Coverage (Tier 1)
- **Target**: 90% code coverage
- **Focus**: Business logic, error handling, edge cases
- **Exclusions**: Integration points, external dependencies

### Integration Test Coverage (Tier 2)
- **Target**: 80% feature coverage
- **Focus**: Component interactions, data flow, error propagation
- **Exclusions**: External services (use mocks)

## Next Steps
These Tier 1 & 2 tests will:
1. Guide component implementation
2. Ensure code quality before E2E testing
3. Enable rapid development with confidence
4. Provide regression protection
5. Support continuous integration
