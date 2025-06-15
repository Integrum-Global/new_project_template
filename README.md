# Client Project Template

A comprehensive template for client projects using the [Kailash Python SDK](https://pypi.org/project/kailash/) to build enterprise applications and cross-app orchestration solutions.

## 🎯 What This Template Provides

This template gives you everything needed to build enterprise applications for your clients:

- **📱 Self-Contained Apps**: Each app has isolated project management (no merge conflicts)
- **🔄 Cross-App Orchestration**: Solutions layer for coordinating multiple apps  
- **📚 SDK Guidance**: Curated documentation and examples from the Kailash team
- **🏗️ Production Ready**: Enterprise patterns, monitoring, and deployment setup
- **👥 Multi-Developer**: Designed for teams working on different apps simultaneously

## 🚀 Quick Start

### 1. Create Your Project
```bash
# Use this template to create a new client project
git clone <your-template-repo> my-client-project
cd my-client-project

# Install the Kailash SDK from PyPI
pip install kailash

# Set up your environment
cp .env.template .env
# Edit .env with your project-specific settings
```

### 2. Try the Centralized Deployment (NEW!)
```bash
# Start the entire platform with one command
./deployment/scripts/start.sh

# Access the unified gateway
curl http://localhost:8000/api/v1/discovery
curl http://localhost:8000/api/v1/tools

# Stop when done
./deployment/scripts/stop.sh
```

### 3. Create Your First App
```bash
# Copy the app template
cp -r apps/_template apps/my_first_app
cd apps/my_first_app

# Customize for your app
# 1. Edit setup.py (change app name, description)
# 2. Update README.md
# 3. Modify config.py with your settings
# 4. Update manifest.yaml with your app's capabilities

# Install your app
pip install -e .
```

### 4. Start Development
```bash
# Your app has isolated project management
echo "# Initial Architecture Decision" > adr/001-app-setup.md
echo "- [ ] Set up core models" > todos/000-master.md
echo "- [ ] Implement main workflows" >> todos/000-master.md

# Start building with the Kailash SDK
# See sdk-users/ for complete guidance and examples
```

## 📁 Project Structure

```
my-client-project/
├── apps/                      # Client applications (self-contained)
│   ├── _template/             # Template for new apps
│   ├── user_management/       # Example: Enterprise user management
│   ├── analytics/             # Example: Data analytics dashboard
│   └── document_processor/    # Example: Document processing pipeline
│
├── solutions/                 # Cross-app orchestration
│   ├── tenant_orchestration/  # Multi-app workflows
│   ├── shared_services/       # Common services (auth, caching, etc.)
│   ├── data_integration/      # Cross-app data flows
│   └── monitoring/            # System-wide monitoring
│
├── sdk-users/                 # Kailash SDK guidance (from Kailash team)
│   ├── developer/             # Development patterns and guides
│   ├── workflows/             # Production workflow examples
│   ├── essentials/            # Quick reference and cheatsheets
│   └── templates/             # Starter templates
│
├── infrastructure/            # Deployment and DevOps
│   ├── docker/                # Container configurations
│   ├── kubernetes/            # K8s manifests (if needed)
│   └── scripts/               # Setup and deployment scripts
│
└── data/                      # Project data
    ├── inputs/                # Sample/test data
    ├── outputs/               # Generated results
    └── configs/               # Configuration files
```

## 🏗️ Building Applications

### App Development Workflow

1. **Copy Template**: Start with `apps/_template/`
2. **Customize**: Update setup.py, README.md, config.py  
3. **Develop**: Build using Kailash SDK patterns
4. **Test**: Use isolated testing in `apps/my_app/tests/`
5. **Document**: Track in `apps/my_app/adr/`, `todos/`, `mistakes/`

### Example Apps Included

#### **User Management** (`apps/user_management/`)
- Enterprise authentication (SSO, MFA, passwordless)
- AI-powered ABAC authorization  
- Real-time WebSocket updates
- Performance: 15.9x faster than Django Admin

#### **Analytics Dashboard** (`apps/analytics/`)
- Real-time data processing pipelines
- Interactive dashboards with visualizations
- Multi-tenant data isolation
- Scheduled reporting automation

#### **Document Processor** (`apps/document_processor/`)
- AI-powered document analysis
- Batch and real-time processing
- Multiple format support (PDF, Word, Excel)
- Workflow automation for document lifecycle

### Creating Custom Apps

```bash
# Start with the template
cp -r apps/_template apps/my_custom_app
cd apps/my_custom_app

# Essential customizations
1. Edit setup.py:
   - Change 'name' from "my-template-app" to "my-custom-app"
   - Update description and author
   - Add app-specific dependencies

2. Update config.py:
   - Change app_name from "my_template_app" to "my_custom_app"  
   - Add your app-specific configuration

3. Edit README.md:
   - Replace template content with your app description
   - Update all references from "template" to your app name

# Install and start developing
pip install -e .
```

## 🔄 Cross-App Orchestration

Use the `solutions/` folder for coordinating multiple apps:

### Tenant Orchestration
```python
# solutions/tenant_orchestration/user_onboarding.py
from apps.user_management.workflows import CreateUserWorkflow
from apps.analytics.workflows import SetupUserTrackingWorkflow

def complete_user_onboarding(user_data):
    # Coordinate across multiple apps
    user = CreateUserWorkflow().execute(user_data)
    SetupUserTrackingWorkflow().execute(user.id)
    return user
```

### Shared Services
```python
# solutions/shared_services/authentication.py
class TenantAuthService:
    def authenticate_across_apps(self, token):
        # Single sign-on across all apps
        user = self.verify_token(token)
        self.track_login(user.id)
        return user
```

## 👥 Multi-Developer Workflow

### Conflict Prevention
- ✅ **Each app has isolated project management** (`adr/`, `todos/`, `mistakes/`)
- ✅ **Teams work in separate app folders**
- ✅ **No shared files that everyone modifies**
- ✅ **Clear ownership boundaries**

### Team Coordination
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

## 📚 SDK Guidance

The `sdk-users/` folder contains curated guidance from the Kailash team:

- **Getting Started**: `sdk-users/developer/01-node-basics.md`
- **Quick Reference**: `sdk-users/essentials/cheatsheet/`
- **Production Workflows**: `sdk-users/workflows/by-pattern/`
- **Node Catalog**: `sdk-users/nodes/comprehensive-node-catalog.md`

## 🚢 Centralized Deployment Architecture

This template includes a **centralized deployment system** that unifies traditional APIs and MCP servers through an enterprise gateway with service discovery.

### ✨ Features
- **🔍 Auto-Discovery**: Apps declare capabilities in `manifest.yaml`
- **🔗 Unified Gateway**: Single entry point for all services
- **📊 Tool Aggregation**: Combines MCP tools from multiple apps
- **🏥 Health Monitoring**: Real-time service health and metrics
- **🐳 Multi-Platform**: Docker, Kubernetes, and Helm support

### Quick Deployment
```bash
# Start entire platform
./deployment/scripts/start.sh

# Access unified services
curl http://localhost:8000/api/v1/discovery  # Service discovery
curl http://localhost:8000/api/v1/tools      # Aggregated tools
curl http://localhost:8000/docs              # API documentation

# Stop when done
./deployment/scripts/stop.sh
```

### Production Deployment
```bash
# Docker Compose
cd deployment/docker && docker-compose up -d

# Kubernetes
cd deployment/kubernetes
kubectl apply -f infrastructure/
kubectl apply -f apps/

# Helm Charts
cd deployment/helm && helm install mcp-platform .
```

### Adding New Apps
1. Create app with `manifest.yaml`
2. Gateway automatically discovers it
3. Tools appear in unified catalog
4. No manual configuration required!

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for complete details.

## 🛡️ Security & Best Practices

- **Environment Variables**: Use `.env` files for configuration
- **Database Security**: Connection strings in environment variables
- **API Security**: JWT authentication across all apps
- **Audit Logging**: Centralized logging in `solutions/monitoring/`
- **Access Control**: RBAC/ABAC patterns from SDK examples

## 📊 Monitoring & Observability

- **App Health**: Each app exposes `/health` endpoint
- **Metrics**: Prometheus metrics collection
- **Logging**: Centralized logging with structured logs
- **Tracing**: Cross-app request tracing
- **Alerts**: Grafana dashboards and alerting

## 🆘 Support & Documentation

### Getting Help
1. **Check SDK Guidance**: `sdk-users/developer/07-troubleshooting.md`
2. **Search Mistakes**: `apps/my_app/mistakes/000-master.md`
3. **Review Examples**: `sdk-users/workflows/by-pattern/`
4. **Contact Kailash Team**: support@kailash.dev

### Documentation
- **App Development**: `apps/APP_DEVELOPMENT_GUIDE.md`
- **Cross-App Patterns**: `solutions/README.md`
- **SDK Reference**: `sdk-users/developer/QUICK_REFERENCE.md`

## 🎯 Next Steps

1. **Read the Guides**:
   - `apps/APP_DEVELOPMENT_GUIDE.md` - How to build apps
   - `solutions/README.md` - Cross-app coordination
   - `sdk-users/developer/README.md` - SDK usage patterns

2. **Study the Examples**: 
   - Explore `apps/user_management/` for enterprise patterns
   - Check `apps/analytics/` for data processing
   - Review `solutions/` for cross-app coordination

3. **Start Building**:
   - Copy `apps/_template/` to create your first app
   - Follow the SDK patterns in `sdk-users/`
   - Use isolated project management to avoid conflicts

4. **Deploy with Confidence**:
   - Use the infrastructure setup in `infrastructure/`
   - Follow deployment patterns from example apps
   - Monitor with built-in observability tools

---

**Built for enterprise clients who need powerful, scalable applications with the flexibility of the Kailash SDK and the reliability of production-tested patterns.**