# Kailash SDK - Application Development Guide

## 🎯 Overview

Complete guide for building enterprise applications with Kailash SDK. Based on proven patterns from User Management System (15.9x faster than Django) and QA Agentic Testing Framework.

## 🏗️ Quick Start

### 1. Choose Your Architecture Pattern

**Decision Matrix:**
- **Simple App** (<5 workflows): Use inline construction
- **Complex App** (>10 workflows): Use class-based patterns
- **High Performance** (<25ms response): Use hybrid routing
- **LLM Integration**: Use MCP routing (default)

### 2. Standard Directory Structure

```
your_application/
├── core/                    # Business Logic Layer
│   ├── __init__.py
│   ├── models.py           # Domain entities and data models
│   ├── services.py         # Business logic and orchestration
│   ├── database.py         # Database operations and migrations
│   ├── validators.py       # Business rules and validation
│   └── config.py           # Application configuration
├── api/                     # REST API Layer
│   ├── __init__.py
│   ├── main.py            # FastAPI application setup
│   └── routes/            # API endpoints by domain
│       ├── __init__.py
│       ├── auth.py        # Authentication endpoints
│       ├── core.py        # Core business endpoints
│       └── admin.py       # Administrative endpoints
├── cli/                     # Command Line Interface
│   ├── __init__.py
│   └── main.py            # Click CLI implementation
├── workflows/               # Kailash SDK Workflows
│   ├── __init__.py
│   ├── business_workflows.py
│   └── integration_workflows.py
├── tests/                   # Test Suite
│   ├── __init__.py        # Common test utilities
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration tests
│   ├── functional/        # Functional/E2E tests
│   └── performance/       # Performance tests
├── scripts/                 # Utility Scripts
│   ├── __init__.py
│   ├── run_tests.py       # Test runner
│   ├── setup_dev.py       # Development setup
│   └── deploy.py          # Deployment scripts
├── docs/                    # Documentation
│   ├── API_REFERENCE.md   # API documentation
│   ├── DEPLOYMENT.md      # Deployment guide
│   └── DEVELOPMENT.md     # Development guide
├── qa_results/              # Test Results (gitignored)
│   └── .gitkeep
├── data/                    # Application Data
│   ├── inputs/            # Input data files
│   └── outputs/           # Output data files
├── frontend/                # Frontend (Optional)
│   ├── public/
│   ├── src/
│   └── package.json
├── migrations/              # Database Migrations
│   └── versions/
├── __init__.py             # Package initialization
├── setup.py                # Package configuration
├── requirements.txt        # Python dependencies
├── README.md              # User documentation
├── CLAUDE.md              # Claude Code navigation
├── .env.example           # Environment variables
└── .gitignore             # Git ignore rules
```

## 📋 Implementation Steps

### Phase 1: Core Setup (30 minutes)

#### 1.1 Domain Models with Middleware

```python
# core/models.py
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum

class EntityStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"

@dataclass
class YourEntity:
    """Core business entity."""
    entity_id: str
    name: str
    description: str = ""
    status: EntityStatus = EntityStatus.ACTIVE
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    attributes: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "entity_id": self.entity_id,
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "attributes": self.attributes
        }
```

#### 1.2 Database with Middleware

**Never manually implement SQLAlchemy models. Use middleware:**

```python
# core/models.py - Extend middleware base models
from kailash.middleware.database import (
    BaseWorkflowModel, BaseExecutionModel,
    TenantMixin, AuditMixin
)

class YourWorkflow(BaseWorkflowModel):
    __tablename__ = "your_workflows"
    # Only add app-specific fields
    custom_field = Column(String(100))

# core/database.py - Use middleware manager
from kailash.middleware.database import DatabaseManager

class YourDatabase:
    def __init__(self, database_url: str = None):
        self.manager = DatabaseManager(database_url)
        self.workflow_repo = self.manager.get_repository(YourWorkflow)
```

### Phase 2: Workflow Implementation (1 hour)

#### 2.1 Service Layer with SDK Workflows

