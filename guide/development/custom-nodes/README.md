# Custom Node Development Guide

This directory contains comprehensive documentation for developing custom nodes in the Kailash SDK.

## 📁 Directory Structure

```
custom-nodes/
├── README.md                    # This file - Overview and navigation
├── CLAUDE.md                    # Quick reference for LLMs
├── 01-getting-started.md        # Basic custom node concepts
├── 02-parameter-types.md        # Parameter type constraints and patterns
├── 03-common-patterns.md        # Common implementation patterns
├── 04-error-handling.md         # Error handling best practices
├── 05-testing-nodes.md          # Testing custom nodes
├── examples/                    # Working examples
│   ├── basic_node.py           # Simple custom node
│   ├── data_processor.py       # Data processing node
│   ├── api_integration.py      # API integration node
│   └── cycle_aware_node.py     # Cycle-aware custom node
└── troubleshooting.md          # Common issues and solutions
```

## 🚀 Quick Start

1. **New to custom nodes?** Start with [01-getting-started.md](01-getting-started.md)
2. **Parameter issues?** See [02-parameter-types.md](02-parameter-types.md) 
3. **Need examples?** Check the [examples/](examples/) directory
4. **Debugging problems?** Read [troubleshooting.md](troubleshooting.md)

## 📖 Documentation Overview

### [01. Getting Started](01-getting-started.md)
- Understanding the Node base class
- Required abstract methods
- Basic custom node structure
- Your first custom node

### [02. Parameter Types](02-parameter-types.md) ⚠️ **Critical**
- Valid parameter types (str, int, float, bool, list, dict, Any)
- Why generic types fail (List[str], Optional[T], Union[A,B])
- Configuration vs runtime parameters
- Parameter validation patterns

### [03. Common Patterns](03-common-patterns.md)
- Data processing nodes
- API integration nodes
- Transformation nodes
- Aggregation nodes

### [04. Error Handling](04-error-handling.md)
- Validation errors
- Runtime errors
- Error propagation
- Debugging techniques

### [05. Testing Nodes](05-testing-nodes.md)
- Unit testing patterns
- Integration testing
- Mocking strategies
- Performance testing

### [Examples Directory](examples/)
- `basic_node.py` - Minimal working custom node
- `data_processor.py` - Data transformation patterns
- `api_integration.py` - External API integration
- `cycle_aware_node.py` - Iterative processing nodes

### [Troubleshooting](troubleshooting.md)
- "Can't instantiate abstract class" errors
- Parameter validation failures
- Type errors and solutions
- Import issues

## 🎯 Most Common Issues

### 1. **Abstract Class Error**
```python
# ❌ This fails
class MyNode(Node):
    def get_parameters(self):
        return {"param": {"type": "string"}}  # Wrong format!
```

**Solution**: See [02-parameter-types.md](02-parameter-types.md)

### 2. **Generic Type Error**
```python
# ❌ This fails
NodeParameter(name="items", type=List[str])  # Generic type!
```

**Solution**: Use `list` or `Any` instead

### 3. **Missing Abstract Method**
```python
# ❌ This fails - missing run() method
class MyNode(Node):
    def get_parameters(self):
        return {}
```

**Solution**: Implement both `get_parameters()` and `run()`

## 📝 Development Workflow

1. **Define your node class** inheriting from `Node`
2. **Implement `get_parameters()`** with valid types
3. **Implement `run()`** with your logic
4. **Test your node** in isolation
5. **Integrate into workflows**
6. **Document usage patterns**

## 🔗 Related Resources

- [Node API Reference](../../reference/api/03-nodes-base.yaml)
- [Built-in Nodes Catalog](../../reference/nodes/)
- [Workflow Patterns](../../reference/pattern-library/)
- [Testing Guidelines](../../instructions/testing-guidelines.md)

## 🤝 Contributing

When creating custom nodes:
1. Follow the patterns in this guide
2. Add comprehensive docstrings
3. Include usage examples
4. Write tests
5. Document any special requirements

---

*Last Updated: v0.2.1 (2025-01-09)*