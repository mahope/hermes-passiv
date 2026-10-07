/* palette-image.js — hent farverne ud af et billede til paletgeneratoren.
 *
 * Generatoren tager én hexfarve ind. Men den farve de fleste faktisk har, står
 * i deres logo eller i et skærmbillede — ikke i et tekstfelt. Uden denne vej
 * skulle en designer gætte sin brandfarve med pipetten i et andet program og
 * skrive den ind i hånden. Nu kan et billede trækkes ind, indsættes eller
 * vælges, og de dominerende farver kommer ud som klikbare prøver, der sætter
 * basisfarven.
 *
 * Billedet læses med canvas i browseren og uploades aldrig — samme løfte som
 * resten af siden. Der er ingen `fetch` her.
 *
 * `extract()` er ren og uden DOM, så `tests/palette-image.test.mjs` kan kalde
 * den på et kendt pixel-array og holde farverne op mod det den skal finde.
 *
 *   PALETTE_IMAGE.mount({ onPick: fn, strings: { … } })
 */
(function (global) {
  'use strict';

  var MAX = 8;
  // En pixel under denne alfa er baggrund, ikke billede — et gennemsigtigt
  // PNG skal ikke give en "farve" af de tre nul-kanaler.
  var ALPHA_MIN = 125;
  // Næsten-hvid er oftest arket eller siden, ikke en farve nogen valgte. Den
  // springes over, så en logo-på-hvid ikke giver otte prøver af hvid.
  var WHITE_MIN = 250;
  // Fire bits pr. kanal: 4096 bøtter. Nok til at skelne brandfarver, groft nok
  // til at en gradient samler sig i nogle få bøtter i stedet for tusind.
  var QUANT = 4;

  function clamp255(v) { return v < 0 ? 0 : v > 255 ? 255 : Math.round(v); }

  function toHex(rgb) {
    return '#' + rgb.map(function (c) {
      var h = clamp255(c).toString(16);
      return h.length === 1 ? '0' + h : h;
    }).join('');
  }

  // `data` er RGBA (Uint8ClampedArray eller almindeligt array). Returnerer op
  // til `max` farver, sorteret efter hvor stor en del af billedet de dækker,
  // med næsten-identiske nuancer slået sammen.
  function extract(data, opts) {
    var o = opts || {};
    var max = o.max || MAX;
    var alphaMin = o.minAlpha == null ? ALPHA_MIN : o.minAlpha;
    var whiteMin = o.whiteMin == null ? WHITE_MIN : o.whiteMin;
    var buckets = Object.create(null);
    var total = 0;
    for (var i = 0; i < data.length; i += 4) {
      if (data[i + 3] < alphaMin) continue;
      var r = data[i], g = data[i + 1], b = data[i + 2];
      if (r >= whiteMin && g >= whiteMin && b >= whiteMin) continue;
      var key = ((r >> QUANT) << 8) | ((g >> QUANT) << 4) | (b >> QUANT);
      var bk = buckets[key];
      if (!bk) { bk = buckets[key] = { r: 0, g: 0, b: 0, n: 0 }; }
      bk.r += r; bk.g += g; bk.b += b; bk.n++;
      total++;
    }
    if (!total) return [];
    var list = Object.keys(buckets).map(function (k) {
      var bk = buckets[k];
      return { r: bk.r / bk.n, g: bk.g / bk.n, b: bk.b / bk.n, count: bk.n };
    });
    list.sort(function (a, b) { return b.count - a.count; });
    var out = [];
    for (var j = 0; j < list.length && out.length < max; j++) {
      var c = list[j];
      var dup = out.some(function (p) {
        return Math.abs(p.r - c.r) + Math.abs(p.g - c.g) + Math.abs(p.b - c.b) < 36;
      });
      if (!dup) out.push(c);
    }
    return out.map(function (c) {
      return { hex: toHex([c.r, c.g, c.b]), r: c.r, g: c.g, b: c.b, count: c.count };
    });
  }

  function mount(opts) {
    var o = opts || {}, s = o.strings || {};
    var doc = global.document;
    var box = doc.getElementById(o.container || 'pg-img-swatches');
    var file = doc.getElementById(o.fileId || 'pg-img-file');
    var drop = doc.getElementById(o.dropId || 'pg-img');
    var errEl = doc.getElementById(o.errorId || 'pg-img-error');
    if (!box || !file) return null;

    function setErr(msg) { if (errEl) errEl.textContent = msg || ''; }

    function render(colors) {
      box.innerHTML = '';
      if (!colors.length) { setErr(s.none || 'No colours found in that image — try another.'); return; }
      setErr('');
      colors.forEach(function (c) {
        // Navnet er hele grunden til at prøven er der: en ikke-designer kan
        // pege på den og sige «den blå», ikke «#2563eb». Slås op i den ene
        // tabel i /color-names.js, som siden indlæser før denne fil.
        var name = (global.COLOR_NAMES && global.COLOR_NAMES.nearestName) ? global.COLOR_NAMES.nearestName(c.hex) : '';
        var item = doc.createElement('div');
        item.className = 'pg-img-item';
        var b = doc.createElement('button');
        b.type = 'button';
        b.className = 'pg-img-swatch';
        b.style.background = c.hex;
        b.title = name ? (c.hex + ' — ' + name) : c.hex;
        b.setAttribute('aria-label', (s.pick || 'Use') + ' ' + c.hex + (name ? ' (' + name + ')' : ''));
        b.addEventListener('click', function () {
          if (typeof o.onPick === 'function') o.onPick(c.hex);
          Array.prototype.forEach.call(box.querySelectorAll('.pg-img-swatch'), function (el) {
            el.setAttribute('aria-pressed', el === b ? 'true' : 'false');
          });
        });
        item.appendChild(b);
        if (name) {
          var cap = doc.createElement('span');
          cap.className = 'pg-img-name';
          cap.textContent = name;
          item.appendChild(cap);
        }
        box.appendChild(item);
      });
    }

    // Billedet skaleres ned før målingen: en 12 megapixel-fil giver samme
    // farvesvar som en 240 px-version, men pixel-løkken bliver tusind gange
    // kortere, så en telefon ikke hakker.
    var MAX_EDGE = 240;

    function loadFile(f) {
      setErr('');
      if (!f) return;
      if (!/^image\//.test(f.type || '')) { setErr(s.errNotImage || 'Please choose an image file.'); return; }
      var url = global.URL.createObjectURL(f);
      var im = new global.Image();
      im.onload = function () {
        var iw = im.naturalWidth || im.width, ih = im.naturalHeight || im.height;
        var scale = Math.min(1, MAX_EDGE / Math.max(iw, ih));
        var w = Math.max(1, Math.round(iw * scale)), h = Math.max(1, Math.round(ih * scale));
        var cv = doc.createElement('canvas');
        cv.width = w; cv.height = h;
        var ctx = cv.getContext('2d');
        ctx.drawImage(im, 0, 0, w, h);
        var colors = [];
        try { colors = extract(ctx.getImageData(0, 0, w, h).data, { max: o.max || MAX }); }
        catch (e) { setErr(s.errRead || 'Could not read that image.'); }
        render(colors);
        global.URL.revokeObjectURL(url);
      };
      im.onerror = function () {
        global.URL.revokeObjectURL(url);
        setErr(s.errUnreadable || 'Could not read that image file.');
      };
      im.src = url;
    }

    if (file) file.addEventListener('change', function () {
      if (file.files && file.files.length) loadFile(file.files[0]);
    });
    if (drop) {
      ['dragenter', 'dragover'].forEach(function (ev) {
        drop.addEventListener(ev, function (e) { e.preventDefault(); drop.classList.add('pg-img-over'); });
      });
      ['dragleave', 'drop'].forEach(function (ev) {
        drop.addEventListener(ev, function (e) { e.preventDefault(); drop.classList.remove('pg-img-over'); });
      });
      drop.addEventListener('drop', function (e) {
        var dt = e.dataTransfer;
        if (dt && dt.files && dt.files.length) loadFile(dt.files[0]);
      });
    }
    // Ctrl+V/⌘V er den hurtigste vej for et skærmbillede, men må ikke stjæle en
    // indsættelse i et felt — derfor kun uden for input/textarea.
    doc.addEventListener('paste', function (e) {
      var t = e.target;
      if (t && (t.tagName === 'INPUT' || t.tagName === 'TEXTAREA')) return;
      var items = e.clipboardData && e.clipboardData.items;
      if (!items) return;
      for (var i = 0; i < items.length; i++) {
        if (items[i].type && items[i].type.indexOf('image/') === 0) {
          var f = items[i].getAsFile();
          if (f) { loadFile(f); e.preventDefault(); return; }
        }
      }
    });

    return { loadFile: loadFile, render: render };
  }

  global.PALETTE_IMAGE = global.PALETTE_IMAGE || {};
  global.PALETTE_IMAGE.extract = extract;
  global.PALETTE_IMAGE.mount = mount;
  global.PALETTE_IMAGE.toHex = toHex;
})(typeof window !== 'undefined' ? window : globalThis);
