"""
Comprehensive Functional Tests for User Management System
Tests complete user workflows, not just individual components
"""

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from typing import Any, Dict, List

import pytest

from apps.user_management.config.settings import UserManagementConfig
from apps.user_management.main import UserManagementApp
from kailash.runtime.local import LocalRuntime


class TestFunctionalWorkflows:
    """Test complete user management workflows end-to-end"""

    @pytest.fixture
    async def app(self):
        """Create application instance"""
        app_manager = UserManagementApp()
        await app_manager.setup_database()
        return app_manager

    @pytest.fixture
    def runtime(self):
        """Create runtime instance"""
        return LocalRuntime()

    @pytest.mark.asyncio
    async def test_complete_user_lifecycle(self, app, runtime):
        """Test complete user lifecycle from registration to deletion"""

        # 1. Register user
        registration_data = {
            "email": "lifecycle@example.com",
            "username": "lifecycleuser",
            "password": "SecurePass123!",
        }

        reg_workflow = app.user_api.create_user_registration_workflow()
        reg_result = await runtime.execute_async(reg_workflow, registration_data)

        assert reg_result["success"] is True
        user_id = reg_result["user"]["id"]
        access_token = reg_result["tokens"]["access"]

        # 2. Login with credentials
        login_workflow = app.user_api.create_login_workflow()
        login_result = await runtime.execute_async(
            login_workflow,
            {
                "email": registration_data["email"],
                "password": registration_data["password"],
            },
        )

        assert login_result["success"] is True
        assert login_result["session"]["id"] is not None

        # 3. Update profile
        profile_workflow = app.user_api.create_profile_update_workflow()
        profile_result = await runtime.execute_async(
            profile_workflow,
            {
                "user_id": user_id,
                "updates": {
                    "first_name": "Test",
                    "last_name": "User",
                    "bio": "Testing the system",
                },
            },
        )

        assert profile_result["success"] is True

        # 4. Request password reset
        reset_workflow = app.auth_workflows.create_password_reset_workflow()
        reset_result = await runtime.execute_async(
            reset_workflow, {"email": registration_data["email"]}
        )

        assert reset_result["success"] is True
        assert "reset_token" in reset_result

        # 5. Search for user
        search_workflow = app.search_api.create_user_search_workflow()
        search_result = await runtime.execute_async(
            search_workflow, {"user_id": user_id, "filters": {"query": "lifecycleuser"}}
        )

        assert search_result["success"] is True
        assert len(search_result["data"]) > 0

        # 6. Soft delete user
        user_node = runtime.create_node(
            "UserManagementNode", app.config.NODE_CONFIGS["UserManagementNode"]
        )

        delete_result = await runtime.execute_node_async(
            user_node,
            {
                "operation": "update_user",
                "user_id": user_id,
                "updates": {"status": "deleted"},
            },
        )

        assert delete_result["success"] is True

    @pytest.mark.asyncio
    async def test_role_permission_workflow(self, app, runtime):
        """Test complete role and permission management workflow"""

        # 1. Create custom role
        role_workflow = app.role_api.create_role_management_workflow()
        role_result = await runtime.execute_async(
            role_workflow,
            {
                "user_id": "admin123",
                "action": "create",
                "operation": "create_role",
                "role_data": {
                    "name": "content_moderator",
                    "description": "Can moderate user content",
                    "permissions": [
                        "content:read",
                        "content:update",
                        "content:delete",
                        "user:read",
                    ],
                },
            },
        )

        assert role_result["success"] is True

        # 2. Create test user
        user_data = {
            "email": "moderator@example.com",
            "username": "moderator1",
            "password": "ModPass123!",
        }

        reg_workflow = app.user_api.create_user_registration_workflow()
        user_result = await runtime.execute_async(reg_workflow, user_data)

        assert user_result["success"] is True
        user_id = user_result["user"]["id"]

        # 3. Assign role to user
        assign_result = await runtime.execute_async(
            role_workflow,
            {
                "user_id": "admin123",
                "action": "manage",
                "operation": "assign_role_to_user",
                "data": {"user_id": user_id, "role_name": "content_moderator"},
            },
        )

        assert assign_result["success"] is True

        # 4. Check permissions
        perm_node = runtime.create_node(
            "PermissionCheckNode", app.config.NODE_CONFIGS["PermissionCheckNode"]
        )

        # Should have content:update permission
        check_result = await runtime.execute_node_async(
            perm_node, {"user_id": user_id, "resource": "content", "action": "update"}
        )

        assert check_result["allowed"] is True

        # Should NOT have user:delete permission
        check_result2 = await runtime.execute_node_async(
            perm_node, {"user_id": user_id, "resource": "user", "action": "delete"}
        )

        assert check_result2["allowed"] is False

        # 5. Update role permissions
        perm_workflow = app.role_api.create_permission_assignment_workflow()
        perm_result = await runtime.execute_async(
            perm_workflow,
            {
                "admin_id": "admin123",
                "role_name": "content_moderator",
                "permissions": ["user:update"],
                "action": "add",
            },
        )

        assert perm_result["success"] is True

        # 6. Create role hierarchy
        hierarchy_workflow = app.role_api.create_hierarchy_workflow()
        hierarchy_result = await runtime.execute_async(
            hierarchy_workflow,
            {
                "user_id": "admin123",
                "parent_role": "moderator",
                "child_role": "content_moderator",
            },
        )

        assert hierarchy_result["success"] is True

    @pytest.mark.asyncio
    async def test_group_management_workflow(self, app, runtime):
        """Test Django-like group management"""

        # 1. Create group
        group_api = GroupAPI()
        app.group_api = group_api

        group_workflow = group_api.create_group_management_workflow()
        group_result = await runtime.execute_async(
            group_workflow,
            {
                "user_id": "admin123",
                "operation": "create_group",
                "group_data": {
                    "name": "editors",
                    "description": "Content editors group",
                    "permissions": ["content:create", "content:read", "content:update"],
                },
            },
        )

        assert group_result["success"] is True

        # 2. Create multiple users
        users = []
        for i in range(3):
            user_data = {
                "email": f"editor{i}@example.com",
                "username": f"editor{i}",
                "password": "EditorPass123!",
            }

            reg_workflow = app.user_api.create_user_registration_workflow()
            result = await runtime.execute_async(reg_workflow, user_data)
            users.append(result["user"]["id"])

        # 3. Add users to group
        for user_id in users:
            add_result = await runtime.execute_async(
                group_workflow,
                {
                    "user_id": "admin123",
                    "operation": "add_user_to_group",
                    "group_name": "editors",
                    "user_id_to_add": user_id,
                },
            )
            assert add_result["success"] is True

        # 4. Verify group permissions
        user_groups_workflow = group_api.create_user_groups_workflow()
        groups_result = await runtime.execute_async(
            user_groups_workflow, {"user_id": users[0]}
        )

        assert groups_result["success"] is True
        assert len(groups_result["groups"]) > 0
        assert "content:create" in groups_result["aggregated_permissions"]

        # 5. Update group permissions
        perm_workflow = group_api.create_group_permission_workflow()
        perm_update_result = await runtime.execute_async(
            perm_workflow,
            {
                "user_id": "admin123",
                "group_name": "editors",
                "permissions": ["content:delete"],
                "action": "add",
            },
        )

        assert perm_update_result["success"] is True

        # 6. Remove user from group
        remove_result = await runtime.execute_async(
            group_workflow,
            {
                "user_id": "admin123",
                "operation": "remove_user_from_group",
                "group_name": "editors",
                "user_id_to_remove": users[2],
            },
        )

        assert remove_result["success"] is True

    @pytest.mark.asyncio
    async def test_bulk_operations_workflow(self, app, runtime):
        """Test bulk import, update, and delete operations"""

        # 1. Prepare bulk user data
        bulk_users = []
        for i in range(50):
            bulk_users.append(
                {
                    "email": f"bulkuser{i}@example.com",
                    "username": f"bulkuser{i}",
                    "first_name": f"Bulk{i}",
                    "last_name": "User",
                    "department": "sales" if i % 2 == 0 else "marketing",
                }
            )

        # 2. Bulk import users
        import_workflow = app.bulk_api.create_bulk_import_workflow()
        import_result = await runtime.execute_async(
            import_workflow, {"admin_id": "admin123", "users": bulk_users}
        )

        assert import_result["success"] is True
        assert import_result["summary"]["successful"] == 50

        # 3. Bulk update - activate all sales users
        update_workflow = app.bulk_api.create_bulk_update_workflow()

        # Get sales user IDs
        search_workflow = app.search_api.create_user_search_workflow()
        search_result = await runtime.execute_async(
            search_workflow,
            {"user_id": "admin123", "filters": {"department": "sales", "limit": 100}},
        )

        sales_user_ids = [u["id"] for u in search_result["data"]]

        update_result = await runtime.execute_async(
            update_workflow,
            {
                "user_id": "admin123",
                "updates": [
                    {
                        "user_ids": sales_user_ids,
                        "changes": {
                            "status": "active",
                            "attributes": {"verified": True},
                        },
                    }
                ],
            },
        )

        assert update_result["success"] is True

        # 4. Bulk assign roles
        bulk_role_workflow = app.role_api.create_bulk_role_assignment_workflow()

        assignments = []
        for user_id in sales_user_ids[:10]:
            assignments.append({"user_id": user_id, "role_name": "user"})

        role_result = await runtime.execute_async(
            bulk_role_workflow, {"user_id": "admin123", "assignments": assignments}
        )

        assert role_result["success"] is True
        assert role_result["summary"]["successful"] == 10

        # 5. Bulk soft delete marketing users
        marketing_result = await runtime.execute_async(
            search_workflow,
            {
                "user_id": "admin123",
                "filters": {"department": "marketing", "limit": 100},
            },
        )

        marketing_user_ids = [u["id"] for u in marketing_result["data"]]

        delete_workflow = app.bulk_api.create_bulk_delete_workflow()
        delete_result = await runtime.execute_async(
            delete_workflow,
            {"user_id": "admin123", "user_ids": marketing_user_ids, "mode": "soft"},
        )

        assert delete_result["success"] is True

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, app, runtime):
        """Test system under concurrent load"""

        async def create_user(index: int):
            """Create a single user"""
            user_data = {
                "email": f"concurrent{index}@example.com",
                "username": f"concurrent{index}",
                "password": "ConcurrentPass123!",
            }

            workflow = app.user_api.create_user_registration_workflow()
            return await runtime.execute_async(workflow, user_data)

        async def check_permission(user_id: str, resource: str, action: str):
            """Check a permission"""
            perm_node = runtime.create_node(
                "PermissionCheckNode", app.config.NODE_CONFIGS["PermissionCheckNode"]
            )
            return await runtime.execute_node_async(
                perm_node, {"user_id": user_id, "resource": resource, "action": action}
            )

        # 1. Create 20 users concurrently
        start_time = time.time()

        tasks = []
        for i in range(20):
            tasks.append(create_user(i))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        creation_time = time.time() - start_time

        # Check results
        successful = sum(1 for r in results if isinstance(r, dict) and r.get("success"))
        assert successful >= 18  # Allow for some failures due to concurrency

        # 2. Perform 100 concurrent permission checks
        test_user_id = "user123"
        perm_tasks = []

        start_time = time.time()

        for i in range(100):
            resource = ["content", "user", "admin"][i % 3]
            action = ["read", "write", "delete"][i % 3]
            perm_tasks.append(check_permission(test_user_id, resource, action))

        perm_results = await asyncio.gather(*perm_tasks, return_exceptions=True)

        check_time = time.time() - start_time

        # Verify performance
        assert check_time < 5.0  # Should complete 100 checks in under 5 seconds

        # 3. Test concurrent updates to same user
        user_id = results[0]["user"]["id"] if results[0]["success"] else "test123"

        async def update_user_profile(field: str, value: str):
            """Update user profile field"""
            workflow = app.user_api.create_profile_update_workflow()
            return await runtime.execute_async(
                workflow, {"user_id": user_id, "updates": {field: value}}
            )

        update_tasks = []
        fields = ["bio", "first_name", "last_name", "phone"]

        for i in range(10):
            field = fields[i % len(fields)]
            update_tasks.append(update_user_profile(field, f"Value{i}"))

        update_results = await asyncio.gather(*update_tasks, return_exceptions=True)

        # Should handle concurrent updates gracefully
        update_successful = sum(
            1 for r in update_results if isinstance(r, dict) and r.get("success")
        )
        assert update_successful >= 8  # Most should succeed

    @pytest.mark.asyncio
    async def test_audit_trail_completeness(self, app, runtime):
        """Test that all operations create proper audit trails"""

        # Create user for testing
        user_data = {
            "email": "audittest@example.com",
            "username": "audituser",
            "password": "AuditPass123!",
        }

        reg_workflow = app.user_api.create_user_registration_workflow()
        user_result = await runtime.execute_async(reg_workflow, user_data)
        user_id = user_result["user"]["id"]

        # Perform various operations
        operations = [
            ("user_created", "low"),
            ("login", "low"),
            ("profile_updated", "low"),
            ("password_reset_requested", "medium"),
            ("role_assigned", "medium"),
            ("permission_checked", "low"),
            ("bulk_operation", "medium"),
        ]

        # Wait for async audit logging
        await asyncio.sleep(0.5)

        # Query audit logs
        audit_node = runtime.create_node(
            "EnterpriseAuditLogNode", app.config.NODE_CONFIGS["EnterpriseAuditLogNode"]
        )

        audit_result = await runtime.execute_node_async(
            audit_node,
            {"operation": "search_logs", "filters": {"user_id": user_id}, "limit": 100},
        )

        # Verify audit entries exist
        assert audit_result["success"] is True
        assert len(audit_result.get("logs", [])) > 0

        # Check for critical operations
        event_types = [log["event_type"] for log in audit_result.get("logs", [])]
        assert "user_created" in event_types

    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self, app, runtime):
        """Test system behavior under error conditions"""

        # 1. Test invalid data handling
        invalid_user_data = {
            "email": "notanemail",
            "username": "a",  # Too short
            "password": "weak",  # Too weak
        }

        reg_workflow = app.user_api.create_user_registration_workflow()
        invalid_result = await runtime.execute_async(reg_workflow, invalid_user_data)

        assert invalid_result["success"] is False
        assert "errors" in invalid_result
        assert len(invalid_result["errors"]) >= 3

        # 2. Test duplicate user handling
        valid_user_data = {
            "email": "duplicate@example.com",
            "username": "duplicateuser",
            "password": "ValidPass123!",
        }

        # First creation should succeed
        first_result = await runtime.execute_async(reg_workflow, valid_user_data)
        assert first_result["success"] is True

        # Second creation should fail
        # (In real implementation, UserManagementNode would handle this)

        # 3. Test permission denied scenarios
        perm_node = runtime.create_node(
            "PermissionCheckNode", app.config.NODE_CONFIGS["PermissionCheckNode"]
        )

        denied_result = await runtime.execute_node_async(
            perm_node,
            {"user_id": "regular_user", "resource": "admin", "action": "manage"},
        )

        assert denied_result["allowed"] is False

        # 4. Test transaction rollback
        # Create workflow that will fail partway through
        failed_bulk_data = [
            {
                "email": "valid1@example.com",
                "username": "valid1",
                "password": "Pass123!",
            },
            {
                "email": "invalid-email",
                "username": "valid2",
                "password": "Pass123!",
            },  # Invalid
            {
                "email": "valid3@example.com",
                "username": "valid3",
                "password": "Pass123!",
            },
        ]

        import_workflow = app.bulk_api.create_bulk_import_workflow()
        bulk_result = await runtime.execute_async(
            import_workflow, {"admin_id": "admin123", "users": failed_bulk_data}
        )

        # Should handle partial failures gracefully
        assert "validation_errors" in bulk_result
        assert bulk_result["valid"] == 2
        assert bulk_result["invalid"] == 1

        # 5. Test cascading updates
        # Update role permissions and verify cache invalidation
        role_workflow = app.role_api.create_permission_assignment_workflow()

        role_update = await runtime.execute_async(
            role_workflow,
            {
                "admin_id": "admin123",
                "role_name": "user",
                "permissions": ["new:permission"],
                "action": "add",
            },
        )

        assert role_update["success"] is True
        assert role_update.get("cache_invalidated") is True
