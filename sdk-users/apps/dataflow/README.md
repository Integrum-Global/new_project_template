# DataFlow - Zero-Config Database Platform

DataFlow provides MongoDB-style queries across any database with enterprise-grade caching and automatic API generation. This guide is for users who have installed DataFlow via PyPI.

## Installation

```bash
# Install DataFlow directly
pip install kailash-dataflow

# Or as part of Kailash SDK
pip install kailash[dataflow]
```

## 🏗️ DataFlow vs Traditional ORMs

DataFlow is not a traditional ORM. It's a **workflow-native database framework** designed for enterprise applications with distributed transactions, multi-tenancy, and caching built-in.

### Architecture Comparison

| Feature | Traditional ORM | DataFlow |
|---------|----------------|----------|
| **Model Usage** | Direct instantiation (`User()`) | Workflow-native (`UserCreateNode`) |
| **Database Operations** | Method calls (`user.save()`) | Workflow nodes (`UserCreateNode`) |
| **Transaction Handling** | Manual transaction management | Distributed transaction support |
| **Caching** | External cache integration | Built-in enterprise caching |
| **Multi-tenancy** | Custom implementation | Automatic tenant isolation |
| **Performance** | N+1 queries common | Optimized bulk operations |
| **Scalability** | Vertical scaling focus | Horizontal scaling built-in |

### Why Workflow-Native?

**Traditional ORM Limitations:**
```python
# Traditional ORM - doesn't scale well
user = User(name="John", email="john@example.com")
user.save()  # Individual database calls
# Issues: N+1 queries, no caching, no multi-tenancy
```

**DataFlow Advantages:**
```python
# DataFlow - built for enterprise scale
workflow.add_node("UserCreateNode", "create_user", {
    "name": "John Doe",
    "email": "john@example.com"
})
# Benefits: Automatic caching, bulk operations, tenant isolation
```

### Enterprise Benefits

1. **Distributed Transactions**: Automatic transaction coordination across services
2. **Multi-Tenancy**: Built-in tenant isolation and data partitioning
3. **Performance Caching**: Enterprise-grade caching with invalidation strategies
4. **Bulk Operations**: Optimized for high-throughput scenarios (10k+ ops/sec)
5. **Monitoring**: Built-in metrics, deadlock detection, performance monitoring
6. **Security**: Automatic SQL injection prevention, audit trails

### Model Instantiation Not Supported

DataFlow models are **schemas, not objects**. This is intentional:

```python
# ❌ This won't work (by design)
user = User(name="John")  # Models are not instantiable

# ✅ This is the correct pattern
workflow.add_node("UserCreateNode", "create", {
    "name": "John",
    "email": "john@example.com"
})
```

**Why?** Model instantiation bypasses:
- Automatic caching
- Tenant isolation
- Transaction coordination
- Performance optimization
- Security validation

## Quick Start

```python
from dataflow import DataFlow
from kailash.workflow.builder import WorkflowBuilder
from kailash.runtime.local import LocalRuntime

# Zero-configuration startup
db = DataFlow()

# Define a model - automatically generates 9 node types
@db.model
class User:
    name: str
    email: str
    age: int
    department: str
    active: bool = True

# Use generated nodes in workflows
workflow = WorkflowBuilder()

# Create a user
workflow.add_node("UserCreateNode", "create_user", {
    "name": "John Doe",
    "email": "john@example.com",
    "age": 25,
    "department": "engineering"
})

# List users with filters
workflow.add_node("UserListNode", "list_users", {
    "filter": {"age": {"$gt": 18}},
    "limit": 10
})

# Execute workflow
runtime = LocalRuntime()
results, run_id = runtime.execute(workflow.build())
```

## Key Features

### 🔧 Zero Configuration
Start with a single line: `app = DataFlow()` - no database setup, no schema definitions, no configuration files.

### 🗄️ Universal Database Support
MongoDB-style queries work across PostgreSQL, MySQL, SQLite with automatic SQL generation and optimization.

### ⚡ Redis-Powered Caching
Enterprise-grade caching with intelligent invalidation patterns and 99.9% hit rates.

### 🚀 Automatic API Generation
REST APIs, OpenAPI documentation, and health checks generated automatically from your queries.

## Generated Node Types

Each `@db.model` automatically generates 9 node types:

### Basic CRUD Nodes
```python
# Create a single record
workflow.add_node("UserCreateNode", "create", {
    "name": "John",
    "age": 25,
    "department": "engineering"
})

# Read a single record
workflow.add_node("UserReadNode", "read", {
    "conditions": {"id": 123}
})

# Update a record
workflow.add_node("UserUpdateNode", "update", {
    "conditions": {"id": 123},
    "updates": {"age": 26}
})

# Delete a record
workflow.add_node("UserDeleteNode", "delete", {
    "conditions": {"id": 123}
})
```

