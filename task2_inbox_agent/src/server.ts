/**
 * Express Server for Task 2 Inbox Agent & Human Review Interface.
 */

import express, { Request, Response } from "express";
import cors from "cors";
import * as path from "path";
import * as fs from "fs";
import * as dotenv from "dotenv";

import { CustomerEmail, ProcessingStatus, DraftResponse, HumanReviewAction } from "./types/email";
import { EmailClassifier } from "./pipeline/classifier";
import { DraftingAgent } from "./pipeline/draftingAgent";
import { AutonomyRuleEngine } from "./pipeline/autonomyRule";
import { FeedbackStore } from "./storage/feedbackStore";
import { KnowledgeBrainClient } from "./client/knowledgeBrainClient";

dotenv.config({ path: path.join(__dirname, "../../.env") });

const app = express();
const PORT = process.env.INBOX_AGENT_PORT || 3000;

app.use(cors());
app.use(express.json());
const publicPath = fs.existsSync(path.join(__dirname, "public"))
  ? path.join(__dirname, "public")
  : path.join(__dirname, "../src/public");
app.use(express.static(publicPath));

// Core Singletons
const classifier = new EmailClassifier();
const kbClient = new KnowledgeBrainClient();
const draftingAgent = new DraftingAgent(kbClient);
const autonomyEngine = new AutonomyRuleEngine();
const feedbackStore = new FeedbackStore();

// In-Memory Email Cache / State
interface EmailState {
  email: CustomerEmail;
  status: ProcessingStatus;
  draft?: DraftResponse;
  final_sent_reply?: string;
  reviewer_action?: string;
  correction_reason?: string;
  reviewed_at?: string;
}

const emailDatasetPath = fs.existsSync(path.join(__dirname, "storage/dataset.json"))
  ? path.join(__dirname, "storage/dataset.json")
  : path.join(__dirname, "../src/storage/dataset.json");
let emailsCache: Record<string, EmailState> = {};

function initEmails() {
  if (fs.existsSync(emailDatasetPath)) {
    const raw = fs.readFileSync(emailDatasetPath, "utf-8");
    const list: CustomerEmail[] = JSON.parse(raw);
    for (const e of list) {
      emailsCache[e.id] = {
        email: e,
        status: "UNPROCESSED"
      };
    }
  }
}
initEmails();

// API Endpoints

// 1. List all emails
app.get("/api/emails", (req: Request, res: Response) => {
  const result = Object.values(emailsCache).map((s) => ({
    ...s.email,
    status: s.status,
    has_draft: !!s.draft,
    draft: s.draft,
    final_sent_reply: s.final_sent_reply,
    reviewer_action: s.reviewer_action
  }));
  res.json({ total: result.length, emails: result });
});

