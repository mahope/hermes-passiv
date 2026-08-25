# @mahope/eaa-scanner

Universal **EAA / WCAG 2.1 AA** compliance scanner for the command line.
Works on **any** website — WordPress, Shopify, Webflow, Next.js, Squarespace,
hand-written HTML — no plugins or server access required.

Zero dependencies. Node ≥ 18.

## Quick start

```bash
# scan any URL
npx --yes --registry <not-on-npm-yet>   # see "Install" below
```

### Install

Not published to npm yet — install directly from the project's download page:

```bash
npm install -g https://hermes-passiv.pages.dev/downloads/mahope-eaa-scanner-1.0.0.tgz
eaa-scan https://example.com
```

## Usage

```bash
eaa-scan <url-or-file>... [--json] [--fail-on error|warning] [--crawl N]

eaa-scan https://example.com            # human-readable report
eaa-scan https://example.com --json     # machine-readable (pipe to jq)
eaa-scan page.html --fail-on warning    # CI mode: exit 1 if warnings found
eaa-scan https://example.com --crawl 15 # whole-site audit: crawl up to 15 pages
```

### Site crawl (`--crawl N`)

One command scans up to N pages of a site (follows same-origin HTML links,
skips assets) and prints a **site report**: average score, total
errors/warnings/notices, issues ranked by frequency across the site, the worst
page, and per-page scores. `--json` gives the full machine-readable structure
(`aggregate` fields + per-page reports).

```bash
$ eaa-scan https://example.com --crawl 10

SITE REPORT — https://example.com
  Pages scanned: 8
  Average score: 91/100 (A)
  Totals: 3 errors, 4 warnings, 0 notices
  Worst page: 76/100 — https://example.com/pricing
  Issues by frequency:
       5  IMG_ALT
       2  CONTRAST
```

Library use: `const { crawlSite } = require('@mahope/eaa-scanner')`.

## What it checks

22 rules covering the WCAG 2.1 AA subset most relevant to the European
Accessibility Act: missing alt text (including image submit buttons),
unlabeled form fields, empty links and buttons, duplicate IDs, missing
title/lang/viewport, heading structure, iframe titles, table headers,
target="_blank" warnings, aria-hidden on focusable elements, fixed px fonts,
inline colour contrast (WCAG 1.4.3, computed with real relative-luminance
maths), video without caption tracks (1.2.2), audio without a transcript
signal (1.2.1), autoplaying media without pause/mute (1.4.2), deprecated
marquee/blink content (2.2.2), and positive tabindex values (2.4.3).

Each report gives a 0–100 score with a letter grade and concrete findings.

## Library use

```js
const { scanHtml, scanUrl } = require('@mahope/eaa-scanner');
const report = await scanUrl('https://example.com');
console.log(report.score, report.grade);
```

## License

MIT
