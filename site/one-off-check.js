/* one-off-check.js — the front-door check, shared by every site's <h1>.
 *
 * It started on deskuptime.com, whose <h1> asks three questions — is the site
 * up, is the certificate still valid, did the page change — and answered none
 * of them: it asked the visitor to install a CLI to get the first two, and the
 * two free web checkers sat ~120 lines of prose further down the page.
 * Measured 2/10: 4 visitors to deskuptime.com in 28 days, 100 % bounce, 0 s.
 *
 * So the front door answers what it can: one check, from our own server, in
 * about a second. `/api/url-inspect` already returned status, redirect chain,
 * security headers and a live TLS handshake — it was just never called from
 * here. Which headers we look for is the *worker's* list, read from
 * `securityHeadersChecked` in the answer, because hard-coding the eight names
 * in a second place is how a list silently rots.
 *
 * The page owns its own words. What this check cannot do, and where the visitor
 * goes next, differ per site — DeskUptime's answer ends in "that is the CLI and
 * the desktop app", mahope.tools' in "here is the scanner that goes deeper" —
 * so both live in `window.ONE_OFF_CHECK = { then, next: [{label, href}] }` on
 * the page itself, next to the form they belong to. Nothing about a single
 * product is hard-coded here; a page that declares neither still renders the
 * verdict, cert and header chips, and simply has no follow-up.
 *
 * The form is a real GET to /api/url-inspect, so without JavaScript it still
 * checks the site and shows the raw answer. Retry policy, and the rule that a
 * 429 is final and shows the server's own sentence, live in /net.js with the
 * other five clients; `tools/check_net_copies.py` keeps it the only copy.
 */
