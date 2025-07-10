# DataFlow Model Definition

Comprehensive guide to defining and managing database models in DataFlow.

## Basic Model Definition

DataFlow models are Python classes with type hints that define your database schema:

```python
from kailash_dataflow import DataFlow
from datetime import datetime
from typing import Optional, List

db = DataFlow()

@db.model
class User:
    # Required fields
    name: str
    email: str
    age: int

    # Optional fields with defaults
    active: bool = True
    created_at: datetime  # Auto-handled by DataFlow
    profile: Optional[str] = None
```

## Supported Field Types

### Basic Types
```python
@db.model
class Product:
    # String fields
    name: str
    description: Optional[str] = None

    # Numeric fields
    price: float
    stock: int

    # Boolean fields
    active: bool = True
    featured: bool = False

    # Date/time fields
    created_at: datetime
    updated_at: Optional[datetime] = None
```

### Advanced Types
```python
from decimal import Decimal
from uuid import UUID

@db.model
class Order:
    # UUID primary key
    id: UUID

    # Decimal for precise currency
    total: Decimal

    # JSON data
    metadata: dict

    # Arrays (PostgreSQL)
    tags: List[str]

    # Enum-like fields
    status: str = "pending"  # pending, processing, completed
```

## Model Configuration

### DataFlow Options
```python
@db.model
class Customer:
    name: str
    email: str

    # DataFlow-specific configuration
    __dataflow__ = {
        'soft_delete': True,      # Adds deleted_at field
        'versioned': True,        # Adds version field for optimistic locking
        'multi_tenant': True,     # Adds tenant_id field
        'timestamps': True,       # Adds created_at, updated_at
        'audit_log': True,        # Enables audit logging
        'encrypted_fields': ['email'],  # Encrypt sensitive fields
    }
```

### Database Indexes
```python
@db.model
class BlogPost:
    title: str
    content: str
    author_id: int
    published: bool = False
    published_at: Optional[datetime] = None

    # Index definitions
    __indexes__ = [
        # Simple index
        {'name': 'idx_author', 'fields': ['author_id']},

        # Composite index
        {'name': 'idx_published', 'fields': ['published', 'published_at']},

        # Unique index
        {'name': 'idx_title_author', 'fields': ['title', 'author_id'], 'unique': True},

        # Partial index (PostgreSQL)
        {'name': 'idx_published_posts', 'fields': ['published_at'], 'condition': 'published = true'},

        # Text search index
        {'name': 'idx_content_search', 'fields': ['title', 'content'], 'type': 'gin'},
    ]
```

### Table Configuration
```python
@db.model
class Analytics:
    event_type: str
    user_id: int
    timestamp: datetime
    data: dict

    # Table-level configuration
    __table_config__ = {
        'table_name': 'analytics_events',  # Custom table name
        'schema': 'analytics',             # Database schema
        'comment': 'User analytics events',
        'engine': 'InnoDB',               # MySQL engine
        'charset': 'utf8mb4',             # Character set
        'partitioned': True,              # Enable partitioning
        'partition_by': 'timestamp',      # Partition field
    }
```

## Model Relationships

### Foreign Key Relationships
```python
@db.model
class User:
    name: str
    email: str

@db.model
class Order:
    user_id: int  # Foreign key to User
    total: float
    status: str = "pending"

    # Relationship metadata (optional)
    __relationships__ = {
        'user': {
            'model': 'User',
            'foreign_key': 'user_id',
            'type': 'many_to_one'
        }
    }
```

### One-to-Many Relationships
```python
@db.model
class Customer:
    name: str
    email: str

@db.model
class Order:
    customer_id: int
    total: float

    __relationships__ = {
        'customer': {
            'model': 'Customer',
            'foreign_key': 'customer_id',
            'type': 'many_to_one'
        }
    }

# Access in workflows
workflow.add_node("OrderListNode", "customer_orders", {
    "filter": {"customer_id": 123},
    "include": ["customer"]  # Include related customer data
})
```

## Model Validation

