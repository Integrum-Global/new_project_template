# ⚠️ Top 15 Mistakes SDK Users Make

Learn from others' errors to build better solutions faster.

---

## 1. 📝 Editing sdk-users/ Directory

### ❌ **Wrong**: Modifying SDK documentation
```bash
# DON'T DO THIS!
vim sdk-users/workflows/my_custom_workflow.py
# or
echo "my fix" >> sdk-users/nodes/README.md
```

### ✅ **Right**: Use as reference only
```
"Show me the ETL pattern from sdk-users/workflows/"
"I'll implement my version in src/solutions/data_pipeline/"
```

### **Why it matters**: The entire `sdk-users/` directory is synced from template and changes will be LOST

---

## 2. 🗂️ Wrong Directory for Code

### ❌ **Wrong**: Creating files in wrong locations
```bash
# Don't put solution code here
touch workflows/my_solution.py
touch sdk-users/custom/my_node.py
touch my_workflow.py  # in root
```

### ✅ **Right**: Always use src/solutions/
```bash
# Correct structure
src/solutions/my_module/
├── __init__.py
├── workflows/
│   └── my_workflow.py
├── nodes/
│   └── custom_node.py
└── examples/
    └── example.py
```

### **Why it matters**: Proper structure ensures maintainability and prevents sync conflicts

---

## 3. 💭 Not Using Claude Code

### ❌ **Wrong**: Struggling alone
```python
# Spending hours trying to figure out the right pattern
# Googling random Python solutions
# Writing everything from scratch
```

### ✅ **Right**: Ask Claude Code first
```
"Show me how to implement data validation using Kailash SDK"
"What's the best pattern for processing CSV files with transformations?"
"Help me debug this DataTransformer error"
```

### **Why it matters**: Claude Code knows SDK patterns and saves hours of trial and error

---

## 4. 📋 Manual TODO Management

### ❌ **Wrong**: Editing todos/000-master.md directly
```bash
vim todos/000-master.md
# Manually updating task status
```

### ✅ **Right**: Update through conversation
```
"Update: Completed data ingestion module, starting transformation logic"
"I'm blocked on API authentication - need help with OAuth flow"
```

### **Why it matters**: Automated tracking maintains consistency and history

---

## 5. 🔍 Not Checking Existing Patterns

### ❌ **Wrong**: Reinventing the wheel
```python
# Writing custom CSV parser
def my_csv_reader():
    # 100 lines of custom code
```

### ✅ **Right**: Use SDK patterns
```
"Show me CSV processing examples from sdk-users/workflows/"
"What nodes already exist for file processing?"
```

### **Why it matters**: SDK has battle-tested patterns for common tasks

---

## 6. 🏗️ Poor Module Structure

### ❌ **Wrong**: Everything in one file
```python
# src/solutions/everything.py
# 1000+ lines of mixed concerns
```

### ✅ **Right**: Organized modules
```
src/solutions/customer_analytics/
├── __init__.py
├── config.py
├── workflows/
│   ├── __init__.py
│   ├── ingestion.py
│   └── analysis.py
├── nodes/
│   └── custom_validator.py
└── examples/
    └── run_analytics.py
```

### **Why it matters**: Maintainable, testable, reusable solutions

---

## 7. 🐛 Skipping Error Handling

### ❌ **Wrong**: Happy path only
```python
data = workflow.run()  # What if this fails?
process_data(data)     # No validation
```

### ✅ **Right**: Robust implementation
```python
try:
    result = workflow.run()
    if result.success:
        process_data(result.data)
    else:
        handle_error(result.error)
except Exception as e:
    log_error(f"Workflow failed: {e}")
```

### **Why it matters**: Production solutions need proper error handling

---

## 8. 📚 Ignoring SDK Best Practices

### ❌ **Wrong**: Using wrong node names
```python
# Common naming mistakes
workflow.add_node("csv_reader", CSVReader())  # Wrong!
workflow.add_node("transform", DataTransform())  # Wrong!
```

### ✅ **Right**: Follow SDK conventions
```python
# Correct node names
workflow.add_node("reader", CSVReaderNode())
workflow.add_node("transformer", DataTransformer())
```

