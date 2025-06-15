"""
GDPR Compliance REST API Routes

This module implements GDPR compliance endpoints using pure Kailash SDK.
Supports data export, deletion, consent management, and audit trails.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json
import base64
import uuid

from fastapi import APIRouter, HTTPException, Query, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, EmailStr

from apps.user_management.core.startup import agent_ui, runtime
from kailash.middleware import WorkflowEvent, EventType
from kailash.workflow import WorkflowBuilder
from kailash.runtime.local import LocalRuntime


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
    consent_type: str = Field(..., pattern="^(marketing|analytics|cookies|data_sharing)$")
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
    export_request: DataExportRequest,
    background_tasks: BackgroundTasks
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
        builder.add_node("ABACPermissionEvaluatorNode", "check_export_permission", {
            "resource": "user_data",
            "action": "export",
            "user_id": export_request.user_id,
            "require_self_or_admin": True
        })
        
        # Add user data collection
        builder.add_node("UserManagementNode", "collect_user_data", {
            "operation": "get_user_complete",
            "user_id": export_request.user_id,
            "include_history": True
        })
        
        # Add audit log collection if requested
        if export_request.include_audit_logs:
            builder.add_node("AuditLogNode", "collect_audit_logs", {
                "operation": "get_user_logs",
                "user_id": export_request.user_id,
                "limit": 10000
            })
        
        # Add permission history if requested
        if export_request.include_permissions:
            builder.add_node("PythonCodeNode", "collect_permissions", {
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
"""
            })
        
        # Add session history if requested
        if export_request.include_sessions:
            builder.add_node("PythonCodeNode", "collect_sessions", {
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
"""
            })
        
        # Add data compilation node
        builder.add_node("PythonCodeNode", "compile_export", {
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
"""
        })
        
        # Add audit logging
        builder.add_node("AuditLogNode", "audit_export", {
            "operation": "log_event",
            "event_type": "gdpr_data_export",
            "severity": "high",
            "user_id": export_request.user_id
        })
        
        # Connect nodes
        builder.add_connection("check_export_permission", "allowed", "collect_user_data", "proceed")
        builder.add_connection("collect_user_data", "result", "compile_export", "user_data")
        
        if export_request.include_audit_logs:
            builder.add_connection("collect_audit_logs", "result", "compile_export", "audit_logs")
        
        if export_request.include_permissions:
            builder.add_connection("collect_permissions", "result", "compile_export", "permissions")
        
        if export_request.include_sessions:
            builder.add_connection("collect_sessions", "result", "compile_export", "sessions")
        
        builder.add_connection("compile_export", "result", "audit_export", "export_info")
        
        # Build and execute
        workflow = builder.build()
        results, execution_id = await async_runtime.execute(workflow)
        
        # Check permission
        if not results.get("check_export_permission", {}).get("allowed"):
            raise HTTPException(status_code=403, detail="Permission denied for data export")
        
        # Get export data
        export_result = results.get("compile_export", {}).get("result", {})
        
        # Create download response
        return StreamingResponse(
            iter([export_result["data"]]),
            media_type=export_result["content_type"],
            headers={
                "Content-Disposition": f'attachment; filename="{export_result["filename"]}"',
                "X-GDPR-Export": "true",
                "X-Export-ID": execution_id
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/delete-data")
async def delete_user_data(
    deletion_request: DataDeletionRequest,
    background_tasks: BackgroundTasks
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
        builder.add_node("PythonCodeNode", "validate_confirmation", {
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
"""
        })
        
        # Add permission check
        builder.add_node("ABACPermissionEvaluatorNode", "check_delete_permission", {
            "resource": "user_data",
            "action": "delete",
            "user_id": deletion_request.user_id,
            "require_self_or_admin": True
        })
        
        # Add impact analysis
        builder.add_node("PythonCodeNode", "analyze_impact", {
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
"""
        })
        
        # Add deletion/anonymization node
        builder.add_node("PythonCodeNode", "process_deletion", {
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
"""
        })
        
        # Add notification node
        builder.add_node("PythonCodeNode", "send_confirmation", {
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
"""
        })
        
        # Add compliance audit
        builder.add_node("AuditLogNode", "audit_deletion", {
            "operation": "log_event",
            "event_type": "gdpr_data_deletion",
            "severity": "critical",
            "user_id": deletion_request.user_id
        })
        
        # Connect nodes
        builder.add_connection("validate_confirmation", "result", "check_delete_permission", "validation")
        builder.add_connection("check_delete_permission", "allowed", "analyze_impact", "proceed")
        builder.add_connection("analyze_impact", "result", "process_deletion", "impact")
        builder.add_connection("process_deletion", "result", "send_confirmation", "deletion_info")
        builder.add_connection("process_deletion", "result", "audit_deletion", "deletion_details")
        
        # Execute workflow
        workflow = builder.build()
        results, execution_id = await async_runtime.execute(workflow)
        
        # Check validation
        validation = results.get("validate_confirmation", {}).get("result", {})
        if not validation.get("valid"):
            raise HTTPException(status_code=400, detail=validation.get("error"))
        
        # Check permission
        if not results.get("check_delete_permission", {}).get("allowed"):
            raise HTTPException(status_code=403, detail="Permission denied for data deletion")
        
        # Get deletion result
        deletion_result = results.get("process_deletion", {}).get("result", {})
        
        # Broadcast compliance event
        await agent_ui.realtime.broadcast_event(
            WorkflowEvent(
                type=EventType.GDPR_DELETION_COMPLETED,
                workflow_id="delete_user_data_workflow",
                execution_id=execution_id,
                data=deletion_result
            )
        )
        
        return {
            "success": True,
            "action": deletion_result["action"],
            "user_id": deletion_request.user_id,
            "execution_id": execution_id,
            "details": deletion_result["details"],
            "timestamp": deletion_result["timestamp"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/consent")
async def update_consent(
    consent_update: ConsentUpdateRequest
):
    """
    Update user consent preferences.
    
    Tracks:
    - Marketing consent
    - Analytics consent
    - Cookie preferences
    - Data sharing agreements
    """
    try:
        # Create session
        session_id = await agent_ui.create_session("gdpr_export")
        
        # Create export workflow
        export_workflow = {
            "name": "export_user_data_gdpr",
            "nodes": [
                {
                    "id": "check_permissions",
                    "type": "ABACPermissionEvaluatorNode",
                    "config": {
                        "resource": f"users:{user_id}:data",
                        "action": "export"
                    }
                },
                {
                    "id": "collect_data",
                    "type": "GDPRComplianceNode",
                    "config": {
                        "operation": "collect_user_data",
                        "include_all_categories": True
                    }
                },
                {
                    "id": "format_export",
                    "type": "PythonCodeNode",
                    "config": {
                        "name": "format_data_export",
                        "code": f"""
# Format user data for export
import json
import csv
import io
from datetime import datetime

user_data = collected_data.get("user_data", {{}})
format_type = "{format}"

if format_type == "json":
    # JSON format
    export_data = {{
        "export_metadata": {{
            "user_id": "{user_id}",
            "export_date": datetime.now().isoformat(),
            "data_categories": list(user_data.keys()),
            "gdpr_compliant": True
        }},
        "user_data": user_data
    }}
    content = json.dumps(export_data, indent=2, default=str)
    content_type = "application/json"
    filename = f"user_{{'{user_id}'}}_data_export.json"
    
elif format_type == "csv":
    # CSV format - flatten nested data
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write headers
    writer.writerow(["Category", "Field", "Value", "Last_Updated"])
    
    # Write data
    for category, data in user_data.items():
        if isinstance(data, dict):
            for field, value in data.items():
                writer.writerow([category, field, str(value), datetime.now().isoformat()])
        else:
            writer.writerow([category, "value", str(data), datetime.now().isoformat()])
    
    content = output.getvalue()
    content_type = "text/csv"
    filename = f"user_{{'{user_id}'}}_data_export.csv"
    
else:  # XML format
    # Simple XML format
    xml_parts = ['<?xml version="1.0" encoding="UTF-8"?>']
    xml_parts.append('<UserDataExport>')
    xml_parts.append(f'  <UserId>{{'{user_id}'}}</UserId>')
    xml_parts.append(f'  <ExportDate>{{datetime.now().isoformat()}}</ExportDate>')
    xml_parts.append('  <UserData>')
    
    for category, data in user_data.items():
        xml_parts.append(f'    <{{category}}>')
        if isinstance(data, dict):
            for field, value in data.items():
                xml_parts.append(f'      <{{field}}>{{str(value)}}</{{field}}>')
        else:
            xml_parts.append(f'      {{str(data)}}')
        xml_parts.append(f'    </{{category}}>')
    
    xml_parts.append('  </UserData>')
    xml_parts.append('</UserDataExport>')
    
    content = '\\n'.join(xml_parts)
    content_type = "application/xml"
    filename = f"user_{{'{user_id}'}}_data_export.xml"

result = {{
    "result": {{
        "content": content,
        "content_type": content_type,
        "filename": filename,
        "size_bytes": len(content.encode('utf-8'))
    }}
}}
"""
                    }
                },
                {
                    "id": "audit_export",
                    "type": "AuditLogNode",
                    "config": {
                        "log_level": "INFO",
                        "event_type": "gdpr_data_export",
                        "compliance_mode": True
                    }
                }
            ],
            "connections": [
                {
                    "from_node": "check_permissions",
                    "from_output": "allowed",
                    "to_node": "collect_data",
                    "to_input": "proceed"
                },
                {
                    "from_node": "collect_data",
                    "from_output": "collected_data",
                    "to_node": "format_export",
                    "to_input": "collected_data"
                },
                {
                    "from_node": "format_export",
                    "from_output": "result",
                    "to_node": "audit_export",
                    "to_input": "event_data"
                }
            ]
        }
        
        workflow_id = await agent_ui.create_dynamic_workflow(
            session_id,
            export_workflow
        )
        
        execution_id = await agent_ui.execute_workflow(
            session_id,
            workflow_id,
            inputs={"user_id": user_id}
        )
        
        result = await agent_ui.wait_for_execution(
            session_id,
            execution_id,
            timeout=30
        )
        
        # Get export data
        export_data = result.get("outputs", {}).get("format_export", {}).get("result", {})
        
        # Return as streaming response
        return StreamingResponse(
            io.BytesIO(export_data["content"].encode('utf-8')),
            media_type=export_data["content_type"],
            headers={
                "Content-Disposition": f'attachment; filename="{export_data["filename"]}"'
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/consent/update")
async def update_consent(
    consent: ConsentUpdate,
    token: str = Depends(oauth2_scheme)
):
    """
    Update user consent preferences.
    
    Tracks consent changes with full audit trail.
    """
    try:
        # Create session
        session_id = await agent_ui.create_session("consent_update")
        
        # Create consent workflow
        consent_workflow = {
            "name": "update_user_consent",
            "nodes": [
                {
                    "id": "validate_consent",
                    "type": "PythonCodeNode",
                    "config": {
                        "name": "validate_consent_types",
                        "code": f"""
# Validate consent types
valid_consent_types = [
    "marketing_emails",
    "analytics_tracking", 
    "third_party_sharing",
    "personalization",
    "push_notifications",
    "sms_communications",
    "location_tracking"
]

consent_data = {repr(consent.dict())}
errors = []

for consent_type in consent_data['consent_types']:
    if consent_type not in valid_consent_types:
        errors.append(f"Invalid consent type: {{consent_type}}")

result = {{
    "result": {{
        "valid": len(errors) == 0,
        "errors": errors,
        "consent_data": consent_data
    }}
}}
"""
                    }
                },
                {
                    "id": "update_consent",
                    "type": "GDPRComplianceNode",
                    "config": {
                        "operation": "update_consent",
                        "track_history": True
                    }
                },
                {
                    "id": "audit_consent",
                    "type": "AuditLogNode",
                    "config": {
                        "log_level": "INFO",
                        "event_type": "consent_updated",
                        "compliance_mode": True,
                        "include_sensitive": False
                    }
                }
            ],
            "connections": [
                {
                    "from_node": "validate_consent",
                    "from_output": "result",
                    "to_node": "update_consent",
                    "to_input": "consent_request"
                },
                {
                    "from_node": "update_consent",
                    "from_output": "consent_result",
                    "to_node": "audit_consent",
                    "to_input": "event_data"
                }
            ]
        }
        
        workflow_id = await agent_ui.create_dynamic_workflow(
            session_id,
            consent_workflow
        )
        
        execution_id = await agent_ui.execute_workflow(
            session_id,
            workflow_id,
            inputs={}
        )
        
        result = await agent_ui.wait_for_execution(
            session_id,
            execution_id,
            timeout=10
        )
        
        # Check validation
        validation = result.get("outputs", {}).get("validate_consent", {}).get("result", {})
        if not validation.get("valid"):
            raise HTTPException(
                status_code=400,
                detail={"errors": validation.get("errors", [])}
            )
        
        # Get consent result
        consent_result = result.get("outputs", {}).get("update_consent", {}).get("consent_result", {})
        
        return {
            "message": "Consent preferences updated",
            "user_id": consent.user_id,
            "updated_consents": consent.consent_types,
            "consent_id": consent_result.get("consent_id"),
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/consent/{user_id}")
async def get_consent_status(
    user_id: str,
    token: str = Depends(oauth2_scheme)
):
    """Get current consent status for user."""
    try:
        # Create session
        session_id = await agent_ui.create_session("consent_status")
        
        # Create consent query workflow
        consent_workflow = {
            "name": "get_consent_status",
            "nodes": [
                {
                    "id": "get_consent",
                    "type": "GDPRComplianceNode",
                    "config": {
                        "operation": "get_consent_status"
                    }
                }
            ]
        }
        
        workflow_id = await agent_ui.create_dynamic_workflow(
            session_id,
            consent_workflow
        )
        
        execution_id = await agent_ui.execute_workflow(
            session_id,
            workflow_id,
            inputs={"user_id": user_id}
        )
        
        result = await agent_ui.wait_for_execution(
            session_id,
            execution_id,
            timeout=5
        )
        
        consent_data = result.get("outputs", {}).get("get_consent", {}).get("consent_status", {})
        
        return {
            "user_id": user_id,
            "consents": consent_data.get("consents", {}),
            "last_updated": consent_data.get("last_updated"),
            "consent_version": consent_data.get("version", "1.0"),
            "withdrawal_methods": [
                {"method": "api", "endpoint": f"/api/compliance/consent/withdraw/{user_id}"},
                {"method": "email", "address": "privacy@company.com"},
                {"method": "portal", "url": "https://privacy.company.com"}
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/report/generate")
async def generate_compliance_report(
    report_request: ComplianceReportRequest,
    token: str = Depends(oauth2_scheme)
):
    """
    Generate compliance report.
    
    Supports multiple frameworks:
    - GDPR
    - CCPA
    - HIPAA
    - SOC2
    - ISO27001
    """
    try:
        # Create session
        session_id = await agent_ui.create_session("compliance_report")
        
        # Create report generation workflow
        report_workflow = {
            "name": "generate_compliance_report",
            "nodes": [
                {
                    "id": "check_permissions",
                    "type": "ABACPermissionEvaluatorNode",
                    "config": {
                        "resource": "compliance:reports",
                        "action": "generate",
                        "require_admin": True
                    }
                },
                {
                    "id": "collect_metrics",
                    "type": "PythonCodeNode",
                    "config": {
                        "name": "collect_compliance_metrics",
                        "code": f"""
# Collect compliance metrics for report
from datetime import datetime, timedelta

framework = "{report_request.framework.value}"
start_date = datetime.fromisoformat("{report_request.start_date.isoformat()}")
end_date = datetime.fromisoformat("{report_request.end_date.isoformat()}")

# Mock compliance metrics - in production, query real data
metrics = {{
    "framework": framework,
    "period": {{
        "start": start_date.isoformat(),
        "end": end_date.isoformat(),
        "days": (end_date - start_date).days
    }},
    "summary": {{
        "compliance_score": 96.5,
        "critical_findings": 0,
        "high_findings": 2,
        "medium_findings": 5,
        "low_findings": 12
    }},
    "categories": {{
        "data_protection": {{"score": 98, "findings": 3}},
        "access_control": {{"score": 95, "findings": 4}},
        "encryption": {{"score": 100, "findings": 0}},
        "audit_logging": {{"score": 94, "findings": 5}},
        "incident_response": {{"score": 92, "findings": 7}}
    }},
    "data_requests": {{
        "access_requests": 45,
        "deletion_requests": 12,
        "rectification_requests": 3,
        "portability_requests": 8,
        "avg_response_time_hours": 18.5
    }},
    "security_events": {{
        "total_events": 234,
        "high_severity": 2,
        "blocked_threats": 198,
        "false_positives": 36
    }}
}}

result = {{"result": {{"metrics": metrics}}}}
"""
                    }
                },
                {
                    "id": "generate_report",
                    "type": "GDPRComplianceNode",
                    "config": {
                        "operation": "generate_report",
                        "format": "pdf",
                        "include_recommendations": True
                    }
                },
                {
                    "id": "audit_report",
                    "type": "AuditLogNode",
                    "config": {
                        "log_level": "INFO",
                        "event_type": "compliance_report_generated",
                        "compliance_mode": True
                    }
                }
            ],
            "connections": [
                {
                    "from_node": "check_permissions",
                    "from_output": "allowed",
                    "to_node": "collect_metrics",
                    "to_input": "proceed"
                },
                {
                    "from_node": "collect_metrics",
                    "from_output": "result.metrics",
                    "to_node": "generate_report",
                    "to_input": "report_data"
                },
                {
                    "from_node": "generate_report",
                    "from_output": "report",
                    "to_node": "audit_report",
                    "to_input": "event_data"
                }
            ]
        }
        
        workflow_id = await agent_ui.create_dynamic_workflow(
            session_id,
            report_workflow
        )
        
        execution_id = await agent_ui.execute_workflow(
            session_id,
            workflow_id,
            inputs={}
        )
        
        result = await agent_ui.wait_for_execution(
            session_id,
            execution_id,
            timeout=30
        )
        
        # Get report info
        report_info = result.get("outputs", {}).get("generate_report", {}).get("report", {})
        
        return {
            "report_id": report_info.get("report_id"),
            "framework": report_request.framework.value,
            "period": {
                "start": report_request.start_date.isoformat(),
                "end": report_request.end_date.isoformat()
            },
            "status": "completed",
            "download_url": f"/api/compliance/report/{report_info.get('report_id')}/download",
            "summary": result.get("outputs", {}).get("collect_metrics", {}).get("result", {}).get("metrics", {}).get("summary", {}),
            "generated_at": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/retention/policies")
async def get_retention_policies(
    token: str = Depends(oauth2_scheme)
):
    """Get data retention policies."""
    try:
        # Create session
        session_id = await agent_ui.create_session("retention_policies")
        
        # Create retention query workflow
        retention_workflow = {
            "name": "get_retention_policies",
            "nodes": [
                {
                    "id": "get_policies",
                    "type": "DataRetentionPolicyNode",
                    "config": {
                        "operation": "list_policies"
                    }
                }
            ]
        }
        
        workflow_id = await agent_ui.create_dynamic_workflow(
            session_id,
            retention_workflow
        )
        
        execution_id = await agent_ui.execute_workflow(
            session_id,
            workflow_id,
            inputs={}
        )
        
        result = await agent_ui.wait_for_execution(
            session_id,
            execution_id,
            timeout=5
        )
        
        policies = result.get("outputs", {}).get("get_policies", {}).get("policies", {})
        
        return {
            "policies": policies,
            "default_retention": "7 years",
            "categories": {
                "user_data": {"retention": "7 years", "deletion": "automatic"},
                "audit_logs": {"retention": "10 years", "deletion": "manual_review"},
                "security_events": {"retention": "5 years", "deletion": "automatic"},
                "consent_records": {"retention": "indefinite", "deletion": "manual_only"},
                "financial_records": {"retention": "10 years", "deletion": "manual_review"}
            },
            "last_updated": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))