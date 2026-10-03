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
  function rgbToHex(rgb) {
    return '#' + rgb.map(function (v) {
      var n = Math.max(0, Math.min(255, Math.round(v))).toString(16);
      return n.length < 2 ? '0' + n : n;
    }).join('');
  }
  // Den *inverse* af `lum()`s sRGB-kurve: hvilken kanalværdi giver den relative
  // lysstyrke `L`? De to er ikke det samme tal — `lum([128,128,128])` er 0.216,
  // ikke 0.502 — så at regne i `L` og så bruge det som kanalværdi giver en farve
  // der er dobbelt så mørk som den man bad om. Uden denne funktion ville den
  // foreslåede tekstfarve være *mørkere* end den tærskel den skal klare, og
  // dommen ville være grøn fordi den måler `ratio()` i `lum()`-rum.
  function lumToChannel(L) {
    var v = (Math.pow(Math.max(0, Math.min(1, L)), 1 / 2.4) * 1.055 - 0.055) * 255;
    return Math.max(0, Math.min(255, v));
  }
  function grey(L) { var v = lumToChannel(L); return [v, v, v]; }
  // Bland baggrundspixelen med et slør af dækning `a`. Det er præcis det
  // browseren gør med `rgba(0,0,0,.62)` over et billede, og det er den
  // blanding læseren ser — så dommen skal regne på *den*, ikke på billedet.
  function over(bg, hex, a) {
    var sc = hexToRgb(hex);
    return bg.map(function (v, i) { return sc[i] * a + v * (1 - a); });
  }
  // Den mindste dækning der får **begge** endepunkter over tærsklen. Begge
  // par (sort slør + hvid tekst, lys slør + sort tekst) bliver bedre monotont
  // med stigende dækning, så binærsøgningen er gyldig for dem begge — og
  // svaret tjekkes bagefter med `ratio()`. Løsningen af en formel er en
  // påstand; målingen er dommen.
  function minScrimAlpha(bgMin, bgMax, need, scrim, textHex) {
    var text = hexToRgb(textHex);
    function ok(a) {
      return ratio(text, over(bgMax, scrim, a)) >= need &&
             ratio(text, over(bgMin, scrim, a)) >= need;
    }
    if (!ok(1)) return null;
    var lo = 0, hi = 1, mid = 0;
    for (var i = 0; i < 30; i++) {
      mid = (lo + hi) / 2;
      if (ok(mid)) hi = mid; else lo = mid;
    }
    // Op til hele procent, og *opad*. En dækning der rundes ned ville se
    // pænere ud i tallet og så fejle igen, og det er præcis den løfte der ikke
    // må gå herfra.
    var pct = Math.min(1, Math.ceil(hi * 100) / 100);
    return ok(pct) ? pct : null;
  }
  // Den rettelse værktøjet før *bad om* i stedet for at give: læseren skulle
  // selv finde på både en tekstfarve og et slør, og det er to tal der skal
  // slås sammen på én gang. Kernen løser dem begge, i den rækkefølge der
  // ødelægger mindst.
  //
  // 1. **Én tekstfarve alene**, når baggrunden er smal nok til at én farve kan
  //    klare begge ende. Det er det mindst indgribende fix, så det prøves
  //    først, og den grå der findes er den *mørkeste* der stadig passerer —
  //    så farven beholder så meget af billedets tone som muligt.
  // 2. **Et slør**, når baggrunden spænder for meget til at én farve kan
  //    klare den. Det er præcis det råd værktøjet selv gav («add a
  //    translucent scrim») — nu med den mindste dækning der virker i stedet
  //    for «prøv lidt mørkere».
  //
  //   `bgMin`/`bgMax` er endepunkterne fra `sampleContrast()`: den lyseste og
  //   den mørkeste pixel under bogstaverne, altså det værktøjet *allerede*
  //   har målt. Rettelsen er derfor aldrig baseret på et billede, der er læst
  //   endnu en gang og måske målt et andet sted i.
  function suggestFix(bgMin, bgMax, need, currentHex) {
    if (!bgMin || !bgMax) return null;

    // 1. Én tekstfarve mod begge ende. Hvert endepunkt stiller sit eget krav,
    //    og det er det *strammeste* af de to, der bestemmer:
    //      mørkere tekst: (L_ende+0.05)/(L+0.05) >= need  =>  L <= (L_ende+0.05)/need-0.05
    //                     strammest for den DØRKESTE baggrund, fordi en mørk
    //                     tekst mod en mørk baggrund er den korte afstand.
    //      lysere tekst : (L+0.05)/(L_ende+0.05) >= need  =>  L >= need*(L_ende+0.05)-0.05
    //                     strammest for den LYSE baggrund.
    //    De to intervaller er disjunkte: en L imellem dem *fejler* — så en løsning
    //    der kun tager den ene ende ville give en farve, der fejler den anden.
    //    Derfor løses de to grene hver for sig, og kravet tjekkes bagefter med
    //    `ratio()` mod begge.
    var m = Math.min(lum(bgMin), lum(bgMax)); // den mørkeste baggrund
    var l = Math.max(lum(bgMin), lum(bgMax)); // den lyseste baggrund
    var kandidat = [];
    var morkMax = (m + 0.05) / need - 0.05;            // mørkere tekst: højst denne L
    var lysMin = need * (l + 0.05) - 0.05;              // lysere tekst: mindst denne L
    if (morkMax >= 0) kandidat.push(morkMax * 0.94);    // marginen *ind* mod den mørke ende
    if (lysMin <= 1) kandidat.push(Math.min(1, lysMin * 1.06)); // ad den lyse ende
    // Den kandidat der faktisk *består begge* ende tages, og den der ligger
    // tættest på den nuværende tekstfarve foretrækkes — en rettelse der
    // flytter farven mindst, er den bruteren genkender som sin egen.
    var nu = currentHex ? lum(hexToRgb(currentHex)) : 1;
    var bedst = null;
    kandidat.forEach(function (L) {
      var rgb = grey(L);
      var ra = Math.min(ratio(rgb, bgMin), ratio(rgb, bgMax));
      if (ra < need) return;                 // kravet er *målt*, ikke antaget
      if (!bedst || Math.abs(L - nu) < Math.abs(bedst.L - nu)) bedst = { L: L, rgb: rgb, r: ra };
    });
    if (bedst) {
      return { kind: 'color', hex: rgbToHex(bedst.rgb), scrim: null, alpha: 0, ratio: bedst.r };
    }

    // 2. Slør. Begge kandidater prøves, og den med mindst dækning vinder —
    //    en mindre sløring ligger tættere på det billede, bruteren sendte ind.
    bedst = null;
    [{ s: '#000000', t: '#ffffff' }, { s: '#ffffff', t: '#000000' }].forEach(function (k) {
      var a = minScrimAlpha(bgMin, bgMax, need, k.s, k.t);
      if (a !== null && (!bedst || a < bedst.alpha)) bedst = { kind: 'scrim', scrim: k.s, alpha: a, hex: k.t };
    });
    if (!bedst) return null;
    bedst.ratio = Math.min(
      ratio(hexToRgb(bedst.hex), over(bgMax, bedst.scrim, bedst.alpha)),
      ratio(hexToRgb(bedst.hex), over(bgMin, bedst.scrim, bedst.alpha))
    );
    return bedst;
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
    // Den rettelse kernen selv lavede, så siden kan fortælle *hvad* der skete —
    // uden den er der kun et tal, og et tal uden årsag er det samme som det
    // problem værktøjet havde før. Nulstilles når bruteren selv rører
    // farvefeltet, ellers ville en gammel beskrivelse stå under et tal de selv
    // har lavet.
    var lastFix = null;
    // Sløret der ligger over billedet lige nu, eller null. Det er *tegnet* i
    // `draw()` og regnet på i `effectiveBg()`, så tallet og det læseren ser
    // kommer fra samme blanding.
    var scrim = null;

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
      // Sløret tegnes på *canvas*, ikke kun i regningen. Ellers ville værktøjet
      // vise et bedre tal end det læseren kan se, og det er den værste slags
      // løfte: et tal der kun er rigtigt i koden.
      if (scrim) drawScrim();
      applyFont();
      ctx.fillStyle = $('fg').value;
      ctx.fillText($('text').value || ' ', tx, ty);
    }
    // Sløret dækker præcis den boks, teksten står i — og lidt uden om, så
    // kanten af sløret ikke ligger i bogstavernes egen baggrund, hvor en
    // læser ville se en skarp stribe.
    function drawScrim() {
      var box = textBox();
      if (!box) return;
      var pad = Math.round(fontSizePx() * 0.35);
      ctx.save();
      ctx.fillStyle = scrim.hex + Math.round(scrim.alpha * 255).toString(16).padStart(2, '0');
      ctx.fillRect(Math.max(0, box.x - pad), Math.max(0, box.y - pad),
                   Math.min(cv.width, box.w + pad * 2), Math.min(cv.height, box.h + pad * 2));
      ctx.restore();
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
      // Sløret er en del af det bruteren ser, så det er en del af det der
      // måles. Pass 1 tegner kun billedet, så blandingen laves her — på præcis
      // den måde `drawScrim()` maler den, med samme farve og samme dækning.
      // Uden dette viste værktøjet et bedre tal end det læseren kan se, fordi
      // dommen ville regne på det rå billede mens sløret lå tegnet oveni.
      var visMin = effectiveBg(minC), visMax = effectiveBg(maxC);
      var fgRgb = hexToRgb($('fg').value);
      var worst = Infinity;
      [visMin, visMax].forEach(function (c) {
        if (!c) return;
        var r = ratio(fgRgb, c);
        if (r < worst) worst = r;
      });
      // Endepunkterne gives videre som *rå* billedpixels, uden slør. Pass 1
      // tegner kun billedet, så de er uafhængige af hvad der ligger oveni —
      // og det er dem `suggestFix()` så danner sin *effektive* baggrund af, så
      // dens svar afhænger af det der faktisk er tegnet lige nu.
      return { ratio: worst === Infinity ? null : worst, bgMin: minC, bgMax: maxC };
    }

    // Det bruteren ser bag bogstaverne: billedet, og sløret oveni hvis der er
    // ét. Denne blanding er både det `drawScrim()` maler og det tallet bliver
    // regnet på — de to kan derfor ikke komme i ukig.
    function effectiveBg(c) {
      if (!c) return null;
      return scrim ? over(c, scrim.hex, scrim.alpha) : c;
    }

    // Den ene knap, der manglede: «Fix it». Den sætter enten tekstfarven eller
    // sløret til det, der passerer, og lader så `updateAll()` genmåle — så det
    // der vises bagefter er en *ny måling* af det samme billede, ikke et løfte
    // om at et bedre tal ville komme.
    function applyFix(fix) {
      if (!fix) return false;
      lastFix = fix;
      if (fix.kind === 'scrim') {
        scrim = { hex: fix.scrim, alpha: fix.alpha };
        $('fg').value = fix.hex;
      } else {
        scrim = null;
        $('fg').value = fix.hex;
      }
      updateAll();
      return true;
    }

    // Hvad kernen gjorde, i lærerens sprog. `scrimPct` og `hex` er tal og
    // farver fra kernens egen måling — aldrig noget en besøgende har skrevet —
    // og hele strengen kommer fra siden, så en dansk læser ikke møder en
    // engelsk beskrivelse af sin egen rettelse.
    function fixBeskrivelse(f) {
      if (f.kind === 'scrim') {
        // Sløret er prøvet i begge retninger — sort baggrund med lys tekst,
        // hvid baggrund med mørk tekst — og den med mindst dækning vinder.
        // På et lyst billede er det den *hvide* der slår, så en beskrivelse
        // der altid sagde «mørkt lag» ville være en løfte der kun holder for
        // den ene. Kernen ved hvilken retning der vandt; ordene kommer fra
        // siden, så en dansk læser ikke møder en engelsk beskrivelse.
        var morkt = lum(hexToRgb(f.scrim)) < 0.5;
        return ((morkt ? s.fixedScrimDark : s.fixedScrimLight) || '')
          .replace('%s', Math.round(f.alpha * 100));
      }
      return (s.fixed || '').replace('%s', f.hex);
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
      // Rettelsen regnes på den måling vi lige lavede — og på det slør der
      // allerede ligger, så et nyt forslag ikke oveni et gammelt. Den foreslås
      // kun når der faktisk fejler: på en bestået farve ville «fix»-knappen
      // være en knap uden opgave.
      var fix = passAA ? null : suggestFix(effectiveBg(sample.bgMin), effectiveBg(sample.bgMax), need, $('fg').value);
      res.hidden = false;
      // Klasserne er *ikke* præfikset: de er `ti-*` i `style.css`, og en
      // forekomst på en artikelside skal se identisk ud med værktøjssiden.
      // Præfikset gælder kun id'erne — dem skal to forekomster på samme side
      // kunne have hver sin.
      res.className = 'ti-result ' + (passAA ? 'ti-pass' : 'ti-fail');
      // Alt der kommer fra brugeren (`r`) er et tal, ikke markup, og alt
      // `s.*` er sidens egen tekst fra den side den ligger på. Ingenting her
      // bygger en streng af noget en besøgende kan skrive. Knappen bruges
      // `<button type="button">` og ikke et `<a href="#">`, fordi den gør
      // noget ved siden — ikke en ny side — og en anchor ville blive
      // genindlæst i historikken ved hvert tryk.
      res.innerHTML =
        '<span class="ti-badge" style="background:' + (passAA ? '#16a34a' : '#dc2626') + '">' +
        (passAA ? s.pass : s.fail) + '</span>&nbsp; <strong>' + fmt(r.toFixed(2)) + ':1</strong> ' +
        (s.worstCase || '') + ' ' + (s.needs || '') + ' ' + fmt(need) + ':1 ' + (s.forAA || '') + ' ' +
        (large ? (s.largeText || '') : (s.normalText || '')) +
        (passAA && !passAAA ? '<br>' + (s.aaNotAAA || '') + ' (' + fmt(aaaNeed) + ':1).' :
         passAAA ? '<br>' + (s.alsoAAA || '') :
          '<br>' + (s.tryFix || '')) +
        (fix && s.fixBtn ? '<br><button type="button" class="btn-secondary ti-fix" data-ti-fix>' + s.fixBtn + '</button>' : '') +
        (lastFix ? '<br><span class="ti-fixed">' + fixBeskrivelse(lastFix) + '</span>' : '') +
        (s.downloadBtn ? '<br><button type="button" class="btn-secondary ti-dl" data-ti-dl>' + s.downloadBtn + '</button>' : '') +
        '<br><span style="font-size:.85rem;color:var(--color-text-muted)">' + (s.measured || '') + '</span>'
        + (s.proCard || '') +
        '<br><span style="font-size:13px;color:var(--color-text-muted)">' + (s.note || '') + '</span>';
      // Lytteren bindes på den knap `innerHTML` lige nu skrev, ikke på `res`,
      // så en ny måling der skriver en ny knap ikke efterlader to lyttere på
      // den gamle. `updateAll()` kaldes inde i handleren, som genskriver
      // `innerHTML` — og den her knap forsvinder, fordi den nye måling
      // består, så der ikke kan opstå et uendeligt klik-loop.
      var btn = res.querySelector('[data-ti-fix]');
      if (btn) btn.addEventListener('click', function () { applyFix(fix); });
      var dl = res.querySelector('[data-ti-dl]');
      if (dl) dl.addEventListener('click', downloadPng);
    }

    // Den rettede grafik som en fil. Før 3/10 endte værktøjet ved et tal: bruteren
    // rettede teksten, fik et grønt tal — og skulle selv finde ud af hvordan han
    // fik sit billede med sin egen rettelse ud af værktøjet igen. Det er hele
    // grunden til at han er her.
    //
    // `draw()` kaldes igen **før** eksporten, fordi `sampleContrast()` efterlader
    // canvas med *kun bogstaverne* på et ryddet billede. Uden den ville den
    // hentede fil være en transparent baggrund med hvid tekst — altså ikke det
    // bruteren lige har set og målt. Efter «Fix it» er sløret og den nye
    // tekstfarve dermed *med* i filen, hvilket er hele poenget.
    //
    // Filnavnet er sidens egen streng, aldrig bruterens tekst: et navn bygget på
    // noget en besøgende har skrevet kan indeholde `/`, `..` eller et tegn, der
    // ikke kan bruges i et filnavn.
    function downloadPng() {
      if (!img) return false;
      draw();
      var dataUrl;
      try {
        dataUrl = cv.toDataURL('image/png');
      } catch (e) {
        return false;
      }
      var doc = global.document;
      var a = doc.createElement('a');
      a.href = dataUrl;
      a.download = (s.fileStem || 'text-on-image') + '.png';
      // Chrome og Firefox udløser et download på et anchor der ikke sidder i
      // dokumentet, men hænger det op i DOM'en mens klikket varer, gør det også
      // det i Safari — og fjernes igen bagefter, så der ikke bliver liggende.
      if (doc.body && doc.body.appendChild) doc.body.appendChild(a);
      if (a.click) a.click();
      if (a.remove) a.remove();
      return true;
    }

    function loadFile(file) {
      var errEl = $('err');
      errEl.textContent = '';
      if (!file || !/^image\//.test(file.type)) { errEl.textContent = s.errNotImage || ''; return; }
      var url = global.URL.createObjectURL(file);
      var im = new Image();
      im.onload = function () {
        img = im;
        // Et nyt billede er et nyt spørgsmål. Sløret var beregnet på *sidste*
        // billedes endepunkter, så hvis det blev liggende ville tallet på det nye
        // billede være en måling af en rettelse, brugeren ikke har lavet — og
        // `.ti-fixed`-teksten ville stå under et tal der ikke stammer fra den.
        // Samme nulstilling som farvefeltet og `fontsize` gør, og af samme
        // grund: en beskrivelse af kernens egen indgreb må aldrig overleve det
        // input den beskriver.
        scrim = null;
        lastFix = null;
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
    // Egen farvevalg = bruterens beslutning. Kernels rettelse gælder kun
    // indtil da, så en beskrivelse af den skal ikke blive stående under et tal
    // der ikke længere stammer fra den.
    $('fg').addEventListener('input', function () { lastFix = null; scrim = null; updateAll(); });
    $('fontsize').addEventListener('change', function () { lastFix = null; scrim = null; updateAll(); });
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
    // kode i en sandkasse i stedet for at tro på markup. `suggestFix` er med,
    // fordi rettelsens *matematik* skal kunne dømmes uden en browser: et tal
    // påstanden ikke kan efterprøve på er en påstand.
    return { sampleContrast: sampleContrast, updateAll: updateAll, applyFix: applyFix, suggestFix: suggestFix };
  }

  global.TiContrast = { mount: mount, lum: lum, ratio: ratio, hexToRgb: hexToRgb,
                      lumToChannel: lumToChannel, suggestFix: suggestFix };
})(typeof globalThis !== 'undefined' ? globalThis : this);