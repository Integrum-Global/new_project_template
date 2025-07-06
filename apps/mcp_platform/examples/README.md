# MCP Integration Patterns for Kailash SDK Applications

**Complete patterns for integrating Model Context Protocol (MCP) into Kailash SDK applications**

This directory provides production-ready patterns for building applications that leverage the Kailash SDK's comprehensive MCP implementation. These patterns demonstrate how to use MCP for tool interoperability, service discovery, and distributed AI agent communication.

## 🚀 Quick Start Patterns

### Basic MCP Server Integration
```python
from kailash.mcp_server import MCPServer
from kailash import LocalRuntime, WorkflowBuilder

# Create MCP server with Kailash workflows
server = MCPServer("kailash-app-server")

@server.tool()
def execute_workflow(workflow_name: str, inputs: dict) -> dict:
    """Execute a Kailash workflow via MCP."""
    runtime = LocalRuntime()
    workflow = WorkflowBuilder.from_dict(get_workflow_config(workflow_name))
    result = runtime.execute(workflow, inputs)
    return {"workflow": workflow_name, "result": result}

server.run()
```

### Client Discovery and Usage
```python
from kailash.mcp_server import discover_mcp_servers, get_mcp_client

# Discover available AI services
ai_servers = await discover_mcp_servers(capability="ai")
nlp_client = await get_mcp_client("nlp")

# Use in Kailash workflows
result = await nlp_client.call_tool("analyze_text", {"text": data})
```

## 📁 Pattern Categories

### [Basic Integration](basic_integration/)
- Simple MCP server setup with Kailash
- Tool registration patterns
- Resource management
- Configuration examples

### [Service Discovery](service_discovery/)
- Multi-server discovery patterns
- Load balancing with Kailash workflows
- Health monitoring integration
- Failover strategies

### [Authentication & Security](auth_security/)
- API key authentication patterns
- JWT integration with Kailash middleware
- Permission-based tool access
- Security best practices

### [Production Deployment](production/)
- Docker deployment with MCP
- Kubernetes service discovery
- Monitoring and metrics
- Scaling patterns

### [Advanced Patterns](advanced/)
- Multi-modal content handling
- Progress reporting in long workflows
- Circuit breaker integration
- Streaming data patterns

### [Real-World Examples](examples/)
- Complete application implementations
- Industry-specific patterns
- Migration guides
- Performance optimization

## 🎯 Use Cases

### 1. **Distributed AI Agents**
Build networks of AI agents that discover and communicate via MCP:
- Agent discovery and registration
- Tool sharing between agents
- Coordinated multi-agent workflows
- Result aggregation patterns

### 2. **Tool Interoperability**
Create standardized interfaces for AI tools:
- Unified tool APIs across platforms
- Version compatibility handling
- Tool chaining and composition
- Error handling and fallbacks

### 3. **Service Mesh Architecture**
Implement microservices with MCP communication:
- Service registration and discovery
- Load balancing and failover
- Circuit breaker patterns
- Distributed tracing

### 4. **Enterprise Integration**
Connect existing enterprise systems via MCP:
- Legacy system wrapping
- API gateway patterns
- Authentication integration
- Audit logging and compliance

## 🏗️ Architecture Patterns

### Hub and Spoke
```
Central MCP Registry
├── AI Agent A (NLP)
├── AI Agent B (Vision)
├── AI Agent C (Reasoning)
└── Client Applications
```

### Peer-to-Peer Discovery
```
Agent Network
├── Each agent discovers others
├── Direct communication
├── Redundant pathways
└── Self-healing topology
```

### Layered Services
```
Application Layer
├── Business Logic (Kailash Workflows)
├── MCP Communication Layer
├── Service Discovery Layer
└── Transport Layer (STDIO/HTTP/WS)
```

## 📊 Performance Considerations

### Latency Optimization
- Connection pooling patterns
- Caching strategies
- Async communication patterns
- Batch operation handling

### Scaling Patterns
- Horizontal server scaling
- Load balancing algorithms
- Resource allocation strategies
- Performance monitoring

## 🔒 Security Best Practices

### Authentication Patterns
- Multi-factor authentication
- Token-based security
- Role-based access control
- Session management

### Data Protection
- Encryption in transit
- Secure credential storage
- Audit logging
- Compliance patterns

## 🧪 Testing Strategies

### Unit Testing
- MCP server testing
- Tool registration validation
- Authentication testing
- Error handling verification

### Integration Testing
- Multi-server communication
- Service discovery testing
- Failover scenario testing
- Performance benchmarking

### End-to-End Testing
- Complete workflow testing
- User scenario validation
- Security penetration testing
- Load testing patterns

## 📚 Documentation Structure

Each pattern directory contains:
- **README.md** - Pattern overview and use cases
- **implementation.py** - Complete working example
- **config/** - Configuration templates
- **tests/** - Test examples
- **docs/** - Detailed documentation

## 🚦 Getting Started

1. **Choose your pattern** based on use case
2. **Review the implementation** in the pattern directory
3. **Adapt the configuration** to your needs
4. **Run the tests** to validate setup
5. **Deploy using** the provided guidelines

## 🔗 Related Resources

- **[MCP Documentation](../sdk-users/mcp/README.md)** - Complete MCP implementation guide
- **[App Development Guide](../APP_DEVELOPMENT_GUIDE.md)** - General app building patterns
- **[Enterprise Patterns](../ENTERPRISE_PATTERNS.md)** - Advanced enterprise features
- **[Testing Framework](../sdk-users/developer/14-async-testing-framework-guide.md)** - Testing best practices

## 🤝 Contributing

When adding new patterns:
1. Follow the established directory structure
2. Include complete working examples
3. Add comprehensive tests
4. Document performance characteristics
5. Include security considerations

---

**Next Steps:**
- Explore [basic_integration/](basic_integration/) for simple patterns
- Check [examples/](examples/) for complete applications
- Review [production/](production/) for deployment strategies
