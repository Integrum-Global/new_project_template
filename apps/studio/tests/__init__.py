"""Test utilities for Studio Application."""
from pathlib import Path

def get_results_path(filename: str) -> Path:
    """Get path for test results in qa_results directory."""
    app_dir = Path(__file__).parent.parent
    results_dir = app_dir / "qa_results"
    results_dir.mkdir(exist_ok=True)
    return results_dir / filename