"""
Functional tests for complete user lifecycle

Tests end-to-end user management scenarios including creation,
authentication, role management, and deletion.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch
import uuid

from apps.user_management.workflows.registry import WorkflowRegistry
from kailash.middleware import AgentUIMiddleware
from kailash.runtime.local import LocalRuntime


class TestUserLifecycle:
    """Test complete user lifecycle scenarios."""
    
    @pytest.fixture
    async def mock_agent_ui(self):
        """Create mock AgentUIMiddleware for testing."""
        agent_ui = AsyncMock()
        agent_ui.create_session = AsyncMock()
        agent_ui.execute_workflow_template = AsyncMock()
        agent_ui.wait_for_execution = AsyncMock()
        agent_ui.create_dynamic_workflow = AsyncMock()
        agent_ui.execute_workflow = AsyncMock()
        agent_ui.register_workflow_template = AsyncMock()
        return agent_ui
    
    @pytest.fixture
    async def workflow_registry(self, mock_agent_ui):
        """Create WorkflowRegistry with mock agent UI."""
        registry = WorkflowRegistry(mock_agent_ui)
        await registry.register_all_workflows()
        return registry
    
    @pytest.mark.asyncio
    async def test_complete_user_creation_flow(self, workflow_registry, sample_user_data):
        """Test complete user creation with SSO and MFA setup."""
        mock_agent_ui = workflow_registry.agent_ui
        
        # Mock session creation
        session_id = "test_session_123"
        mock_agent_ui.create_session.return_value = session_id
        
        # Mock workflow execution
        execution_id = "test_execution_123"
        mock_agent_ui.execute_workflow_template.return_value = execution_id
        
        # Mock successful user creation result
        user_id = str(uuid.uuid4())
        mock_result = {
            "outputs": {
                "validate_user_data": {
                    "result": {
                        "valid": True,
                        "errors": [],
                        "user_data": sample_user_data
                    }
                },
                "check_permissions": {
                    "allowed": True
                },
                "create_user": {
                    "user_result": {
                        "user_id": user_id,
                        "email": sample_user_data["email"],
                        "first_name": sample_user_data["first_name"],
                        "last_name": sample_user_data["last_name"],
                        "is_active": True,
                        "created_at": datetime.now().isoformat()
                    }
                },
                "setup_sso": {
                    "sso_result": {
                        "success": True,
                        "provider": "saml",
                        "entity_id": "test_user_entity"
                    }
                },
                "setup_mfa": {
                    "mfa_result": {
                        "success": True,
                        "methods": ["totp"],
                        "backup_codes": ["12345678", "87654321"]
                    }
                },
                "log_audit": {
                    "audit_result": {
                        "logged": True,
                        "entry_id": str(uuid.uuid4())
                    }
                },
                "send_notification": {
                    "result": {
                        "type": "user_created",
                        "user_id": user_id,
                        "email": sample_user_data["email"],
                        "sso_enabled": True,
                        "mfa_enabled": True
                    }
                }
            }
        }
        
        mock_agent_ui.wait_for_execution.return_value = mock_result
        
        # Execute the workflow
        result = await self._execute_user_creation_workflow(
            mock_agent_ui,
            sample_user_data
        )
        
        # Verify workflow execution
        mock_agent_ui.create_session.assert_called_once()
        mock_agent_ui.execute_workflow_template.assert_called_once_with(
            session_id,
            "user_creation_enterprise",
            inputs={"user_data": sample_user_data}
        )
        mock_agent_ui.wait_for_execution.assert_called_once_with(
            session_id,
            execution_id,
            timeout=30
        )
        
        # Verify results
        user_result = result["outputs"]["create_user"]["user_result"]
        assert user_result["user_id"] == user_id
        assert user_result["email"] == sample_user_data["email"]
        assert user_result["is_active"] is True
        
        sso_result = result["outputs"]["setup_sso"]["sso_result"]
        assert sso_result["success"] is True
        
        mfa_result = result["outputs"]["setup_mfa"]["mfa_result"]
        assert mfa_result["success"] is True
        assert len(mfa_result["backup_codes"]) == 2
    
    @pytest.mark.asyncio
    async def test_user_authentication_flow(self, workflow_registry):
        """Test complete authentication flow with risk assessment."""
        mock_agent_ui = workflow_registry.agent_ui
        
        # Authentication data
        auth_data = {
            "credentials": {
                "username": "test@example.com",
                "password": "secure_password",
                "device_id": "test_device_123",
                "ip_address": "192.168.1.100"
            },
            "context": {
                "timestamp": datetime.now().isoformat(),
                "user_agent": "Mozilla/5.0 Test Browser"
            }
        }
        
        # Mock authentication workflow result
        session_id = "auth_session_123"
        execution_id = "auth_execution_123"
        user_id = str(uuid.uuid4())
        
        mock_result = {
            "outputs": {
                "assess_risk": {
                    "risk_score": 0.2,  # Low risk
                    "factors": ["new_device", "usual_location"],
                    "recommendation": "proceed"
                },
                "threat_detection": {
                    "threat_assessment": {
                        "threats_detected": [],
                        "risk_level": "low",
                        "confidence": 0.95
                    }
                },
                "authenticate": {
                    "auth_result": {
                        "authenticated": True,
                        "user_id": user_id,
                        "session_token": "secure_session_token_123",
                        "requires_mfa": False,
                        "auth_method": "password"
                    }
                },
                "create_session": {
                    "session": {
                        "session_id": str(uuid.uuid4()),
                        "access_token": "access_token_123",
                        "refresh_token": "refresh_token_123",
                        "expires_at": (datetime.now() + timedelta(hours=1)).isoformat()
                    }
                },
                "log_event": {
                    "security_event": {
                        "event_type": "user_authenticated",
                        "severity": "INFO",
                        "logged": True
                    }
                }
            }
        }
        
        mock_agent_ui.create_session.return_value = session_id
        mock_agent_ui.execute_workflow_template.return_value = execution_id
        mock_agent_ui.wait_for_execution.return_value = mock_result
        
        # Execute authentication workflow
        result = await self._execute_authentication_workflow(
            mock_agent_ui,
            auth_data
        )
        
        # Verify authentication success
        auth_result = result["outputs"]["authenticate"]["auth_result"]
        assert auth_result["authenticated"] is True
        assert auth_result["user_id"] == user_id
        
        session_result = result["outputs"]["create_session"]["session"]
        assert "access_token" in session_result
        assert "refresh_token" in session_result
        
        # Verify security measures
        risk_assessment = result["outputs"]["assess_risk"]
        assert risk_assessment["risk_score"] == 0.2
        
        threat_assessment = result["outputs"]["threat_detection"]["threat_assessment"]
        assert threat_assessment["risk_level"] == "low"
    
    @pytest.mark.asyncio
    async def test_high_risk_authentication_flow(self, workflow_registry):
        """Test authentication flow with high risk factors."""
        mock_agent_ui = workflow_registry.agent_ui
        
        # High-risk authentication data
        auth_data = {
            "credentials": {
                "username": "test@example.com",
                "password": "secure_password",
                "device_id": "unknown_device",
                "ip_address": "203.0.113.1"  # Suspicious IP
            },
            "context": {
                "timestamp": datetime.now().isoformat(),
                "location": "Unknown Country"
            }
        }
        
        # Mock high-risk authentication result
        mock_result = {
            "outputs": {
                "assess_risk": {
                    "risk_score": 0.8,  # High risk
                    "factors": ["unknown_device", "suspicious_location", "unusual_time"],
                    "recommendation": "require_additional_verification"
                },
                "threat_detection": {
                    "threat_assessment": {
                        "threats_detected": ["location_anomaly"],
                        "risk_level": "high",
                        "confidence": 0.85
                    }
                },
                "authenticate": {
                    "auth_result": {
                        "authenticated": False,
                        "requires_mfa": True,
                        "mfa_methods": ["totp", "sms", "email"],
                        "challenge_token": "mfa_challenge_123"
                    }
                }
            }
        }
        
        mock_agent_ui.create_session.return_value = "high_risk_session"
        mock_agent_ui.execute_workflow_template.return_value = "high_risk_execution"
        mock_agent_ui.wait_for_execution.return_value = mock_result
        
        # Execute authentication workflow
        result = await self._execute_authentication_workflow(
            mock_agent_ui,
            auth_data
        )
        
        # Verify MFA is required
        auth_result = result["outputs"]["authenticate"]["auth_result"]
        assert auth_result["authenticated"] is False
        assert auth_result["requires_mfa"] is True
        assert "totp" in auth_result["mfa_methods"]
        
        # Verify risk assessment
        risk_assessment = result["outputs"]["assess_risk"]
        assert risk_assessment["risk_score"] == 0.8
        assert "unknown_device" in risk_assessment["factors"]
    
    @pytest.mark.asyncio
    async def test_role_assignment_flow(self, workflow_registry):
        """Test role assignment and permission workflow."""
        mock_agent_ui = workflow_registry.agent_ui
        
        # Role assignment data
        user_id = str(uuid.uuid4())
        role_data = {
            "action": "assign",
            "user_id": user_id,
            "role_name": "developer",
            "reason": "Joined development team"
        }
        
        # Mock role assignment result
        mock_result = {
            "outputs": {
                "validate_role": {
                    "result": {
                        "valid": True,
                        "errors": [],
                        "role_data": role_data
                    }
                },
                "check_permissions": {
                    "allowed": True,
                    "reason": "Admin has role assignment permissions"
                },
                "manage_role": {
                    "result": {
                        "success": True,
                        "assignment_id": str(uuid.uuid4()),
                        "role_assigned": "developer",
                        "assigned_at": datetime.now().isoformat()
                    }
                },
                "audit_log": {
                    "audit_result": {
                        "logged": True,
                        "event_type": "role_assigned"
                    }
                }
            }
        }
        
        mock_agent_ui.create_session.return_value = "role_session"
        mock_agent_ui.execute_workflow_template.return_value = "role_execution"
        mock_agent_ui.wait_for_execution.return_value = mock_result
        
        # Execute role assignment workflow
        result = await self._execute_role_management_workflow(
            mock_agent_ui,
            role_data
        )
        
        # Verify role assignment
        role_result = result["outputs"]["manage_role"]["result"]
        assert role_result["success"] is True
        assert role_result["role_assigned"] == "developer"
        
        # Verify audit logging
        audit_result = result["outputs"]["audit_log"]["audit_result"]
        assert audit_result["logged"] is True
        assert audit_result["event_type"] == "role_assigned"
    
    @pytest.mark.asyncio
    async def test_gdpr_data_export_flow(self, workflow_registry):
        """Test GDPR data export workflow."""
        mock_agent_ui = workflow_registry.agent_ui
        
        user_id = str(uuid.uuid4())
        gdpr_request = {
            "action": "export_data",
            "user_id": user_id,
            "format": "json"
        }
        
        # Mock GDPR export result
        mock_result = {
            "outputs": {
                "validate_request": {
                    "result": {
                        "valid": True,
                        "errors": [],
                        "request_data": gdpr_request
                    }
                },
                "gdpr_processor": {
                    "compliance_result": {
                        "success": True,
                        "request_id": str(uuid.uuid4()),
                        "data_categories": [
                            "personal_info",
                            "account_data",
                            "activity_logs"
                        ],
                        "export_url": f"https://exports.example.com/{user_id}.json",
                        "expires_at": (datetime.now() + timedelta(days=7)).isoformat()
                    }
                },
                "data_retention": {
                    "retention_info": {
                        "policies_applied": ["user_data_7_years"],
                        "next_review": (datetime.now() + timedelta(days=365)).isoformat()
                    }
                },
                "audit_compliance": {
                    "compliance_audit": {
                        "logged": True,
                        "compliance_framework": "gdpr",
                        "event_type": "data_export_requested"
                    }
                }
            }
        }
        
        mock_agent_ui.create_session.return_value = "gdpr_session"
        mock_agent_ui.execute_workflow_template.return_value = "gdpr_execution"
        mock_agent_ui.wait_for_execution.return_value = mock_result
        
        # Execute GDPR workflow
        result = await self._execute_gdpr_workflow(
            mock_agent_ui,
            gdpr_request
        )
        
        # Verify GDPR compliance
        gdpr_result = result["outputs"]["gdpr_processor"]["compliance_result"]
        assert gdpr_result["success"] is True
        assert len(gdpr_result["data_categories"]) == 3
        assert "export_url" in gdpr_result
        
        # Verify compliance audit
        audit_result = result["outputs"]["audit_compliance"]["compliance_audit"]
        assert audit_result["compliance_framework"] == "gdpr"
        assert audit_result["logged"] is True
    
    @pytest.mark.asyncio
    async def test_user_deletion_flow(self, workflow_registry):
        """Test complete user deletion with compliance."""
        mock_agent_ui = workflow_registry.agent_ui
        
        user_id = str(uuid.uuid4())
        deletion_data = {
            "user_id": user_id,
            "deletion_reason": "Account closure requested"
        }
        
        # Mock deletion workflow result
        mock_result = {
            "outputs": {
                "check_permissions": {
                    "allowed": True,
                    "requires_elevation": True
                },
                "compliance_check": {
                    "compliance_result": {
                        "can_delete": True,
                        "retention_required": ["audit_logs"],
                        "retention_period": "7 years",
                        "compliance_frameworks": ["gdpr", "ccpa"]
                    }
                },
                "archive_data": {
                    "result": {
                        "archive_record": {
                            "archive_id": str(uuid.uuid4()),
                            "user_id": user_id,
                            "archived_at": datetime.now().isoformat(),
                            "data_retained": ["audit_logs", "compliance_records"]
                        },
                        "ready_to_delete": True
                    }
                },
                "delete_user": {
                    "deletion_result": {
                        "success": True,
                        "deleted_at": datetime.now().isoformat(),
                        "archive_reference": "archive_123"
                    }
                },
                "audit_log": {
                    "compliance_audit": {
                        "logged": True,
                        "event_type": "user_deleted",
                        "compliance_mode": True
                    }
                }
            }
        }
        
        mock_agent_ui.create_session.return_value = "deletion_session"
        mock_agent_ui.execute_workflow_template.return_value = "deletion_execution"
        mock_agent_ui.wait_for_execution.return_value = mock_result
        
        # Execute deletion workflow
        result = await self._execute_deletion_workflow(
            mock_agent_ui,
            deletion_data
        )
        
        # Verify deletion success
        deletion_result = result["outputs"]["delete_user"]["deletion_result"]
        assert deletion_result["success"] is True
        assert "deleted_at" in deletion_result
        
        # Verify data archival
        archive_result = result["outputs"]["archive_data"]["result"]
        assert archive_result["ready_to_delete"] is True
        assert "archive_id" in archive_result["archive_record"]
        
        # Verify compliance
        compliance_result = result["outputs"]["compliance_check"]["compliance_result"]
        assert compliance_result["can_delete"] is True
        assert "gdpr" in compliance_result["compliance_frameworks"]
    
    # Helper methods for workflow execution
    async def _execute_user_creation_workflow(self, agent_ui, user_data):
        """Execute user creation workflow."""
        session_id = await agent_ui.create_session("test_user_creation")
        execution_id = await agent_ui.execute_workflow_template(
            session_id,
            "user_creation_enterprise",
            inputs={"user_data": user_data}
        )
        return await agent_ui.wait_for_execution(session_id, execution_id, timeout=30)
    
    async def _execute_authentication_workflow(self, agent_ui, auth_data):
        """Execute authentication workflow."""
        session_id = await agent_ui.create_session("test_authentication")
        execution_id = await agent_ui.execute_workflow_template(
            session_id,
            "user_authentication_enterprise",
            inputs=auth_data
        )
        return await agent_ui.wait_for_execution(session_id, execution_id, timeout=15)
    
    async def _execute_role_management_workflow(self, agent_ui, role_data):
        """Execute role management workflow."""
        session_id = await agent_ui.create_session("test_role_management")
        execution_id = await agent_ui.execute_workflow_template(
            session_id,
            "role_management_enterprise",
            inputs=role_data
        )
        return await agent_ui.wait_for_execution(session_id, execution_id, timeout=10)
    
    async def _execute_gdpr_workflow(self, agent_ui, gdpr_request):
        """Execute GDPR compliance workflow."""
        session_id = await agent_ui.create_session("test_gdpr")
        execution_id = await agent_ui.execute_workflow_template(
            session_id,
            "gdpr_compliance_enterprise",
            inputs=gdpr_request
        )
        return await agent_ui.wait_for_execution(session_id, execution_id, timeout=30)
    
    async def _execute_deletion_workflow(self, agent_ui, deletion_data):
        """Execute user deletion workflow."""
        session_id = await agent_ui.create_session("test_deletion")
        execution_id = await agent_ui.execute_workflow_template(
            session_id,
            "user_deletion_enterprise",
            inputs=deletion_data
        )
        return await agent_ui.wait_for_execution(session_id, execution_id, timeout=30)


class TestPermissionScenarios:
    """Test complex permission and access control scenarios."""
    
    @pytest.mark.asyncio
    async def test_dynamic_permission_evaluation(self, workflow_registry):
        """Test dynamic permission evaluation with context."""
        mock_agent_ui = workflow_registry.agent_ui
        
        # Permission check with dynamic context
        permission_data = {
            "user_id": str(uuid.uuid4()),
            "resource": "documents:project_alpha",
            "action": "read",
            "context": {
                "time": "business_hours",
                "location": "office",
                "project_member": True,
                "clearance_level": "confidential"
            }
        }
        
        # Mock permission evaluation result
        mock_result = {
            "outputs": {
                "get_user_context": {
                    "user": {
                        "id": permission_data["user_id"],
                        "department": "Engineering",
                        "clearance_level": "confidential",
                        "project_assignments": ["project_alpha"]
                    }
                },
                "evaluate_permission": {
                    "evaluation_result": {
                        "allowed": True,
                        "reason": "User is project member with appropriate clearance",
                        "policies_applied": [
                            "project_access_policy",
                            "clearance_level_policy",
                            "business_hours_policy"
                        ],
                        "ai_reasoning": "Access granted based on project membership and clearance level match",
                        "evaluation_time_ms": 12.3
                    }
                },
                "format_response": {
                    "result": {
                        "allowed": True,
                        "reason": "User is project member with appropriate clearance",
                        "applicable_policies": ["project_access_policy"],
                        "user_id": permission_data["user_id"],
                        "resource": permission_data["resource"],
                        "action": permission_data["action"],
                        "timestamp": datetime.now().isoformat()
                    }
                }
            }
        }
        
        mock_agent_ui.create_session.return_value = "permission_session"
        mock_agent_ui.execute_workflow_template.return_value = "permission_execution"
        mock_agent_ui.wait_for_execution.return_value = mock_result
        
        # Execute permission check
        result = await self._execute_permission_check_workflow(
            mock_agent_ui,
            permission_data
        )
        
        # Verify permission granted
        final_result = result["outputs"]["format_response"]["result"]
        assert final_result["allowed"] is True
        assert "project member" in final_result["reason"]
        
        # Verify AI reasoning
        evaluation_result = result["outputs"]["evaluate_permission"]["evaluation_result"]
        assert "ai_reasoning" in evaluation_result
        assert evaluation_result["evaluation_time_ms"] < 15  # Performance target
    
    async def _execute_permission_check_workflow(self, agent_ui, permission_data):
        """Execute permission check workflow."""
        session_id = await agent_ui.create_session("test_permission_check")
        execution_id = await agent_ui.execute_workflow_template(
            session_id,
            "permission_check_enterprise",
            inputs=permission_data
        )
        return await agent_ui.wait_for_execution(session_id, execution_id, timeout=5)


class TestErrorScenarios:
    """Test error handling and edge cases."""
    
    @pytest.mark.asyncio
    async def test_invalid_user_creation(self, workflow_registry):
        """Test user creation with invalid data."""
        mock_agent_ui = workflow_registry.agent_ui
        
        # Invalid user data
        invalid_data = {
            "email": "invalid-email",  # Invalid format
            "first_name": "",  # Empty name
            "department": None
        }
        
        # Mock validation failure
        mock_result = {
            "outputs": {
                "validate_user_data": {
                    "result": {
                        "valid": False,
                        "errors": [
                            "Invalid email format",
                            "First name is required"
                        ],
                        "user_data": invalid_data
                    }
                }
            }
        }
        
        mock_agent_ui.create_session.return_value = "invalid_session"
        mock_agent_ui.execute_workflow_template.return_value = "invalid_execution"
        mock_agent_ui.wait_for_execution.return_value = mock_result
        
        # Execute workflow with invalid data
        result = await self._execute_user_creation_workflow(
            mock_agent_ui,
            invalid_data
        )
        
        # Verify validation failure
        validation_result = result["outputs"]["validate_user_data"]["result"]
        assert validation_result["valid"] is False
        assert len(validation_result["errors"]) == 2
        assert "Invalid email format" in validation_result["errors"]
    
    @pytest.mark.asyncio
    async def test_permission_denied_scenario(self, workflow_registry):
        """Test permission denied scenario."""
        mock_agent_ui = workflow_registry.agent_ui
        
        # Permission request that should be denied
        permission_data = {
            "user_id": str(uuid.uuid4()),
            "resource": "admin:system_settings",
            "action": "delete",
            "context": {"role": "user"}  # Regular user trying admin action
        }
        
        # Mock permission denied result
        mock_result = {
            "outputs": {
                "evaluate_permission": {
                    "evaluation_result": {
                        "allowed": False,
                        "reason": "Insufficient privileges for admin operations",
                        "required_roles": ["admin", "system_admin"],
                        "user_roles": ["user"],
                        "evaluation_time_ms": 8.7
                    }
                },
                "format_response": {
                    "result": {
                        "allowed": False,
                        "reason": "Insufficient privileges for admin operations",
                        "applicable_policies": [],
                        "user_id": permission_data["user_id"],
                        "timestamp": datetime.now().isoformat()
                    }
                }
            }
        }
        
        mock_agent_ui.create_session.return_value = "denied_session"
        mock_agent_ui.execute_workflow_template.return_value = "denied_execution"
        mock_agent_ui.wait_for_execution.return_value = mock_result
        
        # Execute permission check
        result = await self._execute_permission_check_workflow(
            mock_agent_ui,
            permission_data
        )
        
        # Verify permission denied
        final_result = result["outputs"]["format_response"]["result"]
        assert final_result["allowed"] is False
        assert "Insufficient privileges" in final_result["reason"]
        
        evaluation_result = result["outputs"]["evaluate_permission"]["evaluation_result"]
        assert "admin" in evaluation_result["required_roles"]
    
    async def _execute_user_creation_workflow(self, agent_ui, user_data):
        """Execute user creation workflow."""
        session_id = await agent_ui.create_session("test_user_creation")
        execution_id = await agent_ui.execute_workflow_template(
            session_id,
            "user_creation_enterprise",
            inputs={"user_data": user_data}
        )
        return await agent_ui.wait_for_execution(session_id, execution_id, timeout=30)
    
    async def _execute_permission_check_workflow(self, agent_ui, permission_data):
        """Execute permission check workflow."""
        session_id = await agent_ui.create_session("test_permission_check")
        execution_id = await agent_ui.execute_workflow_template(
            session_id,
            "permission_check_enterprise",
            inputs=permission_data
        )
        return await agent_ui.wait_for_execution(session_id, execution_id, timeout=5)