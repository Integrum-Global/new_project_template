# Project Developer Guide

Complete guide for developing with this client project template, covering project-specific patterns, team coordination, and deployment strategies.

## 📋 Quick Navigation

| **What You Need** | **Where to Go** |
|-------------------|-----------------|
| **Start a new project** | [Getting Started](getting-started.md) |
| **Understand the architecture** | [Architecture Overview](architecture-overview.md) |
| **Build individual apps** | [Apps Development Guide](../../apps/APP_DEVELOPMENT_GUIDE.md) |
| **Coordinate multiple apps** | [Multi-App Coordination](multi-app-coordination.md) |
| **Deploy to production** | [Deployment Guide](deployment-guide.md) |
| **Team collaboration** | [Team Workflows](team-workflows.md) |
| **Solve common issues** | [Troubleshooting](troubleshooting.md) |
| **Use Kailash SDK** | [SDK User Guide](../../sdk-users/developer/README.md) |

## 🎯 Guide Hierarchy

This project template has three levels of documentation:

### 1. **Project Development** (This Guide)
- **Purpose**: Client project-specific guidance
- **Location**: `guides/developer/`
- **Covers**: Project setup, team coordination, deployment pipeline, cross-app architecture
- **Audience**: Project teams working on client deliveries

### 2. **App Development** 
- **Purpose**: Individual app development patterns
- **Location**: `apps/APP_DEVELOPMENT_GUIDE.md`
- **Covers**: Single app architecture, SDK integration, testing, deployment
- **Audience**: Developers building specific applications

### 3. **SDK Usage**
- **Purpose**: Kailash SDK reference and patterns
- **Location**: `sdk-users/`
- **Covers**: SDK nodes, workflows, runtime configuration, best practices
- **Audience**: Developers using Kailash SDK features

## 🚀 Getting Started

### New to This Project Template?
1. **Start Here**: [Getting Started Guide](getting-started.md)
2. **Understand the Structure**: [Architecture Overview](architecture-overview.md)
3. **Build Your First App**: [Apps Development Guide](../../apps/APP_DEVELOPMENT_GUIDE.md)
4. **Learn SDK Patterns**: [SDK User Guide](../../sdk-users/developer/README.md)

### Project Team Lead?
1. **Project Setup**: [Getting Started Guide](getting-started.md)
2. **Team Coordination**: [Team Workflows](team-workflows.md)
3. **Multi-App Strategy**: [Multi-App Coordination](multi-app-coordination.md)
4. **Deployment Pipeline**: [Deployment Guide](deployment-guide.md)

### Experienced Developer?
- **Quick Reference**: [SDK Cheatsheet](../../sdk-users/cheatsheet/README.md)
- **Production Patterns**: [SDK Workflows](../../sdk-users/workflows/by-pattern/README.md)
- **Cross-App Patterns**: [Solutions Layer](../../solutions/README.md)

## 🏗️ Project Template Architecture

This template is designed for **enterprise client projects** with multiple applications:

```
Client Project Structure:
├── src/                     # Client project modules (your custom code)
│   ├── new_project/         # Template project module
│   ├── customer_module/     # Client-specific business logic
│   ├── integration_module/  # Client integrations
│   └── custom_workflows/    # Client-specific workflows
├── apps/                    # 3rd party SDK apps (inherited wholesale)
│   ├── user_management/     # Enterprise authentication (from SDK projects)
│   ├── analytics/           # Data processing (from SDK projects)
│   ├── document_processor/  # AI workflows (from SDK projects)
│   └── qa_agentic_testing/  # QA automation (from SDK projects)
├── solutions/               # Cross-app orchestration
│   ├── tenant_orchestration/ # Multi-app workflows
│   ├── shared_services/     # Common services (auth, caching)
│   └── data_integration/    # Cross-app data flows
├── guides/developer/        # Project-specific guidance (this guide)
├── sdk-users/              # Kailash SDK reference
└── deployment/             # Infrastructure & deployment
```

### Key Design Principles

