"""
User Management System - Main Application
Built with Kailash SDK Admin Nodes
"""

from contextlib import asynccontextmanager
from typing import Any, Dict

import uvicorn
from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from apps.user_management.api.bulk_api import BulkAPI
from apps.user_management.api.role_api import RoleAPI
from apps.user_management.api.search_api import SearchAPI
from apps.user_management.api.user_api import UserAPI
from apps.user_management.config.settings import UserManagementConfig
from apps.user_management.middleware.auth_middleware import (
    AuditMiddleware,
    AuthMiddleware,
    PermissionMiddleware,
    RateLimitMiddleware,
    SessionMiddleware,
)
from apps.user_management.workflows.auth_workflows import AuthWorkflows
from kailash.middleware import create_gateway
from kailash.nodes.admin.schema_manager import AdminSchemaManager
from kailash.runtime.local import LocalRuntime


class UserManagementApp:
    """Main application class for user management system"""

    def __init__(self):
        self.config = UserManagementConfig()
        self.runtime = LocalRuntime()

        # Initialize APIs
        self.user_api = UserAPI()
        self.role_api = RoleAPI()
        self.search_api = SearchAPI()
        self.bulk_api = BulkAPI()
        self.auth_workflows = AuthWorkflows()

        # Initialize middleware
        self.auth_middleware = AuthMiddleware()
        self.permission_middleware = PermissionMiddleware()
        self.rate_limit_middleware = RateLimitMiddleware()
        self.session_middleware = SessionMiddleware()
        self.audit_middleware = AuditMiddleware()

        # Initialize schema manager
        self.schema_manager = AdminSchemaManager(
            {
                "connection_string": self.config.DATABASE_URL,
                "database_type": "postgresql",
            }
        )

    async def setup_database(self):
        """Initialize database schema"""
        print("Setting up database schema...")
        # Note: AdminSchemaManager is synchronous, not async
        self.schema_manager.create_full_schema()
        print("Database schema created successfully")

        # Create default roles
        print("Creating default roles...")
        from kailash.nodes.admin.role_management import RoleManagementNode

        role_node = RoleManagementNode(
            operation="create_role",
            tenant_id="default",
            database_config={
                "connection_string": self.config.DATABASE_URL,
                "database_type": "postgresql",
            },
        )

        for role_data in self.config.DEFAULT_ROLES:
            try:
                result = role_node.execute(
                    operation="create_role",
                    tenant_id="default",
                    database_config={
                        "connection_string": self.config.DATABASE_URL,
                        "database_type": "postgresql",
                    },
                    role_data=role_data,
                )
                if result.get("result", {}).get("success"):
                    print(f"Created role: {role_data['name']}")
            except Exception as e:
                print(
                    f"Failed to create role {role_data.get('name', 'unknown')}: {str(e)}"
                )

    def create_app(self) -> FastAPI:
        """Create and configure the FastAPI application"""

        @asynccontextmanager
        async def lifespan(app: FastAPI):
            # Startup
            await self.setup_database()
            yield
            # Shutdown
            print("Shutting down user management system...")

        # Create app with Kailash gateway
        app = create_gateway(
            title="User Management System",
            description="Enterprise-grade user management built with Kailash SDK",
            version="1.0.0",
            lifespan=lifespan,
        )

        # Configure CORS
        app.add_middleware(
            CORSMiddleware,
            allow_origins=self.config.ALLOWED_ORIGINS,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Add global middleware
        @app.middleware("http")
        async def audit_requests(request: Request, call_next):
            """Audit all requests"""
            # Get current user if authenticated
            current_user = None
            try:
                auth_header = request.headers.get("Authorization")
                if auth_header:
                    current_user = await self.auth_middleware.get_current_user(
                        auth_header
                    )
            except:
                pass

            # Log request
            await self.audit_middleware.log_request(request, current_user)

            # Process request
            response = await call_next(request)
            return response

        # Register API routes
        self._register_auth_routes(app)
        self._register_user_routes(app)
        self._register_role_routes(app)
        self._register_search_routes(app)
        self._register_bulk_routes(app)
        self._register_admin_routes(app)

        # Add health check
        @app.get("/health")
        async def health_check():
            return {"status": "healthy", "service": "user_management"}

        return app

    def _register_auth_routes(self, app: FastAPI):
        """Register authentication routes"""

        @app.post("/api/v1/auth/register")
        async def register(email: str, username: str, password: str):
            """Register a new user"""
            workflow = self.user_api.create_user_registration_workflow()
            result = await self.runtime.execute_async(
                workflow, {"email": email, "username": username, "password": password}
            )
            return result

        @app.post("/api/v1/auth/login")
        async def login(email: str, password: str):
            """Login user"""
            workflow = self.user_api.create_login_workflow()
            result = await self.runtime.execute_async(
                workflow, {"email": email, "password": password}
            )
            return result

        @app.post("/api/v1/auth/logout")
        async def logout(
            current_user: Dict = Depends(self.auth_middleware.get_current_user),
        ):
            """Logout user"""
            # Invalidate session
            return {"success": True, "message": "Logged out successfully"}

        @app.post("/api/v1/auth/refresh")
        async def refresh_token(refresh_token: str):
            """Refresh access token"""
            workflow = self.auth_workflows.create_session_management_workflow()
            result = await self.runtime.execute_async(
                workflow, {"refresh_token": refresh_token}
            )
            return result

        @app.post("/api/v1/auth/password-reset")
        async def request_password_reset(email: str):
            """Request password reset"""
            workflow = self.auth_workflows.create_password_reset_workflow()
            result = await self.runtime.execute_async(workflow, {"email": email})
            return result

        @app.post("/api/v1/auth/password-reset/confirm")
        async def confirm_password_reset(token: str, user_id: str, new_password: str):
            """Confirm password reset"""
            workflow = self.auth_workflows.create_password_reset_confirm_workflow()
            result = await self.runtime.execute_async(
                workflow,
                {"token": token, "user_id": user_id, "new_password": new_password},
            )
            return result

        @app.post("/api/v1/auth/2fa/setup")
        async def setup_2fa(
            current_user: Dict = Depends(self.auth_middleware.get_current_user),
        ):
            """Setup 2FA for user"""
            workflow = self.auth_workflows.create_2fa_setup_workflow()
            result = await self.runtime.execute_async(
                workflow, {"user_id": current_user["id"]}
            )
            return result

    def _register_user_routes(self, app: FastAPI):
        """Register user management routes"""

        @app.get("/api/v1/users/me")
        async def get_current_user(
            current_user: Dict = Depends(self.auth_middleware.get_current_user),
        ):
            """Get current user profile"""
            return {"user": current_user}

        @app.put("/api/v1/users/me")
        async def update_profile(
            updates: Dict[str, Any],
            current_user: Dict = Depends(self.auth_middleware.get_current_user),
        ):
            """Update current user profile"""
            workflow = self.user_api.create_profile_update_workflow()
            result = await self.runtime.execute_async(
                workflow, {"user_id": current_user["id"], "updates": updates}
            )
            return result

        @app.get("/api/v1/users/{user_id}")
        async def get_user(
            user_id: str,
            _: Dict = Depends(
                self.permission_middleware.require_permission("users", "read")
            ),
        ):
            """Get user by ID"""
            return await self.user_api.get_user(user_id)

        @app.put("/api/v1/users/{user_id}")
        async def update_user(
            user_id: str,
            updates: Dict[str, Any],
            _: Dict = Depends(
                self.permission_middleware.require_permission("users", "update")
            ),
        ):
            """Update user by ID"""
            user_node = self.runtime.create_node(
                "UserManagementNode", self.config.NODE_CONFIGS["UserManagementNode"]
            )
            result = await self.runtime.execute_node_async(
                user_node,
                {"operation": "update_user", "user_id": user_id, "updates": updates},
            )
            return result

        @app.delete("/api/v1/users/{user_id}")
        async def delete_user(
            user_id: str,
            _: Dict = Depends(
                self.permission_middleware.require_permission("users", "delete")
            ),
        ):
            """Delete user by ID"""
            user_node = self.runtime.create_node(
                "UserManagementNode", self.config.NODE_CONFIGS["UserManagementNode"]
            )
            result = await self.runtime.execute_node_async(
                user_node, {"operation": "delete_user", "user_id": user_id}
            )
            return result

    def _register_role_routes(self, app: FastAPI):
        """Register role management routes"""
        self.role_api.register_endpoints(app)

    def _register_search_routes(self, app: FastAPI):
        """Register search routes"""
        self.search_api.register_endpoints(app)

    def _register_bulk_routes(self, app: FastAPI):
        """Register bulk operation routes"""
        self.bulk_api.register_endpoints(app)

    def _register_admin_routes(self, app: FastAPI):
        """Register admin-only routes"""

        @app.get("/api/v1/admin/stats")
        async def get_system_stats(
            _: Dict = Depends(self.permission_middleware.require_role("admin")),
        ):
            """Get system statistics"""
            # Get various stats
            stats = {
                "users": {"total": 0, "active": 0, "inactive": 0},
                "roles": {"total": 0},
                "sessions": {"active": 0},
                "security": {"failed_logins_24h": 0, "security_events_24h": 0},
            }

            # Get user stats
            user_node = self.runtime.create_node(
                "UserManagementNode", self.config.NODE_CONFIGS["UserManagementNode"]
            )
            user_result = await self.runtime.execute_node_async(
                user_node, {"operation": "list_users", "limit": 1}
            )
            stats["users"]["total"] = user_result.get("total", 0)

            # Get role stats
            role_node = self.runtime.create_node(
                "RoleManagementNode", self.config.NODE_CONFIGS["RoleManagementNode"]
            )
            role_result = await self.runtime.execute_node_async(
                role_node, {"operation": "list_roles"}
            )
            stats["roles"]["total"] = len(role_result.get("roles", []))

            return stats

        @app.get("/api/v1/admin/audit-logs")
        async def get_audit_logs(
            limit: int = 100,
            offset: int = 0,
            severity: Optional[str] = None,
            _: Dict = Depends(self.permission_middleware.require_role("admin")),
        ):
            """Get audit logs"""
            audit_node = self.runtime.create_node(
                "EnterpriseAuditLogNode",
                self.config.NODE_CONFIGS["EnterpriseAuditLogNode"],
            )

            filters = {}
            if severity:
                filters["severity"] = severity

            result = await self.runtime.execute_node_async(
                audit_node,
                {
                    "operation": "search_logs",
                    "limit": limit,
                    "offset": offset,
                    "filters": filters,
                },
            )
            return result

        @app.get("/api/v1/admin/security-events")
        async def get_security_events(
            limit: int = 100,
            event_type: Optional[str] = None,
            _: Dict = Depends(self.permission_middleware.require_role("admin")),
        ):
            """Get security events"""
            security_node = self.runtime.create_node(
                "EnterpriseSecurityEventNode",
                self.config.NODE_CONFIGS["EnterpriseSecurityEventNode"],
            )

            filters = {}
            if event_type:
                filters["event_type"] = event_type

            result = await self.runtime.execute_node_async(
                security_node,
                {"operation": "get_events", "limit": limit, "filters": filters},
            )
            return result


def create_user_management_app() -> FastAPI:
    """Factory function to create the user management app"""
    app_manager = UserManagementApp()
    return app_manager.create_app()


if __name__ == "__main__":
    # Create and run the app
    app = create_user_management_app()
    uvicorn.run(app, host="0.0.0.0", port=8000)
