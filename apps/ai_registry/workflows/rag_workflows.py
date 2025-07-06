"""
RAG Workflows - Pure Kailash Implementation

Workflow orchestrators for RAG operations including PDF processing,
knowledge extraction, and embedding generation.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from kailash import Workflow
from kailash.nodes.ai import EmbeddingGeneratorNode, LLMAgentNode
from kailash.nodes.base import Node
from kailash.nodes.data import DocumentSourceNode, JSONReaderNode

# Note: Using our custom chunking nodes instead of kailash.nodes.text
# from kailash.nodes.text import HierarchicalChunkerNode, TextSplitterNode
from kailash.nodes.transform import DataTransformer
from kailash.nodes.transform.chunkers import HierarchicalChunkerNode
from kailash.runtime import LocalRuntime

logger = logging.getLogger(__name__)


class RAGWorkflows:
    """
    RAG workflow orchestrator for the Enhanced MCP Server.

    Provides MCP tools that execute complete RAG workflows using pure Kailash components.
    All tools are automatically cached and formatted by the Enhanced MCP Server.
    """

    def __init__(self, server, rag_module, runtime: LocalRuntime):
        """
        Initialize RAG workflows.

        Args:
            server: Enhanced MCP Server instance
            rag_module: RAG module with core components
            runtime: Kailash workflow runtime
        """
        self.server = server
        self.rag_module = rag_module
        self.runtime = runtime

        # Workflow state
        self.active_workflows = {}
        self.completed_workflows = {}

        # Register MCP tools
        self._register_tools()

        logger.info("RAG Workflows registered with Enhanced MCP Server")

    def _register_tools(self):
        """Register RAG tools with the MCP server."""

        @self.server.tool(
            cache_key="pdf_analysis",
            cache_ttl=3600,  # Cache for 1 hour
            format_response="markdown",
        )
        def analyze_pdf_document(
            pdf_path: str, analysis_mode: str = "detailed"
        ) -> dict:
            """
            Analyze PDF document structure and identify use case sections.

            Args:
                pdf_path: Path to PDF file to analyze
                analysis_mode: "quick" or "detailed" analysis

            Returns:
                Document analysis results with sections and metadata
            """
            try:
                return self._execute_pdf_analysis_workflow(pdf_path, analysis_mode)
            except Exception as e:
                logger.error(f"PDF analysis failed: {str(e)}")
                return {"success": False, "error": str(e)}

        @self.server.tool(
            cache_key="extract_use_cases",
            cache_ttl=1800,  # Cache for 30 minutes
            format_response="json",
        )
        def extract_use_cases_from_pdf(
            pdf_path: str, section_filter: str = None
        ) -> dict:
            """
            Extract structured use cases from PDF document.

            Args:
                pdf_path: Path to PDF file
                section_filter: Optional section filter (e.g., "7.1", "healthcare")

            Returns:
                Extracted use cases with detailed information
            """
            try:
                return self._execute_use_case_extraction_workflow(
                    pdf_path, section_filter
                )
            except Exception as e:
                logger.error(f"Use case extraction failed: {str(e)}")
                return {"success": False, "error": str(e)}

        @self.server.tool(
            cache_key="generate_knowledge_base",
            cache_ttl=7200,  # Cache for 2 hours
            format_response="markdown",
        )
        def generate_markdown_knowledge_base(
            source_pdfs: list, output_format: str = "hierarchical"
        ) -> dict:
            """
            Generate markdown knowledge base from PDF sources.

            Args:
                source_pdfs: List of PDF file paths to process
                output_format: "hierarchical" or "flat" organization

            Returns:
                Generated knowledge base with markdown files and index
            """
            try:
                return self._execute_knowledge_base_generation_workflow(
                    source_pdfs, output_format
                )
            except Exception as e:
                logger.error(f"Knowledge base generation failed: {str(e)}")
                return {"success": False, "error": str(e)}

        @self.server.tool(
            cache_key="generate_embeddings",
            cache_ttl=3600,  # Cache for 1 hour
            format_response="json",
        )
        def generate_embeddings_for_content(
            content_list: list, batch_size: int = 100
        ) -> dict:
            """
            Generate embeddings for content list using optimal model.

            Args:
                content_list: List of text content to embed
                batch_size: Number of items to process in each batch

            Returns:
                Embedding generation results with vectors and metadata
            """
            try:
                return self._execute_embedding_generation_workflow(
                    content_list, batch_size
                )
            except Exception as e:
                logger.error(f"Embedding generation failed: {str(e)}")
                return {"success": False, "error": str(e)}

        @self.server.tool(
            cache_key="process_section_7_pdfs",
            cache_ttl=7200,  # Cache for 2 hours
            format_response="markdown",
        )
        def process_section_7_pdfs(pdf_2021_path: str, pdf_2024_path: str) -> dict:
            """
            Complete processing of both Section 7 PDFs for AI Registry.

            Args:
                pdf_2021_path: Path to 2021 Section 7 PDF
                pdf_2024_path: Path to 2024 Section 7 PDF

            Returns:
                Complete processing results including extracted use cases,
                generated knowledge base, and embeddings
            """
            try:
                return self._execute_complete_section_7_workflow(
                    pdf_2021_path, pdf_2024_path
                )
            except Exception as e:
                logger.error(f"Section 7 processing failed: {str(e)}")
                return {"success": False, "error": str(e)}

    def _execute_pdf_analysis_workflow(
        self, pdf_path: str, analysis_mode: str
    ) -> Dict[str, Any]:
        """Execute PDF analysis workflow."""
        workflow_id = f"pdf_analysis_{datetime.now().timestamp()}"

        try:
            # Create PDF analysis workflow
            workflow = Workflow(
                "pdf_analysis", f"Analyze PDF document: {Path(pdf_path).name}"
            )

            # Load PDF document
            pdf_loader = DocumentSourceNode(name="pdf_loader", file_path=pdf_path)
            workflow.add_node("pdf_loader", pdf_loader)

            # Chunk document hierarchically
            chunker = HierarchicalChunkerNode(
                name="chunker", chunk_size=2000, chunk_overlap=200, levels=3
            )
            workflow.add_node("chunker", chunker)
            workflow.connect("pdf_loader", "chunker", mapping={"content": "text"})

            # Analyze document structure
            analyzer = LLMAgentNode(
                name="analyzer",
                model="gpt-4o-mini",
                system_prompt=self._get_structure_analysis_prompt(),
                max_tokens=3000,
                temperature=0.1,
            )
            workflow.add_node("analyzer", analyzer)
            workflow.connect("chunker", "analyzer", mapping={"chunks": "input"})

            if analysis_mode == "detailed":
                # Detailed section analysis
                section_analyzer = LLMAgentNode(
                    name="section_analyzer",
                    model="gpt-4o-mini",
                    system_prompt=self._get_section_analysis_prompt(),
                    max_tokens=4000,
                    temperature=0.1,
                )
                workflow.add_node("section_analyzer", section_analyzer)
                workflow.connect(
                    "analyzer", "section_analyzer", mapping={"response": "structure"}
                )
                workflow.connect(
                    "chunker", "section_analyzer", mapping={"chunks": "content"}
                )

            # Execute workflow
            self.active_workflows[workflow_id] = workflow
            results, run_id = self.runtime.execute(workflow)

            # Store results
            self.completed_workflows[workflow_id] = {
                "results": results,
                "run_id": run_id,
                "completed_at": datetime.now().isoformat(),
            }

            # Format results
            analysis_result = self._format_analysis_results(
                results, pdf_path, analysis_mode
            )

            logger.info(f"PDF analysis completed: {workflow_id}")
            return analysis_result

        except Exception as e:
            logger.error(f"PDF analysis workflow failed: {str(e)}")
            raise
        finally:
            if workflow_id in self.active_workflows:
                del self.active_workflows[workflow_id]

    def _execute_use_case_extraction_workflow(
        self, pdf_path: str, section_filter: Optional[str]
    ) -> Dict[str, Any]:
        """Execute use case extraction workflow."""
        workflow_id = f"use_case_extraction_{datetime.now().timestamp()}"

        try:
            # Create use case extraction workflow
            workflow = Workflow(
                "use_case_extraction", f"Extract use cases from: {Path(pdf_path).name}"
            )

            # Load and analyze PDF (reuse analysis if cached)
            pdf_loader = DocumentSourceNode(name="pdf_loader", file_path=pdf_path)
            workflow.add_node("pdf_loader", pdf_loader)

            chunker = HierarchicalChunkerNode(
                name="chunker", chunk_size=3000, chunk_overlap=300, levels=2
            )
            workflow.add_node("chunker", chunker)
            workflow.connect("pdf_loader", "chunker", mapping={"content": "text"})

            # Use case extractor
            extractor = LLMAgentNode(
                name="extractor",
                model="gpt-4o-mini",
                system_prompt=self._get_use_case_extraction_prompt(),
                max_tokens=4000,
                temperature=0.1,
            )
            workflow.add_node("extractor", extractor)
            workflow.connect("chunker", "extractor", mapping={"chunks": "content"})

            # Validator and enricher
            validator = LLMAgentNode(
                name="validator",
                model="gpt-4o-mini",
                system_prompt=self._get_validation_prompt(),
                max_tokens=2000,
                temperature=0.0,
            )
            workflow.add_node("validator", validator)
            workflow.connect(
                "extractor", "validator", mapping={"response": "extracted_data"}
            )

            # Execute workflow
            parameters = {}
            if section_filter:
                parameters["section_filter"] = section_filter

            self.active_workflows[workflow_id] = workflow
            results, run_id = self.runtime.execute(workflow, parameters=parameters)

            # Store results
            self.completed_workflows[workflow_id] = {
                "results": results,
                "run_id": run_id,
                "completed_at": datetime.now().isoformat(),
            }

            # Format results
            extraction_result = self._format_extraction_results(
                results, pdf_path, section_filter
            )

            logger.info(f"Use case extraction completed: {workflow_id}")
            return extraction_result

        except Exception as e:
            logger.error(f"Use case extraction workflow failed: {str(e)}")
            raise
        finally:
            if workflow_id in self.active_workflows:
                del self.active_workflows[workflow_id]

    def _execute_knowledge_base_generation_workflow(
        self, source_pdfs: List[str], output_format: str
    ) -> Dict[str, Any]:
        """Execute knowledge base generation workflow."""
        workflow_id = f"knowledge_base_{datetime.now().timestamp()}"

        try:
            # Create knowledge base generation workflow
            workflow = Workflow(
                "knowledge_base_generation",
                f"Generate knowledge base from {len(source_pdfs)} PDFs",
            )

            # Multi-document processor
            doc_processor = DataTransformer(
                name="doc_processor",
                transformations=[
                    "result = process_multiple_pdfs(source_pdfs)",
                    "result = extract_all_use_cases(result)",
                    "result = organize_by_domain(result)",
                ],
            )
            workflow.add_node("doc_processor", doc_processor)

            # Markdown generator
            markdown_generator = LLMAgentNode(
                name="markdown_generator",
                model="gpt-4o-mini",
                system_prompt=self._get_markdown_generation_prompt(),
                max_tokens=4000,
                temperature=0.1,
            )
            workflow.add_node("markdown_generator", markdown_generator)
            workflow.connect(
                "doc_processor", "markdown_generator", mapping={"result": "use_cases"}
            )

            # Cross-reference generator
            cross_ref_generator = DataTransformer(
                name="cross_ref_generator",
                transformations=[
                    "result = generate_cross_references(markdown_files)",
                    "result = create_domain_indexes(result)",
                    "result = create_master_index(result)",
                ],
            )
            workflow.add_node("cross_ref_generator", cross_ref_generator)
            workflow.connect(
                "markdown_generator",
                "cross_ref_generator",
                mapping={"response": "markdown_files"},
            )

            # Execute workflow
            parameters = {"source_pdfs": source_pdfs, "output_format": output_format}

            self.active_workflows[workflow_id] = workflow
            results, run_id = self.runtime.execute(workflow, parameters=parameters)

            # Store results
            self.completed_workflows[workflow_id] = {
                "results": results,
                "run_id": run_id,
                "completed_at": datetime.now().isoformat(),
            }

            # Format results
            kb_result = self._format_knowledge_base_results(
                results, source_pdfs, output_format
            )

            logger.info(f"Knowledge base generation completed: {workflow_id}")
            return kb_result

        except Exception as e:
            logger.error(f"Knowledge base generation workflow failed: {str(e)}")
            raise
        finally:
            if workflow_id in self.active_workflows:
                del self.active_workflows[workflow_id]

    def _execute_embedding_generation_workflow(
        self, content_list: List[str], batch_size: int
    ) -> Dict[str, Any]:
        """Execute embedding generation workflow."""
        workflow_id = f"embedding_generation_{datetime.now().timestamp()}"

        try:
            # Create embedding generation workflow
            workflow = Workflow(
                "embedding_generation",
                f"Generate embeddings for {len(content_list)} items",
            )

            # Text preprocessor
            preprocessor = DataTransformer(
                name="preprocessor",
                transformations=[
                    "result = clean_and_normalize_text(content_list)",
                    "result = chunk_long_content(result, max_length=8000)",
                    f"result = create_batches(result, batch_size={batch_size})",
                ],
            )
            workflow.add_node("preprocessor", preprocessor)

            # Embedding generator
            embedder = EmbeddingGeneratorNode(
                name="embedder", model="text-embedding-3-small", batch_size=batch_size
            )
            workflow.add_node("embedder", embedder)
            workflow.connect("preprocessor", "embedder", mapping={"result": "texts"})

            # Embedding processor
            processor = DataTransformer(
                name="processor",
                transformations=[
                    "result = organize_embeddings(embeddings, original_content)",
                    "result = calculate_metadata(result)",
                    "result = store_embeddings(result)",
                ],
            )
            workflow.add_node("processor", processor)
            workflow.connect(
                "embedder", "processor", mapping={"embeddings": "embeddings"}
            )
            workflow.connect(
                "preprocessor", "processor", mapping={"result": "original_content"}
            )

            # Execute workflow
            parameters = {"content_list": content_list}

            self.active_workflows[workflow_id] = workflow
            results, run_id = self.runtime.execute(workflow, parameters=parameters)

            # Store results
            self.completed_workflows[workflow_id] = {
                "results": results,
                "run_id": run_id,
                "completed_at": datetime.now().isoformat(),
            }

            # Format results
            embedding_result = self._format_embedding_results(
                results, content_list, batch_size
            )

            logger.info(f"Embedding generation completed: {workflow_id}")
            return embedding_result

        except Exception as e:
            logger.error(f"Embedding generation workflow failed: {str(e)}")
            raise
        finally:
            if workflow_id in self.active_workflows:
                del self.active_workflows[workflow_id]

    def _execute_complete_section_7_workflow(
        self, pdf_2021_path: str, pdf_2024_path: str
    ) -> Dict[str, Any]:
        """Execute complete Section 7 processing workflow."""
        workflow_id = f"section_7_complete_{datetime.now().timestamp()}"

        try:
            logger.info("Starting complete Section 7 processing workflow")

            # Create comprehensive workflow
            workflow = Workflow(
                "section_7_complete", "Complete Section 7 PDF Processing"
            )

            # Process 2021 PDF
            pdf_2021_loader = DocumentSourceNode(
                name="pdf_2021_loader", file_path=pdf_2021_path
            )
            workflow.add_node("pdf_2021_loader", pdf_2021_loader)

            chunker_2021 = HierarchicalChunkerNode(
                name="chunker_2021", chunk_size=2500, chunk_overlap=250, levels=3
            )
            workflow.add_node("chunker_2021", chunker_2021)
            workflow.connect(
                "pdf_2021_loader", "chunker_2021", mapping={"content": "text"}
            )

            extractor_2021 = LLMAgentNode(
                name="extractor_2021",
                model="gpt-4o-mini",
                system_prompt=self._get_comprehensive_extraction_prompt("2021"),
                max_tokens=4000,
                temperature=0.1,
            )
            workflow.add_node("extractor_2021", extractor_2021)
            workflow.connect(
                "chunker_2021", "extractor_2021", mapping={"chunks": "content"}
            )

            # Process 2024 PDF
            pdf_2024_loader = DocumentSourceNode(
                name="pdf_2024_loader", file_path=pdf_2024_path
            )
            workflow.add_node("pdf_2024_loader", pdf_2024_loader)

            chunker_2024 = HierarchicalChunkerNode(
                name="chunker_2024", chunk_size=2500, chunk_overlap=250, levels=3
            )
            workflow.add_node("chunker_2024", chunker_2024)
            workflow.connect(
                "pdf_2024_loader", "chunker_2024", mapping={"content": "text"}
            )

            extractor_2024 = LLMAgentNode(
                name="extractor_2024",
                model="gpt-4o-mini",
                system_prompt=self._get_comprehensive_extraction_prompt("2024"),
                max_tokens=4000,
                temperature=0.1,
            )
            workflow.add_node("extractor_2024", extractor_2024)
            workflow.connect(
                "chunker_2024", "extractor_2024", mapping={"chunks": "content"}
            )

            # Merge and process results
            merger = LLMAgentNode(
                name="merger",
                model="gpt-4o",  # Use more powerful model for complex merging
                system_prompt=self._get_merging_prompt(),
                max_tokens=4000,
                temperature=0.1,
            )
            workflow.add_node("merger", merger)
            workflow.connect(
                "extractor_2021", "merger", mapping={"response": "data_2021"}
            )
            workflow.connect(
                "extractor_2024", "merger", mapping={"response": "data_2024"}
            )

            # Generate final knowledge base
            kb_generator = LLMAgentNode(
                name="kb_generator",
                model="gpt-4o-mini",
                system_prompt=self._get_knowledge_base_prompt(),
                max_tokens=4000,
                temperature=0.1,
            )
            workflow.add_node("kb_generator", kb_generator)
            workflow.connect(
                "merger", "kb_generator", mapping={"response": "merged_data"}
            )

            # Generate embeddings for all content
            embedder = EmbeddingGeneratorNode(
                name="embedder", model="text-embedding-3-small", batch_size=50
            )
            workflow.add_node("embedder", embedder)
            workflow.connect(
                "kb_generator",
                "embedder",
                mapping={"response": "content_for_embeddings"},
            )

            # Execute workflow
            parameters = {
                "pdf_2021_path": pdf_2021_path,
                "pdf_2024_path": pdf_2024_path,
            }

            self.active_workflows[workflow_id] = workflow
            results, run_id = self.runtime.execute(workflow, parameters=parameters)

            # Store results
            self.completed_workflows[workflow_id] = {
                "results": results,
                "run_id": run_id,
                "completed_at": datetime.now().isoformat(),
            }

            # Format comprehensive results
            complete_result = self._format_complete_results(
                results, pdf_2021_path, pdf_2024_path
            )

            logger.info(f"Complete Section 7 processing completed: {workflow_id}")
            return complete_result

        except Exception as e:
            logger.error(f"Complete Section 7 workflow failed: {str(e)}")
            raise
        finally:
            if workflow_id in self.active_workflows:
                del self.active_workflows[workflow_id]

    # Prompt templates
    def _get_structure_analysis_prompt(self) -> str:
        """System prompt for document structure analysis."""
        return """You are a document structure analyst for ISO/IEC technical reports containing AI use cases.

