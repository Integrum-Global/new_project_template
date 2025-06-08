# Complete Solution Patterns

End-to-end business solution patterns using Kailash SDK.

## 📊 Customer Data Processing Solution

### Business Use Case
Process customer data from multiple sources, enrich with AI insights, and output to CRM system.

### Complete Solution
```python
from kailash import Workflow
from kailash.nodes.data import CSVReaderNode, DatabaseQueryNode, CSVWriterNode
from kailash.nodes.ai import LLMAgentNode
from kailash.nodes.api import RESTClientNode
from kailash.nodes.code import PythonCodeNode
from kailash.runtime import LocalRuntime

def create_customer_processing_solution():
    """Complete customer data processing solution"""
    
    workflow = Workflow("customer_data_solution")
    
    # 1. Extract: Read customer data from multiple sources
    csv_customers = CSVReaderNode(
        "csv_source",
        file_path="${CUSTOMER_CSV_PATH}"
    )
    
    db_customers = DatabaseQueryNode(
        "db_source",
        connection_string="${DATABASE_URL}",
        query="""
        SELECT customer_id, email, last_purchase_date, total_spent
        FROM customers 
        WHERE status = 'active' 
        AND last_purchase_date >= CURRENT_DATE - INTERVAL '90 days'
        """
    )
    
    # 2. Transform: Merge and clean data
    data_merger = PythonCodeNode(
        "merge_data",
        code="""
def process(csv_data, db_data):
    # Create lookup for database data
    db_lookup = {row['customer_id']: row for row in db_data}
    
    # Merge CSV data with database data
    enriched_customers = []
    for csv_row in csv_data:
        customer_id = csv_row.get('customer_id')
        db_row = db_lookup.get(customer_id, {})
        
        # Merge data
        merged = {
            'customer_id': customer_id,
            'name': csv_row.get('name', '').strip().title(),
            'email': csv_row.get('email', '').lower(),
            'phone': csv_row.get('phone', ''),
            'last_purchase_date': db_row.get('last_purchase_date'),
            'total_spent': db_row.get('total_spent', 0),
            'segment': determine_segment(db_row),
            'data_quality_score': calculate_quality_score(csv_row, db_row)
        }
        enriched_customers.append(merged)
    
    return enriched_customers

def determine_segment(db_row):
    total_spent = db_row.get('total_spent', 0)
    if total_spent > 10000:
        return 'VIP'
    elif total_spent > 1000:
        return 'Premium'
    else:
        return 'Standard'

def calculate_quality_score(csv_row, db_row):
    score = 0
    if csv_row.get('email') and '@' in csv_row['email']:
        score += 25
    if csv_row.get('phone') and len(csv_row['phone']) >= 10:
        score += 25
    if db_row.get('last_purchase_date'):
        score += 25
    if csv_row.get('name') and len(csv_row['name']) > 2:
        score += 25
    return score
        """
    )
    
    # 3. AI Enhancement: Generate customer insights
    ai_insights = LLMAgentNode(
        "customer_insights",
        model_config={
            "provider": "openai",
            "model": "gpt-4",
            "temperature": 0.1
        },
        system_prompt="""You are a customer analytics expert. 
        Analyze customer data and provide actionable business insights.
        Return insights in structured JSON format.""",
        user_prompt_template="""
        Analyze this customer data and provide insights:
        
        Customer Segment Distribution:
        {segment_summary}
        
        Data Quality Issues:
        {quality_issues}
        
        Provide insights in this JSON format:
        {
            "key_findings": ["finding1", "finding2"],
            "recommendations": ["rec1", "rec2"],
            "risk_customers": ["customer_id1", "customer_id2"],
            "upsell_opportunities": ["customer_id1", "customer_id2"]
        }
        """
    )
    
    # 4. Load: Output to CRM system
    crm_integration = RESTClientNode(
        "crm_upload",
        base_url="${CRM_API_URL}",
        auth_type="bearer_token",
        auth_config={"token": "${CRM_API_TOKEN}"},
        default_headers={"Content-Type": "application/json"}
    )
    
    # 5. Backup: Save processed data
    backup_writer = CSVWriterNode(
        "backup_data",
        file_path="${OUTPUT_PATH}/processed_customers_{timestamp}.csv"
    )
    
    # Build workflow
    workflow.add_node(csv_customers)
    workflow.add_node(db_customers)
    workflow.add_node(data_merger)
    workflow.add_node(ai_insights)
    workflow.add_node(crm_integration)
    workflow.add_node(backup_writer)
    
    # Connect nodes
    workflow.connect(csv_customers, data_merger, mapping={"data": "csv_data"})
    workflow.connect(db_customers, data_merger, mapping={"result": "db_data"})
    workflow.connect(data_merger, ai_insights, mapping={"result": "enriched_customers"})
    workflow.connect(data_merger, crm_integration, mapping={"result": "customer_data"})
    workflow.connect(data_merger, backup_writer, mapping={"result": "data"})
    
    return workflow

# Usage
def main():
    workflow = create_customer_processing_solution()
    runtime = LocalRuntime()
    
    parameters = {
        "CUSTOMER_CSV_PATH": "data/customers.csv",
        "DATABASE_URL": "postgresql://user:pass@localhost/crm",
        "CRM_API_URL": "https://api.crm.company.com",
        "CRM_API_TOKEN": "your-crm-token",
        "OUTPUT_PATH": "data/processed"
    }
    
    result = runtime.execute(workflow, parameters=parameters)
    print(f"Processed {len(result.get('processed_customers', []))} customers")

if __name__ == "__main__":
    main()
```

