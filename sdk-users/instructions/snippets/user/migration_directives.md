# Kailash SDK Migration Directives

## 📋 Migration Process Overview

This guide provides strict directives for implementing the Kailash SDK migration using Test-Driven Development (TDD) and continuous validation.

## Document-First Migration Strategy

### Migration Documentation Structure

**IMPORTANT**: Use the two-document approach for comprehensive migration:

1. **Systematic Patterns**: [WORKFLOW_MIGRATION_PATTERNS.md](WORKFLOW_MIGRATION_PATTERNS.md)
   - Framework translation guide (LangGraph → Kailash SDK)
   - Standard configuration templates
   - Error handling and recovery patterns  
   - Data validation schemas
   - Testing strategy framework
   - Monitoring and alerting patterns
   - Operational readiness checklists

2. **Workflow-Specific Analysis**: `workflows/wX_name/WX_ORIGINAL_COMPLETE_ANALYSIS.md`
   - Workflow-specific business logic
   - Workflow-specific configuration parameters
   - Workflow-specific testing scenarios
   - Workflow-specific monitoring metrics
   - Workflow-specific error scenarios

### For Complex Workflow Migrations (RECOMMENDED)

When migrating workflows with intricate business logic, use this document-first approach:

1. **Create Comprehensive Original Analysis**
   - Check each workflow in docs/workflows (e.g. W1_ORIGINAL_COMPLETE_ANALYSIS.md) 
   - Add to your understanding the langgraph implementations in workflows/
   - **Reference systematic patterns**: Use [WORKFLOW_MIGRATION_PATTERNS.md](WORKFLOW_MIGRATION_PATTERNS.md) for framework concerns
   - **Focus on workflow specifics**: Capture workflow-unique business logic, configurations, edge cases
   - Ensure that there are no gaps and we have all the information and connectivity to recreate the migrated workflows with 100% replicability
   - Document EVERY workflow-specific business logic in detail
   - Capture all API calls with exact parameters
   - Map all state transitions and context updates
   - Document workflow-specific edge cases and error handling
   - Include workflow-specific performance requirements
   - Include trigger conditions and integration points
   - Include model method signatures unique to this workflow
   - Include specific error response formats
   - Other workflow-specific implementation details

2. **Self-Critique the Analysis from Multiple Perspectives**
   - **Migration Engineer**: Can this be implemented in Kailash SDK?
   - **Testing Engineer**: Are all edge cases testable?
   - **Operations Engineer**: Can this be monitored and maintained?
   - **Business Analyst**: Are business rules clear and complete?
   - Review for 100% completeness using systematic patterns as baseline
   - Identify workflow-specific gaps not covered by patterns
   - Validate business rule capture against original requirements

3. **Validate Content Separation (Critical)**
   - **Systematic Content Check**: Does anything in workflow doc apply to other workflows?
   - **Missing Patterns Check**: Are there systematic patterns not captured in patterns doc?
   - **Business Context Check**: Does workflow doc explain WHY not just WHAT?
   - **Performance Baseline Check**: Are actual measurements included?
   - **Integration Flow Check**: Are state transitions clearly documented?

4. **Use Combined Documentation to Guide Migration**
   - Use systematic patterns for framework translation
   - Use workflow analysis for specific business logic
   - Implement based on documented logic
   - Preserve all critical business rules
   - Maintain performance optimizations
   - Keep analysis files for validation

### Content Separation Quality Gates

Before proceeding with migration, validate content separation:

#### Must-Pass Criteria ✅
- [ ] **No Systematic Patterns in Workflow Doc**: Everything in workflow doc is workflow-unique
- [ ] **Complete Business Justification**: All workflow rules have WHY explanations  
- [ ] **Performance Baselines**: Actual measurements from original implementation
- [ ] **State Transition Flows**: Clear diagrams for integration scenarios
- [ ] **Configuration Separation**: Only workflow-specific config in workflow doc

#### Content Placement Decision Tree
```
Is this content workflow-specific?
├── YES: Unique to this workflow → Put in WX_ORIGINAL_COMPLETE_ANALYSIS.md
└── NO: Could apply to other workflows
    ├── Framework pattern → Put in WORKFLOW_MIGRATION_PATTERNS.md
    ├── Configuration template → Put in WORKFLOW_MIGRATION_PATTERNS.md  
    ├── Error handling pattern → Put in WORKFLOW_MIGRATION_PATTERNS.md
    └── Testing strategy → Put in WORKFLOW_MIGRATION_PATTERNS.md
```

