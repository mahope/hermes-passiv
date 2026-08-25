/**
 * scanner.js — Electron wrapper for the EAA scanner core
 * Same scanHtml function as the npm package, plus site crawl support.
 */
'use strict';

const { scanHtml } = require('./scanner-core.js');

async function scanUrl(url, timeoutMs = 15000) {
  for (let i = 0; i < 5; i++) {
    const ctrl = new AbortController();
    const t = setTimeout(() => ctrl.abort(), timeoutMs);
    try {
      const res = await fetch(url, {
        redirect: 'manual',
        headers: { 'User-Agent': 'EAA-ComplianceScanner/1.1 (desktop)' },
        signal: ctrl.signal,
      });
      if ([301, 302, 303, 307, 308].includes(res.status)) {
        const loc = res.headers.get('location');
        if (loc) url = new URL(loc, url).href;
        res.body && res.body.cancel();
        continue;
      }
      const html = (await res.text()).slice(0, 2_000_000);
      const rep = scanHtml(html);
      rep.url = url;
      rep.html = html; // retained so crawlSite can extract same-origin links
      return rep;
    } finally { clearTimeout(t); }
  }
  return { ok: false, error: 'too many redirects', score: null, findings: [], summary: {} };
}

// --- link extraction + site crawl (parity with npm package v1.1.0) -----------
function extractLinks(html, baseUrl) {
  const base = new URL(baseUrl);
  const out = new Set();
  const re = /<a\s[^>]*href\s*=\s*("([^"]*)"|'([^']*)')/gi;
  let m;
  while ((m = re.exec(html)) !== null) {
    const href = m[2] !== undefined ? m[2] : m[3];
    if (!href || /^(mailto:|tel:|javascript:|data:|#)/i.test(href.trim())) continue;
    if (/\.(zip|tar|gz|tgz|pdf|png|jpe?g|gif|svg|webp|ico|css|js|json|xml|woff2?|mp4|mp3|dmg|exe|deb|appimage|whl)(\?|$)/i.test(href)) continue;
    try {
      const u = new URL(href, base);
      if (u.protocol !== 'http:' && u.protocol !== 'https:') continue;
      if (u.hostname !== base.hostname) continue; // same-site only
      u.hash = '';
      out.add(u.href);
    } catch { /* malformed URL — skip */ }
  }
  return [...out];
}

const GRADE = s => s >= 90 ? 'A' : s >= 75 ? 'B' : s >= 55 ? 'C' : 'D';

/**
 * Crawl a site: start at startUrl, follow same-origin links up to maxPages.
 * Returns { pages: [report,...], aggregate }. Page failures are reported,
 * never thrown.
 */
async function crawlSite(startUrl, maxPages = 10, timeoutMs = 15000, onPage = null) {
  const seen = new Set();
  const queue = [new URL(startUrl).href];
  const pages = [];
  while (queue.length && seen.size < maxPages) {
    const url = queue.shift();
    if (seen.has(url)) continue;
    seen.add(url);
    const rep = await scanUrl(url, timeoutMs);
    rep.target = url;
    pages.push(rep);
    if (onPage) { try { onPage(rep, seen.size, maxPages); } catch { /* ignore */ } }
    await new Promise(r => setTimeout(r, 250)); // be polite
    if (rep.ok && rep.html) {
      for (const link of extractLinks(rep.html, url))
        if (!seen.has(link)) queue.push(link);
    }
  }
  const okPages = pages.filter(p => p.ok);
  const totals = { errors: 0, warnings: 0, notices: 0 };
  const byRule = {};
  for (const p of okPages) {
    totals.errors += p.summary.errors || 0;
    totals.warnings += p.summary.warnings || 0;
    totals.notices += p.summary.notices || 0;
    for (const f of p.findings)
      byRule[f.rule_id] = (byRule[f.rule_id] || 0) + (f.count || 1);
  }
  const failed = pages.length - okPages.length;
  const avgScore = okPages.length
    ? Math.round(okPages.reduce((s, p) => s + p.score, 0) / okPages.length) : null;
  const worst = okPages.length ? okPages.reduce((w, p) => p.score < w.score ? p : w) : null;
  const aggregate = {
    pagesScanned: pages.length, pagesFailed: failed,
    averageScore: avgScore,
    grade: avgScore === null ? null : GRADE(avgScore),
    totalErrors: totals.errors, totalWarnings: totals.warnings,
    totalNotices: totals.notices,
    rulesByFrequency: Object.entries(byRule).sort((a, b) => b[1] - a[1]),
    worstPage: worst ? { target: worst.target, score: worst.score } : null,
  };
  return { pages, aggregate };
}

module.exports = { scanUrl, scanHtml, extractLinks, crawlSite };
