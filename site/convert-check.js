/* convert-check.js — cleancopy.tools' front-door check.
 *
 * `/url-to-markdown` already converts a URL to Markdown, and it sat one link
 * away from the front door while the homepage's own <h1> — «Copy any web page
 * as clean Markdown or plain text» — answered nothing. Measured 2/10: 7 of 9
 * visitors to cleancopy.tools landed on `/` and 71 % left from it; the two who
 * stayed reached the tool itself. A homepage whose headline is a promise the
 * page cannot demonstrate is the same defect as DeskUptime's, in the other
 * direction: there the check was missing, here it existed but was not on the
 * way in.
 *
 * So this is that tool, moved to the front door. One URL in, the real Markdown
 * out, in about a second. It is deliberately the *same* engine `/url-to-markdown`
 * uses — `CleanCopyCore.htmlToMarkdown` over `CleanCopyReadable.extract` — so
 * the sample on the homepage is not a demo of something else. If the converter
 * changes, this changes with it.
 *
 * What the page must not do is claim more than the check does. The fetch goes
 * through our server (`/scan-proxy`, the same open route the other six public
 * tools use) because a browser cannot fetch a third-party page itself; the
 * conversion then runs here, in the visitor's browser. So a login-walled page
 * comes back empty, and the closing sentence says so instead of hiding it.
 *
 * Retries, and the rule that a 429 is final and shows the server's own
 * sentence, live in `/net.js` with the other five clients — this file never
 * writes `.transient` or `.limited` itself, and `tools/check_net_copies.py`
 * keeps it that way.
 */
