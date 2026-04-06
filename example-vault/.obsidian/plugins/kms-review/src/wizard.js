import { Modal } from "obsidian";
import { REVIEW_QUEUE_FILENAME, DASHBOARD_FILENAME } from "./constants";
import { _t } from "./i18n";

const path = require("path");
const fs = require("fs");

export class KmsOnboardingWizard extends Modal {
  constructor(app, plugin) {
    super(app);
    this.plugin = plugin;
    this.step = 0;
    this.totalSteps = 6;
    this.checks = {};
    this.inboxCount = 0;
  }

  onOpen() {
    const { contentEl } = this;
    contentEl.addClass("kms-wizard-modal");
    this._renderStep();
  }

  _renderStep() {
    const { contentEl } = this;
    const t = (k, ...a) => _t(this.plugin.settings, k, ...a);
    contentEl.empty();

    const stepLabels = [
      t("wizStep1"), t("wizProfileTitle"), t("wizStep2"),
      t("wizStep3"), t("wizStep4"), t("wizStepHelp"),
    ];
    const indicator = contentEl.createDiv({ cls: "kms-wizard-steps" });
    for (let i = 0; i < stepLabels.length; i++) {
      const dot = indicator.createSpan({
        cls: `kms-wizard-dot${i === this.step ? " active" : i < this.step ? " done" : ""}`,
        text: i < this.step ? "\u2713" : String(i + 1),
      });
      dot.title = stepLabels[i];
      if (i < stepLabels.length - 1) indicator.createSpan({ cls: "kms-wizard-dot-line" });
    }

    const body = contentEl.createDiv({ cls: "kms-wizard-body" });

    if (this.step === 0) this._stepWelcome(body);
    else if (this.step === 1) this._stepProfile(body);
    else if (this.step === 2) this._stepEnvironment(body);
    else if (this.step === 3) this._stepInbox(body);
    else if (this.step === 4) this._stepFirstRun(body);
    else if (this.step === 5) this._stepHelp(body);
  }

  // ── Step 0: Welcome ──
  _stepWelcome(body) {
    const t = (k, ...a) => _t(this.plugin.settings, k, ...a);
    body.createEl("h3", { text: t("wizTitle") });
    body.createEl("p", { text: t("wizIntro") });

    const features = body.createEl("ul", { cls: "kms-wizard-features" });
    for (const f of t("wizFeatures")) {
      features.createEl("li", { text: f });
    }

    body.createEl("p", { cls: "kms-wizard-hint", text: t("wizHint") });
    this._navButtons(body, { showBack: false, nextLabel: t("next") });
  }

  // ── Step 1: Profile selection ──
  _stepProfile(body) {
    const t = (k, ...a) => _t(this.plugin.settings, k, ...a);
    body.createEl("h3", { text: t("wizProfileTitle") });
    body.createEl("p", { text: t("wizProfileIntro") });

    const profiles = [
      { value: "core", label: t("profileCore"), desc: t("profileCoreDesc") },
      { value: "ai-local", label: t("profileAiLocal"), desc: t("profileAiLocalDesc") },
      { value: "ai-cloud", label: t("profileAiCloud"), desc: t("profileAiCloudDesc") },
    ];

    const list = body.createDiv({ cls: "kms-wizard-profiles" });
    for (const p of profiles) {
      const card = list.createDiv({
        cls: `kms-wizard-profile-card${this.plugin.settings.profile === p.value ? " active" : ""}`,
      });
      card.createEl("strong", { text: p.label });
      card.createEl("p", { text: p.desc });
      card.addEventListener("click", async () => {
        this.plugin.settings.profile = p.value;
        await this.plugin.saveSettings();
        list.querySelectorAll(".kms-wizard-profile-card").forEach((c) => c.removeClass("active"));
        card.addClass("active");
      });
    }

    this._navButtons(body, { showBack: true, nextLabel: t("next") });
  }

