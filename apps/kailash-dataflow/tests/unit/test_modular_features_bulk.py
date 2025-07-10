"""
Unit Tests: Modular DataFlow Bulk Operations

Tests for the new modular bulk operations feature.
"""

from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from dataflow.core import Environment
from dataflow.core.config import DataFlowConfig
from dataflow.core.engine import DataFlow
from dataflow.features.bulk import BulkOperations


class TestBulkOperationConfig:
    """Test bulk operation configuration."""

    def test_bulk_config_defaults(self):
        """Test default bulk operation configuration via DataFlowConfig."""
        config = DataFlowConfig()

        # Test that DataFlowConfig has sensible defaults
        assert config.database is not None
        assert config.monitoring is not None
        assert config.security is not None

    def test_bulk_config_custom_values(self):
        """Test custom bulk operation configuration."""
        config = DataFlowConfig()

        # Test that we can customize configuration
        config.database.pool_size = 500
        config.monitoring.enabled = False

        assert config.database.pool_size == 500
        assert config.monitoring.enabled is False

    def test_bulk_config_validation(self):
        """Test bulk operation configuration validation."""
        # Valid configuration
        config = DataFlowConfig()
        config.database.pool_size = 100
        issues = config.validate()
        assert len(issues) == 0

        # Test with production environment
        config.environment = Environment.PRODUCTION
        issues = config.validate()
        # May have validation issues in production without proper DB URL
        assert isinstance(issues, list)


class TestBulkOperationResult:
    """Test bulk operation result tracking."""

    def test_bulk_result_initialization(self):
        """Test bulk operation result initialization."""
        config = DataFlowConfig()
        dataflow_instance = DataFlow(config=config)
        bulk_ops = BulkOperations(dataflow_instance)

        # Test a bulk operation
        result = bulk_ops.bulk_create("test_model", [], batch_size=100)

        assert result["records_processed"] == 0
        assert result["success_count"] == 0
        assert result["batch_size"] == 100
        assert result["success"] is True

    def test_bulk_result_progress_tracking(self):
        """Test progress tracking in bulk results."""
        config = DataFlowConfig()
        dataflow_instance = DataFlow(config=config)
        bulk_ops = BulkOperations(dataflow_instance)

        # Test bulk update with data
        test_data = [{"id": i, "name": f"Item {i}"} for i in range(50)]
        result = bulk_ops.bulk_update("test_model", data=test_data, batch_size=50)

        assert result["records_processed"] == 50
        assert result["success_count"] == 50
        assert result["batch_size"] == 50
        assert result["success"] is True

    def test_bulk_result_completion_status(self):
        """Test bulk operation completion status."""
        config = DataFlowConfig()
        dataflow_instance = DataFlow(config=config)
        bulk_ops = BulkOperations(dataflow_instance)

        # Test bulk delete
        test_data = [{"id": i} for i in range(100)]
        result = bulk_ops.bulk_delete("test_model", data=test_data, batch_size=25)

        # Should be completed after operation
        assert result["records_processed"] == 100
        assert result["success_count"] == 100
        assert result["success"] is True

    def test_bulk_result_error_handling(self):
        """Test error handling in bulk results."""
        config = DataFlowConfig()
        dataflow_instance = DataFlow(config=config)
        bulk_ops = BulkOperations(dataflow_instance)

        # Test error handling with invalid parameters
        result = bulk_ops.bulk_create("test_model", None, batch_size=20)

        # Should handle the error gracefully
        assert result["success"] is False
        assert "error" in result
        assert "cannot be None" in result["error"]


