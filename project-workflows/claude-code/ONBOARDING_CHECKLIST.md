# ✅ Solution Developer Onboarding Checklist

Complete this checklist to ensure you're ready to build solutions with Claude Code and the Kailash SDK.

## 📅 Day 1: Environment Setup

### Prerequisites
- [ ] **Python 3.11+** installed
- [ ] **uv** package manager installed
- [ ] **Git** configured
- [ ] **Claude Code** access (browser or app)
- [ ] **IDE** (VS Code, PyCharm, etc.)

### Project Setup
```bash
# 1. Clone the repository
git clone <your-repo-url>
cd <project-name>

# 2. Install dependencies with uv
uv sync

# 3. Verify installation
uv run python --version
uv run python -c "import kailash; print('Kailash SDK imported successfully')"
```

### Directory Understanding
- [ ] **Locate** `sdk-users/` (READ-ONLY reference)
- [ ] **Find** `src/solutions/` (your code goes here)
- [ ] **Check** `todos/` (task tracking)
- [ ] **Review** `prd/` (business requirements)
- [ ] **Understand** `adr/` (architecture decisions)

### First Claude Code Interaction
- [ ] Open Claude Code
- [ ] Try: `"Hello, I'm setting up my development environment for Kailash SDK solutions"`
- [ ] Verify Claude Code understands the project structure
- [ ] Test: `"Show me the structure of src/solutions/"`

## 📅 Day 2: Learn the Patterns

### Explore SDK Documentation (Read-Only!)
```
# DO NOT EDIT these files - just read and reference
sdk-users/
├── workflows/     # Complete workflow examples
├── essentials/    # Quick reference guides
├── templates/     # Starter code patterns
├── nodes/         # Node documentation
└── developer/     # Development guides
```

### Practice with Claude Code
Try these conversations:
- [ ] "Show me a basic ETL workflow pattern from sdk-users"
- [ ] "How do I process CSV files using Kailash nodes?"
- [ ] "What's the best pattern for API integration?"
- [ ] "Help me understand DataTransformer node"

### Understand Solution Structure
```
src/solutions/your_module/
├── __init__.py
├── config.py         # Configuration
├── workflows/        # Your workflow implementations
├── nodes/           # Custom nodes (if needed)
├── examples/        # Working examples
└── tests/          # Your tests
```

## 📅 Day 3: First Solution

### Get Your First Task
```
"I'm ready to build my first solution. What should I work on?"
```

### Understand Requirements
- [ ] **Read** business requirements in `prd/`
- [ ] **Ask** Claude Code to explain the requirements
- [ ] **Identify** which SDK patterns apply
- [ ] **Plan** your implementation approach

### Start Building
```
"Help me create a solution for [requirement]. Guide me through:
1. Setting up the module structure
2. Choosing the right nodes
3. Implementing the workflow
4. Testing the solution"
```

### Implementation Checklist
- [ ] Create module in `src/solutions/`
- [ ] Implement workflow using SDK patterns
- [ ] Add configuration in `config.py`
- [ ] Create working example
- [ ] Write basic tests
- [ ] Document your decisions

## 📅 Week 1: Full Workflow

### Daily Habits
- [ ] **Morning**: Start session with Claude Code
- [ ] **Planning**: Review requirements and get guidance
- [ ] **Implementation**: Build with AI assistance
- [ ] **Testing**: Validate your solution works
- [ ] **Evening**: Update progress and document

### Solution Development Skills
- [ ] **Pattern Recognition**: Find relevant examples in `sdk-users/`
- [ ] **Node Selection**: Choose appropriate Kailash nodes
- [ ] **Workflow Design**: Connect nodes effectively
- [ ] **Error Handling**: Implement robust solutions
- [ ] **Testing**: Ensure solution meets requirements

### Documentation Practice
- [ ] **Architecture Decisions**: Document in `adr/`
- [ ] **Mistakes & Learnings**: Track in `mistakes/`
- [ ] **Progress Updates**: Through Claude Code
- [ ] **Code Comments**: Explain complex logic

## 🔧 Validation Checklist

### Run Environment Check
```bash
# Create validation script
cat > validate_setup.sh << 'EOF'
#!/bin/bash
echo "🔍 Validating Solution Development Setup"
echo "========================================"

# Check Python
echo -n "Python 3.11+: "
if python --version | grep -E "3\.(1[1-9]|[2-9][0-9])" > /dev/null; then
    echo "✅ $(python --version)"
else
    echo "❌ Wrong version"
fi

# Check uv
echo -n "uv installed: "
if command -v uv > /dev/null; then
    echo "✅ $(uv --version)"
else
    echo "❌ Not found"
fi

# Check Kailash
echo -n "Kailash SDK: "
if python -c "import kailash" 2>/dev/null; then
    echo "✅ Installed"
else
    echo "❌ Not installed"
fi

# Check directories
echo -n "Project structure: "
if [ -d "sdk-users" ] && [ -d "src/solutions" ]; then
    echo "✅ Correct"
else
    echo "❌ Missing directories"
fi

echo ""
echo "Ready to build solutions!"
EOF

chmod +x validate_setup.sh
./validate_setup.sh
```

## 🚨 Common Setup Issues

### Issue: "Can't import kailash"
**Solution**: Run `uv sync` to install dependencies

### Issue: "Python version too old"
**Solution**: Install Python 3.11+ and update your PATH

### Issue: "Can't find sdk-users/"
**Solution**: Make sure you're in the project root directory

### Issue: "Claude Code doesn't understand project"
**Solution**: Provide more context about using Kailash SDK

## 📝 Before You Start Building

### Understand the Rules
- [ ] `sdk-users/` is READ-ONLY (never edit!)
- [ ] All code goes in `src/solutions/`
- [ ] Use Claude Code for all guidance
- [ ] Update progress conversationally
- [ ] Document decisions and learnings

### Know Your Resources
- [ ] SDK patterns in `sdk-users/workflows/`
- [ ] Quick guides in `sdk-users/essentials/`
- [ ] Node docs in `sdk-users/nodes/`
- [ ] Templates in `sdk-users/templates/`

### Ready to Build?
- [ ] Environment validated
- [ ] Understand project structure
- [ ] Practiced with Claude Code
- [ ] Know where to find patterns
- [ ] Ready to implement solutions

## 🎉 Onboarding Complete!

Once all boxes are checked:
```
"I've completed onboarding. Environment is set up, I understand the structure, and I'm ready to build solutions."
```

### Next Steps
1. Get your first requirement
2. Design solution with Claude Code
3. Implement using SDK patterns
4. Test and validate
5. Document and deliver

## 📞 Getting Help

### If Stuck
1. Ask Claude Code for help
2. Review SDK documentation
3. Check common mistakes
4. Contact project lead

### Useful Prompts
- "Explain this SDK pattern to me"
- "Help me debug this error"
- "Is this the right approach?"
- "Review my implementation"

---

*Welcome to solution development with Kailash SDK! Let Claude Code be your guide.*
