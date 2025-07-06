# MCP Platform - Unified Model Context Protocol Infrastructure

**Type**: Core Infrastructure Platform
**Purpose**: Enterprise-grade MCP server management, gateway, and tooling
**Status**: Production-ready consolidated platform

## Overview

The MCP Platform is the unified infrastructure for Model Context Protocol (MCP) in the Kailash SDK ecosystem. It consolidates all MCP infrastructure components into a single, well-organized platform.

## Architecture

```
mcp_platform/
├── core/           # Core MCP server management and orchestration
├── gateway/        # Enterprise gateway with multi-tenancy and routing
├── tools/          # MCP tool servers and implementations
├── examples/       # Integration patterns and example code
└── deployment/     # Unified deployment configurations
```

### Core Components

#### 1. Core Management (`core/`)
- **MCP Server Lifecycle**: Create, configure, and manage MCP servers
- **Tool Registry**: Discover, catalog, and execute MCP tools
- **Resource Management**: Handle MCP resources with caching
- **Service Discovery**: Automatic MCP server discovery
- **Monitoring**: Real-time metrics and health checks

#### 2. Enterprise Gateway (`gateway/`)
- **Multi-tenancy**: Isolated MCP environments per organization
- **Authentication**: Enterprise auth with JWT, OAuth2, SAML
- **Authorization**: Fine-grained access control for MCP resources
- **Routing**: Intelligent request routing to MCP servers
- **Audit Logging**: Comprehensive audit trails

#### 3. Tool Servers (`tools/`)
- **Basic Server**: Simple MCP server implementation
- **Production Server**: High-performance server with all features
- **Tool Implementations**: Various MCP tool examples
- **Client Libraries**: Python clients for MCP interaction

#### 4. Examples (`examples/`)
- **Integration Patterns**: Common MCP integration scenarios
- **Client Examples**: How to connect to MCP servers
- **Workflow Integration**: Using MCP with Kailash workflows
- **Advanced Patterns**: Streaming, distributed agents, etc.

## Quick Start

### 1. Running the Core Platform

```bash
# Start the MCP management platform
cd apps/mcp_platform/core
python main.py

# API will be available at http://localhost:8000
```

### 2. Running the Enterprise Gateway

```bash
# Start the enterprise gateway
cd apps/mcp_platform/gateway
python -m gateway.core.server

# Gateway will be available at http://localhost:8080
```

### 3. Running a Tool Server

```bash
# Start a basic MCP tool server
cd apps/mcp_platform/tools
python servers/basic_server.py

# Or start the production server
python servers/production_server.py
```

## API Overview

### Core Management APIs

```python
# Server management
POST   /api/v1/servers              # Create MCP server
GET    /api/v1/servers              # List servers
GET    /api/v1/servers/{id}         # Get server details
PUT    /api/v1/servers/{id}         # Update server
DELETE /api/v1/servers/{id}         # Delete server

# Tool management
GET    /api/v1/tools                # List available tools
POST   /api/v1/tools/execute        # Execute a tool
GET    /api/v1/tools/{id}/schema    # Get tool schema

# Resource management
GET    /api/v1/resources            # List resources
GET    /api/v1/resources/{uri}      # Get resource content
```

### Gateway APIs

```python
# Authentication
POST   /api/v1/auth/login           # Login
POST   /api/v1/auth/refresh         # Refresh token
POST   /api/v1/auth/logout          # Logout

# Tenant management
GET    /api/v1/tenants              # List tenants
POST   /api/v1/tenants              # Create tenant
GET    /api/v1/tenants/{id}         # Get tenant details

# Routing
POST   /api/v1/route                # Route MCP request
GET    /api/v1/routes               # List routing rules
```

## Configuration

### Environment Variables

```bash
# Core configuration
MCP_PLATFORM_HOST=0.0.0.0
MCP_PLATFORM_PORT=8000
MCP_PLATFORM_LOG_LEVEL=INFO

# Database
DATABASE_URL=postgresql://user:pass@localhost/mcp_platform

# Redis (for caching)
REDIS_URL=redis://localhost:6379

# Gateway configuration
GATEWAY_HOST=0.0.0.0
GATEWAY_PORT=8080
GATEWAY_AUTH_SECRET=your-secret-key

# Multi-tenancy
ENABLE_MULTI_TENANCY=true
DEFAULT_TENANT_ID=default
```

### Configuration Files

- `config/settings.py` - Core platform settings
- `gateway/config.yaml` - Gateway configuration
- `tools/server_config.json` - Tool server configuration

## Deployment

### Docker Deployment

