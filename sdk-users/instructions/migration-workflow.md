# Migration Workflow - Claude Code Instructions

## 🚨 CRITICAL: Migration Analysis Process

When a user places an existing project in `migrations/to_migrate/`, follow this structured analysis process.

### 1. Initial Project Scan

**ALWAYS start by analyzing the project structure:**

```python
# Check project structure
project_path = "migrations/to_migrate/[project_name]"
- Identify main application entry points
- Map directory structure
- Identify technology stack
- Find configuration files
- Locate data models and schemas
- Identify test structure
```

### 2. Deep Architecture Analysis

**Create comprehensive architecture analysis:**

#### Backend Analysis
- **Framework identification** (Flask, FastAPI, Django, Express, etc.)
- **Database connections** (SQL, NoSQL, file-based)
- **API endpoints** (REST, GraphQL, WebSocket)
- **Authentication/Authorization** patterns
- **Business logic organization**
- **Data processing workflows**
- **External integrations** (APIs, services, webhooks)

#### Frontend Analysis (if applicable)
- **Framework/Library** (React, Vue, Angular, vanilla JS)
- **State management** (Redux, Vuex, Context API)
- **API communication** patterns
- **Component architecture**
- **Routing structure**
- **Data binding** methods

#### Data Flow Analysis
- **Request/Response cycles**
- **Data transformation points**
- **Caching layers**
- **Queue systems**
- **File processing workflows**
- **Report generation**

### 3. Kailash SDK Mapping Strategy

**For each backend component, identify Kailash equivalents:**

#### API Endpoints → Kailash Nodes
```python
# Example mapping
OLD: @app.route('/api/data/process', methods=['POST'])
NEW: DataProcessorNode with APIInputNode and APIOutputNode
```

#### Data Processing → Workflow Chains
```python
# Example mapping
OLD: def process_data(input_data):
     cleaned = clean_data(input_data)
     transformed = transform_data(cleaned)
     return save_to_db(transformed)

NEW: Workflow with DataCleanerNode → DataTransformerNode → DatabaseWriterNode
```

#### Database Operations → Data Nodes
```python
# Example mapping
OLD: SQLAlchemy models and queries
NEW: DatabaseReaderNode, DatabaseWriterNode, QueryBuilderNode
```

### 4. Migration Document Generation

**ALWAYS create these documents:**

#### A. Architecture Analysis (`architecture_analysis.md`)
- Current system overview
- Technology stack assessment
- Component dependencies
- Data flow diagrams (text descriptions)
- Integration points
- Performance characteristics
- Scalability considerations

#### B. API Mapping (`api_mapping.md`)
- Complete endpoint inventory
- Request/response schemas
- Authentication requirements
- Rate limiting
- Error handling patterns
- Kailash node equivalents

#### C. Migration Plan (`migration_plan.md`)
- Phase-by-phase migration strategy
- Risk assessment and mitigation
- Timeline estimates
- Resource requirements
- Testing strategy
- Rollback procedures
- Success criteria

#### D. Data Migration Strategy (`data_migration.md`)
- Data model analysis
- Migration scripts requirements
- Data validation processes
- Backup strategies
- Downtime considerations

### 5. Master Todo Integration

**AUTOMATICALLY update `todos/000-master.md` with:**

```markdown
## MIGRATION: [Project Name]

### Phase 1: Analysis & Planning (PRIORITY: HIGH)
- [ ] Complete architecture analysis
- [ ] Map all API endpoints to Kailash nodes
- [ ] Identify data migration requirements
- [ ] Create detailed migration timeline
- [ ] Set up development environment

### Phase 2: Core Backend Migration (PRIORITY: HIGH)
- [ ] Implement critical API endpoints as Kailash workflows
- [ ] Migrate data processing logic
- [ ] Set up database connections
- [ ] Implement authentication/authorization
- [ ] Create error handling workflows

### Phase 3: Integration & Testing (PRIORITY: MEDIUM)
- [ ] Frontend integration with new backend
- [ ] End-to-end testing
- [ ] Performance testing
- [ ] Security testing
- [ ] Load testing

### Phase 4: Deployment & Monitoring (PRIORITY: MEDIUM)
- [ ] Production deployment strategy
- [ ] Monitoring and logging setup
- [ ] Documentation update
- [ ] Team training
- [ ] Go-live checklist
```

