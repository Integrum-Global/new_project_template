#!/usr/bin/env python3
"""
Refactor all user_management workflows to use proper service integration.

This script creates refactored versions of all workflows that:
1. Use service nodes instead of inline business logic
2. Call app APIs via HTTPRequestNode
3. Leverage proper SDK nodes for operations
4. Follow separation of concerns
"""

import os
import sys
from typing import Dict, Any, List


# Template for refactored workflows
REFACTORED_WORKFLOW_TEMPLATE = '''#!/usr/bin/env python3
"""
{title} - Refactored

This workflow properly uses the user_management app's service layer
instead of inline PythonCodeNode logic.
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
from kailash.nodes.data import SQLDatabaseNode
from kailash.nodes.security import AuditLogNode
from kailash.nodes.transform import DataTransformer
from kailash.nodes.logic import SwitchNode


class {class_name}Refactored:
    """
    {description}
    
    This implementation demonstrates proper service integration.
    """
    
    def __init__(self, user_id: str = "{default_user}", api_base_url: str = "http://localhost:8000"):
        """
        Initialize the workflow.
        
        Args:
            user_id: ID of the user performing operations
            api_base_url: Base URL of the user management API
        """
        {{self.user_id}} = user_id
        self.api_base_url = api_base_url
        {{self.runner}} = WorkflowRunner(
            user_type="{user_type}",
            user_id=user_id,
            enable_debug=True,
            enable_audit=True,
            enable_monitoring=True
        )
    
    def _get_auth_token(self) -> str:
        """Get authentication token for API calls."""
        # In production, this would retrieve a valid JWT token
        return f"{{{self.user_id}}}_token"
    
    {methods}
    
    def run_demo(self) -> Dict[str, Any]:
        """
        Run a demonstration of the workflow.
        
        Returns:
            Demonstration results
        """
        print("🚀 Starting {title} Demonstration...")
        print("=" * 70)
        print("NOTE: This requires the user_management API to be running!")
        print("Start it with: python -m apps.user_management.api")
        print("=" * 70)
        
        results = {{}}
        
        try:
            # Run workflow operations
            {demo_calls}
            
            print("\\n✅ Demonstration completed successfully!")
            return results
            
        except Exception as e:
            print(f"❌ Demonstration failed: {str(e)}")
            raise


def test_workflow(test_params: Optional[Dict[str, Any]] = None) -> bool:
    """
    Test the refactored workflow.
    
    Args:
        test_params: Optional test parameters
        
    Returns:
        True if test passes, False otherwise
    """
    try:
        print("🧪 Testing {title}...")
        
        # Create test workflow
        workflow = {class_name}Refactored("test_user")
        
        # Validate workflow structure
        builder = workflow.runner.create_workflow("test_validation")
        
        # Add a service node to test registration
        builder.add_node("UserServiceNode", "test_service", {{
            "operation": "list_users"
        }})
        
        test_workflow = builder.build()
        
        if test_workflow and len(test_workflow.nodes) > 0:
            print("✅ Workflow structure test passed")
            return True
        else:
            return False
        
    except Exception as e:
        print(f"❌ Workflow test failed: {str(e)}")
        return False


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        # Run test
        success = test_workflow()
        sys.exit(0 if success else 1)
    else:
        # Run demonstration
        workflow = {class_name}Refactored()
        
        try:
            results = workflow.run_demo()
            print("🎉 Workflow demonstration completed!")
        except Exception as e:
            print(f"❌ Demonstration failed: {str(e)}")
            print("\\nTo run this demo, start the API server first:")
            print("python -m apps.user_management.api")
            sys.exit(1)
'''


