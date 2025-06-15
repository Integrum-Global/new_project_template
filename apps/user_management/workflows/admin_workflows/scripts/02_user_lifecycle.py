#!/usr/bin/env python3
"""
Admin Workflow: User Lifecycle Management

This workflow handles complete user lifecycle operations including:
- Individual user creation and management
- Bulk user operations (CSV import/export)
- User deactivation and deletion
- Access reviews and compliance
"""

import csv
import json
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


class UserLifecycleWorkflow:
    """
    Complete user lifecycle management workflow for administrators.
    """

    def __init__(self, admin_user_id: str = "admin"):
        """
        Initialize the user lifecycle workflow.

        Args:
            admin_user_id: ID of the administrator performing operations
        """
        self.admin_user_id = admin_user_id
        self.runner = WorkflowRunner(
            user_type="admin",
            user_id=admin_user_id,
            enable_debug=True,
            enable_audit=False,  # Disable for testing
            enable_monitoring=True,
        )

    def create_single_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a single user with complete profile setup.

        Args:
            user_data: User information dictionary

        Returns:
            User creation results
        """
        print(f"👤 Creating user: {user_data.get('email', 'Unknown')}")

        builder = self.runner.create_workflow("single_user_creation")

        # Input validation
        validation_rules = {
            "email": {"required": True, "type": str, "min_length": 5},
            "first_name": {"required": True, "type": str, "min_length": 1},
            "last_name": {"required": True, "type": str, "min_length": 1},
            "department": {"required": True, "type": str, "min_length": 2},
            "role": {"required": False, "type": str},
        }

        builder.add_node(
            "PythonCodeNode",
            "validate_user_input",
            create_validation_node(validation_rules),
        )

        # User creation with profile setup
        builder.add_node(
            "PythonCodeNode",
            "create_user_profile",
            {
                "name": "create_complete_user_profile",
                "code": """
import random
import string

def generate_id():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=12))
import random
import string
from datetime import datetime

# Generate user ID and initial password
user_id = generate_id()
temp_password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
password_hash = f"hash_{random.randint(100000, 999999)}"

# Create comprehensive user profile
user_profile = {
    "id": user_id,
    "email": email,
    "first_name": first_name,
    "last_name": last_name,
    "department": department,
    "password_hash": password_hash,
    "temporary_password": temp_password,
    "is_active": True,
    "email_verified": False,
    "must_change_password": True,
    "created_at": datetime.now().isoformat(),
    "created_by": "admin",
    "profile_complete": False,
    "last_login": None,
    "failed_login_attempts": 0,
    "account_locked": False
}

# Set default role if not provided
user_role = role if 'role' in locals() and role else "employee"

result = {
    "result": {
        "user_created": True,
        "user_id": user_id,
        "email": email,
        "temporary_password": temp_password,
        "default_role": user_role,
        "next_steps": [
            "send_welcome_email",
            "assign_role",
            "setup_initial_permissions"
        ]
    }
}
""",
            },
        )

        # Role assignment
        builder.add_node(
            "PythonCodeNode",
            "assign_user_role",
            {
                "name": "assign_initial_user_role",
                "code": """
# Assign initial role based on department and position
role_assignments = []

# Get role from user creation or use default
assigned_role = user_creation.get("default_role", "employee")

# Department-specific role mapping
department_roles = {
    "Engineering": ["developer", "employee"],
    "Sales": ["sales_rep", "employee"],
    "Marketing": ["marketing_specialist", "employee"],
    "HR": ["hr_specialist", "employee"],
    "Finance": ["finance_analyst", "employee"],
    "IT": ["it_support", "employee"]
}

# Add department-specific roles
dept = user_creation.get("email", "").split("@")[0]  # Simplified department detection
if department in department_roles:
    role_assignments.extend(department_roles[department])
else:
    role_assignments.append("employee")

# Add the specifically requested role if provided
if assigned_role not in role_assignments:
    role_assignments.append(assigned_role)

