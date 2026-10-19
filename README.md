# AI Tech Consultant — Enterprise Capstone System

An end-to-end, multi-agent AI system designed to help software and service businesses handle customer inquiries, automate customer email drafting with human approval & autonomy safeguards, and transform unstructured client discovery meetings into feasible Scopes of Work, 3-point estimates, and client proposals.

---

## 🏛️ System Architecture

The project is structured into three connected systems sharing a single foundational knowledge service:

```
                            ┌──────────────────────────────────────────────┐
                            │          Brilliant Directories Help          │
                            │  https://support.brilliantdirectories.com/   │
                            └──────────────────────┬───────────────────────┘
                                                   │
                                                   ▼
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│ Task 1: Knowledge Brain (Python / FastAPI)                                                       │
│ • Resumable Polite Crawler (Rate limiting, retries, checkpoint manifest, content hash diffing)   │
│ • Multimodal Image & Screenshot Processor (Interface labels, settings paths, button names)      │
│ • Heading-Aware Chunker (Preserves procedures, tables, and screenshot context)                   │
│ • Hybrid Retriever (Dense vector cosine similarity + BM25 keyword matching + RRF fusion)         │
│ • Grounded QA Engine (Verifiable citations, insufficient evidence detection, injection defense) │
│ • Human Expert Escalation & Versioned Knowledge Feedback Store                                   │
│ • Daily Sitemap Freshness Background Scheduler                                                   │
│                                                                                                  │
│   Endpoints: POST /query | POST /ingestion/run | GET /ingestion/status | POST /escalations       │
└───────────────────────────────────┬───────────────────────────────────┬──────────────────────────┘
                                    │                                   │
             HTTP REST API (/query) │                                   │ HTTP REST API (/query)
                                    ▼                                   ▼
┌──────────────────────────────────────────┐    ┌──────────────────────────────────────────────────┐
│ Task 2: Inbox Agent (TypeScript / Node)  │    │ Task 3: Meeting to Scope (Python Multi-Agent)    │
│ • 7-Category Intent & Risk Classifier    │    │ • Transcript Analyst (Long dialogue windowing)   │
│ • Grounded Response Drafting Agent       │    │ • Feasibility Agent (Queries Task 1 Knowledge)   │
│ • Safety & Policy Guardrail Validator    │    │ • Scope Agent (Deliverables, exclusions, criteria│
│ • 20-Approval Autonomy Engine            │    │ • Estimation Agent (3-point low/likely/high hrs) │
│ • Versioned Feedback Learning Store      │    │ • Proposal Agent (Milestones, pricing breakdown) │
│ • Modern Web Human Review Interface      │    │ • Scope Comparison Agent (Meeting C Delta Report)│
│ • 50 Realistic Customer Emails Dataset   │    │ • 3 Comprehensive Meeting Transcripts (A, B, C)  │
└──────────────────────────────────────────┘    └──────────────────────────────────────────────────┘
```

> **Critical Architectural Rule Adhered To**: Tasks 2 and 3 consume Task 1 strictly through its documented HTTP API (`POST /query`). Neither downstream application duplicates Task 1's retrieval or parsing logic, making the knowledge service fully reusable for any enterprise business.

---

## 📂 Project Organization

