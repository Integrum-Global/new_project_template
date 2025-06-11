# Solution Development with Kailash SDK

## 📁 Quick Directory Access by Role

| **SDK Users** (Building with SDK) |
|-----------------------------------|
| [sdk-users/developer/](sdk-users/developer/) - Build from scratch |
| [sdk-users/workflows/](sdk-users/workflows/) - Production workflows |
| [sdk-users/essentials/](sdk-users/essentials/) - Quick patterns |
| | [examples/feature-tests/](examples/feature-tests/) - Feature validation |

## 🎯 Quick Navigation
- **Track project** → todos/, adr/, mistakes/ (project-specific)
- **Business logic** → src/solutions/ (your implementations)
- **Project vision** → prd/ (your requirements)
- **Migrate legacy** → migrations/ (convert existing projects)
- 
## ⚡ Critical Validation Rules
1. **Node Names**: ALL end with "Node" (`CSVReaderNode` ✓)
2. **PythonCodeNode**: Input variables EXCLUDED from outputs!
   - `mapping={"result": "input_data"}` ✓
   - `mapping={"result": "result"}` ✗
3. **Parameter types**: ONLY `str`, `int`, `float`, `bool`, `list`, `dict`, `Any`
4. **Node Creation**: Can create without required params (validated at execution)
5. **PythonCodeNode Best Practice**: ALWAYS use `.from_function()` for code > 3 lines!
   - ❌ `PythonCodeNode(name="x", code="...100 lines...")` → Inline strings = NO IDE support
   - ✅ `PythonCodeNode.from_function(name="x", func=my_func)` → Full IDE support
   - String code ONLY for: one-liners, dynamic generation, user input
6. **Enhanced MCP Server**: Production-ready features enabled by default
   - ✅ `from kailash.mcp import MCPServer` → Gets caching, metrics, config management
   - ✅ `@server.tool(cache_key="name", cache_ttl=600)` → Automatic caching with TTL
   - ✅ `@server.tool(format_response="markdown")` → LLM-friendly formatting

## 🔧 Core Node Quick Reference (80+ total)
**AI**: LLMAgentNode, EmbeddingGeneratorNode, A2AAgentNode, MCPAgentNode, SelfOrganizingAgentNode
**Data**: CSVReaderNode, JSONReaderNode, SQLDatabaseNode, SharePointGraphReader, DirectoryReaderNode
**API**: HTTPRequestNode, RESTClientNode, OAuth2Node, GraphQLClientNode
**Logic**: SwitchNode, MergeNode, WorkflowNode, ConvergenceCheckerNode
**Transform**: FilterNode, Map, DataTransformer, HierarchicalChunkerNode
**Code**: PythonCodeNode (use only when no specialized node exists)
**Full catalog**: sdk-users/nodes/comprehensive-node-catalog.md

## ⚠️ CRITICAL: DO NOT EDIT sdk-users/ DIRECTORY
**The entire `sdk-users/` directory is automatically synced from the template.**
- ❌ **DO NOT** add, edit, or modify ANY files in `sdk-users/`
- ❌ **DO NOT** create custom files or folders in `sdk-users/`
- ❌ **DO NOT** fix bugs or typos directly in `sdk-users/`
- ✅ **ALL changes will be LOST** during the next template sync
- ✅ **Report issues** to the template repository instead
- ✅ **Use `src/solutions/`** for your custom code and workflows

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
- **Create & start todos**: Add tasks → mark "in_progress" in `todos/` and write the details into `todos/active`

### **Phase 2: Implement → Example → Test**
- **Migration**: Follow `sdk-users/instructions/migration-workflow.md` for legacy conversion
- **Implement**: Use `sdk-users/essentials/` and `sdk-users/templates/` for patterns
- **Custom Nodes**: Follow `sdk-users/developer/` for node creation
- **Create Example**: MUST create working example and verify it runs
- **Validate**: Check `sdk-users/validation-guide.md` for correctness
- **Track mistakes**: Document issues in `mistakes/current-session-mistakes.md`
- **Test**: Validate with real data and scenarios

### **Phase 3: Document → Deploy → Learn**
- **Update todos**: Mark completed in `todos/`, update details from `todos/active` and move it to `todos/completed'
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

## 🏗️ Infrastructure Patterns

When developing with infrastructure services:
1. **Setup**: Use `infrastructure/scripts/` for environment management
2. **Patterns**: Reference `sdk-users/INFRASTRUCTURE_GUIDE.md` for best practices
3. **Examples**: See `sdk-users/workflows/by-pattern/infrastructure/` for patterns
4. **Configuration**: Keep configs in `infrastructure/` directory
5. **Security**: Never commit credentials or .env files

### Quick Infrastructure Commands
```bash
# Start services
./infrastructure/scripts/start-sdk-dev.sh

# Check status
./infrastructure/scripts/sdk-dev-status.sh

# Stop services
./infrastructure/scripts/stop-sdk-dev.sh
```

## Project-Specific Instructions

<!-- Add your project-specific Claude Code instructions here -->
<!-- IMPORTANT: Template updates replace this entire file. When merging template updates, -->
<!-- manually merge your project-specific instructions from this section into the new CLAUDE.md -->
