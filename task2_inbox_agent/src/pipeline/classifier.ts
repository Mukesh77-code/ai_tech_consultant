/**
 * Email Intent, Category, and Risk Classifier.
 */

import { CustomerEmail, ClassificationResult, EmailCategory, RiskLevel, UrgencyLevel } from "../types/email";

export class EmailClassifier {
  private anthropicApiKey?: string;

  constructor() {
    this.anthropicApiKey = process.env.ANTHROPIC_API_KEY;
  }

  public async classify(email: CustomerEmail): Promise<ClassificationResult> {
    if (this.anthropicApiKey) {
      const llmResult = await this.classifyWithClaude(email);
      if (llmResult) return llmResult;
    }
    return this.classifyLocal(email);
  }

  private classifyLocal(email: CustomerEmail): ClassificationResult {
    const text = `${email.subject} ${email.body}`.toLowerCase();
    const riskReasons: string[] = [];

    // 1. Check for Refund or Cancellation (FINANCIAL RISK)
    if (
      /refund|cancel|cancellation|chargeback|dispute|money\s*back|reverse\s*(the\s*)?(charge|transaction)|duplicate\s*charge/i.test(text)
    ) {
      riskReasons.push("Involves financial transactions, account termination, or credit card refunds.");
      return {
        category: "Refund or cancellation",
        intent: "Requesting subscription cancellation, invoice refund, or disputing charges.",
        urgency: /immediately|urgent|unauthorized|chargeback/i.test(text) ? "URGENT" : "HIGH",
        risk_level: "FINANCIAL_RISK",
        confidence: 0.94,
        requires_human_approval: true,
        risk_reasons: riskReasons
      };
    }

    // 2. Check for Complaint (REPUTATION RISK)
    if (
      /unacceptable|furious|appalled|horrible|broken|embarrassing|competent|downtime|lawsuit|disaster|awful/i.test(text) ||
      /terrible|worst|shameful|lost\s*(our\s*)?data/i.test(text)
    ) {
      riskReasons.push("Contains expressions of severe customer frustration, service outage, or brand reputation risk.");
      return {
        category: "Complaint",
        intent: "Escalating dissatisfaction with service quality, reliability, or software defects.",
        urgency: "HIGH",
        risk_level: "REPUTATION_RISK",
        confidence: 0.92,
        requires_human_approval: true,
        risk_reasons: riskReasons
      };
    }

    // 3. Check for Quote Request (COMMERCIAL RISK)
    if (
      /quote|how\s*much\s*would|cost\s*estimate|ballpark|pricing\s*proposal|itemized\s*quote|hourly\s*rate/i.test(text) &&
      !/can\s*you\s*(build|develop|take\s*on)/i.test(text)
    ) {
      riskReasons.push("Commercial inquiry involving pricing commitments or formal billing quotations.");
      return {
        category: "Quote request",
        intent: "Requesting pricing estimates, billable development rates, or formal commercial proposals.",
        urgency: "MEDIUM",
        risk_level: "COMMERCIAL_RISK",
        confidence: 0.91,
        requires_human_approval: true,
        risk_reasons: riskReasons
      };
    }

    // 4. Check for Project Request (SCOPE AND PRICING RISK)
    if (
      /build\s*a\s*custom|custom\s*(mobile\s*app|integration|development|booking|escrow|sso|invoicing)|develop\s*(native|custom)|schedule\s*a\s*technical\s*scoping/i.test(text) ||
      /take\s*on\s*this\s*development\s*project/i.test(text)
    ) {
      riskReasons.push("New engineering or customization scope requiring feasibility and architectural review.");
      return {
        category: "Project request",
        intent: "Proposing custom software development, third-party integrations, or platform extensions.",
        urgency: "MEDIUM",
        risk_level: "COMMERCIAL_RISK",
        confidence: 0.93,
        requires_human_approval: true,
        risk_reasons: riskReasons
      };
    }

    // 5. Check for Follow-up
    if (
      /following\s*up|any\s*updates|did\s*you\s*(receive|get)|status\s*of\s*(our|my)|previous\s*(email|discussion|ticket|call)/i.test(text)
    ) {
      return {
        category: "Follow-up",
        intent: "Checking progress or status on an existing pending ticket or prior request.",
        urgency: /launch|party|deadline|today/i.test(text) ? "HIGH" : "LOW",
        risk_level: "LOW",
        confidence: 0.90,
        requires_human_approval: false,
        risk_reasons: []
      };
    }

    // 6. Check for Troubleshooting
    if (
      /troubleshooting|error|failing|stopped\s*(working|functioning)|watermark|404|401|500|warning|warning\s*showing|not\s*sending|not\s*displaying|corrupted|sideways/i.test(text) ||
      /issue\s*with|broken/i.test(text)
    ) {
      return {
        category: "Troubleshooting",
        intent: "Reporting a technical bug, error message, or configuration breakdown.",
        urgency: /urgent|since\s*yesterday|stopped/i.test(text) ? "HIGH" : "MEDIUM",
        risk_level: "MODERATE",
        confidence: 0.89,
        requires_human_approval: false,
        risk_reasons: ["Technical diagnostics required."]
      };
    }

    // 7. Default to How-to question
    return {
      category: "How-to question",
      intent: "Inquiring about platform settings, feature configuration, or standard administration steps.",
      urgency: "LOW",
      risk_level: "LOW",
      confidence: 0.92,
      requires_human_approval: false,
      risk_reasons: []
    };
  }

  private async classifyWithClaude(email: CustomerEmail): Promise<ClassificationResult | null> {
    try {
      const prompt = `Classify this customer support email into one of 7 categories:
1. "How-to question"
2. "Troubleshooting"
3. "Project request"
4. "Refund or cancellation"
5. "Complaint"
6. "Quote request"
7. "Follow-up"

Subject: ${email.subject}
Body: ${email.body}

Return JSON only:
{
  "category": "...",
  "intent": "...",
  "urgency": "LOW|MEDIUM|HIGH|URGENT",
  "risk_level": "LOW|MODERATE|HIGH|FINANCIAL_RISK|COMMERCIAL_RISK|REPUTATION_RISK",
  "requires_human_approval": true/false,
  "confidence": 0.95,
  "risk_reasons": ["..."]
}`;

      const res = await fetch("https://api.anthropic.com/v1/messages", {
        method: "POST",
        headers: {
          "x-api-key": this.anthropicApiKey!,
          "anthropic-version": "2023-06-01",
          "content-type": "application/json"
        },
        body: JSON.stringify({
          model: "claude-3-5-sonnet-20241022",
          max_tokens: 300,
          messages: [{ role: "user", content: prompt }]
        })
      });

      if (res.ok) {
        const data = await res.json();
        const text = data.content[0].text;
        const match = text.match(/\{[\s\S]*\}/);
        if (match) {
          return JSON.parse(match[0]) as ClassificationResult;
        }
      }
    } catch (e) {
      console.warn("Claude classification failed, using local rule classifier:", e);
    }
    return null;
  }
}
