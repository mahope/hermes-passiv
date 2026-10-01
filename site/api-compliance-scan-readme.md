# Compliance Scan API

Free REST API: send a URL, get a 9-point EU compliance report back. Same engine as the [Website Compliance Checker](https://mahope.tools/compliance-site-check) and the [mahope/compliance-site-check GitHub Action](https://github.com/mahope/compliance-site-check).

**Endpoint:** `GET https://mahope.tools/api/compliance-scan?url=<target>`

No auth. No API key. CORS enabled.

## What it checks

1. Privacy policy page linked from the site
2. Terms of service page
3. Cookie consent banner detected on the homepage
4. Imprint / legal notice
5. Accessibility statement
6. DPA (data processing agreement) reference
7. Security headers (CSP, HSTS, X-Frame-Options, X-Content-Type-Options, Referrer-Policy)
8. SEO meta tags (title, description, viewport, canonical, robots, Open Graph)
9. Hreflang / HTML lang declaration

## Quick start

```bash
curl -s "https://mahope.tools/api/compliance-scan?url=example.com"
```

Response:

```json
{
  "ok": true,
  "url": "https://example.com",
  "score": 11,
  "grade": "D",
  "passed": 1,
  "failed": 7,
  "not_checked": 1,
  "total": 9,
  "results": {
    "passed": [ { "key": "hreflang", "label": "...", "status": "pass", "details": "...", "subResults": [] } ],
    "failed": [ { "key": "privacy", "label": "...", "status": "fail", "details": "..." } ],
    "notChecked": [ { "key": "dpa", "label": "...", "status": "unknown", "details": "..." } ]
  },
  "version": "2.0"
}
```

| Field        | Type    | Meaning                                             |
|--------------|---------|-----------------------------------------------------|
| `score`      | number  | 0-100, share of checks passed.                      |
| `grade`      | string  | A / B / C / D derived from score.                   |
| `passed`/`failed`/`total` | number | Check counts. `passed + failed + not_checked` is always `total`. |
| `not_checked` | number | Checks that were **not completed** — the page limit ran out before the check was reached. These are not findings. |
| `pages_read` | array | The URLs that answered with content, in the order they were read. |
| `pages_checked` | number | How many pages the call fetched, including the 404s. |
| `results.passed` / `results.failed` / `results.notChecked` | array | Per-check results with `details` and optional `subResults`. `notChecked` entries have `"status": "unknown"`. |
| `scanned_url` | string | The URL that was read (after redirects), which is not always the one you sent. |
| `error`      | string  | Present only when `ok` is `false`.                  |

## Error handling

- Missing `?url=` → HTTP 400, `{"ok":false,"error":"Missing ?url= parameter"}`
- Invalid URL → HTTP 400
- Target unreachable → HTTP 502 with reason
- A scan takes up to ~15 seconds.

## The page limit, and what a finding means

The server reads **at most 12 pages per call, shared across every URL in that
call** — 12 for one URL, 4 each for three, 3+3+2+2+2 for five. The budget is
spent round-robin, so every legal-page check gets at least two candidates to
read before any check gets a third.

That limit decides what a result is allowed to say:

- **A page the homepage links to counts as found**, without spending budget on
  it. A link is the evidence; a guessed path is not.
- `"status": "fail"` with `"Not found. Add a … page"` means the scan read the
  candidates it expected and none of them was the page. If the candidate list
  was cut short by the limit, the `details` string says so: *«We read 2 of the
  7 pages we expected here.»*
- `"status": "unknown"` in `results.notChecked` means the limit ran out before
  that check got a single page read. **No finding was made**, so do not report
  it as a missing page — re-run that URL on its own if you need the full check.

## Rate limits

Keep it reasonable: one origin per client per 10 seconds. For automated checking in CI, prefer the GitHub Action instead of hammering this endpoint.

## Try it live

Interactive UI: https://mahope.tools/compliance-site-check (English) or https://mahope.tools/da/compliance-site-check (Danish).
