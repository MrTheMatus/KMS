import { ItemView, setIcon } from "obsidian";
import { PANEL_VIEW_TYPE, REVIEW_QUEUE_FILENAME, DASHBOARD_FILENAME } from "./constants";
import { _t } from "./i18n";
import { KmsSearchModal, KmsRevertModal, KmsBatchRevertModal } from "./modals";

export class KmsPanelView extends ItemView {
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
    const t = (k, ...a) => _t(this.plugin.settings, k, ...a);

    root.createEl("h4", { cls: "kms-panel-title", text: t("panelTitle") });

    const statsEl = root.createDiv({ cls: "kms-panel-stats" });
    statsEl.createEl("p", { cls: "kms-search-loading", text: t("loadingStats") });
    this._loadStats(statsEl);

    const section = (title) => {
      const s = root.createDiv({ cls: "kms-panel-section" });
      s.createEl("div", { cls: "kms-panel-section-title", text: title });
      return s;
    };

    // Pipeline
    const pipeSection = section(t("secPipeline"));
    this._actionBtn(pipeSection, t("btnRefresh"), "rotate-cw", t("tooltipRefresh"), () => this.plugin._runPipeline("refresh"));
    this._actionBtn(pipeSection, t("btnApply"), "check-circle", t("tooltipApply"), () => this.plugin._runPipeline("apply"));
    if (this.plugin.settings.profile !== "core") {
      this._actionBtn(pipeSection, t("btnRetriage"), "wand", t("tooltipRetriage"), () => this.plugin._runPipeline("retriage"));
    }

    // Bulk
    const bulkSection = section(t("secBulk"));
    this._actionBtn(bulkSection, t("btnApproveAll"), "check", "", () => this.plugin._bulkDecision("approve"));
    this._actionBtn(bulkSection, t("btnRejectAll"), "x", "", () => this.plugin._bulkDecision("reject"));

    // Navigate
    const navSection = section(t("secNavigate"));
    this._actionBtn(navSection, t("btnReviewQueue"), "file-text", "", () => this.plugin._openFile(REVIEW_QUEUE_FILENAME));
    this._actionBtn(navSection, t("btnDashboard"), "bar-chart-2", "", () => this.plugin._openFile(DASHBOARD_FILENAME));
    this._actionBtn(navSection, t("btnSearch"), "search", "", () => new KmsSearchModal(this.plugin.app, this.plugin).open());

    // Advanced
    const advSection = section(t("secAdvanced"));
    this._actionBtn(advSection, t("btnRevertProposal"), "undo", t("tooltipRevert"), () => new KmsRevertModal(this.plugin.app, this.plugin).open());
    this._actionBtn(advSection, t("btnRevertBatch"), "rotate-ccw", t("tooltipBatchRevert"), () => new KmsBatchRevertModal(this.plugin.app, this.plugin).open());
  }

  _actionBtn(parent, label, icon, tooltip, onClick) {
    const btn = parent.createEl("button", { cls: "kms-panel-btn" });
    const iconSpan = btn.createSpan({ cls: "kms-panel-btn-icon" });
    try { setIcon(iconSpan, icon); } catch { /* fallback */ }
    btn.createSpan({ text: label });
    if (tooltip) btn.title = tooltip;
    btn.addEventListener("click", onClick);
    return btn;
  }

  async _loadStats(el) {
    const t = (k, ...a) => _t(this.plugin.settings, k, ...a);
    const python = this.plugin._getPython();
    const projectRoot = this.plugin._getProjectRoot();

    try {
      const stdout = await this.plugin._exec(`"${python}" -m kms.scripts.proposal_detail`, projectRoot);
      const all = JSON.parse(stdout);
      el.empty();

      const pending = all.filter((p) => p.decision === "pending").length;
      const approve = all.filter((p) => p.decision === "approve").length;
      const reject = all.filter((p) => p.decision === "reject").length;
      const postpone = all.filter((p) => p.decision === "postpone").length;
      const applied = all.filter((p) => p.is_applied).length;
      const total = all.length;

      const grid = el.createDiv({ cls: "kms-stats-grid" });
      this._statCard(grid, String(total), t("statTotal"), "");
      this._statCard(grid, String(pending), t("statPending"), "kms-stat-pending");
      this._statCard(grid, String(approve), t("statApproved"), "kms-stat-approve");
      this._statCard(grid, String(applied), t("statApplied"), "kms-stat-applied");
      this._statCard(grid, String(reject), t("statRejected"), "kms-stat-reject");
      this._statCard(grid, String(postpone), t("statPostpone"), "kms-stat-postpone");

      const domains = {};
      for (const p of all) {
        const d = p.domain || "(none)";
        domains[d] = (domains[d] || 0) + 1;
      }
      const sorted = Object.entries(domains).sort((a, b) => b[1] - a[1]).slice(0, 8);

      if (sorted.length > 0 && !(sorted.length === 1 && sorted[0][0] === "(none)")) {
        const domEl = el.createDiv({ cls: "kms-panel-domains" });
        domEl.createEl("div", { cls: "kms-panel-section-title", text: t("topDomains") });
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
      el.createEl("p", { cls: "kms-search-error", text: `${t("statsError")} ${err.message}` });
    }
  }

  _statCard(parent, value, label, cls) {
    const card = parent.createDiv({ cls: `kms-stat-card ${cls}` });
    card.createDiv({ cls: "kms-stat-value", text: value });
    card.createDiv({ cls: "kms-stat-label", text: label });
  }

  async onClose() {}
}
