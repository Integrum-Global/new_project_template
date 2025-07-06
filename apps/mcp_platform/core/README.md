# MCP Application - Model Context Protocol Management System

A comprehensive, production-ready application for managing Model Context Protocol (MCP) servers, tools, and integrations built with the Kailash SDK.

## Overview

This application demonstrates enterprise-grade MCP management with:
- Complete MCP server lifecycle management
- Tool discovery and execution orchestration
- Multi-transport support (STDIO, HTTP, SSE)
- Authentication and authorization for MCP access
- Resource management and caching
- Real-time monitoring and metrics
- Production-ready deployment configurations

## Features

### Core Capabilities
- **MCP Server Management**: Create, configure, and manage MCP servers
- **Tool Registry**: Discover, catalog, and execute MCP tools
- **Resource Management**: Handle MCP resources with caching and optimization
- **Transport Layer**: Support for multiple transport protocols
- **Security**: Authentication, authorization, and secure tool execution
- **Monitoring**: Real-time metrics, health checks, and audit logging

### Enterprise Features
- **Multi-tenancy**: Isolated MCP environments per organization
- **High Availability**: Failover and load balancing for MCP servers
- **Compliance**: Audit trails and security event logging
- **Integration**: REST APIs, webhooks, and event streaming
- **Scalability**: Horizontal scaling with distributed caching

## Architecture

```
mcp/
├── core/                      # Core business logic
│   ├── gateway.py            # Main MCP orchestrator
│   ├── models.py             # MCP data models
│   ├── services.py           # Business services
│   ├── registry.py           # Tool and server registry
│   └── security.py           # Security and auth
│
├── services/                  # Service layer
│   ├── mcp/                  # MCP-specific services
│   │   ├── server_manager.py # Server lifecycle management
│   │   ├── tool_executor.py  # Tool execution engine
│   │   ├── resource_handler.py # Resource management
│   │   └── transport/        # Transport implementations
│   ├── discovery/            # Service discovery
│   ├── monitoring/           # Metrics and monitoring
│   └── cache/               # Caching services
│
├── api/                      # API endpoints
│   ├── servers_api.py       # MCP server management
│   ├── tools_api.py         # Tool discovery and execution
│   ├── resources_api.py     # Resource management
│   ├── admin_api.py         # Administrative endpoints
│   └── webhooks_api.py      # Event webhooks
│
├── nodes/                    # Custom Kailash nodes
│   ├── mcp_server_node.py   # MCP server management node
│   ├── tool_executor_node.py # Tool execution node
│   ├── discovery_node.py    # Service discovery node
│   └── monitor_node.py      # Monitoring node
│
├── workflows/                # MCP workflows
│   ├── server_workflows.py  # Server lifecycle workflows
│   ├── tool_workflows.py    # Tool execution workflows
│   ├── discovery_workflows.py # Discovery workflows
│   └── admin_workflows.py   # Administrative workflows
│
├── tests/                    # Comprehensive tests
│   ├── unit/                # Unit tests
│   ├── integration/         # Integration tests
│   ├── e2e/                 # End-to-end tests
│   └── performance/         # Performance tests
│
├── config/                   # Configuration
│   ├── settings.py          # Application settings
│   ├── mcp_servers.yaml     # Server configurations
│   └── security.yaml        # Security policies
│
├── examples/                 # Usage examples
│   ├── basic_server.py      # Basic MCP server
│   ├── tool_execution.py    # Tool execution examples
│   ├── multi_transport.py   # Multi-transport setup
│   └── production_setup.py  # Production configuration
│
└── docs/                    # Documentation
    ├── architecture/        # Architecture decisions
    ├── api/                 # API documentation
    ├── deployment/          # Deployment guides
    └── tutorials/           # Step-by-step tutorials
```

## Quick Start

### Installation

```bash
# Clone and navigate to the MCP app
cd apps/mcp

# Install in development mode
pip install -e .

# Install test dependencies
pip install -r requirements-test.txt
```

