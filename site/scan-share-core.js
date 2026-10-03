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
 * Format: `#u=<encoded url>;p=<platform>;f=<ID>:<sev>:<count>,…`
 * e.g. `#u=https%3A%2F%2Fexample.com;p=WordPress;f=IMG_ALT:e:4,CONTRAST:e:1`
 * The severity letter and the count are all that travel per finding: the prose
 * and the fix are looked up in the page's own `FIX` table, so a hand-edited link
 * can change a number but can never put its own words on mahope.tools.
 *
 * The score does *not* travel in the link, and that is the whole point of it.
 * It used to: `#u=…;s=100;f=IMG_ALT:e:1` painted «100/100 — Grade A» directly
 * above a list with an error in it, because `decode()` took `s=` at face value
 * while the two counts next to it were recomputed from the findings. So the
 * scorecard could contradict its own list, and the only thing that could change
 * it was the sender's typing. The score is fully derivable from `f=` — nothing
 * else travels — so it is derived here, by the same `scoreOf()` the two pages
 * call for a fresh scan. Old links with `s=` still open: the key is unknown
 * now, so it is dropped like any other, and the score comes out honest.
 *
 * Both language versions of the page read and write it from here, so the two
 * copies cannot drift the way the inline /net.js copies did (see net.js for that
 * story), and a Danish page that kept its own copy goes red in
 * `tests/scan-share.test.mjs` — a codec-only test would still pass.
 *
 * Det her er ikke kun et codec mere. Under det ligger de tre ting en læser med
 * en fund-liste spørger om, og som siden før dette ikke kunne svare på:
 * `startHere()` (hvilke tre der betyder mest), `diffFindings()` (hvad er ændret
 * siden sidste scanning) og `remember()`/`recall()` (sidste ti sider, kun i
 * læserens egen browser). Alle tre er rene funktioner over fund-lister — ingen
 * af dem kender en pris, en knap eller en markup, så de kan dømmes uden en
 * browser, og en side der glemmer at kalde dem, kan ikke se en fordel.
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
 *      at most 16 findings. Unknown keys are dropped, so a link from a future
 *      version degrades to the part it shares.
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

  // The page's own scoring formula, in one place, because it has three callers:
  // `/scan` and `/scan-da` both print the number for a fresh scan, and this file
  // prints the number for a shared one. Three copies of a scoring formula is how
  // a scorecard ends up saying «100/100 — Grade A» above a list of findings —
  // before this, each copy was free to disagree with the other two.
  var WEIGHT = { error: 12, warning: 5, notice: 2 };

  function scoreOf(findings) {
    if (!Array.isArray(findings)) return 0;
    var score = 100;
    for (var i = 0; i < findings.length; i++) {
      var sev = String((findings[i] || {}).sev || '').toLowerCase();
      score -= WEIGHT[sev] || 0;
    }
    return Math.max(0, Math.min(100, score));
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

    // The score is computed, never read. `s=` is not a field any more: a
    // hand-edited link can no longer claim «Grade A» above findings it did not
    // earn, and an old link that still carries one is not rejected for it.
    return {
      url: url,
      score: scoreOf(findings),
      findings: findings,
      // The counts come out of the findings too, for the same reason: the two
      // numbers on the card, the score above them and the list under them are
      // now all one calculation, so they cannot contradict each other.
      errors: findings.filter(function (f) { return f.sev === 'error'; }).length,
      warnings: findings.filter(function (f) { return f.sev === 'warning'; }).length,
      platform: normalizePlatform(kv.p)
    };
  }

  function encode(state) {
    if (!state) return '';
    var url = normalizeUrl(state.url);
    var findings = Array.isArray(state.findings) ? state.findings : [];
    if (!url || !findings.length) return '';

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

    var parts = ['u=' + encodeURIComponent(url), 'f=' + list.join(',')];
    var p = normalizePlatform(state.platform);
    if (p) parts.push('p=' + p);
    return '#' + parts.join(';');
  }

  // ---------------------------------------------------------------- rankering
  // Fundene kommer ud af `scan()` i den rækkefølge reglerne kører i, så en side
  // med fire billeder uden alt-tekst og én knap uden navn viser ALT-kravet
  // først og den ene knap sidst — omvendt af hvad der bliver rettet hurtigst.
  // Rækkefølgen er derfor eksplisit og målbar: alvor før advarsel, og inden for
  // samme alvor det fund der optræder oftest. Tallet på fundet *er* alvorgraden
  // her — fire billeder uden alt er fire brud, ikke ét — så det bruges ikke
  // til at slå en alvorlig regel med én forekomst.
  var SEV_RANK = { error: 0, warning: 1, notice: 2 };

  function rankFindings(findings) {
    if (!Array.isArray(findings)) return [];
    return findings.map(function (f, i) {
      return { f: f || {}, i: i };
    }).sort(function (a, b) {
      var sa = SEV_RANK[a.f.sev], sb = SEV_RANK[b.f.sev];
      if (sa === undefined) sa = 3;
      if (sb === undefined) sb = 3;
      if (sa !== sb) return sa - sb;
      var ca = Number(a.f.count) || 0, cb = Number(b.f.count) || 0;
      if (ca !== cb) return cb - ca;
      // `sort` er stabil i moderne motorer, men det afhænger af inputrækkefølgen,
      // som er koderækkefølgen. indekset gør den rækkefølge til en *lov* i stedet
      // for en egenskab ved motoren.
      return a.i - b.i;
    }).map(function (w) { return w.f; });
  }

  // De tre der betyder mest. `n` er med, fordi «start her» er en påstand om
  // hvor mange linjer en læser orkeder — ikke en ny grænse på fundene.
  function startHere(findings, n) {
    var k = n === undefined ? 3 : n;
    return rankFindings(findings).slice(0, k < 0 ? 0 : k);
  }

  // ------------------------------------------------------------- hvad er ændret
  // Det eneste en læser med en fejl-liste faktisk vil vide efter at have rettet:
  // om der er blevet færre. Før dette stod der ingen vej til at svare på det —
  // scan igen gav et nyt tal og ingen forskel, og så måtte læseren selv holde
  // de to lister ved siden af hinanden og regne.
  function diffFindings(prev, cur) {
    if (!Array.isArray(prev) || !Array.isArray(cur)) return null;
    var before = {}, after = {};
    var i;
    for (i = 0; i < prev.length; i++) {
      if (prev[i] && typeof prev[i].id === 'string') before[prev[i].id] = Number(prev[i].count) || 0;
    }
    for (i = 0; i < cur.length; i++) {
      if (cur[i] && typeof cur[i].id === 'string') after[cur[i].id] = Number(cur[i].count) || 0;
    }
    var fixed = [], added = [], reduced = [], grew = [];
    Object.keys(after).forEach(function (id) {
      if (!(id in before)) { added.push(id); return; }
      if (after[id] < before[id]) reduced.push({ id: id, from: before[id], to: after[id] });
      else if (after[id] > before[id]) grew.push({ id: id, from: before[id], to: after[id] });
    });
    Object.keys(before).forEach(function (id) {
      if (!(id in after)) fixed.push(id);
    });
    return {
      fixed: fixed, added: added, reduced: reduced, grew: grew,
      scoreFrom: scoreOf(prev), scoreTo: scoreOf(cur)
    };
  }

  // ------------------------------------------------------------------- huskeværk
  // Ti seneste sider i *én* nøgle, så en læser der scanner mange sider ikke
  // efterlader et grænseløst spor i sin egen browser. Alt sammen klient-side:
  // intet af det forlader siden, og det er den eneste måde den her forskel kan
  // findes på uden en konto.
  var STORE_KEY = 'eaa:last';
  var STORE_MAX = 10;

  // Nøglen er scheme-strippet vært + sti, så `https://a.dk/x` og
  // `http://a.dk/x` er samme side, men `/` og `/da/` ikke er. Query og hash
  // droppes: de er ikke en anden side, og en URL med et sporings-id i sig
  // må ikke gøre to sider til to forskellige nøgler.
  function storeKey(url) {
    var v = normalizeUrl(url);
    if (!v) return null;
    // Regex, ikke `new URL()`: `normalizeUrl()` har allerede sikret `http(s)`,
    // så det eneste der er tilbage er at finde vært og sti — og kernen skal
    // kunne køres uden `URL` (den testes i en vm, og den skal ikke have en
    // afhængighed den ikke bruger til noget).
    var m = /^https?:\/\/([^/?#]+)([^?#]*)/i.exec(v);
    if (!m) return null;
    var p = m[2].replace(/\/+$/, '') || '/';
    return m[1].toLowerCase() + p;
  }

  function readStore() {
    try {
      var ls = global.localStorage;
      if (!ls) return {};
      var raw = ls.getItem(STORE_KEY);
      if (!raw) return {};
      var parsed = JSON.parse(raw);
      return (parsed && typeof parsed === 'object' && !Array.isArray(parsed)) ? parsed : {};
    } catch (e) { return {}; }   // privat browsertilstand, kvote, korrumperet JSON
  }

  function writeStore(store) {
    try {
      var ls = global.localStorage;
      if (ls) ls.setItem(STORE_KEY, JSON.stringify(store));
    } catch (e) { /* privat browsertilstand eller fuld kvota: følelsen er valgfri */ }
  }

  function recall(url) {
    var key = storeKey(url);
    if (!key) return null;
    var e = readStore()[key];
    if (!e || !Array.isArray(e.f)) return null;
    var findings = [];
    for (var i = 0; i < e.f.length && i < MAX_FINDINGS; i++) {
      var row = e.f[i];
      if (!Array.isArray(row) || row.length !== 3) continue;
      var n = countOf(row[2]);
      var sev = SEV[String(row[1] || '').toLowerCase()];
      if (typeof row[0] !== 'string' || !ID_RE.test(row[0]) || !sev || n === null) continue;
      findings.push({ id: row[0], sev: sev, count: n });
    }
    return findings.length ? { findings: findings, at: Number(e.t) || 0 } : null;
  }

  function remember(url, findings) {
    var key = storeKey(url);
    if (!key || !Array.isArray(findings) || !findings.length) return null;
    var store = readStore();
    var rows = [];
    for (var i = 0; i < findings.length && i < MAX_FINDINGS; i++) {
      var f = findings[i] || {};
      var sev = SEV_BACK[String(f.sev || '').toLowerCase()];
      var n = countOf(f.count);
      if (typeof f.id !== 'string' || !ID_RE.test(f.id) || !sev || n === null) continue;
      rows.push([f.id, sev, n]);
    }
    if (!rows.length) return null;
    store[key] = { t: Date.now(), f: rows };
    // Ti nyligste. `Object.keys` uden en eksplicit sortering ville være
    // afhængig af indsættelsesrækkefølgen, og det er ikke en orden.
    var keep = Object.keys(store).sort(function (a, b) {
      return ((store[b] || {}).t || 0) - ((store[a] || {}).t || 0);
    }).slice(0, STORE_MAX);
    var next = {};
    keep.forEach(function (k) { next[k] = store[k]; });
    writeStore(next);
    return rows.length;
  }

  global.SCANSHARE = global.SCANSHARE || {};
  global.SCANSHARE.decode = decode;
  global.SCANSHARE.encode = encode;
  global.SCANSHARE.scoreOf = scoreOf;
  global.SCANSHARE.rankFindings = rankFindings;
  global.SCANSHARE.startHere = startHere;
  global.SCANSHARE.diffFindings = diffFindings;
  global.SCANSHARE.storeKey = storeKey;
  global.SCANSHARE.recall = recall;
  global.SCANSHARE.remember = remember;
  global.SCANSHARE.MAX_FINDINGS = MAX_FINDINGS;
})(typeof window !== 'undefined' ? window : globalThis);
