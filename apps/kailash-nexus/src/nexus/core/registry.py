"""
Workflow Registry for Nexus Application

Manages workflow registration, versioning, and discovery using Kailash SDK.
"""

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from kailash.nodes.data.async_sql import AsyncSQLDatabaseNode
from kailash.nodes.validation.validation_nodes import WorkflowValidationNode
from kailash.workflow import Workflow
from kailash.workflow.builder import WorkflowBuilder

logger = logging.getLogger(__name__)


@dataclass
class WorkflowMetadata:
    """Metadata for a registered workflow."""

    workflow_id: str
    name: str
    description: str
    version: str
    author: str
    created_at: datetime
    updated_at: datetime
    tags: List[str] = field(default_factory=list)
    category: Optional[str] = None
    is_public: bool = False
    tenant_id: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    parameters_schema: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "workflow_id": self.workflow_id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "author": self.author,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "tags": self.tags,
            "category": self.category,
            "is_public": self.is_public,
            "tenant_id": self.tenant_id,
            "dependencies": self.dependencies,
            "parameters_schema": self.parameters_schema,
        }


class WorkflowRegistry:
    """Registry for managing workflows with versioning and discovery.

    Built entirely on Kailash SDK components.
    """

    def __init__(self):
        """Initialize workflow registry."""
        self._workflows: Dict[str, Workflow] = {}
        self._metadata: Dict[str, WorkflowMetadata] = {}
        self._versions: Dict[str, List[Tuple[str, WorkflowMetadata]]] = (
            {}
        )  # workflow_id -> [(version, metadata)]

        # Create management workflows
        self._init_management_workflows()

        logger.info("Workflow registry initialized")

    def _init_management_workflows(self):
        """Initialize built-in management workflows using SDK nodes."""
        # Workflow validation workflow
        validation_workflow = WorkflowBuilder()
        validation_workflow.add_node(
            "WorkflowValidationNode",
            "validator",
            {"strict_mode": True, "check_cycles": True, "validate_parameters": True},
        )
        validation_workflow.add_node(
            "PythonCodeNode",
            "format_results",
            {
                "code": """
# Format validation results
if validation_result.get('valid', False):
    result = {
        'status': 'valid',
        'message': 'Workflow validation passed',
        'details': validation_result
    }
else:
    result = {
        'status': 'invalid',
        'message': 'Workflow validation failed',
        'errors': validation_result.get('errors', []),
        'warnings': validation_result.get('warnings', [])
    }
"""
            },
        )
        validation_workflow.add_connection(
            "validator", "result", "format_results", "validation_result"
        )

        # Register as system workflow
        self._register_system_workflow(
            "system/workflow-validator", validation_workflow.build()
        )

        # Workflow search workflow
        search_workflow = WorkflowBuilder()
        search_workflow.add_node(
            "PythonCodeNode",
            "search_registry",
            {
                "code": """
# Search workflows by criteria
import re
from typing import List, Dict, Any

def search_workflows(
    query: str = "",
    tags: List[str] = None,
    category: str = None,
    author: str = None,
    is_public: bool = None
) -> List[Dict[str, Any]]:
    results = []

    # This would normally query the registry
    # For now, return a placeholder
    result = {
        'workflows': results,
        'total': len(results),
        'query': query
    }
"""
            },
        )

        self._register_system_workflow(
            "system/workflow-search", search_workflow.build()
        )

    def _register_system_workflow(self, workflow_id: str, workflow: Workflow):
        """Register a system workflow."""
        metadata = WorkflowMetadata(
            workflow_id=workflow_id,
            name=workflow_id.split("/")[-1],
            description=f"System workflow: {workflow_id}",
            version="1.0.0",
            author="system",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            tags=["system"],
            category="system",
            is_public=False,
        )

        self._workflows[workflow_id] = workflow
        self._metadata[workflow_id] = metadata

    def register(
        self,
        workflow_id: str,
        workflow: Workflow,
        metadata: Optional[WorkflowMetadata] = None,
        validate: bool = True,
    ) -> WorkflowMetadata:
        """Register a workflow in the registry.

        Args:
            workflow_id: Unique identifier for the workflow
            workflow: The workflow instance
            metadata: Optional metadata, auto-generated if not provided
            validate: Whether to validate the workflow

        Returns:
            WorkflowMetadata instance

        Raises:
            ValueError: If workflow is invalid or ID already exists
        """
        # Check if ID already exists
        if workflow_id in self._workflows and not self._is_new_version(
            workflow_id, workflow
        ):
            raise ValueError(f"Workflow {workflow_id} already registered")

        # Validate workflow if requested
        if validate:
            validation_result = self._validate_workflow(workflow)
            if not validation_result.get("valid", False):
                raise ValueError(
                    f"Workflow validation failed: {validation_result.get('errors')}"
                )

        # Create metadata if not provided
        if metadata is None:
            metadata = WorkflowMetadata(
                workflow_id=workflow_id,
                name=workflow_id,
                description="",
                version="1.0.0",
                author="unknown",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )

        # Store workflow and metadata
        self._workflows[workflow_id] = workflow
        self._metadata[workflow_id] = metadata

        # Track version
        self._track_version(workflow_id, metadata.version, metadata)

        logger.info(f"Registered workflow: {workflow_id} (v{metadata.version})")
        return metadata

    def _validate_workflow(self, workflow: Workflow) -> Dict[str, Any]:
        """Validate a workflow using WorkflowValidationNode.

        For now, returns a simple validation result.
        In production, this would use the actual validation node.
        """
        # TODO: Use actual WorkflowValidationNode once available
        return {"valid": True, "errors": [], "warnings": []}

    def _is_new_version(self, workflow_id: str, workflow: Workflow) -> bool:
        """Check if this is a new version of an existing workflow."""
        if workflow_id not in self._workflows:
            return False

        # Compare workflow content (simplified)
        # In production, this would do a proper comparison
        existing = self._workflows[workflow_id]
        return str(existing) != str(workflow)

    def _track_version(
        self, workflow_id: str, version: str, metadata: WorkflowMetadata
    ):
        """Track workflow version."""
        if workflow_id not in self._versions:
            self._versions[workflow_id] = []

        self._versions[workflow_id].append((version, metadata))
        self._versions[workflow_id].sort(key=lambda x: x[0], reverse=True)

    def get(
        self, workflow_id: str, version: Optional[str] = None
    ) -> Optional[Workflow]:
        """Get a workflow by ID and optional version.

        Args:
            workflow_id: Workflow identifier
            version: Optional version, latest if not specified

        Returns:
            Workflow instance or None if not found
        """
        if version:
            # Get specific version
            for ver, metadata in self._versions.get(workflow_id, []):
                if ver == version:
                    # In production, would retrieve the actual workflow for this version
                    return self._workflows.get(workflow_id)
            return None

        # Get latest version
        return self._workflows.get(workflow_id)

    def get_metadata(self, workflow_id: str) -> Optional[WorkflowMetadata]:
        """Get workflow metadata.

        Args:
            workflow_id: Workflow identifier

        Returns:
            WorkflowMetadata or None if not found
        """
        return self._metadata.get(workflow_id)

    def list(
        self,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        is_public: Optional[bool] = None,
        tenant_id: Optional[str] = None,
    ) -> List[WorkflowMetadata]:
        """List workflows with optional filtering.

        Args:
            category: Filter by category
            tags: Filter by tags (any match)
            is_public: Filter by public status
            tenant_id: Filter by tenant

        Returns:
            List of workflow metadata
        """
        results = []

        for workflow_id, metadata in self._metadata.items():
            # Apply filters
            if category and metadata.category != category:
                continue

            if tags and not any(tag in metadata.tags for tag in tags):
                continue

            if is_public is not None and metadata.is_public != is_public:
                continue

            if tenant_id is not None and metadata.tenant_id != tenant_id:
                continue

            results.append(metadata)

        # Sort by updated time, newest first
        results.sort(key=lambda m: m.updated_at, reverse=True)
        return results

    def search(
        self, query: str, limit: int = 20, offset: int = 0
    ) -> Tuple[List[WorkflowMetadata], int]:
        """Search workflows by query.

        Args:
            query: Search query
            limit: Maximum results
            offset: Results offset

        Returns:
            Tuple of (results, total_count)
        """
        # Simple search implementation
        # In production, this would use full-text search
        query_lower = query.lower()
        matches = []

        for metadata in self._metadata.values():
            if (
                query_lower in metadata.name.lower()
                or query_lower in metadata.description.lower()
                or any(query_lower in tag.lower() for tag in metadata.tags)
            ):
                matches.append(metadata)

        total = len(matches)
        results = matches[offset : offset + limit]

        return results, total

    def update_metadata(
        self, workflow_id: str, updates: Dict[str, Any]
    ) -> WorkflowMetadata:
        """Update workflow metadata.

        Args:
            workflow_id: Workflow identifier
            updates: Fields to update

        Returns:
            Updated metadata

        Raises:
            ValueError: If workflow not found
        """
        if workflow_id not in self._metadata:
            raise ValueError(f"Workflow {workflow_id} not found")

        metadata = self._metadata[workflow_id]

        # Update allowed fields
        allowed_fields = ["description", "tags", "category", "is_public"]
        for field_name, value in updates.items():
            if field_name in allowed_fields:
                setattr(metadata, field_name, value)

        metadata.updated_at = datetime.now(timezone.utc)

        logger.info(f"Updated metadata for workflow: {workflow_id}")
        return metadata

    def delete(self, workflow_id: str) -> bool:
        """Delete a workflow from the registry.

        Args:
            workflow_id: Workflow identifier

        Returns:
            True if deleted, False if not found
        """
        if workflow_id not in self._workflows:
            return False

        # Don't allow deletion of system workflows
        metadata = self._metadata.get(workflow_id)
        if metadata and metadata.category == "system":
            raise ValueError("Cannot delete system workflows")

        # Remove from all stores
        del self._workflows[workflow_id]
        del self._metadata[workflow_id]
        self._versions.pop(workflow_id, None)

        logger.info(f"Deleted workflow: {workflow_id}")
        return True

    def get_dependencies(self, workflow_id: str) -> List[str]:
        """Get workflow dependencies.

        Args:
            workflow_id: Workflow identifier

        Returns:
            List of dependency workflow IDs
        """
        metadata = self._metadata.get(workflow_id)
        if not metadata:
            return []

        return metadata.dependencies

    def export_metadata(self) -> Dict[str, Any]:
        """Export all metadata for backup/migration.

        Returns:
            Dictionary of all metadata
        """
        return {
            workflow_id: metadata.to_dict()
            for workflow_id, metadata in self._metadata.items()
        }

    def import_metadata(self, data: Dict[str, Any]):
        """Import metadata from backup/migration.

        Args:
            data: Metadata dictionary
        """
        for workflow_id, metadata_dict in data.items():
            # Convert datetime strings back to datetime objects
            metadata_dict["created_at"] = datetime.fromisoformat(
                metadata_dict["created_at"]
            )
            metadata_dict["updated_at"] = datetime.fromisoformat(
                metadata_dict["updated_at"]
            )

            # Create metadata instance
            metadata = WorkflowMetadata(**metadata_dict)
            self._metadata[workflow_id] = metadata

            # Track version
            self._track_version(workflow_id, metadata.version, metadata)

        logger.info(f"Imported metadata for {len(data)} workflows")
