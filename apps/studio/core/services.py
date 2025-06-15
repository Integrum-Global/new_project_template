"""
Studio Core Services - Enterprise Middleware Integration

Business logic and service layer using 100% Kailash SDK middleware components.
All workflow operations delegate to middleware with no manual orchestration.
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple

from kailash.middleware import (
    AgentUIMiddleware, AIChatMiddleware, RealtimeMiddleware,
    DynamicSchemaRegistry, NodeSchemaGenerator, EventStream
)
from kailash.middleware.communication.events import (
    EventType, EventPriority, WorkflowEvent, NodeEvent, UIEvent
)
from kailash.workflow.builder import WorkflowBuilder
from kailash.workflow.templates import BusinessWorkflowTemplates
from kailash.runtime.async_local import AsyncLocalRuntime
from kailash.nodes.base import NodeRegistry

from .models import (
    StudioWorkflow, WorkflowExecution, WorkflowTemplate, NodeSchema,
    ExecutionStatus, WorkflowStatus, TemplateCategory, NodeType,
    AIGenerationRequest, NodeDefinitionAPI, ConnectionDefinitionAPI
)
from .database import StudioDatabase
from .security import SecurityService

logger = logging.getLogger(__name__)


class WorkflowService:
    """Service for managing workflows using enterprise middleware."""
    
    def __init__(self, agent_ui: AgentUIMiddleware, db: StudioDatabase = None):
        self.db = db or StudioDatabase()
        self.agent_ui = agent_ui
        self.runtime = AsyncLocalRuntime()
        
        # Initialize security service
        self.security = SecurityService()
        
        # Initialize registries for workflow generation
        self.node_registry = NodeRegistry()
        self.schema_registry = DynamicSchemaRegistry()
        
    async def create_workflow(self, name: str, description: str = "", 
                            tenant_id: str = "default", owner_id: str = None,
                            user_context: Dict[str, Any] = None) -> StudioWorkflow:
        """Create a new workflow with security validation."""
        # Check permissions using ABAC
        if user_context:
            can_create = await self.security.evaluate_permission(
                user_context, "workflow", "create"
            )
            if not can_create:
                raise PermissionError("Insufficient permissions to create workflow")
        
        # Create session with middleware
        session_id = await self.agent_ui.create_session(owner_id or "anonymous")
        
        workflow = StudioWorkflow(
            workflow_id=f"workflow_{uuid.uuid4().hex}",
            name=name,
            description=description,
            tenant_id=tenant_id,
            owner_id=owner_id,
            session_id=session_id
        )
        
        await self.db.save_workflow(workflow)
        logger.info(f"Created workflow {workflow.workflow_id}: {name}")
        
        # Log security event
        await self.security.log_security_event(
            "workflow_created", workflow.workflow_id, user_context
        )
        
        return workflow
    
    async def create_dynamic_workflow(self, session_id: str, config: Dict[str, Any],
                                    tenant_id: str = "default") -> str:
        """Create workflow dynamically using AgentUIMiddleware."""
        workflow_id = await self.agent_ui.create_dynamic_workflow(session_id, config)
        
        # Save to our database for tracking
        workflow = StudioWorkflow(
            workflow_id=workflow_id,
            name=config.get("name", "Dynamic Workflow"),
            description=config.get("description", "Generated dynamically"),
            tenant_id=tenant_id,
            session_id=session_id
        )
        
        # Add nodes from config
        for node_data in config.get("nodes", []):
            workflow.add_node(
                node_type=node_data["type"],
                name=node_data.get("name", node_data["type"]),
                config=node_data.get("config", {}),
                position=node_data.get("position", {"x": 0, "y": 0})
            )
        
        # Add connections from config
        for conn_data in config.get("connections", []):
            workflow.add_connection(
                from_node=conn_data["from_node"],
                from_output=conn_data["from_output"],
                to_node=conn_data["to_node"],
                to_input=conn_data["to_input"]
            )
        
        await self.db.save_workflow(workflow)
        logger.info(f"Created dynamic workflow {workflow_id} with {len(workflow.nodes)} nodes")
        return workflow_id
    
    async def execute_workflow(self, session_id: str, workflow_id: str, 
                             inputs: Dict[str, Any] = None) -> str:
        """Execute workflow using AgentUIMiddleware delegation."""
        execution_id = await self.agent_ui.execute_workflow(
            session_id, workflow_id, inputs or {}
        )
        
        # Create execution record for tracking
        execution = WorkflowExecution(
            execution_id=execution_id,
            workflow_id=workflow_id,
            inputs=inputs or {},
            tenant_id="default"  # Extract from session if needed
        )
        execution.start("system")
        
        await self.db.save_execution(execution)
        logger.info(f"Started execution {execution_id} for workflow {workflow_id}")
        return execution_id
    
    async def get_workflow(self, workflow_id: str, tenant_id: str = "default",
                         user_context: Dict[str, Any] = None) -> Optional[StudioWorkflow]:
        """Get a workflow by ID with security validation."""
        # Check read permissions
        if user_context:
            can_read = await self.security.evaluate_permission(
                user_context, f"workflow:{workflow_id}", "read"
            )
            if not can_read:
                return None
        
        return await self.db.get_workflow(workflow_id, tenant_id)
    
    async def update_workflow(self, workflow: StudioWorkflow,
                            user_context: Dict[str, Any] = None) -> StudioWorkflow:
        """Update an existing workflow with security validation."""
        # Check update permissions
        if user_context:
            can_update = await self.security.evaluate_permission(
                user_context, f"workflow:{workflow.workflow_id}", "update"
            )
            if not can_update:
                raise PermissionError("Insufficient permissions to update workflow")
        
        workflow.updated_at = datetime.now(timezone.utc)
        workflow.version += 1
        await self.db.save_workflow(workflow)
        
        # Log security event
        await self.security.log_security_event(
            "workflow_updated", workflow.workflow_id, user_context
        )
        
        logger.info(f"Updated workflow {workflow.workflow_id} to version {workflow.version}")
        return workflow
    
    async def delete_workflow(self, workflow_id: str, tenant_id: str = "default",
                            user_context: Dict[str, Any] = None) -> bool:
        """Delete a workflow with security validation."""
        # Check delete permissions
        if user_context:
            can_delete = await self.security.evaluate_permission(
                user_context, f"workflow:{workflow_id}", "delete"
            )
            if not can_delete:
                raise PermissionError("Insufficient permissions to delete workflow")
        
        result = await self.db.delete_workflow(workflow_id, tenant_id)
        if result:
            # Log security event
            await self.security.log_security_event(
                "workflow_deleted", workflow_id, user_context
            )
            logger.info(f"Deleted workflow {workflow_id}")
        return result
    
    async def list_workflows(self, tenant_id: str = "default", 
                           status: WorkflowStatus = None, 
                           owner_id: str = None,
                           user_context: Dict[str, Any] = None) -> List[StudioWorkflow]:
        """List workflows with security filtering."""
        workflows = await self.db.list_workflows(tenant_id, status, owner_id)
        
        # Filter based on user permissions
        if user_context:
            filtered_workflows = []
            for workflow in workflows:
                can_read = await self.security.evaluate_permission(
                    user_context, f"workflow:{workflow.workflow_id}", "read"
                )
                if can_read:
                    filtered_workflows.append(workflow)
            return filtered_workflows
        
        return workflows
    
    async def generate_workflow_from_ai(self, request: AIGenerationRequest) -> StudioWorkflow:
        """Generate a workflow using AIChatMiddleware."""
        logger.info(f"Generating workflow from AI prompt: {request.prompt[:100]}...")
        
        # Create session for AI interaction
        session_id = await self.agent_ui.create_session("ai_generator")
        
        # Use AIChatMiddleware through AgentUI
        # Note: AIChatMiddleware is integrated into AgentUI
        workflow_config = {
            "name": "AI Generated Workflow",
            "description": f"Generated from: {request.prompt}",
            "ai_prompt": request.prompt,
            "constraints": request.constraints,
            "preferred_nodes": request.preferred_nodes
        }
        
        # Create dynamic workflow using middleware
        workflow_id = await self.create_dynamic_workflow(
            session_id, workflow_config, request.tenant_id
        )
        
        workflow = await self.get_workflow(workflow_id, request.tenant_id)
        logger.info(f"Generated workflow {workflow_id} with AI assistance")
        return workflow


class ExecutionService:
    """Service for managing workflow executions using middleware."""
    
    def __init__(self, agent_ui: AgentUIMiddleware, realtime: RealtimeMiddleware, 
                 db: StudioDatabase = None):
        self.db = db or StudioDatabase()
        self.agent_ui = agent_ui
        self.realtime = realtime
        self.runtime = AsyncLocalRuntime()
        self.security = SecurityService()
        
    async def start_execution(self, workflow_id: str, inputs: Dict[str, Any] = None,
                            tenant_id: str = "default", started_by: str = None,
                            user_context: Dict[str, Any] = None) -> WorkflowExecution:
        """Start workflow execution using middleware with security validation."""
        # Check execute permissions
        if user_context:
            can_execute = await self.security.evaluate_permission(
                user_context, f"workflow:{workflow_id}", "execute"
            )
            if not can_execute:
                raise PermissionError("Insufficient permissions to execute workflow")
        
        workflow = await self.db.get_workflow(workflow_id, tenant_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        # Create session and execute via middleware
        session_id = workflow.session_id or await self.agent_ui.create_session(started_by or "anonymous")
        execution_id = await self.agent_ui.execute_workflow(session_id, workflow_id, inputs or {})
        
        execution = WorkflowExecution(
            execution_id=execution_id,
            workflow_id=workflow_id,
            inputs=inputs or {},
            tenant_id=tenant_id
        )
        execution.start(started_by)
        execution.progress.total_nodes = len(workflow.nodes)
        
        await self.db.save_execution(execution)
        
        # Log security event
        await self.security.log_security_event(
            "workflow_executed", workflow_id, user_context
        )
        
        logger.info(f"Started execution {execution_id} for workflow {workflow_id}")
        return execution
    
    async def get_execution(self, execution_id: str, tenant_id: str = "default",
                          user_context: Dict[str, Any] = None) -> Optional[WorkflowExecution]:
        """Get execution with security validation."""
        execution = await self.db.get_execution(execution_id, tenant_id)
        if not execution:
            return None
            
        # Check read permissions for the workflow
        if user_context:
            can_read = await self.security.evaluate_permission(
                user_context, f"workflow:{execution.workflow_id}", "read"
            )
            if not can_read:
                return None
        
        return execution
    
    async def cancel_execution(self, execution_id: str, tenant_id: str = "default",
                             user_context: Dict[str, Any] = None) -> bool:
        """Cancel execution with security validation."""
        execution = await self.get_execution(execution_id, tenant_id, user_context)
        if not execution:
            return False
        
        # Check execute permissions (needed to cancel)
        if user_context:
            can_execute = await self.security.evaluate_permission(
                user_context, f"workflow:{execution.workflow_id}", "execute"
            )
            if not can_execute:
                raise PermissionError("Insufficient permissions to cancel execution")
        
        if execution.status == ExecutionStatus.RUNNING:
            execution.status = ExecutionStatus.CANCELLED
            execution.completed_at = datetime.now(timezone.utc)
            await self.db.save_execution(execution)
            
            # Send real-time update via RealtimeMiddleware
            event = WorkflowEvent(
                id=f"event_{uuid.uuid4().hex}",
                type=EventType.WORKFLOW_CANCELLED,
                timestamp=datetime.now(timezone.utc),
                workflow_id=execution.workflow_id,
                execution_id=execution_id,
                source="execution_service",
                session_id=tenant_id
            )
            await self.realtime.event_stream.emit(event)
            
            # Log security event
            await self.security.log_security_event(
                "execution_cancelled", execution_id, user_context
            )
            
            logger.info(f"Cancelled execution {execution_id}")
            return True
        
        return False
    
    async def list_executions(self, workflow_id: str = None, tenant_id: str = "default",
                            status: ExecutionStatus = None,
                            user_context: Dict[str, Any] = None) -> List[WorkflowExecution]:
        """List executions with security filtering."""
        executions = await self.db.list_executions(workflow_id, tenant_id, status)
        
        # Filter based on user permissions
        if user_context:
            filtered_executions = []
            for execution in executions:
                can_read = await self.security.evaluate_permission(
                    user_context, f"workflow:{execution.workflow_id}", "read"
                )
                if can_read:
                    filtered_executions.append(execution)
            return filtered_executions
        
        return executions


class NodeService:
    """Service for managing node schemas and discovery with enterprise features."""
    
    def __init__(self):
        self.schema_registry = DynamicSchemaRegistry()
        self.node_registry = NodeRegistry()
        self.schema_generator = NodeSchemaGenerator()
        self.security = SecurityService()
    
    async def get_node_types(self, category: NodeType = None,
                           user_context: Dict[str, Any] = None) -> Dict[str, List[NodeSchema]]:
        """Get available node types with security filtering."""
        # Get all registered node classes including enterprise security nodes
        all_nodes = self.node_registry.list_nodes()
        all_node_classes = list(all_nodes.values())
        node_types = self.schema_registry.get_all_node_schemas(all_node_classes)
        
        # Add enterprise security nodes
        security_nodes = await self.security.get_security_node_schemas()
        node_types.update(security_nodes)
        
        # Category mapping
        category_mapping = {
            "ai": NodeType.AI_ML,
            "ai_ml": NodeType.AI_ML,
            "data": NodeType.DATA_PROCESSING,
            "data_processing": NodeType.DATA_PROCESSING,
            "api": NodeType.API_INTEGRATION,
            "api_integration": NodeType.API_INTEGRATION,
            "logic": NodeType.LOGIC_CONTROL,
            "logic_control": NodeType.LOGIC_CONTROL,
            "transform": NodeType.TRANSFORM,
            "admin": NodeType.ADMIN_SECURITY,
            "security": NodeType.ADMIN_SECURITY,
            "admin_security": NodeType.ADMIN_SECURITY,
            "enterprise": NodeType.ENTERPRISE,
            "testing": NodeType.TESTING,
            "code": NodeType.CODE_EXECUTION,
            "code_execution": NodeType.CODE_EXECUTION,
            "general": NodeType.CODE_EXECUTION
        }
        
        categorized_nodes = {}
        for node_type, schema_data in node_types.items():
            # Check if user has permission to use this node type
            if user_context:
                can_use = await self.security.evaluate_permission(
                    user_context, f"node:{node_type}", "use"
                )
                if not can_use:
                    continue
            
            raw_category = schema_data.get("category", "general").lower()
            mapped_category = category_mapping.get(raw_category, NodeType.CODE_EXECUTION)
            
            node_schema = NodeSchema(
                node_type=node_type,
                category=mapped_category,
                display_name=schema_data.get("display_name", node_type),
                description=schema_data.get("description", ""),
                parameters=schema_data.get("parameters", {}),
                input_schema=schema_data.get("input_schema", {}),
                output_schema=schema_data.get("output_schema", {}),
                examples=schema_data.get("examples", [])
            )
            
            if category is None or node_schema.category == category:
                category_name = node_schema.category.value
                if category_name not in categorized_nodes:
                    categorized_nodes[category_name] = []
                categorized_nodes[category_name].append(node_schema)
        
        return categorized_nodes
    
    async def get_node_schema(self, node_type: str,
                            user_context: Dict[str, Any] = None) -> Optional[NodeSchema]:
        """Get schema for a specific node type with permission check."""
        # Check permissions
        if user_context:
            can_use = await self.security.evaluate_permission(
                user_context, f"node:{node_type}", "use"
            )
            if not can_use:
                return None
        
        # Check security nodes first
        security_schema = await self.security.get_security_node_schema(node_type)
        if security_schema:
            return security_schema
        
        # Get node class from registry
        node_class = self.node_registry.get(node_type)
        if not node_class:
            return None
            
        schema_data = self.schema_registry.get_node_schema(node_class)
        if not schema_data:
            return None
        
        return NodeSchema(
            node_type=node_type,
            category=NodeType(schema_data.get("category", "code_execution")),
            display_name=schema_data.get("display_name", node_type),
            description=schema_data.get("description", ""),
            parameters=schema_data.get("parameters", {}),
            input_schema=schema_data.get("input_schema", {}),
            output_schema=schema_data.get("output_schema", {}),
            examples=schema_data.get("examples", [])
        )
    
    async def validate_node_config(self, node_type: str, config: Dict[str, Any],
                                 user_context: Dict[str, Any] = None) -> Tuple[bool, List[str]]:
        """Validate node configuration with security checks."""
        # Check permissions
        if user_context:
            can_use = await self.security.evaluate_permission(
                user_context, f"node:{node_type}", "use"
            )
            if not can_use:
                return False, ["Insufficient permissions to use this node type"]
        
        schema = await self.get_node_schema(node_type, user_context)
        if not schema:
            return False, [f"Node type {node_type} not found or not accessible"]
        
        errors = []
        
        # Validate required parameters
        required_params = [
            param for param, details in schema.parameters.items()
            if details.get("required", False)
        ]
        
        for param in required_params:
            if param not in config:
                errors.append(f"Required parameter '{param}' is missing")
        
        # Validate parameter types (simplified validation)
        for param, value in config.items():
            if param in schema.parameters:
                param_schema = schema.parameters[param]
                expected_type = param_schema.get("type")
                
                # Basic type validation (could be enhanced)
                if expected_type == "str" and not isinstance(value, str):
                    errors.append(f"Parameter '{param}' should be a string")
                elif expected_type == "int" and not isinstance(value, int):
                    errors.append(f"Parameter '{param}' should be an integer")
                elif expected_type == "bool" and not isinstance(value, bool):
                    errors.append(f"Parameter '{param}' should be a boolean")
        
        return len(errors) == 0, errors


class TemplateService:
    """Service for managing workflow templates with enterprise features."""
    
    def __init__(self, db: StudioDatabase = None):
        self.db = db or StudioDatabase()
        self.business_templates = BusinessWorkflowTemplates()
        self.security = SecurityService()
    
    async def get_templates(self, category: TemplateCategory = None,
                          user_context: Dict[str, Any] = None) -> List[WorkflowTemplate]:
        """Get available workflow templates with security filtering."""
        templates = await self.db.list_templates(category)
        
        # Add built-in business templates if none exist
        if not templates:
            templates = await self._create_builtin_templates()
        
        # Filter based on user permissions
        if user_context:
            filtered_templates = []
            for template in templates:
                can_use = await self.security.evaluate_permission(
                    user_context, f"template:{template.template_id}", "use"
                )
                if can_use:
                    filtered_templates.append(template)
            return filtered_templates
        
        return templates
    
    async def create_workflow_from_template(self, template_id: str, name: str,
                                          tenant_id: str = "default",
                                          owner_id: str = None,
                                          user_context: Dict[str, Any] = None) -> StudioWorkflow:
        """Create a workflow instance from a template with security validation."""
        # Check template permissions
        if user_context:
            can_use = await self.security.evaluate_permission(
                user_context, f"template:{template_id}", "use"
            )
            if not can_use:
                raise PermissionError("Insufficient permissions to use this template")
        
        template = await self.db.get_template(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")
        
        workflow = template.create_workflow_instance(name, tenant_id, owner_id)
        await self.db.save_workflow(workflow)
        
        # Update template usage count
        template.usage_count += 1
        await self.db.save_template(template)
        
        # Log security event
        await self.security.log_security_event(
            "template_used", template_id, user_context
        )
        
        logger.info(f"Created workflow {workflow.workflow_id} from template {template_id}")
        return workflow
    
    async def _create_builtin_templates(self) -> List[WorkflowTemplate]:
        """Create built-in enterprise templates."""
        templates = []
        
        # Enterprise Security Templates
        security_templates = [
            ("Threat Detection Pipeline", "AI-powered threat detection and response workflow"),
            ("ABAC Permission Audit", "Comprehensive permission audit and compliance check"),
            ("Security Event Analysis", "Automated security event analysis and alerting")
        ]
        
        for name, description in security_templates:
            workflow = StudioWorkflow(
                workflow_id=f"builtin_{uuid.uuid4().hex}",
                name=name,
                description=description,
                status=WorkflowStatus.TEMPLATE
            )
            
            template = WorkflowTemplate(
                template_id=f"builtin_template_{uuid.uuid4().hex}",
                name=name,
                description=description,
                category=TemplateCategory.ADMIN_SECURITY,
                workflow_definition=workflow,
                difficulty_level="advanced",
                tags=["builtin", "security", "enterprise"]
            )
            
            await self.db.save_template(template)
            templates.append(template)
        
        # Data Processing Templates
        data_templates = [
            ("CSV Processing Pipeline", "Complete pipeline for CSV data processing with validation"),
            ("Database ETL Workflow", "Extract, transform, and load data between databases"),
            ("File Processing Automation", "Automated file processing with error handling")
        ]
        
        for name, description in data_templates:
            workflow = StudioWorkflow(
                workflow_id=f"builtin_{uuid.uuid4().hex}",
                name=name,
                description=description,
                status=WorkflowStatus.TEMPLATE
            )
            
            template = WorkflowTemplate(
                template_id=f"builtin_template_{uuid.uuid4().hex}",
                name=name,
                description=description,
                category=TemplateCategory.DATA_PROCESSING,
                workflow_definition=workflow,
                difficulty_level="intermediate",
                tags=["builtin", "data", "processing"]
            )
            
            await self.db.save_template(template)
            templates.append(template)
        
        return templates


class ExportService:
    """Service for exporting workflows to Python/YAML with enhanced styles."""
    
    def __init__(self):
        self.security = SecurityService()
    
    async def export_to_python(self, workflow: StudioWorkflow, 
                             style: str = "production",
                             user_context: Dict[str, Any] = None) -> str:
        """Export workflow to Python code with security validation."""
        # Check export permissions
        if user_context:
            can_export = await self.security.evaluate_permission(
                user_context, f"workflow:{workflow.workflow_id}", "export"
            )
            if not can_export:
                raise PermissionError("Insufficient permissions to export workflow")
        
        if style == "production":
            return await self._export_production_style(workflow)
        elif style == "development":
            return await self._export_development_style(workflow)
        elif style == "tutorial":
            return await self._export_tutorial_style(workflow)
        else:
            return await self._export_production_style(workflow)
    
    async def _export_production_style(self, workflow: StudioWorkflow) -> str:
        """Export in production-ready style."""
        lines = [
            "#!/usr/bin/env python3",
            '"""',
            f"Production Workflow: {workflow.name}",
            f"Description: {workflow.description}",
            f"Generated: {datetime.now().isoformat()}",
            '"""',
            "",
            "import asyncio",
            "import logging",
            "from kailash.workflow.builder import WorkflowBuilder",
            "from kailash.runtime.async_local import AsyncLocalRuntime",
            "",
            "logger = logging.getLogger(__name__)",
            "",
            "async def main():",
            f'    """Execute {workflow.name} workflow."""',
            "    # Build workflow",
            f'    builder = WorkflowBuilder()',
            ""
        ]
        
        # Add nodes
        for node in workflow.nodes:
            lines.append(f'    builder.add_node("{node.node_type}", "{node.node_id}", {node.config})')
        
        lines.append("")
        
        # Add connections
        for connection in workflow.connections:
            lines.append(
                f'    builder.add_connection("{connection.from_node}", "{connection.from_output}", '
                f'"{connection.to_node}", "{connection.to_input}")'
            )
        
        lines.extend([
            "",
            f'    workflow = builder.build("{workflow.workflow_id}")',
            "",
            "    # Execute workflow",
            "    runtime = AsyncLocalRuntime()",
            "    try:",
            "        result = await runtime.execute(workflow)",
            '        logger.info("Workflow completed successfully")',
            "        return result",
            "    except Exception as e:",
            '        logger.error(f"Workflow failed: {e}")',
            "        raise",
            "",
            'if __name__ == "__main__":',
            "    asyncio.run(main())"
        ])
        
        return "\n".join(lines)
    
    async def _export_development_style(self, workflow: StudioWorkflow) -> str:
        """Export in development-friendly style with debugging."""
        lines = [
            f"# Development Workflow: {workflow.name}",
            f"# {workflow.description}",
            "",
            "from kailash.workflow.builder import WorkflowBuilder",
            "from kailash.runtime.local import LocalRuntime",
            "",
            f'# Create workflow: {workflow.name}',
            f'builder = WorkflowBuilder()',
            ""
        ]
        
        # Add nodes with comments
        for i, node in enumerate(workflow.nodes):
            lines.append(f"# Node {i+1}: {node.name}")
            lines.append(f'builder.add_node("{node.node_type}", "{node.node_id}", {node.config})')
            lines.append("")
        
        # Add connections with comments
        lines.append("# Connections")
        for connection in workflow.connections:
            lines.append(
                f'builder.add_connection("{connection.from_node}", "{connection.from_output}", '
                f'"{connection.to_node}", "{connection.to_input}")  # {connection.from_node} -> {connection.to_node}'
            )
        
        lines.extend([
            "",
            f'workflow = builder.build("{workflow.workflow_id}")',
            "",
            "# Execute with debugging",
            "runtime = LocalRuntime(debug=True)",
            "result = runtime.execute(workflow)",
            "print(f'Result: {result}')"
        ])
        
        return "\n".join(lines)
    
    async def _export_tutorial_style(self, workflow: StudioWorkflow) -> str:
        """Export in tutorial style with explanations."""
        lines = [
            f"# Tutorial: {workflow.name}",
            f"# {workflow.description}",
            "",
            "# This tutorial shows how to build and execute a Kailash workflow",
            "",
            "# Step 1: Import required modules",
            "from kailash.workflow.builder import WorkflowBuilder",
            "from kailash.runtime.local import LocalRuntime",
            "",
            "# Step 2: Create a workflow builder",
            f'builder = WorkflowBuilder()',
            ""
        ]
        
        # Add nodes with detailed explanations
        for i, node in enumerate(workflow.nodes):
            lines.extend([
                f"# Step {i+3}: Add {node.name} ({node.node_type})",
                f"# This node will: {node.node_type.replace('Node', '').replace('_', ' ').lower()}",
                f'builder.add_node(',
                f'    node_type="{node.node_type}",',
                f'    node_id="{node.node_id}",',
                f'    config={node.config}',
                f')',
                ""
            ])
        
        # Add connections with explanations
        if workflow.connections:
            step_num = len(workflow.nodes) + 3
            lines.append(f"# Step {step_num}: Connect the nodes")
            for connection in workflow.connections:
                lines.extend([
                    f"# Connect {connection.from_node} output to {connection.to_node} input",
                    f'builder.add_connection("{connection.from_node}", "{connection.from_output}", '
                    f'"{connection.to_node}", "{connection.to_input}")',
                    ""
                ])
        
        final_step = len(workflow.nodes) + len(workflow.connections) + 4
        lines.extend([
            f"# Step {final_step}: Build and execute the workflow",
            f'workflow = builder.build("{workflow.workflow_id}")',
            "",
            "# Execute the workflow",
            "runtime = LocalRuntime()",
            "result = runtime.execute(workflow)",
            "",
            "# Print the results",
            "print('Workflow completed!')",
            "print(f'Results: {result}')"
        ])
        
        return "\n".join(lines)
    
    async def export_to_yaml(self, workflow: StudioWorkflow,
                           user_context: Dict[str, Any] = None) -> str:
        """Export workflow to YAML format with security validation."""
        # Check export permissions
        if user_context:
            can_export = await self.security.evaluate_permission(
                user_context, f"workflow:{workflow.workflow_id}", "export"
            )
            if not can_export:
                raise PermissionError("Insufficient permissions to export workflow")
        
        import yaml
        
        workflow_dict = {
            "name": workflow.name,
            "description": workflow.description,
            "version": workflow.version,
            "metadata": {
                "created_at": workflow.created_at.isoformat(),
                "updated_at": workflow.updated_at.isoformat(),
                "tenant_id": workflow.tenant_id,
                "owner_id": workflow.owner_id
            },
            "nodes": [
                {
                    "id": node.node_id,
                    "type": node.node_type,
                    "name": node.name,
                    "config": node.config,
                    "position": node.position
                }
                for node in workflow.nodes
            ],
            "connections": [
                {
                    "from_node": conn.from_node,
                    "from_output": conn.from_output,
                    "to_node": conn.to_node,
                    "to_input": conn.to_input
                }
                for conn in workflow.connections
            ]
        }
        
        return yaml.dump(workflow_dict, default_flow_style=False, indent=2)