```
ai_tech_consultant/
├── .env.example                               # Environment template (Anthropic/OpenAI keys optional)
├── .env                                       # Local environment configuration
├── README.md                                  # Executive documentation
├── start_all.py                               # Unified one-click runner for Task 1 & Task 2
│
├── task1_knowledge_brain/                     # Task 1: Shared Foundational Knowledge Service (Python)
│   ├── requirements.txt                       # Python dependencies
│   ├── crawler/
│   │   ├── sitemap_parser.py                  # Sitemap XML downloader, URL deduplicator, manifest diff
│   │   ├── polite_crawler.py                  # Polite crawler with exponential backoff & checkpoints
│   │   ├── article_parser.py                  # HTML extractor (headings, tables, steps, image context)
│   │   └── multimodal_processor.py            # Screenshot analyzer & UI label extractor
│   ├── rag/
│   │   ├── chunker.py                         # Heading-based chunker with procedural coherence
│   │   ├── embeddings.py                      # 128-dim dense semantic embeddings engine
│   │   ├── vector_store.py                    # Vector store with cosine similarity index
│   │   ├── hybrid_retriever.py                # BM25 + Dense vector Reciprocal Rank Fusion
│   │   └── grounded_qa.py                     # Grounded QA, citation attribution, injection defense
│   ├── storage/
│   │   ├── manifest.json                      # Ingestion manifest & state tracking
│   │   ├── escalations.db                     # SQLite escalation & expert knowledge store
│   │   ├── seed_knowledge.py                  # Authoritative Brilliant Directories seed knowledge
│   │   └── articles/                          # Cached article JSON records
│   ├── api/
│   │   ├── app.py                             # FastAPI server (query, ingestion, escalations, health)
│   │   ├── schemas.py                         # Pydantic contract schemas
│   │   └── scheduler.py                       # Daily automated sitemap diff scheduler
│   ├── tests/
│   │   └── test_rag_and_api.py                # Pytest unit & integration test suite (7/7 Passed)
│   └── evaluation/
│       ├── eval_dataset.json                  # 22 diverse evaluation test cases
│       └── run_evaluation.py                  # Evaluation runner (22/22 Passed, 100%)
│
├── task2_inbox_agent/                         # Task 2: Customer Email Inbox Agent (TypeScript)
│   ├── package.json                           # Node.js dependencies
│   ├── tsconfig.json                          # TypeScript configuration
│   ├── src/
│   │   ├── types/email.ts                     # Strict TypeScript interfaces & data types
│   │   ├── client/knowledgeBrainClient.ts     # Typed client consuming Task 1 API
│   │   ├── pipeline/
│   │   │   ├── classifier.ts                  # 7-Category intent & risk classifier
│   │   │   ├── validator.ts                   # Financial & commercial guardrail validator
│   │   │   ├── draftingAgent.ts               # Grounded response drafting engine
│   │   │   └── autonomyRule.ts                # 20-consecutive-approval autonomy engine
│   │   ├── storage/
│   │   │   ├── dataset.json                   # 50 realistic customer emails with ground truth
│   │   │   └── feedbackStore.ts               # Versioned human review feedback audit store
│   │   ├── server.ts                          # Express backend & API endpoints
│   │   └── public/                            # Modern Web Review Interface
│   │       ├── index.html                     # Responsive human review inbox layout
│   │       ├── style.css                      # Modern dark slate UI with glassmorphism
│   │       └── app.js                         # Dynamic state, citation display, review actions
│   └── tests/
│       └── run_evaluation.ts                  # Evaluation suite (28/28 Passed, 100%)
│
└── task3_meeting_to_scope/                    # Task 3: Meeting to Scope of Work (Python Multi-Agent)
    ├── requirements.txt                       # Python dependencies
    ├── models/schemas.py                      # Pydantic schemas (Requirements, Feasibility, Scope, Estimates)
    ├── transcripts/
    │   ├── meeting_a_website_improvements.txt # Client discovery dialogue: Search, radius, mobile
    │   ├── meeting_b_ecommerce_workflow.txt   # Client discovery dialogue: Stripe, PayPal, trial billing
    │   └── meeting_c_followup_and_changes.txt # Client follow-up dialogue: AI search, polygon map, 4-week deadline
    ├── agents/
    │   ├── transcript_analyst.py              # Dialogue windowing & structured requirement extraction
    │   ├── feasibility_agent.py               # Feature feasibility checker (queries Task 1 API)
    │   ├── scope_agent.py                     # Scope of Work compiler (exclusions, deliverables, criteria)
    │   ├── estimation_agent.py                # 3-point estimation engine (low, likely, high hours)
    │   ├── proposal_agent.py                  # Client proposal generator (milestones, configurable rates)
    │   └── comparison_agent.py                # Scope Creep & Delta Agent (Meeting C vs Meeting A)
    ├── orchestrator.py                        # Master pipeline orchestrator
    ├── tests/test_orchestrator.py             # Pytest unit tests (4/4 Passed)
    ├── outputs/                               # Generated Scopes, Proposals, and Change Reports
    └── evaluation/run_evaluation.py           # Evaluation runner (6/6 Passed, 100%)
```

---

## ⚡ Quick Start & Running Locally

