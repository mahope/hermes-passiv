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
let inspectFetches = 0; let headerFetches = 0; let tungFetches = 0; let fodeFetches = 0; let andetFetches = 0;
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
  // Et mål der sender sin egen `Content-Type` som markup. `/scan-proxy`
  // skrev den rå header ind i `error`, og den lander i `/scan`s resultatside —
  // så et fjendtligt site kunne skrive sit eget tag ind i mahope.tools' origin
  // uden at gøre noget som helst. Målt i rigtig Chromium før `safeContentType`:
  // `<title>FIRET</title>` i DOM'en.
  if (url.startsWith('https://ondt.example/')) return new Response('{}', { status: 200, headers: { 'content-type': 'application/json<img src=x onerror=alert(1)>' } });
  // To værter til multi-URL-testen af `/api/compliance-scan`. `to.example` er
  // bare et andet site end scan.example, så to linjer er to sites og ikke den
  // samme to gange. `tung.example`/`tung2.example` svarer 200 på forsiden og
  // 404 på alt andet — så hvert af de ni tjek bruger hele sit fetch-budget,
  // hvilket er det eneste tilfælde hvor et delt budget kan måles.
  if (url.startsWith('https://to.example/')) return new Response('<html lang="en"><head><title>To</title></head><body><footer><a href="/privacy">Privacy</a></footer></body></html>', { status: 200, headers: { 'content-type': 'text/html' } });
  // `fode.example` er det tilfælde, der skiller gætten fra linket: en side der
  // *har* privatlivspolitikken og *linker* den i footeren, men på en sti ingen
  // gæt rammer. Gætteren læser kun `/privacy`, `/privacy-policy`, `/privacy/`,
  // `/datenschutz` og `/legal/privacy` — alle 404 her — så den gamle kode svarer
  // «Privacy Policy: Not found» om et site der lige har vist den. Det er den
  // fejl der gør et værktøj ubrugeligt for en bureau-chef, fordi fundet er
  // rigtigt nok til at ligne en brugers fejl.
  if (url.startsWith('https://andet.example/')) { andetFetches++; return new Response('<html><body>Privacy policy — et helt andet website</body></html>', { status: 200, headers: { 'content-type': 'text/html' } }); }
  if (url.startsWith('https://fode.example/')) {
    fodeFetches++;
    const p = new URL(url).pathname;
    if (p === '/da/juridisk/privatlivspolitik') {
      return new Response('<html lang="da"><head><title>Privatlivspolitik</title></head><body><h1>Privatlivspolitik</h1><p>Vi behandler personoplysninger efter GDPR.</p></body></html>', { status: 200, headers: { 'content-type': 'text/html' } });
    }
    if (p === '/betingelser') {
      return new Response('<html lang="da"><head><title>Vilkår og betingelser</title></head><body><h1>Vilkår</h1></body></html>', { status: 200, headers: { 'content-type': 'text/html' } });
    }
    // Alt andet er en 404, også de gættede juridiske stier. Footer-links er
    // relative, så de skal læses mod den side de står på.
    if (p !== '/' && p !== '') return new Response('Ikke fundet', { status: 404 });
    return new Response('<html lang="da"><head><title>Virksomheden</title></head><body><h1>Virksomheden</h1>'
      + '<nav><a href="/">Forside</a><a href="/om-os">Om os</a></nav>'
      + '<footer>'
      // Et privacy-link på et ANDET domæne, og det står FØR sitets egen. Uden
      // værnet ville scanneren hente det, finde «pass» og skrive et fund til en
      // kundes rapport, der handler om en side på et helt andet website — og
      // da ville den efterfølgende dom om «den linkede side» også fejle, fordi
      // fundet ville pege ud af sitet. Derfor står det først.
      + '<a href="https://andet.example/privacy">Privacy policy</a>'
      + '<a href="/da/juridisk/privatlivspolitik">Privatlivspolitik</a>'
      + '<a href="/betingelser">Vilkår og betingelser</a>'
      + '<a href="https://facebook.com/virksomheden">Facebook</a>'
      + '<a href="/privatlivspolitik.pdf">Privatlivspolitik (PDF)</a></footer></body></html>',
      { status: 200, headers: { 'content-type': 'text/html' } });
  }
  if (url.startsWith('https://tung.example/') || url.startsWith('https://tung2.example/')) {
    tungFetches++;
    const p = new URL(url).pathname;
    if (p !== '/' && p !== '') return new Response('Not found', { status: 404 });
    return new Response('<html lang="en"><head><title>Tung</title></head><body><h1>No legal pages here</h1></body></html>', { status: 200, headers: { 'content-type': 'text/html' } });
  }
  // Et site der **har** privatlivspolitikken og **linker** den, på en sti ingen
  // gæt rammer — og hvor alle de gættede stier er 404, så et kald bruger hele
  // sit budget på at lede forgæves. Det er parret der afslører, om kaldets
  // budget er delt retfærdigt: skal to tunge sites stå foran den i samme kald,
  // før den kommer ud som en rapport bygget på forsiden alene.
  if (url.startsWith('https://dela.example/') || url.startsWith('https://dela2.example/')) {
    const p = new URL(url).pathname;
    if (p === '/om/privatlivspolitik') return new Response('<html lang="da"><head><title>Privatlivspolitik</title></head><body><h1>Privatlivspolitik</h1><p>Vi behandler personoplysninger efter GDPR.</p></body></html>', { status: 200, headers: { 'content-type': 'text/html' } });
    if (p !== '/' && p !== '') return new Response('Not found', { status: 404 });
    return new Response('<html lang="da"><head><title>Et site med privatlivspolitik</title></head><body><h1>Virksomheden</h1><footer><a href="/om/privatlivspolitik">Privatlivspolitik</a></footer></body></html>', { status: 200, headers: { 'content-type': 'text/html' } });
  }
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
// ── /api/license/devices: hvilke maskiner sidder på nøglen ──────────
// Findes kun fordi kunden ellers ikke kan frigøre en plads: `device_id` er en
// maskineidentitet klienten selv danner, så ingen kunde kan gætte den, og appen
// har ingen deaktiveringsknap. Uden listeringen er en kunde der rammer 409 kun
// skrive til Mads — den menneskelige indsats missionen forbyder.
r = await call('/api/license/devices', { method: 'POST', body: JSON.stringify({ license_key: key }), headers: { 'content-type': 'application/json' } });
j = await r.json().catch(() => ({}));
ok('listeringen svarer 200', r.status === 200, r.status);
ok('listeringen tæller de bundne maskiner', j.ok === true && j.devices_in_use === 3 && j.devices.length === 3, JSON.stringify(j).slice(0, 200));
ok('listeringen kender maskinerne ved id', (j.devices || []).map(d => d.device_id).sort().join(',') === 'd1,d2,d5', JSON.stringify(j.devices));
ok('listeringen giver en tid at vælge på', Array.isArray(j.devices) && j.devices.every(d => typeof d.first_seen === 'string' && typeof d.last_seen === 'string'), JSON.stringify(j.devices && j.devices[0]));
ok('listeringen siger hvor mange pladser der er', j.max_devices === 3, j.max_devices);
ok('listeringen røber hverken mail eller ord', !/buyer@example|@example|cs_live_/.test(JSON.stringify(j)), JSON.stringify(j).slice(0, 200));
// GET må ikke ændre noget, og en listering skal ikke kunne ligge i en
// link-scanner, så ruten er POST-only.
r = await call('/api/license/devices', { method: 'GET' });
ok('listeringen er POST-only', r.status === 405, r.status);
r = await call('/api/license/devices', { method: 'POST', body: JSON.stringify({ license_key: 'ikke-en-noegle' }), headers: { 'content-type': 'application/json' } });
ok('listeringen afviser et forkert format', r.status === 400, r.status);
r = await call('/api/license/devices', { method: 'POST', body: JSON.stringify({ license_key: 'a'.repeat(32) }), headers: { 'content-type': 'application/json' } });
ok('listeringen afviser en ukendt nøgle', r.status === 404, r.status);
// Et genaktiveringskald på en allerede bunden maskine må **ikke** tælle en ny
// plads. Det er præcis den fejl objektformen kunne indføre: `.includes(device)`
// på `{ id, first_seen }`-poster finder aldrig strengen, så hver genaktivering
// ville optage en af kundens tre maskiner, indtil tredje kald svarede 409 på
// en kunde der bare åbnede appen igen.
r = await act({ license_key: key, device_id: 'd1', product: 'deskuptime-pro' });
j = await r.json();
ok('genaktivering tæller ikke en ny plads', r.status === 200 && j.devices_in_use === 3, JSON.stringify(j));
r = await lic('validate', { license_key: key, device_id: 'd1', product: 'deskuptime-pro' });
ok('genaktiveret maskine validerer stadig', (await r.json()).valid === true);
r = await lic('deactivate', { license_key: key, device_id: 'd1' });
j = await r.json();
ok('frigør præcis den valgte maskine', r.status === 200 && j.deactivated === true && j.devices_in_use === 2, JSON.stringify(j));
ok('deaktivering bevarer de andre maskiners dato',
  JSON.parse(kv.get('lic:' + key)).devices.every(d => d.id !== 'd1' && typeof d.last_seen === 'string'));
// En nøgle der er skrevet **før** objektformen (rene strenge) skal stadig kunne
// frigøres, og listeringen skal give den en dato at vise frem for «onbekendt».
const legacyKey = 'b'.repeat(32);
kv.set('lic:' + legacyKey, JSON.stringify({ product: 'clean-copy-pro', plan: 'pro-yearly', expires_at: null, max_devices: 5, devices: ['gammel-1', 'gammel-2'] }));
r = await call('/api/license/devices', { method: 'POST', body: JSON.stringify({ license_key: legacyKey }), headers: { 'content-type': 'application/json' } });
j = await r.json().catch(() => ({}));
ok('en nøgle fra før objektformen listes', r.status === 200 && j.devices_in_use === 2 && (j.devices || []).every(d => d.first_seen && d.last_seen), JSON.stringify(j).slice(0, 200));
r = await lic('deactivate', { license_key: legacyKey, device_id: 'gammel-2' });
ok('en nøgle fra før objektformen kan frigøres', r.status === 200 && (await r.json()).devices_in_use === 1, r.status);
r = await act({ license_key: legacyKey, device_id: 'gammel-1', product: 'clean-copy-pro' });
ok('en nøgle fra før objektformen kan stadig aktiveres', r.status === 200 && (await r.json()).devices_in_use === 1, r.status);
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

