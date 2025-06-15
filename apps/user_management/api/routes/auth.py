"""
Authentication REST API Routes

This module implements authentication endpoints using enterprise auth nodes.
Supports SSO, MFA, adaptive authentication, and risk assessment.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field

from apps.user_management.core.startup import agent_ui, enterprise_auth
from kailash.middleware import EventType, WorkflowEvent


# Pydantic models
class LoginRequest(BaseModel):
    """Login request model."""

    username: str
    password: str
    device_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class SSOInitRequest(BaseModel):
    """SSO initialization request."""

    provider: str = Field(
        ..., description="SSO provider (saml, oauth2, azure, google, okta)"
    )
    redirect_uri: str = Field(..., description="Redirect URI after authentication")
    state: Optional[str] = Field(None, description="State parameter for security")


class MFASetupRequest(BaseModel):
    """MFA setup request."""

    method: str = Field(..., description="MFA method (totp, sms, email, push)")
    phone_number: Optional[str] = Field(None, description="Phone for SMS")
    email: Optional[EmailStr] = Field(None, description="Email for email-based MFA")


class MFAVerifyRequest(BaseModel):
    """MFA verification request."""

    code: str = Field(..., description="MFA code to verify")
    method: str = Field(..., description="MFA method used")


class TokenResponse(BaseModel):
    """Authentication token response."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: Optional[str] = None
    user_id: str
    session_id: str


# Create router
router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")


@router.post("/login", response_model=TokenResponse)
async def login(credentials: LoginRequest):
    """
    Authenticate user with adaptive security.

    Features:
    - Risk assessment based on behavior
    - Threat detection
    - Adaptive authentication
    - Session management
    - Device tracking
    """
    try:
        # Create session
        session_id = await agent_ui.create_session("auth_login")

        # Execute authentication workflow
        execution_id = await agent_ui.execute_workflow_template(
            session_id,
            "user_authentication_enterprise",
            inputs={
                "credentials": credentials.dict(),
                "context": {
                    "device_id": credentials.device_id,
                    "ip_address": credentials.ip_address,
                    "user_agent": credentials.user_agent,
                    "timestamp": datetime.now().isoformat(),
                },
            },
        )

        # Wait for completion
        result = await agent_ui.wait_for_execution(session_id, execution_id, timeout=15)

        # Extract authentication result
        auth_result = (
            result.get("outputs", {}).get("authenticate", {}).get("auth_result", {})
        )
        session_result = (
            result.get("outputs", {}).get("create_session", {}).get("session", {})
        )

        if not auth_result.get("authenticated"):
            # Check if MFA is required
            if auth_result.get("mfa_required"):
                raise HTTPException(
                    status_code=428,  # Precondition Required
                    detail={
                        "message": "MFA verification required",
                        "mfa_methods": auth_result.get("mfa_methods", []),
                        "session_id": session_id,
                    },
                )

            # Authentication failed
            raise HTTPException(
                status_code=401,
                detail=auth_result.get("error", "Authentication failed"),
            )

        # Generate token
        token_data = {
            "access_token": session_result.get("access_token"),
            "token_type": "bearer",
            "expires_in": 3600,  # 1 hour
            "refresh_token": session_result.get("refresh_token"),
            "user_id": auth_result.get("user_id"),
            "session_id": session_result.get("session_id"),
        }

        # Send authentication event
        await agent_ui.realtime.broadcast_event(
            WorkflowEvent(
                type=EventType.USER_AUTHENTICATED,
                workflow_id="user_authentication_enterprise",
                execution_id=execution_id,
                data={
                    "user_id": auth_result.get("user_id"),
                    "session_id": session_result.get("session_id"),
                    "risk_score": auth_result.get("risk_score", 0),
                },
            )
        )

        return TokenResponse(**token_data)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/token")
