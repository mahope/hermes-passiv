/* palette-share-core.js — the share link for the palette generator.
 *
 * What it is for: a designer builds a palette from one base color and a page
 * background, and wants a colleague to open *that* palette, not a screenshot of
 * it. The generator runs entirely in the browser and has no server call, so the
 * state died with the tab. A palette is the one thing on the page worth
 * forwarding, so it now has an address.
 *
 * Format: `#c=<hex>;b=<hex>`, e.g. `#c=2563eb;b=111827`. The base color is the
 * bare value after `c=`; the background is a normal key=value pair, because the
 * background is optional (the default white is the common case). Colours are
 * `#rrggbb` without the `#` so the separator never has to be escaped, and a link
 * a human can edit by hand is worth the two extra bytes.
 *
 * Both language versions of the page read and write it from here, so the two
 * copies cannot drift the way the inline /net.js copies did (see net.js for
 * that story). `tests/palette-share.test.mjs` judges both the codec and the fact
 * that each page really calls it — a page that kept its own inline copy would go
 * red there.
 *
 * Two rules the decoder keeps, because the fragment is attacker-written:
 *   1. Nothing here throws. `location.hash` is whatever a reader or a bookmark
 *      says, and a hand-typed `#c=%` or a truncated link must leave the default
 *      palette on screen, not an empty page. (Same URIError the `#url=` readers
 *      hit — see c2891ac.)
 *   2. Every field is validated, not trusted. Colours must be 3 or 6 hex
 *      digits; anything else decodes to null and the page keeps its default.
 */
(function (global) {
  'use strict';

  var HEX3 = /^[0-9a-f]{3}$/;
  var HEX6 = /^[0-9a-f]{6}$/;

  // `#rgb` and `#rrggbb`, with or without the leading `#`, lowercased. Returns
  // null for anything else, so the caller decides what to do — never a guess.
  function normalizeColor(raw) {
    if (typeof raw !== 'string') return null;
    var v = raw.trim().replace(/^#/, '').toLowerCase();
    if (!HEX3.test(v) && !HEX6.test(v)) return null;
    if (HEX3.test(v)) v = v[0] + v[0] + v[1] + v[1] + v[2] + v[2];
    return '#' + v;
  }

  // Only the fields we know, in the order we write them. Unknown keys are
  // dropped, so a link from a future version degrades to the part it shares.
  function decode(hash) {
    var out = { base: null, bg: null };
    var s = typeof hash === 'string' ? hash : '';
    if (s.charAt(0) === '#') s = s.slice(1);
    // A `%` that is not a valid escape must not kill the page.
    try { s = decodeURIComponent(s); } catch (e) { return out; }
    if (s.indexOf('c=') !== 0) return out;

    // `c=` holds a bare value, not a key=value pair, so it is read first and
    // the rest of the fragment is parsed as pairs after it.
    var rest = s.slice(2);
    var semi = rest.indexOf(';');
    var baseRaw = semi === -1 ? rest : rest.slice(0, semi);
    var pairs = semi === -1 ? '' : rest.slice(semi + 1);
    out.base = normalizeColor(baseRaw);

    var seen = { c: true };
    pairs.split(';').forEach(function (part) {
      if (!part) return;
      var eq = part.indexOf('=');
      if (eq < 1) return;
      var key = part.slice(0, eq).trim();
      var val = part.slice(eq + 1).trim();
      if (Object.prototype.hasOwnProperty.call(seen, key)) return;  // first wins
      seen[key] = true;
      if (key === 'b') out.bg = val;
    });
    out.bg = normalizeColor(out.bg);
    return out;
  }

  function encode(state) {
    var base = normalizeColor(state && state.base);
    var parts = ['c=' + (base ? base.slice(1) : '')];
    var bg = normalizeColor(state && state.bg);
    if (bg) parts.push('b=' + bg.slice(1));
    return '#' + parts.join(';');
  }

  global.PALETTE_SHARE = global.PALETTE_SHARE || {};
  global.PALETTE_SHARE.decode = decode;
  global.PALETTE_SHARE.encode = encode;
  global.PALETTE_SHARE.normalizeColor = normalizeColor;
})(typeof window !== 'undefined' ? window : globalThis);