### 6. Claude Code Migration Commands

**Use these specific prompts for migration analysis:**

#### Initial Analysis
```
"Analyze the project in migrations/to_migrate/[project_name]. Create a comprehensive architecture analysis, identify all API endpoints, map data flows, and generate a complete migration plan to Kailash SDK. Update the master todo list with migration tasks."
```

#### API Mapping
```
"Map all API endpoints in [project_name] to equivalent Kailash SDK node workflows. Create detailed node configurations and connection patterns for each endpoint."
```

#### Data Flow Analysis
```
"Analyze data flows in [project_name]. Identify all data processing pipelines and map them to Kailash workflow chains. Include data transformation logic and storage patterns."
```

#### Frontend Integration
```
"Analyze frontend-backend integration in [project_name]. Identify API calls, state management, and data binding. Create migration strategy for frontend to work with new Kailash backend."
```

### 7. Risk Assessment Framework

**ALWAYS include risk analysis:**

#### Technical Risks
- Complex business logic
- Legacy dependencies
- Data integrity concerns
- Performance requirements
- Integration complexity
- Testing challenges

#### Business Risks
- Downtime requirements
- User impact
- Training needs
- Timeline constraints
- Resource availability
- Budget considerations

#### Mitigation Strategies
- Parallel development
- Gradual migration
- Feature flags
- Rollback procedures
- Comprehensive testing
- User communication

### 8. Success Criteria Definition

**Define clear success metrics:**

#### Functional Success
- All features working as before
- API compatibility maintained
- Data integrity preserved
- Performance equals or exceeds original

#### Technical Success
- Clean Kailash workflow architecture
- Maintainable code structure
- Comprehensive test coverage
- Proper error handling
- Monitoring and logging

#### Business Success
- Zero data loss
- Minimal downtime
- User satisfaction maintained
- Team confidence in new system
- Documentation completeness

## Migration Best Practices

### 1. **Always Backup First**
- Complete database backup
- Code repository backup
- Configuration backup
- Document current system behavior

### 2. **Incremental Migration**
- Start with least critical components
- Maintain parallel systems during transition
- Use feature flags for controlled rollout
- Test each phase thoroughly

### 3. **Comprehensive Testing**
- Unit tests for each Kailash node
- Integration tests for workflows
- End-to-end API testing
- Performance regression testing
- User acceptance testing

### 4. **Documentation First**
- Document before changing
- Update as you migrate
- Create troubleshooting guides
- Maintain API documentation

### 5. **Team Involvement**
- Include all stakeholders
- Provide Kailash training
- Regular progress updates
- Knowledge transfer sessions

## Common Migration Patterns

### REST API → Kailash Workflow
```python
# Pattern: CRUD API endpoint
OLD: @app.route('/api/users/<id>', methods=['GET'])
NEW: APIInputNode → UserReaderNode → ResponseFormatterNode → APIOutputNode
```

### Data Processing Job → Kailash Pipeline
```python
# Pattern: Background job
OLD: Celery task with multiple steps
NEW: Scheduled workflow with ChainNode connecting processing steps
```

### Database Integration → Data Nodes
```python
# Pattern: Database operations
OLD: SQLAlchemy/Mongoose operations
NEW: DatabaseReaderNode, DatabaseWriterNode, QueryBuilderNode
```

### File Processing → File Workflows
```python
# Pattern: File upload and processing
OLD: File upload endpoint with processing
NEW: FileReaderNode → DataValidatorNode → ProcessorNode → FileWriterNode
```

This systematic approach ensures no critical components are missed and provides a clear roadmap for successful migration.
