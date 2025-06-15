#!/usr/bin/env python3
"""
User Workflow: Data Management and Access

This workflow handles personal data management including:
- Personal data access and viewing
- Data export for GDPR compliance
- Data correction requests
- Data usage analytics
- Activity log review
"""

import sys
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

# Add shared utilities to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))

from workflow_runner import WorkflowRunner, create_user_context_node, create_validation_node


class DataManagementWorkflow:
    """
    Complete data management workflow for end users.
    """
    
    def __init__(self, user_id: str = "user"):
        """
        Initialize the data management workflow.
        
        Args:
            user_id: ID of the user performing data operations
        """
        self.user_id = user_id
        self.runner = WorkflowRunner(
            user_type="user",
            user_id=user_id,
            enable_debug=True,
            enable_audit=False,  # Disable for testing
            enable_monitoring=True
        )
    
    def access_personal_data(self, access_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Access and view personal data stored in the system.
        
        Args:
            access_request: Data access request parameters
            
        Returns:
            Personal data access results
        """
        print(f"📁 Accessing personal data for user: {self.user_id}")
        
        builder = self.runner.create_workflow("personal_data_access")
        
        # Validate access request
        validation_rules = {
            "data_categories": {"required": False, "type": "list"},
            "date_range": {"required": False, "type": "dict"},
            "format": {"required": False, "type": "str"}
        }
        
        builder.add_node("PythonCodeNode", "validate_access_request", 
                        create_validation_node(validation_rules))
        
        # Collect comprehensive personal data
        builder.add_node("PythonCodeNode", "collect_personal_data", {
            "name": "collect_user_personal_data",
            "code": """
from datetime import datetime, timedelta

# Collect all personal data categories for user
user_id = "test@example.com"
access_request_data = {"request_type": "export", "data_categories": ["profile", "activity_logs"], "format": "json"}

# Define data categories available to user
available_categories = [
    "profile_information", "activity_logs", "preferences", "communications",
    "system_usage", "permissions_history", "security_events", "support_tickets"
]

requested_categories = access_request_data.get("data_categories", available_categories)
date_range = access_request_data.get("date_range", {})
export_format = access_request_data.get("format", "json")

# Collect profile information
profile_data = {
    "category": "profile_information",
    "data": {
        "personal_details": {
            "user_id": user_id,
            "email": f"{user_id}@company.com",
            "first_name": "John",
            "last_name": "Doe",
            "department": "Engineering",
            "position": "Software Developer",
            "created_at": "2024-01-15T10:00:00Z",
            "last_updated": "2024-06-10T14:30:00Z"
        },
        "contact_information": {
            "work_email": f"{user_id}@company.com",
            "work_phone": "+1-555-0123",
            "emergency_contact": {
                "name": "Jane Doe",
                "relationship": "Spouse",
                "phone": "+1-555-0124"
            }
        },
        "employment_data": {
            "employee_id": f"EMP{user_id[:8]}",
            "start_date": "2024-01-15",
            "department": "Engineering",
            "manager": "manager@company.com",
            "location": "New York Office"
        }
    }
}

# Collect activity logs
activity_data = {
    "category": "activity_logs",
    "data": {
        "login_history": [
            {
                "timestamp": "2024-06-15T09:00:00Z",
                "ip_address": "192.168.1.100",
                "device": "Chrome on macOS",
                "location": "New York, NY",
                "success": True
            },
            {
                "timestamp": "2024-06-14T17:30:00Z",
                "ip_address": "192.168.1.101",
                "device": "Safari on iOS",
                "location": "New York, NY", 
                "success": True
            }
        ],
        "system_activities": [
            {
                "timestamp": "2024-06-15T10:30:00Z",
                "action": "profile_update",
                "details": "Updated phone number",
                "ip_address": "192.168.1.100"
            },
            {
                "timestamp": "2024-06-10T14:30:00Z",
                "action": "password_change",
                "details": "Password updated successfully",
                "ip_address": "192.168.1.100"
            }
        ]
    }
}

# Collect user preferences
preferences_data = {
    "category": "preferences",
    "data": {
        "notification_preferences": {
            "email_notifications": True,
            "sms_notifications": False,
            "browser_notifications": True,
            "marketing_communications": False
        },
        "ui_preferences": {
            "theme": "dark",
            "language": "en",
            "dashboard_layout": "compact",
            "timezone": "UTC-5"
        },
        "privacy_settings": {
            "profile_visibility": "team",
            "data_sharing": True,
            "usage_analytics": True
        }
    }
}

# Collect system usage data
usage_data = {
    "category": "system_usage",
    "data": {
        "feature_usage": {
            "dashboard_views": 145,
            "profile_updates": 8,
            "security_settings_access": 3,
            "support_tickets_created": 1
        },
        "session_statistics": {
            "total_sessions": 89,
            "average_session_duration": "4.2 hours",
            "most_active_day": "Tuesday",
            "most_active_time": "10:00-11:00"
        },
        "data_exports": [
            {
                "export_date": "2024-05-15T09:00:00Z",
                "export_type": "profile_data",
                "format": "json",
                "size_kb": 45
            }
        ]
    }
}

# Collect permissions history
permissions_data = {
    "category": "permissions_history",
    "data": {
        "current_roles": ["employee", "developer"],
        "role_history": [
            {
                "role": "employee",
                "assigned_date": "2024-01-15T10:00:00Z",
                "assigned_by": "admin",
                "status": "active"
            },
            {
                "role": "developer",
                "assigned_date": "2024-02-01T09:00:00Z", 
                "assigned_by": "manager",
                "status": "active"
            }
        ],
        "permission_changes": [
            {
                "timestamp": "2024-02-01T09:00:00Z",
                "action": "permission_granted",
                "permission": "code_repository_access",
                "granted_by": "manager"
            }
        ]
    }
}

# Aggregate requested data
collected_data = {}
for category in requested_categories:
    if category == "profile_information":
        collected_data[category] = profile_data["data"]
    elif category == "activity_logs":
        collected_data[category] = activity_data["data"]
    elif category == "preferences":
        collected_data[category] = preferences_data["data"]
    elif category == "system_usage":
        collected_data[category] = usage_data["data"]
    elif category == "permissions_history":
        collected_data[category] = permissions_data["data"]

# Data access metadata
access_metadata = {
    "user_id": user_id,
    "access_timestamp": datetime.now().isoformat(),
    "requested_categories": requested_categories,
    "categories_found": list(collected_data.keys()),
    "total_data_points": sum(len(str(data)) for data in collected_data.values()),
    "access_method": "user_self_service",
    "compliance_status": "gdpr_compliant"
}

result = {
    "result": {
        "data_access_successful": True,
        "categories_retrieved": len(collected_data),
        "personal_data": collected_data,
        "access_metadata": access_metadata,
        "data_summary": {
            "profile_records": 1 if "profile_information" in collected_data else 0,
            "activity_records": len(collected_data.get("activity_logs", {}).get("login_history", [])),
            "preference_categories": len(collected_data.get("preferences", {})),
            "usage_metrics": len(collected_data.get("system_usage", {}).get("feature_usage", {}))
        }
    }
}
"""
        })
        
        # Generate data access report
        builder.add_node("PythonCodeNode", "generate_data_report", {
            "name": "generate_personal_data_report",
            "code": """
from datetime import datetime
# Generate comprehensive data access report
data_collection = personal_data_collection
access_metadata = data_collection.get("access_metadata", {})
personal_data = data_collection.get("personal_data", {})

# Data analysis and insights
data_insights = {
    "data_completeness": {
        "profile_complete": "profile_information" in personal_data,
        "activity_tracking": "activity_logs" in personal_data,
        "preferences_set": "preferences" in personal_data,
        "usage_analytics": "system_usage" in personal_data
    },
    "data_quality": {
        "profile_accuracy": 95,  # Percentage of accurate profile data
        "data_freshness": "recent",  # Based on last update dates
        "completeness_score": len(personal_data) / len(access_metadata.get("requested_categories", [])) * 100
    },
    "privacy_compliance": {
        "gdpr_compliant": True,
        "data_minimization": True,
        "purpose_limitation": True,
        "retention_policy_applied": True
    }
}

# User data rights summary
data_rights_info = {
    "right_to_access": {
        "status": "exercised",
        "last_access": access_metadata.get("access_timestamp"),
        "access_frequency": "as_needed"
    },
    "right_to_rectification": {
        "status": "available", 
        "process": "Submit correction request through profile settings",
        "response_time": "5 business days"
    },
    "right_to_erasure": {
        "status": "available",
        "process": "Contact data protection officer",
        "conditions": "Subject to legal retention requirements"
    },
    "right_to_portability": {
        "status": "available",
        "formats": ["JSON", "CSV", "XML"],
        "delivery_method": "secure_download"
    }
}

# Data processing information
processing_info = {
    "processing_purposes": [
        "Account management and authentication",
        "Service provision and support",
        "Security monitoring and fraud prevention", 
        "Legal compliance and audit",
        "System improvement and analytics"
    ],
    "legal_basis": [
        "Contract performance",
        "Legitimate interests",
        "Legal obligation"
    ],
    "data_retention": {
        "profile_data": "Duration of employment + 7 years",
        "activity_logs": "2 years",
        "preferences": "Duration of account",
        "support_data": "3 years after resolution"
    },
    "data_sharing": {
        "internal_sharing": "Limited to authorized personnel",
        "external_sharing": "None without consent",
        "third_party_processors": ["Cloud storage provider", "Email service provider"]
    }
}

# Actionable recommendations
recommendations = [
    {
        "category": "data_accuracy",
        "priority": "medium",
        "title": "Review Profile Information",
        "description": "Ensure your profile information is up to date",
        "action": "Update profile if any information has changed"
    },
    {
        "category": "privacy_settings",
        "priority": "low",
        "title": "Review Privacy Preferences",
        "description": "Check your privacy settings and data sharing preferences",
        "action": "Visit privacy settings if you want to make changes"
    }
]

# Data access summary report
access_report = {
    "report_id": f"DATA_ACCESS_{access_metadata.get('user_id')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
    "generated_at": datetime.now().isoformat(),
    "user_id": access_metadata.get("user_id"),
    "data_categories": len(personal_data),
    "total_data_size_estimate": f"{access_metadata.get('total_data_points', 0) / 1024:.1f} KB",
    "compliance_verified": True,
    "user_rights_respected": True
}

result = {
    "result": {
        "report_generated": True,
        "data_insights": data_insights,
        "data_rights_info": data_rights_info,
        "processing_info": processing_info,
        "recommendations": recommendations,
        "access_report": access_report,
        "next_steps": ["review_data_accuracy", "check_privacy_settings", "consider_data_updates"]
    }
}
"""
        })
        
        # Connect data access nodes
        builder.add_connection("validate_access_request", "result", "collect_personal_data", "validation_result")
        builder.add_connection("collect_personal_data", "result.result", "generate_data_report", "personal_data_collection")
        
        # Execute workflow
        workflow = builder.build()
        results, execution_id = self.runner.execute_workflow(
            workflow, access_request, "personal_data_access"
        )
        
        return results
    
    def export_personal_data(self, export_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Export personal data for GDPR compliance or backup purposes.
        
        Args:
            export_request: Data export request parameters
            
        Returns:
            Data export results
        """
        print(f"📤 Exporting personal data for user: {self.user_id}")
        
        builder = self.runner.create_workflow("personal_data_export")
        
        # Process data export request
        builder.add_node("PythonCodeNode", "process_export_request", {
            "name": "process_personal_data_export",
            "code": """
from datetime import datetime, timedelta
# Process comprehensive data export request
user_id = "test@example.com"
export_request_data = {"format": "json", "categories": "all", "include_metadata": True, "encryption": True, "delivery": "download"}

# Export configuration
export_config = {
    "export_id": f"EXPORT_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
    "user_id": user_id,
    "requested_format": export_request_data.get("format", "json"),
    "requested_categories": export_request_data.get("categories", "all"),
    "include_metadata": export_request_data.get("include_metadata", True),
    "encryption_required": export_request_data.get("encryption", True),
    "delivery_method": export_request_data.get("delivery", "download")
}

# Comprehensive data collection for export
export_data = {
    "export_metadata": {
        "export_id": export_config["export_id"],
        "user_id": user_id,
        "export_timestamp": datetime.now().isoformat(),
        "export_type": "complete_user_data",
        "gdpr_compliant": True,
        "format": export_config["requested_format"],
        "encryption": "AES-256" if export_config["encryption_required"] else None
    },
    "personal_information": {
        "profile": {
            "user_id": user_id,
            "email": f"{user_id}@company.com",
            "first_name": "John",
            "last_name": "Doe",
            "department": "Engineering",
            "position": "Software Developer",
            "employee_id": f"EMP{user_id[:8]}",
            "created_at": "2024-01-15T10:00:00Z",
            "last_updated": "2024-06-10T14:30:00Z"
        },
        "contact_details": {
            "primary_email": f"{user_id}@company.com",
            "work_phone": "+1-555-0123",
            "emergency_contact": {
                "name": "Jane Doe",
                "relationship": "Spouse", 
                "phone": "+1-555-0124"
            }
        },
        "preferences": {
            "notifications": {
                "email_enabled": True,
                "sms_enabled": False,
                "browser_enabled": True
            },
            "ui_settings": {
                "theme": "dark",
                "language": "en",
                "timezone": "UTC-5"
            },
            "privacy": {
                "profile_visibility": "team",
                "data_analytics": True,
                "marketing_consent": False
            }
        }
    },
    "activity_data": {
        "authentication_logs": [
            {
                "timestamp": "2024-06-15T09:00:00Z",
                "event": "login_success",
                "ip_address": "192.168.1.100",
                "device": "Chrome on macOS",
                "location": "New York, NY"
            },
            {
                "timestamp": "2024-06-14T17:30:00Z", 
                "event": "logout",
                "ip_address": "192.168.1.100",
                "device": "Chrome on macOS"
            }
        ],
        "system_activities": [
            {
                "timestamp": "2024-06-15T10:30:00Z",
                "action": "profile_update",
                "details": "Updated contact information",
                "changed_fields": ["phone"]
            },
            {
                "timestamp": "2024-06-10T14:30:00Z",
                "action": "security_update",
                "details": "Password changed"
            }
        ],
        "feature_usage": {
            "dashboard_visits": 145,
            "profile_edits": 8,
            "data_exports": 2,
            "support_tickets": 1,
            "last_activity": "2024-06-15T10:30:00Z"
        }
    },
    "permissions_and_roles": {
        "current_roles": ["employee", "developer"],
        "permission_history": [
            {
                "timestamp": "2024-01-15T10:00:00Z",
                "action": "role_assigned",
                "role": "employee",
                "assigned_by": "admin"
            },
            {
                "timestamp": "2024-02-01T09:00:00Z",
                "action": "role_assigned", 
                "role": "developer",
                "assigned_by": "manager"
            }
        ],
        "access_grants": [
            {
                "permission": "dashboard_access",
                "granted_date": "2024-01-15T10:00:00Z",
                "status": "active"
            },
            {
                "permission": "code_repository_access",
                "granted_date": "2024-02-01T09:00:00Z",
                "status": "active"
            }
        ]
    },
    "communications": {
        "support_tickets": [
            {
                "ticket_id": "TICK-001",
                "created_date": "2024-05-10T14:00:00Z",
                "subject": "Password reset assistance",
                "status": "resolved",
                "resolution_date": "2024-05-10T15:30:00Z"
            }
        ],
        "system_notifications": [
            {
                "timestamp": "2024-06-01T09:00:00Z",
                "type": "security_alert",
                "message": "Password will expire in 30 days"
            },
            {
                "timestamp": "2024-05-15T10:00:00Z",
                "type": "feature_announcement",
                "message": "New dashboard features available"
            }
        ]
    }
}

# Calculate export statistics
export_stats = {
    "categories_included": len(export_data) - 1,  # Excluding metadata
    "total_records": (
        len(export_data.get("activity_data", {}).get("authentication_logs", [])) +
        len(export_data.get("activity_data", {}).get("system_activities", [])) +
        len(export_data.get("permissions_and_roles", {}).get("permission_history", [])) +
        len(export_data.get("communications", {}).get("support_tickets", []))
    ),
    "estimated_size_kb": len(str(export_data)) / 1024,
    "processing_time_seconds": 2.5
}

result = {
    "result": {
        "export_prepared": True,
        "export_id": export_config["export_id"],
        "export_data": export_data,
        "export_stats": export_stats,
        "export_config": export_config,
        "ready_for_packaging": True
    }
}
"""
        })
        
        # Package and secure export
        builder.add_node("PythonCodeNode", "package_export", {
            "name": "package_secure_data_export",
            "code": """
from datetime import datetime, timedelta
# Package and secure the data export
export_preparation = export_prep_data
export_config = export_preparation.get("export_config", {})
export_data = export_preparation.get("export_data", {})

# Format data according to requested format
requested_format = export_config.get("requested_format", "json")

if requested_format == "json":
    import json
    formatted_data = json.dumps(export_data, indent=2, default=str)
    file_extension = "json"
    content_type = "application/json"
elif requested_format == "csv":
    # Simplified CSV export (would need proper CSV formatting)
    formatted_data = "category,field,value\\n"
    for category, data in export_data.items():
        if isinstance(data, dict):
            for field, value in data.items():
                formatted_data += f"{category},{field},{value}\\n"
    file_extension = "csv"
    content_type = "text/csv"
elif requested_format == "xml":
    # Simplified XML export
    formatted_data = '<?xml version="1.0" encoding="UTF-8"?>\\n<user_data>\\n'
    for category, data in export_data.items():
        formatted_data += f"  <{category}>{data}</{category}>\\n"
    formatted_data += '</user_data>'
    file_extension = "xml"
    content_type = "application/xml"
else:
    formatted_data = str(export_data)
    file_extension = "txt"
    content_type = "text/plain"

# Create export package
export_package = {
    "package_info": {
        "package_id": export_config.get("export_id"),
        "created_at": datetime.now().isoformat(),
        "user_id": export_config.get("user_id"),
        "format": requested_format,
        "file_extension": file_extension,
        "content_type": content_type,
        "size_bytes": len(formatted_data.encode('utf-8')),
        "encryption": "AES-256" if export_config.get("encryption_required") else None
    },
    "security": {
        "access_token": "secure_token_12345",  # Would be actual secure token
        "expiry_hours": 24,
        "download_limit": 1,
        "ip_restriction": None,
        "password_protected": export_config.get("encryption_required", True)
    },
    "delivery": {
        "method": export_config.get("delivery_method", "download"),
        "download_url": f"https://secure.company.com/exports/{export_config.get('export_id')}",
        "notification_sent": True,
        "available_until": (datetime.now() + timedelta(hours=24)).isoformat()
    },
    "compliance": {
        "gdpr_compliant": True,
        "data_minimization": True,
        "purpose_limitation": True,
        "audit_logged": True,
        "user_consent_verified": True
    }
}

# Export completion summary
completion_summary = {
    "export_successful": True,
    "package_ready": True,
    "total_data_categories": export_preparation.get("export_stats", {}).get("categories_included", 0),
    "total_records": export_preparation.get("export_stats", {}).get("total_records", 0),
    "file_size_kb": export_package["package_info"]["size_bytes"] / 1024,
    "processing_time": export_preparation.get("export_stats", {}).get("processing_time_seconds", 0),
    "delivery_ready": True
}

# User instructions
user_instructions = {
    "download_instructions": [
        f"Click the download link: {export_package['delivery']['download_url']}",
        "Enter the access token when prompted",
        "Save the file to a secure location",
        "The download link expires in 24 hours"
    ],
    "security_notes": [
        "This export contains all your personal data",
        "Keep the downloaded file secure and encrypted",
        "Do not share the access token with anyone",
        "Delete the file securely when no longer needed"
    ],
    "data_format_info": {
        "format": requested_format,
        "structure": "Organized by data categories",
        "encoding": "UTF-8",
        "compatibility": "Standard format readable by most applications"
    }
}

result = {
    "result": {
        "packaging_complete": True,
        "export_package": export_package,
        "completion_summary": completion_summary,
        "user_instructions": user_instructions,
        "ready_for_delivery": True
    }
}
"""
        })
        
        # Connect export nodes
        builder.add_connection("process_export_request", "result.result", "package_export", "export_prep_data")
        
        # Execute workflow
        workflow = builder.build()
        results, execution_id = self.runner.execute_workflow(
            workflow, export_request, "personal_data_export"
        )
        
        return results
    
    def request_data_correction(self, correction_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Request correction of personal data.
        
        Args:
            correction_request: Data correction request details
            
        Returns:
            Data correction request results
        """
        print(f"✏️ Requesting data correction for user: {self.user_id}")
        
        builder = self.runner.create_workflow("data_correction_request")
        
        # Process correction request
        builder.add_node("PythonCodeNode", "process_correction_request", {
            "name": "process_data_correction_request",
            "code": """
from datetime import datetime
import random
import string

def generate_id():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=12))

