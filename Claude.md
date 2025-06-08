# Kailash SDK Solutions - Claude Code Instructions

## 🚨 FIRST: Always Check These
1. **CURRENT SESSION**: `guide/todos/000-master.md` - What's happening NOW & immediate priorities
2. **TODO SYSTEM**: `guide/todos/README.md` - How to use the todos system & file navigation
3. **API Reference**: `reference/api/` - Modular API docs by module (workflow, nodes, security)
4. **VALIDATION**: `reference/validation/solution-validation-guide.md` - Critical rules to prevent mistakes
5. **WORKFLOW GUIDE**: `guide/workflows/solution-development-phases.md` - Full 5-phase process details
6. **MISTAKES GUIDE**: `guide/mistakes/README.md` - Quick reference for documented mistakes and solutions
7. **CHEATSHEET**: `reference/cheatsheet/README.md` - Quick reference organized by topic with focused examples

## 🚀 Solution Development Workflow Phases

### Phase 1: Discovery & Planning
```
PLAN MODE:
1. Check: guide/todos/000-master.md (current session status & immediate priorities)
2. Review: guide/todos/active/ (existing plans & implementation details)
3. Research: reference/api/, reference/nodes/, reference/pattern-library/
4. Review: guide/mistakes/README.md for known issues & patterns
5. Output: Solution architecture plan with deliverables
```

### Phase 2: Implementation & Integration
```
EDIT MODE:
6. Update TODOs → In Progress (in guide/todos/000-master.md)
7. Check implementation details (in guide/todos/active/)
8. Write solution examples → Debug → Learn
9. Use reference/cheatsheet/ for quick patterns
10. Reference mistakes from guide/mistakes/README.md when resolving issues
11. Implement → Test → Learn more
12. Track all mistakes in: guide/mistakes/current-session-mistakes.md
```

### Phase 3: Testing & Validation
```
VALIDATION MODE:
13. List all mistakes from current-session-mistakes.md
14. Identify patterns and root causes
15. Plan which docs need updates
16. Run validation checklist from reference/validation/
17. Output: Validation report and documentation update plan
```

### Phase 4: Documentation & Deployment Prep
```
EDIT MODE:
18. Update all docstrings to solution development standards
19. Create guide/mistakes/XXX-mistake-name.md (detailed mistake file)
20. Update guide/mistakes/README.md (add link to browse by category and index)
21. Remove mistakes from current-session-mistakes.md
22. Update relevant reference docs
23. Complete deployment checklist from reference/validation/deployment-checklist.md
```

### Phase 5: Deployment & Monitoring
```
EDIT MODE:
24. Run full validation suite
25. Deploy using patterns from reference/cheatsheet/006-deployment-patterns.md
26. Update TODOs → Complete (in guide/todos/000-master.md)
27. Set up monitoring and alerting
28. Document deployment and handover
```

## Core Rules (MEMORIZE THESE)
1. **ALL node classes end with "Node"**: `CSVReaderNode` ✓, `CSVReader` ✗
2. **ALL methods use snake_case**: `add_node()` ✓, `addNode()` ✗
3. **ALL config keys use underscores**: `file_path` ✓, `filePath` ✗
4. **Workflow execution pattern**: Always use `runtime.execute(workflow, parameters={...})` ✓
5. **Parameter order is STRICT**: Check exact signatures in reference/api/
6. **Docstring examples use doctest format**: `>>> code` ✓, `:: code` ✗
7. **get_parameters() defines ALL node parameters**: Both config AND runtime
8. **Config vs Runtime**: Config=HOW (static), Runtime=WHAT (dynamic data)
9. **Execution inputs**: Use `runtime.execute(workflow, parameters={...})` only
10. **Initial workflow data**: Can use source nodes OR pass via parameters to ANY node
11. **Use Workflow.connect()**: NOT WorkflowBuilder (different API, causes confusion)
12. **ASYNC is DEFAULT**: Use async/await patterns wherever possible, especially for I/O operations
13. **Solution Focus**: Build for production deployment, not SDK development

