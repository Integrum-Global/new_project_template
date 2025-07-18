# Kailash SDK Project Template

## ⚡ Quick Start

### Installation
```bash
# Core SDK only
pip install kailash

# With app frameworks
pip install kailash[dataflow,nexus]  # Database + multi-channel
pip install kailash[all]             # Everything
```

## 🚀 ESSENTIAL PATTERNS - COPY THESE FIRST

### Basic Workflow
```python
from kailash.workflow.builder import WorkflowBuilder
from kailash.runtime.local import LocalRuntime

workflow = WorkflowBuilder()
workflow.add_node("LLMAgentNode", "agent", {"model": "gpt-4"})
runtime = LocalRuntime()
results, run_id = runtime.execute(workflow.build())
```

### Cyclic Workflows (v0.6.6+) - CycleBuilder API
```python
from kailash.workflow.builder import WorkflowBuilder
from kailash.runtime.local import LocalRuntime

workflow = WorkflowBuilder()
workflow.add_node("DataProcessorNode", "processor", {"threshold": 0.9})
workflow.add_node("QualityEvaluatorNode", "evaluator", {"target_quality": 0.95})

# Create cycle using CycleBuilder API (NOT deprecated cycle=True)
cycle_builder = workflow.create_cycle("quality_improvement")
cycle_builder.connect("processor", "evaluator", mapping={"result": "input_data"}) \
             .connect("evaluator", "processor", mapping={"feedback": "adjustment"}) \
             .max_iterations(50) \
             .converge_when("quality > 0.95") \
             .timeout(300) \
             .build()

runtime = LocalRuntime()
results, run_id = runtime.execute(workflow.build())  # Real cyclic execution
```

### ❌ NEVER
- `workflow.execute(runtime)` → Use `runtime.execute(workflow)`
- `workflow.addNode()` → Use `workflow.add_node()`
- `inputs={}` → Use `parameters={}`
- String code in PythonCodeNode → Use `.from_function()`
- `workflow.connect(..., cycle=True)` → Use `workflow.create_cycle("name").connect(...).build()`
- Override `execute()` in nodes → Implement `run()` instead
- Use `operation` parameter → Use `action` for consistency

### 🎯 Multi-Step Strategy (Enterprise Workflow)
1. **First implementation** → Copy basic pattern above
2. **Architecture decisions** → [sdk-users/decision-matrix.md](sdk-users/decision-matrix.md)
3. **Node selection** → [sdk-users/nodes/node-selection-guide.md](sdk-users/nodes/node-selection-guide.md)
4. **AI Agents with MCP** → Use `use_real_mcp=True` (default) for real tool execution
5. **Multi-channel apps** → [sdk-users/enterprise/nexus-patterns.md](sdk-users/enterprise/nexus-patterns.md) (API, CLI, MCP unified)
6. **Security & access control** → [sdk-users/enterprise/security-patterns.md](sdk-users/enterprise/security-patterns.md) (User management, RBAC, auth)
7. **Enterprise integration** → [sdk-users/enterprise/gateway-patterns.md](sdk-users/enterprise/gateway-patterns.md) (API gateways, external systems)
8. **Custom logic** → [sdk-users/cheatsheet/031-pythoncode-best-practices.md](sdk-users/cheatsheet/031-pythoncode-best-practices.md) (Use `.from_function()`)
9. **Custom nodes** → [sdk-users/developer/05-custom-development.md](sdk-users/developer/05-custom-development.md)
10. **Production deployment** → [sdk-users/enterprise/production-patterns.md](sdk-users/enterprise/production-patterns.md) (Scaling, monitoring)
11. **Enterprise resilience** → [sdk-users/enterprise/resilience-patterns.md](sdk-users/enterprise/resilience-patterns.md) (Circuit breaker, bulkhead, health monitoring)
12. **Distributed transactions** → [sdk-users/cheatsheet/049-distributed-transactions.md](sdk-users/cheatsheet/049-distributed-transactions.md) (Saga, 2PC, automatic pattern selection)
13. **Governance & compliance** → [sdk-users/enterprise/compliance-patterns.md](sdk-users/enterprise/compliance-patterns.md) (Audit, data policies)
14. **Common errors** → [sdk-users/validation/common-mistakes.md](sdk-users/validation/common-mistakes.md)

---

## 🏗️ Core SDK vs App Framework Architecture

### Core SDK Components (kailash)
The **Core SDK** provides foundational workflow building blocks:
- **Runtime System**: `LocalRuntime`, `ParallelRuntime` - Execute workflows
- **Workflow Builder**: `WorkflowBuilder` - Create workflows programmatically
- **Node Library**: 110+ production-ready nodes
- **MCP Integration**: Complete Model Context Protocol support

### App Frameworks (via PyPI)
Production-ready applications you can install:
- **kailash-dataflow**: Zero-config database with MongoDB-style queries
- **kailash-nexus**: Multi-channel platform (API, CLI, MCP from single codebase)

