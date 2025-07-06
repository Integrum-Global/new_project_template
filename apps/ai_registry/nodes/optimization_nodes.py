"""
Optimization Nodes for Advanced RAG - Kailash SDK

State-of-the-art optimization nodes implementing contextual compression,
HyDE, query transformation, self-query, and adaptive RAG techniques.
"""

import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from kailash.nodes.ai import EmbeddingGeneratorNode, LLMAgentNode
from kailash.nodes.base import Node, NodeParameter
from kailash.nodes.transform import DataTransformer

logger = logging.getLogger(__name__)


class ContextualCompressorNode(Node):
    """
    Contextual compression node that filters and compresses retrieved content
    to maximize relevant information density for optimal context utilization.
    """

    def __init__(self, name: str = "contextual_compressor", **kwargs):
        # Set attributes before calling super().__init__() as Kailash validates during init
        self.max_tokens = kwargs.get("max_tokens", 4000)
        self.compression_ratio = kwargs.get("compression_ratio", 0.6)
        self.relevance_threshold = kwargs.get("relevance_threshold", 0.7)
        self.compression_strategy = kwargs.get(
            "compression_strategy", "extractive_summarization"
        )

        super().__init__(name=name)

        # Relevance scorer
        self.relevance_scorer = LLMAgentNode(
            name=f"{name}_relevance_scorer",
            provider="ollama",
            model="llama3.2:3b",
            system_prompt=self._get_relevance_scoring_prompt(),
            temperature=0.0,
        )

        # Content compressor
        self.content_compressor = LLMAgentNode(
            name=f"{name}_compressor",
            provider="ollama",
            model="llama3.2:3b",
            system_prompt=self._get_compression_prompt(),
            temperature=0.1,
        )

        # Passage selector
        self.passage_selector = DataTransformer(
            name=f"{name}_selector",
            transformations=[
                "result = score_passages_for_relevance(query, passages)",
                "result = rank_by_relevance_and_diversity(result)",
                "result = select_top_passages(result, max_tokens, compression_ratio)",
            ],
        )

        logger.info(
            f"ContextualCompressorNode initialized with max_tokens={self.max_tokens}"
        )

    def compress_context(
        self,
        query: str,
        retrieved_docs: List[Dict[str, Any]],
        compression_target: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Compress retrieved context for optimal relevance and density."""

        if compression_target is None:
            compression_target = self.max_tokens

        if not retrieved_docs:
            return {"compressed_context": "", "compression_metadata": {}}

        logger.info(
            f"Compressing {len(retrieved_docs)} documents to {compression_target} tokens"
        )

        # Stage 1: Score passages for relevance
        scored_passages = self._score_passage_relevance(query, retrieved_docs)

        # Stage 2: Select optimal passages
        selected_passages = self._select_optimal_passages(
            scored_passages, compression_target
        )

        # Stage 3: Compress selected content
        compressed_context = self._compress_selected_content(query, selected_passages)

        # Stage 4: Generate metadata
        compression_metadata = self._generate_compression_metadata(
            retrieved_docs, selected_passages, compressed_context
        )

        logger.info(
            f"Compression completed: {len(retrieved_docs)} docs -> {len(compressed_context)} chars"
        )

        return {
            "compressed_context": compressed_context,
            "compression_metadata": compression_metadata,
            "selected_passages": selected_passages,
        }

    def _score_passage_relevance(self, query: str, documents: List[Dict]) -> List[Dict]:
        """Score each passage for relevance to the query."""

        scored_passages = []

        for i, doc in enumerate(documents):
            content = doc.get("content", "")

            if not content.strip():
                continue

            # Score relevance using LLM
            scoring_input = {
                "query": query,
                "passage": content[:1000],  # Limit for scoring
                "metadata": doc.get("metadata", {}),
                "scoring_criteria": [
                    "direct_relevance",
                    "information_completeness",
                    "factual_accuracy",
                    "unique_value",
                ],
            }

            scoring_result = self.relevance_scorer.run(
                provider="ollama",
                model="llama3.2:3b",
                messages=[{"role": "user", "content": json.dumps(scoring_input)}],
            )
            relevance_score = scoring_result.get("relevance_score", 0.5)
            importance_factors = scoring_result.get("importance_factors", {})

            # Combine with original retrieval score
            original_score = doc.get("similarity_score", 0.5)
            combined_score = 0.7 * relevance_score + 0.3 * original_score

            if combined_score >= self.relevance_threshold:
                scored_passages.append(
                    {
                        "document": doc,
                        "content": content,
                        "relevance_score": relevance_score,
                        "combined_score": combined_score,
                        "importance_factors": importance_factors,
                        "original_index": i,
                        "token_count": len(content.split())
                        * 1.3,  # Rough token estimate
                    }
                )

        # Sort by combined score
        scored_passages.sort(key=lambda x: x["combined_score"], reverse=True)

        return scored_passages

    def _select_optimal_passages(
        self, scored_passages: List[Dict], target_tokens: int
    ) -> List[Dict]:
        """Select optimal passages within token budget."""

        if not scored_passages:
            return []

        selected = []
        total_tokens = 0
        diversity_threshold = 0.8

        for passage in scored_passages:
            passage_tokens = passage["token_count"]

            # Check token budget
            if total_tokens + passage_tokens > target_tokens:
                # Try to fit partial content if it's high value
                if passage["combined_score"] > 0.9 and len(selected) < 3:
                    remaining_tokens = target_tokens - total_tokens
                    if remaining_tokens > 50:  # Minimum useful content
                        # Truncate passage to fit
                        truncated_content = self._truncate_passage(
                            passage["content"], remaining_tokens
                        )
                        passage_copy = passage.copy()
                        passage_copy["content"] = truncated_content
                        passage_copy["token_count"] = remaining_tokens
                        passage_copy["is_truncated"] = True
                        selected.append(passage_copy)
                        total_tokens = target_tokens
                break

            # Check diversity (avoid near-duplicate content)
            is_diverse = True
            for selected_passage in selected:
                similarity = self._calculate_content_similarity(
                    passage["content"], selected_passage["content"]
                )
                if similarity > diversity_threshold:
                    is_diverse = False
                    break

            if is_diverse:
                selected.append(passage)
                total_tokens += passage_tokens

        logger.info(f"Selected {len(selected)} passages ({total_tokens:.0f} tokens)")
        return selected

    def _compress_selected_content(
        self, query: str, selected_passages: List[Dict]
    ) -> str:
        """Compress selected passages into coherent context."""

        if not selected_passages:
            return ""

        # Prepare compression input
        passages_for_compression = []
        for passage in selected_passages:
            passages_for_compression.append(
                {
                    "content": passage["content"],
                    "relevance_score": passage["relevance_score"],
                    "importance_factors": passage["importance_factors"],
                    "is_truncated": passage.get("is_truncated", False),
                }
            )

        compression_input = {
            "query": query,
            "passages": passages_for_compression,
            "compression_strategy": self.compression_strategy,
            "target_compression_ratio": self.compression_ratio,
            "preserve_key_information": True,
        }

        compression_result = self.content_compressor.run(
            provider="ollama",
            model="llama3.2:3b",
            messages=[{"role": "user", "content": json.dumps(compression_input)}],
        )
        compressed_context = compression_result.get("compressed_content", "")

        return compressed_context

    def _calculate_content_similarity(self, content1: str, content2: str) -> float:
        """Calculate similarity between two content pieces."""
        words1 = set(content1.lower().split())
        words2 = set(content2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return intersection / union if union > 0 else 0.0

    def _truncate_passage(self, content: str, max_tokens: int) -> str:
        """Intelligently truncate passage to fit token budget."""
        words = content.split()
        target_words = int(max_tokens / 1.3)  # Rough token-to-word ratio

        if len(words) <= target_words:
            return content

        # Try to end at sentence boundary
        truncated_words = words[:target_words]
        truncated_text = " ".join(truncated_words)

        # Find last sentence boundary
        last_sentence_end = max(
            truncated_text.rfind("."),
            truncated_text.rfind("!"),
            truncated_text.rfind("?"),
        )

        if (
            last_sentence_end > len(truncated_text) * 0.7
        ):  # If we can preserve most content
            return truncated_text[: last_sentence_end + 1]
        else:
            return truncated_text + "..."

    def _generate_compression_metadata(
        self,
        original_docs: List[Dict],
        selected_passages: List[Dict],
        compressed_context: str,
    ) -> Dict[str, Any]:
        """Generate metadata about the compression process."""

        original_length = sum(len(doc.get("content", "")) for doc in original_docs)
        compressed_length = len(compressed_context)

        return {
            "original_document_count": len(original_docs),
            "selected_passage_count": len(selected_passages),
            "original_char_count": original_length,
            "compressed_char_count": compressed_length,
            "compression_ratio": (
                compressed_length / original_length if original_length > 0 else 0
            ),
            "avg_relevance_score": (
                np.mean([p["relevance_score"] for p in selected_passages])
                if selected_passages
                else 0
            ),
            "compression_strategy": self.compression_strategy,
            "token_budget": self.max_tokens,
            "passages_truncated": sum(
                1 for p in selected_passages if p.get("is_truncated", False)
            ),
        }

    def _get_relevance_scoring_prompt(self) -> str:
        """Get prompt for relevance scoring."""
        return """You are a relevance scoring specialist for contextual compression.

        Score how relevant a passage is to the given query on a scale of 0.0 to 1.0:

        Scoring Criteria:
        - Direct relevance: Does the passage directly address the query?
        - Information completeness: Does it provide comprehensive information?
        - Factual accuracy: Is the information accurate and reliable?
        - Unique value: Does it add unique insights not found elsewhere?

        Consider:
        - Semantic relevance beyond keyword matching
        - Quality and depth of information
        - Specificity and detail level
        - Credibility indicators

        Return JSON with:
        - relevance_score: float (0.0-1.0)
        - importance_factors: {factor: weight} for each scoring criterion
        - key_concepts: list of main concepts in the passage"""

    def _get_compression_prompt(self) -> str:
        """Get prompt for content compression."""
        return """You are a contextual compression specialist for RAG systems.

        Compress the given passages into a coherent, information-dense context:

        Compression Guidelines:
        - Preserve all information directly relevant to the query
        - Combine complementary information from multiple passages
        - Remove redundant or tangential content
        - Maintain logical flow and coherence
        - Preserve important facts, figures, and specific details

        Compression Strategies:
        - Extractive summarization: Select key sentences and facts
        - Abstractive synthesis: Rewrite to combine information
        - Hierarchical organization: Structure by importance
        - Concept consolidation: Merge related concepts

        Return compressed_content as a coherent, information-dense text
        that preserves all query-relevant information."""

    def get_parameters(self) -> Dict[str, NodeParameter]:
        """Get node parameters for Kailash framework."""
        return {
            "max_tokens": NodeParameter(
                name="max_tokens",
                type=int,
                required=False,
                default=self.max_tokens,
                description="Maximum tokens for contextual compression",
            ),
            "compression_ratio": NodeParameter(
                name="compression_ratio",
                type=float,
                required=False,
                default=self.compression_ratio,
                description="Target compression ratio",
            ),
            "relevance_threshold": NodeParameter(
                name="relevance_threshold",
                type=float,
                required=False,
                default=self.relevance_threshold,
                description="Relevance threshold for passage selection",
            ),
            "compression_strategy": NodeParameter(
                name="compression_strategy",
                type=str,
                required=False,
                default=self.compression_strategy,
                description="Compression strategy to use",
            ),
        }

    def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Run method required by Kailash Node interface."""
        return self.process(inputs)

    def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Process inputs for Kailash workflow integration."""

        query = inputs.get("query", "")
        retrieved_docs = inputs.get("retrieved_docs", [])
        compression_target = inputs.get("compression_target", self.max_tokens)

        if not query or not retrieved_docs:
            return {
                "error": "Query and retrieved documents required",
                "compressed_context": "",
            }

        result = self.compress_context(query, retrieved_docs, compression_target)

        return {
            "compressed_context": result["compressed_context"],
            "compression_metadata": result["compression_metadata"],
            "num_input_docs": len(retrieved_docs),
            "compression_success": len(result["compressed_context"]) > 0,
        }


class HyDENode(Node):
    """
    Hypothetical Document Embeddings (HyDE) node that generates hypothetical
    documents based on queries to improve retrieval by reducing query-document asymmetry.
    """

    def __init__(self, name: str = "hyde_node", **kwargs):
        # Set attributes before calling super().__init__() as Kailash validates during init
        self.num_hypothetical_docs = kwargs.get("num_hypothetical_docs", 3)
        self.doc_length = kwargs.get("doc_length", "medium")  # short, medium, long
        self.doc_style = kwargs.get("doc_style", "technical")
        self.embedding_model = kwargs.get("embedding_model", "text-embedding-3-small")

        super().__init__(name=name)

        # Document generator
        self.doc_generator = LLMAgentNode(
            name=f"{name}_generator",
            provider="ollama",
            model="llama3.2:3b",
            system_prompt=self._get_document_generation_prompt(),
            temperature=0.7,
        )

        # Embedding generator
        self.embedder = EmbeddingGeneratorNode(
            name=f"{name}_embedder", provider="ollama", model="nomic-embed-text"
        )

        # Quality assessor
        self.quality_assessor = LLMAgentNode(
            name=f"{name}_assessor",
            provider="ollama",
            model="llama3.2:3b",
            system_prompt=self._get_quality_assessment_prompt(),
            temperature=0.1,
        )

        logger.info(
            f"HyDENode initialized to generate {self.num_hypothetical_docs} documents"
        )

    def generate_hypothetical_documents(
        self, query: str, domain_context: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Generate hypothetical documents based on the query."""

        logger.info(
            f"Generating {self.num_hypothetical_docs} hypothetical documents for query"
        )

        # Generate multiple document variants
        hypothetical_docs = []

        for i in range(self.num_hypothetical_docs):
            generation_input = {
                "query": query,
                "domain_context": domain_context or "",
                "document_variant": i + 1,
                "total_variants": self.num_hypothetical_docs,
                "document_length": self.doc_length,
                "document_style": self.doc_style,
                "generation_strategy": self._get_generation_strategy(i),
            }

            generation_result = self.doc_generator.run(
                provider="ollama",
                model="llama3.2:3b",
                messages=[{"role": "user", "content": json.dumps(generation_input)}],
            )
            hypothetical_content = generation_result.get("hypothetical_document", "")

            if hypothetical_content.strip():
                # Assess quality of generated document
                quality_assessment = self._assess_document_quality(
                    query, hypothetical_content
                )

                doc_info = {
                    "content": hypothetical_content,
                    "variant_index": i,
                    "generation_strategy": self._get_generation_strategy(i),
                    "quality_assessment": quality_assessment,
                    "query": query,
                    "domain_context": domain_context,
                }

                hypothetical_docs.append(doc_info)

        logger.info(f"Generated {len(hypothetical_docs)} hypothetical documents")
        return hypothetical_docs

    def generate_hyde_embeddings(
        self, query: str, domain_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate HyDE embeddings for improved retrieval."""

        # Generate hypothetical documents
        hypothetical_docs = self.generate_hypothetical_documents(query, domain_context)

        if not hypothetical_docs:
            logger.warning("No hypothetical documents generated")
            return {"embeddings": [], "documents": []}

        # Extract content for embedding
        doc_contents = [doc["content"] for doc in hypothetical_docs]

        # Generate embeddings
        embedding_result = self.embedder.run(
            operation="embed_batch",
            provider="ollama",
            model="nomic-embed-text",
            input_texts=doc_contents,
        )
        embeddings = embedding_result.get("embeddings", [])

        # Combine embeddings and documents
        hyde_result = {
            "query": query,
            "hypothetical_documents": hypothetical_docs,
            "embeddings": embeddings,
            "embedding_metadata": {
                "model": self.embedding_model,
                "num_documents": len(hypothetical_docs),
                "embedding_dimension": len(embeddings[0]) if embeddings else 0,
                "generation_timestamp": datetime.now().isoformat(),
            },
        }

        return hyde_result

    def hyde_retrieval(
        self,
        query: str,
        document_embeddings: Dict[str, List[float]],
        top_k: int = 20,
        domain_context: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Perform retrieval using HyDE embeddings."""

        # Generate HyDE embeddings
        hyde_result = self.generate_hyde_embeddings(query, domain_context)
        hyde_embeddings = hyde_result.get("embeddings", [])

        if not hyde_embeddings:
            logger.error("Failed to generate HyDE embeddings")
            return []

        # Calculate similarities with document collection
        retrieval_results = []

        for doc_id, doc_embedding in document_embeddings.items():
            # Calculate similarity with each hypothetical document embedding
            similarities = []
            for hyde_embedding in hyde_embeddings:
                similarity = self._cosine_similarity(hyde_embedding, doc_embedding)
                similarities.append(similarity)

            # Use maximum similarity across hypothetical documents
            max_similarity = max(similarities)
            avg_similarity = np.mean(similarities)

            retrieval_results.append(
                {
                    "document_id": doc_id,
                    "max_hyde_similarity": max_similarity,
                    "avg_hyde_similarity": avg_similarity,
                    "hyde_similarities": similarities,
                    "retrieval_method": "hyde",
                }
            )

        # Sort by maximum similarity and return top-k
        retrieval_results.sort(key=lambda x: x["max_hyde_similarity"], reverse=True)
        top_results = retrieval_results[:top_k]

        logger.info(f"HyDE retrieval returned {len(top_results)} results")
        return top_results

    def _get_generation_strategy(self, variant_index: int) -> str:
        """Get generation strategy for document variant."""
        strategies = [
            "comprehensive_answer",  # Detailed, complete response
            "factual_summary",  # Fact-focused, concise
            "conceptual_explanation",  # Concept-heavy, educational
            "technical_analysis",  # Technical depth and detail
            "practical_application",  # Use cases and applications
        ]
        return strategies[variant_index % len(strategies)]

    def _assess_document_quality(self, query: str, document: str) -> Dict[str, Any]:
        """Assess quality of generated hypothetical document."""

        assessment_input = {
            "query": query,
            "generated_document": document,
            "assessment_criteria": [
                "query_alignment",
                "factual_plausibility",
                "content_coherence",
                "information_density",
                "retrieval_effectiveness",
            ],
        }

        result = self.quality_assessor.run(
            provider="ollama",
            model="llama3.2:3b",
            messages=[{"role": "user", "content": json.dumps(assessment_input)}],
        )

        return result.get(
            "quality_assessment",
            {
                "overall_quality": 0.7,
                "query_alignment": 0.7,
                "factual_plausibility": 0.7,
                "content_coherence": 0.7,
                "information_density": 0.7,
                "retrieval_effectiveness": 0.7,
            },
        )

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        vec1_np = np.array(vec1)
        vec2_np = np.array(vec2)

        norm1 = np.linalg.norm(vec1_np)
        norm2 = np.linalg.norm(vec2_np)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return np.dot(vec1_np, vec2_np) / (norm1 * norm2)

    def _get_document_generation_prompt(self) -> str:
        """Get prompt for hypothetical document generation."""
        return """You are a hypothetical document generator for improving retrieval systems.

        Generate a plausible document that would contain information relevant to the query:

        Generation Guidelines:
        - Create content that would realistically exist and answer the query
        - Include specific details, facts, and examples
        - Use appropriate technical terminology and domain language
        - Structure information logically and coherently
        - Vary perspective and focus across document variants

        Document Styles:
        - comprehensive_answer: Detailed, complete coverage of the topic
        - factual_summary: Concise, fact-focused information
        - conceptual_explanation: Educational, concept-heavy content
        - technical_analysis: Deep technical details and analysis
        - practical_application: Real-world use cases and applications

        The goal is to create documents that would rank highly for the query
        and bridge the semantic gap between query and real documents.

        Return hypothetical_document as realistic, query-relevant content."""

    def _get_quality_assessment_prompt(self) -> str:
        """Get prompt for quality assessment."""
        return """You are a quality assessor for hypothetical documents in retrieval systems.

        Assess the generated document across these criteria:

        Assessment Criteria:
        - query_alignment: How well does the document address the query?
        - factual_plausibility: How plausible and realistic is the content?
        - content_coherence: How well-structured and coherent is the text?
        - information_density: How much useful information does it contain?
        - retrieval_effectiveness: How effective would this be for retrieval?

        Score each criterion from 0.0 to 1.0 and provide an overall quality score.

        Return quality_assessment with scores for each criterion."""

    def get_parameters(self) -> Dict[str, NodeParameter]:
        """Get node parameters for Kailash framework."""
        return {
            "num_hypothetical_docs": NodeParameter(
                name="num_hypothetical_docs",
                type=int,
                required=False,
                default=self.num_hypothetical_docs,
                description="Number of hypothetical documents to generate",
            ),
            "doc_length": NodeParameter(
                name="doc_length",
                type=str,
                required=False,
                default=self.doc_length,
                description="Length of generated documents (short, medium, long)",
            ),
            "doc_style": NodeParameter(
                name="doc_style",
                type=str,
                required=False,
                default=self.doc_style,
                description="Style of generated documents",
            ),
            "embedding_model": NodeParameter(
                name="embedding_model",
                type=str,
                required=False,
                default=self.embedding_model,
                description="Embedding model for document embeddings",
            ),
        }

    def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Run method required by Kailash Node interface."""
        return self.process(inputs)

    def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Process inputs for Kailash workflow integration."""

        query = inputs.get("query", "")
        domain_context = inputs.get("domain_context", None)
        task = inputs.get(
            "task", "generate_embeddings"
        )  # "generate_embeddings" or "retrieval"

        if not query:
            return {"error": "Query required", "result": {}}

        if task == "generate_embeddings":
            result = self.generate_hyde_embeddings(query, domain_context)
            return {
                "hyde_embeddings": result.get("embeddings", []),
                "hypothetical_documents": result.get("hypothetical_documents", []),
                "embedding_metadata": result.get("embedding_metadata", {}),
                "query": query,
            }

        elif task == "retrieval":
            document_embeddings = inputs.get("document_embeddings", {})
            top_k = inputs.get("top_k", 20)

            if not document_embeddings:
                return {
                    "error": "Document embeddings required for retrieval",
                    "results": [],
                }

            results = self.hyde_retrieval(
                query, document_embeddings, top_k, domain_context
            )
            return {
                "retrieval_results": results,
                "num_results": len(results),
                "retrieval_method": "hyde",
            }

        else:
            return {"error": f"Unknown task: {task}", "result": {}}


class QueryTransformerNode(Node):
    """
    Query transformation node that rewrites and expands queries
    for improved retrieval accuracy using multiple transformation strategies.
    """

    def __init__(self, name: str = "query_transformer", **kwargs):
        # Set attributes before calling super().__init__() as Kailash validates during init
        self.transformation_strategies = kwargs.get(
            "transformation_strategies",
            [
                "expansion",
                "rewriting",
                "decomposition",
                "clarification",
                "specialization",
            ],
        )
        self.max_variants = kwargs.get("max_variants", 5)
        self.include_original = kwargs.get("include_original", True)

        super().__init__(name=name)

        # Query analyzer
        self.query_analyzer = LLMAgentNode(
            name=f"{name}_analyzer",
            provider="ollama",
            model="llama3.2:3b",
            system_prompt=self._get_query_analysis_prompt(),
            temperature=0.1,
        )

        # Query transformer
        self.query_transformer = LLMAgentNode(
            name=f"{name}_transformer",
            provider="ollama",
            model="llama3.2:3b",
            system_prompt=self._get_transformation_prompt(),
            temperature=0.3,
        )

        # Query validator
        self.query_validator = LLMAgentNode(
            name=f"{name}_validator",
            provider="ollama",
            model="llama3.2:3b",
            system_prompt=self._get_validation_prompt(),
            temperature=0.1,
        )

        logger.info(
            f"QueryTransformerNode initialized with {len(self.transformation_strategies)} strategies"
        )

    def transform_query(
        self, original_query: str, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Transform query using multiple strategies."""

        logger.info(f"Transforming query: '{original_query[:50]}...'")

        # Analyze original query
        query_analysis = self._analyze_query(original_query, context)

        # Generate transformations
        transformations = self._generate_transformations(
            original_query, query_analysis, context
        )

        # Validate transformations
        validated_transformations = self._validate_transformations(
            original_query, transformations, query_analysis
        )

        # Rank transformations
        ranked_transformations = self._rank_transformations(
            original_query, validated_transformations, query_analysis
        )

        result = {
            "original_query": original_query,
            "query_analysis": query_analysis,
            "transformations": ranked_transformations,
            "recommended_queries": [
                t["transformed_query"] for t in ranked_transformations[:3]
            ],
            "transformation_metadata": {
                "strategies_used": self.transformation_strategies,
                "num_transformations": len(ranked_transformations),
                "analysis_timestamp": datetime.now().isoformat(),
            },
        }

        logger.info(f"Generated {len(ranked_transformations)} query transformations")
        return result

    def _analyze_query(
        self, query: str, context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Analyze query characteristics and requirements."""

        analysis_input = {
            "query": query,
            "context": context or {},
            "analysis_dimensions": [
                "intent",
                "complexity",
                "ambiguity",
                "specificity",
                "domain",
                "scope",
                "information_need",
            ],
        }

        result = self.query_analyzer.run(
            provider="ollama",
            model="llama3.2:3b",
            messages=[{"role": "user", "content": json.dumps(analysis_input)}],
        )

        return result.get(
            "query_analysis",
            {
                "intent": "informational",
                "complexity": "medium",
                "ambiguity": "low",
                "specificity": "medium",
                "domain": "general",
                "scope": "focused",
                "information_need": "factual",
                "transformation_opportunities": [],
            },
        )

    def _generate_transformations(
        self,
        original_query: str,
        analysis: Dict[str, Any],
        context: Optional[Dict] = None,
    ) -> List[Dict[str, Any]]:
        """Generate query transformations using multiple strategies."""

        transformations = []

        for strategy in self.transformation_strategies:
            transformation_input = {
                "original_query": original_query,
                "query_analysis": analysis,
                "transformation_strategy": strategy,
                "context": context or {},
                "strategy_descriptions": {
                    "expansion": "Add related terms, synonyms, and broader concepts",
                    "rewriting": "Rephrase for clarity and different perspectives",
                    "decomposition": "Break complex queries into sub-questions",
                    "clarification": "Make ambiguous queries more specific",
                    "specialization": "Focus on specific aspects or domains",
                },
            }

            result = self.query_transformer.run(
                provider="ollama",
                model="llama3.2:3b",
                messages=[
                    {"role": "user", "content": json.dumps(transformation_input)}
                ],
            )
            strategy_transformations = result.get("transformations", [])

            for transformation in strategy_transformations:
                transformation["strategy"] = strategy
                transformation["confidence"] = transformation.get("confidence", 0.7)
                transformations.append(transformation)

        return transformations

    def _validate_transformations(
        self, original_query: str, transformations: List[Dict], analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Validate quality and effectiveness of transformations."""

        validated = []

        for transformation in transformations:
            validation_input = {
                "original_query": original_query,
                "transformed_query": transformation.get("transformed_query", ""),
                "transformation_strategy": transformation.get("strategy", ""),
                "query_analysis": analysis,
                "validation_criteria": [
                    "semantic_preservation",
                    "clarity_improvement",
                    "retrieval_effectiveness",
                    "information_completeness",
                ],
            }

            validation_result = self.query_validator.run(
                provider="ollama",
                model="llama3.2:3b",
                messages=[{"role": "user", "content": json.dumps(validation_input)}],
            )
            validation_scores = validation_result.get("validation_scores", {})

            # Add validation information
            transformation["validation"] = validation_scores
            transformation["overall_quality"] = validation_scores.get(
                "overall_quality", 0.5
            )
            transformation["is_valid"] = (
                validation_scores.get("overall_quality", 0.5) > 0.6
            )

            if transformation["is_valid"]:
                validated.append(transformation)

        return validated

    def _rank_transformations(
        self, original_query: str, transformations: List[Dict], analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Rank transformations by expected effectiveness."""

        # Calculate ranking scores
        for transformation in transformations:
            # Combine multiple scoring factors
            confidence = transformation.get("confidence", 0.5)
            quality = transformation.get("overall_quality", 0.5)
            strategy_weight = self._get_strategy_weight(
                transformation.get("strategy", ""), analysis
            )

            ranking_score = 0.4 * confidence + 0.4 * quality + 0.2 * strategy_weight
            transformation["ranking_score"] = ranking_score

        # Sort by ranking score
        ranked = sorted(transformations, key=lambda x: x["ranking_score"], reverse=True)

        # Add rank positions
        for i, transformation in enumerate(ranked):
            transformation["rank"] = i + 1

        return ranked[: self.max_variants]

    def _get_strategy_weight(self, strategy: str, analysis: Dict[str, Any]) -> float:
        """Get strategy weight based on query analysis."""

        query_complexity = analysis.get("complexity", "medium")
        query_ambiguity = analysis.get("ambiguity", "low")
        query_specificity = analysis.get("specificity", "medium")

        weights = {
            "expansion": 0.8 if query_specificity == "low" else 0.6,
            "rewriting": 0.7 if query_ambiguity == "high" else 0.5,
            "decomposition": 0.9 if query_complexity == "high" else 0.4,
            "clarification": 0.8 if query_ambiguity == "high" else 0.3,
            "specialization": 0.7 if query_specificity == "low" else 0.8,
        }

        return weights.get(strategy, 0.5)

    def _get_query_analysis_prompt(self) -> str:
        """Get prompt for query analysis."""
        return """You are a query analysis specialist for information retrieval.

        Analyze the query across multiple dimensions:

        Analysis Dimensions:
        - intent: informational, navigational, transactional, comparison
        - complexity: simple, medium, complex, multi-faceted
        - ambiguity: low, medium, high (how unclear or ambiguous)
        - specificity: low, medium, high (how specific vs. broad)
        - domain: general, technical, academic, commercial, etc.
        - scope: narrow, focused, broad, comprehensive
        - information_need: factual, analytical, procedural, comparative

        Also identify transformation opportunities:
        - Which strategies would most benefit this query?
        - What are the main limitations of the current query?
        - What additional context would be helpful?

        Return query_analysis with scores and recommendations."""

    def _get_transformation_prompt(self) -> str:
        """Get prompt for query transformation."""
        return """You are a query transformation specialist for improving retrieval effectiveness.

        Transform the query using the specified strategy:

        Transformation Strategies:
        - expansion: Add synonyms, related terms, broader concepts
        - rewriting: Rephrase for different perspectives and clarity
        - decomposition: Break into focused sub-questions
        - clarification: Make vague queries more specific and precise
        - specialization: Focus on particular aspects or domains

        Transformation Guidelines:
        - Preserve the original intent and information need
        - Improve retrieval effectiveness and precision
        - Make queries more specific and actionable
        - Consider different user perspectives and vocabularies
        - Maintain semantic coherence and clarity

        Return transformations as a list with:
        - transformed_query: the transformed query text
        - transformation_rationale: explanation of changes made
        - confidence: confidence in transformation quality (0.0-1.0)
        - expected_improvement: expected retrieval improvement"""

    def _get_validation_prompt(self) -> str:
        """Get prompt for transformation validation."""
        return """You are a query transformation validator for retrieval systems.

        Validate the quality and effectiveness of query transformations:

        Validation Criteria:
        - semantic_preservation: Does it preserve original intent?
        - clarity_improvement: Is it clearer than the original?
        - retrieval_effectiveness: Will it improve retrieval results?
        - information_completeness: Does it capture all information needs?

        Score each criterion from 0.0 to 1.0 and provide overall quality.

        Return validation_scores with individual and overall scores."""

    def get_parameters(self) -> Dict[str, NodeParameter]:
        """Get node parameters for Kailash framework."""
        return {
            "original_query": NodeParameter(
                name="original_query",
                type=str,
                required=True,
                description="Original query to transform",
            ),
            "context": NodeParameter(
                name="context",
                type=dict,
                required=False,
                default={},
                description="Optional context for transformation",
            ),
            "max_variants": NodeParameter(
                name="max_variants",
                type=int,
                required=False,
                default=self.max_variants,
                description="Maximum number of query variants to generate",
            ),
        }

    def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Run method required by Kailash Node interface."""
        return self.process(inputs)

    def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Process inputs for Kailash workflow integration."""

        original_query = inputs.get("original_query", "")
        context = inputs.get("context", {})

        if not original_query:
            return {"error": "Original query required", "transformations": []}

        result = self.transform_query(original_query, context)

        return {
            "transformed_queries": result["recommended_queries"],
            "all_transformations": result["transformations"],
            "query_analysis": result["query_analysis"],
            "transformation_count": len(result["transformations"]),
            "original_query": original_query,
        }


class SelfQueryNode(Node):
    """
    Self-query node that uses LLMs to generate and refine queries
    for improved retrieval performance through iterative self-improvement.
    """

    def __init__(self, name: str = "self_query_node", **kwargs):
        super().__init__(name=name)

        self.max_iterations = kwargs.get("max_iterations", 3)
        self.improvement_threshold = kwargs.get("improvement_threshold", 0.1)
        self.query_types = kwargs.get(
            "query_types",
            ["specific", "broad", "technical", "conceptual", "comparative"],
        )

        # Query generator
        self.query_generator = LLMAgentNode(
            name=f"{name}_generator",
            provider="ollama",
            model="llama3.2:3b",
            system_prompt=self._get_query_generation_prompt(),
            temperature=0.4,
        )

        # Query evaluator
        self.query_evaluator = LLMAgentNode(
            name=f"{name}_evaluator",
            provider="ollama",
            model="llama3.2:3b",
            system_prompt=self._get_query_evaluation_prompt(),
            temperature=0.1,
        )

        # Query refiner
        self.query_refiner = LLMAgentNode(
            name=f"{name}_refiner",
            provider="ollama",
            model="llama3.2:3b",
            system_prompt=self._get_query_refinement_prompt(),
            temperature=0.2,
        )

        logger.info(
            f"SelfQueryNode initialized with max_iterations={self.max_iterations}"
        )

    def self_query_retrieval(
        self, user_intent: str, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate and refine optimal queries through self-improvement."""

        logger.info(f"Self-query retrieval for intent: '{user_intent[:50]}...'")

        # Initial query generation
        current_queries = self._generate_initial_queries(user_intent, context)

        # Iterative improvement
        iteration_history = []

        for iteration in range(self.max_iterations):
            logger.info(f"Self-query iteration {iteration + 1}/{self.max_iterations}")

            # Evaluate current queries
            evaluation_results = self._evaluate_queries(
                user_intent, current_queries, context
            )

            # Check for convergence
            if self._has_converged(evaluation_results, iteration_history):
                logger.info(f"Converged after {iteration + 1} iterations")
                break

            # Refine queries based on evaluation
            refined_queries = self._refine_queries(
                user_intent, current_queries, evaluation_results, context
            )

            # Store iteration results
            iteration_history.append(
                {
                    "iteration": iteration + 1,
                    "queries": current_queries.copy(),
                    "evaluations": evaluation_results,
                    "improvements": self._calculate_improvements(
                        evaluation_results,
                        (
                            iteration_history[-1]["evaluations"]
                            if iteration_history
                            else None
                        ),
                    ),
                }
            )

            current_queries = refined_queries

        # Final evaluation and selection
        final_evaluation = self._evaluate_queries(user_intent, current_queries, context)
        optimal_queries = self._select_optimal_queries(
            current_queries, final_evaluation
        )

        result = {
            "user_intent": user_intent,
            "optimal_queries": optimal_queries,
            "all_generated_queries": current_queries,
            "final_evaluation": final_evaluation,
            "iteration_history": iteration_history,
            "convergence_info": {
                "converged": len(iteration_history) < self.max_iterations,
                "total_iterations": len(iteration_history) + 1,
                "final_scores": [q["overall_score"] for q in final_evaluation],
            },
        }

        logger.info(f"Self-query completed with {len(optimal_queries)} optimal queries")
        return result

    def _generate_initial_queries(
        self, user_intent: str, context: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """Generate initial set of queries for different query types."""

        initial_queries = []

        for query_type in self.query_types:
            generation_input = {
                "user_intent": user_intent,
                "context": context or {},
                "query_type": query_type,
                "generation_guidelines": {
                    "specific": "Create precise, targeted queries",
                    "broad": "Create comprehensive, wide-scope queries",
                    "technical": "Create domain-specific, technical queries",
                    "conceptual": "Create concept-focused, educational queries",
                    "comparative": "Create comparison and analysis queries",
                },
            }

            result = self.query_generator.run(
                provider="ollama",
                model="llama3.2:3b",
                messages=[{"role": "user", "content": json.dumps(generation_input)}],
            )
            generated_queries = result.get("generated_queries", [])

            for query_text in generated_queries:
                initial_queries.append(
                    {
                        "query_text": query_text,
                        "query_type": query_type,
                        "generation_iteration": 0,
                        "confidence": 0.7,  # Initial confidence
                    }
                )

        return initial_queries

    def _evaluate_queries(
        self, user_intent: str, queries: List[Dict], context: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """Evaluate quality and effectiveness of queries."""

        evaluations = []

        for query_info in queries:
            evaluation_input = {
                "user_intent": user_intent,
                "query": query_info["query_text"],
                "query_type": query_info["query_type"],
                "context": context or {},
                "evaluation_criteria": [
                    "intent_alignment",
                    "retrieval_effectiveness",
                    "specificity",
                    "clarity",
                    "completeness",
                ],
            }

            result = self.query_evaluator.run(
                provider="ollama",
                model="llama3.2:3b",
                messages=[{"role": "user", "content": json.dumps(evaluation_input)}],
            )
            evaluation = result.get("evaluation", {})

            # Calculate overall score
            scores = evaluation.get("scores", {})
            overall_score = np.mean(list(scores.values())) if scores else 0.5

            evaluations.append(
                {
                    "query_text": query_info["query_text"],
                    "query_type": query_info["query_type"],
                    "scores": scores,
                    "overall_score": overall_score,
                    "strengths": evaluation.get("strengths", []),
                    "weaknesses": evaluation.get("weaknesses", []),
                    "improvement_suggestions": evaluation.get(
                        "improvement_suggestions", []
                    ),
                }
            )

        return evaluations

    def _refine_queries(
        self,
        user_intent: str,
        current_queries: List[Dict],
        evaluations: List[Dict],
        context: Optional[Dict] = None,
    ) -> List[Dict[str, Any]]:
        """Refine queries based on evaluation feedback."""

        refined_queries = []

        for query_info, evaluation in zip(current_queries, evaluations):
            if evaluation["overall_score"] >= 0.8:  # Already high quality
                refined_queries.append(query_info)
                continue

            refinement_input = {
                "user_intent": user_intent,
                "original_query": query_info["query_text"],
                "query_type": query_info["query_type"],
                "evaluation_feedback": evaluation,
                "context": context or {},
                "refinement_focus": evaluation.get("improvement_suggestions", []),
            }

            result = self.query_refiner.run(
                provider="ollama",
                model="llama3.2:3b",
                messages=[{"role": "user", "content": json.dumps(refinement_input)}],
            )
            refined_query_text = result.get("refined_query", query_info["query_text"])
            refinement_rationale = result.get("refinement_rationale", "")

            refined_query = {
                "query_text": refined_query_text,
                "query_type": query_info["query_type"],
                "generation_iteration": query_info.get("generation_iteration", 0) + 1,
                "confidence": min(1.0, query_info.get("confidence", 0.7) + 0.1),
                "refinement_rationale": refinement_rationale,
                "original_query": query_info["query_text"],
            }

            refined_queries.append(refined_query)

        return refined_queries

    def _has_converged(
        self, current_evaluations: List[Dict], iteration_history: List[Dict]
    ) -> bool:
        """Check if query refinement has converged."""

        if not iteration_history:
            return False

        # Get previous evaluation scores
        previous_evaluations = iteration_history[-1]["evaluations"]

        # Calculate average improvement
        current_avg = np.mean([e["overall_score"] for e in current_evaluations])
        previous_avg = np.mean([e["overall_score"] for e in previous_evaluations])

        improvement = current_avg - previous_avg

        # Converged if improvement is below threshold
        return improvement < self.improvement_threshold

    def _calculate_improvements(
        self, current_evals: List[Dict], previous_evals: Optional[List[Dict]]
    ) -> Dict[str, float]:
        """Calculate improvements from previous iteration."""

        if not previous_evals:
            return {"average_improvement": 0.0}

        current_scores = [e["overall_score"] for e in current_evals]
        previous_scores = [e["overall_score"] for e in previous_evals]

        improvements = [
            curr - prev for curr, prev in zip(current_scores, previous_scores)
        ]

        return {
            "average_improvement": np.mean(improvements),
            "max_improvement": max(improvements),
            "min_improvement": min(improvements),
            "queries_improved": sum(1 for imp in improvements if imp > 0),
        }

    def _select_optimal_queries(
        self, queries: List[Dict], evaluations: List[Dict]
    ) -> List[Dict[str, Any]]:
        """Select optimal queries from refined set."""

        # Combine queries with evaluations
        query_eval_pairs = list(zip(queries, evaluations))

        # Sort by overall score
        query_eval_pairs.sort(key=lambda x: x[1]["overall_score"], reverse=True)

        # Select top queries (up to 3)
        optimal_queries = []
        for query_info, evaluation in query_eval_pairs[:3]:
            optimal_queries.append(
                {
                    "query_text": query_info["query_text"],
                    "query_type": query_info["query_type"],
                    "overall_score": evaluation["overall_score"],
                    "confidence": query_info.get("confidence", 0.7),
                    "refinement_iterations": query_info.get("generation_iteration", 0),
                    "strengths": evaluation.get("strengths", []),
                    "evaluation_scores": evaluation.get("scores", {}),
                }
            )

        return optimal_queries

    def _get_query_generation_prompt(self) -> str:
        """Get prompt for query generation."""
        return """You are an expert query generator for information retrieval systems.

        Generate optimal queries based on user intent and query type:

        Query Types:
        - specific: Precise, targeted queries for exact information
        - broad: Comprehensive queries covering multiple aspects
        - technical: Domain-specific queries using technical terminology
        - conceptual: Educational queries focusing on concepts and understanding
        - comparative: Queries for comparison and analysis tasks

        Generation Guidelines:
        - Align queries closely with user intent
        - Use appropriate vocabulary and terminology
        - Consider different information needs and perspectives
        - Optimize for retrieval effectiveness
        - Ensure clarity and specificity

        Return generated_queries as a list of query strings."""

    def _get_query_evaluation_prompt(self) -> str:
        """Get prompt for query evaluation."""
        return """You are a query evaluation specialist for retrieval systems.

        Evaluate queries across multiple criteria:

        Evaluation Criteria:
        - intent_alignment: How well does the query match user intent?
        - retrieval_effectiveness: How effective will this be for retrieval?
        - specificity: Is the query appropriately specific?
        - clarity: Is the query clear and unambiguous?
        - completeness: Does it capture all aspects of the information need?

        For each criterion, provide:
        - Score (0.0-1.0)
        - Brief explanation

        Also identify:
        - Strengths of the query
        - Weaknesses and limitations
        - Specific improvement suggestions

        Return evaluation with scores, strengths, weaknesses, and suggestions."""

    def _get_query_refinement_prompt(self) -> str:
        """Get prompt for query refinement."""
        return """You are a query refinement specialist for improving retrieval performance.

        Refine the query based on evaluation feedback:

        Refinement Strategies:
        - Address identified weaknesses
        - Enhance clarity and specificity
        - Improve alignment with user intent
        - Add missing context or terminology
        - Remove ambiguous or problematic elements

        Refinement Guidelines:
        - Preserve the core intent and meaning
        - Make targeted improvements based on feedback
        - Enhance retrieval effectiveness
        - Maintain query naturalness and readability
        - Consider domain-specific requirements

        Return refined_query and refinement_rationale explaining changes made."""

    def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Process inputs for Kailash workflow integration."""

        user_intent = inputs.get("user_intent", "")
        context = inputs.get("context", {})

        if not user_intent:
            return {"error": "User intent required", "optimal_queries": []}

        result = self.self_query_retrieval(user_intent, context)

        return {
            "optimal_queries": [q["query_text"] for q in result["optimal_queries"]],
            "query_details": result["optimal_queries"],
            "convergence_info": result["convergence_info"],
            "iteration_count": result["convergence_info"]["total_iterations"],
            "user_intent": user_intent,
        }


class AdaptiveRAGNode(Node):
    """
    Adaptive RAG node that dynamically adjusts retrieval strategies
    based on query characteristics, user feedback, and performance metrics.
    """

    def __init__(self, name: str = "adaptive_rag_node", **kwargs):
        super().__init__(name=name)

        self.available_strategies = kwargs.get(
            "available_strategies",
            [
                "dense_retrieval",
                "sparse_retrieval",
                "hybrid_retrieval",
                "contextual_compression",
                "hyde",
                "query_expansion",
            ],
        )
        self.adaptation_history = []
        self.performance_tracker = {}

        # Strategy selector
        self.strategy_selector = LLMAgentNode(
            name=f"{name}_selector",
            provider="ollama",
            model="llama3.2:3b",
            system_prompt=self._get_strategy_selection_prompt(),
            temperature=0.2,
        )

        # Performance analyzer
        self.performance_analyzer = LLMAgentNode(
            name=f"{name}_analyzer",
            provider="ollama",
            model="llama3.2:3b",
            system_prompt=self._get_performance_analysis_prompt(),
            temperature=0.1,
        )

        # Adaptation engine
        self.adaptation_engine = DataTransformer(
            name=f"{name}_adapter",
            transformations=[
                "result = analyze_query_characteristics(query, context)",
                "result = select_optimal_strategies(result, available_strategies)",
                "result = adapt_parameters_based_on_history(result, performance_history)",
            ],
        )

        logger.info(
            f"AdaptiveRAGNode initialized with {len(self.available_strategies)} strategies"
        )

    def adaptive_retrieval(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        user_feedback: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Perform adaptive retrieval with dynamic strategy selection."""

        logger.info(f"Adaptive retrieval for query: '{query[:50]}...'")

        # Analyze query and context
        query_analysis = self._analyze_query_context(query, context)

        # Select optimal strategies
        selected_strategies = self._select_strategies(query_analysis, user_feedback)

        # Execute retrieval with selected strategies
        retrieval_results = self._execute_adaptive_retrieval(
            query, selected_strategies, context
        )

        # Analyze performance
        performance_metrics = self._analyze_performance(
            query, retrieval_results, user_feedback
        )

        # Update adaptation history
        self._update_adaptation_history(
            query,
            query_analysis,
            selected_strategies,
            performance_metrics,
            user_feedback,
        )

        # Prepare adaptive response
        adaptive_response = {
            "query": query,
            "query_analysis": query_analysis,
            "selected_strategies": selected_strategies,
            "retrieval_results": retrieval_results,
            "performance_metrics": performance_metrics,
            "adaptation_metadata": {
                "adaptation_confidence": selected_strategies.get("confidence", 0.7),
                "strategy_count": len(selected_strategies.get("strategies", [])),
                "adaptation_timestamp": datetime.now().isoformat(),
            },
        }

        logger.info(
            f"Adaptive retrieval completed with {len(selected_strategies.get('strategies', []))} strategies"
        )
        return adaptive_response

    def _analyze_query_context(
        self, query: str, context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Analyze query and context characteristics."""

        analysis_input = {
            "query": query,
            "context": context or {},
            "analysis_dimensions": [
                "complexity",
                "domain",
                "intent",
                "specificity",
                "ambiguity",
                "temporal_aspect",
                "entity_focus",
            ],
            "historical_performance": self._get_relevant_history(query),
        }

        result = self.strategy_selector.run(
            provider="ollama",
            model="llama3.2:3b",
            messages=[{"role": "user", "content": json.dumps(analysis_input)}],
        )

        return result.get(
            "query_analysis",
            {
                "complexity": "medium",
                "domain": "general",
                "intent": "informational",
                "specificity": "medium",
                "ambiguity": "low",
                "retrieval_challenges": [],
                "recommended_approaches": [],
            },
        )

    def _select_strategies(
        self, query_analysis: Dict[str, Any], user_feedback: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Select optimal retrieval strategies based on analysis."""

        selection_input = {
            "query_analysis": query_analysis,
            "available_strategies": self.available_strategies,
            "user_feedback": user_feedback or {},
            "performance_history": self.performance_tracker,
            "strategy_descriptions": {
                "dense_retrieval": "Semantic similarity using embeddings",
                "sparse_retrieval": "Keyword-based retrieval (BM25)",
                "hybrid_retrieval": "Combination of dense and sparse",
                "contextual_compression": "Content filtering and compression",
                "hyde": "Hypothetical document generation",
                "query_expansion": "Query transformation and expansion",
            },
        }

        result = self.strategy_selector.run(
            provider="ollama",
            model="llama3.2:3b",
            messages=[{"role": "user", "content": json.dumps(selection_input)}],
        )

        return result.get(
            "strategy_selection",
            {
                "strategies": ["dense_retrieval"],
                "confidence": 0.7,
                "reasoning": "Default selection",
                "parameters": {},
            },
        )

    def _execute_adaptive_retrieval(
        self, query: str, selected_strategies: Dict, context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Execute retrieval using selected strategies."""

        strategies = selected_strategies.get("strategies", [])
        parameters = selected_strategies.get("parameters", {})

        # Simulate strategy execution (in practice, use actual retrievers)
        results = {
            "strategy_results": {},
            "combined_results": [],
            "execution_metadata": {
                "strategies_executed": strategies,
                "execution_time": 0.5,  # Mock execution time
                "success": True,
            },
        }

        for strategy in strategies:
            # Mock strategy execution
            strategy_result = {
                "strategy": strategy,
                "documents": [
                    {
                        "id": f"{strategy}_doc_{i}",
                        "score": 0.8 - i * 0.1,
                        "content": f"Mock content {i}",
                    }
                    for i in range(5)
                ],
                "execution_time": 0.1,
                "parameters_used": parameters.get(strategy, {}),
            }
            results["strategy_results"][strategy] = strategy_result

        # Combine results from multiple strategies
        all_docs = []
        for strategy_result in results["strategy_results"].values():
            all_docs.extend(strategy_result["documents"])

        # Simple deduplication and ranking
        unique_docs = {doc["id"]: doc for doc in all_docs}.values()
        combined_docs = sorted(unique_docs, key=lambda x: x["score"], reverse=True)[:10]

        results["combined_results"] = combined_docs

        return results

    def _analyze_performance(
        self, query: str, retrieval_results: Dict, user_feedback: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Analyze performance of adaptive retrieval."""

        analysis_input = {
            "query": query,
            "retrieval_results": retrieval_results,
            "user_feedback": user_feedback or {},
            "performance_criteria": [
                "relevance",
                "coverage",
                "diversity",
                "efficiency",
                "user_satisfaction",
            ],
        }

        result = self.performance_analyzer.run(
            provider="ollama",
            model="llama3.2:3b",
            messages=[{"role": "user", "content": json.dumps(analysis_input)}],
        )

        return result.get(
            "performance_metrics",
            {
                "relevance_score": 0.7,
                "coverage_score": 0.6,
                "diversity_score": 0.8,
                "efficiency_score": 0.9,
                "user_satisfaction": 0.7,
                "overall_performance": 0.7,
            },
        )

    def _update_adaptation_history(
        self,
        query: str,
        query_analysis: Dict,
        selected_strategies: Dict,
        performance_metrics: Dict,
        user_feedback: Optional[Dict] = None,
    ):
        """Update adaptation history for learning."""

        adaptation_record = {
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "query_analysis": query_analysis,
            "selected_strategies": selected_strategies,
            "performance_metrics": performance_metrics,
            "user_feedback": user_feedback or {},
            "success": performance_metrics.get("overall_performance", 0) > 0.6,
        }

        self.adaptation_history.append(adaptation_record)

        # Update performance tracker
        for strategy in selected_strategies.get("strategies", []):
            if strategy not in self.performance_tracker:
                self.performance_tracker[strategy] = []

            self.performance_tracker[strategy].append(
                {
                    "query_type": query_analysis.get("domain", "general"),
                    "performance": performance_metrics.get("overall_performance", 0),
                    "timestamp": datetime.now().isoformat(),
                }
            )

        # Keep history bounded
        if len(self.adaptation_history) > 100:
            self.adaptation_history = self.adaptation_history[-50:]

    def _get_relevant_history(self, query: str) -> List[Dict]:
        """Get relevant adaptation history for current query."""

        # Simple similarity-based filtering (in practice, use embeddings)
        relevant_history = []
        query_words = set(query.lower().split())

        for record in self.adaptation_history[-20:]:  # Recent history
            record_words = set(record["query"].lower().split())
            overlap = len(query_words & record_words) / len(query_words | record_words)

            if overlap > 0.3:  # Some similarity
                relevant_history.append(record)

        return relevant_history[-5:]  # Most recent relevant records

    def _get_strategy_selection_prompt(self) -> str:
        """Get prompt for strategy selection."""
        return """You are an adaptive RAG strategy selector.

        Analyze the query and select optimal retrieval strategies:

        Strategy Selection Criteria:
        - Query complexity and structure
        - Domain and technical specificity
        - Information need type (factual, analytical, etc.)
        - Historical performance for similar queries
        - User feedback and preferences

        Available Strategies:
        - dense_retrieval: Best for semantic similarity
        - sparse_retrieval: Best for keyword matching
        - hybrid_retrieval: Balanced approach
        - contextual_compression: For information density
        - hyde: For query-document gap bridging
        - query_expansion: For comprehensive coverage

        Return strategy_selection with:
        - strategies: list of selected strategy names
        - confidence: confidence in selection (0.0-1.0)
        - reasoning: explanation for selection
        - parameters: strategy-specific parameters"""

    def _get_performance_analysis_prompt(self) -> str:
        """Get prompt for performance analysis."""
        return """You are a performance analyzer for adaptive RAG systems.

        Analyze the performance of retrieval results:

        Performance Criteria:
        - relevance_score: How relevant are the results?
        - coverage_score: How comprehensively do they cover the query?
        - diversity_score: How diverse are the perspectives/sources?
        - efficiency_score: How efficient was the retrieval process?
        - user_satisfaction: Based on feedback and engagement

        Consider:
        - Result quality and accuracy
        - Information completeness
        - Response time and efficiency
        - User interaction patterns
        - Feedback signals

        Return performance_metrics with scores (0.0-1.0) for each criterion
        and overall_performance score."""

    def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Process inputs for Kailash workflow integration."""

        query = inputs.get("query", "")
        context = inputs.get("context", {})
        user_feedback = inputs.get("user_feedback", {})

        if not query:
            return {"error": "Query required", "results": {}}

        result = self.adaptive_retrieval(query, context, user_feedback)

        return {
            "adaptive_results": result["retrieval_results"]["combined_results"],
            "selected_strategies": result["selected_strategies"]["strategies"],
            "performance_metrics": result["performance_metrics"],
            "adaptation_confidence": result["adaptation_metadata"][
                "adaptation_confidence"
            ],
            "query": query,
        }
