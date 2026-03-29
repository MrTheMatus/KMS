/*
 * KMS Review Queue Plugin for Obsidian
 *
 * Features:
 * - Interactive review widgets for ```kms-review code blocks
 * - Command palette: Refresh queue, Apply decisions, Bulk approve/reject
 * - Auto-saves decisions back to source file
 * - Dashboard generation
 */

const { Plugin, MarkdownRenderer, Notice } = require("obsidian");
const { exec } = require("child_process");
const path = require("path");

const REVIEW_QUEUE_FILENAME = "00_Admin/review-queue.md";
const DASHBOARD_FILENAME = "00_Admin/dashboard.md";
const KMS_BEGIN = "<!-- kms:begin -->";
const KMS_END = "<!-- kms:end -->";

module.exports = class KmsReviewPlugin extends Plugin {
  async onload() {
    // ── Code block processor ──
    this.registerMarkdownCodeBlockProcessor("kms-review", (source, el, ctx) => {
      this._renderReviewBlock(source, el, ctx);
    });

    // ── Commands ──

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
      id: "approve-all-pending",
      name: "Approve all pending proposals",
      callback: () => this._bulkDecision("approve"),
    });

    this.addCommand({
      id: "reject-all-pending",
      name: "Reject all pending proposals",
      callback: () => this._bulkDecision("reject"),
    });

    // ── Ribbon ──
    this.addRibbonIcon("checkbox-glyph", "KMS Review Queue", () => {
      this._openFile(REVIEW_QUEUE_FILENAME);
    });

    console.log("KMS Review plugin loaded");
  }

  onunload() {
    console.log("KMS Review plugin unloaded");
  }

  // ════════════════════════════════════════════════
  // Pipeline commands (run Python scripts)
  // ════════════════════════════════════════════════

  _getProjectRoot() {
    const vaultPath = this.app.vault.adapter.basePath;
    return path.dirname(vaultPath);
  }

  async _runPipeline(mode) {
    const projectRoot = this._getProjectRoot();
    const python = path.join(projectRoot, ".venv", "bin", "python");

    let steps;
    if (mode === "refresh") {
      steps = [
        { cmd: `"${python}" -m kms.scripts.scan_inbox`, label: "Scanning inbox" },
        {
          cmd: `"${python}" -m kms.scripts.make_review_queue --ai-summary`,
          label: "Generating review queue (AI)",
        },
        {
          cmd: `"${python}" -m kms.scripts.generate_dashboard`,
          label: "Updating dashboard",
        },
      ];
    } else if (mode === "apply") {
      steps = [
        {
          cmd: `"${python}" -m kms.scripts.apply_decisions`,
          label: "Applying decisions",
        },
        {
          cmd: `"${python}" -m kms.scripts.make_review_queue`,
          label: "Refreshing queue",
        },
        {
          cmd: `"${python}" -m kms.scripts.generate_dashboard`,
          label: "Updating dashboard",
        },
      ];
    }

    const notice = new Notice(`KMS: Starting ${mode}...`, 0);

    for (const step of steps) {
      try {
        notice.setMessage(`KMS: ${step.label}...`);
        await this._exec(step.cmd, projectRoot);
      } catch (err) {
        notice.hide();
        new Notice(`KMS Error: ${step.label} failed.\n${err.message}`, 10000);
        console.error("KMS pipeline error:", err);
        return;
      }
    }

    notice.hide();
    new Notice(`KMS: ${mode} complete!`, 5000);

    // Reload open files so changes are visible
    this.app.workspace.iterateAllLeaves((leaf) => {
      if (leaf.view?.file?.path === REVIEW_QUEUE_FILENAME ||
          leaf.view?.file?.path === DASHBOARD_FILENAME) {
        leaf.rebuildView();
      }
    });
  }

  _exec(cmd, cwd) {
    return new Promise((resolve, reject) => {
      exec(
        cmd,
        { cwd, timeout: 600000, env: { ...process.env, PYTHONPATH: cwd } },
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

      // Only change pending blocks
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

    // Reload view
    this.app.workspace.iterateAllLeaves((leaf) => {
      if (leaf.view?.file?.path === REVIEW_QUEUE_FILENAME) {
        leaf.rebuildView();
      }
    });
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

    // Header
    const header = container.createDiv({ cls: "kms-review-header" });
    header.createSpan({
      cls: "kms-review-title",
      text: `Proposal #${parsed.proposal_id}`,
    });
    const badge = header.createSpan({
      cls: "kms-review-badge",
      text: parsed.decision.toUpperCase(),
    });

    // Decision buttons
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
        btnRow
          .querySelectorAll(".kms-decision-btn")
          .forEach((b) => (b.className = "kms-decision-btn"));
        btn.className = `kms-decision-btn active-${d.value}`;
        container.className = `kms-review-block kms-decision-${d.value}`;
        badge.textContent = d.value.toUpperCase();
        await this._updateField(
          ctx.sourcePath,
          parsed.proposal_id,
          "decision",
          d.value
        );
        new Notice(`Proposal #${parsed.proposal_id}: ${d.value}`);
      });
    }

    // Review note
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
        await this._updateField(
          ctx.sourcePath,
          parsed.proposal_id,
          "review_note",
          noteInput.value
        );
      }, 800);
    });
  }

  _parseYaml(text) {
    const get = (key) => {
      const match = text.match(new RegExp(`^${key}:\\s*(.*)$`, "m"));
      if (!match) return "";
      let val = match[1].trim();
      if (
        (val.startsWith("'") && val.endsWith("'")) ||
        (val.startsWith('"') && val.endsWith('"'))
      ) {
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
      const quoted =
        typeof value === "string" && value.includes(" ")
          ? `'${value}'`
          : value || "''";

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
      if (beginIdx === -1) {
        parts.push({ isKms: false, text: remaining });
        break;
      }
      if (beginIdx > 0) {
        parts.push({ isKms: false, text: remaining.substring(0, beginIdx) });
      }
      const endIdx = remaining.indexOf(KMS_END, beginIdx);
      if (endIdx === -1) {
        parts.push({ isKms: true, text: remaining.substring(beginIdx) });
        break;
      }
      const blockEnd = endIdx + KMS_END.length;
      parts.push({
        isKms: true,
        text: remaining.substring(beginIdx, blockEnd),
      });
      remaining = remaining.substring(blockEnd);
    }

    return parts;
  }
};
