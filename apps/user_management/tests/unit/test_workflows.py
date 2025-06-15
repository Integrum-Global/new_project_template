"""
Unit tests for User Management workflows

Tests the workflow definitions and registry functionality.
"""

import asyncio
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest

from apps.user_management.workflows.registry import WorkflowRegistry
from kailash.middleware import AgentUIMiddleware
from kailash.runtime.local import LocalRuntime
from kailash.workflow import WorkflowBuilder


class TestWorkflowRegistry:
    """Test WorkflowRegistry functionality."""

    @pytest.fixture
    async def test_agent_ui(self):
        """Create test AgentUIMiddleware."""
        agent_ui = AgentUIMiddleware(
            max_sessions=10, session_timeout_minutes=30, enable_persistence=False
        )
        return agent_ui

    @pytest.fixture
    async def workflow_registry(self, test_agent_ui):
        """Create WorkflowRegistry for testing."""
        return WorkflowRegistry(test_agent_ui)

    @pytest.mark.asyncio
    async def test_workflow_registry_initialization(self, workflow_registry):
        """Test workflow registry initialization."""
        assert workflow_registry.agent_ui is not None
        assert workflow_registry.workflows == {}

    @pytest.mark.asyncio
    async def test_register_all_workflows(self, workflow_registry):
        """Test registering all workflows."""
        # Mock the agent_ui.register_workflow_template method
        mock_workflow_id = str(uuid.uuid4())
        workflow_registry.agent_ui.register_workflow_template = AsyncMock(
            return_value=mock_workflow_id
        )

        await workflow_registry.register_all_workflows()

        # Check that workflows were registered
        assert len(workflow_registry.workflows) > 0
        assert "user_creation" in workflow_registry.workflows
        assert "authentication" in workflow_registry.workflows
        assert "user_update" in workflow_registry.workflows
        assert "user_deletion" in workflow_registry.workflows
        assert "role_management" in workflow_registry.workflows
        assert "permission_check" in workflow_registry.workflows
        assert "gdpr_compliance" in workflow_registry.workflows
        assert "admin_statistics" in workflow_registry.workflows

    @pytest.mark.asyncio
    async def test_user_creation_workflow_structure(self, workflow_registry):
        """Test user creation workflow structure."""
        # Access the private method to test workflow structure
        mock_register = AsyncMock(return_value="test_id")
        workflow_registry.agent_ui.register_workflow_template = mock_register

        await workflow_registry._register_user_creation_workflow()

        # Verify the workflow was registered
        mock_register.assert_called_once()
        call_args = mock_register.call_args

        assert call_args[0][0] == "user_creation_enterprise"
        workflow_def = call_args[0][1]

        # Verify workflow structure
        assert workflow_def["name"] == "user_creation_enterprise"
        assert "nodes" in workflow_def
        assert "connections" in workflow_def

        # Check for required nodes
        node_types = [node["type"] for node in workflow_def["nodes"]]
        assert "PythonCodeNode" in node_types
        assert "ABACPermissionEvaluatorNode" in node_types
        assert "UserManagementNode" in node_types
        assert "SSOAuthenticationNode" in node_types
        assert "MultiFactorAuthNode" in node_types
        assert "AuditLogNode" in node_types

    @pytest.mark.asyncio
    async def test_authentication_workflow_structure(self, workflow_registry):
        """Test authentication workflow structure."""
        mock_register = AsyncMock(return_value="test_id")
        workflow_registry.agent_ui.register_workflow_template = mock_register

        await workflow_registry._register_user_authentication_workflow()

        mock_register.assert_called_once()
        call_args = mock_register.call_args
        workflow_def = call_args[0][1]

        # Check for security-focused nodes
        node_types = [node["type"] for node in workflow_def["nodes"]]
        assert "BehaviorAnalysisNode" in node_types
        assert "ThreatDetectionNode" in node_types
        assert "EnterpriseAuthProviderNode" in node_types
        assert "SessionManagementNode" in node_types
        assert "SecurityEventNode" in node_types


