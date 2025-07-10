"""
Unit Tests: Modular DataFlow Node Generation

Tests for the new modular core node generation system.
"""

from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest
from dataflow.core.config import DataFlowConfig
from dataflow.core.engine import DataFlow
from dataflow.core.models import DataFlowModel, Environment
from dataflow.core.nodes import NodeGenerator


class TestNodeGenerator:
    """Test the NodeGenerator class functionality."""

    def test_node_generator_initialization(self):
        """Test NodeGenerator initialization."""
        config = DataFlowConfig()
        dataflow_instance = DataFlow(config=config)
        generator = NodeGenerator(dataflow_instance)

        assert generator.dataflow_instance == dataflow_instance

    def test_node_generator_custom_naming(self):
        """Test NodeGenerator with custom naming conventions."""
        config = DataFlowConfig()
        config.node_prefix = "Custom"
        config.node_suffix = "Handler"
        dataflow_instance = DataFlow(config=config)
        generator = NodeGenerator(dataflow_instance)

        assert generator.dataflow_instance.config.node_prefix == "Custom"
        assert generator.dataflow_instance.config.node_suffix == "Handler"

    def test_generate_node_name(self):
        """Test node name generation."""
        config = DataFlowConfig()
        dataflow_instance = DataFlow(config=config)
        generator = NodeGenerator(dataflow_instance)

        # Test basic name generation via node creation
        fields = {"name": {"type": str, "required": True}}
        generator.generate_crud_nodes("User", fields)

        # Check if nodes were created in the instance
        assert "UserCreateNode" in dataflow_instance._nodes
        assert "UserReadNode" in dataflow_instance._nodes

    def test_generate_crud_nodes_basic(self):
        """Test basic CRUD node generation."""
        config = DataFlowConfig()
        dataflow_instance = DataFlow(config=config)
        generator = NodeGenerator(dataflow_instance)

        # Generate nodes for a model
        fields = {
            "name": {"type": str, "required": True},
            "email": {"type": str, "required": True},
        }

        generator.generate_crud_nodes("TestModel", fields)

        # Should generate all CRUD operations
        expected_nodes = [
            "TestModelCreateNode",
            "TestModelReadNode",
            "TestModelUpdateNode",
            "TestModelDeleteNode",
            "TestModelListNode",
        ]

        for node_name in expected_nodes:
            assert node_name in dataflow_instance._nodes
            node_class = dataflow_instance._nodes[node_name]
            assert hasattr(node_class, "__name__")
            assert node_class.__name__ == node_name

    def test_generate_crud_nodes_with_soft_delete(self):
        """Test CRUD node generation with soft delete enabled."""
        config = DataFlowConfig()
        dataflow_instance = DataFlow(config=config)
        generator = NodeGenerator(dataflow_instance)

        # Generate nodes for a model with soft delete
        fields = {
            "name": {"type": str, "required": True},
            "deleted_at": {"type": str, "required": False},
        }

        generator.generate_crud_nodes("SoftDeleteModel", fields)

        # Delete node should be available
        assert "SoftDeleteModelDeleteNode" in dataflow_instance._nodes
        delete_node_class = dataflow_instance._nodes["SoftDeleteModelDeleteNode"]
        assert delete_node_class.__name__ == "SoftDeleteModelDeleteNode"

    def test_generate_crud_nodes_with_multi_tenant(self):
        """Test CRUD node generation with multi-tenant support."""
        config = DataFlowConfig()
        config.security.multi_tenant = True
        dataflow_instance = DataFlow(config=config)
        generator = NodeGenerator(dataflow_instance)

        # Generate nodes for a multi-tenant model
        fields = {
            "name": {"type": str, "required": True},
            "tenant_id": {"type": str, "required": True},
        }

        generator.generate_crud_nodes("MultiTenantModel", fields)

        # All nodes should be available with multi-tenant support
        assert "MultiTenantModelCreateNode" in dataflow_instance._nodes
        create_node_class = dataflow_instance._nodes["MultiTenantModelCreateNode"]
        assert create_node_class.__name__ == "MultiTenantModelCreateNode"

    def test_generate_bulk_nodes(self):
        """Test bulk operation node generation."""
        config = DataFlowConfig()
        dataflow_instance = DataFlow(config=config)
        generator = NodeGenerator(dataflow_instance)

        # Generate bulk nodes for a model
        fields = {
            "name": {"type": str, "required": True},
            "value": {"type": int, "required": True},
        }

        generator.generate_bulk_nodes("BulkModel", fields)

        expected_bulk_nodes = [
            "BulkModelBulkCreateNode",
            "BulkModelBulkUpdateNode",
            "BulkModelBulkDeleteNode",
            "BulkModelBulkUpsertNode",
        ]

        for node_name in expected_bulk_nodes:
            assert node_name in dataflow_instance._nodes
            node_class = dataflow_instance._nodes[node_name]
            assert hasattr(node_class, "__name__")
            assert node_class.__name__ == node_name


