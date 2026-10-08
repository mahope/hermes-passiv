/* text-on-image-share.js — share link for the text-on-image checker.
 *
 * What it is for: a designer tunes text color, scrim, position and gradient
 * on an image, and wants a colleague to open *that exact check* without
 * re-doing every step. The tool runs entirely in the browser and has no
 * server call, so the state dies with the tab. A share link makes it persistent.
 *
 * Format: `#ti=...` with these fields:
 *   bg=image|gradient     background mode
 *   g1=<hex>              gradient start color (6 hex, no #)
 *   g2=<hex>              gradient end color (6 hex, no #)
 *   ga=<deg>              gradient angle 0-360
 *   t1=<text>             text 1 content (URL-encoded)
 *   c1=<hex>              text 1 color (6 hex, no #)
 *   fs1=small|large       text 1 font size
 *   x1=<num>              text 1 x position
 *   y1=<num>              text 1 y position
 *   s1=<hex>,<pct>        text 1 scrim (color + alpha 0-100), optional
 *   t2=<text>             text 2 content (URL-encoded), optional
 *   c2=<hex>              text 2 color, optional
 *   fs2=small|large       text 2 font size, optional
 *   x2=<num>              text 2 x position, optional
 *   y2=<num>              text 2 y position, optional
 *   s2=<hex>,<pct>        text 2 scrim, optional
 *   a=0|1                 active block (0 or 1)
 *
 * Example: #ti=bg=gradient;g1=1e3a5f;g2=c9d8e4;ga=45;t1=Hello;c1=ffffff;fs1=large;x1=54;y1=218;s1=000000,42;a=0
 *
 * Images cannot be shared via URL (too large, local file). When bg=image,
 * the recipient must upload their own image — the rest of the settings apply.
 *
 * Two rules the decoder keeps, because the fragment is attacker-written:
 *   1. Nothing here throws. A malformed fragment leaves defaults on screen.
 *   2. Every field is validated, not trusted. Unknown keys are ignored.
 */
