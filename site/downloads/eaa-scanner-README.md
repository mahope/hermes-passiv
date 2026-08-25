# eaa-scanner

Universal **EAA / WCAG 2.1 AA** compliance scanner for any website — WordPress,
Shopify, Webflow, Next.js, Squarespace, Wix, or hand-written HTML.

Zero dependencies. Pure Python standard library. Python 3.8+.

## Why

The European Accessibility Act (EAA) applies from 28 June 2025 to most
consumer-facing digital services in the EU. This tool gives you a fast,
automated first check of the issues that matter most:

- images missing alt text
- form fields without labels
- empty links / empty buttons
- duplicate `id` attributes (breaks label/aria references)
- iframes without titles, tables without headers
- missing page title / `lang` / viewport meta
- heading structure problems (no h1, skipped levels)
- links opening new windows without warning
- focusable elements hidden with `aria-hidden`
- inline text below the WCAG AA contrast minimum (computed, not guessed)

## Install

```bash
pip install eaa-scanner
```

Or run directly from source (no install):

```bash
git clone <this repo> && cd scanner
python scan.py https://example.com
```

## Usage

```bash
# scan one or more URLs
eaa-scan https://example.com https://example.com/pricing

# scan local HTML files
eaa-scan page.html other.html

# machine-readable output
eaa-scan --json https://example.com

# CI mode: fail the build on warnings too
eaa-scan --fail-on warning https://example.com

# whole-site audit: crawl up to N same-origin pages
eaa-scan https://example.com --crawl 15
```

Exit code is `0` when clean, `1` when findings at `--fail-on` severity exist
(default: errors) — drop it straight into CI.

## GitHub Actions

A ready-made workflow is published alongside this README:
[`eaa-scan-github-action.yml`](https://hermes-passiv.pages.dev/downloads/eaa-scan-github-action.yml).
Drop it into `.github/workflows/eaa-scan.yml`, edit the `PAGES` list, and every
push / pull request / weekly schedule runs the scanner with `--fail-on warning`.
The template also includes an optional `crawl-audit` job that runs
`--crawl 25` on schedules for a whole-site report.

## Example output

```
EAA/WCAG report — https://example.com
Score: 88/100  Grade B (errors=1, warnings=0, notices=0)
------------------------------------------------------------
[ERROR  ] IMG_ALT: 2 image(s) missing alt text
           e.g. hero.png
...
Note: automated checks catch ~30-40% of accessibility issues.
A full manual checklist is still required for EAA conformance.
```

## Desktop app (optional)

A desktop version (Electron) is available as source:
[`eaa-scanner-desktop-src-1.1.1.zip`](https://hermes-passiv.pages.dev/downloads/eaa-scanner-desktop-src-1.1.1.zip).

```bash
unzip eaa-scanner-desktop-src-1.1.1.zip && cd desktop
npm install
npm start
```

Note: on some npm versions the Electron post-install script is blocked
("Electron failed to install correctly"). Fix with:

```bash
node node_modules/electron/install.js   # or: npm rebuild electron
npm start
```

Requires Node.js 18+. The scanner core itself is pure JavaScript with no
runtime dependencies — `scanner-core.js` can also be used directly in Node.

## Library use

```python
from eaa_scanner import scan_url, scan_html

report = scan_url("https://example.com")
print(report["score"], report["grade"])
for f in report["findings"]:
    print(f["severity"], f["rule_id"], f["message"])
```

## Limits

Automated checks catch roughly 30–40% of accessibility issues. A passing score
is **not** an EAA conformance statement — pair it with manual testing
(keyboard navigation, screen reader).

## License

MIT.
