# Ollama Integration Patterns - Cheatsheet

*Copy-paste patterns for local LLM integration with Ollama*

## 🎯 Quick Overview

**Use Case**: Local LLM processing with Ollama
**Node Type**: `LLMAgentNode` (v0.6.2+ with async support) or `PythonCodeNode` (for custom control)
**Port**: 11434 (default Ollama port)
**Models**: `llama3.2:3b` or `llama3.2:1b` (LLM), `nomic-embed-text:latest` (embeddings)

## 🆕 v0.6.2+ LLMAgentNode with Ollama

```python
from kailash.workflow.builder import WorkflowBuilder
from kailash.nodes.ai import LLMAgentNode
from kailash.runtime.local import LocalRuntime

# Basic usage with improved async support
workflow = WorkflowBuilder()
llm_node = LLMAgentNode(name="ollama_llm")
workflow.add_node("llm", llm_node)

# Execute with async runtime
runtime = LocalRuntime()
result, _ = await runtime.execute_async(workflow, parameters={
    "llm": {
        "provider": "ollama",
        "model": "llama3.2:3b",
        "prompt": "Write a haiku about programming",
        "generation_config": {
            "temperature": 0.7,
            "max_tokens": 300
        }
    }
})

# Remote Ollama server
result, _ = await runtime.execute_async(workflow, parameters={
    "llm": {
        "provider": "ollama",
        "model": "llama3.2:3b",
        "prompt": "Explain quantum computing",
        "backend_config": {
            "host": "gpu-server.local",
            "port": 11434
        }
    }
})
```

## 🚀 Alternative: Direct API with PythonCodeNode

```python
from kailash.workflow.builder import WorkflowBuilder
from kailash.runtime.local import LocalRuntime
from kailash.nodes.code import PythonCodeNode

def ollama_generate(prompt="Hello", model="llama3.2:1b"):
    import requests

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.7, "num_predict": 200}
            },
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            return {
                "response": data.get("response", ""),
                "success": True,
                "duration": data.get("total_duration", 0) / 1e9
            }
        else:
            return {"success": False, "error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

# Create workflow
workflow = WorkflowBuilder()
llm_node = PythonCodeNode.from_function(ollama_generate, name="llm")
workflow.add_node("generate", llm_node)

# Execute
runtime = LocalRuntime()
result, _ = runtime.execute(workflow, parameters={
    "generate": {"prompt": "Write a haiku about coding", "model": "llama3.2:1b"}
})

# Access result
if result["generate"]["result"]["success"]:
    print(result["generate"]["result"]["response"])
```

## 🔍 Embedding Generation

```python
def ollama_embeddings(texts=None):
    import requests

    if not texts:
        texts = ["Hello world"]

    embeddings = []
    for text in texts:
        try:
            response = requests.post(
                "http://localhost:11434/api/embeddings",
                json={"model": "nomic-embed-text:latest", "prompt": text},
                timeout=10
            )

            if response.status_code == 200:
                # CRITICAL: Extract embedding from response
                embeddings.append(response.json().get("embedding", []))
        except Exception as e:
            print(f"Failed for '{text}': {e}")

    return {
        "embeddings": embeddings,
        "success": len(embeddings) > 0,
        "dimensions": len(embeddings[0]) if embeddings else 0
    }

# Usage
embed_node = PythonCodeNode.from_function(ollama_embeddings, name="embedder")
workflow.add_node("embed", embed_node)

result, _ = runtime.execute(workflow, parameters={
    "embed": {"texts": ["Python is great", "AI is powerful"]}
})

embeddings = result["embed"]["result"]["embeddings"]
print(f"Generated {len(embeddings)} embeddings of {result['embed']['result']['dimensions']} dimensions")
```

## 🔄 Cyclic Workflow with Ollama

