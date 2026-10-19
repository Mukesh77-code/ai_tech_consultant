/**
 * Evaluation Suite for Task 2 Inbox Agent.
 * Runs 25 comprehensive test cases validating:
 * 1. Email classification accuracy across all 7 categories
 * 2. Risk level and human review mandatory gating
 * 3. Guardrail and policy validation (blocking unauthorized financial/pricing commitments)
 * 4. 20-consecutive-approval autonomy counter and hard safety gates
 * 5. Feedback learning metrics computation
 */

import * as fs from "fs";
import * as path from "path";
import { CustomerEmail, EmailCategory } from "../src/types/email";
import { EmailClassifier } from "../src/pipeline/classifier";
import { ResponseValidator } from "../src/pipeline/validator";
import { AutonomyRuleEngine } from "../src/pipeline/autonomyRule";
import { FeedbackStore } from "../src/storage/feedbackStore";
import { DraftingAgent } from "../src/pipeline/draftingAgent";
import { KnowledgeBrainClient } from "../src/client/knowledgeBrainClient";

async function runTask2Evaluation() {
  console.log("================================================================================");
  console.log("RUNNING TASK 2 INBOX AGENT COMPREHENSIVE EVALUATION SUITE");
  console.log("================================================================================\n");

  const datasetPath = path.join(__dirname, "../src/storage/dataset.json");
  const dataset: CustomerEmail[] = JSON.parse(fs.readFileSync(datasetPath, "utf-8"));

  const classifier = new EmailClassifier();
  const validator = new ResponseValidator();
  const feedbackStore = new FeedbackStore(path.join(__dirname, "../src/storage/test_feedback.json"));
  const autonomyEngine = new AutonomyRuleEngine(path.join(__dirname, "../src/storage/test_autonomy.json"), 20);

  let passedTests = 0;
  let totalTests = 0;

  // -------------------------------------------------------------------------
  // Test Section 1: Classification & Risk Detection on 20 Diverse Emails
  // -------------------------------------------------------------------------
  console.log("--- Section 1: Email Intent, Category & Risk Classification ---");
  const sampleIndices = [0, 1, 2, 6, 7, 12, 13, 14, 17, 22, 23, 24, 28, 29, 30, 34, 35, 40, 41, 45, 46, 47];

  for (const idx of sampleIndices) {
    totalTests++;
    const email = dataset[idx];
    const res = await classifier.classify(email);

    const categoryMatch = res.category === email.expected_category;
    const humanReviewEnforced =
      ["Refund or cancellation", "Complaint", "Project request", "Quote request"].includes(res.category)
        ? res.requires_human_approval === true
        : true;

    const isPassed = categoryMatch && humanReviewEnforced;
    if (isPassed) passedTests++;

    console.log(
      `${isPassed ? "[PASS]" : "[FAIL]"} TC-${String(totalTests).padStart(2, "0")} [${email.id}] ` +
      `Exp: "${email.expected_category}" -> Got: "${res.category}" ` +
      `(Risk: ${res.risk_level}, HumanGate: ${res.requires_human_approval})`
    );
  }

  // -------------------------------------------------------------------------
  // Test Section 2: Policy Guardrail Enforcement (Refund & Pricing Promises)
  // -------------------------------------------------------------------------
  console.log("\n--- Section 2: Guardrail & Policy Protection ---");

  // Subtest 2.1: Rejecting unauthorized refund promise
  totalTests++;
  const unsafeRefundText = "We have issued a full refund of $499 back to your credit card immediately.";
  const refundValidation = validator.validate(unsafeRefundText, "Refund or cancellation", "FINANCIAL_RISK");
  const refundBlocked = !refundValidation.isValid && refundValidation.enforceHumanReview;
  if (refundBlocked) passedTests++;
  console.log(
    `${refundBlocked ? "[PASS]" : "[FAIL]"} TC-${String(totalTests).padStart(2, "0")} ` +
    `Unauthorized Refund Commitment Interception (Violations: ${refundValidation.violations.length})`
  );

  // Subtest 2.2: Rejecting unauthorized price quote
  totalTests++;
  const unsafePriceText = "We charge $8,500 for this custom integration and the total cost will be $8,500.";
  const priceValidation = validator.validate(unsafePriceText, "Quote request", "COMMERCIAL_RISK");
  const priceBlocked = !priceValidation.isValid && priceValidation.enforceHumanReview;
  if (priceBlocked) passedTests++;
  console.log(
    `${priceBlocked ? "[PASS]" : "[FAIL]"} TC-${String(totalTests).padStart(2, "0")} ` +
    `Unauthorized Price Quote Interception (Violations: ${priceValidation.violations.length})`
  );

  // -------------------------------------------------------------------------
  // Test Section 3: 20-Consecutive-Approval Autonomy Engine
  // -------------------------------------------------------------------------
  console.log("\n--- Section 3: 20-Consecutive-Approval Autonomy Engine ---");

  // Subtest 3.1: Consecutive unmodified approvals incrementing
  totalTests++;
  const draft = "Here is how to update your logo: Go to Settings > General Settings.";
  for (let i = 0; i < 5; i++) {
    autonomyEngine.recordReviewOutcome("How-to question", draft, draft, "APPROVE_AS_IS");
  }
  const statusAfter5 = autonomyEngine.getStatus("How-to question");
  const incOk = statusAfter5.consecutive_unmodified_approvals === 5;
  if (incOk) passedTests++;
  console.log(
    `${incOk ? "[PASS]" : "[FAIL]"} TC-${String(totalTests).padStart(2, "0")} ` +
    `5 Consecutive Approvals Recorded: count = ${statusAfter5.consecutive_unmodified_approvals}/20`
  );

  // Subtest 3.2: Human modification resets streak to 0
  totalTests++;
  const modifiedDraft = "Here is how to update your logo: Go to Settings > General Settings and click Brand Identity.";
  autonomyEngine.recordReviewOutcome("How-to question", draft, modifiedDraft, "EDIT_AND_SEND");
  const statusAfterEdit = autonomyEngine.getStatus("How-to question");
  const resetOk = statusAfterEdit.consecutive_unmodified_approvals === 0;
  if (resetOk) passedTests++;
  console.log(
    `${resetOk ? "[PASS]" : "[FAIL]"} TC-${String(totalTests).padStart(2, "0")} ` +
    `Human Edit Resets Consecutive Count: count = ${statusAfterEdit.consecutive_unmodified_approvals}`
  );

  // Subtest 3.3: Hard safety gate prevents high risk categories even with 20 approvals
  totalTests++;
  for (let i = 0; i < 22; i++) {
    autonomyEngine.recordReviewOutcome("Refund or cancellation", "Processing refund inquiry.", "Processing refund inquiry.", "APPROVE_AS_IS");
  }
  const refundStatus = autonomyEngine.getStatus("Refund or cancellation");
  const safetyGateOk = refundStatus.hard_safety_gate_blocked && !refundStatus.is_eligible_for_autonomy_trial;
  if (safetyGateOk) passedTests++;
  console.log(
    `${safetyGateOk ? "[PASS]" : "[FAIL]"} TC-${String(totalTests).padStart(2, "0")} ` +
    `Hard Safety Gate Blocks High-Risk Autonomy (Category: Refund or cancellation, Blocked: ${refundStatus.hard_safety_gate_blocked})`
  );

  // Subtest 3.4: Feedback Store metrics computation
  totalTests++;
  feedbackStore.addRecord({
    id: "FB-TEST-1",
    email_id: "EM-001",
    category: "How-to question",
    original_email_body: "Test email",
    generated_draft: draft,
    final_sent_reply: draft,
    was_modified: false,
    edit_character_diff: 0,
    review_action: "APPROVE_AS_IS",
    reviewer_name: "Test Reviewer",
    timestamp: new Date().toISOString()
  });
  const metrics = feedbackStore.getSummaryMetrics();
  const metricsOk = metrics.total_reviews >= 1 && typeof metrics.unmodified_rate_percent === "number";
  if (metricsOk) passedTests++;
  console.log(
    `${metricsOk ? "[PASS]" : "[FAIL]"} TC-${String(totalTests).padStart(2, "0")} ` +
    `Feedback Store Summary Metrics (Total: ${metrics.total_reviews}, Unmodified Rate: ${metrics.unmodified_rate_percent}%)`
  );

  // Clean up test files
  try {
    if (fs.existsSync(path.join(__dirname, "../src/storage/test_autonomy.json"))) {
      fs.unlinkSync(path.join(__dirname, "../src/storage/test_autonomy.json"));
    }
    if (fs.existsSync(path.join(__dirname, "../src/storage/test_feedback.json"))) {
      fs.unlinkSync(path.join(__dirname, "../src/storage/test_feedback.json"));
    }
  } catch {}

  const passRate = Math.round((passedTests / totalTests) * 1000) / 10;
  console.log("\n================================================================================");
  console.log(`TASK 2 EVALUATION SUMMARY: ${passedTests}/${totalTests} Passed (${passRate}%)`);
  console.log("================================================================================");

  // Save report
  const reportPath = path.join(__dirname, "../evaluation_report.json");
  fs.writeFileSync(
    reportPath,
    JSON.stringify(
      {
        timestamp: new Date().toISOString(),
        total_tests: totalTests,
        passed_tests: passedTests,
        pass_rate_percent: passRate
      },
      null,
      2
    )
  );

  if (passRate < 100) {
    process.exit(1);
  }
}

runTask2Evaluation().catch((err) => {
  console.error("Evaluation failed:", err);
  process.exit(1);
});
