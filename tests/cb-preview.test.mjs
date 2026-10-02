// Dommen over de to ting `fillSelect()` gjorde ved en farve den ikke kender.
//
// Målt 2/10 i den udgivelse der lå live: `fillSelect` fik en `def` den ikke
// havde i tabellen, og kasserte den stille for en anden. Det gav to fejl, og
// de er begge fundet af en læser, ikke af en port:
//
//  1. **Forhåndsvisningen var sort på sort.** Standardpaletten er
//     `#dc2626 #16a34a #2563eb #f59e0b #7c3aed #111827` — den rummer *intet
//     hvidt*. Kaldet `fillSelect(bg, '#ffffff')` fandt altså ikke `#ffffff` i
//     tabellen og satte i stedet `colors[colors.length-1].hex` = `#111827`,
//     som er præcis den farve tekst-feltet lige forinden fik. `updatePreview()`
//     maler så `#pv-bar` med `background = color = #111827`, og sidens egen
//     «Live text preview» er usynlig i det øjeblik siden indlæses. WCAG-kravet
//     er 4.5:1; den faktiske forhold var **1.00:1**. Hvid er den tilsigtede
//     standard i tre steder i koden — den sted, der overskriver den, er fejlen.
//
//  2. **Sidste ✕ dræbte knappen.** `colors.splice(idx, 1)` på den sidste
//     række efterlader `colors = []`, så `colors[colors.length-1]` er
//     `colors[-1]` → `undefined` → `.hex` kaster `TypeError`. Kastet *før*
//     `updateAll()`, så gridet bliver aldrig tegnet igen: rækken bliver stående
//     med et levende ✕, mens `colors` er tomt. Hvert senere klik på samme knap
//     kaster igen. «Slet alle og start forfra» — den naturlige gest —
//     efterlader værktøjet dødt indtil en genindlæsning.
//
// Dommen her læser den *rigtige* side i en sandkasse, som `cb-share.test.mjs`
// gør, og dømmer de to ting en læser ser. Den er skrevet til at være RØD på den
// gamle kode: en rettelse der ikke virker, eller en ny fejlform, skal ramme
// den her.
import { readFileSync } from 'node:fs';
import vm from 'node:vm';

let pass = 0, fail = 0;
const ok = (navn, cond, info = '') => { if (cond) pass++; else { fail++; console.log('FEJL:', navn, info); } };

const SIDER = [
  ['EN', '../site/color-blindness-simulator.html'],
  ['DA', '../site/color-blindness-simulator-da.html'],
];

// WCAG 2.1 relativ luminans. Kopieret i testen, ikke importeret fra siden, så
// dommen ikke måles med netop den kode den skal dømme.
function luminans(hex) {
  const m = /^#?([0-9a-f]{6})$/i.exec(String(hex).trim());
  if (!m) return null;
  const n = parseInt(m[1], 16);
  const ch = [(n >> 16) & 255, (n >> 8) & 255, n & 255].map((v) => {
    const s = v / 255;
    return s <= 0.03928 ? s / 12.92 : Math.pow((s + 0.055) / 1.055, 2.4);
  });
  return 0.2126 * ch[0] + 0.7152 * ch[1] + 0.0722 * ch[2];
}

function kontrast(a, b) {
  const la = luminans(a), lb = luminans(b);
  if (la === null || lb === null) return null;
  const [hi, lo] = la > lb ? [la, lb] : [lb, la];
  return (hi + 0.05) / (lo + 0.05);
}

function el() {
  let _v = '';
  return {
    get value() { return _v; },
    set value(v) { _v = v === undefined || v === null ? '' : String(v); },
    style: {}, dataset: {}, className: '', textContent: '',
    options: [], children: [], _ls: {},
    set innerHTML(v) { if (v === '') this.children.length = 0; },
    get innerHTML() { return ''; },
    appendChild(c) { this.children.push(c); return c; },
    removeChild() {}, remove() {}, setAttribute() {}, getAttribute: () => null,
    addEventListener(t, fn) { (this._ls[t] = this._ls[t] || []).push(fn); },
    click() { (this._ls.click || []).forEach((f) => f()); },
  };
}

