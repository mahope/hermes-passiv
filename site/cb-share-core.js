/* cb-share-core.js — the share link for the color-blindness simulator.
 *
 * What it is for: a designer picks four colors, drags severity to 60 % and wants
 * a colleague to see *that exact* simulation, not a description of it. The tool
 * runs entirely in the browser and has no server call, so there was nothing to
 * send — the state simply died with the tab. A simulation is the one thing on
 * this page that is worth forwarding, so it now has an address.
 *
 * Format: `#pal=<hex>,<hex>,…;s=<0-100>;f=<hex>;b=<hex>`, e.g.
 * `#pal=2563eb,e91e63;f=111827;b=ffffff;s=60`. Colours are `#rrggbb` without the
 * `#`, because the separator would otherwise have to be escaped, and a link a
 * human can edit by hand is worth the two extra bytes.
 *
 * Both language versions of the page read and write it from here, so the two
 * copies cannot drift the way the inline /net.js copies did (see net.js for
 * that story). `tests/cb-share.test.mjs` judges both the codec and the fact that
 * each page really calls it — a page that kept its own inline copy would go red
 * there.
 *
 * Two rules the decoder keeps, because the fragment is attacker-written:
 *   1. Nothing here throws. `location.hash` is whatever a reader or a bookmark
 *      says, and a hand-typed `#pal=%` or a truncated link must leave the
 *      default palette on screen, not an empty page. (Same URIError the
 *      `#url=` readers hit — see c2891ac.)
 *   2. Every field is validated, not trusted. Colours must be 3 or 6 hex
 *      digits, at most 10 of them (the page's own limit), and severity is
 *      clamped into 0–100. The decoder cannot know which colours the restored
 *      palette ends up holding, so `f`/`b` are only as good as the page: both
 *      versions apply them only when they are in that palette, otherwise the
 *      preview would show a text colour the grid does not contain.
 */
(function (global) {
  'use strict';

  var MAX_COLORS = 10;   // the page refuses an eleventh color
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
    var out = { colors: null, severity: null, fg: null, bg: null };
    var s = typeof hash === 'string' ? hash : '';
    if (s.charAt(0) === '#') s = s.slice(1);
    // A `%` that is not a valid escape must not kill the page.
    try { s = decodeURIComponent(s); } catch (e) { return out; }
    if (s.indexOf('pal=') !== 0) return out;

    // `pal=` holds a bare list, not a key=value pair, so it is read first and
    // the rest of the fragment is parsed as pairs after it.
    var rest = s.slice(4);
    var semi = rest.indexOf(';');
    var palRaw = semi === -1 ? rest : rest.slice(0, semi);
    var pairs = semi === -1 ? '' : rest.slice(semi + 1);
    out.colors = palRaw ? palRaw.split(',').map(normalizeColor) : null;

    var seen = { pal: true };
    pairs.split(';').forEach(function (part) {
      if (!part) return;
      var eq = part.indexOf('=');
      if (eq < 1) return;
      var key = part.slice(0, eq).trim();
      var val = part.slice(eq + 1).trim();
      if (Object.prototype.hasOwnProperty.call(seen, key)) return;  // first wins
      seen[key] = true;
      if (key === 's') out.sev_raw = val;
      else if (key === 'f') out.fg = val;
      else if (key === 'b') out.bg = val;
    });

    // One bad colour drops the whole palette: a grid that is half the sender's
    // and half ours is a lie about what they simulated.
    if (out.colors) {
      var list = out.colors;
      if (!list.length || list.length > MAX_COLORS || list.indexOf(null) !== -1) out.colors = null;
    }
    if (out.sev_raw !== undefined) {
      var n = parseInt(out.sev_raw, 10);
      out.severity = isNaN(n) ? null : Math.max(0, Math.min(100, n));
      delete out.sev_raw;
    }
    out.fg = normalizeColor(out.fg);
    out.bg = normalizeColor(out.bg);
    return out;
  }

  function encode(state) {
    var colors = (state && state.colors) || [];
    var parts = ['pal=' + colors.map(function (c) {
      var n = normalizeColor(c && c.hex !== undefined ? c.hex : c);
      return n ? n.slice(1) : '';
    }).filter(Boolean).join(',')];
    var sev = state ? parseInt(state.severity, 10) : NaN;
    if (!isNaN(sev)) parts.push('s=' + Math.max(0, Math.min(100, sev)));
    var fg = normalizeColor(state && state.fg);
    if (fg) parts.push('f=' + fg.slice(1));
    var bg = normalizeColor(state && state.bg);
    if (bg) parts.push('b=' + bg.slice(1));
    return '#' + parts.join(';');
  }

  global.CBSHARE = global.CBSHARE || {};
  global.CBSHARE.decode = decode;
  global.CBSHARE.encode = encode;
  global.CBSHARE.normalizeColor = normalizeColor;
  global.CBSHARE.MAX_COLORS = MAX_COLORS;
})(typeof window !== 'undefined' ? window : globalThis);