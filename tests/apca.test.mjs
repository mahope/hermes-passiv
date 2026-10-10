// Dommen over APCA-scoren på /contrast-checker (EN + DA).
//
// WCAG 2.1-forholdet er blindt for polaritet: 4.5:1 mørk-på-lys læses
// anderledes end 4.5:1 lys-på-mørk. APCA er den perceptuelle model, WCAG 3
// bygger på, og `site/apca.js` tilføjer dens signerede Lc-tal til værktøjet.
//
// Dommen holder tre ting fast, som hver kan gå stille i stykker:
//
//   1. **Tallet er referencen, ikke en efterligning.** `apca-w3`'s egen
//      testsuite (test/index.js, 0.1.9) har faste Lc-værdier for otte farvepar,
//      inklusive et nær-sort par og begge polariteter. En forvekslet eksponent
//      eller et manglende fortegn giver et andet tal og fanges her.
//
//   2. **Begge sprogudgaver viser den.** Den danske side er en
//      håndvedligeholdt kopi; glemmer den script-tagget eller `#apca-out`,
//      ville den engelske se ud til at virke.
//
//   3. **Modulet kan fejle.** Mutationen nedenfor vender polariteten og skal
//      give et forkert tal — så dommen ikke er grøn på hvad som helst.
//
// Dommen er skrevet til at være RØD på koden før denne opgave: `site/apca.js`
// findes ikke, og ingen side har `#apca-out`.
import { readFileSync } from 'node:fs';
import vm from 'node:vm';

let pass = 0, fail = 0;
const ok = (navn, cond, info = '') => { if (cond) pass++; else { fail++; console.log('FEJL:', navn, info); } };

function loadApca() {
  const sb = { console, Math };
  sb.window = sb;
  sb.globalThis = sb;
  vm.createContext(sb);
  vm.runInContext(readFileSync(new URL('../site/apca.js', import.meta.url), 'utf8'), sb);
  return sb.APCA;
}

function rgb(hex) {
  const h = hex.replace('#', '');
  const e = h.length === 3 ? h.split('').map((c) => c + c).join('') : h;
  return [parseInt(e.slice(0, 2), 16), parseInt(e.slice(2, 4), 16), parseInt(e.slice(4, 6), 16)];
}

// ---------------------------------------------------------------------------
// 1. Modulet findes og eksponerer den rene beregning.
// ---------------------------------------------------------------------------
const APCA = loadApca();
ok('apca.js eksponerer contrast() og label()',
  APCA && typeof APCA.contrast === 'function' && typeof APCA.label === 'function',
  Object.keys(APCA || {}).join(','));

// ---------------------------------------------------------------------------
// 2. Tallene er apca-w3's egne referenceværdier (0.1.9). Tekst først, baggrund
//    bagefter — fortegnet skifter med rækkefølgen.
// ---------------------------------------------------------------------------
const REF = [
  ['#888', '#FFF', 63.056469930209424],
  ['#FFF', '#888', -68.54146436644962],
  ['#000', '#aaa', 58.146262578561334],
  ['#aaa', '#000', -56.24113336839742],
  ['#123', '#def', 91.66830811481631],
  ['#def', '#123', -93.06770049484275],
  ['#123', '#444', 8.32326136957393],
  ['#444', '#123', -7.526878460278154],
];
for (const [fg, bg, forventet] of REF) {
  const got = APCA.contrast(rgb(fg), rgb(bg));
  ok(`Lc for ${fg} på ${bg}`, Math.abs(got - forventet) < 1e-6,
    `fik ${got}, forventede ${forventet}`);
}

// Fortegnet skal følge polariteten, ikke bare størrelsen.
ok('mørk-på-lys er positiv, lys-på-mørk negativ',
  APCA.contrast(rgb('#000'), rgb('#fff')) > 0 && APCA.contrast(rgb('#fff'), rgb('#000')) < 0);

// ---------------------------------------------------------------------------
// 3. Rådene følger APCA's tærskler og findes på begge sprog.
// ---------------------------------------------------------------------------
ok('label() svarer på engelsk', /body text/.test(APCA.label(90, 'en')));
ok('label() svarer på dansk', /brødtekst/.test(APCA.label(90, 'da')));
ok('højt Lc råder til brødtekst, lavt til ikke-tekst',
  /body text/.test(APCA.label(90, 'en')) && /non-text/.test(APCA.label(20, 'en')));

// ---------------------------------------------------------------------------
// 4. Begge sider henter modulet og viser resultatet.
// ---------------------------------------------------------------------------
const SIDER = [
  ['EN', '../site/contrast-checker.html'],
  ['DA', '../site/contrast-checker-da.html'],
];
for (const [navn, fil] of SIDER) {
  const html = readFileSync(new URL(fil, import.meta.url), 'utf8');
  ok(`${navn}: henter /apca.js`, /<script[^>]+src="\/apca\.js"/.test(html));
  ok(`${navn}: har #apca-out`, /id="apca-out"/.test(html));
  ok(`${navn}: kalder APCA.contrast`, /APCA\.contrast\(/.test(html));
  ok(`${navn}: APCA-kolonne i batch-tabellen`, /<th[^>]*>APCA Lc<\/th>/.test(html));
}

// ---------------------------------------------------------------------------
// 4b. Tekst-på-billede-tjekkeren viser også APCA. WCAG-forholdet mod de rå
//     billedpixels er blindt for polaritet, præcis som farvepar-tjekket var —
//     så den delte kerne (`site/text-on-image-core.js`) får samme Lc-tal for
//     den værst tænkelige pixel. Alle fire sider deler kernen, så de skal alle
//     hente modulet *før* kernen; ellers står linjen bare ikke.
// ---------------------------------------------------------------------------
const TEXTPAA_BILLEDE = [
  ['EN checker', '../site/text-on-image-checker.html'],
  ['DA checker', '../site/text-on-image-checker-da.html'],
  ['EN artikel', '../site/blog/text-on-image-contrast-check.html'],
  ['DA artikel', '../site/da/blog/tekst-paa-billede-kontrasttjek.html'],
];
for (const [navn, fil] of TEXTPAA_BILLEDE) {
  const html = readFileSync(new URL(fil, import.meta.url), 'utf8');
  const apca = html.search(/<script[^>]+src="\/apca\.js"/);
  const kerne = html.search(/<script[^>]+src="\/text-on-image-core\.js"/);
  ok(`${navn}: henter /apca.js`, apca >= 0);
  ok(`${navn}: henter /apca.js FØR kernen`, apca >= 0 && kerne >= 0 && apca < kerne,
    `apca ${apca}, kerne ${kerne}`);
}
{
  const kerne = readFileSync(new URL('../site/text-on-image-core.js', import.meta.url), 'utf8');
  ok('kernen kalder APCA.contrast', /APCA\.contrast\(/.test(kerne));
  ok('kernen skriver data-ti-apca i resultatet', /data-ti-apca=/.test(kerne));
}

// ---------------------------------------------------------------------------
// 5. Modulet kan fejle: vend polariteten og se at et referencetal ændrer sig.
//    (Beviser at dommen ovenfor ikke er grøn på hvad som helst.)
// ---------------------------------------------------------------------------
{
  const muteret = loadApca();
  const rigtig = muteret.contrast;
  muteret.contrast = (a, b) => -rigtig(a, b);
  const snydt = Math.abs(muteret.contrast(rgb('#888'), rgb('#FFF')) - 63.056469930209424) < 1e-6;
  ok('mutation: vendt polaritet giver et forkert tal', !snydt);
}

console.log(`apca: ${pass} bestået, ${fail} fejl`);
process.exit(fail ? 1 : 0);