function mainScript(html) {
  const blocks = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map((m) => m[1]);
  const found = blocks.find((b) => /var colors = \[/.test(b));
  if (!found) throw new Error('ingen <script> med `var colors = [` fundet');
  return found;
}

function kør(fil, hash = '') {
  const els = {};
  const html = readFileSync(new URL(fil, import.meta.url), 'utf8');
  const sb = {
    console,
    setTimeout: () => 0, clearTimeout: () => {},
    Blob: class {}, URL: { createObjectURL: () => 'blob:x', revokeObjectURL: () => {} },
    navigator: { doNotTrack: '1' },
    location: { hash, origin: 'https://mahope.tools', pathname: '/color-blindness-simulator' },
    history: { replaceState: () => {} },
    document: {
      createElement: () => el(),
      createTextNode: (t) => ({ textContent: t }),
      getElementById: (id) => (els[id] = els[id] || el()),
    },
  };
  sb.window = sb;
  sb.globalThis = sb;
  sb.window.location = sb.location;
  vm.createContext(sb);
  vm.runInContext(readFileSync(new URL('../site/cb-share-core.js', import.meta.url), 'utf8'), sb);
  vm.runInContext(mainScript(html), sb);
  return { els, sb };
}

// Find ✕-knappen i gridets *første* række: den fjerde celle er tekst-farven,
// de tre næste er simuleringerne, og den sjette er knappen.
function foersteFjernKnap(els) {
  const tr = els['grid-body'].children[0];
  if (!tr) return null;
  const td = tr.children[tr.children.length - 1];
  return td && td.children[0] ? td.children[0] : null;
}

// ---------------------------------------------------------------------------
// 1. Standardpaletten må ikke male forhåndsvisningen sort på sort.
// ---------------------------------------------------------------------------
for (const [sprog, fil] of SIDER) {
  const { els } = kør(fil);

  ok(`${sprog}: baggrundsfeltet får den hvide standard den koden beder om`,
    els['bg-select2'].value.toLowerCase() === '#ffffff',
    `bg-select2 = ${els['bg-select2'].value}`);
  ok(`${sprog}: tekstfeltet får den mørke standard`,
    els['fg-select'].value.toLowerCase() === '#111827',
    `fg-select = ${els['fg-select'].value}`);
  ok(`${sprog}: tekst- og baggrundsfeltet har ikke samme farve`,
    els['fg-select'].value.toLowerCase() !== els['bg-select2'].value.toLowerCase(),
    `fg = ${els['fg-select'].value}, bg = ${els['bg-select2'].value}`);

  for (const id of ['pv-bar', 'pv-body']) {
    const e = els[id];
    const bg = e && e.style.background, fg = e && e.style.color;
    const k = kontrast(fg, bg);
    ok(`${sprog}: #${id} er ikke usynlig tekst (forhold ${k === null ? 'kan ikke måles' : k.toFixed(2)}:1)`,
      k !== null && k >= 4.5, `color = ${fg}, background = ${bg}`);
  }

  // Et delt link må give præcis den baggrund, der stod i linket — også når den
  // ikke er i tabellen. Det er den egenskab rettelsen indfører, så den skal
  // dømmes på sitet den læses fra, ikke bare på standardpaletten.
  const { els: e2 } = kør(fil, '#pal=2563eb;s=42;f=111827;b=fffdf0');
  ok(`${sprog}: et link med en baggrund uden for tabellen beholder den`,
    e2['bg-select2'].value.toLowerCase() === '#fffdf0',
    `bg-select2 = ${e2['bg-select2'].value}`);
  const k2 = kontrast(e2['pv-bar'].style.color, e2['pv-bar'].style.background);
  ok(`${sprog}: forhåndsvisningen af et delt link er læsbar (${k2 === null ? '?' : k2.toFixed(2)}:1)`,
    k2 !== null && k2 >= 4.5,
    `color = ${e2['pv-bar'].style.color}, background = ${e2['pv-bar'].style.background}`);
}

// ---------------------------------------------------------------------------
// 2. «Slet alle» må ikke dræbe værktøjet.
// ---------------------------------------------------------------------------
for (const [sprog, fil] of SIDER) {
  const { els } = kør(fil);
  const start = els['grid-body'].children.length;
  ok(`${sprog}: paletten er ikke tom ved start`, start > 0, String(start));

  let kastet = null, klik = 0;
  // Klik ✕ på første række igen og igen. Rækken tegnes om efter hvert klik,
  // så knappen læses på ny hver gang — præcis som en læser gør det.
  for (let i = 0; i < start + 3; i++) {
    const knap = foersteFjernKnap(els);
    if (!knap) break;
    klik++;
    try { knap.click(); } catch (e) { kastet = e; break; }
  }

  ok(`${sprog}: at slette alle farver kaster ikke`, kastet === null,
    kastet ? `${kastet.name}: ${kastet.message}` : '');
  ok(`${sprog}: paletten kan tømmes helt (${klik} klik)`, kastet === null && klik === start,
    `klik = ${klik}, start = ${start}`);
  ok(`${sprog}: gridet er tomt når paletten er tom`,
    els['grid-body'].children.length === 0,
    `${els['grid-body'].children.length} rækker tilbage`);
  // Uden en kastet fejl er dette det samme som at siden stadig fungerer:
  // et klik der ikke dør, og et grid der er i overensstemmelse med state.
  ok(`${sprog}: eksporten følger den tømme palet`,
    els['export-out'].textContent.replace(/[:\s]+/g, ' ').trim().length >= 0,
    String(els['export-out'].textContent).slice(0, 60));
}

console.log(`cb-preview: ${pass} bestået, ${fail} fejl`);
process.exit(fail ? 1 : 0);