Analyze the document and identify:
1. Main sections and subsections
2. Page ranges for each section
3. Content types (use cases, technical info, appendices)
4. Estimated number of use cases per section

Focus on Section 7 and subsections as they contain the primary use case content.

Output structured JSON with sections, metadata, and confidence scores."""

    def _get_section_analysis_prompt(self) -> str:
        """System prompt for detailed section analysis."""
        return """You are a section content analyst for AI use case documents.

For each section, analyze:
1. Detailed content breakdown
2. Use case identification and numbering
3. Domain categorization
4. Implementation status assessment

Provide detailed analysis with high accuracy."""

    def _get_use_case_extraction_prompt(self) -> str:
        """System prompt for use case extraction."""
        return """You are an expert at extracting structured AI use case information.

Extract detailed information for each use case:
- Use case ID, name, and description
- Application domain and narrative
- AI methods and tasks
- Implementation details and challenges
- Status and deployment information

Output structured JSON with complete use case data."""

    def _get_validation_prompt(self) -> str:
        """System prompt for data validation."""
        return """You are a data validation specialist for AI use cases.

Validate extracted use case data for:
1. Completeness and accuracy
2. Schema compliance
3. Data consistency
4. Missing or invalid fields

Output validated and corrected data with confidence scores."""

    def _get_markdown_generation_prompt(self) -> str:
        """System prompt for markdown generation."""
        return """You are a technical documentation specialist.