(function () {
  'use strict';
  var d = document;
  var form = d.getElementById('cc-check-form');
  if (!form || !window.NET) return;
  var input = d.getElementById('cc-check-url');
  var status = d.getElementById('cc-check-status');
  var out = d.getElementById('cc-check-result');
  var btn = form.querySelector('button[type=submit]');
  var da = (d.documentElement.lang || 'en').slice(0, 2) === 'da';
  var MAX_TRIES = 3;

  // Enough to judge the output by eye on a phone, few enough that the card does
  // not push its own follow-up links off the screen. The real conversion is on
  // the tool page; this is the first glance, and it says so.
  var PREVIEW_LINES = 24;

  var T = da ? {
    converting: 'Konverterer',
    retry: 'Serveren er trav — prøver igen …',
    busy: 'Vores konverteringsserver svarer ikke lige nu. Prøv igen om et øjeblik.',
    offline: 'Vi kunne ikke nå konverteringsserveren. Tjek din forbindelse og prøv igen.',
    failed: 'Konverteringen mislykkedes',
    converted: 'Konverteret til Markdown',
    char: 'tegn',
    chars: 'tegn',
    word: 'ord',
    words: 'ord',
    heading: 'overskrift',
    headings: 'overskrifter',
    link: 'link',
    links: 'links',
    preview: 'Første linjer af den fulde konvertering',
    truncated: 'Kun de første linjer vises ovenfor. Den fulde tekst, du kan kopiere, står på værktøjet.',
    nothing: 'Der kom ikke læsbar tekst ud af den side. Prøv en anden — en artikel eller en dokumentationsside virker bedst.',
    noCore: 'Konverteren kunne ikke hentes. Genindlæs siden, og prøv igen.'
  } : {
    converting: 'Converting',
    retry: 'Server busy — trying again …',
    busy: 'Our conversion server is not answering right now. Try again in a moment.',
    offline: 'We could not reach the conversion server. Check your connection and try again.',
    failed: 'The conversion failed',
    converted: 'Converted to Markdown',
    char: 'character',
    chars: 'characters',
    word: 'word',
    words: 'words',
    heading: 'heading',
    headings: 'headings',
    link: 'link',
    links: 'links',
    preview: 'First lines of the full conversion',
    truncated: 'Only the first lines are shown. The full text you can copy is on the tool page.',
    nothing: 'No readable text came out of that page. Try another one — an article or a documentation page works best.',
    noCore: 'The converter could not be loaded. Reload the page and try again.'
  };

  function el(tag, cls, text) {
    var n = d.createElement(tag);
    if (cls) n.className = cls;
    if (text !== undefined && text !== null) n.textContent = String(text);
    return n;
  }

  function count(t, re) {
    var m = String(t).match(re);
    return m ? m.length : 0;
  }

  // `toLocaleString` is a formatting call, not a measurement — the counts below
  // are the ones the sentence is about and they come from the string itself.
  // Each label carries a singular form, because "1 links" on the front page of
  // a product that sells correctness in text is the kind of small wrongness a
  // visitor reads without noticing and remembers.
  function stat(value, en, fa) {
    return el('span', 'cc-stat', value.toLocaleString() + ' ' + (value === 1 ? en : fa));
  }

  function render(md, url) {
    out.textContent = '';
    var trimmed = md.trim();
    var card = el('div', 'oc-card');

    var head = el('p', 'oc-verdict is-ok');
    // Stated out, as in `one-off-check.js`: `check_built_css.py` reads the
    // literal `createElement('strong')` call, not a tag name passed as an
    // argument to the local `el()` helper.
    var lead = d.createElement('strong');
    lead.textContent = T.converted;
    head.appendChild(lead);
    head.appendChild(el('span', 'oc-verdict-url', url));
    card.appendChild(head);

    var stats = el('p', 'cc-stats');
    stats.appendChild(stat(trimmed.length, T.char, T.chars));
    stats.appendChild(stat(count(trimmed, /[\p{L}\p{N}]+/gu), T.word, T.words));
    stats.appendChild(stat(count(trimmed, /^#{1,6}\s/gm), T.heading, T.headings));
    stats.appendChild(stat(count(trimmed, /\[[^\]]*\]\([^)]*\)/g), T.link, T.links));
    card.appendChild(stats);

    var lines = trimmed.split('\n');
    var shown = lines.slice(0, PREVIEW_LINES);
    // The fetched page is attacker-controlled, so the preview is `textContent`
    // and nothing else. `innerHTML` here would execute whatever the page it
    // fetched chose to put in its own markup.
    var pre = el('pre', 'cc-preview');
    pre.appendChild(el('code', null, shown.join('\n')));
    pre.setAttribute('aria-label', T.preview);
    card.appendChild(pre);
    if (lines.length > PREVIEW_LINES) {
      card.appendChild(el('p', 'oc-note', T.truncated));
    }

    // The page declares its own closing sentence and its own way onward, because
    // what this check cannot do is a property of the product, not of the check.
    // Same contract as `window.ONE_OFF_CHECK` on the other two front doors.
    var cfg = window.CONVERT_CHECK || {};
    if (typeof cfg.then === 'string' && cfg.then) {
      card.appendChild(el('p', 'oc-next', cfg.then));
    }
    var links = Array.isArray(cfg.next) ? cfg.next : [];
    if (links.length) {
      var row = el('p', 'oc-next-links');
      links.forEach(function (item) {
        if (!item || typeof item.href !== 'string' || !item.href) return;
        var a = el('a', 'btn-secondary', item.label || item.href);
        a.href = item.href;
        a.rel = 'noopener';
        row.appendChild(a);
      });
      if (row.childNodes.length) card.appendChild(row);
    }

    // Declared by the page, not here: `tools/check_donation_paths.py` judges the
    // page file, the href has to be the catalog's, and the line must not be able
    // to appear before there is a result.
    if (window.CC_DONATE) {
      var holder = d.createElement('div');
      holder.innerHTML = window.CC_DONATE;
      while (holder.firstChild) card.appendChild(holder.firstChild);
    }

    out.appendChild(card);
    out.hidden = false;
  }

  function fail(message) {
    out.textContent = '';
    var box = el('div', 'oc-card oc-card-error');
    box.appendChild(el('p', 'oc-error', message));
    out.appendChild(box);
    out.hidden = false;
  }

  // A visitor types `example.com` more often than `https://example.com`, and
  // `/scan-proxy` answers "Invalid URL" to the first one. Add the scheme here
  // rather than spend a request on something we already know will be refused.
  function normalise(value) {
    var v = String(value || '').trim();
    if (!v) return '';
    if (!/^[a-z][a-z0-9+.-]*:/i.test(v)) v = 'https://' + v.replace(/^\/+/, '');
    return v;
  }

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    var url = normalise(input.value);
    if (!url) { fail(T.failed); return; }
    // Both scripts are ours and both are on the page; saying which one is
    // missing beats converting nothing and showing a generic error.
    if (!window.CleanCopyCore || !window.CleanCopyReadable) { fail(T.noCore); return; }
    input.value = url;
    out.hidden = true;
    out.textContent = '';
    btn.disabled = true;
    status.textContent = T.converting + ' ' + url + ' …';
    NET.askGet('/scan-proxy?url=' + encodeURIComponent(url), MAX_TRIES, function () {
      status.textContent = T.retry;
    }).then(function (j) {
      // The route answers 200 with `ok: false` and its own sentence on a target
      // it will not fetch, so a body that names its error is still an error.
      if (!j || j.ok === false || j.error) {
        fail((j && j.error) || T.failed);
        status.textContent = '';
        return;
      }
      var md = CleanCopyCore.htmlToMarkdown(CleanCopyReadable.extract(j.html || ''));
      if (!md || md.replace(/[#*\->|`\[\]()]/g, '').trim().length < 20) {
        fail(T.nothing);
        status.textContent = '';
        return;
      }
      render(md, url);
      status.textContent = '';
    }, function (err) {
      // `net.js` already decided what is final. A 429 is final and carries the
      // server's own sentence; a 5xx or a dropped connection is ours to retry
      // and was retried MAX_TRIES times before we say anything.
      fail(err.transport ? T.offline : (err.transient ? T.busy : (err.message || T.failed)));
      status.textContent = '';
    // Both arms re-arm the button. A single `.then` would leave it disabled for
    // good if `render` itself threw, and a form whose only button is dead is a
    // dead end the visitor cannot get out of.
    }).then(function () { btn.disabled = false; }, function () { btn.disabled = false; });
  });
})();
