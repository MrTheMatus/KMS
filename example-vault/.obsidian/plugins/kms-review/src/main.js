import { Plugin, Notice, MarkdownView } from "obsidian";
import { REVIEW_QUEUE_FILENAME, DASHBOARD_FILENAME, KMS_BEGIN, KMS_END, PANEL_VIEW_TYPE, DEFAULT_SETTINGS } from "./constants";
import { _t } from "./i18n";
import { KmsPanelView } from "./panel";
import { KmsSettingsTab } from "./settings";
import { KmsOnboardingWizard, KmsHelpModal } from "./wizard";
import { KmsNoticeModal, KmsSearchModal, KmsDetailModal, KmsRevertModal, KmsBatchRevertModal, KmsConfirmModal, KmsProgressModal, KmsAskLlmModal } from "./modals";

const { exec } = require("child_process");
const path = require("path");

export default class KmsReviewPlugin extends Plugin {
  async onload() {
    await this.loadSettings();

    this.addSettingTab(new KmsSettingsTab(this.app, this));

    this.registerView(PANEL_VIEW_TYPE, (leaf) => new KmsPanelView(leaf, this));

    this.registerMarkdownCodeBlockProcessor("kms-review", (source, el, ctx) => {
      this._renderReviewBlock(source, el, ctx);
    });

    // ── Commands ──
    this.addCommand({ id: "open-panel", name: "Open control panel", callback: () => this._activatePanel() });
    this.addCommand({ id: "open-review-queue", name: "Open review queue", callback: () => this._openFile(REVIEW_QUEUE_FILENAME) });
    this.addCommand({ id: "open-dashboard", name: "Open dashboard", callback: () => this._openFile(DASHBOARD_FILENAME) });
    this.addCommand({ id: "refresh-review-queue", name: "Refresh review queue (scan + AI summaries + dashboard)", callback: () => this._runPipeline("refresh") });
    this.addCommand({ id: "apply-decisions", name: "Apply decisions (move approved files)", callback: () => this._runPipeline("apply") });
    this.addCommand({ id: "retriage-all", name: "Retriage all proposals (re-classify domains/topics via LLM)", callback: () => this._runPipeline("retriage") });
    this.addCommand({ id: "approve-all-pending", name: "Approve all pending proposals", callback: () => this._bulkDecision("approve") });
    this.addCommand({ id: "reject-all-pending", name: "Reject all pending proposals", callback: () => this._bulkDecision("reject") });
    this.addCommand({ id: "search-proposals", name: "Search proposals", callback: () => new KmsSearchModal(this.app, this).open() });
    this.addCommand({ id: "revert-proposal", name: "Revert applied proposal (enter proposal ID)", callback: () => new KmsRevertModal(this.app, this).open() });
    this.addCommand({ id: "revert-batch", name: "Revert batch (undo entire bulk operation)", callback: () => new KmsBatchRevertModal(this.app, this).open() });
    this.addCommand({ id: "run-wizard", name: "Run setup wizard", callback: () => new KmsOnboardingWizard(this.app, this).open() });
    this.addCommand({ id: "ask-llm", name: "Ask knowledge base (AnythingLLM)", callback: () => {
      if (!this.settings.anythingllmEnabled) {
        new KmsNoticeModal(this.app, this,
          "AnythingLLM",
          _t(this.settings, "askNoAnythingLLM"),
          { actions: [{ label: _t(this.settings, "wizOpenSettings"), cls: "mod-cta", callback: () => {
            this.app.setting.open();
            this.app.setting.openTabById("kms-review");
          }}]},
        ).open();
        return;
      }
      new KmsAskLlmModal(this.app, this).open();
    }});
    this.addCommand({ id: "show-help", name: "Help & how-to", callback: () => new KmsHelpModal(this.app, this).open() });

    this.addRibbonIcon("layout-dashboard", "KMS Control Panel", () => this._activatePanel());

    if (!this.settings.onboardingDone) {
      this.app.workspace.onLayoutReady(() => new KmsOnboardingWizard(this.app, this).open());
    }
  }

