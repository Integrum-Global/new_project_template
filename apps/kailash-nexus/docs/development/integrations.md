# Custom Integrations

Extend Nexus capabilities with custom channels, workflows, and external system integrations.

## Quick Start

```python
from kailash_nexus import create_nexus
from kailash.nexus.channels import BaseChannel

# Create custom channel
class MyCustomChannel(BaseChannel):
    def __init__(self, config):
        super().__init__(config)
        self.setup_custom_protocol()

    async def handle_request(self, request):
        # Custom request handling
        workflow_result = await self.execute_workflow(request.workflow_id, request.data)
        return self.format_response(workflow_result)

# Register with Nexus
nexus = create_nexus()
nexus.add_channel("custom", MyCustomChannel, {"port": 9000})
```

## Channel Development

### Base Channel Interface
```python
from kailash.nexus.channels import BaseChannel

class WebSocketChannel(BaseChannel):
    channel_type = "websocket"

    def __init__(self, config):
        super().__init__(config)
        self.websocket_server = None

    async def start(self):
        """Start the channel server"""
        self.websocket_server = await websockets.serve(
            self.handle_websocket,
            self.config["host"],
            self.config["port"]
        )

    async def stop(self):
        """Stop the channel server"""
        if self.websocket_server:
            self.websocket_server.close()
            await self.websocket_server.wait_closed()

    async def handle_websocket(self, websocket, path):
        """Handle WebSocket connections"""
        try:
            async for message in websocket:
                request = self.parse_request(message)
                result = await self.execute_workflow(
                    request["workflow_id"],
                    request["data"]
                )
                await websocket.send(self.format_response(result))
        except Exception as e:
            await websocket.send(self.format_error(e))
```

### Authentication Integration
```python
class AuthenticatedChannel(BaseChannel):
    def __init__(self, config):
        super().__init__(config)
        self.auth_provider = self.create_auth_provider(config["auth"])

    async def authenticate_request(self, request):
        """Authenticate incoming requests"""
        token = self.extract_token(request)
        user = await self.auth_provider.validate_token(token)
        if not user:
            raise AuthenticationError("Invalid token")
        return user

    async def handle_request(self, request):
        user = await self.authenticate_request(request)
        request.user = user
        return await super().handle_request(request)
```

## External System Integration

### Database Integration
```python
from kailash.workflow.builder import WorkflowBuilder

# Custom database node
class CustomDatabaseNode:
    def __init__(self, config):
        self.connection_string = config["connection_string"]
        self.connection_pool = None

    async def execute(self, context):
        query = context.get_parameter("query")
        params = context.get_parameter("params", {})

        async with self.connection_pool.acquire() as conn:
            result = await conn.fetch(query, **params)

        return {"data": result, "count": len(result)}

# Register with workflow
workflow = WorkflowBuilder()
workflow.register_node_type("CustomDatabaseNode", CustomDatabaseNode)
workflow.add_node("CustomDatabaseNode", "db_query", {
    "connection_string": "postgresql://...",
    "query": "SELECT * FROM users WHERE active = $1",
    "params": {"active": True}
})
```

### Message Queue Integration
```python
import asyncio
from kailash.nexus.integrations import BaseIntegration

class RabbitMQIntegration(BaseIntegration):
    def __init__(self, config):
        super().__init__(config)
        self.connection = None
        self.channel = None

    async def connect(self):
        """Connect to RabbitMQ"""
        self.connection = await aio_pika.connect_robust(
            self.config["connection_string"]
        )
        self.channel = await self.connection.channel()

    async def publish_message(self, queue_name, message):
        """Publish message to queue"""
        await self.channel.default_exchange.publish(
            aio_pika.Message(json.dumps(message).encode()),
            routing_key=queue_name
        )

    async def consume_messages(self, queue_name, callback):
        """Consume messages from queue"""
        queue = await self.channel.declare_queue(queue_name)
        await queue.consume(callback)

# Use in workflow
class MessageProcessorNode:
    def __init__(self, config):
        self.rabbitmq = RabbitMQIntegration(config["rabbitmq"])

    async def execute(self, context):
        message = context.get_parameter("message")
        queue = context.get_parameter("queue")

        await self.rabbitmq.publish_message(queue, message)
        return {"status": "published", "queue": queue}
```

