# Architecture Decision Records - [MODULE_NAME]

This directory contains Architecture Decision Records (ADRs) specific to the [MODULE_NAME] module.

## Module vs Root ADRs

- **Module ADRs** (this directory): Decisions specific to this module's implementation
- **Root ADRs** (/adr/): Project-wide architectural decisions affecting multiple modules

## When to Create a Module ADR

Create an ADR in this directory when:
- The decision only affects this module
- You're choosing between implementation approaches within the module
- You need to document module-specific trade-offs
- The decision doesn't impact other modules or system architecture

## Template

Use the template at `/adr/0000-template.md` for creating new ADRs.

## Index

| ADR | Title | Status | Date |
|-----|-------|--------|------|
| [0001](0001-example.md) | Example Module Decision | Draft | YYYY-MM-DD |

## Naming Convention

- Format: `NNNN-descriptive-name.md`
- NNNN: Zero-padded sequential number
- Use lowercase with hyphens
- Be descriptive but concise
