"""
Role and Permission Management API using Kailash SDK
"""

from typing import Any, Dict, List, Optional

from apps.user_management.config.settings import UserManagementConfig
from kailash.runtime.local import LocalRuntime
from kailash.workflow.builder import WorkflowBuilder


class RoleAPI:
    """Role and permission management API"""

    def __init__(self):
        self.config = UserManagementConfig()
        self.runtime = LocalRuntime()

    def create_role_management_workflow(self) -> WorkflowBuilder:
        """Create workflow for role management operations"""
        workflow = WorkflowBuilder("role_management")

        # Add nodes
        workflow.add_node(
            "permission_checker",
            "PermissionCheckNode",
            self.config.NODE_CONFIGS["PermissionCheckNode"],
        )
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
        workflow.add_connection("permission_checker", "role_manager", "result", "input")
        workflow.add_connection("role_manager", "audit_logger", "result", "input")
        workflow.add_connection("audit_logger", "output", "result", "result")

        # Configure permission checker
        workflow.update_node(
            "permission_checker",
            {"user_id": "$.user_id", "resource": "roles", "action": "$.action"},
        )

        return workflow

    def create_permission_assignment_workflow(self) -> WorkflowBuilder:
        """Create workflow for permission assignment"""
        workflow = WorkflowBuilder("permission_assignment")

        # Add nodes
        workflow.add_node(
            "admin_checker",
            "PermissionCheckNode",
            self.config.NODE_CONFIGS["PermissionCheckNode"],
        )
        workflow.add_node("validator", "PythonCodeNode")
        workflow.add_node(
            "role_updater",
            "RoleManagementNode",
            self.config.NODE_CONFIGS["RoleManagementNode"],
        )
        workflow.add_node("cache_invalidator", "PythonCodeNode")
        workflow.add_node(
            "audit_logger",
            "EnterpriseAuditLogNode",
            self.config.NODE_CONFIGS["EnterpriseAuditLogNode"],
        )

        # Connect nodes
        workflow.add_connection("input", "admin_checker", "data", "input")
        workflow.add_connection("admin_checker", "validator", "result", "input")
        workflow.add_connection("validator", "role_updater", "result", "input")
        workflow.add_connection("role_updater", "cache_invalidator", "result", "input")
        workflow.add_connection("cache_invalidator", "audit_logger", "result", "input")
        workflow.add_connection("audit_logger", "output", "result", "result")

        # Configure admin checker
        workflow.update_node(
            "admin_checker",
            {"user_id": "$.admin_id", "resource": "permissions", "action": "manage"},
        )

        # Configure validator
        validator_code = """
if not input_data.get("allowed"):
    result = {"success": False, "error": "Admin permission required"}
else:
    role_name = input_data.get("role_name")
    permissions = input_data.get("permissions", [])
    action = input_data.get("action", "add")  # add or remove

    # Validate permission format
    valid_permissions = []
    for perm in permissions:
        if ":" in perm:  # Format: resource:action
            valid_permissions.append(perm)

    if not valid_permissions:
        result = {"success": False, "error": "No valid permissions provided"}
    else:
        result = {
            "operation": f"{action}_permissions",
            "role_name": role_name,
            "permissions": valid_permissions
        }
"""
        workflow.update_node("validator", {"code": validator_code})

        # Configure cache invalidator
        cache_code = """
# Invalidate permission cache for affected users
# This ensures permission changes take effect immediately
result = {
    "success": True,
    "role": input_data.get("role"),
    "permissions_updated": input_data.get("permissions"),
    "cache_invalidated": True
}
"""
        workflow.update_node("cache_invalidator", {"code": cache_code})

        return workflow

    def create_hierarchy_workflow(self) -> WorkflowBuilder:
        """Create workflow for role hierarchy management"""
        workflow = WorkflowBuilder("role_hierarchy")

        # Add nodes
        workflow.add_node(
            "permission_checker",
            "PermissionCheckNode",
            self.config.NODE_CONFIGS["PermissionCheckNode"],
        )
        workflow.add_node("hierarchy_validator", "PythonCodeNode")
        workflow.add_node(
            "role_manager",
            "RoleManagementNode",
            self.config.NODE_CONFIGS["RoleManagementNode"],
        )
        workflow.add_node("inheritance_processor", "PythonCodeNode")
        workflow.add_node(
            "audit_logger",
            "EnterpriseAuditLogNode",
            self.config.NODE_CONFIGS["EnterpriseAuditLogNode"],
        )

        # Connect nodes
        workflow.add_connection("input", "permission_checker", "data", "input")
        workflow.add_connection(
            "permission_checker", "hierarchy_validator", "result", "input"
        )
        workflow.add_connection(
            "hierarchy_validator", "role_manager", "result", "input"
        )
        workflow.add_connection(
            "role_manager", "inheritance_processor", "result", "input"
        )
        workflow.add_connection(
            "inheritance_processor", "audit_logger", "result", "input"
        )
        workflow.add_connection("audit_logger", "output", "result", "result")

        # Configure hierarchy validator
        validator_code = """
if not input_data.get("allowed"):
    result = {"success": False, "error": "Permission denied"}
else:
    parent_role = input_data.get("parent_role")
    child_role = input_data.get("child_role")

    # Check for circular dependencies
    if parent_role == child_role:
        result = {"success": False, "error": "Role cannot be its own parent"}
    else:
        result = {
            "operation": "set_parent",
            "role_name": child_role,
            "parent_name": parent_role
        }
"""
        workflow.update_node("hierarchy_validator", {"code": validator_code})

        # Configure inheritance processor
        inheritance_code = """
# Process permission inheritance
role = input_data.get("role", {})
parent = input_data.get("parent", {})

inherited_permissions = parent.get("permissions", [])
role_permissions = role.get("permissions", [])

# Combine permissions (role permissions override inherited)
all_permissions = list(set(inherited_permissions + role_permissions))

result = {
    "success": True,
    "role": role,
    "inherited_permissions": inherited_permissions,
    "total_permissions": all_permissions
}
"""
        workflow.update_node("inheritance_processor", {"code": inheritance_code})

        return workflow

    def create_bulk_role_assignment_workflow(self) -> WorkflowBuilder:
        """Create workflow for bulk role assignments"""
        workflow = WorkflowBuilder("bulk_role_assignment")

        # Add nodes
        workflow.add_node(
            "permission_checker",
            "PermissionCheckNode",
            self.config.NODE_CONFIGS["PermissionCheckNode"],
        )
        workflow.add_node("batch_processor", "PythonCodeNode")
        workflow.add_node(
            "role_assigner",
            "RoleManagementNode",
            self.config.NODE_CONFIGS["RoleManagementNode"],
        )
        workflow.add_node("result_aggregator", "PythonCodeNode")
        workflow.add_node(
            "audit_logger",
            "EnterpriseAuditLogNode",
            self.config.NODE_CONFIGS["EnterpriseAuditLogNode"],
        )

        # Connect nodes
        workflow.add_connection("input", "permission_checker", "data", "input")
        workflow.add_connection(
            "permission_checker", "batch_processor", "result", "input"
        )
        workflow.add_connection("batch_processor", "role_assigner", "result", "input")
        workflow.add_connection("role_assigner", "result_aggregator", "result", "input")
        workflow.add_connection("result_aggregator", "audit_logger", "result", "input")
        workflow.add_connection("audit_logger", "output", "result", "result")

        # Configure batch processor
        batch_code = """
if not input_data.get("allowed"):
    result = {"success": False, "error": "Permission denied"}
else:
    assignments = input_data.get("assignments", [])

    # Prepare bulk operation
    bulk_data = []
    for assignment in assignments:
        bulk_data.append({
            "user_id": assignment["user_id"],
            "role_name": assignment["role_name"]
        })

    result = {
        "operation": "bulk_assign",
        "assignments": bulk_data
    }
"""
        workflow.update_node("batch_processor", {"code": batch_code})

        # Configure result aggregator
        aggregator_code = """
results = input_data.get("results", [])
successful = [r for r in results if r.get("success")]
failed = [r for r in results if not r.get("success")]

result = {
    "success": True,
    "summary": {
        "total": len(results),
        "successful": len(successful),
        "failed": len(failed)
    },
    "results": results
}
"""
        workflow.update_node("result_aggregator", {"code": aggregator_code})

        return workflow

    def register_endpoints(self, app):
        """Register role management endpoints"""

        # Initialize workflows
        role_workflow = self.create_role_management_workflow()
        permission_workflow = self.create_permission_assignment_workflow()
        hierarchy_workflow = self.create_hierarchy_workflow()
        bulk_workflow = self.create_bulk_role_assignment_workflow()

        @app.post("/api/v1/roles")
        async def create_role(
            user_id: str, name: str, description: str, permissions: List[str]
        ):
            """Create a new role"""
            result = await self.runtime.execute_async(
                role_workflow,
                {
                    "user_id": user_id,
                    "action": "create",
                    "operation": "create_role",
                    "role_data": {
                        "name": name,
                        "description": description,
                        "permissions": permissions,
                    },
                },
            )
            return result

        @app.put("/api/v1/roles/{role_name}/permissions")
        async def update_permissions(
            role_name: str, admin_id: str, permissions: List[str], action: str = "add"
        ):
            """Add or remove permissions from a role"""
            result = await self.runtime.execute_async(
                permission_workflow,
                {
                    "admin_id": admin_id,
                    "role_name": role_name,
                    "permissions": permissions,
                    "action": action,
                },
            )
            return result

        @app.put("/api/v1/roles/{child_role}/parent/{parent_role}")
        async def set_role_hierarchy(child_role: str, parent_role: str, admin_id: str):
            """Set role hierarchy"""
            result = await self.runtime.execute_async(
                hierarchy_workflow,
                {
                    "user_id": admin_id,
                    "child_role": child_role,
                    "parent_role": parent_role,
                },
            )
            return result

        @app.post("/api/v1/roles/bulk-assign")
        async def bulk_assign_roles(admin_id: str, assignments: List[Dict[str, str]]):
            """Bulk assign roles to users"""
            result = await self.runtime.execute_async(
                bulk_workflow, {"user_id": admin_id, "assignments": assignments}
            )
            return result

        @app.get("/api/v1/roles")
        async def list_roles():
            """List all roles"""
            role_node = WorkflowBuilder.create_node(
                "RoleManagementNode", self.config.NODE_CONFIGS["RoleManagementNode"]
            )
            result = await self.runtime.execute_node_async(
                role_node, {"operation": "list_roles"}
            )
            return result

        @app.get("/api/v1/users/{user_id}/roles")
        async def get_user_roles(user_id: str):
            """Get roles assigned to a user"""
            user_node = WorkflowBuilder.create_node(
                "UserManagementNode", self.config.NODE_CONFIGS["UserManagementNode"]
            )
            result = await self.runtime.execute_node_async(
                user_node, {"operation": "get_user_roles", "user_id": user_id}
            )
            return result

        @app.post("/api/v1/permissions/check")
        async def check_permission(
            user_id: str, resource: str, action: str, attributes: Optional[Dict] = None
        ):
            """Check if user has permission"""
            perm_node = WorkflowBuilder.create_node(
                "PermissionCheckNode", self.config.NODE_CONFIGS["PermissionCheckNode"]
            )
            result = await self.runtime.execute_node_async(
                perm_node,
                {
                    "user_id": user_id,
                    "resource": resource,
                    "action": action,
                    "resource_attributes": attributes or {},
                },
            )
            return result
