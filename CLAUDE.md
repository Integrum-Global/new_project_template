# Kailash Studio - Development Guide

## When asked to implement a solution
1. Use 100% kailash sdk components (v 0.4.0) and consult sdk-users/ every time.
   - Do not create new code without checking it against the existing SDK components.
   - Do not assume any new functionality without verifying it against the frontend specifications.
   - If you meet any errors in the SDK, check sdk-users/ because we would have resolved it already. 
   - extensive testing on your implementation.
2. Always test your implementation thoroughly until they pass!
   - Use 100% kailash SDK components, and that you have consulted sdk-users/ for any doubts.
   - This is a live production migration so do not use any mocks.
     - The use of simplified examples or tests is allowed for your learning, and must be re-implemented into your original design.

## 📁 Quick Access
| **SDK Users** | **SDK Contributors** | **Shared** |
|---------------|---------------------|-----------|
| [sdk-users/](sdk-users/) | [sdk-contributors/architecture/](sdk-contributors/architecture/) | [shared/mistakes/](shared/mistakes/) |
| [sdk-users/nodes/node-selection-guide.md](sdk-users/nodes/node-selection-guide.md) | [sdk-contributors/training/](sdk-contributors/training/) | [tests/](tests/) |
| [sdk-users/cheatsheet/](sdk-users/cheatsheet/) | [sdk-contributors/research/](sdk-contributors/research/) | [examples/](examples/) |

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

## ⚡ Critical Patterns
1. **Data Paths**: `get_input_data_path()`, `get_output_data_path()`
2. **Access Control**: `AccessControlManager(strategy="rbac"|"abac"|"hybrid")`
3. **Execution**: Use `.execute()` not `.process()` or `.call()`
4. **Ollama Embeddings**: Extract with `[emb["embedding"] for emb in result["embeddings"]]`
5. **Cyclic Workflows**: Preserve state with `set_cycle_state()`, explicit parameter mapping
6. **WorkflowBuilder**: String-based `add_node("CSVReaderNode", ...)`, 4-param `add_connection()`

## 🔧 Core Nodes (110+ available)
**Choose Smart**: [Node Selection Guide](sdk-users/nodes/node-selection-guide.md) - Decision trees + quick finder
**AI**: LLMAgentNode, MonitoredLLMAgentNode, EmbeddingGeneratorNode, A2AAgentNode, SelfOrganizingAgentNode
**Data**: CSVReaderNode, JSONReaderNode, SQLDatabaseNode, AsyncSQLDatabaseNode, DirectoryReaderNode
**RAG**: 47+ specialized nodes - see [RAG Guide](sdk-users/developer/07-comprehensive-rag-guide.md)
**API**: HTTPRequestNode, RESTClientNode, OAuth2Node, GraphQLClientNode
**Logic**: SwitchNode, MergeNode, WorkflowNode, ConvergenceCheckerNode
**Enterprise**: MultiFactorAuthNode, ThreatDetectionNode, AccessControlManager, GDPRComplianceNode
**Full catalog**: [Complete Node Catalog](sdk-users/nodes/comprehensive-node-catalog.md)

## 🔗 Quick Links by Need

| **I need to...** | **SDK User** | **SDK Contributor** |
|-------------------|--------------|---------------------|
| **Build a workflow** | [sdk-users/workflows/](sdk-users/workflows/) | - |
| **Make arch decisions** | [sdk-users/decision-matrix.md](sdk-users/decision-matrix.md) | [Architecture ADRs](sdk-contributors/architecture/adr/) |
| **Fix an error** | [sdk-users/developer/05-troubleshooting.md](sdk-users/developer/05-troubleshooting.md) | [shared/mistakes/](shared/mistakes/) |
| **Find patterns** | [sdk-users/patterns/](sdk-users/patterns/) | - |
| **Learn from workflows** | [sdk-users/workflows/](sdk-users/workflows/) - Production workflows | - |

## 🏗️ Architecture Decisions

**For app building guidance:** → [sdk-users/decision-matrix.md](sdk-users/decision-matrix.md)

**Before any app implementation:**
1. Enter `sdk-users/` directory to load full architectural guidance
2. Check decision matrix for patterns and trade-offs
3. Reference complete app guide as needed

## 🎯 Quick Start Guide

**Building Apps/Workflows:**
- **Start**: [sdk-users/](sdk-users/) - Complete solution guide with decision matrix
- **Node Selection**: [Node Selection Guide](sdk-users/nodes/node-selection-guide.md) - Smart finder
- **Quick Patterns**: [Cheatsheet](sdk-users/cheatsheet/) - 37 copy-paste patterns
- **Enterprise**: [Enterprise Patterns](sdk-users/enterprise/) - Advanced features

**Need Help:**
- **Errors**: [Troubleshooting](sdk-users/developer/05-troubleshooting.md)
- **Common Mistakes**: [sdk-users/validation/common-mistakes.md](sdk-users/validation/common-mistakes.md)

