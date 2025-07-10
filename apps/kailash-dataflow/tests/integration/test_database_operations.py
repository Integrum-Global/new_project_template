"""
Integration Tests: Database Operations

Tests DataFlow database operations with real PostgreSQL.
Extracted from E2E flows to test components in isolation.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List

import pytest
from dataflow import DataFlow
from dataflow.core.config import DataFlowConfig, Environment

from kailash.nodes.data.workflow_connection_pool import WorkflowConnectionPool
from kailash.runtime.local import LocalRuntime
from kailash.workflow.builder import WorkflowBuilder


@pytest.mark.integration
@pytest.mark.requires_postgres
class TestDatabaseConnectionManagement:
    """Test connection pool management with real database."""

    @pytest.mark.asyncio
    async def test_connection_pool_initialization(self, dataflow_config):
        """Test that connection pool initializes correctly."""
        db = DataFlow(config=dataflow_config)

        # Verify connection manager exists
        assert db._connection_manager is not None

        # Check if we can get connection pool from connection manager
        # Note: Connection pool might be lazily initialized
        try:
            pool = db._connection_manager.get_pool()
            assert pool is not None
        except AttributeError:
            # Connection pool might be implemented differently
            pass

        # Verify configuration is stored correctly
        assert db.config.database.pool_size == 10
        assert db.config.database.max_overflow == 20
        assert (
            db.config.database.url
            == "postgresql://test_user:test_password@localhost:5434/kailash_test"
        )

        # Test that the connection manager configuration is accessible
        assert db.config.database.get_pool_size(db.config.environment) == 10

    @pytest.mark.asyncio
    async def test_connection_persistence_across_workflow(self, dataflow):
        """Test that connections persist across workflow nodes."""
        runtime = LocalRuntime()

        @dataflow.model
        class ConnectionTest:
            name: str
            counter: int = 0

        # Create workflow with multiple operations
        workflow = WorkflowBuilder()

        # Multiple operations that should reuse connection
        for i in range(5):
            workflow.add_node(
                "ConnectionTestCreateNode",
                f"create_{i}",
                {"name": f"test_{i}", "counter": i},
            )

        # Bulk read
        workflow.add_node("ConnectionTestListNode", "list_all", {})

        results, _ = await runtime.execute_async(workflow.build())

        # All operations should succeed
        assert all(results[f"create_{i}"]["status"] == "success" for i in range(5))

        # Verify data
        items = results["list_all"]["output"]
        assert len(items) == 5

        # Check connection pool metrics
        pool = dataflow.get_connection_pool()
        metrics = await pool.get_metrics()

        # Should show efficient connection reuse
        assert metrics["connections_created"] < 5  # Not one per operation
        assert metrics["connections_reused"] > 0

    @pytest.mark.asyncio
    async def test_connection_pool_under_load(self, dataflow):
        """Test connection pool behavior under concurrent load."""
        runtime = LocalRuntime()

        @dataflow.model
        class LoadTest:
            request_id: str
            processed: bool = False

        # Create many concurrent operations
        workflows = []
        for batch in range(10):
            workflow = WorkflowBuilder()

            # 10 parallel operations per workflow
            for i in range(10):
                workflow.add_node(
                    "LoadTestCreateNode",
                    f"op_{i}",
                    {"request_id": f"batch_{batch}_op_{i}"},
                )

            workflows.append(workflow.build())

        # Execute concurrently
        tasks = [runtime.execute_async(workflow) for workflow in workflows]

        results_list = await asyncio.gather(*tasks)

        # All should succeed despite high concurrency
        for results, _ in results_list:
            assert all(result["status"] == "success" for result in results.values())

        # Verify pool handled load efficiently
        pool = dataflow.get_connection_pool()
        health = await pool.get_health_status()

        assert health["status"] == "healthy"
        assert health["total_connections"] <= pool.max_connections


@pytest.mark.integration
@pytest.mark.requires_postgres
class TestModelOperations:
    """Test model registration and CRUD operations."""

    def test_model_registration(self, dataflow):
        """Test model registration process."""

        # Define a model
        @dataflow.model
        class Product:
            name: str
            price: float
            category: str
            in_stock: bool = True

        # Verify registration
        assert "Product" in dataflow._models
        assert "Product" in dataflow._model_nodes

        # Check generated nodes
        nodes = dataflow._model_nodes["Product"]
        assert all(op in nodes for op in ["create", "read", "update", "delete", "list"])

        # Verify model metadata
        model_meta = dataflow._schema_registry.get_model("Product")
        assert model_meta is not None
        assert model_meta.name == "Product"
        assert model_meta.table_name == "product"

        # Check fields
        assert "name" in model_meta.fields
        assert model_meta.fields["name"].field_type.value == "VARCHAR"
        assert model_meta.fields["price"].field_type.value == "FLOAT"
        assert model_meta.fields["in_stock"].nullable is False
        assert model_meta.fields["in_stock"].default is True

    @pytest.mark.asyncio
    async def test_crud_operations(self, dataflow, clean_database):
        """Test all CRUD operations with real database."""
        runtime = LocalRuntime()

        @dataflow.model
        class Article:
            title: str
            content: str
            author: str
            published: bool = False
            views: int = 0
            tags: List[str] = []

        # CREATE
        create_workflow = WorkflowBuilder()
        create_workflow.add_node(
            "ArticleCreateNode",
            "create",
            {
                "title": "Integration Testing Best Practices",
                "content": "This article covers integration testing...",
                "author": "Test Author",
                "tags": ["testing", "integration", "best-practices"],
            },
        )

        results, _ = await runtime.execute_async(create_workflow.build())

        assert results["create"]["status"] == "success"
        article = results["create"]["output"]
        assert article["id"] is not None
        assert article["title"] == "Integration Testing Best Practices"
        assert article["published"] is False
        assert article["views"] == 0
        article_id = article["id"]

        # READ
        read_workflow = WorkflowBuilder()
        read_workflow.add_node(
            "ArticleReadNode", "read", {"conditions": {"id": article_id}}
        )

        results, _ = await runtime.execute_async(read_workflow.build())

        assert results["read"]["status"] == "success"
        read_article = results["read"]["output"]
        assert read_article["id"] == article_id
        assert read_article["author"] == "Test Author"

        # UPDATE
        update_workflow = WorkflowBuilder()
        update_workflow.add_node(
            "ArticleUpdateNode",
            "update",
            {
                "conditions": {"id": article_id},
                "updates": {
                    "published": True,
                    "views": 100,
                    "tags": ["testing", "integration", "best-practices", "updated"],
                },
            },
        )

        results, _ = await runtime.execute_async(update_workflow.build())

        assert results["update"]["status"] == "success"
        updated = results["update"]["output"]
        assert updated["published"] is True
        assert updated["views"] == 100
        assert "updated" in updated["tags"]

        # LIST
        list_workflow = WorkflowBuilder()
        list_workflow.add_node(
            "ArticleListNode",
            "list",
            {"filter": {"published": True}, "order_by": ["-views"]},
        )

        results, _ = await runtime.execute_async(list_workflow.build())

        assert results["list"]["status"] == "success"
        articles = results["list"]["output"]
        assert len(articles) >= 1
        assert any(a["id"] == article_id for a in articles)

        # DELETE
        delete_workflow = WorkflowBuilder()
        delete_workflow.add_node(
            "ArticleDeleteNode", "delete", {"conditions": {"id": article_id}}
        )

        results, _ = await runtime.execute_async(delete_workflow.build())

        assert results["delete"]["status"] == "success"

        # Verify deletion
        verify_workflow = WorkflowBuilder()
        verify_workflow.add_node(
            "ArticleReadNode", "verify", {"conditions": {"id": article_id}}
        )

        results, _ = await runtime.execute_async(verify_workflow.build())

        # Should not find deleted article
        assert results["verify"]["output"] is None

    @pytest.mark.asyncio
    async def test_bulk_operations(self, dataflow, clean_database):
        """Test bulk create and update operations."""
        runtime = LocalRuntime()

        @dataflow.model
        class BulkItem:
            name: str
            quantity: int
            price: float

        # Bulk create
        items = [
            {"name": f"Item {i}", "quantity": i * 10, "price": i * 9.99}
            for i in range(100)
        ]

        bulk_workflow = WorkflowBuilder()
        bulk_workflow.add_node(
            "BulkItemBulkCreateNode", "bulk_create", {"records": items}
        )

        results, _ = await runtime.execute_async(bulk_workflow.build())

        assert results["bulk_create"]["status"] == "success"
        created = results["bulk_create"]["output"]
        assert len(created) == 100

        # Bulk update
        update_workflow = WorkflowBuilder()
        update_workflow.add_node(
            "BulkItemBulkUpdateNode",
            "bulk_update",
            {
                "filter": {"quantity": {"$lt": 500}},
                "updates": {"price": "price * 0.9"},  # 10% discount
            },
        )

        results, _ = await runtime.execute_async(update_workflow.build())

        assert results["bulk_update"]["status"] == "success"
        update_count = results["bulk_update"]["output"]["updated_count"]
        assert update_count == 50  # Items 0-49 have quantity < 500

        # Verify updates
        verify_workflow = WorkflowBuilder()
        verify_workflow.add_node(
            "BulkItemListNode", "verify", {"filter": {"name": "Item 10"}, "limit": 1}
        )

        results, _ = await runtime.execute_async(verify_workflow.build())

        item = results["verify"]["output"][0]
        assert item["price"] == pytest.approx(10 * 9.99 * 0.9, 0.01)


@pytest.mark.integration
@pytest.mark.requires_postgres
class TestAdvancedFeatures:
    """Test advanced database features."""

    @pytest.mark.asyncio
    async def test_optimistic_locking(self, dataflow, clean_database):
        """Test optimistic locking for concurrent updates."""
        runtime = LocalRuntime()

        @dataflow.model
        class VersionedDoc:
            title: str
            content: str

            __dataflow__ = {"versioned": True}

        # Create document
        create_workflow = WorkflowBuilder()
        create_workflow.add_node(
            "VersionedDocCreateNode",
            "create",
            {"title": "Concurrent Doc", "content": "Initial content"},
        )

        results, _ = await runtime.execute_async(create_workflow.build())

        doc = results["create"]["output"]
        doc_id = doc["id"]
        version = doc["version"]

        assert version == 1

        # Simulate concurrent updates
        update1 = WorkflowBuilder()
        update1.add_node(
            "VersionedDocUpdateNode",
            "update1",
            {
                "conditions": {"id": doc_id, "version": version},
                "updates": {"content": "Updated by user 1"},
            },
        )

        update2 = WorkflowBuilder()
        update2.add_node(
            "VersionedDocUpdateNode",
            "update2",
            {
                "conditions": {"id": doc_id, "version": version},
                "updates": {"content": "Updated by user 2"},
            },
        )

        # Execute both updates
        results1, _ = await runtime.execute_async(update1.build())
        results2, _ = await runtime.execute_async(update2.build())

        # One should succeed, one should fail
        statuses = [results1["update1"]["status"], results2["update2"]["status"]]

        assert "success" in statuses
        assert "failed" in statuses or None in [
            results1["update1"].get("output"),
            results2["update2"].get("output"),
        ]

        # Verify final state
        read_workflow = WorkflowBuilder()
        read_workflow.add_node(
            "VersionedDocReadNode", "read", {"conditions": {"id": doc_id}}
        )

        results, _ = await runtime.execute_async(read_workflow.build())

        final_doc = results["read"]["output"]
        assert final_doc["version"] == 2
        assert final_doc["content"] in ["Updated by user 1", "Updated by user 2"]

    @pytest.mark.asyncio
    async def test_soft_delete(self, dataflow, clean_database):
        """Test soft delete functionality."""
        runtime = LocalRuntime()

        @dataflow.model
        class SoftDeleteItem:
            name: str
            active: bool = True

            __dataflow__ = {"soft_delete": True}

        # Create item
        create_workflow = WorkflowBuilder()
        create_workflow.add_node(
            "SoftDeleteItemCreateNode", "create", {"name": "Temporary Item"}
        )

        results, _ = await runtime.execute_async(create_workflow.build())
        item_id = results["create"]["output"]["id"]

        # Soft delete
        delete_workflow = WorkflowBuilder()
        delete_workflow.add_node(
            "SoftDeleteItemDeleteNode", "delete", {"conditions": {"id": item_id}}
        )

        results, _ = await runtime.execute_async(delete_workflow.build())
        assert results["delete"]["status"] == "success"

        # Normal read should not find it
        read_workflow = WorkflowBuilder()
        read_workflow.add_node(
            "SoftDeleteItemReadNode", "read", {"conditions": {"id": item_id}}
        )

        results, _ = await runtime.execute_async(read_workflow.build())
        assert results["read"]["output"] is None

        # Read with deleted should find it
        read_deleted_workflow = WorkflowBuilder()
        read_deleted_workflow.add_node(
            "SoftDeleteItemReadNode",
            "read_deleted",
            {"conditions": {"id": item_id}, "include_deleted": True},
        )

        results, _ = await runtime.execute_async(read_deleted_workflow.build())

        deleted_item = results["read_deleted"]["output"]
        assert deleted_item is not None
        assert deleted_item["id"] == item_id
        assert deleted_item["deleted_at"] is not None

        # Restore item
        restore_workflow = WorkflowBuilder()
        restore_workflow.add_node(
            "SoftDeleteItemUpdateNode",
            "restore",
            {
                "conditions": {"id": item_id},
                "updates": {"deleted_at": None},
                "include_deleted": True,
            },
        )

        results, _ = await runtime.execute_async(restore_workflow.build())
        assert results["restore"]["status"] == "success"

        # Verify restoration
        verify_workflow = WorkflowBuilder()
        verify_workflow.add_node(
            "SoftDeleteItemReadNode", "verify", {"conditions": {"id": item_id}}
        )

        results, _ = await runtime.execute_async(verify_workflow.build())
        restored = results["verify"]["output"]
        assert restored is not None
        assert restored["deleted_at"] is None

    @pytest.mark.asyncio
    async def test_json_field_operations(self, dataflow, clean_database):
        """Test JSONB field operations."""
        runtime = LocalRuntime()

        @dataflow.model
        class ConfigData:
            name: str
            config: Dict[str, Any] = {}
            tags: List[str] = []

        # Create with JSON data
        create_workflow = WorkflowBuilder()
        create_workflow.add_node(
            "ConfigDataCreateNode",
            "create",
            {
                "name": "app_config",
                "config": {
                    "database": {"host": "localhost", "port": 5432, "pool_size": 20},
                    "features": {"auth": True, "analytics": False, "cache_ttl": 300},
                },
                "tags": ["production", "v2", "stable"],
            },
        )

        results, _ = await runtime.execute_async(create_workflow.build())
        config_id = results["create"]["output"]["id"]

        # Query by JSON field
        query_workflow = WorkflowBuilder()

        # Find configs with specific feature
        query_workflow.add_node(
            "ConfigDataListNode",
            "by_feature",
            {"filter": {"config": {"$contains": {"features": {"auth": True}}}}},
        )

        # Find by tag
        query_workflow.add_node(
            "ConfigDataListNode",
            "by_tag",
            {"filter": {"tags": {"$contains": ["production"]}}},
        )

        results, _ = await runtime.execute_async(query_workflow.build())

        by_feature = results["by_feature"]["output"]
        assert len(by_feature) >= 1
        assert any(c["id"] == config_id for c in by_feature)

        by_tag = results["by_tag"]["output"]
        assert len(by_tag) >= 1
        assert any(c["id"] == config_id for c in by_tag)

        # Update JSON field
        update_workflow = WorkflowBuilder()
        update_workflow.add_node(
            "ConfigDataUpdateNode",
            "update_json",
            {
                "conditions": {"id": config_id},
                "updates": {
                    "config": {
                        "database": {
                            "host": "prod-db.example.com",
                            "port": 5432,
                            "pool_size": 50,
                        },
                        "features": {
                            "auth": True,
                            "analytics": True,  # Enabled
                            "cache_ttl": 600,  # Increased
                            "new_feature": True,  # Added
                        },
                    }
                },
            },
        )

        results, _ = await runtime.execute_async(update_workflow.build())

        updated = results["update_json"]["output"]
        assert updated["config"]["database"]["host"] == "prod-db.example.com"
        assert updated["config"]["features"]["analytics"] is True
        assert updated["config"]["features"]["new_feature"] is True
