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

# whole-site audit: crawl up to N same-origin pages (1-200)
eaa-scan https://example.com --crawl 15
```

### Site crawl (`--crawl N`)

One command scans a whole site: it starts at your URL, follows same-origin
links breadth-first (assets like .zip/.pdf/images are skipped), and returns a
combined report — average score, total issues ranked by frequency across the
site, and the worst-scoring page. Combine with `--json` for machine output.
Progress goes to stderr, so you can pipe the report.

Exit code is `0` when clean, `1` when findings at `--fail-on` severity exist
(default: errors) — drop it straight into CI.

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
