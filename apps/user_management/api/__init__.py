"""
API Routes Package

This package contains all REST API routes for the User Management system.
Routes are organized by functionality and use pure Kailash patterns.
"""

from fastapi import FastAPI

from apps.user_management.api.routes import (
    admin,
    auth,
    compliance,
    permissions,
    roles,
    sso,
    users,
    websocket,
)


async def setup_routes(app: FastAPI):
    """Setup all API routes on the FastAPI application."""

    # Include all route modules
    app.include_router(users.router, prefix="/api/users", tags=["users"])
    app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
    app.include_router(roles.router, prefix="/api/roles", tags=["roles"])
    app.include_router(
        permissions.router, prefix="/api/permissions", tags=["permissions"]
    )
    app.include_router(sso.router, prefix="/api/sso", tags=["sso"])
    app.include_router(compliance.router, prefix="/api/compliance", tags=["compliance"])
    app.include_router(admin.router, prefix="/api/admin", tags=["admin"])

    # Setup WebSocket routes
    await websocket.setup_websocket_routes(app)

    # Add root endpoint
    @app.get("/", tags=["root"])
    async def root():
        """Root endpoint with API information."""
        return {
            "name": "Kailash Enterprise User Management API",
            "version": "1.0.0",
            "features": {
                "authentication": {
                    "sso": True,
                    "mfa": True,
                    "adaptive": True,
                    "providers": ["saml", "oauth2", "azure", "google", "okta"],
                },
                "authorization": {
                    "rbac": True,
                    "abac": True,
                    "ai_reasoning": True,
                    "operators": 16,
                },
                "compliance": {"gdpr": True, "ccpa": True, "audit_logging": True},
                "performance": {
                    "avg_response_ms": 50,
                    "auth_response_ms": 200,
                    "permission_check_ms": 15,
                },
            },
            "endpoints": {
                "docs": "/docs",
                "redoc": "/redoc",
                "openapi": "/openapi.json",
            },
        }