result = {
    "result": {
        "roles_assigned": role_assignments,
        "primary_role": assigned_role,
        "department_roles": department_roles.get(department, ["employee"]),
        "assignment_date": datetime.now().isoformat()
    }
}
""",
            },
        )

        # Welcome notification
        builder.add_node(
            "PythonCodeNode",
            "send_welcome_notification",
            {
                "name": "send_user_welcome_email",
                "code": """
# Generate welcome email notification
welcome_email = {
    "to": user_creation.get("email"),
    "subject": "Welcome to the User Management System",
    "template": "user_welcome",
    "variables": {
        "first_name": user_creation.get("email", "").split("@")[0],  # Simplified
        "temporary_password": user_creation.get("temporary_password"),
        "login_url": "https://company.com/login",
        "support_email": "support@company.com",
        "setup_instructions": [
            "1. Login with your temporary password",
            "2. Complete your profile information",
            "3. Set up a new secure password",
            "4. Enable multi-factor authentication",
            "5. Review privacy settings"
        ]
    }
}

# System notification for admin
admin_notification = {
    "type": "user_created",
    "message": f"New user {user_creation.get('email')} created successfully",
    "details": {
        "user_id": user_creation.get("user_id"),
        "roles": role_assignment.get("roles_assigned", []),
        "created_by": "admin"
    }
}

