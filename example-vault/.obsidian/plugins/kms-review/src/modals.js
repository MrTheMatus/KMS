import { Modal, Notice, requestUrl, MarkdownRenderer } from "obsidian";
import { _t } from "./i18n";

// ── Notice Modal (replaces toasts for errors & important messages) ──

export class KmsNoticeModal extends Modal {
  /**
   * @param {App} app
   * @param {Plugin} plugin
   * @param {string} title - Modal heading
   * @param {string} message - Main message text
   * @param {Object} [opts] - Optional: { detail, actions: [{label, cls, callback}] }
   */
  constructor(app, plugin, title, message, opts = {}) {
    super(app);
    this.plugin = plugin;
    this._title = title;
    this._message = message;
    this._detail = opts.detail || "";
    this._actions = opts.actions || [];
  }

  onOpen() {
    const { contentEl } = this;
    const t = (k, ...a) => _t(this.plugin.settings, k, ...a);
    contentEl.addClass("kms-notice-modal");
    contentEl.createEl("h3", { text: this._title });
    contentEl.createEl("p", { cls: "kms-notice-message", text: this._message });

    if (this._detail) {
      const detailEl = contentEl.createEl("pre", { cls: "kms-notice-detail", text: this._detail });
      const copyBtn = contentEl.createEl("button", { cls: "kms-notice-copy-btn", text: t("copyError") });
      copyBtn.addEventListener("click", () => {
        navigator.clipboard.writeText(this._detail);
        copyBtn.textContent = t("copied");
        setTimeout(() => { copyBtn.textContent = t("copyError"); }, 1500);
      });
    }

    const btnRow = contentEl.createDiv({ cls: "kms-notice-actions" });

    for (const action of this._actions) {
      const btn = btnRow.createEl("button", { text: action.label, cls: action.cls || "" });
      btn.addEventListener("click", () => {
        this.close();
        if (action.callback) action.callback();
      });
    }

    const closeBtn = btnRow.createEl("button", { text: t("close"), cls: this._actions.length ? "" : "mod-cta" });
    closeBtn.addEventListener("click", () => this.close());
  }

  onClose() { this.contentEl.empty(); }
}

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
          } catch (err) {
            revertBtn.textContent = t("revertFailed"); revertBtn.disabled = false;
            new KmsNoticeModal(this.app, this.plugin, t("revertFailed"), t("revertFailed"), { detail: err.message }).open();
          }
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
      if (!pid) { previewEl.empty(); previewEl.createEl("p", { cls: "kms-search-error", text: t("revertInvalidId") }); return; }
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
      } catch (err) {
        revertBtn.textContent = t("revertFailed"); revertBtn.disabled = false;
        new KmsNoticeModal(this.app, this.plugin, t("revertFailed"), t("revertFailed"), { detail: err.message }).open();
      }
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
            revertBtn.disabled = false;
            new KmsNoticeModal(this.app, this.plugin, t("batchRevertFailed"), t("batchRevertFailed"), { detail: err.message }).open();
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

// ── Ask LLM Modal (hybrid: AnythingLLM + vault keyword search) ──

export class KmsAskLlmModal extends Modal {
  constructor(app, plugin) {
    super(app);
    this.plugin = plugin;
    this._vaultResults = [];
    this._lastQuestion = "";
  }

