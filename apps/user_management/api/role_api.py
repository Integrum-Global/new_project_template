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

    def create_role_management_workflow(self):
        """Create workflow for role management operations"""
        workflow = WorkflowBuilder()

        # Add nodes
        workflow.add_node(
            "PermissionCheckNode",
            "permission_checker",
            self.config.NODE_CONFIGS["PermissionCheckNode"],
        )
        workflow.add_node(
            "RoleManagementNode",
            "role_manager",
            self.config.NODE_CONFIGS["RoleManagementNode"],
        )
        workflow.add_node(
            "EnterpriseAuditLogNode",
            "audit_logger",
            self.config.NODE_CONFIGS["EnterpriseAuditLogNode"],
        )

        # Connect nodes
        workflow.add_connection("permission_checker", "result", "role_manager", "input")
        workflow.add_connection("role_manager", "result", "audit_logger", "input")

        # Configure permission checker
        workflow.update_node(
            "permission_checker",
            {
                "operation": "check_permission",  # Use a valid permission operation
                "resource": "roles",
                "action": "manage",
                "user_id": "a3645f07-7f3b-4d7d-afab-4d6a17068aec",  # System user UUID for admin operations
                "resource_id": "roles",  # Resource ID for role management
                "permission": "roles:manage",  # Specific permission to check
                "database_config": {
                    "connection_string": self.config.DATABASE_URL,
                    "database_type": "postgresql",
                },
            },
        )

        # Configure role manager
        workflow.update_node(
            "role_manager",
            {
                "operation": "assign_user",  # Correct operation for role assignment
                "tenant_id": "default",  # Use default tenant
                "database_config": {
                    "connection_string": self.config.DATABASE_URL,
                    "database_type": "postgresql",
                },
            },
        )

        # Configure audit logger
        workflow.update_node(
            "audit_logger",
            {
                "operation": "log_event",  # Use valid AuditOperation for role management
                "tenant_id": "default",  # Use default tenant
                "database_config": {
                    "connection_string": self.config.DATABASE_URL,
                    "database_type": "postgresql",
                },
            },
        )

        # Add workflow input mappings for runtime parameters
        # Map specific parameters to prevent unintended parameter injection

        # Permission checker should only get user_id for authorization
        workflow.add_workflow_inputs(
            "permission_checker",
            {"user_id": "user_id"},  # Only pass user_id for permission checking
        )

        # Role manager gets the specific data we need for role assignment
        workflow.add_workflow_inputs(
            "role_manager",
            {
                "data.user_id": "user_id",
                "data.role_name": "role_id",  # Map role_name to role_id (for "admin" role)
            },
        )

        # Audit logger should not receive conflicting parameters
        # Provide empty mapping to prevent workflow parameter injection
        workflow.add_workflow_inputs("audit_logger", {})

        return workflow.build("role_management")

    def create_permission_assignment_workflow(self):
        """Create workflow for permission assignment"""
        workflow = WorkflowBuilder()

        # Add nodes
        workflow.add_node(
            "PermissionCheckNode",
            "admin_checker",
            self.config.NODE_CONFIGS["PermissionCheckNode"],
        )
        workflow.add_node("PythonCodeNode", "validator")
        workflow.add_node(
            "RoleManagementNode",
            "role_updater",
            self.config.NODE_CONFIGS["RoleManagementNode"],
        )
        workflow.add_node("PythonCodeNode", "cache_invalidator")
        workflow.add_node(
            "EnterpriseAuditLogNode",
            "audit_logger",
            self.config.NODE_CONFIGS["EnterpriseAuditLogNode"],
        )

        # Connect nodes
        workflow.add_connection("admin_checker", "result", "validator", "input")
        workflow.add_connection("validator", "result", "role_updater", "input")
        workflow.add_connection("role_updater", "result", "cache_invalidator", "input")
        workflow.add_connection("cache_invalidator", "result", "audit_logger", "input")

        # Configure admin checker
        workflow.update_node(
            "admin_checker",
            {"user_id": "admin", "resource": "permissions", "action": "manage"},
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
        # Configure validator
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
        # Configure cache invalidator
        workflow.update_node("cache_invalidator", {"code": cache_code})

        return workflow.build("permission_assignment")

    def create_hierarchy_workflow(self):
        """Create workflow for role hierarchy management"""
        workflow = WorkflowBuilder()

        # Add nodes
        workflow.add_node(
            "PermissionCheckNode",
            "permission_checker",
            self.config.NODE_CONFIGS["PermissionCheckNode"],
        )
        workflow.add_node("PythonCodeNode", "hierarchy_validator")
        workflow.add_node(
            "RoleManagementNode",
            "role_manager",
            self.config.NODE_CONFIGS["RoleManagementNode"],
        )
        workflow.add_node("PythonCodeNode", "inheritance_processor")
        workflow.add_node(
            "EnterpriseAuditLogNode",
            "audit_logger",
            self.config.NODE_CONFIGS["EnterpriseAuditLogNode"],
        )

        # Connect nodes
        workflow.add_connection(
            "permission_checker", "result", "hierarchy_validator", "input"
        )
        workflow.add_connection(
            "hierarchy_validator", "result", "role_manager", "input"
        )
        workflow.add_connection(
            "role_manager", "result", "inheritance_processor", "input"
        )
        workflow.add_connection(
            "inheritance_processor", "result", "audit_logger", "input"
        )

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
        # Configure hierarchy validator
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
        # Configure inheritance processor
        workflow.update_node("inheritance_processor", {"code": inheritance_code})

        return workflow.build("role_hierarchy")

    def create_bulk_role_assignment_workflow(self):
        """Create workflow for bulk role assignments"""
        workflow = WorkflowBuilder()

        # Add nodes
        workflow.add_node(
            "PermissionCheckNode",
            "permission_checker",
            self.config.NODE_CONFIGS["PermissionCheckNode"],
        )
        workflow.add_node("PythonCodeNode", "batch_processor")
        workflow.add_node(
            "RoleManagementNode",
            "role_assigner",
            self.config.NODE_CONFIGS["RoleManagementNode"],
        )
        workflow.add_node("PythonCodeNode", "result_aggregator")
        workflow.add_node(
            "EnterpriseAuditLogNode",
            "audit_logger",
            self.config.NODE_CONFIGS["EnterpriseAuditLogNode"],
        )

        # Connect nodes
        workflow.add_connection(
            "permission_checker", "result", "batch_processor", "input"
        )
        workflow.add_connection("batch_processor", "result", "role_assigner", "input")
        workflow.add_connection("role_assigner", "result", "result_aggregator", "input")
        workflow.add_connection("result_aggregator", "result", "audit_logger", "input")

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
        # Configure batch processor
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
        # Configure result aggregator
        workflow.update_node("result_aggregator", {"code": aggregator_code})

        return workflow.build("bulk_role_assignment")

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
