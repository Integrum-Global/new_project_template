# MCP Tools Server

A production-ready Model Context Protocol (MCP) server implementation using the Kailash SDK. This example demonstrates how to build a comprehensive MCP server with multiple tools, authentication, service discovery, and high availability features.

## Features

- **Multiple Tool Categories**: Math, data processing, file operations, and utility tools
- **Authentication**: Bearer token, API key, and JWT support
- **Service Discovery**: Automatic service registration and health monitoring
- **High Availability**: Load balancing and failover capabilities
- **Caching**: Built-in caching for expensive operations
- **Metrics**: Comprehensive monitoring and observability
- **Docker Support**: Ready for containerized deployment

## Quick Start

### 1. Basic Server

```bash
# Run the basic MCP server
python basic_server.py
```

### 2. Production Server

```bash
# Run with all production features
python production_server.py
```

### 3. Docker Deployment

```bash
# Build and run with Docker
docker-compose up -d
```

## Architecture

```
mcp_tools_server/
├── servers/           # Different server configurations
│   ├── basic_server.py      # Simple MCP server
│   ├── auth_server.py       # Server with authentication
│   ├── ha_server.py         # High-availability server
│   └── production_server.py # Full production setup
├── tools/            # MCP tool implementations
│   ├── math_tools.py        # Mathematical operations
│   ├── data_tools.py        # Data processing tools
│   ├── file_tools.py        # File operations
│   └── utility_tools.py     # General utilities
├── clients/          # Example client applications
│   ├── basic_client.py      # Simple client
│   ├── agent_client.py      # LLM agent with MCP
│   └── workflow_client.py   # Workflow integration
├── config/           # Configuration files
│   ├── server_config.yaml   # Server settings
│   └── auth_config.yaml     # Authentication config
└── tests/            # Test suite
    ├── test_tools.py        # Tool tests
    └── test_integration.py  # Integration tests
```

## Tools Available

### Math Tools
- `calculate`: Basic arithmetic operations
- `factorial`: Calculate factorial of a number
- `fibonacci`: Generate Fibonacci sequence
- `prime_check`: Check if number is prime
- `statistics`: Calculate mean, median, mode

### Data Tools
- `json_parse`: Parse and validate JSON
- `csv_process`: Process CSV data
- `data_transform`: Transform data structures
- `aggregate`: Aggregate data with various functions

### File Tools
- `read_file`: Read file contents
- `write_file`: Write data to file
- `list_directory`: List directory contents
- `file_info`: Get file metadata

### Utility Tools
- `datetime_now`: Get current datetime
- `uuid_generate`: Generate UUID
- `hash_data`: Hash data with various algorithms
- `encode_decode`: Base64 encoding/decoding

## Authentication

The server supports multiple authentication methods:

### Bearer Token
```python
auth = BearerTokenAuth(token="your-secret-token")
```

### API Key
```python
auth = APIKeyAuth(api_keys=["key1", "key2"])
```

### JWT
```python
auth = JWTAuth(secret_key="jwt-secret", algorithm="HS256")
```

## Service Discovery

The server automatically registers with service discovery:

```python
# Discover available MCP servers
services = await discovery.discover(service_type="mcp-server")
```

## Load Balancing

Deploy multiple instances with automatic load balancing:

```yaml
# docker-compose.yml
services:
  mcp-server-1:
    build: .
    environment:
      - SERVER_NAME=mcp-1
      - PORT=8080

  mcp-server-2:
    build: .
    environment:
      - SERVER_NAME=mcp-2
      - PORT=8081

  mcp-server-3:
    build: .
    environment:
      - SERVER_NAME=mcp-3
      - PORT=8082
```

## Client Examples

### Basic Client
```python
from kailash.mcp_server import MCPClient

client = MCPClient("my-client")
await client.connect("mcp://localhost:8080")
result = await client.call_tool("calculate", {"a": 10, "b": 5, "operation": "add"})
```

### Agent Integration
```python
from kailash.nodes.ai import LLMAgentNode

agent = LLMAgentNode(
    name="mcp_agent",
    mcp_servers=["mcp://localhost:8080"],
    enable_mcp=True
)
```

## Monitoring

Access metrics at `http://localhost:8080/metrics`:
- Request counts
- Latency histograms
- Error rates
- Cache hit rates

## Testing

```bash
# Run unit tests
pytest tests/test_tools.py

# Run integration tests
pytest tests/test_integration.py

# Run load tests
python tests/load_test.py
```

## Production Deployment

See [deployment/README.md](deployment/README.md) for:
- Kubernetes manifests
- Helm charts
- Terraform configs
- CI/CD pipelines

## Security Considerations

- Always use HTTPS in production
- Rotate authentication tokens regularly
- Enable rate limiting
- Use network policies in Kubernetes
- Monitor for anomalous usage patterns

## Performance Tuning

- Adjust worker count based on CPU cores
- Configure cache TTL for your use case
- Use connection pooling for databases
- Enable response compression
- Implement request batching for bulk operations
