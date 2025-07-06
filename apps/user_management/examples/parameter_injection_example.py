"""
Example demonstrating WorkflowBuilder parameter injection.

This example shows how the Kailash SDK's parameter injection feature
simplifies workflow parameter passing by automatically mapping workflow-level
parameters to appropriate nodes.
"""

import asyncio
from datetime import datetime

from kailash.nodes.admin.role_management import RoleManagementNode
from kailash.nodes.admin.user_management import UserManagementNode
from kailash.nodes.code.python import PythonCodeNode
from kailash.runtime.local import LocalRuntime
from kailash.workflow.builder import WorkflowBuilder


def create_user_onboarding_workflow(database_url: str):
    """Create a user onboarding workflow with automatic parameter injection."""
    builder = WorkflowBuilder()

    # 1. Validation node - receives workflow parameters automatically
    def validate_and_prepare(email: str, role: str, department: str) -> dict:
        """Validate inputs and prepare user data."""
        # Validation logic
        if "@" not in email:
            raise ValueError("Invalid email format")

        # Extract username from email
        username = email.split("@")[0]

        # Prepare user data
        return {
            "user_data": {
                "email": email,
                "username": username,
                "status": "active",
                "attributes": {
                    "department": department,
                    "onboarded_at": str(datetime.now()),
                },
            },
            "role_name": role,
            "validation_passed": True,
        }

    # 2. User creation node
    builder.add_node(PythonCodeNode.from_function(validate_and_prepare), "validator")

    builder.add_node(
        UserManagementNode(
            operation="create_user",
            tenant_id="default",
            database_config={
                "connection_string": database_url,
                "database_type": "postgresql",
            },
        ),
        "user_creator",
    )

    # 3. Role assignment node
    builder.add_node(
        RoleManagementNode(
            operation="assign_role",
            tenant_id="default",
            database_config={
                "connection_string": database_url,
                "database_type": "postgresql",
            },
        ),
        "role_assigner",
    )

    # 4. Welcome email node
    def send_welcome_email(user: dict, department: str) -> dict:
        """Simulate sending welcome email."""
        return {
            "email_sent": True,
            "recipient": user["email"],
            "template": f"welcome_{department}",
            "timestamp": str(datetime.now()),
        }

    builder.add_node(PythonCodeNode.from_function(send_welcome_email), "email_sender")

    # Connect nodes
    builder.connect("validator", "user_creator", {"result.user_data": "user_data"})

    builder.connect("user_creator", "role_assigner", {"result.user.user_id": "user_id"})

    builder.connect("user_creator", "email_sender", {"result.user": "user"})

    # Define workflow input mappings
    # These mappings tell the SDK how to route workflow-level parameters to nodes
    builder.add_workflow_inputs(
        "validator",
        {
            "email": "email",  # workflow param "email" -> validator param "email"
            "role": "role",  # workflow param "role" -> validator param "role"
            "department": "department",  # workflow param "department" -> validator param "department"
        },
    )

    builder.add_workflow_inputs(
        "user_creator",
        {
            "password": "password"  # workflow param "password" -> user_creator param "password"
        },
    )

    builder.add_workflow_inputs(
        "role_assigner",
        {
            "role": "role_name"  # workflow param "role" -> role_assigner param "role_name"
        },
    )

    builder.add_workflow_inputs(
        "email_sender",
        {
            "department": "department"  # workflow param "department" -> email_sender param "department"
        },
    )

    return builder.build("user_onboarding")


async def main():
    """Demonstrate parameter injection with different approaches."""

    # Initialize runtime with debug mode to see parameter injection in action
    runtime = LocalRuntime(debug=True)

    # Create workflow
    database_url = "postgresql://test_user:test_password@localhost:5434/kailash_test"
    workflow = create_user_onboarding_workflow(database_url)

    print("=== Parameter Injection Example ===\n")

    # Example 1: Workflow-level parameters (NEW FEATURE!)
    print("1. Using workflow-level parameters (simplified approach):")
    print("   Parameters are automatically injected into appropriate nodes")

    workflow_params = {
        "email": "john.doe@company.com",
        "password": "SecurePass123!",
        "role": "analyst",
        "department": "data_science",
    }

    results1, run_id1 = await runtime.execute_async(
        workflow, parameters=workflow_params
    )

    print(
        f"\n   ✓ User created: {results1['user_creator']['result']['user']['user_id']}"
    )
    print(f"   ✓ Role assigned: {workflow_params['role']}")
    print(f"   ✓ Email sent: {results1['email_sender']['result']['email_sent']}")

    # Example 2: Node-specific parameters (traditional approach, still supported)
    print("\n2. Using node-specific parameters (traditional approach):")
    print("   Parameters are provided directly to each node")

    node_params = {
        "validator": {
            "email": "jane.smith@company.com",
            "role": "engineer",
            "department": "engineering",
        },
        "user_creator": {"password": "AnotherSecure123!"},
        "role_assigner": {"role_name": "engineer"},
        "email_sender": {"department": "engineering"},
    }

    results2, run_id2 = await runtime.execute_async(workflow, parameters=node_params)

    print(
        f"\n   ✓ User created: {results2['user_creator']['result']['user']['user_id']}"
    )
    print("   ✓ Traditional approach still works!")

    # Example 3: Mixed approach (workflow + node-specific overrides)
    print("\n3. Using mixed parameters (workflow + overrides):")
    print("   Workflow parameters with node-specific overrides")

    mixed_params = {
        # Workflow-level defaults
        "email": "admin@company.com",
        "password": "AdminPass123!",
        "role": "admin",
        "department": "it",
        # Node-specific override
        "email_sender": {
            "department": "executive"  # Override department for email template
        },
    }

    results3, run_id3 = await runtime.execute_async(workflow, parameters=mixed_params)

    print(f"\n   ✓ User created with role: {mixed_params['role']}")
    print(
        f"   ✓ Email sent with template: welcome_{mixed_params['email_sender']['department']}"
    )

    print("\n=== Benefits of Parameter Injection ===")
    print("• Simpler API - just pass parameters at workflow level")
    print("• Automatic routing - parameters find their way to the right nodes")
    print("• Backward compatible - existing node-specific params still work")
    print("• Flexible - mix workflow and node-specific parameters as needed")
    print("• Smart mapping - uses metadata from add_workflow_inputs()")


if __name__ == "__main__":
    asyncio.run(main())
