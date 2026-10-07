// Dommen over billed-simuleringen i farveblindhedssimulatoren (EN + DA).
//
// Farve-tabellen på siden viser et par udvalgte farver. De fleste kommer for
// at se deres *eget* skærmbillede, logo eller diagram gennem protan-,
// deuteran- og tritanopi — og det kunne værktøjet ikke. Det kan det nu, og
// dommen her holder den nye vej fast på to ting der begge kan gå stille i
// stykker:
//
//   1. **Der er stadig kun én model.** Billed-løkken i `site/cb-image.js`
//      regner pr. pixel, mens tabellen kalder `simulate()` på en hex. De skal
//      give *samme* farve. Ellers ville et billede og et farvefelt på samme
//      side kunne vise hver sit svar på det samme spørgsmål. Dommen kører
//      derfor pixel-løkken på en stribe farver, typer og sværhedsgrader og
//      kræver præcis samme RGB som `CB_SIM.simulate` — som er den funktion
//      tabellen selv bruger.
//
//   2. **Begge sprogudgaver kalder den.** Den danske side er en
//      håndvedligeholdt kopi; en kopi der glemmer script-tagget eller
//      mount-kaldet ville se ud til at virke på den engelske. Derfor læses
//      begge *rigtige* sider.
//
// Dommen er skrevet til at være RØD på koden før denne opgave: `cb-image.js`
// findes ikke, `CB_SIM` eksponeres ikke, og ingen side kalder `CBIMAGE.mount`.
import { readFileSync } from 'node:fs';
import vm from 'node:vm';

let pass = 0, fail = 0;
const ok = (navn, cond, info = '') => { if (cond) pass++; else { fail++; console.log('FEJL:', navn, info); } };

const SIDER = [
  ['EN', '../site/color-blindness-simulator.html'],
  ['DA', '../site/color-blindness-simulator-da.html'],
];

// Samme minimale DOM som `cb-preview.test.mjs`: nok til at sidens eget script
// kan køre, men uden canvas — så `mount()` ser, at den ikke er på den rigtige
// side, og returnerer. Pixel-løkken testes direkte.
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
  return sb;
}

// ---------------------------------------------------------------------------
// 1. Siden skal eksponere modellen og indlæse billed-kernen.
// ---------------------------------------------------------------------------
const sb = kør(SIDER[0][1]);
ok('siden eksponerer CB_SIM med simulate og matrix',
  sb.CB_SIM && typeof sb.CB_SIM.simulate === 'function' && typeof sb.CB_SIM.matrix === 'function',
  Object.keys(sb.CB_SIM || {}).join(','));
ok('cb-image.js eksporterer transform og mount',
  sb.CBIMAGE && typeof sb.CBIMAGE.transform === 'function' && typeof sb.CBIMAGE.mount === 'function',
  Object.keys(sb.CBIMAGE || {}).join(','));

// ---------------------------------------------------------------------------
// 2. Pixel-løkken skal give præcis den samme farve som tabellens model.
// ---------------------------------------------------------------------------
const FARVER = [[255, 0, 0], [0, 255, 0], [0, 0, 255], [255, 255, 255], [0, 0, 0],
  [17, 24, 39], [245, 158, 11], [124, 58, 237], [22, 163, 74], [128, 64, 200]];
const TYPER = ['protanomaly', 'deuteranomaly', 'tritanomaly'];
const GRAder = [0.2, 0.5, 0.8, 1.0];

let sammenligninger = 0;
for (const type of TYPER) {
  for (const sev of GRAder) {
    const data = new Uint8ClampedArray(FARVER.length * 4);
    FARVER.forEach((c, i) => {
      data[i * 4] = c[0]; data[i * 4 + 1] = c[1]; data[i * 4 + 2] = c[2]; data[i * 4 + 3] = 255;
    });
    const kørt = sb.CBIMAGE.transform(data, type, sev);
    ok(`transform kører (${type} @ ${sev})`, kørt === true, String(kørt));
    FARVER.forEach((c, i) => {
      const forvent = sb.CB_SIM.simulate(c.slice(), type, sev).map((v) => Math.round(v));
      const fik = [data[i * 4], data[i * 4 + 1], data[i * 4 + 2]];
      sammenligninger++;
      ok(`pixel matcher simulate (${type} @ ${sev}): ${c.join(',')}`,
        fik[0] === forvent[0] && fik[1] === forvent[1] && fik[2] === forvent[2],
        `fik ${fik.join(',')} forventede ${forvent.join(',')}`);
    });
  }
}
ok('dommen har sammenlignet et reelt antal pixels', sammenligninger >= 100, String(sammenligninger));

// ---------------------------------------------------------------------------
// 3. 0 % er normalt syn: pixel-løkken må ikke røre noget.
// ---------------------------------------------------------------------------
{
  const data = new Uint8ClampedArray([200, 30, 90, 255, 10, 220, 40, 128]);
  const før = Array.from(data);
  sb.CBIMAGE.transform(data, 'deuteranomaly', 0);
  ok('0 % efterlader pixels uændret', Array.from(data).every((v, i) => v === før[i]),
    Array.from(data).join(','));
}

// ---------------------------------------------------------------------------
// 4. Gennemsigtige pixels er baggrund og skal stå urørt; alfa bevares.
// ---------------------------------------------------------------------------
{
  const data = new Uint8ClampedArray([255, 0, 0, 255, 12, 34, 56, 0]);
  sb.CBIMAGE.transform(data, 'protanomaly', 1);
  ok('en fuldt gennemsigtig pixel røres ikke',
    data[4] === 12 && data[5] === 34 && data[6] === 56, `${data[4]},${data[5]},${data[6]}`);
  ok('alfa bevares', data[3] === 255 && data[7] === 0, `${data[3]},${data[7]}`);
}

// ---------------------------------------------------------------------------
// 5. Uden modellen skal pixel-løkken sige fra, ikke tie.
// ---------------------------------------------------------------------------
{
  const tom = kør(SIDER[0][1]);
  const gemt = tom.CB_SIM;
  tom.CB_SIM = null;
  const data = new Uint8ClampedArray([255, 0, 0, 255]);
  const kørt = tom.CBIMAGE.transform(data, 'deuteranomaly', 1);
  tom.CB_SIM = gemt;
  ok('transform uden CB_SIM returnerer false', kørt === false, String(kørt));
}

// ---------------------------------------------------------------------------
// 6. Begge sider skal indlæse kernen, have feltet og kalde mount.
// ---------------------------------------------------------------------------
for (const [sprog, fil] of SIDER) {
  const html = readFileSync(new URL(fil, import.meta.url), 'utf8');
  ok(`${sprog}: indlæser /cb-image.js`, /<script src="\/cb-image\.js"><\/script>/.test(html));
  ok(`${sprog}: har billed-sektionen med canvas og filfelt`,
    /id="cbi-cv"/.test(html) && /id="cbi-file"/.test(html) && /for="cbi-file"/.test(html));
  ok(`${sprog}: kalder CBIMAGE.mount`, /CBIMAGE\.mount\(/.test(html));
  ok(`${sprog}: eksponerer CB_SIM`, /globalThis\.CB_SIM\s*=/.test(html));
}

console.log(`cb-image: ${pass} bestået, ${fail} fejl`);
process.exit(fail ? 1 : 0);
