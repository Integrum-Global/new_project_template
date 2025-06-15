"""
REST API for QA Agentic Testing System.

FastAPI-based REST interface for managing test projects, runs, and results.
"""

from .main import app, create_app
from .routes import analytics, projects, reports, results, runs

__all__ = ["app", "create_app"]
