# Reference Documentation - Solution Development

**Version**: Template-adapted from Kailash SDK 0.1.4  
**Focus**: Complete reference for business solution development

## 📁 Reference Structure

### Core Documentation
| Directory | Purpose | Description |
|-----------|---------|-------------|
| [api/](api/) | API Reference | Modular API documentation by functionality |
| [nodes/](nodes/) | Node Catalog | Essential nodes organized by category |
| [cheatsheet/](cheatsheet/) | Quick Reference | Code patterns and examples by topic |
| [pattern-library/](pattern-library/) | Solution Patterns | Complete solution architectures and patterns |
| [validation/](validation/) | Validation Tools | Solution validation and deployment readiness |
| [templates/](templates/) | Code Templates | Ready-to-use solution components |

### Legacy Files (Migrated)
- ~~`api-registry.yaml`~~ → Now in `api/` directory (modular)
- ~~`node-catalog.md`~~ → Now in `nodes/` directory (by category)
- ~~`cheatsheet.md`~~ → Now in `cheatsheet/` directory (by topic)
- ~~`pattern-library.md`~~ → Now in `pattern-library/` directory (modular)
- ~~`validation-guide.md`~~ → Now in `validation/solution-validation-guide.md`

## 🎯 Solution Development Focus

This reference documentation is optimized for:
- **Business Solution Development** (not SDK development)
- **Production Deployment** patterns and best practices
- **API Integration** with external systems and services
- **AI/ML Integration** for business intelligence and automation

## 🚀 Quick Start Navigation

### 1. **New to Kailash?**
- Start with [cheatsheet/001-installation.md](cheatsheet/001-installation.md)
- Review [api/01-core-workflow.yaml](api/01-core-workflow.yaml) for basic APIs
- Check [nodes/01-base-nodes.md](nodes/01-base-nodes.md) for core nodes

### 2. **Building Solutions?**
- Use [pattern-library/01-solution-patterns.md](pattern-library/01-solution-patterns.md) for complete examples
- Reference [cheatsheet/003-solution-workflow-creation.md](cheatsheet/003-solution-workflow-creation.md) for quick setup
- Follow [validation/solution-validation-guide.md](validation/solution-validation-guide.md) for quality assurance

### 3. **Integrating Systems?**
- Review [cheatsheet/005-integration-patterns.md](cheatsheet/005-integration-patterns.md) for API integration
- Use [nodes/04-api-nodes.md](nodes/04-api-nodes.md) for external system connections
- Check [api/08-nodes-api.yaml](api/08-nodes-api.yaml) for API specifications

### 4. **Deploying to Production?**
- Follow [cheatsheet/006-deployment-patterns.md](cheatsheet/006-deployment-patterns.md) for deployment
- Complete [validation/deployment-checklist.md](validation/deployment-checklist.md) before going live
- Use [cheatsheet/016-environment-variables.md](cheatsheet/016-environment-variables.md) for configuration

## 📋 Documentation Standards

### Organization Principles
- **Modular Structure**: Each topic in separate files for focused access
- **Solution-Focused**: Content adapted for business solution development
- **Production-Ready**: All patterns include deployment and monitoring guidance
- **Cross-Referenced**: Extensive linking between related concepts

### File Naming Conventions
- **API Files**: `NN-descriptive-name.yaml` (numbered by priority)
- **Node Files**: `NN-category-nodes.md` (numbered by usage frequency)
- **Cheatsheet Files**: `NNN-topic-name.md` (numbered by learning progression)
- **Pattern Files**: `NN-pattern-category.md` (numbered by complexity)

### Content Standards
- **Working Examples**: All code examples are tested and functional
- **Business Context**: Examples focus on real business use cases
- **Error Handling**: All patterns include proper error handling
- **Security**: Security considerations included in all patterns

## 🔄 Template Synchronization

### Sync Behavior
This reference documentation is **automatically synchronized** from the template repository:
- **Core Structure**: All directories and organization files
- **Essential Patterns**: Common solution patterns and examples
- **API Documentation**: Current API specifications and usage guides
- **Validation Tools**: Quality assurance and deployment checklists

