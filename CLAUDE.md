# Kailash SDK - Development Guide

## 🚀 ESSENTIAL PATTERNS - COPY THESE FIRST

### Basic Workflow (Required Foundation)
```python
from kailash.workflow.builder import WorkflowBuilder
from kailash.runtime.local import LocalRuntime

workflow = WorkflowBuilder()
workflow.add_node("LLMAgentNode", "agent", {"model": "gpt-4"})  # All classes end with "Node"
runtime = LocalRuntime()
results, run_id = runtime.execute(workflow.build())  # runtime executes workflow
```

### ❌ NEVER
- `workflow.execute(runtime)` → Use `runtime.execute(workflow)`
- `workflow.addNode()` → Use `workflow.add_node()`
- `inputs={}` → Use `parameters={}`
- String code in PythonCodeNode → Use `.from_function()` (step 4)

### 🎯 Multi-Step Strategy (Enterprise Workflow)
1. **First implementation** → Copy basic pattern above
2. **Architecture decisions** → [sdk-users/decision-matrix.md](sdk-users/decision-matrix.md)
3. **Node selection** → [sdk-users/nodes/node-selection-guide.md](sdk-users/nodes/node-selection-guide.md)
4. **Security & access control** → [sdk-users/enterprise/security-patterns.md](sdk-users/enterprise/security-patterns.md) (User management, RBAC, auth)
5. **Enterprise integration** → [sdk-users/enterprise/gateway-patterns.md](sdk-users/enterprise/gateway-patterns.md) (API gateways, external systems)
6. **Custom logic** → [sdk-users/cheatsheet/031-pythoncode-best-practices.md](sdk-users/cheatsheet/031-pythoncode-best-practices.md) (Use `.from_function()`)
7. **Custom nodes** → [sdk-users/developer/05-custom-development.md](sdk-users/developer/05-custom-development.md)
8. **Production deployment** → [sdk-users/enterprise/production-patterns.md](sdk-users/enterprise/production-patterns.md) (Scaling, monitoring)
9. **Governance & compliance** → [sdk-users/enterprise/compliance-patterns.md](sdk-users/enterprise/compliance-patterns.md) (Audit, data policies)
10. **Common errors** → [sdk-users/validation/common-mistakes.md](sdk-users/validation/common-mistakes.md)

---

## When asked to implement a solution
1. Use 100% kailash sdk components (latest on pypi) and consult sdk-users/ every time.
   - Do not create new code without checking it against the existing SDK components.
   - Do not assume any new functionality without verifying it against the frontend specifications.
   - If you meet any errors in the SDK, check sdk-users/ because we would have resolved it already.
2. Always test your implementation thoroughly until they pass!
   - Use 100% kailash SDK components, and that you have consulted sdk-users/ for any doubts.
   - This is a live production migration so do not use any mocks.
     - The use of simplified examples or tests is allowed for your learning, and must be re-implemented into your original design.

## 📁 Quick Access
| **Project Development** | **SDK Users** |
|-------------------------|---------------|
| [guides/developer/](guides/developer/) | [sdk-users/](sdk-users/) |
| [guides/developer/getting-started.md](guides/developer/getting-started.md) | [sdk-users/nodes/node-selection-guide.md](sdk-users/nodes/node-selection-guide.md) |
| [guides/developer/architecture-overview.md](guides/developer/architecture-overview.md) | [sdk-users/cheatsheet/](sdk-users/cheatsheet/) |

## 📁 Complete Documentation
**Full SDK Reference**: [sdk-users/](sdk-users/) - Comprehensive guides and patterns
