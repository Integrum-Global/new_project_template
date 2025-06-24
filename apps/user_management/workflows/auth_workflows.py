"""
Authentication Workflows including password reset, 2FA, and session management
"""

import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from apps.user_management.config.settings import UserManagementConfig
from kailash.runtime.local import LocalRuntime
from kailash.workflow.builder import WorkflowBuilder


class AuthWorkflows:
    """Authentication and session management workflows"""

    def __init__(self):
        self.config = UserManagementConfig()
        self.runtime = LocalRuntime()

    def create_password_reset_workflow(self) -> WorkflowBuilder:
        """Create workflow for password reset process"""
        workflow = WorkflowBuilder("password_reset")

        # Add nodes
        workflow.add_node(
            "user_finder",
            "UserManagementNode",
            self.config.NODE_CONFIGS["UserManagementNode"],
        )
        workflow.add_node("token_generator", "PythonCodeNode")
        workflow.add_node("token_storage", "PythonCodeNode")
        workflow.add_node(
            "email_sender",
            "EmailNode",
            {"smtp_config": {"host": "localhost", "port": 1025}},
        )
        workflow.add_node(
            "audit_logger",
            "EnterpriseAuditLogNode",
            self.config.NODE_CONFIGS["EnterpriseAuditLogNode"],
        )
        workflow.add_node(
            "security_event",
            "EnterpriseSecurityEventNode",
            self.config.NODE_CONFIGS["EnterpriseSecurityEventNode"],
        )

        # Connect nodes
        workflow.add_connection("input", "user_finder", "data", "input")
        workflow.add_connection("user_finder", "token_generator", "result", "input")
        workflow.add_connection("token_generator", "token_storage", "result", "input")
        workflow.add_connection("token_storage", "email_sender", "result", "input")
        workflow.add_connection("email_sender", "audit_logger", "result", "input")
        workflow.add_connection("audit_logger", "security_event", "result", "input")
        workflow.add_connection("security_event", "output", "result", "result")

        # Configure user finder
        workflow.update_node(
            "user_finder",
            {
                "operation": "get_user",
                "identifier": "$.email",
                "identifier_type": "email",
            },
        )

        # Configure token generator
        token_code = """
import secrets
from datetime import datetime, timedelta

user = input_data.get("user")
if not user:
    result = {"success": False, "error": "User not found"}
else:
    # Generate secure reset token
    token = secrets.token_urlsafe(32)
    expires_at = (datetime.utcnow() + timedelta(hours=24)).isoformat()

    result = {
        "success": True,
        "user": user,
        "reset_token": {
            "token": token,
            "user_id": user["id"],
            "expires_at": expires_at,
            "created_at": datetime.utcnow().isoformat()
        }
    }
"""
        workflow.update_node("token_generator", {"code": token_code})

        # Configure token storage
        storage_code = '''
# In production, store this in Redis or database
# For now, we'll prepare the data for email
reset_data = input_data["reset_token"]
user = input_data["user"]

# Create reset URL
base_url = "https://example.com/reset-password"
reset_url = f"{base_url}?token={reset_data['token']}&user={user['id']}"

result = {
    "success": True,
    "email_data": {
        "to": user["email"],
        "subject": "Password Reset Request",
        "body": f"""
Hello {user.get('username', 'User')},

You requested a password reset. Click the link below to reset your password:

{reset_url}

This link will expire in 24 hours.

If you didn't request this, please ignore this email.

Best regards,
The Team
        """,
        "html": f"""
<h2>Password Reset Request</h2>
<p>Hello {user.get('username', 'User')},</p>
<p>You requested a password reset. Click the link below to reset your password:</p>
<p><a href="{reset_url}">Reset Password</a></p>
<p>This link will expire in 24 hours.</p>
<p>If you didn't request this, please ignore this email.</p>
<p>Best regards,<br>The Team</p>
        """
    },
    "reset_token": reset_data
}
'''
        workflow.update_node("token_storage", {"code": storage_code})

        # Configure audit logger
        workflow.update_node(
            "audit_logger",
            {
                "operation": "log_event",
                "event_type": "password_reset_requested",
                "severity": "medium",
                "details": {
                    "user_id": "$.reset_token.user_id",
                    "email": "$.email_data.to",
                },
            },
        )

        # Configure security event
        workflow.update_node(
            "security_event",
            {
                "operation": "log_event",
                "event_type": "password_reset",
                "severity": "low",
                "details": {
                    "user_id": "$.reset_token.user_id",
                    "ip_address": "$.ip_address",
                },
            },
        )

        return workflow

    def create_password_reset_confirm_workflow(self) -> WorkflowBuilder:
        """Create workflow to confirm password reset with token"""
        workflow = WorkflowBuilder("password_reset_confirm")

        # Add nodes
        workflow.add_node("token_validator", "PythonCodeNode")
        workflow.add_node("password_hasher", "PythonCodeNode")
        workflow.add_node(
            "user_updater",
            "UserManagementNode",
            self.config.NODE_CONFIGS["UserManagementNode"],
        )
        workflow.add_node("session_invalidator", "PythonCodeNode")
        workflow.add_node(
            "audit_logger",
            "EnterpriseAuditLogNode",
            self.config.NODE_CONFIGS["EnterpriseAuditLogNode"],
        )

        # Connect nodes
        workflow.add_connection("input", "token_validator", "data", "input")
        workflow.add_connection("token_validator", "password_hasher", "result", "input")
        workflow.add_connection("password_hasher", "user_updater", "result", "input")
        workflow.add_connection(
            "user_updater", "session_invalidator", "result", "input"
        )
        workflow.add_connection(
            "session_invalidator", "audit_logger", "result", "input"
        )
        workflow.add_connection("audit_logger", "output", "result", "result")

        # Configure token validator
        validator_code = """
from datetime import datetime

token = input_data.get("token")
user_id = input_data.get("user_id")
new_password = input_data.get("new_password")

# In production, validate token from Redis/database
# For now, we'll do basic validation
if not token or len(token) < 32:
    result = {"success": False, "error": "Invalid token"}
else:
    # Validate password requirements
    errors = []
    if len(new_password) < 8:
        errors.append("Password must be at least 8 characters")

    if errors:
        result = {"success": False, "errors": errors}
    else:
        result = {
            "success": True,
            "user_id": user_id,
            "new_password": new_password
        }
"""
        workflow.update_node("token_validator", {"code": validator_code})

        # Configure password hasher
        hasher_code = """
import bcrypt

if not input_data.get("success"):
    result = input_data
else:
    password = input_data["new_password"].encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password, salt).decode('utf-8')

    result = {
        "operation": "set_password",
        "user_id": input_data["user_id"],
        "password_hash": hashed
    }
"""
        workflow.update_node("password_hasher", {"code": hasher_code})

        # Configure session invalidator
        invalidator_code = """
# Invalidate all user sessions after password reset
result = {
    "success": True,
    "user_id": input_data["user"]["id"],
    "sessions_invalidated": True,
    "message": "Password reset successful. Please login with your new password."
}
"""
        workflow.update_node("session_invalidator", {"code": invalidator_code})

        return workflow

    def create_2fa_setup_workflow(self) -> WorkflowBuilder:
        """Create workflow for 2FA setup"""
        workflow = WorkflowBuilder("2fa_setup")

        # Add nodes
        workflow.add_node(
            "permission_checker",
            "PermissionCheckNode",
            self.config.NODE_CONFIGS["PermissionCheckNode"],
        )
        workflow.add_node("secret_generator", "PythonCodeNode")
        workflow.add_node("qr_generator", "PythonCodeNode")
        workflow.add_node(
            "user_updater",
            "UserManagementNode",
            self.config.NODE_CONFIGS["UserManagementNode"],
        )
        workflow.add_node(
            "audit_logger",
            "EnterpriseAuditLogNode",
            self.config.NODE_CONFIGS["EnterpriseAuditLogNode"],
        )

        # Connect nodes
        workflow.add_connection("input", "permission_checker", "data", "input")
        workflow.add_connection(
            "permission_checker", "secret_generator", "result", "input"
        )
        workflow.add_connection("secret_generator", "qr_generator", "result", "input")
        workflow.add_connection("qr_generator", "user_updater", "result", "input")
        workflow.add_connection("user_updater", "audit_logger", "result", "input")
        workflow.add_connection("audit_logger", "output", "result", "result")

        # Configure secret generator
        secret_code = """
import pyotp
import base64

if not input_data.get("allowed"):
    result = {"success": False, "error": "Permission denied"}
else:
    user_id = input_data["user_id"]

    # Generate TOTP secret
    secret = pyotp.random_base32()

    result = {
        "success": True,
        "user_id": user_id,
        "totp_secret": secret,
        "issuer": "UserManagementApp"
    }
"""
        workflow.update_node("secret_generator", {"code": secret_code})

        # Configure QR generator
        qr_code = """
# Generate provisioning URI for QR code
user_id = input_data["user_id"]
secret = input_data["totp_secret"]
issuer = input_data["issuer"]

# Create TOTP URI
totp_uri = f"otpauth://totp/{issuer}:{user_id}?secret={secret}&issuer={issuer}"

result = {
    "operation": "update_user",
    "user_id": user_id,
    "updates": {
        "two_factor_secret": secret,
        "two_factor_enabled": False,  # Will be enabled after verification
        "two_factor_backup_codes": []  # Generate backup codes
    },
    "provisioning_uri": totp_uri
}
"""
        workflow.update_node("qr_generator", {"code": qr_code})

        return workflow

    def create_session_management_workflow(self) -> WorkflowBuilder:
        """Create workflow for session management"""
        workflow = WorkflowBuilder("session_management")

        # Add nodes
        workflow.add_node("session_validator", "PythonCodeNode")
        workflow.add_node("session_refresher", "PythonCodeNode")
        workflow.add_node("activity_tracker", "PythonCodeNode")
        workflow.add_node(
            "security_checker",
            "EnterpriseSecurityEventNode",
            self.config.NODE_CONFIGS["EnterpriseSecurityEventNode"],
        )

        # Connect nodes
        workflow.add_connection("input", "session_validator", "data", "input")
        workflow.add_connection(
            "session_validator", "session_refresher", "result", "input"
        )
        workflow.add_connection(
            "session_refresher", "activity_tracker", "result", "input"
        )
        workflow.add_connection(
            "activity_tracker", "security_checker", "result", "input"
        )
        workflow.add_connection("security_checker", "output", "result", "result")

        # Configure session validator
        validator_code = f"""
import jwt
from datetime import datetime

token = input_data.get("access_token")
try:
    # Decode and validate JWT
    payload = jwt.decode(token, "{self.config.JWT_SECRET_KEY}", algorithms=["{self.config.JWT_ALGORITHM}"])

    # Check if session is still valid
    if datetime.utcnow().timestamp() > payload.get("exp", 0):
        result = {{"success": False, "error": "Session expired"}}
    else:
        result = {{
            "success": True,
            "user_id": payload["user_id"],
            "session_id": payload["session_id"],
            "expires_in": payload["exp"] - datetime.utcnow().timestamp()
        }}
except jwt.InvalidTokenError:
    result = {{"success": False, "error": "Invalid token"}}
"""
        workflow.update_node("session_validator", {"code": validator_code})

        # Configure session refresher
        refresher_code = f"""
from datetime import datetime, timedelta
import jwt

if not input_data.get("success"):
    result = input_data
else:
    # Check if session needs refresh (less than 15 minutes remaining)
    expires_in = input_data["expires_in"]

    if expires_in < 900:  # 15 minutes
        # Generate new token
        now = datetime.utcnow()
        new_payload = {{
            "user_id": input_data["user_id"],
            "session_id": input_data["session_id"],
            "exp": now + timedelta(hours=1),
            "iat": now
        }}
        new_token = jwt.encode(new_payload, "{self.config.JWT_SECRET_KEY}", algorithm="{self.config.JWT_ALGORITHM}")

        result = {{
            "success": True,
            "refreshed": True,
            "new_token": new_token,
            "user_id": input_data["user_id"],
            "session_id": input_data["session_id"]
        }}
    else:
        result = {{
            "success": True,
            "refreshed": False,
            "user_id": input_data["user_id"],
            "session_id": input_data["session_id"]
        }}
"""
        workflow.update_node("session_refresher", {"code": refresher_code})

        # Configure activity tracker
        tracker_code = """
from datetime import datetime

# Track user activity
result = {
    "success": True,
    "activity": {
        "user_id": input_data["user_id"],
        "session_id": input_data["session_id"],
        "last_activity": datetime.utcnow().isoformat(),
        "refreshed": input_data.get("refreshed", False)
    },
    "security_check": {
        "user_id": input_data["user_id"],
        "event_type": "session_activity",
        "details": {
            "session_id": input_data["session_id"],
            "ip_address": input_data.get("ip_address"),
            "user_agent": input_data.get("user_agent")
        }
    }
}
"""
        workflow.update_node("activity_tracker", {"code": tracker_code})

        return workflow
