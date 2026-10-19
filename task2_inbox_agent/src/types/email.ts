/**
 * TypeScript Data Types for Task 2 Inbox Agent
 */

export type EmailCategory =
  | "How-to question"
  | "Troubleshooting"
  | "Project request"
  | "Refund or cancellation"
  | "Complaint"
  | "Quote request"
  | "Follow-up";

export type RiskLevel = "LOW" | "MODERATE" | "HIGH" | "FINANCIAL_RISK" | "COMMERCIAL_RISK" | "REPUTATION_RISK";

export type UrgencyLevel = "LOW" | "MEDIUM" | "HIGH" | "URGENT";

export type ProcessingStatus = "UNPROCESSED" | "DRAFTED" | "APPROVED" | "EDITED_AND_SENT" | "REJECTED" | "ESCALATED";

export interface KnowledgeCitation {
  title: string;
  url: string;
  section?: string;
  excerpt?: string;
  image_url?: string | null;
}

export interface KnowledgeBrainResponse {
  question: string;
  answer: string;
  confidence: number;
  status: "grounded" | "insufficient_evidence" | "escalated";
  requires_human: boolean;
  escalation_id?: string | null;
  sources: KnowledgeCitation[];
}

export interface CustomerEmail {
  id: string;
  sender_email: string;
  sender_name: string;
  subject: string;
  body: string;
  received_at: string;
  expected_category?: EmailCategory;
  expected_risk?: RiskLevel;
}

export interface ClassificationResult {
  category: EmailCategory;
  intent: string;
  urgency: UrgencyLevel;
  risk_level: RiskLevel;
  confidence: number;
  requires_human_approval: boolean;
  risk_reasons: string[];
}

export interface DraftResponse {
  email_id: string;
  category: EmailCategory;
  summary: string;
  suggested_reply: string;
  risk_level: RiskLevel;
  requires_human_approval: boolean;
  citations: KnowledgeCitation[];
  grounding_status: string;
  confidence: number;
  suggested_next_action: string;
  model_version: string;
  prompt_version: string;
  created_at: string;
}

export interface HumanReviewAction {
  email_id: string;
  action: "APPROVE_AS_IS" | "EDIT_AND_SEND" | "REJECT_AND_REWRITE" | "ESCALATE_TO_EXPERT";
  final_sent_reply?: string;
  correction_reason?: string;
  reviewer_name?: string;
}

export interface AutonomyRuleStatus {
  category: EmailCategory;
  consecutive_unmodified_approvals: number;
  is_eligible_for_autonomy_trial: boolean;
  is_autonomously_sending: boolean;
  hard_safety_gate_blocked: boolean;
  safety_block_reason?: string;
  last_updated: string;
}

export interface FeedbackRecord {
  id: string;
  email_id: string;
  category: EmailCategory;
  original_email_body: string;
  generated_draft: string;
  final_sent_reply: string;
  was_modified: boolean;
  edit_character_diff: number;
  review_action: string;
  correction_reason?: string;
  reviewer_name: string;
  timestamp: string;
}
