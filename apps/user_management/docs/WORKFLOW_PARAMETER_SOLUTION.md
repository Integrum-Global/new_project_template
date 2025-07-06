# WorkflowBuilder Parameter Passing Issue and Solution

## Problem Statement

The WorkflowBuilder in Kailash SDK has a limitation where workflow-level parameters are not automatically passed to nodes, especially those without incoming connections (entry nodes). This causes nodes to receive empty inputs even when parameters are provided to the workflow execution.

### Example of the Issue

```python
# This workflow will fail because user_fetcher doesn't receive required parameters
workflow = WorkflowBuilder()
workflow.add_node("UserManagementNode", "user_fetcher", {
    "operation": "get_user",
    "identifier": "$.email",
    "identifier_type": "email"
    # Missing: tenant_id and database_config
})

# Even if you pass parameters to execution, the node won't receive them
result = runtime.execute_async(workflow, {
    "email": "user@example.com",
    "tenant_id": "default",
    "database_config": {...}
})
# ERROR: Node 'user_fetcher' missing required inputs: ['tenant_id', 'database_config']
```

## Root Cause

1. WorkflowBuilder doesn't have a mechanism to map workflow-level parameters to node inputs
2. Nodes without incoming connections don't have a source for their required parameters
3. The workflow validation checks node requirements but doesn't consider workflow parameters

## Solutions

### Solution 1: Direct Node Execution (Recommended)

Instead of using complex workflows, use direct node execution for simple operations:

```python
from kailash.nodes.admin.user_management import UserManagementNode

# Direct node execution - simple and reliable
user_node = UserManagementNode(
    operation="create_user",
    tenant_id="default",
    database_config={
        "connection_string": DATABASE_URL,
        "database_type": "postgresql"
    }
)

result = user_node.execute(
    user_data={
        "email": "user@example.com",
        "username": "username",
        "status": "active"
    },
    password="SecurePassword123!"
)
```

**Advantages:**
- No parameter passing issues
- Simpler code
- Better error handling
- Direct access to results

### Solution 2: Configure Nodes with Required Parameters

If you must use WorkflowBuilder, configure nodes with all required parameters:

```python
workflow = WorkflowBuilder()
workflow.add_node("UserManagementNode", "user_fetcher", {
    "operation": "get_user",
    "identifier": "$.email",
    "identifier_type": "email",
    # Include all required parameters in node config
    "tenant_id": "default",
    "database_config": {
        "connection_string": DATABASE_URL,
        "database_type": "postgresql"
    }
})
```

### Solution 3: Use PythonCodeNode for Input Handling

Create a PythonCodeNode that prepares inputs for subsequent nodes:

```python
workflow = WorkflowBuilder()

# Input preparation node
input_prep_code = """
# Extract and prepare inputs for UserManagementNode
email = locals().get('email', '')
tenant_id = locals().get('tenant_id', 'default')
database_config = locals().get('database_config', {})

result = {
    "email": email,
    "tenant_id": tenant_id,
    "database_config": database_config
}
"""

workflow.add_node("PythonCodeNode", "input_prep", {"code": input_prep_code})
workflow.add_node("UserManagementNode", "user_fetcher", {
    "operation": "get_user",
    "identifier": "$.email",
    "identifier_type": "email"
})

# Connect the preparation node to the user fetcher
workflow.add_connection("input_prep", "result", "user_fetcher", "input")
```

## Best Practices

1. **Use Direct Node Execution** for simple operations (single node operations)
2. **Use WorkflowBuilder** only for complex multi-node workflows
3. **Always Configure Required Parameters** in node definitions
4. **Test Parameter Passing** thoroughly before deployment
5. **Document Parameter Requirements** clearly in your code

## Migration Guide

To migrate from complex workflows to direct node execution:

### Before (Complex Workflow)
```python
def create_user_registration_workflow(self):
    workflow = WorkflowBuilder()

    # Multiple nodes for validation, hashing, creation
    workflow.add_node("PythonCodeNode", "validator", {...})
    workflow.add_node("PythonCodeNode", "password_hasher", {...})
    workflow.add_node("UserManagementNode", "user_creator", {...})

    # Complex connections
    workflow.add_connection("validator", "result", "password_hasher", "input")
    workflow.add_connection("password_hasher", "result", "user_creator", "input")

    return workflow.build()
```

### After (Direct Node Execution)
```python
def register_user(self, email: str, username: str, password: str):
    # Direct node execution
    user_node = UserManagementNode(
        operation="create_user",
        tenant_id="default",
        database_config=self.db_config
    )

    result = user_node.execute(
        user_data={
            "email": email,
            "username": username,
            "status": "active"
        },
        password=password
    )

    return result
```

## Future SDK Improvements

The Kailash SDK team should consider:

1. Adding automatic parameter injection for entry nodes
2. Supporting workflow input declarations
3. Providing better error messages for parameter issues
4. Adding a `workflow.add_input()` method for explicit input mapping

## Conclusion

While WorkflowBuilder has parameter passing limitations, the direct node execution pattern provides a simpler, more reliable solution for most use cases. Reserve WorkflowBuilder for truly complex multi-node workflows where the benefits outweigh the complexity.
