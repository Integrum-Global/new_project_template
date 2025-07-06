"""
Model configuration for the AI Registry RAG system.
Optimized for cost/performance based on analysis in MODEL_PERFORMANCE_ANALYSIS.md
"""

import os
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class ModelConfig:
    """Configuration for different model types in the RAG pipeline."""

    # Primary models (API-based)
    PDF_ANALYZER_MODEL = "gpt-4o-mini"  # Best cost/performance for PDF analysis
    USE_CASE_EXTRACTOR_MODEL = "gpt-4o-mini"  # Excellent structure understanding
    STRUCTURE_VALIDATOR_MODEL = "gpt-4o-mini"  # Fast validation, good accuracy
    METADATA_ENRICHER_MODEL = "gpt-4o-mini"  # Good for enhancement tasks
    SEMANTIC_ANALYZER_MODEL = "gpt-4o-mini"  # Sufficient for domain analysis

    # Advanced analysis models (high accuracy needed)
    TREND_ANALYZER_MODEL = "gpt-4o"  # Complex reasoning required
    CROSS_DOMAIN_SYNTHESIS_MODEL = "gpt-4o"  # High-quality insights required

    # Embedding models
    PRIMARY_EMBEDDING_MODEL = "text-embedding-3-small"  # Optimal cost/performance
    FALLBACK_EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # Local fallback

    # Local fallback models (via Ollama)
    LOCAL_FALLBACK_MODEL = "llama3.1:8b"  # No API costs, decent performance
    LOCAL_EMBEDDING_MODEL = "nomic-embed-text"  # Local embedding option

    # API Configuration
    OPENAI_API_KEY = "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"
    OLLAMA_BASE_URL = "http://localhost:11434"

    # Performance thresholds
    MAX_TOKENS_PER_REQUEST = 4000
    MAX_RETRIES = 3
    REQUEST_TIMEOUT = 30
    CACHE_TTL = 3600  # 1 hour cache for embeddings

    # Quality thresholds
    MINIMUM_CONFIDENCE_SCORE = 0.85
    VALIDATION_ACCURACY_THRESHOLD = 0.90

    @classmethod
    def get_model_for_task(
        cls,
        task_complexity: str,
        accuracy_required: float,
        budget_constraint: bool = False,
    ) -> str:
        """
        Intelligently select the optimal model based on task requirements.

        Args:
            task_complexity: "low", "medium", "high"
            accuracy_required: 0.0 to 1.0
            budget_constraint: True to prefer cost-effective options

        Returns:
            Model name to use for the task
        """
        if budget_constraint or os.getenv("RAG_USE_LOCAL", "false").lower() == "true":
            return cls.LOCAL_FALLBACK_MODEL

        if task_complexity == "high" and accuracy_required > 0.95:
            return cls.TREND_ANALYZER_MODEL  # gpt-4o
        elif task_complexity in ["medium", "high"] and accuracy_required > 0.90:
            return cls.PDF_ANALYZER_MODEL  # gpt-4o-mini (sweet spot)
        else:
            return cls.PDF_ANALYZER_MODEL  # gpt-4o-mini (default)

    @classmethod
    def get_embedding_model(cls, use_local: bool = False) -> str:
        """Get the appropriate embedding model."""
        if (
            use_local
            or os.getenv("RAG_USE_LOCAL_EMBEDDINGS", "false").lower() == "true"
        ):
            return cls.LOCAL_EMBEDDING_MODEL
        return cls.PRIMARY_EMBEDDING_MODEL

    @classmethod
    def get_api_config(cls) -> Dict[str, Any]:
        """Get API configuration for external models."""
        return {
            "openai": {
                "api_key": os.getenv("OPENAI_API_KEY", cls.OPENAI_API_KEY),
                "base_url": "https://api.openai.com/v1",
                "timeout": cls.REQUEST_TIMEOUT,
                "max_retries": cls.MAX_RETRIES,
            },
            "ollama": {
                "base_url": os.getenv("OLLAMA_BASE_URL", cls.OLLAMA_BASE_URL),
                "timeout": cls.REQUEST_TIMEOUT,
            },
        }

    @classmethod
    def get_cost_estimate(
        cls, input_tokens: int, output_tokens: int, model: str
    ) -> float:
        """
        Estimate cost for a model operation.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            model: Model name

        Returns:
            Estimated cost in USD
        """
        # Pricing per 1M tokens (as of 2024)
        pricing = {
            "gpt-4o": {"input": 2.50, "output": 10.00},
            "gpt-4o-mini": {"input": 0.15, "output": 0.60},
            "text-embedding-3-small": {"input": 0.02, "output": 0.0},
            "text-embedding-3-large": {"input": 0.13, "output": 0.0},
        }

        if model not in pricing:
            return 0.0  # Free local models

        cost = (input_tokens / 1_000_000) * pricing[model]["input"] + (
            output_tokens / 1_000_000
        ) * pricing[model]["output"]
        return round(cost, 6)


