var __defProp = Object.defineProperty;
var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
var __getOwnPropNames = Object.getOwnPropertyNames;
var __hasOwnProp = Object.prototype.hasOwnProperty;
var __export = (target, all) => {
  for (var name in all)
    __defProp(target, name, { get: all[name], enumerable: true });
};
var __copyProps = (to, from, except, desc) => {
  if (from && typeof from === "object" || typeof from === "function") {
    for (let key of __getOwnPropNames(from))
      if (!__hasOwnProp.call(to, key) && key !== except)
        __defProp(to, key, { get: () => from[key], enumerable: !(desc = __getOwnPropDesc(from, key)) || desc.enumerable });
  }
  return to;
};
var __toCommonJS = (mod) => __copyProps(__defProp({}, "__esModule", { value: true }), mod);

// src/main.js
var main_exports = {};
__export(main_exports, {
  default: () => KmsReviewPlugin
});
module.exports = __toCommonJS(main_exports);
var import_obsidian5 = require("obsidian");

// src/constants.js
var REVIEW_QUEUE_FILENAME = "00_Admin/review-queue.md";
var DASHBOARD_FILENAME = "00_Admin/dashboard.md";
var KMS_BEGIN = "<!-- kms:begin -->";
var KMS_END = "<!-- kms:end -->";
var PANEL_VIEW_TYPE = "kms-panel";
var DEFAULT_SETTINGS = {
  pythonPath: "",
  projectRoot: "",
  language: "pl",
  profile: "core",
  anythingllmEnabled: false,
  anythingllmUrl: "http://localhost:3001",
  anythingllmSlug: "my-workspace",
  anythingllmApiKey: "",
  onboardingDone: false
};

