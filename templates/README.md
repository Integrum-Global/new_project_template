# Solution Templates

This directory contains ready-to-use templates for common solution patterns with the Kailash SDK. Each template provides a complete working example that you can copy and modify for your specific needs.

## Available Templates

### 1. Basic ETL Pipeline (`basic_etl/`)
Extract, Transform, and Load data between different formats and systems.
- CSV to CSV transformation
- Data filtering and aggregation
- Error handling and validation

### 2. API Integration (`api_integration/`)
Connect to external APIs and process responses.
- HTTP request handling
- Authentication patterns
- Response processing and storage
- Rate limiting and retries

### 3. AI/LLM Analysis (`ai_analysis/`)
Leverage AI models for data analysis and insights.
- Document analysis
- Text summarization
- Data enrichment
- Batch processing patterns

## Common Solution Patterns

### Data Processing Pipeline
```python
# Extract -> Transform -> Load (ETL)
workflow.add_node("extract", CSVReaderNode, file_path="raw_data.csv")
workflow.add_node("transform", DataTransformerNode, operations=[...])
workflow.add_node("load", CSVWriterNode, file_path="processed_data.csv")

workflow.connect("extract", "transform", mapping={"data": "input"})
workflow.connect("transform", "load", mapping={"output": "data"})
```

### API Integration
```python
# API Call -> Process -> Store
workflow.add_node("api_call", HTTPRequestNode, 
    url="https://api.example.com/data",
    method="GET",
    headers={"Authorization": "Bearer YOUR_TOKEN"}
)
workflow.add_node("process", PythonCodeNode, code="""
def execute(response_data):
    # Custom processing logic here
    return {"processed": process_api_response(response_data)}
""")
workflow.add_node("store", JSONWriterNode, file_path="results.json")

workflow.connect("api_call", "process", mapping={"response": "input"})
workflow.connect("process", "store", mapping={"processed": "data"})
```

### AI/LLM Analysis
```python
# Data -> AI Analysis -> Results
workflow.add_node("input", JSONReaderNode, file_path="documents.json")
workflow.add_node("ai_analysis", LLMAgentNode,
    provider="openai",
    model="gpt-4",
    system_prompt="Analyze the following data and provide insights..."
)
workflow.add_node("output", JSONWriterNode, file_path="analysis_results.json")

workflow.connect("input", "ai_analysis", mapping={"data": "prompt"})
workflow.connect("ai_analysis", "output", mapping={"response": "data"})
```

## How to Use Templates

1. **Choose a Template**
   - Browse the template directories
   - Select the one closest to your use case

2. **Copy to Your Solution**
   ```bash
   cp -r templates/basic_etl/* src/solutions/my_solution/
   ```

3. **Customize**
   - Update the workflow ID and name
   - Modify node configurations
   - Add your business logic
   - Update documentation

4. **Validate**
   ```bash
   python reference/validate_kailash_code.py src/solutions/my_solution/workflow.py
   ```

## Template Structure

Each template includes:
- `workflow.py` - Main workflow implementation
- `config.py` - Configuration management
- `README.md` - Template-specific documentation
- `config.yaml` - Default configuration
- `examples/` - Working examples
  - `basic_usage.py` - Simple example
  - `advanced_usage.py` - Full-featured example
- `tests/` - Unit and integration tests

## Creating New Templates

When creating a new template:
1. Follow the standard solution structure
2. Include comprehensive examples
3. Add clear documentation
4. Test with real scenarios
5. Submit a PR with your template

## Best Practices

- Start with the simplest template that meets your needs
- Modify incrementally and test frequently
- Use debug mode during development
- Validate your code before deployment
- Document any template modifications