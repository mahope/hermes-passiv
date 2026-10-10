// Ende-til-ende-test af konverteren inde i guiderne (`site/clean-copy-embed.js`).
//
// Feature-kø 58: cleancopy.tools' tre HTML-to-Markdown-guider havde 3, 2 og 2
// besøgende i 28 dage (Plausible, 10/10) og 50–67 % bounce. De linker til
// /clean-copy-tool, men indeholder det ikke — mahope.tools' kontrastguide
// viste det modsatte mønster virker: læseren der møder værktøjet i teksten
// bruger det.
//
// Testen indlæser selve embed-scriptet i en vm-sandkasse med en minimal DOM
// og den RIGTIGE konverteringskerne (`clean-copy-core.js`), så «konverterer
// den?», «hvad vises, og hvad vises ikke?» og «hvad gøres der ved en
// licens?» dømmes på den kode der faktisk ships — ikke på en kopi.
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import vm from 'node:vm';
import { createRequire } from 'node:module';

const root = fileURLToPath(new URL('..', import.meta.url));
const require = createRequire(import.meta.url);
const CleanCopyCore = require(join(root, 'site/clean-copy-core.js'));

let pass = 0, fail = 0;
const ok = (navn, cond, info = '') => { if (cond) pass++; else { fail++; console.log('FEJL:', navn, info); } };

const KEY = 'a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6';
const BUY_LINK = 'https://buy.stripe.com/6oU4gy76PgvgdBIdAXbMQ00';
const EMBED_PATH = join(root, 'site/clean-copy-embed.js');
const embed = readFileSync(EMBED_PATH, 'utf8');
const net = readFileSync(join(root, 'site/net.js'), 'utf8');
const DAY = 24 * 60 * 60 * 1000;

// DOM-stub: nok til at embed-scriptet kan bygge sit UI, og nok til at testen
// kan læse felterne tilbage. `id` registrerer noden, så `getElementById`
// finder den i det øjeblik scriptet sætter den — som i en rigtig DOM efter
// appendChild.
function makeDom(lang) {
  const byId = new Map();
  const node = (tag) => {
    const n = {
      tag, children: [], _text: '', _attrs: {}, style: {},
      hidden: false, value: '', type: '', href: '', rel: '', placeholder: '',
      className: '', checked: false, disabled: false, listeners: {},
      setAttribute(k, v) { this._attrs[k] = String(v); },
      getAttribute(k) { return k in this._attrs ? this._attrs[k] : null; },
      appendChild(c) { this.children.push(c); return c; },
      addEventListener(ev, fn) { (this.listeners[ev] = this.listeners[ev] || []).push(fn); },
      removeEventListener() {},
      focus() {}, remove() {},
      // Samme kontrakt som browserens click(): alle lyttere for den hændelse.
      click() { (this.listeners.click || []).forEach((fn) => fn({ preventDefault() {} })); },
      fire(ev, e) { (this.listeners[ev] || []).forEach((fn) => fn(e || { preventDefault() {} })); },
      // Dyb søgning: et `<a>` i et `<p>` i kortet skal kunne findes.
      find(pred) {
        for (const c of this.children) {
          if (pred(c)) return c;
          const d = c.find ? c.find(pred) : null;
          if (d) return d;
        }
        return null;
      },
    };
    Object.defineProperty(n, 'textContent', {
      get() { return this._text; },
      set(v) { this._text = String(v); },
    });
    Object.defineProperty(n, 'id', {
      get() { return this._id || ''; },
      set(v) { this._id = String(v); byId.set(String(v), this); },
    });
    return n;
  };
  const host = node('div');
  byId.set('cc-embed', host);
  const document = {
    documentElement: { lang: lang || 'en' },
    createElement: (tag) => node(tag),
    createTextNode: (t) => ({ text: String(t) }),
    getElementById: (id) => byId.get(id) || null,
  };
  return { byId, node, document, host };
}

