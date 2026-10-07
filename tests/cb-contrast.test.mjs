// Dommen over kontrast-tabellen pr. synstype i farveblindhedssimulatoren (EN + DA).
//
// Farve-tabellen viser hvordan en farve *ser ud* for protan-, deuteran- og
// tritanopi, og forhåndsvisningen maler et tekststykke i de simulerede farver.
// Men den sagde ikke det tal en læser kan handle på: WCAG-forholdet mellem
// tekst og baggrund *for den synstype*. Et par kan bestå AA for normalt syn og
// falde under 4.5:1 for en deuteranop, fordi rød og grøn nærmer sig hinanden i
// lysstyrke — præcis den forskel et almindeligt kontrasttjek ikke ser, og som
// de store simulatorer viser. `site/cb-contrast.js` lukker hullet.
//
// Dommen holder to ting fast der begge kan gå stille i stykker:
//
//   1. **Tallet kommer fra den rigtige model.** `readout()` skal bruge
//      `CB_SIM.simulate` — den funktion tabellen selv bruger — og regne WCAG
//      korrekt oven på den. Testen har sin *egen* luminans-implementering og
//      kræver præcis samme forhold, så en kopi af formlen der driver fra
//      specifikationen bliver fanget.
//
//   2. **Begge sprogudgaver kalder den.** Den danske side er en
//      håndvedligeholdt kopi; en kopi der glemmer script-tagget eller
//      mount-kaldet ville se ud til at virke på den engelske. Derfor læses
//      begge *rigtige* sider.
//
// Dommen er skrevet til at være RØD på koden før denne opgave: `cb-contrast.js`
// findes ikke, ingen side har `#cvd-contrast`, og ingen kalder `CBCONTRAST.mount`.
import { readFileSync } from 'node:fs';
import vm from 'node:vm';

let pass = 0, fail = 0;
const ok = (navn, cond, info = '') => { if (cond) pass++; else { fail++; console.log('FEJL:', navn, info); } };

const SIDER = [
  ['EN', '../site/color-blindness-simulator.html'],
  ['DA', '../site/color-blindness-simulator-da.html'],
];

// WCAG 2.1 relativ luminans. Kopieret i testen, ikke importeret fra modulet, så
// dommen ikke måles med netop den kode den skal dømme.
function luminans(rgb) {
  const c = rgb.slice(0, 3).map((v) => {
    const s = v / 255;
    return s <= 0.03928 ? s / 12.92 : Math.pow((s + 0.055) / 1.055, 2.4);
  });
  return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2];
}
function kontrast(a, b) {
  let la = luminans(a), lb = luminans(b);
  if (la < lb) { const t = la; la = lb; lb = t; }
  return (la + 0.05) / (lb + 0.05);
}
function hex(h) {
  h = String(h).replace('#', '');
  return [parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16), parseInt(h.slice(4, 6), 16)];
}

