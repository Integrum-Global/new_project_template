# Nexus Integration Patterns

## Channel-Specific Patterns for API, CLI, and MCP

This guide provides detailed patterns and best practices for integrating with each Nexus channel. Whether you're building REST APIs, command-line tools, or AI agent integrations, these patterns will help you leverage the full power of Nexus.

## 📡 API Channel Patterns

### RESTful API Design

#### Standard CRUD Operations

```python
from kailash_nexus import create_nexus
from kailash.workflow.builder import WorkflowBuilder

nexus = create_nexus(title="Product API")

# Create product workflow
create_product = WorkflowBuilder("create_product")
create_product.add_node("ValidationNode", "validate", {
    "schema": {
        "type": "object",
        "properties": {
            "name": {"type": "string", "minLength": 1},
            "price": {"type": "number", "minimum": 0},
            "category": {"type": "string"}
        },
        "required": ["name", "price"]
    }
})

create_product.add_node("AsyncSQLDatabaseNode", "insert", {
    "query": """
    INSERT INTO products (name, price, category, created_at)
    VALUES (:name, :price, :category, NOW())
    RETURNING *
    """,
    "connection_string": "${DATABASE_URL}"
})

create_product.add_connection("validate", "insert")
nexus.register_workflow(create_product)

# Automatic REST endpoints:
# POST   /api/workflows/create_product/execute
# GET    /api/workflows/create_product/schema
# GET    /api/workflows/create_product/status/{run_id}
```

#### Resource-Based APIs

```python
# Define resource with full CRUD
@nexus.resource("products")
class ProductResource:
    """Product resource with automatic API generation."""

    model = {
        "id": "uuid",
        "name": "string",
        "price": "number",
        "category": "string",
        "created_at": "datetime",
        "updated_at": "datetime"
    }

    # Automatic endpoints:
    # GET    /api/products           - List all
    # GET    /api/products/{id}      - Get one
    # POST   /api/products           - Create
    # PUT    /api/products/{id}      - Update
    # DELETE /api/products/{id}      - Delete
    # PATCH  /api/products/{id}      - Partial update

    # Custom actions
    @action(method="POST")
    async def bulk_import(self, data: List[Dict]) -> Dict:
        """POST /api/products/bulk_import"""
        workflow = self.nexus.get_workflow("bulk_product_import")
        result = await workflow.execute({"products": data})
        return {"imported": len(result["imported"]), "errors": result["errors"]}

    @action(method="GET")
    async def by_category(self, category: str) -> List[Dict]:
        """GET /api/products/by_category?category=electronics"""
        return await self.query({"category": category})
```

### WebSocket Patterns

#### Real-Time Subscriptions

```python
# Server-side WebSocket handling
@nexus.websocket_handler
async def handle_product_updates(websocket, session):
    """Handle real-time product subscriptions."""

    # Client subscribes to specific events
    message = await websocket.recv()
    subscription = json.loads(message)

    if subscription["action"] == "subscribe":
        categories = subscription.get("categories", [])

        # Subscribe to filtered events
        async for event in nexus.event_stream.subscribe(
            "product.*",
            filter=lambda e: not categories or e.data.get("category") in categories
        ):
            await websocket.send(json.dumps({
                "type": "product_update",
                "action": event.type.split(".")[-1],  # created, updated, deleted
                "product": event.data
            }))
```

#### Client-Side WebSocket

```javascript
// JavaScript client
class ProductWebSocket {
    constructor(token) {
        this.ws = new WebSocket('ws://localhost:8000/ws');
        this.token = token;
        this.handlers = {};
    }

    connect() {
        this.ws.onopen = () => {
            // Authenticate
            this.send({
                type: 'auth',
                token: this.token
            });

            // Subscribe to product updates
            this.send({
                action: 'subscribe',
                categories: ['electronics', 'books']
            });
        };

        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);

            if (data.type === 'product_update') {
                this.handleProductUpdate(data);
            }
        };
    }

    handleProductUpdate(data) {
        // Update UI based on action
        switch(data.action) {
            case 'created':
                this.onProductCreated?.(data.product);
                break;
            case 'updated':
                this.onProductUpdated?.(data.product);
                break;
            case 'deleted':
                this.onProductDeleted?.(data.product);
                break;
        }
    }

    send(data) {
        this.ws.send(JSON.stringify(data));
    }
}
```

### Server-Sent Events (SSE)

