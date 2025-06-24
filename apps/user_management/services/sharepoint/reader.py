"""
SharePoint document reader integration.

This module provides functionality to read and process documents
from SharePoint.

Implementation Guidelines:
1. Use OAuth2Node from kailash_sdk for authentication
2. Implement SharePoint REST API integration
3. Handle various document types (docx, xlsx, pdf, etc.)
4. Support both SharePoint Online and On-Premises
5. Implement connection pooling and retry logic
6. Add document metadata extraction
7. Consider using DirectoryReaderNode for batch operations

SharePoint Operations:
- Authenticate using OAuth2 (client credentials or user delegation)
- List documents and folders with metadata
- Read document contents (with format conversion if needed)
- Search documents using SharePoint Search API
- Download documents to local storage
- Handle permissions and access control
- Support document versioning
- Implement change tracking/delta queries
"""
