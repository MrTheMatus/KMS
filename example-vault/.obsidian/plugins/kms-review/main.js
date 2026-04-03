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

const { Plugin, Modal, Notice, MarkdownView, ItemView, PluginSettingTab, Setting } = require("obsidian");
const { exec } = require("child_process");
const path = require("path");
const fs = require("fs");

const REVIEW_QUEUE_FILENAME = "00_Admin/review-queue.md";
const DASHBOARD_FILENAME = "00_Admin/dashboard.md";
const KMS_BEGIN = "<!-- kms:begin -->";
const KMS_END = "<!-- kms:end -->";
const PANEL_VIEW_TYPE = "kms-panel";

const DEFAULT_SETTINGS = {
  pythonPath: "",
  projectRoot: "",
  language: "pl",
  anythingllmEnabled: false,
  anythingllmSlug: "my-workspace",
  onboardingDone: false,
};

// ── i18n ──
const I18N = {
  pl: {
    // Wizard
    wizStep1: "Witaj", wizStep2: "Środowisko", wizStep3: "Inbox", wizStep4: "Pierwszy skan",
    wizTitle: "Witaj w KMS",
    wizIntro: "KMS to system zarządzania wiedzą oparty o Obsidian. Pomaga uporządkować pliki z Inboxu \u2014 AI tworzy propozycje, Ty decydujesz.",
    wizFeatures: [
      "Wrzuć pliki do 00_Inbox/",
      "Plugin skanuje, klasyfikuje i tworzy propozycje",
      "Ty zatwierdzasz, odrzucasz lub odkładasz \u2014 jednym klikiem",
      "Zatwierdzone trafiają do docelowych folderów, odrzucone do archiwum",
    ],
    wizHint: 'Ten kreator sprawdzi konfiguracj\u0119 i przeprowadzi Ci\u0119 przez pierwszy skan.',
    wizEnvTitle: "Sprawdzanie \u015brodowiska",
    wizEnvIntro: "Weryfikuj\u0119 czy wszystko jest gotowe do pracy.",
    wizEnvFixConfig: "Skopiuj config.example.yaml \u2192 config.yaml",
    wizEnvOk: "OK",
    wizEnvIntegrity: "Integralno\u015b\u0107 systemu",
    wizEnvChecking: "Sprawdzam...",
    wizEnvNeedsRepair: "Wymaga naprawy",
    wizEnvFirstRun: "Pierwsze uruchomienie \u2014 to normalne",
    wizEnvSkip: "Pomi\u0144 \u2014 najpierw napraw powy\u017csze",
    wizEnvFixHint: "Popraw problemy powy\u017cej, albo ustaw \u015bcie\u017cki w ustawieniach pluginu:",
    wizOpenSettings: "Otw\u00f3rz ustawienia",
    wizInboxTitle: "Tw\u00f3j Inbox",
    wizInboxFound: (n) => `Znaleziono ${n} plik\u00f3w w 00_Inbox/. Mo\u017cesz uruchomi\u0107 pierwszy skan.`,
    wizInboxEmpty: "00_Inbox/ jest pusty. Wrzu\u0107 tam pliki, kt\u00f3re chcesz przetworzy\u0107:",
    wizInboxTips: ["Pliki PDF (artyku\u0142y, materia\u0142y)", "Pliki Markdown (notatki, fragmenty)", "Eksporty czat\u00f3w z Claude/ChatGPT"],
    wizInboxLater: 'Mo\u017cesz te\u017c uruchomi\u0107 skan p\u00f3\u017aniej \u2014 Ctrl+P \u2192 "KMS: Refresh review queue".',
    wizScanTitle: "Pierwszy skan",
    wizScanIntro: (n) => `Skanuj\u0119 ${n} plik\u00f3w z Inboxu, tworz\u0119 propozycje i generuj\u0119 dashboard.`,
    wizScanDone: "Gotowe! Otw\u00f3rz review queue aby przejrze\u0107 propozycje.",
    wizRetry: "Spr\u00f3buj ponownie",
    wizFinishAnyway: "Zako\u0144cz mimo to",
    // Nav
    back: "\u2190 Wstecz", next: "Dalej \u2192", skip: "Pomi\u0144", finish: "Zako\u0144cz",
    openReviewQueue: "Otw\u00f3rz Review Queue", openDashboard: "Otw\u00f3rz Dashboard",
    runScan: "Uruchom skan \u2192",
    nextAnyway: "Dalej mimo to \u2192",
    // Pipeline
    scanning: "Skanowanie inboxu", generating: "Generowanie kolejki (AI)",
    updatingDash: "Aktualizacja dashboardu", applying: "Stosowanie decyzji",
    refreshingQueue: "Od\u015bwie\u017canie kolejki", retriaging: "Re-klasyfikacja propozycji (LLM)",
    // Bulk
    confirmTitle: "Potwierdzenie",
    confirmYes: "Tak, wykonaj", confirmNo: "Anuluj",
    bulkApproveQ: (n) => `Czy na pewno chcesz zatwierdzi\u0107 ${n} propozycji?`,
    bulkRejectQ: (n) => `Czy na pewno chcesz odrzuci\u0107 ${n} propozycji?`,
    bulkDone: (n, d) => `${n} propozycji ustawionych na ${d}.`,
    noPending: "Brak propozycji pending do zmiany.",
    // Progress
    pipelineDone: "Gotowe!",
    pipelineError: "B\u0142\u0105d pipeline:",
    copyError: "Kopiuj b\u0142\u0105d", close: "Zamknij",
    copied: "Skopiowano do schowka.",
    // Panel
    panelTitle: "KMS Control Panel",
    secPipeline: "Pipeline", secBulk: "Operacje zbiorcze", secNavigate: "Nawigacja", secAdvanced: "Zaawansowane",
    btnRefresh: "Od\u015bwie\u017c kolejk\u0119", btnApply: "Zastosuj decyzje", btnRetriage: "Re-klasyfikacja",
    btnApproveAll: "Zatwierd\u017a wszystkie", btnRejectAll: "Odrzu\u0107 wszystkie",
    btnReviewQueue: "Review queue", btnDashboard: "Dashboard", btnSearch: "Szukaj propozycji",
    btnRevertProposal: "Cofnij propozycj\u0119", btnRevertBatch: "Cofnij batch",
    loadingStats: "\u0141adowanie statystyk...", statsError: "B\u0142\u0105d statystyk:",
    topDomains: "Top domeny",
    tooltipRefresh: "Skan inbox + AI streszczenia + dashboard",
    tooltipApply: "Przenie\u015b zatwierdzone pliki",
    tooltipRetriage: "Re-klasyfikacja domen/temat\u00f3w przez LLM",
    tooltipRevert: "Cofnij pojedyncz\u0105 zaaplikowan\u0105 propozycj\u0119",
    tooltipBatchRevert: "Cofnij ca\u0142\u0105 operacj\u0119 batch",
    // Search
    searchTitle: "Szukaj propozycji KMS",
    searchPlaceholder: "np. Angular, migration, python, debugging...",
    searchOnlyPending: " Tylko pending",
    searchMinChars: "Wpisz min. 2 znaki aby wyszuka\u0107...",
    searchLoading: "Szukam...",
    searchNoResults: (q) => `Brak propozycji pasuj\u0105cych do "${q}".`,
    searchCount: (n) => `${n} wynik${n > 1 ? "\u00f3w" : ""}`,
    goToProposal: "Id\u017a do propozycji",
    openSource: "Otw\u00f3rz \u017ar\u00f3d\u0142o",
    detailsBtn: "Szczeg\u00f3\u0142y",
    // Detail
    detailTitle: (id) => `Propozycja #${id}`,
    detailLoading: "\u0141adowanie...",
    detailNotFound: "Nie znaleziono propozycji.",
    // Revert
    revertTitle: "Cofnij zaaplikowan\u0105 propozycj\u0119",
    revertDesc: "Podaj ID propozycji do cofni\u0119cia. Plik zostanie przeniesiony z powrotem, a rekord wykonania usuni\u0119ty.",
    revertPreview: "Podgl\u0105d (dry-run)",
    revertBtn: "Cofnij",
    reverting: "Cofanie...",
    revertFailed: "Cofanie nie powiod\u0142o si\u0119",
    revertDone: (id) => `Propozycja #${id} cofni\u0119ta.`,
    // Batch revert
    batchRevertTitle: "Cofnij operacj\u0119 batch",
    batchRevertDesc: "Wybierz batch do cofni\u0119cia \u2014 wszystkie propozycje z tej operacji zostan\u0105 cofni\u0119te.",
    batchLoading: "\u0141adowanie batch\u00f3w...",
    noBatches: "Brak aktywnych batch\u00f3w do cofni\u0119cia.",
    activeBatches: (n) => `${n} aktywny${n > 1 ? "ch" : ""} batch${n > 1 ? "\u00f3w" : ""}`,
    revertEntireBatch: "Cofnij ca\u0142y batch",
    batchReverted: (id, n) => `Batch ${id} cofni\u0119ty (${n} propozycji).`,
    batchRevertFailed: "Cofanie batcha nie powiod\u0142o si\u0119:",
    // Settings
    settingsTitle: "KMS Review \u2014 Ustawienia",
    settingPython: "\u015acie\u017cka Python",
    settingPythonDesc: "Pe\u0142na \u015bcie\u017cka do interpretera Python (domy\u015blnie: .venv/bin/python w katalogu projektu)",
    settingProject: "Katalog projektu",
    settingProjectDesc: "\u015acie\u017cka do katalogu g\u0142\u00f3wnego KMS (domy\u015blnie: katalog nadrz\u0119dny vaultu)",
    settingLang: "J\u0119zyk interfejsu",
    settingLangDesc: "J\u0119zyk komunikat\u00f3w w pluginie",
    settingAnythingLLM: "W\u0142\u0105cz AnythingLLM",
    settingAnythingLLMDesc: "Integracja z AnythingLLM dla retrieval i Q&A",
    settingSlug: "Workspace slug",
    settingSlugDesc: "Nazwa workspace w AnythingLLM",
    settingHelp: "Pomoc",
    settingHelpText: 'Otw\u00f3rz <code>docs/workflow.md</code> aby zobaczy\u0107 pe\u0142ny opis pracy z KMS.',
    fileNotFound: (f) => `${f} nie znaleziono. Uruchom pipeline.`,
  },
  en: {
    wizStep1: "Welcome", wizStep2: "Environment", wizStep3: "Inbox", wizStep4: "First scan",
    wizTitle: "Welcome to KMS",
    wizIntro: "KMS is a knowledge management system built on Obsidian. It helps organize files from your Inbox \u2014 AI creates proposals, you decide.",
    wizFeatures: [
      "Drop files into 00_Inbox/",
      "Plugin scans, classifies, and creates proposals",
      "You approve, reject, or postpone \u2014 with one click",
      "Approved files go to target folders, rejected to archive",
    ],
    wizHint: "This wizard will check your configuration and walk you through the first scan.",
    wizEnvTitle: "Environment check",
    wizEnvIntro: "Verifying everything is ready.",
    wizEnvFixConfig: "Copy config.example.yaml \u2192 config.yaml",
    wizEnvOk: "OK",
    wizEnvIntegrity: "System integrity",
    wizEnvChecking: "Checking...",
    wizEnvNeedsRepair: "Needs repair",
    wizEnvFirstRun: "First run \u2014 this is normal",
    wizEnvSkip: "Skip \u2014 fix the above first",
    wizEnvFixHint: "Fix the issues above, or set paths in plugin settings:",
    wizOpenSettings: "Open settings",
    wizInboxTitle: "Your Inbox",
    wizInboxFound: (n) => `Found ${n} files in 00_Inbox/. Ready to run the first scan.`,
    wizInboxEmpty: "00_Inbox/ is empty. Drop files you want to process:",
    wizInboxTips: ["PDF files (articles, materials)", "Markdown files (notes, fragments)", "Chat exports from Claude/ChatGPT"],
    wizInboxLater: 'You can also run the scan later \u2014 Ctrl+P \u2192 "KMS: Refresh review queue".',
    wizScanTitle: "First scan",
    wizScanIntro: (n) => `Scanning ${n} files from Inbox, creating proposals, and generating dashboard.`,
    wizScanDone: "Done! Open the review queue to see proposals.",
    wizRetry: "Try again",
    wizFinishAnyway: "Finish anyway",
    back: "\u2190 Back", next: "Next \u2192", skip: "Skip", finish: "Finish",
    openReviewQueue: "Open Review Queue", openDashboard: "Open Dashboard",
    runScan: "Run scan \u2192",
    nextAnyway: "Next anyway \u2192",
    scanning: "Scanning inbox", generating: "Generating review queue (AI)",
    updatingDash: "Updating dashboard", applying: "Applying decisions",
    refreshingQueue: "Refreshing queue", retriaging: "Re-classifying proposals (LLM)",
    confirmTitle: "Confirm",
    confirmYes: "Yes, proceed", confirmNo: "Cancel",
    bulkApproveQ: (n) => `Approve ${n} pending proposals?`,
    bulkRejectQ: (n) => `Reject ${n} pending proposals?`,
    bulkDone: (n, d) => `${n} proposals set to ${d}.`,
    noPending: "No pending proposals to change.",
    pipelineDone: "Done!",
    pipelineError: "Pipeline error:",
    copyError: "Copy error", close: "Close",
    copied: "Copied to clipboard.",
    // Panel
    panelTitle: "KMS Control Panel",
    secPipeline: "Pipeline", secBulk: "Bulk actions", secNavigate: "Navigate", secAdvanced: "Advanced",
    btnRefresh: "Refresh queue", btnApply: "Apply decisions", btnRetriage: "Retriage all",
    btnApproveAll: "Approve all pending", btnRejectAll: "Reject all pending",
    btnReviewQueue: "Review queue", btnDashboard: "Dashboard", btnSearch: "Search proposals",
    btnRevertProposal: "Revert proposal", btnRevertBatch: "Revert batch",
    loadingStats: "Loading stats...", statsError: "Stats error:",
    topDomains: "Top domains",
    tooltipRefresh: "Scan inbox + AI summaries + dashboard",
    tooltipApply: "Move approved files to targets",
    tooltipRetriage: "Re-classify domains/topics via LLM",
    tooltipRevert: "Revert single applied proposal",
    tooltipBatchRevert: "Undo entire bulk operation",
    // Search
    searchTitle: "Search KMS proposals",
    searchPlaceholder: "e.g. Angular, migration, python, debugging...",
    searchOnlyPending: " Only pending",
    searchMinChars: "Type at least 2 characters to search...",
    searchLoading: "Searching...",
    searchNoResults: (q) => `No proposals matching "${q}".`,
    searchCount: (n) => `${n} result${n > 1 ? "s" : ""}`,
    goToProposal: "Go to proposal",
    openSource: "Open source",
    detailsBtn: "Details",
    // Detail
    detailTitle: (id) => `Proposal #${id}`,
    detailLoading: "Loading...",
    detailNotFound: "Proposal not found.",
    // Revert
    revertTitle: "Revert applied proposal",
    revertDesc: "Enter the proposal ID to revert. This will move the file back to its original location and remove the execution record.",
    revertPreview: "Preview (dry-run)",
    revertBtn: "Revert",
    reverting: "Reverting...",
    revertFailed: "Revert failed",
    revertDone: (id) => `Proposal #${id} reverted.`,
    // Batch revert
    batchRevertTitle: "Revert batch operation",
    batchRevertDesc: "Select a batch to revert all proposals applied in that operation.",
    batchLoading: "Loading batches...",
    noBatches: "No active batches to revert.",
    activeBatches: (n) => `${n} active batch${n > 1 ? "es" : ""}`,
    revertEntireBatch: "Revert entire batch",
    batchReverted: (id, n) => `Batch ${id} reverted (${n} proposals).`,
    batchRevertFailed: "Batch revert failed:",
    // Settings
    settingsTitle: "KMS Review \u2014 Settings",
    settingPython: "Python path",
    settingPythonDesc: "Full path to Python interpreter (default: .venv/bin/python in project dir)",
    settingProject: "Project directory",
    settingProjectDesc: "Path to KMS root directory (default: parent of vault)",
    settingLang: "Interface language",
    settingLangDesc: "Language for plugin messages",
    settingAnythingLLM: "Enable AnythingLLM",
    settingAnythingLLMDesc: "AnythingLLM integration for retrieval and Q&A",
    settingSlug: "Workspace slug",
    settingSlugDesc: "AnythingLLM workspace name",
    settingHelp: "Help",
    settingHelpText: 'Open <code>docs/workflow.md</code> for a full workflow description.',
    fileNotFound: (f) => `${f} not found. Run the pipeline first.`,
  },
};

