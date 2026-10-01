// Ende-til-ende-test af de gratis værktøjer, der kalder vores egen worker:
// `/compliance-site-check` (EN + DA), `/url-inspector`, `/page-profile` (EN + DA),
// `book-ai.js`, `/compliance-ai` (EN + DA) og `/security-headers-check`.
//
// Baggrund: begge klienter gjorde `r.json()` på *ethvert* svar. Cloudflare
// svarer en worker der er faldet ned med en HTML-side, så `.json()` kastede og
// catch'en skrev "Network error: Unexpected token '<'" — altså skyldte vores egen
// 5xx besøgerens wifi, og et forbigående blip gav op efter ét forsøg. Det er den
// samme fejlklasse som `/thanks` havde, og den rammer de sider en bruger møder
// *før* de overhovedet kan se et betalt tilbud.
//
// Testen indlæser sidernes egne scripts i en vm-sandkasse med en minimal DOM og
// kører dem mod et programmeret svarforløb, så "genkalder den?" og "hvad står der
// i fejlkassen?" dømmes på den kode der faktisk ships — ikke på en kopi.
import { readFileSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import vm from 'node:vm';

const root = fileURLToPath(new URL('..', import.meta.url));

let pass = 0, fail = 0;
const ok = (navn, cond, info = '') => { if (cond) pass++; else { fail++; console.log('FEJL:', navn, info); } };

// --------------------------------------------------------------------------
// 1. Sandkassen. Kun det sidernes scripts rører ved opstart og i fejlvejen.
// --------------------------------------------------------------------------
// Elementstubben beholder også sine lystere, fordi `/url-inspector` kalder
// `inspect()` fra en knap og ikke fra topniveau. `createTextNode` ligger på
// `document`, fordi sidernes `esc()` bruger den.
function el() {
  const e = {
    value: '', disabled: false, src: '', _t: '', _h: undefined,
    // `esc()` på de nye sider sætter `textContent` og læser `innerHTML` tilbage,
    // så de to skal hænge sammen. Hver beholder kun det der blev sat.
    get textContent() { return this._t; },
    set textContent(v) { this._t = v; this._h = undefined; },
    get innerHTML() { return this._h !== undefined ? this._h : this._t; },
    set innerHTML(v) { this._h = v; },
    style: {}, dataset: {}, children: [], _ls: {},
    // `remove()` sætter et flag i stedet for at være en no-op: kapabilitets-
    // sonden på `/compliance-ai` skjuler chatten ved at fjerne `#askArea`, og
    // uden flaget kunne dommen ikke se forskel på «chatten er væk» og «der var
    // aldrig en chat» — den ville være grøn på en side der fjerner den hele
    // tidligere end den skjuler den.
    _removed: false,
    remove() { this._removed = true; },
    classList: { _s: new Set(), add(c) { this._s.add(c); }, remove(c) { this._s.delete(c); }, contains(c) { return this._s.has(c); } },
    // `esc()` på siderne hænger en text-node på et midlertidigt element og
    // læser `innerHTML` tilbage. Uden at `appendChild` gjorde noget, gav den
    // tomme strenge for *alt* gennem esc — også de URLs, resultatet viser, så
    // dommen «begge sites står i resultatet» kunne ikke se dem.
    appendChild(child) { if (child && typeof child.textContent === 'string') { this._t += child.textContent; this._h = undefined; } },
    removeChild() {}, setAttribute() {}, focus() {},
    getAttribute: () => null,
    addEventListener(t, fn) { (this._ls[t] = this._ls[t] || []).push(fn); },
    // `fire()` lader en test gøre det en bruger gør: sætte værdien og udløse
    // lytteren. `/clean-copy-tool` binder `convert()` på `input` og holder den
    // i en IIFE, så der er ingen anden vej ind — sandkassen skal kunne trykke
    // på tastaturet, ellers kan kortet kun dømmes ved at kalde kode den ikke
    // eksponerer.
    fire(t) { (this._ls[t] || []).forEach((fn) => fn({ target: this, preventDefault() {} })); },
    click() { (this._ls.click || []).forEach((fn) => fn({})); },
    submit() { (this._ls.submit || []).forEach((fn) => fn({ preventDefault() {} })); },
    querySelectorAll: () => [],
    // Et elements `querySelector` giver et element i en rigtig browser. Det
    // `/contrast-checker` er afhængig af: den maler på `preview.querySelector
    // ('.large')`, så en `null` her døde siden ved sidevisning.
    querySelector: () => el(),
  };
  return e;
}

// Et 2D-canvas der svarer, så `/text-on-image-checker` kan køre rigtigt igennem
// i sandkassen. Det er kun et læse-skab: `getImageData` giver et ensfarvet
// billede, så værktøjet har noget at måle på og skriver sit resultat —
// dommen skal ikke dømme et tal, men at købsvejen lander i den markup der
// kommer ud af et gennemført tjek. Uden denne ville siden fejle på
// `getContext` og dommen ville aldrig nå sin påstand.
function ctx2d() {
  const grad = { addColorStop() {} };
  return {
    canvas: null, font: '', textBaseline: '', fillStyle: '',
    measureText: (t) => ({ width: Math.max(8, String(t || '').length * 9) }),
    getImageData: (x, y, w, h) => {
      const n = Math.max(1, Math.round(w) * Math.max(1, Math.round(h)));
      // Baggrund lys, bogstaver dækker intet: så er «ingen pixels dækket af
      // tekst» den sande svar, og værktøjet falder tilbage på fotoet under
      // boksen — den sti, der findes ved måling på en rigtig side.
      return { data: new Uint8ClampedArray(n * 4).fill(200) };
    },
    putImageData() {}, drawImage() {}, clearRect() {}, fillRect() {},
    fillText() {}, beginPath() {}, arc() {}, fill() {}, save() {}, restore() {},
    createLinearGradient: () => grad, createRadialGradient: () => grad,
    translate() {}, scale() {}, rect() {},
  };
}
const withCanvas = (e) => { e.getContext = () => ctx2d(); e.width = 900; e.height = 420; return e; };

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
// Genkalderne står i produktionskoden med 1200 ms mellemrum. Sandkassen klemmer
// dem til 0, så en test ikke skal vente minutter — antallet forsøg måles i stedet.
const fastTimeout = (fn, _ms, ...rest) => setTimeout(fn, 0, ...rest);

// `/net.js` er den delte hjælper. Sektion 10 sætter denne til en muteret kopi for
// at bevise, at alle tre klienter virkelig læser *én* implementering.
let netOverride = null;

function loadPage(path, fetchImpl, opts = {}) {
  // En `.js`-fil (som `book-ai.js`) køres som den er; en `.html` får sine egne
  // inline scripts. `match` vælger det rigtige script på de sider hvor et andet
  // end klientens også rører `fetch` (fx analytics der poster på /api/track).
  // `opts.source` gør at mutationen kan køre den *gamle* sides bytes gennem
  // samme sandkasse, så en dom er målt på kode der faktisk har kørt.
  const html = opts.source ?? readFileSync(join(root, path), 'utf8');
  const scripts = path.endsWith('.js')
    ? [html]
    : [...html.matchAll(/<script(?![^>]*\bsrc=)(?![^>]*ld\+json)[^>]*>([\s\S]*?)<\/script>/g)].map((m) => m[1]);
  const main = path.endsWith('.js')
    ? html
    : opts.match
      ? scripts.find((s) => opts.match.test(s))
      : scripts.find((s) => /fetch\(|inspect|scan/.test(s) && !/api\/track/.test(s));
  if (!main) throw new Error(`ingen brugbar <script> i ${path}`);
  const nodes = new Map();
  // Felternes startværdier læses *af siden selv*, ellers kører værktøjet med
  // tomme felter hvor browseren ville have `#ffffff` og „Your headline here“.
  // `/text-on-image-checker` regner på den værdi: uden den er forholdet NaN,
  // og dommen ville måle en side der aldrig viser et resultat.
  const seeds = {};
  for (const m of html.matchAll(/<(?:input|select|textarea)\b[^>]*\bid="([^"]+)"[^>]*>/g)) {
    const v = /\bvalue="([^"]*)"/.exec(m[0]);
    if (v) seeds[m[1]] = v[1];
  }
  // `opts.canvas` giver hver stub et læse-canvas. Kun `/text-on-image-checker`
  // har brug for det; de andre sider kalder aldrig `getContext`.
  const make = (id) => {
    const n = el();
    if (id in seeds) n.value = seeds[id];
    if (opts.canvas) withCanvas(n);
    return n;
  };
  // `book-ai.js` bygger sin egen sektion og hænger den før <footer>, så
  // sandkassen skal have et footer-element med en forælder.
  const footer = make();
  footer.parentNode = { insertBefore() {} };
  const sandbox = {
    console, setTimeout: fastTimeout, clearTimeout, URL, URLSearchParams, Promise, Error, JSON, Date, Math,
    encodeURIComponent, Object, Array, String, Number, Boolean, RegExp, Map, Set, Blob,
    scrollTo() {}, print() {}, alert() {}, confirm: () => true,
    // `window` *er* sandkassen, så værktøjer der binder på `window` (dragging
    // på canvas) skal kunne gøre det. Ingen lytter skal dog fyre i en test.
    addEventListener() {}, removeEventListener() {},
    fetch: fetchImpl,
    document: {
      getElementById(id) {
        // `opts.absent` er id'er siden *ikke* har i DOM'en. Uden dem ville
        // stubben skabe dem, og en vagt som `if (getElementById('x')) return;`
        // ville altid tro at elementet allerede var der.
        if (opts.absent && opts.absent.includes(id)) return null;
        if (!nodes.has(id)) nodes.set(id, make(id));
        return nodes.get(id);
      },
      querySelector(sel) { return sel === 'footer' && !opts.noFooter ? footer : null; },
      querySelectorAll: () => [],
      addEventListener() {}, createElement: () => make(), createTextNode: (t) => ({ textContent: t }),
      body: make(), documentElement: make(), head: make(),
      // `/scan` går selv igennem det hentede HTML med `DOMParser` og løber så
      // reglerne over `querySelectorAll`. Sandkassen skal derfor kunne gennemføre
      // et gennemført tjek, så dommen om pro-kortet måles på den markup siden
      // faktisk skriver. Der er ingen elementer at finde, så tjekket finder ingen
      // fejl — det er fund-kortet og dets købsvej, dommen handler om.
      createTreeWalker: () => ({ nextNode: () => null }),
    },
    // Samme grund. En tom `doc` med det `#scan` læser, så kaldet kører hele vejen
    // igennem og skriver sit resultat.
    DOMParser: class {
      parseFromString() {
        return {
          images: [], title: 'Example', body: make(), documentElement: make(),
          querySelectorAll: () => [], querySelector: () => null,
        };
      }
    },
    NodeFilter: { SHOW_TEXT: 4 },
    navigator: { doNotTrack: '0' },
    location: { pathname: '/' + path.split('/').pop(), href: 'https://mahope.tools/', hash: '' },
  };
  sandbox.window = sandbox;
  sandbox.globalThis = sandbox;
  vm.createContext(sandbox);
  // `/net.js` står med `defer` i head, så browseren har kørt den længe før nogen
  // kan klikke. Sandkassen gør det samme — ellers ville de tre klienter der læser
  // den delte hjælper blive dømt mod en global der aldrig findes.
  vm.runInContext(netOverride ?? readFileSync(join(root, 'site/net.js'), 'utf8'), sandbox, { filename: 'site/net.js' });
  vm.runInContext(main, sandbox, { filename: path });
  return { sandbox, nodes };
}