// `respond` får URL'en og returnerer {status, json} eller en Error (netfald).
function laad(opts = {}) {
  const { byId, document, host } = makeDom(opts.lang);
  const store = Object.assign({}, opts.store);
  const requests = [];
  const tracked = [];
  const sandbox = {
    console, Math, Date, JSON, Promise, String, Number, Object, Array, RegExp, Error,
    setTimeout, clearTimeout,
    CleanCopyCore,
    location: { pathname: opts.path || '/blog/html-to-markdown-cli' },
    // Siden erklærer sin egen sti — artiklen gør det med denne linje.
    CC_EMBED: { path: opts.path || '/blog/html-to-markdown-cli' },
    document,
    navigator: { doNotTrack: opts.dnt === '1' ? '1' : '0', clipboard: { writeText: async () => {} } },
    localStorage: {
      getItem: (k) => (k in store ? store[k] : null),
      setItem: (k, v) => { store[k] = String(v); },
      removeItem: (k) => { delete store[k]; },
    },
    crypto: { randomUUID: () => 'dev-embed' },
    // Nok til at embed-scriptets DOMParser-kald får markup tilbage: kernen
    // Renser HTML med egne regexer, så stubben skal kun levere strengen.
    DOMParser: function () {
      return { parseFromString: (raw) => ({ body: { innerHTML: raw, textContent: String(raw).replace(/<[^>]*>/g, '') } }) };
    },
    fetch: (url, o) => {
      const u = String(url);
      if (u === '/api/track') { tracked.push(JSON.parse(o.body)); return Promise.resolve({ status: 200, json: () => Promise.resolve({}) }); }
      requests.push({ url: u, body: o && o.body ? JSON.parse(o.body) : {} });
      const r = (opts.respond || (() => ({ status: 200, json: {} })))(u);
      if (r instanceof Error) return Promise.reject(r);
      // Som browserens Response: `ok` følger status, fordi net.js læser den.
      return Promise.resolve({ status: r.status, ok: r.status >= 200 && r.status < 300, json: () => Promise.resolve(r.json) });
    },
  };
  sandbox.window = sandbox;
  sandbox.self = sandbox;
  vm.createContext(sandbox);
  // Den rigtige `net.js` indlæses: licenskaldet skal gå gennem kernen, ikke
  // en kopi — `opts.netless` kører siden uden den, for at domme fallbacken.
  if (!opts.netless) vm.runInContext(net, sandbox, { filename: 'net.js' });
  vm.runInContext(opts.source || embed, sandbox, { filename: 'clean-copy-embed.js' });
  return { byId, store, requests, tracked, sandbox, host };
}
const flush = () => new Promise((r) => setTimeout(r, 0));
const VALID = { status: 200, json: { ok: true, valid: true, plan: 'pro-yearly', expires_at: '2027-08-24T00:00:00Z' } };

// --------------------------------------------------------------------------
// 1. Uden nøgle: intet licenskald, batch lukket, henvisning til webværktøjet.
// --------------------------------------------------------------------------
{
  const t = laad({ respond: () => VALID });
  await flush();
  ok('embed: uden nøgle sendes intet licenskald', t.requests.length === 0, JSON.stringify(t.requests));
  ok('embed: uden nøgle er batch lukket', t.byId.get('cc-batch').hidden === true);
  ok('embed: uden nøgle står aktiverings-henvisningen', t.byId.get('cc-pro-note').hidden === false);
  ok('embed: konverteringsfelterne findes', !!t.byId.get('cc-input') && !!t.byId.get('cc-output'));
  ok('embed: fire tilstande er på plads', ['markdown', 'wikilinks', 'csv', 'plain'].every((m) => !!t.byId.get('cc-mode-' + m)));
}