### **Why it matters**: Consistency prevents subtle bugs

---

## 9. 🔗 Bad Workflow Connections

### ❌ **Wrong**: Incorrect mapping
```python
# This causes "result" to override itself
workflow.connect("processor", "output", mapping={"result": "result"})
```

### ✅ **Right**: Proper field mapping
```python
# Map to different field names
workflow.connect("processor", "output", mapping={"result": "processed_data"})
```

### **Why it matters**: Prevents data loss and confusion

---

## 10. 📝 No Documentation

### ❌ **Wrong**: Code without context
```python
def process():
    # Complex logic with no explanation
    return x * 2.4 + y / 3.7
```

### ✅ **Right**: Document decisions
```python
def calculate_risk_score(base_score: float, modifier: float) -> float:
    """
    Calculate risk score using client's proprietary formula.

    Formula: base * 2.4 + modifier / 3.7
    Documented in ADR-001: Risk Calculation Methodology
    """
    return base_score * 2.4 + modifier / 3.7
```

### **Why it matters**: Future maintainers need to understand why

---

## 11. 🧪 Not Testing Solutions

### ❌ **Wrong**: "It works on my machine"
```python
# No tests, just hope it works
```

### ✅ **Right**: Test with real scenarios
```python
def test_customer_workflow():
    """Test with sample customer data"""
    workflow = create_customer_workflow()
    result = workflow.run(test_data)
    assert result.success
    assert len(result.data) == expected_count
```

### **Why it matters**: Catch issues before production

---

## 12. 🎯 Vague Requirements

### ❌ **Wrong**: Starting without clarity
```
"I'll build a data processor"  # What kind? For what data?
```

### ✅ **Right**: Get specific requirements
```
"Help me understand these requirements:
- Process daily sales CSV files (10MB average)
- Validate against product catalog
- Generate summary reports
- Send to dashboard API"
```

### **Why it matters**: Clear requirements lead to correct solutions

---

## 13. 🔄 Not Tracking Progress

### ❌ **Wrong**: Radio silence for days
```
# Working in isolation
# No updates to team
# Surprise "it's not working" at deadline
```

### ✅ **Right**: Regular updates
```
"Morning update: Starting customer validation module"
"Afternoon: Completed validation, found edge case with international addresses"
"EOD: Module working, tomorrow will add error recovery"
```

### **Why it matters**: Early visibility prevents last-minute surprises

---

## 14. 🚀 Premature Optimization

### ❌ **Wrong**: Over-engineering from start
```python
# Building distributed system for 100 rows of data
# Creating abstract factories for 2 node types
```

### ✅ **Right**: Start simple, iterate
```python
# Version 1: Get it working
basic_workflow = create_simple_pipeline()

# Version 2: Add features as needed
enhanced_workflow = add_error_handling(basic_workflow)
```

### **Why it matters**: Working solution > perfect architecture

---

## 15. 🔧 Not Using Development Tools

### ❌ **Wrong**: print() debugging only
```python
print("here")
print(data)
print("now here")
```

### ✅ **Right**: Use proper tools
```python
# Use logging
logger.info(f"Processing batch: {batch_id}")

# Use debugger
import pdb; pdb.set_trace()

# Use Claude Code
"Help me debug this error: [full stack trace]"
```

### **Why it matters**: Professional tools save time

---

## 🎯 Quick Reference: Mistake Prevention

### Before Starting
- ✅ Understand requirements fully
- ✅ Check SDK patterns first
- ✅ Plan structure in src/solutions/
- ✅ Never edit sdk-users/

### During Development
- ✅ Use Claude Code for guidance
- ✅ Follow SDK conventions
- ✅ Update progress regularly
- ✅ Handle errors properly

### Before Finishing
- ✅ Test with real data
- ✅ Document decisions
- ✅ Create working examples
- ✅ Update all tracking

---

## 💡 Remember

**The Golden Rules:**
1. **sdk-users/** is READ-ONLY
2. **src/solutions/** is for YOUR code
3. **Claude Code** is your pair programmer
4. **Progress updates** keep everyone informed
5. **SDK patterns** exist for a reason

*Make mistakes, learn fast, build better!*
