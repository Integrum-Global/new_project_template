"""
Simplified login workflow using parameter injection.

This example shows how parameter injection makes workflows more intuitive
by allowing direct parameter passing without complex node-specific nesting.
"""

from kailash.nodes.admin.permission_check import PermissionCheckNode
from kailash.nodes.admin.user_management import UserManagementNode
from kailash.nodes.code.python import PythonCodeNode
from kailash.runtime.local import LocalRuntime
from kailash.workflow.builder import WorkflowBuilder


def create_simplified_login_workflow(database_url: str) -> WorkflowBuilder:
    """Create a login workflow that uses parameter injection."""
    builder = WorkflowBuilder()

    # 1. User lookup node
    builder.add_node(
        UserManagementNode(
            operation="get_user",
            tenant_id="default",
            database_config={
                "connection_string": database_url,
                "database_type": "postgresql",
            },
        ),
        "user_lookup",
    )

    # 2. Password verification
    def verify_password(user: dict, password: str) -> dict:
        """Verify password (simplified for example)."""
        import bcrypt

        if not user:
            return {"authenticated": False, "error": "User not found"}

        # In real app, compare with hashed password
        # For demo, just check if password is provided
        if password and len(password) > 8:
            return {
                "authenticated": True,
                "user_id": user["user_id"],
                "username": user["username"],
            }

        return {"authenticated": False, "error": "Invalid password"}

    builder.add_node(PythonCodeNode.from_function(verify_password), "password_verifier")

    # 3. Permission check
    builder.add_node(
        PermissionCheckNode(
            tenant_id="default",
            database_config={
                "connection_string": database_url,
                "database_type": "postgresql",
            },
        ),
        "permission_checker",
    )

    # 4. Session creation
    def create_session(auth_result: dict, permissions: dict) -> dict:
        """Create user session."""
        if not auth_result.get("authenticated"):
            return {"session_created": False, "error": auth_result.get("error")}

        import uuid
        from datetime import datetime, timedelta

        session = {
            "session_id": str(uuid.uuid4()),
            "user_id": auth_result["user_id"],
            "username": auth_result["username"],
            "permissions": permissions.get("permissions", []),
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(hours=24)).isoformat(),
        }

        return {
            "session_created": True,
            "session": session,
            "message": f"Welcome back, {auth_result['username']}!",
        }

    builder.add_node(PythonCodeNode.from_function(create_session), "session_creator")

    # Connect nodes
    builder.connect("user_lookup", "password_verifier", {"result.user": "user"})

    builder.connect(
        "password_verifier", "permission_checker", {"result.user_id": "user_id"}
    )

    builder.connect("password_verifier", "session_creator", {"result": "auth_result"})

    builder.connect("permission_checker", "session_creator", {"result": "permissions"})

    # PARAMETER INJECTION CONFIGURATION
    # This is where the magic happens - we define how workflow parameters
    # map to individual node parameters

    # Username/email can be passed directly to user_lookup
    builder.add_workflow_inputs(
        "user_lookup",
        {
            "username": "username",  # If username provided, use it
            "email": "email",  # If email provided, use it
        },
    )

    # Password goes to the verifier
    builder.add_workflow_inputs("password_verifier", {"password": "password"})

    # Permission checker gets resource/action from workflow params
    builder.add_workflow_inputs(
        "permission_checker", {"resource": "resource", "action": "action"}
    )

    return builder.build("simplified_login")


def demonstrate_usage():
    """Show different ways to use the login workflow."""
    runtime = LocalRuntime()
    database_url = "postgresql://localhost/userdb"
    workflow = create_simplified_login_workflow(database_url)

    print("=== Simplified Login with Parameter Injection ===\n")

    # Example 1: Simple username/password login
    print("1. Basic login (workflow-level parameters):")
    print(
        """
    results = runtime.execute(workflow, parameters={
        "username": "john_doe",
        "password": "MySecurePass123",
        "resource": "dashboard",
        "action": "view"
    })
    """
    )

    # Example 2: Email-based login
    print("\n2. Email-based login:")
    print(
        """
    results = runtime.execute(workflow, parameters={
        "email": "john@example.com",
        "password": "MySecurePass123",
        "resource": "profile",
        "action": "edit"
    })
    """
    )

    # Example 3: With default permissions
    print("\n3. Login with default permissions:")
    print(
        """
    results = runtime.execute(workflow, parameters={
        "username": "admin",
        "password": "AdminPass123"
        # No resource/action specified - checker will use defaults
    })
    """
    )

    print("\n=== Comparison with Traditional Approach ===")

    print("\nTraditional (without parameter injection):")
    print(
        """
    results = runtime.execute(workflow, parameters={
        "user_lookup": {
            "username": "john_doe"
        },
        "password_verifier": {
            "password": "MySecurePass123"
        },
        "permission_checker": {
            "resource": "dashboard",
            "action": "view"
        }
    })
    """
    )

    print("\nWith parameter injection:")
    print(
        """
    results = runtime.execute(workflow, parameters={
        "username": "john_doe",
        "password": "MySecurePass123",
        "resource": "dashboard",
        "action": "view"
    })
    """
    )

    print("\n✓ 70% less code!")
    print("✓ More intuitive API")
    print("✓ Easier to understand")
    print("✓ Backward compatible")


if __name__ == "__main__":
    demonstrate_usage()