  onunload() {
    this.app.workspace.detachLeavesOfType(PANEL_VIEW_TYPE);
  }

  async loadSettings() {
    this.settings = Object.assign({}, DEFAULT_SETTINGS, await this.loadData());
  }

  async saveSettings() {
    await this.saveData(this.settings);
  }

  // ── Panel ──

  async _activatePanel() {
    const existing = this.app.workspace.getLeavesOfType(PANEL_VIEW_TYPE);
    if (existing.length) { this.app.workspace.revealLeaf(existing[0]); return; }
    const leaf = this.app.workspace.getRightLeaf(false);
    await leaf.setViewState({ type: PANEL_VIEW_TYPE, active: true });
    this.app.workspace.revealLeaf(leaf);
  }

  _refreshPanel() {
    for (const leaf of this.app.workspace.getLeavesOfType(PANEL_VIEW_TYPE)) {
      if (leaf.view instanceof KmsPanelView) leaf.view.refresh();
    }
  }

  // ── Pipeline ──

  _getProjectRoot() {
    if (this.settings.projectRoot) return this.settings.projectRoot;
    return path.dirname(this.app.vault.adapter.basePath);
  }

  _getPython() {
    if (this.settings.pythonPath) return this.settings.pythonPath;
    return path.join(this._getProjectRoot(), ".venv", "bin", "python");
  }

  async _runPipeline(mode) {
    const projectRoot = this._getProjectRoot();
    const python = this._getPython();
    const t = (k, ...a) => _t(this.settings, k, ...a);

    const aiFlag = this.settings.profile !== "core" ? " --ai-summary" : "";

    const pipelines = {
      refresh: [
        { cmd: `"${python}" -m kms.scripts.scan_inbox`, label: t("scanning") },
        { cmd: `"${python}" -m kms.scripts.make_review_queue${aiFlag}`, label: t("generating") },
        { cmd: `"${python}" -m kms.scripts.generate_dashboard`, label: t("updatingDash") },
      ],
      apply: [
        { cmd: `"${python}" -m kms.scripts.apply_decisions`, label: t("applying") },
        { cmd: `"${python}" -m kms.scripts.make_review_queue`, label: t("refreshingQueue") },
        { cmd: `"${python}" -m kms.scripts.generate_dashboard`, label: t("updatingDash") },
      ],
      retriage: [
        { cmd: `"${python}" -m kms.scripts.make_review_queue --retriage${aiFlag}`, label: t("retriaging") },
        { cmd: `"${python}" -m kms.scripts.generate_dashboard`, label: t("updatingDash") },
      ],
    };

    const steps = pipelines[mode];
    if (!steps) return;
    await this._executeSteps(mode, steps);
  }

  async _runRevertPipeline(revertCmdLabel, revertCmd) {
    const python = this._getPython();
    const t = (k, ...a) => _t(this.settings, k, ...a);
    const steps = [
      { cmd: revertCmd, label: revertCmdLabel || t("revertBtn") },
      { cmd: `"${python}" -m kms.scripts.make_review_queue`, label: t("refreshingQueue") },
      { cmd: `"${python}" -m kms.scripts.generate_dashboard`, label: t("updatingDash") },
    ];
    return this._executeSteps("revert", steps);
  }

  /** Shared step-runner: opens progress modal, runs commands, returns true on success. */
  async _executeSteps(mode, steps) {
    const progress = new KmsProgressModal(this.app, this, mode, steps.map((s) => s.label));
    progress.open();
    const cwd = this._getProjectRoot();

    for (let i = 0; i < steps.length; i++) {
      progress.setStep(i, "running");
      const start = Date.now();
      try {
        await this._exec(steps[i].cmd, cwd);
        progress.setStep(i, "done", Date.now() - start);
      } catch (err) {
        progress.setStep(i, "error", Date.now() - start);
        progress.showError(err.message);
        this._refreshPanel();
        return false;
      }
    }

    progress.showDone();
    this._reloadKmsViews();
    this._refreshPanel();
    return true;
  }

