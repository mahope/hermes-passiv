// Ende-til-ende-test af Stripe-levering i site/_worker.js med falsk KV, Stripe og Resend.
import { createHash, createHmac } from 'node:crypto';
import { copyFileSync, readFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
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
    if (request.method !== 'GET' && request.method !== 'HEAD') return new Response('Method not allowed', { status: 405 });
    return new Response('Not found', { status: 404 });
  } } };

const mails = []; let stripeCalls = 0; let resendNede = false;
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
  if (url.startsWith('https://scan.example/')) return new Response('<html lang="en"><head><title>Test</title><script async src="https://www.googletagmanager.com/gtag/js?id=G-1"></script></head><body><form action="http://insecure.example/send"></form><footer><a href="/cookie-policy">Cookie policy</a></footer></body></html>', { status: 200 });
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

r = await call('/api/lemon-webhook', { method: 'GET' });
ok('gammel Lemon-rute: GET = 404', r.status === 404);
r = await call('/api/lemon-webhook', { method: 'POST', body: '{}' });
ok('gammel Lemon-rute: POST = 404', r.status === 404);

// Licens via tak-siden
r = await call('/api/stripe/fulfillment?session_id=cs_live_licenseAAAAAAAAAA');
let j = await r.json();
ok('licens udstedt', r.status === 200 && /^[a-f0-9]{32}$/.test(j.license_key), JSON.stringify(j));
ok('leveringssvar er ikke cross-origin læsbare', !r.headers.get('access-control-allow-origin'));
ok('max 3 enheder', j.max_devices === 3);
ok('én mail', mails.length === 1 && mails[0].to[0] === 'buyer@example.com');
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
// Abonnement: antal × grænse, udløb, fornyelse
r = await call('/api/stripe/fulfillment?session_id=cs_live_subscripBBBBBBBBBB'); j = await r.json();
ok('eucomply 2 sites', j.max_devices === 2 && j.expires_at && j.expires_at.startsWith('2033'), JSON.stringify(j));
const inv = JSON.stringify({ type: 'invoice.paid', data: { object: { subscription: 'sub_1', lines: { data: [{ period: { end: 2100000000 } }] } } } });
r = await call('/api/stripe-webhook', { method: 'POST', body: inv, headers: { 'stripe-signature': sign(inv) } });
const rec = JSON.parse(kv.get('lic:' + j.license_key));
ok('fornyelse forlænger', rec.expires_at.startsWith('2036'), rec.expires_at);
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
const euKey = (await r.json()).license_key;
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

console.log(`${pass}/${pass + fail} ok`);
process.exit(fail ? 1 : 0);
