"""
Kailash Nexus - Enterprise Application Framework

Built on Kailash SDK's NexusGateway with additional enterprise features.
"""

from nexus.core.application import NexusApplication, create_application
from nexus.core.config import NexusConfig
from nexus.core.registry import WorkflowMetadata, WorkflowRegistry
from nexus.core.session import EnhancedSessionManager
from nexus.enterprise.auth import APIKey, AuthToken, EnterpriseAuthManager
from nexus.enterprise.multi_tenant import MultiTenantManager, Tenant
from nexus.marketplace.registry import MarketplaceItem, MarketplaceRegistry

__version__ = "1.0.0"

__all__ = [
    # Core
    "NexusApplication",
    "create_application",
    "NexusConfig",
    "EnhancedSessionManager",
    "WorkflowRegistry",
    "WorkflowMetadata",
    # Enterprise
    "MultiTenantManager",
    "Tenant",
    "EnterpriseAuthManager",
    "AuthToken",
    "APIKey",
    # Marketplace
    "MarketplaceRegistry",
    "MarketplaceItem",
]