### 1. Prerequisites
- Python 3.10+
- Node.js v18+ & npm

### 2. Launch All Services (One Command)
Run the master launcher:
```bash
python start_all.py
```
This automatically boots:
- **Task 1 Knowledge Brain API**: `http://127.0.0.1:8000` (API Docs at `http://127.0.0.1:8000/docs`)
- **Task 2 Inbox Agent Web Interface**: `http://localhost:3000`

---

## 🧪 Comprehensive Evaluation Results

Each task includes an automated evaluation suite testing accuracy, safety guardrails, and compliance:

### Task 1: Knowledge Brain
Run the evaluation:
```bash
python -m task1_knowledge_brain.evaluation.run_evaluation
```
- **Test Cases**: 22 diverse test queries (Feature lookups, billing, Google Maps, domain setup, multimodal screenshot labels, prompt injections, and unsupported questions).
- **Pass Rate**: **100.0% (22/22 Passed)**
- **Average Query Latency**: **1.6ms**
- **Safety**: Prompt injection attempts (`TC-19`) rejected immediately; unsupported questions (`TC-20`, `TC-21`, `TC-22`) flagged as `status: "insufficient_evidence"` and routed to human expert escalation.
- **Unit Tests**: `python -m pytest task1_knowledge_brain/tests/test_rag_and_api.py -v` (**7/7 Passed**).

### Task 2: Inbox Agent
Run the evaluation:
```bash
cd task2_inbox_agent
npx tsx tests/run_evaluation.ts
```
- **Test Cases**: 28 test cases across all 7 email categories, risk detection, guardrail validation, 20-approval counter mechanics, and feedback metrics.
- **Pass Rate**: **100.0% (28/28 Passed)**
- **Guardrail Enforcement**: Unauthorized refund commitments and arbitrary pricing quotes are blocked and sanitized with mandatory human review.
- **Autonomy Safety Gate**: High-risk categories (`Refund or cancellation`, `Complaint`, `Quote request`) are hard-blocked from autonomous sending even after 20 approvals.
- **Build**: `npm run build` (**TypeScript compiles with 0 errors**).

### Task 3: Meeting to Scope of Work
Run the evaluation:
```bash
python -m task3_meeting_to_scope.evaluation.run_evaluation
```
- **Test Cases**: 6 end-to-end orchestration tests covering Meeting A, Meeting B, Meeting C Delta, Feasibility Checking, 3-Point Estimation Math, and Change Order generation.
- **Pass Rate**: **100.0% (6/6 Passed)**
- **Feasibility Verification**: Correctly identifies native platform configurations (Google Maps, Stripe, privacy toggles) vs custom development (AI natural language search, polygon drawing).
- **Scope Comparison**: Successfully detects 2 Added requirements, 1 Removed requirement, flags Out-of-Scope warnings, and computes net hour delta (`+42.0h`).
- **Unit Tests**: `python -m pytest task3_meeting_to_scope/tests/test_orchestrator.py -v` (**4/4 Passed**).

---

## 🔍 Task-by-Task Details

### Task 1: Knowledge Brain
- **Polite Crawler**: Rate limits requests (`0.5s` delay), retries transient errors with exponential backoff (up to 3 attempts), isolates failures, checkpoints status in `storage/manifest.json`, and diffs content hashes (SHA-256) to reprocess only changed pages. Tested live against `https://support.brilliantdirectories.com/support/sitemap.xml` (1,540 URLs indexed).
- **Multimodal Understanding**: Preserves immediate paragraph and procedural context around screenshots, extracting visible interface labels, navigation paths (`Settings > General Settings`), and form buttons. Supports Claude 3.5 Sonnet Vision when `ANTHROPIC_API_KEY` is set.
- **Hybrid Search**: Combines 128-dimensional dense semantic vectors with BM25 keyword matching via Reciprocal Rank Fusion (RRF), with visual label matching boosts.
- **Human Escalation Workflow**: Unanswered or low-confidence questions trigger `POST /escalations`. When an expert resolves an escalation (`POST /escalations/{id}/resolve`), the answer is stored in a versioned SQLite database and dynamically re-indexed into the vector store for immediate retrieval.

