/**
 * Feedback Learning Store.
 * Records all drafts, human corrections, review outcomes, and computes quality metrics.
 */

import * as fs from "fs";
import * as path from "path";
import { FeedbackRecord, EmailCategory } from "../types/email";

export class FeedbackStore {
  private filePath: string;
  private records: FeedbackRecord[] = [];

  constructor(filePath: string = path.join(__dirname, "../storage/feedback_store.json")) {
    this.filePath = filePath;
    this.records = this.loadRecords();
  }

  private loadRecords(): FeedbackRecord[] {
    if (fs.existsSync(this.filePath)) {
      try {
        const raw = fs.readFileSync(this.filePath, "utf-8");
        return JSON.parse(raw);
      } catch (e) {
        console.warn(`[FeedbackStore] Failed to load feedback records:`, e);
      }
    }
    return [];
  }

  private saveRecords(): void {
    const dir = path.dirname(this.filePath);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
    fs.writeFileSync(this.filePath, JSON.stringify(this.records, null, 2), "utf-8");
  }

  public addRecord(record: FeedbackRecord): void {
    this.records.push(record);
    this.saveRecords();
  }

  public getAllRecords(): FeedbackRecord[] {
    return this.records;
  }

  public getSummaryMetrics() {
    const total = this.records.length;
    if (total === 0) {
      return {
        total_reviews: 0,
        unmodified_rate_percent: 0,
        modified_rate_percent: 0,
        rejection_rate_percent: 0,
        by_category: {}
      };
    }

    const approvedAsIs = this.records.filter((r) => r.review_action === "APPROVE_AS_IS" && !r.was_modified).length;
    const edited = this.records.filter((r) => r.was_modified || r.review_action === "EDIT_AND_SEND").length;
    const rejected = this.records.filter((r) => r.review_action === "REJECT_AND_REWRITE").length;

    const byCat: Record<string, { total: number; unmodified: number; edited: number; rejected: number }> = {};
    for (const r of this.records) {
      if (!byCat[r.category]) {
        byCat[r.category] = { total: 0, unmodified: 0, edited: 0, rejected: 0 };
      }
      byCat[r.category].total += 1;
      if (r.review_action === "APPROVE_AS_IS" && !r.was_modified) {
        byCat[r.category].unmodified += 1;
      } else if (r.was_modified || r.review_action === "EDIT_AND_SEND") {
        byCat[r.category].edited += 1;
      } else if (r.review_action === "REJECT_AND_REWRITE") {
        byCat[r.category].rejected += 1;
      }
    }

    return {
      total_reviews: total,
      unmodified_rate_percent: Math.round((approvedAsIs / total) * 1000) / 10,
      modified_rate_percent: Math.round((edited / total) * 1000) / 10,
      rejection_rate_percent: Math.round((rejected / total) * 1000) / 10,
      by_category: byCat
    };
  }
}
