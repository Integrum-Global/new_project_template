# AI Registry Examples - Real-World Usage Scenarios

This directory contains practical examples showing how to use the AI Registry MCP Server for various business and technical scenarios.

## 🎯 Quick Start Examples

### 1. Basic Search - Find What You Need

```python
# basic_search.py - Simple keyword search
from apps.ai_registry.workflows import execute_simple_search

# Find all machine learning implementations in healthcare
results = execute_simple_search(
    query="machine learning healthcare",
    limit=10
)

print(f"Found {results['count']} implementations:")
for use_case in results['results']:
    print(f"• {use_case['name']} - {use_case['status']}")
```

### 2. Industry Analysis - Understand Your Market

```python
# industry_analysis.py - Analyze AI adoption in your industry
from apps.ai_registry.workflows import execute_domain_overview

# Get comprehensive analysis of all industries
overview = execute_domain_overview()

# Find your industry's AI maturity
industry_stats = overview['domain_stats']['Healthcare']
print(f"Healthcare AI implementations: {industry_stats['count']}")
print(f"Production readiness: {industry_stats['production_rate']}%")
```

### 3. Natural Language Query - Ask Like a Human

```python
# natural_language_search.py - Use AI to understand your question
from apps.ai_registry.workflows import execute_agent_search

# Ask a business question
response = execute_agent_search(
    user_query="What are the most successful AI implementations for reducing operational costs?"
)

print(response['response']['content'])
```

## 💼 Business Leader Examples

### Finding ROI Evidence

```python
# roi_analysis.py - Find implementations with proven business value
from apps.ai_registry.workflows import execute_simple_search

# Search for production implementations with clear business impact
results = execute_simple_search(
    query="cost reduction efficiency improvement ROI",
    filters={"status": "Production"},
    limit=20
)

print("Production AI implementations with proven ROI:")
for uc in results['results']:
    if uc['status'] == 'Production':
        print(f"\n{uc['name']} ({uc['application_domain']})")
        print(f"Methods: {', '.join(uc['ai_methods'])}")
        if uc.get('narrative'):
            print(f"Impact: {uc['narrative'][:200]}...")
```

### Competitive Intelligence

```python
# competitive_analysis.py - See what competitors might be doing
from apps.ai_registry.workflows import execute_cross_domain_comparison

# Compare AI adoption across competitive industries
comparison = execute_cross_domain_comparison(
    domains=["Finance", "Insurance", "Banking"]
)

print("AI Adoption Comparison:")
for domain, stats in comparison['domain_comparison'].items():
    print(f"\n{domain}:")
    print(f"  Total implementations: {stats['use_case_count']}")
    print(f"  Production rate: {stats['production_rate']:.1%}")
    print(f"  Top methods: {', '.join([m[0] for m in stats['top_methods']])}")
```

## 👨‍💻 Technical Team Examples

### Technology Selection

```python
# tech_selection.py - Compare different AI approaches
from apps.ai_registry.workflows import execute_simple_search

# Compare different approaches for the same problem
approaches = {
    "Traditional ML": execute_simple_search("fraud detection machine learning -deep", limit=5),
    "Deep Learning": execute_simple_search("fraud detection deep learning", limit=5),
    "Hybrid": execute_simple_search("fraud detection ensemble hybrid", limit=5)
}

for approach, results in approaches.items():
    production_count = sum(1 for uc in results['results'] if uc['status'] == 'Production')
    print(f"\n{approach}: {production_count}/{results['count']} in production")
```

### Implementation Patterns

```python
# implementation_patterns.py - Find common successful patterns
from apps.ai_registry.server.indexer import RegistryIndexer

# Initialize registry
indexer = RegistryIndexer()
indexer.load_and_index('src/solutions/ai_registry/data/combined_ai_registry.json')

# Find all production NLP implementations
nlp_production = indexer.search("", filters={
    "ai_method": "Natural Language Processing",
    "status": "Production"
})

# Analyze common patterns
common_tasks = {}
for uc in nlp_production:
    for task in uc.get('tasks', []):
        common_tasks[task] = common_tasks.get(task, 0) + 1

print("Most common NLP tasks in production:")
for task, count in sorted(common_tasks.items(), key=lambda x: x[1], reverse=True)[:5]:
    print(f"• {task}: {count} implementations")
```

## 📊 Data Scientist Examples

### Similar Use Case Discovery

```python
# find_similar_cases.py - Find implementations similar to yours
from apps.ai_registry.server.indexer import RegistryIndexer

indexer = RegistryIndexer()
indexer.load_and_index('src/solutions/ai_registry/data/combined_ai_registry.json')

# Define your planned use case
my_use_case = {
    "application_domain": "Healthcare",
    "ai_methods": ["Machine Learning", "Computer Vision"],
    "tasks": ["Diagnosis", "Image Analysis"]
}

# Find the most similar existing implementation
all_cases = indexer.search("")  # Get all
best_match = None
best_score = 0

for case in all_cases:
    score = 0
    if case['application_domain'] == my_use_case['application_domain']:
        score += 0.4

    method_overlap = len(set(case['ai_methods']) & set(my_use_case['ai_methods']))
    score += 0.3 * (method_overlap / len(my_use_case['ai_methods']))

    task_overlap = len(set(case.get('tasks', [])) & set(my_use_case['tasks']))
    score += 0.3 * (task_overlap / len(my_use_case['tasks']))

    if score > best_score:
        best_score = score
        best_match = case

print(f"Most similar implementation (score: {best_score:.2f}):")
print(f"Name: {best_match['name']}")
print(f"Status: {best_match['status']}")
print(f"Methods: {', '.join(best_match['ai_methods'])}")
```

