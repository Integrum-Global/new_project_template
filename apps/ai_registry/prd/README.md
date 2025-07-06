# Product Requirements Documents - [MODULE_NAME]

This directory contains Product Requirements Documents (PRDs) specific to the [MODULE_NAME] module.

## Module vs Root PRDs

- **Module PRDs** (this directory): Requirements specific to this module's functionality
- **Root PRDs** (/prd/): Project-wide requirements and overall system specifications

## When to Create a Module PRD

Create a PRD in this directory when:
- Defining features specific to this module
- Documenting module-specific user stories
- Capturing module-level acceptance criteria
- The requirements don't affect other modules

## Structure

```
prd/
├── README.md           # This file
├── 001-feature-name.md # Individual feature requirements
├── 002-api-spec.md     # Module API specifications
└── 003-ui-design.md    # Module UI requirements
```

## Template Structure

### Feature PRD Template
```markdown
# Feature Name

## Overview
Brief description of the feature

## User Stories
- As a [role], I want [feature] so that [benefit]

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2

## Technical Requirements
- Specific technical constraints
- Performance requirements
- Integration points

## Dependencies
- Other modules or systems this depends on
```

## Index

| PRD | Title | Status | Last Updated |
|-----|-------|--------|--------------|
| [001](001-example.md) | Example Feature | Draft | YYYY-MM-DD |