class TestWorkflowExecution:
    """Test workflow execution scenarios."""

    @pytest.fixture
    async def test_runtime(self):
        """Create test runtime."""
        return LocalRuntime(enable_async=True, enable_monitoring=False, debug=True)

    @pytest.mark.asyncio
    async def test_simple_validation_workflow(self, test_runtime):
        """Test a simple validation workflow."""
        # Build a simple workflow for testing
        builder = WorkflowBuilder("test_validation")

        builder.add_node(
            "PythonCodeNode",
            "validate",
            {
                "name": "validate_input",
                "code": """
# Validate user input
valid = True
errors = []

if not input_data.get("email"):
    valid = False
    errors.append("Email is required")

if not input_data.get("first_name"):
    valid = False
    errors.append("First name is required")

result = {
    "result": {
        "valid": valid,
        "errors": errors,
        "data": input_data
    }
}
""",
            },
        )

        workflow = builder.build()

        # Test with valid data
        results, _ = await test_runtime.execute(
            workflow,
            parameters={
                "input_data": {
                    "email": "test@example.com",
                    "first_name": "Test",
                    "last_name": "User",
                }
            },
        )

        validation_result = results["validate"]["result"]
        assert validation_result["valid"] is True
        assert len(validation_result["errors"]) == 0

        # Test with invalid data
        results, _ = await test_runtime.execute(
            workflow,
            parameters={
                "input_data": {"last_name": "User"}  # Missing email and first_name
            },
        )

        validation_result = results["validate"]["result"]
        assert validation_result["valid"] is False
        assert len(validation_result["errors"]) == 2

    @pytest.mark.asyncio
    async def test_workflow_with_connections(self, test_runtime):
        """Test workflow with node connections."""
        builder = WorkflowBuilder("test_connected")

        # First node: validation
        builder.add_node(
            "PythonCodeNode",
            "validate",
            {
                "name": "validate_user",
                "code": """
valid = input_data.get("email") and "@" in input_data.get("email", "")
result = {
    "result": {
        "valid": valid,
        "user_data": input_data if valid else None
    }
}
""",
            },
        )

        # Second node: processing
        builder.add_node(
            "PythonCodeNode",
            "process",
            {
                "name": "process_user",
                "code": """
if validated_data and validated_data.get("valid"):
    user_data = validated_data.get("user_data", {})
    user_data["id"] = "generated_id_123"
    user_data["created_at"] = "2024-01-01T00:00:00Z"
    result = {"result": {"user": user_data, "success": True}}
else:
    result = {"result": {"error": "Validation failed", "success": False}}
""",
            },
        )

        # Connect nodes
        builder.add_connection("validate", "result", "process", "validated_data")

        workflow = builder.build()

        # Test with valid email
        results, _ = await test_runtime.execute(
            workflow,
            parameters={
                "input_data": {"email": "test@example.com", "first_name": "Test"}
            },
        )

        process_result = results["process"]["result"]
        assert process_result["success"] is True
        assert process_result["user"]["id"] == "generated_id_123"
        assert process_result["user"]["email"] == "test@example.com"

        # Test with invalid email
        results, _ = await test_runtime.execute(
            workflow,
            parameters={"input_data": {"email": "invalid-email", "first_name": "Test"}},
        )

        process_result = results["process"]["result"]
        assert process_result["success"] is False
        assert "error" in process_result

    @pytest.mark.asyncio
    async def test_workflow_error_handling(self, test_runtime):
        """Test workflow error handling."""
        builder = WorkflowBuilder("test_error_handling")

        # Node that will cause an error
        builder.add_node(
            "PythonCodeNode",
            "error_node",
            {
                "name": "error_producer",
                "code": """
# Intentionally cause an error
if trigger_error:
    raise ValueError("Test error message")
else:
    result = {"result": {"success": True}}
""",
            },
        )

        workflow = builder.build()

        # Test normal execution
        results, _ = await test_runtime.execute(
            workflow, parameters={"trigger_error": False}
        )

        assert results["error_node"]["result"]["success"] is True

        # Test error handling
        with pytest.raises(Exception):
            await test_runtime.execute(workflow, parameters={"trigger_error": True})


