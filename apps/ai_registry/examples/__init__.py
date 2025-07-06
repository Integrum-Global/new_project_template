"""
Examples and demonstrations for AI Registry MCP Server.
"""

from .agent_conversations import (
    AIRegistryConversationExamples,
    demonstrate_custom_agent_setup,
    run_conversation_demos,
)
from .integration_patterns import RegistryIntegrationPatterns, run_integration_examples
from .quickstart import (
    demo_mcp_server_tools,
    quickstart_agent_conversation,
    quickstart_basic_search,
    run_all_quickstart_examples,
)

__all__ = [
    # Quickstart examples
    "run_all_quickstart_examples",
    "quickstart_basic_search",
    "quickstart_agent_conversation",
    "demo_mcp_server_tools",
    # Agent conversation examples
    "AIRegistryConversationExamples",
    "run_conversation_demos",
    "demonstrate_custom_agent_setup",
    # Integration pattern examples
    "RegistryIntegrationPatterns",
    "run_integration_examples",
]
