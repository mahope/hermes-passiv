/**
 * _worker.js — Cloudflare Pages Worker
 *
 * Two responsibilities:
 * 1. GET /scan-proxy?url=... — fetches a URL server-side (no CORS)
 * 2. Everything else — serves static assets from Pages
 *
 * This file replaces the `functions/` directory approach for
 * maximum compatibility with existing Pages projects.
 */

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const path = url.pathname;

    // === Route: scan-proxy ===
    if (path === '/scan-proxy') {
      return handleScanProxy(request, url);
    }

    // === Route: AI Compliance Assistant ===
    if (path === '/api/compliance-ai') return handleComplianceAI(request, env);

    // === Route: page profiler ===
    if (path === '/api/profile') return handleProfile(request, url, env);

    // === Route: waitlist signup ===
    if (path === '/api/waitlist') return handleWaitlist(request, env);

    // === Route: cookieless visit tracking ===
    if (path === '/api/track') return handleTrack(request, env);
    if (path === '/api/stats') return handleStats(url, env);

    // === Route: self-monitoring health check ===
    if (path === '/api/health') return handleHealth(url, env);

    // === Route: download counting for /downloads/* files ===
    if (path.startsWith('/downloads/')) return handleDownload(request, url, env);

    // === Routes: Clean Copy Pro licensing ===
    if (path === '/api/license/activate') return handleLicenseActivate(request, env);
    if (path === '/api/license/lookup') return handleLicenseLookup(request, env);
    if (path === '/api/license/validate') return handleLicenseValidate(request, env);

    // === Route: Clean Copy API (HTML → Markdown) ===
    if (path === '/api/clean-copy') return handleCleanCopyAPI(request);

    // === Route: Security Headers Checker ===
    if (path === '/api/header-check') return handleHeaderCheck(request, url);

    // === Route: Compliance Site Check (9 checks, server-side) ===
    if (path === '/api/compliance-scan') return handleComplianceScan(request, url, env);

    // === Route: bugbottle live demo (receive + list reports) ===
    if (path === '/api/bugbottle-demo') return handleBugbottleDemo(request, url, env);

    // === Route: Lemon Squeezy webhook (auto-issues license keys) ===
    if (path === '/api/lemon-webhook') return handleLemonWebhook(request, env);

    // === Route: IndexNow key verification (key file generated on the fly) ===
    if (path.startsWith('/indexnow-')) {
      return new Response(path.slice('/indexnow-'.length), {
        headers: { 'Content-Type': 'text/plain; charset=utf-8' },
      });
    }

    // === Route: Clean Copy Pro checkout URL (dynamic embed) ===
    if (path === '/api/checkout') return handleCheckout(url, env);

    // === Route: URL Inspector (redirect chain + security headers) ===
    if (path === '/api/url-inspect') return handleUrlInspect(request, url);

    // === Route: Danish posts moved from /blog to /da/blog (301) ===
    const DA_BLOG_REDIRECTS = {
    'cookie-consent-gdpr-2026': true,
    'dbbaftale-webbureau': true,
    'eaa-frister-2026': true,
    'eaa-haandhaevelse-2026': true,
    'gdpr-boeder-2026': true,
    '/da/blog/gdpr-webbureau-da': true,
    'gdpr-webbureau-da': true,
    'gratis-eaa-saetninger': true,
    'gratis-nis2-vaerktoejer': true,
    'kopier-tabel-fra-pdf': true,
    'kopier-tabel-hjemmeside-til-excel': true,
    'kopier-tabel-hjemmeside-til-notion': true,
    'nis2-guide-da': true,
    'nis2-leverandoerkaede-sikkerhed': true,
    'pris-tilgaengelighedsgennemgang': true,
    'teknisk-seo-tjek-hjemmeside': true,
    'tilgaengeligheds-overlays-eaa': true,
    'tilgaengelighedsscanner-cli': true,
    'wcag-22-aendringer': true,
    };
    const daMatch = path.match(/^\/blog\/([a-z0-9-]+)\/?(?:#.*)?$/);
    if (daMatch && DA_BLOG_REDIRECTS[daMatch[1]]) {
      return Response.redirect(new URL(`/da/blog/${daMatch[1]}`, request.url).toString(), 301);
    }

    // Iter 244: gdpr-rolle-webbureau was a near-duplicate of gdpr-webbureau-da
    // (same H2 structure). Merged: 301 the duplicate to the canonical DA post.
    const DA_BLOG_DUP_REDIRECTS = {
      'gdpr-rolle-webbureau': 'gdpr-webbureau-da',
    };
    const dupSlug = path.replace(/^\/da\/blog\//, '').replace(/\/$/, '');
    if (DA_BLOG_DUP_REDIRECTS[dupSlug]) {
      return Response.redirect(
        new URL(`/da/blog/${DA_BLOG_DUP_REDIRECTS[dupSlug]}`, request.url).toString(),
        301
      );
    }

    // Iter 242: 19 English posts were wrongly moved to /da/blog in iter 241.
    // They are back under /blog; redirect the old /da/blog paths.
    const EN_BLOG_BACK_REDIRECTS = {
    'accessibility-audit-cost': true,
    'copy-as-markdown-chrome-extension': true,
    'copy-clean-text-from-website': true,
    'copy-from-chatgpt-into-word': true,
    'copy-table-from-website-to-excel': true,
    'copy-table-website-iphone-ipad': true,
    'eaa-deadline-2026': true,
    'free-accessibility-testing-tools': true,
    'free-nis2-assessment-tools': true,
    'gdpr-agency-role': true,
    'how-to-write-accessibility-statement': true,
    'html-to-markdown-converter': true,
    'html-to-markdown-vscode': true,
    'meta-tag-checker': true,
    'open-graph-checker': true,
    'paste-into-obsidian-clean-markdown': true,
    'paste-without-formatting-chrome': true,
    'url-to-markdown-converter': true,
    'wcag-22-what-changes': true,
    };
    const enBackMatch = path.match(/^\/da\/blog\/([a-z0-9-]+)\/?(?:#.*)?$/);
    if (enBackMatch && EN_BLOG_BACK_REDIRECTS[enBackMatch[1]]) {
      return Response.redirect(new URL(`/blog/${enBackMatch[1]}`, request.url).toString(), 301);
    }

    // === Redirect old DA slugs to new (iter 460: renamed 5 DA mirrors) ===
    const DA_SLUG_REDIRECTS = {
      'pris-tilgaengelighedsgennemgang': 'hvad-koster-tilgaengelighedsgennemgang',
      'ren-tekst-fra-hjemmeside': 'kopier-ren-tekst-fra-hjemmeside',
      'tjek-hjemmeside-hastighed-uden-lighthouse': 'tjek-hastighed-uden-lighthouse',
      'kopier-tabel-fra-pdf': 'kopier-tabel-fra-pdf-til-excel',
      'open-graph-tjekker': 'open-graph-tjekker-guide',
    };
    const daSlugMatch = path.match(/^\/da\/blog\/([a-z0-9-]+)\/?(?:#.*)?$/);
    if (daSlugMatch && DA_SLUG_REDIRECTS[daSlugMatch[1]]) {
      return Response.redirect(new URL(`/da/blog/${DA_SLUG_REDIRECTS[daSlugMatch[1]]}`, request.url).toString(), 301);
    }

    // === Route: everything else — serve static assets ===
    try {
      const response = await env.ASSETS.fetch(request);
      // If the asset exists, return it
      if (response.status !== 404) return response;
    } catch {
      // ASSETS.fetch throws when no matching asset
    }

    // Fallback: serve index.html (SPA-like behavior for deep links)
    const indexResponse = await env.ASSETS.fetch(new Request(
      new URL('/index.html', request.url),
      request
    ));
    return indexResponse;
  },
};

/**
 * Count a /downloads/<file> hit server-side, then serve the asset.
 * Key format matches pageview stats: t:<day>:downloads@<file>, plus
 * unique u:<day>:downloads@<file>:<hash>. Bots are skipped.
 */
async function handleDownload(request, url, env) {
  const file = url.pathname.slice('/downloads/'.length).split('?')[0];
  try {
    const ua = request.headers.get('user-agent') || '';
    if (!/bot|crawl|spider|curl|wget|headless/i.test(ua)) {
      const day = dailySalt();
      const vh = await visitorHash(request);
      const p = 'downloads@' + file;
      const uniqueKey = `u:${day}:${p}:${vh}`;
      if (!(await env.VISITS.get(uniqueKey))) {
        await env.VISITS.put(uniqueKey, '1', { expirationTtl: 90 * 86400 });
      }
      const totKey = `t:${day}:${p}`;
      const prev = parseInt((await env.VISITS.get(totKey)) || '0', 10);
      await env.VISITS.put(totKey, String(prev + 1), { expirationTtl: 90 * 86400 });
    }
  } catch {
    // counting must never break the download
  }
  return env.ASSETS.fetch(new Request(new URL(url.pathname, request.url), request));
}

/**
 * Handle the scan-proxy endpoint.
 * Fetches a URL server-side and returns the HTML as JSON.
 */
async function handleScanProxy(request, url) {
  const targetUrlParam = url.searchParams.get('url');

  const headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Content-Type': 'application/json',
  };

  // Preflight
  if (request.method === 'OPTIONS') {
    return new Response(null, { status: 204, headers });
  }

  // Validate URL parameter
  if (!targetUrlParam) {
    return new Response(
      JSON.stringify({ ok: false, error: 'Missing ?url= parameter' }),
      { status: 400, headers }
    );
  }

  let targetUrl;
  try {
    targetUrl = new URL(targetUrlParam);
    if (!['http:', 'https:'].includes(targetUrl.protocol)) {
      throw new Error('Invalid protocol');
    }
  } catch {
    return new Response(
      JSON.stringify({ ok: false, error: 'Invalid URL — must start with http:// or https://' }),
      { status: 400, headers }
    );
  }

  try {
    const response = await fetch(targetUrl.toString(), {
      method: 'GET',
      headers: {
        'User-Agent': 'HermesPassiv-Scanner/1.0 (compliance scanner; +https://hermes-passiv.pages.dev)',
        'Accept': 'text/html,application/xhtml+xml,*/*',
      },
      redirect: 'follow',
    });

    const contentType = response.headers.get('content-type') || '';
    if (!contentType.includes('text/html') && !contentType.includes('application/xhtml')) {
      return new Response(
        JSON.stringify({
          ok: false,
          error: `Target returned ${contentType} — not an HTML page. Only HTML pages can be scanned.`,
        }),
        { status: 400, headers }
      );
    }

    const text = await response.text();
    const MAX_SIZE = 500 * 1024;
    if (text.length > MAX_SIZE) {
      return new Response(
        JSON.stringify({
          ok: false,
          error: `Page is too large (${(text.length / 1024).toFixed(0)} KB). Maximum is 500 KB.`,
        }),
        { status: 413, headers }
      );
    }

    return new Response(
      JSON.stringify({ ok: true, html: text, url: targetUrl.toString(), size: text.length }),
      { status: 200, headers }
    );
  } catch (err) {
    return new Response(
      JSON.stringify({
        ok: false,
        error: `Could not fetch the page: ${err.message || 'Unknown error'}`,
        url: targetUrl.toString(),
      }),
      { status: 502, headers }
    );
  }
}
/**
 * Handle the page-profile endpoint.
 * GET /api/profile?url=... — fetches the page server-side and returns
 * a structured profile (meta, OG, JSON-LD, headings, alt, security)
 * with a 21-point weighted score and letter grade. Mirrors the CLI.
 */
async function handleProfile(request, url, env) {
  const headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Content-Type': 'application/json',
  };

  if (request.method === 'OPTIONS') return new Response(null, { status: 204, headers });

  // === Rate limit: max 30 profiles per visitor per day (UTC) ===
  // Keeps server-side fetching bounded so the free API can run unattended.
  if (env && env.VISITS) {
    try {
      const vh = await visitorHash(request);
      const rlKey = `pprl:${dailySalt()}:${vh}`;
      const used = parseInt((await env.VISITS.get(rlKey)) || '0', 10);
      if (used >= 30) {
        return new Response(
          JSON.stringify({
            ok: false,
            error: 'Daily profile limit reached (30). Please come back tomorrow — the limit resets at midnight UTC.',
            limitReached: true,
          }),
          { status: 429, headers }
        );
      }
      await env.VISITS.put(rlKey, String(used + 1), { expirationTtl: 2 * 86400 });
    } catch { /* rate-limit must never block a working answer */ }
  }

  const targetUrlParam = url.searchParams.get('url');
  if (!targetUrlParam) {
    return new Response(JSON.stringify({ ok: false, error: 'Missing ?url= parameter' }), { status: 400, headers });
  }

  let targetUrl;
  try {
    targetUrl = new URL(targetUrlParam);
    if (!['http:', 'https:'].includes(targetUrl.protocol)) throw new Error('bad protocol');
  } catch {
    return new Response(JSON.stringify({ ok: false, error: 'Invalid URL — must start with http:// or https://' }), { status: 400, headers });
  }
  // never profile ourselves — infinite loop risk
  if (/(^|\.)hermes-passiv\.pages\.dev$/.test(targetUrl.hostname)) {
    return new Response(JSON.stringify({ ok: false, error: 'Cannot profile this site itself.' }), { status: 400, headers });
  }

  let resp;
  try {
    resp = await fetch(targetUrl.toString(), {
      method: 'GET',
      headers: { 'User-Agent': 'HermesPassiv-PageProfile/1.0 (+https://hermes-passiv.pages.dev/page-profile)', Accept: 'text/html,application/xhtml+xml,*/*' },
      redirect: 'follow',
    });
  } catch (err) {
    return new Response(JSON.stringify({ ok: false, error: `Could not fetch the page: ${err.message || 'unknown error'}` }), { status: 502, headers });
  }

  const html = await resp.text();
  const MAX_SIZE = 500 * 1024;
  if (resp.status >= 400) {
    return new Response(JSON.stringify({ ok: false, error: `The page returned HTTP ${resp.status}. Check that the URL is correct and publicly reachable.` }), { status: 200, headers });
  }
  if (html.length > MAX_SIZE) {
    return new Response(JSON.stringify({ ok: false, error: `Page is too large (${(html.length / 1024).toFixed(0)} KB). Maximum is 500 KB.` }), { status: 413, headers });
  }

  const profile = analyzeHtml(html, {
    finalUrl: resp.url,
    status: resp.status,
    hsts: resp.headers.has('strict-transport-security'),
    csp: resp.headers.has('content-security-policy'),
    xfo: resp.headers.has('x-frame-options'),
    xcto: resp.headers.has('x-content-type-options'),
  });
  const scored = scoreProfile(profile);

  return new Response(JSON.stringify({ ok: true, url: targetUrl.toString(), final_url: resp.url, status: resp.status, ...profile, ...scored }), { status: 200, headers });
}

const PP_WEIGHTS = {
  title_present: 2, title_length_ok: 1,
  meta_description_present: 2, meta_description_length_ok: 1,
  canonical_present: 1.5,
  og_title_present: 1, og_description_present: 1, og_image_present: 1,
  twitter_card_present: 0.5,
  json_ld_present: 1,
  h1_count_ok: 1,
  images_alt_ok: 2,
  hsts_present: 1, csp_present: 1, xfo_present: 0.5, xcto_present: 0.5,
  lang_present: 1, charset_present: 0.5,
  https: 1,
  no_hreflang_issues: 0.5,
};
const PP_MAX = Object.values(PP_WEIGHTS).reduce((a, b) => a + b, 0);

function analyzeHtml(html, net) {
  const getAttr = (attrs, name) => {
    for (let i = 0; i < attrs.length; i++) if (attrs[i][0] === name || attrs[i][0].toLowerCase() === name) return attrs[i][1];
    return null;
  };
  const meta = { title: null, description: null, canonical: null, language: null, charset: null, og: {}, twitter: {}, hreflang: [] };
  const headings = { h1: [], h2: [], h3: [], h4: [], h5: [], h6: [] };
  const images = { total: 0, with_alt: 0, without_alt: 0 };
  let jsonLdBlocks = 0;
  const jsonLdTypes = [];
  let currentHeading = null;

  // charset from early bytes/meta
  const csMatch = html.slice(0, 2048).match(/<meta[^>]+charset\s*=\s*["']?([\w-]+)/i);
  if (csMatch) meta.charset = csMatch[1].toLowerCase();

  // JSON-LD blocks via regex over raw HTML (script content not needed beyond @type)
  const ldRe = /<script[^>]+type=["']application\/ld\+json["'][^>]*>([\s\S]*?)<\/script>/gi;
  let m;
  while ((m = ldRe.exec(html)) !== null) {
    jsonLdBlocks++;
    try {
      const data = JSON.parse(m[1].trim());
      const items = Array.isArray(data) ? data : [data];
      for (const item of items) {
        if (item && typeof item === 'object' && item['@type']) {
          if (Array.isArray(item['@type'])) jsonLdTypes.push(...item['@type'].map(String));
          else jsonLdTypes.push(String(item['@type']));
        }
      }
    } catch { /* invalid JSON-LD counts as block but no type */ }
  }

  // tag-level parsing with a simple regex scanner (Workers have no DOMParser)
  const tagRe = /<(\/?)(title|meta|link|h[1-6]|img|html)\b([^>]*)>/gi;
  while ((m = tagRe.exec(html)) !== null) {
    const closing = m[1] === '/';
    const tag = m[2].toLowerCase();
    const attrStr = m[3];
    // parse attributes
    const attrs = [];
    const attrRe = /([:\w-]+)\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>]+))/g;
    let am;
    while ((am = attrRe.exec(attrStr)) !== null) attrs.push([am[1].toLowerCase(), am[2] ?? am[3] ?? am[4] ?? '']);

    if (closing) {
      if (tag === 'title') meta.title = (meta.titleRaw || '').trim().slice(0, 300) || null;
      if (currentHeading) { headings[currentHeading].push((headings[currentHeading + '_raw'] || '').trim()); delete headings[currentHeading + '_raw']; currentHeading = null; }
      continue;
    }

    if (tag === 'title') { meta.titleRaw = ''; continue; }
    if (tag === 'html') { const lang = getAttr(attrs, 'lang'); if (lang && !meta.language) meta.language = lang; continue; }

    if (tag === 'meta') {
      const name = (getAttr(attrs, 'name') || '').toLowerCase();
      const prop = (getAttr(attrs, 'property') || '').toLowerCase();
      const content = getAttr(attrs, 'content');
      const httpEquiv = (getAttr(attrs, 'http-equiv') || '').toLowerCase();
      if (name === 'description' && content && !meta.description) meta.description = content.trim();
      else if (prop === 'og:title' && content) meta.og.title = content;
      else if (prop === 'og:description' && content) meta.og.description = content;
      else if (prop === 'og:image' && content) meta.og.image = content;
      else if (name === 'twitter:card' && content) meta.twitter.card = content;
      else if (httpEquiv === 'content-type' && content && !meta.charset) {
        const c = content.match(/charset=([\w-]+)/i); if (c) meta.charset = c[1].toLowerCase();
      }
      continue;
    }

    if (tag === 'link') {
      const rel = (getAttr(attrs, 'rel') || '').toLowerCase();
      const href = getAttr(attrs, 'href');
      if (rel === 'canonical' && href && !meta.canonical) meta.canonical = href;
      else if (rel === 'alternate' && href && getAttr(attrs, 'hreflang')) meta.hreflang.push({ lang: getAttr(attrs, 'hreflang'), href });
      continue;
    }

    if (/^h[1-6]$/.test(tag)) { currentHeading = tag; headings[tag + '_raw'] = ''; continue; }

    if (tag === 'img') {
      images.total++;
      if (getAttr(attrs, 'alt') !== null && getAttr(attrs, 'alt').trim() !== '') images.with_alt++;
      else images.without_alt++;
      continue;
    }
  }

  // capture text inside the currently-open title/heading tags between matches:
  // simpler approach — extract title and heading texts with dedicated scans
  if (!meta.title) {
    const t = html.match(/<title[^>]*>([\s\S]*?)<\/title>/i);
    if (t) meta.title = t[1].replace(/<[^>]+>/g, '').replace(/\s+/g, ' ').trim().slice(0, 300) || null;
  }
  delete meta.titleRaw;
  for (const lvl of ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']) {
    delete headings[lvl + '_raw'];
    headings[lvl] = headings[lvl].filter(Boolean);
    if (headings[lvl].length === 0) {
      // fallback scan for this level
      const re = new RegExp(`<${lvl}[^>]*>([\\s\\S]*?)</${lvl}>`, 'gi');
      let hm; const texts = [];
      while ((hm = re.exec(html)) !== null && texts.length < 50) {
        const txt = hm[1].replace(/<[^>]+>/g, '').replace(/\s+/g, ' ').trim();
        if (txt) texts.push(txt);
      }
      headings[lvl] = texts;
    } else {
      headings[lvl] = headings[lvl].filter(Boolean);
    }
  }

  return {
    title: meta.title,
    title_length: meta.title ? meta.title.length : 0,
    meta_description: meta.description,
    meta_description_length: meta.description ? meta.description.length : 0,
    canonical: meta.canonical,
    language: meta.language,
    charset: meta.charset,
    og: meta.og,
    twitter: meta.twitter,
    json_ld_count: jsonLdBlocks,
    json_ld_types: [...new Set(jsonLdTypes)].slice(0, 20),
    headings,
    images,
    hreflang_count: meta.hreflang.length,
    security: { hsts: !!net.hsts, csp: !!net.csp, xfo: !!net.xfo, xcto: !!net.xcto },
    https: net.finalUrl.startsWith('https://'),
  };
}

function scoreProfile(r) {
  let s = 0;
  const penalties = [];
  if (r.title) {
    s += PP_WEIGHTS.title_present;
    if (r.title_length >= 20 && r.title_length <= 70) s += PP_WEIGHTS.title_length_ok;
    else penalties.push(`Title length (${r.title_length} chars) outside recommended 20-70`);
  } else penalties.push('Missing <title>');

  if (r.meta_description) {
    s += PP_WEIGHTS.meta_description_present;
    if (r.meta_description_length >= 50 && r.meta_description_length <= 165) s += PP_WEIGHTS.meta_description_length_ok;
    else penalties.push(`Meta description length (${r.meta_description_length} chars) outside recommended 50-165`);
  } else penalties.push('Missing meta description');

  if (r.canonical) s += PP_WEIGHTS.canonical_present;
  if (r.og.title) s += PP_WEIGHTS.og_title_present;
  if (r.og.description) s += PP_WEIGHTS.og_description_present;
  if (r.og.image) s += PP_WEIGHTS.og_image_present;
  if (r.twitter.card) s += PP_WEIGHTS.twitter_card_present;
  if (r.json_ld_count > 0) s += PP_WEIGHTS.json_ld_present;

  const h1c = r.headings.h1.length;
  if (h1c === 1) s += PP_WEIGHTS.h1_count_ok;
  else if (h1c > 1) penalties.push(`Multiple H1 tags (${h1c}) — should be exactly 1`);
  else penalties.push('Missing H1 tag');

  if (r.images.total > 0) {
    const ratio = r.images.with_alt / r.images.total;
    if (ratio >= 0.9) s += PP_WEIGHTS.images_alt_ok;
    else if (ratio >= 0.5) s += PP_WEIGHTS.images_alt_ok * 0.5;
    else penalties.push(`Low alt-text coverage: ${r.images.with_alt}/${r.images.total} images have alt`);
  } else s += PP_WEIGHTS.images_alt_ok;

  if (r.security.hsts) s += PP_WEIGHTS.hsts_present;
  if (r.security.csp) s += PP_WEIGHTS.csp_present;
  if (r.security.xfo) s += PP_WEIGHTS.xfo_present;
  if (r.security.xcto) s += PP_WEIGHTS.xcto_present;
  if (r.language) s += PP_WEIGHTS.lang_present;
  if (r.charset) s += PP_WEIGHTS.charset_present;
  if (r.https) s += PP_WEIGHTS.https;
  if (r.hreflang_count > 0) s += PP_WEIGHTS.no_hreflang_issues;

  s = Math.round(s * 10) / 10;
  const pct = (s / PP_MAX) * 100;
  const grade = pct >= 90 ? 'A' : pct >= 75 ? 'B' : pct >= 55 ? 'C' : pct >= 35 ? 'D' : 'F';
  return { score: s, max_score: PP_MAX, grade, penalties };
}

/**
 * Handle the AI Compliance Assistant endpoint.
 * Accepts a user question, calls OpenRouter (Ox Alpha / fallback),
 * and returns the answer as JSON.
 */
async function handleComplianceAI(request, env) {
  const headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Content-Type': 'application/json',
  };

  if (request.method === 'OPTIONS') {
    return new Response(null, { status: 204, headers });
  }

  if (request.method !== 'POST') {
    return new Response(
      JSON.stringify({ ok: false, error: 'POST only' }),
      { status: 405, headers }
    );
  }

  let body;
  try {
    body = await request.json();
  } catch {
    return new Response(
      JSON.stringify({ ok: false, error: 'Invalid JSON body' }),
      { status: 400, headers }
    );
  }

  const question = (body.question || '').trim().slice(0, 2000);
  if (!question) {
    return new Response(
      JSON.stringify({ ok: false, error: 'Missing question' }),
      { status: 400, headers }
    );
  }

  const harmful = /(how\s+to\s+hack|exploit|sql\s+injection|malware|illegal)/i;
  if (harmful.test(question)) {
    return new Response(
      JSON.stringify({ ok: false, error: 'I can only answer compliance-related questions. Please rephrase.' }),
      { status: 400, headers }
    );
  }

  const apiKey = env.OPENROUTER_API_KEY;
  if (!apiKey) {
    return new Response(
      JSON.stringify({ ok: false, error: 'AI service not configured. Contact the site owner.' }),
      { status: 503, headers }
    );
  }

  // === Rate limit: max 20 questions per visitor per day (UTC) ===
  // Keeps OpenRouter spend bounded so the assistant can run unattended.
  if (env.VISITS) {
    try {
      const vh = await visitorHash(request);
      const rlKey = `airl:${dailySalt()}:${vh}`;
      const used = parseInt((await env.VISITS.get(rlKey)) || '0', 10);
      if (used >= 20) {
        try {
          const hk = `airl-hit:${dailySalt()}`;
          const hp = parseInt((await env.VISITS.get(hk)) || '0', 10);
          await env.VISITS.put(hk, String(hp + 1), { expirationTtl: 2 * 86400 });
        } catch { /* best-effort */ }
        return new Response(
          JSON.stringify({
            ok: false,
            error: 'Daily question limit reached (20). Please come back tomorrow — the limit resets at midnight UTC.',
            limitReached: true,
          }),
          { status: 429, headers }
        );
      }
      await env.VISITS.put(rlKey, String(used + 1), { expirationTtl: 2 * 86400 });
    } catch { /* rate-limit must never block a working answer */ }

    // Anonymous usage counter (no content stored) for /api/stats visibility.
    try {
      const cKey = 'ai-ask-count';
      const prev = parseInt((await env.VISITS.get(cKey)) || '0', 10);
      await env.VISITS.put(cKey, String(prev + 1), { expirationTtl: 365 * 86400 });
    } catch { /* counting is best-effort */ }
  }


  const systemPrompt = `You are a practical EU digital compliance expert for small web agencies (1-50 employees). You answer questions about:

1. **EAA (European Accessibility Act)** — WCAG 2.1/2.2 AA requirements, accessibility statements, enforcement since June 2025, exemptions for micro-enterprises
2. **NIS2 Directive** — cybersecurity requirements for digital service providers, vendor security assessments, incident reporting (24h/72h), supply chain security
3. **GDPR** — data processing agreements, controller vs processor roles, cookie consent, subject access requests, data breach notification
4. **Practical compliance** — documentation templates, contract clauses, audit checklists, implementing compliance without a dedicated team

Guidelines:
- Be PRACTICAL and ACTIONABLE. Give specific steps, not just theory.
- Reference exact regulation articles where relevant (e.g., NIS2 Art. 20, GDPR Art. 28, EAA Annex I).
- If you don't know something, say so honestly — don't make up regulation numbers.
- Keep answers concise but complete. Aim for 2-5 paragraphs unless the question needs more.
- Use plain English, not legalese.
- IMPORTANT: You are NOT a lawyer. Always include a brief disclaimer when giving specific legal interpretation.
- End with a practical next-step suggestion where appropriate.

The user's site is: https://hermes-passiv.pages.dev — a free resource with an EAA scanner, platform guides, and compliance templates. Mention it only when directly relevant to their question.`;

  const openRouterUrl = 'https://openrouter.ai/api/v1/chat/completions';
  const payload = {
    model: 'openrouter/auto',
    messages: [
      { role: 'system', content: systemPrompt },
      { role: 'user', content: question },
    ],
    max_tokens: 1500,
    temperature: 0.3,
  };

  try {
    const orResponse = await fetch(openRouterUrl, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json',
        'HTTP-Referer': 'https://hermes-passiv.pages.dev',
        'X-Title': 'Hermes Passiv Compliance AI',
      },
      body: JSON.stringify(payload),
    });

    if (!orResponse.ok) {
      const errText = await orResponse.text().catch(() => 'Unknown error');
      return new Response(
        JSON.stringify({ ok: false, error: 'The AI service is temporarily unavailable. Please try again in a moment.' }),
        { status: 502, headers }
      );
    }

    const data = await orResponse.json();
    const answer = (data.choices?.[0]?.message?.content || '').trim();

    if (!answer) {
      return new Response(
        JSON.stringify({ ok: false, error: 'The AI returned an empty response. Please rephrase your question.' }),
        { status: 502, headers }
      );
    }

    headers['Content-Type'] = 'application/json';
    return new Response(
      JSON.stringify({ ok: true, answer }),
      { status: 200, headers }
    );
  } catch (err) {
    return new Response(
      JSON.stringify({ ok: false, error: 'Network error contacting the AI service. Please try again.' }),
      { status: 502, headers }
    );
  }
}
/**
 * Cookieless visit tracking.
 *
 * Privacy: no cookies, no localStorage, no cross-site identifiers.
 * A daily salt (rotates at 00:00 UTC) is hashed with the visitor IP so
 * unique counts work without ever storing an IP address. Keys are
 * aggregated per path per day and expire after 90 days.
 */

