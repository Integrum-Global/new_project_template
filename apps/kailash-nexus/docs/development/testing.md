# Testing Guide

Comprehensive testing strategies for Nexus multi-channel applications.

## Quick Start

```python
import pytest
from kailash.nexus.testing import NexusTestClient
from kailash_nexus import create_nexus

@pytest.fixture
def nexus_app():
    """Create test Nexus application"""
    return create_nexus(
        title="Test App",
        enable_api=True,
        enable_cli=True,
        enable_mcp=True,
        config={"environment": "test"}
    )

@pytest.fixture
def client(nexus_app):
    """Create test client"""
    return NexusTestClient(nexus_app)

async def test_all_channels(client):
    """Test workflow across all channels"""
    workflow_data = {"message": "Hello, World!"}

    # Test API channel
    api_response = await client.api.post("/workflows/greeting", json=workflow_data)
    assert api_response.status_code == 200

    # Test CLI channel
    cli_result = await client.cli.execute("greeting", workflow_data)
    assert cli_result.success

    # Test MCP channel
    mcp_result = await client.mcp.call_tool("greeting", workflow_data)
    assert mcp_result["success"]
```

## Test Structure

```
tests/
├── unit/              # Fast, isolated tests
│   ├── channels/      # Channel-specific tests
│   ├── workflows/     # Workflow logic tests
│   └── integrations/  # Integration unit tests
├── integration/       # Component interaction tests
│   ├── api/          # API integration tests
│   ├── cli/          # CLI integration tests
│   └── mcp/          # MCP integration tests
├── e2e/              # End-to-end scenarios
│   ├── user_flows/    # Complete user journeys
│   └── performance/   # Load and performance tests
├── fixtures/         # Test data and fixtures
├── conftest.py       # Shared test configuration
└── README.md         # Test documentation
```

## Unit Testing

### Channel Testing
```python
import pytest
from kailash.nexus.channels.api import APIChannel

class TestAPIChannel:
    @pytest.fixture
    def api_channel(self):
        config = {
            "host": "localhost",
            "port": 8000,
            "cors_enabled": True
        }
        return APIChannel(config)

    async def test_route_registration(self, api_channel):
        """Test route registration"""
        workflow_id = "test_workflow"
        api_channel.register_workflow_route(workflow_id, "/test")

        assert "/test" in api_channel.routes
        assert api_channel.routes["/test"]["workflow_id"] == workflow_id

    async def test_request_processing(self, api_channel):
        """Test request processing"""
        with api_channel.mock_workflow("test_workflow") as mock:
            mock.return_value = {"result": "success"}

            response = await api_channel.handle_request({
                "method": "POST",
                "path": "/test",
                "body": {"data": "test"}
            })

            assert response["status"] == 200
            assert response["body"]["result"] == "success"
```

### Workflow Testing
```python
from kailash.workflow.builder import WorkflowBuilder
from kailash.runtime.local import LocalRuntime

class TestWorkflows:
    def test_simple_workflow(self):
        """Test basic workflow construction"""
        workflow = WorkflowBuilder()
        workflow.add_node("HTTPRequestNode", "api_call", {
            "url": "https://api.example.com/data",
            "method": "GET"
        })

        built_workflow = workflow.build()
        assert "api_call" in built_workflow.nodes
        assert built_workflow.nodes["api_call"]["type"] == "HTTPRequestNode"

    async def test_workflow_execution(self):
        """Test workflow execution"""
        workflow = WorkflowBuilder()
        workflow.add_node("PythonCodeNode", "processor", {
            "code": "return {'result': context['input'] * 2}"
        })

        runtime = LocalRuntime()
        results, run_id = runtime.execute(
            workflow.build(),
            parameters={"processor": {"input": 5}}
        )

        assert results["processor"]["result"] == 10
```

## Integration Testing

### Multi-Channel Testing
```python
import asyncio
import pytest
from kailash.nexus.testing import MultiChannelTestClient

class TestMultiChannel:
    @pytest.fixture
    def multi_client(self, nexus_app):
        return MultiChannelTestClient(nexus_app)

    async def test_session_sync(self, multi_client):
        """Test session synchronization across channels"""
        # Start session via API
        api_session = await multi_client.api.create_session()
        session_id = api_session["session_id"]

        # Use same session in CLI
        cli_result = await multi_client.cli.execute(
            "get-session-data",
            session_id=session_id
        )

        # Verify session data is available
        assert cli_result.session_data["session_id"] == session_id

        # Use same session in MCP
        mcp_result = await multi_client.mcp.call_tool(
            "get_session_info",
            {"session_id": session_id}
        )

        assert mcp_result["session_id"] == session_id

    async def test_workflow_consistency(self, multi_client):
        """Test workflow produces consistent results across channels"""
        test_data = {"input": "test message", "multiplier": 3}

        # Execute via API
        api_result = await multi_client.api.post("/workflows/multiply", json=test_data)

        # Execute via CLI
        cli_result = await multi_client.cli.execute("multiply", test_data)

        # Execute via MCP
        mcp_result = await multi_client.mcp.call_tool("multiply", test_data)

        # Results should be identical
        expected_result = test_data["input"] * test_data["multiplier"]
        assert api_result.json()["result"] == expected_result
        assert cli_result.data["result"] == expected_result
        assert mcp_result["result"] == expected_result
```

