#!/usr/bin/env python3
"""Dom at `/text-on-image-checker` måler baggrunden under teksten rigtigt.

Målt 30/9 i Chromium mod den **live** side, med et rent hvidt 400×300-billede
og hvid tekst: værktøjet svarede **1.47:1**, og tallet flyttede sig næsten ikke
mellem helt forskellige tilstande (1.42 / 1.46 / 1.47) — sort tekst på hvid
gav 1.46, hvid på sort 1.44. Det fulgte hverken billedet eller tekstfarven, kun
fontstørrelsen, fordi den afhænger af billedets bredde.

Årsagen er strukturel, ikke et regnestykke. `lum()` og `ratio()` var korrekte
WCAG-formler hele vejen; det var *hvilke* pixels der blev læst. Den gamle
`sampleContrast()` malede billedet **og** teksten på samme canvas og læste så
`getImageData` i tekstens bounding box, idet den kasserede alt hvad der lå
inden for `dr+dg+db < 120` af tekstfarven. Men en anti-aliaset glyfkant med 16 %
dækning scorer allerede 126, så kantpixelerne overlevede filteret — og værktøjet
målte teksten mod sin egen grå frimængse. Hvid tekst på hvid gav desuden *intet
resultat*, fordi så bliver alle pixels filtreret væk og `worst` forblev uendelig.

Rettelsen er at male i to adskilte lag: ét pass med kun fotografiet, der læses
som baggrund, og ét pass med kun bogstaverne, hvor alpha er den præcise
dækning pr. pixel. Det er den eneste måde at skelne en bogstav fra et
billedpixel på — en farveafstand kan aldrig det, fordi kanten *er* en blanding.

Samme fejlform er fundet i denne portfamilie tre gange (lejettagtelt, wom,
mahope.tools url-inspect): **et løfte uden dom**. Derfor dømmer den her det tal
læseren ser, kørt mod billeder med kendte farver, og `--self-test` smutter fire
mutationer ind i koden for at bevise at porten bliver rød på hver af dem.

Porten kører **uden browser**: sidenes egen IIFE indlejres i en Node-fil med en
canvas-stub der implementerer source-over-kompositing, nearest-neighbour
skalering og det gennemsigtige sorte `getImageData` uden for canvas'en. Der er
ingen fontmotor, så `fillText()` tegner syntetiske, *antialiasede* glyfer — som
er præcis den situation den gamle kode fejlede i. Det er den kode der faktisk
ships, ikke en kopi af den.

    python3 tools/check_contrast_sampling.py            # dom begge sider
    python3 tools/check_contrast_sampling.py --list     # kun antal løfter
    python3 tools/check_contrast_sampling.py --self-test # 11 kontroller
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
SIDER = ("text-on-image-checker.html", "text-on-image-checker-da.html")
# De to artikler der indlejrer samme værktøj. De males ikke af `dom()` — de
# kører kernen med andre billeder og deres egne tekster — men de bærer de
# *samme* strenge, så en rettelse på værktøjssiden uden tilsvarende på
# artiklen er den fejl der læseren møder som en dansk læser.
ARTIKLER = ("blog/text-on-image-contrast-check.html",
            "da/blog/tekst-paa-billede-kontrasttjek.html")

# Tallene er WCAG 2.1's egne: L = 0.2126R + 0.7152G + 0.0722B over
# lineærliserede kanaler, og forholdet er (Llight + 0.05) / (Ldark + 0.05).
# De er slået op, ikke regnet ud fra koden — ellers ville porten bare
# gentage den fejl den er sat op for at finde.
#   (side, billedfarve, tekstfarve, forventet forhold)
FARVEPAR = (
    ("hvid tekst på hvidt billede", "#ffffff", "#ffffff", 1.00),
    ("sort tekst på hvidt billede", "#ffffff", "#000000", 21.00),
    ("hvid tekst på sort billede", "#000000", "#ffffff", 21.00),
    ("#767676 på hvid (AA-grænsen)", "#ffffff", "#767676", 4.54),
    ("#949494 på hvid (AAA for stor)", "#ffffff", "#949494", 3.03),
    ("hvid på rødt", "#ff0000", "#ffffff", 4.00),
    ("#1a1a1a på sort (næsten usynligt)", "#000000", "#1a1a1a", 1.21),
)
# 400×40 er bevidst fladere end fontstørselen kan blive (6 % af 400 = 24 px),
# så tekstkassen rammer billedets nederste kant. Kun de nederste 10 rækker er
# sorte. Her må værktøjet *klippe* kassen og ikke flytte den opad, og det er
# målt med to forventede tal: 21:1 fordi boksen kun rører de sorte rækker, 1:1
# hvis den derimod løber op i de hvide.
FLADT = ("tekst der rækker til nederste kant", 400, 40, 42, 21.00)
# Et todelt billede er det eneste hvor mutationerne bliver synlige: på et
# ensfarvet billede er det ligegyldigt, om laget målt på også indeholder
# bogstaverne, fordi baggrunden overalt er den samme farve. Her er den ene
# halvdel sort og den anden hvid, så både *at tekstfarven følger billedet* og
# *at laget er rent* bliver dømt af tal læseren kan se forveksle.
TODELT = (
    ("hvid tekst over den mørke halvdel", 400, 300, 100, "#ffffff", 21.00),
    ("hvid tekst over den lyse halvdel", 400, 300, 300, "#ffffff", 1.00),
)
# Et gradientbillede er det eneste sted hvor *bedste* og *dårligste*
# baggrund kan ligge i den samme tekstkasse, og derfor det eneste sted
# hvor porten kan se forskel på dem. På de ensfarvede og todelte billeder
# er det umærkeligt: med hvid tekst er den *lyseste* baggrund altid den
# dårligste, så at springe den mørkeste over ændrer intet. Med sort tekst
# bytter roller de om — da er den mørkeste den dårligste — og mutationen
# springer præcis den over. Det er fejlen: værktøjet svarer på det bedste
# sted under bogstaverne og siger PASS oveni en læsbarhedsfejl.
#   (navn, bredde, højde, x, y, tekstfarve, forventet)
GRADIENT = ("sort tekst over et hvidt-til-sort gradient", 400, 300, 0, 200, "#000000", 1.00)
# Teksten skal være lang nok til at kassen dækker de flade ender i
# gradienten. 39 tegn * 0,52 * 24 px = 487, klippet til billedets 400,
# så kassen dækker hele bredden og begge ender ligger i den.
GRADIENT_TEKST = "Sort tekst hen over et gradientbillede"
TOLERANS = 0.02

# --------------------------------------------------------------------------
# Udtrækningen. WCAG-formlen ligger i `site/text-on-image-core.js` siden 2/10 —
# fire sider bruger den, og fire kopier er fire steder hvor en rettelse kan
# glemmes. Porten læser derfor *kernen* plus sidens eget `mount()`-kald, som er
# den kode der faktisk ships. En side der definerer `sampleContrast` selv er
# en fejl, ikke en fejl-fravær: så ville porten dømme kernen mens læseren
# kørte kopien.
# --------------------------------------------------------------------------
IIFE_RE = re.compile(
    # `(?:/\*.*?\*/\s*)*` springer en *ledende* kommentar over — mount()-kallet
    # har en. Det gøres her og ikke med en global kommentar-stripper, fordi den
    # slugte `accept="image/*"` i markup'en og slugte dermed hele mount()-blokken
    # med, da næste `*/` lå i kommentaren.
    r"<script(?![^>]*\bsrc=)[^>]*>\s*(?:/\*.*?\*/\s*)*(\(function\s*\(\)\s*\{.*?\}\)\(\);)\s*</script>",
    re.S | re.I,
)
KERNE = SITE / "text-on-image-core.js"


def hent_kode(fil: str) -> str:
    """Kernen + sidens egen `mount()`-kald, eller en fejl der siger hvorfor ikke."""
    if not KERNE.is_file():
        raise SystemExit(
            f"FEJL: {KERNE.name} mangler. Uden den har de fire sider der bruger "
            "tjekkeren ingen sampling-kode at dømme.")
    kerne = KERNE.read_text(encoding="utf-8")
    if "function sampleContrast" not in kerne:
        raise SystemExit(
            f"FEJL: {KERNE.name} definerer ikke sampleContrast(). Porten dømmer "
            "formlen; hvis den flytter et andet sted, skal denne pege med.")
    html = (SITE / fil).read_text(encoding="utf-8")
    if re.search(r"function\s+sampleContrast\s*\(", html):
        raise SystemExit(
            f"FEJL: {fil} definerer sin egen sampleContrast() ude i markup'en. "
            "Så dømmer porten kernen, mens læseren kører kopien — to formler, "
            "en dømt.")
    if '/text-on-image-core.js' not in html:
        raise SystemExit(
            f"FEJL: {fil} indlæser ikke /text-on-image-core.js. Uden den kalder "
            "siden mount() på en global der aldrig findes.")
    for m in IIFE_RE.finditer(html):
        if "TiContrast.mount" in m.group(1):
            return kerne + "\n\n" + m.group(1)
    raise SystemExit(
        f"FEJL: {fil} har ingen inline-<script> der kalder TiContrast.mount(). "
        "Er værktøjet flyttet, eller kalder siden kernen på en anden måde?")


# --------------------------------------------------------------------------
# Node-harnessen. Denne tekst + sidens egen kode danner den fil der køres.
# --------------------------------------------------------------------------
HARNESS = r"""
'use strict';
// ==========================================================================
// Canvas-stub. Alt hvad `/text-on-image-checker` kalder er her implementeret
// med den adfærd en rigtig browser har — især de to ting den gamle kode
// fejlede på: source-over blanding af en antialiaset glyf, og det
// gennemsigtige sorte getImageData uden for canvas'en.
// ==========================================================================
function hexToRgb(h) {
  h = String(h).replace('#', '');
  if (h.length === 3) h = h[0] + h[0] + h[1] + h[1] + h[2] + h[2];
  return [parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16), parseInt(h.slice(4, 6), 16)];
}

class ImgData {
  constructor(w, h) { this.width = w; this.height = h; this.data = new Uint8ClampedArray(w * h * 4); }
}

function blend(dst, src, alpha) {
  const a = alpha / 255, da = dst[3] / 255;
  const oa = a + da * (1 - a);
  if (oa <= 0) { dst[0] = dst[1] = dst[2] = dst[3] = 0; return dst; }
  for (let k = 0; k < 3; k++) dst[k] = Math.round((src[k] * a + dst[k] * da * (1 - a)) / oa);
  dst[3] = Math.round(oa * 255);
  return dst;
}

class Ctx {
  constructor(cv) { this.cv = cv; this._font = '10px sans-serif'; this._fontPx = 10;
                    this._fill = [0, 0, 0]; this.fillStyle = '#000000'; this.textBaseline = 'top'; }
  // Canvas' bredde/højde ændres af loadFile() *efter* konteksten er hentet,
  // så bufferen følger den aktuelle størrelse og nulstilles kun ved ændring.
  get buf() {
    if (!this._buf || this._bw !== this.cv.width || this._bh !== this.cv.height) {
      this._buf = new ImgData(this.cv.width, this.cv.height);
      this._bw = this.cv.width; this._bh = this.cv.height;
    }
    return this._buf;
  }
  set font(v) { this._font = v; const m = /(\d+(?:\.\d+)?)px/.exec(v); this._fontPx = m ? +m[1] : 10; }
  get font() { return this._font; }
  // `#rrggbbaa` skal læses *rigtigt*. `drawScrim()` sætter netop den form
  // (`scrim.hex + alpha-hex`), fordi canvas kun kan blande én farve med én
  // alfa. En stub der kaster de otte tegn væk ville male sløret i *fuld
  // uopaque* sort, og porten ville så måle en baggrund læseren aldrig ser.
  // Før 3/10 fandtes ingen alfa her, så det er en tilføjelse — ikke en
  // ændring af noget der virkede.
  set fillStyle(v) {
    if (v && v.__grad) { this._grad = v; this._fill = [128, 128, 128]; this._alpha = 1; return; }
    this._grad = null;
    const m = /^#([0-9a-f]{6})([0-9a-f]{2})?$/i.exec(String(v || '#000'));
    if (!m) { this._fill = hexToRgb(v || '#000'); this._alpha = 1; return; }
    this._fill = hexToRgb('#' + m[1]);
    this._alpha = m[2] === undefined ? 1 : parseInt(m[2], 16) / 255;
  }
  get fillStyle() { return '#000000'; }
  clearRect() { this._grad = null; this.buf.data.fill(0); }
  // Én gradientstop ad gangen: `t` er projekteret på aksen, så `s0` og `s1`
  // blandes efter hvor **langt** fra hver ende pixelen ligger. Den projekterede
  // værdi klippes til 0–1, fordi en pixel uden for aksens endepunkter ligger
  // *på* den første eller sidste farve — præcis som i en rigtig browser.
  _gradientFarve(g, t) {
    const s = g.stops;
    if (!s.length) return [128, 128, 128];
    if (t <= s[0][0]) return hexToRgb(s[0][1]);
    for (let i = 1; i < s.length; i++) {
      if (t <= s[i][0]) {
        const a = s[i - 1], b = s[i], u = (t - a[0]) / (b[0] - a[0]);
        const ca = hexToRgb(a[1]), cb = hexToRgb(b[1]);
        return [0, 1, 2].map((k) => Math.round(ca[k] + (cb[k] - ca[k]) * u));
      }
    }
    return hexToRgb(s[s.length - 1][1]);
  }
  // Sløret males *rigtigt* ind i bufferen, så `getImageData` læser den
  // blanding læseren ser. Uden dette ville porten måle billedet uden slør og
  // «fix»-dommen ville være grøn på et tal værktøjet ikke viser.
  fillRect(x, y, w, h) {
    const d = this.buf, W = this.cv.width, a = this._alpha === undefined ? 1 : this._alpha;
    const x0 = Math.max(0, Math.round(x)), y0 = Math.max(0, Math.round(y));
    const x1 = Math.min(W, Math.round(x + w)), y1 = Math.min(this.cv.height, Math.round(y + h));
    // En gradient males i sRGB, som `createLinearGradient()` gør i en browser.
    // Aksen er projiceret på gradientens egen linje, og `t` er positionen
    // mellem endepunkterne — så porten måler præcis den blanding læseren ser.
    const g = this._grad;
    const dx = g ? g.x1 - g.x0 : 0, dy = g ? g.y1 - g.y0 : 0;
    const len2 = dx * dx + dy * dy;
    for (let py = y0; py < y1; py++) for (let px = x0; px < x1; px++) {
      let f = this._fill;
      if (g) {
        const t = len2 ? Math.max(0, Math.min(1, ((px - g.x0) * dx + (py - g.y0) * dy) / len2)) : 0;
        f = this._gradientFarve(g, t);
      }
      const i = (py * W + px) * 4;
      for (let k = 0; k < 3; k++) d.data[i + k] = Math.round(f[k] * a + d.data[i + k] * (1 - a));
      d.data[i + 3] = 255;
    }
  }
  // `drawScrim()` gemmer og gendanner tilstanden omkring sit `fillRect`, så
  // sløret ikke smitter videre på bogstaverne der tegnes bagefter.
  save() { this._saved = { fill: this._fill.slice(), alpha: this._alpha, font: this._font }; }
  restore() { if (this._saved) { this._fill = this._saved.fill; this._alpha = this._saved.alpha; this._font = this._saved.font; } }
  drawImage(img, _dx, _dy, dw, dh) {
    const s = img._pix, d = this.buf, W = this.cv.width;
    for (let y = 0; y < dh; y++) {
      const sy = Math.min(s.h - 1, Math.floor(y * s.h / dh));
      for (let x = 0; x < dw; x++) {
        const sx = Math.min(s.w - 1, Math.floor(x * s.w / dw));
        const si = (sy * s.w + sx) * 4, di = (y * W + x) * 4;
        d.data[di] = s.data[si]; d.data[di + 1] = s.data[si + 1];
        d.data[di + 2] = s.data[si + 2]; d.data[di + 3] = s.data[si + 3];
      }
    }
  }
  measureText(t) { return { width: String(t).length * this._fontPx * 0.52 }; }
  // Den stiplede ramme om den tekstblok et klik flytter. Den males *intet* ind
  // i bufferen — en stiplet strege er ikke en baggrund, og hvis porten malte den
  // som fyld ville målingen få en kant den bruteren ikke ser. Den findes her
  // fordi kernen kalder den på enhver canvas-stub; en stub der mangler den
  // dør med en TypeError og dommen siger intet.
  setLineDash() {}
  strokeRect() {}
  // Syntetiske men antialiasede glyfer: en hård kerne med to bløde kantkolonner.
  // Det er præcis den form en rigtig rasteriser giver ved en bogstavkant, og
  // det er den de gamle `dr+dg+db < 120` ikke kunne skelne fra baggrund.
  fillText(t, x, y) {
    const fs = this._fontPx, w = Math.round(this.measureText(t).width), d = this.buf;
    for (let px = 0; px < w; px++) {
      const k = px % 12;
      const a = (k === 0 || k === 11) ? 46 : (k >= 2 && k <= 9 ? 255 : 0);
      if (!a) continue;
      for (let py = 0; py < fs; py++) {
        const al = (py === 0 || py === fs - 1) ? Math.round(a * 0.5) : a;
        if (!al) continue;
        const cx = x + px, cy = y + py;
        if (cx < 0 || cy < 0 || cx >= this.cv.width || cy >= this.cv.height) continue;
        const di = (cy * this.cv.width + cx) * 4;
        const o = blend([d.data[di], d.data[di + 1], d.data[di + 2], d.data[di + 3]],
                        this._fill, al);
        d.data[di] = o[0]; d.data[di + 1] = o[1]; d.data[di + 2] = o[2]; d.data[di + 3] = o[3];
      }
    }
  }
  getImageData(x, y, w, h) {
    const out = new ImgData(w, h), d = this.buf, W = this.cv.width, H = this.cv.height;
    for (let j = 0; j < h; j++) for (let i = 0; i < w; i++) {
      const oi = (j * w + i) * 4, sx = x + i, sy = y + j;
      // Uden for canvas'en giver browseren gennemsigtigt sort, ikke en fejl.
      if (sx < 0 || sy < 0 || sx >= W || sy >= H) continue;
      const si = (sy * W + sx) * 4;
      out.data[oi] = d.data[si]; out.data[oi + 1] = d.data[si + 1];
      out.data[oi + 2] = d.data[si + 2]; out.data[oi + 3] = d.data[si + 3];
    }
    return out;
  }
  // Demo-billedet tegnes med gradient og cirkel; porten dømmer ikke demoen,
  // men koden skal kunne køre igennem den.
  createLinearGradient(x0, y0, x1, y1) { return { __grad: true, x0: x0, y0: y0, x1: x1, y1: y1, stops: [], addColorStop(o, c) { this.stops.push([o, c]); } }; }
  beginPath() {} arc() {} fill() {}
}

// Gradienten males **pixel for pixel** ind i bufferen, så `getImageData`
// læser den blanding læseren ser. Uden det var `createLinearGradient()` en
// no-op-stub, der malte fladen i grå [128,128,128] — og så ville løftet «en
// gradient måles» være grønt for enhver kode, også en der ignorerer begge
// stops. Det er præcis det porten er bygget imod: et løfte uden dom.

class Canvas {
  constructor(w, h) { this.width = w; this.height = h; this._ctx = null; }
  getContext() { if (!this._ctx) this._ctx = new Ctx(this); return this._ctx; }
  getBoundingClientRect() { return { left: 0, top: 0, width: this.width, height: this.height }; }
  get _pix() { return { w: this.width, h: this.height, data: this.getContext().buf.data }; }
  // `downloadPng()` kalder `toDataURL('image/png')`. En stub uden den døde med
  // en TypeError *ved klikket* — altså først når bruteren trykker, hvilket er
  // netop den fejl porten skal se. Den gemmer bufferen **som den ser ud i det
  // øjeblik** kaldet kommer, så dommen kan spørge om den hentede fil er det
  // bruteren så (billedet med tekst og slør) eller kun bogstaverne på en
  // gennemsigtig baggrund — `sampleContrast()` efterlader præcis den sidste.
  toDataURL(type) {
    Eksport.type = type || 'image/png';
    Eksport.bredde = this.width;
    Eksport.hoejde = this.height;
    Eksport.pixels = Uint8ClampedArray.from(this.getContext().buf.data);
    return 'data:' + Eksport.type + ';base64,iVBORw0KGgo=';
  }
}

