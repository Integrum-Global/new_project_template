"""
Integration Tests: Startup Developer (Sarah) - Zero to First Query Flow

Tests for the critical "Zero to First Query in 5 minutes" user flow.
This is the most important flow for developer adoption.
"""

import time
from datetime import datetime

import pytest
from dataflow import DataFlow, DataFlowConfig

from kailash.runtime.local import LocalRuntime
from kailash.workflow.builder import WorkflowBuilder


class TestZeroToFirstQueryFlow:
    """Test Sarah's zero-to-first-query flow - Priority 1."""

    @pytest.fixture
    async def dataflow_quick_start(self):
        """Quick start DataFlow instance with minimal config."""
        # Zero-config initialization (what Sarah would actually do)
        db = DataFlow()  # Should work with SQLite by default

        yield db

        # Cleanup
        await db.cleanup_test_tables()
        await db.close()

    @pytest.mark.asyncio
    async def test_complete_zero_to_first_query_under_5_minutes(
        self, dataflow_quick_start
    ):
        """Complete zero-to-first-query flow must complete under 5 minutes."""
        db = dataflow_quick_start

        # Track total time - this is the critical metric
        start_time = time.time()

        # STEP 1: Define first model (should be instant)
        step1_start = time.time()

        @db.model
        class User:
            name: str
            email: str
            active: bool = True

        step1_time = time.time() - step1_start
        assert step1_time < 0.5  # Model definition should be instant

        # STEP 2: Create workflow (should be under 1 second)
        step2_start = time.time()

        workflow = WorkflowBuilder()
        workflow.add_node(
            "UserCreateNode",
            "create_user",
            {"name": "Sarah Startup", "email": "sarah@startup.com"},
        )

        step2_time = time.time() - step2_start
        assert step2_time < 1.0  # Workflow creation should be fast

        # STEP 3: Execute first operation (should be under 2 seconds)
        step3_start = time.time()

        runtime = LocalRuntime()
        results, run_id = runtime.execute(workflow.build())

        step3_time = time.time() - step3_start
        assert step3_time < 2.0  # First execution should be fast

        # STEP 4: Verify results (immediate)
        step4_start = time.time()

        assert results is not None
        assert "create_user" in results

        user = results["create_user"]
        assert user["name"] == "Sarah Startup"
        assert user["email"] == "sarah@startup.com"
        assert user["active"] is True
        assert "id" in user  # Should have auto-generated ID

        step4_time = time.time() - step4_start
        assert step4_time < 0.1  # Verification should be instant

        # CRITICAL: Total time must be under 5 minutes (300 seconds)
        total_time = time.time() - start_time
        assert (
            total_time < 300
        ), f"Zero-to-first-query took {total_time:.2f}s, must be under 300s"

        # Ideally should be much faster (under 30 seconds for great UX)
        if total_time < 30:
            print(f"✅ EXCELLENT: Zero-to-first-query completed in {total_time:.2f}s")
        elif total_time < 60:
            print(f"✅ GOOD: Zero-to-first-query completed in {total_time:.2f}s")
        else:
            print(f"⚠️ ACCEPTABLE: Zero-to-first-query completed in {total_time:.2f}s")

    @pytest.mark.asyncio
    async def test_crud_operations_discovery(self, dataflow_quick_start):
        """Test that Sarah can discover and use all CRUD operations."""
        db = dataflow_quick_start

        @db.model
        class Product:
            name: str
            price: float
            in_stock: bool = True

        # Sarah should be able to use all generated nodes
        workflow = WorkflowBuilder()

        # CREATE
        workflow.add_node(
            "ProductCreateNode",
            "create_product",
            {"name": "Widget", "price": 19.99, "in_stock": True},
        )

        # READ (after create)
        workflow.add_node(
            "ProductReadNode", "read_product", {"filter": {"name": "Widget"}}
        )

        # UPDATE
        workflow.add_node(
            "ProductUpdateNode",
            "update_product",
            {"filter": {"name": "Widget"}, "updates": {"price": 24.99}},
        )

        # LIST (find all products)
        workflow.add_node(
            "ProductListNode",
            "list_products",
            {"filter": {"in_stock": True}, "limit": 10},
        )

        # Connect operations logically
        workflow.add_connection("create_product", "read_product", "id", "id")
        workflow.add_connection("read_product", "update_product", "id", "id")
        workflow.add_connection("update_product", "list_products", "", "")

        runtime = LocalRuntime()
        results, _ = runtime.execute(workflow.build())

        # Verify all CRUD operations work
        created_product = results["create_product"]
        read_product = results["read_product"]
        updated_product = results["update_product"]
        product_list = results["list_products"]

        assert created_product["name"] == "Widget"
        assert created_product["price"] == 19.99

        assert read_product["id"] == created_product["id"]
        assert read_product["name"] == "Widget"

        assert updated_product["price"] == 24.99  # Should be updated

        assert len(product_list) >= 1
        assert any(p["name"] == "Widget" for p in product_list)

    @pytest.mark.asyncio
    async def test_error_handling_is_beginner_friendly(self, dataflow_quick_start):
        """Test that error messages are helpful for beginners."""
        db = dataflow_quick_start

        @db.model
        class Customer:
            email: str
            age: int

            def validate_email(self, email: str) -> str:
                if "@" not in email:
                    raise ValueError("Email must contain @ symbol")
                return email

            def validate_age(self, age: int) -> int:
                if age < 0:
                    raise ValueError("Age cannot be negative")
                return age

        # Test validation error handling
        workflow = WorkflowBuilder()

        workflow.add_node(
            "CustomerCreateNode",
            "create_invalid_customer",
            {"email": "invalid-email", "age": -5},  # Missing @  # Negative age
        )

        runtime = LocalRuntime()

        # Should handle validation errors gracefully
        try:
            results, _ = runtime.execute(workflow.build())
            # If no exception, check for error in results
            if "create_invalid_customer" in results:
                result = results["create_invalid_customer"]
                if "error" in result:
                    error_msg = result["error"]
                    assert (
                        "Email must contain @ symbol" in error_msg
                        or "Age cannot be negative" in error_msg
                    )
        except Exception as e:
            # Error message should be helpful
            error_msg = str(e)
            assert "Email" in error_msg or "Age" in error_msg
            assert "validation" in error_msg.lower() or "invalid" in error_msg.lower()

    @pytest.mark.asyncio
    async def test_multiple_model_relationships(self, dataflow_quick_start):
        """Test that Sarah can easily create related models."""
        db = dataflow_quick_start

        @db.model
        class Author:
            name: str
            email: str

        @db.model
        class BlogPost:
            title: str
            content: str
            author_id: int  # Foreign key
            published: bool = False

        # Create related data workflow
        workflow = WorkflowBuilder()

        workflow.add_node(
            "AuthorCreateNode",
            "create_author",
            {"name": "Sarah Writer", "email": "sarah@writer.com"},
        )

        workflow.add_node(
            "BlogPostCreateNode",
            "create_post",
            {
                "title": "Getting Started with DataFlow",
                "content": "DataFlow makes database operations incredibly easy...",
                "published": True,
            },
        )

        # Relationship connection
        workflow.add_connection("create_author", "create_post", "id", "author_id")

        runtime = LocalRuntime()
        results, _ = runtime.execute(workflow.build())

        # Verify relationships work correctly
        author = results["create_author"]
        post = results["create_post"]

        assert author["name"] == "Sarah Writer"
        assert post["title"] == "Getting Started with DataFlow"
        assert post["author_id"] == author["id"]  # Relationship should be set
        assert post["published"] is True

    def test_zero_config_database_connection(self):
        """Test that DataFlow works with zero configuration."""
        # This should work without any configuration
        db = DataFlow()

        # Should have working config
        assert db.config is not None
        assert db.config.database_url is not None

        # Should use SQLite by default for development
        assert "sqlite" in db.config.database_url.lower()

        # Should have reasonable defaults
        assert db.config.pool_size > 0
        assert db.config.max_overflow >= db.config.pool_size
