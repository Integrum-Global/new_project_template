"""
Integration tests for DataFlow with real database connections
Aligned with tests/utils infrastructure
"""

import time
from datetime import datetime
from typing import Any, Dict, List

import pytest
from dataflow import DataFlow
from dataflow.core.config import DataFlowConfig

from kailash.runtime.local import LocalRuntime
from kailash.workflow.builder import WorkflowBuilder


@pytest.mark.requires_postgres
@pytest.mark.requires_docker
class TestDataFlowRealDatabase:
    """Test DataFlow with real PostgreSQL database."""

    @pytest.fixture
    def real_dataflow(self, test_database_url):
        """Create DataFlow with real database connection."""
        config = DataFlowConfig(
            database_url=test_database_url,
            pool_size=10,
            echo=True,  # Enable SQL logging for debugging
            cache_enabled=True,
            audit_logging=True,
        )

        db = DataFlow(config=config)

        # Define test models
        @db.model
        class TestUser:
            name: str
            email: str
            age: int
            active: bool = True

            __dataflow__ = {
                "indexes": [{"name": "idx_email", "fields": ["email"], "unique": True}]
            }

        @db.model
        class TestOrder:
            user_id: int
            total: float
            status: str = "pending"
            items: List[Dict[str, Any]] = []

            __dataflow__ = {
                "indexes": [
                    {"name": "idx_user_orders", "fields": ["user_id", "created_at"]}
                ]
            }

        yield db

        # Cleanup would happen here

    def test_real_database_connection(self, real_dataflow):
        """Test actual database connection."""
        # In a real implementation, this would test actual connection
        assert real_dataflow.health_check() is True
        assert real_dataflow.ready_check() is True

    def test_crud_operations_real_database(self, real_dataflow, runtime):
        """Test CRUD operations with real database."""
        workflow = WorkflowBuilder()

        # Create user
        workflow.add_node(
            "TestUserCreateNode",
            "create_user",
            {"name": "John Doe", "email": "john@example.com", "age": 30},
        )

        # Read user
        workflow.add_node("TestUserReadNode", "read_user", {"id": ":user_id"})

        # Update user
        workflow.add_node(
            "TestUserUpdateNode", "update_user", {"id": ":user_id", "age": 31}
        )

        # List users
        workflow.add_node(
            "TestUserListNode", "list_users", {"filter": {"active": True}}
        )

        # Connect workflow
        workflow.add_connection("create_user", "read_user", "id", "user_id")
        workflow.add_connection("read_user", "update_user", "id", "user_id")

        # Execute workflow
        results, run_id = runtime.execute(workflow.build())

        # Verify results
        assert results["create_user"]["success"] is True
        assert results["create_user"]["data"]["name"] == "John Doe"

        assert results["read_user"]["success"] is True
        assert results["read_user"]["data"]["email"] == "john@example.com"

        assert results["update_user"]["success"] is True
        assert results["update_user"]["data"]["age"] == 31

        assert results["list_users"]["success"] is True
        assert len(results["list_users"]["data"]) >= 1

    def test_bulk_operations_real_database(self, real_dataflow, runtime):
        """Test bulk operations with real database."""
        # Generate test data
        users = []
        for i in range(1000):
            users.append(
                {
                    "name": f"User {i}",
                    "email": f"user{i}@example.com",
                    "age": 20 + (i % 50),
                }
            )

        workflow = WorkflowBuilder()

        # Bulk create
        workflow.add_node(
            "TestUserBulkCreateNode", "bulk_create", {"data": users, "batch_size": 100}
        )

        # Verify count
        workflow.add_node("TestUserListNode", "count_users", {"count_only": True})

        # Execute
        start_time = time.time()
        results, run_id = runtime.execute(workflow.build())
        end_time = time.time()

        # Verify results
        assert results["bulk_create"]["success"] is True
        assert results["bulk_create"]["success_count"] == 1000
        assert results["bulk_create"]["failure_count"] == 0

        # Performance check
        duration = end_time - start_time
        records_per_second = 1000 / duration
        print(f"Bulk insert performance: {records_per_second:.2f} records/second")

        # Should be reasonably fast
        assert duration < 10.0  # Less than 10 seconds for 1000 records

    def test_transaction_management(self, real_dataflow, runtime):
        """Test transaction management with real database."""
        workflow = WorkflowBuilder()

        # Start transaction
        workflow.add_node(
            "TransactionContextNode", "start_tx", {"isolation_level": "READ_COMMITTED"}
        )

        # Create user
        workflow.add_node(
            "TestUserCreateNode",
            "create_user",
            {"name": "Transaction Test", "email": "tx@example.com", "age": 25},
        )

        # Create order for user
        workflow.add_node(
            "TestOrderCreateNode",
            "create_order",
            {
                "user_id": ":user_id",
                "total": 100.00,
                "items": [{"product": "Item 1", "quantity": 2, "price": 50.00}],
            },
        )

        # Commit transaction
        workflow.add_node("TransactionCommitNode", "commit_tx", {})

        # Connect workflow
        workflow.add_connection("start_tx", "create_user")
        workflow.add_connection("create_user", "create_order", "id", "user_id")
        workflow.add_connection("create_order", "commit_tx")

        # Execute
        results, run_id = runtime.execute(workflow.build())

        # Verify transaction completed
        assert results["create_user"]["success"] is True
        assert results["create_order"]["success"] is True

    def test_query_performance(self, real_dataflow, runtime):
        """Test query performance with real database."""
        # First create test data
        workflow = WorkflowBuilder()

        # Create users with different ages
        users = []
        for i in range(100):
            users.append(
                {
                    "name": f"Query Test {i}",
                    "email": f"query{i}@example.com",
                    "age": 18 + (i % 50),
                    "active": i % 3 != 0,
                }
            )

        workflow.add_node("TestUserBulkCreateNode", "create_users", {"data": users})

        # Execute setup
        runtime.execute(workflow.build())

        # Test various queries
        query_workflow = WorkflowBuilder()

        # Query 1: Filter by age range
        query_workflow.add_node(
            "TestUserListNode",
            "query_age_range",
            {"filter": {"age": {"$gte": 25, "$lte": 35}}, "order_by": ["age", "name"]},
        )

        # Query 2: Complex filter
        query_workflow.add_node(
            "TestUserListNode",
            "query_complex",
            {
                "filter": {
                    "$and": [
                        {"active": True},
                        {"age": {"$gte": 30}},
                        {"email": {"$regex": "query[0-9]+@"}},
                    ]
                }
            },
        )

        # Query 3: Aggregation
        query_workflow.add_node(
            "TestUserListNode",
            "query_aggregate",
            {
                "group_by": "active",
                "aggregations": {
                    "count": {"$count": "*"},
                    "avg_age": {"$avg": "age"},
                    "min_age": {"$min": "age"},
                    "max_age": {"$max": "age"},
                },
            },
        )

        # Execute queries
        start_time = time.time()
        results, run_id = runtime.execute(query_workflow.build())
        query_time = time.time() - start_time

        # Verify results
        assert results["query_age_range"]["success"] is True
        assert results["query_complex"]["success"] is True
        assert results["query_aggregate"]["success"] is True

        # Performance check
        print(f"Query execution time: {query_time:.3f} seconds")
        assert query_time < 1.0  # Queries should be fast


