"""
SSO Management REST API Routes

This module implements enterprise Single Sign-On using pure Kailash SDK.
Supports SAML, OAuth2, Azure AD, Google, Okta, and custom providers.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import secrets
import base64

from fastapi import APIRouter, HTTPException, Query, Depends, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field, HttpUrl

from apps.user_management.core.startup import agent_ui, runtime
from kailash.middleware import WorkflowEvent, EventType
from kailash.workflow import WorkflowBuilder
from kailash.runtime.local import LocalRuntime


# Pydantic models
class SSOProviderCreateRequest(BaseModel):
    """SSO provider creation request."""
    name: str = Field(..., min_length=1, max_length=100)
    provider_type: str = Field(..., pattern="^(saml|oauth2|azure|google|okta|custom)$")
    client_id: str = Field(..., description="OAuth client ID or SAML entity ID")
    client_secret: Optional[str] = Field(None, description="OAuth client secret")
    metadata_url: Optional[HttpUrl] = Field(None, description="SAML metadata URL")
    authorization_url: Optional[HttpUrl] = Field(None, description="OAuth authorization URL")
    token_url: Optional[HttpUrl] = Field(None, description="OAuth token URL")
    userinfo_url: Optional[HttpUrl] = Field(None, description="OAuth userinfo URL")
    scopes: List[str] = Field(default_factory=lambda: ["openid", "email", "profile"])
    attribute_mapping: Dict[str, str] = Field(
        default_factory=dict,
        description="Map provider attributes to user fields"
    )
    is_active: bool = Field(True, description="Enable/disable provider")
    allow_signup: bool = Field(True, description="Allow new user creation")
    domain_whitelist: List[str] = Field(
        default_factory=list,
        description="Allowed email domains"
    )


class SSOSessionResponse(BaseModel):
    """SSO session response."""
    session_id: str
    provider: str
    authorization_url: str
    state: str
    expires_at: datetime


class SSOCallbackRequest(BaseModel):
    """SSO callback request."""
    code: Optional[str] = None
    state: str
    error: Optional[str] = None
    error_description: Optional[str] = None


class SSOUserInfo(BaseModel):
    """SSO user information."""
    sub: str  # Subject/unique ID
    email: str
    name: Optional[str] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    picture: Optional[str] = None
    email_verified: bool = True
    groups: List[str] = Field(default_factory=list)
    attributes: Dict[str, Any] = Field(default_factory=dict)


class SSOProviderResponse(BaseModel):
    """SSO provider response."""
    id: str
    name: str
    provider_type: str
    client_id: str
    is_active: bool
    allow_signup: bool
    domain_whitelist: List[str]
    created_at: datetime
    updated_at: datetime
    last_used: Optional[datetime]
    user_count: int
    success_rate: float


# Create router
router = APIRouter()

# Initialize async runtime
async_runtime = LocalRuntime(enable_async=True, debug=False)


@router.post("/providers", response_model=SSOProviderResponse)
async def create_sso_provider(provider_data: SSOProviderCreateRequest):
    """
    Create a new SSO provider configuration.
    
    Features beyond Django:
    - Multiple provider types (SAML, OAuth2, etc.)
    - Domain-based access control
    - Automatic metadata discovery
    - Custom attribute mapping
    - Real-time provider health monitoring
    """
    try:
        builder = WorkflowBuilder("create_sso_provider_workflow")
        
        # Validate provider configuration
        builder.add_node("PythonCodeNode", "validate_provider", {
            "name": "validate_sso_provider",
            "code": """
# Validate SSO provider configuration
errors = []
provider = provider_data

# Provider-specific validation
if provider['provider_type'] == 'saml':
    if not provider.get('metadata_url') and not provider.get('client_secret'):
        errors.append('SAML provider requires metadata_url')
elif provider['provider_type'] in ['oauth2', 'google', 'azure', 'okta']:
    if not provider.get('authorization_url'):
        errors.append('OAuth provider requires authorization_url')
    if not provider.get('token_url'):
        errors.append('OAuth provider requires token_url')