Generate clean, structured markdown files for AI use cases:
1. Consistent formatting and structure
2. Cross-references and links
3. Domain organization
4. Search-friendly content

Create professional documentation suitable for developers and researchers."""

    def _get_comprehensive_extraction_prompt(self, year: str) -> str:
        """System prompt for comprehensive extraction."""
        return f"""You are processing the {year} ISO/IEC TR 24030 Section 7 document for comprehensive AI use case extraction.

Extract ALL use cases with complete details:
- Full descriptions and narratives
- Technical implementation details
- Challenges and solutions
- Domain-specific information
- Cross-references and relationships

Focus on accuracy and completeness for the {year} dataset."""

    def _get_merging_prompt(self) -> str:
        """System prompt for merging 2021 and 2024 data."""
        return """You are a data integration specialist merging AI use case datasets from 2021 and 2024.

Merge the datasets by:
1. Identifying overlapping use cases
2. Preserving unique cases from each year
3. Tracking evolution and updates
4. Maintaining data integrity

Create a comprehensive merged dataset with proper attribution."""

    def _get_knowledge_base_prompt(self) -> str:
        """System prompt for knowledge base generation."""
        return """You are creating a comprehensive AI use case knowledge base.

Generate:
1. Individual markdown files for each use case
2. Domain-specific organization
3. Cross-reference system
4. Master index and navigation
5. Search-optimized content

