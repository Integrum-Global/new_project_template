"""
SharePoint Connector MCP Server using Kailash SDK.

This server provides MCP tools for integrating with SharePoint Online,
enabling document retrieval, metadata extraction, and content analysis.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from kailash import NodeParameter
from kailash.middleware.mcp import MiddlewareMCPServer as MCPServer
from kailash.nodes.data import SharePointGraphReaderEnhanced
from kailash.runtime import LocalRuntime
from kailash.workflow import Workflow

logger = logging.getLogger(__name__)


class SharePointConnectorServer:
    """
    MCP Server for SharePoint integration using Kailash SDK.

    Features:
    - Document retrieval from SharePoint libraries
    - Metadata extraction and indexing
    - Full-text search across SharePoint content
    - Permission-aware content filtering
    - Bulk document processing workflows
    """

    def __init__(
        self,
        config_file: Optional[str] = None,
        config_override: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize SharePoint Connector Server.

        Args:
            config_file: Path to YAML configuration file
            config_override: Optional configuration overrides
        """
        # Initialize Enhanced MCP Server
        self.server = MCPServer(
            name="sharepoint-connector",
            config_file=config_file,
            enable_cache=True,
            cache_ttl=600,  # 10 minute default for SharePoint data
            enable_metrics=True,
            enable_formatting=True,
        )

        # Initialize runtime for workflow execution
        self.runtime = LocalRuntime(
            enable_async=True, max_concurrency=5  # Limit concurrent SharePoint requests
        )

        # Store config for SharePoint node initialization
        self.config = config_override or {}

        # Set up tools and resources
        self._setup_tools()
        self._setup_resources()
        self._setup_workflows()

    def _create_sharepoint_node(self, **kwargs) -> SharePointGraphReaderEnhanced:
        """Create a configured SharePoint node."""
        return SharePointGraphReaderEnhanced(
            name=kwargs.get("name", "sharepoint_reader"),
            tenant_id=self.config.get("sharepoint.tenant_id"),
            client_id=self.config.get("sharepoint.client_id"),
            client_secret=self.config.get("sharepoint.client_secret"),
            site_url=self.config.get("sharepoint.site_url"),
            **kwargs,
        )

    def _setup_tools(self):
        """Set up SharePoint MCP tools."""

        @self.server.tool(
            cache_key="list_documents",
            cache_ttl=300,  # 5 minute cache
            format_response="markdown",
        )
        def list_documents(
            library_name: str = "Documents",
            folder_path: Optional[str] = None,
            limit: int = 50,
        ) -> dict:
            """List documents in a SharePoint library."""
            node = self._create_sharepoint_node(name="doc_lister")

            try:
                # Create workflow for document listing
                workflow = Workflow("list_docs", "List SharePoint documents")
                workflow.add_node("reader", node)

                parameters = {
                    "library_name": library_name,
                    "folder_path": folder_path or "/",
                    "limit": limit,
                }

                result, _ = self.runtime.execute(workflow, parameters=parameters)

                return {
                    "success": True,
                    "library": library_name,
                    "folder": folder_path or "/",
                    "documents": result.get("reader", {}).get("documents", []),
                    "count": len(result.get("reader", {}).get("documents", [])),
                }
            except Exception as e:
                logger.error(f"Error listing documents: {e}")
                return {"success": False, "error": str(e), "library": library_name}

        @self.server.tool(
            cache_key="get_document",
            cache_ttl=3600,  # 1 hour cache for documents
            format_response="markdown",
        )
        def get_document(
            document_path: str,
            include_content: bool = True,
            include_metadata: bool = True,
        ) -> dict:
            """Retrieve a specific document from SharePoint."""
            node = self._create_sharepoint_node(name="doc_getter")

            try:
                workflow = Workflow("get_doc", "Get SharePoint document")
                workflow.add_node("reader", node)

                parameters = {
                    "document_path": document_path,
                    "include_content": include_content,
                    "include_metadata": include_metadata,
                }

                result, _ = self.runtime.execute(workflow, parameters=parameters)
                doc_data = result.get("reader", {})

                return {
                    "success": True,
                    "path": document_path,
                    "document": doc_data.get("document"),
                    "metadata": doc_data.get("metadata") if include_metadata else None,
                    "content": doc_data.get("content") if include_content else None,
                }
            except Exception as e:
                logger.error(f"Error getting document: {e}")
                return {"success": False, "error": str(e), "path": document_path}

        @self.server.tool(
            cache_key="search_documents", cache_ttl=300, format_response="search"
        )
        def search_documents(
            query: str,
            library_name: Optional[str] = None,
            file_types: Optional[List[str]] = None,
            limit: int = 20,
        ) -> dict:
            """Search for documents across SharePoint."""
            node = self._create_sharepoint_node(name="doc_searcher")

            try:
                workflow = Workflow("search_docs", "Search SharePoint documents")
                workflow.add_node("searcher", node)

                parameters = {
                    "query": query,
                    "library_name": library_name,
                    "file_types": file_types or [],
                    "limit": limit,
                }

                result, _ = self.runtime.execute(workflow, parameters=parameters)
                search_results = result.get("searcher", {}).get("results", [])

                return {
                    "success": True,
                    "query": query,
                    "total_results": len(search_results),
                    "results": search_results,
                    "filters": {"library": library_name, "file_types": file_types},
                }
            except Exception as e:
                logger.error(f"Error searching documents: {e}")
                return {"success": False, "error": str(e), "query": query}

        @self.server.tool(
            cache_key="get_metadata",
            cache_ttl=1800,  # 30 minute cache
            format_response="json",
        )
        def get_document_metadata(document_path: str) -> dict:
            """Get detailed metadata for a SharePoint document."""
            node = self._create_sharepoint_node(name="metadata_reader")

            try:
                workflow = Workflow("get_metadata", "Get document metadata")
                workflow.add_node("reader", node)

                parameters = {
                    "document_path": document_path,
                    "include_content": False,
                    "include_metadata": True,
                    "include_permissions": True,
                }

                result, _ = self.runtime.execute(workflow, parameters=parameters)
                metadata = result.get("reader", {}).get("metadata", {})

                return {
                    "success": True,
                    "path": document_path,
                    "metadata": metadata,
                    "permissions": result.get("reader", {}).get("permissions", {}),
                    "last_modified": metadata.get("modified"),
                    "created": metadata.get("created"),
                    "author": metadata.get("author"),
                }
            except Exception as e:
                logger.error(f"Error getting metadata: {e}")
                return {"success": False, "error": str(e), "path": document_path}

        @self.server.tool(format_response="markdown")
        def bulk_download_documents(
            library_name: str,
            output_dir: str,
            file_types: Optional[List[str]] = None,
            modified_after: Optional[str] = None,
        ) -> dict:
            """Bulk download documents from SharePoint library."""
            node = self._create_sharepoint_node(name="bulk_downloader")

            try:
                # Create workflow for bulk download
                workflow = Workflow(
                    "bulk_download", "Bulk download SharePoint documents"
                )
                workflow.add_node("downloader", node)

                parameters = {
                    "library_name": library_name,
                    "output_dir": output_dir,
                    "file_types": file_types or [],
                    "modified_after": modified_after,
                }

                result, _ = self.runtime.execute(workflow, parameters=parameters)
                download_results = result.get("downloader", {})

                return {
                    "success": True,
                    "library": library_name,
                    "output_directory": output_dir,
                    "downloaded_count": download_results.get("count", 0),
                    "downloaded_files": download_results.get("files", []),
                    "total_size": download_results.get("total_size", 0),
                    "filters_applied": {
                        "file_types": file_types,
                        "modified_after": modified_after,
                    },
                }
            except Exception as e:
                logger.error(f"Error in bulk download: {e}")
                return {"success": False, "error": str(e), "library": library_name}

    def _setup_resources(self):
        """Set up SharePoint MCP resources."""

        @self.server.resource(uri="sharepoint://libraries")
        def list_libraries() -> dict:
            """List all available SharePoint libraries."""
            return {
                "libraries": self.config.get(
                    "sharepoint.libraries", ["Documents", "Reports", "Archives"]
                ),
                "site_url": self.config.get(
                    "sharepoint.site_url",
                    "https://company.sharepoint.com/sites/default",
                ),
            }

        @self.server.resource(uri="sharepoint://config")
        def get_sharepoint_config() -> dict:
            """Get current SharePoint configuration."""
            return {
                "site_url": self.config.get("sharepoint.site_url"),
                "tenant_id": self.config.get("sharepoint.tenant_id"),
                "libraries": self.config.get("sharepoint.libraries", []),
                "default_library": self.config.get(
                    "sharepoint.default_library", "Documents"
                ),
            }

        @self.server.resource(uri="sharepoint://statistics")
        def get_statistics() -> dict:
            """Get SharePoint usage statistics."""
            # In production, this would query actual SharePoint analytics
            return {
                "total_documents": 0,
                "total_libraries": len(self.config.get("sharepoint.libraries", [])),
                "last_sync": datetime.now().isoformat(),
                "storage_used_gb": 0.0,
            }

    def _setup_workflows(self):
        """Set up pre-defined SharePoint workflows."""

        @self.server.tool(
            cache_key="sync_to_registry", cache_ttl=3600, format_response="markdown"
        )
        def sync_sharepoint_to_registry(
            library_name: str = "AI_Use_Cases",
            output_path: str = "data/sharepoint_sync.json",
        ) -> dict:
            """Sync SharePoint documents to AI Registry format."""
            # This would create a workflow that:
            # 1. Lists all documents in the library
            # 2. Extracts metadata and content
            # 3. Transforms to AI Registry format
            # 4. Saves to output file

            return {
                "success": True,
                "message": "Sync workflow initiated",
                "library": library_name,
                "output": output_path,
                "status": "This is a placeholder - implement full workflow",
            }

        @self.server.tool(format_response="markdown")
        def analyze_document_trends(library_name: str, days_back: int = 30) -> dict:
            """Analyze document creation and modification trends."""
            # This would create a workflow that analyzes document activity

            return {
                "success": True,
                "library": library_name,
                "period_days": days_back,
                "trends": {
                    "documents_created": 0,
                    "documents_modified": 0,
                    "most_active_users": [],
                    "popular_file_types": [],
                },
                "status": "This is a placeholder - implement full workflow",
            }

    def run(self):
        """Start the SharePoint Connector MCP server."""
        logger.info("Starting SharePoint Connector MCP Server...")
        self.server.run()
