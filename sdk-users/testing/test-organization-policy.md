# Test Organization Policy

This document defines the test organization standards for the Kailash SDK. It should be read together with [regression-testing-strategy.md](regression-testing-strategy.md).

## ⚠️ Ensure No Hidden Tests

Strict tier enforcement - if a test needs sleep/delays or takes >1s, it MUST be moved to the appropriate tier where it will actually run.

## Directory Structure

All tests MUST be organized into the following three-tier structure:

```
tests/
├── unit/           # Tier 1: Fast, isolated tests
├── integration/    # Tier 2: Component interaction tests
├── e2e/           # Tier 3: End-to-end scenarios
├── utils/          # Test utilities (docker_config.py, setup scripts)
├── fixtures/       # Shared test data
├── infrastructure/ # Infrastructure tests (optional, for testing deployments)
└── conftest.py    # Global pytest configuration
```

## Test Classification Rules

### Tier 1: Unit Tests (`tests/unit/`)
- **Execution time**: < 1 second per test
- **Dependencies**: NONE (no Docker, Redis, Ollama, PostgreSQL)
- **Markers**: `@pytest.mark.unit` or no markers
- **Purpose**: Test individual components in isolation
- **CI/CD**: Run on every commit
- **STRICT RULES**: 
  - ❌ NO `@pytest.mark.slow` allowed - will fail in CI
  - ❌ NO sleep/delays allowed - will fail in CI
  - ✅ If test needs delays, move to integration/ or e2e/

### Tier 2: Integration Tests (`tests/integration/`)
- **Execution time**: < 30 seconds per test
- **Dependencies**: MUST use REAL Docker services (PostgreSQL, Redis, Ollama)
- **Markers**: `@pytest.mark.integration`
- **Purpose**: Test component interactions with REAL infrastructure
- **CI/CD**: Run on every PR
- **CRITICAL**: NO MOCKING ALLOWED - Use real Docker services via tests/utils/docker_config.py

### Tier 3: E2E Tests (`tests/e2e/`)
- **Execution time**: Any duration
- **Dependencies**: MUST use REAL Docker services (PostgreSQL, Redis, Ollama)
- **Markers**: `@pytest.mark.e2e`, `@pytest.mark.slow`, `@pytest.mark.requires_*`
- **Purpose**: Test complete business scenarios with REAL infrastructure
- **CI/CD**: Run nightly or on release
- **CRITICAL**: NO MOCKING ALLOWED - Use real Docker services via tests/utils/docker_config.py

## File Organization Rules

### 1. NO Scattered Test Files
- ❌ Never place test files directly in `tests/`
- ❌ Never create `test_*` directories outside the tier structure
- ✅ All test files must be in `unit/`, `integration/`, or `e2e/`

### 2. Mirror Source Structure
Tests should mirror the source code structure:
```
src/kailash/nodes/ai/llm_agent.py → tests/unit/nodes/ai/test_llm_agent.py
src/kailash/runtime/local.py      → tests/unit/runtime/test_local.py
```

### 3. Comprehensive Tests
If a test covers multiple components or real-world scenarios:
- Unit version → `tests/unit/component/test_feature.py`
- Integration version → `tests/integration/component/test_feature_comprehensive.py`
- E2E version → `tests/e2e/test_feature_real_world.py`

## Critical Testing Rules

### NO MOCKING IN INTEGRATION AND E2E TESTS

**This is a MANDATORY rule for Tier 2 (Integration) and Tier 3 (E2E) tests:**

1. **Integration Tests (`tests/integration/`)** - MUST use REAL Docker services
   - ✅ Use real PostgreSQL via `tests/utils/docker_config.py`
   - ✅ Use real Redis via `tests/utils/docker_config.py`
   - ✅ Use real Ollama for LLM testing
   - ❌ NEVER mock database connections
   - ❌ NEVER use `unittest.mock` or `patch` for infrastructure
   - ❌ NEVER use fake/in-memory databases

2. **E2E Tests (`tests/e2e/`)** - MUST use REAL Docker services
   - Same rules as integration tests
   - Test complete workflows with real data

3. **Only Unit Tests (`tests/unit/`)** may use mocks
   - This is the ONLY place where mocking is allowed
   - Mock external dependencies to test in isolation

