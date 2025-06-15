"""
Role Management REST API Routes

This module implements role management endpoints using pure Kailash patterns.
Supports RBAC with hierarchical roles and dynamic permissions.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field

from apps.user_management.core.startup import agent_ui
from apps.user_management.api.routes.auth import oauth2_scheme


# Pydantic models
class RoleCreateRequest(BaseModel):
    """Role creation request."""
    name: str = Field(..., min_length=1, max_length=50)
    description: str = Field(..., max_length=200)
    permissions: List[str] = Field(default_factory=list)
    parent_role: Optional[str] = Field(None, description="Parent role for hierarchy")
    is_system_role: bool = Field(False, description="System roles cannot be modified")


class RoleUpdateRequest(BaseModel):
    """Role update request."""
    description: Optional[str] = Field(None, max_length=200)
    permissions: Optional[List[str]] = None
    parent_role: Optional[str] = None


class RoleAssignmentRequest(BaseModel):
    """Role assignment request."""
    user_id: str
    role_name: str
    expires_at: Optional[datetime] = Field(None, description="Optional expiration")
    reason: Optional[str] = Field(None, description="Assignment reason")


class RoleResponse(BaseModel):
    """Role response model."""
    id: str
    name: str
    description: str
    permissions: List[str]
    parent_role: Optional[str]
    is_system_role: bool
    created_at: datetime
    updated_at: datetime
    user_count: int


class RoleListResponse(BaseModel):
    """Role list response."""
    roles: List[RoleResponse]
    total: int
    hierarchy: Dict[str, List[str]]  # Parent -> children mapping


# Create router
router = APIRouter()


@router.post("/", response_model=RoleResponse)
async def create_role(
    role_data: RoleCreateRequest,
    token: str = Depends(oauth2_scheme)
):
    """
    Create a new role.
    
    Features:
    - Hierarchical role support
    - Dynamic permission assignment
    - Audit logging
    - Permission validation
    """
    try:
        # Create session
        session_id = await agent_ui.create_session("role_create")
        
        # Create role creation workflow
        create_workflow = {
            "name": "create_role_dynamic",
            "nodes": [
                {
                    "id": "validate_role",
                    "type": "PythonCodeNode",
                    "config": {
                        "name": "validate_role_data",
                        "code": f"""
# Validate role creation data
import re

errors = []
role_data = {repr(role_data.dict())}

# Validate role name format
if not re.match(r'^[a-zA-Z0-9_-]+$', role_data['name']):
    errors.append("Role name must contain only alphanumeric characters, underscores, and hyphens")

# Check for reserved role names
reserved_names = ['admin', 'superuser', 'root', 'system']
if role_data['name'].lower() in reserved_names and not role_data.get('is_system_role'):
    errors.append(f"Role name '{role_data['name']}' is reserved")

# Validate permissions format
valid_permission_pattern = r'^[a-zA-Z0-9]+:[a-zA-Z0-9]+:[a-zA-Z0-9]+$'
for perm in role_data.get('permissions', []):
    if not re.match(valid_permission_pattern, perm):
        errors.append(f"Invalid permission format: {perm}")

