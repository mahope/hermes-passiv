#!/usr/bin/env python3
"""Iteration 463: Base64 tool upgrade — FAQ section + FAQPage JSON-LD.

Idempotent: second run changes nothing. Follows the same JSON-LD validation
pattern as the blog generators (parse every application/ld+json block after
writing, assert schema.org context).
"""
import json, os, re

ROOT = '/Users/madsholstjensen/hermes-passiv'
PATH = os.path.join(ROOT, 'site', 'base64-encoder-decoder.html')
URL = 'https://hermes-passiv.pages.dev/base64-encoder-decoder'

FAQS = [
    ('Is Base64 encryption?',
     'No. Base64 is an encoding, not encryption — it provides zero secrecy and '
     'anyone can decode it instantly. Use it for transport and storage formats '
     '(email attachments, data URIs, JWT segments), never to protect secrets on '
     'its own.'),
    ('Does this tool upload my data anywhere?',
     'No. Encoding and decoding run entirely in JavaScript in your browser. The '
     'text you paste never leaves your device, which makes the tool safe for '
     'tokens and other sensitive strings you are debugging.'),
    ('Can it handle Unicode, emoji and Danish characters?',
     'Yes. Both directions use UTF-8 via the TextEncoder/TextDecoder APIs, so æøå, '
     'emoji and non-Latin scripts encode and round-trip exactly.'),
    ('Why does my Base64 string fail to decode?',
     'The three usual causes are: characters outside the Base64 alphabet (A–Z, '
     'a–z, 0–9, +, / and =), a length that is not a multiple of 4 (padding is '
     'missing or has been trimmed), or a URL-safe variant using - and _ instead '
     'of + and /. Whitespace and line breaks are stripped automatically before '
     'decoding.'),
    ('What is URL-safe Base64?',
     'A variant used in JWTs and URLs where + is replaced by - and / by _, usually '
     'without padding. This tool decodes the standard alphabet; for URL-safe input, '
     'replace - with + and _ with / first, and append = until the length is a '
     'multiple of 4.'),
]

FAQ_HTML = '\n      '.join(
    f'<div class="card"><h3>{q}</h3><p>{a}</p></div>' for q, a in FAQS)

FAQ_JSON = json.dumps({
    '@context': 'https://schema.org', '@type': 'FAQPage',
    'mainEntity': [{'@type': 'Question', 'name': q,
                    'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in FAQS],
}, ensure_ascii=False)

SECTION = f'''<section style="margin:2.5rem 0;">
  <h2>Frequently asked questions</h2>
  <div class="problem-cards" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:1rem;">
      {FAQ_HTML}
  </div>
</section>

'''

ANCHOR = '</main>'

def main():
    c = open(PATH).read()
    if 'FAQPage' in c:
        print('already upgraded; validating only')
    else:
        assert c.count(ANCHOR) == 1
        c = c.replace(ANCHOR, SECTION + ANCHOR, 1)
        # insert FAQPage JSON-LD before </head>, after the existing WebApplication block
        head_anchor = '</head>'
        assert c.count(head_anchor) == 1
        c = c.replace(head_anchor,
                      '<script type="application/ld+json">\n' + FAQ_JSON + '\n</script>\n'
                      + head_anchor, 1)
        open(PATH, 'w').write(c)
        print('FAQ section + FAQPage JSON-LD inserted')

    # validate all JSON-LD blocks
    blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', c, re.DOTALL)
    types = []
    for b in blocks:
        p = json.loads(b)
        assert p['@context'] == 'https://schema.org'
        types.append(p['@type'])
    print('JSON-LD OK:', types)
    assert 'FAQPage' in types

if __name__ == '__main__':
    main()
