# Solutions Repository Structure

## Overview

This document defines the complete structure and organization of the Kailash SDK Solutions repository. All solutions MUST follow this structure to ensure consistency, maintainability, and reusability across the project.

## Complete Repository Structure

```
solutions_repo/
├── CLAUDE.md                    # Claude Code instructions & quick reference
├── README.md                    # Repository overview & getting started
├── CHANGELOG.md                 # Version history and changes
├── MANIFEST.in                  # Package manifest for distribution
├── pyproject.toml              # Modern Python packaging configuration
├── uv.lock                     # Dependency lock file (uv package manager)
├── setup.py                    # Legacy package setup (if needed)
├── .gitignore                  # Git ignore patterns
├── .env.example                # Example environment variables
│
├── src/                        # SOURCE CODE - All Python packages
│   ├── __init__.py            # Main package initialization
│   │
│   ├── shared/                 # Shared components package
│   │   ├── __init__.py        # Package initialization
│   │   ├── nodes/             # Custom shared nodes
│   │   │   ├── __init__.py
│   │   │   ├── data_processors.py  # Data processing nodes
│   │   │   ├── ai_analyzers.py    # AI/LLM analysis nodes
│   │   │   ├── api_connectors.py  # API integration nodes
│   │   │   └── validators.py      # Data validation nodes
│   │   ├── workflows/         # Reusable workflow components
│   │   │   ├── __init__.py
│   │   │   ├── etl_patterns.py    # Extract-Transform-Load patterns
│   │   │   ├── api_patterns.py    # API integration patterns
│   │   │   └── ai_patterns.py     # AI analysis patterns
│   │   ├── utils/             # Shared utilities
│   │   │   ├── __init__.py
│   │   │   ├── config.py      # Configuration management
│   │   │   ├── logging.py     # Logging setup
│   │   │   └── validation.py  # Input validation
│   │   └── tests/             # Tests for shared components
│   │       ├── __init__.py
│   │       ├── test_nodes.py
│   │       ├── test_workflows.py
│   │       └── test_utils.py
│   │
│   └── solutions/              # Individual solution packages
│       ├── __init__.py
│       └── {solution_name}/    # Each solution follows this structure
│           ├── __init__.py    # Package exports
│           ├── __main__.py    # Entry point (python -m solutions.{name})
│           ├── config.py      # Configuration handling
│           ├── workflows/     # Main workflow logic
│           │   ├── __init__.py
│           │   └── workflow.py
│           ├── nodes/         # Custom nodes (if needed)
│           │   └── __init__.py
│           ├── examples/      # Solution examples
│           │   └── __init__.py
│           ├── README.md      # Solution-specific documentation
│           ├── config.yaml    # Default configuration file
│           └── tests/         # Solution-specific tests
│               ├── __init__.py
│               ├── test_workflow.py
│               ├── test_config.py
│               └── test_integration.py
│
├── data/                       # Data files (not in src/)
│   ├── samples/               # Sample data for testing
│   │   └── example_data.csv
│   ├── configs/              # Configuration files
│   │   └── default_config.yaml
│   └── outputs/              # Output directory (gitignored)
│
├── docs/                       # Documentation (Sphinx)
│   ├── conf.py               # Sphinx configuration
│   ├── index.rst             # Documentation index
│   ├── api/                  # API documentation
│   │   ├── index.rst
│   │   └── modules.rst
│   ├── guides/               # User guides (deprecated - use guide/instructions)
│   ├── examples/             # Example documentation
│   └── build_docs.py         # Documentation build script
│
├── examples/                   # Working examples (if applicable)
│   ├── _utils/               # Example utilities
│   │   └── test_all_examples.py
│   └── {category}_examples/  # Categorized examples
│
├── scripts/                    # Utility scripts
│   ├── deploy.py             # Deployment automation
│   ├── validate.py           # Code validation script
│   └── setup_env.py          # Environment setup helper
│
├── reference/                  # API references (from Kailash SDK)
│   ├── README.md             # Reference documentation overview
│   ├── api-registry.yaml     # EXACT API specifications
│   ├── api-validation-schema.json  # API validation schema
│   ├── validation-guide.md   # Error prevention rules
│   ├── validation_report.md  # Validation results
│   ├── corrections-summary.md # Common corrections
│   ├── cheatsheet.md        # Common patterns and examples
│   └── validate_kailash_code.py # Code validation tool
│
├── guide/                      # Solution development guides
│   ├── adr/                   # Architecture Decision Records
│   │   └── README.md         # ADR overview and index
│   ├── mistakes/             # Mistakes and lessons learned
│   │   └── 000-master.md     # Consolidated mistakes log
│   ├── prd/                  # Product Requirements Documents
│   │   └── 000-project_structure.md  # This file
│   └── instructions/         # Development instructions
│       ├── solution-development.md   # Detailed workflows
│       ├── solution-templates.md     # Code templates
│       ├── checklists.md            # Quick checklists
│       └── best-practices.md        # Best practices
│
├── todos/                      # Task tracking
│   ├── 000-master.md         # Active priorities and tasks
│   └── completed-archive.md  # Completed tasks archive
│
└── tests/                      # Global test suite (if needed)
    ├── __init__.py
    ├── conftest.py           # Pytest configuration
    └── test_integration.py   # Cross-solution tests
```

