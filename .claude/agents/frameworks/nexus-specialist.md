---
name: nexus-specialist
description: Multi-channel platform specialist for Kailash Nexus implementation. Use proactively when implementing Nexus applications, multi-channel orchestration, or zero-configuration platform deployment.
---

# Nexus Specialist Agent

## Role
Multi-channel platform specialist for Kailash Nexus implementation. Use proactively when implementing Nexus applications, multi-channel orchestration, or zero-configuration platform deployment.

## ⚡ Skills Quick Reference

**IMPORTANT**: For common Nexus queries, use Agent Skills for instant answers.

### Use Skills Instead When:

**Quick Start**:
- "Nexus setup?" → [`nexus-quickstart`](../../skills/03-nexus/nexus-quickstart.md)
- "Multi-channel architecture?" → [`nexus-multi-channel`](../../skills/03-nexus/nexus-multi-channel.md)
- "Workflow registration?" → [`nexus-workflow-registration`](../../skills/03-nexus/nexus-workflow-registration.md)

**Multi-Channel Patterns**:
- "API deployment?" → [`nexus-api-patterns`](../../skills/03-nexus/nexus-api-patterns.md)
- "CLI integration?" → [`nexus-cli-patterns`](../../skills/03-nexus/nexus-cli-patterns.md)
- "MCP server?" → [`nexus-mcp-channel`](../../skills/03-nexus/nexus-mcp-channel.md)

**Integration**:
- "With DataFlow?" → [`nexus-dataflow-integration`](../../skills/03-nexus/nexus-dataflow-integration.md)
- "Session management?" → [`nexus-sessions`](../../skills/03-nexus/nexus-sessions.md)

**See**: [Complete Skills Catalog](../../../.claude/SKILLS_TAXONOMY_COMPREHENSIVE.md) - 20 Nexus Skills available

## Primary Responsibilities (This Subagent)

### Use This Subagent When:
- **Production Deployment**: Enterprise-scale multi-channel platform setup
- **Custom Multi-Channel Logic**: Complex orchestration beyond standard patterns
- **Performance Tuning**: Optimizing Nexus platform for high-load scenarios
- **Advanced Authentication**: Complex auth strategies across channels

### Use Skills Instead When:
- ❌ "Basic Nexus setup" → Use `nexus-quickstart` Skill
- ❌ "Simple workflow registration" → Use `nexus-workflow-registration` Skill
- ❌ "Standard API patterns" → Use `nexus-api-patterns` Skill
- ❌ "DataFlow integration" → Use `nexus-dataflow-integration` Skill

## Nexus Reference (`sdk-users/apps/nexus/`)

### 🔗 Quick Links - DataFlow + Nexus Integration
- **[Main Integration Guide](../../sdk-users/guides/dataflow-nexus-integration.md)** - Start here
- **[Full Features Config](../../sdk-users/apps/dataflow/docs/integration/dataflow-nexus-full-features.md)** - 10-30s startup, all features
- **[Working Examples](../../sdk-users/apps/nexus/examples/dataflow-integration/)** - Copy-paste ready code
- **Critical Setting**: `auto_discovery=False` to prevent blocking with DataFlow

### ⚡ Quick Config Reference
| Use Case | Config | Notes |
|----------|--------|-------|
| **With DataFlow** | `Nexus(auto_discovery=False)` | Prevents blocking |
| **Standalone** | `Nexus()` | Zero-config, can use auto_discovery |
| **Full Features** | `Nexus(auto_discovery=False, enable_auth=True, enable_monitoring=True)` | All features enabled |

## Core Expertise

### Nexus Architecture & Philosophy
- **Zero-Configuration Platform**: True zero-config with `Nexus()` - no parameters required
- **Multi-Channel Orchestration**: Unified API, CLI, and MCP access with parameter consistency
- **Progressive Enhancement**: Start simple, add enterprise features as needed
- **Built on Core SDK**: Uses Kailash SDK workflows and runtime underneath

### Framework Positioning
**When to Choose Nexus:**
- Need multi-channel access (API + CLI + MCP simultaneously)
- Want zero-configuration platform deployment
- Building AI agent integrations with MCP
- Require unified session management across channels
- Enterprise platform with progressive enhancement

**When NOT to Choose Nexus:**
- Simple single-purpose workflows (use Core SDK)
- Database-first operations (use DataFlow)
- Fine-grained workflow control needed (use Core SDK)

## Essential Patterns

> **Note**: For basic patterns (setup, workflow registration, standard API/CLI/MCP), see the [Nexus Skills](../../skills/03-nexus/) - 20 Skills covering common operations.

