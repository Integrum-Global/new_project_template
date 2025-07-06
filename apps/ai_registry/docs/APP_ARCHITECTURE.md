# AI Registry App Architecture - Pure Kailash SDK

## 🏗️ Recommended App Structure

### Single App with Multiple Modules
Since AI Registry is conceptually one application (AI use case registry with RAG capabilities), it should be structured as one Kailash app with multiple modules:

```
ai_registry/
├── app.py                    # Main application entry point & orchestrator
├── mcp_server.py            # Enhanced MCP Server implementation
├── modules/                 # Business logic modules
│   ├── rag/                # RAG processing module
│   │   ├── document_processor.py
│   │   ├── knowledge_extractor.py
│   │   └── embedding_manager.py
│   ├── search/             # Search & retrieval module
│   │   ├── semantic_search.py
│   │   ├── similarity_engine.py
│   │   └── result_formatter.py
│   ├── analysis/           # Analytics & insights module
│   │   ├── trend_analyzer.py
│   │   ├── domain_analyzer.py
│   │   └── cross_domain_synthesis.py
│   └── registry/           # Core registry management
│       ├── indexer.py
│       ├── data_manager.py
│       └── statistics.py
├── workflows/              # Kailash workflows for business logic
│   ├── rag_workflows.py    # PDF processing, extraction workflows
│   ├── search_workflows.py # Search and discovery workflows
│   ├── analysis_workflows.py # Trend analysis workflows
│   └── export_workflows.py # Data export workflows
├── data/                   # Configuration and assets
│   ├── app_config.yaml     # Main app configuration
│   ├── registry_data/      # AI registry datasets
│   ├── knowledge_base/     # Generated markdown files
│   └── embeddings/         # Vector storage
├── deployment/             # Deployment configurations
│   ├── docker/            # Container setup
│   ├── k8s/               # Kubernetes manifests
│   └── infrastructure/    # Infrastructure as code
└── tests/                 # Comprehensive test suite
    ├── unit/              # Unit tests for modules
    ├── integration/       # Integration tests for workflows
    └── e2e/               # End-to-end app tests
```

## 🔗 Core SDK Integration Strategy

### Multi-App Architecture in Core SDK
```
Core Kailash SDK:
├── apps/
│   ├── user_management/     # User authentication & authorization
│   ├── ai_registry/         # Our AI Registry app (portable)
│   ├── data_processing/     # ETL and data pipeline apps
│   ├── notification/        # Notification and messaging
│   └── analytics/           # Cross-app analytics
├── shared/
│   ├── config/             # Shared configuration patterns
│   ├── models/             # Common data models
│   ├── security/           # Security and auth utilities
│   └── infrastructure/     # Shared infrastructure components
└── runtime/
    ├── app_manager.py      # App lifecycle management
    ├── service_discovery.py # Inter-app communication
    └── resource_sharing.py # Shared resource management
```

### App Interaction Patterns
1. **Resource Sharing**: Apps expose MCP resources that other apps can consume
2. **Workflow Composition**: Apps can invoke workflows from other apps
3. **Event-Driven**: Apps communicate through event publishing/subscribing
4. **Configuration Sharing**: Common settings and credentials

## 🎯 Pure Kailash Implementation

### 1. Enhanced MCP Server Foundation
```python
# ai_registry/app.py
from kailash.mcp import MCPServer
from .modules.rag import RAGModule
from .modules.search import SearchModule
from .modules.analysis import AnalysisModule
from .workflows import RAGWorkflows, SearchWorkflows, AnalysisWorkflows

class AIRegistryApp:
    \"\"\"Pure Kailash SDK application for AI Registry with RAG capabilities.\"\"\"

    def __init__(self, config_file=None, config_override=None):
        # Enhanced MCP Server with all production features
        self.server = MCPServer(
            name="ai-registry",
            config_file=config_file,
            config_override=config_override,
            enable_cache=True,
            cache_ttl=300,
            enable_metrics=True,
            enable_formatting=True
        )

        # Initialize modules
        self.rag_module = RAGModule(self.server)
        self.search_module = SearchModule(self.server)
        self.analysis_module = AnalysisModule(self.server)

        # Initialize workflows
        self.rag_workflows = RAGWorkflows(self.server, self.rag_module)
        self.search_workflows = SearchWorkflows(self.server, self.search_module)
        self.analysis_workflows = AnalysisWorkflows(self.server, self.analysis_module)

        # Setup MCP components
        self._setup_tools()
        self._setup_resources()
        self._setup_workflows()

    def run(self):
        \"\"\"Start the AI Registry application.\"\"\"
        self.server.run()
```

