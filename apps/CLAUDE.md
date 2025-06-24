# Kailash Apps - Quick Navigation

## 🏗️ Architecture Decisions

**For app building guidance:** → [../sdk-users/decision-matrix.md](../sdk-users/decision-matrix.md)

**Before any app implementation:**
1. Enter `sdk-users/` directory to load full architectural guidance
2. Check decision matrix for patterns and trade-offs
3. Reference complete app guide as needed

## 🚨 IMPORTANT: App Structure Convention

**All app-specific content MUST be contained within the app folder:**
- ✅ `apps/my_app/workflows/` - App workflows
- ✅ `apps/my_app/tests/` - App tests
- ✅ `apps/my_app/docs/` - App documentation
- ❌ `sdk-users/workflows/` - For SDK examples only
- ❌ `tests/` - For SDK core tests only
- ❌ `examples/` - For SDK feature examples only

**Test Organization per App:**
```
apps/my_app/tests/
├── unit/           # Fast, isolated component tests
├── integration/    # Component interaction tests
├── functional/     # Feature & workflow tests
├── e2e/           # End-to-end user scenarios
├── performance/    # Load & benchmark tests
├── conftest.py    # Shared fixtures
└── README.md      # Test documentation
```

**Documentation Principle:**
- Generic SDK patterns → `/apps/` root
- App-specific features → Each app's folder
- SDK examples → `sdk-users/workflows/`
- SDK tests → `tests/`

## 🎯 Architecture Decision

**Choose Pattern:**
1. **Simple** (<5 workflows) → Inline construction
2. **Complex** (>10 workflows) → Class-based
3. **High-Perf** (<25ms) → Hybrid routing
4. **Default** → MCP routing with LLM support

**Never:**
- Create FastAPI manually → Use `create_gateway()`
- Write SQLAlchemy models → Extend middleware bases
- Implement auth → Use enterprise auth stack

## ⚡ Performance Targets

- API Response: <100ms (achieved: 45ms)
- User Operations: <200ms
- Auth Check: <15ms
- Concurrent Users: 500+
- Success Rate: 100%
