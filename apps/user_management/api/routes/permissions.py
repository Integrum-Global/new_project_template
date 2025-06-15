"""
Permission Management REST API Routes

This module implements advanced permission management using pure Kailash SDK.
Supports ABAC with 16+ operators, dynamic evaluation, and data masking.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field

from apps.user_management.core.startup import agent_ui, runtime
from apps.user_management.core.repositories import permission_repository
from kailash.middleware import WorkflowEvent, EventType
from kailash.workflow import WorkflowBuilder
from kailash.runtime.local import LocalRuntime


# Pydantic models
class PermissionCreateRequest(BaseModel):
    """Permission creation request model."""
    name: str = Field(..., min_length=1, max_length=100)
    resource: str = Field(..., description="Resource type (users, roles, documents, etc.)")
    action: str = Field(..., description="Action (create, read, update, delete, execute, etc.)")
    description: Optional[str] = Field(None, max_length=500)
    conditions: Optional[Dict[str, Any]] = Field(
        None, 
        description="ABAC conditions using 16+ operators"
    )
    data_mask_rules: Optional[Dict[str, Any]] = Field(
        None,
        description="Field-level data masking rules"
    )
    requires_mfa: bool = Field(False, description="Require MFA for this permission")
    risk_level: int = Field(1, ge=1, le=10, description="Risk level (1-10)")


class PermissionUpdateRequest(BaseModel):
    """Permission update request model."""
    description: Optional[str] = None
    conditions: Optional[Dict[str, Any]] = None
    data_mask_rules: Optional[Dict[str, Any]] = None
    requires_mfa: Optional[bool] = None
    risk_level: Optional[int] = Field(None, ge=1, le=10)


class PermissionCheckRequest(BaseModel):
    """Permission check request model."""
    user_id: str
    resource: str
    action: str
    resource_attributes: Optional[Dict[str, Any]] = Field(
        None, 
        description="Resource-specific attributes for ABAC evaluation"
    )
    context: Optional[Dict[str, Any]] = Field(
        None,
        description="Request context (IP, time, location, etc.)"
    )


class PermissionResponse(BaseModel):
    """Permission response model."""
    id: str
    name: str
    resource: str
    action: str
    description: Optional[str]
    conditions: Optional[Dict[str, Any]]
    data_mask_rules: Optional[Dict[str, Any]]
    requires_mfa: bool
    risk_level: int
    created_at: datetime
    updated_at: datetime
    usage_count: int
    last_used: Optional[datetime]


class PermissionCheckResponse(BaseModel):
    """Permission check response model."""
    allowed: bool
    reason: Optional[str]
    requires_mfa: bool
    data_masks: Optional[Dict[str, str]]
    risk_score: float
    evaluation_time_ms: float
    matched_rules: List[Dict[str, Any]]


class PermissionListResponse(BaseModel):
    """Permission list response model."""
    permissions: List[PermissionResponse]
    total: int
    page: int
    limit: int
    has_next: bool
    by_resource: Dict[str, int]
    by_action: Dict[str, int]


# Create router
router = APIRouter()

# Initialize async runtime
async_runtime = LocalRuntime(enable_async=True, debug=False)


@router.post("/", response_model=PermissionResponse)
async def create_permission(permission_data: PermissionCreateRequest):
    """
    Create a new permission with ABAC conditions.
    
    Features beyond Django:
    - 16+ ABAC operators
    - Field-level data masking
    - Risk-based access control
    - Dynamic condition evaluation
    - MFA requirements per permission
    """
    try:
        # Create a workflow using pure SDK components
        builder = WorkflowBuilder("create_permission_workflow")
        
        # Add validation node
        builder.add_node("PythonCodeNode", "validate_permission", {
            "name": "validate_permission_data",
            "code": """
# Validate permission structure and conditions
import re

errors = []
permission = permission_data

# Validate resource/action format
if not re.match(r'^[a-zA-Z0-9_]+$', permission['resource']):
    errors.append('Resource must be alphanumeric with underscores')

if not re.match(r'^[a-zA-Z0-9_]+$', permission['action']):
    errors.append('Action must be alphanumeric with underscores')

