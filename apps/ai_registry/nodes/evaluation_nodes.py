"""
Evaluation Nodes for Advanced RAG - Kailash SDK

Comprehensive evaluation nodes for assessing RAG system performance
including faithfulness, relevancy, hallucination detection, and metrics.
"""

import json
import logging
import statistics
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from kailash.nodes.ai import LLMAgentNode
from kailash.nodes.base import Node, NodeParameter
from kailash.nodes.transform import DataTransformer

logger = logging.getLogger(__name__)


class BaseEvaluationNode(Node, ABC):
    """Base class for all evaluation nodes."""

    def __init__(self, name: str, **kwargs):
        # Set attributes before calling super().__init__() as Kailash validates during init
        self.evaluation_criteria = kwargs.get("evaluation_criteria", [])
        self.confidence_threshold = kwargs.get("confidence_threshold", 0.7)
        super().__init__(name=name)

    @abstractmethod
    def evaluate(self, **kwargs) -> Dict[str, Any]:
        """Evaluate the given inputs and return assessment results."""
        pass

    def _normalize_score(
        self, score: float, min_val: float = 0.0, max_val: float = 1.0
    ) -> float:
        """Normalize score to 0-1 range."""
        return max(min_val, min(max_val, score))

    def _calculate_confidence(self, scores: List[float]) -> float:
        """Calculate confidence based on score consistency."""
        if len(scores) <= 1:
            return 0.5

        std_dev = statistics.stdev(scores)
        mean_score = statistics.mean(scores)

        # Higher confidence for lower variance and higher mean
        confidence = max(0.0, min(1.0, (1.0 - std_dev) * mean_score))
        return confidence