### Field Validation
```python
@db.model
class Product:
    name: str
    price: float
    category: str

    # Validation rules
    __validation__ = {
        'name': {
            'min_length': 3,
            'max_length': 100,
            'required': True
        },
        'price': {
            'min_value': 0.01,
            'max_value': 999999.99,
            'required': True
        },
        'category': {
            'choices': ['electronics', 'clothing', 'books', 'home'],
            'required': True
        }
    }
```

### Custom Validation
```python
@db.model
class User:
    name: str
    email: str
    age: int

    # Custom validation methods
    def validate_email(self, value: str) -> bool:
        """Validate email format."""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, value) is not None

    def validate_age(self, value: int) -> bool:
        """Validate age is reasonable."""
        return 0 <= value <= 150

    __validators__ = {
        'email': validate_email,
        'age': validate_age
    }
```

## Model Migration

### Automatic Migrations
```python
# DataFlow automatically detects changes
@db.model
class User:
    name: str
    email: str
    age: int
    # Adding new field - migration created automatically
    phone: Optional[str] = None
```

### Manual Migrations
```python
# Create custom migration
def migrate_add_phone_column():
    """Add phone column to users table."""
    return """
    ALTER TABLE users ADD COLUMN phone VARCHAR(20);
    CREATE INDEX idx_users_phone ON users(phone);
    """

# Register migration
db.register_migration("add_phone_column", migrate_add_phone_column)
```

## Model Inheritance

### Base Models
```python
@db.model
class BaseModel:
    """Base model with common fields."""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    __dataflow__ = {
        'timestamps': True,
        'abstract': True  # This model won't create a table
    }

@db.model
class User(BaseModel):
    """User model inheriting from BaseModel."""
    name: str
    email: str
```

### Mixins
```python
class TimestampMixin:
    """Mixin for timestamp fields."""
    created_at: datetime
    updated_at: Optional[datetime] = None

class SoftDeleteMixin:
    """Mixin for soft delete functionality."""
    deleted_at: Optional[datetime] = None

    __dataflow__ = {
        'soft_delete': True
    }

@db.model
class Product(TimestampMixin, SoftDeleteMixin):
    """Product with timestamps and soft delete."""
    name: str
    price: float
```

## Advanced Model Features

### Computed Fields
```python
@db.model
class Order:
    subtotal: float
    tax_rate: float
    shipping: float

    # Computed fields
    __computed__ = {
        'tax_amount': 'subtotal * tax_rate',
        'total': 'subtotal + (subtotal * tax_rate) + shipping'
    }
```

### JSON Fields
```python
@db.model
class UserProfile:
    user_id: int
    preferences: dict  # JSON field
    settings: dict     # JSON field

    # JSON field validation
    __json_schemas__ = {
        'preferences': {
            'type': 'object',
            'properties': {
                'theme': {'type': 'string', 'enum': ['light', 'dark']},
                'notifications': {'type': 'boolean'}
            }
        }
    }
```

### Encrypted Fields
```python
@db.model
class User:
    name: str
    email: str
    ssn: str

    # Encryption configuration
    __dataflow__ = {
        'encrypted_fields': ['ssn'],
        'encryption_key': 'env:ENCRYPTION_KEY'
    }
```

## Model Caching

### Cache Configuration
```python
@db.model
class Product:
    name: str
    price: float

    # Cache configuration
    __cache__ = {
        'enabled': True,
        'ttl': 300,  # 5 minutes
        'key_pattern': 'product:{id}',
        'invalidate_on': ['update', 'delete']
    }
```

### Cache Strategies
```python
@db.model
class User:
    name: str
    email: str

    __cache__ = {
        'strategy': 'write_through',  # write_through, write_back, write_around
        'ttl': 600,
        'tags': ['user', 'auth']
    }
```

## Model Events

### Lifecycle Hooks
```python
@db.model
class User:
    name: str
    email: str

    def before_create(self):
        """Called before creating a user."""
        self.email = self.email.lower()

    def after_create(self):
        """Called after creating a user."""
        # Send welcome email
        pass

    def before_update(self):
        """Called before updating a user."""
        self.updated_at = datetime.now()

    def after_delete(self):
        """Called after deleting a user."""
        # Cleanup related data
        pass
```

