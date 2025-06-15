# Studio - Visual Workflow Builder

Real-time workflow designer with AI-powered generation and visual execution monitoring.

## 📋 What This App Does

**Core Features:**
- Visual workflow designer with drag-and-drop
- AI chat for natural language workflow creation
- Real-time execution monitoring via WebSocket
- Code export to Python/YAML
- 98+ nodes with dynamic schemas
- 20+ workflow templates

**Unique Capabilities:**
- Live node progress visualization
- Multi-tenant workflow isolation
- Collaborative editing support
- Export styles: production, development, tutorial

## 🚀 Quick Start

```bash
# Install and run
cd apps/studio
pip install -e .
studio server  # API at http://localhost:8000

# Access points
# API Docs: http://localhost:8000/api/docs
# WebSocket: ws://localhost:8000/ws
```

## 📊 API Endpoints

### Workflow Management
```
POST   /api/workflows              # Create/update + AI generation
GET    /api/workflows/{id}         # Get with execution status
DELETE /api/workflows/{id}         # Delete workflow
GET    /api/workflows              # List with filtering
```

### Real-time Execution
```
POST   /api/execution/start        # Start execution
GET    /api/execution/{id}         # Get status
POST   /api/execution/{id}/cancel  # Cancel running
WS     /ws                         # Real-time updates
```

### AI Chat Interface
```
POST   /api/chat                   # AI conversation
POST   /api/chat/generate          # Direct generation
POST   /api/chat/suggest-nodes     # Node recommendations
```

### Node Catalog
```
GET    /api/nodes/types            # All 98+ nodes
GET    /api/nodes/types/{type}     # Node schema
POST   /api/nodes/validate         # Validate config
GET    /api/nodes/categories       # Browse by category
```

### Code Export
```
POST   /api/export/workflows/{id}  # Generate code
GET    /api/export/workflows/{id}/download  # Download file
```

## 💻 CLI Commands

```bash
# Server management
studio server --host 0.0.0.0 --port 8000
studio init                        # Initialize database

# Workflow operations
studio workflows list
studio workflows export <id> --format python
studio workflows delete <id>

# Execution monitoring
studio executions list --status running
studio executions logs <id>

# Template management
studio templates list
studio templates create --from-workflow <id>

# Maintenance
studio cleanup --days 30           # Remove old executions
studio stats                       # System statistics
```

## 🔄 Real-Time Features

### WebSocket Events
```javascript
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:8000/ws');

// Event types
ws.on('execution_started', (data) => {
  console.log(`Execution ${data.execution_id} started`);
});

ws.on('node_progress', (data) => {
  console.log(`Node ${data.node_id}: ${data.status}`);
  console.log(`Progress: ${data.progress.percentage}%`);
});

ws.on('execution_completed', (data) => {
  console.log(`Results: ${data.result}`);
});
```

### Server-Sent Events
```javascript
// Alternative: SSE for one-way updates
const events = new EventSource('/api/events/execution/<id>');
events.onmessage = (event) => {
  const data = JSON.parse(event.data);
  updateProgress(data);
};
```

## 🤖 AI-Powered Features

### Natural Language Workflow Creation
```python
# POST /api/chat
{
    "message": "Create a workflow that reads customer data from CSV, filters by region, and sends personalized emails",
    "context": {"industry": "retail", "complexity": "medium"}
}

# Response includes:
# - Generated workflow JSON
# - Explanation of nodes used
# - Suggested improvements
```

### Intelligent Node Suggestions
```python
# POST /api/chat/suggest-nodes
{
    "current_workflow": {...},
    "last_node_id": "csv_reader_1",
    "intent": "filter_data"
}

# Returns ranked node suggestions with reasons
```

## 📑 Template Library

### Business Templates
- **Customer Onboarding**: Multi-step validation and provisioning
- **Invoice Processing**: OCR, validation, approval workflow
- **Lead Scoring**: AI-powered scoring with CRM integration
- **Report Generation**: Data aggregation and distribution

### Data Processing Templates
- **CSV ETL Pipeline**: Read, transform, validate, load
- **API Data Sync**: Periodic fetch and synchronization
- **Data Quality Check**: Validation and cleansing

### AI/ML Templates
- **Document Analysis**: Extract insights from documents
- **Sentiment Analysis**: Analyze customer feedback
- **Content Generation**: AI-powered content creation

## 📁 App-Specific Components

### Custom Models
- `StudioWorkflow`: Extended with visual positioning data
- `WorkflowExecution`: Real-time progress tracking
- `NodePosition`: X/Y coordinates for visual layout
- `ChatSession`: AI conversation context

### Specialized Services
- `VisualLayoutService`: Auto-layout algorithms
- `RealtimeExecutionService`: WebSocket broadcasting
- `AIGenerationService`: LLM integration for workflows
- `TemplateAnalyticsService`: Usage tracking

## 🔧 Configuration

### Environment Variables
```bash
# Server
STUDIO_HOST=0.0.0.0
STUDIO_PORT=8000

# Database
STUDIO_DATABASE_URL=sqlite:///studio.db
# For production: postgresql://user:pass@localhost/studio

# WebSocket
STUDIO_WS_HEARTBEAT=30
STUDIO_WS_MAX_CONNECTIONS=1000

# AI Integration
STUDIO_OPENAI_API_KEY=sk-...
STUDIO_AI_MODEL=gpt-4

# CORS (for frontend)
STUDIO_CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

## 📊 Performance Optimization

### Database Indexes
```sql
-- Workflow queries
CREATE INDEX idx_workflows_tenant_updated
    ON workflows(tenant_id, updated_at DESC);

-- Execution tracking
CREATE INDEX idx_executions_workflow_status
    ON executions(workflow_id, status);

-- Template analytics
CREATE INDEX idx_template_usage
    ON template_usage(template_id, used_at);
```

### Caching Strategy
- Node schemas: 1 hour TTL
- Template list: 15 minutes
- Workflow metadata: 5 minutes
- Execution results: Until completed

## 🚀 Production Deployment

### Docker
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -e .
CMD ["studio", "server", "--host", "0.0.0.0"]
```

### Kubernetes
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: studio-api
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: studio
        image: kailash/studio:latest
        env:
        - name: STUDIO_DATABASE_URL
          value: postgresql://postgres:5432/studio
```

## 📊 Metrics & Monitoring

### Key Metrics
- API response time: <200ms average
- WebSocket latency: <50ms
- Concurrent workflows: 100+
- Node discovery time: <100ms

### Health Checks
```bash
# API health
curl http://localhost:8000/health

# WebSocket health
wscat -c ws://localhost:8000/ws/health
```

## 📚 App Documentation

| Document | Purpose |
|----------|---------|
| [CLAUDE.md](CLAUDE.md) | Developer navigation and code guide |
| [API Docs](http://localhost:8000/api/docs) | Interactive API documentation |
| [WebSocket Protocol](docs/WEBSOCKET.md) | Real-time event specifications |

## 🎯 Why Studio?

1. **Visual Design**: No-code workflow creation
2. **AI Assistant**: Natural language to workflow
3. **Real-time**: Live execution monitoring
4. **Export**: Generate production-ready code
5. **Templates**: Start from proven patterns
6. **Collaborative**: Multi-tenant with isolation