// 2. Process / Generate draft for an email
app.post("/api/emails/:id/process", async (req: Request, res: Response) => {
  const emailId = req.params.id;
  const state = emailsCache[emailId];

  if (!state) {
    return res.status(404).json({ error: `Email ${emailId} not found` });
  }

  try {
    const classification = await classifier.classify(state.email);
    const draft = await draftingAgent.generateDraft(state.email, classification);

    state.draft = draft;
    state.status = "DRAFTED";

    // Check if category is autonomously sending
    const autonomyStatus = autonomyEngine.getStatus(draft.category);
    if (autonomyStatus.is_autonomously_sending && !draft.requires_human_approval) {
      state.status = "APPROVED";
      state.final_sent_reply = draft.suggested_reply;
      state.reviewer_action = "AUTONOMOUSLY_SENT";
      state.reviewed_at = new Date().toISOString();

      // Record feedback
      feedbackStore.addRecord({
        id: `FB-${Date.now()}`,
        email_id: emailId,
        category: draft.category,
        original_email_body: state.email.body,
        generated_draft: draft.suggested_reply,
        final_sent_reply: draft.suggested_reply,
        was_modified: false,
        edit_character_diff: 0,
        review_action: "APPROVE_AS_IS",
        reviewer_name: "Autonomous Agent Engine",
        timestamp: new Date().toISOString()
      });
    }

    res.json({ success: true, email_state: state });
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

// 3. Process all unprocessed emails in bulk
app.post("/api/emails/process-all", async (req: Request, res: Response) => {
  try {
    let count = 0;
    for (const id of Object.keys(emailsCache)) {
      const state = emailsCache[id];
      if (state.status === "UNPROCESSED") {
        const classification = await classifier.classify(state.email);
        const draft = await draftingAgent.generateDraft(state.email, classification);
        state.draft = draft;
        state.status = "DRAFTED";
        count++;
      }
    }
    res.json({ success: true, processed_count: count });
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

// 4. Submit Human Review Decision
app.post("/api/emails/:id/review", (req: Request, res: Response) => {
  const emailId = req.params.id;
  const state = emailsCache[emailId];

  if (!state || !state.draft) {
    return res.status(404).json({ error: "Email or draft not found. Run process first." });
  }

  const review: HumanReviewAction = req.body;
  const draftReply = state.draft.suggested_reply;
  const finalSent = review.final_sent_reply || draftReply;

  // Determine if draft was modified
  const { isUnmodified, diffChars } = autonomyEngine.isTextUnmodified(draftReply, finalSent);

  // Update autonomy counter
  const updatedAutonomy = autonomyEngine.recordReviewOutcome(
    state.draft.category,
    draftReply,
    finalSent,
    review.action
  );

  // Set processing status
  if (review.action === "APPROVE_AS_IS") {
    state.status = "APPROVED";
  } else if (review.action === "EDIT_AND_SEND") {
    state.status = "EDITED_AND_SENT";
  } else if (review.action === "REJECT_AND_REWRITE") {
    state.status = "REJECTED";
  } else if (review.action === "ESCALATE_TO_EXPERT") {
    state.status = "ESCALATED";
  }

  state.final_sent_reply = finalSent;
  state.reviewer_action = review.action;
  state.correction_reason = review.correction_reason;
  state.reviewed_at = new Date().toISOString();

  // Save audit feedback record
  feedbackStore.addRecord({
    id: `FB-${Date.now()}`,
    email_id: emailId,
    category: state.draft.category,
    original_email_body: state.email.body,
    generated_draft: draftReply,
    final_sent_reply: finalSent,
    was_modified: !isUnmodified,
    edit_character_diff: diffChars,
    review_action: review.action,
    correction_reason: review.correction_reason,
    reviewer_name: review.reviewer_name || "Support Reviewer",
    timestamp: new Date().toISOString()
  });

  res.json({
    success: true,
    email_state: state,
    autonomy_status: updatedAutonomy
  });
});

// 5. Get 20-consecutive rule autonomy status
app.get("/api/autonomy/status", (req: Request, res: Response) => {
  res.json({
    threshold: 20,
    categories: autonomyEngine.getAllStatuses()
  });
});

// 6. Toggle autonomous sending for an eligible category
app.post("/api/autonomy/toggle", (req: Request, res: Response) => {
  const { category, enable } = req.body;
  try {
    const updated = autonomyEngine.setAutonomousSending(category, enable);
    res.json({ success: true, status: updated });
  } catch (err: any) {
    res.status(400).json({ error: err.message });
  }
});

// 7. Feedback summary and metrics
app.get("/api/feedback/summary", (req: Request, res: Response) => {
  res.json(feedbackStore.getSummaryMetrics());
});

// Start Server
if (require.main === module) {
  app.listen(PORT, () => {
    console.log(`[Task 2 Inbox Agent] Server listening at http://localhost:${PORT}`);
    console.log(`[Task 2 Inbox Agent] Web Interface accessible at http://localhost:${PORT}`);
  });
}

export default app;
