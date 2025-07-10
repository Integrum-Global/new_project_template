# Workflow Development for Nexus

Learn how to build workflows that run across all Nexus channels (API, CLI, MCP).

## Quick Start

```python
from kailash.workflow.builder import WorkflowBuilder
from kailash.runtime.local import LocalRuntime
from kailash_nexus import create_nexus

# Create workflow
workflow = WorkflowBuilder()
workflow.add_node("LLMAgentNode", "assistant", {
    "provider": "openai",
    "model": "gpt-4",
    "use_real_mcp": True
})

# Deploy to Nexus
nexus = create_nexus(
    title="My Assistant",
    enable_api=True,
    enable_cli=True,
    enable_mcp=True
)

# Register workflow
nexus.register_workflow("assistant", workflow.build())
```

## Channel-Specific Patterns

### API Channel
```python
# HTTP request triggers workflow
workflow.add_node("HTTPRequestNode", "api_input", {
    "method": "POST",
    "endpoint": "/process"
})
```

### CLI Channel
```python
# Command line triggers workflow
workflow.add_node("CLIInputNode", "cli_input", {
    "command": "process",
    "args": ["--input", "text"]
})
```

### MCP Channel
```python
# AI agent triggers workflow
workflow.add_node("MCPToolNode", "mcp_input", {
    "tool_name": "process_data",
    "description": "Process user data"
})
```

## Session Management

```python
# Unified sessions across channels
nexus = create_nexus(
    channels_synced=True,  # Sessions sync across API/CLI/MCP
    session_timeout=3600   # 1 hour session timeout
)
```

## Error Handling

```python
# Graceful error handling
workflow.add_node("TryNode", "safe_operation", {
    "try_workflow": main_workflow,
    "catch_workflow": error_workflow,
    "finally_workflow": cleanup_workflow
})
```

## Authentication Integration

```python
# Enterprise auth
nexus = create_nexus(
    auth_strategy="enterprise",
    sso_enabled=True,
    rbac_enabled=True
)
```

## Performance Optimization

```python
# Async processing
workflow.add_node("AsyncProcessorNode", "batch_process", {
    "concurrency": 10,
    "batch_size": 100
})
```

## Monitoring Integration

```python
# Built-in metrics
workflow.add_node("MetricsNode", "monitor", {
    "track_performance": True,
    "export_prometheus": True
})
```

## Testing Workflows

```python
# Test all channels
def test_workflow():
    # Test API
    response = nexus.api_client.post("/process", json={"data": "test"})
    assert response.status_code == 200

    # Test CLI
    result = nexus.cli_client.execute("process --input test")
    assert result.success

    # Test MCP
    mcp_result = nexus.mcp_client.call_tool("process_data", {"input": "test"})
    assert mcp_result["success"]
```

## Best Practices

1. **Channel Agnostic**: Design workflows that work across all channels
2. **Session Aware**: Use unified sessions for user state
3. **Error Resilient**: Always include error handling
4. **Performance First**: Use async operations for heavy workloads
5. **Security Minded**: Apply authentication and authorization
6. **Monitoring Ready**: Include metrics and logging
7. **Test Comprehensive**: Validate all channels

## Common Patterns

### Data Processing Pipeline
```python
workflow = WorkflowBuilder()
workflow.add_node("DataReaderNode", "input", {"source": "database"})
workflow.add_node("DataTransformerNode", "transform", {"operation": "clean"})
workflow.add_node("DataWriterNode", "output", {"destination": "api"})

workflow.add_connection("input", "result", "transform", "data")
workflow.add_connection("transform", "result", "output", "data")
```

### AI Assistant with Tools
```python
workflow = WorkflowBuilder()
workflow.add_node("LLMAgentNode", "assistant", {
    "provider": "openai",
    "model": "gpt-4",
    "mcp_servers": [
        {"name": "file_tools", "transport": "stdio", "command": "mcp-server-filesystem"},
        {"name": "web_tools", "transport": "stdio", "command": "mcp-server-web"}
    ]
})
```

### Multi-Step Authentication
```python
workflow = WorkflowBuilder()
workflow.add_node("AuthNode", "auth", {"strategy": "multi_factor"})
workflow.add_node("SwitchNode", "auth_check", {
    "condition": lambda x: x["authenticated"],
    "true_branch": "main_workflow",
    "false_branch": "auth_error"
})
```

## Advanced Features

### Custom Channel Integration
```python
# Add custom channel
nexus.add_channel("websocket", {
    "handler": WebSocketHandler,
    "port": 8080
})
```

### Workflow Versioning
```python
# Version management
nexus.register_workflow("assistant_v1", workflow_v1)
nexus.register_workflow("assistant_v2", workflow_v2)
nexus.set_default("assistant", "assistant_v2")
```

### Dynamic Configuration
```python
# Runtime configuration
nexus.configure({
    "max_concurrent_workflows": 100,
    "enable_auto_scaling": True,
    "metrics_export_interval": 30
})
```

## Next Steps

- **Testing**: [Testing Guide](testing.md) - Comprehensive testing strategies
- **Integrations**: [Custom Integrations](integrations.md) - Extend Nexus capabilities
- **Enterprise**: [Enterprise Setup](../enterprise/setup.md) - Production deployment
- **Monitoring**: [Monitoring & Operations](../enterprise/monitoring.md) - Observability setup
