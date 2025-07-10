"""
Unit tests for Workflow Registry.
"""

from datetime import datetime, timezone
from unittest.mock import Mock, patch

import pytest
from nexus.core.registry import WorkflowMetadata, WorkflowRegistry

from kailash.nodes.data.python_code import PythonCodeNode
from kailash.workflow import Workflow
from kailash.workflow.builder import WorkflowBuilder


class TestWorkflowRegistry:
    """Test WorkflowRegistry class."""

    @pytest.fixture
    def registry(self):
        """Create a workflow registry instance."""
        return WorkflowRegistry()

    @pytest.fixture
    def sample_workflow(self):
        """Create a sample workflow."""

        def process_func():
            """Sample processing function."""
            return "test"

        builder = WorkflowBuilder()
        builder.add_node(
            "PythonCodeNode", "process", PythonCodeNode.from_function(process_func)
        )
        return builder.build()

    def test_initialization(self, registry):
        """Test registry initialization."""
        assert len(registry._workflows) > 0  # Should have system workflows
        assert len(registry._metadata) > 0
        assert "system/workflow-validator" in registry._workflows
        assert "system/workflow-search" in registry._workflows

    def test_register_workflow(self, registry, sample_workflow):
        """Test registering a workflow."""
        metadata = registry.register(
            workflow_id="test/workflow1", workflow=sample_workflow
        )

        assert metadata.workflow_id == "test/workflow1"
        assert metadata.name == "test/workflow1"
        assert metadata.version == "1.0.0"
        assert metadata.author == "unknown"

        # Check workflow is stored
        assert "test/workflow1" in registry._workflows
        assert registry._workflows["test/workflow1"] == sample_workflow

    def test_register_with_metadata(self, registry, sample_workflow):
        """Test registering with custom metadata."""
        custom_metadata = WorkflowMetadata(
            workflow_id="test/workflow2",
            name="Test Workflow",
            description="A test workflow",
            version="2.0.0",
            author="test_user",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            tags=["test", "example"],
            category="testing",
            is_public=True,
        )

        metadata = registry.register(
            workflow_id="test/workflow2",
            workflow=sample_workflow,
            metadata=custom_metadata,
        )

        assert metadata.name == "Test Workflow"
        assert metadata.description == "A test workflow"
        assert metadata.version == "2.0.0"
        assert metadata.author == "test_user"
        assert metadata.tags == ["test", "example"]
        assert metadata.category == "testing"
        assert metadata.is_public is True

    def test_register_duplicate_workflow(self, registry, sample_workflow):
        """Test registering duplicate workflow ID."""
        registry.register("test/duplicate", sample_workflow)

        # Should raise error for duplicate
        with pytest.raises(ValueError, match="already registered"):
            registry.register("test/duplicate", sample_workflow)

    def test_get_workflow(self, registry, sample_workflow):
        """Test getting a workflow by ID."""
        registry.register("test/get", sample_workflow)

        # Get workflow
        workflow = registry.get("test/get")
        assert workflow == sample_workflow

        # Get non-existent
        workflow = registry.get("test/nonexistent")
        assert workflow is None

    def test_get_metadata(self, registry, sample_workflow):
        """Test getting workflow metadata."""
        registry.register("test/metadata", sample_workflow)

        metadata = registry.get_metadata("test/metadata")
        assert metadata is not None
        assert metadata.workflow_id == "test/metadata"

        # Non-existent
        metadata = registry.get_metadata("test/nonexistent")
        assert metadata is None

    def test_list_workflows(self, registry, sample_workflow):
        """Test listing workflows with filters."""
        # Register multiple workflows
        for i in range(3):
            metadata = WorkflowMetadata(
                workflow_id=f"test/list{i}",
                name=f"List Test {i}",
                description="Test workflow",
                version="1.0.0",
                author="test_user",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                tags=["test"] if i % 2 == 0 else ["example"],
                category="testing" if i < 2 else "production",
                is_public=i % 2 == 0,
                tenant_id="tenant1" if i == 0 else None,
            )
            registry.register(f"test/list{i}", sample_workflow, metadata)

        # List all
        all_workflows = registry.list()
        assert len(all_workflows) >= 3

        # Filter by category
        testing_workflows = registry.list(category="testing")
        assert len([w for w in testing_workflows if w.category == "testing"]) >= 2

        # Filter by tags
        test_tagged = registry.list(tags=["test"])
        assert all(
            "test" in w.tags for w in test_tagged if w.workflow_id.startswith("test/")
        )

        # Filter by public status
        public_workflows = registry.list(is_public=True)
        assert all(
            w.is_public for w in public_workflows if w.workflow_id.startswith("test/")
        )

        # Filter by tenant
        tenant_workflows = registry.list(tenant_id="tenant1")
        assert len([w for w in tenant_workflows if w.tenant_id == "tenant1"]) == 1

    def test_search_workflows(self, registry, sample_workflow):
        """Test searching workflows."""
        # Register searchable workflows
        metadata1 = WorkflowMetadata(
            workflow_id="search/data-processor",
            name="Data Processor",
            description="Process data efficiently",
            version="1.0.0",
            author="test_user",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            tags=["data", "processing"],
        )
        registry.register("search/data-processor", sample_workflow, metadata1)

        metadata2 = WorkflowMetadata(
            workflow_id="search/api-caller",
            name="API Caller",
            description="Call external APIs",
            version="1.0.0",
            author="test_user",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            tags=["api", "integration"],
        )
        registry.register("search/api-caller", sample_workflow, metadata2)

        # Search by name
        results, total = registry.search("data")
        assert total >= 1
        assert any(r.workflow_id == "search/data-processor" for r in results)

        # Search by description
        results, total = registry.search("api")
        assert total >= 1
        assert any(r.workflow_id == "search/api-caller" for r in results)

        # Search by tag
        results, total = registry.search("processing")
        assert total >= 1
        assert any("processing" in r.tags for r in results)

        # Search with limit
        results, total = registry.search("", limit=1)
        assert len(results) == 1
        assert total >= 2

    def test_update_metadata(self, registry, sample_workflow):
        """Test updating workflow metadata."""
        registry.register("test/update", sample_workflow)

        # Update metadata
        updated = registry.update_metadata(
            "test/update",
            {
                "description": "Updated description",
                "tags": ["updated", "test"],
                "category": "updated",
                "is_public": True,
            },
        )

        assert updated.description == "Updated description"
        assert updated.tags == ["updated", "test"]
        assert updated.category == "updated"
        assert updated.is_public is True

        # Try to update non-existent
        with pytest.raises(ValueError):
            registry.update_metadata("test/nonexistent", {})

    def test_delete_workflow(self, registry, sample_workflow):
        """Test deleting a workflow."""
        registry.register("test/delete", sample_workflow)

        # Delete workflow
        result = registry.delete("test/delete")
        assert result is True

        # Check it's gone
        assert registry.get("test/delete") is None
        assert registry.get_metadata("test/delete") is None

        # Delete non-existent
        result = registry.delete("test/nonexistent")
        assert result is False

    def test_delete_system_workflow(self, registry):
        """Test that system workflows cannot be deleted."""
        with pytest.raises(ValueError, match="Cannot delete system workflows"):
            registry.delete("system/workflow-validator")

    def test_workflow_versioning(self, registry, sample_workflow):
        """Test workflow version tracking."""
        # Register initial version
        metadata = WorkflowMetadata(
            workflow_id="test/versioned",
            name="Versioned Workflow",
            description="Test versioning",
            version="1.0.0",
            author="test_user",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        registry.register("test/versioned", sample_workflow, metadata)

        # Check version tracking
        assert "test/versioned" in registry._versions
        versions = registry._versions["test/versioned"]
        assert len(versions) == 1
        assert versions[0][0] == "1.0.0"

    def test_get_dependencies(self, registry, sample_workflow):
        """Test getting workflow dependencies."""
        metadata = WorkflowMetadata(
            workflow_id="test/with-deps",
            name="Workflow with Dependencies",
            description="Has dependencies",
            version="1.0.0",
            author="test_user",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            dependencies=["test/dep1", "test/dep2"],
        )
        registry.register("test/with-deps", sample_workflow, metadata)

        deps = registry.get_dependencies("test/with-deps")
        assert deps == ["test/dep1", "test/dep2"]

        # No dependencies
        deps = registry.get_dependencies("test/nonexistent")
        assert deps == []

    def test_export_import_metadata(self, registry, sample_workflow):
        """Test exporting and importing metadata."""
        # Register some workflows
        for i in range(2):
            metadata = WorkflowMetadata(
                workflow_id=f"test/export{i}",
                name=f"Export Test {i}",
                description="Test export",
                version="1.0.0",
                author="test_user",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            registry.register(f"test/export{i}", sample_workflow, metadata)

        # Export metadata
        exported = registry.export_metadata()
        assert "test/export0" in exported
        assert "test/export1" in exported

        # Create new registry and import
        new_registry = WorkflowRegistry()
        new_registry.import_metadata({"test/imported": exported["test/export0"]})

        # Check imported
        metadata = new_registry.get_metadata("test/imported")
        assert metadata is not None
        assert metadata.name == "Export Test 0"
