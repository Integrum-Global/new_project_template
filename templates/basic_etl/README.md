# Basic ETL Pipeline Template

A simple Extract-Transform-Load (ETL) workflow template for processing CSV data with the Kailash SDK.

## Overview

This template provides a foundation for building ETL pipelines that:
- Extract data from CSV files
- Transform data with filtering, sorting, and calculations
- Load processed data to output files

## Features

- CSV file reading and writing
- Data filtering based on conditions
- Sorting by specified columns
- Calculated columns
- Configuration management
- Error handling
- Comprehensive examples and tests

## Quick Start

1. **Copy this template to your solution:**
   ```bash
   cp -r templates/basic_etl/* src/solutions/my_etl_solution/
   ```

2. **Configure your pipeline:**
   Edit `config.yaml` with your specific settings:
   ```yaml
   input_file: "data/my_data.csv"
   output_file: "data/processed_data.csv"
   threshold: 1000
   sort_column: "value"
   ```

3. **Run the pipeline:**
   ```bash
   python -m solutions.my_etl_solution
   ```

## Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `input_file` | string | "data/input.csv" | Path to input CSV file |
| `output_file` | string | "data/output.csv" | Path to output CSV file |
| `delimiter` | string | "," | CSV delimiter character |
| `has_header` | boolean | true | Whether input has header row |
| `threshold` | number | 0 | Filter values greater than this |
| `sort_column` | string | "value" | Column to sort by |
| `sort_descending` | boolean | false | Sort in descending order |

## Environment Variables

Override configuration with environment variables:
- `ETL_INPUT_FILE` - Input file path
- `ETL_OUTPUT_FILE` - Output file path
- `ETL_DELIMITER` - CSV delimiter
- `ETL_THRESHOLD` - Filter threshold
- `ETL_SORT_COLUMN` - Sort column name

## Customization Guide

### Adding Custom Transformations

Edit the `operations` list in `workflow.py`:

```python
operations=[
    {"type": "filter", "condition": "status == 'active'"},
    {"type": "calculate", "column": "tax", "formula": "amount * 0.08"},
    {"type": "aggregate", "group_by": "category", "agg_func": "sum"}
]
```

### Adding New Data Sources

Replace `CSVReaderNode` with other readers:
- `JSONReaderNode` - For JSON files
- `DatabaseReaderNode` - For database queries
- `APIReaderNode` - For API endpoints

### Custom Processing Logic

Add a `PythonCodeNode` for custom logic:

```python
workflow.add_node(
    "custom_process",
    PythonCodeNode,
    code="""
def execute(data):
    # Your custom processing logic
    return {"processed": transformed_data}
"""
)
```

## Examples

See the `examples/` directory for:
- `basic_usage.py` - Simple ETL pipeline
- `advanced_usage.py` - Complex transformations with multiple steps

## Testing

Run the test suite:
```bash
pytest tests/
```

## Common Use Cases

1. **Sales Data Processing**
   - Filter transactions above threshold
   - Calculate totals and taxes
   - Sort by date or amount

2. **Log File Analysis**
   - Parse log entries
   - Filter by severity
   - Aggregate by time periods

3. **Data Cleaning**
   - Remove duplicates
   - Handle missing values
   - Standardize formats

## Troubleshooting

### "Input file not found"
- Check the file path in config.yaml
- Ensure the data directory exists
- Use absolute paths if needed

### "Column not found"
- Verify column names match your CSV headers
- Check if `has_header` is set correctly
- Print column names for debugging

### Memory issues with large files
- Process in chunks using batch size
- Use streaming nodes for large datasets
- Increase available memory

## Next Steps

1. Customize the transformation operations
2. Add error handling for your use case
3. Implement data validation
4. Add monitoring and logging
5. Create comprehensive tests