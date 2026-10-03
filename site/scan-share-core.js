/* scan-share-core.js — the share link for the EAA/WCAG screen reader (/scan).
 *
 * What it is for: a bureau scans a client's page, gets twelve findings, and wants
 * the client to see *that exact audit*. Before this the page offered «Copy
 * shareable link», and the link it copied was only the URL — so the client
 * opened it, got an empty form, and had to press Scan themselves. That is the
 * one thing the recipient cannot do: they are not the one with the finding, and
 * re-running the scan spends the *recipient's* rate limit rather than the
 * sender's, on a page that may well have changed since.
 *
 * Format: `#u=<encoded url>;s=<0-100>;p=<platform>;f=<ID>:<sev>:<count>,…`
 * e.g. `#u=https%3A%2F%2Fexample.com;s=74;p=WordPress;f=IMG_ALT:e:4,CONTRAST:e:1`
 * The severity letter and the count are all that travel per finding: the prose
 * and the fix are looked up in the page's own `FIX` table, so a hand-edited link
 * can change a number but can never put its own words on mahope.tools.
 *
 * Both language versions of the page read and write it from here, so the two
 * copies cannot drift the way the inline /net.js copies did (see net.js for that
 * story), and a Danish page that kept its own copy goes red in
 * `tests/scan-share.test.mjs` — a codec-only test would still pass.
 *
 * Four rules the decoder keeps, because the fragment is attacker-written:
 *   1. Nothing here throws. `location.hash` is whatever a reader, a bookmark or
 *      a truncated message says; `#u=%` must leave the form alone, not empty the
 *      page. (Same URIError the `#url=` readers hit — see c2891ac.)
 *   2. The fragment is split on `;` *before* anything is percent-decoded, and
 *      only the `u` value is decoded. `encodeURIComponent` does escape `;`, so
 *      decoding the whole string first would put a `;` back inside a URL and cut
 *      the address in half.
 *   3. Only the known fields, each validated: a finding id is `[A-Z][A-Z0-9_]*`
 *      up to 24 characters, severity is one of two letters, a count is 1–9999,
 *      the score is 0–100, at most 16 findings. Unknown keys are dropped, so a
 *      link from a future version degrades to the part it shares.
 *   4. It never invents a result. A fragment with no readable `f=` is not an
 *      audit with zero findings — the page can honestly say "no issues found",
 *      but only about a scan it actually ran — so `f=` is required and an
 *      unreadable one yields null instead of a clean-looking scorecard.
 */