const STATS_TOKEN = 'hp-stats-v1'; // change to something secret before sharing stats URL

function dailySalt() {
  return new Date().toISOString().slice(0, 10); // YYYY-MM-DD (UTC)
}

async function visitorHash(request) {
  const ip = request.headers.get('cf-connecting-ip') || 'unknown';
  const ua = request.headers.get('user-agent') || '';
  const data = new TextEncoder().encode(dailySalt() + '|' + ip + '|' + ua);
  const digest = await crypto.subtle.digest('SHA-256', data);
  return [...new Uint8Array(digest)].map(b => b.toString(16).padStart(2, '0')).join('');
}

function jsonResp(obj, status = 200) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: {
      'Content-Type': 'application/json',
      'Access-Control-Allow-Origin': '*',
      'Cache-Control': 'no-store',
    },
  });
}

/**
 * Clean Copy Pro licensing.
 *
 * Design: license keys are random 32-hex tokens generated server-side,
 * stored in KV (lic:<key> → JSON record). No HMAC needed because the key
 * itself is the secret and never leaves the customer. Activation binds a
 * device fingerprint (hashed) — max 5 devices per key, re-activating the
 * same device is free. Validation is idempotent and rate-limit friendly.
 *
 * Keys can be issued two ways:
 *  1. LS webhook (POST /api/license/activate with {checkout_id} handled by
 *     lemon-webhook flow once Lemon Squeezy is live — see lemon-setup.js).
 *  2. Manual: admin creates keys via `node tools/license-admin.js issue N`.
 *     Until then this endpoint accepts keys from KV only; nothing is
 *     auto-issued without payment.
 */