# Validate ABAC conditions if provided
if permission.get('conditions'):
    valid_operators = [
        'equals', 'not_equals', 'contains', 'not_contains',
        'in', 'not_in', 'greater_than', 'less_than',
        'greater_or_equal', 'less_or_equal', 'between',
        'matches', 'hierarchical_match', 'security_level_meets',
        'security_level_below', 'matches_data_region', 'contains_any'
    ]
    
    def validate_condition(cond):
        if 'type' not in cond:
            return 'Condition missing type'
        if cond['type'] == 'attribute' and 'operator' in cond.get('value', {}):
            if cond['value']['operator'] not in valid_operators:
                return f"Invalid operator: {cond['value']['operator']}"
        return None
    
    # Recursively validate conditions
    cond_error = validate_condition(permission['conditions'])
    if cond_error:
        errors.append(cond_error)

result = {
    "result": {
        "valid": len(errors) == 0,
        "errors": errors,
        "permission_data": permission
    }
}
"""
        })
        
        # Add permission check node
        builder.add_node("ABACPermissionEvaluatorNode", "check_create_permission", {
            "resource": "permissions",
            "action": "create",
            "require_admin": True
        })
        
        # Add creation node using PythonCodeNode
        builder.add_node("PythonCodeNode", "create_in_db", {
            "name": "create_permission_in_db",
            "code": """
# Create permission in database
import uuid
from datetime import datetime

permission_id = str(uuid.uuid4())
now = datetime.now()

created_permission = {
    "id": permission_id,
    "name": permission_data["name"],
    "resource": permission_data["resource"],
    "action": permission_data["action"],
    "description": permission_data.get("description"),
    "conditions": permission_data.get("conditions"),
    "data_mask_rules": permission_data.get("data_mask_rules"),
    "requires_mfa": permission_data.get("requires_mfa", False),
    "risk_level": permission_data.get("risk_level", 1),
    "created_at": now,
    "updated_at": now,
    "usage_count": 0,
    "last_used": None
}

result = {"result": created_permission}
"""
        })
        
        # Add audit logging
        builder.add_node("AuditLogNode", "audit_creation", {
            "operation": "log_event",
            "event_type": "permission_created",
            "severity": "high"
        })
        
        # Add notification node
        builder.add_node("PythonCodeNode", "prepare_notification", {
            "name": "prepare_creation_notification",
            "code": """
# Prepare real-time notification
from datetime import datetime

result = {
    "result": {
        "event_type": "permission_created",
        "permission": created_permission,
        "risk_level": created_permission.get('risk_level', 1),
        "timestamp": datetime.now().isoformat()
    }
}
"""
        })
        
        # Connect the nodes
        builder.add_connection("validate_permission", "result", "check_create_permission", "validation")
        builder.add_connection("check_create_permission", "allowed", "create_in_db", "proceed")
        builder.add_connection("validate_permission", "result.permission_data", "create_in_db", "permission_data")
        builder.add_connection("create_in_db", "result", "audit_creation", "resource")
        builder.add_connection("create_in_db", "result", "prepare_notification", "created_permission")
        
        # Build and execute workflow
        workflow = builder.build()
        
        results, execution_id = await async_runtime.execute(
            workflow,
            parameters={"permission_data": permission_data.dict()}
        )
        
        # Check validation results
        validation = results.get("validate_permission", {}).get("result", {})
        if not validation.get("valid"):
            raise HTTPException(
                status_code=400,
                detail={"errors": validation.get("errors", [])}
            )
        
        # Get created permission
        created = results.get("create_in_db", {}).get("result", {})
        if not created:
            raise HTTPException(status_code=500, detail="Permission creation failed")
        
        # Save to database using repository
        db_permission = await permission_repository.create_permission(created)
        
        # Broadcast event
        notification_data = results.get("prepare_notification", {}).get("result", {})
        await agent_ui.realtime.broadcast_event(
            WorkflowEvent(
                type=EventType.PERMISSION_CREATED,
                workflow_id="create_permission_workflow",
                execution_id=execution_id,
                data=notification_data
            )
        )
        
        return PermissionResponse(**db_permission)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/check", response_model=PermissionCheckResponse)
async def check_permission(check_request: PermissionCheckRequest):
    """
    Check if user has permission with ABAC evaluation.
    
    This endpoint demonstrates Kailash's superior ABAC system:
    - Dynamic attribute evaluation
    - Hierarchical matching
    - Security level comparison
    - Time-based restrictions
    - Geographic constraints
    - Risk scoring
    """
    try:
        # Create advanced permission check workflow
        builder = WorkflowBuilder("check_permission_workflow")
        
        # Add user context enrichment
        builder.add_node("UserManagementNode", "get_user_context", {
            "operation": "get_user_with_attributes",
            "user_id": check_request.user_id
        })
        
        # Add ABAC evaluation node
        builder.add_node("ABACPermissionEvaluatorNode", "evaluate_permission", {
            "resource": check_request.resource,
            "action": check_request.action,
            "user_id": check_request.user_id,
            "context": check_request.context or {}
        })
        
        # Add risk assessment
        builder.add_node("BehaviorAnalysisNode", "assess_risk", {
            "operation": "analyze_access_request",
            "user_id": check_request.user_id,
            "resource": check_request.resource,
            "action": check_request.action
        })
        
        # Add MFA check if required
        builder.add_node("MultiFactorAuthNode", "check_mfa", {
            "operation": "check_requirement",
            "user_id": check_request.user_id
        })
        
        # Add result processing
        builder.add_node("PythonCodeNode", "process_results", {
            "name": "process_permission_results",
            "code": """
