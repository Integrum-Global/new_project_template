"""Example of using workflow-level parameter injection for user management.

This example demonstrates the new parameter injection feature that allows
passing parameters directly to runtime.execute() without manual node mapping.
"""

import asyncio
import os

from kailash import Workflow, WorkflowBuilder
from kailash.nodes.admin import RoleManagementNode, UserManagementNode
from kailash.nodes.code import PythonCodeNode
from kailash.runtime import LocalRuntime


async def simple_workflow_example():
    """Simple example using PythonCodeNode with automatic parameter injection."""
    print("\n=== Simple Workflow Example ===")

    # Create workflow
    workflow = Workflow("user_registration", "User registration workflow")

    # Add validation node
    def validate_user(email: str, password: str) -> dict:
        return {
            "valid": "@" in email and len(password) >= 8,
            "email": email,
            "errors": [] if "@" in email else ["Invalid email format"],
        }

    # Add user creation node
    def create_user(email: str, password: str, role: str = "user") -> dict:
        return {
            "user_id": f"usr_{email.split('@')[0]}_{role}",
            "email": email,
            "role": role,
            "created": True,
        }

    # Build workflow with nodes
    workflow.add_node("validator", PythonCodeNode.from_function(validate_user))
    workflow.add_node("creator", PythonCodeNode.from_function(create_user))

    # Connect nodes
    workflow.connect("validator", "creator", {"result.email": "email"})

    # Execute with workflow-level parameters
    runtime = LocalRuntime()
    results, _ = runtime.execute(
        workflow,
        parameters={
            "email": "alice@example.com",
            "password": "secure123",
            "role": "admin",  # This goes to creator node automatically
        },
    )

    print(f"Validation result: {results['validator']['result']}")
    print(f"User created: {results['creator']['result']}")


async def workflow_builder_example():
    """Example using WorkflowBuilder with explicit input mappings."""
    print("\n=== WorkflowBuilder Example ===")

    builder = WorkflowBuilder()

    # Define nodes
    def process_signup(user_email: str, user_password: str, full_name: str) -> dict:
        first_name = full_name.split()[0] if full_name else "User"
        return {
            "email": user_email,
            "password": user_password,
            "first_name": first_name,
            "username": user_email.split("@")[0],
        }

    def create_account(
        email: str,
        password: str,
        username: str,
        first_name: str,
        account_type: str = "standard",
    ) -> dict:
        return {
            "account_id": f"acc_{username}_{account_type}",
            "email": email,
            "username": username,
            "first_name": first_name,
            "account_type": account_type,
        }

    # Add nodes
    builder.add_node(PythonCodeNode.from_function(process_signup), "signup")
    builder.add_node(PythonCodeNode.from_function(create_account), "account")

    # Define explicit input mappings
    builder.add_workflow_inputs(
        "signup",
        {
            "email": "user_email",  # Workflow "email" -> node "user_email"
            "password": "user_password",  # Workflow "password" -> node "user_password"
            "name": "full_name",  # Workflow "name" -> node "full_name"
        },
    )

    builder.add_workflow_inputs(
        "account",
        {
            "subscription": "account_type"  # Workflow "subscription" -> node "account_type"
        },
    )

    # Connect nodes
    builder.connect(
        "signup",
        "account",
        {
            "result.email": "email",
            "result.password": "password",
            "result.username": "username",
            "result.first_name": "first_name",
        },
    )

    # Build and execute
    workflow = builder.build("user_workflow")
    runtime = LocalRuntime()

    results, _ = runtime.execute(
        workflow,
        parameters={
            "email": "bob@company.com",
            "password": "verysecure456",
            "name": "Bob Smith",
            "subscription": "premium",
        },
    )

    print(f"Signup processing: {results['signup']['result']}")
    print(f"Account created: {results['account']['result']}")


async def real_user_management_example():
    """Example using real UserManagementNode with database."""
    print("\n=== Real User Management Example ===")

    # Check if database is configured
    db_url = os.getenv(
        "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/kailash_test"
    )

    # Create workflow
    workflow = Workflow("user_mgmt", "User management with database")

    # Add role creation node
    role_node = RoleManagementNode(
        operation="create_role",
        tenant_id="default",
        database_config={"connection_string": db_url, "database_type": "postgresql"},
    )
    workflow.add_node("role_creator", role_node)

    # Add user creation node
    user_node = UserManagementNode(
        operation="create_user",
        tenant_id="default",
        database_config={"connection_string": db_url, "database_type": "postgresql"},
    )
    workflow.add_node("user_creator", user_node)

    # Define workflow metadata for parameter injection
    workflow.metadata["_workflow_inputs"] = {
        "role_creator": {
            "role_name": "role_data",  # Maps workflow param to node param
            "permissions": "permissions",
        },
        "user_creator": {
            "email": "user_data",  # Nested mapping to user_data.email
            "password": "password",
        },
    }

    runtime = LocalRuntime()

    try:
        # Create admin role first
        role_results, _ = runtime.execute(
            workflow,
            parameters={
                "role_name": {"name": "admin", "description": "Administrator role"},
                "permissions": [
                    "users.create",
                    "users.read",
                    "users.update",
                    "users.delete",
                ],
            },
        )
        print(f"Role created: {role_results.get('role_creator', {}).get('result', {})}")

        # Create user with admin role
        user_results, _ = runtime.execute(
            workflow,
            parameters={
                "email": {"email": "admin@example.com", "role": "admin"},
                "password": "admin123secure",
            },
        )
        print(f"User created: {user_results.get('user_creator', {}).get('result', {})}")

    except Exception as e:
        print(f"Note: Database example requires PostgreSQL running: {e}")


async def mixed_parameter_example():
    """Example showing mixed parameter formats (backward compatibility)."""
    print("\n=== Mixed Parameter Example ===")

    workflow = Workflow("mixed", "Mixed parameter formats")

    # Nodes
    def node_a(input_a: str) -> dict:
        return {"processed_a": input_a.upper()}

    def node_b(input_b: str, config: dict = None) -> dict:
        return {"processed_b": input_b.lower(), "config": config or {}}

    workflow.add_node("node_a", PythonCodeNode.from_function(node_a))
    workflow.add_node("node_b", PythonCodeNode.from_function(node_b))

    runtime = LocalRuntime()

    # Mix workflow-level and node-specific parameters
    results, _ = runtime.execute(
        workflow,
        parameters={
            # Workflow-level parameter (goes to node_a)
            "input_a": "Hello",
            # Node-specific parameters (explicit override for node_b)
            "node_b": {"input_b": "WORLD", "config": {"debug": True}},
        },
    )

    print(f"Node A result: {results['node_a']['result']}")
    print(f"Node B result: {results['node_b']['result']}")


if __name__ == "__main__":
    print("Workflow Parameter Injection Examples")
    print("=" * 50)

    # Run all examples
    asyncio.run(simple_workflow_example())
    asyncio.run(workflow_builder_example())
    asyncio.run(real_user_management_example())
    asyncio.run(mixed_parameter_example())

    print("\n✅ Examples completed!")
    print("\nKey Takeaways:")
    print("1. Pass parameters as flat dict to runtime.execute()")
    print("2. Parameters automatically map to nodes by name")
    print("3. Use WorkflowBuilder.add_workflow_inputs() for custom mappings")
    print("4. Mix workflow-level and node-specific formats for flexibility")
    print("5. Enable debug=True on LocalRuntime to see parameter mapping")
