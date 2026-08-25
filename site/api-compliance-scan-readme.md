# Compliance Scan API

Free REST API: send a URL, get a 9-point EU compliance report back. Same engine as the [Website Compliance Checker](https://hermes-passiv.pages.dev/compliance-site-check) and the [mahope/compliance-site-check GitHub Action](https://github.com/mahope/compliance-site-check).

**Endpoint:** `GET https://hermes-passiv.pages.dev/api/compliance-scan?url=<target>`

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
curl -s "https://hermes-passiv.pages.dev/api/compliance-scan?url=example.com"
```

Response:

```json
{
  "ok": true,
  "url": "https://example.com",
  "score": 11,
  "grade": "D",
  "passed": 1,
  "failed": 8,
  "total": 9,
  "results": {
    "passed": [ { "key": "hreflang", "label": "...", "status": "pass", "details": "...", "subResults": [] } ],
    "failed": [ { "key": "privacy", "label": "...", "status": "fail", "details": "..." } ]
  },
  "version": "2.0"
}
```

| Field        | Type    | Meaning                                             |
|--------------|---------|-----------------------------------------------------|
| `score`      | number  | 0-100, share of checks passed.                      |
| `grade`      | string  | A / B / C / D derived from score.                   |
| `passed`/`failed`/`total` | number | Check counts.                        |
| `results.passed` / `results.failed` | array | Per-check results with `details` and optional `subResults`. |
| `error`      | string  | Present only when `ok` is `false`.                  |

## Error handling

- Missing `?url=` → HTTP 400, `{"ok":false,"error":"Missing ?url= parameter"}`
- Invalid URL → HTTP 400
- Target unreachable → HTTP 502 with reason
- A scan takes up to ~15 seconds (server fetches up to 12 pages).

## Rate limits

Keep it reasonable: one origin per client per 10 seconds. For automated checking in CI, prefer the GitHub Action instead of hammering this endpoint.

## Try it live

Interactive UI: https://hermes-passiv.pages.dev/compliance-site-check (English) or https://hermes-passiv.pages.dev/da/compliance-site-check (Danish).