result = {{
    "result": {{
        "valid": len(errors) == 0,
        "errors": errors,
        "role_data": role_data
    }}
}}
"""
                    }
                },
                {
                    "id": "check_permissions",
                    "type": "ABACPermissionEvaluatorNode",
                    "config": {
                        "resource": "roles",
                        "action": "create",
                        "require_admin": True
                    }
                },
                {
                    "id": "create_role",
                    "type": "RoleManagementNode",
                    "config": {
                        "operation": "create_role",
                        "enable_audit": True
                    }
                },
                {
                    "id": "audit_log",
                    "type": "AuditLogNode",
                    "config": {
                        "log_level": "INFO",
                        "event_type": "role_created"
                    }
                }
            ],
            "connections": [
                {
                    "from_node": "validate_role",
                    "from_output": "result",
                    "to_node": "check_permissions",
                    "to_input": "resource_context"
                },
                {
                    "from_node": "check_permissions",
                    "from_output": "allowed",
                    "to_node": "create_role",
                    "to_input": "permission_granted"
                },
                {
                    "from_node": "validate_role",
                    "from_output": "result.role_data",
                    "to_node": "create_role",
                    "to_input": "role_data"
                },
                {
                    "from_node": "create_role",
                    "from_output": "role",
                    "to_node": "audit_log",
                    "to_input": "event_data"
                }
            ]
        }
        
        workflow_id = await agent_ui.create_dynamic_workflow(
            session_id,
            create_workflow
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
        validation_result = result.get("outputs", {}).get("validate_role", {}).get("result", {})
        if not validation_result.get("valid"):
            raise HTTPException(
                status_code=400,
                detail={"errors": validation_result.get("errors", [])}
            )
        
        # Get created role
        role_result = result.get("outputs", {}).get("create_role", {}).get("role", {})
        
        if not role_result:
            raise HTTPException(status_code=500, detail="Role creation failed")
        
        return RoleResponse(**role_result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=RoleListResponse)
async def list_roles(
    token: str = Depends(oauth2_scheme),
    include_system: bool = Query(True, description="Include system roles"),
    include_hierarchy: bool = Query(True, description="Include role hierarchy")
):
    """
    List all roles with optional hierarchy.
    
    Returns:
    - All roles in the system
    - Role hierarchy mapping
    - User counts per role
    """
    try:
        # Create session
        session_id = await agent_ui.create_session("role_list")
        
        # Create role listing workflow
        list_workflow = {
            "name": "list_roles_dynamic",
            "nodes": [
                {
                    "id": "list_roles",
                    "type": "RoleManagementNode",
                    "config": {
                        "operation": "list_roles",
                        "include_user_counts": True
                    }
                },
                {
                    "id": "process_roles",
                    "type": "PythonCodeNode",
                    "config": {
                        "name": "process_role_list",
                        "code": f"""
# Process role list
roles = role_list.get("roles", [])

# Filter system roles if needed
if not {include_system}:
    roles = [r for r in roles if not r.get("is_system_role", False)]

# Build hierarchy
hierarchy = {{}}
if {include_hierarchy}:
    for role in roles:
        parent = role.get("parent_role")
        if parent:
            if parent not in hierarchy:
                hierarchy[parent] = []
            hierarchy[parent].append(role["name"])

# Sort roles by name
roles.sort(key=lambda r: r.get("name", ""))

result = {{
    "result": {{
        "roles": roles,
        "total": len(roles),
        "hierarchy": hierarchy
    }}
}}
"""
                    }
                }
            ],
            "connections": [
                {
                    "from_node": "list_roles",
                    "from_output": "role_list",
                    "to_node": "process_roles",
                    "to_input": "role_list"
                }
            ]
        }
        
        workflow_id = await agent_ui.create_dynamic_workflow(
            session_id,
            list_workflow
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
        
        role_data = result.get("outputs", {}).get("process_roles", {}).get("result", {})
        
        return RoleListResponse(**role_data)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{role_name}", response_model=RoleResponse)
async def get_role(
    role_name: str,
    token: str = Depends(oauth2_scheme)
):
    """Get role by name."""
    try:
        # Create session
        session_id = await agent_ui.create_session("role_get")
        
        # Create get role workflow
        get_workflow = {
            "name": "get_role_by_name",
            "nodes": [
                {
                    "id": "get_role",
                    "type": "RoleManagementNode",
                    "config": {
                        "operation": "get_role"
                    }
                }
            ]
        }
        
        workflow_id = await agent_ui.create_dynamic_workflow(
            session_id,
            get_workflow
        )
        
        execution_id = await agent_ui.execute_workflow(
            session_id,
            workflow_id,
            inputs={"role_name": role_name}
        )
        
        result = await agent_ui.wait_for_execution(
            session_id,
            execution_id,
            timeout=5
        )
        
        role_data = result.get("outputs", {}).get("get_role", {}).get("role")
        
        if not role_data:
            raise HTTPException(status_code=404, detail="Role not found")
        
        return RoleResponse(**role_data)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{role_name}", response_model=RoleResponse)
async def update_role(
    role_name: str,
    update_data: RoleUpdateRequest,
    token: str = Depends(oauth2_scheme)
):
    """
    Update role information.
    
    Note: System roles cannot be modified.
    """
    try:
        # Create session
        session_id = await agent_ui.create_session("role_update")
        
        # Execute role management workflow
        execution_id = await agent_ui.execute_workflow_template(
            session_id,
            "role_management_enterprise",
            inputs={
                "action": "update",
                "role_name": role_name,
                "update_data": update_data.dict(exclude_unset=True)
            }
        )
        
        result = await agent_ui.wait_for_execution(
            session_id,
            execution_id,
            timeout=10
        )
        
        role_result = result.get("outputs", {}).get("manage_role", {}).get("result", {})
        
        if not role_result.get("success"):
            raise HTTPException(
                status_code=400,
                detail=role_result.get("error", "Role update failed")
            )
        
        return RoleResponse(**role_result.get("role", {}))
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{role_name}")
async def delete_role(
    role_name: str,
    token: str = Depends(oauth2_scheme),
    force: bool = Query(False, description="Force delete even if users assigned")
):
    """
    Delete a role.
    
    Note: System roles cannot be deleted.
    """
    try:
        # Create session
        session_id = await agent_ui.create_session("role_delete")
        
        # Create role deletion workflow
        delete_workflow = {
            "name": "delete_role_dynamic",
            "nodes": [
                {
                    "id": "check_role",
                    "type": "RoleManagementNode",
                    "config": {
                        "operation": "get_role"
                    }
                },
                {
                    "id": "validate_deletion",
                    "type": "PythonCodeNode",
                    "config": {
                        "name": "validate_role_deletion",
                        "code": f"""
