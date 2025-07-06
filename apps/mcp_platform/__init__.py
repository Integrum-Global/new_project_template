"""
MCP Platform - Unified Model Context Protocol Infrastructure

This package provides a comprehensive platform for MCP management including:
- Core server management and orchestration
- Enterprise gateway with multi-tenancy
- Tool servers and implementations
- Integration examples and patterns
"""

__version__ = "1.0.0"

# Core exports
from apps.mcp_platform.core.core.gateway import MCPGateway
from apps.mcp_platform.core.core.registry import MCPRegistry
from apps.mcp_platform.core.core.services import MCPService
from apps.mcp_platform.gateway.gateway.auth.authentication import AuthenticationMiddleware

# Gateway exports
from apps.mcp_platform.gateway.gateway.core.server import EnterpriseGateway

# Tools exports
from apps.mcp_platform.tools.servers.basic_server import BasicMCPServer
from apps.mcp_platform.tools.servers.production_server import ProductionMCPServer

# from apps.mcp_platform.gateway.gateway.auth.authorization import AuthorizationManager


__all__ = [
    "MCPGateway",
    "MCPRegistry",
    "MCPService",
    "EnterpriseGateway",
    "AuthenticationMiddleware",
    # "AuthorizationManager",
    "BasicMCPServer",
    "ProductionMCPServer",
]