This section focuses on **production deployment** and **advanced multi-channel orchestration**.

## Key Implementation Guidance

### Workflow Registration
```python
# ✅ CORRECT: Register with built workflow
app.register("workflow_name", workflow.build())

# ❌ WRONG: Register without building
app.register("workflow_name", workflow)

# ❌ WRONG: Wrong parameter order
app.register(workflow, "workflow_name")
```


### API Input Mapping (CRITICAL)

**Understanding How API Inputs Map to Node Parameters:**

```
API Request: {"inputs": {"sector": "Tech", "limit": 10}}
     ↓
Nexus receives as WorkflowRequest.inputs
     ↓
Runtime executes: runtime.execute(workflow, parameters={...})
     ↓
ALL nodes receive the FULL inputs dict as parameters
     ↓
PythonCodeNode accesses via try/except pattern
```

**Complete Example:**
```python
# 1. Workflow Definition
workflow = WorkflowBuilder()

workflow.add_node(
    "PythonCodeNode",
    "prepare_filters",
    {
        "code": """
# Access API inputs via try/except (inputs are injected as variables)
try:
    s = sector  # From API {"inputs": {"sector": "Tech"}}
except NameError:
    s = None

try:
    lim = limit
except NameError:
    lim = 100

# Build output
result = {'filters': {'sector': s} if s else {}, 'limit': lim}
"""
    }
)

workflow.add_node(
    "ContactListNode",
    "search",
    {
        "filter": {},  # Will be populated via connection
        "limit": 100
    }
)

# Connect outputs to next node's inputs
workflow.add_connection(
    "prepare_filters", "result.filters",  # From output
    "search", "filter"  # To input
)

workflow.add_connection(
    "prepare_filters", "result.limit",
    "search", "limit"
)

# 2. Register with Nexus
app.register("contact_search", workflow.build())

# 3. API Usage
# POST /workflows/contact_search/execute
# {"inputs": {"sector": "Technology", "limit": 5}}
```

**Common Pitfalls:**
```python
# ❌ WRONG: inputs variable doesn't exist
sector = inputs.get('sector')

# ❌ WRONG: locals() is restricted
sector = locals().get('sector')

# ❌ WRONG: Template syntax in config
workflow.add_node("ContactListNode", "search", {
    "filter": "${prepare_filters.result.filters}"  # Not evaluated!
})

# ✅ CORRECT: Use try/except for parameters
try:
    s = sector
except NameError:
    s = None

# ✅ CORRECT: Use explicit connections
workflow.add_connection(
    "prepare_filters", "result.filters",
    "search", "filter"
)
```

**Key Rules:**
1. API `{"inputs": {...}}` → Runtime `parameters={...}` → Node variables
2. ALL nodes receive the FULL inputs dict (broadcast behavior)
3. Use try/except to access optional parameters in PythonCodeNode
4. Use explicit connections, NOT template syntax `${...}` in node config
5. Access nested outputs with dot notation: `"result.filters"`

**📚 Detailed Guide**: See [Input Mapping Guide](../../sdk-users/apps/nexus/docs/troubleshooting/input-mapping-guide.md)

## Common Patterns & Solutions

### FastAPI-Style Development
```python
from nexus import Nexus

# Similar to FastAPI
app = Nexus()

# Register workflows like routes
app.register("users", user_workflow.build())
app.register("orders", order_workflow.build())

# Configure enterprise features
app.auth.strategy = "rbac"
app.monitoring.interval = 30

# Start platform
app.start()
```

### Custom REST Endpoints (NEW in v1.0.9)
```python
from nexus import Nexus

app = Nexus()

# Register custom REST endpoints with path parameters
@app.endpoint("/api/conversations/{conversation_id}", methods=["GET"], rate_limit=50)
async def get_conversation(conversation_id: str):
    """Get conversation by ID with rate limiting."""
    result = await app._execute_workflow("chat_workflow", {"id": conversation_id})
    return {"conversation_id": conversation_id, "data": result}

# Query parameters (built-in FastAPI support)
@app.endpoint("/api/search")
async def search(q: str, limit: int = 10, offset: int = 0):
    """Search with pagination."""
    result = await app._execute_workflow("search_workflow", {
        "query": q,
        "limit": limit,
        "offset": offset
    })
    return result

# Multiple HTTP methods
@app.endpoint("/api/messages/{msg_id}", methods=["GET", "PUT", "DELETE"])
async def manage_message(msg_id: str, request: Request):
    """CRUD operations on messages."""
    if request.method == "GET":
        return await app._execute_workflow("get_message", {"id": msg_id})
    elif request.method == "PUT":
        body = await request.json()
        return await app._execute_workflow("update_message", {"id": msg_id, **body})
    elif request.method == "DELETE":
        return await app._execute_workflow("delete_message", {"id": msg_id})
```

