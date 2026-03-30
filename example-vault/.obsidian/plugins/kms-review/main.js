/*
 * KMS Review Queue Plugin for Obsidian
 *
 * Features:
 * - Sidebar control panel with stats + action buttons
 * - Interactive review widgets for ```kms-review code blocks
 * - Command palette: Refresh, Apply, Bulk approve/reject, Retriage
 * - Search proposals → navigate to proposal in review-queue or open source
 * - Proposal detail modal (SQLite data)
 * - Revert applied decisions
 */

const { Plugin, Modal, Notice, MarkdownView, ItemView } = require("obsidian");
const { exec } = require("child_process");
const path = require("path");

const REVIEW_QUEUE_FILENAME = "00_Admin/review-queue.md";
const DASHBOARD_FILENAME = "00_Admin/dashboard.md";
const KMS_BEGIN = "<!-- kms:begin -->";
const KMS_END = "<!-- kms:end -->";
const PANEL_VIEW_TYPE = "kms-panel";

module.exports = class KmsReviewPlugin extends Plugin {
  async onload() {
    // ── Sidebar panel view ──
    this.registerView(PANEL_VIEW_TYPE, (leaf) => new KmsPanelView(leaf, this));

    // ── Code block processor ──
    this.registerMarkdownCodeBlockProcessor("kms-review", (source, el, ctx) => {
      this._renderReviewBlock(source, el, ctx);
    });

    // ── Commands ──
    this.addCommand({
      id: "open-panel",
      name: "Open control panel",
      callback: () => this._activatePanel(),
    });

    this.addCommand({
      id: "open-review-queue",
      name: "Open review queue",
      callback: () => this._openFile(REVIEW_QUEUE_FILENAME),
    });

    this.addCommand({
      id: "open-dashboard",
      name: "Open dashboard",
      callback: () => this._openFile(DASHBOARD_FILENAME),
    });

    this.addCommand({
      id: "refresh-review-queue",
      name: "Refresh review queue (scan + AI summaries + dashboard)",
      callback: () => this._runPipeline("refresh"),
    });

    this.addCommand({
      id: "apply-decisions",
      name: "Apply decisions (move approved files)",
      callback: () => this._runPipeline("apply"),
    });

    this.addCommand({
      id: "retriage-all",
      name: "Retriage all proposals (re-classify domains/topics via LLM)",
      callback: () => this._runPipeline("retriage"),
    });

    this.addCommand({
      id: "approve-all-pending",
      name: "Approve all pending proposals",
      callback: () => this._bulkDecision("approve"),
    });

    this.addCommand({
      id: "reject-all-pending",
      name: "Reject all pending proposals",
      callback: () => this._bulkDecision("reject"),
    });

    this.addCommand({
      id: "search-proposals",
      name: "Search proposals",
      callback: () => new KmsSearchModal(this.app, this).open(),
    });

    this.addCommand({
      id: "revert-proposal",
      name: "Revert applied proposal (enter proposal ID)",
      callback: () => new KmsRevertModal(this.app, this).open(),
    });

    this.addCommand({
      id: "revert-batch",
      name: "Revert batch (undo entire bulk operation)",
      callback: () => new KmsBatchRevertModal(this.app, this).open(),
    });

    // ── Ribbon → opens panel ──
    this.addRibbonIcon("layout-dashboard", "KMS Control Panel", () => {
      this._activatePanel();
    });

    console.log("KMS Review plugin loaded");
  }

  onunload() {
    this.app.workspace.detachLeavesOfType(PANEL_VIEW_TYPE);
    console.log("KMS Review plugin unloaded");
  }

  // ════════════════════════════════════════════════
  // Sidebar panel activation
  // ════════════════════════════════════════════════

  async _activatePanel() {
    const existing = this.app.workspace.getLeavesOfType(PANEL_VIEW_TYPE);
    if (existing.length) {
      this.app.workspace.revealLeaf(existing[0]);
      return;
    }
    const leaf = this.app.workspace.getRightLeaf(false);
    await leaf.setViewState({ type: PANEL_VIEW_TYPE, active: true });
    this.app.workspace.revealLeaf(leaf);
  }

  _refreshPanel() {
    for (const leaf of this.app.workspace.getLeavesOfType(PANEL_VIEW_TYPE)) {
      if (leaf.view instanceof KmsPanelView) {
        leaf.view.refresh();
      }
    }
  }

  // ════════════════════════════════════════════════
  // Pipeline commands (run Python scripts)
  // ════════════════════════════════════════════════

  _getProjectRoot() {
    const vaultPath = this.app.vault.adapter.basePath;
    return path.dirname(vaultPath);
  }

  _getPython() {
    return path.join(this._getProjectRoot(), ".venv", "bin", "python");
  }

  async _runPipeline(mode) {
    const projectRoot = this._getProjectRoot();
    const python = this._getPython();

    const pipelines = {
      refresh: [
        { cmd: `"${python}" -m kms.scripts.scan_inbox`, label: "Scanning inbox" },
        { cmd: `"${python}" -m kms.scripts.make_review_queue --ai-summary`, label: "Generating review queue (AI)" },
        { cmd: `"${python}" -m kms.scripts.generate_dashboard`, label: "Updating dashboard" },
      ],
      apply: [
        { cmd: `"${python}" -m kms.scripts.apply_decisions`, label: "Applying decisions" },
        { cmd: `"${python}" -m kms.scripts.make_review_queue`, label: "Refreshing queue" },
        { cmd: `"${python}" -m kms.scripts.generate_dashboard`, label: "Updating dashboard" },
      ],
      retriage: [
        { cmd: `"${python}" -m kms.scripts.make_review_queue --retriage --ai-summary`, label: "Re-classifying all proposals (LLM)" },
        { cmd: `"${python}" -m kms.scripts.generate_dashboard`, label: "Updating dashboard" },
      ],
    };

    const steps = pipelines[mode];
    if (!steps) return;

    const notice = new Notice(`KMS: Starting ${mode}...`, 0);

    for (const step of steps) {
      try {
        notice.setMessage(`KMS: ${step.label}...`);
        await this._exec(step.cmd, projectRoot);
      } catch (err) {
        notice.hide();
        new Notice(`KMS Error: ${step.label} failed.\n${err.message}`, 10000);
        console.error("KMS pipeline error:", err);
        this._refreshPanel();
        return;
      }
    }

    notice.hide();
    new Notice(`KMS: ${mode} complete!`, 5000);
    this._reloadKmsViews();
    this._refreshPanel();
  }

  _exec(cmd, cwd) {
    return new Promise((resolve, reject) => {
      exec(
        cmd,
        {
          cwd: cwd || this._getProjectRoot(),
          timeout: 600000,
          env: { ...process.env, PYTHONPATH: cwd || this._getProjectRoot() },
        },
        (error, stdout, stderr) => {
          if (error) {
            const msg = stderr?.trim() || stdout?.trim() || error.message;
            reject(new Error(msg.slice(-500)));
          } else {
            resolve(stdout);
          }
        }
      );
    });
  }

  _reloadKmsViews() {
    this.app.workspace.iterateAllLeaves((leaf) => {
      const fp = leaf.view?.file?.path;
      if (fp === REVIEW_QUEUE_FILENAME || fp === DASHBOARD_FILENAME) {
        leaf.rebuildView();
      }
    });
  }

  // ════════════════════════════════════════════════
  // Navigate to proposal # in review-queue.md
  // ════════════════════════════════════════════════

  async _scrollToProposal(proposalId) {
    const file = this.app.vault.getAbstractFileByPath(REVIEW_QUEUE_FILENAME);
    if (!file) {
      new Notice("review-queue.md not found.");
      return;
    }
    const leaf = await this.app.workspace.getLeaf(false);
    await leaf.openFile(file);

    const content = await this.app.vault.read(file);
    const lines = content.split("\n");
    const needle = `proposal_id: ${proposalId}`;
    let targetLine = -1;
    for (let i = 0; i < lines.length; i++) {
      if (lines[i].includes(needle)) {
        for (let j = i; j >= Math.max(0, i - 5); j--) {
          if (lines[j].includes(KMS_BEGIN)) { targetLine = j; break; }
        }
        if (targetLine === -1) targetLine = i;
        break;
      }
    }

    if (targetLine >= 0) {
      const view = leaf.view;
      if (view instanceof MarkdownView && view.editor) {
        view.editor.setCursor({ line: targetLine, ch: 0 });
        view.editor.scrollIntoView(
          { from: { line: targetLine, ch: 0 }, to: { line: targetLine + 20, ch: 0 } },
          true
        );
      }
    }
  }

  // ════════════════════════════════════════════════
  // Bulk operations
  // ════════════════════════════════════════════════

  async _bulkDecision(decision) {
    const file = this.app.vault.getAbstractFileByPath(REVIEW_QUEUE_FILENAME);
    if (!file) {
      new Notice("review-queue.md not found.");
      return;
    }

    let content = await this.app.vault.read(file);
    const blocks = this._splitKmsBlocks(content);
    let count = 0;

    for (const block of blocks) {
      if (!block.isKms) continue;
      const currentDecision = block.text.match(/decision:\s*(\S+)/);
      if (!currentDecision || currentDecision[1] !== "pending") continue;

      const fieldRegex = /^(decision:\s*)(.*)$/m;
      if (fieldRegex.test(block.text)) {
        block.text = block.text.replace(fieldRegex, `$1${decision}`);
        count++;
      }
    }

    if (count === 0) {
      new Notice("No pending proposals to change.");
      return;
    }

    const newContent = blocks.map((b) => b.text).join("");
    await this.app.vault.modify(file, newContent);
    new Notice(`${count} proposals set to ${decision}.`);
    this._reloadKmsViews();
    this._refreshPanel();
  }

  // ════════════════════════════════════════════════
  // File helpers
  // ════════════════════════════════════════════════

  async _openFile(filePath) {
    const file = this.app.vault.getAbstractFileByPath(filePath);
    if (file) {
      await this.app.workspace.openLinkText(file.path, "", false);
    } else {
      new Notice(`${filePath} not found. Run pipeline first.`);
    }
  }

  // ════════════════════════════════════════════════
  // Review block rendering
  // ════════════════════════════════════════════════

  async _renderReviewBlock(source, el, ctx) {
    const parsed = this._parseYaml(source);
    if (!parsed.proposal_id) {
      el.createEl("pre", { text: source });
      return;
    }

    const container = el.createDiv({
      cls: `kms-review-block kms-decision-${parsed.decision}`,
    });
    container.dataset.proposalId = parsed.proposal_id;

    const header = container.createDiv({ cls: "kms-review-header" });
    const titleEl = header.createSpan({
      cls: "kms-review-title kms-clickable",
      text: `Proposal #${parsed.proposal_id}`,
    });
    titleEl.addEventListener("click", () => {
      new KmsDetailModal(this.app, this, parsed.proposal_id).open();
    });
    titleEl.title = "Click to view details";

    const badge = header.createSpan({
      cls: "kms-review-badge",
      text: parsed.decision.toUpperCase(),
    });

    const btnRow = container.createDiv({ cls: "kms-decision-buttons" });
    for (const d of [
      { value: "approve", label: "Approve" },
      { value: "reject", label: "Reject" },
      { value: "postpone", label: "Postpone" },
    ]) {
      const btn = btnRow.createEl("button", {
        cls: `kms-decision-btn${parsed.decision === d.value ? ` active-${d.value}` : ""}`,
        text: d.label,
      });
      btn.addEventListener("click", async () => {
        btnRow.querySelectorAll(".kms-decision-btn").forEach((b) => (b.className = "kms-decision-btn"));
        btn.className = `kms-decision-btn active-${d.value}`;
        container.className = `kms-review-block kms-decision-${d.value}`;
        badge.textContent = d.value.toUpperCase();
        await this._updateField(ctx.sourcePath, parsed.proposal_id, "decision", d.value);
        new Notice(`Proposal #${parsed.proposal_id}: ${d.value}`);
      });
    }

    const noteInput = container.createEl("input", {
      cls: "kms-review-note-input",
      type: "text",
      placeholder: "Review note (optional)...",
      value: parsed.review_note || "",
    });
    let debounceTimer;
    noteInput.addEventListener("input", () => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(async () => {
        await this._updateField(ctx.sourcePath, parsed.proposal_id, "review_note", noteInput.value);
      }, 800);
    });
  }

  _parseYaml(text) {
    const get = (key) => {
      const match = text.match(new RegExp(`^${key}:\\s*(.*)$`, "m"));
      if (!match) return "";
      let val = match[1].trim();
      if ((val.startsWith("'") && val.endsWith("'")) || (val.startsWith('"') && val.endsWith('"'))) {
        val = val.slice(1, -1);
      }
      if (val === "null" || val === "~") return "";
      return val;
    };
    return {
      proposal_id: get("proposal_id"),
      item_id: get("item_id"),
      decision: get("decision") || "pending",
      reviewer: get("reviewer"),
      override_target: get("override_target"),
      review_note: get("review_note"),
    };
  }

  // ════════════════════════════════════════════════
  // File mutation (write decisions back)
  // ════════════════════════════════════════════════

  async _updateField(filePath, proposalId, fieldName, value) {
    const file = this.app.vault.getAbstractFileByPath(filePath);
    if (!file) return;

    let content = await this.app.vault.read(file);
    const blocks = this._splitKmsBlocks(content);
    let modified = false;

    for (const block of blocks) {
      if (!block.isKms) continue;
      const pidMatch = block.text.match(/proposal_id:\s*(\d+)/);
      if (!pidMatch || pidMatch[1] !== String(proposalId)) continue;

      const fieldRegex = new RegExp(`^(${fieldName}:\\s*)(.*)$`, "m");
      const quoted = typeof value === "string" && value.includes(" ") ? `'${value}'` : value || "''";

      if (fieldRegex.test(block.text)) {
        block.text = block.text.replace(fieldRegex, `$1${quoted}`);
        modified = true;
      }
    }

    if (modified) {
      const newContent = blocks.map((b) => b.text).join("");
      await this.app.vault.modify(file, newContent);
    }
  }

  _splitKmsBlocks(content) {
    const parts = [];
    let remaining = content;
    while (remaining.length > 0) {
      const beginIdx = remaining.indexOf(KMS_BEGIN);
      if (beginIdx === -1) { parts.push({ isKms: false, text: remaining }); break; }
      if (beginIdx > 0) parts.push({ isKms: false, text: remaining.substring(0, beginIdx) });
      const endIdx = remaining.indexOf(KMS_END, beginIdx);
      if (endIdx === -1) { parts.push({ isKms: true, text: remaining.substring(beginIdx) }); break; }
      const blockEnd = endIdx + KMS_END.length;
      parts.push({ isKms: true, text: remaining.substring(beginIdx, blockEnd) });
      remaining = remaining.substring(blockEnd);
    }
    return parts;
  }
};

