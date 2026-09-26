// Ende-til-ende-test af tak-siden: worker's rigtige leveringssvar ind i sidens
// rigtige JavaScript.
//
// Baggrund (opgave 33): `site/thanks.html` rendrede to af tre `kind` i
// `STRIPE_PRODUCTS`. En donation (`support-mahope-oss`) faldt igennem til
// download-grenen, hvor `d.downloads.map(...)` kaster, fordi feltet ikke findes
// på et donationssvar. Kunden så så "Network problem. Refresh this page in a
// moment." i rødt efter ~15 sekunders tavse gentagelser — på en betaling der
// lykkedes, og hvor workeren med vilje ikke sender mail ("Stripe viser selv
// takkebeskeden"). Den ødelagte side var donatorens eneste bekræftelse.
//
// `tests/stripe-worker.test.mjs` beviser allerede, at workeren *svarer*
// korrekt på en donation. Det er den anden halvdel af kæden — at siden kan
// vise svaret — der manglede. Derfor henter denne test de rigtige svar fra
// workeren og renderer dem i sidens eget script.
import { copyFileSync, readFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import vm from 'node:vm';

const root = fileURLToPath(new URL('..', import.meta.url));
const workerSrc = process.argv[2] || join(root, 'site', '_worker.js');
const pagePath = process.argv[3] || join(root, 'site', 'thanks.html');

const tmp = join(tmpdir(), `thanks-worker-${process.pid}.mjs`);
copyFileSync(workerSrc, tmp);
const worker = (await import(pathToFileURL(tmp).href)).default;

let pass = 0, fail = 0;
const ok = (navn, cond, info = '') => { if (cond) pass++; else { fail++; console.log('FEJL:', navn, info); } };

// --------------------------------------------------------------------------
// 1. Falsk KV + Stripe, så vi kan få ægte leveringssvar for hver kind.
// --------------------------------------------------------------------------
const kv = new Map();
const VISITS = {
  get: async (k) => (kv.has(k) ? kv.get(k) : null),
  put: async (k, v) => { kv.set(k, v); },
  delete: async (k) => { kv.delete(k); },
  list: async ({ prefix = '' } = {}) => ({ keys: [...kv.keys()].filter(k => k.startsWith(prefix)).map(name => ({ name })), list_complete: true }),
};
const env = { VISITS, STRIPE_SECRET_KEY: 'sk_test_x', RESEND_API_KEY: 're_x' };
const sessions = {
  cs_live_thankslicAAAAAAAA: { status: 'complete', payment_status: 'paid', subscription: null,
    customer_details: { email: 'a@b.dk' }, line_items: { data: [{ quantity: 1, price: { lookup_key: 'deskuptime-pro-v1' } }] } },
  cs_live_thankssubBBBBBBBB: { status: 'complete', payment_status: 'paid', subscription: 'sub_t1',
    customer_details: { email: 'c@d.dk' }, line_items: { data: [{ quantity: 2, price: { lookup_key: 'eucomply-pro-v1' } }] } },
  cs_live_thanksdlCCCCCCCCC: { status: 'complete', payment_status: 'paid', subscription: null,
    customer_details: { email: 'e@f.dk' }, line_items: { data: [{ quantity: 1, price: { lookup_key: 'eucomply-dpa-v1' } }] } },
  cs_live_thanksdonDDDDDDDD: { status: 'complete', payment_status: 'paid', subscription: null,
    customer_details: { email: 'g@h.dk' }, line_items: { data: [{ quantity: 1, price: { lookup_key: 'support-mahope-oss-v1' } }] } },
  cs_live_thanksnoemailEEEEEE: { status: 'complete', payment_status: 'paid', subscription: null,
    customer_details: {}, line_items: { data: [{ quantity: 1, price: { lookup_key: 'deskuptime-pro-v1' } }] } },
};
const mails = [];
globalThis.fetch = async (url, opts = {}) => {
  url = String(url);
  if (url.startsWith('https://api.stripe.com/v1/checkout/sessions/')) {
    const id = decodeURIComponent(url.split('/sessions/')[1].split('?')[0]);
    const s = sessions[id];
    if (!s) return new Response('{}', { status: 404 });
    return new Response(JSON.stringify({ ...s, id, payment_intent: 'pi_' + id.slice(-6), invoice: null }));
  }
  if (url.startsWith('https://api.stripe.com/v1/subscriptions/')) {
    return new Response(JSON.stringify({ current_period_end: Math.floor(Date.now() / 1000) + 86400 * 300 }));
  }
  if (url === 'https://api.resend.com/emails') { mails.push(JSON.parse(opts.body)); return new Response('{}', { status: 200 }); }
  throw new Error('uventet fetch ' + url);
};
const call = (path) => worker.fetch(new Request('https://mahope.tools' + path), env, {});

// --------------------------------------------------------------------------
// 2. Render tak-sidens eget script med et svar fra workeren.
// --------------------------------------------------------------------------
const pageHtml = readFileSync(pagePath, 'utf8');
const script = pageHtml.split('<script>')[1].split('</script>')[0];

async function render(payload) {
  const els = {
    title: { textContent: '' }, status: { textContent: '', className: 'hint' },
    result: { innerHTML: '', hidden: true }, mail: { textContent: '' },
  };
  let fetches = 0;
  const sandbox = {
    console,
    document: { getElementById: (id) => els[id] || null },
    location: { search: '?session_id=cs_live_abcdefghij1234567890' },
    navigator: { clipboard: { writeText: () => Promise.resolve() } },
    URLSearchParams,
    setTimeout: (fn) => setTimeout(fn, 0),
    fetch: async (url) => {
      if (!String(url).includes('/api/stripe/fulfillment')) throw new Error('uventet kald: ' + url);
      fetches++;
      return { status: 200, json: async () => payload };
    },
  };
  vm.createContext(sandbox);
  let thrown = null;
  try { vm.runInContext(script, sandbox); } catch (e) { thrown = e; }
  // `.catch` i poll() fanger en TypeError og genkalder — lad de gentagelser ske,
  // ellers ville porten være grøn på den præcis fejl den er skrevet til at fange.
  for (let i = 0; i < 12; i++) await new Promise((r) => setTimeout(r, 4));
  return { ...els, fetches, thrown };
}

// --------------------------------------------------------------------------
// 3. Hver kind i STRIPE_PRODUCTS skal kunne renderes på den rigtige side.
//    Kilderne er de ægte leveringssvar, så payload'en kan ikke aftales med
//    siden ved en fejl.
// --------------------------------------------------------------------------
const cases = [
  ['license (engangskøb)', 'cs_live_thankslicAAAAAAAA'],
  ['license (abonnement, 2 enheder)', 'cs_live_thankssubBBBBBBBB'],
  ['download', 'cs_live_thanksdlCCCCCCCCC'],
  ['donation', 'cs_live_thanksdonDDDDDDDD'],
  ['license (kunden gav ingen mailadresse)', 'cs_live_thanksnoemailEEEEEE'],
];
const rendered = {};
for (const [label, sid] of cases) {
  const res = await call('/api/stripe/fulfillment?session_id=' + sid);
  const payload = await res.json();
  ok(`${label}: workeren svarer 200`, res.status === 200, res.status + ' ' + JSON.stringify(payload));
  const page = await render(payload);
  rendered[label] = { payload, page };
  ok(`${label}: siden kaster ikke`, page.thrown === null, String(page.thrown && page.thrown.message));
  ok(`${label}: kortet vises og er ikke tomt`, page.result.hidden === false && page.result.innerHTML.length > 20,
    `hidden=${page.result.hidden} html=${JSON.stringify(page.result.innerHTML.slice(0, 80))}`);
  ok(`${label}: ingen netværksfejl på en betalt ordre`, !/Network problem/i.test(page.status.textContent), page.status.textContent);
  ok(`${label}: ingen tavse gentagelser`, page.fetches === 1, 'fetches=' + page.fetches);
  // "Vi har også sendt det" må kun siges om en nøgle eller en download, og kun
  // når `emailed` er sand. En donation har emailed=true fordi der *intet* skal
  // sendes, så den tæller ikke som "vi har mailet dig det".
  const claimsEmail = /have also emailed/i.test(page.mail.textContent);
  const donates = payload.kind === 'donation';
  ok(`${label}: mail-påstand følger emailed=${payload.emailed}`, donates ? !claimsEmail : claimsEmail === (payload.emailed === true),
    `emailed=${payload.emailed} mail=${JSON.stringify(page.mail.textContent.slice(0, 60))}`);
}

const lic = rendered['license (abonnement, 2 enheder)'];
ok('licens: nøglen vises', /<code id="key">[0-9a-f]{32}<\/code>/.test(lic.page.result.innerHTML), lic.payload.license_key);
ok('licens: antal enheder følger antal købt', /Works on up to 2 device\(s\)/.test(lic.page.result.innerHTML), lic.page.result.innerHTML);
ok('licens: kundeportalen tilbydes ved abonnement', /Manage your subscription/.test(lic.page.result.innerHTML));
ok('licens: aktiveringslink følger produktets home', lic.page.result.innerHTML.includes(lic.payload.activate_url), lic.payload.activate_url);

const dl = rendered['download'];
ok('download: filnavn vises', dl.page.result.innerHTML.includes('dpa-template.pdf'), dl.page.result.innerHTML);
ok('download: linket er workerens /api/download-adresse', dl.page.result.innerHTML.includes(dl.payload.downloads[0].url));

const don = rendered['donation'];
ok('donation: ingen licensnøgle-kasse', !/key-box/.test(don.page.result.innerHTML), don.page.result.innerHTML);
ok('donation: ingen downloadliste', !/<li>/.test(don.page.result.innerHTML), don.page.result.innerHTML);
ok('donation: siger tak uden at kræve aktivering', /nothing to activate/i.test(don.page.result.innerHTML), don.page.result.innerHTML);
ok('donation: påstår ikke at vi har sendt mail', !/have also emailed/i.test(don.page.mail.textContent), don.page.mail.textContent);

// Et kvarterprodukt må ikke hvidvaske siden, hvis det nogensinde tilføjes.
const future = await render({ ok: true, product: 'ny', product_name: 'Nyt produkt', kind: 'seat', emailed: true });
ok('ukendt kind giver en læsbar besked, ikke en hvid side',
  future.thrown === null && future.result.hidden === false && /could not read your order/i.test(future.result.innerHTML),
  `thrown=${future.thrown && future.thrown.message} html=${JSON.stringify(future.result.innerHTML.slice(0, 80))}`);
ok('ukendt kind udløser ingen gentagelsesstorm', future.fetches === 1, 'fetches=' + future.fetches);

// Det modsatte tilfælde: et download-svar uden `downloads`. Det er præcis den
// kastende linje i den gamle kode, så det må heller ikke give en hvid side.
const noFiles = await render({ ok: true, product: 'eucomply-dpa', product_name: 'GDPR DPA template', kind: 'download', emailed: true });
ok('download-svar uden downloads giver en læsbar bessted, ikke en hvid side',
  noFiles.thrown === null && noFiles.result.hidden === false && noFiles.result.innerHTML.length > 20,
  `thrown=${noFiles.thrown && noFiles.thrown.message} html=${JSON.stringify(noFiles.result.innerHTML.slice(0, 80))}`);
ok('download-svar uden downloads hænger ikke i en gentagelsesstorm', noFiles.fetches === 1, 'fetches=' + noFiles.fetches);
ok('siden guardinger d.downloads med Array.isArray', /Array\.isArray\(d\.downloads\)/.test(script));

// --------------------------------------------------------------------------
// 4. Statisk kontrakt: hver kind i workerens produkttabel skal have en egen
//    gren på siden. Uden denne bliver et nyt produkt med en ny `kind` rødt
//    først i en kundes browser.
// --------------------------------------------------------------------------
const workerText = readFileSync(workerSrc, 'utf8');
const table = /const STRIPE_PRODUCTS = \{([\s\S]*?)\n\};/.exec(workerText);
ok('STRIPE_PRODUCTS er fundet i workeren', !!table);
const kinds = [...new Set([...(table ? table[1] : '').matchAll(/kind: '([a-z_]+)'/g)].map((m) => m[1]))].sort();
ok('workeren har mindst de tre kend vi kender', kinds.length >= 3 && kinds.includes('license') && kinds.includes('download') && kinds.includes('donation'), kinds.join(','));
const branched = new Set([...script.matchAll(/d\.kind\s*===\s*'([a-z_]+)'/g)].map((m) => m[1]));
// `download` dækkes af `Array.isArray(d.downloads)` frem for en `kind ===`-gren.
// Det er en bredere regel end en kind-gren — den fanger også et svar der
// kommer med filer uden at være et download-produkt — og de to huller den
// efterlader er dækket andre steder: et nyt `kind` uden `downloads` rammer
// `ukendt kind giver en læsbar besked`, og en fjernet guard rammer
// `download-svar uden downloads`.
if (/Array\.isArray\(d\.downloads\)/.test(script)) branched.add('download');
for (const kind of kinds) {
  ok(`siden har en egen gren for kind="${kind}"`, branched.has(kind), `grenet: ${[...branched].join(',') || '(ingen)'}`);
}

console.log(`${pass}/${pass + fail} ok`);
process.exit(fail ? 1 : 0);
