"""
RAG Module - Pure Kailash SDK Implementation

Handles document processing, knowledge extraction, and embedding generation
using only Kailash SDK components for optimal portability.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from kailash import Workflow
from kailash.nodes.ai import EmbeddingGeneratorNode, LLMAgentNode
from kailash.nodes.base import Node
from kailash.nodes.data import DirectoryReaderNode, JSONReaderNode
from kailash.nodes.transform import DataTransformer, HierarchicalChunkerNode
from kailash.runtime import LocalRuntime

logger = logging.getLogger(__name__)


class RAGModule:
    """
    RAG processing module using pure Kailash SDK components.

    Provides:
    - PDF document analysis and structure identification
    - Use case extraction with intelligent parsing
    - Knowledge base generation in markdown format
    - Embedding generation for semantic search
    - Vector storage and similarity matching
    """

    def __init__(self, server, runtime: LocalRuntime):
        """
        Initialize the RAG module.

        Args:
            server: Enhanced MCP Server instance
            runtime: Kailash workflow runtime
        """
        self.server = server
        self.runtime = runtime
        self.config = self._load_config()

        # Initialize core components
        self._setup_llm_agents()
        self._setup_data_processors()
        self._setup_embedding_system()

        # Module state
        self.processed_documents = {}
        self.knowledge_base = {}
        self.embeddings_cache = {}
        self._ready = True

        logger.info("RAG Module initialized with pure Kailash components")

    def _load_config(self) -> Dict[str, Any]:
        """Load RAG module configuration."""
        return {
            "models": {
                "document_analyzer": "gpt-4o-mini",
                "use_case_extractor": "gpt-4o-mini",
                "metadata_enricher": "gpt-4o-mini",
                "embedding_model": "text-embedding-3-small",
            },
            "processing": {
                "chunk_size": 2000,
                "chunk_overlap": 200,
                "max_tokens": 4000,
                "temperature": 0.1,
            },
            "extraction": {
                "max_use_cases_per_section": 50,
                "confidence_threshold": 0.8,
                "validation_enabled": True,
            },
            "embeddings": {
                "dimension": 1536,
                "batch_size": 100,
                "similarity_threshold": 0.75,
            },
        }

    def _setup_llm_agents(self):
        """Setup LLM agents for document processing."""
        models_config = self.config["models"]
        processing_config = self.config["processing"]

        # Document structure analyzer
        self.document_analyzer = LLMAgentNode(
            name="document_analyzer",
            model=models_config["document_analyzer"],
            system_prompt=self._get_document_analysis_prompt(),
            max_tokens=processing_config["max_tokens"],
            temperature=processing_config["temperature"],
        )

        # Use case extractor
        self.use_case_extractor = LLMAgentNode(
            name="use_case_extractor",
            model=models_config["use_case_extractor"],
            system_prompt=self._get_use_case_extraction_prompt(),
            max_tokens=processing_config["max_tokens"],
            temperature=processing_config["temperature"],
        )

        # Metadata enricher
        self.metadata_enricher = LLMAgentNode(
            name="metadata_enricher",
            model=models_config["metadata_enricher"],
            system_prompt=self._get_metadata_enrichment_prompt(),
            max_tokens=processing_config["max_tokens"],
            temperature=processing_config["temperature"],
        )

        logger.info("LLM agents initialized")

    def _setup_data_processors(self):
        """Setup data processing nodes."""
        processing_config = self.config["processing"]

        # Document chunker for hierarchical processing
        self.document_chunker = HierarchicalChunkerNode(
            name="document_chunker",
            chunk_size=processing_config["chunk_size"],
            chunk_overlap=processing_config["chunk_overlap"],
            levels=3,  # Document, section, paragraph levels
        )

        # Text splitter for embedding preparation using DataTransformer
        self.text_splitter = DataTransformer(
            name="text_splitter",
            transformations=[
                f"chunk_size = {processing_config['chunk_size']}",
                f"chunk_overlap = {processing_config['chunk_overlap']}",
                "chunks = split_text_into_chunks(text, chunk_size, chunk_overlap)",
                "result = chunks",
            ],
        )

        logger.info("Data processors initialized")

    def _setup_embedding_system(self):
        """Setup embedding generation system."""
        models_config = self.config["models"]

        # Embedding generator
        self.embedding_generator = EmbeddingGeneratorNode(
            name="embedding_generator",
            model=models_config["embedding_model"],
            batch_size=self.config["embeddings"]["batch_size"],
        )

        logger.info("Embedding system initialized")

    def _get_document_analysis_prompt(self) -> str:
        """System prompt for document structure analysis."""
        return """You are a specialized document analysis expert for ISO/IEC technical reports containing AI use cases.

