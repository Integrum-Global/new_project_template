# Todos Management System

Instructions for using the todo tracking system in your Kailash-based project.

## 📁 File Structure & Purpose

| File | Purpose | When to Use |
|------|---------|-------------|
| **[000-master.md](000-master.md)** | Current session status & planned work | Check at start of session for priorities |
| **[active/](active/)** | Detailed active todo files (empty in template) | Copy templates from `templates/todo_tracking/` as needed |
| **[completed/](completed/)** | Historical session records | When referencing past work or patterns |
| **[template.md](template.md)** | Template for new todos | When creating new todo files |

## 🎯 Quick Navigation

### For Current Work
- **Start here**: [000-master.md](000-master.md) - What's happening now
- **Active details**: [active/](active/) - Directory for detailed task tracking files (empty in template)
- **Templates**: Use `template.md` as starting point for new todo files

### For Historical Reference  
- **Sessions overview**: [completed/README.md](completed/README.md) - Entry point for all completed sessions
- **Individual sessions**: [completed/XXX-session-name.md](completed/) - Specific session details

## 🔄 How to Use This System

### At Session Start
1. **Check current status**: Read [000-master.md](000-master.md) for immediate priorities
2. **Get implementation details**: Check relevant files in [active/](active/) 
3. **Reference past work**: Check [completed/README.md](completed/README.md) for sessions overview

### During Development
1. **Update status**: Mark todos as in_progress in [000-master.md](000-master.md)
2. **Add details**: Update implementation notes in [active/](active/) files
3. **Track completion**: Mark completed todos in [000-master.md](000-master.md)

### At Session End
1. **Archive session**: Create new file in [completed/](completed/) using [template.md](template.md)
2. **Update master**: Move completed items from [000-master.md](000-master.md) to archive
3. **Plan next**: Add new priorities to [000-master.md](000-master.md)

## 📊 Current Project Stats

See [000-master.md](000-master.md) for up-to-date project statistics and status.

## 📁 Creating New Todo Files

To create new active todo files:

1. **Use template**: Copy `template.md` as starting point: `cp template.md active/[your-project].md`
2. **Customize**: Replace placeholder text with your project details
3. **Track progress**: Update tasks and status as work progresses

The `template.md` file provides a standard structure for organizing project tasks and can be adapted for any type of work (deployment, migration, feature development, etc.).

---
*This system optimizes context usage for Claude Code while maintaining comprehensive project tracking.*