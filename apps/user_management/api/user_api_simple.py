"""
Simple User Management API Implementation using Kailash SDK
"""

import re
import secrets
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from apps.user_management.config.settings import UserManagementConfig
from kailash.middleware import create_gateway
from kailash.runtime.local import LocalRuntime
from kailash.workflow.builder import WorkflowBuilder


class SimpleUserAPI:
    """Simple user management API using Kailash SDK admin nodes"""

    def __init__(self):
        self.config = UserManagementConfig()
        self.runtime = LocalRuntime()

    def create_user_registration_workflow(self):
        """Create workflow for user registration"""
        workflow = WorkflowBuilder()

        # Configure simple data preparation node that gets workflow parameters
        data_prep_code = """
# For WorkflowBuilder, input parameters should be passed as node parameters
# Let's use a simple approach and pass data via configuration
import re
from datetime import datetime

# If we receive parameters via inputs, use them
email_input = locals().get('email', '')
username_input = locals().get('username', '')
password_input = locals().get('password', '')
first_name_input = locals().get('first_name', '')
last_name_input = locals().get('last_name', '')

# Basic validation and prepare data for UserManagementNode
if not email_input:
    result = {"error": "Email is required", "success": False}
elif not username_input:
    result = {"error": "Username is required", "success": False}
elif not password_input:
    result = {"error": "Password is required", "success": False}
else:
    # Prepare data exactly as UserManagementNode expects
    result = {
        "user_data": {
            "email": email_input,
            "username": username_input,
            "first_name": first_name_input,
            "last_name": last_name_input,
            "status": "active"
        },
        "password": password_input
    }
"""

        # Configure token generator
        token_code = """
from datetime import datetime, timedelta
import uuid

# Get user creation result
try:
    user_creation_result = input_data
except NameError:
    user_creation_result = {}

# Extract user from the result
if "user" in user_creation_result:
    user = user_creation_result["user"]
elif "result" in user_creation_result and "user" in user_creation_result["result"]:
    user = user_creation_result["result"]["user"]
else:
    user = user_creation_result  # Assume input_data is the user directly

now = datetime.utcnow()

# Generate simple tokens for test (use proper JWT in production)
access_token = f"access_token_{str(uuid.uuid4())[:8]}_{user.get('user_id', user.get('id', ''))[:8]}"
refresh_token = f"refresh_token_{str(uuid.uuid4())[:8]}_{user.get('user_id', user.get('id', ''))[:8]}"

result = {
    "success": True,
    "user": {
        "id": user.get("user_id", user.get("id")),
        "username": user.get("username"),
        "email": user.get("email")
    },
    "tokens": {
        "access": access_token,
        "refresh": refresh_token
    }
}
"""

        # Add nodes with their configurations
        workflow.add_node("PythonCodeNode", "data_prep", {"code": data_prep_code})
        workflow.add_node(
            "UserManagementNode",
            "user_creator",
            {
                **self.config.NODE_CONFIGS["UserManagementNode"],
                "operation": "create_user",
                "tenant_id": "default",
                "database_config": {
                    "connection_string": self.config.DATABASE_URL,
                    "database_type": "postgresql",
                },
            },
        )
        workflow.add_node("PythonCodeNode", "token_generator", {"code": token_code})

        # Connect nodes - simpler flow
        workflow.add_connection(
            "data_prep", "result.user_data", "user_creator", "user_data"
        )
        workflow.add_connection(
            "data_prep", "result.password", "user_creator", "password"
        )
        workflow.add_connection(
            "user_creator", "result", "token_generator", "input_data"
        )

        return workflow.build(name="user_registration")

    def create_app(self):
        """Create the user management FastAPI application"""
        app = create_gateway()

        # Register workflows
        registration_workflow = self.create_user_registration_workflow()

        @app.post("/api/v1/auth/register")
        async def register(email: str, username: str, password: str):
            """Register a new user"""
            # Pass parameters to the data_prep node specifically
            result = await self.runtime.execute_async(
                registration_workflow,
                {
                    "data_prep": {
                        "email": email,
                        "username": username,
                        "password": password,
                        "first_name": "",
                        "last_name": "",
                    }
                },
            )
            return result

        return app
