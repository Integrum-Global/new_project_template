# Kailash SDK Solution Development Guide

## 🎯 Primary Development Workflow

### **Every Session: Check Current Status**
1. **Current Session**: Check `todos/000-master.md` - What's happening NOW (create from template if needed)
2. **Task Status**: Update todos from "pending" → "in_progress" → "completed"

### **Phase 1: Plan → Research**
- **Requirements**: Define business needs and success criteria
- **Research**: `guide/adr/` (architecture), `guide/workflows/` (process patterns)
- **Reference**: `guide/reference/CLAUDE.md` → cheatsheet, validation, patterns
- **Plan**: Clear solution approach with realistic timelines
- **Create & start todos**: Add new tasks from plan → mark "in_progress" in `todos/000-master.md` (create from template if needed)
- **Create implementation details**: Architecture and implementation plan with deliverables in `guide/todos/active/`

### **Phase 2: Implement → Example → Test → Learn**
- **Implement**: Use `reference/templates/` and `reference/cheatsheet/` for copy-paste patterns
- **Create Example**: MUST create working example in `examples/` directory and verify it runs successfully
- **Validate**: Check `guide/reference/validation/validation-guide.md` for LLM rules
- **Test**: Validate with real data, track issues in `mistakes/current-session-mistakes.md` (if present)
- **Node Selection**: Use `guide/reference/nodes/comprehensive-node-catalog.md`

### **Phase 3: Document → Deploy**
- **Update todos**: Mark completed in `todos/000-master.md` (create from template if needed)
- **Update mistakes**: Add learnings to `mistakes/` from current session (create from template if needed)
- **Update patterns**: Add new solution patterns to `guide/reference/pattern-library/`
- **Deploy**: Use `guide/reference/cheatsheet/` deployment patterns

## ⚡ Critical Validation Rules
1. **Node Names**: ALL end with "Node" (`CSVReaderNode` ✓)
2. **Methods**: ALL use snake_case (`add_node()` ✓)
3. **Config Keys**: ALL use underscores (`file_path` ✓)
4. **Config vs Runtime**: Config=HOW (static), Runtime=WHAT (dynamic data)
5. **Parameter Order**: Check exact signatures in `guide/reference/api/`

## 📁 Solution Module Organization
1. **Implementation Documentation**: Each solution MUST include implementation details in markdown files documenting considerations, steps, and design decisions
2. **Nodes**: Custom nodes go in `nodes/` directory under the solution module
3. **Workflows**: Main workflow logic organized in `workflows/` directory  
4. **Examples**: Solution-specific examples stored in `examples/` directory
5. **Tests**: Solution-specific tests organized in `tests/` directory

## 🔗 Essential References
- **Development**: `guide/reference/CLAUDE.md` → API reference, patterns, validation
- **Architecture**: `guide/adr/` → Design decisions and rationale
- **Process**: `guide/workflows/` → Development and deployment workflows
- **Templates**: `templates/` → Ready-to-use solution starting points

## 🔄 Learning Loop
Implementation → Mistakes → Analysis → Documentation → Better Solutions

## 📋 Template Sync & Project Structure
See detailed guides:
- **Migration**: `guide/instructions/migration-workflow.md`
- **Development Process**: `guide/workflows/`
- **Solution Structure**: `templates/` for starting points

## Template Sync Information

**This template preserves your work:**
- `src/solutions/` - Your business solutions with workflows/, nodes/, and examples/ directories (never touched)
- `data/` - Your data files (preserved, template samples added if missing)
- `.env*` files - Your environment configurations (never touched)
- `todos/` - Your task tracking (preserved if exists)
- `mistakes/` - Your error learning (preserved if exists)
- Custom workflow files ending in `*_custom.yml` (preserved)

**Template updates from SDK releases refresh:**
- `guide/reference/` - API docs, patterns, validation (updated from SDK)
- `guide/instructions/` - Development guidelines (merged with your customizations)
- `guide/workflows/` - Process patterns (merged with your customizations)
- `guide/frontend/` - UI development standards (updated from SDK)

**See `guide/reference/sync-files-reference.md` for complete sync details.**

## Project-Specific Instructions

<!-- Add your project-specific Claude Code instructions here -->
<!-- IMPORTANT: Template updates replace this entire file. When merging template updates, -->
<!-- manually merge your project-specific instructions from this section into the new CLAUDE.md -->
