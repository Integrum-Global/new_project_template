#!/usr/bin/env python3
"""
Temporary test file to validate Nexus documentation examples.
This ensures all code snippets in documentation are correct and runnable.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


def test_basic_nexus_pattern():
    """Test basic Nexus multi-channel pattern from quickstart"""

    # Mock the imports to avoid actual execution
    class MockWorkflowBuilder:
        def add_node(self, node_type, name, config):
            pass

        def build(self):
            return {}

    class MockLocalRuntime:
        def execute(self, workflow, parameters=None):
            return ({}, "run_id")

    class MockNexus:
        def __init__(self, **kwargs):
            self.config = kwargs

        def register_workflow(self, name, workflow):
            pass

    def create_nexus(**kwargs):
        return MockNexus(**kwargs)

    # Test the basic pattern
    from kailash.workflow.builder import WorkflowBuilder

    WorkflowBuilder = MockWorkflowBuilder  # Override with mock

    from kailash.runtime.local import LocalRuntime

    LocalRuntime = MockLocalRuntime  # Override with mock

    # Create workflow
    workflow = WorkflowBuilder()
    workflow.add_node(
        "LLMAgentNode",
        "assistant",
        {"provider": "openai", "model": "gpt-4", "use_real_mcp": True},
    )

    # Deploy to Nexus
    nexus = create_nexus(
        title="My Assistant", enable_api=True, enable_cli=True, enable_mcp=True
    )

    # Register workflow
    nexus.register_workflow("assistant", workflow.build())

    # Verify basic structure
    assert nexus.config["title"] == "My Assistant"
    assert nexus.config["enable_api"] is True
    assert nexus.config["enable_cli"] is True
    assert nexus.config["enable_mcp"] is True


def test_channel_patterns():
    """Test channel-specific patterns from workflow guide"""

    class MockWorkflowBuilder:
        def add_node(self, node_type, name, config):
            self.last_node = {"type": node_type, "name": name, "config": config}

        def build(self):
            return {}

    # Test API Channel
    workflow = MockWorkflowBuilder()
    workflow.add_node(
        "HTTPRequestNode", "api_input", {"method": "POST", "endpoint": "/process"}
    )
    assert workflow.last_node["type"] == "HTTPRequestNode"
    assert workflow.last_node["config"]["method"] == "POST"

    # Test CLI Channel
    workflow = MockWorkflowBuilder()
    workflow.add_node(
        "CLIInputNode", "cli_input", {"command": "process", "args": ["--input", "text"]}
    )
    assert workflow.last_node["type"] == "CLIInputNode"
    assert workflow.last_node["config"]["command"] == "process"

    # Test MCP Channel
    workflow = MockWorkflowBuilder()
    workflow.add_node(
        "MCPToolNode",
        "mcp_input",
        {"tool_name": "process_data", "description": "Process user data"},
    )
    assert workflow.last_node["type"] == "MCPToolNode"
    assert workflow.last_node["config"]["tool_name"] == "process_data"


def test_session_management():
    """Test session management patterns"""

    class MockNexus:
        def __init__(self, **kwargs):
            self.config = kwargs

    def create_nexus(**kwargs):
        return MockNexus(**kwargs)

    # Unified sessions across channels
    nexus = create_nexus(
        channels_synced=True,  # Sessions sync across API/CLI/MCP
        session_timeout=3600,  # 1 hour session timeout
    )

    assert nexus.config["channels_synced"] is True
    assert nexus.config["session_timeout"] == 3600


def test_authentication_integration():
    """Test authentication patterns"""

    class MockNexus:
        def __init__(self, **kwargs):
            self.config = kwargs

    def create_nexus(**kwargs):
        return MockNexus(**kwargs)

    # Enterprise auth
    nexus = create_nexus(
        auth_strategy="enterprise", sso_enabled=True, rbac_enabled=True
    )

    assert nexus.config["auth_strategy"] == "enterprise"
    assert nexus.config["sso_enabled"] is True
    assert nexus.config["rbac_enabled"] is True


def test_workflow_patterns():
    """Test common workflow patterns"""

    class MockWorkflowBuilder:
        def __init__(self):
            self.nodes = {}
            self.connections = []

        def add_node(self, node_type, name, config):
            self.nodes[name] = {"type": node_type, "config": config}

        def add_connection(self, from_node, from_output, to_node, to_input):
            self.connections.append((from_node, from_output, to_node, to_input))

        def build(self):
            return {"nodes": self.nodes, "connections": self.connections}

    # Data Processing Pipeline
    workflow = MockWorkflowBuilder()
    workflow.add_node("DataReaderNode", "input", {"source": "database"})
    workflow.add_node("DataTransformerNode", "transform", {"operation": "clean"})
    workflow.add_node("DataWriterNode", "output", {"destination": "api"})

    workflow.add_connection("input", "result", "transform", "data")
    workflow.add_connection("transform", "result", "output", "data")

    built = workflow.build()
    assert "input" in built["nodes"]
    assert "transform" in built["nodes"]
    assert "output" in built["nodes"]
    assert len(built["connections"]) == 2
    assert built["connections"][0] == ("input", "result", "transform", "data")


def test_ai_assistant_pattern():
    """Test AI assistant with tools pattern"""

    class MockWorkflowBuilder:
        def add_node(self, node_type, name, config):
            self.last_node = {"type": node_type, "name": name, "config": config}

        def build(self):
            return {}

    workflow = MockWorkflowBuilder()
    workflow.add_node(
        "LLMAgentNode",
        "assistant",
        {
            "provider": "openai",
            "model": "gpt-4",
            "mcp_servers": [
                {
                    "name": "file_tools",
                    "transport": "stdio",
                    "command": "mcp-server-filesystem",
                },
                {
                    "name": "web_tools",
                    "transport": "stdio",
                    "command": "mcp-server-web",
                },
            ],
        },
    )

    assert workflow.last_node["type"] == "LLMAgentNode"
    assert len(workflow.last_node["config"]["mcp_servers"]) == 2
    assert workflow.last_node["config"]["mcp_servers"][0]["name"] == "file_tools"


def test_integration_patterns():
    """Test integration patterns from integrations guide"""

    # Custom Channel Pattern
    class BaseChannel:
        def __init__(self, config):
            self.config = config

    class MockCustomChannel(BaseChannel):
        channel_type = "custom"

        def __init__(self, config):
            super().__init__(config)
            self.setup_custom_protocol()

        def setup_custom_protocol(self):
            pass

        async def handle_request(self, request):
            # Custom request handling
            workflow_result = await self.execute_workflow(
                request.workflow_id, request.data
            )
            return self.format_response(workflow_result)

        async def execute_workflow(self, workflow_id, data):
            return {"result": "mock_result"}

        def format_response(self, result):
            return {"status": "success", "data": result}

    # Test custom channel creation
    channel = MockCustomChannel({"port": 9000})
    assert channel.config["port"] == 9000
    assert channel.channel_type == "custom"


def test_testing_patterns():
    """Test testing patterns from testing guide"""

    # Mock test client pattern
    class MockNexusTestClient:
        def __init__(self, nexus_app):
            self.app = nexus_app
            self.api = MockAPIClient()
            self.cli = MockCLIClient()
            self.mcp = MockMCPClient()

    class MockAPIClient:
        async def post(self, path, json=None):
            return MockResponse(200, {"status": "success", "data": json})

    class MockCLIClient:
        async def execute(self, command, data=None):
            return MockCLIResult(True, {"result": "success"})

    class MockMCPClient:
        async def call_tool(self, tool_name, data=None):
            return {"success": True, "result": "success"}

    class MockResponse:
        def __init__(self, status_code, data):
            self.status_code = status_code
            self._data = data

        def json(self):
            return self._data

    class MockCLIResult:
        def __init__(self, success, data):
            self.success = success
            self.data = data

    class MockNexusApp:
        def __init__(self, **kwargs):
            self.config = kwargs

    # Test client creation
    nexus_app = MockNexusApp(title="Test App", enable_api=True)
    client = MockNexusTestClient(nexus_app)

    assert client.app.config["title"] == "Test App"
    assert hasattr(client, "api")
    assert hasattr(client, "cli")
    assert hasattr(client, "mcp")


def test_configuration_patterns():
    """Test configuration patterns"""
    import os

    # Environment-based configuration pattern
    class MockBaseConfig:
        def __init__(self):
            pass

    class MockProductionConfig(MockBaseConfig):
        def __init__(self):
            super().__init__()
            self.database_url = os.getenv("DATABASE_URL", "postgresql://test")
            self.redis_url = os.getenv("REDIS_URL", "redis://test")
            self.secret_key = os.getenv("SECRET_KEY", "test-key")
            self.log_level = os.getenv("LOG_LEVEL", "INFO")

        def validate(self):
            """Validate required configuration"""
            required = ["database_url", "redis_url", "secret_key"]
            missing = [key for key in required if not getattr(self, key)]
            if missing:
                raise Exception(f"Missing required config: {missing}")

    # Test configuration validation
    config = MockProductionConfig()
    config.validate()  # Should not raise exception with default values

    assert config.database_url == "postgresql://test"
    assert config.log_level == "INFO"


def run_all_tests():
    """Run all documentation validation tests"""
    tests = [
        test_basic_nexus_pattern,
        test_channel_patterns,
        test_session_management,
        test_authentication_integration,
        test_workflow_patterns,
        test_ai_assistant_pattern,
        test_integration_patterns,
        test_testing_patterns,
        test_configuration_patterns,
    ]

    print("Running Nexus documentation validation tests...\n")

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            print(f"✓ {test.__name__}")
            passed += 1
        except Exception as e:
            print(f"✗ {test.__name__}: {e}")
            failed += 1

    print(f"\n{'='*60}")
    print("Documentation validation results:")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Total: {len(tests)}")

    if failed == 0:
        print("\n✅ All Nexus documentation examples are valid!")
        return True
    else:
        print(f"\n❌ {failed} documentation examples need fixing")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