### DataFlow Quick Start
```python
from dataflow import DataFlow
from kailash.workflow.builder import WorkflowBuilder
from kailash.runtime.local import LocalRuntime

db = DataFlow()

@db.model
class User:
    name: str
    age: int

# Use generated nodes in workflows
workflow = WorkflowBuilder()
workflow.add_node("UserCreateNode", "create", {"name": "Alice", "age": 25})
workflow.add_node("UserListNode", "list", {"filter": {"age": {"$gt": 18}}})

runtime = LocalRuntime()
results, run_id = runtime.execute(workflow.build())
```

### Nexus Quick Start
```python
from nexus import Nexus
from kailash.workflow.builder import WorkflowBuilder

app = Nexus()

# Create and register workflow
workflow = WorkflowBuilder()
workflow.add_node("PythonCodeNode", "process", {
    "code": "result = {'result': sum(parameters.get('data', []))}"
})
app.register("process_data", workflow)

app.start()  # Available as API, CLI, and MCP
```

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
1. **🚨 Node Execution**: ALWAYS use `.execute()` - NEVER `.run()`, `.process()`, or `.call()`
2. **SDK-First Development**: Use SDK components, NO custom orchestration
3. **Real Solutions Only**: Never simplify examples or use mock data
4. **Node Development Rules**: Names end with "Node", set attributes BEFORE `super().__init__()`
5. **PythonCodeNode Patterns**: Use `.from_function()` for multi-line code
6. **Middleware**: Use `create_gateway()` for production apps
7. **Git Safety**: NEVER destroy uncommitted work
    - ❌ **FORBIDDEN**: `git reset --hard`, `git clean -fd`, `rm -rf` on code
    - ✅ **REQUIRED**: `git add . && git commit -m "WIP"` before risky operations
    - ✅ Use `git stash` instead of destructive resets
    - 🚨 **ASK PERMISSION** before any potentially destructive git command

## ⚡ Critical Patterns
1. **Data Paths**: `get_input_data_path()`, `get_output_data_path()`
2. **Access Control**: `AccessControlManager(strategy="rbac"|"abac"|"hybrid")`
3. **Execution Pattern - CRITICAL**:
   - **Users call**: `node.execute(**params)` - Public API with validation
   - **Nodes implement**: `def run(self, **kwargs)` - Protected method with actual logic
   - **Never override**: `execute()` in custom nodes - breaks validation chain
4. **Ollama Embeddings**: Extract with `[emb["embedding"] for emb in result["embeddings"]]`
5. **Cyclic Workflows**: Use CycleBuilder API `workflow.create_cycle("name").connect(...).max_iterations(N).build()`
6. **WorkflowBuilder**: String-based `add_node("CSVReaderNode", ...)`, 4-param `add_connection()`
7. **MCP Integration**: 100% validated, comprehensive testing (407 tests, 100% pass rate) - see [MCP Guide](sdk-users/cheatsheet/025-mcp-integration.md)
8. **MCP Real Execution**: All AI agents use `use_real_mcp=True` by default (v0.6.6+) - BREAKING CHANGE from mock execution
9. **Documentation**: Comprehensive validation across 9 critical phases, 100% pass rates achieved - see [SDK Users](sdk-users/) navigation hub
10. **Enterprise Resilience**: Circuit breaker, bulkhead isolation, health monitoring - see [Resilience Patterns](sdk-users/enterprise/resilience-patterns.md)
11. **Transaction Monitoring**: 5 production-tested nodes for metrics, deadlock detection, race conditions - see [Transaction Monitoring](sdk-users/cheatsheet/048-transaction-monitoring.md)
12. **Distributed Transactions**: Automatic pattern selection (Saga/2PC), compensation logic, recovery - see [Distributed Transactions](sdk-users/cheatsheet/049-distributed-transactions.md)
13. **AsyncSQL Parameter Types**: PostgreSQL type inference fix with `parameter_types` for JSONB/COALESCE contexts (v0.6.6+) - see [AsyncSQL Patterns](sdk-users/cheatsheet/047-asyncsql-enterprise-patterns.md)
14. **Core SDK Architecture**: TODO-111 resolved critical infrastructure gaps - CyclicWorkflowExecutor, WorkflowVisualizer, and ConnectionManager now production-ready with comprehensive test coverage
15. **Parameter Naming Convention**: Use `action` (not `operation`) for consistency across nodes
16. **Test Performance**: Run unit tests directly for 11x faster execution: `pytest tests/unit/`

