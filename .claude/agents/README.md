# Kailash SDK Focused Subagents

This directory contains focused subagents designed to replace the token-heavy feature-implementation.md workflow with efficient specialists that operate in separate context windows.

## Focused Subagent Architecture

The subagents are designed around the core workflow phases identified in `CLAUDE.md` and `feature-implementation.md`:

### Core Specialists

| Agent | Purpose | When to Use |
|-------|---------|-------------|
| **sdk-navigator** | Documentation navigation with file indexes | Finding specific patterns, guides, examples |
| **framework-advisor** | Framework selection and coordination | Choosing between Core SDK, DataFlow, Nexus, MCP |
| **pattern-expert** | Core SDK patterns (workflows, nodes, parameters) | Implementing workflows, debugging pattern issues |
| **gold-standards-validator** | Compliance checking against gold standards | Code validation, catching violations early |
| **testing-specialist** | 3-tier testing strategy with real infrastructure | Understanding testing requirements and strategy |
| **tdd-implementer** | Test-first development methodology | Implementing features with write-test-then-code |
| **documentation-validator** | Documentation validation and testing | Testing code examples, ensuring doc accuracy |
| **ultrathink-analyst** | Deep analysis and failure point identification | Complex features, systemic issues, risk analysis |
| **requirements-analyst** | Requirements breakdown and ADR creation | Systematic analysis, architecture decisions |
| **intermediate-reviewer** | Checkpoint reviews and progress critique | Reviewing todos and implementation milestones |
| **todo-manager** | Task management and local tracking | Creating and managing local development tasks |
| **gh-manager** | GitHub projects and issue management | Creating user stories, syncing with project boards |
| **mcp-specialist** | MCP server implementation and integration | Model Context Protocol patterns and debugging |
| **git-release-specialist** | Git workflows, CI validation, and releases | Pre-commit checks, PR creation, version releases |

### Framework Specialists (NEW)

| Agent | Purpose | When to Use |
|-------|---------|-------------|
| **nexus-specialist** | Nexus multi-channel platform implementation | Zero-config deployment, API/CLI/MCP orchestration, **DataFlow integration** |
| **dataflow-specialist** | DataFlow database framework implementation | Database operations, bulk processing, auto node generation, **Nexus integration** |

### Critical Integration Guides

**⚠️ IMPORTANT: DataFlow + Nexus Integration**
- See: `sdk-users/guides/dataflow-nexus-integration.md` for tested configurations
- Key settings to prevent blocking: `Nexus(auto_discovery=False)` + `DataFlow(skip_registry=True)`
- Full featured config available with 10-30s startup time
- Both specialists updated with integration warnings

### Design Principles

1. **Navigation over Loading**: Agents use file indexes rather than loading entire contexts
2. **Focused Expertise**: Each agent has a specific, narrow domain of expertise  
3. **Reference-Based**: Agents provide specific file paths and references
4. **Workflow-Aligned**: Agents map to the established development workflow phases

## Suggested Usage Sequence

Follow this sequence for efficient feature development:

### Quick Reference: Agents by Phase

| Phase | Agents (in order) | Purpose |
|-------|-------------------|---------|
| **1. Analysis** | ultrathink-analyst → requirements-analyst → sdk-navigator → framework-advisor → (nexus/dataflow-specialist) | Deep analysis, requirements, existing patterns, tech selection, framework-specific guidance |
| **2. Planning** | gh-manager → todo-manager → intermediate-reviewer | Create GitHub issues, create local todos, validate task breakdown |
| **3. Implementation** | tdd-implementer → pattern-expert → (nexus/dataflow-specialist) → todo-manager (sync) → intermediate-reviewer → gold-standards-validator | Test-first, implement, framework patterns, sync to GH, review, validate (repeat per component) |
| **4. Testing** | testing-specialist → documentation-validator | Full test coverage, doc accuracy |
| **5. Release** | git-release-specialist → gh-manager (close issues) | Pre-commit validation, PR creation, close GitHub issues |
| **6. Final** | intermediate-reviewer → gh-manager (project update) | Final critique, update project board |