  // ── Step 2: Environment checks ──
  async _stepEnvironment(body) {
    const t = (k, ...a) => _t(this.plugin.settings, k, ...a);
    body.createEl("h3", { text: t("wizEnvTitle") });
    body.createEl("p", { text: t("wizEnvIntro") });

    const list = body.createEl("ul", { cls: "kms-health-list" });
    const pythonPath = this.plugin._getPython();
    const projectRoot = this.plugin._getProjectRoot();
    const configPath = path.join(projectRoot, "kms", "config", "config.yaml");

    const pythonOk = fs.existsSync(pythonPath);
    this.checks.python = pythonOk;
    this._checkItem(list, pythonOk, "Python", pythonOk ? pythonPath : `Not found: ${pythonPath}`);

    const configOk = fs.existsSync(configPath);
    this.checks.config = configOk;
    this._checkItem(list, configOk, "config.yaml", configOk ? t("wizEnvOk") : t("wizEnvFixConfig"));

    const intLi = this._checkItem(list, null, t("wizEnvIntegrity"), t("wizEnvChecking"));
    if (pythonOk && configOk) {
      try {
        const out = await this.plugin._exec(`"${pythonPath}" -m kms.scripts.verify_integrity --json`, projectRoot);
        const ok = JSON.parse(out).ok === true;
        this.checks.integrity = ok;
        intLi.className = ok ? "kms-health-ok" : "kms-health-fail";
        intLi.empty();
        intLi.createSpan({ text: ok ? "\u2713 " : "\u2717 " });
        intLi.createSpan({ text: `${t("wizEnvIntegrity")}: ` });
        intLi.createEl("code", { text: ok ? t("wizEnvOk") : t("wizEnvNeedsRepair") });
      } catch {
        this.checks.integrity = false;
        intLi.className = "kms-health-fail";
        intLi.empty();
        intLi.createSpan({ text: "\u2717 " });
        intLi.createSpan({ text: `${t("wizEnvIntegrity")}: ` });
        intLi.createEl("code", { text: t("wizEnvFirstRun") });
      }
    } else {
      this.checks.integrity = false;
      intLi.className = "kms-health-fail";
      intLi.empty();
      intLi.createSpan({ text: "\u2014 " });
      intLi.createSpan({ text: `${t("wizEnvIntegrity")}: ` });
      intLi.createEl("code", { text: t("wizEnvSkip") });
    }

    const allOk = this.checks.python && this.checks.config;
    if (!allOk) {
      const hint = body.createDiv({ cls: "kms-wizard-fix-hint" });
      hint.createEl("p", { text: t("wizEnvFixHint") });
      const fixBtn = hint.createEl("button", { text: t("wizOpenSettings"), cls: "mod-cta" });
      fixBtn.addEventListener("click", () => {
        this.close();
        this.app.setting.open();
        this.app.setting.openTabById("kms-review");
      });
    }

    this._navButtons(body, { showBack: true, nextLabel: allOk ? t("next") : t("nextAnyway") });
  }

  // ── Step 3: Inbox ──
  _stepInbox(body) {
    const t = (k, ...a) => _t(this.plugin.settings, k, ...a);
    body.createEl("h3", { text: t("wizInboxTitle") });

    const inboxFolder = this.app.vault.getAbstractFileByPath("00_Inbox");
    let fileCount = 0;
    if (inboxFolder) {
      const countRecursive = (folder) => {
        if (!folder.children) return 0;
        let n = 0;
        for (const child of folder.children) {
          if (child.children) n += countRecursive(child);
          else if (!child.name.startsWith(".") && !child.name.startsWith("_") && child.extension) n++;
        }
        return n;
      };
      fileCount = countRecursive(inboxFolder);
    }
    this.inboxCount = fileCount;

    if (fileCount > 0) {
      body.createEl("p", { cls: "kms-wizard-good", text: t("wizInboxFound", fileCount) });
    } else {
      body.createEl("p", { text: t("wizInboxEmpty") });
      const tips = body.createEl("ul", { cls: "kms-wizard-features" });
      for (const tip of t("wizInboxTips")) {
        tips.createEl("li", { text: tip });
      }
      body.createEl("p", { cls: "kms-wizard-hint", text: t("wizInboxLater") });
    }

    this._navButtons(body, {
      showBack: true,
      nextLabel: fileCount > 0 ? t("runScan") : t("next"),
      nextAction: fileCount > 0 ? () => { this.step = 4; this._renderStep(); } : () => { this.step = 5; this._renderStep(); },
    });
  }

