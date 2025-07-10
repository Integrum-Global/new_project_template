# Kailash Nexus User Guide

## Building Unified Applications with API, CLI, and MCP

This guide walks you through using Kailash Nexus to build applications that seamlessly integrate multiple interfaces. We'll start simple and progressively add features, demonstrating the power of unified orchestration.

## 📚 Table of Contents

1. [Getting Started](#getting-started)
2. [Basic Nexus Application](#basic-nexus-application)
3. [Adding Authentication](#adding-authentication)
4. [Cross-Channel Workflows](#cross-channel-workflows)
5. [Real-Time Features](#real-time-features)
6. [Enterprise Configuration](#enterprise-configuration)
7. [Custom Channels](#custom-channels)
8. [Production Deployment](#production-deployment)

## 🚀 Getting Started

### Installation

Nexus is included with the Kailash SDK:

```bash
pip install kailash
```

### Your First Nexus

```python
from kailash_nexus import NexusConfig, NexusApplication

# Zero-configuration Nexus
config = NexusConfig(
    name="MyApp",
    channels={
        "api": {"enabled": True},
        "cli": {"enabled": True},
        "mcp": {"enabled": True}
    }
)
app = NexusApplication(config)

# Start the platform
app.start()
```

That's it! You now have:
- REST API at `http://localhost:8000/api/`
- API documentation at `http://localhost:8000/docs`
- CLI available via `nexus` command
- MCP server for AI agent integration
- WebSocket endpoint at `ws://localhost:8000/ws`
- Server-sent events at `http://localhost:8000/events`

## 🎯 Basic Nexus Application

Let's build a simple task management application with full API, CLI, and MCP support:

```python
from kailash_nexus import NexusConfig, NexusApplication
from kailash.workflow.builder import WorkflowBuilder
import asyncio

# Create Nexus
config = NexusConfig(
    name="Task Manager",
    channels={
        "api": {"enabled": True},
        "cli": {"enabled": True},
        "mcp": {"enabled": True}
    }
)
app = NexusApplication(config)

# Define task workflow
task_workflow = WorkflowBuilder("task_operations")

# Add task creation
task_workflow.add_node("ValidationNode", "validate_task", {
    "schema": {
        "type": "object",
        "properties": {
            "title": {"type": "string", "minLength": 1},
            "description": {"type": "string"},
            "priority": {"type": "string", "enum": ["low", "medium", "high"]}
        },
        "required": ["title"]
    }
})

task_workflow.add_node("DataTransformer", "create_task", {
    "transformation_type": "custom",
    "custom_code": """
import uuid
from datetime import datetime

result = {
    'id': str(uuid.uuid4()),
    'title': data['title'],
    'description': data.get('description', ''),
    'priority': data.get('priority', 'medium'),
    'status': 'pending',
    'created_at': datetime.utcnow().isoformat()
}
"""
})

task_workflow.add_connection("validate_task", "create_task")

# Register workflow with Nexus
app.register_workflow("task_operations", task_workflow.build())

# Start Nexus
if __name__ == "__main__":
    asyncio.run(app.start())
```

### Using the Application

#### Via API:
```bash
# Create a task
curl -X POST http://localhost:8000/api/workflows/task_operations/execute \
  -H "Content-Type: application/json" \
  -d '{
    "inputs": {
        "title": "Review documentation",
        "description": "Review and update API docs",
        "priority": "high"
    }
}'
```

#### Via CLI:
```bash
# Same operation from command line
nexus workflow execute task_operations \
  --title "Review documentation" \
  --description "Review and update API docs" \
  --priority high
```

#### Via MCP:
```python
# AI agents can use the same workflow
from kailash.mcp import MCPClient

async def use_mcp_client():
    client = MCPClient("http://localhost:8000/mcp")
    result = await client.call_tool(
        "task_operations",
    {
        "title": "Review documentation",
        "description": "Review and update API docs",
        "priority": "high"
    }
)
```

## 🔐 Adding Authentication

Let's add JWT authentication that works across all channels:

```python
from kailash_nexus import create_nexus
from kailash.workflow.builder import WorkflowBuilder
from kailash.nodes.auth import JWTAuthNode, PasswordHashNode
from kailash.nodes.data import AsyncSQLDatabaseNode

# Create Nexus with authentication
config = NexusConfig(
    name="Secure Task Manager",
    channels={
        "api": {"enabled": True},
        "cli": {"enabled": True},
        "mcp": {"enabled": True}
    }
)
app = NexusApplication(config)

# User registration workflow
register_workflow = WorkflowBuilder("user_registration")

register_workflow.add_node("ValidationNode", "validate_user", {
    "schema": {
        "type": "object",
        "properties": {
            "username": {"type": "string", "minLength": 3},
            "email": {"type": "string", "format": "email"},
            "password": {"type": "string", "minLength": 8}
        },
        "required": ["username", "email", "password"]
    }
})

register_workflow.add_node("PasswordHashNode", "hash_password", {
    "password_field": "password"
})

register_workflow.add_node("AsyncSQLDatabaseNode", "create_user", {
    "query": """
    INSERT INTO users (username, email, password_hash, created_at)
    VALUES (:username, :email, :password_hash, NOW())
    RETURNING id, username, email
    """,
    "connection_string": "${DATABASE_URL}"
})

register_workflow.add_node("JWTAuthNode", "generate_token", {
    "user_id_field": "id",
    "additional_claims": ["username", "email"]
})

# Connect the workflow
register_workflow.add_connection("validate_user", "hash_password")
register_workflow.add_connection("hash_password", "create_user")
register_workflow.add_connection("create_user", "generate_token")

app.register_workflow("user_registration", register_workflow.build())

# Login workflow
login_workflow = WorkflowBuilder("user_login")

login_workflow.add_node("AsyncSQLDatabaseNode", "find_user", {
    "query": """
    SELECT id, username, email, password_hash
    FROM users
    WHERE username = :username OR email = :username
    """,
    "connection_string": "${DATABASE_URL}"
})

login_workflow.add_node("PasswordHashNode", "verify_password", {
    "mode": "verify",
    "password_field": "password",
    "hash_field": "password_hash"
})

login_workflow.add_node("JWTAuthNode", "generate_token", {
    "user_id_field": "id",
    "additional_claims": ["username", "email"]
})

login_workflow.add_connection("find_user", "verify_password")
login_workflow.add_connection("verify_password", "generate_token")

app.register_workflow("user_login", login_workflow.build())

# Protect task operations
app.require_auth("task_operations")
```

### Using Authentication

#### API Authentication:
```bash
# Register user
curl -X POST http://localhost:8000/api/workflows/user_registration/execute \
  -H "Content-Type: application/json" \
  -d '{
    "inputs": {
        "username": "alice",
        "email": "alice@example.com",
        "password": "secure_password_123"
    }
}'

# Login
TOKEN=$(curl -X POST http://localhost:8000/api/workflows/user_login/execute \
  -H "Content-Type: application/json" \
  -d '{
    "inputs": {
        "username": "alice",
        "password": "secure_password_123"
    }
}' | jq -r '.results.token')

# Use authenticated endpoint
curl -X POST http://localhost:8000/api/workflows/task_operations/execute \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"inputs": {"title": "Secure task"}}'
```

#### CLI Authentication:
```bash
# Login via CLI
nexus login alice
# Enter password when prompted

# CLI automatically uses stored token
nexus workflow execute task_operations --title "Secure task"

# Or manually specify token
nexus --token $TOKEN workflow execute task_operations --title "Secure task"
```

## 🔄 Cross-Channel Workflows

Let's create a workflow that demonstrates cross-channel communication:

```python
from kailash_nexus import NexusConfig, NexusApplication
from kailash.workflow.builder import WorkflowBuilder
import asyncio

config = NexusConfig(
    name="Collaborative Task Manager",
    channels={
        "api": {"enabled": True},
        "cli": {"enabled": True},
        "mcp": {"enabled": True}
    }
)
app = NexusApplication(config)

# Task creation with real-time updates
collaborative_workflow = WorkflowBuilder("collaborative_task")

# ... validation and creation nodes ...

# Broadcast to all channels
collaborative_workflow.add_node("EventStreamNode", "emit_event", {
    "event_type": "task.created",
    "include_metadata": True
})

collaborative_workflow.add_node("WebSocketBroadcastNode", "notify_websocket", {
    "channel": "tasks",
    "message_template": "New task created: {title}"
})

# Send CLI notification
collaborative_workflow.add_node("PythonCodeNode", "cli_notification", {
    "code": """
# Send notification to CLI users
import os
notification = f"\\n🔔 New task: {data['title']}\\n"
# This will appear in active CLI sessions
result = {'notification': notification}
"""
})

# MCP tool notification
collaborative_workflow.add_node("MCPResourceNode", "update_mcp_state", {
    "resource_type": "task_list",
    "operation": "append",
    "data_field": "task"
})

# Connect all notifications
collaborative_workflow.add_connection("create_task", "emit_event")
collaborative_workflow.add_connection("create_task", "notify_websocket")
collaborative_workflow.add_connection("create_task", "cli_notification")
collaborative_workflow.add_connection("create_task", "update_mcp_state")

app.register_workflow("collaborative_task", collaborative_workflow.build())

# Subscribe to events in CLI
@app.cli_handler("watch")
async def watch_tasks(session):
    """Watch for real-time task updates."""
    print("👀 Watching for task updates... (Press Ctrl+C to stop)")

    async for event in app.event_stream.subscribe("task.*"):
        if event.type == "task.created":
            print(f"✨ New task: {event.data['title']}")
        elif event.type == "task.completed":
            print(f"✅ Completed: {event.data['title']}")
```

### Real-Time Updates Across Channels

When a task is created via any channel:

1. **API clients** receive WebSocket notifications
2. **CLI users** see real-time updates if watching
3. **MCP tools** get updated resource state
4. **Web dashboards** update automatically via SSE

## ⚡ Real-Time Features

### WebSocket Integration

```javascript
// Client-side WebSocket connection
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onopen = () => {
    // Authenticate
    ws.send(JSON.stringify({
        type: 'auth',
        token: localStorage.getItem('token')
    }));

    // Subscribe to events
    ws.send(JSON.stringify({
        type: 'subscribe',
        events: ['task.created', 'task.updated', 'task.completed']
    }));
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);

    switch(data.type) {
        case 'task.created':
            addTaskToUI(data.task);
            break;
        case 'task.updated':
            updateTaskInUI(data.task);
            break;
        case 'task.completed':
            markTaskComplete(data.task.id);
            break;
    }
};
```

### Server-Sent Events

```python
# Python client for SSE
import sseclient

response = requests.get(
    'http://localhost:8000/events',
    headers={'Authorization': f'Bearer {token}'},
    stream=True
)

client = sseclient.SSEClient(response)
for event in client.events():
    data = json.loads(event.data)
    print(f"Event: {event.event} - {data}")
```

## 🏢 Enterprise Configuration

For production deployments with full enterprise features:

```python
from kailash_nexus import NexusConfig, NexusApplication
import asyncio

# Enterprise configuration
config = NexusConfig(
    name="Enterprise Platform",
    channels={
        "api": {"enabled": True},
        "cli": {"enabled": True},
        "mcp": {"enabled": True}
    }
)
app = NexusApplication(config)

# Additional enterprise features can be configured
app.configure(
    database_url="postgresql://prod-cluster:5432/nexus",

    # Channel-specific settings
    channels={
        "api": {
            "rate_limit": 10000,
            "burst_limit": 15000,
            "cors_origins": ["https://*.company.com"]
        },
        "cli": {
            "require_vpn": True,
            "session_recording": True
        },
        "mcp": {
            "allowed_tools": ["approved_list"],
            "require_signed_requests": True
        }
    }
)

# Add enterprise workflows (assume these are defined elsewhere)
# app.register_workflow("compliance", compliance_workflow.build())
# app.register_workflow("audit", audit_workflow.build())
# app.register_workflow("data_governance", data_governance_workflow.build())
```

### Multi-Tenant Usage

```python
# Tenant-specific task creation workflow
tenant_task_workflow = WorkflowBuilder("tenant_task")

# Add validation
tenant_task_workflow.add_node("ValidationNode", "validate", {
    "schema": {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "description": {"type": "string"}
        },
        "required": ["title"]
    }
})

# Add tenant-aware creation
tenant_task_workflow.add_node("PythonCodeNode", "create_task", {
    "code": """
import uuid
from datetime import datetime

# Get tenant from session context
tenant_id = context.get('tenant_id', 'default')
user_id = context.get('user_id', 'anonymous')

result = {
    'id': str(uuid.uuid4()),
    'title': data['title'],
    'description': data.get('description', ''),
    'tenant_id': tenant_id,
    'created_by': user_id,
    'created_at': datetime.utcnow().isoformat()
}
"""
})

tenant_task_workflow.add_connection("validate", "create_task")

# Register the tenant-aware workflow
app.register_workflow("tenant_task", tenant_task_workflow.build())
```

## 🔧 Custom Channels

Extend Nexus with custom channels for specialized interfaces:

```python
from kailash_nexus import Channel, ChannelRequest, ChannelResponse

class VoiceChannel(Channel):
    """Voice interface channel using speech recognition."""

    def __init__(self):
        self.speech_recognizer = SpeechRecognizer()
        self.text_to_speech = TextToSpeech()
        self.nlu = NaturalLanguageProcessor()

    async def initialize(self, nexus):
        """Initialize voice channel with Nexus."""
        self.nexus = nexus

        # Register voice commands
        self.commands = {
            "create task": self._create_task,
            "list tasks": self._list_tasks,
            "complete task": self._complete_task
        }

    async def handle_request(self, request: ChannelRequest) -> ChannelResponse:
        """Process voice input."""
        # Convert speech to text
        text = await self.speech_recognizer.process(request.audio)

        # Extract intent and entities
        intent = await self.nlu.analyze(text)

        # Execute appropriate workflow
        if intent.name in self.commands:
            result = await self.commands[intent.name](intent.entities)
        else:
            result = {"message": "I didn't understand that command"}

        # Convert response to speech
        audio = await self.text_to_speech.synthesize(result['message'])

        return ChannelResponse(
            audio=audio,
            text=result.get('message'),
            data=result
        )

    async def _create_task(self, entities):
        """Create task from voice command."""
        # Execute workflow
        result = await self.nexus.execute_workflow(
            "task_operations",
            {
                "title": entities.get("task_name"),
                "priority": entities.get("priority", "medium")
            }
        )

        return {
            "message": f"Created task: {result['title']}",
            "task": result
        }

# Add voice channel to Nexus
config = NexusConfig(
    name="Voice-Enabled Task Manager",
    channels={
        "api": {"enabled": True},
        "cli": {"enabled": True},
        "mcp": {"enabled": True}
    }
)
app = NexusApplication(config)
app.add_channel("voice", VoiceChannel())

# Voice endpoint automatically available at /voice
```

## 🚀 Production Deployment

### Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application
COPY nexus_app.py .
COPY workflows/ ./workflows/

# Environment configuration
ENV NEXUS_ENV=production
ENV DATABASE_URL=postgresql://nexus:password@db:5432/nexus
ENV REDIS_URL=redis://redis:6379

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose ports
EXPOSE 8000

# Run Nexus
CMD ["python", "nexus_app.py"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  nexus:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://nexus:password@postgres:5432/nexus
      - REDIS_URL=redis://redis:6379
      - NEXUS_SECRET_KEY=${NEXUS_SECRET_KEY}
    depends_on:
      - postgres
      - redis
    volumes:
      - ./workflows:/app/workflows

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=nexus
      - POSTGRES_USER=nexus
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - nexus

volumes:
  postgres_data:
  redis_data:
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nexus
  namespace: production
spec:
  replicas: 3
  selector:
    matchLabels:
      app: nexus
  template:
    metadata:
      labels:
        app: nexus
    spec:
      containers:
      - name: nexus
        image: company/nexus:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: nexus-secrets
              key: database-url
        - name: NEXUS_ENV
          value: "production"
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

```yaml
apiVersion: v1
kind: Service
metadata:
  name: nexus-service
  namespace: production
spec:
  selector:
    app: nexus
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

## 📊 Monitoring & Observability

### Prometheus Metrics

```python
# Automatic metrics exposure
config = NexusConfig(
    name="Monitored Nexus",
    channels={
        "api": {"enabled": True},
        "cli": {"enabled": True},
        "mcp": {"enabled": True}
    }
)
app = NexusApplication(config)

# Metrics available at /metrics
# - nexus_requests_total
# - nexus_request_duration_seconds
# - nexus_active_sessions
# - nexus_workflow_executions_total
# - nexus_channel_errors_total
```

### Custom Metrics

```python
# Business workflow with custom metrics
business_workflow = WorkflowBuilder("business_process")

business_workflow.add_node("PythonCodeNode", "track_metrics", {
    "code": """
import time
from datetime import datetime

# Start timer
start_time = time.time()

# Simulate business logic
result = {
    'processed': True,
    'revenue': 1234.56,
    'product': 'premium',
    'duration': time.time() - start_time
}

# In production, metrics would be exported to monitoring system
print(f"Processed in {result['duration']:.2f} seconds")
print(f"Revenue: ${result['revenue']}")
"""
})

app.register_workflow("business_process", business_workflow.build())
```

## 🎯 Best Practices

### 1. Workflow Design
- Keep workflows focused and composable
- Use validation nodes for input checking
- Add error handling and retry logic
- Include audit logging for compliance

### 2. Security
- Always enable authentication in production
- Use least-privilege access control
- Implement rate limiting for APIs
- Enable audit logging for compliance

### 3. Performance
- Use connection pooling for databases
- Enable caching for frequently accessed data
- Implement pagination for large datasets
- Monitor and optimize slow workflows

### 4. Monitoring
- Export metrics to monitoring systems
- Set up alerts for critical errors
- Track business KPIs through custom metrics
- Use distributed tracing for debugging

## 🚦 Next Steps

You now understand how to:
- Create basic Nexus applications
- Add authentication and security
- Build cross-channel workflows
- Deploy to production
- Monitor and scale

For more advanced topics:
- [Under the Hood](UNDER_THE_HOOD.md) - Technical implementation details
- [Integration Patterns](INTEGRATION_PATTERNS.md) - Specific patterns for each channel
- [Architecture](ARCHITECTURE.md) - Deep dive into Nexus internals

---

**Ready to build?** Start with our [example applications](../examples/) or explore the [API reference](/api/docs).
