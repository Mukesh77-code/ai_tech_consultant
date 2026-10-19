"""
Evaluation Suite for Task 3 Meeting to Scope of Work.
Tests:
1. End-to-end processing of Meeting A (Website Improvements)
2. End-to-end processing of Meeting B (E-commerce Workflow)
3. Feasibility classification accuracy against Task 1
4. 3-point estimation math integrity (low <= likely <= high)
5. Scope comparison and delta detection between Meeting A and Meeting C
6. Detection of Added, Modified, Removed requirements and Out-of-Scope warnings
"""

import json
import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from task3_meeting_to_scope.orchestrator import MeetingToScopeOrchestrator
from task3_meeting_to_scope.models.schemas import ScopeOfWork


def run_eval():
    print("================================================================================")
    print("RUNNING TASK 3 MEETING TO SCOPE COMPREHENSIVE EVALUATION SUITE")
    print("================================================================================\n")

    transcripts_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "transcripts"))
    outputs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "outputs"))
    os.makedirs(outputs_dir, exist_ok=True)

    orchestrator = MeetingToScopeOrchestrator(kb_api_url="http://127.0.0.1:8000", hourly_rate=120.0)

    pass_count = 0
    total_tests = 0

    # -------------------------------------------------------------------------
    # Test 1: Meeting A End-to-End Processing
    # -------------------------------------------------------------------------
    total_tests += 1
    with open(os.path.join(transcripts_dir, "meeting_a_website_improvements.txt"), "r", encoding="utf-8") as f:
        t_a = f.read()

    res_a = orchestrator.process_transcript(t_a, project_id="Meeting-A", timeline_weeks=7.0)

    scope_a = res_a["scope_of_work"]
    proposal_a = res_a["proposal"]
    reqs_a = scope_a["agreed_requirements"]

    test_1_pass = (
        len(reqs_a) >= 5 and
        proposal_a["total_likely_hours"] > 0 and
        len(scope_a["explicit_exclusions"]) > 0 and
        len(proposal_a["milestones"]) == 3
    )
    if test_1_pass:
        pass_count += 1
    print(
        f"{'[PASS]' if test_1_pass else '[FAIL]'} TC-01 Meeting A Orchestration: "
        f"{len(reqs_a)} Requirements Extracted, {proposal_a['total_likely_hours']}h Likely Effort, "
        f"${proposal_a['total_estimated_cost']} Total Cost"
    )

    # -------------------------------------------------------------------------
    # Test 2: Meeting B End-to-End Processing
    # -------------------------------------------------------------------------
    total_tests += 1
    with open(os.path.join(transcripts_dir, "meeting_b_ecommerce_workflow.txt"), "r", encoding="utf-8") as f:
        t_b = f.read()

    res_b = orchestrator.process_transcript(t_b, project_id="Meeting-B", timeline_weeks=5.0)
    proposal_b = res_b["proposal"]
    reqs_b = res_b["scope_of_work"]["agreed_requirements"]

    test_2_pass = (
        len(reqs_b) >= 4 and
        any("stripe" in r["description"].lower() for r in reqs_b) and
        proposal_b["timeline_weeks"] == 5.0
    )
    if test_2_pass:
        pass_count += 1
    print(
        f"{'[PASS]' if test_2_pass else '[FAIL]'} TC-02 Meeting B Orchestration: "
        f"{len(reqs_b)} Requirements Extracted (Stripe/PayPal), {proposal_b['total_likely_hours']}h Effort"
    )

    # -------------------------------------------------------------------------
    # Test 3: Feasibility Classification Accuracy (Configuration vs Custom Dev)
    # -------------------------------------------------------------------------
    total_tests += 1
    feas_a = res_a["feasibility_results"]
    maps_feas = next((f for f in feas_a if "REQ-001" in f["req_id"] or "REQ-002" in f["req_id"]), None)
    config_detected = maps_feas and maps_feas["classification"] == "existing_configuration"

    if config_detected:
        pass_count += 1
    print(
        f"{'[PASS]' if config_detected else '[FAIL]'} TC-03 Feasibility Agent: "
        f"Correctly identified Google Maps as existing_configuration (Settings: {maps_feas['documented_settings_path'] if maps_feas else 'None'})"
    )

    # -------------------------------------------------------------------------
    # Test 4: 3-Point Estimation Math Consistency
    # -------------------------------------------------------------------------
    total_tests += 1
    estimates_a = res_a["task_estimates"]
    math_valid = all(e["low_hours"] <= e["likely_hours"] <= e["high_hours"] for e in estimates_a)

    if math_valid:
        pass_count += 1
    print(
        f"{'[PASS]' if math_valid else '[FAIL]'} TC-04 Estimation Agent: "
        f"Verified 3-point estimate math integrity (low <= likely <= high across all {len(estimates_a)} tasks)"
    )

    # -------------------------------------------------------------------------
    # Test 5: Scope Comparison & Delta Detection (Meeting C vs Meeting A)
    # -------------------------------------------------------------------------
    total_tests += 1
    with open(os.path.join(transcripts_dir, "meeting_c_followup_and_changes.txt"), "r", encoding="utf-8") as f:
        t_c = f.read()

    scope_obj_a = ScopeOfWork(**scope_a)
    delta_res = orchestrator.compare_followup_meeting(
        original_scope=scope_obj_a,
        followup_transcript_text=t_c,
        project_id="Meeting-C-Delta"
    )

    change_report = delta_res["change_report"]
    added_list = change_report["added_requirements"]
    removed_list = change_report["removed_requirements"]
    modified_list = change_report["modified_requirements"]
    warnings = change_report["out_of_scope_warnings"]

    # Verify:
    # 1. Added contains AI Search or Polygon
    # 2. Removed contains REQ-005 (HubSpot)
    # 3. Warnings contains Out-of-scope warning
    # 4. Net hour delta is calculated
    has_added_ai = any("ai-powered" in a["description"].lower() or "polygon" in a["description"].lower() for a in added_list)
    has_removed_hubspot = any("REQ-005" in r["req_id"] for r in removed_list)
    has_warnings = len(warnings) >= 2

    delta_pass = has_added_ai and has_removed_hubspot and has_warnings and change_report["net_hour_delta_likely"] > 0
    if delta_pass:
        pass_count += 1

    print(
        f"{'[PASS]' if delta_pass else '[FAIL]'} TC-05 Scope Comparison Agent: "
        f"Detected {len(added_list)} Added, {len(modified_list)} Modified, {len(removed_list)} Removed. "
        f"Net Delta: +{change_report['net_hour_delta_likely']}h"
    )

    # -------------------------------------------------------------------------
    # Test 6: Out-of-Scope Warning and Change Order Generation
    # -------------------------------------------------------------------------
    total_tests += 1
    has_co_warning = any("OUT-OF-SCOPE WARNING" in w for w in warnings)
    if has_co_warning:
        pass_count += 1
    print(
        f"{'[PASS]' if has_co_warning else '[FAIL]'} TC-06 Commercial Guardrail: "
        f"Generated formal Out-of-Scope Warning & Change Order recommendation"
    )

    # Save deliverables to disk for inspection
    with open(os.path.join(outputs_dir, "meeting_a_proposal.json"), "w", encoding="utf-8") as f:
        json.dump(res_a, f, indent=2, default=str)

    with open(os.path.join(outputs_dir, "meeting_b_proposal.json"), "w", encoding="utf-8") as f:
        json.dump(res_b, f, indent=2, default=str)

    with open(os.path.join(outputs_dir, "meeting_c_change_report.json"), "w", encoding="utf-8") as f:
        json.dump(delta_res, f, indent=2, default=str)

    pass_rate = round((pass_count / total_tests) * 100.0, 1)
    print("\n================================================================================")
    print(f"TASK 3 EVALUATION SUMMARY: {pass_count}/{total_tests} Passed ({pass_rate}%)")
    print("================================================================================")
    print(f"Generated deliverables saved to: {outputs_dir}")

    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%SZ", time.gmtime()),
        "total_tests": total_tests,
        "passed_tests": pass_count,
        "pass_rate_percent": pass_rate
    }
    with open(os.path.join(os.path.dirname(__file__), "evaluation_report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    return report


if __name__ == "__main__":
    run_eval()
