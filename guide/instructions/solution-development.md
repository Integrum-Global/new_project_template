# Solution Development Guide

This guide provides detailed workflows for developing solutions with the Kailash SDK.

## Table of Contents
- [Solution Development Workflow](#solution-development-workflow)
- [Component Sharing Workflow](#component-sharing-workflow)
- [Solution Documentation Framework](#solution-documentation-framework)
- [Solution Development Process](#solution-development-process)
- [Debug Common Issues](#debug-common-issues)

## Solution Development Workflow

### Phase 1: Planning and Setup

1. **Check Current Priorities**
   - Review `todos/000-master.md` for active solution requirements
   - Identify business requirements and constraints
   - Check if similar solutions exist in `solutions/`

2. **Solution Design**
   - Break down requirements into workflow steps
   - Identify reusable components in `shared/`
   - Choose appropriate template from `templates/`
   - Plan data flow and error handling

### Phase 2: Implementation

3. **Create Solution Structure**
   ```bash
   # Create new solution package in src/
   mkdir -p src/solutions/my_solution
   cd src/solutions/my_solution
   
   # Create package structure
   touch __init__.py
   touch __main__.py
   touch workflow.py
   touch config.py
   
   # Copy template (choose appropriate one from reference/templates/)
   cp -r ../../../reference/templates/workflow/* ./
   
   # Update configuration
   cp ../../../.env.example ../../../.env
   ```

4. **Implement Core Logic**
   - Use `reference/api-registry.yaml` for exact APIs
   - Follow patterns from `reference/cheatsheet/README.md`
   - Reuse components from `shared/nodes/` and `shared/workflows/`
   - Validate with `python reference/validate_kailash_code.py`

5. **Configuration Management**
   - Create `config.yaml` with all parameters
   - Use environment variables for sensitive data
   - Document all configuration options in README.md

### Phase 3: Testing and Validation

6. **Test Solution**
   - Create `tests/` directory with unit tests
   - Test with sample data
   - Validate output format and quality
   - Test error handling scenarios

7. **Integration Testing**
   - Test with realistic data volumes
   - Verify performance requirements
   - Test with various input formats
   - Validate against business requirements

### Phase 4: Documentation and Deployment

8. **Document Solution**
   - Update solution README.md with usage instructions
   - Document configuration options
   - Include example inputs/outputs
   - Add troubleshooting guide

9. **Share Components**
   - Extract reusable nodes to `shared/nodes/`
   - Extract reusable workflows to `shared/workflows/`
   - Update shared component documentation
   - Update todos with completion status

## Component Sharing Workflow

### Creating Shared Nodes
- Extract common node logic from solutions
- Place in appropriate `shared/nodes/` category
- Write comprehensive tests
- Document usage and configuration
- Update imports in existing solutions

### Creating Shared Workflows
- Identify reusable workflow patterns
- Make configurable via parameters
- Add to `shared/workflows/`
- Write integration tests
- Document usage examples

## Solution Documentation Framework

### Architecture Decision Records (ADR)
**`guide/adr/`** - Document significant solution design decisions
- Why specific integration patterns were chosen
- Trade-offs between different approaches
- Technology selection rationale
- Performance vs. cost decisions

**When to create an ADR:**
- Making non-obvious design choices
- Choosing between multiple valid approaches
- Establishing patterns for shared components
- Documenting integration strategies

**ADR Template Example:**
```markdown
# ADR-001: Batch Processing vs. Real-time for Sales Data

## Status
Accepted

## Context
Sales data arrives hourly but dashboard needs near real-time updates.

## Decision
Use batch processing with 15-minute intervals.

## Consequences
- Good: Lower API costs, better error handling
- Bad: 15-minute delay in dashboard updates
```

### Mistakes and Lessons Learned
**`mistakes/000-master.md`** - Track solution-specific issues
- Common API integration problems
- Data quality issues and fixes
- Performance bottlenecks discovered
- Production failures and resolutions

**When to document mistakes:**
- After resolving any production issue
- When discovering non-obvious API behavior
- After performance optimization
- When data assumptions prove incorrect

**Mistake Documentation Example:**
```markdown
## API Rate Limiting Issue (2024-01-15)
**Problem**: SharePoint API returns 429 after 100 requests/minute
**Impact**: Solution failed during large data syncs
**Solution**: Implemented exponential backoff and request batching
**Prevention**: Added rate limiting to shared API connector nodes
```

### Solution Requirements
**`guide/requirements/`** - Business requirements for solutions
- What each solution must achieve
- Success metrics and KPIs
- Stakeholder needs and constraints
- Scope boundaries

**Requirements Template:**
```markdown
# Solution: Customer Analytics Dashboard

## Business Need
Provide real-time visibility into customer behavior patterns.

## Success Criteria
- [ ] Process 100K records within 5 minutes
- [ ] 99.9% uptime during business hours
- [ ] Export capability to Excel/PDF
- [ ] Role-based access control

## Constraints
- Must use existing SharePoint data
- Cannot exceed $500/month in API costs
- Must comply with GDPR requirements
```

## Solution Development Process

### 1. Plan Your Solution
```bash
# Create solution directory
mkdir my_solution
cd my_solution

# Copy reference files
cp -r /path/to/kailash_sdk/guide/reference ./
cp -r /path/to/kailash_sdk/todos ./

# Create solution file
cp reference/CLAUDE_SOLUTIONS.md ./CLAUDE.md
```

### 2. Build Incrementally
1. **Start Simple**: Create minimal workflow with 2-3 nodes
2. **Test Early**: Run workflow to verify basic functionality
3. **Add Complexity**: Add more nodes and connections incrementally
4. **Validate Often**: Use validation tools after each change

### 3. Solution Creation Workflow

#### Step 1: Requirements Analysis
```markdown
# Solution Requirements Template
## Problem Statement
- What needs to be solved?
- What are the inputs and outputs?
- What processing steps are needed?

## Workflow Design
- [ ] Data sources (CSV, API, database, etc.)
- [ ] Processing steps (transform, filter, analyze, etc.)
- [ ] Output destinations (files, APIs, dashboards, etc.)
- [ ] Error handling requirements
- [ ] Performance requirements

## Implementation Plan
- [ ] Break into workflow steps
- [ ] Identify required node types
- [ ] Plan data flow between nodes
- [ ] Design error handling
```

#### Step 2: Package Structure Example

For each solution, create the following structure in `src/solutions/`:

**`__init__.py`** - Package initialization
```python
"""Customer Analytics Solution Package."""
from .workflow import create_workflow
from .config import load_config

__all__ = ['create_workflow', 'load_config']
```

**`__main__.py`** - Entry point for `python -m solutions.customer_analytics`
```python
"""Run the customer analytics solution."""
import sys
from .workflow import main

if __name__ == "__main__":
    sys.exit(main())
```

**`config.py`** - Configuration management
```python
"""Configuration for customer analytics solution."""
import os
from pathlib import Path
import yaml

def load_config(config_path=None):
    """Load configuration from file or environment."""
    if not config_path:
        config_path = Path(__file__).parent.parent.parent.parent / "data/configs/customer_analytics.yaml"
    
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    # Override with environment variables
    config['api_key'] = os.getenv('API_KEY', config.get('api_key'))
    
    return config
```

## Debug Common Issues
```python
# Enable debug mode for detailed logging
runtime = LocalRuntime(debug=True)

# Check workflow structure before execution
workflow.validate()  # Validates connections and structure

# Inspect intermediate results
results, run_id = runtime.execute(workflow)
print(f"Node outputs: {results}")
```

## Quick Validation Commands
```bash
# Validate a single solution file
python reference/validate_kailash_code.py src/solutions/my_solution/workflow.py

# Test shared components
pytest src/shared/tests/ -v

# Test specific solution
pytest src/solutions/my_solution/tests/ -v

# Run all tests (shared + all solutions)
pytest src/ -v

# Install Kailash SDK
pip install kailash

# Install solution package in development mode
pip install -e .

# Run a solution as a module
python -m solutions.my_solution

# Or run directly
python src/solutions/my_solution/__main__.py

# Check for syntax issues
python -m py_compile src/solutions/my_solution/*.py

# Run tests for just one solution
cd src/solutions/my_solution && python -m pytest tests/ -v
```