Analyze PDF content and identify:
1. Document structure and sections
2. Use case locations and organization
3. Page ranges for each section
4. Content type classification

Focus on Section 7 and subsections containing detailed AI use case descriptions.

Output structured JSON with:
- sections: List of identified sections with titles, page ranges, content types
- metadata: Document type, version, estimated use case count
- confidence: Analysis confidence score (0-1)

Be precise and conservative in your analysis."""

    def _get_use_case_extraction_prompt(self) -> str:
        """System prompt for use case extraction."""
        return """You are an expert at extracting structured AI use case information from technical documents.

Extract detailed use case information including:
- Use case ID and name
- Application domain and description
- AI methods and tasks
- Implementation details and challenges
- Status and deployment information

Output structured JSON for each use case with all available fields.
Maintain high accuracy and completeness."""

    def _get_metadata_enrichment_prompt(self) -> str:
        """System prompt for metadata enrichment."""
        return """You are a metadata enrichment specialist for AI use cases.

Enhance use case data with:
- Cross-references to related use cases
- Technology categorization
- Implementation complexity assessment
- Domain-specific insights

Output enhanced JSON with additional metadata fields."""

    def process_pdf_document(
        self, pdf_path: str, analysis_mode: str = "detailed"
    ) -> Dict[str, Any]:
        """
        Process PDF document using pure Kailash workflow.

        Args:
            pdf_path: Path to PDF file
            analysis_mode: "quick" or "detailed" analysis

        Returns:
            Document processing results
        """
        try:
            logger.info(f"Processing PDF: {pdf_path} (mode: {analysis_mode})")

            # Create and execute document processing workflow
            workflow = self._create_pdf_processing_workflow(analysis_mode)
            parameters = {
                "pdf_loader": {"file_path": pdf_path},
                "analysis_mode": analysis_mode,
            }

            results, run_id = self.runtime.execute(workflow, parameters=parameters)

            # Store results
            doc_key = Path(pdf_path).stem
            self.processed_documents[doc_key] = {
                "results": results,
                "run_id": run_id,
                "processed_at": datetime.now().isoformat(),
                "mode": analysis_mode,
            }

            logger.info(f"PDF processing completed: {doc_key}")
            return results

        except Exception as e:
            logger.error(f"PDF processing failed: {str(e)}")
            raise

    def _create_pdf_processing_workflow(self, analysis_mode: str) -> Workflow:
        """Create workflow for PDF processing."""
        workflow = Workflow(
            "pdf_processing", f"Process PDF document ({analysis_mode} mode)"
        )

        # Load PDF document using DirectoryReaderNode or custom PythonCodeNode
        # Since we need PDF loading, use PythonCodeNode with appropriate logic
        from kailash.nodes.code import PythonCodeNode

        pdf_loader = PythonCodeNode.from_function(
            name="pdf_loader",
            function="""
def load_pdf(file_path: str) -> dict:
    import PyPDF2
    import os

    if not os.path.exists(file_path):
        return {"error": f"File not found: {file_path}"}

    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text += page.extract_text()

        return {"content": text, "page_count": len(pdf_reader.pages)}
    except Exception as e:
        return {"error": f"Failed to read PDF: {str(e)}"}