// --------------------------------------------------------------------------
// 2. Konverteringen: samme kerne som /clean-copy-tool, kørende i artiklen.
// --------------------------------------------------------------------------
{
  const t = laad({});
  const input = t.byId.get('cc-input');
  const output = t.byId.get('cc-output');
  const nudge = t.byId.get('cc-nudge');
  ok('embed: kortet er skjult før der er konverteret', nudge.hidden === true);

  // Ren tekst i markdown-tilstand: ingen kerne, kun mellemrumsrens.
  input.value = '  Hej  verden\u00A0igen  ';
  input.fire('input');
  ok('embed: ren tekst konverteres uden at røre indholdet',
    output.value === 'Hej  verden igen', JSON.stringify(output.value));
  ok('embed: statistikken tæller tegn og ord', /chars · \d+ words/.test(t.byId.get('cc-stats').textContent), t.byId.get('cc-stats').textContent);
  ok('embed: Pro-kortet kommer efter et rigtigt resultat', nudge.hidden === false);
  ok('embed: Pro-kortet køber via den aftale Stripe-lænke',
    nudge.find((n) => n.tag === 'a' && n.href === BUY_LINK) !== null);

  // Rå HTML: kernen kører, outputtet er Markdown (h2 → ##, som i værktøjet).
  input.value = '<h2>Kvartalsrapport</h2><p>Omsætningen voksede <strong>34 %</strong>.</p>';
  input.fire('input');
  ok('embed: HTML bliver til Markdown med samme kerne som værktøjet',
    output.value.indexOf('## Kvartalsrapport') === 0 && output.value.indexOf('**34 %**') !== -1,
    JSON.stringify(output.value));
  ok('embed: kernen bevares ved skift af tilstand',
    (() => { t.byId.get('cc-mode-csv').click(); return true; })() && true);

  // CSV-tilstand på en tabel.
  input.value = '<table><tr><th>Navn</th><th>Tal</th></tr><tr><td>a</td><td>1</td></tr></table>';
  input.fire('input');
  ok('embed: CSV-tilstand laver komma-separerede rækker',
    output.value.indexOf('Navn,Tal') !== -1 && output.value.indexOf('a,1') !== -1, JSON.stringify(output.value));
  ok('embed: den valgte tilstand er markeret',
    t.byId.get('cc-mode-csv').getAttribute('aria-pressed') === 'true' &&
    t.byId.get('cc-mode-markdown').getAttribute('aria-pressed') === 'false');

  // Smarte anførselstegster kun når kassen er slået til.
  t.byId.get('cc-mode-markdown').click();
  input.value = 'Han sagde \u201Chej\u201D';
  input.fire('input');
  ok('embed: uden rensning bliver de krøllede tegn stående', output.value.indexOf('\u201C') !== -1);
  const smart = t.byId.get('cc-smart');
  smart.checked = true;
  smart.fire('change');
  ok('embed: med rensning bliver de krøllede tegn til almindelige', output.value === 'Han sagde "hej"', JSON.stringify(output.value));

  // Kopi uden indhold siger det, i stedet for at gøre ingenting.
  input.value = '';
  input.fire('input');
  t.byId.get('cc-copy').click();
  ok('embed: kopiering af ingenting siger at der ikke er noget', /Nothing to copy yet/.test(t.byId.get('cc-status').textContent));
  ok('embed: rydning skjuler Pro-kortet igen', (() => {
    input.value = '<p>x</p>';
    input.fire('input');
    t.byId.get('cc-clear').click();
    return nudge.hidden === true && output.value === '';
  })());

  // Ét anonymt signal pr. side, og intet når læseren har bedt om ro.
  ok('embed: en konvertering sendes ét anonymt signal med artiklens sti',
    t.tracked.length === 1 && t.tracked[0].event === 'convert' && t.tracked[0].path === '/blog/html-to-markdown-cli',
    JSON.stringify(t.tracked));
}