## Common Pitfalls (Avoid These!)
1. **Config vs Runtime** (#1 issue!): Config=HOW (code, paths), Runtime=WHAT (data)
2. **Hardcoded Credentials**: Always use environment variables for secrets
3. **Missing Error Handling**: Implement robust error handling for production
4. **Unvalidated External Data**: Always validate data from external sources
5. **Poor Resource Management**: Use connection pooling and proper cleanup

📋 **Quick reference guide**:
- **Solution Patterns?** → `reference/pattern-library/`
- **Code Snippets?** → `reference/cheatsheet/`
- **API Specs?** → `reference/api/`
- **Validation?** → `reference/validation/`

## 📁 Context-Optimized Navigation

### For Planning (Phases 1 & 3):
- `guide/todos/000-master.md` - Current state
- `reference/api/` - API specs
- `guide/mistakes/README.md` - Mistakes index & critical patterns
- `reference/pattern-library/` - Solution patterns
- `reference/nodes/` - Essential nodes for solutions

### For Implementation (Phase 2):
- `guide/todos/000-master.md` - Update task status
- `guide/todos/active/` - Implementation details
- `reference/cheatsheet/` - Quick code patterns and examples
- `reference/templates/` - Ready-to-use code templates
- `guide/mistakes/current-session-mistakes.md` - Track issues
- `reference/validation/deployment-checklist.md` - Validation steps

### For Documentation (Phase 4):
- `guide/mistakes/` - Update mistake logs
- `reference/api/` - Update API docs
- `reference/nodes/` - Update node catalog
- `reference/validation/` - Update validation rules
- `reference/pattern-library/` - Update solution patterns

### For Deployment (Phase 5):
- `reference/cheatsheet/006-deployment-patterns.md` - Deployment implementation
- `reference/validation/deployment-checklist.md` - Production readiness
- `reference/cheatsheet/016-environment-variables.md` - Configuration management

## 🔄 Learning Loop
Implementation → Mistakes → Analysis → Documentation → Better Solutions

## 📋 Solution Development Workflow

### Migration Workflow
When migrating existing projects to Kailash SDK:

1. **Place project in**: `migrations/to_migrate/[project_name]/`
2. **Follow migration guide**: See **[Migration Workflow Instructions](guide/workflows/migration-workflow.md)**
3. **Use templates**: Check `migrations/templates/` for document templates
4. **Update todos**: Add migration tasks to `guide/todos/000-master.md`

### Quick Development Process
1. **PLAN**: Check `guide/todos/000-master.md` → Use `reference/pattern-library/` → Design solution
2. **IMPLEMENT**: Use `reference/cheatsheet/` → Build with `reference/templates/` → Track in todos
3. **TEST**: Validate with `reference/validation/` → Test with realistic data → Document issues
4. **DOCUMENT**: Update todos → Create solution docs → Track mistakes
5. **DEPLOY**: Use `reference/cheatsheet/006-deployment-patterns.md` → Monitor → Handover

### Solution Structure
```
src/solutions/my_solution/
├── __init__.py        # Package exports
├── __main__.py        # Entry point (python -m solutions.my_solution)
├── workflow.py        # Main workflow logic
├── config.py          # Configuration management
├── README.md          # Solution documentation
├── examples/          # Working examples
└── tests/             # Solution tests
```

## Error Prevention Checklist
- [ ] All node class names end with "Node"
- [ ] All method names use snake_case
- [ ] Environment variables used for all secrets
- [ ] Connections use mapping={"output": "input"}
- [ ] Execution uses runtime.execute(workflow)
- [ ] Error handling implemented for external systems

## Important Reminders
- **Check references first** - Don't guess APIs
- **Use solution patterns** - Check `reference/pattern-library/`
- **Follow deployment patterns** - Check `reference/cheatsheet/006-deployment-patterns.md`
- **Track progress** - Update guide/todos/000-master.md
- **Document mistakes** - Use guide/mistakes/current-session-mistakes.md

## Quick Reference Links
- **TODO LIST (CRITICAL)**: `guide/todos/000-master.md` ← CHECK FIRST!
- **API Reference**: `reference/api/` ← Modular API documentation
- **Node Catalog**: `reference/nodes/` ← Essential nodes for solutions
- **Pattern Library**: `reference/pattern-library/` ← Complete solution patterns
- **Cheatsheet**: `reference/cheatsheet/` ← Quick code patterns
- **Templates**: `reference/templates/` ← Ready-to-use code
- **Validation**: `reference/validation/` ← Solution validation tools
- **Deployment**: `reference/cheatsheet/006-deployment-patterns.md` ← Production deployment
- **Mistakes Guide**: `guide/mistakes/README.md` ← Organized mistake patterns

For detailed guides, see the `guide/` directory structure.

## Updating Template-Managed Files in Downstream Repositories

When working in a downstream repository created from this template, certain files are managed by the template sync process. 
Add new custom instructions under this section to preserve them during updates.

## Project-Specific Instructions

<!-- Add your project-specific Claude Code instructions here -->
<!-- These instructions will be preserved during template updates -->