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
4. **Workflow execution patterns**: `runtime.execute(workflow)` ✓, `workflow.execute(runtime)` ✗
5. **Parameter order is STRICT**: Check exact signatures in api-registry.yaml

## 📚 Documentation Guides
- **[Solution Development Guide](guide/instructions/solution-development.md)** - Detailed workflow processes
- **[Solution Templates](templates/README.md)** - Ready-to-use code templates
- **[Development Checklists](guide/instructions/checklists.md)** - Quick reference checklists
- **[Best Practices](guide/instructions/best-practices.md)** - Development best practices

## Primary Workflows (MANDATORY FOR ALL USERS)

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

6. **Write Examples FIRST**
   - Start with basic template from `templates/`
   - Create `examples/` directory in your solution
   - Write `basic_usage.py` showing simple use case
   - Write `advanced_usage.py` showing all features
   - Validate: `python reference/validate_kailash_code.py examples/*.py`
   - Test execution to ensure they work

7. **Implement Full Solution**
   - Build on validated prototype
   - Add error handling and edge cases
   - Extract reusable parts to `src/shared/`

#### TEST: Verify everything works
8. **Write Tests**
   - Create `tests/` directory in solution
   - Test core workflow logic
   - Test error handling
   - Run: `pytest src/solutions/my_solution/tests/`

9. **Integration Testing**
   - Test with real data samples
   - Verify performance requirements
   - Check memory usage for large datasets

10. **Run Validation**
    - Validate code: `python reference/validate_kailash_code.py src/solutions/my_solution/*.py`
    - Run linting: `black . && isort . && ruff check .`

#### DOCUMENT: Update all docs
11. **Update Task Tracking**
    - Update `todos/000-master.md` (mark completed)
    - Document issues in `guide/mistakes/000-master.md`
    - Create ADR if design decisions made

12. **Solution Documentation**
    - Create README.md in solution directory
    - Document configuration options
    - Include usage examples
    - Add troubleshooting guide

13. **Update Project Docs**
    - Update project structure in `guide/prd/000-project_structure.md`
    - Update main README.md if needed
    - Add to `CHANGELOG.md`
    - Update Sphinx docs: `cd docs && python build_docs.py`

#### FINALIZE: Prepare for deployment
14. **Code Review**
    - Review all changes
    - Ensure follows best practices
    - Check for hardcoded values

15. **Final Testing**
    - Run full test suite: `pytest`
    - Test in production-like environment
    - Verify all requirements met

16. **Deploy**
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

⚠️ **CRITICAL**: The pattern `workflow.execute(runtime)` does NOT exist. Always use `runtime.execute(workflow)`.

## Important Reminders
- **Check references first** - Don't guess APIs
- **Reuse shared components** - Check `shared/` directory in each solution
- **Follow templates** - Start from `templates/`
- **Test frequently** - Enable debug mode
- **Track progress** - Update todos

For detailed guides, see the `guide/instructions/` directory.