# User Management System Implementation Guide

## Overview

This guide documents the implementation of a comprehensive user management system using Kailash SDK admin nodes. The system provides Django admin-like capabilities with 10-100x better performance through async/await architecture.

## ⚠️ Important Updates from E2E Testing

Based on extensive E2E testing, several important patterns and fixes have been identified:
1. **Permission Check Structure**: Use `result.check.allowed` not `result.allowed`
2. **Direct Node Execution**: Preferred over workflows for database operations to avoid transaction isolation issues
3. **Role ID Generation**: RoleManagementNode generates IDs from role names using lowercase and underscore replacement

## Architecture

### Core Components

1. **Admin Nodes** (from `kailash.nodes.admin`):
   - `UserManagementNode` - User CRUD operations, lifecycle management
   - `RoleManagementNode` - Role and permission management
   - `PermissionManagementNode` - Permission definitions and validation

2. **Access Control**:
   - `AccessControlManager` - RBAC/ABAC enforcement
   - Built-in support for multi-tenancy
   - JWT-based authentication

3. **Infrastructure**:
   - PostgreSQL with JSONB for flexible attributes
   - Redis for session management and caching
   - Ollama for AI-powered features

## Quick Start

### Basic User Creation

```python
from kailash.nodes.admin import UserManagementNode

# Initialize the node with tenant and database config
user_node = UserManagementNode(
    operation="create_user",
    tenant_id="your_tenant",
    database_config={
        "connection_string": "postgresql://user:pass@localhost:5432/db",
        "database_type": "postgresql"
    }
)

# Create a user
result = user_node.execute(
    user_data={
        "email": "user@example.com",
        "username": "johndoe",
        "password": "SecurePass123!",
        "first_name": "John",
        "last_name": "Doe",
        "attributes": {
            "department": "Engineering",
            "employee_id": "EMP001"
        },
        "status": "active"  # Important: Set status explicitly
    },
    tenant_id="your_tenant"
)

# Check result structure
if result.get("result", {}).get("success", False):
    user_id = result["result"]["user"]["user_id"]
    print(f"User created with ID: {user_id}")
```

### Role Management

```python
from kailash.nodes.admin import RoleManagementNode

# Create a role
role_node = RoleManagementNode(
    operation="create_role",
    tenant_id="your_tenant",
    database_config=db_config
)

role_result = role_node.execute(
    role_data={
        "name": "Developer Role",  # Note: ID will be "developer_role"
        "description": "Developer role with code access",
        "permissions": ["code:read", "code:write", "pr:create"],
        "role_type": "custom"  # "system" or "custom"
    },
    tenant_id="your_tenant"
)

# Role ID is generated from name (lowercase, underscores)
# "Developer Role" -> "developer_role"
role_id = role_result["result"]["role"]["role_id"]

# Assign role to user - use separate node instance
assign_node = RoleManagementNode(
    operation="assign_user",  # Note: "assign_user" not "assign_roles"
    tenant_id="your_tenant",
    database_config=db_config
)

assign_result = assign_node.execute(
    user_id=user_id,
    role_id=role_id,  # Use the generated role_id
    tenant_id="your_tenant"
)
```

### Permission Checking

```python
from kailash.nodes.admin import PermissionCheckNode

# Check permissions
perm_node = PermissionCheckNode(
    operation="check_permission",
    tenant_id="your_tenant",
    database_config=db_config
)

# Check if user has permission
perm_result = perm_node.execute(
    user_id=user_id,
    resource_id="system",
    permission="admin",  # Can be "admin" or "system:admin" format
    tenant_id="your_tenant"
)

# IMPORTANT: Permission result structure is nested
if perm_result.get("result", {}).get("check", {}).get("allowed", False):
    print("Permission granted!")
else:
    reason = perm_result["result"]["check"].get("reason", "Unknown")
    print(f"Permission denied: {reason}")
```

## Supported Operations

### UserManagementNode Operations

| Operation | Description | Key Parameters |
|-----------|-------------|----------------|
| `create_user` | Create new user | `user_data` (dict with email, username, password, attributes) |
| `update_user` | Update user details | `user_id`, `user_data` (partial update) |
| `delete_user` | Soft delete user | `user_id` |
| `get_user` | Retrieve user details | `user_id` |
| `list_users` | List users with filters | `filters`, `limit`, `offset` |
| `search_users` | Search users | `query`, `limit` |
| `get_user_roles` | Get user's roles | `user_id` |
| `get_user_permissions` | Get effective permissions | `user_id` |

