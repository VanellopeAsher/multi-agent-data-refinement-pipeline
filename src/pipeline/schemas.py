"""
Graph schema + pipeline schema definitions.
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


# ==================== Graph Schema ====================

class PaperNode(BaseModel):
    """Paper node schema."""
    id: str
    title: str
    abstract: Optional[str] = None
    year: Optional[int] = None
    venue: Optional[str] = None
    doi: Optional[str] = None
    citation_count: int = 0
    local_pdf_path: Optional[str] = None


class AuthorNode(BaseModel):
    """Author node schema."""
    id: str
    name: str
    affiliation: Optional[str] = None


class ConceptNode(BaseModel):
    """Concept node schema."""
    id: str
    name: str
    level: int = 0
    field: Optional[str] = None


class ResourceNode(BaseModel):
    """Resource node schema."""
    id: str
    name: str
    resource_type: str  # 'dataset', 'model', 'tool', etc.
    url: Optional[str] = None


# ==================== Pipeline Schema ====================

class RefinementIssue(BaseModel):
    """Issue detected by DiagnoseAgent."""
    issue_type: str  # 'missing_field', 'inconsistent', 'duplicate', 'malformed', etc.
    entity_type: str  # 'Paper', 'Author', 'Concept', 'Resource', 'Edge'
    entity_id: str
    description: str
    severity: str = 'medium'  # 'low', 'medium', 'high'
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SearchResult(BaseModel):
    """Evidence retrieved by SearchAgent."""
    issue_id: str  # Reference to RefinementIssue
    source: str  # 'web', 'openalex', 'pdf'
    content: str
    confidence: float = 0.5
    metadata: Dict[str, Any] = Field(default_factory=dict)


class NormalizedUpdate(BaseModel):
    """Standardized update from NormalizationAgent."""
    issue_id: str
    entity_type: str
    entity_id: str
    normalized_value: Any
    original_value: Any
    confidence: float = 0.5
    metadata: Dict[str, Any] = Field(default_factory=dict)


class NodeUpdate(BaseModel):
    """Node update operation."""
    operation: str  # 'create', 'update', 'merge', 'delete'
    node_type: str  # 'Paper', 'Author', 'Concept', 'Resource'
    node_id: str
    fields: Dict[str, Any] = Field(default_factory=dict)
    merge_with: Optional[str] = None  # For merge operations


class EdgeUpdate(BaseModel):
    """Edge update operation."""
    operation: str  # 'create', 'update', 'delete'
    src_id: str
    rel_type: str  # 'CITES', 'WRITTEN_BY', 'CENTERS_ON', 'USES'
    dst_id: str
    properties: Dict[str, Any] = Field(default_factory=dict)


class GraphUpdate(BaseModel):
    """Complete graph update from CodingAgent."""
    node_updates: List[NodeUpdate] = Field(default_factory=list)
    edge_updates: List[EdgeUpdate] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ReviewedGraphUpdate(BaseModel):
    """Graph update after ReviewAgent validation."""
    node_updates: List[NodeUpdate] = Field(default_factory=list)
    edge_updates: List[EdgeUpdate] = Field(default_factory=list)
    rejected_updates: List[Dict[str, Any]] = Field(default_factory=list)
    pending_human: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

