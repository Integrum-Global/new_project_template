"""
DataFlow Node Generation

Dynamic node generation for database operations.
"""

from typing import Any, Dict, Type, Union

from kailash.nodes.base import Node, NodeParameter, NodeRegistry


class NodeGenerator:
    """Generates workflow nodes for DataFlow models."""

    def __init__(self, dataflow_instance):
        self.dataflow_instance = dataflow_instance

    def generate_crud_nodes(self, model_name: str, fields: Dict[str, Any]):
        """Generate CRUD workflow nodes for a model."""
        nodes = {
            f"{model_name}CreateNode": self._create_node_class(
                model_name, "create", fields
            ),
            f"{model_name}ReadNode": self._create_node_class(
                model_name, "read", fields
            ),
            f"{model_name}UpdateNode": self._create_node_class(
                model_name, "update", fields
            ),
            f"{model_name}DeleteNode": self._create_node_class(
                model_name, "delete", fields
            ),
            f"{model_name}ListNode": self._create_node_class(
                model_name, "list", fields
            ),
        }

        # Register nodes with Kailash's NodeRegistry system
        for node_name, node_class in nodes.items():
            NodeRegistry.register(node_class, alias=node_name)
            # Also register in module namespace for direct imports
            globals()[node_name] = node_class
            # Store in DataFlow instance for testing
            self.dataflow_instance._nodes[node_name] = node_class

    def generate_bulk_nodes(self, model_name: str, fields: Dict[str, Any]):
        """Generate bulk operation nodes for a model."""
        nodes = {
            f"{model_name}BulkCreateNode": self._create_node_class(
                model_name, "bulk_create", fields
            ),
            f"{model_name}BulkUpdateNode": self._create_node_class(
                model_name, "bulk_update", fields
            ),
            f"{model_name}BulkDeleteNode": self._create_node_class(
                model_name, "bulk_delete", fields
            ),
            f"{model_name}BulkUpsertNode": self._create_node_class(
                model_name, "bulk_upsert", fields
            ),
        }

        # Register nodes with Kailash's NodeRegistry system
        for node_name, node_class in nodes.items():
            NodeRegistry.register(node_class, alias=node_name)
            globals()[node_name] = node_class
            # Store in DataFlow instance for testing
            self.dataflow_instance._nodes[node_name] = node_class

    def _create_node_class(
        self, model_name: str, operation: str, fields: Dict[str, Any]
    ) -> Type[Node]:
        """Create a workflow node class for a model operation."""

        # Store parent DataFlow instance in closure
        dataflow_instance = self.dataflow_instance

        class DataFlowNode(Node):
            """Auto-generated DataFlow node."""

            def __init__(self, **kwargs):
                super().__init__(**kwargs)
                self.model_name = model_name
                self.operation = operation
                self.dataflow_instance = dataflow_instance
                self.model_fields = fields

            def get_parameters(self) -> Dict[str, NodeParameter]:
                """Define parameters for this DataFlow node."""
                if operation == "create":
                    # Generate parameters from model fields
                    params = {}
                    for field_name, field_info in fields.items():
                        if field_name not in ["id", "created_at", "updated_at"]:
                            params[field_name] = NodeParameter(
                                name=field_name,
                                type=field_info["type"],
                                required=field_info.get("required", True),
                                default=field_info.get("default"),
                                description=f"{field_name} for the record",
                            )
                    return params

                elif operation == "read":
                    return {
                        "id": NodeParameter(
                            name="id",
                            type=int,
                            required=False,
                            default=1,
                            description="ID of record to read",
                        )
                    }

                elif operation == "update":
                    params = {
                        "id": NodeParameter(
                            name="id",
                            type=int,
                            required=False,
                            default=1,
                            description="ID of record to update",
                        )
                    }
                    # Add all model fields as optional update parameters
                    for field_name, field_info in fields.items():
                        if field_name not in ["id", "created_at", "updated_at"]:
                            params[field_name] = NodeParameter(
                                name=field_name,
                                type=field_info["type"],
                                required=False,
                                description=f"New {field_name} for the record",
                            )
                    return params

                elif operation == "delete":
                    return {
                        "id": NodeParameter(
                            name="id",
                            type=int,
                            required=False,
                            default=1,
                            description="ID of record to delete",
                        )
                    }

                elif operation == "list":
                    return {
                        "limit": NodeParameter(
                            name="limit",
                            type=int,
                            required=False,
                            default=10,
                            description="Maximum number of records to return",
                        ),
                        "offset": NodeParameter(
                            name="offset",
                            type=int,
                            required=False,
                            default=0,
                            description="Number of records to skip",
                        ),
                        "order_by": NodeParameter(
                            name="order_by",
                            type=list,
                            required=False,
                            default=[],
                            description="Fields to sort by",
                        ),
                        "filter": NodeParameter(
                            name="filter",
                            type=dict,
                            required=False,
                            default={},
                            description="Filter criteria",
                        ),
                    }

                elif operation.startswith("bulk_"):
                    return {
                        "data": NodeParameter(
                            name="data",
                            type=list,
                            required=False,
                            default=[],
                            description="List of records for bulk operation",
                        ),
                        "batch_size": NodeParameter(
                            name="batch_size",
                            type=int,
                            required=False,
                            default=1000,
                            description="Batch size for bulk operations",
                        ),
                        "conflict_resolution": NodeParameter(
                            name="conflict_resolution",
                            type=str,
                            required=False,
                            default="skip",
                            description="How to handle conflicts",
                        ),
                        "filter": NodeParameter(
                            name="filter",
                            type=dict,
                            required=False,
                            default={},
                            description="Filter for bulk update/delete",
                        ),
                        "update": NodeParameter(
                            name="update",
                            type=dict,
                            required=False,
                            default={},
                            description="Update values for bulk update",
                        ),
                    }

                return {}

            def execute(self, **kwargs) -> Dict[str, Any]:
                """Execute the database operation."""
                # Apply tenant filtering if multi-tenant mode
                if self.dataflow_instance.config.multi_tenant:
                    tenant_id = self.dataflow_instance._tenant_context.get("tenant_id")
                    if tenant_id and "filter" in kwargs:
                        kwargs["filter"]["tenant_id"] = tenant_id

                # Simulate database operations
                if operation == "create":
                    record_id = 1  # Simulated ID
                    result = {"id": record_id, **kwargs}

                elif operation == "read":
                    record_id = kwargs.get("id", 1)
                    result = {"id": record_id, "found": True}

                elif operation == "update":
                    record_id = kwargs.get("id", 1)
                    updates = {k: v for k, v in kwargs.items() if k != "id"}
                    result = {"id": record_id, "updated": True, "changes": updates}

                elif operation == "delete":
                    record_id = kwargs.get("id", 1)
                    result = {"id": record_id, "deleted": True}

                elif operation == "list":
                    limit = kwargs.get("limit", 10)
                    result = {"records": [], "count": 0, "limit": limit}

                elif operation.startswith("bulk_"):
                    data = kwargs.get("data", [])
                    batch_size = kwargs.get("batch_size", 1000)
                    result = {
                        "processed": len(data),
                        "batch_size": batch_size,
                        "operation": operation,
                    }

                else:
                    result = {"operation": operation, "status": "executed"}

                # Add metadata
                result.update(
                    {
                        "model": model_name,
                        "operation": operation,
                        "timestamp": "2024-01-01T00:00:00Z",
                    }
                )

                return result

        # Set dynamic class name and proper module
        DataFlowNode.__name__ = (
            f"{model_name}{operation.replace('_', ' ').title().replace(' ', '')}Node"
        )
        DataFlowNode.__qualname__ = DataFlowNode.__name__

        return DataFlowNode
