# Migration System

This directory contains tools and templates for migrating existing projects to the Kailash SDK workflow architecture.

## Directory Structure

```
migrations/
├── to_migrate/          # Place existing projects here for analysis
├── in_progress/         # Active migration projects
├── completed/           # Successfully migrated projects
└── templates/           # Migration document templates
```

## Migration Process

### 1. **Preparation**
- Place existing project in `to_migrate/[project_name]/`
- Begin comprehensive manual analysis
- Review migration templates and guides

### 2. **Analysis**
- Architecture analysis
- API endpoint mapping
- Data flow identification
- Frontend-backend integration points
- Technology stack assessment

### 3. **Planning**
- Migration strategy document
- Risk assessment
- Timeline estimation
- Resource requirements
- Testing strategy

### 4. **Execution**
- Move to `in_progress/`
- Follow migration plan
- Implement in phases
- Continuous testing
- Update master todos

### 5. **Completion**
- Final testing and validation
- Documentation update
- Move to `completed/`
- Post-migration review

## Getting Started

1. **Add project to migrate:**
   ```bash
   cp -r /path/to/existing/project migrations/to_migrate/my_project
   ```

2. **Start migration analysis:**
   - Follow the detailed instructions in `guide/instructions/migration-workflow.md`
   - Use templates from `migrations/templates/` to document your analysis
   - Perform thorough manual exploration of the codebase

3. **Create migration documents in `migrations/in_progress/my_project/`:**
   - `architecture_analysis.md` - System overview and technology stack
   - `api_mapping.md` - Endpoint to Kailash workflow mappings
   - `migration_plan.md` - Phased migration approach
   - `risk_assessment.md` - Risk identification and mitigation
   - `data_migration.md` - Data transfer strategy

4. **Update master todos:**
   - Add migration tasks to `todos/000-master.md` based on your analysis

## Claude Code Instructions

See [Migration Instructions](../guide/instructions/migration-workflow.md) for detailed Claude Code guidance.