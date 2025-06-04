# Kailash SDK Solutions - Claude Code Instructions

## 🚨 CRITICAL: Check These First!

### 1. API Reference - NEVER GUESS!
**STOP!** Before writing ANY code:
1. Open `reference/api-registry.yaml` for exact APIs
2. Check `reference/validation-guide.md` for rules
3. Use `reference/cheatsheet.md` for common patterns
4. Never guess method names, class names, or parameters

### 2. Solution Planning
**`todos/000-master.md`** - Track your solution progress
- Break down requirements into tasks
- Mark progress as you implement
- Document any issues encountered

## Quick Reference Links
- **API Reference**: `reference/api-registry.yaml` ← EXACT APIs HERE
- **Common Patterns**: `reference/cheatsheet.md` ← COPY THESE
- **Validation Rules**: `reference/validation-guide.md` ← PREVENT ERRORS
- **Shared Components**: `src/shared/` ← REUSE THESE
- **Solution Templates**: `templates/` ← START HERE
- **Project Todos**: `todos/000-master.md` ← TRACK PROGRESS

## Core Rules (MEMORIZE THESE)
1. **ALL node classes end with "Node"**: `CSVReaderNode` ✓, `CSVReader` ✗
2. **ALL methods use snake_case**: `add_node()` ✓, `addNode()` ✗
3. **ALL config keys use underscores**: `file_path` ✓, `filePath` ✗
4. **Workflow execution pattern**: Always use `runtime.execute(workflow, parameters={...})` ✓
5. **Parameter order is STRICT**: Check exact signatures in api-registry.yaml
6. **Docstring examples use doctest format**: `>>> code` ✓, `:: code` ✗
7. **get_parameters() defines ALL node parameters**: Both config AND runtime
8. **Config vs Runtime**: Config=HOW (static), Runtime=WHAT (dynamic data)
9. **Execution inputs**: Use `runtime.execute(workflow, parameters={...})` only
10. **Initial workflow data**: Can use source nodes OR pass via parameters to ANY node
11. **Use Workflow.connect()**: NOT WorkflowBuilder (different API, causes confusion)

## 📚 Documentation Guides
- **[Solution Development Guide](guide/instructions/solution-development.md)** - Detailed workflow processes
- **[Solution Templates](templates/README.md)** - Ready-to-use code templates
- **[Development Checklists](guide/instructions/checklists.md)** - Quick reference checklists
- **[Best Practices](guide/instructions/best-practices.md)** - Development best practices

## 📋 TODO Management System (CRITICAL)

The todo system in `todos/` at the root directory is the central task tracking system:

### File Structure:
- **`000-master.md`** - ACTIVE TODO LIST (Always check first!)
  - Current tasks and priorities
  - Tasks in progress
  - Urgent client needs
  - Recent achievements

- **`completed-archive.md`** - Historical record
  - All completed tasks from past sessions
  - Detailed implementation notes
  - Session summaries and statistics

- **Numbered files** (001-xxx.md) - Session-specific logs
  - How todos were approached and resolved
  - Challenges faced and solutions found
  - Lessons learned for future reference

### When to Update:
- **Start of session**: Check 000-master.md for priorities
- **Starting a task**: Mark as "In Progress"
- **Completing a task**: Mark as "Completed" immediately
- **Finding new tasks**: Add to appropriate priority level
- **End of session**: Move completed tasks to archive

## Maintaining Mistakes Documentation

When documenting mistakes:
1. **Full Documentation** (`000-master.md`): Add complete details, code examples, impact, solution
2. **Quick Reference** (`consolidated-guide.md`): Update if the mistake represents a common pattern that Claude Code needs to avoid

The consolidated guide should only contain:
- Critical API patterns (with ✅/❌ examples)
- Common pitfalls by category
- Quick fixes for frequent errors
- Validation checklist items

## Primary Workflows (MANDATORY)

### Migration Workflow

When migrating existing projects to Kailash SDK:

1. **Place project in**: `migrations/to_migrate/[project_name]/`
2. **Follow migration guide**: See **[Migration Workflow Instructions](guide/instructions/migration-workflow.md)**
3. **Use templates**: Check `migrations/templates/` for document templates
4. **Update todos**: Add migration tasks to `todos/000-master.md`

**Key Points:**
- Manual analysis required - each project is unique
- Create comprehensive documentation before coding
- Ask questions when patterns are unclear
- Think in Kailash workflows, not direct translation

