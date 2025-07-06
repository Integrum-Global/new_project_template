"""
AI Registry RAG System

A comprehensive Retrieval-Augmented Generation system for processing AI use case documents
and creating a searchable knowledge base.

Components:
- agents/: Intelligent agents for document processing
- workflows/: Kailash workflows for end-to-end processing
- knowledge_base/: Generated markdown files for each use case
- embeddings/: Vector storage and similarity search
- config/: Configuration and model selection
"""

from .agents.document_analyzer import DocumentAnalysis, DocumentAnalyzerAgent
from .config.model_config import ModelConfig, RAGConfig

__version__ = "1.0.0"
__all__ = ["ModelConfig", "RAGConfig", "DocumentAnalyzerAgent", "DocumentAnalysis"]