### RoleManagementNode Operations

| Operation | Description | Key Parameters |
|-----------|-------------|----------------|
| `create_role` | Create new role | `role_data` (name, description, permissions) |
| `update_role` | Update role | `role_id`, `role_data` |
| `delete_role` | Delete role | `role_id` |
| `get_role` | Get role details | `role_id` |
| `list_roles` | List all roles | `filters` |
| `add_permission` | Add permission to role | `role_id`, `permission` |
| `remove_permission` | Remove permission | `role_id`, `permission` |
| `assign_user` | Assign role to user | `user_id`, `role_id` |
| `unassign_user` | Remove role from user | `user_id`, `role_id` |
| `get_user_roles` | Get roles for a user | `user_id` |

## Parameter Structure

### Important: Nested vs Flat Parameters

The admin nodes expect parameters in specific structures:

1. **User operations** expect `user_data` as a nested dictionary:
   ```python
   user_node.execute(
       operation="create_user",
       user_data={  # Nested under user_data
           "email": "...",
           "username": "...",
           "password": "..."
       },
       tenant_id="...",
       database_config={...}
   )
   ```

2. **Role operations** expect `role_data` as a nested dictionary:
   ```python
   role_node.execute(
       operation="create_role",
       role_data={  # Nested under role_data
           "name": "...",
           "description": "...",
           "permissions": [...]
       },
       tenant_id="...",
       database_config={...}
   )
   ```

## Important E2E Testing Findings

### Direct Node Execution vs Workflows

For database operations, especially role creation and assignment, use direct node execution instead of workflows:

```python
# ✅ GOOD: Direct node execution
role_node = RoleManagementNode(
    operation="create_role",
    tenant_id=tenant_id,
    database_config=db_config
)
result = role_node.execute(role_data=data, tenant_id=tenant_id)

# ❌ AVOID: Workflow-based execution for simple operations
# Can cause transaction isolation issues
```

### Role ID Generation Pattern

RoleManagementNode automatically generates role IDs from role names:

```python
import re

def generate_role_id(name: str) -> str:
    """Mimics RoleManagementNode ID generation"""
    role_id = re.sub(r"[^a-zA-Z0-9_]", "_", name.lower())
    role_id = re.sub(r"_+", "_", role_id)
    role_id = role_id.strip("_")
    return role_id

# Examples:
# "Senior Engineer" -> "senior_engineer"
# "VP of Sales" -> "vp_of_sales"
# "C++ Developer" -> "c_developer"
```

### Permission Format Flexibility

The permission check supports multiple formats:

```python
# Both work:
permission="admin"          # Simple format
permission="system:admin"   # Resource:action format

# The system will match:
# - Exact: "system:admin"
# - Wildcard: "system:*" or "*:admin"
```

### User Status Requirement

Always set user status explicitly when creating users:

```python
user_data = {
    "email": "user@example.com",
    "username": "user123",
    "password": "SecurePass123!",
    "status": "active"  # Required for permission checks!
}
```

## Database Schema

The admin nodes automatically create required tables on first use:

- `users` - User accounts with JSONB attributes
- `roles` - Role definitions with JSONB permissions
- `user_roles` - Many-to-many relationship
- `permissions` - Permission definitions
- `audit_logs` - All operations logged

## Integration with Middleware

For production applications, use the gateway middleware:

```python
from kailash.middleware import create_gateway

# Create gateway with user management
app = create_gateway(
    port=8080,
    enable_auth=True,
    enable_user_management=True,
    database_config=db_config,
    redis_url="redis://localhost:6379"
)

# Access via REST API:
# POST /api/users - Create user
# GET /api/users/{id} - Get user
# PUT /api/users/{id} - Update user
# DELETE /api/users/{id} - Delete user
```

## Known Issues and Solutions

### Permission Check Result Structure

The permission check result has a nested structure that differs from other operations:

```python
# ❌ WRONG:
if perm_result.get("result", {}).get("allowed", False):

# ✅ CORRECT:
if perm_result.get("result", {}).get("check", {}).get("allowed", False):
```

### Transaction Isolation in Workflows

When creating roles and immediately using them in workflows, transaction isolation can cause "role not found" errors:

