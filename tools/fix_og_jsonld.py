#!/usr/bin/env python3
"""Iteration 119: tilføj manglende og:image til alle HTML-sider under site/,
og SoftwareApplication/WebApplication JSON-LD til produktsiderne der mangler det.
Idempotent: springer sider over der allerede har et og:image."""
import os, re, json

BASE = "https://hermes-passiv.pages.dev"
SITE = os.path.join(os.path.dirname(__file__), "..", "site")
DEFAULT_IMG = BASE + "/cover.jpg"

# product pages that lack structured data entirely -> inject minimal JSON-LD
PRODUCT_LD = {
    "page-profile.html": {
        "@type": "SoftwareApplication",
        "name": "page-profile",
        "applicationCategory": "DeveloperApplication",
        "operatingSystem": "Any",
        "description": "Free CLI web page profiler: HTTP status, meta tags, Open Graph, JSON-LD, headings, alt text, security headers.",
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
    },
    "clean-copy.html": {
        "@type": "WebApplication",
        "name": "Clean Copy",
        "applicationCategory": "UtilitiesApplication",
        "operatingSystem": "Chrome",
        "description": "Chrome extension that copies selected web text as clean Markdown or plain text.",
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
    },
    "-icons.html": {
        "@type": "SoftwareApplication",
        "name": "site-icons",
        "applicationCategory": "DeveloperApplication",
        "operatingSystem": "Any",
        "description": "CLI tool that generates favicons, OG images and PWA icon sets from one source image.",
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
    },
}

og_re = re.compile(r'<meta property="og:image"')
head_end_re = re.compile(r"</head>")

def add_og_image(content):
    if '<script type="application/ld+json"' in content and False:
        pass
    tag = ('  <meta property="og:image" content="%s">\n'
           '  <meta name="twitter:card" content="summary_large_image">\n' % DEFAULT_IMG)
    m = head_end_re.search(content)
    if not m:
        return None
    return content[:m.start()] + tag + content[m.start():]

def add_jsonld(content, ld):
    block = ('\n<script type="application/ld+json">\n%s\n</script>\n' %
             json.dumps({"@context": "https://schema.org", **ld}, indent=2))
    m = head_end_re.search(content)
    if not m:
        return None
    return content[:m.start()] + block + content[m.start():]

changed = []
for root, dirs, files in os.walk(SITE):
    if "node_modules" in root:
        continue
    for f in files:
        if not f.endswith(".html"):
            continue
        p = os.path.join(root, f)
        rel = os.path.relpath(p, SITE)
        c = open(p, encoding="utf-8").read()
        orig = c
        # og:image missing?
        if "<meta property=\"og:image\"" not in c and 'property="og:image"' not in c:
            nc = add_og_image(c)
            if nc:
                c = nc
        # product JSON-LD
        key = rel if rel in PRODUCT_LD else ("/" + rel if ("/" + rel) in PRODUCT_LD else None)
        if key is None:
            base_name = rel.lstrip("./")
            if base_name in PRODUCT_LD:
                key = base_name
        if key and "application/ld+json" not in c:
            nc = add_jsonld(c, PRODUCT_LD[key])
            if nc:
                c = nc
        if c != orig:
            open(p, "w", encoding="utf-8").write(c)
            changed.append(rel)

print(f"Changed {len(changed)} files:")
for r in sorted(changed):
    print(" ", "/" + r)

# validate ALL JSON-LD blocks sitewide
bad = []
for root, dirs, files in os.walk(SITE):
    if "node_modules" in root:
        continue
    for f in files:
        if not f.endswith(".html"):
            continue
        p = os.path.join(root, f)
        c = open(p, encoding="utf-8").read()
        for i, blk in enumerate(re.findall(r'<script type="application/ld\+json">(.*?)</script>', c, re.DOTALL)):
            try:
                d = json.loads(blk)
                assert d.get("@context") == "https://schema.org"
            except Exception as e:
                bad.append((p.replace(SITE, ""), i, str(e)))
print("\nJSON-LD validation:", "ALL VALID" if not bad else bad[:20])
