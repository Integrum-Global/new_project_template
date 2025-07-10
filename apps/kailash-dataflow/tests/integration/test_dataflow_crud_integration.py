"""Integration tests for DataFlow CRUD operations with real database."""

import pytest

from kailash.runtime.local import LocalRuntime
from kailash.workflow.builder import WorkflowBuilder


@pytest.mark.requires_postgres
class TestDataFlowCRUDIntegration:
    """Test DataFlow CRUD operations with real PostgreSQL."""

    @pytest.mark.asyncio
    async def test_create_and_read_workflow(self, dataflow, sample_models, runtime):
        """Test creating and reading records through workflow."""
        # Create models
        User, Post, Comment = sample_models(dataflow)

        # Create workflow
        workflow = WorkflowBuilder()

        # Create user
        workflow.add_node(
            "UserCreateNode",
            "create_user",
            {"name": "Test User", "email": "test@example.com"},
        )

        # Read user back
        workflow.add_node("UserReadNode", "read_user")

        # Connect nodes - pass user ID from create to read
        workflow.add_connection("create_user", "id", "read_user", "id")

        # Execute workflow
        results, run_id = runtime.execute(workflow.build())

        # Verify results
        assert results["create_user"]["data"]["name"] == "Test User"
        assert results["create_user"]["data"]["email"] == "test@example.com"
        assert (
            results["read_user"]["data"]["id"] == results["create_user"]["data"]["id"]
        )

    @pytest.mark.asyncio
    async def test_update_workflow(self, dataflow, sample_models, runtime):
        """Test updating records through workflow."""
        User, _, _ = sample_models(dataflow)

        workflow = WorkflowBuilder()

        # Create user
        workflow.add_node(
            "UserCreateNode",
            "create_user",
            {"name": "Original Name", "email": "original@example.com"},
        )

        # Update user
        workflow.add_node("UserUpdateNode", "update_user", {"name": "Updated Name"})

        # Read updated user
        workflow.add_node("UserReadNode", "read_user")

        # Connect nodes
        workflow.add_connection("create_user", "id", "update_user", "id")
        workflow.add_connection("update_user", "id", "read_user", "id")

        # Execute
        results, run_id = runtime.execute(workflow.build())

        # Verify update
        assert results["read_user"]["data"]["name"] == "Updated Name"
        assert results["read_user"]["data"]["email"] == "original@example.com"

    @pytest.mark.asyncio
    async def test_list_with_filters(self, dataflow, sample_models, runtime, test_data):
        """Test listing records with filters."""
        User, Post, _ = sample_models(dataflow)

        workflow = WorkflowBuilder()

        # Create multiple users
        for i, user_data in enumerate(test_data["users"]):
            workflow.add_node("UserCreateNode", f"create_user_{i}", user_data)

        # List active users
        workflow.add_node(
            "UserListNode",
            "list_active",
            {"filter": {"active": True}, "order_by": ["name"]},
        )

        # Execute
        results, run_id = runtime.execute(workflow.build())

        # Verify list results
        users = results["list_active"]["data"]
        assert len(users) == 3  # All test users are active by default
        assert users[0]["name"] == "Alice Smith"  # Ordered by name

    @pytest.mark.asyncio
    async def test_bulk_operations(self, dataflow, sample_models, runtime, test_data):
        """Test bulk create operations."""
        _, Post, _ = sample_models(dataflow)

        workflow = WorkflowBuilder()

        # First create a user to be the author
        workflow.add_node(
            "UserCreateNode",
            "create_author",
            {"name": "Author", "email": "author@example.com"},
        )

        # Bulk create posts
        workflow.add_node(
            "PostBulkCreateNode", "bulk_create_posts", {"data": test_data["posts"]}
        )

        # List all posts
        workflow.add_node("PostListNode", "list_posts")

        # Execute
        results, run_id = runtime.execute(
            workflow.build(),
            {
                "bulk_create_posts": {
                    "data": [{**post, "author_id": 1} for post in test_data["posts"]]
                }
            },
        )

        # Verify bulk creation
        posts = results["list_posts"]["data"]
        assert len(posts) == len(test_data["posts"])

    @pytest.mark.asyncio
    async def test_delete_workflow(self, dataflow, sample_models, runtime):
        """Test deleting records."""
        User, _, _ = sample_models(dataflow)

        workflow = WorkflowBuilder()

        # Create user
        workflow.add_node(
            "UserCreateNode",
            "create_user",
            {"name": "To Delete", "email": "delete@example.com"},
        )

        # Delete user
        workflow.add_node("UserDeleteNode", "delete_user")

        # Try to read deleted user
        workflow.add_node("UserReadNode", "read_deleted", {"raise_on_not_found": False})

        # Connect nodes
        workflow.add_connection("create_user", "id", "delete_user", "id")
        workflow.add_connection("delete_user", "id", "read_deleted", "id")

        # Execute
        results, run_id = runtime.execute(workflow.build())

        # Verify deletion
        assert results["delete_user"]["success"] is True
        assert results["read_deleted"]["found"] is False

    @pytest.mark.asyncio
    async def test_transaction_workflow(self, dataflow, sample_models, runtime):
        """Test transactional workflow operations."""
        User, Post, Comment = sample_models(dataflow)

        workflow = WorkflowBuilder()

        # Start transaction context
        workflow.add_node("TransactionContextNode", "txn_start", {"operation": "begin"})

        # Create user
        workflow.add_node(
            "UserCreateNode",
            "create_user",
            {"name": "Transaction User", "email": "txn@example.com"},
        )

        # Create post for user
        workflow.add_node(
            "PostCreateNode",
            "create_post",
            {"title": "Transaction Post", "content": "Testing transactions"},
        )

        # Commit transaction
        workflow.add_node(
            "TransactionContextNode", "txn_commit", {"operation": "commit"}
        )

        # Connect nodes
        workflow.add_connection("txn_start", "context", "create_user", "transaction")
        workflow.add_connection("create_user", "id", "create_post", "author_id")
        workflow.add_connection("create_post", "result", "txn_commit", "data")

        # Execute
        results, run_id = runtime.execute(workflow.build())

        # Verify transaction completed
        assert results["txn_commit"]["status"] == "committed"

    @pytest.mark.asyncio
    async def test_relationship_loading(self, dataflow, sample_models, runtime):
        """Test loading relationships."""
        User, Post, Comment = sample_models(dataflow)

        # Create test data
        workflow = WorkflowBuilder()

        # Create user
        workflow.add_node(
            "UserCreateNode",
            "create_user",
            {"name": "Post Author", "email": "author@example.com"},
        )

        # Create posts
        workflow.add_node(
            "PostCreateNode",
            "create_post1",
            {"title": "First Post", "content": "Content 1"},
        )

        workflow.add_node(
            "PostCreateNode",
            "create_post2",
            {"title": "Second Post", "content": "Content 2"},
        )

        # Connect author to posts
        workflow.add_connection("create_user", "id", "create_post1", "author_id")
        workflow.add_connection("create_user", "id", "create_post2", "author_id")

        # Execute setup
        results, _ = runtime.execute(workflow.build())
        user_id = results["create_user"]["data"]["id"]

        # Now test loading with relationships
        load_workflow = WorkflowBuilder()
        load_workflow.add_node(
            "UserReadNode", "load_user", {"id": user_id, "include": ["posts"]}
        )

        # Execute load
        load_results, _ = runtime.execute(load_workflow.build())

        # Verify relationships loaded
        user = load_results["load_user"]["data"]
        assert len(user["posts"]) == 2
        assert user["posts"][0]["title"] in ["First Post", "Second Post"]