## 📈 Sales Analytics Solution

### Business Use Case
Analyze sales data, predict trends, and generate automated reports for stakeholders.

### Complete Solution
```python
def create_sales_analytics_solution():
    """Sales analytics and reporting solution"""
    
    workflow = Workflow("sales_analytics_solution")
    
    # 1. Data Collection
    sales_reader = DatabaseQueryNode(
        "sales_data",
        connection_string="${SALES_DB_URL}",
        query="""
        SELECT 
            sale_date, product_id, customer_id, quantity, amount,
            sales_rep_id, region, channel
        FROM sales 
        WHERE sale_date >= CURRENT_DATE - INTERVAL '12 months'
        ORDER BY sale_date DESC
        """
    )
    
    # 2. Data Analysis
    analytics_processor = PythonCodeNode(
        "analytics",
        code="""
import pandas as pd
from datetime import datetime, timedelta

def process(sales_data):
    df = pd.DataFrame(sales_data)
    df['sale_date'] = pd.to_datetime(df['sale_date'])
    
    # Calculate key metrics
    analytics = {
        'total_revenue': df['amount'].sum(),
        'total_transactions': len(df),
        'avg_transaction_value': df['amount'].mean(),
        'monthly_trends': calculate_monthly_trends(df),
        'top_products': get_top_products(df),
        'top_customers': get_top_customers(df),
        'regional_performance': get_regional_performance(df),
        'forecast': generate_forecast(df)
    }
    
    return analytics

def calculate_monthly_trends(df):
    monthly = df.groupby(df['sale_date'].dt.to_period('M')).agg({
        'amount': 'sum',
        'quantity': 'sum'
    }).to_dict('index')
    
    return {str(k): v for k, v in monthly.items()}

def get_top_products(df, limit=10):
    return df.groupby('product_id')['amount'].sum().nlargest(limit).to_dict()

def get_top_customers(df, limit=10):
    return df.groupby('customer_id')['amount'].sum().nlargest(limit).to_dict()

def get_regional_performance(df):
    return df.groupby('region')['amount'].sum().to_dict()

def generate_forecast(df):
    # Simple trend-based forecast
    monthly_revenue = df.groupby(df['sale_date'].dt.to_period('M'))['amount'].sum()
    trend = monthly_revenue.pct_change().mean()
    last_month = monthly_revenue.iloc[-1]
    
    return {
        'next_month_forecast': last_month * (1 + trend),
        'growth_rate': trend,
        'confidence': 'medium' if abs(trend) < 0.1 else 'low'
    }
        """,
        imports=["pandas", "datetime"]
    )
    
    # 3. AI Insights
    insights_generator = LLMAgentNode(
        "insights",
        model_config={
            "provider": "openai", 
            "model": "gpt-4",
            "temperature": 0.2
        },
        system_prompt="""You are a sales analytics expert. 
        Analyze sales data and provide strategic business insights.""",
        user_prompt_template="""
        Based on this sales analytics data, provide strategic insights:
        
        Revenue: ${total_revenue:,.2f}
        Transactions: {total_transactions:,}
        Average Transaction: ${avg_transaction_value:.2f}
        Growth Rate: {growth_rate:.1%}
        
        Monthly Trends: {monthly_trends}
        Top Products: {top_products}
        Regional Performance: {regional_performance}
        
        Provide insights in this format:
        1. Key Performance Indicators Summary
        2. Growth Opportunities 
        3. Risk Areas to Monitor
        4. Strategic Recommendations
        """
    )
    
    # 4. Report Generation
    report_generator = PythonCodeNode(
        "report",
        code="""
def process(analytics, insights):
    from datetime import datetime
    
    report = {
        'report_date': datetime.now().isoformat(),
        'executive_summary': {
            'total_revenue': analytics['total_revenue'],
            'growth_rate': analytics['forecast']['growth_rate'],
            'key_insights': insights.get('key_findings', [])
        },
        'detailed_analytics': analytics,
        'ai_insights': insights,
        'recommendations': insights.get('recommendations', [])
    }
    
    return report
        """
    )
    
    # 5. Distribution
    email_sender = RESTClientNode(
        "email_report",
        base_url="${EMAIL_SERVICE_URL}",
        auth_type="api_key",
        auth_config={"api_key": "${EMAIL_API_KEY}"}
    )
    
    dashboard_updater = RESTClientNode(
        "dashboard_update",
        base_url="${DASHBOARD_API_URL}",
        auth_type="bearer_token", 
        auth_config={"token": "${DASHBOARD_TOKEN}"}
    )
    
    # Build workflow
    workflow.add_node(sales_reader)
    workflow.add_node(analytics_processor)
    workflow.add_node(insights_generator)
    workflow.add_node(report_generator)
    workflow.add_node(email_sender)
    workflow.add_node(dashboard_updater)
    
    # Connect workflow
    workflow.connect(sales_reader, analytics_processor, mapping={"result": "sales_data"})
    workflow.connect(analytics_processor, insights_generator, mapping={"result": "analytics"})
    workflow.connect(analytics_processor, report_generator, mapping={"result": "analytics"})
    workflow.connect(insights_generator, report_generator, mapping={"response": "insights"})
    workflow.connect(report_generator, email_sender, mapping={"result": "report_data"})
    workflow.connect(report_generator, dashboard_updater, mapping={"result": "metrics"})
    
    return workflow
```