```python
# Server-side SSE streaming
@nexus.sse_endpoint("/events/products")
async def stream_product_events(request, session):
    """Stream product events to clients."""

    async def event_generator():
        # Send initial state
        products = await nexus.execute_workflow("list_products", {})
        yield {
            "event": "initial",
            "data": json.dumps(products["results"])
        }

        # Stream updates
        async for event in nexus.event_stream.subscribe("product.*"):
            yield {
                "event": event.type,
                "data": json.dumps(event.data),
                "id": event.id
            }

    return EventSourceResponse(event_generator())
```

```javascript
// Client-side SSE
const eventSource = new EventSource('/events/products', {
    headers: {
        'Authorization': `Bearer ${token}`
    }
});

eventSource.addEventListener('product.created', (event) => {
    const product = JSON.parse(event.data);
    addProductToList(product);
});

eventSource.addEventListener('product.updated', (event) => {
    const product = JSON.parse(event.data);
    updateProductInList(product);
});
```

### GraphQL Integration

```python
# GraphQL schema with Nexus workflows
graphql_schema = """
type Product {
    id: ID!
    name: String!
    price: Float!
    category: String
    inventory: Int
}

type Query {
    products(category: String, limit: Int): [Product!]!
    product(id: ID!): Product
}

type Mutation {
    createProduct(input: ProductInput!): Product!
    updateProduct(id: ID!, input: ProductInput!): Product!
    deleteProduct(id: ID!): Boolean!
}

type Subscription {
    productUpdates(categories: [String!]): Product!
}
"""

@nexus.graphql_resolver
class ProductResolver:
    """GraphQL resolver using Nexus workflows."""

    async def products(self, category: str = None, limit: int = 100):
        """Query resolver for products."""
        result = await nexus.execute_workflow("list_products", {
            "filter": {"category": category} if category else {},
            "limit": limit
        })
        return result["products"]

    async def create_product(self, input: dict):
        """Mutation resolver for creating products."""
        result = await nexus.execute_workflow("create_product", input)
        return result["product"]

    async def product_updates(self, categories: List[str] = None):
        """Subscription resolver for real-time updates."""
        async for event in nexus.event_stream.subscribe("product.*"):
            if not categories or event.data.get("category") in categories:
                yield event.data
```

## 💻 CLI Channel Patterns

### Command Structure

#### Basic Commands

```python
# Define CLI commands that map to workflows
@nexus.cli_command("product")
class ProductCommands:
    """Product management commands."""

    @command("create")
    @option("--name", required=True, help="Product name")
    @option("--price", type=float, required=True, help="Product price")
    @option("--category", help="Product category")
    async def create_product(self, name: str, price: float, category: str = None):
        """Create a new product."""
        result = await nexus.execute_workflow("create_product", {
            "name": name,
            "price": price,
            "category": category
        })

        click.echo(f"✅ Created product: {result['product']['id']}")
        click.echo(f"   Name: {result['product']['name']}")
        click.echo(f"   Price: ${result['product']['price']}")

    @command("list")
    @option("--category", help="Filter by category")
    @option("--format", type=click.Choice(["table", "json", "csv"]), default="table")
    async def list_products(self, category: str = None, format: str = "table"):
        """List all products."""
        result = await nexus.execute_workflow("list_products", {
            "filter": {"category": category} if category else {}
        })

        if format == "table":
            self._print_table(result["products"])
        elif format == "json":
            click.echo(json.dumps(result["products"], indent=2))
        elif format == "csv":
            self._print_csv(result["products"])
```

#### Interactive CLI

```python
@nexus.cli_command("interactive")
class InteractiveCLI:
    """Interactive product management shell."""

    @command("shell")
    async def start_shell(self):
        """Start interactive shell."""
        click.echo("🚀 Nexus Interactive Shell")
        click.echo("Type 'help' for commands, 'exit' to quit")

        session = await nexus.create_cli_session()

        while True:
            try:
                # Prompt with context
                prompt = f"nexus ({session.user_id})> "
                command = await ainput(prompt)

                if command == "exit":
                    break
                elif command == "help":
                    self._show_help()
                else:
                    # Parse and execute command
                    result = await self._execute_command(command, session)
                    self._display_result(result)

            except KeyboardInterrupt:
                click.echo("\nUse 'exit' to quit")
            except Exception as e:
                click.echo(f"❌ Error: {e}", err=True)

    async def _execute_command(self, command: str, session):
        """Parse and execute interactive command."""
        parts = shlex.split(command)
        if not parts:
            return

        cmd_name = parts[0]
        args = parts[1:]

        # Map to workflow
        workflow_map = {
            "create": "create_product",
            "list": "list_products",
            "update": "update_product",
            "delete": "delete_product"
        }

        if cmd_name in workflow_map:
            workflow_id = workflow_map[cmd_name]
            inputs = self._parse_args(args)
            return await nexus.execute_workflow(workflow_id, inputs, session)
```