### 2. Module-Based Business Logic
```python
# ai_registry/modules/rag/rag_module.py
from kailash import Workflow
from kailash.nodes.ai import LLMAgentNode
from kailash.nodes.data import DocumentSourceNode
from kailash.runtime import LocalRuntime

class RAGModule:
    \"\"\"RAG processing module using pure Kailash components.\"\"\"

    def __init__(self, server):
        self.server = server
        self.runtime = LocalRuntime()
        self._setup_agents()

    def _setup_agents(self):
        \"\"\"Setup LLM agents for document processing.\"\"\"
        self.document_analyzer = LLMAgentNode(
            name="document_analyzer",
            model="gpt-4o-mini",
            system_prompt=self._get_analysis_prompt()
        )

        self.use_case_extractor = LLMAgentNode(
            name="use_case_extractor",
            model="gpt-4o-mini",
            system_prompt=self._get_extraction_prompt()
        )

    def process_pdf_document(self, pdf_path: str) -> dict:
        \"\"\"Process PDF using Kailash workflow.\"\"\"
        workflow = self._create_pdf_processing_workflow()
        parameters = {"pdf_path": pdf_path}
        result, run_id = self.runtime.execute(workflow, parameters=parameters)
        return result

    def _create_pdf_processing_workflow(self) -> Workflow:
        \"\"\"Create workflow for PDF processing.\"\"\"
        workflow = Workflow("pdf_processing", "Process PDF and extract use cases")

        # Load PDF document
        doc_loader = DocumentSourceNode(name="pdf_loader")
        workflow.add_node("pdf_loader", doc_loader)

        # Analyze structure
        workflow.add_node("analyzer", self.document_analyzer)
        workflow.connect("pdf_loader", "analyzer", mapping={"content": "input"})

        # Extract use cases
        workflow.add_node("extractor", self.use_case_extractor)
        workflow.connect("analyzer", "extractor", mapping={"response": "context"})

        return workflow
```

### 3. Workflow-Based Business Operations
```python
# ai_registry/workflows/rag_workflows.py
class RAGWorkflows:
    \"\"\"RAG workflows for document processing and knowledge extraction.\"\"\"

    def __init__(self, server, rag_module):
        self.server = server
        self.rag_module = rag_module
        self._register_tools()

    def _register_tools(self):
        \"\"\"Register RAG tools with the MCP server.\"\"\"

        @self.server.tool(
            cache_key="pdf_analysis",
            cache_ttl=3600,  # Cache for 1 hour
            format_response="markdown"
        )
        def analyze_pdf_document(pdf_path: str) -> dict:
            \"\"\"Analyze PDF document and extract structure.\"\"\"
            return self.rag_module.process_pdf_document(pdf_path)

        @self.server.tool(
            cache_key="extract_use_cases",
            cache_ttl=1800,  # Cache for 30 minutes
            format_response="json"
        )
        def extract_use_cases_from_pdf(pdf_path: str, section: str = None) -> dict:
            \"\"\"Extract use cases from specific PDF section.\"\"\"
            return self.rag_module.extract_use_cases(pdf_path, section)

        @self.server.tool(
            cache_key="generate_knowledge_base",
            cache_ttl=7200,  # Cache for 2 hours
            format_response="markdown"
        )
        def generate_markdown_knowledge_base(source_pdfs: list) -> dict:
            \"\"\"Generate markdown knowledge base from PDF sources.\"\"\"
            return self.rag_module.generate_knowledge_base(source_pdfs)
```

### 4. Configuration Management
```yaml
# ai_registry/data/app_config.yaml
app:
  name: "ai-registry"
  version: "1.0.0"
  description: "AI Registry with RAG capabilities"

server:
  transport: "stdio"  # or "http" for REST API

cache:
  enabled: true
  default_ttl: 300
  pdf_analysis_ttl: 3600
  search_ttl: 300
  statistics_ttl: 600

modules:
  rag:
    models:
      document_analyzer: "gpt-4o-mini"
      use_case_extractor: "gpt-4o-mini"
      embedding_model: "text-embedding-3-small"
    processing:
      chunk_size: 2000
      chunk_overlap: 200
      max_tokens: 4000

  search:
    default_limit: 20
    max_limit: 100
    similarity_threshold: 0.75

  analysis:
    trend_analysis_model: "gpt-4o"
    synthesis_model: "gpt-4o"

data:
  registry_file: "data/registry_data/combined_ai_registry.json"
  knowledge_base_path: "data/knowledge_base"
  embeddings_path: "data/embeddings"
  pdf_sources:
    - "data/2021 - Section 7.pdf"
    - "data/2024 - Section 7.pdf"

workflows:
  timeouts:
    pdf_processing: 300  # 5 minutes
    search: 30          # 30 seconds
    analysis: 120       # 2 minutes
```

## 🔄 Migration Benefits

### Immediate Benefits
1. **Pure Kailash Architecture**: 100% SDK components and patterns
2. **Production Ready**: Built-in caching, metrics, monitoring
3. **Highly Modular**: Clear separation of concerns
4. **Configurable**: Environment-aware configuration
5. **Testable**: Workflow-based testing strategies

### Core SDK Integration Benefits
1. **Drop-in Compatibility**: Minimal changes needed for core SDK
2. **Resource Sharing**: Can share resources with other apps
3. **Service Discovery**: Auto-discovery by other apps
4. **Configuration Inheritance**: Inherit shared SDK configuration
5. **Lifecycle Management**: Managed by SDK app manager

## 🚀 Implementation Strategy

### Phase 1: Restructure as Pure Kailash App
1. Refactor current code to use Enhanced MCP Server
2. Create module-based architecture
3. Implement workflow-based business logic
4. Add comprehensive configuration management

### Phase 2: Optimize for Core SDK
1. Abstract configuration for shared settings
2. Implement resource sharing patterns
3. Add service discovery capabilities
4. Create inter-app communication interfaces

### Phase 3: Core SDK Integration
1. Move app to core SDK apps/ directory
2. Update imports and configuration paths
3. Integration testing with other SDK apps
4. Documentation and examples

This architecture ensures the AI Registry is built with pure Kailash patterns while being optimally structured for future core SDK integration.
