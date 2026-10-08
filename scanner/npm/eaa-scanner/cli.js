#!/usr/bin/env node
'use strict';
const { scanHtml, scanUrl } = require('./index.js');
const fs = require('fs');

const RULE_DESCRIPTIONS = {
  IMG_ALT: 'Images must have alt text',
  FORM_LABEL: 'Form inputs must have labels',
  LINK_TEXT: 'Links must have discernible text',
  BUTTON_TEXT: 'Buttons must have discernible text',
  TARGET_BLANK: 'Links opening in new windows must warn users',
  DUP_ID: 'IDs must be unique',
  IFRAME_TITLE: 'Iframes must have a title',
  TABLE_HEADER: 'Tables must have header cells',
  DOC_TITLE: 'Page must have a non-empty title',
  HTML_LANG: 'Html element must have a lang attribute',
  VIEWPORT: 'Viewport meta must allow zoom',
  HEADING_H1: 'Page must have an h1',
  HEADING_SKIP: 'Heading levels must not skip',
  FIXED_PX_FONTS: 'Font sizes should use relative units',
  CONTRAST: 'Text must meet WCAG AA contrast minimum',
  INPUT_TYPE_IMAGE_ALT: 'Image submit buttons must have alt text',
  MARQUEE_BLINK: 'Blinking/moving content must be pausable',
  AUTOPLAY_MEDIA: 'Audio/video must not autoplay',
  ARIA_HIDDEN_FOCUS: 'aria-hidden elements must not be focusable',
  POSITIVE_TABINDEX: 'tabindex must not be positive',
  AUDIO_TRANSCRIPT: 'Audio must have transcripts',
  VIDEO_TRACKS: 'Video must have captions',
};

function usage() {
  console.error(`Usage: eaa-scan <url-or-file>... [--json] [--sarif] [--fail-on error|warning|never] [--crawl N]

Scan web pages or HTML files for EAA / WCAG 2.1 AA issues.
Works on any CMS — no plugins, no server access.

Examples:
  eaa-scan https://example.com
  eaa-scan https://example.com --json
  eaa-scan page.html other.html --fail-on warning   # CI: exit 1 if warnings
  eaa-scan https://example.com --crawl 15           # crawl up to 15 pages, site report
  eaa-scan https://example.com --sarif              # SARIF 2.1.0 for GitHub code scanning`);
}
async function main() {
  const args = process.argv.slice(2);
  const json = args.includes('--json');
  const sarif = args.includes('--sarif');
  const failIdx = args.indexOf('--fail-on');
  let failOn = null;
  if (failIdx !== -1) {
    failOn = args[failIdx + 1];
    // `never` er dokumenteret i det workflow vi sender ud til kunderne
    // (`FAIL_ON warning | error | never`), men CLI'en afviste det med exit 2 —
    // en indstilling der ser gyldig ud og fejler med det samme. Den betyder
    // "rapportér, men døm ikke", hvilket er præcis hvad SARIF-kørsler i CI vil
    // have: fundene skal i Security-taben, jobbet skal ikke være rødt.
    if (!['error', 'warning', 'never'].includes(failOn)) {
      console.error('--fail-on must be "error", "warning" or "never"'); process.exit(2);
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
  const sarifResults = [];
  const sarifRules = new Map();
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
        if (sarif) {
          for (const p of rep.pages) {
            if (!p.ok) continue;
            for (const f of p.findings) {
              sarifRules.set(f.rule_id, RULE_DESCRIPTIONS[f.rule_id] || f.rule_id);
              sarifResults.push({
                ruleId: f.rule_id,
                level: f.severity === 'error' ? 'error' : f.severity === 'warning' ? 'warning' : 'note',
                message: { text: f.message },
                locations: [{ physicalLocation: { artifactLocation: { uri: p.target } } }],
              });
            }
          }
        }
        if (json) console.log(JSON.stringify(rep, null, 2));
        if (!json && !sarif) {
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
    if (sarif && rep.ok) {
      for (const f of rep.findings) {
        sarifRules.set(f.rule_id, RULE_DESCRIPTIONS[f.rule_id] || f.rule_id);
        sarifResults.push({
          ruleId: f.rule_id,
          level: f.severity === 'error' ? 'error' : f.severity === 'warning' ? 'warning' : 'note',
          message: { text: f.message },
          locations: [{ physicalLocation: { artifactLocation: { uri: rep.target } } }],
        });
      }
    }
    // En side der ikke kunne hentes er en fejl i begge udgaver — også når
    // rapporten skal være SARIF, hvor konsol-linjen er skjult. Uden denne
    // linje forlod `--sarif`-kørslen med 0 på en URL den aldrig nåede.
    if (!rep.ok) exitCode = 2;
    if (json) { console.log(JSON.stringify(rep, null, 2)); continue; }
    if (sarif) continue;
    if (!rep.ok) {
      console.log(`✖ ${t}: ERROR ${rep.error}`);
      continue;
    }
    console.log(`\n${t}`);
    console.log(`  Score: ${rep.score}/100 (${rep.grade}) — ${rep.summary.errors} errors, ${rep.summary.warnings} warnings, ${rep.summary.notices} notices`);
    for (const f of rep.findings) {
      const icon = f.severity === 'error' ? '✖' : f.severity === 'warning' ? '⚠' : '·';
      console.log(`  ${icon} [${f.severity.toUpperCase()}] ${f.rule_id}: ${f.message}`);
      for (const ex of f.examples.slice(0, 3)) console.log(`      e.g. ${ex}`);
    }
  }
  // En side der ikke kunne hentes er et fund, ikke en mangel på fund: uden
  // denne linje står en død URL i Security-taben som "ingen resultater", og et
  // CI-job der ikke kunne nå kundens vigtigste side ser grønt ud.
  if (sarif) {
    for (const r of reports) {
      if (r.ok) continue;
      sarifRules.set('SCAN_ERROR', 'The page could not be fetched or parsed');
      sarifResults.push({
        ruleId: 'SCAN_ERROR',
        level: 'error',
        message: { text: `Could not scan ${r.target}: ${r.error || 'unknown error'}` },
        locations: [{ physicalLocation: { artifactLocation: { uri: String(r.target) } } }],
      });
    }
  }
  // Rapporten skrives FØR dømmen. Modsatte rækkefølge (dom først) betød, at en
  // CI-kørsel med fund forlod jobbet uden at skrive SARIF'et — altså præcis de
  // kørsler hvor Security-taben har mest brug for at se fundene.
  if (sarif) {
    const sarifDoc = {
      '$schema': 'https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json',
      version: '2.1.0',
      runs: [{
        tool: {
          driver: {
            name: 'eaa-scanner',
            informationUri: 'https://mahope.tools/scan',
            rules: [...sarifRules.entries()].map(([id, desc]) => ({
              id,
              shortDescription: { text: desc },
            })),
          },
        },
        results: sarifResults,
      }],
    };
    console.log(JSON.stringify(sarifDoc, null, 2));
  }
  if (failOn && failOn !== 'never') {
    const bad = reports.some(r => r.ok &&
      (r.summary.errors > 0 || (failOn === 'warning' && r.summary.warnings > 0)));
    if (bad || reports.some(r => !r.ok)) process.exit(1);
  }
  process.exit(exitCode);
}

main().catch(e => { console.error(e); process.exit(2); });