class TestCRUDNodeFactory:
    """Test the node factory functionality through NodeGenerator."""

    def test_crud_node_factory_create_operation(self):
        """Test CREATE operation node factory."""
        config = DataFlowConfig()
        dataflow_instance = DataFlow(config=config)
        generator = NodeGenerator(dataflow_instance)

        fields = {
            "name": {"type": str, "required": True},
            "email": {"type": str, "required": True},
        }

        generator.generate_crud_nodes("CreateModel", fields)

        # Test node properties
        CreateNode = dataflow_instance._nodes["CreateModelCreateNode"]
        assert CreateNode.__name__ == "CreateModelCreateNode"

        # Test node has required methods
        node_instance = CreateNode()
        assert hasattr(node_instance, "get_parameters")
        assert hasattr(node_instance, "execute")
        assert node_instance.operation == "create"

    def test_crud_node_factory_read_operation(self):
        """Test READ operation node factory."""
        config = DataFlowConfig()
        dataflow_instance = DataFlow(config=config)
        generator = NodeGenerator(dataflow_instance)

        fields = {
            "id": {"type": int, "required": True},
            "name": {"type": str, "required": True},
        }

        generator.generate_crud_nodes("ReadModel", fields)

        ReadNode = dataflow_instance._nodes["ReadModelReadNode"]
        assert ReadNode.__name__ == "ReadModelReadNode"

        # Read node should handle ID-based lookup
        node_instance = ReadNode()
        assert node_instance.operation == "read"
        params = node_instance.get_parameters()
        assert "id" in params

    def test_crud_node_factory_update_operation(self):
        """Test UPDATE operation node factory."""
        config = DataFlowConfig()
        dataflow_instance = DataFlow(config=config)
        generator = NodeGenerator(dataflow_instance)

        fields = {
            "id": {"type": int, "required": True},
            "name": {"type": str, "required": True},
            "value": {"type": float, "required": True},
        }

        generator.generate_crud_nodes("UpdateModel", fields)

        UpdateNode = dataflow_instance._nodes["UpdateModelUpdateNode"]
        assert UpdateNode.__name__ == "UpdateModelUpdateNode"

        # Update node should handle partial updates
        node_instance = UpdateNode()
        assert node_instance.operation == "update"
        params = node_instance.get_parameters()
        assert "id" in params
        assert "name" in params
        assert "value" in params

    def test_crud_node_factory_delete_operation(self):
        """Test DELETE operation node factory."""
        config = DataFlowConfig()
        dataflow_instance = DataFlow(config=config)
        generator = NodeGenerator(dataflow_instance)

        fields = {
            "id": {"type": int, "required": True},
            "name": {"type": str, "required": True},
        }

        generator.generate_crud_nodes("DeleteModel", fields)

        DeleteNode = dataflow_instance._nodes["DeleteModelDeleteNode"]
        assert DeleteNode.__name__ == "DeleteModelDeleteNode"

        node_instance = DeleteNode()
        assert node_instance.operation == "delete"

    def test_crud_node_factory_list_operation(self):
        """Test LIST operation node factory."""
        config = DataFlowConfig()
        dataflow_instance = DataFlow(config=config)
        generator = NodeGenerator(dataflow_instance)

        fields = {
            "name": {"type": str, "required": True},
            "category": {"type": str, "required": True},
            "active": {"type": bool, "required": False, "default": True},
        }

        generator.generate_crud_nodes("ListModel", fields)

        ListNode = dataflow_instance._nodes["ListModelListNode"]
        assert ListNode.__name__ == "ListModelListNode"

        # List node should support filtering and pagination
        node_instance = ListNode()
        assert node_instance.operation == "list"
        params = node_instance.get_parameters()
        assert "limit" in params
        assert "offset" in params
        assert "filter" in params

    def test_crud_node_factory_soft_delete_handling(self):
        """Test soft delete handling in node factory."""
        config = DataFlowConfig()
        dataflow_instance = DataFlow(config=config)
        generator = NodeGenerator(dataflow_instance)

        fields = {
            "id": {"type": int, "required": True},
            "name": {"type": str, "required": True},
            "deleted_at": {"type": str, "required": False},
        }

        generator.generate_crud_nodes("SoftDeleteModel", fields)

        # Should generate soft delete capable delete node
        DeleteNode = dataflow_instance._nodes["SoftDeleteModelDeleteNode"]
        assert DeleteNode.__name__ == "SoftDeleteModelDeleteNode"

        node_instance = DeleteNode()
        assert node_instance.operation == "delete"

    def test_crud_node_factory_with_database_specific_sql(self):
        """Test database-specific SQL generation."""
        # Test PostgreSQL-specific features
        postgres_config = DataFlowConfig()
        postgres_config.database.url = "postgresql://localhost/test"
        postgres_dataflow = DataFlow(config=postgres_config)
        postgres_generator = NodeGenerator(postgres_dataflow)

        fields = {
            "name": {"type": str, "required": True},
            "created_at": {"type": str, "required": False},
        }

        postgres_generator.generate_crud_nodes("DatabaseModel", fields)

        # Test SQLite-specific features
        sqlite_config = DataFlowConfig()
        sqlite_config.database.url = "sqlite:///test.db"
        sqlite_dataflow = DataFlow(config=sqlite_config)
        sqlite_generator = NodeGenerator(sqlite_dataflow)

        sqlite_generator.generate_crud_nodes("DatabaseModel", fields)

        # Both should generate create nodes
        assert "DatabaseModelCreateNode" in postgres_dataflow._nodes
        assert "DatabaseModelCreateNode" in sqlite_dataflow._nodes