const LICENSE_MAX_DEVICES = 5;

async function handleLicenseActivate(request, env) {
  return handleLicense(request, env, 'activate');
}

async function handleLicenseValidate(request, env) {
  return handleLicense(request, env, 'validate');
}

async function handleLicense(request, env, mode) {
  if (request.method === 'OPTIONS') {
    return new Response(null, { status: 204, headers: { 'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Methods': 'POST, OPTIONS', 'Access-Control-Allow-Headers': 'Content-Type' } });
  }
  if (request.method !== 'POST') {
    return jsonResp({ ok: false, error: 'POST only' }, 405);
  }
  if (!env.VISITS) {
    return jsonResp({ ok: false, error: 'Service temporarily unavailable.' }, 503);
  }
  try {
    const body = await request.json();
    const key = String(body.license_key || '').trim().toLowerCase();
    if (!/^[a-f0-9]{32}$/.test(key)) {
      return jsonResp({ ok: false, error: 'Invalid license key format.' }, 400);
    }

    const recRaw = await env.VISITS.get(`lic:${key}`);
    if (!recRaw) {
      return jsonResp({ ok: false, error: 'License key not found. Check for typos or contact support.' }, 404);
    }
    let rec;
    try { rec = JSON.parse(recRaw); } catch { rec = { devices: [] }; }

    const now = new Date().toISOString();
    if (rec.status === 'revoked') {
      return jsonResp({ ok: false, error: 'This license has been revoked.' }, 403);
    }
    if (rec.expires_at && rec.expires_at < now) {
      return jsonResp({ ok: false, valid: false, error: 'License expired. Renew at https://hermes-passiv.pages.dev/clean-copy-tool' }, 403);
    }

    const device = String(body.device_id || '').slice(0, 128);
    if (!device) {
      return jsonResp({ ok: false, error: 'Missing device_id.' }, 400);
    }

    // Validate mode: just report status without mutating anything.
    if (mode === 'validate') {
      const known = (rec.devices || []).includes(device);
      if (!known && (rec.devices || []).length >= LICENSE_MAX_DEVICES) {
        return jsonResp({ ok: true, valid: false, reason: 'device_limit', devices_in_use: rec.devices.length });
      }
      return jsonResp({ ok: true, valid: true, plan: rec.plan || 'pro-yearly', expires_at: rec.expires_at || null });
    }

    // Activate mode: bind the device.
    rec.devices = rec.devices || [];
    if (!rec.devices.includes(device)) {
      if (rec.devices.length >= LICENSE_MAX_DEVICES) {
        return jsonResp({ ok: false, error: `Device limit reached (${LICENSE_MAX_DEVICES}). Deactivate a device first.` }, 409);
      }
      rec.devices.push(device);
      await env.VISITS.put(`lic:${key}`, JSON.stringify(rec));
    }

    return jsonResp({
      ok: true,
      activated: true,
      plan: rec.plan || 'pro-yearly',
      expires_at: rec.expires_at || null,
      devices_in_use: rec.devices.length,
    });
  } catch {
    // Licensing must fail safe, never leak stack traces.
    return jsonResp({ ok: false, error: 'Something went wrong. Please try again.' }, 500);
  }
}

/**
 * Lemon Squeezy webhook — POST /api/lemon-webhook
 *
 * Receives order_created webhooks, verifies the HMAC-SHA256 signature
 * (secret: env.LS_WEBHOOK_SECRET, set via `wrangler pages secret put`),
 * and auto-issues a Clean Copy Pro license key into KV (lic:<key>).
 *
 * Idempotent: one key per LS order id — retries never mint duplicates.
 * The response echoes { license_key } so the buyer's key is attached to
 * the order in Lemon Squeezy's logs. Fail-safe: bad signature = 403,
 * missing secret = 503 (LS will retry), malformed body = 400.
 */

const LICENSE_TTL_YEARS = 1;

