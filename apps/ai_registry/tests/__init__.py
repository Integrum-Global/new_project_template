"""
Test suite for AI Registry MCP Server.

This package contains comprehensive tests for all components of the
AI Registry MCP Server including server, nodes, workflows, and integration tests.

Test Structure:
- test_server.py: Core MCP server functionality
- test_nodes.py: Custom Kailash nodes
- test_workflows.py: Pre-built workflows
- Integration tests across all components

Run Tests:
    # Run all tests
    python -m pytest src/solutions/ai_registry/tests/

    # Run specific test file
    python -m pytest src/solutions/ai_registry/tests/test_server.py -v

    # Run with coverage
    python -m pytest src/solutions/ai_registry/tests/ --cov=src.solutions.ai_registry
"""

# Test utilities and fixtures can be imported here
# For example:
# from .conftest import sample_registry_data, mock_server

__all__ = [
    # Test modules are imported automatically by pytest
    # This can include common fixtures or utilities
]
