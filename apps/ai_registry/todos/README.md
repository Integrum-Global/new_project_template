# Module Task Tracking - [MODULE_NAME]

This directory contains task tracking for the [MODULE_NAME] module.

## Module vs Root Todos

- **Module Todos** (this directory): Tasks specific to this module
- **Root Todos** (/todos/): Project-wide tasks and cross-module coordination

## File Structure

- `000-master.md` - Current active tasks for this module
- `completed-archive.md` - Archive of completed tasks
- `template.md` - Template for new task files

## When to Use Module Todos

Use module-level todos when:
- Tasks are specific to this module's implementation
- Multiple developers are working on different modules
- You need to track module-specific progress
- Tasks don't require coordination with other modules

## Task Format

```markdown
## Task ID: MODULE-YYYY-MM-DD-NNN
**Status**: pending | in_progress | completed | blocked
**Priority**: high | medium | low
**Assigned**: Developer name
**Created**: YYYY-MM-DD
**Updated**: YYYY-MM-DD

### Description
Clear description of what needs to be done

### Acceptance Criteria
- [ ] Specific measurable outcome
- [ ] Another criterion

### Notes
Any relevant notes or blockers
```

## Workflow

1. Create tasks in `000-master.md`
2. Update status as work progresses
3. Move completed tasks to `completed-archive.md` periodically
4. Use root `/todos/` for cross-module coordination