function timingSafeEqual(a, b) {
  if (a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return diff === 0;
}

async function verifyWebhookSignature(request, rawBody) {
  const secret = request.env && request.env.LS_WEBHOOK_SECRET;
  if (!secret) return { ok: false, reason: 'no_secret' };
  const sigHeader = request.headers.get('x-signature') || '';
  // Lemon Squeezy sends hex-encoded HMAC-SHA256 of the raw body.
  if (!/^[a-f0-9]{64}$/i.test(sigHeader)) return { ok: false, reason: 'bad_header' };
  const key = await crypto.subtle.importKey(
    'raw', new TextEncoder().encode(secret),
    { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']
  );
  const mac = await crypto.subtle.sign('HMAC', key, new TextEncoder().encode(rawBody));
  const expected = [...new Uint8Array(mac)].map(b => b.toString(16).padStart(2, '0')).join('');
  return { ok: timingSafeEqual(sigHeader.toLowerCase(), expected) };
}

async function handleLemonWebhook(request, env) {
  // Route table passes (request, env) — verifyWebhookSignature reads the
  // secret from a request.env shim for symmetry with standalone handlers.
  request.env = env;
  if (request.method === 'OPTIONS') {
    return jsonResp({ ok: true }, 204);
  }
  if (request.method !== 'POST') {
    return jsonResp({ ok: false, error: 'POST only' }, 405);
  }

  const rawBody = await request.text();
  const check = await verifyWebhookSignature(request, rawBody);
  if (!check.ok) {
    return jsonResp({ ok: false, error: check.reason === 'no_secret'
      ? 'Webhook not configured.' : 'Invalid signature.' },
      check.reason === 'no_secret' ? 503 : 403);
  }

  let payload;
  try { payload = JSON.parse(rawBody); } catch {
    return jsonResp({ ok: false, error: 'Bad JSON.' }, 400);
  }

  const meta = payload.meta || {};
  const eventName = meta.event_name || '';
  const orderId = String((meta.custom_data && meta.custom_data.order_id)
    || payload.data?.id || '');
  // Buyer email — LS puts it in data.attributes.user_email. Stored hashed so
  // the lookup page (order id + email) can hand back the key without KV
  // holding plaintext addresses.
  const buyerEmail = String(payload.data?.attributes?.user_email || '')
    .trim().toLowerCase();

  // LS sends test pings and other event types — acknowledge politely.
  if (eventName !== 'order_created') {
    return jsonResp({ ok: true, ignored: eventName || 'unknown' });
  }

  if (!env.VISITS) {
    return jsonResp({ ok: false, error: 'Service temporarily unavailable.' }, 503);
  }

  // Idempotency: one key per order id.
  if (orderId) {
    const existing = await env.VISITS.get(`lic-order:${orderId}`);
    if (existing) {
      return jsonResp({ ok: true, duplicate: true, license_key: existing });
    }
  }

  const productName = String(payload.data?.attributes?.first_order_item?.variant_name
    || payload.data?.attributes?.product_name || '').slice(0, 120);

  const now = new Date();
  const expiresAt = new Date(now.getTime() + LICENSE_TTL_YEARS * 365 * 86400 * 1000).toISOString();
  const bytes = new Uint8Array(16);
  crypto.getRandomValues(bytes);
  const key = [...bytes].map(b => b.toString(16).padStart(2, '0')).join('');

  const rec = {
    status: 'active',
    plan: 'pro-yearly',
    product: productName,
    order_id: orderId,
    created_at: now.toISOString(),
    expires_at: expiresAt,
    devices: [],
  };
  await env.VISITS.put(`lic:${key}`, JSON.stringify(rec));
  if (orderId) {
    await env.VISITS.put(`lic-order:${orderId}`, key);
    // Lookup index: lic-email:<sha256(email)>:<orderId> -> key, so the buyer
    // can retrieve their key with order id + email (both are secrets-ish:
    // order ids are unguessable, email is verified as second factor).
    if (buyerEmail) {
      const eDigest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode('lemail:' + buyerEmail));
      const eHash = [...new Uint8Array(eDigest)].map(b => b.toString(16).padStart(2, '0')).join('');
      await env.VISITS.put(`lic-email:${eHash}:${orderId}`, key);
    }
  }

  // Server-side counter of real paid licenses (never self-testable).
  try {
    const prev = parseInt((await env.VISITS.get('t:all:licenses-issued')) || '0', 10);
    await env.VISITS.put('t:all:licenses-issued', String(prev + 1));
  } catch {}

  return jsonResp({
    ok: true,
    license_key: key,
    expires_at: expiresAt,
    activate_url: 'https://hermes-passiv.pages.dev/clean-copy-tool',
    lookup_url: 'https://hermes-passiv.pages.dev/license-lookup',
  });
}

/**
 * License key lookup — POST { order_id, email } -> { license_key }.
 *
 * Closes the delivery gap: LS receipts can't carry the key, so buyers
 * retrieve it themselves with their order id + the email they bought with.
 * Both values are required; a wrong pair answers exactly like an unknown
 * order (no enumeration oracle). Rate-limited by simple KV counter per IP
 * hash per hour to blunt brute-forcing.
 */
async function handleLicenseLookup(request, env) {
  if (request.method === 'OPTIONS') {
    return new Response(null, { status: 204, headers: { 'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Methods': 'POST, OPTIONS', 'Access-Control-Allow-Headers': 'Content-Type' } });
  }
  if (request.method !== 'POST') {
    return jsonResp({ ok: false, error: 'POST only' }, 405);
  }
  if (!env.VISITS) {
    return jsonResp({ ok: false, error: 'Service temporarily unavailable.' }, 503);
  }

  // Simple throttle: max 10 lookups per IP per hour.
  try {
    const vh = await visitorHash(request);
    const rlKey = `rl:lookup:${vh}:${Math.floor(Date.now() / 3600000)}`;
    const hits = parseInt((await env.VISITS.get(rlKey)) || '0', 10);
    if (hits >= 10) {
      return jsonResp({ ok: false, error: 'Too many attempts. Try again later.' }, 429);
    }
    await env.VISITS.put(rlKey, String(hits + 1), { expirationTtl: 7200 });
  } catch {}

  let body;
  try { body = await request.json(); } catch {
    return jsonResp({ ok: false, error: 'Bad request.' }, 400);
  }
  const orderId = String(body.order_id || '').trim();
  const email = String(body.email || '').trim().toLowerCase();
  if (!orderId || !/^[^\s@]{1,64}@[^\s@]+\.[^\s@]{2,}$/.test(email)) {
    // Uniform answer — don't reveal which field failed.
    return jsonResp({ ok: false, error: 'No license found for that order id and email.' }, 404);
  }

  const eDigest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode('lemail:' + email));
  const eHash = [...new Uint8Array(eDigest)].map(b => b.toString(16).padStart(2, '0')).join('');
  const key = await env.VISITS.get(`lic-email:${eHash}:${orderId}`);
  if (!key) {
    return jsonResp({ ok: false, error: 'No license found for that order id and email.' }, 404);
  }
  const recRaw = await env.VISITS.get(`lic:${key}`);
  let rec = {};
  try { rec = JSON.parse(recRaw); } catch {}
  return jsonResp({
    ok: true,
    license_key: key,
    plan: rec.plan || 'pro-yearly',
    expires_at: rec.expires_at || null,
    activate_url: 'https://hermes-passiv.pages.dev/clean-copy-tool',
  });
}

/**
 * Waitlist signup — POST { email }
 * Stored in the same VISITS KV namespace under wl:<email-hash>.
 * One entry per email (dedupe). No personal data beyond the email itself.
 */
async function handleWaitlist(request, env) {
  if (request.method === 'OPTIONS') {
    return new Response(null, { status: 204, headers: { 'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Methods': 'POST, OPTIONS', 'Access-Control-Allow-Headers': 'Content-Type' } });
  }
  if (request.method !== 'POST') {
    return jsonResp({ ok: false, error: 'POST only' }, 405);
  }
  try {
    const body = await request.json();
    const email = String(body.email || '').trim().toLowerCase();
    // basic validation — no regex overreach
    const valid = /^[^\s@]{1,64}[^\s@]*@[^\s@]+\.[^\s@]{2,}$/.test(email);
    if (!valid) {
      return jsonResp({ ok: false, error: 'Please enter a valid email address.' }, 400);
    }
    // optional signup source (e.g. 'book-nis2-for-agencies', 'compliance-ai') — lets
    // stats show WHERE leads come from without storing anything personal beyond email
    let source = String(body.source || '').trim().toLowerCase().slice(0, 40);
    if (!/^[a-z0-9-]+$/.test(source)) source = 'site';

    const digest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode('wl:' + email));
    const key = 'wl:' + [...new Uint8Array(digest)].map(b => b.toString(16).padStart(2, '0')).join('');

    const isNew = !(await env.VISITS.get(key));
    if (isNew) {
      // store "email|source" so Mads can import the list later (split on last |)
      await env.VISITS.put(key, email + '|' + source, { expirationTtl: 365 * 86400 });
      // counter for quick reads
      const cKey = 'wl-count';
      const prev = parseInt((await env.VISITS.get(cKey)) || '0', 10);
      await env.VISITS.put(cKey, String(prev + 1), { expirationTtl: 365 * 86400 });
      // per-source counter
      const sKey = 'wlsrc:' + source;
      const sprev = parseInt((await env.VISITS.get(sKey)) || '0', 10);
      await env.VISITS.put(sKey, String(sprev + 1), { expirationTtl: 365 * 86400 });
    }
    // always answer ok — do not leak whether an address was already signed up
    return jsonResp({ ok: true });
  } catch {
    return jsonResp({ ok: false, error: 'Something went wrong. Please try again.' }, 500);
  }
}

async function handleTrack(request, env) {
  if (request.method !== 'POST') {
    return jsonResp({ ok: false, error: 'POST only' }, 405);
  }
  try {
    const body = await request.json();
    let p = String(body.path || '/');
    // keep keys tidy: strip query strings, cap length
    p = p.split('?')[0].slice(0, 120) || '/';
    // event type: default pageview; tools send event=scan on actual use
    let ev = String(body.event || 'pageview').slice(0, 24);
    if (!/^[a-z0-9-]+$/.test(ev)) ev = 'pageview';
    if (ev !== 'pageview') p = p + '@' + ev;
    const day = dailySalt();

    const vh = await visitorHash(request);
    const uniqueKey = `u:${day}:${p}:${vh}`;
    const isNew = !(await env.VISITS.get(uniqueKey));
    if (isNew) {
      await env.VISITS.put(uniqueKey, '1', { expirationTtl: 90 * 86400 });
    }

    const totKey = `t:${day}:${p}`;
    const prev = parseInt((await env.VISITS.get(totKey)) || '0', 10);
    await env.VISITS.put(totKey, String(prev + 1), { expirationTtl: 90 * 86400 });

    return jsonResp({ ok: true });
  } catch {
    // never let analytics break anything
    return jsonResp({ ok: false }, 202);
  }
}

async function handleStats(url, env) {
  if (url.searchParams.get('token') !== STATS_TOKEN) {
    return jsonResp({ ok: false, error: 'unauthorized' }, 401);
  }
  const days = Math.min(parseInt(url.searchParams.get('days') || '30', 10) || 30, 90);
  const out = {};
  let cursor = null;
  do {
    const page = await env.VISITS.list({ cursor });
    for (const k of page.keys) {
      // key formats: t:<day>:<path> (total) and u:<day>:<path>:<hash> (unique)
      const parts = k.name.split(':');
      if (parts.length < 3) continue;
      const kind = parts[0], day = parts[1];
      if (!out[day]) out[day] = {};
      if (kind === 't') {
        const p = parts.slice(2).join(':');
        out[day][p] = out[day][p] || {};
      }
    }
    cursor = page.list_complete ? null : page.cursor;
  } while (cursor);

  // second pass: read values (list doesn't return values)
  for (const day of Object.keys(out)) {
    for (const p of Object.keys(out[day])) {
      const v = parseInt((await env.VISITS.get(`t:${day}:${p}`)) || '0', 10);
      const prefix = `u:${day}:${p}:`;
      const upage = await env.VISITS.list({ prefix });
      out[day][p] = { visits: v, uniques: upage.keys.length };
    }
  }

  // keep only requested window, newest first
  const cutoff = new Date(Date.now() - days * 86400 * 1000).toISOString().slice(0, 10);
  const filtered = {};
  for (const day of Object.keys(out).sort().reverse()) {
    if (day >= cutoff) filtered[day] = out[day];
  }
  // waitlist count (honest metric)
  let waitlist = null;
  try { waitlist = parseInt((await env.VISITS.get('wl-count')) || '0', 10); } catch {}
  // per-source lead counts (wlsrc:<source>) — scan KV keys, aggregate top sources
  const wl_sources = {};
  try {
    let scursor = null;
    do {
      const page = await env.VISITS.list({ prefix: 'wlsrc:', cursor: scursor });
      for (const k of page.keys) {
        const v = parseInt((await env.VISITS.get(k.name)) || '0', 10);
        if (v > 0) wl_sources[k.name.slice(6)] = v;
      }
      scursor = page.list_complete ? null : page.cursor;
    } while (scursor);
  } catch {}
  let licenses_issued = null;
  try { licenses_issued = parseInt((await env.VISITS.get('t:all:licenses-issued')) || '0', 10); } catch {}

  // AI assistant usage (anonymous counters, no question content stored)
  let ai_asks = null;
  try { ai_asks = parseInt((await env.VISITS.get('ai-ask-count')) || '0', 10); } catch {}
  let ai_limited_today = null;
  try { ai_limited_today = parseInt((await env.VISITS.get(`airl-hit:${dailySalt()}`)) || '0', 10); } catch {}
  let scans = null;
  try { scans = parseInt((await env.VISITS.get('csc-count')) || '0', 10); } catch {}

  return jsonResp({ ok: true, days, stats: filtered, waitlist, wl_sources, licenses_issued, ai_asks, ai_limited_today, scans });
}

