"""
Advanced Retrieval Nodes for Kailash SDK

State-of-the-art retrieval nodes implementing various retrieval strategies
including dense, sparse, hybrid, graph-based, and fusion approaches.
"""

import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

from kailash.nodes.ai import EmbeddingGeneratorNode, LLMAgentNode
from kailash.nodes.base import Node, NodeParameter
from kailash.nodes.transform import DataTransformer

logger = logging.getLogger(__name__)


class BaseRetrieverNode(Node, ABC):
    """Base class for all retrieval nodes."""

    def __init__(self, name: str, **kwargs):
        # Set attributes before calling super().__init__() as Kailash validates during init
        self.top_k = kwargs.get("top_k", 20)
        self.similarity_threshold = kwargs.get("similarity_threshold", 0.75)
        self.metadata_filters = kwargs.get("metadata_filters", {})
        super().__init__(name=name)

    @abstractmethod
    def retrieve(self, query: str, top_k: Optional[int] = None) -> List[Dict[str, Any]]:
        """Retrieve relevant documents for the given query."""
        pass

    def _apply_metadata_filters(
        self, documents: List[Dict], filters: Dict
    ) -> List[Dict]:
        """Apply metadata filters to retrieved documents."""
        if not filters:
            return documents

        filtered = []
        for doc in documents:
            metadata = doc.get("metadata", {})
            include = True

            for key, value in filters.items():
                if key not in metadata or metadata[key] != value:
                    include = False
                    break

            if include:
                filtered.append(doc)

        return filtered


