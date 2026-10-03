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
// Det `<title>` der står i markupken — altså den påstand kunden har set indtil
// svidet svar. `render()` lægger den ind i den falske DOM, så dommene nedenfor
// kan se både udgangspunktet og den tekst, siden efterlod.
const STATISK_TITLE = (/<title>([^<]*)<\/title>/.exec(pageHtml) || [null, ''])[1];

// `steps` giver rækken af svar siden modtager i stedet for ét. Det er sådan
// et forbigående svar (503, 429, et kastende netværkskald) kan testes på den
// rigtige side: kunden skal prøve igen, og det skal kunne måles i `fetches`.
// `lang` er `navigator.language` i den falske browser — `da-DK` er den
// danske kunde, `en-US` er alle andre. Det er hele pointen med opgaven:
// Stripe sender dem begge til den *samme* URL.
async function render(payload, steps, lang = 'en-US') {
  const seen = [];
  const els = {
    title: { textContent: '' }, status: { _v: '', className: 'hint' },
    result: { innerHTML: '', hidden: true }, mail: { textContent: '' },
  };
  // Sidesprog: `data-t` (ren tekst) og `data-t-html` (to afsnit med links)
  // læses af siden lige efter indlæsning. Den falske DOM skal derfor kende de
  // attributter, ellers ville sprogdelen være grøn fordi den aldrig blev kørt.
  // Nøglerne læses *af markupken*, så porten ikke kan blive grøn på en nøgle
  // siden ikke bruger — og den kan heller ikke glemme at dømme en.
  const nøgler = [...new Set([...pageHtml.matchAll(/data-t(?:-html|-aria)?="([^"]+)"/g)].map((m) => m[1]))];
  const lav = (nøgle) => {
    const e = {
      nøgle, textContent: '', _aria: null, _html: '',
      get innerHTML() { return this._html; }, set innerHTML(v) { this._html = v; },
      getAttribute: (a) => (a === 'data-t' || a === 'data-t-html' || a === 'data-t-aria' ? nøgle : null),
    };
    e.setAttribute = (a, v) => { e._aria = v; };
    return e;
  };
  // `#status` skal være det *samme* objekt i begge opslag: i en rigtig browser
  // giver `querySelectorAll('[data-t]')` og `getElementById('status')` det
  // samme element, og hvis den falske DOM giver to, ville sprogdelen og
  // fejlene hænge på hver sin — og porten være grøn på en side der aldrig
  // viste den danske statuslinje.
  els.status.nøgle = 'looking';
  els.status.getAttribute = (a) => (a === 'data-t' ? 'looking' : null);
  els.status.setAttribute = () => {};
  const medNøgle = nøgler.map((k) => (k === 'looking' ? els.status : lav(k)));
  const find = (nøgle) => medNøgle.find((e) => e.nøgle === nøgle);
  const ariaNøgle = (/<[^>]*\bdata-t-aria="([^"]+)"/.exec(pageHtml) || [null, null])[1];
  // Hver skrivning til status'en gemmes, så en test kan se hvad kunden så
  // *mens* siden arbejdede. `show()` tømmer teksten igen ved succes, så den
  // endelige tekst alene kan ikke bevise at der stod noget undervejs.
  Object.defineProperty(els.status, 'textContent', {
    get() { return this._v; },
    set(v) { seen.push(String(v)); this._v = String(v); },
  });
  let fetches = 0;
  // Det kunden så *før* serveren svarede. Det er den eneste måde at dømme
  // indlæsningen på: et svar med fejl eller netværksproblem overskriver titlen
  // bagefter, og så ser et rendt resultat ud til at have været dansk hele vejen.
  let første = null;
  const sandbox = {
    console,
    // `document.title` er med, fordi fanebladet er det kunden ser i
    // vindueslisten, i bogmærket og i historikken. Målt 3/10 i Chromium mod den
    // byggede side med et 400-svar: `<h1>` sagde «We could not confirm your
    // order», `<title>` stadig «Thanks for her purchase» — to elementer der
    // var lige ved at glide fra hinanden. Denne test dømmer, at de ikke gør.
    document: {
      title: STATISK_TITLE, documentElement: { lang: 'en' },
      getElementById: (id) => els[id] || null,
      querySelectorAll: (sel) => (sel === '[data-t]' ? medNøgle
        : sel === '[data-t-html]' ? medNøgle : []),
      querySelector: (sel) => (sel === '[data-t-aria]' ? find(ariaNøgle) : null),
    },
    location: { search: '?session_id=cs_live_abcdefghij1234567890' },
    navigator: { language: lang, clipboard: { writeText: () => Promise.resolve() } },
    URLSearchParams,
    setTimeout: (fn) => setTimeout(fn, 0),
    fetch: async (url) => {
      if (!String(url).includes('/api/stripe/fulfillment')) throw new Error('uventet kald: ' + url);
      if (fetches === 0) første = { docTitle: sandbox.document.title, h1: els.title.textContent,
        lang: sandbox.document.documentElement.lang, status: els.status._v };
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
  return { ...els, fetches, thrown, seen, første, docTitle: sandbox.document.title,
    docLang: sandbox.document.documentElement.lang, nøgler, medNøgle,
    // En nøgle siden ikke har, giver et tomt element i stedet for at kaste:
    // porten skal *finde* fejlen på den gamle kode, ikke dø af den.
    find: (k) => find(k) || { nøgle: k, textContent: '', innerHTML: '', _aria: null, mangler: true } };
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
const blandetPayload = { ok: true, product: 'eucomply-dpa', product_name: 'GDPR DPA template', kind: 'download', emailed: true,
  downloads: [{ file: 'dpa-template.pdf', url: 'https://mahope.tools/api/download/' + 'a'.repeat(32) + '/dpa-template.pdf' }],
  downloads_missing: ['dpa-template.md'] };
const blandet = await render(blandetPayload);
ok('delvist manglende: den virkende fil er stadig et link', blandet.result.innerHTML.includes('/api/download/'), blandet.result.innerHTML);
ok('delvist manglende: den manglende fil er nævnt uden adresse',
  blandet.result.innerHTML.includes('dpa-template.md') && !blandet.result.innerHTML.includes('dpa-template.md</a>'), blandet.result.innerHTML);
ok('delvist manglende: siden beder kunden svare på kvitteringen',
  /reply to that email/i.test(blandet.result.innerHTML), blandet.result.innerHTML);

const alleManglerPayload = { ok: true, product: 'eucomply-dpa', product_name: 'GDPR DPA template', kind: 'download', emailed: true,
  downloads: [], downloads_missing: ['dpa-template.pdf', 'dpa-template.md'] };
const alleMangler = await render(alleManglerPayload);
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
const futurePayload = { ok: true, product: 'ny', product_name: 'Nyt produkt', kind: 'seat', emailed: true };
const future = await render(futurePayload);
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

// --------------------------------------------------------------------------
// 3c. Fanebladet skal sige det samme som overskriften. Målt 3/10 i Chromium mod
//     den byggede side med `/api/stripe/fulfillment` svarende 400:
//
//       Faneblad  : Thanks for your purchase | Mahope tools
//       <h1>     : We could not confirm your order
//       status   : We could not find this order.
//
//     `fbbd0a7`s pointe er at en påstand kun må stå når Stripe har bekræftet
//     ordren, og den gør det rigtigt for `<h1>`. Men `<title>` er statisk i
//     `<head>` og blev ikke rørt af noget — og det er præcis det kunden ser i
//     vindueslisten, i bogmærket og i skærmbilledet af fejlen, altså det der
//     bliver liggende hvis kunden taber fanen og kommer tilbage. Samme måling på
//     429 gav sammeMismatch.
// --------------------------------------------------------------------------
ok('udgangspunktet er en påstand om et køb (testens egen forudsætning)',
  /^Thanks for your purchase/.test(STATISK_TITLE), JSON.stringify(STATISK_TITLE));

for (const [label, side] of [['400', ugyldigt], ['404', ukendt], ['429', vedlige429],
  ['202 udløbet', uigjort], ['503 hele vejen', vedlige503]]) {
  ok(`${label}: fanebladet siger at købet ikke er bekræftet, ikke at det er købt`,
    /^We could not confirm your order/.test(side.docTitle) && !/purchase/i.test(side.docTitle),
    JSON.stringify(side.docTitle));
  ok(`${label}: fanebladet og <h1> er det samme`, side.docTitle === side.title.textContent + ' | Mahope tools',
    `title=${JSON.stringify(side.docTitle)} h1=${JSON.stringify(side.title.textContent)}`);
}
for (const [label, side] of Object.entries(rendered)) {
  ok(`${label}: fanebladet følger den bekræftede overskrift, ikke markupkens`,
    side.page.docTitle === side.page.title.textContent + ' | Mahope tools' && side.page.docTitle !== STATISK_TITLE,
    `title=${JSON.stringify(side.page.docTitle)} h1=${JSON.stringify(side.page.title.textContent)}`);
}
// Ratchet på *formen*: kun `titel()` må røre `<title>`, så de to elementer
// ikke kan glide fra hinanden igen ved en ny tekst der skriver h1 direkte. Der
//for tages `titel()`s egen krop ud af scriptet før der søges — ellers ville
// dommen være rød på den rette kode, fordi `titel()` jo netop skriver `#title`.
// Kommentarer fjernes også: de skal kunne *beskrive* feltet uden at tælle som
// en skrivning, og de skal ikke kunne skjule en reel skrivning bag sig.
const titelKrop = /function titel\(t\) \{[\s\S]*?\n {6}\}/.exec(script);
ok('titel() findes og sætter begge steder',
  !!titelKrop && /document\.title = t/.test(titelKrop[0]) && /getElementById\('title'\)\.textContent/.test(titelKrop[0]),
  JSON.stringify(titelKrop && titelKrop[0].slice(0, 120)));
const kode = script.replace(/\/\/[^\n]*/g, '');
const udenTitrel = kode.replace(titelKrop ? titelKrop[0] : 'function titel', '');
ok('kun titel() sætter h1 og faneblad — ingen anden sted i scriptet',
  !/getElementById\('title'\)/.test(udenTitrel) && !/document\.title/.test(udenTitrel),
  JSON.stringify((udenTitrel.match(/.{0,60}(getElementById\('title'\)|document\.title).{0,40}/) || [''])[0]));

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

// --------------------------------------------------------------------------
// 5. Sprog. Målt 3/10: `/thanks` var `lang="en"` med nul sprogdetektering, og
//    `/da/thanks` er 404. Stripe sender *alle* kunder til samme URL lige efter
//    betalingen, og `success_url` kan ikke ændres — så hele familien er dansk,
//    og det er den ene side en dansk kunde ser i købsøjeblikket. Den skal derfor
//    kunne tale dansk på sin egen adresse.
//
//    Porten dømmer fire ting, og de fire er valgt, fordi hver især kan være
//    grøn mens de tre andre er røde:
//      a. de to sprog har præcis samme nøgler (en manglende nøgle ville vise
//         kunden `undefined` — det er den fejl der ikke klager),
//      b. hver af de fire strenge opgaven navngiver findes på begge sprog,
//      c. den danske side renderer *hele* købsvejen — nøglekasse, kvittering,
//         downloads, donation — ikke kun overskriften,
//      d. de statiske nøgler fra markupken (`data-t`) er oversat, og `<html
//         lang>` følger med.
// --------------------------------------------------------------------------
const tabel = /var STRINGS = \{\n([\s\S]*?)\n {6}\};\n/.exec(script);
ok('siden har en STRINGS-tabel med begge sprog', !!tabel && /\ben: \{/.test(tabel[1]) && /\n {8}da: \{/.test(tabel[1]));
const sprogNøgler = (blok) => [...new Set([...blok.matchAll(/^\s{10}(\w+):/gm)].map((m) => m[1]))].sort();
const enBlok = /\ben: \{([\s\S]*?)\n {8}\},\n/.exec(tabel ? tabel[1] : '');
const daBlok = /\n {8}da: \{([\s\S]*?)\n {8}\}/.exec(tabel ? tabel[1] : '');
const nøgleEn = enBlok ? sprogNøgler(enBlok[1]) : [];
const nøgleDa = daBlok ? sprogNøgler(daBlok[1]) : [];
ok('begge sprog har de samme nøgler', nøgleEn.length > 30 && nøgleEn.join(',') === nøgleDa.join(','),
  `en=${nøgleEn.length} da=${nøgleDa.length} kun-en=${nøgleEn.filter((k) => !nøgleDa.includes(k)).join(',')} kun-da=${nøgleDa.filter((k) => !nøgleEn.includes(k)).join(',')}`);

// (b) De fire opgaven peger på, hver som et helt sætning der kun kan findes
// i tabellen — ikke som et nøglenavn, for det ville være grønt på en tabel der
// indeholder nøglen men en tom streng.
for (const [nøgle, mønster] of [
  ['notConfirmed', /^Vi kunne ikke bekræfte din ordre$/m],
  ['noRef', /^Der står ingen ordrereference i linket\./m],
  ['ranOut', /^Vi kunne ikke hente din ordre lige nu, men din betaling er gået igennem\./m],
  ['pendingOut', /^Din betaling er endnu ikke bekræftet/],
  ['keyHead', /^Din licensnøgle$/m],
  ['mailSent', /^Vi har også sendt det til dig\./m],
]) {
  const værdi = daBlok && new RegExp(`^\\s{10}${nøgle}: '([^']*)'`, 'm').exec(daBlok[1]);
  const rå = daBlok ? new RegExp(`^\\s{10}${nøgle}:([\\s\\S]*?)(?=^\\s{10}\\w+:|\\Z)`, 'm').exec(daBlok[1]) : null;
  const samlet = (værdi ? værdi[1] : rå ? rå[1] : '');
  ok(`dansk "${nøgle}" findes og siger det den skal`, mønster.test(samlet.replace(/\\?\s*\+\s*/g, ' ').replace(/^'|'$/g, '')),
    JSON.stringify(samlet.slice(0, 110)));
}

// (d) Sprogvalget. `navigator.language` er kilden; `?lang=` er kun en
// håndgreb, og den må aldrig finde en sprogstreng uden for tabellen — den læses
// som nøgle, så en kunde der sender `?lang=<script>` får engelsk, ikke markup.
const dansk = await render(lic.payload, null, 'da-DK');
const engelsk = await render(lic.payload, null, 'en-US');
ok('dansk browser får dansk sidesprog', dansk.docLang === 'da' && engelsk.docLang === 'en',
  `da=${dansk.docLang} en=${engelsk.docLang}`);
ok('dansk browser får dansk h1 og kvitteringstekst',
  dansk.title.textContent === 'Tak for dit køb af EUComply Pro!' && /Din licensnøgle/.test(dansk.result.innerHTML),
  `h1=${JSON.stringify(dansk.title.textContent)} html=${JSON.stringify(dansk.result.innerHTML.slice(0, 90))}`);
// Ratchet på *indlæsningen*: h1 og faneblad skal være danske **før** serveren
// svarer. Målt 3/10 i Chromium — `sprogMarkup()` oversatte alt andet, men
// skrev h1/title gennem en linje der ikke fandtes, så den danske kunde læste
// «Thanks for her purchase!» i vindueslisten over et dansk kort.
{
  const s = await render(null, [{ throw: true }], 'da-DK');
  ok('dansk h1 og faneblad er danske fra første maling',
    s.første.h1 === 'Tak for dit køb!' && s.første.docTitle === 'Tak for dit køb! | Mahope tools'
    && s.første.lang === 'da' && s.første.status === 'Vi finder din ordre…',
    JSON.stringify(s.første));
  const e = await render(null, [{ throw: true }], 'en-US');
  ok('engelsk h1 og faneblad er stadig engelske',
    e.første.h1 === 'Thanks for your purchase!' && e.første.docTitle === 'Thanks for your purchase! | Mahope tools'
    && e.første.status === 'Looking up your order…', JSON.stringify(e.første));
  ok('sproghåndgrebet kan ikke finde en sprogstreng uden for tabellen',
    (await render(null, [{ status: 400, body: { error: 'x' } }], 'xx-YY')).docLang === 'en',
    'navigator.language=xx-YY');
}
ok('engelsk browser får engelsk h1 og kvitteringstekst',
  engelsk.title.textContent === 'Thanks for buying EUComply Pro!' && /Your license key/.test(engelsk.result.innerHTML),
  `h1=${JSON.stringify(engelsk.title.textContent)}`);
// Negativ kontrol: de to sprog må ikke vise den samme tekst. Uden denne dom
// kunne `sprog()` være grøn fordi den altid returnerer 'en'.
ok('de to sprog er to forskellige sider, ikke én',
  dansk.title.textContent !== engelsk.title.textContent
  && dansk.result.innerHTML !== engelsk.result.innerHTML
  && dansk.docTitle !== engelsk.docTitle);

// Ratchet: hver `data-t`-nøgle i markupken skal stå i *begge* sprog, ellers
// får den danske kunde den engelske sætning lige under sin egen.
for (const nøgle of dansk.nøgler) {
  // `looking` dømmes et andet sted: `show()` tømmer statuslinjen med vilje, når
  // kortet kommer, så dens *endelige* tekst er tom for et gennemført køb. Den
  // er dømt i «dansk h1 og faneblad er danske fra første maling» i stedet.
  if (nøgle === 'looking') continue;
  const stæt = dansk.find(nøgle);
  const rigtig = nøgleEn.includes(nøgle);
  ok(`statisk nøgle "${nøgle}" er oversat`, rigtig && stæt && stæt.textContent.length > 0
    && stæt.textContent !== (engelsk.find(nøgle) || {}).textContent,
    `da=${JSON.stringify(stæt && stæt.textContent)} nøgle-i-en=${rigtig}`);
}
// `next`-afsnittet og nav-mærkaten er de to steder med markup/attribut, så de
// dømmes på den værdi de får — ikke på `textContent`.
const nextDa = dansk.find('next'), nextEn = engelsk.find('next');
ok('dansk «next»-afsnit har links og dansk tekst',
  /<a href="\/page-profile">/.test(nextDa.innerHTML) && /<a href="\/free-tools">de gratis værktøjer<\/a>/.test(nextDa.innerHTML)
  && !/stay free without a key/.test(nextDa.innerHTML), JSON.stringify(nextDa.innerHTML.slice(0, 140)));
ok('engelsk «next»-afsnit er stadig det engelske afsnit',
  /the free tools<\/a> stay free without a key/.test(nextEn.innerHTML), JSON.stringify(nextEn.innerHTML.slice(0, 140)));
ok('nav-mærkaten er oversat', dansk.find('navLabel')._aria === 'Fortsæt' && engelsk.find('navLabel')._aria === 'Continue',
  JSON.stringify([dansk.find('navLabel')._aria, engelsk.find('navLabel')._aria]));

// (c) Hele købsvejen på dansk — de grene der ikke kører i licens-grenen.
for (const [label, payload, skal] of [
  ['download', dl.payload, /<strong>Dine filer<\/strong> \(links virker i 60 dage\)/],
  ['donation', don.payload, /Tak — der er intet at aktivere\./],
  ['delvist manglende', blandetPayload, /af dine filer er ikke tilgængelige at hente lige nu/],
  ['intet hentbart', alleManglerPayload, /Dine filer er endnu ikke tilgængelige at hente\./],
  ['ukendt kind', futurePayload, /Vi kunne ikke læse din ordre\./],
  ['lifetime', life.payload, /Livstidslicens:<\/strong> én betaling, ingen fornyelse og intet udløb/],
  ['abonnement', lic.payload, /Administrér dit abonnement/],
  ['engangskøb', engang.payload, /Virker på op til 3 enhed\(er\), udløber aldrig\./],
]) {
  const s = await render(payload, null, 'da-DK');
  ok(`dansk ${label}: kortet er på dansk`, s.thrown === null && skal.test(s.result.innerHTML),
    `thrown=${s.thrown && s.thrown.message} html=${JSON.stringify(s.result.innerHTML.slice(0, 120))}`);
  ok(`dansk ${label}: ingen engelsk sætning tilbage i kortet`,
    !/Your license key|Your downloads|nothing to activate|We could not read your order|device\(s\)|Manage your subscription|Lifetime license/.test(s.result.innerHTML),
    JSON.stringify(s.result.innerHTML.slice(0, 160)));
  ok(`dansk ${label}: kvitteringsmailen følger emailed=${payload.emailed}`,
    payload.kind === 'donation'
      ? /Stripe har sendt kvitteringen/.test(s.mail.textContent)
      : (/Vi har også sendt det/.test(s.mail.textContent) === (payload.emailed === true)),
    JSON.stringify(s.mail.textContent.slice(0, 80)));
}

// De danske fejlveje skal også være danske — en dansk kunde der rammer 503
// hele vejen skal ikke læse «Vi har svært ved at hente din ordre».
const da503 = await render(null, [{ status: 503, body: body503 }], 'da-DK');
ok('dansk 503 hele vejen: slutningen er dansk', /din betaling er gået igennem/.test(da503.status.textContent)
  && !/payment went through/.test(da503.status.textContent), da503.status.textContent);
ok('dansk 503 hele vejen: overskriften er dansk', /Vi kunne ikke bekræfte din ordre/.test(da503.docTitle), da503.docTitle);
const da429 = await render(null, [{ status: 429, body: body429 }], 'da-DK');
ok('dansk 429: serverens egen sætning står først, og genkaldes ikke',
  da429.fetches === 1 && da429.status.textContent.startsWith(body429.error), JSON.stringify(da429.status.textContent.slice(0, 80)));
ok('dansk 429: den danske beroligelse følger med', /Grænsen nulstilles/.test(da429.status.textContent), da429.status.textContent);
const da202 = await render(null, [{ status: 202, body: { ok: false, pending: true } }], 'da-DK');
ok('dansk 202: gentages stadig, og siger at betalingen bekræftes',
  da202.fetches === 13 && /Vi bekræfter din betaling/.test(da202.seen.join(' ')), 'fetches=' + da202.fetches);
ok('dansk 202 udløbet: siger «ikke bekræftet endnu», ikke «betalingen gik igennem»',
  /^Din betaling er endnu ikke bekræftet/.test(da202.status.textContent) && !/din betaling er gået igennem/i.test(da202.status.textContent),
  da202.status.textContent);
// En dansk kunde uden ordrereference må få den danske tekst, ikke den engelske.
{
  const s = await render(null, [{ status: 400, body: { ok: false, error: 'Invalid session.' } }], 'da-DK');
  ok('dansk 400: h1 og faneblad er danske',
    /Vi kunne ikke bekræfte din ordre/.test(s.title.textContent) && /Vi kunne ikke bekræfte din ordre/.test(s.docTitle),
    `h1=${JSON.stringify(s.title.textContent)} title=${JSON.stringify(s.docTitle)}`);
}

// Ratchet på escape-reglen: alt der kommer fra serveren skal gå gennem
// `esc()`, på begge sprog. En dansk streng i `innerHTML` er ikke i sig selv
// farlig — de er vores egne — men det er *interpolationerne* der er det, så
// dommen tæller `T.` inde i en `esc(...)`-kontekst.
const escKontekster = [...script.matchAll(/esc\(([^()]*(?:\([^()]*\)[^()]*)*)\)/g)].map((m) => m[1]);
ok('hvert serverfelt der sættes i markupket går gennem esc()',
  escKontekster.some((k) => /license_key/.test(k)) && escKontekster.some((k) => /max_devices/.test(k))
  && escKontekster.some((k) => /f\.url/.test(k)) && escKontekster.some((k) => /f\.file/.test(k))
  && escKontekster.some((k) => /missing\.join/.test(k)) && escKontekster.some((k) => /billing_portal/.test(k))
  && escKontekster.some((k) => /activate_url/.test(k)) && escKontekster.some((k) => /activate_hint/.test(k)),
  JSON.stringify(escKontekster.filter((k) => /license_key|max_devices|f\.|missing|billing_portal|activate/.test(k))));
ok('ingen rå serverstreng i en dansk tekstblok',
  !/[^.]esc\(d\.(license_key|max_devices|activate_hint)\)/.test(daBlok ? daBlok[1] : ''));

console.log(`${pass}/${pass + fail} ok`);
process.exit(fail ? 1 : 0);
