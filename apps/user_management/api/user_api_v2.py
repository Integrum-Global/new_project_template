"""User Management API v2 - Using Workflow Parameter Injection.

This version demonstrates the new workflow-level parameter injection feature
for cleaner and more maintainable code.
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr

from kailash import Workflow, WorkflowBuilder
from kailash.nodes.admin import RoleManagementNode, UserManagementNode
from kailash.nodes.code import PythonCodeNode
from kailash.runtime import LocalRuntime

logger = logging.getLogger(__name__)


# Pydantic models
class UserRegistration(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: str = "user"


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


class UserManagementAPIv2:
    """User Management API using workflow parameter injection."""

    def __init__(self, database_url: str, tenant_id: str = "default"):
        self.database_url = database_url
        self.tenant_id = tenant_id
        self.runtime = LocalRuntime(debug=True)
        self.router = APIRouter(prefix="/api/v2/users", tags=["users-v2"])
        self._setup_routes()
        self._build_workflows()

    def _build_workflows(self):
        """Build reusable workflows with parameter injection support."""

        # Registration workflow
        self.registration_workflow = self._build_registration_workflow()

        # Authentication workflow
        self.auth_workflow = self._build_auth_workflow()

        # User management workflow
        self.mgmt_workflow = self._build_management_workflow()

    def _build_registration_workflow(self) -> Workflow:
        """Build user registration workflow with validation."""
        builder = WorkflowBuilder()

        # Validation node
        def validate_registration(email: str, password: str, full_name: str) -> dict:
            errors = []
            if len(password) < 8:
                errors.append("Password must be at least 8 characters")
            if not full_name.strip():
                errors.append("Full name is required")

            return {"valid": len(errors) == 0, "errors": errors, "email": email}

        # User creation wrapper
        def create_user_wrapper(
            email: str,
            password: str,
            full_name: str,
            role: str,
            tenant_id: str,
            db_config: dict,
        ) -> dict:
            node = UserManagementNode(
                operation="create_user", tenant_id=tenant_id, database_config=db_config
            )

            result = node.execute(
                user_data={"email": email, "full_name": full_name, "role": role},
                password=password,
            )

            return result.get("result", {})

        # Add nodes
        builder.add_node(
            PythonCodeNode.from_function(validate_registration), "validator"
        )
        builder.add_node(PythonCodeNode.from_function(create_user_wrapper), "creator")

        # Connect with validation check
        builder.connect("validator", "creator", {"result.email": "email"})

        # Define parameter mappings
        builder.add_workflow_inputs(
            "validator",
            {"email": "email", "password": "password", "full_name": "full_name"},
        )

        builder.add_workflow_inputs(
            "creator",
            {
                "email": "email",
                "password": "password",
                "full_name": "full_name",
                "role": "role",
                "tenant_id": "tenant_id",
                "database_config": "db_config",
            },
        )

        return builder.build("registration")

    def _build_auth_workflow(self) -> Workflow:
        """Build authentication workflow."""
        workflow = Workflow("auth", "User authentication")

        # Simple auth node
        def authenticate(
            email: str, password: str, tenant_id: str, db_config: dict
        ) -> dict:
            node = UserManagementNode(
                operation="verify_password",
                tenant_id=tenant_id,
                database_config=db_config,
            )

            # First get the user
            get_node = UserManagementNode(
                operation="get_user", tenant_id=tenant_id, database_config=db_config
            )

            user_result = get_node.execute(identifier=email)
            if not user_result.get("result"):
                return {"authenticated": False, "error": "User not found"}

            # Verify password
            verify_result = node.execute(identifier=email, password=password)

            return {
                "authenticated": verify_result.get("result", {}).get("valid", False),
                "user": (
                    user_result.get("result")
                    if verify_result.get("result", {}).get("valid")
                    else None
                ),
            }

        workflow.add_node("auth", PythonCodeNode.from_function(authenticate))

        return workflow

    def _build_management_workflow(self) -> Workflow:
        """Build user management workflow for updates."""
        workflow = Workflow("management", "User management")

        # Update wrapper node
        def update_user(
            email: str, updates: dict, tenant_id: str, db_config: dict
        ) -> dict:
            node = UserManagementNode(
                operation="update_user", tenant_id=tenant_id, database_config=db_config
            )

            result = node.execute(identifier=email, updates=updates)

            return result.get("result", {})

        workflow.add_node("updater", PythonCodeNode.from_function(update_user))

        return workflow

    def _setup_routes(self):
        """Setup API routes."""

        @self.router.post("/register")
        async def register(user: UserRegistration):
            """Register a new user with validation."""
            try:
                # Execute with workflow-level parameters
                results, _ = self.runtime.execute(
                    self.registration_workflow,
                    parameters={
                        "email": user.email,
                        "password": user.password,
                        "full_name": user.full_name,
                        "role": user.role,
                        "tenant_id": self.tenant_id,
                        "db_config": {
                            "connection_string": self.database_url,
                            "database_type": "postgresql",
                        },
                    },
                )

                # Check validation result
                validation = results.get("validator", {}).get("result", {})
                if not validation.get("valid"):
                    raise HTTPException(
                        status_code=400, detail={"errors": validation.get("errors", [])}
                    )

                # Return created user
                created = results.get("creator", {}).get("result", {})
                if not created:
                    raise HTTPException(status_code=500, detail="User creation failed")

                return {
                    "status": "success",
                    "user": {
                        "id": created.get("user_id"),
                        "email": created.get("email"),
                        "role": created.get("role"),
                    },
                }

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Registration error: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.router.post("/login")
        async def login(credentials: UserLogin):
            """Authenticate a user."""
            try:
                results, _ = self.runtime.execute(
                    self.auth_workflow,
                    parameters={
                        "email": credentials.email,
                        "password": credentials.password,
                        "tenant_id": self.tenant_id,
                        "db_config": {
                            "connection_string": self.database_url,
                            "database_type": "postgresql",
                        },
                    },
                )

                auth_result = results.get("auth", {}).get("result", {})

                if not auth_result.get("authenticated"):
                    raise HTTPException(
                        status_code=401,
                        detail=auth_result.get("error", "Invalid credentials"),
                    )

                return {
                    "status": "success",
                    "user": auth_result.get("user"),
                    "token": "mock-jwt-token",  # In real app, generate JWT
                }

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Login error: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.router.patch("/{email}")
        async def update_user(email: str, updates: UserUpdate):
            """Update user information."""
            try:
                # Build updates dict
                update_data = {}
                if updates.email:
                    update_data["email"] = updates.email
                if updates.full_name:
                    update_data["full_name"] = updates.full_name
                if updates.role:
                    update_data["role"] = updates.role
                if updates.is_active is not None:
                    update_data["is_active"] = updates.is_active

                results, _ = self.runtime.execute(
                    self.mgmt_workflow,
                    parameters={
                        "email": email,
                        "updates": update_data,
                        "tenant_id": self.tenant_id,
                        "db_config": {
                            "connection_string": self.database_url,
                            "database_type": "postgresql",
                        },
                    },
                )

                updated = results.get("updater", {}).get("result", {})
                if not updated:
                    raise HTTPException(status_code=404, detail="User not found")

                return {"status": "success", "user": updated}

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Update error: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.router.get("/workflows/info")
        async def workflow_info():
            """Get information about the workflows and parameter injection."""
            return {
                "workflows": {
                    "registration": {
                        "nodes": list(
                            self.registration_workflow._node_instances.keys()
                        ),
                        "accepts_parameters": [
                            "email",
                            "password",
                            "full_name",
                            "role",
                        ],
                        "description": "Validates and creates new users",
                    },
                    "authentication": {
                        "nodes": list(self.auth_workflow._node_instances.keys()),
                        "accepts_parameters": ["email", "password"],
                        "description": "Authenticates users",
                    },
                    "management": {
                        "nodes": list(self.mgmt_workflow._node_instances.keys()),
                        "accepts_parameters": ["email", "updates"],
                        "description": "Updates user information",
                    },
                },
                "parameter_injection": {
                    "enabled": True,
                    "version": "0.6.2",
                    "benefits": [
                        "Simplified API - pass flat parameter dict",
                        "Automatic routing to correct nodes",
                        "No need for node ID knowledge",
                        "Backward compatible with node-specific format",
                    ],
                },
            }


# Example usage
if __name__ == "__main__":
    import os

    import uvicorn
    from fastapi import FastAPI

    app = FastAPI(title="User Management API v2")

    # Initialize API
    api = UserManagementAPIv2(
        database_url=os.getenv(
            "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/kailash"
        ),
        tenant_id="production",
    )

    app.include_router(api.router)

    @app.get("/")
    async def root():
        return {
            "service": "User Management API v2",
            "version": "2.0.0",
            "features": [
                "Workflow parameter injection",
                "Simplified parameter passing",
                "Automatic parameter routing",
            ],
        }

    # Run server
    uvicorn.run(app, host="0.0.0.0", port=8001)