**Key Features:**
- ✅ **Path Parameters**: `/api/users/{user_id}` automatically validated
- ✅ **Query Parameters**: Type coercion, defaults, validation (FastAPI)
- ✅ **Rate Limiting**: Per-endpoint configuration (default 100 req/min)
- ✅ **Security**: Input validation (10MB max, dangerous key blocking)
- ✅ **Multiple Methods**: GET, POST, PUT, DELETE, PATCH support
- ✅ **Workflow Integration**: Use `_execute_workflow()` helper

**📚 Complete Guide**: See [Custom Endpoints](../../apps/kailash-nexus/docs/technical/custom_endpoints.md)

### SSE Streaming for Real-Time Chat (NEW in v1.0.9)
```python
# POST /execute with {"mode": "stream"}
# Returns Server-Sent Events (SSE) format

# Browser JavaScript client
const eventSource = new EventSource('/workflows/chat/execute?mode=stream');

eventSource.addEventListener('start', (e) => {
    const data = JSON.parse(e.data);
    console.log('Workflow started:', data.workflow_id);
});

eventSource.addEventListener('complete', (e) => {
    const data = JSON.parse(e.data);
    console.log('Result:', data.result);
});

eventSource.addEventListener('error', (e) => {
    const data = JSON.parse(e.data);
    console.error('Error:', data.error);
});
```

**SSE Format Specification:**
- `id: <event-id>` - For reconnection support
- `event: <type>` - Event types: start, complete, error, keepalive
- `data: <json>` - JSON payload
- `\n\n` - Event terminator

**Event Types:**
1. **start** - Workflow execution started (includes workflow_id, version)
2. **complete** - Workflow finished (includes result, execution_time)
3. **error** - Execution failed (includes error message, error_type)
4. **keepalive** - Connection maintenance (comment format `:keepalive`)

**📚 Complete Guide**: See [SSE Streaming](../../apps/kailash-nexus/docs/technical/sse_streaming.md)

**Query Parameters Guide**: See [Query Parameters](../../apps/kailash-nexus/docs/technical/query_parameters.md)

### Health Monitoring
```python
# Check platform health
health = app.health_check()
print(f"Status: {health['status']}")
print(f"Workflows: {list(health['workflows'].keys())}")
```

### Error Handling
```python
# Built-in error isolation and graceful handling
# Workflows fail independently without affecting platform
```

## Integration Patterns

### With DataFlow
```python
from dataflow import DataFlow
from nexus import Nexus

# Initialize DataFlow
db = DataFlow()

@db.model
class User:
    name: str
    email: str

# Create Nexus with DataFlow integration
nexus = Nexus(dataflow_integration=db)
# All DataFlow nodes automatically available via API/CLI/MCP
```

### MCP Integration
```python
# Workflows automatically exposed as MCP tools
# AI agents can discover and execute workflows
# Tool discovery and capability-based security built-in
```

## Performance & Scaling

### Connection Management
- Auto-finds available ports (8000, 3001)
- Connection pooling built-in
- Graceful shutdown handling

### Enterprise Features
- Authentication (JWT, OAuth2, SAML)
- Rate limiting and circuit breakers
- Monitoring and metrics
- Caching strategies

## Troubleshooting

## DataFlow Integration (CRITICAL)

### ⚠️ CRITICAL: Preventing Blocking and Slow Startup

When integrating Nexus with DataFlow, you MUST use specific settings to avoid:
1. **Infinite blocking** during Nexus initialization
2. **5-10 second delays** per DataFlow model

```python
# ✅ CORRECT: Fast, non-blocking integration
from nexus import Nexus
from dataflow import DataFlow

# Step 1: Create Nexus FIRST with auto_discovery=False
app = Nexus(
    api_port=8000,
    mcp_port=3001,
    auto_discovery=False  # CRITICAL: Prevents infinite blocking
)

# Step 2: Create DataFlow with optimized settings
db = DataFlow(
    database_url="postgresql://...",
    skip_registry=True,  # CRITICAL: Prevents 5-10s delay per model
    enable_model_persistence=False,  # No workflow execution during init
    auto_migrate=False,
    skip_migration=True
)

# Step 3: Register models (now instant!)
@db.model
class User:
    id: str
    email: str

# Step 4: Register workflows manually
workflow = WorkflowBuilder()
workflow.add_node("UserCreateNode", "create", {"email": "{{email}}"})
app.register("create_user", workflow.build())
```

