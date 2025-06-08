# Integration Patterns - Solution Development

Common patterns for integrating Kailash workflows with existing systems and APIs.

## 🔌 REST API Integration

### Basic REST Client Pattern
```python
from kailash import Workflow
from kailash.nodes.api import RESTClientNode
from kailash.nodes.data import CSVReaderNode, CSVWriterNode
from kailash.runtime import LocalRuntime

# Create workflow with API integration
workflow = Workflow("api_integration_solution")

# Read data
data_source = CSVReaderNode("data_reader", file_path="input_data.csv")
workflow.add_node(data_source)

# Call external API
api_client = RESTClientNode(
    "external_api",
    base_url="https://api.example.com",
    auth_type="bearer_token",
    auth_config={"token": "${API_TOKEN}"}
)
workflow.add_node(api_client)

# Process API responses
result_writer = CSVWriterNode("output_writer", file_path="api_results.csv")
workflow.add_node(result_writer)

# Connect workflow
workflow.connect(data_source, api_client, mapping={"data": "payload"})
workflow.connect(api_client, result_writer, mapping={"response": "data"})

# Execute
runtime = LocalRuntime()
runtime.execute(workflow, parameters={"API_TOKEN": "your-token-here"})
```

### API with Authentication
```python
# OAuth2 Authentication
oauth_api = RESTClientNode(
    "oauth_api",
    base_url="https://secure-api.example.com",
    auth_type="oauth2",
    auth_config={
        "client_id": "${CLIENT_ID}",
        "client_secret": "${CLIENT_SECRET}",
        "token_url": "https://auth.example.com/token"
    }
)

# API Key Authentication  
api_key_client = RESTClientNode(
    "api_key_client",
    base_url="https://api.service.com",
    auth_type="api_key",
    auth_config={
        "header_name": "X-API-Key",
        "api_key": "${SERVICE_API_KEY}"
    }
)
```

## 📊 Database Integration

### Database Query Pattern
```python
from kailash.nodes.data import DatabaseQueryNode, DatabaseWriterNode

# Read from database
db_source = DatabaseQueryNode(
    "db_reader",
    connection_string="${DATABASE_URL}",
    query="SELECT * FROM customers WHERE status = 'active'"
)

# Write to database
db_sink = DatabaseWriterNode(
    "db_writer", 
    connection_string="${DATABASE_URL}",
    table_name="processed_customers"
)

workflow.add_node(db_source)
workflow.add_node(db_sink)
```

### ETL Pipeline Pattern
```python
from kailash.nodes.code import PythonCodeNode

# Extract
extractor = DatabaseQueryNode("extract", connection_string="${SOURCE_DB}")

# Transform
transformer = PythonCodeNode(
    "transform",
    code="""
def process(data):
    # Clean and transform data
    processed = []
    for record in data:
        clean_record = {
            'id': record['customer_id'],
            'name': record['full_name'].strip().title(),
            'email': record['email'].lower(),
            'score': calculate_score(record)
        }
        processed.append(clean_record)
    return processed
    
def calculate_score(record):
    # Business logic for scoring
    return record.get('revenue', 0) * 0.1
"""
)

# Load
loader = DatabaseWriterNode("load", connection_string="${TARGET_DB}")

# Connect ETL pipeline
workflow.connect(extractor, transformer, mapping={"result": "data"})
workflow.connect(transformer, loader, mapping={"result": "data"})
```

## 🤝 SharePoint Integration

### SharePoint Document Processing
```python
from kailash.nodes.data import SharePointGraphReaderNode

# Read from SharePoint
sharepoint_reader = SharePointGraphReaderNode(
    "sharepoint_source",
    tenant_id="${TENANT_ID}",
    client_id="${CLIENT_ID}",
    client_secret="${CLIENT_SECRET}",
    site_url="https://company.sharepoint.com/sites/data",
    folder_path="/Shared Documents/Reports"
)

workflow.add_node(sharepoint_reader)
```

## 🔄 Event-Driven Integration

### Webhook Response Pattern
```python
from kailash.nodes.api import HTTPRequestNode

# Process webhook data
webhook_processor = PythonCodeNode(
    "webhook_handler",
    code="""
def process(webhook_data):
    # Validate webhook payload
    if not validate_signature(webhook_data):
        raise ValueError("Invalid webhook signature")
    
    # Extract relevant data
    event_type = webhook_data.get('event_type')
    payload = webhook_data.get('data', {})
    
    # Process based on event type
    if event_type == 'order.created':
        return process_new_order(payload)
    elif event_type == 'customer.updated':
        return process_customer_update(payload)
    
    return {"status": "ignored", "event": event_type}

def validate_signature(data):
    # Implement webhook signature validation
    return True
"""
)

# Send acknowledgment
ack_sender = HTTPRequestNode(
    "send_ack",
    method="POST",
    url="${WEBHOOK_ACK_URL}"
)
```

## 🌐 Multi-System Integration

### System Synchronization Pattern
```python
# System A → Transform → System B
workflow = Workflow("system_sync")

# Read from System A
system_a = RESTClientNode("system_a", base_url="${SYSTEM_A_URL}")

# Transform data format
format_transformer = PythonCodeNode(
    "format_converter",
    code="""
def process(system_a_data):
    # Convert System A format to System B format
    converted = []
    for record in system_a_data:
        system_b_record = {
            'external_id': record['id'],
            'name': record['customer_name'],
            'contact_info': {
                'email': record['email'],
                'phone': record['phone_number']
            },
            'metadata': {
                'source': 'system_a',
                'imported_at': datetime.now().isoformat()
            }
        }
        converted.append(system_b_record)
    return converted
"""
)

# Write to System B
system_b = RESTClientNode("system_b", base_url="${SYSTEM_B_URL}")

# Connect systems
workflow.connect(system_a, format_transformer, mapping={"response": "system_a_data"})
workflow.connect(format_transformer, system_b, mapping={"result": "payload"})
```

## 🚀 Environment Configuration

### Production Configuration Pattern
```python
# Use environment variables for all secrets and configs
parameters = {
    "DATABASE_URL": "postgresql://user:pass@localhost/db",
    "API_TOKEN": "your-production-token",
    "CLIENT_ID": "your-oauth-client-id",
    "CLIENT_SECRET": "your-oauth-secret",
    "WEBHOOK_ACK_URL": "https://your-app.com/webhook/ack"
}

runtime.execute(workflow, parameters=parameters)
```

## 📋 Best Practices

### ✅ Do
- Use environment variables for all credentials
- Implement proper error handling and retries
- Validate API responses before processing
- Log integration activities for monitoring
- Use connection pooling for database integrations

### ❌ Avoid
- Hardcoding credentials in workflow code
- Ignoring API rate limits
- Processing unvalidated external data
- Creating circular integration dependencies
- Blocking operations without timeout handling

## 🔗 Related Patterns

- **[REST API Cheatsheet](015-workflow-as-rest-api.md)** - Expose workflows as APIs
- **[Environment Variables](016-environment-variables.md)** - Configuration management
- **[Deployment Patterns](006-deployment-patterns.md)** - Production deployment