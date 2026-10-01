/* Kernen i tekst-på-billede-kontrasttjekkeren — ét sted, fire sider.
 *
 * Før denne fil lå samplings-, tegne- og resultatlogikken som en ~220-linjes
 * inline `<script>` på hver af `/text-on-image-checker` (EN), samme fil på
 * `-da`, og igen på de to artikler. Fire kopier af den samme WCAG-formel er
 * fire steder, hvor en rettelse kan glemmes — så kernen ligger her, og siden
 * leverer sin **egen tekst og sin egen markup** til `mount()`.
 *
 * Bevidst ikke en udfyldt tekst-tabel i denne fil: købsprisen, perioden og
 * pro-kortets markup skal stå i sidens HTML, fordi `check_own_prices` og
 * `check_stripe_ctas` dømmer pr. HTML-fil. En pris i en `.js` er en pris ingen
 * port kan se.
 *
 *   TiContrast.mount({ prefix: '', strings: { /* … *\/ } })
 *
 * `prefix` sættes foran hvert id, så artiklen kan have sit eget sæt felter
 * (`art-cv`, `art-file` …) uden at kollidere med en anden forekomst på samme
 * side. Uden prefix er id'erne `cv`, `file`, `text`, `fg`, `fontsize`, `err`
 * og `result` — uændret fra før, så de eksisterende domme stadig finder dem.
 */