# Validate role can be deleted
role = role_data.get("role", {{}})
errors = []

if role.get("is_system_role"):
    errors.append("System roles cannot be deleted")

if role.get("user_count", 0) > 0 and not {force}:
    errors.append(f"Role has {{role.get('user_count')}} assigned users. Use force=true to delete anyway.")

result = {{
    "result": {{
        "can_delete": len(errors) == 0,
        "errors": errors,
        "role": role
    }}
}}
"""
                    }
                },
                {
                    "id": "check_permissions",
                    "type": "ABACPermissionEvaluatorNode",
                    "config": {
                        "resource": "roles",
                        "action": "delete",
                        "require_admin": True
                    }
                },
                {
                    "id": "delete_role",
                    "type": "RoleManagementNode",
                    "config": {
                        "operation": "delete_role",
                        "enable_audit": True
                    }
                },
                {
                    "id": "audit_log",
                    "type": "AuditLogNode",
                    "config": {
                        "log_level": "WARNING",
                        "event_type": "role_deleted"
                    }
                }
            ],
            "connections": [
                {
                    "from_node": "check_role",
                    "from_output": "role",
                    "to_node": "validate_deletion",
                    "to_input": "role_data"
                },
                {
                    "from_node": "validate_deletion",
                    "from_output": "result",
                    "to_node": "check_permissions",
                    "to_input": "resource_context"
                },
                {
                    "from_node": "check_permissions",
                    "from_output": "allowed",
                    "to_node": "delete_role",
                    "to_input": "permission_granted"
                },
                {
                    "from_node": "validate_deletion",
                    "from_output": "result.can_delete",
                    "to_node": "delete_role",
                    "to_input": "proceed"
                },
                {
                    "from_node": "delete_role",
                    "from_output": "result",
                    "to_node": "audit_log",
                    "to_input": "event_data"
                }
            ]
        }
        
        workflow_id = await agent_ui.create_dynamic_workflow(
            session_id,
            delete_workflow
        )
        
        execution_id = await agent_ui.execute_workflow(
            session_id,
            workflow_id,
            inputs={"role_name": role_name}
        )
        
        result = await agent_ui.wait_for_execution(
            session_id,
            execution_id,
            timeout=10
        )
        
        # Check validation
        validation = result.get("outputs", {}).get("validate_deletion", {}).get("result", {})
        if not validation.get("can_delete"):
            raise HTTPException(
                status_code=400,
                detail={"errors": validation.get("errors", [])}
            )
        
        deletion_result = result.get("outputs", {}).get("delete_role", {}).get("result", {})
        
        if not deletion_result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=deletion_result.get("error", "Role deletion failed")
            )
        
        return {
            "message": "Role deleted successfully",
            "role_name": role_name,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/assign")
async def assign_role(
    assignment: RoleAssignmentRequest,
    token: str = Depends(oauth2_scheme)
):
    """
    Assign role to user.
    
    Features:
    - Temporary role assignments with expiration
    - Audit logging with reason
    - Permission validation
    """
    try:
        # Create session
        session_id = await agent_ui.create_session("role_assign")
        
        # Execute role management workflow
        execution_id = await agent_ui.execute_workflow_template(
            session_id,
            "role_management_enterprise",
            inputs={
                "action": "assign",
                "user_id": assignment.user_id,
                "role_name": assignment.role_name,
                "expires_at": assignment.expires_at.isoformat() if assignment.expires_at else None,
                "reason": assignment.reason
            }
        )
        
        result = await agent_ui.wait_for_execution(
            session_id,
            execution_id,
            timeout=10
        )
        
        assignment_result = result.get("outputs", {}).get("manage_role", {}).get("result", {})
        
        if not assignment_result.get("success"):
            raise HTTPException(
                status_code=400,
                detail=assignment_result.get("error", "Role assignment failed")
            )
        
        return {
            "message": "Role assigned successfully",
            "user_id": assignment.user_id,
            "role_name": assignment.role_name,
            "expires_at": assignment.expires_at,
            "assignment_id": assignment_result.get("assignment_id"),
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/revoke")
async def revoke_role(
    user_id: str = Query(..., description="User ID"),
    role_name: str = Query(..., description="Role name to revoke"),
    reason: str = Query(..., description="Revocation reason"),
    token: str = Depends(oauth2_scheme)
):
    """Revoke role from user."""
    try:
        # Create session
        session_id = await agent_ui.create_session("role_revoke")
        
        # Execute role management workflow
        execution_id = await agent_ui.execute_workflow_template(
            session_id,
            "role_management_enterprise",
            inputs={
                "action": "revoke",
                "user_id": user_id,
                "role_name": role_name,
                "reason": reason
            }
        )
        
        result = await agent_ui.wait_for_execution(
            session_id,
            execution_id,
            timeout=10
        )
        
        revoke_result = result.get("outputs", {}).get("manage_role", {}).get("result", {})
        
        if not revoke_result.get("success"):
            raise HTTPException(
                status_code=400,
                detail=revoke_result.get("error", "Role revocation failed")
            )
        
        return {
            "message": "Role revoked successfully",
            "user_id": user_id,
            "role_name": role_name,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{role_name}/users")
async def get_role_users(
    role_name: str,
    token: str = Depends(oauth2_scheme),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200)
):
    """Get all users assigned to a role."""
    try:
        # Create session
        session_id = await agent_ui.create_session("role_users")
        
        # Create workflow to get role users
        users_workflow = {
            "name": "get_role_users",
            "nodes": [
                {
                    "id": "get_users",
                    "type": "RoleManagementNode",
                    "config": {
                        "operation": "get_role_users"
                    }
                },
                {
                    "id": "paginate",
                    "type": "PythonCodeNode",
                    "config": {
                        "name": "paginate_users",
                        "code": f"""
# Paginate user list
users = role_users.get("users", [])
total = len(users)

# Apply pagination
start = ({page} - 1) * {limit}
end = start + {limit}
paginated_users = users[start:end]

result = {{
    "result": {{
        "users": paginated_users,
        "total": total,
        "page": {page},
        "limit": {limit},
        "has_next": end < total,
        "role_name": "{role_name}"
    }}
}}
"""
                    }
                }
            ],
            "connections": [
                {
                    "from_node": "get_users",
                    "from_output": "role_users",
                    "to_node": "paginate",
                    "to_input": "role_users"
                }
            ]
        }
        
        workflow_id = await agent_ui.create_dynamic_workflow(
            session_id,
            users_workflow
        )
        
        execution_id = await agent_ui.execute_workflow(
            session_id,
            workflow_id,
            inputs={"role_name": role_name}
        )
        
        result = await agent_ui.wait_for_execution(
            session_id,
            execution_id,
            timeout=10
        )
        
        users_data = result.get("outputs", {}).get("paginate", {}).get("result", {})
        
        return users_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))