```python
def iterative_improver(text="", iteration=0, target_length=50):
    import requests

    if iteration == 0:
        prompt = f"Write a {target_length}-word story about robots."
    else:
        current_length = len(text.split())
        if abs(current_length - target_length) <= 5:
            return {"text": text, "iteration": iteration, "converged": True}

        if current_length < target_length:
            prompt = f"Expand this story to {target_length} words: {text}"
        else:
            prompt = f"Shorten this story to {target_length} words: {text}"

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3.2:1b",
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.7, "num_predict": 200}
            },
            timeout=30
        )

        if response.status_code == 200:
            new_text = response.json()["response"].strip()
            return {
                "text": new_text,
                "iteration": iteration + 1,
                "word_count": len(new_text.split()),
                "converged": abs(len(new_text.split()) - target_length) <= 5
            }
    except Exception as e:
        return {"text": text, "iteration": iteration, "converged": True, "error": str(e)}

# Cyclic workflow
workflow = WorkflowBuilder()
writer = PythonCodeNode.from_function(iterative_improver, name="writer")
workflow.add_node("improve", writer)

# Create cycle with proper parameter passing
workflow.create_cycle("improvement_cycle") \
    .connect("improve", "improve", {
        "result.text": "text",
        "result.iteration": "iteration",
        "result.target_length": "target_length"
    }) \
    .max_iterations(5) \
    .converge_when("converged == True") \
    .build()

# Execute with initial parameters
result, _ = runtime.execute(workflow, parameters={
    "improve": {"text": "", "iteration": 0, "target_length": 30}
})

print(f"Final story ({result['improve']['result']['word_count']} words):")
print(result['improve']['result']['text'])
```

## 📊 Sentiment Analysis Pipeline

```python
def analyze_sentiment(reviews):
    import requests
    import json
    import re

    results = []
    for review in reviews:
        prompt = f"""Analyze sentiment and respond with ONLY JSON:
{{"sentiment": "positive" or "negative" or "neutral", "confidence": 0.0-1.0}}

Review: {review['text']}

JSON:"""

        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "llama3.2:1b",
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.1, "num_predict": 50}
                },
                timeout=20
            )

            if response.status_code == 200:
                llm_response = response.json()["response"].strip()

                # Extract JSON with fallback
                json_match = re.search(r'\{[^}]+\}', llm_response)
                if json_match:
                    sentiment_data = json.loads(json_match.group())
                else:
                    # Fallback based on keywords
                    if "positive" in llm_response.lower():
                        sentiment_data = {"sentiment": "positive", "confidence": 0.7}
                    elif "negative" in llm_response.lower():
                        sentiment_data = {"sentiment": "negative", "confidence": 0.7}
                    else:
                        sentiment_data = {"sentiment": "neutral", "confidence": 0.5}

                results.append({
                    "id": review["id"],
                    "text": review["text"],
                    "sentiment": sentiment_data.get("sentiment", "unknown"),
                    "confidence": sentiment_data.get("confidence", 0.0)
                })
        except Exception as e:
            results.append({
                "id": review["id"],
                "text": review["text"],
                "sentiment": "error",
                "confidence": 0.0,
                "error": str(e)
            })

    return {
        "analyzed_reviews": results,
        "success": all(r["sentiment"] != "error" for r in results)
    }

# Data pipeline
data_gen = PythonCodeNode.from_function(
    lambda: {
        "reviews": [
            {"id": 1, "text": "This product is amazing!"},
            {"id": 2, "text": "Terrible quality, very disappointed."},
            {"id": 3, "text": "It's okay, nothing special."}
        ]
    },
    name="data_generator"
)

analyzer = PythonCodeNode.from_function(analyze_sentiment, name="analyzer")

workflow = WorkflowBuilder()
workflow.add_node("data", data_gen)
workflow.add_node("analyze", analyzer)
workflow.add_connection("data", "result", "analyze", "input")

result, _ = runtime.execute(workflow.build())
analyzed = result["analyze"]["result"]["analyzed_reviews"]
print(f"Analyzed {len(analyzed)} reviews")
for review in analyzed:
    print(f"Review {review['id']}: {review['sentiment']} ({review['confidence']:.2f})")
```

