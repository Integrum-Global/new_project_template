# Control Flow Patterns

Dynamic workflow routing and conditional logic patterns using SwitchNode and other control structures.

## 1. Simple Boolean Routing

**Purpose**: Route workflow based on true/false conditions

```python
from kailash import Workflow
from kailash.nodes.logic import SwitchNode
from kailash.nodes.code import PythonCodeNode
from kailash.runtime.local import LocalRuntime

workflow = Workflow("validation_flow", "Validation Workflow")

# Validation node that sets is_valid flag
workflow.add_node("validator", PythonCodeNode(),
    code="""
# Validate data
is_valid = True
errors = []

for record in data:
    if not record.get('email') or '@' not in record['email']:
        errors.append(f"Invalid email: {record}")
        is_valid = False

result = {
    'data': data,
    'is_valid': is_valid,
    'errors': errors
}
"""
)

# Switch node for boolean routing
workflow.add_node("switch", SwitchNode(),
    condition_field="is_valid",
    true_route="success_handler",
    false_route="error_handler"
)

# Success path
workflow.add_node("success_handler", PythonCodeNode(),
    code="result = {'status': 'success', 'processed': len(data)}"
)

# Error path
workflow.add_node("error_handler", PythonCodeNode(),
    code="result = {'status': 'failed', 'errors': errors}"
)

# Connections
workflow.connect("validator", "switch", mapping={"result": "input"})
workflow.connect("switch", "success_handler", 
    route="success_handler",
    mapping={"input.data": "data"})
workflow.connect("switch", "error_handler",
    route="error_handler", 
    mapping={"input.errors": "errors"})

# Execute
runtime = LocalRuntime()
results, run_id = runtime.execute(workflow, parameters={
    "validator": {"data": [{"email": "test@example.com"}, {"email": "invalid"}]}
})
```

## 2. Multi-Case Status Routing

**Purpose**: Route based on multiple possible values

```python
# Route based on data size categories
workflow.add_node("categorizer", PythonCodeNode(),
    code="""
size = len(data)
if size == 0:
    status = "empty"
elif size < 100:
    status = "small"
elif size < 1000:
    status = "medium"
else:
    status = "large"

result = {"data": data, "status": status, "size": size}
"""
)

workflow.add_node("router", SwitchNode(),
    condition_field="status",
    routes={
        "empty": "error_handler",
        "small": "simple_processor",
        "medium": "standard_processor",
        "large": "batch_processor"
    }
)

# Different processors for each size
workflow.add_node("error_handler", PythonCodeNode(),
    code="result = {'error': 'No data to process'}"
)

workflow.add_node("simple_processor", PythonCodeNode(),
    code="result = [item * 2 for item in data]"  # Process all at once
)

workflow.add_node("standard_processor", PythonCodeNode(),
    code="""
# Process with progress tracking
result = []
for i, item in enumerate(data):
    result.append(item * 2)
    if i % 10 == 0:
        print(f"Processed {i}/{len(data)}")
"""
)

workflow.add_node("batch_processor", PythonCodeNode(),
    code="""
# Process in batches
batch_size = 100
result = []
for i in range(0, len(data), batch_size):
    batch = data[i:i+batch_size]
    processed_batch = [item * 2 for item in batch]
    result.extend(processed_batch)
    print(f"Processed batch {i//batch_size + 1}")
"""
)

# Connect all routes
workflow.connect("categorizer", "router")
workflow.connect("router", "error_handler", route="error_handler")
workflow.connect("router", "simple_processor", 
    route="simple_processor",
    mapping={"data": "data"})
workflow.connect("router", "standard_processor",
    route="standard_processor",
    mapping={"data": "data"})
workflow.connect("router", "batch_processor",
    route="batch_processor", 
    mapping={"data": "data"})
```

## 3. Critical Pattern: Conditional Cycles (A→B→C→D→Switch→B|E)

**Purpose**: Quality improvement loops with conditional exits

```python
workflow = Workflow("quality_improvement", "Iterative Quality Improvement")

# A: Input node
workflow.add_node("input", PythonCodeNode(),
    code="result = {'text': text, 'iteration': 0}"
)

# B: Processor node
workflow.add_node("processor", PythonCodeNode(),
    code="""
# Enhance text quality
enhanced = text.strip().capitalize()
if 'iteration' in kwargs.get('context', {}).get('cycle', {}):
    iteration = kwargs['context']['cycle']['iteration'] + 1
    enhanced = f"[v{iteration}] {enhanced}"
else:
    iteration = 1

result = {
    'text': enhanced,
    'iteration': iteration
}
"""
)

# C: Transformer node
workflow.add_node("transformer", PythonCodeNode(),
    code="""
# Add metadata
import datetime
result = {
    'text': text,
    'timestamp': datetime.datetime.now().isoformat(),
    'length': len(text),
    'iteration': iteration
}
"""
)

# D: Quality checker node
workflow.add_node("checker", PythonCodeNode(),
    code="""
# Check quality metrics
quality_score = min(1.0, length / 100)  # Simple quality metric
should_continue = quality_score < 0.8 and iteration < 5

result = {
    'data': {
        'text': text,
        'quality': quality_score,
        'iteration': iteration
    },
    'route_decision': 'retry' if should_continue else 'finish',
    'should_continue': should_continue
}
"""
)

# Switch node for routing decision
workflow.add_node("switch", SwitchNode(),
    condition_field="route_decision",
    routes={
        "retry": "processor",
        "finish": "output"
    }
)

# E: Output node
workflow.add_node("output", PythonCodeNode(),
    code="""
result = {
    'final_text': data['text'],
    'quality_score': data['quality'],
    'iterations': data['iteration'],
    'status': 'completed'
}
"""
)

# Linear flow: A → B → C → D → Switch
workflow.connect("input", "processor", mapping={"result": "input"})
workflow.connect("processor", "transformer", mapping={"result.text": "text", "result.iteration": "iteration"})
workflow.connect("transformer", "checker", mapping={"result": "input"})
workflow.connect("checker", "switch", mapping={"result": "input"})

# Conditional routing from switch
workflow.connect("switch", "processor",  # Cycle back to B
    route="retry",
    mapping={"input.data.text": "text"},
    cycle=True,
    max_iterations=10,
    convergence_check="input.should_continue == False"
)

workflow.connect("switch", "output",  # Continue to E
    route="finish",
    mapping={"input.data": "data"}
)

# Execute with initial data
runtime = LocalRuntime()
results, run_id = runtime.execute(workflow, parameters={
    "input": {"text": "hello world"}
})
```