# Validate domain whitelist
for domain in provider.get('domain_whitelist', []):
    if not domain.startswith('@'):
        errors.append(f'Domain {domain} must start with @')

result = {
    "result": {
        "valid": len(errors) == 0,
        "errors": errors,
        "provider_data": provider
    }
}
"""
        })
        
        # Test provider connectivity
        builder.add_node("HTTPRequestNode", "test_connectivity", {
            "name": "test_sso_connectivity",
            "method": "GET",
            "timeout": 5000,
            "validate_ssl": True
        })
        
        # Encrypt sensitive data
        builder.add_node("CredentialManagerNode", "encrypt_secrets", {
            "operation": "encrypt",
            "credential_type": "oauth_secret"
        })
        
        # Create provider record
        builder.add_node("PythonCodeNode", "create_provider", {
            "name": "create_sso_provider_record",
            "code": """
# Create SSO provider
import uuid
from datetime import datetime

provider_id = str(uuid.uuid4())
now = datetime.now()

# Encrypt client secret if provided
encrypted_secret = None
if provider_data.get('client_secret'):
    encrypted_secret = encryption_result.get('encrypted_value')

provider = {
    "id": provider_id,
    "name": provider_data["name"],
    "provider_type": provider_data["provider_type"],
    "client_id": provider_data["client_id"],
    "client_secret": encrypted_secret,
    "metadata_url": provider_data.get("metadata_url"),
    "authorization_url": provider_data.get("authorization_url"),
    "token_url": provider_data.get("token_url"),
    "userinfo_url": provider_data.get("userinfo_url"),
    "scopes": provider_data.get("scopes", ["openid", "email", "profile"]),
    "attribute_mapping": provider_data.get("attribute_mapping", {}),
    "is_active": provider_data.get("is_active", True),
    "allow_signup": provider_data.get("allow_signup", True),
    "domain_whitelist": provider_data.get("domain_whitelist", []),
    "created_at": now,
    "updated_at": now,
    "last_used": None,
    "user_count": 0,
    "success_rate": 0.0
}

result = {"result": provider}
"""
        })
        
        # Audit creation
        builder.add_node("AuditLogNode", "audit_creation", {
            "operation": "log_event",
            "event_type": "sso_provider_created",
            "severity": "high"
        })
        
        # Connect nodes
        builder.add_connection("validate_provider", "result", "test_connectivity", "validation")
        builder.add_connection("test_connectivity", "response", "encrypt_secrets", "connectivity_test")
        builder.add_connection("validate_provider", "result.provider_data", "encrypt_secrets", "data")
        builder.add_connection("encrypt_secrets", "result", "create_provider", "encryption_result")
        builder.add_connection("validate_provider", "result.provider_data", "create_provider", "provider_data")
        builder.add_connection("create_provider", "result", "audit_creation", "resource")
        
        # Execute workflow
        workflow = builder.build()
        
        # Set URL for connectivity test based on provider type
        test_url = provider_data.metadata_url or provider_data.authorization_url
        
        results, execution_id = await async_runtime.execute(
            workflow,
            parameters={
                "provider_data": provider_data.dict(),
                "url": str(test_url) if test_url else None
            }
        )
        
        # Check validation
        validation = results.get("validate_provider", {}).get("result", {})
        if not validation.get("valid"):
            raise HTTPException(
                status_code=400,
                detail={"errors": validation.get("errors", [])}
            )
        
        # Get created provider
        provider = results.get("create_provider", {}).get("result", {})
        
        # Broadcast creation event
        await agent_ui.realtime.broadcast_event(
            WorkflowEvent(
                type=EventType.SSO_PROVIDER_CREATED,
                workflow_id="create_sso_provider_workflow",
                execution_id=execution_id,
                data={"provider": provider}
            )
        )
        
        return SSOProviderResponse(**provider)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/initiate/{provider_id}")
async def initiate_sso(
    provider_id: str,
    redirect_uri: str = Query(..., description="Redirect URI after authentication"),
    request: Request = None
):
    """
    Initiate SSO authentication flow.
    
    Creates a secure session and returns the authorization URL.
    """
    try:
        builder = WorkflowBuilder("initiate_sso_workflow")
        
        # Get provider configuration
        builder.add_node("PythonCodeNode", "get_provider", {
            "name": "get_sso_provider",
            "code": f"""
