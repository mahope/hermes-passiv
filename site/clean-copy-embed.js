/* clean-copy-embed.js — the converter, inside the guides that explain it.
 *
 * Why: the three HTML-to-Markdown guides on cleancopy.tools had 3, 2 and 2
 * visitors in 28 days (Plausible, 10/10) with 50–67 % bounce. They link to
 * /clean-copy-tool but do not contain it — a reader who came for «how do I
 * convert this» has to leave the text to try it. mahope.tools' contrast
 * guide showed the other pattern works: the tool inside the article is what
 * moves a reader from reading to using.
 *
 * A page declares where the converter belongs and nothing else:
 *
 *     <div id="cc-embed"></div>
 *     <script>window.CC_EMBED = { path: '/blog/html-to-markdown-cli' };</script>
 *     <script src="/clean-copy-core.js"></script>
 *     <script src="/clean-copy-embed.js"></script>
 *
 * Same engine as /clean-copy-tool (CleanCopyCore, MIT on GitHub), same four
 * modes, same rule as the tool page: the text is converted here and never
 * uploaded. Batch conversion is Pro and sits behind the same license check
 * the tool page uses — the canonical rules below, byte for byte, and the
 * same localStorage keys, so a key activated on the tool page is already
 * active here (both pages are the same origin). Activation itself stays on
 * the tool page: one form, one seat counter, and one place to release a
 * seat, instead of a second activation flow that can drift from the first.
 */
/* >>> clean-copy-license: tools/clean_copy_license.js — do not edit by hand */
/* Clean Copy — canonical license client rules.
 *
 * This file is the single source of truth for how a Clean Copy client talks
 * to the license API. It is inlined verbatim into every shipped client
 * (Chrome extension, Firefox add-on, Obsidian plugin, web tool);
 * `tools/check_license_clients.py` fails if a copy drifts from these bytes.
 *
 * Contract (24/9-2026): keys are 32 lowercase hex characters, product is
 * `clean-copy-pro`, and a paying customer must never be locked out by a
 * license-server outage — hence the seven-day positive cache.
 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.CleanCopyLicense = factory();
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  var PRODUCT = 'clean-copy-pro';
  var API_BASE = 'https://mahope.tools/api/license';
  var CACHE_MAX_MS = 7 * 24 * 60 * 60 * 1000;

  function normalizeKey(key) {
    return String(key === null || key === undefined ? '' : key).trim().toLowerCase();
  }

  function isKeyFormat(key) {
    return /^[a-f0-9]{32}$/.test(normalizeKey(key));
  }

  // status 0 = the request never got an answer (offline, DNS, timeout).
  function isServerError(status) {
    return status === 0 || status >= 500;
  }

  /* Decide what a client shows, from one HTTP exchange.
   * opts: { status, data, checkedAt, expiresAt, now }
   * Returns { active, message, cached, checkedAt, expiresAt }. */
  function decide(opts) {
    var status = opts.status;
    var data = opts.data || {};
    var now = typeof opts.now === 'number' ? opts.now : Date.now();
    var checkedAt = typeof opts.checkedAt === 'number' ? opts.checkedAt : 0;

    if (status === 200 && data.ok && (data.activated === true || data.valid === true)) {
      return {
        active: true, message: '', cached: false,
        checkedAt: now, expiresAt: data.expires_at || opts.expiresAt || ''
      };
    }

    if (isServerError(status)) {
      if (checkedAt > 0 && now - checkedAt <= CACHE_MAX_MS) {
        return {
          active: true, cached: true, checkedAt: checkedAt,
          expiresAt: opts.expiresAt || '',
          message: 'License server unreachable — Pro stays active until ' +
            new Date(checkedAt + CACHE_MAX_MS).toISOString().slice(0, 10) + '.'
        };
      }
      return {
        active: false, cached: false, checkedAt: 0, expiresAt: '',
        message: 'License server unreachable. Try again later — Pro comes back on its own.'
      };
    }

    if (status === 409) {
      return { active: false, message: data.error || 'Device limit reached for this license.', checkedAt: 0, expiresAt: '' };
    }
    if (status === 403) {
      return { active: false, message: data.error || 'This license is expired, revoked, or for another product.', checkedAt: 0, expiresAt: '' };
    }
    if (status === 404) {
      return { active: false, message: data.error || 'License key not found.', checkedAt: 0, expiresAt: '' };
    }
    if (status === 400) {
      return { active: false, message: data.error || 'Invalid license key.', checkedAt: 0, expiresAt: '' };
    }
    if (status === 200) {
      return {
        active: false, message: data.reason === 'device_limit'
          ? 'Device limit reached for this license.'
          : (data.error || 'This license is not valid anymore.'),
        checkedAt: 0, expiresAt: ''
      };
    }
    return { active: false, message: data.error || 'License check failed. Try again.', checkedAt: 0, expiresAt: '' };
  }

  function payload(key, deviceId) {
    return { license_key: normalizeKey(key), device_id: String(deviceId || ''), product: PRODUCT };
  }

  return {
    PRODUCT: PRODUCT, API_BASE: API_BASE, CACHE_MAX_MS: CACHE_MAX_MS,
    normalizeKey: normalizeKey, isKeyFormat: isKeyFormat,
    isServerError: isServerError, decide: decide, payload: payload
  };
});
/* <<< clean-copy-license */

