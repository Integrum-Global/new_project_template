# Validation Tools - Solution Development

**Version**: Template-adapted from Kailash SDK 0.1.4  
**Focus**: Validation and deployment checks for business solutions

## 📁 Validation Files

| File | Purpose | Description |
|------|---------|-------------|
| [solution-validation-guide.md](solution-validation-guide.md) | Development Rules | Critical rules for solution development |
| [deployment-checklist.md](deployment-checklist.md) | Production Readiness | Pre-deployment validation checklist |
| [api-validation-schema.json](api-validation-schema.json) | API Schema | Machine-readable API validation |
| [validation_report.md](validation_report.md) | Documentation Report | Documentation quality validation |

## 🎯 Solution Development Validation

### Quick Validation Checklist

**Before Development:**
- [ ] Check [solution-validation-guide.md](solution-validation-guide.md) for critical rules
- [ ] Review API patterns in [api-validation-schema.json](api-validation-schema.json)
- [ ] Understand node naming conventions and parameter patterns

**During Development:**
- [ ] Follow snake_case naming for all methods and parameters
- [ ] Use Node suffix for all custom node classes
- [ ] Validate workflow connections and parameter mappings
- [ ] Test with realistic data volumes

**Before Deployment:**
- [ ] Complete [deployment-checklist.md](deployment-checklist.md)
- [ ] Validate environment variable configuration
- [ ] Test error handling and edge cases
- [ ] Verify security configuration

## 🚀 Quick Start Validation

### 1. **API Usage Validation**
```bash
# Validate your solution code against API patterns
python -c "
import yaml
with open('reference/validation/api-validation-schema.json') as f:
    schema = yaml.safe_load(f)
    print('Core workflow APIs:', list(schema.keys())[:5])
"
```

### 2. **Solution Structure Validation**
```python
# Validate solution follows best practices
from pathlib import Path

def validate_solution_structure(solution_path):
    required_files = [
        'workflow.py',
        'config.py', 
        '__init__.py',
        'README.md'
    ]
    
    missing = []
    for file in required_files:
        if not (Path(solution_path) / file).exists():
            missing.append(file)
    
    if missing:
        print(f"Missing required files: {missing}")
        return False
    
    print("Solution structure validation passed")
    return True
```

### 3. **Environment Configuration Validation**
```python
# Validate environment setup
import os
from typing import List

def validate_environment(required_vars: List[str]) -> bool:
    missing = []
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)
    
    if missing:
        print(f"Missing environment variables: {missing}")
        print("See reference/cheatsheet/016-environment-variables.md")
        return False
    
    print("Environment validation passed")
    return True

# Common solution environment variables
solution_env_vars = [
    "DATABASE_URL",
    "API_TOKEN", 
    "LOG_LEVEL",
    "KAILASH_ENV"
]

validate_environment(solution_env_vars)
```

## 📋 Common Validation Errors

### ❌ Naming Convention Errors
```python
# Wrong
class DataProcessor:  # Missing 'Node' suffix
    pass

def processData():  # camelCase instead of snake_case
    pass

# Correct
class DataProcessorNode:  # Proper Node suffix
    pass

def process_data():  # snake_case
    pass
```

### ❌ Configuration Errors
```python
# Wrong - hardcoded values
workflow_config = {
    "api_key": "sk-1234567890",  # Security risk
    "database_url": "postgresql://localhost/mydb"  # Environment-specific
}

# Correct - environment variables
workflow_config = {
    "api_key": "${API_KEY}",  # From environment
    "database_url": "${DATABASE_URL}"  # From environment
}
```

### ❌ Connection Mapping Errors
```python
# Wrong - incorrect parameter mapping
workflow.connect(
    source_node, 
    target_node, 
    mapping={"output": "output"}  # Same name, likely wrong
)

# Correct - meaningful parameter mapping
workflow.connect(
    csv_reader, 
    data_processor, 
    mapping={"data": "raw_input"}  # Clear source -> target mapping
)
```

## 🔧 Automated Validation Scripts

### Solution Validation Script
```python
#!/usr/bin/env python3
"""Validate Kailash solution before deployment"""

import ast
import sys
from pathlib import Path

def validate_python_file(file_path: Path) -> List[str]:
    """Validate Python file for common issues"""
    issues = []
    
    try:
        with open(file_path) as f:
            tree = ast.parse(f.read())
        
        # Check for Node suffix in class names
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if 'Node' in node.name and not node.name.endswith('Node'):
                    issues.append(f"Class {node.name} should end with 'Node'")
        
        # Check for snake_case in function names
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if '_' not in node.name and node.name != '__init__':
                    if any(c.isupper() for c in node.name):
                        issues.append(f"Function {node.name} should use snake_case")
        
    except SyntaxError as e:
        issues.append(f"Syntax error: {e}")
    
    return issues

def main():
    """Run validation on solution directory"""
    solution_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
    
    all_issues = []
    for py_file in solution_dir.rglob('*.py'):
        issues = validate_python_file(py_file)
        if issues:
            all_issues.extend([f"{py_file}: {issue}" for issue in issues])
    
    if all_issues:
        print("Validation Issues Found:")
        for issue in all_issues:
            print(f"  ❌ {issue}")
        sys.exit(1)
    else:
        print("✅ All validation checks passed")

if __name__ == "__main__":
    main()
```

## 🔗 Related Resources

- **[Cheatsheet](../cheatsheet/)** - Quick reference for correct patterns
- **[API Reference](../api/)** - Exact API specifications
- **[Node Catalog](../nodes/)** - Proper node usage patterns
- **[Templates](../templates/)** - Validated code examples

---
*For comprehensive SDK development validation, see the main Kailash SDK repository*