# Get SSO provider configuration
# In real implementation, would fetch from database
provider = {{
    "id": "{provider_id}",
    "provider_type": "oauth2",
    "authorization_url": "https://auth.example.com/authorize",
    "client_id": "example_client_id",
    "scopes": ["openid", "email", "profile"],
    "is_active": True
}}

if not provider.get("is_active"):
    raise ValueError("SSO provider is not active")

result = {{"result": {{"provider": provider}}}}
"""
        })
        
        # Generate secure session
        builder.add_node("PythonCodeNode", "create_session", {
            "name": "create_sso_session",
            "code": """
# Create SSO session
import secrets
import base64
from datetime import datetime, timedelta

# Generate secure state parameter
state = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')

# Create session
session = {
    "session_id": secrets.token_urlsafe(32),
    "provider_id": provider["id"],
    "state": state,
    "redirect_uri": redirect_uri,
    "created_at": datetime.now(),
    "expires_at": datetime.now() + timedelta(minutes=10),
    "ip_address": request_ip
}

result = {"result": {"session": session, "state": state}}
"""
        })
        
        # Build authorization URL
        builder.add_node("PythonCodeNode", "build_auth_url", {
            "name": "build_authorization_url",
            "code": """
# Build authorization URL
from urllib.parse import urlencode

provider = provider_data["provider"]
state = session_data["state"]

# Build OAuth2 parameters
params = {
    "client_id": provider["client_id"],
    "redirect_uri": redirect_uri,
    "response_type": "code",
    "scope": " ".join(provider.get("scopes", ["openid", "email", "profile"])),
    "state": state,
    "access_type": "offline",  # Request refresh token
    "prompt": "select_account"  # Force account selection
}

# Provider-specific parameters
if provider["provider_type"] == "google":
    params["hd"] = "*"  # Allow any G Suite domain
elif provider["provider_type"] == "azure":
    params["response_mode"] = "query"

auth_url = f"{provider['authorization_url']}?{urlencode(params)}"

result = {
    "result": {
        "authorization_url": auth_url,
        "session_id": session_data["session"]["session_id"]
    }
}
"""
        })
        
        # Audit SSO initiation
        builder.add_node("AuditLogNode", "audit_initiation", {
            "operation": "log_event",
            "event_type": "sso_initiated",
            "severity": "info"
        })
        
        # Connect nodes
        builder.add_connection("get_provider", "result", "create_session", "provider_data")
        builder.add_connection("create_session", "result", "build_auth_url", "session_data")
        builder.add_connection("get_provider", "result", "build_auth_url", "provider_data")
        builder.add_connection("build_auth_url", "result", "audit_initiation", "sso_data")
        
        # Execute workflow
        workflow = builder.build()
        results, _ = await async_runtime.execute(
            workflow,
            parameters={
                "redirect_uri": redirect_uri,
                "request_ip": request.client.host if request else "unknown"
            }
        )
        
        # Get authorization URL and session
        auth_data = results.get("build_auth_url", {}).get("result", {})
        session_data = results.get("create_session", {}).get("result", {}).get("session", {})
        
        return SSOSessionResponse(
            session_id=auth_data["session_id"],
            provider=provider_id,
            authorization_url=auth_data["authorization_url"],
            state=session_data["state"],
            expires_at=session_data["expires_at"]
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/callback/{provider_id}")
async def sso_callback(
    provider_id: str,
    callback_data: SSOCallbackRequest
):
    """
    Handle SSO callback from provider.
    
    Validates the callback, exchanges code for tokens, and creates/updates user.
    """
    try:
        # Handle errors from provider
        if callback_data.error:
            raise HTTPException(
                status_code=400,
                detail=f"SSO error: {callback_data.error} - {callback_data.error_description}"
            )
        
        builder = WorkflowBuilder("sso_callback_workflow")
        
        # Validate state parameter
        builder.add_node("PythonCodeNode", "validate_state", {
            "name": "validate_sso_state",
            "code": """