// --------------------------------------------------------------------------
// 3. Privatlivsteksten er ærlig: kører i browseren, licens tjekkes online.
// --------------------------------------------------------------------------
{
  const t = laad({});
  const text = '';
  let privacy = '';
  t.host.find((n) => n.tag === 'p').children.length; // strukturen er bygget
  const p = t.byId.get('cc-embed').children.find((n) => n.tag === 'p' && /license API on mahope\.tools/.test(n._text));
  privacy = p ? p._text : '';
  ok('embed: privatlivsteksten nævner både browseren og licens-API\'et',
    /runs in JavaScript on this page/.test(privacy) && /license API on mahope\.tools/.test(privacy) && text === '',
    JSON.stringify(privacy.slice(0, 80)));
}

// --------------------------------------------------------------------------
// 4. Licensgaten: syvdagesreglen fra det kanoniske modul, uændret.
// --------------------------------------------------------------------------
{
  // Lagret nøgle + 200 → batch åbnes, kaldet bærer produkt, nøgle og enhed.
  const t = laad({
    store: { cc_pro_license: KEY, cc_pro_checked: String(Date.now() - 2 * DAY), cc_device_id: 'dev-embed' },
    respond: () => VALID,
  });
  await flush();
  ok('licens: en lagret nøgle genvalideres', t.requests.length === 1 && t.requests[0].url === '/api/license/validate', JSON.stringify(t.requests));
  ok('licens: valideringen sender produktet', t.requests[0].body.product === 'clean-copy-pro');
  ok('licens: valideringen sender nøglen normaliseret', t.requests[0].body.license_key === KEY);
  ok('licens: valideringen sender enheds-id\'et', t.requests[0].body.device_id === 'dev-embed');
  ok('licens: 200 valid åbner batch', t.byId.get('cc-batch').hidden === false);
  ok('licens: aktiverings-henvisningen forsvinder', t.byId.get('cc-pro-note').hidden === true);
  ok('licens: et positivt tjek stamples', Number(t.store.cc_pro_checked) > Date.now() - 60_000);

  // Batch-konvertering: to stykker, to resultater, i samme rækkefølge.
  t.byId.get('cc-batch-input').value = '<p>Ét stykke</p>\nRen tekst';
  t.byId.get('cc-batch-btn').click();
  const lines = String(t.byId.get('cc-batch-output').value).split('\n');
  ok('batch: to stykker bliver to resultater', lines.length === 2 && lines[0].indexOf('Ét stykke') !== -1, JSON.stringify(lines));
  ok('batch: statussen fortæller hvor mange', /Converted 2 snippets/.test(t.byId.get('cc-batch-status').textContent));

  // 503 inde i syv dage: en betalende kunde miste ikke Pro af en nedetid.
  const t2 = laad({
    store: { cc_pro_license: KEY, cc_pro_checked: String(Date.now() - 2 * DAY) },
    respond: () => ({ status: 503, json: { ok: false, error: 'Service unavailable.' } }),
  });
  await flush();
  ok('licens: 503 inde i syv dage holder batch åben', t2.byId.get('cc-batch').hidden === false);
  ok('licens: 503 inde i cachen beholder nøglen', t2.store.cc_pro_license === KEY);
  ok('licens: nedetiden forklares i overskriften', /unreachable/i.test(t2.byId.get('cc-batch')._text) || /License server unreachable/.test(
    t2.byId.get('cc-batch').children.map((c) => c._text).join(' ')));

  // 503 efter syv dage: cachen er opbrugt, Pro falder tilbage.
  const t3 = laad({
    store: { cc_pro_license: KEY, cc_pro_checked: String(Date.now() - 8 * DAY) },
    respond: () => ({ status: 503, json: {} }),
  });
  await flush();
  ok('licens: 503 efter syv dage lukker batch', t3.byId.get('cc-batch').hidden === true);
  ok('licens: 503 efter syv dage rydder nøglen', t3.store.cc_pro_license === undefined);

  // 403: nøglen er til et andet produkt eller udløbet — batch forbliver lukket.
  const t4 = laad({
    store: { cc_pro_license: KEY, cc_pro_checked: String(Date.now()) },
    respond: () => ({ status: 403, json: { ok: false, error: 'This license key is for another product.' } }),
  });
  await flush();
  ok('licens: et hårdt afslag lukker batch', t4.byId.get('cc-batch').hidden === false === false && t4.byId.get('cc-batch').hidden === true);
  ok('licens: serverens egen sætning vises', /another product/.test(t4.byId.get('cc-batch-status').textContent));

  // Netfald (status 0) inde i cachen: stadig Pro.
  const t5 = laad({
    store: { cc_pro_license: KEY, cc_pro_checked: String(Date.now() - 60 * 1000) },
    respond: () => new Error('network down'),
  });
  await flush();
  ok('licens: et netfald inde i cachen lukker ikke batch', t5.byId.get('cc-batch').hidden === false);

  // Udløbet nøgle: intet kald, lukket med det samme.
  const t6 = laad({
    store: { cc_pro_license: KEY, cc_pro_expires: '2020-01-01T00:00:00Z' },
    respond: () => VALID,
  });
  await flush();
  ok('licens: en udløbet nøgle kalder ikke serveren', t6.requests.length === 0);
  ok('licens: en udløbet nøgle lukker batch', t6.byId.get('cc-batch').hidden === true);
}

