# Best Practices Guide

This guide outlines best practices for developing solutions with the Kailash SDK.

## Table of Contents
- [Solution Design](#solution-design)
- [Code Organization](#code-organization)
- [Performance Considerations](#performance-considerations)
- [Error Handling](#error-handling)
- [Testing Strategies](#testing-strategies)
- [Security Best Practices](#security-best-practices)

## Solution Design

### 1. Reuse Before Create
- Check `shared/` for existing components
- Review other solutions for similar patterns
- Extract common functionality to shared components
- Use templates as starting points

### 2. Configuration Driven
- Externalize all variable parameters
- Use config files for flexibility
- Support environment variable overrides
- Validate configuration on startup

### 3. Design for Failure
- Plan for network interruptions
- Handle API rate limits gracefully
- Implement retry logic with backoff
- Provide meaningful error messages

### 4. Incremental Development
- Start with minimal viable workflow
- Test each addition thoroughly
- Add complexity gradually
- Keep commits atomic and focused

### 5. Documentation First
- Document requirements before coding
- Update docs as you develop
- Include examples and edge cases
- Explain non-obvious decisions

## Code Organization

### 1. Single Responsibility
- Each solution solves one specific problem
- Each node has one clear purpose
- Functions do one thing well
- Modules have cohesive functionality

### 2. Consistent Structure
```
solution/
├── __init__.py      # Package exports
├── __main__.py      # Entry point
├── workflow.py      # Main logic
├── config.py        # Configuration
├── processors.py    # Custom processors
├── utils.py         # Helper functions
└── tests/           # Test suite
```

### 3. Clear Naming
- Use descriptive variable names
- Follow Python naming conventions
- Be consistent across the codebase
- Avoid abbreviations and acronyms

### 4. Modular Design
- Keep functions small and focused
- Extract complex logic to functions
- Make components reusable
- Minimize dependencies between modules

## Performance Considerations

### 1. Data Size Awareness
```python
# Good: Process in chunks
def process_large_file(file_path, chunk_size=1000):
    with open(file_path) as f:
        chunk = []
        for line in f:
            chunk.append(line)
            if len(chunk) >= chunk_size:
                process_chunk(chunk)
                chunk = []
        if chunk:
            process_chunk(chunk)

# Bad: Load everything into memory
def process_large_file(file_path):
    with open(file_path) as f:
        data = f.readlines()  # Could run out of memory
        process_data(data)
```

### 2. Efficient API Usage
```python
# Good: Batch requests
def fetch_multiple_records(ids):
    return api.batch_get(ids)  # Single request

# Bad: Individual requests
def fetch_multiple_records(ids):
    results = []
    for id in ids:
        results.append(api.get(id))  # N requests
    return results
```

### 3. Resource Management
```python
# Good: Use context managers
with open('file.txt') as f:
    data = f.read()
    # File automatically closed

# Bad: Manual resource management
f = open('file.txt')
data = f.read()
f.close()  # Easy to forget
```

### 4. Caching Strategy
```python
from functools import lru_cache

# Good: Cache expensive operations
@lru_cache(maxsize=128)
def expensive_calculation(param):
    # Complex calculation here
    return result

# Consider: Time-based cache for API data
from cachetools import TTLCache
cache = TTLCache(maxsize=100, ttl=300)  # 5-minute cache
```

## Error Handling

### 1. Specific Exception Handling
```python
# Good: Catch specific exceptions
try:
    response = api.get_data()
except ConnectionError:
    logger.error("Network connection failed")
    raise
except JSONDecodeError:
    logger.error("Invalid JSON response")
    raise

# Bad: Catch all exceptions
try:
    response = api.get_data()
except Exception:
    pass  # Silently fails
```

### 2. Meaningful Error Messages
```python
# Good: Provide context
if not os.path.exists(file_path):
    raise FileNotFoundError(
        f"Configuration file not found at {file_path}. "
        f"Please create it from the template at {template_path}"
    )

# Bad: Generic message
if not os.path.exists(file_path):
    raise Exception("File not found")
```

### 3. Graceful Degradation
```python
# Good: Provide fallback behavior
def get_config_value(key, default=None):
    try:
        return config[key]
    except KeyError:
        logger.warning(f"Config key '{key}' not found, using default: {default}")
        return default

# Bad: Fail immediately
def get_config_value(key):
    return config[key]  # KeyError if missing
```

## Testing Strategies

### 1. Test Structure
```python
# Good: Arrange-Act-Assert pattern
def test_data_transformation():
    # Arrange
    input_data = {"value": 100}
    expected = {"value": 110}
    
    # Act
    result = transform_data(input_data, increase_by=10)
    
    # Assert
    assert result == expected
```

### 2. Test Coverage
- Unit tests for individual functions
- Integration tests for workflows
- Edge case testing
- Error condition testing
- Performance testing for large datasets

### 3. Test Data Management
```python
# Good: Use fixtures
@pytest.fixture
def sample_data():
    return pd.DataFrame({
        'id': [1, 2, 3],
        'value': [100, 200, 300]
    })

def test_aggregation(sample_data):
    result = aggregate_data(sample_data)
    assert result['total'] == 600
```

### 4. Mocking External Dependencies
```python
# Good: Mock external services
@patch('requests.get')
def test_api_integration(mock_get):
    mock_get.return_value.json.return_value = {"status": "success"}
    result = fetch_api_data()
    assert result["status"] == "success"
```

## Security Best Practices

### 1. Credential Management
```python
# Good: Use environment variables
api_key = os.environ.get('API_KEY')
if not api_key:
    raise ValueError("API_KEY environment variable not set")

# Bad: Hardcode credentials
api_key = "sk-1234567890abcdef"  # NEVER DO THIS
```

### 2. Input Validation
```python
# Good: Validate inputs
def process_user_input(data):
    if not isinstance(data, dict):
        raise ValueError("Input must be a dictionary")
    
    required_fields = ['id', 'value']
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing required field: {field}")
    
    # Process validated data
```

### 3. Safe File Operations
```python
# Good: Validate file paths
import os

def read_file(file_path):
    # Prevent directory traversal
    safe_path = os.path.abspath(file_path)
    allowed_dir = os.path.abspath('./data')
    
    if not safe_path.startswith(allowed_dir):
        raise ValueError("Access denied: File outside allowed directory")
    
    with open(safe_path) as f:
        return f.read()
```

### 4. Logging Sensitive Data
```python
# Good: Sanitize logs
def log_api_call(url, headers):
    safe_headers = headers.copy()
    if 'Authorization' in safe_headers:
        safe_headers['Authorization'] = '***'
    
    logger.info(f"API call to {url} with headers: {safe_headers}")

# Bad: Log everything
logger.info(f"API call with headers: {headers}")  # Might expose tokens
```

## Success Tips

1. **Start Small**: Begin with a simple 2-3 node workflow
2. **Copy Examples**: Use templates and modify rather than writing from scratch
3. **Test Frequently**: Run your workflow after each major change
4. **Use Debug Mode**: Enable debug logging to see what's happening
5. **Check References**: When in doubt, check the API registry
6. **Follow Patterns**: Stick to the established patterns that work

## Important Reminders

- **Reuse shared components** - don't reinvent the wheel
- **Follow established patterns** - use templates and shared workflows
- **Test with realistic data** - don't just test with perfect inputs
- **Document assumptions** - make requirements explicit
- **Plan for maintenance** - solutions need ongoing support

Remember: The goal is to create working solutions quickly and reliably using the Kailash SDK. When in doubt, copy from working examples and modify incrementally!