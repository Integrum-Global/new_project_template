"""
Studio Data Models - Using Middleware Database Layer

Studio-specific extensions to the middleware base models.
All common functionality is inherited from middleware.
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.orm import validates

# Import base models and enums from middleware
from kailash.middleware.database.base_models import (
    BaseWorkflowModel, BaseExecutionModel, BaseTemplateModel,
    BaseSecurityEventModel, BaseAuditLogModel, BaseComplianceModel
)
from kailash.middleware.database.enums import (
    WorkflowStatus, ExecutionStatus, NodeType,
    TemplateCategory, SecurityEventType, ComplianceFramework
)
from kailash.middleware.database.models import Base

# Re-export enums for compatibility
__all__ = [
    'WorkflowStatus', 'ExecutionStatus', 'NodeType',
    'TemplateCategory', 'SecurityEventType', 'ComplianceFramework',
    'StudioWorkflow', 'WorkflowExecution', 'WorkflowTemplate',
    'SecurityEvent', 'AuditLog', 'ComplianceAssessment',
    'NodeSchema', 'NodeDefinitionAPI', 'ConnectionDefinitionAPI',
    'AIGenerationRequest'
]


class StudioWorkflow(BaseWorkflowModel):
    """Studio-specific workflow model extending middleware base."""
    __tablename__ = "studio_workflows"
    
    # Studio-specific relationships (base provides all core fields)
    executions = relationship("WorkflowExecution", back_populates="workflow", cascade="all, delete-orphan")
    security_events = relationship("SecurityEvent", back_populates="workflow", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="workflow", cascade="all, delete-orphan")
    
    # Additional Studio-specific validations if needed
    @validates('nodes')
    def validate_nodes(self, key, nodes):
        """Additional Studio-specific node validation."""
        # Call parent validation first
        if not isinstance(nodes, list):
            raise ValueError("Nodes must be a list")
        
        # Studio-specific validation
        for node in nodes:
            if not isinstance(node, dict):
                raise ValueError("Each node must be a dictionary")
            required_fields = ['node_id', 'node_type', 'name']
            for field in required_fields:
                if field not in node:
                    raise ValueError(f"Node missing required field: {field}")
        
        return nodes
    
    def add_node(self, node_type: str, name: str, config: Dict[str, Any] = None, 
                 position: Dict[str, float] = None) -> str:
        """Add a node to the workflow and return its ID."""
        node_id = f"node_{len(self.nodes or []) + 1}_{uuid.uuid4().hex[:8]}"
        node = {
            "node_id": node_id,
            "node_type": node_type,
            "name": name,
            "config": config or {},
            "position": position or {"x": 0, "y": 0},
            "metadata": {}
        }
        
        if self.nodes is None:
            self.nodes = []
        self.nodes = self.nodes + [node]  # Create new list for SQLAlchemy tracking
        self.updated_at = datetime.now(timezone.utc)
        return node_id
    
    def add_connection(self, from_node: str, from_output: str, 
                      to_node: str, to_input: str) -> str:
        """Add a connection between nodes and return its ID."""
        connection_id = f"conn_{len(self.connections or []) + 1}_{uuid.uuid4().hex[:8]}"
        connection = {
            "connection_id": connection_id,
            "from_node": from_node,
            "from_output": from_output,
            "to_node": to_node,
            "to_input": to_input,
            "metadata": {}
        }
        
        if self.connections is None:
            self.connections = []
        self.connections = self.connections + [connection]  # Create new list for SQLAlchemy tracking
        self.updated_at = datetime.now(timezone.utc)
        return connection_id


class WorkflowExecution(BaseExecutionModel):
    """Studio-specific execution model extending middleware base."""
    __tablename__ = "studio_executions"
    
    # Studio-specific foreign key
    workflow_id = Column(String(255), ForeignKey("studio_workflows.workflow_id"), nullable=False)
    
    # Studio-specific relationships
    workflow = relationship("StudioWorkflow", back_populates="executions")
    security_events = relationship("SecurityEvent", back_populates="execution", cascade="all, delete-orphan")
    
    def add_log(self, message: str, level: str = "info", node_id: str = None):
        """Add a structured log message."""
        timestamp = datetime.now(timezone.utc).isoformat()
        log_entry = {
            "timestamp": timestamp,
            "level": level,
            "message": message,
            "node_id": node_id
        }
        
        if self.logs is None:
            self.logs = []
        self.logs = self.logs + [log_entry]  # Create new list for SQLAlchemy tracking


class WorkflowTemplate(BaseTemplateModel):
    """Studio-specific template model extending middleware base."""
    __tablename__ = "studio_templates"
    
    # All fields inherited from BaseTemplateModel


class SecurityEvent(BaseSecurityEventModel):
    """Studio-specific security event model."""
    __tablename__ = "studio_security_events"
    
    # Studio-specific foreign keys
    workflow_id = Column(String(255), ForeignKey("studio_workflows.workflow_id"), index=True)
    execution_id = Column(String(255), ForeignKey("studio_executions.execution_id"), index=True)
    
    # Studio-specific relationships
    workflow = relationship("StudioWorkflow", back_populates="security_events")
    execution = relationship("WorkflowExecution", back_populates="security_events")


class AuditLog(BaseAuditLogModel):
    """Studio-specific audit log model."""
    __tablename__ = "studio_audit_logs"
    
    # Studio-specific foreign key
    workflow_id = Column(String(255), ForeignKey("studio_workflows.workflow_id"), index=True)
    
    # Studio-specific relationship
    workflow = relationship("StudioWorkflow", back_populates="audit_logs")


class ComplianceAssessment(BaseComplianceModel):
    """Studio-specific compliance assessment model."""
    __tablename__ = "studio_compliance_assessments"
    
    # All fields inherited from BaseComplianceModel


# Studio-specific event listeners (if needed)
# Base models already have common event listeners


# Pydantic models for API validation (optional, for FastAPI integration)
try:
    from pydantic import BaseModel
    from typing import Optional
    
    class NodeDefinitionAPI(BaseModel):
        """API model for node definition."""
        node_id: str
        node_type: str
        name: str
        config: Dict[str, Any] = {}
        position: Dict[str, float] = {"x": 0, "y": 0}
        metadata: Dict[str, Any] = {}
    
    class ConnectionDefinitionAPI(BaseModel):
        """API model for connection definition."""
        connection_id: Optional[str] = None
        from_node: str
        from_output: str
        to_node: str
        to_input: str
        metadata: Dict[str, Any] = {}
    
    class WorkflowCreateAPI(BaseModel):
        """API model for workflow creation."""
        name: str
        description: str = ""
        nodes: List[NodeDefinitionAPI] = []
        connections: List[ConnectionDefinitionAPI] = []
        metadata: Dict[str, Any] = {}
        security_classification: str = "internal"
        compliance_requirements: List[str] = []
    
    class WorkflowUpdateAPI(BaseModel):
        """API model for workflow updates."""
        name: Optional[str] = None
        description: Optional[str] = None
        nodes: Optional[List[NodeDefinitionAPI]] = None
        connections: Optional[List[ConnectionDefinitionAPI]] = None
        metadata: Optional[Dict[str, Any]] = None
        security_classification: Optional[str] = None
        compliance_requirements: Optional[List[str]] = None
    
    class ExecutionCreateAPI(BaseModel):
        """API model for execution creation."""
        inputs: Dict[str, Any] = {}
        execution_context: Dict[str, Any] = {}
    
    class TemplateCreateAPI(BaseModel):
        """API model for template creation."""
        name: str
        description: str = ""
        category: str
        workflow_definition: Dict[str, Any]
        tags: List[str] = []
        industry: Optional[str] = None
        difficulty_level: str = "intermediate"
        documentation: Optional[str] = None
        compliance_frameworks: List[str] = []
        security_requirements: Dict[str, Any] = {}
        is_public: bool = False

except ImportError:
    # Pydantic not available, skip API models
    pass


# Additional data classes for API responses (non-SQLAlchemy)
from dataclasses import dataclass


@dataclass
class NodeSchema:
    """Schema definition for a node type."""
    node_type: str
    category: NodeType
    display_name: str
    description: str
    parameters: Dict[str, Any]
    input_schema: Dict[str, Any] = None
    output_schema: Dict[str, Any] = None
    examples: List[Dict[str, Any]] = None
    documentation_url: Optional[str] = None
    
    def __post_init__(self):
        if self.input_schema is None:
            self.input_schema = {}
        if self.output_schema is None:
            self.output_schema = {}
        if self.examples is None:
            self.examples = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "node_type": self.node_type,
            "category": self.category.value,
            "display_name": self.display_name,
            "description": self.description,
            "parameters": self.parameters,
            "input_schema": self.input_schema,
            "output_schema": self.output_schema,
            "examples": self.examples,
            "documentation_url": self.documentation_url
        }


@dataclass
class AIGenerationRequest:
    """Request for AI-powered workflow generation."""
    prompt: str
    context: Dict[str, Any] = None
    constraints: Dict[str, Any] = None
    preferred_nodes: List[str] = None
    tenant_id: str = "default"
    
    def __post_init__(self):
        if self.context is None:
            self.context = {}
        if self.constraints is None:
            self.constraints = {}
        if self.preferred_nodes is None:
            self.preferred_nodes = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "prompt": self.prompt,
            "context": self.context,
            "constraints": self.constraints,
            "preferred_nodes": self.preferred_nodes,
            "tenant_id": self.tenant_id
        }