1. **Client Code in src/**: Your custom business logic and modules live in `src/` directories
2. **Inherited SDK Apps**: Apps in `apps/` are 3rd party applications inherited from other SDK projects
3. **Cross-App Coordination**: Use `solutions/` for workflows that span multiple apps and integrate with inherited apps
4. **SDK-First Development**: Leverage Kailash SDK nodes instead of custom code
5. **Enterprise Ready**: Built-in security, monitoring, and deployment patterns

## 🔄 Development Workflow

### Individual App Development
```mermaid
graph LR
    A[Copy Template] --> B[Customize Config]
    B --> C[Develop with SDK]
    C --> D[Test Thoroughly]
    D --> E[Document & Deploy]
```

### Multi-App Coordination
```mermaid
graph LR
    A[Define Cross-App Need] --> B[Design in Solutions Layer]
    B --> C[Implement Coordination]
    C --> D[Test Integration]
    D --> E[Deploy Coordinated System]
```

### Team Collaboration
```mermaid
graph LR
    A[Plan in ADRs] --> B[Track in TODOs]
    B --> C[Develop in Isolation]
    C --> D[Integrate via Solutions]
    D --> E[Deploy as Platform]
```

## 💡 Project-Specific Best Practices

### 1. **Conflict-Free Development**
- Each app has isolated `adr/`, `todos/`, `mistakes/` folders
- Teams work in separate app directories
- Cross-app coordination happens in `solutions/`

### 2. **SDK-First Approach**
- Use Kailash nodes instead of custom implementations
- Check `sdk-users/nodes/` before creating custom solutions
- Follow SDK patterns from `sdk-users/workflows/`

### 3. **Enterprise Patterns**
- Implement proper authentication and authorization
- Use centralized logging and monitoring
- Follow security best practices from day one

### 4. **Documentation Standards**
- Document architecture decisions in `adr/`
- Track progress in `todos/`
- Record learnings in `mistakes/`
- Keep project guide current

## 🛠️ Common Development Scenarios

### Scenario 1: Creating Client Business Logic
1. Create new module in `src/your_client_module/`
2. Implement business logic using Kailash SDK patterns
3. Integrate with inherited apps via `solutions/`

### Scenario 2: Integrating with Inherited Apps
1. Use inherited apps in `apps/` as-is (don't modify)
2. Create integration workflows in `solutions/`
3. Build coordination layer for cross-app features

### Scenario 3: Adding New SDK App
1. Inherit complete app from another SDK project
2. Place in `apps/` directory wholesale
3. Update `solutions/` to coordinate with new app

### Scenario 4: Custom Workflow Development
1. Create workflows in `src/your_module/workflows/`
2. Use `solutions/` for cross-app orchestration
3. Follow SDK patterns and node selection guide

### Scenario 5: Team Onboarding
1. Review [Getting Started](getting-started.md)
2. Set up development environment
3. Follow [Team Workflows](team-workflows.md)

## 📚 Reference Documentation

### Internal References
- **SDK Usage**: `sdk-users/developer/` - Complete Kailash SDK guide
- **Module Development**: `apps/APP_DEVELOPMENT_GUIDE.md` - Development patterns for modules
- **Inherited Apps**: `apps/` - 3rd party SDK apps (use as-is, don't modify)
- **Cross-App Patterns**: `solutions/README.md` - Multi-app coordination
- **API Documentation**: `docs/api/` - API reference

### External References
- **Kailash SDK**: [PyPI Package](https://pypi.org/project/kailash/)
- **FastAPI**: [Documentation](https://fastapi.tiangolo.com/)
- **Docker**: [Documentation](https://docs.docker.com/)
- **Kubernetes**: [Documentation](https://kubernetes.io/docs/)

## 🆘 Getting Help

### Project-Specific Issues
1. Check [Troubleshooting Guide](troubleshooting.md)
2. Review `mistakes/` folders in relevant apps
3. Search existing ADRs for similar decisions

### SDK-Related Issues
1. Check [SDK Troubleshooting](../../sdk-users/developer/07-troubleshooting.md)
2. Review [Common Mistakes](../../sdk-users/validation/common-mistakes.md)
3. Check [SDK Workflows](../../sdk-users/workflows/by-pattern/)

### Team Coordination Issues
1. Review [Team Workflows](team-workflows.md)
2. Check project ADRs for established patterns
3. Consult with project leads

---

**This project developer guide provides the foundation for successful client project delivery using the Kailash SDK template. Each section links to detailed guides for specific scenarios, ensuring teams can work efficiently while maintaining enterprise-grade quality.**