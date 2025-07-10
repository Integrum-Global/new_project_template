# DataFlow Core Concepts

Understanding the fundamental concepts behind DataFlow to build effective database applications.

## What is DataFlow?

DataFlow is a workflow-native database framework that treats database operations as first-class nodes in Kailash workflows. Unlike traditional ORMs that operate in request-response cycles, DataFlow operates in workflow lifecycles.

## Key Concepts

### 1. Model-Driven Development

DataFlow uses Python classes with type hints to define your data models:

```python
from kailash_dataflow import DataFlow
from datetime import datetime
from typing import Optional

db = DataFlow()

@db.model
class User:
    name: str
    email: str
    age: int
    active: bool = True
    created_at: datetime
    profile: Optional[str] = None
```

The framework automatically:
- Creates database tables
- Generates workflow nodes
- Handles migrations
- Provides type safety

### 2. Workflow-Scoped Connections

Traditional ORMs create connections per request:
```
Request → Connection → Operation → Close Connection
```

DataFlow creates connections per workflow:
```
Workflow Start → Connection → Multiple Operations → Workflow End
```

This provides:
- Better performance (fewer connection overhead)
- Automatic transaction boundaries
- Consistent data state throughout workflow

### 3. Generated Nodes

For each model, DataFlow automatically generates these workflow nodes:

#### Basic CRUD Operations
- **CreateNode**: Insert single records
- **ReadNode**: Fetch single records by ID
- **UpdateNode**: Modify existing records
- **DeleteNode**: Remove records
- **ListNode**: Query multiple records with filters

#### High-Performance Bulk Operations
- **BulkCreateNode**: Insert thousands of records efficiently
- **BulkUpdateNode**: Update multiple records with conditions
- **BulkDeleteNode**: Remove multiple records safely
- **BulkUpsertNode**: Insert or update records intelligently

### 4. Workflow Integration

Database operations integrate seamlessly with Kailash workflows:

```python
from kailash.workflow.builder import WorkflowBuilder
from kailash.runtime.local import LocalRuntime

# Create workflow
workflow = WorkflowBuilder()

# Add database operations as nodes
workflow.add_node("UserCreateNode", "create_user", {
    "name": "Alice",
    "email": "alice@example.com",
    "age": 30
})

workflow.add_node("UserListNode", "list_users", {
    "filter": {"active": True},
    "order_by": ["-created_at"],
    "limit": 10
})

# Execute workflow
runtime = LocalRuntime()
results, run_id = runtime.execute(workflow.build())
```

### 5. Automatic Data Safety

DataFlow provides built-in data protection:

#### Transaction Management
- Automatic transaction boundaries
- Rollback on failures
- Consistent data state

#### Bulk Operation Safety
- Automatic chunking for large datasets
- Progress tracking
- Error recovery
- Cleanup on failures

#### Connection Management
- Automatic connection pooling
- Health monitoring
- Failover support

### 6. Query Building

DataFlow includes a MongoDB-style query builder:

```python
from kailash.nodes.data import create_query_builder

# Create query builder
builder = create_query_builder("postgresql")

# Build complex queries
builder.table("users").where("age", "$gt", 18).where("status", "$eq", "active")

# Generate optimized SQL
sql, params = builder.build_select(["name", "email", "created_at"])
```

### 7. Caching Layer

Built-in Redis caching for high performance:

```python
from kailash.nodes.data import create_query_cache

# Create cache
cache = create_query_cache("redis://localhost:6379")

# Cache query results
cached_result = cache.get_or_execute(
    key="active_users",
    query_func=lambda: get_active_users(),
    ttl=300  # 5 minutes
)
```

### 8. Multi-Tenancy

Native multi-tenant support:

```python
db = DataFlow(multi_tenant=True)

@db.model
class Customer:
    name: str
    email: str
    # tenant_id added automatically

    __dataflow__ = {
        'multi_tenant': True,
        'tenant_isolation': 'strict'
    }
```