## Migration Quality Validation Framework

### Four-Pass Critique Strategy (MANDATORY)

Perform 4 ultrathink critique passes to ensure migration completeness:
In each pass, please:
- Document all business logic, API calls, state transitions  
- Identify gaps in requirements, performance, security, integration  
- Validate from migration, testing, operations, and business perspectives  
- Ensure systematic vs workflow-specific content is properly separated

## Essential Context Loading
Load these files before starting (DO NOT proceed until loaded):
- Root `CLAUDE.md` - Core validation rules and critical patterns
- `sdk-users/CLAUDE.md` - Implementation patterns and architectural guidance
- `README.md` - Project overview and structure
- Any existing migration documentation in `docs/migration/` or similar directories
- Current test structure and patterns in `tests/`
- System architecture documentation if available

**For implementation guidance during development, remember these key resource locations** (use MCP tools to search when needed):
- `sdk-users/3-development/` - Core implementation guides and patterns
- `sdk-users/2-core-concepts/nodes/` - Node selection and usage patterns
- `sdk-users/2-core-concepts/cheatsheet/` - Copy-paste implementation patterns
- `sdk-users/2-core-concepts/validation/common-mistakes.md` - Error database with solutions

### Framework-First Approach (MANDATORY)
Check for existing framework solutions that can replace current components (use MCP tools to search):
- `sdk-users/apps/dataflow/` - Replace custom state management
- `sdk-users/apps/nexus/` - Replace FastAPI endpoints
- Other frameworks in `sdk-users/apps/` that may replace custom code

### Critical Understanding Confirmation
After loading the essential files, you MUST confirm you understand:
- **3-tier testing strategy** (`sdk-users/3-development/testing/regression-testing-strategy.md` and `sdk-users/3-development/testing/test-organization-policy.md`)
  - **Tier 1 requirements**: Fast (<1s), isolated, can use mocks, no external dependencies, no sleep
  - **NO MOCKING policy** for Tier 2/3 tests - this is absolutely critical
  - Real Docker infrastructure requirement - never skip this for integration/E2E tests
- **Migration-specific testing**: Test against documented behavior, NOT current implementation
- **Bug fixing during migration**: Fix known bugs instead of replicating them
- **Project structure**: Understand how the current project is organized
- **Available frameworks** in `sdk-users/apps/` that can replace custom code

**Search relevant documentation as needed during implementation using MCP tools instead of loading everything upfront.**

## 🧪 TEST-FIRST DEVELOPMENT (MANDATORY)

Write tests BEFORE implementation. This prevents missing tests and ensures working code. You MUST follow the 3-tier testing strategy exactly as specified in `sdk-users/3-development/testing/regression-testing-strategy.md` and `sdk-users/3-development/testing/test-organization-policy.md`.

### Critical Requirements

**Always ensure that your TDD covers all the detailed todo entries**

Do not write new tests without checking that existing ones can be modified to include them. You MUST have all 3 kinds of tests:

### Tier 1: Unit Tests
- **Location**: `tests/unit/`
- **Requirements**: 
  - Fast execution (<1s per test)
  - Can use mocks
  - No external dependencies
  - No sleep statements
- **Coverage**: 
  - All public methods
  - Edge cases
  - Error conditions
  - Business logic validation
- **Pattern**: Follow existing test patterns in the codebase

### Tier 2: Integration Tests
- **Location**: `tests/integration/`
- **Requirements**:
  - **NO MOCKING** - must use real Docker services
  - Test actual component interactions
  - Use docker implementation in `tests/utils`
- **Setup**: Always run before tests:
  ```bash
  ./tests/utils/test-env up && ./tests/utils/test-env status
  ```

### Tier 3: E2E Tests
- **Location**: `tests/e2e/`
- **Requirements**:
  - **NO MOCKING** - complete scenarios with real infrastructure
  - Test complete user workflows from start to finish
  - Use real data, processes, and responses
- **Coverage**:
  - Complete business workflows
  - Multi-module interactions
  - Performance requirements