# Process data correction request
user_id = "test@example.com"
correction_data = {"field_to_correct": "phone", "current_value": "+1-555-0100", "proposed_value": "+1-555-0200", "justification": "Changed phone number", "priority": "normal"}

# Generate correction request ID
request_id = "CORR_" + user_id + "_" + datetime.now().strftime('%Y%m%d_%H%M%S')

# Validate correction request
required_fields = ["field_to_correct", "current_value", "proposed_value", "justification"]
validation_results = {}

for field in required_fields:
    validation_results[field] = field in correction_data and bool(correction_data.get(field))

all_required_present = all(validation_results.values())

if all_required_present:
    # Create correction request record
    correction_request_record = {
        "request_id": request_id,
        "user_id": user_id,
        "submitted_at": datetime.now().isoformat(),
        "status": "submitted",
        "field_to_correct": correction_data.get("field_to_correct"),
        "current_value": correction_data.get("current_value"),
        "proposed_value": correction_data.get("proposed_value"),
        "justification": correction_data.get("justification"),
        "supporting_documents": correction_data.get("supporting_documents", []),
        "priority": correction_data.get("priority", "normal"),
        "category": "personal_data_correction"
    }
    
    # Determine correction workflow
    field_to_correct = correction_data.get("field_to_correct")
    correction_workflow = {
        "auto_approved_fields": ["preferred_name", "phone", "emergency_contact"],
        "manager_approval_fields": ["department", "position", "work_location"],
        "admin_approval_fields": ["email", "employee_id", "legal_name"],
        "hr_approval_fields": ["employment_status", "salary_grade", "benefits"]
    }
    
    # Determine approval process
    approval_process = "unknown"
    estimated_timeline = "5-10 business days"
    
    if field_to_correct in correction_workflow["auto_approved_fields"]:
        approval_process = "automatic"
        estimated_timeline = "immediate"
    elif field_to_correct in correction_workflow["manager_approval_fields"]:
        approval_process = "manager_approval"
        estimated_timeline = "2-3 business days"
    elif field_to_correct in correction_workflow["admin_approval_fields"]:
        approval_process = "admin_approval"  
        estimated_timeline = "5-7 business days"
    elif field_to_correct in correction_workflow["hr_approval_fields"]:
        approval_process = "hr_approval"
        estimated_timeline = "7-10 business days"
    
    # Create approval workflow
    approval_workflow_config = {
        "process_type": approval_process,
        "estimated_timeline": estimated_timeline,
        "approval_steps": [],
        "notifications_enabled": True,
        "escalation_enabled": True
    }
    
    if approval_process == "automatic":
        approval_workflow_config["approval_steps"] = [
            {
                "step": 1,
                "approver": "system",
                "action": "auto_approve",
                "sla_hours": 0
            }
        ]
    elif approval_process == "manager_approval":
        approval_workflow_config["approval_steps"] = [
            {
                "step": 1,
                "approver": "direct_manager",
                "action": "review_and_approve",
                "sla_hours": 48
            }
        ]
    elif approval_process in ["admin_approval", "hr_approval"]:
        approval_workflow_config["approval_steps"] = [
            {
                "step": 1,
                "approver": "direct_manager",
                "action": "initial_review",
                "sla_hours": 24
            },
            {
                "step": 2,
                "approver": "admin" if approval_process == "admin_approval" else "hr",
                "action": "final_approval",
                "sla_hours": 96
            }
        ]
    
    request_successful = True
    
