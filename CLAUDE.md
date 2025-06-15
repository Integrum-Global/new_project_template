# Client Project Development with Kailash SDK

This template helps you build enterprise applications using the [Kailash Python SDK](https://pypi.org/project/kailash/) with isolated project management and cross-app orchestration.

## 📁 Quick Directory Access

| **Purpose** | **Location** | **Description** |
|-------------|--------------|-----------------|
| **Build Apps** | [apps/](apps/) | Self-contained client applications |
| **Cross-App Coordination** | [solutions/](solutions/) | Tenant-level orchestration |
| **SDK Guidance** | [sdk-users/](sdk-users/) | Curated SDK documentation |
| **Infrastructure** | [infrastructure/](infrastructure/) | Deployment & DevOps |
| **Project Data** | [data/](data/) | Inputs, outputs, configurations |

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
 
### App Development (`apps/`)
```
apps/
├── _template/             # Template for new client apps
│   ├── adr/               # App-specific architecture decisions
│   ├── todos/             # App-specific task tracking
│   ├── mistakes/          # App-specific learning
│   ├── core/              # Business logic
│   ├── workflows/         # Kailash SDK workflows
│   └── tests/             # Comprehensive testing
├── user_management/       # Example: Enterprise user management
├── analytics/             # Example: Data analytics
└── document_processor/    # Example: Document processing
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

### Isolated Project Management
- ✅ **Each app has isolated** `adr/`, `todos/`, `mistakes/` folders
- ✅ **Solutions level has isolated** project management for cross-app work
- ✅ **No shared files** that multiple teams modify
- ✅ **Clear ownership** boundaries between apps and solutions

### Multi-Developer Workflow
```bash
# Team A works on user management
cd apps/user_management
echo "- [ ] Add password reset" >> todos/000-master.md

# Team B works on analytics (no conflicts!)
cd apps/analytics  
echo "- [ ] Add real-time dashboard" >> todos/000-master.md

# Solutions architect coordinates cross-app work
cd solutions
echo "- [ ] Integrate user events with analytics" >> todos/000-master.md
```

## 🔧 Quick Node Reference
**AI**: LLMAgentNode, MonitoredLLMAgentNode, EmbeddingGeneratorNode, A2AAgentNode, MCPAgentNode
**Data**: CSVReaderNode, JSONReaderNode, SQLDatabaseNode, AsyncSQLDatabaseNode, DirectoryReaderNode
**API**: HTTPRequestNode, RESTClientNode, OAuth2Node, GraphQLClientNode
**Logic**: SwitchNode, MergeNode, WorkflowNode, ConvergenceCheckerNode
**Transform**: FilterNode, DataTransformer, HierarchicalChunkerNode
**Security**: CredentialManagerNode, AccessControlManager, AuditLogNode
**Full catalog**: [sdk-users/nodes/comprehensive-node-catalog.md](sdk-users/nodes/comprehensive-node-catalog.md)

## 🚀 Development Workflow

### 1. Creating New Apps
```bash
# Copy the template
cp -r apps/_template apps/my_new_app
cd apps/my_new_app

# Customize
# Edit setup.py, config.py, README.md

# Start isolated project management
echo "# Initial App Architecture" > adr/001-setup.md
echo "- [ ] Define core models" > todos/000-master.md
```

### 2. Building with SDK
```python
from kailash.nodes.data import CSVReaderNode
from kailash.nodes.ai import LLMAgentNode
from kailash.workflow import Workflow
from kailash.runtime import LocalRuntime

class MyAppWorkflow(Workflow):
    def __init__(self):
        super().__init__("my_app_workflow")
        
        # Use SDK nodes
        self.data_reader = CSVReaderNode(name="reader")
        self.ai_processor = LLMAgentNode(name="processor")
        
        # Connect workflow
        self.add_edge(self.data_reader, self.ai_processor)
    
    def execute(self, inputs):
        runtime = LocalRuntime(enable_async=True)
        return runtime.execute(self, inputs)
```

### 3. Cross-App Coordination
```python
# In solutions/tenant_orchestration/
from apps.user_management.workflows import CreateUserWorkflow
from apps.analytics.workflows import TrackUserWorkflow

def complete_user_onboarding(user_data):
    # Coordinate across multiple apps
    user = CreateUserWorkflow().execute(user_data)
    TrackUserWorkflow().execute({"user_id": user.id})
    return user
```

## 📚 Key Documentation

| **Need** | **File** | **Purpose** |
|----------|----------|-------------|
| **Start Building** | [apps/APP_DEVELOPMENT_GUIDE.md](apps/APP_DEVELOPMENT_GUIDE.md) | Complete app development guide |
| **Cross-App Work** | [solutions/README.md](solutions/README.md) | Multi-app coordination patterns |
| **SDK Usage** | [sdk-users/developer/QUICK_REFERENCE.md](sdk-users/developer/QUICK_REFERENCE.md) | SDK patterns and examples |
| **Node Catalog** | [sdk-users/nodes/comprehensive-node-catalog.md](sdk-users/nodes/comprehensive-node-catalog.md) | All available SDK nodes |
| **Troubleshooting** | [sdk-users/developer/07-troubleshooting.md](sdk-users/developer/07-troubleshooting.md) | Common issues and solutions |

## 🎯 Primary Development Tasks

### Every Development Session:
1. **Check app todos**: `cat apps/my_app/todos/000-master.md`
2. **Update task status**: Mark `[~]` when starting, `[x]` when completing
3. **Document decisions**: Add to `apps/my_app/adr/` for app-specific choices
4. **Track learnings**: Add to `apps/my_app/mistakes/` when you solve issues

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