### Database Integration Testing
```python
import pytest
import asyncpg
from kailash.nexus.testing import DatabaseTestCase

class TestDatabaseIntegration(DatabaseTestCase):
    @pytest.fixture
    async def db_connection(self):
        """Create test database connection"""
        conn = await asyncpg.connect(self.test_database_url)
        yield conn
        await conn.close()

    async def test_data_persistence(self, client, db_connection):
        """Test data persistence across channels"""
        # Create data via API
        create_response = await client.api.post("/users", json={
            "name": "Test User",
            "email": "test@example.com"
        })
        user_id = create_response.json()["id"]

        # Verify in database
        user_row = await db_connection.fetchrow(
            "SELECT * FROM users WHERE id = $1", user_id
        )
        assert user_row["name"] == "Test User"

        # Read via CLI
        cli_result = await client.cli.execute("get-user", {"id": user_id})
        assert cli_result.data["name"] == "Test User"

        # Update via MCP
        await client.mcp.call_tool("update_user", {
            "id": user_id,
            "name": "Updated User"
        })

        # Verify update in database
        updated_row = await db_connection.fetchrow(
            "SELECT * FROM users WHERE id = $1", user_id
        )
        assert updated_row["name"] == "Updated User"
```

## End-to-End Testing

### User Journey Testing
```python
import pytest
from kailash.nexus.testing import E2ETestCase

class TestUserJourneys(E2ETestCase):
    async def test_complete_user_workflow(self, client):
        """Test complete user workflow from API to MCP"""
        # 1. User registers via API
        registration_response = await client.api.post("/auth/register", json={
            "email": "user@example.com",
            "password": "secure123",
            "name": "Test User"
        })
        assert registration_response.status_code == 201
        user_id = registration_response.json()["user_id"]

        # 2. User authenticates via CLI
        auth_result = await client.cli.execute("auth login", {
            "email": "user@example.com",
            "password": "secure123"
        })
        assert auth_result.success
        token = auth_result.data["token"]

        # 3. User creates workflow via authenticated API
        workflow_response = await client.api.post(
            "/workflows",
            json={
                "name": "My Workflow",
                "definition": {"nodes": [], "connections": []}
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        assert workflow_response.status_code == 201
        workflow_id = workflow_response.json()["id"]

        # 4. AI agent executes workflow via MCP
        mcp_result = await client.mcp.call_tool("execute_workflow", {
            "workflow_id": workflow_id,
            "input_data": {"message": "Hello from AI"}
        })
        assert mcp_result["success"]

        # 5. User views results via CLI
        results = await client.cli.execute("workflow results", {
            "workflow_id": workflow_id,
            "token": token
        })
        assert results.success
        assert "Hello from AI" in str(results.data)
```

### Performance Testing
```python
import asyncio
import time
from kailash.nexus.testing import PerformanceTestCase

class TestPerformance(PerformanceTestCase):
    async def test_concurrent_requests(self, client):
        """Test concurrent request handling"""
        async def make_request(i):
            start_time = time.time()
            response = await client.api.post("/workflows/simple", json={
                "data": f"request_{i}"
            })
            end_time = time.time()
            return {
                "request_id": i,
                "status_code": response.status_code,
                "duration": end_time - start_time,
                "success": response.status_code == 200
            }

        # Make 100 concurrent requests
        tasks = [make_request(i) for i in range(100)]
        results = await asyncio.gather(*tasks)

        # Analyze results
        success_count = sum(1 for r in results if r["success"])
        avg_duration = sum(r["duration"] for r in results) / len(results)
        max_duration = max(r["duration"] for r in results)

        # Performance assertions
        assert success_count >= 95  # 95% success rate
        assert avg_duration < 0.5   # Average response < 500ms
        assert max_duration < 2.0   # Max response < 2s

    async def test_memory_usage(self, client):
        """Test memory usage under load"""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # Execute many workflows
        for i in range(1000):
            await client.api.post("/workflows/memory_test", json={
                "iteration": i,
                "data": "x" * 1000  # 1KB payload
            })

        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory

        # Memory should not increase significantly
        assert memory_increase < 100 * 1024 * 1024  # Less than 100MB increase
```

## Test Configuration

