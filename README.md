# Hermes

Source for the [mahope.tools](https://mahope.tools) family of small web tools.
Everything here is MIT licensed and free to use. The paid tiers are optional
upgrades for teams that need more than one person needs.

This repository builds the sites and the packages — it is not a single product.

| Site | What it is |
|---|---|
| [mahope.tools](https://mahope.tools) | The tool index, the free e-books, and the license server |
| [cleancopy.tools](https://cleancopy.tools) | Clean Copy: paste as clean Markdown, CSV and JSON — in the browser, your editor, and the CLI |
| [deskuptime.com](https://deskuptime.com) | Uptime and bulk URL checks you run yourself |
| [bugbottle.dev](https://bugbottle.dev) | Browser bug reports into an issue tracker (separate repo: [mahope/bugbottle](https://github.com/mahope/bugbottle)) |

## Free tools

| Tool | Where |
|---|---|
| Clean Copy — Chrome, Firefox, VS Code, Obsidian, CLI | [cleancopy.tools](https://cleancopy.tools) |
| DeskUptime — uptime and bulk URL checker, CLI `@mahope/deskuptime` | [deskuptime.com/tools](https://deskuptime.com/tools) |
| Transmute — document converter, CLI `@mahope/transmute` | [npm](https://www.npmjs.com/package/@mahope/transmute) |
| EUComply / EAA scanner — compliance and accessibility checks, CLI `@mahope/eucomply-scanner` | [mahope.tools/downloads](https://mahope.tools/downloads) |
| Online site check — scan any URL for common compliance problems | [mahope.tools/compliance-site-check](https://mahope.tools/compliance-site-check) |
| Page Profile — per-page audits, CLI `@mahope/passiv-mcp` | [mahope.tools/page-profile](https://mahope.tools/page-profile) |
| Site Icons — app and social icons from one source image | [mahope.tools/site-icons](https://mahope.tools/site-icons) |
| Cookie consent banner | [demo](https://mahope.tools/cookie-consent-banner-demo) |
| Free e-books — GDPR, NIS2, EAA, cookie consent | [mahope.tools/books](https://mahope.tools/books) |

## Paid tiers

The same tools, licensed for a team. A license key activates against
`mahope.tools/api/license` and works in the clients listed above.

| Product | Price |
|---|---|
| [Clean Copy Pro](https://buy.stripe.com/6oU4gy76PgvgdBIdAXbMQ00) — custom cleanup rules with regex support | $19/year |
| [DeskUptime Pro](https://buy.stripe.com/7sY9AS9eX3Iu418fJ5bMQ01) — 3 machines | $19 once |
| [Transmute Desktop](https://buy.stripe.com/eVqbJ0dvdbaW55cgN9bMQ02) — 3 machines | $19 once |
| [Page Profile Pro](https://buy.stripe.com/9B6eVcgHp7YK69ggN9bMQ04) | $19/year |
| [EUComply Pro](https://buy.stripe.com/eVq00i4YH6UG69g0ObbMQ03) — per website | $79/year |

## Privacy

Free features do not send your content anywhere. A paid tier makes exactly one
kind of request: a license check against `mahope.tools/api/license`, carrying
your key and a random per-installation device id — nothing about the file or
page you are working on. If a check cannot complete, the client keeps the last
known answer for up to seven days rather than locking you out. Each tool's own
page documents its requests.

## Build

Requires Python 3.12 (see `.python-version`).

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements-build.txt
python3 build_sites.py          # writes dist/ — never edit dist/ by hand
```

The full quality gate, which is what CI runs before every deploy:

```bash
python3 tools/quality_gate.py
```

`../auditedwp` is a sibling repository used as a build source. It has its own
contract and is not modified from here.

## Support

[mahope.tools/support](https://mahope.tools/support). If a tool saved you time, a
thank-you is welcome: [donate](https://donate.stripe.com/7sYeVcbn50wieFM8gDbMQ0c).

## License

MIT
