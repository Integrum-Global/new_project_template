# Client Applications

This folder contains all applications for this client project. Each application is self-contained with its own project management to prevent merge conflicts between teams.

## 📁 Structure

```
apps/
├── README.md                  # This file - app organization guide
├── APP_DEVELOPMENT_GUIDE.md   # Complete guide for creating new apps
├── _template/                 # Template for new client apps
├── user_management/           # Reference app - enterprise user management
├── qa_testing/                # Reference app - AI-powered testing framework  
└── studio/                    # Reference app - workflow builder
```

## 🚀 Creating a New App

### 1. Copy the Template
```bash
cp -r apps/_template apps/my_new_app
cd apps/my_new_app
```

### 2. Customize Your App
```bash
# Update setup.py with your app name and details
# Edit README.md with your app description
# Modify config.py for your app settings
```

### 3. Start Development with Isolated Project Management
```bash
# Your app has its own project management - no conflicts!
echo "Initial app architecture decisions" > adr/001-app-setup.md
echo "- [ ] Set up core models" > todos/000-master.md
echo "- [ ] Implement main workflows" >> todos/000-master.md
```

## 🔧 App Structure

Each app follows this self-contained structure:

```
my_app/
├── core/              # Business logic and models
├── api/               # REST API endpoints
├── cli/               # Command-line interface
├── workflows/         # Kailash SDK workflows
├── tests/             # App-specific tests
│   ├── unit/          # Fast, isolated tests
│   ├── integration/   # Component interaction tests
│   ├── functional/    # Feature tests
│   └── e2e/           # End-to-end scenarios
├── docs/              # App-specific documentation
├── adr/               # 🔥 APP-SPECIFIC architecture decisions
├── todos/             # 🔥 APP-SPECIFIC task tracking
├── mistakes/          # 🔥 APP-SPECIFIC learnings
└── setup.py           # App package configuration
```

## 🚫 Conflict Prevention

### ✅ What Prevents Conflicts:
- Each app has isolated `adr/`, `todos/`, `mistakes/` folders
- Teams work in separate app directories
- No shared files that everyone modifies
- Clear ownership per app

### ❌ What Would Cause Conflicts:
- Global project management folders (we don't have these!)
- Shared configuration files (we avoid these)
- Cross-app dependencies (use solutions/ instead)

## 📚 Reference Apps

Study these working reference apps to learn patterns:

### **user_management/**
- Enterprise authentication (SSO, MFA, passwordless)
- AI-powered ABAC authorization
- Real-time WebSocket updates
- Performance: 15.9x faster than Django Admin

### **qa_testing/**
- AI-powered autonomous testing framework
- Auto-discovers application structure
- Generates personas and test scenarios
- 100% autonomous with AI agents

### **studio/**
- Visual workflow builder
- Real-time collaboration features
- Multi-tenant isolation
- Enterprise middleware integration

## 🔄 Cross-App Coordination

For cross-app workflows and tenant-level orchestration, see the `solutions/` folder.

## 💡 Best Practices

1. **Isolation**: Keep app-specific concerns within the app folder
2. **Documentation**: Update your app's README.md as you develop
3. **Testing**: Write tests in your app's tests/ folder
4. **Decisions**: Document architecture choices in your app's adr/ folder
5. **Tasks**: Track work in your app's todos/ folder
6. **Learning**: Document issues and solutions in your app's mistakes/ folder

---

*This structure ensures that multiple teams can work on different apps simultaneously without merge conflicts while maintaining clear project organization.*