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
    if (path === '/api/profile') return handleProfile(request, url);

    // === Route: waitlist signup ===
    if (path === '/api/waitlist') return handleWaitlist(request, env);

    // === Route: cookieless visit tracking ===
    if (path === '/api/track') return handleTrack(request, env);
    if (path === '/api/stats') return handleStats(url, env);

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

    // === Route: Lemon Squeezy webhook (auto-issues license keys) ===
    if (path === '/api/lemon-webhook') return handleLemonWebhook(request, env);

    // === Route: IndexNow key verification (key file generated on the fly) ===
    if (path.startsWith('/indexnow-')) {
      return new Response(path.slice('/indexnow-'.length), {
        headers: { 'Content-Type': 'text/plain; charset=utf-8' },
      });
    }

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
async function handleProfile(request, url) {
  const headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Content-Type': 'application/json',
  };

  if (request.method === 'OPTIONS') return new Response(null, { status: 204, headers });

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
    const valid = /^[^\s@]{1,64}@[^\s@]+\.[^\s@]{2,}$/.test(email);
    if (!valid) {
      return jsonResp({ ok: false, error: 'Please enter a valid email address.' }, 400);
    }

    const digest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode('wl:' + email));
    const key = 'wl:' + [...new Uint8Array(digest)].map(b => b.toString(16).padStart(2, '0')).join('');

    const isNew = !(await env.VISITS.get(key));
    if (isNew) {
      // store the email so Mads can import the list later; KV value = email
      await env.VISITS.put(key, email, { expirationTtl: 365 * 86400 });
      // counter for quick reads
      const cKey = 'wl-count';
      const prev = parseInt((await env.VISITS.get(cKey)) || '0', 10);
      await env.VISITS.put(cKey, String(prev + 1), { expirationTtl: 365 * 86400 });
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
  let licenses_issued = null;
  try { licenses_issued = parseInt((await env.VISITS.get('t:all:licenses-issued')) || '0', 10); } catch {}

  return jsonResp({ ok: true, days, stats: filtered, waitlist, licenses_issued });
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
