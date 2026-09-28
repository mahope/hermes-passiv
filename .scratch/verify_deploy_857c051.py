#!/usr/bin/env python3
"""Luk VERIFICER DEPLOY-noten for merge 857c051 paa indhold, et kald, ingen polling."""
import re
import subprocess
import sys
import tempfile
import os

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120 Safari/537.36")

PAGES = {
    "ft": "https://mahope.tools/free-tools",
    "ccb": "https://mahope.tools/cookie-consent-banner-demo",
    "dtt": "https://mahope.tools/blog/developer-text-tools",
    "sd": "https://mahope.tools/scan-da",
}

tmp = tempfile.mkdtemp(prefix="deploycheck")
html = {}
for key, url in PAGES.items():
    path = os.path.join(tmp, key + ".html")
    subprocess.run(["curl", "-s", "-A", UA, url, "-o", path], check=True)
    html[key] = open(path, encoding="utf-8").read()

# Den indlejrede trackers alternativ: regex-kilden i `var m=h.match(/^\/…/)`
# der sendes videre som event:'cta-'+m[1]
ALT = re.compile(r"match\((?P<re>/\^\\?/\(\?:da\\/\)\?\((?P<names>[^)]*)\))")


def alt_names(doc):
    m = ALT.search(doc)
    if not m:
        return None, []
    src = m.group("re")
    names = [n for n in m.group("names").split("|")
             if re.fullmatch(r"[a-z0-9][a-z0-9_\-]*", n)]
    return src, names


ok = True


def check(label, cond, detail=""):
    global ok
    if not cond:
        ok = False
    print(f"  {'OK  ' if cond else 'FEJL'} {label}{(' — ' + detail) if detail else ''}")


print("(a) /free-tools")
ft = html["ft"]
check("href free-downloads findes", len(re.findall(r'href="[^"]*free-downloads', ft)) >= 1,
      f"{len(re.findall(chr(34).join(['href=', '[^', ']*free-downloads']) , ft))}")
src, names = alt_names(ft)
print(f"       tracker-alternativ fundet: {bool(src)}, {len(names)} navn")
check("free-downloads i tracker-alternativet", "free-downloads" in names)
check("mindst 20 navn i alternativet", len(names) >= 20, f"{len(names)}")

print("(b) /cookie-consent-banner-demo")
check("1 /track.js-tag", len(re.findall(r'src="/track\.js"', html["ccb"])) == 1,
      str(len(re.findall(r'src="/track\.js"', html["ccb"]))))

print("(c) /blog/developer-text-tools — alle 5 i tracker-alternativet")
src2, names2 = alt_names(html["dtt"])
print(f"       tracker-alternativ fundet: {bool(src2)}, {len(names2)} navn")
for n in ["word-counter", "json-formatter", "case-converter", "hash-generator",
          "url-encoder-decoder"]:
    check(n, n in names2)

print("(d) /scan-da — ingen nye navn, fjerde form urort")
src3, names3 = alt_names(html["sd"])
print(f"       tracker-alternativ: {src3!r}")
new = [n for n in ["word-counter", "json-formatter", "case-converter", "hash-generator",
                   "url-encoder-decoder", "free-downloads"] if n in names3]
check("0 nye navn", not new, str(new))
check("(da/)?-form bevaret", "(da\\/)?".replace("\\", "\\") in html["sd"] or "(da\\/)?" in html["sd"])
check("0 (?:da/) i gammel forventet form", html["sd"].count("(?:da\\/)") == 0,
      str(html["sd"].count("(?:da\\/)")))

print()
print("RESULTAT:", "ALLE FIRE INDHOLDSKRAV HOLDER" if ok else "NOGET HOLDT IKKE")
sys.exit(0 if ok else 1)