/* --------------------------------------------------------------------------
 * The embed itself. Markup is built here, not declared per page: three
 * articles would otherwise carry the same hundred lines of form, and a fix
 * in one of them would ship in one place and not in the others. Text is
 * set with textContent, never innerHTML — the converter's input can end up
 * in a status line, and a status line must not be an HTML sink.
 * -------------------------------------------------------------------------- */
(function () {
  'use strict';
  var d = document;
  var host = d.getElementById('cc-embed');
  if (!host || !window.CleanCopyCore || !window.CleanCopyLicense) return;
  var L = window.CleanCopyLicense;
  var cfg = window.CC_EMBED || {};
  var da = (d.documentElement.lang || 'en').slice(0, 2) === 'da';

  var T = da ? {
    input: 'Sæt HTML eller formateret tekst ind',
    output: 'Ren Markdown',
    hint: 'Kører i din browser — intet bliver sendt til os.',
    smart: 'Erstat krøllede anførselstegn og tankestreger',
    sample: 'Hent et eksempel',
    clear: 'Ryd',
    copy: 'Kopiér resultatet',
    copied: 'Kopieret til udklipsholderen',
    empty: 'Der er ikke noget at kopiere endnu.',
    stats: function (c, w) { return c + ' tegn · ' + w + ' ord'; },
    modes: ['Markdown', 'WikiLinks', 'CSV', 'Ren tekst'],
    privacy: 'Konverteringen kører i JavaScript på denne side — din tekst forlader aldrig browseren. Har du aktiveret en Clean Copy Pro-nøgle, tjekkes kun den nøgle og et enheds-id mod vores licens-API på mahope.tools, så Pro-funktionerne forbliver slået til.',
    nudgeTitle: 'Ét stykke ad gangen?',
    nudgeLead: 'Det tilføjer Pro oven i denne konverter:',
    nudgeBatch: 'Batch-konvertering. Ét tryk renser mange stykker — ét pr. linje — i stedet for én indsættelse ad gangen.',
    nudgeRules: 'Egne rengøringsregler. I browserudvidelsen: skriv dine egne regler én gang og genbrug dem på alle sider.',
    nudgeKeep: 'Intet bliver taget fra dig. Alle fire tilstande på denne side, og ingen grænse for hvor meget tekst du sætter ind, forbliver gratis.',
    nudgeBuy: 'Køb Clean Copy Pro — 19 $/år',
    nudgeNote: 'Én licens dækker 5 enheder. Aktivér den på webværktøjet, så åbnes batch-konverteringen også her.',
    toolLink: 'Åbn webværktøjet',
    batchTitle: 'Batch-konvertering (Pro) — mange stykker på én gang',
    batchHint: 'Sæt ét stykke pr. linje. Linjer der starter med < konverteres som HTML, resten som ren tekst. Resultaterne kommer én pr. linje, i samme rækkefølge.',
    batchInput: 'Stykker (ét pr. linje)',
    batchOutput: 'Resultater',
    batchBtn: 'Konvertér alle',
    batchCopy: 'Kopiér resultater',
    batchOk: function (n) { return 'Konverterede ' + n + ' stykker.'; },
    batchFail: function (n, f) { return n + ' stykker — ' + f + ' fejlede.'; },
    batchEmpty: 'Sæt mindst ét stykke ind.',
    batchCopied: 'Resultaterne er kopieret.',
    batchClip: 'Kunne ikke få adgang til udklipsholderen.',
    proNote: 'Har du allerede en licensnøgle? Aktivér den på webværktøjet — herefter åbnes batch-konverteringen også her.'
  } : {
    input: 'Paste HTML or formatted text',
    output: 'Clean Markdown',
    hint: 'Runs in your browser — nothing is uploaded.',
    smart: 'Replace smart quotes & dashes',
    sample: 'Load sample',
    clear: 'Clear',
    copy: 'Copy result',
    copied: 'Copied to clipboard',
    empty: 'Nothing to copy yet.',
    stats: function (c, w) { return c + ' chars · ' + w + ' words'; },
    modes: ['Markdown', 'WikiLinks', 'CSV', 'Plain text'],
    privacy: 'The conversion runs in JavaScript on this page — your text never leaves the browser. If you have activated a Clean Copy Pro key, only that key and a device id are checked against our license API on mahope.tools, so Pro features stay switched on.',
    nudgeTitle: 'Cleaning one snippet at a time?',
    nudgeLead: 'What Pro adds on top of this converter:',
    nudgeBatch: 'Batch conversion. One click cleans many snippets — one per line — instead of one paste at a time.',
    nudgeRules: 'Custom cleanup rules. In the browser extension: write your own rules once and reuse them on every site.',
    nudgeKeep: 'Nothing here is taken away. All four modes on this page, and no limit on how much text you paste, stay free.',
    nudgeBuy: 'Buy Clean Copy Pro — $19/year',
    nudgeNote: 'One licence covers 5 devices. Activate it on the web tool and batch conversion unlocks here too.',
    toolLink: 'Open the web tool',
    batchTitle: 'Batch conversion (Pro) — many snippets at once',
    batchHint: 'Paste one snippet per line. Lines starting with < are converted as HTML, the rest as plain text. Results come back one per line, in the same order.',
    batchInput: 'Snippets (one per line)',
    batchOutput: 'Results',
    batchBtn: 'Convert all',
    batchCopy: 'Copy results',
    batchOk: function (n) { return 'Converted ' + n + ' snippets.'; },
    batchFail: function (n, f) { return n + ' snippets — ' + f + ' failed.'; },
    batchEmpty: 'Paste at least one snippet.',
    batchCopied: 'Results copied.',
    batchClip: 'Could not access clipboard.',
    proNote: 'Already have a license key? Activate it on the web tool — batch conversion unlocks here afterwards.'
  };

  // Created nodes are kept in closure references — no id registry, and no
  // patch of `document.getElementById` that the page's other scripts (shell,
  // tracking) would inherit.
  function el(tag, cls, text) {
    var n = d.createElement(tag);
    if (cls) n.className = cls;
    if (text !== undefined && text !== null) n.textContent = String(text);
    return n;
  }
  function anchor(href, cls, text) {
    var a = el('a', cls, text);
    a.href = href;
    return a;
  }

  var toolHref = da ? '/da/clean-copy-tool' : '/clean-copy-tool';

  // ── the converter ───────────────────────────────────────────────────
  var grid = el('div', 'cc-grid');
  var paneIn = el('div', 'cc-pane');
  var labIn = el('label', null, T.input);
  labIn.setAttribute('for', 'cc-input');
  var input = el('textarea', 'cc-box');
  input.id = 'cc-input';
  input.placeholder = da ? 'Sæt formateret tekst ind (kopieret fra en webside, Word, mail…) eller rå HTML…' : 'Paste richly formatted text (copied from a web page, Word, email…) or raw HTML…';
  var paneOut = el('div', 'cc-pane');
  var labOut = el('label', null, T.output);
  labOut.setAttribute('for', 'cc-output');
  var output = el('textarea', 'cc-box');
  output.id = 'cc-output';
  output.setAttribute('readonly', '');
  output.setAttribute('aria-live', 'polite');
  var stats = el('p', 'cc-stats');
  stats.id = 'cc-stats';
  stats.setAttribute('aria-live', 'polite');
  paneIn.appendChild(labIn); paneIn.appendChild(input);
  paneOut.appendChild(labOut); paneOut.appendChild(output); paneOut.appendChild(stats);
  grid.appendChild(paneIn); grid.appendChild(paneOut);

  var bar = el('div', 'cc-bar');
  var modes = el('div', 'cc-modes');
  modes.setAttribute('role', 'group');
  modes.setAttribute('aria-label', da ? 'Outputformat' : 'Output format');
  var mode = 'markdown';
  var modeButtons = {};
  ['markdown', 'wikilinks', 'csv', 'plain'].forEach(function (m, i) {
    var b = el('button', null, T.modes[i]);
    b.type = 'button';
    b.id = 'cc-mode-' + m;
    b.setAttribute('aria-pressed', m === 'markdown' ? 'true' : 'false');
    b.addEventListener('click', function () { setMode(m); });
    modeButtons[m] = b;
    modes.appendChild(b);
  });
  var smart = el('input');
  smart.type = 'checkbox';
  smart.id = 'cc-smart';
  var smartLab = el('label', 'cc-smart-lab', T.smart);
  smartLab.setAttribute('for', 'cc-smart');
  var sample = el('button', 'btn-secondary', T.sample);
  sample.type = 'button'; sample.id = 'cc-sample';
  sample.addEventListener('click', loadSample);
  var clear = el('button', 'btn-secondary', T.clear);
  clear.type = 'button'; clear.id = 'cc-clear';
  clear.addEventListener('click', function () {
    input.value = ''; output.value = ''; stats.textContent = ''; setStatus('');
    nudge.hidden = true;
    input.focus();
  });
  bar.appendChild(modes);
  bar.appendChild(smartLab); smartLab.appendChild(smart);
  bar.appendChild(sample);
  bar.appendChild(clear);

  var copyBtn = el('button', 'btn-primary', T.copy);
  copyBtn.type = 'button'; copyBtn.id = 'cc-copy';
  copyBtn.addEventListener('click', copyResult);
  var status = el('span', 'cc-status');
  status.id = 'cc-status';
  status.setAttribute('role', 'status');
  var copyBar = el('div', 'cc-bar');
  copyBar.appendChild(copyBtn); copyBar.appendChild(status);

  var nudge = el('div', 'pro-card');
  nudge.id = 'cc-nudge';
  nudge.hidden = true;
  (function buildNudge() {
    nudge.appendChild(el('h3', null, T.nudgeTitle));
    nudge.appendChild(el('p', 'pro-lead', T.nudgeLead));
    var ul = el('ul', 'pro-list');
    ul.appendChild(el('li', null, T.nudgeBatch));
    ul.appendChild(el('li', null, T.nudgeRules));
    ul.appendChild(el('li', null, T.nudgeKeep));
    nudge.appendChild(ul);
    var buy = anchor('https://buy.stripe.com/6oU4gy76PgvgdBIdAXbMQ00', 'btn-primary', T.nudgeBuy);
    buy.rel = 'nofollow noopener';
    var p = el('p'); p.appendChild(buy);
    nudge.appendChild(p);
    var note = el('p', 'pro-card-note');
    note.appendChild(document.createTextNode(T.nudgeNote + ' '));
    note.appendChild(anchor(toolHref, null, T.toolLink + ' →'));
    nudge.appendChild(note);
  })();

  // ── batch conversion, behind the license ────────────────────────────
  var batch = el('details', 'cc-batch');
  batch.id = 'cc-batch';
  batch.hidden = true;
  var batchSum = el('summary', null, T.batchTitle);
  var batchHintP = el('p', 'cc-hint', T.batchHint);
  var bGrid = el('div', 'cc-grid');
  var bPaneIn = el('div', 'cc-pane');
  var bLabIn = el('label', null, T.batchInput);
  bLabIn.setAttribute('for', 'cc-batch-input');
  var bIn = el('textarea', 'cc-box');
  bIn.id = 'cc-batch-input';
  var bPaneOut = el('div', 'cc-pane');
  var bLabOut = el('label', null, T.batchOutput);
  bLabOut.setAttribute('for', 'cc-batch-output');
  var bOut = el('textarea', 'cc-box');
  bOut.id = 'cc-batch-output';
  bOut.setAttribute('readonly', '');
  bOut.setAttribute('aria-live', 'polite');
  bPaneIn.appendChild(bLabIn); bPaneIn.appendChild(bIn);
  bPaneOut.appendChild(bLabOut); bPaneOut.appendChild(bOut);
  bGrid.appendChild(bPaneIn); bGrid.appendChild(bPaneOut);
  var bBar = el('div', 'cc-bar');
  var bBtn = el('button', 'btn-primary', T.batchBtn);
  bBtn.type = 'button'; bBtn.id = 'cc-batch-btn';
  bBtn.addEventListener('click', runBatch);
  var bCopy = el('button', 'btn-secondary', T.batchCopy);
  bCopy.type = 'button'; bCopy.id = 'cc-batch-copy';
  bCopy.addEventListener('click', copyBatch);
  var bStatus = el('span', 'cc-status');
  bStatus.id = 'cc-batch-status';
  bStatus.setAttribute('role', 'status');
  bBar.appendChild(bBtn); bBar.appendChild(bCopy); bBar.appendChild(bStatus);
  var proNote = el('p', 'cc-pro-note');
  proNote.id = 'cc-pro-note';
  proNote.appendChild(document.createTextNode(T.proNote + ' '));
  proNote.appendChild(anchor(toolHref, null, T.toolLink + ' →'));
  batch.appendChild(batchSum); batch.appendChild(batchHintP);
  batch.appendChild(bGrid); batch.appendChild(bBar); batch.appendChild(proNote);

  var privacy = el('p', 'cc-privacy', T.privacy);

  host.appendChild(grid);
  host.appendChild(bar);
  host.appendChild(copyBar);
  host.appendChild(nudge);
  host.appendChild(batch);
  host.appendChild(privacy);

  // ── conversion ──────────────────────────────────────────────────────
  function looksLikeHtml(s) {
    return /<\/?(?:p|div|span|h[1-6]|ul|ol|li|a|b|strong|i|em|br|code|pre|table)\b/i.test(s)
      || /&(?:amp|lt|gt|quot|nbsp);/.test(s);
  }
  function setMode(m) {
    mode = m;
    ['markdown', 'wikilinks', 'csv', 'plain'].forEach(function (k) {
      var b = modeButtons[k];
      if (b) b.setAttribute('aria-pressed', k === m ? 'true' : 'false');
    });
    convert();
  }
  function setStatus(msg, isErr) {
    status.textContent = msg || '';
    status.className = msg ? (isErr ? 'cc-status err' : 'cc-status ok') : 'cc-status';
  }
  function convert() {
    var raw = input.value || '';
    if (!raw.trim()) { output.value = ''; stats.textContent = ''; setStatus(''); nudge.hidden = true; return; }
    try {
      var result;
      if (looksLikeHtml(raw)) {
        var doc = new DOMParser().parseFromString(raw, 'text/html');
        result = mode === 'wikilinks' ? window.CleanCopyCore.htmlToWikilinks(doc.body.innerHTML)
          : mode === 'csv' ? window.CleanCopyCore.htmlToCsv(doc.body.innerHTML)
          : window.CleanCopyCore.htmlToMarkdown(doc.body.innerHTML);
      } else if (mode === 'markdown') {
        result = smart.checked ? window.CleanCopyCore.cleanText(raw) : raw.replace(/\u00A0/g, ' ').trim();
      } else {
        var doc2 = new DOMParser().parseFromString(raw, 'text/html');
        result = window.CleanCopyCore.cleanText(doc2.body.textContent || '');
      }
      output.value = result;
      var words = String(result).split(/\s+/).filter(Boolean).length;
      stats.textContent = T.stats(String(result).length, words);
      setStatus('');
      nudge.hidden = false;
      trackUse();
    } catch (err) {
      output.value = '';
      setStatus((da ? 'Konverteringen fejlede: ' : 'Conversion failed: ') + (err && err.message ? err.message : err), true);
    }
  }
  input.addEventListener('input', convert);
  smart.addEventListener('change', convert);

  function loadSample() {
    input.value = '<h2>Quarterly Update</h2>\n<p>Revenue grew <strong>34%</strong> \u2014 driven by '
      + 'the <em>EU launch</em>. Full report at <a href="https://example.com/report">example.com/report</a>.</p>'
      + '<ul><li>Hired 6 engineers</li><li>Shipped v2<ul><li>New editor</li><li>Offline mode</li></ul></li></ul>'
      + '<p>Contact: \u201Cteam\u201D <code>ops@example.com</code></p>';
    convert();
  }

  function copyResult() {
    if (!output.value) { setStatus(T.empty, true); return; }
    writeClipboard(output.value, function (okFlag) {
      setStatus(okFlag ? T.copied : T.empty, !okFlag);
    });
  }
  function writeClipboard(text, done) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(function () { done(true); }, function () { done(false); });
    } else { done(false); }
  }

  // One anonymous event per page, like the tool page's. No text, no key.
  var tracked = false;
  function trackUse() {
    if (tracked) return;
    tracked = true;
    try {
      if (navigator.doNotTrack === '1') return;
      fetch('/api/track', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: cfg.path || '', event: 'convert' }),
        keepalive: true
      }).catch(function () {});
    } catch (e) {}
  }

  // ── batch ───────────────────────────────────────────────────────────
  function runBatch() {
    var lines = (bIn.value || '').split('\n').filter(function (l) { return l.trim().length > 0; });
    if (!lines.length) { bStatus.textContent = T.batchEmpty; bStatus.className = 'cc-status err'; return; }
    var results = window.CleanCopyCore.batchConvert(lines.map(function (l) {
      if (!looksLikeHtml(l)) return l;
      var doc = new DOMParser().parseFromString(l, 'text/html');
      return { html: doc.body.innerHTML };
    }), 'markdown');
    bOut.value = results.map(function (r) {
      return r.ok ? r.content.replace(/\n+/g, ' ').trim() : '[error] ' + r.error;
    }).join('\n');
    var failed = results.filter(function (r) { return !r.ok; }).length;
    bStatus.textContent = failed ? T.batchFail(results.length, failed) : T.batchOk(results.length);
    bStatus.className = 'cc-status ' + (failed ? 'err' : 'ok');
  }
  function copyBatch() {
    if (!bOut.value) { bStatus.textContent = T.empty; bStatus.className = 'cc-status err'; return; }
    writeClipboard(bOut.value, function (okFlag) {
      bStatus.textContent = okFlag ? T.batchCopied : T.batchClip;
      bStatus.className = 'cc-status ' + (okFlag ? 'ok' : 'err');
    });
  }

  // ── the license gate in front of batch ──────────────────────────────
  function deviceId() {
    try {
      var dev = localStorage.getItem('cc_device_id');
      if (!dev) {
        dev = crypto.randomUUID ? crypto.randomUUID() : String(Math.random()).slice(2) + Date.now();
        localStorage.setItem('cc_device_id', dev);
      }
      return dev;
    } catch (e) { return 'anon-' + String(Math.random()).slice(2); }
  }
  function readStore(name) { try { return localStorage.getItem(name) || ''; } catch (e) { return ''; } }
  function writeStore(name, value) { try { localStorage.setItem(name, value); } catch (e) {} }
  function dropStore(name) { try { localStorage.removeItem(name); } catch (e) {} }

  function enableBatch(on) {
    batch.hidden = !on;
    proNote.hidden = on; // the "activate on the web tool" line is only for readers without a key
  }
  function licenseCall(key) {
    // Valideringen går gennem `net.js` — den eneste kæde der læser status
    // før krop, så en 429 forbliver endelig og en 5xx er vor egen nedetid.
    // Siden der glemmer script-tagget kan ikke spørge serveren: status 0
    // fortæller decide() at tjekket ikke kom igennem, og syvdagesreglen
    // afgør om Pro holder — præcis som ved en rigtig nedetid.
    if (!window.NET || !window.NET.postJSON) return Promise.resolve({ status: 0, data: {} });
    return window.NET.postJSON('/api/license/validate', L.payload(key, deviceId())).then(
      function (data) { return { status: 200, data: data }; },
      function (err) {
        return { status: err && err.status ? err.status : 0, data: { error: err && err.message } };
      }
    );
  }
  function applyDecision(dec) {
    if (dec.active) {
      enableBatch(true);
      if (!dec.cached) writeStore('cc_pro_checked', String(Date.now()));
      if (dec.cached) batchSum.textContent = T.batchTitle + ' — ' + dec.message;
    } else {
      dropStore('cc_pro_license');
      dropStore('cc_pro_expires');
      dropStore('cc_pro_checked');
      enableBatch(false);
      bStatus.textContent = dec.message;
      bStatus.className = 'cc-status err';
    }
  }

  try {
    var saved = L.normalizeKey(readStore('cc_pro_license'));
    var expiresSaved = readStore('cc_pro_expires');
    if (!saved) {
      enableBatch(false);
    } else if (expiresSaved && expiresSaved <= new Date().toISOString()) {
      dropStore('cc_pro_license'); dropStore('cc_pro_expires'); dropStore('cc_pro_checked');
      enableBatch(false);
    } else {
      // Show Pro immediately from the local copy, then re-validate quietly.
      enableBatch(true);
      licenseCall(saved).then(function (res) {
        applyDecision(L.decide({
          status: res.status,
          data: res.data,
          checkedAt: Number(readStore('cc_pro_checked')) || 0,
          expiresAt: expiresSaved
        }));
      });
    }
  } catch (e) {}
})();
