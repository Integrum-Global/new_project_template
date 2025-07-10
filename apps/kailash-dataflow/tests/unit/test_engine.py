"""
Unit Tests: DataFlow Engine

Tests core engine functionality with mocking.
"""

import asyncio
import os
from typing import Any, Dict, Type
from unittest.mock import MagicMock, call, patch

import pytest
from dataflow import DataFlow
from dataflow.core import Environment
from dataflow.core.config import (
    DatabaseConfig,
    DataFlowConfig,
    MonitoringConfig,
    SecurityConfig,
)
from dataflow.core.models import DataFlowModel
from dataflow.core.schema import FieldMeta, FieldType, IndexMeta, ModelMeta


def create_test_config(
    environment=Environment.DEVELOPMENT,
    database_url="sqlite:///:memory:",
    pool_size=5,
    multi_tenant=False,
    monitoring_enabled=False,
):
    """Create a real DataFlowConfig for testing."""
    # Create real config objects
    database_config = DatabaseConfig(url=database_url, pool_size=pool_size)

    monitoring_config = MonitoringConfig(enabled=monitoring_enabled)

    security_config = SecurityConfig(multi_tenant=multi_tenant)

    config = DataFlowConfig(
        environment=environment,
        database=database_config,
        monitoring=monitoring_config,
        security=security_config,
    )

    return config


class TestDataFlowInitialization:
    """Test DataFlow initialization."""

    def test_zero_config_init(self):
        """Test zero configuration initialization."""
        with patch.dict(os.environ, {"DATABASE_URL": "sqlite:///:memory:"}):
            db = DataFlow()

            assert db is not None
            assert db.config is not None
            assert db.config.environment in [
                Environment.DEVELOPMENT,
                Environment.TESTING,
            ]

    def test_config_init(self):
        """Test initialization with config object."""
        config = create_test_config()

        db = DataFlow(config=config)

        assert db.config.environment == config.environment
        assert db._models == {}
        assert db._connection_manager is not None

    def test_kwargs_override(self):
        """Test initialization with kwargs override."""
        # Initialize with kwargs that override config defaults
        db = DataFlow(
            database_url="sqlite:///test.db",
            pool_size=100,
            multi_tenant=True,
            monitoring=True,
        )

        # Should use the kwargs values
        assert db.config.database.pool_size == 100
        assert db.config.security.multi_tenant is True
        assert db.config.monitoring.enabled is True

    def test_basic_initialization(self):
        """Test basic DataFlow initialization."""
        config = create_test_config()

        db = DataFlow(config=config)

        assert db is not None
        assert db._models == {}
        assert db._model_fields == {}
        assert db._connection_manager is not None
        assert db._bulk_operations is not None
        assert db._transaction_manager is not None

    @patch("dataflow.core.engine.logger")
    def test_configuration_issues_warning(self, mock_logger):
        """Test warning on configuration issues."""
        # Create config with production environment but SQLite database
        config = create_test_config(
            environment=Environment.PRODUCTION, database_url="sqlite:///prod.db"
        )
        # SQLite in production should cause a validation issue with multi-tenant
        config.security.multi_tenant = True

        db = DataFlow(config=config)

        # Should log warning about SQLite not supporting multi-tenant
        mock_logger.warning.assert_called_once()
        warning_message = str(mock_logger.warning.call_args)
        assert (
            "Configuration issues" in warning_message
            or "Multi-tenant" in warning_message
        )


class TestDataFlowLazyInitialization:
    """Test lazy initialization of components."""

    def test_lazy_init_development(self):
        """Test lazy initialization in development."""
        config = create_test_config()

        db = DataFlow(config=config)
        assert db is not None

    def test_init_production(self):
        """Test initialization in production."""
        config = create_test_config(
            environment=Environment.PRODUCTION,
            database_url="postgresql://prod",
            pool_size=50,
            monitoring_enabled=True,
        )
        config.auto_migrate = False

        db = DataFlow(config=config)
        assert db is not None


class TestModelRegistration:
    """Test model registration functionality."""

    def test_model_decorator(self):
        """Test model decorator functionality."""
        config = create_test_config()
        config.auto_generate_nodes = False
        config.auto_migrate = False

        db = DataFlow(config=config)

        @db.model
        class TestModel:
            name: str
            value: int

        # Should register model
        assert "TestModel" in db._models
        assert db._models["TestModel"] == TestModel

    @patch("dataflow.core.engine.logger")
    def test_model_registration_logging(self, mock_logger):
        """Test model registration logging."""
        config = create_test_config()
        config.auto_generate_nodes = False
        config.auto_migrate = False

        db = DataFlow(config=config)

        @db.model
        class User:
            email: str

        # Model should be registered
        assert "User" in db._models

    def test_model_enhancement(self):
        """Test model class enhancement."""
        config = create_test_config()
        config.auto_generate_nodes = False
        config.auto_migrate = False

        db = DataFlow(config=config)

        @db.model
        class Product:
            name: str

        # Should add attributes
        assert hasattr(Product, "_dataflow")
        assert Product._dataflow == db
        assert "Product" in db._models


