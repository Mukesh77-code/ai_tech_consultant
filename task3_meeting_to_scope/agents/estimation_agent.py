"""
Estimation Agent for Task 3.
Breaks down deliverables into engineering subtasks with 3-point estimates
(Low, Likely, High hours), uncertainty classifications, and technical reasoning.
"""

from typing import Dict, List
from ..models.schemas import RequirementItem, FeasibilityResult, TaskEstimate


class EstimationAgent:
    def estimate_tasks(
        self,
        requirements: List[RequirementItem],
        feasibility_results: List[FeasibilityResult]
    ) -> List[TaskEstimate]:
        tasks: List[TaskEstimate] = []
        feasibility_map = {f.req_id: f for f in feasibility_results}
        task_counter = 0

        for req in requirements:
            feas = feasibility_map.get(req.req_id)
            is_custom = feas and feas.classification == "potential_custom_development"
            is_config = feas and feas.classification == "existing_configuration"

            # 1. Technical investigation & configuration
            task_counter += 1
            if is_config:
                tasks.append(TaskEstimate(
                    task_id=f"TASK-{task_counter:03d}",
                    deliverable=req.req_id,
                    task_name=f"{req.req_id} - Platform Administrative Configuration",
                    low_hours=2.0,
                    likely_hours=3.5,
                    high_hours=5.0,
                    reasoning=f"Configure native settings in {feas.documented_settings_path or 'Admin Panel'}. Verify API keys.",
                    uncertainty_level="LOW",
                    assumptions=["Client provides valid administrative credentials."]
                ))
            else:
                # Custom development requires architecture spike
                tasks.append(TaskEstimate(
                    task_id=f"TASK-{task_counter:03d}",
                    deliverable=req.req_id,
                    task_name=f"{req.req_id} - Architecture Design & API Specification",
                    low_hours=4.0,
                    likely_hours=6.0,
                    high_hours=10.0,
                    reasoning="Design custom data models, API interface contract, and error boundary protocols.",
                    uncertainty_level="HIGH" if is_custom else "MEDIUM",
                    assumptions=["Platform webhooks and custom widgets support external script injection."]
                ))

            # 2. Implementation task
            task_counter += 1
            if is_config:
                tasks.append(TaskEstimate(
                    task_id=f"TASK-{task_counter:03d}",
                    deliverable=req.req_id,
                    task_name=f"{req.req_id} - Frontend Layout & Template Customization",
                    low_hours=3.0,
                    likely_hours=5.0,
                    high_hours=8.0,
                    reasoning="Adjust CSS styling, responsive layout breakpoints, and shortcode placement.",
                    uncertainty_level="LOW",
                    assumptions=["Standard Bootstrap responsive grid applies."]
                ))
            else:
                # Custom engineering backend + frontend
                tasks.append(TaskEstimate(
                    task_id=f"TASK-{task_counter:03d}",
                    deliverable=req.req_id,
                    task_name=f"{req.req_id} - Custom Engineering Implementation",
                    low_hours=12.0,
                    likely_hours=18.0,
                    high_hours=28.0,
                    reasoning="Develop custom microservice / JavaScript module, database integration, and edge cases.",
                    uncertainty_level="HIGH",
                    assumptions=["Third party LLM or Maps APIs maintain 99.9% uptime."]
                ))

            # 3. QA and Acceptance Testing
            task_counter += 1
            tasks.append(TaskEstimate(
                task_id=f"TASK-{task_counter:03d}",
                deliverable=req.req_id,
                task_name=f"{req.req_id} - End-to-End QA & Staging Acceptance Testing",
                low_hours=1.5,
                likely_hours=2.5,
                high_hours=4.0,
                reasoning="Verify against defined acceptance criteria across Chrome, Safari, iOS, and Android mobile browsers.",
                uncertainty_level="LOW",
                assumptions=["Staging environment mirrors production database schema."]
            ))

        return tasks