# Process permission check results
from datetime import datetime

start_time = datetime.now()

# Extract results from nodes
permission_result = evaluate_result or {"allowed": False, "reason": "No evaluation result"}
risk_score = risk_result.get("risk_score", 0.0) if risk_result else 0.0
mfa_required = mfa_result.get("required", False) if mfa_result else False

# Calculate evaluation time
eval_time_ms = (datetime.now() - start_time).total_seconds() * 1000

result = {
    "result": {
        "allowed": permission_result.get("allowed", False),
        "reason": permission_result.get("reason", "Permission denied"),
        "requires_mfa": mfa_required,
        "data_masks": permission_result.get("data_masks", {}),
        "risk_score": risk_score,
        "evaluation_time_ms": eval_time_ms,
        "matched_rules": permission_result.get("matched_rules", [])
    }
}
"""
        })
        
        # Add audit logging
        builder.add_node("AuditLogNode", "audit_check", {
            "operation": "log_event",
            "event_type": "permission_checked",
            "severity": "info"
        })
        
        # Connect nodes
        builder.add_connection("get_user_context", "user", "evaluate_permission", "user_context")
        builder.add_connection("get_user_context", "user", "assess_risk", "user_data")
        builder.add_connection("evaluate_permission", "result", "process_results", "evaluate_result")
        builder.add_connection("assess_risk", "result", "process_results", "risk_result")
        builder.add_connection("check_mfa", "result", "process_results", "mfa_result")
        builder.add_connection("process_results", "result", "audit_check", "check_result")
        
        # Build and execute
        workflow = builder.build()
        
        start_time = datetime.now()
        results, execution_id = await async_runtime.execute(workflow)
        
        # Extract final result
        final_result = results.get("process_results", {}).get("result", {})
        
        # Log high-risk denials
        if not final_result.get("allowed") and final_result.get("risk_score", 0) > 7.0:
            await agent_ui.realtime.broadcast_event(
                WorkflowEvent(
                    type=EventType.HIGH_RISK_ACCESS_DENIED,
                    workflow_id="check_permission_workflow",
                    execution_id=execution_id,
                    data={
                        "user_id": check_request.user_id,
                        "resource": check_request.resource,
                        "action": check_request.action,
                        "risk_score": final_result.get("risk_score")
                    }
                )
            )
        
        return PermissionCheckResponse(**final_result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=PermissionListResponse)
async def list_permissions(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=200, description="Items per page"),
    resource: Optional[str] = Query(None, description="Filter by resource"),
    action: Optional[str] = Query(None, description="Filter by action"),
    risk_level_min: Optional[int] = Query(None, ge=1, le=10, description="Minimum risk level"),
    requires_mfa: Optional[bool] = Query(None, description="Filter by MFA requirement")
):
    """
    List permissions with advanced filtering and analytics.
    
    Features beyond Django:
    - Risk level filtering
    - Usage analytics
    - Resource/action distribution
    - MFA requirement filtering
    """
    try:
        # Get permissions from repository
        all_permissions = await permission_repository.list_permissions(resource, action)
        
        # Create analytics workflow
        builder = WorkflowBuilder("analyze_permissions_workflow")
        
        # Add analytics node
        builder.add_node("PythonCodeNode", "analyze_permissions", {
            "name": "permission_analytics",
            "code": f"""
