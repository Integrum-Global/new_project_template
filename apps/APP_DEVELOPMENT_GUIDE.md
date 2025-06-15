# App Development Guide

Complete guide for building enterprise applications using the Kailash SDK within this client project template.

## 📋 Table of Contents

1. [Getting Started](#getting-started)
2. [App Architecture](#app-architecture)
3. [Development Workflow](#development-workflow)
4. [SDK Integration](#sdk-integration)
5. [Testing Strategy](#testing-strategy)
6. [Deployment](#deployment)
7. [Best Practices](#best-practices)

## 🚀 Getting Started

### Creating a New App

```bash
# 1. Copy the template
cp -r apps/_template apps/my_new_app
cd apps/my_new_app

# 2. Essential customizations
# Edit setup.py - Change app name, description, dependencies
# Edit config.py - Update app_name and configuration
# Edit README.md - Replace template content

# 3. Install your app
pip install -e .

# 4. Initialize project management
echo "# App Architecture Setup" > adr/001-initial-setup.md
echo "- [ ] Define core models" > todos/000-master.md
echo "- [ ] Set up API structure" >> todos/000-master.md
```

### App Template Structure

```
my_new_app/
├── core/              # Business logic and data models
│   ├── models.py      # SQLAlchemy/Pydantic models
│   └── services.py    # Business logic services
├── api/               # FastAPI REST API
│   └── main.py        # API application and routes
├── cli/               # Command-line interface
│   └── main.py        # Click-based CLI commands
├── workflows/         # Kailash SDK workflows
│   └── __init__.py    # Workflow implementations
├── tests/             # Comprehensive testing
│   ├── unit/          # Fast, isolated tests
│   ├── integration/   # Component interaction tests
│   ├── functional/    # Feature and workflow tests
│   └── e2e/           # End-to-end scenarios
├── docs/              # App-specific documentation
├── adr/               # Architecture decisions (isolated)
├── todos/             # Task tracking (isolated)
├── mistakes/          # Learning from errors (isolated)
├── config.py          # App configuration
└── setup.py           # Package configuration
```

## 🏗️ App Architecture

### Core Components

#### 1. Business Logic Layer (`core/`)

**models.py** - Define your data models:
```python
from sqlalchemy import Column, Integer, String, DateTime
from .base import BaseModel

class Customer(BaseModel):
    __tablename__ = "customers"
    
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
```

**services.py** - Implement business logic:
```python
class CustomerService(BaseService):
    def create_customer(self, customer_data: CustomerCreate) -> Customer:
        # Business logic for customer creation
        customer = Customer(**customer_data.dict())
        self.db.add(customer)
        self.db.commit()
        return customer
```

#### 2. API Layer (`api/`)

**main.py** - FastAPI application:
```python
from fastapi import FastAPI
from .core.services import CustomerService

app = FastAPI(title="My App API")

@app.post("/customers/")
def create_customer(customer: CustomerCreate):
    service = CustomerService(db)
    return service.create_customer(customer)
```

#### 3. Workflow Layer (`workflows/`)

**customer_workflows.py** - Kailash SDK workflows:
```python
from kailash import Workflow
from kailash.nodes.data import CSVReaderNode
from kailash.nodes.ai import LLMAgentNode

class CustomerOnboardingWorkflow(Workflow):
    def __init__(self):
        super().__init__("customer_onboarding")
        
        # Add Kailash nodes
        self.csv_reader = CSVReaderNode(name="customer_data")
        self.validator = LLMAgentNode(name="data_validator")
        
        # Connect the workflow
        self.add_edge(self.csv_reader, self.validator)
```

#### 4. CLI Layer (`cli/`)

**main.py** - Command-line interface:
```python
import click
from .core.services import CustomerService

@click.group()
def cli():
    """My App CLI"""
    pass

@cli.command()
def setup():
    """Initialize the app"""
    # Setup logic here
    click.echo("App initialized successfully!")
```

### Configuration Management

**config.py** - Centralized configuration:
```python
@dataclass
class AppConfig:
    app_name: str = "my_custom_app"  # CHANGE THIS
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///app.db")
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("API_PORT", "8000"))
    
    # Add your app-specific settings
    external_api_key: str = os.getenv("EXTERNAL_API_KEY")
    cache_ttl: int = int(os.getenv("CACHE_TTL", "3600"))
```

## 🔄 Development Workflow

### 1. Planning Phase

```bash
# Document your architecture decisions
cp adr/001-template.md adr/002-database-choice.md
# Fill in: Context, Decision, Consequences

# Plan your tasks
echo "- [ ] 🔥 Set up database models" >> todos/000-master.md
echo "- [ ] ⚡ Implement customer service" >> todos/000-master.md
echo "- [ ] 📋 Add API endpoints" >> todos/000-master.md
```

### 2. Implementation Phase

```bash
# Mark task as in progress
sed -i 's/- \[ \] Set up database models/- \[~\] Set up database models/' todos/000-master.md

# Implement your feature
# Edit core/models.py, core/services.py, etc.

# Mark task as completed
sed -i 's/- \[~\] Set up database models/- \[x\] Set up database models/' todos/000-master.md
```

### 3. Testing Phase

```bash
# Write tests as you develop
# Unit tests in tests/unit/
# Integration tests in tests/integration/
# Functional tests in tests/functional/

# Run tests
pytest tests/
```

### 4. Documentation Phase

```bash
# Update your app's README.md
# Document any mistakes in mistakes/000-master.md
# Update architecture decisions in adr/
```

## 🔧 SDK Integration

### Using Kailash Nodes

```python
# Import from Kailash SDK (installed via PyPI)
from kailash.nodes.data import CSVReaderNode, SQLDatabaseNode
from kailash.nodes.ai import LLMAgentNode, EmbeddingGeneratorNode
from kailash.nodes.api import HTTPRequestNode
from kailash.workflow import Workflow
from kailash.runtime import LocalRuntime

# Create workflow with SDK nodes
class DataProcessingWorkflow(Workflow):
    def __init__(self):
        super().__init__("data_processing")
        
        # Data input
        self.csv_reader = CSVReaderNode(
            name="data_reader",
            file_path="data/inputs/customers.csv"
        )
        
        # AI processing
        self.llm_processor = LLMAgentNode(
            name="data_processor",
            model="gpt-4",
            prompt="Analyze customer data and extract insights"
        )
        
        # Data output
        self.db_writer = SQLDatabaseNode(
            name="data_writer",
            connection_string=self.config.database_url,
            operation="insert"
        )
        
        # Connect nodes
        self.add_edge(self.csv_reader, self.llm_processor)
        self.add_edge(self.llm_processor, self.db_writer)
    
    def execute(self, inputs=None):
        runtime = LocalRuntime(enable_async=True)
        return runtime.execute(self, inputs or {})
```

### Workflow Integration with Business Logic

```python
# In core/services.py
from .workflows.customer_workflows import CustomerOnboardingWorkflow

class CustomerService(BaseService):
    def onboard_customer_with_ai(self, customer_data):
        # Use business logic
        customer = self.create_customer(customer_data)
        
        # Integrate with Kailash workflow
        workflow = CustomerOnboardingWorkflow()
        results = workflow.execute({
            "customer_id": customer.id,
            "customer_data": customer_data.dict()
        })
        
        # Process workflow results
        self.update_customer_insights(customer.id, results)
        return customer
```

### SDK Reference Guide

For complete SDK usage, see:
- `sdk-users/developer/01-node-basics.md` - Node fundamentals
- `sdk-users/essentials/cheatsheet/` - Quick patterns
- `sdk-users/workflows/by-pattern/` - Production examples
- `sdk-users/nodes/comprehensive-node-catalog.md` - All available nodes

## 🧪 Testing Strategy

### Test Organization

```
tests/
├── unit/              # Fast, isolated component tests
│   ├── test_models.py
│   ├── test_services.py
│   └── test_workflows.py
├── integration/       # Component interaction tests
│   ├── test_api_integration.py
│   └── test_database_integration.py
├── functional/        # Feature and workflow tests
│   ├── test_customer_onboarding.py
│   └── test_data_processing.py
└── e2e/              # End-to-end user scenarios
    └── test_complete_user_journey.py
```

### Test Examples

**Unit Test** (`tests/unit/test_services.py`):
```python
import pytest
from core.services import CustomerService
from core.models import Customer

def test_create_customer():
    service = CustomerService(mock_db)
    customer_data = CustomerCreate(name="John", email="john@example.com")
    
    customer = service.create_customer(customer_data)
    
    assert customer.name == "John"
    assert customer.email == "john@example.com"
```

**Integration Test** (`tests/integration/test_api_integration.py`):
```python
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def test_create_customer_api():
    response = client.post("/customers/", json={
        "name": "John Doe",
        "email": "john@example.com"
    })
    
    assert response.status_code == 201
    assert response.json()["name"] == "John Doe"
```

**Workflow Test** (`tests/functional/test_workflows.py`):
```python
from workflows.customer_workflows import CustomerOnboardingWorkflow

def test_customer_onboarding_workflow():
    workflow = CustomerOnboardingWorkflow()
    
    results = workflow.execute({
        "customer_data": {"name": "John", "email": "john@example.com"}
    })
    
    assert results["status"] == "success"
    assert "customer_id" in results
```

### Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test types
pytest tests/unit/         # Fast unit tests
pytest tests/integration/  # Integration tests
pytest tests/functional/   # Workflow tests
pytest tests/e2e/          # End-to-end tests

# Run with coverage
pytest tests/ --cov=core --cov=api --cov=workflows

# Run specific test
pytest tests/unit/test_services.py::test_create_customer -v
```

## 🚢 Deployment

### Development Deployment

```bash
# Run API server
cd apps/my_app
python -m api.main

# Run CLI commands
python -m cli.main setup
python -m cli.main --help

# Run workflows
python -c "
from workflows.my_workflow import MyWorkflow
workflow = MyWorkflow()
results = workflow.execute()
print(results)
"
```

### Production Deployment

**Docker** (`Dockerfile`):
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN pip install -e .
EXPOSE 8000

CMD ["python", "-m", "api.main"]
```

**Docker Compose** (`docker-compose.yml`):
```yaml
version: '3.8'
services:
  my-app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/myapp
    depends_on:
      - db
  
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: myapp
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
```

**Kubernetes** (`k8s/deployment.yaml`):
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: my-app
  template:
    metadata:
      labels:
        app: my-app
    spec:
      containers:
      - name: my-app
        image: my-app:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: database-url
```

## 💡 Best Practices

### Code Organization

1. **Separation of Concerns**:
   - Business logic in `core/services.py`
   - Data models in `core/models.py`
   - API endpoints in `api/main.py`
   - Workflows in `workflows/`

2. **Configuration Management**:
   - Use environment variables for configuration
   - Centralize config in `config.py`
   - Validate configuration on startup

3. **Error Handling**:
   - Use structured exception handling
   - Log errors with structured logging
   - Document common errors in `mistakes/`

### SDK Best Practices

1. **Node Usage**:
   - Use specialized nodes instead of PythonCodeNode when possible
   - Follow SDK naming conventions (all nodes end with "Node")
   - Check `sdk-users/nodes/` for available nodes

2. **Workflow Design**:
   - Keep workflows focused on single business processes
   - Use clear, descriptive node names
   - Document workflow purpose and data flow

3. **Runtime Configuration**:
   - Use `LocalRuntime` with appropriate settings
   - Enable async for better performance
   - Configure monitoring and security as needed

### Documentation Standards

1. **Architecture Decisions**:
   - Document all significant choices in `adr/`
   - Include context, decision, and consequences
   - Reference related decisions

2. **Task Tracking**:
   - Use `todos/` for current work
   - Update status regularly
   - Archive completed work

3. **Learning Documentation**:
   - Record mistakes and solutions in `mistakes/`
   - Include prevention strategies
   - Share learnings with team

### Security Guidelines

1. **Environment Variables**:
   - Never commit secrets to version control
   - Use `.env` files for local development
   - Use proper secret management in production

2. **Database Security**:
   - Use connection pooling
   - Implement proper access controls
   - Enable audit logging

3. **API Security**:
   - Implement authentication and authorization
   - Validate all inputs
   - Use HTTPS in production

### Performance Optimization

1. **Database**:
   - Use proper indexing
   - Implement connection pooling
   - Monitor query performance

2. **Workflows**:
   - Use async runtime for I/O bound operations
   - Configure appropriate concurrency limits
   - Monitor workflow execution times

3. **API**:
   - Implement caching where appropriate
   - Use proper HTTP status codes
   - Monitor response times

## 🔗 Integration with Solutions

### Cross-App Coordination

When your app needs to coordinate with other apps, use the `solutions/` layer:

```python
# In your app's workflows
from solutions.shared_services.authentication import TenantAuthService

class MyAppWorkflow(Workflow):
    def execute(self, inputs):
        # Use shared authentication
        auth_service = TenantAuthService()
        user = auth_service.authenticate(inputs["token"])
        
        # Your app-specific logic here
        return self.process_for_user(user)
```

### Shared Services

If your app provides services that other apps need, expose them via the solutions layer:

```python
# solutions/shared_services/my_app_client.py
from apps.my_app.api.client import MyAppAPIClient

class MyAppService:
    def __init__(self):
        self.client = MyAppAPIClient()
    
    def get_data_for_other_apps(self, criteria):
        return self.client.query_data(criteria)
```

## 📚 Additional Resources

- **SDK Documentation**: `sdk-users/developer/README.md`
- **Workflow Examples**: `sdk-users/workflows/by-pattern/`
- **Node Reference**: `sdk-users/nodes/comprehensive-node-catalog.md`
- **Troubleshooting**: `sdk-users/developer/07-troubleshooting.md`
- **Cross-App Patterns**: `solutions/README.md`

---

**This guide provides the foundation for building enterprise applications with the Kailash SDK. Each app is self-contained with isolated project management, ensuring teams can work simultaneously without conflicts while following proven patterns for scalable, maintainable applications.**