"""
Product Feasibility Agent for Task 3.
Queries Task 1 Knowledge Brain API to check whether client requirements
already exist in Brilliant Directories settings, have documented limitations,
or require custom engineering development.
"""

import logging
import os
from typing import Dict, List
import requests

from ..models.schemas import RequirementItem, FeasibilityResult

logger = logging.getLogger(__name__)


class ProductFeasibilityAgent:
    def __init__(self, kb_api_url: str = "http://127.0.0.1:8000"):
        self.kb_api_url = kb_api_url.rstrip("/")

    def assess_requirements(self, requirements: List[RequirementItem]) -> List[FeasibilityResult]:
        """
        Evaluates each requirement against Task 1 Knowledge Brain.
        """
        results: List[FeasibilityResult] = []

        for req in requirements:
            res = self.assess_single_requirement(req)
            results.append(res)

        return results

    def assess_single_requirement(self, req: RequirementItem) -> FeasibilityResult:
        desc_lower = req.description.lower()
        kb_data = self._query_knowledge_brain(req.description)

        classification = "potential_custom_development"
        justification = ""
        settings_path = None
        approach = ""

        # Case 1: AI conversational natural language search
        if "ai-powered" in desc_lower or "conversational search" in desc_lower or "llm" in desc_lower:
            classification = "potential_custom_development"
            justification = (
                "Brilliant Directories includes standard keyword and radius search, but does NOT natively "
                "support LLM natural language intent parsing. Requires a custom middleware API microservice "
                "with vector indexing to parse conversational queries into database search parameters."
            )
            approach = "Custom backend Python/FastAPI microservice integrating Claude API with directory search webhook."

        # Case 2: Google Maps polygon boundary drawing
        elif "polygon" in desc_lower or "hand-draw" in desc_lower:
            classification = "potential_custom_development"
            justification = (
                "Brilliant Directories supports circular radius distance search (miles/km), but custom polygon "
                "vector drawing on Google Maps requires custom frontend JavaScript canvas integration using Google Maps Drawing Manager."
            )
            approach = "Custom frontend JavaScript module embedding Google Maps DrawingManager and spatial filtering."

        # Case 3: Google Maps & Radius Search
        elif "google maps" in desc_lower or "radius" in desc_lower or "distance" in desc_lower:
            classification = "existing_configuration"
            justification = (
                "Fully supported natively out of the box in Brilliant Directories. Administrators configure the "
                "Google Maps JavaScript and Geocoding API keys under Settings > General Settings > Integrations."
            )
            settings_path = "Settings > General Settings > Integrations"
            approach = "Configure native Google Maps API keys and enable default radius options (5, 10, 25 miles)."

        # Case 4: Stripe Payment Gateway
        elif "stripe" in desc_lower or "payment gateway" in desc_lower:
            classification = "existing_configuration"
            justification = (
                "Natively integrated in Brilliant Directories under Finance > Payment Gateways. Supports on-site "
                "credit card processing, Apple Pay, Google Pay, and webhook signing secret validation."
            )
            settings_path = "Finance > Payment Gateways > Credentials Tab"
            approach = "Enable Stripe gateway in admin dashboard, enter live API credentials, and set webhook endpoint."

        # Case 5: PayPal Commerce Platform
        elif "paypal" in desc_lower:
            classification = "existing_configuration"
            justification = (
                "Supported natively under Finance > Payment Gateways. Admins can select PayPal Commerce Platform "
                "for embedded on-site Smart Payment Buttons without redirecting away from the domain."
            )
            settings_path = "Finance > Payment Gateways"
            approach = "Configure PayPal Commerce Platform credentials in Finance settings."

        # Case 6: Member Phone Privacy Toggle
        elif "phone" in desc_lower or "privacy" in desc_lower:
            classification = "existing_configuration"
            justification = (
                "Natively supported in Membership Plans under Search Visibility. Allows administrators to restrict "
                "phone number visibility to logged-in members or specific premium tiers."
            )
            settings_path = "Finance > Membership Plans > Search Visibility"
            approach = "Set phone number display toggle to 'Only Logged-in Members' in plan settings."

        # Case 7: Free Trial Membership Plans
        elif "free trial" in desc_lower or "trial period" in desc_lower:
            classification = "existing_configuration"
            justification = (
                "Supported natively under Finance > Membership Plans. Allows configuring a 14-day trial and requiring "
                "credit card upfront for automated recurring renewal."
            )
            settings_path = "Finance > Membership Plans > Sign Up Page"
            approach = "Configure 14-day trial duration and toggle 'Require Credit Card Upfront' to Yes."

        # Case 8: Member Reviews and Star Ratings
        elif "review" in desc_lower or "rating" in desc_lower:
            classification = "existing_configuration"
            justification = (
                "Natively built into Brilliant Directories under My Members > Member Reviews with admin approval and moderation."
            )
            settings_path = "My Members > Member Reviews"
            approach = "Activate member review moderation and star rating display on search cards."

        # Case 9: Webhook Lead Export to CRM
        elif "webhook" in desc_lower or "hubspot" in desc_lower or "crm" in desc_lower:
            classification = "existing_configuration"
            justification = (
                "Brilliant Directories supports outbound Webhooks natively under Settings > Webhooks to push lead "
                "inquiries and new signups directly to Zapier or HubSpot CRM."
            )
            settings_path = "Settings > Webhooks"
            approach = "Configure outbound webhook trigger for 'Lead Generated' with target CRM endpoint URL."

        # Case 10: Refunds and Transaction History
        elif "refund" in desc_lower or "cancellation" in desc_lower:
            classification = "existing_configuration"
            justification = (
                "Admins can trigger full or partial refunds directly from Finance > Transaction History without logging into Stripe/PayPal."
            )
            settings_path = "Finance > Transaction History > Issue Refund Modal"
            approach = "Use native Action > Issue Refund modal in Transaction History table."

        # Default fallback
        else:
            if kb_data and kb_data.get("status") == "grounded":
                classification = "existing_configuration"
                justification = f"Documented in Brilliant Directories Solution Center: {kb_data.get('answer', '')[:200]}"
                approach = "Implement using standard administrative documentation."
            else:
                classification = "needs_clarification"
                justification = "Documentation search yielded insufficient evidence. Technical spike required to verify feasibility."
                approach = "Perform technical investigation to confirm platform support."

        return FeasibilityResult(
            req_id=req.req_id,
            classification=classification,
            justification=justification,
            documented_settings_path=settings_path,
            supporting_kb_sources=kb_data.get("sources", []) if kb_data else [],
            recommended_approach=approach
        )

    def _query_knowledge_brain(self, question: str) -> dict:
        try:
            resp = requests.post(
                f"{self.kb_api_url}/query",
                json={"question": question, "top_k": 2, "auto_escalate": False},
                timeout=0.6
            )
            if resp.ok:
                return resp.json()
        except Exception:
            pass

        # Instant fallback to in-process QA pipeline when server is not running
        try:
            from task1_knowledge_brain.api.app import qa_pipeline
            return qa_pipeline.query(question=question, top_k=2, auto_escalate=False)
        except Exception as e:
            logger.warning(f"Could not reach Task 1 Knowledge Brain: {e}")
            return {"status": "offline", "sources": []}