## 🤖 AI-Powered Document Processing Solution

### Business Use Case
Automatically process incoming documents, extract key information, and route to appropriate departments.

### Complete Solution
```python
def create_document_processing_solution():
    """AI-powered document processing and routing"""
    
    workflow = Workflow("document_processing_solution")
    
    # 1. Document Ingestion
    doc_reader = SharePointGraphReaderNode(
        "document_source",
        tenant_id="${TENANT_ID}",
        client_id="${CLIENT_ID}",
        client_secret="${CLIENT_SECRET}",
        site_url="${SHAREPOINT_SITE}",
        folder_path="/Shared Documents/Incoming"
    )
    
    # 2. Document Classification
    classifier = LLMAgentNode(
        "document_classifier",
        model_config={
            "provider": "openai",
            "model": "gpt-4",
            "temperature": 0.1
        },
        system_prompt="""You are a document classification expert.
        Classify documents and extract key information.""",
        user_prompt_template="""
        Classify this document and extract key information:
        
        Document Content: {document_content}
        
        Return classification in JSON format:
        {
            "document_type": "invoice|contract|report|other",
            "confidence": 0.95,
            "key_entities": {
                "company": "Company Name",
                "amount": 1000.00,
                "date": "2024-01-01",
                "contact": "person@company.com"
            },
            "routing_department": "finance|legal|operations|general",
            "priority": "high|medium|low",
            "action_required": "approval|review|filing|response"
        }
        """
    )
    
    # 3. Data Extraction
    extractor = PythonCodeNode(
        "data_extractor",
        code="""
def process(classification_result, document_content):
    import json
    import re
    
    # Parse AI classification
    classification = json.loads(classification_result)
    
    # Enhanced extraction based on document type
    extracted_data = classification.copy()
    
    doc_type = classification.get('document_type')
    
    if doc_type == 'invoice':
        extracted_data.update(extract_invoice_data(document_content))
    elif doc_type == 'contract':
        extracted_data.update(extract_contract_data(document_content))
    elif doc_type == 'report':
        extracted_data.update(extract_report_data(document_content))
    
    return extracted_data

def extract_invoice_data(content):
    # Extract invoice-specific data
    invoice_patterns = {
        'invoice_number': r'Invoice\s*#?\s*:?\s*([A-Z0-9-]+)',
        'due_date': r'Due\s*Date\s*:?\s*([0-9]{1,2}[/-][0-9]{1,2}[/-][0-9]{2,4})',
        'total_amount': r'Total\s*:?\s*\$?([0-9,]+\.?[0-9]*)'
    }
    
    extracted = {}
    for field, pattern in invoice_patterns.items():
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            extracted[field] = match.group(1)
    
    return extracted

def extract_contract_data(content):
    # Extract contract-specific data
    return {
        'contract_value': extract_monetary_value(content),
        'term_length': extract_term_length(content),
        'parties': extract_parties(content)
    }

def extract_report_data(content):
    # Extract report-specific data
    return {
        'report_period': extract_date_range(content),
        'key_metrics': extract_metrics(content)
    }
        """
    )
    
    # 4. Routing Logic
    router = PythonCodeNode(
        "document_router",
        code="""
def process(extracted_data):
    routing_rules = {
        'finance': {
            'document_types': ['invoice', 'expense_report'],
            'amount_threshold': 1000,
            'approval_required': True
        },
        'legal': {
            'document_types': ['contract', 'agreement'],
            'priority_escalation': True
        },
        'operations': {
            'document_types': ['report', 'memo'],
            'auto_filing': True
        }
    }
    
    doc_type = extracted_data.get('document_type')
    amount = extracted_data.get('key_entities', {}).get('amount', 0)
    department = extracted_data.get('routing_department', 'general')
    
    # Determine routing actions
    actions = []
    
    if department in routing_rules:
        rules = routing_rules[department]
        
        if doc_type in rules.get('document_types', []):
            if rules.get('approval_required') and amount > rules.get('amount_threshold', 0):
                actions.append('require_approval')
            if rules.get('auto_filing'):
                actions.append('auto_file')
            if rules.get('priority_escalation'):
                actions.append('escalate_priority')
    
    return {
        'department': department,
        'actions': actions,
        'extracted_data': extracted_data,
        'routing_timestamp': datetime.now().isoformat()
    }
        """
    )
    
    # 5. Action Execution
    notification_sender = RESTClientNode(
        "send_notifications",
        base_url="${NOTIFICATION_SERVICE_URL}",
        auth_type="api_key",
        auth_config={"api_key": "${NOTIFICATION_API_KEY}"}
    )
    
    # Build workflow
    workflow.add_node(doc_reader)
    workflow.add_node(classifier)
    workflow.add_node(extractor)
    workflow.add_node(router)
    workflow.add_node(notification_sender)
    
    # Connect workflow
    workflow.connect(doc_reader, classifier, mapping={"content": "document_content"})
    workflow.connect(classifier, extractor, mapping={"response": "classification_result"})
    workflow.connect(doc_reader, extractor, mapping={"content": "document_content"})
    workflow.connect(extractor, router, mapping={"result": "extracted_data"})
    workflow.connect(router, notification_sender, mapping={"result": "routing_info"})
    
    return workflow
```