### Test Quality Validation

Before proceeding with implementation, validate all tests:

1. **Business Logic Coverage**
   - [ ] Tests replicate required original business logic
   - [ ] All acceptance criteria from todos covered
   - [ ] Edge cases and error paths tested

2. **Test Legitimacy Checks**
   - [ ] Tests verify intended functionality, not just syntax
   - [ ] Tests cover actual behavior, not trivial conditions
   - [ ] Tests are not placeholders or empty stubs
   - [ ] Performance tests measure real characteristics
   - [ ] Tests would fail if implementation is wrong

3. **Test Plan Review**
   - [ ] Show complete test plan before implementation
   - [ ] All test files created and reviewed
   - [ ] Test structure matches implementation plan

## 🛠️ IMPLEMENTATION WITH CONTINUOUS VALIDATION

**Always read the detailed todo entries before starting implementation. Extend from core SDK, don't create.**

### Implementation Rules

1. **Small, Verifiable Chunks**: Implement one component at a time
2. **Test After Each Component**: Do not proceed until all tests pass
3. **Continuous Validation**: Validate against requirements after each step
4. **No Shortcuts**: Follow SDK patterns exactly

### Implementation Checkpoints

For each component, you MUST complete this checklist:

**Component: [name]**
- [ ] Implementation complete in `[directory]`
- [ ] Unit tests pass (show full output)
- [ ] Integration tests pass (show full output)
- [ ] Documentation updated if needed
- [ ] No policy violations found
- [ ] Business logic preserved
- [ ] Performance requirements met

### Mandatory Validation Commands

**After EACH component, run these commands and show COMPLETE output:**

1. **Docker Infrastructure**:
   ```bash
   # Check existing containers first
   docker ps -a
   
   # Use existing test utils
   ./tests/utils/test-env up && ./tests/utils/test-env status
   ```
   
   **Docker Creation Rules**:
   - DO NOT create new docker containers before checking existing
   - Use docker-compose approach from `tests/utils/CLAUDE.md`
   - Deconflict ports by checking current usage
   - Document any new services in test infrastructure

2. **Unit Tests**:
   ```bash
   pytest tests/unit/test_[component].py -v --tb=short
   ```

3. **Integration Tests**:
   ```bash
   pytest tests/integration/test_[component].py -v --tb=short
   ```

4. **E2E Tests** (when applicable):
   ```bash
   pytest tests/e2e/test_[workflow].py -v --tb=short
   ```

### Component Validation Checklist

After each component implementation, validate:

1. **SDK Pattern Compliance**
   - [ ] Checked `src/kailash/` for similar implementations
   - [ ] Using existing base classes and interfaces
   - [ ] Following established coding conventions
   - [ ] Respecting directory structure

2. **Documentation Check**
   - [ ] Checked `sdk-users/` for similar patterns
   - [ ] Not duplicating existing functionality
   - [ ] Consistent with documented patterns
   - [ ] Updated relevant documentation

3. **Test Verification**
   - [ ] All tests actually passing (not skipped)
   - [ ] Tests verify correct functionality
   - [ ] No trivial or placeholder tests
   - [ ] Performance tests are meaningful

4. **Production Quality**
   - [ ] Proper error handling implemented
   - [ ] Logging added where appropriate
   - [ ] Edge cases handled
   - [ ] Documentation strings included

5. **Business Logic Preservation**
   - [ ] Original functionality maintained
   - [ ] Performance requirements met
   - [ ] API compatibility preserved
   - [ ] No breaking changes introduced

### Implementation Legitimacy Checks

After implementation, critique for legitimacy:

1. **Correctness**
   - Does it solve the actual problem?
   - Are all requirements met?
   - Is the business logic correct?

2. **Performance**
   - Does it meet performance targets?
   - Is caching implemented correctly?
   - Are queries optimized?

3. **Maintainability**
   - Is the code readable and documented?
   - Does it follow SDK patterns?
   - Can other developers understand it?

4. **Completeness**
   - Are all edge cases handled?
   - Is error handling comprehensive?
   - Are all tests meaningful?

## 🚫 Common Pitfalls to Avoid

1. **Writing Implementation Before Tests**
   - Always write tests first
   - Tests drive the implementation

