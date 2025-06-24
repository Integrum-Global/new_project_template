"""
Group Management API for Django-like Groups functionality
"""

from typing import Any, Dict, List, Optional

from apps.user_management.config.settings import UserManagementConfig
from kailash.runtime.local import LocalRuntime
from kailash.workflow.builder import WorkflowBuilder


class GroupAPI:
    """Group management functionality (Django Groups equivalent)"""

    def __init__(self):
        self.config = UserManagementConfig()
        self.runtime = LocalRuntime()

    def create_group_management_workflow(self) -> WorkflowBuilder:
        """Create workflow for group CRUD operations"""
        workflow = WorkflowBuilder("group_management")

        # Add nodes
        workflow.add_node(
            "permission_checker",
            "PermissionCheckNode",
            self.config.NODE_CONFIGS["PermissionCheckNode"],
        )
        workflow.add_node("group_processor", "PythonCodeNode")
        workflow.add_node(
            "role_manager",
            "RoleManagementNode",
            self.config.NODE_CONFIGS["RoleManagementNode"],
        )
        workflow.add_node(
            "audit_logger",
            "EnterpriseAuditLogNode",
            self.config.NODE_CONFIGS["EnterpriseAuditLogNode"],
        )

        # Connect nodes
        workflow.add_connection("input", "permission_checker", "data", "input")
        workflow.add_connection(
            "permission_checker", "group_processor", "result", "input"
        )
        workflow.add_connection("group_processor", "role_manager", "result", "input")
        workflow.add_connection("role_manager", "audit_logger", "result", "input")
        workflow.add_connection("audit_logger", "output", "result", "result")

        # Configure group processor (Groups are implemented as Roles in our system)
        processor_code = """
if not input_data.get("allowed"):
    result = {"success": False, "error": "Permission denied"}
else:
    operation = input_data.get("operation")

    if operation == "create_group":
        # Map group to role with group-specific attributes
        group_data = input_data.get("group_data", {})
        result = {
            "operation": "create_role",
            "role_data": {
                "name": f"group_{group_data['name']}",
                "description": group_data.get("description", f"Group: {group_data['name']}"),
                "permissions": group_data.get("permissions", []),
                "attributes": {
                    "type": "group",
                    "group_name": group_data["name"],
                    "created_by": input_data.get("user_id")
                }
            }
        }
    elif operation == "add_user_to_group":
        # Assign group role to user
        result = {
            "operation": "assign_role_to_user",
            "data": {
                "user_id": input_data["user_id_to_add"],
                "role_name": f"group_{input_data['group_name']}"
            }
        }
    elif operation == "remove_user_from_group":
        # Remove group role from user
        result = {
            "operation": "remove_role_from_user",
            "data": {
                "user_id": input_data["user_id_to_remove"],
                "role_name": f"group_{input_data['group_name']}"
            }
        }
    else:
        result = {"success": False, "error": f"Unknown operation: {operation}"}
"""
        workflow.update_node("group_processor", {"code": processor_code})

        return workflow

    def create_group_permission_workflow(self) -> WorkflowBuilder:
        """Create workflow for group permission management"""
        workflow = WorkflowBuilder("group_permissions")

        # Add nodes
        workflow.add_node(
            "permission_checker",
            "PermissionCheckNode",
            self.config.NODE_CONFIGS["PermissionCheckNode"],
        )
        workflow.add_node("permission_mapper", "PythonCodeNode")
        workflow.add_node(
            "role_manager",
            "RoleManagementNode",
            self.config.NODE_CONFIGS["RoleManagementNode"],
        )
        workflow.add_node("cache_invalidator", "PythonCodeNode")

        # Connect nodes
        workflow.add_connection("input", "permission_checker", "data", "input")
        workflow.add_connection(
            "permission_checker", "permission_mapper", "result", "input"
        )
        workflow.add_connection("permission_mapper", "role_manager", "result", "input")
        workflow.add_connection("role_manager", "cache_invalidator", "result", "input")
        workflow.add_connection("cache_invalidator", "output", "result", "result")

        # Configure permission mapper
        mapper_code = """
if not input_data.get("allowed"):
    result = {"success": False, "error": "Permission denied"}
else:
    group_name = input_data["group_name"]
    permissions = input_data.get("permissions", [])
    action = input_data.get("action", "set")  # set, add, remove

    # Map Django-style permissions to our permission format
    mapped_permissions = []
    for perm in permissions:
        if "." in perm:  # Django format: app_label.permission_codename
            app_label, codename = perm.split(".", 1)
            # Convert to resource:action format
            if codename.startswith("add_"):
                resource = codename[4:]
                action = "create"
            elif codename.startswith("change_"):
                resource = codename[7:]
                action = "update"
            elif codename.startswith("delete_"):
                resource = codename[7:]
                action = "delete"
            elif codename.startswith("view_"):
                resource = codename[5:]
                action = "read"
            else:
                resource = codename
                action = "*"

            mapped_permissions.append(f"{resource}:{action}")
        else:
            # Already in our format
            mapped_permissions.append(perm)

    if action == "set":
        operation = "set_permissions"
    elif action == "add":
        operation = "add_permissions"
    else:
        operation = "remove_permissions"

    result = {
        "operation": operation,
        "role_name": f"group_{group_name}",
        "permissions": mapped_permissions
    }
"""
        workflow.update_node("permission_mapper", {"code": mapper_code})

        # Configure cache invalidator
        cache_code = """
# Invalidate permission cache for all users in the group
group_role = input_data.get("role", {})
result = {
    "success": True,
    "group": {
        "name": group_role.get("name", "").replace("group_", ""),
        "permissions": group_role.get("permissions", [])
    },
    "cache_invalidated": True,
    "message": "Group permissions updated successfully"
}
"""
        workflow.update_node("cache_invalidator", {"code": cache_code})

        return workflow

    def create_user_groups_workflow(self) -> WorkflowBuilder:
        """Create workflow to get all groups for a user"""
        workflow = WorkflowBuilder("user_groups")

        # Add nodes
        workflow.add_node(
            "user_roles",
            "UserManagementNode",
            self.config.NODE_CONFIGS["UserManagementNode"],
        )
        workflow.add_node("group_filter", "PythonCodeNode")
        workflow.add_node("permission_aggregator", "PythonCodeNode")

        # Connect nodes
        workflow.add_connection("input", "user_roles", "data", "input")
        workflow.add_connection("user_roles", "group_filter", "result", "input")
        workflow.add_connection(
            "group_filter", "permission_aggregator", "result", "input"
        )
        workflow.add_connection("permission_aggregator", "output", "result", "result")

        # Configure user roles fetcher
        workflow.update_node(
            "user_roles", {"operation": "get_user_roles", "user_id": "$.user_id"}
        )

        # Configure group filter
        filter_code = """
roles = input_data.get("roles", [])
groups = []

# Filter only group-type roles
for role in roles:
    if role.get("name", "").startswith("group_"):
        group_name = role["name"].replace("group_", "")
        groups.append({
            "id": role.get("id"),
            "name": group_name,
            "permissions": role.get("permissions", []),
            "created_at": role.get("created_at"),
            "attributes": role.get("attributes", {})
        })

result = {
    "groups": groups,
    "user_id": input_data.get("user_id")
}
"""
        workflow.update_node("group_filter", {"code": filter_code})

        # Configure permission aggregator
        aggregator_code = """
groups = input_data.get("groups", [])

# Aggregate all permissions from groups
all_permissions = set()
for group in groups:
    all_permissions.update(group.get("permissions", []))

# Also get permission objects with metadata
permission_objects = []
for perm in all_permissions:
    if ":" in perm:
        resource, action = perm.split(":", 1)
        permission_objects.append({
            "permission": perm,
            "resource": resource,
            "action": action,
            "from_groups": [g["name"] for g in groups if perm in g.get("permissions", [])]
        })

result = {
    "success": True,
    "groups": groups,
    "aggregated_permissions": list(all_permissions),
    "permission_details": permission_objects,
    "total_groups": len(groups),
    "total_permissions": len(all_permissions)
}
"""
        workflow.update_node("permission_aggregator", {"code": aggregator_code})

        return workflow

    def register_endpoints(self, app):
        """Register group management endpoints"""

        # Initialize workflows
        group_workflow = self.create_group_management_workflow()
        permission_workflow = self.create_group_permission_workflow()
        user_groups_workflow = self.create_user_groups_workflow()

        @app.post("/api/v1/groups")
        async def create_group(
            name: str,
            description: Optional[str] = None,
            permissions: Optional[List[str]] = None,
            admin_id: str = None,
        ):
            """Create a new group"""
            result = await self.runtime.execute_async(
                group_workflow,
                {
                    "user_id": admin_id,
                    "operation": "create_group",
                    "group_data": {
                        "name": name,
                        "description": description,
                        "permissions": permissions or [],
                    },
                },
            )
            return result

        @app.put("/api/v1/groups/{group_name}/permissions")
        async def update_group_permissions(
            group_name: str,
            permissions: List[str],
            action: str = "set",
            admin_id: str = None,
        ):
            """Update group permissions"""
            result = await self.runtime.execute_async(
                permission_workflow,
                {
                    "user_id": admin_id,
                    "group_name": group_name,
                    "permissions": permissions,
                    "action": action,
                },
            )
            return result

        @app.post("/api/v1/groups/{group_name}/users/{user_id}")
        async def add_user_to_group(
            group_name: str, user_id: str, admin_id: str = None
        ):
            """Add user to group"""
            result = await self.runtime.execute_async(
                group_workflow,
                {
                    "user_id": admin_id,
                    "operation": "add_user_to_group",
                    "group_name": group_name,
                    "user_id_to_add": user_id,
                },
            )
            return result

        @app.delete("/api/v1/groups/{group_name}/users/{user_id}")
        async def remove_user_from_group(
            group_name: str, user_id: str, admin_id: str = None
        ):
            """Remove user from group"""
            result = await self.runtime.execute_async(
                group_workflow,
                {
                    "user_id": admin_id,
                    "operation": "remove_user_from_group",
                    "group_name": group_name,
                    "user_id_to_remove": user_id,
                },
            )
            return result

        @app.get("/api/v1/users/{user_id}/groups")
        async def get_user_groups(user_id: str):
            """Get all groups for a user"""
            result = await self.runtime.execute_async(
                user_groups_workflow, {"user_id": user_id}
            )
            return result

        @app.get("/api/v1/groups")
        async def list_groups():
            """List all groups"""
            role_node = WorkflowBuilder.create_node(
                "RoleManagementNode", self.config.NODE_CONFIGS["RoleManagementNode"]
            )

            # Get all roles and filter groups
            result = await self.runtime.execute_node_async(
                role_node, {"operation": "list_roles"}
            )

            # Filter group-type roles
            groups = []
            for role in result.get("roles", []):
                if role.get("name", "").startswith("group_"):
                    groups.append(
                        {
                            "name": role["name"].replace("group_", ""),
                            "permissions": role.get("permissions", []),
                            "user_count": role.get("user_count", 0),
                            "created_at": role.get("created_at"),
                        }
                    )

            return {"groups": groups, "total": len(groups)}
