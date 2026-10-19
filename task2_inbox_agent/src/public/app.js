/**
 * Frontend JavaScript for Inbox Agent Review Interface.
 */

let allEmails = [];
let currentEmailId = null;
let currentFilter = "ALL";

document.addEventListener("DOMContentLoaded", () => {
  loadEmails();
  setupEventListeners();
  checkKnowledgeBrainHealth();
});

async function checkKnowledgeBrainHealth() {
  const dot = document.getElementById("kb-status-dot");
  const text = document.getElementById("kb-status-text");
  try {
    const res = await fetch("http://127.0.0.1:8000/health");
    if (res.ok) {
      dot.className = "status-dot dot-green";
      text.textContent = "Knowledge Brain: Connected";
    } else {
      dot.className = "status-dot dot-orange";
      text.textContent = "Knowledge Brain: Degraded";
    }
  } catch {
    dot.className = "status-dot dot-orange";
    text.textContent = "Knowledge Brain: Offline (Simulated)";
  }
}

async function loadEmails() {
  const container = document.getElementById("email-list-container");
  try {
    const res = await fetch("/api/emails");
    const data = await res.json();
    allEmails = data.emails || [];
    renderEmailList();
  } catch (err) {
    container.innerHTML = `<div class="empty-state"><p>Error connecting to Inbox API: ${err.message}</p></div>`;
  }
}

function renderEmailList() {
  const container = document.getElementById("email-list-container");
  const search = document.getElementById("email-search").value.toLowerCase();

  const filtered = allEmails.filter((item) => {
    const matchesFilter = currentFilter === "ALL" || item.expected_category === currentFilter;
    const matchesSearch =
      item.subject.toLowerCase().includes(search) ||
      item.sender_name.toLowerCase().includes(search) ||
      item.body.toLowerCase().includes(search);
    return matchesFilter && matchesSearch;
  });

  if (filtered.length === 0) {
    container.innerHTML = `<div class="empty-state"><p>No emails match this filter.</p></div>`;
    return;
  }

  container.innerHTML = filtered
    .map((e) => {
      const isSelected = e.id === currentEmailId;
      const statusBadge = getStatusBadge(e.status);
      const categoryBadge = getCategoryBadge(e.expected_category);

      return `
      <div class="email-card ${isSelected ? "selected" : ""}" onclick="selectEmail('${e.id}')">
        <div class="card-top-row">
          <span class="card-sender">${escapeHtml(e.sender_name)}</span>
          <span class="card-time">${e.id}</span>
        </div>
        <div class="card-subject">${escapeHtml(e.subject)}</div>
        <div class="card-preview">${escapeHtml(e.body)}</div>
        <div class="card-badges">
          ${categoryBadge}
          ${statusBadge}
        </div>
      </div>
    `;
    })
    .join("");
}

function getCategoryBadge(cat) {
  if (!cat) return "";
  let cls = "badge-howto";
  if (cat === "Troubleshooting") cls = "badge-troubleshoot";
  if (cat === "Project request") cls = "badge-project";
  if (cat === "Refund or cancellation") cls = "badge-refund";
  if (cat === "Complaint") cls = "badge-complaint";
  if (cat === "Quote request") cls = "badge-quote";
  if (cat === "Follow-up") cls = "badge-followup";

  return `<span class="badge ${cls}">${cat}</span>`;
}

function getStatusBadge(status) {
  let cls = "badge-status-unprocessed";
  let label = "Unprocessed";

  if (status === "DRAFTED") {
    cls = "badge-status-drafted";
    label = "Draft Ready";
  } else if (status === "APPROVED") {
    cls = "badge-status-approved";
    label = "Approved & Sent";
  } else if (status === "EDITED_AND_SENT") {
    cls = "badge-status-edited";
    label = "Edited & Sent";
  } else if (status === "REJECTED") {
    cls = "badge-status-rejected";
    label = "Rejected";
  } else if (status === "ESCALATED") {
    cls = "badge-status-rejected";
    label = "Escalated";
  }

  return `<span class="badge ${cls}">${label}</span>`;
}

