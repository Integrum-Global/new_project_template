"""
Main gateway orchestrator for the application.

This module contains the main gateway class that orchestrates
all services and provides the primary interface for the application.

Implementation Guidelines:
1. Use kailash_sdk.gateway.create_gateway() for production apps
2. Initialize LocalRuntime for execution
3. Coordinate between all services (RAG, SharePoint, MCP, etc.)
4. Handle request routing and response aggregation
5. Integrate with authentication and session management
6. Implement proper error handling and logging
7. Consider implementing health checks and monitoring

Gateway Responsibilities:
- Service initialization and lifecycle management
- Request validation and routing
- Response aggregation and transformation
- Cross-cutting concerns (auth, logging, monitoring)
- API endpoint management
"""