// ════════════════════════════════════════════════════════════════
// Sidebar Panel View
// ════════════════════════════════════════════════════════════════

class KmsPanelView extends ItemView {
  constructor(leaf, plugin) {
    super(leaf);
    this.plugin = plugin;
  }

  getViewType() { return PANEL_VIEW_TYPE; }
  getDisplayText() { return "KMS"; }
  getIcon() { return "layout-dashboard"; }

  async onOpen() {
    this.containerEl.empty();
    const root = this.containerEl.createDiv({ cls: "kms-panel" });
    this.panelRoot = root;
    await this._render(root);
  }

  async refresh() {
    if (!this.panelRoot) return;
    this.panelRoot.empty();
    await this._render(this.panelRoot);
  }

  async _render(root) {
    // ── Header ──
    root.createEl("h4", { cls: "kms-panel-title", text: "KMS Control Panel" });

    // ── Stats (loaded from dashboard script output) ──
    const statsEl = root.createDiv({ cls: "kms-panel-stats" });
    statsEl.createEl("p", { cls: "kms-search-loading", text: "Loading stats..." });

    this._loadStats(statsEl);

    // ── Action buttons ──
    const section = (title) => {
      const s = root.createDiv({ cls: "kms-panel-section" });
      s.createEl("div", { cls: "kms-panel-section-title", text: title });
      return s;
    };

    // Pipeline
    const pipeSection = section("Pipeline");
    this._actionBtn(pipeSection, "Refresh queue", "rotate-cw", "Scan inbox + AI summaries + dashboard", () => this.plugin._runPipeline("refresh"));
    this._actionBtn(pipeSection, "Apply decisions", "check-circle", "Move approved files to targets", () => this.plugin._runPipeline("apply"));
    this._actionBtn(pipeSection, "Retriage all", "wand", "Re-classify domains/topics via LLM", () => this.plugin._runPipeline("retriage"));

    // Bulk
    const bulkSection = section("Bulk actions");
    this._actionBtn(bulkSection, "Approve all pending", "check", "", () => this.plugin._bulkDecision("approve"));
    this._actionBtn(bulkSection, "Reject all pending", "x", "", () => this.plugin._bulkDecision("reject"));

    // Navigate
    const navSection = section("Navigate");
    this._actionBtn(navSection, "Review queue", "file-text", "", () => this.plugin._openFile(REVIEW_QUEUE_FILENAME));
    this._actionBtn(navSection, "Dashboard", "bar-chart-2", "", () => this.plugin._openFile(DASHBOARD_FILENAME));
    this._actionBtn(navSection, "Search proposals", "search", "", () => new KmsSearchModal(this.plugin.app, this.plugin).open());

    // Advanced
    const advSection = section("Advanced");
    this._actionBtn(advSection, "Revert proposal", "undo", "Revert single applied proposal", () => new KmsRevertModal(this.plugin.app, this.plugin).open());
    this._actionBtn(advSection, "Revert batch", "rotate-ccw", "Undo entire bulk operation", () => new KmsBatchRevertModal(this.plugin.app, this.plugin).open());
  }

