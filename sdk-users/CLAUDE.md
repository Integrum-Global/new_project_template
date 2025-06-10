# SDK Users - Quick Reference

*Building solutions WITH the Kailash SDK*

## 🎯 Quick Decision Guide
- **"Build from scratch"** → [developer/CLAUDE.md](developer/CLAUDE.md) - Node patterns, troubleshooting
- **"Lift working example"** → [workflows/README.md](workflows/README.md) - End-to-end use cases
- **"Quick pattern"** → [essentials/README.md](essentials/README.md) - Copy-paste snippets
- **"Which node?"** → [nodes/comprehensive-node-catalog.md](nodes/comprehensive-node-catalog.md) - Node selection guide

## 🚨 Critical Rules (Must Know)
1. **Node names**: ALL end with "Node" (`CSVReaderNode` ✓, `CSVReader` ✗)
2. **PythonCodeNode**: Input variables EXCLUDED from outputs!
   - `mapping={"result": "input_data"}` ✓
   - `mapping={"result": "result"}` ✗
3. **Always include name**: `PythonCodeNode(name="processor", code="...")`
4. **Parameter types**: ONLY `str`, `int`, `float`, `bool`, `list`, `dict`, `Any`
5. **Node Creation**: Can create without required params (validated at execution)
6. **Data Files**: Use centralized `/data/` with `examples/utils/data_paths.py`
7. **Output Files**: NEVER create `outputs/` directories!
   - ❌ `os.makedirs("outputs")` → ✅ `ensure_output_dir_exists()`
   - ❌ `"outputs/report.json"` → ✅ `get_output_data_path("category/report.json")`
   - All outputs → `/data/outputs/{category}/`

## 📁 Navigation Guide

### **Build from Scratch or Modify**
- **[developer/](developer/)** - Node creation, patterns, troubleshooting
  - Critical PythonCodeNode patterns
  - Directory reader best practices
  - Document processing workflows
  - Custom node development

### **Lift Working Examples**
- **[workflows/](workflows/)** - End-to-end use cases to copy
  - Quick-start patterns (30-second workflows)
  - Common patterns (data, API, AI)
  - Industry solutions (healthcare, finance)
  - Production-ready scripts

### **Quick Reference**
- **[essentials/](essentials/)** - Copy-paste patterns (streamlined cheatsheet)
- **[api/](api/)** - API documentation and signatures
- **[nodes/](nodes/)** - Complete node catalog with examples
- **[patterns/](patterns/)** - Architectural workflow patterns
- **[templates/](templates/)** - Boilerplate code templates

### **User Features**
- **[features/](features/)** - Feature guides and when to use them
- **[validation-guide.md](validation-guide.md)** - Critical rules to prevent errors

## ⚡ Quick Fix Templates

### Basic Workflow
```python
from kailash import Workflow
from kailash.nodes.data import CSVReaderNode
from kailash.runtime import LocalRuntime

workflow = Workflow("example", "Basic Example")
reader = CSVReaderNode(name="reader")
workflow.add_node("reader", reader)

runtime = LocalRuntime()
result = runtime.execute(workflow, parameters={
    "reader": {"file_path": "data.csv"}
})
```

### PythonCodeNode (Best Practices)
```python
# 🚀 BEST: Use .from_function() for code > 3 lines
def process_data(input_data: dict) -> dict:
    """Full IDE support!"""
    files = input_data.get("files", [])
    return {"processed": len(files)}

processor = PythonCodeNode.from_function(
    func=process_data,
    name="processor"
)

# ✅ String code only for: dynamic code, user input, simple one-liners
node = PythonCodeNode(name="calc", code="result = value * 1.1")  # OK

# ⚠️ Remember: Input variables EXCLUDED from outputs
workflow.connect("discovery", "processor", mapping={"result": "input_data"})
```

## 🔗 Quick Links by Task
| I need to... | Go to | Best for |
|--------------|-------|----------|
| **Fix an error** | [developer/07-troubleshooting.md](developer/07-troubleshooting.md) | Error lookup |
| **Copy working example** | [workflows/](workflows/) | Production patterns |
| **Quick code snippet** | [essentials/](essentials/) | Fast implementation |
| **Choose right node** | [nodes/comprehensive-node-catalog.md](nodes/comprehensive-node-catalog.md) | Node selection |
| **Learn architecture** | [patterns/](patterns/) | Design patterns |
| **API signature** | [api/](api/) | Method documentation |

## 🔴 Common Mistakes
1. **Forgetting node suffix**: `CSVReader` → `CSVReaderNode`
2. **Using generic types**: `List[str]` → `list`
3. **Mapping to same variable**: `{"result": "result"}` → `{"result": "input_data"}`
4. **Missing PythonCodeNode name**: `PythonCodeNode(code=...)` → `PythonCodeNode(name="x", code=...)`
5. **Manual file operations**: Use `DirectoryReaderNode` not `os.listdir`
6. **Hardcoded data paths**: `"examples/data/file.csv"` → Use `get_input_data_path("file.csv")`
7. **Old execution pattern**: `node.run()` → Use `node.execute()` for complete lifecycle

## 🤝 Team Assignments
If user asks about getting work or tasks, they should use Claude Code workflow system.
Guide them to `NEW_TEAM_MEMBER.md` at root level for onboarding.

---

**For SDK development**: See [../sdk-contributors/CLAUDE.md](../sdk-contributors/CLAUDE.md)
**New to team**: See [../NEW_TEAM_MEMBER.md](../NEW_TEAM_MEMBER.md)
**For shared resources**: See [../shared/](../shared/)