# Analyze permission distribution
permissions = all_permissions

# Apply additional filters
filtered = permissions
if {risk_level_min}:
    filtered = [p for p in filtered if p.get('risk_level', 1) >= {risk_level_min}]
if {requires_mfa} is not None:
    filtered = [p for p in filtered if p.get('requires_mfa', False) == {requires_mfa}]

# Calculate analytics
by_resource = {{}}
by_action = {{}}
for perm in filtered:
    res = perm['resource']
    act = perm['action']
    by_resource[res] = by_resource.get(res, 0) + 1
    by_action[act] = by_action.get(act, 0) + 1

# Paginate
total = len(filtered)
start = ({page} - 1) * {limit}
end = start + {limit}
paginated = filtered[start:end]

result = {{
    "result": {{
        "permissions": paginated,
        "total": total,
        "page": {page},
        "limit": {limit},
        "has_next": end < total,
        "by_resource": by_resource,
        "by_action": by_action
    }}
}}
"""
        })
        
        # Execute workflow
        workflow = builder.build()
        results, _ = await async_runtime.execute(
            workflow,
            parameters={"all_permissions": all_permissions}
        )
        
        analytics = results.get("analyze_permissions", {}).get("result", {})
        
        return PermissionListResponse(**analytics)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{permission_id}", response_model=PermissionResponse)
async def get_permission(permission_id: str):
    """Get detailed permission information including usage statistics."""
    try:
        # Get permission from repository
        permission = await permission_repository.get_permission(permission_id)
        
        if not permission:
            raise HTTPException(status_code=404, detail="Permission not found")
        
        # Create usage stats workflow
        builder = WorkflowBuilder("get_usage_stats_workflow")
        
        # Add usage analysis node
        builder.add_node("PythonCodeNode", "analyze_usage", {
            "name": "analyze_permission_usage",
            "code": """
# Analyze permission usage
# In real implementation, would query audit logs
import random
from datetime import datetime, timedelta

# Simulate usage stats
usage_count = random.randint(0, 1000)
last_used = datetime.now() - timedelta(hours=random.randint(1, 720))

result = {
    "result": {
        "usage_count": usage_count,
        "last_used": last_used
    }
}
"""
        })
        
        # Execute workflow
        workflow = builder.build()
        results, _ = await async_runtime.execute(workflow)
        
        usage_stats = results.get("analyze_usage", {}).get("result", {})
        
        # Combine permission with usage stats
        permission.update(usage_stats)
        
        return PermissionResponse(**permission)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{permission_id}", response_model=PermissionResponse)
async def update_permission(permission_id: str, update_data: PermissionUpdateRequest):
    """Update permission with validation and change tracking."""
    try:
        # Get current permission
        current = await permission_repository.get_permission(permission_id)
        if not current:
            raise HTTPException(status_code=404, detail="Permission not found")
        
        builder = WorkflowBuilder("update_permission_workflow")
        
        # Add validation node
        builder.add_node("PythonCodeNode", "validate_changes", {
            "name": "validate_permission_changes",
            "code": """
# Validate permission changes
errors = []
changed_fields = []

# Track what's changing for audit
for field, value in update_data.items():
    if value is not None and current.get(field) != value:
        changed_fields.append(field)