# Workflow refactoring specifications
WORKFLOW_SPECS = {
    "admin_workflows": {
        "03_security_management.py": {
            "class_name": "SecurityManagementWorkflow",
            "title": "Security Management Workflow",
            "description": "Manages security policies, threat detection, and compliance.",
            "default_user": "admin",
            "user_type": "admin",
            "methods": '''
    def configure_security_policies(self, policies: Dict[str, Any]) -> Dict[str, Any]:
        """Configure security policies using SecurityService."""
        builder = {{self.runner}}.create_workflow("configure_policies")
        
        # Apply policies through service
        builder.add_node("SecurityServiceNode", "apply_policies", {
            "operation": "configure_policies"
        })
        
        # Audit the configuration
        builder.add_node("AuditLogNode", "audit_config", {
            "action": "SECURITY_POLICIES_CONFIGURED",
            "resource_type": "security_policy",
            "user_id": {{self.user_id}}
        })
        
        # Connect nodes
        builder.add_connection("apply_policies", "result", "audit_config", "policy_result")
        
        # Execute
        workflow = builder.build()
        results, _ = {{self.runner}}.execute_workflow(workflow, {"policies": policies}, "configure_policies")
        return results
    
    def detect_security_threats(self) -> Dict[str, Any]:
        """Detect and analyze security threats."""
        builder = {{self.runner}}.create_workflow("threat_detection")
        
        # Call threat detection API
        builder.add_node("HTTPRequestNode", "detect_threats", {
            "url": f"{{self.api_base_url}}/api/v1/security/threats/detect",
            "method": "POST",
            "headers": {
                "Authorization": f"Bearer {{self._get_auth_token()}}"
            }
        })
        
        # Analyze results
        builder.add_node("DataTransformer", "analyze_threats", {
            "operations": [
                {
                    "type": "filter",
                    "config": {"field": "severity", "operator": ">=", "value": "medium"}
                }
            ]
        })
        
        # Create security events
        builder.add_node("SecurityServiceNode", "create_events", {
            "operation": "create_security_events"
        })
        
        # Connect nodes
        builder.add_connection("detect_threats", "result.data", "analyze_threats", "threats")
        builder.add_connection("analyze_threats", "result", "create_events", "threat_data")
        
        # Execute
        workflow = builder.build()
        results, _ = {{self.runner}}.execute_workflow(workflow, {}, "threat_detection")
        return results''',
            "demo_calls": '''
            # Configure security policies
            policies = {
                "password_policy": {
                    "min_length": 12,
                    "require_special": True
                },
                "session_policy": {
                    "timeout_minutes": 30,
                    "max_concurrent": 3
                }
            }
            results["policies"] = self.configure_security_policies(policies)
            
            # Detect threats
            results["threats"] = self.detect_security_threats()'''
        },
        "04_monitoring_analytics.py": {
            "class_name": "MonitoringAnalyticsWorkflow",
            "title": "Monitoring and Analytics Workflow",
            "description": "Provides system monitoring, user analytics, and reporting.",
            "default_user": "admin",
            "user_type": "admin",
            "methods": '''
    def collect_system_metrics(self) -> Dict[str, Any]:
        """Collect system performance metrics."""
        builder = {{self.runner}}.create_workflow("collect_metrics")
        
        # Get metrics via API
        builder.add_node("HTTPRequestNode", "get_metrics", {
            "url": f"{{self.api_base_url}}/api/v1/monitoring/metrics",
            "method": "GET",
            "headers": {
                "Authorization": f"Bearer {{self._get_auth_token()}}"
            }
        })
        
        # Process metrics
        builder.add_node("DataTransformer", "process_metrics", {
            "operations": [
                {
                    "type": "aggregate",
                    "config": {
                        "group_by": "metric_type",
                        "aggregations": {
                            "avg": "average",
                            "max": "maximum",
                            "min": "minimum"
                        }
                    }
                }
            ]
        })
        
        # Store in monitoring service
        builder.add_node("HTTPRequestNode", "store_metrics", {
            "url": f"{{self.api_base_url}}/api/v1/monitoring/store",
            "method": "POST",
            "headers": {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {{self._get_auth_token()}}"
            }
        })
        
        # Connect nodes
        builder.add_connection("get_metrics", "result.data", "process_metrics", "metrics")
        builder.add_connection("process_metrics", "result", "store_metrics", "body")
        
        # Execute
        workflow = builder.build()
        results, _ = {{self.runner}}.execute_workflow(workflow, {}, "collect_metrics")
        return results
    
    def generate_analytics_report(self, report_type: str = "user_activity") -> Dict[str, Any]:
        """Generate analytics reports."""
        builder = {{self.runner}}.create_workflow("generate_report")
        
        # Request report generation
        builder.add_node("HTTPRequestNode", "request_report", {
            "url": f"{{self.api_base_url}}/api/v1/analytics/reports/generate",
            "method": "POST",
            "headers": {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {{self._get_auth_token()}}"
            },
            "body": {
                "report_type": report_type,
                "format": "json",
                "include_visualizations": True
            }
        })
        
        # Transform report data
        builder.add_node("DataTransformer", "format_report", {
            "operations": [
                {
                    "type": "add_field",
                    "config": {
                        "field": "generated_at",
                        "value": datetime.now().isoformat()
                    }
                }
            ]
        })
        
        # Audit report generation
        builder.add_node("AuditLogNode", "audit_report", {
            "action": "ANALYTICS_REPORT_GENERATED",
            "resource_type": "report",
            "user_id": {{self.user_id}}
        })
        
        # Connect nodes
        builder.add_connection("request_report", "result.data", "format_report", "report_data")
        builder.add_connection("format_report", "result", "audit_report", "report_info")
        
        # Execute
        workflow = builder.build()
        results, _ = {{self.runner}}.execute_workflow(workflow, {"report_type": report_type}, "generate_report")
        return results''',
            "demo_calls": '''
            # Collect system metrics
            results["metrics"] = self.collect_system_metrics()
            
            # Generate analytics report
            results["report"] = self.generate_analytics_report("user_activity")'''
        },
        "05_backup_recovery.py": {
            "class_name": "BackupRecoveryWorkflow",
            "title": "Backup and Recovery Workflow",
            "description": "Handles system backups, disaster recovery, and data restoration.",
            "default_user": "admin",
            "user_type": "admin",
            "methods": '''
    def create_system_backup(self, backup_type: str = "full") -> Dict[str, Any]:
        """Create a system backup."""
        builder = {{self.runner}}.create_workflow("create_backup")
        
        # Initiate backup via API
        builder.add_node("HTTPRequestNode", "initiate_backup", {
            "url": f"{{self.api_base_url}}/api/v1/backup/create",
            "method": "POST",
            "headers": {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {{self._get_auth_token()}}"
            },
            "body": {
                "backup_type": backup_type,
                "include_audit_logs": True,
                "compress": True,
                "encrypt": True
            }
        })
        
        # Monitor backup progress
        builder.add_node("SwitchNode", "check_status", {
            "condition_field": "status",
            "cases": {
                "completed": "finalize_backup",
                "failed": "handle_failure",
                "in_progress": "wait_completion"
            }
        })
        
        # Finalize backup
        builder.add_node("ComplianceServiceNode", "finalize_backup", {
            "operation": "verify_backup_compliance"
        })
        
        # Audit backup creation
        builder.add_node("AuditLogNode", "audit_backup", {
            "action": "BACKUP_CREATED",
            "resource_type": "backup",
            "user_id": {{self.user_id}}
        })
        
        # Connect nodes
        builder.add_connection("initiate_backup", "result.data", "check_status", "backup_info")
        builder.add_connection("check_status", "completed", "finalize_backup", "backup_data")
        builder.add_connection("finalize_backup", "result", "audit_backup", "compliance_info")
        
        # Execute
        workflow = builder.build()
        results, _ = {{self.runner}}.execute_workflow(workflow, {"backup_type": backup_type}, "create_backup")
        return results
    
    def test_recovery_plan(self) -> Dict[str, Any]:
        """Test the disaster recovery plan."""
        builder = {{self.runner}}.create_workflow("test_recovery")
        
        # Run recovery test
        builder.add_node("HTTPRequestNode", "run_recovery_test", {
            "url": f"{{self.api_base_url}}/api/v1/backup/test-recovery",
            "method": "POST",
            "headers": {
                "Authorization": f"Bearer {{self._get_auth_token()}}"
            },
            "body": {
                "test_type": "partial",
                "target_environment": "test",
                "validate_data": True
            }
        })
        
        # Validate results
        builder.add_node("DataTransformer", "validate_recovery", {
            "operations": [
                {
                    "type": "validate",
                    "config": {
                        "rules": {
                            "success_rate": {"min": 95},
                            "data_integrity": {"equals": True}
                        }
                    }
                }
            ]
        })
        
        # Create recovery report
        builder.add_node("ComplianceServiceNode", "create_report", {
            "operation": "generate_recovery_report"
        })
        
        # Connect nodes
        builder.add_connection("run_recovery_test", "result.data", "validate_recovery", "test_results")
        builder.add_connection("validate_recovery", "result", "create_report", "validation_data")
        
        # Execute
        workflow = builder.build()
        results, _ = {{self.runner}}.execute_workflow(workflow, {}, "test_recovery")
        return results''',
            "demo_calls": '''
            # Create system backup
            results["backup"] = self.create_system_backup("incremental")
            
            # Test recovery plan
            results["recovery_test"] = self.test_recovery_plan()'''
        }
    },
    "manager_workflows": {
        "01_team_setup.py": {
            "class_name": "TeamSetupWorkflow",
            "title": "Team Setup Workflow",
            "description": "Sets up teams, departments, and organizational structure.",
            "default_user": "manager",
            "user_type": "manager",
            "methods": '''
    def create_team(self, team_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new team."""
        builder = {{self.runner}}.create_workflow("create_team")
        
        # Create team via API
        builder.add_node("HTTPRequestNode", "create_team_api", {
            "url": f"{{self.api_base_url}}/api/v1/teams",
            "method": "POST",
            "headers": {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {{self._get_auth_token()}}"
            },
            "body": team_data
        })
        
        # Set up team permissions
        builder.add_node("RoleServiceNode", "setup_permissions", {
            "operation": "create_team_role"
        })
        
        # Audit team creation
        builder.add_node("AuditLogNode", "audit_team", {
            "action": "TEAM_CREATED",
            "resource_type": "team",
            "user_id": {{self.user_id}}
        })
        
        # Connect nodes
        builder.add_connection("create_team_api", "result.data", "setup_permissions", "team_info")
        builder.add_connection("setup_permissions", "result", "audit_team", "permission_info")
        
        # Execute
        workflow = builder.build()
        results, _ = {{self.runner}}.execute_workflow(workflow, team_data, "create_team")
        return results
    
    def assign_team_members(self, team_id: str, member_ids: List[str]) -> Dict[str, Any]:
        """Assign members to a team."""
        builder = {{self.runner}}.create_workflow("assign_members")
        
        # Bulk assign members
        builder.add_node("HTTPRequestNode", "assign_members_api", {
            "url": f"{{self.api_base_url}}/api/v1/teams/{team_id}/members",
            "method": "POST",
            "headers": {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {{self._get_auth_token()}}"
            },
            "body": {
                "member_ids": member_ids,
                "notify_members": True
            }
        })
        
        # Update member roles
        builder.add_node("RoleServiceNode", "update_roles", {
            "operation": "assign_team_member_roles"
        })
        
        # Send notifications
        builder.add_node("HTTPRequestNode", "send_notifications", {
            "url": f"{{self.api_base_url}}/api/v1/notifications/send",
            "method": "POST",
            "headers": {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {{self._get_auth_token()}}"
            }
        })
        
        # Connect nodes
        builder.add_connection("assign_members_api", "result.data", "update_roles", "assignment_info")
        builder.add_connection("update_roles", "result", "send_notifications", "role_info")
        
        # Execute
        workflow = builder.build()
        results, _ = {{self.runner}}.execute_workflow(
            workflow, 
            {"team_id": team_id, "member_ids": member_ids}, 
            "assign_members"
        )
        return results''',
            "demo_calls": '''
            # Create a team
            team_data = {
                "name": "Development Team",
                "description": "Software development team",
                "department": "Engineering"
            }
            results["team"] = self.create_team(team_data)
            
            # Assign team members
            # results["assignments"] = self.assign_team_members("team_123", ["user_1", "user_2"])'''
        },
        "02_user_management.py": {
            "class_name": "ManagerUserManagementWorkflow",
            "title": "Manager User Management Workflow",
            "description": "Manages team members, profiles, and permissions.",
            "default_user": "manager",
            "user_type": "manager",
            "methods": '''
    def add_team_member(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new team member."""
        builder = {{self.runner}}.create_workflow("add_team_member")
        
        # Create user through service
        builder.add_node("UserServiceNode", "create_user", {
            "operation": "create_user"
        })
        
        # Assign to manager's team
        builder.add_node("HTTPRequestNode", "assign_to_team", {
            "url": f"{{self.api_base_url}}/api/v1/teams/my-team/members",
            "method": "POST",
            "headers": {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {{self._get_auth_token()}}"
            }
        })
        
        # Set up initial permissions
        builder.add_node("RoleServiceNode", "setup_permissions", {
            "operation": "assign_role"
        })
        
        # Connect nodes
        builder.add_connection("create_user", "user", "assign_to_team", "member_data")
        builder.add_connection("assign_to_team", "result.data", "setup_permissions", "assignment_info")
        
        # Execute
        workflow = builder.build()
        results, _ = {{self.runner}}.execute_workflow(workflow, user_data, "add_team_member")
        return results
    
    def update_member_profile(self, user_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update team member profile."""
        builder = {{self.runner}}.create_workflow("update_member")
        
        # Verify manager permissions
        builder.add_node("RoleServiceNode", "check_permissions", {
            "operation": "check_permission"
        })
        
        # Update user through service
        builder.add_node("UserServiceNode", "update_user", {
            "operation": "update_user"
        })
        
        # Audit the update
        builder.add_node("AuditLogNode", "audit_update", {
            "action": "TEAM_MEMBER_UPDATED",
            "resource_type": "user",
            "resource_id": user_id,
            "user_id": {{self.user_id}}
        })
        
        # Connect nodes
        builder.add_connection("check_permissions", "has_permission", "update_user", "permission_check")
        builder.add_connection("update_user", "user", "audit_update", "update_info")
        
        # Execute
        workflow = builder.build()
        results, _ = {{self.runner}}.execute_workflow(
            workflow,
            {"user_id": user_id, "updates": updates, "permission": "users.update"},
            "update_member"
        )
        return results''',
            "demo_calls": '''
            # Add a team member
            member_data = {
                "email": "new.member@company.com",
                "first_name": "New",
                "last_name": "Member",
                "department": "Engineering"
            }
            results["new_member"] = self.add_team_member(member_data)
            
            # Update member profile
            # results["update"] = self.update_member_profile("user_123", {"position": "Senior Developer"})'''
        },
        "03_permission_assignment.py": {
            "class_name": "PermissionAssignmentWorkflow", 
            "title": "Permission Assignment Workflow",
            "description": "Manages role and permission assignments for team members.",
            "default_user": "manager",
            "user_type": "manager",
            "methods": '''
    def assign_role_to_member(self, user_id: str, role: str) -> Dict[str, Any]:
        """Assign a role to a team member."""
        builder = {{self.runner}}.create_workflow("assign_role")
        
        # Verify manager can assign this role
        builder.add_node("RoleServiceNode", "verify_authority", {
            "operation": "check_permission"
        })
        
        # Assign role through service
        builder.add_node("RoleServiceNode", "assign_role", {
            "operation": "assign_role"
        })
        
        # Send notification
        builder.add_node("HTTPRequestNode", "notify_user", {
            "url": f"{{self.api_base_url}}/api/v1/notifications/send",
            "method": "POST",
            "headers": {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {{self._get_auth_token()}}"
            },
            "body": {
                "recipient_id": user_id,
                "type": "role_assigned",
                "template": "role_assignment"
            }
        })
        
        # Audit role assignment
        builder.add_node("AuditLogNode", "audit_assignment", {
            "action": "ROLE_ASSIGNED",
            "resource_type": "user",
            "resource_id": user_id,
            "user_id": {{self.user_id}}
        })
        
        # Connect nodes
        builder.add_connection("verify_authority", "has_permission", "assign_role", "authority_check")
        builder.add_connection("assign_role", "result", "notify_user", "role_info")
        builder.add_connection("notify_user", "result", "audit_assignment", "notification_info")
        
        # Execute
        workflow = builder.build()
        results, _ = {{self.runner}}.execute_workflow(
            workflow,
            {
                "user_id": user_id,
                "role": role,
                "permission": "roles.assign",
                "resource": f"team:{{{self.user_id}}}"
            },
            "assign_role"
        )
        return results
    
    def review_team_permissions(self) -> Dict[str, Any]:
        """Review and audit team permissions."""
        builder = {{self.runner}}.create_workflow("review_permissions")
        
        # Get team members
        builder.add_node("HTTPRequestNode", "get_team_members", {
            "url": f"{{self.api_base_url}}/api/v1/teams/my-team/members",
            "method": "GET",
            "headers": {
                "Authorization": f"Bearer {{self._get_auth_token()}}"
            }
        })
        
        # Analyze permissions
        builder.add_node("DataTransformer", "analyze_permissions", {
            "operations": [
                {
                    "type": "group",
                    "config": {
                        "by": "role",
                        "aggregate": "count"
                    }
                }
            ]
        })
        
        # Generate compliance report
        builder.add_node("ComplianceServiceNode", "compliance_check", {
            "operation": "verify_permission_compliance"
        })
        
        # Connect nodes
        builder.add_connection("get_team_members", "result.data", "analyze_permissions", "members")
        builder.add_connection("analyze_permissions", "result", "compliance_check", "permission_data")
        
        # Execute
        workflow = builder.build()
        results, _ = {{self.runner}}.execute_workflow(workflow, {}, "review_permissions")
        return results''',
            "demo_calls": '''
            # Assign role to team member
            # results["role_assignment"] = self.assign_role_to_member("user_123", "developer")
            
            # Review team permissions
            results["permission_review"] = self.review_team_permissions()'''
        },
        "04_reporting_analytics.py": {
            "class_name": "ReportingAnalyticsWorkflow",
            "title": "Reporting and Analytics Workflow",
            "description": "Generates team reports, analytics, and performance metrics.",
            "default_user": "manager",
            "user_type": "manager",
            "methods": '''
    def generate_team_report(self, report_type: str = "performance") -> Dict[str, Any]:
        """Generate team performance report."""
        builder = {{self.runner}}.create_workflow("generate_report")
        
        # Request team metrics
        builder.add_node("HTTPRequestNode", "get_team_metrics", {
            "url": f"{{self.api_base_url}}/api/v1/analytics/team-metrics",
            "method": "GET",
            "headers": {
                "Authorization": f"Bearer {{self._get_auth_token()}}"
            },
            "params": {
                "report_type": report_type,
                "period": "last_30_days"
            }
        })
        
        # Process metrics
        builder.add_node("DataTransformer", "process_metrics", {
            "operations": [
                {
                    "type": "calculate",
                    "config": {
                        "metrics": ["average", "trend", "comparison"]
                    }
                }
            ]
        })
        
        # Generate visual report
        builder.add_node("HTTPRequestNode", "generate_visuals", {
            "url": f"{{self.api_base_url}}/api/v1/reports/generate",
            "method": "POST",
            "headers": {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {{self._get_auth_token()}}"
            }
        })
        
        # Connect nodes
        builder.add_connection("get_team_metrics", "result.data", "process_metrics", "raw_metrics")
        builder.add_connection("process_metrics", "result", "generate_visuals", "body")
        
        # Execute
        workflow = builder.build()
        results, _ = {{self.runner}}.execute_workflow(workflow, {"report_type": report_type}, "generate_report")
        return results
    
    def analyze_team_productivity(self) -> Dict[str, Any]:
        """Analyze team productivity metrics."""
        builder = {{self.runner}}.create_workflow("analyze_productivity")
        
        # Get activity data
        builder.add_node("HTTPRequestNode", "get_activity_data", {
            "url": f"{{self.api_base_url}}/api/v1/analytics/team-activity",
            "method": "GET",
            "headers": {
                "Authorization": f"Bearer {{self._get_auth_token()}}"
            }
        })
        
        # Calculate productivity scores
        builder.add_node("DataTransformer", "calculate_scores", {
            "operations": [
                {
                    "type": "score",
                    "config": {
                        "metrics": ["efficiency", "collaboration", "output"]
                    }
                }
            ]
        })
        
        # Generate insights
        builder.add_node("HTTPRequestNode", "generate_insights", {
            "url": f"{{self.api_base_url}}/api/v1/analytics/insights",
            "method": "POST",
            "headers": {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {{self._get_auth_token()}}"
            }
        })
        
        # Connect nodes
        builder.add_connection("get_activity_data", "result.data", "calculate_scores", "activity_data")
        builder.add_connection("calculate_scores", "result", "generate_insights", "body")
        
        # Execute
        workflow = builder.build()
        results, _ = {{self.runner}}.execute_workflow(workflow, {}, "analyze_productivity")
        return results''',
            "demo_calls": '''
            # Generate team report
            results["team_report"] = self.generate_team_report("performance")
            
            # Analyze productivity
            results["productivity"] = self.analyze_team_productivity()'''
        },
        "05_approval_workflows.py": {
            "class_name": "ApprovalWorkflowsWorkflow",
            "title": "Approval Workflows",
            "description": "Manages approval processes for various team requests.",
            "default_user": "manager",
            "user_type": "manager",
            "methods": '''
    def review_access_request(self, request_id: str, decision: str = "approve") -> Dict[str, Any]:
        """Review and process access requests."""
        builder = {{self.runner}}.create_workflow("review_request")
        
        # Get request details
        builder.add_node("HTTPRequestNode", "get_request", {
            "url": f"{{self.api_base_url}}/api/v1/approvals/requests/{request_id}",
            "method": "GET",
            "headers": {
                "Authorization": f"Bearer {{self._get_auth_token()}}"
            }
        })
        
        # Make decision
        builder.add_node("SwitchNode", "process_decision", {
            "condition_field": "decision",
            "cases": {
                "approve": "approve_request",
                "deny": "deny_request",
                "defer": "defer_request"
            }
        })
        
        # Approve request
        builder.add_node("HTTPRequestNode", "approve_request", {
            "url": f"{{self.api_base_url}}/api/v1/approvals/requests/{request_id}/approve",
            "method": "POST",
            "headers": {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {{self._get_auth_token()}}"
            }
        })
        
        # Audit decision
        builder.add_node("AuditLogNode", "audit_decision", {
            "action": "APPROVAL_DECISION",
            "resource_type": "approval_request",
            "resource_id": request_id,
            "user_id": {{self.user_id}}
        })
        
        # Connect nodes
        builder.add_connection("get_request", "result.data", "process_decision", "request_data")
        builder.add_connection("process_decision", "approve", "approve_request", "approval_data")
        builder.add_connection("approve_request", "result", "audit_decision", "decision_result")
        
        # Execute
        workflow = builder.build()
        results, _ = {{self.runner}}.execute_workflow(
            workflow,
            {"request_id": request_id, "decision": decision},
            "review_request"
        )
        return results
    
    def setup_approval_workflow(self, workflow_config: Dict[str, Any]) -> Dict[str, Any]:
        """Set up a new approval workflow."""
        builder = {{self.runner}}.create_workflow("setup_approval")
        
        # Create workflow configuration
        builder.add_node("HTTPRequestNode", "create_workflow", {
            "url": f"{{self.api_base_url}}/api/v1/approvals/workflows",
            "method": "POST",
            "headers": {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {{self._get_auth_token()}}"
            },
            "body": workflow_config
        })
        
        # Configure notifications
        builder.add_node("HTTPRequestNode", "setup_notifications", {
            "url": f"{{self.api_base_url}}/api/v1/notifications/configure",
            "method": "POST",
            "headers": {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {{self._get_auth_token()}}"
            }
        })
        
        # Test workflow
        builder.add_node("DataTransformer", "validate_workflow", {
            "operations": [
                {
                    "type": "validate",
                    "config": {
                        "schema": "approval_workflow"
                    }
                }
            ]
        })
        
        # Connect nodes
        builder.add_connection("create_workflow", "result.data", "setup_notifications", "workflow_info")
        builder.add_connection("setup_notifications", "result", "validate_workflow", "config_data")
        
        # Execute
        workflow = builder.build()
        results, _ = {{self.runner}}.execute_workflow(
            workflow,
            workflow_config,
            "setup_approval"
        )
        return results''',
            "demo_calls": '''
            # Set up approval workflow
            workflow_config = {
                "name": "Resource Access Approval",
                "type": "sequential",
                "approvers": ["manager", "security_team"],
                "auto_approve_conditions": {
                    "risk_level": "low",
                    "resource_type": "read_only"
                }
            }
            results["approval_setup"] = self.setup_approval_workflow(workflow_config)
            
            # Review a request (would need actual request ID)
            # results["review"] = self.review_access_request("req_123", "approve")'''
        }
    },
    "user_workflows": {
        "01_profile_setup.py": {
            "class_name": "ProfileSetupWorkflow",
            "title": "Profile Setup Workflow",
            "description": "Manages user profile creation and updates.",
            "default_user": "user",
            "user_type": "user",
            "methods": '''
    def complete_profile(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Complete user profile setup."""
        builder = {{self.runner}}.create_workflow("complete_profile")
        
        # Update profile via API
        builder.add_node("HTTPRequestNode", "update_profile", {
            "url": f"{{self.api_base_url}}/api/v1/users/me/profile",
            "method": "PUT",
            "headers": {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {{self._get_auth_token()}}"
            },
            "body": profile_data
        })
        
        # Upload profile picture if provided
        builder.add_node("SwitchNode", "check_picture", {
            "condition_field": "has_picture",
            "cases": {
                "true": "upload_picture",
                "false": "skip_picture"
            }
        })
        
        # Validate profile completeness
        builder.add_node("DataTransformer", "validate_profile", {
            "operations": [
                {
                    "type": "validate",
                    "config": {
                        "required_fields": ["first_name", "last_name", "phone", "department"]
                    }
                }
            ]
        })
        
        # Connect nodes
        builder.add_connection("update_profile", "result.data", "check_picture", "profile_info")
        builder.add_connection("check_picture", "skip_picture", "validate_profile", "profile_data")
        
        # Execute
        workflow = builder.build()
        results, _ = {{self.runner}}.execute_workflow(
            workflow,
            profile_data,
            "complete_profile"
        )
        return results
    
    def update_preferences(self, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Update user preferences."""
        builder = {{self.runner}}.create_workflow("update_preferences")
        
        # Update preferences
        builder.add_node("HTTPRequestNode", "update_prefs", {
            "url": f"{{self.api_base_url}}/api/v1/users/me/preferences",
            "method": "PUT",
            "headers": {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {{self._get_auth_token()}}"
            },
            "body": preferences
        })
        
        # Apply UI theme if changed
        builder.add_node("DataTransformer", "apply_theme", {
            "operations": [
                {
                    "type": "transform",
                    "config": {
                        "apply": "theme_settings"
                    }
                }
            ]
        })
        
        # Save to local storage
        builder.add_node("PythonCodeNode", "save_local", {
            "name": "save_preferences_locally",
            "code": """
# Save preferences to local storage for offline access
import json
local_prefs = {
    "theme": preferences.get("theme", "light"),
    "language": preferences.get("language", "en"),
    "notifications": preferences.get("notifications", True)
}
result = {"result": {"saved_locally": True, "preferences": local_prefs}}
"""
        })
        
        # Connect nodes
        builder.add_connection("update_prefs", "result.data", "apply_theme", "preference_data")
        builder.add_connection("apply_theme", "result", "save_local", "preferences")
        
        # Execute
        workflow = builder.build()
        results, _ = {{self.runner}}.execute_workflow(
            workflow,
            preferences,
            "update_preferences"
        )
        return results''',
            "demo_calls": '''
            # Complete profile
            profile_data = {
                "phone": "+1-555-0123",
                "department": "Engineering",
                "position": "Software Developer",
                "bio": "Passionate about building great software",
                "has_picture": False
            }
            results["profile"] = self.complete_profile(profile_data)
            
            # Update preferences
            preferences = {
                "theme": "dark",
                "language": "en",
                "notifications": {
                    "email": True,
                    "browser": True,
                    "mobile": False
                }
            }
            results["preferences"] = self.update_preferences(preferences)'''
        },
        "02_security_settings.py": {
            "class_name": "SecuritySettingsWorkflow",
            "title": "Security Settings Workflow",
            "description": "Manages personal security settings and authentication.",
            "default_user": "user",
            "user_type": "user",
            "methods": '''
    def change_password(self, current_password: str, new_password: str) -> Dict[str, Any]:
        """Change user password."""
        builder = {{self.runner}}.create_workflow("change_password")
        
        # Validate current password
        builder.add_node("HTTPRequestNode", "validate_current", {
            "url": f"{{self.api_base_url}}/api/v1/auth/validate-password",
            "method": "POST",
            "headers": {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {{self._get_auth_token()}}"
            },
            "body": {
                "current_password": current_password
            }
        })
        
        # Check password policy
        builder.add_node("SecurityServiceNode", "check_policy", {
            "operation": "validate_password_policy"
        })
        
        # Update password
        builder.add_node("HTTPRequestNode", "update_password", {
            "url": f"{{self.api_base_url}}/api/v1/users/me/password",
            "method": "PUT",
            "headers": {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {{self._get_auth_token()}}"
            },
            "body": {
                "new_password": new_password
            }
        })
        
        # Revoke existing sessions
        builder.add_node("SecurityServiceNode", "revoke_sessions", {
            "operation": "revoke_sessions"
        })
        
        # Connect nodes
        builder.add_connection("validate_current", "result", "check_policy", "validation_result")
        builder.add_connection("check_policy", "result", "update_password", "policy_check")
        builder.add_connection("update_password", "result", "revoke_sessions", "password_update")
        
        # Execute
        workflow = builder.build()
        results, _ = {{self.runner}}.execute_workflow(
            workflow,
            {
                "password": new_password,
                "user_id": {{self.user_id}},
                "reason": "password_change"
            },
            "change_password"
        )
        return results
    
    def enable_two_factor(self) -> Dict[str, Any]:
        """Enable two-factor authentication."""
        builder = {{self.runner}}.create_workflow("enable_2fa")
        
        # Generate 2FA secret
        builder.add_node("HTTPRequestNode", "generate_secret", {
            "url": f"{{self.api_base_url}}/api/v1/security/2fa/generate",
            "method": "POST",
            "headers": {
                "Authorization": f"Bearer {{self._get_auth_token()}}"
            }
        })
        
        # Create QR code
        builder.add_node("DataTransformer", "create_qr", {
            "operations": [
                {
                    "type": "generate",
                    "config": {
                        "type": "qr_code",
                        "data_field": "secret"
                    }
                }
            ]
        })
        
        # Save backup codes
        builder.add_node("HTTPRequestNode", "save_backup_codes", {
            "url": f"{{self.api_base_url}}/api/v1/security/2fa/backup-codes",
            "method": "POST",
            "headers": {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {{self._get_auth_token()}}"
            }
        })
        
        # Connect nodes
        builder.add_connection("generate_secret", "result.data", "create_qr", "secret_data")
        builder.add_connection("create_qr", "result", "save_backup_codes", "qr_info")
        
        # Execute
        workflow = builder.build()
        results, _ = {{self.runner}}.execute_workflow(workflow, {}, "enable_2fa")
        return results''',
            "demo_calls": '''
            # Enable two-factor authentication
            results["2fa"] = self.enable_two_factor()
            
            # Note: Password change requires actual credentials
            # results["password"] = self.change_password("current", "new")'''
        },
        "03_data_management.py": {
            "class_name": "DataManagementWorkflow",
            "title": "Data Management Workflow",
            "description": "Manages personal data, exports, and privacy settings.",
            "default_user": "user",
            "user_type": "user",
            "methods": '''
    def export_personal_data(self, format: str = "json") -> Dict[str, Any]:
        """Export all personal data (GDPR compliance)."""
        builder = {{self.runner}}.create_workflow("export_data")
        
        # Request data export
        builder.add_node("ComplianceServiceNode", "request_export", {
            "operation": "export_user_data"
        })
        
        # Monitor export progress
        builder.add_node("HTTPRequestNode", "check_progress", {
            "url": f"{{self.api_base_url}}/api/v1/exports/status",
            "method": "GET",
            "headers": {
                "Authorization": f"Bearer {{self._get_auth_token()}}"
            }
        })
        
        # Download when ready
        builder.add_node("SwitchNode", "check_ready", {
            "condition_field": "status",
            "cases": {
                "ready": "download_export",
                "processing": "wait_export",
                "failed": "handle_error"
            }
        })
        
        # Connect nodes
        builder.add_connection("request_export", "export_id", "check_progress", "export_id")
        builder.add_connection("check_progress", "result.data", "check_ready", "export_status")
        
        # Execute
        workflow = builder.build()
        results, _ = {{self.runner}}.execute_workflow(
            workflow,
            {
                "user_id": {{self.user_id}},
                "format": format,
                "categories": ["personal_data", "activity_data", "preferences_data"]
            },
            "export_data"
        )
        return results
    
    def delete_activity_data(self, data_type: str = "search_history") -> Dict[str, Any]:
        """Delete specific activity data."""
        builder = {{self.runner}}.create_workflow("delete_data")
        
        # Verify user authorization
        builder.add_node("HTTPRequestNode", "verify_auth", {
            "url": f"{{self.api_base_url}}/api/v1/auth/verify",
            "method": "POST",
            "headers": {
                "Authorization": f"Bearer {{self._get_auth_token()}}"
            }
        })
        
        # Delete specified data
        builder.add_node("HTTPRequestNode", "delete_data", {
            "url": f"{{self.api_base_url}}/api/v1/users/me/data/{data_type}",
            "method": "DELETE",
            "headers": {
                "Authorization": f"Bearer {{self._get_auth_token()}}"
            }
        })
        
        # Audit deletion
        builder.add_node("AuditLogNode", "audit_deletion", {
            "action": "USER_DATA_DELETED",
            "resource_type": "user_data",
            "resource_id": data_type,
            "user_id": {{self.user_id}}
        })
        
        # Connect nodes
        builder.add_connection("verify_auth", "result", "delete_data", "auth_result")
        builder.add_connection("delete_data", "result", "audit_deletion", "deletion_info")
        
        # Execute
        workflow = builder.build()
        results, _ = {{self.runner}}.execute_workflow(
            workflow,
            {"data_type": data_type},
            "delete_data"
        )
        return results''',
            "demo_calls": '''
            # Export personal data
            results["export"] = self.export_personal_data("json")
            
            # Delete activity data
            results["deletion"] = self.delete_activity_data("search_history")'''
        },
        "04_privacy_controls.py": {
            "class_name": "PrivacyControlsWorkflow",
            "title": "Privacy Controls Workflow",
            "description": "Manages privacy settings and data sharing preferences.",
            "default_user": "user",
            "user_type": "user",
            "methods": '''
    def update_privacy_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Update privacy settings."""
        builder = {{self.runner}}.create_workflow("update_privacy")
        
        # Update privacy preferences
        builder.add_node("HTTPRequestNode", "update_settings", {
            "url": f"{{self.api_base_url}}/api/v1/users/me/privacy",
            "method": "PUT",
            "headers": {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {{self._get_auth_token()}}"
            },
            "body": settings
        })
        
        # Apply visibility changes
        builder.add_node("DataTransformer", "apply_visibility", {
            "operations": [
                {
                    "type": "apply",
                    "config": {
                        "visibility_rules": settings.get("visibility", {})
                    }
                }
            ]
        })
        
        # Update consent records
        builder.add_node("ComplianceServiceNode", "update_consent", {
            "operation": "update_consent_records"
        })
        
        # Connect nodes
        builder.add_connection("update_settings", "result.data", "apply_visibility", "privacy_data")
        builder.add_connection("apply_visibility", "result", "update_consent", "visibility_info")
        
        # Execute
        workflow = builder.build()
        results, _ = {{self.runner}}.execute_workflow(
            workflow,
            settings,
            "update_privacy"
        )
        return results
    
    def manage_data_sharing(self, sharing_config: Dict[str, Any]) -> Dict[str, Any]:
        """Manage data sharing permissions."""
        builder = {{self.runner}}.create_workflow("manage_sharing")
        
        # Update sharing preferences
        builder.add_node("HTTPRequestNode", "update_sharing", {
            "url": f"{{self.api_base_url}}/api/v1/users/me/sharing",
            "method": "PUT",
            "headers": {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {{self._get_auth_token()}}"
            },
            "body": sharing_config
        })
        
        # Revoke existing shares if needed
        builder.add_node("SwitchNode", "check_revoke", {
            "condition_field": "revoke_existing",
            "cases": {
                "true": "revoke_shares",
                "false": "skip_revoke"
            }
        })
        
        # Audit sharing changes
        builder.add_node("AuditLogNode", "audit_sharing", {
            "action": "DATA_SHARING_UPDATED",
            "resource_type": "privacy_settings",
            "user_id": {{self.user_id}}
        })
        
        # Connect nodes
        builder.add_connection("update_sharing", "result.data", "check_revoke", "sharing_info")
        builder.add_connection("check_revoke", "skip_revoke", "audit_sharing", "sharing_result")
        
        # Execute
        workflow = builder.build()
        results, _ = {{self.runner}}.execute_workflow(
            workflow,
            sharing_config,
            "manage_sharing"
        )
        return results''',
            "demo_calls": '''
            # Update privacy settings
            privacy_settings = {
                "profile_visibility": "connections_only",
                "activity_visibility": "private",
                "search_indexing": False,
                "data_analytics": False
            }
            results["privacy"] = self.update_privacy_settings(privacy_settings)
            
            # Manage data sharing
            sharing_config = {
                "share_with_partners": False,
                "share_for_research": False,
                "share_anonymized": True,
                "revoke_existing": False
            }
            results["sharing"] = self.manage_data_sharing(sharing_config)'''
        },
        "05_support_requests.py": {
            "class_name": "SupportRequestsWorkflow",
            "title": "Support Requests Workflow",
            "description": "Manages support tickets and help requests.",
            "default_user": "user",
            "user_type": "user",
            "methods": '''
    def create_support_ticket(self, ticket_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new support ticket."""
        builder = {{self.runner}}.create_workflow("create_ticket")
        
        # Validate ticket data
        builder.add_node("DataTransformer", "validate_ticket", {
            "operations": [
                {
                    "type": "validate",
                    "config": {
                        "required": ["subject", "description", "category"]
                    }
                }
            ]
        })
        
        # Create ticket via API
        builder.add_node("HTTPRequestNode", "create_ticket", {
            "url": f"{{self.api_base_url}}/api/v1/support/tickets",
            "method": "POST",
            "headers": {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {{self._get_auth_token()}}"
            },
            "body": ticket_data
        })
        
        # Attach system info
        builder.add_node("DataTransformer", "attach_info", {
            "operations": [
                {
                    "type": "enrich",
                    "config": {
                        "add_fields": {
                            "user_agent": "browser_info",
                            "timestamp": "current_time",
                            "user_context": "session_data"
                        }
                    }
                }
            ]
        })
        
        # Send confirmation
        builder.add_node("HTTPRequestNode", "send_confirmation", {
            "url": f"{{self.api_base_url}}/api/v1/notifications/send",
            "method": "POST",
            "headers": {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {{self._get_auth_token()}}"
            }
        })
        
        # Connect nodes
        builder.add_connection("validate_ticket", "result", "create_ticket", "validated_data")
        builder.add_connection("create_ticket", "result.data", "attach_info", "ticket_info")
        builder.add_connection("attach_info", "result", "send_confirmation", "enriched_ticket")
        
        # Execute
        workflow = builder.build()
        results, _ = {{self.runner}}.execute_workflow(
            workflow,
            ticket_data,
            "create_ticket"
        )
        return results
    
    def check_ticket_status(self, ticket_id: str) -> Dict[str, Any]:
        """Check support ticket status."""
        builder = {{self.runner}}.create_workflow("check_status")
        
        # Get ticket status
        builder.add_node("HTTPRequestNode", "get_status", {
            "url": f"{{self.api_base_url}}/api/v1/support/tickets/{ticket_id}",
            "method": "GET",
            "headers": {
                "Authorization": f"Bearer {{self._get_auth_token()}}"
            }
        })
        
        # Check for updates
        builder.add_node("DataTransformer", "check_updates", {
            "operations": [
                {
                    "type": "compare",
                    "config": {
                        "field": "last_updated",
                        "with": "last_checked"
                    }
                }
            ]
        })
        
        # Format response
        builder.add_node("DataTransformer", "format_response", {
            "operations": [
                {
                    "type": "format",
                    "config": {
                        "template": "ticket_status",
                        "include_history": True
                    }
                }
            ]
        })
        
        # Connect nodes
        builder.add_connection("get_status", "result.data", "check_updates", "ticket_data")
        builder.add_connection("check_updates", "result", "format_response", "update_info")
        
        # Execute
        workflow = builder.build()
        results, _ = {{self.runner}}.execute_workflow(
            workflow,
            {"ticket_id": ticket_id},
            "check_status"
        )
        return results''',
            "demo_calls": '''
            # Create support ticket
            ticket_data = {
                "subject": "Cannot access team resources",
                "description": "I'm unable to access shared team documents since yesterday.",
                "category": "access_issue",
                "priority": "medium"
            }
            results["ticket"] = self.create_support_ticket(ticket_data)
            
            # Check ticket status (would need actual ticket ID)
            # results["status"] = self.check_ticket_status("ticket_123")'''
        }
    }
}


