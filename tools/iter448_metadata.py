#!/usr/bin/env python3
"""Iteration 448: metadata-hygiene sweep across EN+DA blog posts.
Fixes, idempotently:
1. Missing og:image (and og:site_name) on blog posts -> add after og:url.
2. Incomplete hreflang sets on mirror pairs:
   - website-seo-metadata-audit <-> seo-metadata-tjek-hjemmeside
   - free-website-compliance-checker <-> gratis-compliance-tjek-hjemmeside
   -> full {en, da, x-default->EN} set on both sides.
3. twitter:title/description missing where twitter:card exists.
Validates everything afterwards. Run from repo root: python3 tools/iter448_metadata.py
"""
import os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "site")
BASE = "https://hermes-passiv.pages.dev"
OG_IMAGE = f"{BASE}/cover.jpg"


def url_for(rel):
    return f"{BASE}/{rel[:-5]}"


def fix_og_image(path):
    with open(path, encoding="utf-8") as f:
        h = f.read()
    changed = []
    if 'property="og:image"' not in h:
        m = re.search(r'<meta property="og:url" content="[^"]*"\s*/?>', h)
        if not m:
            return ["og-image-NO-ANCHOR"]
        h = h[: m.end()] + f'\n<meta property="og:image" content="{OG_IMAGE}">' + h[m.end():]
        changed.append("og:image")
    if 'property="og:site_name"' not in h:
        m = re.search(r'<meta property="og:type" content="[^"]*"\s*/?>', h)
        if m:
            h = h[: m.end()] + '\n<meta property="og:site_name" content="Hermes Passiv">' + h[m.end():]
            changed.append("og:site_name")
    if changed:
        with open(path, "w", encoding="utf-8") as f:
            f.write(h)
    return changed


def fix_twitter_meta(path):
    with open(path, encoding="utf-8") as f:
        h = f.read()
    if 'name="twitter:card"' not in h or 'name="twitter:title"' in h:
        return []
    title = re.search(r'<meta property="og:title" content="([^"]*)"', h)
    desc = re.search(r'<meta property="og:description" content="([^"]*)"', h)
    m = re.search(r'<meta name="twitter:card" content="[^"]*"\s*/?>', h)
    if not (title and desc and m):
        return []
    ins = (f'\n<meta name="twitter:title" content="{title.group(1)}">'
           f'\n<meta name="twitter:description" content="{desc.group(1)}">')
    h = h[: m.end()] + ins + h[m.end():]
    with open(path, "w", encoding="utf-8") as f:
        f.write(h)
    return ["twitter-title-desc"]


def fix_hreflang(path, en_url, da_url):
    """Ensure exactly one alternate per lang incl. x-default pointing at EN."""
    with open(path, encoding="utf-8") as f:
        h = f.read()
    h = re.sub(r'[ \t]*<link rel="alternate" hreflang="[^"]*" href="[^"]*">\n?', "", h)
    block = (f'<link rel="alternate" hreflang="en" href="{en_url}">\n'
             f'<link rel="alternate" hreflang="da" href="{da_url}">\n'
             f'<link rel="alternate" hreflang="x-default" href="{en_url}">\n')
    m = re.search(r'[ \t]*<link rel="canonical"[^>]*>\n', h)
    if not m:
        print(f"WARN no canonical anchor in {path}", file=sys.stderr)
        return False
    h = h[: m.start()] + block + h[m.start():]
    with open(path, "w", encoding="utf-8") as f:
        f.write(h)
    return True


changed_files = 0

for sub in ("blog", os.path.join("da", "blog")):
    d = os.path.join(SITE, sub)
    for fn in sorted(os.listdir(d)):
        if not fn.endswith(".html"):
            continue
        p = os.path.join(d, fn)
        ch = fix_og_image(p) + fix_twitter_meta(p)
        if ch:
            print(f"{sub}/{fn}: {', '.join(ch)}")
            changed_files += 1

PAIRS = [
    ("blog/website-seo-metadata-audit.html", "da/blog/seo-metadata-tjek-hjemmeside.html"),
    ("blog/free-website-compliance-checker.html", "da/blog/gratis-compliance-tjek-hjemmeside.html"),
]
for en_rel, da_rel in PAIRS:
    en_u, da_u = url_for(en_rel), url_for(da_rel)
    for rel in (en_rel, da_rel):
        if fix_hreflang(os.path.join(SITE, rel), en_u, da_u):
            print(f"{rel}: hreflang normalized")
            changed_files += 1

print(f"\n{changed_files} file-updates done. Validating...")

# --- validation ---
ok = True
for sub in ("blog", os.path.join("da", "blog")):
    d = os.path.join(SITE, sub)
    for fn in sorted(os.listdir(d)):
        if not fn.endswith(".html"):
            continue
        h = open(os.path.join(d, fn), encoding="utf-8").read()
        if 'property="og:image"' not in h:
            print("FAIL og:image:", fn); ok = False
        if 'name="twitter:card"' in h and 'name="twitter:title"' not in h:
            print("FAIL twitter:title:", fn); ok = False

for en_rel, da_rel in PAIRS:
    for rel, self_url in ((en_rel, url_for(en_rel)), (da_rel, url_for(da_rel))):
        h = open(os.path.join(SITE, rel), encoding="utf-8").read()
        n_en = h.count('hreflang="en"')
        n_da = h.count('hreflang="da"')
        n_xd = h.count('hreflang="x-default"')
        can = re.search(r'rel="canonical" href="([^"]+)"', h)
        if not (n_en == 1 and n_da == 1 and n_xd == 1):
            print(f"FAIL hreflang counts ({n_en},{n_da},{n_xd}):", rel); ok = False
        if not can or can.group(1) != self_url:
            print("FAIL canonical:", rel, "->", can and can.group(1)); ok = False

print("ALL VALID" if ok else "ERRORS FOUND")
sys.exit(0 if ok else 1)