// Svarene kommer som en række, og der tælles kald, så "prøver den igen?" kan
// måles i stedet for at læses.
//
// `opts.skip` tager kald ud af rækken uden at tælle dem: `/api/track`-beacons
// fra analytics er en bivirkning, ikke en del af det værktøjet gør. Uden den
// undtagelse spiste en beacon et programmeret svar, og et tjek der *skal*
// genkalde efter en 502 så enten ikke gjorde det eller fik svaret to gange —
// altså blev dommen om prøv-igen grøn på en fejl.
//
// En post må være `{ test, body }` i stedet for et regex, fordi nogle sider
// *inden* de gør noget læser kapabilitet fra den samme rute som værktøjet
// bruger: `/compliance-ai` spørger ved sidevisning «er assistenten tændt?» med
// et GET, og stiller bagefter det samme spørgsmål med et POST. Kun regexet kunne
// ikke skelne de to, så sonden spiste det første programmerede svar — og så blev
// dommen om både prøv-igen og kvoten grøn på det forkerte svar. `test` får derfor
// både url og `init`, så metoden kan være en del af dommen, og `body` er det
// svar klienten læser i stedet for et tomt objekt.
function responses(list, opts = {}) {
  const state = { calls: 0, urls: [] };
  const skips = (opts.skip || []).map((s) => (s instanceof RegExp ? { test: (u) => s.test(u) } : s));
  const fetchImpl = async (url, init) => {
    state.urls.push(String(url));
    for (const s of skips) {
      if (s.test(String(url), init)) return { ok: true, status: 200, json: async () => s.body || {} };
    }
    const i = state.calls++;
    const step = list[Math.min(i, list.length - 1)];
    if (step.reject) throw new Error(step.reject);
    const body = step.html ? '<html>error</html>' : JSON.stringify(step.body);
    return {
      ok: step.status >= 200 && step.status < 300,
      status: step.status,
      json: async () => { if (step.html) throw new SyntaxError("Unexpected token '<'"); return JSON.parse(body); },
    };
  };
  return { fetchImpl, state };
}

const OK_SCAN = { status: 200, body: { ok: true, url: 'https://example.com', score: 90, grade: 'A', passed: 9, total: 10, results: {} } };
const OK_INSPECT = { status: 200, body: { inspectUrl: 'https://example.com', finalUrl: 'https://example.com/', finalStatus: 200, finalStatusText: 'OK', totalRedirects: 0, redirectChain: [], headers: [] } };

async function runScan(path, list) {
  const { fetchImpl, state } = responses(list);
  const { sandbox, nodes } = loadPage(path, fetchImpl);
  nodes.get('urlInput').value = 'example.com';
  await sandbox.scan();
  await sleep(30);
  return { calls: state.calls, err: (nodes.get('errorBox') || {}).textContent || '', cta: (nodes.get('ctaBox') || {}).style?.display };
}

// `/url-inspector` kører en eksempel-URL ved sidevisning (`setTimeout(..., 300)`).
// Den tælles ikke med: målingen starter efter at den er faldt, og klikket på
// knappen er den vej en besøger faktisk tager. Men siden har et `value=` i
// markup, så den kørte URL'en *kun* fordi sandkassens felt var tomt før —
// altså bruger det første svar i listen på den og klikket får det anden.
// Derfor præfiksér listen med ét svar, der kun den auto-kørsel kan nå.
async function runInspect(list) {
  const { fetchImpl, state } = responses([OK_INSPECT, ...list], { skip: [/api\/track/] });
  const { sandbox, nodes } = loadPage('site/url-inspector/index.html', fetchImpl);
  await sleep(30);
  const base = state.calls;
  nodes.get('url-input').value = 'https://example.com';
  nodes.get('inspect-btn').click();
  await sleep(30);
  return { calls: state.calls - base, err: (nodes.get('error-placeholder') || {}).innerHTML || '' };
}

const PAGES = [
  ['site/compliance-site-check.html', 'EN'],
  ['site/da/compliance-site-check.html', 'DA'],
];

// --------------------------------------------------------------------------
// 2. Det gamle svar skal stadig virke, og det skal gøre det på ét kald.
// --------------------------------------------------------------------------
for (const [path, lang] of PAGES) {
  const r = await runScan(path, [OK_SCAN]);
  ok(`${lang}: et godt svar renderer på ét kald`, r.calls === 1 && r.cta === '', `calls=${r.calls} cta=${JSON.stringify(r.cta)} err=${r.err}`);
  ok(`${lang}: et godt svar giver ingen fejl`, r.err === '', r.err);
}

// --------------------------------------------------------------------------
// 3. Kernen: en 5xx med HTML-krop (Cloudflares egen side) skal genkaldes, og
//    brugeren må aldrig få skylden for vores egen fejl.
// --------------------------------------------------------------------------
for (const [path, lang] of PAGES) {
  const r = await runScan(path, [{ status: 502, html: true }, OK_SCAN]);
  ok(`${lang}: 502 med HTML genkaldes og lykkes`, r.calls === 2 && r.err === '' && r.cta === '', `calls=${r.calls} err=${r.err}`);
}
{
  const r = await runScan('site/compliance-site-check.html', [{ status: 503, html: true }]);
  ok('EN: 503 hele vejen giver tre forsøg, ikke ét', r.calls === 3, `calls=${r.calls}`);
  ok('EN: 503 hele vejen skylder ikke brugerens netværk', /temporarily unavailable/.test(r.err) && !/Network error/.test(r.err), r.err);
}
{
  const r = await runScan('site/da/compliance-site-check.html', [{ status: 503, html: true }]);
  ok('DA: 503 hele vejen skylder ikke brugerens netværk', /midlertidigt utilgængelig/.test(r.err) && !/Netværksfejl/.test(r.err), r.err);
}
{
  const r = await runScan('site/compliance-site-check.html', [{ status: 429, body: { ok: false, error: 'Too many scans this hour.' } }]);
  ok('EN: 429 er endeligt, ét kald, og viser serverens timegrænse',
    r.calls === 1 && /Too many scans this hour/.test(r.err), `calls=${r.calls} err=${r.err}`);
}
{
  const r = await runScan('site/compliance-site-check.html', [{ status: 400, body: { ok: false, error: 'Missing ?url= parameter' } }]);
  ok('EN: et 4xx er endeligt og viser serverens egen tekst', r.calls === 1 && r.err === 'Missing ?url= parameter', `calls=${r.calls} err=${r.err}`);
}
{
  const r = await runScan('site/compliance-site-check.html', [{ reject: 'Failed to fetch' }]);
  ok('EN: et afbrudt kald prøves igen og skyldes ikke vores server', r.calls === 3 && /could not reach the scan server/.test(r.err) && !/Network error/.test(r.err), `calls=${r.calls} err=${r.err}`);
}
{
  const r = await runScan('site/da/compliance-site-check.html', [{ reject: 'Failed to fetch' }]);
  ok('DA: et afbrudt kald prøves igen og skyldes ikke vores server', r.calls === 3 && /kunne ikke nå scanningsserveren/.test(r.err) && !/Netværksfejl/.test(r.err), `calls=${r.calls} err=${r.err}`);
}

// --------------------------------------------------------------------------
// 4. Samme regel i url-inspector.
// --------------------------------------------------------------------------
{
  const r = await runInspect([{ status: 500, html: true }, OK_INSPECT]);
  ok('url-inspector: 500 med HTML genkaldes og lykkes', r.calls === 2 && !/temporarily unavailable/.test(r.err), `calls=${r.calls} err=${r.err}`);
}
{
  const r = await runInspect([{ status: 503, html: true }]);
  ok('url-inspector: 503 hele vejen giver tre forsøg og en ærlig tekst', r.calls === 3 && /temporarily unavailable/.test(r.err) && !/Network error/.test(r.err), `calls=${r.calls} err=${r.err}`);
}
{
  const r = await runInspect([{ status: 400, body: { error: 'Invalid URL' } }]);
  ok('url-inspector: et 4xx er endeligt og viser serverens tekst', r.calls === 1 && /Invalid URL/.test(r.err), `calls=${r.calls} err=${r.err}`);
}
{
  // Workerens egen særform: 200 med et `error`-felt på en redirect-kæde den
  // ikke kan følge. Det er et rigtigt svar og må ikke genkaldes.
  const r = await runInspect([{ status: 200, body: { error: 'Invalid redirect location' } }]);
  ok('url-inspector: 200 med error-felt er stadig en fejl, ét kald', r.calls === 1 && /Invalid redirect location/.test(r.err), `calls=${r.calls} err=${r.err}`);
}
{
  const r = await runInspect([OK_INSPECT]);
  ok('url-inspector: et godt svar renderer på ét kald', r.calls === 1 && r.err === '', `calls=${r.calls} err=${r.err}`);
}

// --------------------------------------------------------------------------
// 5. `/page-profile` (EN + DA): GET-kaldet gjorde også blindt `r.json()`, så
//    vores egen 5xx blev vist som "Could not reach the profiling service" —
//    én gang, uden genkald, og en 4xx fik samme tekst.
// --------------------------------------------------------------------------
const OK_PROFILE = { status: 200, body: { ok: true, url: 'https://example.com', status: 200, final_url: 'https://example.com', title: 'A perfectly reasonable page title', title_length: 32, meta_description: 'A description that is long enough to pass the length check used by the tool here.', meta_description_length: 90, canonical: 'https://example.com', language: 'en', charset: 'utf-8', og: { title: 't', description: 'd', image: 'i' }, twitter: { card: 'summary' }, json_ld_count: 1, json_ld_types: ['WebSite'], headings: { h1: ['Example'] }, images: { total: 2, with_alt: 2 }, links: { total: 5, internal: 5 }, security: { hsts: true, csp: true, xfo: true }, score: 92, max_score: 100, grade: 'A', penalties: [] } };

async function runProfile(path, list) {
  const { fetchImpl, state } = responses(list);
  const { nodes } = loadPage(path, fetchImpl, { match: /profile-form/ });
  nodes.get('profile-url').value = 'example.com';
  nodes.get('profile-form').submit();
  await sleep(30);
  return { calls: state.calls, out: (nodes.get('profile-result').innerHTML) || '' };
}

for (const [path, lang] of [['site/page-profile.html', 'EN'], ['site/da/page-profile.html', 'DA']]) {
  const good = await runProfile(path, [OK_PROFILE]);
  ok(`${lang} page-profile: et godt svar renderer på ét kald`, good.calls === 1 && !/temporarily unavailable|Error:/.test(good.out), `calls=${good.calls} out=${good.out.slice(0,200)}`);

  const busy = await runProfile(path, [{ status: 502, html: true }, OK_PROFILE]);
  ok(`${lang} page-profile: 502 med HTML genkaldes og lykkes`, busy.calls === 2 && !/temporarily unavailable/.test(busy.out), `calls=${busy.calls}`);

  const dead = await runProfile(path, [{ status: 503, html: true }]);
  ok(`${lang} page-profile: 503 hele vejen giver tre forsøg og skylder ikke brugerens netværk`,
    dead.calls === 3 && /temporarily unavailable|midlertidigt utilgængelig/.test(dead.out) && !/Could not reach the profiling service|Vi kunne ikke nå profileringstjenesten/.test(dead.out),
    `calls=${dead.calls} out=${dead.out.slice(0, 120)}`);

  const rate = await runProfile(path, [{ status: 429, body: { ok: false, error: 'Too many profiles this hour.' } }]);
  ok(`${lang} page-profile: 429 er endeligt, ét kald, og viser serverens timegrænse`,
    rate.calls === 1 && /Too many profiles this hour/.test(rate.out), `calls=${rate.calls} out=${rate.out}`);

  const bad = await runProfile(path, [{ status: 400, body: { ok: false, error: 'Missing ?url= parameter' } }]);
  ok(`${lang} page-profile: et 4xx er endeligt og viser serverens egen tekst`,
    bad.calls === 1 && /Missing \?url= parameter/.test(bad.out) && !/temporarily unavailable/.test(bad.out), `calls=${bad.calls} out=${bad.out.slice(0, 120)}`);

  const offline = await runProfile(path, [{ reject: 'Failed to fetch' }]);
  ok(`${lang} page-profile: et afbrudt kald prøves igen og får sin egen tekst`,
    offline.calls === 3 && /Check your connection|Tjek din forbindelse/.test(offline.out), `calls=${offline.calls} out=${offline.out.slice(0, 120)}`);
}

