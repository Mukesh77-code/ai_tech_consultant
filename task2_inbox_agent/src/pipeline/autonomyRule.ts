/**
 * 20-Consecutive-Approval Autonomy Rule Engine.
 * Evaluates draft vs final sent reply, tracks unedited approval streaks,
 * enforces hard safety gates for high-risk categories, and manages autonomy trials.
 */

import * as fs from "fs";
import * as path from "path";
import { EmailCategory, AutonomyRuleStatus, RiskLevel } from "../types/email";

export class AutonomyRuleEngine {
  private stateFilePath: string;
  private consecutiveThreshold: number;
  private state: Record<EmailCategory, AutonomyRuleStatus>;

  // Categories permanently blocked from autonomous sending regardless of consecutive approvals
  private static readonly HARD_SAFETY_BLOCKED_CATEGORIES: EmailCategory[] = [
    "Refund or cancellation",
    "Complaint",
    "Project request",
    "Quote request"
  ];

  constructor(
    stateFilePath: string = path.join(__dirname, "../storage/autonomy_state.json"),
    threshold: number = parseInt(process.env.CONSECUTIVE_APPROVAL_THRESHOLD || "20", 10)
  ) {
    this.stateFilePath = stateFilePath;
    this.consecutiveThreshold = threshold;
    this.state = this.loadState();
  }

  private getDefaultCategoryStatus(category: EmailCategory): AutonomyRuleStatus {
    const isHardBlocked = AutonomyRuleEngine.HARD_SAFETY_BLOCKED_CATEGORIES.includes(category);
    let reason: string | undefined;

    if (category === "Refund or cancellation") {
      reason = "Hard safety gate: Involves financial liabilities, Stripe/PayPal refunds, and accounting sign-off.";
    } else if (category === "Complaint") {
      reason = "Hard safety gate: Reputation and SLA risk requires empathetic human escalation.";
    } else if (category === "Project request" || category === "Quote request") {
      reason = "Hard safety gate: Commercial scoping and binding price commitments require human approval.";
    }

    return {
      category,
      consecutive_unmodified_approvals: 0,
      is_eligible_for_autonomy_trial: false,
      is_autonomously_sending: false,
      hard_safety_gate_blocked: isHardBlocked,
      safety_block_reason: reason,
      last_updated: new Date().toISOString()
    };
  }

  private loadState(): Record<EmailCategory, AutonomyRuleStatus> {
    const categories: EmailCategory[] = [
      "How-to question",
      "Troubleshooting",
      "Project request",
      "Refund or cancellation",
      "Complaint",
      "Quote request",
      "Follow-up"
    ];

    if (fs.existsSync(this.stateFilePath)) {
      try {
        const raw = fs.readFileSync(this.stateFilePath, "utf-8");
        const parsed = JSON.parse(raw);
        // Ensure all categories exist
        for (const cat of categories) {
          if (!parsed[cat]) {
            parsed[cat] = this.getDefaultCategoryStatus(cat);
          }
        }
        return parsed;
      } catch (e) {
        console.warn(`[AutonomyRuleEngine] Failed to read state from ${this.stateFilePath}:`, e);
      }
    }

    const initial: Record<string, AutonomyRuleStatus> = {};
    for (const cat of categories) {
      initial[cat] = this.getDefaultCategoryStatus(cat);
    }
    return initial as Record<EmailCategory, AutonomyRuleStatus>;
  }

  public saveState(): void {
    const dir = path.dirname(this.stateFilePath);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
    fs.writeFileSync(this.stateFilePath, JSON.stringify(this.state, null, 2), "utf-8");
  }

  /**
   * Normalized string diff comparison to check if draft was modified by reviewer.
   * Strips whitespace discrepancies, trailing punctuation, and normalizes line breaks.
   */
  public isTextUnmodified(originalDraft: string, finalSentText: string): { isUnmodified: boolean; diffChars: number } {
    const normA = originalDraft.trim().replace(/\r\n/g, "\n").replace(/[ \t]+/g, " ");
    const normB = finalSentText.trim().replace(/\r\n/g, "\n").replace(/[ \t]+/g, " ");

    const diff = Math.abs(normA.length - normB.length);
    const isUnmodified = normA === normB;
    return { isUnmodified, diffChars: isUnmodified ? 0 : diff };
  }

  /**
   * Evaluates human review outcome and updates the consecutive counter.
   */
  public recordReviewOutcome(
    category: EmailCategory,
    originalDraft: string,
    finalSentText: string,
    action: "APPROVE_AS_IS" | "EDIT_AND_SEND" | "REJECT_AND_REWRITE" | "ESCALATE_TO_EXPERT"
  ): AutonomyRuleStatus {
    const status = this.state[category] || this.getDefaultCategoryStatus(category);
    const { isUnmodified, diffChars } = this.isTextUnmodified(originalDraft, finalSentText);

    if (action === "APPROVE_AS_IS" && isUnmodified) {
      status.consecutive_unmodified_approvals += 1;

      // Check if threshold reached
      if (
        status.consecutive_unmodified_approvals >= this.consecutiveThreshold &&
        !status.hard_safety_gate_blocked
      ) {
        status.is_eligible_for_autonomy_trial = true;
      }
    } else {
      // Any edit, rejection, or manual rewrite resets the counter immediately to 0
      status.consecutive_unmodified_approvals = 0;
      status.is_eligible_for_autonomy_trial = false;
      status.is_autonomously_sending = false;
    }

    status.last_updated = new Date().toISOString();
    this.state[category] = status;
    this.saveState();

    return status;
  }

  public getAllStatuses(): AutonomyRuleStatus[] {
    return Object.values(this.state);
  }

  public getStatus(category: EmailCategory): AutonomyRuleStatus {
    return this.state[category] || this.getDefaultCategoryStatus(category);
  }

  public setAutonomousSending(category: EmailCategory, enable: boolean): AutonomyRuleStatus {
    const status = this.getStatus(category);
    if (status.hard_safety_gate_blocked && enable) {
      throw new Error(`Cannot enable autonomous sending for ${category}: Blocked by hard safety policy.`);
    }
    if (!status.is_eligible_for_autonomy_trial && enable) {
      throw new Error(`Cannot enable autonomous sending for ${category}: Requires ${this.consecutiveThreshold} consecutive unmodified approvals.`);
    }

    status.is_autonomously_sending = enable;
    status.last_updated = new Date().toISOString();
    this.state[category] = status;
    this.saveState();
    return status;
  }
}
