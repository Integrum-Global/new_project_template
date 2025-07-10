# Nexus Architecture

## Technical Design of the Unified Orchestration Platform

This document provides a comprehensive technical overview of Kailash Nexus architecture, detailing how it unifies API, CLI, and MCP interfaces through a single orchestration platform built entirely on Kailash SDK components.

## 🏗️ High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Client Layer                                 │
├─────────────┬──────────────┬──────────────┬───────────────────────┤
│   Web App   │  CLI Tools   │  MCP Clients │   Custom Integrations │
└──────┬──────┴──────┬───────┴──────┬───────┴───────────┬───────────┘
       │             │              │                    │
       ▼             ▼              ▼                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         Nexus Gateway                                │
├─────────────┬──────────────┬──────────────┬───────────────────────┤
│ API Channel │  CLI Channel │  MCP Channel │   Extension Channels   │
├─────────────┴──────────────┴──────────────┴───────────────────────┤
│                    Channel Manager                                   │
├─────────────────────────────────────────────────────────────────────┤
│                 Unified Orchestration Layer                          │
├──────────────┬──────────────┬──────────────┬──────────────────────┤
│   Session    │    Event     │   Workflow   │     Security         │
│ Orchestrator │    Router    │   Executor   │     Manager          │
├──────────────┴──────────────┴──────────────┴──────────────────────┤
│                  Core Services Layer                                 │
├──────────────┬──────────────┬──────────────┬──────────────────────┤
│   Resource   │   Monitoring │     Data     │   Integration        │
│   Registry   │   & Metrics  │   Persistence│     Adapters         │
├──────────────┴──────────────┴──────────────┴──────────────────────┤
│                    Kailash SDK Foundation                           │
├──────────────────────────────────────────────────────────────────────┤
│  Runtime │ Nodes │ Workflows │ Middleware │ Access Control         │
└──────────────────────────────────────────────────────────────────────┘
```

## 📦 Core Components

### 1. Nexus Gateway

The central entry point that coordinates all channels and services:

```python
class NexusGateway:
    """
    Central orchestration hub for all Nexus operations.

    Built on:
    - kailash.middleware.APIGateway
    - kailash.gateway.enhanced_gateway.EnhancedDurableAPIGateway
    """

    def __init__(self, config: NexusConfig):
        # Initialize base gateway
        self.base_gateway = create_gateway(
            title=config.title,
            enable_docs=config.enable_docs,
            enable_auth=config.enable_auth,
            database_url=config.database_url
        )

        # Initialize channel manager
        self.channel_manager = ChannelManager()

        # Setup core services
        self.session_orchestrator = SessionOrchestrator()
        self.event_router = EventRouter()
        self.workflow_executor = WorkflowExecutor()

        # Register default channels
        self._register_default_channels()
```

### 2. Channel Architecture

Each interface type is abstracted as a channel with common interfaces:

```python
class Channel(ABC):
    """Base channel interface."""

    @abstractmethod
    async def initialize(self, nexus: NexusGateway):
        """Initialize channel with nexus reference."""

    @abstractmethod
    async def handle_request(self, request: ChannelRequest) -> ChannelResponse:
        """Handle incoming request."""

    @abstractmethod
    async def emit_event(self, event: NexusEvent):
        """Emit event to channel subscribers."""

    @abstractmethod
    async def get_capabilities(self) -> List[Capability]:
        """Return channel capabilities."""
```

#### API Channel

Handles REST, GraphQL, WebSocket, and SSE:

```python
class APIChannel(Channel):
    """
    REST API and real-time communication channel.

    Components:
    - HTTPRequestNode for REST endpoints
    - GraphQLNode for GraphQL queries
    - WebSocketNode for real-time bidirectional
    - SSENode for server-sent events
    """

    def __init__(self):
        self.rest_handler = RESTHandler()
        self.websocket_handler = WebSocketHandler()
        self.sse_handler = SSEHandler()
        self.graphql_handler = GraphQLHandler()

    async def initialize(self, nexus: NexusGateway):
        # Register routes
        nexus.base_gateway.add_api_route(
            "/api/{path:path}",
            self.handle_api_request,
            methods=["GET", "POST", "PUT", "DELETE", "PATCH"]
        )

        # WebSocket endpoint
        nexus.base_gateway.websocket("/ws")(self.handle_websocket)

        # SSE endpoint
        nexus.base_gateway.get("/events")(self.handle_sse)
