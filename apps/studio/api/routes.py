"""
Studio-specific API routes that complement the SDK gateway.

These routes provide additional functionality required by the PRD:
- AI Chat endpoints for natural language workflow creation
- Export endpoints for Python/YAML code generation
- PRD-compliant endpoint naming conventions

All implementations use SDK components only - no custom orchestration.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
import json
from fastapi import HTTPException, Request, Query
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field

from kailash.middleware import AIChatMiddleware, ChatMessage, WorkflowGenerator
from kailash.utils.export import WorkflowExporter
from kailash.workflow import Workflow
from kailash.workflow.builder import WorkflowBuilder
from kailash.nodes.ai import LLMAgentNode
from kailash.nodes.code import PythonCodeNode

logger = logging.getLogger(__name__)


# Pydantic Models for PRD-compliant endpoints
class ChatRequest(BaseModel):
    """Request model for AI chat endpoint (PRD-compliant)."""
    message: str
    workflow_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ChatResponse(BaseModel):
    """Response model for AI chat endpoint (PRD-compliant)."""
    response: str
    workflow_update: Optional[Dict[str, Any]] = None
    suggested_actions: Optional[List[str]] = None


class ExportRequest(BaseModel):
    """Request model for workflow export (PRD-compliant)."""
    format: str = Field(description="Export format: python or yaml", pattern="^(python|yaml)$")


class ExportResponse(BaseModel):
    """Response model for workflow export (PRD-compliant)."""
    format: str
    content: str
    filename: str


class NodeTypesResponse(BaseModel):
    """Response model for node types endpoint (PRD-compliant)."""
    categories: Dict[str, Dict[str, List[Dict[str, Any]]]]


def add_studio_routes(gateway):
    """
    Add Studio-specific routes that align with PRD specifications.
    
    This function adds the missing endpoints required by the PRD:
    - POST /api/chat - AI chat interface
    - POST /api/workflows/{id}/export - Export workflow as Python/YAML
    - GET /api/nodes/types - Get available node types (PRD naming)
    - WebSocket /api/workflows/{id}/live - Real-time execution updates
    
    All implementations use SDK components only.
    """
    
    # Initialize AI chat middleware if not already present
    if not hasattr(gateway, 'ai_chat'):
        gateway.ai_chat = AIChatMiddleware(
            agent_ui_middleware=gateway.agent_ui,
            enable_semantic_search=True
        )
    
    # Initialize workflow generator for AI-based workflow creation
    if not hasattr(gateway, 'workflow_generator'):
        gateway.workflow_generator = WorkflowGenerator(gateway.schema_registry)
    
    # Initialize workflow exporter using SDK's export functionality
    if not hasattr(gateway, 'workflow_exporter'):
        gateway.workflow_exporter = WorkflowExporter()
    
    @gateway.app.post("/api/chat", response_model=ChatResponse, tags=["AI Chat"])
    async def chat_with_ai(
        request: ChatRequest, 
        session_id: Optional[str] = Query(None, description="Session ID for context")
    ):
        """
        Send chat message to AI assistant for workflow creation and modification.
        
        This endpoint enables the chat-first design principle from the PRD,
        allowing users to create and modify workflows using natural language.
        """
        try:
            # Start chat session if not provided
            if not session_id:
                session_id = await gateway.ai_chat.start_chat_session(
                    user_id="default_user",
                    metadata={"source": "studio_api"}
                )
            
            # Create chat message
            message = ChatMessage(
                content=request.message,
                role="user",
                timestamp=datetime.now(timezone.utc),
                metadata=request.context
            )
            
            # Process message and get response
            response = await gateway.ai_chat.process_message(
                session_id=session_id,
                message=message,
                workflow_id=request.workflow_id
            )
            
            # Check if workflow creation/modification is requested
            workflow_update = None
            suggested_actions = []
            
            # Analyze intent for workflow operations
            if any(keyword in request.message.lower() for keyword in 
                   ["create", "build", "make", "design", "workflow", "process"]):
                
                # Generate workflow from natural language
                workflow_config = await gateway.workflow_generator.generate_from_prompt(
                    prompt=request.message,
                    context=request.context
                )
                
                if workflow_config:
                    # Create workflow in the session
                    workflow_id = await gateway.agent_ui.create_dynamic_workflow(
                        session_id=session_id,
                        workflow_config=workflow_config
                    )
                    
                    workflow_update = {
                        "action": "created",
                        "workflow_id": workflow_id,
                        "config": workflow_config
                    }
                    
                    suggested_actions = [
                        "Configure node parameters",
                        "Test the workflow",
                        "Export as Python code"
                    ]
            
            elif request.workflow_id and any(keyword in request.message.lower() for keyword in
                                           ["add", "modify", "change", "update", "remove"]):
                
                # Modify existing workflow
                modifications = await gateway.workflow_generator.generate_modifications(
                    workflow_id=request.workflow_id,
                    prompt=request.message,
                    context=request.context
                )
                
                if modifications:
                    workflow_update = {
                        "action": "modified",
                        "workflow_id": request.workflow_id,
                        "modifications": modifications
                    }
                    
                    suggested_actions = [
                        "Review changes",
                        "Test updated workflow",
                        "Revert if needed"
                    ]
            
            return ChatResponse(
                response=response.content,
                workflow_update=workflow_update,
                suggested_actions=suggested_actions
            )
            
        except Exception as e:
            logger.error(f"Chat error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @gateway.app.post("/api/workflows/{workflow_id}/export", 
                      response_model=ExportResponse, 
                      tags=["Workflows"])
    async def export_workflow(
        workflow_id: str, 
        request: ExportRequest,
        session_id: str = Query(..., description="Session ID required for workflow access")
    ):
        """
        Export workflow as Python code or YAML configuration.
        
        This endpoint allows users to export their visual workflows as
        production-ready Python code or YAML configuration files.
        Uses SDK's export functionality only.
        """
        try:
            # Get the workflow
            session = await gateway.agent_ui.get_session(session_id)
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")
            
            workflow = None
            if workflow_id in session.workflows:
                workflow = session.workflows[workflow_id]
            elif workflow_id in gateway.agent_ui.shared_workflows:
                workflow = gateway.agent_ui.shared_workflows[workflow_id]
            else:
                raise HTTPException(status_code=404, detail="Workflow not found")
            
            # Export based on format using SDK's WorkflowExporter
            if request.format == "python":
                # Generate Python code using SDK patterns
                content = _generate_python_code(workflow)
                filename = f"{workflow.name.replace(' ', '_').lower()}_workflow.py"
            else:  # yaml
                # Use SDK's YAML export
                content = gateway.workflow_exporter.to_yaml(workflow)
                filename = f"{workflow.name.replace(' ', '_').lower()}_workflow.yaml"
            
            return ExportResponse(
                format=request.format,
                content=content,
                filename=filename
            )
            
        except Exception as e:
            logger.error(f"Export error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @gateway.app.get("/api/nodes/types", response_model=NodeTypesResponse, tags=["Schemas"])
    async def get_node_types():
        """
        Get available node types and their configuration schemas (PRD-compliant naming).
        
        This endpoint provides the node palette information needed by the
        frontend to display available nodes grouped by category.
        """
        try:
            # Get all registered nodes
            available_nodes = gateway.node_registry.get_all_nodes()
            
            # Organize by category with schemas
            categories = {
                "AI": {"nodes": []},
                "Data": {"nodes": []},
                "Logic": {"nodes": []},
                "API": {"nodes": []},
                "Code": {"nodes": []},
                "Transform": {"nodes": []},
                "MCP": {"nodes": []},
                "Security": {"nodes": []},
                "Admin": {"nodes": []}
            }
            
            # Categorize nodes
            for node_name, node_class in available_nodes.items():
                # Get node schema
                schema = gateway.schema_registry.get_node_schema(node_class)
                
                # Determine category
                category = _get_node_category(node_name, node_class)
                
                # Add to appropriate category
                if category in categories:
                    categories[category]["nodes"].append({
                        "name": node_name,
                        "display_name": schema.get("display_name", node_name),
                        "description": schema.get("description", ""),
                        "schema": schema,
                        "icon": schema.get("icon", "node"),
                        "color": schema.get("color", "#6366f1")
                    })
            
            # Remove empty categories
            categories = {k: v for k, v in categories.items() if v["nodes"]}
            
            return NodeTypesResponse(categories=categories)
            
        except Exception as e:
            logger.error(f"Error getting node types: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @gateway.app.websocket("/api/workflows/{workflow_id}/live")
    async def workflow_live_updates(websocket, workflow_id: str):
        """
        WebSocket connection for real-time workflow execution updates (PRD-compliant).
        
        This endpoint provides real-time updates during workflow execution,
        including node completion, progress updates, and error notifications.
        """
        await gateway.realtime.handle_workflow_websocket(
            websocket=websocket,
            workflow_id=workflow_id
        )
    
    logger.info("✅ Studio PRD-compliant routes added to gateway")


def _generate_python_code(workflow: Workflow) -> str:
    """
    Generate Python code from a workflow using SDK patterns only.
    
    This generates production-ready Python code that uses the Kailash SDK
    to recreate the workflow programmatically.
    """
    lines = []
    
    # Import statements
    lines.extend([
        '"""',
        f'Generated Kailash Workflow: {workflow.name}',
        f'{workflow.description or ""}',
        '',
        'This code was generated from a visual workflow and can be executed',
        'directly using the Kailash SDK.',
        '"""',
        '',
        'from kailash.workflow import Workflow',
        'from kailash.workflow.builder import WorkflowBuilder',
        'from kailash.runtime import LocalRuntime',
    ])
    
    # Collect unique node types for imports
    node_types = set()
    for node_id, node_instance in workflow.nodes.items():
        actual_node = workflow._node_instances.get(node_id)
        if actual_node:
            node_types.add(actual_node.__class__.__name__)
    
    # Import node classes
    lines.append('')
    lines.append('# Import required nodes')
    for node_type in sorted(node_types):
        module = _get_node_module(node_type)
        if module:
            lines.append(f'from kailash.nodes.{module} import {node_type}')
    
    # Create workflow function
    lines.extend([
        '',
        '',
        'def create_workflow():',
        f'    """Create and configure the {workflow.name} workflow."""',
        f'    workflow = Workflow("{workflow.name}", "{workflow.description or ""}")',
        '',
        '    # Add nodes'
    ])
    
    # Add nodes
    for node_id, node_instance in workflow.nodes.items():
        # Get the actual node from the workflow's _node_instances
        actual_node = workflow._node_instances.get(node_id)
        if actual_node:
            node_class = actual_node.__class__.__name__
            # Get node configuration
            config_items = []
            try:
                for param_name, param in actual_node.get_parameters().items():
                    if hasattr(actual_node, param_name):
                        value = getattr(actual_node, param_name)
                        if value is not None:
                            if isinstance(value, str):
                                config_items.append(f'{param_name}="{value}"')
                            else:
                                config_items.append(f'{param_name}={repr(value)}')
            except:
                # Fallback: just use name
                config_items.append(f'name="{node_id}"')
            
            config_str = ", ".join(config_items)
            lines.append(f'    workflow.add_node("{node_id}", {node_class}({config_str}))')
        else:
            # Fallback for unknown node type
            lines.append(f'    # workflow.add_node("{node_id}", UnknownNode(name="{node_id}"))')
    
    # Add connections
    if workflow.connections:
        lines.extend([
            '',
            '    # Add connections'
        ])
        for conn in workflow.connections:
            lines.append(
                f'    workflow.connect("{conn.source_node}", "{conn.source_output}", '
                f'"{conn.target_node}", "{conn.target_input}")'
            )
    
    # Return workflow
    lines.extend([
        '',
        '    return workflow',
        '',
        '',
        'def main():',
        '    """Execute the workflow."""',
        '    # Create workflow',
        '    workflow = create_workflow()',
        '',
        '    # Create runtime and execute',
        '    runtime = LocalRuntime()',
        '    results, run_id = runtime.execute(workflow, parameters={})',
        '',
        '    print(f"Execution completed. Run ID: {run_id}")',
        '    print(f"Results: {results}")',
        '',
        '',
        'if __name__ == "__main__":',
        '    main()'
    ])
    
    return '\n'.join(lines)


