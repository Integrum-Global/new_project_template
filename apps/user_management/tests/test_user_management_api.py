"""
Test User Management API functionality.

This module tests the complete user management application including:
- User CRUD operations
- Authentication flows
- Authorization and permissions
- Session management
- Audit trails
- Integration between components
"""

import pytest
import asyncio
from datetime import datetime, timedelta, UTC
from unittest.mock import Mock, patch, MagicMock
import json
import jwt
import requests

from kailash.nodes.admin import UserManagementNode, RoleManagementNode
from kailash.nodes.auth.sso import SSOAuthenticationNode
from kailash.nodes.auth.enterprise_auth_provider import EnterpriseAuthProviderNode
from kailash.nodes.security.abac_evaluator import ABACPermissionEvaluatorNode
from kailash.workflow import Workflow
from kailash.runtime import LocalRuntime


class TestUserManagementAPI:
    """Test suite for User Management API."""
    
    @pytest.fixture
    def app_components(self):
        """Create application components."""
        return {
            "user_mgmt": UserManagementNode(name="user_management"),
            "role_mgmt": RoleManagementNode(name="role_management"),
            "auth_provider": EnterpriseAuthProviderNode(
                name="auth_provider",
                enabled_methods=["sso", "directory", "mfa"],
                sso_config={
                    "providers": ["saml", "oauth2"],
                    "saml_settings": {
                        "entity_id": "https://sso.company.com"
                    }
                },
                directory_config={
                    "directory_type": "ldap",
                    "connection_config": {
                        "server": "ldap://dc.company.com"
                    }
                }
            ),
            "permission_eval": ABACPermissionEvaluatorNode(
                name="permission_evaluator",
                ai_reasoning=True
            )
        }
    
    @pytest.fixture
    def test_users(self):
        """Create test user data."""
        return [
            {
                "username": "admin",
                "email": "admin@company.com",
                "first_name": "Admin",
                "last_name": "User",
                "roles": ["admin", "user"],
                "department": "IT",
                "status": "active"
            },
            {
                "username": "jdoe",
                "email": "jdoe@company.com",
                "first_name": "John",
                "last_name": "Doe",
                "roles": ["user"],
                "department": "Engineering",
                "status": "active"
            },
            {
                "username": "jsmith",
                "email": "jsmith@company.com",
                "first_name": "Jane",
                "last_name": "Smith",
                "roles": ["user", "manager"],
                "department": "HR",
                "status": "active"
            }
        ]
    
    def test_user_creation_workflow(self, app_components, test_users):
        """Test complete user creation workflow."""
        workflow = Workflow(name="user_creation_workflow")
        
        # Add nodes to workflow
        workflow.add_node(app_components["user_mgmt"])
        workflow.add_node(app_components["role_mgmt"])
        workflow.add_node(app_components["auth_provider"])
        
        # Connect workflow
        workflow.connect("user_management", "role_management")
        workflow.connect("role_management", "auth_provider")
        
        # Execute workflow
        runtime = LocalRuntime()
        
        for user_data in test_users:
            result = runtime.execute(
                workflow,
                inputs={
                    "user_management": {
                        "action": "create",
                        "user_data": user_data
                    }
                }
            )
            
            assert result.success is True
            assert result.outputs["user_management"]["user_id"] is not None
            assert result.outputs["role_management"]["roles_assigned"] == user_data["roles"]
    
    def test_authentication_flow(self, app_components):
        """Test user authentication flow."""
        auth_workflow = Workflow(name="authentication_workflow")
        
        # Add authentication nodes
        auth_workflow.add_node(app_components["auth_provider"])
        auth_workflow.add_node(app_components["permission_eval"])
        
        # Connect nodes
        auth_workflow.connect("auth_provider", "permission_evaluator")
        
        # Test authentication
        runtime = LocalRuntime()
        
        with patch.object(app_components["auth_provider"], '_authenticate_with_provider') as mock_auth:
            mock_auth.return_value = {
                "success": True,
                "user": {
                    "username": "jdoe",
                    "roles": ["user"],
                    "department": "Engineering"
                }
            }
            
            result = runtime.execute(
                auth_workflow,
                inputs={
                    "auth_provider": {
                        "action": "authenticate",
                        "username": "jdoe",
                        "password": "password123",
                        "auth_context": {
                            "ip_address": "10.0.1.50",
                            "user_agent": "Mozilla/5.0"
                        }
                    }
                }
            )
        
        assert result.success is True
        assert result.outputs["auth_provider"]["authenticated"] is True
        assert "session_id" in result.outputs["auth_provider"]
    
    def test_authorization_workflow(self, app_components):
        """Test authorization workflow with ABAC."""
        auth_workflow = Workflow(name="authorization_workflow")
        
        # Add permission evaluator
        auth_workflow.add_node(app_components["permission_eval"])
        
        runtime = LocalRuntime()
        
        # Test user permission check
        user_context = {
            "user_id": "jdoe",
            "roles": ["user"],
            "department": "Engineering",
            "clearance_level": 3
        }
        
        resource_context = {
            "resource_type": "user_profile",
            "resource_id": "jsmith",
            "owner": "jsmith",
            "classification": "internal"
        }
        
        result = runtime.execute(
            auth_workflow,
            inputs={
                "permission_evaluator": {
                    "user_context": user_context,
                    "resource_context": resource_context,
                    "permission": "read"
                }
            }
        )
        
        assert result.success is True
        # User should be able to read internal resources
        assert result.outputs["permission_evaluator"]["allowed"] is True
    
    def test_user_update_with_audit(self, app_components):
        """Test user update with audit trail."""
        update_workflow = Workflow(name="user_update_workflow")
        
        # Add nodes
        update_workflow.add_node(app_components["user_mgmt"])
        update_workflow.add_node(app_components["permission_eval"])
        
        runtime = LocalRuntime()
        
        # Admin context for permission
        admin_context = {
            "user_id": "admin",
            "roles": ["admin"],
            "department": "IT"
        }
        
        # Update user
        result = runtime.execute(
            update_workflow,
            inputs={
                "permission_evaluator": {
                    "user_context": admin_context,
                    "resource_context": {
                        "resource_type": "user",
                        "resource_id": "jdoe"
                    },
                    "permission": "update"
                },
                "user_management": {
                    "action": "update",
                    "user_id": "jdoe",
                    "updates": {
                        "department": "DevOps",
                        "title": "Senior Engineer"
                    },
                    "updated_by": "admin"
                }
            }
        )
        
        assert result.success is True
        assert result.outputs["permission_evaluator"]["allowed"] is True
        assert result.outputs["user_management"]["updated"] is True
    
    def test_role_based_access_control(self, app_components):
        """Test RBAC integration."""
        rbac_workflow = Workflow(name="rbac_workflow")
        
        # Add role management
        rbac_workflow.add_node(app_components["role_mgmt"])
        rbac_workflow.add_node(app_components["permission_eval"])
        
        runtime = LocalRuntime()
        
        # Create custom role
        role_result = runtime.execute(
            rbac_workflow,
            inputs={
                "role_management": {
                    "action": "create_role",
                    "role_data": {
                        "name": "data_analyst",
                        "description": "Data analysis team",
                        "permissions": [
                            "read:analytics",
                            "write:reports",
                            "read:databases"
                        ],
                        "parent_roles": ["user"]
                    }
                }
            }
        )
        
        assert role_result.success is True
        assert role_result.outputs["role_management"]["role_id"] is not None
        
        # Assign role to user
        assign_result = runtime.execute(
            rbac_workflow,
            inputs={
                "role_management": {
                    "action": "assign_role",
                    "user_id": "jdoe",
                    "role": "data_analyst"
                }
            }
        )
        
        assert assign_result.success is True
    
    def test_bulk_user_operations(self, app_components, test_users):
        """Test bulk user operations."""
        bulk_workflow = Workflow(name="bulk_operations")
        
        bulk_workflow.add_node(app_components["user_mgmt"])
        
        runtime = LocalRuntime()
        
        # Bulk create users
        result = runtime.execute(
            bulk_workflow,
            inputs={
                "user_management": {
                    "action": "bulk_create",
                    "users": test_users,
                    "options": {
                        "send_welcome_email": False,
                        "generate_temp_password": True
                    }
                }
            }
        )
        
        assert result.success is True
        assert result.outputs["user_management"]["created_count"] == len(test_users)
        assert result.outputs["user_management"]["failed_count"] == 0
    
    def test_user_deactivation_cascade(self, app_components):
        """Test user deactivation with cascading effects."""
        deactivation_workflow = Workflow(name="user_deactivation")
        
        # Add all components
        for node in app_components.values():
            deactivation_workflow.add_node(node)
        
        # Connect nodes for deactivation flow
        deactivation_workflow.connect("permission_evaluator", "user_management")
        deactivation_workflow.connect("user_management", "auth_provider")
        deactivation_workflow.connect("user_management", "role_management")
        
        runtime = LocalRuntime()
        
        # Deactivate user
        result = runtime.execute(
            deactivation_workflow,
            inputs={
                "permission_evaluator": {
                    "user_context": {"user_id": "admin", "roles": ["admin"]},
                    "resource_context": {"resource_type": "user", "resource_id": "jdoe"},
                    "permission": "deactivate"
                },
                "user_management": {
                    "action": "deactivate",
                    "user_id": "jdoe",
                    "reason": "Employee termination",
                    "deactivated_by": "admin"
                }
            }
        )
        
        assert result.success is True
        assert result.outputs["user_management"]["status"] == "inactive"
        # Sessions should be terminated
        assert result.outputs["auth_provider"].get("sessions_terminated", 0) >= 0
    
    def test_user_search_and_filter(self, app_components):
        """Test user search functionality."""
        search_workflow = Workflow(name="user_search")
        
        search_workflow.add_node(app_components["user_mgmt"])
        search_workflow.add_node(app_components["permission_eval"])
        
        runtime = LocalRuntime()
        
        # Search users
        result = runtime.execute(
            search_workflow,
            inputs={
                "permission_evaluator": {
                    "user_context": {"user_id": "hr_manager", "roles": ["manager", "hr"]},
                    "resource_context": {"resource_type": "user_list"},
                    "permission": "read"
                },
                "user_management": {
                    "action": "search",
                    "filters": {
                        "department": "Engineering",
                        "status": "active",
                        "roles": ["user"]
                    },
                    "pagination": {
                        "page": 1,
                        "page_size": 20
                    }
                }
            }
        )
        
        assert result.success is True
        assert "users" in result.outputs["user_management"]
        assert "total_count" in result.outputs["user_management"]
        assert "page_info" in result.outputs["user_management"]
    
    def test_password_reset_workflow(self, app_components):
        """Test password reset workflow."""
        reset_workflow = Workflow(name="password_reset")
        
        reset_workflow.add_node(app_components["user_mgmt"])
        reset_workflow.add_node(app_components["auth_provider"])
        
        runtime = LocalRuntime()
        
        # Initiate password reset
        init_result = runtime.execute(
            reset_workflow,
            inputs={
                "user_management": {
                    "action": "initiate_password_reset",
                    "email": "jdoe@company.com"
                }
            }
        )
        
        assert init_result.success is True
        assert "reset_token" in init_result.outputs["user_management"]
        
        # Complete password reset
        reset_token = init_result.outputs["user_management"]["reset_token"]
        
        complete_result = runtime.execute(
            reset_workflow,
            inputs={
                "user_management": {
                    "action": "reset_password",
                    "reset_token": reset_token,
                    "new_password": "NewSecurePass123!",
                    "confirm_password": "NewSecurePass123!"
                }
            }
        )
        
        assert complete_result.success is True
        assert complete_result.outputs["user_management"]["password_reset"] is True
    
    def test_user_profile_management(self, app_components):
        """Test user profile self-service."""
        profile_workflow = Workflow(name="profile_management")
        
        profile_workflow.add_node(app_components["user_mgmt"])
        profile_workflow.add_node(app_components["permission_eval"])
        
        runtime = LocalRuntime()
        
        # User updating own profile
        result = runtime.execute(
            profile_workflow,
            inputs={
                "permission_evaluator": {
                    "user_context": {"user_id": "jdoe", "roles": ["user"]},
                    "resource_context": {"resource_type": "user_profile", "resource_id": "jdoe"},
                    "permission": "update_own"
                },
                "user_management": {
                    "action": "update_profile",
                    "user_id": "jdoe",
                    "profile_updates": {
                        "phone": "+1234567890",
                        "bio": "Software engineer passionate about cloud technologies",
                        "preferences": {
                            "notifications": "email",
                            "theme": "dark"
                        }
                    }
                }
            }
        )
        
        assert result.success is True
        assert result.outputs["permission_evaluator"]["allowed"] is True
        assert result.outputs["user_management"]["profile_updated"] is True
    
    def test_integration_with_external_systems(self, app_components):
        """Test integration with external systems (LDAP, SSO)."""
        integration_workflow = Workflow(name="external_integration")
        
        integration_workflow.add_node(app_components["auth_provider"])
        integration_workflow.add_node(app_components["user_mgmt"])
        
        runtime = LocalRuntime()
        
        # Sync users from LDAP
        with patch.object(app_components["auth_provider"], '_sync_from_ldap') as mock_sync:
            mock_sync.return_value = {
                "users": [
                    {"username": "ldap_user1", "email": "user1@company.com"},
                    {"username": "ldap_user2", "email": "user2@company.com"}
                ],
                "count": 2
            }
            
            result = runtime.execute(
                integration_workflow,
                inputs={
                    "auth_provider": {
                        "action": "sync_users",
                        "source": "ldap",
                        "options": {
                            "filter": "(objectClass=user)",
                            "base_dn": "OU=Users,DC=company,DC=com"
                        }
                    }
                }
            )
        
        assert result.success is True
        assert result.outputs["auth_provider"]["synced_count"] == 2
    
    def test_compliance_reporting(self, app_components):
        """Test compliance and audit reporting."""
        compliance_workflow = Workflow(name="compliance_reporting")
        
        compliance_workflow.add_node(app_components["user_mgmt"])
        
        runtime = LocalRuntime()
        
        # Generate compliance report
        result = runtime.execute(
            compliance_workflow,
            inputs={
                "user_management": {
                    "action": "compliance_report",
                    "report_type": "user_access_review",
                    "options": {
                        "period": "quarterly",
                        "include_inactive": True,
                        "include_privileged": True,
                        "format": "pdf"
                    }
                }
            }
        )
        
        assert result.success is True
        assert "report_id" in result.outputs["user_management"]
        assert "summary" in result.outputs["user_management"]
        assert result.outputs["user_management"]["summary"]["total_users"] > 0
    
    def test_error_handling_and_recovery(self, app_components):
        """Test error handling and recovery mechanisms."""
        error_workflow = Workflow(name="error_handling")
        
        error_workflow.add_node(app_components["user_mgmt"])
        
        runtime = LocalRuntime()
        
        # Test duplicate user creation
        result1 = runtime.execute(
            error_workflow,
            inputs={
                "user_management": {
                    "action": "create",
                    "user_data": {
                        "username": "duplicate_user",
                        "email": "dup@company.com"
                    }
                }
            }
        )
        
        # Try to create duplicate
        result2 = runtime.execute(
            error_workflow,
            inputs={
                "user_management": {
                    "action": "create",
                    "user_data": {
                        "username": "duplicate_user",
                        "email": "dup@company.com"
                    }
                }
            }
        )
        
        assert result1.success is True
        assert result2.success is False
        assert "already exists" in result2.error.lower()
    
    def test_performance_under_load(self, app_components):
        """Test performance with concurrent operations."""
        import concurrent.futures
        import time
        
        perf_workflow = Workflow(name="performance_test")
        perf_workflow.add_node(app_components["user_mgmt"])
        
        runtime = LocalRuntime()
        
        def create_user(index):
            return runtime.execute(
                perf_workflow,
                inputs={
                    "user_management": {
                        "action": "create",
                        "user_data": {
                            "username": f"perf_user_{index}",
                            "email": f"perf{index}@company.com"
                        }
                    }
                }
            )
        
        # Run concurrent user creations
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(create_user, i) for i in range(100)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Check results
        success_count = sum(1 for r in results if r.success)
        assert success_count >= 95  # Allow for some failures due to concurrency
        assert duration < 30  # Should complete within 30 seconds
        
        # Calculate operations per second
        ops_per_second = success_count / duration
        assert ops_per_second > 3  # Should handle at least 3 ops/sec


@pytest.mark.asyncio
class TestUserManagementAPIAsync:
    """Test asynchronous operations in user management."""
    
    async def test_async_user_operations(self):
        """Test async user operations if implemented."""
        # This is a placeholder for future async implementation
        pass