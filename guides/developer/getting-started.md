# Getting Started with Client Project Template

Complete guide for setting up and starting development with this client project template.

## 🎯 Prerequisites

### System Requirements
- **Python**: 3.11 or higher
- **Git**: Latest version
- **Docker**: For containerized development (optional but recommended)
- **IDE**: VS Code, PyCharm, or your preferred editor

### Knowledge Requirements
- Basic Python development experience
- Familiarity with REST APIs and FastAPI
- Understanding of SQL databases
- Basic Docker knowledge (for deployment)

## 🚀 Initial Project Setup

### 1. Clone or Create from Template

**Option A: Use as Template (Recommended)**
```bash
# Create new repository from this template on GitHub
# Then clone your new repository
git clone https://github.com/your-org/your-client-project.git
cd your-client-project
```

**Option B: Clone Directly**
```bash
git clone https://github.com/integrum/new_project_template.git my-client-project
cd my-client-project
rm -rf .git  # Remove template git history
git init     # Initialize new git repository
```

### 2. Environment Setup

**Install Dependencies**
```bash
# Install the Kailash SDK from PyPI
pip install kailash

# Install project dependencies
pip install -e .

# Or using uv (recommended)
uv sync
```

**Configure Environment**
```bash
# Copy environment template
cp .env.template .env

# Edit .env with your project-specific settings
# - Database connection strings
# - API keys and secrets
# - Environment-specific configuration
```

**Verify Installation**
```bash
# Test Kailash SDK installation
python -c "from kailash import Workflow; print('Kailash SDK installed successfully')"

# Test project structure
python -c "from apps.user_management.core.models import User; print('Project structure valid')"
```

### 3. Database Setup

**Local Development (SQLite)**
```bash
# SQLite is configured by default for development
# Database file will be created automatically
```

**PostgreSQL (Production-like)**
```bash
# Start PostgreSQL with Docker
docker run --name client-db -e POSTGRES_PASSWORD=password -d -p 5432:5432 postgres:15

# Update .env file
echo "DATABASE_URL=postgresql://postgres:password@localhost:5432/client_db" >> .env

# Run migrations (if available)
# alembic upgrade head
```

### 4. Verify Setup

**Quick Verification**
```bash
# Test the centralized deployment
./deployment/scripts/start.sh

# Check if services are running
curl http://localhost:8000/api/v1/discovery
curl http://localhost:8000/docs

# Stop services
./deployment/scripts/stop.sh
```

## 📁 Project Structure Overview

Understanding the template structure is crucial for effective development:

```
your-client-project/
├── 📱 apps/                     # Individual client applications
│   ├── user_management/         # Enterprise user management
│   ├── analytics/               # Data analytics dashboard
│   ├── document_processor/      # AI document processing
│   ├── qa_agentic_testing/      # QA testing automation
│   └── _template/               # Template for new apps
│
├── 🔄 solutions/                # Cross-app orchestration
│   ├── tenant_orchestration/    # Multi-app workflows
│   ├── shared_services/         # Common services
│   └── data_integration/        # Cross-app data flows
│
├── 📚 docs/                     # Project documentation
│   ├── developer/               # Developer guides (this guide)
│   ├── api/                     # API documentation
│   └── guides/                  # User guides
│
├── 🛠️ sdk-users/                # Kailash SDK reference
│   ├── developer/               # SDK development patterns
│   ├── workflows/               # Production workflow examples
│   ├── nodes/                   # Available SDK nodes
│   └── cheatsheet/              # Quick reference
│
├── 🚢 deployment/               # Infrastructure & deployment
│   ├── docker/                  # Docker configurations
│   ├── kubernetes/              # K8s manifests
│   └── scripts/                 # Deployment automation
│
└── 📊 data/                     # Project data
    ├── inputs/                  # Sample/test data
    ├── outputs/                 # Generated results
    └── configs/                 # Configuration files
```

## 🏗️ Development Environment Setup

### IDE Configuration

**VS Code (Recommended)**
```bash
# Install recommended extensions
code --install-extension ms-python.python
code --install-extension ms-python.flake8
code --install-extension ms-python.black-formatter
code --install-extension bradlc.vscode-tailwindcss

# Open project
code .
```

**PyCharm**
1. Open project directory
2. Configure Python interpreter to use virtual environment
3. Enable Django support if using Django features
4. Configure code formatting with Black

### Development Tools

**Code Quality Tools**
```bash
# Install development tools
pip install black isort ruff mypy pytest pre-commit

# Set up pre-commit hooks
pre-commit install

# Run code formatting
black .
isort .
ruff check .
```