## 🔧 Core Nodes (110+ available)
**Quick Access**: [Node Index](sdk-users/nodes/node-index.md) - Minimal reference (47 lines)
**Choose Smart**: [Node Selection Guide](sdk-users/nodes/node-selection-guide.md) - Decision trees + quick finder
**AI**: **LLMAgentNode**, **IterativeLLMAgentNode** (real MCP execution by default), MonitoredLLMAgentNode, EmbeddingGeneratorNode, A2AAgentNode, SelfOrganizingAgentNode
**Data**: CSVReaderNode, JSONReaderNode, SQLDatabaseNode, AsyncSQLDatabaseNode, DirectoryReaderNode
**RAG**: 47+ specialized nodes - see [RAG Guide](sdk-users/developer/06-comprehensive-rag-guide.md)
**API**: HTTPRequestNode, RESTClientNode, OAuth2Node, GraphQLClientNode
**Logic**: SwitchNode, MergeNode, WorkflowNode, ConvergenceCheckerNode
**Enterprise**: MultiFactorAuthNode, ThreatDetectionNode, AccessControlManager, GDPRComplianceNode
**Monitoring**: TransactionMetricsNode, TransactionMonitorNode, DeadlockDetectorNode, RaceConditionDetectorNode, PerformanceAnomalyNode - see [Monitoring Guide](sdk-users/nodes/monitoring-nodes.md)
**Transactions**: DistributedTransactionManagerNode, SagaCoordinatorNode, TwoPhaseCommitCoordinatorNode - see [Transaction Guide](sdk-users/nodes/transaction-nodes.md)
**Full catalog**: [Complete Node Catalog](sdk-users/nodes/comprehensive-node-catalog.md) (2194 lines - use sparingly)

## 📂 Directory Navigation Convention
**File Naming Standard**:
- **README.md** = Directory index/navigation (what's here, where to go)
- **QUICK_REFERENCE.md** = Hands-on implementation guide (code patterns, quick fixes)
- **Numbered guides** = Detailed topic-specific documentation

## 📁 Complete Documentation
**Full SDK Reference**: [sdk-users/](sdk-users/) - Comprehensive guides and patterns


## 🏗️ Architecture Decisions

**For app building guidance:** → [sdk-users/decision-matrix.md](sdk-users/decision-matrix.md)

**Before any app implementation:**
1. Enter `sdk-users/` directory to load full architectural guidance
2. Check decision matrix for patterns and trade-offs
3. Reference complete app guide as needed

## 🔗 Quick Links by Need

| **I need to...** | **Core SDK** | **App Framework** |
|-----------------|--------------|---------------------|
| **Build a workflow** | [sdk-users/workflows/](sdk-users/workflows/) | - |
| **Build an app** | [sdk-users/decision-matrix.md](sdk-users/decision-matrix.md) | [sdk-users/apps/](sdk-users/apps/) |
| **Database operations** | [sdk-users/cheatsheet/047-asyncsql-enterprise-patterns.md](sdk-users/cheatsheet/047-asyncsql-enterprise-patterns.md) | [sdk-users/apps/dataflow/](sdk-users/apps/dataflow/) - Zero-config |
| **Multi-channel platform** | [sdk-users/enterprise/nexus-patterns.md](sdk-users/enterprise/nexus-patterns.md) | [sdk-users/apps/nexus/](sdk-users/apps/nexus/) - Production-ready |
| **MCP integration** | [sdk-users/cheatsheet/025-mcp-integration.md](sdk-users/cheatsheet/025-mcp-integration.md) | - |
| **AI & RAG** | [sdk-users/developer/06-comprehensive-rag-guide.md](sdk-users/developer/06-comprehensive-rag-guide.md) | - |
| **User management** | [sdk-users/enterprise/security-patterns.md](sdk-users/enterprise/security-patterns.md) | - |
| **Fix an error** | [sdk-users/developer/05-troubleshooting.md](sdk-users/developer/05-troubleshooting.md) | - |
| **Distributed transactions** | [sdk-users/cheatsheet/049-distributed-transactions.md](sdk-users/cheatsheet/049-distributed-transactions.md) | - |
| **Run tests**   | See Testing Requirements section below | - |

## 🧪 CRITICAL: Testing Requirements
- **Test Guide**: [tests/README.md](tests/README.md) - 3-tier testing strategy

### 1. Fast Unit Tests
**Run unit tests directly**: `pytest tests/unit/ --timeout=1 --tb=short`
- 11x faster execution without process forking overhead
- Proper test isolation through fixtures
- 99.96% pass rate with optimized state management
- Tests requiring isolation (< 1%) are automatically handled with `@pytest.mark.requires_isolation`

### 2. Timeout Enforcement
**ALWAYS enforce timeout limits**:
- **Unit tests**: 1 second max (`--timeout=1`)
- **Integration tests**: 5 seconds max (`--timeout=5`)
- **E2E tests**: 10 seconds max (`--timeout=10`)

### 3. Fix Timeout Violations
When tests exceed timeout:
1. Check for `asyncio.sleep(10)` → change to `asyncio.sleep(0.1)`
2. Check actor/pool cleanup → add proper task cancellation
3. Check database configs → use `health_check_interval=0.1`
4. Mock slow services instead of real calls
5. Use smaller test datasets
6. Add proper cleanup in finally blocks
---

# important-instruction-reminders
Do what has been asked; nothing more, nothing less.
NEVER create files unless they're absolutely necessary for achieving your goal.
ALWAYS prefer editing an existing file to creating a new one.
NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.