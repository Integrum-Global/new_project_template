"""Unit tests for DataFlow core functionality."""

from unittest.mock import Mock, patch

import pytest
from dataflow import DataFlow, DataFlowConfig
from dataflow.core import Environment


class TestDataFlowInitialization:
    """Test DataFlow initialization and configuration."""

    def test_zero_config_initialization(self):
        """Test DataFlow initializes with zero configuration."""
        db = DataFlow()

        assert db is not None
        assert db.config is not None
        assert db.config.environment == Environment.DEVELOPMENT

    def test_database_url_initialization(self):
        """Test DataFlow initializes with database URL."""
        test_url = "postgresql://user:pass@localhost/test"
        db = DataFlow(database_url=test_url)

        assert db.config.database.url == test_url

    def test_config_object_initialization(self):
        """Test DataFlow initializes with config object."""
        from dataflow.core.config import DatabaseConfig

        config = DataFlowConfig(
            environment=Environment.TESTING,
            database=DatabaseConfig(url="sqlite:///test.db"),
        )
        db = DataFlow(config=config)

        assert db.config.environment == Environment.TESTING
        assert db.config.database.url == "sqlite:///test.db"


class TestModelRegistration:
    """Test model registration and node generation."""

    def test_model_decorator_registration(self):
        """Test @db.model decorator registers model."""
        db = DataFlow()

        @db.model
        class User:
            name: str
            email: str
            age: int

        # Check model is registered
        assert "User" in db._models
        assert db._models["User"] == User

    def test_node_generation_for_model(self):
        """Test nodes are generated for registered model."""
        db = DataFlow()

        @db.model
        class Product:
            name: str
            price: float

        # Check all CRUD nodes are generated
        expected_nodes = [
            "ProductCreateNode",
            "ProductReadNode",
            "ProductUpdateNode",
            "ProductDeleteNode",
            "ProductListNode",
            "ProductBulkCreateNode",
            "ProductBulkUpdateNode",
            "ProductBulkDeleteNode",
            "ProductBulkUpsertNode",
        ]

        for node_name in expected_nodes:
            assert node_name in db._nodes

    def test_model_with_defaults(self):
        """Test model with default values."""
        db = DataFlow()

        @db.model
        class Task:
            title: str
            completed: bool = False
            priority: int = 1

        # Model should be registered with defaults preserved
        assert "Task" in db._models

    def test_model_with_special_fields(self):
        """Test model with DataFlow special fields."""
        db = DataFlow()

        @db.model
        class Document:
            title: str
            content: str

            __dataflow__ = {
                "soft_delete": True,
                "multi_tenant": True,
                "versioned": True,
            }

        # Model should be registered with special configuration
        assert "Document" in db._models
        assert hasattr(db._models["Document"], "__dataflow__")


class TestNodeGeneration:
    """Test automatic node generation for models."""

    def test_create_node_parameters(self):
        """Test CreateNode has correct parameters."""
        db = DataFlow()

        @db.model
        class User:
            name: str
            email: str
            age: int
            active: bool = True

        # Get generated CreateNode
        create_node_class = db._nodes["UserCreateNode"]

        # Check it has the right base class
        assert hasattr(create_node_class, "get_parameters")

        # Create instance and check parameters
        node = create_node_class()
        params = node.get_parameters()

        # Should have model fields as parameters
        assert "name" in params
        assert "email" in params
        assert "age" in params
        assert "active" in params

        # Check defaults
        assert params["active"].default is True
        assert params["name"].required is True

    def test_list_node_filter_parameters(self):
        """Test ListNode has filter parameters."""
        db = DataFlow()

        @db.model
        class Product:
            name: str
            price: float
            category: str

        # Get generated ListNode
        list_node_class = db._nodes["ProductListNode"]

        # Create instance and check parameters
        node = list_node_class()
        params = node.get_parameters()

        # Should have filter, limit, offset, order_by
        assert "filter" in params
        assert "limit" in params
        assert "offset" in params
        assert "order_by" in params

    def test_bulk_node_parameters(self):
        """Test BulkCreateNode has data parameter."""
        db = DataFlow()

        @db.model
        class Order:
            customer_id: int
            total: float

        # Get generated BulkCreateNode
        bulk_node_class = db._nodes["OrderBulkCreateNode"]

        # Create instance and check parameters
        node = bulk_node_class()
        params = node.get_parameters()

        # Should have data parameter for bulk operations
        assert "data" in params
        assert params["data"].description