### Solution Development Workflow

#### PLAN: Define requirements
1. **Check Current Priorities**
   - Review `todos/000-master.md` for active requirements
   - Document requirements in `guide/prd/`
   - Check existing solutions in `src/solutions/`

2. **Design Solution Architecture**
   - Break down into workflow steps
   - Identify reusable components in `src/shared/`
   - Document decisions in `guide/adr/`

3. **Create Task Plan**
   - Update `todos/000-master.md` with subtasks
   - Define success criteria
   - Estimate effort and timeline

#### IMPLEMENT: Write code
4. **Use Reference Documentation**
   - Check `reference/api-registry.yaml` for exact APIs
   - Follow patterns from `reference/cheatsheet.md`
   - Review `reference/validation-guide.md` for rules

5. **Create Solution Structure**
   ```bash
   mkdir -p src/solutions/my_solution
   cd src/solutions/my_solution
   touch __init__.py __main__.py workflow.py config.py
   ```

6. **Write detailed docstrings**
   - Follow guide/instructions/documentation-requirements.md
   - Include all 8 required sections (design, dependencies, usage, implementation, etc.)
   - Use Google-style format with doctest examples (>>> syntax)
   - Document all parameters, returns, raises, and side effects
   
7. **Write Examples FIRST**
   - Start with basic template from `templates/`
   - Create `examples/` directory in your solution
   - Write `basic_usage.py` showing simple use case
   - Write `advanced_usage.py` showing all features
   - Validate: `python reference/validate_kailash_code.py examples/*.py`
   - Test execution to ensure they work

8. **Implement Full Solution**
   - Build on validated prototype
   - Add error handling and edge cases
   - Extract reusable parts to `src/shared/`

#### TEST: Verify everything works
9. **Write Tests**
   - Create `tests/` directory in solution
   - Test core workflow logic
   - Test error handling
   - Run: `pytest src/solutions/my_solution/tests/`

10. **Integration Testing**
    - Test with real data samples
    - Verify performance requirements
    - Check memory usage for large datasets

11. **Run Validation**
    - Validate code: `python reference/validate_kailash_code.py src/solutions/my_solution/*.py`
    - Run linting: `black . && isort . && ruff check .`

#### DOCUMENT: Update all docs
12. **Update Task Tracking**
    - Update `todos/000-master.md` (mark completed)
    - Document issues in `guide/mistakes/000-master.md`
    - Create ADR if design decisions made

13. **Solution Documentation**
    - Create README.md in solution directory
    - Document configuration options
    - Include usage examples
    - Add troubleshooting guide

14. **Update Project Docs**
    - Update project structure in `guide/prd/000-project_structure.md`
    - Update main README.md if needed
    - Add to `CHANGELOG.md`
    - Update Sphinx docs: `cd docs && python build_docs.py`

#### FINALIZE: Prepare for deployment
15. **Code Review**
    - Review all changes
    - Ensure follows best practices
    - Check for hardcoded values

16. **Final Testing**
    - Run full test suite: `pytest`
    - Test in production-like environment
    - Verify all requirements met

17. **Deploy**
    - Run deployment script: `python scripts/deploy.py`
    - Monitor initial execution
    - Document any post-deployment issues

### Solution Structure
See **[Full Project Structure](guide/prd/000-project_structure.md)** for complete repository organization.

Quick reference for solution structure:
```
src/solutions/my_solution/
├── __init__.py        # Package exports
├── __main__.py        # Entry point (python -m solutions.my_solution)
├── workflow.py        # Main workflow logic
├── config.py          # Configuration management
├── README.md          # Solution documentation
├── config.yaml        # Default configuration
├── examples/          # Working examples
│   ├── basic_usage.py
│   └── advanced_usage.py
└── tests/             # Solution tests
```

## Error Prevention
- [ ] All node class names end with "Node"
- [ ] All method names use snake_case
- [ ] Configuration passed as kwargs, NOT as dict
- [ ] Connections use mapping={"output": "input"}
- [ ] Execution uses runtime.execute(workflow)
- [ ] Import paths are complete and correct

## Important Reminders
- **Check references first** - Don't guess APIs
- **Reuse shared components** - Check `shared/` directory in each solution
- **Follow templates** - Start from `templates/`
- **Test frequently** - Enable debug mode
- **Track progress** - Update todos

For detailed guides, see the `guide/instructions/` directory.