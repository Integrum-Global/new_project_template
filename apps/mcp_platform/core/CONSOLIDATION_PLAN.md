# MCP Applications Consolidation Plan

## Current Structure (Fragmented)
```
apps/
├── mcp/                      # Main MCP platform
├── mcp_ai_assistant/         # AI-powered MCP tools
├── mcp_data_pipeline/        # Data processing MCP tools
├── mcp_enterprise_gateway/   # Enterprise features
├── mcp_integration_patterns/ # Integration examples
├── mcp_tools_server/         # General MCP tools
└── user_management/services/mcp/  # User mgmt MCP integration
```

## Proposed Consolidated Structure
```
apps/mcp/
├── README.md                 # Main MCP documentation
├── core/                     # Core MCP platform (current apps/mcp/core)
│   ├── gateway.py
│   ├── registry.py
│   ├── security.py
│   └── services.py
├── servers/                  # All MCP server implementations
│   ├── ai_assistant/         # From mcp_ai_assistant
│   ├── data_pipeline/        # From mcp_data_pipeline
│   ├── enterprise_gateway/   # From mcp_enterprise_gateway
│   ├── tools_server/         # From mcp_tools_server
│   └── user_management/      # From user_management/services/mcp
├── patterns/                 # From mcp_integration_patterns
│   ├── basic/
│   ├── advanced/
│   └── examples/
├── api/                      # Unified API layer
├── workflows/                # MCP workflows
├── tests/                    # Consolidated tests
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── docker/                   # Docker configurations
│   ├── Dockerfile.platform   # Main platform
│   ├── Dockerfile.ai         # AI assistant
│   ├── Dockerfile.data       # Data pipeline
│   └── docker-compose.yml    # Full stack
└── docs/                     # Consolidated documentation
```

## Benefits of Consolidation

1. **Single Entry Point**: One clear location for all MCP functionality
2. **Shared Core**: All servers use the same core platform code
3. **Unified Testing**: Single test suite for all MCP components
4. **Better Discovery**: Easier to find and understand all MCP capabilities
5. **Reduced Duplication**: Share common code, configs, and utilities
6. **Simplified Deployment**: One docker-compose for entire MCP stack

## Migration Steps

1. Create the new structure in `apps/mcp/`
2. Move server implementations to `servers/` subdirectory
3. Consolidate documentation
4. Update imports and references
5. Merge test suites
6. Update Docker configurations
7. Remove old directories

## Backwards Compatibility

- Keep import aliases for a transition period
- Update documentation with migration guide
- Provide scripts to update existing code references
