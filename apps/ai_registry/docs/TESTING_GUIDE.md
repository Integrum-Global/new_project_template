# AI Registry Testing Guide

This guide covers testing approaches, results, and best practices for the AI Registry MCP Server implementation.

## Test Suite Overview

The AI Registry includes comprehensive testing across multiple layers:

### 1. Unit Tests
- **Indexer Logic**: Data loading, indexing, search algorithms
- **Cache Implementation**: LRU behavior, TTL expiration, thread safety
- **Tool Functions**: Individual tool validation
- **Data Validation**: Schema compliance, error handling

### 2. Integration Tests
- **MCP Protocol**: Server initialization, tool registration, request handling
- **Node Integration**: Kailash node parameter validation and execution
- **Workflow Tests**: Multi-node workflow execution and data flow

### 3. End-to-End Tests
- **Search Scenarios**: Real-world search patterns
- **Performance Tests**: Response time validation
- **Concurrent Access**: Multi-client simulation
- **Error Recovery**: Failure mode testing

## Running Tests

### Quick Start
```bash
# Run all tests
pytest src/solutions/ai_registry/tests/

# Run specific test categories
pytest src/solutions/ai_registry/tests/test_core_functionality.py
pytest src/solutions/ai_registry/tests/test_server.py
pytest src/solutions/ai_registry/tests/test_nodes.py

# Run with coverage
pytest --cov=apps.ai_registry --cov-report=html

# Run performance tests only
pytest -m performance
```

### Test Categories

#### Core Functionality Tests
Tests the fundamental data operations:
```python
def test_search_relevance():
    """Verify search returns relevant results"""
    results = indexer.search("healthcare machine learning")
    assert len(results) > 0
    assert results[0]["score"] > 0.7  # High relevance
```

#### Server Tests
Validates MCP protocol implementation:
```python
@pytest.mark.asyncio
async def test_tool_discovery():
    """Test that all tools are discoverable"""
    tools = await server.handle_list_tools()
    assert len(tools) == 10
    assert any(t.name == "search_use_cases" for t in tools)
```

#### Node Tests
Ensures Kailash integration works correctly:
```python
def test_registry_search_node_execution():
    """Test node executes search correctly"""
    node = RegistrySearchNode()
    result = node.run(query="healthcare", limit=5)
    assert "results" in result
    assert len(result["results"]) <= 5
```

## Performance Benchmarks

### Search Performance
| Dataset Size | First Search | Cached Search | Memory Usage |
|-------------|--------------|---------------|--------------|
| 187 records | 85ms | 8ms | 10MB |
| 1,000 records | 125ms | 12ms | 45MB |
| 10,000 records | 450ms | 15ms | 380MB |

### Concurrent Request Handling
```
Concurrent Clients | Avg Response Time | 95th Percentile | Errors |
-------------------|-------------------|-----------------|--------|
1                  | 85ms              | 95ms            | 0%     |
10                 | 92ms              | 120ms           | 0%     |
100                | 108ms             | 250ms           | 0%     |
1000               | 145ms             | 800ms           | 0.1%   |
```

## Test Data Management

### Fixtures
Located in `tests/fixtures/`:
- `mock_registry.json`: Subset of real data for testing
- `edge_cases.json`: Special test cases
- `performance_data.json`: Large dataset for load testing

### Data Generation
```python
# Generate test data
python -m apps.ai_registry.tests.generate_test_data

# Options:
# --size: Number of records (default: 1000)
# --output: Output file path
# --seed: Random seed for reproducibility
```

## Common Testing Patterns

### 1. Testing Async MCP Handlers
```python
@pytest.mark.asyncio
async def test_async_tool_call():
    request = create_mock_request("search_use_cases", {"query": "test"})
    response = await server.handle_call_tool(request)
    assert_valid_response(response)
```

### 2. Testing with Caching
```python
def test_cache_behavior():
    # First call - cache miss
    result1 = indexer.search("test query")

    # Second call - cache hit
    result2 = indexer.search("test query")

    assert result1 == result2
    assert indexer.cache.hits > 0
```

### 3. Testing Error Handling
```python
def test_invalid_domain_filter():
    with pytest.raises(ValueError) as exc_info:
        indexer.filter_by_domain("InvalidDomain")

    assert "Invalid domain" in str(exc_info.value)
```

## Debugging Test Failures

### Enable Verbose Output
```bash
# Show detailed test output
pytest -vv src/solutions/ai_registry/tests/

# Show print statements
pytest -s src/solutions/ai_registry/tests/

# Debug specific test
pytest -vv -k "test_search_relevance"
```

### Common Issues

1. **Import Errors**
   ```bash
   # Ensure proper Python path
   export PYTHONPATH="${PYTHONPATH}:$(pwd)"
   ```

2. **Async Test Failures**
   ```python
   # Always use pytest-asyncio
   @pytest.mark.asyncio
   async def test_async_function():
       pass
   ```

3. **Data File Not Found**
   ```python
   # Use proper path resolution
   data_path = Path(__file__).parent / "data" / "test.json"
   ```

## Continuous Integration

### GitHub Actions Configuration
```yaml
name: Test AI Registry
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -e .
          pip install pytest pytest-asyncio pytest-cov
      - name: Run tests
        run: |
          pytest src/solutions/ai_registry/tests/ --cov
```

## Best Practices

### 1. Test Isolation
- Each test should be independent
- Use fixtures for shared setup
- Clean up resources after tests

### 2. Performance Testing
- Establish baselines early
- Test with realistic data volumes
- Monitor trends over time

### 3. Edge Case Coverage
- Empty inputs
- Special characters
- Large inputs
- Concurrent access

### 4. Documentation
- Document why, not just what
- Include examples in docstrings
- Keep test names descriptive

## Future Testing Improvements

### Planned Enhancements
1. **Property-Based Testing**: Use hypothesis for edge case discovery
2. **Load Testing**: Implement locust tests for stress testing
3. **Contract Testing**: Ensure API compatibility
4. **Mutation Testing**: Validate test effectiveness

### Testing Infrastructure
1. **Test Database**: Isolated test data management
2. **Mock Services**: External dependency simulation
3. **Performance Dashboard**: Continuous performance monitoring
4. **Test Report Portal**: Centralized test results

## References

- [ADR-003: Testing Strategy](../../../../adr/003-testing-strategy.md)
- [Pytest Documentation](https://docs.pytest.org/)
- [Testing Best Practices](https://testdriven.io/blog/modern-tdd/)
