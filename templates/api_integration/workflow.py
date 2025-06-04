#!/usr/bin/env python3
"""
API Integration Solution Template

This template demonstrates how to integrate with external APIs,
handle authentication, process responses, and store results.

Requirements:
- Input: API configuration and parameters
- Processing: Call APIs, handle responses, transform data
- Output: Processed data stored in desired format

Created with Kailash SDK
"""

from pathlib import Path
from typing import Any, Dict
import json

# Kailash SDK imports
from kailash.workflow.graph import Workflow
from kailash.runtime.local import LocalRuntime

# Import required nodes
from kailash.nodes.api.http import HTTPRequestNode
from kailash.nodes.code.python import PythonCodeNode
from kailash.nodes.data import JSONWriterNode, CSVWriterNode


def create_api_workflow(config: Dict[str, Any] = None):
    """
    Create API integration workflow.

    Args:
        config: Configuration dictionary

    Returns:
        Configured Workflow instance
    """
    if config is None:
        config = {}

    workflow = Workflow(workflow_id="api_integration", name="API Integration Workflow")

    # 1. Make API request
    workflow.add_node(
        "api_call",
        HTTPRequestNode,
        url=config.get("api_url", "https://api.example.com/data"),
        method=config.get("method", "GET"),
        headers=config.get("headers", {}),
        params=config.get("params", {}),
        timeout=config.get("timeout", 30000),  # 30 seconds
        retry_count=config.get("retry_count", 3),
        retry_delay=config.get("retry_delay", 1000),  # 1 second
    )

    # 2. Process API response
    workflow.add_node(
        "process_response",
        PythonCodeNode,
        code="""
def execute(api_response):
    # Extract data from response
    if api_response.get('status_code') != 200:
        raise Exception(f"API returned {api_response.get('status_code')}: {api_response.get('error')}")
    
    data = api_response.get('body', {})
    
    # Transform data as needed
    processed_records = []
    for item in data.get('items', []):
        processed_records.append({
            'id': item.get('id'),
            'name': item.get('name'),
            'value': item.get('value', 0),
            'status': item.get('status', 'unknown'),
            'processed_at': datetime.now().isoformat()
        })
    
    return {
        "processed": processed_records,
        "metadata": {
            "total_records": len(processed_records),
            "api_version": data.get('version', 'unknown'),
            "timestamp": datetime.now().isoformat()
        }
    }
""",
    )

    # 3. Validate and enrich data
    workflow.add_node(
        "validate",
        PythonCodeNode,
        code="""
def execute(data):
    validated_records = []
    errors = []
    
    for record in data['processed']:
        # Validate required fields
        if not record.get('id'):
            errors.append(f"Missing ID for record: {record}")
            continue
            
        # Enrich with additional data
        record['category'] = categorize_value(record.get('value', 0))
        record['priority'] = calculate_priority(record)
        
        validated_records.append(record)
    
    return {
        "validated": validated_records,
        "validation_errors": errors,
        "metadata": data['metadata']
    }

def categorize_value(value):
    if value < 100:
        return 'low'
    elif value < 1000:
        return 'medium'
    else:
        return 'high'

def calculate_priority(record):
    if record['status'] == 'urgent':
        return 1
    elif record['category'] == 'high':
        return 2
    else:
        return 3
""",
    )

    # 4. Store results
    workflow.add_node(
        "save_json",
        JSONWriterNode,
        file_path=config.get("output_json", "data/api_results.json"),
        pretty_print=True,
    )

    workflow.add_node(
        "save_csv",
        CSVWriterNode,
        file_path=config.get("output_csv", "data/api_results.csv"),
        write_header=True,
    )

    # Connect workflow
    workflow.connect(
        "api_call", "process_response", mapping={"response": "api_response"}
    )
    workflow.connect("process_response", "validate", mapping={"processed": "data"})
    workflow.connect("validate", "save_json", mapping={"validated": "data"})
    workflow.connect("validate", "save_csv", mapping={"validated": "data"})

    return workflow


def main():
    """Main execution function."""
    try:
        # Configuration
        config = {
            "api_url": "https://jsonplaceholder.typicode.com/users",
            "method": "GET",
            "headers": {"Accept": "application/json", "User-Agent": "Kailash-SDK/1.0"},
            "output_json": "data/users.json",
            "output_csv": "data/users.csv",
        }

        # Add auth token if available
        import os

        if api_token := os.getenv("API_TOKEN"):
            config["headers"]["Authorization"] = f"Bearer {api_token}"

        # Create and execute workflow
        workflow = create_api_workflow(config)
        runtime = LocalRuntime(debug=True)

        print("Starting API Integration...")
        results, run_id = runtime.execute(workflow)

        print(f"✅ API integration completed!")
        print(f"Run ID: {run_id}")
        print(f"Results saved to:")
        print(f"  - JSON: {config['output_json']}")
        print(f"  - CSV: {config['output_csv']}")

        return True

    except Exception as e:
        print(f"❌ API integration failed: {e}")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