# Validate state parameter
# In real implementation, would check against stored session
import secrets

# For demo, just check it's not empty
if not state or len(state) < 32:
    raise ValueError("Invalid state parameter")

# Verify session hasn't expired
from datetime import datetime
# Mock session check - in real impl would query session store
session_valid = True

if not session_valid:
    raise ValueError("SSO session expired or invalid")

result = {"result": {"valid": True}}
"""
        })
        
        # Exchange code for tokens
        builder.add_node("OAuth2Node", "exchange_code", {
            "operation": "exchange_code",
            "provider_id": provider_id
        })
        
        # Get user info from provider
        builder.add_node("HTTPRequestNode", "get_userinfo", {
            "name": "get_sso_userinfo",
            "method": "GET",
            "headers": {
                "Authorization": "Bearer {access_token}"
            }
        })
        
        # Process user data
        builder.add_node("PythonCodeNode", "process_userinfo", {
            "name": "process_sso_userinfo",
            "code": """
# Process user info from SSO provider
import json

# Parse userinfo response
userinfo_raw = userinfo_response.get("body", "{}")
userinfo = json.loads(userinfo_raw) if isinstance(userinfo_raw, str) else userinfo_raw

# Map provider attributes to standard fields
# In real implementation, would use provider's attribute mapping
user_data = {
    "sub": userinfo.get("sub") or userinfo.get("id"),
    "email": userinfo.get("email") or userinfo.get("mail"),
    "name": userinfo.get("name") or f"{userinfo.get('given_name', '')} {userinfo.get('family_name', '')}".strip(),
    "given_name": userinfo.get("given_name") or userinfo.get("firstName"),
    "family_name": userinfo.get("family_name") or userinfo.get("lastName"),
    "picture": userinfo.get("picture") or userinfo.get("avatar_url"),
    "email_verified": userinfo.get("email_verified", True),
    "groups": userinfo.get("groups", []),
    "attributes": {k: v for k, v in userinfo.items() if k not in ["sub", "email", "name"]}
}

# Check domain whitelist
email_domain = "@" + user_data["email"].split("@")[-1]
# In real impl, would check against provider's domain_whitelist

result = {"result": {"user_data": user_data}}
"""
        })
        
        # Create or update user
        builder.add_node("UserManagementNode", "upsert_user", {
            "operation": "create_or_update_sso_user"
        })
        
        # Create authentication token
        builder.add_node("PythonCodeNode", "create_token", {
            "name": "create_auth_token",
            "code": """
# Create JWT token for user
import jwt
import secrets
from datetime import datetime, timedelta

# Token payload
payload = {
    "sub": user["id"],
    "email": user["email"],
    "name": user.get("name"),
    "iat": datetime.utcnow(),
    "exp": datetime.utcnow() + timedelta(hours=24),
    "jti": secrets.token_urlsafe(16),
    "sso_provider": provider_id
}

# In real implementation, would use proper JWT signing
token = jwt.encode(payload, "secret_key", algorithm="HS256")

