"""
Direct Node Execution Patterns for User Management

This file demonstrates the working patterns for user management operations
using direct node execution instead of complex workflows. These patterns
have been proven to work reliably in production tests.

Key Benefits:
- No parameter passing issues
- Simpler code structure
- Better error handling
- Direct access to results
"""

from typing import Any, Dict, List, Optional

from kailash.nodes.admin.permission_check import PermissionCheckNode
from kailash.nodes.admin.role_management import RoleManagementNode
from kailash.nodes.admin.user_management import UserManagementNode


class UserManagementPatterns:
    """Best practices for user management operations"""

    def __init__(self, database_config: Dict[str, Any]):
        """
        Initialize with database configuration.

        Args:
            database_config: Dict with 'connection_string' and 'database_type'
        """
        self.db_config = database_config
        self.default_tenant = "default"

    def create_user(
        self,
        email: str,
        username: str,
        password: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create a new user using direct node execution.

        Returns:
            Dict with 'success' and 'user' keys
        """
        # Create node instance
        user_node = UserManagementNode(
            operation="create_user",
            tenant_id=self.default_tenant,
            database_config=self.db_config,
        )

        # Prepare user data
        user_data = {"email": email, "username": username, "status": "active"}

        if first_name:
            user_data["first_name"] = first_name
        if last_name:
            user_data["last_name"] = last_name
        if attributes:
            user_data["attributes"] = attributes

        # Execute node directly
        result = user_node.execute(user_data=user_data, password=password)

        # Format response
        if "result" in result and "user" in result["result"]:
            return {"success": True, "user": result["result"]["user"]}
        else:
            return {
                "success": False,
                "error": "User creation failed",
                "details": result,
            }

    def list_users(
        self, status: Optional[str] = "active", limit: int = 10, offset: int = 0
    ) -> Dict[str, Any]:
        """
        List users with pagination and filtering.

        Returns:
            Dict with users list and pagination info
        """
        user_node = UserManagementNode(
            operation="list_users",
            tenant_id=self.default_tenant,
            database_config=self.db_config,
        )

        result = user_node.execute(
            operation="list_users",
            tenant_id=self.default_tenant,
            database_config=self.db_config,
            status=status,
            limit=limit,
            offset=offset,
        )

        if "result" in result:
            return {
                "success": True,
                "users": result["result"]["users"],
                "pagination": result["result"]["pagination"],
            }
        else:
            return {
                "success": False,
                "error": "Failed to list users",
                "details": result,
            }

    def search_users(
        self, search_query: str, fields: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Search users by query across specified fields.

        Returns:
            Dict with matching users
        """
        if fields is None:
            fields = ["email", "username", "first_name", "last_name"]

        user_node = UserManagementNode(
            operation="search_users",
            tenant_id=self.default_tenant,
            database_config=self.db_config,
        )

        result = user_node.execute(
            operation="search_users",
            tenant_id=self.default_tenant,
            database_config=self.db_config,
            search_query=search_query,
            fields=fields,
        )

        if "result" in result:
            return {
                "success": True,
                "users": result["result"].get("users", []),
                "count": len(result["result"].get("users", [])),
            }
        else:
            return {"success": False, "error": "Search failed", "details": result}

    def update_user(self, user_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update user information.

        Returns:
            Dict with updated user info
        """
        user_node = UserManagementNode(
            operation="update_user",
            tenant_id=self.default_tenant,
            database_config=self.db_config,
        )

        result = user_node.execute(
            operation="update_user",
            tenant_id=self.default_tenant,
            database_config=self.db_config,
            user_id=user_id,
            user_data=updates,
        )

        if "result" in result and result["result"].get("success"):
            return {"success": True, "user": result["result"]["user"]}
        else:
            return {"success": False, "error": "Update failed", "details": result}

    def bulk_update_users(
        self, user_ids: List[str], updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update multiple users at once.

        Returns:
            Dict with update count and results
        """
        user_node = UserManagementNode(
            operation="bulk_update",
            tenant_id=self.default_tenant,
            database_config=self.db_config,
        )

        result = user_node.execute(
            operation="bulk_update",
            tenant_id=self.default_tenant,
            database_config=self.db_config,
            user_ids=user_ids,
            updates=updates,
        )

        if "result" in result:
            return {
                "success": True,
                "updated_count": result["result"].get("updated_count", 0),
                "results": result["result"],
            }
        else:
            return {"success": False, "error": "Bulk update failed", "details": result}


class RoleManagementPatterns:
    """Best practices for role management operations"""

    def __init__(self, database_config: Dict[str, Any]):
        """
        Initialize with database configuration.

        Args:
            database_config: Dict with 'connection_string' and 'database_type'
        """
        self.db_config = database_config
        self.default_tenant = "production_test"  # Or use a config value

    def create_role(
        self,
        name: str,
        description: str,
        permissions: List[str],
        role_type: str = "custom",
        parent_roles: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Create a new role with permissions.

        Returns:
            Dict with created role info
        """
        role_node = RoleManagementNode(
            operation="create_role",
            tenant_id=self.default_tenant,
            database_config=self.db_config,
        )

        role_data = {
            "name": name,
            "description": description,
            "permissions": permissions,
            "role_type": role_type,
            "is_active": True,
        }

        if parent_roles:
            role_data["parent_roles"] = parent_roles

        result = role_node.execute(
            operation="create_role",
            tenant_id=self.default_tenant,
            database_config=self.db_config,
            role_data=role_data,
        )

        if "result" in result and result["result"].get("success"):
            return {"success": True, "role": result["result"]["role"]}
        else:
            return {
                "success": False,
                "error": "Role creation failed",
                "details": result,
            }

    def assign_role_to_user(self, user_id: str, role_id: str) -> Dict[str, Any]:
        """
        Assign a role to a user.

        Returns:
            Dict with assignment status
        """
        role_node = RoleManagementNode(
            operation="assign_user",
            tenant_id=self.default_tenant,
            database_config=self.db_config,
        )

        result = role_node.execute(
            operation="assign_user",
            tenant_id=self.default_tenant,
            database_config=self.db_config,
            user_id=user_id,
            role_id=role_id,
        )

        if "result" in result and result["result"].get("success"):
            return {"success": True, "assignment": result["result"]["assignment"]}
        else:
            return {
                "success": False,
                "error": "Role assignment failed",
                "details": result,
            }

    def get_user_permissions(self, user_id: str) -> Dict[str, Any]:
        """
        Get all permissions for a user (including inherited from roles).

        Returns:
            Dict with user permissions
        """
        user_node = UserManagementNode(
            operation="get_user_permissions",
            tenant_id=self.default_tenant,
            database_config=self.db_config,
        )

        result = user_node.execute(
            operation="get_user_permissions",
            tenant_id=self.default_tenant,
            database_config=self.db_config,
            user_id=user_id,
        )

        if "result" in result:
            return {
                "success": True,
                "permissions": result["result"]["permissions"],
                "roles": result["result"].get("roles", []),
            }
        else:
            return {
                "success": False,
                "error": "Failed to get permissions",
                "details": result,
            }


# Example usage
if __name__ == "__main__":
    # Database configuration
    db_config = {
        "connection_string": "postgresql://admin:admin@localhost:5433/kailash_admin",
        "database_type": "postgresql",
    }

    # Initialize patterns
    user_mgmt = UserManagementPatterns(db_config)
    role_mgmt = RoleManagementPatterns(db_config)

    # Example 1: Create a user
    print("Creating user...")
    user_result = user_mgmt.create_user(
        email="john.doe@company.com",
        username="john_doe",
        password="SecurePassword123!",
        first_name="John",
        last_name="Doe",
        attributes={"department": "engineering", "employee_id": "EMP001"},
    )

    if user_result["success"]:
        user_id = user_result["user"]["user_id"]
        print(f"✓ Created user: {user_id}")

        # Example 2: Create a role
        print("\nCreating role...")
        role_result = role_mgmt.create_role(
            name="developer",
            description="Software developer role",
            permissions=["code:read", "code:write", "deploy:staging"],
        )

        if role_result["success"]:
            role_id = role_result["role"]["role_id"]
            print(f"✓ Created role: {role_id}")

            # Example 3: Assign role to user
            print("\nAssigning role to user...")
            assign_result = role_mgmt.assign_role_to_user(user_id, role_id)

            if assign_result["success"]:
                print("✓ Role assigned successfully")

                # Example 4: Check user permissions
                print("\nChecking user permissions...")
                perm_result = role_mgmt.get_user_permissions(user_id)

                if perm_result["success"]:
                    print(f"✓ User has {len(perm_result['permissions'])} permissions")
                    print(f"  Permissions: {', '.join(perm_result['permissions'])}")

    # Example 5: Search users
    print("\nSearching for users...")
    search_result = user_mgmt.search_users("john")

    if search_result["success"]:
        print(f"✓ Found {search_result['count']} users")

    # Example 6: List users with pagination
    print("\nListing active users...")
    list_result = user_mgmt.list_users(status="active", limit=5)

    if list_result["success"]:
        print(f"✓ Found {len(list_result['users'])} users")
        print(f"  Total count: {list_result['pagination']['total_count']}")