(function (global) {
  'use strict';

  var MAX_FINDINGS = 16;   // the page emits at most 12; the cap is for hand-written links
  var MAX_COUNT = 9999;
  var ID_RE = /^[A-Z][A-Z0-9_]{0,23}$/;
  var SEV = { e: 'error', w: 'warning' };
  var SEV_BACK = { error: 'e', warning: 'w' };

  function clampInt(raw, lo, hi) {
    if (typeof raw !== 'string' && typeof raw !== 'number') return null;
    var s = String(raw).trim();
    if (!/^\d{1,6}$/.test(s)) return null;
    var n = parseInt(s, 10);
    if (isNaN(n)) return null;
    return Math.max(lo, Math.min(hi, n));
  }

  // Et antal *fund* er 1–9999. Nul er ikke et fund, det er en mangel på et, så
  // det afvises i stedet for at blive klippet op til 1 — ellers ville et
  // håndredigeret `f=IMG_ALT:e:0` vise «1 image(s) missing alt text».
  function countOf(raw) {
    if (typeof raw !== 'string' && typeof raw !== 'number') return null;
    var s = String(raw).trim();
    if (!/^\d{1,4}$/.test(s)) return null;
    var n = parseInt(s, 10);
    return (isNaN(n) || n < 1) ? null : n;
  }

  // The scanned address. `http(s)` only, and it is the one field that reaches
  // the page as text, so it comes back as data and the caller escapes it — the
  // decoder does not decide what is safe to render. Control characters are
  // refused: a newline in an address-bar value is a header-splitting payload the
  // moment anyone copies it back out into a request.
  function normalizeUrl(raw) {
    if (typeof raw !== 'string') return null;
    var v = raw.trim();
    if (!v || v.length > 2048) return null;
    try { v = decodeURIComponent(v); } catch (e) { return null; }
    v = v.trim();
    if (!v || v.length > 2048) return null;
    if (/[\u0000-\u001f\u007f]/.test(v)) return null;
    if (!/^https?:\/\//i.test(v)) return null;
    return v;
  }

  // The platform is only a *key* into the page's own guide table. Anything that
  // is not a plain word is dropped, and the page additionally requires the key
  // to exist in its table before it renders a link.
  function normalizePlatform(raw) {
    if (typeof raw !== 'string') return null;
    var v = raw.trim();
    if (!v || v.length > 32 || !/^[A-Za-z][A-Za-z0-9+._-]*$/.test(v)) return null;
    return v;
  }

  function parseFindings(raw) {
    if (typeof raw !== 'string' || !raw) return null;
    var list = raw.split(',');
    if (list.length > MAX_FINDINGS) return null;
    var out = [];
    for (var i = 0; i < list.length; i++) {
      var parts = list[i].split(':');
      if (parts.length !== 3) return null;
      var id = parts[0];
      var sev = SEV[parts[1].toLowerCase()];
      var n = countOf(parts[2]);
      if (!ID_RE.test(id) || !sev || n === null) return null;
      out.push({ id: id, sev: sev, count: n });
    }
    return out.length ? out : null;
  }

  function decode(hash) {
    var s = typeof hash === 'string' ? hash : '';
    if (s.charAt(0) === '#') s = s.slice(1);
    if (s.indexOf('u=') !== 0) return null;

    var parts = s.split(';');
    var kv = { u: parts.shift().slice(2) };
    parts.forEach(function (part) {
      if (!part) return;
      var eq = part.indexOf('=');
      if (eq < 1) return;
      var key = part.slice(0, eq).trim();
      if (Object.prototype.hasOwnProperty.call(kv, key)) return;  // first wins
      kv[key] = part.slice(eq + 1);
    });

    var url = normalizeUrl(kv.u);
    if (!url) return null;
    var findings = parseFindings(kv.f);
    if (!findings) return null;
    var score = clampInt(kv.s, 0, 100);
    if (score === null) return null;

    return {
      url: url,
      score: score,
      findings: findings,
      // The two counts are recomputed from the findings themselves, not read from
      // the link, so the scorecard's numbers cannot contradict its own list.
      errors: findings.filter(function (f) { return f.sev === 'error'; }).length,
      warnings: findings.filter(function (f) { return f.sev === 'warning'; }).length,
      platform: normalizePlatform(kv.p)
    };
  }

  function encode(state) {
    if (!state) return '';
    var url = normalizeUrl(state.url);
    var findings = Array.isArray(state.findings) ? state.findings : [];
    var score = clampInt(state && state.score, 0, 100);
    if (!url || !findings.length || score === null) return '';

    var list = [];
    for (var i = 0; i < findings.length && i < MAX_FINDINGS; i++) {
      var f = findings[i] || {};
      var id = typeof f.id === 'string' ? f.id.trim().toUpperCase() : '';
      var sev = SEV_BACK[f.sev] || SEV_BACK[String(f.sev || '').toLowerCase()];
      var n = countOf(f.count);
      if (!ID_RE.test(id) || !sev || n === null) continue;
      list.push(id + ':' + sev + ':' + n);
    }
    if (!list.length) return '';

    var parts = ['u=' + encodeURIComponent(url), 's=' + score, 'f=' + list.join(',')];
    var p = normalizePlatform(state.platform);
    if (p) parts.push('p=' + p);
    return '#' + parts.join(';');
  }

  global.SCANSHARE = global.SCANSHARE || {};
  global.SCANSHARE.decode = decode;
  global.SCANSHARE.encode = encode;
  global.SCANSHARE.MAX_FINDINGS = MAX_FINDINGS;
})(typeof window !== 'undefined' ? window : globalThis);