```python
# core/services.py
from typing import List, Optional, Dict, Any
from .models import YourEntity, EntityStatus
from .database import YourAppDatabase

class YourEntityService:
    """Service for managing your entities."""

    def __init__(self, db: Optional[YourAppDatabase] = None):
        self.db = db or YourAppDatabase()

    async def create_entity(self, name: str, description: str = "", **kwargs) -> YourEntity:
        """Create a new entity."""
        entity = YourEntity(
            entity_id=str(uuid.uuid4()),
            name=name,
            description=description,
            **kwargs
        )

        # Save to database
        async with self.db.get_connection() as conn:
            await conn.execute("""
                INSERT INTO your_entities
                (entity_id, name, description, status, created_at, attributes)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                entity.entity_id, entity.name, entity.description,
                entity.status.value, entity.created_at.isoformat(),
                json.dumps(entity.attributes)
            ))
            await conn.commit()

        return entity

    async def get_entity(self, entity_id: str) -> Optional[YourEntity]:
        """Get entity by ID."""
        async with self.db.get_connection() as conn:
            cursor = await conn.execute(
                "SELECT * FROM your_entities WHERE entity_id = ?", (entity_id,)
            )
            row = await cursor.fetchone()
            if row:
                return self._row_to_entity(row)
            return None
```

#### 2.2 Workflow Patterns

**Choose based on complexity:**

```python
# workflows/workflows.py - Pattern 1: Simple inline
def create_simple_workflow():
    builder = WorkflowBuilder("simple_operation")
    builder.add_node("CSVReaderNode", "reader", {
        "file_path": get_input_data_path("data.csv")
    })
    builder.add_node("DataTransformer", "transform", {
        "transformations": [{"operation": "filter"}]
    })
    builder.add_connection("reader", "result", "transform", "data")
    return builder.build()

# Pattern 2: Complex class-based with templates
class EnterpriseWorkflows(WorkflowTemplates):
    def __init__(self, config):
        self.config = config
        self.workflows = {
            "user_onboarding": self.create_crud_template("user"),
            "data_pipeline": self._create_data_pipeline()
        }

    def _create_data_pipeline(self) -> Workflow:
        workflow = self.create_etl_template("customer_data")
        # Add custom steps
        workflow.add_node("ai_enrichment", LLMAgentNode(
            model=self.config.llm_model
        ))
        return workflow
```

### Phase 3: Interface Layer (30 minutes)

#### 3.1 API with Enterprise Middleware

```python
# api/main.py - Never create FastAPI manually!
from kailash.middleware import create_gateway
from .workflows import app_workflows

# Enterprise API with all features
app = create_gateway(
    title="Your Application API",
    workflows=app_workflows,
    enable_auth=True,
    enable_monitoring=True,
    enable_realtime=True,
    rate_limits={
        "/api/auth/*": "5 per minute",
        "/api/*": "100 per minute"
    }
)

# That's it! You get:
# - OpenAPI docs at /docs
# - Authentication & SSO
# - WebSocket support
# - Metrics & monitoring
# - Rate limiting
# - CORS handling
# - Security headers
```

#### 3.2 CLI with SDK Integration

```python
# cli/main.py
import asyncio
import click
from ..core.services import YourEntityService
from ..core.database import YourAppDatabase

@click.group()
@click.version_option(version="1.0.0")
def cli():
    """Your Application - Built with Kailash SDK."""
    pass

@cli.command()
@click.argument('name')
@click.option('--description', '-d', default='', help='Entity description')
def create(name: str, description: str):
    """Create a new entity."""

    async def run_create():
        service = YourEntityService()
        entity = await service.create_entity(name, description)
        click.echo(f"✅ Entity created: {entity.entity_id}")
        click.echo(f"Name: {entity.name}")

    asyncio.run(run_create())

@cli.command()
def server():
    """Start the web server."""
    import uvicorn
    from ..api.main import app

    click.echo("🚀 Starting Your Application server...")
    uvicorn.run(app, host="localhost", port=8000)

if __name__ == '__main__':
    cli()
```

### Phase 4: Testing & Deployment (1 hour)