class TestNodeGeneration:
    """Test CRUD node generation."""

    def test_crud_node_generation(self):
        """Test CRUD node generation for models."""
        config = create_test_config()
        config.auto_generate_nodes = True
        config.auto_migrate = False
        config.node_prefix = ""
        config.node_suffix = "Node"

        db = DataFlow(config=config)

        @db.model
        class Article:
            title: str

        # Should register model
        assert "Article" in db._models
        assert db._models["Article"] == Article

        # Should track model fields
        assert "Article" in db._model_fields
        fields = db._model_fields["Article"]
        assert "title" in fields
        assert fields["title"]["type"] == str

    def test_soft_delete_model(self):
        """Test soft delete model registration."""
        config = create_test_config()
        config.auto_generate_nodes = True
        config.auto_migrate = False

        db = DataFlow(config=config)

        @db.model
        class SoftModel:
            name: str
            __dataflow__ = {"soft_delete": True}

        # Should register model
        assert "SoftModel" in db._models
        # Should have dataflow config
        assert hasattr(SoftModel, "_dataflow_config")
        assert SoftModel._dataflow_config == {"soft_delete": True}


class TestConnectionManagement:
    """Test connection pool management."""

    def test_get_connection_pool(self):
        """Test getting connection pool."""
        config = create_test_config()

        db = DataFlow(config=config)

        # Connection manager should be initialized
        assert db._connection_manager is not None

    def test_get_models(self):
        """Test getting registered models."""
        config = create_test_config()

        db = DataFlow(config=config)

        @db.model
        class TestModel:
            name: str

        models = db.get_models()
        assert "TestModel" in models
        assert models["TestModel"] == TestModel

    def test_get_model_fields(self):
        """Test getting model fields."""
        config = create_test_config()

        db = DataFlow(config=config)

        @db.model
        class User:
            name: str
            age: int

        fields = db.get_model_fields("User")
        assert "name" in fields
        assert "age" in fields
        assert fields["name"]["type"] == str
        assert fields["age"]["type"] == int


class TestMigrationSupport:
    """Test migration functionality."""

    def test_multi_tenant_context(self):
        """Test multi-tenant context setting."""
        config = create_test_config(multi_tenant=True)

        db = DataFlow(config=config)

        # Should have tenant context
        assert db._tenant_context == {}

        # Set tenant context
        db.set_tenant_context("tenant_123")
        assert db._tenant_context == {"tenant_id": "tenant_123"}

    def test_multi_tenant_model(self):
        """Test multi-tenant model registration."""
        config = create_test_config(multi_tenant=True)

        db = DataFlow(config=config)

        @db.model
        class Customer:
            name: str

        # Should auto-add tenant_id field
        fields = db._model_fields["Customer"]
        assert "tenant_id" in fields
        assert fields["tenant_id"]["type"] == str
        assert fields["tenant_id"]["required"] is False


class TestContextManager:
    """Test context manager support."""

    def test_health_check(self):
        """Test health check functionality."""
        config = create_test_config()

        db = DataFlow(config=config)

        @db.model
        class Product:
            name: str

        health = db.health_check()

        assert "status" in health
        assert "database_url" in health
        assert health["models_registered"] == 1
        assert health["multi_tenant_enabled"] is False
        assert health["monitoring_enabled"] is False

    def test_feature_module_access(self):
        """Test access to feature modules."""
        config = create_test_config()

        db = DataFlow(config=config)

        # Should have feature modules
        assert db.bulk is not None
        assert db.transactions is not None
        assert db.connection is not None

        # Multi-tenant should be None when disabled
        assert db.tenants is None

        # With multi-tenant enabled
        config_mt = create_test_config(multi_tenant=True)
        db_mt = DataFlow(config=config_mt)
        assert db_mt.tenants is not None


class TestModelFeatures:
    """Test model features and attributes."""

    def test_model_with_defaults(self):
        """Test model with default values."""
        config = create_test_config()

        db = DataFlow(config=config)

        @db.model
        class User:
            name: str
            active: bool = True
            score: int = 0

        # Check fields were parsed correctly
        fields = db._model_fields["User"]
        assert fields["name"]["required"] is True
        assert fields["active"]["required"] is False
        assert fields["active"]["default"] is True
        assert fields["score"]["required"] is False
        assert fields["score"]["default"] == 0

    def test_model_with_complex_types(self):
        """Test model with various field types."""
        config = create_test_config()

        db = DataFlow(config=config)

        from datetime import datetime
        from typing import Optional

        @db.model
        class Order:
            id: int
            customer_name: str
            total: float
            created_at: datetime
            notes: Optional[str] = None

        # Check fields
        fields = db._model_fields["Order"]
        assert fields["id"]["type"] == int
        assert fields["customer_name"]["type"] == str
        assert fields["total"]["type"] == float
        assert fields["created_at"]["type"] == datetime
        assert fields["notes"]["type"] == Optional[str]
        assert fields["notes"]["default"] is None


class TestWorkflowIntegration:
    """Test workflow integration features."""

    def test_model_workflow_nodes(self):
        """Test that models can be used in workflows."""
        config = create_test_config()

        db = DataFlow(config=config)

        @db.model
        class Task:
            title: str
            completed: bool = False

        # Model should be registered and ready for workflow use
        assert "Task" in db._models
        assert db._models["Task"] == Task

        # Fields should be tracked for node generation
        fields = db._model_fields["Task"]
        assert "title" in fields
        assert "completed" in fields
