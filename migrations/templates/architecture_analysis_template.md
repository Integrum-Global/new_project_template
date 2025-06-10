# Architecture Analysis - [Project Name]

Generated: [Date]

## Project Overview

**Project Name:** [Name]
**Analysis Date:** [Date]
**Analyzed By:** [Analyst]
**Project Type:** [Web App/API/Service/Other]

## Executive Summary

[Brief 2-3 paragraph summary of the project, its purpose, and key architectural findings]

## Technology Stack

### Backend Technologies
- **Language:** [Python/JavaScript/Java/etc.]
- **Framework:** [Flask/Django/Express/Spring/etc.]
- **API Type:** [REST/GraphQL/SOAP/etc.]
- **Additional Libraries:** [List key libraries]

### Frontend Technologies
- **Framework/Library:** [React/Vue/Angular/etc.]
- **State Management:** [Redux/Vuex/Context/etc.]
- **UI Library:** [Material-UI/Bootstrap/etc.]
- **Build Tools:** [Webpack/Vite/etc.]

### Database & Storage
- **Primary Database:** [PostgreSQL/MySQL/MongoDB/etc.]
- **Cache Layer:** [Redis/Memcached/None]
- **File Storage:** [S3/Local/etc.]
- **Search Engine:** [Elasticsearch/None]

### Infrastructure & DevOps
- **Hosting:** [AWS/Azure/GCP/On-premise]
- **Container:** [Docker/None]
- **Orchestration:** [Kubernetes/Docker Compose/None]
- **CI/CD:** [Jenkins/GitHub Actions/GitLab CI/etc.]

## Architecture Overview

### System Architecture
```
[ASCII diagram or description of system components]
```

### Request Flow
1. [Step 1: Client request]
2. [Step 2: Load balancer/Gateway]
3. [Step 3: Application server]
4. [Step 4: Business logic]
5. [Step 5: Database interaction]
6. [Step 6: Response generation]

### Component Breakdown

#### Core Components
1. **[Component Name]**
   - Purpose: [Description]
   - Technology: [Tech used]
   - Dependencies: [Other components]
   - Criticality: [High/Medium/Low]

2. **[Component Name]**
   - Purpose: [Description]
   - Technology: [Tech used]
   - Dependencies: [Other components]
   - Criticality: [High/Medium/Low]

#### Supporting Components
[List and describe supporting components]

## Data Architecture

### Data Models
- **User Model:** [Description]
- **[Model Name]:** [Description]
- **[Model Name]:** [Description]

### Data Flow Patterns
1. **[Pattern Name]:** [Description]
2. **[Pattern Name]:** [Description]

### Data Storage Strategy
- **Transactional Data:** [Storage approach]
- **Analytics Data:** [Storage approach]
- **File/Media Storage:** [Storage approach]

## API Architecture

### API Design Pattern
- **Style:** [REST/GraphQL/RPC]
- **Versioning:** [Strategy]
- **Authentication:** [Method]
- **Rate Limiting:** [Yes/No, details]

### Key API Groups
1. **[Group Name]:** [Purpose and endpoints]
2. **[Group Name]:** [Purpose and endpoints]

### External Integrations
- **[Service Name]:** [Purpose and integration method]
- **[Service Name]:** [Purpose and integration method]

## Security Architecture

### Authentication & Authorization
- **Method:** [JWT/Session/OAuth/etc.]
- **Provider:** [Internal/Auth0/Okta/etc.]
- **Permissions Model:** [RBAC/ACL/etc.]

### Data Security
- **Encryption at Rest:** [Yes/No, method]
- **Encryption in Transit:** [Yes/No, method]
- **Sensitive Data Handling:** [Approach]

### Security Measures
- **Input Validation:** [Approach]
- **SQL Injection Protection:** [Method]
- **XSS Protection:** [Method]
- **CSRF Protection:** [Method]

## Performance Characteristics

### Current Metrics
- **Average Response Time:** [ms]
- **Peak Load:** [requests/second]
- **Database Query Time:** [avg ms]
- **Memory Usage:** [MB/GB]

### Bottlenecks Identified
1. [Bottleneck description and impact]
2. [Bottleneck description and impact]

### Optimization Opportunities
1. [Optimization suggestion]
2. [Optimization suggestion]

## Scalability Analysis

### Current Limitations
- **Horizontal Scaling:** [Capable/Limited/Not possible]
- **Vertical Scaling:** [Current limits]
- **Database Scaling:** [Strategy]

### Growth Considerations
- **Expected Growth:** [Projection]
- **Scaling Strategy:** [Approach]
- **Resource Requirements:** [Estimates]

## Technical Debt Assessment

### High Priority Issues
1. **[Issue]:** [Description and impact]
2. **[Issue]:** [Description and impact]

### Medium Priority Issues
1. **[Issue]:** [Description and impact]
2. **[Issue]:** [Description and impact]

### Low Priority Issues
1. **[Issue]:** [Description and impact]

## Migration Complexity Assessment

### Complexity Factors
- **Codebase Size:** [LOC, number of files]
- **API Endpoints:** [Count]
- **Database Complexity:** [Tables/Collections count]
- **External Dependencies:** [Count and criticality]
- **Business Logic Complexity:** [High/Medium/Low]

### Migration Challenges
1. **[Challenge]:** [Description and mitigation approach]
2. **[Challenge]:** [Description and mitigation approach]

### Migration Opportunities
1. **[Opportunity]:** [How Kailash can improve this]
2. **[Opportunity]:** [How Kailash can improve this]

## Recommendations

### Immediate Actions
1. [Action item]
2. [Action item]

### Short-term Improvements
1. [Improvement suggestion]
2. [Improvement suggestion]

### Long-term Strategy
1. [Strategic recommendation]
2. [Strategic recommendation]

## Appendices

### A. File Structure
```
project/
├── src/
│   ├── [directory]/
│   └── [directory]/
├── tests/
├── config/
└── [other directories]
```

### B. Key Configuration Files
- **[File]:** [Purpose]
- **[File]:** [Purpose]

### C. Environment Variables
- **[Variable]:** [Purpose]
- **[Variable]:** [Purpose]

### D. Third-party Services
- **[Service]:** [Purpose and credentials location]
- **[Service]:** [Purpose and credentials location]

## Next Steps

1. Review this analysis with the team
2. Validate findings with system tests
3. Create detailed migration plan
4. Begin proof of concept implementation

---
**Document Version:** 1.0
**Last Updated:** [Date]
**Reviewed By:** [Names]