/**
 * GET /api/health — lightweight self-monitoring endpoint.
 * Returns KV reachability, site status, and basic metrics.
 * Used by cron job to detect silent failures.
 */
async function handleHealth(url, env) {
  const DAY = 86400 * 1000;
  const now = Date.now();
  const today = new Date(now).toISOString().slice(0, 10);
  const yesterday = new Date(now - DAY).toISOString().slice(0, 10);

  let kvOk = false, statsOk = false, recentVisits = 0, recentDownloads = 0, lastDeploy = null;
  try {
    // check KV is reachable by reading yesterday's homepage visits
    const test = await env.VISITS.get(`t:${yesterday}:/`);
    kvOk = true;
    // count recent traffic (today + yesterday)
    for (const day of [today, yesterday]) {
      const page = await env.VISITS.list({ prefix: `t:${day}:` });
      for (const k of page.keys) {
        const v = parseInt((await env.VISITS.get(k.name)) || '0', 10);
        if (k.name.includes('downloads@')) recentDownloads += v;
        else recentVisits += v;
      }
    }
    statsOk = true;
  } catch (e) {
    // KV may be unreachable or empty — not a fatal error
  }

  let waitlist = 0;
  try { waitlist = parseInt((await env.VISITS.get('wl-count')) || '0', 10); } catch {}
  let scans = 0;
  try { scans = parseInt((await env.VISITS.get('csc-count')) || '0', 10); } catch {}

  return jsonResp({
    ok: true,
    status: kvOk ? 'healthy' : 'degraded',
    kv: kvOk,
    timestamp: new Date().toISOString(),
    stats: { recentVisits, recentDownloads, waitlist, scans },
    lastDeploy: lastDeploy,
    version: 1,
  });
}

/**
 * Clean Copy API — POST /api/clean-copy
 *
 * Accepts HTML and returns clean Markdown or plain text.
 * Free tier: no auth, up to 50 KB input, rate-limited client-side.
 * Pro tier (future): higher limits, custom cleanup rules.
 */

/**
 * Handle /api/header-check — fetches a URL server-side and returns all response headers.
 * Used by the Security Headers Checker tool. No CORS issues since it's server-side.
 */
async function handleHeaderCheck(request, url) {
  const targetUrlParam = url.searchParams.get('url');

  const headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Content-Type': 'application/json',
  };

  if (request.method === 'OPTIONS') {
    return new Response(null, { status: 204, headers });
  }

  if (!targetUrlParam) {
    return new Response(
      JSON.stringify({ ok: false, error: 'Missing ?url= parameter' }),
      { status: 400, headers }
    );
  }

  let targetUrl;
  try {
    targetUrl = new URL(targetUrlParam);
    if (!['http:', 'https:'].includes(targetUrl.protocol)) {
      throw new Error('Invalid protocol');
    }
  } catch {
    return new Response(
      JSON.stringify({ ok: false, error: 'Invalid URL — must start with http:// or https://' }),
      { status: 400, headers }
    );
  }

  try {
    const response = await fetch(targetUrl.toString(), {
      method: 'GET',
      headers: {
        'User-Agent': 'HermesPassiv-SecurityHeaders/1.0 (+https://hermes-passiv.pages.dev)',
        'Accept': 'text/html,application/xhtml+xml,application/xml,*/*',
      },
      redirect: 'follow',
    });

    // Collect all response headers
    const responseHeaders = {};
    response.headers.forEach((value, key) => {
      responseHeaders[key] = value;
    });

    return new Response(JSON.stringify({
      ok: true,
      url: response.url,
      status: response.status,
      statusText: response.statusText,
      headers: responseHeaders,
      redirected: response.redirected,
      finalUrl: response.url,
    }), { status: 200, headers });
  } catch (err) {
    return new Response(JSON.stringify({
      ok: false,
      error: err.message || 'Failed to fetch URL',
    }), { status: 502, headers });
  }
}

async function handleCleanCopyAPI(request) {
  const headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Content-Type': 'application/json',
  };

  if (request.method === 'OPTIONS') {
    return new Response(null, { status: 204, headers });
  }

  if (request.method !== 'POST') {
    return new Response(
      JSON.stringify({ ok: false, error: 'POST only' }),
      { status: 405, headers }
    );
  }

  let body;
  try { body = await request.json(); }
  catch {
    return new Response(
      JSON.stringify({ ok: false, error: 'Invalid JSON body' }),
      { status: 400, headers }
    );
  }

  const html = String(body.html || '').trim();
  if (!html) {
    return new Response(
      JSON.stringify({ ok: false, error: 'Missing html — send the HTML you want to convert.' }),
      { status: 400, headers }
    );
  }

  if (html.length > 50000) {
    return new Response(
      JSON.stringify({ ok: false, error: 'Input too large (max 50 KB).' }),
      { status: 413, headers }
    );
  }

  const mode = body.mode === 'plain' ? 'plain' : 'markdown';

  try {
    let markdown;
    if (mode === 'plain') {
      markdown = _ccCleanText(_ccStripTagsSafe(html));
    } else {
      markdown = _ccHtmlToMarkdown(html);
    }

    return new Response(JSON.stringify({
      ok: true,
      markdown,
      mode,
      input_chars: html.length,
      output_chars: markdown.length,
      version: '1.5.2',
    }), { status: 200, headers });
  } catch (err) {
    return new Response(
      JSON.stringify({ ok: false, error: 'Conversion failed: ' + (err.message || 'unknown error') }),
      { status: 500, headers }
    );
  }
}

/* ── Clean Copy Converter Core (embedded) ─────────────────────────────
 * Extracted from tools/clean_copy_core.js v1.5.2. Same engine as the
 * Chrome extension, CLI, web tool, and all other Clean Copy surfaces.
 * All functions prefixed _cc_ to avoid collisions with page-profile code.
 */

const _CC_CLEAN_RULES = [
  { pattern: /[\u201C\u201D]/g, replacement: '"' },
  { pattern: /[\u2018\u2019]/g, replacement: "'" },
  { pattern: /\u2014/g, replacement: ' -- ' },
  { pattern: /\u2013/g, replacement: ' - ' },
  { pattern: /[\u200B\u200C\u200D\uFEFF]/g, replacement: '' },
  { pattern: /[\u2060-\u2064\uFEFF]/g, replacement: '' },
  { pattern: /\u00A0/g, replacement: ' ' },
  { pattern: /([^\n \t])[ \t]{2,}/g, replacement: '$1 ' },
  { pattern: /\n{3,}/g, replacement: '\n\n' },
];

function _ccStripTagsSafe(html) {
  let out = '', i = 0, n = html.length;
  while (i < n) {
    const lt = html.indexOf('<', i);
    if (lt === -1) { out += html.slice(i); break; }
    out += html.slice(i, lt);
    let j = lt + 1, quote = null;
    while (j < n) {
      const ch = html[j];
      if (quote) { if (ch === quote) quote = null; }
      else if (ch === '"' || ch === "'") quote = ch;
      else if (ch === '>') break;
      j++;
    }
    if (j >= n) { out += html.slice(lt); break; }
    i = j + 1;
  }
  return out;
}

function _ccCleanText(text) {
  let cleaned = text;
  for (const rule of _CC_CLEAN_RULES) cleaned = cleaned.replace(rule.pattern, rule.replacement);
  return cleaned.trim();
}

