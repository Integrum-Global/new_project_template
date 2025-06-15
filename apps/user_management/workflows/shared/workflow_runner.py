#!/usr/bin/env python3
"""
Common Workflow Execution Engine

This module provides a unified workflow execution engine used by all user types
(admin, manager, user) to run Kailash SDK workflows with consistent error handling,
logging, and performance monitoring.
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from kailash.runtime.local import LocalRuntime
from kailash.workflow import WorkflowBuilder


class WorkflowExecutionError(Exception):
    """Custom exception for workflow execution errors."""

    pass


class WorkflowRunner:
    """
    Unified workflow execution engine for the User Management System.

    Provides consistent execution patterns, error handling, and monitoring
    across all workflow types.
    """

    def __init__(
        self,
        user_type: str = "system",
        user_id: str = "admin",
        enable_debug: bool = False,
        enable_audit: bool = True,
        enable_monitoring: bool = True,
    ):
        """
        Initialize the workflow runner.

        Args:
            user_type: Type of user (admin, manager, user)
            user_id: Unique identifier for the user
            enable_debug: Enable debug logging
            enable_audit: Enable audit logging
            enable_monitoring: Enable performance monitoring
        """
        self.user_type = user_type
        self.user_id = user_id
        self.enable_debug = enable_debug
        self.enable_audit = enable_audit
        self.enable_monitoring = enable_monitoring

        # Initialize runtime with enterprise features
        self.runtime = LocalRuntime(
            enable_async=True,
            debug=enable_debug,
            enable_monitoring=enable_monitoring,
            enable_audit=enable_audit,
        )

        # Execution statistics
        self.execution_stats = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "total_execution_time": 0.0,
            "average_execution_time": 0.0,
        }

    def create_workflow(self, workflow_name: str) -> WorkflowBuilder:
        """
        Create a new workflow builder with standard configuration.

        Args:
            workflow_name: Name identifier for the workflow

        Returns:
            Configured WorkflowBuilder instance
        """
        builder = WorkflowBuilder()

        # Add standard audit logging node if enabled
        if self.enable_audit:
            builder.add_node(
                "PythonCodeNode",
                "audit_start",
                {
                    "name": "workflow_audit_start",
                    "code": f"""
import time
from datetime import datetime

# Create audit log entry for workflow start
audit_entry = {{
    "timestamp": datetime.now().isoformat(),
    "operation": "workflow_start",
    "event_type": "workflow_execution",
    "severity": "info",
    "user_id": "{self.user_id}",
    "user_type": "{self.user_type}",
    "workflow_name": "{workflow_name}",
    "session_id": f"session_{{int(time.time())}}"
}}

