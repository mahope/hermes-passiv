import { copyFileSync, existsSync, readFileSync, readdirSync, unlinkSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const src = process.argv[2] || fileURLToPath(new URL('../site/_worker.js', import.meta.url));
const tmp = join(tmpdir(), `tracking-worker-${process.pid}-${Date.now()}.mjs`);
copyFileSync(src, tmp);
const worker = (await import(pathToFileURL(tmp).href)).default;
unlinkSync(tmp);

class MemoryKV {
  constructor(pageSize = 2) {
    this.values = new Map();
    this.pageSize = pageSize;
  }

  async get(key) {
    return this.values.has(key) ? this.values.get(key) : null;
  }

  async put(key, value) {
    this.values.set(key, String(value));
  }

  async delete(key) {
    this.values.delete(key);
  }

  async list({ prefix = '', cursor = '' } = {}) {
    const keys = [...this.values.keys()].filter(key => key.startsWith(prefix)).sort();
    const start = Number(cursor || 0);
    const end = Math.min(start + this.pageSize, keys.length);
    return {
      keys: keys.slice(start, end).map(name => ({ name })),
      list_complete: end >= keys.length,
      cursor: end < keys.length ? String(end) : '',
    };
  }
}

function makeEnv() {
  const VISITS = new MemoryKV();
  return {
    VISITS,
    ASSETS: { fetch: async request => new URL(request.url).pathname.startsWith('/downloads/') ? new Response('asset') : new Response('Not found', { status: 404 }) },
  };
}

let pass = 0;
let fail = 0;
const ok = (name, condition, detail = '') => {
  if (condition) pass++;
  else {
    fail++;
    console.log('FEJL:', name, detail);
  }
};

const chromeUA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/140.0 Safari/537.36';
const domains = ['cleancopy.tools', 'deskuptime.com', 'bugbottle.dev', 'mahope.tools'];
const day = new Date().toISOString().slice(0, 10);

async function track(env, domain, body, userAgent = chromeUA, referrerPath = null) {
  const referrer = referrerPath ?? body.path ?? '/';
  return worker.fetch(new Request(`https://${domain}/api/track`, {
    method: 'POST',
    headers: {
      'content-type': 'application/json',
      'origin': `https://${domain}`,
      'referer': `https://${domain}${referrer}`,
      'user-agent': userAgent,
      'cf-connecting-ip': '203.0.113.7',
    },
    body: JSON.stringify(body),
  }), env, {});
}

function putMetric(env, domain, metric, subject, visits, uniques, id = 'single') {
  const prefix = `${day}:${domain}:${metric}:${encodeURIComponent(subject)}`;
  for (let index = 0; index < visits; index++) {
    env.VISITS.put(`p:v3:${prefix}:${id}-${index}`, '1');
  }
  for (let index = 0; index < uniques; index++) {
    env.VISITS.put(`u:v3:${prefix}:${id}-visitor-${index}`, '1');
  }
}

{
  const env = makeEnv();
  for (const domain of domains) {
    const response = await track(env, domain, {
      path: '/pricing.html?campaign=self-test',
      domain: 'spoofed.example',
      day: '1999-01-01',
    });
    ok(`${domain}: pageview accepted`, response.status === 200);
  }
  const totals = [...env.VISITS.values.keys()].filter(key => key.startsWith('p:v3:'));
  const uniques = [...env.VISITS.values.keys()].filter(key => key.startsWith('u:v3:'));
  ok('én pageview-total pr. domæne', totals.length === 4 && totals.every(key => env.VISITS.values.get(key) === '1'), totals.join(','));
  ok('domæneopdelt unik nøgle pr. domæne', uniques.length === 4, uniques.join(','));
  ok('ingen rå IP gemmes', ![...env.VISITS.values.entries()].some(([key, value]) => `${key}${value}`.includes('203.0.113.7')));
  ok('spoofet domæne ignoreres', totals.every(key => key.includes(':mahope.tools:') || key.includes(':cleancopy.tools:') || key.includes(':deskuptime.com:') || key.includes(':bugbottle.dev:')));
  ok('serverens dato bruges', [...env.VISITS.values.keys()].every(key => !key.includes('1999-01-01')));
  ok('ingen 90-dages coverage-markør skrives', ![...env.VISITS.values.keys()].some(key => key.startsWith('traffic:coverage:v3:')));
  const response = await track(env, 'mahope.tools', { path: '/pricing' });
  const pricingEvents = [...env.VISITS.values.keys()].filter(key => key.startsWith(`p:v3:${day}:mahope.tools:page:%2Fpricing:`));
  ok('query og .html normaliseres', response.status === 200 && pricingEvents.length === 2);
}

{
  const env = makeEnv();
  const responses = await Promise.all(Array.from({ length: 32 }, () =>
    track(env, 'mahope.tools', { path: '/concurrent' })));
  const statsResponse = await worker.fetch(new Request('https://mahope.tools/api/stats?token=hp-stats-v1&days=7'), env, {});
  const stats = await statsResponse.json();
  const row = stats.stats_by_domain?.['mahope.tools']?.[day]?.['/concurrent'];
  ok('samtidige pageviews tælles uden tab',
    responses.every(response => response.status === 200) && row?.visits === 32 && row?.uniques === 1,
    JSON.stringify(row));
}

{
  const env = makeEnv();
  const response = await track(env, 'mahope.tools', { path: '/spoofed-client-path' }, chromeUA, '/verified-referrer');
  const statsResponse = await worker.fetch(new Request('https://mahope.tools/api/stats?token=hp-stats-v1&days=7'), env, {});
  const stats = await statsResponse.json();
  ok('besøgsstien kommer fra same-origin-referer',
    response.status === 200
    && stats.stats_by_domain?.['mahope.tools']?.[day]?.['/verified-referrer']?.visits === 1
    && stats.stats_by_domain?.['mahope.tools']?.[day]?.['/spoofed-client-path'] === undefined,
    JSON.stringify(stats.stats_by_domain?.['mahope.tools']?.[day]));
}

{
  const env = makeEnv();
  const automated = [
    'Googlebot/2.1',
    'bingbot/2.0',
    'curl/8.7.1',
    'Wget/1.24',
    'HeadlessChrome/140.0',
    'GitHub-Actions/1',
    'HermesHealthCheck/3.0',
    'HermesSitemapCheck/1.0',
    'seo_check/1.0',
    'mahope-weekly-report/1',
  ];
  for (const userAgent of automated) {
    const response = await track(env, 'mahope.tools', { path: '/private-bot-probe' }, userAgent);
    ok(`automatisk trafik ignoreres: ${userAgent}`, response.status === 200);
  }
  ok('ingen bot-trafik skrives', env.VISITS.values.size === 0, [...env.VISITS.values.keys()].join(','));
  const wrongHost = await track(env, 'hermes-passiv.pages.dev', { path: '/private-preview' });
  ok('uallowlistet domæne afvises', wrongHost.status === 404);
  const crossOrigin = await worker.fetch(new Request('https://mahope.tools/api/track', {
    method: 'POST',
    headers: { 'content-type': 'application/json', 'origin': 'https://evil.example', 'user-agent': chromeUA },
    body: JSON.stringify({ path: '/forged' }),
  }), env, {});
  const missingOrigin = await worker.fetch(new Request('https://mahope.tools/api/track', {
    method: 'POST',
    headers: { 'content-type': 'application/json', 'user-agent': chromeUA },
    body: JSON.stringify({ path: '/forged' }),
  }), env, {});
  ok('cross-origin tracking afvises', crossOrigin.status === 403 && missingOrigin.status === 403);
  ok('cross-origin request skriver ingen data', ![...env.VISITS.values.keys()].some(key => key.includes('forged')));
  const invalidEvent = await track(env, 'mahope.tools', { path: '/pricing', event: 'bad_event' });
  ok('ugyldigt event afvises', invalidEvent.status === 400);
  const get = await worker.fetch(new Request('https://mahope.tools/api/track'), makeEnv(), {});
  ok('GET pageview afvises', get.status === 405);
}

{
  const env = makeEnv();
  const download = (userAgent, extraHeaders = {}) => worker.fetch(new Request('https://cleancopy.tools/downloads/book.epub', {
    headers: { 'user-agent': userAgent, 'cf-connecting-ip': '203.0.113.8', ...extraHeaders },
  }), env, {});
  const human = await download(chromeUA);
  const crossSite = await download(chromeUA, { 'sec-fetch-site': 'cross-site', origin: 'https://checkout.stripe.com' });
  const bot = await download('Googlebot/2.1');
  ok('download serveres stadig', human.status === 200 && crossSite.status === 200 && bot.status === 200);
  ok('download tælles domæneopdelt', [...env.VISITS.values.keys()].filter(key => key.startsWith(`p:v3:${day}:cleancopy.tools:download:book.epub:`)).length === 2);
  ok('bot-download tælles ikke', [...env.VISITS.values.keys()].filter(key => key.includes(':download:')).length === 3);
  const missingEnv = makeEnv();
  missingEnv.ASSETS.fetch = async () => new Response('Not found', { status: 404 });
  const missing = await worker.fetch(new Request('https://cleancopy.tools/downloads/missing.zip', {
    headers: { 'user-agent': chromeUA, 'cf-connecting-ip': '203.0.113.8' },
  }), missingEnv, {});
  ok('mislykket download tælles ikke', missing.status === 404
    && ![...missingEnv.VISITS.values.keys()].some(key => key.includes(':download:')), [...missingEnv.VISITS.values.keys()].join(','));
}

{
  const env = makeEnv();
  putMetric(env, 'mahope.tools', 'event', '/pricing@cta', 1, 1);
  const response = await worker.fetch(new Request('https://mahope.tools/api/stats?token=hp-stats-v1&days=7'), env, {});
  const data = await response.json();
  ok('event-only domæne er ukendt for pageviews', data.traffic_status === 'unknown'
    && data.domain_status?.['mahope.tools'] === 'unknown', JSON.stringify(data));
  ok('events er bevaret som events', data.events_by_domain?.['mahope.tools']?.[day]?.['/pricing@cta']?.visits === 1,
    JSON.stringify(data.events_by_domain));
}

{
  const env = makeEnv();
  const put = (key, value) => env.VISITS.put(key, value);
  for (const domain of domains) putMetric(env, domain, 'page', `/${domain}`, 1, 1, `seed-${domain}`);
  putMetric(env, 'mahope.tools', 'page', '/pricing', 2, 2);
  putMetric(env, 'cleancopy.tools', 'page', '/', 4, 1);
  putMetric(env, 'mahope.tools', 'event', '/pricing@cta', 9, 1);
  putMetric(env, 'mahope.tools', 'download', 'book.epub', 3, 1);
  await put('t:2026-09-25:%2Flegacy', '99');
  await put('ful:cs_live_0000000000000001', JSON.stringify({ ok: true, product: 'clean-copy-pro', product_name: 'Clean Copy Pro', kind: 'license', license_key: 'secret-must-not-leak' }));
  await put('ful:cs_live_0000000000000002', JSON.stringify({ ok: true, product: 'page-profile-pro', product_name: 'Page Profile Pro', kind: 'license' }));
  await put('ful:cs_live_0000000000000003', JSON.stringify({ ok: true, product: 'clean-copy-pro', product_name: 'Clean Copy Pro', kind: 'license' }));

  const unauthorized = await worker.fetch(new Request('https://mahope.tools/api/stats?token=wrong&days=30'), env, {});
  ok('stats afviser forkert token', unauthorized.status === 401);
  const response = await worker.fetch(new Request(`https://mahope.tools/api/stats?token=hp-stats-v1&days=30`), env, {});
  const data = await response.json();
  ok('stats svarer komplet', response.status === 200 && data.traffic_status === 'ok', JSON.stringify(data));
  ok('stats er ikke cross-origin læsbar', !response.headers.get('access-control-allow-origin'));
  ok('alle domæner har aktuelle pageviews', domains.every(domain => data.domain_status?.[domain] === 'ok'));
  ok('trafik er domæneopdelt', data.stats_by_domain?.['mahope.tools']?.[day]?.['/pricing']?.visits === 2);
  ok('unikke tælles fuldstændigt', data.stats_by_domain?.['mahope.tools']?.[day]?.['/pricing']?.uniques === 2);
  ok('downloads er domæneopdelt', data.downloads_by_domain?.['mahope.tools']?.[day]?.['book.epub']?.visits === 3);
  ok('download-prefix kunne ikke fordobles', data.stats?.[day]?.['downloads@book.epub']?.visits === 3);
  ok('events er ikke sider', data.stats_by_domain?.['mahope.tools']?.[day]?.['/pricing@cta'] === undefined);
  ok('events er domæneopdelt', data.events_by_domain?.['mahope.tools']?.[day]?.['/pricing@cta']?.visits === 9);
  ok('legacy-data ikke tilskrives et domæne', !JSON.stringify(data.stats_by_domain || {}).includes('/legacy'));
  ok('salg tælles pr. unik session og produkt', data.sales?.by_product?.['clean-copy-pro'] === 2 && data.sales?.by_product?.['page-profile-pro'] === 1);
  ok('salgstætteren dokumenterer scope', data.sales?.scope === 'all_time_gross_fulfillments');
  ok('licenser tælles fra ledger', data.licenses_issued === 3);
  ok('ful-records eksponeres ikke', !JSON.stringify(data).includes('secret-must-not-leak'));
}

{
  const env = makeEnv();
  for (let index = 0; index < 76; index++) {
    const session = `cs_live_${String(index).padStart(20, '0')}`;
    await env.VISITS.put(`ful:${session}`, JSON.stringify({
      ok: true,
      product: 'clean-copy-pro',
      product_name: 'Clean Copy Pro',
      kind: 'license',
    }));
  }
  const response = await worker.fetch(new Request('https://mahope.tools/api/stats?token=hp-stats-v1&days=30'), env, {});
  const data = await response.json();
  ok('salgsledgeren har ingen arbitrær 75-post-grænse', data.sales_status === 'ok'
    && data.sales.by_product['clean-copy-pro'] === 76 && data.licenses_issued === 76, JSON.stringify(data));
}

{
  const env = makeEnv();
  await env.VISITS.put('ful:cs_live_retired0000000001', JSON.stringify({
    ok: true,
    product: 'retired-clean-copy',
    product_name: 'Retired Clean Copy',
    kind: 'license',
  }));
  const response = await worker.fetch(new Request('https://mahope.tools/api/stats?token=hp-stats-v1&days=30'), env, {});
  const data = await response.json();
  ok('historisk produkt tælles uden aktuel katalog', data.sales_status === 'ok'
    && data.sales?.by_product?.['retired-clean-copy'] === 1, JSON.stringify(data.sales));
}

{
  const env = makeEnv();
  await env.VISITS.put('ful:cs_test_internal000000001', JSON.stringify({
    ok: true,
    product: 'clean-copy-pro',
    product_name: 'Clean Copy Pro',
    kind: 'license',
  }));
  const response = await worker.fetch(new Request('https://mahope.tools/api/stats?token=hp-stats-v1&days=30'), env, {});
  const data = await response.json();
  ok('Stripe-testkøb tælles ikke som reelt salg', data.sales_status === 'unknown'
    && data.sales === null && data.licenses_issued === null, JSON.stringify(data.sales));
}

{
  const env = makeEnv();
  putMetric(env, 'cleancopy.tools', 'page', '/known', 1, 1, 'known');
  const response = await worker.fetch(new Request('https://mahope.tools/api/stats?token=hp-stats-v1&days=7'), env, {});
  const data = await response.json();
  ok('uinstrumenteret domæne er ukendt', data.traffic_status === 'partial'
    && data.domain_status?.['cleancopy.tools'] === 'ok'
    && data.domain_status?.['bugbottle.dev'] === 'unknown'
    && data.stats_by_domain?.['bugbottle.dev'] === null, JSON.stringify(data));
}

{
  const env = makeEnv();
  for (const domain of domains) await env.VISITS.put(`traffic:coverage:v3:${domain}:page`, '1');
  const response = await worker.fetch(new Request('https://mahope.tools/api/stats?token=hp-stats-v1&days=7'), env, {});
  const data = await response.json();
  ok('gammel coverage-markør giver ikke falsk nul', data.traffic_status === 'unknown'
    && domains.every(domain => data.domain_status?.[domain] === 'unknown')
    && domains.every(domain => data.stats_by_domain?.[domain] === null), JSON.stringify(data));
  ok('tom fulfillment-ledger er ikke et dokumenteret nul', data.sales_status === 'unknown'
    && data.sales === null && data.licenses_issued === null, JSON.stringify(data));
}

{
  const env = makeEnv();
  await env.VISITS.put('ful:cs_live_ledger00000000000001', JSON.stringify({
    ok: true,
    product: 'clean-copy-pro',
    product_name: 'Clean Copy Pro',
    kind: 'license',
  }));
  await env.VISITS.put('fulpending:cs_live_pending00000000001', JSON.stringify({
    session_id: 'cs_live_pending00000000001',
    started_at: new Date().toISOString(),
  }));
  let response = await worker.fetch(new Request('https://mahope.tools/api/stats?token=hp-stats-v1&days=30'), env, {});
  let data = await response.json();
  ok('aktiv fulfillment gør salg ukendt', data.sales_status === 'unknown' && data.sales === null);
  await env.VISITS.put('fulpending:cs_live_pending00000000001', JSON.stringify({
    session_id: 'cs_live_pending00000000001',
    started_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
  }));
  response = await worker.fetch(new Request('https://mahope.tools/api/stats?token=hp-stats-v1&days=30'), env, {});
  data = await response.json();
  ok('forfalden pending-markør blokerer ikke salgsledger', data.sales_status === 'ok'
    && data.sales?.by_product?.['clean-copy-pro'] === 1, JSON.stringify(data.sales));
}

{
  const env = makeEnv();
  await env.VISITS.put('ful:broken', '{not-json');
  const response = await worker.fetch(new Request('https://mahope.tools/api/stats?token=hp-stats-v1&days=30'), env, {});
  const data = await response.json();
  ok('ødelagt sales-ledger er ukendt', data.sales_status === 'unknown' && data.sales === null, JSON.stringify(data));
}

{
  const env = makeEnv();
  await env.VISITS.put('ful:incomplete', JSON.stringify({ ok: true, product: 'clean-copy-pro' }));
  const response = await worker.fetch(new Request('https://mahope.tools/api/stats?token=hp-stats-v1&days=30'), env, {});
  const data = await response.json();
  ok('ufuldstændig sales-ledger er ukendt', data.sales_status === 'unknown' && data.licenses_issued === null);
}

{
  const env = makeEnv();
  await env.VISITS.put('ful:not-a-checkout-session', JSON.stringify({ ok: true, product: 'clean-copy-pro', product_name: 'Clean Copy Pro', kind: 'license' }));
  const response = await worker.fetch(new Request('https://mahope.tools/api/stats?token=hp-stats-v1&days=30'), env, {});
  const data = await response.json();
  ok('ugyldig fulfillment-session gør salg ukendt', data.sales_status === 'unknown' && data.sales === null, JSON.stringify(data));
}

{
  const env = makeEnv();
  putMetric(env, 'mahope.tools', 'page', '/missing-unique', 1, 0);
  const response = await worker.fetch(new Request('https://mahope.tools/api/stats?token=hp-stats-v1&days=30'), env, {});
  const data = await response.json();
  ok('manglende unik nøgle bevarer pageview men markerer unik som ukendt',
    data.traffic_status === 'partial' && data.unique_status === 'unknown'
    && data.stats_by_domain?.['mahope.tools']?.[day]?.['/missing-unique']?.visits === 1
    && data.stats_by_domain?.['mahope.tools']?.[day]?.['/missing-unique']?.uniques === null,
    JSON.stringify(data.stats_by_domain));
}

{
  const env = makeEnv();
  env.VISITS.pageSize = 1000;
  for (const domain of domains.filter(domain => domain !== 'mahope.tools')) {
    putMetric(env, domain, 'page', `/${domain}`, 1, 1, `seed-${domain}`);
  }
  for (let index = 0; index < 251; index++) {
    putMetric(env, 'mahope.tools', 'page', `/page-${index}`, 1, 1, `scale-${index}`);
  }
  const response = await worker.fetch(new Request('https://mahope.tools/api/stats?token=hp-stats-v1&days=30'), env, {});
  const data = await response.json();
  ok('251 reelle sider kan stadig rapporteres', data.traffic_status === 'ok'
    && Object.keys(data.stats_by_domain?.['mahope.tools']?.[day] || {}).length === 251, data.traffic_status);
}

{
  const env = makeEnv();
  env.VISITS.pageSize = 1000;
  for (let index = 0; index <= 5000; index++) {
    env.VISITS.values.set(`p:v3:${day}:mahope.tools:page:%2Fpage-${index}:event-${index}`, '1');
  }
  const response = await worker.fetch(new Request('https://mahope.tools/api/stats?token=hp-stats-v1&days=30'), env, {});
  const data = await response.json();
  ok('for stort datagrundlag gør data ukendt', data.traffic_status === 'unknown', data.traffic_status);
}

{
  const env = makeEnv();
  const originalPut = env.VISITS.put.bind(env.VISITS);
  env.VISITS.put = async (key, value, options) => {
    if (key.startsWith('p:v3:')) throw new Error('pageview write failed');
    return originalPut(key, value, options);
  };
  const response = await track(env, 'mahope.tools', { path: '/pageview-failure' });
  ok('fejlet pageview skriver ingen trafikdata', response.status === 202
    && ![...env.VISITS.values.keys()].some(key => key.startsWith('p:v3:') || key.startsWith('u:v3:')),
    [...env.VISITS.values.keys()].join(','));
  const statsResponse = await worker.fetch(new Request('https://mahope.tools/api/stats?token=hp-stats-v1&days=7'), env, {});
  const stats = await statsResponse.json();
  ok('fejlet skrivning rapporteres som ukendt', stats.traffic_status === 'unknown', JSON.stringify(stats));
}

{
  const env = makeEnv();
  const originalPut = env.VISITS.put.bind(env.VISITS);
  env.VISITS.put = async (key, value, options) => {
    if (key.startsWith('u:v3:')) throw new Error('unique write failed');
    return originalPut(key, value, options);
  };
  const response = await track(env, 'mahope.tools', { path: '/unique-failure' });
  const statsResponse = await worker.fetch(new Request('https://mahope.tools/api/stats?token=hp-stats-v1&days=7'), env, {});
  const stats = await statsResponse.json();
  const row = stats.stats_by_domain?.['mahope.tools']?.[day]?.['/unique-failure'];
  ok('fejlet unikskrivning gør ikke hele trafikken ukendt', response.status === 202
    && stats.traffic_status === 'partial' && stats.unique_status === 'unknown'
    && row?.visits === 1 && row?.uniques === null, JSON.stringify(stats));
}

{
  const env = makeEnv();
  const response = await worker.fetch(new Request('https://mahope.tools/api/health'), env, {});
  const data = await response.json();
  ok('tom men tilgængelig KV er healthy', data.status === 'healthy' && data.kv === true, JSON.stringify(data));
  ok('ukendt trafik rapporteres ikke som nul', data.traffic_status === 'unknown'
    && data.stats.recentVisits === null && data.stats.recentDownloads === null, JSON.stringify(data));
}

{
  const env = makeEnv();
  putMetric(env, 'mahope.tools', 'page', '/known', 1, 1, 'known');
  const response = await worker.fetch(new Request('https://mahope.tools/api/health'), env, {});
  const data = await response.json();
  ok('delvis trafik rapporteres med kendte tal', data.traffic_status === 'partial'
    && data.stats.recentVisits === 1 && data.stats.recentDownloads === 0, JSON.stringify(data));
}

{
  const env = makeEnv();
  env.VISITS.get = async () => { throw new Error('KV unavailable'); };
  const response = await worker.fetch(new Request('https://mahope.tools/api/health'), env, {});
  const data = await response.json();
  ok('degraderet health gør selvstændige counters ukendte', data.traffic_status === 'unknown'
    && data.stats.recentVisits === null && data.stats.recentDownloads === null
    && data.stats.waitlist === null && data.stats.scans === null, JSON.stringify(data));
}

{
  const root = fileURLToPath(new URL('../site', import.meta.url));
  const invalidEvents = [];
  const visit = directory => {
    for (const entry of readdirSync(directory, { withFileTypes: true })) {
      const path = join(directory, entry.name);
      if (entry.isDirectory()) visit(path);
      else if (/\.(?:html|js)$/.test(entry.name)) {
        const source = readFileSync(path, 'utf8');
        for (const match of source.matchAll(/trackEvent\(\s*['"]([^'"]+)['"]/g)) {
          if (!/^[a-z0-9-]+$/.test(match[1])) invalidEvents.push(`${path}:${match[1]}`);
        }
      }
    }
  };
  visit(root);
  ok('alle statiske eventnavne er gyldige', invalidEvents.length === 0, invalidEvents.join('\n'));
}

{
  const root = fileURLToPath(new URL('../dist', import.meta.url));
  const summary = join(root, 'build-summary.json');
  const duplicates = [];
  let htmlCount = 0;
  let sharedTrackerCount = 0;
  const visit = directory => {
    for (const entry of readdirSync(directory, { withFileTypes: true })) {
      const path = join(directory, entry.name);
      if (entry.isDirectory()) visit(path);
      else if (entry.name.endsWith('.html')) {
        htmlCount++;
        const html = readFileSync(path, 'utf8');
        const hasShared = /<script\b[^>]*\bsrc=["'][^"']*\/track\.js["']/i.test(html);
        if (hasShared) sharedTrackerCount++;
        const hasPagePayload = /JSON\.stringify\(\{\s*\{?\s*path\s*:\s*p\s*\}?\s*\}\s*\)/i.test(html);
        const hasInlineRequest = /(?:fetch|sendBeacon)\(\s*['"]\/api\/track['"]/i.test(html);
        const hasInlinePageview = hasPagePayload && hasInlineRequest;
        if (hasShared && hasInlinePageview) duplicates.push(path);
      }
    }
  };
  if (existsSync(root)) visit(root);
  ok('bygget output findes før tracking-gaten', existsSync(summary) && htmlCount > 0 && sharedTrackerCount > 0,
    `${summary}: html=${htmlCount}, shared=${sharedTrackerCount}`);
  ok('ingen buildet side har dobbelt pageview', duplicates.length === 0, duplicates.join('\n'));
}

console.log(`${pass}/${pass + fail} ok`);
process.exit(fail ? 1 : 0);
