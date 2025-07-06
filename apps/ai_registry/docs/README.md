# AI Registry MCP Server Documentation

## Overview

The AI Registry MCP Server provides Claude Desktop with tools to query and analyze 187 AI use cases across 24 domains. It's one of several specialized MCP servers in the platform.

## 📚 Documentation Contents

### Setup & Configuration
- **[Claude Desktop Setup](/docs/source/getting_started/claude_desktop_setup.md)** - Platform guide for configuring MCP servers with Claude Desktop
- **[TESTING_GUIDE.md](TESTING_GUIDE.md)** - How to test the AI Registry server

### Implementation Details
- **[IMPLEMENTATION.md](IMPLEMENTATION.md)** - Technical implementation using Kailash SDK
- **[TECHNICAL_REVIEW.md](TECHNICAL_REVIEW.md)** - Architecture and design decisions
- **[TEST_SUMMARY.md](TEST_SUMMARY.md)** - Test results and validation

### API Documentation
- **[api/](api/)** - Auto-generated API documentation for nodes and classes

## 🚀 Quick Start

### Launch the Server
```bash
# From project root
python -m apps.ai_registry

# With options
python -m apps.ai_registry --debug --disable-cache
```

### Configure in Claude Desktop
Add to `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "ai-registry": {
      "command": "python",
      "args": ["-m", "apps.ai_registry"],
      "cwd": "/path/to/mcp_server"
    }
  }
}
```

## 🛠️ Available Tools

The server provides 11 MCP tools:
1. `search_use_cases` - Full-text search
2. `filter_by_domain` - Filter by application domain
3. `filter_by_ai_method` - Filter by AI method
4. `filter_by_status` - Filter by implementation status
5. `get_use_case_details` - Get specific use case
6. `get_statistics` - Registry statistics
7. `list_domains` - List all domains
8. `list_ai_methods` - List all AI methods
9. `find_similar_cases` - Find similar use cases
10. `analyze_trends` - Analyze AI trends
11. `health_check` - Server health status

## 📁 Module Structure

```
ai_registry/
├── __main__.py          # Entry point
├── mcp_server.py        # Enhanced MCP Server
├── indexer.py           # Search indexer
├── config.py            # Configuration
├── data/                # Registry data & PDFs
├── nodes/               # Custom Kailash nodes
├── workflows/           # Kailash workflows
├── examples/            # Usage examples
├── tests/               # Test suite
└── docs/                # This documentation
```

## 🔗 Related Documentation

- **Platform Documentation**: See `/docs/` for platform-wide concepts
- **Module Tasks**: See `todos/000-master.md` for current development tasks
- **Architecture Decisions**: See `adr/` for module design decisions
