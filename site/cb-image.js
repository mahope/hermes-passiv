/* cb-image.js — billed-simuleringen i farveblindhedssimulatoren.
 *
 * Farve-tabellen på `/color-blindness-simulator` og `-da` viser et par udvalgte
 * farver. Det er ikke det, de fleste kommer for: de vil se deres *egen*
 * skærm, deres logo eller et diagram gennem protan-, deuteran- og tritanopi.
 * En simulator der kun kender hex-felter kan ikke svare på det — og det er
 * præcis den mangel de store simulatorer (Coblis, Toptal) dækker og vi ikke
 * gjorde. Derfor kan et billede nu trækkes ind, indsættes eller vælges, og de
 * fire felter tegnes af den samme model som tabellen.
 *
 * Modellen er *den samme*: siden eksponerer sit eget `simulate`/`machadoMatrix`
 * som `window.CB_SIM`, og her oversættes den til én pixel-løkke. Der er derfor
 * ikke to Machado-implementeringer på siden der kan drive fra hinanden — kun én
 * model og to måder at kalde den på. `tests/cb-image.test.mjs` dømmer at
 * pixel-løkken giver præcis samme farve som `CB_SIM.simulate` for hver pixel,
 * så en hurtig vej ikke kan blive en anden model.
 *
 * Billedet læses med canvas i browseren og uploades aldrig, som resten af
 * siden lover. Der er ingen `fetch` her.
 *
 *   CBIMAGE.mount({ strings: { /* … *\/ } })
 */