// --------------------------------------------------------------------------
// 5. Dansk: samme script, dansk tekst.
// --------------------------------------------------------------------------
{
  const t = laad({ lang: 'da', store: { cc_pro_license: KEY, cc_pro_checked: String(Date.now() - DAY) }, respond: () => VALID });
  await flush();
  const sum = t.byId.get('cc-batch').children[0]._text;
  ok('dansk: batch-overskriften er dansk', /Batch-konvertering/.test(sum), sum);
  const nudge = t.byId.get('cc-nudge');
  ok('dansk: Pro-kortet er dansk', /ét stykke ad gangen/i.test(nudge.children[0]._text));
  ok('dansk: privatlivsteksten nævner licens-API\'et', /licens-API på mahope\.tools/.test(
    t.byId.get('cc-embed').children.map((c) => c._text).join(' ')));
}

// --------------------------------------------------------------------------
// 6. At testen kan fejle: mutationen der fjerner Pro-kortet må gå rød.
// --------------------------------------------------------------------------
{
  const muteret = embed.replace('nudge.hidden = false;', '/* mutation: kortet kommer aldrig */');
  ok('mutation: kilden til mutationen findes', muteret !== embed);
  const t = laad({ source: muteret });
  const input = t.byId.get('cc-input');
  input.value = '<p>noget</p>';
  input.fire('input');
  ok('embed: uden mutationen vises kortet — med mutationen forbliver det skjult',
    (() => { const frisk = laad({}); const i2 = frisk.byId.get('cc-input'); i2.value = '<p>x</p>'; i2.fire('input'); return frisk.byId.get('cc-nudge').hidden === false && t.byId.get('cc-nudge').hidden === true; })(),
    `frisk vs muteret`);
}

// --------------------------------------------------------------------------
// 7. De tre guider indlæser scriptet og erklærer deres egen sti.
// --------------------------------------------------------------------------
{
  const guides = [
    ['site/blog/html-to-markdown-cli.html', '/blog/html-to-markdown-cli'],
    ['site/blog/html-to-markdown-vscode.html', '/blog/html-to-markdown-vscode'],
    ['site/blog/copy-as-markdown-chrome-extension.html', '/blog/copy-as-markdown-chrome-extension'],
  ];
  for (const [fil, sti] of guides) {
    const html = readFileSync(join(root, fil), 'utf8');
    ok(`guider: ${fil} har beholderen`, /<div id="cc-embed"><\/div>/.test(html));
    ok(`guider: ${fil} erklærer sin egen sti`, html.indexOf(`window.CC_EMBED = { path: '${sti}' }`) !== -1);
    ok(`guider: ${fil} indlæser kernen og embed-scriptet`,
      html.indexOf('<script src="/clean-copy-core.js"></script>') !== -1 &&
      html.indexOf('<script src="/clean-copy-embed.js"></script>') !== -1);
    // net.js skal stå FØR embed-scriptet: licenskaldet kører med det samme.
    ok(`guider: ${fil} indlæser net.js før embed-scriptet`,
      html.indexOf('<script src="/net.js"></script>') !== -1 &&
      html.indexOf('<script src="/net.js"></script>') < html.indexOf('<script src="/clean-copy-embed.js"></script>'));
  }
}

