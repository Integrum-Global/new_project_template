"""
Integration tests for Studio API endpoints.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock
from fastapi.testclient import TestClient
from httpx import AsyncClient

# Import the FastAPI app
from ...api.main import create_app
from ...core.config import StudioConfig
from ...core.database import StudioDatabase


@pytest.fixture
def test_config():
    """Test configuration."""
    config = StudioConfig()
    config.enable_auth = False  # Disable auth for testing
    config.database_url = ":memory:"  # Use in-memory database
    return config


@pytest.fixture
def test_app(test_config):
    """Test FastAPI application."""
    # Override config for testing
    import apps.studio.api.main as main_module
    main_module.config = test_config
    
    app = create_app()
    return app


@pytest.fixture
def client(test_app):
    """Test client."""
    return TestClient(test_app)


@pytest.fixture
async def async_client(test_app):
    """Async test client."""
    async with AsyncClient(app=test_app, base_url="http://test") as ac:
        yield ac


class TestHealthEndpoints:
    """Test health and system endpoints."""
    
    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "middleware" in data
    
    def test_system_info(self, client):
        """Test system info endpoint."""
        response = client.get("/api/info")
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == "Kailash Studio API"
        assert "features" in data
        assert "node_categories" in data
    
    def test_system_stats(self, client):
        """Test system stats endpoint."""
        response = client.get("/api/stats")
        assert response.status_code == 200
        
        data = response.json()
        assert "workflows" in data
        assert "executions" in data
        assert "templates" in data


class TestWorkflowEndpoints:
    """Test workflow management endpoints."""
    
    def test_create_workflow(self, client):
        """Test creating a workflow."""
        workflow_data = {
            "name": "Test Workflow",
            "description": "A test workflow",
            "nodes": [],
            "connections": []
        }
        
        response = client.post("/api/workflows/", json=workflow_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["name"] == "Test Workflow"
        assert data["description"] == "A test workflow"
        assert "workflow_id" in data
    
    def test_list_workflows(self, client):
        """Test listing workflows."""
        # Create a workflow first
        workflow_data = {
            "name": "Test Workflow",
            "description": "A test workflow"
        }
        client.post("/api/workflows/", json=workflow_data)
        
        # List workflows
        response = client.get("/api/workflows/")
        assert response.status_code == 200
        
        data = response.json()
        assert "workflows" in data
        assert data["total"] >= 1
    
    def test_get_workflow(self, client):
        """Test getting a specific workflow."""
        # Create a workflow first
        workflow_data = {
            "name": "Test Workflow",
            "description": "A test workflow"
        }
        create_response = client.post("/api/workflows/", json=workflow_data)
        workflow_id = create_response.json()["workflow_id"]
        
        # Get the workflow
        response = client.get(f"/api/workflows/{workflow_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["workflow_id"] == workflow_id
        assert data["name"] == "Test Workflow"
    
    def test_update_workflow(self, client):
        """Test updating a workflow."""
        # Create a workflow first
        workflow_data = {
            "name": "Test Workflow",
            "description": "A test workflow"
        }
        create_response = client.post("/api/workflows/", json=workflow_data)
        workflow_id = create_response.json()["workflow_id"]
        
        # Update the workflow
        update_data = {
            "name": "Updated Workflow",
            "description": "An updated test workflow"
        }
        response = client.put(f"/api/workflows/{workflow_id}", json=update_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == "Updated Workflow"
        assert data["description"] == "An updated test workflow"
    
    def test_delete_workflow(self, client):
        """Test deleting a workflow."""
        # Create a workflow first
        workflow_data = {
            "name": "Test Workflow",
            "description": "A test workflow"
        }
        create_response = client.post("/api/workflows/", json=workflow_data)
        workflow_id = create_response.json()["workflow_id"]
        
        # Delete the workflow
        response = client.delete(f"/api/workflows/{workflow_id}")
        assert response.status_code == 204
        
        # Verify it's deleted
        get_response = client.get(f"/api/workflows/{workflow_id}")
        assert get_response.status_code == 404


class TestNodeEndpoints:
    """Test node management endpoints."""
    
    def test_get_node_types(self, client):
        """Test getting node types."""
        response = client.get("/api/nodes/types")
        assert response.status_code == 200
        
        data = response.json()
        assert "categories" in data
        assert "total_nodes" in data
        assert data["total_nodes"] > 0
    
    def test_get_node_categories(self, client):
        """Test getting node categories."""
        response = client.get("/api/nodes/categories")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        
        # Check category structure
        category = data[0]
        assert "name" in category
        assert "display_name" in category
        assert "description" in category
    
    def test_search_nodes(self, client):
        """Test searching nodes."""
        response = client.get("/api/nodes/search?q=csv")
        assert response.status_code == 200
        
        data = response.json()
        assert "query" in data
        assert "results" in data
        assert data["query"] == "csv"
    
    def test_validate_node_config(self, client):
        """Test validating node configuration."""
        validation_data = {
            "node_type": "CSVReaderNode",
            "config": {
                "file_path": "/data/test.csv",
                "headers": True
            }
        }
        
        response = client.post("/api/nodes/validate", json=validation_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "valid" in data
        assert "errors" in data


class TestExecutionEndpoints:
    """Test execution management endpoints."""
    
    def test_list_executions(self, client):
        """Test listing executions."""
        response = client.get("/api/execution/")
        assert response.status_code == 200
        
        data = response.json()
        assert "executions" in data
        assert "total" in data
    
    def test_get_execution_stats(self, client):
        """Test getting execution statistics."""
        response = client.get("/api/execution/stats/summary")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_executions" in data
        assert "by_status" in data
        assert "success_rate" in data


class TestTemplateEndpoints:
    """Test template management endpoints."""
    
    def test_list_templates(self, client):
        """Test listing templates."""
        response = client.get("/api/templates/")
        assert response.status_code == 200
        
        data = response.json()
        assert "templates" in data
        assert "total" in data
        assert "by_category" in data
    
    def test_get_template_categories(self, client):
        """Test getting template categories."""
        response = client.get("/api/templates/categories/list")
        assert response.status_code == 200
        
        data = response.json()
        assert "categories" in data
        assert "total_templates" in data
    
    def test_get_popular_templates(self, client):
        """Test getting popular templates."""
        response = client.get("/api/templates/featured/popular")
        assert response.status_code == 200
        
        data = response.json()
        assert "popular_templates" in data
        assert "total_shown" in data


class TestExportEndpoints:
    """Test export functionality endpoints."""
    
    def test_preview_export_no_workflow(self, client):
        """Test export preview with non-existent workflow."""
        response = client.get("/api/export/workflows/nonexistent/preview")
        assert response.status_code == 404


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    def test_404_endpoints(self, client):
        """Test 404 responses for non-existent resources."""
        # Non-existent workflow
        response = client.get("/api/workflows/nonexistent")
        assert response.status_code == 404
        
        # Non-existent execution
        response = client.get("/api/execution/nonexistent")
        assert response.status_code == 404
        
        # Non-existent template
        response = client.get("/api/templates/nonexistent")
        assert response.status_code == 404
    
    def test_invalid_request_data(self, client):
        """Test handling of invalid request data."""
        # Invalid workflow creation
        invalid_data = {
            "name": "",  # Empty name
            "description": "Test"
        }
        response = client.post("/api/workflows/", json=invalid_data)
        assert response.status_code == 422
    
    def test_malformed_json(self, client):
        """Test handling of malformed JSON."""
        response = client.post(
            "/api/workflows/",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422


@pytest.mark.asyncio
class TestAsyncEndpoints:
    """Test async endpoint behavior."""
    
    async def test_async_workflow_creation(self, async_client):
        """Test async workflow creation."""
        workflow_data = {
            "name": "Async Test Workflow",
            "description": "Testing async functionality"
        }
        
        response = await async_client.post("/api/workflows/", json=workflow_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["name"] == "Async Test Workflow"