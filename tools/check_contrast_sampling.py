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
# Udtrækningen. Kun den første inline-<script> der definerer `sampleContrast`
# — den er sideens egen kode, ikke en kopi i porten.
# --------------------------------------------------------------------------
IIFE_RE = re.compile(
    r"<script(?![^>]*\bsrc=)[^>]*>\s*(\(function\s*\(\)\s*\{.*?\}\)\(\);)\s*</script>",
    re.S | re.I,
)


def hent_kode(fil: str) -> str:
    """Sideens egen sampling-kode, eller en fejl der siger hvorfor ikke."""
    html = (SITE / fil).read_text(encoding="utf-8")
    for m in IIFE_RE.finditer(html):
        if "sampleContrast" in m.group(1):
            return m.group(1)
    raise SystemExit(
        f"FEJL: {fil} har ingen inline-<script> der definerer sampleContrast(). "
        "Er samplingslogikken flyttet ud i site/*.js? Så skal denne port "
        "læse den fil i stedet for HTML'en.")


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
  set fillStyle(v) { this._fill = (v && v.addColorStop) ? [128, 128, 128] : hexToRgb(v || '#000'); }
  get fillStyle() { return '#000000'; }
  clearRect() { this.buf.data.fill(0); }
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
  beginPath() {} arc() {} fill() {} fillRect() {}
}

class Canvas {
  constructor(w, h) { this.width = w; this.height = h; this._ctx = null; }
  getContext() { if (!this._ctx) this._ctx = new Ctx(this); return this._ctx; }
  getBoundingClientRect() { return { left: 0, top: 0, width: this.width, height: this.height }; }
  get _pix() { return { w: this.width, h: this.height, data: this.getContext().buf.data }; }
}

class El {
  constructor(id, opts) {
    opts = opts || {};
    this.id = id; this._v = opts.value || ''; this._l = {};
    this.textContent = ''; this.innerHTML = ''; this.hidden = false; this.className = '';
    this.files = []; this._c = opts.canvas || null;
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
  getBoundingClientRect() { return this._c.getBoundingClientRect(); }
  addEventListener(t, fn) { (this._l[t] = this._l[t] || []).push(fn); }
  fire(t, ev) { (this._l[t] || []).forEach(function (f) { f(ev || {}); }); }
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

// ==========================================================================
// DOM'en sidekoden får, og så kører den.
// ==========================================================================
const cv = new Canvas(300, 150);
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
  createElement: function (t) { return t === 'canvas' ? new Canvas(1, 1) : new El(t); },
};
globalThis.window = { addEventListener: function () {} };
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
console.log(JSON.stringify(svar));
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
     "    var x = Math.max(0, Math.round(tx)), y = Math.max(0, Math.round(ty));",
     "    var x = 0, y = Math.max(0, Math.round(ty));"),
    # Den gamle kode i dens egen, kortere form: ét lag med billede *og* tekst,
    # brugt som både baggrund og dækningskort, uden filter. Det er præcis
    # fejlen der gav 1,47:1 for hvid tekst på hvid, og for hvid tekst over
    # den mørke halvdel tæller de hvide bogstaver som den lyseste baggrund:
    # 1:1 i stedet for 21:1.
    ("læser farverne fra det lag der indeholder teksten",
     "    ctx.clearRect(0, 0, cv.width, cv.height);\n"
     "    ctx.drawImage(img, 0, 0, cv.width, cv.height);\n"
     "    var photo = ctx.getImageData(box.x, box.y, box.w, box.h).data;\n"
     "    // Pass 2 — the letters alone, so alpha is the glyph coverage.\n"
     "    drawTextLayer();",
     "    draw();\n"
     "    var photo = ctx.getImageData(box.x, box.y, box.w, box.h).data;\n"
     "    var glyph = ctx.getImageData(box.x, box.y, box.w, box.h).data;\n"
     "    if (false) drawTextLayer();"),
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
     "    [minC, maxC].forEach(function (c) {",
     "    [maxC].forEach(function (c) {"),
    # Flytter tekstkassen opad i stedet for at klippe den. Det er den fejl
    # der læseren mærker først på et fladt billede: kassen løber op i det
    # hvide og svaret falder fra 21:1 til 1:1.
    ("flytter tekstkassen opad i stedet for at klippe den",
     "    var x = Math.max(0, Math.round(tx)), y = Math.max(0, Math.round(ty));",
     "    var x = Math.max(0, Math.round(tx)), y = Math.max(0, Math.min(cv.height - fontSizePx() - 1, Math.round(ty)));"),
)


def byg_kode(kode: str) -> str:
    return (HARNESS.replace("%%SIDENS_KODE%%", kode)
            .replace("__FARVEPAR__", json.dumps([list(p) for p in FARVEPAR]))
            .replace("__FLADT__", json.dumps(list(FLADT)))
            .replace("__GRADIENT__", json.dumps(list(GRADIENT)))
            .replace("__GRADIENT_TEKST__", json.dumps(GRADIENT_TEKST))
            .replace("__TODELT__", json.dumps(list(TODELT))))


def koer(kode: str) -> list[dict]:
    """Kør sidekoden i Node-harnessen og læs de tal den viser."""
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
    linje = [l for l in p.stdout.splitlines() if l.startswith("[")]
    if not linje:
        raise SystemExit("FEJL: harnessen skrev intet resultat:\n" + p.stdout[:2000])
    return json.loads(linje[-1])


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
    spring = kode.replace("    [minC, maxC].forEach(function (c) {",
                         "    [maxC].forEach(function (c) {", 1)
    bedste = {r["navn"]: r["fik"] for r in koer(spring)}.get(GRADIENT[0])
    tjek("gradientet kan svare 21:1 når kun den bedste baggrund tælles",
         naer(bedste, 21.00),
         f"mutationen svarede {bedste}, så casen kan ikke se forskellen")

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
        r = koer(kode)
        antal += len(r)
        for linje in dom(kode, r):
            fund.append(f"{fil}: {linje}")
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
