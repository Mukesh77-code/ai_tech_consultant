"""
Pydantic Schemas for Task 3 Meeting to Scope of Work.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class RequirementItem(BaseModel):
    req_id: str = Field(..., description="Unique ID, e.g. REQ-001")
    description: str
    source_passage: str
    speaker: str
    priority: str = Field(default="Must-Have")  # Must-Have, Should-Have, Nice-to-Have
    status: str = Field(default="Confirmed")    # Confirmed, Unclear, Disputed
    is_inferred: bool = False
    acceptance_criteria: Optional[str] = None
    dependencies: List[str] = []


class FeasibilityResult(BaseModel):
    req_id: str
    classification: str  # "existing_configuration", "existing_feature_with_limitation", "potential_custom_development", "needs_clarification"
    justification: str
    documented_settings_path: Optional[str] = None
    supporting_kb_sources: List[dict] = []
    recommended_approach: str


class TaskEstimate(BaseModel):
    task_id: str
    deliverable: str
    task_name: str
    low_hours: float
    likely_hours: float
    high_hours: float
    reasoning: str
    uncertainty_level: str  # "LOW", "MEDIUM", "HIGH"
    assumptions: List[str] = []


class ScopeOfWork(BaseModel):
    project_title: str
    client_name: str
    project_objective: str
    current_problem: str
    agreed_requirements: List[RequirementItem]
    proposed_solution: str
    deliverables: List[str]
    explicit_exclusions: List[str]
    assumptions_and_dependencies: List[str]
    acceptance_criteria: List[str]
    client_responsibilities: List[str]
    open_questions_and_risks: List[str]


class Proposal(BaseModel):
    project_title: str
    client_name: str
    executive_summary: str
    scope_summary: str
    deliverables: List[str]
    timeline_weeks: float
    milestones: List[dict]
    task_estimates: List[TaskEstimate]
    total_low_hours: float
    total_likely_hours: float
    total_high_hours: float
    hourly_rate: float
    currency: str
    total_estimated_cost: float
    pricing_assumptions: str
    client_responsibilities: List[str]
    exclusions: List[str]
    risks_and_mitigations: List[dict]
    approval_and_next_steps: str


class ScopeChangeItem(BaseModel):
    change_type: str  # "ADDED", "MODIFIED", "REMOVED"
    req_id: str
    description: str
    original_state: Optional[str] = None
    new_state: Optional[str] = None
    impact_analysis: str
    is_out_of_scope: bool = False
    estimated_hour_delta: float = 0.0


class ScopeChangeReport(BaseModel):
    original_meeting_id: str
    followup_meeting_id: str
    summary_of_changes: str
    added_requirements: List[ScopeChangeItem]
    modified_requirements: List[ScopeChangeItem]
    removed_requirements: List[ScopeChangeItem]
    out_of_scope_warnings: List[str]
    net_hour_delta_likely: float
    revised_total_hours: float
    commercial_recommendation: str
