"""
Node Registry for AI Registry custom nodes.

This module registers custom nodes with the Kailash SDK's WorkflowBuilder
to enable string-based node creation.
"""

from kailash.workflow import WorkflowBuilder

# Import custom nodes
from .nodes import RegistryAnalyticsNode, RegistryCompareNode, RegistrySearchNode


def register_ai_registry_nodes():
    """Register AI Registry custom nodes with WorkflowBuilder."""

    # Register nodes with WorkflowBuilder's node registry
    node_mappings = {
        "RegistrySearchNode": RegistrySearchNode,
        "RegistryAnalyticsNode": RegistryAnalyticsNode,
        "RegistryCompareNode": RegistryCompareNode,
    }

    # Update WorkflowBuilder's node registry
    for node_name, node_class in node_mappings.items():
        WorkflowBuilder._node_registry[node_name] = node_class

    return node_mappings


# Auto-register on import
_registered_nodes = register_ai_registry_nodes()