#### 4.1 Testing with QA Framework

```python
# Run comprehensive QA testing
from qa_agentic_testing import AutonomousQATester

async def validate_app():
    tester = AutonomousQATester()
    await tester.discover_app(".")
    results = await tester.execute_tests()
    tester.generate_report("qa_report.html")

    # Also run performance tests
    from kailash.testing import PerformanceTester
    perf_tester = PerformanceTester(app)
    perf_results = await perf_tester.run_benchmarks()

    print(f"✅ Success rate: {results.success_rate}%")
    print(f"⚡ Avg response: {perf_results.avg_response_ms}ms")
```

#### 4.2 Deployment

```dockerfile
# Dockerfile - Production ready
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
RUN pip install -e .
EXPOSE 8000
CMD ["your-app", "server"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/app
      - REDIS_URL=redis://redis:6379
  db:
    image: postgres:15
  redis:
    image: redis:7-alpine
```

## 📦 Configuration Templates

### **setup.py**
```python
from setuptools import setup, find_packages

setup(
    name="your-application",
    version="1.0.0",
    description="Enterprise application built with Kailash SDK",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "fastapi>=0.104.0",
        "uvicorn[standard]>=0.24.0",
        "click>=8.0.0",
        "aiosqlite>=0.19.0",
        "kailash-sdk",
    ],
    entry_points={
        "console_scripts": [
            "your-app=your_app.cli.main:cli",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
```

## 📚 Common Patterns

### High-Performance Data Processing
```python
# Hybrid routing for <25ms operations
class DataProcessor:
    FAST_OPS = {"validate", "transform", "filter"}

    async def process(self, operation: str, data: dict):
        if operation in self.FAST_OPS:
            return await self._direct_process(data)
        else:
            return await self.mcp_server.call_tool(operation, data)
```

### LLM-Enhanced Operations
```python
# Always use MonitoredLLMAgentNode for production
workflow.add_node("analyzer", MonitoredLLMAgentNode(
    model="gpt-4",
    monitoring_config={"track_costs": True}
))
```

### Enterprise Security
```python
# Automatic ABAC with AI reasoning
workflow.add_node("auth", ABACPermissionEvaluatorNode(
    ai_reasoning=True,
    cache_results=True
))
```

## 🎯 Performance Optimization

### Response Time Categories
- **Ultra-low (<5ms)**: Direct calls, no abstraction
- **Low (5-25ms)**: Hybrid routing, selective optimization
- **Medium (25-100ms)**: Standard patterns, MCP acceptable
- **High (>100ms)**: Full middleware stack

### Optimization Checklist
- [ ] Profile critical paths with `cProfile`
- [ ] Use `AsyncLocalRuntime` for I/O operations
- [ ] Enable connection pooling in database
- [ ] Implement caching for repeated operations
- [ ] Use batch operations for bulk data

## ⚠️ Common Pitfalls

1. **Creating manual FastAPI/SQLAlchemy** → Use middleware
2. **PythonCodeNode for everything** → Check node catalog first
3. **Hardcoded paths** → Use `get_output_data_path()`
4. **Missing "result" wrapper** → PythonCodeNode always needs it
5. **Direct node instantiation** → Use string-based `WorkflowBuilder`

## 📋 Quick Development Checklist

### Start (Day 1)
- [ ] Run `create-kailash-app` template generator
- [ ] Choose architecture pattern from decision matrix
- [ ] Define models extending middleware bases
- [ ] Create workflows (inline or class-based)
- [ ] Use `create_gateway()` for API

### Test (Day 2)
- [ ] Run QA framework: `qa-test .`
- [ ] Check performance: < 100ms target
- [ ] Validate security with ABAC tester

### Deploy (Day 3)
- [ ] Docker build and compose
- [ ] Configure monitoring
- [ ] Production checklist

## 📚 Reference Examples

- **User Management**: 15.9x faster than Django Admin
- **QA Testing**: 100% autonomous with AI agents
- **Studio**: Workflow builder with real-time collaboration

All examples in `/apps/` follow these patterns.
