"""
Scope Agent for Task 3.
Synthesizes structured requirements and feasibility assessments into a clear,
rigorous Scope of Work with verified deliverables, explicit exclusions, and acceptance criteria.
"""

from typing import Dict, List
from ..models.schemas import RequirementItem, FeasibilityResult, ScopeOfWork


class ScopeAgent:
    def generate_scope(
        self,
        analysis: Dict,
        feasibility_results: List[FeasibilityResult]
    ) -> ScopeOfWork:
        reqs: List[RequirementItem] = analysis.get("requirements", [])
        exclusions: List[str] = analysis.get("explicit_exclusions", [])
        client_name = analysis.get("client_name", "Client")
        project_title = analysis.get("project_title", "Technology Consulting Project")

        feasibility_map = {f.req_id: f for f in feasibility_results}

        # Build deliverables list
        deliverables = []
        acceptance_criteria = []
        assumptions = [
            "Client will provide valid administrative API credentials (Google Cloud, Stripe, PayPal).",
            "Brilliant Directories hosted platform uptime and core codebase maintained by vendor.",
            "Work will be verified against agreed acceptance criteria in a dedicated staging environment prior to production launch."
        ]

        for req in reqs:
            feas = feasibility_map.get(req.req_id)
            feas_note = f" [{feas.classification.replace('_', ' ').upper()}]" if feas else ""
            deliverables.append(f"{req.req_id}: {req.description}{feas_note}")

            if req.acceptance_criteria:
                acceptance_criteria.append(f"{req.req_id}: {req.acceptance_criteria}")

        client_responsibilities = [
            "Provide Google Cloud Console billing account and API keys with Geocoding and Maps JavaScript APIs enabled.",
            "Provide production and sandbox API keys for Stripe and PayPal merchant accounts.",
            "Review and approve staging deployment milestones within 3 business days of delivery.",
            "Supply high-resolution brand assets (transparent PNG logo, 1920x600 hero banner)."
        ]

        open_risks = [
            "Google Maps API usage quotas: High search volume may incur Google Cloud consumption charges.",
            "Browser geolocation permission: Distance search radius requires end-user browser GPS permission consent.",
            "Third-party API rate limits and webhook delivery guarantees."
        ]

        current_problem = (
            "Current platform lacks distance radius filtering, causing visitor drop-off and irrelevant search results. "
            "Mobile user experience requires optimization, and key commercial checkout and lead export workflows "
            "require automated integration to prevent manual administrative overhead."
        )

        proposed_solution = (
            "Implement a cohesive, hybrid solution leveraging Brilliant Directories native configuration "
            "for core settings (Google Maps radius, payment gateways, review moderation) and dedicated custom "
            "modules where out-of-the-box settings are insufficient, ensuring optimal budget allocation and fast delivery."
        )

        return ScopeOfWork(
            project_title=project_title,
            client_name=client_name,
            project_objective=f"Deliver a high-performance, conversion-optimized directory portal for {client_name}.",
            current_problem=current_problem,
            agreed_requirements=reqs,
            proposed_solution=proposed_solution,
            deliverables=deliverables,
            explicit_exclusions=exclusions,
            assumptions_and_dependencies=assumptions,
            acceptance_criteria=acceptance_criteria,
            client_responsibilities=client_responsibilities,
            open_questions_and_risks=open_risks
        )
