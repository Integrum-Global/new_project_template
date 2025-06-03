# API Integration Template

A comprehensive template for integrating with external APIs using the Kailash SDK.

## Overview

This template provides a foundation for:
- Making HTTP requests to external APIs
- Handling authentication and headers
- Processing API responses
- Validating and enriching data
- Storing results in multiple formats
- Error handling and retries

## Features

- HTTP request handling (GET, POST, PUT, DELETE)
- Authentication support (Bearer tokens, API keys)
- Automatic retries with exponential backoff
- Response processing and transformation
- Data validation and enrichment
- Multiple output formats (JSON, CSV)
- Comprehensive error handling

## Quick Start

1. **Copy this template to your solution:**
   ```bash
   cp -r templates/api_integration/* src/solutions/my_api_solution/
   ```

2. **Configure your API settings:**
   Edit `config.yaml`:
   ```yaml
   api_url: "https://api.example.com/data"
   method: "GET"
   headers:
     Authorization: "Bearer YOUR_TOKEN"
   ```

3. **Set environment variables (for sensitive data):**
   ```bash
   export API_TOKEN="your-api-token"
   export API_KEY="your-api-key"
   ```

4. **Run the integration:**
   ```bash
   python -m solutions.my_api_solution
   ```

## Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `api_url` | string | required | API endpoint URL |
| `method` | string | "GET" | HTTP method |
| `headers` | dict | {} | Request headers |
| `params` | dict | {} | Query parameters |
| `body` | dict | {} | Request body (for POST/PUT) |
| `timeout` | int | 30000 | Request timeout (ms) |
| `retry_count` | int | 3 | Number of retries |
| `retry_delay` | int | 1000 | Delay between retries (ms) |
| `output_json` | string | "data/results.json" | JSON output path |
| `output_csv` | string | "data/results.csv" | CSV output path |

## Authentication Patterns

### Bearer Token
```yaml
headers:
  Authorization: "Bearer ${API_TOKEN}"
```

### API Key in Header
```yaml
headers:
  X-API-Key: "${API_KEY}"
```

### API Key in Query
```yaml
params:
  api_key: "${API_KEY}"
```

### Basic Authentication
```python
import base64
auth = base64.b64encode(f"{username}:{password}".encode()).decode()
headers = {"Authorization": f"Basic {auth}"}
```

## Common API Patterns

### Pagination
```python
workflow.add_node(
    "paginate",
    PythonCodeNode,
    code="""
def execute(data):
    all_records = []
    page = 1
    
    while True:
        response = make_api_call(page=page)
        records = response.get('items', [])
        all_records.extend(records)
        
        if not response.get('has_next'):
            break
        page += 1
    
    return {"all_records": all_records}
"""
)
```

### Rate Limiting
```python
workflow.add_node(
    "rate_limit",
    PythonCodeNode,
    code="""
import time

def execute(data):
    # Implement rate limiting
    requests_per_minute = 60
    delay = 60 / requests_per_minute
    
    results = []
    for item in data['items']:
        result = process_item(item)
        results.append(result)
        time.sleep(delay)
    
    return {"results": results}
"""
)
```

### Batch Processing
```python
workflow.add_node(
    "batch_api",
    HTTPRequestNode,
    url="https://api.example.com/batch",
    method="POST",
    body={
        "items": "${items}",
        "batch_size": 100
    }
)
```

## Error Handling

### API Error Responses
The template includes handling for:
- HTTP status codes
- Timeout errors
- Connection errors
- Rate limit errors (429)
- Server errors (5xx)

### Custom Error Handling
```python
def execute(response):
    if response['status_code'] == 429:
        # Rate limited
        retry_after = response['headers'].get('Retry-After', 60)
        raise RetryableError(f"Rate limited. Retry after {retry_after}s")
    
    if response['status_code'] >= 500:
        # Server error - retry
        raise RetryableError("Server error")
    
    if response['status_code'] >= 400:
        # Client error - don't retry
        raise ValueError(f"Client error: {response['body']}")
```

## Examples

See the `examples/` directory for:
- `basic_usage.py` - Simple API call
- `advanced_usage.py` - Complex integration with pagination and error handling

## Testing

### Mock API Responses
```python
def test_api_integration(mocker):
    # Mock the HTTP request
    mock_response = {
        "status_code": 200,
        "body": {"items": [{"id": 1, "name": "Test"}]}
    }
    mocker.patch('HTTPRequestNode.run', return_value=mock_response)
    
    # Run workflow
    results = run_workflow()
    assert len(results['processed']) == 1
```

### Integration Tests
```bash
# Run against test API
export API_URL="https://api-test.example.com"
pytest tests/test_integration.py
```

## Best Practices

1. **Always use environment variables for sensitive data**
2. **Implement proper error handling and retries**
3. **Log API calls for debugging**
4. **Validate API responses before processing**
5. **Handle rate limits gracefully**
6. **Use appropriate timeouts**
7. **Test with mock responses first**

## Troubleshooting

### "Connection timeout"
- Increase timeout value in config
- Check network connectivity
- Verify API endpoint is correct

### "401 Unauthorized"
- Check authentication credentials
- Verify token hasn't expired
- Ensure headers are formatted correctly

### "429 Too Many Requests"
- Implement rate limiting
- Add delays between requests
- Use batch endpoints if available

### "Invalid JSON response"
- Check Content-Type header
- Verify API returns JSON
- Handle non-JSON responses gracefully