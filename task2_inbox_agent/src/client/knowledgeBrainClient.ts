/**
 * Typed Knowledge Brain API Client.
 * Consumes Task 1 /query endpoint over HTTP.
 */

import { KnowledgeBrainResponse } from "../types/email";

export class KnowledgeBrainClient {
  private baseUrl: string;
  private timeoutMs: number;

  constructor(baseUrl: string = process.env.KNOWLEDGE_BRAIN_URL || "http://127.0.0.1:8000", timeoutMs: number = 8000) {
    this.baseUrl = baseUrl.replace(/\/$/, "");
    this.timeoutMs = timeoutMs;
  }

  public async query(question: string, topK: number = 4): Promise<KnowledgeBrainResponse> {
    const url = `${this.baseUrl}/query`;
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeoutMs);

    try {
      const response = await fetch(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "User-Agent": "Task2-InboxAgent/1.0"
        },
        body: JSON.stringify({
          question,
          top_k: topK,
          auto_escalate: false
        }),
        signal: controller.signal
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new Error(`Knowledge Brain API returned HTTP ${response.status}: ${response.statusText}`);
      }

      const data = (await response.json()) as KnowledgeBrainResponse;
      return data;
    } catch (err: any) {
      clearTimeout(timeoutId);
      console.warn(`[KnowledgeBrainClient] Failed to query Knowledge Brain: ${err.message}. Using safe fallback response.`);

      return {
        question,
        answer: "The Knowledge Brain service could not be reached or returned an error. This inquiry requires manual human review.",
        confidence: 0.0,
        status: "insufficient_evidence",
        requires_human: true,
        sources: []
      };
    }
  }

  public async checkHealth(): Promise<boolean> {
    try {
      const resp = await fetch(`${this.baseUrl}/health`);
      return resp.ok;
    } catch {
      return false;
    }
  }
}