def create_refactored_workflow(workflow_path: str, spec: Dict[str, Any]) -> str:
    """
    Create a refactored workflow file.
    
    Args:
        workflow_path: Path to the original workflow
        spec: Refactoring specification
        
    Returns:
        Path to the refactored file
    """
    # Generate refactored content
    content = REFACTORED_WORKFLOW_TEMPLATE.format(**spec)
    
    # Create refactored filename
    base_name = os.path.basename(workflow_path)
    refactored_name = base_name.replace('.py', '_refactored.py')
    refactored_path = os.path.join(os.path.dirname(workflow_path), refactored_name)
    
    # Write refactored file
    with open(refactored_path, 'w') as f:
        f.write(content)
    
    # Make executable
    os.chmod(refactored_path, 0o755)
    
    return refactored_path


def main():
    """
    Main refactoring function.
    """
    print("🔧 Refactoring User Management Workflows...")
    print("=" * 70)
    
    base_dir = os.path.join(os.path.dirname(__file__))
    refactored_count = 0
    
    # Process each workflow type
    for workflow_type, workflows in WORKFLOW_SPECS.items():
        print(f"\n📁 Processing {workflow_type}...")
        
        workflow_dir = os.path.join(base_dir, workflow_type, "scripts")
        
        for filename, spec in workflows.items():
            workflow_path = os.path.join(workflow_dir, filename)
            
            if os.path.exists(workflow_path):
                print(f"  ✅ Refactoring {filename}...")
                refactored_path = create_refactored_workflow(workflow_path, spec)
                print(f"     Created: {os.path.basename(refactored_path)}")
                refactored_count += 1
            else:
                print(f"  ❌ Not found: {filename}")
    
    print(f"\n{'='*70}")
    print(f"✅ Refactored {refactored_count} workflows")
    print("\nNext steps:")
    print("1. Test refactored workflows: python <workflow>_refactored.py --test")
    print("2. Start API server: python -m apps.user_management.api")
    print("3. Run full workflows: python <workflow>_refactored.py")
    print("4. Remove original workflows once refactored versions are validated")
    

if __name__ == "__main__":
    main()