function _t(settings, key, ...args) {
  const lang = settings?.language || "pl";
  const val = (I18N[lang] || I18N.pl)[key] || (I18N.pl)[key] || key;
  return typeof val === "function" ? val(...args) : val;
}

module.exports = class KmsReviewPlugin extends Plugin {
  async onload() {
    await this.loadSettings();

    this.addSettingTab(new KmsSettingsTab(this.app, this));

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

    this.addCommand({
      id: "run-wizard",
      name: "Run setup wizard",
      callback: () => new KmsOnboardingWizard(this.app, this).open(),
    });

    // ── Ribbon → opens panel ──
    this.addRibbonIcon("layout-dashboard", "KMS Control Panel", () => {
      this._activatePanel();
    });

    if (!this.settings.onboardingDone) {
      this.app.workspace.onLayoutReady(() => this._firstRunHealthCheck());
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
    if (this.settings.projectRoot) return this.settings.projectRoot;
    const vaultPath = this.app.vault.adapter.basePath;
    return path.dirname(vaultPath);
  }

  _getPython() {
    if (this.settings.pythonPath) return this.settings.pythonPath;
    return path.join(this._getProjectRoot(), ".venv", "bin", "python");
  }

  async _runPipeline(mode) {
    const projectRoot = this._getProjectRoot();
    const python = this._getPython();

    const t = (k, ...a) => _t(this.settings, k, ...a);
    const pipelines = {
      refresh: [
        { cmd: `"${python}" -m kms.scripts.scan_inbox`, label: t("scanning") },
        { cmd: `"${python}" -m kms.scripts.make_review_queue --ai-summary`, label: t("generating") },
        { cmd: `"${python}" -m kms.scripts.generate_dashboard`, label: t("updatingDash") },
      ],
      apply: [
        { cmd: `"${python}" -m kms.scripts.apply_decisions`, label: t("applying") },
        { cmd: `"${python}" -m kms.scripts.make_review_queue`, label: t("refreshingQueue") },
        { cmd: `"${python}" -m kms.scripts.generate_dashboard`, label: t("updatingDash") },
      ],
      retriage: [
        { cmd: `"${python}" -m kms.scripts.make_review_queue --retriage --ai-summary`, label: t("retriaging") },
        { cmd: `"${python}" -m kms.scripts.generate_dashboard`, label: t("updatingDash") },
      ],
    };

    const steps = pipelines[mode];
    if (!steps) return;

    const progress = new KmsProgressModal(this.app, this, mode, steps.map((s) => s.label));
    progress.open();

    for (let i = 0; i < steps.length; i++) {
      const step = steps[i];
      progress.setStep(i, "running");
      const start = Date.now();
      try {
        await this._exec(step.cmd, projectRoot);
        progress.setStep(i, "done", Date.now() - start);
      } catch (err) {
        progress.setStep(i, "error", Date.now() - start);
        progress.showError(err.message);
        this._refreshPanel();
        return;
      }
    }

    progress.showDone();
    this._reloadKmsViews();
    this._refreshPanel();
  }

  async _runRevertPipeline(revertCmdLabel, revertCmd) {
    const projectRoot = this._getProjectRoot();
    const python = this._getPython();
    const t = (k, ...a) => _t(this.settings, k, ...a);
    const steps = [
      { cmd: revertCmd, label: revertCmdLabel || t("revertBtn") },
      { cmd: `"${python}" -m kms.scripts.make_review_queue`, label: t("refreshingQueue") },
      { cmd: `"${python}" -m kms.scripts.generate_dashboard`, label: t("updatingDash") },
    ];

    const progress = new KmsProgressModal(this.app, this, "revert", steps.map((s) => s.label));
    progress.open();

    for (let i = 0; i < steps.length; i++) {
      const step = steps[i];
      progress.setStep(i, "running");
      const start = Date.now();
      try {
        await this._exec(step.cmd, projectRoot);
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
      exec(
        cmd,
        {
          cwd: cwd || this._getProjectRoot(),
          timeout: 600000,
          env: { ...process.env, PYTHONPATH: cwd || this._getProjectRoot() },
        },
        (error, stdout, stderr) => {
          if (error) {
            const raw = stderr?.trim() || stdout?.trim() || error.message;
            const tbIdx = raw.lastIndexOf("Traceback");
            const errIdx = raw.lastIndexOf("Error:");
            const relevant = tbIdx >= 0 ? raw.slice(tbIdx) : errIdx >= 0 ? raw.slice(errIdx) : raw;
            reject(new Error(relevant.slice(-800)));
          } else {
            resolve(stdout);
          }
        }
      );
    });
  }

  async _firstRunHealthCheck() {
    new KmsOnboardingWizard(this.app, this).open();
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
      count++;
    }

    const t = (k, ...a) => _t(this.settings, k, ...a);
    if (count === 0) {
      new Notice(t("noPending"));
      return;
    }

    const qKey = decision === "approve" ? "bulkApproveQ" : "bulkRejectQ";
    const confirmed = await new Promise((resolve) => {
      new KmsConfirmModal(this.app, this.plugin || this, t(qKey, count), resolve).open();
    });
    if (!confirmed) return;

    content = await this.app.vault.read(file);
    const freshBlocks = this._splitKmsBlocks(content);
    let applied = 0;
    for (const block of freshBlocks) {
      if (!block.isKms) continue;
      const currentDecision = block.text.match(/decision:\s*(\S+)/);
      if (!currentDecision || currentDecision[1] !== "pending") continue;
      const fieldRegex = /^(decision:\s*)(.*)$/m;
      if (fieldRegex.test(block.text)) {
        block.text = block.text.replace(fieldRegex, `$1${decision}`);
        applied++;
      }
    }

    const newContent = freshBlocks.map((b) => b.text).join("");
    await this.app.vault.modify(file, newContent);
    new Notice(t("bulkDone", applied, decision));
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
      new Notice(_t(this.settings, "fileNotFound", filePath));
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
      { value: "approve", label: "Approve", aria: "Zatwierdź propozycję" },
      { value: "reject", label: "Reject", aria: "Odrzuć propozycję" },
      { value: "postpone", label: "Postpone", aria: "Odłóż propozycję" },
    ]) {
      const btn = btnRow.createEl("button", {
        cls: `kms-decision-btn${parsed.decision === d.value ? ` active-${d.value}` : ""}`,
        text: d.label,
        attr: { "aria-label": `${d.aria} #${parsed.proposal_id}` },
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
    const t = (k, ...a) => _t(this.plugin.settings, k, ...a);

    // ── Header ──
    root.createEl("h4", { cls: "kms-panel-title", text: t("panelTitle") });

    // ── Stats (loaded from dashboard script output) ──
    const statsEl = root.createDiv({ cls: "kms-panel-stats" });
    statsEl.createEl("p", { cls: "kms-search-loading", text: t("loadingStats") });

    this._loadStats(statsEl);

    // ── Action buttons ──
    const section = (title) => {
      const s = root.createDiv({ cls: "kms-panel-section" });
      s.createEl("div", { cls: "kms-panel-section-title", text: title });
      return s;
    };

    // Pipeline
    const pipeSection = section(t("secPipeline"));
    this._actionBtn(pipeSection, t("btnRefresh"), "rotate-cw", t("tooltipRefresh"), () => this.plugin._runPipeline("refresh"));
    this._actionBtn(pipeSection, t("btnApply"), "check-circle", t("tooltipApply"), () => this.plugin._runPipeline("apply"));
    this._actionBtn(pipeSection, t("btnRetriage"), "wand", t("tooltipRetriage"), () => this.plugin._runPipeline("retriage"));

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
        domEl.createEl("div", { cls: "kms-panel-section-title", text: _t(this.plugin.settings, "topDomains") });
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
      el.createEl("p", { cls: "kms-search-error", text: `${_t(this.plugin.settings, "statsError")} ${err.message}` });
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
    const t = (k, ...a) => _t(this.plugin.settings, k, ...a);
    contentEl.addClass("kms-search-modal");
    contentEl.createEl("h3", { text: t("searchTitle") });

    const inputRow = contentEl.createDiv({ cls: "kms-search-input-row" });
    const input = inputRow.createEl("input", {
      cls: "kms-search-input",
      type: "text",
      placeholder: t("searchPlaceholder"),
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
          for (const t of r.topics) topicsEl.createSpan({ cls: "kms-tag", text: t });
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
            if (ok) {
              new Notice(t("revertDone", this.proposalId));
              this.close();
            } else {
              revertBtn.textContent = t("revertFailed");
              revertBtn.disabled = false;
            }
          } catch (err) { revertBtn.textContent = t("revertFailed"); new Notice(`${t("revertFailed")}: ${err.message}`, 10000); revertBtn.disabled = false; }
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
    const t = (k, ...a) => _t(this.plugin.settings, k, ...a);
    contentEl.addClass("kms-revert-modal");
    contentEl.createEl("h3", { text: t("revertTitle") });
    contentEl.createEl("p", { text: t("revertDesc") });

    const inputRow = contentEl.createDiv({ cls: "kms-revert-input-row" });
    const input = inputRow.createEl("input", { cls: "kms-revert-input", type: "number", placeholder: "Proposal ID (e.g. 42)" });
    const previewEl = contentEl.createDiv({ cls: "kms-revert-preview" });

    const btnRow = contentEl.createDiv({ cls: "kms-revert-btn-row" });
    const previewBtn = btnRow.createEl("button", { cls: "kms-search-action-btn kms-action-detail", text: t("revertPreview") });
    const revertBtn = btnRow.createEl("button", { cls: "kms-search-action-btn kms-action-revert", text: t("revertBtn") });
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
      revertBtn.disabled = true; revertBtn.textContent = t("reverting");
      const python = this.plugin._getPython();
      const projectRoot = this.plugin._getProjectRoot();
      try {
        const ok = await this.plugin._runRevertPipeline(
          `${t("revertBtn")} #${pid}`,
          `"${python}" -m kms.scripts.revert_apply --proposal-id ${pid}`,
        );
        if (ok) {
          new Notice(t("revertDone", pid));
          this.close();
        } else {
          revertBtn.textContent = t("revertFailed");
          revertBtn.disabled = false;
        }
      } catch (err) { revertBtn.textContent = t("revertFailed"); new Notice(`${t("revertFailed")}: ${err.message}`, 10000); revertBtn.disabled = false; }
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
    const t = (k, ...a) => _t(this.plugin.settings, k, ...a);
    contentEl.addClass("kms-revert-modal");
    contentEl.createEl("h3", { text: t("batchRevertTitle") });
    contentEl.createEl("p", { text: t("batchRevertDesc") });

    const listEl = contentEl.createDiv({ cls: "kms-search-results" });
    listEl.createEl("p", { cls: "kms-search-loading", text: t("batchLoading") });

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
        listEl.createEl("p", { cls: "kms-search-empty", text: t("noBatches") });
        return;
      }

      listEl.createEl("p", { cls: "kms-search-count", text: t("activeBatches", active.length) });

      for (const b of active) {
        const item = listEl.createDiv({ cls: "kms-search-result" });
        const header = item.createDiv({ cls: "kms-search-result-header" });
        header.createSpan({ cls: "kms-search-pid", text: b.id.slice(0, 8) });
        header.createSpan({ cls: "kms-tag kms-tag-domain", text: b.action });
        header.createSpan({ cls: "kms-search-decision kms-decision-approve", text: `${b.proposal_count} proposals` });

        item.createDiv({ cls: "kms-search-path", text: b.description || "" });
        item.createDiv({ cls: "kms-search-summary", text: `Created: ${(b.created_at || "").replace("T", " ").slice(0, 16)}` });

        const actions = item.createDiv({ cls: "kms-search-actions" });
        const revertBtn = actions.createEl("button", { cls: "kms-search-action-btn kms-action-revert", text: t("revertEntireBatch") });

        revertBtn.addEventListener("click", async () => {
          revertBtn.disabled = true;
          revertBtn.textContent = "Reverting...";
          try {
            const ok = await this.plugin._runRevertPipeline(
              `${t("revertEntireBatch")} ${b.id.slice(0, 8)} (${b.proposal_count})`,
              `"${python}" -m kms.scripts.revert_apply --batch-id "${b.id}"`,
            );
            if (ok) {
              new Notice(t("batchReverted", b.id.slice(0, 8), b.proposal_count));
              this.close();
            } else {
              revertBtn.textContent = t("revertFailed");
              revertBtn.disabled = false;
            }
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

// ════════════════════════════════════════════════════════════════
// Settings Tab
// ════════════════════════════════════════════════════════════════

class KmsSettingsTab extends PluginSettingTab {
  constructor(app, plugin) {
    super(app, plugin);
    this.plugin = plugin;
  }

  display() {
    const { containerEl } = this;
    const t = (k, ...a) => _t(this.plugin.settings, k, ...a);
    containerEl.empty();
    containerEl.createEl("h2", { text: t("settingsTitle") });

    new Setting(containerEl)
      .setName(t("settingPython"))
      .setDesc(t("settingPythonDesc"))
      .addText((text) =>
        text
          .setPlaceholder(".venv/bin/python")
          .setValue(this.plugin.settings.pythonPath)
          .onChange(async (value) => {
            this.plugin.settings.pythonPath = value.trim();
            await this.plugin.saveSettings();
          }),
      );

    new Setting(containerEl)
      .setName(t("settingProject"))
      .setDesc(t("settingProjectDesc"))
      .addText((text) =>
        text
          .setPlaceholder("auto-detect")
          .setValue(this.plugin.settings.projectRoot)
          .onChange(async (value) => {
            this.plugin.settings.projectRoot = value.trim();
            await this.plugin.saveSettings();
          }),
      );

    new Setting(containerEl)
      .setName(t("settingLang"))
      .setDesc(t("settingLangDesc"))
      .addDropdown((dropdown) =>
        dropdown
          .addOption("pl", "Polski")
          .addOption("en", "English")
          .setValue(this.plugin.settings.language)
          .onChange(async (value) => {
            this.plugin.settings.language = value;
            await this.plugin.saveSettings();
          }),
      );

    containerEl.createEl("h3", { text: "AnythingLLM" });

    new Setting(containerEl)
      .setName(t("settingAnythingLLM"))
      .setDesc(t("settingAnythingLLMDesc"))
      .addToggle((toggle) =>
        toggle
          .setValue(this.plugin.settings.anythingllmEnabled)
          .onChange(async (value) => {
            this.plugin.settings.anythingllmEnabled = value;
            await this.plugin.saveSettings();
          }),
      );

    new Setting(containerEl)
      .setName(t("settingSlug"))
      .setDesc(t("settingSlugDesc"))
      .addText((text) =>
        text
          .setPlaceholder("my-workspace")
          .setValue(this.plugin.settings.anythingllmSlug)
          .onChange(async (value) => {
            this.plugin.settings.anythingllmSlug = value.trim();
            await this.plugin.saveSettings();
          }),
      );

    containerEl.createEl("h3", { text: t("settingHelp") });
    const helpLink = containerEl.createEl("p");
    helpLink.innerHTML = t("settingHelpText");
  }
}

// ════════════════════════════════════════════════════════════════
// Onboarding Wizard (first-run)
// ════════════════════════════════════════════════════════════════

class KmsOnboardingWizard extends Modal {
  constructor(app, plugin) {
    super(app);
    this.plugin = plugin;
    this.step = 0;
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

    // Step indicator
    const steps = [t("wizStep1"), t("wizStep2"), t("wizStep3"), t("wizStep4")];
    const indicator = contentEl.createDiv({ cls: "kms-wizard-steps" });
    for (let i = 0; i < steps.length; i++) {
      const dot = indicator.createSpan({
        cls: `kms-wizard-dot${i === this.step ? " active" : i < this.step ? " done" : ""}`,
        text: i < this.step ? "✓" : String(i + 1),
      });
      dot.title = steps[i];
      if (i < steps.length - 1) indicator.createSpan({ cls: "kms-wizard-dot-line" });
    }

    const body = contentEl.createDiv({ cls: "kms-wizard-body" });

    if (this.step === 0) this._stepWelcome(body);
    else if (this.step === 1) this._stepEnvironment(body);
    else if (this.step === 2) this._stepInbox(body);
    else if (this.step === 3) this._stepFirstRun(body);
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

  // ── Step 1: Environment checks ──
  async _stepEnvironment(body) {
    const t = (k, ...a) => _t(this.plugin.settings, k, ...a);
    body.createEl("h3", { text: t("wizEnvTitle") });
    body.createEl("p", { text: t("wizEnvIntro") });

    const list = body.createEl("ul", { cls: "kms-health-list" });
    const pythonPath = this.plugin._getPython();
    const projectRoot = this.plugin._getProjectRoot();
    const configPath = path.join(projectRoot, "kms", "config", "config.yaml");

    // Check 1: Python
    const pythonOk = fs.existsSync(pythonPath);
    this.checks.python = pythonOk;
    this._checkItem(list, pythonOk, "Python", pythonOk ? pythonPath : `Not found: ${pythonPath}`);

    // Check 2: config.yaml
    const configOk = fs.existsSync(configPath);
    this.checks.config = configOk;
    this._checkItem(list, configOk, "config.yaml", configOk ? t("wizEnvOk") : t("wizEnvFixConfig"));

    // Check 3: verify_integrity (async)
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

  // ── Step 2: Inbox ──
  _stepInbox(body) {
    const t = (k, ...a) => _t(this.plugin.settings, k, ...a);
    body.createEl("h3", { text: t("wizInboxTitle") });

    const inboxPath = "00_Inbox";
    const inboxFolder = this.app.vault.getAbstractFileByPath(inboxPath);
    let fileCount = 0;
    if (inboxFolder && inboxFolder.children) {
      fileCount = inboxFolder.children.filter((f) => !f.name.startsWith(".") && f.extension).length;
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
      nextLabel: fileCount > 0 ? t("runScan") : t("finish"),
      nextAction: fileCount > 0 ? () => { this.step = 3; this._renderStep(); } : () => this._finish(),
    });
  }

  // ── Step 3: First pipeline run ──
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
      li.createSpan({ cls: "kms-progress-icon", text: "○" });
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
      li.querySelector(".kms-progress-icon").textContent = "◉";
      const start = Date.now();
      try {
        await this.plugin._exec(`"${python}" -m kms.scripts.${steps[i].cmd}`, projectRoot);
        const elapsed = ((Date.now() - start) / 1000).toFixed(1);
        li.className = "kms-progress-step kms-step-done";
        li.querySelector(".kms-progress-icon").textContent = "✓";
        li.querySelector(".kms-progress-time").textContent = `${elapsed}s`;
      } catch (err) {
        const elapsed = ((Date.now() - start) / 1000).toFixed(1);
        li.className = "kms-progress-step kms-step-error";
        li.querySelector(".kms-progress-icon").textContent = "✗";
        li.querySelector(".kms-progress-time").textContent = `${elapsed}s`;
        footer.createEl("pre", { cls: "kms-progress-error-detail", text: err.message.slice(-400) });
        failed = true;
        break;
      }
    }

    if (!failed) {
      footer.createEl("p", { cls: "kms-wizard-good", text: t("wizScanDone") });
      const btnRow = footer.createDiv({ cls: "kms-wizard-actions" });
      const openBtn = btnRow.createEl("button", { text: t("openReviewQueue"), cls: "mod-cta" });
      openBtn.addEventListener("click", () => {
        this._finish();
        this.plugin._openFile(REVIEW_QUEUE_FILENAME);
      });
      const dashBtn = btnRow.createEl("button", { text: t("openDashboard") });
      dashBtn.addEventListener("click", () => {
        this._finish();
        this.plugin._openFile(DASHBOARD_FILENAME);
      });
    } else {
      const btnRow = footer.createDiv({ cls: "kms-wizard-actions" });
      const retryBtn = btnRow.createEl("button", { text: t("wizRetry"), cls: "mod-cta" });
      retryBtn.addEventListener("click", () => { this.step = 3; this._renderStep(); });
      const skipBtn = btnRow.createEl("button", { text: t("wizFinishAnyway") });
      skipBtn.addEventListener("click", () => this._finish());
    }
  }

  // ── Helpers ──
  _checkItem(list, ok, label, detail) {
    const cls = ok === null ? "kms-health-pending" : ok ? "kms-health-ok" : "kms-health-fail";
    const icon = ok === null ? "… " : ok ? "✓ " : "✗ ";
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

// ════════════════════════════════════════════════════════════════
// Confirm Modal (for destructive bulk ops)
// ════════════════════════════════════════════════════════════════

class KmsConfirmModal extends Modal {
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

// ════════════════════════════════════════════════════════════════
// Progress Modal (for pipeline steps)
// ════════════════════════════════════════════════════════════════

class KmsProgressModal extends Modal {
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
      li.createSpan({ cls: "kms-progress-icon", text: "○" });
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
    if (state === "running") icon.textContent = "◉";
    else if (state === "done") icon.textContent = "✓";
    else if (state === "error") icon.textContent = "✗";
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