class El {
  constructor(id, opts) {
    opts = opts || {};
    this.id = id; this._v = opts.value || ''; this._l = {};
    this.textContent = ''; this.innerHTML = ''; this.hidden = false; this.className = '';
    this.files = []; this._c = opts.canvas || null;
    // Kernen skriver `felt.style.display` for at skjule gradientens felter. En
    // stub uden `style` ville kaste en TypeError *ved sidevisning*, og porten
    // ville dømme ingen fejl overhovedet — grøn fordi den aldrig kom så langt.
    this.style = {};
    this._q = {}; this._qHtml = '';
  }
  get value() { return this._v; }
  set value(v) { this._v = v; }
  // `loadFile()` skalerer billedet ned og sætter `cv.width`/`cv.height`. Uden
  // videre-sendelsen lander det på stubben og ikke på canvas-bufferen, så
  // værktøjet måler i den gamle størrelse og porten får grønt på en fejl.
  get width() { return this._c ? this._c.width : 0; }
  set width(v) { if (this._c) this._c.width = v; }
  get height() { return this._c ? this._c.height : 0; }
  set height(v) { if (this._c) this._c.height = v; }
  getContext() { return this._c.getContext(); }
  // `cv` er i kernen `document.getElementById('cv')` — altså *elementet*, ikke
  // konteksten. I browseren er elementet en canvas og har selv `toDataURL()`.
  // Uden videre-sendelsen her ville `downloadPng()` få `undefined` og stå med
  // en TypeError, og porten ville dømme en kern der virker.
  toDataURL(t) { return this._c.toDataURL(t); }
  getBoundingClientRect() { return this._c.getBoundingClientRect(); }
  addEventListener(t, fn) { (this._l[t] = this._l[t] || []).push(fn); }
  fire(t, ev) { (this._l[t] || []).forEach(function (f) { f(ev || {}); }); }
  // `updateResult()` binder «fix»-knappen den lige har skrevet ved at slå den
  // op med `res.querySelector('[data-ti-fix]')`. En stub uden `querySelector`
  // fik porten til at dø med en TypeError *ved sidevisning*, så den dømmede
  // ingen fejl overhovedet — grøn fordi den aldrig kom så langt.
  //
  // Den skal give det **samme** element hver gang den spørgs for samme
  // selector. Et nyt objekt hver gang ville være en knap uden lyttere: et
  // klik på den ville ikke gøre noget, og porten ville se uændrede tal og
  // dømme «rettelsen virker ikke» om en kern der virker fint. Derfor caches
  // den pr. selector — præcis som en rigtig browser gør, fordi der kun er én
  // knap i markup'en.
  //
  // Cachen skal dog **dø med markup'en**: `updateResult()` skriver en ny
  // `innerHTML` og binder så den knap den lige har skrevet. Uden den
  // nulstilling ville en knap fra et tidligere billede blive fundet igen, og
  // `if (!knap) return null` i `fixKnap()` ville aldrig være sand — altså et
  // løfte uden dom. Det var ikke en hypotese: med en cache der levede for evig
  // gav mutationen «fjern knappen af markup'en» **grønt**, fordi stubben stadig
  // fandt en knap i et gammelt element.
  //
  // Og den skal svare **null** når markup'en ikke har knappen. Det er hele
  // pointen med at have en selector overfor en streng: `updateResult()`
  // skriver knappen *ind i* `innerHTML`, så det er dér, sandheden om hvor der
  // står en knap, ligger.
  querySelector(sel) {
    if (this._qHtml !== this.innerHTML) { this._q = {}; this._qHtml = this.innerHTML; }
    const attr = /^\[([a-z][a-z0-9-]*)(?:=["']?[^"'\]]*["']?)?\]$/.exec(sel);
    // Et attributnavn må indeholde `-`, så en **bindestreg** er ikke et
    // skel. Uden `(?![\w-])` fandt `[data-ti-dl]`-opslaget også
    // `data-ti-dl-mark`, fordi `\b` siger "slut her" foran enhver `-` — og
    // mutationen «fjern den rene download-knap» stod grøn, fordi stubben stadig
    // fandt den markerede knap. Det er præcis det porten er skrevet imod: en
    // mutation der giver grønt, er en løfte uden dom.
    if (attr && !new RegExp('\\b' + attr[1] + '(?![\\w-])').test(this.innerHTML || '')) return null;
    if (!this._q[sel]) { this._q[sel] = new El(sel); this._q[sel]._ejer = this; }
    return this._q[sel];
  }
  // Attributterne læses ud af den markup kernen lige har skrevet — ikke fra en
  // felt på stubben. Det er hele pointen med at dømme `innerHTML`: en stub der
  // *svarede* `aria-pressed` ville være grøn på en knap der aldrig fik den.
  // `data-ti-pick="1"`/`"0"` og `aria-pressed="true"`/`"false"` ligger begge i
  // resultatets markup, så det er dér sandheden er.
getAttribute(name) {
    // Markup'en er *ejerens* — knappen er fundet i den, så dens attributter
    // står dér og ikke på den lille stub. Uden `_ejer` ville porten se en
    // knap uden attributter og dømme den rød uden grund.
    const h = (this._ejer || this).innerHTML || '';
    const m = new RegExp('\\b' + name + '="([^"]*)"').exec(h);
    if (m) return m[1];
    return new RegExp('\\b' + name + '\\b').test(h) ? '' : null;
  }
  click() { this.fire('click', {}); }
}

// Image-stubben: `loadFile()` sætter onload og derefter src, så src-setteren
// kalder onload med det billede harnessen har lagt klar.
class Img {
  constructor() { this._onload = null; this._onerror = null; this._pix = Img.next; }
  set onload(f) { this._onload = f; } get onload() { return this._onload; }
  set onerror(f) { this._onerror = f; }
  set src(v) {
    this._src = v;
    if (!this._pix) { if (this._onerror) this._onerror(); return; }
    this.naturalWidth = this._pix.w; this.naturalHeight = this._pix.h;
    if (this._onload) this._onload();
  }
  get src() { return this._src; }
}
Img.next = null;

function ensfarvet(w, h, hex) {
  const rgb = hexToRgb(hex), p = { w: w, h: h, data: new Uint8ClampedArray(w * h * 4) };
  for (let i = 0; i < w * h; i++) {
    p.data[i * 4] = rgb[0]; p.data[i * 4 + 1] = rgb[1]; p.data[i * 4 + 2] = rgb[2]; p.data[i * 4 + 3] = 255;
  }
  return p;
}
function todelt(w, h, hexVenstre, hexHoejre) {
  const a = ensfarvet(w, h, hexVenstre), b = ensfarvet(w, h, hexHoejre);
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
    const p = x < w / 2 ? a : b, i = (y * w + x) * 4;
    a.data[i] = p.data[i]; a.data[i + 1] = p.data[i + 1];
    a.data[i + 2] = p.data[i + 2]; a.data[i + 3] = 255;
  }
  return a;
}
// Gradient med flade ender: de yderste `flad` kolonner er helt hvide og
// helt sorte. En ren rampe har kun de to yderste pixel i de rene farver,
// og netop dem kan et bogstav dække. Flade ender er også det et rigtigt
// billede har: et mørkt forgrund og en lys himmel.
function gradient(w, h, hexVenstre, hexHoejre, flad) {
  const a = hexToRgb(hexVenstre), b = hexToRgb(hexHoejre);
  const p = { w: w, h: h, data: new Uint8ClampedArray(w * h * 4) };
  const mid = flad, bred = Math.max(1, w - 2 * flad);
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
    const t = Math.min(1, Math.max(0, (x - mid) / bred));
    const i = (y * w + x) * 4;
    for (let k = 0; k < 3; k++) p.data[i + k] = Math.round(a[k] + (b[k] - a[k]) * t);
    p.data[i + 3] = 255;
  }
  return p;
}
function lodret(w, h, hexOeverst, hexNederst) {
  const a = ensfarvet(w, h, hexOeverst), b = ensfarvet(w, h, hexNederst);
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
    const p = y < h - 10 ? a : b, i = (y * w + x) * 4;
    a.data[i] = p.data[i]; a.data[i + 1] = p.data[i + 1];
    a.data[i + 2] = p.data[i + 2]; a.data[i + 3] = 255;
  }
  return a;
}

// Et todelt billede hvor den *venstre* halvdel er én farve og den højre en
// anden. Det er den form «fix»-knappen er skrevet til: tekstkassen dækker
// begge sider, så værktøjet måler det dårligste par, og rettelsen skal løse
// begge ende på én gang. `lodret()` kan ikke bruges — den deler kun de
// nederste 10 rækker, så kassen ville ligge i én halvdel, og rettelsen ville
// aldrig blive prøvet af på den svære del.
function todeltVandret(w, h, hexVenstre, hexHoejre) {
  const d = ensfarvet(w, h, hexVenstre), e = ensfarvet(w, h, hexHoejre);
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
    const p = x < w / 2 ? d : e, i = (y * w + x) * 4;
    d.data[i] = p.data[i]; d.data[i + 1] = p.data[i + 1];
    d.data[i + 2] = p.data[i + 2]; d.data[i + 3] = 255;
  }
  return d;
}

// ==========================================================================
// DOM'en sidekoden får, og så kører den.
// ==========================================================================
const cv = new Canvas(300, 150);
// Hvad eksporten faktisk gjorde. Anchoren oprettes af kernen og klikkes af
// den, så det er her porten ser om der kom en fil ud med et navn — ikke om
// der stod en knap i markup'en.
const Eksport = { ankre: [], type: null, bredde: 0, hoejde: 0, pixels: null };
const nodes = {
  'cv': new El('cv', { canvas: cv }),
  'file': new El('file'),
  'text': new El('text', { value: 'Your headline here' }),
  'fg': new El('fg', { value: '#ffffff' }),
  'fontsize': new El('fontsize', { value: 'large' }),
  'err': new El('err'),
  'result': new El('result'),
  // Blok 2 er en *rigtig* del af harnessen, ikke en streng der testes. Uden
  // disse felter ville `getElementById('fg2')` returnere en ny, tom stub
  // hver gang kernen spørger — så blok 2 ville måle en tom tekst i ingen
  // farve, og porten ville dømme en egenskab der ikke virker, som om den
  // virkede. Det er præcis det en løfte uden dom er.
  'text2': new El('text2', { value: 'Din undertekst her' }),
  'fg2': new El('fg2', { value: '#ffffff' }),
  'result2': new El('result2'),
  // Gradient-baggrunden er en *rigtig* del af harnessen, samme grund som blok
  // 2: uden felterne ville `getElementById('gfrom')` returnere en ny, tom stub
  // hver gang kernen spørger, gradienten ville male sort, og porten ville
  // dømme «værktøjet måler ikke gradienten» på en side der faktisk gør det.
  'bgmode': new El('bgmode', { value: 'image' }),
  'gfrom': new El('gfrom', { value: '#1e3a5f' }),
  'gto': new El('gto', { value: '#c9d8e4' }),
  'gang': new El('gang', { value: '45' }),
  'tigrad': new El('tigrad'),
};
globalThis.document = {
  getElementById: function (id) { return nodes[id] || new El(id); },
  createElement: function (t) {
    if (t === 'canvas') return new Canvas(1, 1);
    const el = new El(t);
    // `downloadPng()` sætter `href`/`download` og kalder `click()`. Her
    // registreres resultatet, så dommen kan dømme filen og ikke knappen.
    if (t === 'a') {
      const raa = el.click.bind(el);
      el.click = function () {
        Eksport.ankre.push({ href: el.href || '', download: el.download || '' });
        raa();
      };
    }
    return el;
  },
};
// I en browser *er* `window` `globalThis`. Det er ikke en bivirkende detalje:
// kernen lægger `TiContrast` på `globalThis`, og siden kalder den gennem
// `window.` — så et lokalt `window`-objekt ville gøre `mount()` til en
// ReferenceError, og porten ville dømme en side uden værktøj.
globalThis.addEventListener = function () {};
globalThis.window = globalThis;
globalThis.Image = Img;
globalThis.URL = { createObjectURL: function () { return 'blob:stub'; }, revokeObjectURL: function () {} };

/* ---- SIDENS EGEN KODE -------------------------------------------------- */
%%SIDENS_KODE%%
/* ----------------------------------------------------------------------- */

// Kernet har lige monteret værktøjet, og bruteren har endnu ikke valgt et
// billede. Dette er *pristine*-tilstanden — den eneste i hele harnessen hvor
// det er sandt at intet er uploadet — så demo-noten skal dømmes her. Alle
// målinger længere nede uploader et billede, og en dom der læste state dér
// ville være grøn uden at se den fejl den er skrevet til.
function demoVedStart() {
  const h = nodes['result'].innerHTML || '';
  const m = /data-ti-demo>([\s\S]*?)</.exec(h);
  return {
    tekst: m ? m[1] : null,
    // Står noten *før* badge'en? Ellers læser en læser der kun ser PASS/
    // FAIL-kappen et målt tal uden at vide hvor det kom fra. Det er den
    // forskel på «et eksempel med en advarsel» og «en advarsel med et
    // eksempel».
    forBadge: m ? h.indexOf('data-ti-demo') < h.indexOf('ti-badge') : false,
    // Demoen skal stadig *måle* — den er den, der lærer bruteren hvad
    // værktøjet gør. Uden et tal er den en tom flade.
    harTal: /<strong>[0-9.,]+:1<\/strong>/.test(h),
  };
}
const demoStart = demoVedStart();
// `demoEfterUpload()` måles **med det samme**, ikke i JSON'en til sidst. Den
// spørger om demo-noten er væk igen *efter* et upload — og da gradient-kæden
// længere nede har sat `demoBillede = false`, ville den vædd målt på en
// tilstand bruteren ikke kan være i, og mutationen «nulstil ikke flaget» ville
// stå grøn fordi noten var væk af en helt anden grund. Det er præcis det en
// løfte uden dom er: dommen læser et tal hun ikke kan skaffe selv.
const demoEfter = demoEfterUpload();

// ==========================================================================
// Sådan stilles et spørgsmål til værktøjet, som en bruger gør det: upload et
// billede, sæt tekstfarven, træk teksten hen. Og læs det tal der står på
// skærmen — ikke et tal porten har hentet ud af en intern variabel.
// ==========================================================================
function spoerg(billede, tekstfarve, tekst, x, y) {
  Img.next = billede;
  nodes['file'].files = [{ type: 'image/png' }];
  nodes['file'].fire('change', { target: { files: nodes['file'].files } });
  nodes['fg'].value = tekstfarve; nodes['fg'].fire('input');
  if (tekst !== undefined) { nodes['text'].value = tekst; nodes['text'].fire('input'); }
  if (x !== undefined) {
    nodes['cv'].fire('mousedown', { clientX: x, clientY: y, preventDefault: function () {} });
  }
  // Den danske side skriver 21,00 med komma — korrekt dansk — så porten læser
  // begge former. Den må ikke straffe siden for at tale dansk.
  const m = /<strong>([0-9.,]+):1<\/strong>/.exec(nodes['result'].innerHTML);
  return m ? parseFloat(m[1].replace(',', '.')) : null;
}

/* ---- «Fix it»-knappen: den ende-til-ende-dom ----------------------
 * `klikFix()` gør præcis det bruteren gør — trykker på den knap, kernen
 * lige har skrevet — og læser det tal der så står på skærmen. Den læser
 * *markup'en*, ikke et tal ud af en intern variabel, så den er målt på
 * den kode der faktisk ships.
 *
 * Før 3/10 skrev værktøjet «try a darker/lighter text color» og standsede.
 * Uden denne funktion dømmer ingen port at rettelsen virker: mutationen
 * «fjern knappens lytter» giver præcis de samme 22 tal som den rigtige
 * kode, fordi tallene er ændret *inden* knappen skrives. */
function fixKnap() {
  const res = nodes['result'];
  const knap = res.querySelector('[data-ti-fix]');
  if (!knap) return null;
  knap.click();
  const m = /<strong>([0-9.,]+):1<\/strong>/.exec(res.innerHTML);
  return { fik: m ? parseFloat(m[1].replace(',', '.')) : null, harKnap: true };
}
function fixEfter(billede, tekstfarve, tekst, x, y) {
  Img.next = billede;
  nodes['file'].files = [{ type: 'image/png' }];
  nodes['file'].fire('change', { target: { files: nodes['file'].files } });
  nodes['fg'].value = tekstfarve; nodes['fg'].fire('input');
  if (tekst !== undefined) { nodes['text'].value = tekst; nodes['text'].fire('input'); }
  if (x !== undefined) {
    nodes['cv'].fire('mousedown', { clientX: x, clientY: y, preventDefault: function () {} });
  }
  const foer = spoerg(billede, tekstfarve, tekst, x, y);
  const efter = fixKnap();
  return { foer: foer, efter: efter };
}

// ==========================================================================
// Gradient-baggrunden: den anden rute ind i *samme* måling. Bruteren skriver
// to stop og en vinkel i stedet for at uploade et foto, og læser så tallet på
// skærmen — nøjagtig som `spoerg()` gør for et foto, så dommen ikke kan være
// grøn fordi den læser en anden vej end bruteren.
// ==========================================================================
function gradientStart(fra, til, vinkel) {
  nodes['bgmode'].value = 'gradient';
  nodes['bgmode'].fire('change', {});
  nodes['gfrom'].value = fra; nodes['gfrom'].fire('input', {});
  nodes['gto'].value = til; nodes['gto'].fire('input', {});
  nodes['gang'].value = String(vinkel); nodes['gang'].fire('input', {});
}
// Tallet og dommen, begge læst i den markup bruteren ser. `ti-pass`/`ti-fail`
// ligger på `res.className`, så dommen kan skelne «den er grøn» fra «der står
// et højt tal og den fejler alligevel».
function laesResultat() {
  const h = nodes['result'].innerHTML || '';
  const m = /<strong>([0-9.,]+):1<\/strong>/.exec(h);
  return {
    fik: m ? parseFloat(m[1].replace(',', '.')) : null,
    fejler: /ti-fail/.test(nodes['result'].className || ''),
  };
}
function spoergGradient(fra, til, vinkel, tekstfarve, tekst, x, y) {
  gradientStart(fra, til, vinkel);
  // Blok 1 skal være den valgte. `toBlokke()` slutter med blok 2 valgt, fordi
  // det er den den dom dømmer — og et klik på billedet flytter da *blok 2*, så
  // blok 1s tal blev liggende det samme uanset hvor bruteren flyttede hen. Det
  // er ikke en målefejl men en *brugsfejl*, og den er grå og dummere end de
  // løfter den forsvandt i. Vælgeren trykkes her — præcis som bruteren gør.
  // Vælgeren trykkes med præcis den selector kernen selv bruger. El-stubben
  // cached pr. selector-*streng*, så `[data-ti-pick="0"]` ville give en anden
  // stub end `[data-ti-pick]` — uden lytter, og porten ville tro at bruteren
  // ikke kan vælge blok. Blok 0 står i `result`, så dens attribut er den der
  // læses.
  const valg = nodes['result'].querySelector('[data-ti-pick]');
  if (valg) valg.click();
  nodes['fg'].value = tekstfarve; nodes['fg'].fire('input', {});
  nodes['text'].value = tekst; nodes['text'].fire('input', {});
  if (x !== undefined) {
    nodes['cv'].fire('mousedown', { clientX: x, clientY: y, preventDefault: function () {} });
  }
  return laesResultat();
}

const FARVEPAR = __FARVEPAR__;
const FLADT = __FLADT__;
const TODELT = __TODELT__;
const GRADIENT = __GRADIENT__;
const svar = [];
for (const p of FARVEPAR) {
  svar.push({ navn: p[0], forventet: p[3], fik: spoerg(ensfarvet(400, 300, p[1]), p[2]) });
}
svar.push({ navn: FLADT[0], forventet: FLADT[4], fik: spoerg(lodret(FLADT[1], FLADT[2], '#ffffff', '#000000'), '#ffffff', 'Hi', FLADT[3], FLADT[3]) });
for (const t of TODELT) {
  svar.push({ navn: t[0], forventet: t[5], fik: spoerg(todelt(t[1], t[2], '#000000', '#ffffff'), t[4], 'Hi', t[3], 200) });
}
// Den ene case hvor bedste og dårligste baggrund kan ligge i samme kasse.
svar.push({ navn: GRADIENT[0], forventet: GRADIENT[6],
            fik: spoerg(gradient(GRADIENT[1], GRADIENT[2], '#ffffff', '#000000', 120), GRADIENT[5], __GRADIENT_TEKST__, GRADIENT[3], GRADIENT[4]) });
// De to billeder rettelsen er skrevet til: det ene kan klares med én
// tekstfarve, det andet kræver et slør fordi ingen farve består begge
// ende. Begge er **fejlende** i udgangspunktet, så tallet efter et tryk
// på knappen kan dømmes mod det krav, siden viser.
const FIX = [
  // Alle fire er billeder hvor den **venstre** halvdel er mørkere end den
  // højre, og teksten står midt i overgangen — så kassen dækker begge ende
  // og værktøjet måler det dårligste par. Det er den situation «fix» er
  // skrevet til; på et ensfarvet billede ville den altid bestå med hvid
  // tekst, og knappen ville aldrig blive prøvet af.
  { navn: 'jævnt baggrund (tekstfarve)', bg: ['#60646c', '#787c84'], farve: '#ffffff', krav: 4.5 },
  { navn: 'midtone baggrund (tekstfarve)', bg: ['#6e727a', '#82868e'], farve: '#ffffff', krav: 4.5 },
  { navn: 'spredt baggrund (slør)', bg: ['#161a22', '#ebeef2'], farve: '#ffffff', krav: 4.5 },
  { navn: 'spredt baggrund, stor tekst', bg: ['#161a22', '#ebeef2'], farve: '#ffffff', krav: 3 },
];
const fixSvar = [];
for (const f of FIX) {
  const d = todeltVandret(400, 300, f.bg[0], f.bg[1]);
  // `fontsize`-stubben står på `large`, så 4,5:1-casen sættes til `small` —
  // ellers ville alle fire dømme det samme krav, og 3:1-casen ville være
  // en dublet af den første.
  nodes['fontsize'].value = f.krav === 3 ? 'large' : 'small';
  const r = fixEfter(d, f.farve, 'Dette er en overskrift over et todelt billede', 20, 140);
  fixSvar.push({ navn: f.navn, krav: f.krav, foer: r.foer, efter: r.efter });
}

/* ---- To billeder i træk med «fix» imellem -------------------------------
 *
 * Alt ovenfor dømmer **ét** billede pr. måling. Det er den fejlform reviewen
 * 3/10 målte i rigtig Chromium på den byggede side: `loadFile()` satte hverken
 * `scrim` eller `lastFix` null, så et slør beregnet på *første* bildes
 * endepunkter blev tegnet på det næste, og `.ti-fixed`-teksten stod under et
 * tal der ikke stammer fra det bruteren havde lavet. Målt: foto A efter fix
 * 4,52:1, og det næste foto **1,52:1** med «Jeg lagde et 13 % mørkt lag bag
 * teksten» under sig — en påstand målt på et andet input end den den
 * udtaler sig om.
 *
* `spoerg()` og `fixEfter()` kan ikke finde den: begge sætter `fg` og affyrer
 * `input`, og **den** handler nulstiller sløret. Så hvert eneste kald i
 * porten ryddede netop den tilstand, fejlen ligger i. Derfor er der her en
 * egen kæde, der *kun* uploader: `uploadBillede()` rører hverken farvefelt,
 * tekstfelt eller mus — det er præcis hvad en bruger gør ved sit tredje foto
 * i træk.
 *
 * Rækkefølgen er hele pointen, og den er kun to målinger:
 *   1. foto A + «fix»     → kernen får et slør, der hører til A
 *   2. foto B, intet rørt → `efter` er hvad bruteren faktisk ser
 *   3. foto B, farve=F    → `refer` er B's eget tal *ved den farve fixen
 *                           efterlod*, altså B målt uden slør
 *
 * Step 3 er ikke en småting. `applyFix()` sætter **også** tekstfarven, fordi
 * et hvidt slør kræver sort tekst — så efter en rettelse står der `#000000` i
 * feltet, og B's eget tal er sort-tekst-på-B, ikke hvid-på-B. Uden step 3
 * ville dommen sammenligne to forskellige farver og dømme en kern der gør
 * helt rigtigt. Den kommer *efter* step 2, så den nulstiller ikke den
 * tilstand den måler. */