// src/i18n.js
var I18N = {
  pl: {
    // Wizard
    wizStep1: "Witaj",
    wizStep2: "\u015Arodowisko",
    wizStep3: "Inbox",
    wizStep4: "Pierwszy skan",
    wizTitle: "Witaj w KMS",
    wizIntro: "KMS to system zarz\u0105dzania wiedz\u0105 oparty o Obsidian. Pomaga uporz\u0105dkowa\u0107 pliki z Inboxu \u2014 AI tworzy propozycje, Ty decydujesz.",
    wizFeatures: [
      "Wrzu\u0107 pliki do 00_Inbox/",
      "Plugin skanuje, klasyfikuje i tworzy propozycje",
      "Ty zatwierdzasz, odrzucasz lub odk\u0142adasz \u2014 jednym klikni\u0119ciem",
      "Zatwierdzone trafiaj\u0105 do docelowych folder\xF3w, odrzucone do archiwum"
    ],
    wizHint: "Ten kreator sprawdzi konfiguracj\u0119 i przeprowadzi Ci\u0119 przez pierwszy skan.",
    wizEnvTitle: "Sprawdzanie \u015Brodowiska",
    wizEnvIntro: "Weryfikuj\u0119 czy wszystko jest gotowe do pracy.",
    wizEnvFixConfig: "Skopiuj config.example.yaml \u2192 config.yaml",
    wizEnvOk: "OK",
    wizEnvIntegrity: "Integralno\u015B\u0107 systemu",
    wizEnvChecking: "Sprawdzam...",
    wizEnvNeedsRepair: "Wymaga naprawy",
    wizEnvFirstRun: "Pierwsze uruchomienie \u2014 to normalne",
    wizEnvSkip: "Pomi\u0144 \u2014 najpierw napraw powy\u017Csze",
    wizEnvFixHint: "Popraw problemy powy\u017Cej, albo ustaw \u015Bcie\u017Cki w ustawieniach pluginu:",
    wizOpenSettings: "Otw\xF3rz ustawienia",
    wizInboxTitle: "Tw\xF3j Inbox",
    wizInboxFound: (n) => `Znaleziono ${n} plik\xF3w w 00_Inbox/. Mo\u017Cesz uruchomi\u0107 pierwszy skan.`,
    wizInboxEmpty: "00_Inbox/ jest pusty. Wrzu\u0107 tam pliki, kt\xF3re chcesz przetworzy\u0107:",
    wizInboxTips: ["Pliki PDF (artyku\u0142y, materia\u0142y)", "Pliki Markdown (notatki, fragmenty)", "Eksporty czat\xF3w z Claude/ChatGPT"],
    wizInboxLater: 'Mo\u017Cesz te\u017C uruchomi\u0107 skan p\xF3\u017Aniej \u2014 Ctrl+P \u2192 "KMS: Refresh review queue".',
    wizScanTitle: "Pierwszy skan",
    wizScanIntro: (n) => `Skanuj\u0119 ${n} plik\xF3w z Inboxu, tworz\u0119 propozycje i generuj\u0119 dashboard.`,
    wizScanDone: "Gotowe! Otw\xF3rz review queue aby przejrze\u0107 propozycje.",
    wizRetry: "Spr\xF3buj ponownie",
    wizFinishAnyway: "Zako\u0144cz mimo to",
    // Wizard profile
    wizProfileTitle: "Profil u\u017Cytkowania",
    wizProfileIntro: "Wybierz profil, kt\xF3ry najlepiej pasuje do Twojego sposobu pracy:",
    profileCore: "Core",
    profileCoreDesc: "Podstawowy pipeline: skan \u2192 review \u2192 apply. Bez AI.",
    profileAiLocal: "AI \u2014 lokalnie",
    profileAiLocalDesc: "Streszczenia i klasyfikacja przez lokalne modele (Ollama).",
    profileAiCloud: "AI \u2014 chmura",
    profileAiCloudDesc: "Streszczenia i klasyfikacja przez API chmurowe (OpenAI, Anthropic).",
    wizStepHelp: "Pomoc",
    // Help / How-To
    helpTitle: "Jak korzysta\u0107 z KMS",
    helpIntro: "Skr\xF3cona instrukcja obs\u0142ugi \u2014 kliknij sekcj\u0119, aby j\u0105 rozwin\u0105\u0107.",
    helpSections: [
      {
        icon: "\u{1F680}",
        title: "Codzienny workflow",
        items: [
          { label: "1. Wrzu\u0107 pliki do 00_Inbox/", desc: "PDF, Markdown, eksporty czat\xF3w" },
          { label: "2. Ctrl+P \u2192 \u201EKMS: Refresh review queue\u201D", desc: "Skanuje inbox, tworzy propozycje, generuje dashboard" },
          { label: "3. Otw\xF3rz review-queue.md", desc: "Kliknij Zatwierd\u017A / Odrzu\u0107 / Od\u0142\xF3\u017C przy ka\u017Cdej propozycji" },
          { label: "4. Ctrl+P \u2192 \u201EKMS: Apply decisions\u201D", desc: "Przenosi zatwierdzone pliki do docelowych folder\xF3w" }
        ]
      },
      {
        icon: "\u{1F50D}",
        title: "Przydatne komendy",
        items: [
          { label: "Search proposals", desc: "Szukaj propozycji po tek\u015Bcie, domenie, temacie" },
          { label: "Retriage all", desc: "Re-klasyfikacja domen/temat\xF3w przez LLM" },
          { label: "Revert proposal", desc: "Cofnij pojedyncz\u0105 zaaplikowan\u0105 propozycj\u0119" },
          { label: "Revert batch", desc: "Cofnij ca\u0142\u0105 operacj\u0119 zbiorczego zatwierdzenia" },
          { label: "Ask knowledge base", desc: "Zapytaj AnythingLLM o informacje z bazy wiedzy" },
          { label: "Run setup wizard", desc: "Uruchom ponownie ten kreator" }
        ]
      },
      {
        icon: "\u2699\uFE0F",
        title: "Profile",
        items: [
          { label: "Core", desc: "Podstawowy pipeline bez AI" },
          { label: "AI \u2014 lokalnie", desc: "Streszczenia i klasyfikacja przez Ollama" },
          { label: "AI \u2014 chmura", desc: "Streszczenia i klasyfikacja przez OpenAI / Anthropic" }
        ]
      }
    ],
    helpKeyboardTitle: "Skr\xF3ty klawiszowe",
    helpKeyboard: [
      { key: "Ctrl+P", desc: "Paleta komend \u2014 wpisz \u201EKMS\u201D aby zobaczy\u0107 wszystkie komendy" },
      { key: "Ctrl+Shift+R", desc: "Mo\u017Cesz przypisac do Refresh review queue" },
      { key: "Ctrl+Shift+A", desc: "Mo\u017Cesz przypisac do Apply decisions" }
    ],
    helpStructureTitle: "Struktura vaultu",
    helpStructureTree: "00_Admin/\n  review-queue.md    \u2190 propozycje do przegl\u0105du\n  dashboard.md       \u2190 statystyki\n00_Inbox/              \u2190 WRZUCAJ PLIKI TUTAJ\n10_Sources/\n  web/               \u2190 zatwierdzone notatki web\n  pdf/               \u2190 zatwierdzone PDF-y\n20_Source-Notes/       \u2190 wygenerowane notatki \u017Ar\xF3d\u0142owe\n30_Permanent-Notes/    \u2190 Twoja kanonowa baza wiedzy\n80_Archive/            \u2190 odrzucone pliki",
    helpDocsHint: "Pe\u0142na dokumentacja: docs/USAGE.md, docs/INSTALL.md, docs/gateway.md",
    // Nav
    back: "\u2190 Wstecz",
    next: "Dalej \u2192",
    skip: "Pomi\u0144",
    finish: "Zako\u0144cz",
    openReviewQueue: "Otw\xF3rz Review Queue",
    openDashboard: "Otw\xF3rz Dashboard",
    runScan: "Uruchom skan \u2192",
    nextAnyway: "Dalej mimo to \u2192",
    // Pipeline
    scanning: "Skanowanie inboxu",
    generating: "Generowanie kolejki (AI)",
    updatingDash: "Aktualizacja dashboardu",
    applying: "Stosowanie decyzji",
    refreshingQueue: "Od\u015Bwie\u017Canie kolejki",
    retriaging: "Re-klasyfikacja propozycji (LLM)",
    // Bulk
    bulkTitle: "Operacja zbiorcza",
    confirmTitle: "Potwierdzenie",
    confirmYes: "Tak, wykonaj",
    confirmNo: "Anuluj",
    bulkApproveQ: (n) => `Czy na pewno chcesz zatwierdzi\u0107 ${n} propozycji?`,
    bulkRejectQ: (n) => `Czy na pewno chcesz odrzuci\u0107 ${n} propozycji?`,
    bulkDone: (n, d) => `${n} propozycji ustawionych na ${d}.`,
    noPending: "Brak propozycji pending do zmiany.",
    applyHint: "Uruchom \u201EZastosuj decyzje\u201D aby przenie\u015B\u0107 pliki.",
    // Progress
    pipelineDone: "Gotowe!",
    pipelineError: "B\u0142\u0105d pipeline:",
    copyError: "Kopiuj b\u0142\u0105d",
    close: "Zamknij",
    copied: "Skopiowano do schowka.",
    // Panel
    panelTitle: "KMS Control Panel",
    secPipeline: "Pipeline",
    secBulk: "Operacje zbiorcze",
    secNavigate: "Nawigacja",
    secAdvanced: "Zaawansowane",
    btnRefresh: "Od\u015Bwie\u017C kolejk\u0119",
    btnApply: "Zastosuj decyzje",
    btnRetriage: "Re-klasyfikacja",
    btnApproveAll: "Zatwierd\u017A wszystkie",
    btnRejectAll: "Odrzu\u0107 wszystkie",
    btnReviewQueue: "Review queue",
    btnDashboard: "Dashboard",
    btnSearch: "Szukaj propozycji",
    btnRevertProposal: "Cofnij propozycj\u0119",
    btnRevertBatch: "Cofnij batch",
    btnSettings: "Ustawienia",
    btnHelp: "Pomoc",
    btnAskLlm: "Zapytaj baz\u0119 wiedzy",
    tooltipAskLlm: "Zapytaj AnythingLLM o Twoje notatki",
    loadingStats: "\u0141adowanie statystyk...",
    statsError: "B\u0142\u0105d statystyk:",
    topDomains: "Top domeny",
    tooltipRefresh: "Skan inbox + AI streszczenia + dashboard",
    tooltipApply: "Przenie\u015B zatwierdzone pliki",
    tooltipRetriage: "Re-klasyfikacja domen/temat\xF3w przez LLM",
    tooltipRevert: "Cofnij pojedyncz\u0105 zaaplikowan\u0105 propozycj\u0119",
    tooltipBatchRevert: "Cofnij ca\u0142\u0105 operacj\u0119 batch",
    // Search
    searchTitle: "Szukaj propozycji KMS",
    searchPlaceholder: "np. Angular, migration, python, debugging...",
    searchOnlyPending: " Tylko pending",
    searchMinChars: "Wpisz min. 2 znaki aby wyszuka\u0107...",
    searchLoading: "Szukam...",
    searchNoResults: (q) => `Brak propozycji pasuj\u0105cych do "${q}".`,
    searchCount: (n) => `${n} wynik${n > 1 ? "\xF3w" : ""}`,
    goToProposal: "Id\u017A do propozycji",
    openSource: "Otw\xF3rz \u017Ar\xF3d\u0142o",
    detailsBtn: "Szczeg\xF3\u0142y",
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
    batchLoading: "\u0141adowanie batch\xF3w...",
    noBatches: "Brak aktywnych batch\xF3w do cofni\u0119cia.",
    activeBatches: (n) => `${n} aktywny${n > 1 ? "ch" : ""} batch${n > 1 ? "\xF3w" : ""}`,
    revertEntireBatch: "Cofnij ca\u0142y batch",
    batchReverted: (id, n) => `Batch ${id} cofni\u0119ty (${n} propozycji).`,
    batchRevertFailed: "Cofanie batcha nie powiod\u0142o si\u0119:",
    // Settings
    settingsTitle: "KMS Review \u2014 Ustawienia",
    settingPython: "\u015Acie\u017Cka Python",
    settingPythonDesc: "Pe\u0142na \u015Bcie\u017Cka do interpretera Python (domy\u015Blnie: .venv/bin/python w katalogu projektu)",
    settingProject: "Katalog projektu",
    settingProjectDesc: "\u015Acie\u017Cka do katalogu g\u0142\xF3wnego KMS (domy\u015Blnie: katalog nadrz\u0119dny vaultu)",
    settingLang: "J\u0119zyk interfejsu",
    settingLangDesc: "J\u0119zyk komunikat\xF3w w pluginie",
    settingProfile: "Profil",
    settingProfileDesc: "Okre\u015Bla widoczno\u015B\u0107 zaawansowanych opcji",
    settingAnythingLLMHeader: "AnythingLLM",
    settingAnythingLLM: "W\u0142\u0105cz AnythingLLM",
    settingAnythingLLMDesc: "Integracja z AnythingLLM dla retrieval i Q&A",
    settingAnythingLLMUrl: "URL AnythingLLM",
    settingAnythingLLMUrlDesc: "Adres serwera AnythingLLM",
    settingSlug: "Workspace slug",
    settingSlugDesc: "Nazwa workspace w AnythingLLM",
    settingApiKey: "API Key",
    settingApiKeyDesc: "Klucz API AnythingLLM (znajdziesz w AnythingLLM \u2192 Settings \u2192 API Keys)",
    settingHelp: "Pomoc",
    settingHelpText: "Otw\xF3rz <code>docs/workflow.md</code> aby zobaczy\u0107 pe\u0142ny opis pracy z KMS.",
    // Stats
    statTotal: "Razem",
    statPending: "Oczekuj\u0105ce",
    statApproved: "Zatwierdzone",
    statApplied: "Zastosowane",
    statRejected: "Odrzucone",
    statPostpone: "Od\u0142o\u017Cone",
    // Detail sections
    detailStatus: "Status",
    detailClassification: "Klasyfikacja",
    detailPaths: "\u015Acie\u017Cki",
    detailAppliedSection: "Zastosowanie",
    detailSummarySection: "Streszczenie",
    // Detail fields
    fieldDecision: "Decyzja",
    fieldLifecycle: "Cykl \u017Cycia",
    fieldItemStatus: "Status elementu",
    fieldConfidence: "Pewno\u015B\u0107",
    fieldReviewer: "Recenzent",
    fieldReviewNote: "Notatka",
    fieldDecidedAt: "Zdecydowano",
    fieldDomain: "Domena",
    fieldTopics: "Tematy",
    fieldKind: "Rodzaj",
    fieldSuggestedAction: "Sugerowana akcja",
    fieldTarget: "Cel",
    fieldOverrideTarget: "Nadpisany cel",
    fieldSource: "\u0179r\xF3d\u0142o",
    fieldSourceNote: "Notatka \u017Ar\xF3d\u0142owa",
    fieldCreated: "Utworzono",
    fieldAppliedAt: "Zastosowano",
    fieldIndexStatus: "Status indeksu",
    fieldExecutionId: "ID wykonania",
    fieldRevertedAt: "Cofni\u0119to",
    // Revert helpers
    revertPlaceholder: "ID propozycji (np. 42)",
    revertInvalidId: "Podaj prawid\u0142owe ID propozycji.",
    revertDryRun: "Podgl\u0105d (dry-run)...",
    revertNotFound: (id) => `Propozycja #${id} nie znaleziona.`,
    revertAlreadyReverted: (id) => `Propozycja #${id} zosta\u0142a ju\u017C cofni\u0119ta.`,
    revertNotApplied: (id) => `Propozycja #${id} nie zosta\u0142a jeszcze zastosowana.`,
    revertWillRevert: (path3, action, target) => `Cofni\u0119cie: ${path3} (${action} \u2192 ${target})`,
    revertAppliedAtLabel: (at) => `Zastosowano: ${at || "nieznane"}`,
    // Review block
    proposalTitle: (id) => `Propozycja #${id}`,
    clickToViewDetails: "Kliknij aby zobaczy\u0107 szczeg\xF3\u0142y",
    reviewNotePlaceholder: "Notatka recenzenta (opcjonalnie)...",
    btnApprove: "Zatwierd\u017A",
    btnReject: "Odrzu\u0107",
    btnPostpone: "Od\u0142\xF3\u017C",
    ariaApprove: (id) => `Zatwierd\u017A propozycj\u0119 #${id}`,
    ariaReject: (id) => `Odrzu\u0107 propozycj\u0119 #${id}`,
    ariaPostpone: (id) => `Od\u0142\xF3\u017C propozycj\u0119 #${id}`,
    // Batch list
    batchProposalCount: (n) => `${n} propozycji`,
    batchCreatedLabel: (at) => `Utworzono: ${at}`,
    // Ask LLM
    askTitle: "Zapytaj baz\u0119 wiedzy",
    askDesc: "Zadaj pytanie \u2014 AnythingLLM przeszuka Twoje notatki i odpowie na podstawie bazy wiedzy.",
    askPlaceholder: "np. Jak dzia\u0142a move semantics w C++?",
    askSend: "Zapytaj",
    askLoading: "Szukam odpowiedzi...",
    askAnswer: "Odpowied\u017A",
    askSources: "\u0179r\xF3d\u0142a",
    askErrorTitle: "B\u0142\u0105d AnythingLLM",
    askError: (msg) => `B\u0142\u0105d AnythingLLM: ${msg}`,
    askNoApiKey: "Brak klucza API. Ustaw API Key w ustawieniach pluginu (sekcja AnythingLLM).",
    askNoAnythingLLM: "W\u0142\u0105cz AnythingLLM w ustawieniach pluginu.",
    askHistoryHint: (url) => `Historia czat\xF3w i eksport \u2192 ${url}`,
    askHistoryBtn: "Otw\xF3rz histori\u0119 czat\xF3w",
    askVaultTitle: "Znalezione w vault (keyword search)",
    askVaultDesc: "Zaznacz pliki, by do\u0142\u0105czy\u0107 ich tre\u015B\u0107 jako kontekst i zapyta\u0107 ponownie.",
    askVaultEmpty: "Brak dodatkowych trafie\u0144 w vault.",
    askReaskWithContext: "Zapytaj ponownie z kontekstem \u21BB",
    askContextBadge: "\u2726 wzbogacone kontekstem z vault",
    // Contradiction
    contradictionWarning: "\u26A0 Sprzeczno\u015B\u0107 z istniej\u0105c\u0105 wiedz\u0105",
    contradictionLabel: "Sprzeczno\u015B\u0107",
    // Errors
    searchErrorMsg: (msg) => `B\u0142\u0105d wyszukiwania: ${msg}`,
    detailErrorMsg: (msg) => `B\u0142\u0105d \u0142adowania szczeg\xF3\u0142\xF3w: ${msg}`,
    reviewQueueNotFound: "review-queue.md nie znaleziono.",
    proposalDecision: (id, d) => `Propozycja #${id}: ${d}`,
    fileNotFound: (f) => `${f} nie znaleziono. Uruchom pipeline.`
  },
  en: {
    wizStep1: "Welcome",
    wizStep2: "Environment",
    wizStep3: "Inbox",
    wizStep4: "First scan",
    wizTitle: "Welcome to KMS",
    wizIntro: "KMS is a knowledge management system built on Obsidian. It helps organize files from your Inbox \u2014 AI creates proposals, you decide.",
    wizFeatures: [
      "Drop files into 00_Inbox/",
      "Plugin scans, classifies, and creates proposals",
      "You approve, reject, or postpone \u2014 with one click",
      "Approved files go to target folders, rejected to archive"
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
    wizProfileTitle: "Usage profile",
    wizProfileIntro: "Choose the profile that best fits your workflow:",
    profileCore: "Core",
    profileCoreDesc: "Basic pipeline: scan \u2192 review \u2192 apply. No AI.",
    profileAiLocal: "AI \u2014 local",
    profileAiLocalDesc: "Summaries and classification via local models (Ollama).",
    profileAiCloud: "AI \u2014 cloud",
    profileAiCloudDesc: "Summaries and classification via cloud API (OpenAI, Anthropic).",
    wizStepHelp: "Help",
    // Help / How-To
    helpTitle: "How to use KMS",
    helpIntro: "Quick reference guide \u2014 click a section to expand it.",
    helpSections: [
      {
        icon: "\u{1F680}",
        title: "Daily workflow",
        items: [
          { label: "1. Drop files into 00_Inbox/", desc: "PDFs, Markdown, chat exports" },
          { label: '2. Ctrl+P \u2192 "KMS: Refresh review queue"', desc: "Scans inbox, creates proposals, generates dashboard" },
          { label: "3. Open review-queue.md", desc: "Click Approve / Reject / Postpone for each proposal" },
          { label: '4. Ctrl+P \u2192 "KMS: Apply decisions"', desc: "Moves approved files to target folders" }
        ]
      },
      {
        icon: "\u{1F50D}",
        title: "Useful commands",
        items: [
          { label: "Search proposals", desc: "Search proposals by text, domain, topic" },
          { label: "Retriage all", desc: "Re-classify domains/topics via LLM" },
          { label: "Revert proposal", desc: "Undo a single applied proposal" },
          { label: "Revert batch", desc: "Undo an entire bulk approval operation" },
          { label: "Ask knowledge base", desc: "Ask AnythingLLM about your knowledge base" },
          { label: "Run setup wizard", desc: "Re-run this wizard" }
        ]
      },
      {
        icon: "\u2699\uFE0F",
        title: "Profiles",
        items: [
          { label: "Core", desc: "Basic pipeline without AI" },
          { label: "AI \u2014 local", desc: "Summaries and classification via Ollama" },
          { label: "AI \u2014 cloud", desc: "Summaries and classification via OpenAI / Anthropic" }
        ]
      }
    ],
    helpKeyboardTitle: "Keyboard shortcuts",
    helpKeyboard: [
      { key: "Ctrl+P", desc: 'Command palette \u2014 type "KMS" to see all commands' },
      { key: "Ctrl+Shift+R", desc: "You can assign to Refresh review queue" },
      { key: "Ctrl+Shift+A", desc: "You can assign to Apply decisions" }
    ],
    helpStructureTitle: "Vault structure",
    helpStructureTree: "00_Admin/\n  review-queue.md    \u2190 proposals for review\n  dashboard.md       \u2190 stats\n00_Inbox/              \u2190 DROP FILES HERE\n10_Sources/\n  web/               \u2190 approved web notes\n  pdf/               \u2190 approved PDFs\n20_Source-Notes/       \u2190 generated source notes\n30_Permanent-Notes/    \u2190 your canonical knowledge base\n80_Archive/            \u2190 rejected files",
    helpDocsHint: "Full documentation: docs/USAGE.md, docs/INSTALL.md, docs/gateway.md",
    back: "\u2190 Back",
    next: "Next \u2192",
    skip: "Skip",
    finish: "Finish",
    openReviewQueue: "Open Review Queue",
    openDashboard: "Open Dashboard",
    runScan: "Run scan \u2192",
    nextAnyway: "Next anyway \u2192",
    scanning: "Scanning inbox",
    generating: "Generating review queue (AI)",
    updatingDash: "Updating dashboard",
    applying: "Applying decisions",
    refreshingQueue: "Refreshing queue",
    retriaging: "Re-classifying proposals (LLM)",
    bulkTitle: "Bulk operation",
    confirmTitle: "Confirm",
    confirmYes: "Yes, proceed",
    confirmNo: "Cancel",
    bulkApproveQ: (n) => `Approve ${n} pending proposals?`,
    bulkRejectQ: (n) => `Reject ${n} pending proposals?`,
    bulkDone: (n, d) => `${n} proposals set to ${d}.`,
    noPending: "No pending proposals to change.",
    applyHint: "Run 'Apply decisions' to move files.",
    pipelineDone: "Done!",
    pipelineError: "Pipeline error:",
    copyError: "Copy error",
    close: "Close",
    copied: "Copied to clipboard.",
    panelTitle: "KMS Control Panel",
    secPipeline: "Pipeline",
    secBulk: "Bulk actions",
    secNavigate: "Navigate",
    secAdvanced: "Advanced",
    btnRefresh: "Refresh queue",
    btnApply: "Apply decisions",
    btnRetriage: "Retriage all",
    btnApproveAll: "Approve all pending",
    btnRejectAll: "Reject all pending",
    btnReviewQueue: "Review queue",
    btnDashboard: "Dashboard",
    btnSearch: "Search proposals",
    btnRevertProposal: "Revert proposal",
    btnRevertBatch: "Revert batch",
    btnSettings: "Settings",
    btnHelp: "Help",
    btnAskLlm: "Ask knowledge base",
    tooltipAskLlm: "Ask AnythingLLM about your notes",
    loadingStats: "Loading stats...",
    statsError: "Stats error:",
    topDomains: "Top domains",
    tooltipRefresh: "Scan inbox + AI summaries + dashboard",
    tooltipApply: "Move approved files to targets",
    tooltipRetriage: "Re-classify domains/topics via LLM",
    tooltipRevert: "Revert single applied proposal",
    tooltipBatchRevert: "Undo entire bulk operation",
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
    detailTitle: (id) => `Proposal #${id}`,
    detailLoading: "Loading...",
    detailNotFound: "Proposal not found.",
    revertTitle: "Revert applied proposal",
    revertDesc: "Enter the proposal ID to revert. This will move the file back to its original location and remove the execution record.",
    revertPreview: "Preview (dry-run)",
    revertBtn: "Revert",
    reverting: "Reverting...",
    revertFailed: "Revert failed",
    revertDone: (id) => `Proposal #${id} reverted.`,
    batchRevertTitle: "Revert batch operation",
    batchRevertDesc: "Select a batch to revert all proposals applied in that operation.",
    batchLoading: "Loading batches...",
    noBatches: "No active batches to revert.",
    activeBatches: (n) => `${n} active batch${n > 1 ? "es" : ""}`,
    revertEntireBatch: "Revert entire batch",
    batchReverted: (id, n) => `Batch ${id} reverted (${n} proposals).`,
    batchRevertFailed: "Batch revert failed:",
    settingsTitle: "KMS Review \u2014 Settings",
    settingPython: "Python path",
    settingPythonDesc: "Full path to Python interpreter (default: .venv/bin/python in project dir)",
    settingProject: "Project directory",
    settingProjectDesc: "Path to KMS root directory (default: parent of vault)",
    settingLang: "Interface language",
    settingLangDesc: "Language for plugin messages",
    settingProfile: "Profile",
    settingProfileDesc: "Controls visibility of advanced options",
    settingAnythingLLMHeader: "AnythingLLM",
    settingAnythingLLM: "Enable AnythingLLM",
    settingAnythingLLMDesc: "AnythingLLM integration for retrieval and Q&A",
    settingAnythingLLMUrl: "AnythingLLM URL",
    settingAnythingLLMUrlDesc: "AnythingLLM server address",
    settingSlug: "Workspace slug",
    settingSlugDesc: "AnythingLLM workspace name",
    settingApiKey: "API Key",
    settingApiKeyDesc: "AnythingLLM API key (find in AnythingLLM \u2192 Settings \u2192 API Keys)",
    settingHelp: "Help",
    settingHelpText: "Open <code>docs/workflow.md</code> for a full workflow description.",
    statTotal: "Total",
    statPending: "Pending",
    statApproved: "Approved",
    statApplied: "Applied",
    statRejected: "Rejected",
    statPostpone: "Postpone",
    detailStatus: "Status",
    detailClassification: "Classification",
    detailPaths: "Paths",
    detailAppliedSection: "Applied",
    detailSummarySection: "Summary",
    fieldDecision: "Decision",
    fieldLifecycle: "Lifecycle",
    fieldItemStatus: "Item status",
    fieldConfidence: "Confidence",
    fieldReviewer: "Reviewer",
    fieldReviewNote: "Review note",
    fieldDecidedAt: "Decided at",
    fieldDomain: "Domain",
    fieldTopics: "Topics",
    fieldKind: "Kind",
    fieldSuggestedAction: "Suggested action",
    fieldTarget: "Target",
    fieldOverrideTarget: "Override target",
    fieldSource: "Source",
    fieldSourceNote: "Source note",
    fieldCreated: "Created",
    fieldAppliedAt: "Applied at",
    fieldIndexStatus: "Index status",
    fieldExecutionId: "Execution ID",
    fieldRevertedAt: "Reverted at",
    revertPlaceholder: "Proposal ID (e.g. 42)",
    revertInvalidId: "Enter a valid proposal ID.",
    revertDryRun: "Running dry-run...",
    revertNotFound: (id) => `Proposal #${id} not found.`,
    revertAlreadyReverted: (id) => `Proposal #${id} was already reverted.`,
    revertNotApplied: (id) => `Proposal #${id} has not been applied yet.`,
    revertWillRevert: (path3, action, target) => `Will revert: ${path3} (${action} \u2192 ${target})`,
    revertAppliedAtLabel: (at) => `Applied at: ${at || "unknown"}`,
    proposalTitle: (id) => `Proposal #${id}`,
    clickToViewDetails: "Click to view details",
    reviewNotePlaceholder: "Review note (optional)...",
    btnApprove: "Approve",
    btnReject: "Reject",
    btnPostpone: "Postpone",
    ariaApprove: (id) => `Approve proposal #${id}`,
    ariaReject: (id) => `Reject proposal #${id}`,
    ariaPostpone: (id) => `Postpone proposal #${id}`,
    batchProposalCount: (n) => `${n} proposal${n !== 1 ? "s" : ""}`,
    batchCreatedLabel: (at) => `Created: ${at}`,
    // Ask LLM
    askTitle: "Ask your knowledge base",
    askDesc: "Ask a question \u2014 AnythingLLM will search your notes and answer based on your knowledge base.",
    askPlaceholder: "e.g. How does move semantics work in C++?",
    askSend: "Ask",
    askLoading: "Searching for an answer...",
    askAnswer: "Answer",
    askSources: "Sources",
    askErrorTitle: "AnythingLLM Error",
    askError: (msg) => `AnythingLLM error: ${msg}`,
    askNoApiKey: "No API key set. Configure the API Key in plugin settings (AnythingLLM section).",
    askNoAnythingLLM: "Enable AnythingLLM in plugin settings.",
    askHistoryHint: (url) => `Chat history & export \u2192 ${url}`,
    askHistoryBtn: "Open chat history",
    askVaultTitle: "Found in vault (keyword search)",
    askVaultDesc: "Select files to include their content as context and re-ask.",
    askVaultEmpty: "No additional matches found in vault.",
    askReaskWithContext: "Re-ask with context \u21BB",
    askContextBadge: "\u2726 enriched with vault context",
    // Contradiction
    contradictionWarning: "\u26A0 Contradicts existing knowledge",
    contradictionLabel: "Contradiction",
    // Errors
    searchErrorMsg: (msg) => `Search error: ${msg}`,
    detailErrorMsg: (msg) => `Error loading detail: ${msg}`,
    reviewQueueNotFound: "review-queue.md not found.",
    proposalDecision: (id, d) => `Proposal #${id}: ${d}`,
    fileNotFound: (f) => `${f} not found. Run the pipeline first.`
  }
};
function _t(settings, key, ...args) {
  const lang = settings?.language || "pl";
  const val = (I18N[lang] || I18N.pl)[key] || I18N.pl[key] || key;
  return typeof val === "function" ? val(...args) : val;
}

// src/panel.js
var import_obsidian3 = require("obsidian");

// src/modals.js
var import_obsidian = require("obsidian");
var KmsNoticeModal = class extends import_obsidian.Modal {
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
        setTimeout(() => {
          copyBtn.textContent = t("copyError");
        }, 1500);
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
  onClose() {
    this.contentEl.empty();
  }
};
var KmsSearchModal = class extends import_obsidian.Modal {
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
      placeholder: t("searchPlaceholder")
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
      if (e.key === "Enter") {
        clearTimeout(debounceTimer);
        this._search(input.value, checkbox.checked, resultsEl);
      }
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
        goBtn.addEventListener("click", (e) => {
          e.stopPropagation();
          this.close();
          this.plugin._scrollToProposal(r.proposal_id);
        });
        const srcBtn = actions.createEl("button", { cls: "kms-search-action-btn kms-action-source", text: t("openSource") });
        srcBtn.addEventListener("click", (e) => {
          e.stopPropagation();
          this.close();
          this.plugin._openFile(r.item_path);
        });
        const detailBtn = actions.createEl("button", { cls: "kms-search-action-btn kms-action-detail", text: t("detailsBtn") });
        detailBtn.addEventListener("click", (e) => {
          e.stopPropagation();
          this.close();
          new KmsDetailModal(this.app, this.plugin, r.proposal_id).open();
        });
      }
    } catch (err) {
      resultsEl.empty();
      resultsEl.createEl("p", { cls: "kms-search-error", text: t("searchErrorMsg", err.message) });
    }
  }
  onClose() {
    this.contentEl.empty();
  }
};
var KmsDetailModal = class extends import_obsidian.Modal {
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
      if (results.length === 0) {
        body.createEl("p", { text: t("detailNotFound") });
        return;
      }
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
      gotoBtn.addEventListener("click", () => {
        this.close();
        this.plugin._scrollToProposal(this.proposalId);
      });
      const srcBtn = actions.createEl("button", { cls: "kms-search-action-btn kms-action-source", text: t("openSource") });
      srcBtn.addEventListener("click", () => {
        this.close();
        this.plugin._openFile(d.item_path);
      });
      if (d.can_revert) {
        const revertBtn = actions.createEl("button", { cls: "kms-search-action-btn kms-action-revert", text: t("revertBtn") });
        revertBtn.addEventListener("click", async () => {
          revertBtn.disabled = true;
          revertBtn.textContent = t("reverting");
          try {
            const ok = await this.plugin._runRevertPipeline(
              `${t("revertBtn")} #${this.proposalId}`,
              `"${python}" -m kms.scripts.revert_apply --proposal-id ${this.proposalId}`
            );
            if (ok) {
              new import_obsidian.Notice(t("revertDone", this.proposalId));
              this.close();
            } else {
              revertBtn.textContent = t("revertFailed");
              revertBtn.disabled = false;
            }
          } catch (err) {
            revertBtn.textContent = t("revertFailed");
            revertBtn.disabled = false;
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
  onClose() {
    this.contentEl.empty();
  }
};
var KmsRevertModal = class extends import_obsidian.Modal {
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
      if (!pid) {
        previewEl.empty();
        previewEl.createEl("p", { cls: "kms-search-error", text: t("revertInvalidId") });
        return;
      }
      previewEl.empty();
      previewEl.createEl("p", { cls: "kms-search-loading", text: t("revertDryRun") });
      const python = this.plugin._getPython();
      const projectRoot = this.plugin._getProjectRoot();
      try {
        const stdout = await this.plugin._exec(`"${python}" -m kms.scripts.proposal_detail --proposal-id ${pid}`, projectRoot);
        const results = JSON.parse(stdout);
        previewEl.empty();
        if (results.length === 0) {
          previewEl.createEl("p", { text: t("revertNotFound", pid) });
          return;
        }
        const d = results[0];
        if (!d.can_revert) {
          previewEl.createEl("p", { cls: "kms-search-error", text: d.is_applied ? t("revertAlreadyReverted", pid) : t("revertNotApplied", pid) });
          return;
        }
        previewEl.createEl("p", { text: t("revertWillRevert", d.item_path, d.suggested_action, d.suggested_target) });
        previewEl.createEl("p", { text: t("revertAppliedAtLabel", d.applied_at), cls: "kms-detail-summary" });
        revertBtn.disabled = false;
      } catch (err) {
        previewEl.empty();
        previewEl.createEl("p", { cls: "kms-search-error", text: t("detailErrorMsg", err.message) });
      }
    });
    revertBtn.addEventListener("click", async () => {
      const pid = parseInt(input.value, 10);
      if (!pid) return;
      revertBtn.disabled = true;
      revertBtn.textContent = t("reverting");
      const python = this.plugin._getPython();
      const projectRoot = this.plugin._getProjectRoot();
      try {
        const ok = await this.plugin._runRevertPipeline(
          `${t("revertBtn")} #${pid}`,
          `"${python}" -m kms.scripts.revert_apply --proposal-id ${pid}`
        );
        if (ok) {
          new import_obsidian.Notice(t("revertDone", pid));
          this.close();
        } else {
          revertBtn.textContent = t("revertFailed");
          revertBtn.disabled = false;
        }
      } catch (err) {
        revertBtn.textContent = t("revertFailed");
        revertBtn.disabled = false;
        new KmsNoticeModal(this.app, this.plugin, t("revertFailed"), t("revertFailed"), { detail: err.message }).open();
      }
    });
    setTimeout(() => input.focus(), 50);
  }
  onClose() {
    this.contentEl.empty();
  }
};
var KmsBatchRevertModal = class extends import_obsidian.Modal {
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
              `"${python}" -m kms.scripts.revert_apply --batch-id "${b.id}"`
            );
            if (ok) {
              new import_obsidian.Notice(t("batchReverted", b.id.slice(0, 8), b.proposal_count));
              this.close();
            } else {
              revertBtn.textContent = t("revertFailed");
              revertBtn.disabled = false;
            }
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
  onClose() {
    this.contentEl.empty();
  }
};
var KmsConfirmModal = class extends import_obsidian.Modal {
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
    yesBtn.addEventListener("click", () => {
      this._resolved = true;
      this.close();
      this._callback(true);
    });
    const noBtn = btnRow.createEl("button", { text: t("confirmNo") });
    noBtn.addEventListener("click", () => {
      this._resolved = true;
      this.close();
      this._callback(false);
    });
  }
  onClose() {
    this.contentEl.empty();
    if (!this._resolved && this._callback) this._callback(false);
  }
};
var KmsAskLlmModal = class extends import_obsidian.Modal {
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
      attr: { rows: "3", placeholder: t("askPlaceholder") }
    });
    const btnRow = contentEl.createDiv({ cls: "kms-ask-actions" });
    const askBtn = btnRow.createEl("button", { text: t("askSend"), cls: "mod-cta" });
    const responseEl = contentEl.createDiv({ cls: "kms-ask-response" });
    const vaultEl = contentEl.createDiv({ cls: "kms-ask-vault" });
    const settings = this.plugin.settings;
    const baseHost = (settings.anythingllmUrl || "http://localhost:3001").replace(/\/+$/, "");
    const chatsUrl = `${baseHost}/settings/workspace-chats`;
    const footer = contentEl.createDiv({ cls: "kms-ask-footer" });
    const footerLink = footer.createEl("a", {
      cls: "kms-ask-history-link",
      text: t("askHistoryBtn"),
      attr: { href: chatsUrl }
    });
    footerLink.addEventListener("click", (e) => {
      e.preventDefault();
      window.open(chatsUrl, "_blank");
    });
    footer.createSpan({ cls: "kms-ask-footer-hint", text: ` \u2014 ${t("askHistoryHint", chatsUrl)}` });
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
            } }]
          }).open();
          askBtn.disabled = false;
          askBtn.textContent = t("askSend");
          return;
        }
        let message = question;
        let mode = "query";
        if (withContext) {
          const selected = this._getSelectedVaultFiles(vaultEl);
          if (selected.length > 0) {
            const ctx = selected.map(
              (r) => `--- ${r.path} ---
${r.content.substring(0, 1500)}`
            ).join("\n\n");
            message = `Kontekst z moich notatek:

${ctx}

---
Pytanie: ${question}`;
            mode = "chat";
          }
        }
        const resp = await (0, import_obsidian.requestUrl)({
          url: `${baseUrl}/api/v1/workspace/${slug}/chat`,
          method: "POST",
          headers: {
            "Authorization": `Bearer ${apiKey}`,
            "Content-Type": "application/json"
          },
          body: JSON.stringify({ message, mode, attachments: [] })
        });
        const data = resp.json;
        responseEl.empty();
        const text = data.textResponse || data.error || JSON.stringify(data);
        const answer = responseEl.createDiv({ cls: "kms-ask-answer" });
        answer.createEl("h4", { text: t("askAnswer") });
        if (withContext) {
          answer.createEl("span", { cls: "kms-ask-context-badge", text: t("askContextBadge") });
        }
        const answerBody = answer.createDiv({ cls: "kms-ask-answer-body" });
        try {
          await import_obsidian.MarkdownRenderer.render(this.app, text, answerBody, "", this);
        } catch (_) {
          for (const para of text.split("\n\n")) {
            if (para.trim()) answerBody.createEl("p", { text: para.trim() });
          }
        }
        const sources = data.sources || [];
        if (sources.length > 0) {
          const srcEl = responseEl.createDiv({ cls: "kms-ask-sources" });
          srcEl.createEl("h4", { text: t("askSources") });
          for (const src of sources) {
            const title = src.title || src.name || src.location || "\u2014";
            srcEl.createEl("p", { cls: "kms-ask-source-item", text: `\u2022 ${title}` });
          }
        }
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
          } }]
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
      row.createSpan({ cls: "kms-ask-vault-score", text: `${r.matched}/${r.total} terms \xB7 ${r.score} pts` });
      if (r.snippet) {
        item.createEl("p", { cls: "kms-ask-vault-snippet", text: r.snippet });
      }
    }
    const reaskBtn = container.createEl("button", {
      cls: "kms-ask-vault-reask",
      text: t("askReaskWithContext")
    });
    reaskBtn.addEventListener("click", () => reaskCallback());
  }
  // ── Keyword search across vault markdown files ──
  // Improved: stop words, prefix stemming, coverage-weighted scoring
  async _searchVault(query) {
    const files = this.app.vault.getMarkdownFiles();
    const raw = query.toLowerCase().replace(/[^a-ząćęłńóśźż0-9\s]/gi, "").split(/\s+/);
    const STOP = /* @__PURE__ */ new Set([
      "i",
      "w",
      "z",
      "na",
      "do",
      "to",
      "co",
      "jak",
      "czy",
      "\u017Ce",
      "nie",
      "si\u0119",
      "jest",
      "od",
      "za",
      "po",
      "ale",
      "lub",
      "te",
      "ten",
      "ta",
      "tym",
      "tego",
      "tej",
      "o",
      "a",
      "ze",
      "dla",
      "przy",
      "przez",
      "bez",
      "nad",
      "pod",
      "czego",
      "czym",
      "jaki",
      "jaka",
      "jakie",
      "kt\xF3ry",
      "kt\xF3ra",
      "kt\xF3re",
      "by\u0107",
      "by\u0142",
      "by\u0142a",
      "by\u0142o",
      "by\u0142y",
      "b\u0119dzie",
      "mie\u0107",
      "mia\u0142",
      "mia\u0142a",
      "dotyczy\u0142a",
      "dotyczy\u0142o",
      "the",
      "a",
      "an",
      "is",
      "are",
      "was",
      "were",
      "be",
      "been",
      "have",
      "has",
      "had",
      "do",
      "does",
      "did",
      "will",
      "would",
      "could",
      "should",
      "may",
      "can",
      "of",
      "in",
      "to",
      "for",
      "with",
      "on",
      "at",
      "from",
      "by",
      "about",
      "as",
      "and",
      "but",
      "or",
      "not",
      "what",
      "which",
      "who",
      "this",
      "that",
      "how",
      "where",
      "when",
      "why",
      "it",
      "its",
      "my",
      "your",
      "his",
      "her"
    ]);
    const terms = raw.filter((w) => w.length >= 2 && !STOP.has(w));
    if (terms.length === 0) return [];
    const termSets = terms.map((t) => {
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
          while ((idx = lower.indexOf(stem, idx)) !== -1) {
            count++;
            idx += stem.length;
          }
          if (nameLower.includes(stem)) count += 5;
          best = Math.max(best, count);
        }
        if (best > 0) {
          termsMatched++;
          totalScore += Math.min(best, 10);
          if (!bestMatchStem) {
            bestMatchStem = stems.find((s) => lower.includes(s));
          }
        }
      }
      if (totalScore > 0 && termsMatched > 0) {
        const coverage = termsMatched / termSets.length;
        const finalScore = Math.round(totalScore * (0.5 + coverage * 2));
        const stem = bestMatchStem || terms[0];
        const matchIdx = Math.max(0, lower.indexOf(stem));
        const start = Math.max(0, matchIdx - 60);
        const end = Math.min(content.length, matchIdx + 250);
        const snippet = (start > 0 ? "\u2026" : "") + content.substring(start, end).replace(/\n+/g, " ").trim() + (end < content.length ? "\u2026" : "");
        scored.push({
          path: file.path,
          score: finalScore,
          matched: termsMatched,
          total: termSets.length,
          snippet,
          content
        });
      }
    }
    scored.sort((a, b) => b.score - a.score);
    return scored.slice(0, 8);
  }
  // ── Get checked vault files from the UI ──
  _getSelectedVaultFiles(container) {
    const checked = container.querySelectorAll("input[type=checkbox]:checked");
    const paths = new Set([...checked].map((cb) => cb.getAttribute("data-path")));
    return this._vaultResults.filter((r) => paths.has(r.path));
  }
  onClose() {
    this.contentEl.empty();
  }
};
var KmsProgressModal = class extends import_obsidian.Modal {
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
      li.createSpan({ cls: "kms-progress-icon", text: "\u25CB" });
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
    if (state === "running") icon.textContent = "\u25C9";
    else if (state === "done") icon.textContent = "\u2713";
    else if (state === "error") icon.textContent = "\u2717";
    if (elapsedMs != null) {
      this.timeEls[idx].textContent = `${(elapsedMs / 1e3).toFixed(1)}s`;
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
      new import_obsidian.Notice(t("copied"));
    });
    const closeBtn = btnRow.createEl("button", { text: t("close") });
    closeBtn.addEventListener("click", () => this.close());
  }
  onClose() {
    this.contentEl.empty();
  }
};