### 9. Monitoring and Observability

Built-in monitoring and metrics:

```python
db = DataFlow(
    monitoring=True,
    metrics_export="prometheus",
    slow_query_threshold=1.0
)

# Access monitoring data
monitor = db.get_monitor()
metrics = monitor.get_metrics()
health = monitor.get_health_status()
```

## DataFlow vs Traditional ORMs

### Traditional ORM Approach
```python
# Django ORM
from django.db import models, transaction

class User(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()

# Manual transaction management
with transaction.atomic():
    user = User.objects.create(name="Alice", email="alice@example.com")
    # Process user...
    user.save()
```

### DataFlow Approach
```python
# DataFlow
from kailash_dataflow import DataFlow

db = DataFlow()

@db.model
class User:
    name: str
    email: str

# Automatic transaction management in workflow
workflow.add_node("UserCreateNode", "create_user", {
    "name": "Alice",
    "email": "alice@example.com"
})
```

## Performance Characteristics

### Connection Efficiency
- **Traditional**: 1 connection per request
- **DataFlow**: 1 connection per workflow (can span multiple operations)

### Bulk Operations
- **Traditional**: Manual optimization required
- **DataFlow**: Database-specific optimization automatic

### Caching
- **Traditional**: Manual cache management
- **DataFlow**: Built-in intelligent caching

### Monitoring
- **Traditional**: External tools required
- **DataFlow**: Built-in metrics and monitoring

## Development Workflow

### 1. Define Models
```python
@db.model
class Product:
    name: str
    price: float
    category: str
    stock: int
```

### 2. Use in Workflows
```python
workflow.add_node("ProductCreateNode", "create_product", {
    "name": "iPhone 15",
    "price": 999.99,
    "category": "electronics",
    "stock": 100
})
```

### 3. Execute and Monitor
```python
runtime = LocalRuntime()
results, run_id = runtime.execute(workflow.build())

# Monitor performance
print(f"Workflow {run_id} completed in {results['execution_time']}s")
```

## Configuration Options

### Basic Configuration
```python
# Zero configuration
db = DataFlow()
```

### Production Configuration
```python
# Full configuration
db = DataFlow(
    database_url="postgresql://user:pass@localhost/db",
    pool_size=20,
    pool_max_overflow=50,
    monitoring=True,
    multi_tenant=True,
    cache_enabled=True,
    security_enabled=True
)
```

## Best Practices

### 1. Model Design
- Use clear, descriptive names
- Leverage type hints for validation
- Define appropriate indexes
- Use DataFlow features (soft_delete, versioning)

### 2. Workflow Patterns
- Keep workflows focused and modular
- Use bulk operations for large datasets
- Leverage automatic transaction boundaries
- Monitor performance metrics

### 3. Production Deployment
- Use environment variables for configuration
- Enable monitoring and alerting
- Configure appropriate connection pooling
- Set up health checks

### 4. Error Handling
- Let DataFlow handle automatic retries
- Monitor failure patterns
- Use built-in recovery mechanisms
- Log important events

## Next Steps

- **Quick Start**: [Quickstart Guide](quickstart.md)
- **Model Definition**: [Model Guide](../development/models.md)
- **Workflow Integration**: [Workflow Guide](../workflows/nodes.md)
- **Production Setup**: [Deployment Guide](../production/deployment.md)

## Summary

DataFlow transforms database operations from imperative code into declarative workflow nodes, providing:

✅ **Automatic Safety**: Built-in transaction management and error recovery
✅ **High Performance**: Workflow-scoped connections and bulk optimizations
✅ **Zero Configuration**: Works out of the box with intelligent defaults
✅ **Enterprise Ready**: Multi-tenancy, monitoring, and security built-in
✅ **Type Safety**: Full Python type hints and validation

Understanding these concepts will help you build robust, high-performance database applications with DataFlow.
