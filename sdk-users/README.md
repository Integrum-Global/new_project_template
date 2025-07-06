# SDK Users Guide

*Everything you need to build solutions with the Kailash SDK*

## 🚨 Start Here: [CLAUDE.md](CLAUDE.md)
Quick reference with critical rules, common patterns, and navigation guide.

## 🎯 **Critical for Claude Code Users**
- **[cheatsheet/000-claude-code-guide.md](cheatsheet/000-claude-code-guide.md)** - **START HERE** Essential success patterns
- **[cheatsheet/025-mcp-integration.md](cheatsheet/025-mcp-integration.md)** - MCP (Model Context Protocol) integration
- **[cheatsheet/038-integration-mastery.md](cheatsheet/038-integration-mastery.md)** - Complete integration guide
- **[cheatsheet/039-workflow-composition.md](cheatsheet/039-workflow-composition.md)** - Advanced workflow patterns

## 🚀 **MCP (Model Context Protocol) - AI Tool Integration**
- **[guides/mcp-quickstart.md](guides/mcp-quickstart.md)** - **NEW!** Quick start guide for MCP
- **[cheatsheet/025-mcp-integration.md](cheatsheet/025-mcp-integration.md)** - Complete MCP reference with code snippets
- **[patterns/12-mcp-patterns.md](patterns/12-mcp-patterns.md)** - Production MCP patterns and best practices
- **[examples/mcp/](examples/mcp/)** - Ready-to-run MCP examples
- **[developer/22-mcp-development-guide.md](developer/22-mcp-development-guide.md)** - Build custom MCP servers and clients (✅ 100% validated)

## 📁 Contents

### **Enterprise & Production**
- **[enterprise/](enterprise/)** - Enterprise-grade patterns and architecture
  - Advanced middleware patterns
  - Multi-tenant session management
  - Production security and monitoring
  - High-scale deployment patterns

- **[production-patterns/](production-patterns/)** - Real app implementations & deployment
  - Proven patterns from actual production apps
  - 15.9x performance optimizations
  - Production deployment configurations
  - Real-world security and monitoring

### **Build from Scratch or Modify**
- **[developer/](developer/)** - Node creation, patterns, troubleshooting
  - Critical PythonCodeNode input exclusion patterns
  - DirectoryReaderNode file discovery
  - Document processing workflows
  - Custom node development guide
  - Advanced troubleshooting
  - **✅ [MCP Development Guide](developer/22-mcp-development-guide.md)** - Build MCP servers and clients (comprehensive validation complete)

### **Lift Working Examples**
- **[workflows/](workflows/)** - End-to-end use cases ready to copy
  - Quick-start patterns for immediate use
  - Common patterns (data processing, API integration, AI)
  - Industry solutions (healthcare, finance, manufacturing)
  - Production-ready scripts with real data

### **Quick Reference**
- **[cheatsheet/](cheatsheet/)** - Copy-paste code snippets
  - **NEW: Claude Code specific guides**
  - Installation and basic setup
  - Common node patterns
  - Connection patterns
  - Error handling
- **[migration-guides/](migration-guides/)** - Version upgrade guides
  - Architecture improvements by version
  - Step-by-step migration instructions
  - Breaking changes documentation
  - Security configuration

- **[api/](api/)** - Complete API documentation
  - Method signatures and parameters
  - YAML specifications
  - Usage examples

- **[nodes/](nodes/)** - Comprehensive node catalog
  - 110+ nodes with examples
  - Node selection guide
  - Use case recommendations

- **[patterns/](patterns/)** - Architectural workflow patterns
  - Core workflow patterns
  - Control flow and data processing
  - Integration and deployment patterns
  - Performance and security patterns
  - **NEW: [MCP Patterns](patterns/12-mcp-patterns.md)** - Model Context Protocol patterns

- **[workflows/](workflows/)** - Ready-to-use boilerplate code
  - Basic workflows
  - Custom node templates
  - Integration examples

### **User Features**
- **[features/](features/)** - Feature guides and implementation examples
  - When and how to use each feature
  - Decision guides and best practices
  - Real-world implementation patterns

- **[validation-guide.md](validation-guide.md)** - Critical rules to prevent common errors

## 🎯 Quick Start Paths

### **New to Kailash?**
1. Read [CLAUDE.md](CLAUDE.md) for critical rules
2. Try [workflows/quick-start/](workflows/quick-start/) examples
3. Use [cheatsheet/](cheatsheet/) for common patterns
4. Reference [nodes/](nodes/) for available components