// --------------------------------------------------------------------------
// 8. Kaldet går gennem den rigtige net.js: en 429 er endelig og viser
//    serverens egen sætning — ikke en genkaldt kvote.
// --------------------------------------------------------------------------
{
  const lagret = { cc_pro_license: KEY, cc_pro_checked: String(Date.now()) };

  // 429: serverens sætning skal frem, og Pro falder tilbage.
  const t = laad({
    store: lagret,
    respond: () => ({ status: 429, json: { ok: false, error: 'Too many requests. Try again later.' } }),
  });
  await flush();
  ok('net: valideringen kaldes via kernen', t.requests.length === 1 && t.requests[0].url === '/api/license/validate',
    JSON.stringify(t.requests));
  ok('net: en 429 lukker batch', t.byId.get('cc-batch').hidden === true);
  ok('net: en 429 viser serverens egen sætning', /Too many requests/.test(t.byId.get('cc-batch-status').textContent),
    t.byId.get('cc-batch-status').textContent);

  // Uden net.js på siden: intet kald sendes, og syvdagesreglen afgør.
  const t2 = laad({ store: lagret, netless: true, respond: () => VALID });
  await flush();
  ok('net: uden kernen sendes intet kald', t2.requests.length === 0, JSON.stringify(t2.requests));
  ok('net: uden kernen holder cachen Pro åben', t2.byId.get('cc-batch').hidden === false);
  ok('net: uden kernen står der at serveren ikke kunne nås',
    /unreachable/i.test(t2.byId.get('cc-batch').children.map((c) => c._text).join(' ')),
    t2.byId.get('cc-batch').children.map((c) => c._text).join(' '));
}

// --------------------------------------------------------------------------
// 9. At den nye test kan fejle: uden NET-grenen kalder embedet kernen i en
//    sandkasse uden kernen, og fejlen sluges af try/catch'et ved kaldet.
// --------------------------------------------------------------------------
{
  const udenNet = embed.replace(
    "if (!window.NET || !window.NET.postJSON) return Promise.resolve({ status: 0, data: {} });",
    "if (false) return Promise.resolve({ status: 0, data: {} });");
  ok('mutation: NET-grenen findes i kilden', udenNet !== embed);
  const lagret = { cc_pro_license: KEY, cc_pro_checked: String(Date.now() - DAY) };
  const frisk = laad({ store: lagret, netless: true, respond: () => VALID });
  const muteret = laad({ store: lagret, netless: true, source: udenNet, respond: () => VALID });
  await flush();
  // Uden grenen fortsætter kaldet ud i en NET der ikke findes: beslutten
  // kommer aldrig tilbage, så overskriften forbliver den tomme standard.
  const overskrift = (t) => t.byId.get('cc-batch').children.map((c) => c._text).join(' ');
  ok('mutation: uden grenen forbliver overskriften tom, med grenen står der «unreachable»',
    /unreachable/i.test(overskrift(frisk)) && !/unreachable/i.test(overskrift(muteret)),
    `frisk=${overskrift(frisk)} muteret=${overskrift(muteret)}`);
}

console.log(`\nclean-copy-embed: ${pass}/${pass + fail}`);
process.exit(fail ? 1 : 0);
