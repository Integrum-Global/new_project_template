# Testing Guidelines for Claude Code

## ⚠️ Critical Update: All Tests Must Run

**Previous Issue**: Tests marked `@pytest.mark.slow` in unit/ were excluded from CI, becoming hidden "zombie tests".

**New Approach**: Strict tier enforcement - every test runs in the appropriate pipeline stage.

## Essential Reading
1. **[regression-testing-strategy.md](regression-testing-strategy.md)** - Three-tier testing approach with new pipeline stages
2. **[test-organization-policy.md](test-organization-policy.md)** - Strict test organization rules with enforcement

## Quick Reference

### Test Structure
```
tests/
├── unit/           # Tier 1: Fast, no dependencies
├── integration/    # Tier 2: Component interactions
├── e2e/           # Tier 3: Full scenarios with Docker
└── conftest.py    # Global configuration
```

### Running Tests by Pipeline Stage
```bash
# Stage 1: Fast Feedback (every commit)
pytest tests/unit/ -m "not (requires_docker or requires_postgres or requires_mysql or requires_redis or requires_ollama)"

# Stage 2: Pre-merge (every PR)
pytest tests/unit/ tests/integration/ -m "not (slow and not critical)"

# Stage 3: Full Regression (nightly/release)
pytest  # ALL tests, no exclusions
```

### Audit and Enforcement
```bash
# Find test violations
python scripts/audit_test_organization.py

# Track which tests run where
python scripts/test_inventory_tracker.py

# Enforce strict organization
pytest --strict-test-organization
```

### Key Rules
1. **NO scattered test files** - Everything must be in unit/, integration/, or e2e/
2. **Mirror source structure** - `src/kailash/nodes/ai/` → `tests/unit/nodes/ai/`
3. **Use proper markers** - `@pytest.mark.integration`, `@pytest.mark.requires_docker`
4. **Keep tests fast** - Unit tests < 1s, Integration < 30s
5. **NO MOCKING in Tier 2/3** - Integration and E2E tests MUST use REAL Docker services
   - ❌ NEVER mock databases in integration/
   - ❌ NEVER use patch/Mock in e2e/
   - ✅ Use real PostgreSQL, Redis, Ollama via tests/utils/docker_config.py

### When Writing Tests
- **Unit tests**: Test one component, mock all dependencies (ONLY place mocking is allowed)
- **Integration tests**: Test component interactions with REAL Docker services (NO MOCKING)
- **E2E tests**: Test complete scenarios with REAL Docker services (NO MOCKING)

### Common Mistakes to Avoid
- ❌ Creating `tests/test_*` directories
- ❌ Putting slow tests in unit/
- ❌ Forgetting Docker requirement markers
- ❌ Duplicating tests across tiers
- ✅ Always organize by tier and component