## 📋 Solution Implementation Guide

### 1. **Setup Requirements**
```bash
# Install dependencies
pip install kailash[full]
pip install pandas openai

# Set environment variables
export DATABASE_URL="postgresql://user:pass@localhost/db"
export CRM_API_TOKEN="your-crm-token"
export OPENAI_API_KEY="your-openai-key"
```

### 2. **Configuration Files**
```yaml
# config/solution.yaml
solution:
  name: "customer_processing"
  version: "1.0.0"
  
database:
  connection_string: "${DATABASE_URL}"
  pool_size: 10
  timeout: 30

apis:
  crm:
    base_url: "${CRM_API_URL}"
    token: "${CRM_API_TOKEN}"
    rate_limit: 100  # requests per minute

ai:
  provider: "openai"
  model: "gpt-4"
  temperature: 0.1
  max_tokens: 2000
```

### 3. **Deployment Configuration**
```python
# Deploy with production settings
runtime = LocalRuntime(
    max_concurrent_workflows=5,
    enable_monitoring=True,
    log_level="INFO"
)

# Execute with error handling
try:
    result = runtime.execute(workflow, parameters=parameters)
    logger.info(f"Solution completed successfully: {result}")
except Exception as e:
    logger.error(f"Solution failed: {e}")
    # Implement retry logic or alerting
```

## 🔗 Related Patterns

- **[Integration Patterns](02-integration-patterns.md)** - API and system integration
- **[Deployment Patterns](03-deployment-patterns.md)** - Production deployment
- **[Migration Patterns](04-migration-patterns.md)** - Legacy system conversion