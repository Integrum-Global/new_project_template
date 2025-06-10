"""
pytest configuration for template repository tests.
"""

from pathlib import Path

import pytest


@pytest.fixture
def repo_root():
    """Fixture providing the repository root path."""
    return Path(__file__).parent.parent.parent


@pytest.fixture
def workflows_dir(repo_root):
    """Fixture providing the GitHub workflows directory path."""
    return repo_root / ".github" / "workflows"


@pytest.fixture
def reference_dir(repo_root):
    """Fixture providing the reference documentation directory path."""
    return repo_root / "reference"
