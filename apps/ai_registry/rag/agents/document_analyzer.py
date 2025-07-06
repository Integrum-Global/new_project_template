"""
DocumentAnalyzerAgent - Intelligent PDF structure analysis and section identification.

This agent is the first step in the RAG pipeline, responsible for:
1. Analyzing PDF document structure
2. Identifying sections containing use cases
3. Extracting metadata about document organization
4. Preparing structured input for downstream agents
"""

import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from kailash import LocalRuntime, Workflow
from kailash.nodes.ai import LLMAgentNode
from kailash.nodes.base import Node
from kailash.nodes.data import DocumentSourceNode
from kailash.nodes.text import HierarchicalChunkerNode, TextSplitterNode

from ..config.model_config import ModelConfig, RAGConfig

logger = logging.getLogger(__name__)


@dataclass
class DocumentSection:
    """Represents a section identified in the PDF."""

    section_number: str
    title: str
    page_range: Tuple[int, int]
    content_type: str  # "use_case", "overview", "technical", "appendix"
    use_case_count: int
    confidence: float
    summary: str


@dataclass
class DocumentAnalysis:
    """Complete analysis result for a PDF document."""

    document_path: str
    document_version: str  # "2021" or "2024"
    total_pages: int
    identified_sections: List[DocumentSection]
    metadata: Dict[str, Any]
    analysis_timestamp: str
    confidence_score: float


