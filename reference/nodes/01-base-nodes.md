# Base Node Classes

**Module**: `kailash.nodes.base*`  
**Last Updated**: 2025-01-06

This document covers the foundational base classes that all nodes inherit from.

## Table of Contents
- [Core Base Classes](#core-base-classes)
- [Specialized Base Classes](#specialized-base-classes)
- [Node Development Guide](#node-development-guide)

## Core Base Classes

### Node
- **Module**: `kailash.nodes.base`
- **Description**: Abstract base class for all synchronous nodes
- **Key Methods**:
  - `get_parameters()`: Define node parameters
  - `run(context, **kwargs)`: Execute node logic
  - `get_output_schema()`: Optional output validation

### AsyncNode
- **Module**: `kailash.nodes.base_async`
- **Description**: Abstract base class for all asynchronous nodes
- **Key Methods**:
  - `async run(context, **kwargs)`: Async execution

## Specialized Base Classes

### CycleAwareNode
- **Module**: `kailash.nodes.base_cycle_aware`
- **Description**: Base class for nodes that participate in cyclic workflows
- **Key Methods**:
  - `get_iteration(context)`: Get current iteration number (0-based)
  - `get_previous_state(context)`: Access state from previous iteration
  - `set_cycle_state(state)`: Persist state for next iteration
  - `accumulate_values(context, key, value)`: Build rolling window of values
  - `detect_convergence_trend(context, metric_key)`: Analyze convergence patterns
  - `log_cycle_info(context, message)`: Log structured cycle information
- **Use Cases**:
  - Retry patterns with exponential backoff
  - Iterative optimization algorithms
  - Data quality improvement loops
  - Stream processing with batches
  - Multi-stage processing pipelines
- **Example**:
  ```python
  class OptimizerNode(CycleAwareNode):
      def run(self, context, **kwargs):
          iteration = self.get_iteration(context)
          prev_state = self.get_previous_state(context)
          
          # Optimization logic
          value = prev_state.get("value", 0.5) + 0.1
          self.set_cycle_state({"value": value})
          
          # Track convergence
          self.accumulate_values(context, "value", value)
          trend = self.detect_convergence_trend(context, "value")
          
          return {
              "value": value,
              "converged": value > 0.95 or trend["converging"]
          }
  ```

## Node Development Guide

### Creating a Custom Node
```python
from kailash.nodes.base import Node

class MyCustomNode(Node):
    def get_parameters(self):
        return {
            "param1": {"type": str, "required": True},
            "param2": {"type": int, "default": 10}
        }

    def run(self, context, **kwargs):
        param1 = kwargs.get("param1")
        param2 = kwargs.get("param2", 10)

        # Node logic here
        result = f"{param1} processed with {param2}"

        return {"result": result}

    def get_output_schema(self):
        return {
            "type": "object",
            "properties": {
                "result": {"type": "string"}
            },
            "required": ["result"]
        }
```

### Best Practices
1. Always inherit from `Node` or `AsyncNode`
2. Define clear parameter schemas in `get_parameters()`
3. Implement output validation with `get_output_schema()`
4. Handle errors gracefully
5. Document expected inputs and outputs
6. Follow the naming convention: `YourPurposeNode`

## See Also
- [AI Nodes](02-ai-nodes.md) - AI and ML node implementations
- [Data Nodes](03-data-nodes.md) - Data processing nodes
- [API Reference](../api/03-nodes-base.yaml) - Detailed API documentation