  _actionBtn(parent, label, icon, tooltip, onClick) {
    const btn = parent.createEl("button", { cls: "kms-panel-btn" });
    // Use Obsidian's setIcon for lucide icons
    const iconSpan = btn.createSpan({ cls: "kms-panel-btn-icon" });
    try {
      const { setIcon } = require("obsidian");
      setIcon(iconSpan, icon);
    } catch { /* fallback: no icon */ }
    btn.createSpan({ text: label });
    if (tooltip) btn.title = tooltip;
    btn.addEventListener("click", onClick);
    return btn;
  }

  async _loadStats(el) {
    const python = this.plugin._getPython();
    const projectRoot = this.plugin._getProjectRoot();
    const cmd = `"${python}" -m kms.scripts.proposal_detail`;

    try {
      const stdout = await this.plugin._exec(cmd, projectRoot);
      const all = JSON.parse(stdout);
      el.empty();

      const pending = all.filter((p) => p.decision === "pending").length;
      const approve = all.filter((p) => p.decision === "approve").length;
      const reject = all.filter((p) => p.decision === "reject").length;
      const postpone = all.filter((p) => p.decision === "postpone").length;
      const applied = all.filter((p) => p.is_applied).length;
      const total = all.length;

      // Donut-style summary
      const grid = el.createDiv({ cls: "kms-stats-grid" });

      this._statCard(grid, String(total), "Total", "");
      this._statCard(grid, String(pending), "Pending", "kms-stat-pending");
      this._statCard(grid, String(approve), "Approved", "kms-stat-approve");
      this._statCard(grid, String(applied), "Applied", "kms-stat-applied");
      this._statCard(grid, String(reject), "Rejected", "kms-stat-reject");
      this._statCard(grid, String(postpone), "Postpone", "kms-stat-postpone");

      // Domain breakdown
      const domains = {};
      for (const p of all) {
        const d = p.domain || "(none)";
        domains[d] = (domains[d] || 0) + 1;
      }
      const sorted = Object.entries(domains).sort((a, b) => b[1] - a[1]).slice(0, 8);

      if (sorted.length > 0 && !(sorted.length === 1 && sorted[0][0] === "(none)")) {
        const domEl = el.createDiv({ cls: "kms-panel-domains" });
        domEl.createEl("div", { cls: "kms-panel-section-title", text: "Top domains" });
        for (const [domain, count] of sorted) {
          const row = domEl.createDiv({ cls: "kms-domain-row" });
          row.createSpan({ cls: "kms-domain-name", text: domain });
          const bar = row.createDiv({ cls: "kms-domain-bar-bg" });
          const fill = bar.createDiv({ cls: "kms-domain-bar-fill" });
          fill.style.width = `${Math.round((count / total) * 100)}%`;
          row.createSpan({ cls: "kms-domain-count", text: String(count) });
        }
      }
    } catch (err) {
      el.empty();
      el.createEl("p", { cls: "kms-search-error", text: `Stats error: ${err.message}` });
    }
  }

