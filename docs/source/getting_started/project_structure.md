# Project Structure

Understanding the project structure is key to effectively using the Kailash SDK Template.

## Directory Overview

```
new_project_template/
├── .github/                    # GitHub Actions workflows and configuration
│   ├── workflows/             # CI/CD workflows
│   └── CODEOWNERS            # Code ownership rules
├── data/                      # Data directory
│   ├── configs/              # Configuration files
│   ├── outputs/              # Output files (gitignored)
│   └── samples/              # Sample data files
├── docs/                      # Documentation
│   ├── source/               # Sphinx documentation source
│   └── build/                # Built documentation (gitignored)
├── guide/                     # Development guides
│   ├── adr/                  # Architecture Decision Records
│   ├── instructions/         # Detailed instructions
│   ├── mistakes/             # Common mistakes and solutions
│   └── prd/                  # Product Requirements Documents
├── migrations/                # Migration system
│   ├── to_migrate/           # Projects to migrate
│   ├── in_progress/          # Active migrations
│   ├── completed/            # Completed migrations
│   └── templates/            # Migration document templates
├── reference/                 # API and pattern references
│   ├── api-registry.yaml     # Kailash SDK API reference
│   ├── cheatsheet.md         # Quick reference guide
│   └── templates/            # Code templates
├── scripts/                   # Utility scripts
│   ├── setup_env.py          # Environment setup
│   ├── validate.py           # Code validation
│   ├── deploy.py             # Deployment script
│   └── sync_template.py      # Template synchronization
├── src/                       # Source code
│   ├── shared/               # Shared components
│   │   ├── nodes/           # Reusable nodes
│   │   ├── utils/           # Utility functions
│   │   └── workflows/       # Workflow patterns
│   └── solutions/            # Solution implementations
│       └── [solution_name]/  # Individual solutions
├── templates/                 # Solution templates
│   ├── basic_etl/           # ETL workflow template
│   ├── api_integration/     # API integration template
│   └── ai_analysis/         # AI analysis template
├── todos/                     # Task management
│   ├── 000-master.md        # Active todo list
│   └── completed-archive.md  # Completed tasks
├── .env.example              # Environment variables example
├── .gitignore                # Git ignore rules
├── .pre-commit-config.yaml   # Pre-commit hooks configuration
├── Claude.md                 # Claude Code instructions
├── MANIFEST.in               # Package manifest
├── pyproject.toml            # Project configuration
└── README.md                 # Project readme
```

## Key Directories Explained

### `/src/solutions/`

This is where you create your solution implementations:

```
src/solutions/my_solution/
├── __init__.py              # Package initialization
├── __main__.py              # Entry point (python -m src.solutions.my_solution)
├── workflow.py              # Main workflow definition
├── config.py                # Configuration management
├── config.yaml              # Default configuration
├── nodes/                   # Solution-specific nodes
├── utils/                   # Solution-specific utilities
├── examples/                # Usage examples
│   ├── basic_usage.py
│   └── advanced_usage.py
├── tests/                   # Solution tests
│   ├── __init__.py
│   ├── test_workflow.py
│   └── test_nodes.py
└── README.md                # Solution documentation
```

### `/src/shared/`

Reusable components shared across solutions:

- **`nodes/`**: Custom nodes that can be used by any solution
- **`utils/`**: Utility functions (logging, validation, config)
- **`workflows/`**: Common workflow patterns

### `/reference/`

Critical reference documentation:

- **`api-registry.yaml`**: Complete Kailash SDK API reference
- **`cheatsheet.md`**: Quick lookup for common patterns
- **`validation-guide.md`**: Code validation rules

### `/guide/`

Development guides and documentation:

- **`instructions/`**: Step-by-step guides
- **`adr/`**: Architecture decisions
- **`mistakes/`**: Common pitfalls and solutions

## File Naming Conventions

- **Python files**: `snake_case.py`
- **Markdown files**: `kebab-case.md` or `snake_case.md`
- **YAML files**: `kebab-case.yaml` or `snake_case.yaml`
- **Directories**: `snake_case/`

## Import Structure

### Absolute Imports

Always use absolute imports from the project root:

```python
# Good
from src.shared.nodes import CustomNode
from src.shared.utils import logger
from src.solutions.my_solution.workflow import MyWorkflow

# Avoid
from ..shared.nodes import CustomNode  # Relative import
```

### Package Structure

Each solution is a package that can be run as a module:

```bash
# Run a solution
python -m src.solutions.my_solution

# Run with arguments
python -m src.solutions.my_solution --config custom_config.yaml
```

## Configuration Management

### Environment Variables

Use `.env` files for environment-specific settings:

```python
# src/shared/utils/config.py
from dotenv import load_dotenv
import os

load_dotenv()

API_KEY = os.getenv("API_KEY")
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
```

### Solution Configuration

Each solution can have its own `config.yaml`:

```yaml
# src/solutions/my_solution/config.yaml
workflow:
  name: "data_processing"
  description: "Process daily data files"
  
parameters:
  input_path: "data/input/"
  output_path: "data/output/"
  batch_size: 1000
  
nodes:
  reader:
    file_pattern: "*.csv"
    encoding: "utf-8"
```

## Best Practices

1. **Keep solutions isolated**: Each solution should be self-contained
2. **Share common code**: Put reusable components in `/src/shared/`
3. **Document everything**: Every solution needs a README
4. **Test thoroughly**: Write tests for all custom nodes and workflows
5. **Use type hints**: Improve code clarity and IDE support
6. **Follow conventions**: Stick to the established patterns

## Adding a New Solution

1. Copy a template:
   ```bash
   cp -r templates/basic_etl src/solutions/my_new_solution
   ```

2. Update the solution name in files:
   - `__init__.py`
   - `workflow.py`
   - `config.yaml`

3. Customize the workflow for your needs

4. Add tests and documentation

5. Run validation:
   ```bash
   python scripts/validate.py src/solutions/my_new_solution
   ```

## Next Steps

- Learn about [Solution Development](../guide/solution_development.md)
- Explore [Templates](../templates/basic_etl.md)
- Read [Best Practices](../guide/best_practices.md)