### Event Listeners
```python
@db.model
class Order:
    customer_id: int
    total: float
    status: str = "pending"

    # Event listeners
    __events__ = {
        'after_create': ['send_order_confirmation', 'update_inventory'],
        'status_changed': ['notify_customer', 'update_analytics']
    }
```

## Model Testing

### Model Factories
```python
# Create test data factory
def create_user_factory():
    """Factory for creating test users."""
    return {
        "name": "Test User",
        "email": "test@example.com",
        "age": 25,
        "active": True
    }

# Use in tests
workflow.add_node("UserCreateNode", "create_test_user", create_user_factory())
```

### Model Fixtures
```python
# Load test fixtures
def load_user_fixtures():
    """Load user test fixtures."""
    return [
        {"name": "Alice", "email": "alice@test.com", "age": 30},
        {"name": "Bob", "email": "bob@test.com", "age": 25},
        {"name": "Charlie", "email": "charlie@test.com", "age": 35}
    ]

# Use in tests
workflow.add_node("UserBulkCreateNode", "load_test_users", {
    "data": load_user_fixtures()
})
```

## Model Performance

### Optimization Tips
```python
@db.model
class Product:
    name: str
    price: float
    category: str

    # Performance optimizations
    __indexes__ = [
        {'name': 'idx_category_price', 'fields': ['category', 'price']},
        {'name': 'idx_price_range', 'fields': ['price'], 'type': 'btree'}
    ]

    __cache__ = {
        'enabled': True,
        'ttl': 3600,
        'key_pattern': 'product:{id}:{category}'
    }
```

### Bulk Operations
```python
# Efficient bulk operations
workflow.add_node("ProductBulkCreateNode", "import_products", {
    "data": product_list,
    "batch_size": 1000,
    "conflict_resolution": "skip"
})
```

## Model Monitoring

### Performance Metrics
```python
@db.model
class User:
    name: str
    email: str

    # Monitoring configuration
    __monitoring__ = {
        'enabled': True,
        'track_queries': True,
        'slow_query_threshold': 1.0,
        'metrics': ['query_time', 'cache_hits', 'cache_misses']
    }
```

## Best Practices

### 1. Naming Conventions
```python
# Good naming
@db.model
class UserProfile:
    user_id: int
    first_name: str
    last_name: str
    email_address: str

# Avoid
@db.model
class usrprof:  # Too abbreviated
    uid: int
    fn: str
    ln: str
```

### 2. Field Organization
```python
@db.model
class Order:
    # IDs first
    id: int
    customer_id: int

    # Core fields
    total: float
    status: str

    # Metadata
    notes: Optional[str] = None

    # Timestamps last
    created_at: datetime
    updated_at: Optional[datetime] = None
```

### 3. Index Strategy
```python
@db.model
class Product:
    name: str
    price: float
    category: str

    # Index common query patterns
    __indexes__ = [
        {'name': 'idx_category', 'fields': ['category']},           # Category queries
        {'name': 'idx_price_range', 'fields': ['price']},          # Price range queries
        {'name': 'idx_category_price', 'fields': ['category', 'price']}, # Combined queries
    ]
```

### 4. Validation Strategy
```python
@db.model
class User:
    name: str
    email: str
    age: int

    # Combine built-in and custom validation
    __validation__ = {
        'name': {'min_length': 2, 'max_length': 100},
        'email': {'required': True, 'format': 'email'},
        'age': {'min_value': 0, 'max_value': 150}
    }
```

## Next Steps

- **CRUD Operations**: [CRUD Guide](crud.md)
- **Workflow Integration**: [Workflow Guide](../workflows/nodes.md)
- **Bulk Operations**: [Bulk Operations Guide](bulk-operations.md)
- **Production Deployment**: [Deployment Guide](../production/deployment.md)

DataFlow models provide a powerful, type-safe way to define your database schema while maintaining the flexibility and performance needed for modern applications.
