"""
MCP Application - Model Context Protocol Management System

A comprehensive, production-ready application for managing MCP servers,
tools, and integrations built with the Kailash SDK.
"""

from .core.gateway import MCPGateway
from .core.models import MCPResource, MCPServer, MCPTool
from .main import create_mcp_app

__version__ = "1.0.0"

__all__ = [
    "MCPGateway",
    "MCPServer",
    "MCPTool",
    "MCPResource",
    "create_mcp_app",
]
