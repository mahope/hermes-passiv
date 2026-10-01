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
  // Lifetime (founding-pris): engangspris på abonnementsproduktet, 2 websites.
  cs_live_thankslifeFFFFFFFF: { status: 'complete', payment_status: 'paid', subscription: null, mode: 'payment',
    customer_details: { email: 'l@f.dk' }, line_items: { data: [{ quantity: 2, price: { lookup_key: 'eucomply-pro-lifetime-v1' } }] } },
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

// `steps` giver rækken af svar siden modtager i stedet for ét. Det er sådan
// et forbigående svar (503, 429, et kastende netværkskald) kan testes på den
// rigtige side: kunden skal prøve igen, og det skal kunne måles i `fetches`.
async function render(payload, steps) {
  const seen = [];
  const els = {
    title: { textContent: '' }, status: { _v: '', className: 'hint' },
    result: { innerHTML: '', hidden: true }, mail: { textContent: '' },
  };
  // Hver skrivning til status'en gemmes, så en test kan se hvad kunden så
  // *mens* siden arbejdede. `show()` tømmer teksten igen ved succes, så den
  // endelige tekst alene kan ikke bevise at der stod noget undervejs.
  Object.defineProperty(els.status, 'textContent', {
    get() { return this._v; },
    set(v) { seen.push(String(v)); this._v = String(v); },
  });
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
      const i = fetches++;
      const step = steps ? steps[Math.min(i, steps.length - 1)] : { status: 200, body: payload };
      if (step.throw) throw new Error('netværksfejl');
      return { status: step.status, json: async () => step.body };
    },
  };
  vm.createContext(sandbox);
  let thrown = null;
  try { vm.runInContext(script, sandbox); } catch (e) { thrown = e; }
  // `.catch` i poll() fanger en TypeError og genkalder — lad de gentagelser ske,
  // ellers ville porten være grøn på den præcis fejl den er skrevet til at fange.
  // 40 runder: det er nok til et helt retry-budget (12 kald gennem to led) og
  // koster stadig under 200 ms.
  for (let i = 0; i < 40; i++) await new Promise((r) => setTimeout(r, 4));
  return { ...els, fetches, thrown, seen };
}

