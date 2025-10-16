# Important Directives 📜
1. Always use kailash SDK with its frameworks to implement.
2. Always use the specialist subagents (nexus-specialist, dataflow-specialist, mcp-specialist, kaizen-specialist) when working with the frameworks.
3. Never attempt to write codes from scratch before checking the frameworks with the specialist subagents. 
   - Instead of using direct SQL, SQLAlchemy, Django ORM, always check with the dataflow-specialist on how to do it with the dataflow framework
   - Instead of building your own API gateway or use FastAPI, always check with the nexus-specialist on how to do it with the nexus framework
   - Instead of building your own MCP server/client, always check with the mcp-specialist on how to do it with the mcp_server module inside the core SDK
   - Instead of building your own agentic platform, always check with the kaizen-specialist on how to do it with the kaizen framework

## 🏗️ Documentation

### Core SDK (`sdk-users/`)
**Foundational building blocks** for workflow automation:
- **Purpose**: Custom workflows, fine-grained control, integrations
- **Components**: WorkflowBuilder, LocalRuntime, 110+ nodes, MCP integration
- **Usage**: Direct workflow construction with full programmatic control
- **Install**: `pip install kailash`

### DataFlow (`sdk-users/apps/dataflow/`)
**Zero-config database framework** built on Core SDK:
- **Purpose**: Database operations with automatic model-to-node generation
- **Features**: @db.model decorator generates 9 nodes per model automatically. DataFlow IS NOT AN ORM!
- **Usage**: Database-first applications with enterprise features
- **Install**: `pip install kailash-dataflow`
- **Import**: `from dataflow import DataFlow`

### Nexus (`sdk-users/apps/nexus/`)
**Multi-channel platform** built on Core SDK:
- **Purpose**: Deploy workflows as API + CLI + MCP simultaneously
- **Features**: Unified sessions, zero-config platform deployment
- **Usage**: Platform applications requiring multiple access methods
- **Install**: `pip install kailash-nexus`
- **Import**: `from nexus import Nexus`

### Kaizen ('sdk-users/apps/kaizen/')
**AI agent framework** built on Core SDK:
- **Purpose**: Production-ready AI agents with multi-modal processing, multi-agent coordination, and enterprise features built on Kailash SDK
- **Features**: Signature-based programming, BaseAgent architecture, automatic optimization, error handling, audit trails
- **Usage**: Agentic applications requiring robust AI capabilities
- **Install**: `pip install kailash-kaizen`
- **Import**: `from kaizen.* import ...`

### Critical Relationships
- **DataFlow and Nexus are built ON Core SDK** - they don't replace it
- **Framework choice affects development patterns** - different approaches for each
- **All use the same underlying workflow execution** - `runtime.execute(workflow.build())`

## 🎯 Specialized Subagents

### Analysis & Planning
- **ultrathink-analyst** → Deep failure analysis, complexity assessment
- **requirements-analyst** → Requirements breakdown, ADR creation
- **sdk-navigator** → Find patterns before coding, resolve errors during development
- **framework-advisor** → Choose Core SDK, DataFlow, or Nexus; coordinates with specialists

### Framework Implementation
- **nexus-specialist** → Multi-channel platform implementation (API/CLI/MCP)
- **dataflow-specialist** → Database operations with auto-generated nodes (PostgreSQL-only alpha)

### Core Implementation  
- **pattern-expert** → Workflow patterns, nodes, parameters
- **tdd-implementer** → Test-first development
- **intermediate-reviewer** → Review after todos and implementation
- **gold-standards-validator** → Compliance checking

### Testing & Validation
- **testing-specialist** → 3-tier strategy with real infrastructure
- **documentation-validator** → Test code examples, ensure accuracy

### Release & Operations
- **todo-manager** → Task management and project tracking
- **mcp-specialist** → MCP server implementation and integration
- **git-release-specialist** → Git workflows, CI validation, releases

## ⚡ Essential Pattern (All Frameworks)
```python
from kailash.workflow.builder import WorkflowBuilder
from kailash.runtime.local import LocalRuntime

workflow = WorkflowBuilder()
workflow.add_node("NodeName", "id", {"param": "value"})  # String-based
runtime = LocalRuntime()
results, run_id = runtime.execute(workflow.build())  # ALWAYS .build()
```

## 🚨 Emergency Fixes
- **"Missing required inputs"** → Use sdk-navigator for common-mistakes.md solutions
- **Parameter issues** → Use pattern-expert for 3-method parameter guide
- **Test failures** → Use testing-specialist for real infrastructure setup
- **DataFlow errors** → Use dataflow-specialist for PostgreSQL-specific debugging
- **Nexus platform issues** → Use nexus-specialist for multi-channel troubleshooting
- **Framework selection** → Use framework-advisor to coordinate appropriate specialists

## ⚠️ Critical Rules
- ALWAYS: `runtime.execute(workflow.build())`
- NEVER: `workflow.execute(runtime)`
- String-based nodes: `workflow.add_node("NodeName", "id", {})`
- Real infrastructure: NO MOCKING in Tiers 2-3 tests
