// Dom over kunderapporten fra EAA/WCAG-scanneren (`/scan` + `/scan-da`).
//
// Hvorfor den findes: scanneren kunne udskrive (`window.print()`, som udskriver
// hele siden *omkring* resultatet — navigation, «hvad tjekkeren», pro-kortet) og
// dele et link (som modtageren skal åbne på vores site). Ingen af dem er et
// dokument. Den, der står over for en kunde og har fået «hvad fandt du?», har
// brug for én fil vedlægge.
//
// Dommen dækker fire lag, fordi de kan falde hver for sig:
//
//   1. codecen i `site/scan-report.js` — ren vare i en `vm`, ingen DOM;
//   2. **at rapporten ikke kan lyve.** Fund-teksten og rettelsen kommer fra
//      sidens *egne* MSG/FIX-tabeller, så modulet skal afvise en kaldet, der
//      ikke rammer dem. Ellers kunne en rapportfind alt i `id` og skrive sine
//      egne ord på mahope.tools;
//   3. **at læserens egen tekst ikke bliver markup.** Adressen er
//      læserstyret og havner i `href`, i `<code>` og i en `<title>` på én gang.
//      Dommen kører en adresse med `<script>`, `"` og `javascript:`;
//   4. **at begge *rigtige* sider faktisk kalder den.** Codecen kan være
//      perfekt, mens den danske side har mistet knappen, og så ser den stadig ud
//      til at virke på den engelske. Derfor læses begges egne bytes.
//
// Polaritet: dommene under (2)–(4) er røde mod koden fra før denne ændring —
// modulet findes ikke, og ingen af siderne har knappen.
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import vm from 'node:vm';

const root = fileURLToPath(new URL('..', import.meta.url));

let pass = 0, fail = 0;
const ok = (navn, cond, info = '') => { if (cond) pass++; else { fail++; console.log('FEJL:', navn, info); } };

// ---------------------------------------------------------------------------
// 1. Modulen i en ren vm — ingen document, ingen window.
// ---------------------------------------------------------------------------
const ctx = {};
vm.createContext(ctx);
vm.runInContext(readFileSync(new URL('../site/scan-report.js', import.meta.url), 'utf8'), ctx);
const R = ctx.SCANREPORT;

ok('modulen eksporterer build/download', typeof R?.build === 'function' && typeof R?.download === 'function');

// Tabellerne er side-NES. De er skrevet her, ikke importeret, fordi det er
// pointen: modulet skal kunne skrive fund ud fra dem OG afvise alt andet.
const MSG = {
  IMG_ALT: '{n} image(s) missing alt text',
  CONTRAST: '{n} text(s) below the contrast ratio',
  HEADING_SKIP: '{n} heading level(s) skipped'
};
const FIX = {
  IMG_ALT: 'Fix: add an alt attribute describing each image.',
  CONTRAST: 'Fix: darken the text until the ratio is at least 4.5:1.',
  HEADING_SKIP: 'Fix: do not skip heading levels.'
};

const EN = {
  url: 'https://example.com/pris',
  score: 71,
  grade: 'C',
  findings: [
    { id: 'IMG_ALT', sev: 'error', count: 4 },
    { id: 'CONTRAST', sev: 'error', count: 1 },
    { id: 'HEADING_SKIP', sev: 'warning', count: 2 }
  ]
};

const opts = { lang: 'en', msg: MSG, fix: FIX };

// ---------------------------------------------------------------------------
// 2. Rapporten siger det samme som siden.
// ---------------------------------------------------------------------------
const en = R.build(EN, opts);

ok('EN: doctype og lang', en.startsWith('<!doctype html>') && en.includes('<html lang="en">'));
ok('EN: fund-teksten er sidens egen', en.includes('4 image(s) missing alt text'));
ok('EN: antallet kommer fra fundene, ikke fra en streng', en.includes('1 text(s) below the contrast ratio'));
ok('EN: rettelsen følger med', en.includes('add an alt attribute describing each image'));
ok('EN: scoren fra siden, ikke udregnet igen', en.includes('>71<') && en.includes('Grade: <b>C</b>'));

// Uden rettelseslinjen for en regel, der ikke findes, forsvinder «Fix:»-linjen
// i stedet for at blive til en tom etiket.
const delvis = R.build(EN, { lang: 'en', msg: MSG, fix: {} });
ok('EN: ukendt rettelse giver ingen tom Fix-linje', !/class="how"/.test(delvis));