**Key Benefits**:
- Quality improvement loops with conditional exits
- Error handling with retry logic
- Dynamic workflow behavior based on data conditions
- Clean separation of business logic and routing logic

## 4. Multi-Level Decision Trees

**Purpose**: Complex nested routing logic

```python
# Customer routing workflow
workflow = Workflow("customer_routing", "Multi-Level Customer Router")

# First level: Active/Inactive status
workflow.add_node("status_router", SwitchNode(),
    condition_field="status",
    routes={
        "active": "tier_router",
        "inactive": "reactivation_flow"
    }
)

# Second level: Customer tier (for active customers)
workflow.add_node("tier_router", SwitchNode(),
    condition_field="tier",
    routes={
        "gold": "gold_benefits",
        "silver": "silver_benefits",
        "bronze": "bronze_benefits"
    }
)

# Third level: Region-specific processing (example for gold)
workflow.add_node("gold_region_router", SwitchNode(),
    condition_field="region",
    routes={
        "us": "us_gold_processor",
        "eu": "eu_gold_processor",
        "asia": "asia_gold_processor"
    }
)

# Connect the decision tree
workflow.connect("customer_data", "status_router")
workflow.connect("status_router", "tier_router", route="active")
workflow.connect("status_router", "reactivation_flow", route="inactive")

workflow.connect("tier_router", "gold_benefits", route="gold")
workflow.connect("gold_benefits", "gold_region_router")

workflow.connect("gold_region_router", "us_gold_processor", route="us")
workflow.connect("gold_region_router", "eu_gold_processor", route="eu")
workflow.connect("gold_region_router", "asia_gold_processor", route="asia")
```

## 5. Dynamic Route Generation

**Purpose**: Create routes based on runtime data

```python
workflow.add_node("dynamic_router", PythonCodeNode(),
    code="""
# Determine route based on complex logic
if data.get('priority') == 'high' and data.get('value') > 1000:
    route = 'vip_processing'
elif data.get('risk_score', 0) > 0.7:
    route = 'manual_review'
elif data.get('automated_eligible'):
    route = 'auto_processing'
else:
    route = 'standard_processing'

result = {
    'data': data,
    'selected_route': route,
    'reasoning': f"Routed to {route} based on business rules"
}
"""
)

# Use the dynamic route
workflow.add_node("route_switch", SwitchNode(),
    condition_field="selected_route",
    routes={
        "vip_processing": "vip_handler",
        "manual_review": "review_queue",
        "auto_processing": "automated_handler",
        "standard_processing": "standard_handler"
    }
)
```

## Best Practices

1. **Route Naming**: Use clear, descriptive route names
2. **Default Routes**: Always include error/default handling
3. **Route Documentation**: Document routing logic clearly
4. **Testing**: Test all possible routes thoroughly
5. **Monitoring**: Log routing decisions for debugging

## Common Patterns

### Error Recovery Pattern
```python
workflow.add_node("error_switch", SwitchNode(),
    condition_field="error_type",
    routes={
        "retryable": "retry_handler",
        "permanent": "error_logger",
        "unknown": "manual_intervention"
    }
)
```

### A/B Testing Pattern
```python
workflow.add_node("ab_test_router", PythonCodeNode(),
    code="""
import random
# 50/50 split for A/B test
route = 'variant_a' if random.random() < 0.5 else 'variant_b'
result = {'data': data, 'variant': route}
"""
)
```

### Load Balancing Pattern
```python
workflow.add_node("load_balancer", PythonCodeNode(),
    code="""
# Round-robin between processors
processor_count = 3
selected = hash(data.get('id', '')) % processor_count
result = {'data': data, 'processor': f'processor_{selected}'}
"""
)
```

## See Also
- [Core Patterns](01-core-patterns.md) - Basic workflow structures
- [Data Processing Patterns](03-data-processing-patterns.md) - Complex data handling
- [Error Handling Patterns](05-error-handling-patterns.md) - Resilient routing