# Module Mistakes Log - [MODULE_NAME]

This directory tracks mistakes, errors, and learnings specific to the [MODULE_NAME] module.

## Module vs Root Mistakes

### Use Module Mistakes (/src/solutions/[module]/mistakes/) when:
- Error is specific to module implementation
- Learning applies only to this module's patterns
- Bug was in module-specific code
- Solution doesn't apply to other modules

### Use Root Mistakes (/mistakes/) when:
- Error affects multiple modules
- Learning applies project-wide
- Pattern should be avoided everywhere
- Infrastructure or framework issue

## File Structure

- `000-master.md` - Current known issues and active mistakes
- `current-session-mistakes.md` - Today's learnings (move to archived after session)
- `template.md` - Template for documenting mistakes
- `archived/` - Historical mistakes by date/category

## Mistake Documentation Format

```markdown
## Mistake ID: MODULE-ERR-YYYY-MM-DD-NNN
**Type**: bug | design | process | performance
**Severity**: high | medium | low
**Status**: active | resolved | monitoring
**Discovered**: YYYY-MM-DD
**Resolved**: YYYY-MM-DD (if applicable)

### What Happened
Clear description of the mistake or error

### Root Cause
Why this happened

### Impact
- What broke or could have broken
- Performance impact
- User impact

### Solution
How it was fixed or mitigated

### Prevention
How to avoid this in the future

### Related Issues
- Links to PRs, issues, or other mistakes
```

## Categories

- **Implementation**: Code bugs, logic errors
- **Design**: Architecture mistakes, wrong patterns
- **Integration**: Issues with other modules/systems
- **Performance**: Optimization mistakes
- **Testing**: Missed test cases, wrong assumptions

## Learning Culture

Document mistakes openly to:
- Prevent repetition
- Share knowledge
- Improve module quality
- Build better patterns