2. **Skipping Integration Tests**
   - Never mock in Tier 2/3
   - Always use real services

3. **Trivial Tests**
   - Tests must verify behavior
   - Avoid testing syntax only

4. **Ignoring Existing Patterns**
   - Always check SDK for examples
   - Don't reinvent the wheel

5. **Proceeding with Failing Tests**
   - Fix all issues before continuing
   - Never skip or disable tests

## ✅ Definition of Done

A component is ONLY complete when:

1. All tests written and passing (all tiers)
2. Implementation follows SDK patterns
3. Documentation updated
4. Performance requirements met
5. Code reviewed for legitimacy
6. Business logic preserved
7. No breaking changes introduced

## 📊 Progress Tracking

Track each component's progress:

| Component | Tests Written | Unit Pass | Integration Pass | E2E Pass | Reviewed | Complete |
|-----------|--------------|-----------|------------------|----------|----------|----------|
| Example   | ✅           | ✅        | ✅              | ✅       | ✅       | ✅       |

**STOP SIGN**: If any column is ❌, do not proceed to next component.

---

## 🔍 MANDATORY PHASE CRITIQUE & VALIDATION

**CRITICAL**: After completing each phase, perform this mandatory critique step before proceeding.

### Phase Completion Critique Checklist

#### **1. UltraThink Analysis - What Did We Actually Accomplish?**
- [ ] List every component implemented with evidence
- [ ] Verify all acceptance criteria from phase requirements met
- [ ] Check all tests actually PASS (not skipped or mocked in integration/E2E)
- [ ] Validate business logic preservation with real examples

#### **2. Critical Gap Analysis - What's Missing?**
- [ ] **Integration Reality Check**: Do integration tests use REAL services?
- [ ] **Performance Validation**: Are performance claims measured with real data?
- [ ] **Business Continuity**: Does existing functionality still work?
- [ ] **Security & Compliance**: Are business-critical requirements satisfied?
- [ ] **Developer Experience**: Can the team actually use what was built?

#### **3. Production Readiness Assessment**
- [ ] **Error Handling**: Graceful failure modes implemented?
- [ ] **Monitoring**: Health checks and observability in place?
- [ ] **Documentation**: Usage examples and migration guides created?
- [ ] **Backward Compatibility**: Existing systems not broken?

#### **4. Workflow Integration Validation** (Kailash-Specific)
- [ ] **Actual Workflows**: Created real WorkflowBuilder examples using components?
- [ ] **Node Generation**: Verified DataFlow models generate working nodes?
- [ ] **Runtime Execution**: Tested `runtime.execute(workflow.build())` pattern?
- [ ] **SDK Compliance**: Following CLAUDE.md essential patterns exactly?

#### **5. Critique Documentation Requirements**
Create critiques documentation containing:
- **What Actually Works**: Evidence-based component validation
- **Critical Gaps**: Honest assessment of missing pieces
- **Production Risks**: Security, performance, compliance issues
- **Next Phase Blockers**: Dependencies that must be resolved

#### **6. Mandatory Validation Commands**
Run these commands and document COMPLETE output:

```bash
# Verify all tests pass with real services
./tests/utils/test-env up && ./tests/utils/test-env status
pytest tests/unit/ -v --tb=short
pytest tests/integration/ -v --tb=short --no-skip
pytest tests/e2e/ -v --tb=short --no-skip

# Validate component functionality
python -c "from your.module import component; component.validate_production_ready()"

# Performance benchmarking
python scripts/benchmark_phase_{N}.py --validate-requirements
```

#### **7. Go/No-Go Decision**
**Before proceeding to next phase:**
- [ ] All acceptance criteria met with evidence
- [ ] All tests pass against real infrastructure  
- [ ] Performance requirements validated with measurements
- [ ] No critical security or compliance gaps
- [ ] Team can actually use the implemented components

**If ANY checkbox is unchecked, DO NOT proceed to next phase.**

#### **8. Stakeholder Sign-off**
- [ ] Technical lead review of critique findings
- [ ] Business owner validation of requirements met
- [ ] Security review if applicable
- [ ] Documentation review for completeness

---

**Remember**: Quality over speed. It's better to have one component working perfectly than five components partially working.

**STOP SIGN**: If phase critique reveals critical gaps, pause implementation and address gaps before continuing.