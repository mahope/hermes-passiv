#!/usr/bin/env python3
"""Hvor stor er hver halvdel af blindpletten? Skriv som fil, ikke heredoc."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from check_inline_cta_events import RE_HREF, _trackers, RE_TRACK_JS  # noqa: E402
DOMAINS = ("mahope.tools", "cleancopy.tools", "deskuptime.com", "bugbottle.dev")
RE_ABS = re.compile(
    r"^https?://(" + "|".join(d.replace(".", r"\.") for d in DOMAINS) + r")"
    r"(?:/da)?/?([a-z0-9-]+)/?(?:\.html)?(?:#[^#]*)?$")

sys.path.insert(0, str(ROOT / "tools"))
from audit_unmeasured_routes import measured_names  # noqa: E402

names = measured_names(ROOT)
print(f"malte i alt: {len(names)}")

rows = []
for path in sorted((ROOT / "dist").rglob("*.html")):
    text = path.read_text(encoding="utf-8", errors="ignore")
    rel = path.relative_to(ROOT / "dist").as_posix()
    has_inline = bool(_trackers(text))
    loads_track_js = bool(RE_TRACK_JS.search(text))
    for href in set(RE_HREF.findall(text)):
        if href.startswith(("mailto:", "tel:", "javascript:", "//", "#")):
            continue
        if href.startswith(("http://", "https://")):
            m = RE_ABS.match(href)
            if not m:
                continue
            kind, name = "abs", m.group(2)
        else:
            seg = re.fullmatch(r"/(?:da/)?([a-z0-9-]+)/?(?:\.html)?(?:#[^#]*)?", href)
            if not seg:
                continue
            kind, name = "rel", seg.group(1)
        if not name or name in names:
            continue
        # ubefalet: kan dette klik overhovedet sendes noget?
        if kind == "abs":
            sendes = (not has_inline) and loads_track_js
        else:
            sendes = False  # hverken inline-whitelist (mangler navnet) eller track.js
        rows.append((kind, name, rel, has_inline, loads_track_js, sendes))

from collections import Counter  # noqa: E402
c = Counter((r[0], r[1]) for r in rows)
print(f"\nubefalede dist-links i alt: {len(rows)}")
print(f"  rodrelative: {sum(1 for r in rows if r[0]=='rel')}")
print(f"  absolut krydsdomaene: {sum(1 for r in rows if r[0]=='abs')}")
print(f"  af de absolutte: sendes alligevel (ingen inline-tracker): "
      f"{sum(1 for r in rows if r[0]=='abs' and r[5])}")
print("\nTop 12 efter antal ubefalede dist-links:")
for (kind, name), n in c.most_common(12):
    print(f"  {n:>4}  {kind}  /{name}")
