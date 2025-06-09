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

### **Phase 2: Implement → Test → Learn**
- **Implement**: Use `reference/templates/` and `reference/cheatsheet/` for copy-paste patterns
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
- `src/solutions/` - Your business solutions (never touched)
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
<!-- These instructions will be preserved during template updates -->