"""
Enterprise-Grade Validators using 100% Kailash SDK Middleware

Leverages existing SDK components:
- SecurityMixin for automatic input validation and sanitization  
- Enhanced MCP Server for caching and performance tracking
- Existing data validation patterns from SDK templates
- Built-in security nodes and compliance workflows
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass

# Use 100% existing Kailash SDK middleware
from kailash.nodes.mixins import SecurityMixin
from kailash.nodes.base import Node
from kailash.nodes.transform import FilterNode, DataTransformer
from kailash.workflow import Workflow
from kailash.runtime import Runtime
from kailash.mcp import MCPServer

# Import existing validation patterns from SDK templates
from kailash.templates.data.validation import (
    validate_required_fields,
    validate_data_types,
    validate_constraints,
    validate_patterns,
    ValidationResult as SDKValidationResult
)

from .models import User, Tenant, Role, Permission


class UserValidator(SecurityMixin, Node):
    """User validation using 100% Kailash SDK components."""
    
    def __init__(self):
        super().__init__()
        # Use Enhanced MCP Server for caching validation results
        self.mcp_server = MCPServer("user-validator",
            enable_cache=True,
            enable_metrics=True,
            enable_formatting=True
        )
        
        # Register validation tools with caching
        self._register_validation_tools()
    
    def _register_validation_tools(self):
        """Register validation tools with MCP server."""
        
        @self.mcp_server.tool(
            cache_key="user_creation_validation",
            cache_ttl=300,  # 5 minutes cache
            format_response="json"
        )
        def validate_user_creation(user_data: dict) -> dict:
            """Cached user creation validation."""
            return self._validate_user_creation_internal(user_data)
        
        @self.mcp_server.tool(
            cache_key="user_update_validation", 
            cache_ttl=300,
            format_response="json"
        )
        def validate_user_update(user_data: dict) -> dict:
            """Cached user update validation."""
            return self._validate_user_update_internal(user_data)
    
    def validate_create_data(self, user_data: Dict[str, Any]) -> SDKValidationResult:
        """Validate user creation using SDK SecurityMixin and built-in validation."""
        
        # Use SecurityMixin for automatic input sanitization
        safe_data = self.validate_and_sanitize_inputs(user_data)
        
        # Log security event using SecurityMixin
        self.log_security_event("User validation started", level="INFO")
        
        # Use existing SDK validation patterns
        validation_rules = {
            "required_fields": ["username", "email"],
            "data_types": {
                "username": str,
                "email": str,
                "first_name": str,
                "last_name": str,
                "is_active": bool
            },
            "constraints": {
                "username": {"min_length": 3, "max_length": 50},
                "email": {"max_length": 254},
                "first_name": {"max_length": 100},
                "last_name": {"max_length": 100}
            },
            "patterns": {
                "email": r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
                "username": r'^[a-zA-Z0-9._-]+$'
            }
        }
        
        # Use SDK's built-in validation functions
        required_result = validate_required_fields(safe_data, validation_rules["required_fields"])
        types_result = validate_data_types(safe_data, validation_rules["data_types"])
        constraints_result = validate_constraints(safe_data, validation_rules["constraints"])
        patterns_result = validate_patterns(safe_data, validation_rules["patterns"])
        
        # Combine results using SDK patterns
        all_errors = (
            required_result.errors + 
            types_result.errors + 
            constraints_result.errors + 
            patterns_result.errors
        )
        
        is_valid = len(all_errors) == 0
        
        # Log validation result
        if is_valid:
            self.log_security_event("User validation passed", level="INFO")
        else:
            self.log_security_event("User validation failed", level="WARNING", 
                                  context={"errors": [str(e) for e in all_errors]})
        
        return SDKValidationResult(
            is_valid=is_valid,
            errors=all_errors,
            warnings=[],
            field_results={}
        )
    
    def validate_update_data(self, user_data: Dict[str, Any]) -> SDKValidationResult:
        """Validate user update using SDK components."""
        
        # Use SecurityMixin for input validation
        safe_data = self.validate_and_sanitize_inputs(user_data)
        
        # Log security event
        self.log_security_event("User update validation started", level="INFO")
        
        # Less strict validation for updates (no required fields)
        validation_rules = {
            "data_types": {
                "username": str,
                "email": str,
                "first_name": str,
                "last_name": str,
                "is_active": bool
            },
            "constraints": {
                "username": {"min_length": 3, "max_length": 50},
                "email": {"max_length": 254},
                "first_name": {"max_length": 100},
                "last_name": {"max_length": 100}
            },
            "patterns": {
                "email": r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
                "username": r'^[a-zA-Z0-9._-]+$'
            }
        }
        
        # Use SDK validation functions
        types_result = validate_data_types(safe_data, validation_rules["data_types"])
        constraints_result = validate_constraints(safe_data, validation_rules["constraints"])
        patterns_result = validate_patterns(safe_data, validation_rules["patterns"])
        
        all_errors = types_result.errors + constraints_result.errors + patterns_result.errors
        is_valid = len(all_errors) == 0
        
        return SDKValidationResult(
            is_valid=is_valid,
            errors=all_errors,
            warnings=[],
            field_results={}
        )


class RoleValidator(SecurityMixin, Node):
    """Role validation using 100% Kailash SDK components."""
    
    def __init__(self):
        super().__init__()
        self.mcp_server = MCPServer("role-validator",
            enable_cache=True,
            enable_metrics=True
        )
    
    def validate_create_data(self, role_data: Dict[str, Any]) -> SDKValidationResult:
        """Validate role creation using SDK SecurityMixin."""
        
        # Use SecurityMixin for input sanitization
        safe_data = self.validate_and_sanitize_inputs(role_data)
        
        # Log security event
        self.log_security_event("Role validation started", level="INFO")
        
        # Use SDK validation patterns
        validation_rules = {
            "required_fields": ["name"],
            "data_types": {
                "name": str,
                "description": str,
                "permissions": list,
                "is_assignable": bool
            },
            "constraints": {
                "name": {"min_length": 2, "max_length": 100},
                "description": {"max_length": 500}
            },
            "patterns": {
                "name": r'^[a-zA-Z0-9\s_-]+$'
            }
        }
        
        # Use SDK's built-in validation
        required_result = validate_required_fields(safe_data, validation_rules["required_fields"])
        types_result = validate_data_types(safe_data, validation_rules["data_types"])
        constraints_result = validate_constraints(safe_data, validation_rules["constraints"])
        patterns_result = validate_patterns(safe_data, validation_rules["patterns"])
        
        all_errors = (
            required_result.errors + 
            types_result.errors + 
            constraints_result.errors + 
            patterns_result.errors
        )
        
        is_valid = len(all_errors) == 0
        
        return SDKValidationResult(
            is_valid=is_valid,
            errors=all_errors,
            warnings=[],
            field_results={}
        )


class SecurityValidator(SecurityMixin, Node):
    """Security validation using 100% Kailash SDK security patterns."""
    
    def __init__(self):
        super().__init__()
        # Enhanced MCP Server provides automatic security monitoring
        self.mcp_server = MCPServer("security-validator",
            enable_cache=True,
            enable_metrics=True,
            enable_formatting=True
        )
    
    def validate_security_context(self, context_data: Dict[str, Any]) -> SDKValidationResult:
        """Validate security context using SDK SecurityMixin."""
        
        # SecurityMixin automatically handles:
        # - Input sanitization
        # - Threat detection
        # - Security event logging
        safe_data = self.validate_and_sanitize_inputs(context_data)
        
        # Log security validation
        self.log_security_event("Security context validation", level="INFO")
        
        # Use existing SDK security validation patterns
        validation_rules = {
            "required_fields": ["ip_address", "user_agent"],
            "data_types": {
                "ip_address": str,
                "user_agent": str,
                "session_id": str
            },
            "patterns": {
                # Basic IP validation pattern
                "ip_address": r'^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$'
            }
        }
        
        # Use SDK validation
        required_result = validate_required_fields(safe_data, validation_rules["required_fields"])
        types_result = validate_data_types(safe_data, validation_rules["data_types"])
        patterns_result = validate_patterns(safe_data, validation_rules["patterns"])
        
        all_errors = required_result.errors + types_result.errors + patterns_result.errors
        is_valid = len(all_errors) == 0
        
        return SDKValidationResult(
            is_valid=is_valid,
            errors=all_errors,
            warnings=[],
            field_results={}
        )