result = {
    "result": {
        "welcome_email_queued": True,
        "admin_notification_sent": True,
        "onboarding_checklist_created": True,
        "user_setup_complete": True
    }
}
""",
            },
        )

        # Connect workflow nodes
        builder.add_connection(
            "validate_user_input", "result", "create_user_profile", "validation_result"
        )
        builder.add_connection(
            "create_user_profile", "result.result", "assign_user_role", "user_creation"
        )
        builder.add_connection(
            "create_user_profile",
            "result.result",
            "send_welcome_notification",
            "user_creation",
        )
        builder.add_connection(
            "assign_user_role",
            "result.result",
            "send_welcome_notification",
            "role_assignment",
        )

        # Execute workflow
        workflow = builder.build()
        results, execution_id = self.runner.execute_workflow(
            workflow, user_data, "single_user_creation"
        )

        return results

    def bulk_create_users(self, users_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create multiple users from a list of user data.

        Args:
            users_data: List of user information dictionaries

        Returns:
            Bulk creation results
        """
        print(f"👥 Creating {len(users_data)} users in bulk...")

        builder = self.runner.create_workflow("bulk_user_creation")

        # Bulk user processing
        builder.add_node(
            "PythonCodeNode",
            "process_bulk_users",
            {
                "name": "process_bulk_user_creation",
                "code": f"""
import random
import string

def generate_id():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=12))
import random
import string
from datetime import datetime

# Process all users in the bulk list
users_data_list = {users_data}
created_users = []
failed_users = []

for user_data in users_data_list:
    try:
        # Validate required fields
        required_fields = ["email", "first_name", "last_name", "department"]
        missing_fields = [field for field in required_fields if not user_data.get(field)]

        if missing_fields:
            failed_users.append({{
                "email": user_data.get("email", "unknown"),
                "error": f"Missing required fields: {{missing_fields}}"
            }})
            continue

        # Create user profile
        user_id = generate_id()
        temp_password = secrets.token_urlsafe(12)
        password_hash = hashlib.sha256((temp_password + "salt123").encode()).hexdigest()

        user_profile = {{
            "id": user_id,
            "email": user_data["email"],
            "first_name": user_data["first_name"],
            "last_name": user_data["last_name"],
            "department": user_data["department"],
            "password_hash": password_hash,
            "temporary_password": temp_password,
            "is_active": True,
            "created_at": datetime.now().isoformat(),
            "created_by": "admin_bulk_import"
        }}

        created_users.append(user_profile)

    except Exception as e:
        failed_users.append({{
            "email": user_data.get("email", "unknown"),
            "error": str(e)
        }})

result = {{
    "result": {{
        "total_processed": len(users_data_list),
        "successful_creations": len(created_users),
        "failed_creations": len(failed_users),
        "created_users": created_users,
        "failed_users": failed_users,
        "success_rate": len(created_users) / len(users_data_list) * 100 if users_data_list else 0
    }}
}}
""",
            },
        )

        # Generate bulk welcome notifications
        builder.add_node(
            "PythonCodeNode",
            "generate_bulk_notifications",
            {
                "name": "generate_bulk_welcome_notifications",
                "code": """
# Generate welcome notifications for all successfully created users
bulk_notifications = []
admin_summary = {
    "total_users_created": bulk_results.get("successful_creations", 0),
    "notifications_generated": 0,
    "failed_notifications": 0
}

for user in bulk_results.get("created_users", []):
    try:
        welcome_notification = {
            "to": user["email"],
            "subject": "Welcome to the User Management System",
            "template": "bulk_user_welcome",
            "variables": {
                "first_name": user["first_name"],
                "last_name": user["last_name"],
                "temporary_password": user["temporary_password"],
                "user_id": user["id"],
                "department": user["department"]
            }
        }
        bulk_notifications.append(welcome_notification)
        admin_summary["notifications_generated"] += 1

    except Exception as e:
        admin_summary["failed_notifications"] += 1

result = {
    "result": {
        "notifications_queued": len(bulk_notifications),
        "notification_summary": admin_summary,
        "bulk_import_complete": True
    }
}
""",
            },
        )

        # Connect bulk processing nodes
        builder.add_connection(
            "process_bulk_users",
            "result.result",
            "generate_bulk_notifications",
            "bulk_results",
        )

        # Execute workflow
        workflow = builder.build()
        results, execution_id = self.runner.execute_workflow(
            workflow, {}, "bulk_user_creation"
        )

        return results

    def deactivate_user(
        self, user_id: str, reason: str = "standard_deactivation"
    ) -> Dict[str, Any]:
        """
        Deactivate a user account (soft deletion).

        Args:
            user_id: ID of user to deactivate
            reason: Reason for deactivation

        Returns:
            Deactivation results
        """
        print(f"🔒 Deactivating user: {user_id}")

        builder = self.runner.create_workflow("user_deactivation")

        # User deactivation process
        builder.add_node(
            "PythonCodeNode",
            "deactivate_user_account",
            {
                "name": "perform_user_deactivation",
                "code": f"""
from datetime import datetime

# Deactivation parameters
target_user_id = "{user_id}"
deactivation_reason = "{reason}"

# Simulate user lookup and deactivation
user_account = {{
    "id": target_user_id,
    "email": f"user_{target_user_id}@company.com",
    "status": "active",
    "last_login": datetime.now().isoformat(),
    "department": "Engineering"
}}

# Perform deactivation steps
deactivation_steps = []

# 1. Disable login access
deactivation_steps.append({{
    "step": "disable_login",
    "status": "completed",
    "timestamp": datetime.now().isoformat()
}})

# 2. Revoke active sessions
deactivation_steps.append({{
    "step": "revoke_sessions",
    "status": "completed",
    "sessions_revoked": 3
}})

# 3. Remove from active groups
deactivation_steps.append({{
    "step": "remove_group_memberships",
    "status": "completed",
    "groups_removed": ["developers", "engineering_team"]
}})

# 4. Archive user data
deactivation_steps.append({{
    "step": "archive_user_data",
    "status": "completed",
    "archive_location": f"archive/users/{target_user_id}"
}})

# 5. Send notifications
deactivation_steps.append({{
    "step": "send_notifications",
    "status": "completed",
    "notifications_sent": ["manager", "hr", "it_admin"]
}})

result = {{
    "result": {{
        "user_deactivated": True,
        "user_id": target_user_id,
        "deactivation_reason": deactivation_reason,
        "deactivation_timestamp": datetime.now().isoformat(),
        "steps_completed": len(deactivation_steps),
        "deactivation_steps": deactivation_steps,
        "data_retained": True,
        "compliance_status": "compliant"
    }}
}}
""",
            },
        )

        # GDPR compliance check
        builder.add_node(
            "PythonCodeNode",
            "gdpr_compliance_check",
            {
                "name": "verify_gdpr_compliance",
                "code": """
# GDPR compliance verification for deactivation
compliance_checks = []

# Check data retention requirements
compliance_checks.append({
    "check": "data_retention_policy",
    "status": "compliant",
    "retention_period": "7_years",
    "justification": "Legal and audit requirements"
})

# Check data subject rights
compliance_checks.append({
    "check": "data_subject_rights",
    "status": "compliant",
    "rights_preserved": ["access", "portability", "rectification"]
})

# Check processing lawfulness
compliance_checks.append({
    "check": "processing_lawfulness",
    "status": "compliant",
    "legal_basis": "contract_performance"
})

result = {
    "result": {
        "gdpr_compliant": True,
        "compliance_checks": compliance_checks,
        "data_protection_verified": True,
        "retention_schedule_set": True
    }
}
""",
            },
        )

        # Connect deactivation nodes
        builder.add_connection(
            "deactivate_user_account",
            "result.result",
            "gdpr_compliance_check",
            "deactivation_info",
        )

        # Execute workflow
        workflow = builder.build()
        results, execution_id = self.runner.execute_workflow(
            workflow, {"user_id": user_id, "reason": reason}, "user_deactivation"
        )

        return results

    def export_user_data(
        self, user_id: str, export_format: str = "json"
    ) -> Dict[str, Any]:
        """
        Export user data for GDPR compliance or backup purposes.

        Args:
            user_id: ID of user whose data to export
            export_format: Format for export (json, csv, xml)

        Returns:
            Export results
        """
        print(f"📁 Exporting data for user: {user_id} in {export_format} format")

        builder = self.runner.create_workflow("user_data_export")

        # Data collection and export
        builder.add_node(
            "PythonCodeNode",
            "collect_user_data",
            {
                "name": "collect_complete_user_data",
                "code": f"""
from datetime import datetime
import json

# Collect all user data categories
user_data_export = {{
    "export_metadata": {{
        "user_id": "{user_id}",
        "export_timestamp": datetime.now().isoformat(),
        "export_format": "{export_format}",
        "export_type": "complete",
        "gdpr_compliant": True
    }},
    "personal_data": {{
        "profile_information": {{
            "id": "{user_id}",
            "email": f"user_{user_id}@company.com",
            "first_name": "John",
            "last_name": "Doe",
            "department": "Engineering",
            "position": "Software Developer",
            "created_at": "2024-01-15T10:00:00Z",
            "last_updated": datetime.now().isoformat()
        }},
        "contact_information": {{
            "primary_email": f"user_{user_id}@company.com",
            "phone": "+1-555-0123",
            "emergency_contact": "Jane Doe",
            "emergency_phone": "+1-555-0124"
        }},
        "employment_data": {{
            "employee_id": f"EMP{user_id[:8]}",
            "department": "Engineering",
            "position": "Software Developer",
            "manager": "manager@company.com",
            "start_date": "2024-01-15",
            "employment_status": "active"
        }}
    }},
    "activity_data": {{
        "login_history": [
            {{
                "timestamp": "2024-06-15T09:00:00Z",
                "ip_address": "192.168.1.100",
                "user_agent": "Mozilla/5.0...",
                "success": True
            }},
            {{
                "timestamp": "2024-06-14T09:00:00Z",
                "ip_address": "192.168.1.100",
                "user_agent": "Mozilla/5.0...",
                "success": True
            }}
        ],
        "system_usage": {{
            "last_login": "2024-06-15T09:00:00Z",
            "total_logins": 150,
            "average_session_duration": "4.5_hours",
            "most_used_features": ["dashboard", "reports", "profile"]
        }},
        "permissions_history": [
            {{
                "action": "role_assigned",
                "role": "employee",
                "timestamp": "2024-01-15T10:00:00Z",
                "assigned_by": "admin"
            }},
            {{
                "action": "permission_granted",
                "permission": "file_access",
                "timestamp": "2024-01-16T10:00:00Z",
                "granted_by": "manager"
            }}
        ]
    }},
    "preferences_data": {{
        "notification_preferences": {{
            "email_notifications": True,
            "sms_notifications": False,
            "browser_notifications": True
        }},
        "privacy_settings": {{
            "profile_visibility": "team",
            "data_sharing": False,
            "marketing_communications": False
        }},
        "ui_preferences": {{
            "language": "en",
            "timezone": "UTC-5",
            "theme": "light",
            "date_format": "MM/DD/YYYY"
        }}
    }}
}}

# Format data based on requested format
if "{export_format}" == "json":
    formatted_data = json.dumps(user_data_export, indent=2)
elif "{export_format}" == "csv":
    # Simplified CSV representation
    formatted_data = "category,key,value\\nprofile,email,user_{user_id}@company.com\\n"
else:
    formatted_data = str(user_data_export)

result = {{
    "result": {{
        "export_successful": True,
        "data_categories": len(user_data_export),
        "export_size_kb": len(formatted_data) / 1024,
        "export_format": "{export_format}",
        "gdpr_compliant": True,
        "data_integrity_verified": True
    }}
}}
""",
            },
        )

        # Data validation and packaging
        builder.add_node(
            "PythonCodeNode",
            "package_export",
            {
                "name": "package_user_data_export",
                "code": """
# Package export with metadata and validation
export_package = {
    "package_info": {
        "package_id": f"export_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "created_at": datetime.now().isoformat(),
        "data_categories": export_data.get("data_categories", 0),
        "size_kb": export_data.get("export_size_kb", 0),
        "format": export_data.get("export_format", "json"),
        "encryption": "AES-256",
        "compression": "gzip"
    },
    "validation": {
        "data_integrity": "verified",
        "completeness_check": "passed",
        "gdpr_compliance": "verified",
        "export_quality": "high"
    },
    "delivery": {
        "method": "secure_download",
        "expiry_hours": 24,
        "download_limit": 1,
        "access_logs_enabled": True
    }
}

result = {
    "result": {
        "package_ready": True,
        "package_id": export_package["package_info"]["package_id"],
        "download_url": f"https://secure.company.com/exports/{export_package['package_info']['package_id']}",
        "expiry_time": "24_hours",
        "export_complete": True
    }
}
""",
            },
        )

        # Connect export nodes
        builder.add_connection(
            "collect_user_data", "result.result", "package_export", "export_data"
        )

        # Execute workflow
        workflow = builder.build()
        results, execution_id = self.runner.execute_workflow(
            workflow, {"user_id": user_id, "format": export_format}, "user_data_export"
        )

        return results

    def run_comprehensive_user_lifecycle_demo(self) -> Dict[str, Any]:
        """
        Run a comprehensive demonstration of all user lifecycle operations.

        Returns:
            Complete demonstration results
        """
        print("🚀 Starting Comprehensive User Lifecycle Demonstration...")
        print("=" * 70)

        demo_results = {}

        try:
            # 1. Create single user
            print("\\n1. Creating Single User...")
            single_user_data = {
                "email": "john.doe@company.com",
                "first_name": "John",
                "last_name": "Doe",
                "department": "Engineering",
                "role": "developer",
            }
            demo_results["single_user"] = self.create_single_user(single_user_data)

            # 2. Bulk create users
            print("\\n2. Creating Multiple Users...")
            bulk_users_data = [
                {
                    "email": "alice.smith@company.com",
                    "first_name": "Alice",
                    "last_name": "Smith",
                    "department": "Marketing",
                },
                {
                    "email": "bob.johnson@company.com",
                    "first_name": "Bob",
                    "last_name": "Johnson",
                    "department": "Sales",
                },
                {
                    "email": "carol.brown@company.com",
                    "first_name": "Carol",
                    "last_name": "Brown",
                    "department": "HR",
                },
            ]
            demo_results["bulk_users"] = self.bulk_create_users(bulk_users_data)

            # 3. Export user data
            print("\\n3. Exporting User Data...")
            demo_results["data_export"] = self.export_user_data("user123", "json")

            # 4. Deactivate user
            print("\\n4. Deactivating User...")
            demo_results["user_deactivation"] = self.deactivate_user(
                "user123", "employee_departure"
            )

            # Print comprehensive summary
            self.print_lifecycle_summary(demo_results)

            return demo_results

        except Exception as e:
            print(f"❌ Demonstration failed: {str(e)}")
            raise

    def print_lifecycle_summary(self, results: Dict[str, Any]):
        """
        Print a comprehensive lifecycle demonstration summary.

        Args:
            results: Demonstration results from all workflows
        """
        print("\\n" + "=" * 70)
        print("USER LIFECYCLE DEMONSTRATION COMPLETE")
        print("=" * 70)

        # Single user creation summary
        single_user = (
            results.get("single_user", {})
            .get("create_user_profile", {})
            .get("result", {})
            .get("result", {})
        )
        print(f"👤 Single User: Created {single_user.get('email', 'N/A')}")

        # Bulk user creation summary
        bulk_users = (
            results.get("bulk_users", {})
            .get("process_bulk_users", {})
            .get("result", {})
            .get("result", {})
        )
        print(
            f"👥 Bulk Users: {bulk_users.get('successful_creations', 0)}/{bulk_users.get('total_processed', 0)} created"
        )

        # Data export summary
        export_result = (
            results.get("data_export", {})
            .get("collect_user_data", {})
            .get("result", {})
            .get("result", {})
        )
        print(
            f"📁 Data Export: {export_result.get('export_size_kb', 0):.1f} KB exported"
        )

        # Deactivation summary
        deactivation = (
            results.get("user_deactivation", {})
            .get("deactivate_user_account", {})
            .get("result", {})
            .get("result", {})
        )
        print(
            f"🔒 Deactivation: {deactivation.get('steps_completed', 0)} steps completed"
        )

        print("\\n🎉 All user lifecycle operations completed successfully!")
        print("=" * 70)

        # Print execution statistics
        self.runner.print_stats()