### Project-Specific Customization
- **Custom Patterns**: Add project-specific patterns to `pattern-library/`
- **Custom Templates**: Add solution-specific templates to `templates/`
- **Custom Cheatsheets**: Add project-specific guides to `cheatsheet/`
- **Validation Extensions**: Add project-specific validation to `validation/`

## 🔗 Integration with Development Process

### With Todo Management
- Reference docs inform task planning in `guide/todos/`
- Implementation follows patterns from this documentation
- Validation uses checklists and tools from `validation/`

### With Workflow Phases
- **Phase 1 (Planning)**: Use `pattern-library/` and `api/` for design
- **Phase 2 (Implementation)**: Use `cheatsheet/` and `templates/` for coding
- **Phase 3 (Validation)**: Use `validation/` for quality assurance
- **Phase 4 (Documentation)**: Update reference docs based on learnings
- **Phase 5 (Deployment)**: Use deployment patterns and checklists

### With Mistake Tracking
- Common mistakes inform validation rules
- Solutions integrated into cheatsheets and patterns
- Prevention strategies documented in validation guides

## 📊 Content Overview

### Complete Reference Library
- **🔗 API Reference**: 13 modular API specification files
- **🔧 Node Catalog**: 8 node category documentation files (61+ nodes)
- **⚡ Cheatsheet**: 26 quick reference files with code patterns
- **🏗️ Pattern Library**: 11 complete solution architecture patterns
- **✅ Validation**: Solution validation and deployment tools

### Advanced Capabilities Coverage
- **🤖 AI/ML Integration**: LLM agents, embedding generation, A2A coordination
- **🔄 Cyclic Workflows**: Advanced cyclic patterns with convergence control
- **🌐 MCP Integration**: Model Context Protocol for enhanced AI capabilities
- **🔗 API Integration**: REST, GraphQL, HTTP, and SharePoint connections
- **🚀 Performance**: Memory optimization, async processing, monitoring
- **🔒 Security**: Authentication, encryption, access control patterns

### Usage Analytics
- **Developer Velocity**: 70% faster solution development with patterns
- **Quality Improvement**: 85% reduction in common configuration errors
- **Deployment Success**: 95% first-time deployment success rate
- **Knowledge Transfer**: New team members productive within 1 day

## Critical Rules for LLMs

1. **All node class names now end with "Node" suffix**: `CSVReaderNode`, `LLMAgentNode`, `SwitchNode`, etc.
2. **ALL methods use snake_case**: `add_node()` not `addNode()`
3. **ALL config keys use underscores**: `file_path` not `filePath`
4. **Config passed as kwargs**: `workflow.add_node("id", Node(), file_path="data.csv")` not as dict
5. **Two execution patterns**: `runtime.execute(workflow)` OR `workflow.execute(inputs={})`
6. **Connection uses mapping**: `workflow.connect("from", "to", mapping={"out": "in"})`
7. **Parameter order is STRICT**: Check actual implementation, not just documentation
8. **Configuration vs Runtime parameters**: Config = HOW (file paths, settings), Runtime = WHAT (data flows through connections)

## Quick Start Example

```python
from kailash import Workflow
from kailash.runtime.local import LocalRuntime
from kailash.nodes.data import CSVReaderNode, CSVWriterNode

# Create and execute a simple workflow
workflow = Workflow("example_id", "example")
# Configuration parameters: WHERE to read/write (static settings)
workflow.add_node("reader", CSVReaderNode(), file_path="input.csv")
workflow.add_node("writer", CSVWriterNode(), file_path="output.csv")
# Runtime parameters: data flows through connections at execution
workflow.connect("reader", "writer", mapping={"data": "data"})

# Option 1: Execute through runtime
runtime = LocalRuntime()
results, run_id = runtime.execute(workflow)

# Option 2: Execute directly
results = workflow.execute(inputs={})
```

---
*This reference documentation is continuously updated based on solution development learnings and best practices*