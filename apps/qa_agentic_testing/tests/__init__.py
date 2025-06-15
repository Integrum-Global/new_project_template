"""
QA Agentic Testing Test Suite

This package contains all test files organized by type:
- unit/: Unit tests for individual components
- integration/: Integration tests for component interactions
- functional/: Functional tests for complete features
- performance/: Performance and load tests
"""

# Test result paths
import os
from pathlib import Path

# Ensure qa_results directory exists for qa_agentic_testing's own test results
# Note: When testing other apps, results are stored in the target app's qa_results folder
QA_RESULTS_DIR = Path(__file__).parent.parent / "qa_results"
QA_RESULTS_DIR.mkdir(exist_ok=True)


# Common test utilities
def get_results_path(filename: str) -> Path:
    """Get path for test results file."""
    return QA_RESULTS_DIR / filename