### Basic Usage

```python
from mcp.core.gateway import MCPGateway
from kailash.runtime.local import LocalRuntime

# Initialize the MCP gateway
gateway = MCPGateway()
runtime = LocalRuntime()

# Create an MCP server
server_config = {
    "name": "data-tools",
    "transport": "stdio",
    "command": "python",
    "args": ["-m", "data_tools_server"]
}

# Register the server
server_id = await gateway.register_server(server_config)

# Discover available tools
tools = await gateway.discover_tools(server_id)
print(f"Discovered {len(tools)} tools")

# Execute a tool
result = await gateway.execute_tool(
    server_id,
    "search_data",
    {"query": "customer orders"}
)
```

### API Usage

```bash
# Start the MCP application
python main.py

# The API will be available at http://localhost:8000
```

#### Register an MCP Server
```bash
curl -X POST http://localhost:8000/api/v1/servers \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "analytics-server",
    "transport": "http",
    "url": "http://analytics:8080",
    "auth": {
      "type": "bearer",
      "token": "server-token"
    }
  }'
```

#### Discover Tools
```bash
curl http://localhost:8000/api/v1/servers/{server_id}/tools \
  -H "Authorization: Bearer $TOKEN"
```

#### Execute a Tool
```bash
curl -X POST http://localhost:8000/api/v1/tools/execute \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "server_id": "analytics-server",
    "tool_name": "analyze_sales",
    "parameters": {
      "date_range": "last_30_days",
      "metrics": ["revenue", "orders"]
    }
  }'
```

## Workflows

### Server Lifecycle Management

```python
from mcp.workflows.server_workflows import ServerWorkflows
from kailash.runtime.local import LocalRuntime

workflows = ServerWorkflows()
runtime = LocalRuntime()

# Create server deployment workflow
workflow = workflows.create_server_deployment_workflow()

# Execute deployment
result = await runtime.execute_async(workflow, {
    "server_config": {
        "name": "production-server",
        "transport": "http",
        "url": "https://mcp.example.com",
        "replicas": 3,
        "health_check": {
            "endpoint": "/health",
            "interval": 30
        }
    }
})
```

### Tool Discovery and Cataloging

```python
from mcp.workflows.discovery_workflows import DiscoveryWorkflows

workflows = DiscoveryWorkflows()

# Create discovery workflow
workflow = workflows.create_tool_discovery_workflow()

# Discover and catalog tools
result = await runtime.execute_async(workflow, {
    "servers": ["server1", "server2", "server3"],
    "catalog_config": {
        "index_descriptions": True,
        "generate_embeddings": True,
        "cache_results": True
    }
})
```

## Custom Nodes

### MCP Server Node

```python
from mcp.nodes.mcp_server_node import MCPServerNode

# Create and configure the node
node = MCPServerNode({
    "transport": "stdio",
    "command": "python",
    "args": ["-m", "custom_server"]
})

# Execute server operations
result = await node.execute({
    "operation": "start_server",
    "config": {
        "name": "custom-tools",
        "environment": {"API_KEY": "secret"}
    }
})
```

### Tool Executor Node

```python
from mcp.nodes.tool_executor_node import ToolExecutorNode

# Create executor node
executor = ToolExecutorNode({
    "timeout": 120,
    "retry_attempts": 3,
    "cache_results": True
})

# Execute a tool
result = await executor.execute({
    "server_id": "data-server",
    "tool_name": "query_database",
    "parameters": {
        "query": "SELECT * FROM orders LIMIT 10"
    }
})
```

## Configuration

### Application Settings (config/settings.py)

```python
class MCPConfig:
    # Server defaults
    DEFAULT_TIMEOUT = 30
    MAX_CONCURRENT_SERVERS = 50

    # Transport settings
    STDIO_BUFFER_SIZE = 8192
    HTTP_CONNECTION_POOL_SIZE = 100

    # Security
    REQUIRE_AUTHENTICATION = True
    ALLOWED_COMMANDS = ["mcp-server", "python", "node"]

    # Caching
    CACHE_TTL = 3600
    CACHE_MAX_SIZE = 1000

    # Monitoring
    METRICS_ENABLED = True
    METRICS_INTERVAL = 60
```