### Phase 1: Analysis & Planning (Sequential)
```
1. > Use the ultrathink-analyst subagent to analyze requirements and identify failure points for [feature]
2. > Use the requirements-analyst subagent to create systematic breakdown and ADR for [feature]
3. > Use the sdk-navigator subagent to find existing patterns similar to [feature]
4. > Use the framework-advisor subagent to recommend Core SDK vs DataFlow vs Nexus for [feature]
   - If DataFlow recommended: > Use the dataflow-specialist subagent for implementation details
   - If Nexus recommended: > Use the nexus-specialist subagent for implementation details

OR chain all Phase 1 agents:
> Use the ultrathink-analyst, requirements-analyst, sdk-navigator, and framework-advisor subagents to perform complete analysis and planning for [feature]
```

### Phase 2: Project & Task Planning (Sequential)
```
1. > Use the gh-manager subagent to create GitHub issues from requirements/user stories
2. > Use the todo-manager subagent to create local todos from GitHub issues
3. > Use the intermediate-reviewer subagent to review task completeness and feasibility

OR chain Phase 2:
> Use the gh-manager, todo-manager, and intermediate-reviewer subagents to create GitHub issues, local todos, and validate breakdown

**Important**: gh-manager creates project-level tracking (GitHub), todo-manager creates implementation tracking (local files)
```

### Phase 3: Implementation (Iterative per component)
```
For each component:
1. > Use the tdd-implementer subagent to write tests first for [component]
2. > Use the pattern-expert subagent to implement [component] following SDK patterns
   - For DataFlow components: > Use the dataflow-specialist subagent for database patterns
   - For Nexus components: > Use the nexus-specialist subagent for multi-channel patterns
3. > Use the todo-manager subagent to update progress and sync to GitHub via gh-manager
4. > Use the gold-standards-validator subagent to ensure [component] compliance
5. > Use the intermediate-reviewer subagent to review [component] implementation

OR chain Phase 3 for a component:
> Use the tdd-implementer, pattern-expert, todo-manager, gold-standards-validator, nexus-specialist, and dataflow-specialist subagents, as needed, to implement, sync progress, and validate [component]

POST Phase 3:
> Use the intermediate-reviewer subagent to ensure that the implementation meets all requirements and standards

**Important**: todo-manager automatically syncs progress to GitHub issues at key milestones (start, 50%, blocked, complete)
```

### Phase 4: Testing & Documentation
```
1. > Use the testing-specialist subagent to verify 3-tier test coverage
2. > Use the documentation-validator subagent to test all code examples in documentation
3. > Use the todo-manager subagent to ensure all todos are complete and update the todo system accordingly

OR chain Phase 4:
> Use the testing-specialist, documentation-validator, and todo-manager subagents to ensure complete test coverage and documentation accuracy
```

### Phase 5: Release & Git Management
```
1. > Use the git-release-specialist subagent to run pre-commit validation (black, isort, ruff)
2. > Use the git-release-specialist subagent to create feature branch and PR workflow
3. > Use the gh-manager subagent to close related GitHub issues with PR references
4. > Use the git-release-specialist subagent to handle version management and release procedures (if applicable)

OR chain Phase 5:
> Use the git-release-specialist and gh-manager subagents to validate code quality, create PR, close issues, and manage release workflow

**Important**: Always close GitHub issues when PR is merged to maintain sync between code and project tracking
```

### Phase 6: Final Review & Project Update
```
1. > Use the intermediate-reviewer subagent to perform final critique of complete implementation
2. > Use the gh-manager subagent to update project board status and generate sprint report

OR chain Phase 6:
> Use the intermediate-reviewer and gh-manager subagents for final critique and project status update
```

### Quick Debugging Sequence
```
When facing issues:
1. > Use the sdk-navigator subagent to find solutions in common-mistakes.md
2. > Use the pattern-expert subagent to debug specific pattern issues
3. > Use the testing-specialist subagent to understand test failures
   - For DataFlow issues: > Use the dataflow-specialist subagent for database-specific debugging
   - For Nexus issues: > Use the nexus-specialist subagent for multi-channel debugging
4. > Use the todo-manager subagent to mark todo as blocked and sync to GitHub via gh-manager

OR for comprehensive debugging:
> Use the sdk-navigator, pattern-expert, testing-specialist, and todo-manager subagents to diagnose, fix, and track [issue]

**Important**: Always update GitHub issue status when blocked to keep stakeholders informed
```