// src/wizard.js
var import_obsidian2 = require("obsidian");
var path = require("path");
var fs = require("fs");
var KmsOnboardingWizard = class extends import_obsidian2.Modal {
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
      t("wizStep1"),
      t("wizProfileTitle"),
      t("wizStep2"),
      t("wizStep3"),
      t("wizStep4"),
      t("wizStepHelp")
    ];
    const indicator = contentEl.createDiv({ cls: "kms-wizard-steps" });
    for (let i = 0; i < stepLabels.length; i++) {
      const dot = indicator.createSpan({
        cls: `kms-wizard-dot${i === this.step ? " active" : i < this.step ? " done" : ""}`,
        text: i < this.step ? "\u2713" : String(i + 1)
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
      { value: "ai-cloud", label: t("profileAiCloud"), desc: t("profileAiCloudDesc") }
    ];
    const list = body.createDiv({ cls: "kms-wizard-profiles" });
    for (const p of profiles) {
      const card = list.createDiv({
        cls: `kms-wizard-profile-card${this.plugin.settings.profile === p.value ? " active" : ""}`
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
      nextAction: fileCount > 0 ? () => {
        this.step = 4;
        this._renderStep();
      } : () => {
        this.step = 5;
        this._renderStep();
      }
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
      { label: t("updatingDash"), cmd: "generate_dashboard" }
    ];
    const lis = [];
    for (const s of steps) {
      const li = progress.createEl("li", { cls: "kms-progress-step kms-step-pending" });
      li.createSpan({ cls: "kms-progress-icon", text: "\u25CB" });
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
      li.querySelector(".kms-progress-icon").textContent = "\u25C9";
      const start = Date.now();
      try {
        await this.plugin._exec(`"${python}" -m kms.scripts.${steps[i].cmd}`, projectRoot);
        const elapsed = ((Date.now() - start) / 1e3).toFixed(1);
        li.className = "kms-progress-step kms-step-done";
        li.querySelector(".kms-progress-icon").textContent = "\u2713";
        li.querySelector(".kms-progress-time").textContent = `${elapsed}s`;
      } catch (err) {
        const elapsed = ((Date.now() - start) / 1e3).toFixed(1);
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
      retryBtn.addEventListener("click", () => {
        this.step = 4;
        this._renderStep();
      });
      const skipBtn = btnRow.createEl("button", { text: t("wizFinishAnyway") });
      skipBtn.addEventListener("click", () => {
        this.step = 5;
        this._renderStep();
      });
    }
    if (!failed) {
      this._navButtons(body, { showBack: false, nextLabel: t("next"), nextAction: () => {
        this.step = 5;
        this._renderStep();
      } });
    }
  }
  // ── Step 5: Help / How-To ──
  _stepHelp(body) {
    const t = (k, ...a) => _t(this.plugin.settings, k, ...a);
    body.createEl("h3", { text: t("helpTitle") });
    body.createEl("p", { text: t("helpIntro") });
    const sections = t("helpSections");
    for (const section of sections) {
      const details = body.createEl("details", { cls: "kms-help-section" });
      const summary = details.createEl("summary", { cls: "kms-help-summary" });
      summary.createSpan({ cls: "kms-help-icon", text: section.icon });
      summary.createSpan({ text: section.title });
      const content = details.createDiv({ cls: "kms-help-content" });
      for (const item of section.items) {
        const row2 = content.createDiv({ cls: "kms-help-item" });
        row2.createEl("strong", { text: item.label });
        row2.createEl("span", { text: ` \u2014 ${item.desc}` });
      }
    }
    const kbSection = body.createEl("details", { cls: "kms-help-section" });
    const kbSummary = kbSection.createEl("summary", { cls: "kms-help-summary" });
    kbSummary.createSpan({ cls: "kms-help-icon", text: "\u2328" });
    kbSummary.createSpan({ text: t("helpKeyboardTitle") });
    const kbContent = kbSection.createDiv({ cls: "kms-help-content" });
    for (const kb of t("helpKeyboard")) {
      const row2 = kbContent.createDiv({ cls: "kms-help-item" });
      row2.createEl("kbd", { text: kb.key, cls: "kms-help-kbd" });
      row2.createEl("span", { text: ` ${kb.desc}` });
    }
    const structSection = body.createEl("details", { cls: "kms-help-section" });
    const structSummary = structSection.createEl("summary", { cls: "kms-help-summary" });
    structSummary.createSpan({ cls: "kms-help-icon", text: "\u{1F4C1}" });
    structSummary.createSpan({ text: t("helpStructureTitle") });
    const structContent = structSection.createDiv({ cls: "kms-help-content" });
    structContent.createEl("pre", { cls: "kms-help-tree", text: t("helpStructureTree") });
    body.createEl("p", { cls: "kms-help-docs-hint", text: t("helpDocsHint") });
    const row = body.createDiv({ cls: "kms-wizard-actions" });
    const openRQ = row.createEl("button", { text: t("openReviewQueue"), cls: "mod-cta" });
    openRQ.addEventListener("click", () => {
      this._finish();
      this.plugin._openFile(REVIEW_QUEUE_FILENAME);
    });
    const openDash = row.createEl("button", { text: t("openDashboard") });
    openDash.addEventListener("click", () => {
      this._finish();
      this.plugin._openFile(DASHBOARD_FILENAME);
    });
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
      back.addEventListener("click", () => {
        this.step--;
        this._renderStep();
      });
    }
    const skipBtn = row.createEl("button", { text: t("skip") });
    skipBtn.addEventListener("click", () => this._finish());
    const next = row.createEl("button", { text: nextLabel || t("next"), cls: "mod-cta" });
    next.addEventListener("click", nextAction || (() => {
      this.step++;
      this._renderStep();
    }));
  }
  async _finish() {
    this.plugin.settings.onboardingDone = true;
    await this.plugin.saveSettings();
    this.close();
    this.plugin._reloadKmsViews();
    this.plugin._refreshPanel();
  }
  onClose() {
    this.contentEl.empty();
  }
};
var KmsHelpModal = class extends import_obsidian2.Modal {
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
        row.createEl("span", { text: ` \u2014 ${item.desc}` });
      }
    }
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
    const structSection = contentEl.createEl("details", { cls: "kms-help-section" });
    const structSummary = structSection.createEl("summary", { cls: "kms-help-summary" });
    structSummary.createSpan({ cls: "kms-help-icon", text: "\u{1F4C1}" });
    structSummary.createSpan({ text: t("helpStructureTitle") });
    const structContent = structSection.createDiv({ cls: "kms-help-content" });
    structContent.createEl("pre", { cls: "kms-help-tree", text: t("helpStructureTree") });
    contentEl.createEl("p", { cls: "kms-help-docs-hint", text: t("helpDocsHint") });
    const closeRow = contentEl.createDiv({ cls: "kms-wizard-actions" });
    const closeBtn = closeRow.createEl("button", { text: t("close"), cls: "mod-cta" });
    closeBtn.addEventListener("click", () => this.close());
  }
  onClose() {
    this.contentEl.empty();
  }
};

