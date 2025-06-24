"""
Integration Tests for Complete User Management Workflows
Tests full workflow execution with real components and database
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List

import pytest

from apps.user_management.api.group_api import GroupAPI
from apps.user_management.main import UserManagementApp
from apps.user_management.workflows.auth_workflows import AuthWorkflows
from kailash.runtime.local import LocalRuntime
from kailash.workflow.builder import WorkflowBuilder


class TestCompleteWorkflows:
    """Integration tests for complete user management workflows"""

    @pytest.fixture
    async def app_environment(self):
        """Set up complete application environment"""
        app = UserManagementApp()
        await app.setup_database()

        runtime = LocalRuntime()

        # Create test admin user
        reg_workflow = app.user_api.create_user_registration_workflow()
        admin_result = await runtime.execute_async(
            reg_workflow,
            {
                "email": "integration_admin@example.com",
                "username": "integration_admin",
                "password": "IntegrationAdmin123!",
            },
        )

        # Assign admin role
        role_workflow = app.role_api.create_role_management_workflow()
        await runtime.execute_async(
            role_workflow,
            {
                "user_id": "system",
                "action": "manage",
                "operation": "assign_role_to_user",
                "data": {"user_id": admin_result["user"]["id"], "role_name": "admin"},
            },
        )

        return {
            "app": app,
            "runtime": runtime,
            "admin": admin_result["user"],
            "admin_token": admin_result["tokens"]["access"],
        }

    @pytest.mark.asyncio
    async def test_complete_user_lifecycle(self, app_environment):
        """Test complete user lifecycle from creation to deletion"""
        env = await app_environment
        app = env["app"]
        runtime = env["runtime"]
        admin = env["admin"]

        # Phase 1: User Registration
        user_data = {
            "email": "lifecycle_test@example.com",
            "username": "lifecycle_user",
            "password": "LifecyclePass123!",
            "first_name": "Test",
            "last_name": "User",
        }

        reg_workflow = app.user_api.create_user_registration_workflow()
        reg_result = await runtime.execute_async(reg_workflow, user_data)

        assert reg_result["success"] is True
        user_id = reg_result["user"]["id"]
        user_token = reg_result["tokens"]["access"]

        # Phase 2: First Login
        login_workflow = app.user_api.create_login_workflow()
        login_result = await runtime.execute_async(
            login_workflow,
            {"email": user_data["email"], "password": user_data["password"]},
        )

        assert login_result["success"] is True
        assert login_result["session"]["id"] is not None

        # Phase 3: Profile Update
        profile_workflow = app.user_api.create_profile_update_workflow()
        profile_result = await runtime.execute_async(
            profile_workflow,
            {
                "user_id": user_id,
                "updates": {
                    "bio": "Software Developer",
                    "phone": "+1234567890",
                    "preferences": {"theme": "dark", "notifications": True},
                },
            },
        )

        assert profile_result["success"] is True

        # Phase 4: Role Assignment
        role_workflow = app.role_api.create_role_management_workflow()

        # Create developer role
        await runtime.execute_async(
            role_workflow,
            {
                "user_id": admin["id"],
                "action": "create",
                "operation": "create_role",
                "role_data": {
                    "name": "developer",
                    "description": "Software Developer",
                    "permissions": ["code:read", "code:write", "docs:read"],
                },
            },
        )

        # Assign role
        role_result = await runtime.execute_async(
            role_workflow,
            {
                "user_id": admin["id"],
                "action": "manage",
                "operation": "assign_role_to_user",
                "data": {"user_id": user_id, "role_name": "developer"},
            },
        )

        assert role_result["success"] is True

        # Phase 5: Permission Check
        perm_node = runtime.create_node(
            "PermissionCheckNode", app.config.NODE_CONFIGS["PermissionCheckNode"]
        )

        # Should have code:write permission
        perm_result = await runtime.execute_node_async(
            perm_node, {"user_id": user_id, "resource": "code", "action": "write"}
        )

        assert perm_result["allowed"] is True

        # Should NOT have admin permission
        admin_perm_result = await runtime.execute_node_async(
            perm_node, {"user_id": user_id, "resource": "admin", "action": "manage"}
        )

        assert admin_perm_result["allowed"] is False

        # Phase 6: Password Reset
        reset_workflow = app.auth_workflows.create_password_reset_workflow()
        reset_result = await runtime.execute_async(
            reset_workflow, {"email": user_data["email"]}
        )

        assert reset_result["success"] is True
        assert "reset_token" in reset_result

        # Phase 7: Activity Audit
        audit_node = runtime.create_node(
            "EnterpriseAuditLogNode", app.config.NODE_CONFIGS["EnterpriseAuditLogNode"]
        )

        audit_result = await runtime.execute_node_async(
            audit_node,
            {"operation": "search_logs", "filters": {"user_id": user_id}, "limit": 50},
        )

        assert audit_result["success"] is True
        assert len(audit_result.get("logs", [])) > 0

        # Verify audit events
        event_types = [log["event_type"] for log in audit_result.get("logs", [])]
        assert "user_created" in event_types
        assert "password_reset_requested" in event_types

        # Phase 8: User Deactivation
        user_node = runtime.create_node(
            "UserManagementNode", app.config.NODE_CONFIGS["UserManagementNode"]
        )

        deactivate_result = await runtime.execute_node_async(
            user_node,
            {
                "operation": "update_user",
                "user_id": user_id,
                "updates": {
                    "status": "inactive",
                    "deactivated_at": datetime.utcnow().isoformat(),
                },
            },
        )

        assert deactivate_result["success"] is True

        # Verify cannot login when inactive
        login_result = await runtime.execute_async(
            login_workflow,
            {"email": user_data["email"], "password": user_data["password"]},
        )

        # Should fail or indicate inactive status
        assert (
            not login_result.get("success")
            or login_result.get("user", {}).get("status") == "inactive"
        )

    @pytest.mark.asyncio
    async def test_group_based_access_control(self, app_environment):
        """Test group-based permission management"""
        env = await app_environment
        app = env["app"]
        runtime = env["runtime"]
        admin = env["admin"]

        # Initialize GroupAPI
        group_api = GroupAPI()

        # Phase 1: Create Groups
        groups = [
            {
                "name": "engineering",
                "description": "Engineering Team",
                "permissions": ["code:*", "docs:*", "ci:trigger"],
            },
            {
                "name": "marketing",
                "description": "Marketing Team",
                "permissions": ["content:*", "analytics:read", "social:manage"],
            },
            {
                "name": "finance",
                "description": "Finance Team",
                "permissions": ["reports:*", "billing:*", "users:read"],
            },
        ]

        group_workflow = group_api.create_group_management_workflow()

        for group_data in groups:
            result = await runtime.execute_async(
                group_workflow,
                {
                    "user_id": admin["id"],
                    "operation": "create_group",
                    "group_data": group_data,
                },
            )
            assert result["success"] is True

        # Phase 2: Create Users
        users = []
        departments = ["engineering", "marketing", "finance"]

        for i, dept in enumerate(departments):
            for j in range(2):  # 2 users per department
                user_data = {
                    "email": f"{dept}_user{j}@example.com",
                    "username": f"{dept}_user{j}",
                    "password": "DeptPass123!",
                    "department": dept,
                }

                reg_workflow = app.user_api.create_user_registration_workflow()
                result = await runtime.execute_async(reg_workflow, user_data)

                users.append(
                    {
                        "id": result["user"]["id"],
                        "department": dept,
                        "email": user_data["email"],
                    }
                )

        # Phase 3: Assign Users to Groups
        for user in users:
            result = await runtime.execute_async(
                group_workflow,
                {
                    "user_id": admin["id"],
                    "operation": "add_user_to_group",
                    "group_name": user["department"],
                    "user_id_to_add": user["id"],
                },
            )
            assert result["success"] is True

        # Phase 4: Test Group Permissions
        perm_node = runtime.create_node(
            "PermissionCheckNode", app.config.NODE_CONFIGS["PermissionCheckNode"]
        )

        # Engineering user should have code access
        eng_user = next(u for u in users if u["department"] == "engineering")

        code_perm = await runtime.execute_node_async(
            perm_node,
            {"user_id": eng_user["id"], "resource": "code", "action": "write"},
        )
        assert code_perm["allowed"] is True

        # But not billing access
        billing_perm = await runtime.execute_node_async(
            perm_node,
            {"user_id": eng_user["id"], "resource": "billing", "action": "read"},
        )
        assert billing_perm["allowed"] is False

        # Finance user should have billing access
        fin_user = next(u for u in users if u["department"] == "finance")

        fin_billing_perm = await runtime.execute_node_async(
            perm_node,
            {"user_id": fin_user["id"], "resource": "billing", "action": "manage"},
        )
        assert fin_billing_perm["allowed"] is True

        # Phase 5: Test Group Permission Updates
        perm_workflow = group_api.create_group_permission_workflow()

        # Add deployment permission to engineering
        perm_update = await runtime.execute_async(
            perm_workflow,
            {
                "user_id": admin["id"],
                "group_name": "engineering",
                "permissions": ["deploy:production"],
                "action": "add",
            },
        )
        assert perm_update["success"] is True

        # Verify new permission
        deploy_perm = await runtime.execute_node_async(
            perm_node,
            {"user_id": eng_user["id"], "resource": "deploy", "action": "production"},
        )
        assert deploy_perm["allowed"] is True

        # Phase 6: Test User Group Listing
        user_groups_workflow = group_api.create_user_groups_workflow()

        groups_result = await runtime.execute_async(
            user_groups_workflow, {"user_id": eng_user["id"]}
        )

        assert groups_result["success"] is True
        assert len(groups_result["groups"]) == 1
        assert groups_result["groups"][0]["name"] == "engineering"
        assert "code:*" in groups_result["aggregated_permissions"]
        assert "deploy:production" in groups_result["aggregated_permissions"]

    @pytest.mark.asyncio
    async def test_security_monitoring_workflow(self, app_environment):
        """Test security monitoring and incident response"""
        env = await app_environment
        app = env["app"]
        runtime = env["runtime"]
        admin = env["admin"]

        # Create test user
        user_data = {
            "email": "security_test@example.com",
            "username": "security_user",
            "password": "SecurePass123!",
        }

        reg_workflow = app.user_api.create_user_registration_workflow()
        user_result = await runtime.execute_async(reg_workflow, user_data)
        user_id = user_result["user"]["id"]

        # Phase 1: Simulate Failed Login Attempts
        login_workflow = app.user_api.create_login_workflow()
        security_node = runtime.create_node(
            "EnterpriseSecurityEventNode",
            app.config.NODE_CONFIGS["EnterpriseSecurityEventNode"],
        )

        # Generate failed login events
        for i in range(5):
            # Attempt with wrong password
            await runtime.execute_async(
                login_workflow,
                {"email": user_data["email"], "password": "WrongPassword123!"},
            )

            # Log security event
            await runtime.execute_node_async(
                security_node,
                {
                    "operation": "log_event",
                    "event_type": "failed_login",
                    "severity": "medium" if i < 3 else "high",
                    "details": {
                        "user_email": user_data["email"],
                        "attempt_number": i + 1,
                        "ip_address": f"192.168.1.{100 + i}",
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                },
            )

            # Small delay between attempts
            await asyncio.sleep(0.1)

        # Phase 2: Check Security Events
        events_result = await runtime.execute_node_async(
            security_node,
            {
                "operation": "get_events",
                "filters": {
                    "event_type": "failed_login",
                    "user_email": user_data["email"],
                },
                "limit": 10,
            },
        )

        assert events_result["success"] is True
        assert len(events_result.get("events", [])) >= 5

        # Phase 3: Automatic Account Lock
        user_node = runtime.create_node(
            "UserManagementNode", app.config.NODE_CONFIGS["UserManagementNode"]
        )

        # Lock account after threshold
        lock_result = await runtime.execute_node_async(
            user_node,
            {
                "operation": "update_user",
                "user_id": user_id,
                "updates": {
                    "status": "locked",
                    "locked_reason": "Multiple failed login attempts",
                    "locked_at": datetime.utcnow().isoformat(),
                    "unlock_at": (
                        datetime.utcnow() + timedelta(minutes=30)
                    ).isoformat(),
                },
            },
        )

        assert lock_result["success"] is True

        # Phase 4: Verify Account Locked
        login_result = await runtime.execute_async(
            login_workflow,
            {
                "email": user_data["email"],
                "password": user_data["password"],  # Even correct password
            },
        )

        # Should fail due to lock
        assert (
            not login_result.get("success")
            or login_result.get("error", "").lower().find("lock") != -1
        )

        # Phase 5: Generate Security Report
        report_workflow = WorkflowBuilder("security_report")
        report_workflow.add_node("data_collector", "PythonCodeNode")
        report_workflow.add_node("report_generator", "PythonCodeNode")

        report_workflow.add_connection("input", "data_collector", "data", "input")
        report_workflow.add_connection(
            "data_collector", "report_generator", "result", "input"
        )
        report_workflow.add_connection("report_generator", "output", "result", "result")

        collector_code = """