function _ccHtmlToMarkdown(html) {
  let md = html;

  // Strip script/style/noscript/template/head content
  md = md.replace(/<(script|style|noscript|template|head)\b[^>]*>[\s\S]*?<\/\1>/gi, '');

  // CDATA: keep content
  md = md.replace(/<!\[CDATA\[([\s\S]*?)\]\]>/g, '$1');

  // Strip SVG/MathML subtrees entirely
  md = md.replace(/<(svg|math)\b[^>]*>[\s\S]*?<\/\1>/gi, (m, tag) => {
    if (tag.toLowerCase() === 'math') {
      const alt = /alt="([^"]*)"/i.exec(m);
      if (alt && alt[1]) return '\n' + alt[1].trim() + '\n';
    }
    return '';
  });

  // Form controls
  md = md.replace(/<select\b[^>]*>([\s\S]*?)<\/select>/gi, (_, body) => {
    const opts = [];
    const re = /<(?:option|optgroup)\b[^>]*>/gi;
    let m;
    while ((m = re.exec(body)) !== null) {
      const labelM = /label="([^"]*)"/i.exec(m[0]);
      if (labelM) { opts.push(labelM[1].trim()); continue; }
      const rest = body.slice(re.lastIndex);
      const text = /^([^<]*)/.exec(rest)[1];
      if (text.trim()) opts.push(text.trim());
    }
    return opts.length ? '\n' + opts.join('\n') + '\n' : '';
  });
  md = md.replace(/<(input|textarea)\b[^>]*>/gi, (m, tag) => {
    if (tag.toLowerCase() === 'textarea') return m;
    const val = /value="([^"]*)"/i.exec(m);
    return val && val[1] ? '\n' + val[1] + '\n' : '';
  });

  // iframe/object
  md = md.replace(/<(iframe|object)\b[^>]*>([\s\S]*?)<\/\1>/gi, (_, tag, body) => {
    if (tag.toLowerCase() === 'object') return '\n' + body.replace(/<param\b[^>]*>/gi, '') + '\n';
    return '\n' + body + '\n';
  });

  // details/summary
  md = md.replace(/<details[^>]*>([\s\S]*?)<\/details>/gi, (_, body) => {
    let out = '';
    const sum = body.match(/<summary[^>]*>([\s\S]*?)<\/summary>/i);
    if (sum) out += '**' + _ccHtmlToMarkdown(sum[1]).trim() + '**\n\n';
    out += _ccHtmlToMarkdown(body.replace(/<summary[^>]*>[\s\S]*?<\/summary>/i, ''));
    return '\n' + out + '\n\n';
  });

  // Definition lists
  md = md.replace(/<dl[^>]*>([\s\S]*?)<\/dl>/gi, (_, body) => {
    const parts = [];
    const re = /<(dt|dd)[^>]*>([\s\S]*?)<\/\1>/gi;
    let m;
    while ((m = re.exec(body)) !== null) {
      const text = m[2].replace(/<[^>]*>/g, '').trim();
      if (!text) continue;
      parts.push(m[1].toLowerCase() === 'dt' ? '**' + text + '**' : ':   ' + text);
    }
    return parts.length ? '\n' + parts.join('\n') + '\n\n' : '';
  });

  // Figcaptions
  md = md.replace(/<figcaption[^>]*>([\s\S]*?)<\/figcaption>/gi, (_, cap) => '\n\n' + cap + '\n\n');

  // Blockquotes
  let bqPrev;
  do {
    bqPrev = md;
    md = md.replace(/<blockquote[^>]*>((?:(?!<\/?blockquote)[\s\S])*)<\/blockquote>/gi, (_, body) => {
      const inner = _ccHtmlToMarkdown(body);
      const quoted = inner.split('\n').map(l => (l ? '> ' + l : '>')).join('\n');
      return '\n' + quoted + '\n';
    });
  } while (md !== bqPrev);

  // Headings
  md = md.replace(/<h1[^>]*>(.*?)<\/h1>/gi, '# $1\n\n');
  md = md.replace(/<h2[^>]*>(.*?)<\/h2>/gi, '## $1\n\n');
  md = md.replace(/<h3[^>]*>(.*?)<\/h3>/gi, '### $1\n\n');
  md = md.replace(/<h4[^>]*>(.*?)<\/h4>/gi, '#### $1\n\n');
  md = md.replace(/<h5[^>]*>(.*?)<\/h5>/gi, '##### $1\n\n');
  md = md.replace(/<h6[^>]*>(.*?)<\/h6>/gi, '###### $1\n\n');

  // Bold / italic
  md = md.replace(/<(?:b|strong)[^>]*>(.*?)<\/(?:b|strong)>/gi, '**$1**');
  md = md.replace(/<(?:i|em)[^>]*>(.*?)<\/(?:i|em)>/gi, '*$1*');

  // Links
  md = md.replace(/<a[^>]*href="([^"]*)"[^>]*>([\s\S]*?)<\/a>/gi, (m, href, inner) => {
    const text = inner.replace(/<img[^>]*>/gi, '').replace(/<[^>]*>/g, '').trim();
    if (!text || /^#/.test(href)) return inner;
    return '[' + text + '](' + href + ')';
  });

  // Images
  md = md.replace(/<img[^>]*src="([^"]*)"[^>]*alt="([^"]*)"[^>]*>/gi, '![$2]($1)');
  md = md.replace(/<img[^>]*src="([^"]*)"[^>]*>/gi, '![]($1)');

  // Code blocks
  md = md.replace(/<pre[^>]*>([\s\S]*?)<\/pre>/gis, (_, code) => {
    let lang = '';
    const langMatch = /<code[^>]*class=["'][^"']*\b(?:language-|lang-|brush:\s*)([a-zA-Z0-9+#_]+)\b[^"']*["'][^>]*>/i.exec(code)
      || /<pre[^>]*class=["'][^"']*\b(?:language-|lang-)([a-zA-Z0-9+#_]+)\b[^"']*["'][^>]*>/i.exec(code);
    if (langMatch) lang = langMatch[1].toLowerCase();
    code = code.replace(/<code[^>]*>/gi, '').replace(/<\/code>/gi, '');
    code = code.replace(/<br\s*\/?>/gi, '\n');
    return '```' + lang + '\n' + code.trim() + '\n```\n\n';
  });

  md = md.replace(/<code[^>]*>(.*?)<\/code>/gi, '`$1`');

  // Abbreviations
  const abbrSeen = new Set();
  md = md.replace(/<abbr[^>]*title="([^"]*)"[^>]*>([\s\S]*?)<\/abbr>|<abbr[^>]*>([\s\S]*?)<\/abbr>/gi, (m, title, term1, term2) => {
    const term = (term1 || '').trim() || (term2 || '').trim();
    if (!term) return '';
    const t = (title || '').trim();
    if (t && !abbrSeen.has(term.toLowerCase() + '|' + t)) {
      abbrSeen.add(term.toLowerCase() + '|' + t);
      return term + ' (' + t + ')';
    }
    return term;
  });

  // Tables
  const _ccAlignOf = (tag) => {
    const style = (tag.match(/style\s*=\s*[\x22\x27]([^\x22\x27]*)[\x22\x27]/i) || [])[1] || '';
    const attr = (tag.match(/\balign\s*=\s*[\x22\x27]([^\x22\x27]*)[\x22\x27]/i) || [])[1] || '';
    const hay = (style.replace(/;/g, ' ') + ' ' + attr).toLowerCase();
    if (/text-align\s*:\s*(center|right|left)|\b(center|right|left)\b/.test(hay)) {
      if (/\bleft\b/.test(hay)) return ':---';
      if (/\bright\b/.test(hay)) return '---:';
      if (/\bcenter\b/.test(hay)) return ':---:';
    }
    return null;
  };
  const _ccConvertTable = (_, tableHtml) => {
    const cellText = (cellHtml) => {
      let t = _ccHtmlToMarkdown(cellHtml);
      return t.replace(/\s*\n+\s*/g, ' ').replace(/\|/g, '\\|').trim();
    };
    const rows = []; const aligns = [];
    const trRe = /<tr[^>]*>([\s\S]*?)<\/tr>/gi;
    let trm;
    while ((trm = trRe.exec(tableHtml)) !== null) {
      const cells = []; const rowAligns = [];
      const cellRe = /<(th|td)\b([^>]*)>([\s\S]*?)<\/\1>/gi;
      let cm;
      while ((cm = cellRe.exec(trm[1])) !== null) {
        cells.push(cellText(cm[3]));
        const spanMatch = /colspan\s*=\s*[\x22\x27]?(\d+)[\x22\x27]?/i.exec(cm[2]);
        const span = Math.max(1, parseInt(spanMatch ? spanMatch[1] : '1', 10) || 1);
        for (let s = 0; s < span; s++) {
          if (s === 0) rowAligns.push(_ccAlignOf(cm[2]));
          else rowAligns.push(null);
        }
      }
      rows.push(cells); aligns.push(rowAligns);
    }
    if (rows.length === 0) return '';
    const cols = Math.max(...rows.map(r => r.length));
    rows.forEach(r => { while (r.length < cols) r.push(''); });
    aligns.forEach(a => { while (a.length < cols) a.push(null); });
    const colAlign = Array(cols).fill(null);
    for (let c = 0; c < cols; c++) {
      for (const a of aligns) { if (a[c]) { colAlign[c] = a[c]; break; } }
    }
    const sepRow = Array.from({length: cols}, (_, i) => colAlign[i] || ' --- ');
    const out = ['| ' + rows[0].join(' | ') + ' |',
                 '|' + sepRow.join('|') + '|'];
    for (let i = 1; i < rows.length; i++) {
      out.push('| ' + rows[i].join(' | ') + ' |');
    }
    return '\n' + out.join('\n') + '\n\n';
  };
  let tblPrev;
  do {
    tblPrev = md;
    md = md.replace(/<table[^>]*>((?:(?!<table[\s>]|<\/table)[\s\S])*)<\/table>/gi, _ccConvertTable);
  } while (md !== tblPrev);

  // Lists
  const _ccConvertList = (_, openTag, body) => {
    const ordered = /^<ol/i.test(openTag);
    let idx = 0;
    const startAttr = /start\s*=\s*["']?(\d+)["']?/i.exec(openTag);
    if (ordered && startAttr) idx = Math.max(0, parseInt(startAttr[1], 10) - 1);
    const items = [];
    const re = /<li[^>]*>([\s\S]*?)<\/li>/gi;
    let m;
    while ((m = re.exec(body)) !== null) {
      idx += 1;
      const marker = ordered ? `${idx}. ` : '- ';
      const inner = m[1].replace(/^\s+/, '').replace(/\s+$/, '')
        .replace(/\n([ \t]*)- /g, (all, ws) => '\n  ' + ws + '- ')
        .replace(/\n([ \t]*)(\d+)\. /g, (all, ws, n) => '\n  ' + ws + n + '. ');
      items.push(marker + inner);
    }
    if (items.length === 0) return '\n' + body + '\n';
    return '\n' + items.join('\n') + '\n';
  };
  let listPrev;
  do {
    listPrev = md;
    md = md.replace(/(<(?:ul|ol)[^>]*>)((?:(?!<\/?(?:ul|ol)[^>]*>)[\s\S])*)<\/(?:ul|ol)>/gi, _ccConvertList);
  } while (md !== listPrev);

  // Paragraphs, breaks, horizontal rules
  md = md.replace(/<p[^>]*>(.*?)<\/p>/gi, '$1\n\n');
  md = md.replace(/<br\s*\/?>/gi, '\n');
  md = md.replace(/<hr\s*\/?>/gi, '---\n\n');

  // Strip remaining tags
  md = _ccStripTagsSafe(md);

  // HTML entities
  const _CC_ENTITIES = { amp: '&', lt: '<', gt: '>', quot: '"', apos: "'", nbsp: '\u00A0',
    copy: '\u00A9', reg: '\u00AE', trade: '\u2122', hellip: '\u2026', mdash: '\u2014', ndash: '\u2013',
    lsquo: '\u2018', rsquo: '\u2019', ldquo: '\u201C', rdquo: '\u201D',
    eacute: '\u00E9', egrave: '\u00E8', agrave: '\u00E0', ccedil: '\u00E7', uuml: '\u00FC', ouml: '\u00F6', auml: '\u00E4',
    aring: '\u00E5', oslash: '\u00F8', aelig: '\u00E6', ntilde: '\u00F1', iuml: 'ï', szlig: '\u00DF', euro: '\u20AC', deg: '\u00B0' };
  md = md.replace(/&(#[0-9]+|#x[0-9a-fA-F]+|[a-zA-Z][a-zA-Z0-9]*);/g, function (ent, body) {
    if (body[0] === '#') {
      const code = body[1] === 'x' || body[1] === 'X' ? parseInt(body.slice(2), 16) : parseInt(body.slice(1), 10);
      return code > 0 && code <= 0x10ffff ? String.fromCodePoint(code) : ent;
    }
    return Object.prototype.hasOwnProperty.call(_CC_ENTITIES, body) ? _CC_ENTITIES[body] : ent;
  });
  md = md.replace(/&amp;/g, '&');

  // Whitespace cleanup
  md = md.replace(/\n{4,}/g, '\n\n');
  md = md.replace(/([^\n \t])[ ]{2,}/g, '$1 ');

  return _ccCleanText(md);
}

/* ── Compliance Site Check API — GET /api/compliance-scan?url=... ─────
 * Server-side port of mahope/compliance-site-check v2 (9 checks).
 * Used by /compliance-site-check.html and available as a free API.
 */

const CSC_CHECKS = {
  privacy: {
    label: 'Privacy Policy',
    type: 'page',
    paths: ['/privacy', '/privacy-policy', '/privacy/', '/datenschutz', '/legal/privacy'],
    hints: ['privacy', 'privatliv', 'datenschutz', 'data protection', 'personal data', 'personoplysninger', 'gdpr'],
    importance: 'Required by GDPR Art. 13-14 if you process personal data.',
  },
  terms: {
    label: 'Terms of Service',
    type: 'page',
    paths: ['/terms', '/terms-of-service', '/terms-and-conditions', '/tos', '/conditions', '/vilkar', '/agb'],
    hints: ['terms', 'conditions', 'vilkar', 'agb', 'nutzungsbedingungen'],
    importance: 'Required for any commercial website, especially SaaS and e-commerce.',
  },
  cookie: {
    label: 'Cookie Consent Banner',
    type: 'scan',
    hints: ['cookie', 'cookieconsent', 'Cookiebot', 'cookie_notice', 'cookie-law', 'consent', 'OneTrust', 'cookielaw', 'cookiecontrol', 'osano', 'termly', 'complianz', 'cookiescript', 'CookieFirst', 'cookie_consent', 'cc-window', 'cookie-bar', 'cmp-banner', 'cmp-wrapper'],
    importance: 'Required by ePrivacy Directive / GDPR — opt-in for non-essential cookies.',
  },
  imprint: {
    label: 'Imprint / Impressum / Legal Notice',
    type: 'page',
    paths: ['/imprint', '/impressum', '/legal', '/legal-notice', '/legal/imprint', '/about/legal', '/site-notice', '/disclaimer'],
    hints: ['imprint', 'impressum', 'legal notice', 'legal disclosure', 'site notice', 'ansvarlig', 'udgiver'],
    importance: 'Required in Germany (§5 TMG, §18 MStV), Austria, Switzerland.',
  },
  accessibility: {
    label: 'Accessibility Statement',
    type: 'page',
    paths: ['/accessibility', '/accessibility-statement', '/a11y', '/accessibility/', '/tilgaengelighed', '/tilgaengelighedserklaering', '/erklaering', '/wcag', '/accessibility-declaration'],
    hints: ['accessibility', 'tilgaengelighed', 'wcag', 'a11y', 'barrierefreiheit'],
    importance: 'Required by EAA / EN 301 549 for public sector and essential-service websites.',
  },
  dpa: {
    label: 'Data Processing Agreement (DPA)',
    type: 'page',
    paths: ['/dpa', '/data-processing-agreement', '/databehandleraftale', '/dpa/', '/gdpr/dpa', '/gdpr-data-processing'],
    hints: ['data processing', 'databehandler', 'dpa agreement', 'processor agreement'],
    importance: 'Required when using third-party processors (hosting, analytics, SaaS).',
  },
  'security-headers': {
    label: 'Security Headers',
    type: 'headers',
    hints: [],
    importance: 'Protects against XSS, clickjacking, and downgrade attacks.',
  },
  'meta-tags': {
    label: 'Meta Tags',
    type: 'scan',
    hints: [],
    importance: 'Essential for SEO, social sharing, and mobile usability.',
  },
  hreflang: {
    label: 'Hreflang / Language Declaration',
    type: 'scan',
    hints: [],
    importance: 'Required for multilingual sites. Helps search engines serve the right language version.',
  },
};