class DocumentAnalyzerAgent(Node):
    """
    Intelligent agent for analyzing PDF document structure and content.

    Uses GPT-4o Mini for optimal cost/performance in document analysis tasks.
    """

    def __init__(self, name: str = "document_analyzer", **kwargs):
        super().__init__(name=name, **kwargs)
        self.model_config = ModelConfig()
        self.rag_config = RAGConfig()
        self._setup_models()

    def _setup_models(self):
        """Initialize the LLM agents for analysis."""
        # Structure analyzer - identifies document sections
        self.structure_analyzer = LLMAgentNode(
            name="structure_analyzer",
            model=self.model_config.PDF_ANALYZER_MODEL,
            system_prompt=self._get_structure_analysis_prompt(),
            api_key=self.model_config.OPENAI_API_KEY,
            max_tokens=2000,
            temperature=0.1,  # Low temperature for consistent analysis
        )

        # Content classifier - determines section types
        self.content_classifier = LLMAgentNode(
            name="content_classifier",
            model=self.model_config.PDF_ANALYZER_MODEL,
            system_prompt=self._get_content_classification_prompt(),
            api_key=self.model_config.OPENAI_API_KEY,
            max_tokens=1000,
            temperature=0.0,  # Deterministic classification
        )

    def _get_structure_analysis_prompt(self) -> str:
        """System prompt for document structure analysis."""
        return """You are a specialized document analysis expert focusing on ISO/IEC technical reports containing AI use cases.

Your task is to analyze PDF content and identify the document structure, specifically:

1. **Section Identification**: Find all numbered sections (e.g., "7.1", "7.2", etc.)
2. **Use Case Sections**: Identify sections that contain detailed AI use case descriptions
3. **Page Mapping**: Determine the page range for each section
4. **Content Assessment**: Estimate how many use cases are in each section

**Expected Document Structure** (ISO/IEC TR 24030):
- Section 7: "AI use case descriptions" (main content)
- Subsections 7.x.x: Individual use case descriptions
- Annexes: Additional use cases and summaries

**Output Format** (JSON):
```json
{
    "document_version": "2021|2024",
    "total_pages": 150,
    "sections": [
        {
            "section_number": "7.1",
            "title": "Healthcare Use Cases",
            "page_range": [45, 65],
            "estimated_use_cases": 8,
            "content_preview": "First 200 chars of section content..."
        }
    ],
    "metadata": {
        "document_type": "ISO/IEC TR 24030",
        "main_use_case_section": "7",
        "total_estimated_use_cases": 187
    }
}
```

**Guidelines**:
- Focus on Section 7 and its subsections as primary use case content
- Look for patterns like "Use case X:", "Application:", "Description:"
- Identify appendices that might contain additional use cases
- Be precise with page ranges - they're critical for extraction
- Estimate use case count conservatively but accurately"""

    def _get_content_classification_prompt(self) -> str:
        """System prompt for content type classification."""
        return """You are a content classification specialist for technical documents containing AI use cases.

Given a section of text from an ISO/IEC technical report, classify the content type and extract key metadata.

**Classification Types**:
1. **use_case_detailed**: Detailed use case with full description, narrative, challenges, etc.
2. **use_case_summary**: Brief use case mention or summary
3. **overview**: Introductory or overview content
4. **technical**: Technical specifications, frameworks, definitions
5. **appendix**: Supporting material, lists, references
6. **table_of_contents**: Navigation/index content

**Analysis Focus**:
- Count actual use cases (not just mentions)
- Identify the application domain (Healthcare, Finance, Manufacturing, etc.)
- Assess content completeness and detail level
- Note any unique identifiers or numbering schemes

**Output Format** (JSON):
```json
{
    "content_type": "use_case_detailed",
    "use_case_count": 3,
    "application_domains": ["Healthcare", "Manufacturing"],
    "detail_level": "high|medium|low",
    "key_indicators": ["Use case 42:", "Application domain:", "Narrative:"],
    "confidence": 0.95,
    "summary": "Section contains 3 detailed healthcare use cases with full narratives and technical details"
}
```

**Quality Indicators**:
- Look for structured fields: Description, Narrative, AI Methods, Tasks, etc.
- Check for unique identifiers and references
- Assess information completeness and technical depth"""

    def run(self, **kwargs) -> Dict[str, Any]:
        """
        Analyze PDF document structure and identify use case sections.

        Args:
            pdf_path: Path to the PDF file to analyze
            analysis_mode: "quick" or "detailed" analysis

        Returns:
            DocumentAnalysis with identified sections and metadata
        """
        try:
            pdf_path = kwargs.get("pdf_path")
            analysis_mode = kwargs.get("analysis_mode", "detailed")

            if not pdf_path:
                raise ValueError("pdf_path is required")

            logger.info(f"Starting document analysis for: {pdf_path}")

            # Step 1: Load and chunk the PDF
            document_content = self._load_and_chunk_pdf(pdf_path)

            # Step 2: Analyze document structure
            structure_analysis = self._analyze_structure(document_content)

            # Step 3: Classify content sections
            section_classifications = self._classify_sections(
                document_content, structure_analysis
            )

            # Step 4: Generate final analysis
            analysis_result = self._generate_analysis_result(
                pdf_path, structure_analysis, section_classifications
            )

            logger.info(
                f"Document analysis completed. Found {len(analysis_result.identified_sections)} sections"
            )

            return {
                "success": True,
                "analysis": asdict(analysis_result),
                "sections_count": len(analysis_result.identified_sections),
                "confidence": analysis_result.confidence_score,
                "metadata": {
                    "processing_time": datetime.now().isoformat(),
                    "model_used": self.model_config.PDF_ANALYZER_MODEL,
                    "analysis_mode": analysis_mode,
                },
            }

        except Exception as e:
            logger.error(f"Document analysis failed: {str(e)}")
            return {"success": False, "error": str(e), "analysis": None}

    def _load_and_chunk_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """Load PDF and create hierarchical chunks for analysis."""
        try:
            # Create workflow for PDF processing
            workflow = Workflow("pdf_analysis", "Load and chunk PDF for analysis")

            # Load PDF document
            doc_loader = DocumentSourceNode(name="pdf_loader", file_path=pdf_path)
            workflow.add_node("pdf_loader", doc_loader)

            # Create hierarchical chunks for structure analysis
            chunker = HierarchicalChunkerNode(
                name="chunker",
                chunk_size=self.rag_config.PDF_CHUNK_SIZE,
                chunk_overlap=self.rag_config.PDF_CHUNK_OVERLAP,
                levels=2,  # Document and section level chunks
            )
            workflow.add_node("chunker", chunker)
            workflow.connect("pdf_loader", "chunker", mapping={"content": "text"})

            # Execute workflow
            runtime = LocalRuntime()
            results, _ = runtime.execute(workflow)

            return {
                "content": results["pdf_loader"]["content"],
                "chunks": results["chunker"]["chunks"],
                "metadata": results["pdf_loader"].get("metadata", {}),
            }

        except Exception as e:
            logger.error(f"PDF loading failed: {str(e)}")
            raise

    def _analyze_structure(self, document_content: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze document structure to identify sections."""
        try:
            # Prepare content for structure analysis
            content_text = document_content["content"][
                :20000
            ]  # First 20K chars for overview

            # Create analysis workflow
            workflow = Workflow("structure_analysis", "Analyze document structure")
            workflow.add_node("analyzer", self.structure_analyzer)

            # Execute structure analysis
            runtime = LocalRuntime()
            parameters = {
                "analyzer": {
                    "prompt": f"Analyze this document structure and identify sections:\n\n{content_text}",
                    "response_format": "json",
                }
            }

            results, _ = runtime.execute(workflow, parameters=parameters)
            analysis_result = results["analyzer"]["response"]

            # Parse JSON response
            if isinstance(analysis_result, str):
                analysis_result = json.loads(analysis_result)

            return analysis_result

        except Exception as e:
            logger.error(f"Structure analysis failed: {str(e)}")
            return {"sections": [], "metadata": {}}

    def _classify_sections(
        self, document_content: Dict[str, Any], structure_analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Classify each identified section for content type."""
        classifications = []
        chunks = document_content.get("chunks", [])

        for section in structure_analysis.get("sections", []):
            try:
                # Find relevant chunks for this section
                section_content = self._extract_section_content(chunks, section)

                if not section_content:
                    continue

                # Classify section content
                workflow = Workflow(
                    "content_classification", "Classify section content"
                )
                workflow.add_node("classifier", self.content_classifier)

                runtime = LocalRuntime()
                parameters = {
                    "classifier": {
                        "prompt": f"Classify this section content:\n\nSection: {section['title']}\nContent: {section_content[:3000]}",
                        "response_format": "json",
                    }
                }

                results, _ = runtime.execute(workflow, parameters=parameters)
                classification = results["classifier"]["response"]

                if isinstance(classification, str):
                    classification = json.loads(classification)

                # Combine section info with classification
                classification.update(
                    {
                        "section_number": section["section_number"],
                        "title": section["title"],
                        "page_range": section["page_range"],
                    }
                )

                classifications.append(classification)

            except Exception as e:
                logger.warning(
                    f"Classification failed for section {section.get('section_number', 'unknown')}: {str(e)}"
                )
                continue

        return classifications

    def _extract_section_content(self, chunks: List[Dict], section: Dict) -> str:
        """Extract content for a specific section from chunks."""
        # Simple implementation - find chunks that match section pages
        section_content = []
        page_range = section.get("page_range", [0, 0])

        for chunk in chunks:
            chunk_metadata = chunk.get("metadata", {})
            chunk_page = chunk_metadata.get("page", 0)

            if page_range[0] <= chunk_page <= page_range[1]:
                section_content.append(chunk.get("content", ""))

        return "\n\n".join(section_content)

    def _generate_analysis_result(
        self, pdf_path: str, structure_analysis: Dict, classifications: List[Dict]
    ) -> DocumentAnalysis:
        """Generate final document analysis result."""
        # Determine document version from path
        document_version = "2024" if "2024" in str(pdf_path) else "2021"

        # Create DocumentSection objects
        sections = []
        total_confidence = 0

        for classification in classifications:
            section = DocumentSection(
                section_number=classification.get("section_number", ""),
                title=classification.get("title", ""),
                page_range=tuple(classification.get("page_range", [0, 0])),
                content_type=classification.get("content_type", "unknown"),
                use_case_count=classification.get("use_case_count", 0),
                confidence=classification.get("confidence", 0.0),
                summary=classification.get("summary", ""),
            )
            sections.append(section)
            total_confidence += section.confidence

        # Calculate overall confidence
        avg_confidence = total_confidence / len(sections) if sections else 0.0

        # Create analysis result
        analysis = DocumentAnalysis(
            document_path=str(pdf_path),
            document_version=document_version,
            total_pages=structure_analysis.get("total_pages", 0),
            identified_sections=sections,
            metadata={
                "document_type": structure_analysis.get("metadata", {}).get(
                    "document_type", "ISO/IEC TR 24030"
                ),
                "main_use_case_section": structure_analysis.get("metadata", {}).get(
                    "main_use_case_section", "7"
                ),
                "total_estimated_use_cases": sum(s.use_case_count for s in sections),
                "processing_model": self.model_config.PDF_ANALYZER_MODEL,
            },
            analysis_timestamp=datetime.now().isoformat(),
            confidence_score=round(avg_confidence, 3),
        )

        return analysis


# Utility functions for testing and development
def analyze_pdf_document(
    pdf_path: str, analysis_mode: str = "detailed"
) -> DocumentAnalysis:
    """
    Standalone function to analyze a PDF document.

    Args:
        pdf_path: Path to PDF file
        analysis_mode: "quick" or "detailed"

    Returns:
        DocumentAnalysis object
    """
    analyzer = DocumentAnalyzerAgent()
    result = analyzer.run(pdf_path=pdf_path, analysis_mode=analysis_mode)

    if result["success"]:
        return DocumentAnalysis(**result["analysis"])
    else:
        raise Exception(f"Analysis failed: {result['error']}")


if __name__ == "__main__":
    # Test the DocumentAnalyzerAgent
    import sys

    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
        try:
            analysis = analyze_pdf_document(pdf_path)
            print(f"Analysis completed for {analysis.document_version} document")
            print(f"Found {len(analysis.identified_sections)} sections")
            print(
                f"Estimated {analysis.metadata['total_estimated_use_cases']} use cases"
            )
            print(f"Confidence: {analysis.confidence_score}")

            for section in analysis.identified_sections:
                if section.use_case_count > 0:
                    print(
                        f"  {section.section_number}: {section.title} ({section.use_case_count} use cases)"
                    )

        except Exception as e:
            print(f"Error: {e}")
    else:
        print("Usage: python document_analyzer.py <pdf_path>")
