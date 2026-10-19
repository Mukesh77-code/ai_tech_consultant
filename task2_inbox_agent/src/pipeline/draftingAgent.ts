/**
 * Drafting Agent for Task 2.
 * Synthesizes grounded, empathetic, brand-aligned email drafts
 * strictly consuming the Knowledge Brain API (Task 1).
 */

import { CustomerEmail, ClassificationResult, DraftResponse, KnowledgeBrainResponse } from "../types/email";
import { KnowledgeBrainClient } from "../client/knowledgeBrainClient";
import { ResponseValidator } from "./validator";

export class DraftingAgent {
  private knowledgeBrain: KnowledgeBrainClient;
  private validator: ResponseValidator;
  private modelVersion: string = "claude-3-5-sonnet-inbox-v1";
  private promptVersion: string = "inbox-system-v2.1";

  constructor(knowledgeBrainClient?: KnowledgeBrainClient) {
    this.knowledgeBrain = knowledgeBrainClient || new KnowledgeBrainClient();
    this.validator = new ResponseValidator();
  }

  public async generateDraft(
    email: CustomerEmail,
    classification: ClassificationResult
  ): Promise<DraftResponse> {
    const category = classification.category;
    let kbResult: KnowledgeBrainResponse | null = null;

    // 1. Query Knowledge Brain for technical/procedural evidence
    if (["How-to question", "Troubleshooting", "Project request"].includes(category)) {
      const queryPrompt = `${email.subject}: ${email.body}`;
      kbResult = await this.knowledgeBrain.query(queryPrompt, 3);
    }

    // 2. Draft Response by Category
    let suggestedReply = "";
    let suggestedNextAction = "";

    switch (category) {
      case "How-to question":
        if (kbResult && kbResult.status === "grounded") {
          suggestedReply = (
            `Hi ${email.sender_name},\n\n` +
            `Thank you for reaching out to support! Here is how you can resolve this:\n\n` +
            `${kbResult.answer}\n\n` +
            `If you have any further questions or if anything isn't displaying as expected, please feel free to reply directly to this email.\n\n` +
            `Best regards,\nCustomer Support Team\nAI Tech Consulting`
          );
          suggestedNextAction = "Send instructional guide with attached documentation link.";
        } else {
          suggestedReply = (
            `Hi ${email.sender_name},\n\n` +
            `Thank you for contacting us regarding "${email.subject}". We are currently verifying the configuration requirements for your specific directory setup and will follow up with complete step-by-step instructions shortly.\n\n` +
            `Best regards,\nCustomer Support Team`
          );
          suggestedNextAction = "Verify admin settings with technical specialist.";
        }
        break;

      case "Troubleshooting":
        if (kbResult && kbResult.status === "grounded") {
          suggestedReply = (
            `Hi ${email.sender_name},\n\n` +
            `Thank you for bringing this issue to our attention. Based on our technical diagnostics:\n\n` +
            `${kbResult.answer}\n\n` +
            `Please test this in your dashboard and let us know if the issue persists so our engineering team can investigate your server logs further.\n\n` +
            `Best regards,\nTechnical Support Team`
          );
          suggestedNextAction = "Provide diagnostic steps and monitor for confirmation.";
        } else {
          suggestedReply = (
            `Hi ${email.sender_name},\n\n` +
            `Thank you for reporting this issue with ${email.subject}. Our technical team has opened diagnostic ticket #${email.id} to investigate the error and inspect your site logs. We will update you as soon as the root cause is resolved.\n\n` +
            `Best regards,\nTechnical Support Team`
          );
          suggestedNextAction = "Escalate diagnostic logs to engineering.";
        }
        break;

      case "Project request":
        suggestedReply = (
          `Hi ${email.sender_name},\n\n` +
          `Thank you for considering our team for your custom development project! Your request regarding "${email.subject}" has been reviewed by our technical consulting group.\n\n` +
          `To ensure we deliver an accurate scope of work, technical architecture, and milestone timeline, we would love to schedule a 20-minute technical discovery call with our lead architect.\n\n` +
          `Please let us know your availability this week, or book directly via our consultation calendar.\n\n` +
          `Best regards,\nSolutions Architecture Team`
        );
        suggestedNextAction = "Coordinate technical discovery call and initiate Task 3 Meeting to Scope.";
        break;

      case "Refund or cancellation":
        suggestedReply = (
          `Hi ${email.sender_name},\n\n` +
          `We have received your cancellation and billing request regarding your subscription. We take billing inquiries very seriously.\n\n` +
          `Our finance team is currently reviewing your account transaction history and invoice details. We will process your account request in accordance with our service terms and send you a formal confirmation receipt within 1 business day.\n\n` +
          `Sincerely,\nBilling Operations Team`
        );
        suggestedNextAction = "Verify transaction history in Stripe/PayPal and obtain manager sign-off.";
        break;

      case "Complaint":
        suggestedReply = (
          `Dear ${email.sender_name},\n\n` +
          `I am truly sorry to hear about your frustrating experience with "${email.subject}". This does not reflect the standard of quality and reliability we strive to deliver.\n\n` +
          `I have personally escalated this matter to our Senior Engineering Leadership team with top priority. We are actively investigating the issue and will provide you with a full incident report and resolution path today.\n\n` +
          `Sincerely,\nClient Relations & Support Leadership`
        );
        suggestedNextAction = "Senior executive review and immediate SLA check.";
        break;

      case "Quote request":
        suggestedReply = (
          `Hi ${email.sender_name},\n\n` +
          `Thank you for your inquiry regarding custom development pricing for "${email.subject}".\n\n` +
          `To provide you with an itemized, guaranteed estimate, our solutions team is preparing a tailored proposal based on your specific requirements and integration scope. We will follow up with our complete proposal and hour estimates shortly.\n\n` +
          `Best regards,\nCommercial Consulting Team`
        );
        suggestedNextAction = "Compile structured proposal via Task 3 Estimation Engine.";
        break;

      case "Follow-up":
        suggestedReply = (
          `Hi ${email.sender_name},\n\n` +
          `Thank you for following up with us. We have located your prior request regarding "${email.subject}".\n\n` +
          `Our team is actively working on this item and expects to have a definitive update for you by end of day today. We appreciate your patience!\n\n` +
          `Best regards,\nCustomer Support Team`
        );
        suggestedNextAction = "Check resolution timeline with assigned agent.";
        break;
    }

    // 3. Apply Policy Validation & Guardrails
    const validation = this.validator.validate(suggestedReply, category, classification.risk_level);
    const finalReply = validation.sanitizedReply;
    const requiresHuman = classification.requires_human_approval || validation.enforceHumanReview;

    return {
      email_id: email.id,
      category,
      summary: `${classification.intent} (Urgency: ${classification.urgency}, Risk: ${classification.risk_level})`,
      suggested_reply: finalReply,
      risk_level: classification.risk_level,
      requires_human_approval: requiresHuman,
      citations: kbResult?.sources || [],
      grounding_status: kbResult?.status || "policy_template",
      confidence: kbResult?.confidence || classification.confidence,
      suggested_next_action: suggestedNextAction,
      model_version: this.modelVersion,
      prompt_version: this.promptVersion,
      created_at: new Date().toISOString()
    };
  }
}
