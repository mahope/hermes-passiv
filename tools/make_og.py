#!/usr/bin/env python3
"""Render the 1200x630 Open Graph image for every product into site/_brand/<product>/og.png.

    python tools/make_og.py               # all products
    python tools/make_og.py bugbottle     # one

Renders a small HTML template with Playwright (Chromium) so the image uses the
same typeface and palette as the sites. Layout: product mark + name, one line,
domain and mahoje.dk. No gradients, no decoration.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent))
from brand import BRANDS, BRAND_DIR, BG, INK, MUTED  # noqa: E402

TEMPLATE = """<!doctype html><html><head><meta charset="utf-8">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700&display=swap" rel="stylesheet">
<style>
  html,body{{margin:0;width:1200px;height:630px;background:{bg};font-family:Inter,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;color:{ink};-webkit-font-smoothing:antialiased}}
  .wrap{{position:relative;width:1200px;height:630px;padding:72px 80px;box-sizing:border-box;display:flex;flex-direction:column;justify-content:space-between}}
  .brand{{display:flex;align-items:center;gap:22px}}
  .mark{{width:64px;height:64px;border-radius:14px;background:{accent};color:#fff;font-weight:700;font-size:40px;display:flex;align-items:center;justify-content:center;line-height:1}}
  .name{{font-size:38px;font-weight:700;letter-spacing:-0.02em}}
  .by{{font-size:24px;color:{muted};font-weight:400;margin-left:14px}}
  .line{{font-size:60px;font-weight:700;letter-spacing:-0.03em;line-height:1.1;max-width:1000px}}
  .foot{{display:flex;justify-content:space-between;align-items:flex-end;font-size:26px;color:{muted}}}
  .foot b{{color:{ink};font-weight:500}}
  .bar{{position:absolute;left:0;bottom:0;width:1200px;height:12px;background:{accent}}}
</style></head><body><div class="wrap">
  <div class="brand"><div class="mark">{mark}</div><div class="name">{name}<span class="by">by mahoje.dk</span></div></div>
  <div class="line">{tagline}</div>
  <div class="foot"><span><b>{domain}</b></span><span>{sub}</span></div>
  <div class="bar"></div>
</div></body></html>"""


def render(page, product: str, lang: str = "en") -> Path:
    b = BRANDS[product]
    out = BRAND_DIR / product
    out.mkdir(parents=True, exist_ok=True)
    html = TEMPLATE.format(bg=BG, ink=INK, muted=MUTED, accent=b["accent"], mark=b["mark"], name=b["name"],
                           tagline=b["tagline"][lang], domain=b["domain"],
                           sub="Free, open source, no account" if lang == "en" else "Gratis, open source, ingen konto")
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as f:
        f.write(html)
        tmp = Path(f.name)
    page.goto(tmp.as_uri())
    page.wait_for_load_state("networkidle")
    page.evaluate("document.fonts.ready")
    target = out / ("og.png" if lang == "en" else f"og-{lang}.png")
    page.screenshot(path=str(target), clip={"x": 0, "y": 0, "width": 1200, "height": 630})
    tmp.unlink(missing_ok=True)
    return target


def main(argv: list[str]) -> int:
    products = argv or list(BRANDS)
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1200, "height": 630}, device_scale_factor=1)
        for p in products:
            for lang in ("en", "da"):
                print(f"og: {p}/{lang} -> {render(page, p, lang)}")
        browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