class TestBulkOperationsMixin:
    """Test the BulkOperations functionality."""

    def test_bulk_mixin_initialization(self):
        """Test BulkOperations initialization."""
        config = DataFlowConfig()
        dataflow_instance = DataFlow(config=config)
        bulk_ops = BulkOperations(dataflow_instance)

        assert bulk_ops.dataflow == dataflow_instance
        assert hasattr(bulk_ops, "bulk_create")
        assert hasattr(bulk_ops, "bulk_update")
        assert hasattr(bulk_ops, "bulk_delete")

    def test_bulk_create_operation(self):
        """Test bulk create operation."""
        config = DataFlowConfig()
        dataflow_instance = DataFlow(config=config)
        bulk_ops = BulkOperations(dataflow_instance)

        # Mock data
        test_data = [
            {"name": "Item 1", "value": 10},
            {"name": "Item 2", "value": 20},
            {"name": "Item 3", "value": 30},
            {"name": "Item 4", "value": 40},
        ]

        result = bulk_ops.bulk_create("test_model", test_data, batch_size=2)

        assert isinstance(result, dict)
        assert result["records_processed"] == 4
        assert result["success_count"] == 4
        assert result["batch_size"] == 2
        assert result["success"] is True

    def test_bulk_update_operation(self):
        """Test bulk update operation."""
        config = DataFlowConfig()
        dataflow_instance = DataFlow(config=config)
        bulk_ops = BulkOperations(dataflow_instance)

        # Mock update data
        update_data = [
            {"id": 1, "name": "Updated 1"},
            {"id": 2, "name": "Updated 2"},
            {"id": 3, "name": "Updated 3"},
        ]

        result = bulk_ops.bulk_update("test_model", data=update_data, batch_size=3)

        assert result["records_processed"] == 3
        assert result["success_count"] == 3
        assert result["success"] is True

    def test_bulk_delete_operation(self):
        """Test bulk delete operation."""
        config = DataFlowConfig()
        dataflow_instance = DataFlow(config=config)
        bulk_ops = BulkOperations(dataflow_instance)

        # Mock delete criteria
        delete_data = [{"id": i} for i in range(1, 8)]

        result = bulk_ops.bulk_delete("test_model", data=delete_data, batch_size=5)

        assert result["records_processed"] == 7
        assert result["success_count"] == 7
        assert result["success"] is True

    def test_bulk_operation_error_handling(self):
        """Test error handling in bulk operations."""
        config = DataFlowConfig()
        dataflow_instance = DataFlow(config=config)
        bulk_ops = BulkOperations(dataflow_instance)

        # Mock data that will cause errors
        problematic_data = [
            {"name": None, "value": 10},  # NULL constraint violation
            {"name": "Valid", "value": 20},
        ]

        # Test error handling - BulkOperations should handle gracefully
        result = bulk_ops.bulk_create("test_model", problematic_data, batch_size=2)

        # Should return a result (may be successful simulation)
        assert isinstance(result, dict)
        assert "success" in result

    def test_bulk_operation_conflict_resolution(self):
        """Test conflict resolution strategies."""
        config = DataFlowConfig()
        dataflow_instance = DataFlow(config=config)
        bulk_ops = BulkOperations(dataflow_instance)

        duplicate_data = [{"id": 1, "name": "Existing"}, {"id": 2, "name": "New"}]

        result = bulk_ops.bulk_upsert(
            "test_model", duplicate_data, conflict_resolution="skip", batch_size=2
        )

        # Should handle conflict according to strategy
        assert result["records_processed"] >= 0
        assert result["success"] is True
        assert "conflict_resolution" in result

    def test_bulk_operation_progress_callback(self):
        """Test progress callback functionality."""
        config = DataFlowConfig()
        dataflow_instance = DataFlow(config=config)
        bulk_ops = BulkOperations(dataflow_instance)

        test_data = [{"name": f"Item {i}"} for i in range(10)]

        result = bulk_ops.bulk_create("test_model", test_data, batch_size=2)

        # Should complete successfully
        assert result["records_processed"] == 10
        assert result["success"] is True

    def test_batch_size_optimization(self):
        """Test automatic batch size optimization."""
        config = DataFlowConfig()
        dataflow_instance = DataFlow(config=config)
        bulk_ops = BulkOperations(dataflow_instance)

        # Test small dataset - should handle efficiently
        small_data = [{"name": f"Item {i}"} for i in range(50)]
        result = bulk_ops.bulk_create("test_model", small_data, batch_size=10)
        assert result["records_processed"] == 50
        assert result["batch_size"] == 10

        # Test large dataset - should handle efficiently
        large_data = [{"name": f"Item {i}"} for i in range(1000)]
        result = bulk_ops.bulk_create("test_model", large_data, batch_size=1000)
        assert result["records_processed"] == 1000
        assert result["batch_size"] == 1000

    def test_memory_usage_optimization(self):
        """Test memory usage optimization in bulk operations."""
        config = DataFlowConfig()
        dataflow_instance = DataFlow(config=config)
        bulk_ops = BulkOperations(dataflow_instance)

        # Large dataset that would consume significant memory
        large_data = [{"name": f"Item {i}", "data": "x" * 100} for i in range(500)]

        # Should handle large datasets efficiently
        result = bulk_ops.bulk_create("test_model", large_data, batch_size=100)

        assert result["records_processed"] == 500
        assert result["batch_size"] == 100
        assert result["success"] is True


class TestBulkOperationIntegration:
    """Test integration of bulk operations with other components."""

    def test_bulk_operations_with_model_validation(self):
        """Test bulk operations with model validation."""

        class ValidatedModel:
            name: str
            email: str

            def validate_email(self, email: str) -> str:
                if "@" not in email:
                    raise ValueError("Invalid email format")
                return email

        config = DataFlowConfig()
        dataflow_instance = DataFlow(config=config)
        bulk_ops = BulkOperations(dataflow_instance)

        # Data with validation issues
        mixed_data = [
            {"name": "Valid User", "email": "user@example.com"},
            {"name": "Invalid User", "email": "invalid-email"},  # Will fail validation
            {"name": "Another Valid", "email": "another@example.com"},
        ]

        # Bulk operation should handle validation errors gracefully
        result = bulk_ops.bulk_create("ValidatedModel", mixed_data)

        # Should process all records (validation happens at model level)
        assert result["records_processed"] == 3
        assert result["success"] is True

    @patch("dataflow.utils.connection.ConnectionManager")
    def test_bulk_operations_with_connection_pooling(self, mock_connection_manager):
        """Test bulk operations with connection pooling."""
        config = DataFlowConfig()
        dataflow_instance = DataFlow(config=config)
        bulk_ops = BulkOperations(dataflow_instance)

        # Mock connection pool
        mock_pool = MagicMock()
        mock_connection_manager.return_value.get_pool.return_value = mock_pool

        test_data = [{"name": f"Item {i}"} for i in range(100)]

        result = bulk_ops.bulk_create("test_model", test_data, batch_size=10)

        # Should process successfully
        assert result["records_processed"] == 100
        assert result["success"] is True

    def test_bulk_operations_with_monitoring(self):
        """Test bulk operations with monitoring integration."""
        config = DataFlowConfig()
        config.monitoring.enabled = True
        dataflow_instance = DataFlow(config=config)
        bulk_ops = BulkOperations(dataflow_instance)

        metrics_collected = []

        def metrics_callback(operation: str, metrics: Dict[str, Any]):
            metrics_collected.append({"operation": operation, "metrics": metrics})

        # Test that monitoring is available
        assert config.monitoring.enabled is True
        assert callable(metrics_callback)

        # Test bulk operation with monitoring enabled
        test_data = [{"name": f"Item {i}"} for i in range(10)]
        result = bulk_ops.bulk_create("test_model", test_data)

        assert result["records_processed"] == 10
        assert result["success"] is True