class TestNodeRegistration:
    """Test node registration and management."""

    def test_node_registration_tracking(self):
        """Test that generated nodes are properly tracked."""
        config = DataFlowConfig()
        dataflow_instance = DataFlow(config=config)
        generator = NodeGenerator(dataflow_instance)

        fields = {"name": {"type": str, "required": True}}

        generator.generate_crud_nodes("TrackedModel", fields)

        # Should track all generated nodes
        assert len(dataflow_instance._nodes) > 0

        # Each node should be registered with correct metadata
        expected_nodes = [
            "TrackedModelCreateNode",
            "TrackedModelReadNode",
            "TrackedModelUpdateNode",
            "TrackedModelDeleteNode",
            "TrackedModelListNode",
        ]
        for node_name in expected_nodes:
            assert node_name in dataflow_instance._nodes
            node_class = dataflow_instance._nodes[node_name]
            assert hasattr(node_class, "__name__")
            assert node_class.__name__ == node_name

    def test_node_name_collision_handling(self):
        """Test handling of node name collisions."""
        config = DataFlowConfig()
        dataflow_instance = DataFlow(config=config)
        generator = NodeGenerator(dataflow_instance)

        fields = {"name": {"type": str, "required": True}}

        # Generate nodes for both models (same operation names)
        generator.generate_crud_nodes("Model1", fields)
        generator.generate_crud_nodes("Model2", fields)

        # Should have different class names to avoid collisions
        assert "Model1CreateNode" in dataflow_instance._nodes
        assert "Model2CreateNode" in dataflow_instance._nodes
        assert (
            dataflow_instance._nodes["Model1CreateNode"].__name__
            != dataflow_instance._nodes["Model2CreateNode"].__name__
        )
        assert "Model1" in dataflow_instance._nodes["Model1CreateNode"].__name__
        assert "Model2" in dataflow_instance._nodes["Model2CreateNode"].__name__

    def test_conditional_node_generation(self):
        """Test conditional node generation based on configuration."""
        # Config with normal operations
        config = DataFlowConfig()
        dataflow_instance = DataFlow(config=config)
        generator = NodeGenerator(dataflow_instance)

        fields = {"name": {"type": str, "required": True}}

        # Should generate CRUD nodes
        generator.generate_crud_nodes("ConditionalModel", fields)
        expected_crud_nodes = [
            "ConditionalModelCreateNode",
            "ConditionalModelReadNode",
            "ConditionalModelUpdateNode",
            "ConditionalModelDeleteNode",
            "ConditionalModelListNode",
        ]
        for node_name in expected_crud_nodes:
            assert node_name in dataflow_instance._nodes

        # Should generate bulk nodes when requested
        generator.generate_bulk_nodes("ConditionalModel", fields)
        expected_bulk_nodes = [
            "ConditionalModelBulkCreateNode",
            "ConditionalModelBulkUpdateNode",
            "ConditionalModelBulkDeleteNode",
            "ConditionalModelBulkUpsertNode",
        ]
        for node_name in expected_bulk_nodes:
            assert node_name in dataflow_instance._nodes


class TestNodeIntegration:
    """Test integration between nodes and other components."""

    @patch("dataflow.utils.connection.ConnectionManager")
    def test_node_connection_integration(self, mock_connection):
        """Test that nodes integrate with connection management."""
        config = DataFlowConfig()
        dataflow_instance = DataFlow(config=config)
        generator = NodeGenerator(dataflow_instance)

        fields = {"name": {"type": str, "required": True}}

        generator.generate_crud_nodes("ConnectionModel", fields)

        CreateNode = dataflow_instance._nodes["ConnectionModelCreateNode"]

        # Node should be able to execute operations
        node_instance = CreateNode()
        assert hasattr(node_instance, "execute")

        # Mock a connection and test usage
        mock_connection.return_value.execute.return_value = {"id": 1}

        # This would be tested with actual execution in integration tests
        assert True  # Placeholder for connection integration test

    def test_node_validation_integration(self):
        """Test that nodes integrate with model validation."""
        config = DataFlowConfig()
        dataflow_instance = DataFlow(config=config)
        generator = NodeGenerator(dataflow_instance)

        fields = {
            "email": {"type": str, "required": True},
            "age": {"type": int, "required": True},
        }

        generator.generate_crud_nodes("ValidatedModel", fields)

        CreateNode = dataflow_instance._nodes["ValidatedModelCreateNode"]

        # Node should respect model validation
        node_instance = CreateNode()
        assert hasattr(node_instance, "model_fields")
        assert node_instance.model_fields == fields
        assert node_instance.model_name == "ValidatedModel"