// src/panel.js
var KmsPanelView = class extends import_obsidian3.ItemView {
  constructor(leaf, plugin) {
    super(leaf);
    this.plugin = plugin;
  }
  getViewType() {
    return PANEL_VIEW_TYPE;
  }
  getDisplayText() {
    return "KMS";
  }
  getIcon() {
    return "layout-dashboard";
  }
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
    const pipeSection = section(t("secPipeline"));
    this._actionBtn(pipeSection, t("btnRefresh"), "rotate-cw", t("tooltipRefresh"), () => this.plugin._runPipeline("refresh"));
    this._actionBtn(pipeSection, t("btnApply"), "check-circle", t("tooltipApply"), () => this.plugin._runPipeline("apply"));
    if (this.plugin.settings.profile !== "core") {
      this._actionBtn(pipeSection, t("btnRetriage"), "wand", t("tooltipRetriage"), () => this.plugin._runPipeline("retriage"));
    }
    const bulkSection = section(t("secBulk"));
    this._actionBtn(bulkSection, t("btnApproveAll"), "check", "", () => this.plugin._bulkDecision("approve"));
    this._actionBtn(bulkSection, t("btnRejectAll"), "x", "", () => this.plugin._bulkDecision("reject"));
    const navSection = section(t("secNavigate"));
    this._actionBtn(navSection, t("btnReviewQueue"), "file-text", "", () => this.plugin._openFile(REVIEW_QUEUE_FILENAME));
    this._actionBtn(navSection, t("btnDashboard"), "bar-chart-2", "", () => this.plugin._openFile(DASHBOARD_FILENAME));
    this._actionBtn(navSection, t("btnSearch"), "search", "", () => new KmsSearchModal(this.plugin.app, this.plugin).open());
    if (this.plugin.settings.anythingllmEnabled) {
      this._actionBtn(navSection, t("btnAskLlm"), "message-circle", t("tooltipAskLlm"), () => {
        if (!this.plugin.settings.anythingllmApiKey) {
          new KmsNoticeModal(this.plugin.app, this.plugin, "AnythingLLM", t("askNoApiKey"), {
            actions: [{ label: t("wizOpenSettings"), cls: "mod-cta", callback: () => {
              this.plugin.app.setting.open();
              this.plugin.app.setting.openTabById("kms-review");
            } }]
          }).open();
          return;
        }
        new KmsAskLlmModal(this.plugin.app, this.plugin).open();
      });
    }
    const advSection = section(t("secAdvanced"));
    this._actionBtn(advSection, t("btnRevertProposal"), "undo", t("tooltipRevert"), () => new KmsRevertModal(this.plugin.app, this.plugin).open());
    this._actionBtn(advSection, t("btnRevertBatch"), "rotate-ccw", t("tooltipBatchRevert"), () => new KmsBatchRevertModal(this.plugin.app, this.plugin).open());
    this._actionBtn(advSection, t("btnSettings"), "settings", "", () => {
      this.plugin.app.setting.open();
      this.plugin.app.setting.openTabById("kms-review");
    });
    this._actionBtn(advSection, t("btnHelp"), "help-circle", "", () => new KmsHelpModal(this.plugin.app, this.plugin).open());
  }
  _actionBtn(parent, label, icon, tooltip, onClick) {
    const btn = parent.createEl("button", { cls: "kms-panel-btn" });
    const iconSpan = btn.createSpan({ cls: "kms-panel-btn-icon" });
    try {
      (0, import_obsidian3.setIcon)(iconSpan, icon);
    } catch {
    }
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
          fill.style.width = `${Math.round(count / total * 100)}%`;
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
  async onClose() {
  }
};

