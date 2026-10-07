// Dommen over farvenavnene i paletgeneratoren (EN + DA).
//
// Generatoren regner i hex, men en ikke-designer taler om «den blå». Navnet er
// den sætning de mangler, når de har fået en farve ud af et logo. `site/color-
// names.js` bærer de 148 navngivne CSS-farver og vælger den nærmeste.
//
// Dommen holder tre ting fast:
//
//   1. **Opslaget er rigtigt.** Kendte hexer skal give det rigtige navn — også
//      hvor to navne ligger tæt på hinanden (`#00ff00` er lime, ikke green), så
//      tabellen ikke bare kan returnere den første række.
//   2. **Tabellen er komplet og entydig.** Alle 139 forskellige CSS-farver
//      (spec'ens 148 navne minus de ni dubletter, fx aqua/cyan), uden navne der
//      gentages.
//   3. **Begge sider bruger den.** Den danske side er en håndvedligeholdt kopi;
//      en kopi der glemmer script-tagget ville se ud til at virke på den
//      engelske. Derfor læses begge *rigtige* sider, og billed-prøverne skal
//      vise navnet med.
//
// Dommen er skrevet til at være RØD på koden før denne opgave: `color-names.js`
// findes ikke, og ingen side indlæser eller kalder den.
import { readFileSync } from 'node:fs';
import vm from 'node:vm';

let pass = 0, fail = 0;
const ok = (navn, cond, info = '') => { if (cond) pass++; else { fail++; console.log('FEJL:', navn, info); } };

function load() {
  const sb = { console };
  sb.window = sb;
  sb.globalThis = sb;
  vm.createContext(sb);
  vm.runInContext(readFileSync(new URL('../site/color-names.js', import.meta.url), 'utf8'), sb);
  return sb;
}

const sb = load();
ok('color-names.js eksporterer nearestName og table',
  sb.COLOR_NAMES && typeof sb.COLOR_NAMES.nearestName === 'function'
  && Array.isArray(sb.COLOR_NAMES.table),
  Object.keys(sb.COLOR_NAMES || {}).join(','));

const nearest = sb.COLOR_NAMES.nearestName;

// ---------------------------------------------------------------------------
// 1. Kendte farver, inkl. de nære par hvor «den første række» ville være forkert.
// ---------------------------------------------------------------------------
const KENDTE = [
  ['#ff0000', 'red'],
  ['#dc143c', 'crimson'],
  ['#6a5acd', 'slateblue'],
  ['#f5f5f5', 'whitesmoke'],
  ['#2e8b57', 'seagreen'],
  ['#000000', 'black'],
  ['#ffffff', 'white'],
  ['#ffd700', 'gold'],
  ['#00ff00', 'lime'],
  ['#008000', 'green'],
  ['#1e90ff', 'dodgerblue'],
  ['#663399', 'rebeccapurple'],
  ['#d2691e', 'chocolate'],
  ['#708090', 'slategray'],
  ['#ff00ff', 'fuchsia'],
  ['#00ffff', 'aqua'],
];
for (const [hex, navn] of KENDTE) {
  ok(`nearestName('${hex}') = ${navn}`, nearest(hex) === navn, nearest(hex));
}

// 2. Form: store bogstaver, uden #, og 3-cifret kortform.
ok('store bogstaver ignoreres', nearest('#FF0000') === 'red', nearest('#FF0000'));
ok('uden # virker', nearest('2e8b57') === 'seagreen', nearest('2e8b57'));
ok('3-cifret kortform virker', nearest('#f00') === 'red', nearest('#f00'));

// 3. Ugyldigt input giver tom streng, ikke et tilfældigt navn.
ok('ugyldig hex giver tom streng', nearest('nope') === '', JSON.stringify(nearest('nope')));
ok('tom streng giver tom streng', nearest('') === '', JSON.stringify(nearest('')));
ok('null giver tom streng', nearest(null) === '', JSON.stringify(nearest(null)));

// 4. Tabellen er komplet og entydig.
const names = sb.COLOR_NAMES.table.map(r => r[0]);
ok('tabellen har 139 forskellige CSS-farver', names.length === 139, String(names.length));
ok('ingen dubletter i navnene', new Set(names).size === names.length,
  names.length - new Set(names).size + ' dubletter');
ok('alle hexer er 6-cifrede', sb.COLOR_NAMES.table.every(r => /^[0-9a-f]{6}$/.test(r[1])),
  sb.COLOR_NAMES.table.filter(r => !/^[0-9a-f]{6}$/.test(r[1])).map(r => r[0]).join(','));
ok('alle navne er små bogstaver uden mellemrum',
  names.every(n => /^[a-z]+$/.test(n)), names.filter(n => !/^[a-z]+$/.test(n)).join(','));

// 5. En farve midt mellem to navne vælger stadig ét navn (deterministisk).
ok('deterministisk: samme svar to gange', nearest('#2563eb') === nearest('#2563eb'));
ok('#2563eb får et rigtigt blå-navn', /blue/.test(nearest('#2563eb')), nearest('#2563eb'));

// ---------------------------------------------------------------------------
// 6. Begge sider skal indlæse tabellen og kalde den i render.
// ---------------------------------------------------------------------------
const SIDER = [
  ['EN', '../site/palette-generator.html'],
  ['DA', '../site/palette-generator-da.html'],
];
for (const [sprog, fil] of SIDER) {
  const html = readFileSync(new URL(fil, import.meta.url), 'utf8');
  ok(`${sprog}: indlæser /color-names.js`, /<script src="\/color-names\.js"><\/script>/.test(html));
  ok(`${sprog}: kalder COLOR_NAMES.nearestName`, /COLOR_NAMES\.nearestName\(/.test(html));
  ok(`${sprog}: viser navnet i en .pg-name-celle`, /class="pg-name"/.test(html));
}

// 7. Billed-prøverne skal vise navnet med, ikke kun sætte basisfarven.
const billed = readFileSync(new URL('../site/palette-image.js', import.meta.url), 'utf8');
ok('palette-image.js slår farvenavnet op', /COLOR_NAMES\.nearestName\(/.test(billed));
ok('palette-image.js tegner navnet under prøven', /pg-img-name/.test(billed));

console.log(`color-names: ${pass} bestået, ${fail} fejl`);
process.exit(fail ? 1 : 0);