// --------------------------------------------------------------------------
// 3. Hver kind i STRIPE_PRODUCTS skal kunne renderes på den rigtige side.
//    Kilderne er de ægte leveringssvar, så payload'en kan ikke aftales med
//    siden ved en fejl. Download-filen lægges i KV først, så dette er den
//    fuldt leverede købsvej; den delvist manglende udgave står længere nede med
//    sit eget håndlavede svar.
// --------------------------------------------------------------------------
kv.set('paidfile:dpa-template.pdf', '%PDF-dpa');
kv.set('paidfile:dpa-template.md', '# DPA');
const cases = [
  ['license (engangskøb)', 'cs_live_thankslicAAAAAAAA'],
  ['license (abonnement, 2 enheder)', 'cs_live_thankssubBBBBBBBB'],
  ['download', 'cs_live_thanksdlCCCCCCCCC'],
  ['donation', 'cs_live_thanksdonDDDDDDDD'],
  ['license (kunden gav ingen mailadresse)', 'cs_live_thanksnoemailEEEEEE'],
  ['license (lifetime, 2 websites)', 'cs_live_thankslifeFFFFFFFF'],
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
// Engangskøb: de tre felter `/thanks` skriver lige i DOM'en — `max_devices`,
// `expires_at` og `billing_portal` — var korrekt afledt, men ingen port dømte
// dem, så de kunne stå på hver især (samme stilling som `product_name` før
// `receipt-ord`). Her låses både **afledningen** i workeren og den **visning**
// på siden: en abonnementssætning på et engangsprodukt er den konkrete
// fejlform, så den skal kunne dø begge steder.
const engang = rendered['license (engangskøb)'];
ok('engangskøb: workeren sender hverken udløbsdato eller kundeportal',
  engang.payload.expires_at == null && engang.payload.billing_portal === undefined,
  JSON.stringify({ expires_at: engang.payload.expires_at, billing_portal: engang.payload.billing_portal }));
ok('engangskøb: siden siger "no expiry"', /no expiry/.test(engang.page.result.innerHTML), engang.page.result.innerHTML);
ok('engangskøb: siden siger ikke "renews"', !/renews/i.test(engang.page.result.innerHTML), engang.page.result.innerHTML);
ok('engangskøb: ingen kundeportal på siden', !/Manage your subscription/.test(engang.page.result.innerHTML), engang.page.result.innerHTML);
ok('engangskøb: enhedstallet vises stadig', /Works on up to 3 device\(s\)/.test(engang.page.result.innerHTML), engang.page.result.innerHTML);
ok('abonnement: workeren sender både udløbsdato og kundeportal',
  !!lic.payload.expires_at && !!lic.payload.billing_portal, JSON.stringify(lic.payload.expires_at));
ok('abonnement: siden siger fornyelse, ikke "no expiry"',
  /renews with your subscription/.test(lic.page.result.innerHTML) && !/no expiry/.test(lic.page.result.innerHTML), lic.page.result.innerHTML);

// Lifetime: samme licensgren, men siden skal sige "Lifetime" og hverken
// fornyelse eller kundeportal — der er intet abonnement at opsige.
const life = rendered['license (lifetime, 2 websites)'];
ok('lifetime: workeren sender lifetime uden udløb og uden kundeportal',
  life.payload.lifetime === true && life.payload.expires_at == null && life.payload.billing_portal === undefined && life.payload.subscription === undefined,
  JSON.stringify(life.payload));
ok('lifetime: overskriften siger Lifetime', /Thanks for buying EUComply Pro Lifetime!/.test(life.page.title.textContent), life.page.title.textContent);
ok('lifetime: kortet siger lifetime og no expiry', /Lifetime license:<\/strong> one payment, no renewal and no expiry/.test(life.page.result.innerHTML), life.page.result.innerHTML);
ok('lifetime: siden siger ikke "renews"', !/renews/i.test(life.page.result.innerHTML), life.page.result.innerHTML);
ok('lifetime: ingen kundeportal', !/Manage your subscription/.test(life.page.result.innerHTML), life.page.result.innerHTML);
ok('lifetime: antal websites følger antal købt', /Works on up to 2 device\(s\)/.test(life.page.result.innerHTML), life.page.result.innerHTML);

const dl = rendered['download'];
ok('download: filnavn vises', dl.page.result.innerHTML.includes('dpa-template.pdf'), dl.page.result.innerHTML);
ok('download: linket er workerens /api/download-adresse', dl.page.result.innerHTML.includes(dl.payload.downloads[0].url));

// En fil kunden har betalt for, men som ikke kan hentes, må ikke blive et link.
// `/api/download` svarer 503 på den, så et link ville være et dødt løfte.
const blandet = await render({ ok: true, product: 'eucomply-dpa', product_name: 'GDPR DPA template', kind: 'download', emailed: true,
  downloads: [{ file: 'dpa-template.pdf', url: 'https://mahope.tools/api/download/' + 'a'.repeat(32) + '/dpa-template.pdf' }],
  downloads_missing: ['dpa-template.md'] });
ok('delvist manglende: den virkende fil er stadig et link', blandet.result.innerHTML.includes('/api/download/'), blandet.result.innerHTML);
ok('delvist manglende: den manglende fil er nævnt uden adresse',
  blandet.result.innerHTML.includes('dpa-template.md') && !blandet.result.innerHTML.includes('dpa-template.md</a>'), blandet.result.innerHTML);
ok('delvist manglende: siden beder kunden svare på kvitteringen',
  /reply to that email/i.test(blandet.result.innerHTML), blandet.result.innerHTML);

const alleMangler = await render({ ok: true, product: 'eucomply-dpa', product_name: 'GDPR DPA template', kind: 'download', emailed: true,
  downloads: [], downloads_missing: ['dpa-template.pdf', 'dpa-template.md'] });
ok('intet hentbart: ingen downloadlinks overhovedet', !/\/api\/download\//.test(alleMangler.result.innerHTML), alleMangler.result.innerHTML);
ok('intet hentbart: siger det rent ud, uden en tom "Your downloads"-liste',
  /not available for download yet/i.test(alleMangler.result.innerHTML) && !/Your downloads/.test(alleMangler.result.innerHTML), alleMangler.result.innerHTML);
ok('intet hentbart: kvitteringsmailen er nævnt som bevis på betalingen',
  /record of it/i.test(alleMangler.result.innerHTML), alleMangler.result.innerHTML);
ok('intet hentbart: begge filer nævnes ved navn',
  alleMangler.result.innerHTML.includes('dpa-template.pdf') && alleMangler.result.innerHTML.includes('dpa-template.md'), alleMangler.result.innerHTML);
ok('en manglende fil sender ingen mail-påstand om at alt er gemt',
  !/save what is on this page/i.test(alleMangler.mail.textContent) || alleMangler.payload.emailed === true, alleMangler.mail.textContent);

const kunReady = await render({ ok: true, product: 'eucomply-dpa', product_name: 'GDPR DPA template', kind: 'download', emailed: true,
  downloads: [{ file: 'dpa-template.pdf', url: 'https://mahope.tools/api/download/' + 'a'.repeat(32) + '/dpa-template.pdf' }] });
ok('fuldt hentbart køb siger intet om manglende filer',
  !/not available/i.test(kunReady.result.innerHTML), kunReady.result.innerHTML);

const don = rendered['donation'];
ok('donation: ingen licensnøgle-kasse', !/key-box/.test(don.page.result.innerHTML), don.page.result.innerHTML);
ok('donation: ingen downloadliste', !/<li>/.test(don.page.result.innerHTML), don.page.result.innerHTML);
ok('donation: siger tak uden at kræve aktivering', /nothing to activate/i.test(don.page.result.innerHTML), don.page.result.innerHTML);
ok('donation: påstår ikke at vi har sendt mail', !/have also emailed/i.test(don.page.mail.textContent), don.page.mail.textContent);

// Målt 27/9: overskriften skrev "Thanks for buying Support for Mahope open
// source" til en donator, mens kortet under sagde "there is nothing to
// activate". Pengene blev *givet*, så det er en påstand kunden kan se er
// falsh. Negativ kontrol på de to andre `kind`: de er køb, så de SKAL stadig
// siges købt — ellers er hilsenen blot en global erstatning.
ok('donation: overskriften siger tak for støtte, ikke at den er købt',
  /^Thank you for supporting /.test(don.page.title.textContent) && !/buying/i.test(don.page.title.textContent),
  JSON.stringify(don.page.title.textContent));
for (const [label, must] of [['license (engangskøb)', /Thanks for buying DeskUptime Pro!/],
  ['license (abonnement, 2 enheder)', /Thanks for buying EUComply Pro!/],
  ['download', /Thanks for buying GDPR DPA template!/]]) {
  ok(`${label}: overskriften siger stadig at varen er købt`,
    must.test(rendered[label].page.title.textContent), JSON.stringify(rendered[label].page.title.textContent));
}
ok('donation: hilsenen er afledt af kind, ikke en standardsætning',
  /d\.kind === 'donation'/.test(script) && !/title'\)\.textContent = 'Thanks for buying/.test(script));

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
// 3b. En betaling der lige er gennemført må aldrig ende i en permanent
//     fejlside. Målt 29/9: `202` blev gentaget op til 12 gange, men `503` og
//     `429` gav op med det samme — så ét KV-blip kunne efterlade en kunde, der
//     netop havde betalt for EUComply Pro, med "Service temporarily
//     unavailable." og ingen vej videre. Svarene her er de *ægte* fra
//     workeren: 503 fordi env mangler `STRIPE_SECRET_KEY`, 429 fordi
//     timegrænsen virkelig er kørt op på et eget KV.
// --------------------------------------------------------------------------
const subSid = 'cs_live_thankssubBBBBBBBB';
const res503 = await worker.fetch(new Request('https://mahope.tools/api/stripe/fulfillment?session_id=' + subSid), { VISITS, RESEND_API_KEY: 're_x' }, {});
const body503 = await res503.json();
ok('workeren svarer ægte 503 når STRIPE_SECRET_KEY mangler',
  res503.status === 503 && body503.error === 'Service temporarily unavailable.', res503.status + ' ' + JSON.stringify(body503));

// Eget KV, så timegrænsetælleren ikke rammer de andre kald i denne fil.
const kv429 = new Map();
const env429 = { VISITS: { get: async (k) => (kv429.has(k) ? kv429.get(k) : null), put: async (k, v) => { kv429.set(k, v); } }, STRIPE_SECRET_KEY: 'sk_test_x' };
let res429 = null;
for (let i = 0; i < 31; i++) res429 = await worker.fetch(new Request('https://mahope.tools/api/stripe/fulfillment?session_id=' + subSid), env429, {});
const body429 = await res429.json();
ok('workeren svarer ægte 429 når timegrænsen er nået', res429.status === 429, res429.status + ' ' + JSON.stringify(body429));

// Den gamle 202-sti skal stadig fungere, og med sit eget budget. Den kan ikke
// hentes fra workeren her — den falske Stripe har ingen session der står
// "unpaid", så den svarer 404 — men siden skal behandle 202 præcis som før.
const uigjort = await render(null, [{ status: 202, body: { ok: false, pending: true } }]);
ok('202: gentages stadig, og siger at betalingen bekræftes', uigjort.fetches === 13 && /Confirming your payment/i.test(uigjort.seen.join(' ')), 'fetches=' + uigjort.fetches + ' seen=' + JSON.stringify(uigjort.seen.slice(0, 2)));
ok('202: når budgettet er brugt, siger siden at betalingen endnu ikke er bekræftet',
  /not confirmed yet/i.test(uigjort.status.textContent) && !/payment went through/i.test(uigjort.status.textContent), uigjort.status.textContent);
// 202 betyder "Stripe har endnu ikke bekræftet", så at slutte på "your payment
// went through" er en påstand vi ikke kan dokumentere — den er modsatte af
// det vi ved. Det er målt på den gamle kode: samme streng for 202 og for 503.
ok('202: den lyder ikke som de 503/429-grene gør', /not confirmed yet/i.test(uigjort.status.textContent), uigjort.status.textContent);

const helbredt503 = await render(null, [{ status: 503, body: body503 }, { status: 503, body: body503 }, { status: 200, body: lic.payload }]);
ok('503 der går over: siden viser nøglen alligevel', helbredt503.thrown === null && /<code id="key">[0-9a-f]{32}<\/code>/.test(helbredt503.result.innerHTML),
  `thrown=${helbredt503.thrown && helbredt503.thrown.message} html=${JSON.stringify(helbredt503.result.innerHTML.slice(0, 80))}`);
ok('503 der går over: den prøver igen frem for at give op', helbredt503.fetches === 3, 'fetches=' + helbredt503.fetches);
ok('503 der går over: kunden ser at siden arbejder på det', helbredt503.seen.some((t) => /trying again/i.test(t)), JSON.stringify(helbredt503.seen));

// Et 429 er **endeligt**, så denne test dømmer modsat af 503: serveren siger
// «for mange forsøg» og næste kald ville have svaret 200 med nøglen — men det
// kald tæller i den samme tæller, der lige har sagt stop. Målt 1/10 på den
// gamle kode: tolv genkald á fire sekunder, og den der ventede længst fik
// *færrest* forsøg tilbage. Så her venter vi ikke på det andet svar; vi
// fortæller kunden at et reload virker, og viser ingen nøgle vi ikke har læst.
const helbredt429 = await render(null, [{ status: 429, body: body429 }, { status: 200, body: lic.payload }]);
ok('429: ingen nyt kald ind i den tæller der sagde stop', helbredt429.fetches === 1, 'fetches=' + helbredt429.fetches);
ok('429: serverens egen sætning står i stedet for vores egen',
  // Uden denne dom er `startsWith` under den næste vacuous: en tom `error`
  // ville være præfiks for alt. Så den skal først findes.
  typeof body429.error === 'string' && body429.error.length > 0
  && helbredt429.status.textContent.startsWith(body429.error), JSON.stringify(body429) + ' | ' + helbredt429.status.textContent);
ok('429: kunden får at vide at et reload virker', /reload will work/i.test(helbredt429.status.textContent), helbredt429.status.textContent);
ok('429: ingen nøgle der ligner en levering, men som vi ikke har læst',
  helbredt429.result.hidden === true, JSON.stringify(helbredt429.result.innerHTML.slice(0, 80)));

const netvaerk = await render(null, [{ throw: true }, { throw: true }, { status: 200, body: lic.payload }]);
ok('netværksfejl der går over: siden viser nøglen', netvaerk.fetches === 3 && /<code id="key">[0-9a-f]{32}<\/code>/.test(netvaerk.result.innerHTML), 'fetches=' + netvaerk.fetches);

// Det alvorlige tilfælde: serveren svarer 503 hele vejen. Siden må ikke sige
// "ordren findes ikke", og den må ikke blive ved i det uendelige.
const vedlige503 = await render(null, [{ status: 503, body: body503 }]);
ok('503 hele vejen: siden siger at betalingen gennemførte, ikke at ordren mangler',
  /payment went through/i.test(vedlige503.status.textContent) && !/could not find this order/i.test(vedlige503.status.textContent), vedlige503.status.textContent);
ok('503 hele vejen: kunden får et rådt service-svar, ikke vores interne tekst', !/temporarily unavailable/i.test(vedlige503.status.textContent), vedlige503.status.textContent);
ok('503 hele vejen: kvitteringen nævnes som bevis på betalingen', /receipt/i.test(vedlige503.status.textContent), vedlige503.status.textContent);
ok('503 hele vejen: gentagelserne er begrænset af et budget, ikke uendelige',
  vedlige503.fetches === 13, 'fetches=' + vedlige503.fetches);
ok('503 hele vejen: ingen licence-kasse der ligner en levering', vedlige503.result.hidden === true, JSON.stringify(vedlige503.result.innerHTML.slice(0, 80)));

const vedlige429 = await render(null, [{ status: 429, body: body429 }]);
ok('429 hele vejen: samme ærlige slutning som ved 503', /payment went through/i.test(vedlige429.status.textContent), vedlige429.status.textContent);
ok('429 hele vejen: den siger ikke at ordren mangler', !/could not find this order/i.test(vedlige429.status.textContent), vedlige429.status.textContent);
// Ratcheten mod den selvforstærkende løkke fra opgave 35. Den gamle kode
// svarede 13 gange på 13 ens 429 — ét kald mere end budgettet på 5xx, fordi
// 429 lå i samme gren. Det er præcis den egenskab der lå i live.
ok('429 hele vejen: ét kald, ikke tretten', vedlige429.fetches === 1, 'fetches=' + vedlige429.fetches);
ok('429 hele vejen: ingen licenskasse der ligner en levering', vedlige429.result.hidden === true, JSON.stringify(vedlige429.result.innerHTML.slice(0, 80)));

// Negativ kontrol: 404 *er* et reelt svar — ordren findes ikke. Det må dømmes
// med det samme, ellers ville rettelsen have gjort alle fejl forbigående.
const res404 = await call('/api/stripe/fulfillment?session_id=cs_live_findesikke12345678');
const body404 = await res404.json();
ok('workeren svarer 404 på en session der ikke findes', res404.status === 404 && body404.error === 'Order not found.', res404.status + ' ' + JSON.stringify(body404));
const ukendt = await render(null, [{ status: 404, body: body404 }]);
ok('404: dømmes med det samme, ikke gentaget i en storm', ukendt.fetches === 1, 'fetches=' + ukendt.fetches);
// Sidens egen tekst er en *reserveret* nødtekst; her kommer den fra workerens
// `error`, som er den ærlige. Det der dømmes er at den hverken er tom eller
// lyder som om betalingen gennemførte.
ok('404: siden siger at ordren ikke blev fundet, og påstår ikke at betalingen lykkedes',
  /order not found/i.test(ukendt.status.textContent) && !/payment went through/i.test(ukendt.status.textContent), ukendt.status.textContent);

// 400 (ugyldigt sessions-id) er også terminalt. Det fanges af regexen på
// siden, så workeren nås aldrig — låst her så det bliver ved med at være sådan.
const ugyldigt = await render(null, [{ status: 400, body: { ok: false, error: 'Invalid session.' } }]);
ok('400: heller ikke gentaget', ugyldigt.fetches === 1, 'fetches=' + ugyldigt.fetches);

// Den gamle 202-sti skal stadig fungere, og med sit eget budget.

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
