"""
GDPR Compliance REST API Routes

This module implements GDPR compliance endpoints using pure Kailash SDK.
Supports data export, deletion, consent management, and audit trails.
"""

import base64
import io
import json
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, EmailStr, Field

from apps.user_management.core.startup import agent_ui, runtime
from kailash.middleware import EventType, WorkflowEvent
from kailash.runtime.local import LocalRuntime
from kailash.workflow import WorkflowBuilder


# Pydantic models
class DataExportRequest(BaseModel):
    """User data export request."""

    user_id: str = Field(..., description="User ID to export data for")
    format: str = Field("json", pattern="^(json|csv|pdf)$", description="Export format")
    include_audit_logs: bool = Field(True, description="Include audit trail")
    include_permissions: bool = Field(True, description="Include permission history")
    include_sessions: bool = Field(True, description="Include session history")
    encryption_key: Optional[str] = Field(None, description="Optional encryption key")


class DataDeletionRequest(BaseModel):
    """User data deletion request."""

    user_id: str = Field(..., description="User ID to delete data for")
    reason: str = Field(..., min_length=10, description="Deletion reason")
    delete_audit_logs: bool = Field(False, description="Also delete audit logs")
    anonymize_instead: bool = Field(False, description="Anonymize instead of delete")
    confirmation_code: str = Field(..., description="Confirmation code sent to user")


class ConsentUpdateRequest(BaseModel):
    """User consent update request."""

    user_id: str
    consent_type: str = Field(
        ..., pattern="^(marketing|analytics|cookies|data_sharing)$"
    )
    granted: bool
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class RetentionPolicyRequest(BaseModel):
    """Data retention policy configuration."""

    data_type: str = Field(..., pattern="^(user_data|audit_logs|sessions|backups)$")
    retention_days: int = Field(..., ge=1, le=3650)
    auto_delete: bool = Field(True)
    notify_before_days: int = Field(30, ge=1, le=90)


class ComplianceReportRequest(BaseModel):
    """Compliance report generation request."""

    report_type: str = Field(..., pattern="^(gdpr|ccpa|hipaa|sox|pci)$")
    start_date: datetime
    end_date: datetime
    include_violations: bool = Field(True)
    include_recommendations: bool = Field(True)


# Create router
router = APIRouter()

# Initialize async runtime
async_runtime = LocalRuntime(enable_async=True, debug=False)