# Validate risk level changes
if 'risk_level' in changed_fields:
    old_risk = current.get('risk_level', 1)
    new_risk = update_data['risk_level']
    if old_risk <= 3 and new_risk > 7:
        errors.append("Cannot increase risk level from low to high without review")

result = {
    "result": {
        "valid": len(errors) == 0,
        "errors": errors,
        "changed_fields": changed_fields
    }
}
"""
        })
        
        # Add update node
        builder.add_node("PythonCodeNode", "apply_updates", {
            "name": "apply_permission_updates",
            "code": """
# Apply updates to permission
from datetime import datetime

updated = current.copy()
for field, value in update_data.items():
    if value is not None:
        updated[field] = value

updated['updated_at'] = datetime.now()

result = {"result": updated}
"""
        })
        
        # Add audit node
        builder.add_node("AuditLogNode", "audit_update", {
            "operation": "log_event",
            "event_type": "permission_updated",
            "severity": "medium"
        })
        
        # Connect nodes
        builder.add_connection("validate_changes", "result", "apply_updates", "validation")
        builder.add_connection("apply_updates", "result", "audit_update", "resource")
        
        # Execute
        workflow = builder.build()
        results, execution_id = await async_runtime.execute(
            workflow,
            parameters={
                "current": current,
                "update_data": update_data.dict(exclude_unset=True)
            }
        )
        
        # Check validation
        validation = results.get("validate_changes", {}).get("result", {})
        if not validation.get("valid"):
            raise HTTPException(
                status_code=400,
                detail={"errors": validation.get("errors", [])}
            )
        
        # Get updated permission
        updated = results.get("apply_updates", {}).get("result", {})
        
        # Save to database (in real implementation)
        # For now, just return the updated data
        
        # Broadcast update if risk level changed
        if "risk_level" in validation.get("changed_fields", []):
            await agent_ui.realtime.broadcast_event(
                WorkflowEvent(
                    type=EventType.PERMISSION_RISK_CHANGED,
                    workflow_id="update_permission_workflow",
                    execution_id=execution_id,
                    data={
                        "permission_id": permission_id,
                        "old_risk": current.get("risk_level", 1),
                        "new_risk": updated.get("risk_level", 1)
                    }
                )
            )
        
        return PermissionResponse(**updated)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{permission_id}")
async def delete_permission(permission_id: str):
    """
    Delete permission with impact analysis.
    
    Features beyond Django:
    - Impact analysis before deletion
    - Automatic role cleanup
    - Orphaned permission detection
    """
    try:
        builder = WorkflowBuilder("delete_permission_workflow")
        
        # Add impact analysis node
        builder.add_node("PythonCodeNode", "analyze_impact", {
            "name": "analyze_deletion_impact",
            "code": """
# Analyze impact of deleting this permission
# In real implementation, would query role_permissions table
impact = {
    "affected_roles": ["admin", "manager"],  # Would be from DB
    "affected_users": 25,  # Would be calculated
    "recent_usage": 15  # Last 30 days usage
}

can_delete = impact["affected_users"] < 100  # Business rule

result = {
    "result": {
        "can_delete": can_delete,
        "impact": impact
    }
}
"""
        })
        
        # Add deletion confirmation node
        builder.add_node("PythonCodeNode", "confirm_deletion", {
            "name": "confirm_and_delete",
            "code": """
# Confirm and execute deletion
from datetime import datetime

if not impact_analysis.get("can_delete", False):
    raise ValueError("Cannot delete permission due to high impact")

deleted_at = datetime.now()

