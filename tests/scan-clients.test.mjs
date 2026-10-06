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
import { readFileSync, existsSync } from 'node:fs';
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
    // eksponerer. `ev` er til de domme der skal *falske et event* (en finger på
    // et canvas har `touches` og `clientX`; en tastaturtrykning har ingen af
    // dele), fordi en `TouchEvent` ikke kan konstrueres i en vm.
    fire(t, ev) {
      (this._ls[t] || []).forEach((fn) => fn(ev
        ? Object.assign({ target: this }, ev)
        : { target: this, preventDefault() {} }));
    },
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
    // Den stiplede ramme om den tekstblok et klik flytter. Den tegner
    // *intet* ind i bufferen — en stiplet strege er ikke en baggrund, og
    // måle den som fyld ville give porten en kant bruteren ikke ser. Den
    // findes her fordi kernen kalder den på enhver canvas-stub; en stub
    // der mangler den dør med en TypeError ved sidevisning, og så dømmer
    // hele dommen ingenting — grøn fordi den aldrig kom så langt.
    setLineDash() {}, strokeRect() {},
    createLinearGradient: () => grad, createRadialGradient: () => grad,
    translate() {}, scale() {}, rect() {},
  };
}
const withCanvas = (e) => { e.getContext = () => ctx2d(); e.width = 900; e.height = 420; e.getBoundingClientRect = () => rect(e); return e; };
// `pos()` i kernen placerer teksten efter canvas' **synlige** rektangel, så
// stubben skal have en. Den er 1:1 i pixel (900x420), altså samme forhold som
// `width`/`height` — så et tal i dommen kan læses som pixel uden at regne om.
const rect = (e) => ({ left: 0, top: 0, width: e.width, height: e.height, right: e.width, bottom: e.height });

// Det billede næste `new Image()` læser. En læsende sandkasse måler ellers alle
// billeder ens, og så er en fejl der *kun* rammer det andet billede i en træk-
// række usynlig — hvilket er præcis den fejl der lå i «Fiks det»-knappen.
let naesteBillede = { a: [200, 200, 200], b: [200, 200, 200] };
const saetBillede = (b) => { naesteBillede = b; return b; };

// En *levende* udgave af læse-canvassen ovenfor: `getImageData` læser det billede
// `drawImage()` netop har tegnet, og `clearRect` husker at næste læsning er
// bogstavelaget — så alpha er præcis dækningen, som er det eneste en farveafstand
// aldrig kan fortælle. Kun `opts.levendeBilleder` tænder den, så de andre domme
// fortsat kører mod den flade.
function ctx2dLevende(st) {
  const grad = { addColorStop() {} };
  return {
    canvas: null, font: '', textBaseline: '', fillStyle: '',
    measureText: (t) => ({ width: Math.max(8, String(t || '').length * 9) }),
    getImageData: (x, y, w, h) => {
      const W = Math.max(1, Math.round(w)), H = Math.max(1, Math.round(h));
      const d = new Uint8ClampedArray(W * H * 4);
      // Bogstaverne ligger på en ryddet flade, så hver pixel er baggrund.
      if (st.ryddet) return { data: d };
      // Venstre halvdel i den ene farve, højre i den anden. Baggrunden *spænder*
      // altså, så kernen må finde både sin mørkeste og sin lyseste pixel — uden
      // det ville en slør-rettelse aldrig blive foreslået, og dommen ville dømme
      // en veje kernen ikke kan tage.
      const p = st.px || naesteBillede;
      for (let r = 0; r < H; r++) {
        for (let c = 0; c < W; c++) {
          const i = (r * W + c) * 4;
          const k = c * 2 < W ? p.a : p.b;
          d[i] = k[0]; d[i + 1] = k[1]; d[i + 2] = k[2]; d[i + 3] = 255;
        }
      }
      return { data: d };
    },
    putImageData() {},
    drawImage(img) { st.px = (img && img.pixel) || st.px; st.ryddet = false; },
    clearRect() { st.ryddet = true; },
    fillRect() {},
    // Hver `fillText` huskes med sit sted. Det er den **tegnede** placering, altså
    // den eneste der kan dømme om en finger flyttede teksten: et tal i en variabel
    // ville være kernens egen påstand om sig selv, og et tal i et billede
    // kræver en browser. `st.tekst` vokser med hver tegning, så en dom læser
    // den *sidste* — og `st.draws` tæller, så den kan se at der overhovedet
    // blev tegnet noget.
    fillText(t, x, y) { (st.tekst = st.tekst || []).push([t, x, y]); st.draws = (st.draws || 0) + 1; },
    beginPath() {}, arc() {}, fill() {},
    save() {}, restore() {}, createLinearGradient: () => grad,
    setLineDash() {}, strokeRect() {},
    createRadialGradient: () => grad, translate() {}, scale() {}, rect() {},
  };
}

