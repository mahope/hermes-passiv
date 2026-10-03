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
  score: 74,
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
ok('roundtrip: score', tilbage?.score === 74);
ok('roundtrip: fundene i rækkefølge', JSON.stringify(tilbage?.findings) === JSON.stringify(RIGTIG.findings));
ok('roundtrip: platform', tilbage?.platform === 'WordPress');
ok('tællerne regnes fra fundene, ikke fra linket',
  tilbage?.errors === 2 && tilbage?.warnings === 1, JSON.stringify(tilbage));

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
  ['#u=https%3A%2F%2Fex.com;s=abc;f=A:e:1', 'score der ikke er et tal'],
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
ok('encode uden fund giver intet', S.encode({ url: RIGTIG.url, score: 74, findings: [] }) === '');
ok('encode uden score giver intet', S.encode({ ...RIGTIG, score: null }) === '');

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
  url: RIGTIG.url, score: 74, errors: 2, warnings: 1, findings: RIGTIG.findings, platform: 'WordPress'
};

const SIDER = [
  { fil: 'site/scan.html', rute: '/scan', del: 'Copy link to this result', note: 'Shared result for',
    tal: ['4 image(s) missing alt text', '1 text colour combination(s)', '2 heading level skip(s)'] },
  { fil: 'site/scan-da.html', rute: '/scan-da', del: 'Kopiér link til dette resultat', note: 'Delt resultat for',
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

  // Kør sidens egen render() og shareResult() på de bytes der faktisk ships.
  // Et *delt* resultat skal gengives uden et eneste netværkskald: modtageren
  // har ingen kvote at brænde, og siden kan være ændret siden. Dommen måler
  // adfærd — `fetch` tælles — fordi en regex over kilden ville være grøn for
  // en render-sti der alligevel kaldte scan().
  const delt = dom('#u=' + encodeURIComponent(RIGTIG.url) + ';s=74;f='
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