### Trend Analysis

```python
# trend_analysis.py - Identify emerging patterns
from apps.ai_registry.workflows import execute_simple_search

# Get all recent implementations
all_implementations = execute_simple_search("", limit=200)

# Analyze method combinations
method_combinations = {}
for uc in all_implementations['results']:
    methods = tuple(sorted(uc['ai_methods']))
    if len(methods) > 1:  # Only combinations
        method_combinations[methods] = method_combinations.get(methods, 0) + 1

print("Emerging AI method combinations:")
for methods, count in sorted(method_combinations.items(), key=lambda x: x[1], reverse=True)[:10]:
    print(f"• {' + '.join(methods)}: {count} implementations")
```

## 🚀 Complete Workflow Example

### From Business Need to Technical Solution

```python
# complete_workflow.py - End-to-end discovery process

from apps.ai_registry.workflows import (
    execute_agent_search,
    execute_simple_search,
    execute_domain_deep_dive
)

# Step 1: Business Need
print("=== Step 1: Define Business Need ===")
business_need = "reduce customer service response time while maintaining quality"

# Step 2: AI Assistant Consultation
print("\n=== Step 2: Ask AI Assistant ===")
ai_advice = execute_agent_search(
    user_query=f"What AI solutions can help {business_need}?"
)
print(ai_advice['response']['content'][:500] + "...")

# Step 3: Specific Search
print("\n=== Step 3: Search Specific Solutions ===")
specific_results = execute_simple_search(
    query="customer service automation response time",
    filters={"status": "Production"},
    limit=5
)

print(f"Found {specific_results['count']} production implementations:")
for uc in specific_results['results']:
    print(f"• {uc['name']} - {uc['application_domain']}")

# Step 4: Deep Dive into Domain
print("\n=== Step 4: Analyze Domain ===")
if specific_results['results']:
    domain = specific_results['results'][0]['application_domain']
    domain_analysis = execute_domain_deep_dive(domain)

    print(f"\n{domain} AI Landscape:")
    print(f"• Total implementations: {domain_analysis['stats']['total_use_cases']}")
    print(f"• Production rate: {domain_analysis['stats']['production_rate']:.1%}")
    print(f"• Top methods: {', '.join(domain_analysis['stats']['top_methods'][:3])}")

# Step 5: Recommendations
print("\n=== Step 5: Recommendations ===")
print("Based on the analysis:")
print("1. Focus on production-ready NLP solutions")
print("2. Consider transformer models for best quality")
print("3. Look at hybrid approaches for speed/quality balance")
print("4. Review similar implementations for lessons learned")
```

## 🔌 Integration Examples

### Slack Bot Integration

```python
# slack_bot_integration.py - Answer AI questions in Slack
import os
from slack_bolt import App
from apps.ai_registry.workflows import execute_agent_search

app = App(token=os.environ["SLACK_BOT_TOKEN"])

@app.message("ai registry")
def handle_ai_registry_question(message, say):
    user_question = message['text'].replace('ai registry', '').strip()

    # Query the AI Registry
    response = execute_agent_search(user_query=user_question)

    # Send response to Slack
    say(response['response']['content'][:3000])  # Slack message limit

if __name__ == "__main__":
    app.start(port=3000)
```

### Daily Report Generation

```python
# daily_report.py - Generate daily AI insights
import datetime
from apps.ai_registry.workflows import execute_domain_overview

def generate_daily_report():
    today = datetime.date.today()

    # Get overall statistics
    overview = execute_domain_overview(output_format="markdown")

    report = f"""# AI Registry Daily Report - {today}

## Overview
{overview['markdown'][:1000]}

## Top Insights
1. Most active domain: {overview['stats']['most_active_domain']}
2. Production implementations: {overview['stats']['production_count']}
3. Emerging methods: {', '.join(overview['stats']['emerging_methods'][:3])}

## Recommendation of the Day
Focus on {overview['stats']['most_active_domain']} implementations
with {overview['stats']['top_methods'][0]} for highest success rate.
"""

    # Save or email report
    with open(f"reports/ai_insights_{today}.md", "w") as f:
        f.write(report)

    return report

if __name__ == "__main__":
    report = generate_daily_report()
    print("Daily report generated!")
```

## 🎓 Learning Resources

### Understanding the Data

Each AI implementation in the registry contains:
- **name**: Descriptive name of the AI system
- **application_domain**: Industry or sector (Healthcare, Finance, etc.)
- **ai_methods**: List of AI technologies used
- **tasks**: Specific tasks the AI performs
- **status**: Maturity level (Research, PoC, Pilot, Production)
- **narrative**: Detailed description (when available)
- **challenges**: Implementation challenges faced
- **kpis**: Key performance indicators

### Best Practices

1. **Start with Status Filter**: Use `filters={"status": "Production"}` to find proven solutions
2. **Combine Search Terms**: Use multiple keywords for better results
3. **Check Multiple Domains**: Good ideas often transfer between industries
4. **Use Natural Language**: The agent search understands context
5. **Iterate Searches**: Start broad, then refine based on results

## 🚦 Running the Examples

1. Ensure the AI Registry server is installed:
```bash
pip install -r requirements.txt
```

2. Run any example:
```bash
python examples/basic_search.py
```

3. Or use in your own code:
```python
from apps.ai_registry.workflows import execute_simple_search

# Your code here
results = execute_simple_search("your query")
```

---

**Need help?** Start with `basic_search.py` and work your way up to more complex examples!
