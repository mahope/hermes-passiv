#!/usr/bin/env python3
"""Generate a KDP-ready eBook cover with Pillow (parameterised).

Run: python3 make_cover_all.py            # both covers
     python3 make_cover_all.py eaa        # just one
Output: ebook/<slug>-cover.jpg (1600x2560)
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.abspath(__file__))
W, H = 1600, 2560

BG = (13, 27, 42)        # dark navy
ACCENT = (46, 196, 182)  # teal
LIGHT = (224, 251, 252)
SUBTEXT = (180, 205, 215)

COVERS = {
    "nis2": {
        "out": os.path.join(ROOT, "ebook", "cover.jpg"),
        "kicker": "EU CYBERSECURITY LAW",
        "title_lines": ["NIS2 Compliance", "for Small", "Web Agencies"],
        "sub_lines": [
            "A practical guide to meeting EU",
            "cybersecurity requirements without",
            "a compliance team",
        ],
    },
    "eaa": {
        "out": os.path.join(ROOT, "ebook", "eaa-cover.jpg"),
        "kicker": "EU ACCESSIBILITY LAW",
        "title_lines": ["EAA Compliance", "Checklist for", "WordPress Sites"],
        "sub_lines": [
            "The 10-point checklist every agency",
            "needs to pass the European",
            "Accessibility Act",
        ],
    },
    "eaa-shopify": {
        "out": os.path.join(ROOT, "ebook", "eaa-shopify-cover.jpg"),
        "kicker": "EU ACCESSIBILITY LAW",
        "title_lines": ["EAA Compliance", "for Shopify", "Stores"],
        "sub_lines": [
            "A practical guide to making your",
            "Shopify store compliant with the",
            "European Accessibility Act",
        ],
    },
    "cookie-consent": {
        "out": os.path.join(ROOT, "ebook", "cookie-consent-cover.jpg"),
        "kicker": "GDPR & EPRIVACY LAW",
        "title_lines": ["Cookie Consent", "& Privacy", "Compliance"],
        "sub_lines": [
            "A practical guide to meeting GDPR",
            "and cookie requirements for small",
            "websites",
        ],
    },
    "gdpr": {
        "out": os.path.join(ROOT, "ebook", "gdpr-cover.jpg"),
        "kicker": "EU DATA PROTECTION LAW",
        "title_lines": ["GDPR Compliance", "for Small", "Web Agencies"],
        "sub_lines": [
            "A practical guide to client data",
            "protection without a legal department",
            "",
        ],
    },
    "chrome-ext": {
        "out": os.path.join(ROOT, "ebook", "chrome-extension-cover.jpg"),
        "kicker": "BROWSER DEVELOPMENT",
        "title_lines": ["Build Your First", "Chrome", "Extension"],
        "sub_lines": [
            "From a blank folder to the Chrome",
            "Web Store in three hours —",
            "a complete practical guide",
        ],
    },
}


def load_font(size, bold=True):
    candidates = [
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/SFNS.ttf",
        "/Library/Fonts/Arial.ttf",
    ]
    for c in candidates:
        if os.path.exists(c):
            try:
                return ImageFont.truetype(c, size)
            except OSError:
                continue
    return ImageFont.load_default()


def centered(d, y, text, font, fill):
    bbox = d.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0]
    d.text(((W - w) / 2 - bbox[0], y), text, font=font, fill=fill)


def build(cfg):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    d.rectangle([0, 0, W, 40], fill=ACCENT)
    d.rectangle([0, H - 40, W, H], fill=ACCENT)

    for x in range(80, W, 120):
        for y in range(140, H - 140, 120):
            d.ellipse([x, y, x + 4, y + 4], fill=(23, 42, 58))

    f_kicker = load_font(52, bold=False)
    f_title = load_font(150)
    f_sub = load_font(62, bold=False)
    f_author = load_font(72)

    centered(d, 260, cfg["kicker"], f_kicker, ACCENT)

    y = 620
    for line in cfg["title_lines"]:
        centered(d, y, line, f_title, LIGHT)
        y += 190

    d.line([(W / 2 - 200, y + 30), (W / 2 + 200, y + 30)], fill=ACCENT, width=8)

    yy = y + 100
    for i, line in enumerate(cfg["sub_lines"]):
        centered(d, yy + i * 90, line, f_sub, SUBTEXT)

    centered(d, H - 420, "MAHOPE", f_author, LIGHT)

    img.save(cfg["out"], "JPEG", quality=92)
    print(f"Cover written: {cfg['out']}")


def main():
    which = sys.argv[1:] or list(COVERS)
    for key in which:
        build(COVERS[key])


if __name__ == "__main__":
    main()