  _statCard(parent, value, label, cls) {
    const card = parent.createDiv({ cls: `kms-stat-card ${cls}` });
    card.createDiv({ cls: "kms-stat-value", text: value });
    card.createDiv({ cls: "kms-stat-label", text: label });
  }

  async onClose() {}
}

// ════════════════════════════════════════════════════════════════
// Search Modal
// ════════════════════════════════════════════════════════════════

class KmsSearchModal extends Modal {
  constructor(app, plugin) {
    super(app);
    this.plugin = plugin;
  }

  onOpen() {
    const { contentEl } = this;
    contentEl.addClass("kms-search-modal");
    contentEl.createEl("h3", { text: "Search KMS proposals" });

    const inputRow = contentEl.createDiv({ cls: "kms-search-input-row" });
    const input = inputRow.createEl("input", {
      cls: "kms-search-input",
      type: "text",
      placeholder: "np. Angular, migration, python, debugging...",
    });
    const allToggle = inputRow.createEl("label", { cls: "kms-search-toggle" });
    const checkbox = allToggle.createEl("input", { type: "checkbox" });
    allToggle.appendText(" Tylko pending");

    const resultsEl = contentEl.createDiv({ cls: "kms-search-results" });

    let debounceTimer;
    const doSearch = () => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => this._search(input.value, checkbox.checked, resultsEl), 400);
    };
    input.addEventListener("input", doSearch);
    checkbox.addEventListener("change", doSearch);
    input.addEventListener("keydown", (e) => {
      if (e.key === "Enter") { clearTimeout(debounceTimer); this._search(input.value, checkbox.checked, resultsEl); }
    });
    setTimeout(() => input.focus(), 50);
  }

  async _search(query, pendingOnly, resultsEl) {
    if (query.length < 2) {
      resultsEl.empty();
      resultsEl.createEl("p", { cls: "kms-search-hint", text: "Wpisz min. 2 znaki aby wyszukać..." });
      return;
    }

    const projectRoot = this.plugin._getProjectRoot();
    const python = this.plugin._getPython();
    const escaped = query.replace(/"/g, '\\"');
    const flag = pendingOnly ? " --pending-only" : "";
    const cmd = `"${python}" -m kms.scripts.search_proposals --query "${escaped}" --format json${flag}`;

    resultsEl.empty();
    resultsEl.createEl("p", { cls: "kms-search-loading", text: "Searching..." });

    try {
      const stdout = await this.plugin._exec(cmd, projectRoot);
      const results = JSON.parse(stdout);
      resultsEl.empty();

      if (results.length === 0) {
        resultsEl.createEl("p", { cls: "kms-search-empty", text: `No proposals matching "${query}".` });
        return;
      }
      resultsEl.createEl("p", { cls: "kms-search-count", text: `${results.length} result${results.length > 1 ? "s" : ""}` });

      for (const r of results) {
        const item = resultsEl.createDiv({ cls: "kms-search-result" });
        const header = item.createDiv({ cls: "kms-search-result-header" });
        header.createSpan({ cls: "kms-search-pid", text: `#${r.proposal_id}` });
        if (r.domain) header.createSpan({ cls: "kms-tag kms-tag-domain", text: r.domain });
        header.createSpan({ cls: `kms-search-decision kms-decision-${r.decision}`, text: r.decision });

        item.createEl("div", { cls: "kms-search-path", text: r.item_path });

        if (r.topics && r.topics.length > 0) {
          const topicsEl = item.createDiv({ cls: "kms-search-topics" });
          for (const t of r.topics) topicsEl.createSpan({ cls: "kms-tag", text: t });
        }
        if (r.summary) {
          item.createEl("div", { cls: "kms-search-summary", text: r.summary.substring(0, 180) + (r.summary.length > 180 ? "..." : "") });
        }

        const actions = item.createDiv({ cls: "kms-search-actions" });
        const goBtn = actions.createEl("button", { cls: "kms-search-action-btn kms-action-goto", text: "Go to proposal" });
        goBtn.addEventListener("click", (e) => { e.stopPropagation(); this.close(); this.plugin._scrollToProposal(r.proposal_id); });

        const srcBtn = actions.createEl("button", { cls: "kms-search-action-btn kms-action-source", text: "Open source" });
        srcBtn.addEventListener("click", (e) => { e.stopPropagation(); this.close(); this.plugin._openFile(r.item_path); });

        const detailBtn = actions.createEl("button", { cls: "kms-search-action-btn kms-action-detail", text: "Details" });
        detailBtn.addEventListener("click", (e) => { e.stopPropagation(); this.close(); new KmsDetailModal(this.app, this.plugin, r.proposal_id).open(); });
      }
    } catch (err) {
      resultsEl.empty();
      resultsEl.createEl("p", { cls: "kms-search-error", text: `Search error: ${err.message}` });
    }
  }

  onClose() { this.contentEl.empty(); }
}