(function () {
  'use strict';
  var d = document;
  var form = d.getElementById('oc-check-form');
  if (!form || !window.NET) return;
  var input = d.getElementById('oc-check-url');
  var status = d.getElementById('oc-check-status');
  var out = d.getElementById('oc-check-result');
  var btn = form.querySelector('button[type=submit]');
  var da = (d.documentElement.lang || 'en').slice(0, 2) === 'da';
  var MAX_TRIES = 3;

  var T = da ? {
    checking: 'Tjekker',
    retry: 'Serveren er trav — prøver igen …',
    busy: 'Vores tjek-server svarer ikke lige nu. Prøv igen om et øjeblik.',
    offline: 'Vi kunne ikke nå tjek-serveren. Tjek din forbindelse og prøv igen.',
    failed: 'Tjekket mislykkedes',
    reachable: 'Sitet svarede',
    viaRedirects: 'Sitet svarede efter',
    unreachable: 'Serveren fik ikke et svar fra sitet',
    redirects: 'omdirigeringer',
    finalUrl: 'Slutadresse',
    cert: 'Certifikat',
    daysLeft: 'dage tilbage',
    expiredDays: 'udløb for',
    daysAgo: 'dage siden',
    expires: 'Udløber',
    issuer: 'Udstedt af',
    chain: 'Kæde',
    chainOk: 'Serveren stoler på kæden',
    chainBad: 'Kæden er ikke tillid',
    protocol: 'Protokol',
    headers: 'Sikkerhedsoverskrifter',
    present: 'findes',
    missing: 'mangler',
    none: 'Ingen af de otte er med i svaret.',
    // De tre grunde serveren kan give for et certifikat, den ikke fik læst.
    sslNoHttps: 'Slutadressen er ikke HTTPS',
    sslUnavailable: 'Certifikat-opslaget var ikke tilgængeligt',
    sslFailed: 'Certifikat-opslaget mislykkedes eller tog for lang tid'
  } : {
    checking: 'Checking',
    retry: 'Server busy — trying again …',
    busy: 'Our check server is not answering right now. Try again in a moment.',
    offline: 'We could not reach the check server. Check your connection and try again.',
    failed: 'The check failed',
    reachable: 'The site answered',
    viaRedirects: 'The site answered after',
    unreachable: 'The server got no answer from the site',
    redirects: 'redirects',
    finalUrl: 'Final address',
    cert: 'Certificate',
    daysLeft: 'days left',
    expiredDays: 'expired',
    daysAgo: 'days ago',
    expires: 'Expires',
    issuer: 'Issued by',
    chain: 'Chain',
    chainOk: 'the server trusts this chain',
    chainBad: 'the chain is not trusted',
    protocol: 'Protocol',
    headers: 'Security headers',
    present: 'present',
    missing: 'missing',
    none: 'None of the eight came back.',
    sslNoHttps: 'The final address is not HTTPS',
    sslUnavailable: 'The certificate lookup was unavailable',
    sslFailed: 'The certificate lookup failed or timed out'
  };

  var MONTHS_DA = ['januar', 'februar', 'marts', 'april', 'maj', 'juni', 'juli',
    'august', 'september', 'oktober', 'november', 'december'];
  var MONTHS_EN = ['January', 'February', 'March', 'April', 'May', 'June', 'July',
    'August', 'September', 'October', 'November', 'December'];

  // `validTo` is an ISO timestamp. Formatting the date part as text avoids a
  // Date parse altogether, so a certificate cannot be shown as expiring the
  // day before it does because the reader is west of UTC.
  function certDate(iso) {
    var m = /^(\d{4})-(\d{2})-(\d{2})/.exec(String(iso || ''));
    if (!m) return String(iso || '');
    var day = parseInt(m[3], 10), month = parseInt(m[2], 10) - 1;
    if (isNaN(day) || month < 0 || month > 11) return String(iso);
    return day + ' ' + (da ? MONTHS_DA[month] : MONTHS_EN[month]) + ' ' + m[1];
  }

  // The worker's `reason` is its own sentence and is the truth when we get one.
  // These three are the only ones it can return; anything else is shown in the
  // server's own words rather than guessed at.
  function sslReason(reason) {
    var r = String(reason || '');
    if (/not HTTPS/i.test(r)) return T.sslNoHttps;
    if (/unavailable/i.test(r)) return T.sslUnavailable;
    if (/failed or timed out/i.test(r)) return T.sslFailed;
    return r;
  }

  function el(tag, cls, text) {
    var n = d.createElement(tag);
    if (cls) n.className = cls;
    if (text !== undefined && text !== null) n.textContent = String(text);
    return n;
  }

  function row(dl, term, value) {
    var wrap = el('div', 'oc-row');
    wrap.appendChild(el('dt', null, term));
    var dd = el('dd');
    if (value instanceof Node) dd.appendChild(value); else dd.textContent = String(value);
    wrap.appendChild(dd);
    dl.appendChild(wrap);
  }

  // The list of names to look for comes from the worker, so a change to its
  // `secHeaders` cannot leave eight stale names in this file. Which of them are
  // present is always read from the answer's `securityHeaders`, never guessed
  // from this list — so the fallback below only supplies the names to look for.
  var FALLBACK_HEADERS = ['strict-transport-security', 'content-security-policy',
    'x-content-type-options', 'x-frame-options', 'x-xss-protection',
    'referrer-policy', 'permissions-policy', 'access-control-allow-origin'];

  function verdict(data) {
    var code = Number(data.finalStatus) || 0;
    var hops = Number(data.totalRedirects) || 0;
    if (code === 0) return T.unreachable;
    if (code >= 200 && code < 300) {
      return hops ? T.viaRedirects + ' ' + hops + ' ' + T.redirects : T.reachable;
    }
    return T.reachable + ' with ' + code + ' ' + (data.finalStatusText || '');
  }

  // Den adresse læseren lige har tjekket rejser med videre.
  //
  // Målt 2/10: `#url=` er ikke en ny idé her — fem sider læser den allerede og
  // kører på den (`/scan`, `/scan-da`, `/cookie-check`, `/cookie-check-da`,
  // `/compliance-report`), og syv platform-guides linker til `/scan#url=…`.
  // Men **ingen side i familien producerede den**: den der tjekkede sit site på
  // forsiden og trykkede «Fuld WCAG-scanning» landede på `/scan` med et tomt
  // felt og skulle skrive den samme adresse ind en gang til. Den dybeste
  // handling på den side — den scanner der sælger EUComply Pro til $79 pr. år —
  // startede altså med at spørge om noget læseren allerede havde svaret på.
  //
  // Siden erklærer selv hvilke af *dens* links der vil have den med
  // (`takesUrl: true` i `ONE_OFF_CHECK.next`), så der står intet om et
  // produkt i denne fil. Adressen er den vi *fandt ved at svare* — altså den
  // endelige adresse efter redirects — fordi det er den læseren vil se igen.
  // `#` i en eksisterende href ville slå fragmentet sammen, så da bruges der
  // intet; en adresse der ikke er http(s) sendes aldrig videre.
  function medUrl(item, data) {
    if (!item.takesUrl) return item.href;
    var u = String((data && (data.finalUrl || data.inspectUrl)) || '');
    if (/#/.test(item.href) || !/^https?:\/\//i.test(u)) return item.href;
    return item.href + '#url=' + encodeURIComponent(u);
  }

  function render(data) {
    out.textContent = '';
    var code = Number(data.finalStatus) || 0;
    var ok = code >= 200 && code < 300;

    var card = el('div', 'oc-card');
    var head = el('p', 'oc-verdict ' + (ok ? 'is-ok' : 'is-warn'));
    // `createElement('strong')` stavet ud, så `check_built_css.py` kan se at
    // siden faktisk har et `strong` — porten læser kun bogstavelige
    // `createElement('…')`-kald, ikke et navn der kommer som argument til `el`.
    var lead = document.createElement('strong');
    lead.textContent = verdict(data);
    head.appendChild(lead);
    head.appendChild(el('span', 'oc-verdict-url', data.finalUrl || data.inspectUrl || ''));
    card.appendChild(head);

    var dl = el('dl', 'oc-rows');
    row(dl, T.finalUrl, data.finalUrl || '—');

    var ssl = data.ssl || {};
    var certText;
    if (!ssl.available) {
      certText = sslReason(ssl.reason);
    } else if (typeof ssl.daysRemaining === 'number' && ssl.daysRemaining < 0) {
      certText = T.expiredDays + ' ' + Math.abs(ssl.daysRemaining) + ' ' + T.daysAgo;
    } else if (typeof ssl.daysRemaining === 'number') {
      certText = ssl.daysRemaining + ' ' + T.daysLeft;
    } else {
      certText = ssl.validTo ? T.expires + ' ' + certDate(ssl.validTo) : T.expires + ' —';
    }
    row(dl, T.cert, certText);
    if (ssl.available) {
      if (ssl.validTo) row(dl, T.expires, certDate(ssl.validTo));
      if (ssl.issuer) row(dl, T.issuer, ssl.issuer);
      if (ssl.tlsVersion) row(dl, T.protocol, String(ssl.tlsVersion).replace(/_/g, '.'));
      if (ssl.chainTrusted !== undefined) {
        row(dl, T.chain, ssl.chainTrusted ? T.chainOk : T.chainBad);
      }
    }

    var checked = Array.isArray(data.securityHeadersChecked) && data.securityHeadersChecked.length
      ? data.securityHeadersChecked : FALLBACK_HEADERS;
    var found = data.securityHeaders || {};
    var chips = el('ul', 'oc-chips');
    var presentCount = 0;
    checked.forEach(function (h) {
      var has = Object.prototype.hasOwnProperty.call(found, h);
      if (has) presentCount++;
      var li = el('li', 'oc-chip ' + (has ? 'is-ok' : 'is-missing'));
      li.appendChild(el('span', 'oc-chip-name', h));
      li.appendChild(el('span', 'oc-chip-state', has ? T.present : T.missing));
      chips.appendChild(li);
    });
    var headersCell = el('span');
    headersCell.appendChild(chips);
    if (!presentCount) headersCell.appendChild(el('span', 'oc-note', T.none));
    row(dl, T.headers, headersCell);

    card.appendChild(dl);

    // The page declares its own closing sentence and its own way onward, because
    // what this check cannot do is a property of the site, not of the check:
    // DeskUptime's next step is the CLI, mahope.tools' is the deeper scanner.
    // A page that declares neither still gets the verdict, cert and chips.
    var cfg = window.ONE_OFF_CHECK || {};
    if (typeof cfg.then === 'string' && cfg.then) {
      card.appendChild(el('p', 'oc-next', cfg.then));
    }
    var links = Array.isArray(cfg.next) ? cfg.next : [];
    if (links.length) {
      var row2 = el('p', 'oc-next-links');
      links.forEach(function (item) {
        // Only a label and a same-document link are used. A page is our own
        // markup, so this is not an injection path, but the label is still set
        // as text and the href is still read from the page, never from the
        // answer — a URL we fetched must never be able to become a link here.
        if (!item || typeof item.href !== 'string' || !item.href) return;
        var a = el('a', 'btn-secondary', item.label || item.href);
        a.href = medUrl(item, data);
        a.rel = 'noopener';
        row2.appendChild(a);
      });
      if (row2.childNodes.length) card.appendChild(row2);
    }

    // A page can declare a Pro note that appears in the check result,
    // showing what DeskUptime Pro adds (continuous monitoring, webhooks,
    // client-ready reports, unlimited sites). The note is placed after the
    // verdict card and before any "next step" links.
    if (window.ONE_OFF_CHECK_PRO) {
      var proNote = el('div', 'oc-pro-note');
      proNote.innerHTML = String(window.ONE_OFF_CHECK_PRO);
      card.appendChild(proNote);
    }

    // The donation line is declared by the page itself (see `OC_DONATE` in the
    // HTML) because `tools/check_donation_paths.py` judges the page file: the
    // href must be the one in the catalog, it must sit in a `<script>` so it
    // cannot show before there is a result, and it must never be a button. The
    // markup is ours, not the visitor's, so appending it is not an injection
    // path — same shape as `/scan` and `/url-inspector`.
    if (window.OC_DONATE) {
      var holder = document.createElement('div');
      holder.innerHTML = window.OC_DONATE;
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

  // A visitor types `example.com` far more often than `https://example.com`, and
  // the worker answers "Invalid URL" to the first one. Add the scheme here
  // rather than sending a request we already know will be refused.
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
    input.value = url;
    out.hidden = true;
    out.textContent = '';
    btn.disabled = true;
    status.textContent = T.checking + ' ' + url + ' …';
    NET.askGet('/api/url-inspect?url=' + encodeURIComponent(url), MAX_TRIES, function () {
      status.textContent = T.retry;
    }).then(function (data) {
      // The worker answers 200 with an `error` on a target it will not inspect,
      // so a body that names its own error is still an error.
      if (data && data.error) { fail(data.error); return; }
      render(data);
      status.textContent = '';
    }, function (err) {
      // `net.js` already decided what is final. A 429 is final and its message
      // is the server's own sentence; a 5xx or a dropped connection is ours to
      // retry and was retried MAX_TRIES times before we say anything.
      fail(err.transport ? T.offline : (err.transient ? T.busy : (err.message || T.failed)));
      status.textContent = '';
    }).then(function () { btn.disabled = false; });
  });
})();