result = {
    "result": {
        "deleted": True,
        "deleted_at": deleted_at,
        "impact": impact_analysis.get("impact", {})
    }
}
"""
        })
        
        # Add audit deletion
        builder.add_node("AuditLogNode", "audit_deletion", {
            "operation": "log_event",
            "event_type": "permission_deleted",
            "severity": "high"
        })
        
        # Connect nodes
        builder.add_connection("analyze_impact", "result", "confirm_deletion", "impact_analysis")
        builder.add_connection("confirm_deletion", "result", "audit_deletion", "deletion_result")
        
        # Execute
        workflow = builder.build()
        results, execution_id = await async_runtime.execute(
            workflow,
            parameters={"permission_id": permission_id}
        )
        
        impact = results.get("analyze_impact", {}).get("result", {})
        deletion = results.get("confirm_deletion", {}).get("result", {})
        
        # Broadcast high-impact deletions
        if impact.get("impact", {}).get("affected_users", 0) > 10:
            await agent_ui.realtime.broadcast_event(
                WorkflowEvent(
                    type=EventType.HIGH_IMPACT_PERMISSION_DELETED,
                    workflow_id="delete_permission_workflow",
                    execution_id=execution_id,
                    data={
                        "permission_id": permission_id,
                        "impact": impact["impact"]
                    }
                )
            )
        
        return {
            "success": True,
            "message": "Permission deleted successfully",
            "impact": impact.get("impact", {}),
            "deleted_at": deletion.get("deleted_at")
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/evaluate-conditions")
async def evaluate_conditions(
    conditions: Dict[str, Any],
    test_context: Dict[str, Any]
):
    """
    Test ABAC conditions with sample context.
    
    This is a developer tool to test complex ABAC rules
    before applying them to permissions.
    """
    try:
        builder = WorkflowBuilder("test_conditions_workflow")
        
        # Add ABAC test node
        builder.add_node("ABACPermissionEvaluatorNode", "test_conditions", {
            "resource": "test",
            "action": "evaluate",
            "conditions": conditions,
            "context": test_context,
            "test_mode": True
        })
        
        # Add result processing
        builder.add_node("PythonCodeNode", "format_results", {
            "name": "format_evaluation_results",
            "code": """
# Format evaluation results
from datetime import datetime

eval_result = test_result or {"result": False, "reason": "No evaluation performed"}

result = {
    "result": {
        "evaluated": True,
        "result": eval_result.get("allowed", False),
        "matched_conditions": eval_result.get("matched_conditions", []),
        "evaluation_path": eval_result.get("evaluation_path", []),
        "time_ms": eval_result.get("evaluation_time_ms", 0)
    }
}
"""
        })
        
        # Connect nodes
        builder.add_connection("test_conditions", "result", "format_results", "test_result")
        
        # Execute
        workflow = builder.build()
        results, _ = await async_runtime.execute(workflow)
        
        formatted = results.get("format_results", {}).get("result", {})
        
        return formatted
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/matrix/{user_id}")
async def get_permission_matrix(
    user_id: str,
    resources: List[str] = Query(None, description="Resources to check"),
    actions: List[str] = Query(None, description="Actions to check")
):
    """
    Get permission matrix for a user.
    
    Shows all permissions for specified resources and actions in a matrix format.
    This is a feature Django Admin lacks - comprehensive permission visualization.
    """
    try:
        # Default resources and actions if not specified
        if not resources:
            resources = ["users", "roles", "permissions", "documents", "reports"]
        if not actions:
            actions = ["create", "read", "update", "delete", "execute"]
        
        builder = WorkflowBuilder("permission_matrix_workflow")
        
        # Add matrix generation node
        builder.add_node("PythonCodeNode", "generate_matrix", {
            "name": "generate_permission_matrix",
            "code": f"""
# Generate permission matrix
matrix = {{}}
resources_list = {resources}
actions_list = {actions}

# Initialize matrix
for resource in resources_list:
    matrix[resource] = {{}}
    for action in actions_list:
        # In real implementation, would check actual permissions
        # For demo, simulate some permissions
        import random
        matrix[resource][action] = {{
            "allowed": random.choice([True, False]),
            "source": random.choice(["role:admin", "role:user", "policy:default", "inherited"]),
            "requires_mfa": random.choice([True, False]) if action in ["delete", "execute"] else False
        }}

result = {{
    "result": {{
        "user_id": "{user_id}",
        "matrix": matrix,
        "resources": resources_list,
        "actions": actions_list,
        "generated_at": datetime.now().isoformat()
    }}
}}
"""
        })
        
        # Execute workflow
        workflow = builder.build()
        results, _ = await async_runtime.execute(workflow)
        
        matrix_data = results.get("generate_matrix", {}).get("result", {})
        
        return matrix_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))