// Samme minimale DOM som `cb-image.test.mjs`.
function el() {
  let _v = '';
  return {
    get value() { return _v; },
    set value(v) { _v = v === undefined || v === null ? '' : String(v); },
    style: {}, dataset: {}, className: '', textContent: '', hidden: false,
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

function kør(fil) {
  const els = {};
  const html = readFileSync(new URL(fil, import.meta.url), 'utf8');
  const sb = {
    console,
    setTimeout: () => 0, clearTimeout: () => {},
    navigator: { doNotTrack: '1' },
    location: { hash: '', origin: 'https://mahope.tools', pathname: '/color-blindness-simulator' },
    history: { replaceState: () => {} },
    document: {
      createElement: () => el(),
      getElementById: (id) => (els[id] = els[id] || el()),
      addEventListener: () => {},
    },
  };
  sb.window = sb;
  sb.globalThis = sb;
  sb.window.location = sb.location;
  vm.createContext(sb);
  vm.runInContext(readFileSync(new URL('../site/cb-share-core.js', import.meta.url), 'utf8'), sb);
  vm.runInContext(mainScript(html), sb);
  vm.runInContext(readFileSync(new URL('../site/cb-image.js', import.meta.url), 'utf8'), sb);
  vm.runInContext(readFileSync(new URL('../site/cb-contrast.js', import.meta.url), 'utf8'), sb);
  return { sb, els };
}

// ---------------------------------------------------------------------------
// 1. Modulet skal eksponere den rene beregning og kunne mountes.
// ---------------------------------------------------------------------------
const { sb, els } = kør(SIDER[0][1]);
ok('siden eksponerer CB_SIM', sb.CB_SIM && typeof sb.CB_SIM.simulate === 'function');
ok('cb-contrast.js eksporterer mount og readout',
  sb.CBCONTRAST && typeof sb.CBCONTRAST.mount === 'function' && typeof sb.CBCONTRAST.readout === 'function',
  Object.keys(sb.CBCONTRAST || {}).join(','));
{
  const monteret = sb.CBCONTRAST.mount({ strings: {} });
  ok('mount() returnerer en update-funktion', monteret && typeof monteret.update === 'function',
    JSON.stringify(monteret));
}

// ---------------------------------------------------------------------------
// 2. Tallet skal komme fra CB_SIM-modellen og den rigtige WCAG-formel.
// ---------------------------------------------------------------------------
const PAR = [
  ['#111827', '#ffffff', 1.0],
  ['#dc2626', '#ffffff', 1.0],
  ['#2563eb', '#f59e0b', 1.0],
  ['#16a34a', '#000000', 0.5],
  ['#7c3aed', '#e2e8f0', 0.8],
  ['#dc2626', '#16a34a', 1.0],
];
const TYPER = ['protanomaly', 'deuteranomaly', 'tritanomaly'];
let sammenligninger = 0;
for (const [fgHex, bgHex, sev] of PAR) {
  const res = sb.CBCONTRAST.readout(fgHex, bgHex, sev, {});
  ok(`readout svarer for ${fgHex} på ${bgHex}`, !!res, String(res));
  if (!res) continue;
  const fg = hex(fgHex), bg = hex(bgHex);
  const forventet = [
    kontrast(fg, bg),
    ...TYPER.map((t) => kontrast(sb.CB_SIM.simulate(fg.slice(), t, sev), sb.CB_SIM.simulate(bg.slice(), t, sev)))
  ];
  res.rows.forEach((row, i) => {
    sammenligninger++;
    ok(`forhold matcher (${fgHex}/${bgHex} @ ${sev}, række ${i})`,
      Math.abs(row.ratio - forventet[i]) < 1e-9,
      `fik ${row.ratio}, forventede ${forventet[i]}`);
    ok(`AA-flag matcher (${fgHex}/${bgHex} @ ${sev}, række ${i})`,
      row.passesNormal === (forventet[i] >= 4.5) && row.passesLarge === (forventet[i] >= 3),
      `passesNormal=${row.passesNormal}, passesLarge=${row.passesLarge}, ratio=${forventet[i]}`);
  });
}
ok('dommen har sammenlignet et reelt antal forhold', sammenligninger >= 24, String(sammenligninger));

// ---------------------------------------------------------------------------
// 3. Hele pointen: et par der består for normalt syn, men fejler for en
//    farveblind. `#dc2626` på hvidt er 4.83:1 normalt, men rød falder mod hvid
//    under deuteranopi. Dommen finder de typer der *falder under* selv.
// ---------------------------------------------------------------------------
{
  const res = sb.CBCONTRAST.readout('#dc2626', '#ffffff', 1, { deutan: 'Deuteranopia', tritan: 'Tritanopia', protan: 'Protanopia' });
  ok('rød på hvidt består AA for normalt syn', res.normalPasses === true);
  const fg = hex('#dc2626'), bg = hex('#ffffff');
  const forventDropped = TYPER.filter((t) => {
    const r = kontrast(sb.CB_SIM.simulate(fg.slice(), t, 1), sb.CB_SIM.simulate(bg.slice(), t, 1));
    return r < 4.5;
  });
  ok('de typer der falder under 4.5:1 er fundet', forventDropped.length > 0, forventDropped.join(','));
  ok('de fundne typer er præcis dem modellen siger',
    res.dropped.length === forventDropped.length,
    `modulet: ${res.dropped.join(',')} — forventet: ${forventDropped.join(',')}`);
}

// ---------------------------------------------------------------------------
// 4. 0 % er normalt syn: alle rækker skal være identiske med den normale.
// ---------------------------------------------------------------------------
{
  const res = sb.CBCONTRAST.readout('#2563eb', '#f59e0b', 0, {});
  const norm = res.rows[0].ratio;
  ok('ved 0 % er alle synstyper ens',
    res.rows.every((row) => Math.abs(row.ratio - norm) < 1e-12),
    res.rows.map((r) => r.ratio.toFixed(4)).join(','));
  ok('ved 0 % er der ingen farveblinde-fald', res.dropped.length === 0);
}

// ---------------------------------------------------------------------------
// 5. Uden modellen skal den rene beregning sige fra, ikke gætte.
// ---------------------------------------------------------------------------
{
  const { sb: sb2 } = kør(SIDER[0][1]);
  const gemt = sb2.CB_SIM;
  sb2.CB_SIM = null;
  const res = sb2.CBCONTRAST.readout('#000000', '#ffffff', 1, {});
  sb2.CB_SIM = gemt;
  ok('readout uden CB_SIM returnerer null', res === null, String(res));
}

// ---------------------------------------------------------------------------
// 6. Begge sider skal indlæse kernen, have containeren og kalde mount.
// ---------------------------------------------------------------------------
for (const [sprog, fil] of SIDER) {
  const html = readFileSync(new URL(fil, import.meta.url), 'utf8');
  ok(`${sprog}: indlæser /cb-contrast.js`, /<script src="\/cb-contrast\.js"><\/script>/.test(html));
  ok(`${sprog}: har containeren #cvd-contrast`, /id="cvd-contrast"/.test(html));
  ok(`${sprog}: kalder CBCONTRAST.mount`, /CBCONTRAST\.mount\(/.test(html));
}

console.log(`cb-contrast: ${pass} bestået, ${fail} fejl`);
process.exit(fail ? 1 : 0);