// --------------------------------------------------------------------------
// 6. `book-ai.js`: samme klasse igen, på de fem bog-sider der deler filen.
//    Både chatten og den lokale venteliste skal genkalde, og en tabt tilmelding
//    skal kunne prøves igen — knappen bliver derfor aktiv igen.
// --------------------------------------------------------------------------
const OK_ASK = { status: 200, body: { ok: true, answer: 'NIS2 applies from 10 employees or €2m turnover.' } };
const OK_WAIT = { status: 200, body: { ok: true } };

// Sonden ved sidevisning er et GET på samme rute som spørgsmålet. Den skal
// svare «tændt», for det er den tilstand dommene ovenfor måler — og den må ikke
// tælles som et værktøjskald, fordi den ikke er et. Målt 1/10: den lå i rækken
// og spiste det første svar, så «503 hele vejen» så 3 kald i stedet for 2 og
// dommen om to forsøg døde på et svar, der aldrig blev brugt.
const probeSkipped = {
  test: (url, init) => /\/api\/compliance-ai\b/.test(String(url)) && (init?.method || 'GET') === 'GET',
  body: { ok: true, available: true },
};

async function runBook(list, { ask = true, wait = true } = {}) {
  const { fetchImpl, state } = responses(list);
  const { nodes } = loadPage('site/book-ai.js', fetchImpl, { absent: ['baiLead'] });
  nodes.get('baiInput').value = 'Does NIS2 apply to a 5-person agency?';
  nodes.get('baiAsk').click();
  await sleep(40);
  const chat = (nodes.get('baiTopStatus').textContent) || '';
  let lead = '', btnLive = true;
  if (wait) {
    nodes.get('baiEmail').value = 'kontakt@eksempel.dk';
    nodes.get('baiBtn').click();
    await sleep(40);
    lead = (nodes.get('baiStatus').textContent) || '';
    btnLive = nodes.get('baiBtn').disabled === false;
  }
  return { calls: state.calls, chat, lead, btnLive };
}

{
  const r = await runBook([OK_ASK, OK_WAIT]);
  ok('book-ai: et godt svar på chat og venteliste, ét kald hver', r.calls === 2 && r.chat === '' && /on the list/.test(r.lead), `calls=${r.calls} chat=${r.chat} lead=${r.lead}`);
}
{
  const r = await runBook([{ status: 502, html: true }, OK_ASK, OK_WAIT]);
  ok('book-ai: 502 med HTML genkaldes og lykkes', r.calls === 3 && r.chat === '', `calls=${r.calls} chat=${r.chat}`);
  // 3 = ét mislykket spørgsmål (2 forsøg) + ét godt svar på genkaldet + ventelisten.
}
{
  const r = await runBook([{ status: 503, html: true }], { wait: false });
  ok('book-ai: 503 hele vejen giver to forsøg og skylder ikke brugerens netværk',
    r.calls === 2 && /temporarily unavailable/.test(r.chat) && !/Network error/.test(r.chat), `calls=${r.calls} chat=${r.chat}`);
}
{
  const r = await runBook([{ reject: 'Failed to fetch' }], { wait: false });
  ok('book-ai: et afbrudt kald prøves igen og får sin egen tekst',
    r.calls === 2 && /could not reach the assistant server/.test(r.chat) && !/Network error/.test(r.chat), `calls=${r.calls} chat=${r.chat}`);
}
{
  const r = await runBook([OK_ASK, { status: 503, html: true }, OK_WAIT]);
  ok('book-ai: ventelisten genkaldes, så en tilmelding ikke tabes', r.calls === 3 && /on the list/.test(r.lead), `calls=${r.calls} lead=${r.lead}`);
}
{
  const r = await runBook([OK_ASK, { status: 503, html: true }]);
  // Ventelisten er vores egen KV-skrivning uden omkostninger opstrøms, så den
  // beholder tre forsøg selv om spørgsmålet kun får to: 1 (chat) + 3 = 4.
  ok('book-ai: en venteliste der holder op giver en ærlig tekst og fri knap igen',
    r.calls === 4 && /temporarily unavailable/.test(r.lead) && r.btnLive === true, `calls=${r.calls} lead=${r.lead} btn=${r.btnLive}`);
}
{
  const r = await runBook([OK_ASK, { status: 400, body: { ok: false, error: 'That email is already on the list.' } }]);
  ok('book-ai: et 4xx er endeligt og viser serverens egen tekst',
    r.calls === 2 && /already on the list/.test(r.lead) && !/temporarily unavailable/.test(r.lead), `calls=${r.calls} lead=${r.lead}`);
}

// --------------------------------------------------------------------------
// 7. `/compliance-ai` (EN + DA): chatten og ventelisten deler én `postJSON()`.
//    Den blev rettet i 1af9302, men var kun dømt af en grep — her dømmer
//    sandkassen den på samme måde som de fire klienter ovenfor.
// --------------------------------------------------------------------------
// `OK_ASK` og `OK_WAIT` er allerede erklæret ovenfor til book-ai — samme
// svarform, og de skal måles ens.

// Sidens eget script rører også `/api/track`, så den skal findes på sit eget
// kendetegn — målt, ikke antaget: `loadPage`s standardfinder ville ellers ramme
// track-scriptet, der ikke kender `sendQuestion`.
async function runAsk(path, list) {
  const { fetchImpl, state } = responses(list, { skip: [probeSkipped] });
  const { sandbox, nodes } = loadPage(path, fetchImpl, { match: /ASK_MAX_TRIES/ });
  nodes.get('questionInput').value = 'Does NIS2 apply to a 5-person agency?';
  sandbox.sendQuestion();
  await sleep(40);
  return { calls: state.calls, status: nodes.get('chatStatus').textContent || '', btn: nodes.get('sendBtn').disabled };
}

// Kapabilitets-sonden, som kører ved sidevisning og før alt andet. Den er den
// eneste handling på siden når nøglen mangler, så den måles på sit eget:
// `step` er hvad serveren svarer på GET'et, og dommen er hvad der så sker med
// chatten. Uden den var «assistenten er slukket» kun dømt af en grep i
// `tools/check_unavailable_routes.py`, som ikke kan se om sonden *gør* noget.
async function runProbe(path, step) {
  const { fetchImpl } = responses([step]);
  const { sandbox } = loadPage(path, fetchImpl, { match: /ASK_MAX_TRIES/ });
  await sleep(40);
  // Læs elementerne gennem DOM'en, ikke gennem `nodes`: kortet får kun en
  // stub for det siden *selv* nåede at slå op. `#askArea` forsvinder netop i
  // den tilstand dommen måler, så den skal læses som «findes den stadig?».
  const doc = sandbox.document;
  const area = doc.getElementById('askArea');
  const note = doc.getElementById('aiUnavailable');
  return { chatGone: area._removed === true, notice: note.hidden === false };
}

// Ventelisten ligger bag et vellykket svar, så den måles på den samme kørsel.
async function runAskLead(path, list) {
  const { fetchImpl, state } = responses(list, { skip: [probeSkipped] });
  const { sandbox, nodes } = loadPage(path, fetchImpl, { match: /ASK_MAX_TRIES/ });
  nodes.get('questionInput').value = 'Does NIS2 apply to a 5-person agency?';
  sandbox.sendQuestion();
  await sleep(40);
  nodes.get('leadEmail').value = 'kontakt@eksempel.dk';
  nodes.get('leadBtn').click();
  await sleep(40);
  return { calls: state.calls, lead: nodes.get('leadStatus').textContent || '', btnLive: nodes.get('leadBtn').disabled === false };
}

