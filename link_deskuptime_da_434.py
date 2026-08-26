#!/usr/bin/env python3
"""Iter 434: tilføj /deskuptime/ links til alle 55 DA-blogindlæg.
Idempotent: gør intet hvis linket allerede findes i filen."""
import glob, os, re

SITE = os.path.join(os.getcwd(), "site", "da", "blog")

CARD = '<div class="card"><span class="badge" style="font-size:0.75em;display:inline-block;margin-bottom:6px;">UPTIME</span><h3><a href="/deskuptime/" style="color:var(--color-accent);text-decoration:none;">DeskUptime: Gratis Desktop Uptime- &amp; SSL-overvågning</a></h3></div>'

INLINE = '''<section class="products">
  <div class="container">
    <p>Skal din hjemmeside holde sig online? <a href="/deskuptime/" style="color:var(--color-accent);">DeskUptime</a> er et gratis desktopprogram til uptime- og SSL-certifikatovervågning for macOS, Linux og Windows.</p>
  </div>
</section>
'''

files = sorted(glob.glob(os.path.join(SITE, "*.html")))
added_card = added_inline = 0
skipped = []
for f in files:
    html = open(f, encoding="utf-8").read()
    if "/deskuptime/" in html:
        skipped.append(f)
        continue
    m = re.search(r'(<div class="problem-cards">\s*)(<div class="card")', html)
    if m and "Relaterede guides" in html:
        html = html[:m.start(2)] + CARD + "\n      " + html[m.start(2):]
        added_card += 1
    else:
        # indsæt inline-sektion lige før footer
        fm = re.search(r'<footer', html)
        if not fm:
            print("NO FOOTER:", f)
            continue
        html = html[:fm.start()] + INLINE + html[fm.start():]
        added_inline += 1
    open(f, "w", encoding="utf-8").write(html)

print(f"cards={added_card} inline={added_inline} already-linked={len(skipped)} total={len(files)}")