```

#### CLI Channel

Provides command-line interface with workflow execution:

```python
class CLIChannel(Channel):
    """
    Command-line interface channel.

    Components:
    - CommandParserNode for parsing CLI commands
    - InteractiveShellNode for REPL interface
    - BatchExecutorNode for script execution
    - ProgressDisplayNode for real-time updates
    """

    def __init__(self):
        self.command_registry = CommandRegistry()
        self.shell = InteractiveShell()
        self.batch_executor = BatchExecutor()

    async def register_commands(self, nexus: NexusGateway):
        # Auto-discover commands from workflows
        workflows = await nexus.workflow_executor.list_workflows()
        for workflow in workflows:
            self.command_registry.register(
                WorkflowCommand(workflow)
            )
```

#### MCP Channel

Integrates Model Context Protocol for AI agents and tools:

```python
class MCPChannel(Channel):
    """
    Model Context Protocol channel.

    Components:
    - MCPServerNode for tool/resource serving
    - MCPClientNode for external service integration
    - ServiceDiscoveryNode for dynamic discovery
    - CapabilityRegistryNode for capability management
    """

    def __init__(self):
        self.mcp_server = MiddlewareMCPServer()
        self.service_registry = ServiceRegistry()
        self.capability_manager = CapabilityManager()

    async def expose_tools(self, nexus: NexusGateway):
        # Expose workflows as MCP tools
        for workflow in await nexus.workflow_executor.list_workflows():
            tool = WorkflowTool(workflow)
            await self.mcp_server.register_tool(tool)
```

### 3. Unified Orchestration Layer

Core services that work across all channels:

#### Session Orchestrator

Manages sessions that persist across channels:

```python
class SessionOrchestrator:
    """
    Unified session management across channels.

    Built on:
    - kailash.middleware.core.agent_ui.AgentUIMiddleware
    - kailash.nodes.auth.session_management.SessionManagementNode
    """

    def __init__(self):
        self.agent_ui = AgentUIMiddleware(
            enable_persistence=True,
            enable_auth=True
        )
        self.session_node = SessionManagementNode()

    async def create_session(self, user_id: str, channel: str) -> Session:
        # Create unified session
        session_id = await self.agent_ui.create_session(user_id)

        # Track channel association
        session = Session(
            id=session_id,
            user_id=user_id,
            channels={channel},
            created_at=datetime.utcnow()
        )

        # Enable cross-channel access
        await self._enable_cross_channel(session)

        return session

    async def get_session(self, token: str) -> Optional[Session]:
        """Retrieve session from any channel token."""
        # Works with JWT, CLI tokens, MCP auth
        return await self.agent_ui.get_session_by_token(token)
```

#### Event Router

Distributes events across all channels:

```python
class EventRouter:
    """
    Cross-channel event distribution system.

    Built on:
    - kailash.middleware.communication.events.EventStream
    - kailash.nodes.streaming.EventStreamNode
    """

    def __init__(self):
        self.event_stream = EventStream()
        self.subscriptions = defaultdict(list)

    async def publish(self, event: NexusEvent):
        """Publish event to all interested channels."""
        # Add metadata
        event.timestamp = datetime.utcnow()
        event.source_channel = self.current_channel

        # Route to subscribers
        for channel in self.subscriptions[event.type]:
            await channel.emit_event(event)

        # Persist for audit
        await self.event_stream.publish(event)

    async def subscribe(self, channel: Channel, event_types: List[str]):
        """Subscribe channel to event types."""
        for event_type in event_types:
            self.subscriptions[event_type].append(channel)
