#!/usr/bin/env python3
"""
Advanced ETL Pipeline Example

This example demonstrates advanced features including:
- Multiple data transformations
- Custom processing logic
- Error handling
- Progress monitoring
"""

from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from kailash.workflow.graph import Workflow
from kailash.runtime.local import LocalRuntime
from kailash.nodes.data import CSVReaderNode, CSVWriterNode
from kailash.nodes.transform import DataTransformerNode
from kailash.nodes.code.python import PythonCodeNode


def create_advanced_etl_workflow():
    """Create an advanced ETL workflow with multiple transformations."""

    workflow = Workflow(
        workflow_id="advanced_etl_pipeline",
        name="Advanced ETL Pipeline with Custom Processing",
    )

    # 1. Extract data
    workflow.add_node(
        "extract",
        CSVReaderNode,
        file_path="examples/sample_data/sales.csv",
        delimiter=",",
        has_header=True,
    )

    # 2. Initial filtering and cleaning
    workflow.add_node(
        "clean",
        DataTransformerNode,
        operations=[
            # Remove invalid records
            {"type": "filter", "condition": "amount > 0"},
            {"type": "filter", "condition": "status != 'cancelled'"},
            # Standardize date format
            {"type": "transform", "column": "date", "format": "YYYY-MM-DD"},
        ],
    )

    # 3. Custom business logic
    workflow.add_node(
        "calculate",
        PythonCodeNode,
        code="""
def execute(data):
    import pandas as pd
    
    # Convert to DataFrame for easier processing
    df = pd.DataFrame(data['records'])
    
    # Calculate commission (10% for sales > 1000, 5% otherwise)
    df['commission'] = df['amount'].apply(
        lambda x: x * 0.10 if x > 1000 else x * 0.05
    )
    
    # Calculate tax (8% of amount)
    df['tax'] = df['amount'] * 0.08
    
    # Calculate net amount
    df['net_amount'] = df['amount'] - df['commission'] - df['tax']
    
    # Add performance category
    df['performance'] = pd.cut(
        df['amount'], 
        bins=[0, 500, 1000, 5000, float('inf')],
        labels=['Low', 'Medium', 'High', 'Premium']
    )
    
    return {"processed": df.to_dict('records')}
""",
    )

    # 4. Aggregate and summarize
    workflow.add_node(
        "aggregate",
        DataTransformerNode,
        operations=[
            # Sort by net amount
            {"type": "sort", "key": "net_amount", "reverse": True},
            # Group by performance category
            {"type": "aggregate", "group_by": "performance", "agg_func": "sum"},
        ],
    )

    # 5. Final formatting
    workflow.add_node(
        "format",
        PythonCodeNode,
        code="""
def execute(data):
    # Format numbers for output
    for record in data['aggregated']:
        record['total_amount'] = f"${record['amount']:,.2f}"
        record['total_commission'] = f"${record['commission']:,.2f}"
        record['total_tax'] = f"${record['tax']:,.2f}"
        record['total_net'] = f"${record['net_amount']:,.2f}"
    
    return {"formatted": data['aggregated']}
""",
    )

    # 6. Write results
    workflow.add_node(
        "save_detailed",
        CSVWriterNode,
        file_path="examples/sample_data/detailed_results.csv",
        write_header=True,
    )

    workflow.add_node(
        "save_summary",
        CSVWriterNode,
        file_path="examples/sample_data/summary_results.csv",
        write_header=True,
    )

    # Connect the workflow
    workflow.connect("extract", "clean", mapping={"data": "input"})
    workflow.connect("clean", "calculate", mapping={"cleaned": "data"})
    workflow.connect("calculate", "aggregate", mapping={"processed": "data"})
    workflow.connect("calculate", "save_detailed", mapping={"processed": "data"})
    workflow.connect("aggregate", "format", mapping={"aggregated": "data"})
    workflow.connect("format", "save_summary", mapping={"formatted": "data"})

    return workflow


def main():
    """Run the advanced ETL pipeline with error handling."""

    try:
        # Create sample data if it doesn't exist
        sample_dir = Path("examples/sample_data")
        sample_dir.mkdir(parents=True, exist_ok=True)

        # Create workflow
        workflow = create_advanced_etl_workflow()

        # Configure runtime with monitoring
        runtime = LocalRuntime(debug=True, max_retries=3, retry_delay=1000)  # 1 second

        print("Starting Advanced ETL Pipeline...")
        print("=" * 50)

        # Execute workflow
        results, run_id = runtime.execute(workflow)

        print("\n✅ Pipeline completed successfully!")
        print(f"Run ID: {run_id}")
        print("\nOutputs created:")
        print("- Detailed results: examples/sample_data/detailed_results.csv")
        print("- Summary results: examples/sample_data/summary_results.csv")

        # Display summary statistics
        if "save_summary" in results:
            print("\nSummary by Performance Category:")
            print("-" * 30)
            # Would print actual summary here

    except Exception as e:
        print(f"\n❌ Pipeline failed: {e}")
        print("\nTroubleshooting:")
        print("1. Ensure sample data exists in examples/sample_data/")
        print("2. Check that all required columns are present")
        print("3. Verify file permissions")
        raise


if __name__ == "__main__":
    main()
