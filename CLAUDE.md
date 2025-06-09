# Solution Development with Kailash SDK

## 🎯 Quick Navigation
- **Build workflows** → sdk-users/ (synced from SDK, don't edit)
- **Track project** → todos/, adr/, mistakes/ (project-specific)  
- **Business logic** → src/solutions/ (your implementations)
- **Project vision** → prd/ (your requirements)
- **Migrate legacy** → migrations/ (convert existing projects)

## ⚡ Critical Validation Rules
1. **Node Names**: ALL end with "Node" (`CSVReaderNode` ✓)
2. **PythonCodeNode**: Input variables EXCLUDED from outputs!
   - `mapping={"result": "input_data"}` ✓
   - `mapping={"result": "result"}` ✗
3. **Parameter types**: ONLY `str`, `int`, `float`, `bool`, `list`, `dict`, `Any`

## 🚀 Quick Code Patterns
```python
# Basic workflow
workflow = Workflow("id", "name")
workflow.add_node("reader", CSVReaderNode(), file_path="data.csv")
workflow.connect("reader", "writer", mapping={"data": "data"})
runtime.execute(workflow, parameters={})

# PythonCodeNode (correct pattern)
workflow.connect("discovery", "processor", mapping={"result": "input_data"})
processor = PythonCodeNode(name="processor", code="result = {'count': len(input_data)}")
```

## 🎯 Solution Development Workflow

### **Every Session: Check Current Status**
1. **Current Session**: Check `todos/000-master.md` - What's happening NOW
2. **Task Status**: Update todos from "pending" → "in_progress" → "completed"

### **Phase 1: Plan → Research**
- **Requirements**: Define business needs in `prd/`
- **Legacy Analysis**: Use `migrations/` for existing project conversion
- **Research**: `sdk-users/patterns/` and `sdk-users/workflows/` for solutions
- **Architecture**: Document decisions in `adr/`
- **Plan**: Clear solution approach with deliverables
- **Create & start todos**: Add tasks → mark "in_progress" in `todos/`

### **Phase 2: Implement → Example → Test**
- **Migration**: Follow `sdk-users/instructions/migration-workflow.md` for legacy conversion
- **Implement**: Use `sdk-users/essentials/` and `sdk-users/templates/` for patterns
- **Custom Nodes**: Follow `sdk-users/developer/` for node creation
- **Create Example**: MUST create working example and verify it runs
- **Validate**: Check `sdk-users/validation-guide.md` for correctness
- **Track mistakes**: Document issues in `mistakes/current-session-mistakes.md`
- **Test**: Validate with real data and scenarios

### **Phase 3: Document → Deploy → Learn**
- **Update todos**: Mark completed in `todos/`
- **Update mistakes**: Add learnings from current session
- **Document architecture**: Update `adr/` with decisions made
- **Migration completion**: Move completed projects in `migrations/completed/`
- **Deploy**: Use `sdk-users/patterns/pattern-library/09-deployment-patterns.md`
- **Learn**: Capture patterns for future solutions

## 📁 Project Structure for Solutions
1. **Implementation**: Each solution in `src/solutions/[module]/`
2. **Migration Projects**: Legacy conversions in `migrations/`
3. **Documentation**: Architecture decisions in `adr/`
4. **Examples**: Working examples in solution modules
5. **Learning**: Track errors and patterns in `mistakes/`

## 🔗 Essential References
- **Development**: `sdk-users/developer/CLAUDE.md` → API reference, patterns, validation
- **Architecture**: `adr/` → Design decisions and rationale  
- **Process**: `sdk-users/workflows/` → Development and deployment workflows
- **Templates**: `sdk-users/templates/` → Ready-to-use solution starting points
- **Migration**: `migrations/templates/` → Legacy project conversion guides

## 🔄 Learning Loop
Implementation → Mistakes → Analysis → Documentation → Better Solutions

## Project-Specific Instructions

<!-- Add your project-specific Claude Code instructions here -->
<!-- IMPORTANT: Template updates replace this entire file. When merging template updates, -->
<!-- manually merge your project-specific instructions from this section into the new CLAUDE.md -->