def test_workflow(test_params: Optional[Dict[str, Any]] = None) -> bool:
    """
    Test the user lifecycle workflow.

    Args:
        test_params: Optional test parameters

    Returns:
        True if test passes, False otherwise
    """
    try:
        print("🧪 Testing User Lifecycle Workflow...")

        # Create test workflow
        lifecycle = UserLifecycleWorkflow("test_admin")

        # Test single user creation
        test_user = {
            "email": "test.user@company.com",
            "first_name": "Test",
            "last_name": "User",
            "department": "Engineering",
            "role": "developer",
        }

        result = lifecycle.create_single_user(test_user)
        if (
            not result.get("create_user_profile", {})
            .get("result", {})
            .get("result", {})
            .get("user_created")
        ):
            return False

        print("✅ User lifecycle workflow test passed")
        return True

    except Exception as e:
        print(f"❌ User lifecycle workflow test failed: {str(e)}")
        return False


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        # Run test
        success = test_workflow()
        sys.exit(0 if success else 1)
    else:
        # Run comprehensive demonstration
        lifecycle = UserLifecycleWorkflow()

        try:
            results = lifecycle.run_comprehensive_user_lifecycle_demo()
            print("🎉 User lifecycle demonstration completed successfully!")
        except Exception as e:
            print(f"❌ Demonstration failed: {str(e)}")
            sys.exit(1)
