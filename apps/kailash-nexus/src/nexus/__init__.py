"""
Kailash Nexus - Multi-Channel Orchestration Platform

Built entirely on Kailash SDK components for enterprise workflow automation.
"""

from .core.application import NexusApplication, create_application
from .core.config import NexusConfig

__version__ = "1.0.0"
__all__ = ["NexusApplication", "create_application", "NexusConfig"]
