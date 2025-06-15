"""
Unit tests for Studio core models.
"""

from datetime import datetime, timezone
from unittest.mock import Mock

import pytest

from ...core.models import (
    ConnectionDefinition,
    ExecutionStatus,
    NodeDefinition,
    StudioWorkflow,
    TemplateCategory,
    WorkflowExecution,
    WorkflowMetadata,
    WorkflowStatus,
    WorkflowTemplate,
)


class TestNodeDefinition:
    """Test NodeDefinition model."""

    def test_create_node_definition(self):
        """Test creating a node definition."""
        node = NodeDefinition(
            node_id="test_node",
            node_type="CSVReaderNode",
            name="Test CSV Reader",
            config={"file_path": "/data/test.csv"},
            position={"x": 100, "y": 200},
        )

        assert node.node_id == "test_node"
        assert node.node_type == "CSVReaderNode"
        assert node.name == "Test CSV Reader"
        assert node.config["file_path"] == "/data/test.csv"
        assert node.position["x"] == 100

    def test_node_to_dict(self):
        """Test converting node to dictionary."""
        node = NodeDefinition(
            node_id="test_node", node_type="CSVReaderNode", name="Test CSV Reader"
        )

        result = node.to_dict()
        assert result["node_id"] == "test_node"
        assert result["node_type"] == "CSVReaderNode"
        assert result["name"] == "Test CSV Reader"

    def test_node_from_dict(self):
        """Test creating node from dictionary."""
        data = {
            "node_id": "test_node",
            "node_type": "CSVReaderNode",
            "name": "Test CSV Reader",
            "config": {"file_path": "/data/test.csv"},
        }

        node = NodeDefinition.from_dict(data)
        assert node.node_id == "test_node"
        assert node.config["file_path"] == "/data/test.csv"


class TestConnectionDefinition:
    """Test ConnectionDefinition model."""

    def test_create_connection(self):
        """Test creating a connection definition."""
        conn = ConnectionDefinition(
            connection_id="test_conn",
            from_node="node1",
            from_output="output",
            to_node="node2",
            to_input="input",
        )

        assert conn.connection_id == "test_conn"
        assert conn.from_node == "node1"
        assert conn.to_node == "node2"

    def test_connection_to_dict(self):
        """Test converting connection to dictionary."""
        conn = ConnectionDefinition(
            connection_id="test_conn",
            from_node="node1",
            from_output="output",
            to_node="node2",
            to_input="input",
        )

        result = conn.to_dict()
        assert result["connection_id"] == "test_conn"
        assert result["from_node"] == "node1"
        assert result["to_node"] == "node2"


class TestStudioWorkflow:
    """Test StudioWorkflow model."""

    def test_create_workflow(self):
        """Test creating a workflow."""
        workflow = StudioWorkflow(
            workflow_id="test_workflow",
            name="Test Workflow",
            description="A test workflow",
        )

        assert workflow.workflow_id == "test_workflow"
        assert workflow.name == "Test Workflow"
        assert workflow.status == WorkflowStatus.DRAFT
        assert len(workflow.nodes) == 0
        assert len(workflow.connections) == 0

    def test_add_node(self):
        """Test adding a node to workflow."""
        workflow = StudioWorkflow(workflow_id="test_workflow", name="Test Workflow")

        node_id = workflow.add_node(
            node_type="CSVReaderNode",
            name="CSV Reader",
            config={"file_path": "/data/test.csv"},
        )

        assert len(workflow.nodes) == 1
        assert workflow.nodes[0].node_id == node_id
        assert workflow.nodes[0].node_type == "CSVReaderNode"
        assert workflow.updated_at is not None

    def test_add_connection(self):
        """Test adding a connection to workflow."""
        workflow = StudioWorkflow(workflow_id="test_workflow", name="Test Workflow")

        # Add nodes first
        node1_id = workflow.add_node("CSVReaderNode", "Reader")
        node2_id = workflow.add_node("FilterNode", "Filter")

        # Add connection
        conn_id = workflow.add_connection(
            from_node=node1_id, from_output="output", to_node=node2_id, to_input="input"
        )

        assert len(workflow.connections) == 1
        assert workflow.connections[0].connection_id == conn_id
        assert workflow.connections[0].from_node == node1_id
        assert workflow.connections[0].to_node == node2_id

    def test_remove_node(self):
        """Test removing a node from workflow."""
        workflow = StudioWorkflow(workflow_id="test_workflow", name="Test Workflow")

        # Add nodes and connection
        node1_id = workflow.add_node("CSVReaderNode", "Reader")
        node2_id = workflow.add_node("FilterNode", "Filter")
        workflow.add_connection(node1_id, "output", node2_id, "input")

        # Remove node
        success = workflow.remove_node(node1_id)

        assert success
        assert len(workflow.nodes) == 1
        assert len(workflow.connections) == 0  # Connection should be removed too

    def test_workflow_to_dict(self):
        """Test converting workflow to dictionary."""
        workflow = StudioWorkflow(
            workflow_id="test_workflow",
            name="Test Workflow",
            description="Test description",
        )

        workflow.add_node("CSVReaderNode", "Reader")

        result = workflow.to_dict()
        assert result["workflow_id"] == "test_workflow"
        assert result["name"] == "Test Workflow"
        assert result["status"] == "draft"
        assert len(result["nodes"]) == 1

    def test_workflow_from_dict(self):
        """Test creating workflow from dictionary."""
        data = {
            "workflow_id": "test_workflow",
            "name": "Test Workflow",
            "description": "Test description",
            "status": "active",
            "nodes": [
                {
                    "node_id": "node1",
                    "node_type": "CSVReaderNode",
                    "name": "Reader",
                    "config": {},
                    "position": {"x": 0, "y": 0},
                }
            ],
            "connections": [],
            "metadata": {},
            "tenant_id": "default",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "version": 1,
        }

        workflow = StudioWorkflow.from_dict(data)
        assert workflow.workflow_id == "test_workflow"
        assert workflow.status == WorkflowStatus.ACTIVE
        assert len(workflow.nodes) == 1
        assert workflow.nodes[0].node_type == "CSVReaderNode"


