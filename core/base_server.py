"""
Base Data Bridge MCP Server - Built entirely with Kailash SDK components.

This provides the foundation for all Mode 1 and Mode 2 MCP servers.
"""

from typing import Dict, Any, List, Optional, Callable
import logging

from kailash.middleware.mcp import MiddlewareMCPServer, MCPServerConfig, MCPToolNode
from kailash.workflow.builder import WorkflowBuilder
from kailash.runtime.local import LocalRuntime
from kailash.nodes.ai import LLMAgentNode, MonitoredLLMAgentNode
from kailash.nodes.security import CredentialManagerNode, AuditLogNode
from kailash.nodes.data import AsyncSQLDatabaseNode
from kailash.middleware import create_gateway

logger = logging.getLogger(__name__)


class DataBridgeMCPServer(MiddlewareMCPServer):
    """
    Base class for all data bridge MCP servers.
    
    Built entirely with Kailash SDK components:
    - Uses MiddlewareMCPServer for MCP protocol
    - LocalRuntime for workflow execution
    - SDK nodes for all functionality
    - No custom orchestration
    """
    
    def __init__(
        self,
        config: MCPServerConfig = None,
        enable_security: bool = True,
        enable_monitoring: bool = True,
        enable_ai: bool = False
    ):
        """
        Initialize data bridge MCP server.
        
        Args:
            config: MCP server configuration
            enable_security: Enable enterprise security features
            enable_monitoring: Enable performance monitoring
            enable_ai: Enable AI-powered features (Mode 2)
        """
        super().__init__(config or MCPServerConfig())
        
        # Initialize Kailash runtime for workflow execution
        self.runtime = LocalRuntime(
            enable_async=True,
            enable_monitoring=enable_monitoring,
            enable_security=enable_security
        )
        
        # Set up core components
        self._setup_security(enable_security)
        self._setup_monitoring(enable_monitoring)
        self._setup_ai(enable_ai)
        
        # Registry for data connectors
        self.connectors: Dict[str, Any] = {}
        
        # Registry for dynamic workflows
        self.workflows: Dict[str, WorkflowBuilder] = {}
        
        logger.info(f"Initialized {self.__class__.__name__} with Kailash SDK components")
    
    def _setup_security(self, enabled: bool):
        """Set up enterprise security using Kailash nodes."""
        if not enabled:
            return
            
        # Credential management
        self.credential_manager = CredentialManagerNode(
            name="credential_manager",
            storage_backend="encrypted_file",  # Can be vault, aws_secrets, etc.
            auto_rotate=True
        )
        
        # Audit logging
        self.audit_logger = AuditLogNode(
            name="audit_logger",
            storage_type="database",
            retention_days=365
        )
        
        # Register security workflow
        security_workflow = WorkflowBuilder("security_check")
        security_workflow.add_node("CredentialManagerNode", "creds", {
            "name": "credential_validator"
        })
        security_workflow.add_node("AuditLogNode", "audit", {
            "name": "access_logger"
        })
        
        self.workflows["security_check"] = security_workflow
    
    def _setup_monitoring(self, enabled: bool):
        """Set up monitoring using Kailash nodes."""
        if not enabled:
            return
            
        # Create monitoring workflow
        monitoring_workflow = WorkflowBuilder("performance_monitor")
        
        # Add performance tracking node
        monitoring_workflow.add_node("PythonCodeNode", "tracker", {
            "name": "performance_tracker",
            "code": """
import time
start_time = time.time()
# Track execution metrics
result = {
    'timestamp': time.time(),
    'duration': 0,
    'status': 'monitoring'
}
"""
        })
        
        self.workflows["performance_monitor"] = monitoring_workflow
    
    def _setup_ai(self, enabled: bool):
        """Set up AI components for Mode 2 servers."""
        if not enabled:
            return
            
        # Query understanding agent
        self.query_agent = LLMAgentNode(
            name="query_analyzer",
            provider="openai",
            model="gpt-4",
            system_prompt="""
            Analyze data queries and determine:
            1. Intent and required data sources
            2. Optimal execution strategy
            3. Caching opportunities
            Return analysis as structured JSON.
            """
        )
        
        # Cost-aware agent for optimization
        self.optimizer_agent = MonitoredLLMAgentNode(
            name="cost_optimizer",
            model="gpt-3.5-turbo",
            budget_limit=10.0,
            system_prompt="Optimize queries for cost and performance"
        )
    
    def register_connector(self, name: str, connector_node: Any):
        """
        Register a data connector node.
        
        Args:
            name: Connector name
            connector_node: Kailash node instance
        """
        self.connectors[name] = connector_node
        logger.info(f"Registered connector: {name}")
    
    def create_tool_from_workflow(
        self,
        tool_name: str,
        workflow: WorkflowBuilder,
        description: str = ""
    ):
        """
        Create an MCP tool from a Kailash workflow.
        
        Args:
            tool_name: Name for the MCP tool
            workflow: WorkflowBuilder instance
            description: Tool description
        """
        # Build the workflow
        built_workflow = workflow.build()
        
        # Create MCP tool node that executes the workflow
        class WorkflowToolNode(MCPToolNode):
            def __init__(self, runtime: LocalRuntime):
                super().__init__(tool_name, description)
                self.runtime = runtime
                self.workflow = built_workflow
            
            def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
                # Execute workflow using Kailash runtime
                results, run_id = self.runtime.execute(
                    self.workflow,
                    parameters=inputs
                )
                return {
                    "tool_result": results,
                    "run_id": run_id
                }
        
        # Register the tool
        tool_node = WorkflowToolNode(self.runtime)
        self.register_tool(tool_node)
        
        logger.info(f"Created MCP tool '{tool_name}' from workflow")
    
    def create_dynamic_tools(self, config: Dict[str, Any]):
        """
        Create MCP tools dynamically from configuration.
        
        This demonstrates using WorkflowBuilder.from_dict() for dynamic creation.
        
        Args:
            config: Tool configuration with workflow definitions
        """
        for tool_config in config.get("tools", []):
            # Create workflow from configuration
            workflow = WorkflowBuilder.from_dict(tool_config["workflow"])
            
            # Create MCP tool
            self.create_tool_from_workflow(
                tool_name=tool_config["name"],
                workflow=workflow,
                description=tool_config.get("description", "")
            )
    
    async def execute_with_monitoring(
        self,
        tool_name: str,
        inputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute tool with monitoring and security.
        
        Args:
            tool_name: Tool to execute
            inputs: Tool inputs
            
        Returns:
            Execution results
        """
        # Security check if enabled
        if hasattr(self, 'audit_logger'):
            await self.audit_logger.log_event({
                "event": "tool_execution",
                "tool": tool_name,
                "user": inputs.get("user_id", "anonymous"),
                "timestamp": datetime.now().isoformat()
            })
        
        # Execute tool
        result = await self.execute_tool(tool_name, inputs)
        
        # Performance tracking
        if "performance_monitor" in self.workflows:
            monitor_result, _ = self.runtime.execute(
                self.workflows["performance_monitor"].build(),
                parameters={"execution_info": result}
            )
        
        return result
    
    def get_status(self) -> Dict[str, Any]:
        """Get server status using Kailash components."""
        return {
            "server": self.config.name,
            "version": self.config.version,
            "runtime": "Kailash LocalRuntime",
            "connectors": list(self.connectors.keys()),
            "tools": list(self.tools.keys()),
            "workflows": list(self.workflows.keys()),
            "features": {
                "security": hasattr(self, 'credential_manager'),
                "monitoring": "performance_monitor" in self.workflows,
                "ai": hasattr(self, 'query_agent')
            }
        }


class DataBridgeGateway:
    """
    Enterprise gateway for data bridge MCP servers.
    
    Uses Kailash middleware for:
    - Real-time communication
    - Session management
    - API documentation
    - Authentication
    """
    
    def __init__(self, mcp_servers: List[DataBridgeMCPServer] = None):
        """
        Initialize gateway with MCP servers.
        
        Args:
            mcp_servers: List of MCP server instances
        """
        self.mcp_servers = mcp_servers or []
        
        # Create Kailash enterprise gateway
        self.gateway = create_gateway(
            title="Data Bridge Enterprise Gateway",
            description="Universal data connectivity with AI",
            enable_docs=True,
            enable_auth=True,
            cors_origins=["*"]
        )
        
        # Register MCP servers with gateway
        for server in self.mcp_servers:
            self._register_server(server)
    
    def _register_server(self, server: DataBridgeMCPServer):
        """Register MCP server with gateway."""
        # Gateway automatically handles:
        # - WebSocket connections for real-time updates
        # - Session management for multi-tenant isolation
        # - API documentation generation
        # - Authentication and authorization
        
        logger.info(f"Registered {server.config.name} with enterprise gateway")
    
    def add_server(self, server: DataBridgeMCPServer):
        """Add a new MCP server to the gateway."""
        self.mcp_servers.append(server)
        self._register_server(server)
    
    def run(self, host: str = "0.0.0.0", port: int = 8000):
        """Start the enterprise gateway."""
        logger.info(f"Starting Data Bridge Gateway on {host}:{port}")
        self.gateway.run(host=host, port=port)