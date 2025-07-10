# Nexus Quick Start Guide

Get your first workflow running in 5 minutes!

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- 2GB free disk space

## Step 1: Install Nexus

```bash
# Install from PyPI (Nexus is included with Kailash SDK)
pip install kailash

# Or install from source
git clone https://github.com/kailash/nexus.git
cd nexus
pip install -e .
```

## Step 2: Start Nexus

```python
# nexus_app.py
from kailash_nexus import NexusConfig, NexusApplication

# Configure your platform
config = NexusConfig(
    name="MyPlatform",
    description="My first Nexus platform",
    channels={
        "api": {"enabled": True, "port": 8000},
        "cli": {"enabled": True},
        "mcp": {"enabled": True, "port": 3001}
    }
)

# Initialize and start
app = NexusApplication(config)
app.start()

# You'll see:
# ✅ Nexus started successfully!
# 🌐 API: http://localhost:8000 (docs: http://localhost:8000/docs)
# 💻 CLI: Available via app.cli_channel
# 🤖 MCP: localhost:3001
```

## Step 3: Create Your First Workflow

Let's create a simple data processing workflow:

```python
# hello_world_workflow.py
from kailash.workflow.builder import WorkflowBuilder

# Create the workflow
workflow = WorkflowBuilder()

# Add a simple greeting node
workflow.add_node("PythonCodeNode", "greet", {
    "code": """
name = data.get('name', 'World')
result = f'Hello, {name}!'
print(result)
"""
})

# Register with Nexus
app.register_workflow("hello-world", workflow.build())
```

## Step 4: Test Your Workflow

```python
# Test directly
from kailash.runtime.local import LocalRuntime

runtime = LocalRuntime()
results, run_id = runtime.execute(
    workflow.build(),
    inputs={"name": "Nexus User"}
)

# Output:
# ✅ Workflow executed successfully!
# Hello, Nexus User!
```

## Step 5: Deploy and Use

### Via API

```bash
# The workflow is already registered and available via API
curl -X POST http://localhost:8000/api/workflows/hello-world/execute \
  -H "Content-Type: application/json" \
  -d '{"name": "API User"}'
```

### Via CLI

```bash
# Execute directly (assuming a CLI wrapper is set up)
python -m nexus run hello-world --name "CLI User"
```

### Via Python

```python
import requests

response = requests.post(
    "http://localhost:8000/api/workflows/hello-world/execute",
    json={"name": "Python User"}
)
print(response.json())
```

## Step 6: Explore More Features

### Browse Available Nodes

```bash
# List all available nodes
nexus nodes list

# Get details about a specific node
nexus nodes describe PythonCodeNode
```

### Use Pre-built Workflows

```bash
# List marketplace workflows
nexus marketplace search

# Install a workflow
nexus install data-processor

# Use it immediately
nexus run data-processor --input data.json
```

### Monitor Execution

```bash
# View recent executions
nexus executions list

# Get execution details
nexus executions get <execution-id>

# Stream logs
nexus logs -f
```

## Next Steps

- **[Build Complex Workflows](../development/workflow-guide.md)** - Multi-node workflows
- **[Channel Guides](../channels/)** - Deep dive into API, CLI, MCP
- **[Enterprise Setup](../enterprise/setup.md)** - Production deployment

## Common Issues

### Port Already in Use

```bash
# Use different ports
nexus start --api-port 8080 --mcp-port 3001
```

### Permission Denied

```bash
# Install in user space
pip install --user kailash-nexus

# Or use virtual environment
python -m venv nexus-env
source nexus-env/bin/activate  # On Windows: nexus-env\Scripts\activate
pip install kailash-nexus
```

### Import Errors

```bash
# Ensure Kailash SDK is installed
pip install kailash

# Verify installation
python -c "import kailash; print(kailash.__version__)"
```

## Get Help

- Check logs: `nexus logs`
- Debug mode: `nexus start --debug`
- Community: [Discord](https://discord.gg/kailash)
- Issues: [GitHub](https://github.com/kailash/nexus/issues)
