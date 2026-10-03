// Adfærdsdom over del-linket på EAA/WCAG-scanneren (`/scan` + `/scan-da`).
//
// Hvorfor den findes: `shareResult()` kopierede før dette kun *URL'en*, så den
// der modtog linket så en tom formular og skulle trykke Scan selv — og brugte
// sin egen kvote på en side, der måske var ændret siden. Det er præcis den
// viste, en bureau-audit skal kunne sendes videre på, så fundene ligger nu i
// fragmentet og gengives uden et eneste serverkald.
//
// Dommen dækker tre lag, fordi de kan falde hver for sig:
//   1. codecen i `site/scan-share-core.js`, inklusive de fjendtlige fragmenter
//      en læser eller en beskåret besked kan producere — `#u=%` må efterlade
//      formularen som den var, ikke tømme siden (samme URIError som `#url=`
//      læserne ramte, c2891ac);
//   2. at hver *rigtig* side faktisk kalder den. Codecen kan være perfekt, mens
//      den danske side har sin egen kopi eller har mistet knappen, og så ser
//      den stadig ud til at virke på den engelske. Derfor læses begges egne
//      bytes, og deres `render()`/`shareResult()` køres i en vm mod en
//      håndlavet DOM;
//   3. at fund-teksten ikke kan reddes ud af tabellen. Kun id, alvor og antal
//      rejser i fragmentet, så et håndredigeret link kan ændre et tal og
//      aldrig sætte sine egne ord på mahope.tools.
//
// Polaritet: dommene under (2) og (3) er skrevet, så de bliver røde mod koden
// fra før denne ændring — den læser `#url=`, bruger `alert()`, og `add()`
// tager en tekst, der skrives direkte i `innerHTML`.
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import vm from 'node:vm';

const root = fileURLToPath(new URL('..', import.meta.url));

let pass = 0, fail = 0;
const ok = (navn, cond, info = '') => { if (cond) pass++; else { fail++; console.log('FEJL:', navn, info); } };

// ---------------------------------------------------------------------------
// 1. Codecen. Ren vare, ingen DOM — den skal kunne læses påstanden om
//    «kaster aldrig» direkte.
// ---------------------------------------------------------------------------
const codecCtx = {};
vm.createContext(codecCtx);
vm.runInContext(readFileSync(new URL('../site/scan-share-core.js', import.meta.url), 'utf8'), codecCtx);
const S = codecCtx.SCANSHARE;

ok('kernen eksporterer decode/encode', typeof S?.decode === 'function' && typeof S?.encode === 'function');