  _exec(cmd, cwd) {
    return new Promise((resolve, reject) => {
      exec(cmd, {
        cwd: cwd || this._getProjectRoot(),
        timeout: 600000,
        env: { ...process.env, PYTHONPATH: cwd || this._getProjectRoot() },
      }, (error, stdout, stderr) => {
        if (error) {
          const raw = stderr?.trim() || stdout?.trim() || error.message;
          const tbIdx = raw.lastIndexOf("Traceback");
          const errIdx = raw.lastIndexOf("Error:");
          const relevant = tbIdx >= 0 ? raw.slice(tbIdx) : errIdx >= 0 ? raw.slice(errIdx) : raw;
          reject(new Error(relevant.slice(-800)));
        } else {
          resolve(stdout);
        }
      });
    });
  }

  _reloadKmsViews() {
    this.app.workspace.iterateAllLeaves((leaf) => {
      const fp = leaf.view?.file?.path;
      if (fp === REVIEW_QUEUE_FILENAME || fp === DASHBOARD_FILENAME) leaf.rebuildView();
    });
  }

  // ── Navigate ──

  async _openFile(filePath) {
    const file = this.app.vault.getAbstractFileByPath(filePath);
    if (file) {
      await this.app.workspace.openLinkText(file.path, "", false);
    } else {
      const t = (k, ...a) => _t(this.settings, k, ...a);
      new KmsNoticeModal(this.app, this, t("pipelineError"), t("fileNotFound", filePath), {
        actions: [{ label: t("btnRefresh"), cls: "mod-cta", callback: () => this._runPipeline("refresh") }],
      }).open();
    }
  }