(function (global) {
  'use strict';

  function hexToRgb(h) {
    h = String(h).replace('#', '');
    return [parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16), parseInt(h.slice(4, 6), 16)];
  }
  function lum(rgb) {
    var c = rgb.map(function (v) {
      v /= 255;
      return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
    });
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2];
  }
  function ratio(a, b) {
    var l1 = lum(a), l2 = lum(b);
    if (l1 < l2) { var t = l1; l1 = l2; l2 = t; }
    return (l1 + 0.05) / (l2 + 0.05);
  }

  function mount(opts) {
    var o = opts || {};
    var p = o.prefix || '';
    var s = o.strings || {};
    var $ = function (id) { return global.document.getElementById(p + id); };
    var cv = $('cv');
    if (!cv) return null;
    var ctx = cv.getContext('2d', { willReadFrequently: true });
    var img = null, tx = 0, ty = 0, dragging = false;

    // Dansk bruger komma, engelsk punktum — samme tal, to sæt.
    function fmt(n) {
      return String(n).replace('.', s.dec === ',' ? ',' : '.');
    }

    // A pixel with more than this much glyph on it is text, not background.
    // Measured 30/9: the old filter threw away anything within dr+dg+db < 120
    // of the text colour, but an anti-aliased glyph edge at 16% coverage
    // already scores 126 — so the edges survived, the tool measured white
    // text against its own grey fringe, and answered 1.47:1 for white text
    // on a white photo.
    var COVER_MAX = 8;

    function fontSizePx() {
      return Math.max(18, Math.round(cv.width * 0.06));
    }
    // `measureText()` reads whatever font is currently set, so every caller
    // that measures has to set it first — otherwise the first box after page
    // load is measured in the canvas default of 10px sans-serif.
    function applyFont() {
      ctx.font = '700 ' + fontSizePx() + 'px system-ui, sans-serif';
      ctx.textBaseline = 'top';
    }
    function draw() {
      if (!img) return;
      ctx.drawImage(img, 0, 0, cv.width, cv.height);
      applyFont();
      ctx.fillStyle = $('fg').value;
      ctx.fillText($('text').value || ' ', tx, ty);
    }
    // The letters on their own, on a cleared canvas. Alpha is then exactly how
    // much of each pixel the glyph covers, which is the one thing a colour
    // distance can never tell you.
    function drawTextLayer() {
      ctx.clearRect(0, 0, cv.width, cv.height);
      applyFont();
      ctx.fillStyle = $('fg').value;
      ctx.fillText($('text').value || ' ', tx, ty);
    }

    // The box is clipped to the canvas, never nudged back inside it:
    // getImageData() outside the canvas returns transparent black, which
    // reads as a black background and invents contrast that is not there.
    function textBox() {
      applyFont();
      var x = Math.max(0, Math.round(tx)), y = Math.max(0, Math.round(ty));
      var w = Math.min(Math.max(2, Math.ceil(ctx.measureText($('text').value || '').width)),
                       cv.width - x);
      var h = Math.min(fontSizePx(), cv.height - y);
      if (w < 2 || h < 2) return null;
      return { x: x, y: y, w: w, h: h };
    }

    function sampleContrast() {
      if (!img) return null;
      var box = textBox();
      if (!box) return null;
      // Pass 1 — the photo alone, read back as the background.
      ctx.clearRect(0, 0, cv.width, cv.height);
      ctx.drawImage(img, 0, 0, cv.width, cv.height);
      var photo = ctx.getImageData(box.x, box.y, box.w, box.h).data;
      // Pass 2 — the letters alone, so alpha is the glyph coverage.
      drawTextLayer();
      var glyph = ctx.getImageData(box.x, box.y, box.w, box.h).data;

      var bgCandidates = [];
      for (var i = 0; i < photo.length; i += 4) {
        if (glyph[i + 3] > COVER_MAX) continue; // this pixel is a letter
        bgCandidates.push([photo[i], photo[i + 1], photo[i + 2]]);
      }
      // Every pixel under the box is more than a letter thick, so there is no
      // visible background left to read. Fall back to the photo under the box
      // rather than reporting no number at all.
      if (!bgCandidates.length) {
        for (var j = 0; j < photo.length; j += 4) {
          bgCandidates.push([photo[j], photo[j + 1], photo[j + 2]]);
        }
      }
      // Worst case: the foreground against the lightest and the darkest
      // background pixel a reader can actually see behind the letters.
      var minL = Infinity, maxL = -Infinity, minC = null, maxC = null;
      bgCandidates.forEach(function (c) {
        var L = lum(c);
        if (L < minL) { minL = L; minC = c; }
        if (L > maxL) { maxL = L; maxC = c; }
      });
      var fgRgb = hexToRgb($('fg').value);
      var worst = Infinity;
      [minC, maxC].forEach(function (c) {
        if (!c) return;
        var r = ratio(fgRgb, c);
        if (r < worst) worst = r;
      });
      return { ratio: worst === Infinity ? null : worst };
    }

    function updateResult() {
      var res = $('result'), errEl = $('err');
      errEl.textContent = '';
      var sample = sampleContrast();
      if (!sample || sample.ratio === null) { res.hidden = true; return; }
      var large = $('fontsize').value === 'large';
      var need = large ? 3 : 4.5;
      var aaaNeed = large ? 4.5 : 7;
      var r = sample.ratio;
      var passAA = r >= need;
      var passAAA = r >= aaaNeed;
      res.hidden = false;
      // Klasserne er *ikke* præfikset: de er `ti-*` i `style.css`, og en
      // forekomst på en artikelside skal se identisk ud med værktøjssiden.
      // Præfikset gælder kun id'erne — dem skal to forekomster på samme side
      // kunne have hver sin.
      res.className = 'ti-result ' + (passAA ? 'ti-pass' : 'ti-fail');
      // Alt der kommer fra brugeren (`r`) er et tal, ikke markup, og alt
      // `s.*` er sidens egen tekst fra den side den ligger på. Ingenting her
      // bygger en streng af noget en besøgende kan skrive.
      res.innerHTML =
        '<span class="ti-badge" style="background:' + (passAA ? '#16a34a' : '#dc2626') + '">' +
        (passAA ? s.pass : s.fail) + '</span>&nbsp; <strong>' + fmt(r.toFixed(2)) + ':1</strong> ' +
        (s.worstCase || '') + ' ' + (s.needs || '') + ' ' + fmt(need) + ':1 ' + (s.forAA || '') + ' ' +
        (large ? (s.largeText || '') : (s.normalText || '')) +
        (passAA && !passAAA ? '<br>' + (s.aaNotAAA || '') + ' (' + fmt(aaaNeed) + ':1).' :
         passAAA ? '<br>' + (s.alsoAAA || '') :
         '<br>' + (s.tryFix || '')) +
        '<br><span style="font-size:.85rem;color:var(--color-text-muted)">' + (s.measured || '') + '</span>'
        + (s.proCard || '') +
        '<br><span style="font-size:13px;color:var(--color-text-muted)">' + (s.note || '') + '</span>';
    }

    function loadFile(file) {
      var errEl = $('err');
      errEl.textContent = '';
      if (!file || !/^image\//.test(file.type)) { errEl.textContent = s.errNotImage || ''; return; }
      var url = global.URL.createObjectURL(file);
      var im = new Image();
      im.onload = function () {
        img = im;
        var maxW = 900;
        var scale = Math.min(1, maxW / im.naturalWidth);
        cv.width = Math.round(im.naturalWidth * scale);
        cv.height = Math.round(im.naturalHeight * scale);
        tx = Math.round(cv.width * 0.06);
        ty = Math.round(cv.height * 0.70);
        global.URL.revokeObjectURL(url);
        updateAll();
      };
      im.onerror = function () { errEl.textContent = s.errUnreadable || ''; };
      im.src = url;
    }

    function pos(e) {
      var rect = cv.getBoundingClientRect();
      var cx = (e.touches ? e.touches[0].clientX : e.clientX) - rect.left;
      var cy = (e.touches ? e.touches[0].clientY : e.clientY) - rect.top;
      tx = cx * cv.width / rect.width - fontSizePx() / 2;
      ty = cy * cv.height / rect.height - fontSizePx() / 2;
    }
    function onMove(e) {
      if (!img) return;
      e.preventDefault();
      pos(e);
      updateAll();
    }
    // `sampleContrast()` ends on a cleared canvas holding only the letters, so
    // the visible drawing is the last thing that happens, not the first.
    function updateAll() { updateResult(); draw(); }

    $('file').addEventListener('change', function (e) { loadFile(e.target.files[0]); });
    $('text').addEventListener('input', updateAll);
    $('fg').addEventListener('input', updateAll);
    $('fontsize').addEventListener('change', updateAll);
    cv.addEventListener('mousedown', function (e) { dragging = true; onMove(e); });
    global.addEventListener('mousemove', function (e) { if (dragging) onMove(e); });
    global.addEventListener('mouseup', function () { dragging = false; });
    cv.addEventListener('touchstart', onMove, { passive: false });

    // Default demo background so the tool works before uploading anything.
    var demo = global.document.createElement('canvas');
    demo.width = 900; demo.height = 420;
    var dctx = demo.getContext('2d');
    var grad = dctx.createLinearGradient(0, 0, 900, 420);
    grad.addColorStop(0, '#1e3a5f'); grad.addColorStop(0.55, '#4a7ba6'); grad.addColorStop(1, '#c9d8e4');
    dctx.fillStyle = grad; dctx.fillRect(0, 0, 900, 420);
    dctx.fillStyle = 'rgba(255,255,255,0.35)';
    dctx.beginPath(); dctx.arc(650, 130, 90, 0, Math.PI * 2); dctx.fill();
    img = demo;
    cv.width = demo.width; cv.height = demo.height;
    tx = Math.round(cv.width * 0.06); ty = Math.round(cv.height * 0.62);
    updateAll();

    // Synlig for testene i `tests/scan-clients.test.mjs`, der dømmer den her
    // kode i en sandkasse i stedet for at tro på markup.
    return { sampleContrast: sampleContrast, updateAll: updateAll };
  }

  global.TiContrast = { mount: mount, lum: lum, ratio: ratio, hexToRgb: hexToRgb };
})(typeof globalThis !== 'undefined' ? globalThis : this);