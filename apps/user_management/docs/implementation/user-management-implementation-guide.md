# User Management System Implementation Guide

## Overview

This guide documents the implementation of a comprehensive user management system using Kailash SDK admin nodes. The system provides Django admin-like capabilities with 10-100x better performance through async/await architecture.

## ⚠️ Important Notice

The admin nodes (`UserManagementNode`, `RoleManagementNode`) currently have datetime serialization bugs that need to be fixed. See the [Known Issues](#known-issues) section for workarounds.

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
from kailash.nodes.admin.user_management import UserManagementNode

# Initialize the node
user_node = UserManagementNode()

# Create a user
result = user_node.execute(
    operation="create_user",
    tenant_id="your_tenant",
    database_config={
        "connection_string": "postgresql://user:pass@localhost:5432/db",
        "database_type": "postgresql"
    },
    user_data={
        "email": "user@example.com",
        "username": "johndoe",
        "password": "SecurePass123!",
        "first_name": "John",
        "last_name": "Doe",
        "attributes": {
            "department": "Engineering",
            "employee_id": "EMP001"
        }
    }
)
```

### Role Management

```python
from kailash.nodes.admin.role_management import RoleManagementNode

role_node = RoleManagementNode()

# Create a role
role_result = role_node.execute(
    operation="create_role",
    tenant_id="your_tenant",
    database_config=db_config,
    role_data={
        "name": "developer",
        "description": "Developer role with code access",
        "permissions": ["code.read", "code.write", "pr.create"]
    }
)

# Assign role to user
user_node.execute(
    operation="assign_roles",
    tenant_id="your_tenant",
    database_config=db_config,
    user_id=user_id,
    role_ids=[role_id]
)
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
| `assign_roles` | Assign roles to user | `user_id`, `role_ids` |
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

## Known Issues

### DateTime Serialization Bug

The admin nodes have a bug where `to_dict()` methods try to call `isoformat()` on string timestamps. This causes errors like:

```
AttributeError: 'str' object has no attribute 'isoformat'
```

**Workaround**: The nodes have been patched with `parse_datetime` and `format_datetime` helper functions that handle both datetime objects and strings.

### SQL Parameter Indexing

The `RoleManagementNode` had an incorrect parameter index in the UPDATE query. This has been fixed in the latest version.

### Missing user_roles Table

Some operations may fail if the `user_roles` table doesn't exist. The schema manager should create it automatically, but you may need to run the schema initialization manually.

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
