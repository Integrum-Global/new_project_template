# Client Project Development with Kailash SDK

This template helps you build enterprise applications using the [Kailash Python SDK](https://pypi.org/project/kailash/) with isolated project management and cross-app orchestration.

## 📁 Quick Directory Access

| **Purpose**                | **Location**               | **Description** |
|----------------------------|----------------------------|-----------------|
| **Build Apps**             | [apps/](apps/)             | Self-contained client applications |
| **Cross-App Coordination** | [solutions/](solutions/)   | Tenant-level orchestration |
| **SDK Guidance**           | [sdk-users/](sdk-users/)   | Curated SDK documentation |
| **Deployment**             | [deployment/](deployment/) | Deployment & DevOps |
| **Project Data**           | [data/](data/)             | Inputs, outputs, configurations |

## ⚠️ MUST FOLLOW - Kailash SDK Best Practices

### 1. **Use SDK Components, Workflows & Runtime - NO Custom Orchestration**
- ✅ Async by default (nodes, workflows, runtime)
- ✅ Always check the catalog for specialized nodes before using PythonCodeNode
- ❌ Manual workflow orchestration or custom execution logic
- ✅ Use `WorkflowBuilder.from_dict()` for dynamic workflows
- ✅ Use class-based workflows for reusable patterns across multiple services (inheritance, templates)
- ✅ Delegate ALL execution to SDK runtime (`LocalRuntime`/`AsyncLocalRuntime`)
- ✅ Use `TaskManager` for execution tracking
- ✅ Use SDK nodes for ALL operations - the SDK has a node for almost everything!
- ⚠️ The SDK is comprehensive - if you're writing custom code, you're probably doing it wrong!
- ❌ Don't work around SDK limitations - stop, analyze, and recommend core SDK improvements instead
- 🚨 **NEVER manually implement database models, sessions, or repositories** - use `from kailash.middleware.database import BaseWorkflowModel, DatabaseManager`
- 🚨 **NEVER create custom FastAPI apps** - use `from kailash.middleware import create_gateway()` which returns a complete enterprise app

### 2. **NEVER Use Simpler Examples or Mock Data**: Always implement real, comprehensive solutions
- ❌ Creating simpler versions to pass tests or avoid complexity
- ❌ Using mock data, processes, or responses to make failing examples pass
- ✅ Fix the original complex examples to work correctly, even if the error is not in the current scope
- ✅ Simple examples created for understanding must be deleted after fixing the original
- ⚠️ Real data, real processes, real complexity - no shortcuts!

### 3. **Unified Runtime**: LocalRuntime now includes Async + ALL enterprise capabilities
- ✅ Use `LocalRuntime` for all workflow execution (100% backward compatible)
- ✅ Available parameters:
    - `debug: bool = False` → Enable debug logging
    - `enable_cycles: bool = True` → Support cyclic workflows
    - `enable_async: bool = True` → Auto-detect and run async nodes
    - `max_concurrency: int = 10` → Maximum parallel operations
    - `user_context: Optional[UserContext] = None` → User/tenant isolation
    - `enable_monitoring: bool = True` → Automatic performance tracking
    - `enable_security: bool = False` → Access control enforcement
    - `enable_audit: bool = False` → Compliance audit logging
    - `resource_limits: Optional[dict] = None` → Resource constraints (memory_mb, cpu_cores, timeout_seconds)
- ⚠️ `AsyncLocalRuntime()` is ONLY a compatibility wrapper - use `LocalRuntime(enable_async=True)` instead

### 4. **Enterprise Middleware Integration**: Use enterprise middleware for production apps
- ✅ `from kailash.middleware import AgentUIMiddleware, APIGateway` → Production-ready stack
- ✅ Dynamic workflows: `WorkflowBuilder.from_dict()` with automatic parameter mapping
- ✅ Real-time communication: `RealtimeMiddleware` with WebSocket/SSE support
- ✅ Session management: Multi-tenant isolation with automatic cleanup

### 5. **Node Development Rules**: Core requirements for all node creation
- ✅ **Node names**: ALL end with "Node" (`CSVReaderNode` ✓, `CSVReader` ✗)
- ✅ **Node attributes**: MUST set attributes BEFORE `super().__init__()`
    - ❌ `super().__init__(name)` then `self.attr = value` → AttributeError
    - ✅ `self.attr = value` then `super().__init__(name)` → Correct order
- ✅ **get_parameters()**: MUST return `Dict[str, NodeParameter]`
    - ❌ `return {"param": self.param_value}` → Validation error
    - ✅ `return {"param": NodeParameter(name="param", type=int, ...)}`

### 6. **PythonCodeNode + Mapping**: Output wrapping and connection patterns
- ✅ **Result wrapping**: `{"result": {"data": processed}}` or `{"result": 42}`
- ❌ Direct returns without "result" wrapper
- ✅ **Dot notation**: Access nested data with `"result.data"`, `"result.metrics"` 
- ✅ **Connections**: `mapping={"result": "next_param"}` or `{"result.data": "next_param"}`
- ✅ **Multi-line code**: Use `.from_function()` for complex logic
- ❌ Inline strings using `code=...` for complex logic

### 7. **Auto-Mapping Parameters**: Automatic connection discovery
- ✅ **auto_map_primary=True** → Automatically maps primary input
- ✅ **auto_map_from=["alt1", "alt2"]** → Maps from alternative parameter names
- ✅ **workflow_alias="alias_name"** → Maps from workflow-level parameter name
- ⚠️ Reduces need for explicit workflow connections

### 8. **Cyclic Workflows**: Preserve state and configuration across iterations
- ❌ **Parameters lost after first iteration**: `targets = kwargs.get("targets", {})`
- ✅ **Preserve state**: `if not targets and prev_state.get("targets"): targets = prev_state["targets"]`
- ✅ **Save in cycle state**: `**self.set_cycle_state({"targets": targets, "constraints": constraints})`
- ✅ **Use packager pattern for SwitchNode cycles**: see [developer guide](sdk-users/developer/09-cyclic-workflows-guide.md)
- ⚠️ Always explicitly map parameters in cycle connections
 
### App Development
```
apps/                      # Template-provided example apps (sync-replaced)
├── qa_agentic_testing/    # QA testing example
├── studio/                # Workflow studio example  
└── user_management/       # User management example

src/                       # Client project directory
├── new_project/           # Template project structure (sync-replaced)
└── your_project/          # Your project name (NEVER synced)
    ├── module1/           # First module
    ├── module2/           # Second module
    └── shared/            # Shared code between modules
```

### Cross-App Orchestration (`solutions/`)
```
solutions/
├── adr/                   # Solutions-level architecture decisions
├── todos/                 # Solutions-level task tracking
├── mistakes/              # Solutions-level learning
├── tenant_orchestration/  # Multi-app workflows
├── shared_services/       # Common services (auth, caching)
├── data_integration/      # Cross-app data flows
└── monitoring/            # System-wide monitoring
```

## 🚫 Conflict Prevention Strategy

### Clear Separation
- ✅ **Template apps in `apps/`** - Sync-replaced example apps from template
- ✅ **Template structure in `src/new_project/`** - Sync-replaced template
- ✅ **Client code in `src/your_project/`** - Never synced, fully owned by client
- ✅ **No merge conflicts** - Use a different name than "new_project" for your code
- ✅ **Clear boundaries** - Your code is safe with a unique project name

## 🔧 Core Nodes (110+ available)
**AI**: LLMAgentNode, MonitoredLLMAgentNode, EmbeddingGeneratorNode, A2AAgentNode, SelfOrganizingAgentNode
**Data**: CSVReaderNode, JSONReaderNode, SQLDatabaseNode, AsyncSQLDatabaseNode, DirectoryReaderNode
**RAG**: 47+ specialized nodes - see [comprehensive guide](sdk-users/developer/20-comprehensive-rag-guide.md)
**API**: HTTPRequestNode, RESTClientNode, OAuth2Node, GraphQLClientNode
**Logic**: SwitchNode, MergeNode, WorkflowNode, ConvergenceCheckerNode
**Auth/Security**: MultiFactorAuthNode, ThreatDetectionNode, AccessControlManager, GDPRComplianceNode
**Middleware**: AgentUIMiddleware, RealtimeMiddleware, APIGateway, AIChatMiddleware
**Full catalog**: [sdk-users/nodes/comprehensive-node-catalog.md](sdk-users/nodes/comprehensive-node-catalog.md)

## 📚 Key Documentation

| **Need** | **File** | **Purpose** |
|----------|----------|-------------|
| **Start Building** | Create your project in `src/your_project/` | Client code safe from sync |
| **Example Apps** | See `apps/` for qa_agentic_testing, studio, user_management | Reference implementations |
| **SDK Usage** | [sdk-users/developer/QUICK_REFERENCE.md](sdk-users/developer/QUICK_REFERENCE.md) | SDK patterns and examples |
| **Node Catalog** | [sdk-users/nodes/comprehensive-node-catalog.md](sdk-users/nodes/comprehensive-node-catalog.md) | All available SDK nodes |
| **Troubleshooting** | [sdk-users/developer/07-troubleshooting.md](sdk-users/developer/07-troubleshooting.md) | Common issues and solutions |

## 🎯 Primary Development Tasks

### Every Development Session:
1. **Start in src/**: `cd src/your_project/` - Your code is safe here
2. **Reference examples**: Check `apps/` for patterns from qa_agentic_testing, studio, user_management
3. **Use SDK docs**: Follow patterns in `sdk-users/developer/`
4. **Plan with todos**: Track tasks in your project's todos
5. **Implement**: Use node catalog, test thoroughly
6. **No sync worries**: Your `src/` code is never touched by template updates

### Multi-App Coordination:
1. **Solutions planning**: Use `solutions/todos/000-master.md` for cross-app work
2. **Architecture decisions**: Document in `solutions/adr/` for cross-app patterns
3. **Integration issues**: Track in `solutions/mistakes/` for cross-app learnings

## 💡 Best Practices

### App Development:
- **Start with template**: Always copy `apps/_template/` for new apps
- **Follow SDK patterns**: Check `sdk-users/` for proven approaches
- **Use specialized nodes**: Always check catalog before using PythonCodeNode
- **Test comprehensively**: Use the testing structure in `apps/_template/tests/`

### Cross-App Coordination:
- **Use solutions layer**: Don't directly couple apps together
- **Shared services**: Put common functionality in `solutions/shared_services/`
- **Data integration**: Use `solutions/data_integration/` for cross-app data flows
- **Monitor everything**: Use `solutions/monitoring/` for system-wide observability

### Conflict Prevention:
- **Isolated management**: Keep project management within app boundaries
- **Clear ownership**: Apps own their domain, solutions owns coordination
- **Regular sync**: Weekly standup for cross-app dependencies
- **Document everything**: Decisions, tasks, and learnings in appropriate folders

---

**Quick Start**: Read [README.md](README.md) → Copy [apps/_template/](apps/_template/) → Follow [apps/APP_DEVELOPMENT_GUIDE.md](apps/APP_DEVELOPMENT_GUIDE.md) → Build with Kailash SDK!