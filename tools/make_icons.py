#!/usr/bin/env python3
"""Generate the favicon set for every product into site/_brand/<product>/.

    python tools/make_icons.py            # all products
    python tools/make_icons.py deskuptime

Output per product: favicon.svg, favicon.ico (32px), apple-touch-icon.png (180),
icon-192.png, icon-512.png, site.webmanifest. A plain monogram on a rounded
square in the product accent; no gradients, no effects.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
from brand import BRANDS, BRAND_DIR  # noqa: E402

FONT_CANDIDATES = [
    "C:/Windows/Fonts/arialbd.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
]


def font(size: int) -> ImageFont.FreeTypeFont:
    for p in FONT_CANDIDATES:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def svg(mark: str, accent: str) -> str:
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
        f'<rect width="64" height="64" rx="12" fill="{accent}"/>'
        '<text x="32" y="46" text-anchor="middle" font-family="Inter, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif" '
        f'font-size="40" font-weight="700" fill="#fff">{mark}</text></svg>\n'
    )


def png(mark: str, accent: str, size: int, pad_ratio: float = 0.0) -> Image.Image:
    """Render the mark at `size` px. pad_ratio adds safe-area margin (maskable icons)."""
    scale = 4
    s = size * scale
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    pad = int(s * pad_ratio)
    radius = int((s - 2 * pad) * 0.19)
    d.rounded_rectangle([pad, pad, s - pad - 1, s - pad - 1], radius=radius, fill=accent)
    f = font(int((s - 2 * pad) * 0.66))
    box = d.textbbox((0, 0), mark, font=f)
    w, h = box[2] - box[0], box[3] - box[1]
    x = (s - w) / 2 - box[0]
    y = (s - h) / 2 - box[1]
    d.text((x, y), mark, font=f, fill="#ffffff")
    return img.resize((size, size), Image.LANCZOS)


def manifest(name: str, accent: str) -> str:
    return json.dumps({
        "name": name,
        "short_name": name,
        "icons": [
            {"src": "/icon-192.png", "sizes": "192x192", "type": "image/png"},
            {"src": "/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable"},
        ],
        "theme_color": accent,
        "background_color": "#f7f7f5",
        "display": "browser",
        "start_url": "/",
    }, indent=2) + "\n"


def build(product: str) -> Path:
    b = BRANDS[product]
    out = BRAND_DIR / product
    out.mkdir(parents=True, exist_ok=True)
    (out / "favicon.svg").write_text(svg(b["mark"], b["accent"]), encoding="utf-8")
    png(b["mark"], b["accent"], 32).save(out / "favicon.ico", format="ICO", sizes=[(32, 32)])
    png(b["mark"], b["accent"], 180).convert("RGB").save(out / "apple-touch-icon.png", optimize=True)
    png(b["mark"], b["accent"], 192).save(out / "icon-192.png", optimize=True)
    png(b["mark"], b["accent"], 512, pad_ratio=0.1).save(out / "icon-512.png", optimize=True)
    (out / "site.webmanifest").write_text(manifest(b["name"], b["accent"]), encoding="utf-8")
    return out


def main(argv: list[str]) -> int:
    products = argv or list(BRANDS)
    for p in products:
        print(f"icons: {p} -> {build(p)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
