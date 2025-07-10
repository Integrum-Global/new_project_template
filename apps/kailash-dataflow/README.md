# Kailash DataFlow

**Zero-Config Database Framework** - Django simplicity meets enterprise-grade production quality.

[![Tests](https://img.shields.io/badge/tests-passing-brightgreen)](tests/)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
[![SDK](https://img.shields.io/badge/built%20with-Kailash%20SDK-orange)](../README.md)

## 🚀 Quick Start (60 seconds)

```python
from kailash_dataflow import DataFlow

# That's it! No configuration needed
db = DataFlow()

# Define your model
@db.model
class User:
    id: int
    name: str
    email: str

# DataFlow automatically creates:
# ✅ Database (SQLite for dev, PostgreSQL for prod)
# ✅ 9 workflow nodes per model (CRUD + bulk ops)
# ✅ MongoDB-style query builder with cross-database support
# ✅ Redis query cache with pattern-based invalidation
# ✅ Migrations and connection pooling
# ✅ Transaction management
# ✅ Monitoring and protection
```

You now have a production-ready database layer!

## 🎯 What Makes DataFlow Different?

### Zero Configuration That Actually Works
```python
# Development? Uses SQLite automatically
db = DataFlow()  # Just works!

# Production? Reads from environment
# DATABASE_URL=postgresql://...
db = DataFlow()  # Still just works!

# Need control? Progressive enhancement
db = DataFlow(
    pool_size=50,
    read_replicas=['replica1', 'replica2'],
    monitoring=True
)
```

### MongoDB-Style Query Building
```python
# Traditional ORMs: Database-specific syntax
User.objects.filter(age__gt=18, status="active")  # Django
session.query(User).filter(User.age > 18, User.status == "active")  # SQLAlchemy

# DataFlow: MongoDB-style queries for any database
builder = User.query_builder()
builder.where("age", "$gt", 18)
builder.where("status", "$eq", "active")
sql, params = builder.build_select(["name", "email"])
# Works with PostgreSQL, MySQL, SQLite automatically!
```

### Redis Query Caching
```python
# Automatic query result caching
db = DataFlow(enable_query_cache=True)

# First call executes query
result = User.cached_query("SELECT * FROM users WHERE age > $1", [21])

# Second call returns cached result
result = User.cached_query("SELECT * FROM users WHERE age > $1", [21])  # Cache hit!

# Smart cache invalidation
user.update({"age": 25})  # Automatically invalidates related cache entries
```

### Database Operations as Workflow Nodes
```python
# Traditional ORMs: Imperative code
user = User.objects.create(name="Alice")  # Django
user = User(name="Alice"); session.add(user)  # SQLAlchemy

# DataFlow: Workflow-native (9 nodes per model!)
workflow = WorkflowBuilder()
workflow.add_node("UserCreateNode", "create_user", {
    "name": "Alice",
    "email": "alice@example.com"
})
workflow.add_node("UserListNode", "find_users", {
    "filter": {"name": {"$like": "A%"}}
})
```

### Enterprise Features Built-In
```python
# Multi-tenancy with automatic query isolation
db = DataFlow(multi_tenant=True)

# Queries automatically include tenant_id
builder = User.query_builder()
builder.where("status", "$eq", "active")
# Generates: SELECT * FROM users WHERE tenant_id = $1 AND status = $2

# Redis caching with tenant isolation
result = User.cached_query(
    "SELECT * FROM users WHERE status = $1",
    ["active"],
    tenant_id="tenant_123"
)

# Automatic cache invalidation by tenant
db.get_query_cache().invalidate_table("users", tenant_id="tenant_123")

# Built-in monitoring with cache metrics
db = DataFlow(
    monitoring=True,
    slow_query_threshold=1.0,
    cache_invalidation_strategy="pattern_based"
)
```

## 📚 Documentation

### Getting Started
- **[5-Minute Tutorial](docs/getting-started/quickstart.md)** - Build your first app
- **[Core Concepts](docs/getting-started/concepts.md)** - Understand DataFlow
- **[Examples](examples/)** - Complete applications

### Development
- **[Models](docs/development/models.md)** - Define your schema
- **[CRUD Operations](docs/development/crud.md)** - Basic operations
- **[Relationships](docs/development/relationships.md)** - Model associations

### Production
- **[Deployment](docs/production/deployment.md)** - Go to production
- **[Performance](docs/production/performance.md)** - Optimization guide
- **[Monitoring](docs/advanced/monitoring.md)** - Observability

## 💡 Real-World Examples

### E-Commerce Platform
```python
# Define your models
@db.model
class Product:
    id: int
    name: str
    price: float
    stock: int

@db.model
class Order:
    id: int
    user_id: int
    total: float
    status: str

# Use in workflows
workflow = WorkflowBuilder()

# Check inventory
workflow.add_node("ProductGetNode", "check_stock", {
    "id": "{product_id}"
})

# Create order with transaction
workflow.add_node("TransactionContextNode", "tx_start")
workflow.add_node("OrderCreateNode", "create_order", {
    "user_id": "{user_id}",
    "total": "{total}"
})
workflow.add_node("ProductUpdateNode", "update_stock", {
    "id": "{product_id}",
    "stock": "{new_stock}"
})
```

### Multi-Tenant SaaS with Smart Caching
```python
# Enable multi-tenancy with Redis caching
db = DataFlow(
    multi_tenant=True,
    enable_query_cache=True,
    cache_invalidation_strategy="pattern_based"
)

# Build tenant-isolated queries
builder = User.query_builder()
builder.where("status", "$in", ["active", "premium"])
builder.where("created_at", "$gte", "2024-01-01")

# Automatic tenant isolation in cache
result = User.cached_query(
    "SELECT * FROM users WHERE status IN ($1, $2)",
    ["active", "premium"],
    tenant_id="acme-corp"
)

# Cache invalidation respects tenant boundaries
db.get_query_cache().invalidate_table("users", tenant_id="acme-corp")
```

### High-Performance ETL with Query Optimization
```python
# Bulk operations for millions of records
workflow.add_node("UserBulkCreateNode", "import_users", {
    "data": users_data,  # List of 1M+ users
    "batch_size": 10000,
    "parallel": True
})

# Optimized queries with automatic caching
builder = db.build_query("users")
builder.where("status", "$eq", "active")
builder.where("last_login", "$gte", "2024-01-01")
sql, params = builder.build_select(["id", "email", "metadata"])

# Stream processing with cached intermediate results
workflow.add_node("UserStreamNode", "process_users", {
    "query": sql,
    "parameters": params,
    "chunk_size": 1000,
    "cache_results": True
})
```

## 🏗️ Architecture

DataFlow seamlessly integrates with Kailash's workflow architecture:

```
┌─────────────────────────────────────────────────────┐
│                 Your Application                     │
├─────────────────────────────────────────────────────┤
│                    DataFlow                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐         │
│  │  Models  │  │   Nodes  │  │ Migrations│         │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘         │
│       └──────────────┴──────────────┘               │
│                Core Features                         │
│  QueryBuilder │ QueryCache │ Monitoring │ Multi-tenant │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐         │
│  │MongoDB-  │  │Redis     │  │Pattern   │         │
│  │style     │  │Caching   │  │Invalidate│         │
│  └──────────┘  └──────────┘  └──────────┘         │
├─────────────────────────────────────────────────────┤
│               Kailash SDK                           │
│         Workflows │ Nodes │ Runtime                 │
└─────────────────────────────────────────────────────┘
```

## 🧪 Testing

DataFlow includes comprehensive testing support:

```python
# Test with in-memory database
def test_user_creation():
    db = DataFlow(testing=True)

    @db.model
    class User:
        id: int
        name: str

    # Automatic test isolation
    user = db.test_create(User, name="Test User")
    assert user.name == "Test User"
```

## 🤝 Contributing

We welcome contributions! DataFlow follows Kailash SDK patterns:

1. Use SDK components and patterns
2. Maintain zero-config philosophy
3. Write comprehensive tests
4. Update documentation

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## 📊 Performance

DataFlow is optimized for real-world performance:

- **10k+ transactions/second** on modest hardware
- **Sub-millisecond** connection pooling
- **Automatic query optimization**
- **Built-in caching** where appropriate

See [benchmarks/](benchmarks/) for detailed results.

## ⚡ Why DataFlow?

- **Zero Configuration**: Actually works with no setup
- **Workflow-Native**: Database ops as first-class nodes
- **Production-Ready**: Enterprise features built-in
- **Progressive**: Simple to start, powerful when needed
- **100% Kailash**: No external dependencies

---

**Built with Kailash SDK** | [Parent Project](../../README.md) | [SDK Docs](../../sdk-users/)