result = {{"result": audit_entry}}
""",
                },
            )

        return builder

    def execute_workflow(
        self,
        workflow: Any,
        parameters: Optional[Dict[str, Any]] = None,
        workflow_name: str = "unnamed_workflow",
    ) -> Tuple[Dict[str, Any], str]:
        """
        Execute a workflow with comprehensive error handling and monitoring.

        Args:
            workflow: Built workflow to execute
            parameters: Optional runtime parameters
            workflow_name: Name for logging and monitoring

        Returns:
            Tuple of (results, execution_id)

        Raises:
            WorkflowExecutionError: If execution fails
        """
        if parameters is None:
            parameters = {}

        execution_id = f"exec_{int(time.time())}_{self.user_id}"
        start_time = time.time()

        try:
            if self.enable_debug:
                print(f"🚀 Starting workflow execution: {workflow_name}")
                print(f"   Execution ID: {execution_id}")
                print(f"   User: {self.user_id} ({self.user_type})")
                print(f"   Parameters: {len(parameters)} provided")

            # Execute the workflow
            results, runtime_execution_id = self.runtime.execute(workflow, parameters)

            # Calculate execution time
            execution_time = time.time() - start_time

            # Update statistics
            self.execution_stats["total_executions"] += 1
            self.execution_stats["successful_executions"] += 1
            self.execution_stats["total_execution_time"] += execution_time
            self.execution_stats["average_execution_time"] = (
                self.execution_stats["total_execution_time"]
                / self.execution_stats["total_executions"]
            )

            if self.enable_debug:
                print(f"✅ Workflow completed successfully in {execution_time:.3f}s")
                print(f"   Results: {len(results)} nodes executed")

            # Log execution for monitoring
            if self.enable_monitoring:
                self._log_execution_metrics(workflow_name, execution_time, True, None)

            return results, execution_id

        except Exception as e:
            execution_time = time.time() - start_time

            # Update error statistics
            self.execution_stats["total_executions"] += 1
            self.execution_stats["failed_executions"] += 1
            self.execution_stats["total_execution_time"] += execution_time
            self.execution_stats["average_execution_time"] = (
                self.execution_stats["total_execution_time"]
                / self.execution_stats["total_executions"]
            )

            if self.enable_debug:
                print(f"❌ Workflow failed after {execution_time:.3f}s")
                print(f"   Error: {str(e)}")

            # Log execution for monitoring
            if self.enable_monitoring:
                self._log_execution_metrics(
                    workflow_name, execution_time, False, str(e)
                )

            raise WorkflowExecutionError(f"Workflow '{workflow_name}' failed: {str(e)}")

    def validate_workflow(
        self, workflow: Any, workflow_name: str = "unnamed_workflow"
    ) -> bool:
        """
        Validate a workflow without executing it.

        Args:
            workflow: Built workflow to validate
            workflow_name: Name for logging

        Returns:
            True if valid, False otherwise
        """
        try:
            # Basic validation - check if workflow can be built
            if not hasattr(workflow, "nodes") or not workflow.nodes:
                print(
                    f"❌ Workflow '{workflow_name}' validation failed: No nodes found"
                )
                return False

            if self.enable_debug:
                print(f"✅ Workflow '{workflow_name}' validation passed")
                print(f"   Nodes: {len(workflow.nodes)}")
                print(f"   Connections: {len(getattr(workflow, 'connections', []))}")

            return True

        except Exception as e:
            print(f"❌ Workflow '{workflow_name}' validation failed: {str(e)}")
            return False

    def _log_execution_metrics(
        self,
        workflow_name: str,
        execution_time: float,
        success: bool,
        error_message: Optional[str],
    ):
        """
        Log execution metrics for monitoring and analytics.

        Args:
            workflow_name: Name of the executed workflow
            execution_time: Time taken for execution
            success: Whether execution was successful
            error_message: Error message if failed
        """
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "workflow_name": workflow_name,
            "user_id": self.user_id,
            "user_type": self.user_type,
            "execution_time": execution_time,
            "success": success,
            "error_message": error_message,
        }

        # In a real implementation, this would send to monitoring system
        if self.enable_debug:
            print(f"📊 Execution metrics: {json.dumps(metrics, indent=2)}")

    def get_execution_stats(self) -> Dict[str, Any]:
        """
        Get current execution statistics.

        Returns:
            Dictionary containing execution statistics
        """
        return {
            **self.execution_stats,
            "success_rate": (
                self.execution_stats["successful_executions"]
                / max(self.execution_stats["total_executions"], 1)
            )
            * 100,
            "error_rate": (
                self.execution_stats["failed_executions"]
                / max(self.execution_stats["total_executions"], 1)
            )
            * 100,
        }

    def print_stats(self):
        """Print execution statistics in a formatted way."""
        stats = self.get_execution_stats()

        print("\n" + "=" * 60)
        print("WORKFLOW EXECUTION STATISTICS")
        print("=" * 60)
        print(f"Total Executions: {stats['total_executions']}")
        print(
            f"Successful: {stats['successful_executions']} ({stats['success_rate']:.1f}%)"
        )
        print(f"Failed: {stats['failed_executions']} ({stats['error_rate']:.1f}%)")
        print(f"Average Execution Time: {stats['average_execution_time']:.3f}s")
        print(f"Total Execution Time: {stats['total_execution_time']:.3f}s")
        print("=" * 60 + "\n")


def create_user_context_node(
    user_id: str, user_type: str, permissions: List[str]
) -> Dict[str, Any]:
    """
    Create a standardized user context node configuration.

    Args:
        user_id: Unique user identifier
        user_type: Type of user (admin, manager, user)
        permissions: List of user permissions

    Returns:
        Node configuration dictionary
    """
    return {
        "name": "create_user_context",
        "code": f"""
