// Ende-til-ende-test af de to gratis scanningsværktøjer, der kalder vores egen
// worker: `/compliance-site-check` (EN + DA) og `/url-inspector`.
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
    value: '', textContent: '', innerHTML: '', disabled: false, src: '',
    style: {}, dataset: {}, children: [], _ls: {},
    classList: { _s: new Set(), add(c) { this._s.add(c); }, remove(c) { this._s.delete(c); }, contains(c) { return this._s.has(c); } },
    appendChild() {}, removeChild() {}, setAttribute() {}, remove() {}, focus() {},
    getAttribute: () => null,
    addEventListener(t, fn) { (this._ls[t] = this._ls[t] || []).push(fn); },
    click() { (this._ls.click || []).forEach((fn) => fn({})); },
    querySelectorAll: () => [], querySelector: () => null,
  };
  return e;
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
// Genkalderne står i produktionskoden med 1200 ms mellemrum. Sandkassen klemmer
// dem til 0, så en test ikke skal vente minutter — antallet forsøg måles i stedet.
const fastTimeout = (fn, _ms, ...rest) => setTimeout(fn, 0, ...rest);

function loadPage(path, fetchImpl) {
  const html = readFileSync(join(root, path), 'utf8');
  const scripts = [...html.matchAll(/<script(?![^>]*\bsrc=)(?![^>]*ld\+json)[^>]*>([\s\S]*?)<\/script>/g)].map((m) => m[1]);
  const main = scripts.find((s) => /fetch\(|inspect|scan/.test(s) && !/api\/track/.test(s));
  if (!main) throw new Error(`ingen brugbar <script> i ${path}`);
  const nodes = new Map();
  const sandbox = {
    console, setTimeout: fastTimeout, clearTimeout, URL, URLSearchParams, Promise, Error, JSON, Date, Math,
    encodeURIComponent, Object, Array, String, Number, Boolean, RegExp, Map, Set,
    scrollTo() {}, print() {}, alert() {}, confirm: () => true,
    fetch: fetchImpl,
    document: {
      getElementById(id) { if (!nodes.has(id)) nodes.set(id, el()); return nodes.get(id); },
      querySelector() { return null; }, querySelectorAll: () => [],
      addEventListener() {}, createElement: () => el(), createTextNode: (t) => ({ textContent: t }),
      body: el(), documentElement: el(),
    },
    navigator: { doNotTrack: '0' },
    location: { pathname: '/' + path.split('/').pop(), href: 'https://mahope.tools/' },
  };
  sandbox.window = sandbox;
  sandbox.globalThis = sandbox;
  vm.createContext(sandbox);
  vm.runInContext(main, sandbox, { filename: path });
  return { sandbox, nodes };
}

// Svarene kommer som en række, og der tælles kald, så "prøver den igen?" kan
// måles i stedet for at læses.
function responses(list) {
  const state = { calls: 0 };
  const fetchImpl = async () => {
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
  ok('EN: 429 er forbigående og genkaldes', r.calls === 3, `calls=${r.calls}`);
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
// 5. Mutationer af *læseren*, så kontrollerne ovenfor ikke er en grøn cirkel.
//    Hver mutation skal gøre den navngivne kontrol rød.
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
  m = m.replace('err.transient = !data || r.status === 429 || r.status >= 500;', 'err.transient = false;')
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

console.log(`\nscan-clients: ${pass}/${pass + fail}`);
process.exit(fail ? 1 : 0);
