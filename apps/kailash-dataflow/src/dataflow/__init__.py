"""
Kailash DataFlow - Clean Modular Architecture

This is the modernized DataFlow framework with proper modular structure.
The monolithic 526-line implementation has been refactored into focused modules:

- core/engine.py: Main DataFlow class
- core/models.py: Configuration and base models
- core/nodes.py: Dynamic node generation
- features/bulk.py: High-performance bulk operations
- features/transactions.py: Enterprise transaction management
- features/multi_tenant.py: Multi-tenant data isolation
- utils/connection.py: Connection pooling and management

This maintains 100% functional compatibility while providing:
- Better maintainability
- Improved testability
- Clear separation of concerns
- Easier contribution and extension
"""

from .core.config import DataFlowConfig
from .core.engine import DataFlow
from .core.models import DataFlowModel

# Legacy compatibility - maintain the original imports
__version__ = "1.0.0"
__all__ = ["DataFlow", "DataFlowConfig", "DataFlowModel"]

# Backward compatibility note:
# All existing code using `from dataflow import DataFlow` will continue to work.
# The internal architecture is now modular, but the public API remains unchanged.
