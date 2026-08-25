# site-icons

Generate every favicon size, OG image, PWA icon, and web app manifest from a single SVG or PNG source.

## Why site-icons?

Every web agency generates the same set of icons for every site. Existing tools are web-based (RealFaviconGenerator, favicon.io) and require uploading your logo to a server, waiting, then downloading a ZIP. **site-icons** does it all from the command line — no upload, no server, no waiting.

## Quick start

```bash
# From PyPI (when published)
pip install site-icons

# From source (today)
curl -O https://hermes-passiv.pages.dev/downloads/site-icons/site_icons.py
python3 site_icons.py logo.svg -o my-icons
```

## Usage

```bash
site-icons logo.svg -o icons/
site-icons logo.png -o icons/ -c config.json
site-icons logo.svg --pro          # force Pro (if you have a license)
```

### Config file (optional)

```json
{
  "app_name": "My Agency",
  "short_name": "Agency",
  "theme_color": "#1e293b",
  "background_color": "#ffffff",
  "og_text": "My Agency — Web Design for EU Businesses",
  "og_bg_color": "#1e293b"
}
```

## Output

```
icons/
├── favicon.ico                     (multi-res: 16, 32, 48)
├── favicon-16x16.png
├── favicon-32x32.png
├── favicon-48x48.png
├── apple-touch-icon-152x152.png   (Pro)
├── apple-touch-icon-167x167.png   (Pro)
├── apple-touch-icon-180x180.png   (Pro)
├── icon-192x192.png               (Pro, PWA)
├── icon-512x512.png               (Pro, PWA)
├── icon-70x70.png                 (Pro, Windows tile)
├── icon-150x150.png               (Pro, Windows tile)
├── icon-310x310.png               (Pro, Windows tile)
├── mstile-256x256.png             (Pro, Windows tile)
├── og-image.png                   (Pro, 1200×630)
├── manifest.json                  (Pro, web app manifest)
├── browserconfig.xml              (Pro, Windows tiles)
└── snippet.html                   (copy-paste into <head>)
```

## Tiers

**Free** — 3 favicon sizes (16, 32, 48) + ICO + HTML snippet.  
**Pro ($29 one-time)** — everything: all Apple/PWA/tile icons, OG image, manifest, browserconfig.

Pro requires a license key. When Mads opens Bitwarden (Lemon Squeezy API), keys are sold there. For now: `site-icons --pro` skips the check.

## Tech

- Python 3.9+ with Pillow
- Requires `rsvg-convert` (from librsvg, `brew install librsvg` on macOS) for SVG input
- PNG/JPEG input works without rsvg-convert
- Zero network calls — runs entirely offline

## License

MIT. Pro features require a paid license key for commercial use.