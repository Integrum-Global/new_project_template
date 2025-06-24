"""
Role-based filters for RAG operations.

This module provides filtering capabilities based on user roles
and permissions for RAG operations.

Implementation Guidelines:
1. Define FilterRule dataclass with:
   - role: User role name
   - allowed_tags: Set of permitted document tags
   - excluded_tags: Set of forbidden document tags
   - metadata_filters: Dict of required metadata values
2. Implement rule management (add, update, remove rules)
3. Filter documents based on:
   - Document tags
   - Document metadata
   - User roles and permissions
4. Integrate with AccessControlManager for permission checks
5. Support dynamic rule loading from configuration
6. Add audit logging for filter applications

Filter Operations:
- Define role-based access rules
- Filter document lists based on user role
- Generate search filters for vector queries
- Support hierarchical roles (inheritance)
- Handle special cases (admin, public access)
- Provide filter explanations for debugging
"""
