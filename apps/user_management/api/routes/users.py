"""
User Management REST API Routes

This module implements user CRUD operations using pure Kailash patterns.
All business logic is delegated to workflows executed by the SDK runtime.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, EmailStr, Field

from apps.user_management.core.startup import agent_ui, runtime
from apps.user_management.core.repositories import UserRepository


# Pydantic models for request/response
class UserCreateRequest(BaseModel):
    """User creation request model."""
    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    department: Optional[str] = Field(None, max_length=100)
    title: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    enable_sso: bool = True
    enable_mfa: bool = True


class UserUpdateRequest(BaseModel):
    """User update request model."""
    email: Optional[EmailStr] = None
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    department: Optional[str] = Field(None, max_length=100)
    title: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)


class UserResponse(BaseModel):
    """User response model."""
    id: str
    email: str
    first_name: str
    last_name: str
    department: Optional[str]
    title: Optional[str]
    phone: Optional[str]
    sso_enabled: bool
    mfa_enabled: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime]
    is_active: bool


class UserListResponse(BaseModel):
    """User list response model."""
    users: List[UserResponse]
    total: int
    page: int
    limit: int
    has_next: bool


# Create router
router = APIRouter()


@router.post("/", response_model=UserResponse)
async def create_user(user_data: UserCreateRequest):
    """
    Create a new user with enterprise features.
    
    This endpoint:
    - Validates user data
    - Checks permissions using ABAC
    - Creates user with SSO provisioning
    - Sets up MFA if enabled
    - Logs audit trail
    """
    try:
        # Create session for this operation
        session_id = await agent_ui.create_session("api_user_create")
        
        # Execute user creation workflow
        execution_id = await agent_ui.execute_workflow_template(
            session_id,
            "user_creation_enterprise",
            inputs={"user_data": user_data.dict()}
        )
        
        # Wait for completion
        result = await agent_ui.wait_for_execution(
            session_id,
            execution_id,
            timeout=30
        )
        
        # Extract user from result
        outputs = result.get("outputs", {})
        user_result = outputs.get("create_user", {}).get("user", {})
        
        if not user_result:
            raise HTTPException(status_code=500, detail="User creation failed")
        
        # Send real-time update
        from kailash.middleware import WorkflowEvent, EventType
        await agent_ui.realtime.broadcast_event(
            WorkflowEvent(
                type=EventType.USER_CREATED,
                workflow_id="user_creation_enterprise",
                execution_id=execution_id,
                data={"user": user_result}
            )
        )
        
        return UserResponse(**user_result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=UserListResponse)
async def list_users(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=200, description="Items per page"),
    search: Optional[str] = Query(None, description="Search term"),
    department: Optional[str] = Query(None, description="Filter by department"),
    is_active: Optional[bool] = Query(None, description="Filter by active status")
):
    """
    List users with pagination and filtering.
    
    This endpoint provides:
    - Pagination support
    - Search by name/email
    - Department filtering
    - Active status filtering
    - Real-time updates via WebSocket
    """
    try:
        # Create session
        session_id = await agent_ui.create_session("api_user_list")
        
        # Create dynamic listing workflow
        list_workflow = {
            "name": "list_users_dynamic",
            "nodes": [
                {
                    "id": "user_manager",
                    "type": "UserManagementNode",
                    "config": {"operation": "list_users"}
                },
                {
                    "id": "filter_processor",
                    "type": "PythonCodeNode",
                    "config": {
                        "name": "filter_and_paginate",
                        "code": f"""
# Apply filters and pagination
users = user_list.get("users", [])
total = len(users)

# Apply search filter
if {repr(search)}:
    search_term = {repr(search)}.lower()
    users = [u for u in users if 
             search_term in u.get("email", "").lower() or
             search_term in u.get("first_name", "").lower() or 
             search_term in u.get("last_name", "").lower()]

# Apply department filter
if {repr(department)}:
    users = [u for u in users if u.get("department", "").lower() == {repr(department)}.lower()]

# Apply active status filter
if {repr(is_active)} is not None:
    users = [u for u in users if u.get("is_active", True) == {repr(is_active)}]

# Update total after filtering
filtered_total = len(users)

# Apply pagination
start = ({page} - 1) * {limit}
end = start + {limit}
paginated_users = users[start:end]

