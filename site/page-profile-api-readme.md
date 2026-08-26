# page-profile API

Free JSON API: send a public URL, get a structured profile back — HTTP status, title, meta description, canonical, Open Graph and Twitter Card tags, JSON-LD structured data, heading outline, image alt-text coverage, security headers — plus a quality score (0–21) and letter grade. Same engine as the [page-profile CLI](/page-profile).

**Endpoint:** `GET https://hermes-passiv.pages.dev/api/profile?url=...`

No auth. No API key. CORS enabled. Fair use: 30 requests per visitor per day.

## Quick start

### curl

```bash
curl -s "https://hermes-passiv.pages.dev/api/profile?url=https://example.com"
```

Response:

```json
{
  "ok": true,
  "url": "https://example.com/",
  "final_url": "https://example.com/",
  "status": 200,
  "title": "Example Domain",
  "title_length": 14,
  "meta_description": null,
  "meta_description_length": 0,
  "canonical": null,
  "language": "en",
  "og": {},
  "twitter": {},
  "json_ld_count": 0,
  "json_ld_types": [],
  "headings": { "h1": ["Example Domain"], "h2": [], "h3": [] },
  "images": { "total": 0, "with_alt": 0, "without_alt": 0 },
  "security": { "hsts": false, "csp": false, "xfo": false, "xcto": false },
  "https": true,
  "score": 7,
  "max_score": 21,
  "grade": "F",
  "penalties": ["Title length (14 chars) outside recommended range"]
}
```

### Python

```python
import requests

def profile(url: str) -> dict:
    r = requests.get(
        "https://hermes-passiv.pages.dev/api/profile",
        params={"url": url},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()

p = profile("https://example.com")
print(p["grade"], p["score"], "/", p["max_score"])
```

### JavaScript / TypeScript

```js
const res = await fetch(`https://hermes-passiv.pages.dev/api/profile?url=${encodeURIComponent(url)}`);
const data = await res.json();
if (!data.ok) throw new Error(data.error);
console.log(data.grade);
```

## Response fields

| Field | Type | Description |
|---|---|---|
| `ok` | boolean | `false` means the request failed — check `error` |
| `url` | string | The URL as requested |
| `final_url` | string | URL after redirects |
| `status` | integer | HTTP status of the fetched page |
| `title` | string \| null | `<title>` text |
| `meta_description` | string \| null | Meta description content |
| `canonical` | string \| null | Canonical link href |
| `language` | string \| null | `lang` attribute |
| `og` / `twitter` | object | Open Graph / Twitter Card tags found |
| `json_ld_count` / `json_ld_types` | int / array | Structured data blocks found |
| `headings` | object | Heading outline by level |
| `images` | object | Total images and alt-text coverage |
| `security` | object | HSTS, CSP, X-Frame-Options, X-Content-Type-Options presence |
| `score` / `max_score` | integer | Quality score out of 21 |
| `grade` | string | Letter grade A–F |
| `penalties` | array | Human-readable reasons points were lost |

## Errors

| Status | Meaning |
|---|---|
| 400 | Missing or invalid `?url=` parameter, or the target is this site itself |
| 413 | Target page larger than 500 KB |
| 429 | Daily limit reached (30/day per visitor) — resets at midnight UTC |
| 502 | Could not fetch the target page |
| 200 with `ok:false` | Target page returned an HTTP 4xx/5xx — details in `error` |

## Use in CI

Gate deploys on a minimum grade using `--json`-style checks against the API:

```bash
grade=$(curl -s "https://hermes-passiv.pages.dev/api/profile?url=$URL" | python3 -c 'import json,sys;print(json.load(sys.stdin).get("grade",""))')
[ "$grade" = "A" ] || [ "$grade" = "B" ] || { echo "Quality gate failed: $grade"; exit 1; }
```

For unlimited local runs, download the [single-file Python CLI](/downloads/page-profile/page_profile.py) instead.