class TestWorkflowPerformance:
    """Test workflow performance characteristics."""

    @pytest.mark.asyncio
    async def test_workflow_execution_time(self, test_runtime, performance_timer):
        """Test workflow execution performance."""
        builder = WorkflowBuilder("performance_test")

        # Simple processing node
        builder.add_node(
            "PythonCodeNode",
            "process",
            {
                "name": "simple_processor",
                "code": """
# Simple processing
processed_data = {
    "id": input_data.get("id", "default"),
    "processed": True,
    "timestamp": "2024-01-01T00:00:00Z"
}

result = {"result": processed_data}
""",
            },
        )

        workflow = builder.build()

        performance_timer.start()
        results, _ = await test_runtime.execute(
            workflow, parameters={"input_data": {"id": "test_123"}}
        )
        elapsed = performance_timer.stop()

        # Workflow should execute quickly
        assert elapsed < 1000  # Less than 1 second
        assert results["process"]["result"]["processed"] is True

    @pytest.mark.asyncio
    async def test_concurrent_workflow_execution(self, test_runtime):
        """Test concurrent workflow execution."""
        builder = WorkflowBuilder("concurrent_test")

        builder.add_node(
            "PythonCodeNode",
            "process",
            {
                "name": "concurrent_processor",
                "code": """
import time
# Simulate some processing time
time.sleep(0.1)

result = {
    "result": {
        "id": input_id,
        "processed": True
    }
}
""",
            },
        )

        workflow = builder.build()

        # Run multiple workflows concurrently
        tasks = []
        for i in range(5):
            task = test_runtime.execute(workflow, parameters={"input_id": f"test_{i}"})
            tasks.append(task)

        start_time = asyncio.get_event_loop().time()
        results_list = await asyncio.gather(*tasks)
        end_time = asyncio.get_event_loop().time()

        # All should complete
        assert len(results_list) == 5

        # Should be faster than sequential execution
        execution_time = end_time - start_time
        assert execution_time < 1.0  # Should be much less than 5 * 0.1 seconds

        # Verify all results
        for i, (results, _) in enumerate(results_list):
            assert results["process"]["result"]["id"] == f"test_{i}"
            assert results["process"]["result"]["processed"] is True


class TestWorkflowValidation:
    """Test workflow definition validation."""

    def test_workflow_node_validation(self):
        """Test that workflow nodes have required fields."""
        builder = WorkflowBuilder("validation_test")

        # Valid node
        builder.add_node(
            "PythonCodeNode",
            "valid_node",
            {"name": "valid_processor", "code": "result = {'result': {'valid': True}}"},
        )

        workflow = builder.build()
        assert len(workflow.nodes) == 1

        # Test node has required attributes
        node = workflow.nodes[0]
        assert hasattr(node, "node_id")
        assert hasattr(node, "name")

    def test_workflow_connection_validation(self):
        """Test workflow connection validation."""
        builder = WorkflowBuilder("connection_test")

        # Add two nodes
        builder.add_node(
            "PythonCodeNode",
            "node1",
            {"name": "first_node", "code": "result = {'result': {'data': 'test'}}"},
        )

        builder.add_node(
            "PythonCodeNode",
            "node2",
            {
                "name": "second_node",
                "code": "result = {'result': {'processed': input_data}}",
            },
        )

        # Add valid connection
        builder.add_connection("node1", "result", "node2", "input_data")

        workflow = builder.build()

        # Verify workflow structure
        assert len(workflow.nodes) == 2
        assert len(workflow.connections) == 1

        connection = workflow.connections[0]
        assert connection.from_node_id == "node1"
        assert connection.from_output == "result"
        assert connection.to_node_id == "node2"
        assert connection.to_input == "input_data"