  async _scrollToProposal(proposalId) {
    const file = this.app.vault.getAbstractFileByPath(REVIEW_QUEUE_FILENAME);
    if (!file) {
      new KmsNoticeModal(this.app, this, _t(this.settings, "pipelineError"), _t(this.settings, "reviewQueueNotFound"), {
        actions: [{ label: _t(this.settings, "btnRefresh"), cls: "mod-cta", callback: () => this._runPipeline("refresh") }],
      }).open();
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
          { from: { line: targetLine, ch: 0 }, to: { line: targetLine + 20, ch: 0 } }, true,
        );
      }
    }
  }

  // ── Bulk operations ──

  async _bulkDecision(decision) {
    const file = this.app.vault.getAbstractFileByPath(REVIEW_QUEUE_FILENAME);
    const t = (k, ...a) => _t(this.settings, k, ...a);
    if (!file) {
      new KmsNoticeModal(this.app, this, t("pipelineError"), t("reviewQueueNotFound"), {
        actions: [{ label: t("btnRefresh"), cls: "mod-cta", callback: () => this._runPipeline("refresh") }],
      }).open();
      return;
    }

    let content = await this.app.vault.read(file);
    const blocks = this._splitKmsBlocks(content);
    let count = 0;
    for (const block of blocks) {
      if (!block.isKms) continue;
      const m = block.text.match(/decision:\s*(\S+)/);
      if (m && m[1] === "pending") count++;
    }

    if (count === 0) {
      new KmsNoticeModal(this.app, this, t("bulkTitle"), t("noPending")).open();
      return;
    }

    const qKey = decision === "approve" ? "bulkApproveQ" : "bulkRejectQ";
    const confirmed = await new Promise((resolve) => {
      new KmsConfirmModal(this.app, this, t(qKey, count), resolve).open();
    });
    if (!confirmed) return;

    content = await this.app.vault.read(file);
    const freshBlocks = this._splitKmsBlocks(content);
    let applied = 0;
    for (const block of freshBlocks) {
      if (!block.isKms) continue;
      const m = block.text.match(/decision:\s*(\S+)/);
      if (!m || m[1] !== "pending") continue;
      const fieldRegex = /^(decision:\s*)(.*)$/m;
      if (fieldRegex.test(block.text)) { block.text = block.text.replace(fieldRegex, `$1${decision}`); applied++; }
    }

    await this.app.vault.modify(file, freshBlocks.map((b) => b.text).join(""));
    new KmsNoticeModal(this.app, this, t("bulkTitle"), t("bulkDone", applied, decision), {
      actions: [{ label: t("btnApply"), cls: "mod-cta", callback: () => this._runPipeline("apply") }],
    }).open();
    this._reloadKmsViews();
    this._refreshPanel();
  }

  // ── Review block rendering ──

  async _renderReviewBlock(source, el, ctx) {
    const parsed = this._parseYaml(source);
    if (!parsed.proposal_id) { el.createEl("pre", { text: source }); return; }

    const t = (k, ...a) => _t(this.settings, k, ...a);
    const container = el.createDiv({ cls: `kms-review-block kms-decision-${parsed.decision}` });
    container.dataset.proposalId = parsed.proposal_id;

    const header = container.createDiv({ cls: "kms-review-header" });
    const titleEl = header.createSpan({ cls: "kms-review-title kms-clickable", text: t("proposalTitle", parsed.proposal_id) });
    titleEl.addEventListener("click", () => new KmsDetailModal(this.app, this, parsed.proposal_id).open());
    titleEl.title = t("clickToViewDetails");

    header.createSpan({ cls: "kms-review-badge", text: parsed.decision.toUpperCase() });

    const btnRow = container.createDiv({ cls: "kms-decision-buttons" });
    for (const d of [
      { value: "approve", label: t("btnApprove"), aria: t("ariaApprove", parsed.proposal_id) },
      { value: "reject", label: t("btnReject"), aria: t("ariaReject", parsed.proposal_id) },
      { value: "postpone", label: t("btnPostpone"), aria: t("ariaPostpone", parsed.proposal_id) },
    ]) {
      const btn = btnRow.createEl("button", {
        cls: `kms-decision-btn${parsed.decision === d.value ? ` active-${d.value}` : ""}`,
        text: d.label,
        attr: { "aria-label": d.aria },
      });
      btn.addEventListener("click", async () => {
        btnRow.querySelectorAll(".kms-decision-btn").forEach((b) => (b.className = "kms-decision-btn"));
        btn.className = `kms-decision-btn active-${d.value}`;
        container.className = `kms-review-block kms-decision-${d.value}`;
        header.querySelector(".kms-review-badge").textContent = d.value.toUpperCase();
        await this._updateField(ctx.sourcePath, parsed.proposal_id, "decision", d.value);
        new Notice(`${_t(this.settings, "proposalDecision", parsed.proposal_id, d.value)} — ${_t(this.settings, "applyHint")}`, 6000);
      });
    }

    const noteInput = container.createEl("input", {
      cls: "kms-review-note-input", type: "text",
      placeholder: t("reviewNotePlaceholder"), value: parsed.review_note || "",
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
      if ((val.startsWith("'") && val.endsWith("'")) || (val.startsWith('"') && val.endsWith('"'))) val = val.slice(1, -1);
      if (val === "null" || val === "~") return "";
      return val;
    };
    return {
      proposal_id: get("proposal_id"), item_id: get("item_id"),
      decision: get("decision") || "pending", reviewer: get("reviewer"),
      override_target: get("override_target"), review_note: get("review_note"),
    };
  }

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
      if (fieldRegex.test(block.text)) { block.text = block.text.replace(fieldRegex, `$1${quoted}`); modified = true; }
    }

    if (modified) await this.app.vault.modify(file, blocks.map((b) => b.text).join(""));
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
}
