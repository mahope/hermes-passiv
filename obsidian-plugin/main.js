/* Clean Copy for Obsidian — main plugin.
 * Commands:
 *   - "Paste as clean Markdown": clipboard HTML → Markdown.
 *   - "Clean selection": clean the selected text in the current note.
 * Pro: custom cleanup rules + license activation against the same
 * /api/license/* endpoints Clean Copy Pro uses (Cloudflare Worker + KV).
 */
'use strict';

var obsidian = require('obsidian');
var CleanCopyCore = require('./core.js');

var DEFAULT_SETTINGS = {
  licenseKey: '',
  proActive: false,
  rules: [],            // Pro: [{find, replace, regex?, caseSensitive?}]
  defaultMode: 'markdown'
};

var LICENSE_API = 'https://hermes-passiv.pages.dev/api/license';

function randomDeviceId() {
  var buf = new Uint8Array(16);
  crypto.getRandomValues(buf);
  return Array.from(buf, function (b) { return b.toString(16).padStart(2, '0'); }).join('');
}

async function licenseRequest(endpoint, payload) {
  // Uses Obsidian's requestUrl (not fetch) per developer guidelines.
  var res = await obsidian.requestUrl({
    url: LICENSE_API + '/' + endpoint,
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
    throw: false,
  });
  var data = null;
  try { data = res.json; } catch (e) { data = null; }
  return { status: res.status, ok: res.status >= 200 && res.status < 300, data: data };
}

var CleanCopySettingTab = /** @class */ (function () {
  function Tab(app, plugin) {
    var _this = this;
    obsidian.PluginSettingTab.call(_this, app, plugin);
    _this.plugin = plugin;
  }
  Tab.prototype = Object.create(obsidian.PluginSettingTab.prototype);
  Tab.prototype.constructor = Tab;
  Tab.prototype.display = function () {
    var _this = this;
    var containerEl = this.containerEl;
    containerEl.empty();

    new obsidian.Setting(containerEl)
      .setName('Default paste mode')
      .setDesc('How paste as clean text or Markdown converts clipboard content.')
      .addDropdown(function (dd) {
        dd.addOption('markdown', 'Markdown');
        dd.addOption('plain', 'Plain text');
        dd.setValue(_this.plugin.settings.defaultMode);
        dd.onChange(function (v) {
          _this.plugin.settings.defaultMode = v;
          _this.plugin.saveSettings();
        });
      });

    new obsidian.Setting(containerEl)
      .setName('Clean Copy Pro license')
      .setDesc('Enter your Pro key to enable custom cleanup rules.')
      .addText(function (t) {
        t.setPlaceholder('32-character key').setValue(_this.plugin.settings.licenseKey);
        t.onChange(function (v) { _this.plugin.settings.licenseKey = v.trim(); });
      })
      .addButton(function (b) {
        b.setButtonText('Activate').onClick(function () {
          _this.plugin.activateLicense().then(function (ok) {
            new obsidian.Notice(ok ? 'Clean Copy Pro activated.' : 'Activation failed — check the key and try again.');
            _this.display();
          });
        });
      });

    if (_this.plugin.settings.proActive) {
      new obsidian.Setting(containerEl)
        .setName('Pro status')
        .setDesc('Active' + (_this.plugin.settings.expiresAt ? ' until ' + _this.plugin.settings.expiresAt.slice(0, 10) : ''))
        .addButton(function (b) {
          b.setButtonText('Deactivate locally').onClick(function () {
            _this.plugin.settings.proActive = false;
            _this.plugin.saveSettings();
            _this.display();
          });
        });
    }

    var rulesEl = containerEl.createDiv();
    rulesEl.createEl('h3', { text: 'Custom cleanup rules (Pro)' });
    if (!_this.plugin.settings.proActive) {
      rulesEl.createEl('p', { text: 'Requires an active Pro license.' });
      return;
    }
    _this.plugin.settings.rules.forEach(function (rule, i) {
      new obsidian.Setting(rulesEl)
        .setName((rule.regex ? '/' : '"') + rule.find + (rule.regex ? '/' : '"') + ' → ' + rule.replace)
        .addExtraButton(function (btn) {
          btn.setIcon('trash').setTooltip('Delete rule').onClick(function () {
            _this.plugin.settings.rules.splice(i, 1);
            _this.plugin.saveSettings();
            _this.display();
          });
        });
    });
    new obsidian.Setting(rulesEl)
      .setName('Add rule')
      .addText(function (t) { t.setPlaceholder('Find'); t.onChange(function (v) { _this._newFind = v; }); })
      .addText(function (t) { t.setPlaceholder('Replace'); t.onChange(function (v) { _this._newReplace = v; }); })
      .addExtraButton(function (btn) {
        btn.setIcon('plus').setTooltip('Add rule').onClick(function () {
          if (!_this._newFind) return;
          _this.plugin.settings.rules.push({ find: _this._newFind, replace: _this._newReplace || '' });
          _this._newFind = ''; _this._newReplace = '';
          _this.plugin.saveSettings();
          _this.display();
        });
      });
  };
  return Tab;
})();