result = {{
    "result": {{
        "users": paginated_users,
        "total": filtered_total,
        "page": {page},
        "limit": {limit},
        "has_next": end < filtered_total
    }}
}}
"""
                    }
                }
            ],
            "connections": [
                {
                    "from_node": "user_manager",
                    "from_output": "user_list",
                    "to_node": "filter_processor",
                    "to_input": "user_list"
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
            inputs={"action": "list_users"}
        )
        
        result = await agent_ui.wait_for_execution(
            session_id,
            execution_id,
            timeout=10
        )
        
        list_data = result.get("outputs", {}).get("filter_processor", {}).get("result", {})
        
        return UserListResponse(**list_data)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: str):
    """Get user by ID."""
    try:
        # Create session
        session_id = await agent_ui.create_session("api_user_get")
        
        # Create workflow to get user
        get_workflow = {
            "name": "get_user_by_id",
            "nodes": [
                {
                    "id": "user_manager",
                    "type": "UserManagementNode",
                    "config": {"operation": "get_user"}
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
            inputs={"user_id": user_id}
        )
        
        result = await agent_ui.wait_for_execution(
            session_id,
            execution_id,
            timeout=5
        )
        
        user_data = result.get("outputs", {}).get("user_manager", {}).get("user")
        
        if not user_data:
            raise HTTPException(status_code=404, detail="User not found")
        
        return UserResponse(**user_data)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(user_id: str, update_data: UserUpdateRequest):
    """
    Update user information.
    
    This endpoint:
    - Validates update data
    - Checks permissions
    - Updates user information
    - Logs audit trail
    - Sends real-time updates
    """
    try:
        # Create session
        session_id = await agent_ui.create_session("api_user_update")
        
        # Execute update workflow
        execution_id = await agent_ui.execute_workflow_template(
            session_id,
            "user_update_enterprise",
            inputs={
                "user_id": user_id,
                "update_data": update_data.dict(exclude_unset=True)
            }
        )
        
        # Wait for completion
        result = await agent_ui.wait_for_execution(
            session_id,
            execution_id,
            timeout=15
        )
        
        # Extract updated user
        user_result = result.get("outputs", {}).get("update_user", {}).get("user", {})
        
        if not user_result:
            raise HTTPException(status_code=500, detail="User update failed")
        
        # Send real-time update
        from kailash.middleware import WorkflowEvent, EventType
        await agent_ui.realtime.broadcast_event(
            WorkflowEvent(
                type=EventType.USER_UPDATED,
                workflow_id="user_update_enterprise",
                execution_id=execution_id,
                data={"user": user_result}
            )
        )
        
        return UserResponse(**user_result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{user_id}")
async def delete_user(user_id: str, reason: str = Query(..., description="Reason for deletion")):
    """
    Delete user with GDPR compliance.
    
    This endpoint:
    - Checks elevated permissions
    - Performs compliance checks
    - Archives user data
    - Deletes user
    - Logs compliance audit
    """
    try:
        # Create session
        session_id = await agent_ui.create_session("api_user_delete")
        
        # Execute deletion workflow
        execution_id = await agent_ui.execute_workflow_template(
            session_id,
            "user_deletion_enterprise",
            inputs={
                "user_id": user_id,
                "deletion_reason": reason
            }
        )
        
        # Wait for completion
        result = await agent_ui.wait_for_execution(
            session_id,
            execution_id,
            timeout=30
        )
        
        deletion_result = result.get("outputs", {}).get("delete_user", {}).get("deletion_result", {})
        
        if not deletion_result.get("success"):
            raise HTTPException(status_code=500, detail="User deletion failed")
        
        # Send real-time update
        from kailash.middleware import WorkflowEvent, EventType
        await agent_ui.realtime.broadcast_event(
            WorkflowEvent(
                type=EventType.USER_DELETED,
                workflow_id="user_deletion_enterprise",
                execution_id=execution_id,
                data={"user_id": user_id, "reason": reason}
            )
        )
        
        return {
            "message": "User deleted successfully",
            "user_id": user_id,
            "archive_id": deletion_result.get("archive_id"),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{user_id}/disable")
async def disable_user(user_id: str, reason: str = Query(..., description="Reason for disabling")):
    """Disable user account."""
    try:
        # Create session
        session_id = await agent_ui.create_session("api_user_disable")
        
        # Use update workflow to disable user
        execution_id = await agent_ui.execute_workflow_template(
            session_id,
            "user_update_enterprise",
            inputs={
                "user_id": user_id,
                "update_data": {"is_active": False},
                "reason": reason
            }
        )
        
        result = await agent_ui.wait_for_execution(
            session_id,
            execution_id,
            timeout=10
        )
        
        user_result = result.get("outputs", {}).get("update_user", {}).get("user", {})
        
        return {
            "message": "User disabled successfully",
            "user_id": user_id,
            "is_active": user_result.get("is_active", False),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{user_id}/enable")
async def enable_user(user_id: str):
    """Enable user account."""
    try:
        # Create session
        session_id = await agent_ui.create_session("api_user_enable")
        
        # Use update workflow to enable user
        execution_id = await agent_ui.execute_workflow_template(
            session_id,
            "user_update_enterprise",
            inputs={
                "user_id": user_id,
                "update_data": {"is_active": True}
            }
        )
        
        result = await agent_ui.wait_for_execution(
            session_id,
            execution_id,
            timeout=10
        )
        
        user_result = result.get("outputs", {}).get("update_user", {}).get("user", {})
        
        return {
            "message": "User enabled successfully",
            "user_id": user_id,
            "is_active": user_result.get("is_active", True),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))