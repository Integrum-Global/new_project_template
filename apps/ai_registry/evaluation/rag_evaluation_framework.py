"""
RAG Evaluation Framework - Comprehensive Testing and Benchmarking

This framework provides extensive evaluation capabilities for all advanced RAG techniques,
including automated benchmarking, performance comparison, and optimal configuration selection.
"""

import json
import logging
import time
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from kailash import Workflow
from kailash.nodes.ai import EmbeddingGeneratorNode, LLMAgentNode
from kailash.nodes.transform import DataTransformer
from kailash.runtime import LocalRuntime

logger = logging.getLogger(__name__)


@dataclass
class EvaluationMetrics:
    """Comprehensive evaluation metrics for RAG systems."""

    # Retrieval Metrics
    hit_at_k: Dict[int, float]  # Hit@1, Hit@5, Hit@10, etc.
    mrr: float  # Mean Reciprocal Rank
    ndcg_at_k: Dict[int, float]  # Normalized Discounted Cumulative Gain
    map_score: float  # Mean Average Precision
    recall_at_k: Dict[int, float]  # Recall@K
    precision_at_k: Dict[int, float]  # Precision@K

    # Generation Metrics
    faithfulness: float  # How faithful is generated answer to sources
    answer_relevancy: float  # How relevant is answer to query
    context_precision: float  # Precision of retrieved context
    context_recall: float  # Recall of relevant context

    # Efficiency Metrics
    retrieval_latency: float  # Time to retrieve documents (ms)
    generation_latency: float  # Time to generate response (ms)
    total_latency: float  # End-to-end latency (ms)
    cost_per_query: float  # Computational cost per query

    # Quality Metrics
    coherence: float  # Response coherence score
    completeness: float  # Response completeness score
    accuracy: float  # Factual accuracy score
    hallucination_rate: float  # Rate of hallucinated content

    # Advanced Metrics
    diversity_score: float  # Diversity of retrieved results
    coverage_score: float  # Coverage of query aspects
    novelty_score: float  # Novelty of retrieved information
    explainability_score: float  # How explainable are the results


@dataclass
class RAGConfiguration:
    """Configuration for a specific RAG system setup."""

    name: str
    retrieval_method: str
    chunking_strategy: str
    embedding_model: str
    reranking_method: str
    generation_model: str
    fusion_strategy: Optional[str] = None
    compression_method: Optional[str] = None
    query_transformation: Optional[str] = None
    parameters: Dict[str, Any] = None


class EvaluationDataset:
    """Evaluation dataset with ground truth for RAG assessment."""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.queries = []
        self.ground_truth = {}
        self.contexts = {}
        self.metadata = {}

    def add_query(
        self,
        query_id: str,
        query: str,
        relevant_docs: List[str],
        ideal_answer: str,
        query_type: str = "general",
        difficulty: str = "medium",
        domain: str = "general",
    ):
        """Add a query with ground truth to the dataset."""

        self.queries.append(
            {
                "id": query_id,
                "query": query,
                "type": query_type,
                "difficulty": difficulty,
                "domain": domain,
            }
        )

        self.ground_truth[query_id] = {
            "relevant_docs": relevant_docs,
            "ideal_answer": ideal_answer,
            "relevance_scores": {
                doc: 1.0 for doc in relevant_docs
            },  # Binary relevance by default
        }

    def add_graded_relevance(self, query_id: str, doc_id: str, relevance_score: float):
        """Add graded relevance score for more nuanced evaluation."""
        if query_id not in self.ground_truth:
            raise ValueError(f"Query {query_id} not found in dataset")

        self.ground_truth[query_id]["relevance_scores"][doc_id] = relevance_score

    def get_query_subset(
        self, query_type: str = None, difficulty: str = None, domain: str = None
    ) -> List[Dict]:
        """Get subset of queries based on filters."""

        filtered_queries = self.queries

        if query_type:
            filtered_queries = [q for q in filtered_queries if q["type"] == query_type]
        if difficulty:
            filtered_queries = [
                q for q in filtered_queries if q["difficulty"] == difficulty
            ]
        if domain:
            filtered_queries = [q for q in filtered_queries if q["domain"] == domain]

        return filtered_queries