// `loadFile()` i kernen laver et `<img>` fra et objekt-URL, så sandkassen skal
// kunne både URL'et og billedet. `src`-sætteren kalder `onload` — en browser
// gør det også, og kernen forventer at være inde i `onload` når den måler.
class SandkasseBillede {
  set src(v) {
    this._src = v;
    this.pixel = naesteBillede;
    this.naturalWidth = 900;
    this.naturalHeight = 420;
    if (this.onload) this.onload();
  }
}
class SandkasseURL extends URL {}
SandkasseURL.createObjectURL = () => 'blob:sandkasse';
SandkasseURL.revokeObjectURL = () => {};

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
  // `opts.memoQSelector` giver hvert stub-element **samme** svar på samme
  // `querySelector`, som en rigtig DOM gør. Uden det får hvert kald en ny stub,
  // så en dom på «knappen er låst» ville læse en anden knap end den siden
  // låste — altså grøn på en side der ikke låser noget. Kun `/scan` har brug
  // for det, og kun fordi dens submit-handler låser knappen.
  const memoQSelector = (e) => {
    e._qs = {};
    e.querySelector = (sel) => (e._qs[sel] = e._qs[sel] || el());
    return e;
  };
  // `opts.canvas` giver hver stub et læse-canvas. Kun `/text-on-image-checker`
  // har brug for det; de andre sider kalder aldrig `getContext`.
  const make = (id) => {
    const n = el();
    if (id in seeds) n.value = seeds[id];
    if (opts.memoQSelector) memoQSelector(n);
    if (opts.canvas) (opts.levendeBilleder ? withLevendeCanvas(n) : withCanvas(n));
    return n;
  };
  // `opts.levendeBilleder` giver hver stub et canvas der *læser det billede der
  // lige blev tegnet*, så to fotos i træk kan måles hver for sig gennem den
  // samme `mount()`. Demoscenen er en `<canvas>`-stub, så den får også et billede.
  const st = { px: null, ryddet: true };
  const withLevendeCanvas = (e) => {
    e.getContext = () => ctx2dLevende(st);
    e.pixel = naesteBillede;
    e.width = 900; e.height = 420;
    e.getBoundingClientRect = () => rect(e);
    // En rigtig DOM giver det *samme* element ved to `querySelector` med samme
    // vælger, og et nyt element efter en `innerHTML`. Uden det kunne en test
    // hverken finde den knap kernen lige skrev eller ramme den rigtige lytter —
    // den ville trykke på en gammel måling. Det er hele pointen med en sekvens.
    e._qs = {};
    e.querySelector = (sel) => (e._qs[sel] = e._qs[sel] || el());
    let _h;
    Object.defineProperty(e, 'innerHTML', {
      get() { return _h !== undefined ? _h : e._t; },
      set(v) { _h = v; e._qs = {}; },
      configurable: true,
    });
    Object.defineProperty(e, 'textContent', {
      get() { return e._t; },
      set(v) { e._t = v; _h = undefined; },
      configurable: true,
    });
    return e;
  };
  // `book-ai.js` bygger sin egen sektion og hænger den før <footer>, så
  // sandkassen skal have et footer-element med en forælder.
  const footer = make();
  footer.parentNode = { insertBefore() {} };
  // `DOMContentLoaded`-lyttere samles og fyres *efter* sidens egen inline-kode,
  // i den rækkefølge browseren gør det i: inline scripts under parsing, så
  // deferred scripts (`/net.js`), så DOMContentLoaded. Uden det døde dommen om
  // kapabilitets-sonden i `/compliance-ai` stætigt på sandkassens no-op-stub,
  // fordi siden spørger på DOMContentLoaded — netop fordi `NET` endnu ikke findes
  // under parsing. Sonden var altså usynlig, ikke grøn.
  const domReady = [];
  const sandbox = {
    console, setTimeout: fastTimeout, clearTimeout, URL: SandkasseURL,
    URLSearchParams, Promise, Error, JSON, Date, Math,
    Image: SandkasseBillede,
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
      addEventListener(type, fn) { if (type === 'DOMContentLoaded') domReady.push(fn); },
      createElement: () => make(), createTextNode: (t) => ({ textContent: t }),
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
  // Se forklaringen ved `st.begivenheder`: `trackEvent` skal findes **før**
  // sidens egen kode kører, ellers dømmer en dom kernen på en ReferenceError.
  st.begivenheder = [];
  sandbox.trackEvent = (e) => { st.begivenheder.push(String(e)); };
  vm.createContext(sandbox);
  // `/net.js` står med `defer` i head, så browseren har kørt den længe før nogen
  // kan klikke. Sandkassen gør det samme — ellers ville de tre klienter der læser
  // den delte hjælper blive dømt mod en global der aldrig findes.
  vm.runInContext(netOverride ?? readFileSync(join(root, 'site/net.js'), 'utf8'), sandbox, { filename: 'site/net.js' });
  // `opts.preload` er de `src`-scripts browseren ville have kørt *før* siden
  // egen inline-kode. Uden dem kunne ingen dom lade en side kalde `TiContrast`:
  // sandkassen læser kun de inline blokke, og så ville artiklens `mount()` bare
  // være en ReferenceError — altså en grøn dom på en side med intet værktøj.
  // `opts.kilder` erstatter enkeltstående `src`-scripts med en given tekst, så
  // en dom kan køre den *gamle* kode gennem den samme sandkasse. Uden det måtte
  // en polaritetsdom skrive sin egen kopi af filen fra hukommelsen — og så er
  // den grøn fordi den dommer sin egen fejlform, ikke den der lå i repoet.
  for (const fil of opts.preload || []) {
    const tekst = opts.kilder && fil in opts.kilder ? opts.kilder[fil] : readFileSync(join(root, fil), 'utf8');
    vm.runInContext(tekst, sandbox, { filename: fil });
  }
  vm.runInContext(main, sandbox, { filename: path });
  // Se række forklaringen over `domReady`. En lytter der kaster stopper de
  // øvrige, som i en browser.
  for (const fn of domReady) fn.call(sandbox.document);
  // `st` er canvas-stubbens fælles hukommelse. Den skal kunne læses udefra, ellers
  // kan ingen dom se hvad kernen har tegnet — og det er tegningen, ikke et tal
  // i en variabel, der svarer på «flyttede fingeren teksten».
  return { sandbox, nodes, st };
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
  const state = { calls: 0, urls: [], saga: [] };
  const skips = (opts.skip || []).map((s) => (s instanceof RegExp ? { test: (u) => s.test(u) } : s));
  const fetchImpl = async (url, init) => {
    state.urls.push(String(url));
    // `opts.onCall` læser side-elementer i det øjeblik kaldet går ud. Det er
    // den eneste måde at se, hvad siden *sagde* undervejs: en dom på teksten
    // bagefter ville være grøn, fordi resultatet eller fejlen har overskrevet
    // den. Bruges af `/url-inspector`, der fortæller at den prøver igen.
    if (opts.onCall) state.saga.push(opts.onCall(String(url)));
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
  // `onCall` sættes *efter* loadPage, fordi den skal kunne læse sidens egne
  // elementer. Indtil da er den null, og intet kald er sendt endnu: siden kører
  // først sin egen URL ved sidevisning, og det første klik sker bagefter.
  const opts = { skip: [/api\/track/], onCall: null };
  const { fetchImpl, state } = responses([OK_INSPECT, ...list], opts);
  const { nodes } = loadPage('site/url-inspector/index.html', fetchImpl);
  opts.onCall = () => (nodes.get('status-bar') || {}).innerHTML || '';
  await sleep(30);
  const base = state.calls;
  nodes.get('url-input').value = 'https://example.com';
  nodes.get('inspect-btn').click();
  await sleep(30);
  return {
    calls: state.calls - base,
    err: (nodes.get('error-placeholder') || {}).innerHTML || '',
    // Statuslinjen i det øjeblik hvert kald går ud. Det er det eneste
    // tidspunkt, hvor siden skal have fortalt brugeren at den prøver igen:
    // bagefter står der kun resultat eller en fejl, så en dom på slutværdien
    // ville være grøn uden at sige noget.
    saga: state.saga,
  };
}

const PAGES = [
  ['site/compliance-site-check.html', 'EN'],
  ['site/da/compliance-site-check.html', 'DA'],
];

// Dybt link til PDF-trinet på de fire scanneresider. Før 6/10 pegede pro-kortets
// note bare på `/compliance-report` (`/da/compliance-report` på dansk), så en
// Pro-holder der lige har betalt $79 og set sit resultat landede i et **tomt**
// felt, måtte køre scanningen igen og scrollede ned til nøglefeltet bagefter.
// Dommen kræver derfor at `#url=` er kodet med **den side der faktisk blev læst**
// — en note uden koden er præcis den gamle fejl. Mutation: sektion 11.
const PDF_HANDOFF = /href="\/compliance-report#url=https%3A%2F%2Fexample\.com"/;

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
  // Genkalderne ligger i /net.js nu. Siden skal stadig fortælle at den prøver
  // igen — ellers står brugeren og kigger på en spinder der ser ud til at være
  // hængt, i to og et halvt sekund. Målt i det øjeblik det andet kald går ud.
  const under = r.saga[r.saga.length - 1];
  ok('url-inspector: siden siger at den prøver igen undervejs', /retrying/i.test(under), under);
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
    // Regelens to linjer ligger i /net.js, så her dømmes *at siden læser den*:
    // en kopi ville være grøn, fordi den ikke kan se ud over sin egen fil.
    ok(`mutation: ${p} har samme regel`, /PROFILE_MAX_TRIES = 3/.test(src) && /NET\.askGet\(/.test(src));
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
    fetch: fetchImpl, navigator: { doNotTrack: '0' }, location: { pathname: '/x.html', search: '', hash: '' },
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
  // Regelens linjer lå seks steder; de ligger nu i /net.js. Ratcheten skal derfor
  // finde *kernen*, og de seks klienter skal læse den — en kopi ville være grøn
  // her, fordi den kan se ud over sin egen fil.
  const src = readFileSync(join(root, 'site/compliance-site-check.html'), 'utf8');
  ok('mutation: kernen læser status før kroppen', /res\.json\(\)\.catch/.test(readFileSync(join(root, 'site/net.js'), 'utf8')));
  ok('mutation: 503-grænsen er en konstant, ikke et hærdet tal', /SCAN_MAX_TRIES = 3/.test(src));
  ok('mutation: url-inspector har samme regel', /INSPECT_MAX_TRIES = 3/.test(readFileSync(join(root, 'site/url-inspector/index.html'), 'utf8')));
  ok('mutation: DA-siden har samme regel', /SCAN_MAX_TRIES = 3/.test(readFileSync(join(root, 'site/da/compliance-site-check.html'), 'utf8')));
  for (const p of ['site/compliance-site-check.html', 'site/da/compliance-site-check.html',
                   'site/page-profile.html', 'site/da/page-profile.html',
                   'site/security-headers-check.html', 'site/url-inspector/index.html']) {
    const klient = readFileSync(join(root, p), 'utf8');
    ok(`mutation: ${p} læser den delte regel`, /NET\.askGet\(/.test(klient), 'egen regel');
  }
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
      navigator: { doNotTrack: '0' }, location: { pathname: '/x.html', search: '', hash: '' } };
    sandbox.window = sandbox; sandbox.globalThis = sandbox;
    vm.createContext(sandbox);
    // Siden læser reglen i /net.js nu, så mutationen ville dømme en
    // ReferenceError i stedet for genkaldsregelen. Den skal være indlæst først,
    // som browseren gør med `defer` i head.
    vm.runInContext(readFileSync(join(root, 'site/net.js'), 'utf8'), sandbox, { filename: 'site/net.js' });
    vm.runInContext(main, sandbox);
    nodes.get('urlInput').value = 'example.com';
    await sandbox.scan();
    await new Promise((r) => setTimeout(r, 20));
    ok('mutation: uden genkald bliver kontrollen rød', state.calls === 1, `calls=${state.calls} (forventet 3)`);
  }
}
{
  // `#url=`-fragmentet skal *gøre* noget, ikke bare være læst.
  //
  // `check_url_handoff.py` dømmer, at forsiden erklærer `takesUrl` og at
  // målruten læser `#url=` med `location.hash`. Den dømmer ikke, at siden
  // *bruger* den — og det er den tredje ende, hvor de kan være forskudt fra
  // hinanden helt stille. Her scanner compliance-siden sig selv, fordi
  // fragmentet siger det, så læseren der trykkede «Compliance-tjek» ud fra
  // forsidens tjek ikke skal skrive den samme adresse ind en gang til.
  //
  // Mutationen her er bevidst den stille: `if (!m) return;` → `if (true)
  // return;`. Siden læser stadig `#url=` (porten er grøn), `#url=` i
  // adresselinjen ser stadig ud som om den gør noget — men intet kald går ud.
  // En test der blot greb efter teksten ville være grøn på den mutation.
  const HANDOFF_URL = 'https://hvor-dette-er.example/';
  const MUTATION = "if (!m) return;";
  for (const p of ['site/compliance-site-check.html', 'site/da/compliance-site-check.html']) {
    const html = readFileSync(join(root, p), 'utf8');
    const main = [...html.matchAll(/<script(?![^>]*\bsrc=)[^>]*>([\s\S]*?)<\/script>/g)]
      .map((x) => x[1]).find((s) => /function fetchScan/.test(s));
    ok(`handoff: ${p} har et script med fetchScan`, !!main);
    ok(`mutation: ${p} har den kode der læser fragmentet`, html.includes(MUTATION));
    ok(`mutation: ${p} kan gøres tavs`, html.includes('if (true) return;') === false);

    async function kørMed(tekst, hash) {
      const { fetchImpl, state } = responses([OK_SCAN]);
      const nodes = new Map();
      const sandbox = { console, setTimeout, URL, Promise, Error, JSON, Object, Array, String,
        Number, Boolean, RegExp, encodeURIComponent, decodeURIComponent,
        fetch: fetchImpl, navigator: { doNotTrack: '0' },
        location: { pathname: '/' + p.split('/').pop(), search: '', hash },
        document: { getElementById(id) { if (!nodes.has(id)) nodes.set(id, el()); return nodes.get(id); },
          querySelector: () => el(), createElement: () => el(), head: el(), body: el(),
          createTextNode: (t) => ({ textContent: String(t) }), addEventListener() {} } };
      sandbox.window = sandbox; sandbox.globalThis = sandbox;
      sandbox.scrollTo = () => {};
      vm.createContext(sandbox);
      vm.runInContext(readFileSync(join(root, 'site/net.js'), 'utf8'), sandbox, { filename: 'site/net.js' });
      vm.runInContext(tekst, sandbox, { filename: p });
      await new Promise((r) => setTimeout(r, 25));
      return state;
    }

    const hash = '#url=' + encodeURIComponent(HANDOFF_URL);
    const rigtig = await kørMed(main, hash);
    ok(`handoff: ${p} scanner den adresse fragmentet indeholder`,
      rigtig.calls === 1 && rigtig.urls.some((u) => u.includes('hvor-dette-er.example')),
      `calls=${rigtig.calls} urls=${JSON.stringify(rigtig.urls)}`);

    const tavs = await kørMed(main.replace(MUTATION, 'if (true) return;'), hash);
    ok(`mutation: ${p} uden fragment-læsningen går rød`,
      tavs.calls === 0,
      `calls=${tavs.calls} (forventede 0 — porten er stadig grøn, den dømmer teksten)`);

    const anden = await kørMed(main, '#url=' + encodeURIComponent('javascript:alert(1)'));
    ok(`handoff: ${p} lader ikke en ikke-http adresse gå i scan`,
      anden.calls === 0, `calls=${anden.calls} (forventede 0)`);
  }
}
{
  // Den anden halvdel af den gamle fejl: at et forbigående svar blev meldt som
  // "Network error". Sætter vi beskeden tilbage og gør 5xx endeligt, skal både
  // genkaldskontrollen og tekstkontrollen blive røde.
  //
  // De to halvdele bor nu i hver sin fil — reglen i `/net.js`, beskeden på siden
  // — så mutationen rører dem hver for sig, ligesom den gamle kode gjorde. En
  // mutation der kun ramte den ene ville være grøn på den anden.
  const gammelKode = readFileSync(join(root, 'site/compliance-site-check.html'), 'utf8')
    .replace("fejl.push({ url: target, error: err.transport ? OFFLINE : (err.transient ? SERVER_BUSY : (err.message || 'Scan failed')) });",
             "fejl.push({ url: target, error: 'Network error: ' + (err.message || 'unknown') });");
  const gammelRegel = readFileSync(join(root, 'site/net.js'), 'utf8')
    .replace('err.transient = !data || res.status >= 500;', 'err.transient = false;');
  ok('mutation: den gamle behandling kan fremstilles',
    /Network error: ' \+ \(err\.message/.test(gammelKode) && /err\.transient = false;/.test(gammelRegel));
  {
    const { fetchImpl, state } = responses([{ status: 502, html: true }]);
    const scripts = [...gammelKode.matchAll(/<script(?![^>]*\bsrc=)(?![^>]*ld\+json)[^>]*>([\s\S]*?)<\/script>/g)].map((x) => x[1]);
    const main = scripts.find((s) => /fetchScan/.test(s));
    const nodes = new Map();
    const sandbox = { console, setTimeout: fastTimeout, URL, Promise, Error, JSON, encodeURIComponent, scrollTo() {},
      fetch: fetchImpl, navigator: { doNotTrack: '0' }, location: { pathname: '/x.html', search: '', hash: '' },
      document: { getElementById(id) { if (!nodes.has(id)) nodes.set(id, el()); return nodes.get(id); },
        createElement: () => el(), createTextNode: (t) => ({ textContent: t }), body: el(), addEventListener() {} } };
    sandbox.window = sandbox; sandbox.globalThis = sandbox;
    vm.createContext(sandbox);
    vm.runInContext(gammelRegel, sandbox, { filename: 'site/net.js' });
    vm.runInContext(main, sandbox);
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
    fetch: fetchImpl, navigator: { doNotTrack: '0' }, location: { pathname: '/compliance-ai.html', search: '', hash: '' },
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
    fetch: fetchImpl, navigator: { doNotTrack: '0' }, location: { pathname: '/security-headers-check.html', search: '', hash: '' },
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
  // De seks GET-klienter læste hver sin kopi af reglen. Nu skal de læse den
  // her, og de skal *indlæse* den — en side der bruger `NET.askGet()` uden at
  // hente filen ville være grøn på regexet og dø i browseren.
  for (const p of ['site/compliance-site-check.html', 'site/da/compliance-site-check.html',
    'site/page-profile.html', 'site/da/page-profile.html',
    'site/security-headers-check.html', 'site/url-inspector/index.html']) {
    const src = readFileSync(join(root, p), 'utf8');
    ok(`net.js: ${p} indlæser den`, /<script defer src="\/net\.js"><\/script>/.test(src));
    ok(`net.js: ${p} læser den delte regel i stedet for at kopiere den`,
      /NET\.askGet\(/.test(src) && !/function postJSON/.test(src) && !/\.transient\s*=/.test(src),
      'egen kopi af reglen');
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
  // De seks GET-klienter skal følge med ned på *samme* mutation. Havde de
  // hver haft en kopi af reglen, ville de være grønne her — det er præcis den
  // fejlform der gjorde det nødvendigt at samle dem.
  netOverride = broken;
  try {
    for (const [p, lang] of PAGES) {
      const r = await runScan(p, [{ status: 503, html: true }]);
      ok(`mutation: ${lang} compliance-site-check læser /net.js, så den følger med ned`, r.calls === 1, `calls=${r.calls} (forventet 3)`);
    }
    for (const [p, lang] of [['site/page-profile.html', 'EN'], ['site/da/page-profile.html', 'DA']]) {
      const r = await runProfile(p, [{ status: 503, html: true }]);
      ok(`mutation: ${lang} page-profile læser /net.js, så den følger med ned`, r.calls === 1, `calls=${r.calls} (forventet 3)`);
    }
    {
      const r = await runHeaders([{ status: 503, html: true }]);
      ok('mutation: security-headers-check læser /net.js, så den følger med ned', r.calls === 1, `calls=${r.calls} (forventet 3)`);
    }
    {
      const r = await runInspect([{ status: 503, html: true }]);
      ok('mutation: url-inspector læser /net.js, så den følger med ned', r.calls === 1, `calls=${r.calls} (forventet 3)`);
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
    ['site/compliance-site-check.html', 'EN', PDF_HANDOFF],
    ['site/da/compliance-site-check.html', 'DA', PDF_HANDOFF],
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

    // Mutation på **PDF-vejen alene**: samme side, men `#url=`-koden er væk, så
    // noten peger på `/compliance-report` som før 6/10. Uden den mutation er
    // dommen grøn på en side hvor handoffen aldrig virkede — den gamle kode fra
    // `da3999e` kan ikke bruges, fordi den pro-kort slet ikke havde.
    const mutation = src.replace(
      /^.*var handoff = dyb \? '\/compliance-report#url=' \+ encodeURIComponent\(url\).*$/m,
      "    var handoff = '/compliance-report';");
    ok(`${label}: mutationsankeret for PDF-vejen findes`,
      mutation !== src, 'sideformen ændrede sig — mutationen ville køre på uændret kode');
    {
      const { fetchImpl: mutFetch } = responses([OK_SCAN]);
      const mut = loadPage(path, mutFetch, { source: mutation });
      mut.nodes.get('urlInput').value = 'example.com';
      await mut.sandbox.scan();
      await sleep(30);
      const mutHtml = (mut.nodes.get('results') || {}).innerHTML || '';
      ok(`${label}: mutation: uden #url= er den dybe PDF-vej rød`,
        !PDF_HANDOFF.test(mutHtml) && mutHtml.includes('href="/compliance-report"'),
        'dommen kan altså blive rød');
    }

    // Den dybe vej må **kun** bære en adresse rapport-siden genkender. Den
    // bruger `/^https?:\/\//i` på sit fragment, så en værdi uden scheme
    // (`example.com`, som er helt normalt at skrive) blev afvist stille, og
    // læseren landede i præcis det tomme felt handoffen fjerner. Dommen her
    // tvinger serverens svar til at være **uden** scheme — det er det eneste
    // input, der adskiller de to veje — og kræver den gamle rute.
    {
      const rå = { status: 200, body: { ...OK_SCAN.body, url: 'example.com' } };
      const { fetchImpl: råFetch } = responses([rå]);
      const r = loadPage(path, råFetch);
      r.nodes.get('urlInput').value = 'example.com';
      await r.sandbox.scan();
      await sleep(30);
      const råHtml = (r.nodes.get('results') || {}).innerHTML || '';
      ok(`${label}: en adresse uden scheme falder til den gamle rute, ikke til et tomt felt`,
        !/#url=/.test(råHtml) && /href="\/((?:da\/)?compliance-report)"/.test(råHtml),
        'håndværket ville sende læseren til en rapport der aldrig genereres');
    }

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
      // skrives uden et netværkskald. Sandkassen får et læse-canvas og kernen
      // fra `/text-on-image-core.js`, fordi 2/10 flyttede WCAG-formlen dér —
      // uden `preload` ville `mount()` være en ReferenceError, og dommen ville
      // være grøn på en side uden værktøj.
      async kør() {
        const { nodes } = loadPage('site/text-on-image-checker.html', responses([OK_COOKIE]).fetchImpl,
          { match: /TiContrast\.mount/, canvas: true, preload: ['site/text-on-image-core.js'] });
        await sleep(30);
        return { markup: (nodes.get('result') || {}).innerHTML || '', afsløret: true,
                 donation: (nodes.get('result') || {}).innerHTML || '' };
      },
    },
    {
      path: 'site/text-on-image-checker-da.html', label: 'text-on-image DA', product: 'eucomply-pro',
      report: /href="\/da\/compliance-report"/, form: 'script',
      // Samme kern som den engelske. Uden denne linje ville en fejl i den
      // danske sides egen tekst (fx et tal med punktum i stedet for komma)
      // være usynlig, fordi dommen kun læste den engelske.
      async kør() {
        const { nodes } = loadPage('site/text-on-image-checker-da.html', responses([OK_COOKIE]).fetchImpl,
          { match: /TiContrast\.mount/, canvas: true, preload: ['site/text-on-image-core.js'] });
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
      report: PDF_HANDOFF, form: 'script',
      async kør() {
        const { fetchImpl } = responses([OK_SCAN_PROXY]);
        const { sandbox, nodes } = loadPage('site/scan.html', fetchImpl,
          { match: /scan-proxy/, preload: ['site/scan-share-core.js'] });
        await sandbox.scan('https://example.com');
        await sleep(30);
        const html = (nodes.get('result') || {}).innerHTML || '';
        return { markup: html, donation: html, afsløret: true };
      },
    },
    {
      path: 'site/scan-da.html', label: 'scan DA', product: 'eucomply-pro',
      report: PDF_HANDOFF, form: 'script',
      async kør() {
        const { fetchImpl } = responses([OK_SCAN_PROXY]);
        const { sandbox, nodes } = loadPage('site/scan-da.html', fetchImpl,
          { match: /scan-proxy/, preload: ['site/scan-share-core.js'] });
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
    // Samme hul som på `/compliance-site-check`: scanneren får sin adresse fra
    // serverens `url`, og den kan komme uden scheme (`example.com` er helt
    // normalt at skrive). Rapport-siden genkender kun `/^https?:\/\//i`, så
    // `#url=` med en sådan værdi ville give præcis det tomme felt handoffen
    // er lavet for at fjerne. Målt mutation: `var dyb = !!url` på begge
    // scannerens sider gør dommen rød, fordi hverken EN eller DA scanner før
    // denne rettelse havde noget `forsteUrl`-krav — de tog bare `state.url`.
    if (t.path === 'site/scan.html' || t.path === 'site/scan-da.html') {
      const { fetchImpl: råFetch } = responses([
        { status: 200, body: { ...OK_SCAN_PROXY.body, url: 'example.com' } }]);
      const r = loadPage(t.path, råFetch,
        { match: /scan-proxy/, preload: ['site/scan-share-core.js'] });
      await r.sandbox.scan('example.com');
      await sleep(30);
      const råMarkup = (r.nodes.get('result') || {}).innerHTML || '';
      ok(`${t.label}: en adresse uden scheme falder til den gamle rute, ikke til et tomt felt`,
        !/#url=/.test(råMarkup) && /href="\/((?:da\/)?compliance-report)"/.test(råMarkup),
        'håndværket ville sende læseren til en rapport der aldrig genereres');
    }
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
//     4. Pro-boksen lover ikke en krybning, route `/api/report` ikke har.
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
    // Dom 4. Her lå der en dom, der krævede den **modsatte** påstand:
    // «crawls the whole site — the same check on every page it finds» skulle
    // stå i kortet i begge sprog. Målt 6/10 er den usand — `handleReport`
    // kalder `cscFetch` præcis én gang, så den læser én side og ser dens
    // svarheadere. Testen holdt altså løgnen i live. Nu dømmer den det samme
    // som `tools/check_scan_page_claims.py` dom 4: intet krybende verb **i
    // pro-kortet**, og den positive sætning om at læse siden fra serveren
    // skal være der — så en side kan heller ikke bare slette løftet og tie.
    //
    // Kun kortet måles. `#result` indeholder også ærlige **negationer** som
    // «One page per site … — not the whole site»; en hel-fil-søgning ville
    // være rød på en sand sætning. Det er præcis den afgrønsning dom 4 i
    // `check_scan_page_claims.py` gør med sin `proCard()`-udsnit.
    const kortStart = html.indexOf('pro-card');
    const kort = kortStart >= 0 ? html.slice(kortStart) : '';
    const kryb = lang === 'EN'
      ? /crawl\w*|whole site/i
      : /gennemgår|gennemløb|hele sitet/i;
    // Formuleringerne er pr. side («It reads the page from the server too» på
    // /scan, «It reads the page you name from the server» på
    // compliance-site-check), så dommen læser kernen — siden læser fra
    // serveren — og ikke hele sætningen.
    const laeserFraServeren = lang === 'EN'
      ? /reads the page[\s\S]{0,60}from the server/i
      : /læser (?:den side|siden)[\s\S]{0,60}fra serveren/i;
    ok(`${lang}: Pro-kortet ikke lover en krybning`,
      kortStart >= 0 && !kryb.test(kort),
      kortStart < 0 ? 'pro-card ikke fundet i #result' : kort.slice(0, 300));
    ok(`${lang}: Pro-kortet siger at Pro læser siden fra serveren`,
      laeserFraServeren.test(kort), kort.slice(0, 300));
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
      // Svarformen sender begge tal (site/_worker.js:3118 og :3125), så et
      // svar uden `pages_read` findes ikke i virkeligheden. Her læses alle seks
      // kald — så de to tal er lige, og dommen på «6 … læst» kan slås.
      pages_read: ['https://example.com/kontakt', 'https://example.com/privatliv',
        'https://example.com/terms', 'https://example.com/cookie',
        'https://example.com/imprint', 'https://example.com/om-os'],
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

// --------------------------------------------------------------------------
// 14. Compliance-generatorernes købsvej til den betalte skabelon.
//     `paid-templates.html` sælger DPA-skabelonen ($59), NIS2/DORA-klausursættet
//     ($49), EAA-erklæringen ($39) og rapport-kit'et ($69). Fire generatorer
//     laver præcis det output, to af de betalte filer svarer til — men de linkede
//     ingen vegne hen til dem: målt 1/10 linker pr. generator var 0 af 8 til
//     `/paid-templates`, og den eneste undtagelse (`nis2-gap-assessment-da`) så
//     *ikke* ud i den betalte vare, bare videre til siden.
//     Kortet hænger på `renderHTML(current) + UPSELL + DONATION`, altså i
//     resultatet og ikke i markup'en, og `renderText()` bygger kun fra
//     `renderHTML(current)` — så det kommer ikke med i det, brugeren kopierer.
// --------------------------------------------------------------------------
{
  const UP = [
    { f: 'dpa-generator.html', key: 'eucomply-dpa', pris: '$59', da: false },
    { f: 'dpa-generator-da.html', key: 'eucomply-dpa', pris: '$59', da: true },
    { f: 'nis2-incident-generator.html', key: 'eucomply-nis2-clauses', pris: '$49', da: false },
    { f: 'nis2-incident-generator-da.html', key: 'eucomply-nis2-clauses', pris: '$49', da: true },
    // 2/10: de tre generatorer der manglede resten. RoPA og
    // tilgængelighedserklæringen sælger den betalte udgave af præcis det de
    // selv skriver (DPA'en med bilag hhv. erklæringen som filer); privacy
    // notice har *ikke* en betalt udgave, så kortet sælger de dokumenter man
    // ellers skriver pr. kunde og siger det i første linje.
    { f: 'ropa-generator.html', key: 'eucomply-dpa', pris: '$59', da: false },
    { f: 'ropa-generator-da.html', key: 'eucomply-dpa', pris: '$59', da: true },
    { f: 'privacy-notice-generator.html', key: 'eucomply-template-bundle', pris: '$149', da: false },
    { f: 'privacy-notice-generator-da.html', key: 'eucomply-template-bundle', pris: '$149', da: true },
    { f: 'accessibility-statement-generator.html', key: 'eucomply-eaa-statement', pris: '$39', da: false },
    { f: 'tilgaengelighedserklaering-generator-da.html', key: 'eucomply-eaa-statement', pris: '$39', da: true },
  ];
  // Kortet skal *rendere*, ikke bare være en streng i filen: vi trækker de
  // `UPSELL +=`-linjer ud og kører dem i en vm, så en forkert quote eller en
  // uafsluttet streng gør dommen rød i stedet for at ligge død i markup'en.
  const render = (js) => {
    const sandbox = {};
    vm.createContext(sandbox);
    vm.runInContext(js.replace(/^var UPSELL/m, 'var UPSELL'), sandbox);
    return sandbox.UPSELL;
  };
  for (const u of UP) {
    const src = readFileSync(join(root, 'site', u.f), 'utf8');
    const start = src.indexOf('var UPSELL =');
    const end = src.indexOf("UPSELL += '</div>';", start);
    ok(`${u.f}: UPSELL-blokken findes og er afsluttet`, start > 0 && end > start,
      `start=${start} end=${end}`);
    if (start < 1 || end < start) continue;
    const js = src.slice(start, end + "UPSELL += '</div>';".length);
    let html = '';
    try { html = render(js); } catch (e) { html = 'RENDERFEJL: ' + e.message; }
    ok(`${u.f}: kortet renderer`, html.startsWith('<div') && html.endsWith('</div>'), html.slice(0, 120));

    // Prisen kommer fra katalogen, ikke fra hukommelsen — samme regel som
    // `tools/check_own_prices.py`, så de to porte ikke kan blive uenige.
    const cat = JSON.parse(readFileSync(join(root, 'tools/stripe_catalog.json'), 'utf8'));
    const key = u.key;
    ok(`${u.f}: pris og periode er katalogens`,
      html.includes(u.pris) && html.includes(u.da ? 'engang' : 'once'),
      `katalog: ${cat.products[key].price} (${cat.products[key].price_note})`);
    ok(`${u.f}: betalingslinket er katalogets`,
      html.includes(cat.products[key].payment_link)
      && html.includes(cat.products[key].payment_link.slice(cat.products[key].payment_link.indexOf('/') + 1)),
      `katalog: ${cat.products[key].payment_link}`);

    // `no-print` er hele pointen: uden den trykker brugeren salgsteksten med i
    // sit eget dokument, præcis som fejlen på `/scan` i forrige iteration.
    ok(`${u.f}: kortet skjuler sig i den trykte rapport`,
      html.includes('no-print'), 'upsell-kortet mangler no-print');
    // Og det skal hænge på resultatet, ikke i markup'en — ellers står det der
    // altid, også før brugeren har lavet noget.
    ok(`${u.f}: kortet hænger på resultatet, ikke i markup'en`,
      src.includes('renderHTML(current) + UPSELL + DONATION'),
      'skal være UPSELL mellem renderHTML(current) og DONATION');

    // Mutation: prisen og perioden på knappen skal kunne findes, ellers dømmer
    // dommen ingenting. Samme mønster som dom 13.
    const ord = u.da ? 'engang' : 'once';
    ok(`${u.f}: perioden står som sit eget ord i knappen`,
      new RegExp(`(^|[^a-zA-Z])${ord}([^a-zA-Z]|$)`).test(html.replace(/<[^>]+>/g, ' ')),
      `knappeteksten skal indeholde ordet «${ord}»`);
    const forkert = js.replace(u.pris, '$99').replace(ord, 'engangskob-uden-periode');
    const rForkert = render(forkert);
    ok(`mutation: ${u.f} forkeret pris/periode fanges`,
      !rForkert.includes(u.pris)
      && !new RegExp(`(^|[^a-zA-Z])${ord}([^a-zA-Z]|$)`).test(rForkert.replace(/<[^>]+>/g, ' ')),
      `mutationen gav stadig $59 eller perioden «${ord}»`);
  }
  // Copy-gate: kortet må ikke love noget, de andre sider modsiger. Bogen er
  // gratis og siger det syv gange; en købsvej til *bogen* ville være modsigende.
  // Vi sælger skabeloner og klausursæt, og de filer ligger i et separat repo.
  for (const f of UP.map((u) => u.f)) {
    const src = readFileSync(join(root, 'site', f), 'utf8');
    ok(`${f}: købsvejen sælger en skabelon, ikke bogen`,
      !/fZu9AScr9a6SbtA68vbMQ0b/.test(src), 'skal ikke pege på e-book-bundlet');
  }
  // Copy-gate 2: siden må ikke sige det modsatte af det kort den nu hænger.
  // `accessibility-statement-generator.html` sagde «If you only need the
  // statement, you never need to pay for anything», mens den samme side nu
  // sælger erklæringen som fil. Sætningen er erstattet; porten dømmer at den
  // ikke kan komme tilbage på nogen af siderne.
  for (const f of UP.map((u) => u.f)) {
    const src = readFileSync(join(root, 'site', f), 'utf8');
    ok(`${f}: siden modsiger ikke sit eget købskort`,
      !/never need to pay for anything/.test(src)
      && !/aldrig behøver at betale for noget/.test(src),
      'skal ikke love gratis, når siden sælger den samme vare');
  }
  // Og privacy notice har *ikke* en betalt udgave. Kortet skal sige det, ellers
  // er det en købsknap til noget siden siger er gratis.
  for (const f of ['privacy-notice-generator.html', 'privacy-notice-generator-da.html']) {
    const src = readFileSync(join(root, 'site', f), 'utf8');
    const start = src.indexOf('var UPSELL =');
    const html = render(src.slice(start, src.indexOf("UPSELL += '</div>';", start) + 20));
    ok(`${f}: kortet siger at der ingen betalt udgave af erklæringen findes`,
      /There is no paid version of this notice/.test(html)
      || /Der er ingen betalt udgave af denne erklæring/.test(html),
      'kortet skal indrømme at denne erklæring ikke sælges');
  }
}

// --------------------------------------------------------------------------
// 15. Kontrasttjekkeren *inde i* de to artikler, og kernen ét sted.
//     Målt 2/10 (Plausible 28 d): `/blog/text-on-image-contrast-check` var
//     mahope.tools' største indgangsside med 8 af 18 besøgende og **100 %
//     bounce** — alle otte forlod den igen, og 7 af dem nåede aldrig
//     `/text-on-image-checker`, som artiklen sendte dem videre til. Den
//     billigste retning på den trafik er at lade dem tjekke deres billede
//     uden at forlade siden.
//
//     Fire domme, alle falsifiable på den gamle kode:
//
//     1. Kernen ligger i ÉN fil, og ingen af de fire sider har en egen kopi
//        af `sampleContrast` — fire kopier af WCAG-formlen er fire steder,
//        hvor en rettelse kan glemmes.
//     2. Begge artikler *renderer et resultat*: `art-result` skriver en
//        ratio, en dom (PASS/FAIL) og et pro-kort, målt på den kode der
//        faktisk kører, ikke på markup'en.
//     3. Artiklens egen `href` i heroen peger på det indlejrede værktøj, så
//        læseren ikke sendes ud af siden for at gøre det han kom for.
//     4. Pro-kortet i artiklen peger på artiklens *egen* `#report`, ikke på
//        endnu et Stripe-link — artiklen har allerede sin købsvej med hele
//        tabellen, og to knapper til samme produkt er to valg uden et valg.
// --------------------------------------------------------------------------
{
  const KERNE = 'site/text-on-image-core.js';
  const ARTIKLER = [
    { side: 'site/blog/text-on-image-contrast-check.html', sprog: 'EN', anker: '#try-it',
      dom: 'Try it on your own image', set: 'PASS', fejl: 'FAIL', stoer: 'Try a darker/lighter text color' },
    { side: 'site/da/blog/tekst-paa-billede-kontrasttjek.html', sprog: 'DA', anker: '#prov-dit-billede',
      dom: 'Prøv det på dit eget billede', set: 'BESTÅET', fejl: 'IKKE BESTÅET', stoer: 'Prøv en mørkere/lysere tekstfarve' },
  ];
  const VAEKTOJER = ['site/text-on-image-checker.html', 'site/text-on-image-checker-da.html'];

  ok('kernen ligger i sin egen fil', existsSync(join(root, KERNE)), KERNE + ' mangler');
  // Dom 1. `sampleContrast` defineres i kernen og *kun* dér.
  const defineret = readFileSync(join(root, KERNE), 'utf8').match(/function sampleContrast\s*\(/g) || [];
  ok('kernen definerer sampleContrast præcis én gang', defineret.length === 1, `fandt ${defineret.length}`);
  for (const f of [...VAEKTOJER, ...ARTIKLER.map((a) => a.side)]) {
    const src = readFileSync(join(root, f), 'utf8');
    ok(`${f}: indlæser den delte kerne i stedet for at kopiere den`,
      /<script[^>]+src="\/text-on-image-core\.js"/.test(src), 'mangler <script src="/text-on-image-core.js">');
    ok(`${f}: har ingen egen kopi af WCAG-formlen`,
      !/function sampleContrast\s*\(/.test(src) && !/function lum\s*\(/.test(src),
      'siden definerer stadig lum/sampleContrast selv');
  }

  for (const a of ARTIKLER) {
    const src = readFileSync(join(root, a.side), 'utf8');
    // Dom 3. Ratcheten i `tools/first_action.json` dømmer denne forbindelse
    // også, men kun på *folden*. Her dømmes den anker, heroen faktisk peger på,
    // fordi en ratchet der er grøn mens artiklen sender læseren ud af siden
    // ville være en port der måler det forkerte.
    const hero = /<div class="hero-cta">([\s\S]*?)<\/div>/.exec(src);
    ok(`${a.sprog}: heroens primære handling er det indlejrede værktøj`,
      hero !== null && new RegExp(`<a href="${a.anker.replace('#', '\\#')}" class="btn-primary">`).test(hero[1]),
      hero === null ? 'ingen hero-cta' : hero[1].slice(0, 160));
    ok(`${a.sprog}: ankeret findes i artiklen`,
      new RegExp(`id="${a.anker.slice(1)}"`).test(src), `mangler id="${a.anker.slice(1)}"`);
    ok(`${a.sprog}: afsnittet har en overskrift læseren kan finde`,
      src.includes(a.dom), `mangler «${a.dom}»`);

    // Dom 2. Kører kernen og sidens egen `mount()` i sandkassen med et
    // læse-canvas, så `art-result` skriver det den ville skrive i en browser.
    const { nodes } = loadPage(a.side, responses([OK_SCAN]).fetchImpl,
      { match: /var PRO_CARD/, canvas: true, preload: [KERNE] });
    await sleep(30);
    const res = (nodes.get('art-result') || {});
    const markup = res.innerHTML || '';
    ok(`${a.sprog}: tjekkeren renderer et målt resultat`, res.hidden === false && /:\d|:1/.test(markup),
      `hidden=${res.hidden} markup=${markup.slice(0, 160)}`);
    ok(`${a.sprog}: resultatet dømmer i læserens eget sprog`,
      markup.includes(a.set) || markup.includes(a.fejl), 'ingen PASS/FAIL-bage i sit sprog');
    ok(`${a.sprog}: resultatet forklarer hvad der skal gøres ved et kravbrud`,
      markup.includes(a.stoer), 'ingen fejlvejledning');
    // Uden `<script>`-blokene — ellers er PRO_CARD's JS-streng i mount()-kallet
    // nok til at lyde som et kort der lå i sidens krop, og dommen ville være
    // grøn på den fejl den er skrevet imod.
    const krop = src.replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi, '');
    ok(`${a.sprog}: pro-kortet hænger på resultatet, ikke i markup'en`,
      markup.includes('pro-card') && !/class="pro-card"/.test(krop),
      'kortet skal først opstå når der er et resultat');
    // Dom 4. Artiklen har sin egen købsvej med tabellen; kortet skal pege på den.
    ok(`${a.sprog}: pro-kortet peger på artiklens egen købsvej, ikke på Stripe`,
      /href="#(report|rapport)"/.test(markup) && !/buy\.stripe\.com/.test(markup),
      'to købsknapper til samme produkt er to valg uden at vælge');
    ok(`${a.sprog}: donationslinjen er med, og er ikke en knap`,
      /donate\.stripe\.com/.test(markup) && !/<a[^>]*donate\.stripe\.com[^>]*class="btn/.test(markup),
      'donationen skal være en 13px-linje, ikke en knap');

    // Mutation: artiklen uden `mount()`-kaldet skal rødme. Uden denne linje
    // ville dom 2 være grøn på en side hvor `preload` alene nok fik kernen
    // indlæst — altså ville den ikke kunne se præcis den fejl den er skrevet
    // imod: et indlejret værktøj der ikke virker.
    const { nodes: d } = loadPage(a.side, responses([OK_SCAN]).fetchImpl,
      { match: /var PRO_CARD/, canvas: true, preload: [KERNE], source: src.replace("prefix: 'art-'", "prefix: 'skjult-'") });
    await sleep(20);
    ok(`mutation: ${a.sprog} artikel uden mount() fanges`,
      (d.get('art-result') || {}).hidden !== false, 'mutationen gav stadig et resultat');
  }
}

// --------------------------------------------------------------------------
// 16. Værktøjet sagde «try a darker colour» og lod læseren regne det ud.
//     Samme trafikgrund som sektion 15: `/blog/text-on-image-contrast-check` er
//     mahope.tools' største indgangsside (8 af 18 besøgende, 100 % bounce), og
//     den færdige måling *sluttede* med en ordre. WCAG-tallet stod der, men
//     den beslutning der skal følge — hvilken farve — lå hos læseren, og den
//     kræver at læse to tal samtidig (den lyseste og den mørkeste pixel).
//
//     Fire domme, alle falsifiable på den gamle kode:
//
//     1. `suggestFix()` returnerer en farve, der faktisk passerer mod **begge**
//        endepunkter — målt med kernens egen `ratio()`, ikke med en løsning
//        af en formel. Dømmes på ren JavaScript, så tallet kan efterprøves.
//     2. Den foreslåede farve er *bedre end rent sort eller hvid* på den
//        mellemlyseste baggrund: en designer skal kunne bruge den, og det er
//        præcis den fordel der gør knappen værd at trykke.
//     3. Den **gamle kode** fanger dømningen: samme domme mod den kørende
//        `text-on-image-core.js` fra før rettelsen skal være røde, ellers er
//        de grønne fordi de intet ser.
//     4. Alle fire sider har knappens tekst, og den er på **begge** sprog —
//        en dansk læser må ikke møde en engelsk knap i sit eget værktøj.
// --------------------------------------------------------------------------
{
  const KERNE = 'site/text-on-image-core.js';
  // Kør kernen i en tom kontekst: den skal kunne *regne* uden et canvas, så
  // dommen over matematikken ikke afhænger af en browser.
  const kern = readFileSync(join(root, KERNE), 'utf8');
  const sandkasse = { module: undefined, exports: undefined, Uint8ClampedArray };
  vm.createContext(sandkasse);
  vm.runInContext(kern, sandkasse);
  const Ti = sandkasse.TiContrast;

  ok('kernen eksporterer suggestFix()', !!(Ti && typeof Ti.suggestFix === 'function'),
    'TkContrast.suggestFix mangler — rettelsen kan ikke dømmes');
  if (Ti && typeof Ti.suggestFix === 'function') {
    // Den blanding læseren reelt ser efter en rettelse: et slør af farven `sc`
    // med dækning `a` over pixel `bg`. Samme formel som kernens `over()`.
    const over = (bg, sc, a) => bg.map((v, i) => [sc[0], sc[1], sc[2]][i] * a + v * (1 - a));

    // Dom 1 + 2. To *realistiske* billeder, fordi de to fejltyper er forskellige:
    //
    //   a) **Jævnt mellemlys baggrund** — en farve kan klare den alene, så
    //      rettelsen skal være en tekstfarve. Gråsort ville give 21:1 mod det
    //      mørke og 1,1:1 mod det lyse; hvid omvendt. Den foreslåede grå skal
    //      ligge *mellem* — hverken sort eller hvid, men den mindste mætning
    //      der stadig holder. Det er den fordel, der gør knappen værd at trykke.
    //   b) **Helt spredt baggrund** — en himmel der går fra næsten hvid til
    //      næsten sort. Her kan *ingen* tekstfarve bestå begge ende, så den
    //      eneste rigtige svar er det slør, værktøjet selv før bad om uden at
    //      finde dækningen: «prøv lidt mørkere». Det er den almindelige
    //      solopgang med en overskrift i bunden, altså ikke et hjørne.
    // Bemærk rækkefølgen: `bgMin` er det **mørkeste** og `bgMax` det **lyseste**
    // endepunkt, fordi det er `sampleContrast()`s `minC`/`maxC` der gives videre,
    // og de er navngivet efter *lystyrke*, ikke efter rækkefølge i billedet.
    const baggrunde = [
      // En baggrund der *ikke* spænder: her kan én tekstfarve klare begge ende,
      // så rettelsen skal være en farve. Gråsort giver 21:1 mod det mørke og
      // 1,1:1 mod det lyse, hvid omvendt — den foreslåede grå skal ligge
      // imellem, hverken sort eller hvid. Det er den fordel, der gør knappen
      // værd at trykke over «brug bare sort».
      { navn: 'jævnt mellemlys', bgMin: [180, 190, 205], bgMax: [235, 238, 242], forventer: 'color' },
      // En himmel der går fra næsten hvid til næsten sort. Her kan *ingen*
      // tekstfarve bestå begge ende, så det eneste rigtige svar er det slør,
      // værktøjet selv før bad om uden at finde dækningen: «prøv lidt mørkere».
      // Det er den almindelige solopgang med en overskrift i bunden.
      { navn: 'spredt (hvid mod sort)', bgMin: [22, 26, 34], bgMax: [235, 238, 242], forventer: 'scrim' },
      // Et *midtone*-billede — den type der er sværest at sætte tekst på, fordi
      // hverken sort eller hvid har nok kontrast. Ved 4,5:1 kan ingen tekstfarve
      // klare det, så svaret er et slør. Ved 3:1 (stor tekst) kan en grå det, så
      // rettelsen skal være en farve og ikke et slør, der ville skjule præcis det
      // billede bruteren ville beholde. Samme billede, to krav, to forskellige
      // svar — så en port der altid svarer «slør» eller altid «farve» er rød.
      { navn: 'midtone ved 4,5:1', bgMin: [96, 100, 108], bgMax: [120, 124, 130], forventer: 'scrim', kunVed: 4.5 },
      { navn: 'midtone ved 3:1 (stor tekst)', bgMin: [96, 100, 108], bgMax: [120, 124, 130], forventer: 'color', kunVed: 3 },
    ];
    for (const b of baggrunde) {
      for (const [navn, need] of [['4,5:1 normal tekst', 4.5], ['3:1 stor tekst', 3]]) {
        if (b.kunVed && b.kunVed !== need) continue;
        const fix = Ti.suggestFix(b.bgMin, b.bgMax, need, '#ffffff');
        ok(`suggestFix() finder en rettelse på ${b.navn} ved ${navn}`,
          fix && /^#[0-9a-f]{6}$/.test(fix.hex) && typeof fix.alpha === 'number',
          `fandt ${JSON.stringify(fix)}`);
        if (!fix || !/^#[0-9a-f]{6}$/.test(fix.hex)) continue;
        const rgb = Ti.hexToRgb(fix.hex);
        const sc = fix.scrim ? Ti.hexToRgb(fix.scrim) : null;
        // Dom 1: kravet er mod **begge** endepunkter. Kun den mørkeste var det,
        // den gamle kode og dens læsere så — og det er den der svætter mest.
        const modDunkelst = Ti.ratio(rgb, sc ? over(b.bgMax, sc, fix.alpha) : b.bgMax);
        const modLysest = Ti.ratio(rgb, sc ? over(b.bgMin, sc, fix.alpha) : b.bgMin);
        ok(`rettelsen passerer mod den mørkeste pixel på ${b.navn} ved ${navn}`,
          modDunkelst >= need, `${modDunkelst.toFixed(2)} < ${need} for ${JSON.stringify(fix)}`);
        ok(`rettelsen passerer mod den lyseste pixel på ${b.navn} ved ${navn}`,
          modLysest >= need, `${modLysest.toFixed(2)} < ${need} for ${JSON.stringify(fix)}`);
        // Dom 2. På den jævne baggrund skal svaret være en *tekstfarve*: et
        // slør dér ville skjule præcis det billede bruteren ville beholde, og
        // det er en dyrere rettelse end den kræver. Kun når ingen farve
        // består begge ende, er sløret det rigtige svar.
        ok(`${b.navn} rettes med ${b.forventer === 'color' ? 'en tekstfarve' : 'et slør'}, ` +
           `fordi ${b.forventer === 'color' ? 'én farve kan klare begge ende' : 'ingen farve kan det'}`,
          fix.kind === b.forventer, `foreslog ${JSON.stringify(fix)}`);
        if (fix.kind === 'color') {
          ok('den foreslåede farve er hverken sort eller hvid',
            fix.hex !== '#000000' && fix.hex !== '#ffffff',
            `foreslog ${fix.hex} — så er der ingen fordel ved knappen over «brug sort»`);
          // Dom 2b. Den skal være den *mindste* indgrebne rettelse, ikke bare
          // en der består. En tekstfarve der er meget mørkere end nødvendigt
          // består alle «består den»-domme og er stadig en dårlig rettelse: den
          // ser ud som om bruteren har fået sort skrift, og det er præcis den
          // fordel knappen skal fjerne — at man slipper for at gætte.
          //
          //   Målt 3/10: mutationen der regner i kanalværdi i stedet for
          //   lystyrke gav #121212 med 9.98:1 ved et krav på 4.5 — den består
          //   *alle* de andre domme her, fordi den bare er for mørk. Uden
          //   denne dom ville porten være grøn på en kern der fjerner hele
          //   pointen med knappen.
          const margin = Math.min(modDunkelst, modLysest) / need;
          ok('den foreslåede farve ligger tæt på kravet (maks 1,5×)',
            margin <= 1.5,
            `${fix.hex} giver ${Math.min(modDunkelst, modLysest).toFixed(2)}:1 = ${margin.toFixed(2)}× kravet ved ${need}:1`);
        }
        // Den dækning der foreslås skal være den *mindste* der virker, ikke en
        // tilfældig: 1 % mindre skal fejle igen. Ellers lå knappen bare kunne
        // have gjort sløret mørkere, og det er den beslutning den skulle tage.
        //
        // Minimum tages over **begge** ende, ikke over ét. Det er den fælde der
        // lå i mit første forsøg: et hvidt slør over en *lys* baggrund gør den
        // lysere, så sort tekst får *bedre* kontrast med dækningen — og sløret
        // begrænses i stedet af den mørke ende. En dom der kun testede den lyse
        // ville have erklæret den mindste dækning for ikke at være minimal,
        // fordi den lyse ende netop ikke er den der binder.
        if (fix.kind === 'scrim' && fix.alpha > 0.01) {
          const a = fix.alpha - 0.01;
          const mindre = Math.min(Ti.ratio(rgb, over(b.bgMin, sc, a)), Ti.ratio(rgb, over(b.bgMax, sc, a)));
          ok('den foreslåede dækning er den mindste der virker (1 % mindre fejler)',
            mindre < need, `${Math.round(fix.alpha * 100)} % er ikke minimal — ${mindre.toFixed(2)} ved minus 1 %`);
          // Og modsat: den skal også *virkelig* holde, med al den afrunding en
          // hel procent indebærer. En dækning der rundes ned ville se pænere
          // ud i tallet og så fejle igen.
          const ved = Math.min(Ti.ratio(rgb, over(b.bgMin, sc, fix.alpha)), Ti.ratio(rgb, over(b.bgMax, sc, fix.alpha)));
          ok('den foreslåede dækning holder efter afrunding til hel procent',
            ved >= need, `${ved.toFixed(2)} < ${need} for ${Math.round(fix.alpha * 100)} %`);
        }
      }
    }

    // `lumToChannel(L)` er den inverse af `lum()`. De to er *ikke* det samme
    // tal: `lum([128,128,128])` er 0.216, ikke 0.502. Uden inversen regner
    // kernen i lystyrke og bruger resultatet som kanalværdi, så den foreslåede
    // farve bliver dobbelt så mørk som den tærskel den skal klare — og
    // dommen ville være grøn, fordi den måler `ratio()` i lystyrke-rum.
    ok('kernen eksporterer lumToChannel() som den inverse af lum()',
      typeof Ti.lumToChannel === 'function', 'lumToChannel mangler');
    if (typeof Ti.lumToChannel === 'function') {
      let rundt = true;
      for (const L of [0.02, 0.1, 0.216, 0.5, 0.85, 1]) {
        const c = Ti.lumToChannel(L);
        if (Math.abs(Ti.lum([c, c, c]) - L) > 1e-3) rundt = false;
      }
      ok('lumToChannel() og lum() er hinandens inverse (6 lysstyrker, 1e-3 tolerance)',
        rundt, 'rundturen holder ikke — kernen regner i to forskellige rum');
    }

    // Dom 3. Den gamle kode, målt gennem samme sandkasse. `suggestFix` blev
    // tilføjet 3/10, så på `fbbd0a7` er den enten fraværende eller ubrugt;
    // begge dele skal give røde domme, ikke en grøn der skyldes en fejl.
    const gammel = execFileSync('git', ['show', 'fbbd0a7:site/text-on-image-core.js'],
      { cwd: root, encoding: 'utf8' });
    const gammelSandkasse = { module: undefined, exports: undefined, Uint8ClampedArray };
    vm.createContext(gammelSandkasse);
    vm.runInContext(gammel, gammelSandkasse);
    const gammelTi = gammelSandkasse.TiContrast;
    ok('mutation: den gamle kode har ingen suggestFix() at dømme',
      !(gammelTi && typeof gammelTi.suggestFix === 'function'),
      'mutationen gav stadig en funktion — dommen kan ikke se forskel');
    // Og den skal heller ikke have knappen: det er den del bruteren ser.
    const gammelEN = execFileSync('git', ['show', 'fbbd0a7:site/text-on-image-checker.html'],
      { cwd: root, encoding: 'utf8' });
    ok('mutation: den gamle side tilbød ingen «fix»-knap',
      !/fixBtn:/.test(gammelEN), 'mutationen havde allerede knappen');
  }

  // Dom 4. Knappens tekst ligger på *siden*, i hvert sprog — fordi kernen er
  // delt, og en knap der stod i kernen ville være engelsk på den danske side.
  for (const [f, forventet] of [
    ['site/text-on-image-checker.html', 'Fix it — set the text color for me'],
    ['site/blog/text-on-image-contrast-check.html', 'Fix it — set the text color for me'],
    ['site/text-on-image-checker-da.html', 'Fiks det — sæt tekstfarven for mig'],
    ['site/da/blog/tekst-paa-billede-kontrasttjek.html', 'Fiks det — sæt tekstfarven for mig'],
  ]) {
    const src = readFileSync(join(root, f), 'utf8');
    ok(`${f}: har knappens tekst i sit eget sprog`,
      src.includes(`fixBtn: '${forventet}'`), `mangler fixBtn: '${forventet}'`);
    // Slør-rettelsen har sin egen sætning. Uden den ville en spredt baggrund
    // vise den *engelske* `fixed`-linje under et tal, der blev målt med et
    // slør, den danske læser ikke kan se forklaret.
    //
    // To nøgler, ikke én: kernen prøver slør i begge retninger (sort baggrund
    // med lys tekst, hvid baggrund med mørk tekst) og vælger den mindste
    // dækning, så på et lyst billede vinder det *hvide*. Én nøgle med ordet
    // «mørkt» i sig ville være en løfte der kun holder for halvdelen af
    // billederne — målt 3/10 i review af den første udgave af denne diff.
    for (const noegle of ['fixedScrimDark', 'fixedScrimLight']) {
      ok(`${f}: har også teksten til slør-rettelsen (${noegle})`,
        new RegExp(`${noegle}: '[^']*%s[^']*'`).test(src), `mangler ${noegle} med %s`);
    }
    // Kernen skal *vælge* mellem dem, ellers er den anden nøgle død tekst,
    // og dommen ovenfor ville være grøn fordi den kun tæller tilstedeværelse.
    ok(`${f}: kernen vælger slør-retning efter lagets lyshed`,
      kern.includes('s.fixedScrimDark') && kern.includes('s.fixedScrimLight') &&
      kern.includes('lum(hexToRgb(f.scrim)) < 0.5'),
      'kernen bruger ikke begge nøgler');
    // Knappen skal kunne virke: kernen binder den på `[data-ti-fix]`, så
    // uden den attribut er der en knap der intet gør.
    ok(`${f}: kerne og knap hænger sammen på data-ti-fix`,
      kern.includes('data-ti-fix') && kern.includes("res.querySelector('[data-ti-fix]')"),
      'kernen binder ikke den knap den skriver');
    // 44 px: målt 3/10 i Chromium ved 390 px. `.btn-secondary` har kun
    // padding, så uden `min-height` er knappen 42 px — under de 44 px resten
    // af sitet bruger, og målt på en telefon.
    const css = readFileSync(join(root, 'site/style.css'), 'utf8');
    ok('knappen er mindst 44 px høj (min-height:44px + centreret indhold)',
      /\.ti-fix\s*\{[^}]*min-height:\s*44px[^}]*\}/.test(css) &&
      /\.ti-fix\s*\{[^}]*align-items:\s*center/.test(css),
      '.ti-fix mangler min-height:44px eller align-items:center');
  }
}

// --------------------------------------------------------------------------
// 17. «Fiks det» må ikke slå på det næste foto.
//
// Målt 3/10 i rigtig Chromium: en bruger lægger tre fotos i træk (det er præcis
// hvad værktøjet er til), trykker «Fix it» på det første og ser på det tredje at
// tallet står på 1,52:1 med en forklaring om et 13 % mørkt lag — et lag der
// var beregnet til et *andet* billedes endepunkter. Tre ting var sande på én
// gang og ingen af dem rigtige: sløret lå stadig tegnet på foto B, så tallet var
// ikke en måling af det brugeren havde lavet; `.ti-fixed`-teksten beskrev et lag
// brugeren ikke kunne se i tallet; og den sagde «ryd det med farvefeltet
// ovenfor» — som er præcis den handling der *sletter* sløret og nulstiller
// målingen til 1,13:1, altså den rettelse den beder om gør billedet dårligere.
//
// Kernen nulstillede `scrim` og `lastFix` i *farve*- og *fontsize*-handlerne,
// altså i to af de fire veje ind i `updateAll()`. Billedskiftet var den tredje.
//
// Dommen er *sekventiel* gennem den samme `mount()`: `check_contrast_sampling.py`
// kører uden browser og dømmer ét billede pr. kald, så den kan ikke se det.
// --------------------------------------------------------------------------
{
  const KERNE = 'site/text-on-image-core.js';
  const SIDE = 'site/text-on-image-checker.html';
  // Foto A: baggrunden spænder fra næsten sort til næsten hvid, så ingen
  // tekstfarve kan klare begge ende og rettelsen *er* et slør — den vej der så
  // tegnes. Kernels søgning vælger det *hvide* lag her, fordi det dækker mindst,
  // og det sætter tekstfarven til sort. Foto B: et smallere, men stadig
  // spredt område der fejler med både sort og hvid tekst, så der igen *er* en
  // rettelse at tilbyde — altså skal knappen dukke op igen, og tallet skal være
  // B's egen måling. En jævnmidtone kan ikke bruges: en sådan består altid med
  // enten sort eller hvid ved 4,5:1, så den ville aldrig nå at vise et tal der
  // afhænger af om sløret fra A stadig lå over den.
  const A = { a: [20, 22, 28], b: [235, 238, 242] };
  const B = { a: [96, 100, 108], b: [150, 152, 156] };

  // Én `mount()`, trin for trin: et tal i rækken er et billede, `'fix'` er et
  // tryk på den knap kernen lige skrev, `farve:#…` er bruterens eget farvevalg.
  // `loadPage` kører sidens egen `mount()`-kald, så der er ingen anden vej ind —
  // testen gør præcis det en bruger gør, og rettelsen skal ske *mellem* to fotos,
  // som i fundet.
  async function foer(steps) {
    const { nodes } = loadPage(SIDE, responses([]).fetchImpl,
      { match: /TiContrast\.mount/, canvas: true, levendeBilleder: true, preload: [KERNE] });
    await sleep(20);
    for (const step of steps) {
      if (step === 'fix') { nodes.get('result').querySelector('[data-ti-fix]').click(); continue; }
      if (typeof step === 'string' && step.startsWith('farve:')) {
        const felt = nodes.get('fg');
        felt.value = step.slice(6);
        felt.fire('input');
        continue;
      }
      saetBillede(step);
      const input = nodes.get('file');
      input.files = [{ type: 'image/png' }];
      input.fire('change');
    }
    return nodes;
  }
  const resultat = (nodes) => (nodes.get('result') || {}).innerHTML || '';
  const tallet = (markup) => {
    const m = /<strong>(\d+(?:[.,]\d+)?):1<\/strong>/.exec(markup);
    return m ? m[1] : null;
  };
  // Kernens egen formel på B's *egen* pixel, med den tekstfarve rettelsen på A
  // efterlod — så forventningen er ikke en håndskrevet optimum, og dommen er
  // ikke afhængig af hvilken retning sløret vandt i.
  const forventet = (hex, px) => {
    const lum = (rgb) => {
      const c = rgb.map((v) => {
        v /= 255;
        return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
      });
      return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2];
    };
    const h = hexToRgb(hex);
    // Worst case: mod både ender, præcis som `sampleContrast()` gør.
    return Math.min(...[px.a, px.b].map((p) => {
      const l1 = lum(h), l2 = lum(p);
      const [a, z] = l1 < l2 ? [l2, l1] : [l1, l2];
      return (a + 0.05) / (z + 0.05);
    }));
  };
  const hexToRgb = (h) => {
    const s = String(h).replace('#', '');
    return [0, 2, 4].map((i) => parseInt(s.slice(i, i + 2), 16));
  };

  // (1) Foto A alene, så tryk. Rettelsen skal *være* et slør, ellers måler dommen
  //     en veje kernen ikke kan slå fra. Og den skal flytte tallet, så en fejl der
  //     nulsiller sløret uden at røre billedet ikke kan være grøn her.
  const a = await foer([A]);
  const markupA = resultat(a);
  ok('foto A fejler 4,5:1 og får en «Fix it»-knap',
    /data-ti-fix/.test(markupA), `markup=${markupA.slice(0, 120)}`);
  const foerFix = tallet(markupA);
  a.get('result').querySelector('[data-ti-fix]').click();
  const markupEfterFix = resultat(a);
  ok('«Fix it» på foto A flytter målingen og fortæller hvad den gjorde',
    tallet(markupEfterFix) !== foerFix && /class="ti-fixed"/.test(markupEfterFix) &&
    /\d+ % (dark|light) layer/.test(markupEfterFix),
    `før=${foerFix} efter=${tallet(markupEfterFix)} fixed=${/class="ti-fixed"/.test(markupEfterFix)}`);

  // (2) Foto B i samme mount, efter rettelsen på A. Alt tre ting fra fundet skal
  //     være væk: sløret må ikke tegnes på B, beskrivelsen af rettelsen må ikke stå
  //     under et tal der ikke stammer fra den, og knappen skal dukke op igen fordi
  //     B igen fejler. Tallet måles mod kernens egen formel på *B's* pixel, så
  //     dommen kan ikke være grøn fordi den læser et hvilket som helst tal.
  const b = await foer([A, 'fix', B]);
  const markupB = resultat(b);
  const renB = tallet(markupB);
  const rigtigB = forventet(b.get('fg').value, B).toFixed(2);
  ok('foto B måles på sit *eget* billede, ikke på sløret fra foto A',
    renB === rigtigB,
    `viste ${renB}:1, kernen siger ${rigtigB}:1 for ${b.get('fg').value} på rgb(${B.a})/rgb(${B.b})`);
  ok('beskrivelsen af rettelsen på foto A er væk, da foto B er målt',
    !/class="ti-fixed"/.test(markupB), `stadig: ${(markupB.match(/class="ti-fixed">[^<]*/) || [''])[0]}`);
  ok('«Fix it» dukker op igen på foto B',
    /data-ti-fix/.test(markupB), `markup=${markupB.slice(0, 120)}`);

  // (3) Samme foto B med *samme* tekstfarve i en frisk mount, uden nogen rettelse.
  //     Tallet skal være præcis det fra (2) — det er den direkte dom på at
  //     rettelsen på A ikke har sat spor i B's måling. Uden denne linje kunne
  //     dommen være grøn på en kjerne der maler et andet tal end forventet, blot
  //     et fast, så længe (2) havde noget at være forkert med.
  const kunB = await foer(['farve:#000000', B]);
  ok('foto B måles identisk med og uden en tidligere rettelse i samme mount',
    tallet(resultat(kunB)) === renB,
    `ren=${tallet(resultat(kunB))} efter A=${renB}`);
}

// --------------------------------------------------------------------------
// «Sider læst» skal være det tal listen kan efterprøve — ikke antallet kald.
// --------------------------------------------------------------------------
// `pages_checked` er antallet *kald* og medtager 404'er, fordi et kald der
// svarer 404 også er et kald (site/_worker.js:3119-3124). `pages_read` er
// listen kunden kan se. Overblikket skrev før dette det første tal under
// ordene «pages read» / «sider læst», mens `<details>` lige under viste det
// andet — så samme ord med to tal i en rapport der sendes videre til en kunde.
const MISMATCH = {
  ok: true, url: 'https://example.com', scanned_url: 'https://example.com/',
  score: 90, grade: 'A', passed: 9, total: 10, results: {},
  // 9 kald, hvor 4 svarede 404: kun 5 sider blev læst.
  pages_checked: 9,
  pages_read: ['https://example.com/', 'https://example.com/privatliv',
    'https://example.com/terms', 'https://example.com/cookie', 'https://example.com/imprint'],
};

async function scanResultsHtml(path, source) {
  const { fetchImpl } = responses([{ status: 200, body: MISMATCH }]);
  const { sandbox, nodes } = loadPage(path, fetchImpl, source ? { source } : {});
  nodes.get('urlInput').value = 'example.com';
  await sandbox.scan();
  await sleep(30);
  return (nodes.get('results') || {}).innerHTML || '';
}

for (const [path, ord] of [['site/compliance-site-check.html', 'pages read'], ['site/da/compliance-site-check.html', 'sider læst']]) {
  const html = await scanResultsHtml(path);
  ok(`${path.includes("/da/") ? "DA" : "EN"}: «sider læst» er de 5 læste sider, ikke de 9 kald`,
    new RegExp(`5 ${ord}`).test(html) && !new RegExp(`9 ${ord}`).test(html),
    ` fandt: ${(html.match(new RegExp(`[^·]{0,24}${ord}[^<]{0,12}`, 'g')) || []).join(' | ') || '—'}`);

  // Polaritet: samme dom på den gamle kode. Mutationen genskaber præcis det
  // felt den gamle linje læste, i den rigtige fil — ikke en håndskrevet kopi.
  const egen = readFileSync(join(root, path), 'utf8');
  const gammel = egen.replace('var laeste = (data && data.pages_read) || [];',
    'var laeste = { length: data.pages_checked };');
  ok(`${path.includes("/da/") ? "DA" : "EN"}: mutationen (pages_checked) er fanget`,
    gammel !== egen && new RegExp(`9 ${ord}`).test(await scanResultsHtml(path, gammel)),
    'mutationen gav ikke det gamle tal, så dommen kan ikke se forskellen');
}

// --------------------------------------------------------------------------
// En skannet adresse må ikke skrive markup i vores egen resultatside.
// --------------------------------------------------------------------------
// Kæden er tre led: `handleScanProxy` lægger målets *egen* `Content-Type` ind
// i `error`, `scan()` kaster den videre som `new Error(data.error)`, og
// fejlkassen skriver `e.message` i `#result`'s `innerHTML`. Et mål der svarer
// `Content-Type: application/json<img src=x onerror=…>` fik derfor sit eget
// markup til at køre i mahope.tools' origin — og `#url=`-læseren kalder
// `scan(u)` ved sideindlæsning, så offerret ikke engang trykker på noget.
// Målt i rigtig Chromium før rettelsen: `<title>FIRET</title>` i DOM'en.
const FIJLT = 'application/json<img src=x onerror=alert(1)>';

async function scanFejlHtml(path, source) {
  const { fetchImpl } = responses([{
    status: 400,
    // Den *rå* header, ufiltreret. Workerens `safeContentType()` er et lag for
    // sig, men dommen skal måle at klienten kan klare sig uden det — ellers
    // ville den være grøn, fordi filteret allerede var slået til.
    body: { ok: false, error: `Target returned ${FIJLT} — not an HTML page. Only HTML pages can be scanned.` },
  }]);
  const { sandbox, nodes } = loadPage(path, fetchImpl, {
    match: /scan-proxy/, preload: ['site/scan-share-core.js'], ...(source ? { source } : {}),
  });
  await sandbox.scan('https://ondt.example/');
  await sleep(30);
  return (nodes.get('result') || {}).innerHTML || '';
}

for (const [path, lang] of [['site/scan.html', 'EN'], ['site/scan-da.html', 'DA']]) {
  const html = await scanFejlHtml(path);
  // Fejlens egen afsnit skal være ren tekst. Det afsnit skriver siden selv med
  // sin egen `<p …>`, så indholdet imellem må ikke have *et eneste* rått
  // `<` — så ved vi at målets header ikke har skrevet et element, uanset
  // hvilket tag det måtte have valgt. Ordet `onerror` står gerne i den escaped
  // tekst, så det kan ikke være dommen.
  const afsnit = (html.match(/<p style="color:#667;font-size:14px">([\s\S]*?)<\/p>/) || ['', ''])[1];
  ok(`scan ${lang}: fejlens egen afsnit er ren tekst, intet rått '<'`,
    afsnit.length > 0 && !afsnit.includes('<'), ` fandt: ${(afsnit.match(/[^·]{0,30}/) || ['—'])[0]}`);
  ok(`scan ${lang}: målets egen markup skriver ingen img-tag i hele resultatet`,
    !/<img/i.test(html), ` fandt: ${(html.match(/<img[^>]*>/i) || ['—'])[0]}`);
  ok(`scan ${lang}: fejlen står som escaped tekst, så læseren kan se typen`,
    html.includes('&lt;img') && html.includes('application/json'),
    ` fandt: ${(html.match(/[^·]{0,30}application\/json[^<]{0,40}/) || ['—'])[0]}`);

  // Polaritet: samme dom på den gamle kode. Mutationen fjerner præcis det `esc`-
  // kald rettelsen tilføjede, i den rigtige fil — ikke en håndskrevet kopi.
  const egen = readFileSync(join(root, path), 'utf8');
  const gammel = egen.replace(`esc(e.message)`, `e.message`);
  ok(`scan ${lang}: mutationen (uden esc) er fanget`,
    gammel !== egen && /<img/i.test(await scanFejlHtml(path, gammel)),
    'mutationen gav ikke den gamle kode, så dommen kan ikke se forskellen');
}

// --------------------------------------------------------------------------
// Ét kald ad gangen. «Scan now» koster nu fem sider pr. tryk, og `rateLimitIp`
// tæller **én** slot pr. side — så et dobbeltklik brænder ti af de 60 timer i
// timen. `revealResult` skriver det andet resultat oven i det første, så
// læseren så ét svar og ingen fejl, hvilket er værre end at se fejlen.
//
// Dommen måler **antallet kald til `/scan-proxy`**, ikke antallet gange
// `scan()` blev kaldt: en lås der bare returnerer tidligt uden at tælle
// noget ville være grøn på «knappen låses», men den brænder stadig kvote.
// Svaret kommer først efter en tick, fordi et dobbeltklik i virkeligheden er
// to kald der ligger samtidig — ellers ville den anden submit nå at køre
// efter den første var færdig, og dommen ville være grøn på koden uden lås.
// --------------------------------------------------------------------------
async function dobbeltklikPaaScan(path, source, knapTekst) {
  const kald = [];
  const svar = { ok: true, url: 'https://example.com', html: '<html lang="en"><head><title>Example</title></head><body><h1>Example</h1></body></html>' };
  const fetchImpl = async (u) => {
    kald.push(String(u));
    await sleep(30);
    return { ok: true, status: 200, json: async () => svar };
  };
  const { sandbox, nodes } = loadPage(path, fetchImpl,
    { match: /scan-proxy/, preload: ['site/scan-share-core.js'], memoQSelector: true, ...(source ? { source } : {}) });
  // Formularens knap er den eneste vej en læser har. Sandkassen læser ikke
  // knappens tekst fra HTML'en, så den sættes her — ellers ville «får sin
  // egen tekst tilbage» være grøn på en knap der aldrig havde haft en.
  const knap = sandbox.document.getElementById('scanForm').querySelector('button');
  knap.textContent = knapTekst;
  sandbox.document.getElementById('url').value = 'https://example.com/\nhttps://example.com/kontakt';
  sandbox.document.getElementById('scanForm').fire('submit');
  await sleep(10);                 // midt i kaldet: knappen skal være låst
  const laast = knap.disabled === true;
  const undervejsTekst = (knap.textContent || '').trim();
  const undervejs = kald.length;
  sandbox.document.getElementById('scanForm').fire('submit');   // samme finger igen
  await sleep(90);
  return {
    kald: kald.filter((u) => u.includes('/scan-proxy')).length,
    undervejs, laast, undervejsTekst,
    tekst: (knap.textContent || '').trim(),
    resultat: (nodes.get('result') || {}).innerHTML || '',
  };
}

for (const [path, lang, knapTekst, undervejsTekst] of [
  ['site/scan.html', 'EN', 'Scan now', 'Scanning…'],
  ['site/scan-da.html', 'DA', 'Scan nu', 'Scanner …'],
]) {
  const r = await dobbeltklikPaaScan(path, null, knapTekst);
  ok(`scan ${lang}: et dobbeltklik sender ét kald, ikke to`,
    r.kald === 1, `kald=${r.kald} (forventet 1); undervejs=${r.undervejs}`);
  ok(`scan ${lang}: den anden trykning sker mens det første svar er i luft`,
    r.undervejs === 1, `undervejs=${r.undervejs} (forventet 1)`);
  ok(`scan ${lang}: knappen er låst mens kaldet er i luft`, r.laast);
  ok(`scan ${lang}: den låste knap siger at den arbejder`,
    r.undervejsTekst === undervejsTekst, `fandt: «${r.undervejsTekst}»`);
  ok(`scan ${lang}: knappen får sin egen tekst tilbage`, r.tekst === knapTekst,
    `fandt: «${r.tekst}»`);
  ok(`scan ${lang}: resultatet er en færdig scorecard, ikke «Scanning …»`,
    r.resultat.includes('class="scorecard"'), `fandt: ${(r.resultat.match(/Scanning[^<]{0,30}/) || ['(tomt)'])[0]}`);

  // Polaritet: mutationen fjerner præcis låsen i den rigtige fil — ikke en
  // håndskrevet kopi af den gamle side. Uden den ville dommen være grøn på
  // en side hvor låsen aldrig har været. Kun antallet kald er målingen her:
  // to sideløbende kald sætter begge knappens tekst, så hvilken der gendanner
  // den sidst er en rækkefølge-egenskab ved et kald der alligevel er en fejl.
  const egen = readFileSync(join(root, path), 'utf8');
  const gammel = egen.replace(/if\(scanILuft\) return scanILuft;/, '');
  const m = gammel !== egen ? await dobbeltklikPaaScan(path, gammel, knapTekst) : null;
  ok(`scan ${lang}: mutationen (uden lås) er fanget`,
    !!m && m.kald === 2,
    `mutationen gav ikke den gamle kode, så dommen kan ikke se forskellen: ${m ? `kald=${m.kald}` : 'ingen kode'}`);
}

// --------------------------------------------------------------------------
// Fingeren skal kunne trække teksten.
//
// Målt 3/10 i Chromium 153 ved 390 px: `touchstart` flyttede teksten ét sted,
// og seks `touchmove` ændrede intet. Alle fire sider lover dog «(or drag)» /
// «(eller træk)» i teksten under billedet — altså sand på en mus, falsk på en
// telefon, som er den enhed størstedelen af læserne af artiklen bruger. Samme
// måling fandt at `touchstart`'s `preventDefault()` låste scrolling med fingeren
// oven på billedet.
//
// Dommen her læser den **tegnede** placering (`fillText` i canvas-stubben), fordi
// det er den eneste der svarer på «flyttede fingeren teksten»: et tal i en
// variabel er kernens egen påstand om sig selv. Mutationsdommen nedenfor kører
// den *gamle* kode gennem samme sandkasse, så en port der ikke kan se
// forskellen på de to, bliver rød i stedet for grøn på løgnen.
{
  const KERNE = 'site/text-on-image-core.js';
  const SIDE = 'site/text-on-image-checker.html';

  // Én `mount()` pr. scenarie, som `loadPage` gør: sidens eget mount-kaldes
  // strings og markup, ikke en håndfuld funktioner. `st.tekst` er den tegnede
  // tekst; den sidste indgang er blok 1 (`drawTextLayer(1)` tegner blok 2 bagefter).
  async function kørMed(gester, kilder) {
    const { nodes, st } = loadPage(SIDE, responses([]).fetchImpl,
      { match: /TiContrast\.mount/, canvas: true, levendeBilleder: true, preload: [KERNE], kilder });
    await sleep(20);
    const cv = nodes.get('cv');
    const log = [];
    const finger = (type, x, y) => {
      const t = { clientX: x, clientY: y, identifier: 1, target: cv };
      log.push(type);
      cv.fire(type, {
        // `touches` er tomt ved `touchend`, præcis som i en browser — så en dom
        // der læser `touches[0]` der får `undefined` og dør, ligesom kernen
        // gør det hvis den glemmer `changedTouches`.
        touches: type === 'touchend' || type === 'touchcancel' ? [] : [t],
        changedTouches: [t],
        cancelable: true,
        preventDefault() { log.push('preventDefault'); },
      });
    };
    gester(finger, cv);
    await sleep(10);
    // Blok 1 og blok 2 tegnes i samme `draw()`, så den *sidste* `fillText` er
    // blok 2 — og dens y er fast, uanset hvor fingeren har været. Vi vil have
    // blok 1, så dommen leder den op på **sides egen tekst** i tekstfeltet og
    // ikke på rækkefølgen af to tegninger.
    const min = nodes.get('text').value;
    const eg = (st.tekst || []).filter((t) => t[0] === min).pop() || [];
    return { nodes, st, log, x: eg[1], y: eg[2], tegnet: st.draws || 0 };
  }
  // Den nuværende kode, som alt annet i filen.
  const kør = (gester) => kørMed(gester, null);

  // `pos()` lægger teksten med sit **øverste venstre** hjørne ved fingeren minus
  // halve skriftstørrelsen, så den tegnede placering er fingeren minus 27 px i
  // en 900 px bred flade: `fontSizePx()` er `max(18, 0.06 * bredden)`. Tallet
  // står her eksplicit, for et tal der *ligner* rigtigt er ikke en dom.
  const FS = 54;
  const vedFinger = (v, finger) => Number.isFinite(v) && Math.abs(v - (finger - FS / 2)) <= 2;

  // Fingeren ned og op uden at flytte sig: 3/10 flyttede teksten i `touchstart`,
  // så et tryk skal stadig gøre det. Bevaringsdom.
  const tryk = await kør((f) => { f('touchstart', 200, 120); f('touchend', 200, 120); });
  ok('tryk på billedet flytter teksten (finger ned og op samme sted)',
    tryk.tegnet > 0 && vedFinger(tryk.x, 200) && vedFinger(tryk.y, 120),
    `tegnet=${tryk.tegnet} tekst=[${tryk.x}, ${tryk.y}] log=${tryk.log.join(',')}`);

  // Trækket: fingeren ned i venstre side og **vandret** hen i højre side. Den
  // gamle kode flyttede teksten til nedtrykningsstedet og lod resten ligge —
  // så dommen er den der dømmer den løgn.
  const traek = await kør((f) => {
    f('touchstart', 100, 120);
    for (let i = 1; i <= 6; i++) f('touchmove', 100 + i * 100, 120);
    f('touchend', 700, 120);
  });
  ok('træk med fingeren flytter teksten med fingeren, ikke kun ved nedtryk',
    traek.tegnet > 0 && vedFinger(traek.x, 700) && vedFinger(traek.y, 120),
    `tekst=[${traek.x}, ${traek.y}] log=${traek.log.join(',')}`);

  // Scrolling er bruterens, ikke vores. Et **lodret** fingerstræk over billedet
  // skal derfor hverken flytte teksten eller tage scrollen: det er præcis den
  // bevægelse en læser gør for at komme videre ned ad siden, og 3/10 låste den
  // helt. Dommen på `preventDefault` er derfor den egentlige: at *ikke* flytte
  // tekst uden at låse scrollen er hele pointen med den lodrede undtagelse.
  const lodret = await kør((f) => {
    f('touchstart', 400, 100);
    for (let i = 1; i <= 6; i++) f('touchmove', 400, 100 + i * 40);
    f('touchend', 400, 340);
  });
  ok('lodret fingerstræk lader siden scroll(e) og flytter ikke teksten',
    lodret.log.includes('touchstart') && !lodret.log.includes('preventDefault'),
    `log=${lodret.log.join(',')}`);

  // Et afbrudt træk må ikke efterlade kernen i en tilstand hvor næste tryk
  // ignoreres — det er den fejl en `touchcancel`-handler uden nulstilling giver.
  const afbrudt = await kør((f) => {
    f('touchstart', 300, 100);
    f('touchmove', 500, 100);
    f('touchcancel', 500, 100);
  });
  const efter = await kør((f) => { f('touchstart', 700, 250); f('touchend', 700, 250); });
  ok('efter en afbrudt gest virker et tryk igen',
    vedFinger(efter.x, 700) && vedFinger(efter.y, 250),
    `tekst=[${efter.x}, ${efter.y}] log=${efter.log.join(',')}`);

  // Polaritet: den **gamle** kode gennem samme sandkasse. Gemt med `git show` på
  // en **fast commit** (`34bdbfa`, lige før finger-trækket kom), altså de bytes
  // der faktisk lå i repoet — ikke en håndskrevet kopi, hvor en ny fejlform
  // ville blive grøn.
  //
  // 4/10: denne reference var `HEAD:`. Det er den *nye* kode, så snart den er
  // committet, og polaritetsdommen blev rød i CI til sidst — mutationen læste
  // den kode den skulle modsige. Alle andre `git show` i denne fil står på en
  // fast sha af samme grund (se `1af9302^`, `fbbd0a7`, `PRE_SENTRY_SHA`), så
  // dommen her gør også det, plus den tjekker at referencen stadig er den gamle.
  const FØR_FINGER_TRÆK = '34bdbfa';
  const gammelKjerne = execFileSync('git', ['show', `${FØR_FINGER_TRÆK}:site/text-on-image-core.js`],
    { cwd: root, encoding: 'utf8', maxBuffer: 1 << 26 });
  ok('polaritetsreferencen er stadig kernen uden finger-træk',
    !gammelKjerne.includes('touchmove')
    && readFileSync(join(root, KERNE), 'utf8').includes('touchmove'),
    `mutationen læste ${FØR_FINGER_TRÆK}, som ${gammelKjerne.includes('touchmove') ? 'allerede' : 'ikke'} har touchmove`);
  const mutation = await kørMed((f) => {
    f('touchstart', 100, 120);
    for (let i = 1; i <= 6; i++) f('touchmove', 100 + i * 100, 120);
    f('touchend', 700, 120);
  }, { [KERNE]: gammelKjerne });
  ok('mutationen (kernen uden finger-træk) er fanget',
    !(mutation.tegnet > 0 && mutation.x > 600),
    `mutationen flyttede stadig teksten til x=${mutation.x} — dommen kan ikke se forskellen`);
}

// --------------------------------------------------------------------------
// 21. Værktøjet målte, rettede — og så stoppede det ved et procenttal.
//
// To fejl i træk på `/blog/text-on-image-contrast-check`, som er mahope.tools'
// største indgangsside (9 af 23 menneskelige besøgende, 100 % bounce):
//
//  1. **Resultatet var ikke målt.** Kernen skrev et tal, men ingen sted kaldte
//     `trackEvent`, og `contrast-measured` (eller hvad den hed) stod ikke i
//     `RESULT_EVENTS` — så `/api/results` viste præcis nul. Vi kunne se at 9
//     mennesker læste artiklen og ikke se, om *én* af dem kørte et tjek. Et tal
//     om værktøjet uden et tal om hvor mange gange det blev brugt, er to
//     påstande om hver sin ting, og bare den første var ærlig.
//  2. **Rettelsen ikke kunne bruges.** Artiklen siger at den hurtigste løsning
//     er «et halvgennemsigtigt lag bag teksten», kernen *regner* den mindste
//     dækning der virker, og «Fix it» lægger den på canvas. Så stod bruteren
//     med «42 % mørkt lag» og skulle selv regne ud at det er `rgba(0,0,0,0.42)`
//     i sit eget stylesheet. Den sidste halvdel af opgaven — at få tallet *ind i
//     sit projekt* — var ikke i værktøjet.
//
// Dommerne er falsifiable på den gamle kode:
//
//  A. Efter `mount()` med kernens **eget** demo-billede er der **0**
//     begivenheder. Demoen er tegnet af kernen, ikke uploadet af nogen, så en
//     måling af den er ikke en måling bruteren lavede — ellers tæller hver
//     sidevisning som et gennemført tjek, og det er det tal der ikke må bruges.
//  B. Når bruteren vælger sin egen baggrund, sender kernen **én**
//     `contrast-measured` — og **kun én**, også når der måles igen bagefter.
//     `updateResult()` kaldes fra hvert `mousemove` under et træk, så en kernne
//     uden tælleren ville sende hundredvis for ét resultat.
//  C. Resultatboksen indeholder den CSS der hører til rettelsen, og dens farve
//     er præcis den farve «Fix it» skriver i farvefeltet — samme måling, to
//     steder, så de kan ikke komme i strid.
//  D. `cssFix()` danner rgba-linjen for et **slør** med præcis den dækning
//     `suggestFix()` valgte for de samme endepunkter. Det er den linje der
//     kun kan skrives rigtigt af at regne på kernens egen måling.
//  E. Mutation: kernen fra før denne ændring skal være rød på alle tre.
// --------------------------------------------------------------------------
{
  const KERNE = 'site/text-on-image-core.js';
  // `p` er kernens id-præfiks: artiklerne har deres eget sæt felter, så de kan
  // have et værktøj mere på samme side. Uden denne her ville dommen læse feltet
  // på værktøjssiden og dømme artiklen på den — altså grøn på en side den ikke
  // kørte.
  const SIDER = [
    { f: 'site/text-on-image-checker.html', sprog: 'EN', p: '', mount: /TiContrast\.mount/,
      label: 'Paste this into your own CSS', fremmed: 'Sæt dette ind i din egen CSS' },
    { f: 'site/text-on-image-checker-da.html', sprog: 'DA', p: '', mount: /TiContrast\.mount/,
      label: 'Sæt dette ind i din egen CSS', fremmed: 'Paste this into your own CSS' },
    { f: 'site/blog/text-on-image-contrast-check.html', sprog: 'EN artikel', p: 'art-', mount: /var PRO_CARD/,
      label: 'Paste this into your own CSS', fremmed: 'Sæt dette ind i din egen CSS' },
    { f: 'site/da/blog/tekst-paa-billede-kontrasttjek.html', sprog: 'DA artikel', p: 'art-', mount: /var PRO_CARD/,
      label: 'Sæt dette ind i din egen CSS', fremmed: 'Paste this into your own CSS' },
  ];
  // Kør kernen i en tom kontekst, så dommen over *formlen* ikke afhænger af en
  // browser — samme greb som sektion 16 gør for `suggestFix()`.
  const kern = readFileSync(join(root, KERNE), 'utf8');
  const tom = { module: undefined, exports: undefined, Uint8ClampedArray };
  vm.createContext(tom);
  vm.runInContext(kern, tom);
  const Ti = tom.TiContrast;

  // Dom D. Sløret. Endepunkterne er sort mod hvid, fordi det er det eneste
  // billede hvor **ingen** enkelt tekstfarve kan bestå begge ender — så
  // `suggestFix()` falder ned i slør-grenen, som er den linje der er sværest at
  // skrive rigtigt (tre kanaler plus en dækning) og den der aldrig nåede
  // læseren før.
  const hvidSort = Ti.suggestFix([0, 0, 0], [255, 255, 255], 3, '#ffffff');
  ok('dom D: sort mod hvid kan ikke passes med én tekstfarve (ellers dømmer dommen intet)',
    hvidSort && hvidSort.kind === 'scrim',
    JSON.stringify(hvidSort));
  const cssSlør = Ti.cssFix(hvidSort);
  const kanaler = Ti.hexToRgb(hvidSort.scrim);
  const alfa = Math.round(hvidSort.alpha * 100) / 100;
  // Forventningen er bygget af **kernens egen** måling, ikke af en antaget
  // farve: på sort mod hvid er det den *hvide* slør der vinder med mindst
  // dækning, så en port der hardkoder `rgba(0,0,0,…)` ville dømme den rigtige
  // kode som forkert — eller, værre, ved at fejlen lignede en korrekt måling.
  const forventet = 'color: ' + hvidSort.hex + ';\nbackground: rgba('
    + kanaler.join(', ') + ', ' + alfa + ');';
  ok('dom D: CSS-linjen for et slør er tekstfarve + rgba i kernens egne tal',
    cssSlør === forventet, `fik ${JSON.stringify(cssSlør)} ville have ${JSON.stringify(forventet)}`);
  // Samme streng skal kunne læses *tilbage* til den dækning kernen målte. Uden
  // denne krydsprøve er dommen grøn fordi den genbygger sin egen formel.
  const dækningI = /rgba\((\d+), (\d+), (\d+), ([0-9.]+)\)/.exec(cssSlør || '');
  ok('dom D: rgba-linjen kan læses tilbage som den dækning der blev målt',
    dækningI !== null && Number(dækningI[4]) === alfa
    && Number(dækningI[1]) === kanaler[0],
    cssSlør);
  ok('dom D: en tekstfarve alene giver én linje, og intet giver ingen',
    Ti.cssFix({ kind: 'color', hex: '#1a2b3c' }) === 'color: #1a2b3c;'
    && Ti.cssFix({ kind: 'spot' }) === '' && Ti.cssFix(null) === '',
    'cssFix svarer ikke på de tre tilfælde');

  // Dom A–C på den kørende side, ikke på markup'en: `loadPage` kører sidens egen
  // `mount()` med canvas-stubben, så «der står en måling» er noget kernen har
  // gjort ved denne kørsel.
  async function kør(side, kilder) {
    const { nodes, st } = loadPage(side.f, responses([]).fetchImpl,
      { match: side.mount, canvas: true, preload: [KERNE], kilder });
    await sleep(20);
    return { nodes, st };
  }

  for (const side of SIDER) {
    // Dom A. Demoen er kernens egen: `mount()` maler den og måler den med det
    // samme `updateAll()`, så en kernne der tæller her tæller hver sidevisning.
    const demo = await kør(side);
    ok(`dom A: ${side.sprog} tæller ikke kernens egen demo som et gennemført tjek`,
      demo.st.begivenheder.length === 0,
      `begivenheder=${JSON.stringify(demo.st.begivenheder)}`);

    // Dom B. Bruteren vælger sin egen baggrund: her en gradient, hvilket er den
    // vej `vaerlGradient()` nulstiller `demoBillede` på — præcis den betingelse
    // demo-noten forsvinder på.
    demo.nodes.get(side.p + 'bgmode').value = 'gradient';
    demo.nodes.get(side.p + 'bgmode').fire('change');
    await sleep(20);
    ok(`dom B: ${side.sprog} sender én måling når læseren vælger sin baggrund`,
      demo.st.begivenheder.length === 1 && demo.st.begivenheder[0] === 'contrast-measured',
      `begivenheder=${JSON.stringify(demo.st.begivenheder)}`);

    // Og igen: samme måles igen ved hvert farvevalg og hvert træk.
    demo.nodes.get(side.p + 'fg').fire('input');
    demo.nodes.get(side.p + 'gfrom').fire('input');
    await sleep(20);
    ok(`dom B: ${side.sprog} sender ikke én begivenhed pr. måling (men én pr. side)`,
      demo.st.begivenheder.length === 1,
      `begivenheder=${JSON.stringify(demo.st.begivenheder)}`);

    // Dom C. Den CSS der står i resultatboksen, i læserens eget sprog og på
    // **kernens** måling. Markup'en læses efter at gradienten er valgt, fordi
    // først dér er der en rettelse at skrive — en bestående måling skal *ikke*
    // have en CSS-linje, og det er samme betingelse i begge tilfælde.
    const res = demo.nodes.get(side.p + 'result');
    const efter = (res || {}).innerHTML || '';
    const kode = /<code>(color: #[0-9a-f]{6};)<\/code>/.exec(efter);
    ok(`dom C: ${side.sprog} viser den CSS-linje der hører til rettelsen`,
      kode !== null,
      `resultatet=${JSON.stringify(efter.slice(0, 200))}`);
    ok(`dom C: ${side.sprog} etiketterer den med sidens egen sprog, ikke med den andens`,
      efter.includes(side.label) && !efter.includes(side.fremmed),
      `label=${JSON.stringify((/ti-css-label">([\s\S]*?)</.exec(efter) || [])[1])}`);
    // Den stærkeste af de tre: farven i CSS'en *består* det tjek den er skrevet
    // til. Den læses tilbage og sættes i farvefeltet — præcis hvad læseren gør
    // efter at have kopieret den — og dommen beder så kernen om at måle igen.
    // En CSS-linje der ikke løser problemet ville være det værste vi kan sende
    // en designér: han indsætter den, og siden fejler stadig.
    if (kode) {
      demo.nodes.get(side.p + 'fg').value = kode[1].slice(7, 13);
      demo.nodes.get(side.p + 'fg').fire('input');
      await sleep(20);
      ok(`dom C: ${side.sprog} farven i CSS'en består det tjek den er skrevet til`,
        /ti-pass/.test(String((res || {}).className || '')),
        `klasse=${(res || {}).className} farve=${kode[1]}`);
    }
  }

  // Dom E. Mutationen: kernen fra før denne ændring. Den skal være rød på alle
  // tre domme, ellers dømmer de grønt på en fejl de ikke kan se.
  const FØR_CSS = '34bdbfa';
  const gammelKjerne = execFileSync('git', ['show', `${FØR_CSS}:site/text-on-image-core.js`],
    { cwd: root, encoding: 'utf8', maxBuffer: 1 << 26 });
  ok('dom E: polaritetsreferencen er stadig kernen uden CSS-linjen',
    !gammelKjerne.includes('cssFix'),
    `mutationen læste ${FØR_CSS}, som ${gammelKjerne.includes('cssFix') ? 'allerede' : 'ikke'} har cssFix`);
  const mutation = await kør(SIDER[0], { [KERNE]: gammelKjerne });
  mutation.nodes.get('bgmode').value = 'gradient';
  mutation.nodes.get('bgmode').fire('change');
  await sleep(20);
  ok('dom E: mutationen (kernen uden resultatbegivenhed) fanges',
    mutation.st.begivenheder.length === 0,
    `den gamle kode sendte ${JSON.stringify(mutation.st.begivenheder)}`);
  const mutationMarkup = (mutation.nodes.get('result') || {}).innerHTML || '';
  ok('dom E: mutationen (kernen uden CSS-linjen) fanges',
    !mutationMarkup.includes('color: #'),
    'den gamle kode skrev en CSS-linje');
}

console.log(`\nscan-clients: ${pass}/${pass + fail}`);
process.exit(fail ? 1 : 0);