class DenseRetrieverNode(BaseRetrieverNode):
    """
    Dense retrieval using vector embeddings and similarity search.

    Supports multiple embedding models and similarity metrics.
    """

    def __init__(self, name: str = "dense_retriever", **kwargs):
        # Set attributes before calling super().__init__() as Kailash validates during init
        self.embedding_model = kwargs.get("embedding_model", "text-embedding-3-small")
        self.similarity_metric = kwargs.get("similarity_metric", "cosine")
        self.batch_size = kwargs.get("batch_size", 100)

        super().__init__(name, **kwargs)

        # Initialize embedding generator
        self.embedder = EmbeddingGeneratorNode(
            name=f"{name}_embedder",
            model=self.embedding_model,
            batch_size=self.batch_size,
        )

        # Document embeddings storage (in production, use vector database)
        self.document_embeddings = {}
        self.documents = {}

        logger.info(f"DenseRetrieverNode initialized with {self.embedding_model}")

    def index_documents(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Index documents by generating embeddings."""

        logger.info(f"Indexing {len(documents)} documents")

        # Extract text content for embedding
        texts = []
        doc_ids = []

        for doc in documents:
            doc_id = doc.get("id", f"doc_{len(self.documents)}")
            content = doc.get("content", "")

            if not content:
                continue

            texts.append(content)
            doc_ids.append(doc_id)
            self.documents[doc_id] = doc

        # Generate embeddings
        embeddings_result = self.embedder.run(
            operation="embed_batch",
            provider="ollama",
            model="nomic-embed-text",
            input_texts=texts,
        )
        embedding_dicts = embeddings_result.get("embeddings", [])

        # Extract actual embedding vectors from the dictionaries
        embeddings = []
        for embedding_dict in embedding_dicts:
            if isinstance(embedding_dict, dict) and "embedding" in embedding_dict:
                # Extract the actual vector from the dictionary
                vector = embedding_dict["embedding"]
                embeddings.append(vector)
            elif isinstance(embedding_dict, list):
                # Already a vector
                embeddings.append(embedding_dict)
            else:
                # Fallback for unexpected format
                embeddings.append([0.0] * 768)  # Ollama nomic-embed-text dimension

        # Store embeddings
        for doc_id, embedding in zip(doc_ids, embeddings):
            self.document_embeddings[doc_id] = embedding

        logger.info(f"Indexed {len(embeddings)} document embeddings")

        return {
            "indexed_documents": len(embeddings),
            "total_documents": len(self.documents),
            "embedding_dimension": len(embeddings[0]) if embeddings else 0,
        }

    def retrieve(self, query: str, top_k: Optional[int] = None) -> List[Dict[str, Any]]:
        """Retrieve documents using dense vector similarity."""

        if top_k is None:
            top_k = self.top_k

        # Generate query embedding
        query_result = self.embedder.run(
            operation="embed_batch",
            provider="ollama",
            model="nomic-embed-text",
            input_texts=[query],
        )
        embedding_dicts = query_result.get("embeddings", [])
        query_embedding = None

        if embedding_dicts:
            embedding_dict = embedding_dicts[0]
            if isinstance(embedding_dict, dict) and "embedding" in embedding_dict:
                query_embedding = embedding_dict["embedding"]
            elif isinstance(embedding_dict, list):
                query_embedding = embedding_dict
            else:
                query_embedding = None

        if query_embedding is None:
            logger.error("Failed to generate query embedding")
            return []

        # Calculate similarities
        similarities = []
        for doc_id, doc_embedding in self.document_embeddings.items():
            similarity = self._calculate_similarity(query_embedding, doc_embedding)

            if similarity >= self.similarity_threshold:
                similarities.append((doc_id, similarity))

        # Sort by similarity and get top-k
        similarities.sort(key=lambda x: x[1], reverse=True)
        top_similarities = similarities[:top_k]

        # Build result documents
        results = []
        for doc_id, similarity in top_similarities:
            doc = self.documents[doc_id].copy()
            doc["similarity_score"] = similarity
            doc["retrieval_method"] = "dense_vector"
            results.append(doc)

        logger.info(f"Retrieved {len(results)} documents for query")
        return results

    def _calculate_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate similarity between two vectors."""

        if self.similarity_metric == "cosine":
            return self._cosine_similarity(vec1, vec2)
        elif self.similarity_metric == "dot_product":
            return np.dot(vec1, vec2)
        elif self.similarity_metric == "euclidean":
            return 1.0 / (1.0 + np.linalg.norm(np.array(vec1) - np.array(vec2)))
        else:
            raise ValueError(f"Unsupported similarity metric: {self.similarity_metric}")

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        vec1_np = np.array(vec1)
        vec2_np = np.array(vec2)

        norm1 = np.linalg.norm(vec1_np)
        norm2 = np.linalg.norm(vec2_np)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return np.dot(vec1_np, vec2_np) / (norm1 * norm2)

    def get_parameters(self) -> Dict[str, NodeParameter]:
        """Get node parameters for Kailash framework."""
        return {
            "query": NodeParameter(
                name="query",
                type=str,
                required=True,
                description="Query text for dense retrieval",
            ),
            "top_k": NodeParameter(
                name="top_k",
                type=int,
                required=False,
                default=self.top_k,
                description="Number of top results to return",
            ),
            "similarity_threshold": NodeParameter(
                name="similarity_threshold",
                type=float,
                required=False,
                default=self.similarity_threshold,
                description="Minimum similarity threshold",
            ),
        }

    def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Run method required by Kailash Node interface."""
        return self.process(inputs)

    def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Process inputs for Kailash workflow integration."""

        query = inputs.get("query", "")
        top_k = inputs.get("top_k", self.top_k)

        if not query:
            return {"error": "No query provided", "results": []}

        results = self.retrieve(query, top_k)

        return {
            "results": results,
            "query": query,
            "retrieval_method": "dense_vector",
            "num_results": len(results),
        }


class SparseRetrieverNode(BaseRetrieverNode):
    """
    Sparse retrieval using BM25 and learned sparse representations.

    Supports traditional BM25 and modern learned sparse methods like SPLADE.
    """

    def __init__(self, name: str = "sparse_retriever", **kwargs):
        # Set attributes before calling super().__init__() as Kailash validates during init
        self.method = kwargs.get("method", "bm25")  # "bm25" or "splade"
        self.k1 = kwargs.get("k1", 1.2)  # BM25 parameter
        self.b = kwargs.get("b", 0.75)  # BM25 parameter

        super().__init__(name, **kwargs)

        # Document storage and statistics
        self.documents = {}
        self.term_frequencies = {}
        self.document_frequencies = {}
        self.total_documents = 0
        self.avg_doc_length = 0

        # For learned sparse methods
        if self.method == "splade":
            self.sparse_encoder = LLMAgentNode(
                name=f"{name}_sparse_encoder",
                model="gpt-4o-mini",
                system_prompt=self._get_sparse_encoding_prompt(),
            )

        logger.info(f"SparseRetrieverNode initialized with {self.method}")

    def index_documents(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Index documents for sparse retrieval."""

        logger.info(f"Indexing {len(documents)} documents for sparse retrieval")

        total_length = 0

        for doc in documents:
            doc_id = doc.get("id", f"doc_{len(self.documents)}")
            content = doc.get("content", "")

            if not content:
                continue

            self.documents[doc_id] = doc

            # Tokenize and count terms
            terms = self._tokenize(content)
            doc_length = len(terms)
            total_length += doc_length

            # Calculate term frequencies for this document
            tf_dict = {}
            for term in terms:
                tf_dict[term] = tf_dict.get(term, 0) + 1

            self.term_frequencies[doc_id] = tf_dict

            # Update document frequencies
            for term in set(terms):
                self.document_frequencies[term] = (
                    self.document_frequencies.get(term, 0) + 1
                )

        self.total_documents = len(self.documents)
        self.avg_doc_length = (
            total_length / self.total_documents if self.total_documents > 0 else 0
        )

        logger.info(
            f"Indexed {self.total_documents} documents, avg length: {self.avg_doc_length:.1f}"
        )

        return {
            "indexed_documents": self.total_documents,
            "unique_terms": len(self.document_frequencies),
            "avg_document_length": self.avg_doc_length,
        }

    def retrieve(self, query: str, top_k: Optional[int] = None) -> List[Dict[str, Any]]:
        """Retrieve documents using sparse methods."""

        if top_k is None:
            top_k = self.top_k

        if self.method == "bm25":
            return self._bm25_retrieve(query, top_k)
        elif self.method == "splade":
            return self._splade_retrieve(query, top_k)
        else:
            raise ValueError(f"Unsupported sparse method: {self.method}")

    def _bm25_retrieve(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """Retrieve using BM25 algorithm."""

        query_terms = self._tokenize(query)
        scores = {}

        for doc_id in self.documents:
            score = 0.0
            doc_tf = self.term_frequencies[doc_id]
            doc_length = sum(doc_tf.values())

            for term in query_terms:
                if term in doc_tf:
                    tf = doc_tf[term]
                    df = self.document_frequencies.get(term, 0)

                    if df > 0:
                        idf = np.log((self.total_documents - df + 0.5) / (df + 0.5))

                        # BM25 formula
                        numerator = tf * (self.k1 + 1)
                        denominator = tf + self.k1 * (
                            1 - self.b + self.b * (doc_length / self.avg_doc_length)
                        )

                        score += idf * (numerator / denominator)

            if score > 0:
                scores[doc_id] = score

        # Sort and get top-k
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]

        # Build results
        results = []
        for doc_id, score in sorted_scores:
            if score >= self.similarity_threshold:
                doc = self.documents[doc_id].copy()
                doc["similarity_score"] = score
                doc["retrieval_method"] = "bm25"
                results.append(doc)

        return results

    def _splade_retrieve(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """Retrieve using SPLADE-like learned sparse representations."""

        # Generate sparse representation for query
        query_sparse = self.sparse_encoder.run(
            provider="ollama",
            model="llama3.2:3b",
            messages=[
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "text": query,
                            "task": "generate_sparse_representation",
                            "output_format": "term_weights",
                        }
                    ),
                }
            ],
        )

        query_weights = query_sparse.get("term_weights", {})

        # Calculate similarity with all documents
        scores = {}
        for doc_id in self.documents:
            # Generate sparse representation for document (cached in practice)
            doc_sparse = self.sparse_encoder.run(
                provider="ollama",
                model="llama3.2:3b",
                messages=[
                    {
                        "role": "user",
                        "content": json.dumps(
                            {
                                "text": self.documents[doc_id].get("content", ""),
                                "task": "generate_sparse_representation",
                                "output_format": "term_weights",
                            }
                        ),
                    }
                ],
            )

            doc_weights = doc_sparse.get("term_weights", {})

            # Calculate sparse similarity (e.g., weighted dot product)
            similarity = self._sparse_similarity(query_weights, doc_weights)

            if similarity >= self.similarity_threshold:
                scores[doc_id] = similarity

        # Sort and build results
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]

        results = []
        for doc_id, score in sorted_scores:
            doc = self.documents[doc_id].copy()
            doc["similarity_score"] = score
            doc["retrieval_method"] = "splade"
            results.append(doc)

        return results

    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization (in practice, use proper tokenizer)."""
        return text.lower().split()

    def _sparse_similarity(
        self, weights1: Dict[str, float], weights2: Dict[str, float]
    ) -> float:
        """Calculate similarity between sparse representations."""

        common_terms = set(weights1.keys()) & set(weights2.keys())

        if not common_terms:
            return 0.0

        # Weighted dot product
        similarity = sum(weights1[term] * weights2[term] for term in common_terms)

        # Normalize by magnitude (optional)
        norm1 = np.sqrt(sum(w**2 for w in weights1.values()))
        norm2 = np.sqrt(sum(w**2 for w in weights2.values()))

        if norm1 > 0 and norm2 > 0:
            similarity = similarity / (norm1 * norm2)

        return similarity

    def _get_sparse_encoding_prompt(self) -> str:
        """Get prompt for sparse encoding."""
        return """You are a sparse representation encoder for text retrieval.

        Generate sparse term weights that capture the most important terms
        for retrieval purposes. Focus on:
        - Key concepts and entities
        - Technical terms and domain vocabulary
        - Important semantic indicators

        Return JSON with term_weights as a dictionary of term -> weight."""

    def get_parameters(self) -> Dict[str, NodeParameter]:
        """Get node parameters for Kailash framework."""
        return {
            "query": NodeParameter(
                name="query",
                type=str,
                required=True,
                description="Query text for sparse retrieval",
            ),
            "top_k": NodeParameter(
                name="top_k",
                type=int,
                required=False,
                default=self.top_k,
                description="Number of top results to return",
            ),
            "method": NodeParameter(
                name="method",
                type=str,
                required=False,
                default=self.method,
                description="Sparse retrieval method (bm25 or splade)",
            ),
        }

    def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Run method required by Kailash Node interface."""
        return self.process(inputs)

    def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Process inputs for Kailash workflow integration."""

        query = inputs.get("query", "")
        top_k = inputs.get("top_k", self.top_k)

        if not query:
            return {"error": "No query provided", "results": []}

        results = self.retrieve(query, top_k)

        return {
            "results": results,
            "query": query,
            "retrieval_method": f"sparse_{self.method}",
            "num_results": len(results),
        }


class HybridRetrieverNode(BaseRetrieverNode):
    """
    Hybrid retrieval combining dense and sparse methods with intelligent fusion.

    Supports multiple fusion strategies including RRF, linear combination,
    and learned fusion weights.
    """

    def __init__(self, name: str = "hybrid_retriever", **kwargs):
        # Set attributes before calling super().__init__() as Kailash validates during init
        self.fusion_strategy = kwargs.get(
            "fusion_strategy", "rrf"
        )  # "rrf", "linear", "learned"
        self.dense_weight = kwargs.get("dense_weight", 0.6)
        self.sparse_weight = kwargs.get("sparse_weight", 0.4)
        self.rrf_k = kwargs.get("rrf_k", 60)

        super().__init__(name, **kwargs)

        # Initialize component retrievers
        self.dense_retriever = DenseRetrieverNode(
            name=f"{name}_dense", **kwargs.get("dense_config", {})
        )

        self.sparse_retriever = SparseRetrieverNode(
            name=f"{name}_sparse", **kwargs.get("sparse_config", {})
        )

        # For learned fusion
        if self.fusion_strategy == "learned":
            self.fusion_model = LLMAgentNode(
                name=f"{name}_fusion",
                model="gpt-4o-mini",
                system_prompt=self._get_fusion_prompt(),
            )

        logger.info(
            f"HybridRetrieverNode initialized with {self.fusion_strategy} fusion"
        )

    def index_documents(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Index documents in both dense and sparse retrievers."""

        logger.info("Indexing documents in hybrid retriever")

        dense_result = self.dense_retriever.index_documents(documents)
        sparse_result = self.sparse_retriever.index_documents(documents)

        return {
            "dense_indexing": dense_result,
            "sparse_indexing": sparse_result,
            "total_documents": dense_result.get("indexed_documents", 0),
        }

    def retrieve(self, query: str, top_k: Optional[int] = None) -> List[Dict[str, Any]]:
        """Retrieve using hybrid fusion of dense and sparse methods."""

        if top_k is None:
            top_k = self.top_k

        # Retrieve from both methods
        dense_results = self.dense_retriever.retrieve(
            query, top_k * 2
        )  # Get more for fusion
        sparse_results = self.sparse_retriever.retrieve(query, top_k * 2)

        # Fuse results
        if self.fusion_strategy == "rrf":
            fused_results = self._reciprocal_rank_fusion(
                dense_results, sparse_results, top_k
            )
        elif self.fusion_strategy == "linear":
            fused_results = self._linear_fusion(dense_results, sparse_results, top_k)
        elif self.fusion_strategy == "learned":
            fused_results = self._learned_fusion(
                query, dense_results, sparse_results, top_k
            )
        else:
            raise ValueError(f"Unsupported fusion strategy: {self.fusion_strategy}")

        logger.info(f"Hybrid retrieval returned {len(fused_results)} documents")
        return fused_results

    def _reciprocal_rank_fusion(
        self, dense_results: List[Dict], sparse_results: List[Dict], top_k: int
    ) -> List[Dict]:
        """Implement Reciprocal Rank Fusion (RRF)."""

        # Create rank mappings
        dense_ranks = {doc["id"]: i + 1 for i, doc in enumerate(dense_results)}
        sparse_ranks = {doc["id"]: i + 1 for i, doc in enumerate(sparse_results)}

        # Collect all unique document IDs
        all_doc_ids = set(dense_ranks.keys()) | set(sparse_ranks.keys())

        # Calculate RRF scores
        rrf_scores = {}
        for doc_id in all_doc_ids:
            score = 0

            if doc_id in dense_ranks:
                score += 1 / (self.rrf_k + dense_ranks[doc_id])

            if doc_id in sparse_ranks:
                score += 1 / (self.rrf_k + sparse_ranks[doc_id])

            rrf_scores[doc_id] = score

        # Sort by RRF score and get top-k
        sorted_docs = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)[
            :top_k
        ]

        # Build result documents
        doc_map = {}
        for doc in dense_results + sparse_results:
            doc_map[doc["id"]] = doc

        results = []
        for doc_id, rrf_score in sorted_docs:
            if doc_id in doc_map:
                doc = doc_map[doc_id].copy()
                doc["similarity_score"] = rrf_score
                doc["retrieval_method"] = "hybrid_rrf"
                results.append(doc)

        return results

    def _linear_fusion(
        self, dense_results: List[Dict], sparse_results: List[Dict], top_k: int
    ) -> List[Dict]:
        """Implement linear combination fusion."""

        # Normalize scores to 0-1 range
        dense_scores = [doc["similarity_score"] for doc in dense_results]
        sparse_scores = [doc["similarity_score"] for doc in sparse_results]

        dense_max = max(dense_scores) if dense_scores else 1.0
        sparse_max = max(sparse_scores) if sparse_scores else 1.0

        # Create score mappings
        dense_score_map = {
            doc["id"]: doc["similarity_score"] / dense_max for doc in dense_results
        }
        sparse_score_map = {
            doc["id"]: doc["similarity_score"] / sparse_max for doc in sparse_results
        }

        # Collect all unique document IDs
        all_doc_ids = set(dense_score_map.keys()) | set(sparse_score_map.keys())

        # Calculate linear combination scores
        linear_scores = {}
        for doc_id in all_doc_ids:
            dense_score = dense_score_map.get(doc_id, 0)
            sparse_score = sparse_score_map.get(doc_id, 0)

            combined_score = (
                self.dense_weight * dense_score + self.sparse_weight * sparse_score
            )
            linear_scores[doc_id] = combined_score

        # Sort and build results
        sorted_docs = sorted(linear_scores.items(), key=lambda x: x[1], reverse=True)[
            :top_k
        ]

        # Build result documents
        doc_map = {}
        for doc in dense_results + sparse_results:
            doc_map[doc["id"]] = doc

        results = []
        for doc_id, combined_score in sorted_docs:
            if doc_id in doc_map:
                doc = doc_map[doc_id].copy()
                doc["similarity_score"] = combined_score
                doc["retrieval_method"] = "hybrid_linear"
                results.append(doc)

        return results

    def _learned_fusion(
        self,
        query: str,
        dense_results: List[Dict],
        sparse_results: List[Dict],
        top_k: int,
    ) -> List[Dict]:
        """Implement learned fusion using LLM."""

        fusion_input = {
            "query": query,
            "dense_results": [
                {
                    "id": doc["id"],
                    "score": doc["similarity_score"],
                    "content_preview": doc.get("content", "")[:200],
                }
                for doc in dense_results[:10]
            ],
            "sparse_results": [
                {
                    "id": doc["id"],
                    "score": doc["similarity_score"],
                    "content_preview": doc.get("content", "")[:200],
                }
                for doc in sparse_results[:10]
            ],
            "fusion_task": "intelligent_ranking",
        }

        fusion_result = self.fusion_model.run(
            provider="ollama",
            model="llama3.2:3b",
            messages=[{"role": "user", "content": json.dumps(fusion_input)}],
        )
        ranked_ids = fusion_result.get("ranked_document_ids", [])

        # Build result documents
        doc_map = {}
        for doc in dense_results + sparse_results:
            doc_map[doc["id"]] = doc

        results = []
        for i, doc_id in enumerate(ranked_ids[:top_k]):
            if doc_id in doc_map:
                doc = doc_map[doc_id].copy()
                doc["similarity_score"] = 1.0 - (
                    i / len(ranked_ids)
                )  # Rank-based score
                doc["retrieval_method"] = "hybrid_learned"
                results.append(doc)

        return results

    def _get_fusion_prompt(self) -> str:
        """Get prompt for learned fusion."""
        return """You are an intelligent document ranking system for hybrid retrieval.

        Given a query and results from both dense and sparse retrieval methods,
        intelligently rank the documents by considering:
        - Query relevance from both semantic and lexical perspectives
        - Document quality and completeness
        - Complementary strengths of both retrieval methods

        Return ranked_document_ids as a list of document IDs in order of relevance."""

    def get_parameters(self) -> Dict[str, NodeParameter]:
        """Get node parameters for Kailash framework."""
        return {
            "query": NodeParameter(
                name="query",
                type=str,
                required=True,
                description="Query text for hybrid retrieval",
            ),
            "top_k": NodeParameter(
                name="top_k",
                type=int,
                required=False,
                default=self.top_k,
                description="Number of top results to return",
            ),
            "fusion_strategy": NodeParameter(
                name="fusion_strategy",
                type=str,
                required=False,
                default=self.fusion_strategy,
                description="Fusion strategy (rrf, linear, learned)",
            ),
        }

    def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Run method required by Kailash Node interface."""
        return self.process(inputs)

    def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Process inputs for Kailash workflow integration."""

        query = inputs.get("query", "")
        top_k = inputs.get("top_k", self.top_k)

        if not query:
            return {"error": "No query provided", "results": []}

        results = self.retrieve(query, top_k)

        return {
            "results": results,
            "query": query,
            "retrieval_method": f"hybrid_{self.fusion_strategy}",
            "num_results": len(results),
        }


class GraphRetrieverNode(BaseRetrieverNode):
    """
    Graph-based retrieval using knowledge graphs and relationship traversal.

    Implements graph algorithms for relationship-aware document retrieval.
    """

    def __init__(self, name: str = "graph_retriever", **kwargs):
        super().__init__(name, **kwargs)

        self.max_hops = kwargs.get("max_hops", 3)
        self.traversal_strategy = kwargs.get("traversal_strategy", "breadth_first")
        self.relationship_weight = kwargs.get("relationship_weight", 0.8)

        # Knowledge graph storage (in practice, use graph database)
        self.entities = {}
        self.relationships = {}
        self.document_entities = {}

        # Entity extraction LLM
        self.entity_extractor = LLMAgentNode(
            name=f"{name}_entity_extractor",
            model="gpt-4o-mini",
            system_prompt=self._get_entity_extraction_prompt(),
        )

        logger.info(
            f"GraphRetrieverNode initialized with {self.traversal_strategy} traversal"
        )

    def index_documents(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Index documents by extracting entities and relationships."""

        logger.info(f"Building knowledge graph from {len(documents)} documents")

        total_entities = 0
        total_relationships = 0

        for doc in documents:
            doc_id = doc.get("id", f"doc_{len(self.document_entities)}")
            content = doc.get("content", "")

            if not content:
                continue

            # Extract entities and relationships
            extraction_result = self.entity_extractor.run(
                provider="ollama",
                model="llama3.2:3b",
                messages=[
                    {
                        "role": "user",
                        "content": json.dumps(
                            {
                                "text": content,
                                "extraction_task": "entities_and_relationships",
                                "document_id": doc_id,
                            }
                        ),
                    }
                ],
            )

            entities = extraction_result.get("entities", [])
            relationships = extraction_result.get("relationships", [])

            # Store entities
            doc_entities = []
            for entity in entities:
                entity_id = entity.get("id", entity.get("name", ""))
                if entity_id:
                    self.entities[entity_id] = entity
                    doc_entities.append(entity_id)
                    total_entities += 1

            self.document_entities[doc_id] = doc_entities

            # Store relationships
            for rel in relationships:
                rel_id = f"{rel.get('source', '')}_{rel.get('relation', '')}_{rel.get('target', '')}"
                self.relationships[rel_id] = rel
                total_relationships += 1

        logger.info(
            f"Built knowledge graph: {total_entities} entities, {total_relationships} relationships"
        )

        return {
            "indexed_documents": len(self.document_entities),
            "total_entities": total_entities,
            "total_relationships": total_relationships,
        }

    def retrieve(self, query: str, top_k: Optional[int] = None) -> List[Dict[str, Any]]:
        """Retrieve documents using graph traversal."""

        if top_k is None:
            top_k = self.top_k

        # Extract entities from query
        query_extraction = self.entity_extractor.run(
            provider="ollama",
            model="llama3.2:3b",
            messages=[
                {
                    "role": "user",
                    "content": json.dumps(
                        {"text": query, "extraction_task": "entities_only"}
                    ),
                }
            ],
        )

        query_entities = query_extraction.get("entities", [])

        if not query_entities:
            logger.warning("No entities extracted from query")
            return []

        # Find entry points in the graph
        entry_points = []
        for entity in query_entities:
            entity_id = entity.get("id", entity.get("name", ""))
            if entity_id in self.entities:
                entry_points.append(entity_id)

        if not entry_points:
            logger.warning("No query entities found in knowledge graph")
            return []

        # Perform graph traversal
        relevant_entities = self._graph_traversal(entry_points)

        # Find documents containing relevant entities
        doc_scores = {}
        for doc_id, doc_entities in self.document_entities.items():
            score = 0
            for entity_id in doc_entities:
                if entity_id in relevant_entities:
                    # Score based on entity relevance and hop distance
                    entity_score = relevant_entities[entity_id]
                    score += entity_score

            if score > 0:
                doc_scores[doc_id] = score

        # Sort and get top-k documents
        sorted_docs = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)[
            :top_k
        ]

        # Build results (documents need to be stored separately)
        results = []
        for doc_id, score in sorted_docs:
            if score >= self.similarity_threshold:
                # In practice, retrieve full document from storage
                doc = {
                    "id": doc_id,
                    "similarity_score": score,
                    "retrieval_method": "graph_traversal",
                    "relevant_entities": [
                        e
                        for e in self.document_entities[doc_id]
                        if e in relevant_entities
                    ],
                }
                results.append(doc)

        logger.info(f"Graph retrieval returned {len(results)} documents")
        return results

    def _graph_traversal(self, entry_points: List[str]) -> Dict[str, float]:
        """Perform graph traversal to find relevant entities."""

        visited = {}
        queue = [
            (entity_id, 0, 1.0) for entity_id in entry_points
        ]  # (entity, hop, score)

        # Initialize entry points
        for entity_id in entry_points:
            visited[entity_id] = 1.0

        while queue:
            current_entity, hop_count, current_score = queue.pop(0)

            if hop_count >= self.max_hops:
                continue

            # Find connected entities
            connected_entities = self._find_connected_entities(current_entity)

            for connected_entity, relationship_strength in connected_entities:
                new_score = (
                    current_score * self.relationship_weight * relationship_strength
                )

                # Only visit if we haven't seen this entity or found a better path
                if (
                    connected_entity not in visited
                    or visited[connected_entity] < new_score
                ):

                    visited[connected_entity] = new_score
                    queue.append((connected_entity, hop_count + 1, new_score))

        return visited

    def _find_connected_entities(self, entity_id: str) -> List[Tuple[str, float]]:
        """Find entities connected to the given entity."""

        connected = []

        for rel_id, relationship in self.relationships.items():
            source = relationship.get("source", "")
            target = relationship.get("target", "")
            strength = relationship.get("strength", 1.0)

            # Bidirectional relationships
            if source == entity_id and target != entity_id:
                connected.append((target, strength))
            elif target == entity_id and source != entity_id:
                connected.append((source, strength))

        return connected

    def _get_entity_extraction_prompt(self) -> str:
        """Get prompt for entity and relationship extraction."""
        return """You are an expert knowledge graph extractor for technical documents.

        Extract entities and relationships from the given text:

        Entities should include:
        - Organizations, people, technologies
        - Concepts, methods, processes
        - Products, systems, standards

        Relationships should capture:
        - Uses, implements, requires
        - Part-of, type-of, related-to
        - Causes, enables, improves

        Return JSON with:
        - entities: [{id, name, type, description}]
        - relationships: [{source, relation, target, strength}]"""

    def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Process inputs for Kailash workflow integration."""

        query = inputs.get("query", "")
        top_k = inputs.get("top_k", self.top_k)

        if not query:
            return {"error": "No query provided", "results": []}

        results = self.retrieve(query, top_k)

        return {
            "results": results,
            "query": query,
            "retrieval_method": "graph_traversal",
            "num_results": len(results),
        }


class FusionRetrieverNode(BaseRetrieverNode):
    """
    Advanced fusion retriever that combines multiple retrieval methods
    with intelligent orchestration and adaptive weighting.
    """

    def __init__(self, name: str = "fusion_retriever", **kwargs):
        super().__init__(name, **kwargs)

        self.fusion_strategy = kwargs.get("fusion_strategy", "adaptive_weighted")
        self.retrievers = kwargs.get("retrievers", [])
        self.weights = kwargs.get("weights", {})

        # Initialize fusion orchestrator
        self.fusion_orchestrator = LLMAgentNode(
            name=f"{name}_orchestrator",
            model="gpt-4o",
            system_prompt=self._get_fusion_orchestrator_prompt(),
        )

        logger.info(
            f"FusionRetrieverNode initialized with {len(self.retrievers)} retrievers"
        )

    def add_retriever(self, retriever: BaseRetrieverNode, weight: float = 1.0):
        """Add a retriever to the fusion ensemble."""
        self.retrievers.append(retriever)
        self.weights[retriever.name] = weight

    def retrieve(self, query: str, top_k: Optional[int] = None) -> List[Dict[str, Any]]:
        """Retrieve using fusion of multiple methods."""

        if top_k is None:
            top_k = self.top_k

        if not self.retrievers:
            logger.error("No retrievers configured for fusion")
            return []

        # Collect results from all retrievers
        all_results = {}
        for retriever in self.retrievers:
            try:
                results = retriever.retrieve(query, top_k * 2)  # Get more for fusion
                all_results[retriever.name] = results
            except Exception as e:
                logger.error(f"Retriever {retriever.name} failed: {str(e)}")
                all_results[retriever.name] = []

        # Intelligent fusion based on strategy
        if self.fusion_strategy == "adaptive_weighted":
            fused_results = self._adaptive_weighted_fusion(query, all_results, top_k)
        elif self.fusion_strategy == "voting":
            fused_results = self._voting_fusion(all_results, top_k)
        elif self.fusion_strategy == "cascade":
            fused_results = self._cascade_fusion(query, all_results, top_k)
        else:
            raise ValueError(f"Unsupported fusion strategy: {self.fusion_strategy}")

        return fused_results

    def _adaptive_weighted_fusion(
        self, query: str, all_results: Dict[str, List[Dict]], top_k: int
    ) -> List[Dict]:
        """Adaptive weighted fusion based on query characteristics."""

        # Analyze query to determine optimal weights
        query_analysis = self.fusion_orchestrator.run(
            provider="ollama",
            model="llama3.2:3b",
            messages=[
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "query": query,
                            "task": "query_analysis",
                            "available_retrievers": list(all_results.keys()),
                            "retriever_strengths": {
                                "dense_retriever": "semantic similarity, concept matching",
                                "sparse_retriever": "keyword matching, exact terms",
                                "graph_retriever": "relationship traversal, entity connections",
                                "hybrid_retriever": "balanced approach",
                            },
                        }
                    ),
                }
            ],
        )

        adaptive_weights = query_analysis.get("optimal_weights", self.weights)

        # Weighted fusion of results
        doc_scores = {}

        for retriever_name, results in all_results.items():
            weight = adaptive_weights.get(
                retriever_name, self.weights.get(retriever_name, 1.0)
            )

            for i, doc in enumerate(results):
                doc_id = doc.get("id", "")
                if not doc_id:
                    continue

                # Combine rank-based and score-based weighting
                rank_score = 1.0 / (i + 1)  # Reciprocal rank
                original_score = doc.get("similarity_score", 0)

                combined_score = weight * (0.7 * original_score + 0.3 * rank_score)

                if doc_id in doc_scores:
                    doc_scores[doc_id]["score"] += combined_score
                    doc_scores[doc_id]["retriever_votes"].append(retriever_name)
                else:
                    doc_scores[doc_id] = {
                        "score": combined_score,
                        "document": doc,
                        "retriever_votes": [retriever_name],
                    }

        # Sort and build final results
        sorted_docs = sorted(
            doc_scores.items(), key=lambda x: x[1]["score"], reverse=True
        )[:top_k]

        results = []
        for doc_id, doc_data in sorted_docs:
            doc = doc_data["document"].copy()
            doc["similarity_score"] = doc_data["score"]
            doc["retrieval_method"] = "adaptive_fusion"
            doc["contributing_retrievers"] = doc_data["retriever_votes"]
            doc["fusion_confidence"] = len(doc_data["retriever_votes"]) / len(
                self.retrievers
            )
            results.append(doc)

        return results

    def _get_fusion_orchestrator_prompt(self) -> str:
        """Get prompt for fusion orchestrator."""
        return """You are an intelligent fusion orchestrator for multi-modal retrieval.

        Analyze queries and determine optimal weights for different retrieval methods:
        - Dense retrieval: Best for semantic similarity and concept matching
        - Sparse retrieval: Best for keyword matching and exact terms
        - Graph retrieval: Best for relationship-aware and entity-based queries
        - Hybrid methods: Balanced approaches

        For each query, return optimal_weights as a dictionary mapping
        retriever names to weight values (0.0 to 1.0).

        Consider query characteristics:
        - Technical vs. conceptual queries
        - Specific vs. broad queries
        - Entity-focused vs. relationship-focused queries"""

    def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Process inputs for Kailash workflow integration."""

        query = inputs.get("query", "")
        top_k = inputs.get("top_k", self.top_k)

        if not query:
            return {"error": "No query provided", "results": []}

        results = self.retrieve(query, top_k)

        return {
            "results": results,
            "query": query,
            "retrieval_method": f"fusion_{self.fusion_strategy}",
            "num_results": len(results),
            "num_retrievers": len(self.retrievers),
        }


class AgenticRetrieverNode(BaseRetrieverNode):
    """
    Agentic retriever that dynamically selects and adapts retrieval strategies
    based on query analysis and context.
    """

    def __init__(self, name: str = "agentic_retriever", **kwargs):
        super().__init__(name, **kwargs)

        # Available retrieval strategies
        self.available_retrievers = kwargs.get("available_retrievers", {})
        self.strategy_history = []

        # Agentic components
        self.strategy_agent = LLMAgentNode(
            name=f"{name}_strategy_agent",
            model="gpt-4o",
            system_prompt=self._get_strategy_selection_prompt(),
        )

        self.adaptation_agent = LLMAgentNode(
            name=f"{name}_adaptation_agent",
            model="gpt-4o-mini",
            system_prompt=self._get_adaptation_prompt(),
        )

        logger.info(
            f"AgenticRetrieverNode initialized with {len(self.available_retrievers)} strategies"
        )

    def add_retriever_strategy(
        self, name: str, retriever: BaseRetrieverNode, characteristics: Dict[str, Any]
    ):
        """Add a retrieval strategy with its characteristics."""
        self.available_retrievers[name] = {
            "retriever": retriever,
            "characteristics": characteristics,
            "performance_history": [],
        }

    def retrieve(self, query: str, top_k: Optional[int] = None) -> List[Dict[str, Any]]:
        """Retrieve using intelligent strategy selection."""

        if top_k is None:
            top_k = self.top_k

        # Analyze query and select optimal strategy
        strategy_selection = self.strategy_agent.run(
            provider="ollama",
            model="llama3.2:3b",
            messages=[
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "query": query,
                            "available_strategies": {
                                name: info["characteristics"]
                                for name, info in self.available_retrievers.items()
                            },
                            "performance_history": self.strategy_history[
                                -10:
                            ],  # Recent history
                            "task": "strategy_selection",
                        }
                    ),
                }
            ],
        )

        selected_strategies = strategy_selection.get("selected_strategies", [])

        if not selected_strategies:
            logger.warning("No strategies selected, using default")
            selected_strategies = [list(self.available_retrievers.keys())[0]]

        # Execute selected strategies
        strategy_results = {}
        for strategy_name in selected_strategies:
            if strategy_name in self.available_retrievers:
                retriever = self.available_retrievers[strategy_name]["retriever"]
                try:
                    results = retriever.retrieve(query, top_k)
                    strategy_results[strategy_name] = results
                except Exception as e:
                    logger.error(f"Strategy {strategy_name} failed: {str(e)}")

        # Adaptive result combination
        if len(strategy_results) == 1:
            final_results = list(strategy_results.values())[0]
        else:
            adaptation_result = self.adaptation_agent.run(
                provider="ollama",
                model="llama3.2:3b",
                messages=[
                    {
                        "role": "user",
                        "content": json.dumps(
                            {
                                "query": query,
                                "strategy_results": strategy_results,
                                "task": "result_adaptation",
                                "combination_method": "intelligent_fusion",
                            }
                        ),
                    }
                ],
            )

            final_results = adaptation_result.get("adapted_results", [])

        # Update strategy history
        self.strategy_history.append(
            {
                "query": query,
                "selected_strategies": selected_strategies,
                "num_results": len(final_results),
                "timestamp": datetime.now().isoformat(),
            }
        )

        # Add agentic metadata to results
        for doc in final_results:
            doc["retrieval_method"] = "agentic_adaptive"
            doc["selected_strategies"] = selected_strategies

        return final_results

    def _get_strategy_selection_prompt(self) -> str:
        """Get prompt for strategy selection agent."""
        return """You are an intelligent retrieval strategy selector.

        Analyze the query and select the most appropriate retrieval strategies:

        Strategy Characteristics:
        - Dense: Best for semantic similarity, concept matching, embedding-based search
        - Sparse: Best for keyword matching, exact terms, traditional IR
        - Hybrid: Balanced approach combining dense and sparse
        - Graph: Best for entity relationships, knowledge graph traversal
        - Fusion: Multi-modal combination for complex queries

        Query Analysis Factors:
        - Query complexity and ambiguity
        - Presence of specific terms vs. concepts
        - Domain specificity
        - Relationship vs. factual focus

        Return selected_strategies as a list of strategy names.
        Prefer multiple strategies for complex queries."""

    def _get_adaptation_prompt(self) -> str:
        """Get prompt for result adaptation agent."""
        return """You are a result adaptation specialist for multi-strategy retrieval.

        Given results from multiple retrieval strategies, intelligently combine them:

        Combination Strategies:
        - Consensus: Documents appearing in multiple strategies
        - Complementary: Unique documents from each strategy
        - Quality-based: Best documents regardless of strategy
        - Diversity: Ensure diverse perspectives and information

        Return adapted_results as a ranked list of the best combined results."""

    def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Process inputs for Kailash workflow integration."""

        query = inputs.get("query", "")
        top_k = inputs.get("top_k", self.top_k)

        if not query:
            return {"error": "No query provided", "results": []}

        results = self.retrieve(query, top_k)

        return {
            "results": results,
            "query": query,
            "retrieval_method": "agentic_adaptive",
            "num_results": len(results),
            "strategy_count": len(self.available_retrievers),
        }