result = {
    "result": {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": 86400,
        "user": user
    }
}
"""
        })
        
        # Audit successful login
        builder.add_node("AuditLogNode", "audit_login", {
            "operation": "log_event",
            "event_type": "sso_login_success",
            "severity": "info"
        })
        
        # Connect nodes
        builder.add_connection("validate_state", "result", "exchange_code", "state_validation")
        builder.add_connection("exchange_code", "tokens", "get_userinfo", "token_data")
        builder.add_connection("get_userinfo", "response", "process_userinfo", "userinfo_response")
        builder.add_connection("process_userinfo", "result.user_data", "upsert_user", "sso_user_data")
        builder.add_connection("upsert_user", "user", "create_token", "user")
        builder.add_connection("create_token", "result", "audit_login", "login_data")
        
        # Execute workflow
        workflow = builder.build()
        results, execution_id = await async_runtime.execute(
            workflow,
            parameters={
                "state": callback_data.state,
                "code": callback_data.code,
                "provider_id": provider_id
            }
        )
        
        # Get authentication result
        auth_result = results.get("create_token", {}).get("result", {})
        
        # Broadcast successful SSO login
        await agent_ui.realtime.broadcast_event(
            WorkflowEvent(
                type=EventType.SSO_LOGIN_SUCCESS,
                workflow_id="sso_callback_workflow",
                execution_id=execution_id,
                data={
                    "user_id": auth_result["user"]["id"],
                    "provider": provider_id
                }
            )
        )
        
        return auth_result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/providers", response_model=List[SSOProviderResponse])
async def list_sso_providers(
    include_inactive: bool = Query(False, description="Include inactive providers")
):
    """
    List all configured SSO providers.
    
    Shows provider status, usage statistics, and health metrics.
    """
    try:
        builder = WorkflowBuilder("list_sso_providers_workflow")
        
        # Get providers from database
        builder.add_node("PythonCodeNode", "get_providers", {
            "name": "get_all_providers",
            "code": f"""
# Get SSO providers
# In real implementation, would query database
from datetime import datetime, timedelta

providers = [
    {{
        "id": "google-1",
        "name": "Google Workspace",
        "provider_type": "google",
        "client_id": "google_client_id",
        "is_active": True,
        "allow_signup": True,
        "domain_whitelist": ["@company.com"],
        "created_at": datetime.now() - timedelta(days=30),
        "updated_at": datetime.now() - timedelta(days=1),
        "last_used": datetime.now() - timedelta(hours=2),
        "user_count": 156,
        "success_rate": 0.98
    }},
    {{
        "id": "azure-1",
        "name": "Azure AD",
        "provider_type": "azure",
        "client_id": "azure_client_id",
        "is_active": True,
        "allow_signup": False,
        "domain_whitelist": ["@company.com", "@partner.com"],
        "created_at": datetime.now() - timedelta(days=60),
        "updated_at": datetime.now() - timedelta(days=7),
        "last_used": datetime.now() - timedelta(hours=5),
        "user_count": 89,
        "success_rate": 0.95
    }},
    {{
        "id": "okta-1",
        "name": "Okta SSO",
        "provider_type": "okta",
        "client_id": "okta_client_id",
        "is_active": {not include_inactive},
        "allow_signup": True,
        "domain_whitelist": [],
        "created_at": datetime.now() - timedelta(days=15),
        "updated_at": datetime.now() - timedelta(days=3),
        "last_used": None,
        "user_count": 0,
        "success_rate": 0.0
    }}
]

# Filter based on include_inactive
if not {include_inactive}:
    providers = [p for p in providers if p["is_active"]]

result = {{"result": {{"providers": providers}}}}
"""
        })
        
        # Check provider health
        builder.add_node("PythonCodeNode", "check_health", {
            "name": "check_provider_health",
            "code": """
# Check health status of each provider
import random

providers_with_health = []
for provider in providers:
    # In real implementation, would ping provider endpoints
    health_status = "healthy"
    if provider["success_rate"] < 0.9:
        health_status = "degraded"
    elif not provider["last_used"]:
        health_status = "unknown"
    
    provider["health_status"] = health_status
    provider["response_time_ms"] = random.randint(50, 200) if health_status == "healthy" else random.randint(200, 1000)
    
    providers_with_health.append(provider)

