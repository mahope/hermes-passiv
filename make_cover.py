#!/usr/bin/env python3
"""Generate a KDP-ready eBook cover (1600x2560 JPG) with Pillow.

Run: .venv/bin/python3 make_cover.py
Output: ebook/cover.jpg
"""
import os
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.abspath(__file__))
W, H = 1600, 2560
OUT = os.path.join(ROOT, "ebook", "cover.jpg")

BG = (13, 27, 42)        # dark navy
ACCENT = (46, 196, 182)  # teal
LIGHT = (224, 251, 252)


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


def centered(draw, y, text, font, fill):
    bbox = draw.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0]
    draw.text(((W - w) / 2 - bbox[0], y), text, font=font, fill=fill)
    return bbox[3] - bbox[1]


def main():
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    # Accent band at top and bottom
    d.rectangle([0, 0, W, 40], fill=ACCENT)
    d.rectangle([0, H - 40, W, H], fill=ACCENT)

    # Subtle grid dots for texture
    for x in range(80, W, 120):
        for y in range(140, H - 140, 120):
            d.ellipse([x, y, x + 4, y + 4], fill=(23, 42, 58))

    f_kicker = load_font(52, bold=False)
    f_title = load_font(150)
    f_sub = load_font(62, bold=False)
    f_author = load_font(72)

    centered(d, 260, "EU CYBERSECURITY LAW", f_kicker, ACCENT)

    y = 620
    for line in ["NIS2 Compliance", "for Small", "Web Agencies"]:
        centered(d, y, line, f_title, LIGHT)
        y += 190

    d.line([(W / 2 - 200, y + 30), (W / 2 + 200, y + 30)], fill=ACCENT, width=8)

    yy = y + 100
    centered(d, yy, "A practical guide to meeting EU", f_sub, (180, 205, 215))
    centered(d, yy + 90, "cybersecurity requirements without", f_sub, (180, 205, 215))
    centered(d, yy + 180, "a compliance team", f_sub, (180, 205, 215))

    centered(d, H - 420, "MAHOPE", f_author, LIGHT)

    img.save(OUT, "JPEG", quality=92)
    print(f"Cover written: {OUT}")


if __name__ == "__main__":
    main()