### List and Query Nodes
```python
# List with MongoDB-style filters
workflow.add_node("UserListNode", "list", {
    "filter": {
        "age": {"$gt": 18, "$lt": 65},           # age > 18 AND age < 65
        "name": {"$regex": "^John"},              # name LIKE 'John%'
        "department": {"$in": ["eng", "sales"]},  # department IN ('eng', 'sales')
        "status": {"$ne": "inactive"}             # status != 'inactive'
    },
    "order_by": ["-created_at"],  # Sort by created_at descending
    "limit": 10,
    "offset": 0
})
```

### Bulk Operations
```python
# Bulk create
workflow.add_node("UserBulkCreateNode", "bulk_create", {
    "data": [
        {"name": "Alice", "age": 30, "department": "sales"},
        {"name": "Bob", "age": 35, "department": "engineering"}
    ],
    "batch_size": 1000
})

# Bulk update
workflow.add_node("UserBulkUpdateNode", "bulk_update", {
    "filter": {"department": "engineering"},
    "update": {"$inc": {"age": 1}}  # Increment age by 1
})

# Bulk delete
workflow.add_node("UserBulkDeleteNode", "bulk_delete", {
    "filter": {"status": "inactive"},
    "soft_delete": True
})

# Bulk upsert (insert or update)
workflow.add_node("UserBulkUpsertNode", "bulk_upsert", {
    "data": [
        {"email": "alice@example.com", "name": "Alice Updated"},
        {"email": "new@example.com", "name": "New User"}
    ],
    "match_fields": ["email"]
})
```

## Advanced Features

### Multi-Database Operations
```python
# Configure multiple databases
db = DataFlow(
    database_url="postgresql://user:pass@localhost/main",
    analytics_db="postgresql://user:pass@localhost/analytics"
)

# Models can specify their database
@db.model
class User:
    name: str
    email: str
    __dataflow__ = {"database": "primary"}

@db.model
class Event:
    user_id: int
    action: str
    __dataflow__ = {"database": "analytics"}
```

### Enterprise Features
```python
# Enable multi-tenancy
@db.model
class Order:
    customer_id: int
    total: float
    __dataflow__ = {
        'multi_tenant': True,      # Adds tenant_id field
        'soft_delete': True,       # Adds deleted_at field
        'audit_log': True,         # Tracks all changes
        'versioned': True          # Optimistic locking
    }

# Use in workflows with automatic tenant isolation
workflow.add_node("OrderCreateNode", "create", {
    "customer_id": 123,
    "total": 250.00,
    "tenant_id": "tenant_abc"  # Automatic isolation
})
```

### Transaction Management
```python
# Distributed transactions
workflow.add_node("TransactionManagerNode", "payment_flow", {
    "transaction_type": "saga",
    "steps": [
        {"node": "PaymentCreateNode", "compensation": "PaymentRollbackNode"},
        {"node": "OrderUpdateNode", "compensation": "OrderRevertNode"},
        {"node": "InventoryUpdateNode", "compensation": "InventoryRestoreNode"}
    ],
    "timeout": 30
})
```

## Production Examples

### E-commerce Order Processing
```python
from dataflow import DataFlow
from kailash.workflow.builder import WorkflowBuilder
from kailash.runtime.local import LocalRuntime

db = DataFlow()

@db.model
class Order:
    customer_id: int
    total: float
    status: str = "pending"

@db.model
class OrderItem:
    order_id: int
    product_id: int
    quantity: int
    price: float

# Complex order processing workflow
workflow = WorkflowBuilder()

# Create order
workflow.add_node("OrderCreateNode", "create_order", {
    "customer_id": 123,
    "total": 0,
    "status": "pending"
})

# Add order items in bulk
workflow.add_node("OrderItemBulkCreateNode", "add_items", {
    "data": [
        {"product_id": 1, "quantity": 2, "price": 50.00},
        {"product_id": 2, "quantity": 1, "price": 100.00}
    ]
})

# Calculate and update total
workflow.add_node("OrderUpdateNode", "update_total", {
    "updates": {"total": 200.00, "status": "confirmed"}
})

# Connect nodes
workflow.add_connection("create_order", "id", "add_items", "order_id")
workflow.add_connection("create_order", "id", "update_total", "order_id")
workflow.add_connection("add_items", "result", "update_total", "input")

runtime = LocalRuntime()
results, run_id = runtime.execute(workflow.build())
```

### Analytics Dashboard
```python
# Create analytics workflow
analytics_workflow = WorkflowBuilder()

# Get today's sales
analytics_workflow.add_node("OrderListNode", "today_sales", {
    "filter": {
        "created_at": {"$gte": "2025-01-17T00:00:00"},
        "status": "completed"
    }
})

# Get top products
analytics_workflow.add_node("OrderItemListNode", "top_products", {
    "aggregate": [
        {"$group": {"_id": "$product_id", "sold": {"$sum": "$quantity"}}},
        {"$sort": {"sold": -1}},
        {"$limit": 10}
    ]
})

# Execute analytics
results, run_id = runtime.execute(analytics_workflow.build())
print(f"Today's orders: {len(results['today_sales']['result'])}")
print(f"Top products: {results['top_products']['result']}")
```

