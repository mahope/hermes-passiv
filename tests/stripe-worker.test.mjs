// Ende-til-ende-test af Stripe-levering i site/_worker.js med falsk KV, Stripe og Resend.
import { createHash, createHmac } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { copyFileSync, readFileSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
const root = fileURLToPath(new URL('..', import.meta.url));
// _worker.js er ESM, men repoet er ikke "type": "module" — kopiér til en .mjs før import.
const src = process.argv[2] || fileURLToPath(new URL('../site/_worker.js', import.meta.url));
const tmp = join(tmpdir(), `worker-under-test-${process.pid}.mjs`);
copyFileSync(src, tmp);
const worker = (await import(pathToFileURL(tmp).href)).default;

const kv = new Map();
const VISITS = {
  get: async (k, type) => { const v = kv.get(k); if (v === undefined) return null; return type === 'arrayBuffer' ? new TextEncoder().encode(v).buffer : v; },
  // Kun metadata, som den rigtige binding: workeren må aldrig hente en hel fil
  // for at finde ud af om den er der.
  head: async (k) => (kv.has(k) ? { metadata: null } : null),
  put: async (k, v) => { kv.set(k, typeof v === 'string' ? v : v); },
  delete: async (k) => { kv.delete(k); },
  list: async ({ prefix = '' } = {}) => ({ keys: [...kv.keys()].filter(key => key.startsWith(prefix)).sort().map(name => ({ name })), list_complete: true }),
};
const WHSEC = 'whsec_test123';
const env = { VISITS, STRIPE_SECRET_KEY: 'sk_test_x', STRIPE_WEBHOOK_SECRET: WHSEC, RESEND_API_KEY: 're_x',
  ASSETS: { fetch: async (request) => {
    const pathname = new URL(request.url).pathname;
    if (pathname === '/downloads/eaa-checklist.epub') return new Response('asset', { status: 200 });
    // CDN'en har stadig den gamle fil, selv om den er slettet i git — det er
    // præcis den tilstand, der gjorde 1.5.3 hentbar med den falske README. Den
    // skal serveres af ASSETS, så reglen er den eneste grund til at kunden ikke
    // får den.
    if (pathname === '/downloads/clean-copy-firefox-v1.5.3.zip') return new Response('No network requests — nothing leaves your browser', { status: 200 });
    // Samme tilstand for desktop-kildearkivet: 1.3.3 lovede "$19/year" for et
    // produkt uden product_key og sendte kunden ud for at købe. Målt 200 på
    // mahope.tools 26/9, så det er denne regel — ikke kilden — der lukker den.
    if (pathname === '/downloads/eaa-scanner-desktop-src-1.3.3.zip') return new Response('Pro requires an annual license key ($19/year) — Purchase a license at hermes-passiv.pages.dev/clean-copy', { status: 200 });
    // Målt 27/9 på cleancopy.tools: `/clean-copy` lå som byte-identisk kopi af
    // forsiden (canonical på `/`). `build_sites.py` publicerer filen ikke
    // længere, men CDN'en beholder den indtil næste deploy — så fakeen skal
    // have den, ellers ville porten være grøn uden at reglen var prøvet.
    if (pathname === '/clean-copy' || pathname === '/da/clean-copy') return new Response('<html lang="en"><head><title>Clean Copy</title><link rel="canonical" href="https://cleancopy.tools/"></head><body>DUPLIKAT AF FORSIDEN</body></html>', { status: 200 });
    if (pathname === '/clean-copy/og-preview.png') return new Response('png', { status: 200 });
    if (request.method !== 'GET' && request.method !== 'HEAD') return new Response('Method not allowed', { status: 405 });
    return new Response('Not found', { status: 404 });
  } } };

const mails = []; let stripeCalls = 0; let resendNede = false; let scanFetches = 0; let privFetches = 0;
let inspectFetches = 0; let headerFetches = 0;
const statsToken = createHash('sha256').update('stats-auth-v1:re_x').digest('hex');
const statsCall = () => call('/api/stats?days=30', { headers: { authorization: `Bearer ${statsToken}` } });
const sessions = {
  cs_live_licenseAAAAAAAAAA: { status: 'complete', payment_status: 'paid', subscription: null, customer_details: { email: 'Buyer@Example.com' },
    line_items: { data: [{ quantity: 1, price: { lookup_key: 'deskuptime-pro-v1' } }] } },
  cs_live_subscripBBBBBBBBBB: { status: 'complete', payment_status: 'paid', subscription: 'sub_1', customer_details: { email: 'a@b.dk' },
    line_items: { data: [{ quantity: 2, price: { lookup_key: 'eucomply-pro-v1' } }] } },
  cs_live_downloadCCCCCCCCCC: { status: 'complete', payment_status: 'paid', subscription: null, customer_details: { email: 'c@d.dk' },
    line_items: { data: [{ quantity: 1, price: { lookup_key: 'eucomply-dpa-v1' } }] } },
  cs_live_unpaidDDDDDDDDDDDD: { status: 'open', payment_status: 'unpaid', line_items: { data: [] } },
  // Betalt download der endnu ikke ligger i KV — tilstanden for alle svyv
  // downloadprodukter, indtil Mads har lagt filerne ind (opgave 24).
  cs_live_manglendeMMMMMMMMMM: { status: 'complete', payment_status: 'paid', subscription: null, customer_details: { email: 'mangler@x.dk' },
    line_items: { data: [{ quantity: 1, price: { lookup_key: 'eucomply-nis2-clauses-v1' } }] } },
  cs_live_raceEEEEEEEEEEEEEE: { status: 'complete', payment_status: 'paid', subscription: null, payment_intent: 'pi_race', customer_details: { email: 'r@x.dk' },
    line_items: { data: [{ quantity: 1, price: { lookup_key: 'transmute-desktop-v1' } }] } },
  cs_live_mailfejlFFFFFFFFFF: { status: 'complete', payment_status: 'paid', subscription: null, customer_details: { email: 'm@x.dk' },
    line_items: { data: [{ quantity: 1, price: { lookup_key: 'eucomply-nda-clauses-v1' } }] } },
  cs_live_ukendtGGGGGGGGGGGG: { status: 'complete', payment_status: 'paid', customer_details: { email: 'u@x.dk' },
    line_items: { data: [{ quantity: 1, price: { lookup_key: null } }] } },
  cs_live_donationHHHHHHHHHH: { status: 'complete', payment_status: 'paid', customer_details: { email: 'd@x.dk' },
    line_items: { data: [{ quantity: 1, price: { lookup_key: 'support-mahope-oss-v1' } }] } },
  cs_live_refundIIIIIIIIIIII: { status: 'complete', payment_status: 'paid', subscription: null, payment_intent: 'pi_ref', customer_details: { email: 'f@x.dk' },
    line_items: { data: [{ quantity: 1, price: { lookup_key: 'deskuptime-pro-v1' } }] } },
  cs_live_subrefundMMMMMMMM: { status: 'complete', payment_status: 'paid', subscription: 'sub_refund', invoice: 'in_refund', customer_details: { email: 'sr@x.dk' },
    line_items: { data: [{ quantity: 1, price: { lookup_key: 'clean-copy-pro-v1' } }] } },
  cs_live_ledgerfailJJJJJJJJJJ: { status: 'complete', payment_status: 'paid', subscription: null, customer_details: { email: 'l@x.dk' },
    line_items: { data: [{ quantity: 1, price: { lookup_key: 'transmute-desktop-v1' } }] } },
  cs_live_pendingfailKKKKKKKKKK: { status: 'complete', payment_status: 'paid', subscription: null, customer_details: { email: 'p@x.dk' },
    line_items: { data: [{ quantity: 1, price: { lookup_key: 'deskuptime-pro-v1' } }] } },
  // Lifetime (founding-pris): engangspris på abonnementsprodukterne. Engangs-
  // links har `invoice_creation` slået til, så købet har en faktura.
  cs_live_lifeccLLLLLLLLLLLL: { status: 'complete', payment_status: 'paid', mode: 'payment', subscription: null, invoice: 'in_life', payment_intent: 'pi_life', customer_details: { email: 'Life@Example.com' },
    line_items: { data: [{ quantity: 1, price: { lookup_key: 'clean-copy-pro-lifetime-v1' } }] } },
  cs_live_lifeeuLLLLLLLLLLLL: { status: 'complete', payment_status: 'paid', mode: 'payment', subscription: null, customer_details: { email: 'eu@x.dk' },
    line_items: { data: [{ quantity: 3, price: { lookup_key: 'eucomply-pro-lifetime-v1' } }] } },
  // Et produkt uden lifetime-udgave, og en lifetime-pris på et abonnement: begge
  // er fejlkonfigurationer, der skal alarmere i stedet for at levere.
  cs_live_lifeukendtLLLLLLLL: { status: 'complete', payment_status: 'paid', mode: 'payment', subscription: null, customer_details: { email: 'x@x.dk' },
    line_items: { data: [{ quantity: 1, price: { lookup_key: 'deskuptime-pro-lifetime-v1' } }] } },
  cs_live_lifesubLLLLLLLLLLL: { status: 'complete', payment_status: 'paid', mode: 'subscription', subscription: 'sub_life_forkert', customer_details: { email: 'y@x.dk' },
    line_items: { data: [{ quantity: 1, price: { lookup_key: 'page-profile-pro-lifetime-v1' } }] } },
  // Almindeligt engangskøb med faktura (DeskUptime): `invoice.paid` for den
  // faktura må ikke give licensen en udløbsdato.
  cs_live_engangfakturaOOOOO: { status: 'complete', payment_status: 'paid', mode: 'payment', subscription: null, invoice: 'in_engang', customer_details: { email: 'o@x.dk' },
    line_items: { data: [{ quantity: 1, price: { lookup_key: 'deskuptime-pro-v1' } }] } },
  cs_live_supccNNNNNNNNNNNNNN: { status: 'complete', payment_status: 'paid', subscription: null, customer_details: { email: 'cc@x.dk' },
    line_items: { data: [{ quantity: 1, price: { lookup_key: 'clean-copy-pro-v1' } }] } },
  cs_live_supdlNNNNNNNNNNNNNN: { status: 'complete', payment_status: 'paid', subscription: null, customer_details: { email: 'dl@x.dk' },
    line_items: { data: [{ quantity: 1, price: { lookup_key: 'eucomply-dpa-v1' } }] } },
};
globalThis.fetch = async (url, opts = {}) => {
  url = String(url);
  if (url.startsWith('https://api.stripe.com/v1/checkout/sessions/')) {
    stripeCalls++;
    const id = decodeURIComponent(url.split('/sessions/')[1].split('?')[0]);
    return new Response(JSON.stringify(sessions[id] || {}), { status: sessions[id] ? 200 : 404 });
  }
  if (url.startsWith('https://api.stripe.com/v1/subscriptions/')) return new Response(JSON.stringify({ current_period_end: 2000000000 }));
  // /api/report henter den scannede side. En side uden cookie-banner, med en
  // form over http og uden HSTS/CSP-header giver fund i hver af de tre
  // kategorier, saa testen kan bevise at Pro-analysen virker. Den bruger
  // Google Analytics og linker samtidig til sin cookiepolitik — det er det
  // virkelige billede, og det er præcis det tilfælde det gamle
  // /cookie|consent|gdpr|cmp/ -tjek passerede, fordi ordet "cookie" stod i
  // href'en. Se de fire GDPR-fixtures nede for sig selv.
  if (url.startsWith('https://scan.example/')) { scanFetches++; return new Response('<html lang="en"><head><title>Test</title><script async src="https://www.googletagmanager.com/gtag/js?id=G-1"></script></head><body><form action="http://insecure.example/send"></form><footer><a href="/cookie-policy">Cookie policy</a></footer></body></html>', { status: 200, headers: { 'content-type': 'text/html; charset=utf-8' } }); }
  // ── URL Inspector og header-tjekker ─────────────────────────────────
  // Begge er åbne ruter der henter en kaldersstyret URL, så stubben skal kunne
  // svare på dem — ellers ville porten være grøn fordi den afviser alt, hvilket
  // er den fejlretning der låser et virkende værktøj ude. Redirect-kæden skal
  // kunne hoppe *ind i* en privat vært: det er præcis det tilfælde, en
  // mål-uden-hop-værn ikke kan se.
  if (url.startsWith('https://inspect.example/')) {
    inspectFetches++;
    if (url === 'https://inspect.example/hop-privat') return new Response('', { status: 302, headers: { location: 'http://169.254.169.254/latest/meta-data/' } });
    if (url === 'https://inspect.example/hop-ok') return new Response('', { status: 301, headers: { location: 'https://inspect.example/final' } });
    return new Response('<html lang="en"><head><title>Inspect</title></head><body>ok</body></html>', { status: 200, headers: { 'content-type': 'text/html', 'strict-transport-security': 'max-age=63072000' } });
  }
  if (url.startsWith('https://headers.example/')) {
    headerFetches++;
    if (url.endsWith('/hop-privat')) return new Response('', { status: 302, headers: { location: 'http://127.0.0.1:8787/admin' } });
    if (url.endsWith('/hop-ok')) return new Response('', { status: 302, headers: { location: 'https://headers.example/final' } });
    return new Response('<html lang="en"><head><title>H</title></head><body>ok</body></html>', { status: 200, headers: { 'content-type': 'text/html', 'x-content-type-options': 'nosniff' } });
  }
  // En privat vært SKAL svare her. Uden denne rute er SSRF-porten grøn af en
  // fejl, der ligner en rettelse: stubben ville kaste på en ukendt URL, så det
  // gamle kode sendte et kald og fik en fejl — og fejlen ligner afvisningen.
  // Med routen svarer den gamle kode 200 *og* giver body'en tilbage, hvilket er
  // selve lækagen. Tælleren er så det eneste bevis på at intet slap ud.
  if (/^https?:\/\/(127\.0\.0\.1|localhost|10\.|192\.168\.|169\.254\.|100\.(6[4-9]|[7-9]\d|1[01]\d|12[0-7])\.|\[::1\]|\[::ffff:|\[64:ff9b:|[\w-]+\.(local|internal|home\.arpa))/.test(url)) {
    privFetches++;
    return new Response('<html><body>INTERNAL SECRET: database=admin/hemmeligt</body></html>', { status: 200, headers: { 'content-type': 'text/html' } });
  }
  // GDPR-fundene skal hvile på bevis, ikke på ord. Fire sider, der dækker de
  // fire former det virkelige web har:
  if (url.startsWith('https://sporing.example/')) return new Response('<html lang="en"><head><title>Butik</title><script async src="https://www.googletagmanager.com/gtag/js?id=G-1"></script></head><body><h1>Butik</h1></body></html>', { status: 200 });
  if (url.startsWith('https://stille.example/')) return new Response('<html lang="en"><head><title>GDPR og cookies forklaret</title><meta name="description" content="Vi tager kun nødvendige cookies"></head><body><h1>Om os</h1><footer><a href="/privatlivspolitik">Privatlivspolitik</a></footer></body></html>', { status: 200 });
  if (url.startsWith('https://cmp.example/')) return new Response('<html lang="en"><head><title>Butik</title><script src="https://cdn.cookielaw.org/scripttemplates/otSDKStub.js" type="text/javascript"></script><script async src="https://www.googletagmanager.com/gtag/js?id=G-1"></script></head><body><h1>Butik</h1></body></html>', { status: 200 });
  if (url.startsWith('https://egen-banner.example/')) return new Response('<html lang="en"><head><title>Butik</title><script async src="https://www.googletagmanager.com/gtag/js?id=G-1"></script></head><body><div id="cookie-banner" class="cookie-consent" role="dialog">Vi bruger cookies</div></body></html>', { status: 200 });
  if (url.startsWith('https://meta-pixel.example/')) return new Response('<html lang="en"><head><title>Butik</title><script src="https://connect.facebook.net/en_US/fbevents.js"></script></head><body><h1>Butik</h1></body></html>', { status: 200 });
  // Ren hjemmeside: ingen tracking og intet ord om cookies. Det gamle tjek
  // gav den en rød GDPR-fejl om "tracking technologies" den ikke bruger —
  // 36 af vores egne 298 sider fik den.
  if (url.startsWith('https://minimal.example/')) return new Response('<html lang="en"><head><title>Cykelsmed</title><meta name="description" content="Reparation af cykler i Aarhus"></head><body><h1>Cykelsmed</h1><footer><a href="/privatlivspolitik">Privatlivspolitik</a></footer></body></html>', { status: 200 });
  if (url === 'https://api.resend.com/emails') { if (resendNede) return new Response('{}', { status: 503 }); mails.push({ ...JSON.parse(opts.body), idem: opts.headers['Idempotency-Key'] }); return new Response('{}', { status: 200 }); }
  if (url.startsWith('https://api.stripe.com/v1/invoices/')) {
    const id = decodeURIComponent(url.split('/invoices/')[1].split('?')[0]);
    const invoice = { parent: { subscription_details: { subscription: 'sub_1' } } };
    if (id === 'in_refund' && url.includes('expand[]=payments')) {
      invoice.payments = { data: [{ payment: { payment_intent: 'pi_sub_refund' } }] };
    }
    return new Response(JSON.stringify(invoice));
  }
  if (url.startsWith('https://api.stripe.com/v1/charges/')) return new Response(JSON.stringify({ id: 'ch_d', payment_intent: 'pi_lic', refunded: false }));
  throw new Error('uventet fetch ' + url);
};

let pass = 0, fail = 0;
const ok = (navn, cond, info = '') => { if (cond) pass++; else { fail++; console.log('FEJL:', navn, info); } };
const call = (path, init) => worker.fetch(new Request('https://mahope.tools' + path, init), env, {});
const sign = (body, t = Math.floor(Date.now() / 1000)) => `t=${t},v1=${createHmac('sha256', WHSEC).update(`${t}.${body}`).digest('hex')}`;

let r;
// 9) Tilbagetrukne arkiver: 301 til den nuværende fil, aldrig en gammel 200.
// Opslås FØR /downloads/-ruten, ellers ville handleDownload tælle den gamle fil
// som et download og den falske README blive serveret videre.
//
// Kaldene sender en rigtig browser-UA. Uden en ville `isAutomatedRequest` sige
// ja, og "tælles ikke som download"-påstanden ville være grøn uden at prøve
// noget — den skal kunne fange den gamle kode, så den skal have en UA.
const UA = { headers: { 'user-agent': 'Mozilla/5.0 (Windows NT 10.0; rv:128.0) Gecko/20100101 Firefox/128.0' } };
r = await call('/downloads/clean-copy-firefox-v1.5.3.zip', { ...UA, redirect: 'manual' });
ok('tilbagetrukket arkiv = 301', r.status === 301, r.status);
ok('301 peger på den nuværende fil', r.headers.get('location') === 'https://mahope.tools/downloads/clean-copy-firefox-v1.5.4.zip', r.headers.get('location'));
ok('den gamle fil serveres ikke, selv om CDN\'en stadig har den', !(await r.text()).includes('nothing leaves your browser'));
r = await call('/downloads/clean-copy-firefox-v1.5.3.zip?cb=1', { ...UA, redirect: 'manual' });
ok('query-streng følger med i reglen', r.status === 301 && r.headers.get('location') === 'https://mahope.tools/downloads/clean-copy-firefox-v1.5.4.zip', r.status + ' ' + r.headers.get('location'));
ok('tilbagetrukket arkiv tælles ikke som download', ![...kv.keys()].some(key => key.includes('clean-copy-firefox-v1.5.3.zip')), [...kv.keys()].join(' '));
r = await call('/downloads/clean-copy-firefox-v1.5.4.zip', { ...UA, redirect: 'manual' });
ok('den nuværende fil er ikke omfattet af reglen', r.status === 404, r.status);
r = await call('/downloads/eaa-checklist.epub', { ...UA, redirect: 'manual' });
ok('en eksisterende fil serveres stadig', r.status === 200);
ok('ikke-tilbagetrukne downloads tælles stadig', [...kv.keys()].some(key => key.includes('download:eaa-checklist.epub')), [...kv.keys()].join(' '));

// 9b) Samme krav for desktop-kildearkivet. Her handler det ikke om privatlivs-
// løftet men om en PRIS: 1.3.3 lovede "$19/year" for EAA-scanneren, som ikke
// har nogen product_key, og den lå stadig i CDN'en med 200 (målt 26/9).
const gammelDesktop = await call('/downloads/eaa-scanner-desktop-src-1.3.3.zip', { ...UA, redirect: 'manual' });
ok('slettet desktop-kildearkiv = 301', gammelDesktop.status === 301, gammelDesktop.status);
ok('301 peger på 1.3.4', gammelDesktop.headers.get('location') === 'https://mahope.tools/downloads/eaa-scanner-desktop-src-1.3.4.zip', gammelDesktop.headers.get('location'));
const gammelDesktopBody = await gammelDesktop.text();
ok('den gamle desktop-pris serveres ikke, selv om CDN\'en stadig har filen', !/\$19\/year|Purchase a license at/.test(gammelDesktopBody), gammelDesktopBody.slice(0, 80));
ok('slettet desktop-arkiv tælles ikke som download', ![...kv.keys()].some(key => key.includes('eaa-scanner-desktop-src-1.3.3.zip')), [...kv.keys()].join(' '));
// Uden denne ville porten være grøn på præcis den fejl den er skrevet til: en
// regel der kun dækker Clean Copy ville efterlade desktop-filen hentbar.
r = await call('/downloads/eaa-scanner-desktop-src-1.3.4.zip', { ...UA, redirect: 'manual' });
ok('det nuværende desktop-arkiv er ikke omfattet af reglen', r.status === 404, r.status);
r = await call('/downloads/eaa-scanner-desktop-src-1.3.3.zip?cb=2', { ...UA, redirect: 'manual' });
ok('query-streng følger med også for desktop-arkivet', r.status === 301 && r.headers.get('location') === 'https://mahope.tools/downloads/eaa-scanner-desktop-src-1.3.4.zip', r.status + ' ' + r.headers.get('location'));

// 9c) cleancopy.tools' to forside-dobletter. Målt 27/9: `cmp` sagde IDENTISK
// mellem `clean-copy.html` og `index.html`, altså to URL'er for én forside med
// canonical på `/` — og hver af dem havde en købsknap. Ruterne er nu 301, så
// gamle links dør ikke, og kun den kanoniske forside kan tage pengene.
// Reglen er host-scoped: `/clean-copy` er en 404 på de tre andre domæner, og
// en 301 til *deres* forside derfra ville være en løgneste.
const onHost = (host, path, init) => worker.fetch(new Request('https://' + host + path, init), env, {});
const ccDup = await onHost('cleancopy.tools', '/clean-copy', { redirect: 'manual' });
ok('cleancopy.tools/clean-copy = 301', ccDup.status === 301, ccDup.status);
ok('301 peger på den kanoniske forside', ccDup.headers.get('location') === 'https://cleancopy.tools/', ccDup.headers.get('location'));
ok('dubletten serveres ikke, selv om CDN\'en stadig har den', !(await ccDup.text()).includes('DUPLIKAT'));
const ccDupDa = await onHost('cleancopy.tools', '/da/clean-copy', { redirect: 'manual' });
ok('cleancopy.tools/da/clean-copy = 301 til /da/', ccDupDa.status === 301 && ccDupDa.headers.get('location') === 'https://cleancopy.tools/da/', ccDupDa.status + ' ' + ccDupDa.headers.get('location'));
const ccDir = await onHost('cleancopy.tools', '/clean-copy/', { redirect: 'manual' });
ok('mappen selv sender også 301 (den har ingen side)', ccDir.status === 301, ccDir.status);
const ccPng = await onHost('cleancopy.tools', '/clean-copy/og-preview.png', { redirect: 'manual' });
ok('filer under mappen serveres stadig', ccPng.status === 200, ccPng.status);
const otherHost = await onHost('mahope.tools', '/clean-copy', { redirect: 'manual' });
ok('reglen gælder kun cleancopy.tools', otherHost.status !== 301, otherHost.status);
const ccHome = await onHost('cleancopy.tools', '/', { redirect: 'manual' });
ok('forsiden selv er ikke omfattet af reglen', ccHome.status !== 301, ccHome.status);

r = await call('/api/lemon-webhook', { method: 'GET' });
ok('gammel Lemon-rute: GET = 404', r.status === 404);r = await call('/api/lemon-webhook', { method: 'POST', body: '{}' });
ok('gammel Lemon-rute: POST = 404', r.status === 404);

// Licens via tak-siden
r = await call('/api/stripe/fulfillment?session_id=cs_live_licenseAAAAAAAAAA');
let j = await r.json();
ok('licens udstedt', r.status === 200 && /^[a-f0-9]{32}$/.test(j.license_key), JSON.stringify(j));
ok('leveringssvar er ikke cross-origin læsbare', !r.headers.get('access-control-allow-origin'));
ok('max 3 enheder', j.max_devices === 3);
ok('én mail', mails.length === 1 && mails[0].to[0] === 'buyer@example.com');
// Hilsenen i kvitteringen er afledt af `kind`, så en licens stadig skal siges
// købt. Uden denne kontrol kunne `thanksLine` blive en global erstatning, der
// skrev "Thank you for supporting" på de tolv produkter der *er* købt — og
// ingen anden arm ville have set det, fordi de kun læser nøglen.
ok('licensens hilsen siger stadig at varen er købt',
  mails[0].text.startsWith('Thanks for buying DeskUptime Pro!')
  && mails[0].html.includes('Thanks for buying <strong>DeskUptime Pro</strong>!')
  && mails[0].subject === 'Your DeskUptime Pro',
  JSON.stringify({ text: mails[0].text.slice(0, 40), emne: mails[0].subject }));
ok('licensens hilsen bruger ikke donationsformuleringen',
  !/supporting|Thank you for your donation/i.test(mails[0].text + mails[0].html + mails[0].subject));
const key = j.license_key;
// Idempotens: samme session igen, også via webhook
r = await call('/api/stripe/fulfillment?session_id=cs_live_licenseAAAAAAAAAA'); j = await r.json();
ok('idempotent nøgle', j.license_key === key);
const body = JSON.stringify({ type: 'checkout.session.completed', data: { object: { id: 'cs_live_licenseAAAAAAAAAA' } } });
r = await call('/api/stripe-webhook', { method: 'POST', body, headers: { 'stripe-signature': sign(body) } });
ok('webhook ok', r.status === 200);
ok('stadig kun én mail', mails.length === 1);
ok('stripe kun kaldt én gang', stripeCalls === 1, stripeCalls);
// Ugyldig signatur / gammel timestamp
r = await call('/api/stripe-webhook', { method: 'POST', body, headers: { 'stripe-signature': 't=1,v1=abc' } });
ok('forkert signatur afvist', r.status === 400);
r = await call('/api/stripe-webhook', { method: 'POST', body, headers: { 'stripe-signature': sign(body, Math.floor(Date.now() / 1000) - 1000) } });
ok('gammel timestamp afvist', r.status === 400);
// Aktivering: produkt-tjek og enhedsgrænse
const act = (b) => call('/api/license/activate', { method: 'POST', body: JSON.stringify(b), headers: { 'content-type': 'application/json' } });
const originalGet = VISITS.get;
VISITS.get = async () => { throw new Error('license KV unavailable'); };
r = await act({ license_key: key, device_id: 'error-test', product: 'deskuptime-pro' });
VISITS.get = originalGet;
ok('uventet licensfejl svarer 503', r.status === 503, r.status);
r = await act({ license_key: key, device_id: 'd1', product: 'transmute-desktop' });
ok('forkert produkt afvist', r.status === 403);
for (const d of ['d1', 'd2', 'd3']) { r = await act({ license_key: key, device_id: d, product: 'deskuptime-pro' }); ok('aktivering ' + d, r.status === 200); }
r = await act({ license_key: key, device_id: 'd4', product: 'deskuptime-pro' });
ok('4. enhed afvist', r.status === 409);
r = await act({ license_key: key, device_id: 'd2' });
ok('aktivering uden produkt afvist', r.status === 400);
r = await call('/api/license/validate', { method: 'POST', body: JSON.stringify({ license_key: key, device_id: 'fremmed', product: 'deskuptime-pro' }), headers: { 'content-type': 'application/json' } });
ok('validate på uaktiveret enhed = ugyldig', (await r.json()).valid === false);
r = await call('/api/license/validate', { method: 'POST', body: JSON.stringify({ license_key: key, device_id: 'd2', product: 'deskuptime-pro' }), headers: { 'content-type': 'application/json' } });
ok('validate på aktiveret enhed = gyldig', (await r.json()).valid === true);
r = await call('/api/license/deactivate', { method: 'POST', body: JSON.stringify({ license_key: key, device_id: 'd3' }), headers: { 'content-type': 'application/json' } });
ok('deaktivering frigør enhed', r.status === 200 && (await r.json()).devices_in_use === 2);
r = await act({ license_key: key, device_id: 'd4', product: 'deskuptime-pro' });
ok('ny enhed efter deaktivering', r.status === 200);
// `instance_id` som alias for `device_id`: de to betalte apps sender
// Lemon Squeezy's feltnavn, så en app der kun får URL'en ompegt skal kunne
// aktivere, validere og frigøre en enhed. Beviset på at det er ET alias og
// ikke en identitet til ved, at samme enhed er gyldig under begge navne.
const lic = (route, b) => call('/api/license/' + route, { method: 'POST', body: JSON.stringify(b), headers: { 'content-type': 'application/json' } });
r = await lic('deactivate', { license_key: key, instance_id: 'd4' });
ok('instance_id frigør en enhed', r.status === 200 && (await r.json()).devices_in_use === 2, r.status);
r = await act({ license_key: key, instance_id: 'd5', product: 'deskuptime-pro' });
ok('instance_id aktiverer', r.status === 200, r.status);
r = await lic('validate', { license_key: key, instance_id: 'd5', product: 'deskuptime-pro' });
ok('instance_id validerer', (await r.json()).valid === true);
r = await lic('validate', { license_key: key, device_id: 'd5', product: 'deskuptime-pro' });
ok('instance_id og device_id er den samme enhed, ikke to', (await r.json()).valid === true);
// Uden denne arm ville porten være grøn på præcis den fejl den er skrevet til:
// et menneskelabel som enhedsidentitet ville optære en af kundens tre maskiner
// på noget deaktiveringen aldrig kan frigøre, fordi appens egen deaktivering
// bruger instance_id.
r = await act({ license_key: key, instance_name: 'd6', product: 'deskuptime-pro' });
ok('instance_name er ikke en enhedsidentitet', r.status === 400 && /Missing device_id/.test((await r.json()).error), r.status);
r = await lic('deactivate', { license_key: key, instance_id: 'd6' });
ok('instance_name binder ingen enhed', r.status === 200 && (await r.json()).devices_in_use === 3, r.status);
// Abonnement: antal × grænse, udløb, fornyelse
r = await call('/api/stripe/fulfillment?session_id=cs_live_subscripBBBBBBBBBB'); j = await r.json();
ok('eucomply 2 sites', j.max_devices === 2 && j.expires_at && j.expires_at.startsWith('2033'), JSON.stringify(j));
const inv = JSON.stringify({ type: 'invoice.paid', data: { object: { subscription: 'sub_1', lines: { data: [{ period: { end: 2100000000 } }] } } } });
r = await call('/api/stripe-webhook', { method: 'POST', body: inv, headers: { 'stripe-signature': sign(inv) } });
const rec = JSON.parse(kv.get('lic:' + j.license_key));
ok('fornyelse forlænger', rec.expires_at.startsWith('2036'), rec.expires_at);
// 8e) Én kvittering, to varianter. Før stod abonnementssætningen kun i
//     tekstvarianten, så det samme køb læstes som to forskellige kvitteringer
//     alt efter hvilken variant mailklienten viste. Nu afledes den fra
//     `expires_at` på ét sted, og armene dømmer begge varianter — så en
//     fremtidig drift kan ikke skille dem igen. De negative kontroller er
//     beviset på at sætningen ikke er en standardsætning: et engangsprodukt
//     må ikke høre om fornyelse i nogen af dem.
const subMail = mails.filter((m) => (m.to || []).includes('a@b.dk')).pop();
ok('abonnementskvitteringen siger fornyelse i tekst OG html',
  !!subMail && /and renews with your subscription/.test(subMail.text) && /and renews with your subscription/.test(subMail.html),
  JSON.stringify(subMail && { text: /renews/.test(subMail.text), html: /renews/.test(subMail.html) }));
ok('begge varianter siger det samme om enhederne',
  !!subMail && /Works on up to 2 device\(s\)/.test(subMail.text) && /Works on up to 2 device\(s\)/.test(subMail.html),
  JSON.stringify(subMail && subMail.text.match(/.*device\(s\).*/g)));
ok('engangskvitteringen taler ikke om fornyelse — hverken i tekst eller html',
  !/renews/i.test(mails[0].text) && !/renews/i.test(mails[0].html), JSON.stringify(mails[0].text.match(/.*device\(s\).*/g)));
ok('engangskøb får ingen kundeportal i kvitteringen',
  !/billing\.stripe\.com/.test(mails[0].text + mails[0].html), mails[0].html.slice(0, 120));
ok('abonnementskøb får kundeportalen i begge varianter',
  !!subMail && /billing\.stripe\.com/.test(subMail.text) && /billing\.stripe\.com/.test(subMail.html));
// Download
kv.set('paidfile:dpa-template.pdf', '%PDF-test');
kv.set('paidfile:dpa-template.md', '# DPA');
r = await call('/api/stripe/fulfillment?session_id=cs_live_downloadCCCCCCCCCC'); j = await r.json();
ok('downloadlinks', j.downloads && j.downloads.length === 2, JSON.stringify(j));
ok('filer der ligger i KV giver ingen manglende-liste', !j.downloads_missing, JSON.stringify(j.downloads_missing));
r = await call(new URL(j.downloads[0].url).pathname);
ok('betalt fil serveres', r.status === 200 && r.headers.get('content-disposition').includes('dpa-template.pdf'));
r = await call(new URL(j.downloads[0].url).pathname.replace('dpa-template.pdf', 'nda-clause-set.pdf'));
ok('fil uden for købet afvist', r.status === 404);
r = await call('/api/download/' + 'a'.repeat(32) + '/dpa-template.pdf');
ok('ukendt token afvist', r.status === 404);
// En betalt fil der ikke ligger i KV må ikke gives en adresse, der svarer 503.
r = await call('/api/stripe/fulfillment?session_id=cs_live_manglendeMMMMMMMMMM'); j = await r.json();
ok('manglende filer giver nul links', Array.isArray(j.downloads) && j.downloads.length === 0, JSON.stringify(j.downloads));
ok('manglende filer nævnes ved navn', j.downloads_missing && j.downloads_missing.length === 2
  && j.downloads_missing.includes('nis2-vendor-clauses.pdf') && j.downloads_missing.includes('nis2-vendor-clauses.md'), JSON.stringify(j.downloads_missing));
ok('svaret indeholder ingen /api/download-adresse', !JSON.stringify(j).includes('/api/download/'), JSON.stringify(j).slice(0, 200));
const manglendeMail = mails.filter(m => (m.to || []).includes('mangler@x.dk')).pop();
const manglendeTekst = (manglendeMail && manglendeMail.text) || '';
ok('kvitteringsmailen har heller ingen død adresse', !!manglendeMail && !JSON.stringify(manglendeMail).includes('/api/download/'), manglendeTekst.slice(0, 200));
ok('kvitteringsmailen siger det er betalt og beder svare', /reply to this email/i.test(manglendeTekst) && /went through/i.test(manglendeTekst), manglendeTekst.slice(0, 240));
// Leveringen selv er urørt: filen er der, så den serveres stadig med sit navn.
kv.set('paidfile:nis2-vendor-clauses.pdf', '%PDF-nis2');
r = await call('/api/stripe/fulfillment?session_id=cs_live_manglendeMMMMMMMMMM'); j = await r.json();
ok('fil lagt ind efter køb giver straks et virkende link', j.downloads.length === 1
  && j.downloads[0].file === 'nis2-vendor-clauses.pdf', JSON.stringify(j.downloads));
ok('manglende-listen er frisk, ikke ledgerens gamle', j.downloads_missing.length === 1
  && j.downloads_missing[0] === 'nis2-vendor-clauses.md', JSON.stringify(j.downloads_missing));
const nis2Token = new URL(j.downloads[0].url).pathname.split('/')[3];
r = await call(new URL(j.downloads[0].url).pathname);
ok('den senere lagte fil hentes med sit navn', r.status === 200 && r.headers.get('content-disposition').includes('nis2-vendor-clauses.pdf'), r.status);
r = await call(`/api/download/${nis2Token}/nis2-vendor-clauses.md`);
ok('en stadig manglende fil i samme køb giver stadig 503', r.status === 503, r.status);
// Ubetalt, ugyldig session, offentlig bundle
r = await call('/api/stripe/fulfillment?session_id=cs_live_unpaidDDDDDDDDDDDD');
ok('ubetalt = 202', r.status === 202);
r = await call('/api/stripe/fulfillment?session_id=../../etc');
ok('ugyldigt id = 400', r.status === 400);
r = await call('/downloads/compliance-bundle.pdf');
ok('offentlig bundle lukket', r.status === 404);
r = await call('/downloads/eaa-checklist.epub');
ok('gratis epub stadig åben', r.status === 200);

// --- Review-fund 25/9 ---
const wh = (type, object) => { const b = JSON.stringify({ type, data: { object } }); return call('/api/stripe-webhook', { method: 'POST', body: b, headers: { 'stripe-signature': sign(b) } }); };
// 1) Tak-side og webhook samtidig: samme nøgle, én record
const mailsFoer = mails.length;
const [a1, a2] = await Promise.all([
  call('/api/stripe/fulfillment?session_id=cs_live_raceEEEEEEEEEEEEEE').then(x => x.json()),
  wh('checkout.session.completed', { id: 'cs_live_raceEEEEEEEEEEEEEE', payment_status: 'paid' }).then(() => null),
]);
const raceKeys = [...kv.keys()].filter(k => k.startsWith('lic:')).map(k => JSON.parse(kv.get(k))).filter(v => v.stripe_session === 'cs_live_raceEEEEEEEEEEEEEE');
ok('samtidig levering giver én licens', raceKeys.length === 1, raceKeys.length);
r = await call('/api/stripe/fulfillment?session_id=cs_live_raceEEEEEEEEEEEEEE'); j = await r.json();
ok('samme nøgle bagefter', j.license_key === a1.license_key);
ok('mails har idempotency-nøgle', mails.slice(mailsFoer).every(m => m.idem === 'sale-cs_live_raceEEEEEEEEEEEEEE'));
const raceFulfillmentKeys = [...kv.keys()].filter(k => k === 'ful:cs_live_raceEEEEEEEEEEEEEE');
ok('race/replay giver én fulfillment-record', raceFulfillmentKeys.length === 1);
ok('fulfillment-ledger har ét produkt', JSON.parse(kv.get(raceFulfillmentKeys[0])).product === 'transmute-desktop');
ok('ingen separat salgstæller skrives', ![...kv.keys()].some(k => k.startsWith('t:all:sales:')));
r = await statsCall(); j = await r.json();
ok('race/replay tæller præcis ét salg', j.sales_status === 'ok' && j.sales.by_product['transmute-desktop'] === 1, JSON.stringify(j.sales));
const originalPut = VISITS.put;
VISITS.put = async (k, v, options) => {
  if (k.startsWith('fulpending:')) throw new Error('pending write failed');
  return originalPut(k, v, options);
};
r = await call('/api/stripe/fulfillment?session_id=cs_live_pendingfailKKKKKKKKKK');
VISITS.put = originalPut;
ok('fejlet pending-markør afbryder levering uden salgsrecord', r.status === 503 && !kv.has('ful:cs_live_pendingfailKKKKKKKKKK'), r.status);
VISITS.put = async (k, v, options) => {
  if (k === 'ful:cs_live_ledgerfailJJJJJJJJJJ' && String(v).includes('"ok":true')) throw new Error('ledger write failed');
  return originalPut(k, v, options);
};
r = await call('/api/stripe/fulfillment?session_id=cs_live_ledgerfailJJJJJJJJJJ');
VISITS.put = originalPut;
ok('ufuldstændig fulfillment svarer 503', r.status === 503, r.status);
for (const key of [...kv.keys()]) if (key.startsWith('fulpending:')) kv.delete(key);
for (const key of [...kv.keys()]) if (key.startsWith('ful:')) kv.delete(key);
r = await statsCall(); j = await r.json();
ok('ufuldstændig fulfillment-ledger er ukendt, ikke nul', j.sales_status === 'unknown' && j.sales === null, JSON.stringify(j.sales));
// 10) /api/stats har sin egen nøgle, ikke mailnøglen. Målt 26/9: tokenet var
// SHA-256 af RESEND_API_KEY, så nøglen der sender købermail fra
// orders@mahope.dk gav også adgang til salgstal — en lækket mailnøgle lækkede
// begge. Fire asserts, fire tilstande: egen nøgle virker, mailnøglen låses ude
// når den egen er sat, mailnøglen virker stadig når den egen IKKE er sat (så
// Mads kan sætte den nye nøgle uden at rapporten låses ude), og uden nogen
// nøgle er ruten ikke konfigureret. Uden den tredje assert ville en fejl i
// rækkefølgen låse rapporten ude, og det er den fejl der gør nytte.
const callWith = (path, init, e) => worker.fetch(new Request('https://mahope.tools' + path, init), e, {});
const tokenFor = (secret) => createHash('sha256').update('stats-auth-v1:' + secret).digest('hex');
const STATS_SECRET = 'st_stats_egen_noegle_0123456789';
const statsWith = (token, e) => callWith('/api/stats?days=30', { headers: { authorization: `Bearer ${token}` } }, e);
r = await statsWith(tokenFor(STATS_SECRET), { ...env, STATS_TOKEN: STATS_SECRET });
ok('egen stats-nøgle giver adgang', r.status === 200 && (await r.json()).ok === true, r.status);
r = await statsWith(statsToken, { ...env, STATS_TOKEN: STATS_SECRET });
ok('mailnøglen låses ude når den egen nøgle er sat', r.status === 401, r.status);
r = await statsWith(statsToken, env);
ok('uden egen nøgel virker mailnøglen stadig, så ingen låses ude', r.status === 200, r.status);
r = await statsWith(statsToken, { ...env, RESEND_API_KEY: '' });
ok('uden nogen nøgle er /api/stats ikke konfigureret', r.status === 503, r.status);
// 2) Nyt fakturaformat (parent.subscription_details) forlænger
r = await wh('invoice.paid', { parent: { subscription_details: { subscription: 'sub_1' } }, lines: { data: [{ period: { end: 2200000000 } }] } });
const subRec = JSON.parse(kv.get('lic:' + kv.get('lic-sub:sub_1')));
ok('nyt fakturaformat forlænger', subRec.expires_at.startsWith('2039'), subRec.expires_at);
// 3) Mail fejler: webhook 500, næste forsøg sender
resendNede = true;
r = await wh('checkout.session.completed', { id: 'cs_live_mailfejlFFFFFFFFFF', payment_status: 'paid' });
ok('webhook 500 når mail fejler', r.status === 500);
resendNede = false;
const m0 = mails.length;
r = await wh('checkout.session.completed', { id: 'cs_live_mailfejlFFFFFFFFFF', payment_status: 'paid' });
ok('retry sender mailen', r.status === 200 && mails.length === m0 + 1 && mails[mails.length - 1].to[0] === 'm@x.dk');
// 4) Ukendt produkt: alarm til Mads, ingen tavs succes
const m1 = mails.length;
r = await call('/api/stripe/fulfillment?session_id=cs_live_ukendtGGGGGGGGGGGG');
ok('ukendt produkt = 404', r.status === 404);
ok('ukendt produkt efterlader ingen pending-markør', ![...kv.keys()].some(key => key.startsWith('fulpending:cs_live_ukendt')));
ok('alarm til Mads', mails.length === m1 + 1 && mails[mails.length - 1].to[0] === 'mads@mahope.dk');
// 5) Donation: ok, ingen alarm, ingen kundemail
const m2 = mails.length;
r = await wh('checkout.session.completed', { id: 'cs_live_donationHHHHHHHHHH', payment_status: 'paid' });
ok('donation ok uden mails', r.status === 200 && mails.length === m2);
// 6) Fuld refundering tilbagekalder licens; delvis gør ikke
r = await call('/api/stripe/fulfillment?session_id=cs_live_refundIIIIIIIIIIII'); const refKey = (await r.json()).license_key;
r = await wh('charge.refunded', { payment_intent: 'pi_ref', refunded: false });
r = await act({ license_key: refKey, device_id: 'x1', product: 'deskuptime-pro' });
ok('delvis refundering bevarer adgang', r.status === 200);
r = await wh('charge.refunded', { payment_intent: 'pi_ref', refunded: true });
r = await act({ license_key: refKey, device_id: 'x2', product: 'deskuptime-pro' });
ok('fuld refundering tilbagekalder', r.status === 403);
r = await call('/api/stripe/fulfillment?session_id=cs_live_subrefundMMMMMMMM');
j = await r.json();
const subRefundKey = j.license_key;
ok('Clean Copy-aktiveringsguide i leveringssvar', j.activate_url === 'https://cleancopy.tools/activate/', j.activate_url);
r = await wh('invoice.paid', { id: 'in_refund', subscription: 'sub_refund', lines: { data: [{ period: { end: 2000000000 } }] } });
ok('første faktura kobler payment intent til licens', kv.get('lic-pi:pi_sub_refund') === subRefundKey, kv.get('lic-pi:pi_sub_refund'));
r = await wh('charge.refunded', { payment_intent: 'pi_sub_refund', refunded: true });
ok('abonnementsrefunding tilbagekalder licens', (await r.json()).revoked === true);
r = await act({ license_key: subRefundKey, device_id: 'sub-refund', product: 'clean-copy-pro' });
ok('refunderet abonnement giver 403', r.status === 403, r.status);
r = await call('/api/download/' + 'b'.repeat(32) + '/%E0%A4%A');
ok('ødelagt kodning = 404', r.status === 404);
// 6b) Lifetime: licens uden udløb, som abonnements-webhooks ikke kan røre.
{
  const mL = mails.length;
  r = await call('/api/stripe/fulfillment?session_id=cs_live_lifeccLLLLLLLLLLLL');
  j = await r.json();
  const lifeKey = j.license_key;
  ok('lifetime: licens udstedt', r.status === 200 && /^[a-f0-9]{32}$/.test(lifeKey), JSON.stringify(j));
  ok('lifetime: samme produkt som abonnementet', j.product === 'clean-copy-pro', j.product);
  ok('lifetime: lifetime=true og ingen udløbsdato', j.lifetime === true && j.expires_at === null, JSON.stringify(j));
  ok('lifetime: ingen kundeportal og intet abonnement', j.billing_portal === undefined && j.subscription === undefined, JSON.stringify(j));
  ok('lifetime: produktnavnet siger Lifetime', j.product_name === 'Clean Copy Pro Lifetime', j.product_name);
  ok('lifetime: 5 enheder som abonnementet', j.max_devices === 5, j.max_devices);
  const rec = JSON.parse(kv.get(`lic:${lifeKey}`));
  ok('lifetime: KV-posten er lifetime uden udløb', rec.lifetime === true && rec.expires_at === null && rec.stripe_subscription === null && rec.product === 'clean-copy-pro', JSON.stringify(rec));
  ok('lifetime: ingen abonnementskobling i KV', ![...kv.keys()].some(k => k.startsWith('lic-sub:') && kv.get(k) === lifeKey));
  const mail = mails[mL];
  ok('lifetime: én mail til køberen', mails.length === mL + 1 && mail.to[0] === 'life@example.com', JSON.stringify(mail && mail.to));
  ok('lifetime: mailens emne siger Lifetime', mail && mail.subject === 'Your Clean Copy Pro Lifetime', mail && mail.subject);
  ok('lifetime: mailen siger ingen fornyelse og intet udløb i både tekst og HTML',
    mail && /Lifetime license: one payment, no renewal and no expiry/.test(mail.text) && /Lifetime license: one payment, no renewal and no expiry/.test(mail.html), mail && mail.text);
  ok('lifetime: mailen nævner hverken fornyelse eller kundeportal',
    mail && !/renews|Manage your subscription/i.test(mail.text + mail.html), mail && mail.text);

  // Aktivering og validering svarer lifetime uden udløb.
  r = await act({ license_key: lifeKey, device_id: 'life-1', product: 'clean-copy-pro' });
  let a = await r.json();
  ok('lifetime: activate = 200 med lifetime og uden udløb', r.status === 200 && a.activated === true && a.lifetime === true && a.expires_at === null, JSON.stringify(a));
  r = await call('/api/license/validate', { method: 'POST', body: JSON.stringify({ license_key: lifeKey, device_id: 'life-1', product: 'clean-copy-pro' }), headers: { 'content-type': 'application/json' } });
  a = await r.json();
  ok('lifetime: validate = gyldig med lifetime og uden udløb', r.status === 200 && a.valid === true && a.lifetime === true && a.expires_at === null, JSON.stringify(a));
  r = await act({ license_key: lifeKey, device_id: 'life-1', product: 'page-profile-pro' });
  ok('lifetime: nøglen låser ikke et andet produkt op', r.status === 403, r.status);
  // Et almindeligt abonnement får ikke feltet.
  r = await call('/api/license/validate', { method: 'POST', body: JSON.stringify({ license_key: subRefundKey, device_id: 'x', product: 'clean-copy-pro' }), headers: { 'content-type': 'application/json' } });
  ok('abonnement: intet lifetime-felt', !('lifetime' in (await r.json())));

  // Fakturaen for engangskøbet betales (invoice_creation), og en fremmed
  // abonnementsfaktura peger ved en fejl på samme faktura-id: ingen af dem må
  // give licensen en udløbsdato.
  r = await wh('invoice.paid', { id: 'in_life', lines: { data: [{ period: { end: 1800000000 } }] } });
  ok('lifetime: invoice.paid for engangsfakturaen accepteres', r.status === 200, r.status);
  ok('lifetime: invoice.paid giver ingen udløbsdato', JSON.parse(kv.get(`lic:${lifeKey}`)).expires_at === null, kv.get(`lic:${lifeKey}`));
  r = await wh('invoice.paid', { id: 'in_life', subscription: 'sub_fremmed', lines: { data: [{ period: { end: 1800000000 } }] } });
  ok('lifetime: en abonnementsfaktura kan ikke sætte udløb', JSON.parse(kv.get(`lic:${lifeKey}`)).expires_at === null, kv.get(`lic:${lifeKey}`));
  r = await call('/api/license/validate', { method: 'POST', body: JSON.stringify({ license_key: lifeKey, device_id: 'life-1', product: 'clean-copy-pro' }), headers: { 'content-type': 'application/json' } });
  a = await r.json();
  ok('lifetime: stadig gyldig uden udløb efter fakturahændelser', a.valid === true && a.expires_at === null && a.lifetime === true, JSON.stringify(a));
  // Workeren håndterer ikke abonnementsophør som hændelse; det skal heller ikke ramme lifetime.
  r = await wh('customer.subscription.deleted', { id: 'sub_fremmed', status: 'canceled' });
  ok('lifetime: customer.subscription.deleted ignoreres', r.status === 200 && JSON.parse(kv.get(`lic:${lifeKey}`)).status === 'active', kv.get(`lic:${lifeKey}`));

  // EUComply Pro lifetime: antal websites følger antal købt.
  r = await call('/api/stripe/fulfillment?session_id=cs_live_lifeeuLLLLLLLLLLLL');
  j = await r.json();
  ok('lifetime EUComply: 3 websites, uden udløb', j.max_devices === 3 && j.lifetime === true && j.expires_at === null && j.product === 'eucomply-pro', JSON.stringify(j));

  // Fejlkonfigurationer leverer ikke, men alarmerer Mads.
  let mA = mails.length;
  r = await call('/api/stripe/fulfillment?session_id=cs_live_lifeukendtLLLLLLLL');
  ok('lifetime på produkt uden lifetime-udgave = 404 og alarm', r.status === 404 && mails.length === mA + 1 && mails[mA].to[0] === 'mads@mahope.dk', r.status);
  mA = mails.length;
  r = await call('/api/stripe/fulfillment?session_id=cs_live_lifesubLLLLLLLLLLL');
  ok('lifetime-pris på et abonnement = 404 og alarm', r.status === 404 && mails.length === mA + 1 && mails[mA].to[0] === 'mads@mahope.dk', r.status);

  // Fuld refundering tilbagekalder stadig en lifetime-licens.
  r = await wh('charge.refunded', { payment_intent: 'pi_life', refunded: true });
  ok('lifetime: fuld refundering tilbagekalder', (await r.json()).revoked === true);
  r = await act({ license_key: lifeKey, device_id: 'life-2', product: 'clean-copy-pro' });
  ok('lifetime: refunderet licens giver 403', r.status === 403, r.status);

  // Almindeligt engangskøb (DeskUptime) med faktura: invoice.paid må ikke give
  // udløb. Før rettelsen fik licensen "periodens slut + 7 dage".
  r = await call('/api/stripe/fulfillment?session_id=cs_live_engangfakturaOOOOO');
  const onceKey = (await r.json()).license_key;
  r = await wh('invoice.paid', { id: 'in_engang', lines: { data: [{ period: { end: 1800000000 } }] } });
  ok('engangskøb: invoice.paid giver ingen udløbsdato', JSON.parse(kv.get(`lic:${onceKey}`)).expires_at === null, kv.get(`lic:${onceKey}`));
}

// 7) Svaradresse følger produktets domæne; produkter uden `home` falder tilbage til mahope.tools
const m7 = mails.length;
r = await call('/api/stripe/fulfillment?session_id=cs_live_supccNNNNNNNNNNNNNN');
ok('Clean Copy Pro leveret', r.status === 200, r.status);
ok('svaradresse følger Clean Copy-domænet', mails[m7] && mails[m7].reply_to === 'support@cleancopy.tools', JSON.stringify(mails[m7] && mails[m7].reply_to));
r = await call('/api/stripe/fulfillment?session_id=cs_live_supdlNNNNNNNNNNNNNN');
ok('download leveret', r.status === 200, r.status);
ok('produkt uden home bruger mahope.tools', mails[m7 + 1] && mails[m7 + 1].reply_to === 'support@mahope.tools', JSON.stringify(mails[m7 + 1] && mails[m7 + 1].reply_to));
ok('ingen kundemail svarer til en privat indbakke', mails.every(m => !String(m.reply_to || '').startsWith('mads@')));
// 8) Kundeportal: kun abonnenter må opsige selv
const PORTAL = 'https://billing.stripe.com/p/login/6oU4gy76PgvgdBIdAXbMQ00';
ok('Clean Copy Pro (abonnement) får kundeportalen i mailen', mails[m7].text.includes(PORTAL) && mails[m7].html.includes(PORTAL), JSON.stringify(mails[m7].text));
ok('EUComply Pro (abonnement) får kundeportalen', mails[1].text.includes(PORTAL) && mails[1].html.includes(PORTAL), JSON.stringify(mails[1].text));
ok('DeskUptime Pro (engangskøb) får ikke kundeportalen', !mails[0].text.includes(PORTAL) && !mails[0].html.includes('billing.stripe.com'), JSON.stringify(mails[0].text));
ok('download-køb får ikke kundeportalen', !mails[2].text.includes(PORTAL) && !mails[2].html.includes('billing.stripe.com'));
const mSub = mails.filter(m => m.text.includes(PORTAL));
ok('kun de tre årlige produkter får kundeportalen', mSub.length === 3 && mSub.every(m => /Your (Clean Copy Pro|EUComply Pro|Page Profile Pro)/.test(m.subject)), mSub.map(m => m.subject).join(' | '));
// 8b) EUComply Pro: et link med navnet "Activate it here" er ikke en
//     instruktion. `activate_url` lå på /pricing/ — en butiksvindue med 0 input
//     og uden nøgle — så køberen af det dyreste produkt fik en mail og en knap
//     "How to activate" på /thanks, der begge endte i en butik. Målt 27/9.
const euMail = mails[1];
ok('EUComply Pro: aktiveringslinket er ikke længere en prisside', euMail.text.includes('https://eucomplypro.com/pro/') && !euMail.text.includes('eucomplypro.com/pricing/'), JSON.stringify(euMail.text));
ok('EUComply Pro: mailen siger hvor nøglen sættes ind', euMail.text.includes('Where to paste the key: In WordPress: EUComply > Settings, in the "Pro License Key" field.'), JSON.stringify(euMail.text));
ok('EUComply Pro: HTML-mailen har samme instruktion', euMail.html.includes('Pro License Key') && euMail.html.includes('eucomplypro.com/pro/'), JSON.stringify(euMail.html));
ok('EUComply Pro: nøglen og aktiveringslinjen er stadig i mailen', /Your license key:\n[a-f0-9]{32}/.test(euMail.text) && euMail.text.includes('Activate it here:'), JSON.stringify(euMail.text));
// Negativ kontrol: kun det produkt der har brug for en instruktion får en.
// Ellers ville mailen bare få en standardsætning, der intet beviser.
// Negativ kontrol: kun produkter med en *målt* aktivering får en instruktion.
// Ellers ville mailen bare få en standardsætning, der intet beviser. Denne arm
// blev sat op 27/9 med DeskUptime som modpart og sagde "kun EUComply"; da
// næste iteration målte de fem `home`-sider, viste det at DeskUptime også har
// et dokumenteret sted (appen spørger ved første start, målt på
// site/deskuptime/index.html:99), så armen dømmer nu det den egentlig skal:
// **intet EUComply-materiale i et andet produkts mail.**
ok('DeskUptime Pro får sin egen instruktion, ikke EUComplys', mails[0].text.includes('Where to paste the key: The desktop app asks for the licence key') && !mails[0].text.includes('Pro License Key') && !mails[0].text.includes('EUComply'), JSON.stringify(mails[0].text));
ok('et downloadprodukt får ingen nøgleinstruktion', !mails[2].text.includes('Where to paste the key'), JSON.stringify(mails[2].text));
r = await call('/api/stripe/fulfillment?session_id=cs_live_supccNNNNNNNNNNNNNN');
j = await r.json();
ok('Clean Copy Pro leveringssvar bærer kundeportalen', j.subscription === true && j.billing_portal === PORTAL, JSON.stringify(j));
r = await call('/api/stripe/fulfillment?session_id=cs_live_licenseAAAAAAAAAA');
j = await r.json();
ok('engangskøb har ingen kundeportal i leveringssvaret', j.subscription === undefined && !j.billing_portal, JSON.stringify(j));
// 9) EUComply Pro: rapporten er betalt indhold, så den skal regnes server-side.
//    Før dette laa GDPR/NIS2-fundene i DOM'en, før nøglen blev tastet, og
//    @media print skjulte kun licensfeltet — Ctrl+P gav den betalte PDF.
r = await call('/api/stripe/fulfillment?session_id=cs_live_subscripBBBBBBBBBB');
j = await r.json();
const euKey = j.license_key;
// Det er denne `activate_url` /thanks' knap "How to activate" bruger, så den
// skal pege på en side der forklarer aktivering — ikke på en prisside.
ok('EUComply Pro: leveringssvaret peger på Pro-siden, ikke på /pricing/', j.activate_url === 'https://eucomplypro.com/pro/', JSON.stringify(j.activate_url));
// 8c) /thanks' knap "How to activate" er et link, ikke en instruktion. 8b fik
//     kvitteringsmailen til at sige hvor nøglen sættes ind; her læser køberen
//     det samme på købssiden. Feltet er **additivt** og findes kun på de
//     produkter der har en målt aktivering (målingen står over STRIPE_PRODUCTS):
//     2 af 5 licensprodukter. Derfor er hver arm dømt på sit rigtige produkt,
//     og de to negative kontroller er ikke pynt — de er beviset på at feltet
//     ikke er en standardsætning.
r = await call('/api/stripe/fulfillment?session_id=cs_live_subscripBBBBBBBBBB'); j = await r.json();
ok('EUComply Pro: leveringssvaret siger hvor nøglen sættes ind', j.activate_hint === 'In WordPress: EUComply > Settings, in the "Pro License Key" field. On the web: https://mahope.tools/compliance-report', JSON.stringify(j.activate_hint));
r = await call('/api/stripe/fulfillment?session_id=cs_live_licenseAAAAAAAAAA'); j = await r.json();
ok('DeskUptime Pro: leveringssvaret siger hvad appen gør med nøglen', j.activate_hint === 'The desktop app asks for the licence key the first time you start it. Free without a key: the command-line tool.', JSON.stringify(j.activate_hint));
ok('licensnøglen er stadig i svaret — instruktionen har ikke fortrængt den', /^[a-f0-9]{32}$/.test(j.license_key) && j.activate_url === 'https://deskuptime.com/', JSON.stringify(j));
// Negativ kontrol 1: Clean Copy Pros `home` ER aktiveringen (HowTo med tre
// trin), så en instruktion dér ville være støj. Mangler feltet her, så skærmen
// ikke kan have fået en standardsætning.
r = await call('/api/stripe/fulfillment?session_id=cs_live_supccNNNNNNNNNNNNNN'); j = await r.json();
ok('Clean Copy Pro får ingen instruktion — hans side ER aktiveringen', j.activate_hint === undefined && j.activate_url === 'https://cleancopy.tools/activate/', JSON.stringify(j.activate_hint));
// Negativ kontrol 2: et downloadprodukt må ALDRIG få besked om at indsætte en
// nøgle. Denne arm kan ikke fyre alene: `eucomply-dpa` har ingen `activateHint`,
// så "feltet mangler" er en tautologi, ikke et bevis — målt 27/9 ved at hænge
// feltet i downloadgrenen, hvor armen stadig var grøn. Beviset ligger derfor i
// tabellen nedenfor, der kan bide, fordi den dømmer *hvilke* produkter der har
// et hint. Leveringssvaret for et download er ellers uændret af denne diff.
r = await call('/api/stripe/fulfillment?session_id=cs_live_downloadCCCCCCCCCC'); j = await r.json();
ok('download får ingen nøgleinstruktion', j.activate_hint === undefined && Array.isArray(j.downloads), JSON.stringify(j.activate_hint));
// Tabelinvarianten der kan bide: kun et `kind: 'license'` må have `activateHint`.
// Hvis en fremtidig iteration skriver en aktivering på et download, dør den her.
const workerSrc = await readFileSync(process.argv[2] || new URL('../site/_worker.js', import.meta.url), 'utf8');
const tableRows = [...workerSrc.matchAll(/^\s*'([a-z0-9-]+)':\s*\{ name: '[^']*', kind: '(\w+)'([^\n]*)\}/gm)];
const hintOnNonLicense = tableRows.filter(([, key, kind, rest]) => kind !== 'license' && rest.includes('activateHint')).map(([, key]) => key);
ok('intet download eller donation har en aktiveringsinstruktion', hintOnNonLicense.length === 0, hintOnNonLicense.join(', '));
const hintedLicenses = tableRows.filter(([, key, kind, rest]) => kind === 'license' && rest.includes('activateHint')).map(([, key]) => key).sort();
ok('kun de to målte produkter har en instruktion (2 af 5 licensprodukter)', JSON.stringify(hintedLicenses) === JSON.stringify(['deskuptime-pro', 'eucomply-pro']), hintedLicenses.join(', '));
// 8d) `/api/license/lookup` var utestet og er ændret af samme diff, så den får
//     sine egne arme. Den skal sige det samme som leveringssvaret — ellers er
//     den ene af de to veje en kunde kan gå ind ad en sted, hvor svaret er
//     tyndere. Nøglen i KV er skrevet af den hash mailen blev gemt under, så
//     testen henter den nøgle, en kunde faktisk ville skrive.
const look = (b) => call('/api/license/lookup', { method: 'POST', body: JSON.stringify(b), headers: { 'content-type': 'application/json' } });
r = await look({ order_id: 'cs_live_licenseAAAAAAAAAA', email: 'buyer@example.com' }); j = await r.json();
ok('nøgleopslag: DeskUptime Pro finder nøglen og siger hvor den sættes ind', r.status === 200 && j.ok === true && /^[a-f0-9]{32}$/.test(j.license_key)
  && j.activate_hint === 'The desktop app asks for the licence key the first time you start it. Free without a key: the command-line tool.', JSON.stringify(j));
ok('nøgleopslag: aktiveringslinket er urørt', j.activate_url === 'https://deskuptime.com/', JSON.stringify(j.activate_url));
r = await look({ order_id: 'cs_live_licenseAAAAAAAAAA', email: 'indrigere@x.dk' }); j = await r.json();
ok('nøgleopslag med forkert mail giver intet', r.status === 404 && j.license_key === undefined, JSON.stringify(j));
r = await look({ order_id: 'cs_live_subscripBBBBBBBBBB', email: 'a@b.dk' }); j = await r.json();
ok('nøgleopslag: EUComply Pro har samme instruktion som leveringssvaret', j.ok === true && j.activate_hint && j.activate_hint.includes('Pro License Key') && j.activate_url === 'https://eucomplypro.com/pro/', JSON.stringify(j));
const rep = (b) => call('/api/report', { method: 'POST', body: JSON.stringify(b), headers: { 'content-type': 'application/json' } });
r = await rep({ license_key: 'a'.repeat(32), device_id: 'pro-dev', product: 'eucomply-pro', url: 'https://scan.example/' });
ok('rapport uden gyldig nøgle er afvist', r.status === 402, r.status);
r = await rep({ license_key: key, device_id: 'd1', url: 'https://scan.example/' });
ok('nøgle til et andet produkt giver ikke rapporten', r.status === 402, r.status);
r = await rep({ license_key: euKey, device_id: 'pro-dev', url: 'https://scan.example/' });
ok('nøgle uden aktivering på maskinen giver ikke rapporten', r.status === 402, r.status);
r = await act({ license_key: euKey, device_id: 'pro-dev', product: 'eucomply-pro' });
ok('EUComply Pro kan aktiveres', r.status === 200, r.status);
r = await rep({ license_key: euKey, device_id: 'pro-dev', url: 'https://scan.example/' });
j = await r.json();
const ids = (j.findings || []).map(f => f.id);
ok('gyldig nøgle får serverens Pro-fund', r.status === 200 && j.ok === true, r.status);
ok('NIS2, GDPR og header-fund er med', ['FORM_HTTP', 'COOKIE_BANNER', 'SEC_HSTS', 'SEC_CSP'].every(i => ids.includes(i)), ids.join(','));
ok('alle fund har en rettelse eller er notices', (j.findings || []).every(f => f.id && f.sev && f.msg));
r = await call('/api/report?url=https://scan.example/');
ok('GET på rapporten er 405', r.status === 405, r.status);
r = await rep({ license_key: euKey, device_id: 'pro-dev', url: 'https://127.0.0.1/' });
ok('rapporten henter ikke private værter (SSRF)', r.status === 400, r.status);
r = await rep({ license_key: euKey, device_id: 'pro-dev', url: 'https://scan.example.local/' });
ok('.local-vært afvist', r.status === 400, r.status);

// GDPR-fundene skal ramme det de er lavet til. Det gamle tjek var
// /cookie|consent|gdpr|cmp/ over hele HTML'en, altså et ordmønster: en side
// der bruger Google Analytics og samtidig linker til den cookiepolitik GDPR
// kræver, blev meldt som renset, fordi "cookie" stod i href'en. Målt på vores
// egne 298 sider passede 254 uden eneste consent-script, og 36 fik en rød
// GDPR-fejl uden at sætte én eneste cookie.
const idsFor = async (url) => (await (await rep({ license_key: euKey, device_id: 'pro-dev', url })).json()).findings.map(f => f.id);
let g = await idsFor('https://sporing.example/');
ok('GA uden banner giver COOKIE_BANNER og GA_NO_CONSENT', g.includes('COOKIE_BANNER') && g.includes('GA_NO_CONSENT'), g.join(','));
g = await idsFor('https://meta-pixel.example/');
ok('Meta-pixel uden banner giver COOKIE_BANNER og FB_NO_CONSENT', g.includes('COOKIE_BANNER') && g.includes('FB_NO_CONSENT'), g.join(','));
g = await idsFor('https://cmp.example/');
ok('en consent-platform tæller som banner', !g.includes('COOKIE_BANNER') && !g.includes('GA_NO_CONSENT') && g.includes('COOKIE_SCRIPTS'), g.join(','));
g = await idsFor('https://egen-banner.example/');
ok('et eget banner-element tæller som banner', !g.includes('COOKIE_BANNER') && !g.includes('GA_NO_CONSENT'), g.join(','));
g = await idsFor('https://stille.example/');
ok('en side der hverken tracker eller har banner får ingen GDPR-fejl', !g.includes('COOKIE_BANNER') && !g.includes('GA_NO_CONSENT') && !g.includes('FB_NO_CONSENT'), g.join(','));
ok('…og siger i stedet hvorfor der ikke står et GDPR-fund', g.includes('NO_ANALYTICS'), g.join(','));
g = await idsFor('https://minimal.example/');
ok('en side uden tracking og uden cookie-ord får ingen GDPR-fejl', !g.includes('COOKIE_BANNER') && !g.includes('GA_NO_CONSENT') && !g.includes('FB_NO_CONSENT'), g.join(','));
ok('en cookiepolitik-ling giver ikke en renset mangel-melding', (await idsFor('https://scan.example/')).includes('COOKIE_BANNER'));

// Selve hullet: hvis nøglen ikke gør Pro-fundene afhængige af serveren, er
// Ctrl+P stadig en gratis vej til det betalte. Porten læser derfor kilden.
const reportHtml = await readFileSync(new URL('../site/compliance-report.html', import.meta.url), 'utf8');
const clientSide = reportHtml.slice(reportHtml.indexOf('function runScan'), reportHtml.indexOf('// ── License validation'));
ok('ingen GDPR/NIS2-tjek er beregnet i browseren', !/COOKIE_BANNER|SEC_HSTS|OG_TITLE|hasCookieBanner/.test(clientSide));
ok('siden henter Pro-fund fra /api/report', /fetch\('\/api\/report'/.test(reportHtml));
ok('print uden licens er mærket som gratis', /print-only/.test(reportHtml));

// 10) Grænse på de ruter, der henter en URL. Målt 26/9: ingen af de seks
//     ruter, der henter en kalders URL eller gør tungt arbejde, havde nogen
//     tæller, mens de tre billige (lookup, fulfillment, demo) alle havde. Alle
//     fire domæner deler én worker, så en løbet kvote tager også
//     /api/license/validate med — den rute betalende kunder er afhængige af.
//
//     Hver test bruger sin egen cf-connecting-ip, så tællerne ikke smitter
//     ind i den 'unknown'-spand som resten af suiten deler.
const ip = (n) => ({ headers: { 'cf-connecting-ip': `203.0.113.${n}` } });
const scanGet = (init) => call('/scan-proxy?url=https%3A%2F%2Fscan.example%2F', init);

// Under grænsen: kaldet går igennem og henter stadig. Beviser at tælleren
// ikke har brudt scanneren, som er den offentlige indgang.
r = await scanGet(ip(1));
ok('scan-proxy under grænsen henter stadig siden', r.status === 200, r.status);

// Over grænsen: 429, og — det der adskiller det fra en låst ude-kunde — med
// CORS-headers, så browseren kan læse fejlen. Uden dem ser siden en uoplys
// netværksfejl, som er præcis den følelse en 429 aldrig må give.
for (let i = 1; i < 60; i++) await scanGet(ip(1));
r = await scanGet(ip(1));
const overBody = await r.json().catch(() => null);
ok('scan-proxy over grænsen giver 429', r.status === 429, r.status);
ok('429 kan læses i browseren (CORS med)', r.headers.get('Access-Control-Allow-Origin') === '*', r.headers.get('Access-Control-Allow-Origin'));
ok('429 siger det er timegrænsen, ikke noget andet', /hour/i.test(overBody && overBody.error || ''), JSON.stringify(overBody));

// Det vigtigste: en 429 skal spare arbejdet, ikke bare svare hurtigt. Før
// kaldet må der ikke være sket en eneste ude-fetch.
const fetchesBefore = scanFetches;
for (let i = 0; i < 5; i++) await scanGet(ip(1));
ok('en 429 henter ikke den url igen', scanFetches === fetchesBefore, `${scanFetches - fetchesBefore} fetch`);

// Scoperne er adskilte. Et bureau der scanner mange kunders sider må ikke brænde
// sin egen rapport- eller headerkvote af — og omvendt. Samme IP, anden rute.
r = await call('/api/header-check?url=https%3A%2F%2Fscan.example%2F', ip(1));
ok('en låst scan-proxy låser ikke header-check', r.status !== 429, r.status);

// Fejler åbent: en tæller der går ned må aldrig tage værktøjet med. Det er den
// modsatte fejlretning af den vi lukker her, og den er den der låser kunder ude.
const rlGet = VISITS.get;
VISITS.get = async (k) => { if (String(k).startsWith('rl:')) throw new Error('rate-KV nede'); return rlGet(k); };
r = await scanGet(ip(2));
ok('en nede tæller-KV låser ikke scanneren ude', r.status === 200, r.status);
VISITS.get = rlGet;

// Betalt rute: tælleren sidder efter licenstjekket, så en ugyldig nøgle koster
// os intet og må ikke æde en kundes kvote. Den betalte sti skal også virke
// under sin egen grænse — det er den, kunden betalte for.
r = await rep({ license_key: 'a'.repeat(32), device_id: 'pro-dev', product: 'eucomply-pro', url: 'https://scan.example/' });
ok('en ugyldig nøgle tæller ikke på rapportkvoten', r.status === 402, r.status);
const repIp = { ...ip(3), method: 'POST', body: JSON.stringify({ license_key: euKey, device_id: 'pro-dev', url: 'https://scan.example/' }), headers: { 'content-type': 'application/json', 'cf-connecting-ip': '203.0.113.3' } };
r = await call('/api/report', repIp);
ok('en betalt kunde får stadig sin rapport under grænsen', r.status === 200 && (await r.json()).ok === true, r.status);
for (let i = 1; i < 120; i++) await call('/api/report', repIp);
r = await call('/api/report', repIp);
ok('rapporten over grænsen giver 429 med timegrænsen', r.status === 429 && /hour/i.test((await r.json().catch(() => ({}))).error || ''), r.status);

// ── SSRF på den åbne rute ────────────────────────────────────────────
// /scan-proxy er ubeskyttet af licens og deles af seks offentlige værktøjer,
// så en manglende værn-der er en informationsudlæsning uden betaling. Den skal
// afvise præcis de værter, rapporten allerede afviste, ellers svarer de to
// ruter forskelligt på samme URL — og det er sådan en kunde kommer til at få
// skylden lagt på sin egen nøgle (se de to tests efter dette).
const PRIVATE_TARGETS = [
  ['http://127.0.0.1:8787/', 'loopback'],
  ['http://192.168.1.10/', 'RFC1918'],
  ['http://10.0.0.5/', 'RFC1918'],
  ['http://169.254.169.254/latest/meta-data/', 'link-local (cloud metadata)'],
  ['http://[::1]:8080/', 'IPv6 loopback'],
  ['http://printer.local/', '.local'],
  ['http://100.64.0.1/', 'CGNAT'],
];
for (const [target, why] of PRIVATE_TARGETS) {
  r = await call('/scan-proxy?url=' + encodeURIComponent(target), ip(4));
  const body = await r.json().catch(() => ({}));
  ok(`scan-proxy afviser ${why}`, r.status === 400 && /cannot be scanned/i.test(body.error || ''), `${target} -> ${r.status} ${JSON.stringify(body).slice(0, 90)}`);
  // Samme afvisning på den betalte rute. De to skal være enige, ellers opstår
  // fundet her: en kunde der har fået sin frie scanning af en privat vært.
  r = await call('/api/report', { ...ip(5), method: 'POST', headers: { 'content-type': 'application/json', 'cf-connecting-ip': '203.0.113.5' },
    body: JSON.stringify({ license_key: euKey, device_id: 'pro-dev', product: 'eucomply-pro', url: target }) });
  const rbody = await r.json().catch(() => ({}));
  ok(`rapporten afviser ${why} på samme måde`, r.status === 400 && /cannot be scanned/i.test(rbody.error || ''), `${target} -> ${r.status}`);
}
// Det stærkeste bevis: stubben ville have svaret en privat vært med en 200 og
// en krop. Der kom 0 af de 7, så ingen anmodning slap ud overhovedet.
ok('ingen privat vært blev hentet overhovedet', privFetches === 0, `${privFetches} ude-fetch`);

// Den offentlige rute skal stadig virke. Uden denne ville porten være grøn fordi
// den afviser alt — det er den fejlretning, der låser et virkende værktøj ude.
r = await call('/scan-proxy?url=https%3A%2F%2Fscan.example%2F', ip(4));
ok('en offentlig side scanner stadig', r.status === 200 && (await r.json()).ok === true, r.status);

// Værterne skal heller ikke slippe igennem som ren tekst, f.eks. "127.0.0.1.nip.io".
// Vi lader den ligge som en kendt begrænsning i stedet for at tro at vi dækker
// DNS-rebinding: kun den bogstavelige IP og de fire suffikser afvises.
// Beviset på at porten ikke er grøn af vilje: en URL med en offentlig vært
// men ugyldigt protokol er stadig afvist med dens egen tekst.
r = await call('/scan-proxy?url=' + encodeURIComponent('file:///etc/passwd'), ip(4));
ok('file:// er afvist med protokol-teksten', r.status === 400 && /http/i.test((await r.json().catch(() => ({}))).error || ''), r.status);

// ── /api/url-inspect var død på hvert eneste kald ────────────────────
// Målt 30/9 på den live udgivelse: GET /api/url-inspect svarede 500 med
// Cloudflares "error code: 1101" på alle kald, fordi handleren tog (request,
// url) men kaldte rateLimitIp(request, env, …) — `env` fandtes ikke i det
// scope. Ruten var altså ubrugelig, og ingen test rørte den, så porten var grøn
// på et værktøj der ikke virkede. Fire ting dømmes her, i rækkefølge:
//   1. den svarer overhovedet,
//   2. den gør det stadig efter at kravet er skrevet op (mutation),
//   3. den afviser private mål — også de IPv4-mappede IPv6-skriftformer,
//   4. den afviser et redirect-HOP ind i en privat vært, som et kun-mål-værn
//      ikke kan se, fordi runtime'en følger kæden for os.
let inspectRes = await call('/api/url-inspect?url=' + encodeURIComponent('https://inspect.example/'), ip(6));
ok('url-inspect svarer på et offentligt mål (ikke 500/1101)', inspectRes.status === 200, inspectRes.status);
const inspectBody = await inspectRes.json().catch(() => ({}));
ok('url-inspect fortæller hvor den endte, og at der ingen omdirigering var',
  inspectBody.finalUrl === 'https://inspect.example/' && inspectBody.totalRedirects === 0 && inspectBody.finalStatus === 200,
  JSON.stringify(inspectBody).slice(0, 140));
ok('url-inspect læser security-headere, som er hele pointen',
  /max-age/.test(JSON.stringify(inspectBody.securityHeaders || {})), JSON.stringify(inspectBody.securityHeaders));

// Beviset på at kravet kan fange den gamle kode: kør den fra git, hvor `env`
// ikke var med, gennem den samme port. Uden den ville første kontrol være
// grøn af den grund at den ikke kan fejle.
// Målt 30/9 af review: et hardkodet `git show` på modul-niveau dræbte hele
// filen i en shallow clone, en tarball-eksport eller en omskrevet historie —
// også de 260 betalings- og licenstests, der intet har med mutationen at gøre.
// Derfor er git *valgfrit*: mangler den, springes mutationen over med en
// tydelig note, og alle øvrige kontroller kører stadig.
let oldWorker = null, oldSrcNote = '';
try {
  const oldWorkerSrc = execFileSync('git', ['show', '241b14e:site/_worker.js'], { cwd: root, encoding: 'utf8', maxBuffer: 64 * 1024 * 1024, stdio: ['ignore', 'pipe', 'ignore'] });
  const oldTmp = join(tmpdir(), `worker-old-${process.pid}.mjs`);
  writeFileSync(oldTmp, oldWorkerSrc);
  oldWorker = (await import(pathToFileURL(oldTmp).href)).default;
} catch (e) {
  oldSrcNote = 'git-historikken er ikke tilgængelig her: ' + (e.code || e.message);
}
// Den gamle kode kaster ikke et svar, den kaster: lokalt en ReferenceError,
// i Cloudflares runtime det samme som den 500/1101 vi målte live. Derfor
// fanges den her — ellers ville mutationen dræbe hele porten i stedet for at
// gøre én kontrol rød, og så ville den ikke lære os noget.
if (oldWorker) {
  let oldStatus = 0, oldThrew = null;
  try {
    const oldRes = await oldWorker.fetch(new Request('https://mahope.tools/api/url-inspect?url=' + encodeURIComponent('https://inspect.example/')), env, {});
    oldStatus = oldRes.status;
  } catch (e) {
    oldThrew = e;
  }
  ok('mutation: den gamle kode fejler på url-inspect, så porten dømmer rigtigt',
    oldThrew !== null || oldStatus === 500, 'threw=' + (oldThrew && oldThrew.message) + ' status=' + oldStatus);
  // Og at den *kun* fejler dér: mutationen skal ramme præcis den linje.
  const oldOk = await oldWorker.fetch(new Request('https://mahope.tools/api/license/validate', {
    method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ license_key: 'ZZZ' }) }), env, {});
  ok('mutation: den gamle kode fejler kun på url-inspect, licensvejen er urørt',
    oldOk.status === 400, oldOk.status);
} else {
  console.log('NOTE: mutationen mod den gamle kode er sprunget over — ' + oldSrcNote);
}

// Private mål på de to åbne ruter. Den mappede IPv6-form er den interessante:
// URL-parseren normaliserer ::ffff:127.0.0.1 til ::ffff:7f00:1, så den ligner
// hverken en punktummer-IPv4 (dotted-quad-grenen) eller en fc/fd-adresse —
// den smuttede lige igennem begge.
const MAPPED = [
  ['http://[::ffff:127.0.0.1]/', 'IPv4-mapped IPv6 loopback'],
  ['http://[::ffff:10.0.0.5]/', 'IPv4-mapped IPv6 RFC1918'],
  ['http://[::ffff:169.254.169.254]/', 'IPv4-mapped IPv6 cloud metadata'],
  ['http://[64:ff9b::7f00:1]/', 'NAT64'],
];
for (const [target, why] of MAPPED) {
  r = await call('/api/url-inspect?url=' + encodeURIComponent(target), ip(6));
  const body = await r.json().catch(() => ({}));
  ok(`url-inspect afviser ${why}`, r.status === 400 && /cannot be inspected/i.test(body.error || ''), `${target} -> ${r.status} ${JSON.stringify(body).slice(0, 90)}`);
  r = await call('/api/header-check?url=' + encodeURIComponent(target), ip(6));
  const hbody = await r.json().catch(() => ({}));
  ok(`header-check afviser ${why}`, r.status === 400 && /cannot be checked/i.test(hbody.error || ''), `${target} -> ${r.status} ${JSON.stringify(hbody).slice(0, 90)}`);
}
// De almindelige private ruter skal også holdes på de to nye ruter — samme
// værn som på /scan-proxy, ellers svarer fire ruter forskelligt på samme URL.
for (const [target, why] of PRIVATE_TARGETS) {
  r = await call('/api/url-inspect?url=' + encodeURIComponent(target), ip(6));
  ok(`url-inspect afviser ${why} på samme måde som scanneren`, r.status === 400 && /cannot be inspected/i.test((await r.json().catch(() => ({}))).error || ''), `${target} -> ${r.status}`);
}

// Hop-værnet. Et offentligt mål der 302er ind i en privat vært er den samme
// SSRF med ét ekstra led, og den gamle kode fulgte kæden lige til 169.254.
const privBefore = privFetches;
r = await call('/api/url-inspect?url=' + encodeURIComponent('https://inspect.example/hop-privat'), ip(6));
const hopBody = await r.json().catch(() => ({}));
ok('url-inspect afviser et redirect ind i en privat vært',
  r.status === 400 && /cannot be inspected/i.test(hopBody.error || ''), r.status + ' ' + JSON.stringify(hopBody).slice(0, 120));
r = await call('/api/header-check?url=' + encodeURIComponent('https://headers.example/hop-privat'), ip(6));
ok('header-check afviser et redirect ind i en privat vært',
  r.status === 400 && /private network/i.test((await r.json().catch(() => ({}))).error || ''), r.status);
ok('ingen af hop-hængene blev hentet', privFetches === privBefore, `${privFetches - privBefore} ude-fetch`);

// En offentlig redirect skal stadig virke — ellers er porten grøn fordi den
// afviser alt, hvilket er den anden fejlretning.
r = await call('/api/url-inspect?url=' + encodeURIComponent('https://inspect.example/hop-ok'), ip(6));
const hopOk = await r.json().catch(() => ({}));
ok('url-inspect følger en offentlig redirect og tæller den',
  r.status === 200 && hopOk.totalRedirects === 1 && hopOk.finalUrl === 'https://inspect.example/final', r.status + ' ' + JSON.stringify(hopOk).slice(0, 120));
r = await call('/api/header-check?url=' + encodeURIComponent('https://headers.example/hop-ok'), ip(6));
const hOk = await r.json().catch(() => ({}));
ok('header-check følger en offentlig redirect og melder den',
  r.status === 200 && hOk.redirected === true && hOk.finalUrl === 'https://headers.example/final', r.status + ' ' + JSON.stringify(hOk).slice(0, 120));

// Timegrænsen skal stadig virke på den nye rute — den var den linje der faldt.
for (let i = 0; i < 80; i++) await call('/api/url-inspect?url=' + encodeURIComponent('https://inspect.example/'), ip(7));
r = await call('/api/url-inspect?url=' + encodeURIComponent('https://inspect.example/'), ip(7));
ok('url-inspect over grænsen giver 429 med timegrænsen', r.status === 429 && /hour/i.test((await r.json().catch(() => ({}))).error || ''), r.status);
r = await call('/api/url-inspect?url=' + encodeURIComponent('https://inspect.example/'), ip(8));
ok('en låst url-inspect låser ikke header-check', r.status === 200, r.status);

// ── Målingen fandt to ruter til, som ingen port dømte ─────────────────
// Review 30/9 fandt at guard-arbejdet kun dækkede de to ruter, CEO-køet havde
// nævnt. Målt på koden: `/api/profile` henter en kaldersstyret URL og
// *returnerer tekst fra den* (titel, beskrivelse, overskrifter, hreflang) — en
// fuld læseprimitiv mod private adresser, gratis og uden licens. Og
// `/scan-proxy` + `/api/compliance-scan` fulgte redirects, så et offentligt
// mål der 302er ind i 169.254.169.254 slap lige forbi et mål-værn.
// Samme private rækker, samme forventning: fire ruter skal være enige.
for (const [target, why] of PRIVATE_TARGETS) {
  r = await call('/api/profile?url=' + encodeURIComponent(target), ip(9));
  const pbody = await r.json().catch(() => ({}));
  ok(`profile afviser ${why}`, r.status === 400 && /cannot be profiled/i.test(pbody.error || ''), `${target} -> ${r.status} ${JSON.stringify(pbody).slice(0, 90)}`);
  r = await call('/api/compliance-scan?url=' + encodeURIComponent(target), ip(9));
  const sbody = await r.json().catch(() => ({}));
  ok(`compliance-scan afviser ${why}`, r.status >= 400 && /cannot be scanned/i.test(sbody.error || ''), `${target} -> ${r.status} ${JSON.stringify(sbody).slice(0, 90)}`);
}
for (const [target, why] of MAPPED) {
  r = await call('/api/profile?url=' + encodeURIComponent(target), ip(9));
  ok(`profile afviser ${why}`, r.status === 400 && /cannot be profiled/i.test((await r.json().catch(() => ({}))).error || ''), `${target} -> ${r.status}`);
}
// Hop-værnet på de to der fulgte redirects førhen. Uden dette er mål-værnet
// kosmetik: 302'en sker inde i runtime'en, som porten aldrig ser.
if (privFetches === privBefore) {
  r = await call('/scan-proxy?url=' + encodeURIComponent('https://scan.example/'), ip(4));
  ok('scan-proxy på en offentlig side virker stadig', r.status === 200, r.status);
}
// Hop-værnet på /api/profile måles adfærd, ikke navn. Review 29/9 fandt at
// ruten stadig fulgte kæden med redirect:'follow', så et offentligt mål der
// 302er ind i 127.0.0.1 blev hentet alligevel — og analyzeHtml() lagde title og
// description fra den side i JSON-svaret. Den gamle port greb kun *navnet*
// `targetIsPublic` i de første 3000 tegn af funktionen, så den var grøn både
// før og efter rettelsen. Derfor tælles de ude-fetch her, som for de andre
// ruter, og det navnegreb er væk: målværnet er allerede dømt adfærdsmæssigt af
// PRIVATE_TARGETS-løkken ovenfor.
const profBefore = privFetches;
r = await call('/api/profile?url=' + encodeURIComponent('https://headers.example/hop-privat'), ip(9));
const profBody = await r.json().catch(() => ({}));
ok('profile afviser et redirect ind i en privat vært',
  r.status === 400 && /private network/i.test(profBody.error || ''), `${r.status} ${JSON.stringify(profBody).slice(0, 120)}`);
ok('profile hentede ingen af hop-hængene', privFetches === profBefore, `${privFetches - profBefore} ude-fetch`);
// En offentlig redirect skal stadig virke, ellers er porten grøn fordi den
// afviser alt — den anden fejlretning, som lå bag de tre andre hop-tests.
r = await call('/api/profile?url=' + encodeURIComponent('https://headers.example/hop-ok'), ip(9));
const profOk = await r.json().catch(() => ({}));
ok('profile følger en offentlig redirect og melder den',
  r.status === 200 && profOk.final_url === 'https://headers.example/final', `${r.status} ${JSON.stringify(profOk).slice(0, 120)}`);

// Ingen rute må overlade kæden til runtime'en: så ser måleværnet kun første
// hop, og et offentligt mål der 302er ind i 169.254.169.254 er igen præcis det
// samme som at skrive den private adresse direkte. Heltalsmålet, fordi det er
// den egenskab der gælder for hele filen — ikke for én funktion ved navn.
// Kommentarlinjer tælles ikke med: `_worker.js` forklarer netop denne fejlform
// to steder, og en port der rødmer på sin egen forklaring er død.
const liveFollows = readFileSync(join(root, 'site/_worker.js'), 'utf8')
  .split('\n')
  .filter(l => !/^\s*(\/\/|\*|\/\*)/.test(l))
  .filter(l => /redirect:\s*['"`]follow['"`]/.test(l));
ok('ingen rute overlader redirect-kæden til runtime\'en', liveFollows.length === 0,
  `${liveFollows.length} kald: ${(liveFollows[0] || '').trim()}`);

// ── Nøglen må ikke få skylden for noget der ikke er nøglen ───────────
// Nøglen er bekræftet aktiv, før /api/report kaldes, så ingen gren efter det
// kald kan afvise den. Den gamle 4xx-gren sagde "the report server refused
// the key" og nåede et 400 for en privat værtsadresse: en kunde der betalte
// $79 fik at vide at hans egen nøgle var afvist, fordi han havde tastet en
// adresse i sit eget netværk.
const reportClient = reportHtml.slice(reportHtml.indexOf("fetch('/api/report'"));
ok('siden har en egen 429-gren', /r\.status === 429/.test(reportClient));
ok('siden siger aldrig at nøglen blev afvist', !/refused the key/.test(reportClient), 'refused the key');
ok('siden siger at nøglen er gyldig og hvad der stoppede', /your key is valid/.test(reportClient) && /could not be produced/.test(reportClient));
ok('timegrænsen nåer aldrig nøgle-teksten', reportClient.indexOf('r.status === 429') < reportClient.indexOf('your key is valid'));
ok('siden siger timegrænsen og åbner PDF\'en alligevel', /hourly report limit/.test(reportHtml) && /resets within the hour/.test(reportHtml));

// Adfærd, ikke læsning: blokken køres med de svar den kan få. Den er
// ekstraheret fra den indlejrede kode, ikke kopieret, så en ændring i siden
// ændrer denne test. Den løber fra den note der sættes ved svaret til den
// statuslinje kunden faktisk ser — altså hele den tekst, påstanden handler om.
const flowSrc = reportHtml.slice(reportHtml.indexOf('let note =', reportHtml.indexOf("fetch('/api/report'") - 400),
  reportHtml.indexOf('window.setTimeout(() => window.print()'));
const runFlow = async (svar) => {
  const statusNode = { className: '', textContent: '' };
  const doc = { getElementById: () => statusNode };
  const win = { print() {}, setTimeout() {} };
  const f = new Function('fetch', 'getDeviceId', 'renderReport', 'mergeProFindings', 'document', 'window', 'key', 'result',
    `return (async () => { ${flowSrc} return { text: document.getElementById('licenseStatus').textContent }; })()`);
  await f(async () => svar, () => 'dev', () => {}, () => {}, doc, win, euKey, { cached: false });
  return { text: statusNode.textContent };
};
const verdicts = {};
for (const [navn, svar] of [
  ['private-host', new Response(JSON.stringify({ ok: false, error: 'That host cannot be scanned.' }), { status: 400 })],
  ['ugyldig-url', new Response(JSON.stringify({ ok: false, error: 'Invalid URL.' }), { status: 400 })],
  ['timegraense', new Response(JSON.stringify({ ok: false, error: 'Too many reports this hour. Try again later.' }), { status: 429 })],
  ['server-nede', new Response('nope', { status: 503 })],
  ['fuld-rapport', new Response(JSON.stringify({ ok: true, findings: [] }), { status: 200 })],
]) verdicts[navn] = await runFlow(svar);
ok('ingen af fejlene skyldes nøglen', ['private-host', 'ugyldig-url', 'timegraense', 'server-nede']
  .every((k) => !/refus|invalid license|license (not valid|expired|revoked)/i.test(verdicts[k].text)), JSON.stringify(verdicts));
ok('kunden får at vide nøglen stadig er gyldig', /your key is valid/.test(verdicts['private-host'].text), verdicts['private-host'].text);
ok('kunden får at vide hvad der stoppede', /cannot be scanned/.test(verdicts['private-host'].text), verdicts['private-host'].text);
ok('en fuld rapport siger den er fuld', /License valid/.test(verdicts['fuld-rapport'].text) && !/only/.test(verdicts['fuld-rapport'].text), verdicts['fuld-rapport'].text);
ok('alle fem ender med at PDF\'en åbner', Object.values(verdicts).every((v) => /your PDF opens now/.test(v.text)), JSON.stringify(verdicts, null, 0));

// 26) GET /api/paid-files — betalingslinket for et downloadprodukt udleveres
// KUN når filerne ligger i KV. Det er hele pointen: `check_stripe_ctas.py`
// (regel 5) forbyder linket i `site/`, når `kv_verified` er false, fordi
// køberen ellers betaler for en download der svarer 503 i /api/download.
// Uden denne port har siden ingen kilde til sit købslink, og med en port der
// bare lister nøglerne ville den sælge alle svyv fra dag ét.
r = await call('/api/paid-files');
ok('paid-files svarer 200', r.status === 200, r.status);
// Tidligere arme har lagt `paidfile:`-nøgler i den delte fake-KV, så målingen
// skal starte fra en kendt tilstand — ellers ville "tom KV" være en løgneste.
for (const key of [...kv.keys()]) if (key.startsWith('paidfile:')) kv.delete(key);
const pfBody = await (await call('/api/paid-files')).json();
ok('paid-files svarer ok og kv_ok', pfBody.ok === true && pfBody.kv_ok === true, JSON.stringify(pfBody).slice(0, 120));
ok('alle svyv downloadprodukter er med', pfBody.products.length === 7, pfBody.products.length);
ok('intet produkt er leverbart i en tom KV', pfBody.products.every((p) => p.available === false), JSON.stringify(pfBody.products.map((p) => p.ready)));
ok('intet betalingslink udleveres når filerne mangler',
  pfBody.products.every((p) => p.payment_link === undefined), JSON.stringify(pfBody.products[0]));

// Læg alle filer fra ét produkt ind — kun dét, så "delvis leveret" er en
// tilstand der faktisk opstår, og ikke en opfundet. Filnavnene står hardkodet
// her med vilje: de er de nøgler `withPaidFiles` og `handlePaidDownload`
// læser, så en stavetype i workeren skal kunne fange sig her.
const dpa = ['dpa-template.pdf', 'dpa-template.md'];
r = await call('/api/paid-files');
let pf = await r.json();
ok('et produkt uden filer i KV er ikke leverbart', pf.products.find((p) => p.product === 'eucomply-dpa').ready === 0);
for (const f of dpa.slice(0, 1)) kv.set(`paidfile:${f}`, 'x');
pf = await (await call('/api/paid-files')).json();
const dpaDelvis = pf.products.find((p) => p.product === 'eucomply-dpa');
ok('en halvt uploadet filsamling er ikke leverbar', dpaDelvis.ready === 1 && dpaDelvis.available === false, JSON.stringify(dpaDelvis));
ok('en delvis levering får heller intet link', dpaDelvis.payment_link === undefined);
for (const f of dpa.slice(1)) kv.set(`paidfile:${f}`, 'x');
pf = await (await call('/api/paid-files')).json();
const dpaFuld = pf.products.find((p) => p.product === 'eucomply-dpa');
ok('alle filer i KV = leverbart', dpaFuld.available === true && dpaFuld.ready === dpaFuld.files, JSON.stringify(dpaFuld));
ok('betalingslinket kommer først når produktet kan leveres', dpaFuld.payment_link === 'https://buy.stripe.com/bJe7sK8aT4My7dk7czbMQ05', dpaFuld.payment_link);
ok('de øvrige produkter er stadig lukket, selv om ét er åbent',
  pf.products.filter((p) => p.available).length === 1, pf.products.filter((p) => p.available).map((p) => p.product).join(','));

// Mutation-kontrol: kun filerne for *dette* produkt må tænde det. Uden denne
// arm ville porten være grøn, hvis `available` bare hang på "der er nogen fil".
kv.delete('paidfile:dpa-template.pdf');
kv.delete('paidfile:dpa-template.md');
pf = await (await call('/api/paid-files')).json();
ok('sletning i KV lukker knappen igen', pf.products.every((p) => !p.available) && pf.products.every((p) => p.payment_link === undefined));

// `?product=` må ikke kunne bruges til at få et link for et produkt der ikke
// kan leveres — det er samme regel, bare med et andre kald.
for (const f of dpa) kv.set(`paidfile:${f}`, 'x');
pf = await (await call('/api/paid-files?product=eucomply-dpa')).json();
ok('?product= svarer 200 med netop det produkt', pf.products.length === 1 && pf.products[0].product === 'eucomply-dpa', JSON.stringify(pf.products));
ok('?product= kan ikke fremme et andet produkt', pf.products[0].payment_link === 'https://buy.stripe.com/bJe7sK8aT4My7dk7czbMQ05');
kv.delete('paidfile:dpa-template.pdf');
kv.delete('paidfile:dpa-template.md');

// KV nede må ikke læse som "filer mangler" — ellers slår en fejl fra salget.
const envNede = { ...env, VISITS: { ...VISITS, list: async () => { throw new Error('kv nede'); } } };
r = await callWith('/api/paid-files', {}, envNede);
const nede = await r.json();
ok('KV-fejl svarer stadig 200 med kv_ok false', r.status === 200 && nede.kv_ok === false, r.status + ' ' + JSON.stringify(nede).slice(0, 80));
ok('KV-fejl giver ingen betalingslink', nede.products.every((p) => p.payment_link === undefined));
ok('KV-fejl påstår ikke at filerne mangler', nede.products.every((p) => p.missing === null), JSON.stringify(nede.products[0]));

// ── AI-kvoten må ikke tælle vores egne 502'ere ───────────────────────
// /api/compliance-ai tager en daglig kvote (20 spørgsmål) FØR den kalder
// OpenRouter, og klienten genkalder én gang ved 502. Målt 30/9: kravet var, at
// et genkald på vores egen fejl ikke må tælle brugerens kvote op, og højst må
// give ét ekstra betalt kald. Uden refusion brændte ét dårligt minut tre af de
// tyve daglige spørgsmål, og siden sagde så "daily limit reached" til en
// bruger, der aldrig havde fået et svar.
const aiEnv = { ...env, OPENROUTER_API_KEY: 'sk-or-test' };
const aiBody = { question: 'Does the EAA apply to my website?' };
let aiStatus = 200;
const realFetch = globalThis.fetch;
globalThis.fetch = async (u, o) => {
  if (String(u).startsWith('https://openrouter.ai/')) {
    return aiStatus === 200
      ? new Response(JSON.stringify({ choices: [{ message: { content: 'Ja, det gælder.' } }] }), { status: 200 })
      : new Response('upstream down', { status: aiStatus });
  }
  return realFetch(u, o);
};
const aiPost = (init) => worker.fetch(new Request('https://mahope.tools/api/compliance-ai', {
  method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(aiBody), ...init }), aiEnv, {});
const aiCount = async () => {
  let n = 0;
  for (const k of kv.keys()) if (k.startsWith('airl:') && !k.includes('hit')) n = Math.max(n, parseInt(kv.get(k), 10) || 0);
  return n;
};
r = await aiPost();
ok('AI: et godt spørgsmål svarer og tæller én kvote', r.status === 200 && (await r.json()).ok === true, r.status);
ok('AI: den tæller præcis én', await aiCount() === 1, 'kvote=' + await aiCount());
aiStatus = 502;
const before502 = await aiCount();
r = await aiPost();
ok('AI: en 502 fra OpenRouter er en 502 for klienten', r.status === 502, r.status);
ok('AI: vores egen 502 tæller ikke brugerens kvote op', await aiCount() === before502, `${before502} -> ${await aiCount()}`);
aiStatus = 200;
r = await aiPost();
ok('AI: efter en 502 kan brugeren stadig spørge (dvs. kvote ikke tabt)', r.status === 200, r.status);
ok('AI: den tæller så ét mere, som forventet', await aiCount() === before502 + 1, 'kvote=' + await aiCount());
// Kvoten skal stadig være ægte: den må ikke være slået helt fra, fordi vi
// refunderer. 20 på række skal give den 429, der fortægger brugeren hvornår
// den nulstilles — ellers ville refusionen have gjort assistenten ufri.
let lastAi = null;
for (let i = 0; i < 25; i++) lastAi = await aiPost();
const limitBody = await lastAi.json().catch(() => ({}));
ok('AI: kvoten består stadig, og siger hvornår den nulstilles',
  lastAi.status === 429 && /resets at midnight UTC/i.test(limitBody.error || ''), lastAi.status + ' ' + JSON.stringify(limitBody).slice(0, 120));
globalThis.fetch = realFetch;

// Licens- og leveringsvejen er urørt af alt dette — bevist med en rigtig
// download: token i KV, fil i KV, og så skal `/api/download` levere den.
ok('/api/stripe-webhook findes stadig', (await call('/api/stripe-webhook', { method: 'POST' })).status !== 404);
kv.set('dl:' + 'a'.repeat(32), JSON.stringify({ files: ['dpa-template.pdf'], expires_at: '2999-01-01T00:00:00.000Z' }));
kv.set('paidfile:dpa-template.pdf', 'PDF');
const dl = await call('/api/download/' + 'a'.repeat(32) + '/dpa-template.pdf');
ok('/api/download/ leverer stadig filen', dl.status === 200 && await dl.text() === 'PDF', dl.status);
ok('/api/download/ sætter stadig attachment', (dl.headers.get('content-disposition') || '').includes('dpa-template.pdf'), dl.headers.get('content-disposition'));

// ── Workeren melder sine egne uventede fejl til Sentry ───────────────
// 1/10-prompten siger «Ingen uløste fejl de seneste 14 dage» og spørger så om
// SDK'en overhovedet er sat op. Den var ikke: nul forekomster af "sentry" i
// hele repoet. Det er ikke en kosmetisk mangel — `/api/url-inspect` lå på
// 500/1101 på hvert kald 30/9, og `/api/compliance-ai` har svaret 503
// «AI service not configured» i dagevis, fordi ingen overvågning så det.
//
// Scenariet her er det realistiske: Pages-bindingen er død, så *alle*
// statiske sider fejler. Før blev det Cloudflares rå 1101. Nu skal det være en
// ren 500 *og* en rapport — og rapporten må ikke indeholde persondata,
// `/api/license/lookup` tager `{ order_id, email }` i kroppen.
//
// En del af hver test her er beviset på at den kan fejle: mutationen til sidst
// lægger den gamle kode ind (rapporten fjernet) og forventer nul rapporter.
const SENTRY_HOST = 'o1087332.ingest.us.sentry.io';
let sentryEnvelopes = [];
const outerFetch = globalThis.fetch;
globalThis.fetch = async (input, init) => {
  const u = typeof input === 'string' ? input : input && input.url;
  if (typeof u === 'string' && u.includes(SENTRY_HOST)) {
    sentryEnvelopes.push({ url: u, headers: (init && init.headers) || {}, body: String((init && init.body) || '') });
    return new Response('', { status: 200 });
  }
  return outerFetch(input, init);
};
// Død binding: 404-fallbacken kaster, og det er præcis den fejl der tager
// alle fire domæner ned. Den første ASSETS-kald er pakket i en catch, så det
// er den anden der løber ud — dvs. fejlen kommer uden om rutedispatcheren,
// som er præcis den egenskab guarden skal fange.
// `deadTag' giver hvert scenario sin egen fejltekst. Det er ikke pynt: alle
// statiske 404'er falder igennem på `/404.html`, så uden tag ville hver test
// have samme nøgle i tælleren, den første ville æde hele budgetten, og
// løkketesten ville måle 0 rapporter og se ud til at virke.
let deadTag = 'findes-ikke';
const deadEnv = { ...env, ASSETS: { fetch: async () => { throw new Error('binding nede: ' + deadTag); } } };
const deadCall = (path, init) => worker.fetch(new Request('https://mahope.tools' + path, init), deadEnv, {});
const lastEnvelope = () => sentryEnvelopes[sentryEnvelopes.length - 1] || { url: '', headers: {}, body: '' };

// 1. En uventet fejl giver en ren 500 og en rapport.
sentryEnvelopes = [];
const deadRes = await deadCall('/findes-ikke?license_key=SECRETLIGNOEGLE', {
  headers: { authorization: 'Bearer HEMLIGHED', cookie: 'session=SMUL' },
});
const deadEnv0 = lastEnvelope();
ok('uventet fejl giver en ren 500 i stedet for Cloudflares 1101', deadRes.status === 500, deadRes.status);
ok('uventet fejl meldes til Sentry', sentryEnvelopes.length === 1, 'enveloper=' + sentryEnvelopes.length);
ok('rapporten går til det rigtige projekt med den offentlige nøgle',
  deadEnv0.url === 'https://o1087332.ingest.us.sentry.io/api/4512180032045056/envelope/' &&
  /sentry_key=14c098aa6fcbb129d9fa4467f7e2dad6/.test(String(deadEnv0.headers['x-sentry-auth'] || '')),
  deadEnv0.url + ' | ' + String(deadEnv0.headers['x-sentry-auth'] || ''));
ok('rapporten er en envelope med en fejl, ikke en tekststreng',
  deadEnv0.body.startsWith('{') && /"exception"/.test(deadEnv0.body) &&
  /binding nede:/.test(deadEnv0.body), deadEnv0.body.slice(0, 120));
ok('rapporten ved hvilken rute der fejlede', /"route":"\/findes-ikke"/.test(deadEnv0.body), deadEnv0.body.slice(0, 300));

// 2. Ingen persondata. Det er den regel der gør det trygt at sende en fejl
//    der stammer fra en rute med licensnøgler og ordrer i kroppen.
const dBody = deadEnv0.body;
ok('rapporten indeholder ingen authorization-header',
  !/HEMLIGHED/.test(dBody) && !/"authorization"/i.test(dBody), 'lækket header');
ok('rapporten indeholder ingen cookie', !/SMUL/.test(dBody) && !/"cookie"/i.test(dBody), 'lækket cookie');
ok('rapporten indeholder ikke query-strengen', !/SECRETLIGNOEGLE/.test(dBody) && !/\?license_key/.test(dBody), 'lækket query');
ok('rapporten sender hverken krop eller user-agent',
  !/"body"/i.test(dBody) && !/"headers"/i.test(dBody) && !/python-requests|User-Agent/i.test(dBody), 'lækket krop/UA');

// 3. Håndterede tilstande er ikke fejl. En 404 på en ukendt licensnøgle og en
//    429 fra kvoten er det, brugeren skal se en sætning om — de er ikke
//    exceptions, og de må ikke fylde Sentry.
sentryEnvelopes = [];
await call('/api/license/lookup', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ order_id: 'cs_live_intet', email: 'a@b.dk' }) });
await call('/api/ukendt-rute');
ok('håndterede fejl (404/ukendt nøgle) melder ikke til Sentry', sentryEnvelopes.length === 0, 'enveloper=' + sentryEnvelopes.length);

// 4. Kun i produktion. En lokal kørsel må ikke fylde projektet med rapporter.
//    Egen `deadTag' igen: ellers springer rapporten over på tælleren fra
//    test 1, og kontrollen er grøn uden at localhost-værnet har været i spil —
//    altså grøn af den grund at den ikke kan fejle.
sentryEnvelopes = [];
deadTag = 'lokal-korsel';
const localRes = await worker.fetch(new Request('https://localhost/findes-ikke'), deadEnv, {});
ok('localhost sender ikke rapporter', sentryEnvelopes.length === 0 && localRes.status === 500,
  'enveloper=' + sentryEnvelopes.length + ' status=' + localRes.status);
// Beviset på at værnet er det der holder: samme fejl på et rigtigt domæne
// sender netop én rapport (delt ovenfor), så forskellen er værnet og ikke
// en død kodevej. Derfor testes domænet lige her igen med en ny nøgle.
sentryEnvelopes = [];
deadTag = 'rigtigt-domaene';
await deadCall('/findes-ikke-paa-domaene');
ok('samme fejl på et rigtigt domæne sender derimod en rapport',
  sentryEnvelopes.length === 1, 'enveloper=' + sentryEnvelopes.length);

// 5. En fejl i en løkke må ikke brænde kvoten væk. Den samme kvota betalende
//    kunder bruger til /api/license/validate, så en ubegrænset rapport er
//    en reel risiko, ikke en bagatel.
sentryEnvelopes = [];
deadTag = 'loekke';
for (let i = 0; i < 12; i++) await deadCall('/loekke');
ok('en fejl i en løkke sendes højst SENTRY_MAX_PER_MINUTE gange',
  sentryEnvelopes.length > 0 && sentryEnvelopes.length <= 5, 'enveloper=' + sentryEnvelopes.length);
ok('tælleren lader den første fejl komme ud, så den ikke er død',
  sentryEnvelopes.length === 1, 'enveloper=' + sentryEnvelopes.length);

// 6. Overvågningen må aldrig tage ruten ned. Hvis Sentry svarer 500 eller
//    afbryder forbindelsen, skal brugeren stadig få sit 500.
sentryEnvelopes = [];
deadTag = 'sentry-er-nede';
globalThis.fetch = async (input, init) => {
  const u = typeof input === 'string' ? input : input && input.url;
  if (typeof u === 'string' && u.includes(SENTRY_HOST)) return Promise.reject(new Error('sentry nede'));
  return outerFetch(input, init);
};
let stillRes = null, stillThrew = null;
try { stillRes = await deadCall('/sentry-er-nede'); } catch (e) { stillThrew = e; }
ok('en nede Sentry giver stadig et svar til brugeren',
  stillThrew === null && stillRes && stillRes.status === 500,
  'threw=' + (stillThrew && stillThrew.message) + ' status=' + (stillRes && stillRes.status));
globalThis.fetch = async (input, init) => {
  const u = typeof input === 'string' ? input : input && input.url;
  if (typeof u === 'string' && u.includes(SENTRY_HOST)) {
    sentryEnvelopes.push({ url: u, headers: (init && init.headers) || {}, body: String((init && init.body) || '') });
    return new Response('', { status: 200 });
  }
  return outerFetch(input, init);
};

// 7. Mutationen: den kode der var her *før* opgaven skal give nul rapporter i
//    samme scenario. Uden denne kontrol er de tolv kontroller ovenfor grønne
//    af den grund at de ikke kan fejle — præcis den fejlform `awk`-kriteriet i
//    opgave 42 var. Sha'en er låst til den commit lige før denne ændring, så
//    mutationen er den virkelige gamle kode og ikke "main plus et hack".
//    Git er valgfrit: mangler historikken, springes mutationen over med en
//    note, og alle øvrige kontroller kører stadig.
const PRE_SENTRY_SHA = '54fcc7e';
let preSentryWorker = null, preNote = '';
try {
  const oldSrcText = execFileSync('git', ['show', `${PRE_SENTRY_SHA}:site/_worker.js`],
    { cwd: root, encoding: 'utf8', maxBuffer: 64 * 1024 * 1024, stdio: ['ignore', 'pipe', 'ignore'] });
  ok('mutationen finder den gamle kode (ellers dommer den intet)', !/SENTRY_DSN_FALLBACK/.test(oldSrcText));
  const oldTmp = join(tmpdir(), `worker-presentry-${process.pid}.mjs`);
  writeFileSync(oldTmp, oldSrcText);
  preSentryWorker = (await import(pathToFileURL(oldTmp).href)).default;
} catch (e) {
  preNote = 'git-historikken er ikke tilgængelig her: ' + (e.code || e.message);
}
if (preSentryWorker) {
  sentryEnvelopes = [];
  deadTag = 'gammel-kode';
  let oldStatus = 0, oldThrew = null;
  try { oldStatus = (await preSentryWorker.fetch(new Request('https://mahope.tools/findes-ikke'), deadEnv, {})).status; } catch (e) { oldThrew = e; }
  ok('mutation: den gamle kode melder ingenting og giver den rå 1101',
    sentryEnvelopes.length === 0 && (oldThrew !== null || oldStatus !== 500),
    'enveloper=' + sentryEnvelopes.length + ' threw=' + (oldThrew && oldThrew.message) + ' status=' + oldStatus);
  // Og at den *kun* fejler dér: mutationen skal ramme præcis fangsten, ikke
  // gøre licensvejen urørt-ligegyldig.
  sentryEnvelopes = [];
  const oldLicense = await preSentryWorker.fetch(new Request('https://mahope.tools/api/license/validate', {
    method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ license_key: 'ZZZ' }) }), env, {});
  ok('mutation: den gamle kode svarer normalt på licensvejen',
    oldLicense.status === 400 && sentryEnvelopes.length === 0, oldLicense.status);
} else {
  console.log('NOTE: mutationen mod den gamle kode er sprunget over — ' + preNote);
}

globalThis.fetch = outerFetch;

console.log(`${pass}/${pass + fail} ok`);
process.exit(fail ? 1 : 0);