```python
# ❌ PROBLEM: Role created in workflow, used in another workflow
# Solution: Use direct node execution or add delays between operations
```

### Role Assignment Operation Name

The operation for assigning roles is `assign_user`, not `assign_roles`:

```python
# ❌ WRONG:
operation="assign_roles"

# ✅ CORRECT:
operation="assign_user"
```

### DateTime Serialization (Fixed)

Previous versions had datetime serialization issues. These have been resolved with helper functions that handle both datetime objects and strings.

## Performance Characteristics

Based on integration testing with Docker services:

- **User Creation**: ~50ms per user
- **Role Assignment**: ~10ms per assignment
- **User Search**: <100ms for most queries
- **List Operations**: <200ms with pagination
- **Concurrent Operations**: Handles 20+ concurrent requests

## Testing

The system includes comprehensive tests in three tiers:

1. **Unit Tests** (`tests/unit/apps/user_management/`)
   - Component validation
   - Password security
   - JWT handling

2. **Integration Tests** (`tests/integration/apps/user_management/`)
   - Real PostgreSQL operations
   - Multi-node workflows
   - Performance benchmarks

3. **E2E Tests** (`tests/e2e/apps/user_management/`)
   - Complete user journeys
   - 8 persona scenarios
   - Production workflows

Run tests with:
```bash
# Integration tests with Docker
pytest tests/integration/apps/user_management/ -v

# All user management tests
pytest tests/ -k "user_management" -v
```

## Migration from Django Admin

### Key Differences

1. **Async by Default**: All operations are async
2. **JSONB Attributes**: Flexible schema without migrations
3. **Workflow-Based**: Compose complex operations
4. **Multi-Tenant**: Built-in tenant isolation
5. **Performance**: 10-100x faster operations

### Migration Steps

1. Export Django users:
   ```python
   # Django
   users = User.objects.all().values()
   ```

2. Import to Kailash:
   ```python
   # Kailash
   for user in users:
       user_node.execute(
           operation="create_user",
           user_data={
               "email": user["email"],
               "username": user["username"],
               "attributes": {
                   "django_id": user["id"],
                   "is_staff": user["is_staff"],
                   "is_superuser": user["is_superuser"]
               }
           },
           tenant_id="default",
           database_config=db_config
       )
   ```

## Best Practices

1. **Always specify tenant_id** for multi-tenant isolation
2. **Use attributes JSONB** for flexible user properties
3. **Implement proper error handling** for node operations
4. **Use connection pooling** for database connections
5. **Enable audit logging** for compliance
6. **Implement rate limiting** for API endpoints
7. **Use Redis caching** for frequently accessed data

## Security Considerations

1. **Password Policy**: Enforced by default (min 8 chars, complexity)
2. **JWT Tokens**: Short-lived access tokens with refresh
3. **RBAC/ABAC**: Fine-grained permission control
4. **Audit Trail**: All operations logged with timestamps
5. **SQL Injection**: Prevented by parameterized queries
6. **Multi-Tenancy**: Complete data isolation

## Troubleshooting

### Common Issues

1. **"password authentication failed"**
   - Check `docker_config.py` has correct credentials
   - Default: `test_user`/`test_password` on port 5434

2. **"relation does not exist"**
   - Schema not initialized
   - Admin nodes should auto-create tables on first use

3. **DateTime errors**
   - Known bug in admin nodes
   - Use the patched version with helper functions

4. **"no rows returned"**
   - Check tenant_id matches
   - Verify user/role exists in database

## Example Workflows

See the complete examples in:
- `/sdk-users/workflows/user-management/full_user_management_system.py`
- `/sdk-users/workflows/user-management/user_management_enterprise_gateway.py`
- `/sdk-users/workflows/user-management/scenario_*.py` for specific use cases

## Next Steps

1. Fix the datetime bugs in admin nodes
2. Add missing operations (bulk delete, password reset)
3. Enhance search with full-text capabilities
4. Add GraphQL API support
5. Implement SSO integrations

## Support

For issues or questions:
- Check `/sdk-users/developer/05-troubleshooting.md`
- Review test files for usage examples
- See `/shared/mistakes/` for common pitfalls

---

*Last Updated: June 2025*
*Tested with: Kailash SDK v2.x, PostgreSQL 14, Redis 7, Python 3.12*