```

#### Workflow Executor

Executes workflows from any channel:

```python
class WorkflowExecutor:
    """
    Channel-agnostic workflow execution.

    Built on:
    - kailash.runtime.local.LocalRuntime
    - kailash.workflow.builder.WorkflowBuilder
    """

    def __init__(self):
        self.runtime = LocalRuntime()
        self.workflow_registry = {}

    async def execute(self,
                     workflow_id: str,
                     inputs: Dict,
                     session: Session) -> ExecutionResult:
        """Execute workflow with session context."""
        # Get workflow
        workflow = self.workflow_registry[workflow_id]

        # Add session context
        enriched_inputs = {
            **inputs,
            "_session": session,
            "_channel": session.current_channel
        }

        # Execute with monitoring
        with self.monitor_execution(workflow_id, session):
            results, run_id = await self.runtime.execute_async(
                workflow,
                inputs=enriched_inputs
            )

        return ExecutionResult(
            run_id=run_id,
            results=results,
            session_id=session.id
        )
```

### 4. Security Architecture

Unified security across all channels:

```python
class SecurityManager:
    """
    Enterprise security management.

    Components:
    - JWTAuthNode for token management
    - PermissionCheckNode for authorization
    - AuditLogNode for compliance logging
    - RateLimitNode for API protection
    """

    def __init__(self, config: SecurityConfig):
        self.auth_manager = KailashJWTAuth(config.jwt_config)
        self.access_control = AccessControlManager(
            strategy=config.access_strategy  # "rbac", "abac", or "hybrid"
        )
        self.audit_logger = AuditLogNode()

    async def authenticate(self, credentials: Dict, channel: str) -> AuthResult:
        """Authenticate across any channel."""
        # Channel-specific auth methods
        if channel == "api":
            return await self._auth_jwt(credentials)
        elif channel == "cli":
            return await self._auth_cli_token(credentials)
        elif channel == "mcp":
            return await self._auth_mcp_bearer(credentials)

    async def authorize(self, session: Session, resource: str, action: str) -> bool:
        """Unified authorization check."""
        return await self.access_control.check_permission(
            user_id=session.user_id,
            resource=resource,
            action=action,
            context={
                "channel": session.current_channel,
                "tenant_id": session.tenant_id
            }
        )
```

### 5. Data Persistence Layer

Unified data management:

```python
class DataPersistence:
    """
    Multi-backend data persistence.

    Built on:
    - AsyncSQLDatabaseNode for relational data
    - AsyncPostgreSQLVectorNode for embeddings
    - RedisNode for caching
    - S3Node for object storage
    """

    def __init__(self, config: DataConfig):
        # Primary database
        self.primary_db = AsyncSQLDatabaseNode(
            connection_string=config.database_url,
            pool_size=config.pool_size
        )

        # Vector database for AI/search
        self.vector_db = AsyncPostgreSQLVectorNode(
            connection_string=config.vector_db_url
        )

        # Cache layer
        self.cache = RedisNode(
            connection_string=config.redis_url
        )

        # Object storage
        self.object_store = S3Node(
            bucket=config.s3_bucket,
            region=config.aws_region
        )
```

## 🔄 Request Flow

Here's how a request flows through Nexus:

### 1. API Request Flow
```
Client → API Channel → Auth Middleware → Session Orchestrator
    → Workflow Executor → Business Logic → Response Formatter
    → Event Router → Other Channels → Client Response
```

### 2. CLI Command Flow
```
Terminal → CLI Channel → Command Parser → Session Validation
    → Workflow Executor → Progress Updates → Event Router
    → API/MCP Channels → Terminal Output
```

### 3. MCP Tool Invocation Flow
```
AI Agent → MCP Channel → Tool Discovery → Capability Check
    → Session Context → Workflow Executor → Result Transform
    → Event Router → Monitoring → AI Agent Response
