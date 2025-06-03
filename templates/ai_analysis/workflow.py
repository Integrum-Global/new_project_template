#!/usr/bin/env python3
"""
AI/LLM Analysis Solution Template

This template demonstrates how to use AI/LLM models for data analysis,
text processing, and generating insights from various data sources.

Requirements:
- Input: Documents, text data, or structured data for analysis
- Processing: AI-powered analysis, summarization, extraction
- Output: Insights, summaries, or enriched data

Created with Kailash SDK
"""

from pathlib import Path
from typing import Any, Dict, List
import json

# Kailash SDK imports
from kailash.workflow.graph import Workflow
from kailash.runtime.local import LocalRuntime

# Import required nodes
from kailash.nodes.data import JSONReaderNode, JSONWriterNode, CSVReaderNode
from kailash.nodes.ai.llm import LLMAgentNode
from kailash.nodes.code.python import PythonCodeNode
from kailash.nodes.transform import DataTransformerNode


def create_ai_analysis_workflow(config: Dict[str, Any] = None):
    """
    Create AI analysis workflow.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Configured Workflow instance
    """
    if config is None:
        config = {}
    
    workflow = Workflow(
        workflow_id="ai_analysis",
        name="AI-Powered Data Analysis Workflow"
    )
    
    # 1. Load input data
    workflow.add_node(
        "load_data",
        JSONReaderNode,
        file_path=config.get("input_file", "data/documents.json")
    )
    
    # 2. Prepare data for AI analysis
    workflow.add_node(
        "prepare_data",
        PythonCodeNode,
        code="""
def execute(data):
    # Prepare documents for AI analysis
    prepared_docs = []
    
    for idx, item in enumerate(data.get('documents', [])):
        # Extract text content
        content = item.get('content', '')
        metadata = item.get('metadata', {})
        
        # Chunk large documents if needed
        if len(content) > 4000:  # Token limit consideration
            chunks = chunk_text(content, 3500)
            for chunk_idx, chunk in enumerate(chunks):
                prepared_docs.append({
                    'id': f"{item.get('id', idx)}_{chunk_idx}",
                    'content': chunk,
                    'metadata': {**metadata, 'chunk': chunk_idx}
                })
        else:
            prepared_docs.append({
                'id': item.get('id', idx),
                'content': content,
                'metadata': metadata
            })
    
    return {"prepared_docs": prepared_docs}

def chunk_text(text, max_length):
    # Simple chunking by sentences
    sentences = text.split('. ')
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        if len(current_chunk) + len(sentence) < max_length:
            current_chunk += sentence + ". "
        else:
            chunks.append(current_chunk.strip())
            current_chunk = sentence + ". "
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks
"""
    )
    
    # 3. AI Analysis - Extract insights
    workflow.add_node(
        "ai_extract",
        LLMAgentNode,
        provider=config.get("ai_provider", "openai"),
        model=config.get("ai_model", "gpt-4"),
        temperature=config.get("temperature", 0.3),
        system_prompt="""You are an expert data analyst. Extract key information from the provided text:
        
        1. Main topics and themes
        2. Key entities (people, organizations, locations)
        3. Important dates and events
        4. Sentiment and tone
        5. Action items or recommendations
        
        Provide structured output in JSON format.""",
        max_tokens=config.get("max_tokens", 1000)
    )
    
    # 4. AI Analysis - Generate summary
    workflow.add_node(
        "ai_summarize",
        LLMAgentNode,
        provider=config.get("ai_provider", "openai"),
        model=config.get("ai_model", "gpt-4"),
        temperature=config.get("temperature", 0.5),
        system_prompt="""Create a concise summary of the provided content:
        
        - Highlight the most important points
        - Maintain factual accuracy
        - Use clear, professional language
        - Keep summary under 200 words
        """,
        max_tokens=300
    )
    
    # 5. Process and structure AI results
    workflow.add_node(
        "process_results",
        PythonCodeNode,
        code="""
def execute(data):
    import json
    
    insights = data.get('insights', {})
    summaries = data.get('summaries', {})
    
    # Combine results
    analyzed_docs = []
    
    for doc in data['original_docs']:
        doc_id = doc['id']
        
        # Parse AI responses
        try:
            insight_data = json.loads(insights.get(doc_id, '{}'))
        except:
            insight_data = {}
        
        analyzed_docs.append({
            'id': doc_id,
            'original_content': doc['content'],
            'summary': summaries.get(doc_id, ''),
            'topics': insight_data.get('topics', []),
            'entities': insight_data.get('entities', {}),
            'sentiment': insight_data.get('sentiment', 'neutral'),
            'key_points': insight_data.get('key_points', []),
            'metadata': doc.get('metadata', {})
        })
    
    # Generate overall analysis
    overall_analysis = {
        'total_documents': len(analyzed_docs),
        'common_topics': extract_common_topics(analyzed_docs),
        'sentiment_distribution': calculate_sentiment_distribution(analyzed_docs),
        'all_entities': merge_entities(analyzed_docs)
    }
    
    return {
        "analyzed_docs": analyzed_docs,
        "overall_analysis": overall_analysis
    }

def extract_common_topics(docs):
    # Count topic frequencies
    topic_counts = {}
    for doc in docs:
        for topic in doc.get('topics', []):
            topic_counts[topic] = topic_counts.get(topic, 0) + 1
    
    # Return top topics
    return sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:10]

def calculate_sentiment_distribution(docs):
    sentiments = {}
    for doc in docs:
        sentiment = doc.get('sentiment', 'neutral')
        sentiments[sentiment] = sentiments.get(sentiment, 0) + 1
    return sentiments

def merge_entities(docs):
    all_entities = {'people': set(), 'organizations': set(), 'locations': set()}
    for doc in docs:
        entities = doc.get('entities', {})
        for entity_type, entity_list in entities.items():
            if entity_type in all_entities:
                all_entities[entity_type].update(entity_list)
    
    # Convert sets to lists
    return {k: list(v) for k, v in all_entities.items()}
"""
    )
    
    # 6. Save results
    workflow.add_node(
        "save_analysis",
        JSONWriterNode,
        file_path=config.get("output_file", "data/ai_analysis_results.json"),
        pretty_print=True
    )
    
    workflow.add_node(
        "save_summary_report",
        PythonCodeNode,
        code="""
def execute(data):
    # Generate markdown report
    report = generate_markdown_report(data['analyzed_docs'], data['overall_analysis'])
    
    # Save report
    with open('data/analysis_report.md', 'w') as f:
        f.write(report)
    
    return {"report_saved": True}

def generate_markdown_report(docs, analysis):
    report = "# AI Analysis Report\\n\\n"
    report += f"**Total Documents Analyzed**: {analysis['total_documents']}\\n\\n"
    
    report += "## Overall Insights\\n\\n"
    
    report += "### Sentiment Distribution\\n"
    for sentiment, count in analysis['sentiment_distribution'].items():
        report += f"- {sentiment}: {count} documents\\n"
    
    report += "\\n### Top Topics\\n"
    for topic, count in analysis['common_topics'][:5]:
        report += f"- {topic} ({count} mentions)\\n"
    
    report += "\\n### Key Entities\\n"
    for entity_type, entities in analysis['all_entities'].items():
        if entities:
            report += f"\\n**{entity_type.title()}**:\\n"
            for entity in entities[:10]:
                report += f"- {entity}\\n"
    
    report += "\\n## Document Summaries\\n\\n"
    for doc in docs:
        report += f"### Document: {doc['id']}\\n"
        report += f"**Summary**: {doc['summary']}\\n"
        report += f"**Sentiment**: {doc['sentiment']}\\n"
        report += f"**Topics**: {', '.join(doc['topics'][:5])}\\n\\n"
    
    return report
"""
    )
    
    # Connect workflow
    workflow.connect("load_data", "prepare_data", mapping={"documents": "data"})
    workflow.connect("prepare_data", "ai_extract", mapping={"prepared_docs": "documents"})
    workflow.connect("prepare_data", "ai_summarize", mapping={"prepared_docs": "documents"})
    workflow.connect(
        ["prepare_data", "ai_extract", "ai_summarize"], 
        "process_results",
        mapping={
            "prepared_docs": "original_docs",
            "ai_extract": "insights",
            "ai_summarize": "summaries"
        }
    )
    workflow.connect("process_results", "save_analysis", mapping={"analyzed_docs": "data"})
    workflow.connect("process_results", "save_summary_report", mapping={"analyzed_docs": "data"})
    
    return workflow


def main():
    """Main execution function."""
    try:
        # Configuration
        config = {
            "input_file": "data/documents.json",
            "output_file": "data/ai_analysis_results.json",
            "ai_provider": "openai",
            "ai_model": "gpt-4",
            "temperature": 0.3,
            "max_tokens": 1000
        }
        
        # Check for API key
        import os
        if not os.getenv("OPENAI_API_KEY"):
            print("⚠️  Warning: OPENAI_API_KEY not set. Using mock mode.")
            config["ai_provider"] = "mock"
        
        # Create and execute workflow
        workflow = create_ai_analysis_workflow(config)
        runtime = LocalRuntime(debug=True)
        
        print("Starting AI Analysis Workflow...")
        print("=" * 50)
        
        results, run_id = runtime.execute(workflow)
        
        print(f"\n✅ AI analysis completed!")
        print(f"Run ID: {run_id}")
        print(f"\nResults saved to:")
        print(f"  - Analysis data: {config['output_file']}")
        print(f"  - Summary report: data/analysis_report.md")
        
        return True
        
    except Exception as e:
        print(f"❌ AI analysis failed: {e}")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)