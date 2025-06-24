"""
User Management API Implementation using Kailash SDK
"""

import re
import secrets
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import bcrypt
import jwt

from apps.user_management.config.settings import UserManagementConfig
from kailash.middleware import create_gateway
from kailash.runtime.local import LocalRuntime
from kailash.workflow.builder import WorkflowBuilder


class UserAPI:
    """User management API using Kailash SDK admin nodes"""

    def __init__(self):
        self.config = UserManagementConfig()
        self.runtime = LocalRuntime()

    def create_user_registration_workflow(self) -> WorkflowBuilder:
        """Create workflow for user registration"""
        workflow = WorkflowBuilder("user_registration")

        # Add nodes
        workflow.add_node("validator", "PythonCodeNode")
        workflow.add_node("password_hasher", "PythonCodeNode")
        workflow.add_node(
            "user_creator",
            "UserManagementNode",
            self.config.NODE_CONFIGS["UserManagementNode"],
        )
        workflow.add_node(
            "role_assigner",
            "RoleManagementNode",
            self.config.NODE_CONFIGS["RoleManagementNode"],
        )
        workflow.add_node(
            "audit_logger",
            "EnterpriseAuditLogNode",
            self.config.NODE_CONFIGS["EnterpriseAuditLogNode"],
        )
        workflow.add_node("token_generator", "PythonCodeNode")

        # Connect nodes
        workflow.add_connection("input", "validator", "data", "input")
        workflow.add_connection("validator", "password_hasher", "result", "input")
        workflow.add_connection("password_hasher", "user_creator", "result", "input")
        workflow.add_connection("user_creator", "role_assigner", "result", "input")
        workflow.add_connection("role_assigner", "audit_logger", "result", "input")
        workflow.add_connection("audit_logger", "token_generator", "result", "input")
        workflow.add_connection("token_generator", "output", "result", "result")

        # Configure validator
        validator_code = """
import re
from datetime import datetime

email = input_data.get("email", "")
password = input_data.get("password", "")
username = input_data.get("username", "")
errors = []

# Email validation
email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
if not re.match(email_pattern, email):
    errors.append("Invalid email format")

# Password validation
if len(password) < 8:
    errors.append("Password must be at least 8 characters")
if not re.search(r'[A-Z]', password):
    errors.append("Password must contain uppercase letter")
if not re.search(r'[a-z]', password):
    errors.append("Password must contain lowercase letter")
if not re.search(r'[0-9]', password):
    errors.append("Password must contain number")
if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
    errors.append("Password must contain special character")

# Username validation
if len(username) < 3:
    errors.append("Username must be at least 3 characters")
if not re.match(r'^[a-zA-Z0-9_]+$', username):
    errors.append("Username can only contain letters, numbers, and underscores")

if errors:
    result = {"success": False, "errors": errors}
else:
    result = {
        "success": True,
        "user_data": {
            "email": email,
            "username": username,
            "password": password,
            "created_at": datetime.utcnow().isoformat()
        }
    }
"""
        workflow.update_node("validator", {"code": validator_code})

        # Configure password hasher
        hasher_code = """
import bcrypt

if not input_data.get("success"):
    result = input_data
else:
    user_data = input_data["user_data"]
    password = user_data["password"].encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password, salt).decode('utf-8')

    user_data["password_hash"] = hashed
    del user_data["password"]  # Remove plain password

    result = {
        "operation": "create_user",
        "data": user_data
    }
"""
        workflow.update_node("password_hasher", {"code": hasher_code})

        # Configure role assigner
        workflow.update_node(
            "role_assigner",
            {
                "operation": "assign_role_to_user",
                "data": {"user_id": "$.result.user.id", "role_name": "user"},
            },
        )

        # Configure audit logger
        workflow.update_node(
            "audit_logger",
            {
                "operation": "log_event",
                "event_type": "user_created",
                "severity": "low",
                "details": {
                    "user_id": "$.result.user.id",
                    "username": "$.result.user.username",
                },
            },
        )

        # Configure token generator
        token_code = f"""
import jwt
from datetime import datetime, timedelta

user = input_data["result"]["user"]
now = datetime.utcnow()

# Generate access token
access_payload = {{
    "user_id": user["id"],
    "username": user["username"],
    "email": user["email"],
    "exp": now + timedelta(hours=1),
    "iat": now
}}
access_token = jwt.encode(access_payload, "{self.config.JWT_SECRET_KEY}", algorithm="{self.config.JWT_ALGORITHM}")

# Generate refresh token
refresh_payload = {{
    "user_id": user["id"],
    "type": "refresh",
    "exp": now + timedelta(days=30),
    "iat": now
}}
refresh_token = jwt.encode(refresh_payload, "{self.config.JWT_SECRET_KEY}", algorithm="{self.config.JWT_ALGORITHM}")

result = {{
    "success": True,
    "user": {{
        "id": user["id"],
        "username": user["username"],
        "email": user["email"]
    }},
    "tokens": {{
        "access": access_token,
        "refresh": refresh_token
    }}
}}
"""
        workflow.update_node("token_generator", {"code": token_code})

        return workflow

    def create_login_workflow(self) -> WorkflowBuilder:
        """Create workflow for user login"""
        workflow = WorkflowBuilder("user_login")

        # Add nodes
        workflow.add_node(
            "user_fetcher",
            "UserManagementNode",
            self.config.NODE_CONFIGS["UserManagementNode"],
        )
        workflow.add_node("password_verifier", "PythonCodeNode")
        workflow.add_node(
            "permission_checker",
            "PermissionCheckNode",
            self.config.NODE_CONFIGS["PermissionCheckNode"],
        )
        workflow.add_node("session_creator", "PythonCodeNode")
        workflow.add_node(
            "audit_logger",
            "EnterpriseAuditLogNode",
            self.config.NODE_CONFIGS["EnterpriseAuditLogNode"],
        )
        workflow.add_node(
            "security_checker",
            "EnterpriseSecurityEventNode",
            self.config.NODE_CONFIGS["EnterpriseSecurityEventNode"],
        )

        # Connect nodes
        workflow.add_connection("input", "user_fetcher", "data", "input")
        workflow.add_connection("user_fetcher", "password_verifier", "result", "input")
        workflow.add_connection(
            "password_verifier", "permission_checker", "result", "input"
        )
        workflow.add_connection(
            "permission_checker", "session_creator", "result", "input"
        )
        workflow.add_connection("session_creator", "audit_logger", "result", "input")
        workflow.add_connection("audit_logger", "security_checker", "result", "input")
        workflow.add_connection("security_checker", "output", "result", "result")

        # Configure user fetcher
        workflow.update_node(
            "user_fetcher",
            {
                "operation": "get_user",
                "identifier": "$.email",
                "identifier_type": "email",
            },
        )

        # Configure password verifier
        verifier_code = """
import bcrypt

user = input_data.get("user")
if not user:
    result = {"success": False, "error": "User not found"}
else:
    password = input_data.get("password", "").encode('utf-8')
    stored_hash = user.get("password_hash", "").encode('utf-8')

    if bcrypt.checkpw(password, stored_hash):
        result = {
            "success": True,
            "user": user,
            "check_permissions": {
                "user_id": user["id"],
                "resource": "login",
                "action": "access"
            }
        }
    else:
        result = {"success": False, "error": "Invalid credentials"}
"""
        workflow.update_node("password_verifier", {"code": verifier_code})

        # Configure session creator
        session_code = f"""
import jwt
import uuid
from datetime import datetime, timedelta

if input_data.get("allowed"):
    user = input_data["user"]
    now = datetime.utcnow()
    session_id = str(uuid.uuid4())

    # Create session tokens
    access_payload = {{
        "user_id": user["id"],
        "username": user["username"],
        "email": user["email"],
        "session_id": session_id,
        "exp": now + timedelta(hours=1),
        "iat": now
    }}
    access_token = jwt.encode(access_payload, "{self.config.JWT_SECRET_KEY}", algorithm="{self.config.JWT_ALGORITHM}")

    refresh_payload = {{
        "user_id": user["id"],
        "session_id": session_id,
        "type": "refresh",
        "exp": now + timedelta(days=30),
        "iat": now
    }}
    refresh_token = jwt.encode(refresh_payload, "{self.config.JWT_SECRET_KEY}", algorithm="{self.config.JWT_ALGORITHM}")

    result = {{
        "success": True,
        "user": {{
            "id": user["id"],
            "username": user["username"],
            "email": user["email"]
        }},
        "session": {{
            "id": session_id,
            "created_at": now.isoformat()
        }},
        "tokens": {{
            "access": access_token,
            "refresh": refresh_token
        }}
    }}
else:
    result = {{"success": False, "error": "Access denied"}}
"""
        workflow.update_node("session_creator", {"code": session_code})

        return workflow

    def create_profile_update_workflow(self) -> WorkflowBuilder:
        """Create workflow for profile updates"""
        workflow = WorkflowBuilder("profile_update")

        # Add nodes
        workflow.add_node(
            "permission_checker",
            "PermissionCheckNode",
            self.config.NODE_CONFIGS["PermissionCheckNode"],
        )
        workflow.add_node("validator", "PythonCodeNode")
        workflow.add_node(
            "updater",
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
        workflow.add_connection("permission_checker", "validator", "result", "input")
        workflow.add_connection("validator", "updater", "result", "input")
        workflow.add_connection("updater", "audit_logger", "result", "input")
        workflow.add_connection("audit_logger", "output", "result", "result")

        # Configure permission checker
        workflow.update_node(
            "permission_checker",
            {
                "user_id": "$.user_id",
                "resource": "profile",
                "action": "update",
                "resource_attributes": {"owner_id": "$.user_id"},
            },
        )

        # Configure validator
        validator_code = """
if not input_data.get("allowed"):
    result = {"success": False, "error": "Permission denied"}
else:
    updates = input_data.get("updates", {})
    validated_updates = {}

    # Validate allowed fields
    allowed_fields = ["first_name", "last_name", "phone", "bio", "avatar_url", "preferences"]
    for field, value in updates.items():
        if field in allowed_fields:
            validated_updates[field] = value

    result = {
        "operation": "update_profile",
        "user_id": input_data["user_id"],
        "updates": validated_updates
    }
"""
        workflow.update_node("validator", {"code": validator_code})

        return workflow

    def create_app(self):
        """Create the user management FastAPI application"""
        app = create_gateway()

        # Register workflows
        registration_workflow = self.create_user_registration_workflow()
        login_workflow = self.create_login_workflow()
        profile_workflow = self.create_profile_update_workflow()

        @app.post("/api/v1/auth/register")
        async def register(email: str, username: str, password: str):
            """Register a new user"""
            result = await self.runtime.execute_async(
                registration_workflow,
                {"email": email, "username": username, "password": password},
            )
            return result

        @app.post("/api/v1/auth/login")
        async def login(email: str, password: str):
            """Login user"""
            result = await self.runtime.execute_async(
                login_workflow, {"email": email, "password": password}
            )
            return result

        @app.put("/api/v1/users/{user_id}/profile")
        async def update_profile(user_id: str, updates: Dict[str, Any]):
            """Update user profile"""
            result = await self.runtime.execute_async(
                profile_workflow, {"user_id": user_id, "updates": updates}
            )
            return result

        @app.get("/api/v1/users/{user_id}")
        async def get_user(user_id: str):
            """Get user details"""
            user_node = workflow.create_node(
                "UserManagementNode", self.config.NODE_CONFIGS["UserManagementNode"]
            )
            result = await self.runtime.execute_node_async(
                user_node, {"operation": "get_user", "user_id": user_id}
            )
            return result

        return app
