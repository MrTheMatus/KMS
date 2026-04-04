import { PluginSettingTab, Setting } from "obsidian";
import { _t } from "./i18n";

export class KmsSettingsTab extends PluginSettingTab {
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

    new Setting(containerEl)
      .setName(t("settingProfile"))
      .setDesc(t("settingProfileDesc"))
      .addDropdown((dropdown) =>
        dropdown
          .addOption("core", t("profileCore"))
          .addOption("ai-local", t("profileAiLocal"))
          .addOption("ai-cloud", t("profileAiCloud"))
          .setValue(this.plugin.settings.profile)
          .onChange(async (value) => {
            this.plugin.settings.profile = value;
            await this.plugin.saveSettings();
          }),
      );

    containerEl.createEl("h3", { text: t("settingAnythingLLMHeader") });

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