// FIX-linjen begynder selv med «Fix: ». En etikette oven på den gav «Fix Fix:
// …» i output — og på dansk «Ret Fix: …», fordi rettelsesteksten på begge
// sprog begynder med «Fix: ». Dommen tæller præfikserne, fordi det er præcis
// sådan et dubletpræfiks man ikke ser i koden.
const dobbelt = (en.match(/Fix:\s*Fix:/g) || []).length;
ok('EN: intet dobbelt «Fix:»-præfiks', dobbelt === 0, `${dobbelt} fundet`);
ok('EN: rettelsen står ordret som siden skrev den', en.includes('Fix: add an alt attribute describing each image.'));
// Den døde `76B`-linje fra det første udkast lå lige over de to linjer der
// allerede siger «Score: 76 · Grade: B».
ok('EN: scoren står i de to felter, ikke i en linje uden skilletegn', !/>\d+<span class="grade">/.test(en));

// En regel, modulet ikke kender, skriver sit id — aldrig sin egen tekst. Den
// kan ikke finde på noget, fordi den har ingen tekst med.
const ukendt = R.build({ url: 'https://x.dk', score: 88, grade: 'B', findings: [{ id: 'HJÆLP', sev: 'error', count: 9 }] }, opts);
ok('EN: ukendt regel giver sit id, ikke sin egen tekst', ukendt.includes('HJÆLP') && !ukendt.includes('hjælp-fiks'));

const rene = R.build({ url: 'https://x.dk', score: 100, grade: 'A', findings: [] }, opts);
ok('EN: nul fund siger det rent', rene.includes('No issues found by the automated checks.'));

// ---------------------------------------------------------------------------
// 3. Læserens egen adresse bliver aldrig markup.
// ---------------------------------------------------------------------------
const fjende = 'https://evil.example/"><script>alert(1)</script>';
const angreb = R.build({ url: fjende, score: 60, grade: 'D', findings: [{ id: 'IMG_ALT', sev: 'error', count: 1 }] }, opts);

ok('ingen rå <script i rapporten', !/<script/i.test(angreb));
ok('adressen er escaped', angreb.includes('&lt;script&gt;') && !angreb.includes('"><script>'));
ok('injektionen overlever kun som tekst', (angreb.match(/<script/gi) || []).length === 0);

