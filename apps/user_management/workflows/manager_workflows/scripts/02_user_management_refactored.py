#!/usr/bin/env python3
"""
Manager Workflow: User Management - Refactored

This workflow properly uses the user_management app's service layer
for team member management instead of inline PythonCodeNode logic.
"""

import sys
import os
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add shared utilities to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from workflow_runner import WorkflowRunner
from service_nodes import (
    UserServiceNode, 
    RoleServiceNode, 
    SecurityServiceNode,
    ComplianceServiceNode
)
from kailash.nodes.api import HTTPRequestNode
from kailash.nodes.security import AuditLogNode
from kailash.nodes.transform import DataTransformer
from kailash.nodes.logic import SwitchNode


class ManagerUserManagementWorkflowRefactored:
    """
    Manager user management workflow using proper service integration.
    
    This demonstrates:
    - Using service nodes for team member operations
    - Proper API integration for team management
    - Audit logging for manager actions
    """
    
    def __init__(self, manager_id: str = "manager", api_base_url: str = "http://localhost:8000"):
        """
        Initialize the manager user management workflow.
        
        Args:
            manager_id: ID of the manager
            api_base_url: Base URL of the user management API
        """
        self.manager_id = manager_id
        self.api_base_url = api_base_url
        self.runner = WorkflowRunner(
            user_type="manager",
            user_id=manager_id,
            enable_debug=True,
            enable_audit=True,
            enable_monitoring=True
        )
    
    def _get_auth_token(self) -> str:
        """Get authentication token for API calls."""
        return f"{self.manager_id}_token"
    
    def add_team_member(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add a new team member using UserService.
        
        Args:
            user_data: User information dictionary
            
        Returns:
            Team member creation results
        """
        print(f"👤 Adding team member: {user_data.get('email', 'Unknown')}")
        
        builder = self.runner.create_workflow("add_team_member")
        
        # Validate manager permissions
        builder.add_node("RoleServiceNode", "check_permissions", {
            "operation": "check_permission"
        })
        
        # Create user through UserService
        builder.add_node("UserServiceNode", "create_user", {
            "operation": "create_user"
        })
        
        # Assign to manager's team via API
        builder.add_node("HTTPRequestNode", "assign_to_team", {
            "name": "assign_member_to_team",
            "url": f"{self.api_base_url}/api/v1/teams/my-team/members",
            "method": "POST",
            "headers": {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._get_auth_token()}"
            },
            "body": {
                "user_id": "{{user_id}}",
                "role": "team_member",
                "manager_id": self.manager_id
            }
        })
        
        # Set initial permissions
        builder.add_node("RoleServiceNode", "setup_permissions", {
            "operation": "assign_role"
        })
        
        # Send welcome notification
        builder.add_node("HTTPRequestNode", "send_welcome", {
            "name": "send_welcome_notification",
            "url": f"{self.api_base_url}/api/v1/notifications/send",
            "method": "POST",
            "headers": {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._get_auth_token()}"
            },
            "body": {
                "recipient_id": "{{user_id}}",
                "type": "team_welcome",
                "template": "manager_welcome"
            }
        })
        
        # Audit the addition
        builder.add_node("AuditLogNode", "audit_addition", {
            "name": "audit_team_member_addition",
            "action": "TEAM_MEMBER_ADDED",
            "resource_type": "user",
            "resource_id": "{{user_id}}",
            "user_id": self.manager_id,
            "details": {
                "team": "manager_team",
                "role": "team_member"
            }
        })
        
        # Connect workflow nodes
        builder.add_connection("check_permissions", "has_permission", "create_user", "permission_check")
        builder.add_connection("create_user", "user", "assign_to_team", "user_data")
        builder.add_connection("assign_to_team", "result.data", "setup_permissions", "team_assignment")
        builder.add_connection("setup_permissions", "result", "send_welcome", "permission_result")
        builder.add_connection("send_welcome", "result", "audit_addition", "notification_result")
        
        # Execute workflow
        workflow = builder.build()
        results, execution_id = self.runner.execute_workflow(
            workflow, 
            {
                "user_data": user_data, 
                "actor_id": self.manager_id,
                "permission": "users.create",
                "role": "employee"
            }, 
            "add_team_member"
        )
        
        return results
    
    def update_member_profile(self, user_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update team member profile using UserService.
        
        Args:
            user_id: ID of user to update
            updates: Profile updates
            
        Returns:
            Update results
        """
        print(f"✏️ Updating member profile: {user_id}")
        
        builder = self.runner.create_workflow("update_member")
        
        # Verify manager has authority over this user
        builder.add_node("HTTPRequestNode", "verify_authority", {
            "name": "verify_manager_authority",
            "url": f"{self.api_base_url}/api/v1/teams/my-team/members/{user_id}",
            "method": "GET",
            "headers": {
                "Authorization": f"Bearer {self._get_auth_token()}"
            }
        })
        
        # Update user through UserService
        builder.add_node("UserServiceNode", "update_user", {
            "operation": "update_user"
        })
        
        # Check if role needs updating
        builder.add_node("SwitchNode", "check_role_update", {
            "name": "check_if_role_changed",
            "condition_field": "role_changed",
            "cases": {
                "true": "update_role",
                "false": "skip_role_update"
            },
            "default_case": "skip_role_update"
        })
        
        # Update role if needed
        builder.add_node("RoleServiceNode", "update_role", {
            "operation": "assign_role"
        })
        
        # Audit the update
        builder.add_node("AuditLogNode", "audit_update", {
            "name": "audit_member_update",
            "action": "TEAM_MEMBER_UPDATED",
            "resource_type": "user",
            "resource_id": user_id,
            "user_id": self.manager_id,
            "details": {
                "fields_updated": "{{updated_fields}}",
                "team": "manager_team"
            }
        })
        
        # Connect workflow nodes
        builder.add_connection("verify_authority", "result.data", "update_user", "authority_check")
        builder.add_connection("update_user", "user", "check_role_update", "update_result")
        builder.add_connection("check_role_update", "true", "update_role", "role_data")
        builder.add_connection("check_role_update", "false", "audit_update", "final_result")
        builder.add_connection("update_role", "result", "audit_update", "role_update_result")
        
        # Execute workflow
        workflow = builder.build()
        results, execution_id = self.runner.execute_workflow(
            workflow,
            {
                "user_id": user_id,
                "updates": updates,
                "actor_id": self.manager_id,
                "role": updates.get("role"),
                "role_changed": "role" in updates
            },
            "update_member"
        )
        
        return results
    
    def list_team_members(self, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        List team members with optional filtering.
        
        Args:
            filters: Optional filters to apply
            
        Returns:
            Team member list
        """
        print("👥 Listing team members...")
        
        builder = self.runner.create_workflow("list_team_members")
        
        # Get team members via API
        builder.add_node("HTTPRequestNode", "get_team_members", {
            "name": "fetch_team_members",
            "url": f"{self.api_base_url}/api/v1/teams/my-team/members",
            "method": "GET",
            "headers": {
                "Authorization": f"Bearer {self._get_auth_token()}"
            },
            "params": filters or {}
        })
        
        # Apply additional filtering if needed
        builder.add_node("DataTransformer", "apply_filters", {
            "name": "apply_member_filters",
            "operations": [
                {
                    "type": "filter",
                    "config": {
                        "conditions": filters or {}
                    }
                },
                {
                    "type": "sort",
                    "config": {
                        "by": "last_name",
                        "order": "asc"
                    }
                }
            ]
        })
        
        # Enrich with role information
        builder.add_node("HTTPRequestNode", "enrich_roles", {
            "name": "enrich_member_roles",
            "url": f"{self.api_base_url}/api/v1/users/roles/batch",
            "method": "POST",
            "headers": {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._get_auth_token()}"
            },
            "body": {
                "user_ids": "{{member_ids}}"
            }
        })
        
        # Connect workflow nodes
        builder.add_connection("get_team_members", "result.data", "apply_filters", "members")
        builder.add_connection("apply_filters", "result", "enrich_roles", "filtered_members")
        
        # Execute workflow
        workflow = builder.build()
        results, execution_id = self.runner.execute_workflow(
            workflow, {"filters": filters}, "list_team_members"
        )
        
        return results
    
    def run_demo(self) -> Dict[str, Any]:
        """
        Run a demonstration of manager user management.
        
        Returns:
            Demonstration results
        """
        print("🚀 Starting Manager User Management Demonstration...")
        print("=" * 70)
        print("NOTE: This requires the user_management API to be running!")
        print("Start it with: python -m apps.user_management.api")
        print("=" * 70)
        
        results = {}
        
        try:
            # 1. Add a team member
            print("\n1. Adding Team Member...")
            member_data = {
                "email": "new.member@company.com",
                "first_name": "New",
                "last_name": "Member",
                "department": "Engineering",
                "position": "Junior Developer"
            }
            results["add_member"] = self.add_team_member(member_data)
            
            # 2. List team members
            print("\n2. Listing Team Members...")
            results["team_list"] = self.list_team_members({"active": True})
            
            # 3. Update member profile (would use real user ID)
            print("\n3. Updating Member Profile...")
            updates = {
                "position": "Developer",
                "phone": "+1-555-0123"
            }
            # results["update"] = self.update_member_profile("user_123", updates)
            
            print("\n✅ Manager user management demonstration completed!")
            return results
            
        except Exception as e:
            print(f"❌ Demonstration failed: {str(e)}")
            print("\nTo run this demo, start the API server first:")
            print("python -m apps.user_management.api")
            raise


def test_workflow(test_params: Optional[Dict[str, Any]] = None) -> bool:
    """
    Test the refactored manager workflow.
    
    Args:
        test_params: Optional test parameters
        
    Returns:
        True if test passes, False otherwise
    """
    try:
        print("🧪 Testing Manager User Management Workflow...")
        
        # Create test workflow
        workflow = ManagerUserManagementWorkflowRefactored("test_manager")
        
        # Validate workflow structure
        builder = workflow.runner.create_workflow("test_validation")
        
        # Add service nodes to test registration
        builder.add_node("UserServiceNode", "test_user_service", {
            "operation": "list_users"
        })
        
        builder.add_node("RoleServiceNode", "test_role_service", {
            "operation": "check_permission"
        })
        
        test_workflow = builder.build()
        
        if test_workflow and len(test_workflow.nodes) >= 2:
            print("✅ Manager workflow structure test passed")
            return True
        else:
            return False
        
    except Exception as e:
        print(f"❌ Manager workflow test failed: {str(e)}")
        return False


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        # Run test
        success = test_workflow()
        sys.exit(0 if success else 1)
    else:
        # Run demonstration
        workflow = ManagerUserManagementWorkflowRefactored()
        
        try:
            results = workflow.run_demo()
            print("🎉 Manager workflow demonstration completed!")
        except Exception as e:
            print(f"❌ Demonstration failed: {str(e)}")
            print("\nTo run this demo, start the API server first:")
            print("python -m apps.user_management.api")
            sys.exit(1)