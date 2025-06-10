# Mistakes Reference - Quick Error Lookup

## 🚨 Critical Solution Development Issues

### **Config vs Runtime Parameters** (#1 Issue!)
- **Problem**: Mixing configuration (HOW) with runtime data (WHAT)
- **Solution**: Config = paths/settings, Runtime = data flow
- **Example**: `file_path="data.csv"` (config) vs data passed through connections (runtime)

### **Node Naming Convention Errors**
- **Problem**: Missing "Node" suffix in class names
- **Solution**: All node classes end with "Node": `CSVReaderNode`, `LLMAgentNode`

### **Hardcoded Credentials**
- **Problem**: API keys and secrets in code
- **Solution**: Always use environment variables and secure configuration

### **Missing Error Handling**
- **Problem**: Production failures due to unhandled external system errors
- **Solution**: Implement retry logic, circuit breakers, and graceful degradation

### **Unvalidated External Data**
- **Problem**: Assuming external APIs return expected data formats
- **Solution**: Always validate data schemas and handle missing/malformed data

## 📋 Quick Error Resolution

### API Integration Issues
- Check `reference/cheatsheet/013-api-integration.md` for patterns
- Validate request/response formats
- Implement proper authentication and rate limiting

### Performance Problems
- Use connection pooling for databases
- Implement caching for frequently accessed data
- Monitor resource usage and optimize bottlenecks

### Deployment Failures
- Validate environment configuration
- Check dependency versions and compatibility
- Test with production-like data volumes

## 🔗 Detailed Mistake Catalog
See `mistakes/README.md` for complete categorized mistake reference with solutions and prevention strategies.

**Current session mistakes**: Track new issues in `mistakes/current-session-mistakes.md` during development.
