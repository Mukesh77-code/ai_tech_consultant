"""
Proposal and Review Agent for Task 3.
Synthesizes Scope of Work and task estimates into an executive-ready,
commercially transparent client proposal with configurable hourly rates and milestone schedules.
"""

from typing import Dict, List
from ..models.schemas import ScopeOfWork, TaskEstimate, Proposal


class ProposalAgent:
    def __init__(self, default_hourly_rate: float = 120.0, default_currency: str = "USD"):
        self.default_hourly_rate = default_hourly_rate
        self.default_currency = default_currency

    def generate_proposal(
        self,
        scope: ScopeOfWork,
        task_estimates: List[TaskEstimate],
        hourly_rate: float = 120.0,
        timeline_weeks: float = 6.0
    ) -> Proposal:
        rate = hourly_rate or self.default_hourly_rate

        total_low = sum(t.low_hours for t in task_estimates)
        total_likely = sum(t.likely_hours for t in task_estimates)
        total_high = sum(t.high_hours for t in task_estimates)

        total_cost = round(total_likely * rate, 2)

        milestones = [
            {
                "milestone": "Milestone 1: Architectural Foundation & Configuration",
                "weeks": "Week 1 - 2",
                "deliverables": "Admin settings, API key integrations (Google Maps, Stripe/PayPal), initial staging environment.",
                "percentage_payment": "30%"
            },
            {
                "milestone": "Milestone 2: Feature Implementation & Template Customization",
                "weeks": f"Week 3 - {max(3, int(timeline_weeks - 1))}",
                "deliverables": "Search radius filters, interactive map display, responsive mobile layout, custom workflows.",
                "percentage_payment": "40%"
            },
            {
                "milestone": "Milestone 3: Quality Assurance, UAT & Production Launch",
                "weeks": f"Week {int(timeline_weeks)}",
                "deliverables": "Cross-device browser verification, client user acceptance sign-off, DNS live deployment.",
                "percentage_payment": "30%"
            }
        ]

        risks = [
            {
                "risk": "Third-party API credentials delay",
                "impact": "Schedule slippage",
                "mitigation": "Client provides verified API keys during Sprint 0 kick-off."
            },
            {
                "risk": "Scope expansion during staging review",
                "impact": "Budget and timeline variance",
                "mitigation": "Formal change control process with incremental scope estimation."
            }
        ]

        exec_summary = (
            f"AI Tech Consulting is pleased to present this technical scope and proposal for {scope.client_name}. "
            f"This engagement targets delivering an optimized, modern web solution addressing current user friction, "
            f"integrating verified platform capabilities, and delivering measurable performance improvements within an estimated "
            f"{timeline_weeks}-week delivery window."
        )

        pricing_assumptions = (
            f"Estimates are calculated at a professional services consulting rate of {rate} {self.default_currency}/hour. "
            f"Total likely investment is {total_cost} {self.default_currency} based on {total_likely} likely engineering hours "
            f"(Range: {total_low}h low to {total_high}h high). Invoices are billed per milestone completion upon written client acceptance."
        )

        approval_steps = (
            "To proceed with project kick-off:\n"
            "1. Review and approve the attached Scope of Work and Deliverables.\n"
            "2. Sign the Master Services Agreement (MSA) and Statement of Work (SOW).\n"
            "3. Remit the 30% Milestone 1 initial deposit invoice.\n"
            "4. Complete the technical onboarding credential checklist."
        )

        return Proposal(
            project_title=scope.project_title,
            client_name=scope.client_name,
            executive_summary=exec_summary,
            scope_summary=scope.proposed_solution,
            deliverables=scope.deliverables,
            timeline_weeks=timeline_weeks,
            milestones=milestones,
            task_estimates=task_estimates,
            total_low_hours=round(total_low, 1),
            total_likely_hours=round(total_likely, 1),
            total_high_hours=round(total_high, 1),
            hourly_rate=rate,
            currency=self.default_currency,
            total_estimated_cost=total_cost,
            pricing_assumptions=pricing_assumptions,
            client_responsibilities=scope.client_responsibilities,
            exclusions=scope.explicit_exclusions,
            risks_and_mitigations=risks,
            approval_and_next_steps=approval_steps
        )
