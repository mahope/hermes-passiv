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
    // **To tekstblokke.** Den anden er den mest almindelige reelle case — en
    // designér med to overlejrende tekster på ét foto får i dag kun tallet for
    // den *sidste*, og det er det tal han så stoler på. Blok 2 findes kun når
    // siden har givet den egne felter (`#text2`/`#fg2`), så de sider der ikke
    // har dem, kører præcis som før: én blok, ét tal, én måling.
    var t2 = { x: 0, y: 0, scrim: null, lastFix: null };
    // Hvilken blok et klik på billedet flytter. Der er præcis én cursor, og
    // bruteren skal kunne se hvilken blok den griber — derfor tegner `draw()`
    // en stiplet ramme om den aktive.
    var aktiv = 0;

    // Én tekstbloks tilstand læses gennem disse, så al resten af kernen er
    // skrevet ét sted for to blokke i stedet for to gange. Blok 0 er den
    // værktøjet altid har haft, så dens felter er de oprindelige id'er.
    function txtFelt(i) { return $(i ? 'text2' : 'text'); }
    function farveFelt(i) { return $(i ? 'fg2' : 'fg'); }
    function laegX(i) { return i ? t2.x : tx; }
    function laegY(i) { return i ? t2.y : ty; }
    function laegScrim(i) { return i ? t2.scrim : scrim; }
    function laegFix(i) { return i ? t2.lastFix : lastFix; }
    function saetX(i, v) { if (i) { t2.x = v; } else { tx = v; } }
    function saetY(i, v) { if (i) { t2.y = v; } else { ty = v; } }
    function saetScrim(i, v) { if (i) { t2.scrim = v; } else { scrim = v; } }
    function saetFix(i, v) { if (i) { t2.lastFix = v; } else { lastFix = v; } }
    // Blok 2 tæller kun, når siden faktisk har givet den felter — ellers ville
    // kernen tegne en tekst, bruteren ikke kan se eller ændre, og måle den.
    function blok2Findes() { return !!(txtFelt(1) && farveFelt(1)); }
    function blokAntal() { return blok2Findes() ? 2 : 1; }
    // Aktivér en blok og mål igen, så stregen på billedet og tallet på skærmen
    // altid beskriver den samme blok.
    function aktivere(i) {
      aktiv = i;
      updateAll();
    }
    // Sandt når bruteren ikke har valgt en baggrund, og det vi viser er det
    // eksempel kernen selv tegner. Uden denne tilstand står et *målt tal* under
    // et billede læseren aldrig har set — og «målt mod de lyseste og mørkeste
    // billedpixels under dine bogstaver» er så en påstand om deres egen fil.
    // Derfor nulstilles den i `loadFile()` og i `vaerlGradient()` lige så vel
    // som `scrim`/`lastFix`: en ny baggrund er et nyt spørgsmål, også for den
    // her oplysning.
    var demoBillede = true;
    // Den sidste *opladede* fil, så bruteren kan gå tilbage til den efter at
    // have valgt en gradient. Uden denne ville skiftet være destruktivt: en
    // bruger der prøver en gradient og gider tilbage ville have mistet sit foto.
    var filBillede = null;
    // Den *skalerede* størrelse af den sidste upload. `img.width` er ikke en
    // egenskab ved et `HTMLImageElement` — det har `naturalWidth` — så uden
    // disse to ville skiftet tilbage til fotoet sætte canvas til 0×0, og
    // `textBox()` ville returnere null og værktøjet ville stå tomt.
    var filBredde = 0, filHoejde = 0;

    // ------------------------------------------------------------ baggrund
    // En CSS-gradient er det andet bruteren har stående under sin overskrift,
    // og den var umulig at måle: værktøjet kendte kun `img`, og en gradient kan
    // ikke uploades. Derfor males den ind i et canvas og lægges i præcis den
    // **samme** `img`-plads — så `draw()`, `sampleContrast()`, `findSpot()` og
    // `downloadPng()` røres ikke en linje, og «tekst på en mørk baggrund»
    // måles af den samme kode som et foto. To ruter ind i *én* måling, ikke to
    // måleveje der kan komme i ukig: det er hele fordelen ved at male
    // gradienten ind i stedet for at skrive en målevej ved siden af.
    //
    // Felterne er valgfrie, så de to artikler der kun har et billede kører
    // præcis som før — samme idiom som `blok2Findes()`.
    var GRAD_BREDDE = 900, GRAD_HOEJDE = 420;
    function gradientFindes() {
      return !!($('bgmode') && $('gfrom') && $('gto'));
    }
    function gradientAktiv() {
      return gradientFindes() && $('bgmode').value === 'gradient';
    }
    // CSS-vinklen: 0° peger opad og tæller med uret, så
    // `linear-gradient(180deg, …)` i et stylesheet er præcis det bruteren har
    // skrevet. Retningen *regnes*, den er ikke antaget — og det er derfor den
    // er et løfte porten kan dømme: en mutation der bytter om på fortegnet maler
    // gradienten modsat, og «0°» og «180°» bytter da plads.
    function malGradient() {
      var c = global.document.createElement('canvas');
      c.width = GRAD_BREDDE; c.height = GRAD_HOEJDE;
      var g = c.getContext('2d');
      var rawn = $('gang') ? Number($('gang').value) : 0;
      var rad = (isFinite(rawn) ? rawn : 0) * Math.PI / 180;
      var dx = Math.sin(rad), dy = -Math.cos(rad);
      // Halv længden af den længste projicerede side, så gradienten dækker
      // hele fladen i *enhver* vinkel — ellers ville 45° kun male et bånd
      // igennem midten og resten stå som den sidste stops farve.
      var L = (Math.abs(GRAD_BREDDE * dx) + Math.abs(GRAD_HOEJDE * dy)) / 2;
      var cx = GRAD_BREDDE / 2, cy = GRAD_HOEJDE / 2;
      var grad = g.createLinearGradient(cx - dx * L, cy - dy * L, cx + dx * L, cy + dy * L);
      grad.addColorStop(0, $('gfrom').value);
      grad.addColorStop(1, $('gto').value);
      g.fillStyle = grad;
      g.fillRect(0, 0, GRAD_BREDDE, GRAD_HOEJDE);
      return c;
    }
    // Nulstillingen der hører til *enhver* ny baggrund. Den lå før spredt i to
    // steder (`loadFile()` og demoen); med gradienten er der tre veje ind, og
    // en beskrivelse af kernens egen indgreb må aldrig overleve det input den
    // beskriver — hverken sløret, `lastFix` eller demo-noten.
    function baggrundNul() {
      scrim = null;
      lastFix = null;
      t2.scrim = null;
      t2.lastFix = null;
    }
    // Baggrunden bliver gradienten. Den er bruterens *egen* baggrund, så
    // demo-noten væk: den siger «eksempel, ikke dit», og det er ikke længere
    // rigtigt — han har valgt farverne selv.
    function vaerlGradient() {
      img = malGradient();
      cv.width = GRAD_BREDDE; cv.height = GRAD_HOEJDE;
      // Samme pladsering som demoen, fordi en gradient *er* demoens
      // baggrund gjort redigerbar — bruteren skal se den samme scene.
      tx = Math.round(cv.width * 0.06); ty = Math.round(cv.height * 0.52);
      t2.x = Math.round(cv.width * 0.06); t2.y = Math.round(cv.height * 0.80);
      baggrundNul();
      demoBillede = false;
      var felt = $('tigrad');
      if (felt) felt.style.display = '';
      updateAll();
    }
    // Tilbage til fotoet: den sidste upload hvis der var en, ellers demoen.
    // Ikke-destruktivt, fordi det er præcis den bevægelse bruteren har lavet to
    // gange (gradient → gradient → foto) i sit eget hoved.
    function vaerlBillede() {
      img = filBillede || baggrundDemo();
      demoBillede = !filBillede;
      cv.width = filBillede ? filBredde : GRAD_BREDDE;
      cv.height = filBillede ? filHoejde : GRAD_HOEJDE;
      baggrundNul();
      // Blokke placeres i folden igen, så en tekst der lå midt i en 900×420
      // gradient ikke bliver hængende halvt uden for det foto der kommer
      // tilbage — `textBox()` klipper den, og bruteren ville se en tekst der
      // var klippet i stedet for den han havde lagt.
      tx = Math.round(cv.width * 0.06); ty = Math.round(cv.height * 0.70);
      t2.x = Math.round(cv.width * 0.06); t2.y = Math.round(cv.height * 0.86);
      var felt = $('tigrad');
      if (felt) felt.style.display = 'none';
      updateAll();
    }
    function baggrundDemo() {
      var demo = global.document.createElement('canvas');
      demo.width = GRAD_BREDDE; demo.height = GRAD_HOEJDE;
      var dctx = demo.getContext('2d');
      var grad = dctx.createLinearGradient(0, 0, GRAD_BREDDE, GRAD_HOEJDE);
      grad.addColorStop(0, '#1e3a5f'); grad.addColorStop(0.55, '#4a7ba6'); grad.addColorStop(1, '#c9d8e4');
      dctx.fillStyle = grad; dctx.fillRect(0, 0, GRAD_BREDDE, GRAD_HOEJDE);
      dctx.fillStyle = 'rgba(255,255,255,0.35)';
      dctx.beginPath(); dctx.arc(650, 130, 90, 0, Math.PI * 2); dctx.fill();
      return demo;
    }

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
    // Billedet, og så *alle* blokke oveni det i rækkefølge. Sløret tegnes på
    // *canvas*, ikke kun i regningen — ellers ville værktøjet vise et bedre tal
    // end det læseren kan se, og det er den værste slags løfte: et tal der kun
    // er rigtigt i koden. Blok 2 tegnes oveni blok 1, så en tekst der lapper
    // over den anden ser ud som den gør i designværktøjet.
    function draw() {
      if (!img) return;
      ctx.drawImage(img, 0, 0, cv.width, cv.height);
      var n = blokAntal();
      for (var i = 0; i < n; i++) {
        if (laegScrim(i)) drawScrim(i);
        applyFont();
        ctx.fillStyle = farveFelt(i).value;
        ctx.fillText(txtFelt(i).value || ' ', laegX(i), laegY(i));
      }
      drawActive();
    }
    // Sløret dækker præcis den boks, teksten står i — og lidt uden om, så
    // kanten af sløret ikke ligger i bogstavernes egen baggrund, hvor en
    // læser ville se en skarp stribe.
    function drawScrim(i) {
      var s = laegScrim(i);
      var box = textBox(i);
      if (!box || !s) return;
      var pad = Math.round(fontSizePx() * 0.35);
      ctx.save();
      ctx.fillStyle = s.hex + Math.round(s.alpha * 255).toString(16).padStart(2, '0');
      ctx.fillRect(Math.max(0, box.x - pad), Math.max(0, box.y - pad),
                   Math.min(cv.width, box.w + pad * 2), Math.min(cv.height, box.h + pad * 2));
      ctx.restore();
    }
    // Stiplet ramme om den blok et klik vil flytte. Uden den er der to tekster
    // og ingen anelse om hvilken man trækker — så bruteren ville måle den ene og
    // flytte den anden og tro at værktøjet er i ulave.
    function drawActive() {
      if (blokAntal() < 2) return;
      var box = textBox(aktiv);
      if (!box) return;
      var pad = Math.round(fontSizePx() * 0.22);
      ctx.save();
      ctx.strokeStyle = s.activeRing || 'rgba(255,255,255,.85)';
      ctx.lineWidth = 2;
      ctx.setLineDash([6, 5]);
      ctx.strokeRect(Math.max(1, box.x - pad), Math.max(1, box.y - pad),
                     Math.min(cv.width - 2, box.w + pad * 2), Math.min(cv.height - 2, box.h + pad * 2));
      ctx.restore();
    }
    // The letters of *one* block on a cleared canvas. Alpha is then exactly how
    // much of each pixel the glyph covers, which is the one thing a colour
    // distance can never tell you. Only this block's letters are drawn: the
    // other block is not part of the background being measured here, and
    // drawing it would put its glyphs into the alpha mask and delete real
    // background pixels from under this one.
    function drawTextLayer(i) {
      ctx.clearRect(0, 0, cv.width, cv.height);
      applyFont();
      ctx.fillStyle = farveFelt(i).value;
      ctx.fillText(txtFelt(i).value || ' ', laegX(i), laegY(i));
    }

    // The box is clipped to the canvas, never nudged back inside it:
    // getImageData() outside the canvas returns transparent black, which
    // reads as a black background and invents contrast that is not there.
    function textWidth(i) {
      applyFont();
      return Math.max(2, Math.ceil(ctx.measureText(txtFelt(i).value || '').width));
    }
    function textBox(i) {
      applyFont();
      var x = Math.max(0, Math.round(laegX(i))), y = Math.max(0, Math.round(laegY(i)));
      var w = Math.min(textWidth(i), cv.width - x);
      var h = Math.min(fontSizePx(), cv.height - y);
      if (w < 2 || h < 2) return null;
      return { x: x, y: y, w: w, h: h };
    }

    // Målingen for én blok. Samme to pass og samme kloge som før — de er
    // flyttet fra den ene tekst til *en* tekst, så formlen og portens tal er
    // uændrede, og blok 2 måles af præcis den samme kode.
    function sampleContrast(i) {
      if (!img) return null;
      var box = textBox(i);
      if (!box) return null;
      // Pass 1 — the photo alone, read back as the background.
      ctx.clearRect(0, 0, cv.width, cv.height);
      ctx.drawImage(img, 0, 0, cv.width, cv.height);
      var photo = ctx.getImageData(box.x, box.y, box.w, box.h).data;
      // Pass 2 — the letters alone, so alpha is the glyph coverage.
      drawTextLayer(i);
      var glyph = ctx.getImageData(box.x, box.y, box.w, box.h).data;

      var bgCandidates = [], bgOff = [];
      // Sløjfevariablen hedder `p` og ikke `i`: `i` er *blokkens* nummer her,
      // og en pixel-tæller der overskriver den ville læse blok 2's felter under
      // blok 0's måling — to tekstblokke, to tal, og porten ville dømme det
      // falske tal. Samme navn bruges i `drawTextLayer()`.
      for (var p = 0; p < photo.length; p += 4) {
        if (glyph[p + 3] > COVER_MAX) continue; // this pixel is a letter
        bgCandidates.push([photo[p], photo[p + 1], photo[p + 2]]);
        // Byte-offsetet i boksen ved siden af farven. Uden det vidste dommen
        // *hvilken* baggrund der var værst, men ikke hvor den sad — og et tal
        // uden en plads er præcis det værktøjet allerede gav.
        bgOff.push(p);
      }
      // Every pixel under the box is more than a letter thick, so there is no
      // visible background left to read. Fall back to the photo under the box
      // rather than reporting no number at all.
      if (!bgCandidates.length) {
        for (var j = 0; j < photo.length; j += 4) {
          bgCandidates.push([photo[j], photo[j + 1], photo[j + 2]]);
          bgOff.push(j);
        }
      }
      // Worst case: the foreground against the lightest and the darkest
      // background pixel a reader can actually see behind the letters.
      var minL = Infinity, maxL = -Infinity, minC = null, maxC = null;
      var minOff = -1, maxOff = -1;
      bgCandidates.forEach(function (c, k) {
        var L = lum(c);
        if (L < minL) { minL = L; minC = c; minOff = bgOff[k]; }
        if (L > maxL) { maxL = L; maxC = c; maxOff = bgOff[k]; }
      });
      // Sløret er en del af det bruteren ser, så det er en del af det der
      // måles. Pass 1 tegner kun billedet, så blandingen laves her — på præcis
      // den måde `drawScrim()` maler den, med samme farve og samme dækning.
      // Uden dette viste værktøjet et bedre tal end det læseren kan se, fordi
      // dommen ville regne på det rå billede mens sløret lå tegnet oveni.
      var visMin = effectiveBg(minC, i), visMax = effectiveBg(maxC, i);
      var fgRgb = hexToRgb(farveFelt(i).value);
      var worst = Infinity, worstOff = minOff;
      // `k === 0` er `visMin` og `k === 1` er `visMax`, så den baggrund der
      // *afgør* tallet kan følges tilbage til den pixel den kom fra. Det er
      // den plads, feltet i den hentede fil tegnes omkring.
      [visMin, visMax].forEach(function (c, k) {
        if (!c) return;
        var r = ratio(fgRgb, c);
        if (r < worst) { worst = r; worstOff = k === 0 ? minOff : maxOff; }
      });
      // Offsetet er i boksen, og boksen kan ligge et sted inde i billedet — så
      // pladsen regnes om til canvas-koordinater. Uden denne `+ box.x` ville
      // feltet blive tegnet i billedets øverste venstre hjørne.
      var punkt = null;
      if (worstOff >= 0) {
        punkt = { x: box.x + (worstOff % box.w), y: box.y + Math.floor(worstOff / box.w) };
      }
      // Endepunkterne gives videre som *rå* billedpixels, uden slør. Pass 1
      // tegner kun billedet, så de er uafhængige af hvad der ligger oveni —
      // og det er dem `suggestFix()` så danner sin *effektive* baggrund af, så
      // dens svar afhænger af det der faktisk er tegnet lige nu.
      return { ratio: worst === Infinity ? null : worst, bgMin: minC, bgMax: maxC, punkt: punkt };
    }

    // Hvor fejlen sidder, tegnet som et felt i den hentede fil. Et tal på
    // 1,10:1 siger at noget er galt, men ikke hvor — og «hvor» er præcis det
    // et bureau der gennemgår en kundes fotos har brug for, når det skal give
    // designeren besked uden at åbne værktøjet igen.
    //
    // Fire **fyldte** rektangler og ikke ét `strokeRect()`. En strege er to
    // pixels bred og forsvinder i en komprimeret PNG, og den er usynlig for
    // enhver port der læser den hentede fil — altså ville «feltet er med i
    // filen» være en løfte uden dom. Fyldt er den målbar og synlig. Samme røde
    // som FAIL-badge'en ovenfor, så feltet og dommen er én familie.
    function drawMark(punkt) {
      if (!punkt) return false;
      var pad = Math.max(6, Math.round(fontSizePx() * 0.45));
      var tyk = Math.max(2, Math.round(fontSizePx() * 0.14));
      var x0 = Math.max(0, punkt.x - pad), y0 = Math.max(0, punkt.y - pad);
      var x1 = Math.min(cv.width, punkt.x + pad + 1), y1 = Math.min(cv.height, punkt.y + pad + 1);
      var w = x1 - x0, h = y1 - y0;
      // Et felt der er smallere end sin egen tykkelse ville være en ubrugelig
      // streg, så da tegnes intet — og bruteren får billedet rent.
      if (w < tyk * 2 || h < tyk * 2) return false;
      ctx.save();
      ctx.fillStyle = '#dc2626';
      ctx.fillRect(x0, y0, w, tyk);
      ctx.fillRect(x0, y1 - tyk, w, tyk);
      ctx.fillRect(x0, y0, tyk, h);
      ctx.fillRect(x1 - tyk, y0, tyk, h);
      ctx.restore();
      return true;
    }

    // Det bruteren ser bag bogstaverne: billedet, og sløret oveni hvis der er
    // ét. Denne blanding er både det `drawScrim()` maler og det tallet bliver
    // regnet på — de to kan derfor ikke komme i ukig.
    function effectiveBg(c, i) {
      if (!c) return null;
      return laegScrim(i) ? over(c, laegScrim(i).hex, laegScrim(i).alpha) : c;
    }

    // Den ene knap, der manglede: «Fix it». Den sætter enten tekstfarven eller
    // sløret til det, der passerer, og lader så `updateAll()` genmåle — så det
    // der vises bagefter er en *ny måling* af det samme billede, ikke et løfte
    // om at et bedre tal ville komme.
    function applyFix(i, fix, foer) {
      if (!fix) return false;
      // `foer` er tallet `updateResult()` **lige målte** og skrev på skærmen —
      // ikke en ny måling her. Det er den ene værdi der er rigtig: bruteren
      // trykkede på et tal, og «før» skal være præcis det tal. En måling for
      // anden gang ville være en anden værdi, hvis bare canvas imellem de to
      // kald er blevet ryddet — `sampleContrast()` efterlader den præcis sådan,
      // med bogstaverne på en tom flade.
      saetFix(i, fix);
      fix.before = typeof foer === 'number' ? foer : null;
      if (fix.kind === 'scrim') {
        saetScrim(i, { hex: fix.scrim, alpha: fix.alpha });
        farveFelt(i).value = fix.hex;
      } else {
        saetScrim(i, null);
        farveFelt(i).value = fix.hex;
      }
      updateAll();
      return true;
    }

    // Hvor teksten læses bedst. Et foto kan bestå under den ene halvdel af
    // bogstaverne og fejle under den anden, så det ærlige svar på «kan min
    // overskrift ligge her?» er et *sted* og ikke ét tal ét sted — og det er
    // langsomst at finde ved at trække rundt med musen. Hvert sted måles med
    // `sampleContrast()`, altså præcis den måling tallet på skærmen kommer fra,
    // så det værktøjet flytter teksten til, er et sted hvor *dette* tal gælder.
    //
    // To ting er bevidste: bruterens egen pladsering vinder på *ulige* målinger,
    // så der er ingen grund til at rykke en tekst der allerede står bedst, og
    // alle prober ligger helt inde i billedet — `textBox()` klipper en kasse
    // der går ud over kanten, og så ville dommen måle en tekst der ikke er den
    // bruteren ser.
    function findSpot(i) {
      if (!img) return null;
      var w = textWidth(i), h = fontSizePx();
      var maxX = Math.max(0, cv.width - w), maxY = Math.max(0, cv.height - h);
      if (maxX < 1 || maxY < 1) return null;
      // Hvor teksten *lå* da knappen blev tryktk. Uden denne var `rykket`
      // altid falsk: `bx`/`by` er prober inden i billedet, så de kan ikke
      // fortælle om de er flyttet — og kernen skrev «det er allerede det bedste
      // sted» under et billede den selv lige havde flyttet teksten på.
      var startX = laegX(i), startY = laegY(i);
      var bx = startX, by = startY;
      var bedst = sampleContrast(i);
      var best = bedst && bedst.ratio !== null ? bedst.ratio : -1;
      var cols = 5, rows = 4, c, r, x, y, s, v;
      for (r = 0; r < rows; r++) {
        for (c = 0; c < cols; c++) {
          x = Math.round(maxX * c / (cols - 1));
          y = Math.round(maxY * r / (rows - 1));
          saetX(i, x); saetY(i, y);
          s = sampleContrast(i);
          v = s && s.ratio !== null ? s.ratio : -1;
          if (v > best) { best = v; bx = x; by = y; }
        }
      }
      saetX(i, Math.max(0, Math.min(bx, maxX)));
      saetY(i, Math.max(0, Math.min(by, maxY)));
      if (best < 0) return null;
      return { x: laegX(i), y: laegY(i), ratio: best, rykket: laegX(i) !== startX || laegY(i) !== startY };
    }

    // Marker koden i sig selv, så bruteren kan kopiere den med Ctrl+C. Det er
    // vejen for de browsere der nægter skriveadgang til udklipsholderen, og
    // derfor skal den *kun* bruges når kopieringen faktisk mislykkedes — ellers
    // ville den fjerne den markering læseren netop har bedt om.
    function markText(el) {
      if (!el || !window.getSelection || !document.createRange) return;
      try {
        var rg = document.createRange();
        rg.selectNodeContents(el);
        var sel = window.getSelection();
        sel.removeAllRanges();
        sel.addRange(rg);
      } catch (e) { /* en browser der ikke kan markere er ikke en fejl i værktøjet */ }
    }

    // Hvad kernen gjorde, i læserens sprog. `scrimPct` og `hex` er tal og
    // farver fra kernens egen måling — aldrig noget en besøgende har skrevet —
    // og hele strengen kommer fra siden, så en dansk læser ikke møder en
    // engelsk beskrivelse af sin egen rettelse.
    function fixBeskrivelse(f) {
      if (f.kind === 'spot') {
        // Samme regel som for sløret: siger kernen at den har flyttet noget,
        // skal den sige *hvorhen* og hvad der blev målt dér. «%s» er kernens
        // egen måling på den nye pladsering.
        return ((f.rykket ? s.movedSpot : s.keptSpot) || '')
          .replace('%s', fmt(f.ratio.toFixed(2)) + ':1');
      }
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

    // Én måling pr. blok, hver i sin egen boks. Blok 0 beholder alt det den
    // altid har haft (resultatboks, download, pro-kort, note); blok 2 får
    // sit eget resultat uden dem — to download-knapper og to pro-kort på én
    // side er to valg, ikke to valg der hjælper. Download er fælles, fordi
    // `downloadPng()` kalder `draw()`, og `draw()` tegner begge blokke.
    // Vælgeren af hvilken blok der flyttes. Den er *knappen* og ikke farve: to
    // blokke kan have samme farve, så farve kan ikke være den eneste måde at
    // vælge på. Den lægger sig derfor i resultatboksen, hvor blokkens eget
    // tal står — så det er tydeligt at den hører til netop den måling.
    function pickBox(i) {
      if (blokAntal() < 2) return '';
      return '<br><button type="button" class="ti-pick" data-ti-pick="' + i + '" aria-pressed="'
        + (aktiv === i ? 'true' : 'false') + '">' + (s.pick || 'Move this text') + '</button>';
    }

    function updateResult() {
      var errEl = $('err');
      if (errEl) errEl.textContent = '';
      var n = blokAntal();
      for (var i = 0; i < n; i++) renderBlock(i);
    }

    function renderBlock(i) {
      var res = $(i ? 'result2' : 'result');
      if (!res) return;
      var sample = sampleContrast(i);
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
      var fix = passAA ? null : suggestFix(effectiveBg(sample.bgMin, i), effectiveBg(sample.bgMax, i), need, farveFelt(i).value);
      res.hidden = false;
      // Klasserne er *ikke* præfikset: de er `ti-*` i `style.css`, og en
      // forekomst på en artikelside skal se identisk ud med værktøjssiden.
      // Præfikset gælder kun id'erne — dem skal to forekomster på samme side
      // kunne have hver sin.
      res.className = 'ti-result ' + (passAA ? 'ti-pass' : 'ti-fail');
      // Før → nu. Kappen ovenfor siger hvad tallet *er*; dette siger hvad det
      // *var*, målt med den samme `sampleContrast()`. Det er det tal en læser
      // skal kunne tage med: uden det er «PASS 3,04:1» en påstand uden
      // bevis, og bruteren ved ikke om rettelsen gjorde forskel.
      //
      // To regler, begge nødvendige for at linjen ikke lyver:
      //   1. kun når der *er* målt før — uden før-tal er der intet at sammenligne
      //      med, og en mangel på `before` betyder at kernen ikke kan svare på
      //      spørgsmålet, ikke at svaret er «0:1 → 3,04:1».
      //   2. kun når tallet faktisk flyttede sig. «3,04:1 før, 3,04:1 nu» er
      //      støjende oplysninger om at tallet er det samme — og det er
      //      præcis tilfældet når «Find det bedste sted» konkluderer at
      //      bruterens egen pladsering allerede var den bedste.
      var minFix = laegFix(i);
      var foerTal = minFix && minFix.before !== null && minFix.before !== undefined
        ? minFix.before : null;
      var delta = '';
      if (foerTal !== null && Math.abs(r - foerTal) > 0.005 && s.delta) {
        var foerTekst = fmt(foerTal.toFixed(2));
        var nuTekst = fmt(r.toFixed(2));
        delta = '<br><span class="ti-delta" data-ti-delta="' + foerTekst + '|' + nuTekst + '">'
          + s.delta.replace('%s', foerTekst).replace('%s', nuTekst) + '</span>';
      }
      // Den målte tekstfarve som en kode bruteren kan tage med. `hexNu` er
      // farvefeltets egen værdi — altså den farve målingen faktisk regnede på,
      // også efter «Fix it», fordi den handler skriver tilbage i feltet. Uden
      // denne linje måtte bruteren finde den valgte farve ved at kigge på
      // farvefeltet og skrive den af i Figma: værktøjet målte, rettede og
      // sagde «#1a1a1a» i en sætning, men gav ingen værdi at kopiere.
      //
      // Det er en `<button>` og ikke et `<span>`, fordi den *gør* noget
      // (kopierer) — punkt 2 i husets kvalitetsliste. `s.copyHex` er sidens egen
      // tekst fra den side den ligger på, altså ikke noget en besøgende kan
      // skrive, og det er samme behandling resten af `s.*` får her.
      var hexNu = String(farveFelt(i).value || '').toLowerCase();
      // Alt der kommer fra brugeren (`r`) er et tal, ikke markup, og alt
      // `s.*` er sidens egen tekst fra den side den ligger på. Ingenting her
      // bygger en streng af noget en besøgende kan skrive. Knappen bruges
      // `<button type="button">` og ikke et `<a href="#">`, fordi den gør
      // noget ved siden — ikke en ny side — og en anchor ville blive
      // genindlæst i historikken ved hvert tryk.
      // Kommer *før* tallet, ikke bagefter: badge'en siger PASS/FAIL, så en
      // læser der kun læser den første linje skal kunne se at tallet stammer
      // fra kernens eget eksempel. `data-ti-demo` er ikke pynt — det er den
      // ene ting porten skal kunne dømme, fordi en note der ikke kan slås fra
      // er lige så død som ingen note.
      res.innerHTML =
        (demoBillede && s.demoNote ? '<span class="ti-demo" data-ti-demo>' + s.demoNote + '</span><br>' : '') +
        '<span class="ti-badge" style="background:' + (passAA ? '#16a34a' : '#dc2626') + '">' +
        (passAA ? s.pass : s.fail) + '</span>&nbsp; <strong>' + fmt(r.toFixed(2)) + ':1</strong> ' +
        (s.worstCase || '') + ' ' + (s.needs || '') + ' ' + fmt(need) + ':1 ' + (s.forAA || '') + ' ' +
        (large ? (s.largeText || '') : (s.normalText || '')) +
        (passAA && !passAAA ? '<br>' + (s.aaNotAAA || '') + ' (' + fmt(aaaNeed) + ':1).' :
         passAAA ? '<br>' + (s.alsoAAA || '') :
          '<br>' + (s.tryFix || '')) +
        // Koden ligger lige under tallet og *før* de tre knapper, fordi den
        // er svaret på målingen — de tre er de næste handlinger. Den skriver
        // aldrig en værdi den ikke selv har målt: `hexNu` er farvefeltet.
        (hexNu ? '<br><button type="button" class="ti-hex" data-ti-hex="' + hexNu + '" title="'
          + (s.copyHex || '') + '"><span class="ti-swatch" style="background:' + hexNu
          + '"></span><code>' + hexNu + '</code></button>' : '') +
        (fix && s.fixBtn ? '<br><button type="button" class="btn-secondary ti-fix" data-ti-fix>' + s.fixBtn + '</button>' : '') +
        pickBox(i) +
        // Før → nu står *før* beskrivelsen af hvad kernen gjorde: tallet er
        // beviset, og `.ti-fixed` er så den Grund det står der.
        delta +
        // `data-ti-moved` er ikke pynt: det er den ene ting porten skal kunne
        // dømme om flytningen, fordi *hvilken* sætning kernen vælger afhænger
        // af den. Ordene er sidens egen tekst på to sprog, så de kan ikke være
        // et fastslået tal i porten.
        (minFix ? '<br><span class="ti-fixed" data-ti-moved="' + (minFix.rykket ? '1' : '0') + '">' + fixBeskrivelse(minFix) + '</span>' : '') +
        // Download, pro-kort og note ligger kun på blok 0. De handler om
        // *billedet* og om siden som helhed, ikke om den enkelte tekstblok, og
        // to download-knapper på én skærm er to valg uden opgave. Download er
        // desuden fælles: `draw()` maler begge blokke, så den hentede PNG
        // indeholder dem begge — det er derfor knappen ikke skal gentages.
        (!i && s.downloadBtn ? '<br><button type="button" class="btn-secondary ti-dl" data-ti-dl>' + s.downloadBtn + '</button>' : '') +
        // Et **andet** valg end den rene grafik, ikke en anden etikette på den.
        // Bureauet der gennemgår kundens fotos skal kunne få det dårligste sted
        // udpeget i filen uden selv at åbne værktøjet igen, og den rene fil skal
        // stadig være den rene fil — så den ligger i sit egen knap, ikke i et
        // felt der er slået til og fra oveni den anden.
        (!i && s.markBtn ? '<br><button type="button" class="btn-secondary ti-mark" data-ti-dl-mark title="'
          + (s.markTitle || '') + '">' + s.markBtn + '</button>' : '') +
        // Sidst i rækken: det er den tredje handling i resultatet, og den
        // udfylder de to andre — «Fix it» farver teksten, den her flytter den.
        // Den ligger *uden* for `fix`-betingelsen, fordi den også har en
        // opgave når teksten allerede består: der kan være et bedre sted.
        (s.findSpot ? '<br><button type="button" class="btn-secondary ti-spot" data-ti-spot>' + s.findSpot + '</button>' : '') +
        '<br><span style="font-size:.85rem;color:var(--color-text-muted)">' + (s.measured || '') + '</span>'
        + (!i ? (s.proCard || '') : '') +
        '<br><span style="font-size:13px;color:var(--color-text-muted)">' + (s.note || '') + '</span>';
      // Lytteren bindes på den knap `innerHTML` lige nu skrev, ikke på `res`,
      // så en ny måling der skriver en ny knap ikke efterlader to lyttere på
      // den gamle. `updateAll()` kaldes inde i handleren, som genskriver
      // `innerHTML` — og den her knap forsvinder, fordi den nye måling
      // består, så der ikke kan opstå et uendeligt klik-loop.
      var btn = res.querySelector('[data-ti-fix]');
      // `r` er tallet fra denne måling — det der stod på skærmen da
      // bruteren trykkede. Samme værdi som står i `data-ti-delta`s første
      // halvdel, så de to kan ikke komme i ukig.
      if (btn) btn.addEventListener('click', function () { applyFix(i, fix, r); });
      // Vælgeren binder på sit eget `data-ti-pick`, så en ny måling der
      // genskriver `innerHTML` ikke efterlader to lyttere på den gamle knap.
      var pick = res.querySelector('[data-ti-pick]');
      if (pick) pick.addEventListener('click', function () {
        aktivere(parseInt(pick.getAttribute('data-ti-pick'), 10) || 0);
      });
      var hexBtn = res.querySelector('[data-ti-hex]');
      // Kopien skal lykkes, ellers må knappen ikke sige at den gjorde det. Et
      // nægtet `clipboard`-løfte er et normalt udfald (ingen tilladelse, ikke
      // et https-domæne), så da markerer vi koden i stedet for at lyve — og
      // bruteren kan tage den med Ctrl+C. `isConnected` før tilbagestillingen,
      // fordi `updateAll()` kan have skrevet et nyt resultat imens, og så skal
      // vi ikke røre en knap der ikke længere findes.
      if (hexBtn) hexBtn.addEventListener('click', function () {
        var kode = hexBtn.getAttribute('data-ti-hex');
        var svin = hexBtn.querySelector('code');
        var vis = function (tekst) {
          if (hexBtn.isConnected && svin && svin.isConnected) svin.textContent = tekst;
        };
        var ryd = function () { vis(kode); };
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(kode).then(function () {
            vis(s.copiedHex || 'Copied');
            setTimeout(ryd, 1800);
          }, function () {
            markText(svin);
            vis(s.copyManual || kode);
          });
          return;
        }
        markText(svin);
        vis(s.copyManual || kode);
      });
      var dl = res.querySelector('[data-ti-dl]');
      // `false`/«uden felt» er **eksplicit** på begge knapper. Uden det ville
      // lytteren få klik-begivenheden som sit argument, og den er sand — så
      // den rene download også fik feltet, og de to valg blev ét.
      if (dl) dl.addEventListener('click', function () { downloadPng(false); });
      var dlMark = res.querySelector('[data-ti-dl-mark]');
      if (dlMark) dlMark.addEventListener('click', function () { downloadPng(true); });
      var spot = res.querySelector('[data-ti-spot]');
      if (spot) spot.addEventListener('click', function () {
        // Samme værdi som i `applyFix()`-kaldet: tallet fra denne måling.
        // `findSpot()` flytter `tx`/`ty` undervejs, så måles der efter kaldet
        // står `tx`/`ty` altid ved det bedste sted, og «før» ville være «nu».
        var spot2 = findSpot(i);
        if (!spot2) return;
        // Samme slags som `applyFix()`: beskrivelsen af kernens egen indgreb
        // hører til den pladsering den lagde, så `onMove()` nulstiller den igen
        // så snart bruteren selv rører teksten.
        saetFix(i, { kind: 'spot', ratio: spot2.ratio, rykket: spot2.rykket, before: r });
        updateAll();
      });
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
    // `mark` er et **valg**, ikke en tilfældighed: den rene fil er den
    // rettede grafik, og kun den markerede bæger feltet. Derfor måles feltet
    // på den pladsering og det billede, tallet på skærmen stammer fra — og
    // derfor skal den rene knap ikke få feltet med.
    //
    // Filnavnet er sidens egen streng, aldrig bruterens tekst: et navn bygget på
    // noget en besøgende har skrevet kan indeholde `/`, `..` eller et tegn, der
    // ikke kan bruges i et filnavn.
    function downloadPng(mark) {
      if (!img) return false;
      // Målingen *før* `draw()`: `sampleContrast()` rydder canvasen, så hvis
      // feltet blev tegnet før den, ville det blive malet på en tom flade — og
      // den hentede fil ville være gennemsigtig med en rød ramme i.
      var sample = mark ? sampleContrast(aktiv) : null;
      draw();
      var dataUrl = null;
      try {
        if (sample) drawMark(sample.punkt);
        dataUrl = cv.toDataURL('image/png');
      } catch (e) {
        dataUrl = null;
      }
      // Forhåndsvisningen skal vise billedet *uden* felt bagefter. Bruteren
      // bad om en fil med et felt — ikke om at hans eget billede fik en, og
      // et felt der bliver stående ville ligne en del af hans design.
      draw();
      if (!dataUrl) return false;
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
        filBillede = im;
        // Et nyt billede er et nyt spørgsmål. Sløret var beregnet på *sidste*
        // baggrunds endepunkter, så hvis det blev liggende ville tallet på den
        // nye baggrund være en måling af en rettelse, brugeren ikke har lavet —
        // og `.ti-fixed`-teksten ville stå under et tal der ikke stammer fra den.
        // Samme nulstilling som farvefeltet og `fontsize` gør, og af samme
        // grund: en beskrivelse af kernens egen indgreb må aldrig overleve det
        // input den beskriver. `demoBillede` hører i samme række: «dette er et
        // eksempel» er kun sandt, indtil der er en baggrund der er bruterens —
        // ellers kalder værktøjet deres egen foto et eksempel.
        baggrundNul();
        demoBillede = false;
        // Vælgeren skal ikke sige «gradient» når der lige kom et foto ind: den
        // skal vise hvad bruteren faktisk ser. Ellers stod der «Gradient» over
        // et foto, hvilket er en påstand om et input der ikke fandtes.
        if (gradientFindes() && gradientAktiv()) {
          $('bgmode').value = 'image';
          // Felterne skjules med, ellers stod de tre farvefelter fremme under
          // et foto — de ville se ud som om de gjorde noget, de ikke gjorde.
          var gemt = $('tigrad');
          if (gemt) gemt.style.display = 'none';
        }
        var maxW = 900;
        var scale = Math.min(1, maxW / im.naturalWidth);
        cv.width = Math.round(im.naturalWidth * scale);
        filBredde = cv.width;
        cv.height = Math.round(im.naturalHeight * scale);
        filHoejde = cv.height;
        tx = Math.round(cv.width * 0.06);
        ty = Math.round(cv.height * 0.70);
        // Blok 2 starter i den nederste linje, så den lapper ikke blok 1 oppe
        // på et nyt billede — to tekster oveni hinanden er svært at læse, og
        // bruteren skal kunne se begge tal uden at flytte noget først.
        t2.x = Math.round(cv.width * 0.06);
        t2.y = Math.round(cv.height * 0.86);
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
      saetX(aktiv, cx * cv.width / rect.width - fontSizePx() / 2);
      saetY(aktiv, cy * cv.height / rect.height - fontSizePx() / 2);
    }
    function onMove(e) {
      if (!img) return;
      e.preventDefault();
      pos(e);
      // Bruteren flyttede teksten selv. En beskrivelse af kernens egen
      // flytning («jeg satte den på det bedste sted») må ikke blive stående
      // under et tal der nu stammer fra en helt anden pladsering — samme
      // grund som farvefeltet og `fontsize` nulstiller den. Kun den blok der
      // faktisk blev flyttet: den anden behøver ikke miste sin beskrivelse,
      // fordi bruteren rørte en anden tekst.
      saetFix(aktiv, null);
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
    // Blok 2 har de samme lyttere på egne felter. `addEventListener` på en
    // felt-stub der ikke findes ville kaste, så de bindes kun når siden faktisk
    // har lagt dem ind — det er også sådan `blok2Findes()` ved det.
    if (blok2Findes()) {
      $('text2').addEventListener('input', updateAll);
      $('fg2').addEventListener('input', function () { t2.lastFix = null; t2.scrim = null; updateAll(); });
    }
    cv.addEventListener('mousedown', function (e) { dragging = true; onMove(e); });
    global.addEventListener('mousemove', function (e) { if (dragging) onMove(e); });
    global.addEventListener('mouseup', function () { dragging = false; });

    // **En finger skal kunne trække teksten, ligesom en mus.** Målt 3/10 i
    // Chromium 153 ved 390 px: `touchstart` flyttede teksten ét sted, og seks
    // `touchmove` ændrede *intet* — så «(eller træk)» i teksten på alle fire
    // sider var sand på en mus og en løgn på en telefon, altså på den enhed de
    // fleste læser artiklen på. Samme måling: `touchstart`'s `preventDefault()`
    // låste scrollen med fingeren oven på billedet, så man heller ikke kunne
    // læse videre som man plejer.
    //
    // Derfor er et tryk et *tryk* og et træk et *træk*, og de må ikke forveksles:
    //   - fingeren ned og op uden at flytte sig → tryk → teksten flyttes derhen,
    //     præcis som 3/10. Bevares, fordi det er den bevægelse de fleste lavør.
    //   - fingeren ned og **vandret** hen over → træk → teksten følger fingeren.
    //     Vandret, fordi et lodret træk er præcis det en læser gør for at komme
    //     videre ned ad siden, og den scroll skal vi ikke tage.
    //   - først når trækket er i gang må fingeren gå hvor som helst: det er den
    //     bevægelse der *startede* det, der afgør hvad resten af gesten er.
    var touchX = 0, touchY = 0, touchMode = '';
    function touchStart(e) {
      if (!img) return;
      var t = e.touches && e.touches[0];
      if (!t) return;
      touchX = t.clientX; touchY = t.clientY; touchMode = '';
      // Bevidst **ikke** `preventDefault()`: så beholder bruteren scrolling med
      // fingeren oven på billedet. Det var den låste 3/10.
    }
    function touchMove(e) {
      if (!img) return;
      var t = e.touches && e.touches[0];
      if (!t) return;
      var dx = t.clientX - touchX, dy = t.clientY - touchY;
      if (!touchMode) {
        // 6 px: lille nok til at en klam finger ikke udløser et træk, stort
        // nok til at en vilje flytter teksten. Efter grænsen afgør den kraftigste
        // retning, og kun *én* gang — ellers ville en skæv finger skifte mening
        // undervejs og tekst flytte mens siden scroller.
        if (Math.abs(dx) < 6 && Math.abs(dy) < 6) return;
        touchMode = Math.abs(dx) >= Math.abs(dy) ? 'drag' : 'scroll';
      }
      if (touchMode !== 'drag') return;
      // Når scrolling først er begyndt, er `touchmove` ikke længere cancellable:
      // browseren ruller videre, og vi ville trække teksten under fingeren
      // *mens* siden flytter sig. Da er vi for sent — giv scrollen fred.
      if (e.cancelable === false) { touchMode = 'scroll'; return; }
      // `onMove()` kalder selv `preventDefault()`, altså det er her et træk
      // fortryder den scroll, vi netop erklærede for vores.
      onMove(e);
    }
    function touchEnd(e) {
      // Et tryk er et finger-op uden at have flyttet sig. Her flytter vi teksten
      // — 3/10 gjorde det i `touchstart`, så en berøring stadig virker som klik.
      // `onMove()` læser `touches[0]`, og et `touchend`s `touches` er *tom*,
      // så vi giver den den finger der slap.
      var t = e.changedTouches && e.changedTouches[0];
      if (!touchMode && t && img) onMove({ clientX: t.clientX, clientY: t.clientY, preventDefault: function () {} });
      touchMode = '';
    }
    cv.addEventListener('touchstart', touchStart, { passive: false });
    cv.addEventListener('touchmove', touchMove, { passive: false });
    cv.addEventListener('touchend', touchEnd, { passive: false });
    // En afbrudt gest (et opkald, en besked, en finger der gik uden for skærmen)
    // må ikke efterlade kernen i et træk der fortsætter uden finger.
    cv.addEventListener('touchcancel', function () { touchMode = ''; }, { passive: false });

    // Default demo background so the tool works before uploading anything.
    img = baggrundDemo();
    cv.width = GRAD_BREDDE; cv.height = GRAD_HOEJDE;
    tx = Math.round(cv.width * 0.06); ty = Math.round(cv.height * 0.52);
    t2.x = Math.round(cv.width * 0.06); t2.y = Math.round(cv.height * 0.80);
    updateAll();

    // Baggrunden: foto eller gradient. Vælgeren er et `<select>` og **ikke** en
    // knap, fordi `check_first_action` dømmer knapper i folden — et nyt værktøj
    // skal komme med ét klik, ikke to. Gradient-felterne er skjult indtil de
    // bruges, så bruteren ikke læser tre felter der intet gør.
    if (gradientFindes()) {
      var tigrad = $('tigrad');
      if (tigrad) tigrad.style.display = 'none';
      $('bgmode').addEventListener('change', function () {
        if (gradientAktiv()) vaerlGradient(); else vaerlBillede();
      });
      $('gfrom').addEventListener('input', vaerlGradient);
      $('gto').addEventListener('input', vaerlGradient);
      if ($('gang')) $('gang').addEventListener('input', vaerlGradient);
    }

    // Synlig for testene i `tests/scan-clients.test.mjs`, der dømmer den her
    // kode i en sandkasse i stedet for at tro på markup. `suggestFix` er med,
    // fordi rettelsens *matematik* skal kunne dømmes uden en browser: et tal
    // påstanden ikke kan efterprøve på er en påstand.
    return { sampleContrast: sampleContrast, updateAll: updateAll, applyFix: applyFix, suggestFix: suggestFix, findSpot: findSpot,
      blokAntal: blokAntal, aktivere: aktivere, blok: function (i) { return { x: laegX(i), y: laegY(i), hex: farveFelt(i).value, text: txtFelt(i).value }; },
      aktiv: function () { return aktiv; } };
  }

  global.TiContrast = { mount: mount, lum: lum, ratio: ratio, hexToRgb: hexToRgb,
                      lumToChannel: lumToChannel, suggestFix: suggestFix };
})(typeof globalThis !== 'undefined' ? globalThis : this);