  onOpen() {
    const { contentEl, modalEl } = this;
    const t = (k, ...a) => _t(this.plugin.settings, k, ...a);
    modalEl.addClass("kms-ask-modal");
    contentEl.createEl("h3", { text: t("askTitle") });
    contentEl.createEl("p", { cls: "kms-ask-desc", text: t("askDesc") });

    const input = contentEl.createEl("textarea", {
      cls: "kms-ask-input",
      attr: { rows: "3", placeholder: t("askPlaceholder") },
    });

    const btnRow = contentEl.createDiv({ cls: "kms-ask-actions" });
    const askBtn = btnRow.createEl("button", { text: t("askSend"), cls: "mod-cta" });

    const responseEl = contentEl.createDiv({ cls: "kms-ask-response" });
    const vaultEl = contentEl.createDiv({ cls: "kms-ask-vault" });

    // Chat history footer for power users
    const settings = this.plugin.settings;
    const baseHost = (settings.anythingllmUrl || "http://localhost:3001").replace(/\/+$/, "");
    const chatsUrl = `${baseHost}/settings/workspace-chats`;
    const footer = contentEl.createDiv({ cls: "kms-ask-footer" });
    const footerLink = footer.createEl("a", {
      cls: "kms-ask-history-link",
      text: t("askHistoryBtn"),
      attr: { href: chatsUrl },
    });
    footerLink.addEventListener("click", (e) => {
      e.preventDefault();
      window.open(chatsUrl, "_blank");
    });
    footer.createSpan({ cls: "kms-ask-footer-hint", text: ` — ${t("askHistoryHint", chatsUrl)}` });

    const doAsk = async (withContext = false) => {
      const question = input.value.trim();
      if (!question) return;
      this._lastQuestion = question;
      askBtn.disabled = true;
      askBtn.textContent = t("askLoading");
      responseEl.empty();
      responseEl.createEl("p", { cls: "kms-search-loading", text: t("askLoading") });
      if (!withContext) vaultEl.empty();

      try {
        const s = this.plugin.settings;
        const slug = s.anythingllmSlug || "my-workspace";
        const baseUrl = (s.anythingllmUrl || "http://localhost:3001").replace(/\/+$/, "");
        const apiKey = s.anythingllmApiKey || "";

        if (!apiKey) {
          responseEl.empty();
          this.close();
          new KmsNoticeModal(this.app, this.plugin, "AnythingLLM", t("askNoApiKey"), {
            actions: [{ label: t("wizOpenSettings"), cls: "mod-cta", callback: () => {
              this.app.setting.open();
              this.app.setting.openTabById("kms-review");
            }}],
          }).open();
          askBtn.disabled = false;
          askBtn.textContent = t("askSend");
          return;
        }

        // ── Build message (optionally enriched with vault context) ──
        let message = question;
        let mode = "query"; // embedding-based RAG
        if (withContext) {
          const selected = this._getSelectedVaultFiles(vaultEl);
          if (selected.length > 0) {
            const ctx = selected.map(r =>
              `--- ${r.path} ---\n${r.content.substring(0, 1500)}`
            ).join("\n\n");
            message = `Kontekst z moich notatek:\n\n${ctx}\n\n---\nPytanie: ${question}`;
            mode = "chat"; // we provide context, skip embedding retrieval
          }
        }

        // ── Call AnythingLLM ──
        const resp = await requestUrl({
          url: `${baseUrl}/api/v1/workspace/${slug}/chat`,
          method: "POST",
          headers: {
            "Authorization": `Bearer ${apiKey}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ message, mode, attachments: [] }),
        });

        const data = resp.json;
        responseEl.empty();

        // ── Render answer as Markdown ──
        const text = data.textResponse || data.error || JSON.stringify(data);
        const answer = responseEl.createDiv({ cls: "kms-ask-answer" });
        answer.createEl("h4", { text: t("askAnswer") });
        if (withContext) {
          answer.createEl("span", { cls: "kms-ask-context-badge", text: t("askContextBadge") });
        }
        const answerBody = answer.createDiv({ cls: "kms-ask-answer-body" });
        try {
          await MarkdownRenderer.render(this.app, text, answerBody, "", this);
        } catch (_) {
          // Fallback: plain paragraphs
          for (const para of text.split("\n\n")) {
            if (para.trim()) answerBody.createEl("p", { text: para.trim() });
          }
        }

        // ── Show AnythingLLM sources ──
        const sources = data.sources || [];
        if (sources.length > 0) {
          const srcEl = responseEl.createDiv({ cls: "kms-ask-sources" });
          srcEl.createEl("h4", { text: t("askSources") });
          for (const src of sources) {
            const title = src.title || src.name || src.location || "—";
            srcEl.createEl("p", { cls: "kms-ask-source-item", text: `• ${title}` });
          }
        }

        // ── Vault keyword search (only on first ask, not re-ask) ──
        if (!withContext) {
          this._vaultResults = await this._searchVault(question);
          this._renderVaultResults(vaultEl, t, () => doAsk(true));
        }
      } catch (err) {
        responseEl.empty();
        this.close();
        new KmsNoticeModal(this.app, this.plugin, t("askErrorTitle"), t("askError", err.message), {
          detail: err.message,
          actions: [{ label: t("wizOpenSettings"), callback: () => {
            this.app.setting.open();
            this.app.setting.openTabById("kms-review");
          }}],
        }).open();
      }

      askBtn.disabled = false;
      askBtn.textContent = t("askSend");
    };

    askBtn.addEventListener("click", () => doAsk(false));
    input.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) doAsk(false);
    });
    setTimeout(() => input.focus(), 50);
  }

  // ── Render vault keyword-search results with checkboxes ──
  _renderVaultResults(container, t, reaskCallback) {
    container.empty();
    if (this._vaultResults.length === 0) {
      container.createEl("p", { cls: "kms-ask-vault-empty", text: t("askVaultEmpty") });
      return;
    }

    const header = container.createDiv({ cls: "kms-ask-vault-header" });
    header.createEl("h4", { text: t("askVaultTitle") });
    header.createEl("p", { cls: "kms-ask-vault-desc", text: t("askVaultDesc") });

    const list = container.createDiv({ cls: "kms-ask-vault-list" });
    for (const r of this._vaultResults) {
      const item = list.createDiv({ cls: "kms-ask-vault-item" });
      const row = item.createEl("label", { cls: "kms-ask-vault-label" });
      row.createEl("input", { type: "checkbox", attr: { "data-path": r.path } });
      row.createSpan({ cls: "kms-ask-vault-path", text: r.path });
      row.createSpan({ cls: "kms-ask-vault-score", text: `${r.matched}/${r.total} terms · ${r.score} pts` });
      if (r.snippet) {
        item.createEl("p", { cls: "kms-ask-vault-snippet", text: r.snippet });
      }
    }

    const reaskBtn = container.createEl("button", {
      cls: "kms-ask-vault-reask",
      text: t("askReaskWithContext"),
    });
    reaskBtn.addEventListener("click", () => reaskCallback());
  }

  // ── Keyword search across vault markdown files ──
  // Improved: stop words, prefix stemming, coverage-weighted scoring
  async _searchVault(query) {
    const files = this.app.vault.getMarkdownFiles();

    // 1) Strip punctuation, lowercase, split
    const raw = query.toLowerCase().replace(/[^a-ząćęłńóśźż0-9\s]/gi, "").split(/\s+/);

    // 2) Stop words (PL + EN) — filter out noise
    const STOP = new Set([
      "i","w","z","na","do","to","co","jak","czy","że","nie","się","jest",
      "od","za","po","ale","lub","te","ten","ta","tym","tego","tej","o","a",
      "ze","dla","przy","przez","bez","nad","pod","czego","czym","jaki",
      "jaka","jakie","który","która","które","być","był","była","było",
      "były","będzie","mieć","miał","miała","dotyczyła","dotyczyło",
      "the","a","an","is","are","was","were","be","been","have","has",
      "had","do","does","did","will","would","could","should","may",
      "can","of","in","to","for","with","on","at","from","by","about",
      "as","and","but","or","not","what","which","who","this","that",
      "how","where","when","why","it","its","my","your","his","her",
    ]);
    const terms = raw.filter(w => w.length >= 2 && !STOP.has(w));
    if (terms.length === 0) return [];

    // 3) Generate prefix stems for Polish declension tolerance
    //    "simona" → ["simona","simon"], "johnem" → ["johnem","johne","john"]
    const termSets = terms.map(t => {
      const stems = [t];
      if (t.length > 3) stems.push(t.slice(0, -1));
      if (t.length > 4) stems.push(t.slice(0, -2));
      return { original: t, stems };
    });

    const searchFolders = /^(10_Sources|20_Source-Notes|30_Permanent-Notes)\//;
    const scored = [];

    for (const file of files) {
      if (!searchFolders.test(file.path)) continue;
      const content = await this.app.vault.cachedRead(file);
      const lower = content.toLowerCase();
      const nameLower = file.basename.toLowerCase().replace(/[-_]/g, " ");

      let totalScore = 0;
      let termsMatched = 0;
      let bestMatchStem = null;

      for (const { stems } of termSets) {
        let best = 0;
        for (const stem of stems) {
          let count = 0;
          let idx = 0;
          while ((idx = lower.indexOf(stem, idx)) !== -1) { count++; idx += stem.length; }
          if (nameLower.includes(stem)) count += 5; // filename match bonus
          best = Math.max(best, count);
        }
        if (best > 0) {
          termsMatched++;
          totalScore += Math.min(best, 10); // cap per-term to prevent single word domination
          if (!bestMatchStem) {
            bestMatchStem = stems.find(s => lower.includes(s));
          }
        }
      }

      if (totalScore > 0 && termsMatched > 0) {
        // 4) Coverage bonus: strongly prefer files matching MORE distinct query terms
        //    coverage=1.0 → ×2.5, coverage=0.5 → ×1.5, coverage=0.25 → ×1.0
        const coverage = termsMatched / termSets.length;
        const finalScore = Math.round(totalScore * (0.5 + coverage * 2));

        const stem = bestMatchStem || terms[0];
        const matchIdx = Math.max(0, lower.indexOf(stem));
        const start = Math.max(0, matchIdx - 60);
        const end = Math.min(content.length, matchIdx + 250);
        const snippet =
          (start > 0 ? "…" : "") +
          content.substring(start, end).replace(/\n+/g, " ").trim() +
          (end < content.length ? "…" : "");
        scored.push({
          path: file.path,
          score: finalScore,
          matched: termsMatched,
          total: termSets.length,
          snippet,
          content,
        });
      }
    }

    scored.sort((a, b) => b.score - a.score);
    return scored.slice(0, 8);
  }

  // ── Get checked vault files from the UI ──
  _getSelectedVaultFiles(container) {
    const checked = container.querySelectorAll("input[type=checkbox]:checked");
    const paths = new Set([...checked].map(cb => cb.getAttribute("data-path")));
    return this._vaultResults.filter(r => paths.has(r.path));
  }

  onClose() { this.contentEl.empty(); }
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
