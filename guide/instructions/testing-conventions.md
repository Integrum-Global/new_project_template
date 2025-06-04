# Testing Conventions

## Test Directory Structure

### ✅ **Recommended: Module-level Tests**
```
src/
├── solutions/
│   └── my_solution/
│       ├── workflow.py
│       ├── config.py
│       └── tests/          # Tests for this solution
│           ├── __init__.py
│           ├── conftest.py
│           └── test_workflow.py

scripts/
├── sync_template.py
├── validate.py
└── tests/                  # Tests for scripts module
    ├── __init__.py
    ├── conftest.py
    ├── test_template_setup.py
    └── test_validation.py

src/shared/
├── nodes/
├── utils/
└── tests/                  # Tests for shared components
    ├── __init__.py
    ├── conftest.py
    ├── test_nodes.py
    └── test_utils.py
```

### ❌ **Avoid: Root-level Tests Directory**
```
tests/                      # DON'T DO THIS
├── test_everything.py      # Hard to maintain
└── conftest.py            # Too broad scope
```

## Testing Guidelines

### 1. **Test Placement**
- Place tests **next to the code they test**
- Use module-specific `tests/` directories
- Keep test scope focused and narrow

### 2. **Test Naming**
- Test files: `test_*.py`
- Test functions: `test_*`
- Test classes: `Test*`

### 3. **Documentation Tests**
- `docs/` directory is reserved for **Sphinx documentation**
- Don't put reference docs in `docs/`
- Use `reference/` for API references and guides

### 4. **Fixtures and Configuration**
- Each module has its own `conftest.py`
- Share common fixtures via imports
- Keep fixture scope minimal

### 5. **Test Categories**

#### **Unit Tests**
```python
# In src/solutions/my_solution/tests/test_workflow.py
def test_workflow_creation():
    """Test basic workflow creation."""
    pass
```

#### **Integration Tests**
```python
# In scripts/tests/test_template_setup.py
def test_project_structure():
    """Test overall project structure."""
    pass
```

#### **End-to-End Tests**
```python
# In examples/_utils/test_all_examples.py
def test_examples_execute():
    """Test that all examples run successfully."""
    pass
```

## Running Tests

### **Module-specific Tests**
```bash
# Test specific solution
pytest src/solutions/my_solution/tests/

# Test scripts
pytest scripts/tests/

# Test shared components
pytest src/shared/tests/
```

### **All Tests**
```bash
# Run all tests in project
pytest

# With coverage
pytest --cov=src --cov=scripts
```

### **CI/CD Tests**
```bash
# Basic smoke tests (used in CI)
pytest scripts/tests/test_template_setup.py -v
```

## Benefits of This Structure

### ✅ **Advantages**
- **Focused scope**: Tests close to code they test
- **Easy maintenance**: Clear ownership of tests
- **Faster execution**: Run only relevant tests
- **Better organization**: Logical grouping
- **Parallel development**: Teams can work independently

### 🚫 **Avoid Root Tests Because**
- **Broad scope**: Hard to determine what's being tested
- **Maintenance burden**: Single point of failure
- **Slow execution**: Must run all tests together
- **Merge conflicts**: Everyone modifying same directory
- **Unclear ownership**: Who maintains which tests?

## Examples

### **Good: Solution Tests**
```
src/solutions/data_pipeline/
├── __init__.py
├── workflow.py
├── config.py
├── README.md
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── test_workflow.py
    └── test_config.py
```

### **Good: Shared Component Tests**
```
src/shared/nodes/
├── __init__.py
├── csv_reader.py
├── data_transformer.py
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── test_csv_reader.py
    └── test_data_transformer.py
```

This structure ensures tests are maintainable, focused, and follow Python best practices.