class TestDataFlowIntegration:
    """Test DataFlow integration with Kailash SDK."""

    def test_nodes_are_discoverable(self):
        """Test generated nodes are discoverable by Kailash."""
        db = DataFlow()

        @db.model
        class Article:
            title: str
            content: str

        # Nodes should be registered and accessible
        # Check nodes can be retrieved from DataFlow instance
        assert "ArticleCreateNode" in db._nodes
        assert "ArticleListNode" in db._nodes
        assert db._nodes["ArticleCreateNode"] is not None
        assert db._nodes["ArticleListNode"] is not None

    def test_workflow_integration(self):
        """Test DataFlow nodes work in workflows."""
        from kailash.workflow.builder import WorkflowBuilder

        db = DataFlow()

        @db.model
        class Message:
            text: str
            sender: str

        # Build workflow with generated nodes
        workflow = WorkflowBuilder()

        # Should not raise errors
        workflow.add_node(
            "MessageCreateNode", "create_msg", {"text": "Hello", "sender": "test"}
        )

        workflow.add_node(
            "MessageListNode", "list_msgs", {"filter": {"sender": "test"}}
        )

        # Connect nodes
        workflow.add_connection("create_msg", "id", "list_msgs", "after_id")

        # Build should succeed
        wf = workflow.build()
        assert wf is not None


class TestDataFlowConfiguration:
    """Test DataFlow configuration options."""

    def test_connection_pooling_config(self):
        """Test connection pooling configuration."""
        db = DataFlow(pool_size=10, pool_max_overflow=20, pool_recycle=3600)

        assert db.config.database.pool_size == 10
        assert db.config.database.max_overflow == 20
        assert db.config.database.pool_recycle == 3600

    def test_multi_tenant_config(self):
        """Test multi-tenant configuration."""
        db = DataFlow(multi_tenant=True)

        assert db.config.security.multi_tenant is True

    def test_monitoring_config(self):
        """Test monitoring configuration."""
        db = DataFlow(monitoring=True, slow_query_threshold=0.5)

        assert db.config.monitoring.enabled is True
        assert db.config.monitoring.slow_query_threshold == 0.5


class TestDataFlowHelperMethods:
    """Test DataFlow helper methods."""

    def test_create_tables_method(self):
        """Test create_tables helper method."""
        db = DataFlow()

        @db.model
        class TestModel:
            name: str

        # Mock the table creation
        with patch.object(db, "_execute_ddl") as mock_ddl:
            db.create_tables()

            # Should have been called
            mock_ddl.assert_called()

    def test_health_check_method(self):
        """Test health_check method."""
        db = DataFlow()

        # Mock database connection
        with patch.object(db, "_check_database_connection", return_value=True):
            result = db.health_check()

            assert result["status"] == "healthy"
            assert result["connection_healthy"] is True

    def test_close_method(self):
        """Test close method cleans up resources."""
        db = DataFlow()

        # Mock connection pool
        mock_pool = Mock()
        db._connection_pool = mock_pool

        db.close()

        # Pool should be closed
        mock_pool.close.assert_called_once()


class TestDataFlowErrors:
    """Test DataFlow error handling."""

    def test_invalid_model_definition(self):
        """Test error on invalid model definition."""
        db = DataFlow()

        # Model without any fields should raise error
        with pytest.raises(ValueError, match="must have at least one field"):

            @db.model
            class Empty:
                pass

    def test_duplicate_model_name(self):
        """Test error on duplicate model names."""
        db = DataFlow()

        @db.model
        class User:
            name: str

        # Registering same name should raise error
        with pytest.raises(ValueError, match="already registered"):

            @db.model
            class User:  # noqa: F811
                email: str

    def test_invalid_database_url(self):
        """Test error on invalid database URL."""
        with pytest.raises(ValueError, match="Invalid database URL"):
            DataFlow(database_url="not://a/valid/url")
