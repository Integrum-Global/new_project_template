# Kailash Studio - Development Guide

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

## ⚠️ MUST FOLLOW
1. **SDK-First Development**: Use SDK components, NO custom orchestration
    - ✅ Check [node selection guide](sdk-users/nodes/node-selection-guide.md) before PythonCodeNode
    - ✅ Use `LocalRuntime` (includes async + enterprise features)
    - ✅ Use `WorkflowBuilder.from_dict()` for dynamic workflows
    - 🚨 **NEVER** manual database/FastAPI - use `create_gateway()` from middleware

2. **Real Solutions Only**: Never simplify examples or use mock data
    - ✅ Fix complex examples, delete simple test versions
    - ❌ Mock data to make failing examples pass
    - ✅ Use built-in infrastructure: docker and ollama

3. **Node Development Rules**:
    - ✅ Names end with "Node" (`CSVReaderNode` ✓)
    - ✅ Set attributes BEFORE `super().__init__()`
    - ✅ `get_parameters()` returns `Dict[str, NodeParameter]`

4. **PythonCodeNode Patterns**:
    - ✅ Wrap outputs: `{"result": data}`
    - ✅ Use dot notation: `"result.data"` in connections
    - ✅ Use `.from_function()` for multi-line code

5. **Middleware**: Use `create_gateway()` for production apps
    - ✅ Real-time communication, AI chat, session management included

6. **Git Safety**: NEVER destroy uncommitted work
    - ❌ **FORBIDDEN**: `git reset --hard`, `git clean -fd`, `rm -rf` on code
    - ✅ **REQUIRED**: `git add . && git commit -m "WIP"` before risky operations
    - ✅ Use `git stash` instead of destructive resets
    - 🚨 **ASK PERMISSION** before any potentially destructive git command

## ⚡ Critical Patterns
1. **Data Paths**: `get_input_data_path()`, `get_output_data_path()`
2. **Access Control**: `AccessControlManager(strategy="rbac"|"abac"|"hybrid")`
3. **Execution**: Use `.execute()` not `.process()` or `.call()`
4. **Ollama Embeddings**: Extract with `[emb["embedding"] for emb in result["embeddings"]]`
5. **Cyclic Workflows**: Preserve state with `set_cycle_state()`, explicit parameter mapping
6. **WorkflowBuilder**: String-based `add_node("CSVReaderNode", ...)`, 4-param `add_connection()`

## 🔧 Core Nodes (110+ available)
**Quick Access**: [Node Index](sdk-users/nodes/node-index.md) - Minimal reference (47 lines)
**Choose Smart**: [Node Selection Guide](sdk-users/nodes/node-selection-guide.md) - Decision trees + quick finder
**AI**: LLMAgentNode, MonitoredLLMAgentNode, EmbeddingGeneratorNode, A2AAgentNode, SelfOrganizingAgentNode
**Data**: CSVReaderNode, JSONReaderNode, SQLDatabaseNode, AsyncSQLDatabaseNode, DirectoryReaderNode
**RAG**: 47+ specialized nodes - see [RAG Guide](sdk-users/developer/07-comprehensive-rag-guide.md)
**API**: HTTPRequestNode, RESTClientNode, OAuth2Node, GraphQLClientNode
**Logic**: SwitchNode, MergeNode, WorkflowNode, ConvergenceCheckerNode
**Enterprise**: MultiFactorAuthNode, ThreatDetectionNode, AccessControlManager, GDPRComplianceNode
**Full catalog**: [Complete Node Catalog](sdk-users/nodes/comprehensive-node-catalog.md) (2194 lines - use sparingly)

## 🔗 Quick Links by Need

| **I need to...** | **Project Guide** | **SDK Reference** |
|-------------------|-------------------|-------------------|
| **Set up project** | [Getting Started](guides/developer/getting-started.md) | - |
| **Understand architecture** | [Architecture Overview](guides/developer/architecture-overview.md) | [Decision Matrix](sdk-users/decision-matrix.md) |
| **Build a workflow** | [Multi-App Coordination](guides/developer/multi-app-coordination.md) | [SDK Workflows](sdk-users/workflows/) |
| **Fix an error** | [Project Troubleshooting](guides/developer/troubleshooting.md) | [SDK Troubleshooting](sdk-users/developer/05-troubleshooting.md) |
| **Find patterns** | [Team Workflows](guides/developer/team-workflows.md) | [SDK Patterns](sdk-users/patterns/) |
| **Deploy application** | [Deployment Guide](guides/developer/deployment-guide.md) | [Production Workflows](sdk-users/workflows/) |

## 🏗️ Architecture Decisions

**For project-specific guidance:** → [guides/developer/architecture-overview.md](guides/developer/architecture-overview.md)
**For SDK patterns and decisions:** → [sdk-users/decision-matrix.md](sdk-users/decision-matrix.md)

**Before any implementation:**
1. Check [Project Architecture Guide](guides/developer/architecture-overview.md) for project-specific patterns
2. Enter `sdk-users/` directory for SDK architectural guidance  
3. Check SDK decision matrix for patterns and trade-offs
4. Reference complete app guide as needed

## 🎯 Quick Start Guide

**New to This Project:**
- **Start Here**: [Project Getting Started](guides/developer/getting-started.md) - Complete project setup
- **Architecture**: [Project Architecture](guides/developer/architecture-overview.md) - Project design overview
- **Team Setup**: [Team Workflows](guides/developer/team-workflows.md) - Collaboration patterns

**Building Apps/Workflows:**
- **SDK Guide**: [sdk-users/](sdk-users/) - Complete SDK solution guide
- **Node Selection**: [Node Selection Guide](sdk-users/nodes/node-selection-guide.md) - Smart finder
- **Quick Patterns**: [Cheatsheet](sdk-users/cheatsheet/) - 37 copy-paste patterns
- **Enterprise**: [Enterprise Patterns](sdk-users/enterprise/) - Advanced features

**Need Help:**
- **Project Issues**: [Project Troubleshooting](guides/developer/troubleshooting.md)
- **SDK Errors**: [SDK Troubleshooting](sdk-users/developer/05-troubleshooting.md)
- **Common Mistakes**: [sdk-users/validation/common-mistakes.md](sdk-users/validation/common-mistakes.md)
