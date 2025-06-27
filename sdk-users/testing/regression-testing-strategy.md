# Regression Testing Strategy

## ⚠️ Critical Update: All Tests Must Run

Strict tier enforcement ensures every test runs in the appropriate pipeline stage.

### Test Categories
```
tests/
├── unit/          # ~1,200 tests - Fast, isolated
├── integration/   # ~500 tests - Component interaction
└── e2e/          # ~144 tests - Full system tests
```

## Regression Testing Strategy

### 1. Test Organization Tiers

Tests are organized by directory structure:
- **Tier 1**: `tests/unit/` - Fast, isolated tests (no external dependencies)
- **Tier 2**: `tests/integration/` - Component interaction tests
- **Tier 3**: `tests/e2e/` - End-to-end scenarios with Docker

### 2. New Pipeline Strategy - Every Test Runs

#### Stage 1: Fast Feedback (2-5 minutes)
```bash
# Run on every commit - unit tests without dependencies
pytest tests/unit/ -m "not (requires_docker or requires_postgres or requires_mysql or requires_redis or requires_ollama)"
```

**Includes:**
- All unit tests (NO slow markers allowed in unit/)
- No external dependencies
- Catches logic errors immediately

#### Stage 2: Pre-Merge Validation (10-15 minutes)
```bash
# Run on every PR - unit + integration, excluding only very slow tests
pytest tests/unit/ tests/integration/ -m "not (slow and not critical)"
```

**Includes:**
- All unit tests
- All integration tests 
- Critical slow tests still run
- Uses real Docker services

#### Stage 3: Full Regression (45-60 minutes)
```bash
# Run nightly or on release - EVERYTHING
pytest
```

**Includes:**
- ALL tests - no exclusions
- Slow tests, performance tests
- Complete E2E scenarios
- Full Docker environment

### 3. Test Organization Improvements

#### A. Mark Tests by Priority
```python
# Add to critical tests
@pytest.mark.critical
def test_workflow_execution():
    """Core functionality that must never break"""
    pass

# Add to frequently broken areas
@pytest.mark.regression
def test_edge_case_handling():
    """Areas that have broken before"""
    pass
```

#### B. New Marker Philosophy
```ini
# Speed markers are for SCHEDULING, not EXCLUSION
markers =
    # Speed markers (scheduling hints)
    fast: <1s tests for quick feedback
    medium: 1-30s tests for pre-commit
    slow: >30s tests for nightly runs
    
    # Priority markers (importance)
    critical: Must pass for any release
    regression: Previously broken areas
    
    # Dependency markers (environment)
    requires_docker: Needs Docker
    requires_postgres: Needs PostgreSQL
    requires_redis: Needs Redis
    requires_ollama: Needs Ollama
```

**Key Changes:**
- `slow` marker no longer excludes tests from CI
- Speed markers help schedule when tests run
- All tests run somewhere in the pipeline

### 4. Parallel Execution Strategy

#### Local Development
```bash
# Use pytest-xdist for parallel execution
pytest -n auto --maxfail=5 -m "not slow"
```

#### CI Pipeline
```yaml
# .github/workflows/test.yml
test:
  strategy:
    matrix:
      group: [1, 2, 3, 4]
  steps:
    - run: pytest --splits 4 --group ${{ matrix.group }}
```

### 5. Smart Test Selection

#### A. Test Impact Analysis
```bash
# Run only tests affected by changes
pytest --testmon --changed
```

#### B. Dependency-based Testing
```python
# tests/conftest.py
def pytest_collection_modifyitems(items, config):
    """Run tests based on modified files"""
    changed_files = get_changed_files()

    # Map files to tests
    for item in items:
        if not affects_test(item, changed_files):
            item.add_marker(pytest.mark.skip())
```

### 6. Regression Test Checklist

#### Before Major Changes
1. **Baseline Performance**
   ```bash
   pytest --benchmark-only --benchmark-save=baseline
   ```

