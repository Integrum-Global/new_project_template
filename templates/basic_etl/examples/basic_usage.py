#!/usr/bin/env python3
"""
Basic ETL Pipeline Example

This example shows the simplest usage of the ETL pipeline template.
"""

from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from workflow import create_etl_workflow
from kailash.runtime.local import LocalRuntime


def main():
    """Run a basic ETL pipeline."""

    # Simple configuration
    config = {
        "input_file": "examples/sample_data/sales.csv",
        "output_file": "examples/sample_data/processed_sales.csv",
        "threshold": 500,  # Only process sales > $500
        "sort_column": "amount",
        "sort_descending": True,
    }

    # Create and execute workflow
    workflow = create_etl_workflow(config)
    runtime = LocalRuntime(debug=True)

    print("Starting Basic ETL Pipeline...")
    results, run_id = runtime.execute(workflow)

    print(f"✅ Pipeline completed!")
    print(f"Results saved to: {config['output_file']}")


if __name__ == "__main__":
    main()