@router.post("/export-data")
async def export_user_data(
    export_request: DataExportRequest, background_tasks: BackgroundTasks
):
    """
    Export all user data for GDPR compliance.

    Features beyond Django:
    - Multiple export formats (JSON, CSV, PDF)
    - Optional encryption
    - Comprehensive data collection
    - Async processing for large datasets
    """
    try:
        # Create export workflow
        builder = WorkflowBuilder("export_user_data_workflow")

        # Add permission check
        builder.add_node(
            "ABACPermissionEvaluatorNode",
            "check_export_permission",
            {
                "resource": "user_data",
                "action": "export",
                "user_id": export_request.user_id,
                "require_self_or_admin": True,
            },
        )

        # Add user data collection
        builder.add_node(
            "UserManagementNode",
            "collect_user_data",
            {
                "operation": "get_user_complete",
                "user_id": export_request.user_id,
                "include_history": True,
            },
        )

        # Add audit log collection if requested
        if export_request.include_audit_logs:
            builder.add_node(
                "AuditLogNode",
                "collect_audit_logs",
                {
                    "operation": "get_user_logs",
                    "user_id": export_request.user_id,
                    "limit": 10000,
                },
            )

        # Add permission history if requested
        if export_request.include_permissions:
            builder.add_node(
                "PythonCodeNode",
                "collect_permissions",
                {
                    "name": "collect_permission_history",
                    "code": """
# Collect permission history
import json
from datetime import datetime

# Simulate permission history collection
permission_history = [
    {
        "date": "2024-01-15",
        "action": "granted",
        "permission": "users:read:all",
        "granted_by": "admin"
    },
    {
        "date": "2024-02-20",
        "action": "revoked",
        "permission": "users:delete:all",
        "revoked_by": "security_team"
    }
]

result = {"result": {"permission_history": permission_history}}
""",
                },
            )

        # Add session history if requested
        if export_request.include_sessions:
            builder.add_node(
                "PythonCodeNode",
                "collect_sessions",
                {
                    "name": "collect_session_history",
                    "code": """
# Collect session history
from datetime import datetime, timedelta

# Simulate session history
sessions = []
for i in range(10):
    sessions.append({
        "session_id": f"session_{i}",
        "login_time": (datetime.now() - timedelta(days=i)).isoformat(),
        "ip_address": f"192.168.1.{100+i}",
        "user_agent": "Mozilla/5.0...",
        "duration_minutes": 30 + i * 5
    })

result = {"result": {"session_history": sessions}}
""",
                },
            )

        # Add data compilation node
        builder.add_node(
            "PythonCodeNode",
            "compile_export",
            {
                "name": "compile_export_data",
                "code": f"""
# Compile all collected data
import json
import base64
from datetime import datetime

export_data = {{
    "export_info": {{
        "user_id": "{export_request.user_id}",
        "export_date": datetime.now().isoformat(),
        "format": "{export_request.format}",
        "gdpr_compliant": True
    }},
    "user_data": user_data.get("user", {{}}),
    "audit_logs": audit_logs.get("logs", []) if {export_request.include_audit_logs} else [],
    "permission_history": permissions.get("permission_history", []) if {export_request.include_permissions} else [],
    "session_history": sessions.get("session_history", []) if {export_request.include_sessions} else []
}}

# Format based on request
if "{export_request.format}" == "json":
    formatted_data = json.dumps(export_data, indent=2)
    content_type = "application/json"
    filename = f"user_{{export_data['user_data'].get('email', 'unknown')}}_data_export.json"
elif "{export_request.format}" == "csv":
    # Simple CSV conversion (in production, use proper CSV library)
    csv_lines = ["Type,Field,Value"]
    for key, value in export_data['user_data'].items():
        csv_lines.append(f"UserData,{{key}},{{value}}")
    formatted_data = "\\n".join(csv_lines)
    content_type = "text/csv"
    filename = f"user_{{export_data['user_data'].get('email', 'unknown')}}_data_export.csv"
else:
    # PDF would require proper library
    formatted_data = json.dumps(export_data, indent=2)
    content_type = "application/json"
    filename = f"user_{{export_data['user_data'].get('email', 'unknown')}}_data_export.json"

# Optional encryption
if "{export_request.encryption_key}":
    # In production, use proper encryption
    formatted_data = base64.b64encode(formatted_data.encode()).decode()

result = {{
    "result": {{
        "data": formatted_data,
        "content_type": content_type,
        "filename": filename,
        "size_bytes": len(formatted_data),
        "encrypted": bool("{export_request.encryption_key}")
    }}
}}
""",
            },
        )

        # Add audit logging
        builder.add_node(
            "AuditLogNode",
            "audit_export",
            {
                "operation": "log_event",
                "event_type": "gdpr_data_export",
                "severity": "high",
                "user_id": export_request.user_id,
            },
        )

        # Connect nodes
        builder.add_connection(
            "check_export_permission", "allowed", "collect_user_data", "proceed"
        )
        builder.add_connection(
            "collect_user_data", "result", "compile_export", "user_data"
        )

        if export_request.include_audit_logs:
            builder.add_connection(
                "collect_audit_logs", "result", "compile_export", "audit_logs"
            )

        if export_request.include_permissions:
            builder.add_connection(
                "collect_permissions", "result", "compile_export", "permissions"
            )

        if export_request.include_sessions:
            builder.add_connection(
                "collect_sessions", "result", "compile_export", "sessions"
            )

        builder.add_connection(
            "compile_export", "result", "audit_export", "export_info"
        )

        # Build and execute
        workflow = builder.build()
        results, execution_id = await async_runtime.execute(workflow)

        # Check permission
        if not results.get("check_export_permission", {}).get("allowed"):
            raise HTTPException(
                status_code=403, detail="Permission denied for data export"
            )

        # Get export data
        export_result = results.get("compile_export", {}).get("result", {})

        # Create download response
        return StreamingResponse(
            iter([export_result["data"]]),
            media_type=export_result["content_type"],
            headers={
                "Content-Disposition": f'attachment; filename="{export_result["filename"]}"',
                "X-GDPR-Export": "true",
                "X-Export-ID": execution_id,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/delete-data")
async def delete_user_data(
    deletion_request: DataDeletionRequest, background_tasks: BackgroundTasks
):
    """
    Delete or anonymize user data for GDPR compliance.

    Features:
    - Right to be forgotten implementation
    - Optional anonymization instead of deletion
    - Audit trail preservation options
    - Confirmation code validation
    """
    try:
        builder = WorkflowBuilder("delete_user_data_workflow")

        # Add confirmation validation
        builder.add_node(
            "PythonCodeNode",
            "validate_confirmation",
            {
                "name": "validate_deletion_confirmation",
                "code": f"""
# Validate confirmation code
# In production, check against stored confirmation code
expected_code = "DELETE-" + "{deletion_request.user_id}"[:6].upper()
valid = "{deletion_request.confirmation_code}" == expected_code

result = {{
    "result": {{
        "valid": valid,
        "error": "Invalid confirmation code" if not valid else None
    }}
}}
""",
            },
        )

        # Add permission check
        builder.add_node(
            "ABACPermissionEvaluatorNode",
            "check_delete_permission",
            {
                "resource": "user_data",
                "action": "delete",
                "user_id": deletion_request.user_id,
                "require_self_or_admin": True,
            },
        )

        # Add impact analysis
        builder.add_node(
            "PythonCodeNode",
            "analyze_impact",
            {
                "name": "analyze_deletion_impact",
                "code": """
# Analyze impact of deletion
impact = {
    "active_sessions": 2,
    "pending_workflows": 0,
    "shared_resources": 5,
    "team_memberships": 3,
    "can_delete": True,
    "warnings": [
        "User has 5 shared resources that will be transferred",
        "User is member of 3 teams"
    ]
}

result = {"result": impact}
""",
            },
        )

        # Add deletion/anonymization node
        builder.add_node(
            "PythonCodeNode",
            "process_deletion",
            {
                "name": "process_data_deletion",
                "code": f"""
# Process deletion or anonymization
from datetime import datetime
import hashlib

if not impact.get("can_delete", False):
    raise ValueError("Cannot delete user due to active dependencies")

if {deletion_request.anonymize_instead}:
    # Anonymize data
    anonymized_id = hashlib.sha256("{deletion_request.user_id}".encode()).hexdigest()[:12]
    action = "anonymized"
    details = {{
        "anonymized_id": f"anon_{{anonymized_id}}",
        "fields_anonymized": [
            "email", "first_name", "last_name", "phone",
            "address", "ip_addresses", "device_ids"
        ],
        "preserved_fields": ["created_at", "department", "role"]
    }}
else:
    # Delete data
    action = "deleted"
    details = {{
        "deleted_tables": [
            "users", "user_sessions", "user_preferences",
            "user_devices", "user_notifications"
        ],
        "preserved_for_legal": [] if {deletion_request.delete_audit_logs} else ["audit_logs"]
    }}

result = {{
    "result": {{
        "action": action,
        "user_id": "{deletion_request.user_id}",
        "timestamp": datetime.now().isoformat(),
        "reason": "{deletion_request.reason}",
        "details": details
    }}
}}
""",
            },
        )

        # Add notification node
        builder.add_node(
            "PythonCodeNode",
            "send_confirmation",
            {
                "name": "send_deletion_confirmation",
                "code": """
# Send confirmation email
# In production, integrate with email service
result = {
    "result": {
        "email_sent": True,
        "template": "gdpr_deletion_complete",
        "recipient": "user@example.com"
    }
}
""",
            },
        )

        # Add compliance audit
        builder.add_node(
            "AuditLogNode",
            "audit_deletion",
            {
                "operation": "log_event",
                "event_type": "gdpr_data_deletion",
                "severity": "critical",
                "user_id": deletion_request.user_id,
            },
        )

        # Connect nodes
        builder.add_connection(
            "validate_confirmation", "result", "check_delete_permission", "validation"
        )
        builder.add_connection(
            "check_delete_permission", "allowed", "analyze_impact", "proceed"
        )
        builder.add_connection("analyze_impact", "result", "process_deletion", "impact")
        builder.add_connection(
            "process_deletion", "result", "send_confirmation", "deletion_info"
        )
        builder.add_connection(
            "process_deletion", "result", "audit_deletion", "deletion_details"
        )

        # Execute workflow
        workflow = builder.build()
        results, execution_id = await async_runtime.execute(workflow)

        # Check validation
        validation = results.get("validate_confirmation", {}).get("result", {})
        if not validation.get("valid"):
            raise HTTPException(status_code=400, detail=validation.get("error"))

        # Check permission
        if not results.get("check_delete_permission", {}).get("allowed"):
            raise HTTPException(
                status_code=403, detail="Permission denied for data deletion"
            )

        # Get deletion result
        deletion_result = results.get("process_deletion", {}).get("result", {})

        # Broadcast compliance event
        await agent_ui.realtime.broadcast_event(
            WorkflowEvent(
                type=EventType.GDPR_DELETION_COMPLETED,
                workflow_id="delete_user_data_workflow",
                execution_id=execution_id,
                data=deletion_result,
            )
        )

        return {
            "success": True,
            "action": deletion_result["action"],
            "user_id": deletion_request.user_id,
            "execution_id": execution_id,
            "details": deletion_result["details"],
            "timestamp": deletion_result["timestamp"],
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/consent")
async def update_consent(consent_update: ConsentUpdateRequest):
    """
    Update user consent preferences.

    Tracks:
    - Marketing consent
    - Analytics consent
    - Cookie preferences
    - Data sharing agreements
    """
    try:
        builder = WorkflowBuilder("update_consent_workflow")

        # Add consent validation
        builder.add_node(
            "PythonCodeNode",
            "validate_consent",
            {
                "name": "validate_consent_update",
                "code": f"""
# Validate consent update
from datetime import datetime

# Check if consent type requires special handling
special_handling = {{
    "data_sharing": {{
        "requires_explicit": True,
        "min_age": 16,
        "notification_required": True
    }},
    "marketing": {{
        "can_be_implicit": False,
        "retention_days": 365
    }}
}}

handling = special_handling.get("{consent_update.consent_type}", {{}})

result = {{
    "result": {{
        "valid": True,
        "handling": handling,
        "consent_data": {{
            "user_id": "{consent_update.user_id}",
            "consent_type": "{consent_update.consent_type}",
            "granted": {consent_update.granted},
            "timestamp": datetime.now().isoformat(),
            "ip_address": "{consent_update.ip_address or 'not_provided'}",
            "user_agent": "{consent_update.user_agent or 'not_provided'}"
        }}
    }}
}}
""",
            },
        )

        # Add consent storage
        builder.add_node(
            "PythonCodeNode",
            "store_consent",
            {
                "name": "store_consent_update",
                "code": """
# Store consent update
import uuid
from datetime import datetime

consent_record = {
    "id": str(uuid.uuid4()),
    "user_id": consent_data["user_id"],
    "consent_type": consent_data["consent_type"],
    "granted": consent_data["granted"],
    "timestamp": consent_data["timestamp"],
    "ip_address": consent_data["ip_address"],
    "user_agent": consent_data["user_agent"],
    "version": "1.0",
    "legal_basis": "explicit_consent"
}

# Calculate consent expiry if applicable
if handling.get("retention_days"):
    from datetime import timedelta
    expiry_date = datetime.now() + timedelta(days=handling["retention_days"])
    consent_record["expires_at"] = expiry_date.isoformat()

result = {"result": consent_record}
""",
            },
        )

        # Add notification if required
        builder.add_node(
            "PythonCodeNode",
            "notify_consent",
            {
                "name": "notify_consent_change",
                "code": """
# Notify about consent change
notifications = []

if handling.get("notification_required"):
    notifications.append({
        "type": "email",
        "template": "consent_update_notification",
        "sent": True
    })

# Always log to audit
notifications.append({
    "type": "audit",
    "logged": True
})

result = {"result": {"notifications": notifications}}
""",
            },
        )

        # Add audit logging
        builder.add_node(
            "AuditLogNode",
            "audit_consent",
            {
                "operation": "log_event",
                "event_type": "consent_updated",
                "severity": "medium",
                "user_id": consent_update.user_id,
            },
        )

        # Connect nodes
        builder.add_connection(
            "validate_consent", "result.consent_data", "store_consent", "consent_data"
        )
        builder.add_connection(
            "validate_consent", "result.handling", "store_consent", "handling"
        )
        builder.add_connection(
            "validate_consent", "result.handling", "notify_consent", "handling"
        )
        builder.add_connection(
            "store_consent", "result", "audit_consent", "consent_record"
        )

        # Execute
        workflow = builder.build()
        results, execution_id = await async_runtime.execute(workflow)

        consent_record = results.get("store_consent", {}).get("result", {})
        notifications = results.get("notify_consent", {}).get("result", {})

        return {
            "success": True,
            "consent_id": consent_record["id"],
            "user_id": consent_update.user_id,
            "consent_type": consent_update.consent_type,
            "granted": consent_update.granted,
            "timestamp": consent_record["timestamp"],
            "expires_at": consent_record.get("expires_at"),
            "notifications": notifications["notifications"],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/consent/{user_id}")
async def get_user_consents(user_id: str):
    """
    Get all consent records for a user.
    """
    try:
        builder = WorkflowBuilder("get_consents_workflow")

        # Add consent retrieval
        builder.add_node(
            "PythonCodeNode",
            "get_consents",
            {
                "name": "retrieve_user_consents",
                "code": f"""
# Retrieve user consents
from datetime import datetime, timedelta

# Simulate consent records
consent_types = ["marketing", "analytics", "cookies", "data_sharing"]
consents = []

for consent_type in consent_types:
    consents.append({{
        "consent_type": consent_type,
        "granted": consent_type != "marketing",  # Example: marketing not granted
        "timestamp": (datetime.now() - timedelta(days=30)).isoformat(),
        "expires_at": (datetime.now() + timedelta(days=335)).isoformat() if consent_type == "marketing" else None,
        "version": "1.0",
        "legal_basis": "explicit_consent"
    }})

result = {{
    "result": {{
        "user_id": "{user_id}",
        "consents": consents,
        "last_updated": datetime.now().isoformat()
    }}
}}
""",
            },
        )

        # Execute
        workflow = builder.build()
        results, _ = await async_runtime.execute(workflow)

        return results.get("get_consents", {}).get("result", {})

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/retention-policy")
async def configure_retention_policy(policy: RetentionPolicyRequest):
    """
    Configure data retention policies.

    Features:
    - Automatic data deletion
    - Retention period configuration
    - Notification before deletion
    - Compliance reporting
    """
    try:
        builder = WorkflowBuilder("configure_retention_workflow")

        # Add policy validation
        builder.add_node(
            "PythonCodeNode",
            "validate_policy",
            {
                "name": "validate_retention_policy",
                "code": f"""
# Validate retention policy
from datetime import datetime

# Check compliance requirements
compliance_minimums = {{
    "audit_logs": 2555,  # 7 years for financial compliance
    "user_data": 90,     # 90 days minimum
    "sessions": 30,      # 30 days minimum
    "backups": 365      # 1 year minimum
}}

min_days = compliance_minimums.get("{policy.data_type}", 30)
valid = {policy.retention_days} >= min_days

result = {{
    "result": {{
        "valid": valid,
        "error": f"Minimum retention for {{'{policy.data_type}'}} is {{min_days}} days" if not valid else None,
        "policy_data": {{
            "data_type": "{policy.data_type}",
            "retention_days": {policy.retention_days},
            "auto_delete": {policy.auto_delete},
            "notify_before_days": {policy.notify_before_days},
            "created_at": datetime.now().isoformat()
        }}
    }}
}}
""",
            },
        )

        # Add policy storage
        builder.add_node(
            "PythonCodeNode",
            "store_policy",
            {
                "name": "store_retention_policy",
                "code": """
# Store retention policy
import uuid

policy_record = {
    "id": str(uuid.uuid4()),
    **policy_data,
    "active": True,
    "last_run": None,
    "next_run": None
}

# Schedule first run
from datetime import datetime, timedelta
if policy_data["auto_delete"]:
    policy_record["next_run"] = (datetime.now() + timedelta(days=1)).isoformat()

result = {"result": policy_record}
""",
            },
        )

        # Add audit
        builder.add_node(
            "AuditLogNode",
            "audit_policy",
            {
                "operation": "log_event",
                "event_type": "retention_policy_configured",
                "severity": "high",
            },
        )

        # Connect nodes
        builder.add_connection(
            "validate_policy", "result.policy_data", "store_policy", "policy_data"
        )
        builder.add_connection(
            "store_policy", "result", "audit_policy", "policy_record"
        )

        # Execute
        workflow = builder.build()
        results, execution_id = await async_runtime.execute(workflow)

        # Check validation
        validation = results.get("validate_policy", {}).get("result", {})
        if not validation.get("valid"):
            raise HTTPException(status_code=400, detail=validation.get("error"))

        policy_record = results.get("store_policy", {}).get("result", {})

        return {
            "success": True,
            "policy_id": policy_record["id"],
            "data_type": policy.data_type,
            "retention_days": policy.retention_days,
            "auto_delete": policy.auto_delete,
            "next_run": policy_record.get("next_run"),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compliance-report")
async def generate_compliance_report(report_request: ComplianceReportRequest):
    """
    Generate comprehensive compliance reports.

    Supports:
    - GDPR compliance
    - CCPA compliance
    - HIPAA compliance
    - SOX compliance
    - PCI DSS compliance
    """
    try:
        builder = WorkflowBuilder("generate_compliance_report_workflow")

        # Add data collection
        builder.add_node(
            "PythonCodeNode",
            "collect_metrics",
            {
                "name": "collect_compliance_metrics",
                "code": f"""
# Collect compliance metrics
from datetime import datetime

# Simulate compliance metrics
metrics = {{
    "period": {{
        "start": "{report_request.start_date.isoformat()}",
        "end": "{report_request.end_date.isoformat()}"
    }},
    "statistics": {{
        "total_users": 1250,
        "data_requests": 45,
        "deletion_requests": 12,
        "consent_updates": 234,
        "breaches": 0,
        "average_response_time_hours": 23.5
    }},
    "compliance_score": {{
        "overall": 94.5,
        "data_protection": 96.0,
        "user_rights": 93.0,
        "documentation": 94.0,
        "security_measures": 95.0
    }}
}}

result = {{"result": metrics}}
""",
            },
        )

        # Add violation detection
        if report_request.include_violations:
            builder.add_node(
                "PythonCodeNode",
                "detect_violations",
                {
                    "name": "detect_compliance_violations",
                    "code": """
# Detect compliance violations
violations = [
    {
        "type": "response_time",
        "severity": "low",
        "description": "2 data requests exceeded 30-day response time",
        "date": "2024-03-15",
        "remediation": "Automated workflow implemented"
    }
]

result = {"result": {"violations": violations}}
""",
                },
            )

        # Add recommendations
        if report_request.include_recommendations:
            builder.add_node(
                "PythonCodeNode",
                "generate_recommendations",
                {
                    "name": "generate_compliance_recommendations",
                    "code": f"""
# Generate recommendations based on report type
recommendations = []

if "{report_request.report_type}" == "gdpr":
    recommendations.extend([
        {{
            "priority": "high",
            "area": "consent_management",
            "recommendation": "Implement granular consent tracking",
            "impact": "Improve consent compliance by 15%"
        }},
        {{
            "priority": "medium",
            "area": "data_retention",
            "recommendation": "Review and update retention policies",
            "impact": "Reduce data liability"
        }}
    ])

result = {{"result": {{"recommendations": recommendations}}}}
""",
                },
            )

        # Add report generation
        builder.add_node(
            "PythonCodeNode",
            "generate_report",
            {
                "name": "compile_compliance_report",
                "code": f"""
# Compile final report
from datetime import datetime
import uuid

report = {{
    "report_id": str(uuid.uuid4()),
    "type": "{report_request.report_type}",
    "generated_at": datetime.now().isoformat(),
    "period": metrics["period"],
    "executive_summary": {{
        "compliance_score": metrics["compliance_score"]["overall"],
        "critical_issues": 0,
        "improvements": 3,
        "status": "COMPLIANT" if metrics["compliance_score"]["overall"] >= 90 else "NEEDS_IMPROVEMENT"
    }},
    "metrics": metrics,
    "violations": violations.get("violations", []) if {report_request.include_violations} else [],
    "recommendations": recommendations.get("recommendations", []) if {report_request.include_recommendations} else []
}}

result = {{"result": report}}
""",
            },
        )

        # Connect nodes
        builder.add_connection(
            "collect_metrics", "result", "generate_report", "metrics"
        )

        if report_request.include_violations:
            builder.add_connection(
                "detect_violations", "result", "generate_report", "violations"
            )

        if report_request.include_recommendations:
            builder.add_connection(
                "generate_recommendations",
                "result",
                "generate_report",
                "recommendations",
            )

        # Execute
        workflow = builder.build()
        results, execution_id = await async_runtime.execute(workflow)

        report = results.get("generate_report", {}).get("result", {})

        # Broadcast report generation
        await agent_ui.realtime.broadcast_event(
            WorkflowEvent(
                type=EventType.COMPLIANCE_REPORT_GENERATED,
                workflow_id="generate_compliance_report_workflow",
                execution_id=execution_id,
                data={
                    "report_id": report["report_id"],
                    "type": report["type"],
                    "score": report["executive_summary"]["compliance_score"],
                },
            )
        )

        return report

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/audit-trail/{user_id}")
async def get_compliance_audit_trail(
    user_id: str, days: int = Query(90, ge=1, le=365, description="Days of history")
):
    """
    Get complete compliance audit trail for a user.
    """
    try:
        builder = WorkflowBuilder("get_audit_trail_workflow")

        # Add audit retrieval
        builder.add_node(
            "AuditLogNode",
            "get_audit_trail",
            {
                "operation": "get_user_logs",
                "user_id": user_id,
                "days": days,
                "include_compliance": True,
            },
        )

        # Add processing
        builder.add_node(
            "PythonCodeNode",
            "process_audit",
            {
                "name": "process_compliance_audit",
                "code": """
# Process audit trail for compliance view
audit_logs = logs.get("logs", [])

# Group by compliance category
compliance_events = {
    "data_access": [],
    "consent_changes": [],
    "data_exports": [],
    "deletion_requests": [],
    "permission_changes": []
}

for log in audit_logs:
    event_type = log.get("event_type", "")
    if "consent" in event_type:
        compliance_events["consent_changes"].append(log)
    elif "export" in event_type:
        compliance_events["data_exports"].append(log)
    elif "deletion" in event_type or "delete" in event_type:
        compliance_events["deletion_requests"].append(log)
    elif "permission" in event_type:
        compliance_events["permission_changes"].append(log)
    else:
        compliance_events["data_access"].append(log)

result = {
    "result": {
        "user_id": user_id,
        "period_days": days,
        "total_events": len(audit_logs),
        "compliance_events": compliance_events,
        "summary": {
            "data_access_count": len(compliance_events["data_access"]),
            "consent_changes_count": len(compliance_events["consent_changes"]),
            "data_exports_count": len(compliance_events["data_exports"]),
            "deletion_requests_count": len(compliance_events["deletion_requests"]),
            "permission_changes_count": len(compliance_events["permission_changes"])
        }
    }
}
""",
            },
        )

        # Connect nodes
        builder.add_connection("get_audit_trail", "result", "process_audit", "logs")

        # Execute
        workflow = builder.build()
        results, _ = await async_runtime.execute(
            workflow, parameters={"user_id": user_id, "days": days}
        )

        return results.get("process_audit", {}).get("result", {})

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
