# QA Agentic Testing - Test Suite

## 📁 Directory Structure

```
tests/
├── unit/                    # Unit tests for individual components
├── integration/             # Integration tests for component interactions
├── functional/              # Functional tests for complete features
├── performance/             # Performance and load tests
└── run_all_tests.py        # Main test runner with HTML report generation
```

## 🚀 Running Tests

### Run All Tests
```bash
python tests/run_all_tests.py
```

### Run Individual Test Categories
```bash
# Unit tests
python tests/unit/test_basic_functionality.py
python tests/unit/test_working_components.py
python tests/unit/test_report_generation.py

# Integration tests
python tests/integration/test_complete_functionality.py
python tests/integration/final_validation_test.py

# Full test suite
python tests/run_all_tests.py
```

## 📊 Test Results

All test results are saved to the `qa_results/` directory:

- `test_suite_results.json` - Complete test results in JSON format
- `test_suite_report.html` - Interactive HTML report with visualizations
- Individual test result files (e.g., `basic_functionality_results.json`)

## 📄 HTML Report Format

The HTML report includes:

### 1. Overview Tab
- Executive summary with success rate
- Key metrics (coverage, execution time, etc.)
- Visual test distribution chart
- High-level insights

### 2. Methodology Tab
- 4-step validation process explanation
- Application discovery results
- Test coverage matrix by scenario type

### 3. Personas Tab
- All test personas with roles and permissions
- Visual permission matrix
- Behavioral patterns and goals

### 4. Results Tab
- Detailed test results table
- Filtering by status (pass/fail/warning)
- Individual test details and confidence scores

### 5. Validation Tab
- Pass/fail criteria for each test type
- Validation strategy explanation
- Permission-based testing details

### 6. AI Insights Tab
- LLM analysis results (when available)
- Consensus findings across multiple agents
- Recommendations for improvements

### 7. Performance Tab
- Performance metrics and timing analysis
- Visual performance distribution
- Slowest/fastest test identification

## 🔧 Best Practices

### When Writing Tests

1. **Always save results to qa_results/**
   ```python
   from tests import get_results_path

   results_file = get_results_path("my_test_results.json")
   ```

2. **Include comprehensive metadata**
   ```python
   test_data = {
       "test_name": "My Test",
       "timestamp": datetime.now().isoformat(),
       "results": {...},
       "summary": {...}
   }
   ```

3. **Use proper test categorization**
   - Unit tests: Test individual components in isolation
   - Integration tests: Test component interactions
   - Functional tests: Test complete user workflows
   - Performance tests: Test speed and scalability

4. **Return proper exit codes**
   ```python
   if __name__ == "__main__":
       success = asyncio.run(test_function())
       sys.exit(0 if success else 1)
   ```

## 📈 HTML Report Features

The report generator creates a comprehensive, interactive HTML report with:

- **Responsive Design**: Works on desktop and mobile
- **Interactive Charts**: Visual representation of test results
- **Tabbed Navigation**: Easy access to different report sections
- **Filtering**: Filter results by status, persona, or test type
- **Performance Metrics**: Detailed timing and throughput analysis
- **Export Options**: Download results as JSON

## 🎨 Report Styling

The HTML report uses:
- Modern gradient headers
- Color-coded status indicators
- Interactive hover effects
- Responsive grid layouts
- Clear typography and spacing

## 🔄 Continuous Integration

The test suite is designed to work with CI/CD pipelines:

1. Exit codes indicate success/failure
2. JSON output can be parsed by CI tools
3. HTML reports can be archived as artifacts
4. Performance metrics can trigger alerts

## 📝 Adding New Tests

1. Create test file in appropriate directory
2. Import common utilities:
   ```python
   from tests import get_results_path
   ```
3. Save results to qa_results/
4. Add test to appropriate category in `run_all_tests.py`

## 🐛 Troubleshooting

- **Import errors**: Ensure proper sys.path setup
- **File not found**: Check test file locations
- **Permission errors**: Ensure qa_results/ is writable
- **Timeout issues**: Adjust timeout in test runner
