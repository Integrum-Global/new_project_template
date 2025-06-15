# App Template

This is a template for creating new client applications. Copy this entire folder to start a new app.

## Quick Start

```bash
# Copy template to create new app
cp -r apps/_template apps/my_new_app
cd apps/my_new_app

# Customize for your app
# 1. Edit this README.md
# 2. Update setup.py
# 3. Modify config.py
# 4. Start development
```

## Template Structure

```
_template/
├── README.md          # App overview (edit this!)
├── __init__.py        # App package initialization
├── config.py          # App configuration
├── setup.py           # Package setup (edit app name!)
├── core/              # Business logic
│   ├── __init__.py
│   ├── models.py      # Data models
│   └── services.py    # Business services
├── api/               # REST API
│   ├── __init__.py
│   └── main.py        # FastAPI application
├── cli/               # Command line interface
│   ├── __init__.py
│   └── main.py        # CLI commands
├── workflows/         # Kailash SDK workflows
│   ├── __init__.py
│   └── example.py     # Example workflow
├── tests/             # App tests
│   ├── __init__.py
│   ├── unit/
│   ├── integration/
│   ├── functional/
│   └── e2e/
├── docs/              # App documentation
│   └── README.md
├── adr/               # Architecture decisions
│   ├── README.md
│   └── 001-template.md
├── todos/             # Task tracking
│   ├── README.md
│   ├── 000-master.md
│   └── template.md
└── mistakes/          # Learning from errors
    ├── README.md
    ├── 000-master.md
    └── template.md
```

## Development Workflow

### 1. Setup
```bash
# Install your app in development mode
pip install -e .

# Initialize your app's project management
echo "# Initial Architecture\n\nFirst architecture decisions for my_new_app" > adr/001-initial-setup.md
echo "- [ ] Define core models" > todos/000-master.md
echo "- [ ] Set up API structure" >> todos/000-master.md
```

### 2. Development
- Use `core/` for business logic and data models
- Use `workflows/` for Kailash SDK workflow implementations  
- Use `api/` for REST API endpoints
- Use `cli/` for command-line interface

### 3. Testing
```bash
# Run your app's tests
pytest tests/

# Different test types
pytest tests/unit/         # Fast unit tests
pytest tests/integration/  # Component interaction
pytest tests/functional/   # Feature tests
pytest tests/e2e/          # End-to-end scenarios
```

### 4. Documentation
- Keep app overview in this README.md
- Document architecture decisions in `adr/`
- Track tasks and progress in `todos/`
- Record learnings and fixes in `mistakes/`

## App Metadata

Update this section for your app:

- **App Name**: my_new_app (CHANGE THIS)
- **Purpose**: What this app does (CHANGE THIS)
- **Owner**: Your name/team (CHANGE THIS)
- **Created**: YYYY-MM-DD (CHANGE THIS)
- **Status**: Development

## Next Steps

1. **Rename**: Change all references from "_template" to your app name
2. **Customize**: Update setup.py with your app details
3. **Develop**: Start building your core models and workflows
4. **Test**: Write tests as you develop
5. **Document**: Keep your documentation updated

---

*Remember: This app is isolated - you can work on it without conflicts with other teams working on other apps!*