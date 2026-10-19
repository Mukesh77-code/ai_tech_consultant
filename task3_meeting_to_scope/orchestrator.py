"""
Multi-Agent Orchestrator for Task 3: Meeting to Scope of Work.
Coordinates Transcript Analyst, Feasibility Agent, Scope Agent,
Estimation Agent, Proposal Agent, and Comparison Agent.
"""

import json
import logging
import os
import sys
from typing import Dict, Optional

from .agents.transcript_analyst import TranscriptAnalyst
from .agents.feasibility_agent import ProductFeasibilityAgent
from .agents.scope_agent import ScopeAgent
from .agents.estimation_agent import EstimationAgent
from .agents.proposal_agent import ProposalAgent
from .agents.comparison_agent import ScopeComparisonAgent
from .models.schemas import ScopeOfWork, Proposal, ScopeChangeReport

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


class MeetingToScopeOrchestrator:
    def __init__(self, kb_api_url: str = "http://127.0.0.1:8000", hourly_rate: float = 120.0):
        self.analyst = TranscriptAnalyst()
        self.feasibility = ProductFeasibilityAgent(kb_api_url=kb_api_url)
        self.scope_agent = ScopeAgent()
        self.estimation = EstimationAgent()
        self.proposal_agent = ProposalAgent(default_hourly_rate=hourly_rate)
        self.comparison_agent = ScopeComparisonAgent()
        self.hourly_rate = hourly_rate

    def process_transcript(
        self,
        transcript_text: str,
        project_id: str = "PROJ-A",
        timeline_weeks: float = 6.0
    ) -> Dict:
        """
        Runs full pipeline: Transcript -> Feasibility -> Scope -> Estimates -> Proposal.
        """
        logger.info(f"Step 1: Analyzing meeting transcript for {project_id}...")
        analysis = self.analyst.analyze_transcript(transcript_text, project_id=project_id)

        logger.info("Step 2: Checking feature feasibility against Task 1 Knowledge Brain API...")
        feasibility_results = self.feasibility.assess_requirements(analysis["requirements"])

        logger.info("Step 3: Generating Scope of Work...")
        scope = self.scope_agent.generate_scope(analysis, feasibility_results)

        logger.info("Step 4: Estimating development hours (3-point estimates)...")
        estimates = self.estimation.estimate_tasks(analysis["requirements"], feasibility_results)

        logger.info("Step 5: Compiling client-ready proposal...")
        proposal = self.proposal_agent.generate_proposal(
            scope=scope,
            task_estimates=estimates,
            hourly_rate=self.hourly_rate,
            timeline_weeks=timeline_weeks
        )

        serialized_analysis = {
            **analysis,
            "requirements": [r.model_dump() for r in analysis["requirements"]]
        }

        return {
            "project_id": project_id,
            "analysis": serialized_analysis,
            "feasibility_results": [f.model_dump() for f in feasibility_results],
            "scope_of_work": scope.model_dump(),
            "task_estimates": [e.model_dump() for e in estimates],
            "proposal": proposal.model_dump()
        }

    def compare_followup_meeting(
        self,
        original_scope: ScopeOfWork,
        followup_transcript_text: str,
        project_id: str = "PROJ-C-FOLLOWUP"
    ) -> Dict:
        """
        Compares follow-up meeting (Meeting C) against baseline scope (Meeting A).
        """
        logger.info("Analyzing follow-up meeting transcript...")
        followup_analysis = self.analyst.analyze_transcript(followup_transcript_text, project_id=project_id)

        logger.info("Checking feasibility of new/modified requirements...")
        feasibility_results = self.feasibility.assess_requirements(followup_analysis["requirements"])

        logger.info("Running scope comparison and delta detection...")
        change_report = self.comparison_agent.compare_scopes(
            original_scope=original_scope,
            followup_requirements=followup_analysis["requirements"],
            original_meeting_id="Meeting A (Oct 14)",
            followup_meeting_id="Meeting C (Oct 18)"
        )

        # Generate revised scope
        revised_scope = self.scope_agent.generate_scope(followup_analysis, feasibility_results)
        revised_estimates = self.estimation.estimate_tasks(followup_analysis["requirements"], feasibility_results)
        revised_proposal = self.proposal_agent.generate_proposal(
            scope=revised_scope,
            task_estimates=revised_estimates,
            hourly_rate=self.hourly_rate,
            timeline_weeks=4.0  # compressed timeline
        )

        return {
            "change_report": change_report.model_dump(),
            "revised_scope": revised_scope.model_dump(),
            "revised_proposal": revised_proposal.model_dump()
        }