### API Gateway Integration
```python
from kailash.nexus.middleware import BaseMiddleware

class APIGatewayMiddleware(BaseMiddleware):
    def __init__(self, config):
        super().__init__(config)
        self.gateway_url = config["gateway_url"]
        self.api_key = config["api_key"]

    async def process_request(self, request):
        """Forward request to API gateway"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.gateway_url}/workflows/{request.workflow_id}",
                json=request.data,
                headers=headers
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return self.create_response(result)
                else:
                    raise IntegrationError(f"Gateway error: {response.status}")
```

## Monitoring Integration

### Custom Metrics
```python
from kailash.nexus.monitoring import BaseMonitor

class PrometheusMonitor(BaseMonitor):
    def __init__(self, config):
        super().__init__(config)
        self.metrics_registry = prometheus_client.CollectorRegistry()
        self.request_counter = prometheus_client.Counter(
            'nexus_requests_total',
            'Total requests',
            ['channel', 'workflow'],
            registry=self.metrics_registry
        )
        self.request_duration = prometheus_client.Histogram(
            'nexus_request_duration_seconds',
            'Request duration',
            ['channel', 'workflow'],
            registry=self.metrics_registry
        )

    async def record_request(self, channel, workflow, duration):
        """Record request metrics"""
        self.request_counter.labels(
            channel=channel,
            workflow=workflow
        ).inc()

        self.request_duration.labels(
            channel=channel,
            workflow=workflow
        ).observe(duration)

    def get_metrics(self):
        """Export metrics for Prometheus"""
        return prometheus_client.generate_latest(self.metrics_registry)
```

### Health Check Integration
```python
from kailash.nexus.health import BaseHealthCheck

class DatabaseHealthCheck(BaseHealthCheck):
    def __init__(self, config):
        super().__init__(config)
        self.database_url = config["database_url"]

    async def check_health(self):
        """Check database connectivity"""
        try:
            async with asyncpg.connect(self.database_url) as conn:
                result = await conn.fetchval("SELECT 1")
                return {
                    "status": "healthy",
                    "component": "database",
                    "response_time": self.last_check_duration
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "component": "database",
                "error": str(e)
            }

# Register health checks
nexus.add_health_check("database", DatabaseHealthCheck, {
    "database_url": "postgresql://..."
})
```

## Configuration Management

### Environment-based Configuration
```python
import os
from kailash.nexus.config import BaseConfig

class ProductionConfig(BaseConfig):
    def __init__(self):
        super().__init__()
        self.database_url = os.getenv("DATABASE_URL")
        self.redis_url = os.getenv("REDIS_URL")
        self.secret_key = os.getenv("SECRET_KEY")
        self.log_level = os.getenv("LOG_LEVEL", "INFO")

    def validate(self):
        """Validate required configuration"""
        required = ["database_url", "redis_url", "secret_key"]
        missing = [key for key in required if not getattr(self, key)]
        if missing:
            raise ConfigurationError(f"Missing required config: {missing}")

# Use configuration
nexus = create_nexus(config=ProductionConfig())
```

### Dynamic Configuration
```python
class DynamicConfig:
    def __init__(self, config_source):
        self.config_source = config_source
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes

    async def get_config(self, key):
        """Get configuration with caching"""
        if key in self.cache:
            cached_value, timestamp = self.cache[key]
            if time.time() - timestamp < self.cache_ttl:
                return cached_value

        # Fetch from source
        value = await self.config_source.get(key)
        self.cache[key] = (value, time.time())
        return value

    async def watch_config(self, key, callback):
        """Watch for configuration changes"""
        await self.config_source.watch(key, callback)
```

## Security Integration

