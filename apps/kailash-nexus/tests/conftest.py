"""
Nexus Application Test Configuration

Provides shared fixtures and configuration for Nexus application tests.
"""

import sys
from pathlib import Path

import pytest

# Add the Nexus app src directory to Python path
nexus_src = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(nexus_src))

# Add the main SDK to Python path for imports
sdk_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(sdk_root))

# Import test utilities from the main SDK
sys.path.insert(0, str(sdk_root / "tests" / "utils"))

# Mark configuration
pytest_plugins = []