**Example of CORRECT Integration Test:**
```python
# tests/integration/test_admin_nodes.py
from tests.utils.docker_config import get_postgres_connection_string

class TestAdminIntegration:
    def test_user_creation(self):
        # CORRECT: Using real database
        db_config = {
            "connection_string": get_postgres_connection_string(),
            "database_type": "postgresql"
        }
        user_mgmt = UserManagementNode()
        result = user_mgmt.run(database_config=db_config, ...)
```

**Example of INCORRECT Integration Test:**
```python
# WRONG - Never do this in integration tests!
from unittest.mock import patch

class TestAdminIntegration:
    @patch("database.connect")  # ❌ NO MOCKING!
    def test_user_creation(self, mock_db):
        ...
```

## Prohibited Patterns

### 1. Duplicate Test Directories
Never create these directories:
- `tests/test_*` (e.g., `tests/test_workflow/`)
- `tests/middleware/`, `tests/nodes/`, etc. (use `tests/unit/middleware/`)
- Any test directory outside the three-tier structure

### 2. Misclassified Tests
- Never put slow tests in `unit/`
- Never put Docker-dependent tests in `unit/` or unmarked `integration/`
- Always use appropriate pytest markers

### 3. Scattered Test Support Files
Keep test support files organized:
- Test utilities & configs → `tests/utils/`
- Shared fixtures → `tests/fixtures/`
- Infrastructure tests → `tests/infrastructure/` (if testing deployments)

## Test Markers

### New Marker Strategy

```python
# Speed markers (for scheduling, not exclusion)
@pytest.mark.fast     # <1s - quick feedback
@pytest.mark.medium   # 1-30s - pre-commit  
@pytest.mark.slow     # >30s - nightly runs

# Priority markers
@pytest.mark.critical    # Must always pass
@pytest.mark.regression  # Previously broken areas

# Dependency markers
@pytest.mark.requires_docker
@pytest.mark.requires_postgres
@pytest.mark.requires_redis
@pytest.mark.requires_ollama
```

### Examples by Tier

```python
# Unit test (Tier 1) - MUST be fast, no slow marker
def test_simple_function():
    assert calculate(2, 2) == 4

# Integration test (Tier 2) - can be marked medium/slow
@pytest.mark.integration
@pytest.mark.medium
@pytest.mark.requires_postgres
def test_database_integration():
    # Uses real PostgreSQL
    pass

# E2E test (Tier 3) - typically slow
@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.requires_docker
def test_full_workflow():
    # Complete scenario with real services
    pass
```

## Migration Checklist

When adding or moving tests:

1. **Determine the correct tier** based on dependencies and execution time
2. **Use the appropriate directory** (`unit/`, `integration/`, or `e2e/`)
3. **Mirror the source structure** for easy navigation
4. **Add proper markers** for classification
5. **Remove any duplicate** or misplaced versions
6. **Update imports** if moving existing tests

## Essential Files Only

The `tests/` directory should contain ONLY:
- `unit/`, `integration/`, `e2e/` directories
- `conftest.py` - Global pytest configuration
- `utils/` - Test utilities and configuration (docker_config.py, setup scripts)
- `fixtures/` - Shared test fixtures
- `infrastructure/` - Infrastructure tests (optional)
- `README.md` - Test suite documentation
- `CLAUDE.md` - AI assistant instructions

All other files should be removed or properly organized.

## Enforcement

This policy is enforced through:

### 1. Automated Enforcement (conftest.py)
- Unit tests with `@pytest.mark.slow` → Test fails with error
- Unit tests with sleep/delays → Test fails with error  
- Integration/E2E tests with mocking → Test fails with error
- Run with `--strict-test-organization` to enforce in CI

### 2. Test Audit Script
```bash
# Run audit to find violations
python scripts/audit_test_organization.py

# Output includes:
# - Unit tests with sleep/delays
# - Unit tests marked as slow
# - Integration tests using mocks
# - Tests in wrong directories
```

### 3. CI Pipeline Stages
```bash
# Stage 1: Fast feedback (every commit)
pytest tests/unit/ -m "not (requires_docker or requires_*)"

# Stage 2: Pre-merge (every PR)  
pytest tests/unit/ tests/integration/ -m "not (slow and not critical)"

# Stage 3: Nightly (all tests)
pytest  # Runs EVERYTHING, no exclusions
```

### 4. Migration Process
For tests identified as violations:
1. **Refactor to be fast** - Remove sleeps, reduce data
2. **Move to correct tier** - Integration or E2E if needs delays
3. **Split into versions** - Fast unit + slow integration
