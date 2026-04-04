import { Modal, Notice } from "obsidian";
import { _t } from "./i18n";

// ── Search Modal ──

export class KmsSearchModal extends Modal {
  constructor(app, plugin) {
    super(app);
    this.plugin = plugin;
  }

  onOpen() {
    const { contentEl } = this;
    const t = (k, ...a) => _t(this.plugin.settings, k, ...a);
    contentEl.addClass("kms-search-modal");
    contentEl.createEl("h3", { text: t("searchTitle") });

    const inputRow = contentEl.createDiv({ cls: "kms-search-input-row" });
    const input = inputRow.createEl("input", {
      cls: "kms-search-input", type: "text", placeholder: t("searchPlaceholder"),
    });
    const allToggle = inputRow.createEl("label", { cls: "kms-search-toggle" });
    const checkbox = allToggle.createEl("input", { type: "checkbox" });
    allToggle.appendText(t("searchOnlyPending"));

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
    const t = (k, ...a) => _t(this.plugin.settings, k, ...a);
    if (query.length < 2) {
      resultsEl.empty();
      resultsEl.createEl("p", { cls: "kms-search-hint", text: t("searchMinChars") });
      return;
    }

    const projectRoot = this.plugin._getProjectRoot();
    const python = this.plugin._getPython();
    const escaped = query.replace(/"/g, '\\"');
    const flag = pendingOnly ? " --pending-only" : "";
    const cmd = `"${python}" -m kms.scripts.search_proposals --query "${escaped}" --format json${flag}`;

    resultsEl.empty();
    resultsEl.createEl("p", { cls: "kms-search-loading", text: t("searchLoading") });

    try {
      const stdout = await this.plugin._exec(cmd, projectRoot);
      const results = JSON.parse(stdout);
      resultsEl.empty();

      if (results.length === 0) {
        resultsEl.createEl("p", { cls: "kms-search-empty", text: t("searchNoResults", query) });
        return;
      }
      resultsEl.createEl("p", { cls: "kms-search-count", text: t("searchCount", results.length) });

      for (const r of results) {
        const item = resultsEl.createDiv({ cls: "kms-search-result" });
        const header = item.createDiv({ cls: "kms-search-result-header" });
        header.createSpan({ cls: "kms-search-pid", text: `#${r.proposal_id}` });
        if (r.domain) header.createSpan({ cls: "kms-tag kms-tag-domain", text: r.domain });
        header.createSpan({ cls: `kms-search-decision kms-decision-${r.decision}`, text: r.decision });

        item.createEl("div", { cls: "kms-search-path", text: r.item_path });

        if (r.topics && r.topics.length > 0) {
          const topicsEl = item.createDiv({ cls: "kms-search-topics" });
          for (const tp of r.topics) topicsEl.createSpan({ cls: "kms-tag", text: tp });
        }
        if (r.summary) {
          item.createEl("div", { cls: "kms-search-summary", text: r.summary.substring(0, 180) + (r.summary.length > 180 ? "..." : "") });
        }

        const actions = item.createDiv({ cls: "kms-search-actions" });
        const goBtn = actions.createEl("button", { cls: "kms-search-action-btn kms-action-goto", text: t("goToProposal") });
        goBtn.addEventListener("click", (e) => { e.stopPropagation(); this.close(); this.plugin._scrollToProposal(r.proposal_id); });
        const srcBtn = actions.createEl("button", { cls: "kms-search-action-btn kms-action-source", text: t("openSource") });
        srcBtn.addEventListener("click", (e) => { e.stopPropagation(); this.close(); this.plugin._openFile(r.item_path); });
        const detailBtn = actions.createEl("button", { cls: "kms-search-action-btn kms-action-detail", text: t("detailsBtn") });
        detailBtn.addEventListener("click", (e) => { e.stopPropagation(); this.close(); new KmsDetailModal(this.app, this.plugin, r.proposal_id).open(); });
      }
    } catch (err) {
      resultsEl.empty();
      resultsEl.createEl("p", { cls: "kms-search-error", text: t("searchErrorMsg", err.message) });
    }
  }

  onClose() { this.contentEl.empty(); }
}

// ── Detail Modal ──

export class KmsDetailModal extends Modal {
  constructor(app, plugin, proposalId) {
    super(app);
    this.plugin = plugin;
    this.proposalId = proposalId;
  }