class FaithfulnessEvaluatorNode(BaseEvaluationNode):
    """
    Evaluates faithfulness of generated answers to source documents.
    Assesses factual consistency and source attribution accuracy.
    """

    def __init__(self, name: str = "faithfulness_evaluator", **kwargs):
        # Set attributes before calling super().__init__() as Kailash validates during init
        self.evaluation_aspects = kwargs.get(
            "evaluation_aspects",
            [
                "factual_consistency",
                "source_attribution",
                "claim_support",
                "contradiction_detection",
                "information_accuracy",
            ],
        )

        super().__init__(name, **kwargs)

        # Faithfulness assessor
        self.faithfulness_assessor = LLMAgentNode(
            name=f"{name}_assessor",
            provider="ollama",
            model="llama3.2:3b",
            system_prompt=self._get_faithfulness_assessment_prompt(),
            temperature=0.0,
        )

        # Claim extractor
        self.claim_extractor = LLMAgentNode(
            name=f"{name}_claim_extractor",
            provider="ollama",
            model="llama3.2:3b",
            system_prompt=self._get_claim_extraction_prompt(),
            temperature=0.1,
        )

        # Evidence validator
        self.evidence_validator = LLMAgentNode(
            name=f"{name}_evidence_validator",
            provider="ollama",
            model="llama3.2:3b",
            system_prompt=self._get_evidence_validation_prompt(),
            temperature=0.0,
        )

        logger.info(
            f"FaithfulnessEvaluatorNode initialized with {len(self.evaluation_aspects)} aspects"
        )

    def evaluate(
        self, query: str, generated_answer: str, source_documents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Evaluate faithfulness of generated answer to sources."""

        logger.info(
            f"Evaluating faithfulness for answer of {len(generated_answer)} characters"
        )

        # Extract claims from generated answer
        claims = self._extract_claims(generated_answer)

        # Validate each claim against sources
        claim_validations = self._validate_claims(claims, source_documents)

        # Overall faithfulness assessment
        overall_assessment = self._assess_overall_faithfulness(
            query, generated_answer, source_documents, claim_validations
        )

        # Calculate metrics
        faithfulness_metrics = self._calculate_faithfulness_metrics(
            claim_validations, overall_assessment
        )

        evaluation_result = {
            "query": query,
            "generated_answer": generated_answer,
            "faithfulness_score": faithfulness_metrics["overall_score"],
            "aspect_scores": faithfulness_metrics["aspect_scores"],
            "claim_analysis": {
                "total_claims": len(claims),
                "supported_claims": sum(
                    1 for c in claim_validations if c["is_supported"]
                ),
                "unsupported_claims": sum(
                    1 for c in claim_validations if not c["is_supported"]
                ),
                "claim_validations": claim_validations,
            },
            "overall_assessment": overall_assessment,
            "confidence": faithfulness_metrics["confidence"],
            "evaluation_metadata": {
                "evaluator": "faithfulness",
                "evaluation_timestamp": datetime.now().isoformat(),
                "source_document_count": len(source_documents),
            },
        }

        logger.info(
            f"Faithfulness evaluation completed: score={faithfulness_metrics['overall_score']:.3f}"
        )
        return evaluation_result

    def _extract_claims(self, generated_answer: str) -> List[Dict[str, Any]]:
        """Extract factual claims from generated answer."""

        extraction_input = {
            "text": generated_answer,
            "extraction_task": "factual_claims",
            "claim_types": ["facts", "statistics", "assertions", "attributions"],
        }

        result = self.claim_extractor.run(
            provider="ollama",
            model="llama3.2:3b",
            messages=[{"role": "user", "content": json.dumps(extraction_input)}],
        )
        claims = result.get("extracted_claims", [])

        # Ensure claims have required structure
        structured_claims = []
        for i, claim in enumerate(claims):
            if isinstance(claim, str):
                structured_claims.append(
                    {
                        "claim_id": f"claim_{i}",
                        "claim_text": claim,
                        "claim_type": "general",
                        "confidence": 0.8,
                    }
                )
            else:
                structured_claims.append(claim)

        return structured_claims

    def _validate_claims(
        self, claims: List[Dict], source_documents: List[Dict]
    ) -> List[Dict[str, Any]]:
        """Validate claims against source documents."""

        source_content = " ".join([doc.get("content", "") for doc in source_documents])

        validations = []

        for claim in claims:
            validation_input = {
                "claim": claim["claim_text"],
                "source_content": source_content[:3000],  # Limit for processing
                "validation_task": "claim_support_verification",
                "validation_criteria": [
                    "direct_support",
                    "implicit_support",
                    "contradiction",
                    "no_evidence",
                ],
            }

            result = self.evidence_validator.run(
                provider="ollama",
                model="llama3.2:3b",
                messages=[{"role": "user", "content": json.dumps(validation_input)}],
            )
            validation = result.get("validation_result", {})

            validations.append(
                {
                    "claim_id": claim["claim_id"],
                    "claim_text": claim["claim_text"],
                    "is_supported": validation.get("is_supported", False),
                    "support_type": validation.get("support_type", "no_evidence"),
                    "support_evidence": validation.get("support_evidence", ""),
                    "confidence": validation.get("confidence", 0.5),
                    "contradictions": validation.get("contradictions", []),
                }
            )

        return validations

    def _assess_overall_faithfulness(
        self,
        query: str,
        answer: str,
        sources: List[Dict],
        claim_validations: List[Dict],
    ) -> Dict[str, Any]:
        """Assess overall faithfulness of the answer."""

        assessment_input = {
            "query": query,
            "generated_answer": answer,
            "source_documents": [doc.get("content", "")[:500] for doc in sources[:3]],
            "claim_validations": claim_validations,
            "assessment_criteria": self.evaluation_aspects,
        }

        result = self.faithfulness_assessor.run(
            provider="ollama",
            model="llama3.2:3b",
            messages=[{"role": "user", "content": json.dumps(assessment_input)}],
        )

        return result.get(
            "faithfulness_assessment",
            {
                "factual_consistency": 0.7,
                "source_attribution": 0.7,
                "claim_support": 0.7,
                "contradiction_detection": 0.7,
                "information_accuracy": 0.7,
                "overall_faithfulness": 0.7,
                "strengths": [],
                "weaknesses": [],
                "recommendations": [],
            },
        )

    def _calculate_faithfulness_metrics(
        self, claim_validations: List[Dict], overall_assessment: Dict
    ) -> Dict[str, Any]:
        """Calculate comprehensive faithfulness metrics."""

        # Claim-based metrics
        total_claims = len(claim_validations)
        supported_claims = sum(1 for c in claim_validations if c["is_supported"])
        claim_support_ratio = (
            supported_claims / total_claims if total_claims > 0 else 1.0
        )

        # Aspect scores from overall assessment
        aspect_scores = {}
        for aspect in self.evaluation_aspects:
            aspect_scores[aspect] = overall_assessment.get(aspect, 0.7)

        # Calculate overall score
        claim_weight = 0.4
        assessment_weight = 0.6

        overall_score = (
            claim_weight * claim_support_ratio
            + assessment_weight * overall_assessment.get("overall_faithfulness", 0.7)
        )

        # Calculate confidence
        all_scores = [claim_support_ratio] + list(aspect_scores.values())
        confidence = self._calculate_confidence(all_scores)

        return {
            "overall_score": self._normalize_score(overall_score),
            "claim_support_ratio": claim_support_ratio,
            "aspect_scores": aspect_scores,
            "confidence": confidence,
            "metrics_breakdown": {
                "claim_based_score": claim_support_ratio,
                "assessment_based_score": overall_assessment.get(
                    "overall_faithfulness", 0.7
                ),
                "weighted_combination": overall_score,
            },
        }

    def _get_faithfulness_assessment_prompt(self) -> str:
        """Get prompt for faithfulness assessment."""
        return """You are a faithfulness assessment specialist for RAG systems.

        Evaluate how faithful the generated answer is to the source documents:

        Assessment Criteria:
        - factual_consistency: Are facts consistent with sources?
        - source_attribution: Are claims properly attributable to sources?
        - claim_support: Are claims supported by evidence in sources?
        - contradiction_detection: Are there contradictions to source material?
        - information_accuracy: Is the information accurate and precise?

        Score each criterion from 0.0 to 1.0:
        - 1.0: Perfect faithfulness, fully supported by sources
        - 0.8-0.9: High faithfulness, well-supported
        - 0.6-0.7: Moderate faithfulness, mostly supported
        - 0.4-0.5: Low faithfulness, partially supported
        - 0.0-0.3: Poor faithfulness, unsupported or contradictory

        Return faithfulness_assessment with scores, strengths, weaknesses, and recommendations."""

    def _get_claim_extraction_prompt(self) -> str:
        """Get prompt for claim extraction."""
        return """You are a claim extraction specialist for factual verification.

        Extract all factual claims from the generated text:

        Claim Types:
        - Facts: Specific factual statements
        - Statistics: Numerical data and figures
        - Assertions: Claims about relationships or causation
        - Attributions: Claims about sources or origins

        For each claim, identify:
        - The specific factual statement
        - The type of claim
        - Confidence in claim extraction

        Return extracted_claims as a list of claim objects."""

    def _get_evidence_validation_prompt(self) -> str:
        """Get prompt for evidence validation."""
        return """You are an evidence validation specialist for source verification.

        Validate whether the claim is supported by the source content:

        Validation Categories:
        - direct_support: Explicitly stated in sources
        - implicit_support: Can be reasonably inferred from sources
        - contradiction: Contradicts information in sources
        - no_evidence: No relevant evidence found in sources

        Return validation_result with:
        - is_supported: boolean
        - support_type: validation category
        - support_evidence: specific supporting text
        - confidence: confidence in validation
        - contradictions: any contradictory evidence found"""

    def get_parameters(self) -> Dict[str, NodeParameter]:
        """Get node parameters for Kailash framework."""
        return {
            "query": NodeParameter(
                name="query",
                type=str,
                required=True,
                description="Query to evaluate faithfulness against",
            ),
            "generated_answer": NodeParameter(
                name="generated_answer",
                type=str,
                required=True,
                description="Generated answer to evaluate",
            ),
            "source_documents": NodeParameter(
                name="source_documents",
                type=list,
                required=True,
                description="Source documents for faithfulness verification",
            ),
        }

    def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Run method required by Kailash Node interface."""
        return self.process(inputs)

    def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Process inputs for Kailash workflow integration."""

        query = inputs.get("query", "")
        generated_answer = inputs.get("generated_answer", "")
        source_documents = inputs.get("source_documents", [])

        if not all([query, generated_answer, source_documents]):
            return {"error": "Query, generated answer, and source documents required"}

        result = self.evaluate(query, generated_answer, source_documents)

        return {
            "faithfulness_score": result["faithfulness_score"],
            "aspect_scores": result["aspect_scores"],
            "claim_analysis": result["claim_analysis"],
            "confidence": result["confidence"],
        }


class RelevancyEvaluatorNode(BaseEvaluationNode):
    """
    Evaluates relevancy of generated answers to user queries.
    Assesses query coverage, completeness, and appropriateness.
    """

    def __init__(self, name: str = "relevancy_evaluator", **kwargs):
        # Set attributes before calling super().__init__() as Kailash validates during init
        self.relevancy_dimensions = kwargs.get(
            "relevancy_dimensions",
            [
                "query_coverage",
                "information_completeness",
                "answer_focus",
                "directness",
                "specificity",
                "contextual_appropriateness",
            ],
        )

        super().__init__(name, **kwargs)

        # Relevancy assessor
        self.relevancy_assessor = LLMAgentNode(
            name=f"{name}_assessor",
            provider="ollama",
            model="llama3.2:3b",
            system_prompt=self._get_relevancy_assessment_prompt(),
            temperature=0.1,
        )

        # Query analyzer
        self.query_analyzer = LLMAgentNode(
            name=f"{name}_query_analyzer",
            provider="ollama",
            model="llama3.2:3b",
            system_prompt=self._get_query_analysis_prompt(),
            temperature=0.1,
        )

        logger.info(
            f"RelevancyEvaluatorNode initialized with {len(self.relevancy_dimensions)} dimensions"
        )

    def evaluate(
        self,
        query: str,
        generated_answer: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Evaluate relevancy of generated answer to query."""

        logger.info(f"Evaluating relevancy for query: '{query[:50]}...'")

        # Analyze query requirements
        query_analysis = self._analyze_query_requirements(query, context)

        # Assess answer relevancy
        relevancy_assessment = self._assess_answer_relevancy(
            query, generated_answer, query_analysis, context
        )

        # Calculate relevancy metrics
        relevancy_metrics = self._calculate_relevancy_metrics(
            query_analysis, relevancy_assessment
        )

        evaluation_result = {
            "query": query,
            "generated_answer": generated_answer,
            "relevancy_score": relevancy_metrics["overall_score"],
            "dimension_scores": relevancy_metrics["dimension_scores"],
            "query_analysis": query_analysis,
            "relevancy_assessment": relevancy_assessment,
            "confidence": relevancy_metrics["confidence"],
            "evaluation_metadata": {
                "evaluator": "relevancy",
                "evaluation_timestamp": datetime.now().isoformat(),
                "dimensions_evaluated": len(self.relevancy_dimensions),
            },
        }

        logger.info(
            f"Relevancy evaluation completed: score={relevancy_metrics['overall_score']:.3f}"
        )
        return evaluation_result

    def _analyze_query_requirements(
        self, query: str, context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Analyze what the query is asking for."""

        analysis_input = {
            "query": query,
            "context": context or {},
            "analysis_focus": [
                "information_need",
                "query_intent",
                "expected_answer_type",
                "specificity_level",
                "scope",
                "complexity",
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
                "information_need": "factual",
                "query_intent": "informational",
                "expected_answer_type": "descriptive",
                "specificity_level": "medium",
                "scope": "focused",
                "complexity": "medium",
                "key_aspects": [],
                "success_criteria": [],
            },
        )

    def _assess_answer_relevancy(
        self,
        query: str,
        answer: str,
        query_analysis: Dict,
        context: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Assess how well the answer addresses the query."""

        assessment_input = {
            "query": query,
            "generated_answer": answer,
            "query_analysis": query_analysis,
            "context": context or {},
            "assessment_dimensions": self.relevancy_dimensions,
        }

        result = self.relevancy_assessor.run(
            provider="ollama",
            model="llama3.2:3b",
            messages=[{"role": "user", "content": json.dumps(assessment_input)}],
        )

        return result.get(
            "relevancy_assessment",
            {
                "query_coverage": 0.7,
                "information_completeness": 0.7,
                "answer_focus": 0.7,
                "directness": 0.7,
                "specificity": 0.7,
                "contextual_appropriateness": 0.7,
                "overall_relevancy": 0.7,
                "coverage_analysis": {},
                "improvement_suggestions": [],
            },
        )

    def _calculate_relevancy_metrics(
        self, query_analysis: Dict, relevancy_assessment: Dict
    ) -> Dict[str, Any]:
        """Calculate comprehensive relevancy metrics."""

        # Dimension scores
        dimension_scores = {}
        for dimension in self.relevancy_dimensions:
            dimension_scores[dimension] = relevancy_assessment.get(dimension, 0.7)

        # Calculate weighted overall score
        dimension_weights = self._get_dimension_weights(query_analysis)
        weighted_score = sum(
            dimension_scores[dim] * dimension_weights.get(dim, 1.0)
            for dim in self.relevancy_dimensions
        ) / sum(dimension_weights.values())

        # Calculate confidence
        all_scores = list(dimension_scores.values())
        confidence = self._calculate_confidence(all_scores)

        return {
            "overall_score": self._normalize_score(weighted_score),
            "dimension_scores": dimension_scores,
            "weighted_score": weighted_score,
            "confidence": confidence,
            "dimension_weights": dimension_weights,
        }

    def _get_dimension_weights(self, query_analysis: Dict) -> Dict[str, float]:
        """Get dimension weights based on query characteristics."""

        # Default weights
        weights = {
            "query_coverage": 1.0,
            "information_completeness": 1.0,
            "answer_focus": 1.0,
            "directness": 1.0,
            "specificity": 1.0,
            "contextual_appropriateness": 1.0,
        }

        # Adjust weights based on query analysis
        complexity = query_analysis.get("complexity", "medium")
        specificity = query_analysis.get("specificity_level", "medium")

        if complexity == "high":
            weights["information_completeness"] = 1.5
            weights["query_coverage"] = 1.3

        if specificity == "high":
            weights["specificity"] = 1.4
            weights["directness"] = 1.2

        return weights

    def _get_relevancy_assessment_prompt(self) -> str:
        """Get prompt for relevancy assessment."""
        return """You are a relevancy assessment specialist for question-answering systems.

        Evaluate how well the generated answer addresses the query:

        Assessment Dimensions:
        - query_coverage: How completely does the answer address the query?
        - information_completeness: How complete is the information provided?
        - answer_focus: How focused and on-topic is the answer?
        - directness: How directly does it answer the specific question?
        - specificity: How specific and detailed is the answer?
        - contextual_appropriateness: How appropriate is it for the context?

        Score each dimension from 0.0 to 1.0:
        - 1.0: Excellent - fully satisfies the dimension
        - 0.8-0.9: Good - mostly satisfies with minor gaps
        - 0.6-0.7: Adequate - satisfies but with notable limitations
        - 0.4-0.5: Poor - partially satisfies with significant gaps
        - 0.0-0.3: Very poor - fails to satisfy the dimension

        Return relevancy_assessment with scores and detailed analysis."""

    def _get_query_analysis_prompt(self) -> str:
        """Get prompt for query analysis."""
        return """You are a query analysis specialist for understanding information needs.

        Analyze what the query is asking for:

        Analysis Dimensions:
        - information_need: What type of information is needed?
        - query_intent: What is the user trying to accomplish?
        - expected_answer_type: What format should the answer take?
        - specificity_level: How specific vs. general is the query?
        - scope: How broad vs. narrow is the information scope?
        - complexity: How complex is the information need?

        Also identify:
        - key_aspects: Main aspects the answer should cover
        - success_criteria: What would make an answer successful?

        Return query_analysis with comprehensive understanding of requirements."""

    def get_parameters(self) -> Dict[str, NodeParameter]:
        """Get node parameters for Kailash framework."""
        return {
            "query": NodeParameter(
                name="query",
                type=str,
                required=True,
                description="Query to evaluate relevancy against",
            ),
            "generated_answer": NodeParameter(
                name="generated_answer",
                type=str,
                required=True,
                description="Generated answer to evaluate",
            ),
            "context": NodeParameter(
                name="context",
                type=dict,
                required=False,
                default={},
                description="Optional context for evaluation",
            ),
        }

    def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Run method required by Kailash Node interface."""
        return self.process(inputs)

    def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Process inputs for Kailash workflow integration."""

        query = inputs.get("query", "")
        generated_answer = inputs.get("generated_answer", "")
        context = inputs.get("context", {})

        if not all([query, generated_answer]):
            return {"error": "Query and generated answer required"}

        result = self.evaluate(query, generated_answer, context)

        return {
            "relevancy_score": result["relevancy_score"],
            "dimension_scores": result["dimension_scores"],
            "query_analysis": result["query_analysis"],
            "confidence": result["confidence"],
        }


class HallucinationDetectorNode(BaseEvaluationNode):
    """
    Detects hallucinations in generated content by identifying
    unsupported claims and fabricated information.
    """

    def __init__(self, name: str = "hallucination_detector", **kwargs):
        # Set attributes before calling super().__init__() as Kailash validates during init
        self.detection_types = kwargs.get(
            "detection_types",
            [
                "factual_hallucination",
                "entity_hallucination",
                "statistical_hallucination",
                "attribution_hallucination",
                "logical_inconsistency",
            ],
        )

        super().__init__(name, **kwargs)

        # Hallucination detector
        self.hallucination_detector = LLMAgentNode(
            name=f"{name}_detector",
            provider="ollama",
            model="llama3.2:3b",
            system_prompt=self._get_hallucination_detection_prompt(),
            temperature=0.0,
        )

        # Fact checker
        self.fact_checker = LLMAgentNode(
            name=f"{name}_fact_checker",
            provider="ollama",
            model="llama3.2:3b",
            system_prompt=self._get_fact_checking_prompt(),
            temperature=0.0,
        )

        # Consistency analyzer
        self.consistency_analyzer = LLMAgentNode(
            name=f"{name}_consistency_analyzer",
            provider="ollama",
            model="llama3.2:3b",
            system_prompt=self._get_consistency_analysis_prompt(),
            temperature=0.0,
        )

        logger.info(
            f"HallucinationDetectorNode initialized with {len(self.detection_types)} types"
        )

    def evaluate(
        self,
        generated_answer: str,
        source_documents: List[Dict[str, Any]],
        query: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Detect hallucinations in generated content."""

        logger.info(
            f"Detecting hallucinations in {len(generated_answer)} character response"
        )

        # Extract statements for fact-checking
        statements = self._extract_checkable_statements(generated_answer)

        # Check statements against sources
        fact_check_results = self._fact_check_statements(statements, source_documents)

        # Detect different types of hallucinations
        hallucination_analysis = self._analyze_hallucinations(
            generated_answer, source_documents, fact_check_results, query
        )

        # Check internal consistency
        consistency_analysis = self._analyze_consistency(generated_answer)

        # Calculate hallucination metrics
        hallucination_metrics = self._calculate_hallucination_metrics(
            fact_check_results, hallucination_analysis, consistency_analysis
        )

        evaluation_result = {
            "generated_answer": generated_answer,
            "hallucination_score": hallucination_metrics["hallucination_rate"],
            "detection_results": hallucination_analysis,
            "fact_check_results": fact_check_results,
            "consistency_analysis": consistency_analysis,
            "detected_hallucinations": hallucination_metrics["detected_hallucinations"],
            "confidence": hallucination_metrics["confidence"],
            "evaluation_metadata": {
                "evaluator": "hallucination_detector",
                "evaluation_timestamp": datetime.now().isoformat(),
                "statements_checked": len(statements),
                "source_document_count": len(source_documents),
            },
        }

        logger.info(
            f"Hallucination detection completed: rate={hallucination_metrics['hallucination_rate']:.3f}"
        )
        return evaluation_result

    def _extract_checkable_statements(
        self, generated_answer: str
    ) -> List[Dict[str, Any]]:
        """Extract statements that can be fact-checked."""

        # Simple sentence splitting (in practice, use more sophisticated NLP)
        sentences = generated_answer.split(". ")

        checkable_statements = []
        for i, sentence in enumerate(sentences):
            if len(sentence.strip()) > 10:  # Skip very short sentences
                checkable_statements.append(
                    {
                        "statement_id": f"stmt_{i}",
                        "statement_text": sentence.strip(),
                        "statement_type": self._classify_statement_type(sentence),
                        "position": i,
                    }
                )

        return checkable_statements

    def _classify_statement_type(self, statement: str) -> str:
        """Classify type of statement for targeted checking."""

        statement_lower = statement.lower()

        if any(
            word in statement_lower
            for word in ["according to", "research shows", "study found"]
        ):
            return "attribution"
        elif any(char.isdigit() for char in statement):
            return "statistical"
        elif any(
            word in statement_lower
            for word in ["is", "are", "was", "were", "has", "have"]
        ):
            return "factual"
        else:
            return "general"

    def _fact_check_statements(
        self, statements: List[Dict], source_documents: List[Dict]
    ) -> List[Dict[str, Any]]:
        """Fact-check statements against source documents."""

        source_content = " ".join([doc.get("content", "") for doc in source_documents])

        fact_check_results = []

        for statement in statements:
            check_input = {
                "statement": statement["statement_text"],
                "source_content": source_content[:3000],  # Limit for processing
                "statement_type": statement["statement_type"],
                "fact_check_criteria": [
                    "factual_accuracy",
                    "source_support",
                    "consistency",
                ],
            }

            result = self.fact_checker.run(
                provider="ollama",
                model="llama3.2:3b",
                messages=[{"role": "user", "content": json.dumps(check_input)}],
            )
            fact_check = result.get("fact_check_result", {})

            fact_check_results.append(
                {
                    "statement_id": statement["statement_id"],
                    "statement_text": statement["statement_text"],
                    "is_supported": fact_check.get("is_supported", False),
                    "support_level": fact_check.get("support_level", "none"),
                    "contradicts_source": fact_check.get("contradicts_source", False),
                    "evidence": fact_check.get("supporting_evidence", ""),
                    "confidence": fact_check.get("confidence", 0.5),
                }
            )

        return fact_check_results

    def _analyze_hallucinations(
        self,
        generated_answer: str,
        source_documents: List[Dict],
        fact_check_results: List[Dict],
        query: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Analyze different types of hallucinations."""

        analysis_input = {
            "generated_answer": generated_answer,
            "source_documents": [
                doc.get("content", "")[:500] for doc in source_documents[:3]
            ],
            "fact_check_results": fact_check_results,
            "query": query or "",
            "detection_types": self.detection_types,
        }

        result = self.hallucination_detector.run(
            provider="ollama",
            model="llama3.2:3b",
            messages=[{"role": "user", "content": json.dumps(analysis_input)}],
        )

        return result.get(
            "hallucination_analysis",
            {
                "factual_hallucination": {"detected": False, "examples": []},
                "entity_hallucination": {"detected": False, "examples": []},
                "statistical_hallucination": {"detected": False, "examples": []},
                "attribution_hallucination": {"detected": False, "examples": []},
                "logical_inconsistency": {"detected": False, "examples": []},
                "overall_assessment": "low_risk",
            },
        )

    def _analyze_consistency(self, generated_answer: str) -> Dict[str, Any]:
        """Analyze internal consistency of the generated answer."""

        consistency_input = {
            "text": generated_answer,
            "consistency_criteria": [
                "logical_consistency",
                "factual_consistency",
                "temporal_consistency",
                "causal_consistency",
            ],
        }

        result = self.consistency_analyzer.run(
            provider="ollama",
            model="llama3.2:3b",
            messages=[{"role": "user", "content": json.dumps(consistency_input)}],
        )

        return result.get(
            "consistency_analysis",
            {
                "logical_consistency": 0.8,
                "factual_consistency": 0.8,
                "temporal_consistency": 0.8,
                "causal_consistency": 0.8,
                "overall_consistency": 0.8,
                "inconsistencies_found": [],
                "consistency_issues": [],
            },
        )

    def _calculate_hallucination_metrics(
        self,
        fact_check_results: List[Dict],
        hallucination_analysis: Dict,
        consistency_analysis: Dict,
    ) -> Dict[str, Any]:
        """Calculate comprehensive hallucination metrics."""

        # Statement-level metrics
        total_statements = len(fact_check_results)
        unsupported_statements = sum(
            1 for r in fact_check_results if not r["is_supported"]
        )
        contradictory_statements = sum(
            1 for r in fact_check_results if r["contradicts_source"]
        )

        statement_hallucination_rate = (
            (unsupported_statements + contradictory_statements) / total_statements
            if total_statements > 0
            else 0
        )

        # Type-specific detection
        detected_types = sum(
            1
            for analysis in hallucination_analysis.values()
            if isinstance(analysis, dict) and analysis.get("detected", False)
        )

        # Consistency score
        consistency_score = consistency_analysis.get("overall_consistency", 0.8)

        # Overall hallucination rate
        overall_rate = (
            0.5 * statement_hallucination_rate
            + 0.3 * (detected_types / len(self.detection_types))
            + 0.2 * (1.0 - consistency_score)
        )

        # Collect detected hallucinations
        detected_hallucinations = []
        for hallucination_type, analysis in hallucination_analysis.items():
            if isinstance(analysis, dict) and analysis.get("detected", False):
                detected_hallucinations.extend(
                    [
                        {"type": hallucination_type, "example": example}
                        for example in analysis.get("examples", [])
                    ]
                )

        # Calculate confidence
        confidence_scores = [
            1.0 - statement_hallucination_rate,
            consistency_score,
            1.0 - (detected_types / len(self.detection_types)),
        ]
        confidence = self._calculate_confidence(confidence_scores)

        return {
            "hallucination_rate": self._normalize_score(overall_rate),
            "statement_hallucination_rate": statement_hallucination_rate,
            "type_detection_rate": detected_types / len(self.detection_types),
            "consistency_score": consistency_score,
            "detected_hallucinations": detected_hallucinations,
            "confidence": confidence,
            "metrics_breakdown": {
                "unsupported_statements": unsupported_statements,
                "contradictory_statements": contradictory_statements,
                "total_statements": total_statements,
                "detected_types": detected_types,
            },
        }

    def _get_hallucination_detection_prompt(self) -> str:
        """Get prompt for hallucination detection."""
        return """You are a hallucination detection specialist for AI-generated content.

        Detect different types of hallucinations in the generated answer:

        Hallucination Types:
        - factual_hallucination: False or unverifiable facts
        - entity_hallucination: Non-existent people, places, or organizations
        - statistical_hallucination: Fabricated numbers or data
        - attribution_hallucination: False citations or source attributions
        - logical_inconsistency: Contradictory statements within the text

        For each type, determine:
        - Whether hallucinations are detected
        - Specific examples of hallucinations found
        - Severity and confidence level

        Return hallucination_analysis with detection results for each type."""

    def _get_fact_checking_prompt(self) -> str:
        """Get prompt for fact checking."""
        return """You are a fact-checking specialist for verifying AI-generated statements.

        Check the statement against the provided source content:

        Verification Criteria:
        - Is the statement factually accurate?
        - Is it supported by the source content?
        - Does it contradict any information in the sources?
        - What level of support exists (strong, weak, none)?

        Return fact_check_result with:
        - is_supported: boolean
        - support_level: none, weak, moderate, strong
        - contradicts_source: boolean
        - supporting_evidence: relevant text from sources
        - confidence: confidence in fact-check assessment"""

    def _get_consistency_analysis_prompt(self) -> str:
        """Get prompt for consistency analysis."""
        return """You are a consistency analysis specialist for text evaluation.

        Analyze the internal consistency of the text:

        Consistency Types:
        - logical_consistency: Are statements logically consistent?
        - factual_consistency: Are facts consistent throughout?
        - temporal_consistency: Are temporal references consistent?
        - causal_consistency: Are cause-effect relationships consistent?

        Identify any inconsistencies, contradictions, or logical problems.

        Return consistency_analysis with scores and detailed findings."""

    def get_parameters(self) -> Dict[str, NodeParameter]:
        """Get node parameters for Kailash framework."""
        return {
            "generated_answer": NodeParameter(
                name="generated_answer",
                type=str,
                required=True,
                description="Generated answer to check for hallucinations",
            ),
            "source_documents": NodeParameter(
                name="source_documents",
                type=list,
                required=True,
                description="Source documents for verification",
            ),
            "query": NodeParameter(
                name="query",
                type=str,
                required=False,
                default="",
                description="Optional query for context",
            ),
        }

    def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Run method required by Kailash Node interface."""
        return self.process(inputs)

    def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Process inputs for Kailash workflow integration."""

        generated_answer = inputs.get("generated_answer", "")
        source_documents = inputs.get("source_documents", [])
        query = inputs.get("query", "")

        if not all([generated_answer, source_documents]):
            return {"error": "Generated answer and source documents required"}

        result = self.evaluate(generated_answer, source_documents, query)

        return {
            "hallucination_rate": result["hallucination_score"],
            "detected_hallucinations": result["detected_hallucinations"],
            "consistency_score": result["consistency_analysis"]["overall_consistency"],
            "confidence": result["confidence"],
        }


class PerformanceMetricsNode(BaseEvaluationNode):
    """
    Comprehensive performance metrics calculator for RAG systems.
    Aggregates and analyzes multiple evaluation dimensions.
    """

    def __init__(self, name: str = "performance_metrics", **kwargs):
        # Set attributes before calling super().__init__() as Kailash validates during init
        self.metric_categories = kwargs.get(
            "metric_categories",
            [
                "retrieval_quality",
                "generation_quality",
                "system_efficiency",
                "user_satisfaction",
                "robustness",
            ],
        )

        super().__init__(name, **kwargs)

        # Metrics aggregator
        self.metrics_aggregator = DataTransformer(
            name=f"{name}_aggregator",
            transformations=[
                "result = aggregate_evaluation_scores(evaluation_results)",
                "result = calculate_composite_metrics(result)",
                "result = generate_performance_insights(result)",
            ],
        )

        logger.info(
            f"PerformanceMetricsNode initialized with {len(self.metric_categories)} categories"
        )

    def evaluate(
        self,
        evaluation_results: Dict[str, Any],
        system_metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Calculate comprehensive performance metrics."""

        logger.info("Calculating comprehensive performance metrics")

        # Extract individual evaluation scores
        individual_scores = self._extract_individual_scores(evaluation_results)

        # Calculate category-level metrics
        category_metrics = self._calculate_category_metrics(individual_scores)

        # Calculate composite metrics
        composite_metrics = self._calculate_composite_metrics(category_metrics)

        # Generate performance insights
        performance_insights = self._generate_performance_insights(
            individual_scores, category_metrics, composite_metrics
        )

        # Calculate benchmarking scores
        benchmarking_scores = self._calculate_benchmarking_scores(composite_metrics)

        metrics_result = {
            "individual_scores": individual_scores,
            "category_metrics": category_metrics,
            "composite_metrics": composite_metrics,
            "performance_insights": performance_insights,
            "benchmarking_scores": benchmarking_scores,
            "overall_performance": composite_metrics.get("overall_performance", 0.7),
            "evaluation_metadata": {
                "metrics_calculator": "performance_metrics",
                "calculation_timestamp": datetime.now().isoformat(),
                "system_metadata": system_metadata or {},
            },
        }

        logger.info(
            f"Performance metrics calculated: overall={composite_metrics.get('overall_performance', 0.7):.3f}"
        )
        return metrics_result

    def _extract_individual_scores(
        self, evaluation_results: Dict[str, Any]
    ) -> Dict[str, float]:
        """Extract individual evaluation scores from results."""

        scores = {}

        # Faithfulness scores
        if "faithfulness" in evaluation_results:
            faithfulness = evaluation_results["faithfulness"]
            scores["faithfulness"] = faithfulness.get("faithfulness_score", 0.7)
            scores["claim_support"] = faithfulness.get("claim_analysis", {}).get(
                "supported_claims", 0
            ) / max(1, faithfulness.get("claim_analysis", {}).get("total_claims", 1))

        # Relevancy scores
        if "relevancy" in evaluation_results:
            relevancy = evaluation_results["relevancy"]
            scores["relevancy"] = relevancy.get("relevancy_score", 0.7)
            scores["query_coverage"] = relevancy.get("dimension_scores", {}).get(
                "query_coverage", 0.7
            )
            scores["completeness"] = relevancy.get("dimension_scores", {}).get(
                "information_completeness", 0.7
            )

        # Hallucination scores (inverse)
        if "hallucination" in evaluation_results:
            hallucination = evaluation_results["hallucination"]
            scores["anti_hallucination"] = 1.0 - hallucination.get(
                "hallucination_score", 0.3
            )
            scores["consistency"] = hallucination.get("consistency_analysis", {}).get(
                "overall_consistency", 0.8
            )

        # Retrieval metrics (if available)
        if "retrieval_metrics" in evaluation_results:
            retrieval = evaluation_results["retrieval_metrics"]
            scores["retrieval_precision"] = retrieval.get("precision_at_10", 0.7)
            scores["retrieval_recall"] = retrieval.get("recall_at_10", 0.7)
            scores["retrieval_ndcg"] = retrieval.get("ndcg_at_10", 0.7)

        # Efficiency metrics (if available)
        if "efficiency_metrics" in evaluation_results:
            efficiency = evaluation_results["efficiency_metrics"]
            scores["response_time"] = 1.0 - min(
                1.0, efficiency.get("total_latency", 1000) / 5000
            )  # Normalize to 5s max
            scores["cost_efficiency"] = 1.0 - min(
                1.0, efficiency.get("cost_per_query", 0.1) / 1.0
            )  # Normalize to $1 max

        return scores

    def _calculate_category_metrics(
        self, individual_scores: Dict[str, float]
    ) -> Dict[str, float]:
        """Calculate category-level metrics."""

        category_metrics = {}

        # Retrieval Quality
        retrieval_scores = [
            individual_scores.get("retrieval_precision", 0.7),
            individual_scores.get("retrieval_recall", 0.7),
            individual_scores.get("retrieval_ndcg", 0.7),
        ]
        category_metrics["retrieval_quality"] = np.mean(retrieval_scores)

        # Generation Quality
        generation_scores = [
            individual_scores.get("faithfulness", 0.7),
            individual_scores.get("relevancy", 0.7),
            individual_scores.get("anti_hallucination", 0.7),
            individual_scores.get("consistency", 0.8),
        ]
        category_metrics["generation_quality"] = np.mean(generation_scores)

        # System Efficiency
        efficiency_scores = [
            individual_scores.get("response_time", 0.8),
            individual_scores.get("cost_efficiency", 0.8),
        ]
        category_metrics["system_efficiency"] = np.mean(efficiency_scores)

        # User Satisfaction (derived from quality metrics)
        satisfaction_scores = [
            individual_scores.get("relevancy", 0.7),
            individual_scores.get("completeness", 0.7),
            individual_scores.get("query_coverage", 0.7),
        ]
        category_metrics["user_satisfaction"] = np.mean(satisfaction_scores)

        # Robustness (based on consistency and anti-hallucination)
        robustness_scores = [
            individual_scores.get("anti_hallucination", 0.7),
            individual_scores.get("consistency", 0.8),
            individual_scores.get("faithfulness", 0.7),
        ]
        category_metrics["robustness"] = np.mean(robustness_scores)

        return category_metrics

    def _calculate_composite_metrics(
        self, category_metrics: Dict[str, float]
    ) -> Dict[str, float]:
        """Calculate composite performance metrics."""

        composite_metrics = {}

        # Overall Performance (weighted average)
        weights = {
            "generation_quality": 0.35,
            "retrieval_quality": 0.25,
            "user_satisfaction": 0.2,
            "robustness": 0.15,
            "system_efficiency": 0.05,
        }

        overall_performance = sum(
            category_metrics.get(category, 0.7) * weight
            for category, weight in weights.items()
        )
        composite_metrics["overall_performance"] = overall_performance

        # Quality Index (focus on accuracy and relevance)
        quality_index = (
            0.4 * category_metrics.get("generation_quality", 0.7)
            + 0.3 * category_metrics.get("retrieval_quality", 0.7)
            + 0.3 * category_metrics.get("robustness", 0.7)
        )
        composite_metrics["quality_index"] = quality_index

        # User Experience Index
        ux_index = (
            0.5 * category_metrics.get("user_satisfaction", 0.7)
            + 0.3 * category_metrics.get("generation_quality", 0.7)
            + 0.2 * category_metrics.get("system_efficiency", 0.8)
        )
        composite_metrics["user_experience_index"] = ux_index

        # Production Readiness Score
        production_score = (
            0.3 * category_metrics.get("robustness", 0.7)
            + 0.25 * category_metrics.get("system_efficiency", 0.8)
            + 0.25 * category_metrics.get("generation_quality", 0.7)
            + 0.2 * category_metrics.get("retrieval_quality", 0.7)
        )
        composite_metrics["production_readiness"] = production_score

        return composite_metrics

    def _generate_performance_insights(
        self, individual_scores: Dict, category_metrics: Dict, composite_metrics: Dict
    ) -> Dict[str, Any]:
        """Generate actionable performance insights."""

        insights = {
            "strengths": [],
            "weaknesses": [],
            "recommendations": [],
            "performance_summary": "",
        }

        # Identify strengths (scores > 0.8)
        for metric, score in {**individual_scores, **category_metrics}.items():
            if score > 0.8:
                insights["strengths"].append(f"{metric}: {score:.3f}")

        # Identify weaknesses (scores < 0.6)
        for metric, score in {**individual_scores, **category_metrics}.items():
            if score < 0.6:
                insights["weaknesses"].append(f"{metric}: {score:.3f}")

        # Generate recommendations
        if category_metrics.get("retrieval_quality", 0.7) < 0.6:
            insights["recommendations"].append(
                "Improve retrieval quality with better indexing or reranking"
            )

        if category_metrics.get("generation_quality", 0.7) < 0.6:
            insights["recommendations"].append(
                "Enhance generation quality with better prompting or model tuning"
            )

        if category_metrics.get("system_efficiency", 0.8) < 0.7:
            insights["recommendations"].append(
                "Optimize system efficiency through caching and parallelization"
            )

        # Performance summary
        overall = composite_metrics.get("overall_performance", 0.7)
        if overall > 0.8:
            insights["performance_summary"] = (
                "Excellent performance across most metrics"
            )
        elif overall > 0.7:
            insights["performance_summary"] = (
                "Good performance with room for improvement"
            )
        elif overall > 0.6:
            insights["performance_summary"] = "Adequate performance, needs optimization"
        else:
            insights["performance_summary"] = (
                "Poor performance, requires significant improvement"
            )

        return insights

    def _calculate_benchmarking_scores(
        self, composite_metrics: Dict[str, float]
    ) -> Dict[str, Any]:
        """Calculate benchmarking scores against industry standards."""

        # Industry benchmark thresholds (example values)
        benchmarks = {
            "research_grade": {
                "threshold": 0.85,
                "description": "Research-quality system",
            },
            "production_grade": {
                "threshold": 0.75,
                "description": "Production-ready system",
            },
            "prototype_grade": {
                "threshold": 0.65,
                "description": "Prototype-quality system",
            },
            "development_grade": {
                "threshold": 0.5,
                "description": "Development-stage system",
            },
        }

        overall_performance = composite_metrics.get("overall_performance", 0.7)

        benchmarking_scores = {}
        achieved_grade = "development_grade"

        for grade, benchmark in benchmarks.items():
            meets_benchmark = overall_performance >= benchmark["threshold"]
            benchmarking_scores[grade] = {
                "meets_benchmark": meets_benchmark,
                "threshold": benchmark["threshold"],
                "description": benchmark["description"],
                "gap": max(0, benchmark["threshold"] - overall_performance),
            }

            if meets_benchmark:
                achieved_grade = grade

        benchmarking_scores["achieved_grade"] = achieved_grade
        benchmarking_scores["overall_score"] = overall_performance

        return benchmarking_scores

    def get_parameters(self) -> Dict[str, NodeParameter]:
        """Get node parameters for Kailash framework."""
        return {
            "evaluation_results": NodeParameter(
                name="evaluation_results",
                type=dict,
                required=True,
                description="Evaluation results from other evaluation nodes",
            ),
            "system_metadata": NodeParameter(
                name="system_metadata",
                type=dict,
                required=False,
                default={},
                description="Optional system metadata for performance analysis",
            ),
        }

    def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Run method required by Kailash Node interface."""
        return self.process(inputs)

    def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Process inputs for Kailash workflow integration."""

        evaluation_results = inputs.get("evaluation_results", {})
        system_metadata = inputs.get("system_metadata", {})

        if not evaluation_results:
            return {"error": "Evaluation results required"}

        result = self.evaluate(evaluation_results, system_metadata)

        return {
            "overall_performance": result["overall_performance"],
            "category_metrics": result["category_metrics"],
            "composite_metrics": result["composite_metrics"],
            "performance_insights": result["performance_insights"],
            "achieved_grade": result["benchmarking_scores"]["achieved_grade"],
        }
