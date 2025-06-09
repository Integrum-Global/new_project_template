# Troubleshooting Custom Nodes

Common issues and their solutions when developing custom nodes.

## Issue: "Can't instantiate abstract class"

### Error Message
```
TypeError: Can't instantiate abstract class MyNode with abstract method get_parameters
```

### Causes and Solutions

#### Cause 1: Using Generic Types
```python
# ❌ This causes the error
from typing import List
def get_parameters(self):
    return {
        'items': NodeParameter(type=List[str], ...)  # Generic type!
    }

# ✅ Solution: Use basic types
def get_parameters(self):
    return {
        'items': NodeParameter(type=list, ...)  # Basic type
    }
```

#### Cause 2: Wrong Return Type
```python
# ❌ Wrong return type
def get_parameters(self):
    return []  # Returns list instead of dict

# ✅ Correct return type
def get_parameters(self) -> Dict[str, NodeParameter]:
    return {}  # Returns dict
```

#### Cause 3: Missing Method Implementation
```python
# ❌ Missing run method
class MyNode(Node):
    def get_parameters(self):
        return {}
    # No run method!

# ✅ Implement both required methods
class MyNode(Node):
    def get_parameters(self) -> Dict[str, NodeParameter]:
        return {}
    
    def run(self, **kwargs) -> Dict[str, Any]:
        return {}
```

## Issue: Parameter Validation Errors

### Error: "Parameter 'X' is required"
```python
# Problem: Required parameter not provided
workflow.add_node("node", MyNode())  # Missing required param

# Solution: Provide required parameters
workflow.add_node("node", MyNode(), required_param="value")
```

### Error: "Invalid type for parameter"
```python
# Problem: Wrong type provided
workflow.add_node("node", MyNode(), count="five")  # String for int

# Solution: Provide correct type
workflow.add_node("node", MyNode(), count=5)
```

## Issue: Import Errors

### HTTPClientNode Not Found
```python
# ❌ Old import (deprecated)
from kailash.nodes.api import HTTPClientNode
# ImportError: cannot import name 'HTTPClientNode'

# ✅ New import
from kailash.nodes.api import HTTPRequestNode
```

### Missing Type Imports
```python
# ❌ Missing Tuple import
def method(self) -> Tuple[str, int]:  # NameError: name 'Tuple' is not defined

# ✅ Complete imports
from typing import Any, Dict, List, Tuple, Optional
```

## Issue: Runtime Type Errors

### Working with Any Type
```python
# When using Any type, validate at runtime
def run(self, **kwargs):
    data = kwargs['data']  # type: Any
    
    # ✅ Add runtime validation
    if not isinstance(data, list):
        raise ValueError(f"Expected list, got {type(data)}")
    
    # Safe to use as list now
    for item in data:
        process(item)
```

## Issue: Cache Decorator Not Found

### Error: "@cached_query not defined"
```python
# ❌ This decorator doesn't exist in Kailash
@cached_query
def my_method(self):
    pass

# ✅ Use Python's built-in caching
from functools import lru_cache

@lru_cache(maxsize=128)
def my_method(self):
    pass
```

## Issue: Node Not Registered

### Node not available in workflow
```python
# Problem: Custom node not registered
workflow.add_node("MyNode", "node1")  # Error: Unknown node type

# Solution 1: Use node instance directly
from my_module import MyCustomNode
workflow.add_node("node1", MyCustomNode())

# Solution 2: Register the node
from kailash.nodes import register_node
register_node("MyNode", MyCustomNode)
workflow.add_node("MyNode", "node1")
```

## Debugging Tips

### 1. Test Node in Isolation
```python
# Test your node directly
node = MyCustomNode(name="test")

# Check parameters
params = node.get_parameters()
print("Parameters:", params)

# Test with valid inputs
result = node.run(param1="value1", param2=123)
print("Result:", result)
```

### 2. Enable Verbose Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Your node will now show detailed logs
```

### 3. Check Parameter Schema
```python
# Verify parameter definitions
node = MyCustomNode(name="test")
for name, param in node.get_parameters().items():
    print(f"{name}: type={param.type}, required={param.required}")
```

### 4. Use Type Checking
```python
# Add type hints and use mypy
from typing import Any, Dict
from kailash.nodes.base import Node, NodeParameter

class MyNode(Node):
    def get_parameters(self) -> Dict[str, NodeParameter]:
        # Type checker will validate this
        return {}
```

## Common Mistakes Checklist

- [ ] Using `List[T]`, `Dict[K,V]` instead of `list`, `dict`
- [ ] Missing `run()` method implementation
- [ ] Wrong return type from `get_parameters()`
- [ ] Not handling optional parameters with defaults
- [ ] Using deprecated class names (HTTPClientNode)
- [ ] Not validating `Any` type parameters at runtime
- [ ] Forgetting to import required types
- [ ] Not providing required parameters when adding to workflow

---

*Need more help? Check the [examples/](examples/) directory for working implementations.*