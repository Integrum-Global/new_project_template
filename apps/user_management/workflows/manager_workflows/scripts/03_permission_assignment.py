#!/usr/bin/env python3
"""
Manager Workflow: Permission Assignment and Role Management

This workflow handles permission and role management including:
- Standard role assignment and management
- Temporary access grants
- Role hierarchy management
- Permission request processing
"""

import sys
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

# Add shared utilities to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))

from workflow_runner import WorkflowRunner, create_user_context_node, create_validation_node


class PermissionAssignmentWorkflow:
    """
    Complete permission assignment workflow for department managers.
    """
    
    def __init__(self, manager_user_id: str = "manager"):
        """
        Initialize the permission assignment workflow.
        
        Args:
            manager_user_id: ID of the manager performing operations
        """
        self.manager_user_id = manager_user_id
        self.runner = WorkflowRunner(
            user_type="manager",
            user_id=manager_user_id,
            enable_debug=True,
            enable_audit=False,  # Disable for testing
            enable_monitoring=True
        )
    
    def assign_standard_roles(self, user_id: str, role_assignment: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assign standard roles to team members.
        
        Args:
            user_id: ID of the team member
            role_assignment: Role assignment details
            
        Returns:
            Role assignment results
        """
        print(f"👤 Assigning roles to team member: {user_id}")
        
        builder = self.runner.create_workflow("standard_role_assignment")
        
        # Role validation
        validation_rules = {
            "roles": {"required": True, "type": list, "min_length": 1},
            "effective_date": {"required": False, "type": str},
            "justification": {"required": True, "type": str, "min_length": 10}
        }
        
        builder.add_node("PythonCodeNode", "validate_role_assignment", 
                        create_validation_node(validation_rules))
        
        # Standard role assignment process
        builder.add_node("PythonCodeNode", "assign_roles", {
            "name": "assign_standard_roles_to_member",
            "code": f"""
from datetime import datetime, timedelta
import random
import string

def generate_id():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=12))

# Current user role information
current_user_roles = {{
    "user_id": "{user_id}",
    "current_roles": ["employee"],
    "department": "Engineering",
    "manager_id": "{self.manager_user_id}",
    "last_role_change": "2024-01-15",
    "active_permissions": ["basic_access", "team_collaboration"]
}}

# Role assignment request
assignment_request = {role_assignment}
requested_roles = assignment_request.get("roles", [])
effective_date = assignment_request.get("effective_date", datetime.now().strftime("%Y-%m-%d"))
justification = assignment_request.get("justification", "Manager assignment")

# Available roles for department managers to assign
assignable_roles = {{
    "developer": {{
        "permissions": ["code_repository", "development_tools", "build_systems"],
        "prerequisites": ["employee"],
        "approval_level": "manager"
    }},
    "senior_developer": {{
        "permissions": ["code_review", "deploy_staging", "mentor_junior", "architecture_input"],
        "prerequisites": ["employee", "developer"],
        "approval_level": "manager"
    }},
    "tech_lead": {{
        "permissions": ["team_coordination", "project_planning", "performance_reviews"],
        "prerequisites": ["employee", "developer", "senior_developer"],
        "approval_level": "manager"
    }},
    "mentor": {{
        "permissions": ["training_delivery", "onboarding_support", "knowledge_sharing"],
        "prerequisites": ["employee"],
        "approval_level": "manager"
    }},
    "specialist": {{
        "permissions": ["domain_expertise", "consultation", "technical_guidance"],
        "prerequisites": ["employee", "developer"],
        "approval_level": "manager"
    }}
}}

# Process role assignments
role_assignments = []
assignment_errors = []

for role in requested_roles:
    if role in assignable_roles:
        role_info = assignable_roles[role]
        
        # Check prerequisites
        missing_prereqs = [req for req in role_info["prerequisites"] 
                          if req not in current_user_roles["current_roles"] + requested_roles]
        
        if not missing_prereqs:
            assignment = {{
                "role": role,
                "permissions": role_info["permissions"],
                "assigned_date": effective_date,
                "assigned_by": "{self.manager_user_id}",
                "justification": justification,
                "status": "approved"
            }}
            role_assignments.append(assignment)
        else:
            assignment_errors.append({{
                "role": role,
                "error": f"Missing prerequisites: {{missing_prereqs}}",
                "status": "rejected"
            }})
    else:
        assignment_errors.append({{
            "role": role,
            "error": "Role not available for manager assignment",
            "status": "requires_admin_approval"
        }})

