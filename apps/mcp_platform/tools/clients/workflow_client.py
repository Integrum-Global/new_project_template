#!/usr/bin/env python3
"""Workflow MCP Client - Complex workflows using MCP tools."""

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List

from kailash.core import LocalRuntime, WorkflowBuilder
from kailash.nodes import PythonCodeNode

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class MCPWorkflowClient:
    """Client for building complex workflows with MCP tools."""

    def __init__(self, mcp_server: str = "mcp://localhost:8080"):
        self.runtime = LocalRuntime()
        self.mcp_server = mcp_server

    def create_data_pipeline_workflow(self) -> Any:
        """Create a data processing pipeline using MCP tools."""
        builder = WorkflowBuilder("data-pipeline")

        # Step 1: Generate sample data
        builder.add_node(
            "data_generator",
            "PythonCodeNode",
            config={
                "code": """
import random
import json

def process(params):
    # Generate sample sales data
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
    products = ["Widget A", "Widget B", "Widget C"]

    data = []
    for month in months:
        for product in products:
            data.append({
                "month": month,
                "product": product,
                "sales": random.randint(1000, 10000),
                "units": random.randint(50, 500)
            })

    return {
        "raw_data": data,
        "count": len(data)
    }
"""
            },
        )

        # Step 2: Call MCP tool to process data
        builder.add_node(
            "mcp_processor",
            "PythonCodeNode",
            config={
                "code": f"""
from kailash.mcp_server import MCPClient
import asyncio

async def process_with_mcp(data):
    client = MCPClient("pipeline-client")

    try:
        await client.connect("{self.mcp_server}")

        # Aggregate by month
        monthly_result = await client.call_tool("aggregate", {{
            "data": data["raw_data"],
            "group_by": "month",
            "aggregate_field": "sales",
            "operation": "sum"
        }})

        # Aggregate by product
        product_result = await client.call_tool("aggregate", {{
            "data": data["raw_data"],
            "group_by": "product",
            "aggregate_field": "sales",
            "operation": "sum"
        }})

        # Calculate statistics
        all_sales = [item["sales"] for item in data["raw_data"]]
        stats_result = await client.call_tool("statistics_calc", {{
            "numbers": all_sales,
            "operations": ["mean", "median", "min", "max", "stdev"]
        }})

        return {{
            "monthly_sales": monthly_result["aggregated"],
            "product_sales": product_result["aggregated"],
            "statistics": stats_result["results"]
        }}

    finally:
        await client.disconnect()

def process(data):
    # Run async function in sync context
    return asyncio.run(process_with_mcp(data))
"""
            },
        )

        # Step 3: Generate report
        builder.add_node(
            "report_generator",
            "PythonCodeNode",
            config={
                "code": """
def process(data):
    report = []
    report.append("=== Sales Analysis Report ===\\n")

    # Monthly sales
    report.append("Monthly Sales Summary:")
    for month, total in data["monthly_sales"].items():
        report.append(f"  {month}: ${total:,.2f}")

    report.append("\\nProduct Sales Summary:")
    for product, total in data["product_sales"].items():
        report.append(f"  {product}: ${total:,.2f}")

    # Statistics
    report.append("\\nStatistical Analysis:")
    stats = data["statistics"]
    report.append(f"  Average Sales: ${stats['mean']:,.2f}")
    report.append(f"  Median Sales: ${stats['median']:,.2f}")
    report.append(f"  Min Sales: ${stats['min']:,.2f}")
    report.append(f"  Max Sales: ${stats['max']:,.2f}")
    if 'stdev' in stats:
        report.append(f"  Std Deviation: ${stats['stdev']:,.2f}")

    return {
        "report": "\\n".join(report),
        "summary": {
            "total_months": len(data["monthly_sales"]),
            "total_products": len(data["product_sales"]),
            "avg_sales": stats['mean']
        }
    }
"""
            },
        )

        # Connect nodes
        builder.add_connection("data_generator", "raw_data", "mcp_processor", "data")
        builder.add_connection("mcp_processor", "output", "report_generator", "data")

        return builder.build()

    def create_file_processing_workflow(self) -> Any:
        """Create a file processing workflow using MCP tools."""
        builder = WorkflowBuilder("file-processor")

        # Step 1: List files
        builder.add_node(
            "file_lister",
            "PythonCodeNode",
            config={
                "code": f"""
from kailash.mcp_server import MCPClient
import asyncio

async def list_files_mcp(params):
    client = MCPClient("file-client")

    try:
        await client.connect("{self.mcp_server}")

        # List directory
        result = await client.call_tool("list_directory", {{
            "path": params.get("directory", "."),
            "pattern": params.get("pattern", "*.txt")
        }})

        return result

    finally:
        await client.disconnect()

def process(params):
    return asyncio.run(list_files_mcp(params))
"""
            },
        )

        # Step 2: Process each file
        builder.add_node(
            "file_processor",
            "PythonCodeNode",
            config={
                "code": f"""
from kailash.mcp_server import MCPClient
import asyncio

async def process_files_mcp(data):
    client = MCPClient("file-processor-client")
    results = []

    try:
        await client.connect("{self.mcp_server}")

        for file_info in data.get("files", []):
            if file_info["type"] == "file":
                # Read file
                try:
                    content_result = await client.call_tool("read_file", {{
                        "path": file_info["name"]
                    }})

                    # Hash content
                    hash_result = await client.call_tool("hash_data", {{
                        "data": content_result["content"],
                        "algorithm": "sha256"
                    }})

                    results.append({{
                        "file": file_info["name"],
                        "size": file_info["size"],
                        "lines": content_result.get("lines", 0),
                        "hash": hash_result["hash"]
                    }})
                except Exception as e:
                    results.append({{
                        "file": file_info["name"],
                        "error": str(e)
                    }})

        return {{"processed_files": results}}

    finally:
        await client.disconnect()

def process(data):
    return asyncio.run(process_files_mcp(data))
"""
            },
        )

        # Step 3: Generate summary
        builder.add_node(
            "summary_generator",
            "PythonCodeNode",
            config={
                "code": """
def process(data):
    files = data.get("processed_files", [])

    summary = {
        "total_files": len(files),
        "successful": len([f for f in files if "error" not in f]),
        "failed": len([f for f in files if "error" in f]),
        "total_size": sum(f.get("size", 0) for f in files if "error" not in f),
        "total_lines": sum(f.get("lines", 0) for f in files if "error" not in f)
    }

    report = []
    report.append("=== File Processing Summary ===")
    report.append(f"Total files: {summary['total_files']}")
    report.append(f"Successful: {summary['successful']}")
    report.append(f"Failed: {summary['failed']}")
    report.append(f"Total size: {summary['total_size']} bytes")
    report.append(f"Total lines: {summary['total_lines']}")

    report.append("\\nFile Details:")
    for file in files:
        if "error" in file:
            report.append(f"  {file['file']}: ERROR - {file['error']}")
        else:
            report.append(f"  {file['file']}: {file['size']} bytes, {file['lines']} lines, SHA256: {file['hash'][:16]}...")

    return {
        "summary": summary,
        "report": "\\n".join(report),
        "file_details": files
    }
"""
            },
        )

        # Connect nodes
        builder.add_connection("file_lister", "output", "file_processor", "data")
        builder.add_connection(
            "file_processor", "processed_files", "summary_generator", "data"
        )

        return builder.build()

    def create_math_analysis_workflow(self) -> Any:
        """Create a mathematical analysis workflow."""
        builder = WorkflowBuilder("math-analysis")

        # Step 1: Generate number sequence
        builder.add_node(
            "sequence_generator",
            "PythonCodeNode",
            config={
                "code": f"""
from kailash.mcp_server import MCPClient
import asyncio

async def generate_sequences(params):
    client = MCPClient("math-client")

    try:
        await client.connect("{self.mcp_server}")

        # Get Fibonacci sequence
        fib_result = await client.call_tool("fibonacci", {{
            "n": params.get("fibonacci_count", 20)
        }})

        # Calculate factorials
        factorials = []
        for i in range(1, params.get("factorial_count", 10) + 1):
            fact_result = await client.call_tool("factorial", {{"n": i}})
            factorials.append({{
                "n": i,
                "factorial": fact_result["result"]
            }})

        return {{
            "fibonacci": fib_result["sequence"],
            "factorials": factorials
        }}

    finally:
        await client.disconnect()

def process(params):
    return asyncio.run(generate_sequences(params))
"""
            },
        )

        # Step 2: Analyze sequences
        builder.add_node(
            "sequence_analyzer",
            "PythonCodeNode",
            config={
                "code": f"""
from kailash.mcp_server import MCPClient
import asyncio

async def analyze_sequences(data):
    client = MCPClient("analyzer-client")

    try:
        await client.connect("{self.mcp_server}")

        # Analyze Fibonacci sequence
        fib_stats = await client.call_tool("statistics_calc", {{
            "numbers": data["fibonacci"],
            "operations": ["mean", "median", "min", "max"]
        }})

        # Analyze factorial growth
        factorial_values = [f["factorial"] for f in data["factorials"]]
        fact_stats = await client.call_tool("statistics_calc", {{
            "numbers": factorial_values[:10],  # Limit to prevent overflow
            "operations": ["mean", "min", "max"]
        }})

        # Calculate ratios for Fibonacci (golden ratio approximation)
        ratios = []
        fib = data["fibonacci"]
        for i in range(2, len(fib)):
            if fib[i-1] != 0:
                ratio = fib[i] / fib[i-1]
                ratios.append(ratio)

        ratio_stats = await client.call_tool("statistics_calc", {{
            "numbers": ratios[-10:],  # Last 10 ratios
            "operations": ["mean", "stdev"]
        }})

        return {{
            "fibonacci_stats": fib_stats["results"],
            "factorial_stats": fact_stats["results"],
            "golden_ratio_approximation": ratio_stats["results"].get("mean", 0),
            "ratio_stability": ratio_stats["results"].get("stdev", 0)
        }}

    finally:
        await client.disconnect()

def process(data):
    return asyncio.run(analyze_sequences(data))
"""
            },
        )

        # Step 3: Generate analysis report
        builder.add_node(
            "analysis_reporter",
            "PythonCodeNode",
            config={
                "code": """
def process(data):
    report = []
    report.append("=== Mathematical Sequence Analysis ===\\n")

    # Fibonacci analysis
    report.append("Fibonacci Sequence Analysis:")
    fib_stats = data["fibonacci_stats"]
    report.append(f"  Mean: {fib_stats['mean']:.2f}")
    report.append(f"  Median: {fib_stats['median']:.2f}")
    report.append(f"  Range: {fib_stats['min']} to {fib_stats['max']}")
    report.append(f"  Golden Ratio Approximation: {data['golden_ratio_approximation']:.6f}")
    report.append(f"  Ratio Stability (StdDev): {data['ratio_stability']:.6f}")

    # Factorial analysis
    report.append("\\nFactorial Sequence Analysis:")
    fact_stats = data["factorial_stats"]
    report.append(f"  Mean: {fact_stats['mean']:,.0f}")
    report.append(f"  Min: {fact_stats['min']}")
    report.append(f"  Max: {fact_stats['max']:,}")

    # Insights
    report.append("\\nInsights:")
    report.append(f"  - The Fibonacci ratio converges to φ ≈ 1.618034")
    report.append(f"  - Actual convergence: {data['golden_ratio_approximation']:.6f}")
    report.append(f"  - Factorial growth is super-exponential")

    return {
        "report": "\\n".join(report),
        "analysis_data": data
    }
"""
            },
        )

        # Connect nodes
        builder.add_connection(
            "sequence_generator", "output", "sequence_analyzer", "data"
        )
        builder.add_connection(
            "sequence_analyzer", "output", "analysis_reporter", "data"
        )

        return builder.build()

    async def run_workflow(
        self, workflow_name: str, params: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Run a specific workflow."""
        if params is None:
            params = {}

        workflows = {
            "data_pipeline": self.create_data_pipeline_workflow,
            "file_processor": self.create_file_processing_workflow,
            "math_analysis": self.create_math_analysis_workflow,
        }

        if workflow_name not in workflows:
            raise ValueError(f"Unknown workflow: {workflow_name}")

        workflow = workflows[workflow_name]()

        try:
            result = await self.runtime.execute_workflow(workflow, params)
            return result
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            raise


async def demo_workflows(client: MCPWorkflowClient):
    """Run demonstration of all workflows."""

    # Demo 1: Data Pipeline
    logger.info("\n=== Data Pipeline Workflow Demo ===")
    try:
        result = await client.run_workflow("data_pipeline")
        final_node = list(result.keys())[-1]
        logger.info(f"\n{result[final_node]['report']}")
    except Exception as e:
        logger.error(f"Data pipeline failed: {e}")

    # Demo 2: File Processor (create test files first)
    logger.info("\n=== File Processor Workflow Demo ===")

    # Create test files
    test_dir = Path("test_files")
    test_dir.mkdir(exist_ok=True)

    for i in range(3):
        file_path = test_dir / f"test_{i}.txt"
        file_path.write_text(f"This is test file {i}\nWith some content\nLine 3")

    try:
        result = await client.run_workflow(
            "file_processor", {"directory": str(test_dir), "pattern": "*.txt"}
        )
        final_node = list(result.keys())[-1]
        logger.info(f"\n{result[final_node]['report']}")
    except Exception as e:
        logger.error(f"File processor failed: {e}")
    finally:
        # Cleanup
        import shutil

        shutil.rmtree(test_dir, ignore_errors=True)

    # Demo 3: Math Analysis
    logger.info("\n=== Math Analysis Workflow Demo ===")
    try:
        result = await client.run_workflow(
            "math_analysis", {"fibonacci_count": 25, "factorial_count": 12}
        )
        final_node = list(result.keys())[-1]
        logger.info(f"\n{result[final_node]['report']}")
    except Exception as e:
        logger.error(f"Math analysis failed: {e}")


async def interactive_workflow_mode(client: MCPWorkflowClient):
    """Interactive mode for running workflows."""
    logger.info("\n=== Interactive Workflow Mode ===")
    logger.info("Available workflows: data_pipeline, file_processor, math_analysis")
    logger.info("Type 'quit' to exit")

    while True:
        try:
            command = input("\nWorkflow> ").strip()

            if command == "quit":
                break

            if command == "help":
                print("Commands:")
                print("  list          - List available workflows")
                print("  run <name>    - Run a workflow")
                print("  quit          - Exit")
                continue

            if command == "list":
                print("Available workflows:")
                print("  data_pipeline  - Generate and analyze sales data")
                print("  file_processor - Process files in a directory")
                print("  math_analysis  - Analyze mathematical sequences")
                continue

            if command.startswith("run "):
                workflow_name = command[4:].strip()

                # Get parameters based on workflow
                params = {}
                if workflow_name == "file_processor":
                    directory = input("Directory path (default: '.'): ").strip() or "."
                    pattern = (
                        input("File pattern (default: '*.txt'): ").strip() or "*.txt"
                    )
                    params = {"directory": directory, "pattern": pattern}
                elif workflow_name == "math_analysis":
                    fib_count = input("Fibonacci count (default: 20): ").strip()
                    fact_count = input("Factorial count (default: 10): ").strip()
                    params = {
                        "fibonacci_count": int(fib_count) if fib_count else 20,
                        "factorial_count": int(fact_count) if fact_count else 10,
                    }

                # Run workflow
                logger.info(f"Running {workflow_name} workflow...")
                try:
                    result = await client.run_workflow(workflow_name, params)
                    final_node = list(result.keys())[-1]

                    if "report" in result[final_node]:
                        print(f"\n{result[final_node]['report']}")
                    else:
                        print(f"\nResult: {result[final_node]}")
                except Exception as e:
                    logger.error(f"Workflow failed: {e}")

        except KeyboardInterrupt:
            break
        except Exception as e:
            logger.error(f"Error: {e}")


async def main():
    """Run the workflow client demo."""
    import sys

    # Get MCP server from command line or use default
    mcp_server = sys.argv[1] if len(sys.argv) > 1 else "mcp://localhost:8080"

    client = MCPWorkflowClient(mcp_server=mcp_server)

    try:
        # Run demos
        await demo_workflows(client)

        # Interactive mode
        await interactive_workflow_mode(client)

    except Exception as e:
        logger.error(f"Workflow client error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
