# Parameter Injection in User Management App

## Overview

The Kailash SDK now supports **automatic parameter injection** for workflows, making it much easier to pass parameters to workflows without complex nested structures.

## What's New?

Previously, you had to specify parameters for each node individually:

```python
# OLD WAY - Node-specific parameters
results = runtime.execute(workflow, parameters={
    "user_lookup": {
        "username": "john_doe"
    },
    "password_verifier": {
        "password": "SecurePass123"
    },
    "permission_checker": {
        "resource": "dashboard",
        "action": "view"
    }
})
```

Now, with parameter injection, you can pass parameters at the workflow level:

```python
# NEW WAY - Workflow-level parameters
results = runtime.execute(workflow, parameters={
    "username": "john_doe",
    "password": "SecurePass123",
    "resource": "dashboard",
    "action": "view"
})
```

## How It Works

1. **Define Input Mappings**: When building your workflow, use `add_workflow_inputs()` to define how workflow parameters map to node parameters:

```python
builder.add_workflow_inputs("user_lookup", {
    "username": "username",  # workflow param -> node param
    "email": "email"        # alternative lookup field
})

builder.add_workflow_inputs("password_verifier", {
    "password": "password"
})
```

2. **Automatic Injection**: The LocalRuntime automatically detects workflow-level parameters and injects them into the appropriate nodes based on your mappings.

3. **Smart Detection**: The runtime intelligently detects whether you're using:
   - Workflow-level parameters (new simplified format)
   - Node-specific parameters (traditional format)
   - Mixed parameters (workflow-level with node-specific overrides)

## Examples in This App

### 1. Login Workflow (`api/user_api.py`)

The login workflow now supports parameter injection:

```python
# Simple login call
result = await runtime.execute_async(
    login_workflow,
    {
        "email": "user@example.com",
        "password": "password123"
    }
)
```

### 2. User Registration

```python
# Direct parameter passing
result = await runtime.execute_async(
    registration_workflow,
    {
        "email": "new@example.com",
        "username": "newuser",
        "password": "SecurePass123",
        "role": "user"
    }
)
```

### 3. Complex Workflows

See `examples/parameter_injection_example.py` for a complete example of:
- User onboarding with validation
- Role assignment
- Welcome email sending
- All using simple workflow-level parameters

## Benefits

1. **Simpler API**: Less nesting, more intuitive parameter passing
2. **Backward Compatible**: Existing node-specific parameters still work
3. **Flexible**: Mix workflow and node-specific parameters as needed
4. **Maintainable**: Easier to understand and modify workflows
5. **Type Safe**: Parameters are still validated by nodes

## Best Practices

1. **Use Workflow Inputs for Common Parameters**: Define mappings for parameters that come from external sources (API calls, user input).

2. **Node-Specific for Internal State**: Use node-specific parameters for data that flows between nodes via connections.

3. **Document Your Mappings**: Make it clear which workflow parameters map to which nodes:

```python
# Define workflow inputs with clear documentation
builder.add_workflow_inputs("validator", {
    "email": "email",           # User's email address
    "role": "role",             # Role to assign
    "department": "department"  # User's department
})
```

4. **Use Meaningful Names**: Workflow parameter names should be intuitive for API users.

## Migration Guide

To enable parameter injection in existing workflows:

1. Add `add_workflow_inputs()` calls for each node that needs external parameters
2. Update your execute calls to use workflow-level parameters
3. Test both old and new parameter formats to ensure compatibility

## Full Example

See the complete examples in:
- `examples/parameter_injection_example.py` - Full onboarding workflow
- `examples/simplified_login_workflow.py` - Simplified login with parameter injection

## Technical Details

The parameter injection system:
- Detects parameter format automatically
- Transforms workflow parameters to node-specific format
- Validates all parameters
- Provides helpful debug logging
- Maintains full backward compatibility

Enable debug mode to see parameter injection in action:

```python
runtime = LocalRuntime(debug=True)
```