## ⚙️ Connection Testing

```python
def test_ollama_connectivity():
    """Test Ollama service availability."""
    import requests

    try:
        # Check service
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            available_models = [m["name"] for m in models]

            print(f"✅ Ollama available with {len(models)} models")
            print(f"Models: {available_models}")

            # Test generation
            test_response = requests.post(
                "http://localhost:11434/api/generate",
                json={"model": "llama3.2:1b", "prompt": "Hello", "stream": False},
                timeout=10
            )

            if test_response.status_code == 200:
                print("✅ LLM generation working")
            else:
                print(f"❌ LLM test failed: {test_response.status_code}")

            return True
    except Exception as e:
        print(f"❌ Ollama not available: {e}")
        print("💡 Start with: ollama serve")
        return False

# Always test connectivity first
if test_ollama_connectivity():
    # Proceed with Ollama workflows
    pass
```

## 🔧 Performance Optimization

```python
def optimized_ollama_request(prompt, model="llama3.2:1b"):
    """Optimized Ollama request for speed."""
    import requests

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,      # Lower for consistency
                    "num_predict": 100,      # Limit response length
                    "num_ctx": 2048,         # Limit context window
                    "top_k": 10,             # Speed up sampling
                    "top_p": 0.9,
                    "repeat_penalty": 1.1
                }
            },
            timeout=20  # Reasonable timeout
        )

        if response.status_code == 200:
            return {
                "response": response.json()["response"],
                "success": True,
                "duration": response.json().get("total_duration", 0) / 1e9
            }
    except requests.Timeout:
        return {"success": False, "error": f"Timeout with {model}"}
    except Exception as e:
        return {"success": False, "error": str(e)}
```

## ❌ Common Mistakes to Avoid

```python
# ❌ DON'T use old httpx-based implementations (pre-v0.6.2)
async with httpx.AsyncClient() as client:  # Fails with TaskGroup

# ❌ DON'T assume embeddings are vectors
embeddings = result["embeddings"]
similarity = cosine_similarity(embeddings[0], embeddings[1])  # Fails!

# ❌ DON'T parse JSON directly from LLM responses
data = json.loads(llm_response)  # Often fails

# ❌ DON'T forget to configure backend for remote Ollama
node.execute(provider="ollama", model="llama3.2:3b")  # May fail if not localhost

# ✅ DO use LLMAgentNode with v0.6.2+ for async workflows
# ✅ DO configure backend_config for remote Ollama servers
# ✅ DO extract embeddings with .get("embedding", [])
# ✅ DO use regex + fallbacks for JSON parsing
# ✅ DO test connectivity before workflows
```

## 📝 Quick Reference

| Operation | Pattern | Key Points |
|-----------|---------|------------|
| **LLM Generation (v0.6.2+)** | `LLMAgentNode` with async | Use `backend_config` for remote servers |
| **LLM Generation (custom)** | `PythonCodeNode.from_function()` | Direct API calls, timeout 30s |
| **Embeddings** | `requests.post("/api/embeddings")` | Extract with `.get("embedding")` |
| **Cycles** | Standard cycle patterns | Use `result.field` mapping |
| **JSON Parsing** | Regex + fallbacks | Never assume clean JSON |
| **Error Handling** | Try/catch with fallbacks | Always provide error responses |
| **Performance** | Limit num_predict, use 3B/1B models | Fast models for development |
| **Remote Servers** | Configure `backend_config` | Set host/port or base_url |

## 🔗 Related Patterns

- **[Cycle Parameter Passing](../developer/10-cycle-parameter-passing-guide.md)** - For cycle workflows
- **[AI Nodes Guide](../nodes/02-ai-nodes.md)** - Full Ollama integration examples
- **[Troubleshooting](../developer/05-troubleshooting.md)** - Common Ollama issues
- **[Node Selection Guide](../nodes/node-selection-guide.md)** - When to use PythonCodeNode vs LLMAgentNode