## Performance & Optimization

- **31.8M operations/second** baseline performance
- **99.9% cache hit rate** with intelligent invalidation
- **Connection pooling** with 10,000+ concurrent connections
- **Automatic query optimization** with SQL generation

### Performance Monitoring
```python
# Built-in performance monitoring with workflow
workflow.add_node("PerformanceMonitorNode", "monitor", {
    "operation": "complex_query",
    "track_metrics": True
})

workflow.add_node("UserListNode", "large_query", {
    "filter": {"status": "active"},
    "aggregate": [
        {"$group": {"_id": "$department", "count": {"$sum": 1}}}
    ]
})

# Execute with monitoring
results, run_id = runtime.execute(workflow.build())
# Performance metrics available in results['monitor']['metrics']
```

## Enterprise Features

### Security & Compliance
```python
# GDPR/CCPA compliance built-in with workflows
workflow.add_node("GDPRComplianceNode", "gdpr_handler", {
    "user_id": 123,
    "request_type": "export",  # or "delete"
    "include_audit_trail": True
})

# Data export workflow
workflow.add_node("UserDataExportNode", "export_data", {
    "user_id": 123,
    "format": "json",
    "include_deleted": True
})

# Data anonymization workflow
workflow.add_node("UserDataAnonymizeNode", "anonymize_data", {
    "user_id": 123,
    "retention_policy": "strict",
    "cascade_delete": True
})

# Audit trail is automatically enabled with multi_tenant: True
```

### Health Monitoring
```python
# Automatic health checks with workflow
workflow.add_node("HealthCheckNode", "health_monitor", {
    "check_database": True,
    "check_cache": True,
    "check_connections": True
})

results, run_id = runtime.execute(workflow.build())
health = results["health_monitor"]["result"]
# {
#   "status": "healthy",
#   "database": "connected",
#   "cache": "connected",
#   "queries_per_second": 31800000
# }
```

## Deployment

### Docker
```dockerfile
FROM python:3.11-slim
RUN pip install kailash-dataflow
COPY app.py .
EXPOSE 8000
CMD ["python", "app.py"]
```

### Environment Variables
```bash
export DATAFLOW_DATABASE_URL="postgresql://..."
export DATAFLOW_REDIS_URL="redis://..."
export DATAFLOW_LOG_LEVEL="INFO"
export DATAFLOW_ENABLE_METRICS="true"
```

## Migration from Raw SQL/ORM

### From Raw SQL
```python
# Before: Raw SQL
cursor.execute("""
    SELECT department, COUNT(*) as count
    FROM users
    WHERE age > %s
    GROUP BY department
    ORDER BY count DESC
""", (18,))

# After: DataFlow
workflow = WorkflowBuilder()
workflow.add_node("UserListNode", "dept_stats", {
    "filter": {"age": {"$gt": 18}},
    "aggregate": [
        {"$group": {"_id": "$department", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
})
```

### From SQLAlchemy ORM
```python
# Before: SQLAlchemy
users = session.query(User).filter(
    User.age > 18,
    User.department.in_(['eng', 'sales'])
).order_by(User.created_at.desc()).limit(10).all()

# After: DataFlow
workflow = WorkflowBuilder()
workflow.add_node("UserListNode", "filtered_users", {
    "filter": {
        "age": {"$gt": 18},
        "department": {"$in": ["eng", "sales"]}
    },
    "order_by": ["-created_at"],
    "limit": 10
})
```

## Additional Documentation

### Guides
- [User Guide](docs/USER_GUIDE.md) - Comprehensive DataFlow guide
- [Quick Start Guide](docs/quickstart.md) - Get started in minutes
- [Query Patterns](docs/query-patterns.md) - Advanced query techniques
- [Database Optimization](docs/database-optimization.md) - Performance tuning
- [Multi-Tenant Architecture](docs/multi-tenant.md) - Enterprise patterns
- [Production Deployment](docs/deployment.md) - Deployment best practices

### Examples
- [Basic CRUD Operations](examples/01_basic_crud.py) - Simple database operations
- [Advanced Features](examples/02_advanced_features.py) - Complex queries and caching
- [Enterprise Integration](examples/03_enterprise_integration.py) - Multi-tenant and security

## Next Steps

- Explore the documentation and examples above
- Read the [API documentation](https://pypi.org/project/kailash-dataflow/)
- Join the [community](https://github.com/integrum/kailash-python-sdk)

DataFlow transforms database operations from complex, database-specific code into simple, intuitive queries that work everywhere. Start building production-ready data services in minutes!