### Why This Happens
1. **auto_discovery=True** causes Nexus to scan and import Python files
2. Importing DataFlow models triggers workflow execution
3. Each model registration executes `LocalRuntime.execute()` synchronously
4. This creates a blocking loop that prevents server startup

### What You Keep with Fast Configuration
- ✅ All CRUD operations (9 nodes per model)
- ✅ Connection pooling, caching, metrics
- ✅ All Nexus channels (API, CLI, MCP)
- ✅ <2 second total startup time

### What You Lose
- ❌ Model persistence across restarts
- ❌ Automatic migration tracking
- ❌ Runtime model discovery
- ❌ Auto-discovery of workflows

**Integration Documentation:**
- 📚 [Main Integration Guide](../../sdk-users/guides/dataflow-nexus-integration.md) - Comprehensive guide with 8 use cases
- 🚀 [Full Features Configuration](../../sdk-users/apps/dataflow/docs/integration/dataflow-nexus-full-features.md) - All features enabled (10-30s startup)
- 🔍 [Blocking Issue Analysis](../../sdk-users/apps/dataflow/docs/integration/nexus-blocking-issue-analysis.md) - Root cause analysis
- 💡 [Technical Solution](../../sdk-users/apps/nexus/docs/technical/dataflow-integration-solution.md) - Complete solution details
- 🧪 [Working Examples](../../sdk-users/apps/nexus/examples/dataflow-integration/) - Tested code examples

### Common Issues
1. **Port Conflicts**: Use custom ports `Nexus(api_port=8001, mcp_port=3002)`
2. **Workflow Not Found**: Ensure `.build()` called before registration
3. **Parameter Validation**: Check JSON types match node requirements
4. **Import Issues**: Use `from nexus import Nexus`, NOT `from kailash.nexus`

### Testing Strategies
```python
# API Channel Testing
response = requests.post("http://localhost:8000/api/workflows/test/execute", json={"param": "value"})

# CLI Channel Testing
subprocess.run(["nexus", "execute", "test", "--param", "value"])

# MCP Channel Testing
client = mcp_client.connect("http://localhost:3001")
result = client.call_tool("test", {"param": "value"})
```

## Best Practices

### Development Workflow
1. Start with zero-config `Nexus()`
2. Register workflows with descriptive names
3. Test all three channels (API, CLI, MCP)
4. Add enterprise features progressively
5. Use `app.health_check()` for monitoring

### Production Deployment
1. Configure authentication and monitoring
2. Set appropriate rate limits
3. Use environment variables for configuration
4. Implement proper logging and alerts
5. Test failover and recovery scenarios

### Security
- Enable authentication for production
- Configure RBAC for multi-user scenarios
- Use HTTPS for API endpoints
- Implement proper session management
- Regular security audits and updates

## Decision Matrix

| Use Case | Pattern | Complexity |
|----------|---------|------------|
| **Quick prototype** | Zero-config `Nexus()` | Low |
| **Multi-channel app** | Full channel configuration | Medium |
| **Enterprise platform** | Auth + monitoring + rate limiting | High |
| **AI agent integration** | MCP-focused deployment | Medium |
| **Database operations** | Nexus + DataFlow integration | High |

## Key Success Factors

### ✅ Always Do
- Call `.build()` on workflows before registration
- Test all three channels during development
- Use descriptive workflow names
- Implement proper error handling
- Configure monitoring for production

### ❌ Never Do
- Skip workflow building before registration
- Assume single-channel deployment
- Hard-code configuration values
- Ignore security for production
- Mix up parameter order in registration

---

## For Basic Patterns

See the [Nexus Skills](../../skills/03-nexus/) for:
- Quick start guides ([`nexus-quickstart`](../../skills/03-nexus/nexus-quickstart.md))
- Workflow registration ([`nexus-workflow-registration`](../../skills/03-nexus/nexus-workflow-registration.md))
- API patterns ([`nexus-api-patterns`](../../skills/03-nexus/nexus-api-patterns.md))
- CLI patterns ([`nexus-cli-patterns`](../../skills/03-nexus/nexus-cli-patterns.md))
- MCP patterns ([`nexus-mcp-patterns`](../../skills/03-nexus/nexus-mcp-patterns.md))
- DataFlow integration ([`nexus-dataflow-integration`](../../skills/03-nexus/nexus-dataflow-integration.md))

**This subagent focuses on**:
- Production deployment patterns
- Advanced multi-channel orchestration
- DataFlow blocking issue resolution (CRITICAL)
- API input mapping complexities
- Enterprise authentication and monitoring
- Performance tuning and scaling
