#!/usr/bin/env python3
"""
Basic ETL Pipeline Solution

This template demonstrates a simple Extract-Transform-Load workflow
for processing CSV data with filtering, transformation, and aggregation.

Requirements:
- Input: CSV file with data to process
- Processing: Filter, transform, and aggregate data
- Output: Processed CSV file with results

Created with Kailash SDK
"""

from pathlib import Path
from typing import Any, Dict

# Kailash SDK imports
from kailash.workflow.graph import Workflow
from kailash.runtime.local import LocalRuntime

# Import required nodes - check reference/api-registry.yaml for exact APIs
from kailash.nodes.data import CSVReaderNode, CSVWriterNode
from kailash.nodes.transform import DataTransformer


def create_etl_workflow(config: Dict[str, Any] = None):
    """
    Create and configure the ETL workflow.
    
    Args:
        config: Optional configuration dictionary
        
    Returns:
        Configured Workflow instance
    """
    if config is None:
        config = {}
    
    # Create workflow with unique ID
    workflow = Workflow(
        workflow_id="basic_etl_pipeline",
        name="Basic ETL Data Processing Pipeline"
    )
    
    # 1. Extract: Read input data
    workflow.add_node(
        "extract",
        CSVReaderNode,
        file_path=config.get("input_file", "data/input.csv"),
        delimiter=config.get("delimiter", ","),
        has_header=config.get("has_header", True)
    )
    
    # 2. Transform: Process the data
    workflow.add_node(
        "transform",
        DataTransformer,
        operations=[
            # Filter rows where value > threshold
            {
                "type": "filter",
                "condition": f"value > {config.get('threshold', 0)}"
            },
            # Sort by specified column
            {
                "type": "sort",
                "key": config.get("sort_column", "value"),
                "reverse": config.get("sort_descending", False)
            },
            # Add calculated column
            {
                "type": "calculate",
                "column": "processed_value",
                "formula": "value * 1.1"  # Example: 10% increase
            }
        ]
    )
    
    # 3. Load: Write results
    workflow.add_node(
        "load",
        CSVWriterNode,
        file_path=config.get("output_file", "data/output.csv"),
        write_header=True,
        delimiter=config.get("delimiter", ",")
    )
    
    # Connect the workflow nodes
    workflow.connect("extract", "transform", mapping={"data": "input"})
    workflow.connect("transform", "load", mapping={"transformed": "data"})
    
    return workflow


def main():
    """Main execution function."""
    try:
        # Load configuration (in real usage, load from config.yaml)
        config = {
            "input_file": "data/sales_data.csv",
            "output_file": "data/processed_sales.csv",
            "threshold": 1000,
            "sort_column": "amount",
            "sort_descending": True
        }
        
        # Create and execute workflow
        workflow = create_etl_workflow(config)
        
        # Execute with debug logging
        runtime = LocalRuntime(debug=True)
        results, run_id = runtime.execute(workflow)
        
        print(f"✅ ETL pipeline completed successfully!")
        print(f"Run ID: {run_id}")
        print(f"Output saved to: {config['output_file']}")
        
        return True
        
    except Exception as e:
        print(f"❌ ETL pipeline failed: {e}")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)