class RAGEvaluationHarness:
    """
    Comprehensive evaluation harness for testing and benchmarking
    different RAG configurations and techniques.
    """

    def __init__(self, output_dir: str = "evaluation_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        self.runtime = LocalRuntime()
        self.evaluator_llm = LLMAgentNode(
            name="evaluator",
            model="gpt-4o-mini",
            system_prompt=self._get_evaluation_prompt(),
        )

        # Initialize evaluation components
        self.faithfulness_evaluator = self._create_faithfulness_evaluator()
        self.relevancy_evaluator = self._create_relevancy_evaluator()
        self.hallucination_detector = self._create_hallucination_detector()

        # Results storage
        self.evaluation_results = {}
        self.benchmark_history = []

        logger.info("RAG Evaluation Harness initialized")

    def create_section7_evaluation_dataset(self) -> EvaluationDataset:
        """Create evaluation dataset for Section 7 AI use cases."""

        dataset = EvaluationDataset(
            name="Section7_AI_UseCases",
            description="Evaluation dataset for ISO/IEC TR 24030 Section 7 AI use cases",
        )

        # Healthcare queries
        dataset.add_query(
            "HC001",
            "What AI use cases exist for medical diagnosis in healthcare?",
            ["section_7_1_healthcare", "medical_diagnosis_subsection"],
            "AI is used in healthcare for various diagnostic applications including medical imaging analysis, symptom assessment, and clinical decision support systems.",
            query_type="domain_specific",
            difficulty="medium",
            domain="healthcare",
        )

        dataset.add_query(
            "HC002",
            "How is machine learning applied to radiology and medical imaging?",
            ["radiology_use_cases", "medical_imaging_ai"],
            "Machine learning in radiology involves automated image analysis, anomaly detection, and diagnostic assistance for X-rays, MRIs, and CT scans.",
            query_type="technical",
            difficulty="medium",
            domain="healthcare",
        )

        # Finance queries
        dataset.add_query(
            "FN001",
            "What are the AI applications in financial risk assessment?",
            ["section_7_financial_services", "risk_assessment_ai"],
            "AI in finance is used for credit scoring, fraud detection, algorithmic trading, and regulatory compliance monitoring.",
            query_type="domain_specific",
            difficulty="medium",
            domain="finance",
        )

        # Transportation queries
        dataset.add_query(
            "TR001",
            "How is AI used in autonomous vehicle development?",
            ["autonomous_vehicles_section", "transportation_ai"],
            "AI in autonomous vehicles includes computer vision for object detection, path planning algorithms, and sensor fusion technologies.",
            query_type="technical",
            difficulty="hard",
            domain="transportation",
        )

        # Complex multi-domain queries
        dataset.add_query(
            "MD001",
            "Compare AI implementations across healthcare, finance, and transportation domains",
            [
                "section_7_1_healthcare",
                "section_7_financial_services",
                "autonomous_vehicles_section",
            ],
            "AI implementations vary significantly across domains, with healthcare focusing on diagnostic accuracy, finance on risk management, and transportation on safety and navigation.",
            query_type="comparative",
            difficulty="hard",
            domain="multi_domain",
        )

        # Technical deep-dive queries
        dataset.add_query(
            "TD001",
            "What are the specific machine learning algorithms mentioned for natural language processing tasks?",
            ["nlp_algorithms_section", "ml_methods_subsection"],
            "NLP applications utilize transformer models, BERT variants, GPT architectures, and traditional methods like LSTM for text analysis and generation.",
            query_type="technical_deep",
            difficulty="hard",
            domain="ai_methods",
        )

        # Temporal comparison queries
        dataset.add_query(
            "TC001",
            "What are the differences between 2021 and 2024 AI use case implementations?",
            ["2021_implementations", "2024_implementations", "evolution_analysis"],
            "Between 2021 and 2024, AI implementations evolved with better foundation models, improved deployment practices, and enhanced ethical considerations.",
            query_type="temporal",
            difficulty="hard",
            domain="evolution",
        )

        return dataset

    def evaluate_rag_configuration(
        self, config: RAGConfiguration, dataset: EvaluationDataset, rag_system: Any
    ) -> EvaluationMetrics:
        """Evaluate a specific RAG configuration against a dataset."""

        logger.info(f"Evaluating RAG configuration: {config.name}")

        all_results = []
        retrieval_times = []
        generation_times = []
        total_costs = []

        for query_data in dataset.queries:
            query_id = query_data["id"]
            query = query_data["query"]

            # Measure retrieval performance
            start_time = time.time()
            retrieval_result = rag_system.retrieve(query, top_k=20)
            retrieval_time = (time.time() - start_time) * 1000
            retrieval_times.append(retrieval_time)

            # Measure generation performance
            start_time = time.time()
            generation_result = rag_system.generate(query, retrieval_result)
            generation_time = (time.time() - start_time) * 1000
            generation_times.append(generation_time)

            # Calculate metrics for this query
            query_metrics = self._calculate_query_metrics(
                query_id, query, retrieval_result, generation_result, dataset
            )
            all_results.append(query_metrics)

            # Estimate cost (mock implementation)
            total_costs.append(
                self._estimate_query_cost(config, query, retrieval_result)
            )

        # Aggregate results
        aggregated_metrics = self._aggregate_metrics(all_results)

        # Add efficiency metrics
        aggregated_metrics.retrieval_latency = np.mean(retrieval_times)
        aggregated_metrics.generation_latency = np.mean(generation_times)
        aggregated_metrics.total_latency = (
            aggregated_metrics.retrieval_latency + aggregated_metrics.generation_latency
        )
        aggregated_metrics.cost_per_query = np.mean(total_costs)

        # Store results
        self.evaluation_results[config.name] = {
            "config": config,
            "metrics": aggregated_metrics,
            "individual_results": all_results,
            "evaluated_at": datetime.now().isoformat(),
        }

        logger.info(f"Evaluation completed for {config.name}")
        return aggregated_metrics

    def benchmark_configurations(
        self,
        configurations: List[RAGConfiguration],
        dataset: EvaluationDataset,
        rag_systems: Dict[str, Any],
    ) -> Dict[str, EvaluationMetrics]:
        """Benchmark multiple RAG configurations and compare performance."""

        logger.info(f"Benchmarking {len(configurations)} RAG configurations")

        benchmark_results = {}

        for config in configurations:
            if config.name not in rag_systems:
                logger.warning(f"RAG system not provided for {config.name}, skipping")
                continue

            try:
                metrics = self.evaluate_rag_configuration(
                    config, dataset, rag_systems[config.name]
                )
                benchmark_results[config.name] = metrics

            except Exception as e:
                logger.error(f"Evaluation failed for {config.name}: {str(e)}")
                continue

        # Generate comparison report
        self._generate_benchmark_report(benchmark_results, dataset.name)

        # Store benchmark history
        self.benchmark_history.append(
            {
                "timestamp": datetime.now().isoformat(),
                "dataset": dataset.name,
                "configurations": [config.name for config in configurations],
                "results": {
                    name: asdict(metrics) for name, metrics in benchmark_results.items()
                },
            }
        )

        return benchmark_results

    def find_optimal_configuration(
        self,
        configurations: List[RAGConfiguration],
        dataset: EvaluationDataset,
        rag_systems: Dict[str, Any],
        optimization_criteria: Dict[str, float] = None,
    ) -> RAGConfiguration:
        """Find optimal RAG configuration based on weighted criteria."""

        if not optimization_criteria:
            optimization_criteria = {
                "ndcg_at_10": 0.3,
                "faithfulness": 0.25,
                "answer_relevancy": 0.25,
                "total_latency": -0.1,  # Negative weight for latency (lower is better)
                "cost_per_query": -0.1,  # Negative weight for cost (lower is better)
            }

        benchmark_results = self.benchmark_configurations(
            configurations, dataset, rag_systems
        )

        # Calculate weighted scores
        weighted_scores = {}
        for config_name, metrics in benchmark_results.items():
            score = 0
            metrics_dict = asdict(metrics)

            for criterion, weight in optimization_criteria.items():
                if criterion in metrics_dict:
                    if criterion == "ndcg_at_k":
                        value = metrics_dict[criterion].get(10, 0)
                    elif criterion == "hit_at_k":
                        value = metrics_dict[criterion].get(10, 0)
                    else:
                        value = metrics_dict[criterion]

                    # Normalize values to 0-1 range for fair comparison
                    normalized_value = self._normalize_metric_value(
                        criterion, value, benchmark_results
                    )
                    score += weight * normalized_value

            weighted_scores[config_name] = score

        # Find optimal configuration
        optimal_config_name = max(weighted_scores, key=weighted_scores.get)
        optimal_config = next(
            c for c in configurations if c.name == optimal_config_name
        )

        logger.info(
            f"Optimal configuration found: {optimal_config_name} (score: {weighted_scores[optimal_config_name]:.3f})"
        )

        # Generate optimization report
        self._generate_optimization_report(
            weighted_scores, optimization_criteria, optimal_config
        )

        return optimal_config

    def ablation_study(
        self,
        base_config: RAGConfiguration,
        components_to_test: Dict[str, List[str]],
        dataset: EvaluationDataset,
        rag_system_factory: Callable,
    ) -> Dict[str, Any]:
        """Perform ablation study to understand component contributions."""

        logger.info("Starting ablation study")

        ablation_results = {}

        # Test each component variation
        for component, variations in components_to_test.items():
            component_results = {}

            for variation in variations:
                # Create modified configuration
                modified_config = RAGConfiguration(**asdict(base_config))
                setattr(modified_config, component, variation)
                modified_config.name = f"{base_config.name}_{component}_{variation}"

                # Create RAG system with modified config
                rag_system = rag_system_factory(modified_config)

                # Evaluate
                metrics = self.evaluate_rag_configuration(
                    modified_config, dataset, rag_system
                )
                component_results[variation] = metrics

            ablation_results[component] = component_results

        # Generate ablation report
        self._generate_ablation_report(ablation_results, base_config)

        return ablation_results

    def _calculate_query_metrics(
        self,
        query_id: str,
        query: str,
        retrieval_result: List[Dict],
        generation_result: Dict,
        dataset: EvaluationDataset,
    ) -> Dict[str, Any]:
        """Calculate metrics for a single query."""

        ground_truth = dataset.ground_truth[query_id]
        relevant_docs = ground_truth["relevant_docs"]
        relevance_scores = ground_truth.get("relevance_scores", {})
        ideal_answer = ground_truth["ideal_answer"]

        # Retrieval metrics
        retrieved_doc_ids = [doc["id"] for doc in retrieval_result]

        hit_at_k = {}
        for k in [1, 3, 5, 10, 20]:
            hit_at_k[k] = (
                1.0
                if any(doc_id in relevant_docs for doc_id in retrieved_doc_ids[:k])
                else 0.0
            )

        # MRR calculation
        mrr = 0
        for i, doc_id in enumerate(retrieved_doc_ids):
            if doc_id in relevant_docs:
                mrr = 1.0 / (i + 1)
                break

        # nDCG calculation
        ndcg_at_k = {}
        for k in [3, 5, 10, 20]:
            ndcg_at_k[k] = self._calculate_ndcg(retrieved_doc_ids[:k], relevance_scores)

        # Generation quality metrics
        generated_answer = generation_result.get("answer", "")

        # Use LLM evaluators for generation metrics
        faithfulness = self._evaluate_faithfulness(generated_answer, retrieval_result)
        answer_relevancy = self._evaluate_answer_relevancy(query, generated_answer)
        hallucination_rate = self._detect_hallucinations(
            generated_answer, retrieval_result
        )

        return {
            "query_id": query_id,
            "hit_at_k": hit_at_k,
            "mrr": mrr,
            "ndcg_at_k": ndcg_at_k,
            "faithfulness": faithfulness,
            "answer_relevancy": answer_relevancy,
            "hallucination_rate": hallucination_rate,
            "generated_answer": generated_answer,
            "retrieved_docs": len(retrieval_result),
        }

    def _calculate_ndcg(
        self, retrieved_docs: List[str], relevance_scores: Dict[str, float]
    ) -> float:
        """Calculate Normalized Discounted Cumulative Gain."""

        dcg = 0
        for i, doc_id in enumerate(retrieved_docs):
            relevance = relevance_scores.get(doc_id, 0)
            dcg += relevance / np.log2(i + 2)

        # Calculate IDCG (Ideal DCG)
        ideal_relevances = sorted(relevance_scores.values(), reverse=True)
        idcg = sum(rel / np.log2(i + 2) for i, rel in enumerate(ideal_relevances))

        return dcg / idcg if idcg > 0 else 0

    def _evaluate_faithfulness(self, answer: str, sources: List[Dict]) -> float:
        """Evaluate faithfulness of generated answer to sources."""

        source_content = " ".join([doc.get("content", "") for doc in sources])

        result = self.faithfulness_evaluator.evaluate(
            {
                "answer": answer,
                "sources": source_content,
                "evaluation_criteria": "factual_consistency",
            }
        )

        return result.get("faithfulness_score", 0.5)

    def _evaluate_answer_relevancy(self, query: str, answer: str) -> float:
        """Evaluate relevancy of answer to query."""

        result = self.relevancy_evaluator.evaluate(
            {
                "query": query,
                "answer": answer,
                "evaluation_criteria": "relevance_to_query",
            }
        )

        return result.get("relevancy_score", 0.5)

    def _detect_hallucinations(self, answer: str, sources: List[Dict]) -> float:
        """Detect hallucination rate in generated answer."""

        source_content = " ".join([doc.get("content", "") for doc in sources])

        result = self.hallucination_detector.detect(
            {
                "answer": answer,
                "sources": source_content,
                "detection_criteria": "unsupported_claims",
            }
        )

        return result.get("hallucination_rate", 0.0)

    def _aggregate_metrics(self, all_results: List[Dict]) -> EvaluationMetrics:
        """Aggregate metrics across all queries."""

        # Calculate mean values for all metrics
        hit_at_k = {}
        ndcg_at_k = {}
        for k in [1, 3, 5, 10, 20]:
            hit_at_k[k] = np.mean([r["hit_at_k"][k] for r in all_results])
            ndcg_at_k[k] = np.mean([r["ndcg_at_k"][k] for r in all_results])

        return EvaluationMetrics(
            hit_at_k=hit_at_k,
            mrr=np.mean([r["mrr"] for r in all_results]),
            ndcg_at_k=ndcg_at_k,
            map_score=0.0,  # Calculate if needed
            recall_at_k={},  # Calculate if needed
            precision_at_k={},  # Calculate if needed
            faithfulness=np.mean([r["faithfulness"] for r in all_results]),
            answer_relevancy=np.mean([r["answer_relevancy"] for r in all_results]),
            context_precision=0.0,  # Calculate if needed
            context_recall=0.0,  # Calculate if needed
            retrieval_latency=0.0,  # Set in main evaluation function
            generation_latency=0.0,  # Set in main evaluation function
            total_latency=0.0,  # Set in main evaluation function
            cost_per_query=0.0,  # Set in main evaluation function
            coherence=0.0,  # Calculate if needed
            completeness=0.0,  # Calculate if needed
            accuracy=np.mean(
                [r["faithfulness"] for r in all_results]
            ),  # Use faithfulness as proxy
            hallucination_rate=np.mean([r["hallucination_rate"] for r in all_results]),
            diversity_score=0.0,  # Calculate if needed
            coverage_score=0.0,  # Calculate if needed
            novelty_score=0.0,  # Calculate if needed
            explainability_score=0.0,  # Calculate if needed
        )

    def _generate_benchmark_report(
        self, results: Dict[str, EvaluationMetrics], dataset_name: str
    ):
        """Generate comprehensive benchmark report."""

        report_path = (
            self.output_dir
            / f"benchmark_report_{dataset_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        )

        # Create comparison plots
        self._create_performance_plots(results)

        # Generate HTML report
        html_content = self._generate_html_report(results, dataset_name)

        with open(report_path, "w") as f:
            f.write(html_content)

        logger.info(f"Benchmark report generated: {report_path}")

    def _create_performance_plots(self, results: Dict[str, EvaluationMetrics]):
        """Create performance comparison plots."""

        # Performance comparison plot
        configs = list(results.keys())

        # nDCG@10 comparison
        ndcg_scores = [results[config].ndcg_at_k[10] for config in configs]

        plt.figure(figsize=(12, 8))
        plt.subplot(2, 2, 1)
        plt.bar(configs, ndcg_scores)
        plt.title("nDCG@10 Comparison")
        plt.xticks(rotation=45)

        # Faithfulness comparison
        faithfulness_scores = [results[config].faithfulness for config in configs]
        plt.subplot(2, 2, 2)
        plt.bar(configs, faithfulness_scores)
        plt.title("Faithfulness Comparison")
        plt.xticks(rotation=45)

        # Latency comparison
        latency_scores = [results[config].total_latency for config in configs]
        plt.subplot(2, 2, 3)
        plt.bar(configs, latency_scores)
        plt.title("Total Latency (ms)")
        plt.xticks(rotation=45)

        # Cost comparison
        cost_scores = [results[config].cost_per_query for config in configs]
        plt.subplot(2, 2, 4)
        plt.bar(configs, cost_scores)
        plt.title("Cost per Query")
        plt.xticks(rotation=45)

        plt.tight_layout()
        plt.savefig(
            self.output_dir / "performance_comparison.png", dpi=300, bbox_inches="tight"
        )
        plt.close()

    def _generate_html_report(
        self, results: Dict[str, EvaluationMetrics], dataset_name: str
    ) -> str:
        """Generate HTML benchmark report."""

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>RAG Benchmark Report - {dataset_name}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .metric {{ font-weight: bold; }}
                .best {{ background-color: #d4edda; }}
                .worst {{ background-color: #f8d7da; }}
            </style>
        </head>
        <body>
            <h1>RAG Benchmark Report</h1>
            <p><strong>Dataset:</strong> {dataset_name}</p>
            <p><strong>Generated:</strong> {datetime.now().isoformat()}</p>

            <h2>Performance Summary</h2>
            <table>
                <tr>
                    <th>Configuration</th>
                    <th>nDCG@10</th>
                    <th>Hit@10</th>
                    <th>MRR</th>
                    <th>Faithfulness</th>
                    <th>Answer Relevancy</th>
                    <th>Total Latency (ms)</th>
                    <th>Cost per Query</th>
                </tr>
        """

        for config_name, metrics in results.items():
            html += f"""
                <tr>
                    <td>{config_name}</td>
                    <td>{metrics.ndcg_at_k[10]:.3f}</td>
                    <td>{metrics.hit_at_k[10]:.3f}</td>
                    <td>{metrics.mrr:.3f}</td>
                    <td>{metrics.faithfulness:.3f}</td>
                    <td>{metrics.answer_relevancy:.3f}</td>
                    <td>{metrics.total_latency:.1f}</td>
                    <td>{metrics.cost_per_query:.4f}</td>
                </tr>
            """

        html += """
            </table>

            <h2>Performance Plots</h2>
            <img src="performance_comparison.png" alt="Performance Comparison" style="max-width: 100%;">

        </body>
        </html>
        """

        return html

    def _create_faithfulness_evaluator(self) -> LLMAgentNode:
        """Create faithfulness evaluator."""
        return LLMAgentNode(
            name="faithfulness_evaluator",
            model="gpt-4o-mini",
            system_prompt="""You are an expert evaluator for RAG system faithfulness.

            Evaluate how faithful a generated answer is to the provided source documents.
            Score from 0.0 (completely unfaithful) to 1.0 (completely faithful).

            Consider:
            - Factual accuracy relative to sources
            - Claims supported by evidence
            - Absence of contradictions

            Return a JSON with faithfulness_score (float).""",
        )

    def _create_relevancy_evaluator(self) -> LLMAgentNode:
        """Create answer relevancy evaluator."""
        return LLMAgentNode(
            name="relevancy_evaluator",
            model="gpt-4o-mini",
            system_prompt="""You are an expert evaluator for answer relevancy.

            Evaluate how relevant a generated answer is to the given query.
            Score from 0.0 (completely irrelevant) to 1.0 (perfectly relevant).

            Consider:
            - Direct addressing of the query
            - Completeness of the answer
            - Absence of irrelevant information

            Return a JSON with relevancy_score (float).""",
        )

    def _create_hallucination_detector(self) -> LLMAgentNode:
        """Create hallucination detector."""
        return LLMAgentNode(
            name="hallucination_detector",
            model="gpt-4o-mini",
            system_prompt="""You are an expert detector of hallucinations in RAG outputs.

            Identify unsupported claims in the generated answer that are not backed by sources.
            Calculate hallucination rate from 0.0 (no hallucinations) to 1.0 (all hallucinated).

            Consider:
            - Claims not supported by source documents
            - Fabricated facts or figures
            - Contradictions to source material

            Return a JSON with hallucination_rate (float).""",
        )

    def _get_evaluation_prompt(self) -> str:
        """Get general evaluation prompt."""
        return """You are an expert RAG system evaluator.

        Provide comprehensive evaluation of retrieval and generation quality
        across multiple dimensions including accuracy, relevance, and coherence.

        Always return structured JSON responses with numeric scores."""

    def _estimate_query_cost(
        self, config: RAGConfiguration, query: str, retrieval_result: List[Dict]
    ) -> float:
        """Estimate computational cost for a query (mock implementation)."""

        # Mock cost estimation based on model usage
        base_cost = 0.001  # Base cost per query

        # Add retrieval cost
        if "dense" in config.retrieval_method:
            base_cost += 0.0005
        if "rerank" in config.reranking_method:
            base_cost += 0.002

        # Add generation cost based on model
        if "gpt-4" in config.generation_model:
            base_cost += 0.01
        elif "gpt-3.5" in config.generation_model:
            base_cost += 0.002

        return base_cost

    def _normalize_metric_value(
        self, metric_name: str, value: float, all_results: Dict[str, EvaluationMetrics]
    ) -> float:
        """Normalize metric value to 0-1 range for comparison."""

        all_values = []
        for metrics in all_results.values():
            metrics_dict = asdict(metrics)
            if metric_name in metrics_dict:
                if metric_name == "ndcg_at_k":
                    all_values.append(metrics_dict[metric_name].get(10, 0))
                else:
                    all_values.append(metrics_dict[metric_name])

        if not all_values:
            return 0.5

        min_val, max_val = min(all_values), max(all_values)

        if max_val == min_val:
            return 1.0

        # For metrics where lower is better (latency, cost), invert
        if metric_name in ["total_latency", "cost_per_query", "hallucination_rate"]:
            return (max_val - value) / (max_val - min_val)
        else:
            return (value - min_val) / (max_val - min_val)

    def _generate_optimization_report(
        self,
        weighted_scores: Dict[str, float],
        criteria: Dict[str, float],
        optimal_config: RAGConfiguration,
    ):
        """Generate optimization report."""

        report_path = (
            self.output_dir
            / f"optimization_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )

        report = {
            "optimization_criteria": criteria,
            "weighted_scores": weighted_scores,
            "optimal_configuration": asdict(optimal_config),
            "generated_at": datetime.now().isoformat(),
        }

        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)

        logger.info(f"Optimization report saved: {report_path}")

    def _generate_ablation_report(
        self, ablation_results: Dict[str, Any], base_config: RAGConfiguration
    ):
        """Generate ablation study report."""

        report_path = (
            self.output_dir
            / f"ablation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )

        # Convert metrics to serializable format
        serializable_results = {}
        for component, variations in ablation_results.items():
            serializable_results[component] = {}
            for variation, metrics in variations.items():
                serializable_results[component][variation] = asdict(metrics)

        report = {
            "base_configuration": asdict(base_config),
            "ablation_results": serializable_results,
            "generated_at": datetime.now().isoformat(),
        }

        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)

        logger.info(f"Ablation study report saved: {report_path}")


# Example usage functions
def create_test_configurations() -> List[RAGConfiguration]:
    """Create test configurations for evaluation."""

    configs = [
        RAGConfiguration(
            name="baseline_dense",
            retrieval_method="dense_retrieval",
            chunking_strategy="fixed_size",
            embedding_model="text-embedding-3-small",
            reranking_method="none",
            generation_model="gpt-4o-mini",
        ),
        RAGConfiguration(
            name="hybrid_reranked",
            retrieval_method="hybrid_dense_sparse",
            chunking_strategy="recursive",
            embedding_model="text-embedding-3-large",
            reranking_method="cross_encoder",
            generation_model="gpt-4o-mini",
        ),
        RAGConfiguration(
            name="advanced_fusion",
            retrieval_method="fusion_rag",
            chunking_strategy="semantic",
            embedding_model="voyage-large-2",
            reranking_method="llm_listwise",
            generation_model="gpt-4o",
            fusion_strategy="adaptive_weighted",
            compression_method="contextual_compression",
            query_transformation="expansion_and_rewrite",
        ),
        RAGConfiguration(
            name="graph_rag",
            retrieval_method="graph_traversal",
            chunking_strategy="hierarchical",
            embedding_model="text-embedding-3-large",
            reranking_method="relationship_aware",
            generation_model="gpt-4o",
        ),
    ]

    return configs


if __name__ == "__main__":
    # Example usage
    harness = RAGEvaluationHarness()
    dataset = harness.create_section7_evaluation_dataset()
    configs = create_test_configurations()

    print(f"Created evaluation dataset with {len(dataset.queries)} queries")
    print(f"Prepared {len(configs)} configurations for testing")
