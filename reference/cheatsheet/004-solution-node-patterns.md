# Common Node Patterns

## Data I/O
```python
# CSV Reading
workflow.add_node("csv_in", CSVReaderNode(),
    file_path="data.csv",
    delimiter=",",
    has_header=True
)

# JSON Writing
workflow.add_node("json_out", JSONWriterNode(),
    file_path="output.json",
    indent=2
)
```

## AI/LLM Integration
```python
# LLM Processing
workflow.add_node("llm", LLMAgentNode(),
    provider="openai",
    model="gpt-4",
    temperature=0.7,
    system_prompt="You are a data analyst."
)

# Generate Embeddings
workflow.add_node("embedder", EmbeddingGeneratorNode(),
    provider="openai",
    model="text-embedding-ada-002"
)
```

## API Calls
```python
# Simple HTTP Request
workflow.add_node("api_call", HTTPRequestNode(),
    url="https://api.example.com/data",
    method="GET",
    headers={"Authorization": "Bearer token"}
)

# REST Client with Auth
workflow.add_node("rest", RESTClientNode(),
    base_url="https://api.example.com",
    auth_type="bearer",
    auth_config={"token": "your-token"}
)
```

## Data Transformation
```python
workflow.add_node("transform", DataTransformerNode(),
    operations=[
        {"type": "filter", "condition": "status == 'active'"},
        {"type": "map", "expression": "{'id': id, 'name': name.upper()}"},
        {"type": "sort", "key": "created_at", "reverse": True}
    ]
)
```

## Conditional Logic
```python
# Route based on conditions
workflow.add_node("router", SwitchNode(),
    conditions=[
        {"output": "high", "expression": "value > 100"},
        {"output": "medium", "expression": "value > 50"},
        {"output": "low", "expression": "value <= 50"}
    ]
)

# Connect conditional outputs
workflow.connect("router", "high_handler", mapping={"high": "input"})
workflow.connect("router", "medium_handler", mapping={"medium": "input"})
workflow.connect("router", "low_handler", mapping={"low": "input"})
```

## Custom Python Code
```python
workflow.add_node("custom", PythonCodeNode(),
    code='''
def execute(data):
    # Custom processing logic
    result = []
    for item in data:
        if item['score'] > 0.8:
            result.append({
                'id': item['id'],
                'category': 'high_confidence',
                'score': item['score']
            })
    return {'filtered': result}
'''
)
```