def _get_node_module(node_type: str) -> Optional[str]:
    """Get the module path for a node type."""
    # Map node types to their modules
    module_map = {
        # AI nodes
        'LLMAgentNode': 'ai',
        'MonitoredLLMAgentNode': 'ai',
        'EmbeddingGeneratorNode': 'ai',
        'A2AAgentNode': 'ai',
        'MCPAgentNode': 'ai',
        'SelfOrganizingAgentNode': 'ai',
        
        # Data nodes
        'CSVReaderNode': 'data',
        'JSONReaderNode': 'data',
        'SQLDatabaseNode': 'data',
        'AsyncSQLDatabaseNode': 'data',
        'SharePointGraphReader': 'data',
        'DirectoryReaderNode': 'data',
        
        # API nodes
        'HTTPRequestNode': 'api',
        'RESTClientNode': 'api',
        'OAuth2Node': 'api',
        'GraphQLClientNode': 'api',
        
        # Logic nodes
        'SwitchNode': 'logic',
        'MergeNode': 'logic',
        'WorkflowNode': 'logic',
        'ConvergenceCheckerNode': 'logic',
        
        # Transform nodes
        'FilterNode': 'transform',
        'DataTransformer': 'transform',
        'HierarchicalChunkerNode': 'transform',
        
        # Code nodes
        'PythonCodeNode': 'code',
        
        # Security nodes
        'CredentialManagerNode': 'security',
        'AccessControlManager': 'security',
        'AuditLogNode': 'security',
        
        # Admin nodes
        'UserManagementNode': 'admin',
        'RoleManagementNode': 'admin',
        'PermissionCheckNode': 'admin',
    }
    
    return module_map.get(node_type)


