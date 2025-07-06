"""
Advanced Reranking Nodes for Kailash SDK

State-of-the-art reranking nodes implementing cross-encoder, LLM-based,
learned ranking, and multi-stage reranking approaches.
"""

import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from kailash.nodes.ai import LLMAgentNode
from kailash.nodes.base import Node
from kailash.nodes.transform import DataTransformer

logger = logging.getLogger(__name__)


class BaseRerankerNode(Node, ABC):
    """Base class for all reranking nodes."""

    def __init__(self, name: str, **kwargs):
        super().__init__(name=name)
        self.top_k = kwargs.get("top_k", 20)
        self.diversity_factor = kwargs.get("diversity_factor", 0.1)
        self.min_score_threshold = kwargs.get("min_score_threshold", 0.0)

    @abstractmethod
    def rerank(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        target_k: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Rerank candidate documents based on query relevance."""
        pass

    def _apply_diversity_filtering(
        self, ranked_docs: List[Dict], diversity_threshold: float = 0.8
    ) -> List[Dict]:
        """Apply diversity filtering to avoid near-duplicate results."""
        if not ranked_docs or self.diversity_factor == 0:
            return ranked_docs

        diverse_docs = [ranked_docs[0]]  # Always include top result

        for doc in ranked_docs[1:]:
            # Check similarity to already selected documents
            is_diverse = True
            for selected_doc in diverse_docs:
                similarity = self._calculate_content_similarity(doc, selected_doc)
                if similarity > diversity_threshold:
                    is_diverse = False
                    break

            if is_diverse:
                diverse_docs.append(doc)

        return diverse_docs

    def _calculate_content_similarity(self, doc1: Dict, doc2: Dict) -> float:
        """Calculate content similarity between two documents (simplified)."""
        content1 = doc1.get("content", "").lower()
        content2 = doc2.get("content", "").lower()

        if not content1 or not content2:
            return 0.0

        # Simple Jaccard similarity on words
        words1 = set(content1.split())
        words2 = set(content2.split())

        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return intersection / union if union > 0 else 0.0


class CrossEncoderRerankerNode(BaseRerankerNode):
    """
    Cross-encoder reranking using transformer models that jointly encode
    query and document pairs for precise relevance scoring.
    """

    def __init__(self, name: str = "cross_encoder_reranker", **kwargs):
        super().__init__(name, **kwargs)

        self.model_name = kwargs.get("model_name", "MonoT5-3B")
        self.batch_size = kwargs.get("batch_size", 16)
        self.max_length = kwargs.get("max_length", 512)

        # Cross-encoder model (simulated with LLM for now)
        self.cross_encoder = LLMAgentNode(
            name=f"{name}_model",
            model="gpt-4o-mini",
            system_prompt=self._get_cross_encoder_prompt(),
            max_tokens=100,
            temperature=0.0,
        )

        logger.info(f"CrossEncoderRerankerNode initialized with {self.model_name}")

    def rerank(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        target_k: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Rerank candidates using cross-encoder scoring."""

        if target_k is None:
            target_k = self.top_k

        if not candidates:
            return []

        logger.info(f"Reranking {len(candidates)} candidates with cross-encoder")

        # Score each query-document pair
        scored_candidates = []

        # Process in batches for efficiency
        for i in range(0, len(candidates), self.batch_size):
            batch = candidates[i : i + self.batch_size]
            batch_scores = self._score_batch(query, batch)

            for doc, score in zip(batch, batch_scores):
                if score >= self.min_score_threshold:
                    doc_copy = doc.copy()
                    doc_copy["rerank_score"] = score
                    doc_copy["original_score"] = doc.get("similarity_score", 0.0)
                    doc_copy["reranker"] = "cross_encoder"
                    scored_candidates.append(doc_copy)

        # Sort by rerank score
        scored_candidates.sort(key=lambda x: x["rerank_score"], reverse=True)

        # Apply diversity filtering if enabled
        if self.diversity_factor > 0:
            scored_candidates = self._apply_diversity_filtering(
                scored_candidates, diversity_threshold=1.0 - self.diversity_factor
            )

        # Return top-k
        final_results = scored_candidates[:target_k]

        # Update similarity scores to rerank scores
        for doc in final_results:
            doc["similarity_score"] = doc["rerank_score"]

        logger.info(
            f"Cross-encoder reranking completed, returning {len(final_results)} documents"
        )
        return final_results

    def _score_batch(self, query: str, batch: List[Dict]) -> List[float]:
        """Score a batch of query-document pairs."""

        batch_input = {
            "query": query,
            "documents": [
                {
                    "content": doc.get("content", "")[: self.max_length],
                    "id": doc.get("id", ""),
                    "title": doc.get("title", ""),
                }
                for doc in batch
            ],
            "scoring_task": "relevance_scoring",
        }

        result = self.cross_encoder.process(batch_input)
        scores = result.get("relevance_scores", [0.5] * len(batch))

        # Ensure we have scores for all documents
        while len(scores) < len(batch):
            scores.append(0.5)

        return scores[: len(batch)]

    def _get_cross_encoder_prompt(self) -> str:
        """Get prompt for cross-encoder scoring."""
        return """You are a cross-encoder relevance scorer for document retrieval.

        Score the relevance of each document to the query on a scale of 0.0 to 1.0:
        - 1.0: Perfectly relevant, directly answers the query
        - 0.8-0.9: Highly relevant, contains most needed information
        - 0.6-0.7: Moderately relevant, contains some useful information
        - 0.4-0.5: Somewhat relevant, tangentially related
        - 0.2-0.3: Minimally relevant, barely related
        - 0.0-0.1: Not relevant, unrelated to query

        Consider:
        - Semantic relevance and query coverage
        - Factual accuracy and completeness
        - Specificity and detail level

        Return relevance_scores as a list of float values."""

    def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Process inputs for Kailash workflow integration."""

        query = inputs.get("query", "")
        candidates = inputs.get("candidates", [])
        target_k = inputs.get("target_k", self.top_k)

        if not query or not candidates:
            return {"error": "Query and candidates required", "reranked_results": []}

        reranked_results = self.rerank(query, candidates, target_k)

        return {
            "reranked_results": reranked_results,
            "query": query,
            "reranker_type": "cross_encoder",
            "num_input": len(candidates),
            "num_output": len(reranked_results),
        }


class LLMRerankerNode(BaseRerankerNode):
    """
    LLM-based reranking using large language models for listwise ranking
    and sophisticated relevance assessment.
    """

    def __init__(self, name: str = "llm_reranker", **kwargs):
        super().__init__(name, **kwargs)

        self.llm_model = kwargs.get("llm_model", "gpt-4o")
        self.ranking_method = kwargs.get(
            "ranking_method", "listwise"
        )  # "listwise" or "pairwise"
        self.max_candidates_per_call = kwargs.get("max_candidates_per_call", 20)
        self.reasoning_enabled = kwargs.get("reasoning_enabled", True)

        # LLM reranker
        self.llm_ranker = LLMAgentNode(
            name=f"{name}_llm",
            model=self.llm_model,
            system_prompt=self._get_llm_ranking_prompt(),
            max_tokens=2000,
            temperature=0.1,
        )

        # For explanation and reasoning
        if self.reasoning_enabled:
            self.reasoning_llm = LLMAgentNode(
                name=f"{name}_reasoning",
                model="gpt-4o-mini",
                system_prompt=self._get_reasoning_prompt(),
                max_tokens=1000,
            )

        logger.info(f"LLMRerankerNode initialized with {self.llm_model}")

    def rerank(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        target_k: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Rerank candidates using LLM-based assessment."""

        if target_k is None:
            target_k = self.top_k

        if not candidates:
            return []

        logger.info(f"LLM reranking {len(candidates)} candidates")

        # Handle large candidate sets by chunking
        if len(candidates) > self.max_candidates_per_call:
            return self._hierarchical_rerank(query, candidates, target_k)
        else:
            return self._direct_rerank(query, candidates, target_k)

    def _direct_rerank(
        self, query: str, candidates: List[Dict], target_k: int
    ) -> List[Dict]:
        """Direct LLM reranking for smaller candidate sets."""

        # Prepare candidates for LLM
        candidate_summaries = []
        for i, doc in enumerate(candidates):
            summary = {
                "rank": i + 1,
                "id": doc.get("id", f"doc_{i}"),
                "title": doc.get("title", "")[:100],
                "content_preview": doc.get("content", "")[:300],
                "original_score": doc.get("similarity_score", 0.0),
            }
            candidate_summaries.append(summary)

        # LLM ranking
        ranking_input = {
            "query": query,
            "candidates": candidate_summaries,
            "ranking_method": self.ranking_method,
            "target_count": target_k,
            "ranking_criteria": [
                "relevance_to_query",
                "information_completeness",
                "factual_accuracy",
                "specificity_and_detail",
            ],
        }

        ranking_result = self.llm_ranker.process(ranking_input)
        ranked_ids = ranking_result.get("ranked_document_ids", [])
        ranking_scores = ranking_result.get("ranking_scores", {})
        explanations = ranking_result.get("explanations", {})

        # Build reranked results
        id_to_doc = {doc.get("id", f"doc_{i}"): doc for i, doc in enumerate(candidates)}
        reranked_results = []

        for i, doc_id in enumerate(ranked_ids[:target_k]):
            if doc_id in id_to_doc:
                doc = id_to_doc[doc_id].copy()
                doc["rerank_score"] = ranking_scores.get(
                    doc_id, 1.0 - (i / len(ranked_ids))
                )
                doc["original_score"] = doc.get("similarity_score", 0.0)
                doc["reranker"] = "llm_listwise"
                doc["rank_position"] = i + 1

                if self.reasoning_enabled and doc_id in explanations:
                    doc["ranking_explanation"] = explanations[doc_id]

                reranked_results.append(doc)

        # Update similarity scores
        for doc in reranked_results:
            doc["similarity_score"] = doc["rerank_score"]

        return reranked_results

    def _hierarchical_rerank(
        self, query: str, candidates: List[Dict], target_k: int
    ) -> List[Dict]:
        """Hierarchical reranking for large candidate sets."""

        # Stage 1: Initial filtering to reduce candidates
        stage1_k = min(self.max_candidates_per_call * 2, len(candidates))
        stage1_candidates = candidates[:stage1_k]

        # Stage 2: LLM reranking on filtered set
        stage2_results = self._direct_rerank(query, stage1_candidates, target_k)

        return stage2_results

    def _get_llm_ranking_prompt(self) -> str:
        """Get prompt for LLM ranking."""
        return """You are an expert document ranker for information retrieval.

        Given a query and a list of candidate documents, rank them by relevance:

        Ranking Criteria:
        1. Direct relevance to the query
        2. Completeness of information
        3. Factual accuracy and reliability
        4. Specificity and detail level
        5. Clarity and comprehensiveness

        For listwise ranking:
        - Consider all documents together
        - Rank from most to least relevant
        - Provide confidence scores (0.0-1.0)
        - Explain ranking decisions

        Return JSON with:
        - ranked_document_ids: ordered list of document IDs
        - ranking_scores: {doc_id: score} mapping
        - explanations: {doc_id: explanation} mapping"""

    def _get_reasoning_prompt(self) -> str:
        """Get prompt for ranking explanations."""
        return """You are a ranking explanation specialist.

        Provide clear, concise explanations for why documents were ranked
        in their positions. Focus on:
        - Key relevance factors
        - Strengths and weaknesses
        - Comparison insights
        - Confidence assessment

        Keep explanations under 100 words each."""

    def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Process inputs for Kailash workflow integration."""

        query = inputs.get("query", "")
        candidates = inputs.get("candidates", [])
        target_k = inputs.get("target_k", self.top_k)

        if not query or not candidates:
            return {"error": "Query and candidates required", "reranked_results": []}

        reranked_results = self.rerank(query, candidates, target_k)

        return {
            "reranked_results": reranked_results,
            "query": query,
            "reranker_type": "llm_listwise",
            "num_input": len(candidates),
            "num_output": len(reranked_results),
        }


class LearnedRankerNode(BaseRerankerNode):
    """
    Learned ranking using machine learning models trained on relevance data.
    Supports feature-based ranking with multiple signals.
    """

    def __init__(self, name: str = "learned_ranker", **kwargs):
        super().__init__(name, **kwargs)

        self.features = kwargs.get(
            "features",
            [
                "semantic_similarity",
                "keyword_overlap",
                "document_length",
                "metadata_relevance",
                "query_document_alignment",
            ],
        )
        self.model_type = kwargs.get("model_type", "gradient_boosting")

        # Feature extractor
        self.feature_extractor = DataTransformer(
            name=f"{name}_feature_extractor",
            transformations=[
                "result = extract_ranking_features(query, documents, feature_types)"
            ],
        )

        # Learned ranking model (simulated)
        self.ranking_model = LLMAgentNode(
            name=f"{name}_model",
            model="gpt-4o-mini",
            system_prompt=self._get_learned_ranking_prompt(),
        )

        logger.info(f"LearnedRankerNode initialized with {len(self.features)} features")

    def rerank(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        target_k: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Rerank using learned ranking model."""

        if target_k is None:
            target_k = self.top_k

        if not candidates:
            return []

        logger.info(f"Learned reranking {len(candidates)} candidates")

        # Extract features for all candidates
        features_result = self.feature_extractor.process(
            {"query": query, "documents": candidates, "feature_types": self.features}
        )

        document_features = features_result.get("result", [])

        # Apply learned ranking model
        ranking_input = {
            "query": query,
            "document_features": document_features,
            "model_type": self.model_type,
            "ranking_task": "feature_based_ranking",
        }

        ranking_result = self.ranking_model.process(ranking_input)
        predicted_scores = ranking_result.get("predicted_scores", [])
        feature_importance = ranking_result.get("feature_importance", {})

        # Combine scores with original documents
        scored_candidates = []
        for i, (doc, score) in enumerate(zip(candidates, predicted_scores)):
            if score >= self.min_score_threshold:
                doc_copy = doc.copy()
                doc_copy["rerank_score"] = score
                doc_copy["original_score"] = doc.get("similarity_score", 0.0)
                doc_copy["reranker"] = "learned_ranking"
                doc_copy["feature_importance"] = feature_importance
                scored_candidates.append(doc_copy)

        # Sort by predicted score
        scored_candidates.sort(key=lambda x: x["rerank_score"], reverse=True)

        # Return top-k
        final_results = scored_candidates[:target_k]

        # Update similarity scores
        for doc in final_results:
            doc["similarity_score"] = doc["rerank_score"]

        logger.info(
            f"Learned reranking completed, returning {len(final_results)} documents"
        )
        return final_results

    def _get_learned_ranking_prompt(self) -> str:
        """Get prompt for learned ranking model."""
        return """You are a learned ranking model for document retrieval.

        Given extracted features for query-document pairs, predict relevance scores:

        Feature Types:
        - semantic_similarity: Vector similarity scores
        - keyword_overlap: Term matching statistics
        - document_length: Document size indicators
        - metadata_relevance: Metadata matching scores
        - query_document_alignment: Structural alignment metrics

        Use these features to predict relevance scores (0.0-1.0) for each document.

        Also provide feature_importance indicating which features were most
        influential for the ranking decisions.

        Return JSON with:
        - predicted_scores: list of relevance scores
        - feature_importance: {feature_name: importance_weight}"""

    def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Process inputs for Kailash workflow integration."""

        query = inputs.get("query", "")
        candidates = inputs.get("candidates", [])
        target_k = inputs.get("target_k", self.top_k)

        if not query or not candidates:
            return {"error": "Query and candidates required", "reranked_results": []}

        reranked_results = self.rerank(query, candidates, target_k)

        return {
            "reranked_results": reranked_results,
            "query": query,
            "reranker_type": "learned_ranking",
            "num_input": len(candidates),
            "num_output": len(reranked_results),
        }


class DiversityRerankerNode(BaseRerankerNode):
    """
    Diversity-aware reranking that balances relevance with result diversity
    to avoid redundant information and provide comprehensive coverage.
    """

    def __init__(self, name: str = "diversity_reranker", **kwargs):
        super().__init__(name, **kwargs)

        self.diversity_strategy = kwargs.get(
            "diversity_strategy", "mmr"
        )  # "mmr", "clustering", "coverage"
        self.lambda_param = kwargs.get(
            "lambda_param", 0.7
        )  # Relevance vs diversity trade-off
        self.clustering_threshold = kwargs.get("clustering_threshold", 0.8)

        # Diversity analyzer
        self.diversity_analyzer = LLMAgentNode(
            name=f"{name}_analyzer",
            model="gpt-4o-mini",
            system_prompt=self._get_diversity_analysis_prompt(),
        )

        logger.info(f"DiversityRerankerNode initialized with {self.diversity_strategy}")

    def rerank(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        target_k: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Rerank with diversity awareness."""

        if target_k is None:
            target_k = self.top_k

        if not candidates:
            return []

        logger.info(f"Diversity reranking {len(candidates)} candidates")

        if self.diversity_strategy == "mmr":
            return self._maximal_marginal_relevance(candidates, target_k)
        elif self.diversity_strategy == "clustering":
            return self._cluster_based_diversity(query, candidates, target_k)
        elif self.diversity_strategy == "coverage":
            return self._coverage_based_diversity(query, candidates, target_k)
        else:
            raise ValueError(
                f"Unsupported diversity strategy: {self.diversity_strategy}"
            )

    def _maximal_marginal_relevance(
        self, candidates: List[Dict], target_k: int
    ) -> List[Dict]:
        """Implement Maximal Marginal Relevance (MMR) algorithm."""

        if not candidates:
            return []

        # Sort candidates by original relevance score
        candidates_sorted = sorted(
            candidates, key=lambda x: x.get("similarity_score", 0), reverse=True
        )

        selected = [candidates_sorted[0]]  # Start with most relevant
        remaining = candidates_sorted[1:]

        while len(selected) < target_k and remaining:
            best_candidate = None
            best_mmr_score = -1

            for candidate in remaining:
                relevance_score = candidate.get("similarity_score", 0)

                # Calculate maximum similarity to already selected documents
                max_similarity = 0
                for selected_doc in selected:
                    similarity = self._calculate_content_similarity(
                        candidate, selected_doc
                    )
                    max_similarity = max(max_similarity, similarity)

                # MMR score: λ * relevance - (1-λ) * max_similarity
                mmr_score = (
                    self.lambda_param * relevance_score
                    - (1 - self.lambda_param) * max_similarity
                )

                if mmr_score > best_mmr_score:
                    best_mmr_score = mmr_score
                    best_candidate = candidate

            if best_candidate:
                selected.append(best_candidate)
                remaining.remove(best_candidate)
            else:
                break

        # Add diversity metadata
        for i, doc in enumerate(selected):
            doc["rerank_score"] = doc.get("similarity_score", 0)
            doc["diversity_rank"] = i + 1
            doc["reranker"] = "diversity_mmr"

        return selected

    def _cluster_based_diversity(
        self, query: str, candidates: List[Dict], target_k: int
    ) -> List[Dict]:
        """Implement cluster-based diversity selection."""

        # Analyze content themes and clusters
        analysis_input = {
            "query": query,
            "documents": [
                {
                    "id": doc.get("id", f"doc_{i}"),
                    "content": doc.get("content", "")[:500],
                    "score": doc.get("similarity_score", 0),
                }
                for i, doc in enumerate(candidates)
            ],
            "clustering_task": "thematic_clustering",
            "num_clusters": min(target_k, len(candidates) // 2),
        }

        analysis_result = self.diversity_analyzer.process(analysis_input)
        clusters = analysis_result.get("document_clusters", {})

        # Select best document from each cluster
        selected_docs = []
        id_to_doc = {doc.get("id", f"doc_{i}"): doc for i, doc in enumerate(candidates)}

        for cluster_id, doc_ids in clusters.items():
            if len(selected_docs) >= target_k:
                break

            # Find best document in this cluster
            cluster_docs = [
                id_to_doc[doc_id] for doc_id in doc_ids if doc_id in id_to_doc
            ]
            if cluster_docs:
                best_doc = max(cluster_docs, key=lambda x: x.get("similarity_score", 0))
                best_doc["rerank_score"] = best_doc.get("similarity_score", 0)
                best_doc["diversity_cluster"] = cluster_id
                best_doc["reranker"] = "diversity_clustering"
                selected_docs.append(best_doc)

        # Fill remaining slots with highest scoring documents
        remaining_candidates = [doc for doc in candidates if doc not in selected_docs]
        remaining_candidates.sort(
            key=lambda x: x.get("similarity_score", 0), reverse=True
        )

        while len(selected_docs) < target_k and remaining_candidates:
            doc = remaining_candidates.pop(0)
            doc["rerank_score"] = doc.get("similarity_score", 0)
            doc["reranker"] = "diversity_clustering"
            selected_docs.append(doc)

        return selected_docs

    def _coverage_based_diversity(
        self, query: str, candidates: List[Dict], target_k: int
    ) -> List[Dict]:
        """Implement coverage-based diversity selection."""

        # Analyze query aspects and document coverage
        coverage_input = {
            "query": query,
            "documents": [
                {
                    "id": doc.get("id", f"doc_{i}"),
                    "content": doc.get("content", "")[:500],
                    "score": doc.get("similarity_score", 0),
                }
                for i, doc in enumerate(candidates)
            ],
            "coverage_task": "aspect_coverage_analysis",
        }

        coverage_result = self.diversity_analyzer.process(coverage_input)
        query_aspects = coverage_result.get("query_aspects", [])
        document_coverage = coverage_result.get("document_coverage", {})

        # Greedy selection for maximum aspect coverage
        selected_docs = []
        covered_aspects = set()
        id_to_doc = {doc.get("id", f"doc_{i}"): doc for i, doc in enumerate(candidates)}

        # Sort documents by relevance score
        sorted_candidates = sorted(
            candidates, key=lambda x: x.get("similarity_score", 0), reverse=True
        )

        for doc in sorted_candidates:
            if len(selected_docs) >= target_k:
                break

            doc_id = doc.get("id", "")
            doc_aspects = set(document_coverage.get(doc_id, []))

            # Calculate new aspects this document would add
            new_aspects = doc_aspects - covered_aspects

            # Select if it adds new coverage or if we need more documents
            if new_aspects or len(selected_docs) < target_k // 2:
                doc["rerank_score"] = doc.get("similarity_score", 0)
                doc["covered_aspects"] = list(doc_aspects)
                doc["new_aspects"] = list(new_aspects)
                doc["reranker"] = "diversity_coverage"
                selected_docs.append(doc)
                covered_aspects.update(doc_aspects)

        return selected_docs

    def _get_diversity_analysis_prompt(self) -> str:
        """Get prompt for diversity analysis."""
        return """You are a diversity analysis specialist for document collections.

        Analyze documents for thematic diversity and query aspect coverage:

        For clustering tasks:
        - Identify distinct themes and topics
        - Group similar documents together
        - Return document_clusters as {cluster_id: [doc_ids]}

        For coverage tasks:
        - Extract key aspects from the query
        - Identify which aspects each document covers
        - Return query_aspects and document_coverage

        Focus on semantic diversity, topical variety, and comprehensive coverage."""

    def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Process inputs for Kailash workflow integration."""

        query = inputs.get("query", "")
        candidates = inputs.get("candidates", [])
        target_k = inputs.get("target_k", self.top_k)

        if not query or not candidates:
            return {"error": "Query and candidates required", "reranked_results": []}

        reranked_results = self.rerank(query, candidates, target_k)

        return {
            "reranked_results": reranked_results,
            "query": query,
            "reranker_type": f"diversity_{self.diversity_strategy}",
            "num_input": len(candidates),
            "num_output": len(reranked_results),
        }


class MultiStageRerankerNode(BaseRerankerNode):
    """
    Multi-stage reranking pipeline that combines multiple reranking approaches
    in sequence for optimal result quality.
    """

    def __init__(self, name: str = "multi_stage_reranker", **kwargs):
        super().__init__(name, **kwargs)

        self.stages = kwargs.get("stages", [])
        self.stage_configs = kwargs.get("stage_configs", {})
        self.intermediate_k_factors = kwargs.get("intermediate_k_factors", [2.0, 1.5])

        # Initialize reranking stages
        self.reranking_stages = []
        self._initialize_stages()

        logger.info(
            f"MultiStageRerankerNode initialized with {len(self.stages)} stages"
        )

    def _initialize_stages(self):
        """Initialize reranking stages."""

        for i, stage_type in enumerate(self.stages):
            stage_config = self.stage_configs.get(stage_type, {})
            stage_name = f"{self.name}_stage_{i}_{stage_type}"

            if stage_type == "cross_encoder":
                stage = CrossEncoderRerankerNode(name=stage_name, **stage_config)
            elif stage_type == "llm":
                stage = LLMRerankerNode(name=stage_name, **stage_config)
            elif stage_type == "learned":
                stage = LearnedRankerNode(name=stage_name, **stage_config)
            elif stage_type == "diversity":
                stage = DiversityRerankerNode(name=stage_name, **stage_config)
            else:
                logger.warning(f"Unknown stage type: {stage_type}")
                continue

            self.reranking_stages.append((stage_type, stage))

    def add_stage(self, stage_type: str, reranker: BaseRerankerNode):
        """Add a reranking stage to the pipeline."""
        self.stages.append(stage_type)
        self.reranking_stages.append((stage_type, reranker))

    def rerank(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        target_k: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Execute multi-stage reranking pipeline."""

        if target_k is None:
            target_k = self.top_k

        if not candidates or not self.reranking_stages:
            return candidates[:target_k] if candidates else []

        logger.info(
            f"Multi-stage reranking {len(candidates)} candidates through {len(self.reranking_stages)} stages"
        )

        current_candidates = candidates.copy()
        stage_results = {}

        for i, (stage_type, reranker) in enumerate(self.reranking_stages):
            # Calculate intermediate target_k
            if i < len(self.reranking_stages) - 1:  # Not the last stage
                factor = self.intermediate_k_factors[
                    min(i, len(self.intermediate_k_factors) - 1)
                ]
                intermediate_k = int(target_k * factor)
            else:  # Last stage
                intermediate_k = target_k

            logger.info(
                f"Stage {i+1}/{len(self.reranking_stages)} ({stage_type}): {len(current_candidates)} -> {intermediate_k}"
            )

            try:
                # Execute reranking stage
                stage_results[f"stage_{i}_{stage_type}"] = {
                    "input_count": len(current_candidates),
                    "output_count": None,
                    "stage_type": stage_type,
                }

                current_candidates = reranker.rerank(
                    query, current_candidates, intermediate_k
                )

                stage_results[f"stage_{i}_{stage_type}"]["output_count"] = len(
                    current_candidates
                )

                # Add stage tracking to documents
                for doc in current_candidates:
                    if "reranking_stages" not in doc:
                        doc["reranking_stages"] = []
                    doc["reranking_stages"].append(
                        {
                            "stage": i + 1,
                            "type": stage_type,
                            "score": doc.get(
                                "rerank_score", doc.get("similarity_score", 0)
                            ),
                        }
                    )

            except Exception as e:
                logger.error(f"Stage {i+1} ({stage_type}) failed: {str(e)}")
                # Continue with current candidates if stage fails
                continue

        # Final processing
        for doc in current_candidates:
            doc["reranker"] = "multi_stage"
            doc["total_stages"] = len(self.reranking_stages)
            doc["stage_results"] = stage_results

        logger.info(
            f"Multi-stage reranking completed, returning {len(current_candidates)} documents"
        )
        return current_candidates

    def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Process inputs for Kailash workflow integration."""

        query = inputs.get("query", "")
        candidates = inputs.get("candidates", [])
        target_k = inputs.get("target_k", self.top_k)

        if not query or not candidates:
            return {"error": "Query and candidates required", "reranked_results": []}

        reranked_results = self.rerank(query, candidates, target_k)

        return {
            "reranked_results": reranked_results,
            "query": query,
            "reranker_type": "multi_stage",
            "num_stages": len(self.reranking_stages),
            "num_input": len(candidates),
            "num_output": len(reranked_results),
        }
