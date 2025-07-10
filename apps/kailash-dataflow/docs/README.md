# Kailash DataFlow Documentation

Welcome to the DataFlow documentation! DataFlow is a **zero-configuration database framework** with enterprise power, currently undergoing **architectural modernization** (TODO-107) to enhance modularity and maintainability.

## 🚧 **Architectural Modernization in Progress**

DataFlow is actively being refactored from a monolithic structure to a **modern modular architecture**:
- 🔄 **Current**: Monolithic 526-line file being split into focused modules
- 🎯 **Target**: Clean `src/` structure with dedicated engine, models, and feature modules
- ✅ **Stability**: All existing functionality remains fully compatible during transition

### **🔮 Modernization Roadmap**
**Phase 1** (Active): Architectural refactoring for better maintainability
**Future**: Enhanced developer experience with improved tooling and performance

---

## 📚 Documentation Structure

### Getting Started
- [Quick Start Guide](getting-started/quickstart.md) - Your first DataFlow app in 5 minutes
- [Installation Guide](getting-started/installation.md) - Setup and configuration
- [Core Concepts](getting-started/concepts.md) - Understanding DataFlow fundamentals

### Development Guides
- [Model Definition](development/models.md) - Creating database models
- [CRUD Operations](development/crud.md) - Basic database operations
- [Bulk Operations](development/bulk-operations.md) - High-performance data handling
- [Relationships](development/relationships.md) - Modeling data relationships
- [Migrations](development/migrations.md) - Schema evolution

### Workflow Integration
- [Workflow Nodes](workflows/nodes.md) - Using database nodes in workflows
- [Transaction Management](workflows/transactions.md) - Data consistency
- [Data Flow Patterns](workflows/patterns.md) - Best practices
- [Error Handling](workflows/error-handling.md) - Resilient database operations

### Advanced Features
- [Connection Pooling](advanced/pooling.md) - Performance optimization
- [Read/Write Splitting](advanced/read-write-split.md) - Scaling strategies
- [Multi-Tenancy](advanced/multi-tenant.md) - Isolated data environments
- [Monitoring](advanced/monitoring.md) - Performance insights
- [Security](advanced/security.md) - Data protection

### Production
- [Deployment Guide](production/deployment.md) - Going to production
- [Performance Tuning](production/performance.md) - Optimization strategies
- [Backup & Recovery](production/backup.md) - Data safety
- [Troubleshooting](production/troubleshooting.md) - Common issues

### Reference
- [API Reference](reference/api.md) - Complete API documentation
- [Node Reference](reference/nodes.md) - All generated nodes
- [Configuration](reference/configuration.md) - All options
- [SQL Dialects](reference/dialects.md) - Database-specific features

### Architecture & Development ⭐ **UPDATED**
- [Architecture Decisions](adr/) - Design decisions and modernization progress
- [Under the Hood](UNDER_THE_HOOD.md) - Implementation details during refactoring
- [Framework Comparison](comparisons/FRAMEWORK_COMPARISON.md) - vs Django/SQLAlchemy/Prisma

## 🎯 Quick Links by Use Case

### I want to...

#### Start Fresh
1. [Quick Start Guide](getting-started/quickstart.md)
2. [Model Definition](development/models.md)
3. [CRUD Operations](development/crud.md)

#### Migrate from Django/Rails
1. [Migration Guide](migration/from-django.md)
2. [ORM Comparison](migration/orm-comparison.md)
3. [Feature Mapping](migration/feature-map.md)

#### Build Production Apps
1. [Production Deployment](production/deployment.md)
2. [Multi-Tenancy](advanced/multi-tenant.md)
3. [Performance Tuning](production/performance.md)

#### Integrate with Workflows
1. [Workflow Nodes](workflows/nodes.md)
2. [Transaction Patterns](workflows/transactions.md)
3. [Error Handling](workflows/error-handling.md)

## 🔍 Feature Deep Dives

### Zero Configuration
- How it works: [Architecture](architecture/zero-config.md)
- When to customize: [Progressive Enhancement](architecture/progressive.md)
- Best practices: [Configuration Guide](getting-started/concepts.md#configuration)

### Workflow-Native Database
- Node generation: [Under the Hood](architecture/node-generation.md)
- Transaction boundaries: [Data Protection](workflows/transactions.md)
- Performance: [Bulk Operations](development/bulk-operations.md)

### Enterprise Features
- Multi-tenancy: [Complete Guide](advanced/multi-tenant.md)
- Compliance: [GDPR & Privacy](advanced/compliance.md)
- Monitoring: [Observability](advanced/monitoring.md)

## 📖 Additional Resources

- **Examples**: See `/examples` for complete applications
- **Tests**: Review `/tests` for usage patterns
- **Benchmarks**: Performance comparisons in `/benchmarks`
- **ADRs**: Architecture decisions in `/docs/adr`
