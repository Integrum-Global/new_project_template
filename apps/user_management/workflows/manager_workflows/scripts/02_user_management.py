#!/usr/bin/env python3
"""
Manager Workflow: Team Member Administration

This workflow handles team member administration including:
- User profile management for team members
- Access review and modification
- Performance tracking and monitoring
- Role changes and permissions
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

# Add shared utilities to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "shared"))

from workflow_runner import (
    WorkflowRunner,
    create_user_context_node,
    create_validation_node,
)


class UserManagementWorkflow:
    """
    Complete user management workflow for department managers.
    """

    def __init__(self, manager_user_id: str = "manager"):
        """
        Initialize the user management workflow.

        Args:
            manager_user_id: ID of the manager performing operations
        """
        self.manager_user_id = manager_user_id
        self.runner = WorkflowRunner(
            user_type="manager",
            user_id=manager_user_id,
            enable_debug=True,
            enable_audit=False,  # Disable for testing
            enable_monitoring=True,
        )

    def manage_team_member_profile(
        self, user_id: str, updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Manage team member profile information.

        Args:
            user_id: ID of the team member
            updates: Profile updates to apply

        Returns:
            Profile management results
        """
        print(f"👤 Managing profile for team member: {user_id}")

        builder = self.runner.create_workflow("team_member_profile_management")

        # Profile validation
        validation_rules = {
            "email": {"required": False, "type": str, "min_length": 5},
            "first_name": {"required": False, "type": str, "min_length": 1},
            "last_name": {"required": False, "type": str, "min_length": 1},
            "department": {"required": False, "type": str, "min_length": 2},
            "position": {"required": False, "type": str},
        }

        builder.add_node(
            "PythonCodeNode",
            "validate_profile_updates",
            create_validation_node(validation_rules),
        )

        # Profile management operations
        builder.add_node(
            "PythonCodeNode",
            "manage_profile",
            {
                "name": "manage_team_member_profile",
                "code": f"""
from datetime import datetime, timedelta
import random
import string

def generate_id():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=12))

# Current team member information (simulated lookup)
current_profile = {{
    "id": "{user_id}",
    "email": f"member_{user_id}@company.com",
    "first_name": "John",
    "last_name": "Doe",
    "department": "Engineering",
    "position": "Software Developer",
    "manager_id": "{self.manager_user_id}",
    "last_updated": datetime.now().isoformat(),
    "status": "active"
}}

# Apply updates from manager
profile_updates = {updates}
updated_fields = []
change_log = []

for field, new_value in profile_updates.items():
    if field in current_profile and current_profile[field] != new_value:
        old_value = current_profile[field]
        current_profile[field] = new_value
        updated_fields.append(field)

        change_log.append({{
            "field": field,
            "old_value": old_value,
            "new_value": new_value,
            "updated_by": "{self.manager_user_id}",
            "timestamp": datetime.now().isoformat()
        }})

# Contact information management
contact_info = {{
    "primary_email": current_profile.get("email"),
    "work_phone": profile_updates.get("work_phone", "+1-555-0123"),
    "emergency_contact": profile_updates.get("emergency_contact", "Jane Doe"),
    "emergency_phone": profile_updates.get("emergency_phone", "+1-555-0124")
}}

# Employment data tracking
employment_data = {{
    "employee_id": f"EMP{{current_profile['id'][:8]}}",
    "department": current_profile["department"],
    "position": current_profile["position"],
    "manager": "{self.manager_user_id}",
    "start_date": profile_updates.get("start_date", "2024-01-15"),
    "employment_status": current_profile["status"],
    "performance_review_date": (datetime.now() + timedelta(days=90)).strftime("%Y-%m-%d")
}}

result = {{
    "result": {{
        "profile_updated": len(updated_fields) > 0,
        "fields_updated": updated_fields,
        "change_log": change_log,
        "contact_info": contact_info,
        "employment_data": employment_data,
        "manager_approval": "completed",
        "next_review_date": employment_data["performance_review_date"]
    }}
}}
""",
            },
        )

        # Track profile changes
        builder.add_node(
            "PythonCodeNode",
            "track_profile_changes",
            {
                "name": "track_team_member_changes",
                "code": """
# Track and audit profile changes
tracking_info = {
    "change_tracking": {
        "total_changes": len(profile_management.get("change_log", [])),
        "last_change_date": datetime.now().isoformat(),
        "manager_id": profile_management.get("employment_data", {}).get("manager"),
        "approval_required": False,  # Manager has authority
        "notification_sent": True
    },
    "audit_trail": {
        "action": "profile_update",
        "performed_by": profile_management.get("employment_data", {}).get("manager"),
        "user_affected": profile_management.get("employment_data", {}).get("employee_id"),
        "fields_modified": profile_management.get("fields_updated", []),
        "timestamp": datetime.now().isoformat(),
        "compliance_check": "passed"
    },
    "notifications": {
        "employee_notification": {
            "type": "profile_update",
            "message": "Your profile has been updated by your manager",
            "details": profile_management.get("fields_updated", []),
            "action_required": False
        },
        "hr_notification": {
            "type": "employee_profile_change",
            "employee_id": profile_management.get("employment_data", {}).get("employee_id"),
            "changes": len(profile_management.get("change_log", [])),
            "manager_approval": True
        }
    }
}

result = {
    "result": {
        "tracking_completed": True,
        "audit_logged": True,
        "notifications_sent": 2,
        "compliance_verified": True,
        "change_tracking": tracking_info["change_tracking"]
    }
}
""",
            },
        )

        # Connect profile management nodes
        builder.add_connection(
            "validate_profile_updates", "result", "manage_profile", "validation_result"
        )
        builder.add_connection(
            "manage_profile",
            "result.result",
            "track_profile_changes",
            "profile_management",
        )

        # Execute workflow
        workflow = builder.build()
        results, execution_id = self.runner.execute_workflow(
            workflow, updates, "team_member_profile_management"
        )

        return results

    def review_and_modify_access(
        self, user_id: str, access_request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Review and modify team member access permissions.

        Args:
            user_id: ID of the team member
            access_request: Access modification request

        Returns:
            Access modification results
        """
        print(f"🔐 Reviewing access for team member: {user_id}")

        builder = self.runner.create_workflow("access_review_modification")

        # Access review process
        builder.add_node(
            "PythonCodeNode",
            "review_current_access",
            {
                "name": "review_team_member_access",
                "code": f"""
from datetime import datetime, timedelta

# Review current access permissions
current_access = {{
    "user_id": "{user_id}",
    "current_roles": ["employee", "developer"],
    "current_permissions": [
        "basic_access", "code_repository", "development_tools",
        "team_collaboration", "project_access"
    ],
    "system_access": [
        "jira", "confluence", "slack", "github", "docker_registry"
    ],
    "access_review_date": datetime.now().isoformat(),
    "last_review_by": "{self.manager_user_id}",
    "compliance_status": "compliant"
}}

# Requested access changes
access_request_data = {access_request}
requested_changes = []

# Analyze requested permissions
for permission in access_request_data.get("permissions_to_add", []):
    requested_changes.append({{
        "action": "add",
        "permission": permission,
        "justification": access_request_data.get("justification", "Manager approval"),
        "risk_level": "low",  # Manager pre-approved
        "approval_status": "approved"
    }})

for permission in access_request_data.get("permissions_to_remove", []):
    requested_changes.append({{
        "action": "remove",
        "permission": permission,
        "justification": "Access cleanup",
        "risk_level": "none",
        "approval_status": "approved"
    }})

# Temporary access handling
temporary_access = access_request_data.get("temporary_access", {{}})
if temporary_access:
    temp_access = {{
        "permissions": temporary_access.get("permissions", []),
        "duration_days": temporary_access.get("duration_days", 30),
        "expiry_date": (datetime.now() + timedelta(days=temporary_access.get("duration_days", 30))).strftime("%Y-%m-%d"),
        "auto_revoke": True,
        "justification": temporary_access.get("justification", "Temporary project access")
    }}
    requested_changes.append({{
        "action": "temp_grant",
        "details": temp_access,
        "approval_status": "approved"
    }})

result = {{
    "result": {{
        "access_reviewed": True,
        "current_access": current_access,
        "requested_changes": len(requested_changes),
        "all_approved": True,
        "compliance_verified": True,
        "review_timestamp": datetime.now().isoformat()
    }}
}}
""",
            },
        )

        # Apply access modifications
        builder.add_node(
            "PythonCodeNode",
            "apply_access_changes",
            {
                "name": "apply_access_modifications",
                "code": """
# Apply approved access changes
access_review = access_review_result.get("current_access", {})
changes_applied = []
failed_changes = []

# Process each requested change
for change in access_review_result.get("requested_changes", []):
    try:
        if change["approval_status"] == "approved":
            change_record = {
                "action": change["action"],
                "permission": change.get("permission", ""),
                "applied_at": datetime.now().isoformat(),
                "applied_by": access_review["last_review_by"],
                "status": "completed"
            }

            # Handle temporary access
            if change["action"] == "temp_grant":
                temp_details = change["details"]
                change_record.update({
                    "expiry_date": temp_details["expiry_date"],
                    "auto_revoke_enabled": temp_details["auto_revoke"]
                })

            changes_applied.append(change_record)
        else:
            failed_changes.append({
                "change": change,
                "reason": "Not approved by manager"
            })
    except Exception as e:
        failed_changes.append({
            "change": change,
            "reason": f"Application error: {str(e)}"
        })

# Updated access summary
updated_access = {
    "user_id": access_review["user_id"],
    "roles": access_review["current_roles"],
    "permissions": access_review["current_permissions"],
    "changes_applied": len(changes_applied),
    "last_modified": datetime.now().isoformat(),
    "modified_by": access_review["last_review_by"],
    "compliance_status": "verified"
}

result = {
    "result": {
        "changes_applied": len(changes_applied),
        "changes_failed": len(failed_changes),
        "access_updated": True,
        "updated_access": updated_access,
        "audit_logged": True,
        "notifications_sent": True
    }
}
""",
            },
        )

        # Connect access review nodes
        builder.add_connection(
            "review_current_access",
            "result.result",
            "apply_access_changes",
            "access_review_result",
        )

        # Execute workflow
        workflow = builder.build()
        results, execution_id = self.runner.execute_workflow(
            workflow, access_request, "access_review_modification"
        )

        return results

    def track_team_performance(
        self, department_id: str, tracking_period: str = "monthly"
    ) -> Dict[str, Any]:
        """
        Track and monitor team performance metrics.

        Args:
            department_id: ID of the department to track
            tracking_period: Period for tracking (daily, weekly, monthly)

        Returns:
            Performance tracking results
        """
        print(f"📊 Tracking team performance for department: {department_id}")

        builder = self.runner.create_workflow("team_performance_tracking")

        # Collect performance data
        builder.add_node(
            "PythonCodeNode",
            "collect_performance_data",
            {
                "name": "collect_team_performance_metrics",
                "code": f"""
# Collect comprehensive team performance data
tracking_period = "{tracking_period}"
department_id = "{department_id}"

# Team member performance metrics
team_members = [
    {{
        "user_id": "user_001",
        "name": "John Doe",
        "login_frequency": 4.8,  # daily average
        "system_usage_hours": 7.2,
        "task_completion_rate": 92,
        "quality_score": 4.2,
        "collaboration_score": 85
    }},
    {{
        "user_id": "user_002",
        "name": "Jane Smith",
        "login_frequency": 4.9,
        "system_usage_hours": 6.8,
        "task_completion_rate": 94,
        "quality_score": 4.5,
        "collaboration_score": 90
    }},
    {{
        "user_id": "user_003",
        "name": "Bob Johnson",
        "login_frequency": 4.2,
        "system_usage_hours": 6.5,
        "task_completion_rate": 88,
        "quality_score": 3.9,
        "collaboration_score": 78
    }}
]

# Department-level metrics
department_metrics = {{
    "department_id": department_id,
    "tracking_period": tracking_period,
    "total_team_members": len(team_members),
    "average_login_frequency": sum(m["login_frequency"] for m in team_members) / len(team_members),
    "average_system_usage": sum(m["system_usage_hours"] for m in team_members) / len(team_members),
    "average_task_completion": sum(m["task_completion_rate"] for m in team_members) / len(team_members),
    "average_quality_score": sum(m["quality_score"] for m in team_members) / len(team_members),
    "average_collaboration": sum(m["collaboration_score"] for m in team_members) / len(team_members)
}}

# Performance trends
performance_trends = {{
    "productivity_trend": "increasing",  # Compared to previous period
    "engagement_trend": "stable",
    "quality_trend": "improving",
    "collaboration_trend": "stable",
    "areas_for_improvement": [
        "Task completion rate consistency",
        "Quality score variance reduction"
    ]
}}

result = {{
    "result": {{
        "data_collected": True,
        "team_members_tracked": len(team_members),
        "department_metrics": department_metrics,
        "individual_metrics": team_members,
        "performance_trends": performance_trends,
        "tracking_timestamp": datetime.now().isoformat()
    }}
}}
""",
            },
        )

        # Generate performance insights
        builder.add_node(
            "PythonCodeNode",
            "generate_performance_insights",
            {
                "name": "generate_team_performance_insights",
                "code": """
# Generate actionable performance insights
performance_data = performance_tracking.get("department_metrics", {})
individual_data = performance_tracking.get("individual_metrics", [])

# Identify top performers
top_performers = sorted(individual_data,
                       key=lambda x: (x["task_completion_rate"] + x["quality_score"] * 20 + x["collaboration_score"]) / 3,
                       reverse=True)[:2]

# Identify areas needing attention
attention_needed = [member for member in individual_data
                   if member["task_completion_rate"] < 90 or member["quality_score"] < 4.0]

# Performance insights
insights = {
    "team_strengths": [
        f"High average task completion rate: {performance_data.get('average_task_completion', 0):.1f}%",
        f"Good collaboration scores: {performance_data.get('average_collaboration', 0):.1f}/100",
        f"Consistent system usage: {performance_data.get('average_system_usage', 0):.1f} hours/day"
    ],
    "improvement_opportunities": [
        "Standardize quality processes for consistency",
        "Implement peer mentoring for lower performers",
        "Increase collaboration tools usage"
    ],
    "recommended_actions": [
        {
            "action": "one_on_one_meetings",
            "target": [member["name"] for member in attention_needed],
            "timeline": "within_1_week",
            "priority": "high"
        },
        {
            "action": "team_training",
            "topic": "quality_assurance",
            "timeline": "within_2_weeks",
            "priority": "medium"
        },
        {
            "action": "recognition_program",
            "target": [member["name"] for member in top_performers],
            "timeline": "immediate",
            "priority": "low"
        }
    ]
}

# Performance report summary
report_summary = {
    "overall_performance": "good",  # excellent, good, needs_improvement, poor
    "team_size": len(individual_data),
    "high_performers": len(top_performers),
    "needs_attention": len(attention_needed),
    "trend_direction": "positive",
    "manager_action_items": len(insights["recommended_actions"])
}

result = {
    "result": {
        "insights_generated": True,
        "performance_insights": insights,
        "report_summary": report_summary,
        "action_items": len(insights["recommended_actions"]),
        "insights_timestamp": datetime.now().isoformat()
    }
}
""",
            },
        )

        # Connect performance tracking nodes
        builder.add_connection(
            "collect_performance_data",
            "result.result",
            "generate_performance_insights",
            "performance_tracking",
        )

        # Execute workflow
        workflow = builder.build()
        results, execution_id = self.runner.execute_workflow(
            workflow,
            {"department_id": department_id, "period": tracking_period},
            "team_performance_tracking",
        )

        return results

    def handle_role_changes(
        self, user_id: str, role_change_request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handle role changes and promotions for team members.

        Args:
            user_id: ID of the team member
            role_change_request: Role change details

        Returns:
            Role change results
        """
        print(f"🎯 Processing role change for team member: {user_id}")

        builder = self.runner.create_workflow("role_change_management")

        # Role change processing
        builder.add_node(
            "PythonCodeNode",
            "process_role_change",
            {
                "name": "process_team_member_role_change",
                "code": f"""
import random
import string

def generate_id():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=12))

# Current role information
current_role_info = {{
    "user_id": "{user_id}",
    "current_roles": ["employee", "developer"],
    "current_position": "Software Developer",
    "department": "Engineering",
    "manager_id": "{self.manager_user_id}",
    "last_role_change": "2024-01-15",
    "tenure_months": 6
}}

# Role change request details
role_request = {role_change_request}
change_type = role_request.get("change_type", "promotion")  # promotion, lateral, demotion, transfer

# Process role change
role_change_details = {{
    "change_id": generate_id(),
    "user_id": "{user_id}",
    "change_type": change_type,
    "effective_date": role_request.get("effective_date", datetime.now().strftime("%Y-%m-%d")),
    "initiated_by": "{self.manager_user_id}",
    "justification": role_request.get("justification", "Performance-based promotion"),
    "approval_status": "manager_approved"
}}

# New role assignment
if change_type == "promotion":
    new_roles = current_role_info["current_roles"] + role_request.get("additional_roles", ["senior_developer"])
    new_position = role_request.get("new_position", "Senior Software Developer")
    salary_impact = role_request.get("salary_increase_percent", 10)
elif change_type == "lateral":
    new_roles = role_request.get("new_roles", ["employee", "tech_lead"])
    new_position = role_request.get("new_position", "Technical Lead")
    salary_impact = role_request.get("salary_increase_percent", 5)
elif change_type == "transfer":
    new_roles = role_request.get("new_roles", ["employee", "developer"])
    new_position = role_request.get("new_position", "Software Developer")
    new_department = role_request.get("new_department", "Product")
    salary_impact = 0
else:
    new_roles = current_role_info["current_roles"]
    new_position = current_role_info["current_position"]
    salary_impact = 0

# Role transition plan
transition_plan = {{
    "knowledge_transfer": {{
        "required": change_type in ["transfer", "promotion"],
        "duration_days": 14,
        "handover_items": [
            "Current project responsibilities",
            "Team knowledge sharing",
            "Process documentation",
            "Stakeholder introductions"
        ]
    }},
    "training_requirements": {{
        "leadership_training": change_type == "promotion",
        "new_system_access": change_type == "transfer",
        "compliance_training": True,
        "estimated_hours": 16
    }},
    "performance_goals": {{
        "30_day_goals": role_request.get("initial_goals", [
            "Complete role transition successfully",
            "Establish new team relationships"
        ]),
        "90_day_goals": [
            "Achieve full productivity in new role",
            "Complete all required training"
        ]
    }}
}}

result = {{
    "result": {{
        "role_change_processed": True,
        "change_id": role_change_details["change_id"],
        "new_roles": new_roles,
        "new_position": new_position,
        "transition_plan": transition_plan,
        "salary_impact_percent": salary_impact,
        "hr_approval_required": salary_impact > 0,
        "effective_date": role_change_details["effective_date"]
    }}
}}
""",
            },
        )

        # Update permissions for new role
        builder.add_node(
            "PythonCodeNode",
            "update_role_permissions",
            {
                "name": "update_permissions_for_new_role",
                "code": """
# Update permissions based on new role
role_change = role_change_processing.get("new_roles", [])
new_position = role_change_processing.get("new_position", "")

# Permission mapping by role
role_permissions = {
    "senior_developer": [
        "code_review", "deploy_staging", "mentor_junior",
        "technical_decisions", "architecture_input"
    ],
    "tech_lead": [
        "team_coordination", "project_planning", "resource_allocation",
        "performance_reviews", "hiring_decisions"
    ],
    "manager": [
        "budget_approval", "hire_fire", "performance_management",
        "strategic_planning", "cross_team_coordination"
    ]
}

# Calculate new permissions
new_permissions = ["basic_access", "team_collaboration"]  # Base permissions
for role in role_change:
    if role in role_permissions:
        new_permissions.extend(role_permissions[role])

# Remove duplicates
new_permissions = list(set(new_permissions))

# Permission update log
permission_updates = {
    "permissions_added": [p for p in new_permissions if p not in ["basic_access", "team_collaboration"]],
    "permissions_removed": [],  # Typically we add, don't remove on promotion
    "update_timestamp": datetime.now().isoformat(),
    "updated_by": role_change_processing.get("transition_plan", {}).get("knowledge_transfer", {}).get("duration_days", 0),
    "approval_chain": ["manager", "hr"] if role_change_processing.get("hr_approval_required") else ["manager"]
}

# Access provisioning status
provisioning_status = {
    "system_access_updated": True,
    "new_tools_provisioned": len(permission_updates["permissions_added"]),
    "training_access_granted": True,
    "documentation_updated": True,
    "manager_notifications_sent": True
}

result = {
    "result": {
        "permissions_updated": True,
        "new_permissions_count": len(new_permissions),
        "permission_updates": permission_updates,
        "provisioning_status": provisioning_status,
        "role_activation_ready": True
    }
}
""",
            },
        )

        # Connect role change nodes
        builder.add_connection(
            "process_role_change",
            "result.result",
            "update_role_permissions",
            "role_change_processing",
        )

        # Execute workflow
        workflow = builder.build()
        results, execution_id = self.runner.execute_workflow(
            workflow, role_change_request, "role_change_management"
        )

        return results

    def run_comprehensive_user_management_demo(self) -> Dict[str, Any]:
        """
        Run a comprehensive demonstration of all user management operations.

        Returns:
            Complete demonstration results
        """
        print("🚀 Starting Comprehensive User Management Demonstration...")
        print("=" * 70)

        demo_results = {}

        try:
            # 1. Manage team member profile
            print("\n1. Managing Team Member Profile...")
            profile_updates = {
                "first_name": "John",
                "last_name": "Smith",
                "position": "Senior Software Developer",
                "work_phone": "+1-555-0199",
            }
            demo_results["profile_management"] = self.manage_team_member_profile(
                "user_001", profile_updates
            )

            # 2. Review and modify access
            print("\n2. Reviewing and Modifying Access...")
            access_request = {
                "permissions_to_add": ["deploy_staging", "code_review"],
                "permissions_to_remove": [],
                "temporary_access": {
                    "permissions": ["admin_panel"],
                    "duration_days": 7,
                    "justification": "Emergency debugging access",
                },
                "justification": "Promotion to senior developer role",
            }
            demo_results["access_management"] = self.review_and_modify_access(
                "user_001", access_request
            )

            # 3. Track team performance
            print("\n3. Tracking Team Performance...")
            demo_results["performance_tracking"] = self.track_team_performance(
                "dept_engineering", "monthly"
            )

            # 4. Handle role changes
            print("\n4. Processing Role Change...")
            role_change_request = {
                "change_type": "promotion",
                "new_position": "Senior Software Developer",
                "additional_roles": ["senior_developer", "mentor"],
                "salary_increase_percent": 12,
                "justification": "Excellent performance and leadership skills",
                "effective_date": "2024-07-01",
            }
            demo_results["role_management"] = self.handle_role_changes(
                "user_001", role_change_request
            )

            # Print comprehensive summary
            self.print_user_management_summary(demo_results)

            return demo_results

        except Exception as e:
            print(f"❌ User management demonstration failed: {str(e)}")
            raise

    def print_user_management_summary(self, results: Dict[str, Any]):
        """
        Print a comprehensive user management summary.

        Args:
            results: User management results from all workflows
        """
        print("\n" + "=" * 70)
        print("USER MANAGEMENT DEMONSTRATION COMPLETE")
        print("=" * 70)

        # Profile management summary
        profile_result = (
            results.get("profile_management", {})
            .get("manage_profile", {})
            .get("result", {})
            .get("result", {})
        )
        print(
            f"👤 Profile: {len(profile_result.get('fields_updated', []))} fields updated"
        )

        # Access management summary
        access_result = (
            results.get("access_management", {})
            .get("apply_access_changes", {})
            .get("result", {})
            .get("result", {})
        )
        print(f"🔐 Access: {access_result.get('changes_applied', 0)} changes applied")

        # Performance tracking summary
        performance_result = (
            results.get("performance_tracking", {})
            .get("collect_performance_data", {})
            .get("result", {})
            .get("result", {})
        )
        print(
            f"📊 Performance: {performance_result.get('team_members_tracked', 0)} team members tracked"
        )

        # Role management summary
        role_result = (
            results.get("role_management", {})
            .get("process_role_change", {})
            .get("result", {})
            .get("result", {})
        )
        print(f"🎯 Role Change: {role_result.get('new_position', 'N/A')} role assigned")

        print("\n🎉 All user management operations completed successfully!")
        print("=" * 70)

        # Print execution statistics
        self.runner.print_stats()


def test_workflow(test_params: Optional[Dict[str, Any]] = None) -> bool:
    """
    Test the user management workflow.

    Args:
        test_params: Optional test parameters

    Returns:
        True if test passes, False otherwise
    """
    try:
        print("🧪 Testing User Management Workflow...")

        # Create test workflow
        user_mgmt = UserManagementWorkflow("test_manager")

        # Test profile management
        test_updates = {"first_name": "Test", "position": "Test Developer"}

        result = user_mgmt.manage_team_member_profile("test_user", test_updates)
        if (
            not result.get("manage_profile", {})
            .get("result", {})
            .get("result", {})
            .get("profile_updated")
        ):
            return False

        print("✅ User management workflow test passed")
        return True

    except Exception as e:
        print(f"❌ User management workflow test failed: {str(e)}")
        return False


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        # Run test
        success = test_workflow()
        sys.exit(0 if success else 1)
    else:
        # Run comprehensive demonstration
        user_mgmt = UserManagementWorkflow()

        try:
            results = user_mgmt.run_comprehensive_user_management_demo()
            print("🎉 User management demonstration completed successfully!")
        except Exception as e:
            print(f"❌ Demonstration failed: {str(e)}")
            sys.exit(1)
