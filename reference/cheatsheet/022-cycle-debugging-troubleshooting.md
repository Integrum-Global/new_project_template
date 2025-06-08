# Cycle Debugging & Troubleshooting

## Safe State Access Patterns

### ✅ Correct: Use .get() with defaults
```python
def run(self, context, **kwargs):
    # Always use .get() with default for cycle state
    cycle_info = context.get("cycle", {})
    iteration = cycle_info.get("iteration", 0)
    node_state = cycle_info.get("node_state") or {}
    
    # Safe access to nested state
    prev_error = node_state.get("error", float('inf'))
    learning_rate = node_state.get("learning_rate", 0.5)
    
    return {"result": processed_data}
```

### ❌ Wrong: Direct key access
```python
def run(self, context, **kwargs):
    # This will cause KeyError in cycles
    cycle_info = context["cycle"]              # KeyError if no cycle
    iteration = cycle_info["iteration"]        # KeyError if missing
    node_state = cycle_info["node_state"]      # KeyError if None
    
    return {"result": processed_data}
```

## Common Cycle Errors and Fixes

### 1. Parameter Propagation Issues

**Error**: Values don't propagate between iterations
```python
# ❌ Problem: Parameters revert to defaults each iteration
class ProcessorNode(Node):
    def run(self, context, **kwargs):
        quality = kwargs.get("quality", 0.0)  # Always gets 0.0!
        return {"quality": quality + 0.2}
```

**✅ Solution**: Use cycle state or correct mapping
```python
# Option 1: Use cycle state
class ProcessorNode(Node):
    def run(self, context, **kwargs):
        cycle_info = context.get("cycle", {})
        node_state = cycle_info.get("node_state") or {}
        
        # Get from cycle state if available
        quality = node_state.get("quality", kwargs.get("quality", 0.0))
        
        new_quality = quality + 0.2
        
        return {
            "quality": new_quality,
            "_cycle_state": {"quality": new_quality}
        }

# Option 2: Check parameter mapping
workflow.connect("processor", "processor",
    mapping={"quality": "quality"},  # Ensure correct mapping
    cycle=True)
```

### 2. PythonCodeNode Parameter Access

**Error**: `NameError: name 'count' is not defined`
```python
# ❌ Problem: Direct parameter access without try/except
code = '''
current_count = count  # NameError on first iteration
result = {"count": current_count + 1}
'''
```

**✅ Solution**: Always use try/except pattern
```python
code = '''
try:
    current_count = count  # From previous iteration
    print(f"Received count: {current_count}")
except NameError:
    current_count = 0      # Default for first iteration
    print("First iteration, starting at 0")

# Process
current_count += 1
done = current_count >= 5

result = {
    "count": current_count,
    "done": done
}
'''
```

### 3. None Value Security Errors

**Error**: `SecurityError: Input type not allowed: <class 'NoneType'>`
```python
# ❌ Problem: Passing None values to security-validated nodes
def run(self, context, **kwargs):
    cycle_state = context.get("cycle", {}).get("node_state")  # Could be None
    return {"state": cycle_state}  # Security error if None
```

**✅ Solution**: Filter None values
```python
def run(self, context, **kwargs):
    cycle_info = context.get("cycle", {})
    node_state = cycle_info.get("node_state") or {}  # Default to empty dict
    
    # Filter None values from output
    result = {"processed": True}
    if node_state:  # Only include if not empty
        result["previous_state"] = {k: v for k, v in node_state.items() if v is not None}
    
    return result
```

### 4. Multi-Node Cycle Detection

**Error**: Nodes in middle of cycle not detected
```python
# ❌ Problem: Only A and C detected in A → B → C → A cycle
workflow.connect("A", "B")          # Regular
workflow.connect("B", "C")          # Regular  
workflow.connect("C", "A", cycle=True)  # Only closing edge marked
# Result: B is treated as separate DAG node
```

**✅ Solution**: Mark only closing edge, ensure proper grouping
```python
# Current workaround: Use direct cycles when possible
workflow.connect("A", "B")
workflow.connect("B", "A", cycle=True)  # Simple 2-node cycle

# For complex multi-node cycles, verify detection
# Check workflow.graph.detect_cycles() output
cycles = workflow.graph.detect_cycles()
print(f"Detected cycles: {cycles}")
```

### 5. Infinite Cycles