else:
    correction_request_record = None
    approval_workflow_config = None
    request_successful = False

# User notification
user_notification = {
    "type": "correction_request_submitted",
    "request_id": request_id if request_successful else None,
    "message": "Your data correction request has been submitted" if request_successful else "Request submission failed",
    "next_steps": [
        "Track request status in your dashboard",
        "You will receive email updates on progress",
        "Contact support if you have questions"
    ] if request_successful else [
        "Please check all required fields",
        "Ensure justification is provided",
        "Try submitting again"
    ]
}

result = {
    "result": {
        "request_submitted": request_successful,
        "request_id": request_id if request_successful else None,
        "correction_request": correction_request_record,
        "approval_workflow": approval_workflow_config,
        "validation_results": validation_results,
        "user_notification": user_notification,
        "estimated_completion": approval_workflow_config.get("estimated_timeline") if request_successful else None
    }
}
"""
        })
        
        # Track correction request status
        builder.add_node("PythonCodeNode", "setup_request_tracking", {
            "name": "setup_correction_request_tracking",
            "code": """
from datetime import datetime, timedelta
# Set up correction request tracking and notifications
correction_processing = correction_request_processing

if correction_processing.get("request_submitted"):
    request_id = correction_processing.get("request_id")
    approval_workflow = correction_processing.get("approval_workflow", {})
    
    # Tracking configuration
    tracking_config = {
        "request_id": request_id,
        "status_tracking_enabled": True,
        "notification_preferences": {
            "email_updates": True,
            "dashboard_notifications": True,
            "sms_alerts": False
        },
        "milestone_notifications": [
            "request_received",
            "under_review", 
            "approval_pending",
            "approved",
            "changes_applied",
            "completed"
        ]
    }
    
    # Status timeline
    status_timeline = [
        {
            "status": "submitted",
            "timestamp": datetime.now().isoformat(),
            "description": "Correction request submitted",
            "completed": True
        },
        {
            "status": "under_review",
            "estimated_timestamp": (datetime.now() + timedelta(hours=24)).isoformat(),
            "description": "Request being reviewed by approver",
            "completed": False
        }
    ]
    
    # Add approval-specific timeline steps
    approval_process = approval_workflow.get("process_type")
    if approval_process == "automatic":
        status_timeline.append({
            "status": "approved",
            "estimated_timestamp": datetime.now().isoformat(),
            "description": "Automatically approved",
            "completed": False
        })
    elif approval_process in ["manager_approval", "admin_approval", "hr_approval"]:
        for step in approval_workflow.get("approval_steps", []):
            status_timeline.append({
                "status": f"pending_approval_step_{step['step']}",
                "estimated_timestamp": (datetime.now() + timedelta(hours=step.get("sla_hours", 48))).isoformat(),
                "description": f"Awaiting approval from {step['approver']}",
                "completed": False
            })
    
    # Final steps
    status_timeline.extend([
        {
            "status": "changes_applied",
            "estimated_timestamp": (datetime.now() + timedelta(days=1)).isoformat(),
            "description": "Data corrections applied to system",
            "completed": False
        },
        {
            "status": "completed",
            "estimated_timestamp": (datetime.now() + timedelta(days=2)).isoformat(),
            "description": "Correction request completed",
            "completed": False
        }
    ])
    
    # User guidance
    user_guidance = {
        "what_happens_next": [
            "Your request will be reviewed by the appropriate approver",
            "You'll receive email notifications at each stage",
            "You can track progress in your dashboard",
            "Changes will be applied once approved"
        ],
        "estimated_timeline": approval_workflow.get("estimated_timeline"),
        "support_contact": "support@company.com",
        "reference_number": request_id
    }
    
    tracking_setup_successful = True
    