### Test Environment Setup
```python
# conftest.py
import asyncio
import pytest
import docker
from pathlib import Path

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def test_infrastructure():
    """Setup test infrastructure (databases, Redis, etc.)"""
    client = docker.from_env()

    # Start test PostgreSQL
    postgres_container = client.containers.run(
        "postgres:15-alpine",
        environment={
            "POSTGRES_DB": "nexus_test",
            "POSTGRES_USER": "test",
            "POSTGRES_PASSWORD": "test"
        },
        ports={"5432/tcp": 5435},
        detach=True,
        remove=True
    )

    # Start test Redis
    redis_container = client.containers.run(
        "redis:7-alpine",
        ports={"6379/tcp": 6381},
        detach=True,
        remove=True
    )

    # Wait for services to be ready
    await asyncio.sleep(5)

    yield {
        "postgres_url": "postgresql://test:test@localhost:5435/nexus_test",
        "redis_url": "redis://localhost:6381/0"
    }

    # Cleanup
    postgres_container.stop()
    redis_container.stop()

@pytest.fixture
def test_config(test_infrastructure):
    """Test configuration"""
    return {
        "database_url": test_infrastructure["postgres_url"],
        "redis_url": test_infrastructure["redis_url"],
        "secret_key": "test-secret-key",
        "environment": "test",
        "log_level": "DEBUG"
    }
```

### Mock Configuration
```python
# test_mocks.py
from unittest.mock import AsyncMock, MagicMock

class MockExternalService:
    """Mock external service for testing"""
    def __init__(self):
        self.calls = []
        self.responses = {}

    def set_response(self, method, endpoint, response):
        """Set mock response for method/endpoint"""
        self.responses[(method, endpoint)] = response

    async def make_request(self, method, endpoint, data=None):
        """Mock HTTP request"""
        self.calls.append((method, endpoint, data))
        return self.responses.get((method, endpoint), {"status": "ok"})

@pytest.fixture
def mock_external_service():
    return MockExternalService()
```

## Testing Best Practices

1. **Test Isolation**: Each test should be independent and not affect others
2. **Realistic Data**: Use realistic test data that matches production scenarios
3. **Error Cases**: Test error conditions and edge cases
4. **Performance**: Include performance tests for critical workflows
5. **Channel Parity**: Test all channels to ensure consistent behavior
6. **Session Management**: Test session handling and synchronization
7. **Security**: Test authentication, authorization, and input validation
8. **Monitoring**: Test that metrics and health checks work correctly

## Continuous Integration

### GitHub Actions Example
```yaml
name: Nexus Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test
          POSTGRES_DB: nexus_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        pip install -e .
        pip install pytest pytest-asyncio pytest-cov

    - name: Run tests
      run: |
        pytest tests/ --cov=nexus --cov-report=xml
      env:
        DATABASE_URL: postgresql://postgres:test@localhost/nexus_test
        REDIS_URL: redis://localhost:6379/0

    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

## Test Utilities

### Custom Assertions
```python
def assert_workflow_success(result):
    """Assert workflow executed successfully"""
    assert result["status"] == "success"
    assert "error" not in result
    assert "result" in result

def assert_api_response(response, expected_status=200):
    """Assert API response format"""
    assert response.status_code == expected_status
    assert response.headers["Content-Type"] == "application/json"

    if expected_status == 200:
        data = response.json()
        assert "status" in data
        assert data["status"] == "success"

def assert_session_valid(session_data):
    """Assert session data is valid"""
    assert "session_id" in session_data
    assert "created_at" in session_data
    assert "expires_at" in session_data
    assert session_data["session_id"] is not None
```

## Debugging Tests

### Test Debugging Tools
```python
import logging
from kailash.nexus.testing import TestDebugger

class TestWithDebugging:
    def setup_method(self):
        """Setup debugging for each test"""
        self.debugger = TestDebugger()
        self.debugger.enable_request_logging()
        self.debugger.enable_workflow_tracing()

    async def test_with_debugging(self, client):
        """Test with comprehensive debugging"""
        with self.debugger.trace_requests():
            response = await client.api.post("/workflows/debug", json={
                "debug": True,
                "trace_level": "detailed"
            })

        # Access debug information
        request_trace = self.debugger.get_request_trace()
        workflow_trace = self.debugger.get_workflow_trace()

        # Assertions with debug context
        if not response.status_code == 200:
            self.debugger.dump_debug_info()
            pytest.fail(f"Request failed: {response.text}")
```

## Next Steps

- **Workflow Development**: [Workflow Guide](workflow-guide.md) - Build testable workflows
- **Integrations**: [Custom Integrations](integrations.md) - Test integration patterns
- **Performance**: [Performance Guide](../advanced/performance.md) - Optimize and benchmark
- **Monitoring**: [Monitoring & Operations](../enterprise/monitoring.md) - Production observability
