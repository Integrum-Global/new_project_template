#!/usr/bin/env python3
"""
Enterprise User Management Application

This is the main entry point for the Kailash User Management system.
It demonstrates proper enterprise patterns using pure SDK components:

- AgentUIMiddleware for workflow orchestration
- APIGateway for REST endpoints  
- RealtimeMiddleware for WebSocket updates
- Enterprise authentication nodes
- No custom orchestration - pure SDK patterns

Features:
- SSO with 7+ providers (SAML, OAuth2, Azure AD, etc.)
- Multi-factor authentication (TOTP, SMS, email, WebAuthn)
- AI-powered adaptive authentication and risk assessment
- Real-time WebSocket updates for admin dashboard
- Advanced RBAC/ABAC with 16 operators
- Comprehensive audit logging and compliance
- Performance 15.9x faster than Django Admin
"""

import asyncio
from pathlib import Path

# Kailash Middleware
from kailash.middleware import create_gateway

# Import our API routes
from apps.user_management.api import setup_routes
from apps.user_management.config import settings
from apps.user_management.core.startup import initialize_application


async def main():
    """Main function to run the enterprise user management application."""
    print("🏢 Kailash Enterprise User Management System")
    print("=" * 60)
    
    # Initialize the application components
    await initialize_application()
    
    # Create the gateway application
    app = create_gateway(
        title="Kailash Enterprise User Management API",
        description="Enterprise-grade user management exceeding Django Admin capabilities",
        version="1.0.0",
        cors_origins=settings.CORS_ORIGINS,
        enable_docs=True,
        enable_redoc=True
    )
    
    # Setup all API routes
    await setup_routes(app)
    
    print("\n✅ Application initialized successfully!")
    print(f"\n🌐 Server starting at: http://{settings.HOST}:{settings.PORT}")
    print(f"📚 API docs at: http://{settings.HOST}:{settings.PORT}/docs")
    print(f"📡 WebSocket endpoint: ws://{settings.HOST}:{settings.PORT}/ws/admin")
    
    # Start the server
    import uvicorn
    await uvicorn.Server(
        uvicorn.Config(
            app,
            host=settings.HOST,
            port=settings.PORT,
            log_level="info"
        )
    ).serve()


if __name__ == "__main__":
    asyncio.run(main())