(function (global) {
  'use strict';

  // Én celle pr. synstype i det 2×2-ark der vises og kan hentes. Størrelsen er
  // fast, så de fire felter kan sammenlignes side om side; billedet lægges
  // "contain" ind i cellen, så et portræt- eller landskabsbillede ikke gør
  // arket skævt.
  var CELL_W = 480, CELL_H = 300, PAD = 12, LABEL_H = 24;

  function clamp255(v) { return v < 0 ? 0 : v > 255 ? 255 : Math.round(v); }
  function srgbToLinear(c) { return c <= 0.04045 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4); }
  function linearToSrgb(c) {
    if (c < 0) c = 0; else if (c > 1) c = 1;
    return c <= 0.0031308 ? c * 12.92 : 1.055 * Math.pow(c, 1 / 2.4) - 0.055;
  }

  // Den samme model som `simulate()` i farve-tabellen, men på et RGBA-array.
  // Matricen hentes én gang for hele billedet, og konverteringen ligger inline,
  // så en 480×300-celle ikke laver tre nye arrays pr. pixel.
  //
  // `data` ændres på plads. Returnerer false hvis modellen ikke er indlæst, så
  // en side der glemmer at eksponere `CB_SIM` fejler synligt frem for at vise
  // et uændret billede og kalde det en simulering.
  function transform(data, type, sev) {
    var sim = global.CB_SIM;
    if (!sim || typeof sim.matrix !== 'function') return false;
    if (!(sev > 0)) return true;                 // 0 % = normalt syn, rør intet
    var m = sim.matrix(type, sev);
    for (var i = 0; i < data.length; i += 4) {
      if (data[i + 3] === 0) continue;           // helt gennemsigtig = baggrund, ikke billede
      var r = srgbToLinear(data[i] / 255);
      var g = srgbToLinear(data[i + 1] / 255);
      var b = srgbToLinear(data[i + 2] / 255);
      data[i]     = clamp255(linearToSrgb(m[0][0] * r + m[0][1] * g + m[0][2] * b) * 255);
      data[i + 1] = clamp255(linearToSrgb(m[1][0] * r + m[1][1] * g + m[1][2] * b) * 255);
      data[i + 2] = clamp255(linearToSrgb(m[2][0] * r + m[2][1] * g + m[2][2] * b) * 255);
    }
    return true;
  }

  function mount(opts) {
    var o = opts || {}, s = o.strings || {};
    var doc = global.document;
    // Uden canvas er vi ikke på simulator-siden (fx i en test-sandkasse), og
    // `mount()` skal bare gøre ingenting frem for at kaste.
    var cv = doc.getElementById('cbi-cv');
    if (!cv || typeof cv.getContext !== 'function') return null;
    var file = doc.getElementById('cbi-file');
    var errEl = doc.getElementById('cbi-error');
    var dl = doc.getElementById('cbi-download');
    var empty = doc.getElementById('cbi-empty');
    var sevEl = doc.getElementById('severity');
    var drop = doc.getElementById('cbi-drop');
    var img = null;

    function setErr(msg) { if (errEl) errEl.textContent = msg || ''; }

    function panelLabels() {
      return [
        { type: null, label: s.original || 'Original' },
        { type: 'protanomaly', label: s.protan || 'Protanopia' },
        { type: 'deuteranomaly', label: s.deutan || 'Deuteranopia' },
        { type: 'tritanomaly', label: s.tritan || 'Tritanopia' }
      ];
    }

    // Grundbilledet skaleret ind i én celle. Bruges som kilde for både det
    // oprindelige felt og de tre simuleringer, så de fire felter umuligt kan
    // vise fire forskellige skaleringer.
    function baseCanvas() {
      var base = doc.createElement('canvas');
      base.width = CELL_W; base.height = CELL_H;
      var bctx = base.getContext('2d');
      bctx.fillStyle = '#ffffff';
      bctx.fillRect(0, 0, CELL_W, CELL_H);
      var iw = img.naturalWidth || img.width, ih = img.naturalHeight || img.height;
      var scale = Math.min(CELL_W / iw, CELL_H / ih);
      var dw = Math.max(1, Math.round(iw * scale)), dh = Math.max(1, Math.round(ih * scale));
      bctx.drawImage(img, Math.round((CELL_W - dw) / 2), Math.round((CELL_H - dh) / 2), dw, dh);
      return base;
    }

    function render() {
      if (!img) return;
      var base = baseCanvas();
      var baseData = base.getContext('2d').getImageData(0, 0, CELL_W, CELL_H);
      var sev = sevEl ? Number(sevEl.value) / 100 : 1;
      var sheetW = PAD * 3 + CELL_W * 2;
      var sheetH = PAD * 3 + (CELL_H + LABEL_H) * 2;
      cv.width = sheetW; cv.height = sheetH;
      var ctx = cv.getContext('2d');
      ctx.fillStyle = '#ffffff';
      ctx.fillRect(0, 0, sheetW, sheetH);
      panelLabels().forEach(function (p, k) {
        var x = PAD + (k % 2) * (CELL_W + PAD);
        var y = PAD + (k >= 2 ? 1 : 0) * (CELL_H + LABEL_H + PAD);
        ctx.fillStyle = '#111827';
        ctx.font = '600 17px system-ui, -apple-system, Segoe UI, sans-serif';
        ctx.textBaseline = 'top';
        ctx.fillText(p.label, x, y);
        var ty = y + LABEL_H;
        if (!p.type || !(sev > 0)) { ctx.drawImage(base, x, ty); return; }
        // Simuleringen lægges i et mellemliggende canvas, fordi `putImageData`
        // skriver i enheds-pixels og ikke kan tegnes forskudt ind i arket.
        var tmp = doc.createElement('canvas');
        tmp.width = CELL_W; tmp.height = CELL_H;
        var tctx = tmp.getContext('2d');
        var out = tctx.createImageData(CELL_W, CELL_H);
        out.data.set(baseData.data);
        transform(out.data, p.type, sev);
        tctx.putImageData(out, 0, 0);
        ctx.drawImage(tmp, x, ty);
      });
      cv.hidden = false;
      if (empty) empty.hidden = true;
      if (dl) dl.disabled = false;
    }

    function loadFile(f) {
      setErr('');
      if (!f) return;
      if (!/^image\//.test(f.type || '')) { setErr(s.errNotImage || 'Please choose an image file.'); return; }
      var url = global.URL.createObjectURL(f);
      var im = new global.Image();
      im.onload = function () {
        img = im;
        render();
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
        drop.addEventListener(ev, function (e) { e.preventDefault(); drop.classList.add('cbi-over'); });
      });
      ['dragleave', 'drop'].forEach(function (ev) {
        drop.addEventListener(ev, function (e) { e.preventDefault(); drop.classList.remove('cbi-over'); });
      });
      drop.addEventListener('drop', function (e) {
        var dt = e.dataTransfer;
        if (dt && dt.files && dt.files.length) loadFile(dt.files[0]);
      });
    }
    // Indsæt med Ctrl+V/⌘V er den hurtigste vej for et skærmbillede, men må
    // ikke stjæle en indsættelse i et felt — derfor kun uden for input/textarea.
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
    // Skyderen ovenfor er fælles med farve-tabellen, så en ændring skal tegne
    // billedet igen — ellers stod de fire felter fast på den sværhedsgrad,
    // billedet først blev målt med.
    if (sevEl) sevEl.addEventListener('input', function () { if (img) render(); });
    if (dl) dl.addEventListener('click', function () {
      if (!img) return;
      try {
        var a = doc.createElement('a');
        a.href = cv.toDataURL('image/png');
        a.download = 'colorblind-simulation.png';
        doc.body.appendChild(a); a.click();
        global.setTimeout(function () { a.remove(); }, 500);
      } catch (e) { setErr(s.errDownload || ''); }
    });

    return { render: render, loadFile: loadFile, hasImage: function () { return !!img; } };
  }

  global.CBIMAGE = global.CBIMAGE || {};
  global.CBIMAGE.transform = transform;
  global.CBIMAGE.mount = mount;
  global.CBIMAGE.CELL = { width: CELL_W, height: CELL_H };
})(typeof window !== 'undefined' ? window : globalThis);
