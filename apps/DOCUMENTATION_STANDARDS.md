# Kailash Apps Documentation Standards

This document defines the documentation standards for all Kailash SDK applications to ensure consistency and quality.

## 📚 Documentation Structure

Every Kailash app should follow this structure:

```
apps/app-name/
├── README.md                    # Main entry point
├── docs/
│   ├── README.md               # Documentation hub
│   ├── getting-started/
│   │   ├── quickstart.md       # 5-minute guide
│   │   ├── installation.md     # Setup instructions
│   │   └── concepts.md         # Core concepts
│   ├── development/            # Development guides
│   ├── production/             # Deployment guides
│   ├── reference/              # API/CLI reference
│   └── architecture/           # Technical details
├── examples/                   # Working examples
├── tests/                      # Test suite
└── validate_docs.py           # Doc validation script
```

## 🎯 README.md Standards

### Structure
1. **Title & Tagline** - Clear, benefit-focused
2. **Badges** - Tests, License, SDK version
3. **Quick Start** - 60-second to first success
4. **Key Features** - What makes it unique
5. **Documentation Links** - Well organized
6. **Architecture** - Simple ASCII diagram
7. **Examples** - Real-world use cases
8. **Testing** - Current status
9. **Contributing** - How to help
10. **Support** - Where to get help

### Example Template
```markdown
# App Name

**Tagline** - What problem it solves

[![Tests](https://img.shields.io/badge/tests-passing-brightgreen)](tests/)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
[![SDK](https://img.shields.io/badge/built%20with-Kailash%20SDK-orange)](../README.md)

## 🚀 Quick Start (X minutes)

[Minimal code to first success]

## 🎯 What Makes [App] Different?

[3-4 key differentiators with code examples]

## 📚 Documentation

### Getting Started
- **[Quick Start](docs/getting-started/quickstart.md)** - First success
- **[Installation](docs/getting-started/installation.md)** - Setup guide
- **[Examples](examples/)** - Complete applications

[More sections...]

## 💡 Real-World Examples

[2-3 concrete use cases with code]

## 🏗️ Architecture

[ASCII diagram showing components]

## 🧪 Testing

[Test status and how to run]

---

**Built with Kailash SDK** | [Parent Project](../../README.md) | [SDK Docs](../../sdk-users/)
```

## 📖 Documentation Guidelines

### Quick Start Guide (`quickstart.md`)
1. **Prerequisites** - Minimal requirements
2. **Step-by-step tutorial** - 5-6 clear steps
3. **Working code** - Copy-paste ready
4. **Visual feedback** - Show expected output
5. **Next steps** - Where to go next
6. **Common issues** - Quick troubleshooting

### Code Examples
- ✅ **DO**: Use SDK patterns correctly
- ✅ **DO**: Show complete, working examples
- ✅ **DO**: Include expected output
- ✅ **DO**: Follow SDK naming conventions
- ❌ **DON'T**: Use mock/simplified code
- ❌ **DON'T**: Skip error handling
- ❌ **DON'T**: Use outdated patterns

### Writing Style
- **Action-oriented**: "Create", "Build", "Deploy"
- **Concise**: Get to the point quickly
- **Progressive**: Simple → Advanced
- **Visual**: Use diagrams and output examples
- **Searchable**: Clear headings and keywords

## 🔍 Documentation Validation

Every app should include `validate_docs.py` to ensure:
1. All code examples are syntactically correct
2. Imports reference actual SDK components
3. No dangerous commands in examples
4. YAML/JSON examples are valid

Run validation:
```bash
python validate_docs.py
```

## 🔗 Cross-References

### To SDK Documentation
- Reference SDK patterns: `See [SDK pattern](../../sdk-users/...)`
- Link to node docs: `Uses [NodeName](../../sdk-users/nodes/...)`
- Point to guides: `Details in [SDK guide](../../sdk-users/developer/...)`

### Between App Docs
- Link related apps: `Similar to [App](../other-app/...)`
- Share patterns: `Uses pattern from [App](../other-app/docs/...)`

## 📋 Checklist for New Apps

- [ ] README.md follows template
- [ ] docs/README.md provides navigation
- [ ] Quick start guide ≤ 5 minutes
- [ ] All code examples validated
- [ ] Architecture diagram included
- [ ] Test status documented
- [ ] Links to SDK docs work
- [ ] Examples directory has working code
- [ ] validate_docs.py passes

## 🎨 Visual Standards

### Diagrams
Use ASCII art for architecture:
```
┌─────────────────────────────────────────────────────┐
│                 Your Application                     │
├─────────────────────────────────────────────────────┤
│                   App Layer                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐         │
│  │Component1│  │Component2│  │Component3│         │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘         │
│       └──────────────┴──────────────┘               │
├─────────────────────────────────────────────────────┤
│                 Kailash SDK                         │
└─────────────────────────────────────────────────────┘
```

### Code Blocks
- Always specify language: ` ```python `
- Include comments for clarity
- Show both input and output
- Keep examples focused

## 🚀 Best Practices

1. **Start with Success**: First example should work immediately
2. **Show, Don't Tell**: Code examples > long explanations
3. **Progressive Enhancement**: Simple first, then advanced
4. **Real-World Focus**: Use practical examples
5. **Test Everything**: Validate all code snippets
6. **Keep Updated**: Review docs with each change

## 📊 Metrics

Good documentation should achieve:
- ✅ New user to first success: < 5 minutes
- ✅ Find any feature: < 30 seconds
- ✅ Code examples: 100% working
- ✅ Coverage: All features documented
- ✅ Freshness: Updated with each release

---

By following these standards, we ensure all Kailash apps provide a consistent, high-quality developer experience.
