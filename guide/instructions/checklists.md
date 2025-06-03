# Development Checklists

Quick reference checklists for common development tasks with the Kailash SDK.

## Common Task Checklists

### □ Creating a New Solution
- [ ] Check `todos/000-master.md` for priorities
- [ ] Review existing solutions for reusable components
- [ ] Choose appropriate template from `templates/`
- [ ] Create solution directory structure
- [ ] Implement using shared components where possible
- [ ] Create configuration file (config.yaml)
- [ ] Write tests for solution logic
- [ ] Document solution in README.md
- [ ] Update todos with completion status

### □ Creating a Shared Node
- [ ] Name ends with "Node" (e.g., `DataCleanerNode`)
- [ ] Inherits from `Node` or `AsyncNode`
- [ ] Has `get_parameters()` and `run()` methods (required)
- [ ] Has `get_output_schema()` method (optional)
- [ ] Add to appropriate category in `shared/nodes/`
- [ ] Write unit tests in `tests/test_shared_nodes.py`
- [ ] Document usage in node docstring
- [ ] Update `shared/nodes/__init__.py` imports

### □ Creating a Shared Workflow
- [ ] Follow established workflow patterns
- [ ] Make configurable via parameters
- [ ] Use shared nodes where applicable
- [ ] Add to `shared/workflows/`
- [ ] Write integration tests
- [ ] Document usage and parameters
- [ ] Update `shared/workflows/__init__.py` imports

### □ Solution Quality Check
- [ ] Uses shared components where applicable
- [ ] Has proper configuration management
- [ ] Includes error handling
- [ ] Has comprehensive tests
- [ ] Documented usage instructions
- [ ] Follows naming conventions
- [ ] Validates input/output data
- [ ] Handles edge cases gracefully

## Error Prevention Checklist

Before running your solution, verify:
- [ ] All node class names end with "Node"
- [ ] All method names use snake_case
- [ ] Configuration passed as kwargs, NOT as dict
- [ ] Connections use mapping={"output": "input"}
- [ ] Execution uses runtime.execute(workflow) - NEVER workflow.execute(runtime)
- [ ] Import paths are complete and correct
- [ ] Required parameters are provided
- [ ] File paths exist and are accessible

⚠️ **CRITICAL**: The pattern `workflow.execute(runtime)` does NOT exist in Kailash SDK.
Always use `runtime.execute(workflow)` for workflow execution.

## Pre-Deployment Checklist

### □ Code Quality
- [ ] Code passes validation (`python reference/validate_kailash_code.py`)
- [ ] All tests pass (`pytest`)
- [ ] No hardcoded credentials or secrets
- [ ] Error handling implemented
- [ ] Logging configured appropriately

### □ Configuration
- [ ] All configurable values externalized
- [ ] Environment variables documented
- [ ] Default values are sensible
- [ ] Config validation implemented
- [ ] Example config file provided

### □ Documentation
- [ ] README.md updated with usage instructions
- [ ] Configuration options documented
- [ ] API dependencies listed
- [ ] Performance characteristics noted
- [ ] Troubleshooting section included

### □ Testing
- [ ] Unit tests written for core logic
- [ ] Integration tests for workflow
- [ ] Edge cases tested
- [ ] Performance tested with expected data volumes
- [ ] Error scenarios tested

### □ Dependencies
- [ ] requirements.txt or pyproject.toml updated
- [ ] Version constraints specified
- [ ] License compatibility checked
- [ ] Security vulnerabilities scanned

## Debugging Checklist

When something goes wrong:
- [ ] Enable debug mode: `LocalRuntime(debug=True)`
- [ ] Check node configurations match API registry
- [ ] Verify file paths are absolute, not relative
- [ ] Confirm all required parameters provided
- [ ] Check data types match expected inputs
- [ ] Review error messages for specific issues
- [ ] Validate workflow before execution
- [ ] Test nodes individually before combining

## Performance Optimization Checklist

### □ Data Processing
- [ ] Filter data early in the pipeline
- [ ] Use appropriate batch sizes
- [ ] Minimize data transformations
- [ ] Cache frequently accessed data
- [ ] Use streaming for large files

### □ API Integration
- [ ] Implement rate limiting
- [ ] Use connection pooling
- [ ] Handle retries with backoff
- [ ] Batch API requests when possible
- [ ] Cache API responses appropriately

### □ Memory Management
- [ ] Process data in chunks
- [ ] Clean up temporary files
- [ ] Release resources after use
- [ ] Monitor memory usage
- [ ] Set appropriate limits

## Quick Reference Commands

```bash
# Validate code
python reference/validate_kailash_code.py src/solutions/my_solution/workflow.py

# Run tests
pytest src/solutions/my_solution/tests/ -v

# Check syntax
python -m py_compile src/solutions/my_solution/*.py

# Install dependencies
pip install -r requirements.txt

# Run solution
python -m solutions.my_solution
```