### **Building with MCP (Model Context Protocol)?**
1. Start with [guides/mcp-quickstart.md](guides/mcp-quickstart.md) for basics
2. Use [cheatsheet/025-mcp-integration.md](cheatsheet/025-mcp-integration.md) for quick reference
3. Try [examples/mcp/](examples/mcp/) for working examples
4. Study [patterns/12-mcp-patterns.md](patterns/12-mcp-patterns.md) for production patterns

### **Building Complex Workflows?**
1. Start with [workflows/common-patterns/](workflows/common-patterns/)
2. Check [patterns/](patterns/) for architectural guidance
3. Use [developer/](developer/) for custom components
4. Reference [api/](api/) for detailed specifications

### **Industry-Specific Solutions?**
1. Browse [workflows/by-industry/](workflows/by-industry/)
2. Check [features/](features/) for relevant capabilities
3. Use [workflows/](workflows/) for boilerplate code
4. Customize with [developer/](developer/) patterns

### **Debugging Issues?**
1. Check [developer/05-troubleshooting.md](developer/05-troubleshooting.md)
2. Review [CLAUDE.md](CLAUDE.md) common mistakes
3. Look up errors in [../shared/mistakes/](../shared/mistakes/)
4. Validate with [validation/common-mistakes.md](validation/common-mistakes.md)

## ✅ Production Quality Validated (2025-07-02)

**Comprehensive Testing Status**: All core SDK functionality validated with production-quality testing

| Test Tier | Results | Status |
|-----------|---------|---------|
| **Tier 1 (Unit)** | 1265/1265 PASSED | ✅ 100% |
| **Tier 2 (Integration)** | 400/400 PASSED | ✅ 100% |
| **Tier 3 (E2E Core)** | 10/10 CORE PASSED | ✅ 100% |

**Key Validations Completed**:
- ✅ **Ollama LLM Integration**: Real AI workflows with aiohttp async compatibility
- ✅ **Performance & Scalability**: Memory usage, concurrency, stress testing
- ✅ **Admin Docker Integration**: Multi-tenant operations with real databases
- ✅ **Cycle Patterns**: ETL pipelines with retry logic and real file processing
- ✅ **Simple AI Docker**: Basic to advanced AI workflow patterns

**Production Features Verified**:
- AsyncWorkflowBuilder with 240-second timeouts for complex AI operations
- Real Ollama LLM instances with 60%+ success rates
- Docker-based admin operations with full CRUD functionality
- Multi-node AI processing pipelines
- Performance patterns under load

See [../e2e_summary.txt](../e2e_summary.txt) for complete test results and technical fixes applied.

## ⚠️ Critical Knowledge

### **MCP Integration with LLMAgentNode**
MCP enables AI agents to use external tools and resources:
```python
from kailash.nodes.ai import LLMAgentNode

# LLM with MCP tools
workflow.add_node("agent", LLMAgentNode())
results, run_id = runtime.execute(workflow, parameters={
    "agent": {
        "provider": "ollama",
        "model": "llama3.2",
        "mcp_servers": [{
            "name": "tools",
            "transport": "stdio",
            "command": "mcp-server"
        }],
        "auto_discover_tools": True,
        "auto_execute_tools": True
    }
})
```

### **PythonCodeNode Input Exclusion**
Variables passed as inputs are EXCLUDED from outputs!
```python
# SDK Setup for example
from kailash import Workflow
from kailash.runtime.local import LocalRuntime
from kailash.nodes.data import CSVReaderNode
from kailash.nodes.ai import LLMAgentNode
from kailash.nodes.api import HTTPRequestNode
from kailash.nodes.logic import SwitchNode, MergeNode
from kailash.nodes.code import PythonCodeNode
from kailash.nodes.base import Node, NodeParameter

# Example setup
workflow = Workflow("example", name="Example")
workflow.runtime = LocalRuntime()
```

### **Node Naming Convention**
ALL nodes must end with "Node":
- ✅ `CSVReaderNode`
- ❌ `CSVReader`

### **Parameter Types**
Only use basic types: `str`, `int`, `float`, `bool`, `list`, `dict`, `Any`
- ❌ `List[str]`, `Optional[int]`, `Union[str, int]`

## 📖 Related Resources

- **SDK Development**: [../sdk-contributors/](../sdk-contributors/)
- **Shared Resources**: [../shared/](../shared/)
- **Error Lookup**: [../shared/mistakes/CLAUDE.md](../shared/mistakes/CLAUDE.md)

---

*This guide focuses on using the SDK to build solutions. For extending the SDK itself, see [../sdk-contributors/README.md](../sdk-contributors/README.md)*