  async onOpen() {
    const { contentEl } = this;
    const t = (k, ...a) => _t(this.plugin.settings, k, ...a);
    contentEl.addClass("kms-detail-modal");
    contentEl.createEl("h3", { text: t("detailTitle", this.proposalId) });

    const body = contentEl.createDiv({ cls: "kms-detail-body" });
    body.createEl("p", { cls: "kms-search-loading", text: t("detailLoading") });

    const python = this.plugin._getPython();
    const projectRoot = this.plugin._getProjectRoot();
    const cmd = `"${python}" -m kms.scripts.proposal_detail --proposal-id ${this.proposalId}`;

    try {
      const stdout = await this.plugin._exec(cmd, projectRoot);
      const results = JSON.parse(stdout);
      body.empty();

      if (results.length === 0) { body.createEl("p", { text: t("detailNotFound") }); return; }

      const d = results[0];

      const statusSection = body.createDiv({ cls: "kms-detail-section" });
      statusSection.createEl("h4", { text: t("detailStatus") });
      const st = statusSection.createEl("table", { cls: "kms-detail-table" });
      this._row(st, t("fieldDecision"), d.decision, `kms-decision-${d.decision}`);
      this._row(st, t("fieldLifecycle"), d.lifecycle_status || "(none)");
      this._row(st, t("fieldItemStatus"), d.item_status);
      this._row(st, t("fieldConfidence"), `${(d.confidence || 0).toFixed(2)}`);
      if (d.reviewer) this._row(st, t("fieldReviewer"), d.reviewer);
      if (d.review_note) this._row(st, t("fieldReviewNote"), d.review_note);
      if (d.decided_at) this._row(st, t("fieldDecidedAt"), d.decided_at);

      const cs = body.createDiv({ cls: "kms-detail-section" });
      cs.createEl("h4", { text: t("detailClassification") });
      const ct = cs.createEl("table", { cls: "kms-detail-table" });
      this._row(ct, t("fieldDomain"), d.domain || "(none)");
      this._row(ct, t("fieldTopics"), (d.topics || []).join(", ") || "(none)");
      this._row(ct, t("fieldKind"), d.kind);
      this._row(ct, t("fieldSuggestedAction"), d.suggested_action);
      this._row(ct, t("fieldTarget"), d.suggested_target || "(none)");
      if (d.override_target) this._row(ct, t("fieldOverrideTarget"), d.override_target);

      const ps = body.createDiv({ cls: "kms-detail-section" });
      ps.createEl("h4", { text: t("detailPaths") });
      const pt = ps.createEl("table", { cls: "kms-detail-table" });
      this._row(pt, t("fieldSource"), d.item_path);
      this._row(pt, t("fieldTarget"), d.suggested_target || "(none)");
      if (d.source_note_path) this._row(pt, t("fieldSourceNote"), d.source_note_path);
      this._row(pt, t("fieldCreated"), d.created_at || "");

      if (d.is_applied) {
        const as = body.createDiv({ cls: "kms-detail-section" });
        as.createEl("h4", { text: t("detailAppliedSection") });
        const at = as.createEl("table", { cls: "kms-detail-table" });
        this._row(at, t("fieldAppliedAt"), d.applied_at || "");
        this._row(at, t("fieldIndexStatus"), d.index_status || "");
        this._row(at, t("fieldExecutionId"), String(d.execution_id || ""));
        if (d.reverted_at) this._row(at, t("fieldRevertedAt"), d.reverted_at);
      }

      if (d.summary) {
        const ss = body.createDiv({ cls: "kms-detail-section" });
        ss.createEl("h4", { text: t("detailSummarySection") });
        ss.createEl("p", { cls: "kms-detail-summary", text: d.summary });
      }

      const actions = body.createDiv({ cls: "kms-detail-actions" });
      const gotoBtn = actions.createEl("button", { cls: "kms-search-action-btn kms-action-goto", text: t("goToProposal") });
      gotoBtn.addEventListener("click", () => { this.close(); this.plugin._scrollToProposal(this.proposalId); });
      const srcBtn = actions.createEl("button", { cls: "kms-search-action-btn kms-action-source", text: t("openSource") });
      srcBtn.addEventListener("click", () => { this.close(); this.plugin._openFile(d.item_path); });

      if (d.can_revert) {
        const revertBtn = actions.createEl("button", { cls: "kms-search-action-btn kms-action-revert", text: t("revertBtn") });
        revertBtn.addEventListener("click", async () => {
          revertBtn.disabled = true; revertBtn.textContent = t("reverting");
          try {
            const ok = await this.plugin._runRevertPipeline(
              `${t("revertBtn")} #${this.proposalId}`,
              `"${python}" -m kms.scripts.revert_apply --proposal-id ${this.proposalId}`,
            );
            if (ok) { new Notice(t("revertDone", this.proposalId)); this.close(); }
            else { revertBtn.textContent = t("revertFailed"); revertBtn.disabled = false; }
          } catch (err) { revertBtn.textContent = t("revertFailed"); new Notice(`${t("revertFailed")}: ${err.message}`, 10000); revertBtn.disabled = false; }
        });
      }
    } catch (err) {
      body.empty();
      body.createEl("p", { cls: "kms-search-error", text: t("detailErrorMsg", err.message) });
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

// ── Revert Modal ──

export class KmsRevertModal extends Modal {
  constructor(app, plugin) {
    super(app);
    this.plugin = plugin;
  }

  onOpen() {
    const { contentEl } = this;
    const t = (k, ...a) => _t(this.plugin.settings, k, ...a);
    contentEl.addClass("kms-revert-modal");
    contentEl.createEl("h3", { text: t("revertTitle") });
    contentEl.createEl("p", { text: t("revertDesc") });

    const inputRow = contentEl.createDiv({ cls: "kms-revert-input-row" });
    const input = inputRow.createEl("input", { cls: "kms-revert-input", type: "number", placeholder: t("revertPlaceholder") });
    const previewEl = contentEl.createDiv({ cls: "kms-revert-preview" });

    const btnRow = contentEl.createDiv({ cls: "kms-revert-btn-row" });
    const previewBtn = btnRow.createEl("button", { cls: "kms-search-action-btn kms-action-detail", text: t("revertPreview") });
    const revertBtn = btnRow.createEl("button", { cls: "kms-search-action-btn kms-action-revert", text: t("revertBtn") });
    revertBtn.disabled = true;

    previewBtn.addEventListener("click", async () => {
      const pid = parseInt(input.value, 10);
      if (!pid) { new Notice(t("revertInvalidId")); return; }
      previewEl.empty();
      previewEl.createEl("p", { cls: "kms-search-loading", text: t("revertDryRun") });
      const python = this.plugin._getPython();
      const projectRoot = this.plugin._getProjectRoot();
      try {
        const stdout = await this.plugin._exec(`"${python}" -m kms.scripts.proposal_detail --proposal-id ${pid}`, projectRoot);
        const results = JSON.parse(stdout);
        previewEl.empty();
        if (results.length === 0) { previewEl.createEl("p", { text: t("revertNotFound", pid) }); return; }
        const d = results[0];
        if (!d.can_revert) {
          previewEl.createEl("p", { cls: "kms-search-error", text: d.is_applied ? t("revertAlreadyReverted", pid) : t("revertNotApplied", pid) });
          return;
        }
        previewEl.createEl("p", { text: t("revertWillRevert", d.item_path, d.suggested_action, d.suggested_target) });
        previewEl.createEl("p", { text: t("revertAppliedAtLabel", d.applied_at), cls: "kms-detail-summary" });
        revertBtn.disabled = false;
      } catch (err) { previewEl.empty(); previewEl.createEl("p", { cls: "kms-search-error", text: t("detailErrorMsg", err.message) }); }
    });

    revertBtn.addEventListener("click", async () => {
      const pid = parseInt(input.value, 10);
      if (!pid) return;
      revertBtn.disabled = true; revertBtn.textContent = t("reverting");
      const python = this.plugin._getPython();
      const projectRoot = this.plugin._getProjectRoot();
      try {
        const ok = await this.plugin._runRevertPipeline(
          `${t("revertBtn")} #${pid}`,
          `"${python}" -m kms.scripts.revert_apply --proposal-id ${pid}`,
        );
        if (ok) { new Notice(t("revertDone", pid)); this.close(); }
        else { revertBtn.textContent = t("revertFailed"); revertBtn.disabled = false; }
      } catch (err) { revertBtn.textContent = t("revertFailed"); new Notice(`${t("revertFailed")}: ${err.message}`, 10000); revertBtn.disabled = false; }
    });
    setTimeout(() => input.focus(), 50);
  }

  onClose() { this.contentEl.empty(); }
}

// ── Batch Revert Modal ──

export class KmsBatchRevertModal extends Modal {
  constructor(app, plugin) {
    super(app);
    this.plugin = plugin;
  }

  async onOpen() {
    const { contentEl } = this;
    const t = (k, ...a) => _t(this.plugin.settings, k, ...a);
    contentEl.addClass("kms-revert-modal");
    contentEl.createEl("h3", { text: t("batchRevertTitle") });
    contentEl.createEl("p", { text: t("batchRevertDesc") });

    const listEl = contentEl.createDiv({ cls: "kms-search-results" });
    listEl.createEl("p", { cls: "kms-search-loading", text: t("batchLoading") });

    const python = this.plugin._getPython();
    const projectRoot = this.plugin._getProjectRoot();

    try {
      const stdout = await this.plugin._exec(`"${python}" -m kms.scripts.list_batches`, projectRoot);
      const batches = JSON.parse(stdout);
      listEl.empty();

      const active = batches.filter((b) => !b.reverted_at);
      if (active.length === 0) {
        listEl.createEl("p", { cls: "kms-search-empty", text: t("noBatches") });
        return;
      }

      listEl.createEl("p", { cls: "kms-search-count", text: t("activeBatches", active.length) });

      for (const b of active) {
        const item = listEl.createDiv({ cls: "kms-search-result" });
        const header = item.createDiv({ cls: "kms-search-result-header" });
        header.createSpan({ cls: "kms-search-pid", text: b.id.slice(0, 8) });
        header.createSpan({ cls: "kms-tag kms-tag-domain", text: b.action });
        header.createSpan({ cls: "kms-search-decision kms-decision-approve", text: t("batchProposalCount", b.proposal_count) });

        item.createDiv({ cls: "kms-search-path", text: b.description || "" });
        item.createDiv({ cls: "kms-search-summary", text: t("batchCreatedLabel", (b.created_at || "").replace("T", " ").slice(0, 16)) });

        const actions = item.createDiv({ cls: "kms-search-actions" });
        const revertBtn = actions.createEl("button", { cls: "kms-search-action-btn kms-action-revert", text: t("revertEntireBatch") });

        revertBtn.addEventListener("click", async () => {
          revertBtn.disabled = true;
          revertBtn.textContent = t("reverting");
          try {
            const ok = await this.plugin._runRevertPipeline(
              `${t("revertEntireBatch")} ${b.id.slice(0, 8)} (${b.proposal_count})`,
              `"${python}" -m kms.scripts.revert_apply --batch-id "${b.id}"`,
            );
            if (ok) { new Notice(t("batchReverted", b.id.slice(0, 8), b.proposal_count)); this.close(); }
            else { revertBtn.textContent = t("revertFailed"); revertBtn.disabled = false; }
          } catch (err) {
            revertBtn.textContent = t("revertFailed");
            new Notice(`${t("batchRevertFailed")} ${err.message}`, 10000);
            revertBtn.disabled = false;
          }
        });
      }
    } catch (err) {
      listEl.empty();
      listEl.createEl("p", { cls: "kms-search-error", text: `${t("batchRevertFailed")} ${err.message}` });
    }
  }

  onClose() { this.contentEl.empty(); }
}

// ── Confirm Modal ──

export class KmsConfirmModal extends Modal {
  constructor(app, plugin, message, callback) {
    super(app);
    this.plugin = plugin;
    this.message = message;
    this._callback = callback;
    this._resolved = false;
  }

  onOpen() {
    const { contentEl } = this;
    const t = (k, ...a) => _t(this.plugin.settings, k, ...a);
    contentEl.addClass("kms-confirm-modal");
    contentEl.createEl("h3", { text: t("confirmTitle") });
    contentEl.createEl("p", { text: this.message });

    const btnRow = contentEl.createDiv({ cls: "kms-confirm-actions" });
    const yesBtn = btnRow.createEl("button", { text: t("confirmYes"), cls: "mod-cta mod-warning" });
    yesBtn.addEventListener("click", () => { this._resolved = true; this.close(); this._callback(true); });
    const noBtn = btnRow.createEl("button", { text: t("confirmNo") });
    noBtn.addEventListener("click", () => { this._resolved = true; this.close(); this._callback(false); });
  }

  onClose() {
    this.contentEl.empty();
    if (!this._resolved && this._callback) this._callback(false);
  }
}

// ── Progress Modal ──

export class KmsProgressModal extends Modal {
  constructor(app, plugin, mode, stepLabels) {
    super(app);
    this.plugin = plugin;
    this.mode = mode;
    this.stepLabels = stepLabels;
    this.stepEls = [];
    this.timeEls = [];
  }

  onOpen() {
    const { contentEl } = this;
    contentEl.addClass("kms-progress-modal");
    contentEl.createEl("h3", { text: `KMS: ${this.mode}` });

    this.listEl = contentEl.createEl("ul", { cls: "kms-progress-list" });
    for (const label of this.stepLabels) {
      const li = this.listEl.createEl("li", { cls: "kms-progress-step kms-step-pending" });
      li.createSpan({ cls: "kms-progress-icon", text: "\u25cb" });
      li.createSpan({ cls: "kms-progress-label", text: label });
      const timeSpan = li.createSpan({ cls: "kms-progress-time" });
      this.stepEls.push(li);
      this.timeEls.push(timeSpan);
    }

    this.footerEl = contentEl.createDiv({ cls: "kms-progress-footer" });
  }

  setStep(idx, state, elapsedMs) {
    const li = this.stepEls[idx];
    if (!li) return;
    const icon = li.querySelector(".kms-progress-icon");
    li.className = `kms-progress-step kms-step-${state}`;
    if (state === "running") icon.textContent = "\u25c9";
    else if (state === "done") icon.textContent = "\u2713";
    else if (state === "error") icon.textContent = "\u2717";
    if (elapsedMs != null) {
      this.timeEls[idx].textContent = `${(elapsedMs / 1000).toFixed(1)}s`;
    }
  }

  showDone() {
    const t = (k, ...a) => _t(this.plugin.settings, k, ...a);
    this.footerEl.empty();
    this.footerEl.createEl("p", { text: t("pipelineDone"), cls: "kms-progress-done" });
    const btnRow = this.footerEl.createDiv({ cls: "kms-progress-actions" });
    const closeBtn = btnRow.createEl("button", { text: t("close"), cls: "mod-cta" });
    closeBtn.addEventListener("click", () => this.close());
  }

  showError(errorMsg) {
    const t = (k, ...a) => _t(this.plugin.settings, k, ...a);
    this.footerEl.empty();
    this.footerEl.createEl("p", { text: t("pipelineError"), cls: "kms-progress-error-title" });
    this.footerEl.createEl("pre", { cls: "kms-progress-error-detail", text: errorMsg.slice(-600) });

    const btnRow = this.footerEl.createDiv({ cls: "kms-progress-actions" });
    const copyBtn = btnRow.createEl("button", { text: t("copyError") });
    copyBtn.addEventListener("click", () => {
      navigator.clipboard.writeText(errorMsg);
      new Notice(t("copied"));
    });
    const closeBtn = btnRow.createEl("button", { text: t("close") });
    closeBtn.addEventListener("click", () => this.close());
  }

  onClose() { this.contentEl.empty(); }
}