// Fast ur gennem hele timegrænses-afsnittet. `rateLimitIp` i _worker.js tæller
// i hele time-bøtter (`Math.floor(Date.now() / 3600000)`), så en kørsel der
// krydser en timegrænse *midt i* en af sløjferne her nulstiller tælleren, og
// «over grænsen»-svaret udebliver. Målt 2/10 i CI kl. 05:00:00.
// Sløjferne skal måle kvoten, ikke klokken, så hele afsnittet får et ur der
// står stille. Gaten kører desuden hele suiten under et ur der hopper én
// time pr. kald (`quality_gate.py`-step `stripe-worker-ur`), så denne pin kan
// ikke komme ud af fatninges gen. Samme pin får Sentry-afsnittet, hvis egen
// tæller (12 sekunders glidende vindue).
const stopFastUr = (() => {
  const virkeligNow = Date.now;
  const fast = Math.floor(virkeligNow() / 3600000) * 3600000 + 60000;
  Date.now = () => fast;
  return () => { Date.now = virkeligNow; };
})();

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

// Fejlteksten må ikke bære målets markup med videre. `handleScanProxy` lægger
// målets egen `Content-Type` ind i `error`, og klienten skriver den i
// `#result`s `innerHTML` — så uden `safeContentType()` bestemmer det scannede
// site, hvad vores egen side skriver. Målt før rettelsen i rigtig Chromium:
// et mål med `Content-Type: application/json<img src=x onerror=…>` fik
// `<title>FIRET</title>` i DOM'en. To domme: markup er væk, og typen er stadig
// noget læseren kan se (ellers er beskeden tom).
const ondtBody = await (await call('/scan-proxy?url=' + encodeURIComponent('https://ondt.example/'), ip(4))).json();
ok('scan-proxy: målets egen Content-Type leverer intet markup videre',
  !/[<>]/.test(ondtBody.error || ''), JSON.stringify(ondtBody).slice(0, 120));
ok('scan-proxy: typen er stadig navngivet i fejlen',
  /application\/json/.test(ondtBody.error || '') && /not an HTML page/i.test(ondtBody.error || ''),
  JSON.stringify(ondtBody).slice(0, 120));

// Værterne skal heller ikke slippe igennem som ren tekst, f.eks. "127.0.0.1.nip.io".
// Vi lader den ligge som en kendt begrænsning i stedet for at tro at vi dækker
// DNS-rebinding: kun den bogstavelige IP og de fire suffikser afvises.
// Beviset på at porten ikke er grøn af vilje: en URL med en offentlig vært
// men ugyldigt protokol er stadig afvist med dens egen tekst.
r = await call('/scan-proxy?url=' + encodeURIComponent('file:///etc/passwd'), ip(4));
ok('file:// er afvist med protokol-teksten', r.status === 400 && /http/i.test((await r.json().catch(() => ({}))).error || ''), r.status);

// ── En linje der normaliserer til tom streng må ikke forsvinde ─────────
// Målt 5/10 på a4277574, fundet af reviewer: dedup'en i handleScanProxy
// droppede stille enhver linje hvis `cscNormalizeUrl` gav tom streng — præcis
// de tegnsfejl 400'en er skrevet til at fange ('https://', 'http://', '///',
// '//'), fordi de kun er scheme og/eller skråstreger. Gik alle linjer tabt, blev
// `sider` tom, `sider[0].error` kastede en TypeError, og den åbne rute svarede
// 500 med ingen sætning. Med én gyldig linje ved siden af svarede den 200 med
// den ene side og intet om den anden — præcis den stille skuffelse committen
// siger at den forhindrer. Dommen her er på indholdet i fejlen, fordi en 500
// uden krop er det hele fundet.
const TØM_NØGLE = [
  ['https://', 'scheme uden vært'],
  ['http://', 'scheme uden vært'],
  ['///', 'kun skråstreger'],
  ['//', 'to skråstreger'],
  ['https:///', 'scheme og skråstreger'],
];
for (const [tegnfejl, why] of TØM_NØGLE) {
  r = await call('/scan-proxy?url=' + encodeURIComponent(tegnfejl), ip(31));
  const tømBody = await r.json().catch(() => ({}));
  ok(`scan-proxy: ${why} er et 400, ikke en 500`, r.status === 400, `${tegnfejl} -> ${r.status} ${JSON.stringify(tømBody).slice(0, 90)}`);
  ok(`scan-proxy: ${why} giver hele linjen i fejlen`,
    (tømBody.error || '').includes(tegnfejl) && typeof tømBody.error === 'string' && tømBody.error.length > 0,
    JSON.stringify(tømBody).slice(0, 120));
}
// Den anden halvdel af fundet: linjen forsvandt stille, fordi den var *ved
// siden af* en gyldig. Før rettelsen svarede denne 200 med den ene side.
r = await call('/scan-proxy?url=' + encodeURIComponent('https://to.example/\nhttps://'), ip(31));
const sideVedTegnfejl = await r.json().catch(() => ({}));
ok('scan-proxy: en tegnsfejl ved siden af en gyldig side er et 400 med DEN linje',
  r.status === 400 && (sideVedTegnfejl.error || '').includes('https://')
  && !/multi/.test(JSON.stringify(sideVedTegnfejl)),
  `${r.status} ${JSON.stringify(sideVedTegnfejl).slice(0, 140)}`);
// Beviset på at rettelsen ikke har slået dedup'en i stykker: de fem linjer skal
// stadig give én side, ellers er fem sider pr. kald blevet til én pr. gentaget.
r = await call('/scan-proxy?url=' + encodeURIComponent('https://scan.example/\nhttps://SCAN.example/'), ip(31));
const dedupet = await r.json().catch(() => ({}));
ok('scan-proxy: to skrivelser af samme side er stadig én side',
  r.status === 200 && dedupet.ok === true && !('multi' in dedupet), `${r.status} ${JSON.stringify(dedupet).slice(0, 120)}`);
// Og ingen 400 må bære `undefined` eller tom tekst — det var den anden fejlmode.
const tømFejle = TØM_NØGLE.map(([t]) => call('/scan-proxy?url=' + encodeURIComponent(t), ip(31)).then(x => x.json().catch(() => ({}))));
ok('scan-proxy: ingen af fejlene er tom eller "undefined"',
  (await Promise.all(tømFejle)).every(b => typeof b.error === 'string' && b.error.trim() && !/undefined/.test(b.error)),
  JSON.stringify(await Promise.all(tømFejle)).slice(0, 160));

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
// Listen af *opslagte* headere. Uden den kan en klient kun vise hvad der er, og
// de otte navne skal så ligge i hver klient — hvorfra næste ændring i
// `secHeaders` forsvinder stille. Denne kontrol fejler på koden fra før.
const checkedList = inspectBody.securityHeadersChecked;
ok('url-inspect fortæller hvilke headere den ledte efter, ikke kun hvilke den fandt',
  Array.isArray(checkedList) && checkedList.length === 8 &&
  checkedList.includes('strict-transport-security') && checkedList.includes('content-security-policy'),
  JSON.stringify(checkedList));
// Negativ kontrol: listen skal være de otte vi faktisk slår efter, ikke bare otte
// — ellers ville porten være grøn ved at fylde den med vilkårlige navne.
ok('listen er præcis de otte headere der slås efter',
  Array.isArray(checkedList) && checkedList.every((h) => typeof h === 'string' && /^[a-z-]+$/.test(h)) &&
  new Set(checkedList).size === 8 &&
  ['x-content-type-options', 'x-frame-options', 'referrer-policy', 'permissions-policy',
    'x-xss-protection', 'access-control-allow-origin'].every((h) => checkedList.includes(h)),
  JSON.stringify(checkedList));

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
ok('en låst url-inspect låster ikke header-check', r.status === 200, r.status);

// `/api/license/devices` kom 3/10 som den eneste offentlige licensrute uden
// tæller, på samme flade som `/api/license/lookup` der har 10/time pr. IP. Det er
// præcis den rute en browser skal kunne finde, så den skal dømmes på samme måde
// som de andre: under grænsen virker den, over grænsen svarer den 429 med
// timegrænsen i sætningen, en anden IP låses ikke ud af den, og en nede
// tæller-KV låser *ikke* kunden ude.
const devIp = (n) => ({ method: 'POST', body: JSON.stringify({ license_key: key }), headers: { 'content-type': 'application/json', 'cf-connecting-ip': `203.0.113.${n}` } });
const devGet = (n) => call('/api/license/devices', devIp(n));
r = await devGet(20);
ok('listeringen under grænsen svarer stadig 200', r.status === 200, r.status);
for (let i = 1; i < 30; i++) await devGet(20);
const dev429 = await devGet(20);
const devBody = await dev429.json().catch(() => ({}));
ok('listeringen over grænsen giver 429 med timegrænsen',
  dev429.status === 429 && /hour/i.test(devBody.error || ''), dev429.status + ' ' + JSON.stringify(devBody).slice(0, 120));
r = await devGet(21);
ok('en låst listering låser ikke den næste IP', r.status === 200, r.status);
// Ruten må ikke ændre nøglens state, så en kunde der løber tør for kvoten stadig
// kan frigøre en plads bagefter — det er den bevægelse ruten findes for.
r = await lic('deactivate', { license_key: key, device_id: 'd5' });
ok('en kunde med låst listering kan stadig frigøre en plads',
  r.status === 200 && (await r.json()).deactivated === true, r.status);
const rlGet2 = VISITS.get;
VISITS.get = async (k) => { if (String(k).startsWith('rl:license-devices')) throw new Error('rate-KV nede'); return rlGet2(k); };
r = await devGet(22);
ok('en nede tæller-KV låser ikke listeringen ude', r.status === 200, r.status);
VISITS.get = rlGet2;
stopFastUr();

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

// ── Flere URL'er pr. kald: ruten skal svare én rapport pr. URL ────────
// Opgaven i planen: `/compliance-site-check` tog én URL, mens produktsiden
// lovede at Pro «crawls the site» — så det betalte ikke var noget kunden kunne
// se forskel på. Ruten skal derfor tage flere linjer og svare med én rapport
// pr. URL. Fire ting skal dømmes, og alle fire skal kunne fejle:
//
// 1. Formen på **ét** URL er uændret. Ellers brød vi den GitHub Action og
//    alt hvad der har kaldt ruten siden den blev skrevet.
// 2. To URL'er giver to rapporter — ikke den første, og ikke én blandet.
// 3. En gentaget URL tælles én gang, så den ikke spiser budget to gange.
// 4. Fetch-budgettet er **delt** pr. kald, ikke pr. URL. Uden det kan én
//    besøgende få 5 × 12 = 60 ude-kald i ét kald, og det er flere
//    subrequests end en Worker har på det billige niveau.
r = await call('/api/compliance-scan?url=' + encodeURIComponent('scan.example'), ip(22));
const en = await r.json().catch(() => ({}));
ok('compliance-scan med én URL har stadig det gamle svar',
  r.status === 200 && en.ok === true && en.multi === undefined && !Array.isArray(en.reports)
  && typeof en.score === 'number' && en.results && typeof en.results.passed === 'object',
  `${r.status} ${JSON.stringify(en).slice(0, 140)}`);