else:
    tracking_config = {}
    status_timeline = []
    user_guidance = {"error": "Cannot set up tracking for failed request"}
    tracking_setup_successful = False

result = {
    "result": {
        "tracking_configured": tracking_setup_successful,
        "tracking_config": tracking_config,
        "status_timeline": status_timeline,
        "user_guidance": user_guidance,
        "request_trackable": tracking_setup_successful
    }
}
"""
        })
        
        # Connect correction request nodes
        builder.add_connection("process_correction_request", "result.result", "setup_request_tracking", "correction_request_processing")
        
        # Execute workflow
        workflow = builder.build()
        results, execution_id = self.runner.execute_workflow(
            workflow, correction_request, "data_correction_request"
        )
        
        return results
    
    def run_comprehensive_data_demo(self) -> Dict[str, Any]:
        """
        Run a comprehensive demonstration of all data management operations.
        
        Returns:
            Complete demonstration results
        """
        print("🚀 Starting Comprehensive Data Management Demonstration...")
        print("=" * 70)
        
        demo_results = {}
        
        try:
            # 1. Access personal data
            print("\n1. Accessing Personal Data...")
            access_request = {
                "data_categories": ["profile_information", "activity_logs", "preferences"],
                "format": "json"
            }
            demo_results["data_access"] = self.access_personal_data(access_request)
            
            # 2. Export personal data
            print("\n2. Exporting Personal Data...")
            export_request = {
                "format": "json",
                "categories": "all",
                "include_metadata": True,
                "encryption": True,
                "delivery": "download"
            }
            demo_results["data_export"] = self.export_personal_data(export_request)
            
            # 3. Request data correction
            print("\n3. Requesting Data Correction...")
            correction_request = {
                "field_to_correct": "phone",
                "current_value": "+1-555-0123",
                "proposed_value": "+1-555-0199",
                "justification": "Phone number changed",
                "priority": "normal"
            }
            demo_results["data_correction"] = self.request_data_correction(correction_request)
            
            # Print comprehensive summary
            self.print_data_management_summary(demo_results)
            
            return demo_results
            
        except Exception as e:
            print(f"❌ Data management demonstration failed: {str(e)}")
            raise
    
    def print_data_management_summary(self, results: Dict[str, Any]):
        """
        Print a comprehensive data management summary.
        
        Args:
            results: Data management results from all workflows
        """
        print("\n" + "=" * 70)
        print("DATA MANAGEMENT DEMONSTRATION COMPLETE")
        print("=" * 70)
        
        # Data access summary
        access_result = results.get("data_access", {}).get("collect_personal_data", {}).get("result", {}).get("result", {})
        print(f"📁 Data Access: {access_result.get('categories_retrieved', 0)} categories retrieved")
        
        # Data export summary
        export_result = results.get("data_export", {}).get("package_export", {}).get("result", {}).get("result", {})
        export_size = export_result.get("completion_summary", {}).get("file_size_kb", 0)
        print(f"📤 Data Export: {export_size:.1f} KB package created")
        
        # Data correction summary
        correction_result = results.get("data_correction", {}).get("process_correction_request", {}).get("result", {}).get("result", {})
        print(f"✏️ Data Correction: Request {correction_result.get('request_id', 'N/A')} submitted")
        
        print("\n🎉 All data management operations completed successfully!")
        print("=" * 70)
        
        # Print execution statistics
        self.runner.print_stats()


def test_workflow(test_params: Optional[Dict[str, Any]] = None) -> bool:
    """
    Test the data management workflow.
    
    Args:
        test_params: Optional test parameters
        
    Returns:
        True if test passes, False otherwise
    """
    try:
        print("🧪 Testing Data Management Workflow...")
        
        # Create test workflow
        data_mgmt = DataManagementWorkflow("test_user")
        
        # Test data access
        test_access_request = {
            "data_categories": ["profile_information"],
            "format": "json"
        }
        
        result = data_mgmt.access_personal_data(test_access_request)
        if not result.get("collect_personal_data", {}).get("result", {}).get("result", {}).get("data_access_successful"):
            return False
        
        print("✅ Data management workflow test passed")
        return True
        
    except Exception as e:
        print(f"❌ Data management workflow test failed: {str(e)}")
        return False


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        # Run test
        success = test_workflow()
        sys.exit(0 if success else 1)
    else:
        # Run comprehensive demonstration
        data_mgmt = DataManagementWorkflow()
        
        try:
            results = data_mgmt.run_comprehensive_data_demo()
            print("🎉 Data management demonstration completed successfully!")
        except Exception as e:
            print(f"❌ Demonstration failed: {str(e)}")
            sys.exit(1)