function cscScoreLabel(s) {
  if (s >= 90) return 'A';
  if (s >= 70) return 'B';
  if (s >= 50) return 'C';
  return 'D';
}

async function cscFetch(urlStr, timeoutMs) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const resp = await fetch(urlStr, {
      signal: controller.signal,
      headers: {
        'User-Agent': 'ComplianceSiteCheck/2.0 (+https://hermes-passiv.pages.dev)',
        'Accept': 'text/html,application/xhtml+xml,*/*',
      },
      redirect: 'follow',
    });
    clearTimeout(timer);
    const text = await resp.text();
    // Cap HTML size to keep memory bounded on Workers
    return { ok: true, html: text.slice(0, 500000), url: resp.url, status: resp.status, headers: resp.headers };
  } catch (err) {
    clearTimeout(timer);
    if (err.name === 'AbortError') return { ok: false, error: 'Timeout' };
    return { ok: false, error: err.message };
  }
}

function cscDetectText(html, hints) {
  const lower = html.toLowerCase();
  return hints.some(h => lower.includes(h));
}

function cscHasHomepageLink(html, paths) {
  const lower = html.toLowerCase();
  return paths.some(p => lower.includes('href="' + p + '"') || lower.includes("href='" + p + "'"));
}

function cscCheckSecurityHeaders(headers) {
  const results = [];
  const get = (name) => headers.get(name) || '';
  const push = (check, ok, passDetail, warnDetail) =>
    results.push({ check, status: ok ? 'pass' : 'warn', detail: ok ? passDetail : warnDetail });

  const csp = get('content-security-policy');
  push('CSP', !!csp,
    'Content-Security-Policy header set.',
    'Content-Security-Policy header missing. CSP mitigates XSS and data injection.');

  const hsts = get('strict-transport-security');
  if (hsts) {
    const m = hsts.match(/max-age=(\d+)/i);
    const maxAge = m ? parseInt(m[1], 10) : 0;
    results.push({ check: 'HSTS', status: maxAge >= 31536000 ? 'pass' : 'warn',
      detail: maxAge >= 31536000 ? 'Strict-Transport-Security present with max-age >= 1 year.'
        : 'Strict-Transport-Security present but max-age < 1 year (recommend >= 31536000).' });
  } else {
    results.push({ check: 'HSTS', status: 'warn',
      detail: 'Strict-Transport-Security header missing. HSTS enforces HTTPS connections.' });
  }

  const xfo = get('x-frame-options');
  push('X-Frame-Options', !!xfo,
    'X-Frame-Options: ' + xfo + ' — prevents clickjacking.',
    'X-Frame-Options header missing. Your site can be embedded in iframes (clickjacking risk).');

  const xcto = get('x-content-type-options');
  push('X-Content-Type-Options', xcto.toLowerCase() === 'nosniff',
    'X-Content-Type-Options: nosniff — prevents MIME sniffing.',
    'X-Content-Type-Options: nosniff missing — browsers may execute scripts with wrong MIME types.');

  const rp = get('referrer-policy');
  results.push({ check: 'Referrer-Policy', status: rp ? 'pass' : 'info',
    detail: rp ? 'Referrer-Policy: ' + rp : 'Referrer-Policy header missing. Recommended for privacy control.' });

  const warnings = results.filter(r => r.status === 'warn');
  const passedCount = results.filter(r => r.status === 'pass').length;
  return {
    status: warnings.length === 0 ? 'pass' : 'warn',
    details: passedCount + '/' + results.length + ' header checks pass.' +
      (warnings.length ? ' Missing/weak: ' + warnings.map(w => w.check).join(', ') + '.' : ''),
    subResults: results,
  };
}