// `javascript:` må aldrig blive et klikbart mål — det er den anden vej ind i en
// fil, der bliver sendt videre til en kunde.
const js = R.build({ url: 'javascript:alert(1)', score: 100, grade: 'A', findings: [] }, opts);
ok('javascript:-adresse bliver aldrig et href', !/<a[^>]+href="javascript:/i.test(js));

// Kvoterings-tegn i `href` er det, der lukker attribut-værdien og gør resten af
// filen til markup. Netop derfor er fund-tallet — ikke URL'en — det svære.
const quote = R.build({ url: 'https://ok.example/a"onmouseover="alert(1)', score: 50, grade: 'D', findings: [] }, opts);
ok('gåseøj i href er escaped', !quote.includes('onmouseover="') && quote.includes('&quot;'));

// ---------------------------------------------------------------------------
// 4. Datoen er Europe/Copenhagen (kvalitetspunkt 4).
// ---------------------------------------------------------------------------
// 2026-10-11T00:30Z er 02.30 samme dag i Danmark (sommertid), mens UTC-datoen
// er 11/10. Vælges den forkerte zone, skriver rapporten 10/10 — en kalenderdag
// forskudt på hvert eneste dokument.
const fast = R.when(Date.UTC(2026, 9, 11, 0, 30), R.ZONE);
ok('ZONE er Europe/Copenhagen', R.ZONE === 'Europe/Copenhagen');
ok('datoen følger Europe/Copenhagen, ikke UTC', fast.includes('11') && fast.includes('October 2026'), fast);

// Vintertid: 2026-01-15T23:30Z er 00.30 den 16. — igen kun den forkerte zone
// kan få det til at stå som 15.
const fast2 = R.when(Date.UTC(2026, 0, 15, 23, 30), R.ZONE);
ok('vintertid passerer datoen korrekt', fast2.includes('16 January 2026'), fast2);

// ---------------------------------------------------------------------------
// 5. Filnavnet. Værten er læserstyret, så det reduceres i stedet for at
//    stoles på.
// ---------------------------------------------------------------------------
ok('filnavn fra vært', R.filename(EN, 'en') === 'example.com-tilgaengelighedstjek.html', R.filename(EN, 'en'));
ok('filnavn DA får sit eget sprog', R.filename(EN, 'da').startsWith('example.com-da-'));
ok('filnavn uden sti eller tegn uden for filnavn', !/[/\\]/.test(R.filename({ url: 'https://a.example/x/y' }, 'en')));
ok('filnavn kan ikke blive en sti opad', !R.filename({ url: 'https://..' }, 'en').includes('..'));

// ---------------------------------------------------------------------------
// 6. Flere sider: én sektion pr. side, og de sider der ikke kunne læses
//    kommer med som det de er.
// ---------------------------------------------------------------------------
const flere = R.build({
  url: 'https://a.dk, https://b.dk',
  score: 66,
  grade: 'C',
  findings: [{ id: 'IMG_ALT', sev: 'error', count: 2 }],
  pages: [
    { url: 'https://a.dk', score: 88, grade: 'B', findings: [{ id: 'IMG_ALT', sev: 'error', count: 1 }] },
    { url: 'https://b.dk', score: 44, grade: 'D', findings: [{ id: 'CONTRAST', sev: 'error', count: 1 }] }
  ],
  mislykkedes: [{ url: 'https://c.dk', error: 'HTTP 503' }]
}, opts);

ok('én sektion pr. side', flere.includes('Page 1 — a.dk') && flere.includes('Page 2 — b.dk'));
ok('den ulæselige side er med som ulæselig', flere.includes('Pages that could not be read') && flere.includes('HTTP 503'));
ok('en liste af sider er ikke én adresse', !flere.includes('a.dk, https://b.dk'));
ok('per-side-score er med', flere.includes('>88<') && flere.includes('>44<'));

// ---------------------------------------------------------------------------
// 7. Selvstændighed. Filen skal kunne åbnes fra en download-mappe om ti år,
//    altså ingen ekstern CSS, ingen skrift, intet script, intet billede.
// ---------------------------------------------------------------------------
for (const [navn, html] of [['EN', en], ['DA', R.build(EN, { lang: 'da', msg: MSG, fix: FIX })], ['flere', flere]]) {
  ok(`${navn}: intet <script>`, !/<script/i.test(html));
  ok(`${navn}: ingen <link>`, !/<link/i.test(html));
  ok(`${navn}: ingen <img>`, !/<img/i.test(html));
  ok(`${navn}: stylesheet kun inline`, !/<style[^>]+src=/i.test(html) && html.includes('<style>'));
  ok(`${navn}: ingen @import`, !/@import/i.test(html));
  // `noindex` — en klients audit skal ikke havne i et søgeindeks.
  ok(`${navn}: noindex`, html.includes('name="robots" content="noindex'));
}

// ---------------------------------------------------------------------------
// 8. Begge sprog. En tabel der har en nøgle i det ene sprog og mangler den i det
//    andet er en rapport, der lover noget på den ene side og ikke på den anden.
// ---------------------------------------------------------------------------
const nøgle = Object.keys(R.T.en).sort().join(',');
ok('EN og DA har præcis de samme nøgler', nøgle === Object.keys(R.T.da).sort().join(','),
  Object.keys(R.T.da).filter((k) => !(k in R.T.en)).join(',') || Object.keys(R.T.en).filter((k) => !(k in R.T.da)).join(','));
ok('ingen tomme oversættelser', Object.keys(R.T.da).every((k) => String(R.T.da[k]).trim().length > 0));

const da = R.build(EN, { lang: 'da', msg: MSG, fix: FIX });
ok('DA: lang="da"', da.includes('<html lang="da">'));
ok('DA: egen tekst, ikke den engelske', da.includes('Tilgængelighedstjek') && !da.includes('Accessibility check'));
ok('DA: intet dobbelt præfiks på rettelsen', !/Ret\s*Fix:/.test(da));

// Rapporten skriver antallet selv, så «1 advarsler» var dansk til grin. EN
// beholder sidens egen «1 warning(s)»-kortform, DA får rigtig en/flertal.
// Tallet er **fund**, altså brudte regler — præcis som `state.errors` på
// kortstabelen, som også tæller fund og ikke forekomster.
const ett = R.build({ url: 'https://a.dk', score: 88, grade: 'B', findings: [{ id: 'IMG_ALT', sev: 'error', count: 1 }, { id: 'HEADING_SKIP', sev: 'warning', count: 1 }] }, { lang: 'da', msg: MSG, fix: FIX });
const to = R.build({ url: 'https://a.dk', score: 76, grade: 'B', findings: [{ id: 'IMG_ALT', sev: 'error', count: 2 }, { id: 'CONTRAST', sev: 'error', count: 1 }, { id: 'HEADING_SKIP', sev: 'warning', count: 2 }, { id: 'LINK_TEXT', sev: 'warning', count: 1 }] }, { lang: 'da', msg: MSG, fix: FIX });
ok('DA: «1 fejl, 1 advarsel» i ental', ett.includes('1 fejl, 1 advarsel'), ett.match(/\d+ fejl[^<]*/)?.[0]);
ok('DA: «2 fejler, 2 advarsler» i flertal', to.includes('2 fejler, 2 advarsler'), to.match(/\d+ fejl[^<]*/)?.[0]);
ok('EN: beholder sidens «(s)»-kortform', R.build(EN, opts).includes('2 error(s), 1 warning(s)'), R.build(EN, opts).match(/\d+ error[^<]*/)?.[0]);
ok('DA: samme karakterord som siden viser', R.T.da.grade === R.T.en.grade);
ok('rapporten har et main-landmark', en.includes('<main>') && en.includes('</main>'));
// Den døde CSS fra det første udkast.
ok('ingen død score/grade-stil', !/\.score\{|\.grade\{/.test(en));

// ---------------------------------------------------------------------------
// 9. De rigtige sider kalder den. Codecen kan være perfekt, mens den danske
//    side har mistet knappen.
// ---------------------------------------------------------------------------
for (const [side, knap, kalder] of [
  ['scan.html', 'Download the report', "window.SCANREPORT.download(LAST,{lang:'en'"],
  ['scan-da.html', 'Hent rapporten', "window.SCANREPORT.download(LAST,{lang:'da'"]
]) {
  const src = readFileSync(new URL(`../site/${side}`, import.meta.url), 'utf8');
  ok(`${side}: indlæser modulet FØR sin egen inline-kode`,
    src.indexOf('/scan-report.js') !== -1 && src.indexOf('/scan-report.js') < src.indexOf('function downloadReport'));
  ok(`${side}: har knappen`, src.includes(knap));
  ok(`${side}: knappen kalder modulet med sit eget sprog og tabeller`, src.includes(kalder));
  ok(`${side}: knappen er i begge resultater (én side og flere)`,
    (src.match(/onclick="downloadReport\(\)"/g) || []).length === 2);
  // Uden `grade` på LAST ville rapporten finde på en karakter. Den hentes fra
  // den samme `gradeOf` som kortstabelen bruger — to beregninger af det samme
  // tal er hvordan et scorekort ender i at modsige sin egen liste.
  ok(`${side}: scoren og karakteren kommer fra siden`, src.includes('grade:gradeOf(score)') && src.includes('state.grade=gradeOf(state.score)'));
  ok(`${side}: rapporten får sidens MSG/FIX, ikke sit eget`, src.includes('msg:MSG,fix:FIX'));
  ok(`${side}: funktionen er eksponeret på window (onclick=)`, src.includes('window.downloadReport=downloadReport'));
}

// Mutation: rapporten uden escaping. Den skal gå rød, ellers dømmer
// «ingen rå <script» intet. Betingelsen er derfor at mutationen *gør* det rå
// script synligt igen — ikke at den stadig er usynlig.
const flygtig = readFileSync(new URL('../site/scan-report.js', import.meta.url), 'utf8')
  .replace(/function esc\(s\) \{[\s\S]*?\n  \}/, 'function esc(s){return String(s);}');
ok('mutationen rammer overhovedet esc()', flygtig.includes('function esc(s){return String(s);}'));
const mCtx = {}; vm.createContext(mCtx); vm.runInContext(flygtig, mCtx);
const mut = mCtx.SCANREPORT.build({ url: fjende, score: 60, grade: 'D', findings: [] }, opts);
ok('mutation: esc() fjernet gør «ingen rå <script» rød', /<script/i.test(mut));

console.log(`\nscan-report: ${pass} bestået, ${fail} fejlede`);
process.exit(fail ? 1 : 0);