## Solution Package Structure (Detailed)

Each solution MUST follow this exact structure:

```
src/solutions/{solution_name}/
├── __init__.py                 # Package initialization and exports
├── __main__.py                 # CLI entry point
├── config.py                   # Configuration management
├── workflows/                  # Main workflow logic
│   ├── __init__.py
│   └── workflow.py            # Main workflow implementation
├── nodes/                     # Custom nodes (if needed)
│   ├── __init__.py
│   ├── processors.py          # Custom data processors (optional)
│   ├── connectors.py          # External system connectors (optional)
│   └── validators.py          # Custom validation nodes (optional)
├── examples/                  # Working examples for this solution
│   ├── __init__.py
│   ├── basic_usage.py        # Simple example
│   ├── advanced_usage.py     # Complex example with all features
│   ├── integration_example.py # Integration with other systems
│   └── sample_data/          # Sample data for examples
│       └── input_data.csv
├── tests/                     # Comprehensive test suite
│   ├── __init__.py
│   ├── test_workflow.py       # Workflow logic tests
│   ├── test_config.py         # Configuration tests
│   ├── test_nodes.py          # Node tests (if applicable)
│   ├── test_integration.py    # End-to-end tests
│   └── fixtures/              # Test data and fixtures
│       └── sample_data.json
├── utils.py                   # Solution-specific utilities (optional)
├── README.md                  # Solution documentation
├── config.yaml                # Default configuration values
├── requirements.txt           # Solution-specific dependencies (optional)
└── docs/                      # Implementation documentation (REQUIRED)
    ├── implementation.md      # REQUIRED: Implementation details, considerations, steps
    ├── architecture.md        # Solution architecture (optional)
    └── troubleshooting.md     # Common issues and solutions (optional)
```

## File Purposes and Requirements

### Core Solution Files

**`__init__.py`** - Package initialization
- MUST export main functions/classes
- MUST include `__all__` definition
- SHOULD have package docstring

**`__main__.py`** - Entry point
- MUST enable `python -m solutions.{name}` execution
- MUST handle command-line arguments
- MUST provide help text
- MUST handle errors gracefully

**`workflows/workflow.py`** - Main logic
- MUST contain workflow creation function
- MUST follow Kailash SDK patterns
- MUST use proper node naming (ending with "Node")
- MUST validate inputs

**`config.py`** - Configuration
- MUST support file and environment configs
- MUST validate configuration
- MUST provide defaults
- MUST handle missing values gracefully

**`README.md`** - Documentation
- MUST include purpose and overview
- MUST document all configuration options
- MUST provide usage examples
- MUST list dependencies
- MUST include troubleshooting