async function selectEmail(id) {
  currentEmailId = id;
  renderEmailList();

  const emptyView = document.getElementById("empty-state-view");
  const activeView = document.getElementById("active-email-view");
  emptyView.classList.add("hidden");
  activeView.classList.remove("hidden");

  const email = allEmails.find((e) => e.id === id);
  if (!email) return;

  // Populate Header
  document.getElementById("view-email-subject").textContent = email.subject;
  document.getElementById("view-email-sender").textContent = `${email.sender_name} <${email.sender_email}>`;
  document.getElementById("view-email-date").textContent = new Date(email.received_at).toLocaleDateString();

  document.getElementById("view-category-badge").outerHTML = getCategoryBadge(email.expected_category);
  document.getElementById("view-risk-badge").className = `badge ${email.expected_risk === "LOW" ? "badge-howto" : "badge-refund"}`;
  document.getElementById("view-risk-badge").textContent = email.expected_risk || "RISK";
  document.getElementById("view-status-badge").outerHTML = getStatusBadge(email.status);

  // Original Message
  document.getElementById("view-original-body").textContent = email.body;

  // Hide confirmation
  document.getElementById("sent-confirmation").classList.add("hidden");

  // Load or generate draft
  if (!email.has_draft) {
    await generateDraftForEmail(id);
  } else {
    displayDraft(email.draft);
  }
}

async function generateDraftForEmail(id) {
  const textarea = document.getElementById("draft-textarea");
  textarea.value = "Generating grounded draft using Knowledge Brain API...";

  try {
    const res = await fetch(`/api/emails/${id}/process`, { method: "POST" });
    const data = await res.json();
    if (data.success && data.email_state) {
      const idx = allEmails.findIndex((e) => e.id === id);
      if (idx !== -1) {
        allEmails[idx] = {
          ...allEmails[idx],
          status: data.email_state.status,
          has_draft: true,
          draft: data.email_state.draft,
          final_sent_reply: data.email_state.final_sent_reply
        };
      }
      displayDraft(data.email_state.draft);
      renderEmailList();
    }
  } catch (err) {
    textarea.value = `Error generating draft: ${err.message}`;
  }
}

function displayDraft(draft) {
  if (!draft) return;
  const textarea = document.getElementById("draft-textarea");
  textarea.value = draft.suggested_reply;

  document.getElementById("view-draft-confidence").textContent = `Confidence: ${Math.round(draft.confidence * 100)}%`;
  document.getElementById("view-next-action-hint").textContent = `Next Action: ${draft.suggested_next_action}`;
  document.getElementById("view-grounding-status").textContent = draft.grounding_status.toUpperCase();

  // Citations
  const citationsContainer = document.getElementById("citations-list");
  if (draft.citations && draft.citations.length > 0) {
    citationsContainer.innerHTML = draft.citations
      .map(
        (c) => `
        <div class="citation-item">
          <div class="citation-header">
            <a href="${c.url}" target="_blank" class="citation-link">${escapeHtml(c.title)}</a>
            <span class="citation-section">${escapeHtml(c.section || "Documentation")}</span>
          </div>
          <div class="citation-excerpt">${escapeHtml(c.excerpt || "")}</div>
        </div>
      `
      )
      .join("");
    document.getElementById("knowledge-evidence-card").classList.remove("hidden");
  } else {
    citationsContainer.innerHTML = `<div class="citation-item"><p class="citation-excerpt">No direct documentation citations needed for this operational request category.</p></div>`;
  }
}

async function submitReview(action) {
  if (!currentEmailId) return;

  const finalReply = document.getElementById("draft-textarea").value;
  const correctionReason = document.getElementById("correction-input").value;

  try {
    const res = await fetch(`/api/emails/${currentEmailId}/review`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        action,
        final_sent_reply: finalReply,
        correction_reason: correctionReason,
        reviewer_name: "Lead Support Engineer"
      })
    });

    const data = await res.json();
    if (data.success) {
      // Update email in memory
      const idx = allEmails.findIndex((e) => e.id === currentEmailId);
      if (idx !== -1) {
        allEmails[idx].status = data.email_state.status;
        allEmails[idx].final_sent_reply = data.email_state.final_sent_reply;
      }
      renderEmailList();

      // Show confirmation
      const banner = document.getElementById("sent-confirmation");
      document.getElementById("sent-confirm-title").textContent = `Review Recorded: ${action.replace(/_/g, " ")}`;
      document.getElementById("sent-confirm-desc").textContent = `Updated consecutive approvals to ${data.autonomy_status.consecutive_unmodified_approvals}/20.`;
      banner.classList.remove("hidden");
    }
  } catch (err) {
    alert(`Error submitting review: ${err.message}`);
  }
}