// ════════════════════════════════════════════════════════════════
// Detail Modal
// ════════════════════════════════════════════════════════════════

class KmsDetailModal extends Modal {
  constructor(app, plugin, proposalId) {
    super(app);
    this.plugin = plugin;
    this.proposalId = proposalId;
  }

  async onOpen() {
    const { contentEl } = this;
    contentEl.addClass("kms-detail-modal");
    contentEl.createEl("h3", { text: `Proposal #${this.proposalId}` });

    const body = contentEl.createDiv({ cls: "kms-detail-body" });
    body.createEl("p", { cls: "kms-search-loading", text: "Loading..." });

    const python = this.plugin._getPython();
    const projectRoot = this.plugin._getProjectRoot();
    const cmd = `"${python}" -m kms.scripts.proposal_detail --proposal-id ${this.proposalId}`;

    try {
      const stdout = await this.plugin._exec(cmd, projectRoot);
      const results = JSON.parse(stdout);
      body.empty();

      if (results.length === 0) { body.createEl("p", { text: "Proposal not found." }); return; }

      const d = results[0];

      const statusSection = body.createDiv({ cls: "kms-detail-section" });
      statusSection.createEl("h4", { text: "Status" });
      const st = statusSection.createEl("table", { cls: "kms-detail-table" });
      this._row(st, "Decision", d.decision, `kms-decision-${d.decision}`);
      this._row(st, "Lifecycle", d.lifecycle_status || "(none)");
      this._row(st, "Item status", d.item_status);
      this._row(st, "Confidence", `${(d.confidence || 0).toFixed(2)}`);
      if (d.reviewer) this._row(st, "Reviewer", d.reviewer);
      if (d.review_note) this._row(st, "Review note", d.review_note);
      if (d.decided_at) this._row(st, "Decided at", d.decided_at);

      const cs = body.createDiv({ cls: "kms-detail-section" });
      cs.createEl("h4", { text: "Classification" });
      const ct = cs.createEl("table", { cls: "kms-detail-table" });
      this._row(ct, "Domain", d.domain || "(none)");
      this._row(ct, "Topics", (d.topics || []).join(", ") || "(none)");
      this._row(ct, "Kind", d.kind);
      this._row(ct, "Suggested action", d.suggested_action);
      this._row(ct, "Target", d.suggested_target || "(none)");
      if (d.override_target) this._row(ct, "Override target", d.override_target);

      const ps = body.createDiv({ cls: "kms-detail-section" });
      ps.createEl("h4", { text: "Paths" });
      const pt = ps.createEl("table", { cls: "kms-detail-table" });
      this._row(pt, "Source", d.item_path);
      this._row(pt, "Target", d.suggested_target || "(none)");
      if (d.source_note_path) this._row(pt, "Source note", d.source_note_path);
      this._row(pt, "Created", d.created_at || "");

      if (d.is_applied) {
        const as = body.createDiv({ cls: "kms-detail-section" });
        as.createEl("h4", { text: "Applied" });
        const at = as.createEl("table", { cls: "kms-detail-table" });
        this._row(at, "Applied at", d.applied_at || "");
        this._row(at, "Index status", d.index_status || "");
        this._row(at, "Execution ID", String(d.execution_id || ""));
        if (d.reverted_at) this._row(at, "Reverted at", d.reverted_at);
      }

      if (d.summary) {
        const ss = body.createDiv({ cls: "kms-detail-section" });
        ss.createEl("h4", { text: "Summary" });
        ss.createEl("p", { cls: "kms-detail-summary", text: d.summary });
      }

      const actions = body.createDiv({ cls: "kms-detail-actions" });
      const gotoBtn = actions.createEl("button", { cls: "kms-search-action-btn kms-action-goto", text: "Go to proposal in queue" });
      gotoBtn.addEventListener("click", () => { this.close(); this.plugin._scrollToProposal(this.proposalId); });
      const srcBtn = actions.createEl("button", { cls: "kms-search-action-btn kms-action-source", text: "Open source file" });
      srcBtn.addEventListener("click", () => { this.close(); this.plugin._openFile(d.item_path); });

      if (d.can_revert) {
        const revertBtn = actions.createEl("button", { cls: "kms-search-action-btn kms-action-revert", text: "Revert this apply" });
        revertBtn.addEventListener("click", async () => {
          revertBtn.disabled = true; revertBtn.textContent = "Reverting...";
          try {
            await this.plugin._exec(`"${python}" -m kms.scripts.revert_apply --proposal-id ${this.proposalId}`, projectRoot);
            new Notice(`Proposal #${this.proposalId} reverted.`);
            this.close();
            this.plugin._runPipeline("refresh");
          } catch (err) { revertBtn.textContent = "Revert failed"; new Notice(`Revert failed: ${err.message}`, 10000); }
        });
      }
    } catch (err) {
      body.empty();
      body.createEl("p", { cls: "kms-search-error", text: `Error loading detail: ${err.message}` });
    }
  }