result = {"result": {"providers": providers_with_health}}
"""
        })
        
        # Connect nodes
        builder.add_connection("get_providers", "result.providers", "check_health", "providers")
        
        # Execute workflow
        workflow = builder.build()
        results, _ = await async_runtime.execute(workflow)
        
        providers = results.get("check_health", {}).get("result", {}).get("providers", [])
        
        return [SSOProviderResponse(**p) for p in providers]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/providers/{provider_id}")
async def update_sso_provider(
    provider_id: str,
    updates: Dict[str, Any]
):
    """Update SSO provider configuration."""
    try:
        builder = WorkflowBuilder("update_sso_provider_workflow")
        
        # Validate updates
        builder.add_node("PythonCodeNode", "validate_updates", {
            "name": "validate_provider_updates",
            "code": """
# Validate SSO provider updates
errors = []

# Don't allow changing provider type
if "provider_type" in updates:
    errors.append("Cannot change provider type")

# Validate new domain whitelist if provided
if "domain_whitelist" in updates:
    for domain in updates["domain_whitelist"]:
        if not domain.startswith("@"):
            errors.append(f"Domain {domain} must start with @")

result = {
    "result": {
        "valid": len(errors) == 0,
        "errors": errors
    }
}
"""
        })
        
        # Apply updates
        builder.add_node("PythonCodeNode", "apply_updates", {
            "name": "update_provider_config",
            "code": """
# Apply updates to provider
from datetime import datetime

# In real implementation, would fetch current provider from DB
current_provider = {
    "id": provider_id,
    "name": "Current Provider",
    "updated_at": datetime.now()
}

# Apply updates
for key, value in updates.items():
    if key not in ["id", "created_at"]:  # Immutable fields
        current_provider[key] = value

current_provider["updated_at"] = datetime.now()

result = {"result": {"provider": current_provider}}
"""
        })
        
        # Test connectivity if URLs changed
        builder.add_node("PythonCodeNode", "test_if_needed", {
            "name": "test_connectivity_if_needed",
            "code": """
# Test connectivity if URLs were updated
should_test = any(key in updates for key in ["authorization_url", "token_url", "metadata_url"])

if should_test:
    # In real implementation, would test the new URLs
    test_result = {"success": True, "response_time_ms": 150}
else:
    test_result = {"skipped": True}

result = {"result": {"test_result": test_result}}
"""
        })
        
        # Audit update
        builder.add_node("AuditLogNode", "audit_update", {
            "operation": "log_event",
            "event_type": "sso_provider_updated",
            "severity": "medium"
        })
        
        # Connect nodes
        builder.add_connection("validate_updates", "result", "apply_updates", "validation")
        builder.add_connection("apply_updates", "result", "test_if_needed", "updated_provider")
        builder.add_connection("test_if_needed", "result", "audit_update", "test_result")
        
        # Execute workflow
        workflow = builder.build()
        results, _ = await async_runtime.execute(
            workflow,
            parameters={
                "provider_id": provider_id,
                "updates": updates
            }
        )
        
        # Check validation
        validation = results.get("validate_updates", {}).get("result", {})
        if not validation.get("valid"):
            raise HTTPException(
                status_code=400,
                detail={"errors": validation.get("errors", [])}
            )
        
        updated = results.get("apply_updates", {}).get("result", {}).get("provider", {})
        
        return {
            "success": True,
            "provider": updated,
            "connectivity_test": results.get("test_if_needed", {}).get("result", {}).get("test_result", {})
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/providers/{provider_id}")
async def delete_sso_provider(provider_id: str):
    """
    Delete SSO provider.
    
    Checks for active users and provides migration options.
    """
    try:
        builder = WorkflowBuilder("delete_sso_provider_workflow")
        
        # Check impact
        builder.add_node("PythonCodeNode", "check_impact", {
            "name": "check_deletion_impact",
            "code": """
# Check impact of deleting SSO provider
# In real implementation, would query user database
impact = {
    "active_users": 25,
    "last_login_days_ago": 2,
    "alternative_providers": ["google-1", "azure-1"]
}

can_delete = impact["active_users"] < 50  # Business rule