Create a professional knowledge base suitable for research and development."""

    # Result formatting methods
    def _format_analysis_results(
        self, results: Dict, pdf_path: str, analysis_mode: str
    ) -> Dict[str, Any]:
        """Format PDF analysis results."""
        return {
            "success": True,
            "analysis_mode": analysis_mode,
            "document": {
                "path": pdf_path,
                "name": Path(pdf_path).name,
                "analyzed_at": datetime.now().isoformat(),
            },
            "structure": results.get("analyzer", {}),
            "sections": (
                results.get("section_analyzer", {})
                if analysis_mode == "detailed"
                else {}
            ),
            "metadata": {"workflow_type": "pdf_analysis", "model_used": "gpt-4o-mini"},
        }

    def _format_extraction_results(
        self, results: Dict, pdf_path: str, section_filter: Optional[str]
    ) -> Dict[str, Any]:
        """Format use case extraction results."""
        return {
            "success": True,
            "document": {
                "path": pdf_path,
                "name": Path(pdf_path).name,
                "section_filter": section_filter,
            },
            "extracted_use_cases": results.get("validator", {}),
            "raw_extraction": results.get("extractor", {}),
            "metadata": {
                "workflow_type": "use_case_extraction",
                "extracted_at": datetime.now().isoformat(),
            },
        }

    def _format_knowledge_base_results(
        self, results: Dict, source_pdfs: List[str], output_format: str
    ) -> Dict[str, Any]:
        """Format knowledge base generation results."""
        return {
            "success": True,
            "knowledge_base": results.get("cross_ref_generator", {}),
            "markdown_files": results.get("markdown_generator", {}),
            "sources": source_pdfs,
            "output_format": output_format,
            "metadata": {
                "workflow_type": "knowledge_base_generation",
                "generated_at": datetime.now().isoformat(),
            },
        }

    def _format_embedding_results(
        self, results: Dict, content_list: List[str], batch_size: int
    ) -> Dict[str, Any]:
        """Format embedding generation results."""
        return {
            "success": True,
            "embeddings": results.get("processor", {}),
            "content_count": len(content_list),
            "batch_size": batch_size,
            "metadata": {
                "workflow_type": "embedding_generation",
                "model": "text-embedding-3-small",
                "generated_at": datetime.now().isoformat(),
            },
        }

    def _format_complete_results(
        self, results: Dict, pdf_2021_path: str, pdf_2024_path: str
    ) -> Dict[str, Any]:
        """Format complete Section 7 processing results."""
        return {
            "success": True,
            "complete_processing": {
                "pdf_2021_results": results.get("extractor_2021", {}),
                "pdf_2024_results": results.get("extractor_2024", {}),
                "merged_data": results.get("merger", {}),
                "knowledge_base": results.get("kb_generator", {}),
                "embeddings": results.get("embedder", {}),
            },
            "sources": {"2021": pdf_2021_path, "2024": pdf_2024_path},
            "summary": {
                "total_use_cases": "extracted_from_results",
                "domains_covered": "extracted_from_results",
                "knowledge_base_files": "extracted_from_results",
            },
            "metadata": {
                "workflow_type": "complete_section_7_processing",
                "processed_at": datetime.now().isoformat(),
                "models_used": ["gpt-4o-mini", "gpt-4o", "text-embedding-3-small"],
            },
        }

    def get_available_workflows(self) -> List[str]:
        """Get list of available workflow types."""
        return [
            "analyze_pdf_document",
            "extract_use_cases_from_pdf",
            "generate_markdown_knowledge_base",
            "generate_embeddings_for_content",
            "process_section_7_pdfs",
        ]

    def get_active_workflows(self) -> Dict[str, Any]:
        """Get currently active workflows."""
        return {
            workflow_id: {"started_at": "timestamp", "type": workflow.name}
            for workflow_id, workflow in self.active_workflows.items()
        }

    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get status of a specific workflow."""
        if workflow_id in self.active_workflows:
            return {
                "status": "active",
                "workflow": self.active_workflows[workflow_id].name,
            }
        elif workflow_id in self.completed_workflows:
            return {
                "status": "completed",
                "result": self.completed_workflows[workflow_id],
            }
        else:
            return {"status": "not_found"}
