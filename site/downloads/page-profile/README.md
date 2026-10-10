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
curl -O https://mahope.tools/downloads/page-profile/page_profile.py
python3 page_profile.py https://example.com

# JSON output
python3 page_profile.py https://example.com --json | jq
```

## Pro features

Page Profile Pro ($19/year, [buy via Stripe](https://buy.stripe.com/9B6eVcgHp7YK69ggN9bMQ04)) adds:
- **Comparison mode** — compare two URLs side by side
- **Batch mode** — profile many URLs and rank them by score
- **HTML report** — create a client-ready report

Activate the 32-character key from your Stripe receipt:

```bash
python3 page_profile.py --activate YOUR-KEY
```

Activation and regular Pro checks contact `mahope.tools`. After a successful check, Pro can be used for up to seven days if the license service is temporarily unavailable. Page profiling and history remain free.

## License

MIT — free for any use.