**Testing Setup**
```bash
# Install test dependencies
pip install pytest pytest-cov pytest-asyncio

# Run tests to verify setup
pytest apps/user_management/tests/unit/
```

## 👥 Team Setup

### Git Configuration

**Branch Strategy**
```bash
# Create development branch
git checkout -b develop

# Feature branch example
git checkout -b feature/user-authentication
git checkout -b feature/analytics-dashboard
```

**Commit Message Convention**
```bash
# Format: type(scope): description
git commit -m "feat(user-mgmt): add password reset functionality"
git commit -m "fix(analytics): resolve data processing error"
git commit -m "docs(deployment): update Docker configuration guide"
```

### Team Collaboration

**Project Management Setup**
```bash
# Each team member should set up their isolated work areas
cd apps/user_management
echo "- [ ] My assigned task" >> todos/000-master.md
echo "# My Architecture Decision" > adr/002-my-decision.md
```

**Avoiding Conflicts**
- Work in separate app directories (`apps/user_management/`, `apps/analytics/`, etc.)
- Use isolated project management (`adr/`, `todos/`, `mistakes/` within each app)
- Coordinate cross-app work through `solutions/` layer

## 🧪 First Development Steps

### 1. Explore Example Applications

**User Management App**
```bash
cd apps/user_management

# Review the structure
ls -la

# Check existing workflows
ls -la workflows/

# Run existing tests
pytest tests/unit/
```

**Analytics App**
```bash
cd apps/analytics

# Understand the data processing patterns
# Review SDK integration examples
```

### 2. Create Your First App

**Copy Template**
```bash
# Copy the app template
cp -r apps/_template apps/my_first_app
cd apps/my_first_app

# Customize configuration
# 1. Edit setup.py - change app name and description
# 2. Edit config.py - update app_name
# 3. Edit README.md - replace template content
```

**Install Your App**
```bash
# Install in development mode
pip install -e .

# Verify installation
python -c "from my_first_app.core.models import BaseModel; print('App created successfully')"
```

### 3. Build Your First Workflow

**Create Simple Workflow**
```python
# apps/my_first_app/workflows/hello_workflow.py
from kailash import Workflow
from kailash.nodes.code import PythonCodeNode

class HelloWorkflow(Workflow):
    def __init__(self):
        super().__init__("hello_workflow")
        
        # Simple hello world node
        self.hello_node = PythonCodeNode.from_function(
            name="hello",
            func=lambda: {"message": "Hello from my first app!"}
        )
    
    def execute(self, inputs=None):
        from kailash.runtime import LocalRuntime
        runtime = LocalRuntime()
        return runtime.execute(self, inputs or {})
```

**Test Your Workflow**
```bash
# Test the workflow
python -c "
from my_first_app.workflows.hello_workflow import HelloWorkflow
workflow = HelloWorkflow()
result = workflow.execute()
print('Workflow result:', result)
"
```

## 📖 Next Steps

### Essential Reading
1. **[Architecture Overview](architecture-overview.md)** - Understand the project design
2. **[App Development Guide](../../apps/APP_DEVELOPMENT_GUIDE.md)** - Build individual applications
3. **[SDK Developer Guide](../../sdk-users/developer/README.md)** - Master the Kailash SDK
4. **[Multi-App Coordination](multi-app-coordination.md)** - Coordinate multiple applications

### Development Path
1. **Week 1**: Set up environment, explore existing apps
2. **Week 2**: Create first custom app using template
3. **Week 3**: Integrate multiple apps using solutions layer
4. **Week 4**: Deploy to staging and production environments

### Key Skills to Develop
- **Kailash SDK**: Node usage, workflow design, runtime configuration
- **FastAPI**: API development, routing, middleware
- **Docker**: Containerization, compose, orchestration
- **Testing**: Unit, integration, functional, e2e testing

## 🛟 Getting Help

### Common Issues
- **Import Errors**: Ensure you've installed the project with `pip install -e .`
- **Database Issues**: Check your `.env` file and database configuration
- **SDK Errors**: Review `sdk-users/developer/07-troubleshooting.md`

### Support Resources
- **Project Issues**: [Troubleshooting Guide](troubleshooting.md)
- **SDK Issues**: [SDK Troubleshooting](../../sdk-users/developer/07-troubleshooting.md)
- **Team Coordination**: [Team Workflows](team-workflows.md)

### Development Community
- Check existing `mistakes/` folders for lessons learned
- Review ADRs for architectural decisions
- Use project TODOs for coordination

---

**You're now ready to start building enterprise applications with the Kailash SDK! Focus on exploring the existing examples first, then gradually build your own applications following the established patterns.**