**Error**: `Warning: Cycle exceeded max_iterations`
```python
# ❌ Problem: Convergence condition never satisfied
workflow.connect("processor", "processor",
    cycle=True,
    max_iterations=10,
    convergence_check="done == True")  # 'done' never becomes True
```

**✅ Solution**: Debug convergence conditions
```python
# Add debugging node before convergence check
class DebugNode(Node):
    def run(self, context, **kwargs):
        cycle_info = context.get("cycle", {})
        iteration = cycle_info.get("iteration", 0)
        
        print(f"Iteration {iteration}: {kwargs}")
        
        # Check convergence field
        done = kwargs.get("done", False)
        print(f"Convergence field 'done': {done} (type: {type(done)})")
        
        return kwargs  # Pass through

workflow.add_node("debug", DebugNode())
workflow.connect("processor", "debug")
workflow.connect("debug", "processor",
    cycle=True,
    max_iterations=10,
    convergence_check="done == True")
```

## Debugging Techniques

### 1. Add Logging Nodes
```python
class CycleLoggerNode(Node):
    """Logs cycle state for debugging."""
    
    def run(self, context, **kwargs):
        cycle_info = context.get("cycle", {})
        iteration = cycle_info.get("iteration", 0)
        
        print(f"=== Iteration {iteration} ===")
        print(f"Context: {context}")
        print(f"Parameters: {kwargs}")
        print(f"Node state: {cycle_info.get('node_state', {})}")
        print("=" * 30)
        
        return kwargs  # Pass through unchanged

# Insert into cycle for debugging
workflow.add_node("logger", CycleLoggerNode())
workflow.connect("processor", "logger")
workflow.connect("logger", "processor", cycle=True)
```

### 2. Monitor Parameter Flow
```python
class ParameterMonitorNode(Node):
    """Monitors parameter propagation between iterations."""
    
    def run(self, context, **kwargs):
        cycle_info = context.get("cycle", {})
        iteration = cycle_info.get("iteration", 0)
        
        # Track which parameters are received
        received_params = list(kwargs.keys())
        
        # Track parameter values
        param_values = {k: v for k, v in kwargs.items() if isinstance(v, (int, float, str, bool))}
        
        print(f"Iteration {iteration}:")
        print(f"  Received parameters: {received_params}")
        print(f"  Parameter values: {param_values}")
        
        # Check for expected parameters
        expected = ["data", "quality", "threshold"]
        missing = [p for p in expected if p not in kwargs]
        if missing:
            print(f"  WARNING: Missing expected parameters: {missing}")
        
        return kwargs
```

### 3. Validate Convergence Logic
```python
class ConvergenceValidatorNode(Node):
    """Validates convergence conditions."""
    
    def run(self, context, **kwargs):
        # Check convergence fields
        convergence_fields = ["done", "converged", "should_continue", "quality_sufficient"]
        found_fields = [f for f in convergence_fields if f in kwargs]
        
        print(f"Convergence fields found: {found_fields}")
        
        for field in found_fields:
            value = kwargs[field]
            print(f"  {field}: {value} (type: {type(value)})")
            
            # Validate boolean fields
            if field in ["done", "converged", "should_continue", "quality_sufficient"]:
                if not isinstance(value, bool):
                    print(f"    WARNING: {field} should be boolean, got {type(value)}")
        
        return kwargs
```

## Testing Patterns for Cycles

### Flexible Assertions
```python
import pytest

def test_cycle_execution():
    """Test cycle with flexible assertions."""
    workflow = create_cycle_workflow()
    runtime = LocalRuntime()
    
    results, run_id = runtime.execute(workflow, parameters={
        "processor": {"data": [1, 2, 3], "target": 10}
    })
    
    # ✅ Good: Use ranges for iteration counts
    final_result = results.get("processor", {})
    iteration = final_result.get("iteration", 0)
    
    # Allow for some variation in iteration count
    assert 3 <= iteration <= 7, f"Expected 3-7 iterations, got {iteration}"
    
    # ❌ Avoid: Exact iteration assertions
    # assert iteration == 5  # Too rigid, can fail due to implementation details
    
    # ✅ Good: Check convergence was achieved
    converged = final_result.get("converged", False)
    assert converged, "Cycle should have converged"
    
    # ✅ Good: Check final quality is in acceptable range
    quality = final_result.get("quality", 0)
    assert 0.8 <= quality <= 1.0, f"Quality {quality} not in expected range"
```