async function openAutonomyModal() {
  const modal = document.getElementById("autonomy-modal");
  const listContainer = document.getElementById("autonomy-categories-list");
  listContainer.innerHTML = "<p>Loading autonomy rule states...</p>";
  modal.classList.remove("hidden");

  try {
    const res = await fetch("/api/autonomy/status");
    const data = await res.json();
    const categories = data.categories || [];

    listContainer.innerHTML = categories
      .map((cat) => {
        const pct = Math.min((cat.consecutive_unmodified_approvals / 20) * 100, 100);
        const isBlocked = cat.hard_safety_gate_blocked;

        return `
        <div class="autonomy-item">
          <div class="autonomy-item-top">
            <span class="autonomy-item-title">${escapeHtml(cat.category)}</span>
            <span class="autonomy-counter-text">${cat.consecutive_unmodified_approvals}/20 Consecutive Approvals</span>
          </div>
          <div class="progress-bar-bg">
            <div class="progress-bar-fill" style="width: ${pct}%"></div>
          </div>
          ${
            isBlocked
              ? `<div class="autonomy-gate-badge">🔒 ${cat.safety_block_reason}</div>`
              : cat.is_eligible_for_autonomy_trial
              ? `<div class="status-text" style="color: #34d399">✨ Eligible for Autonomous Sending Trial!</div>`
              : `<div class="status-text" style="color: #94a3b8">Requires ${20 - cat.consecutive_unmodified_approvals} more consecutive unedited sends.</div>`
          }
        </div>
      `;
      })
      .join("");
  } catch (err) {
    listContainer.innerHTML = `<p>Error loading autonomy data: ${err.message}</p>`;
  }
}

function setupEventListeners() {
  // Filter chips
  document.querySelectorAll(".filter-chip").forEach((chip) => {
    chip.addEventListener("click", (e) => {
      document.querySelectorAll(".filter-chip").forEach((c) => c.classList.remove("active"));
      e.target.classList.add("active");
      currentFilter = e.target.getAttribute("data-filter");
      renderEmailList();
    });
  });

  // Search input
  document.getElementById("email-search").addEventListener("input", () => {
    renderEmailList();
  });

  // Action Buttons
  document.getElementById("btn-approve-as-is").addEventListener("click", () => submitReview("APPROVE_AS_IS"));
  document.getElementById("btn-edit-send").addEventListener("click", () => submitReview("EDIT_AND_SEND"));
  document.getElementById("btn-reject-rewrite").addEventListener("click", () => submitReview("REJECT_AND_REWRITE"));
  document.getElementById("btn-escalate-expert").addEventListener("click", () => submitReview("ESCALATE_TO_EXPERT"));

  document.getElementById("btn-generate-draft").addEventListener("click", () => {
    if (currentEmailId) generateDraftForEmail(currentEmailId);
  });

  // Batch process all
  document.getElementById("btn-process-all").addEventListener("click", async () => {
    const btn = document.getElementById("btn-process-all");
    btn.textContent = "Processing 50 emails...";
    btn.disabled = true;
    try {
      const res = await fetch("/api/emails/process-all", { method: "POST" });
      const data = await res.json();
      btn.textContent = `⚡ Drafted ${data.processed_count} Emails!`;
      await loadEmails();
    } catch {
      btn.textContent = "⚡ Batch Draft All";
    } finally {
      setTimeout(() => {
        btn.textContent = "⚡ Batch Draft All";
        btn.disabled = false;
      }, 3000);
    }
  });

  // Autonomy Modal
  document.getElementById("btn-view-autonomy").addEventListener("click", openAutonomyModal);
  document.getElementById("btn-close-modal").addEventListener("click", () => {
    document.getElementById("autonomy-modal").classList.add("hidden");
  });
}

function escapeHtml(str) {
  if (!str) return "";
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}
