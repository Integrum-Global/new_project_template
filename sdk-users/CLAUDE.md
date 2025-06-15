# SDK Users - Navigation Hub

*Building solutions WITH the Kailash SDK*

## 🚀 v0.4.0 Enterprise Middleware Architecture

**🌉 Complete Middleware Stack**: Production-ready enterprise platform with `create_gateway()` - single function creates full app with real-time communication, AI chat, and session management.

**🔄 Real-time Agent-UI Communication**: WebSocket/SSE streaming, dynamic workflow creation from frontend, multi-tenant session isolation.

**🤖 AI Chat Integration**: Natural language workflow generation, context-aware conversations, automatic workflow creation from user descriptions.

**⚡ Unified Runtime**: LocalRuntime includes async + all enterprise capabilities. See [developer/18-unified-runtime-guide.md](developer/18-unified-runtime-guide.md) for complete guide.

**🔗 Dot Notation Mapping**: Access nested node outputs with `"result.data"`, `"result.metrics"`, `"source.nested.field"` in workflow connections.

**🎯 Auto-Mapping Parameters**: NodeParameter supports `auto_map_primary=True`, `auto_map_from=["alt1"]`, `workflow_alias="name"` for automatic connection discovery.

## 🏗️ Architecture Decisions First

**⚠️ STOP! Before building any app, make these critical decisions:**

### 📋 Decision Matrix → [decision-matrix.md](decision-matrix.md)

The decision matrix provides fast answers to:
- **Workflow Pattern**: Inline vs Class-based vs Hybrid construction
- **Interface Routing**: MCP vs Direct calls vs Hybrid routing
- **Performance Strategy**: Latency thresholds and optimization approaches
- **Common Combinations**: Recommended patterns for different app types

### 📚 Complete Implementation Guidance

| Decision Type | Quick Decisions | Implementation Guide | Technical Details |
|---------------|-----------------|---------------------|-------------------|
| **Workflow Construction** | [decision-matrix.md](decision-matrix.md) | [Apps Guide](../apps/ARCHITECTURAL_GUIDE.md) | [ADR-0045](../sdk-contributors/architecture/adr/0045-workflow-construction-patterns.md) |
| **Interface Routing** | [decision-matrix.md](decision-matrix.md) | [Apps Guide](../apps/ARCHITECTURAL_GUIDE.md) | [ADR-0046](../sdk-contributors/architecture/adr/0046-interface-routing-strategies.md) |
| **Performance Strategy** | [decision-matrix.md](decision-matrix.md) | [Apps Guide](../apps/ARCHITECTURAL_GUIDE.md) | [ADR-0047](../sdk-contributors/architecture/adr/0047-performance-guidelines.md) |

## 🎯 Quick Navigation Guide
| I need to... | Go to | Purpose |
|--------------|-------|---------|
| **Make architecture decisions** | [decision-matrix.md](decision-matrix.md) | Choose workflow patterns, routing |
| **Build complete app** | [../apps/ARCHITECTURAL_GUIDE.md](../apps/ARCHITECTURAL_GUIDE.md) | App implementation guide |
| Build from scratch | [developer/](developer/) | Technical guides, patterns |
| Lift working example | [workflows/](workflows/) | Industry & enterprise solutions |
| Quick code snippet | [essentials/cheatsheet/](essentials/cheatsheet/) | Copy-paste patterns |
| Choose right node | [nodes/](nodes/comprehensive-node-catalog.md) | Node selection guide |
| Fix an error | [developer/07-troubleshooting.md](developer/07-troubleshooting.md) | Error resolution |
| Frontend integration | [middleware/](middleware/) | Real-time agent-UI communication |
| Learn features | [features/](features/) | Feature documentation |
| **Production workflows** | [workflows/](workflows/) | Business-focused solutions |
| **Run tests** | [../tests/README.md](../tests/README.md) | Test suite guide |
| **SDK development** | [../examples/](../examples/) | Feature validation & testing |

## 📁 Navigation Guide

### **Build from Scratch or Modify**
- **[developer/](developer/)** - Node creation, patterns, troubleshooting
  - Critical PythonCodeNode patterns
  - Directory reader best practices
  - Document processing workflows
  - Custom node development
  - Middleware integration patterns
  - Unified runtime with enterprise capabilities
  - **[20-comprehensive-rag-guide.md](developer/20-comprehensive-rag-guide.md)** - Complete RAG toolkit with 30+ specialized nodes

