#!/usr/bin/env node
'use strict';
const { scanHtml, scanUrl } = require('./index.js');
const fs = require('fs');

function usage() {
  console.error(`Usage: eaa-scan <url-or-file>... [--json] [--fail-on error|warning] [--crawl N]

Scan web pages or HTML files for EAA / WCAG 2.1 AA issues.
Works on any CMS — no plugins, no server access.

Examples:
  eaa-scan https://example.com
  eaa-scan https://example.com --json
  eaa-scan page.html other.html --fail-on warning   # CI: exit 1 if warnings
  eaa-scan https://example.com --crawl 15           # crawl up to 15 pages, site report`);
}

async function main() {
  const args = process.argv.slice(2);
  const json = args.includes('--json');
  const failIdx = args.indexOf('--fail-on');
  let failOn = null;
  if (failIdx !== -1) {
    failOn = args[failIdx + 1];
    if (!['error', 'warning'].includes(failOn)) {
      console.error('--fail-on must be "error" or "warning"'); process.exit(2);
    }
    args.splice(failIdx, 2);
  }
  const crawlIdx = args.indexOf('--crawl');
  let crawlMax = null;
  if (crawlIdx !== -1) {
    crawlMax = parseInt(args[crawlIdx + 1], 10);
    if (!Number.isFinite(crawlMax) || crawlMax < 1 || crawlMax > 200) {
      console.error('--crawl must be a number between 1 and 200'); process.exit(2);
    }
    args.splice(crawlIdx, 2);
  }
  const targets = args.filter(a => !a.startsWith('-'));
  if (!targets.length) { usage(); process.exit(2); }

  const reports = [];
  let exitCode = 0;
  for (const t of targets) {
    let rep;
    try {
      if (crawlMax && /^https?:\/\//.test(t)) {
        const { pages, aggregate } = await require('./index.js')
          .crawlSite(t, crawlMax, 15000, {
            onPage: (r, i, max) =>
              process.stderr.write(`  [${i}/${max}] ${r.ok ? r.score : 'ERR'} ${r.target}\n`),
          });
        rep = { ok: true, target: t, crawl: true, ...aggregate, pages };
        if (json) console.log(JSON.stringify(rep, null, 2));
        if (!json) {
          console.log(`\nSITE REPORT — ${t}`);
          console.log(`  Pages scanned: ${rep.pagesScanned}${rep.pagesFailed ? ` (${rep.pagesFailed} failed)` : ''}`);
          console.log(`  Average score: ${rep.averageScore}/100 (${rep.grade})`);
          console.log(`  Totals: ${rep.totalErrors} errors, ${rep.totalWarnings} warnings, ${rep.totalNotices} notices`);
          if (rep.worstPage)
            console.log(`  Worst page: ${rep.worstPage.score}/100 — ${rep.worstPage.target}`);
          if (rep.rulesByFrequency.length) {
            console.log('  Issues by frequency:');
            for (const [rule, n] of rep.rulesByFrequency.slice(0, 8))
              console.log(`    ${String(n).padStart(4)}  ${rule}`);
          }
          console.log('\n  Per-page findings (--json for full detail):');
          for (const p of rep.pages.filter(p => p.ok && p.findings.length))
            console.log(`    ${p.score}/100 ${p.target}`);
        }
        reports.push(rep);
        continue;
      }
      rep = /^https?:\/\//.test(t) ? await scanUrl(t)
        : scanHtml(fs.readFileSync(t, 'utf8'));
      rep.target = t;
    } catch (e) {
      rep = { ok: false, target: t, error: e.message, score: null,
        findings: [], summary: {} };
    }
    reports.push(rep);
    if (json) { console.log(JSON.stringify(rep, null, 2)); continue; }
    if (!rep.ok) {
      console.log(`✖ ${t}: ERROR ${rep.error}`);
      exitCode = 2; continue;
    }
    console.log(`\n${t}`);
    console.log(`  Score: ${rep.score}/100 (${rep.grade}) — ${rep.summary.errors} errors, ${rep.summary.warnings} warnings, ${rep.summary.notices} notices`);
    for (const f of rep.findings) {
      const icon = f.severity === 'error' ? '✖' : f.severity === 'warning' ? '⚠' : '·';
      console.log(`  ${icon} [${f.severity.toUpperCase()}] ${f.rule_id}: ${f.message}`);
      for (const ex of f.examples.slice(0, 3)) console.log(`      e.g. ${ex}`);
    }
  }
  if (!failOn && exitCode === 0) {
    // non-CI default: exit 1 only on scan failures
  }
  if (failOn) {
    const bad = reports.some(r => r.ok &&
      (r.summary.errors > 0 || (failOn === 'warning' && r.summary.warnings > 0)));
    if (bad || reports.some(r => !r.ok)) process.exit(1);
  }
  process.exit(exitCode);
}

main().catch(e => { console.error(e); process.exit(2); });
