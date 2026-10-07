// Dommen over billed-farverne i paletgeneratoren (EN + DA).
//
// Generatoren tager én hexfarve ind. De fleste har ikke deres brandfarve som
// hex — de har den i et logo eller et skærmbillede. `site/palette-image.js`
// læser billedet med canvas og trækker de dominerende farver ud, som prøver
// der sætter basisfarven. Dommen holder to ting fast:
//
//   1. **Udtrækket er rigtigt.** På et pixel-array med kendte farver skal
//      `extract()` finde præcis dem, i den rigtige rækkefølge, uden at tælle
//      gennemsigtige eller næsten-hvide pixels med. Den er ren og uden DOM, så
//      den kan kaldes direkte her.
//
//   2. **Begge sprogudgaver kalder den.** Den danske side er en
//      håndvedligeholdt kopi; en kopi der glemmer script-tagget eller
//      mount-kaldet ville se ud til at virke på den engelske. Derfor læses
//      begge *rigtige* sider.
//
// Dommen er skrevet til at være RØD på koden før denne opgave: `palette-image.js`
// findes ikke, og ingen side indlæser eller kalder den.
import { readFileSync } from 'node:fs';
import vm from 'node:vm';

let pass = 0, fail = 0;
const ok = (navn, cond, info = '') => { if (cond) pass++; else { fail++; console.log('FEJL:', navn, info); } };

const SIDER = [
  ['EN', '../site/palette-generator.html'],
  ['DA', '../site/palette-generator-da.html'],
];

function kør() {
  const sb = { console, setTimeout: () => 0, clearTimeout: () => {} };
  sb.window = sb;
  sb.globalThis = sb;
  vm.createContext(sb);
  vm.runInContext(readFileSync(new URL('../site/palette-image.js', import.meta.url), 'utf8'), sb);
  return sb;
}

const sb = kør();
ok('palette-image.js eksporterer extract, mount og toHex',
  sb.PALETTE_IMAGE && typeof sb.PALETTE_IMAGE.extract === 'function'
  && typeof sb.PALETTE_IMAGE.mount === 'function'
  && typeof sb.PALETTE_IMAGE.toHex === 'function',
  Object.keys(sb.PALETTE_IMAGE || {}).join(','));

function px(list) {
  const a = new Uint8ClampedArray(list.length * 4);
  list.forEach((c, i) => { a[i * 4] = c[0]; a[i * 4 + 1] = c[1]; a[i * 4 + 2] = c[2]; a[i * 4 + 3] = c[3]; });
  return a;
}

// ---------------------------------------------------------------------------
// 1. Kendte farver: den mest dominerende først.
// ---------------------------------------------------------------------------
{
  const data = px([
    [255, 0, 0, 255], [255, 0, 0, 255], [255, 0, 0, 255],
    [0, 0, 255, 255],
    [255, 255, 255, 255],          // næsten-hvid baggrund
    [10, 20, 30, 0],               // helt gennemsigtig
  ]);
  const farver = sb.PALETTE_IMAGE.extract(data);
  ok('finder de to farver og springer hvid/gennemsigtig over', farver.length === 2, String(farver.length));
  ok('mest dominerende farve er rød', farver[0] && farver[0].hex === '#ff0000', farver[0] && farver[0].hex);
  ok('rød har count 3', farver[0] && farver[0].count === 3, farver[0] && String(farver[0].count));
  ok('næste er blå', farver[1] && farver[1].hex === '#0000ff', farver[1] && farver[1].hex);
}

// ---------------------------------------------------------------------------
// 2. Gennemsigtige pixels alene giver ingen farver (ikke en farve af nuller).
// ---------------------------------------------------------------------------
{
  const farver = sb.PALETTE_IMAGE.extract(px([[12, 34, 56, 0], [0, 0, 0, 10]]));
  ok('kun gennemsigtige pixels giver en tom liste', farver.length === 0, String(farver.length));
}

// ---------------------------------------------------------------------------
// 3. Næsten-hvid kan tælles med, hvis man beder om det.
// ---------------------------------------------------------------------------
{
  const data = px([[255, 255, 255, 255], [0, 128, 0, 255]]);
  ok('hvid er væk som standard', sb.PALETTE_IMAGE.extract(data).length === 1);
  const medHvid = sb.PALETTE_IMAGE.extract(data, { whiteMin: 256 });
  ok('whiteMin 256 tæller hvid med', medHvid.length === 2, String(medHvid.length));
}

// ---------------------------------------------------------------------------
// 4. `max` overholdes, og næsten-identiske nuancer slås sammen.
// ---------------------------------------------------------------------------
{
  const mange = [];
  for (let i = 0; i < 40; i++) mange.push([(i * 6) % 256, (i * 10) % 256, (i * 14) % 256, 255]);
  ok('højst max farver ud', sb.PALETTE_IMAGE.extract(px(mange), { max: 5 }).length <= 5);
  // to pixels der ligger tæt på hinanden skal give én prøve
  const tæt = sb.PALETTE_IMAGE.extract(px([[100, 100, 100, 255], [104, 104, 104, 255]]));
  ok('næsten-identiske farver slås sammen', tæt.length === 1, String(tæt.length));
}

// ---------------------------------------------------------------------------
// 5. Deterministisk: samme pixels giver samme svar.
// ---------------------------------------------------------------------------
{
  const data = px([[17, 24, 39, 255], [245, 158, 11, 255], [17, 24, 39, 255]]);
  const a = JSON.stringify(sb.PALETTE_IMAGE.extract(data));
  const b = JSON.stringify(sb.PALETTE_IMAGE.extract(data));
  ok('samme input giver samme output', a === b, a + ' vs ' + b);
}

// ---------------------------------------------------------------------------
// 6. toHex.
// ---------------------------------------------------------------------------
ok('toHex giver en 6-cifret hex', sb.PALETTE_IMAGE.toHex([255, 0, 128]) === '#ff0080',
  sb.PALETTE_IMAGE.toHex([255, 0, 128]));
ok('toHex afrunder og klemmer', sb.PALETTE_IMAGE.toHex([300, -5, 16.6]) === '#ff0011',
  sb.PALETTE_IMAGE.toHex([300, -5, 16.6]));

// ---------------------------------------------------------------------------
// 7. Begge sider skal indlæse kernen, have sektionen og kalde mount.
// ---------------------------------------------------------------------------
for (const [sprog, fil] of SIDER) {
  const html = readFileSync(new URL(fil, import.meta.url), 'utf8');
  ok(`${sprog}: indlæser /palette-image.js`, /<script src="\/palette-image\.js"><\/script>/.test(html));
  ok(`${sprog}: har billed-sektionen med filfelt`,
    /id="pg-img"/.test(html) && /id="pg-img-file"/.test(html) && /for="pg-img-file"/.test(html)
    && /id="pg-img-swatches"/.test(html));
  ok(`${sprog}: kalder PALETTE_IMAGE.mount`, /PALETTE_IMAGE\.mount\(/.test(html));
}

console.log(`palette-image: ${pass} bestået, ${fail} fejl`);
process.exit(fail ? 1 : 0);
