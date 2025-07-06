# Direct Node Usage vs Workflow Pattern - Best Practices

## Executive Summary

**Use Workflows** as the default approach. Direct node usage should be an exception, not the rule.

## Quick Decision Guide

```mermaid
graph TD
    A[Need to execute nodes?] --> B{Multiple steps?}
    B -->|Yes| C[Use Workflow]
    B -->|No| D{Performance critical?}
    D -->|No| C
    D -->|Yes| E{<5ms required?}
    E -->|No| C
    E -->|Yes| F[Consider Direct Node]

    F --> G{Can optimize workflow?}
    G -->|Yes| C
    G -->|No| H[Use Direct Node]
```

## Detailed Comparison

### Workflow Approach (Recommended)

**When to Use** (90% of cases):
- Any multi-step process
- Business logic implementation
- Data transformation pipelines
- User-facing features
- Integration scenarios

**Benefits**:
```python
# ✅ RECOMMENDED: Workflow approach
workflow = Workflow("user_registration", "User registration process")
workflow.add_node("validator", ValidationNode())
workflow.add_node("creator", UserManagementNode())
workflow.connect("validator", "creator", {"result": "input"})

# With new parameter injection (v0.6.2+)
results = runtime.execute(workflow, parameters={
    "email": "user@example.com",
    "password": "secure123"
})
```

**Advantages**:
- 📊 Built-in observability and metrics
- 🔄 Easy to modify and extend
- ✅ Automatic validation
- 📝 Self-documenting
- 🔍 Debugging and tracing support
- 🚀 Future-proof (caching, monitoring)
- 👥 Team-friendly

### Direct Node Usage (Exception)

**When Acceptable** (10% of cases):
- Single atomic operations
- Performance-critical paths (<5ms)
- CLI utilities
- Unit testing
- Emergency hotfixes

**Example**:
```python
# ⚠️ ONLY when justified by requirements
node = UserManagementNode(
    operation="verify_password",
    tenant_id="default",
    database_config=db_config
)
result = node.execute(identifier=email, password=password)
```

**Limitations**:
- ❌ No automatic tracking
- ❌ Manual error handling
- ❌ No built-in validation
- ❌ Harder to maintain
- ❌ No visual representation
- ❌ Limited reusability

## Common Scenarios

### Scenario 1: User Registration
```python
# ❌ AVOID: Direct node chain
validator = ValidationNode()
valid_result = validator.execute(data=user_data)
if valid_result["valid"]:
    creator = UserManagementNode()
    user_result = creator.execute(user_data=user_data)

# ✅ RECOMMENDED: Workflow
workflow = build_registration_workflow()
results = runtime.execute(workflow, parameters=user_data)
```

### Scenario 2: Single Query
```python
# ✅ ACCEPTABLE: True single operation
def get_user_by_id(user_id: str):
    node = UserManagementNode(operation="get_user")
    return node.execute(identifier=user_id)

# ✅ BETTER: Still use workflow for consistency
def get_user_by_id(user_id: str):
    workflow = Workflow("get_user", "Fetch user")
    workflow.add_node("fetcher", UserManagementNode(operation="get_user"))
    return runtime.execute(workflow, parameters={"identifier": user_id})
```

### Scenario 3: Performance Critical
```python
# ⚠️ ONLY if measured and proven necessary
class HighFrequencyHandler:
    def __init__(self):
        # Pre-initialize for performance
        self.auth_node = AuthNode(config=fast_config)

    def authenticate(self, token: str):
        # Direct call for <5ms requirement
        return self.auth_node.execute(token=token)

# ✅ FIRST TRY: Optimized workflow
workflow = Workflow("fast_auth", "Fast authentication")
workflow.add_node("auth", AuthNode(config=fast_config))
# Enable performance optimizations
workflow.metadata["performance_mode"] = "ultra"
```

## Migration Strategies

### From Direct Nodes to Workflows

1. **Identify Direct Node Usage**
   ```python
   # Before
   result1 = node1.execute(data)
   result2 = node2.execute(result1["output"])
   ```

2. **Convert to Workflow**
   ```python
   # After
   workflow = Workflow("process", "Data processing")
   workflow.add_node("step1", node1)
   workflow.add_node("step2", node2)
   workflow.connect("step1", "step2", {"output": "data"})
   ```

3. **Use Parameter Injection**
   ```python
   # Simplified execution
   results = runtime.execute(workflow, parameters={"data": input_data})
   ```

## Performance Considerations

### Workflow Overhead
- Typical overhead: 2-5ms
- Includes: validation, tracking, metrics
- Usually negligible compared to business logic

### When Performance Matters
1. **Measure First**: Profile actual performance
2. **Optimize Workflow**: Try caching, parallel execution
3. **Hybrid Approach**: Critical path direct, rest workflow
4. **Last Resort**: Full direct node implementation

## Best Practices Summary

### ✅ DO
- Use workflows by default
- Leverage parameter injection
- Measure before optimizing
- Document any direct usage
- Consider maintenance cost

### ❌ DON'T
- Default to direct nodes
- Optimize prematurely
- Sacrifice features for minimal gains
- Create unmaintainable code
- Skip workflow benefits

## Decision Checklist

Before using direct nodes, confirm ALL of these:
- [ ] Single atomic operation
- [ ] Measured performance requirement <5ms
- [ ] No need for tracking/metrics
- [ ] No data flow to other operations
- [ ] Documented justification
- [ ] Plan to convert to workflow later

If any checkbox is unchecked, **use a workflow**.

## Example: Proper Test Structure

```python
# ✅ GOOD: Test uses workflow even for simple operations
async def test_user_creation(self):
    workflow = build_user_workflow()
    results = runtime.execute(workflow, parameters={
        "email": "test@example.com",
        "password": "test123"
    })
    assert results["creator"]["result"]["user_id"]

# ❌ AVOID: Test uses direct nodes
async def test_user_creation(self):
    node = UserManagementNode()
    result = node.execute(user_data={...})
    assert result["user_id"]
```

## Conclusion

The Kailash SDK is designed around workflows. They provide the best balance of:
- **Performance**: Negligible overhead
- **Maintainability**: Clear, modifiable structure
- **Features**: Built-in tracking, validation, etc.
- **Team Work**: Self-documenting, shareable

Direct node usage should be a carefully considered exception, not a shortcut.

**Remember**: The new parameter injection feature (v0.6.2) removes the main pain point of workflows while preserving all their benefits. There's now even less reason to use direct nodes.

## Related Documentation
- [Workflow Parameter Injection Guide](../developer/22-workflow-parameter-injection.md)
- [Workflow Creation Patterns](../developer/02-workflows.md)
- [Performance Guidelines](../architecture/adr/0047-performance-guidelines.md)
- [Architecture Decision Matrix](../decision-matrix.md)
