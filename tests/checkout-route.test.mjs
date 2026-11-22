// /api/checkout er den eneste rute der udsteder et købslink, og den lå med en
// stille fejl: `which = … : 'cc'`. Alt den ikke genkendte faldt gennem til
// Clean Copy Pro, så `?product=deskuptime-pro` — den product_key Stripe selv
// bruger — svarede med Clean Copys betalingslink, pris og produktnavn. Køberen
// betalte for en anden udgave end den der blev bedt om, og svaret sagde intet.
//
// Porten dømmer tre ting: at hvert produkt i kontrakten svarer med sit eget
// link og pris, at uvedkommende produkter får et 400 med listen (aldrig et
// andet produkt), og at link og pris er de samme som i
// `tools/stripe_catalog.json` — den maskinlæsbare kontrakt.
import { copyFileSync, readFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const root = fileURLToPath(new URL('..', import.meta.url));
const workerSrc = process.argv[2] || join(root, 'site/_worker.js');
const catalog = JSON.parse(readFileSync(process.argv[3] || join(root, 'tools/stripe_catalog.json'), 'utf8'));

// _worker.js er ESM, men repoet ikke "type": "module" — kopiér til .mjs før import.
const tmp = join(tmpdir(), `checkout-route-under-test-${process.pid}.mjs`);
copyFileSync(workerSrc, tmp);
const worker = (await import(pathToFileURL(tmp).href)).default;

const kv = new Map();
const VISITS = {
  get: async (k) => (kv.has(k) ? kv.get(k) : null),
  head: async (k) => (kv.has(k) ? { metadata: null } : null),
  put: async (k, v) => { kv.set(k, v); },
  delete: async (k) => { kv.delete(k); },
  list: async ({ prefix = '' } = {}) => ({ keys: [...kv.keys()].filter((k) => k.startsWith(prefix)).map((name) => ({ name })), list_complete: true }),
};
const env = { VISITS, ASSETS: { fetch: async () => new Response('Not found', { status: 404 }) } };

let pass = 0;
let fail = 0;
const ok = (name, cond, info = '') => {
  if (cond) { pass++; console.log(`ok ${name}`); }
  else { fail++; console.log(`FEJL ${name}${info ? ' — ' + info : ''}`); }
};
const call = async (q, method = 'GET') => {
  const r = await worker.fetch(new Request(`https://mahope.tools/api/checkout${q}`, { method }), env, {});
  let data = {};
  try { data = await r.clone().json(); } catch { /* ikke JSON */ }
  return { status: r.status, data, headers: r.headers };
};

// ── 1. Page Profile Pro svarer med sit eget link, pris og navn ──
// Salget af Clean Copy Pro og DeskUptime Pro er lukket 22/11-2026, så Page
// Profile Pro er det eneste produkt ruten udsteder et købslink for.
// `payment_link` og `price` kommer fra kontrakten, så en kopiering der glider
// af, bliver rød her i stedet for på en købsside.
const EXPECTED = {
  'page-profile-pro': 'https://buy.stripe.com/9B6eVcgHp7YK69ggN9bMQ04',
};

for (const [key, link] of Object.entries(EXPECTED)) {
  const { status, data } = await call(`?product=${key}`);
  ok(`${key} svarer 200`, status === 200, `fik ${status}`);
  ok(`${key} svarer med sit eget produktnavn`, data.product === key, `fik ${data.product}`);
  ok(`${key} svarer med sit eget betalingslink`, data.checkout_url === link, `fik ${data.checkout_url}`);
  ok(`${key} svarer med produktets pris`, Boolean(data.price) && /\$19/.test(data.price), `fik ${data.price}`);
  const cat = catalog.products[key];
  ok(`${key} er aktiv i tools/stripe_catalog.json`, cat && cat.status !== 'inactive', `status: ${cat && cat.status}`);
  ok(`${key}-linket er uændret i tools/stripe_catalog.json`, cat && cat.payment_link === link,
    `katalog: ${cat && cat.payment_link}`);
  ok(`${key}-beløbet er uændret i tools/stripe_catalog.json`,
    cat && data.price_usd === cat.price_usd, `ruten: ${data.price_usd} / katalog: ${cat && cat.price_usd}`);
  ok(`${key} siger rigtigt om det er et abonnement eller en engangspris`,
    cat && data.billing === (cat.subscription ? 'yearly' : 'once'),
    `ruten: ${data.billing} / katalog: ${cat && (cat.subscription ? 'yearly' : 'once')}`);
}

// ── 2. De lukkede produkter svarer 410 Gone — aldrig et købslink ──
// Dommen er vendt 22/11-2026: før krævede porten et link for begge, nu kræver
// den at intet link kommer ud, og at katalogen siger produktet er inaktivt.
const CLOSED = { 'clean-copy-pro': 'cc', 'deskuptime-pro': 'du' };
for (const [key, short] of Object.entries(CLOSED)) {
  for (const asked of [key, short, key.toUpperCase(), ` ${key} `]) {
    const { status, data } = await call(`?product=${encodeURIComponent(asked)}`);
    ok(`"${asked}" svarer 410 Gone`, status === 410, `fik ${status}`);
    ok(`"${asked}" giver intet købslink`, data.checkout_url === undefined && !/stripe\.com/.test(JSON.stringify(data)),
      JSON.stringify(data).slice(0, 120));
    ok(`"${asked}" navngiver sit eget produkt`, data.product === key, `fik ${data.product}`);
    ok(`"${asked}" siger at salget er lukket og at nøgler virker`,
      /no longer sold/.test(data.error || '') && /keep working/.test(data.error || ''), data.error);
  }
  const cat = catalog.products[key];
  ok(`${key} er inactive i tools/stripe_catalog.json`, cat && cat.status === 'inactive', `status: ${cat && cat.status}`);
}

// En gammel KV-overstyring må ikke genåbne et lukket produkt.
kv.set('cc-pro-checkout', 'https://buy.stripe.com/gammel-cc');
kv.set('du-pro-checkout', 'https://buy.stripe.com/gammel-du');
for (const key of Object.keys(CLOSED)) {
  const { status, data } = await call(`?product=${key}`);
  ok(`en gammel KV-overstyring genåbner ikke ${key}`, status === 410 && data.checkout_url === undefined,
    `${status} ${data.checkout_url}`);
}
kv.clear();

// ── 3. Uvedkommende produkter får et 400, aldrig et andet produkt ──
const unknown = [
  'deskuptime', 'clean-copy', 'eucomply-pro', 'clean-copy-pro-lifetime',
  'support-mahope-oss', 'transmute-desktop', '', '../../etc/passwd',
];
for (const bad of unknown) {
  const { status, data } = await call(`?product=${encodeURIComponent(bad)}`);
  ok(`"${bad}" får 400 og intet købslink`, status === 400 && data.checkout_url === undefined,
    `fik ${status} ${JSON.stringify(data).slice(0, 80)}`);
}

// Mangler parameteren helt, skal svaret også sige det — ikke gætte et produkt.
const missing = await call('');
ok('manglende ?product= får 400', missing.status === 400, `fik ${missing.status}`);
ok('manglende ?product= giver ingen checkout_url', missing.data.checkout_url === undefined);
ok('400-svaret navngiver den gyldige nøgle', /page-profile-pro/.test(missing.data.error || ''), missing.data.error);

// ── 4. Kortformen og skrivemåden består, og KV virker for Page Profile ──
const short = await call('?product=pp');
ok('kortformen ?product=pp svarer stadig med page-profile-pro',
  short.status === 200 && short.data.product === 'page-profile-pro', `${short.status} ${short.data.product}`);
const spaced = await call('?product=%20Page-Profile-Pro%20');
ok('mellemrum og store bogstaver er ikke en ny fejl',
  spaced.status === 200 && spaced.data.product === 'page-profile-pro', `${spaced.status} ${spaced.data.product}`);
kv.set('pp-pro-checkout', 'https://buy.stripe.com/overstyret-pp');
const overridden = await call('?product=page-profile-pro');
ok('KV kan stadig overstyre Page Profile Pro', overridden.data.checkout_url === 'https://buy.stripe.com/overstyret-pp',
  overridden.data.checkout_url);
kv.clear();

// ── 5. Ruten er åben for andres sider, som den har været hele tiden ──
const { headers } = await call('?product=cc');
ok('CORS er stadig åben for indlejring', headers.get('Access-Control-Allow-Origin') === '*');

// Ruten lovede OPTIONS i `Access-Control-Allow-Methods`, men besvarede et
// preflight med det samme produktsvar som et GET.
const preflight = await call('?product=page-profile-pro', 'OPTIONS');
ok('et preflight får 204 og ingen krop',
  preflight.status === 204 && preflight.data.checkout_url === undefined, `fik ${preflight.status}`);

// Fejlsvaret må ikke gengive kalderens egen tekst — ruten er åben med CORS `*`.
const noisy = await call(`?product=${encodeURIComponent('<img src=x onerror=alert(1)>')}`);
ok('et 400 gentager ikke kalderens egen tekst', !/onerror|<img/.test(noisy.data.error || ''), noisy.data.error);

console.log(fail ? `\n${fail} fejl` : `\ncheckout-route: alt grønt (${pass})`);
process.exit(fail ? 1 : 0);