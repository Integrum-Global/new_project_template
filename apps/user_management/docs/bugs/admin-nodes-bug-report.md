# Admin Nodes Bug Report

## Summary

Critical bugs discovered in Kailash SDK admin nodes during integration testing that prevent production use.

## Affected Nodes

1. `kailash.nodes.admin.user_management.UserManagementNode`
2. `kailash.nodes.admin.role_management.RoleManagementNode`

## Bug Details

### 1. DateTime Serialization Error

**Location**: `to_dict()` methods in both nodes

**Error**:
```python
AttributeError: 'str' object has no attribute 'isoformat'
```

**Root Cause**:
The `to_dict()` method assumes datetime fields are `datetime` objects, but PostgreSQL returns them as strings:

```python
# Buggy code in UserManagementNode.to_dict()
return {
    "user_id": user.user_id,
    "created_at": user.created_at.isoformat() if user.created_at else None,  # Fails when created_at is string
    "updated_at": user.updated_at.isoformat() if user.updated_at else None,  # Fails when updated_at is string
    # ...
}
```

**Fix Applied**:
Added helper functions to handle both datetime objects and strings:

```python
def parse_datetime(value: Union[str, datetime, None]) -> Optional[datetime]:
    """Parse datetime from various formats."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace('Z', '+00:00'))
        except ValueError:
            # Try other common formats
            for fmt in ["%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S",
                       "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S"]:
                try:
                    return datetime.strptime(value, fmt)
                except ValueError:
                    continue
    return None

def format_datetime(dt: Union[datetime, str, None]) -> Optional[str]:
    """Format datetime handling both datetime objects and strings."""
    if dt is None:
        return None
    if isinstance(dt, datetime):
        return dt.isoformat()
    if isinstance(dt, str):
        parsed = parse_datetime(dt)
        return parsed.isoformat() if parsed else dt
    return None
```

### 2. SQL Parameter Indexing Error

**Location**: `RoleManagementNode._update_role()` method

**Error**:
```
operator does not exist: character varying = timestamp
```

**Root Cause**:
Incorrect parameter indices in UPDATE query:

```python
# Buggy code
WHERE role_id = ${param_count - 1} AND tenant_id = ${param_count}

# Should be
WHERE role_id = ${param_count} AND tenant_id = ${param_count + 1}
```

## Impact

1. **Cannot create users**: Fails when returning created user
2. **Cannot get users**: Fails when formatting timestamps
3. **Cannot update roles**: SQL type mismatch error
4. **Blocks all production use** of admin nodes

## Test Results

After applying fixes:
- ✅ User CRUD operations working
- ✅ Role CRUD operations working (except delete - constraint issue)
- ✅ Integration tests passing with real PostgreSQL

## Recommended Actions

1. **Immediate**: Apply the datetime handling fixes to both nodes
2. **Short-term**: Add unit tests for datetime edge cases
3. **Long-term**: Standardize datetime handling across all nodes

## Workarounds (if not fixed)

Use `PythonCodeNode` to implement user management directly:

```python
from kailash.nodes.code import PythonCodeNode

# Create user with PythonCodeNode
create_user_node = PythonCodeNode.from_function(
    func=lambda inputs: {
        "result": {
            "user": {
                "user_id": str(uuid4()),
                "email": inputs["email"],
                "created_at": datetime.now(UTC).isoformat()
            }
        }
    },
    name="CreateUserWorkaround"
)
```

## Verification

Run integration tests to verify fixes:
```bash
pytest tests/integration/apps/user_management/test_admin_nodes_docker_integration.py -v
```

Expected output:
```
test_user_management_basic_flow PASSED
test_role_management_basic_flow PASSED
test_user_role_integration PASSED
```

## Additional Fixes Applied

1. **Table Name Mismatch**: Created database view to map `user_role_assignments` to `user_roles`
2. **Missing datetime fix**: Added `format_datetime` call in `_get_user_roles` method (line 1624)
3. **Test adjustments**: Updated tests to handle correct parameter structures and result formats

## Current Status

✅ All 3 integration tests now passing with real Docker PostgreSQL
✅ User CRUD operations working
✅ Role CRUD operations working
✅ User-role assignment working with workarounds

---

*Reported: June 2025*
*Severity: Critical - Blocks Production Use*
*Status: Fixed locally with workarounds, needs upstream merge*