""",
            inputs=["file_path"],
            outputs=["content", "page_count", "error"],
        )
        workflow.add_node("pdf_loader", pdf_loader)

        # Chunk document hierarchically
        workflow.add_node("chunker", self.document_chunker)
        workflow.connect("pdf_loader", "chunker", mapping={"content": "text"})

        # Analyze document structure
        workflow.add_node("analyzer", self.document_analyzer)
        workflow.connect("chunker", "analyzer", mapping={"chunks": "input"})

        if analysis_mode == "detailed":
            # Extract use cases (detailed mode only)
            workflow.add_node("extractor", self.use_case_extractor)
            workflow.connect("analyzer", "extractor", mapping={"response": "context"})
            workflow.connect("chunker", "extractor", mapping={"chunks": "content"})

            # Enrich metadata
            workflow.add_node("enricher", self.metadata_enricher)
            workflow.connect("extractor", "enricher", mapping={"response": "use_cases"})

        return workflow

    def extract_use_cases_from_section(
        self, document_key: str, section_id: str
    ) -> List[Dict[str, Any]]:
        """
        Extract use cases from a specific document section.

        Args:
            document_key: Processed document identifier
            section_id: Section identifier to extract from

        Returns:
            List of extracted use cases
        """
        try:
            if document_key not in self.processed_documents:
                raise ValueError(f"Document not processed: {document_key}")

            # Create section-specific extraction workflow
            workflow = self._create_section_extraction_workflow()

            # Get document data
            doc_data = self.processed_documents[document_key]["results"]

            parameters = {
                "section_id": section_id,
                "document_data": doc_data,
                "max_use_cases": self.config["extraction"]["max_use_cases_per_section"],
            }

            results, _ = self.runtime.execute(workflow, parameters=parameters)

            return results.get("extracted_use_cases", [])

        except Exception as e:
            logger.error(f"Section extraction failed: {str(e)}")
            raise

    def _create_section_extraction_workflow(self) -> Workflow:
        """Create workflow for section-specific use case extraction."""
        workflow = Workflow(
            "section_extraction", "Extract use cases from document section"
        )

        # Section data processor
        section_processor = DataTransformer(
            name="section_processor",
            transformations=[
                "result = extract_section_content(document_data, section_id)",
                "result = prepare_extraction_context(result)",
            ],
        )
        workflow.add_node("section_processor", section_processor)

        # Use case extractor
        workflow.add_node("extractor", self.use_case_extractor)
        workflow.connect(
            "section_processor", "extractor", mapping={"result": "context"}
        )

        # Result validator
        validator = DataTransformer(
            name="validator",
            transformations=[
                "result = validate_extracted_use_cases(extracted_data)",
                "result = filter_by_confidence(result, threshold=0.8)",
            ],
        )
        workflow.add_node("validator", validator)
        workflow.connect(
            "extractor", "validator", mapping={"response": "extracted_data"}
        )

        return workflow

    def generate_knowledge_base(self, source_documents: List[str]) -> Dict[str, Any]:
        """
        Generate markdown knowledge base from processed documents.

        Args:
            source_documents: List of document keys to include

        Returns:
            Knowledge base generation results
        """
        try:
            logger.info(
                f"Generating knowledge base from {len(source_documents)} documents"
            )

            # Create knowledge base generation workflow
            workflow = self._create_knowledge_base_workflow()

            parameters = {
                "source_documents": source_documents,
                "processed_data": self.processed_documents,
                "output_format": "markdown",
            }

            results, run_id = self.runtime.execute(workflow, parameters=parameters)

            # Store knowledge base
            self.knowledge_base = {
                "content": results,
                "sources": source_documents,
                "generated_at": datetime.now().isoformat(),
                "run_id": run_id,
            }

            logger.info("Knowledge base generation completed")
            return results

        except Exception as e:
            logger.error(f"Knowledge base generation failed: {str(e)}")
            raise

    def _create_knowledge_base_workflow(self) -> Workflow:
        """Create workflow for knowledge base generation."""
        workflow = Workflow(
            "knowledge_base_generation", "Generate markdown knowledge base"
        )

        # Data aggregator
        aggregator = DataTransformer(
            name="aggregator",
            transformations=[
                "result = aggregate_use_cases_from_documents(source_documents, processed_data)",
                "result = organize_by_domain_and_method(result)",
            ],
        )
        workflow.add_node("aggregator", aggregator)

        # Markdown generator
        markdown_generator = DataTransformer(
            name="markdown_generator",
            transformations=[
                "result = generate_markdown_files(aggregated_data)",
                "result = create_cross_references(result)",
                "result = generate_index_files(result)",
            ],
        )
        workflow.add_node("markdown_generator", markdown_generator)
        workflow.connect(
            "aggregator", "markdown_generator", mapping={"result": "aggregated_data"}
        )

        return workflow

    def generate_embeddings(self, content_list: List[str]) -> Dict[str, Any]:
        """
        Generate embeddings for content using Kailash embedding node.

        Args:
            content_list: List of text content to embed

        Returns:
            Embedding generation results
        """
        try:
            logger.info(f"Generating embeddings for {len(content_list)} items")

            # Create embedding workflow
            workflow = Workflow(
                "embedding_generation", "Generate embeddings for content"
            )

            # Text preprocessor
            preprocessor = DataTransformer(
                name="preprocessor",
                transformations=[
                    "result = clean_and_normalize_text(content_list)",
                    "result = split_long_content(result, max_length=8000)",
                ],
            )
            workflow.add_node("preprocessor", preprocessor)

            # Embedding generator
            workflow.add_node("embedder", self.embedding_generator)
            workflow.connect("preprocessor", "embedder", mapping={"result": "texts"})

            # Execute workflow
            parameters = {"content_list": content_list}
            results, _ = self.runtime.execute(workflow, parameters=parameters)

            # Cache embeddings
            embedding_key = f"batch_{datetime.now().timestamp()}"
            self.embeddings_cache[embedding_key] = {
                "embeddings": results["embedder"]["embeddings"],
                "content": content_list,
                "generated_at": datetime.now().isoformat(),
            }

            logger.info("Embedding generation completed")
            return results

        except Exception as e:
            logger.error(f"Embedding generation failed: {str(e)}")
            raise

    def find_similar_content(
        self, query_text: str, top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Find similar content using embedding similarity.

        Args:
            query_text: Query text to find similarities for
            top_k: Number of top results to return

        Returns:
            List of similar content with similarity scores
        """
        try:
            # Generate query embedding
            query_embedding = self.generate_embeddings([query_text])

            # Create similarity search workflow
            workflow = Workflow("similarity_search", "Find similar content")

            # Similarity calculator
            similarity_calculator = DataTransformer(
                name="similarity_calculator",
                transformations=[
                    "result = calculate_cosine_similarity(query_embedding, cached_embeddings)",
                    "result = rank_by_similarity(result)",
                    f"result = get_top_k_results(result, k={top_k})",
                ],
            )
            workflow.add_node("similarity_calculator", similarity_calculator)

            parameters = {
                "query_embedding": query_embedding,
                "cached_embeddings": self.embeddings_cache,
                "threshold": self.config["embeddings"]["similarity_threshold"],
            }

            results, _ = self.runtime.execute(workflow, parameters=parameters)

            return results.get("similarity_results", [])

        except Exception as e:
            logger.error(f"Similarity search failed: {str(e)}")
            raise

    # Module management methods
    def is_ready(self) -> bool:
        """Check if the module is ready for operation."""
        return self._ready and all(
            [
                hasattr(self, "document_analyzer"),
                hasattr(self, "use_case_extractor"),
                hasattr(self, "embedding_generator"),
            ]
        )

    def get_status(self) -> Dict[str, Any]:
        """Get current module status."""
        return {
            "healthy": self.is_ready(),
            "status": "Ready" if self.is_ready() else "Not Ready",
            "processed_documents": len(self.processed_documents),
            "knowledge_base_items": len(self.knowledge_base),
            "cached_embeddings": len(self.embeddings_cache),
            "last_activity": datetime.now().isoformat(),
        }

    def get_info(self) -> Dict[str, Any]:
        """Get module information."""
        return {
            "name": "RAG Module",
            "version": "1.0.0",
            "description": "Document processing and knowledge extraction",
            "capabilities": [
                "PDF document analysis",
                "Use case extraction",
                "Knowledge base generation",
                "Embedding generation",
                "Similarity search",
            ],
            "models": self.config["models"],
            "config": self.config,
        }
