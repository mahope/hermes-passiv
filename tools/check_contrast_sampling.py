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
    if (v && v.addColorStop) { this._fill = [128, 128, 128]; this._alpha = 1; return; }
    const m = /^#([0-9a-f]{6})([0-9a-f]{2})?$/i.exec(String(v || '#000'));
    if (!m) { this._fill = hexToRgb(v || '#000'); this._alpha = 1; return; }
    this._fill = hexToRgb('#' + m[1]);
    this._alpha = m[2] === undefined ? 1 : parseInt(m[2], 16) / 255;
  }
  get fillStyle() { return '#000000'; }
  clearRect() { this.buf.data.fill(0); }
  // Sløret males *rigtigt* ind i bufferen, så `getImageData` læser den
  // blanding læseren ser. Uden dette ville porten måle billedet uden slør og
  // «fix»-dommen ville være grøn på et tal værktøjet ikke viser.
  fillRect(x, y, w, h) {
    const d = this.buf, W = this.cv.width, a = this._alpha === undefined ? 1 : this._alpha;
    const x0 = Math.max(0, Math.round(x)), y0 = Math.max(0, Math.round(y));
    const x1 = Math.min(W, Math.round(x + w)), y1 = Math.min(this.cv.height, Math.round(y + h));
    for (let py = y0; py < y1; py++) for (let px = x0; px < x1; px++) {
      const i = (py * W + px) * 4;
      for (let k = 0; k < 3; k++) d.data[i + k] = Math.round(this._fill[k] * a + d.data[i + k] * (1 - a));
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
  createLinearGradient() { return { addColorStop() {} }; }
  beginPath() {} arc() {} fill() {}
}

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
    if (attr && !new RegExp('\\b' + attr[1] + '\\b').test(this.innerHTML || '')) return null;
    if (!this._q[sel]) this._q[sel] = new El(sel);
    return this._q[sel];
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

console.log(JSON.stringify({
  svar: svar, fix: fixSvar,
  sekventiel: {
    efter: sekB1, refer: renB2,
    farve: sekFarve, farveEfterFix: farveEfterFix,
    fixA: fixA,
  },
  download: dlMaal,
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
     "      var x = Math.max(0, Math.round(tx)), y = Math.max(0, Math.round(ty));",
     "      var x = 0, y = Math.max(0, Math.round(ty));"),
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
     "      drawTextLayer();",
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
     "      [visMin, visMax].forEach(function (c) {",
     "      [visMax].forEach(function (c) {"),
    # Flytter tekstkassen opad i stedet for at klippe den. Det er den fejl
    # der læseren mærker først på et fladt billede: kassen løber op i det
    # hvide og svaret falder fra 21:1 til 1:1.
    ("flytter tekstkassen opad i stedet for at klippe den",
     "      var x = Math.max(0, Math.round(tx)), y = Math.max(0, Math.round(ty));",
     "    var x = Math.max(0, Math.round(tx)), y = Math.max(0, Math.min(cv.height - fontSizePx() - 1, Math.round(ty)));"),
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

    # 5: de to sider skal dømme ens. Den danske er en oversættelse, ikke en
    # egen algoritme, så et tal der kun er rigtigt på den ene er en fejl.
    en, da = dom(kode), dom(hent_kode(SIDER[1]))
    tjek("EN-siden er grøn", not en, "; ".join(en))
    tjek("DA-siden er grøn", not da, "; ".join(da))

    # 5b: den sekventielle kæde skal finde præcis den fejl, den er skrevet
    # til. Fundet i review 3/10 og målt i rigtig Chromium: `loadFile()`
    # nulstillede hverken `scrim` eller `lastFix`, så sløret fra foto A blev
    # tegnet på foto B. Det er den eneste fejl i denne port der *kun* kan ses
    # i en kæde, så mutationen her er portens vigtigste.
    gammel_reset = ("        scrim = null;\n        lastFix = null;\n"
                    "        var maxW = 900;")
    tjek("mutationen findes i koden: loadFile() nulstiller sløret",
         gammel_reset in kode, repr(gammel_reset))
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
        koer(kode.replace(gammel_reset, "        var maxW = 900;", 1), hele=True)
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
    spring = kode.replace("      [visMin, visMax].forEach(function (c) {",
                         "      [visMax].forEach(function (c) {", 1)
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
        (koer(kode.replace("      draw();\n      var dataUrl;",
                           "      drawTextLayer();\n      var dataUrl;", 1),
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