function cscCheckMetaTags(html) {
  const results = [];
  const lower = html.toLowerCase();

  const titleMatch = html.match(/<title[^>]*>([\s\S]*?)<\/title>/i);
  if (titleMatch && titleMatch[1].trim().length > 0) {
    const t = titleMatch[1].trim();
    results.push({ check: 'Title', status: t.length >= 30 && t.length <= 120 ? 'pass' : 'warn',
      detail: 'Title present (' + t.length + ' chars)' +
        (t.length < 30 ? ' — too short for SEO (< 30 chars)' : t.length > 120 ? ' — too long (> 120 chars)' : '') });
  } else {
    results.push({ check: 'Title', status: 'fail', detail: 'Missing <title> tag. Critical for SEO and accessibility.' });
  }

  const descMatch = html.match(/<meta[^>]+name=["']description["'][^>]+content=["']([^"']*)["']/i)
    || html.match(/<meta[^>]+content=["']([^"']*)["'][^>]+name=["']description["']/i);
  if (descMatch && descMatch[1].trim().length > 0) {
    const d = descMatch[1].trim();
    results.push({ check: 'Meta Description', status: d.length >= 50 && d.length <= 320 ? 'pass' : 'warn',
      detail: 'Description found (' + d.length + ' chars)' +
        (d.length < 50 ? ' — too short for SERP' : d.length > 320 ? ' — may be truncated in SERP' : '') });
  } else {
    results.push({ check: 'Meta Description', status: 'fail', detail: 'Missing meta description tag.' });
  }

  const vp = html.match(/<meta[^>]+name=["']viewport["'][^>]*>/i);
  results.push({ check: 'Viewport', status: vp ? 'pass' : 'fail',
    detail: vp ? 'Viewport meta tag present — mobile responsive.' : 'Missing viewport meta tag. Mobile rendering may break.' });

  const canon = html.match(/<link[^>]+rel=["']canonical["'][^>]*>/i);
  results.push({ check: 'Canonical', status: canon ? 'pass' : 'info',
    detail: canon ? 'Canonical link tag present.' : 'No canonical link tag (recommended).' });

  const robots = html.match(/<meta[^>]+name=["']robots["'][^>]*>/i);
  results.push({ check: 'Robots', status: robots ? 'pass' : 'info',
    detail: robots ? 'Robots meta tag present.' : 'No robots meta tag (default index/follow is fine).' });

  const ogTitle = lower.includes('property="og:title') || lower.includes("property='og:title");
  results.push({ check: 'OG Title', status: ogTitle ? 'pass' : 'info',
    detail: ogTitle ? 'Open Graph title found.' : 'No og:title — social shares may look generic.' });

  const ogDesc = lower.includes('property="og:description') || lower.includes("property='og:description");
  results.push({ check: 'OG Description', status: ogDesc ? 'pass' : 'info',
    detail: ogDesc ? 'Open Graph description found.' : 'No og:description tag.' });

  const passedCount = results.filter(r => r.status === 'pass').length;
  const warns = results.filter(r => r.status === 'warn');
  const fails = results.filter(r => r.status === 'fail');
  return {
    status: fails.length === 0 ? (warns.length === 0 ? 'pass' : 'warn') : 'fail',
    details: passedCount + '/' + results.length + ' checks pass.' +
      (fails.length ? ' Missing: ' + fails.map(f => f.check).join(', ') + '.' : '') +
      (warns.length ? ' Warnings: ' + warns.map(w => w.check).join(', ') + '.' : ''),
    subResults: results,
  };
}

function cscCheckHreflang(html) {
  const results = [];
  const langMatch = html.match(/<html[^>]+lang=["']([a-z]{2,3}(-[a-z]{2,4})?)["']/i);
  results.push({ check: 'HTML lang attribute', status: langMatch ? 'pass' : 'fail',
    detail: langMatch ? 'lang="' + langMatch[1] + '" present.' :
      'Missing lang attribute on <html>. Required for accessibility (WCAG 3.1.1) and SEO.' });

  const hreflangLinks = html.match(/<link[^>]+rel=["']alternate["'][^>]+hreflang=["']([^"']+)["'][^>]*>/gi);
  results.push({ check: 'Hreflang tags', status: hreflangLinks ? 'pass' : 'info',
    detail: hreflangLinks
      ? hreflangLinks.length + ' hreflang tag(s) found: ' +
        hreflangLinks.map(l => { const m = l.match(/hreflang=["']([^"']+)["']/i); return m ? m[1] : '?'; }).join(', ') + '.'
      : 'No hreflang alternate links (only needed for multilingual sites).' });

  const fails = results.filter(r => r.status === 'fail');
  const passedCount = results.filter(r => r.status === 'pass').length;
  return {
    status: fails.length === 0 ? 'pass' : 'fail',
    details: passedCount + '/' + results.length + ' checks pass.' +
      (fails.length ? ' Missing: ' + fails.map(f => f.check).join(', ') + '.' : ''),
    subResults: results,
  };
}

async function handleComplianceScan(request, url, env) {
  const corsHeaders = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Content-Type': 'application/json',
  };

  if (request.method === 'OPTIONS') return new Response(null, { status: 204, headers: corsHeaders });

  const targetParam = url.searchParams.get('url');
  if (!targetParam) {
    return new Response(JSON.stringify({ ok: false, error: 'Missing ?url= parameter' }), { status: 400, headers: corsHeaders });
  }

  let targetUrl;
  try {
    targetUrl = new URL(targetParam.startsWith('http') ? targetParam : 'https://' + targetParam);
    if (!['http:', 'https:'].includes(targetUrl.protocol)) throw new Error('bad protocol');
  } catch {
    return new Response(JSON.stringify({ ok: false, error: 'Invalid URL' }), { status: 400, headers: corsHeaders });
  }

  // Basic rate limit: one origin per IP per 10 seconds via KV if available, else allow.
  const TIMEOUT_MS = 10000;
  const MAX_PAGES = 12; // safety cap on total fetches

  try {
    const home = await cscFetch(targetUrl.toString(), TIMEOUT_MS);
    if (!home.ok) {
      return new Response(JSON.stringify({ ok: false, error: 'Cannot reach ' + targetUrl.host + ': ' + home.error }),
        { status: 502, headers: corsHeaders });
    }

    let fetchBudget = MAX_PAGES - 1;
    const passed = [];
    const failed = [];

    for (const key of Object.keys(CSC_CHECKS)) {
      const check = CSC_CHECKS[key];
      const result = { key, label: check.label, status: 'unknown', details: '' };

      if (key === 'cookie') {
        const found = cscDetectText(home.html, check.hints);
        result.status = found ? 'pass' : 'fail';
        result.details = found ? 'Cookie consent banner detected on homepage.'
          : 'No cookie consent banner detected. Some banners load via JS — verify manually.';
        (found ? passed : failed).push(result);
        continue;
      }
      if (key === 'meta-tags') {
        const r = cscCheckMetaTags(home.html);
        result.status = r.status === 'pass' ? 'pass' : 'fail';
        result.details = r.details; result.subResults = r.subResults;
        (result.status === 'pass' ? passed : failed).push(result);
        continue;
      }
      if (key === 'hreflang') {
        const r = cscCheckHreflang(home.html);
        result.status = r.status === 'pass' ? 'pass' : 'fail';
        result.details = r.details; result.subResults = r.subResults;
        (result.status === 'pass' ? passed : failed).push(result);
        continue;
      }
      if (key === 'security-headers') {
        const r = cscCheckSecurityHeaders(home.headers);
        result.status = r.status;
        result.details = r.details; result.subResults = r.subResults;
        (result.status === 'pass' ? passed : failed).push(result);
        continue;
      }

      // type: page
      let found = false, foundUrl = '';
      for (const path of check.paths) {
        if (fetchBudget <= 0) break;
        fetchBudget--;
        const pageUrl = new URL(path, targetUrl.toString()).toString();
        const pr = await cscFetch(pageUrl, TIMEOUT_MS);
        if (!pr.ok || pr.status >= 400) continue;
        if (cscDetectText(pr.html, check.hints)) { found = true; foundUrl = pr.url; break; }
        if (pr.status < 300) { found = true; foundUrl = pr.url; break; }
      }
      if (!found) found = cscHasHomepageLink(home.html, check.paths);

      result.status = found ? 'pass' : 'fail';
      result.details = found ? (foundUrl ? 'Found at ' + foundUrl : 'Link found on homepage')
        : 'Not found. Add a ' + check.label + ' page and link it from your footer.';
      (found ? passed : failed).push(result);
    }

    const total = Object.keys(CSC_CHECKS).length;
    const score = Math.round((passed.length / total) * 100);
    const grade = cscScoreLabel(score);

    // Anonymous scan counter (no URL stored) for /api/stats visibility.
    if (env && env.VISITS) {
      try {
        const cKey = 'csc-count';
        const prev = parseInt((await env.VISITS.get(cKey)) || '0', 10);
        await env.VISITS.put(cKey, String(prev + 1), { expirationTtl: 365 * 86400 });
      } catch { /* best-effort */ }
    }

    return new Response(JSON.stringify({
      ok: true,
      url: 'https://' + targetUrl.host,
      score,
      grade,
      passed: passed.length,
      failed: failed.length,
      total,
      results: { passed, failed },
      checks: CSC_CHECKS,
      version: '2.0',
    }), { status: 200, headers: corsHeaders });
  } catch (err) {
    return new Response(JSON.stringify({ ok: false, error: 'Scan failed: ' + (err.message || 'unknown') }),
      { status: 500, headers: corsHeaders });
  }
}

/* ── Clean Copy Pro Checkout — GET /api/checkout ────────────────
 * Returns the Lemon Squeezy checkout URL and whether Pro is available.
 * Until the LS product is created, checkout_url is null and the
 * frontend renders a "coming soon" state.
 * KV keys: cc-pro-checkout (Clean Copy Pro), pp-pro-checkout (Page Profile
 * Pro) — set via tools/set-checkout-url.sh after running lemon-setup.js.
 * ?product=pp returns the Page Profile Pro entry; default is clean-copy-pro.
 */
async function handleCheckout(url, env) {
  const corsHeaders = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Content-Type': 'application/json',
  };

  const which = url.searchParams.get('product') === 'pp' ? 'pp' : 'cc';
  const kvKey = which === 'pp' ? 'pp-pro-checkout' : 'cc-pro-checkout';
  const meta = which === 'pp'
    ? {
        product: 'page-profile-pro',
        price: '$19/year',
        note: 'Pro adds comparison mode, batch mode and client-ready HTML reports to the page-profile CLI.',
      }
    : {
        product: 'clean-copy-pro',
        price: '$19/year',
        note: 'One license covers all 7 surfaces: Chrome, Firefox, Edge, CLI, VS Code, Obsidian, GitHub Action.',
      };

  let checkoutUrl = null;
  let live = false;
  try {
    checkoutUrl = (await env.VISITS.get(kvKey)) || null;
    live = !!checkoutUrl;
  } catch { /* KV not available */ }

  return new Response(JSON.stringify({
    ok: true,
    live,
    checkout_url: checkoutUrl,
    ...meta,
  }), { status: 200, headers: corsHeaders });
}

/* ================= bugbottle live demo ================= */


const BB_MAX_MESSAGE = 4000;
const BB_REPORT_TYPES = ['bug', 'idea', 'other'];
const BB_MAX_SCREENSHOT_DATA_URL = 2_900_000;
const BB_DAY_LIMIT = 200;
const BB_PER_TYPE_LIMIT = 50;

function bbJson(obj, status = 200) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: {
      'Content-Type': 'application/json',
      'Access-Control-Allow-Origin': '*',
      'Cache-Control': 'no-store',
    },
  });
}

function bbDay() {
  return new Date().toISOString().slice(0, 10);
}

async function handleBugbottleDemo(request, url, env) {
  if (request.method === 'OPTIONS') {
    return new Response(null, { status: 204, headers: { 'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Methods': 'POST, OPTIONS', 'Access-Control-Allow-Headers': 'Content-Type' } });
  }
  // GET: the demo page reads back recent reports (no personal data — only what
  // reporters deliberately sent through the public demo form).
  if (request.method === 'GET') {
    try {
      const day = bbDay();
      const list = [];
      let cursor = null;
      do {
        const page = await env.VISITS.list({ prefix: `bb:${day}:r:`, cursor });
        for (const k of page.keys) {
          const v = await env.VISITS.get(k.name);
          if (v) list.push(JSON.parse(v));
        }
        cursor = page.list_complete ? null : page.cursor;
      } while (cursor && list.length < 25);
      list.sort((a, b) => (b.at || 0) - (a.at || 0));
      return bbJson({ ok: true, reports: list.slice(0, 25) });
    } catch {
      return bbJson({ ok: true, reports: [] });
    }
  }
  if (request.method !== 'POST') {
    return bbJson({ ok: false, error: 'POST only' }, 405);
  }

  let body;
  try {
    body = await request.json();
  } catch {
    return bbJson({ ok: false, error: 'Body must be JSON.' }, 400);
  }

  // --- validation mirroring bugbottle/server rules ---
  const message = typeof body.message === 'string' ? body.message.trim().slice(0, BB_MAX_MESSAGE) : '';
  if (!message) return bbJson({ ok: false, error: 'Write a message first.' }, 400);

  const type = BB_REPORT_TYPES.includes(body.type) ? body.type : 'other';

  const ctxIn = body.context && typeof body.context === 'object' ? body.context : {};
  const context = {
    page: String(ctxIn.page ?? '').slice(0, 300),
    viewport: String(ctxIn.viewport ?? ''),
    language: String(ctxIn.language ?? '').slice(0, 20),
  };

  // screenshot: only accept a data URL within limits; never fail the report on it
  let screenshotStored = false;
  let screenshotBytes = 0;
  if (typeof body.screenshotDataUrl === 'string' && body.screenshotDataUrl.length > 0) {
    if (body.screenshotDataUrl.length > BB_MAX_SCREENSHOT_DATA_URL) {
      return bbJson({ ok: false, error: 'Screenshot too large.' }, 413);
    }
    if (!body.screenshotDataUrl.startsWith('data:image/png;base64,')) {
      return bbJson({ ok: false, error: 'Only PNG data URLs are accepted.' }, 415);
    }
    screenshotStored = true;
    screenshotBytes = Math.floor((body.screenshotDataUrl.length - 22) * 0.75);
  }

  // console entries: cap count and size, keep them as plain objects
  let consoleEntries = Array.isArray(body.console) ? body.console : [];
  consoleEntries = consoleEntries.slice(0, 100).map((e) => ({
    level: e && (e.level === 'error' || e.level === 'warn') ? e.level : 'log',
    text: String((e && e.text) || '').slice(0, 500),
  }));

  // --- rate limiting (KV counters, self-expiring) ---
  const day = bbDay();
  const dayKey = `bb:${day}:count`;
  const dayCount = parseInt((await env.VISITS.get(dayKey)) || '0', 10);
  if (dayCount >= BB_DAY_LIMIT) {
    return bbJson({ ok: false, error: 'Demo is at its daily limit of reports. Try again tomorrow.' }, 429);
  }

  // --- store ---
  const id = crypto.randomUUID().slice(0, 8);
  const record = {
    id,
    type,
    message,
    context,
    consoleCount: consoleEntries.length,
    consoleSample: consoleEntries.slice(-3),
    screenshot: screenshotStored ? { bytes: screenshotBytes } : null,
    at: Date.now(),
  };
  await env.VISITS.put(`bb:${day}:r:${id}:${Date.now()}`, JSON.stringify(record), { expirationTtl: 30 * 86400 });
  await env.VISITS.put(dayKey, String(dayCount + 1), { expirationTtl: 2 * 86400 });

  return bbJson({ ok: true, id }, 201);
}

/**
 * URL Inspector — fetch URL, trace redirect chain, return headers
 * GET /api/url-inspect?url=https://example.com
 */
async function handleUrlInspect(request, url) {
  const corsHeaders = {
    'access-control-allow-origin': '*',
    'access-control-allow-methods': 'GET, OPTIONS',
    'access-control-allow-headers': 'Content-Type',
    'content-type': 'application/json',
  };
  if (request.method === 'OPTIONS') return new Response(null, { status: 204, headers: corsHeaders });

  const targetUrlParam = url.searchParams.get('url');
  if (!targetUrlParam) {
    return new Response(JSON.stringify({ error: 'Missing ?url= parameter' }), { status: 400, headers: corsHeaders });
  }
  try { new URL(targetUrlParam); } catch (_) {
    return new Response(JSON.stringify({ error: 'Invalid URL' }), { status: 400, headers: corsHeaders });
  }

  const redirects = [];
  let currentUrl = targetUrlParam;
  let finalResponse = null;
  const MAX_HOPS = 15;

  for (let hop = 0; hop <= MAX_HOPS; hop++) {
    const response = await fetch(currentUrl, {
      method: 'GET',
      redirect: 'manual',
      headers: { 'User-Agent': 'URLInspector/1.0 (Cloudflare Worker; https://hermes-passiv.pages.dev)' }
    });

    const statusCode = response.status;
    const location = response.headers.get('location');
    const hopHeaders = {};
    response.headers.forEach((value, key) => {
      if (Object.keys(hopHeaders).length < 80) {
        hopHeaders[key] = value;
      }
    });

    if (statusCode >= 300 && statusCode < 400 && statusCode !== 304 && location) {
      redirects.push({
        hop: hop + 1,
        url: currentUrl,
        status: statusCode,
        statusText: response.statusText,
        location: location,
        headers: hopHeaders,
      });
      try {
        currentUrl = new URL(location, currentUrl).href;
      } catch (_) {
        return new Response(JSON.stringify({ error: 'Invalid redirect location', redirects, finalUrl: currentUrl }), {
          status: 200, headers: corsHeaders,
        });
      }
    } else {
      finalResponse = {
        url: currentUrl,
        status: statusCode,
        statusText: response.statusText,
        headers: hopHeaders,
      };
      break;
    }
  }

  if (!finalResponse) {
    finalResponse = {
      url: currentUrl,
      status: 0,
      statusText: 'Too many redirects (> ' + MAX_HOPS + ' hops)',
      headers: {},
    };
  }

  // Extract key security headers for a quick overview
  const secHeaders = [
    'strict-transport-security', 'content-security-policy',
    'x-content-type-options', 'x-frame-options', 'x-xss-protection',
    'referrer-policy', 'permissions-policy', 'access-control-allow-origin',
  ];
  const presentSecurity = {};
  for (const h of secHeaders) {
    if (finalResponse.headers[h]) presentSecurity[h] = finalResponse.headers[h];
  }

  const result = {
    inspectUrl: targetUrlParam,
    finalUrl: finalResponse.url,
    totalRedirects: redirects.length,
    redirectChain: redirects,
    finalStatus: finalResponse.status,
    finalStatusText: finalResponse.statusText,
    securityHeaders: presentSecurity,
    allHeaders: finalResponse.headers,
    ssl: await fetchSslInfo(finalResponse.url),
    message: redirects.length > 0
      ? `→ ${redirects[redirects.length - 1].url} (${redirects.length} redirect${redirects.length > 1 ? 's' : ''})`
      : 'No redirects',
  };

  return new Response(JSON.stringify(result, null, 2), { status: 200, headers: corsHeaders });
}

/**
 * Fetch live TLS certificate info for the final URL's host via dnslabs.com
 * (free JSON API, no key, performs a real handshake). Best-effort: any failure
 * returns { available: false } so the main inspect result is never broken.
 */
async function fetchSslInfo(finalUrl) {
  try {
    const host = new URL(finalUrl).hostname;
    if (!finalUrl.startsWith('https://')) {
      return { available: false, reason: 'Final URL is not HTTPS' };
    }
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 8000);
    const res = await fetch(`https://www.dnslabs.com/api/ssl?q=${encodeURIComponent(host)}`, {
      signal: controller.signal,
      headers: { 'User-Agent': 'URLInspector/1.0 (Cloudflare Worker)' },
    });
    clearTimeout(timer);
    if (!res.ok) return { available: false, reason: 'SSL lookup unavailable (HTTP ' + res.status + ')' };
    const data = await res.json();
    const cert = data.cert || {};
    return {
      available: true,
      host,
      validTo: cert.not_after || null,
      daysRemaining: typeof cert.days_remaining === 'number' ? cert.days_remaining : null,
      issuer: cert.issuer_cn || (data.chain && data.chain[0] && data.chain[0].issuer_cn) || null,
      tlsVersion: data.tls_version || null,
      chainTrusted: !!data.chain_trusted,
      checks: (data.checks || []).map(c => ({ id: c.id, label: c.label, status: c.status, detail: c.detail })),
      source: 'dnslabs.com live TLS handshake',
    };
  } catch (_) {
    return { available: false, reason: 'SSL lookup failed or timed out' };
  }
}
