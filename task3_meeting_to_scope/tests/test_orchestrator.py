"""
Unit tests for Task 3 Meeting to Scope of Work.
"""

import os
import pytest
from task3_meeting_to_scope.orchestrator import MeetingToScopeOrchestrator
from task3_meeting_to_scope.models.schemas import RequirementItem, ScopeOfWork
from task3_meeting_to_scope.agents.comparison_agent import ScopeComparisonAgent


def test_transcript_analyst():
    orchestrator = MeetingToScopeOrchestrator()
    sample = """
    Alex Rivers [00:00]: We need Google Maps search radius by zip code (5, 10, 25 miles).
    Alex Rivers [01:00]: We want member phone numbers hidden from anonymous visitors.
    """
    analysis = orchestrator.analyst.analyze_transcript(sample, project_id="Meeting-A")
    assert len(analysis["requirements"]) >= 2
    assert any("radius" in r.description.lower() for r in analysis["requirements"])


def test_feasibility_check():
    orchestrator = MeetingToScopeOrchestrator()
    req = RequirementItem(
        req_id="REQ-001",
        description="Distance and radius-based filtering by zip code and Google Maps",
        source_passage="We need distance search",
        speaker="Alex Rivers"
    )
    feas = orchestrator.feasibility.assess_single_requirement(req)
    assert feas.classification == "existing_configuration"
    assert "Integrations" in (feas.documented_settings_path or "")


def test_custom_dev_feasibility():
    orchestrator = MeetingToScopeOrchestrator()
    req = RequirementItem(
        req_id="REQ-007",
        description="AI-powered natural language conversational search query parser",
        source_passage="Type natural language query",
        speaker="Alex Rivers"
    )
    feas = orchestrator.feasibility.assess_single_requirement(req)
    assert feas.classification == "potential_custom_development"


def test_scope_comparison():
    agent = ScopeComparisonAgent()
    orig_req1 = RequirementItem(req_id="REQ-001", description="Search radius", source_passage="", speaker="A")
    orig_req2 = RequirementItem(req_id="REQ-005", description="HubSpot webhooks", source_passage="", speaker="A")

    scope = ScopeOfWork(
        project_title="Test",
        client_name="Test Client",
        project_objective="Test Obj",
        current_problem="Test Prob",
        agreed_requirements=[orig_req1, orig_req2],
        proposed_solution="Test Sol",
        deliverables=["REQ-001: Search", "REQ-005: HubSpot"],
        explicit_exclusions=[],
        assumptions_and_dependencies=[],
        acceptance_criteria=[],
        client_responsibilities=[],
        open_questions_and_risks=[]
    )

    followup_req1 = RequirementItem(req_id="REQ-001", description="Search radius", source_passage="", speaker="A")
    followup_req3 = RequirementItem(req_id="REQ-007", description="AI-powered conversational search", source_passage="", speaker="A")

    report = agent.compare_scopes(scope, [followup_req1, followup_req3])

    assert len(report.removed_requirements) == 1
    assert report.removed_requirements[0].req_id == "REQ-005"
    assert len(report.added_requirements) == 1
    assert report.added_requirements[0].req_id == "REQ-007"
    assert any("OUT-OF-SCOPE WARNING" in w for w in report.out_of_scope_warnings)