class RAGConfig:
    """Configuration for RAG pipeline components."""

    # PDF Processing
    PDF_CHUNK_SIZE = 2000
    PDF_CHUNK_OVERLAP = 200
    PDF_MAX_PAGES = 1000

    # Use Case Extraction
    USE_CASE_SCHEMA = {
        "use_case_id": "integer",
        "name": "string",
        "application_domain": "string",
        "description": "string",
        "narrative": "string",
        "ai_methods": "list[string]",
        "tasks": "list[string]",
        "challenges": "string",
        "deployment_model": "string",
        "automation_level": "string",
        "status": "string",
        "section_reference": "string",
        "source_version": "string",
    }

    # Vector Database
    VECTOR_DIMENSION = 1536  # text-embedding-3-small
    SIMILARITY_THRESHOLD = 0.75
    MAX_RESULTS = 20

    # Knowledge Base
    KNOWLEDGE_BASE_PATH = "knowledge_base"
    MARKDOWN_TEMPLATE = """# {name}

**Use Case ID**: {use_case_id}
**Domain**: {application_domain}
**AI Methods**: {ai_methods}
**Status**: {status}
**Source**: {source_version} - {section_reference}

## Description
{description}

## Narrative
{narrative}

## Implementation Details
- **Tasks**: {tasks}
- **Deployment Model**: {deployment_model}
- **Automation Level**: {automation_level}

## Challenges & Solutions
{challenges}

## Metadata
- **Extracted**: {extraction_date}
- **Confidence**: {confidence_score}
- **Related Use Cases**: {related_cases}

---
*Generated by AI Registry RAG System*
"""


# Environment setup
def setup_environment():
    """Set up environment variables for the RAG system."""
    os.environ.setdefault("OPENAI_API_KEY", ModelConfig.OPENAI_API_KEY)
    os.environ.setdefault("OLLAMA_BASE_URL", ModelConfig.OLLAMA_BASE_URL)
    os.environ.setdefault("RAG_CACHE_TTL", str(ModelConfig.CACHE_TTL))
    os.environ.setdefault("RAG_USE_LOCAL", "false")
    os.environ.setdefault("RAG_LOG_LEVEL", "INFO")


if __name__ == "__main__":
    # Test model selection
    print("Model Selection Examples:")
    print(f"PDF Analysis: {ModelConfig.get_model_for_task('medium', 0.92)}")
    print(f"Complex Reasoning: {ModelConfig.get_model_for_task('high', 0.97)}")
    print(
        f"Budget Mode: {ModelConfig.get_model_for_task('medium', 0.90, budget_constraint=True)}"
    )
    print(f"Embedding Model: {ModelConfig.get_embedding_model()}")

    # Test cost estimation
    cost = ModelConfig.get_cost_estimate(10000, 2000, "gpt-4o-mini")
    print(f"Cost for 10K input + 2K output tokens (GPT-4o Mini): ${cost}")