// src/settings.js
var import_obsidian4 = require("obsidian");
var KmsSettingsTab = class extends import_obsidian4.PluginSettingTab {
  constructor(app, plugin) {
    super(app, plugin);
    this.plugin = plugin;
  }
  display() {
    const { containerEl } = this;
    const t = (k, ...a) => _t(this.plugin.settings, k, ...a);
    containerEl.empty();
    containerEl.createEl("h2", { text: t("settingsTitle") });
    new import_obsidian4.Setting(containerEl).setName(t("settingPython")).setDesc(t("settingPythonDesc")).addText(
      (text) => text.setPlaceholder(".venv/bin/python").setValue(this.plugin.settings.pythonPath).onChange(async (value) => {
        this.plugin.settings.pythonPath = value.trim();
        await this.plugin.saveSettings();
      })
    );
    new import_obsidian4.Setting(containerEl).setName(t("settingProject")).setDesc(t("settingProjectDesc")).addText(
      (text) => text.setPlaceholder("auto-detect").setValue(this.plugin.settings.projectRoot).onChange(async (value) => {
        this.plugin.settings.projectRoot = value.trim();
        await this.plugin.saveSettings();
      })
    );
    new import_obsidian4.Setting(containerEl).setName(t("settingLang")).setDesc(t("settingLangDesc")).addDropdown(
      (dropdown) => dropdown.addOption("pl", "Polski").addOption("en", "English").setValue(this.plugin.settings.language).onChange(async (value) => {
        this.plugin.settings.language = value;
        await this.plugin.saveSettings();
      })
    );
    new import_obsidian4.Setting(containerEl).setName(t("settingProfile")).setDesc(t("settingProfileDesc")).addDropdown(
      (dropdown) => dropdown.addOption("core", t("profileCore")).addOption("ai-local", t("profileAiLocal")).addOption("ai-cloud", t("profileAiCloud")).setValue(this.plugin.settings.profile).onChange(async (value) => {
        this.plugin.settings.profile = value;
        await this.plugin.saveSettings();
      })
    );
    containerEl.createEl("h3", { text: t("settingAnythingLLMHeader") });
    new import_obsidian4.Setting(containerEl).setName(t("settingAnythingLLM")).setDesc(t("settingAnythingLLMDesc")).addToggle(
      (toggle) => toggle.setValue(this.plugin.settings.anythingllmEnabled).onChange(async (value) => {
        this.plugin.settings.anythingllmEnabled = value;
        await this.plugin.saveSettings();
      })
    );
    new import_obsidian4.Setting(containerEl).setName(t("settingAnythingLLMUrl")).setDesc(t("settingAnythingLLMUrlDesc")).addText(
      (text) => text.setPlaceholder("http://localhost:3001").setValue(this.plugin.settings.anythingllmUrl).onChange(async (value) => {
        this.plugin.settings.anythingllmUrl = value.trim();
        await this.plugin.saveSettings();
      })
    );
    new import_obsidian4.Setting(containerEl).setName(t("settingSlug")).setDesc(t("settingSlugDesc")).addText(
      (text) => text.setPlaceholder("my-workspace").setValue(this.plugin.settings.anythingllmSlug).onChange(async (value) => {
        this.plugin.settings.anythingllmSlug = value.trim();
        await this.plugin.saveSettings();
      })
    );
    new import_obsidian4.Setting(containerEl).setName(t("settingApiKey")).setDesc(t("settingApiKeyDesc")).addText(
      (text) => text.setPlaceholder("AK-xxxxxxxx").setValue(this.plugin.settings.anythingllmApiKey).onChange(async (value) => {
        this.plugin.settings.anythingllmApiKey = value.trim();
        await this.plugin.saveSettings();
      })
    );
    containerEl.createEl("h3", { text: t("settingHelp") });
    const helpLink = containerEl.createEl("p");
    helpLink.innerHTML = t("settingHelpText");
  }
};

