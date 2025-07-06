"""
Advanced Chunking Nodes for Kailash SDK

State-of-the-art chunking nodes implementing semantic, recursive, contextual,
and adaptive chunking strategies for optimal document processing.
"""

import json
import logging
import re
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from kailash.nodes.ai import EmbeddingGeneratorNode, LLMAgentNode
from kailash.nodes.base import Node, NodeParameter
from kailash.nodes.transform import DataTransformer

logger = logging.getLogger(__name__)


class BaseChunkerNode(Node, ABC):
    """Base class for all chunking nodes."""

    def __init__(self, name: str, **kwargs):
        # Set attributes before calling super().__init__() as Kailash validates during init
        self.chunk_size = kwargs.get("chunk_size", 2000)
        self.chunk_overlap = kwargs.get("chunk_overlap", 200)
        self.min_chunk_size = kwargs.get("min_chunk_size", 100)
        self.preserve_sentences = kwargs.get("preserve_sentences", True)
        super().__init__(name=name)

    @abstractmethod
    def chunk_text(
        self, text: str, metadata: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """Chunk text into optimal segments."""
        pass

    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences using regex."""
        # Simple sentence splitting (in practice, use proper sentence segmentation)
        sentence_pattern = r"(?<=[.!?])\s+"
        sentences = re.split(sentence_pattern, text.strip())
        return [s.strip() for s in sentences if s.strip()]

    def _split_into_words(self, text: str) -> List[str]:
        """Split text into words."""
        return text.split()

    def _calculate_text_length(self, text: str, unit: str = "chars") -> int:
        """Calculate text length in specified unit."""
        if unit == "chars":
            return len(text)
        elif unit == "words":
            return len(text.split())
        elif unit == "tokens":
            # Approximate token count (in practice, use proper tokenizer)
            return len(text.split()) * 1.3  # Rough estimate
        else:
            return len(text)

    def _create_chunk_metadata(
        self,
        chunk_text: str,
        chunk_index: int,
        start_pos: int,
        end_pos: int,
        original_metadata: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Create metadata for a chunk."""
        metadata = {
            "chunk_index": chunk_index,
            "start_position": start_pos,
            "end_position": end_pos,
            "chunk_length": len(chunk_text),
            "word_count": len(chunk_text.split()),
            "chunking_method": self.__class__.__name__,
            "created_at": datetime.now().isoformat(),
        }

        if original_metadata:
            metadata.update(original_metadata)

        return metadata


class SemanticChunkerNode(BaseChunkerNode):
    """
    Semantic chunking that splits text based on semantic similarity
    to create meaningful, coherent chunks.
    """

    def __init__(self, name: str = "semantic_chunker", **kwargs):
        # Set attributes before calling super().__init__() as Kailash validates during init
        self.similarity_threshold = kwargs.get("similarity_threshold", 0.75)
        self.window_size = kwargs.get("window_size", 3)  # Sentences to consider
        self.embedding_model = kwargs.get("embedding_model", "text-embedding-3-small")

        super().__init__(name, **kwargs)

        # Embedding generator for semantic analysis
        self.embedder = EmbeddingGeneratorNode(
            name=f"{name}_embedder", provider="ollama", model="nomic-embed-text"
        )

        # Boundary detection LLM
        self.boundary_detector = LLMAgentNode(
            name=f"{name}_boundary_detector",
            provider="ollama",
            model="llama3.2:3b",
            system_prompt=self._get_boundary_detection_prompt(),
        )

        logger.info(
            f"SemanticChunkerNode initialized with threshold {self.similarity_threshold}"
        )

    def chunk_text(
        self, text: str, metadata: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """Chunk text based on semantic similarity."""

        if not text.strip():
            return []

        logger.info(f"Semantic chunking text of {len(text)} characters")

        # Split into sentences
        sentences = self._split_into_sentences(text)

        if len(sentences) <= 1:
            return [self._create_single_chunk(text, metadata)]

        # Generate embeddings for sentences
        sentence_embeddings = self._generate_sentence_embeddings(sentences)

        # Find semantic boundaries
        boundaries = self._find_semantic_boundaries(sentences, sentence_embeddings)

        # Optimize boundaries using LLM
        optimized_boundaries = self._optimize_boundaries(sentences, boundaries)

        # Create chunks from boundaries
        chunks = self._create_chunks_from_boundaries(
            text, sentences, optimized_boundaries, metadata
        )

        logger.info(f"Created {len(chunks)} semantic chunks")
        return chunks

    def _generate_sentence_embeddings(self, sentences: List[str]) -> List[List[float]]:
        """Generate embeddings for all sentences."""

        if not sentences:
            return []

        embeddings_result = self.embedder.run(
            operation="embed_batch",
            provider="ollama",  # Use Ollama with Docker
            model="nomic-embed-text",  # Use Ollama embedding model
            input_texts=sentences,
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

        # Ensure we have embeddings for all sentences
        while len(embeddings) < len(sentences):
            embeddings.append([0.0] * 768)  # Ollama nomic-embed-text dimension

        return embeddings[: len(sentences)]

    def _find_semantic_boundaries(
        self, sentences: List[str], embeddings: List[List[float]]
    ) -> List[int]:
        """Find semantic boundaries using embedding similarity."""

        boundaries = [0]  # Always start with first sentence

        for i in range(1, len(sentences) - 1):
            # Calculate similarity in sliding window
            window_similarities = []

            for j in range(
                max(0, i - self.window_size),
                min(len(sentences), i + self.window_size + 1),
            ):
                if j != i:
                    similarity = self._cosine_similarity(embeddings[i], embeddings[j])
                    window_similarities.append(similarity)

            # Check if this is a good boundary point
            avg_similarity = np.mean(window_similarities) if window_similarities else 0

            if avg_similarity < self.similarity_threshold:
                boundaries.append(i)

        boundaries.append(len(sentences))  # Always end with last sentence
        return boundaries

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        vec1_np = np.array(vec1)
        vec2_np = np.array(vec2)

        norm1 = np.linalg.norm(vec1_np)
        norm2 = np.linalg.norm(vec2_np)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return np.dot(vec1_np, vec2_np) / (norm1 * norm2)

    def _optimize_boundaries(
        self, sentences: List[str], boundaries: List[int]
    ) -> List[int]:
        """Optimize boundaries using LLM analysis."""

        # Create boundary analysis input
        boundary_analysis = []
        for i in range(len(boundaries) - 1):
            start_idx = boundaries[i]
            end_idx = boundaries[i + 1]

            # Get context around boundary
            context_start = max(0, start_idx - 2)
            context_end = min(len(sentences), end_idx + 2)

            context_sentences = sentences[context_start:context_end]
            boundary_position = start_idx - context_start

            boundary_analysis.append(
                {
                    "boundary_index": i,
                    "context": " ".join(context_sentences),
                    "proposed_boundary": boundary_position,
                    "boundary_sentence_index": start_idx,
                }
            )

        # LLM boundary optimization
        optimization_input = {
            "sentences": sentences,
            "proposed_boundaries": boundary_analysis,
            "optimization_criteria": [
                "semantic_coherence",
                "logical_flow",
                "topic_consistency",
                "chunk_size_balance",
            ],
        }

        # Convert to message format for LLM
        prompt = f"""Analyze proposed sentence boundaries and optimize them for semantic chunking.

Input: {optimization_input}

Please optimize the boundaries and return optimized_boundaries as a list of sentence indices."""

        optimization_result = self.boundary_detector.run(
            provider="ollama",
            model="llama3.2:3b",
            messages=[{"role": "user", "content": prompt}],
        )
        optimized_boundaries = optimization_result.get(
            "optimized_boundaries", boundaries
        )

        return optimized_boundaries

    def _create_chunks_from_boundaries(
        self,
        text: str,
        sentences: List[str],
        boundaries: List[int],
        metadata: Optional[Dict] = None,
    ) -> List[Dict[str, Any]]:
        """Create chunks from sentence boundaries."""

        chunks = []

        for i in range(len(boundaries) - 1):
            start_idx = boundaries[i]
            end_idx = boundaries[i + 1]

            # Get sentences for this chunk
            chunk_sentences = sentences[start_idx:end_idx]
            chunk_text = " ".join(chunk_sentences)

            # Calculate positions in original text
            start_pos = text.find(chunk_sentences[0]) if chunk_sentences else 0
            end_pos = start_pos + len(chunk_text)

            # Create chunk metadata
            chunk_metadata = self._create_chunk_metadata(
                chunk_text, i, start_pos, end_pos, metadata
            )
            chunk_metadata.update(
                {
                    "sentence_count": len(chunk_sentences),
                    "semantic_boundary_score": self.similarity_threshold,
                    "chunk_type": "semantic_coherent",
                }
            )

            chunks.append({"content": chunk_text, "metadata": chunk_metadata})

        return chunks

    def _create_single_chunk(
        self, text: str, metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Create a single chunk for short text."""
        chunk_metadata = self._create_chunk_metadata(text, 0, 0, len(text), metadata)
        chunk_metadata["chunk_type"] = "single_semantic"

        return {"content": text, "metadata": chunk_metadata}

    def _get_boundary_detection_prompt(self) -> str:
        """Get prompt for boundary detection optimization."""
        return """You are a semantic boundary optimization specialist for text chunking.

        Analyze proposed sentence boundaries and optimize them for:
        - Semantic coherence within chunks
        - Logical flow and topic consistency
        - Balanced chunk sizes
        - Natural breaking points

        Consider:
        - Topic transitions and shifts
        - Logical argument structure
        - Paragraph and section breaks
        - Conceptual completeness

        Return optimized_boundaries as a list of sentence indices where chunks should start."""

    def get_parameters(self) -> Dict[str, NodeParameter]:
        """Get node parameters for Kailash framework."""
        return {
            "text": NodeParameter(
                name="text",
                type=str,
                required=True,
                description="Text to be chunked into semantic segments",
            ),
            "metadata": NodeParameter(
                name="metadata",
                type=dict,
                required=False,
                default={},
                description="Optional metadata to attach to chunks",
            ),
            "chunk_size": NodeParameter(
                name="chunk_size",
                type=int,
                required=False,
                default=self.chunk_size,
                description="Target size for each chunk in characters",
            ),
            "similarity_threshold": NodeParameter(
                name="similarity_threshold",
                type=float,
                required=False,
                default=self.similarity_threshold,
                description="Similarity threshold for semantic boundaries",
            ),
        }

    def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Run method required by Kailash Node interface."""
        return self.process(inputs)

    def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Process inputs for Kailash workflow integration."""

        text = inputs.get("text", "")
        metadata = inputs.get("metadata", {})

        if not text:
            return {"error": "No text provided", "chunks": []}

        chunks = self.chunk_text(text, metadata)

        return {
            "chunks": chunks,
            "num_chunks": len(chunks),
            "chunking_method": "semantic",
            "total_length": len(text),
        }


class RecursiveChunkerNode(BaseChunkerNode):
    """
    Recursive chunking that splits text hierarchically, starting with
    large chunks and recursively dividing them based on structure.
    """

    def __init__(self, name: str = "recursive_chunker", **kwargs):
        # Set attributes before calling super().__init__() as Kailash validates during init
        self.max_levels = kwargs.get("max_levels", 3)
        self.split_patterns = kwargs.get(
            "split_patterns",
            [
                r"\n\n\n+",  # Multiple line breaks
                r"\n\n",  # Double line breaks
                r"\n",  # Single line breaks
                r"\. ",  # Sentence ends
                r" ",  # Word boundaries
            ],
        )
        self.level_size_factors = kwargs.get("level_size_factors", [1.0, 0.5, 0.25])

        super().__init__(name, **kwargs)

        # Structure analyzer
        self.structure_analyzer = LLMAgentNode(
            name=f"{name}_structure_analyzer",
            provider="ollama",
            model="llama3.2:3b",
            system_prompt=self._get_structure_analysis_prompt(),
            temperature=0.1,
        )

        logger.info(f"RecursiveChunkerNode initialized with {self.max_levels} levels")

    def chunk_text(
        self, text: str, metadata: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """Chunk text using recursive splitting."""

        if not text.strip():
            return []

        logger.info(f"Recursive chunking text of {len(text)} characters")

        # Analyze document structure
        structure_analysis = self._analyze_document_structure(text)

        # Perform recursive chunking
        chunks = self._recursive_split(
            text,
            level=0,
            target_size=self.chunk_size,
            structure_info=structure_analysis,
            metadata=metadata,
        )

        # Post-process chunks
        final_chunks = self._post_process_chunks(chunks)

        logger.info(f"Created {len(final_chunks)} recursive chunks")
        return final_chunks

    def _analyze_document_structure(self, text: str) -> Dict[str, Any]:
        """Analyze document structure to guide recursive splitting."""

        analysis_input = {
            "text": text[:2000],  # Sample for analysis
            "analysis_task": "hierarchical_structure",
            "identify_elements": [
                "sections",
                "subsections",
                "paragraphs",
                "lists",
                "tables",
                "code_blocks",
            ],
        }

        result = self.structure_analyzer.run(
            provider="ollama",
            model="llama3.2:3b",
            messages=[{"role": "user", "content": json.dumps(analysis_input)}],
        )

        return result.get(
            "structure_analysis",
            {
                "has_sections": False,
                "has_subsections": False,
                "paragraph_count": len(text.split("\n\n")),
                "structure_type": "plain_text",
            },
        )

    def _recursive_split(
        self,
        text: str,
        level: int,
        target_size: int,
        structure_info: Dict,
        metadata: Optional[Dict] = None,
        parent_chunk_id: str = "",
    ) -> List[Dict[str, Any]]:
        """Recursively split text into hierarchical chunks."""

        chunks = []

        # Base case: text is small enough or max levels reached
        if len(text) <= target_size or level >= self.max_levels:
            chunk_id = f"{parent_chunk_id}.{len(chunks)}" if parent_chunk_id else "0"
            chunk_metadata = self._create_chunk_metadata(
                text, len(chunks), 0, len(text), metadata
            )
            chunk_metadata.update(
                {
                    "level": level,
                    "chunk_id": chunk_id,
                    "is_leaf": True,
                    "split_method": "base_case",
                }
            )

            return [{"content": text, "metadata": chunk_metadata}]

        # Find best split pattern for current level
        split_pattern = self._select_split_pattern(text, level, structure_info)

        # Split text using selected pattern
        parts = self._split_by_pattern(text, split_pattern)

        # If splitting didn't help, force split by size
        if len(parts) <= 1:
            parts = self._force_split_by_size(text, target_size)

        # Recursively process each part
        for i, part in enumerate(parts):
            if part.strip():  # Skip empty parts
                chunk_id = f"{parent_chunk_id}.{i}" if parent_chunk_id else str(i)

                # Calculate target size for next level
                next_target_size = int(
                    target_size
                    * self.level_size_factors[
                        min(level, len(self.level_size_factors) - 1)
                    ]
                )

                # Recursive call
                sub_chunks = self._recursive_split(
                    part,
                    level + 1,
                    next_target_size,
                    structure_info,
                    metadata,
                    chunk_id,
                )

                # If we got multiple sub-chunks, add intermediate node
                if len(sub_chunks) > 1:
                    intermediate_metadata = self._create_chunk_metadata(
                        part, i, 0, len(part), metadata
                    )
                    intermediate_metadata.update(
                        {
                            "level": level,
                            "chunk_id": chunk_id,
                            "is_leaf": False,
                            "child_count": len(sub_chunks),
                            "split_method": split_pattern,
                        }
                    )

                    chunks.append(
                        {
                            "content": part,
                            "metadata": intermediate_metadata,
                            "children": sub_chunks,
                        }
                    )
                else:
                    # Single sub-chunk, promote it up
                    sub_chunks[0]["metadata"]["chunk_id"] = chunk_id
                    chunks.extend(sub_chunks)

        return chunks

    def _select_split_pattern(self, text: str, level: int, structure_info: Dict) -> str:
        """Select best split pattern for current level and text structure."""

        # Level-based pattern selection
        if level < len(self.split_patterns):
            base_pattern = self.split_patterns[level]
        else:
            base_pattern = self.split_patterns[-1]  # Use last pattern

        # Adjust pattern based on structure
        if structure_info.get("has_sections") and level == 0:
            return r"\n#+\s+"  # Markdown headers
        elif structure_info.get("has_subsections") and level == 1:
            return r"\n###+\s+"  # Markdown subheaders
        elif structure_info.get("structure_type") == "code" and level <= 1:
            return r"\n\ndef\s+|\nclass\s+"  # Function/class boundaries
        else:
            return base_pattern

    def _split_by_pattern(self, text: str, pattern: str) -> List[str]:
        """Split text by regex pattern."""
        try:
            parts = re.split(pattern, text)
            return [part for part in parts if part.strip()]
        except re.error:
            # If regex fails, fall back to simple splitting
            if pattern == r"\n\n":
                return text.split("\n\n")
            elif pattern == r"\n":
                return text.split("\n")
            else:
                return [text]

    def _force_split_by_size(self, text: str, target_size: int) -> List[str]:
        """Force split text by size when pattern splitting fails."""

        parts = []
        start = 0

        while start < len(text):
            end = start + target_size

            if end >= len(text):
                parts.append(text[start:])
                break

            # Try to find natural break point near target size
            break_point = self._find_break_point(text, start, end)

            parts.append(text[start:break_point])
            start = break_point

        return parts

    def _find_break_point(self, text: str, start: int, end: int) -> int:
        """Find natural break point near target position."""

        # Look for sentence boundaries first
        for i in range(end, start, -1):
            if i < len(text) and text[i] in ".!?":
                return i + 1

        # Look for word boundaries
        for i in range(end, start, -1):
            if i < len(text) and text[i] == " ":
                return i

        # Use exact position as last resort
        return end

    def _post_process_chunks(self, chunks: List[Dict]) -> List[Dict[str, Any]]:
        """Post-process chunks to flatten hierarchy and ensure size constraints."""

        final_chunks = []

        def flatten_chunks(chunk_list: List[Dict], parent_level: int = 0):
            for chunk in chunk_list:
                # Check if chunk has children
                if "children" in chunk:
                    # Recursively process children
                    flatten_chunks(chunk["children"], parent_level + 1)
                else:
                    # Leaf chunk - check size and split if necessary
                    content = chunk["content"]
                    metadata = chunk["metadata"]

                    if len(content) > self.chunk_size * 1.5:  # Allow some flexibility
                        # Split oversized chunk
                        sub_chunks = self._split_oversized_chunk(content, metadata)
                        final_chunks.extend(sub_chunks)
                    else:
                        final_chunks.append(chunk)

        flatten_chunks(chunks)

        # Re-index chunks
        for i, chunk in enumerate(final_chunks):
            chunk["metadata"]["final_chunk_index"] = i

        return final_chunks

    def _split_oversized_chunk(
        self, content: str, base_metadata: Dict
    ) -> List[Dict[str, Any]]:
        """Split oversized chunk into smaller pieces."""

        parts = self._force_split_by_size(content, self.chunk_size)
        sub_chunks = []

        for i, part in enumerate(parts):
            chunk_metadata = base_metadata.copy()
            chunk_metadata.update(
                {
                    "sub_chunk_index": i,
                    "is_sub_chunk": True,
                    "parent_chunk_id": base_metadata.get("chunk_id", ""),
                    "split_reason": "oversized",
                }
            )

            sub_chunks.append({"content": part, "metadata": chunk_metadata})

        return sub_chunks

    def _get_structure_analysis_prompt(self) -> str:
        """Get prompt for document structure analysis."""
        return """You are a document structure analyzer for recursive text chunking.

        Analyze the text structure and identify:
        - Document type (article, code, technical doc, etc.)
        - Hierarchical elements (sections, subsections, paragraphs)
        - Structural patterns (headers, lists, code blocks)
        - Natural break points and boundaries

        Return structure_analysis with:
        - has_sections: boolean
        - has_subsections: boolean
        - structure_type: string (article, code, technical, plain_text)
        - suggested_split_strategy: string
        - natural_boundaries: list of suggested split points"""

    def get_parameters(self) -> Dict[str, NodeParameter]:
        """Get node parameters for Kailash framework."""
        return {
            "text": NodeParameter(
                name="text",
                type=str,
                required=True,
                description="Text to be chunked hierarchically",
            ),
            "metadata": NodeParameter(
                name="metadata",
                type=dict,
                required=False,
                default={},
                description="Optional metadata to attach to chunks",
            ),
            "chunk_size": NodeParameter(
                name="chunk_size",
                type=int,
                required=False,
                default=self.chunk_size,
                description="Target size for each chunk in characters",
            ),
            "max_levels": NodeParameter(
                name="max_levels",
                type=int,
                required=False,
                default=self.max_levels,
                description="Maximum levels of recursive splitting",
            ),
        }

    def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Run method required by Kailash Node interface."""
        return self.process(inputs)

    def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Process inputs for Kailash workflow integration."""

        text = inputs.get("text", "")
        metadata = inputs.get("metadata", {})

        if not text:
            return {"error": "No text provided", "chunks": []}

        chunks = self.chunk_text(text, metadata)

        return {
            "chunks": chunks,
            "num_chunks": len(chunks),
            "chunking_method": "recursive",
            "max_levels": self.max_levels,
            "total_length": len(text),
        }


class ContextualChunkerNode(BaseChunkerNode):
    """
    Contextual chunking that maintains context and relationships
    between chunks for better retrieval and generation.
    """

    def __init__(self, name: str = "contextual_chunker", **kwargs):
        # Set attributes before calling super().__init__() as Kailash validates during init
        self.context_window = kwargs.get("context_window", 3)  # Chunks before/after
        self.relationship_types = kwargs.get(
            "relationship_types",
            ["sequential", "hierarchical", "thematic", "reference"],
        )
        self.include_summaries = kwargs.get("include_summaries", True)

        super().__init__(name, **kwargs)

        # Context analyzer
        self.context_analyzer = LLMAgentNode(
            name=f"{name}_context_analyzer",
            provider="ollama",
            model="llama3.2:3b",
            system_prompt=self._get_context_analysis_prompt(),
            temperature=0.1,
        )

        # Relationship detector
        self.relationship_detector = LLMAgentNode(
            name=f"{name}_relationship_detector",
            provider="ollama",
            model="llama3.2:3b",
            system_prompt=self._get_relationship_detection_prompt(),
            temperature=0.1,
        )

        logger.info(
            f"ContextualChunkerNode initialized with context window {self.context_window}"
        )

    def chunk_text(
        self, text: str, metadata: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """Chunk text with contextual awareness."""

        if not text.strip():
            return []

        logger.info(f"Contextual chunking text of {len(text)} characters")

        # Initial chunking using sentence-based approach
        initial_chunks = self._create_initial_chunks(text)

        # Analyze context and relationships
        contextual_chunks = self._add_contextual_information(initial_chunks, text)

        # Generate summaries if enabled
        if self.include_summaries:
            contextual_chunks = self._add_chunk_summaries(contextual_chunks)

        # Add metadata
        final_chunks = self._finalize_contextual_chunks(contextual_chunks, metadata)

        logger.info(f"Created {len(final_chunks)} contextual chunks")
        return final_chunks

    def _create_initial_chunks(self, text: str) -> List[Dict[str, Any]]:
        """Create initial chunks using sentence boundaries."""

        sentences = self._split_into_sentences(text)
        chunks = []

        current_chunk = ""
        current_sentences = []

        for sentence in sentences:
            # Check if adding sentence exceeds chunk size
            potential_chunk = (
                current_chunk + " " + sentence if current_chunk else sentence
            )

            if len(potential_chunk) > self.chunk_size and current_chunk:
                # Create chunk from current content
                chunks.append(
                    {
                        "content": current_chunk.strip(),
                        "sentences": current_sentences.copy(),
                        "start_sentence": len(chunks) * len(current_sentences),
                        "end_sentence": len(chunks) * len(current_sentences)
                        + len(current_sentences),
                    }
                )

                current_chunk = sentence
                current_sentences = [sentence]
            else:
                current_chunk = potential_chunk
                current_sentences.append(sentence)

        # Add final chunk
        if current_chunk:
            chunks.append(
                {
                    "content": current_chunk.strip(),
                    "sentences": current_sentences,
                    "start_sentence": len(chunks) * len(current_sentences),
                    "end_sentence": len(chunks) * len(current_sentences)
                    + len(current_sentences),
                }
            )

        return chunks

    def _add_contextual_information(
        self, chunks: List[Dict], full_text: str
    ) -> List[Dict]:
        """Add contextual information to each chunk."""

        contextual_chunks = []

        for i, chunk in enumerate(chunks):
            # Calculate context window
            start_idx = max(0, i - self.context_window)
            end_idx = min(len(chunks), i + self.context_window + 1)

            # Get surrounding chunks for context
            context_before = chunks[start_idx:i]
            context_after = chunks[i + 1 : end_idx]

            # Analyze relationships with surrounding chunks
            relationships = self._analyze_chunk_relationships(
                chunk, context_before, context_after
            )

            # Create contextual chunk
            contextual_chunk = chunk.copy()
            contextual_chunk.update(
                {
                    "chunk_index": i,
                    "context_before": [
                        c["content"][:100] + "..." for c in context_before[-2:]
                    ],
                    "context_after": [
                        c["content"][:100] + "..." for c in context_after[:2]
                    ],
                    "relationships": relationships,
                    "context_window_size": len(context_before) + len(context_after),
                }
            )

            contextual_chunks.append(contextual_chunk)

        return contextual_chunks

    def _analyze_chunk_relationships(
        self, current_chunk: Dict, context_before: List[Dict], context_after: List[Dict]
    ) -> Dict[str, Any]:
        """Analyze relationships between current chunk and context."""

        analysis_input = {
            "current_chunk": current_chunk["content"],
            "context_before": [c["content"] for c in context_before],
            "context_after": [c["content"] for c in context_after],
            "relationship_types": self.relationship_types,
        }

        result = self.relationship_detector.run(
            provider="ollama",
            model="llama3.2:3b",
            messages=[{"role": "user", "content": json.dumps(analysis_input)}],
        )

        return result.get(
            "relationships",
            {"sequential": [], "thematic": [], "reference": [], "hierarchical": []},
        )

    def _add_chunk_summaries(self, chunks: List[Dict]) -> List[Dict]:
        """Add summaries to chunks for better context."""

        summarized_chunks = []

        for chunk in chunks:
            # Generate summary for this chunk
            summary_input = {
                "content": chunk["content"],
                "context_before": chunk.get("context_before", []),
                "context_after": chunk.get("context_after", []),
                "summary_type": "contextual",
            }

            summary_result = self.context_analyzer.run(
                provider="ollama",
                model="llama3.2:3b",
                messages=[{"role": "user", "content": json.dumps(summary_input)}],
            )
            chunk_summary = summary_result.get("summary", "")
            key_concepts = summary_result.get("key_concepts", [])

            # Add summary information
            chunk["summary"] = chunk_summary
            chunk["key_concepts"] = key_concepts
            chunk["has_summary"] = True

            summarized_chunks.append(chunk)

        return summarized_chunks

    def _finalize_contextual_chunks(
        self, chunks: List[Dict], base_metadata: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """Finalize contextual chunks with complete metadata."""

        final_chunks = []

        for i, chunk in enumerate(chunks):
            # Create comprehensive metadata
            chunk_metadata = self._create_chunk_metadata(
                chunk["content"], i, 0, len(chunk["content"]), base_metadata
            )

            chunk_metadata.update(
                {
                    "contextual_info": {
                        "has_context_before": len(chunk.get("context_before", [])) > 0,
                        "has_context_after": len(chunk.get("context_after", [])) > 0,
                        "relationship_count": sum(
                            len(rels)
                            for rels in chunk.get("relationships", {}).values()
                        ),
                        "key_concepts": chunk.get("key_concepts", []),
                        "has_summary": chunk.get("has_summary", False),
                    },
                    "chunk_relationships": chunk.get("relationships", {}),
                    "context_references": {
                        "previous_chunks": chunk.get("context_before", []),
                        "following_chunks": chunk.get("context_after", []),
                    },
                }
            )

            final_chunk = {"content": chunk["content"], "metadata": chunk_metadata}

            # Add summary if available
            if chunk.get("summary"):
                final_chunk["summary"] = chunk["summary"]

            final_chunks.append(final_chunk)

        return final_chunks

    def _get_context_analysis_prompt(self) -> str:
        """Get prompt for context analysis."""
        return """You are a contextual analysis specialist for document chunking.

        Analyze chunk content in context and provide:
        - Concise summary of the chunk's main points
        - Key concepts and entities mentioned
        - Contextual significance within the document
        - Important relationships to surrounding content

        Keep summaries under 100 words and focus on essential information
        that would help with retrieval and understanding.

        Return JSON with:
        - summary: concise content summary
        - key_concepts: list of important concepts
        - contextual_significance: importance rating (1-5)"""

    def _get_relationship_detection_prompt(self) -> str:
        """Get prompt for relationship detection."""
        return """You are a relationship detection specialist for contextual chunking.

        Analyze relationships between the current chunk and surrounding context:

        Relationship Types:
        - sequential: Direct continuation or progression
        - thematic: Shared topics or themes
        - reference: Cross-references or citations
        - hierarchical: Parent-child or part-whole relationships

        For each relationship type, identify specific connections and their strength.

        Return relationships as a dictionary with relationship types as keys
        and lists of relationship descriptions as values."""

    def get_parameters(self) -> Dict[str, NodeParameter]:
        """Get node parameters for Kailash framework."""
        return {
            "text": NodeParameter(
                name="text",
                type=str,
                required=True,
                description="Text to be chunked with contextual awareness",
            ),
            "metadata": NodeParameter(
                name="metadata",
                type=dict,
                required=False,
                default={},
                description="Optional metadata to attach to chunks",
            ),
            "context_window": NodeParameter(
                name="context_window",
                type=int,
                required=False,
                default=self.context_window,
                description="Number of chunks before/after for context",
            ),
        }

    def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Run method required by Kailash Node interface."""
        return self.process(inputs)

    def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Process inputs for Kailash workflow integration."""

        text = inputs.get("text", "")
        metadata = inputs.get("metadata", {})

        if not text:
            return {"error": "No text provided", "chunks": []}

        chunks = self.chunk_text(text, metadata)

        return {
            "chunks": chunks,
            "num_chunks": len(chunks),
            "chunking_method": "contextual",
            "context_window": self.context_window,
            "total_length": len(text),
        }


class MetadataAwareChunkerNode(BaseChunkerNode):
    """
    Metadata-aware chunking that uses document metadata and structure
    to create semantically meaningful chunks.
    """

    def __init__(self, name: str = "metadata_aware_chunker", **kwargs):
        # Set attributes before calling super().__init__() as Kailash validates during init
        self.metadata_signals = kwargs.get(
            "metadata_signals",
            [
                "headings",
                "sections",
                "page_breaks",
                "chapters",
                "topics",
                "authors",
                "dates",
                "categories",
            ],
        )
        self.structure_importance = kwargs.get("structure_importance", 0.7)

        super().__init__(name, **kwargs)

        # Metadata extractor
        self.metadata_extractor = LLMAgentNode(
            name=f"{name}_metadata_extractor",
            provider="ollama",
            model="llama3.2:3b",
            system_prompt=self._get_metadata_extraction_prompt(),
            temperature=0.1,
        )

        logger.info("MetadataAwareChunkerNode initialized")

    def chunk_text(
        self, text: str, metadata: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """Chunk text using metadata and structure awareness."""

        if not text.strip():
            return []

        logger.info(f"Metadata-aware chunking text of {len(text)} characters")

        # Extract additional metadata from text
        extracted_metadata = self._extract_text_metadata(text)

        # Combine with provided metadata
        combined_metadata = metadata.copy() if metadata else {}
        combined_metadata.update(extracted_metadata)

        # Create structure-aware chunks
        chunks = self._create_structure_aware_chunks(text, combined_metadata)

        # Enhance chunks with metadata
        enhanced_chunks = self._enhance_chunks_with_metadata(chunks, combined_metadata)

        logger.info(f"Created {len(enhanced_chunks)} metadata-aware chunks")
        return enhanced_chunks

    def _extract_text_metadata(self, text: str) -> Dict[str, Any]:
        """Extract metadata signals from text content."""

        extraction_input = {
            "text": text[:3000],  # Sample for analysis
            "metadata_signals": self.metadata_signals,
            "extraction_task": "comprehensive_metadata",
        }

        result = self.metadata_extractor.run(
            provider="ollama",
            model="llama3.2:3b",
            messages=[{"role": "user", "content": json.dumps(extraction_input)}],
        )

        return result.get(
            "extracted_metadata",
            {
                "document_type": "unknown",
                "structure_elements": [],
                "topics": [],
                "entities": [],
            },
        )

    def _create_structure_aware_chunks(
        self, text: str, metadata: Dict
    ) -> List[Dict[str, Any]]:
        """Create chunks based on document structure and metadata."""

        structure_elements = metadata.get("structure_elements", [])

        if not structure_elements:
            # Fall back to sentence-based chunking
            return self._fallback_sentence_chunking(text)

        chunks = []

        # Process structure elements
        for i, element in enumerate(structure_elements):
            element_type = element.get("type", "section")
            start_pos = element.get("start_position", 0)
            end_pos = element.get("end_position", len(text))

            # Extract content for this structural element
            element_content = text[start_pos:end_pos].strip()

            if not element_content:
                continue

            # Check if element content needs further chunking
            if len(element_content) > self.chunk_size:
                # Split large structural elements
                sub_chunks = self._split_structural_element(element_content, element)
                chunks.extend(sub_chunks)
            else:
                # Use entire structural element as chunk
                chunk = {
                    "content": element_content,
                    "structure_element": element,
                    "chunk_index": len(chunks),
                    "start_position": start_pos,
                    "end_position": end_pos,
                }
                chunks.append(chunk)

        return chunks

    def _split_structural_element(
        self, content: str, element: Dict
    ) -> List[Dict[str, Any]]:
        """Split large structural elements while preserving structure."""

        sub_chunks = []
        element_type = element.get("type", "section")

        # Choose splitting strategy based on element type
        if element_type in ["chapter", "section"]:
            # Split by paragraphs first
            paragraphs = content.split("\n\n")
            current_chunk = ""

            for paragraph in paragraphs:
                potential_chunk = (
                    current_chunk + "\n\n" + paragraph if current_chunk else paragraph
                )

                if len(potential_chunk) > self.chunk_size and current_chunk:
                    # Create sub-chunk
                    sub_chunks.append(
                        {
                            "content": current_chunk.strip(),
                            "structure_element": element,
                            "sub_element_index": len(sub_chunks),
                            "is_partial": True,
                        }
                    )
                    current_chunk = paragraph
                else:
                    current_chunk = potential_chunk

            # Add final sub-chunk
            if current_chunk:
                sub_chunks.append(
                    {
                        "content": current_chunk.strip(),
                        "structure_element": element,
                        "sub_element_index": len(sub_chunks),
                        "is_partial": True,
                    }
                )

        else:
            # Fall back to sentence-based splitting
            sentences = self._split_into_sentences(content)
            current_chunk = ""

            for sentence in sentences:
                potential_chunk = (
                    current_chunk + " " + sentence if current_chunk else sentence
                )

                if len(potential_chunk) > self.chunk_size and current_chunk:
                    sub_chunks.append(
                        {
                            "content": current_chunk.strip(),
                            "structure_element": element,
                            "sub_element_index": len(sub_chunks),
                            "is_partial": True,
                        }
                    )
                    current_chunk = sentence
                else:
                    current_chunk = potential_chunk

            if current_chunk:
                sub_chunks.append(
                    {
                        "content": current_chunk.strip(),
                        "structure_element": element,
                        "sub_element_index": len(sub_chunks),
                        "is_partial": True,
                    }
                )

        return sub_chunks

    def _fallback_sentence_chunking(self, text: str) -> List[Dict[str, Any]]:
        """Fallback to sentence-based chunking when no structure detected."""

        sentences = self._split_into_sentences(text)
        chunks = []
        current_chunk = ""

        for sentence in sentences:
            potential_chunk = (
                current_chunk + " " + sentence if current_chunk else sentence
            )

            if len(potential_chunk) > self.chunk_size and current_chunk:
                chunks.append(
                    {
                        "content": current_chunk.strip(),
                        "chunk_index": len(chunks),
                        "fallback_chunking": True,
                    }
                )
                current_chunk = sentence
            else:
                current_chunk = potential_chunk

        if current_chunk:
            chunks.append(
                {
                    "content": current_chunk.strip(),
                    "chunk_index": len(chunks),
                    "fallback_chunking": True,
                }
            )

        return chunks

    def _enhance_chunks_with_metadata(
        self, chunks: List[Dict], global_metadata: Dict
    ) -> List[Dict[str, Any]]:
        """Enhance chunks with comprehensive metadata."""

        enhanced_chunks = []

        for i, chunk in enumerate(chunks):
            # Create base chunk metadata
            chunk_metadata = self._create_chunk_metadata(
                chunk["content"],
                i,
                chunk.get("start_position", 0),
                chunk.get("end_position", len(chunk["content"])),
                global_metadata,
            )

            # Add structure-specific metadata
            if "structure_element" in chunk:
                element = chunk["structure_element"]
                chunk_metadata.update(
                    {
                        "structure_info": {
                            "element_type": element.get("type", "unknown"),
                            "element_title": element.get("title", ""),
                            "element_level": element.get("level", 0),
                            "is_partial": chunk.get("is_partial", False),
                            "sub_element_index": chunk.get("sub_element_index", 0),
                        }
                    }
                )

            # Add document-level metadata
            chunk_metadata.update(
                {
                    "document_metadata": {
                        "document_type": global_metadata.get(
                            "document_type", "unknown"
                        ),
                        "topics": global_metadata.get("topics", []),
                        "entities": global_metadata.get("entities", []),
                        "structure_elements_count": len(
                            global_metadata.get("structure_elements", [])
                        ),
                    },
                    "metadata_aware": True,
                    "structure_importance": self.structure_importance,
                }
            )

            enhanced_chunk = {"content": chunk["content"], "metadata": chunk_metadata}

            enhanced_chunks.append(enhanced_chunk)

        return enhanced_chunks

    def _get_metadata_extraction_prompt(self) -> str:
        """Get prompt for metadata extraction."""
        return """You are a metadata extraction specialist for document analysis.

        Extract comprehensive metadata from the text including:

        Structure Elements:
        - Document type (article, technical doc, report, etc.)
        - Headings and sections with positions
        - Hierarchical structure and levels
        - Page breaks, chapters, subsections

        Content Metadata:
        - Main topics and themes
        - Key entities (people, organizations, concepts)
        - Important dates and references
        - Technical terms and terminology

        For structure elements, include:
        - type: element type (heading, section, etc.)
        - title: element title or content
        - level: hierarchical level (1, 2, 3, etc.)
        - start_position: approximate character position
        - end_position: approximate end position

        Return extracted_metadata with comprehensive document information."""

    def get_parameters(self) -> Dict[str, NodeParameter]:
        """Get node parameters for Kailash framework."""
        return {
            "text": NodeParameter(
                name="text",
                type=str,
                required=True,
                description="Text to be chunked with metadata awareness",
            ),
            "metadata": NodeParameter(
                name="metadata",
                type=dict,
                required=False,
                default={},
                description="Optional metadata to attach to chunks",
            ),
            "structure_importance": NodeParameter(
                name="structure_importance",
                type=float,
                required=False,
                default=self.structure_importance,
                description="Importance weight for structural elements",
            ),
        }

    def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Run method required by Kailash Node interface."""
        return self.process(inputs)

    def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Process inputs for Kailash workflow integration."""

        text = inputs.get("text", "")
        metadata = inputs.get("metadata", {})

        if not text:
            return {"error": "No text provided", "chunks": []}

        chunks = self.chunk_text(text, metadata)

        return {
            "chunks": chunks,
            "num_chunks": len(chunks),
            "chunking_method": "metadata_aware",
            "total_length": len(text),
            "metadata_signals": self.metadata_signals,
        }


class AdaptiveChunkerNode(BaseChunkerNode):
    """
    Adaptive chunking that dynamically adjusts chunking strategies
    based on content characteristics and requirements.
    """

    def __init__(self, name: str = "adaptive_chunker", **kwargs):
        # Set attributes before calling super().__init__() as Kailash validates during init
        self.available_strategies = kwargs.get(
            "available_strategies",
            ["semantic", "recursive", "contextual", "metadata_aware"],
        )
        self.adaptation_criteria = kwargs.get(
            "adaptation_criteria",
            ["content_type", "document_structure", "text_complexity", "intended_use"],
        )

        super().__init__(name, **kwargs)

        # Strategy selector
        self.strategy_selector = LLMAgentNode(
            name=f"{name}_strategy_selector",
            provider="ollama",
            model="llama3.2:3b",
            system_prompt=self._get_strategy_selection_prompt(),
            temperature=0.1,
        )

        # Individual chunkers
        self.chunkers = {}
        self._initialize_chunkers()

        logger.info(
            f"AdaptiveChunkerNode initialized with {len(self.available_strategies)} strategies"
        )

    def _initialize_chunkers(self):
        """Initialize available chunking strategies."""

        for strategy in self.available_strategies:
            if strategy == "semantic":
                self.chunkers["semantic"] = SemanticChunkerNode(
                    name=f"{self.__class__.__name__}_semantic",
                    chunk_size=self.chunk_size,
                    chunk_overlap=self.chunk_overlap,
                )
            elif strategy == "recursive":
                self.chunkers["recursive"] = RecursiveChunkerNode(
                    name=f"{self.__class__.__name__}_recursive",
                    chunk_size=self.chunk_size,
                    chunk_overlap=self.chunk_overlap,
                )
            elif strategy == "contextual":
                self.chunkers["contextual"] = ContextualChunkerNode(
                    name=f"{self.__class__.__name__}_contextual",
                    chunk_size=self.chunk_size,
                    chunk_overlap=self.chunk_overlap,
                )
            elif strategy == "metadata_aware":
                self.chunkers["metadata_aware"] = MetadataAwareChunkerNode(
                    name=f"{self.__class__.__name__}_metadata_aware",
                    chunk_size=self.chunk_size,
                    chunk_overlap=self.chunk_overlap,
                )

    def chunk_text(
        self, text: str, metadata: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """Adaptively chunk text using optimal strategy."""

        if not text.strip():
            return []

        logger.info(f"Adaptive chunking text of {len(text)} characters")

        # Analyze content to select optimal strategy
        optimal_strategy = self._select_optimal_strategy(text, metadata)

        # Execute selected strategy
        if optimal_strategy in self.chunkers:
            chunker = self.chunkers[optimal_strategy]
            chunks = chunker.chunk_text(text, metadata)

            # Add adaptive metadata
            for chunk in chunks:
                chunk["metadata"]["adaptive_info"] = {
                    "selected_strategy": optimal_strategy,
                    "strategy_confidence": 0.8,  # Could be calculated
                    "adaptation_criteria": self.adaptation_criteria,
                    "available_strategies": self.available_strategies,
                }

            logger.info(
                f"Used {optimal_strategy} strategy, created {len(chunks)} chunks"
            )
            return chunks

        else:
            logger.warning(f"Strategy {optimal_strategy} not available, using fallback")
            return self._fallback_chunking(text, metadata)

    def _select_optimal_strategy(
        self, text: str, metadata: Optional[Dict] = None
    ) -> str:
        """Select optimal chunking strategy based on content analysis."""

        # Analyze content characteristics
        content_analysis = {
            "text_sample": text[:2000],  # Sample for analysis
            "text_length": len(text),
            "metadata": metadata or {},
            "adaptation_criteria": self.adaptation_criteria,
            "available_strategies": {
                "semantic": "Best for coherent topics and semantic relationships",
                "recursive": "Best for structured documents with clear hierarchy",
                "contextual": "Best for documents requiring context preservation",
                "metadata_aware": "Best for documents with rich structural metadata",
            },
        }

        selection_result = self.strategy_selector.run(
            provider="ollama",
            model="llama3.2:3b",
            messages=[{"role": "user", "content": json.dumps(content_analysis)}],
        )

        selected_strategy = selection_result.get("optimal_strategy", "semantic")
        confidence = selection_result.get("confidence", 0.5)
        reasoning = selection_result.get("reasoning", "Default selection")

        logger.info(
            f"Selected strategy: {selected_strategy} (confidence: {confidence:.2f})"
        )
        logger.info(f"Reasoning: {reasoning}")

        return selected_strategy

    def _fallback_chunking(
        self, text: str, metadata: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """Fallback chunking when strategy selection fails."""

        # Simple sentence-based chunking as fallback
        sentences = self._split_into_sentences(text)
        chunks = []
        current_chunk = ""

        for sentence in sentences:
            potential_chunk = (
                current_chunk + " " + sentence if current_chunk else sentence
            )

            if len(potential_chunk) > self.chunk_size and current_chunk:
                chunk_metadata = self._create_chunk_metadata(
                    current_chunk, len(chunks), 0, len(current_chunk), metadata
                )
                chunk_metadata["chunking_method"] = "adaptive_fallback"

                chunks.append(
                    {"content": current_chunk.strip(), "metadata": chunk_metadata}
                )
                current_chunk = sentence
            else:
                current_chunk = potential_chunk

        if current_chunk:
            chunk_metadata = self._create_chunk_metadata(
                current_chunk, len(chunks), 0, len(current_chunk), metadata
            )
            chunk_metadata["chunking_method"] = "adaptive_fallback"

            chunks.append(
                {"content": current_chunk.strip(), "metadata": chunk_metadata}
            )

        return chunks

    def _get_strategy_selection_prompt(self) -> str:
        """Get prompt for strategy selection."""
        return """You are an adaptive chunking strategy selector.

        Analyze the text content and characteristics to select the optimal chunking strategy:

        Strategy Guidelines:
        - Semantic: Use for content with clear topics and semantic relationships
        - Recursive: Use for structured documents (academic papers, technical docs)
        - Contextual: Use when context preservation is critical
        - Metadata-aware: Use for documents with rich structural metadata

        Analysis Criteria:
        - Content type and domain
        - Document structure and organization
        - Text complexity and coherence
        - Intended use case (retrieval, summarization, etc.)

        Return JSON with:
        - optimal_strategy: selected strategy name
        - confidence: confidence score (0.0-1.0)
        - reasoning: explanation for selection
        - alternative_strategies: ranked alternatives"""

    def get_parameters(self) -> Dict[str, NodeParameter]:
        """Get node parameters for Kailash framework."""
        return {
            "text": NodeParameter(
                name="text",
                type=str,
                required=True,
                description="Text to be chunked adaptively",
            ),
            "metadata": NodeParameter(
                name="metadata",
                type=dict,
                required=False,
                default={},
                description="Optional metadata to attach to chunks",
            ),
            "chunk_size": NodeParameter(
                name="chunk_size",
                type=int,
                required=False,
                default=self.chunk_size,
                description="Target size for each chunk in characters",
            ),
        }

    def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Run method required by Kailash Node interface."""
        return self.process(inputs)

    def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Process inputs for Kailash workflow integration."""

        text = inputs.get("text", "")
        metadata = inputs.get("metadata", {})

        if not text:
            return {"error": "No text provided", "chunks": []}

        chunks = self.chunk_text(text, metadata)

        return {
            "chunks": chunks,
            "num_chunks": len(chunks),
            "chunking_method": "adaptive",
            "available_strategies": self.available_strategies,
            "total_length": len(text),
        }
