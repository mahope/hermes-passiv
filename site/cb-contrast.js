/* cb-contrast.js — WCAG-kontrasten for hver synstype i farveblindhedssimulatoren.
 *
 * Farve-tabellen viser hvordan en farve *ser ud* for protan-, deuteran- og
 * tritanopi, og forhåndsvisningen maler et tekststykke i de simulerede farver.
 * Men den siger ikke det tal en læser kan handle på: hvor mange gange lysere er
 * teksten så end baggrunden, *for den synstype*? Et par der består AA for
 * normalt syn kan falde under 4.5:1 for en deuteranop, fordi rød og grøn nærmer
 * sig hinanden i lysstyrke — og det er præcis den forskel et almindeligt
 * kontrasttjek ikke ser. De store simulatorer (fx Tim Dixons
 * billed-kontrasttjekker) viser den; vi gjorde ikke.
 *
 * Modellen er den *samme*: `simulate()` kommer fra `window.CB_SIM`, altså den
 * funktion tabellen og billed-kernen selv bruger. Der er derfor stadig kun én
 * Machado-implementering på siden — dette modul oversætter bare farveparret til
 * et WCAG-tal pr. type. Sværhedsgraden følger skyderen ovenfor, så tallet
 * matcher den simulering læseren ser.
 *
 *   CBCONTRAST.mount({ strings: { /* … *\/ } })
 *
 * Ordenes side er sidens egne, så den danske udgave ikke møder engelsk tekst.
 */