def _get_node_category(node_name: str, node_class) -> str:
    """Determine node category based on name and class."""
    # Check module path for hints
    module_path = node_class.__module__
    
    # AI nodes
    if "ai" in module_path or any(name in node_name.lower() for name in 
                                  ["llm", "agent", "embedding", "a2a", "mcp"]):
        return "AI"
    
    # Data nodes
    elif "data" in module_path or any(name in node_name.lower() for name in
                                     ["csv", "json", "sql", "database", "reader", "sharepoint"]):
        return "Data"
    
    # Logic nodes
    elif "logic" in module_path or any(name in node_name.lower() for name in
                                      ["switch", "merge", "convergence", "workflow"]):
        return "Logic"
    
    # API nodes
    elif "api" in module_path or any(name in node_name.lower() for name in
                                    ["http", "rest", "oauth", "graphql", "api"]):
        return "API"
    
    # Transform nodes
    elif "transform" in module_path or any(name in node_name.lower() for name in
                                         ["filter", "map", "transform", "chunk", "processor"]):
        return "Transform"
    
    # MCP nodes
    elif "mcp" in node_name.lower():
        return "MCP"
    
    # Security nodes
    elif "security" in module_path or any(name in node_name.lower() for name in
                                         ["credential", "access", "audit", "security"]):
        return "Security"
    
    # Admin nodes
    elif "admin" in module_path or any(name in node_name.lower() for name in
                                      ["user", "role", "permission", "management"]):
        return "Admin"
    
    # Code nodes (default for PythonCodeNode)
    else:
        return "Code"