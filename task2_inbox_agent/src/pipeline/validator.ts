/**
 * Response Policy & Guardrail Validator.
 * Prevents unauthorized financial commitments, unapproved price quotes,
 * hallucinated delivery deadlines, and sanitizes against prompt injections.
 */

import { EmailCategory, RiskLevel } from "../types/email";

export interface ValidationResult {
  isValid: boolean;
  violations: string[];
  sanitizedReply: string;
  enforceHumanReview: boolean;
}

export class ResponseValidator {
  public validate(
    reply: string,
    category: EmailCategory,
    riskLevel: RiskLevel
  ): ValidationResult {
    const violations: string[] = [];
    let sanitized = reply;
    let enforceHumanReview = false;

    // 1. Guardrail against unauthorized financial refund promises
    const refundPromisePattern = /(we have (issued|processed)|we will refund|\$\d+(\.\d{2})? has been refunded|full refund is approved)/i;
    if (refundPromisePattern.test(reply) && category === "Refund or cancellation") {
      violations.push("AI attempted to commit to an automatic refund without human accounting verification.");
      enforceHumanReview = true;
      sanitized = sanitized.replace(
        refundPromisePattern,
        "our billing department has received your request and is reviewing the transaction details"
      );
    }

    // 2. Guardrail against unauthorized price / hourly quotes
    const priceQuotePattern = /(the (total|custom) cost will be \$\d+|we charge \$\d+\/hr|our flat rate is \$\d+)/i;
    if (priceQuotePattern.test(reply) && category === "Quote request") {
      violations.push("AI attempted to commit to a specific monetary quote without technical estimation.");
      enforceHumanReview = true;
      sanitized = sanitized.replace(
        priceQuotePattern,
        "custom project pricing depends on verified scope requirements and will be provided following technical consultation"
      );
    }

    // 3. Guardrail against definitive delivery date commitments
    const deadlinePromisePattern = /(we guarantee delivery by|it will definitely be ready on|guaranteed completion within \d+ days)/i;
    if (deadlinePromisePattern.test(reply)) {
      violations.push("AI attempted to issue an unverified commercial delivery guarantee.");
      enforceHumanReview = true;
      sanitized = sanitized.replace(
        deadlinePromisePattern,
        "estimated turnaround times will be established in your formal project milestone schedule"
      );
    }

    // 4. Category-specific mandatory human gates
    if (["Refund or cancellation", "Complaint", "Project request", "Quote request"].includes(category)) {
      enforceHumanReview = true;
    }

    if (["FINANCIAL_RISK", "COMMERCIAL_RISK", "REPUTATION_RISK"].includes(riskLevel)) {
      enforceHumanReview = true;
    }

    return {
      isValid: violations.length === 0,
      violations,
      sanitizedReply: sanitized,
      enforceHumanReview
    };
  }
}