### **Frontend Integration**
- **[middleware/](middleware/)** - Enterprise middleware layer
  - Agent-UI communication patterns
  - Real-time event streaming
  - Dynamic workflow creation
  - AI chat integration

### **Production Workflows**
- **[workflows/](workflows/)** - Business-focused, production-ready solutions
  - **One-line principle**: Single source for all production workflows → [workflows/README.md](workflows/README.md)

### **Quick Reference**
- **[essentials/](essentials/)** - Copy-paste patterns (streamlined cheatsheet)
- **[api/](api/)** - API documentation and signatures
- **[nodes/](nodes/)** - Complete node catalog with examples
- **[patterns/](patterns/)** - Architectural workflow patterns
- **[templates/](templates/)** - Boilerplate code templates

### **User Features**
- **[features/](features/)** - Feature guides and when to use them
- **[validation-guide.md](validation-guide.md)** - Critical rules to prevent errors

## 📚 Resource Categories

### **Development Guides**
- **[developer/](developer/)** - In-depth technical documentation
  - Node creation and patterns
  - Parameter types and validation
  - Common patterns and anti-patterns
  - Workflow design process (Session 064)
  - Data integration patterns (Session 064)
  - Production readiness checklist (Session 064)
  - Troubleshooting guide

### **Working Examples**
- **[workflows/](workflows/)** - Complete production workflows
  - **by-industry/** - Finance, healthcare, manufacturing, retail
  - **by-enterprise/** - HR, marketing, operations, analytics
  - **by-pattern/** - ETL, real-time, batch, event-driven

### **Quick Reference**
- **[essentials/cheatsheet/](essentials/cheatsheet/)** - Copy-paste code snippets
  - Installation and setup
  - Common node patterns
  - Connection patterns
  - Workflow design process (Session 064)
  - Data integration patterns (Session 064)
  - Production readiness checklist (Session 064)
  - Best practices summary

### **Node Catalog**
- **[nodes/](nodes/)** - Complete node reference
  - Comprehensive catalog with examples
  - Node selection guide
  - Input/output specifications

### **Features**
- **[features/](features/)** - Advanced SDK capabilities
  - Access control and security
  - API integration patterns
  - Performance optimization
  - Cyclic workflows

## ⚠️ Critical Rules Reference
For validation rules and common mistakes, see:
- **Root CLAUDE.md** - Critical validation rules
- **[decision-matrix.md](decision-matrix.md)** - Architecture decision guidelines
- **[developer/07-troubleshooting.md](developer/07-troubleshooting.md)** - Error fixes
- **[shared/mistakes/](../shared/mistakes/)** - Comprehensive mistake database

## 🤖 Critical Workflow

**MANDATORY STEPS before any app implementation:**

1. **ALWAYS load [decision-matrix.md](decision-matrix.md) FIRST**
2. **Ask user performance requirements** (latency/throughput/volume)
3. **Ask about LLM agent integration needs**
4. **Use decision matrix lookup tables** to choose patterns
5. **Reference [../apps/ARCHITECTURAL_GUIDE.md](../apps/ARCHITECTURAL_GUIDE.md)** for implementation
6. **Document architectural choices in implementation plan**
7. **Surface trade-offs to user for approval**

### Planning Template:
```
Based on your requirements, I recommend:

Performance Analysis:
- Expected latency: [X]ms
- Request volume: [X]/second
- LLM integration: [Y/N]

Architectural Decisions:
- Workflow pattern: [inline/class-based/hybrid] because [reason]
- Interface routing: [MCP/direct/hybrid] because [reason]
- Performance strategy: [approach] because [reason]

Trade-offs:
- [List key trade-offs and implications]

Proceed with this approach?
```

**Key Decision Points:**
- **<5ms + >1000req/sec** = Direct calls likely needed
- **LLM integration required** = MCP routing essential
- **Mixed complexity** = Hybrid approach recommended
- **Unsure** = Start with MCP routing + hybrid workflows

---

**Building workflows?** Start with [developer/](developer/) or [workflows/](workflows/)
**Need help?** Check [developer/07-troubleshooting.md](developer/07-troubleshooting.md)
**For SDK development**: See [../sdk-contributors/CLAUDE.md](../sdk-contributors/CLAUDE.md)