2. **Coverage Baseline**
   ```bash
   pytest --cov=kailash --cov-report=html
   ```

3. **Slow Test Health**
   ```bash
   pytest -m "slow" --json-report
   ```

#### After Changes
1. **Compare Performance**
   ```bash
   pytest --benchmark-only --benchmark-compare=baseline
   ```

2. **Check Coverage Delta**
   ```bash
   pytest --cov=kailash --cov-fail-under=85
   ```

3. **Run Regression Suite**
   ```bash
   pytest -m "regression or critical"
   ```

### 7. Test Maintenance Plan

#### Weekly
- Review slow tests, optimize or mark appropriately
- Update critical test markers based on failures
- Clean up flaky tests

#### Monthly
- Full regression run with reporting
- Performance baseline update
- Test coverage analysis

#### Quarterly
- Test suite optimization
- Remove obsolete tests
- Update test strategies

## Quick Commands

### For Developers
```bash
# Quick check before commit (2 min) - unit tests only
pytest tests/unit/ -m "not (requires_docker or requires_postgres or requires_mysql or requires_redis or requires_ollama)" --maxfail=1

# Standard check before PR (10 min) - unit + integration
pytest tests/unit/ tests/integration/ -m "not (slow and not critical)" -n auto

# Full check for major changes (45 min) - everything
pytest --cov=kailash
```

### For CI Pipeline
```bash
# Stage 1: Every commit (2-5 min)
pytest tests/unit/ -m "not (requires_docker or requires_*)" --junit-xml=results.xml

# Stage 2: Every PR (10-15 min)  
pytest tests/unit/ tests/integration/ -m "not (slow and not critical)" --json-report

# Stage 3: Nightly/Release (60+ min)
pytest --cov=kailash --benchmark-only --html=report.html
```

### Test Migration Commands
```bash
# Find tests that need migration
python scripts/audit_test_organization.py

# Run with strict enforcement
pytest --strict-test-organization

# Check specific tier
pytest tests/unit/ --strict-test-organization
```

## Test Reduction Strategies

### 1. Identify Redundant Tests
```python
# Script to find similar tests
python scripts/find_duplicate_tests.py
```

### 2. Combine Related Tests
- Merge similar unit tests
- Use parametrized tests
- Remove obsolete tests

### 3. Move to Integration
- Convert multiple unit tests to single integration test
- Focus on behavior, not implementation

## Monitoring & Alerts

### Key Metrics
- Test execution time trends
- Failure rate by category
- Flaky test frequency
- Coverage trends

### Alerts
- Critical test failures
- Performance regression >10%
- Coverage drop >5%
- Test suite duration >2x baseline

## Migration Strategy for Test Violations

### Current Violations (as of December 2024)
- **25 unit tests with sleep/delays** → Move to integration/ or refactor
- **25 integration tests with mocks** → Rewrite with real Docker services
- **2 e2e tests with mocks** → Rewrite with real Docker services
- **2 misplaced test files** → Move to proper directories

### Migration Priority
1. **High**: Integration/E2E tests with mocks (breaks test integrity)
2. **Medium**: Unit tests with sleep (hidden from CI)
3. **Low**: Misplaced files (organizational cleanup)

### Migration Process
```bash
# Step 1: Run audit
python scripts/audit_test_organization.py

# Step 2: For each violation, choose approach:
# A) Refactor test to remove sleep/mock
# B) Move test to appropriate tier
# C) Split into fast unit + slow integration

# Step 3: Validate migration
pytest tests/unit/ --strict-test-organization

# Step 4: Update CI once clean
# Enable --strict-test-organization in CI
```

### Expected Outcomes
- **No hidden tests** - All tests run in appropriate pipeline stage
- **Better performance** - Fast unit tests give quick feedback
- **Accurate testing** - Integration/E2E use real services
- **Clear organization** - Easy to find and understand tests