(function (global) {
  'use strict';

  var HEX3 = /^[0-9a-f]{3}$/;
  var HEX6 = /^[0-9a-f]{6}$/;
  var DEG = /^\d+$/;

  function normalizeColor(raw) {
    if (typeof raw !== 'string') return null;
    var v = raw.trim().replace(/^#/, '').toLowerCase();
    if (!HEX3.test(v) && !HEX6.test(v)) return null;
    if (HEX3.test(v)) v = v[0] + v[0] + v[1] + v[1] + v[2] + v[2];
    return '#' + v;
  }

  function clamp(n, min, max) {
    return Math.max(min, Math.min(max, n));
  }

  function decode(hash) {
    var out = {
      bg: 'gradient',
      g1: '#1e3a5f',
      g2: '#c9d8e4',
      ga: 45,
      t1: 'Your headline here',
      c1: '#ffffff',
      fs1: 'large',
      x1: null,
      y1: null,
      s1: null,
      t2: 'Your subtitle here',
      c2: '#ffffff',
      fs2: 'large',
      x2: null,
      y2: null,
      s2: null,
      a: 0
    };

    var s = typeof hash === 'string' ? hash : '';
    if (s.charAt(0) === '#') s = s.slice(1);
    try { s = decodeURIComponent(s); } catch (e) { return out; }
    if (s.indexOf('ti=') !== 0) return out;

    var parts = s.slice(3).split(';');
    var seen = {};

    parts.forEach(function (part) {
      if (!part) return;
      var eq = part.indexOf('=');
      if (eq < 1) return;
      var key = part.slice(0, eq).trim();
      var val = part.slice(eq + 1).trim();
      if (Object.prototype.hasOwnProperty.call(seen, key)) return;
      seen[key] = true;

      switch (key) {
        case 'bg':
          if (val === 'image' || val === 'gradient') out.bg = val;
          break;
        case 'g1':
          var n1 = normalizeColor(val);
          if (n1) out.g1 = n1;
          break;
        case 'g2':
          var n2 = normalizeColor(val);
          if (n2) out.g2 = n2;
          break;
        case 'ga':
          if (DEG.test(val)) {
            var deg = parseInt(val, 10);
            if (deg >= 0 && deg <= 360) out.ga = deg;
          }
          break;
        case 't1':
          out.t1 = val || out.t1;
          break;
        case 'c1':
          var nc1 = normalizeColor(val);
          if (nc1) out.c1 = nc1;
          break;
        case 'fs1':
          if (val === 'small' || val === 'large') out.fs1 = val;
          break;
        case 'x1':
          var x1 = parseInt(val, 10);
          if (!isNaN(x1) && x1 >= 0) out.x1 = x1;
          break;
        case 'y1':
          var y1 = parseInt(val, 10);
          if (!isNaN(y1) && y1 >= 0) out.y1 = y1;
          break;
        case 's1':
          var sp1 = val.split(',');
          if (sp1.length === 2) {
            var sc1 = normalizeColor(sp1[0]);
            var a1 = parseInt(sp1[1], 10);
            if (sc1 && !isNaN(a1)) {
              a1 = Math.max(0, Math.min(100, a1)); // clamp 0-100
              out.s1 = { hex: sc1, alpha: a1 / 100 };
            }
          }
          break;
        case 't2':
          out.t2 = val || out.t2;
          break;
        case 'c2':
          var nc2 = normalizeColor(val);
          if (nc2) out.c2 = nc2;
          break;
        case 'fs2':
          if (val === 'small' || val === 'large') out.fs2 = val;
          break;
        case 'x2':
          var x2 = parseInt(val, 10);
          if (!isNaN(x2) && x2 >= 0) out.x2 = x2;
          break;
        case 'y2':
          var y2 = parseInt(val, 10);
          if (!isNaN(y2) && y2 >= 0) out.y2 = y2;
          break;
        case 's2':
          var sp2 = val.split(',');
          if (sp2.length === 2) {
            var sc2 = normalizeColor(sp2[0]);
            var a2 = parseInt(sp2[1], 10);
            if (sc2 && !isNaN(a2)) {
              a2 = Math.max(0, Math.min(100, a2)); // clamp 0-100
              out.s2 = { hex: sc2, alpha: a2 / 100 };
            }
          }
          break;
        case 'a':
          if (val === '0' || val === '1') out.a = parseInt(val, 10);
          break;
      }
    });

    return out;
  }

  function encode(state) {
    if (!state) return '#ti=';
    var parts = ['ti=bg=' + (state.bg || 'gradient')];

    if (state.bg === 'gradient') {
      var g1 = state.g1 ? state.g1.replace(/^#/, '').toLowerCase() : '1e3a5f';
      var g2 = state.g2 ? state.g2.replace(/^#/, '').toLowerCase() : 'c9d8e4';
      if (HEX6.test(g1)) parts.push('g1=' + g1);
      if (HEX6.test(g2)) parts.push('g2=' + g2);
      if (typeof state.ga === 'number' && state.ga >= 0 && state.ga <= 360) parts.push('ga=' + state.ga);
    }

    if (state.t1) parts.push('t1=' + encodeURIComponent(state.t1));
    var c1 = state.c1 ? state.c1.replace(/^#/, '').toLowerCase() : 'ffffff';
    if (HEX6.test(c1)) parts.push('c1=' + c1);
    if (state.fs1 === 'small' || state.fs1 === 'large') parts.push('fs1=' + state.fs1);
    if (typeof state.x1 === 'number' && state.x1 >= 0) parts.push('x1=' + state.x1);
    if (typeof state.y1 === 'number' && state.y1 >= 0) parts.push('y1=' + state.y1);
    if (state.s1 && state.s1.hex) {
      var s1c = state.s1.hex.replace(/^#/, '').toLowerCase();
      var s1a = Math.round(clamp(state.s1.alpha * 100, 0, 100));
      if (HEX6.test(s1c)) parts.push('s1=' + s1c + ',' + s1a);
    }

    if (state.t2 && state.t2 !== 'Your subtitle here') parts.push('t2=' + encodeURIComponent(state.t2));
    var c2 = state.c2 ? state.c2.replace(/^#/, '').toLowerCase() : 'ffffff';
    if (HEX6.test(c2)) parts.push('c2=' + c2);
    if (state.fs2 === 'small' || state.fs2 === 'large') parts.push('fs2=' + state.fs2);
    if (typeof state.x2 === 'number' && state.x2 >= 0) parts.push('x2=' + state.x2);
    if (typeof state.y2 === 'number' && state.y2 >= 0) parts.push('y2=' + state.y2);
    if (state.s2 && state.s2.hex) {
      var s2c = state.s2.hex.replace(/^#/, '').toLowerCase();
      var s2a = Math.round(clamp(state.s2.alpha * 100, 0, 100));
      if (HEX6.test(s2c)) parts.push('s2=' + s2c + ',' + s2a);
    }

    if (state.a === 0 || state.a === 1) parts.push('a=' + state.a);

    return '#' + parts.join(';');
  }

  global.TEXT_ON_IMAGE_SHARE = global.TEXT_ON_IMAGE_SHARE || {};
  global.TEXT_ON_IMAGE_SHARE.decode = decode;
  global.TEXT_ON_IMAGE_SHARE.encode = encode;
  global.TEXT_ON_IMAGE_SHARE.normalizeColor = normalizeColor;
})(typeof window !== 'undefined' ? window : globalThis);