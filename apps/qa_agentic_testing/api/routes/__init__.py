"""
API routes for QA Agentic Testing System.
"""

# Import all route modules to make them available
from . import analytics, projects, reports, results, runs

__all__ = ["projects", "runs", "results", "analytics", "reports"]