  // ── Step 4: First pipeline run ──
  async _stepFirstRun(body) {
    const t = (k, ...a) => _t(this.plugin.settings, k, ...a);
    body.createEl("h3", { text: t("wizScanTitle") });
    body.createEl("p", { text: t("wizScanIntro", this.inboxCount) });

    const progress = body.createEl("ul", { cls: "kms-progress-list" });
    const steps = [
      { label: t("scanning"), cmd: "scan_inbox" },
      { label: t("generating"), cmd: "make_review_queue" },
      { label: t("updatingDash"), cmd: "generate_dashboard" },
    ];

    const lis = [];
    for (const s of steps) {
      const li = progress.createEl("li", { cls: "kms-progress-step kms-step-pending" });
      li.createSpan({ cls: "kms-progress-icon", text: "\u25cb" });
      li.createSpan({ cls: "kms-progress-label", text: s.label });
      li.createSpan({ cls: "kms-progress-time" });
      lis.push(li);
    }

    const footer = body.createDiv({ cls: "kms-wizard-footer" });
    const python = this.plugin._getPython();
    const projectRoot = this.plugin._getProjectRoot();

    let failed = false;
    for (let i = 0; i < steps.length; i++) {
      const li = lis[i];
      li.className = "kms-progress-step kms-step-running";
      li.querySelector(".kms-progress-icon").textContent = "\u25c9";
      const start = Date.now();
      try {
        await this.plugin._exec(`"${python}" -m kms.scripts.${steps[i].cmd}`, projectRoot);
        const elapsed = ((Date.now() - start) / 1000).toFixed(1);
        li.className = "kms-progress-step kms-step-done";
        li.querySelector(".kms-progress-icon").textContent = "\u2713";
        li.querySelector(".kms-progress-time").textContent = `${elapsed}s`;
      } catch (err) {
        const elapsed = ((Date.now() - start) / 1000).toFixed(1);
        li.className = "kms-progress-step kms-step-error";
        li.querySelector(".kms-progress-icon").textContent = "\u2717";
        li.querySelector(".kms-progress-time").textContent = `${elapsed}s`;
        footer.createEl("pre", { cls: "kms-progress-error-detail", text: err.message.slice(-400) });
        failed = true;
        break;
      }
    }

    if (!failed) {
      footer.createEl("p", { cls: "kms-wizard-good", text: t("wizScanDone") });
    } else {
      const btnRow = footer.createDiv({ cls: "kms-wizard-actions" });
      const retryBtn = btnRow.createEl("button", { text: t("wizRetry"), cls: "mod-cta" });
      retryBtn.addEventListener("click", () => { this.step = 4; this._renderStep(); });
      const skipBtn = btnRow.createEl("button", { text: t("wizFinishAnyway") });
      skipBtn.addEventListener("click", () => { this.step = 5; this._renderStep(); });
    }

    if (!failed) {
      this._navButtons(body, { showBack: false, nextLabel: t("next"), nextAction: () => { this.step = 5; this._renderStep(); } });
    }
  }

  // ── Step 5: Help / How-To ──
  _stepHelp(body) {
    const t = (k, ...a) => _t(this.plugin.settings, k, ...a);
    body.createEl("h3", { text: t("helpTitle") });
    body.createEl("p", { text: t("helpIntro") });

    // ── Quick Reference: collapsible sections ──
    const sections = t("helpSections");
    for (const section of sections) {
      const details = body.createEl("details", { cls: "kms-help-section" });
      const summary = details.createEl("summary", { cls: "kms-help-summary" });
      summary.createSpan({ cls: "kms-help-icon", text: section.icon });
      summary.createSpan({ text: section.title });

      const content = details.createDiv({ cls: "kms-help-content" });
      for (const item of section.items) {
        const row = content.createDiv({ cls: "kms-help-item" });
        row.createEl("strong", { text: item.label });
        row.createEl("span", { text: ` — ${item.desc}` });
      }
    }

    // ── Keyboard Shortcuts ──
    const kbSection = body.createEl("details", { cls: "kms-help-section" });
    const kbSummary = kbSection.createEl("summary", { cls: "kms-help-summary" });
    kbSummary.createSpan({ cls: "kms-help-icon", text: "\u2328" });
    kbSummary.createSpan({ text: t("helpKeyboardTitle") });
    const kbContent = kbSection.createDiv({ cls: "kms-help-content" });
    for (const kb of t("helpKeyboard")) {
      const row = kbContent.createDiv({ cls: "kms-help-item" });
      row.createEl("kbd", { text: kb.key, cls: "kms-help-kbd" });
      row.createEl("span", { text: ` ${kb.desc}` });
    }

    // ── Vault Structure ──
    const structSection = body.createEl("details", { cls: "kms-help-section" });
    const structSummary = structSection.createEl("summary", { cls: "kms-help-summary" });
    structSummary.createSpan({ cls: "kms-help-icon", text: "\ud83d\udcc1" });
    structSummary.createSpan({ text: t("helpStructureTitle") });
    const structContent = structSection.createDiv({ cls: "kms-help-content" });
    structContent.createEl("pre", { cls: "kms-help-tree", text: t("helpStructureTree") });

    // ── Links to docs ──
    body.createEl("p", { cls: "kms-help-docs-hint", text: t("helpDocsHint") });

    // ── Finish ──
    const row = body.createDiv({ cls: "kms-wizard-actions" });
    const openRQ = row.createEl("button", { text: t("openReviewQueue"), cls: "mod-cta" });
    openRQ.addEventListener("click", () => { this._finish(); this.plugin._openFile(REVIEW_QUEUE_FILENAME); });
    const openDash = row.createEl("button", { text: t("openDashboard") });
    openDash.addEventListener("click", () => { this._finish(); this.plugin._openFile(DASHBOARD_FILENAME); });
    const finishBtn = row.createEl("button", { text: t("finish") });
    finishBtn.addEventListener("click", () => this._finish());
  }

