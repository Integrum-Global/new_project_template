# Kailash Nexus

**The Enterprise Multi-Channel Orchestration Platform** - Access your Kailash workflows through API, CLI, or AI agents.

[![Tests](https://img.shields.io/badge/tests-105%20passing-brightgreen)](tests/)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
[![SDK](https://img.shields.io/badge/built%20with-Kailash%20SDK-orange)](../README.md)

## 🚀 Quick Start (2 minutes)

```python
from nexus import NexusApplication, NexusConfig

# Create configuration
config = NexusConfig(
    name="QuickStart",
    channels={
        "api": {"enabled": True, "port": 8000},
        "cli": {"enabled": True},
        "mcp": {"enabled": True, "port": 3001}
    }
)

# Initialize application
app = NexusApplication(config)

# Your platform is ready!
# 🌐 API: http://localhost:8000
# 💻 CLI: Available via app.cli_channel
# 🤖 MCP: localhost:3001
```

That's it! You now have a complete workflow orchestration platform running locally.

## 🎯 What Can You Do with Nexus?

### For Solo Developers
```bash
# Create your first workflow
nexus create workflow data-processor

# Test it
nexus test data-processor --input data.json

# Deploy and use
nexus deploy data-processor
nexus run data-processor --input production.json
```

### For Teams
```bash
# Share workflows via marketplace
nexus publish my-workflow --description "Processes customer data"

# Discover and install team workflows
nexus search "data processing"
nexus install team/data-processor
```

### For Enterprises
```yaml
# Configure multi-tenant deployment
nexus init --enterprise --config enterprise.yaml

# Features included:
# ✅ Multi-tenant isolation
# ✅ SSO/LDAP authentication
# ✅ Role-based access control
# ✅ Audit logging
# ✅ High availability
```

### For Data-Heavy Workflows
```python
# Workflows can use QueryBuilder + QueryCache for performance
from kailash.nodes.data.query_builder import create_query_builder
from kailash.nodes.data.query_cache import QueryCache

# MongoDB-style queries across any database
builder = create_query_builder("postgresql")
builder.table("users").where("age", "$gt", 18)
sql, params = builder.build_select(["name", "email"])

# Redis caching with tenant isolation
cache = QueryCache(redis_host="localhost", redis_port=6379)
result = cache.get(sql, params, tenant_id="tenant_123")
```

## 📚 Documentation

### Getting Started
- **[5-Minute Tutorial](docs/getting-started/quickstart.md)** - Build your first workflow
- **[Installation Guide](docs/getting-started/installation.md)** - Detailed setup instructions
- **[Examples](examples/)** - Ready-to-use workflow templates

### Channel Guides
- **[REST API](docs/channels/api-guide.md)** - RESTful API with OpenAPI docs
- **[CLI](docs/channels/cli-guide.md)** - Powerful command-line interface
- **[MCP](docs/channels/mcp-guide.md)** - AI agent integration

### Workflow Development
- **[Data Workflows](examples/data_workflow_with_caching.py)** - QueryBuilder + QueryCache patterns
- **[Performance Guide](docs/workflows/performance.md)** - Caching and optimization
- **[Multi-tenant Patterns](docs/workflows/multi-tenant.md)** - Enterprise data isolation

### Enterprise
- **[Production Setup](docs/enterprise/setup.md)** - Deploy to production
- **[Security Guide](docs/enterprise/security.md)** - Authentication & authorization
- **[Operations](docs/enterprise/monitoring.md)** - Monitoring & scaling

## 🏗️ Architecture

Nexus is built entirely on the Kailash SDK - no custom orchestration code:

```
┌─────────────────────────────────────────────────────┐
│                   Your Workflows                     │
├─────────────────────────────────────────────────────┤
│                   Nexus Platform                     │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐        │
│  │   API   │    │   CLI   │    │   MCP   │        │
│  └────┬────┘    └────┬────┘    └────┬────┘        │
│       └──────────────┴──────────────┘              │
│                Session Manager                       │
├─────────────────────────────────────────────────────┤
│              Enterprise Features                     │
│  Auth │ Multi-tenant │ RBAC │ Audit │ Monitoring   │
├─────────────────────────────────────────────────────┤
│                 Kailash SDK                         │
└─────────────────────────────────────────────────────┘
```

## 💡 Real-World Examples

### High-Performance Data Pipeline
```python
# workflows/etl_pipeline.py
workflow = WorkflowBuilder()
workflow.add_node("HTTPRequestNode", "fetch_data", {
    "url": "https://api.example.com/data"
})
workflow.add_node("PythonCodeNode", "build_query", {
    "code": """
from kailash.nodes.data.query_builder import create_query_builder
builder = create_query_builder("postgresql")
builder.table("users").where("status", "$eq", "active")
sql, params = builder.build_select(["id", "name", "email"])
result = {"sql": sql, "parameters": params}
"""
})
workflow.add_node("PythonCodeNode", "cached_query", {
    "code": """
from kailash.nodes.data.query_cache import QueryCache
cache = QueryCache(redis_host="localhost", redis_port=6379)
result = cache.get(input_data["sql"], input_data["parameters"])
if not result:
    # Execute query and cache result
    cache.set(input_data["sql"], input_data["parameters"], query_result)
"""
})
```

### AI Agent Integration
```python
# Enable MCP for AI agents
nexus start --mcp

# Your workflows are now AI-accessible!
# Claude, GPT-4, etc. can discover and use them
```

### Multi-Tenant SaaS
```yaml
# Deploy isolated environments per customer
nexus tenant create acme-corp
nexus tenant create globex-inc

# Each tenant gets:
# - Isolated workflows
# - Separate data
# - Custom quotas
# - Independent scaling
```

## 🧪 Testing

Nexus includes comprehensive testing following SDK standards:

```bash
# Run all tests
pytest tests/

# Run by tier
pytest tests/unit/          # Fast, isolated
pytest tests/integration/   # With dependencies
pytest tests/e2e/          # Full scenarios

# Current status: 105/105 tests passing ✅
```

## 🤝 Contributing

We welcome contributions! Nexus is built 100% on Kailash SDK:

1. Use SDK components only (no custom orchestration)
2. Follow SDK patterns and conventions
3. Write tests for all changes
4. Update documentation

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## 📞 Support

- **Documentation**: [docs/](docs/)
- **Examples**: [examples/](examples/)
- **Issues**: [GitHub Issues](https://github.com/kailash/nexus/issues)
- **Community**: [Discord](https://discord.gg/kailash)

## ⚡ Why Nexus?

- **Zero Lock-in**: Built on open SDK standards
- **Multi-Channel**: API, CLI, and AI agent access
- **Enterprise Ready**: Production-tested features
- **Developer Friendly**: Start simple, scale later
- **100% SDK**: No proprietary orchestration code

---

**Built with Kailash SDK** | [Parent Project](../../README.md) | [SDK Docs](../../sdk-users/)