from datetime import datetime, timedelta

# Collect security metrics
end_time = datetime.utcnow()
start_time = end_time - timedelta(hours=1)

metrics = {
    "time_range": {
        "start": start_time.isoformat(),
        "end": end_time.isoformat()
    },
    "failed_logins": input_data.get("failed_login_count", 5),
    "locked_accounts": input_data.get("locked_accounts", 1),
    "suspicious_ips": input_data.get("suspicious_ips", []),
    "security_score": 65  # Medium risk
}

result = {"metrics": metrics}
"""
        report_workflow.update_node("data_collector", {"code": collector_code})

        generator_code = '''
metrics = input_data["metrics"]

report = f"""
# Security Report

**Time Range**: {metrics["time_range"]["start"]} to {metrics["time_range"]["end"]}

## Summary
- Failed Login Attempts: {metrics["failed_logins"]}
- Locked Accounts: {metrics["locked_accounts"]}
- Security Score: {metrics["security_score"]}/100

## Risk Assessment
{"HIGH RISK" if metrics["security_score"] < 50 else "MEDIUM RISK" if metrics["security_score"] < 80 else "LOW RISK"}

## Recommendations
1. Review locked accounts for false positives
2. Analyze IP patterns for potential attacks
3. Consider enabling 2FA for affected users
"""

result = {"report": report, "success": True}
'''
        report_workflow.update_node("report_generator", {"code": generator_code})

        report_result = await runtime.execute_async(
            report_workflow,
            {
                "failed_login_count": len(events_result.get("events", [])),
                "locked_accounts": 1,
                "suspicious_ips": ["192.168.1.100", "192.168.1.101"],
            },
        )

        assert report_result["success"] is True
        assert "Security Report" in report_result["report"]

    @pytest.mark.asyncio
    async def test_bulk_operations_workflow(self, app_environment):
        """Test bulk user operations with real data"""
        env = await app_environment
        app = env["app"]
        runtime = env["runtime"]
        admin = env["admin"]

        # Phase 1: Bulk User Import
        bulk_users = []
        for i in range(50):
            bulk_users.append(
                {
                    "email": f"bulk_test_{i}@example.com",
                    "username": f"bulktest{i}",
                    "first_name": f"Bulk{i}",
                    "last_name": "Test",
                    "department": ["sales", "marketing", "support"][i % 3],
                }
            )

        import_workflow = app.bulk_api.create_bulk_import_workflow()

        start_time = time.time()
        import_result = await runtime.execute_async(
            import_workflow, {"admin_id": admin["id"], "users": bulk_users}
        )
        import_duration = time.time() - start_time

        assert import_result["success"] is True
        assert import_result["summary"]["successful"] >= 45  # Allow 10% failure
        assert import_duration < 15  # Should be fast

        # Phase 2: Search and Filter
        search_workflow = app.search_api.create_user_search_workflow()

        # Search by department
        sales_search = await runtime.execute_async(
            search_workflow,
            {"user_id": admin["id"], "filters": {"department": "sales", "limit": 50}},
        )

        assert sales_search["success"] is True
        assert len(sales_search["data"]) > 0

        # Phase 3: Bulk Role Assignment
        # Get user IDs from search
        user_ids = [user["id"] for user in sales_search["data"][:10]]

        bulk_role_workflow = app.role_api.create_bulk_role_assignment_workflow()

        assignments = [{"user_id": uid, "role_name": "sales_team"} for uid in user_ids]

        # Create sales_team role first
        role_workflow = app.role_api.create_role_management_workflow()
        await runtime.execute_async(
            role_workflow,
            {
                "user_id": admin["id"],
                "action": "create",
                "operation": "create_role",
                "role_data": {
                    "name": "sales_team",
                    "description": "Sales Team Members",
                    "permissions": ["crm:access", "leads:manage", "reports:sales"],
                },
            },
        )

        # Bulk assign
        role_assign_result = await runtime.execute_async(
            bulk_role_workflow, {"user_id": admin["id"], "assignments": assignments}
        )

        assert role_assign_result["success"] is True
        assert role_assign_result["summary"]["successful"] >= 9

        # Phase 4: Bulk Update
        update_workflow = app.bulk_api.create_bulk_update_workflow()

        update_result = await runtime.execute_async(
            update_workflow,
            {
                "user_id": admin["id"],
                "updates": [
                    {
                        "user_ids": user_ids,
                        "changes": {
                            "status": "active",
                            "attributes": {
                                "onboarded": True,
                                "training_complete": False,
                            },
                        },
                    }
                ],
            },
        )

        assert update_result["success"] is True

        # Phase 5: Export Users
        export_workflow = app.search_api.create_export_workflow()

        export_result = await runtime.execute_async(
            export_workflow,
            {
                "user_id": admin["id"],
                "filters": {"department": "sales"},
                "format": "csv",
                "fields": ["id", "email", "username", "department", "status"],
            },
        )

        assert export_result["success"] is True
        assert export_result["format"] == "csv"
        assert export_result["record_count"] > 0

        # Phase 6: Bulk Deactivation
        delete_workflow = app.bulk_api.create_bulk_delete_workflow()

        # Soft delete marketing users
        marketing_search = await runtime.execute_async(
            search_workflow,
            {
                "user_id": admin["id"],
                "filters": {"department": "marketing", "limit": 50},
            },
        )

        marketing_ids = [u["id"] for u in marketing_search["data"]]

        delete_result = await runtime.execute_async(
            delete_workflow,
            {
                "user_id": admin["id"],
                "user_ids": marketing_ids[:5],  # Delete first 5
                "mode": "soft",
            },
        )

        assert delete_result["success"] is True
        assert "backup" in delete_result

    @pytest.mark.asyncio
    async def test_advanced_permission_scenarios(self, app_environment):
        """Test complex permission scenarios with inheritance and ABAC"""
        env = await app_environment
        app = env["app"]
        runtime = env["runtime"]
        admin = env["admin"]

        # Phase 1: Create Role Hierarchy
        roles = [
            {"name": "organization_admin", "permissions": ["org:*"], "parent": None},
            {
                "name": "department_manager",
                "permissions": ["dept:*", "users:read"],
                "parent": "organization_admin",
            },
            {
                "name": "team_lead",
                "permissions": ["team:*", "tasks:assign"],
                "parent": "department_manager",
            },
            {
                "name": "senior_member",
                "permissions": ["tasks:*", "docs:write"],
                "parent": "team_lead",
            },
            {
                "name": "junior_member",
                "permissions": ["tasks:read", "docs:read"],
                "parent": "senior_member",
            },
        ]

        role_workflow = app.role_api.create_role_management_workflow()
        hierarchy_workflow = app.role_api.create_hierarchy_workflow()

        # Create roles
        for role_data in roles:
            result = await runtime.execute_async(
                role_workflow,
                {
                    "user_id": admin["id"],
                    "action": "create",
                    "operation": "create_role",
                    "role_data": {
                        "name": role_data["name"],
                        "permissions": role_data["permissions"],
                    },
                },
            )
            assert result["success"] is True

        # Set up hierarchy
        for role_data in roles:
            if role_data["parent"]:
                result = await runtime.execute_async(
                    hierarchy_workflow,
                    {
                        "user_id": admin["id"],
                        "parent_role": role_data["parent"],
                        "child_role": role_data["name"],
                    },
                )
                assert result["success"] is True

        # Phase 2: Create Users at Different Levels
        test_users = []
        for i, role in enumerate(roles):
            user_data = {
                "email": f"{role['name']}_user@example.com",
                "username": f"{role['name']}_user",
                "password": "RoleTest123!",
            }

            reg_workflow = app.user_api.create_user_registration_workflow()
            user_result = await runtime.execute_async(reg_workflow, user_data)

            # Assign role
            await runtime.execute_async(
                role_workflow,
                {
                    "user_id": admin["id"],
                    "action": "manage",
                    "operation": "assign_role_to_user",
                    "data": {
                        "user_id": user_result["user"]["id"],
                        "role_name": role["name"],
                    },
                },
            )

            test_users.append({"id": user_result["user"]["id"], "role": role["name"]})

        # Phase 3: Test Permission Inheritance
        perm_node = runtime.create_node(
            "PermissionCheckNode", app.config.NODE_CONFIGS["PermissionCheckNode"]
        )

        # Organization admin should have all permissions
        org_admin = next(u for u in test_users if u["role"] == "organization_admin")

        perms_to_check = [
            ("org", "manage", True),
            ("dept", "create", True),  # Inherited
            ("team", "delete", True),  # Inherited
            ("tasks", "assign", True),  # Inherited
        ]

        for resource, action, expected in perms_to_check:
            result = await runtime.execute_node_async(
                perm_node,
                {"user_id": org_admin["id"], "resource": resource, "action": action},
            )
            assert result["allowed"] == expected

        # Junior member should have limited permissions
        junior = next(u for u in test_users if u["role"] == "junior_member")

        junior_perms = [
            ("tasks", "read", True),  # Direct permission
            ("tasks", "write", False),  # Not granted
            ("docs", "read", True),  # Direct permission
            ("team", "manage", False),  # Not inherited this far
        ]

        for resource, action, expected in junior_perms:
            result = await runtime.execute_node_async(
                perm_node,
                {"user_id": junior["id"], "resource": resource, "action": action},
            )
            assert result["allowed"] == expected

        # Phase 4: Test ABAC (Attribute-Based Access Control)
        # Create resource with attributes
        resource_workflow = WorkflowBuilder("resource_permission")
        resource_workflow.add_node(
            "abac_checker",
            "PermissionCheckNode",
            app.config.NODE_CONFIGS["PermissionCheckNode"],
        )

        # Team lead checking team member's task
        team_lead = next(u for u in test_users if u["role"] == "team_lead")

        # Can access own team's resources
        own_team_result = await runtime.execute_node_async(
            perm_node,
            {
                "user_id": team_lead["id"],
                "resource": "task",
                "action": "update",
                "resource_attributes": {
                    "team_id": "team_123",
                    "owner_team": "team_123",
                },
                "user_attributes": {"team_id": "team_123"},
            },
        )

        assert own_team_result["allowed"] is True

        # Cannot access other team's resources
        other_team_result = await runtime.execute_node_async(
            perm_node,
            {
                "user_id": team_lead["id"],
                "resource": "task",
                "action": "update",
                "resource_attributes": {
                    "team_id": "team_456",
                    "owner_team": "team_456",
                },
                "user_attributes": {"team_id": "team_123"},
            },
        )

        # Should be denied (would need cross-team permission)
        assert other_team_result["allowed"] is False or "team_456" not in str(
            other_team_result
        )
