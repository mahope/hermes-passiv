# Clean Copy API

Free REST API: send HTML, get clean Markdown back. Same conversion engine as the [Clean Copy browser extension](https://github.com/mahope/clean-copy) (v1.5.2) — 260+ iterations of edge-case fixes, available programmatically.

**Endpoint:** `POST https://hermes-passiv.pages.dev/api/clean-copy`

No auth. No API key. 50 KB max input per request. CORS enabled.

## Quick start

### curl

```bash
curl -s -X POST https://hermes-passiv.pages.dev/api/clean-copy \
  -H 'Content-Type: application/json' \
  -d '{"html":"<h1>Hello</h1><p>This is <b>bold</b>.</p>"}'
```

Response:

```json
{
  "ok": true,
  "markdown": "# Hello\n\nThis is **bold**.",
  "mode": "markdown",
  "input_chars": 41,
  "output_chars": 26,
  "version": "1.5.2"
}
```

### Python

```python
import requests

def clean_copy(html: str, mode: str = "markdown") -> str:
    r = requests.post(
        "https://hermes-passiv.pages.dev/api/clean-copy",
        json={"html": html, "mode": mode},
        timeout=30,
    )
    r.raise_for_status()
    data = r.json()
    if not data.get("ok"):
        raise ValueError(data.get("error", "unknown error"))
    return data["markdown"]

print(clean_copy("<h1>Hello</h1><p>This is <b>bold</b>.</p>"))
```

### JavaScript / TypeScript

```js
async function cleanCopy(html, mode = "markdown") {
  const res = await fetch("https://hermes-passiv.pages.dev/api/clean-copy", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ html, mode }),
  });
  const data = await res.json();
  if (!data.ok) throw new Error(data.error || "clean-copy failed");
  return data.markdown;
}
```

## Request body

| Field  | Type   | Required | Description                                                        |
|--------|--------|----------|--------------------------------------------------------------------|
| `html` | string | yes      | The HTML to convert (max 50 KB).                                   |
| `mode` | string | no       | `"markdown"` (default) or `"plain"` — plain strips all formatting. |

## Response

| Field         | Type    | Description                                  |
|---------------|---------|----------------------------------------------|
| `ok`          | boolean | `true` on success, `false` on error.         |
| `markdown`    | string  | The converted output.                        |
| `mode`        | string  | Echo of the requested mode.                  |
| `input_chars` | number  | Size of the received HTML.                   |
| `output_chars`| number  | Size of the returned text.                   |
| `version`     | string  | Converter engine version.                    |
| `error`       | string  | Present only when `ok` is `false`.           |

## Error handling

Errors always return HTTP 200 with `ok: false` and an `error` message:

```json
{"ok": false, "error": "Missing html"}
```

- Missing or empty `html` → `Missing html`
- Input over 50 KB → `Input too large`
- Invalid JSON body → `Invalid JSON`

## What it converts

Headings, bold, italic, links, ordered/unordered lists (nested), code blocks (inline and fenced), blockquotes and tables. It strips ads, scripts, hidden elements, inline CSS junk and unescapes HTML entities.

## Related projects

- [Clean Copy for Chrome](https://github.com/mahope/clean-copy)
- [Clean Copy for Firefox](https://github.com/mahope/clean-copy-firefox)
- [clean-copy-cli](https://github.com/mahope/clean-copy-cli) — `brew install clean-copy`
- [Obsidian plugin](https://github.com/mahope/clean-copy-obsidian)

## Try it live

Interactive try-it interface: https://hermes-passiv.pages.dev/clean-copy-api