  // ── Helpers ──
  _checkItem(list, ok, label, detail) {
    const cls = ok === null ? "kms-health-pending" : ok ? "kms-health-ok" : "kms-health-fail";
    const icon = ok === null ? "\u2026 " : ok ? "\u2713 " : "\u2717 ";
    const li = list.createEl("li", { cls });
    li.createSpan({ text: icon });
    li.createSpan({ text: `${label}: ` });
    li.createEl("code", { text: detail });
    return li;
  }

  _navButtons(body, { showBack = true, nextLabel = null, nextAction = null }) {
    const t = (k, ...a) => _t(this.plugin.settings, k, ...a);
    const row = body.createDiv({ cls: "kms-wizard-actions" });
    if (showBack) {
      const back = row.createEl("button", { text: t("back") });
      back.addEventListener("click", () => { this.step--; this._renderStep(); });
    }
    const skipBtn = row.createEl("button", { text: t("skip") });
    skipBtn.addEventListener("click", () => this._finish());
    const next = row.createEl("button", { text: nextLabel || t("next"), cls: "mod-cta" });
    next.addEventListener("click", nextAction || (() => { this.step++; this._renderStep(); }));
  }

  async _finish() {
    this.plugin.settings.onboardingDone = true;
    await this.plugin.saveSettings();
    this.close();
    this.plugin._reloadKmsViews();
    this.plugin._refreshPanel();
  }

  onClose() { this.contentEl.empty(); }
}

// ── Standalone Help Modal (re-accessible from command palette) ──

export class KmsHelpModal extends Modal {
  constructor(app, plugin) {
    super(app);
    this.plugin = plugin;
  }

  onOpen() {
    const { contentEl } = this;
    const t = (k, ...a) => _t(this.plugin.settings, k, ...a);
    contentEl.addClass("kms-wizard-modal");

    contentEl.createEl("h2", { text: t("helpTitle") });
    contentEl.createEl("p", { text: t("helpIntro") });

    // ── Quick Reference ──
    const sections = t("helpSections");
    for (const section of sections) {
      const details = contentEl.createEl("details", { cls: "kms-help-section" });
      const summary = details.createEl("summary", { cls: "kms-help-summary" });
      summary.createSpan({ cls: "kms-help-icon", text: section.icon });
      summary.createSpan({ text: section.title });

      const content = details.createDiv({ cls: "kms-help-content" });
      for (const item of section.items) {
        const row = content.createDiv({ cls: "kms-help-item" });
        row.createEl("strong", { text: item.label });
        row.createEl("span", { text: ` — ${item.desc}` });
      }
    }

    // ── Keyboard Shortcuts ──
    const kbSection = contentEl.createEl("details", { cls: "kms-help-section" });
    const kbSummary = kbSection.createEl("summary", { cls: "kms-help-summary" });
    kbSummary.createSpan({ cls: "kms-help-icon", text: "\u2328" });
    kbSummary.createSpan({ text: t("helpKeyboardTitle") });
    const kbContent = kbSection.createDiv({ cls: "kms-help-content" });
    for (const kb of t("helpKeyboard")) {
      const row = kbContent.createDiv({ cls: "kms-help-item" });
      row.createEl("kbd", { text: kb.key, cls: "kms-help-kbd" });
      row.createEl("span", { text: ` ${kb.desc}` });
    }

    // ── Vault Structure ──
    const structSection = contentEl.createEl("details", { cls: "kms-help-section" });
    const structSummary = structSection.createEl("summary", { cls: "kms-help-summary" });
    structSummary.createSpan({ cls: "kms-help-icon", text: "\ud83d\udcc1" });
    structSummary.createSpan({ text: t("helpStructureTitle") });
    const structContent = structSection.createDiv({ cls: "kms-help-content" });
    structContent.createEl("pre", { cls: "kms-help-tree", text: t("helpStructureTree") });

    contentEl.createEl("p", { cls: "kms-help-docs-hint", text: t("helpDocsHint") });

    const closeRow = contentEl.createDiv({ cls: "kms-wizard-actions" });
    const closeBtn = closeRow.createEl("button", { text: t("close"), cls: "mod-cta" });
    closeBtn.addEventListener("click", () => this.close());
  }

  onClose() { this.contentEl.empty(); }
}