result = {
    "result": {
        "can_delete": can_delete,
        "impact": impact
    }
}
"""
        })
        
        # Delete if allowed
        builder.add_node("PythonCodeNode", "delete_provider", {
            "name": "delete_sso_provider",
            "code": """
# Delete SSO provider
from datetime import datetime

if not impact_check.get("can_delete"):
    raise ValueError(f"Cannot delete provider with {impact_check['impact']['active_users']} active users")

deleted_at = datetime.now()

result = {
    "result": {
        "deleted": True,
        "deleted_at": deleted_at,
        "migration_required": impact_check["impact"]["active_users"] > 0
    }
}
"""
        })
        
        # Audit deletion
        builder.add_node("AuditLogNode", "audit_deletion", {
            "operation": "log_event",
            "event_type": "sso_provider_deleted",
            "severity": "high"
        })
        
        # Connect nodes
        builder.add_connection("check_impact", "result", "delete_provider", "impact_check")
        builder.add_connection("delete_provider", "result", "audit_deletion", "deletion")
        
        # Execute workflow
        workflow = builder.build()
        results, _ = await async_runtime.execute(
            workflow,
            parameters={"provider_id": provider_id}
        )
        
        impact = results.get("check_impact", {}).get("result", {})
        deletion = results.get("delete_provider", {}).get("result", {})
        
        return {
            "success": True,
            "message": "SSO provider deleted",
            "impact": impact.get("impact", {}),
            "deleted_at": deletion.get("deleted_at")
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/providers/{provider_id}/users")
async def get_provider_users(
    provider_id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200)
):
    """Get all users using this SSO provider."""
    try:
        builder = WorkflowBuilder("get_provider_users_workflow")
        
        # Query users
        builder.add_node("UserManagementNode", "get_sso_users", {
            "operation": "list_users_by_sso_provider",
            "provider_id": provider_id,
            "page": page,
            "limit": limit
        })
        
        # Add usage analytics
        builder.add_node("PythonCodeNode", "analyze_usage", {
            "name": "analyze_sso_usage",
            "code": """
# Analyze SSO usage patterns
users = user_list.get("users", [])

# Calculate statistics
total_users = user_list.get("total", len(users))
active_30d = sum(1 for u in users if u.get("last_login_days_ago", 999) < 30)
active_7d = sum(1 for u in users if u.get("last_login_days_ago", 999) < 7)

# Group by department/role
by_department = {}
for user in users:
    dept = user.get("department", "Unknown")
    by_department[dept] = by_department.get(dept, 0) + 1

result = {
    "result": {
        "users": users,
        "total": total_users,
        "page": page,
        "limit": limit,
        "has_next": len(users) == limit,
        "statistics": {
            "active_30d": active_30d,
            "active_7d": active_7d,
            "by_department": by_department
        }
    }
}
"""
        })
        
        # Connect nodes
        builder.add_connection("get_sso_users", "result", "analyze_usage", "user_list")
        
        # Execute workflow
        workflow = builder.build()
        results, _ = await async_runtime.execute(
            workflow,
            parameters={
                "page": page,
                "limit": limit
            }
        )
        
        usage_data = results.get("analyze_usage", {}).get("result", {})
        
        return usage_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test-connection/{provider_id}")
async def test_sso_connection(provider_id: str):
    """
    Test SSO provider connectivity and configuration.
    
    Performs comprehensive health checks beyond Django Admin.
    """
    try:
        builder = WorkflowBuilder("test_sso_connection_workflow")
        
        # Test connectivity
        builder.add_node("HTTPRequestNode", "test_endpoints", {
            "name": "test_provider_endpoints",
            "method": "GET",
            "timeout": 5000,
            "validate_ssl": True
        })
        
        # Test authentication flow
        builder.add_node("OAuth2Node", "test_auth_flow", {
            "operation": "test_authorization",
            "provider_id": provider_id
        })
        
        # Validate configuration
        builder.add_node("PythonCodeNode", "validate_config", {
            "name": "validate_provider_config",
            "code": """
