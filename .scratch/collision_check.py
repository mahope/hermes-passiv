#!/usr/bin/env python3
"""Kollisionskontrol: naar vi gjoer ruterne maalbare, deler de et navn med en
allerede maalt rute, eller med hinanden? Saa slaar to sider sammen i egen begivenhed."""
import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
out = subprocess.run([sys.executable, str(ROOT / "tools" / "audit_unmeasured_routes.py"),
                      "--json"], capture_output=True, text=True).stdout
d = json.loads(out)
measured = set(d["measured"])
rows = d["unmeasured"]

byname = defaultdict(list)
for r in rows:
    byname[r["name"]].append(r["route"])

print("=== navne der allerede er malte (ville vaere doplikat i alternativet) ===")
dup = [n for n in byname if n in measured]
print("  " + (", ".join(sorted(dup)) if dup else "(ingen)"))

print("\n=== navne der bruges af flere ruter (slaar sammen i 'cta-<navn>') ===")
coll = {n: v for n, v in byname.items() if len(v) > 1}
print("  " + (json.dumps(coll, indent=2) if coll else "(ingen)"))

print("\n=== de 35 ubefalede ruter, med beslutning ===")
# /privacy og /terms ligger i footeren paa 320 sider. De faar allerede en
# sidevisning, fordi track.js sender en pageview-begivenhed per sideindlaesning.
# En 'cta-privacy' paa 320 sider er stoej, ikke salg, saa de skal bevidst holdes ude.
HELD_UD = {"privacy", "terms"}
for r in rows:
    beslutning = "HOLDES UDE (sidevisning dækker den)" if r["name"] in HELD_UD else "maales"
    print(f"  {beslutning:<36} {r['name']:<38} {r['total_links']:>4} links  {r['route']}")
