# Custom Node Development - CLAUDE.md

## 📁 Navigation
- **Getting Started**: [01-getting-started.md](01-getting-started.md)
- **Type Constraints**: [02-parameter-types.md](02-parameter-types.md) ⚠️ CRITICAL
- **Common Patterns**: [03-common-patterns.md](03-common-patterns.md)
- **Error Handling**: [04-error-handling.md](04-error-handling.md)
- **Testing**: [05-testing-nodes.md](05-testing-nodes.md)
- **Examples**: [examples/](examples/)
- **Troubleshooting**: [troubleshooting.md](troubleshooting.md)

## 🚨 Critical Rules

1. **Parameter types**: ONLY use `str`, `int`, `float`, `bool`, `list`, `dict`, `Any`
2. **Never use generics**: No `List[T]`, `Dict[K,V]`, `Optional[T]`, `Union[A,B]`
3. **Both methods required**: Must implement `get_parameters()` AND `run()`
4. **HTTPClientNode deprecated**: Use `HTTPRequestNode` instead

## ⚡ Quick Fix Template

```python
from typing import Any, Dict
from kailash.nodes.base import Node, NodeParameter

class YourNode(Node):
    def get_parameters(self) -> Dict[str, NodeParameter]:
        return {
            'param': NodeParameter(
                name='param',
                type=str,  # Use basic type or Any
                required=True,
                description='Description'
            )
        }
    
    def run(self, **kwargs) -> Dict[str, Any]:
        return {'result': kwargs['param']}
```