# Updated user profile
updated_roles = current_user_roles["current_roles"] + [a["role"] for a in role_assignments]
updated_permissions = current_user_roles["active_permissions"].copy()
for assignment in role_assignments:
    updated_permissions.extend(assignment["permissions"])

# Remove duplicates while preserving order
updated_permissions = list(dict.fromkeys(updated_permissions))

result = {{
    "result": {{
        "roles_assigned": len(role_assignments),
        "roles_rejected": len(assignment_errors),
        "successful_assignments": role_assignments,
        "assignment_errors": assignment_errors,
        "updated_roles": updated_roles,
        "updated_permissions": updated_permissions,
        "effective_date": effective_date
    }}
}}
"""
        })
        
        # Generate role assignment notifications
        builder.add_node("PythonCodeNode", "generate_role_notifications", {
            "name": "generate_role_assignment_notifications",
            "code": """
# Generate notifications for role assignments
role_assignment_data = role_assignment_result.get("successful_assignments", [])
assignment_errors = role_assignment_result.get("assignment_errors", [])

# User notification
user_notification = {
    "recipient": role_assignment_result.get("updated_roles", []),
    "type": "role_assignment",
    "subject": "New Role Assignment",
    "message": f"You have been assigned {len(role_assignment_data)} new role(s)",
    "roles_assigned": [a["role"] for a in role_assignment_data],
    "effective_date": role_assignment_result.get("effective_date"),
    "assigned_by": role_assignment_data[0]["assigned_by"] if role_assignment_data else "manager",
    "action_required": "Review new permissions and complete any required training"
}

# HR notification
hr_notification = {
    "type": "role_change_notification",
    "employee_id": role_assignment_result.get("updated_roles", []),
    "roles_added": [a["role"] for a in role_assignment_data],
    "manager_id": role_assignment_data[0]["assigned_by"] if role_assignment_data else "manager",
    "effective_date": role_assignment_result.get("effective_date"),
    "training_required": len(role_assignment_data) > 0
}

# IT notification for system access
it_notification = {
    "type": "permission_update_required",
    "user_id": role_assignment_result.get("updated_roles", []),
    "new_permissions": [perm for assignment in role_assignment_data for perm in assignment["permissions"]],
    "access_provisioning": {
        "immediate_access": ["basic_tools", "collaboration_platforms"],
        "approval_required": ["admin_systems", "financial_data"],
        "training_required": ["security_tools", "compliance_systems"]
    }
}

# Audit trail
audit_record = {
    "event_type": "role_assignment",
    "timestamp": datetime.now().isoformat(),
    "performed_by": role_assignment_data[0]["assigned_by"] if role_assignment_data else "manager",
    "target_user": role_assignment_result.get("updated_roles", []),
    "roles_assigned": len(role_assignment_data),
    "roles_rejected": len(assignment_errors),
    "compliance_status": "compliant",
    "approval_level": "manager_approved"
}