@pytest.mark.requires_redis
@pytest.mark.requires_docker
class TestDataFlowWithCache:
    """Test DataFlow with Redis caching."""

    @pytest.fixture
    def cached_dataflow(self, test_database_url, test_redis_url):
        """Create DataFlow with caching enabled."""
        config = DataFlowConfig(
            database_url=test_database_url,
            cache_enabled=True,
            cache_ttl=60,  # 1 minute TTL for tests
        )

        # In real implementation, would configure Redis URL
        db = DataFlow(config=config)

        @db.model
        class CachedProduct:
            name: str
            price: float
            category: str

        return db

    def test_cache_operations(self, cached_dataflow, runtime):
        """Test caching functionality."""
        workflow = WorkflowBuilder()

        # Create product
        workflow.add_node(
            "CachedProductCreateNode",
            "create_product",
            {"name": "Cached Item", "price": 29.99, "category": "electronics"},
        )

        # Read product (should cache)
        workflow.add_node("CachedProductReadNode", "read_1", {"id": ":product_id"})

        # Read again (should hit cache)
        workflow.add_node("CachedProductReadNode", "read_2", {"id": ":product_id"})

        # Update product (should invalidate cache)
        workflow.add_node(
            "CachedProductUpdateNode",
            "update_product",
            {"id": ":product_id", "price": 24.99},
        )

        # Read after update (should miss cache)
        workflow.add_node("CachedProductReadNode", "read_3", {"id": ":product_id"})

        # Connect workflow
        workflow.add_connection("create_product", "read_1", "id", "product_id")
        workflow.add_connection("read_1", "read_2", "id", "product_id")
        workflow.add_connection("read_2", "update_product", "id", "product_id")
        workflow.add_connection("update_product", "read_3", "id", "product_id")

        # Execute and measure timing
        results, run_id = runtime.execute(workflow.build())

        # Verify all operations succeeded
        assert results["create_product"]["success"] is True
        assert results["read_1"]["success"] is True
        assert results["read_2"]["success"] is True
        assert results["update_product"]["success"] is True
        assert results["read_3"]["success"] is True

        # Verify data consistency
        assert results["read_3"]["data"]["price"] == 24.99