### Task 2: Inbox Agent
- **50 Customer Emails**: Balanced dataset across 7 categories:
  - 12 How-to questions
  - 10 Troubleshooting inquiries
  - 6 Project requests
  - 6 Refund or cancellation requests
  - 6 Complaints
  - 5 Quote requests
  - 5 Follow-ups
- **20-Consecutive-Approval Autonomy Rule**:
  - Compares generated draft against final sent text using normalized character string diff.
  - Exactly 20 consecutive unmodified approved drafts required for a category to become eligible for an autonomy trial.
  - Any edit or rejection resets the streak counter to 0.
  - Hard safety policy permanently bars financial, refund, complaint, and commercial quote requests from autonomy.
- **Feedback Learning Store**: Logs original draft, human modifications, character diff, review action, and reviewer feedback reason to `feedback_store.json` for quality trend analysis.
- **Interactive Web Interface**: Clean, responsive review screen featuring email search, category filters, citation previews, editable drafts, approval buttons, and real-time autonomy progress bars.

### Task 3: Meeting to Scope of Work
- **6-Agent Architecture**:
  1. `Transcript Analyst`: Ingests multi-speaker dialogue and extracts structured requirements (`REQ-001...`).
  2. `Product Feasibility Agent`: Calls Task 1 Knowledge Brain API (`POST /query`) to categorize each requirement as `existing_configuration`, `existing_feature_with_limitation`, or `potential_custom_development`.
  3. `Scope Agent`: Synthesizes objective, agreed requirements, deliverables, explicit exclusions, and acceptance criteria.
  4. `Estimation Agent`: Produces 3-point estimates (Low, Likely, High hours) with uncertainty levels.
  5. `Proposal Agent`: Generates executive proposals with milestone schedules and configurable hourly rates (default `$120/hr`).
  6. `Scope Comparison Agent`: Compares follow-up Meeting C against Meeting A, identifies Added, Modified, and Removed requirements, flags scope creep, and recommends formal Change Orders.
- **Transcripts Tested**:
  - `Meeting A`: Alex Rivers (DirectoryHub) — Website improvements, search radius, mobile speed.
  - `Meeting B`: Elena Rostova (Sensepass Retail) — Stripe/PayPal embedded checkout, 14-day free trial auto-renew, webhook ERP sync.
  - `Meeting C`: Alex Rivers (DirectoryHub) — Follow-up adding AI natural language search, polygon boundary drawing, removing HubSpot webhooks, and compressing deadline to 4 weeks.

---

## 🛡️ Security & Reliability Controls
1. **Prompt Injection Defense**: Sanitizes user queries and customer emails against instruction overrides, jailbreak attempts, and system prompt leakage.
2. **Untrusted Input Isolation**: Customer emails and meeting transcripts are strictly parsed as data payloads, never executed as instruction directives.
3. **Graceful Fallbacks**: If external API keys are omitted, the entire system operates seamlessly with its built-in high-fidelity local dense embedding and deterministic reasoning engines.
4. **Audit Trail**: Every draft, edit diff, and escalation resolution is timestamped and persisted for complete operational accountability.


---

## 🚀 Cloud Deployment Guide

The repository includes ready-to-deploy configurations for **Render**, **Railway**, and **Docker**.

### 1. Deploy on Render (Recommended - Free Tier)
1. Go to [Render Dashboard](https://dashboard.render.com/) and click **New +** -> **Blueprint**.
2. Connect your GitHub repository: Mukesh77-code/ai_tech_consultant.
3. Render will automatically detect 
ender.yaml and provision the containerized web service.
4. Click **Apply**. Once built, Render provides a public HTTPS URL (e.g., https://ai-tech-consultant.onrender.com).

### 2. Deploy on Railway
1. Go to [Railway Dashboard](https://railway.app/) and click **New Project** -> **Deploy from GitHub repo**.
2. Select Mukesh77-code/ai_tech_consultant.
3. Railway automatically detects 
ailway.json and Dockerfile, builds the image, and deploys.
4. Under **Settings > Networking**, click **Generate Domain** to get your public URL.

### 3. Local Docker Compose
To build and run the multi-service container locally:
`ash
docker-compose up --build
`
- Inbox Agent Web UI: http://localhost:3000
- Knowledge Brain API Docs: http://localhost:8000/docs