### Batch Processing

```python
@nexus.cli_command("batch")
class BatchCommands:
    """Batch processing commands."""

    @command("import")
    @argument("file", type=click.Path(exists=True))
    @option("--format", type=click.Choice(["csv", "json", "xlsx"]), default="csv")
    @option("--dry-run", is_flag=True, help="Validate without importing")
    async def import_products(self, file: str, format: str, dry_run: bool):
        """Import products from file."""

        # Read file
        products = await self._read_file(file, format)
        click.echo(f"📁 Found {len(products)} products to import")

        # Validate
        validation_result = await nexus.execute_workflow("validate_bulk_products", {
            "products": products
        })

        if validation_result["errors"]:
            click.echo("❌ Validation errors:", err=True)
            for error in validation_result["errors"]:
                click.echo(f"   - Row {error['row']}: {error['message']}", err=True)

            if dry_run or not click.confirm("Continue with valid products?"):
                return

        if dry_run:
            click.echo("✅ Dry run complete - no data imported")
            return

        # Import with progress bar
        with click.progressbar(
            length=len(products),
            label="Importing products"
        ) as bar:
            result = await nexus.execute_workflow("bulk_import_products", {
                "products": products,
                "progress_callback": lambda p: bar.update(p.completed)
            })

        click.echo(f"✅ Imported {result['imported']} products")
        if result["errors"]:
            click.echo(f"⚠️  {len(result['errors'])} errors - see import.log")
```

### CLI Automation

```python
# Scriptable CLI for automation
@nexus.cli_command("script")
class ScriptCommands:
    """Automation and scripting commands."""

    @command("run")
    @argument("script_file", type=click.Path(exists=True))
    @option("--vars", type=click.Path(exists=True), help="Variables file")
    async def run_script(self, script_file: str, vars: str = None):
        """Run automation script."""

        # Load script
        with open(script_file) as f:
            script = yaml.safe_load(f)

        # Load variables
        variables = {}
        if vars:
            with open(vars) as f:
                variables = yaml.safe_load(f)

        # Execute script steps
        context = ScriptContext(variables)

        for step in script["steps"]:
            click.echo(f"▶️  {step['name']}")

            # Execute workflow
            result = await nexus.execute_workflow(
                step["workflow"],
                self._resolve_variables(step.get("inputs", {}), context)
            )

            # Store result in context
            if step.get("register"):
                context.set(step["register"], result)

            # Check conditions
            if step.get("when") and not self._evaluate_condition(step["when"], context):
                click.echo("   ⏭️  Skipped (condition not met)")
                continue

            click.echo("   ✅ Complete")
```

## 🤖 MCP Channel Patterns

### Tool Registration

```python
# Register workflows as MCP tools
@nexus.mcp_tool("product_manager")
class ProductManagerTool:
    """Product management tool for AI agents."""

    description = "Manages products in the inventory system"

    @tool_function("create_product")
    async def create_product(
        self,
        name: str,
        price: float,
        category: str = None,
        description: str = None
    ) -> Dict:
        """
        Create a new product in the inventory.

        Args:
            name: Product name
            price: Product price in USD
            category: Optional product category
            description: Optional product description

        Returns:
            The created product with ID
        """
        result = await nexus.execute_workflow("create_product", {
            "name": name,
            "price": price,
            "category": category,
            "description": description
        })

        return {
            "success": True,
            "product_id": result["product"]["id"],
            "message": f"Created product '{name}' with ID {result['product']['id']}"
        }

    @tool_function("search_products")
    async def search_products(
        self,
        query: str = None,
        category: str = None,
        min_price: float = None,
        max_price: float = None,
        limit: int = 10
    ) -> List[Dict]:
        """
        Search for products matching criteria.

        Args:
            query: Text search query
            category: Filter by category
            min_price: Minimum price filter
            max_price: Maximum price filter
            limit: Maximum results to return

        Returns:
            List of matching products
        """
        filters = {}
        if query:
            filters["name"] = {"$like": f"%{query}%"}
        if category:
            filters["category"] = category
        if min_price is not None:
            filters["price"] = {"$gte": min_price}
        if max_price is not None:
            filters.setdefault("price", {})["$lte"] = max_price

        result = await nexus.execute_workflow("search_products", {
            "filters": filters,
            "limit": limit
        })

        return result["products"]
```

