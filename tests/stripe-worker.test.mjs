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
  ASSETS: { fetch: async () => new Response('asset', { status: 200 }) } };

const mails = []; let stripeCalls = 0;
const sessions = {
  cs_live_licenseAAAAAAAAAA: { status: 'complete', payment_status: 'paid', subscription: null, customer_details: { email: 'Buyer@Example.com' },
    line_items: { data: [{ quantity: 1, price: { lookup_key: 'deskuptime-pro-v1' } }] } },
  cs_live_subscripBBBBBBBBBB: { status: 'complete', payment_status: 'paid', subscription: 'sub_1', customer_details: { email: 'a@b.dk' },
    line_items: { data: [{ quantity: 2, price: { lookup_key: 'eucomply-pro-v1' } }] } },
  cs_live_downloadCCCCCCCCCC: { status: 'complete', payment_status: 'paid', subscription: null, customer_details: { email: 'c@d.dk' },
    line_items: { data: [{ quantity: 1, price: { lookup_key: 'eucomply-dpa-v1' } }] } },
  cs_live_unpaidDDDDDDDDDDDD: { status: 'open', payment_status: 'unpaid', line_items: { data: [] } },
};
globalThis.fetch = async (url, opts = {}) => {
  url = String(url);
  if (url.startsWith('https://api.stripe.com/v1/checkout/sessions/')) {
    stripeCalls++;
    const id = decodeURIComponent(url.split('/sessions/')[1].split('?')[0]);
    return new Response(JSON.stringify(sessions[id] || {}), { status: sessions[id] ? 200 : 404 });
  }
  if (url.startsWith('https://api.stripe.com/v1/subscriptions/')) return new Response(JSON.stringify({ current_period_end: 2000000000 }));
  if (url === 'https://api.resend.com/emails') { mails.push(JSON.parse(opts.body)); return new Response('{}', { status: 200 }); }
  throw new Error('uventet fetch ' + url);
};

let pass = 0, fail = 0;
const ok = (navn, cond, info = '') => { if (cond) pass++; else { fail++; console.log('FEJL:', navn, info); } };
const call = (path, init) => worker.fetch(new Request('https://mahope.tools' + path, init), env, {});
const sign = (body, t = Math.floor(Date.now() / 1000)) => `t=${t},v1=${createHmac('sha256', WHSEC).update(`${t}.${body}`).digest('hex')}`;

// Licens via tak-siden
let r = await call('/api/stripe/fulfillment?session_id=cs_live_licenseAAAAAAAAAA');
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
ok('kendt enhed uden produktfelt ok', r.status === 200);
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
console.log(`${pass}/${pass + fail} ok`);
process.exit(fail ? 1 : 0);