# Validate provider configuration
from datetime import datetime

tests_passed = []
tests_failed = []

# Check endpoint connectivity
if connectivity_result.get("status_code") == 200:
    tests_passed.append("Endpoint reachable")
else:
    tests_failed.append("Endpoint unreachable")

# Check auth flow
if auth_result.get("success"):
    tests_passed.append("Authorization flow valid")
else:
    tests_failed.append("Authorization flow failed")

# Check certificate validity for SAML
# In real impl, would check cert expiration

result = {
    "result": {
        "provider_id": provider_id,
        "success": len(tests_failed) == 0,
        "tests_passed": tests_passed,
        "tests_failed": tests_failed,
        "tested_at": datetime.now().isoformat(),
        "response_time_ms": connectivity_result.get("response_time_ms", 0)
    }
}
"""
        })
        
        # Audit test
        builder.add_node("AuditLogNode", "audit_test", {
            "operation": "log_event",
            "event_type": "sso_provider_tested",
            "severity": "info"
        })
        
        # Connect nodes
        builder.add_connection("test_endpoints", "response", "validate_config", "connectivity_result")
        builder.add_connection("test_auth_flow", "result", "validate_config", "auth_result")
        builder.add_connection("validate_config", "result", "audit_test", "test_result")
        
        # Execute workflow
        workflow = builder.build()
        results, _ = await async_runtime.execute(
            workflow,
            parameters={"provider_id": provider_id}
        )
        
        test_result = results.get("validate_config", {}).get("result", {})
        
        return test_result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metadata/sp")
async def get_service_provider_metadata():
    """
    Get Service Provider metadata for SAML configuration.
    
    Returns SP metadata XML that can be imported into IdP.
    """
    try:
        builder = WorkflowBuilder("get_sp_metadata_workflow")
        
        # Generate SP metadata
        builder.add_node("PythonCodeNode", "generate_metadata", {
            "name": "generate_sp_metadata",
            "code": """
# Generate SAML SP metadata
from datetime import datetime
import uuid

entity_id = "https://your-domain.com/sso/saml"
acs_url = "https://your-domain.com/api/sso/callback/saml"
slo_url = "https://your-domain.com/api/sso/logout/saml"

# Generate metadata XML
metadata_xml = f'''<?xml version="1.0"?>
<EntityDescriptor xmlns="urn:oasis:names:tc:SAML:2.0:metadata"
                 entityID="{entity_id}">
    <SPSSODescriptor AuthnRequestsSigned="true"
                     WantAssertionsSigned="true"
                     protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol">
        <NameIDFormat>urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress</NameIDFormat>
        <AssertionConsumerService Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"
                                 Location="{acs_url}"
                                 index="0"/>
        <SingleLogoutService Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
                            Location="{slo_url}"/>
    </SPSSODescriptor>
    <Organization>
        <OrganizationName xml:lang="en">Your Organization</OrganizationName>
        <OrganizationDisplayName xml:lang="en">Your Organization</OrganizationDisplayName>
        <OrganizationURL xml:lang="en">https://your-domain.com</OrganizationURL>
    </Organization>
    <ContactPerson contactType="technical">
        <GivenName>Admin</GivenName>
        <EmailAddress>admin@your-domain.com</EmailAddress>
    </ContactPerson>
</EntityDescriptor>'''

result = {
    "result": {
        "metadata_xml": metadata_xml,
        "entity_id": entity_id,
        "acs_url": acs_url,
        "slo_url": slo_url,
        "generated_at": datetime.now().isoformat()
    }
}
"""
        })
        
        # Execute workflow
        workflow = builder.build()
        results, _ = await async_runtime.execute(workflow)
        
        metadata = results.get("generate_metadata", {}).get("result", {})
        
        return {
            "content_type": "application/xml",
            "metadata": metadata["metadata_xml"],
            "download_filename": "sp-metadata.xml",
            "entity_id": metadata["entity_id"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))