  _row(table, label, value, extraCls) {
    const tr = table.createEl("tr");
    tr.createEl("td", { cls: "kms-detail-label", text: label });
    const td = tr.createEl("td", { cls: "kms-detail-value", text: value });
    if (extraCls) td.addClass(extraCls);
  }

  onClose() { this.contentEl.empty(); }
}

// ════════════════════════════════════════════════════════════════
// Revert Modal
// ════════════════════════════════════════════════════════════════

class KmsRevertModal extends Modal {
  constructor(app, plugin) {
    super(app);
    this.plugin = plugin;
  }

  onOpen() {
    const { contentEl } = this;
    contentEl.addClass("kms-revert-modal");
    contentEl.createEl("h3", { text: "Revert applied proposal" });
    contentEl.createEl("p", { text: "Enter the proposal ID to revert. This will move the file back to its original location and remove the execution record." });

    const inputRow = contentEl.createDiv({ cls: "kms-revert-input-row" });
    const input = inputRow.createEl("input", { cls: "kms-revert-input", type: "number", placeholder: "Proposal ID (e.g. 42)" });
    const previewEl = contentEl.createDiv({ cls: "kms-revert-preview" });

    const btnRow = contentEl.createDiv({ cls: "kms-revert-btn-row" });
    const previewBtn = btnRow.createEl("button", { cls: "kms-search-action-btn kms-action-detail", text: "Preview (dry-run)" });
    const revertBtn = btnRow.createEl("button", { cls: "kms-search-action-btn kms-action-revert", text: "Revert" });
    revertBtn.disabled = true;

    previewBtn.addEventListener("click", async () => {
      const pid = parseInt(input.value, 10);
      if (!pid) { new Notice("Enter a valid proposal ID."); return; }
      previewEl.empty();
      previewEl.createEl("p", { cls: "kms-search-loading", text: "Running dry-run..." });
      const python = this.plugin._getPython();
      const projectRoot = this.plugin._getProjectRoot();
      try {
        const stdout = await this.plugin._exec(`"${python}" -m kms.scripts.proposal_detail --proposal-id ${pid}`, projectRoot);
        const results = JSON.parse(stdout);
        previewEl.empty();
        if (results.length === 0) { previewEl.createEl("p", { text: `Proposal #${pid} not found.` }); return; }
        const d = results[0];
        if (!d.can_revert) {
          previewEl.createEl("p", { cls: "kms-search-error", text: d.is_applied ? `Proposal #${pid} was already reverted.` : `Proposal #${pid} has not been applied yet.` });
          return;
        }
        previewEl.createEl("p", { text: `Will revert: ${d.item_path} (${d.suggested_action} -> ${d.suggested_target})` });
        previewEl.createEl("p", { text: `Applied at: ${d.applied_at || "unknown"}`, cls: "kms-detail-summary" });
        revertBtn.disabled = false;
      } catch (err) { previewEl.empty(); previewEl.createEl("p", { cls: "kms-search-error", text: `Error: ${err.message}` }); }
    });

    revertBtn.addEventListener("click", async () => {
      const pid = parseInt(input.value, 10);
      if (!pid) return;
      revertBtn.disabled = true; revertBtn.textContent = "Reverting...";
      const python = this.plugin._getPython();
      const projectRoot = this.plugin._getProjectRoot();
      try {
        await this.plugin._exec(`"${python}" -m kms.scripts.revert_apply --proposal-id ${pid}`, projectRoot);
        new Notice(`Proposal #${pid} reverted successfully.`);
        this.close();
        this.plugin._runPipeline("refresh");
      } catch (err) { revertBtn.textContent = "Revert failed"; new Notice(`Revert failed: ${err.message}`, 10000); }
    });
    setTimeout(() => input.focus(), 50);
  }

