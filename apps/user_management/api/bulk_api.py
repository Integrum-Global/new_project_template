"""
Bulk Operations API for User Management using Kailash SDK
"""

import asyncio
from typing import Any, Dict, List, Optional

from apps.user_management.config.settings import UserManagementConfig
from kailash.runtime.local import LocalRuntime
from kailash.workflow.builder import WorkflowBuilder


class BulkAPI:
    """Bulk operations for user management"""

    def __init__(self):
        self.config = UserManagementConfig()
        self.runtime = LocalRuntime()

    def create_bulk_import_workflow(self) -> WorkflowBuilder:
        """Create workflow for bulk user import"""
        workflow = WorkflowBuilder("bulk_user_import")

        # Add nodes
        workflow.add_node(
            "permission_checker",
            "PermissionCheckNode",
            self.config.NODE_CONFIGS["PermissionCheckNode"],
        )
        workflow.add_node("data_validator", "PythonCodeNode")
        workflow.add_node("duplicate_checker", "PythonCodeNode")
        workflow.add_node("batch_processor", "PythonCodeNode")
        workflow.add_node(
            "user_creator",
            "UserManagementNode",
            self.config.NODE_CONFIGS["UserManagementNode"],
        )
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
            "permission_checker", "data_validator", "result", "input"
        )
        workflow.add_connection(
            "data_validator", "duplicate_checker", "result", "input"
        )
        workflow.add_connection(
            "duplicate_checker", "batch_processor", "result", "input"
        )
        workflow.add_connection("batch_processor", "user_creator", "batch", "input")
        workflow.add_connection("user_creator", "role_assigner", "result", "input")
        workflow.add_connection("role_assigner", "result_aggregator", "result", "input")
        workflow.add_connection("result_aggregator", "audit_logger", "result", "input")
        workflow.add_connection("audit_logger", "output", "result", "result")

        # Configure permission checker
        workflow.update_node(
            "permission_checker",
            {"user_id": "$.admin_id", "resource": "users", "action": "bulk_create"},
        )

        # Configure data validator
        validator_code = """
import re
import bcrypt

if not input_data.get("allowed"):
    result = {"success": False, "error": "Permission denied"}
else:
    users_data = input_data.get("users", [])
    validated_users = []
    validation_errors = []

    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    for idx, user in enumerate(users_data):
        errors = []

        # Validate required fields
        if not user.get("email"):
            errors.append("Email is required")
        elif not re.match(email_pattern, user["email"]):
            errors.append("Invalid email format")

        if not user.get("username"):
            errors.append("Username is required")
        elif len(user["username"]) < 3:
            errors.append("Username must be at least 3 characters")

        # Generate password if not provided
        if not user.get("password"):
            # Generate secure random password
            import secrets
            import string
            alphabet = string.ascii_letters + string.digits + string.punctuation
            user["password"] = ''.join(secrets.choice(alphabet) for i in range(12))
            user["password_generated"] = True

        # Hash password
        if not errors:
            password = user["password"].encode('utf-8')
            salt = bcrypt.gensalt()
            user["password_hash"] = bcrypt.hashpw(password, salt).decode('utf-8')

            # Store original password temporarily for email notification
            user["temp_password"] = user["password"]
            del user["password"]

            validated_users.append(user)
        else:
            validation_errors.append({
                "index": idx,
                "email": user.get("email"),
                "errors": errors
            })

    result = {
        "success": True,
        "validated_users": validated_users,
        "validation_errors": validation_errors,
        "total": len(users_data),
        "valid": len(validated_users),
        "invalid": len(validation_errors)
    }
"""
        workflow.update_node("data_validator", {"code": validator_code})

        # Configure duplicate checker
        duplicate_code = """
validated_users = input_data["validated_users"]
unique_users = []
duplicates = []

# Check for duplicates within the batch
email_set = set()
username_set = set()

for user in validated_users:
    email = user["email"].lower()
    username = user["username"].lower()

    if email in email_set or username in username_set:
        duplicates.append({
            "email": user["email"],
            "username": user["username"],
            "reason": "Duplicate in batch"
        })
    else:
        email_set.add(email)
        username_set.add(username)
        unique_users.append(user)

# TODO: Check against existing users in database
# This would be done by the UserManagementNode

result = {
    "unique_users": unique_users,
    "duplicates": duplicates,
    "stats": {
        "total_validated": len(validated_users),
        "unique": len(unique_users),
        "duplicates": len(duplicates)
    }
}
"""
        workflow.update_node("duplicate_checker", {"code": duplicate_code})

        # Configure batch processor
        batch_code = """
unique_users = input_data["unique_users"]
batch_size = 100  # Process in batches of 100

batches = []
for i in range(0, len(unique_users), batch_size):
    batch = unique_users[i:i + batch_size]
    batches.append({
        "operation": "bulk_create",
        "users": batch
    })

result = {"batches": batches, "total_batches": len(batches)}
"""
        workflow.update_node("batch_processor", {"code": batch_code})

        # Configure result aggregator
        aggregator_code = """
import_results = input_data.get("results", [])
role_results = input_data.get("role_assignments", [])

# Aggregate results
successful_users = []
failed_users = []
users_with_roles = []

for result in import_results:
    if result.get("success"):
        successful_users.extend(result.get("created_users", []))
    else:
        failed_users.extend(result.get("failed_users", []))

# Process role assignment results
for role_result in role_results:
    if role_result.get("success"):
        users_with_roles.extend(role_result.get("users", []))

# Prepare notification data for users with generated passwords
notifications = []
for user in successful_users:
    if user.get("password_generated"):
        notifications.append({
            "email": user["email"],
            "username": user["username"],
            "temp_password": user.get("temp_password")
        })

result = {
    "success": True,
    "summary": {
        "total_processed": len(successful_users) + len(failed_users),
        "successful": len(successful_users),
        "failed": len(failed_users),
        "roles_assigned": len(users_with_roles)
    },
    "successful_users": successful_users,
    "failed_users": failed_users,
    "notifications_required": notifications
}
"""
        workflow.update_node("result_aggregator", {"code": aggregator_code})

        return workflow

    def create_bulk_update_workflow(self) -> WorkflowBuilder:
        """Create workflow for bulk user updates"""
        workflow = WorkflowBuilder("bulk_user_update")

        # Add nodes
        workflow.add_node(
            "permission_checker",
            "PermissionCheckNode",
            self.config.NODE_CONFIGS["PermissionCheckNode"],
        )
        workflow.add_node("update_validator", "PythonCodeNode")
        workflow.add_node(
            "user_updater",
            "UserManagementNode",
            self.config.NODE_CONFIGS["UserManagementNode"],
        )
        workflow.add_node(
            "audit_logger",
            "EnterpriseAuditLogNode",
            self.config.NODE_CONFIGS["EnterpriseAuditLogNode"],
        )

        # Connect nodes
        workflow.add_connection("input", "permission_checker", "data", "input")
        workflow.add_connection(
            "permission_checker", "update_validator", "result", "input"
        )
        workflow.add_connection("update_validator", "user_updater", "result", "input")
        workflow.add_connection("user_updater", "audit_logger", "result", "input")
        workflow.add_connection("audit_logger", "output", "result", "result")

        # Configure update validator
        validator_code = """
if not input_data.get("allowed"):
    result = {"success": False, "error": "Permission denied"}
else:
    updates = input_data.get("updates", [])
    validated_updates = []

    # Allowed fields for bulk update
    allowed_fields = ["status", "department", "role", "attributes", "tags"]

    for update in updates:
        user_ids = update.get("user_ids", [])
        changes = update.get("changes", {})

        # Filter only allowed fields
        filtered_changes = {
            k: v for k, v in changes.items()
            if k in allowed_fields
        }

        if user_ids and filtered_changes:
            validated_updates.append({
                "user_ids": user_ids,
                "changes": filtered_changes
            })

    result = {
        "operation": "bulk_update",
        "updates": validated_updates
    }
"""
        workflow.update_node("update_validator", {"code": validator_code})

        return workflow

    def create_bulk_delete_workflow(self) -> WorkflowBuilder:
        """Create workflow for bulk user deletion"""
        workflow = WorkflowBuilder("bulk_user_delete")

        # Add nodes
        workflow.add_node(
            "permission_checker",
            "PermissionCheckNode",
            self.config.NODE_CONFIGS["PermissionCheckNode"],
        )
        workflow.add_node("deletion_validator", "PythonCodeNode")
        workflow.add_node("backup_creator", "PythonCodeNode")
        workflow.add_node(
            "user_deleter",
            "UserManagementNode",
            self.config.NODE_CONFIGS["UserManagementNode"],
        )
        workflow.add_node("cleanup_processor", "PythonCodeNode")
        workflow.add_node(
            "audit_logger",
            "EnterpriseAuditLogNode",
            self.config.NODE_CONFIGS["EnterpriseAuditLogNode"],
        )

        # Connect nodes
        workflow.add_connection("input", "permission_checker", "data", "input")
        workflow.add_connection(
            "permission_checker", "deletion_validator", "result", "input"
        )
        workflow.add_connection(
            "deletion_validator", "backup_creator", "result", "input"
        )
        workflow.add_connection("backup_creator", "user_deleter", "result", "input")
        workflow.add_connection("user_deleter", "cleanup_processor", "result", "input")
        workflow.add_connection("cleanup_processor", "audit_logger", "result", "input")
        workflow.add_connection("audit_logger", "output", "result", "result")

        # Configure deletion validator
        validator_code = """
if not input_data.get("allowed"):
    result = {"success": False, "error": "Permission denied"}
else:
    user_ids = input_data.get("user_ids", [])
    mode = input_data.get("mode", "soft")  # soft or hard delete

    # Validate deletion request
    if not user_ids:
        result = {"success": False, "error": "No users specified"}
    elif len(user_ids) > 1000:
        result = {"success": False, "error": "Cannot delete more than 1000 users at once"}
    else:
        # Check for system users that cannot be deleted
        protected_users = []  # Would check against system user list

        deletable_users = [uid for uid in user_ids if uid not in protected_users]

        result = {
            "success": True,
            "user_ids": deletable_users,
            "protected_users": protected_users,
            "mode": mode
        }
"""
        workflow.update_node("deletion_validator", {"code": validator_code})

        # Configure backup creator
        backup_code = """
import json
from datetime import datetime

# Create backup of user data before deletion
user_ids = input_data["user_ids"]
mode = input_data["mode"]

# In production, fetch user data from database
backup_data = {
    "timestamp": datetime.utcnow().isoformat(),
    "mode": mode,
    "user_count": len(user_ids),
    "user_ids": user_ids,
    "backup_location": f"/backups/users_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
}

# Prepare deletion operation
if mode == "soft":
    operation = {
        "operation": "bulk_update",
        "updates": [{
            "user_ids": user_ids,
            "changes": {
                "status": "deleted",
                "deleted_at": datetime.utcnow().isoformat()
            }
        }]
    }
else:
    operation = {
        "operation": "bulk_delete",
        "user_ids": user_ids
    }

result = {
    "backup": backup_data,
    **operation
}
"""
        workflow.update_node("backup_creator", {"code": backup_code})

        # Configure cleanup processor
        cleanup_code = """
# Clean up related data after user deletion
deletion_results = input_data.get("results", [])

cleanup_tasks = []
for result in deletion_results:
    if result.get("success"):
        deleted_users = result.get("deleted_users", [])
        for user in deleted_users:
            cleanup_tasks.extend([
                {"type": "sessions", "user_id": user["id"]},
                {"type": "tokens", "user_id": user["id"]},
                {"type": "permissions_cache", "user_id": user["id"]}
            ])

result = {
    "success": True,
    "deletion_summary": input_data,
    "cleanup_tasks": len(cleanup_tasks),
    "audit_data": {
        "event_type": "bulk_user_deletion",
        "severity": "high",
        "details": {
            "user_count": len(deletion_results),
            "mode": input_data.get("mode", "soft")
        }
    }
}
"""
        workflow.update_node("cleanup_processor", {"code": cleanup_code})

        return workflow

    def create_bulk_action_workflow(self) -> WorkflowBuilder:
        """Create generic workflow for bulk actions"""
        workflow = WorkflowBuilder("bulk_action")

        # Add nodes
        workflow.add_node(
            "permission_checker",
            "PermissionCheckNode",
            self.config.NODE_CONFIGS["PermissionCheckNode"],
        )
        workflow.add_node("action_router", "SwitchNode")
        workflow.add_node(
            "status_updater",
            "UserManagementNode",
            self.config.NODE_CONFIGS["UserManagementNode"],
        )
        workflow.add_node(
            "role_updater",
            "RoleManagementNode",
            self.config.NODE_CONFIGS["RoleManagementNode"],
        )
        workflow.add_node("password_resetter", "PythonCodeNode")
        workflow.add_node("result_collector", "MergeNode")
        workflow.add_node(
            "audit_logger",
            "EnterpriseAuditLogNode",
            self.config.NODE_CONFIGS["EnterpriseAuditLogNode"],
        )

        # Connect nodes
        workflow.add_connection("input", "permission_checker", "data", "input")
        workflow.add_connection(
            "permission_checker", "action_router", "result", "input"
        )
        workflow.add_connection("action_router", "status_updater", "activate", "input")
        workflow.add_connection(
            "action_router", "status_updater", "deactivate", "input"
        )
        workflow.add_connection("action_router", "role_updater", "assign_role", "input")
        workflow.add_connection(
            "action_router", "password_resetter", "reset_passwords", "input"
        )
        workflow.add_connection("status_updater", "result_collector", "result", "input")
        workflow.add_connection("role_updater", "result_collector", "result", "input")
        workflow.add_connection(
            "password_resetter", "result_collector", "result", "input"
        )
        workflow.add_connection("result_collector", "audit_logger", "result", "input")
        workflow.add_connection("audit_logger", "output", "result", "result")

        # Configure action router
        workflow.update_node(
            "action_router",
            {
                "condition_field": "$.action",
                "routes": {
                    "activate": "activate",
                    "deactivate": "deactivate",
                    "assign_role": "assign_role",
                    "reset_passwords": "reset_passwords",
                },
            },
        )

        # Configure password resetter
        resetter_code = """
import secrets
import string

user_ids = input_data.get("user_ids", [])
reset_results = []

for user_id in user_ids:
    # Generate new password
    alphabet = string.ascii_letters + string.digits + string.punctuation
    new_password = ''.join(secrets.choice(alphabet) for i in range(12))

    reset_results.append({
        "user_id": user_id,
        "new_password": new_password,
        "reset_required": True
    })

result = {
    "success": True,
    "action": "reset_passwords",
    "results": reset_results
}
"""
        workflow.update_node("password_resetter", {"code": resetter_code})

        return workflow

    def register_endpoints(self, app):
        """Register bulk operation endpoints"""

        # Initialize workflows
        import_workflow = self.create_bulk_import_workflow()
        update_workflow = self.create_bulk_update_workflow()
        delete_workflow = self.create_bulk_delete_workflow()
        action_workflow = self.create_bulk_action_workflow()

        @app.post("/api/v1/users/bulk/import")
        async def bulk_import_users(admin_id: str, users: List[Dict[str, Any]]):
            """Bulk import users"""
            result = await self.runtime.execute_async(
                import_workflow, {"admin_id": admin_id, "users": users}
            )
            return result

        @app.post("/api/v1/users/bulk/update")
        async def bulk_update_users(admin_id: str, updates: List[Dict[str, Any]]):
            """Bulk update users"""
            result = await self.runtime.execute_async(
                update_workflow, {"user_id": admin_id, "updates": updates}
            )
            return result

        @app.delete("/api/v1/users/bulk")
        async def bulk_delete_users(
            admin_id: str, user_ids: List[str], mode: str = "soft"
        ):
            """Bulk delete users"""
            result = await self.runtime.execute_async(
                delete_workflow,
                {"user_id": admin_id, "user_ids": user_ids, "mode": mode},
            )
            return result

        @app.post("/api/v1/users/bulk/action")
        async def bulk_action(
            admin_id: str,
            action: str,
            user_ids: List[str],
            params: Optional[Dict] = None,
        ):
            """Perform bulk action on users"""
            result = await self.runtime.execute_async(
                action_workflow,
                {
                    "user_id": admin_id,
                    "action": action,
                    "user_ids": user_ids,
                    **(params or {}),
                },
            )
            return result