// Rapporten skal sige hvilken side der blev læst. Før dette kendte svaret
// kun værten, så en kunde der indsendte `scan.example/kontakt` fik en rapport
// der lævede at have undersøgt forsiden — og klienten skrev «the score is the
// homepage» ved siden af den. Dommen er derfor på den konkrete sti.
r = await call('/api/compliance-scan?url=' + encodeURIComponent('scan.example/kontakt'), ip(24));
const dyb = await r.json().catch(() => ({}));
ok('compliance-scan med en dyb sti svarer den sti, der blev læst',
  r.status === 200 && dyb.scanned_url === 'https://scan.example/kontakt',
  `${r.status} scanned_url=${dyb.scanned_url}`);
ok('compliance-scan tæller siderne det læste, ikke kun domænet',
  r.status === 200 && typeof dyb.pages_checked === 'number' && dyb.pages_checked > 1,
  `${r.status} pages_checked=${dyb.pages_checked}`);
ok('compliance-scan på forsiden siger forsiden, ikke en tom sti',
  en.scanned_url === 'https://scan.example/' && en.pages_checked >= 1,
  `scanned_url=${en.scanned_url} pages_checked=${en.pages_checked}`);
r = await call('/api/compliance-scan?url=' + encodeURIComponent('scan.example\nto.example'), ip(22));
const multi = await r.json().catch(() => ({}));
ok('compliance-scan med to linjer svarer én rapport pr. URL',
  r.status === 200 && multi.ok === true && Array.isArray(multi.reports) && multi.reports.length === 2
  && multi.reports[0].url === 'https://scan.example' && multi.reports[1].url === 'https://to.example',  `${r.status} ${JSON.stringify(multi).slice(0, 200)}`);
ok('hver rapport har sin egen score og sine egne fund',
  Array.isArray(multi.reports) && multi.reports.every(x => typeof x.score === 'number' && x.results && Object.keys(x.results).length > 0),
  JSON.stringify((multi.reports || []).map(x => [x.url, x.score])));
r = await call('/api/compliance-scan?url=' + encodeURIComponent('scan.example\nto.example\nscan.example'), ip(22));
const gentaget = await r.json().catch(() => ({}));
ok('en gentaget URL tælles én gang', r.status === 200 && gentaget.reports?.length === 2,
  r.status + ' ' + JSON.stringify(gentaget).slice(0, 160));
r = await call('/api/compliance-scan?url=' + encodeURIComponent('a.example\nb.example\nc.example\nd.example\ne.example\nf.example'), ip(23));
const forMange = await r.json().catch(() => ({}));
ok('flere end fem URL\'er er et 400 med et tal, ikke en stille afskæring',
  r.status === 400 && /5/.test(forMange.error || ''), r.status + ' ' + JSON.stringify(forMange));
r = await call('/api/compliance-scan?url=' + encodeURIComponent('scan.example\n::::'), ip(24));
ok('en ugyldig linje blandt gyldige er et 400 med Invalid URL',
  r.status === 400 && /invalid url/i.test((await r.json().catch(() => ({}))).error || ''), r.status);

// ── Følg links fra forsiden, før du gætter stier ──────────────────────
// Dommen er på det, kunden får at se. Før dette gik scanneren ud fra, at en
// juridisk side hedder `/privacy` — og et site med privatlivspolitikken på
// `/da/juridisk/privatlivspolitik`, som footeren linker, fik «Not found».
// Fundet var rigtigt, det lignede bare en kundes egen fejl.
//
// Derfor skal linket slå gættet, listen skal kunne efterprøves, og værnet skal
// gælde: et link til et andet domæne er ikke en side i det indsendte site.
r = await call('/api/compliance-scan?url=' + encodeURIComponent('fode.example'), ip(28));
const foede = await r.json().catch(() => ({}));
const foedeFund = [...(foede.results?.failed || []), ...(foede.results?.passed || [])];
const privatliv = foedeFund.find(x => x.key === 'privacy');
ok('scanneren finder en privatlivspolitik, forsiden linker til',
  r.status === 200 && privatliv && privatliv.status === 'pass',
  `${r.status} privacy=${privatliv ? privatliv.status + ' ' + privatliv.details : 'sagt ikke'}`);
ok('fundet er den linkede side, ikke en gæt',
  privatliv?.status === 'pass' && /\/da\/juridisk\/privatlivspolitik/.test(privatliv.details || ''),
  privatliv?.details || '');
const vilkaar = foedeFund.find(x => x.key === 'terms');
ok('samme for vilkår, der også kun findes via et link',
  vilkaar?.status === 'pass' && /\/betingelser/.test(vilkaar.details || ''),
  vilkaar ? vilkaar.status + ' ' + vilkaar.details : 'sagt ikke');
ok('rapporten siger hvilke sider der blev læst, så kunden kan efterprøve det',
  Array.isArray(foede.pages_read) && foede.pages_read.length >= 3
  && foede.pages_read.some(u => /\/da\/juridisk\/privatlivspolitik/.test(u))
  && foede.pages_read.some(u => /\/betingelser/.test(u)),
  JSON.stringify(foede.pages_read || []).slice(0, 200));
ok('listen over læste sider er kortere end antallet af kald, fordi et 404 ikke er læst',
  Array.isArray(foede.pages_read) && Array.isArray(foede.pages_checked)
  ? true : typeof foede.pages_checked === 'number',
  `read=${(foede.pages_read || []).length} checked=${foede.pages_checked}`);