### Resource Access

```python
@nexus.mcp_resource("product_catalog")
class ProductCatalogResource:
    """Product catalog resource for AI agents."""

    description = "Access to current product catalog"

    @resource_getter
    async def get_catalog(self, format: str = "summary") -> Dict:
        """
        Get current product catalog.

        Args:
            format: Output format (summary, detailed, csv)

        Returns:
            Product catalog in requested format
        """
        products = await nexus.execute_workflow("list_all_products", {})

        if format == "summary":
            return {
                "total_products": len(products["products"]),
                "categories": self._count_by_category(products["products"]),
                "price_range": self._get_price_range(products["products"])
            }
        elif format == "detailed":
            return products
        elif format == "csv":
            return {
                "content_type": "text/csv",
                "content": self._to_csv(products["products"])
            }

    @resource_watcher
    async def watch_changes(self) -> AsyncIterator[Dict]:
        """Watch for catalog changes in real-time."""
        async for event in nexus.event_stream.subscribe("product.*"):
            yield {
                "event": event.type,
                "product": event.data,
                "timestamp": event.metadata["timestamp"]
            }
```

### Service Discovery

```python
# Dynamic service registration
@nexus.mcp_service("analytics")
class AnalyticsService:
    """Analytics service for AI agents."""

    capabilities = {
        "product_analytics": True,
        "sales_forecasting": True,
        "inventory_optimization": True
    }

    @service_method("analyze_product_performance")
    async def analyze_performance(
        self,
        product_id: str,
        time_period: str = "30d"
    ) -> Dict:
        """Analyze product performance metrics."""

        # Execute analytics workflow
        result = await nexus.execute_workflow("product_analytics", {
            "product_id": product_id,
            "time_period": time_period,
            "metrics": ["sales", "revenue", "returns", "rating"]
        })

        return {
            "product_id": product_id,
            "period": time_period,
            "metrics": result["metrics"],
            "insights": result["insights"],
            "recommendations": result["recommendations"]
        }

    @service_method("forecast_demand")
    async def forecast_demand(
        self,
        product_id: str,
        horizon: int = 30
    ) -> Dict:
        """Forecast product demand."""

        result = await nexus.execute_workflow("demand_forecasting", {
            "product_id": product_id,
            "horizon_days": horizon
        })

        return {
            "product_id": product_id,
            "forecast": result["forecast"],
            "confidence_intervals": result["confidence_intervals"],
            "seasonality": result["seasonality"]
        }
```

### AI Agent Integration

```python
# Integration with popular AI frameworks
class NexusMCPAdapter:
    """Adapter for AI agent frameworks."""

    def __init__(self, nexus_url: str, api_key: str):
        self.client = MCPClient(nexus_url, api_key)

    async def for_langchain(self):
        """Create LangChain tools from MCP."""
        from langchain.tools import Tool

        tools = []
        for tool_info in await self.client.list_tools():
            tool = Tool(
                name=tool_info["name"],
                description=tool_info["description"],
                func=lambda **kwargs: asyncio.run(
                    self.client.call_tool(tool_info["name"], kwargs)
                )
            )
            tools.append(tool)

        return tools

    async def for_autogen(self):
        """Create AutoGen functions from MCP."""
        functions = []
        for tool_info in await self.client.list_tools():
            functions.append({
                "name": tool_info["name"],
                "description": tool_info["description"],
                "parameters": tool_info["input_schema"],
                "function": partial(self.client.call_tool, tool_info["name"])
            })

        return functions
```

## 🔄 Cross-Channel Patterns

### Unified Authentication

