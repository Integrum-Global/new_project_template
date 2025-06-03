# AI/LLM Analysis Template

A comprehensive template for leveraging AI and Large Language Models (LLMs) for data analysis using the Kailash SDK.

## Overview

This template provides a foundation for:
- Document analysis and summarization
- Entity extraction and classification
- Sentiment analysis
- Topic modeling and categorization
- Insight generation from unstructured data
- Batch processing of large document sets

## Features

- Multiple LLM provider support (OpenAI, Anthropic, etc.)
- Document chunking for large texts
- Structured data extraction
- Sentiment and tone analysis
- Entity recognition (people, organizations, locations)
- Automated report generation
- Batch processing capabilities
- Cost optimization through efficient prompting

## Quick Start

1. **Copy this template to your solution:**
   ```bash
   cp -r templates/ai_analysis/* src/solutions/my_ai_solution/
   ```

2. **Set up API credentials:**
   ```bash
   export OPENAI_API_KEY="your-openai-api-key"
   # Or for other providers:
   export ANTHROPIC_API_KEY="your-anthropic-api-key"
   ```

3. **Prepare your input data:**
   Create a JSON file with documents to analyze:
   ```json
   {
     "documents": [
       {
         "id": "doc1",
         "content": "Your text content here...",
         "metadata": {"source": "email", "date": "2024-01-15"}
       }
     ]
   }
   ```

4. **Run the analysis:**
   ```bash
   python -m solutions.my_ai_solution
   ```

## Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `input_file` | string | "data/documents.json" | Input documents file |
| `output_file` | string | "data/ai_analysis_results.json" | Analysis results file |
| `ai_provider` | string | "openai" | LLM provider (openai, anthropic, etc.) |
| `ai_model` | string | "gpt-4" | Model to use |
| `temperature` | float | 0.3 | Model temperature (0-1) |
| `max_tokens` | int | 1000 | Maximum tokens per response |
| `chunk_size` | int | 3500 | Document chunk size |
| `batch_size` | int | 10 | Documents per batch |

## Supported LLM Providers

### OpenAI (GPT-4, GPT-3.5)
```yaml
ai_provider: "openai"
ai_model: "gpt-4"  # or "gpt-3.5-turbo"
```

### Anthropic (Claude)
```yaml
ai_provider: "anthropic"
ai_model: "claude-3-opus"  # or "claude-3-sonnet"
```

### Local Models
```yaml
ai_provider: "local"
ai_model: "llama2"  # Requires local setup
```

## Analysis Types

### Document Summarization
Extract concise summaries from long documents:
```python
system_prompt: "Summarize the key points in 3-5 bullet points"
```

### Entity Extraction
Identify people, organizations, and locations:
```python
system_prompt: """Extract entities:
- People: Full names
- Organizations: Company/institution names
- Locations: Cities, countries, addresses
Return as JSON."""
```

### Sentiment Analysis
Analyze emotional tone and sentiment:
```python
system_prompt: """Analyze sentiment:
- Overall: positive/negative/neutral
- Confidence: 0-1
- Key emotions detected
- Supporting quotes"""
```

### Topic Classification
Categorize documents by topic:
```python
system_prompt: """Classify into categories:
- Technology
- Business
- Healthcare
- Education
- Other
Provide confidence scores."""
```

## Advanced Features

### Custom Analysis Prompts
Add custom analysis nodes:
```python
workflow.add_node(
    "custom_analysis",
    LLMAgentNode,
    system_prompt="Your custom analysis instructions here",
    user_prompt_template="Analyze this: {content}"
)
```

### Multi-Step Analysis
Chain multiple AI analyses:
```python
# First: Extract facts
workflow.add_node("extract_facts", LLMAgentNode, ...)

# Then: Verify facts
workflow.add_node("verify_facts", LLMAgentNode, ...)

# Finally: Generate insights
workflow.add_node("generate_insights", LLMAgentNode, ...)
```

### Parallel Processing
Process multiple documents simultaneously:
```python
workflow.add_node(
    "parallel_analysis",
    ParallelProcessorNode,
    max_workers=5,
    node_to_parallelize="ai_analysis"
)
```

## Cost Optimization

### Token Usage Optimization
1. **Chunk documents appropriately** - Don't send unnecessary content
2. **Use structured prompts** - Get exactly what you need
3. **Cache results** - Avoid re-analyzing the same content
4. **Batch similar documents** - Reduce API calls

### Model Selection
- Use GPT-3.5 for simple tasks (summaries, basic extraction)
- Use GPT-4 for complex reasoning and analysis
- Use specialized models for specific tasks (embeddings, classification)

## Output Formats

### JSON Analysis Results
```json
{
  "analyzed_docs": [
    {
      "id": "doc1",
      "summary": "Brief summary...",
      "topics": ["technology", "innovation"],
      "entities": {
        "people": ["John Doe"],
        "organizations": ["Acme Corp"]
      },
      "sentiment": "positive",
      "key_points": ["Point 1", "Point 2"]
    }
  ],
  "overall_analysis": {
    "total_documents": 10,
    "common_topics": [["technology", 8], ["business", 5]],
    "sentiment_distribution": {"positive": 6, "neutral": 3, "negative": 1}
  }
}
```

### Markdown Report
Automatically generated summary report with:
- Executive summary
- Key findings
- Entity lists
- Topic distribution
- Individual document summaries

## Examples

See the `examples/` directory for:
- `basic_usage.py` - Simple document analysis
- `advanced_usage.py` - Complex multi-step analysis with custom prompts

## Best Practices

1. **Validate input data** before sending to AI
2. **Handle API errors gracefully** with retries
3. **Monitor token usage** to control costs
4. **Use appropriate models** for each task
5. **Structure prompts clearly** for consistent results
6. **Test with small datasets** first
7. **Implement caching** for repeated analyses

## Troubleshooting

### "API key not found"
- Ensure environment variable is set
- Check provider-specific key names
- Verify key has necessary permissions

### "Token limit exceeded"
- Reduce chunk size in configuration
- Use more concise prompts
- Consider using a model with higher limits

### "Poor analysis quality"
- Improve prompt clarity and specificity
- Provide examples in the prompt
- Adjust temperature settings
- Try different models

### "Slow processing"
- Enable parallel processing
- Reduce batch sizes
- Use streaming where available
- Consider async processing