function uploadBillede(billede) {
  Img.next = billede;
  nodes['file'].files = [{ type: 'image/png' }];
  nodes['file'].fire('change', { target: { files: nodes['file'].files } });
}
// Læser skærmen, ikke en intern variabel: samme greb som `fixKnap()`.
function laesSkarm() {
  const res = nodes['result'];
  const m = /<strong>([0-9.,]+):1<\/strong>/.exec(res.innerHTML);
  return {
    fik: m ? parseFloat(m[1].replace(',', '.')) : null,
    harFast: /\bti-fixed\b/.test(res.innerHTML),
    harKnap: !!res.querySelector('[data-ti-fix]'),
  };
}
// A er todelt mørk→lys med hvid tekst: ingen tekstfarve består begge ende, så
// rettelsen *må* lægge et slør. Det er den eneste form hvor sløret overlever
// til næste foto, så den er den eneste der kan finde fejlen.
// B er derimod **mørk**, fordi det er den farve fixen efterlader: `applyFix()`
// sætter tekstfarven til sort ved et hvidt slør, og sort tekst på et lyst
// billede består altid. Et B der så består ville få dommen til at gråde over
// en «fix»-knap der med vilje mangler, og løfter (b) og (c) ville være grønne
// fordi de aldrig kan se den fejl, de er skrevet til. B skal altså fejle —
// sort på #3a3a3a er ca. 1,9:1 mod kravet 4,5:1.
const sekA = todeltVandret(400, 300, '#161a22', '#ebeef2');
const sekB = ensfarvet(400, 300, '#3a3a3a');
const sekTekst = 'Dette er en overskrift over et todelt billede';
nodes['fontsize'].value = 'small';
const sekFarve = '#ffffff';
// 1 — fix på A. `fixEfter()` bruger præcis den geometri som FIX-tabellen
// bruger til sin **slør**-case, og det er ikke en tilfældighed: på en anden
// tekstkasse vælger `suggestFix()` en *tekstfarve* i stedet, og så er der intet
// slør at lække. Kun slør-casen kan finde den fejl, porten er skrevet til.
const fixA = fixEfter(sekA, sekFarve, sekTekst, 20, 140);
const farveEfterFix = nodes['fg'].value;
// 2 — foto B igen. Ingen `fg`, intet `input`, ingen mousedown.
uploadBillede(sekB);
const sekB1 = laesSkarm();
// 3 — referencen for præcis den farve fixen efterlod.
nodes['fg'].value = farveEfterFix; nodes['fg'].fire('input');
uploadBillede(sekB);
const renB2 = laesSkarm();

/* ---- Download-knappen: den ende-til-ende-dom ----------------------
 * Kæden er den bruteren går: upload → «Fix it» → «Download». Den sidste
 * handling er den nye, og den er den der *afleverer* noget — før 3/10 endte
 * værktøjet ved et tal, og bruteren måtte selv finde ud af, hvordan han fik
 * sit rettede billede ud igen.
 *
 * Der dømmes tre løfter, fordi de er tre forskellige fejlformer:
 *   a) der står en download-knap at trykke på;
 *   b) et klik afleverer en PNG med et filnavn der ender på `.png` — ellers
 *      hedder filen noget uden udvidelse, og den kan ikke bruges andet steder;
 *   c) den hentede fil er **billedet med rettelsen**: hver pixel dækket, og
 *      den afviger fra det rå foto, altså teksten og sløret er med.
 *
 * (c) er den dom, der kan se resten af `sampleContrast()`: den efterlader
 * bogstaverne på en *ryddet* baggrund, så en eksport der springer
 * `draw()` over giver en fil, der er næsten helt gennemsigtig — og
 * bruteren får noget, der ikke ligner det han lige målte og rettede. */
function downloadMaal() {
  const res = nodes['result'];
  Eksport.ankre.length = 0;
  const knap = res.querySelector('[data-ti-dl]');
  if (!knap) return { harKnap: false };
  knap.click();
  const a = Eksport.ankre[Eksport.ankre.length - 1] || null;
  const px = Eksport.pixels, s = Img.next;
  let uopaque = 0, afvigelser = 0;
  if (px && s) {
    const W = Eksport.bredde, H = Eksport.hoejde;
    for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
      const di = (y * W + x) * 4;
      const sy = Math.min(s.h - 1, Math.floor(y * s.h / H));
      const sx = Math.min(s.w - 1, Math.floor(x * s.w / W));
      const si = (sy * s.w + sx) * 4;
      if (px[di + 3] === 255) uopaque++;
      if (px[di] !== s.data[si] || px[di + 1] !== s.data[si + 1]
          || px[di + 2] !== s.data[si + 2]) afvigelser++;
    }
  }
  return {
    harKnap: true,
    anker: a ? { href: a.href, download: a.download } : null,
    uopaque: uopaque, total: Eksport.bredde * Eksport.hoejde,
    afvigelser: afvigelser,
  };
}
// Efter «fix» på A: sløret ligger på canvas, og netop den rettelse skal være
// med i filen bruteren henter.
fixEfter(sekA, sekFarve, sekTekst, 20, 140);
const dlMaal = downloadMaal();

/* ---- «Download with the worst spot marked»: et *andet* valg ---------
 *
 * Et tal på 1,10:1 siger at noget er galt, men ikke hvor. Det er præcis det
 * et bureau der gennemgår en kundes fotos mangler, når det skal give
 * designeren besked uden at åbne værktøjet igen — og før dette valg var det
 * umuligt: bruteren fik filen, men ingen i filen.
 *
 * Fire løfter, fordi de er fire forskellige fejlformer:
 *   a) der står en knap med en tekst, og den er sin egen knap;
 *   b) den **rene** fil har intet felt i — ellers er de to valg ét valg, og
 *      bruteren kan ikke få den grafik han rettede;
 *   c) feltet sidder over det pixel der *koster mest kontrast*. Porten læser
 *      den rene fils farve under feltets midte og kræver den værste af de to;
 *      den må altså ikke bare ligge et sted i boksen;
 *   d) forhåndsvisningen er ren igen bagefter. Et felt der bliver stående på
 *      skærmen ville ligne en del af bruterens eget design. */
const MARKER = [220, 38, 38];
function taellFarve(px, rgb) {
  if (!px) return 0;
  let n = 0;
  for (let i = 0; i < px.length; i += 4) {
    if (px[i] === rgb[0] && px[i + 1] === rgb[1] && px[i + 2] === rgb[2]) n++;
  }
  return n;
}
function farveBBox(px, rgb) {
  let x0 = Infinity, y0 = Infinity, x1 = -1, y1 = -1, n = 0;
  for (let i = 0; i < px.length; i += 4) {
    if (px[i] !== rgb[0] || px[i + 1] !== rgb[1] || px[i + 2] !== rgb[2]) continue;
    const x = (i / 4) % Eksport.bredde, y = Math.floor((i / 4) / Eksport.bredde);
    if (x < x0) x0 = x; if (x > x1) x1 = x;
    if (y < y0) y0 = y; if (y > y1) y1 = y;
    n++;
  }
  return n ? { x0: x0, y0: y0, x1: x1, y1: y1, antal: n } : null;
}
function pixel(px, x, y) {
  if (!px) return null;
  const i = (y * Eksport.bredde + x) * 4;
  const h = (v) => ('0' + v.toString(16)).slice(-2);
  return '#' + h(px[i]) + h(px[i + 1]) + h(px[i + 2]);
}
// Farven i det **rå foto** under feltets midte. Ikke i den rene hentede fil:
// den har teksten tegnet *på* det pixel, porten vil se på, så den svarer med
// en blanding af bogstav og baggrund (246, 246, 242) i stedet for den
// baggrund bruteren har sin dårligste kontrast imod. Det foto er det kernen
// selv måler på — pass 1 i `sampleContrast()` maler billedet og intet andet —
// så denne læsning er den samme baggrund, uden at porten spørger kernen.
function fotoPixel(foto, x, y) {
  if (!foto || x < 0 || y < 0 || x >= foto.w || y >= foto.h) return null;
  const i = (y * foto.w + x) * 4, h = (v) => ('0' + v.toString(16)).slice(-2);
  return '#' + h(foto.data[i]) + h(foto.data[i + 1]) + h(foto.data[i + 2]);
}
// Hvidt billede med et **sort bånd**. Uden båndet er hele boksen samme
// farve, så «det dårligste pixel» og «et af pixelserne» er det samme sted —
// og porten ville være grøn på en markering i eller ud af kassen.
function baandet(w, h, hexBaand, x0, x1) {
  const p = ensfarvet(w, h, '#ffffff'), rgb = hexToRgb(hexBaand);
  for (let y = 0; y < h; y++) for (let x = x0; x < x1; x++) {
    const i = (y * w + x) * 4;
    p.data[i] = rgb[0]; p.data[i + 1] = rgb[1]; p.data[i + 2] = rgb[2];
  }
  return p;
}
function markeringsMaal() {
  Img.next = baandet(400, 300, '#000000', 150, 180);
  nodes['file'].files = [{ type: 'image/png' }];
  nodes['file'].fire('change', { target: { files: nodes['file'].files } });
  // Lys tekst: på hvid er den ulæselig (1,1:1) og på sort er den 14,6:1, så
  // det *dårligste* sted er den hvide del — og den er den lette at skelne fra
  // den bedste. Porten kræver feltet over den hvide.
  nodes['text'].value = 'Hej'; nodes['text'].fire('input');
  nodes['fg'].value = '#e6e6e6'; nodes['fg'].fire('input');
  nodes['cv'].fire('mousedown', { clientX: 150, clientY: 150, preventDefault: function () {} });
  const res = nodes['result'];
  const ren = res.querySelector('[data-ti-dl]');
  const mark = res.querySelector('[data-ti-dl-mark]');
  if (!mark) return { harKnap: false, harRen: !!ren };
  Eksport.pixels = null;
  if (ren) ren.click();
  const renPx = Eksport.pixels;
  Eksport.pixels = null;
  mark.click();
  const markPx = Eksport.pixels;
  const felt = farveBBox(markPx, MARKER);
  // Farven i det rå foto under feltets midte — altså den baggrund bruteren har
  // mindst kontrast imod, hvis kernen har peget på det rigtige sted. Porten
  // dømmer den, den spørger ikke kernen hvor den troede det var.
  const under = felt ? fotoPixel(Img.next, Math.round((felt.x0 + felt.x1) / 2),
                                        Math.round((felt.y0 + felt.y1) / 2)) : null;
  return {
    harKnap: true, harRen: !!ren, etiket: (/<button[^>]*data-ti-dl-mark[^>]*>([\s\S]*?)<\/button>/.exec(res.innerHTML) || [])[1] || null,
    renMark: taellFarve(renPx, MARKER), markMark: taellFarve(markPx, MARKER),
    felt: felt, under: under,
    liveMark: taellFarve(nodes['cv'].getContext().buf.data, MARKER),
  };
}
const markMaalt = markeringsMaal();

/* ---- «Find where it reads best»: den tredje handling i resultatet -----
 *
 * Et foto består under den ene halvdel af bogstaverne og fejler under den
 * anden, så bruterens spørgsmål er ikke «hvad er tallet her?» men «hvor kan
 * den ligge?». Før 3/10 var svaret «træk selv rundt» — og det er præcis det
 * arbejde værktøjet er lavet for at fjerne.
 *
 * Kæden er den bruteren går: upload → læg teksten på den dårlige halvdel →
 * «Find where it reads best». Billedet er mørkt til venstre og lyst til
 * højre, og hvid tekst på den lyse halvdel kan ikke bestå noget krav, så
 * dommen har både en fejlsituation og et rigtigt svar at kræve. */
function spotLaes() {
  const res = nodes['result'];
  const m = /<strong>([0-9.,]+):1<\/strong>/.exec(res.innerHTML);
  // `[^>]*` fremfor intet: kernen skriver ogsa et `data-ti-moved`-attribut,
  // og en regex der kræver `class="ti-fixed">` holder op at finde en beskrivelse
  // der står der — sa dommen ville vaere gron af den grund at den kenne noget.
  const fast = /<span class="ti-fixed"[^>]*>([\s\S]*?)<\/span>/.exec(res.innerHTML);
  const flyttet = /data-ti-moved="([01])"/.exec(res.innerHTML);
  return {
    fik: m ? parseFloat(m[1].replace(',', '.')) : null,
    harFast: !!fast,
    fast: fast ? fast[1].replace(/<[^>]*>/g, '') : '',
    // Hvorvidt kernen faktisk flyttede teksten, læst som et tal. Sætningen
    // under tallet afhænger af det, så dommen kan ikke læse det ud af teksten
    // på to sprog — den skal kunne se *sandheden*, ikke ordene.
    flyttet: flyttet ? flyttet[1] : null,
    harSpot: !!res.querySelector('[data-ti-spot]'),
    delta: deltaAttribut(),
  };
}
// Før/nu-linjen læses samme sted som resten: fra `innerHTML`, aldrig fra en
// variabel i kernen — ellers dømmer porten kernens egen hensigt i stedet for
// det læseren faktisk ser.
function deltaAttribut() {
  const h = nodes['result'].innerHTML || '';
  const d = /data-ti-delta="([^"]*)"/.exec(h);
  const s = /<span class="ti-delta"[^>]*>([\s\S]*?)<\/span>/.exec(h);
  const dele = d ? d[1].split('|') : [];
  const num = (v) => parseFloat(String(v).replace(',', '.'));
  return {
    harDelta: !!d,
    foer: dele.length === 2 && !isNaN(num(dele[0])) ? num(dele[0]) : null,
    nu: dele.length === 2 && !isNaN(num(dele[1])) ? num(dele[1]) : null,
    tekst: s ? s[1].replace(/<[^>]*>/g, '') : '',
  };
}
function spotMaal() {
  uploadBillede(todeltVandret(400, 300, '#161a22', '#ebeef2'));
  nodes['fg'].value = '#ffffff'; nodes['fg'].fire('input');
  nodes['text'].value = 'Dark'; nodes['text'].fire('input');
  nodes['fontsize'].value = 'large'; nodes['fontsize'].fire('change');
  // Den lyse halvdel: hvid tekst på #ebeef2 er ca. 1,1:1 mod kravet 3:1.
  nodes['cv'].fire('mousedown', { clientX: 340, clientY: 260, preventDefault: function () {} });
  const foer = spotLaes();
  const knap = nodes['result'].querySelector('[data-ti-spot]');
  if (!knap) return { harKnap: false, foer: foer };
  knap.click();
  const efter = spotLaes();
  // Og så bruteren selv: han trækker teksten tilbage. Kimens egen beskrivelse
  // af *sin* flytning skal væk, ellers står der «jeg satte den på det bedste
  // sted» under et tal fra et helt andet sted — præcis den fejl reviewen
  // fandt med sløret ved billedskift.
  nodes['cv'].fire('mousedown', { clientX: 340, clientY: 260, preventDefault: function () {} });
  const rykket = spotLaes();
  return { harKnap: true, foer: foer, efter: efter, rykket: rykket };
}
const spotMaalt = spotMaal();

/* ---- Før → nu: beviset på at kernens egen rettelse gjorde forskel -----
 *
 * Efter «Fix it» sagde værktøjet «I put a 24 % dark layer behind the text and
 * measured again» og så **kun** det nye tal. Hvad rettelsen havde vundet, var
 * væk — bruteren havde set 1,16:1 og så 3,04:1, men intet sted stod at de to
 * hørte sammen. Det er præcis den fejlform scannerens «siden din sidste
 * scanning» blev bygget for (40f24d0): et nyt tal uden en forskel svarer ikke på
 * «virkede det?». Og for en læser der skal tage tallet videre til sin kunde er
 * *forskellen* det interessante tal, ikke det nye.
 *
 * To kæder, fordi de to veje ind i kernen er to forskellige indgreb:
 *   1. «Fix it» — kernen lægger et slør eller skifter tekstfarven
 *   2. «Find det bedste sted» — kernen flytter teksten
 * Begge skal skrive begge tal, og begge skal tie når bruteren selv griber ind.
 *
 * Læst som tal (`data-ti-delta="a|b"`), ikke som tekst: dommen skal kunne se
 * *sandheden*, og en dansk læser skal ikke kunne få den engelske sætning. */
function deltaLaes() {
  const res = nodes['result'];
  const m = /<strong>([0-9.,]+):1<\/strong>/.exec(res.innerHTML);
  return {
    fik: m ? parseFloat(m[1].replace(',', '.')) : null,
    delta: deltaAttribut(),
  };
}
function deltaMaal() {
  // Samme foto som spot-kæden bruger (todelt mørk→lys), fordi det er den
  // eneste der både fejler *og* kan rettes: hvid tekst på den lyse halvdel er
  // ca. 1,1:1 mod kravet 4,5:1, og intet tekstfarve består begge ende af et
  // todelt billede — så rettelsen bliver et slør, og tallet flytter sig.
  uploadBillede(todeltVandret(400, 300, '#161a22', '#ebeef2'));
  nodes['fg'].value = '#ffffff'; nodes['fg'].fire('input');
  nodes['text'].value = 'Dette er en overskrift'; nodes['text'].fire('input');
  nodes['fontsize'].value = 'small'; nodes['fontsize'].fire('change');
  nodes['cv'].fire('mousedown', { clientX: 340, clientY: 260, preventDefault: function () {} });
  const foer = deltaLaes();
  const knap = nodes['result'].querySelector('[data-ti-fix]');
  if (!knap) return { harKnap: false, foer: foer };
  knap.click();
  const efter = deltaLaes();
  // Bruteren tager over selv: han rører farvefeltet, og både beskrivelsen og
  // før/nu-linjen skal væk — ellers står «før 1,16:1» under et tal der ikke
  // længere stammer fra den pladsering kernen lagde.
  nodes['fg'].value = '#ffff00'; nodes['fg'].fire('input');
  const rykket = deltaLaes();
  return { harKnap: true, foer: foer, efter: efter, rykket: rykket };
}
const deltaMaalt = deltaMaal();

/* ---- Farvekoden: den målte tekstfarve som noget bruteren kan tage med -----
 *
 * Værktøjet målte, rettede og sagde «#1a1a1a» i en sætning, men skrev ingen
 * kode nogen sted — så bruteren måtte selv finde farvefeltet og skrive koden
 * af i Figma. Klarer han det, har han gjort værktøjets arbejde for de tre
 * euro den koster ham. Det er den konkrete uge, 3/10 (9a1c7f7).
 *
 * Læst som **tal og attributter**, aldrig som sætninger: dommen skal kunne se
 * sandheden, og en dansk læser må ikke få den engelske tekst. Farvefeltets
 * værdi læses her i harnessen, ikke i kernen — ellers ville porten dømme
 * kernens egen vilje (`hexNu` *er* `$('fg').value`) i stedet for at dømme det
 * der står på skærmen.
 *
 * `praem` læses i hele resultatet og **ikke** i `knap[0]`: farveprøven er en
 * `<span>` *inde i* knappen, så den står ikke i knappens egen åbningstag. Læst
 * i `knap[0]` var den altid `null`, og løftet «prøven er den samme kode» blev
 * da talt uden at dømme noget — præcis det porten her er skrevet til at finde.
 * Målt 3/10 på denne linje. */