const RIGTIG = {
  url: 'https://example.com/pris',
  // 71 er ikke en tilfældig værdi: den er pr. side egen formel for de tre fund
  // nedenunder (100 − 2×12 − 1×5). Før dette skrev testen 74 og «roundtrip:
  // score» bare konstaterede, at encode() skrev det samme tal ud igen — altså at
  // tallet overlevede en kopiering, ikke at det var det rigtige tal. Derfor
  // regnes den her, og den er i dag fundene — ikke en håndredigeret s= i et link.
  score: 71,
  findings: [
    { id: 'IMG_ALT', sev: 'error', count: 4 },
    { id: 'CONTRAST', sev: 'error', count: 1 },
    { id: 'HEADING_SKIP', sev: 'warning', count: 2 }
  ],
  platform: 'WordPress'
};
const hash = S.encode(RIGTIG);
ok('encode skriver et fragment', /^#u=https%3A%2F%2F/.test(hash), hash);
const tilbage = S.decode(hash);
ok('roundtrip: url', tilbage?.url === RIGTIG.url, JSON.stringify(tilbage));
ok('roundtrip: score', tilbage?.score === 71, JSON.stringify(tilbage));
ok('roundtrip: fundene i rækkefølge', JSON.stringify(tilbage?.findings) === JSON.stringify(RIGTIG.findings));
ok('roundtrip: platform', tilbage?.platform === 'WordPress');
ok('tællerne regnes fra fundene, ikke fra linket',
  tilbage?.errors === 2 && tilbage?.warnings === 1, JSON.stringify(tilbage));

// Scoren skrives ikke i linket. Den *kunne* skrives — den var der før — men så
// er den et tal afsenderen kan rette, og det er præcis det tal kortet hænger
// sin overskrift på. Den udregnes i stedet af fundene, så formatet ikke kan
// indeholde et tal der modsiger den liste der står under det.
ok('encode skriver ingen score i linket', !/[;&]s=/.test(hash), hash);

// Polaritet på selve fundet: et link der *påstår* 100/100 over ét error-fund må
// ikke vise 100. Den gamle kode tog `s=` som det den var.
const ljulet = S.decode('#u=https%3A%2F%2Fex.com;s=100;f=A:e:1');
ok('et s= der lover 100/100 giver ikke 100', ljulet?.score === 88, JSON.stringify(ljulet));
const nedtraet = S.decode('#u=https%3A%2F%2Fex.com;s=0;f=A:e:1');
ok('et s= der siger 0 kan heller ikke sænke scoren', nedtraet?.score === 88, JSON.stringify(nedtraet));
// `s=` er ikke længere et felt, så et link der stadig har et — de fleste links
// i verden lige nu — giver et resultat, ikke en afvisning. Bogmærker må ikke dø
// fordi vi flyttede et tal ud af dem.
const gammeltFormat = S.decode('#u=https%3A%2F%2Fex.com;s=100;f=A:e:1;p=WordPress');
ok('et gammelt link med s= giver stadig sit resultat',
  gammeltFormat?.findings?.length === 1 && gammeltFormat?.errors === 1 && gammeltFormat?.score === 88,
  JSON.stringify(gammeltFormat));

// Et `;` i URL'en overlever. `encodeURIComponent` escaper det, så en codec der
// afkoder hele fragmentet før den deler på `;` ville skære adressen i halv.
const medSemi = S.encode({ ...RIGTIG, url: 'https://example.com/a?b=1;c=2' });
ok('et ; i URL\'en overlever roundtrip', S.decode(medSemi)?.url === 'https://example.com/a?b=1;c=2',
  JSON.stringify(S.decode(medSemi)));

// Fragmenter der ikke er et resultat. Ingen af dem må kaste, og ingen må give
// en kortstabel: en læser der får «alt i orden» på en side han aldrig har set
// scannet, har fået den værste mulige løgn.
const DAARE = [
  ['#u=%', 'et ufuldstændigt procenttegn'],
  ['', 'tomt fragment'],
  ['#url=https%3A%2F%2Fexample.com', 'det gamle #url=-link'],
  ['#u=https%3A%2F%2Fexample.com;s=74', 'ingen fund'],
  ['#u=https%3A%2F%2Fexample.com;s=74;f=', 'tom fund-liste'],
  ['#u=https%3A%2F%2Fexample.com;s=74;f=IMG_ALT:e:0', 'nul fund'],
  ['#u=https%3A%2F%2Fexample.com;s=74;f=IMG_ALT:x:3', 'ukendt alvor'],
  ['#u=https%3A%2F%2Fexample.com;s=74;f=<img src=x>:e:1', 'markup som fund-id'],
  ['#u=javascript:alert(1);s=1;f=A:e:1', 'javascript-adresse'],
  ['#u=/scan-da;s=50;f=A:e:1', 'relativ adresse'],
  ['#u=https%3A%2F%2Fex.com;s=74;f=' + Array.from({ length: 20 }, (_, i) => `A${i}:e:1`).join(','), 'for mange fund'],
  ['#u=https%3A%2F%2Fex.com%0AX-Injected:%201;s=74;f=A:e:1', 'linjeskift i adressen'],
  ['#u=https%3A%2F%2Fex.com;s=74;f=%3Cscript%3Ealert(1)%3C%2Fscript%3E:e:1', 'script som fund-id']
];
for (const [h, hvad] of DAARE) {
  let r;
  try { r = S.decode(h); } catch (e) { r = 'KASTEDE ' + e.message; }
  ok(`afvist: ${hvad}`, r === null, JSON.stringify(r));
}

// En platform der ikke er i tabellen er ikke en fejl i linket — den skal bare
// ikke blive til en guide-bok, så hele fundene stadig vises.
const dumPlatform = S.decode('#u=https%3A%2F%2Fex.com;s=74;f=A:e:1;p=%3Cb%3EShopify%3C%2Fb%3E');
ok('markup som platform giver ingen platform', dumPlatform && dumPlatform.platform === null, JSON.stringify(dumPlatform));
ok('markup som platform ødelægger ikke fundene', dumPlatform?.findings?.length === 1);

// Encode må ikke producere noget den ikke selv kan læse.
ok('encode af en url uden protokol giver intet', S.encode({ ...RIGTIG, url: 'example.com' }) === '');
ok('encode uden fund giver intet', S.encode({ url: RIGTIG.url, score: 71, findings: [] }) === '');
ok('encode uden score giver stadig et link, fordi scoren ikke rejser med',
  /^#u=https%3A%2F%2F/.test(S.encode({ ...RIGTIG, score: null })), S.encode({ ...RIGTIG, score: null }));

// ---------------------------------------------------------------------------
// 2+3. Begge rigtige sider. En håndlavet DOM, så deres egen `render()` og
//      `shareResult()` kan køres på de bytes der faktisk ships.
// ---------------------------------------------------------------------------
function dom(hash = '') {
  const el = () => ({
    _html: '', _text: '', value: '', hidden: true, focused: false,
    set innerHTML(v) { this._html = v; }, get innerHTML() { return this._html; },
    set textContent(v) { this._text = v; }, get textContent() { return this._text; },
    focus() { this.focused = true; }, select() { this.sel = true; },
    addEventListener: () => {}
  });
  const nodes = {};
  return {
    dok: {
      getElementById: (id) => (nodes[id] ||= el()),
      querySelector: () => null,
      addEventListener: () => {},
      hash, origin: 'https://mahope.tools', pathname: '/scan'
    },
    nodes
  };
}

// Trækker den store inline-script-blok ud af siden. Den indeholder både
// DOMParser-koden og de funktioner der testes; kun den behøver en DOM.
function udtraek(html) {
  const blok = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map((m) => m[1])
    .find((k) => k.includes('function gradeOf'));
  ok('inline-script med gradeOf fundet', !!blok);
  return blok || '';
}

// Det afsendte resultat: samme fund, så det kopierede link kan læses tilbage.
const RIGTIG_TIL_SEND = {
  url: RIGTIG.url, score: 71, errors: 2, warnings: 1, findings: RIGTIG.findings, platform: 'WordPress'
};

// ---------------------------------------------------------------------------
// 1b. «Start her», «hvad er ændret» og huskværket. Rene funktioner over
//     fund-lister, så påstanden kan læses direkte — ingen DOM, ingen browser.
//     Polaritet: `startHere` er væk i den gamle kode, og `diffFindings` gav
//     ingen `reduced`/`grew`, kun fund der forsvandt helt.
// ---------------------------------------------------------------------------
const HAR_KERNER = ['rankFindings', 'startHere', 'diffFindings', 'storeKey', 'recall', 'remember']
  .every((k) => typeof S?.[k] === 'function');
// Uden denne guard dør hele filen med en TypeError på den kode der kom før, og
// så er «testen er rød» og «testen gik i stykker» det samme signal.
ok('kernen eksporterer ranking, forskel og huskværk', HAR_KERNER,
  'mangler: ' + ['rankFindings', 'startHere', 'diffFindings', 'storeKey', 'recall', 'remember']
    .filter((k) => typeof S?.[k] !== 'function').join(', '));
const MANGE = [
  { id: 'TARGET_BLANK', sev: 'warning', count: 9 },
  { id: 'IMG_ALT', sev: 'error', count: 2 },
  { id: 'DOC_TITLE', sev: 'error', count: 1 },
  { id: 'HEADING_SKIP', sev: 'warning', count: 40 },
  { id: 'FORM_LABEL', sev: 'error', count: 7 }
];
if (HAR_KERNER) {
  const RANKET = S.rankFindings(MANGE).map((f) => f.id);
  ok('rangering: fejl før advarsel, og flest forekomster først inden for alvor',
    JSON.stringify(RANKET) === JSON.stringify(['FORM_LABEL', 'IMG_ALT', 'DOC_TITLE', 'HEADING_SKIP', 'TARGET_BLANK']),
    JSON.stringify(RANKET));
  ok('rangering: en advarsel med 40 forekomster overstiger ikke ét fejlfund',
    RANKET.indexOf('FORM_LABEL') < RANKET.indexOf('HEADING_SKIP'));
  ok('rangering: kilderækken er ikke muteret',
    MANGE[0].id === 'TARGET_BLANK' && MANGE.length === 5);
  ok('startHere: præcis tre, i den rangerede rækkefølge',
    JSON.stringify(S.startHere(MANGE).map((f) => f.id))
      === JSON.stringify(['FORM_LABEL', 'IMG_ALT', 'DOC_TITLE']),
    JSON.stringify(S.startHere(MANGE).map((f) => f.id)));
  ok('startHere: færre end tre fund giver alle, ikke to',
    S.startHere(MANGE, 3).length === 3 && S.startHere(MANGE.slice(0, 2)).length === 2);
  ok('startHere: et ikke-array er tomt, ikke en fejl',
    Array.isArray(S.startHere(null)) && S.startHere(null).length === 0);

  const FØR = [
    { id: 'IMG_ALT', sev: 'error', count: 4 },
    { id: 'DOC_TITLE', sev: 'error', count: 1 },
    { id: 'TARGET_BLANK', sev: 'warning', count: 6 },
    { id: 'HEADING_SKIP', sev: 'warning', count: 2 }
  ];
  const EFTER = [
    { id: 'IMG_ALT', sev: 'error', count: 4 },
    { id: 'CONTRAST', sev: 'error', count: 1 },
    { id: 'TARGET_BLANK', sev: 'warning', count: 3 }
  ];
  const DIFF = S.diffFindings(FØR, EFTER);
  ok('diff: DOC_TITLE og HEADING_SKIP er væk', JSON.stringify(DIFF.fixed) === JSON.stringify(['DOC_TITLE', 'HEADING_SKIP']),
    JSON.stringify(DIFF.fixed));
  ok('diff: CONTRAST er nyt', JSON.stringify(DIFF.added) === JSON.stringify(['CONTRAST']), JSON.stringify(DIFF.added));
  ok('diff: TARGET_BLANK gik fra 6 til 3 — et fald, ikke en forsvundet regel',
    DIFF.reduced.length === 1 && DIFF.reduced[0].id === 'TARGET_BLANK'
    && DIFF.reduced[0].from === 6 && DIFF.reduced[0].to === 3, JSON.stringify(DIFF.reduced));
  ok('diff: scoren flytter sig med de samme fund', DIFF.scoreFrom === 66 && DIFF.scoreTo === 71,
    DIFF.scoreFrom + ' -> ' + DIFF.scoreTo);
  ok('diff: en ulæselig størrelse giver null, ikke en løgn',
    S.diffFindings(null, EFTER) === null && S.diffFindings(FØR, 'x') === null);
  ok('diff: ingen forskel giver fire tomme lister, så siden kan tie',
    S.diffFindings(FØR, FØR).fixed.length === 0 && S.diffFindings(FØR, FØR).added.length === 0);

  ok('nøglen er vært + sti uden query, så to sider ikke blandes',
    S.storeKey('https://Eksempel.dk/Pris/?utm_source=x#da') === 'eksempel.dk/Pris');
  ok('nøglen er den samme uden http:// og med rod-slash',
    S.storeKey('http://eksempel.dk/pris/') === S.storeKey('https://eksempel.dk/pris'));
  ok('nøglen afviser en adresse der ikke er http(s)', S.storeKey('javascript:alert(1)') === null);

  // Huskeværket med en kvælende localStorage — privat browsertilstand kaster her,
  // og en fejl der bliver en hvid skærm er værre end en manglende forskel.
  function medLagring() {
    const data = {};
    return {
      getItem: (k) => (k in data ? data[k] : null),
      setItem: (k, v) => { data[k] = String(v); },
      kaster: false
    };
  }
  const lagring = medLagring();
  const lagrCtx = { localStorage: lagring };
  lagrCtx.window = lagrCtx;
  lagrCtx.globalThis = lagrCtx;
  vm.createContext(lagrCtx);
  vm.runInContext(readFileSync(new URL('../site/scan-share-core.js', import.meta.url), 'utf8'), lagrCtx);
  const L = lagrCtx.SCANSHARE;

  L.remember('https://eksempel.dk/pris', MANGE);
  const HUSKET = L.recall('https://eksempel.dk/pris');
  ok('husk: fundene kan læses tilbage med id, alvor og antal',
    HUSKET && HUSKET.findings.length === 5
    && HUSKET.findings.find((f) => f.id === 'FORM_LABEL').count === 7
    && HUSKET.findings.find((f) => f.id === 'TARGET_BLANK').sev === 'warning',
    JSON.stringify(HUSKET));
  ok('husk: en anden adresse husker intet', L.recall('https://eksempel.dk/anden') === null);
  ok('husk: en kvotadræbt browser ødelægger ikke siden',
    (() => {
      const død = { getItem() { throw new Error('QuotaExceededError'); }, setItem() { throw new Error('nope'); } };
      const c = { localStorage: død }; c.window = c; c.globalThis = c;
      vm.createContext(c);
      vm.runInContext(readFileSync(new URL('../site/scan-share-core.js', import.meta.url), 'utf8'), c);
      c.SCANSHARE.remember('https://eksempel.dk/pris', MANGE);
      return c.SCANSHARE.recall('https://eksempel.dk/pris') === null;
    })());
  ok('husk: højst ti sider gemmes, så en læser der scanner meget ikke fylder sin egen browser',
    (() => {
      for (let i = 0; i < 14; i++) L.remember('https://eksempel.dk/side-' + i, MANGE);
      const n = Object.keys(JSON.parse(lagring.getItem('eaa:last'))).length;
      return n === 10;
    })(), Object.keys(JSON.parse(lagring.getItem('eaa:last'))).length + ' nøgler');
  ok('husk: en korrumperet lagring giver ingen fund, ikke en fejl',
    (() => {
      const død = { getItem: () => '{ikke json', setItem() {} };
      const c = { localStorage: død }; c.window = c; c.globalThis = c;
      vm.createContext(c);
      vm.runInContext(readFileSync(new URL('../site/scan-share-core.js', import.meta.url), 'utf8'), c);
      return c.SCANSHARE.recall('https://eksempel.dk/pris') === null;
    })());
}

const SIDER = [
  { fil: 'site/scan.html', rute: '/scan', del: 'Copy link to this result', note: 'Shared result for',
    siden: 'Since your last scan of this page', forsvandt: '1 finding(s) gone', nyt: '1 new',
    faldt: '1 fewer',
    startHer: 'Start here — the 3 findings that matter most', alleFund: 'All 4 findings',
    forste: '4 image(s) missing alt text', sidste: '3 link(s) opening in a new window',
    tal: ['4 image(s) missing alt text', '1 text colour combination(s)', '2 heading level skip(s)'] },
  { fil: 'site/scan-da.html', rute: '/scan-da', del: 'Kopiér link til dette resultat', note: 'Delt resultat for',
    siden: 'Siden din sidste scanning af denne side', forsvandt: '1 fund væk', nyt: '1 ny',
    faldt: '1 færre',
    startHer: 'Start her — de 3 fund der betyder mest', alleFund: 'Alle 4 fund',
    forste: '4 billede(r) mangler alt-tekst', sidste: '3 link(s) der åbner i nyt vindue',
    tal: ['4 billede(r) mangler alt-tekst', '1 tekstfarvekombination(er)', '2 sprunget(t) overskriftsniveau(er)'] }
];

async function proevSiden(side) {
  const html = readFileSync(new URL('../' + side.fil, import.meta.url), 'utf8');
  const blok = udtraek(html);

  ok(`${side.fil}: indlæser den delte codec`, /<script src="\/scan-share-core\.js"><\/script>/.test(html));
  ok(`${side.fil}: læser fragmentet gennem SCANSHARE`,
    /SCANSHARE\.decode\(location\.hash\)/.test(blok) && /SCANSHARE\.encode\(LAST\)/.test(blok));
  ok(`${side.fil}: knappen siger hvad den giver`, blok.includes(side.del), side.del);
  ok(`${side.fil}: fund-teksten kommer fra en tabel, ikke fra linket`,
    /const MSG=\{/.test(blok) && !/add\('[A-Z0-9_]+','(?:error|warning)','/.test(blok));
  // Den gamle kode skrev «page has no <title>» direkte i innerHTML, så DOMParser
  // slugte `<title>` som et tag, og læseren så «page has no ». Punkt 2.
  ok(`${side.fil}: fund-teksten escapes`, /esc\(describe\(f\.id,f\.count\)\)/.test(blok));
  // Scoren skal komme fra den delte codec. Før dette stod formlen i begge sider
  // *og* i et `s=` i linket, så tre kopier af et tal, der på kortet står over
  // listen af fund. Dommen dømmer begge: at siden bruger `SCANSHARE.scoreOf`,
  // og at den ikke har sin egen formel mere.
  ok(`${side.fil}: scoren kommer fra den delte codec`,
    /window\.SCANSHARE\.scoreOf\(findings\)/.test(blok), 'ingen scoreOf i scriptet');
  ok(`${side.fil}: siden har ikke sin egen scoreformel mere`,
    !/Math\.max\(0,\s*100\s*-\s*errors\s*\*\s*12/.test(blok),
    'formlen står stadig i scriptet');

  // Kør sidens egen render() og shareResult() på de bytes der faktisk ships.
  // Et *delt* resultat skal gengives uden et eneste netværkskald: modtageren
  // har ingen kvote at brænde, og siden kan være ændret siden. Dommen måler
  // adfærd — `fetch` tælles — fordi en regex over kilden ville være grøn for
  // en render-sti der alligevel kaldte scan().
  // Et link i det gamle format, der *påstår* 100/100. Det er linket der kommer
  // fra en håndredigeret besked — og før rettelsen malede kortet «100/100 —
  // Grade A» over fundene nedenunder. Nu er der kun `f=` at regne på.
  const delt = dom('#u=' + encodeURIComponent(RIGTIG.url) + ';s=100;f='
    + RIGTIG.findings.map((f) => `${f.id}:${f.sev === 'error' ? 'e' : 'w'}:${f.count}`).join(',')
    + ';p=WordPress');
  let kaldte = 0;
  const ctx = {
    document: delt.dok, location: delt.dok, console, SCANSHARE: S,
    navigator: { clipboard: { writeText: async () => {} } },
    fetch: () => { kaldte++; throw new Error('et delt resultat må ikke hente'); }
  };
  ctx.window = ctx;
  ctx.globalThis = ctx;
  vm.createContext(ctx);
  vm.runInContext(blok, ctx);
  // Sidens primære handling skal kunne *ses*. `style.css` har
  // `button:not([class])` — hvid baggrund — med samme specificitet som sidens
  // egen `.scanbox button`, men stylesheetet kommer efter <style>. Uden en
  // klasse vandt den, og «Scan now» stod hvidt på hvidt i den byggede side:
  // målt i Chromium på /scan og /scan-da, 390 og 1280 px, lys og mørk.
  // Den måles på kilden og ikke på `render()`, så dommen gælder også den
  // kode der ikke kan findes i scriptet.
  ok(`${side.fil}: sidens primære handling har en klasse, så designsystemets \`button:not([class])\` ikke tager den`,
    /<button type="submit" class="[^"]+"/.test(html),
    'fundet: ' + (html.match(/<button type="submit"[^>]*>/) || ['ingen'])[0]);
  // Den gamle kode har hverken `render()` eller `LAST`. Så rapporterer dommen
  // rød og går videre, i stedet for at hele testen dør med en TypeError —
  // ellers er «testen er rød» og «testen gik i stykker» det samme signal.
  if (typeof ctx.render !== 'function') {
    ok(`${side.fil}: siden har en render() den delte sti kan bruge`, false, 'ingen render() i scriptet');
    ok(`${side.fil}: et delt resultat kalder ingen scanning`, false, 'ingen render() — ikke målt');
    ok(`${side.fil}: et delt resultat viser scannets adresse`, false, 'ingen render() — ikke målt');
    ok(`${side.fil}: et delt resultat siger det er et øjebliksbillede`, false, 'ingen render() — ikke målt');
    ok(`${side.fil}: et delt resultat scorer fundene, ikke linkets s=`, false, 'ingen render() — ikke målt');
    ok(`${side.fil}: fundene gengives med antal`, false, 'ingen render() — ikke målt');
    ok(`${side.fil}: rettelsesteksten er med`, false, 'ingen render() — ikke målt');
    ok(`${side.fil}: platformens guide er med`, false, 'ingen render() — ikke målt');
    ok(`${side.fil}: pro-kortet er stadig med`, false, 'ingen render() — ikke målt');
    ok(`${side.fil}: donationslinjen er stadig med`, false, 'ingen render() — ikke målt');
    ok(`${side.fil}: intet råt markup fra brugerens adresse`, false, 'ingen render() — ikke målt');
    ok(`${side.fil}: «<title>» i fund-teksten er escaped`, false, 'ingen render() — ikke målt');
    ok(`${side.fil}: rettelsen under DOC_TITLE er også escaped`, false, 'ingen render() — ikke målt');
    ok(`${side.fil}: shareLink bliver vist`, false, 'ingen shareResult() — ikke målt');
    ok(`${side.fil}: shareLink peger på ${side.rute}`, false, 'ingen shareResult() — ikke målt');
    ok(`${side.fil}: statuslinjen siger noget`, false, 'ingen shareResult() — ikke målt');
    ok(`${side.fil}: det kopierede link kan læses tilbage`, false, 'ingen shareResult() — ikke målt');
    return;
  }
  ok(`${side.fil}: et delt resultat kalder ingen scanning`, kaldte === 0, kaldte + ' netværkskald');
  const nodes = delt.nodes;
  const ud = nodes.result?.innerHTML || '';
  ok(`${side.fil}: et delt resultat viser scannets adresse`, ud.includes('https://example.com/pris'), ud.slice(0, 300));
  ok(`${side.fil}: et delt resultat siger det er et øjebliksbillede`, ud.includes(side.note));
  // 2 errors + 1 warning er pr. side egen formel 100 − 24 − 5 = 71, altså
  // Grade C. Linket siger 100/100. Kortet skal vise 71 — ellers står der
  // «Grade A» over en liste med fund i, og det er det review-fundet fandt.
  ok(`${side.fil}: et delt resultat scorer fundene, ikke linkets s=`,
    ud.includes('71/100 — Grade C') && !ud.includes('100/100'), ud.slice(0, 220));
  ok(`${side.fil}: fundene gengives med antal`, side.tal.every((t) => ud.includes(t)), side.tal.join(' | '));
  ok(`${side.fil}: rettelsesteksten er med`, ud.includes('alt='), ud.slice(0, 300));
  ok(`${side.fil}: platformens guide er med`, ud.includes('/guides/wordpress-accessibility-check'));
  ok(`${side.fil}: pro-kortet er stadig med`, ud.includes('buy.stripe.com'));
  ok(`${side.fil}: donationslinjen er stadig med`, ud.includes('donate.stripe.com'));
  ok(`${side.fil}: intet råt markup fra brugerens adresse`, !ud.includes('<script>alert'));
  // `<title>` overlever i DOM-kilden, men sluges som et tag hvis teksten ikke
  // escapes — så læseren så «page has no » i stedet for «page has no <title>».
  // DOC_TITLE-fundet afslører escapingen. Skrives teksten råt i innerHTML,
  // sluger DOMParser `<title>` som et tag, og læseren så «page has no » i
  // stedet for «page has no <title>» — det var den gamle kodes fejl.
  // `let LAST` og `const MSG` er lexikale bindinger i scriptet, ikke
  // egenskaber på window — derfor læses de *inde i* vm'en, som browseren gør.
  const MSG = vm.runInContext('MSG', ctx);
  ctx.render({ url: RIGTIG.url, score: 88, errors: 1, warnings: 0,
               findings: [{ id: 'DOC_TITLE', sev: 'error', count: 1 }], platform: null }, { shared: true });
  const medTitel = nodes.result?.innerHTML || '';

  ok(`${side.fil}: «<title>» i fund-teksten er escaped`,
    MSG.DOC_TITLE.includes('<title>') && medTitel.includes('&lt;title&gt;') && !/page has no <\/title>/.test(medTitel),
    medTitel.slice(0, 260));
  ok(`${side.fil}: rettelsen under DOC_TITLE er også escaped`, medTitel.includes('&lt;head&gt;'), medTitel.slice(0, 400));

  // Et *nyt* resultat skal kunne fortælle hvad der er ændret siden sidste
  // scanning, og fundene skal stå i en rækkefølge læseren kan handle i.
  // Delt resultat tæller ikke: det er afsenderens fund, ikke modtagerens, så
  // en delt rapport må aldrig skrive «siden din sidste scanning».
  const lagring = (() => {
    const data = {};
    return { getItem: (k) => (k in data ? data[k] : null), setItem: (k, v) => { data[k] = String(v); } };
  })();
  ctx.localStorage = lagring;
  // Kernen genindlæses i *sidens* kontekst, så `recall()`/`remember()` lukker
  // om den lagring denne side har. Codecen ovenfor blev indlæst uden en, og en
  // dom der så prøvede at huske gennem den ville være grøn fordi den læste
  // ingenting — «ingen forskel» og «kan ikke se forskellen» er samme fejl.
  const S_ET_NU = ctx.SCANSHARE;
  ok(`${side.fil}: siden kan huske og sammenligne fundene`, ['remember', 'recall', 'diffFindings', 'rankFindings']
    .every((k) => typeof S_ET_NU?.[k] === 'function'),
    'kernen mangler: ' + ['remember', 'recall', 'diffFindings', 'rankFindings']
      .filter((k) => typeof S_ET_NU?.[k] !== 'function').join(', '));
  // Resten af dommen kan ikke køre på koden fra før: den kalder `remember()`
  // og `diffFindings()`. Uden denne guard dør filen med en TypeError, og så er
  // «testen er rød» og «testen gå i stykker» det samme signal.
  if (typeof S_ET_NU.remember === 'function') {
  vm.runInContext(readFileSync(new URL('../site/scan-share-core.js', import.meta.url), 'utf8'), ctx);
    const FØR = [
      { id: 'IMG_ALT', sev: 'error', count: 4 },
      { id: 'DOC_TITLE', sev: 'error', count: 1 },
      { id: 'TARGET_BLANK', sev: 'warning', count: 6 },
      { id: 'HEADING_SKIP', sev: 'warning', count: 2 }
    ];
    const EFTER_FUND = [
      { id: 'TARGET_BLANK', sev: 'warning', count: 3 },
      { id: 'CONTRAST', sev: 'error', count: 1 },
      { id: 'IMG_ALT', sev: 'error', count: 4 },
      { id: 'DOC_TITLE', sev: 'error', count: 1 }
    ];
    ctx.SCANSHARE.remember(RIGTIG.url, FØR);
    ctx.render({ url: RIGTIG.url, score: 60, errors: 3, warnings: 1,
                 findings: EFTER_FUND, platform: null });
    const efter = nodes.result?.innerHTML || '';
    ok(`${side.fil}: et nyt resultat siger hvad der er ændret siden sidste scanning`,
      efter.includes(side.siden), efter.slice(0, 300));
    ok(`${side.fil}: forskellen tæller fund, der forsvandt, nye der kom og et der faldt`,
      efter.includes(side.forsvandt) && efter.includes(side.nyt) && efter.includes(side.faldt),
      efter.slice(0, 400));
    ok(`${side.fil}: forskelsen er skrevet med læserens sprog, ikke med fund-id'er`,
      !/TARGET_BLANK|HEADING_SKIP|CONTRAST/.test(efter.split(side.siden)[1] || ''),
      (efter.split(side.siden)[1] || '').slice(0, 300));
    ok(`${side.fil}: fundene står i den rangerede rækkefølge, ikke i kodens`,
      efter.indexOf(side.forste) < efter.indexOf(side.sidste), efter.slice(0, 700));
    ok(`${side.fil}: «start her» står over præcis de tre, og hele listen stadig med`,
      efter.includes(side.startHer) && efter.includes(side.alleFund), efter.slice(0, 700));
    ok(`${side.fil}: et delt resultat skriver aldrig «siden din sidste scanning»`,
      !medTitel.includes(side.siden), medTitel.slice(0, 300));
  } else {
    ok(`${side.fil}: et nyt resultat siger hvad der er ændret siden sidste scanning`, false, 'ingen remember()');
    ok(`${side.fil}: forskellen tæller fund, der forsvandt, nye der kom og et der faldt`, false, 'ingen remember()');
    ok(`${side.fil}: forskelsen er skrevet med læserens sprog, ikke med fund-id'er`, false, 'ingen remember()');
    ok(`${side.fil}: fundene står i den rangerede rækkefølge, ikke i kodens`, false, 'ingen remember()');
    ok(`${side.fil}: «start her» står over præcis de tre, og hele listen stadig med`, false, 'ingen remember()');
    ok(`${side.fil}: et delt resultat skriver aldrig «siden din sidste scanning»`, !medTitel.includes(side.siden), medTitel.slice(0, 300));
  }

  vm.runInContext('LAST = ' + JSON.stringify(RIGTIG_TIL_SEND), ctx);
  await ctx.shareResult();
  const box = nodes.shareLink;
  ok(`${side.fil}: shareLink bliver vist`, box && box.hidden === false);
  ok(`${side.fil}: shareLink peger på ${side.rute}`, box?.value?.startsWith('https://mahope.tools' + side.rute + '#u='), box?.value);
  ok(`${side.fil}: statuslinjen siger noget`, (nodes.shareStatus?.textContent || '').length > 10, nodes.shareStatus?.textContent);
  // `?.` hele vejen: uden `render()` findes feltet ikke, og dommen skal
  // rapportere rød — ikke dø med en TypeError, for så er «testen er rød» og
  // «testen gik i stykker» det samme signal.
  const r = box?.value ? S.decode(box.value.slice(box.value.indexOf('#'))) : null;
  ok(`${side.fil}: det kopierede link kan læses tilbage`,
    r && r.url === RIGTIG.url && r.findings.length === 3 && r.findings[2].count === 2, JSON.stringify(r));

  // Det gamle `#url=`-link skal stadig virke: gamle bogmærker og SMS-links må
  // ikke dø af den nye kode. `fetch` kaster her, så det er selve kaldet der
  // dømmes — ikke resultatet af en scanning.
  const gammel = dom('#url=' + encodeURIComponent('https://example.com/gammel'));
  const ctx2 = {
    document: gammel.dok, location: gammel.dok, console, SCANSHARE: S, navigator: {},
    fetch: () => { kaldte++; return Promise.reject(new Error('stop')) }
  };
  ctx2.window = ctx2;
  ctx2.globalThis = ctx2;
  vm.createContext(ctx2);
  try { vm.runInContext(blok, ctx2); } catch (e) { /* fetch-fejlen er forventet */ }
  ok(`${side.fil}: det gamle #url=-link scanner stadig`,
    gammel.dok.getElementById('url').value === 'https://example.com/gammel',
    gammel.dok.getElementById('url').value);
  ok(`${side.fil}: #url= kalder scanning, #u= ikke`, kaldte === 1, kaldte + ' netværkskald');
}

for (const side of SIDER) await proevSiden(side);

console.log(`\nscan-share: ${pass} bestået, ${fail} fejlet`);
process.exit(fail ? 1 : 0);