**`docs/implementation.md`** - Implementation Documentation (REQUIRED)
- MUST document business requirements and context
- MUST explain design decisions and rationale
- MUST detail implementation steps taken
- MUST document key considerations and trade-offs
- MUST include data flow and processing logic
- MUST note performance characteristics and limitations

### Shared Components Structure

**`shared/nodes/`** - Reusable nodes
- Each file groups related node types
- All classes MUST end with "Node"
- MUST inherit from appropriate base class
- MUST implement required methods

**`shared/workflows/`** - Reusable patterns
- Each file contains related workflow patterns
- MUST be configurable
- MUST be well-documented
- MUST include usage examples

**`shared/utils/`** - Common utilities
- Configuration helpers
- Logging setup
- Validation functions
- Data transformation helpers

## Naming Conventions

### Python Files and Modules
- Use `snake_case` for all files and modules
- Be descriptive but concise
- Group related functionality

### Classes
- Node classes MUST end with "Node": `DataValidatorNode`
- Use `PascalCase` for all classes
- Be specific about functionality

### Functions and Methods
- Use `snake_case` for all functions
- Start with verb: `load_config()`, `validate_data()`
- Be clear about return values

### Configuration Keys
- Use `snake_case` with underscores
- NO camelCase or kebab-case
- Examples: `api_key`, `max_retries`, `output_format`

## Import Organization

Standard import order:
```python
# Standard library imports
import os
import sys
from pathlib import Path

# Third-party imports
import pandas as pd
import requests

# Kailash SDK imports
from kailash.workflow.graph import Workflow
from kailash.runtime.local import LocalRuntime
from kailash.nodes.data import CSVReaderNode

# Local application imports
from ..shared.nodes import CustomProcessorNode
from .config import load_config
from .workflows.workflow import create_workflow
from .nodes.processors import CustomDataNode
```

## Testing Structure

### Unit Tests
- One test file per module
- Test individual functions/methods
- Mock external dependencies
- Fast execution

### Integration Tests
- Test complete workflows
- Use real data samples
- Verify end-to-end functionality
- Test error scenarios

### Test Naming
- Test files: `test_{module}.py`
- Test functions: `test_{function}_{scenario}()`
- Be descriptive about what's tested

## Documentation Requirements

### Code Documentation
- All modules MUST have docstrings
- All public functions MUST have docstrings
- Use Google-style docstring format
- Include type hints

### Solution Documentation
- README.md is mandatory
- Include architecture diagrams if complex
- Document all assumptions
- Provide troubleshooting guide

### API Documentation
- Auto-generated from docstrings
- Kept up-to-date with code
- Include usage examples
- Document error conditions

## Version Control Guidelines

### Branch Naming
- `feature/solution-{name}` - New solutions
- `fix/solution-{name}-{issue}` - Bug fixes
- `refactor/shared-{component}` - Refactoring
- `docs/{topic}` - Documentation updates

### Commit Messages
- Be descriptive and specific
- Reference issue numbers
- Follow conventional commits if adopted
- Example: "feat(solutions): add customer analytics workflow"

## Security Considerations

### Credentials
- NEVER hardcode credentials
- Use environment variables
- Document required permissions
- Implement proper error handling

### Data Privacy
- Follow data protection regulations
- Implement data anonymization if needed
- Document data retention policies
- Secure sensitive outputs

## Performance Guidelines

### Resource Management
- Close file handles properly
- Manage memory for large datasets
- Implement streaming where appropriate
- Monitor resource usage

### Optimization
- Profile before optimizing
- Document performance characteristics
- Set realistic expectations
- Implement progress indicators

## Deployment Considerations

### Dependencies
- Minimize external dependencies
- Pin version numbers
- Test with exact versions
- Document system requirements

### Configuration
- Support multiple environments
- Validate all settings on startup
- Provide clear error messages
- Support configuration overrides

## Maintenance Requirements

### Regular Updates
- Keep dependencies current
- Update documentation
- Review and refactor regularly
- Archive obsolete solutions

### Monitoring
- Implement logging appropriately
- Track execution metrics
- Monitor error rates
- Document known issues

This structure ensures consistency, maintainability, and scalability across all solutions in the repository.