(function (global) {
  'use strict';

  // WCAG 2.x relativ luminans. Kanalerne gamma-ekspanderes først, som i
  // specifikationen — det er den kurve der gør `#808080` til L=0.216 og ikke
  // 0.5, og derfor et almindeligt sted at regne forkert.
  function luminance(rgb) {
    var c = [rgb[0], rgb[1], rgb[2]].map(function (v) {
      var s = v / 255;
      return s <= 0.03928 ? s / 12.92 : Math.pow((s + 0.055) / 1.055, 2.4);
    });
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2];
  }
  function ratio(a, b) {
    var l1 = luminance(a), l2 = luminance(b);
    if (l1 < l2) { var t = l1; l1 = l2; l2 = t; }
    return (l1 + 0.05) / (l2 + 0.05);
  }
  function hexToRgb(h) {
    var v = String(h == null ? '' : h).trim().replace(/^#/, '');
    if (/^[0-9a-f]{3}$/i.test(v)) {
      return [parseInt(v[0] + v[0], 16), parseInt(v[1] + v[1], 16), parseInt(v[2] + v[2], 16)];
    }
    if (/^[0-9a-f]{6}$/i.test(v)) {
      return [parseInt(v.slice(0, 2), 16), parseInt(v.slice(2, 4), 16), parseInt(v.slice(4, 6), 16)];
    }
    return null;
  }

  var AA_NORMAL = 4.5, AA_LARGE = 3;
  // Rækkefølgen er den samme som tabellen og billed-arket bruger, så en læser
  // kan følge én kolonne ned ad siden.
  var TYPES = [
    { type: null, key: 'normal' },
    { type: 'protanomaly', key: 'protan' },
    { type: 'deuteranomaly', key: 'deutan' },
    { type: 'tritanomaly', key: 'tritan' }
  ];

  // Den rene beregning: farvepar + sværhedsgrad ind, tal ud. Uden DOM, så
  // dommen i `tests/cb-contrast.test.mjs` kan kalde den direkte og holde den op
  // mod sin egen luminans-implementering. Returnerer null hvis modellen mangler
  // — så tier vi frem for at vise et tal vi ikke kan stå inde for.
  function readout(fgHex, bgHex, sev, labels) {
    var sim = global.CB_SIM;
    if (!sim || typeof sim.simulate !== 'function') return null;
    var fg = hexToRgb(fgHex), bg = hexToRgb(bgHex);
    if (!fg || !bg) return null;
    var s = Math.max(0, Math.min(1, Number(sev) || 0));
    var lab = labels || {};
    var rows = TYPES.map(function (t) {
      var f = t.type ? sim.simulate(fg.slice(), t.type, s) : fg;
      var b = t.type ? sim.simulate(bg.slice(), t.type, s) : bg;
      var r = ratio(f, b);
      return {
        type: t.type,
        label: lab[t.key] || t.key,
        ratio: r,
        passesNormal: r >= AA_NORMAL,
        passesLarge: r >= AA_LARGE
      };
    });
    var normal = rows[0];
    // Kun de typer der *falder under* fordi synet ændrer lysstyrkeforholdet —
    // altså dem der bestod for normalt syn, men ikke gør det nu.
    var dropped = rows.slice(1).filter(function (row) {
      return normal.passesNormal && !row.passesNormal;
    }).map(function (row) { return row.label; });
    return { rows: rows, normalPasses: normal.passesNormal, dropped: dropped };
  }

  function mount(opts) {
    var o = opts || {}, s = o.strings || {};
    var doc = global.document;
    var box = doc.getElementById(o.container || 'cvd-contrast');
    var fgSel = doc.getElementById('fg-select');
    var bgSel = doc.getElementById('bg-select2');
    var sevEl = doc.getElementById('severity');
    if (!box || !fgSel || !bgSel || !sevEl) return null;

    function el(tag, text, cls) {
      var e = doc.createElement(tag);
      if (text != null) e.textContent = text;
      if (cls) e.className = cls;
      return e;
    }
    function verdict(row) {
      if (row.passesNormal) return { text: s.pass || 'Pass', cls: 'pass' };
      if (row.passesLarge) return { text: s.largeOnly || 'Large text only', cls: 'warn' };
      return { text: s.fail || 'Fail', cls: 'fail' };
    }

    function render(res) {
      box.innerHTML = '';
      var table = el('table', null, 'cb-grid');
      var cap = el('caption', s.caption || 'WCAG contrast ratio for each vision type', 'sr-only');
      table.appendChild(cap);
      var thead = el('thead');
      var hr = el('tr');
      hr.appendChild(el('th', s.colVision || 'Vision', null));
      hr.appendChild(el('th', s.colRatio || 'Ratio', null));
      hr.appendChild(el('th', s.colVerdict || 'AA', null));
      thead.appendChild(hr);
      table.appendChild(thead);
      var tbody = el('tbody');
      res.rows.forEach(function (row) {
        var tr = el('tr');
        var th = el('th', row.label, null);
        th.setAttribute('scope', 'row');
        tr.appendChild(th);
        var num = row.ratio.toFixed(2).replace('.', s.decimal || '.');
        tr.appendChild(el('td', num + ' : 1', null));
        var v = verdict(row);
        tr.appendChild(el('td', v.text, v.cls));
        tbody.appendChild(tr);
      });
      table.appendChild(tbody);
      box.appendChild(table);

      // Én linje der siger hvad tabellen betyder — den er hele grunden til at
      // tjekke pr. synstype: et par kan bestå for dig og fejle for en anden.
      var note;
      if (!res.normalPasses) {
        note = s.baseFails || 'This pair already fails AA for normal text — fix the base contrast before colour blindness is considered.';
      } else if (res.dropped.length) {
        note = (s.dropPrefix || 'Colour blindness changes the verdict: ') +
          res.dropped.join(', ') + (s.dropSuffix || ' drop below 4.5:1 even though normal vision passes.');
      } else {
        note = s.unchanged || 'Every vision type stays at or above 4.5:1 — colour blindness does not change the verdict for this pair.';
      }
      box.appendChild(el('p', note, 'cb-note'));
    }

    function update() {
      var res = readout(fgSel.value, bgSel.value, Number(sevEl.value) / 100, s);
      if (!res) { box.innerHTML = ''; return null; }
      render(res);
      return res;
    }

    // `updateAll()` i sidens eget script kalder `update()` når sværhedsgraden
    // eller paletten ændrer sig. Farvefelterne skifter værdi uden at fyre et
    // `change`, når et farvevalg tilføjes eller fjernes, så vi lytter også selv
    // på dem — ellers stod tabellen fast på det forrige par.
    fgSel.addEventListener('change', update);
    bgSel.addEventListener('change', update);
    update();
    return { update: update, readout: readout };
  }

  global.CBCONTRAST = {
    mount: mount,
    readout: readout,
    ratio: ratio,
    luminance: luminance,
    hexToRgb: hexToRgb
  };
})(typeof window !== 'undefined' ? window : globalThis);