for (const [path, lang] of [['site/compliance-ai.html', 'EN'], ['site/da/compliance-ai.html', 'DA']]) {
  // Kapabilitets-sonden først, fordi den afgør om resten af siden overhovedet
  // kan bruges. Målt 1/10: med nøglen væk var den eneste handling en besøgende
  // fik, og spørgsmålstasten skrev et 503 «AI service not configured» — altså
  // «Contact the site owner» til en kunde på en publiceret side.
  const on = await runProbe(path, { status: 200, body: { ok: true, available: true } });
  ok(`${lang} compliance-ai: en tændt assistent beholder chatten`, on.chatGone === false && on.notice === false,
    `chatGone=${on.chatGone} notice=${on.notice}`);

  const off = await runProbe(path, { status: 200, body: { ok: true, available: false } });
  ok(`${lang} compliance-ai: en slukket assistent fjerner chatten og viser erstatningen`,
    off.chatGone === true && off.notice === true, `chatGone=${off.chatGone} notice=${off.notice}`);

  // Et tjek der fejler er ikke et «nej» — så bliver chatten stående, og et
  // spørgsmål får sit normale svar. Ellers ville en kort netværdsfejl tage
  // siden fra en besøgende hver gang den indlæses.
  const probeBroken = await runProbe(path, { reject: 'Failed to fetch' });
  ok(`${lang} compliance-ai: et tjek der fejler skjuler ikke chatten`,
    probeBroken.chatGone === false && probeBroken.notice === false,
    `chatGone=${probeBroken.chatGone} notice=${probeBroken.notice}`);

  const good = await runAsk(path, [OK_ASK]);
  ok(`${lang} compliance-ai: et godt svar på ét kald og ingen fejltekst`, good.calls === 1 && good.status === '', `calls=${good.calls} status=${good.status}`);

  const busy = await runAsk(path, [{ status: 502, html: true }, OK_ASK]);
  ok(`${lang} compliance-ai: 502 med HTML genkaldes og lykkes`, busy.calls === 2 && busy.status === '', `calls=${busy.calls} status=${busy.status}`);

  const dead = await runAsk(path, [{ status: 503, html: true }]);
  // Spørgsmålet koster penge (OpenRouter), så det har to forsøg: ét plus ét.
  // Tre var en regel kopieret fra de gratis ruter, hvor et tredje forsøg er
  // gratis. Serveren giver den daglige kvote tilbage når upstream-kaldet
  // fejler, så genkaldet koster brugeren ingen kvote — men det er stadig et
  // betalt kald, og ét er nok til ét spørgsmål.
  ok(`${lang} compliance-ai: 503 hele vejen giver to forsøg og skylder ikke brugerens netværk`,
    dead.calls === 2 && /temporarily unavailable|midlertidigt utilgængelig/.test(dead.status) && !/Network error|Netværksfejl/.test(dead.status),
    `calls=${dead.calls} status=${dead.status}`);

  // 429 er endeligt, og her er det dobbelt vigtigt: serverens egen kvota
  // (20 spørgsmål om dagen) tæller et genkald som et forbrugt spørgsmål. Tre
  // forsøg på ét spørgsmål brændte tre af de tyve, før brugeren overhovedet
  // havde fået et svar.
  const rate = await runAsk(path, [{ status: 429, body: { ok: false, error: 'Too many questions this hour.' } }]);
  ok(`${lang} compliance-ai: 429 er endeligt, ét kald, og viser serverens timegrænse`,
    rate.calls === 1 && /Too many questions this hour/.test(rate.status), `calls=${rate.calls} status=${rate.status}`);

  const bad = await runAsk(path, [{ status: 400, body: { ok: false, error: 'That question is too short.' } }]);
  ok(`${lang} compliance-ai: et 4xx er endeligt og viser serverens egen tekst`,
    bad.calls === 1 && bad.status === 'That question is too short.', `calls=${bad.calls} status=${bad.status}`);

  const offline = await runAsk(path, [{ reject: 'Failed to fetch' }]);
  ok(`${lang} compliance-ai: et afbrudt kald prøves igen og får sin egen tekst`,
    offline.calls === 2 && /could not reach the assistant server|kunne ikke nå assistentserveren/.test(offline.status) && !/Network error|Netværksfejl/.test(offline.status),
    `calls=${offline.calls} status=${offline.status}`);

  // Knappen må ikke blive låst af et blip — ellers kan en bruger ikke prøve igen.
  ok(`${lang} compliance-ai: knappen bliver aktiv igen efter en fejl`, dead.btn === false, `disabled=${dead.btn}`);

  // Ventelisten: en tabt tilmelding er en tabt tilmelding.
  const lGood = await runAskLead(path, [OK_ASK, OK_WAIT]);
  ok(`${lang} compliance-ai: ventelisten kvitterer på ét kald`, lGood.calls === 2 && /on the list|på listen/i.test(lGood.lead), `calls=${lGood.calls} lead=${lGood.lead}`);

  const lBlip = await runAskLead(path, [OK_ASK, { status: 502, html: true }, OK_WAIT]);
  ok(`${lang} compliance-ai: ventelisten genkaldes, så en tilmelding ikke tabes`, lBlip.calls === 3 && /on the list|på listen/i.test(lBlip.lead), `calls=${lBlip.calls} lead=${lBlip.lead}`);

  const lDead = await runAskLead(path, [OK_ASK, { status: 503, html: true }]);
  ok(`${lang} compliance-ai: en venteliste der holder op giver en ærlig tekst og fri knap igen`,
    lDead.calls === 4 && /temporarily unavailable|midlertidigt utilgængelig/.test(lDead.lead) && lDead.btnLive === true,
    `calls=${lDead.calls} lead=${lDead.lead} btn=${lDead.btnLive}`);

  const lBad = await runAskLead(path, [OK_ASK, { status: 400, body: { ok: false, error: 'That address is already on the list.' } }]);
  ok(`${lang} compliance-ai: ventelistens 4xx er endeligt og viser serverens tekst`,
    lBad.calls === 2 && /already on the list/.test(lBad.lead) && !/temporarily unavailable|midlertidigt utilgængelig/.test(lBad.lead),
    `calls=${lBad.calls} lead=${lBad.lead}`);
}

// --------------------------------------------------------------------------
// 8. `/security-headers-check`: samme klasse, og den var den værste af dem alle,
//    fordi den skrev den rå JavaScript-fejl `Unexpected token '<'` i
//    brugerens ansigt. Den har heller ingen egen footer at hænge noget i, så
//    den behøver ingen særlig sandkasse — målt, ikke antaget.
//    Siden kører selv et tjek ved sidevisning (`setTimeout(check, 300)`), og
//    `loadPage`s stub starter med `value: ''`, så det tjek falder på "Please
//    enter a URL." og bruger **intet** svar fra listen. Målingen kan derfor
//    bare tælle `/api/header-check`-kaldene; beacon'en på `/api/track` er
//    ikke en del af det vi dømmer. Skulle siden en dag begynde at køre sit
//    tjek med en URL i `value`, ville tællingen se den med, og kontrollerne
//    ville blive røde — altså kan vi højst fejle på den vej.
// --------------------------------------------------------------------------
const OK_HEADERS = { status: 200, body: { ok: true, status: 200, statusText: 'OK', finalUrl: 'https://example.com', redirected: false, headers: { 'strict-transport-security': 'max-age=63072000', 'content-security-policy': "default-src 'self'", 'x-frame-options': 'DENY', 'x-content-type-options': 'nosniff' } } };

// Samme grund som `runInspect`: siden kører sit `value=`-URL ved sidevisning
// (`setTimeout(check, 300)`), så det første svar er til den og klikket får det
// næste.
async function runHeaders(list) {
  const { fetchImpl, state } = responses([OK_HEADERS, ...list], { skip: [/api\/track/] });
  const { nodes } = loadPage('site/security-headers-check.html', fetchImpl, { match: /HEADERS_MAX_TRIES/ });
  await sleep(30);
  const base = state.urls.length;
  nodes.get('urlInput').value = 'example.com';
  nodes.get('checkBtn').click();
  await sleep(40);
  return { calls: state.urls.slice(base).filter((u) => u.includes('/api/header-check')).length, status: nodes.get('statusBox').textContent || '' };
}

{
  const r = await runHeaders([OK_HEADERS]);
  ok('security-headers-check: et godt svar renderer på ét kald', r.calls === 1 && !/temporarily unavailable|Network error/.test(r.status), `calls=${r.calls} status=${r.status}`);
}
{
  const r = await runHeaders([{ status: 502, html: true }, OK_HEADERS]);
  ok('security-headers-check: 502 med HTML genkaldes og lykkes', r.calls === 2 && !/temporarily unavailable/.test(r.status), `calls=${r.calls} status=${r.status}`);
}
{
  const r = await runHeaders([{ status: 503, html: true }]);
  ok('security-headers-check: 503 hele vejen giver tre forsøg og skylder ikke brugerens netværk',
    r.calls === 3 && /temporarily unavailable/.test(r.status) && !/Network error/.test(r.status), `calls=${r.calls} status=${r.status}`);
}
{
  // Den rå fejltekst, der slap ud på den gamle side. Den skal aldrig komme tilbage.
  const r = await runHeaders([{ status: 503, html: true }]);
  ok("security-headers-check: den rå `Unexpected token '<'` vises aldrig", !/Unexpected token/.test(r.status), r.status);
}
{
  const r = await runHeaders([{ reject: 'Failed to fetch' }]);
  ok('security-headers-check: et afbrudt kald prøves igen og får sin egen tekst',
    r.calls === 3 && /could not reach the header server/.test(r.status) && !/Network error/.test(r.status), `calls=${r.calls} status=${r.status}`);
}
{
  const r = await runHeaders([{ status: 400, body: { ok: false, error: 'Not a valid URL.' } }]);
  ok('security-headers-check: et 4xx er endeligt og viser serverens egen tekst',
    r.calls === 1 && r.status === 'Not a valid URL.', `calls=${r.calls} status=${r.status}`);
}
{
  // 429 er endeligt: serveren har sagt hvor længe det varer, og tælleren er
  // læserens egen timekvote. Genkaldene brugte resten af den på svar serveren
  // allerede har afslået at give.
  const r = await runHeaders([{ status: 429, body: { ok: false, error: 'Too many checks this hour.' } }]);
  ok('security-headers-check: 429 er endeligt, ét kald, og viser serverens egen tekst',
    r.calls === 1 && /Too many checks this hour/.test(r.status), `calls=${r.calls} status=${r.status}`);
}
{
  // 200 med `ok:false` er et rigtigt svar, ikke et blip — ét kald, serverens tekst.
  const r = await runHeaders([{ status: 200, body: { ok: false, error: 'Could not fetch that host.' } }]);
  ok('security-headers-check: 200 med ok:false er endeligt, ét kald',
    r.calls === 1 && /Could not fetch that host/.test(r.status), `calls=${r.calls} status=${r.status}`);
}

// --------------------------------------------------------------------------
// 9. Mutationer af *læseren*, så kontrollerne ovenfor ikke er en grøn cirkel.
//    Hver mutation skal gøre den navngivne kontrol rød.
//    --------------------------------------------------------------------------
{
  const book = readFileSync(join(root, 'site/book-ai.js'), 'utf8');
  const net = readFileSync(join(root, 'site/net.js'), 'utf8');
  ok('mutation: book-ai har samme regel som de andre klienter', /BOOK_MAX_TRIES = 2/.test(book));
  // Ratchet på den delte regel: 429 må *ikke* stå på genkaldssiden igen. Den
  // lå der før, og da CEO-køet fangede den, var det fordi den brugte læserens
  // egen kvote på svar serveren allerede havde afslået.
  ok('mutation: bogen læser status før JSON, og 429 er endeligt', /err\.transient = !data \|\| res\.status >= 500/.test(net));
  // Målt 30/9 af review: ratcheten læste kun net.js, så at sætte
  // `r.status === 429` tilbage i security-headers-check eller de to
  // compliance-site-check-kopier ville være grønt. Den skal måle hele korpus.
  // grep giver exit 1 når der ikke er fund — det er det forventede svar her,
  // ikke en fejl, så den sluges frem for at dræbe porten.
  let retried429 = [];
  try {
    retried429 = execFileSync('grep', ['-rlE', 'transient *= *[^\\n]*=== *429', 'site'], { cwd: root, stdio: ['ignore', 'pipe', 'ignore'] })
      .toString('utf8').split('\n').filter(Boolean);
  } catch (e) { retried429 = (e.stdout || '').toString('utf8').split('\n').filter(Boolean); }
  ok('mutation: ingen klient i site/ genkaller en 429', retried429.length === 0, retried429.join(', '));
  for (const p of ['site/page-profile.html', 'site/da/page-profile.html']) {
    const src = readFileSync(join(root, p), 'utf8');
    ok(`mutation: ${p} har samme regel`, /PROFILE_MAX_TRIES = 3/.test(src) && /err\.transient = !j \|\| r\.status >= 500/.test(src));
  }
  // Ingen site-fil må have sin egen postJSON igen — de deler /net.js.
  for (const p of ['site/book-ai.js', 'site/compliance-ai.html', 'site/da/compliance-ai.html',
                   'site/security-headers-check.html', 'site/compliance-site-check.html',
                   'site/da/compliance-site-check.html', 'site/page-profile.html', 'site/da/page-profile.html',
                   'site/url-inspector/index.html']) {
    const src = readFileSync(join(root, p), 'utf8');
    ok(`mutation: ${p} bruger den delte postJSON`, !/function postJSON/.test(src), 'egen postJSON');
  }
}
{
  // Genkalder vi slået fra i book-ai, skal "503 hele vejen giver tre forsøg" blive rød.
  const src = readFileSync(join(root, 'site/book-ai.js'), 'utf8').replace('var BOOK_MAX_TRIES = 2;', 'var BOOK_MAX_TRIES = 1;');
  ok('mutation: slået genkald kan fremstilles i book-ai', src.includes('var BOOK_MAX_TRIES = 1;'));
  const { fetchImpl, state } = responses([{ status: 503, html: true }]);
  const nodes = new Map();
  const footer = el();
  footer.parentNode = { insertBefore() {} };
  const sandbox = { console, setTimeout: fastTimeout, Promise, Error, JSON, Object, Array, String, Number, Boolean, RegExp, encodeURIComponent,
    fetch: fetchImpl, navigator: { doNotTrack: '0' }, location: { pathname: '/x.html' },
    document: { getElementById(id) { if (!nodes.has(id)) nodes.set(id, el()); return nodes.get(id); },
      querySelector: () => footer, createElement: () => el(), head: el(), body: el(), addEventListener() {} } };
  sandbox.window = sandbox; sandbox.globalThis = sandbox;
  vm.createContext(sandbox);
  vm.runInContext(netOverride ?? readFileSync(join(root, 'site/net.js'), 'utf8'), sandbox, { filename: 'site/net.js' });
  vm.runInContext(src, sandbox, { filename: 'site/book-ai.js' });
  nodes.get('baiInput').value = 'Does NIS2 apply?';
  nodes.get('baiAsk').click();
  await sleep(30);
  ok('mutation: uden genkald bliver bogsiden rød', state.calls === 1, `calls=${state.calls} (forventet 3)`);
}

