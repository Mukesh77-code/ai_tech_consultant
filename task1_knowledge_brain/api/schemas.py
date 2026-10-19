"""
Pydantic Schemas for Knowledge Brain API.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str = Field(..., description="Customer question about features, billing, or settings")
    top_k: int = Field(default=4, ge=1, le=10, description="Number of evidence chunks to retrieve")
    auto_escalate: bool = Field(default=False, description="Whether to automatically create an escalation if evidence is insufficient")


class SourceItem(BaseModel):
    title: str
    url: str
    section: Optional[str] = ""
    excerpt: Optional[str] = ""
    image_url: Optional[str] = None


class QueryResponse(BaseModel):
    question: str
    answer: str
    confidence: float
    status: str  # "grounded", "insufficient_evidence", "escalated"
    requires_human: bool
    escalation_id: Optional[str] = None
    sources: List[SourceItem] = []


class IngestionRequest(BaseModel):
    max_pages: int = Field(default=25, ge=1, le=200, description="Max pages to crawl in this batch")
    force_all: bool = Field(default=False, description="Force re-indexing all pages regardless of hash")


class IngestionResponse(BaseModel):
    crawler_running: bool
    current_job: dict
    manifest_summary: dict


class EscalationCreateRequest(BaseModel):
    question: str
    reason: str
    evidence_snippets: Optional[List[str]] = []


class EscalationResolveRequest(BaseModel):
    expert_answer: str
    expert_notes: Optional[str] = None
    approved_by: Optional[str] = "Senior Support Engineer"


class EscalationItem(BaseModel):
    id: str
    question: str
    reason: str
    evidence_snippets: List[str]
    status: str
    expert_answer: Optional[str] = None
    created_at: str
    resolved_at: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    indexed_chunks: int
    tracked_pages: int
    pending_escalations: int