async def token(form_data: OAuth2PasswordRequestForm = Depends()):
    """OAuth2 compatible token endpoint."""
    login_req = LoginRequest(username=form_data.username, password=form_data.password)
    return await login(login_req)


@router.post("/logout")
async def logout(token: str = Depends(oauth2_scheme)):
    """
    Logout user and invalidate session.

    This endpoint:
    - Invalidates the current session
    - Clears session data
    - Logs security event
    """
    try:
        # Create session
        session_id = await agent_ui.create_session("auth_logout")

        # Create logout workflow
        logout_workflow = {
            "name": "user_logout",
            "nodes": [
                {
                    "id": "invalidate_session",
                    "type": "SessionManagementNode",
                    "config": {"operation": "invalidate"},
                },
                {
                    "id": "log_event",
                    "type": "SecurityEventNode",
                    "config": {"event_type": "logout", "event_severity": "INFO"},
                },
            ],
            "connections": [
                {
                    "from_node": "invalidate_session",
                    "from_output": "result",
                    "to_node": "log_event",
                    "to_input": "event_data",
                }
            ],
        }

        workflow_id = await agent_ui.create_dynamic_workflow(
            session_id, logout_workflow
        )

        execution_id = await agent_ui.execute_workflow(
            session_id, workflow_id, inputs={"token": token}
        )

        await agent_ui.wait_for_execution(session_id, execution_id, timeout=5)

        return {
            "message": "Logged out successfully",
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sso/initiate")
async def initiate_sso(sso_request: SSOInitRequest):
    """
    Initiate SSO authentication flow.

    Supports:
    - SAML 2.0
    - OAuth 2.0
    - OpenID Connect
    - Azure AD
    - Google Workspace
    - Okta
    """
    try:
        # Create session
        session_id = await agent_ui.create_session("sso_init")

        # Create SSO workflow
        sso_workflow = {
            "name": "sso_initiation",
            "nodes": [
                {
                    "id": "sso_auth",
                    "type": "SSOAuthenticationNode",
                    "config": {
                        "providers": [sso_request.provider],
                        "encryption_enabled": True,
                    },
                }
            ],
        }

        workflow_id = await agent_ui.create_dynamic_workflow(session_id, sso_workflow)

        execution_id = await agent_ui.execute_workflow(
            session_id,
            workflow_id,
            inputs={
                "action": "initiate",
                "provider": sso_request.provider,
                "redirect_uri": sso_request.redirect_uri,
                "state": sso_request.state,
            },
        )

        result = await agent_ui.wait_for_execution(session_id, execution_id, timeout=5)

        sso_result = result.get("outputs", {}).get("sso_auth", {}).get("sso_result", {})

        return {
            "auth_url": sso_result.get("auth_url"),
            "request_id": sso_result.get("request_id"),
            "expires_at": sso_result.get("expires_at"),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sso/callback")
async def sso_callback(callback_data: Dict[str, Any]):
    """Handle SSO callback."""
    try:
        # Create session
        session_id = await agent_ui.create_session("sso_callback")

        # Execute authentication workflow with SSO data
        execution_id = await agent_ui.execute_workflow_template(
            session_id,
            "user_authentication_enterprise",
            inputs={"sso_callback": callback_data, "auth_type": "sso"},
        )

        result = await agent_ui.wait_for_execution(session_id, execution_id, timeout=15)

        auth_result = (
            result.get("outputs", {}).get("authenticate", {}).get("auth_result", {})
        )
        session_result = (
            result.get("outputs", {}).get("create_session", {}).get("session", {})
        )

        if not auth_result.get("authenticated"):
            raise HTTPException(status_code=401, detail="SSO authentication failed")

        return TokenResponse(
            access_token=session_result.get("access_token"),
            expires_in=3600,
            user_id=auth_result.get("user_id"),
            session_id=session_result.get("session_id"),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/mfa/setup")
async def setup_mfa(mfa_request: MFASetupRequest, token: str = Depends(oauth2_scheme)):
    """
    Setup MFA for authenticated user.

    Supports:
    - TOTP (Google Authenticator, Authy)
    - SMS
    - Email
    - Push notifications
    - Backup codes
    """
    try:
        # Create session
        session_id = await agent_ui.create_session("mfa_setup")

        # Create MFA setup workflow
        mfa_workflow = {
            "name": "mfa_setup",
            "nodes": [
                {
                    "id": "setup_mfa",
                    "type": "MultiFactorAuthNode",
                    "config": {
                        "operation": "setup",
                        "method": mfa_request.method,
                        "backup_codes": True,
                    },
                }
            ],
        }

        workflow_id = await agent_ui.create_dynamic_workflow(session_id, mfa_workflow)

        execution_id = await agent_ui.execute_workflow(
            session_id,
            workflow_id,
            inputs={"token": token, "mfa_config": mfa_request.dict()},
        )

        result = await agent_ui.wait_for_execution(session_id, execution_id, timeout=10)

        mfa_result = (
            result.get("outputs", {}).get("setup_mfa", {}).get("mfa_result", {})
        )

        response = {
            "method": mfa_request.method,
            "setup_complete": mfa_result.get("success", False),
        }

        # Add method-specific data
        if mfa_request.method == "totp":
            response["qr_code"] = mfa_result.get("qr_code")
            response["secret"] = mfa_result.get("secret")
        elif mfa_request.method in ["sms", "email"]:
            response["verification_sent"] = True

        if mfa_result.get("backup_codes"):
            response["backup_codes"] = mfa_result.get("backup_codes")

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/mfa/verify")
async def verify_mfa(
    verification: MFAVerifyRequest,
    session_id: str = Header(..., description="Session ID from login"),
):
    """Verify MFA code."""
    try:
        # Create MFA verification workflow
        verify_workflow = {
            "name": "mfa_verification",
            "nodes": [
                {
                    "id": "verify_mfa",
                    "type": "MultiFactorAuthNode",
                    "config": {"operation": "verify", "method": verification.method},
                }
            ],
        }

        workflow_id = await agent_ui.create_dynamic_workflow(
            session_id, verify_workflow
        )

        execution_id = await agent_ui.execute_workflow(
            session_id,
            workflow_id,
            inputs={"code": verification.code, "method": verification.method},
        )

        result = await agent_ui.wait_for_execution(session_id, execution_id, timeout=5)

        mfa_result = (
            result.get("outputs", {}).get("verify_mfa", {}).get("mfa_result", {})
        )

        if not mfa_result.get("verified"):
            raise HTTPException(status_code=401, detail="Invalid MFA code")

        # Generate full access token after MFA verification
        return {
            "verified": True,
            "access_token": mfa_result.get("access_token"),
            "message": "MFA verification successful",
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/info")
async def get_session_info(token: str = Depends(oauth2_scheme)):
    """Get current session information."""
    try:
        # Create session
        session_id = await agent_ui.create_session("session_info")

        # Create session info workflow
        info_workflow = {
            "name": "session_info",
            "nodes": [
                {
                    "id": "get_session",
                    "type": "SessionManagementNode",
                    "config": {"operation": "get_info"},
                }
            ],
        }

        workflow_id = await agent_ui.create_dynamic_workflow(session_id, info_workflow)

        execution_id = await agent_ui.execute_workflow(
            session_id, workflow_id, inputs={"token": token}
        )

        result = await agent_ui.wait_for_execution(session_id, execution_id, timeout=5)

        session_info = (
            result.get("outputs", {}).get("get_session", {}).get("session", {})
        )

        return {
            "session_id": session_info.get("session_id"),
            "user_id": session_info.get("user_id"),
            "created_at": session_info.get("created_at"),
            "last_activity": session_info.get("last_activity"),
            "expires_at": session_info.get("expires_at"),
            "device_info": session_info.get("device_info"),
            "ip_address": session_info.get("ip_address"),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