result = {
    "result": {
        "notifications_generated": 3,
        "user_notification": user_notification,
        "hr_notification": hr_notification, 
        "it_notification": it_notification,
        "audit_logged": True,
        "audit_record": audit_record
    }
}
"""
        })
        
        # Connect role assignment nodes
        builder.add_connection("validate_role_assignment", "result", "assign_roles", "validation_result")
        builder.add_connection("assign_roles", "result.result", "generate_role_notifications", "role_assignment_result")
        
        # Execute workflow
        workflow = builder.build()
        results, execution_id = self.runner.execute_workflow(
            workflow, role_assignment, "standard_role_assignment"
        )
        
        return results
    
    def grant_temporary_access(self, user_id: str, temporary_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Grant temporary access permissions to team members.
        
        Args:
            user_id: ID of the team member
            temporary_request: Temporary access request details
            
        Returns:
            Temporary access grant results
        """
        print(f"⏰ Granting temporary access to team member: {user_id}")
        
        builder = self.runner.create_workflow("temporary_access_grant")
        
        # Temporary access processing
        builder.add_node("PythonCodeNode", "process_temporary_access", {
            "name": "process_temporary_access_request",
            "code": f"""
import random
import string

def generate_id():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=12))

# Temporary access request details
temp_request = {temporary_request}
user_id = "{user_id}"
manager_id = "{self.manager_user_id}"

# Temporary access configuration
temp_access_config = {{
    "request_id": generate_id(),
    "user_id": user_id,
    "requested_permissions": temp_request.get("permissions", []),
    "duration_days": temp_request.get("duration_days", 7),
    "justification": temp_request.get("justification", "Temporary project access"),
    "project_code": temp_request.get("project_code", ""),
    "requested_by": manager_id,
    "request_date": datetime.now().isoformat()
}}

# Calculate expiry date
expiry_date = datetime.now() + timedelta(days=temp_access_config["duration_days"])
temp_access_config["expiry_date"] = expiry_date.isoformat()

# Temporary access policies
temp_access_policies = {{
    "max_duration_days": 30,  # Manager can approve up to 30 days
    "auto_revoke": True,
    "require_justification": True,
    "monitoring_level": "enhanced",
    "approval_required": {{
        "admin_systems": temp_access_config["duration_days"] > 7,
        "financial_data": True,  # Always requires additional approval
        "customer_data": temp_access_config["duration_days"] > 3,
        "production_systems": temp_access_config["duration_days"] > 1
    }}
}}

# Validate temporary access request
validation_results = []
approved_permissions = []
requires_additional_approval = []

for permission in temp_access_config["requested_permissions"]:
    if permission in temp_access_policies["approval_required"]:
        if temp_access_policies["approval_required"][permission]:
            requires_additional_approval.append(permission)
            validation_results.append({{
                "permission": permission,
                "status": "requires_admin_approval",
                "reason": "Sensitive system access requires additional approval"
            }})
        else:
            approved_permissions.append(permission)
            validation_results.append({{
                "permission": permission,
                "status": "manager_approved",
                "reason": "Within manager approval authority"
            }})
    else:
        approved_permissions.append(permission)
        validation_results.append({{
            "permission": permission,
            "status": "manager_approved",
            "reason": "Standard temporary access"
        }})

# Temporary access grant
temp_access_grant = {{
    "grant_id": generate_id(),
    "user_id": user_id,
    "granted_permissions": approved_permissions,
    "pending_permissions": requires_additional_approval,
    "effective_date": datetime.now().isoformat(),
    "expiry_date": temp_access_config["expiry_date"],
    "auto_revoke_enabled": temp_access_policies["auto_revoke"],
    "monitoring_level": temp_access_policies["monitoring_level"],
    "granted_by": manager_id
}}

result = {{
    "result": {{
        "temporary_access_processed": True,
        "permissions_approved": len(approved_permissions),
        "permissions_pending": len(requires_additional_approval),
        "temp_access_grant": temp_access_grant,
        "validation_results": validation_results,
        "requires_additional_approval": len(requires_additional_approval) > 0
    }}
}}
"""
        })
        
        # Set up monitoring and auto-revocation
        builder.add_node("PythonCodeNode", "setup_temp_access_monitoring", {
            "name": "setup_temporary_access_monitoring",
            "code": """
# Set up monitoring for temporary access
temp_grant = temp_access_processing.get("temp_access_grant", {})

# Monitoring configuration
monitoring_config = {
    "access_tracking": {
        "log_all_actions": True,
        "session_monitoring": True,
        "permission_usage_tracking": True,
        "anomaly_detection": True
    },
    "auto_revocation": {
        "enabled": temp_grant.get("auto_revoke_enabled", True),
        "expiry_date": temp_grant.get("expiry_date"),
        "warning_days_before": 2,
        "revocation_method": "automatic",
        "notification_schedule": ["7_days_before", "1_day_before", "on_expiry"]
    },
    "compliance_monitoring": {
        "access_pattern_analysis": True,
        "policy_violation_detection": True,
        "usage_reporting": True,
        "audit_trail": "enhanced"
    }
}

# Scheduled tasks for temporary access
scheduled_tasks = [
    {
        "task": "expiry_warning",
        "schedule_date": (datetime.now() + timedelta(days=temp_grant.get("duration_days", 7) - 2)).isoformat(),
        "action": "send_expiry_warning",
        "recipients": ["user", "manager"]
    },
    {
        "task": "auto_revoke",
        "schedule_date": temp_grant.get("expiry_date"),
        "action": "revoke_temporary_access",
        "permissions": temp_grant.get("granted_permissions", [])
    },
    {
        "task": "compliance_report",
        "schedule_date": temp_grant.get("expiry_date"),
        "action": "generate_usage_report",
        "include_analytics": True
    }
]

# Access usage policies
usage_policies = {
    "session_limits": {
        "max_concurrent_sessions": 2,
        "session_timeout_minutes": 30,
        "idle_timeout_minutes": 10
    },
    "activity_restrictions": {
        "allowed_hours": "business_hours",  # 9-5 unless emergency
        "weekend_access": False,
        "holiday_access": False,
        "location_restrictions": ["office", "vpn"]
    },
    "violation_responses": {
        "unusual_activity": "alert_manager",
        "policy_violation": "suspend_access",
        "security_concern": "immediate_revoke"
    }
}

result = {
    "result": {
        "monitoring_configured": True,
        "auto_revocation_scheduled": True,
        "compliance_monitoring_enabled": True,
        "scheduled_tasks": len(scheduled_tasks),
        "usage_policies_applied": True,
        "monitoring_level": "enhanced"
    }
}
"""
        })
        
        # Connect temporary access nodes
        builder.add_connection("process_temporary_access", "result.result", "setup_temp_access_monitoring", "temp_access_processing")
        
        # Execute workflow
        workflow = builder.build()
        results, execution_id = self.runner.execute_workflow(
            workflow, temporary_request, "temporary_access_grant"
        )
        
        return results
    
    def manage_role_hierarchy(self, department_id: str, hierarchy_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Manage role hierarchy and delegation configurations.
        
        Args:
            department_id: ID of the department
            hierarchy_config: Hierarchy configuration details
            
        Returns:
            Role hierarchy management results
        """
        print(f"🏗️ Managing role hierarchy for department: {department_id}")
        
        builder = self.runner.create_workflow("role_hierarchy_management")
        
        # Role hierarchy setup
        builder.add_node("PythonCodeNode", "setup_role_hierarchy", {
            "name": "setup_department_role_hierarchy",
            "code": f"""
# Department role hierarchy configuration
department_id = "{department_id}"
hierarchy_config = {hierarchy_config}

# Define role hierarchy structure
role_hierarchy = {{
    "department_head": {{
        "level": 1,
        "reports_to": "executive_team",
        "can_manage": ["manager", "senior_specialist", "team_lead"],
        "delegation_authority": ["budget_approval", "hiring_decisions", "strategic_planning"],
        "approval_limits": {{"budget": 50000, "headcount": 10}}
    }},
    "manager": {{
        "level": 2,
        "reports_to": "department_head",
        "can_manage": ["team_lead", "senior_developer", "developer", "employee"],
        "delegation_authority": ["team_assignments", "performance_reviews", "role_assignments"],
        "approval_limits": {{"budget": 10000, "headcount": 5}}
    }},
    "team_lead": {{
        "level": 3,
        "reports_to": "manager",
        "can_manage": ["senior_developer", "developer", "employee"],
        "delegation_authority": ["task_assignments", "code_reviews", "mentoring"],
        "approval_limits": {{"budget": 2000, "headcount": 0}}
    }},
    "senior_developer": {{
        "level": 4,
        "reports_to": "team_lead",
        "can_manage": ["developer", "junior_developer"],
        "delegation_authority": ["technical_guidance", "code_reviews", "training"],
        "approval_limits": {{"budget": 500, "headcount": 0}}
    }},
    "developer": {{
        "level": 5,
        "reports_to": "senior_developer",
        "can_manage": ["junior_developer", "intern"],
        "delegation_authority": ["task_guidance", "peer_reviews"],
        "approval_limits": {{"budget": 0, "headcount": 0}}
    }}
}}

# Team lead assignments
team_leads = hierarchy_config.get("team_leads", [])
team_lead_assignments = []

for lead_config in team_leads:
    assignment = {{
        "user_id": lead_config.get("user_id"),
        "team_name": lead_config.get("team_name"),
        "team_members": lead_config.get("team_members", []),
        "responsibilities": [
            "Daily team coordination",
            "Sprint planning participation", 
            "Code review oversight",
            "Team member mentoring",
            "Performance feedback"
        ],
        "authority_level": role_hierarchy["team_lead"]["delegation_authority"],
        "reporting_manager": "{self.manager_user_id}"
    }}
    team_lead_assignments.append(assignment)

# Delegation configurations
delegation_rules = {{
    "approval_delegation": {{
        "enabled": True,
        "delegation_levels": {{
            "expense_approval": {{
                "manager_limit": 10000,
                "team_lead_limit": 2000,
                "senior_dev_limit": 500
            }},
            "time_off_approval": {{
                "manager": "unlimited",
                "team_lead": "up_to_5_days",
                "senior_dev": "peer_coverage_only"
            }}
        }}
    }},
    "escalation_procedures": {{
        "no_response_hours": 24,
        "escalation_chain": ["team_lead", "manager", "department_head"],
        "emergency_approver": "{self.manager_user_id}"
    }}
}}

result = {{
    "result": {{
        "hierarchy_configured": True,
        "hierarchy_levels": len(role_hierarchy),
        "team_leads_assigned": len(team_lead_assignments),
        "delegation_rules_set": True,
        "escalation_configured": True,
        "role_hierarchy": role_hierarchy,
        "team_assignments": team_lead_assignments
    }}
}}
"""
        })
        
        # Configure approval chains
        builder.add_node("PythonCodeNode", "configure_approval_chains", {
            "name": "configure_hierarchy_approval_chains",
            "code": """
# Configure approval chains based on hierarchy
hierarchy_data = hierarchy_setup.get("role_hierarchy", {})
team_assignments = hierarchy_setup.get("team_assignments", [])

# Approval workflow configurations
approval_workflows = []

# Access request approval chain
access_approval_chain = {
    "workflow_type": "access_request",
    "approval_levels": [
        {
            "level": 1,
            "approver_role": "direct_manager",
            "criteria": "standard_access",
            "auto_approve_threshold": "low_risk",
            "sla_hours": 24
        },
        {
            "level": 2, 
            "approver_role": "department_manager",
            "criteria": "elevated_access",
            "requires_justification": True,
            "sla_hours": 48
        },
        {
            "level": 3,
            "approver_role": "department_head",
            "criteria": "admin_access",
            "requires_security_review": True,
            "sla_hours": 72
        }
    ],
    "escalation_rules": {
        "no_response_escalation": True,
        "escalation_hours": 48,
        "weekend_handling": "hold_until_business_hours"
    }
}
approval_workflows.append(access_approval_chain)

# Role assignment approval chain
role_approval_chain = {
    "workflow_type": "role_assignment",
    "approval_levels": [
        {
            "level": 1,
            "approver_role": "direct_manager",
            "criteria": "department_roles",
            "can_approve": ["developer", "senior_developer", "specialist"],
            "sla_hours": 24
        },
        {
            "level": 2,
            "approver_role": "department_head", 
            "criteria": "leadership_roles",
            "can_approve": ["team_lead", "manager", "architect"],
            "requires_hr_consultation": True,
            "sla_hours": 72
        }
    ]
}
approval_workflows.append(role_approval_chain)

# Emergency access approval
emergency_approval_chain = {
    "workflow_type": "emergency_access",
    "approval_levels": [
        {
            "level": 1,
            "approver_role": "on_call_manager",
            "criteria": "emergency_justification",
            "max_duration_hours": 4,
            "requires_post_review": True,
            "sla_minutes": 30
        }
    ],
    "post_approval_requirements": {
        "incident_report": True,
        "security_review": True,
        "access_revocation": "automatic"
    }
}
approval_workflows.append(emergency_approval_chain)

# Performance review approval (for promotions)
performance_approval_chain = {
    "workflow_type": "performance_promotion",
    "approval_levels": [
        {
            "level": 1,
            "approver_role": "direct_manager",
            "criteria": "performance_rating",
            "minimum_rating": "meets_expectations",
            "sla_hours": 48
        },
        {
            "level": 2,
            "approver_role": "department_head",
            "criteria": "promotion_readiness",
            "requires_360_review": True,
            "budget_impact_check": True,
            "sla_hours": 96
        }
    ]
}
approval_workflows.append(performance_approval_chain)

result = {
    "result": {
        "approval_chains_configured": len(approval_workflows),
        "workflow_types": [w["workflow_type"] for w in approval_workflows],
        "escalation_enabled": True,
        "emergency_procedures": True,
        "sla_compliance_monitoring": True
    }
}
"""
        })
        
        # Connect hierarchy management nodes
        builder.add_connection("setup_role_hierarchy", "result.result", "configure_approval_chains", "hierarchy_setup")
        
        # Execute workflow
        workflow = builder.build()
        results, execution_id = self.runner.execute_workflow(
            workflow, hierarchy_config, "role_hierarchy_management"
        )
        
        return results
    
    def process_permission_requests(self, requests: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Process multiple permission requests from team members.
        
        Args:
            requests: List of permission requests to process
            
        Returns:
            Permission request processing results
        """
        print(f"📋 Processing {len(requests)} permission requests...")
        
        builder = self.runner.create_workflow("permission_request_processing")
        
        # Batch process permission requests
        builder.add_node("PythonCodeNode", "batch_process_requests", {
            "name": "batch_process_permission_requests",
            "code": f"""
# Process multiple permission requests
requests_list = {requests}
manager_id = "{self.manager_user_id}"

processed_requests = []
approval_decisions = []
escalation_required = []

# Processing criteria
approval_criteria = {{
    "auto_approve": {{
        "standard_tools": ["slack", "jira", "confluence"],
        "development_tools": ["github", "docker", "ci_cd"],
        "max_duration_days": 7
    }},
    "manager_review": {{
        "sensitive_systems": ["production", "database", "customer_data"],
        "elevated_permissions": ["admin", "sudo", "root"],
        "long_duration": lambda days: days > 7
    }},
    "escalation_required": {{
        "financial_systems": ["accounting", "payroll", "billing"],
        "security_systems": ["firewall", "vpn", "security_logs"],
        "compliance_data": ["audit_logs", "compliance_reports"]
    }}
}}

for i, request in enumerate(requests_list):
    request_id = f"REQ{{{i+1:03d}}}"
    user_id = request.get("user_id", f"user_{i}")
    permissions = request.get("permissions", [])
    justification = request.get("justification", "")
    duration_days = request.get("duration_days", 30)
    
    # Evaluate request
    decision_type = "pending"
    decision_reason = ""
    
    # Check for auto-approval
    if all(perm in approval_criteria["auto_approve"]["standard_tools"] + 
           approval_criteria["auto_approve"]["development_tools"] for perm in permissions):
        if duration_days <= approval_criteria["auto_approve"]["max_duration_days"]:
            decision_type = "auto_approved"
            decision_reason = "Standard tools within approval limits"
    
    # Check for escalation requirements
    elif any(perm in approval_criteria["escalation_required"]["financial_systems"] + 
             approval_criteria["escalation_required"]["security_systems"] + 
             approval_criteria["escalation_required"]["compliance_data"] for perm in permissions):
        decision_type = "escalation_required"
        decision_reason = "Requires security/compliance approval"
        escalation_required.append(request_id)
    
    # Manager review required
    else:
        decision_type = "manager_review"
        decision_reason = "Requires manager evaluation"
    
    # Process decision
    processed_request = {{
        "request_id": request_id,
        "user_id": user_id,
        "permissions": permissions,
        "duration_days": duration_days,
        "justification": justification,
        "decision_type": decision_type,
        "decision_reason": decision_reason,
        "processed_by": manager_id,
        "processed_at": datetime.now().isoformat(),
        "status": "approved" if decision_type == "auto_approved" else "pending"
    }}
    processed_requests.append(processed_request)
    
    # Create approval decision record
    approval_decision = {{
        "request_id": request_id,
        "decision": "approve" if decision_type == "auto_approved" else "review",
        "approver": manager_id,
        "approval_level": "manager",
        "conditions": [] if decision_type == "auto_approved" else ["security_review"],
        "expiry_date": (datetime.now() + timedelta(days=duration_days)).strftime("%Y-%m-%d") if decision_type == "auto_approved" else None
    }}
    approval_decisions.append(approval_decision)

# Summary statistics
processing_summary = {{
    "total_requests": len(requests_list),
    "auto_approved": len([r for r in processed_requests if r["decision_type"] == "auto_approved"]),
    "requiring_review": len([r for r in processed_requests if r["decision_type"] == "manager_review"]), 
    "requiring_escalation": len(escalation_required),
    "processing_rate": len(processed_requests) / len(requests_list) * 100 if requests_list else 0
}}

result = {{
    "result": {{
        "requests_processed": len(processed_requests),
        "processing_summary": processing_summary,
        "processed_requests": processed_requests,
        "approval_decisions": approval_decisions,
        "escalation_required": escalation_required
    }}
}}
"""
        })
        
        # Generate batch notifications
        builder.add_node("PythonCodeNode", "generate_batch_notifications", {
            "name": "generate_batch_processing_notifications",
            "code": """
# Generate notifications for batch processed requests
processing_results = batch_processing.get("processed_requests", [])
approval_decisions = batch_processing.get("approval_decisions", [])
escalation_list = batch_processing.get("escalation_required", [])

# User notifications
user_notifications = []
for request in processing_results:
    notification = {
        "recipient": request["user_id"],
        "type": "permission_request_update",
        "request_id": request["request_id"],
        "status": request["status"],
        "message": f"Your permission request has been {request['status']}",
        "next_steps": {
            "approved": "Access will be provisioned within 2 hours",
            "pending": "Request is under manager review",
            "escalated": "Request forwarded to security team"
        }.get(request["status"], "Please contact your manager")
    }
    user_notifications.append(notification)

# Manager summary notification
manager_summary = {
    "type": "batch_processing_summary",
    "total_processed": len(processing_results),
    "auto_approved": len([r for r in processing_results if r["decision_type"] == "auto_approved"]),
    "requiring_attention": len([r for r in processing_results if r["decision_type"] == "manager_review"]),
    "escalated": len(escalation_list),
    "processing_efficiency": batch_processing.get("processing_summary", {}).get("processing_rate", 0)
}

# IT provisioning notifications
it_notifications = []
for request in [r for r in processing_results if r["status"] == "approved"]:
    it_notification = {
        "type": "access_provisioning",
        "user_id": request["user_id"],
        "permissions": request["permissions"],
        "duration_days": request["duration_days"],
        "priority": "standard",
        "auto_revoke": True
    }
    it_notifications.append(it_notification)

# Escalation notifications
escalation_notifications = []
for request_id in escalation_list:
    request = next((r for r in processing_results if r["request_id"] == request_id), None)
    if request:
        escalation_notification = {
            "type": "permission_escalation",
            "request_id": request_id,
            "user_id": request["user_id"],
            "permissions": request["permissions"],
            "justification": request["justification"],
            "escalated_by": request["processed_by"],
            "urgency": "standard"
        }
        escalation_notifications.append(escalation_notification)

result = {
    "result": {
        "notifications_generated": len(user_notifications) + len(it_notifications) + len(escalation_notifications),
        "user_notifications": len(user_notifications),
        "it_notifications": len(it_notifications), 
        "escalation_notifications": len(escalation_notifications),
        "manager_summary": manager_summary,
        "batch_processing_complete": True
    }
}
"""
        })
        
        # Connect batch processing nodes
        builder.add_connection("batch_process_requests", "result.result", "generate_batch_notifications", "batch_processing")
        
        # Execute workflow
        workflow = builder.build()
        results, execution_id = self.runner.execute_workflow(
            workflow, {"requests": requests}, "permission_request_processing"
        )
        
        return results
    
    def run_comprehensive_permission_demo(self) -> Dict[str, Any]:
        """
        Run a comprehensive demonstration of all permission assignment operations.
        
        Returns:
            Complete demonstration results
        """
        print("🚀 Starting Comprehensive Permission Assignment Demonstration...")
        print("=" * 70)
        
        demo_results = {}
        
        try:
            # 1. Assign standard roles
            print("\n1. Assigning Standard Roles...")
            role_assignment = {
                "roles": ["developer", "mentor"],
                "effective_date": "2024-07-01",
                "justification": "Promotion based on excellent performance and mentoring capabilities"
            }
            demo_results["role_assignment"] = self.assign_standard_roles("user_001", role_assignment)
            
            # 2. Grant temporary access
            print("\n2. Granting Temporary Access...")
            temporary_request = {
                "permissions": ["deploy_staging", "admin_panel"],
                "duration_days": 5,
                "justification": "Emergency production debugging access",
                "project_code": "PROJ-2024-001"
            }
            demo_results["temporary_access"] = self.grant_temporary_access("user_002", temporary_request)
            
            # 3. Manage role hierarchy
            print("\n3. Managing Role Hierarchy...")
            hierarchy_config = {
                "team_leads": [
                    {
                        "user_id": "user_003",
                        "team_name": "Frontend Team",
                        "team_members": ["user_004", "user_005", "user_006"]
                    },
                    {
                        "user_id": "user_007",
                        "team_name": "Backend Team", 
                        "team_members": ["user_008", "user_009", "user_010"]
                    }
                ]
            }
            demo_results["hierarchy_management"] = self.manage_role_hierarchy("dept_engineering", hierarchy_config)
            
            # 4. Process permission requests
            print("\n4. Processing Permission Requests...")
            permission_requests = [
                {
                    "user_id": "user_011",
                    "permissions": ["jira", "confluence"],
                    "duration_days": 90,
                    "justification": "New team member onboarding"
                },
                {
                    "user_id": "user_012",
                    "permissions": ["production_access", "database_admin"],
                    "duration_days": 1,
                    "justification": "Emergency production issue resolution"
                },
                {
                    "user_id": "user_013",
                    "permissions": ["github", "docker", "ci_cd"],
                    "duration_days": 30,
                    "justification": "Development environment setup"
                }
            ]
            demo_results["permission_processing"] = self.process_permission_requests(permission_requests)
            
            # Print comprehensive summary
            self.print_permission_summary(demo_results)
            
            return demo_results
            
        except Exception as e:
            print(f"❌ Permission assignment demonstration failed: {str(e)}")
            raise
    
    def print_permission_summary(self, results: Dict[str, Any]):
        """
        Print a comprehensive permission assignment summary.
        
        Args:
            results: Permission assignment results from all workflows
        """
        print("\n" + "=" * 70)
        print("PERMISSION ASSIGNMENT DEMONSTRATION COMPLETE")
        print("=" * 70)
        
        # Role assignment summary
        role_result = results.get("role_assignment", {}).get("assign_roles", {}).get("result", {}).get("result", {})
        print(f"🎭 Roles: {role_result.get('roles_assigned', 0)} roles assigned successfully")
        
        # Temporary access summary
        temp_result = results.get("temporary_access", {}).get("process_temporary_access", {}).get("result", {}).get("result", {})
        print(f"⏰ Temporary: {temp_result.get('permissions_approved', 0)} permissions granted temporarily")
        
        # Hierarchy management summary
        hierarchy_result = results.get("hierarchy_management", {}).get("setup_role_hierarchy", {}).get("result", {}).get("result", {})
        print(f"🏗️ Hierarchy: {hierarchy_result.get('team_leads_assigned', 0)} team leads assigned")
        
        # Permission processing summary
        processing_result = results.get("permission_processing", {}).get("batch_process_requests", {}).get("result", {}).get("result", {})
        print(f"📋 Requests: {processing_result.get('requests_processed', 0)} permission requests processed")
        
        print("\n🎉 All permission assignment operations completed successfully!")
        print("=" * 70)
        
        # Print execution statistics
        self.runner.print_stats()


def test_workflow(test_params: Optional[Dict[str, Any]] = None) -> bool:
    """
    Test the permission assignment workflow.
    
    Args:
        test_params: Optional test parameters
        
    Returns:
        True if test passes, False otherwise
    """
    try:
        print("🧪 Testing Permission Assignment Workflow...")
        
        # Create test workflow
        permission_mgmt = PermissionAssignmentWorkflow("test_manager")
        
        # Test role assignment
        test_assignment = {
            "roles": ["developer"],
            "justification": "Test role assignment"
        }
        
        result = permission_mgmt.assign_standard_roles("test_user", test_assignment)
        if not result.get("assign_roles", {}).get("result", {}).get("result", {}).get("roles_assigned", 0) > 0:
            return False
        
        print("✅ Permission assignment workflow test passed")
        return True
        
    except Exception as e:
        print(f"❌ Permission assignment workflow test failed: {str(e)}")
        return False


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        # Run test
        success = test_workflow()
        sys.exit(0 if success else 1)
    else:
        # Run comprehensive demonstration
        permission_mgmt = PermissionAssignmentWorkflow()
        
        try:
            results = permission_mgmt.run_comprehensive_permission_demo()
            print("🎉 Permission assignment demonstration completed successfully!")
        except Exception as e:
            print(f"❌ Demonstration failed: {str(e)}")
            sys.exit(1)