### Mock-Free Cycle Testing
```python
def test_cycle_without_mocks():
    """Test real cycle execution without mocks."""
    
    # Create real workflow
    workflow = Workflow("test-cycle", "Test Cycle")
    
    # Use simple, predictable nodes
    workflow.add_node("counter", PythonCodeNode(), code='''
try:
    count = count
except:
    count = 0

count += 1
result = {"count": count, "done": count >= 3}
''')
    
    # Simple cycle
    workflow.connect("counter", "counter",
        mapping={"result.count": "count"},
        cycle=True,
        max_iterations=10,
        convergence_check="done == True")
    
    # Execute and verify
    runtime = LocalRuntime()
    results, run_id = runtime.execute(workflow)
    
    final_result = results.get("counter", {})
    assert final_result.get("result", {}).get("count") == 3
    assert final_result.get("result", {}).get("done") is True
```

## Performance Debugging

### Memory Usage Monitoring
```python
import psutil
import os

class MemoryMonitorNode(Node):
    """Monitors memory usage during cycles."""
    
    def run(self, context, **kwargs):
        # Get current process memory
        process = psutil.Process(os.getpid())
        memory_mb = process.memory_info().rss / 1024 / 1024
        
        cycle_info = context.get("cycle", {})
        iteration = cycle_info.get("iteration", 0)
        
        # Track memory growth
        node_state = cycle_info.get("node_state") or {}
        prev_memory = node_state.get("memory_mb", 0)
        memory_growth = memory_mb - prev_memory if prev_memory > 0 else 0
        
        # Warning for memory growth
        if memory_growth > 10:  # More than 10MB growth
            print(f"WARNING: Memory grew by {memory_growth:.1f}MB in iteration {iteration}")
        
        print(f"Iteration {iteration}: Memory usage {memory_mb:.1f}MB")
        
        return {
            **kwargs,
            "_cycle_state": {"memory_mb": memory_mb}
        }
```

### Execution Time Monitoring
```python
import time

class TimingMonitorNode(Node):
    """Monitors execution time per iteration."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.start_time = None
    
    def run(self, context, **kwargs):
        current_time = time.time()
        cycle_info = context.get("cycle", {})
        iteration = cycle_info.get("iteration", 0)
        
        if iteration == 0:
            self.start_time = current_time
            iteration_time = 0
        else:
            node_state = cycle_info.get("node_state") or {}
            prev_time = node_state.get("last_time", self.start_time)
            iteration_time = current_time - prev_time
        
        total_time = current_time - self.start_time if self.start_time else 0
        
        print(f"Iteration {iteration}: {iteration_time:.3f}s (total: {total_time:.3f}s)")
        
        # Warning for slow iterations
        if iteration_time > 5.0:  # More than 5 seconds
            print(f"WARNING: Slow iteration {iteration}: {iteration_time:.3f}s")
        
        return {
            **kwargs,
            "_cycle_state": {"last_time": current_time}
        }
```

## Best Practices for Cycle Debugging

### 1. Start Simple
```python
# ✅ Good: Start with minimal cycle
workflow.add_node("simple", PythonCodeNode(), code='''
try:
    count = count
except:
    count = 0

count += 1
result = {"count": count, "done": count >= 3}
''')

workflow.connect("simple", "simple", 
    mapping={"result.count": "count"},
    cycle=True, max_iterations=5)
```

### 2. Add Debugging Incrementally
```python
# Add one debugging feature at a time
# 1. Start with basic logging
# 2. Add parameter monitoring  
# 3. Add convergence validation
# 4. Add performance monitoring
```

### 3. Use Descriptive Names
```python
# ✅ Good: Clear field names for debugging
return {
    "processed_data": data,
    "current_quality_score": quality,
    "convergence_threshold_met": quality >= threshold,
    "should_continue_processing": not converged,
    "debug_iteration_count": iteration
}

# ❌ Avoid: Ambiguous names
return {"data": data, "q": quality, "done": converged}
```

### 4. Validate Early and Often
```python
def run(self, context, **kwargs):
    # Validate inputs early
    data = kwargs.get("data")
    if data is None:
        raise ValueError("Data parameter is required")
    
    if not isinstance(data, list):
        raise TypeError(f"Data must be list, got {type(data)}")
    
    # Process...
    
    # Validate outputs before returning
    result = process_data(data)
    if not isinstance(result, dict):
        raise TypeError(f"Result must be dict, got {type(result)}")
    
    return result
```