function hexLaes() {
  const h = nodes['result'].innerHTML || '';
  const knap = /<button[^>]*\bdata-ti-hex="([^"]*)"[^>]*>/.exec(h);
  const synlig = /<code>([^<]*)<\/code>/.exec(h);
  const praem = /class="ti-swatch"[^>]*background:\s*([^;"']*)/.exec(h);
  const tal = /<strong>([0-9.,]+):1<\/strong>/.exec(h);
  return {
    harKnap: !!knap,
    // Punkt 2 i husets kvalitetsliste: knappen *gør* noget (kopierer), så
    // den er en `<button>` — ikke en `<span>` der ligner som en knap.
    erKnap: knap ? /<button[^>]*\btype="button"/.test(knap[0]) : false,
    hex: knap ? knap[1] : null,
    // Præcis det bruteren *læser*: koden i knappen. Attributtet er kun til
    // for dommen, så en kode der er i attributtet men ikke på skærmen er
    // en ulovet påstand — punkt 11.
    synlig: synlig ? synlig[1] : null,
    praem: praem ? praem[1].trim() : null,
    // Farvefeltets egen værdi, som bruteren kan se i samme skærmbillede.
    felt: String(nodes['fg'].value || '').toLowerCase(),
    fik: tal ? parseFloat(tal[1].replace(',', '.')) : null,
  };
}
function hexMaal() {
  // Samme todelte foto som de to andre kæder: hvid tekst på den lyse halvdel
  // fejler, så «Fix it» har noget at rette — og `applyFix()` skriver *altid*
  // en ny tekstfarve til feltet, også når rettelsen er et slør. Det er derfor
  // koden kan dømmes for at *følge* rettelsen: ellers ville koden være den
  // fra før trykket, mens bruteren kopierer en farve der ikke er den han ser.
  uploadBillede(todeltVandret(400, 300, '#161a22', '#ebeef2'));
  nodes['fg'].value = '#ffffff'; nodes['fg'].fire('input');
  nodes['text'].value = 'Dette er en overskrift'; nodes['text'].fire('input');
  nodes['fontsize'].value = 'small'; nodes['fontsize'].fire('change');
  nodes['cv'].fire('mousedown', { clientX: 340, clientY: 260, preventDefault: function () {} });
  const foer = hexLaes();
  const knap = nodes['result'].querySelector('[data-ti-fix]');
  if (!knap) return { harFix: false, foer: foer };
  knap.click();
  const efter = hexLaes();
  return { harFix: true, foer: foer, efter: efter };
}
const hexMaalt = hexMaal();

// Demo-noten igen *efter* at bruteren har valgt sit eget billede. Det er den
// anden halvdel af dommen: noten skal forsvinde, fordi «measured against the
// lightest and darkest pixels under your letters» først er sandt når der er
// et billede der er bruterens. Et upload her — også efter at state er flyttet
// — gør dommen uafhængig af hvilken måling der kørte sidst.
function demoEfterUpload() {
  Img.next = ensfarvet(300, 150, '#ffffff');
  nodes['file'].files = [{ type: 'image/png' }];
  nodes['file'].fire('change', { target: { files: nodes['file'].files } });
  const h = nodes['result'].innerHTML || '';
  const m = /data-ti-demo>([\s\S]*?)</.exec(h);
  return { tekst: m ? m[1] : null, harTal: /<strong>[0-9.,]+:1<\/strong>/.test(h) };
}

// ---- To tekstblokke ------------------------------------------------------
// Den mest almindelige reelle case: to overlejrende tekster på ét foto.
// Før 3/10 målte værktøjet kun den *sidste*, så bruteren fik ét tal for to
// tekster og vidste ikke om den anden var ulæselig. Her måles begge, på
// hver sin del af et todelt billede: blok 1 over den mørke halvdel skal
// give 21:1, blok 2 over den lyse 1:1. Kan de to tal ikke være forskellige,
// læser værktøjet den ene blok to gange — eller kun den ene.
function toBlokke() {
  function laes(boks) {
    const m = /<strong>([0-9.,]+):1<\/strong>/.exec(boks.innerHTML || '');
    return m ? parseFloat(m[1].replace(',', '.')) : null;
  }
  Img.next = todeltVandret(400, 300, '#000000', '#ffffff');
  nodes['file'].files = [{ type: 'image/png' }];
  nodes['file'].fire('change', { target: { files: nodes['file'].files } });
  nodes['fontsize'].value = 'large'; nodes['fontsize'].fire('change');
  // De to blokke har *forskellige* farver. Det er ikke pynt: en mutation der
  // læser blok 1s farve i stedet for blok 2s er ækvivalent, når begge er
  // hvide, så den ville være grøn på det langt meste billeder. Med sort mod
  // hvid kan de to tal ikke forveksles, og mutationen kan gå rød.
  nodes['fg'].value = '#ffffff'; nodes['fg'].fire('input');
  nodes['fg2'].value = '#000000'; nodes['fg2'].fire('input');
  nodes['text'].value = 'Overskrift'; nodes['text'].fire('input');
  nodes['text2'].value = 'Undertekst'; nodes['text2'].fire('input');
  // Blok 1 over den mørke venstre halvdel, blok 2 over den lyse højre.
  const plac = function (x, y) {
    nodes['cv'].fire('mousedown', { clientX: x, clientY: y, preventDefault: function () {} });
  };
  // Blok 0 er den aktive fra start, så *dens* klik flytter den.
  plac(20, 240);                       // venstre, mørk halvdel
  const foerste = laes(nodes['result']);
  // Så vælges blok 2 med dens **egen** vælger, og næste klik flytter *den*.
  // Den har sort tekst og skal også stå på den mørke halvdel, så de to tal
  // er 21:1 og 1:1 fra det samme billede. Kan de ikke være forskellige,
  // læser værktøjet den ene blok to gange: bruteren får ét tal for to
  // tekster igen, og det er præcis den fejl værktøjet havde.
  const knap = (nodes['result2'] || { querySelector: function () { return null; } })
    .querySelector('[data-ti-pick]');
  if (knap) knap.click();
  plac(20, 240);
  const anden = laes(nodes['result2']);
  // Blok 2 er stadig den valgte, så næste klik flytter den igen — og kun
  // den. Den skal *helt* ud i den lyse halvdel: tekstkassen er så bred at
  // den løber ind i den mørke, og værktøjet svarer da korrekt på det værste
  // par — et scenarie der ikke kan skelne to blokke fra hinanden. Blok 0
  // skal stå helt uændret: bruterens eget greb må ikke slette den måling han
  // lige lavede.
  plac(360, 240);
  const efterFoerste = laes(nodes['result']);
  const efterAnden = laes(nodes['result2']);
  const valgt = nodes['result2'] ? nodes['result2'].querySelector('[data-ti-pick]') : null;
  const valgt1 = nodes['result'] ? nodes['result'].querySelector('[data-ti-pick]') : null;
  return {
    harBokse: blokAntalErTo(),
    harVaelger: !!knap,
    foerste: foerste, anden: anden,
    efterFoerste: efterFoerste, efterAnden: efterAnden,
    andenTrykket: valgt ? valgt.getAttribute('aria-pressed') : null,
    foersteTrykket: valgt1 ? valgt1.getAttribute('aria-pressed') : null,
  };
}
function blokAntalErTo() {
  // `getElementById` giver en ny stub for ukendte id'er, så «feltet findes»
  // kan ikke dømmes ved at kernens egen tæller er sand — den er alt sand i
  // harnessen. Det porten kan dømme er *markup'en*: to resultatkasser med et
  // tal hver. Det er det bruteren ser.
  return /<strong>[0-9.,]+:1<\/strong>/.test((nodes['result'] || {}).innerHTML || '') &&
         /<strong>[0-9.,]+:1<\/strong>/.test((nodes['result2'] || {}).innerHTML || '');
}
const blokMaalt = toBlokke();

// Gradienten måles **sidst**, fordi den skriver `img` — så den efterlader
// værktøjet i gradienttilstand. Det er i sig selv værd at dømme: en bruter der
// har brugt gradienten og så uploader et foto, skal se fotoet igen.
//
// Dommen er **tærskelbaseret, ikke hardkodet**: to forventede tal ville være
// min egen håndregning af WCAG-formlen, og den ville være lige så skrøbelig
// som porten er dømt for alt andet. Her dømmes derimod på *hvad læseren ser* —
// består den eller fejler den — og på at de to placeringer ikke kan give det
// samme svar. Det sidste er bæredygtigt: en mutation der maler gradienten
// flad, eller bytter om på vinklen, eller tager gennemsnittet af endepunkterne,
// giver enten to ens svar eller to forkerte domme.
const GRAD_TOP = 2;          // tekstkassen i toppen af en 900×420 flade
const GRAD_NED = 360;        // …og i bunden
function læsGradient(fra, til, vinkel, tekst, x, y, stor) {
  nodes['fontsize'].value = stor ? 'large' : 'small';
  nodes['fontsize'].fire('change', {});
  return spoergGradient(fra, til, vinkel, '#ffffff', tekst, x, y);
}
const gradMaalt = (function () {
  // 0° peger opad, så startfarven ligger i *bunden*: hvid tekst i toppen står
  // på den mørke ende og består, i bunden på den lyse og fejler. Ved 180° er
  // det omvendt — og det er den forskel, der gør vinklen målbar.
  const FRA = '#ffffff', TIL = '#000000', TEKST = 'Din overskrift her';
  const top0 = læsGradient(FRA, TIL, 0, TEKST, 0, GRAD_TOP, true);
  const ned0 = læsGradient(FRA, TIL, 0, TEKST, 0, GRAD_NED, true);
  const top180 = læsGradient(FRA, TIL, 180, TEKST, 0, GRAD_TOP, true);
  const ned180 = læsGradient(FRA, TIL, 180, TEKST, 0, GRAD_NED, true);
  // **Værste ende, ikke gennemsnit.** Samme gradient i to placeringer langs
  // aksen med `fontsize` på «normal» (krav 4,5:1): i den mørke ende består
  // hvid tekst, i den lyse fejler den. En måling der tog gennemsnittet ville
  // sige «består» begge steder — og det er præcis det løfte værktøjet ikke
  // må give, siden bruteren skal kunne regne sig frem til hvor teksten er
  // ulæselig.
  const mork = læsGradient('#1c2029', '#a8adb5', 90, 'Hej', 10, 200, false);
  const lys = læsGradient('#1c2029', '#a8adb5', 90, 'Hej', 820, 200, false);
  // Og tilbage til fotoet, så skiftet ikke er destruktivt.
  nodes['bgmode'].value = 'image'; nodes['bgmode'].fire('change', {});
  const foto = laesResultat();
  return {
    top0: top0, ned0: ned0, top180: top180, ned180: ned180,
    mork: mork, lys: lys, foto: foto,
    felterSynlige: (nodes['tigrad'].style || {}).display || '',
  };
})();

console.log(JSON.stringify({
  svar: svar, fix: fixSvar,
  demo: { start: demoStart, efterUpload: demoEfter },
  sekventiel: {
    efter: sekB1, refer: renB2,
    farve: sekFarve, farveEfterFix: farveEfterFix,
    fixA: fixA,
  },
  download: dlMaal,
  mark: markMaalt,
  spot: spotMaalt,
  delta: { fix: deltaMaalt },
  hex: { fix: hexMaalt },
  blok: blokMaalt,
  gradient: gradMaalt,
}));
"""

# Tre mutationer. Hver især en reel fejl i samplingslogikken, og porten
# SKAL blive rød på alle fire — ellers dommer den ingenting.
#
# De første to mutationer var målt OK, men viste sig at være *ækvivalente*:
# at læse `photo` fra det lag der også indeholder teksten ændrer intet, fordi
# dækningskortet (`glyph`) alligevel springer præcis de pixels over som
# teksten har tilføjet. En mutation der ikke kan gøre en forskel er ikke et
# bevis, så de er byttet ud med de fire fejl der faktisk kan opstå — blandt
# andet den gamle kode, som er mutation 2.
MUTATIONER = (
    # Bogstaverne regnes som baggrund, fordi begge lag læses fra samme
    # overflade. Uden et dækningskort er der intet der siger hvad der er
    # tekst. Fanges af hvid tekst over den mørke halvdel: svaret bliver 1:1
    # fordi de hvide bogstaver tæller som den lyseste baggrund.
    # Værktøjet måler i billedets øverste venstre hjørne i stedet for hvor
    # teksten står. Det er den fejl læseren mærker først: flytter du teksten
    # hen over en mørk flæk, siger værktøjet det samme som da den stod over
    # den lyse. Fanges af de to todelte domme, der forventer hhv. 21:1 og 1:1.
    ("måler i hjørnet i stedet for hvor teksten står",
     "      var x = Math.max(0, Math.round(laegX(i))), y = Math.max(0, Math.round(laegY(i)));",
     "      var x = 0, y = Math.max(0, Math.round(laegY(i)));"),
    # Den gamle kode i dens egen, kortere form: ét lag med billede *og* tekst,
    # brugt som både baggrund og dækningskort, uden filter. Det er præcis
    # fejlen der gav 1,47:1 for hvid tekst på hvid, og for hvid tekst over
    # den mørke halvdel tæller de hvide bogstaver som den lyseste baggrund:
    # 1:1 i stedet for 21:1.
    ("læser farverne fra det lag der indeholder teksten",
     "      ctx.clearRect(0, 0, cv.width, cv.height);\n"
     "      ctx.drawImage(img, 0, 0, cv.width, cv.height);\n"
     "      var photo = ctx.getImageData(box.x, box.y, box.w, box.h).data;\n"
     "      // Pass 2 — the letters alone, so alpha is the glyph coverage.\n"
     "      drawTextLayer(i);",
     "      draw();\n"
     "      var photo = ctx.getImageData(box.x, box.y, box.w, box.h).data;\n"
     "      var glyph = ctx.getImageData(box.x, box.y, box.w, box.h).data;\n"
     "      if (false) drawTextLayer();"),
    # Bemærk hvad porten tidligere IKKE dømte: at `worst` springer den
    # mørkeste baggrund over og svarer på den bedste. Det var umærkeligt
    # på de ensfarvede og todelte billeder, fordi de andre domme har hvid
    # tekst — og med hvid tekst er den *lyseste* baggrund altid den
    # dårligste, så at fjerne den mørkeste fra listen ændrer intet.
    # Mutation 4 er derfor sort tekst over et gradient, hvor rollerne
    # bytter om: her er den mørkeste den dårligste, så springer man den
    # over, svarer værktøjet 21:1 oveni en baggrund der indeholder rent
    # sort. Det er den fejl en læser aldrig ville få at vide.
    ("springer den mørkeste baggrund over og svarer på den bedste",
     "      [visMin, visMax].forEach(function (c, k) {",
     "      [visMax].forEach(function (c, k) {"),
    # Flytter tekstkassen opad i stedet for at klippe den. Det er den fejl
    # der læseren mærker først på et fladt billede: kassen løber op i det
    # hvide og svaret falder fra 21:1 til 1:1.
    ("flytter tekstkassen opad i stedet for at klippe den",
     "      var x = Math.max(0, Math.round(laegX(i))), y = Math.max(0, Math.round(laegY(i)));",
     "    var x = Math.max(0, Math.round(laegX(i))), y = Math.max(0, Math.min(cv.height - fontSizePx() - 1, Math.round(laegY(i)))); "),
)


def byg_kode(kode: str) -> str:
    return (HARNESS.replace("%%SIDENS_KODE%%", kode)
            .replace("__FARVEPAR__", json.dumps([list(p) for p in FARVEPAR]))
            .replace("__FLADT__", json.dumps(list(FLADT)))
            .replace("__GRADIENT__", json.dumps(list(GRADIENT)))
            .replace("__GRADIENT_TEKST__", json.dumps(GRADIENT_TEKST))
            .replace("__TODELT__", json.dumps(list(TODELT))))


def koer(kode: str, hele: bool = False):
    """Kør sidekoden i Node-harnessen og læs de tal den viser.

    `hele=True` giver hele svaret (samplings-tallene *og* fix-dommen); ellers
    kun tallene, fordi det er dem de fleste kald vil have.
    """
    if shutil.which("node") is None:
        raise SystemExit("FEJL: node mangler. Porten dømmer den kode der "
                         "factisk ships, så den kan ikke springe Node over.")
    with tempfile.TemporaryDirectory() as tmp:
        fil = Path(tmp) / "harness.mjs"
        fil.write_text(byg_kode(kode), encoding="utf-8")
        p = subprocess.run(["node", str(fil)], capture_output=True, text=True,
                           timeout=120, cwd=ROOT)
    if p.returncode != 0:
        raise SystemExit("FEJL: Node-harnessen døde:\n" + (p.stderr or p.stdout)[:2000])
    linje = [l for l in p.stdout.splitlines() if l.startswith("{")]
    if not linje:
        raise SystemExit("FEJL: harnessen skrev intet resultat:\n" + p.stdout[:2000])
    # Harnessen skriver både samplings-tallene og fix-dommen i ét objekt, så
    # ét kørsel giver dem begge. Uden `hele` får kald kun tallene — dem er
    # `dom()` bygget til, og dem de mutationer i `self_test()` sammenligner.
    r = json.loads(linje[-1])
    return r if hele else r["svar"]


def dom_fix(fix: list[dict]) -> list[str]:
    """Døm «Fix it»-knappen på den kode der faktisk kører.

    Fire krav, og de er fire forskellige fejlformer:

    1. **Den fejler i udgangspunktet.** Ellers ville «rettelsen» være en knap
       der trykkes på et billede, der allerede består, og dommen ville være
       grøn af den grund alene.
    2. **Der står en knap at trykke på.** Ellers har kernen skrevet en
       beskrivelse uden en handling, og det er den fejl værktøjet havde
       før 3/10 i en anden form: et råd uden en vej.
    3. **Efter trykket består kravet.** Dommen læser tallet i `innerHTML` —
       altså det der står på skærmen — ikke en intern variabel. Det er den
       *ny måling af det samme billede*, ikke et løfte om at et bedre tal
       ville komme, og det er præcis forskellen på disse to.
    4. **Forbedringen er reel.** Et krav på 4,5:1 der en mutation løser ved at
       sætte farven til rent sort, ville også bestå (3). Derfor skal den nye
       måling ligge *mellem* kravet og den gamle — altså tæt på grænsen, som
       er det en god rettelse er, og ikke langt over den. En mutation der
       "løser" billedet ved at gøre alt sort ville landet over 10:1 og være
       dømt rød; en mutation der intet gør, lander under kravet og er dømt
       rød af (3).
    """
    fund: list[str] = []
    for f in fix:
        krav = f["krav"]
        foer, efter = f.get("foer"), (f.get("efter") or {})
        if foer is None:
            fund.append(f"{f['navn']}: værktøjet viser intet forholdstal før rettelsen")
            continue
        if foer >= krav:
            fund.append(f"{f['navn']}: billedet består allerede {foer:.2f}:1 "
                        f"(krav {krav}:1), så «fix»-knappen dømmer ingenting")
            continue
        if not efter.get("harKnap"):
            fund.append(f"{f['navn']}: der står ingen «fix»-knap at trykke på")
            continue
        ny = efter.get("fik")
        if ny is None:
            fund.append(f"{f['navn']}: knappen blev trykket, men der står intet tal bagefter")
        elif ny < krav:
            fund.append(f"{f['navn']}: efter «fix» står der {ny:.2f}:1, "
                        f"men kravet er {krav}:1")
        elif ny > krav * 2:
            fund.append(f"{f['navn']}: «fix» landede på {ny:.2f}:1 — mere end "
                        f"dobbelt op mod kravet {krav}:1. Det er ikke en god "
                        f"rettelse, det er en der ødelægger billedet")
    return fund


def dom_sekventiel(s: dict | None) -> list[str]:
    """Døm at et nyt billede måles på *egne* betingelser.

    Fundet i review 3/10 og målt i rigtig Chromium på den byggede side:
    `loadFile()` nulstillede hverken `scrim` eller `lastFix`, så sløret fra foto A
    blev tegnet på foto B og `.ti-fixed`-teksten beskrev det under et tal der
    ikke stammer fra B. Målt i browseren: foto A efter fix 4,52:1, foto B
    **1,52:1** med «13 % mørkt lag» under sig. Målt i *denne* port, der bruger
    andre billeder end browseren: **5,99:1 mod egne 1,85:1**. Begge tal er
    rigtige for deres egen måling, og de skal ikke sammenlignes.

    Tre krav, og de er tre forskellige fejlformer:

    1. **Tallet på B er B's eget.** Ikke «bedre», ikke «værre» — det samme
       tal B viser uden en tidligere rettelse. En tærskel ville være en svag
       dom: en mutation der lagde sløret *tyndere* kunne nødes ned under den,
       og en der lagde det tykkere ville nødes op over den, uden at nogen af
       dem er den fejl læseren mærker.
    2. **Beskrivelsen er væk.** `.ti-fixed` er kernens egen forklaring på
       *dens* indgreb. Står den på et billede den ikke har rørt, er den en
       påstand om et input der ikke fandtes — punkt 11 i kontrakten.
    3. **Knappen er tilbage.** Ellers har bruteren trykket på «fix» på ét
       billede og kan ikke trykke på det næste, fordi kernen tror den
       allerede har gjort arbejdet.

    Der dømmes **tre** løfter, og de tælles på rigtige resultater som altid i
    denne port.
    """
    fund: list[str] = []
    if not s:
        return ["sekventiel: harnessen leverede ingen to-billeders-kæde at dømme"]
    efter, refer = s.get("efter") or {}, s.get("refer") or {}
    if efter.get("fik") is None:
        fund.append("sekventiel: efter et nyt billede står der intet forholdstal "
                    "på skærmen — læseren kan ikke se om B består")
    if refer.get("fik") is None:
        fund.append("sekventiel: referencemålingen af B gav intet tal, så de to "
                    "målinger kan ikke sammenlignes")
    if efter.get("fik") is not None and refer.get("fik") is not None:
        afvigelse = abs(efter["fik"] - refer["fik"])
        if afvigelse > TOLERANS:
            fund.append(f"sekventiel: foto B viser {efter['fik']:.2f}:1 når det "
                        f"uploades efter et fix på foto A, men {refer['fik']:.2f}:1 "
                        f"når det måles for sig selv. Sløret fra A ligger stadig "
                        f"tegnet på B, så tallet er ikke en måling af det "
                        f"bruteren har lavet")
    if efter.get("harFast"):
        fund.append("sekventiel: der står en `.ti-fixed`-tekst under foto B, men "
                    "kernen har ikke lagt et lag på B — beskrivelsen hører til "
                    "et tidligere billede")
    if not efter.get("harKnap"):
        fund.append("sekventiel: der står ingen «fix»-knap på foto B, så bruteren "
                    "kan ikke rette det næste billede")
    return fund


def dom_download(d: dict | None) -> list[str]:
    """Døm at den rettede grafik også *kommer ud* som en fil.

    Før 3/10 endte værktøjet ved et tal. Bruteren rettede teksten, fik et grønt
    tal — og skulle bagefter selv finde ud af, hvordan han fik sit billede *med
    sin egen rettelse* ud af værktøjet igen. Det er hele vejen fra et problem
    til et billede, og det var det sidste stykke.

    Tre løfter, tre forskellige fejlformer:

    1. **Der står en knap.** Ellers har kernen skrevet en mulighed uden en
       vej, som en råd uden en handling.
    2. **Der kommer en fil ved tryk.** Ikke bare en knap: klikket skal sætte
       `href` på et anchor med et `download`-navn der ender på `.png`. En
       `data:image/jpeg` ville hedde `.png` og være en JPEG, og det er den
       slags løfte filnavnet alene ikke kan holde.
    3. **Filen er det bruteren så.** Dommen tæller pixelne i den hentede
       buffer: de skal alle være uopaque (et billede med tekst og slør), og
       de skal afvige fra det rå foto (teksten er med). `sampleContrast()`
       efterlader bogstaverne på en *ryddet* baggrund, så en eksport der
       springer `draw()` over er næsten helt gennemsigtig — filen ville hedde
       «din rettede grafik» og vise en næsten tom baggrund med hvid tekst.
    """
    fund: list[str] = []
    if not d:
        return ["download: harnessen leverede ingen download at dømme"]
    if not d.get("harKnap"):
        fund.append("download: der står ingen download-knap, så den rettede "
                    "grafik kan ikke hentes ud af værktøjet")
        return fund
    a = d.get("anker")
    if not a:
        fund.append("download: knappen blev trykket, men ingen fil blev afleveret "
                    "— intet anchor fik et `href`")
        return fund
    if not str(a.get("href", "")).startswith("data:image/png"):
        fund.append(f"download: filen kommer som `{str(a.get('href'))[:22]}` "
                    "og ikke som PNG, så et filnavn der ender på .png ville være "
                    "en løgnavn")
    navn = str(a.get("download") or "")
    if not navn.endswith(".png") or navn == ".png":
        fund.append(f"download: filen hedder `{navn}`, så den kan ikke bruges "
                    "andre steder — et download-navn skal ende på .png")
    total = d.get("total") or 0
    uopaque = d.get("uopaque") or 0
    if total and uopaque < total:
        fund.append(f"download: kun {uopaque} af {total} pixel i den hentede fil "
                    "er dækket. Det er bogstaverne på en ryddet baggrund, ikke "
                    "billedet med rettelsen — bruteren får en næsten tom fil")
    if not (d.get("afvigelser") or 0):
        fund.append("download: den hentede fil er pixel for pixel det rå foto, "
                    "så hverken den nye tekstfarve eller sløret er med")
    return fund


# Den tekstfarve og de to baggrunde `markeringsMaal()` stiller op: lys tekst på
# hvid er 1,14:1 og på sort 14,63:1. Den *dårligste* baggrund er altså den
# hvide, og det er den porten kræver feltet over. Tallene er ikke taget fra
# kernen — de er regnet med WCAG-formlen i selftestens `ratio()`.
MARK_TEKST = "#e6e6e6"
MARK_BEDST = "#000000"   # sort bånd: den bedste baggrund i opstillingen
MARK_VAERST = "#ffffff"  # hvid: den dårligste


def dom_mark(m: dict | None) -> list[str]:
    """Døm at feltet viser *hvor* fejlen sidder — og at det er et valg for sig.

    Et tal på 1,10:1 siger at noget er galt, men ikke hvor. Det er præcis det
    et bureau der gennemgår en kundes fotos mangler, når beskeden skal videre
    til designeren uden at nogen åbner værktøjet igen.

    Fire løfter, fire fejlformer:

    1. **Der står en knap med en tekst.** Ellers er der ingen handling, kun et
       løfte i teksten.
    2. **Den rene fil har intet felt.** Dobbeltværdien af det nye valg er, at
       bruteren stadig kan få den grafik han rettede. Et felt der ligger i
       begge filer gør de to knapper til én.
    3. **Feltet sidder over det dårligste sted.** Porten læser den rene fils
       farve under feltets midte og kræver den dårligste af de to baggrunde —
       ikke blot «et sted i tekstkassen», for sådan et krav kan en markering
       i hjørnet af boksen ikke opfylde.
    4. **Forhåndsvisningen er ren igen.** Ellers står der et felt på bruterens
       billede resten af tiden, og det ligner en del af hans design.
    """
    fund: list[str] = []
    if not m:
        return ["markering: harnessen leverede ingen markering at dømme"]
    if not m.get("harKnap"):
        fund.append("markering: der står ingen knap, der henter billedet med det "
                    "dårligste sted markeret")
        return fund
    if not m.get("harRen"):
        fund.append("markering: den rene download-knap er væk, så markeringen "
                    "har taget dens plads og de to valg er blevet ét")
    if not str(m.get("etiket") or "").strip():
        fund.append("markering: knappen står i markup'en uden tekst, så bruteren "
                    "ser en knap uden at vide hvad den gør")
    if (m.get("renMark") or 0) > 0:
        fund.append(f"markering: den rene fil har {m['renMark']} markeringspixel, "
                    "så den grafik bruteren rettede er ikke længere den han "
                    "rettede — de to valg er ét")
    if not (m.get("markMark") or 0):
        fund.append("markering: den markerede fil har ikke ét eneste felt, så "
                    "bruteren får det samme billede som uden den knap")
    elif str(m.get("under") or "").lower() != MARK_VAERST:
        fund.append(f"markering: feltet ligger over `{m.get('under')}` og ikke "
                    f"over `{MARK_VAERST}`. Den farve er den baggrund bruteren "
                    "har mindst kontrast imod — feltet skal pege på den")
    if (m.get("liveMark") or 0) > 0:
        fund.append(f"markering: {m['liveMark']} feltpixel står stadig på "
                    "forhåndsvisningen efter klikket, så bruterens billede har "
                    "fået en ramme han ikke bad om")
    return fund


def dom_spot(sp: dict | None) -> list[str]:
    """Døm at værktøjet finder *stedet*, ikke kun tallet.

    Et foto består under den ene halvdel af bogstaverne og fejler under den
    anden. Før 3/10 var svaret på «hvad er tallet her?» det eneste svar, og
    bruteren måtte selv trække teksten rundt for at finde ud af, om den
    overhovedet *kunne* ligge et andet sted. Det er hele det arbejde, værktøjet
    er lavet for at fjerne — «Fix it» og «Download» løser og afleverer, men
    ingen af dem vidste, hvor teksten skulle stå.

    Fire løfter, fire forskellige fejlformer:

    1. **Der står en knap.** Ellers har kernen skrevet et løfte uden en vej.
    2. **Efter trykket står der et bedre tal.** Ikke bare et andet tal: et
       dårligere tal ville være en rettelse der ødelægger billedet, og et uændret
       tal en knap der gør ingenting. Derfor kræves en *streng* forbedring.
    3. **Beskrivelsen er der, og den taler om det samme.** `.ti-fixed` skal
       findes, og skal indeholde præcis det tal der står på skærmen — ellers er
       den en påstand om en måling af noget andet (punkt 11).
    4. **Beskrivelsen forsvinder, når bruteren selv flytter teksten.** Ellers står
       «jeg satte den på det bedste sted» under et tal fra en pladsering
       bruteren selv har valgt. Samme fejl som sløret ved billedskift.
    """
    fund: list[str] = []
    if not sp or not sp.get("harKnap"):
        return ["find-spot: der står ingen «find det bedste sted»-knap, så "
                "bruteren skal selv trække teksten rundt for at finde ud af, "
                "om den overhovedet kan ligge et andet sted"]
    foer, efter = sp.get("foer") or {}, sp.get("efter") or {}
    rykket = sp.get("rykket") or {}
    a, b = foer.get("fik"), efter.get("fik")
    if a is None or b is None:
        fund.append("find-spot: der står intet forholdstal på skærmen hverken "
                    "før eller efter trykket")
        return fund
    if b <= a:
        fund.append(f"find-spot: efter trykket står der {b:.2f}:1, som ikke er "
                    f"bedre end de {a:.2f}:1 den stod med før. Knappen flyttede "
                    "teksten til et sted der ikke læses bedre")
    if b < 3.0:
        fund.append(f"find-spot: efter trykket står der {b:.2f}:1, så det bedste "
                    "sted på billedet fejler stadig kravet på 3:1 for stor tekst")
    if not efter.get("harFast"):
        fund.append("find-spot: kernen flyttede teksten uden at sige det, så "
                    "bruteren står med et nyt tal og ingen forklaring")
    elif efter.get("flyttet") != "1":
        fund.append("find-spot: tallet blev bedre, men kernen skriver at den "
                    "ikke flyttede noget. Enten står teksten et andet sted end "
                    "bruteren tror, eller han får at vide at han selv har fundet "
                    "det bedste sted — og det er kun det ene af dem der er sandt")
    else:
        # Tallet i beskrivelsen skal være *samme* måling som den på skærmen.
        # Både komma og punktum accepteres, fordi den danske side bruger komma.
        to = f"{b:.2f}"
        if to not in efter.get("fast", "") and to.replace(".", ",") not in efter.get("fast", ""):
            fund.append(f"find-spot: beskrivelsen nævner ikke det tal der står på "
                        f"skærmen ({to}:1), så den beskriver en anden måling")
    if rykket.get("harFast"):
        fund.append("find-spot: beskrivelsen står stadig under et tal, efter at "
                    "bruteren selv har flyttet teksten — den taler om kernens "
                    "egen flytning og ikke om det han nu ser")
    return fund


def dom_delta(fil: str, d: dict | None) -> list[str]:
    """Døm at rettelsen siger *hvad den rettede*.

    Efter «Fix it» sagde værktøjet «I put a 24 % dark layer behind the text and
    measured again» og viste **kun** det nye tal. Hvad rettelsen havde vundet,
    var væk: bruteren så 1,16:1 og så 3,04:1, men intet stod at de to hørte
    sammen. Det er samme fejlform som scannerens «siden din sidste scanning» var
    løst med 3/10 (`40f24d0`) — et nyt tal uden en forskel svarer ikke på
    «virkede det?». Og for en læser der skal tage tallet videre til sin kunde er
    *forskellen* det interessante tal, ikke det nye.

    To kæder, fordi kernen har to forskellige indgreb — «Fix it» lægger et slør
    eller skifter farven, «Find det bedste sted» flytter teksten — og de to kan
    glemme hver deres. Fire løfter pr. kæde, og de er fire *forskellige*
    fejlformer:

    1. **Der står en linje.** Ellers er hele dommen grøn fordi den intet læser.
    2. **Før-tallet er tallet der stod.** Ellers er linjen en dif på to målinger
       af to forskellige ting — punkt 11.
    3. **Nu-tallet er tallet på skærmen.** Ellers lover linjen et tal bruteren
       ikke kan finde, og de to støder sammen når han læser dem.
    4. **Linjen væk, når bruteren selv griber ind.** Ellers står «før 1,16:1»
       under et tal der stammer fra en pladsering kernen ikke valgte — samme
       fejl som `.ti-fixed` havde ved billedskift.
    5. **Sætningen er sidens *egen* og nævner begge tal.** Attributtet er kun
       til for dommen; det læseren læser er `tekst`. En dansk læser må ikke få
       den engelske sætning, og en sætning der kun har ét af de to tal er en
       halv påstand (punkt 11).
    """
    egen = re.search(r"delta:\s*'([^']*)'", (SITE / fil).read_text(encoding="utf-8"))
    fund: list[str] = []
    if not d:
        return ["foer-nu: harnessen leverede ingen rettelseskæde at dømme"]
    for navn, k in (("fix", d.get("fix") or {}), ("find-spot", d.get("spot") or {})):
        if not k.get("harKnap"):
            fund.append(f"foer-nu/{navn}: ingen knap at trykke på, så dommen "
                        "kan ikke se om kernen skriver hvad den rettede")
            continue
        foer = k.get("foer") or {}
        efter = k.get("efter") or {}
        rykket = k.get("rykket") or {}
        dlt = efter.get("delta") or {}
        if not dlt.get("harDelta"):
            fund.append(f"foer-nu/{navn}: kernens rettelse giver intet nyt tal at "
                        "sammenligne med — bruteren ser kun resultatet og kan "
                        "aldrig vide om rettelsen overhovedet hjalp")
            continue
        a, b = foer.get("fik"), dlt.get("foer")
        if a is None or b is None:
            fund.append(f"foer-nu/{navn}: der står intet forholdstal hverken før "
                        "trykket eller i før/nu-linjen, så de to kan ikke sammenlignes")
        elif abs(a - b) > TOLERANS:
            fund.append(f"foer-nu/{navn}: linjen siger at tallet var {b:.2f}:1 "
                        f"før, men skærmen stod med {a:.2f}:1 — den beskriver en "
                        "anden måling end den bruteren så")
        c = dlt.get("nu")
        if c is None or efter.get("fik") is None:
            fund.append(f"foer-nu/{navn}: før/nu-linjen mangler tallet for «nu», "
                        "så den ikke kan læses sammen med kappen over sig")
        elif abs(c - efter["fik"]) > TOLERANS:
            fund.append(f"foer-nu/{navn}: linjen siger at tallet nu er {c:.2f}:1, "
                        f"men skærmen viser {efter['fik']:.2f}:1")
        if rykket.get("delta", {}).get("harDelta"):
            fund.append(f"foer-nu/{navn}: før/nu-linjen står stadig under et tal, "
                        "efter at bruteren selv har rørt farve eller pladsering — "
                        "den taler om kernens indgreb og ikke om det han nu ser")
        # Sætningen læseren læser, ikke attributtet dommen læser. Begge tal skal
        # stå i den — ellers er den kun halv så lang som det den fortæller.
        # Både punktum og komma accepteres, fordi den danske side bruger komma —
        # samme greb som resten af porten. Det dømmes er *hvilken sætning* der
        # står, ikke hvilken decimaltegn den bruger.
        sæt = dlt.get("tekst") or ""
        # De to domme er uafhængige, så en sætning der kun nævner ét tal kan
        # findes uden at den samtidig er en fremmed sætning — ellers lå den
        # anden fejl som en skygge under den første og var aldrig målbar.
        for tal, hvilket in ((b, "før"), (c, "nu")):
            if not sæt or tal is None:
                continue
            hvis = f"{tal:.2f}"
            if hvis not in sæt and hvis.replace(".", ",") not in sæt:
                fund.append(f"foer-nu/{navn}: sætningen nævner ikke tallet for "
                            f"«{hvilket}» ({hvis}:1), så læseren skal regne det "
                            "selv sammen")
        varianter = [egen.group(1) % tuple(x.replace(".", s)
                                          for x in (f"{b:.2f}", f"{c:.2f}"))
                     for s in (".", ",")] if (egen and b is not None and c is not None) else []
        if sæt and varianter and sæt not in varianter:
            fund.append(f"foer-nu/{navn}: før/nu-linjen er ikke sidens egen "
                        f"`delta`-tekst ({sæt!r})")
    return fund


def dom(kode: str, r: list[dict] | None = None) -> list[str]:
    fund: list[str] = []
    for r in (r if r is not None else koer(kode)):
        fik = r["fik"]
        if fik is None:
            fund.append(f"{r['navn']}: værktøjet viser intet forholdstal — det skal "
                        f"være {r['forventet']:.2f}:1")
        elif abs(fik - r["forventet"]) > TOLERANS:
            fund.append(f"{r['navn']}: viser {fik:.2f}:1, men billedet og "
                        f"tekstfarven giver {r['forventet']:.2f}:1")
    return fund


def dom_gradient(g: dict | None) -> list[str]:
    """Døm at **gradient** måles af samme kode som et foto — og at den gør det.

    Feature-kø punkt 4, 3/10: bruteren med en `linear-gradient` i sit stylesheet
    kunne ikke måle den overhovedet. `/contrast-checker` tager to *flade* farver,
    og tjekkeren tog kun et *uploadet billede* — så det eneste vejen var at tage
    et skærmbillede og regne på komprimeringen. Kernen maler derfor gradienten
    ind i præcis den `img`-plads et foto fylder, så der er **to ruter ind i én
    måling** og ikke to måleveje der kan komme i ukig.

    Fire løfter, og de er fire forskellige fejlformer:

    1. **Vælgeren skjuler gradientens felter, når de ikke bruges.** Tre
       farvefelter i folden er tre ting læseren ikke kan bruge, og
       `check_first_action` dømmer præcis den slags.
    2. **Vinklen er målbar, i CSS' egen betydning.** `linear-gradient(0deg, …)`
       peger *opad*, så startfarven ligger i bunden og slutfarven i toppen —
       hvid tekst i toppen står altså på sort og består, i bunden på hvid og
       fejler. `180deg` peger *nedad*, så det er omvendt. Kan de to vinkler ikke
       bytte om på dommene, læser værktøjet gradienten som én farve. Og fordi
       vinklen er CSS' egen, er «180°» her præcis det bruteren har skrevet i sit
       stylesheet — ikke en intern definition kernen har fundet på.
    3. **Stop og vinkel males begge.** Ved 0° skal hvid tekst i toppen bestå og
       i bunden fejle; ved 180° omvendt. Kan de to placeringer ikke få hver sin
       dom, læser værktøjet gradienten som én farve.
    4. **Det er *værste ende*, ikke gennemsnit.** Samme gradient i to placeringer
       langs aksen med kravet 4,5:1: den mørke ende består, den lyse fejler. En
       måling der tog gennemsnittet ville bestå begge steder — og det er præcis
       det løfte bruteren ikke må få, siden hele pointen er at *finde* hvor
       teksten er ulæselig.

    Og skiftet tilbage til fotoet skal virke, fordi det er den bevægelse
    bruteren har lavet mere end én gang i sit eget hoved.
    """
    fund: list[str] = []
    if not g:
        return ["gradient: harnessen leverede ingen måling af gradienten at dømme"]
    if g.get("felterSynlige") != "none":
        fund.append("gradient: gradientens egne felter står fremme selv om "
                    "værktøjet kører på et billede, så læseren læser tre "
                    "farvefelter der intet gør")
    # `0deg` i CSS peger opad → startfarven i bunden. `180deg` peger nedad →
    # startfarven i toppen. Hvid tekst i toppen består altså **kun** ved 0°.
    for vinkel in ("0", "180"):
        top, ned = g.get(f"top{vinkel}"), g.get(f"ned{vinkel}")
        if not top or top.get("fik") is None or not ned or ned.get("fik") is None:
            fund.append(f"gradient: ved {vinkel}° står der ikke et tal i begge "
                        f"placeringer, så værktøjet måler ikke hele gradienten")
            continue
        # `0deg` peger opad, så slutfarven (#000000) ligger i toppen og
        # hvid tekst der består. `180deg` peger nedad, så startfarven
        # (#ffffff) ligger i toppen og hvid tekst dér fejler. Begge steder
        # fejler den hvide ende — det er det dommen kræver.
        topSkalFejle = vinkel == "180"
        if bool(top.get("fejler")) != topSkalFejle:
            fund.append(f"gradient: ved {vinkel}° er toppen "
                        f"{'fejlende' if top.get('fejler') else 'bestående'} "
                        f"({top['fik']:.2f}:1), men den ende er "
                        f"{'hvid' if topSkalFejle else 'sort'}")
        if bool(ned.get("fejler")) == topSkalFejle:
            fund.append(f"gradient: ved {vinkel}° er bunden "
                        f"{'fejlende' if ned.get('fejler') else 'bestående'} "
                        f"({ned['fik']:.2f}:1), men den ende er "
                        f"{'sort' if topSkalFejle else 'hvid'}")
    m, l = g.get("mork"), g.get("lys")
    if not m or not l or m.get("fik") is None or l.get("fik") is None:
        fund.append("gradient: der står ikke et tal i begge ender af den "
                    "liggende gradient")
    else:
        if m.get("fejler"):
            fund.append(f"gradient: hvid tekst i den mørke ende af gradienten "
                        f"fejler ({m['fik']:.2f}:1) — den ende er den mørkeste")
        if not l.get("fejler"):
            fund.append(f"gradient: hvid tekst i den lyse ende af gradienten "
                        f"består ({l['fik']:.2f}:1, krav 4.50:1) — så målingen "
                        "tager gennemsnittet af endepunkterne i stedet for det "
                        "værste par under bogstaverne")
    foto = g.get("foto")
    if not foto or foto.get("fik") is None:
        fund.append("gradient: efter at gradienten er valgt og bruteren går "
                    "tilbage til billede, står der intet tal — skiftet ødelægger "
                    "værktøjet")
    return fund


def dom_blokke(b: dict | None) -> list[str]:
    """Døm at værktøjet måler *to* tekstblokke, og kun dem.

    Feature-kø punkt 2, 3/10: den mest almindelige reelle case er to
    overlejrende tekster på ét foto, og værktøjet målte kun den *sidste* —
    bruteren fik ét tal for to tekster og vidste ikke om den anden var
    ulæselig. Seks løfter, seks forskellige fejlformer:

    1. **Der står to tal.** Én boks med ét tal er stadig det gamle værktøj.
    2. **Tallet i den anden boks er rigtigt.** Blok 1 har *hvid* tekst og
       ligger på den mørke halvdel (21:1); blok 2 har *sort* tekst og
       ligger på den mørke halvdel (1:1). Kan de to tal ikke være
       forskellige, læser værktøjet den ene blok to gange. Farverne er
       forskellige med vilje: var de ens, ville en mutation der læser
       blok 1s farve i stedet for blok 2s være grøn på næsten alt.
    3. **Der er en vælger.** To tekster og ét klik uden en måde at vælge
       betyder at bruteren måler den ene og flytter den anden.
    4. **Vælgeren flytter den blok der blev valgt.** Tryk på blok 2 og træk
       i den lyse side: så skal blok 2 skifte fra 21:1 til 1:1, og blok 1
       stå uændret. Det er hele pointen med vælgeren.
    5. **Blok 1 røres ikke.** Flytningen må ikke røre den anden blok — ellers
       ville bruterens egen greb slette den måling han lige lavede.
    6. **Der står hvilken der er valgt.** `aria-pressed` er ikke pynt: uden
       det kan bruteren ikke se hvad han har valgt, og uden det kan porten
       heller ikke se det.
    """
    fund: list[str] = []
    if not b:
        return ["blok: harnessen leverede ingen måling af to tekstblokke at dømme"]
    if not b.get("harBokse"):
        fund.append("blok: der står ikke et tal i begge resultatkasser, så der "
                    "er stadig kun ét tal for to tekster")
    if not b.get("harVaelger"):
        fund.append("blok: der er ingen knap der vælger hvilken tekst et klik "
                    "flytter, så bruteren måler den ene og flytter den anden")
        return fund
    # Blok 1 over den mørke halvdel med hvid tekst er 21:1; blok 2 over den
    # lyse er 1:1. Begge er tal fra WCAG 2.1, slået op og ikke udregnet her.
    foerste, anden = b.get("foerste"), b.get("anden")
    if foerste is None or anden is None:
        fund.append("blok: der står ikke et tal i begge kasser, så bruteren kan "
                    "ikke se om den anden tekst fejler")
    elif abs(foerste - 21.0) > TOLERANS:
        fund.append(f"blok: den første tekst over den mørke halvdel viser "
                    f"{foerste:.2f}:1, men hvid på mørk er 21.00:1")
    elif abs(anden - 1.0) > TOLERANS:
        fund.append(f"blok: den anden tekst over den mørke halvdel viser "
                    f"{anden:.2f}:1, men sort på mørk er 1.00:1 — læser "
                    "værktøjet den første blok to gange?")
    efterFoerste, efterAnden = b.get("efterFoerste"), b.get("efterAnden")
    if efterAnden is None:
        fund.append("blok: efter at blok 2 blev valgt og flyttet står der intet "
                    "tal i dens boks, så valgeren flyttede ikke den valgte blok")
    elif anden is not None and abs(efterAnden - anden) < 0.005:
        fund.append(f"blok: blok 2 blev valgt og flyttet til den lyse halvdel, "
                    f"men tallet står uændret på {efterAnden:.2f}:1 — klikket "
                    "flyttede ikke den blok bruteren valgte")
    if efterFoerste is None or foerste is None:
        fund.append("blok: efter flytningen af blok 2 står der intet tal i "
                    "blok 1's boks")
    elif abs(efterFoerste - foerste) > 0.005:
        fund.append(f"blok: blok 2 blev flyttet, men blok 1s tal flyttede sig "
                    f"også ({foerste:.2f} → {efterFoerste:.2f}) — bruterens eget "
                    "greb ødelagde den anden måling")
    if b.get("andenTrykket") != "true":
        fund.append("blok: der står ikke at blok 2 er den valgte, så bruteren "
                    "kan ikke se hvad et klik vil flytte")
    if b.get("foersteTrykket") != "false":
        fund.append("blok: blok 1 står stadig som den valgte efter at blok 2 "
                    "blev valgt — to blokke, én markering")
    return fund


def dom_demo(fil: str, d: dict | None) -> list[str]:
    """Døm at værktøjet siger *hvad* det måler på, før bruteren har valgt et billede.

    Fundet 3/10 ved at læse koden, målt på den **byggede** side: kernen
    tegner sit eget eksempelbillede ved sidevisning og måler på det med det
    samme, så resultatet stod som «PASS — 5,42:1 … Measured against the
    lightest and darkest image pixels **under your letters**». Ingen sted
    sagde at billedet var kernens eget. Det er en påstand om bruterens fil,
    lavet af et billede bruteren aldrig har set — og den stod på den største
    indgangsside på sitet (`/blog/text-on-image-contrast-check` er 8 af 18
    besøgende, 100 % bounce).

    Fem krav, og de er fem forskellige fejlformer:

    1. **Noten findes overhovedet.** Ellers er hele dommen grøn fordi den
       intet læser.
    2. **Den er sidens *egen* tekst.** Ellers kunne den danske side vise den
       engelske, og dommen ville være grøn fordi den matcher *en* streng.
    3. **Den står før badge'en.** «PASS» er det første en læser ser; en note
       under tallet er en note de fleste ikke læser.
    4. **Eksemplet måler stadig.** Uden et tal er demoen en tom flade, og så
       fjerner vi det læreren faktisk kan lære noget af.
    5. **Noten væk igen efter upload.** Ellers kalder værktøjet bruterens eget
       foto et eksempel — samme fejl som sløret og `lastFix` havde ved
       billedskift, og derfor samme nulstilling.
    """
    fund: list[str] = []
    if not d:
        return [f"{fil}: harnessen målte ikke demo-tilstanden, så den dømmer ingenting"]
    start = d.get("start") or {}
    efter = d.get("efterUpload") or {}
    egen = re.search(r"demoNote:\s*'([^']*)'", (SITE / fil).read_text(encoding="utf-8"))
    if not start.get("tekst"):
        fund.append(f"{fil}: værktøjet måler på sit eget eksempelbillede uden at "
                    "sige det — tallet læseren ser kommer ikke fra deres fil")
    elif egen and start["tekst"] != egen.group(1):
        fund.append(f"{fil}: demo-noten er ikke sidens egen `demoNote`-tekst "
                    f"(fandt {start['tekst']!r})")
    if start.get("tekst") and not start.get("forBadge"):
        fund.append(f"{fil}: demo-noten står *efter* PASS/FAIL-kappen, så en "
                    "læser der kun ser kappen får et målt tal uden at vide hvorfra")
    if start.get("tekst") and not start.get("harTal"):
        fund.append(f"{fil}: eksempelbilledet giver intet forholdstal — så der er "
                    "intet at lære af, før bruteren har uploadet sit eget")
    if efter.get("tekst"):
        fund.append(f"{fil}: demo-noten står stadig efter at bruteren har valgt "
                    f"sit eget billede ({efter['tekst']!r})")
    if not efter.get("harTal"):
        fund.append(f"{fil}: der står intet forholdstal efter upload — værktøjet "
                    "skal stadig måle det bruterens eget billede")
    return fund


def dom_hex(fil: str, d: dict | None) -> list[str]:
    """Døm at den målte tekstfarve står som en kode bruteren kan kopiere.

    Fundet 3/10 ved at læse koden, målt i rigtig Chromium på den **byggede**
    side: kernen skrev «I changed the text color to #1a1a1a» i en sætning og
    viste *intet* derfra. Bruteren skulle finde farvefeltet og skrive koden af
    i Figma — altså gøre værktøjets arbejde selv, på den betalte del af det.
    Og når kernen så skrev den i sætningen, hang den fast ved den kode den
    *havde* valgt: ændrede bruteren farven i feltet, stod den gamle kode stadig i
    teksten. To forskellige sandheder om den samme værdi.

    Fire krav, og de er fire forskellige fejlformer:

    1. **Koden står som en knap.** Ellers er hele dommen grøn fordi den læser
       en farve der ikke er der — eller fordi den læser attributtet og tror
       det er det bruteren ser. Den skal være en `<button>`, fordi den
       *gør* noget: kopierer.
    2. **Koden er farvefeltets værdi.** Ikke «en farve», ikke «den farve
       kernen anbefaler»: den værdi bruteren kan se i feltet ovenfor, fordi
       det er den han skal tage videre. Læses i harnessen, ikke i kernen.
    3. **Den følger «Fix it».** `applyFix()` skriver altid en ny tekstfarve til
       feltet, også når rettelsen er et slør. Koden på skærmen skal være den
       *nye* — ellers kopierer bruteren en farve der ikke er den han ser.
    4. **Den læses samme sted som den gemmes.** Attributtet er kun for dommen;
       det bruteren læser er teksten i knappen. De to kan komme i ukig, og
       så står der en kode på skærmen der ikke er den der kopieres.
    """
    fund: list[str] = []
    if not d:
        return [f"{fil}: harnessen målte ikke farvekoden, så dommen dømmer "
                "intet — grønt her betyder ingenting"]
    kæde = d.get("fix") or {}
    if not kæde.get("harFix"):
        fund.append(f"{fil}: ingen «fix»-knap at trykke på, så dommen kan ikke "
                    "se om koden følger kernens egen rettelse")
        return fund
    for hvornår, laes in (("før", kæde.get("foer") or {}),
                         ("efter", kæde.get("efter") or {})):
        if not laes.get("harKnap"):
            fund.append(f"{fil} ({hvornår} rettelsen): der står ingen farvekode "
                        "under tallet — bruteren skal selv finde farvefeltet og "
                        "skrive koden af i sit eget værktøj")
            continue
        if not laes.get("erKnap"):
            fund.append(f"{fil} ({hvornår} rettelsen): farvekoden er ikke en "
                        "`<button>`, så den ser ud som en handling uden at "
                        "kunne trykkes")
        # 1 og 2: koden er *farvefeltets* værdi, ikke en farve kernen synes
        # om. En kode der ikke er et gyldigt `#rrggbb` kan slet ikke sammenlignes
        # med feltet, så det er samme fejl og dømmes som én.
        hexk = (laes.get("hex") or "").lower()
        felt = (laes.get("felt") or "").lower()
        if not re.fullmatch(r"#[0-9a-f]{6}", hexk):
            fund.append(f"{fil} ({hvornår} rettelsen): farvekoden er {hexk!r}, som "
                        "ikke er en `#rrggbb`-kode bruteren kan indsætte i sit "
                        "værktøj")
        elif hexk != felt:
            fund.append(f"{fil} ({hvornår} rettelsen): koden under tallet er "
                        f"{hexk}, men farvefeltet står med {felt} — bruteren "
                        "kopierer en anden farve end den han ser")
    foer, efter = kæde.get("foer") or {}, kæde.get("efter") or {}
    if foer.get("hex") and efter.get("hex") and foer["hex"].lower() == efter["hex"].lower():
        fund.append(f"{fil}: koden står stadig {foer['hex']} efter «Fix it», "
                    "selv om kernen skrev en ny tekstfarve til feltet — bruteren "
                    "kopierer den farve han havde *før* rettelsen")
    # 4: attributtet er for dommen, teksten er for læseren.
    for hvornår, laes in (("før", foer), ("efter", efter)):
        h, t = laes.get("hex"), laes.get("synlig")
        if h and t and t.lower() != h.lower():
            fund.append(f"{fil} ({hvornår} rettelsen): knappen viser {t!r} men "
                        f"gemmer {h!r} — bruteren læser den ene og kopierer den "
                        "andere")
        # Farveprøven i knappen er det bruteren bruger til at kende farven
        # igen på sit eget billede, så den skal være den samme kode. Uden den
        # er knappen en farve i hex, hvilket præcis er det den skulle spare ham
        # for at slå op. En **manglende** prøve dømmes også: ellers ville den
        # bare springes over, og et løfte der springes over er det samme som
        # et løfte uden dom (målt 3/10 — prøven blev læst i knappens egen
        # tag, så den var altid `null` og tælleren løj).
        if not h:
            continue
        if not laes.get("praem"):
            fund.append(f"{fil} ({hvornår} rettelsen): farveprøven mangler i "
                        "farveknappen, så bruteren skal selv holde koden op mod "
                        "sit billede for at kende farven igen")
        elif laes["praem"].lower() != h.lower():
            fund.append(f"{fil} ({hvornår} rettelsen): farveprøven i knappen er "
                        f"{laes['praem']}, men koden er {h} — de to viser to "
                        "forskellige farver")
    return fund


def dom_knapetekst(fil: str, html: str) -> list[str]:
    """Døm at farveknappens to tekster findes på *denne* side.

    `dom_hex` kører kernen i rigtig Chromium, men kun på de to værktøjssider.
    Artiklerne indlejrer *samme* kerne og får derfor samme streng dømt på
    kildefilen: en tekst der kun findes på værktøjssiden er en halv rettelse —
    bruteren på artiklen får så en knap uden titel og en bekræftelse med det
    forkerte sprog.

    To løfter, og de er to forskellige fejl:

    1. `copyHex` er knappens `title`. Uden den ved bruteren ikke hvad knappen
       gør, før han trykker — en farve i hex med ingen forklaring er præcis
       det han skulle spare op at slå op.
    2. `copiedHex` er det der står **efter** tryk. Kernen falder tilbage til
       koden efter 1,8 s, så en side uden nøglen får enten en knap der siger
       «Copy the measured text color» igen, eller den engelske «Copied» på
       en dansk side. Begge er en løgn om at trykket lykkedes.

    Særskilt fra `dom_hex` og ikke en del af den, fordi disse to løfter tælles
    på **alle fire** sider mens `dom_hex` kun har noget at dømme på to — og en
    tæller der kun tæller det den dømmer, må ikke få dem blandet sammen.
    """
    fund: list[str] = []
    for noegle, hvad in (("copyHex", "beskriver hvad knappen gør"),
                         ("copiedHex", "bekræfter trykket på den side den står på")):
        if re.search(rf"\b{noegle}\s*:\s*'[^']+'", html) is None:
            fund.append(f"{fil}: der er ingen `{noegle}`-tekst, så "
                        f"farveknappen {hvad} ikke på denne side")
    return fund


def self_test() -> int:
    fejl: list[str] = []
    # Tælles op, ikke hardkodet: en hardkodet tæller sig selv grøn for
    # kontroller der ikke længere findes, og det er præcis den fejlform
    # porten er bygget til at dømme — et løfte uden dom.
    talt = 0

    def tjek(navn: str, cond: bool, info: str = "") -> None:
        nonlocal talt
        talt += 1
        if not cond:
            fejl.append(f"{navn} — {info}")

    def naer(fik, forventet: float) -> bool:
        # Ikke `fik or -1`: 0.0 er falsy i Python, så et korrekt nul i
        # tallene ville blive dømt som et manglende svar.
        return fik is not None and abs(fik - forventet) <= TOLERANS

    kode = hent_kode(SIDER[0])

    # 1–5: de fem mutationer skal gøre dommen rød. Det er beviset på at
    # porten dømmer noget og ikke bare læser tallene fra koden.
    for navn, gammel, ny in MUTATIONER:
        tjek(f"mutationen findes i koden: {navn}", gammel in kode, repr(gammel))
        hvis = kode.replace(gammel, ny, 1)
        fund = dom(hvis)
        tjek(f"mutationen gør porten rød: {navn}", bool(fund),
             f"mutationen gav stadig grønt: {json.dumps(koer(hvis), ensure_ascii=False)}")

# 5e: **gradient-baggrunden.** Mutationerne er de tre fejlformer der kan
    # få gradienten til at *se* ud som om den virker, mens den ikke gør det:
    #   (a) slutstoppet males som startfarven, så fladen bliver næsten ensfarvet
    #       — «den er der, den bare ikke slår», hvilket er det værste svar.
    #   (b) vinklen læses ikke, så 0° og 180° bliver det samme billede.
    #   (c) værste ende findes ikke, så dommen er den *første* baggrund der
    #       bliver læst i stedet for den dårligste — altså gennemsnittets
    #       modsætning, og den løfte bruteren ikke må få.
    grad_stop = "      grad.addColorStop(1, $('gto').value);"
    tjek("mutationen findes i koden: gradientens slutstop males fra feltet",
         grad_stop in kode, repr(grad_stop))
    mut_g1 = dom_gradient(koer(kode.replace(
        grad_stop, "      grad.addColorStop(1, $('gfrom').value);", 1),
        hele=True).get("gradient"))
    tjek("mutationen gør gradient-dommen rød: slutstoppet males som startfarven",
         bool(mut_g1), f"mutationen gav stadig grønt: {json.dumps(mut_g1, ensure_ascii=False)}")

    grad_vinkel = "      var rad = (isFinite(rawn) ? rawn : 0) * Math.PI / 180;"
    tjek("mutationen findes i koden: gradientens vinkel læses fra feltet",
         grad_vinkel in kode, repr(grad_vinkel))
    mut_g2 = dom_gradient(koer(kode.replace(grad_vinkel, "      var rad = 0;", 1),
                               hele=True).get("gradient"))
    tjek("mutationen gør gradient-dommen rød: vinklen læses ikke",
         bool(mut_g2), f"mutationen gav stadig grønt: {json.dumps(mut_g2, ensure_ascii=False)}")

    grad_vaerst = "      var worst = Infinity, worstOff = minOff;"
    tjek("mutationen findes i koden: målingen tager den værste ende",
         grad_vaerst in kode, repr(grad_vaerst))
    mut_g3 = dom_gradient(koer(kode.replace(grad_vaerst,
                                            "      var worst = 0, worstOff = minOff;", 1),
                               hele=True).get("gradient"))
    tjek("mutationen gør gradient-dommen rød: værste ende findes ikke",
         bool(mut_g3), f"mutationen gav stadig grønt: {json.dumps(mut_g3, ensure_ascii=False)}")

    # 5: de to sider skal dømme ens. Den danske er en oversættelse, ikke en
    # egen algoritma, så et tal der kun er rigtigt på den ene er en fejl.
    en, da = dom(kode), dom(hent_kode(SIDER[1]))
    tjek("EN-siden er grøn", not en, "; ".join(en))
    tjek("DA-siden er grøn", not da, "; ".join(da))

    # 5d: **to tekstblokke**. Mutationerne her er de tre fejlformer der gav
    # *dette* iterations fejl undervejs, og de er alle fundet i den rigtige
    # fil — ikke opdigtet til selftesten:
    #   (a) pixel-løkken hed `i`, som også er blokkens nummer, så blok 2 blev
    #       målt med blok 1's tekst og farve: 56 røde løfter på de 112 gamle.
    #   (b) `renderBlock` skrev sin markup i *begge* kasser, så der stod to
    #       identiske tal, og bruteren fik ét tal for to tekster igen.
    #   (c) vælgeren flyttede altid blok 0, så et klik efter at blok 2 var
    #       valgt rørte den anden tekst — og bruteren så ikke sin egen greb.
    blok_farve = "      var fgRgb = hexToRgb(farveFelt(i).value);"
    tjek("mutationen findes i koden: hver blok måles med sin egen farve",
         blok_farve in kode, repr(blok_farve))
    # Mutationen dømmer præcis den fejl den her iteration gjorde: målingen
    # læste altid blok 1s felter, uanset hvilken blok den kørte for. Den er
    # *ækvivalent* mellem blokke, der har samme farve — så det er netop
    # todeltes billedet med to forskellige placeringer, der fanger den, og
    # det er derfor dommen bruger to halvdele og ikke ét ensfarvet billede.
    mut_a = dom_blokke(koer(kode.replace(blok_farve,
                                         "      var fgRgb = hexToRgb($('fg').value);", 1),
                            hele=True).get("blok"))
    tjek("mutationen gør blok-dommen rød: blokke måles med blok 1s farve",
         bool(mut_a), f"mutationen gav stadig grønt: {json.dumps(mut_a, ensure_ascii=False)}")

    blok_boks = "      var res = $(i ? 'result2' : 'result');"
    tjek("mutationen findes i koden: hver blok har sin egen boks",
         blok_boks in kode, repr(blok_boks))
    mut_b = dom_blokke(koer(kode.replace(blok_boks, "      var res = $('result');", 1),
                            hele=True).get("blok"))
    tjek("mutationen gør blok-dommen rød: begge blokke skriver i én boks",
         bool(mut_b), "mutationen gav stadig grønt")

    blok_aktiv = "      saetX(aktiv, cx * cv.width / rect.width - fontSizePx() / 2);"
    tjek("mutationen findes i koden: klikket flytter den valgte blok",
         blok_aktiv in kode, repr(blok_aktiv))
    mut_c = dom_blokke(koer(kode.replace(
        blok_aktiv, "      saetX(0, cx * cv.width / rect.width - fontSizePx() / 2);", 1),
        hele=True).get("blok"))
    tjek("mutationen gør blok-dommen rød: klikket flytter altid blok 1",
         bool(mut_c), "mutationen gav stadig grønt")

    # Dommen skal være grøn på den rigtige kode, og de seks løfter skal kunne
    # gå rød hver for sig — ellers kunne de være grønne kun fordi et andet
    # fejler, hvilket præcis er det porten her er bygget til at fange.
    blok_ok = koer(kode, hele=True).get("blok")
    tjek("blok-dommen er grøn på den rigtige kode", not dom_blokke(blok_ok),
         "; ".join(dom_blokke(blok_ok)))

    def blok_handlavet(**over):
        laes = {"harBokse": True, "harVaelger": True, "foerste": 21.0, "anden": 1.0,
                "efterFoerste": 21.0, "efterAnden": 21.0,
                "andenTrykket": "true", "foersteTrykket": "false"}
        laes.update(over)
        return laes

    tjek("blok-dommen ser en anden blok der læser den første to gange",
         any("læser værktøjet den første blok to gange" in f for f in
             dom_blokke(blok_handlavet(anden=21.0))),
         "to ens tal blev dømt grønne")
    tjek("blok-dommen ser en vælger der ikke flytter den valgte blok",
         any("flyttede ikke den blok bruteren valgte" in f for f in
             dom_blokke(blok_handlavet(anden=21.0, efterAnden=21.0))),
         "en vælger der ikke flytter blev dømt grøn")
    tjek("blok-dommen ser bruterens greb ødelægge den anden måling",
         any("ødelagde den anden måling" in f for f in
             dom_blokke(blok_handlavet(efterFoerste=1.0))),
         "en krybende blok 1 blev dømt grøn")
    tjek("blok-dommen ser to blokke med én markering",
         any("to blokke, én markering" in f for f in
             dom_blokke(blok_handlavet(foersteTrykket="true"))),
         "to trykkede markeringer blev dømt grønne")
    tjek("blok-dommen ser en manglende vælger",
         any("der er ingen knap der vælger" in f for f in
             dom_blokke(blok_handlavet(harVaelger=False))),
         "en manglende vælger blev dømt grøn")
    tjek("blok-dommen ser en kasse uden tal",
         any("står ikke et tal i begge" in f for f in
             dom_blokke(blok_handlavet(anden=None))),
         "en tom anden kasse blev dømt grøn")

    # 5b: den sekventielle kæde skal finde præcis den fejl, den er skrevet
    # til. Fundet i review 3/10 og målt i rigtig Chromium: `loadFile()`
    # nulstillede hverken `scrim` eller `lastFix`, så sløret fra foto A blev
    # tegnet på foto B. Det er den eneste fejl i denne port der *kun* kan ses
    # i en kæde, så mutationen her er portens vigtigste.
# Nulstillingsblokkene. De lå i `loadFile()` og lå nu i `baggrundNul()`,
    # som både `loadFile()` og `vaerlGradient()` kalder — samme fejlform som
    # før (sløret og `lastFix` gjaldt det *sidste* input) med tre veje ind i
    # stedet for to. Derfor er mutationen et regex: den skal ramme alle
    # nulstillingerne, også den nye gradient-vej, ellers ville den teste en
    # delmængde af den fejl den er skrevet til. Tællet er derfor ikke et fast
    # tal, men «alle veje ind nulstiller»: `baggrundNul()` skal findes, og
    # begge kaldester skal være med.
    reset_re = re.compile(
        r"^[ \t]*(?:scrim|lastFix|t2\.scrim|t2\.lastFix|demoBillede) = (?:null|false);\n"
        r"(?:[ \t]*//[^\n]*\n)*", re.M)
    tjek("mutationen findes i koden: baggrundNul() nulstiller sløret",
         "function baggrundNul()" in kode
         and "baggrundNul();" in kode
         and len(reset_re.findall(kode)) >= 5, str(len(reset_re.findall(kode))))
    sek_ok = koer(kode, hele=True).get("sekventiel")
    tjek("to-billeders-kæden leverer alle tre læsninger",
         bool(sek_ok) and all(k in sek_ok for k in ("efter", "refer", "fixA")),
         str(sek_ok))
    tjek("porten er grøn på den rigtige kode",
         not dom_sekventiel(sek_ok), "; ".join(dom_sekventiel(sek_ok)))
    # B skal **fejle** i referencen. Ellers er der ingen «fix»-knap at kræve
    # tilbage, og løfterne (b) og (c) er grønne fordi porten aldrig kan se
    # den fejl, de er skrevet til. Dømt på `harKnap`, fordi det er knappens
    # tilstedeværelse i markup'en — ikke et beregnet krav.
    tjek("foto B fejler i udgangspunktet, så løfterne (b) og (c) har noget at dømme",
         bool(sek_ok) and (sek_ok.get("refer") or {}).get("harKnap") is True,
         str(sek_ok))
    # Og «fix» på A skal *virke*. Hvis rettelsen holdt op at løse A, ville
    # `suggestFix()` falde tilbage på en tekstfarve, der så ikke er noget slør
    # at lække — og hele kæden ville være grøn fordi den intet længere kan
    # finde. Det er den stille død, en port kan gå ind i uden at ændre et
    # eneste tal.
    fixA = (sek_ok or {}).get("fixA") or {}
    tjek("«fix» på foto A løser A, så kæden har et slør at lække",
         (fixA.get("efter") or {}).get("fik") is not None
         and fixA["efter"]["fik"] > (fixA.get("foer") or 0),
         str(fixA))
    sek_gammel = dom_sekventiel(
        koer(reset_re.sub("", kode), hele=True)
        .get("sekventiel"))
    # Og den mutation skal give **alle tre** fund. Det er også det bevis der
    # viser at det er et *slør* der lækker: en farve-fix efterlader intet, så
    # mutationen ville give 0 fund hvis `suggestFix()` holdt op med at vælge
    # slør. Færre end tre fund er derfor ikke et svagere bevis — det er et
    # tabt.
    tjek("mutationen gør den sekventielle dom rød i alle tre løfter",
         len(sek_gammel) == 3,
         f"forventede 3 fund, fik {len(sek_gammel)}: " +
         "; ".join(sek_gammel))

    # 5c: dommen skal kunne dømme hvert af de tre løfter *individuelt*. En
    # samlet mutation kan ramme alle tre på én gang og så se ud som om de
    # hver især har polaritet, mens en af dem i virkeligheden kun fanges
    # fordi de andre fejler. Derfor fanges de hver for sig.
    def handlavet(tal, har_fast=False, har_knap=True):
        return {"efter": {"fik": tal, "harFast": har_fast, "harKnap": har_knap},
                "refer": {"fik": 1.85, "harFast": False, "harKnap": True}}
    tjek("dommen kan se et tal der ikke er B's eget",
         bool(dom_sekventiel(handlavet(5.99))),
         str(dom_sekventiel(handlavet(5.99))))
    tjek("dommen kan se en .ti-fixed-tekst der ikke hører til B",
         any("ti-fixed" in f for f in dom_sekventiel(handlavet(1.85, har_fast=True))),
         str(dom_sekventiel(handlavet(1.85, har_fast=True))))
    tjek("dommen kan se en manglende «fix»-knap",
         any("knap" in f for f in dom_sekventiel(handlavet(1.85, har_knap=False))),
         str(dom_sekventiel(handlavet(1.85, har_knap=False))))
    tjek("dommen er grøn på to ens målinger",
         dom_sekventiel(handlavet(1.85)) == [], str(dom_sekventiel(handlavet(1.85))))
    tjek("dommen kan se en kæde, der slet ikke blev leveret",
         bool(dom_sekventiel(None)), "harnessen gav intet")

    # 5d: demo-dommen skal kunne blive rød. To mutationer af den rigtige kode,
    # og de er de to fejl der faktisk kan ske: noten er væk, eller den
    # nulstilles ikke ved billedskift. Den anden er den samme slags fejl som
    # sløret og `lastFix` havde før 3/10 — en oplysning om målingen der
    # overlever det input den måler — så den er værd at have en dom på.
    demo_ok = koer(kode, hele=True).get("demo")
    tjek("porten er grøn på den rigtige kodes demo-tilstand",
         not dom_demo(SIDER[0], demo_ok), "; ".join(dom_demo(SIDER[0], demo_ok)))
    tjek("demo-dommen kan se en note der mangler",
         any("uden at" in f for f in
             dom_demo(SIDER[0], {"start": {"tekst": None, "forBadge": False, "harTal": True},
                                 "efterUpload": {"tekst": None, "harTal": True}})),
         "dommen sagde ingenting om en manglende note")
    tjek("demo-dommen kan se en note der ikke forsvinder ved upload",
         any("efter at bruteren" in f for f in
             dom_demo(SIDER[0], {"start": {"tekst": "Eksempel", "forBadge": True, "harTal": True},
                                 "efterUpload": {"tekst": "Eksempel", "harTal": True}})),
         "dommen sagde ingenting om en note der bliver stående")
    # Mutationerne skal efterlade *gyldig* kode. Den første udgave slettede
    # betingelsen i markup'en, og harnessen døde med en SyntaxError — hvilket
    # er grønt for porten (den tjekker kun at `fund` er ikke tom) på den
    # måde, at porten aldrig nåede at dømme. Det er præcis det
    # `koer()`-kald med SystemExit på død kode skjuler: en fejl der ser ud
    # som en grøn dom, fordi den dør tidligt.
    DEMO_MUT = (
        ("demo-noten vises aldrig", "var demoBillede = true;", "var demoBillede = false;"),
        ("demo-noten nulstilles ikke ved upload", "        demoBillede = false;",
         "        if (false) demoBillede = false;"),
    )
    for navn, gammel, ny in DEMO_MUT:
        tjek(f"mutationen findes i koden: {navn}", gammel in kode, repr(gammel))
        fund = dom_demo(SIDER[0], koer(kode.replace(gammel, ny, 1), hele=True).get("demo"))
        tjek(f"mutationen gør demo-dommen rød: {navn}", bool(fund),
             f"mutationen gav stadig grønt")

    # 6: tallene i tabellen er slået op, ikke regnet ud fra koden. Genregn
    # dem her med WCAG-formlen, så en tastefejl i tabellen bliver rød.
    def lum(rgb):
        c = []
        for v in rgb:
            v /= 255
            c.append(v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4)
        return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]

    def ratio(a, b):
        la, lb = lum(a), lum(b)
        if la < lb:
            la, lb = lb, la
        return (la + 0.05) / (lb + 0.05)

    for navn, baggrund, tekst, forventet in FARVEPAR:
        fak = ratio([int(tekst[1:3], 16), int(tekst[3:5], 16), int(tekst[5:7], 16)],
                    [int(baggrund[1:3], 16), int(baggrund[3:5], 16), int(baggrund[5:7], 16)])
        tjek(f"tabeltallet er WCAG-korrekt: {navn}", abs(fak - forventet) <= TOLERANS,
             f"tabellen siger {forventet}, WCAG siger {fak:.4f}")

    # 7: de to positionsdomme må ikke være døde — hvis harnessen ikke kan
    # flytte teksten, ville FLADT og TODELT bare være flere ensfarvede billeder
    # og porten ville være grøn af den grund alene.
    svar = {r["navn"]: r["fik"] for r in koer(kode)}
    tjek("fladt billede giver et tal", svar.get(FLADT[0]) is not None, str(svar))
    tjek("todelt billede giver tal", all(svar.get(t[0]) is not None for t in TODELT), str(svar))
    tjek("hvid tekst på sort er 21:1", naer(svar.get(TODELT[0][0]), 21.00), str(svar))
    tjek("den samme tekst på hvid er 1:1", naer(svar.get(TODELT[1][0]), 1.00), str(svar))

    # 8: gradientdommet må ikke være dødt. Uden et billede med farvevariation
    # *inde i* tekstkassen er den mørkeste og den lyseste baggrund samme slags
    # valg, så springer man den ene over, ændrer tallet sig ikke — og porten
    # ville være grøn af den grund alene. Den skal både give et tal, og det
    # skal være det dårligste af de to, ikke det bedste.
    tjek("gradientbilledet giver et tal", svar.get(GRADIENT[0]) is not None, str(svar))
    tjek("gradientet svarer på den dårligste baggrund, ikke den bedste",
         naer(svar.get(GRADIENT[0]), GRADIENT[6]), str(svar))
    # Bevis på at casen kan overraske: den mutation der springer den mørkeste
    # baggrund over skal svare 21:1 her, fordi den så kun ser den hvide.
    spring = kode.replace("      [visMin, visMax].forEach(function (c, k) {",
                         "      [visMax].forEach(function (c, k) {", 1)
    bedste = {r["navn"]: r["fik"] for r in koer(spring)}.get(GRADIENT[0])
    tjek("gradientet kan svare 21:1 når kun den bedste baggrund tælles",
         naer(bedste, 21.00),
         f"mutationen svarede {bedste}, så casen kan ikke se forskellen")

    # 9: download-dommen skal være grøn på den rigtige kode og rød på to
    # mutationer der hver især er en reel fejl i den nye handling. Uden dem er
    # de tre løfter bare en tæller.
    dl_ok = dom_download((koer(kode, hele=True) or {}).get("download"))
    tjek("download-dommen er grøn på den kode der kører", dl_ok == [], str(dl_ok))
    dl_glemt = dom_download(
        (koer(kode.replace(" data-ti-dl>", " data-ti-dlx>", 1), hele=True)
         or {}).get("download"))
    tjek("download-dommen kan se en knap der ikke står i markup'en",
         any("ingen download-knap" in f for f in dl_glemt), str(dl_glemt))
    dl_rå = dom_download(
        (koer(kode.replace("      draw();\n      var dataUrl = null;",
                           "      drawTextLayer();\n      var dataUrl = null;", 1),
              hele=True) or {}).get("download"))
    tjek("download-dommen kan se en fil der er bogstaver på en ryddet baggrund",
         any("dækket" in f for f in dl_rå), str(dl_rå))
    dl_jpeg = dom_download(
        (koer(kode.replace("cv.toDataURL('image/png')", "cv.toDataURL('image/jpeg')", 1),
              hele=True) or {}).get("download"))
    tjek("download-dommen kan se en fil der ikke er en PNG",
         any("ikke som PNG" in f for f in dl_jpeg), str(dl_jpeg))

    # 10: dommen skal kunne dømme hvert løft *individuelt*, så ingen af dem er
    # grøn kun fordi et andet fejler.
    def dl_rigtig():
        return {"harKnap": True,
                "anker": {"href": "data:image/png;base64,iVBORw0KGgo=",
                          "download": "text-on-image-contrast.png"},
                "uopaque": 120000, "total": 120000, "afvigelser": 412}

    tjek("download-dommen er grøn på et rigtigt mål",
         dom_download(dl_rigtig()) == [], str(dom_download(dl_rigtig())))
    tjek("download-dommen kan se en kæde, der slet ikke blev leveret",
         bool(dom_download(None)), "harnessen gav intet")
    tjek("download-dommen kan se et knap-tryk uden fil",
         any("ingen fil blev afleveret" in f
             for f in dom_download({"harKnap": True})),
         "tomt mål blev dømt grønt")
    tjek("download-dommen kan se et filnavn uden .png",
         any(".png" in f for f in dom_download(dict(dl_rigtig(), anker={
             "href": "data:image/png;base64,iVBORw0KGgo=", "download": "billede"}))),
         "forkert filnavn blev dømt grønt")
    tjek("download-dommen kan se en fil uden teksten",
         any("rå foto" in f for f in dom_download(dict(dl_rigtig(), afvigelser=0))),
         "fil uden rettelse blev dømt grønt")

    # 11: «Find det bedste sted». Fire løfter, og de skal hver især kunne
    # gå rød — ellers er de fire bare fire tællere.
    spot_ok = (koer(kode, hele=True) or {}).get("spot")
    tjek("find-spot-kæden leverer alle tre læsninger",
         bool(spot_ok) and all(k in spot_ok for k in ("foer", "efter", "rykket")),
         str(spot_ok))
    tjek("find-spot-dommen er grøn på den kode der kører",
         not dom_spot(spot_ok), "; ".join(dom_spot(spot_ok)))
    # Billedet skal **fejle** i udgangspunktet. Ellers er «find det bedste
    # sted» en knap uden opgave, og løftet om et bedre tal ville være grønt
    # fordi porten aldrig kan se den fejl, den er skrevet til.
    tjek("teksten fejler på den halvdel den er lagt på, så dommen har noget at dømme",
         bool(spot_ok) and (spot_ok.get("foer") or {}).get("fik") is not None
         and spot_ok["foer"]["fik"] < 3.0, str(spot_ok))
    tjek("«find det bedste sted» flytter til et sted der består kravet",
         bool(spot_ok) and (spot_ok.get("efter") or {}).get("fik", 0) >= 3.0,
         str(spot_ok))
    # Mutation 1: knappen forsvinder af markup'en.
    tjek("mutationen findes i koden: data-ti-spot", " data-ti-spot>" in kode)
    spot_uden_knap = dom_spot(
        (koer(kode.replace(" data-ti-spot>", " data-ti-spotx>", 1), hele=True)
         or {}).get("spot"))
    tjek("find-spot-dommen kan se en knap der ikke står i markup'en",
         any("ingen «find det bedste sted»-knap" in f for f in spot_uden_knap),
         str(spot_uden_knap))
    # Mutation 2: kernen søger aldrig efter et bedre sted — den knap der gør
    # ingenting, som er den mutation der ligner mest en rigtig fejl.
    tjek("mutationen findes i koden: spot-vurderingen",
         "if (v > best) { best = v; bx = x; by = y; }" in kode)
    spot_uden_spot = dom_spot(
        (koer(kode.replace("if (v > best) { best = v; bx = x; by = y; }",
                           "if (v > best + 99) { best = v; bx = x; by = y; }", 1),
              hele=True) or {}).get("spot"))
    tjek("find-spot-dommen kan se en knap der ikke flytter teksten",
         any("ikke er bedre" in f for f in spot_uden_spot), str(spot_uden_spot))
    # Mutation 3: kernen skriver «det er allerede det bedste sted», selv om
    # den lige flyttede teksten. Det var ikke en hypotese — det var den fejl
    # første kørsel af dommen afslørede i min egen kode, fordi `rykket` blev
    # sammenlignet med proberne i stedet for med pladseringen den startede fra.
    tjek("mutationen findes i koden: rykket måles mod startstedet",
         "rykket: laegX(i) !== startX || laegY(i) !== startY" in kode)
    spot_løgn = dom_spot(
        (koer(kode.replace("rykket: laegX(i) !== startX || laegY(i) !== startY",
                           "rykket: false", 1), hele=True) or {}).get("spot"))
    tjek("find-spot-dommen kan se en kern der lyver om sin egen flytning",
         any("ikke flyttede noget" in f for f in spot_løgn), str(spot_løgn))
    # Mutation 4: beskrivelsen overlever bruterens egen flytning — den fejl
    # reviewen fandt med sløret ved billedskift, i en ny form.
    gammelt_drag = ("      saetFix(aktiv, null);\n      updateAll();\n    }\n"
                    "    // `sampleContrast()` ends on a cleared canvas")
    tjek("mutationen findes i koden: onMove nulstiller beskrivelsen",
         gammelt_drag in kode, repr(gammelt_drag))
    spot_drag = dom_spot(
        (koer(kode.replace(gammelt_drag,
                           "      updateAll();\n    }\n"
                           "    // `sampleContrast()` ends on a cleared canvas", 1),
              hele=True) or {}).get("spot"))
    tjek("find-spot-dommen kan se en beskrivelse der overlever bruterens egen flytning",
         any("efter at bruteren selv har flyttet" in f for f in spot_drag),
         str(spot_drag))
    # Og de fire løfter hver for sig, så ingen af dem er grøn kun fordi et andet
    # fejler.
    def spot_rigtig():
        return {"harKnap": True,
                "foer": {"fik": 1.12},
                "efter": {"fik": 18.0, "harFast": True, "flyttet": "1",
                          "fast": "18.00:1"},
                "rykket": {"fik": 1.12, "harFast": False}}

    tjek("find-spot-dommen er grøn på et rigtigt mål",
         dom_spot(spot_rigtig()) == [], str(dom_spot(spot_rigtig())))
    tjek("find-spot-dommen kan se en pladsering der ikke er bedre",
         any("ikke er bedre" in f for f in dom_spot(
             dict(spot_rigtig(), efter={"fik": 1.12, "harFast": True,
                                         "flyttet": "1", "fast": "1.12:1"}))),
         "en kern der gør intet blev dømt grønt")
    tjek("find-spot-dommen kan se en pladsering der stadig fejler",
         any("fejler stadig" in f for f in dom_spot(
             dict(spot_rigtig(), efter={"fik": 2.4, "harFast": True,
                                         "flyttet": "1", "fast": "2.40:1"}))),
         "en kern der flytter til et stadig fejlende sted blev dømt grønt")
    tjek("find-spot-dommen kan se en beskrivelse uden flytning",
         any("uden at sige det" in f for f in dom_spot(
             dict(spot_rigtig(), efter={"fik": 18.0}))),
         "en tavs flytning blev dømt grønt")
    tjek("find-spot-dommen kan se en kern der skriver at den ikke flyttede noget",
         any("ikke flyttede noget" in f for f in dom_spot(
             dict(spot_rigtig(), efter={"fik": 18.0, "harFast": True,
                                         "flyttet": "0", "fast": "18.00:1"}))),
         "en kern der løj om sin egen flytning blev dømt grønt")
    tjek("find-spot-dommen kan se en beskrivelse om en anden måling",
         any("anden måling" in f for f in dom_spot(
             dict(spot_rigtig(), efter={"fik": 18.0, "harFast": True,
                                         "flyttet": "1", "fast": "4.52:1"}))),
         "en beskrivelse med et forkert tal blev dømt grønt")
    tjek("find-spot-dommen kan se en kæde, der slet ikke blev leveret",
         bool(dom_spot(None)), "harnessen gav intet")

    # 12: «før → nu». Fem løfter pr. indgreb, og de skal hver især kunne gå rød.
    def delta_kæder(k: str):
        s = koer(k, hele=True) or {}
        return {"fix": (s.get("delta") or {}).get("fix"), "spot": s.get("spot")}

    dk = delta_kæder(kode)
    tjek("før/nu-kæden leverer begge indgreb",
         bool(dk.get("fix")) and bool(dk.get("spot")), str(dk)[:200])
    for navn in ("fix", "find-spot"):
        tjek(f"før/nu-dommen er grøn på {navn}-indgrebet",
             not dom_delta("text-on-image-checker.html", dk), "; ".join(dom_delta("text-on-image-checker.html", dk)))
    # Mutation 1: attributtet forsvinder — linjen er skrevet, men uden den
    # ene ting porten kan læse sandheden af.
    tjek("mutationen findes i koden: data-ti-delta", " data-ti-delta=\\\"" in kode or "data-ti-delta" in kode)
    d_uden = dom_delta("text-on-image-checker.html",
                       delta_kæder(kode.replace(" data-ti-delta=", " data-ti-deltax=", 1)))
    tjek("før/nu-dommen kan se en linje uden de to tal",
         any("intet nyt tal at sammenligne" in f for f in d_uden), str(d_uden)[:300])
    # Mutation 2: kernen skriver *efter*-tallet i begge halvdele. Den ser
    # plausibel ud — «3,04:1 før, 3,04:1 nu» — men «før» er så et tal bruteren
    # aldrig har set, og det er præcis punkt 11.
    d_dobbelt = dom_delta("text-on-image-checker.html", delta_kæder(
        kode.replace("var foerTekst = fmt(foerTal.toFixed(2));",
                     "var foerTekst = fmt(r.toFixed(2));", 1)))
    tjek("før/nu-dommen kan se en linje der gentager tallet",
         any("linjen siger at tallet var" in f for f in d_dobbelt), str(d_dobbelt)[:300])
    # Mutation 3: linjen overlever at bruteren selv griber ind i farvefeltet.
    gammel_fg = "function () { lastFix = null; scrim = null; updateAll(); });"
    tjek("mutationen findes i koden: farvefeltet nulstiller beskrivelsen",
         gammel_fg in kode, repr(gammel_fg))
    d_farve = dom_delta("text-on-image-checker.html", delta_kæder(
        kode.replace(gammel_fg, "function () { scrim = null; updateAll(); });", 1)))
    tjek("før/nu-dommen kan se en linje der overlever bruterens eget indgreb",
         any("efter at bruteren selv har rørt" in f for f in d_farve), str(d_farve)[:300])
    # Og de fem løfter hver for sig, så ingen af dem er grøn kun fordi et andet
    # fejler — samme greb som de fire over. `delta_kaede()` er *én* kæde;
    # dommen dømmer begge indgreb, så den får dem begge — det er den fejl jeg
    # selv lavede først, da et håndlavet mål kun havde den ene nøgle.
    def delta_kaede(**over):
        k = {"harKnap": True,
             "foer": {"fik": 1.16},
             "efter": {"fik": 4.72,
                       "delta": {"harDelta": True, "foer": 1.16, "nu": 4.72,
                                 "tekst": "Before this it measured 1.16. It measures 4.72 now."}},
             "rykket": {"fik": 1.16, "delta": {"harDelta": False, "foer": None, "nu": None}}}
        k.update(over)
        return k

    def delta_dom(**over):
        k = delta_kaede(**over)
        return dom_delta("text-on-image-checker.html", {"fix": k, "spot": k})

    tjek("før/nu-dommen er grøn på et rigtigt mål", not delta_dom(),
         "; ".join(delta_dom()))
    tjek("før/nu-dommen kan se en kæde uden linje",
         any("intet nyt tal" in f for f in delta_dom(efter={"fik": 4.72, "delta": {"harDelta": False}})),
         "en kæde uden delta blev dømt grønt")
    tjek("før/nu-dommen kan se et før-tal der ikke var på skærmen",
         any("linjen siger at tallet var" in f for f in
             delta_dom(efter={"fik": 4.72, "delta": {"harDelta": True, "foer": 19.19, "nu": 4.72}})),
         "et opdigtet før-tal blev dømt grønt")
    tjek("før/nu-dommen kan se et nu-tal der ikke står på skærmen",
         any("men skærmen viser" in f for f in
             delta_dom(efter={"fik": 4.72, "delta": {"harDelta": True, "foer": 1.16, "nu": 9.99}})),
         "et nu-tal der ikke stod på skærmen blev dømt grønt")
    tjek("før/nu-dommen kan se en linje der overlever bruterens indgreb",
         any("efter at bruteren selv har rørt" in f for f in
             delta_dom(rykket={"fik": 1.16, "delta": {"harDelta": True, "foer": 1.16, "nu": 4.72}})),
         "en linje der overlevede blev dømt grøn")
    tjek("før/nu-dommen kan se en sætning der ikke er sidens egen",
         any("ikke sidens egen" in f for f in
             delta_dom(efter={"fik": 4.72, "delta": {"harDelta": True, "foer": 1.16, "nu": 4.72,
                                                     "tekst": "Before: 9.99. Now: 9.99."}})),
         "en fremmed sætning blev dømt grøn")
    tjek("før/nu-dommen kan se en sætning der kun nævner ét tal",
         any("sætningen nævner ikke tallet" in f for f in
             delta_dom(efter={"fik": 4.72, "delta": {"harDelta": True, "foer": 1.16, "nu": 4.72,
                                                     "tekst": "Before this it measured 1.16. It measures 9.99 now."}})),
         "en halv sætning blev dømt grøn")
    tjek("før/nu-dommen kan se en kæde uden knap",
         any("ingen knap at trykke" in f for f in
             delta_dom(harKnap=False)),
         "en kæde uden knap blev dømt grøn")
    tjek("før/nu-dommen kan se en kæde, der slet ikke blev leveret",
         bool(dom_delta("text-on-image-checker.html", None)), "harnessen gav intet")
    # `delta`-strengen skal have to `%s` på alle fire sider — kernen sætter
    # dem ind med to `.replace('%s', …)` i træk, så én ville miste et tal.
    tjek("`delta`-teksten har to `%s` på alle fire sider",
         all((re.search(r"delta:\s*'([^']*)'", (SITE / f).read_text(encoding="utf-8")) or
              re.match(r"$", "")).group(1).count("%s") == 2
             for f in SIDER + ARTIKLER),
         "en side mangler den anden %s")

    # 13: farvekoden. Fire løfter, og de skal hver især kunne gå rød — målt
    # ved at slette `data-ti-hex` fra den rigtige fil, så beviset er en sætning
    # i koden der forsvinder, ikke et håndlavet mål.
    hex_k = (koer(kode, hele=True).get("hex") or {}).get("fix")
    tjek("farvekode-kæden leverer begge læsninger",
         bool(hex_k) and hex_k.get("harFix") is True
         and (hex_k.get("foer") or {}).get("harKnap") is True
         and (hex_k.get("efter") or {}).get("harKnap") is True,
         str(hex_k)[:300])
    # Prøven skal **læses** — hver mærkning på hende i `dom_hex` springes
    # over, når `praem` er `null`, så en læsning der altid er null gør
    # løftet til en tæller uden dom. Det var netop fejlen her 3/10:
    # prøven blev læst i knappens egen åbningstag, hvor den ikke står.
    tjek("harnessen læser farveprøven, ikke kun koden",
         (hex_k.get("foer") or {}).get("praem") is not None
         and (hex_k.get("efter") or {}).get("praem") is not None,
         str(hex_k)[:300])
    tjek("farveprøven er den samme kode som den der står i knappen",
         all(((hex_k.get(st) or {}).get("praem") or "").lower()
             == ((hex_k.get(st) or {}).get("hex") or "").lower()
             for st in ("foer", "efter")),
         str(hex_k)[:300])
    tjek("farvekode-dommen er grøn på den rigtige kode",
         not dom_hex("text-on-image-checker.html", {"fix": hex_k}),
         "; ".join(dom_hex("text-on-image-checker.html", {"fix": hex_k})))
    gammel_hex = ' data-ti-hex="\' + hexNu + \'"'
    tjek("mutationen findes i koden: data-ti-hex", gammel_hex in kode, repr(gammel_hex))
    hx_uden = dom_hex("text-on-image-checker.html", {"fix": (
        koer(kode.replace(gammel_hex, ' data-ti-hex-off="\' + hexNu + \'"', 1),
             hele=True).get("hex") or {}).get("fix")})
    tjek("farvekode-dommen kan se at koden forsvandt",
         any("ingen farvekode" in f for f in hx_uden), str(hx_uden)[:300])
    tjek("farvekode-dommen kan se en kæde uden rettelsesknap",
         any("ingen «fix»-knap" in f for f in
             dom_hex("text-on-image-checker.html", {"fix": {"harFix": False}})),
         "en kæde uden fix-knap blev dømt grøn")
    tjek("farvekode-dommen kan se en kæde, der slet ikke blev leveret",
         bool(dom_hex("text-on-image-checker.html", None)), "harnessen gav intet")

    # De fire løfter hver for sig, på et håndlavet mål der ligner et rigtigt.
    # Uden dem kunne et af løfterne være grønt kun fordi et andet fejler.
    def hex_kaede(**over):
        laes = {"harKnap": True, "erKnap": True, "hex": "#1a1a1a", "synlig": "#1a1a1a",
                "praem": "#1a1a1a", "felt": "#1a1a1a", "fik": 21.0}
        k = {"harFix": True, "foer": dict(laes), "efter": dict(laes, hex="#ffffff",
                                                              synlig="#ffffff",
                                                              praem="#ffffff",
                                                              felt="#ffffff")}
        k.update(over)
        return k

    def hex_dom(**over):
        return dom_hex("text-on-image-checker.html", {"fix": hex_kaede(**over)})

    tjek("farvekode-dommen er grøn på et rigtigt mål", not hex_dom(),
         "; ".join(hex_dom()))
    tjek("farvekode-dommen kan se en kode der ikke er farvefeltets",
         any("anden farve end den han ser" in f for f in
             hex_dom(foer={"harKnap": True, "erKnap": True, "hex": "#1a1a1a",
                           "synlig": "#1a1a1a", "praem": "#1a1a1a",
                           "felt": "#ff0000", "fik": 3.0})),
         "en fremmed farve blev dømt grøn")
    tjek("farvekode-dommen kan se en kode der overlever «Fix it»",
         any("står stadig" in f for f in
             hex_dom(efter={"harKnap": True, "erKnap": True, "hex": "#1a1a1a",
                            "synlig": "#1a1a1a", "praem": "#1a1a1a",
                            "felt": "#1a1a1a", "fik": 3.0})),
         "en uændret kode efter rettelsen blev dømt grøn")
    tjek("farvekode-dommen kan se en knap der viser én kode og gemmer en anden",
         any("læser den ene og kopierer den ande" in f for f in
             hex_dom(efter={"harKnap": True, "erKnap": True, "hex": "#ffffff",
                            "synlig": "#000000", "praem": "#ffffff",
                            "felt": "#ffffff", "fik": 21.0})),
         "to forskellige koder i én knap blev dømt grøn")
    tjek("farvekode-dommen kan se en farveprøve i en anden farve",
         any("farveprøven i knappen" in f for f in
             hex_dom(efter={"harKnap": True, "erKnap": True, "hex": "#ffffff",
                            "synlig": "#ffffff", "praem": "#ff0000",
                            "felt": "#ffffff", "fik": 21.0})),
         "en forkert farveprøve blev dømt grøn")
    tjek("farvekode-dommen kan se en kode der ikke kan indsættes i et værktøj",
         any("ikke er en `#rrggbb`-kode" in f for f in
             hex_dom(efter={"harKnap": True, "erKnap": True, "hex": "rgb(26,26,26)",
                            "synlig": "rgb(26,26,26)", "praem": "rgb(26,26,26)",
                            "felt": "rgb(26,26,26)", "fik": 21.0})),
         "en css-farve blev dømt grøn")
    tjek("farvekode-dommen kan se en kode der ikke er en knap",
         any("ikke en `<button>`" in f for f in
             hex_dom(efter={"harKnap": True, "erKnap": False, "hex": "#ffffff",
                            "synlig": "#ffffff", "praem": "#ffffff",
                            "felt": "#ffffff", "fik": 21.0})),
         "en span blev dømt grøn")
    # `copyHex` og `copied` skal findes på alle fire sider — artiklerne kører
    # ikke i harnessen, så de får den samme streng på kildefilen.
    tjek("farveknappens to tekster findes på alle fire sider",
         all(not dom_knapetekst(f, (SITE / f).read_text(encoding="utf-8"))
             for f in SIDER + ARTIKLER),
         "en side mangler copyHex eller copiedHex")

    # De otte løfter ovenfor skal kunne gå rød, ellers er de otte tal i
    # portens tæller løgn. Beviset er en nøgle der er omdøbt i **den rigtige
    # fil** — så dommen dømmer de samme otte tegn som i drift, og ikke en
    # håndlavet streng der kun ligner den.
    rigtig = (SITE / "text-on-image-checker.html").read_text(encoding="utf-8")
    for noegle, forventet in (("copyHex", "beskriver hvad knappen gør"),
                              ("copiedHex", "bekræfter trykket på den side den står på")):
        tjek(f"mutationen fandt `{noegle}` i den rigtige fil",
             f"{noegle}:" in rigtig, f"`{noegle}` fandtes ikke i kilden")
        fjernet = rigtig.replace(f"{noegle}:", f"{noegle}X:", 1)
        tjek(f"knappens dom kan se en side uden `{noegle}`",
             fjernet != rigtig
             and any(forventet in f for f in dom_knapetekst("x.html", fjernet)),
             f"en side uden `{noegle}` blev dømt grøn")
    # Dommen skal dømme **to** løfter, ikke ét: en side der mangler begge
    # nøgler skal få to fund. Ellers kunne den miste den ene og stadig tælle
    # den med, og det er samme fejl som en tæller på et hårdkodet antal.
    tjek("knappens dom dømmer begge nøgler, ikke kun den ene",
         len(dom_knapetekst("x.html", "ingen tekst overhovedet")) == 2,
         str(dom_knapetekst("x.html", "ingen tekst overhovedet")))

    # 14: markeringsknappen. Fire løfter, og hver skal kunne gå rød for sig —
    # ellers er de fire tal i `dom_mark` løgn. Beviset er fire mutationer i
    # **den rigtige fil**, en for hver fejlform:
    mark_ok = (koer(kode, hele=True) or {}).get("mark")
    tjek("markerings-dommen er grøn på den kode der kører",
         dom_mark(mark_ok) == [], str(dom_mark(mark_ok)))
    MARK_MUT = (
        # 1) Knappen er ikke i markup'en. Uden den dommen så grøn ud, fordi
        #    `s.markBtn` er sand på alle fire sider.
        ("markering: der står ingen knap",
         " data-ti-dl-mark title=", " data-ti-dlx title="),
        # 2) Den rene download får feltet med. Det er den mutation der
        #    *kun* findes fordi den nye knap er der: uden den markerede knap
        #    ville `downloadPng(true)` aldrig blive kaldt, så løftet «de to
        #    valg er to» ville være grønt på den mutation der sletter det.
        ("markering: den rene fil har",
         "if (dl) dl.addEventListener('click', function () { downloadPng(false); });",
         "if (dl) dl.addEventListener('click', function () { downloadPng(true); });"),
        # 3) Feltet peger på det *bedste* sted i stedet for det dårligste. Den
        #    er umærkelig på et ensfarvet billede — der er alle pixels lige
        #    gode — og det er derfor `baandet()` findes: den giver et billede,
        #    hvor det dårligste og det bedste er to *forskellige* steder.
        ("markering: feltet ligger over",
         "if (r < worst) { worst = r; worstOff = k === 0 ? minOff : maxOff; }",
         "if (r < worst) { worst = r; worstOff = minOff; }"),
        # 4) Forhåndsvisningen får ikke sin rene tegning tilbage, så feltet
        #    bliver stående på bruterens billede.
        ("feltpixel står stadig på",
         "      draw();\n      if (!dataUrl) return false;",
         "      if (false) draw();\n      if (!dataUrl) return false;"),
    )
    for forventet, gammel, ny in MARK_MUT:
        tjek(f"mutationen findes i koden: {forventet}", gammel in kode, repr(gammel))
        fund = dom_mark((koer(kode.replace(gammel, ny, 1), hele=True) or {}).get("mark"))
        tjek(f"mutationen gør markerings-dommen rød: {forventet}",
             any(forventet in f for f in fund), f"mutationen gav stadig grønt: {fund}")
    # Og dommen skal kunne dømme hvert løft *individuelt*, så ingen af dem er
    # grøn kun fordi et andet fejler.
    def mark_rigtig():
        return {"harKnap": True, "harRen": True, "etiket": "Hent med felt",
                "renMark": 0, "markMark": 412,
                "felt": {"x0": 163, "y0": 150, "x1": 186, "y1": 173, "antal": 412},
                "under": MARK_VAERST, "liveMark": 0}
    tjek("markerings-dommen er grøn på et rigtigt mål", dom_mark(mark_rigtig()) == [],
         str(dom_mark(mark_rigtig())))
    for beskrivelse, greb in (
            ("en knap uden tekst", {"etiket": "  "}),
            ("en ren fil med felt i", {"renMark": 12}),
            ("en markeret fil uden felt", {"markMark": 0}),
            ("et felt over den bedste baggrund", {"under": MARK_BEDST}),
            ("et felt der bliver stående på skærmen", {"liveMark": 12}),
            ("en markering der har taget den rene knaps plads", {"harRen": False})):
        fund_mark = dom_mark(dict(mark_rigtig(), **greb))
        tjek(f"markerings-dommen kan se {beskrivelse}", bool(fund_mark), str(fund_mark))
    tjek("markerings-dommen kan se en kæde, der slet ikke blev leveret",
         bool(dom_mark(None)), "harnessen gav intet")
    # Tallet i dommen skal være *slået op*, ikke antaget: den dårligste af de to
    # baggrunde i opstillingen er den hvide, fordi lys tekst på hvid er
    # 1,14:1 mens den samme tekst på sort er 14,63:1. Genregn begge her med
    # WCAG-formlen, så en byttet farve i opstillingen bliver rød.
    def mark_ratio(a, b):
        def rgb(h):
            return [int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16)]
        la, lb = lum(rgb(a)), lum(rgb(b))
        if la < lb:
            la, lb = lb, la
        return (la + 0.05) / (lb + 0.05)
    tjek("markerings-opstillingens dårligste baggrund er den hvide",
         mark_ratio(MARK_TEKST, MARK_VAERST) < mark_ratio(MARK_TEKST, MARK_BEDST),
         f"hvid {mark_ratio(MARK_TEKST, MARK_VAERST):.2f}:1 mod sort "
         f"{mark_ratio(MARK_TEKST, MARK_BEDST):.2f}:1")
    # Og de to strenge skal findes på alle fire sider — artiklerne kører ikke i
    # harnessen, så de får den samme dømning på kildefilen. En knap uden tekst
    # på den danske værktøjsside er en halv rettelse.
    for fil in SIDER + ARTIKLER:
        html = (SITE / fil).read_text(encoding="utf-8")
        tjek(f"markeringsknappen har en tekst på {fil}",
             "markBtn:" in html and "markTitle:" in html,
             f"`markBtn`/`markTitle` mangler i {fil}")

    for linje in fejl:
        print(f"  FEJL  {linje}")
    print(f"check-contrast-sampling-selftest: {'OK' if not fejl else 'RØD'} "
          f"({talt - len(fejl)}/{talt} kontroller)")
    return 1 if fejl else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list", action="store_true",
                        help="vis hvilke løfter der er dømt, kun talt")
    parser.add_argument("--self-test", action="store_true",
                        help="kør portens egen kontrol af sig selv")
    args = parser.parse_args(argv)
    if args.self_test:
        return self_test()

    fund: list[str] = []
    antal = 0
    for fil in SIDER:
        kode = hent_kode(fil)
        # Tælles på de rigtige resultater, ikke på et hårdkodet antal
        # stillinger. Målt 30/9 på den gamle kode: `+ 2` sagde 11 løfter pr.
        # side mens porten faktisk udførte 10 — den dømte altså 22 løfter
        # og kørte 20, to af dem uden dom. Samme fejlform som de fund
        # porten er bygget til at dømme: et løfte uden dom.
        svar = koer(kode, hele=True)
        r = svar["svar"]
        antal += len(r)
        for linje in dom(kode, r):
            fund.append(f"{fil}: {linje}")
        # «Fix it»-knappen dømmes på samme måde, og hver af de fire fix-cases
        # tæller som sit eget løfte — samme regel om at tælle på de rigtige
        # resultater i stedet for et hårdkodet antal.
        fixfund = dom_fix(svar.get("fix", []))
        antal += len(svar.get("fix", []))
        for linje in fixfund:
            fund.append(f"{fil}: {linje}")
        # To billeder i træk med «fix» imellem. De tre løfter tælles **kun**
        # når dommen faktisk har noget at dømme: ellers kunne en harness der
        # taber kæden stadig fremstille sig som «44 løfter dømt», og det er
        # præcis det en tæller på et hårdkodet antal gør.
        sek = svar.get("sekventiel")
        if sek:
            antal += 3
        for linje in dom_sekventiel(sek):
            fund.append(f"{fil}: {linje}")
        # Download: tre løfter på den fil værktøjet afleverer. Tælles kun når
        # dommen har noget at dømme — samme regel som den sekventielle kæde.
        dl = svar.get("download")
        if dl:
            antal += 3
        for linje in dom_download(dl):
            fund.append(f"{fil}: {linje}")
        # «Find det bedste sted»: fire løfter på den pladsering kernen vælger
        # — knap, bedre tal, beskrivelse der taler om samme måling, og
        # beskrivelsen væk igen når bruteren selv flytter teksten. Tælles kun
        # når dommen fik en kæde at dømme, samme regel som de to andre.
        spot = svar.get("spot")
        if spot:
            antal += 4
        for linje in dom_spot(spot):
            fund.append(f"{fil}: {linje}")
        # Før → nu: fire løfter pr. indgreb — linjen findes, før-tallet er det
        # der stod, nu-tallet er det på skærmen, og linjen væk når bruteren selv
        # griber ind. Begge kæder dømmes, fordi de er to forskellige indgreb i
        # kernen og kan glemme hver deres. Tælles pr. kæde der har noget at
        # dømme — samme regel som de tre kæder over, og derfor ikke ét fast
        # tal for dommen som helhed.
        delta_kæder = {"fix": (svar.get("delta") or {}).get("fix"), "spot": spot}
        antal += 5 * sum(1 for k in delta_kæder.values() if k)
        for linje in dom_delta(fil, delta_kæder):
            fund.append(f"{fil}: {linje}")
        # Demo-tilstanden: fem løfter på den tekst værktøjet skriver, før
        # bruteren har valgt et billede. Tælles kun når dommen fik noget at
        # dømme — samme regel som de tre kæder over.
        demo = svar.get("demo")
        if demo:
            antal += 5
        for linje in dom_demo(fil, demo):
            fund.append(f"{linje}")
        # Farvekoden: fire løfter på den værdi bruteren skal kunne kopiere —
        # den findes som en knap, den er farvefeltets værdi, den følger «Fix
        # it», og den læses samme sted som den gemmes. Tælles kun når
        # dommen fik en kæde at dømme, samme regel som de andre.
        hex_kæde = (svar.get("hex") or {}).get("fix")
        if hex_kæde:
            antal += 4
        for linje in dom_hex(fil, {"fix": hex_kæde}):
            fund.append(f"{linje}")
        # To tekstblokke: seks løfter på den egenskab der gør værktøjet
        # brugbart på det vanligste reelle tilfælde. Tælles kun når dommen fik
        # en måling at dømme — samme regel som de andre kæder.
        blok = svar.get("blok")
        if blok:
            antal += 6
        for linje in dom_blokke(blok):
            fund.append(f"{linje}")
        # Gradient-baggrunden: fire løfter på den anden rute ind i *samme*
        # måling. Tælles kun når dommen fik en måling at dømme — samme regel som
        # de andre kæder.
        grad = svar.get("gradient")
        if grad:
            antal += 4
        for linje in dom_gradient(grad):
            fund.append(f"{linje}")

    # Ratchet på den tekst kernen *skriver til læseren*. `suggestFix()`
    # prøver slør i begge retninger og vælger den mindste dækning, så på et
    # lyst billede vinder det hvide slør med sort tekst. En side med kun én
    # nøgle — eller med «mørkt» i den — ville fortælde læseren at have lagt
    # et mørkt lag, når der ligger et lyst. Det er en påstand i brødteksten,
    # og den skal kunne gå rød: derfor dømmes nøglerne, ikke et tegn.
    for fil in SIDER + ARTIKLER:
        html = (SITE / fil).read_text(encoding="utf-8")
        antal += 2
        for noegle in ("fixedScrimDark", "fixedScrimLight"):
            m = re.search(rf"{noegle}:\s*'([^']*)'", html)
            if m is None:
                fund.append(f"{fil}: der er ingen `{noegle}`-tekst, så det lag "
                            "kernen faktisk lagde bliver ikke beskrevet")
            elif "%s" not in m.group(1):
                fund.append(f"{fil}: `{noegle}` indeholder ikke `%s`, så "
                            "dækningen står ikke i den beskrivelse læseren læser")
        if re.search(r"\bfixedScrim\s*:", html):
            fund.append(f"{fil}: `fixedScrim` med ét ord for begge slørretninger "
                        "— brug `fixedScrimDark` og `fixedScrimLight`")
        # Artiklerne køres ikke i harnessen, så de får den samme streng dømt
        # på kildefilen: de to indlejrer *samme* kerne og må derfor ikke stå
        # med en demo-note på den anden side eller slet ingen. Det er den
        # fejlform porten her helst dømmer på fire steder og ikke to — en
        # note der kun findes på værktøjssiden er halv rettet.
        antal += 1
        if re.search(r"demoNote:\s*'([^']*)'", html) is None:
            fund.append(f"{fil}: der er ingen `demoNote`-tekst, så værktøjet på "
                        "siden måler på sit eget eksempelbillede uden at sige det")
        # `delta`-strengen skal have **to** `%s`. Kernen sætter det første tal
        # ind og derefter det andet med to `.replace('%s', …)` i træk, så en
        # streng med kun ét `%s` viser «før 1,16:1» og lader «nu» mangle — og
        # dommen på attributtet ville aldrig kunne se det, fordi den læser
        # `data-ti-delta` og ikke den sætning læseren læser.
        antal += 1
        mdelta = re.search(r"delta:\s*'([^']*)'", html)
        if mdelta is None:
            fund.append(f"{fil}: der er ingen `delta`-tekst, så værktøjet ikke kan "
                        "sige hvad kernens egen rettelse rettede")
        elif mdelta.group(1).count("%s") != 2:
            fund.append(f"{fil}: `delta` har {mdelta.group(1).count('%s')} af de to "
                        "`%s` den skal have, så læseren får kun ét af de to tal")
        # Farveknappens to tekster skal findes på **alle fire** sider. Knapperne
        # males ikke af `dom_hex` på artiklerne — de kører kernen med andre
        # billeder — så de får den samme streng dømt på kildefilen, fordi en
        # tekst der kun findes på værktøjssiden er en halv rettelse.
        antal += 2
        fund.extend(dom_knapetekst(fil, html))

    if args.list:
        for linje in fund:
            print(linje)
        print(f"\ncontrast-sampling: {antal} løfter dømt på {len(SIDER)} sider")
        return 1 if fund else 0
    for linje in fund:
        print(linje)
    if fund:
        print(f"\ncontrast-sampling: RØD — {len(fund)} af {antal} løfter er forkerte")
        return 1
    print(f"contrast-sampling: GRØN — {antal} løfter dømt på {len(SIDER)} sider, "
          "alle matcher WCAG 2.1 for billedets og tekstens farve")
    return 0


if __name__ == "__main__":
    sys.exit(main())
