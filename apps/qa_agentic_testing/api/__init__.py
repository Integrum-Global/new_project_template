"""
REST API for QA Agentic Testing System.

FastAPI-based REST interface for managing test projects, runs, and results.
"""

from .main import app, create_app
from .routes import projects, runs, results, analytics, reports

__all__ = ["app", "create_app"]