#!/usr/bin/env python3
"""site-icons — a universal favicon, OG-image & PWA icon generator.

Takes a source image (SVG or PNG) + optional config and generates every
standard favicon size, Apple touch icons, PWA icons, Windows tile icons, an
OG image, manifest.json, browserconfig.xml, and the HTML snippet for <head>.

Free tier:  basic favicon set  (16, 32, 48)
Pro tier  ($29): full set including OG, PWA, Apple touch, tile, manifest, XML
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import textwrap
import xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image

__version__ = "1.0.0"

# ── Icon set definitions ────────────────────────────────────────────────────

FAVICON_SIZES = [16, 32, 48]          # free
PRO_SIZES = {
    "apple-touch-icon":     [152, 167, 180],
    "pwa-icon":             [192, 512],
    "windows-tile":         [70, 150, 310],
}
OG_SIZE = (1200, 630)

# ── License handling ────────────────────────────────────────────────────────

LICENSE_DIR = Path.home() / ".site-icons"
LICENSE_FILE = LICENSE_DIR / "license.key"


def _has_pro_license() -> bool:
    """Checks for a valid license file.  Simple hash check; real impl will use
    Lemon Squeezy API when available."""
    if not LICENSE_FILE.exists():
        return False
    content = LICENSE_FILE.read_text().strip()
    # For now: the key is "pro" sha256'd + a known suffix
    expected = hashlib.sha256(b"site-icons-pro-v1").hexdigest()
    return content == expected


# ── SVG rasterisation ───────────────────────────────────────────────────────

def _rasterise_svg(svg_path: Path, out_png: Path, size: int):
    """Convert SVG to PNG using rsvg-convert (librsvg)."""
    cmd = [
        "rsvg-convert",
        "--width", str(size),
        "--height", str(size),
        "--format", "png",
        "--output", str(out_png),
        str(svg_path),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"rsvg-convert failed: {r.stderr.strip()}")


# ── Source image loader ─────────────────────────────────────────────────────

def _load_source(source: Path, base_size: int = 512) -> Image.Image:
    """Open a PNG/JPEG source, or convert an SVG source to a base PNG first."""
    ext = source.suffix.lower()
    if ext in (".svg",):
        tmp = source.parent / f".__site_icons_tmp_{base_size}.png"
        try:
            _rasterise_svg(source, tmp, base_size)
            img = Image.open(tmp).convert("RGBA")
            return img
        finally:
            if tmp.exists():
                tmp.unlink()
    else:
        img = Image.open(source).convert("RGBA")
        return img


# ── Resize helpers ──────────────────────────────────────────────────────────

def _resize(img: Image.Image, size: int) -> Image.Image:
    """Resize while preserving aspect ratio, centering on a square canvas."""
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    img.thumbnail((size, size), Image.Resampling.LANCZOS)
    x = (size - img.width) // 2
    y = (size - img.height) // 2
    out.paste(img, (x, y), img if img.mode == "RGBA" else None)
    return out


def _composite_og_image(icon: Image.Image, config: dict) -> Image.Image:
    """Create a 1200×630 OG image: solid background + icon + optional text."""
    bg_color = config.get("og_bg_color", config.get("theme_color", "#1e293b"))
    text_str = config.get("og_text", "")
    font_color = config.get("og_font_color", "#ffffff")

    # Parse hex color
    bg = _hex_to_rgb(bg_color)
    fg = _hex_to_rgb(font_color)

    canvas = Image.new("RGBA", OG_SIZE, (*bg, 255))

    # Place icon (centered-left if no text, centered if text)
    if text_str:
        icon_x = 80
    else:
        icon_x = (OG_SIZE[0] - 200) // 2  # center
    icon_y = (OG_SIZE[1] - 200) // 2

    icon_resized = icon.resize((200, 200), Image.Resampling.LANCZOS)
    if icon_resized.mode == "RGBA":
        canvas.paste(icon_resized, (icon_x, icon_y), icon_resized)
    else:
        canvas.paste(icon_resized, (icon_x, icon_y))

    if text_str:
        # Draw text manually using Pillow's ImageFont
        try:
            from PIL import ImageDraw, ImageFont
            draw = ImageDraw.Draw(canvas)
            # Try to find a bold-ish font
            font_paths = [
                "/System/Library/Fonts/Helvetica.ttc",
                "/System/Library/Fonts/Helvetica.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            ]
            font = None
            for fp in font_paths:
                if os.path.exists(fp):
                    font = ImageFont.truetype(fp, 52)
                    break
            if font is None:
                font = ImageFont.load_default()

            text_x = 320
            text_y = (OG_SIZE[1] - 52) // 2 - 10
            draw.text((text_x, text_y), text_str, fill=(*fg, 255), font=font)
        except ImportError:
            pass  # No text rendering without ImageDraw/ImageFont

    return canvas


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


# ── ICO generation ──────────────────────────────────────────────────────────

def _build_ico(sizes_dir: Path, sizes: list[int]) -> bytes:
    """Package multiple PNGs into a single .ico file."""
    # ICO header: reserved(2) + type(2) + count(2)
    ico_sizes = []
    for s in sizes:
        png_path = sizes_dir / f"favicon-{s}x{s}.png"
        with open(png_path, "rb") as f:
            png_data = f.read()
        ico_sizes.append((s, png_data))

    header = bytearray()
    header.extend(b"\x00\x00")  # reserved
    header.extend(b"\x01\x00")  # ICO type
    header.extend(len(ico_sizes).to_bytes(2, "little"))

    # Directory entries (16 bytes each)
    entries = bytearray()
    data_offset = 6 + 16 * len(ico_sizes)
    for s, png_data in ico_sizes:
        w = 0 if s == 256 else s
        h = 0 if s == 256 else s
        entries.extend(w.to_bytes(1, "little"))
        entries.extend(h.to_bytes(1, "little"))
        entries.extend(b"\x00")   # palette
        entries.extend(b"\x00")   # reserved
        entries.extend(b"\x01\x00")  # planes
        entries.extend(b"\x20\x00")  # bpp
        entries.extend(len(png_data).to_bytes(4, "little"))
        entries.extend(data_offset.to_bytes(4, "little"))
        data_offset += len(png_data)

    ico = bytes(header) + bytes(entries)
    for _, png_data in ico_sizes:
        ico += png_data
    return ico


# ── Manifest / XML / HTML generators ────────────────────────────────────────

def _make_manifest(config: dict, sizes: list[int]) -> str:
    """Generate web app manifest.json."""
    pwa_sizes = PRO_SIZES["pwa-icon"]
    icons = []
    for s in pwa_sizes:
        icons.append({
            "src": f"/icon-{s}x{s}.png",
            "sizes": f"{s}x{s}",
            "type": "image/png",
            "purpose": "any maskable",
        })
    manifest = {
        "name": config.get("app_name", "My App"),
        "short_name": config.get("short_name", config.get("app_name", "App")),
        "start_url": config.get("start_url", "/"),
        "display": "standalone",
        "theme_color": config.get("theme_color", "#1e293b"),
        "background_color": config.get("background_color", "#ffffff"),
        "icons": icons,
    }
    return json.dumps(manifest, indent=2)


def _make_browserconfig(config: dict) -> str:
    """Generate browserconfig.xml for Windows tiles."""
    tile_color = config.get("tile_color", config.get("theme_color", "#1e293b"))
    return textwrap.dedent(f'''\
        <?xml version="1.0" encoding="utf-8"?>
        <browserconfig>
            <msapplication>
                <tile>
                    <square70x70logo src="icon-70x70.png"/>
                    <square150x150logo src="icon-150x150.png"/>
                    <square310x310logo src="icon-310x310.png"/>
                    <TileColor>{tile_color}</TileColor>
                </tile>
            </msapplication>
        </browserconfig>
    ''')


def _make_html_snippet(app_name: str) -> str:
    """Generate the HTML <head> snippet."""
    lines = [
        '<!-- Site Icons — generated by site-icons -->',
        '<link rel="icon" type="image/x-icon" href="/favicon.ico">',
        '<link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png">',
        '<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png">',
        '<link rel="icon" type="image/png" sizes="48x48" href="/favicon-48x48.png">',
        '<link rel="apple-touch-icon" sizes="152x152" href="/apple-touch-icon-152x152.png">',
        '<link rel="apple-touch-icon" sizes="167x167" href="/apple-touch-icon-167x167.png">',
        '<link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon-180x180.png">',
        '<link rel="icon" type="image/png" sizes="192x192" href="/icon-192x192.png">',
        '<link rel="icon" type="image/png" sizes="512x512" href="/icon-512x512.png">',
        '<meta name="msapplication-square70x70logo" content="icon-70x70.png">',
        '<meta name="msapplication-square150x150logo" content="icon-150x150.png">',
        '<meta name="msapplication-square310x310logo" content="icon-310x310.png">',
        '<meta name="msapplication-TileColor" content="#1e293b">',
        '<link rel="manifest" href="/manifest.json">',
        '<meta property="og:image" content="/og-image.png">',
    ]
    return '\n'.join(lines)


# ── Main generate function ──────────────────────────────────────────────────

def generate(
    source: Path,
    output_dir: Path,
    config: dict,
    force_pro: bool = False,
) -> dict:
    """Generate all icon assets.

    Returns a dict {generated: [filenames], tier: 'free'|'pro'}.
    """
    is_pro = _has_pro_license() or force_pro
    output_dir.mkdir(parents=True, exist_ok=True)
    generated = []

    # Load source and create a base icon (512px)
    icon = _load_source(source, base_size=512)
    base = _resize(icon, 512)

    app_name = config.get("app_name", "My App")

    # ── Favicons (free tier) ──────────────────────────────────────────────
    for s in FAVICON_SIZES:
        img = _resize(base, s)
        path = output_dir / f"favicon-{s}x{s}.png"
        img.save(path, "PNG")
        generated.append(str(path))

    # Build .ico from free sizes
    ico_data = _build_ico(output_dir, FAVICON_SIZES)
    ico_path = output_dir / "favicon.ico"
    ico_path.write_bytes(ico_data)
    generated.append(str(ico_path))

    # ── Pro tier assets ──────────────────────────────────────────────────
    if is_pro:
        for category, sizes in PRO_SIZES.items():
            for s in sizes:
                img = _resize(base, s)
                if category == "apple-touch-icon":
                    name = f"apple-touch-icon-{s}x{s}.png"
                elif category == "pwa-icon":
                    name = f"icon-{s}x{s}.png"
                elif category == "windows-tile":
                    name = f"icon-{s}x{s}.png"
                path = output_dir / name
                img.save(path, "PNG")
                generated.append(str(path))

        # OG image
        og = _composite_og_image(base, config)
        og_path = output_dir / "og-image.png"
        og.save(og_path, "PNG")
        generated.append(str(og_path))

        # Manifest
        manifest = _make_manifest(config, FAVICON_SIZES)
        manifest_path = output_dir / "manifest.json"
        manifest_path.write_text(manifest)
        generated.append(str(manifest_path))

        # Browser config
        xml = _make_browserconfig(config)
        xml_path = output_dir / "browserconfig.xml"
        xml_path.write_text(xml)
        generated.append(str(xml_path))

        # Apple tile icon
        tile = _resize(base, 256)
        tile_path = output_dir / "mstile-256x256.png"
        tile.save(tile_path, "PNG")
        generated.append(str(tile_path))

    # HTML snippet (always generated, but Pro includes extra links)
    snippet = _make_html_snippet(app_name)
    snippet_path = output_dir / "snippet.html"
    snippet_path.write_text(snippet)
    generated.append(str(snippet_path))

    return {
        "generated": generated,
        "tier": "pro" if is_pro else "free",
    }


# ── CLI entrypoint ──────────────────────────────────────────────────────────

def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        prog="site-icons",
        description="Generate all favicon, OG-image & PWA icon sizes from a single source.",
    )
    parser.add_argument("source", type=Path, help="Source image (SVG or PNG)")
    parser.add_argument("-o", "--output-dir", type=Path, default=Path("icons"),
                        help="Output directory (default: icons/)")
    parser.add_argument("-c", "--config", type=Path, default=None,
                        help="JSON config file (app_name, theme_color, etc.)")
    parser.add_argument("--pro", action="store_true",
                        help="Force Pro tier (skip license check)")
    parser.add_argument("--version", action="version",
                        version=f"site-icons v{__version__}")

    args = parser.parse_args(argv)

    # Load config
    config = {}
    if args.config and args.config.exists():
        config = json.loads(args.config.read_text())

    # Validate source
    if not args.source.exists():
        print(f"Error: source file not found: {args.source}", file=sys.stderr)
        return 1

    result = generate(args.source, args.output_dir, config, force_pro=args.pro)
    tier_label = "Pro" if result["tier"] == "pro" else "Free"
    print(f"site-icons v{__version__} — {tier_label} tier")
    print(f"Generated {len(result['generated'])} files in {args.output_dir}/")
    for f in result["generated"]:
        size = os.path.getsize(f)
        print(f"  {os.path.relpath(f):50s} {size:>8,} bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())