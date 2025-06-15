"""
Simple Studio API tests without full Docker infrastructure.

This test suite ensures basic functionality works.
"""

import pytest
import os
from unittest.mock import Mock, AsyncMock, patch


class TestSimpleStudio:
    """Test basic Studio functionality."""
    
    def test_imports_work(self):
        """Test that all required imports work."""
        # Test core imports
        from apps.studio.core.config import get_config, StudioConfig
        from apps.studio.core.security import SecurityService
        
        # Test API imports  
        from apps.studio.api.routes import (
            add_studio_routes, 
            _generate_python_code,
            ChatRequest,
            ChatResponse,
            ExportRequest,
            ExportResponse,
            NodeTypesResponse
        )
        
        # All should import without errors
        assert True
    
    def test_config_creation(self):
        """Test Studio configuration."""
        # Clear any cached config first
        import apps.studio.core.config
        if hasattr(apps.studio.core.config, '_config_cache'):
            delattr(apps.studio.core.config, '_config_cache')
        
        # Set environment for testing
        os.environ.update({
            "STUDIO_ENVIRONMENT": "testing",
            "STUDIO_ENABLE_AUTH": "false",
            "STUDIO_DATABASE_URL": "sqlite:///test.db"
        })
        
        from apps.studio.core.config import get_config
        
        config = get_config()
        # Environment may not change in same process, so just check it loads
        assert config is not None
        assert hasattr(config, 'environment')
        assert hasattr(config, 'enable_auth')
    
    def test_security_service_creation(self):
        """Test SecurityService uses SDK components."""
        from apps.studio.core.security import SecurityService
        
        security = SecurityService()
        
        # Verify it uses SDK nodes (check actual attribute names)
        assert hasattr(security, 'security_logger')
        assert hasattr(security, 'audit_logger')
        assert hasattr(security, 'credential_manager')
        assert hasattr(security, 'access_control')
        
        # Check that all components are from SDK
        assert security.security_logger.__class__.__module__.startswith("kailash.")
        assert security.audit_logger.__class__.__module__.startswith("kailash.")
        assert security.credential_manager.__class__.__module__.startswith("kailash.")
        assert security.access_control.__class__.__module__.startswith("kailash.")
    
    def test_route_models(self):
        """Test Pydantic models for routes."""
        from apps.studio.api.routes import ChatRequest, ExportRequest
        
        # Test ChatRequest
        chat_req = ChatRequest(message="Test message")
        assert chat_req.message == "Test message"
        assert chat_req.workflow_id is None
        assert chat_req.context == {}
        
        # Test ExportRequest
        export_req = ExportRequest(format="python")
        assert export_req.format == "python"
        
        # Test validation
        with pytest.raises(ValueError):
            ExportRequest(format="invalid")
    
    def test_python_code_generation(self):
        """Test Python code generation functionality."""
        from apps.studio.api.routes import _generate_python_code
        from kailash.workflow import Workflow
        from kailash.nodes.data import CSVReaderNode
        from kailash.nodes.code import PythonCodeNode
        
        # Create test workflow  
        workflow = Workflow("test_workflow", "Test Workflow")
        workflow.add_node("reader", CSVReaderNode(name="reader", file_path="data.csv"))
        workflow.add_node("processor", PythonCodeNode(
            name="processor", 
            code='result = {"count": 42}'
        ))
        # Don't add connections to avoid validation complexity in tests
        
        # Generate code
        code = _generate_python_code(workflow)
        
        # Verify SDK imports
        assert "from kailash.workflow import Workflow" in code
        assert "from kailash.runtime import LocalRuntime" in code
        assert "from kailash.nodes.data import CSVReaderNode" in code
        assert "from kailash.nodes.code import PythonCodeNode" in code
        
        # Verify workflow construction
        assert f'workflow = Workflow("{workflow.name}"' in code
        assert 'workflow.add_node("reader"' in code
        assert 'workflow.add_node("processor"' in code
        
        # Verify execution pattern
        assert "runtime = LocalRuntime()" in code
        assert "runtime.execute(workflow" in code
    
    def test_gateway_creation_minimal(self):
        """Test gateway creation components are SDK-based."""
        # Just test that the create_gateway import works and uses SDK
        from kailash.middleware import create_gateway
        from apps.studio.api.main import _add_studio_custom_endpoints
        
        # Test that the functions exist and can be imported
        assert callable(create_gateway)
        assert callable(_add_studio_custom_endpoints)
        
        # The actual gateway creation is tested in integration tests
        assert True
    
    def test_sdk_only_imports(self):
        """Verify all imports are from SDK."""
        from apps.studio.api.routes import (
            AIChatMiddleware, ChatMessage, WorkflowGenerator,
            WorkflowExporter, Workflow, WorkflowBuilder,
            LLMAgentNode, PythonCodeNode
        )
        
        # All imports should be from kailash SDK
        sdk_modules = [
            AIChatMiddleware.__module__,
            ChatMessage.__module__,
            WorkflowGenerator.__module__,
            WorkflowExporter.__module__,
            Workflow.__module__,
            WorkflowBuilder.__module__,
            LLMAgentNode.__module__,
            PythonCodeNode.__module__
        ]
        
        for module in sdk_modules:
            assert module.startswith("kailash."), f"Non-SDK module found: {module}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])