class TestWorkflowExecution:
    """Test WorkflowExecution model."""

    def test_create_execution(self):
        """Test creating a workflow execution."""
        execution = WorkflowExecution(
            execution_id="test_exec", workflow_id="test_workflow"
        )

        assert execution.execution_id == "test_exec"
        assert execution.workflow_id == "test_workflow"
        assert execution.status == ExecutionStatus.PENDING
        assert execution.progress.progress_percentage == 0.0

    def test_start_execution(self):
        """Test starting an execution."""
        execution = WorkflowExecution(
            execution_id="test_exec", workflow_id="test_workflow"
        )

        execution.start("test_user")

        assert execution.status == ExecutionStatus.RUNNING
        assert execution.started_by == "test_user"
        assert execution.started_at is not None

    def test_complete_execution(self):
        """Test completing an execution."""
        execution = WorkflowExecution(
            execution_id="test_exec", workflow_id="test_workflow"
        )

        execution.start("test_user")
        execution.complete({"result": "success"})

        assert execution.status == ExecutionStatus.COMPLETED
        assert execution.outputs["result"] == "success"
        assert execution.completed_at is not None
        assert execution.runtime_seconds is not None

    def test_fail_execution(self):
        """Test failing an execution."""
        execution = WorkflowExecution(
            execution_id="test_exec", workflow_id="test_workflow"
        )

        execution.start("test_user")
        execution.fail("Test error message")

        assert execution.status == ExecutionStatus.FAILED
        assert execution.error_message == "Test error message"
        assert execution.completed_at is not None

    def test_add_log(self):
        """Test adding logs to execution."""
        execution = WorkflowExecution(
            execution_id="test_exec", workflow_id="test_workflow"
        )

        execution.add_log("Test log message")

        assert len(execution.logs) == 1
        assert "Test log message" in execution.logs[0]


class TestWorkflowTemplate:
    """Test WorkflowTemplate model."""

    def test_create_template(self):
        """Test creating a workflow template."""
        workflow = StudioWorkflow(
            workflow_id="template_workflow", name="Template Workflow"
        )

        template = WorkflowTemplate(
            template_id="test_template",
            name="Test Template",
            description="A test template",
            category=TemplateCategory.DATA_PROCESSING,
            workflow_definition=workflow,
        )

        assert template.template_id == "test_template"
        assert template.name == "Test Template"
        assert template.category == TemplateCategory.DATA_PROCESSING
        assert template.usage_count == 0

    def test_create_workflow_instance(self):
        """Test creating workflow instance from template."""
        # Create base workflow
        base_workflow = StudioWorkflow(
            workflow_id="template_workflow", name="Template Workflow"
        )
        base_workflow.add_node("CSVReaderNode", "Reader")

        # Create template
        template = WorkflowTemplate(
            template_id="test_template",
            name="Test Template",
            description="A test template",
            category=TemplateCategory.DATA_PROCESSING,
            workflow_definition=base_workflow,
        )

        # Create instance
        instance = template.create_workflow_instance(
            name="Instance Workflow", tenant_id="test_tenant", owner_id="test_owner"
        )

        assert instance.name == "Instance Workflow"
        assert instance.tenant_id == "test_tenant"
        assert instance.owner_id == "test_owner"
        assert len(instance.nodes) == 1
        assert instance.nodes[0].node_type == "CSVReaderNode"
        assert template.usage_count == 1


class TestWorkflowMetadata:
    """Test WorkflowMetadata model."""

    def test_create_metadata(self):
        """Test creating workflow metadata."""
        metadata = WorkflowMetadata(
            tags=["test", "demo"],
            category="data_processing",
            complexity="medium",
            estimated_runtime=300,
        )

        assert metadata.tags == ["test", "demo"]
        assert metadata.category == "data_processing"
        assert metadata.complexity == "medium"
        assert metadata.estimated_runtime == 300

    def test_metadata_to_dict(self):
        """Test converting metadata to dictionary."""
        metadata = WorkflowMetadata(tags=["test"], category="data_processing")

        result = metadata.to_dict()
        assert result["tags"] == ["test"]
        assert result["category"] == "data_processing"
        assert result["complexity"] == "medium"  # Default value

    def test_metadata_from_dict(self):
        """Test creating metadata from dictionary."""
        data = {
            "tags": ["test", "demo"],
            "category": "data_processing",
            "complexity": "complex",
            "estimated_runtime": 600,
        }

        metadata = WorkflowMetadata.from_dict(data)
        assert metadata.tags == ["test", "demo"]
        assert metadata.complexity == "complex"
        assert metadata.estimated_runtime == 600
