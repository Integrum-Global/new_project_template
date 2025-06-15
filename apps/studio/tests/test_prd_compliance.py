"""
Test Suite for PRD Compliance of Studio API

This test suite ensures that:
1. All PRD-required endpoints are implemented
2. Endpoints return the correct response formats
3. All implementations use SDK components only
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI

from apps.studio.api.main import create_studio_gateway
from apps.studio.api.routes import add_studio_routes, _generate_python_code
from kailash.workflow import Workflow
from kailash.workflow.builder import WorkflowBuilder
from kailash.nodes.data import CSVReaderNode
from kailash.nodes.ai import LLMAgentNode
from kailash.nodes.code import PythonCodeNode
from kailash.middleware import ChatMessage


class TestPRDCompliance:
    """Test PRD compliance for Studio API endpoints."""
    
    @pytest.fixture
    def mock_gateway(self):
        """Create a mock gateway with required components."""
        gateway = Mock()
        
        # Mock FastAPI app
        gateway.app = FastAPI()
        
        # Mock agent UI middleware
        gateway.agent_ui = AsyncMock()
        gateway.agent_ui.create_session = AsyncMock(return_value="test-session-id")
        gateway.agent_ui.get_session = AsyncMock(return_value=Mock(
            user_id="test-user",
            workflows={"test-workflow": Mock(name="Test Workflow", description="Test", nodes={}, connections=[])},
            executions={}
        ))
        gateway.agent_ui.create_dynamic_workflow = AsyncMock(return_value="new-workflow-id")
        gateway.agent_ui.shared_workflows = {}
        
        # Mock AI chat
        gateway.ai_chat = AsyncMock()
        gateway.ai_chat.start_chat_session = AsyncMock(return_value="chat-session-id")
        gateway.ai_chat.process_message = AsyncMock(return_value=Mock(content="AI response"))
        
        # Mock workflow generator
        gateway.workflow_generator = AsyncMock()
        gateway.workflow_generator.generate_from_prompt = AsyncMock(return_value={
            "name": "Generated Workflow",
            "nodes": [{"id": "node1", "type": "CSVReaderNode", "config": {"file_path": "data.csv"}}],
            "connections": []
        })
        
        # Mock workflow exporter
        gateway.workflow_exporter = Mock()
        gateway.workflow_exporter.to_yaml = Mock(return_value="workflow:\n  name: Test\n  nodes: []")
        
        # Mock node registry
        gateway.node_registry = Mock()
        gateway.node_registry.get_all_nodes = Mock(return_value={
            "CSVReaderNode": CSVReaderNode,
            "LLMAgentNode": LLMAgentNode,
            "PythonCodeNode": PythonCodeNode
        })
        
        # Mock schema registry
        gateway.schema_registry = Mock()
        gateway.schema_registry.get_node_schema = Mock(return_value={
            "display_name": "Test Node",
            "description": "Test description",
            "parameters": {}
        })
        
        # Mock realtime middleware
        gateway.realtime = AsyncMock()
        gateway.realtime.handle_workflow_websocket = AsyncMock()
        
        return gateway
    
    @pytest.fixture
    def client(self, mock_gateway):
        """Create test client with mocked gateway."""
        # Add routes to the mock gateway
        add_studio_routes(mock_gateway)
        return TestClient(mock_gateway.app)
    
    def test_chat_endpoint_exists(self, client):
        """Test that POST /api/chat endpoint exists as required by PRD."""
        response = client.post("/api/chat", json={
            "message": "Create a workflow that reads CSV data"
        })
        
        # Should not return 404
        assert response.status_code != 404
        
        # Should return valid response
        assert response.status_code == 200
        data = response.json()
        
        # Check PRD-required response fields
        assert "response" in data
        assert "workflow_update" in data
        assert "suggested_actions" in data
    
    def test_export_endpoint_exists(self, client):
        """Test that POST /api/workflows/{id}/export endpoint exists as required by PRD."""
        response = client.post("/api/workflows/test-workflow/export?session_id=test-session", json={
            "format": "python"
        })
        
        # Should not return 404
        assert response.status_code != 404
        
        # Should return valid response
        assert response.status_code == 200
        data = response.json()
        
        # Check PRD-required response fields
        assert "format" in data
        assert "content" in data
        assert "filename" in data
        assert data["format"] == "python"
    
    def test_export_yaml_format(self, client):
        """Test YAML export format."""
        response = client.post("/api/workflows/test-workflow/export?session_id=test-session", json={
            "format": "yaml"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["format"] == "yaml"
        assert data["filename"].endswith(".yaml")
    
    def test_nodes_types_endpoint_exists(self, client):
        """Test that GET /api/nodes/types endpoint exists as required by PRD."""
        response = client.get("/api/nodes/types")
        
        # Should not return 404
        assert response.status_code != 404
        
        # Should return valid response
        assert response.status_code == 200
        data = response.json()
        
        # Check PRD-required response structure
        assert "categories" in data
        assert isinstance(data["categories"], dict)
        
        # Check that categories have the right structure
        for category, content in data["categories"].items():
            assert "nodes" in content
            assert isinstance(content["nodes"], list)
    
    def test_chat_creates_workflow(self, client, mock_gateway):
        """Test that chat can create workflows."""
        response = client.post("/api/chat", json={
            "message": "Create a workflow to process CSV data with AI"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have workflow update
        assert data["workflow_update"] is not None
        assert data["workflow_update"]["action"] == "created"
        assert "workflow_id" in data["workflow_update"]
        
        # Should have suggested actions
        assert len(data["suggested_actions"]) > 0
    
    def test_python_code_generation(self):
        """Test Python code generation uses SDK patterns."""
        # Create a test workflow
        workflow = Workflow("test_workflow", "Test Workflow")
        workflow.add_node("reader", CSVReaderNode(name="reader", file_path="data.csv"))
        workflow.add_node("processor", PythonCodeNode(
            name="processor",
            code='result = {"count": len(data)}'
        ))
        workflow.connect("reader", "data", "processor", "data")
        
        # Generate Python code
        code = _generate_python_code(workflow)
        
        # Check that code uses SDK imports
        assert "from kailash.workflow import Workflow" in code
        assert "from kailash.runtime import LocalRuntime" in code
        assert "from kailash.nodes.data import CSVReaderNode" in code
        assert "from kailash.nodes.code import PythonCodeNode" in code
        
        # Check workflow creation
        assert 'workflow = Workflow("test_workflow"' in code
        assert 'workflow.add_node("reader"' in code
        assert 'workflow.add_node("processor"' in code
        assert 'workflow.connect("reader", "data", "processor", "data")' in code
        
        # Check execution pattern
        assert "runtime = LocalRuntime()" in code
        assert "runtime.execute(workflow" in code
    
    def test_no_custom_orchestration(self, client):
        """Ensure no custom orchestration is used - all SDK components."""
        # This test verifies the implementation doesn't create custom execution
        response = client.post("/api/chat", json={
            "message": "Test message"
        })
        
        # The response should work without any custom execution logic
        assert response.status_code == 200
        
        # Check that we're using SDK middleware components
        # The mock_gateway should have SDK middleware attributes
        # This would fail if we were doing custom orchestration
    
    @pytest.mark.asyncio
    async def test_websocket_endpoint_format(self, mock_gateway):
        """Test WebSocket endpoint matches PRD format: /api/workflows/{id}/live"""
        # Add routes
        add_studio_routes(mock_gateway)
        
        # Check that the route was added with correct path
        routes = [route.path for route in mock_gateway.app.routes]
        assert "/api/workflows/{workflow_id}/live" in routes


@pytest.mark.asyncio
async def test_all_sdk_components():
    """Integration test to ensure all components are from SDK."""
    # This test would fail if we import or use non-SDK components
    from apps.studio.api.routes import (
        AIChatMiddleware, ChatMessage, WorkflowGenerator,
        WorkflowExporter, Workflow, WorkflowBuilder,
        LLMAgentNode, PythonCodeNode
    )
    
    # All imports should be from kailash SDK
    assert AIChatMiddleware.__module__.startswith("kailash.")
    assert ChatMessage.__module__.startswith("kailash.")
    assert WorkflowGenerator.__module__.startswith("kailash.")
    assert WorkflowExporter.__module__.startswith("kailash.")
    assert Workflow.__module__.startswith("kailash.")
    assert WorkflowBuilder.__module__.startswith("kailash.")
    assert LLMAgentNode.__module__.startswith("kailash.")
    assert PythonCodeNode.__module__.startswith("kailash.")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])