"""
Main FastAPI application for QA Agentic Testing System.
"""

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from ..core.database import setup_database
from .routes import analytics, projects, reports, results, runs


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Initialize database on startup."""
        await setup_database()
        yield

    app = FastAPI(
        title="QA Agentic Testing API",
        description="AI-powered autonomous testing framework for any application",
        version="0.1.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        lifespan=lifespan,
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API routes
    app.include_router(projects.router, prefix="/api/projects", tags=["Projects"])
    app.include_router(runs.router, prefix="/api/runs", tags=["Test Runs"])
    app.include_router(results.router, prefix="/api/results", tags=["Test Results"])
    app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
    app.include_router(reports.router, prefix="/api/reports", tags=["Reports"])

    # Serve static files if frontend exists
    frontend_path = Path(__file__).parent.parent / "frontend" / "dist"
    if frontend_path.exists():
        app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")

    @app.get("/", response_class=HTMLResponse)
    async def root():
        """Serve the frontend or API documentation."""
        frontend_index = (
            Path(__file__).parent.parent / "frontend" / "dist" / "index.html"
        )

        if frontend_index.exists():
            return HTMLResponse(content=frontend_index.read_text())
        else:
            return HTMLResponse(
                content="""
            <html>
                <head>
                    <title>QA Agentic Testing</title>
                    <style>
                        body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
                        .container { background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                        h1 { color: #2c3e50; margin-bottom: 20px; }
                        .links { margin: 20px 0; }
                        .links a { display: inline-block; margin: 10px 20px 10px 0; padding: 10px 20px; background: #3498db; color: white; text-decoration: none; border-radius: 5px; }
                        .links a:hover { background: #2980b9; }
                        .feature { margin: 10px 0; padding: 10px; background: #ecf0f1; border-left: 4px solid #3498db; }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1>🤖 QA Agentic Testing Framework</h1>
                        <p>AI-powered autonomous testing framework that can test any application with minimal configuration.</p>

                        <div class="links">
                            <a href="/api/docs">📚 API Documentation</a>
                            <a href="/api/redoc">📖 API Reference</a>
                        </div>

                        <h2>✨ Key Features</h2>
                        <div class="feature">🔍 <strong>Auto-Discovery</strong> - Automatically discovers REST APIs, CLI commands, web interfaces</div>
                        <div class="feature">🎭 <strong>Intelligent Personas</strong> - Creates personas based on app's user roles and permissions</div>
                        <div class="feature">🧠 <strong>Advanced Agents</strong> - A2A communication, self-organizing pools, iterative reasoning</div>
                        <div class="feature">📊 <strong>Comprehensive Reports</strong> - Interactive HTML dashboards with AI insights</div>
                        <div class="feature">⚡ <strong>Enterprise Ready</strong> - CI/CD integration, regression detection, performance monitoring</div>

                        <h2>🚀 Quick Start</h2>
                        <pre style="background: #2c3e50; color: #ecf0f1; padding: 15px; border-radius: 5px; overflow-x: auto;">
# Install and run
pip install -e .
qa-test /path/to/your/app

# Or use the API
curl -X POST "http://localhost:8000/api/projects" \\
     -H "Content-Type: application/json" \\
     -d '{"name": "My App", "app_path": "/path/to/app", "description": "Test my application"}'
                        </pre>

                        <p style="margin-top: 30px; color: #7f8c8d;">
                            Built with the Kailash SDK - Empowering developers with AI-powered testing capabilities
                        </p>
                    </div>
                </body>
            </html>
            """
            )

    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "service": "qa-agentic-testing"}

    return app


# Create the application instance
app = create_app()