// src/main.js
var { exec } = require("child_process");
var path2 = require("path");
var KmsReviewPlugin = class extends import_obsidian5.Plugin {
  async onload() {
    await this.loadSettings();
    this.addSettingTab(new KmsSettingsTab(this.app, this));
    this.registerView(PANEL_VIEW_TYPE, (leaf) => new KmsPanelView(leaf, this));
    this.registerMarkdownCodeBlockProcessor("kms-review", (source, el, ctx) => {
      this._renderReviewBlock(source, el, ctx);
    });
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
        new KmsNoticeModal(
          this.app,
          this,
          "AnythingLLM",
          _t(this.settings, "askNoAnythingLLM"),
          { actions: [{ label: _t(this.settings, "wizOpenSettings"), cls: "mod-cta", callback: () => {
            this.app.setting.open();
            this.app.setting.openTabById("kms-review");
          } }] }
        ).open();
        return;
      }
      new KmsAskLlmModal(this.app, this).open();
    } });
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
      if (leaf.view instanceof KmsPanelView) leaf.view.refresh();
    }
  }
  // ── Pipeline ──
  _getProjectRoot() {
    if (this.settings.projectRoot) return this.settings.projectRoot;
    return path2.dirname(this.app.vault.adapter.basePath);
  }
  _getPython() {
    if (this.settings.pythonPath) return this.settings.pythonPath;
    return path2.join(this._getProjectRoot(), ".venv", "bin", "python");
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
        { cmd: `"${python}" -m kms.scripts.generate_dashboard`, label: t("updatingDash") }
      ],
      apply: [
        { cmd: `"${python}" -m kms.scripts.apply_decisions`, label: t("applying") },
        { cmd: `"${python}" -m kms.scripts.make_review_queue`, label: t("refreshingQueue") },
        { cmd: `"${python}" -m kms.scripts.generate_dashboard`, label: t("updatingDash") }
      ],
      retriage: [
        { cmd: `"${python}" -m kms.scripts.make_review_queue --retriage${aiFlag}`, label: t("retriaging") },
        { cmd: `"${python}" -m kms.scripts.generate_dashboard`, label: t("updatingDash") }
      ]
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
      { cmd: `"${python}" -m kms.scripts.generate_dashboard`, label: t("updatingDash") }
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
        timeout: 6e5,
        env: { ...process.env, PYTHONPATH: cwd || this._getProjectRoot() }
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
        actions: [{ label: t("btnRefresh"), cls: "mod-cta", callback: () => this._runPipeline("refresh") }]
      }).open();
    }
  }
  async _scrollToProposal(proposalId) {
    const file = this.app.vault.getAbstractFileByPath(REVIEW_QUEUE_FILENAME);
    if (!file) {
      new KmsNoticeModal(this.app, this, _t(this.settings, "pipelineError"), _t(this.settings, "reviewQueueNotFound"), {
        actions: [{ label: _t(this.settings, "btnRefresh"), cls: "mod-cta", callback: () => this._runPipeline("refresh") }]
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
          if (lines[j].includes(KMS_BEGIN)) {
            targetLine = j;
            break;
          }
        }
        if (targetLine === -1) targetLine = i;
        break;
      }
    }
    if (targetLine >= 0) {
      const view = leaf.view;
      if (view instanceof import_obsidian5.MarkdownView && view.editor) {
        view.editor.setCursor({ line: targetLine, ch: 0 });
        view.editor.scrollIntoView(
          { from: { line: targetLine, ch: 0 }, to: { line: targetLine + 20, ch: 0 } },
          true
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
        actions: [{ label: t("btnRefresh"), cls: "mod-cta", callback: () => this._runPipeline("refresh") }]
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
      if (fieldRegex.test(block.text)) {
        block.text = block.text.replace(fieldRegex, `$1${decision}`);
        applied++;
      }
    }
    await this.app.vault.modify(file, freshBlocks.map((b) => b.text).join(""));
    new KmsNoticeModal(this.app, this, t("bulkTitle"), t("bulkDone", applied, decision), {
      actions: [{ label: t("btnApply"), cls: "mod-cta", callback: () => this._runPipeline("apply") }]
    }).open();
    this._reloadKmsViews();
    this._refreshPanel();
  }
  // ── Review block rendering ──
  async _renderReviewBlock(source, el, ctx) {
    const parsed = this._parseYaml(source);
    if (!parsed.proposal_id) {
      el.createEl("pre", { text: source });
      return;
    }
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
      { value: "postpone", label: t("btnPostpone"), aria: t("ariaPostpone", parsed.proposal_id) }
    ]) {
      const btn = btnRow.createEl("button", {
        cls: `kms-decision-btn${parsed.decision === d.value ? ` active-${d.value}` : ""}`,
        text: d.label,
        attr: { "aria-label": d.aria }
      });
      btn.addEventListener("click", async () => {
        btnRow.querySelectorAll(".kms-decision-btn").forEach((b) => b.className = "kms-decision-btn");
        btn.className = `kms-decision-btn active-${d.value}`;
        container.className = `kms-review-block kms-decision-${d.value}`;
        header.querySelector(".kms-review-badge").textContent = d.value.toUpperCase();
        await this._updateField(ctx.sourcePath, parsed.proposal_id, "decision", d.value);
        new import_obsidian5.Notice(`${_t(this.settings, "proposalDecision", parsed.proposal_id, d.value)} \u2014 ${_t(this.settings, "applyHint")}`, 6e3);
      });
    }
    const noteInput = container.createEl("input", {
      cls: "kms-review-note-input",
      type: "text",
      placeholder: t("reviewNotePlaceholder"),
      value: parsed.review_note || ""
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
      if (val.startsWith("'") && val.endsWith("'") || val.startsWith('"') && val.endsWith('"')) val = val.slice(1, -1);
      if (val === "null" || val === "~") return "";
      return val;
    };
    return {
      proposal_id: get("proposal_id"),
      item_id: get("item_id"),
      decision: get("decision") || "pending",
      reviewer: get("reviewer"),
      override_target: get("override_target"),
      review_note: get("review_note")
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
      if (fieldRegex.test(block.text)) {
        block.text = block.text.replace(fieldRegex, `$1${quoted}`);
        modified = true;
      }
    }
    if (modified) await this.app.vault.modify(file, blocks.map((b) => b.text).join(""));
  }
  _splitKmsBlocks(content) {
    const parts = [];
    let remaining = content;
    while (remaining.length > 0) {
      const beginIdx = remaining.indexOf(KMS_BEGIN);
      if (beginIdx === -1) {
        parts.push({ isKms: false, text: remaining });
        break;
      }
      if (beginIdx > 0) parts.push({ isKms: false, text: remaining.substring(0, beginIdx) });
      const endIdx = remaining.indexOf(KMS_END, beginIdx);
      if (endIdx === -1) {
        parts.push({ isKms: true, text: remaining.substring(beginIdx) });
        break;
      }
      const blockEnd = endIdx + KMS_END.length;
      parts.push({ isKms: true, text: remaining.substring(beginIdx, blockEnd) });
      remaining = remaining.substring(blockEnd);
    }
    return parts;
  }
};
