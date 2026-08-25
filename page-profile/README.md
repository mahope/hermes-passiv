# page-profile

**Zero-dependency web page profiler.** Check what a page has before you optimize it.

```bash
python3 page_profile.py https://example.com
```

## What it checks

| Category | Checks |
|----------|--------|
| **Core** | HTTP status, title tag, meta description, canonical URL |
| **Social** | Open Graph (og:title, og:description, og:image), Twitter Card |
| **Structure** | JSON-LD types, heading 1-6 outline, image alt-text coverage |
| **Security** | HSTS, CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy |
| **i18n** | Language, charset, hreflang alternates |
| **Score** | 21-point weighted score with letter grade (A-F) |

## Quick start

```bash
# Single file — no install
curl -O https://hermes-passiv.pages.dev/downloads/page-profile/page_profile.py
python3 page_profile.py https://example.com

# JSON output
python3 page_profile.py https://example.com --json | jq
```

## Pro features

When the Lemon Squeezy payment integration is live:
- **Comparison mode** — diff two URLs
- **History tracking** — see how a page changes over time
- **PDF report** — client-ready report

## License

MIT — free for any use.