# DataFlow Quick Start Guide

Build a complete database-backed application in 5 minutes!

## Prerequisites

- Python 3.8 or higher
- Kailash SDK installed (`pip install kailash`)

## Step 1: Create Your First Model

```python
from datetime import datetime
from kailash_dataflow import DataFlow

# Zero configuration - it just works!
db = DataFlow()

# Define a model
@db.model
class Task:
    title: str
    description: str
    completed: bool = False
    # Note: id and created_at are added automatically by DataFlow
```

That's it! DataFlow has automatically:
- Created an in-memory SQLite database
- Generated 9 workflow nodes for Task operations
- Set up connection pooling and migrations

## Step 2: Use in a Workflow

```python
from kailash.workflow.builder import WorkflowBuilder
from kailash.runtime.local import LocalRuntime

# Create a workflow
workflow = WorkflowBuilder()

# Add a task
workflow.add_node("TaskCreateNode", "create_task", {
    "title": "Learn DataFlow",
    "description": "Complete the quickstart guide"
})

# List all tasks
workflow.add_node("TaskListNode", "list_tasks", {
    "filter": {"completed": False}
})

# Execute
runtime = LocalRuntime()
results, run_id = runtime.execute(workflow.build())

print(results["list_tasks"]["data"])
# [{"id": 1, "title": "Learn DataFlow", "completed": false, ...}]
```

## Step 3: CRUD Operations

DataFlow generates these nodes for every model:

```python
# Create
workflow.add_node("TaskCreateNode", "create", {
    "title": "New Task",
    "description": "Description here"
})

# Read (single)
workflow.add_node("TaskReadNode", "get_task", {
    "id": 1
})

# Update
workflow.add_node("TaskUpdateNode", "update_task", {
    "id": 1,
    "completed": True
})

# Delete
workflow.add_node("TaskDeleteNode", "delete_task", {
    "id": 1
})

# List with filtering
workflow.add_node("TaskListNode", "list_active", {
    "filter": {"completed": False},
    "order_by": ["created_at"],
    "limit": 10
})
```

## Step 4: Bulk Operations

Handle large datasets efficiently:

```python
# Bulk create
workflow.add_node("TaskBulkCreateNode", "import_tasks", {
    "data": [
        {"title": "Task 1", "description": "First task"},
        {"title": "Task 2", "description": "Second task"},
        # ... thousands more
    ],
    "batch_size": 1000
})

# Bulk update
workflow.add_node("TaskBulkUpdateNode", "complete_all", {
    "filter": {"completed": False},
    "update": {"completed": True}
})

# Bulk delete
workflow.add_node("TaskBulkDeleteNode", "cleanup_old", {
    "filter": {"created_at": {"$lt": "2024-01-01"}}
})
```

## Step 5: Transactions

Ensure data consistency:

```python
# Wrap operations in a transaction
workflow.add_node("TransactionContextNode", "tx_start", {
    "isolation_level": "READ_COMMITTED"
})

workflow.add_node("TaskCreateNode", "task1", {
    "title": "First task in transaction"
})

workflow.add_node("TaskCreateNode", "task2", {
    "title": "Second task in transaction"
})

# Both succeed or both fail!
```

## Step 6: Production Configuration

When ready for production:

```python
# Option 1: Environment variables
# DATABASE_URL=postgresql://user:pass@localhost/mydb
db = DataFlow()  # Automatically uses DATABASE_URL

# Option 2: Explicit configuration
db = DataFlow(
    database_url="postgresql://user:pass@localhost/mydb",
    pool_size=20,
    pool_recycle=3600,
    echo=False  # Disable SQL logging
)

# Option 3: Multi-database setup
db = DataFlow(
    write_url="postgresql://primary:5432/db",
    read_urls=[
        "postgresql://replica1:5432/db",
        "postgresql://replica2:5432/db"
    ]
)
```

## Complete Example: Todo API

Here's a complete todo list API:

```python
from datetime import datetime
from typing import Optional
from kailash_dataflow import DataFlow
from kailash.workflow.builder import WorkflowBuilder
from kailash.runtime.local import LocalRuntime

# Initialize DataFlow
db = DataFlow()

# Define model
@db.model
class Todo:
    user_id: int
    title: str
    description: str = ""
    completed: bool = False
    due_date: Optional[datetime] = None
    # Note: id, created_at, and updated_at are added automatically

# Create workflow for todo operations
def create_todo_workflow():
    workflow = WorkflowBuilder()

    # Get user's todos
    workflow.add_node("TodoListNode", "get_todos", {
        "filter": {"user_id": 123},  # Replace with actual user_id
        "order_by": ["-created_at"]
    })

    return workflow.build()

# Create a new todo
def create_todo(user_id: int, title: str, due_date: datetime = None):
    workflow = WorkflowBuilder()

    workflow.add_node("TodoCreateNode", "create", {
        "user_id": user_id,
        "title": title,
        "due_date": due_date
    })

    runtime = LocalRuntime()
    results, _ = runtime.execute(workflow.build())
    return results["create"]["data"]

# Mark todo as complete
def complete_todo(todo_id: int):
    workflow = WorkflowBuilder()

    workflow.add_node("TodoUpdateNode", "complete", {
        "id": todo_id,
        "completed": True,
        "updated_at": datetime.now()
    })

    runtime = LocalRuntime()
    results, _ = runtime.execute(workflow.build())
    return results["complete"]["data"]
```

## Next Steps

- **[Core Concepts](concepts.md)** - Understand DataFlow architecture
- **[Model Definition](../development/models.md)** - Advanced modeling
- **[Workflow Patterns](../workflows/patterns.md)** - Best practices
- **[Production Guide](../production/deployment.md)** - Deploy to production

## Common Issues

### Import Error

```bash
# Ensure Kailash is installed
pip install kailash

# For development features
pip install kailash[dev]
```

### Database Connection

```bash
# Check environment variable
echo $DATABASE_URL

# Test connection
python -c "from kailash_dataflow import DataFlow; db = DataFlow(); print(db.config.database_url)"
```

### Performance

```python
# Enable query logging
db = DataFlow(echo=True)

# Monitor slow queries
db = DataFlow(
    monitoring=True,
    slow_query_threshold=1.0  # Log queries over 1 second
)
```

## Get Help

- Documentation: [docs/](../)
- Examples: [examples/](../../examples/)
- Issues: [GitHub](https://github.com/kailash/dataflow/issues)
- Community: [Discord](https://discord.gg/kailash)