```bash
# Build and run with Docker Compose
cd apps/mcp_platform/deployment
docker-compose up -d

# Services will be available at:
# - Core API: http://localhost:8000
# - Gateway: http://localhost:8080
# - Tool Server: http://localhost:8090
```

### Kubernetes Deployment

```bash
# Deploy to Kubernetes
kubectl apply -f deployment/kubernetes/

# Configure ingress for external access
kubectl apply -f deployment/kubernetes/ingress.yaml
```

### Production Considerations

1. **High Availability**: Deploy multiple instances with load balancing
2. **Database**: Use managed PostgreSQL with replication
3. **Caching**: Use Redis cluster for distributed caching
4. **Monitoring**: Integrate with Prometheus/Grafana
5. **Security**: Enable TLS, implement rate limiting

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run specific component tests
pytest core/tests/
pytest gateway/tests/
pytest tools/tests/

# Run with coverage
pytest --cov=mcp_platform
```

### Adding New Tools

1. Create tool implementation in `tools/implementations/`
2. Register tool in `core/registry.py`
3. Add tests in `tools/tests/`
4. Update documentation

### Extending the Gateway

1. Add new routes in `gateway/routing/`
2. Implement middleware in `gateway/middleware/`
3. Add authentication providers in `gateway/auth/`
4. Test with `gateway/tests/`

## Integration Examples

### With Kailash Workflows

```python
from kailash import LocalRuntime, WorkflowBuilder
from mcp_platform.core import MCPClient

# Create MCP client
mcp = MCPClient("http://localhost:8000")

# Create workflow that uses MCP tools
wf = WorkflowBuilder("mcp-workflow")
wf.add_node("MCPToolNode", "analyzer", {
    "tool_name": "code_analyzer",
    "mcp_client": mcp
})

# Execute workflow
runtime = LocalRuntime()
results = runtime.execute(wf.build())
```

### With AI Agents

```python
from kailash.nodes.ai import LLMAgentNode
from mcp_platform.core import MCPToolRegistry

# Create agent with MCP tools
agent = LLMAgentNode(
    model="gpt-4",
    tools=MCPToolRegistry.get_tools(),
    system_prompt="You are an AI assistant with access to MCP tools."
)
```

## Monitoring and Observability

### Metrics

- Server health and availability
- Tool execution latency
- Resource cache hit rates
- Gateway request throughput
- Authentication success/failure rates

### Logging

- Structured JSON logging
- Correlation IDs for request tracing
- Audit logs for compliance
- Error tracking and alerting

### Health Checks

```bash
# Core platform health
GET /health

# Gateway health
GET /api/v1/health

# Tool server health
GET /health/live
GET /health/ready
```

## Security

### Authentication Methods
- JWT tokens (default)
- OAuth2 integration
- SAML support
- API keys for service accounts

### Authorization
- Role-based access control (RBAC)
- Resource-level permissions
- Tenant isolation
- Tool execution policies

### Security Best Practices
1. Always use TLS in production
2. Rotate secrets regularly
3. Implement rate limiting
4. Enable audit logging
5. Use least privilege principle

## Troubleshooting

### Common Issues

1. **Connection refused**: Check service ports and firewall rules
2. **Authentication failures**: Verify credentials and token expiration
3. **Tool not found**: Ensure tool is registered and available
4. **Performance issues**: Check resource limits and caching

### Debug Mode

```bash
# Enable debug logging
export MCP_PLATFORM_LOG_LEVEL=DEBUG

# Enable SQL query logging
export LOG_SQL_QUERIES=true

# Enable request/response logging
export LOG_HTTP_REQUESTS=true
```

## Migration from Previous Structure

If you were using the previous separate MCP applications:

1. **From `mcp/`**: Update imports to use `mcp_platform.core`
2. **From `mcp_enterprise_gateway/`**: Update to use `mcp_platform.gateway`
3. **From `mcp_tools_server/`**: Update to use `mcp_platform.tools`
4. **From `mcp_integration_patterns/`**: See `mcp_platform/examples/`

## Support and Documentation

- **API Documentation**: http://localhost:8000/docs (when running)
- **Architecture Guide**: See [ARCHITECTURE.md](docs/ARCHITECTURE.md)
- **Contributing**: See [CONTRIBUTING.md](CONTRIBUTING.md)
- **Security**: See [SECURITY.md](SECURITY.md)

## License

This platform is part of the Kailash SDK and follows the same licensing terms.

---

**For MCP application examples**, see:
- [MCP AI Assistant](../mcp_ai_assistant/) - AI assistant using MCP
- [MCP Data Pipeline](../mcp_data_pipeline/) - Data pipeline with MCP orchestration