```

## 🎯 Key Design Patterns

### 1. Channel Abstraction Pattern

All interfaces implement the same `Channel` interface, enabling:
- Uniform request handling
- Cross-channel event propagation
- Consistent security enforcement
- Shared session management

### 2. Event Sourcing Pattern

All actions produce events that:
- Create audit trails
- Enable real-time updates
- Support debugging
- Allow replay and recovery

### 3. Workflow-Centric Pattern

Business logic lives in workflows that:
- Execute identically across channels
- Provide consistent behavior
- Enable visual debugging
- Support composition

### 4. Progressive Enhancement Pattern

Start simple and add complexity:
- Development: In-memory, no auth
- Staging: Database, basic auth
- Production: Full features
- Enterprise: Custom extensions

## 🔐 Security Architecture

### Multi-Layer Security
1. **Channel Security**: Each channel has specific auth methods
2. **Session Security**: Unified session validation
3. **Workflow Security**: Permission checks in workflows
4. **Data Security**: Encryption at rest and in transit
5. **Audit Security**: Comprehensive logging

### Security Flow
```
Request → Channel Auth → Session Validation → Permission Check
    → Workflow Auth → Data Access Control → Audit Logging
    → Response Filtering → Channel Response
```

## 📊 Monitoring & Observability

### Unified Metrics
```python
class NexusMonitoring:
    """Comprehensive monitoring across channels."""

    def __init__(self):
        self.metrics = {
            "requests_total": Counter('nexus_requests_total', 'Total requests', ['channel', 'method']),
            "request_duration": Histogram('nexus_request_duration', 'Request duration', ['channel']),
            "active_sessions": Gauge('nexus_active_sessions', 'Active sessions', ['channel']),
            "workflow_executions": Counter('nexus_workflow_executions', 'Workflow executions', ['workflow', 'channel']),
            "errors": Counter('nexus_errors', 'Errors', ['channel', 'type'])
        }
```

### Health Checks
- Channel health: Each channel reports status
- Service health: Core services monitored
- Dependency health: External services checked
- Resource health: CPU, memory, connections

## 🚀 Scaling Architecture

### Horizontal Scaling
- Stateless channels enable easy scaling
- Session affinity for WebSocket connections
- Distributed event bus for multi-instance
- Shared cache for performance

### Vertical Scaling
- Connection pooling optimization
- Batch processing for bulk operations
- Async execution throughout
- Resource limits per tenant

## 🔧 Extension Points

### Custom Channels
```python
class VoiceChannel(Channel):
    """Example custom channel for voice interfaces."""

    async def handle_request(self, request: ChannelRequest):
        # Speech to text
        text = await self.speech_to_text(request.audio)

        # Natural language processing
        intent = await self.nlu.process(text)

        # Execute workflow
        result = await self.nexus.workflow_executor.execute(
            intent.workflow,
            intent.parameters
        )

        # Text to speech
        audio = await self.text_to_speech(result.message)

        return ChannelResponse(audio=audio)
```

### Custom Services
- Authentication providers
- Storage backends
- Monitoring integrations
- Workflow templates

## 📋 Configuration Architecture

### Hierarchical Configuration
```yaml
nexus:
  # Global settings
  title: "Enterprise Nexus"
  environment: "production"

  # Channel-specific settings
  channels:
    api:
      rate_limit: 1000
      cors_origins: ["https://app.company.com"]

    cli:
      idle_timeout: 300
      history_size: 1000

    mcp:
      service_discovery: true
      capability_caching: true

  # Service settings
  services:
    security:
      strategy: "hybrid"  # rbac + abac
      session_timeout: 3600

    monitoring:
      export_interval: 60
      retention_days: 90
```

## 🏁 Summary

Kailash Nexus architecture provides:

1. **Unified Platform**: Single orchestration layer for all interfaces
2. **Channel Abstraction**: Clean separation of interface concerns
3. **Event-Driven Core**: Real-time synchronization across channels
4. **SDK Foundation**: 100% Kailash SDK components
5. **Enterprise Ready**: Security, monitoring, and scaling built-in
6. **Extensible Design**: Easy to add new channels and services

The architecture enables building complex, multi-interface applications while maintaining simplicity, consistency, and reliability across all channels.

---

**Next Steps:** Explore the [User Guide](USER_GUIDE.md) for practical examples or dive into [Under the Hood](UNDER_THE_HOOD.md) for implementation details.