```python
# Single sign-on across channels
class UnifiedAuth:
    """Authentication that works across all channels."""

    @nexus.auth_provider
    async def authenticate(self, credentials: Dict, channel: str) -> AuthResult:
        """Authenticate user for any channel."""

        # Common authentication logic
        user = await self._verify_credentials(credentials)
        if not user:
            raise AuthenticationError("Invalid credentials")

        # Generate channel-appropriate token
        if channel == "api":
            token = await self._generate_jwt(user)
        elif channel == "cli":
            token = await self._generate_cli_token(user)
        elif channel == "mcp":
            token = await self._generate_mcp_bearer(user)

        # Create unified session
        session = await nexus.create_session(
            user_id=user.id,
            channel=channel,
            metadata={
                "ip_address": credentials.get("ip_address"),
                "user_agent": credentials.get("user_agent"),
                "authenticated_at": datetime.utcnow()
            }
        )

        return AuthResult(
            token=token,
            session_id=session.id,
            expires_at=session.expires_at
        )
```

### Event-Driven Synchronization

```python
# Synchronize state across channels
class CrossChannelSync:
    """Synchronize events across all channels."""

    @nexus.event_handler("product.*")
    async def sync_product_changes(self, event: NexusEvent):
        """Propagate product changes to all channels."""

        # Notify API clients via WebSocket
        await nexus.websocket_broadcast({
            "type": "product_update",
            "action": event.type.split(".")[-1],
            "data": event.data
        })

        # Update CLI sessions
        for cli_session in nexus.get_active_cli_sessions():
            if cli_session.watching("products"):
                await cli_session.notify(
                    f"Product {event.data['name']} was {event.type.split('.')[-1]}"
                )

        # Notify MCP subscribers
        await nexus.mcp_notify_resource_change(
            "product_catalog",
            {
                "change_type": event.type,
                "product": event.data
            }
        )
```

### Workflow Orchestration

```python
# Complex workflows spanning multiple channels
@nexus.workflow("multi_channel_campaign")
class MultiChannelCampaign:
    """Marketing campaign across all channels."""

    async def execute(self, campaign_data: Dict):
        """Execute multi-channel campaign."""

        # 1. Create campaign via API
        campaign = await self.create_campaign(campaign_data)

        # 2. Schedule CLI automation
        await nexus.cli_schedule_task(
            "generate_reports",
            schedule="0 9 * * *",  # Daily at 9 AM
            args={
                "campaign_id": campaign["id"],
                "recipients": campaign_data["report_recipients"]
            }
        )

        # 3. Register MCP tool for AI analysis
        await nexus.mcp_register_temporary_tool(
            name=f"campaign_{campaign['id']}_analyzer",
            description=f"Analyze performance of campaign {campaign['name']}",
            function=partial(self.analyze_campaign, campaign["id"]),
            ttl=campaign_data["duration_days"] * 86400
        )

        # 4. Setup real-time monitoring
        await self.setup_monitoring(campaign["id"])

        return {
            "campaign_id": campaign["id"],
            "api_endpoints": self.get_api_endpoints(campaign["id"]),
            "cli_commands": self.get_cli_commands(campaign["id"]),
            "mcp_tools": [f"campaign_{campaign['id']}_analyzer"]
        }
```

## 📋 Best Practices

### 1. Channel Selection
- **API**: Best for web applications, mobile apps, and third-party integrations
- **CLI**: Ideal for automation, DevOps, and power users
- **MCP**: Perfect for AI agents, chatbots, and intelligent automation

### 2. Security Considerations
- Always validate inputs at the channel level
- Use channel-appropriate authentication methods
- Implement rate limiting per channel
- Audit all cross-channel operations

### 3. Performance Optimization
- Cache frequently accessed data at channel level
- Use appropriate serialization (JSON for API, MessagePack for MCP)
- Implement pagination for large datasets
- Consider async operations for long-running tasks

### 4. Error Handling
- Provide channel-appropriate error messages
- Use proper HTTP status codes for API
- Return structured errors for CLI
- Include recovery suggestions for MCP

### 5. Documentation
- Generate OpenAPI specs for API channels
- Provide CLI help and man pages
- Export MCP tool descriptions
- Maintain cross-channel consistency

## 🎯 Integration Examples

### Example 1: E-commerce Platform
```python
# API for web frontend
# CLI for inventory management
# MCP for AI customer service
```

### Example 2: DevOps Platform
```python
# API for dashboards
# CLI for automation scripts
# MCP for intelligent alerts
```

### Example 3: Data Analytics Platform
```python
# API for visualizations
# CLI for data pipelines
# MCP for AI-driven insights
```

---

**Ready to integrate?** Check out our [example applications](../examples/) or dive into the [API documentation](/api/docs).