### GitHub Project Management Workflows

#### Creating User Stories from Requirements
```
1. > Use the requirements-analyst subagent to break down requirements into user stories
2. > Use the gh-manager subagent to create GitHub issues from user stories and add to project
3. > Use the todo-manager subagent to create implementation todos from GitHub issues

**Result**: Requirements → GitHub Issues → Local Todos (full traceability chain)
```

#### Sprint Planning & Execution
```
1. > Use the gh-manager subagent to prioritize backlog and create sprint in GitHub project
2. > Use the todo-manager subagent to create local todos for sprint items
3. During implementation: todo-manager auto-syncs progress to gh-manager → GitHub issues
4. > Use the gh-manager subagent to generate sprint status reports

**Result**: Synchronized project tracking across GitHub and local development
```

#### Handling Blockers & Dependencies
```
1. Developer encounters blocker → update local todo status to BLOCKED
2. > Use the todo-manager subagent to sync blocker to GitHub via gh-manager
3. > Use the gh-manager subagent to add "blocked" label and notify stakeholders
4. When blocker resolved → todo-manager updates status → gh-manager removes label

**Result**: Real-time visibility into project blockers across teams
```

## Project & Todo Management

### Dual-Tracking System

This project uses **synchronized tracking** between GitHub Projects and local todos:

- **GitHub (gh-manager)**: Project-level tracking, stakeholder visibility, requirements
- **Local Todos (todo-manager)**: Implementation tracking, developer task breakdown

**📖 Complete Guide**: See [PROJECT-MANAGEMENT-GUIDE.md](PROJECT-MANAGEMENT-GUIDE.md) for:
- Synchronization rules and conflict resolution
- Developer workflows (starting work, daily dev, completing, sprints)
- Best practices and anti-patterns
- Troubleshooting common issues

**Key Principle**: GitHub is source of truth for requirements, local todos are source of truth for implementation status. Both stay synchronized automatically.

## Coordination Through Root CLAUDE.md

Since subagents cannot invoke other subagents, coordination happens at the main Claude Code level through the root `CLAUDE.md` file, which:

1. **Loads automatically** when Claude Code starts
2. **Contains the 18-step enterprise workflow** for guidance
3. **References subagents** for specific phases
4. **Maintains the multi-step strategy** that users follow

## File References

### Primary Workflow Sources
- **Root CLAUDE.md**: 18-step enterprise workflow, core patterns
- **feature-implementation.md**: 4-phase detailed implementation process  
- **sdk-users/CLAUDE.md**: Essential SDK patterns navigation

### Framework Documentation  
- **sdk-users/apps/dataflow/**: Zero-config database patterns and guides
- **sdk-users/apps/nexus/**: Multi-channel platform patterns and guides
- **src/kailash/mcp_server/**: Production MCP server implementation

### Gold Standards
- **sdk-users/7-gold-standards/**: All compliance standards
- **sdk-users/2-core-concepts/validation/common-mistakes.md**: Error solutions

This focused architecture maintains the essential workflow while dramatically reducing token usage through targeted, navigation-based agents that guide users to the right documentation at the right time.

## Framework-Specific Workflows

### DataFlow Database Applications
```
1. > Use the framework-advisor subagent to confirm DataFlow is appropriate
2. > Use the dataflow-specialist subagent for:
   - Model definition patterns
   - Auto-generated node usage
   - Bulk operations
   - Migration control (auto_migrate settings)
   - PostgreSQL-only execution limitations
```

### Nexus Multi-Channel Platforms
```
1. > Use the framework-advisor subagent to confirm Nexus is appropriate
2. > Use the nexus-specialist subagent for:
   - Zero-config initialization
   - Workflow registration patterns
   - Multi-channel parameter consistency
   - Progressive enterprise enhancement
   - Session management
```

### Combined Framework Applications
```
For DataFlow + Nexus integration:
1. > Use the framework-advisor subagent for architecture guidance
2. > Use the dataflow-specialist subagent for database layer
3. > Use the nexus-specialist subagent for platform deployment
4. > Use the pattern-expert subagent for workflow connections
```