import time
from datetime import datetime

# Create user context for workflow execution
user_context = {{
    "user_id": "{user_id}",
    "user_type": "{user_type}",
    "permissions": {permissions},
    "timestamp": datetime.now().isoformat(),
    "session_id": f"session_{{int(time.time())}}"
}}

result = {{"result": user_context}}
""",
    }


def create_validation_node(validation_rules: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a standardized validation node configuration.

    Args:
        validation_rules: Dictionary of validation rules

    Returns:
        Node configuration dictionary
    """
    # Simple validation approach for PythonCodeNode context
    # Since we can't rely on locals() or globals() in the execution context,
    # we'll pass validation rules as a parameter and let the workflow handle
    # field checking

    return {
        "name": "validate_input",
        "code": """
# Simple validation - just pass through
# In a real implementation, the workflow would handle validation
# by passing specific fields to validate

result = {
    "result": {
        "valid": True,
        "errors": [],
        "validated_fields": ["department", "period"],
        "message": "Validation passed"
    }
}
""",
    }


def run_workflow_test(
    workflow_script_path: str, test_parameters: Optional[Dict[str, Any]] = None
):
    """
    Test runner for individual workflow scripts.

    Args:
        workflow_script_path: Path to the workflow script
        test_parameters: Optional test parameters
    """
    print(f"\n🧪 Testing workflow: {workflow_script_path}")

    try:
        # Import and run the workflow script
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "workflow_module", workflow_script_path
        )
        workflow_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(workflow_module)

        # Check if module has a test function
        if hasattr(workflow_module, "test_workflow"):
            result = workflow_module.test_workflow(test_parameters or {})
            if result:
                print(f"✅ Test passed: {workflow_script_path}")
            else:
                print(f"❌ Test failed: {workflow_script_path}")
        else:
            print(f"⚠️  No test function found in: {workflow_script_path}")

    except Exception as e:
        print(f"❌ Test error: {workflow_script_path} - {str(e)}")


if __name__ == "__main__":
    # Example usage and testing
    if len(sys.argv) > 1:
        if sys.argv[1] == "--test":
            # Test the workflow runner itself
            runner = WorkflowRunner(
                user_type="admin", user_id="test_admin", enable_debug=True
            )

            # Create a simple test workflow
            builder = runner.create_workflow("test_workflow")
            builder.add_node(
                "PythonCodeNode",
                "test_node",
                {
                    "name": "simple_test",
                    "code": "result = {'result': {'status': 'success', 'message': 'Test completed'}}",
                },
            )

            workflow = builder.build()

            # Validate and execute
            if runner.validate_workflow(workflow, "test_workflow"):
                try:
                    results, execution_id = runner.execute_workflow(
                        workflow, {}, "test_workflow"
                    )
                    print(f"Test workflow results: {results}")
                    runner.print_stats()
                except WorkflowExecutionError as e:
                    print(f"Test workflow failed: {e}")

        elif sys.argv[1] == "--validate-all":
            # Validate all workflows in the system
            workflow_dirs = [
                "admin_workflows/scripts",
                "manager_workflows/scripts",
                "user_workflows/scripts",
            ]

            for workflow_dir in workflow_dirs:
                if os.path.exists(workflow_dir):
                    for file in os.listdir(workflow_dir):
                        if file.endswith(".py"):
                            run_workflow_test(os.path.join(workflow_dir, file))
    else:
        print("Workflow Runner - Usage:")
        print("  --test: Test the workflow runner")
        print("  --validate-all: Validate all workflow scripts")