### OAuth2 Integration
```python
from kailash.nexus.auth import BaseAuthProvider

class OAuth2Provider(BaseAuthProvider):
    def __init__(self, config):
        super().__init__(config)
        self.client_id = config["client_id"]
        self.client_secret = config["client_secret"]
        self.token_url = config["token_url"]
        self.userinfo_url = config["userinfo_url"]

    async def validate_token(self, token):
        """Validate OAuth2 token"""
        headers = {"Authorization": f"Bearer {token}"}

        async with aiohttp.ClientSession() as session:
            async with session.get(self.userinfo_url, headers=headers) as response:
                if response.status == 200:
                    user_info = await response.json()
                    return self.create_user(user_info)
                else:
                    return None

    def create_user(self, user_info):
        """Create user from OAuth2 response"""
        return {
            "id": user_info["sub"],
            "email": user_info["email"],
            "name": user_info["name"],
            "roles": user_info.get("roles", [])
        }
```

### Rate Limiting
```python
from kailash.nexus.middleware import RateLimitMiddleware

class RedisRateLimiter(RateLimitMiddleware):
    def __init__(self, config):
        super().__init__(config)
        self.redis_client = redis.Redis.from_url(config["redis_url"])
        self.rate_limit = config["requests_per_minute"]

    async def check_rate_limit(self, user_id):
        """Check if user is within rate limits"""
        key = f"rate_limit:{user_id}"
        current = await self.redis_client.get(key)

        if current is None:
            await self.redis_client.setex(key, 60, 1)
            return True

        if int(current) >= self.rate_limit:
            return False

        await self.redis_client.incr(key)
        return True
```

## Testing Integrations

```python
import pytest
from kailash.nexus.testing import NexusTestClient

@pytest.fixture
def nexus_client():
    """Create test client"""
    nexus = create_nexus(config=TestConfig())
    return NexusTestClient(nexus)

async def test_custom_channel(nexus_client):
    """Test custom channel integration"""
    # Test custom channel
    response = await nexus_client.custom.send_message({
        "workflow_id": "test_workflow",
        "data": {"message": "hello"}
    })

    assert response["status"] == "success"
    assert "result" in response

async def test_external_integration(nexus_client):
    """Test external system integration"""
    # Mock external system
    with nexus_client.mock_external("database"):
        response = await nexus_client.api.post("/process", {
            "query": "SELECT * FROM users"
        })

        assert response.status_code == 200
        assert len(response.json()["data"]) > 0
```

## Best Practices

1. **Channel Design**: Keep channels stateless and lightweight
2. **Error Handling**: Implement comprehensive error handling and recovery
3. **Security**: Always validate and authenticate external inputs
4. **Performance**: Use async patterns and connection pooling
5. **Monitoring**: Add metrics and health checks for all integrations
6. **Testing**: Mock external dependencies in tests
7. **Configuration**: Use environment-based configuration for flexibility
8. **Documentation**: Document integration APIs and configuration options

## Examples

### Slack Integration
```python
class SlackChannel(BaseChannel):
    async def handle_slack_event(self, event):
        if event["type"] == "message":
            workflow_id = "slack_responder"
            data = {"message": event["text"], "user": event["user"]}
            result = await self.execute_workflow(workflow_id, data)
            await self.send_slack_message(event["channel"], result["response"])
```

### Webhook Integration
```python
class WebhookChannel(BaseChannel):
    async def handle_webhook(self, request):
        signature = request.headers.get("X-Signature")
        if not self.verify_signature(request.body, signature):
            raise AuthenticationError("Invalid signature")

        payload = request.json()
        workflow_id = payload.get("workflow_id", "default")
        result = await self.execute_workflow(workflow_id, payload["data"])
        return {"status": "processed", "result": result}
```

## Next Steps

- **Workflow Development**: [Workflow Guide](workflow-guide.md) - Build channel-agnostic workflows
- **Testing**: [Testing Guide](testing.md) - Test integration patterns
- **Enterprise**: [Enterprise Setup](../enterprise/setup.md) - Production deployment
- **Security**: [Security & Authentication](../enterprise/security.md) - Secure integrations
