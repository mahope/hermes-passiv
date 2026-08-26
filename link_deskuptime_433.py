#!/usr/bin/env python3
"""Iter 433: internal linking — tilføj DeskUptime-kort/linje til alle EN-blogindlæg
der endnu ikke linker til /deskuptime/. Idempotent."""
import re, glob, os

BLOG = os.path.join(os.path.dirname(__file__), '..', 'site', 'blog')

CARD = ('\n      <div class="card"><span class="badge" style="font-size:0.75em;'
        'display:inline-block;margin-bottom:6px;">UPTIME</span><h3>'
        '<a href="/deskuptime/" style="color:var(--color-accent);text-decoration:none;">'
        'DeskUptime: Free Desktop Uptime &amp; SSL Monitor</a></h3></div>')

PARA = ('<section class="products">\n  <div class="container">\n'
        '    <p>Keeping websites online? <a href="/deskuptime/" '
        'style="color:var(--color-accent);">DeskUptime</a> is a free desktop '
        'uptime &amp; SSL-expiry monitor for macOS, Linux and Windows.</p>\n'
        '  </div>\n</section>\n\n')

added_card, added_para = [], []

for path in sorted(glob.glob(os.path.join(BLOG, '*.html'))):
    name = os.path.basename(path)
    if name == 'index.html':
        continue
    with open(path, encoding='utf-8') as f:
        html = f.read()
    if '/deskuptime/' in html:
        continue

    # Find the Related Guides heading, then the first problem-cards div after it
    m_head = re.search(r'<h2>\s*Related [Gg]uides\s*</h2>', html)
    inserted = False
    if m_head:
        m_cards = html.find('<div class="problem-cards">', m_head.end())
        if m_cards != -1:
            ins = m_cards + len('<div class="problem-cards">')
            html = html[:ins] + CARD + html[ins:]
            added_card.append(name)
            inserted = True

    if not inserted:
        # fall back: insert a small section before the first <footer
        idx = html.find('<footer')
        if idx == -1:
            print('SKIP (no anchor):', name)
            continue
        html = html[:idx] + PARA + html[idx:]
        added_para.append(name)

    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)

print(f'cards added: {len(added_card)}')
print(f'paragraphs added: {len(added_para)}')
print('cards:', ', '.join(added_card))
print('paras:', ', '.join(added_para))

# verify: every blog post now links
missing = []
for path in sorted(glob.glob(os.path.join(BLOG, '*.html'))):
    if os.path.basename(path) == 'index.html':
        continue
    with open(path, encoding='utf-8') as f:
        if '/deskuptime/' not in f.read():
            missing.append(os.path.basename(path))
print('still missing:', missing if missing else 'NONE')