module.exports = (function () {
  var Plugin = /** @class */ (function () {
    function Plugin_(app, manifest) {
      obsidian.Plugin.call(this, app, manifest);
      this.settings = Object.assign({}, DEFAULT_SETTINGS);
    }
    Plugin_.prototype = Object.create(obsidian.Plugin.prototype);
    Plugin_.prototype.constructor = Plugin_;

    Plugin_.prototype.onload = function () {
      var _this = this;
      (async function () {
        _this.settings = Object.assign({}, DEFAULT_SETTINGS, await _this.loadData());
        if (!_this.settings.deviceId) {
          _this.settings.deviceId = randomDeviceId();
          await _this.saveData(_this.settings);
        }

        _this.addCommand({
          id: 'paste-clean',
          name: 'Paste as clean ' + (_this.settings.defaultMode === 'markdown' ? 'Markdown' : 'text'),
          editorCallback: function (editor) { _this.pasteClean(editor); },
        });

        _this.addCommand({
          id: 'clean-selection',
          name: 'Clean selection',
          editorCallback: function (editor) { _this.cleanSelection(editor); },
        });

        if (_this.settings.proActive) {
          // Quiet per-session re-validation: revoked/expired keys lose Pro
          // immediately; network failure fails open for this session.
          _this.validateLicensePeriodic();
        }

        _this.addSettingTab(new CleanCopySettingTab(_this.app, _this));
      })();
    };

    Plugin_.prototype.onunload = function () {};

    Plugin_.prototype.saveSettings = async function () {
      await this.saveData(this.settings);
    };

    Plugin_.prototype.convert = function (htmlOrText, modeOverride) {
      var mode = modeOverride || this.settings.defaultMode;
      var res = CleanCopyCore.batchConvert([htmlOrText], mode === 'markdown' ? 'markdown' : 'plain', this.settings.proActive ? this.settings.rules : [])[0];
      return res.ok ? res.content : null;
    };

    Plugin_.prototype.pasteClean = async function (editor) {
      try {
        var items = typeof navigator !== 'undefined' && navigator.clipboard && navigator.clipboard.read ?
          await navigator.clipboard.read() : [];
        var html = null, plain = null;
        for (var _i = 0, items_1 = items; _i < items_1.length; _i++) {
          var item = items_1[_i];
          if (!html && item.types.indexOf('text/html') !== -1) html = await (await item.getType('text/html')).text();
          if (!plain && item.types.indexOf('text/plain') !== -1) plain = await (await item.getType('text/plain')).text();
        }
        var src = html != null ? html : (plain != null ? plain : '');
        if (!src) { new obsidian.Notice('Clipboard is empty.'); return; }
        var out = this.convert(src, html != null ? undefined : 'plain');
        editor.replaceSelection(out == null ? '' : out);
      } catch (e) {
        // Clipboard read can be denied on some platforms; fall back to
        // letting Obsidian's normal paste run, cleaned post-hoc is not
        // possible without DOM parsing, so tell the user honestly.
        new obsidian.Notice('Could not read clipboard. Use Paste, then Clean selection.');
      }
    };

    Plugin_.prototype.cleanSelection = function (editor) {
      var sel = editor.getSelection();
      if (!sel) { new obsidian.Notice('Select some text first.'); return; }
      var looksLikeHtml = /<\/?[a-z][^>]*>/i.test(sel);
      var out = this.convert(sel, looksLikeHtml ? undefined : 'plain');
      if (out == null) return;
      editor.replaceSelection(out);
    };

    Plugin_.prototype.activateLicense = async function () {
      var key = this.settings.licenseKey.toLowerCase().trim();
      if (!/^[a-f0-9]{32}$/.test(key)) return false;
      try {
        var res = await licenseRequest('activate', { license_key: key, device_id: this.settings.deviceId });
        if (!res.ok || !res.data || !res.data.ok) {
          new obsidian.Notice((res.data && res.data.error) || 'Activation failed.');
          return false;
        }
        this.settings.proActive = true;
        this.settings.expiresAt = res.data.expires_at || null;
        await this.saveSettings();
        return true;
      } catch (e) {
        new obsidian.Notice('Network error during activation.');
        return false;
      }
    };

    Plugin_.prototype.validateLicensePeriodic = async function () {
      // Called once per session after load when proActive: re-validate quietly.
      if (!this.settings.proActive) return;
      var key = this.settings.licenseKey.toLowerCase().trim();
      if (!/^[a-f0-9]{32}$/.test(key)) { this.settings.proActive = false; return; }
      try {
        var res = await licenseRequest('validate', { license_key: key, device_id: this.settings.deviceId });
        if (res.status === 403 || (res.data && res.data.valid === false)) {
          this.settings.proActive = false;
          await this.saveSettings();
          new obsidian.Notice('Clean Copy Pro license is no longer valid.');
        } else if (res.ok && res.data && res.data.ok) {
          this.settings.expiresAt = res.data.expires_at || this.settings.expiresAt;
          await this.saveSettings();
        }
        // Network failure → stay pro-active offline (fail-open per session,
        // re-checked next launch). Never locks a paying user out mid-flight.
      } catch (e) { /* offline: fail open for this session */ }
    };

    Plugin_.prototype.registerProCommands = function () {};

    return Plugin_;
  })();
  return Plugin;
})();
