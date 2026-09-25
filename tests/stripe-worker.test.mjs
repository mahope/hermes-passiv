// Ende-til-ende-test af Stripe-levering i site/_worker.js med falsk KV, Stripe og Resend.
import { createHmac } from 'node:crypto';
import { copyFileSync } from 'node:fs';
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
  put: async (k, v) => { kv.set(k, typeof v === 'string' ? v : v); },
  list: async () => ({ keys: [], list_complete: true }),
};
const WHSEC = 'whsec_test123';
const env = { VISITS, STRIPE_SECRET_KEY: 'sk_test_x', STRIPE_WEBHOOK_SECRET: WHSEC, RESEND_API_KEY: 're_x',
  ASSETS: { fetch: async (request) => {
    const pathname = new URL(request.url).pathname;
    if (pathname === '/downloads/eaa-checklist.epub') return new Response('asset', { status: 200 });
    if (request.method !== 'GET' && request.method !== 'HEAD') return new Response('Method not allowed', { status: 405 });
    return new Response('Not found', { status: 404 });
  } } };

const mails = []; let stripeCalls = 0; let resendNede = false;
const sessions = {
  cs_live_licenseAAAAAAAAAA: { status: 'complete', payment_status: 'paid', subscription: null, customer_details: { email: 'Buyer@Example.com' },
    line_items: { data: [{ quantity: 1, price: { lookup_key: 'deskuptime-pro-v1' } }] } },
  cs_live_subscripBBBBBBBBBB: { status: 'complete', payment_status: 'paid', subscription: 'sub_1', customer_details: { email: 'a@b.dk' },
    line_items: { data: [{ quantity: 2, price: { lookup_key: 'eucomply-pro-v1' } }] } },
  cs_live_downloadCCCCCCCCCC: { status: 'complete', payment_status: 'paid', subscription: null, customer_details: { email: 'c@d.dk' },
    line_items: { data: [{ quantity: 1, price: { lookup_key: 'eucomply-dpa-v1' } }] } },
  cs_live_unpaidDDDDDDDDDDDD: { status: 'open', payment_status: 'unpaid', line_items: { data: [] } },
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
};
globalThis.fetch = async (url, opts = {}) => {
  url = String(url);
  if (url.startsWith('https://api.stripe.com/v1/checkout/sessions/')) {
    stripeCalls++;
    const id = decodeURIComponent(url.split('/sessions/')[1].split('?')[0]);
    return new Response(JSON.stringify(sessions[id] || {}), { status: sessions[id] ? 200 : 404 });
  }
  if (url.startsWith('https://api.stripe.com/v1/subscriptions/')) return new Response(JSON.stringify({ current_period_end: 2000000000 }));
  if (url === 'https://api.resend.com/emails') { if (resendNede) return new Response('{}', { status: 503 }); mails.push({ ...JSON.parse(opts.body), idem: opts.headers['Idempotency-Key'] }); return new Response('{}', { status: 200 }); }
  if (url.startsWith('https://api.stripe.com/v1/invoices/')) return new Response(JSON.stringify({ parent: { subscription_details: { subscription: 'sub_1' } } }));
  if (url.startsWith('https://api.stripe.com/v1/charges/')) return new Response(JSON.stringify({ id: 'ch_d', payment_intent: 'pi_lic', refunded: false }));
  throw new Error('uventet fetch ' + url);
};

let pass = 0, fail = 0;
const ok = (navn, cond, info = '') => { if (cond) pass++; else { fail++; console.log('FEJL:', navn, info); } };
const call = (path, init) => worker.fetch(new Request('https://mahope.tools' + path, init), env, {});
const sign = (body, t = Math.floor(Date.now() / 1000)) => `t=${t},v1=${createHmac('sha256', WHSEC).update(`${t}.${body}`).digest('hex')}`;

let r;
r = await call('/api/lemon-webhook', { method: 'GET' });
ok('gammel Lemon-rute: GET = 404', r.status === 404);
r = await call('/api/lemon-webhook', { method: 'POST', body: '{}' });
ok('gammel Lemon-rute: POST = 404', r.status === 404);

// Licens via tak-siden
r = await call('/api/stripe/fulfillment?session_id=cs_live_licenseAAAAAAAAAA');
let j = await r.json();
ok('licens udstedt', r.status === 200 && /^[a-f0-9]{32}$/.test(j.license_key), JSON.stringify(j));
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
r = await call('/api/stripe/fulfillment?session_id=cs_live_downloadCCCCCCCCCC'); j = await r.json();
ok('downloadlinks', j.downloads && j.downloads.length === 2, JSON.stringify(j));
kv.set('paidfile:dpa-template.pdf', '%PDF-test');
r = await call(new URL(j.downloads[0].url).pathname);
ok('betalt fil serveres', r.status === 200 && r.headers.get('content-disposition').includes('dpa-template.pdf'));
r = await call(new URL(j.downloads[0].url).pathname.replace('dpa-template.pdf', 'nda-clause-set.pdf'));
ok('fil uden for købet afvist', r.status === 404);
r = await call('/api/download/' + 'a'.repeat(32) + '/dpa-template.pdf');
ok('ukendt token afvist', r.status === 404);
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
// 7) Ødelagt procent-kodning i download
r = await call('/api/download/' + 'b'.repeat(32) + '/%E0%A4%A');
ok('ødelagt kodning = 404', r.status === 404);
console.log(`${pass}/${pass + fail} ok`);
process.exit(fail ? 1 : 0);
