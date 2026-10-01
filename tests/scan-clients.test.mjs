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
    classList: { _s: new Set(), add(c) { this._s.add(c); }, remove(c) { this._s.delete(c); }, contains(c) { return this._s.has(c); } },
    appendChild() {}, removeChild() {}, setAttribute() {}, remove() {}, focus() {},
    getAttribute: () => null,
    addEventListener(t, fn) { (this._ls[t] = this._ls[t] || []).push(fn); },
    click() { (this._ls.click || []).forEach((fn) => fn({})); },
    submit() { (this._ls.submit || []).forEach((fn) => fn({ preventDefault() {} })); },
    querySelectorAll: () => [], querySelector: () => null,
  };
  return e;
}

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
  // `book-ai.js` bygger sin egen sektion og hænger den før <footer>, så
  // sandkassen skal have et footer-element med en forælder.
  const footer = el();
  footer.parentNode = { insertBefore() {} };
  const sandbox = {
    console, setTimeout: fastTimeout, clearTimeout, URL, URLSearchParams, Promise, Error, JSON, Date, Math,
    encodeURIComponent, Object, Array, String, Number, Boolean, RegExp, Map, Set, Blob,
    scrollTo() {}, print() {}, alert() {}, confirm: () => true,
    fetch: fetchImpl,
    document: {
      getElementById(id) {
        // `opts.absent` er id'er siden *ikke* har i DOM'en. Uden dem ville
        // stubben skabe dem, og en vagt som `if (getElementById('x')) return;`
        // ville altid tro at elementet allerede var der.
        if (opts.absent && opts.absent.includes(id)) return null;
        if (!nodes.has(id)) nodes.set(id, el());
        return nodes.get(id);
      },
      querySelector(sel) { return sel === 'footer' && !opts.noFooter ? footer : null; },
      querySelectorAll: () => [],
      addEventListener() {}, createElement: () => el(), createTextNode: (t) => ({ textContent: t }),
      body: el(), documentElement: el(), head: el(),
    },
    navigator: { doNotTrack: '0' },
    location: { pathname: '/' + path.split('/').pop(), href: 'https://mahope.tools/' },
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
function responses(list) {
  const state = { calls: 0, urls: [] };
  const fetchImpl = async (url) => {
    state.urls.push(String(url));
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
// Den tælles ikke med: målingen starter efter at den er faldet, og klikket på
// knappen er den vej en besøger faktisk tager.
async function runInspect(list) {
  const { fetchImpl, state } = responses(list);
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
  const { fetchImpl, state } = responses(list);
  const { sandbox, nodes } = loadPage(path, fetchImpl, { match: /ASK_MAX_TRIES/ });
  nodes.get('questionInput').value = 'Does NIS2 apply to a 5-person agency?';
  sandbox.sendQuestion();
  await sleep(40);
  return { calls: state.calls, status: nodes.get('chatStatus').textContent || '', btn: nodes.get('sendBtn').disabled };
}

// Ventelisten ligger bag et vellykket svar, så den måles på den samme kørsel.
async function runAskLead(path, list) {
  const { fetchImpl, state } = responses(list);
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

async function runHeaders(list) {
  const { fetchImpl, state } = responses(list);
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
       .replace("showError(err.transport ? OFFLINE : (err.transient ? SERVER_BUSY : (err.message || 'Scan failed')));",
                "showError('Network error: ' + (err.message || 'unknown'));");
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

console.log(`\nscan-clients: ${pass}/${pass + fail}`);
process.exit(fail ? 1 : 0);