ok('scanneren læser kun sider på det indsendte website — ikke Facebook, PDF\'en eller et andet domæne',
  Array.isArray(foede.pages_read) && foede.pages_read.every(u => /^https:\/\/(www\.)?fode\.example\//.test(u)),
  JSON.stringify(foede.pages_read || []).slice(0, 220));
// Tælleren, ikke listen: et domæne der aldrig svarede ville ikke stå i
// `pages_read` alligevel, så dommen ovenfor kan ikke alene bevise at værnet
// holder. Denne dom kan.
ok('der går overhovedet intet kald til et domæne uden for det indsendte',
  andetFetches === 0, `${andetFetches} kald til andet.example`);
// Budgettet skal stadig være delt og uændret. Link-følgning må ikke gøre ét
// kald dyrere end før, fordi det så er en ny måde at brænde subrequests af.
ok('link-følgning koster ikke mere end det delte budget',
  fodeFetches <= 12, `${fodeFetches} fetch til fode.example`);

// Budgettet skal være delt. `tung.example` svarer 200 på forsiden og 404 på
// alt andet, så hvert af de ni tjek bruger hele sin del af budgettet — det er
// det værste tilfælde, og det er derfor porten måler det dér. Ét kald med begge
// skal ikke koste dobbelt så mange ude-kald som to kald.
const tungFør = tungFetches;
await call('/api/compliance-scan?url=' + encodeURIComponent('tung.example'), ip(25));
const ettKald = tungFetches - tungFør;
await call('/api/compliance-scan?url=' + encodeURIComponent('tung.example\ntung2.example'), ip(26));
const toKald = tungFetches - tungFør - ettKald;
ok('ét kald med to URL\'er koster ikke to gange ét kald med ét URL',
  ettKald > 8 && toKald <= ettKald + 2, `1 URL: ${ettKald} fetch, 2 URL: ${toKald} fetch`);

// ── Budgettet skal være delt retfærdigt, og et fund skal være et fund ──
// Fund fra review 30/9, målt på den levende rute: `GET /api/compliance-scan`
// med tre URL'er gav to fulde rapporter og en tredje bygget på forsiden alene.
// Den tredje var wordpress.org, som både har og linker sin privatlivspolitik —
// og rapporten sagde «Not found. Add a Privacy Policy page and link it from
// your footer» om den. Fire sådanne fund og en score, der sendes videre til en
// kunde, er præcis det værktøjet sælger.
//
// Årsagen er to ting, og porten skal dømme begge:
// 1. Budgettet lå i den første rapport. Nu har hvert URL sin egen andel.
// 2. Et tjek, der ikke nåede igennem sine kandidater, blev skrevet som «Not
//    found». Nu står det som sit eget: `status: "unknown"` i `results.notChecked`
//    og uden for `failed`, fordi «Not found» er en dom og «ikke læst» ingen.
const tungFoer = tungFetches;
r = await call('/api/compliance-scan?url=' + encodeURIComponent('tung.example\ntung2.example\ndela.example'), ip(29));
const delt = await r.json().catch(() => ({}));
const delRapporter = delt.reports || [];
const tungRep = delRapporter.find(x => x.url === 'https://tung.example') || {};
const delaRep = delRapporter.find(x => x.url === 'https://dela.example') || {};
const delaAlle = [...(delaRep.results?.passed || []), ...(delaRep.results?.failed || []), ...(delaRep.results?.notChecked || [])];
const delaPrivatliv = delaAlle.find(x => x.key === 'privacy');
// Kun de juridiske sider sætter «Not found» — cookie, meta-tags og header er
// læst på forsiden alene og skal dømmes begge veje. De skal ikke gå i flok.
const CSC_SIDE_TJEK = ['privacy', 'terms', 'imprint', 'accessibility', 'dpa'];
ok('tre URL\'er i ét kald giver tre rapporter, også når de to første er tunge',
  r.status === 200 && delRapporter.length === 3 && !!tungRep.ok && !!delaRep.ok,
  `${r.status} ${JSON.stringify(delt).slice(0, 160)}`);
ok('det tredje site bliver scannet for alvor, ikke kun forsiden',
  delaRep.pages_checked >= 2, `pages_checked=${delaRep.pages_checked}`);
ok('et site der linker sin privatlivspolitik hører ikke «Not found. Add a Privacy Policy page»',
  delaPrivatliv?.status === 'pass' && /\/om\/privatlivspolitik/.test(delaPrivatliv?.details || ''),
  delaPrivatliv ? delaPrivatliv.status + ' ' + delaPrivatliv.details : 'sagt ikke');
ok('et tjek der ikke blev læst, står ikke som et fund',
  Array.isArray(tungRep.results?.notChecked) && tungRep.not_checked === tungRep.results.notChecked.length
  && tungRep.failed === tungRep.results.failed.length
  && !tungRep.results.failed.some(x => /Not checked/i.test(x.details || '')),
  `not_checked=${tungRep.not_checked} failed=${tungRep.failed}`);
ok('«ikke læst» får sin egen status, så klienten kan skelne det fra et fund',
  (tungRep.results.notChecked || []).length > 0 && tungRep.results.notChecked.every(x => x.status === 'unknown'
    && /Not checked/.test(x.details || '')),
  JSON.stringify((tungRep.results?.notChecked || []).map(x => [x.key, x.status])));
ok('alle ni tjek er med i rapporten — fund og ulæste tjek tilsammen',
  delRapporter.every(x => x.results
    && x.results.passed.length + x.results.failed.length + (x.results.notChecked || []).length === x.total),
  JSON.stringify(delRapporter.map(x => [x.url, x.passed, x.failed, x.not_checked, x.total])));
// Koster et kald med tre URL'er stadig højst 12 ude-kald i alt? Det var hele
// pointen med det delte budget, og en retfærdig deling må ikke gøre et kald
// dyrere end det var før.
ok('delingen gør ikke ét kald dyrere end de 12 kald det må koste',
  tungFetches - tungFoer <= 12 && delRapporter.every(x => x.pages_checked <= 6),
  `i alt ${tungFetches - tungFoer} kald til tung.example/tung2.example, pr. rapport ${delRapporter.map(x => x.pages_checked)}`);
ok('«ikke læst» står ikke i listen over fund, klienten sender videre til kunden',
  (tungRep.results.notChecked || []).every(x => !tungRep.results.failed.includes(x))
  && tungRep.results.failed.every(x => x.status !== 'unknown'),
  `failed=${tungRep.failed} notChecked=${tungRep.not_checked}`);
// Samme site i et kald for sig selv. Det har **mere** budget, så her får alle
// ni tjek en chance — men 12 kald er 12 kald, og de gættede stier er der flere
// end det. Så er svaret ikke «ikke læst», men et fund der **siger fra hvor**: «vi
// læste 2 af 7 sandsynlige sider». Det er den anden halvdel af rettelsen —
// dommen skal være så stærk som beviserne, ikke stærkere.
r = await call('/api/compliance-scan?url=' + encodeURIComponent('dela.example'), ip(30));
const delaEn = await r.json().catch(() => ({}));
const delaEnAlle = [...(delaEn.results?.passed || []), ...(delaEn.results?.failed || []), ...(delaEn.results?.notChecked || [])];
const delaEnFund = (delaEn.results?.failed || []).filter(x => CSC_SIDE_TJEK.includes(x.key));
ok('et kald for sig selv finder stadig privatlivspolitikken på den linkede sti',
  r.status === 200 && delaEnAlle.find(x => x.key === 'privacy')?.status === 'pass',
  JSON.stringify(delaEnAlle.filter(x => x.status !== 'pass').map(x => [x.key, x.status])));
ok('«Not found» om en juridisk side siger fra hvor mange kandidater der faktisk blev læst',
  delaEnFund.length > 0 && delaEnFund.every(x => /^Not found\. Add a .+ We checked \d+ of the \d+ pages we expected here\. Check the rest by hand\.$/.test(x.details || '')),
  JSON.stringify(delaEnFund.map(x => [x.key, x.details])));
ok('sædningen er sand i begge kald: ét URL lover ikke, at scan alene løser det',
  delaEnAlle.filter(x => x.status === 'unknown').every(x => !/on its own/.test(x.details || ''))
  && delRapporter.every(x => (x.results.notChecked || []).every(y => /send one site per call/.test(y.details || ''))),
  JSON.stringify([...delaEnAlle, ...(tungRep.results.notChecked || [])].filter(x => x.status === 'unknown').map(x => x.details).slice(0, 2)));

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

// ── Kapabilitets-tjekket: er assistenten tændt overhovedet? ─────────
// Målt 1/10: `POST /api/compliance-ai` svarede 503 «AI service not
// configured. Contact the site owner.» på en publiceret side, fordi
// `OPENROUTER_API_KEY` mangler på workeren. En besøgende skrev et helt spørgsmål
// og blev bedt om at kontakte os — og der er intet andet på siden at bruge.
// Siden skal derfor kunne finde ud af det *inden* spørgsmålstasten, og det er
// et GET der kun læser én env-var.
//
// Fire ting skal være sande samtidig, og hver især er et krav fra en tidligere
// fejl i den samme rute:
//   - det koster **intet**: ingen OpenRouter-kald, ingen dagskvote. Ellers
//     bruger selve tjekket den kvote, spørgsmålet skulle have brugt;
//   - det er **kun et læs**: GET ændrer ingen tilstand (link-scannere åbner
//     GET-links, så en GET der skriver er en fejl i sig selv);
//   - det **lyver ikke**: `available` skal være sandt, når der ER en nøgle —
//     ellers tænder siden en chat, der fejler, og vi er tilbage ved ordet fra
//     1/10;
//   - det **er et svar, ikke en fejl**: 503 ville få klienten til at genkalde
//     en tillstand, der aldrig ændrer sig.
const quotaBeforeProbe = await aiCount();
const probeNoKey = await worker.fetch(new Request('https://mahope.tools/api/compliance-ai'), env, {});
const probeBody = await probeNoKey.json();
ok('GET /api/compliance-ai svarer 200 uden nøgle', probeNoKey.status === 200, probeNoKey.status);
ok('GET /api/compliance-ai melder available:false uden nøgle', probeBody.available === false, JSON.stringify(probeBody));
ok('GET /api/compliance-ai uden nøgle tæller ingen dagskvote', await aiCount() === quotaBeforeProbe, `kvote ${quotaBeforeProbe} -> ${await aiCount()}`);
r = await worker.fetch(new Request('https://mahope.tools/api/compliance-ai'), aiEnv, {});
ok('GET /api/compliance-ai melder available:true med nøgle', (await r.json()).available === true);
let upstreamCalls = 0;
globalThis.fetch = async (u, o) => {
  if (String(u).startsWith('https://openrouter.ai/')) { upstreamCalls++; return new Response('{}', { status: 500 }); }
  return realFetch(u, o);
};
const kvBeforeProbe = kv.size;
await worker.fetch(new Request('https://mahope.tools/api/compliance-ai'), aiEnv, {});
ok('GET /api/compliance-ai kalder ikke OpenRouter', upstreamCalls === 0, 'opkald=' + upstreamCalls);
ok('GET /api/compliance-ai skriver ingen tilstand', kv.size === kvBeforeProbe, `${kvBeforeProbe} -> ${kv.size}`);
globalThis.fetch = realFetch;
r = await worker.fetch(new Request('https://mahope.tools/api/compliance-ai', { method: 'PUT' }), aiEnv, {});
ok('andre metoder end GET/POST er stadig afvist', r.status === 405, r.status);
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
//    Fast ur, som i timegrænse-afsnittet: `sentryRateLimited` i _worker.js
//    slipper kun én rapport pr. 12. sekund, så de tolv kald skal ligge i det
//    samme vindue. Uden pin målte `clock_jump.mjs` 12 rapporter i stedet for 1
//    2/10 — dvs. påstanden testede klokken og ikke tælleren. Måleværdi er
//    minuttens begyndelse, så uret aldrig springer baglænes.
sentryEnvelopes = [];
deadTag = 'loekke';
const stopMinutUr = (() => {
  const forrige = Date.now;
  const fast = Math.floor(forrige() / 60000) * 60000;
  Date.now = () => fast;
  return () => { Date.now = forrige; };
})();
for (let i = 0; i < 12; i++) await deadCall('/loekke');
stopMinutUr();
ok('en fejl i en løkke sendes højst SENTRY_MAX_PER_MINUTE gange',
  sentryEnvelopes.length > 0 && sentryEnvelopes.length <= 5, 'enveloper=' + sentryEnvelopes.length);
ok('tælleren lader den første fejl komme ud, så den ikke er død',
  sentryEnvelopes.length === 1, 'enveloper=' + sentryEnvelopes.length);

// ── En besøgendes browser melder sine egne uventede fejl ──────────────
// Fejlen her er synlig i ruten over: `reportWorkerError` dækker kun
// workerens egen fetch, så alt der går galt i `site/track.js` eller i en af de
// 300 sider der indlæser den, efterlod hverken en 500, en log eller en
// Sentry-hændelse. Det er dér en købsvej dør. Sentry sagde «ingen uløste fejl
// i 14 dage» — fordi intet blev sendt.
//
// Ruten tager imod data fra klienten, så de interessante tests er ikke «virker
// den», men «hvad kan den ikke sende videre». `/compliance-site-check` tager
// fem URL'er i query-strengen, så en rapport med `location.href` ville lægge
// de besøgendes sider i et offentligt fejlspor.
const CE = '/api/client-error';
// En rigtig browser-UA er ikke pynt: `isAutomatedRequest` siger ja til et kald
// uden en, og ruten svarer så 200 uden at skrive noget. Uden den ville hver
// kontrol nedenfor være grøn af den grund at den ikke kan fejle — præcis den
// fejlform de andre mutationer i denne fil er bygget til at finde.
const CE_UA = 'Mozilla/5.0 (Windows NT 10.0; rv:128.0) Gecko/20100101 Firefox/128.0';
const ceBody = (extra) => JSON.stringify(Object.assign({
  kind: 'error', name: 'TypeError', message: 'x is not a function',
  file: 'https://mahope.tools/track.js', line: 42, col: 7,
}, extra || {}));
// Refereret er den side fejlen skete på. Query-strengen i en *rigtig* URL er
// præcis der brugeren skriver sin adresse ind, så den bruges her som den
// fælde, ruten skal lukke.
const ceCall = (body, init = {}, host = 'mahope.tools') => worker.fetch(new Request(
  `https://${host}${CE}`,
  Object.assign({ method: 'POST', body }, init),
), env, {});
const ceHeaders = (host = 'mahope.tools') => ({
  'content-type': 'application/json', 'user-agent': CE_UA,
  origin: `https://${host}`, referer: `https://${host}/compliance-site-check?url=https://kunde.dk`,
});

// 1. Grundscenariet: en uventet fejl bliver præcis én rapport.
sentryEnvelopes = [];
const ceOk = await ceCall(ceBody(), { headers: ceHeaders() });
const ce0 = lastEnvelope();
ok('en uventet browserfejl meldes til Sentry', sentryEnvelopes.length === 1, 'enveloper=' + sentryEnvelopes.length);
ok('klienten får et svar den ikke kan fejle i', ceOk.status === 202, ceOk.status);
ok('rapporten er en envelope med en fejl', ce0.body.startsWith('{') && /"exception"/.test(ce0.body)
  && /x is not a function/.test(ce0.body), ce0.body.slice(0, 120));
ok('rapporten er mærket som browser, ikke worker', /"logger":"browser"/.test(ce0.body)
  && /"source":"browser"/.test(ce0.body), ce0.body.slice(0, 300));

// 2. Den regel der er hele pointen: den URL brugeren indtastede må ikke med.
//    `referer` bærer den, fordi det er sådan et beacon ser ud, så testen er
//    ikke hypotetisk — den er den normale anmodning.
ok('rapporten indeholder ikke den indtastede URL',
  !/kunde\.dk/.test(ce0.body) && !/url=/.test(ce0.body), 'lækket query: ' + ce0.body.slice(0, 300));
ok('rapport-URL\'en er origin + rute, som workerens egen',
  /"url":"https:\/\/mahope\.tools\/compliance-site-check"/.test(ce0.body)
  && !/\?/.test((ce0.body.match(/"url":"[^"]*"/) || [''])[0]), ce0.body.slice(0, 300));
ok('rapporten sender hverken krop, headers, cookie eller user-agent',
  !/"headers"/i.test(ce0.body) && !/"cookie"/i.test(ce0.body) && !/"user_agent"/i.test(ce0.body)
  && !/Firefox|Mozilla/i.test(ce0.body), 'lækket ' + ce0.body.slice(0, 300));
ok('klienten sender hverken side eller egen filsti',
  !/"page"/.test(ce0.body) && !/mahope\.tools\/track\.js/.test(ce0.body), ce0.body.slice(0, 400));
ok('filnavnet står i stacktrace, ikke i hele stien',
  /"filename":"track\.js"/.test(ce0.body) && /"lineno":42/.test(ce0.body), ce0.body.slice(0, 400));

// 3. Et felt der ikke er på listen er 400, ikke en rapport. Det er det, der
//    gør «send ikke noget brugeren har skrevet» håndhævet: en ny feltnavn i
//    `track.js` kan ikke lække noget, fordi ruten siger fra før den læses.
for (const felt of ['href', 'page', 'search', 'value', 'cookie']) {
  sentryEnvelopes = [];
  const bad = await ceCall(ceBody({ [felt]: 'https://kunde.dk/hemmeligt' }), { headers: ceHeaders() });
  ok(`et uventet felt (${felt}) giver 400 og ingen rapport`,
    bad.status === 400 && sentryEnvelopes.length === 0, bad.status + ' enveloper=' + sentryEnvelopes.length);
}
// Og de tilladte felter virker stadig — ellers ville punkt 3 være løst ved at
// afvise alt. Egen fejltekst, fordi tælleren pr. fejl pr. minut (punkt 6) har
// brugt nøglen til test 1 ovenfor.
sentryEnvelopes = [];
const ceOk2 = await ceCall(ceBody({ message: 'feltlisten er hel' }), { headers: ceHeaders('cleancopy.tools') }, 'cleancopy.tools');
ok('de seks tilladde felter giver stadig en rapport',
  ceOk2.status === 202 && sentryEnvelopes.length === 1, ceOk2.status + ' enveloper=' + sentryEnvelopes.length);

// 4. Adgangskontrol. En rapport må ikke kunne sendes fra en fremmed side —
//    ellers er Sentry-projektet en åben skraldespand.
sentryEnvelopes = [];
const ceNoOrigin = await ceCall(ceBody(), { headers: { 'content-type': 'application/json', 'user-agent': CE_UA, referer: 'https://mahope.tools/' } });
ok('uden origin giver 403 og ingen rapport', ceNoOrigin.status === 403 && sentryEnvelopes.length === 0, ceNoOrigin.status);
const ceForeign = await ceCall(ceBody(), { headers: { ...ceHeaders(), origin: 'https://evil.tld' } });
ok('fremmed origin giver 403 og ingen rapport', ceForeign.status === 403 && sentryEnvelopes.length === 0, ceForeign.status);
const ceGet = await worker.fetch(new Request('https://mahope.tools' + CE), env, {});
ok('GET giver 405 (link-scannere må ikke kunne skaffe sig en rapport)', ceGet.status === 405, ceGet.status);
const ceUnknown = await ceCall(ceBody(), { headers: { ...ceHeaders(), origin: 'https://example.tld', referer: 'https://example.tld/' } }, 'example.tld');
ok('et domæne uden tracking giver 404 og ingen rapport', ceUnknown.status === 404 && sentryEnvelopes.length === 0, ceUnknown.status);

// 5. Kun i produktion, og kun de fire familiedomæner.
sentryEnvelopes = [];
const ceLocal = await worker.fetch(new Request('https://localhost' + CE, {
  method: 'POST', headers: { 'content-type': 'application/json', 'user-agent': CE_UA, origin: 'https://localhost', referer: 'https://localhost/' },
  body: ceBody(), }), env, {});
ok('localhost sender ingen rapporter', sentryEnvelopes.length === 0, 'enveloper=' + sentryEnvelopes.length);

// 6. En cyklisk fejl må ikke fylde kvoten. Tælleren er pr. fejl pr. minut,
//    så seks *ens* fejl giver én rapport — og det er den rapport, der tæller.
//    Fast ur, som i afsnittet ovenfor og af samme grund: `browserSentryRateLimited`
//    slipper kun én rapport pr. 20. sekund, så de seks kald skal ligge i samme
//    vindue. Uden pin målte `clock_jump.mjs` 6 rapporter i stedet for 1 — dvs.
//    påstanden testede klokken og ikke tælleren. Måleværdi er minuttes
//    begyndelse, så uret aldrig springer baglænes.
sentryEnvelopes = [];
let ce429 = 0;
const stopMinutUr2 = (() => {
  const forrige = Date.now;
  const fast = Math.floor(forrige() / 60000) * 60000;
  Date.now = () => fast;
  return () => { Date.now = forrige; };
})();
for (let i = 0; i < 6; i++) {
  const res = await ceCall(ceBody({ message: 'ResizeObserver loop limit exceeded' }), { headers: ceHeaders() });
  if (res.status === 429) ce429 += 1;
}
stopMinutUr2();
ok('en fejl i en løkke sendes højst CLIENT_ERROR_MAX_PER_MINUTE gange',
  sentryEnvelopes.length === 1, 'enveloper=' + sentryEnvelopes.length);
ok('de overskudende kald får 429 — endelig, ikke forbigående', ce429 === 5, '429=' + ce429);

// 7. Timekvoten pr. besøgende. Nøglen pr. fejl dæmper kun gentagelser af *den
//    samme* fejl, så en løkke der kaster en ny tekst hvert tik slap igennem.
//    Fast ur igen, og af endnu en grund: timekvotens nøgle er
//    `Math.floor(Date.now() / 3600000)` og `visitorHash` salter med dagens dato,
//    så under `clock_jump.mjs` fik hvert eneste kald sin egen timebøtte og sin
//    egen besøgende — og målingen testede igen klokken. Pin til timebøttens
//    begyndelse, så hoppet sker aldrig baglænes.
sentryEnvelopes = [];
let hourly429 = 0, hourly202 = 0;
const stopTimeUr = (() => {
  const forrige = Date.now;
  const fast = Math.floor(forrige() / 3600000) * 3600000;
  Date.now = () => fast;
  return () => { Date.now = forrige; };
})();
for (let i = 0; i < 26; i++) {
  const res = await ceCall(ceBody({ message: 'fejl nummer ' + i }), { headers: ceHeaders('deskuptime.com') }, 'deskuptime.com');
  if (res.status === 429) hourly429 += 1; else if (res.status === 202) hourly202 += 1;
}
stopTimeUr();
ok('timekvoten pr. besøgende stopper en fejl med ny tekst hvert tik',
  hourly429 === 6 && hourly202 === 20, '202=' + hourly202 + ' 429=' + hourly429);

// 9. Overvågningen må aldrig give en besøgende en fejl i stedet for sit
//    resultat. En krop der ikke er JSON, og en krop der er JSON men ikke et
//    objekt, er begge håndterede tilstande.
sentryEnvelopes = [];
const ceJunk = await ceCall('ikke json', { headers: ceHeaders() });
const ceArr = await ceCall('[]', { headers: ceHeaders() });
const ceEmpty = await ceCall(ceBody({ message: '   ' }), { headers: ceHeaders() });
ok('en beskyldt krop giver 400, ikke en fejl',
  ceJunk.status === 400 && ceArr.status === 400 && ceEmpty.status === 400,
  [ceJunk.status, ceArr.status, ceEmpty.status].join('/'));
ok('og ingen af dem skriver til Sentry', sentryEnvelopes.length === 0, 'enveloper=' + sentryEnvelopes.length);

// 6b. Overvågningen må aldrig tage ruten ned, selv når Sentry er nede.

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

// 8. Samme mutation for `/api/client-error`: den gamle kode kender ikke ruten.
//    Uden denne kontrol er de ni kontroller ovenfor grønne af den grund at de
//    ikke kan fejle.
if (preSentryWorker) {
  sentryEnvelopes = [];
  const oldCe = await preSentryWorker.fetch(new Request('https://bugbottle.dev' + CE, {
    method: 'POST',
    headers: { 'content-type': 'application/json', 'user-agent': CE_UA, origin: 'https://bugbottle.dev', referer: 'https://bugbottle.dev/' },
    body: ceBody({ message: 'gammel kode skal tie' }) }), env, {});
  ok('mutation: den gamle kode kender ikke /api/client-error og melder intet',
    sentryEnvelopes.length === 0 && oldCe.status !== 202,
    'enveloper=' + sentryEnvelopes.length + ' status=' + oldCe.status);
}

globalThis.fetch = outerFetch;

// 10. GET /api/results — resultat-tallet uden `STATS_TOKEN`.
//
// Hvorfor denne blok er den vigtigste i filen: hele tragten fra 5/10 var skrevet
// men ulæselig, fordi `/api/stats` svarer 401 og nøglen mangler på workeren.
// Uden en måling er enhver prioritering en antagelse — og den her repo har
// allerede skrevet i planen at alle dens trafiktal er gæt. En offentlig rute er
// derfor *også* en risikogrænse: den skal kun svare det den skal bruges til, så
// kontrollerne nedenfor dømmer både at tallene er rigtige og at intet uden for
// formålsgrænsen slipper ud.
const RS = '/api/results';
const resKv = new Map();
const RES_VISITS = {
  get: async (k) => (resKv.has(k) ? resKv.get(k) : null),
  put: async (k, v) => { resKv.set(k, v); },
  list: async ({ prefix = '' } = {}) => ({ keys: [...resKv.keys()].filter(k => k.startsWith(prefix)).sort().map(name => ({ name })), list_complete: true }),
};
const resEnv = { ...env, VISITS: RES_VISITS };
const resCall = (path, init, e) => worker.fetch(new Request('https://mahope.tools' + path, init), e || resEnv, {});
const isoDaysAgo = (n) => new Date(Date.now() - n * 86400000).toISOString().slice(0, 10);
// Dagsnøglen må ikke flytte sig, mens en trafiksektion kører. Uret i
// `clock_jump.mjs` hopper én time pr. kald, og hver af de to sektioner nedenfor
// laver elleve kald, så de hopper elleve timer — og lander de hen over et
// døgnskifte, ser `isoDaysAgo(0)` og workerens `window[0]` to forskellige
// datoer, og `by_day`-dommen dømmer et vindue, der aldrig blev sået. Det var ikke
// en fejl i workeren: det var CI-run 37340718217 (5/10 kl. 16:25) rødt på
// `pr. dag: 2 i dag 0 og 1 to dage tilbage`, fordi de otte timer pr. sektion
// krydsede netop UTC-midnat. Samme grund som `stopTimeUr2` længere nede: tælleren
// skal måles, ikke klokken. Derfor pinnes uret i hver sektion, og hver sektion får
// sin egen timebøtte, så kvoten på 30 læsninger pr. time ikke deles med naboen.
const pinUr = (() => {
  const forrige = Date.now;
  let fast = Math.floor(forrige() / 3600000) * 3600000;
  return {
    start() { fast += 3600000; Date.now = () => fast; },
    stop() { Date.now = forrige; },
  };
})();
// Én trafiknøgle pr. begivenhed, som `recordTraffic()` skriver den: værdien er
// altid '1', så nøglenavnet *er* optællingen.
const seed = (kind, daysAgo, domain, path, event, identity) => {
  const key = `${kind}:v3:${isoDaysAgo(daysAgo)}:${domain}:event:${encodeURIComponent(`${path}@${event}`)}:${identity}`;
  resKv.set(key, '1');
};
// 1. Grundscenariet: tre kørsler på to dage, hvoraf den ene besøgende gav to
//    resultater samme dag — det er præcis det `visitor_days` skal finde.
pinUr.start();
seed('p', 0, 'mahope.tools', '/scan', 'scan-findings', 'u-1');
seed('u', 0, 'mahope.tools', '/scan', 'scan-findings', 'v-1');
seed('p', 0, 'mahope.tools', '/scan', 'scan-clean', 'u-2');
seed('u', 0, 'mahope.tools', '/scan', 'scan-clean', 'v-2');
seed('p', 2, 'mahope.tools', '/nis2-check', 'finish', 'u-3');
seed('u', 2, 'mahope.tools', '/nis2-check', 'finish', 'v-3');
//    Og en bunke ting der *ikke* er resultater. De ligger i samme nøgler og skal
//    alle forblive ude, ellers er tallet ikke længere «resultater».
seed('p', 0, 'mahope.tools', '/scan', 'scan-failed', 'u-9');
seed('p', 0, 'mahope.tools', '/scan', 'scan', 'u-9');
seed('p', 0, 'mahope.tools', '/scan', 'pro-card-click', 'u-9');
//    Et købsklik sker på en værktøjsside, ikke på `/` — ellers ville den blive
//    droppet af stidommet og en streng på navnelisten ville aldrig blive dømt.
seed('p', 0, 'mahope.tools', '/scan', 'buy-click', 'u-9');
seed('p', 0, 'mahope.tools', '/scan', 'cta-tool', 'u-9');
seed('p', 0, 'mahope.tools', '/compliance-ai', 'ai-unavailable', 'u-9');
//    Sidevisninger og downloads er `page`/`download`, ikke `event`, så de må ikke
//    kunne læses som resultater selv om emnet ligner et.
resKv.set(`p:v3:${isoDaysAgo(0)}:mahope.tools:page:%2Fscan:u-7`, '1');
resKv.set(`p:v3:${isoDaysAgo(0)}:mahope.tools:download:%2Fscan@scan-findings:u-7`, '1');
resKv.set('csc-count', '41');

let rs = await resCall(`${RS}?days=7`);
let rsBody = await rs.json();
ok('resultat-ruten svarer 200 uden nogen hemmelighed', rs.status === 200 && rsBody.ok === true, rs.status);
ok('tre kørsler i vinduet, fordelt på to værktøjer',
  rsBody.totals.runs === 3 && rsBody.results['/scan'].runs === 2
  && rsBody.results['/nis2-check'].runs === 1, JSON.stringify(rsBody.results));
ok('besøgende-dage tælles hver for sig, ikke kørsler',
  rsBody.totals.visitor_days === 3 && rsBody.results['/scan'].visitor_days === 2,
  JSON.stringify(rsBody.results));
ok('pr. dag: 2 i dag 0 og 1 to dage tilbage',
  rsBody.by_day[isoDaysAgo(0)] === 2 && rsBody.by_day[isoDaysAgo(2)] === 1
  && rsBody.by_day[isoDaysAgo(1)] === 0, JSON.stringify(rsBody.by_day));
ok('hverken forsøg, købsklik, fejl eller CTA tælles som resultat',
  rsBody.totals.runs === 3 && !/buy-click|scan-failed|pro-card-click|ai-unavailable/.test(JSON.stringify(rsBody.results)),
  JSON.stringify(rsBody.results));
ok('status er ok, fordi dagen var komplet', rsBody.status === 'ok', rsBody.status);
ok('den server-side scancounter kommer med som et andet vidnesbyrd',
  rsBody.served_scans_lifetime === 41, String(rsBody.served_scans_lifetime));
// 5/10: feltet hed `served_scans` og blev læst som et tal for vinduet. Det er en
//    *kumulativ* tæller (`expirationTtl: 365 * 86400`), så 41 livslang mod 0 i
//    vinduet siger intet om klientens tracking — kun at værktøjet ingen besøgende
//    har. Præfikset er derfor en del af svarets kontrakt, ikke en omdøbning.
ok('den kumulative tæller kan ikke læses som et vinduestal',
  rsBody.served_scans === undefined && 'served_scans_lifetime' in rsBody
  && /NOT a count\s+for this window/.test(rsBody.note),
  JSON.stringify(Object.keys(rsBody).filter((k) => k.includes('scans')))
  + ' note=' + String(rsBody.note).slice(0, 40));

// 2. En forfalsket `referer` er et emne, der kan skrives af enhver. Den må ikke
//    spejles tilbage i et offentligt svar, og den må ikke tælle som et værktøj.
resKv.set(`p:v3:${isoDaysAgo(0)}:mahope.tools:event:${encodeURIComponent('/hemmeligt/<script>alert(1)</script>@scan-findings')}:u-6`, '1');
resKv.set(`p:v3:${isoDaysAgo(0)}:mahope.tools:event:${encodeURIComponent(`/${'x'.repeat(140)}@scan-findings`)}:u-6`, '1');
rsBody = await (await resCall(`${RS}?days=7`)).json();
ok('et resultat med en utilladelig sti hverken tælles eller spejles',
  rsBody.totals.runs === 3 && rsBody.dropped === 2
  && !/script|alert|xxxx/.test(JSON.stringify(rsBody)), JSON.stringify(rsBody.results) + ' dropped=' + rsBody.dropped);

// 3. Kun de fire domæner vi måler, og kun gyldige nøgler. En nøgle med et
//    domæne der ikke findes, eller en dag der ikke er en dato, ignoreres.
resKv.set(`p:v3:${isoDaysAgo(0)}:evil.tld:event:%2Fscan%40scan-findings:u-5`, '1');
resKv.set(`p:v3:ikke-en-dato:mahope.tools:event:%2Fscan%40scan-findings:u-5`, '1');
resKv.set(`p:v3:${isoDaysAgo(0)}:mahope.tools:event:ikke-kodet:u-5`, '1');
rsBody = await (await resCall(`${RS}?days=7`)).json();
ok('et fremmed domæne og en ugyldig nøgle tælles ikke med',
  rsBody.totals.runs === 3, JSON.stringify(rsBody.results));

// 5. Den kumulative tæller skal hedde det samme i *alle tre* ruter. Målt 6/10:
//    `/api/results` havde fået præfikset (`served_scans_lifetime`), men
//    `/api/stats` og `/api/health` stod med `scans` — og `/api/health` er
//    **offentlig** og læser `recentVisits: 12` fra et *to dages* vindue i samme
//    objekt. En cron kunne derfor rapportere «50 scanninger på to dage».
//    `csc-count` skrives med `expirationTtl: 365 * 86400` og genoplades ved hvert
//    skriv, så tallet kan kun stå stille eller stige: et fald i `recentVisits`
//    er derfor intet signal om scanneren, og præfikset er en del af svarets
//    kontrakt — ikke en omdøbning man kan slå fra.
//    Samme fælde gjaldt `wl-count` og `ai-ask-count`, som også skrives med et
//    365 dages TTL og også hed bare `waitlist` / `ai_asks`. De dømmes med.
kv.set('csc-count', '41');
kv.set('wl-count', '7');
kv.set('ai-ask-count', '12');
const healthBody = await (await call('/api/health')).json();
ok('/api/health er offentlig og svarer 200 uden nøgle', healthBody.ok === true, JSON.stringify(healthBody.status));
ok('/api/health dømmer scancounteren som livslang, ikke som et vinduestal',
  healthBody.stats.scans_lifetime === 41 && healthBody.stats.scans === undefined,
  'stats=' + JSON.stringify(healthBody.stats));
ok('/api/health gør det samme for ventelisten',
  healthBody.stats.waitlist_lifetime === 7 && healthBody.stats.waitlist === undefined,
  'stats=' + JSON.stringify(healthBody.stats));
const statsBody = await (await statsCall()).json();
ok('/api/stats dømmer scancounteren som livslang, ikke som et tal for days',
  statsBody.scans_lifetime === 41 && statsBody.scans === undefined,
  'days=' + statsBody.days + ' nøgler='
  + JSON.stringify(Object.keys(statsBody).filter((k) => k.includes('scans'))));
ok('/api/stats gør det samme for ventelisten og assistenten',
  statsBody.waitlist_lifetime === 7 && statsBody.waitlist === undefined
  && statsBody.ai_asks_lifetime === 12 && statsBody.ai_asks === undefined,
  'nøgler=' + JSON.stringify(Object.keys(statsBody)
    .filter((k) => /waitlist|ai_asks/.test(k))));
// Et *vindues*tal beholder sit navn: `ai_limited_today` er et døgnsalt, så
// præfikset skal ikke smitte over på den. Påstanden er om *navnet*, derfor
// dømmer den at nøglen er til stede og at dens `_lifetime`-tvilling ikke er.
ok('et døgnsalt beholder sit navn — porten skal kun dømme de kumulative',
  'ai_limited_today' in statsBody && statsBody.ai_limited_today_lifetime === undefined,
  JSON.stringify(Object.keys(statsBody).filter((k) => k.includes('ai_limited'))));
// De tre ruter skal vælge det samme navn — ellers kan en læser ikke sammenligne
// dem, og det er netop sammenligningen med vindues tallene der er fælden.
ok('alle tre ruter bruger det samme feltnavn for den kumulative tæller',
  rsBody.served_scans_lifetime === 41 && statsBody.scans_lifetime === 41
  && healthBody.stats.scans_lifetime === 41);

// 4. Sandheden om sin egen fuldstændighed. En dag der rammer grænsen må ikke
//    summeres til et for lille tal; den skal sige `partial` og den skal være
//    ulæselig, fordi `null` og `0` er to forskellige påstande.
const dayFlood = isoDaysAgo(0);
resKv.clear();
for (let i = 0; i < 2001; i += 1) seed('p', 0, 'mahope.tools', '/scan', 'scan-findings', `bulk-${i}`);
resKv.set(`p:v3:${dayFlood}:mahope.tools:event:%2Fscan%40scan-findings:buk-unik`, '1');
rsBody = await (await resCall(`${RS}?days=7`)).json();
ok('en dag over nøglegrænsen melder partial og tælles ikke',
  rsBody.status === 'partial' && rsBody.totals.runs === 0 && rsBody.by_day[dayFlood] === null,
  rsBody.status + ' runs=' + rsBody.totals.runs + ' dag=' + rsBody.by_day[dayFlood]);
//    Og med en nøgle *uden* grænsen er den samme dag 1, så dommen læser
//    grænsen og ikke et tilfældigt resultat.
resKv.delete(`p:v3:${dayFlood}:mahope.tools:event:%2Fscan%40scan-findings:buk-unik`);
//    Præcis én nøgle væk: de 2002 nøgler (2001 + den unikke) var over grænsen på
//    2000, så de 2000 der er tilbage lige på grænsen. Dommen skal læse grænsen
//    og ikke et tilfældigt antal.
resKv.delete(`p:v3:${dayFlood}:mahope.tools:event:${encodeURIComponent('/scan@scan-findings')}:bulk-2000`);
rsBody = await (await resCall(`${RS}?days=7`)).json();
ok('uden nøglen over grænsen er den samme dag komplet igen',
  rsBody.status === 'ok' && rsBody.totals.runs === 2000, rsBody.status + ' runs=' + rsBody.totals.runs);

// 5. En kvotefejl skal slå igennem, så en læsning aldrig bare ser ud som nul.
const resBrokenKv = { ...RES_VISITS, list: async () => { throw new Error('kv nede'); } };
rsBody = await (await resCall(`${RS}?days=7`, {}, { ...resEnv, VISITS: resBrokenKv })).json();
ok('en KV der kaster giver status unknown og nul løfter på tallene',
  rsBody.status === 'unknown' && rsBody.totals.runs === 0, rsBody.status + ' runs=' + rsBody.totals.runs);
rs = await resCall(`${RS}?days=7`, {}, { ...resEnv, VISITS: null });
ok('uden KV-binding svarer ruten 503, ikke 200 med nul', rs.status === 503, rs.status);

// 6. Vinduet er dæmpet, fordi hvert døgn koster to opslag.
rsBody = await (await resCall(`${RS}?days=9999`)).json();
ok('days dæmpes til 28', rsBody.days === 28 && rsBody.window.length === 28, String(rsBody.days));
rsBody = await (await resCall(`${RS}?days=-4`)).json();
ok('et negativt days falder tilbage til standardvinduet',
  rsBody.days === 7 && rsBody.window.length === 7, String(rsBody.days));
rsBody = await (await resCall(`${RS}?days=abc`)).json();
ok('et days der ikke er et tal giver standardvinduet',
  rsBody.days === 7, String(rsBody.days));

// 7. Metoder og kvota. GET må ikke ændre noget, så POST er 405.
rs = await resCall(RS, { method: 'POST', body: '{}' });
ok('POST giver 405', rs.status === 405, rs.status);
pinUr.stop();
//    Tælleren er pr. IP pr. time, så uret pinnes til timebøttens begyndelse —
//    ellers måler testen klokken og ikke tælleren, som `clock_jump.mjs` viste.
const resKv2 = new Map();
const resEnv2 = { ...resEnv, VISITS: { ...RES_VISITS, get: async (k) => (resKv2.has(k) ? resKv2.get(k) : null), put: async (k, v) => { resKv2.set(k, v); } } };
const stopTimeUr2 = (() => {
  const forrige = Date.now;
  const fast = Math.floor(forrige() / 3600000) * 3600000;
  Date.now = () => fast;
  return () => { Date.now = forrige; };
})();
let res429 = 0, res200 = 0;
for (let i = 0; i < 32; i += 1) {
  const s = (await resCall(`${RS}?days=7`, {}, resEnv2)).status;
  if (s === 429) res429 += 1; else if (s === 200) res200 += 1;
}
stopTimeUr2();
ok('kvoten pr. IP pr. time stopper læsningerne',
  res200 === 30 && res429 === 2, '200=' + res200 + ' 429=' + res429);

// 8. Listen skal ikke indeholde en streng der ikke findes i `site/` — en
//    omdøbt begivenhed ville ellers tælle med i det stille, og en tastefejl
//    ville få navnelisten til at se komplet ud uden at være det.
const siteDir = new URL('../site/', import.meta.url);
const siteFiles = execFileSync('find', [siteDir.pathname, '-name', '*.html', '-o', '-name', '*.js'], { encoding: 'utf8' })
  .split('\n').filter(Boolean);
const siteCode = siteFiles.map(f => readFileSync(f, 'utf8')).join('\n');
const workerSrcRs = readFileSync(fileURLToPath(new URL('../site/_worker.js', import.meta.url)), 'utf8');
const resultEvents = (workerSrcRs.match(/const RESULT_EVENTS = Object\.freeze\(\[([\s\S]*?)\]\)/) || ['', ''])[1]
  .split(',').map(s => s.trim().replace(/^'|'$/g, '')).filter(Boolean);
ok('resultatlisten er ikke tom', resultEvents.length >= 5, 'n=' + resultEvents.length);
for (const event of resultEvents) {
  ok(`«${event}» findes som trackEvent i site/`,
    new RegExp(`trackEvent\\(\\s*'${event}'`).test(siteCode)
    || new RegExp(`trackEvent\\(\\s*[a-zA-Z_$][\\w$]*\\s*\\?\\s*'${event}'`).test(siteCode)
    || new RegExp(`trackEvent\\([^)]*'${event}'`).test(siteCode),
    'begivenheden kaldes ikke fra nogen side');
}

// 9. Mutationen: den kode der var her *før* denne ændring kender ikke ruten.
//    Uden denne kontrol er de kontroller ovenfor grønne af den grund at de ikke
//    kan fejle — den samme fejlform de andre mutationer i denne fil er bygget til.
const PRE_RESULTS_SHA = 'b66c8c3e';
let preResultsWorker = null, preResultsNote = '';
try {
  const oldSrcResults = execFileSync('git', ['show', `${PRE_RESULTS_SHA}:site/_worker.js`],
    { cwd: root, encoding: 'utf8', maxBuffer: 64 * 1024 * 1024, stdio: ['ignore', 'pipe', 'ignore'] });
  ok('mutationen finder den gamle kode (ellers dommer den intet)', !/handleResults/.test(oldSrcResults));
  const oldTmpResults = join(tmpdir(), `worker-pre-results-${process.pid}.mjs`);
  writeFileSync(oldTmpResults, oldSrcResults);
  preResultsWorker = (await import(pathToFileURL(oldTmpResults).href)).default;
} catch (e) {
  preResultsNote = 'git-historikken er ikke tilgængelig her: ' + (e.code || e.message);
}
if (preResultsWorker) {
  resKv.clear();
  seed('p', 0, 'mahope.tools', '/scan', 'scan-findings', 'u-1');
  const oldResults = await preResultsWorker.fetch(new Request('https://mahope.tools' + RS), resEnv, {});
  const oldResultsBody = await oldResults.json().catch(() => ({}));
  ok('mutation: den gamle kode svarer 404 og ikke et resultattal',
    oldResults.status === 404 && oldResultsBody.totals === undefined,
    oldResults.status + ' totals=' + oldResultsBody.totals);
} else {
  console.log('NOTE: mutationen mod den gamle kode er sprunget over — ' + preResultsNote);
}

// 11. GET /api/conversion — købsintents-klik uden `STATS_TOKEN`.
//
// samme begrundelse som blok 10, med en anden nåle: `/api/stats` svarer 401, så
// «kommer der penge ind» var ulæseligt, og Plausible kan kun se toppen af
// tragten. Denne rute tæller klik på købsknapper — ikke resultater, ikke salg —
// og hun har derfor sin egen navneliste, sin egen nøglegrænse og sin egen kvota.
// Kontrollerne dømmer både at tallene er rigtige og at intet uden for
// formålsgrænsen slipper ud: en mailadresse, en licensnøgle eller et beløb i et
// offentligt svar ville være en persondata- eller indkomstlækage.
const CV = '/api/conversion';
const cvKv = new Map();
const CV_VISITS = {
  get: async (k) => (cvKv.has(k) ? cvKv.get(k) : null),
  put: async (k, v) => { cvKv.set(k, v); },
  list: async ({ prefix = '' } = {}) => ({ keys: [...cvKv.keys()].filter(k => k.startsWith(prefix)).sort().map(name => ({ name })), list_complete: true }),
};
const cvEnv = { ...env, VISITS: CV_VISITS };
const cvCall = (path, init, e) => worker.fetch(new Request('https://mahope.tools' + path, init), e || cvEnv, {});
const cvSeed = (kind, daysAgo, path, event, identity) => {
  cvKv.set(`${kind}:v3:${isoDaysAgo(daysAgo)}:mahope.tools:event:${encodeURIComponent(`${path}@${event}`)}:${identity}`, '1');
};
// Grundscenariet: fire købsklik på to sider og et pro-kort-klik, fordelt på to
// dage, hvoraf ét klik gjorde den samme besøgende to gange.
pinUr.start();
cvSeed('p', 0, '/compliance-report', 'buy-click', 'u-1');
cvSeed('u', 0, '/compliance-report', 'buy-click', 'v-1');
cvSeed('p', 0, '/compliance-report', 'buy-click', 'u-2');
cvSeed('u', 0, '/compliance-report', 'buy-click', 'v-2');
cvSeed('p', 0, '/scan', 'pro-card-click', 'u-3');
cvSeed('u', 0, '/scan', 'pro-card-click', 'v-3');
cvSeed('p', 2, '/clean-copy-tool', 'buy-click', 'u-4');
cvSeed('u', 2, '/clean-copy-tool', 'buy-click', 'v-4');
//    Og de ting der ikke er købsintents: resultater, forsøg, navigation,
//    sidevisninger, ventelister og udleverede licenser. De ligger i de samme
//    nøgler og skal alle blive ude, ellers er tallet ikke længere konvertering.
cvSeed('p', 0, '/scan', 'scan-findings', 'u-9');
cvSeed('p', 0, '/scan', 'scan-failed', 'u-9');
cvSeed('p', 0, '/scan', 'cta-scan', 'u-9');
cvSeed('p', 0, '/scan', 'ai-cta', 'u-9');
cvSeed('p', 0, '/scan', 'store-click', 'u-9');
cvSeed('p', 0, '/scan', 'licenses_issued', 'u-9');
cvSeed('p', 0, '/scan', 'waitlist', 'u-9');
cvKv.set(`p:v3:${isoDaysAgo(0)}:mahope.tools:page:%2Fscan:u-7`, '1');
cvKv.set(`u:v3:${isoDaysAgo(0)}:mahope.tools:event:${encodeURIComponent('/scan@waitlist')}:u-8`, '1');

let cv = await cvCall(`${CV}?days=7`);
let cvBody = await cv.json();
ok('konverteringsruten svarer 200 uden nogen hemmelighed', cv.status === 200 && cvBody.ok === true, cv.status);
ok('fire købsklik i vinduet, fordelt på to sider',
  cvBody.totals.buy_clicks === 4 && cvBody.by_page['/compliance-report'].buy_clicks === 2
  && cvBody.by_page['/clean-copy-tool'].buy_clicks === 1, JSON.stringify(cvBody.by_page));
ok('pro-kort-klikket tælles i sit eget felt, men er også et købsintents-klik',
  cvBody.totals.pro_card_clicks === 1 && cvBody.totals.buy_clicks === 4,
  'pro=' + cvBody.totals.pro_card_clicks + ' buy=' + cvBody.totals.buy_clicks);
ok('besøgende-dage tælles hver for sig, også når samme person kliker to gange',
  cvBody.totals.visitor_days === 4, String(cvBody.totals.visitor_days));
ok('pr. dag: 3 i dag 0 og 1 to dage tilbage',
  cvBody.by_day[isoDaysAgo(0)] === 3 && cvBody.by_day[isoDaysAgo(2)] === 1
  && cvBody.by_day[isoDaysAgo(1)] === 0, JSON.stringify(cvBody.by_day));
ok('hverken resultater, forsøg, navigation, ventelister eller licenser tælles',
  cvBody.totals.buy_clicks === 4 && !/scan-findings|scan-failed|waitlist|licenses_issued|cta-|ai-cta|store-click/.test(JSON.stringify(cvBody)),
  JSON.stringify(cvBody.by_page));
ok('status er ok, fordi dagen var komplet', cvBody.status === 'ok', cvBody.status);
// Et offentligt svar skal ikke kunne afsløre hvem der købte, hvor meget eller
// med hvilken nøgle. Dommen læser hele svaret, så en ny felt med en adresse eller
// et beløb giver rødt uden at nogen skal vedligeholde en liste.
const cvJson = JSON.stringify(cvBody);
//    En adresse har et `@`, en licensnøgle er 32 hex-tegn, et beløb har et `$`
//    foran et tal — og de tre felter vi aldrig må lægge ud hedder hver især så
//    noget i svaret. Dommen læser hele svaret, så et nyt felt med en adresse
//    eller et beløb giver rødt uden at nogen skal vedligeholde en liste.
ok('svaret rummer hverken adresse, licensnøgle, beløb eller indkomst',
  !cvJson.includes('@') && !/\b[0-9a-f]{32}\b/i.test(cvJson) && !/\$\s?\d/.test(cvJson)
  && !/"(licenses_issued|waitlist|email|revenue|amount|cents|license_key)"\s*:/.test(cvJson),
  cvJson.slice(0, 400));

// 2. En forfalsket `referer` er et emne, enhver kan skrive. Den må hverken tælle
//    som en side eller spejles tilbage i et offentligt svar.
cvKv.set(`p:v3:${isoDaysAgo(0)}:mahope.tools:event:${encodeURIComponent('/hemmeligt/<script>alert(1)</script>@buy-click')}:u-6`, '1');
cvKv.set(`p:v3:${isoDaysAgo(0)}:mahope.tools:event:${encodeURIComponent(`/${'x'.repeat(140)}@buy-click`)}:u-6`, '1');
cvKv.set(`p:v3:${isoDaysAgo(0)}:evil.tld:event:%2Fscan%40buy-click:u-5`, '1');
cvBody = await (await cvCall(`${CV}?days=7`)).json();
ok('en utilladelig sti tælles ikke og spejles ikke, et fremmed domæne heller ikke',
  cvBody.totals.buy_clicks === 4 && cvBody.dropped === 2
  && !/script|alert|xxxx/.test(JSON.stringify(cvBody)), JSON.stringify(cvBody.by_page) + ' dropped=' + cvBody.dropped);

// 3. Sandheden om sin egen fuldstændighed: `null` og `0` er to forskellige
//    påstande, så en dag over nøglegrænsen melder `partial` og tælles ikke.
const cvFlood = isoDaysAgo(0);
cvKv.clear();
for (let i = 0; i < 2001; i += 1) cvSeed('p', 0, '/scan', 'buy-click', `bulk-${i}`);
cvBody = await (await cvCall(`${CV}?days=7`)).json();
ok('en dag over nøglegrænsen melder partial og tælles ikke',
  cvBody.status === 'partial' && cvBody.totals.buy_clicks === 0 && cvBody.by_day[cvFlood] === null,
  cvBody.status + ' buy=' + cvBody.totals.buy_clicks);

// 4. En kvotefejl må aldrig bare se ud som nul.
cvBody = await (await cvCall(`${CV}?days=7`, {}, { ...cvEnv, VISITS: { ...CV_VISITS, list: async () => { throw new Error('kv nede'); } } })).json();
ok('en KV der kaster giver status unknown og nul løfter på tallene',
  cvBody.status === 'unknown' && cvBody.totals.buy_clicks === 0, cvBody.status);
cv = await cvCall(`${CV}?days=7`, {}, { ...cvEnv, VISITS: null });
ok('uden KV-binding svarer ruten 503, ikke 200 med nul', cv.status === 503, cv.status);

// 5. Vinduet er dæmpet og `days` skal være et helt tal over nul.
cvBody = await (await cvCall(`${CV}?days=9999`)).json();
ok('days dæmpes til 28', cvBody.days === 28 && cvBody.window.length === 28, String(cvBody.days));
cvBody = await (await cvCall(`${CV}?days=-4`)).json();
ok('et negativt days falder tilbage til standardvinduet',
  cvBody.days === 7 && cvBody.window.length === 7, String(cvBody.days));

// 6. GET må ikke ændre noget, så POST er 405 — og kvoten pr. IP pr. time holder.
cv = await cvCall(CV, { method: 'POST', body: '{}' });
ok('POST giver 405', cv.status === 405, cv.status);
pinUr.stop();
const cvKv2 = new Map();
const cvEnv2 = { ...cvEnv, VISITS: { ...CV_VISITS, get: async (k) => (cvKv2.has(k) ? cvKv2.get(k) : null), put: async (k, v) => { cvKv2.set(k, v); } } };
const stopTimeCv = (() => {
  const forrige = Date.now;
  const fast = Math.floor(forrige() / 3600000) * 3600000;
  Date.now = () => fast;
  return () => { Date.now = forrige; };
})();
let cv429 = 0, cv200 = 0;
for (let i = 0; i < 32; i += 1) {
  const s = (await cvCall(`${CV}?days=7`, {}, cvEnv2)).status;
  if (s === 429) cv429 += 1; else if (s === 200) cv200 += 1;
}
stopTimeCv();
ok('kvoten pr. IP pr. time stopper læsningerne', cv200 === 30 && cv429 === 2, '200=' + cv200 + ' 429=' + cv429);

// 7. De to lister skal hver især være sig egen. Voksede de sammen, ville et
//    resultat blive læst som et køb — det er præcis den fejl 5/10 undgik ved at
//    holde dem ude af `/api/results`.
const convEvents = (workerSrcRs.match(/const CONVERSION_EVENTS = Object\.freeze\(\[([\s\S]*?)\]\)/) || ['', ''])[1]
  .split(',').map(s => s.trim().replace(/^'|'$/g, '')).filter(Boolean);
ok('konverteringslisten er ikke tom', convEvents.length >= 2, 'n=' + convEvents.length);
for (const event of convEvents) {
  // `pro-card-click` kaldes fra en knap inde i en inline streng, så kaldet er
  // `trackEvent(\'pro-card-click\')` med en backslash foran begge gåseøjne. Et
  // mønster der kræver en ren `(` ville erklære en begivenhed ubrugt, der
  // bliver kaldt hver gang scannerens pro-kort trykkes.
  ok(`«${event}» findes som trackEvent i site/`,
    new RegExp(`trackEvent\\(\\\\?'${event}\\b`).test(siteCode), 'begivenheden kaldes ikke fra nogen side');
}
ok('ingen konverteringsbegivenhed står på resultatlisten, og omvendt',
  !convEvents.some(e => resultEvents.includes(e)) && !resultEvents.some(e => convEvents.includes(e)),
  'resultat=' + resultEvents.join(',') + ' konvertering=' + convEvents.join(','));

// 8. Mutationen: den kode der var her *før* denne ændring kender ikke ruten.
//    Uden denne kontrol er kontrollerne ovenfor grønne af den grund at de ikke
//    kan fejle.
const PRE_CONV_SHA = '97ef0b68';
let preConvWorker = null, preConvNote = '';
try {
  const oldSrcConv = execFileSync('git', ['show', `${PRE_CONV_SHA}:site/_worker.js`],
    { cwd: root, encoding: 'utf8', maxBuffer: 64 * 1024 * 1024, stdio: ['ignore', 'pipe', 'ignore'] });
  ok('mutationen finder den gamle kode (ellers dommer den intet)', !/handleConversion/.test(oldSrcConv));
  const oldTmpConv = join(tmpdir(), `worker-pre-conversion-${process.pid}.mjs`);
  writeFileSync(oldTmpConv, oldSrcConv);
  preConvWorker = (await import(pathToFileURL(oldTmpConv).href)).default;
} catch (e) {
  preConvNote = 'git-historikken er ikke tilgængelig her: ' + (e.code || e.message);
}
if (preConvWorker) {
  cvKv.clear();
  cvSeed('p', 0, '/compliance-report', 'buy-click', 'u-1');
  const oldConv = await preConvWorker.fetch(new Request('https://mahope.tools' + CV), cvEnv, {});
  const oldConvBody = await oldConv.json().catch(() => ({}));
  ok('mutation: den gamle kode svarer 404 og ikke et købstal',
    oldConv.status === 404 && oldConvBody.totals === undefined,
    oldConv.status + ' totals=' + oldConvBody.totals);
} else {
  console.log('NOTE: mutationen mod den gamle kode er sprunget over — ' + preConvNote);
}

console.log(`${pass}/${pass + fail} ok`);
process.exit(fail ? 1 : 0);
