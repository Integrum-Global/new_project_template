# Enterprise Workflow Development Template

A comprehensive template for translating enterprise workflows into executable code using the [Kailash Python SDK](https://integrum-global.github.io/kailash_python_sdk/) with [Claude Code](https://claude.ai/code) as the primary development workflow tool.

## Overview

This template provides a foundation for building node-based workflow architectures that transform complex business processes into automated, maintainable code pipelines. It's specifically designed to work seamlessly with Claude Code for AI-assisted development of enterprise workflows using the Kailash SDK.

### Why Claude Code + Kailash SDK?

- **AI-Assisted Workflow Development**: Claude Code understands the Kailash SDK patterns and can help generate, refactor, and optimize workflow code
- **Comprehensive Documentation Integration**: Built-in support for ADRs, PRDs, and todo management that Claude Code can leverage
- **Quality Assurance**: Automated testing, code formatting, and quality checks that ensure high-quality workflow implementations
- **Enterprise-Ready**: Structured approach to translating complex business processes into maintainable code

## Getting Started

### Prerequisites
- Python 3.11+ (required)
- [uv](https://docs.astral.sh/uv/) for fast Python package management
- [Claude Code](https://claude.ai/code) for AI-assisted development
- Git for version control
- IDE with Python support (VS Code, PyCharm, etc.)

### Quick Setup

1. **Install uv** (if not already installed)
   ```bash
   # macOS/Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # Windows
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

2. **Clone and Setup Environment**
   ```bash
   git clone <your-repo-url>
   cd new_project_template
   ```

3. **Install Dependencies**
   ```bash
   uv sync
   ```
   This creates a virtual environment and installs all dependencies from pyproject.toml.

4. **Activate Environment**
   Automated if using uv, but you can manually activate it:
   ```bash
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

5. **Install Pre-commit Hooks** (Recommended)
   ```bash
   uv run pre-commit install
   ```

6. **Initialize Claude Code Session**
   ```bash
   # Open your project in Claude Code
   claude-code .
   ```
   Claude Code will automatically detect the project structure and documentation framework.

## Enterprise Workflow Translation

### Core Concept
**Enterprise Process -> Kailash Nodes -> Executable Workflows**

### Claude Code Development Process
1. **Analyze Client Workflow**: Use Claude Code to break down business process into discrete steps
2. **Map to Kailash Nodes**: Let Claude Code suggest appropriate built-in nodes or generate custom ones
3. **Define Connections**: Claude Code can help design the workflow pipeline architecture
4. **Configure & Execute**: Claude Code assists with parameter setup and workflow execution
5. **Document & Test**: Automated generation of documentation, examples, and tests

### Example Workflow
```python
from kailash import Workflow

# Create workflow for client data processing
workflow = Workflow("client_enterprise_process")

# Add nodes for each step
data_reader = workflow.add_node("CSVReader", config={"file_path": "client_data.csv"})
transformer = workflow.add_node("DataTransformer", config={"rules": client_rules})
api_sender = workflow.add_node("APIClient", config={"endpoint": client_api})

# Connect the workflow
workflow.add_edge("data_reader", "transformer")
workflow.add_edge("transformer", "api_sender")

# Execute
results = workflow.run()
```

## Claude Code Development Workflow

### Session-Based Development
Claude Code provides structured development sessions that align with enterprise workflow requirements:

1. **Document Requirements**: 
   - Use Claude Code to create comprehensive PRDs in `guide/prd/`
   - Leverage AI to translate business requirements into technical specifications

2. **Design Architecture**: 
   - Claude Code helps document architectural decisions in `guide/adr/`
   - AI-assisted analysis of Kailash SDK patterns and best practices

3. **Implement Nodes**: 
   - Generate custom nodes in `src/` with proper "Node" suffix naming
   - Claude Code ensures adherence to coding standards and patterns

4. **Create Examples**: 
   - Auto-generate working examples in `examples/` with proper categorization
   - Claude Code creates comprehensive usage demonstrations

5. **Write Tests**: 
   - Generate unit tests in `tests/` and integration tests for workflows
   - Automated test coverage and quality assurance

6. **Update Documentation**: 
   - Auto-update Sphinx docs in `docs/`
   - Maintain comprehensive API documentation with examples

### Claude Code Integration Features

- **Todo Management**: Integrated with `guide/todos/` system for session tracking
- **Quality Assurance**: Automatic code formatting, linting, and testing
- **Documentation**: Auto-generation of docstrings, examples, and API docs
- **Mistake Prevention**: References `guide/mistakes/` to avoid common pitfalls

## Project Structure

```
new_project_template/
├── src/                        # SOURCE CODE - All Python packages
│   ├── shared/                 # Shared components package
│   │   ├── nodes/             # Custom shared nodes
│   │   ├── workflows/         # Reusable workflow components
│   │   └── utils/             # Shared utilities
│   └── solutions/              # Individual solution packages
│       └── new_module/        # Example solution module
├── docs/                       # Documentation (Sphinx)
│   ├── api/                   # API documentation
│   ├── guides/               # User guides
│   │   ├── solution-development.md  # Detailed solution workflows
│   │   ├── solution-templates.md    # Ready-to-use templates
│   │   ├── checklists.md           # Quick reference checklists
│   │   └── best-practices.md       # Development best practices
│   └── examples/             # Example usage
├── guide/                      # Solution development guides
│   ├── adr/                   # Architecture Decision Records
│   ├── mistakes/             # Mistakes and lessons learned
│   └── prd/                  # Product Requirements Documents
├── reference/                  # API references (from SDK)
│   ├── api-registry.yaml     # Exact API specifications
│   ├── validation-guide.md   # Error prevention rules
│   └── cheatsheet.md        # Common patterns
├── templates/                  # Solution templates
├── todos/                      # Solution tracking
│   ├── 000-master.md         # Active solution priorities
│   └── completed-archive.md  # Completed solutions
├── data/                       # Data files (not in src/)
│   ├── samples/               # Sample data for testing
│   ├── configs/              # Configuration files
│   └── outputs/              # Output directory
├── scripts/                    # Utility scripts
│   ├── deploy.py             # Deployment script
│   ├── validate.py           # Validation script
│   └── setup_env.py          # Environment setup
├── CLAUDE.md                   # Claude Code instructions & quick reference
├── pyproject.toml              # Modern Python packaging config
└── uv.lock                    # Dependency lock file
```

## Key Kailash SDK Concepts

- **Nodes**: Discrete processing units (data readers, transformers, API clients)
- **Workflows**: Connected sequences of nodes
- **Edges**: Data flow connections between nodes
- **Runtime**: Execution environment (local, Docker, async, parallel)

## Testing

```bash
# Run all tests
uv run pytest

# Test examples
cd examples
uv run python _utils/test_all_examples.py

# Build documentation
cd docs
uv run python build_docs.py
```

## Code Quality

This template includes automated code quality tools:
- **Black**: Code formatting
- **isort**: Import sorting
- **Ruff**: Fast Python linting
- **mypy**: Type checking
- **Pre-commit hooks**: Automated quality checks

## Documentation

- **API Documentation**: Auto-generated with Sphinx
- **Architecture Decisions**: Documented in `guide/adr/`
- **Development Guide**: See `CLAUDE.md` for detailed coding standards

## Contributing

1. Follow the coding standards in `CLAUDE.md`
2. Create examples for new functionality
3. Write comprehensive tests
4. Document architectural decisions
5. Update relevant PRDs and ADRs

## Resources

### Primary Tools
- [Claude Code](https://claude.ai/code) - AI-assisted development workflow
- [Kailash SDK Documentation](https://integrum-global.github.io/kailash_python_sdk/) - Node-based workflow framework

### Project Documentation
- [Project ADRs](guide/adr/) - Architecture Decision Records
- [Current Todos](guide/todos/000-master.md) - Active development tasks
- [Development Mistakes to Avoid](guide/mistakes/000-master.md) - Common pitfalls
- [Coding Standards](CLAUDE.md) - Comprehensive development guidelines

### Claude Code Workflow Tips
1. **Start each session** by reading current todos: `guide/todos/000-master.md`
2. **Follow the documentation structure** outlined in `CLAUDE.md`
3. **Use the ADR process** for architectural decisions
4. **Leverage automated testing** with `examples/_utils/test_all_examples.py`
5. **Maintain code quality** with pre-commit hooks and automated formatting