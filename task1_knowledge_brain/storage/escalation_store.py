"""
Escalation and Expert Knowledge Store for Knowledge Brain.
Persists unanswered questions, human expert tasks, and versioned expert knowledge.
Automatically re-indexes approved expert answers into retrieval.
"""

import json
import logging
import os
import sqlite3
import uuid
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class EscalationStore:
    def __init__(self, db_path: str = "task1_knowledge_brain/storage/escalations.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS escalations (
                    id TEXT PRIMARY KEY,
                    question TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    evidence_snippets TEXT,
                    status TEXT NOT NULL DEFAULT 'PENDING',
                    expert_answer TEXT,
                    expert_notes TEXT,
                    created_at TEXT NOT NULL,
                    resolved_at TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS expert_knowledge (
                    id TEXT PRIMARY KEY,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    version INTEGER NOT NULL DEFAULT 1,
                    source_reference TEXT,
                    approved_by TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            conn.commit()

    def create_escalation(
        self,
        question: str,
        reason: str,
        evidence_snippets: Optional[List[str]] = None
    ) -> str:
        esc_id = f"ESC-{str(uuid.uuid4())[:8].upper()}"
        now = datetime.utcnow().isoformat() + "Z"
        snippets_json = json.dumps(evidence_snippets or [], ensure_ascii=False)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO escalations (id, question, reason, evidence_snippets, status, created_at)
                VALUES (?, ?, ?, ?, 'PENDING', ?)
                """,
                (esc_id, question, reason, snippets_json, now)
            )
            conn.commit()
        logger.info(f"Created escalation task {esc_id} for question: '{question[:60]}'")
        return esc_id

    def list_escalations(self, status: Optional[str] = None) -> List[dict]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if status:
                cursor.execute("SELECT * FROM escalations WHERE status = ? ORDER BY created_at DESC", (status,))
            else:
                cursor.execute("SELECT * FROM escalations ORDER BY created_at DESC")
            rows = cursor.fetchall()
            results = []
            for r in rows:
                results.append({
                    "id": r["id"],
                    "question": r["question"],
                    "reason": r["reason"],
                    "evidence_snippets": json.loads(r["evidence_snippets"] or "[]"),
                    "status": r["status"],
                    "expert_answer": r["expert_answer"],
                    "created_at": r["created_at"],
                    "resolved_at": r["resolved_at"]
                })
            return results

    def resolve_escalation(
        self,
        escalation_id: str,
        expert_answer: str,
        expert_notes: Optional[str] = None,
        approved_by: str = "Senior Support Engineer"
    ) -> dict:
        now = datetime.utcnow().isoformat() + "Z"
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM escalations WHERE id = ?", (escalation_id,))
            row = cursor.fetchone()
            if not row:
                raise ValueError(f"Escalation {escalation_id} not found")

            question = row["question"]

            # Update escalation status
            cursor.execute(
                """
                UPDATE escalations
                SET status = 'RESOLVED', expert_answer = ?, expert_notes = ?, resolved_at = ?
                WHERE id = ?
                """,
                (expert_answer, expert_notes, now, escalation_id)
            )

            # Insert into expert_knowledge versioned records
            ek_id = f"EK-{str(uuid.uuid4())[:8].upper()}"
            cursor.execute(
                """
                INSERT INTO expert_knowledge (id, question, answer, version, source_reference, approved_by, created_at)
                VALUES (?, ?, ?, 1, ?, ?, ?)
                """,
                (ek_id, question, expert_answer, f"Escalation:{escalation_id}", approved_by, now)
            )
            conn.commit()

        logger.info(f"Resolved escalation {escalation_id} with approved answer.")
        return {
            "status": "RESOLVED",
            "escalation_id": escalation_id,
            "expert_knowledge_id": ek_id,
            "question": question,
            "expert_answer": expert_answer,
            "resolved_at": now
        }