### MCP Server Configuration (config/mcp_servers.yaml)

```yaml
servers:
  - name: filesystem
    transport: stdio
    command: npx
    args: ["@modelcontextprotocol/server-filesystem", "/data"]
    auto_start: true

  - name: database
    transport: stdio
    command: mcp-server-sqlite
    args: ["--db-path", "database.db"]
    environment:
      LOG_LEVEL: info

  - name: api-gateway
    transport: http
    url: https://api.example.com/mcp
    auth:
      type: oauth2
      client_id: ${OAUTH_CLIENT_ID}
      client_secret: ${OAUTH_CLIENT_SECRET}
```

## Testing

### Run All Tests
```bash
# Unit tests
pytest tests/unit/

# Integration tests
pytest tests/integration/

# End-to-end tests
pytest tests/e2e/

# Performance tests
pytest tests/performance/

# All tests with coverage
pytest tests/ --cov=mcp --cov-report=html
```

### Test Categories

1. **Unit Tests**: Component-level testing
   - Node functionality
   - Service methods
   - Utility functions

2. **Integration Tests**: Service integration
   - MCP server connections
   - Tool execution flows
   - Cache and database integration

3. **E2E Tests**: Complete workflows
   - Server deployment scenarios
   - Tool discovery and execution
   - Multi-server orchestration

4. **Performance Tests**: Load and stress testing
   - Concurrent server handling
   - Tool execution throughput
   - Resource usage optimization

## Deployment

### Docker Deployment

```bash
# Build the image
docker build -t mcp-app .

# Run with docker-compose
docker-compose up -d
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mcp-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: mcp-app
  template:
    metadata:
      labels:
        app: mcp-app
    spec:
      containers:
      - name: mcp-app
        image: mcp-app:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: mcp-secrets
              key: database-url
```

## Security

### Authentication
- API key authentication for basic access
- OAuth2 for enterprise integrations
- JWT tokens for session management

### Authorization
- Role-based access control (RBAC)
- Resource-level permissions
- Tool execution policies

### Security Policies
```yaml
# config/security.yaml
policies:
  tool_execution:
    - name: require_approval
      tools: ["delete_*", "update_*"]
      approval_required: true

    - name: rate_limit
      tools: ["*"]
      max_calls_per_minute: 100

  server_access:
    - name: production_servers
      servers: ["prod-*"]
      allowed_roles: ["admin", "operator"]
```

## Monitoring

### Metrics
- Server availability and health
- Tool execution performance
- Resource utilization
- Error rates and patterns

### Dashboards
- Real-time server status
- Tool usage analytics
- Performance trends
- Security events

### Alerts
- Server downtime
- Tool execution failures
- Security violations
- Resource exhaustion

## Best Practices

1. **Server Management**
   - Use health checks for all servers
   - Implement proper timeout handling
   - Monitor resource usage
   - Regular server rotation

2. **Tool Execution**
   - Validate all tool inputs
   - Implement rate limiting
   - Cache frequently used results
   - Handle errors gracefully

3. **Security**
   - Authenticate all API calls
   - Authorize tool execution
   - Audit all operations
   - Encrypt sensitive data

4. **Performance**
   - Use connection pooling
   - Implement caching strategies
   - Optimize tool discovery
   - Monitor execution times

## Contributing

1. Follow the code style guidelines
2. Write comprehensive tests
3. Update documentation
4. Submit pull requests

## License

This application is part of the Kailash SDK and follows the same licensing terms.

## Support

- Documentation: [docs/](docs/)
- Issues: GitHub Issues
- Community: Discord/Slack

---

*Built with Kailash SDK - Enterprise-grade MCP management*