  onClose() { this.contentEl.empty(); }
}

// ════════════════════════════════════════════════════════════════
// Batch Revert Modal
// ════════════════════════════════════════════════════════════════

class KmsBatchRevertModal extends Modal {
  constructor(app, plugin) {
    super(app);
    this.plugin = plugin;
  }

  async onOpen() {
    const { contentEl } = this;
    contentEl.addClass("kms-revert-modal");
    contentEl.createEl("h3", { text: "Revert batch operation" });
    contentEl.createEl("p", { text: "Select a batch to revert all proposals applied in that operation." });

    const listEl = contentEl.createDiv({ cls: "kms-search-results" });
    listEl.createEl("p", { cls: "kms-search-loading", text: "Loading batches..." });

    const python = this.plugin._getPython();
    const projectRoot = this.plugin._getProjectRoot();

    try {
      const stdout = await this.plugin._exec(
        `"${python}" -m kms.scripts.list_batches`,
        projectRoot,
      );
      const batches = JSON.parse(stdout);
      listEl.empty();

      const active = batches.filter((b) => !b.reverted_at);
      if (active.length === 0) {
        listEl.createEl("p", { cls: "kms-search-empty", text: "No active batches to revert." });
        return;
      }

      listEl.createEl("p", { cls: "kms-search-count", text: `${active.length} active batch${active.length > 1 ? "es" : ""}` });

      for (const b of active) {
        const item = listEl.createDiv({ cls: "kms-search-result" });
        const header = item.createDiv({ cls: "kms-search-result-header" });
        header.createSpan({ cls: "kms-search-pid", text: b.id.slice(0, 8) });
        header.createSpan({ cls: "kms-tag kms-tag-domain", text: b.action });
        header.createSpan({ cls: "kms-search-decision kms-decision-approve", text: `${b.proposal_count} proposals` });

        item.createDiv({ cls: "kms-search-path", text: b.description || "" });
        item.createDiv({ cls: "kms-search-summary", text: `Created: ${(b.created_at || "").replace("T", " ").slice(0, 16)}` });

        const actions = item.createDiv({ cls: "kms-search-actions" });
        const revertBtn = actions.createEl("button", { cls: "kms-search-action-btn kms-action-revert", text: "Revert entire batch" });

        revertBtn.addEventListener("click", async () => {
          revertBtn.disabled = true;
          revertBtn.textContent = "Reverting...";
          try {
            await this.plugin._exec(
              `"${python}" -m kms.scripts.revert_apply --batch-id "${b.id}"`,
              projectRoot,
            );
            new Notice(`Batch ${b.id.slice(0, 8)} reverted (${b.proposal_count} proposals).`);
            this.close();
            this.plugin._runPipeline("refresh");
          } catch (err) {
            revertBtn.textContent = "Revert failed";
            new Notice(`Batch revert failed: ${err.message}`, 10000);
          }
        });
      }
    } catch (err) {
      listEl.empty();
      listEl.createEl("p", { cls: "kms-search-error", text: `Error loading batches: ${err.message}` });
    }
  }

  onClose() { this.contentEl.empty(); }
}