// --------------------------------------------------------------------------
function mutated(path, from, to) {
  const html = readFileSync(join(root, path), 'utf8');
  if (!html.includes(from)) return null;
  return html.replace(from, to);
}
{
  const src = readFileSync(join(root, 'site/compliance-site-check.html'), 'utf8');
  ok('mutation: en klient uden status-first findes i korpus', /r\.json\(\)\.catch/.test(src), 'genkaldskæden er væk');
  ok('mutation: 503-grænsen er en konstant, ikke et hærdet tal', /SCAN_MAX_TRIES = 3/.test(src));
  ok('mutation: url-inspector har samme regel', /INSPECT_MAX_TRIES = 3/.test(readFileSync(join(root, 'site/url-inspector/index.html'), 'utf8')));
  ok('mutation: DA-siden har samme regel', /SCAN_MAX_TRIES = 3/.test(readFileSync(join(root, 'site/da/compliance-site-check.html'), 'utf8')));
}
{
  // Retter vi genkaldet væk, skal "503 hele vejen giver tre forsøg" blive rød.
  const m = mutated('site/compliance-site-check.html', 'var SCAN_MAX_TRIES = 3;', 'var SCAN_MAX_TRIES = 1;');
  ok('mutation: slået genkald kan fremstilles', m !== null);
  if (m) {
    const { fetchImpl, state } = responses([{ status: 503, html: true }]);
    const html = m;
    const scripts = [...html.matchAll(/<script(?![^>]*\bsrc=)[^>]*>([\s\S]*?)<\/script>/g)].map((x) => x[1]);
    const main = scripts.find((s) => /fetchScan/.test(s));
    const nodes = new Map();
    const sandbox = { console, setTimeout, URL, Promise, Error, JSON, encodeURIComponent, fetch: fetchImpl,
      document: { getElementById(id) { if (!nodes.has(id)) nodes.set(id, el()); return nodes.get(id); } },
      navigator: { doNotTrack: '0' }, location: { pathname: '/x.html' } };
    sandbox.window = sandbox; sandbox.globalThis = sandbox;
    vm.createContext(sandbox); vm.runInContext(main, sandbox);
    nodes.get('urlInput').value = 'example.com';
    await sandbox.scan();
    await new Promise((r) => setTimeout(r, 20));
    ok('mutation: uden genkald bliver kontrollen rød', state.calls === 1, `calls=${state.calls} (forventet 3)`);
  }
}
{
  // Den anden halvdel af den gamle fejl: at et forbigående svar blev meldt som
  // "Network error". Sætter vi beskeden tilbage og gør 5xx endeligt, skal både
  // genkaldskontrollen og tekstkontrollen blive røde.
  let m = readFileSync(join(root, 'site/compliance-site-check.html'), 'utf8');
  m = m.replace('err.transient = !data || r.status >= 500;', 'err.transient = false;')
       .replace("fejl.push({ url: target, error: err.transport ? OFFLINE : (err.transient ? SERVER_BUSY : (err.message || 'Scan failed')) });",
                "fejl.push({ url: target, error: 'Network error: ' + (err.message || 'unknown') });");
  ok('mutation: den gamle behandling kan fremstilles', /Network error: ' \+ \(err\.message/.test(m) && /err\.transient = false;/.test(m));
  if (m) {
    const { fetchImpl, state } = responses([{ status: 502, html: true }]);
    const scripts = [...m.matchAll(/<script(?![^>]*\bsrc=)(?![^>]*ld\+json)[^>]*>([\s\S]*?)<\/script>/g)].map((x) => x[1]);
    const main = scripts.find((s) => /fetchScan/.test(s));
    const nodes = new Map();
    const sandbox = { console, setTimeout: fastTimeout, URL, Promise, Error, JSON, encodeURIComponent, scrollTo() {},
      fetch: fetchImpl, navigator: { doNotTrack: '0' }, location: { pathname: '/x.html' },
      document: { getElementById(id) { if (!nodes.has(id)) nodes.set(id, el()); return nodes.get(id); },
        createElement: () => el(), createTextNode: (t) => ({ textContent: t }), body: el(), addEventListener() {} } };
    sandbox.window = sandbox; sandbox.globalThis = sandbox;
    vm.createContext(sandbox); vm.runInContext(main, sandbox);
    nodes.get('urlInput').value = 'example.com';
    await sandbox.scan();
    await sleep(30);
    const err = nodes.get('errorBox').textContent || '';
    ok('mutation: gamle kode kalder det en netværksfejl', state.calls === 1 && /Network error/.test(err), `calls=${state.calls} err=${err}`);
  }
}

// --------------------------------------------------------------------------
// 10. Den vigtigste mutation: den *gamle kode*, hentet fra git og kørt gennem
//     samme sandkasse. En hærdet konstant beviser kun at porten kan fremstille
//     en tilstand; den beviser ikke at den gamle fejl ville være dømt rød.
// --------------------------------------------------------------------------
{
  const old = execFileSync('git', ['show', '1af9302^:site/compliance-ai.html'], { cwd: root, maxBuffer: 1 << 26 }).toString('utf8');
  const main = [...old.matchAll(/<script(?![^>]*\bsrc=)(?![^>]*ld\+json)[^>]*>([\s\S]*?)<\/script>/g)].map((m) => m[1]).find((s) => /api\/compliance-ai/.test(s));
  ok('mutation: den gamle compliance-ai-kode kan hentes fra git', !!main);
  const { fetchImpl, state } = responses([{ status: 503, html: true }]);
  const nodes = new Map();
  const sandbox = { console, setTimeout: fastTimeout, clearTimeout, URL, Promise, Error, JSON, Object, Array, String, Number, Boolean, RegExp, encodeURIComponent, Blob,
    fetch: fetchImpl, navigator: { doNotTrack: '0' }, location: { pathname: '/compliance-ai.html' },
    document: { getElementById(id) { if (!nodes.has(id)) nodes.set(id, el()); return nodes.get(id); },
      createElement: () => el(), createTextNode: (t) => ({ textContent: t }), querySelectorAll: () => [], addEventListener() {}, body: el() } };
  sandbox.window = sandbox; sandbox.globalThis = sandbox;
  vm.createContext(sandbox); vm.runInContext(main, sandbox, { filename: 'old-compliance-ai.html' });
  nodes.get('questionInput').value = 'Does NIS2 apply?';
  sandbox.sendQuestion();
  await sleep(30);
  const status = nodes.get('chatStatus').textContent || '';
  ok('mutation: den gamle kode giver op efter ét forsøg', state.calls === 1, `calls=${state.calls} (forventet 3)`);
  ok('mutation: den gamle kode kalder vores 5xx en netværksfejl', /Network error/.test(status), status);
}
{
  const old = execFileSync('git', ['show', '1af9302^:site/security-headers-check.html'], { cwd: root, maxBuffer: 1 << 26 }).toString('utf8');
  const main = [...old.matchAll(/<script(?![^>]*\bsrc=)(?![^>]*ld\+json)[^>]*>([\s\S]*?)<\/script>/g)].map((m) => m[1]).find((s) => /header-check/.test(s));
  ok('mutation: den gamle security-headers-check-kode kan hentes fra git', !!main);
  const { fetchImpl, state } = responses([{ status: 503, html: true }]);
  const nodes = new Map();
  const sandbox = { console, setTimeout: fastTimeout, clearTimeout, URL, Promise, Error, JSON, Object, Array, String, Number, Boolean, RegExp, encodeURIComponent,
    fetch: fetchImpl, navigator: { doNotTrack: '0' }, location: { pathname: '/security-headers-check.html' },
    document: { getElementById(id) { if (!nodes.has(id)) nodes.set(id, el()); return nodes.get(id); },
      createElement: () => el(), querySelectorAll: () => [], addEventListener() {}, body: el() } };
  sandbox.window = sandbox; sandbox.globalThis = sandbox;
  vm.createContext(sandbox); vm.runInContext(main, sandbox, { filename: 'old-security-headers-check.html' });
  await sleep(30);
  const base = state.calls;
  nodes.get('urlInput').value = 'example.com';
  nodes.get('checkBtn').click();
  await sleep(30);
  const status = nodes.get('statusBox').textContent || '';
  ok('mutation: den gamle header-tjekker giver op efter ét forsøg', state.calls - base === 1, `calls=${state.calls - base} (forventet 3)`);
  ok("mutation: den gamle header-tjekker viser den rå `Unexpected token '<'`", /Unexpected token/.test(status), status);
}

// --------------------------------------------------------------------------
// 10. Én implementering. `postJSON` lå inline i tre filer, og DA-kopien havde
//     allerede drejet en enkelt streng. Nu ligger reglen i `/net.js`, og de tre
//     klienter skal bevise at de læser den — ikke at de hver har en kopi.
//     Beviset er mutationen: gør vi `/net.js` forkert, skal alle tre blive røde
//     på samme kontrol. Havde de haft hver sin kopi, ville de være grønne.
// --------------------------------------------------------------------------
{
  const net = readFileSync(join(root, 'site/net.js'), 'utf8');
  ok('net.js: reglen ligger et sted — status læses før kroppen',
    /res\.json\(\)\.catch/.test(net) && /err\.transient = !data \|\| res\.status >= 500/.test(net));
  // Ingen `site/`-fil må have sin egen `postJSON` igen. Vælger den at inline
  // hjælperen en tredje gang, skal det kunne ses her, ikke i en diff om et halvt
  // år. Målt over hele træet, ikke kun de tre kendte filer.
  const own = execFileSync('grep', ['-rl', 'function postJSON', 'site'], { cwd: root }).toString('utf8')
    .split('\n').filter((f) => f && f !== 'site/net.js');
  ok('net.js: ingen site-fil definerer sin egen postJSON', own.length === 0, own.join(', '));
  for (const p of ['site/compliance-ai.html', 'site/da/compliance-ai.html', 'site/book-ai.js']) {
    const src = readFileSync(join(root, p), 'utf8');
    ok(`net.js: ${p} læser den delte regel i stedet for at kopiere den`,
      /NET\.ask\(/.test(src) && !/function postJSON/.test(src));
  }
  for (const p of ['site/compliance-ai.html', 'site/da/compliance-ai.html',
    'site/books/gdpr-for-agencies.html', 'site/books/nis2-for-agencies.html',
    'site/books/eaa-checklist.html', 'site/books/eaa-shopify.html', 'site/books/cookie-consent-guide.html']) {
    const src = readFileSync(join(root, p), 'utf8');
    ok(`net.js: ${p} indlæser den`, /<script defer src="\/net\.js"><\/script>/.test(src));
  }
}
{
  // 5xx endeligt i den delte hjælper: alle tre klienter mister genkaldet paa én
  // gang. Tre røde kontroller i stedet for tre kopier der kan drive fra hinanden.
  const good = readFileSync(join(root, 'site/net.js'), 'utf8');
  const broken = good.replace('err.transient = !data || res.status >= 500;', 'err.transient = false;');
  ok('mutation: den delte regel kan gøres forkert', broken !== good);
  netOverride = broken;
  try {
    const r = await runBook([{ status: 503, html: true }], { wait: false });
    ok('mutation: bogsiden læser /net.js, så den følger med ned', r.calls === 1, `calls=${r.calls} (forventet 3)`);
  } finally { netOverride = null; }
  netOverride = broken;
  try {
    for (const p of ['site/compliance-ai.html', 'site/da/compliance-ai.html']) {
      const r = await runAsk(p, [{ status: 503, html: true }]);
      ok(`mutation: ${p} læser /net.js, så den følger med ned`, r.calls === 1, `calls=${r.calls} (forventet 3)`);
    }
  } finally { netOverride = null; }
}

// --------------------------------------------------------------------------
// 11. Den betalte vej i *resultatet* (EN + DA).
//
//     `/compliance-site-check` er den gratis indgang til EUComply Pro — det
//     dyreste produkt i katalogen ($79/år pr. website). Målt 1/10 på live:
//     0 `buy.stripe.com` på hele siden, og det eneste økonomiske opfordring
//     efter et resultat var en donation på 10 kr. Betalt vej fandtes kun som et
//     statisk afsnit *under* værktøjet, altså uden for rækkevidde for den der
//     lige har brugt scanneren. Sådan så det ud, og det er det her dommen er
//     skrevet til: den kører et scan rigtigt igennem og læser den markup der
//     lander i `#results`.
//
//     Dommen læser katalogen for købslink, pris og periode, så den kan ikke
//     grønne en knap der peger på en anden produktrappe eller en pris uden
//     periode. Mutationen kører den samme dom på den kode fra før rettelsen.
// --------------------------------------------------------------------------
{
  const catalog = JSON.parse(readFileSync(join(root, 'tools/stripe_catalog.json'), 'utf8'));
  const pro = catalog.products['eucomply-pro'];
  const periodWords = catalog.billing_periods.products['eucomply-pro']
    .flatMap((k) => catalog.billing_periods.words[k]);

  // Købsknappen skal findes i den markup resultatet renderer — ikke i filens
  // statiske HTML. Derfor strippes `<style>` og `<script>` væk, og det dømmes
  // at linket *kun* findes i scriptet: ellers ville et statisk afsnit kunne
  // bestå dommen, og det er præcis den fejlform der var i live.
  const outsideScripts = (src) => src
    .replace(/<style[\s\S]*?<\/style>/g, ' ')
    .replace(/<script[\s\S]*?<\/script>/g, ' ');

  const døm = (html, label, reportHref) => {
    ok(`${label}: købsknappen i resultatet bruger katalogens betalingslink`,
      html.includes(pro.payment_link), `ledger ${pro.payment_link} i ${html.includes(pro.payment_link) ? '' : 'resultatet'}`);
    ok(`${label}: knappen viser prisen fra katalogen ($${pro.price_usd})`,
      html.includes(`$${pro.price_usd}`));
    ok(`${label}: knappen siger hvilken periode den sælger`,
      periodWords.some((w) => html.includes(w)), periodWords.join(', '));
    ok(`${label}: knappen sælger den rigtige produktrappe`,
      /EUComply Pro/.test(html));
    ok(`${label}: resultatet linker videre til produktsiden med gratis-vs-Pro-tabellen`,
      reportHref.test(html), `${reportHref}`);
  };

  for (const [path, label, reportHref] of [
    ['site/compliance-site-check.html', 'EN', /href="\/compliance-report"/],
    ['site/da/compliance-site-check.html', 'DA', /href="\/da\/compliance-report"/],
  ]) {
    const { fetchImpl } = responses([OK_SCAN]);
    const { sandbox, nodes } = loadPage(path, fetchImpl);
    nodes.get('urlInput').value = 'example.com';
    await sandbox.scan();
    await sleep(30);
    const html = (nodes.get('results') || {}).innerHTML || '';
    ok(`${label}: et gennemført scan renderer resultat-markup`, html.length > 0);
    døm(html, `${label} live`, reportHref);
    // Donationslinjen skal stadig være der — den nye boks er en tilføjelse.
    ok(`${label}: donationslinjen overlevede den nye boks`, /donate\.stripe\.com/.test(html));

    const src = readFileSync(join(root, path), 'utf8');
    ok(`${label}: købslinket står ikke i den statiske HTML — kun i resultatstien`,
      !outsideScripts(src).includes(pro.payment_link));

    // Mutation: den kode fra før rettelsen skal være rød på dommen.
    const old = execFileSync('git', ['show', `da3999e:${path}`], { cwd: root, maxBuffer: 1 << 26 }).toString('utf8');
    ok(`${label}: den gamle side kan hentes fra git`, old.length > 0);
    const { fetchImpl: oldFetch } = responses([OK_SCAN]);
    const gammel = loadPage(path, oldFetch, { source: old });
    gammel.nodes.get('urlInput').value = 'example.com';
    await gammel.sandbox.scan();
    await sleep(30);
    const gammelHtml = (gammel.nodes.get('results') || {}).innerHTML || '';
    ok(`${label}: mutation: den gamle kode har ingen købsvej i resultatet`,
      !gammelHtml.includes(pro.payment_link), 'dommen kan altså blive rød');
  }
}

// --------------------------------------------------------------------------
// 11b. Samme betalte vej på de fem øvrige værktøjer, der sælger EUComply Pro
//      eller Page Profile Pro. Målt 1/10 på live: de otte sider havde 0
//      `buy.stripe.com` hver, altså ingen købsvej i resultatet overhovedet —
//      kun et statisk afsnit under værktøjet og en donation på 10 kr.
//
//      Dommen kører hvert værktøj *rigtigt* igennem i sandkassen og læser den
//      markup resultatet renderer, ligesom sektion 11 gør for scanneren. Den
//      bruger den konkrete købsknap til sit værktøj, fordi de to ikke sælger
//      det samme: `/url-inspector` sælger Page Profile Pro ($19/år — det er
//      også den produktrappe dens eget afsnit peger på), de fire andre sælger
//      EUComply Pro ($79/år pr. website).
//
//      Hver købsknap skal have pris **og** periode fra katalogen, ellers kan en
//      knap med `$19` på sigende sælge et årssubscription.
// --------------------------------------------------------------------------
{
  const catalog = JSON.parse(readFileSync(join(root, 'tools/stripe_catalog.json'), 'utf8'));
  const priceOf = (key) => catalog.products[key].price_usd;
  const periodWordsOf = (key) => catalog.billing_periods.products[key]
    .flatMap((k) => catalog.billing_periods.words[k]);

  const outsideScripts = (src) => src
    .replace(/<style[\s\S]*?<\/style>/g, ' ')
    .replace(/<script[\s\S]*?<\/script>/g, ' ');

  // Cookie-tjekket læser kildedokumentet, så svaret skal have `html`.
  const OK_COOKIE = { status: 200, body: { ok: true, url: 'https://example.com', html: '<html><body>gtag("consent","default")</body></html>' } };
  // `/scan` henter gennem `/scan-proxy`, som svarer med `{ ok, html }` — ikke
  // med en rapport som `/compliance-site-check` gør.
  const OK_SCAN_PROXY = { status: 200, body: { ok: true, url: 'https://example.com', html: '<html lang="en"><head><title>Example</title></head><body><h1>Example</h1></body></html>' } };

  // Siderne har to forskellige former for den samme boks. Nogle bygger den i
  // `innerHTML` som en del af resultat-markuppen — den findes kun i scriptet.
  // Andre har den som statisk markup med `hidden`, som scriptet fjerner i det
  // øjeblik et resultat skrives; den ligger altså i *filen*, og dommen læser
  // den derfra og dømmer synligheden for sig selv. En tredje form ville være en
  // boks der findes i markup uden at nogen kode nogensinde afslører den, og
  // `afsløret` er derfor en del af dommen, ikke en kommentar.
  const statisk = (src, id) => {
    const m = src.match(new RegExp(`<div id="${id}"[\\s\\S]*?</div>\\s*</div>`));
    return m ? m[0] : '';
  };

  // Hvert værktøj: fil, label, produktrappe, rapport-side og en `kør`-funktion
  // der returnerer `{ markup, donation, afsløret }` — den markup købsknappen
  // ligger i, den donationslinje der står ved siden af den, og om koden rent
  // faktisk viste boksen. Donationslinjen er sit eget felt, fordi den ligger
  // uden for boksen på nogle sider (`#shc-donate`) og inde i den på andre.
  const TOOLS = [
    {
      path: 'site/cookie-check.html', label: 'cookie-check EN', product: 'eucomply-pro',
      report: /href="\/compliance-report"/, form: 'script',
      async kør() {
        const { fetchImpl } = responses([OK_COOKIE]);
        const { sandbox, nodes } = loadPage('site/cookie-check.html', fetchImpl, { match: /scan-proxy/ });
        await sandbox.scan('https://example.com');
        await sleep(30);
        const html = (nodes.get('result') || {}).innerHTML || '';
        const m = /donate\.stripe\.com/.exec(html);
        return { markup: m ? html.slice(0, m.index) : html, donation: html, afsløret: true };
      },
    },
    {
      path: 'site/cookie-check-da.html', label: 'cookie-check DA', product: 'eucomply-pro',
      report: /href="\/da\/compliance-report"/, form: 'script',
      async kør() {
        const { fetchImpl } = responses([OK_COOKIE]);
        const { sandbox, nodes } = loadPage('site/cookie-check-da.html', fetchImpl, { match: /scan-proxy/ });
        await sandbox.scan('https://example.com');
        await sleep(30);
        return { markup: (nodes.get('result') || {}).innerHTML || '', afsløret: true,
                 donation: (nodes.get('result') || {}).innerHTML || '' };
      },
    },
    {
      path: 'site/text-on-image-checker.html', label: 'text-on-image EN', product: 'eucomply-pro',
      report: /href="\/compliance-report"/, form: 'script',
      // Værktøjet indlæser en demo-baggrund ved sidevisning, så resultatet
      // skrives uden et netværkskald. Sandkassen får et læse-canvas, så
      // `sampleContrast()` faktisk måler noget og skriver sin markup.
      async kør() {
        const { nodes } = loadPage('site/text-on-image-checker.html', responses([OK_COOKIE]).fetchImpl,
          { match: /sampleContrast/, canvas: true });
        await sleep(30);
        return { markup: (nodes.get('result') || {}).innerHTML || '', afsløret: true,
                 donation: (nodes.get('result') || {}).innerHTML || '' };
      },
    },
    {
      path: 'site/security-headers-check.html', label: 'security-headers-check', product: 'eucomply-pro',
      report: /href="\/compliance-report"/, form: 'statisk', id: 'shc-pro',
      async kør() {
        const { nodes } = loadPage('site/security-headers-check.html', responses([OK_HEADERS]).fetchImpl,
          { match: /HEADERS_MAX_TRIES/ });
        await sleep(30);
        nodes.get('checkBtn').click();
        await sleep(40);
        // `|| {}` overalt: et element koden aldrig rørte skal give en *rød dom*,
        // ikke et `TypeError`. En mutation der crasher er ikke en dom — den er
        // en fejl, og en port der dør med en undtagelse dømmer ingen fejl.
        return { markup: statisk(readFileSync(join(root, 'site/security-headers-check.html'), 'utf8'), 'shc-pro'),
                 donation: (nodes.get('shc-donate') || {}).innerHTML || '',
                 afsløret: (nodes.get('shc-pro') || {}).hidden === false };
      },
    },
    {
      path: 'site/contrast-checker.html', label: 'contrast-checker EN', product: 'eucomply-pro',
      report: /href="\/compliance-report"/, form: 'statisk', id: 'cc-pro',
      async kør() {
        const { nodes } = loadPage('site/contrast-checker.html', responses([OK_COOKIE]).fetchImpl, { match: /parseHex/ });
        await sleep(30);
        return { markup: statisk(readFileSync(join(root, 'site/contrast-checker.html'), 'utf8'), 'cc-pro'),
                 // Værktøjet kører udelukkende i browseren og beder ikke om
                 // penge, så den har aldrig haft en donationslinje. Dommen
                 // kræver derfor kun at den *kunne* være der — en ny boks må
                 // ikke have fjernet en linje der fandtes før.
                 donation: '', afsløret: (nodes.get('cc-pro') || {}).hidden === false };
      },
    },
    {
      path: 'site/clean-copy-tool.html', label: 'clean-copy-tool', product: 'clean-copy-pro',
      // Tabellen med gratis-vs-Pro ligger på siden selv, så kortet peger på
      // den med et anker — de andre værktøjer peger på en produktside i stedet.
      report: /href="#free-vs-pro"/, form: 'script',
      async kør() {
        const { fetchImpl } = responses([{ status: 200, body: { ok: true } }], { skip: [/api\/track/] });
        // `match` vælger den IIFE der både konverterer og holder Pro-logikken.
        const { nodes } = loadPage('site/clean-copy-tool.html', fetchImpl, { match: /batch-details/ });
        await sleep(30);
        // Ren tekst uden markup: konverteringen så den virker i en rigtig browser
        // tager den `raw.replace`-gren, som hverken skal bruge DOMParser eller
        // CleanCopyCore — de to er `src`-scripts sandkassen ikke indlæser.
        nodes.get('input-box').value = 'Revenue grew 34% — see  the  full report.';
        nodes.get('input-box').fire('input');
        await sleep(20);
        return { markup: (nodes.get('pro-nudge') || {}).innerHTML || '',
                 afsløret: (nodes.get('pro-nudge') || {}).hidden === false };
      },
    },
    {
      // `/scan` (EN + DA) er det mest linkede værktøj på sitet — 290 indgående
      // links målt 1/10 — og det var det eneste gratis EAA-tjek, hvis resultat
      // ikke solgte. Det endte i en donationslinje, selv om samme produktrappe
      // sælger i resultatet på de seks søskendeværktøjer ovenfor. Sandkassen
      // får en minimal `DOMParser`, fordi siden selv parserer det hentede HTML
      // og derefter skriver hele resultat-markuppen i én `innerHTML`.
      path: 'site/scan.html', label: 'scan EN', product: 'eucomply-pro',
      report: /href="\/compliance-report"/, form: 'script',
      async kør() {
        const { fetchImpl } = responses([OK_SCAN_PROXY]);
        const { sandbox, nodes } = loadPage('site/scan.html', fetchImpl, { match: /scan-proxy/ });
        await sandbox.scan('https://example.com');
        await sleep(30);
        const html = (nodes.get('result') || {}).innerHTML || '';
        return { markup: html, donation: html, afsløret: true };
      },
    },
    {
      path: 'site/scan-da.html', label: 'scan DA', product: 'eucomply-pro',
      report: /href="\/da\/compliance-report"/, form: 'script',
      async kør() {
        const { fetchImpl } = responses([OK_SCAN_PROXY]);
        const { sandbox, nodes } = loadPage('site/scan-da.html', fetchImpl, { match: /scan-proxy/ });
        await sandbox.scan('https://example.com');
        await sleep(30);
        const html = (nodes.get('result') || {}).innerHTML || '';
        return { markup: html, donation: html, afsløret: true };
      },
    },
  ];

  for (const t of TOOLS) {
    const pro = catalog.products[t.product];
    const words = periodWordsOf(t.product);
    const { markup, donation, afsløret } = await t.kør();
    // Donationslinjen skal overleve den nye boks. En side der ikke havde en,
    // skal heller ikke have fået en påstand om at have mistet en.
    const havdeDonation = readFileSync(join(root, t.path), 'utf8').includes('donate.stripe.com');

    ok(`${t.label}: et gennemført tjek renderer resultat-markup`, markup.length > 0);
    ok(`${t.label}: købsknappen bruger katalogens betalingslink`,
      markup.includes(pro.payment_link), `forventet ${pro.payment_link}`);
    ok(`${t.label}: knappen viser prisen fra katalogen ($${priceOf(t.product)})`,
      markup.includes(`$${priceOf(t.product)}`));
    ok(`${t.label}: knappen siger hvilken periode den sælger`,
      words.some((w) => markup.includes(w)), words.join(', '));
    ok(`${t.label}: knappen sælger den rigtige produktrappe`,
      new RegExp(pro.name.split(' ')[0]).test(markup), pro.name);
    ok(`${t.label}: boksen linker videre til produktsiden med gratis-vs-Pro-tabellen`,
      t.report.test(markup), String(t.report));
    if (havdeDonation) {
      ok(`${t.label}: donationslinjen overlevede den nye boks`, /donate\.stripe\.com/.test(donation));
    }
    // En boks der aldrig bliver vist, er ikke en købsvej. For den byggede form
    // er det resultat-markuppen selv der *er* beviset; for den statiske form er
    // det `hidden`-attributten, koden fjerner.
    if (t.form === 'statisk') {
      ok(`${t.label}: koden afslører boksen i samme øjeblik resultatet skrives`, afsløret,
        'ellers står prisen i markup uden at nogen ser den');
    } else {
      ok(`${t.label}: købslinket findes kun i den markup resultatet renderer`, markup.includes(pro.payment_link));
    }
    if (t.form === 'script' && t.path === 'site/clean-copy-tool.html') {
      // Uden en konvertering er der intet resultat, så kortet skal være væk.
      // Det er den dom der gør resten værd at tro: en port der kun læser
      // `proCard()`s streng ville være grøn på en side der aldrig viser den.
      const { nodes } = loadPage('site/clean-copy-tool.html',
        responses([{ status: 200, body: { ok: true } }], { skip: [/api\/track/] }).fetchImpl,
        { match: /batch-details/ });
      await sleep(30);
      nodes.get('input-box').value = '   ';
      nodes.get('input-box').fire('input');
      await sleep(20);
      ok(`${t.label}: et tomt felt viser ingen købsvej`, !((nodes.get('pro-nudge') || {}).innerHTML || '').trim(),
        'kortet må først vise sig, når der er noget resultat');
    }
    if (t.path === 'site/clean-copy-tool.html') {
      // En kunde der har aktiveret Pro skal ikke få en købsknap for det samme.
      const { sandbox, nodes } = loadPage('site/clean-copy-tool.html',
        responses([{ status: 200, body: { ok: true } }], { skip: [/api\/track/] }).fetchImpl,
        { match: /batch-details/ });
      await sleep(30);
      // `enableBatch(false)` skjuler præcis dette panel, når licensen ikke
      // holder — det er derfor kortet spørger om samme attribut. Panelet opstår
      // normalt i licens-initialiseringen, som ikke kører i sandkassen
      // (`CleanCopyLicense` ligger i et andet inline-script), så den hentes
      // her igennem `getElementById` præcis som koden gør.
      sandbox.document.getElementById('batch-details').hidden = false;
      nodes.get('input-box').value = 'Revenue grew 34%.';
      nodes.get('input-box').fire('input');
      await sleep(20);
      ok(`${t.label}: en aktiveret Pro-licens skjuler købsknappen`,
        ((nodes.get('pro-nudge') || {}).innerHTML || '') === '',
        `markup=${JSON.stringify(((nodes.get('pro-nudge') || {}).innerHTML || '').slice(0, 80))}`);
    }
  }

  // `/url-inspector` sælger den anden produktrappe, så den får sin egen dom.
  {
    const pro = catalog.products['page-profile-pro'];
    const words = periodWordsOf('page-profile-pro');
    const { nodes } = loadPage('site/url-inspector/index.html', responses([OK_INSPECT]).fetchImpl);
    await sleep(30);
    nodes.get('url-input').value = 'https://example.com';
    nodes.get('inspect-btn').click();
    await sleep(30);
    const src = readFileSync(join(root, 'site/url-inspector/index.html'), 'utf8');
    const markup = statisk(src, 'ui-pro');
    ok('url-inspector: købsknappen bruger Page Profile Pros betalingslink',
      markup.includes(pro.payment_link), `forventet ${pro.payment_link}`);
    ok(`url-inspector: knappen viser prisen fra katalogen ($${pro.price_usd})`,
      markup.includes(`$${pro.price_usd}`));
    ok('url-inspector: knappen siger hvilken periode den sælger',
      words.some((w) => markup.includes(w)), words.join(', '));
    ok('url-inspector: knappen sælger Page Profile Pro', /Page Profile Pro/.test(markup));
    ok('url-inspector: koden afslører boksen i samme øjeblik resultatet skrives',
      (nodes.get('ui-pro') || {}).hidden === false, `hidden=${(nodes.get('ui-pro') || {}).hidden}`);
  }

  // Mutation: den kode fra før denne opgave skal være rød på dommen. Den læses
  // fra git, så dommen måles på de bytes der faktisk var i live.
  {
    const before = '6cdabdc';
    for (const [path, product] of [
      ['site/cookie-check.html', 'eucomply-pro'],
      ['site/security-headers-check.html', 'eucomply-pro'],
      ['site/contrast-checker.html', 'eucomply-pro'],
    ]) {
      const old = execFileSync('git', ['show', `${before}:${path}`], { cwd: root, maxBuffer: 1 << 26 }).toString('utf8');
      ok(`mutation: ${path} fra før opgaven kan hentes`, old.length > 0);
      ok(`mutation: ${path} havde ingen købsvej i resultatet`,
        !old.includes(catalog.products[product].payment_link) || !outsideScripts(old).length,
        'dommen kan altså blive rød');
    }
    // Og den konkrete fejl: en knap uden periode skal være rød på ordlisten.
    const words = periodWordsOf('eucomply-pro');
    ok('mutation: en knap uden periode ville være rød',
      !words.some((w) => `Buy EUComply Pro — $79</a>`.includes(w)),
      'dommen kan altså se en knap uden periode');
  }
}

// --------------------------------------------------------------------------
// 12. Flere URL'er pr. kald. Opgaven i planen: feltet tog én URL, mens
//     produktsiden lovede at Pro «crawls the site» — så det betalte var den
//     del, kunden ikke kunne se forskel på. Fire domme, alle falsifiable på
//     den gamle kode:
//
//     1. Feltet tager linjeskift, og hver linje giver sit eget kald.
//     2. Begge sites står i resultatet, hver med sin score.
//     3. Seks linjer er en fejl med et tal — ikke en stille afskæring til 5.
//     4. Pro-boksen siger ærligt, at Pro gør det samme for *hele* sitet, så
//        den nye mulighed ikke får den gamme løfte-sætning til at se forkert ud.
// --------------------------------------------------------------------------
{
  const OK_SCAN2 = { status: 200, body: { ok: true, url: 'https://example.org', score: 40, grade: 'D', passed: 4, total: 9, results: { passed: [], failed: [] } } };

  for (const [path, lang] of PAGES) {
    const { fetchImpl, state } = responses([OK_SCAN, OK_SCAN2]);
    const { sandbox, nodes } = loadPage(path, fetchImpl);
    nodes.get('urlInput').value = 'example.com\nexample.org';
    await sandbox.scan();
    await sleep(60);
    const html = (nodes.get('results') || {}).innerHTML || '';
    const fejl = (nodes.get('errorBox') || {}).textContent || '';
    ok(`${lang}: to linjer giver to kald`, state.calls === 2, `calls=${state.calls} fejl=${fejl}`);
    ok(`${lang}: begge sites står i resultatet med hver sin score`,
      /example\.com/.test(html) && /example\.org/.test(html) && /90/.test(html) && /40/.test(html),
      fejl ? 'fejl=' + fejl : html.slice(0, 300));
    ok(`${lang}: ingen af linjerne blev afskåret tavst`,
      !/only the first|only scans the first/i.test(html), html.slice(0, 200));
    // Dommen er den *konkrete* sætning, ikke et ord: «crawls the whole site —
    // the same check on every page it finds». Den skal være der i begge sprog,
    // ellers kunne en side sige hele løftet og så alligevel skjule, at den
    // kun så den ene side.
    const heleSitet = lang === 'EN'
      ? /crawls the whole site[\s\S]{0,60}every page it finds/i
      : /gennemgår hele sitet[\s\S]{0,60}hver side den finder/i;
    ok(`${lang}: Pro-boksen siger at Pro gør det samme for hele sitet`,
      heleSitet.test(html), 'ingen ærlig crawls-sætning');
    ok(`${lang}: købsknappen overleverede flere sites`,
      /buy\.stripe\.com/.test(html), 'knap mangler');
  }

  for (const [path, lang] of PAGES) {
    const { fetchImpl, state } = responses([OK_SCAN]);
    const { sandbox, nodes } = loadPage(path, fetchImpl);
    nodes.get('urlInput').value = 'a.dk\nb.dk\nc.dk\nd.dk\ne.dk\nf.dk';
    await sandbox.scan();
    await sleep(30);
    const fejl = (nodes.get('errorBox') || {}).textContent || '';
    ok(`${lang}: seks linjer er en fejl med et tal, ikke fem scanninger`,
      state.calls === 0 && /5/.test(fejl), `calls=${state.calls} fejl=${fejl}`);
  }

  // Ét URL skal stadig gøre præcis ét kald og se ud som i dag. Ellers ville
  // den nye vej have brudt alt, der bruger scanneren.
  for (const [path, lang] of PAGES) {
    const r = await runScan(path, [OK_SCAN]);
    ok(`${lang}: én linje er stadig ét kald og ét resultat`, r.calls === 1 && r.err === '', `calls=${r.calls} err=${r.err}`);
  }

  // Hvilken side blev læst? Sætningen «the score is the homepage» lå på
  // overblikket og i rapporten, også når kunden havde indsendt `/kontakt` —
  // så var det ikke værktøjet der var unævnt, men rapporten. Dommen er på
  // den konkrete sti: den skal stå i overblikket, i det enkelte resultat og i
  // den downloadede rapport, og den gamle løgn-sætning skal være væk.
  const OK_SCAN_DYB = {
    status: 200,
    body: {
      ok: true, url: 'https://example.com', scanned_url: 'https://example.com/kontakt',
      pages_checked: 6, score: 90, grade: 'A', passed: 9, total: 10, results: {},
    },
  };
  for (const [path, lang] of PAGES) {
    const { fetchImpl } = responses([OK_SCAN_DYB]);
    const { sandbox, nodes } = loadPage(path, fetchImpl);
    // `downloadReport()` pakker rapporten i en `Blob` og giver den videre til et
    // `<a download>`. For at dommen kan læse den, fanges blobben her — den
    // udskiftes *efter* at siden er kørt ind, fordi `new Blob(...)` slås op i
    // det øjeblik rapporten downloades, ikke da scriptet blev læst.
    let fanget = '';
    const rigtigBlob = sandbox.Blob;
    sandbox.Blob = class extends rigtigBlob {
      constructor(parts, opts) { super(parts, opts); fanget = parts.join(''); }
    };
    nodes.get('urlInput').value = 'example.com/kontakt';
    await sandbox.scan();
    await sleep(30);
    const html = (nodes.get('results') || {}).innerHTML || '';
    sandbox.downloadReport();
    sandbox.Blob = rigtigBlob;
    ok(`${lang}: resultatet siger hvilken side der blev læst`,
      /kontakt/.test(html), html.slice(0, 300));
    ok(`${lang}: resultatet tæller de sider der blev læst`,
      new RegExp(`6 ${lang === 'EN' ? 'pages read' : 'sider læst'}`).test(html),
      html.slice(0, 300));
    ok(`${lang}: siden påstår ikke længere at have læst forsiden`,
      !/the score is the homepage/i.test(html) && !/scoren er forsiden/i.test(html),
      html.slice(0, 300));
    ok(`${lang}: den downloadede rapport siger den læste side`,
      /example\.com\/kontakt/.test(fanget), fanget.slice(0, 300));
  }

  // Hvilke sider blev læst — ikke hvor mange. «12 pages read» kan ingen
  // efterprøve, og det er præcis den slags linje en kunde spørger ind til,
  // når et fund er for godt. Serveren sender `pages_read`, så resultatet og
  // rapporten skal vise de konkrete stier.
  const OK_SCAN_LAESTE = {
    status: 200,
    body: {
      ok: true, url: 'https://example.com', scanned_url: 'https://example.com/',
      pages_checked: 9,
      pages_read: [
        'https://example.com/',
        'https://example.com/da/juridisk/privatlivspolitik',
        'https://example.com/betingelser',
      ],
      score: 88, grade: 'B', passed: 8, total: 9, results: {},
    },
  };
  for (const [path, lang] of PAGES) {
    const { fetchImpl } = responses([OK_SCAN_LAESTE]);
    const { sandbox, nodes } = loadPage(path, fetchImpl);
    let fanget = '';
    const rigtigBlob = sandbox.Blob;
    sandbox.Blob = class extends rigtigBlob {
      constructor(parts, opts) { super(parts, opts); fanget = parts.join(''); }
    };
    nodes.get('urlInput').value = 'example.com';
    await sandbox.scan();
    await sleep(30);
    const html = (nodes.get('results') || {}).innerHTML || '';
    sandbox.downloadReport();
    sandbox.Blob = rigtigBlob;
    ok(`${lang}: resultatet lister de sider der blev læst`,
      /\/da\/juridisk\/privatlivspolitik/.test(html) && /\/betingelser/.test(html),
      html.slice(0, 300));
    ok(`${lang}: listen er foldet sammen, så den ikke skubber fundene ned`,
      /class="pages-read"/.test(html) && /<summary>/.test(html), html.slice(0, 300));
    ok(`${lang}: listen tæller kun sites egne sider`,
      !/andet\.example/.test(html), html.slice(0, 300));
    ok(`${lang}: rapporten lister de samme sider`,
      /\/da\/juridisk\/privatlivspolitik/.test(fanget) && /\/betingelser/.test(fanget),
      fanget.slice(0, 400));
  }

  // Pro-kortet skal kunne sælge på forskellen. Det kan det ikke, hvis det
  // siger «one page» om et kald der nu læser siden PLUS de juridiske sider den
  // peger på — så er forskellen mindre end den lyder, og det er præcis den
  // løgn, kortet blev bygget for at undgå. Dommen læser den rendererede
  // markup, ikke kildekoden, fordi kun den første er noget en kunde ser.
  for (const [path, lang] of PAGES) {
    const { fetchImpl } = responses([OK_SCAN_LAESTE]);
    const { sandbox, nodes } = loadPage(path, fetchImpl);
    nodes.get('urlInput').value = 'example.com';
    await sandbox.scan();
    await sleep(30);
    const html = (nodes.get('results') || {}).innerHTML || '';
    const pro = html.slice(html.indexOf('pro-card'));
    ok(`${lang}: pro-kortet påstår ikke længere at kaldet kun læste én side`,
      pro.length > 0 && !/(checked one page|One page per site|tjekkede én side|Én side pr\. website)/.test(pro),
      pro.slice(0, 160) || 'pro-kortet blev ikke renderet');
    ok(`${lang}: pro-kortet siger hvad der *blev* læst, så forskellen er målbar`,
      /legal pages|juridiske sider, den peger/i.test(pro), pro.slice(0, 220));
  }
}

// 13. Pro-kortet i trykt form. `/scan` og `/compliance-site-check` tilbyder begge
//     «Udskriv / gem som PDF», og `@media print` i `site/style.css` skjuler
//     `.btn` — så uden en linje mere fik brugeren en lilla salgst tekst i sin
//     rapport med den eneste handling fjernet. Målt i browseren før rettelsen:
//     `display: block` på `.pro-card`, `display: none` på knappen inden i den.
//     Domden her læser den rigtige fil, fordi det er den browseren får.
{
  const css = readFileSync(join(root, 'site/style.css'), 'utf8');
  const printBlock = css.slice(css.indexOf('@media print'));
  // `@media print` skjuler med ÉN lang vælgerliste, så domden skal læse
  // hvilke vælgere der står i den regel — ikke søge efter en regel pr. vælger.
  // En regel der skjuler `.btn` men ikke `.pro-card` er præcis fejlen.
  const skjuler = (block, klasse) => {
    for (const m of block.matchAll(/([^{}]+)\{([^{}]*)\}/g)) {
      if (!m[2].includes('display: none')) continue;
      if (m[1].split(',').some((s) => s.trim() === klasse)) return true;
    }
    return false;
  };
  ok('print: pro-kortet skjuler sig i den trykte rapport',
    skjuler(printBlock, '.pro-card'),
    `@media print skal skjule .pro-card, som den skjuler .btn`);
  // Og de otte værktøjer der deler kortet, må ikke stå med en tom regel der
  // ligner som om den gør noget: `.pro-card` skal være i den samme skjul-liste
  // som knappen, ikke i en regel for sig.
  const sammeRegel = printBlock.match(/([^{}]+)\{[^{}]*display: none[^{}]*\}/g) || [];
  ok('print: pro-kortet skjules i samme regel som knappen',
    sammeRegel.some((r) => r.includes('.pro-card') && r.includes('.btn')),
    `regler med display:none: ${sammeRegel.length}, pro-card i egen regel: ${sammeRegel.some((r) => r.includes('.pro-card') && !r.includes('.btn'))}`);
  // Mutation: `.pro-card` fjernet fra print-listen skal gøre dommen rød, så den
  // ikke kan være grøn fordi den slet ikke dømmer.
  const uden = printBlock.replace(/\.pro-card, /, '');
  ok('mutation: pro-kortet fjernet fra print-listen fanges',
    skjuler(printBlock, '.pro-card') && !skjuler(uden, '.pro-card'),
    'altså kan dommen blive rød på den gamle kode');
}

console.log(`\nscan-clients: ${pass}/${pass + fail}`);
process.exit(fail ? 1 : 0);
