#!/usr/bin/env python3
"""Iteration 464: FAQ + FAQPage JSON-LD for 9 free tool pages.

Same pattern as iter463_b64_faq.py. Idempotent: second run changes nothing.
For url-encoder-decoder an HTML FAQ already exists -> only FAQPage JSON-LD is
added, built from its existing Q/A paragraphs.
"""
import json, os, re

ROOT = '/Users/madsholstjensen/hermes-passiv'
SITE = os.path.join(ROOT, 'site')
BASE = 'https://hermes-passiv.pages.dev'

FAQS = {
'hash-generator': [
 ('Is it safe to hash passwords with SHA-256 here?',
  'SHA-256 alone is not a password-hashing scheme — it is fast by design. For storing '
  'passwords use a dedicated slow algorithm such as bcrypt, scrypt or Argon2 in your own '
  'backend. This tool is for verifying file integrity, deduplicating content and building '
  'cache keys.'),
 ('Does my text get uploaded when I hash it?',
  'No. Hashing runs entirely in JavaScript in your browser using the Web Crypto API. The '
  'text never leaves your device, so hashing sensitive strings is safe.'),
 ('Which algorithm should I choose?',
  'SHA-256 is the modern default and what you should reach for first. SHA-1 is broken for '
  'security purposes but still appears in legacy systems like old Git objects. MD5 is shown '
  'for compatibility checks only — never use it for anything security-related.'),
 ('Why do two different texts sometimes give the same hash?',
  'They should not, practically speaking. A collision on SHA-256 requires roughly 2^256/2 '
  'attempts — impossible with current technology. If you see a collision, the inputs are '
  'almost certainly identical after invisible characters like trailing spaces are accounted for.'),
],
'text-diff': [
 ('Is my text sent to a server?',
  'No. The comparison runs entirely in your browser with JavaScript — nothing you paste is '
  'transmitted or stored, so comparing confidential documents and source code is safe.'),
 ('What do the colors mean?',
  'Red lines exist only in the left (original) text and were removed. Green lines exist only '
  'in the right (changed) text and were added. Lines that match exactly are shown unmarked.'),
 ('Can it compare code as well as prose?',
  'Yes. The diff works line by line on any plain text, so source files, config files, JSON, '
  'and legal drafts all work. For very large files (tens of thousands of lines) the browser '
  'may slow down — split the input if that happens.'),
 ('Does whitespace matter?',
  'Yes, by default every space counts, because in code and contracts a changed indent can be '
  'meaningful. Normalize the texts first (trim trailing spaces) if you want to ignore those '
  'differences.'),
],
'word-counter': [
 ('How is reading time calculated?',
  'Reading time uses an average of 200 words per minute for silent reading, rounded up to '
  'the nearest minute. Treat it as an estimate — technical content and non-native readers '
  'are usually slower.'),
 ('Do Danish characters and emoji count correctly?',
  'Yes. Words are counted by splitting on whitespace, so æøå, accented letters and emoji all '
  'count naturally, and multiple spaces or line breaks between words are not miscounted.'),
 ('Is there a character limit?',
  'No hard limit — counting happens locally in your browser. Very large texts (hundreds of '
  'thousands of words) may take a moment but will complete.'),
 ('Why do platforms count characters differently?',
  'Some platforms count every character including spaces (X/Twitter), others count only '
  'letters, and CJK languages count characters rather than words. Use the character count '
  'with spaces for social media limits.'),
],
'json-formatter': [
 ('Is my JSON uploaded anywhere?',
  'No. Parsing, formatting and validation all run locally in your browser. Nothing is sent '
  'to a server, so API responses containing real data or tokens are safe to paste.'),
 ('What does "valid JSON" actually check?',
  'The validator follows RFC 8259: proper quoting, no trailing commas, no single quotes, no '
  'comments, and no unquoted keys. If validation fails, the error message points to the '
  'line and position of the first problem found.'),
 ('Will formatting change my data?',
  'No. Formatting only changes whitespace and indentation — keys, values and ordering are '
  'preserved exactly. Numbers keep their value, though very large numbers may be displayed '
  'in scientific notation by JavaScript.'),
 ('Can it sort keys or minify?',
  'Minify removes all unnecessary whitespace to produce the most compact valid output. Key '
  'sorting preserves object semantics because JSON objects are unordered by specification — '
  'only arrays have a guaranteed order.'),
],
'uuid-generator': [
 ('Are these UUIDs really unique?',
  'Version 4 UUIDs contain 122 random bits. The probability of a collision among trillions '
  'of generated UUIDs is astronomically small — small enough that v4 uniqueness is treated '
  'as guaranteed in practice. Randomness comes from your browser\'s cryptographic random '
  'number generator.'),
 ('Can someone guess a UUID I generated?',
  'Practically no. With 122 random bits, brute-forcing a specific v4 UUID is infeasible. '
  'Still, UUIDs are identifiers, not secrets — do not use them as authentication tokens or '
  'passwords.'),
 ('What is the difference between v4 and other versions?',
  'v1 uses timestamps and MAC addresses (leaks information), v3/v5 derive from a name via '
  'hashing (deterministic), and v7 encodes a timestamp (sortable). v4 is fully random and '
  'the right default unless you need a specific property of another version.'),
 ('Is there a limit on how many I can generate?',
  'No. Generation runs locally in your browser with no server involved — generate as many '
  'as you need, in bulk if required.'),
],
'case-converter': [
 ('Which cases are supported?',
  'UPPERCASE, lowercase, Title Case, Sentence case, camelCase, PascalCase, snake_case and '
  'kebab-case. The programming cases (camel/snake/kebab) handle mixed input like '
  '"HTTP Response Code" or "user_name" sensibly.'),
 ('Does converting change my text otherwise?',
  'No. Only letter casing and, for the programming formats, separators are touched. Accents '
  'like é and Æ, numbers and punctuation are preserved.'),
 ('Is my text uploaded?',
  'No. Conversion runs entirely in your browser — nothing leaves your device.'),
 ('When should I use snake_case vs kebab-case?',
  'snake_case is conventional for variable names in Python and database columns. kebab-case '
  'is standard for URLs, CSS class names, file names and HTML attributes, because hyphens '
  'are URL-safe while underscores are not.'),
],
'markdown-table-generator': [
 ('What input formats does it accept?',
  'CSV (comma-separated) and TSV (tab-separated), including quoted fields with embedded '
  'commas. Paste directly from Excel or Google Sheets too — copied spreadsheet cells arrive '
  'as tab-separated values and are detected automatically.'),
 ('How are pipes inside cells handled?',
  'Cells containing the pipe character | are escaped as \\| in the Markdown output, per the '
  'CommonMark table spec, so the table structure stays intact when rendered.'),
 ('Does it support alignment columns?',
  'Yes. You choose left, center or right alignment per column, and the generator writes the '
  'corresponding colon placement in the separator row (e.g. :---, :---:, ---:).'),
 ('Will GitHub render the result correctly?',
  'Yes. The output follows GitHub Flavored Markdown tables, which is also supported by GitLab, '
  'Obsidian, VS Code preview and most Markdown renderers.'),
],
'palette-generator': [
 ('What do WCAG AA and AAA mean?',
  'They are contrast levels from the Web Content Accessibility Guidelines. AA requires a '
  'contrast ratio of at least 4.5:1 for normal text (3:1 for large text); AAA raises this to '
  '7:1. Every palette generated here shows the exact ratios so you can pick compliant pairs.'),
 ('Is contrast ratio about text only?',
  'Text needs to meet the thresholds above. Non-text UI elements like buttons, form borders '
  'and icons need 3:1 under AA. The generator labels which pairs are safe for each use.'),
 ('Can I use the palette commercially?',
  'Yes. The generated color combinations are yours to use in any project — palettes are '
  'derived from your base color mathematically and carry no license restrictions.'),
 ('Does it work for dark mode designs?',
  'Yes. Generate from a dark base color to get light text pairings, and check the ratios the '
  'same way. Dark mode often needs higher contrast than you expect — verify rather than eyeball.'),
],
'url-encoder-decoder': [],  # FAQ exists in HTML; JSON-LD built from it below.
}

def faq_section_html(faqs):
    cards = '\n      '.join(
        f'<div class="card"><h3>{q}</h3><p>{a}</p></div>' for q, a in faqs)
    return f'''<section style="margin:2.5rem 0;">
  <h2>Frequently asked questions</h2>
  <div class="problem-cards" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:1rem;">
      {cards}
  </div>
</section>

'''

def jsonld(faqs):
    return json.dumps({
        '@context': 'https://schema.org', '@type': 'FAQPage',
        'mainEntity': [{'@type': 'Question', 'name': q,
                        'acceptedAnswer': {'@type': 'Answer', 'text': a}}
                       for q, a in faqs],
    }, ensure_ascii=False)

def extract_urlenc_faqs(c):
    sec = c[c.find('<h3>FAQ</h3>'):]
    out = []
    for q, a in re.findall(r'<p><strong>([^<]+)</strong>\s*(.*?)</p>', sec, re.DOTALL):
        a = re.sub(r'<[^>]+>', '', a).strip()
        out.append((q.strip(), a))
    return out

def main():
    changed = []
    for slug, faqs in FAQS.items():
        path = os.path.join(SITE, slug + '.html')
        c = open(path).read()
        orig = c
        if slug == 'url-encoder-decoder':
            faqs = extract_urlenc_faqs(c)
            assert len(faqs) >= 4, faqs
        if 'FAQPage' not in c:
            if faqs:
                assert c.count('</main>') == 1
                c = c.replace('</main>', faq_section_html(faqs) + '</main>', 1)
            head_anchor = '</head>'
            assert c.count(head_anchor) == 1
            c = c.replace(head_anchor,
                          '<script type="application/ld+json">\n' + jsonld(faqs)
                          + '\n</script>\n' + head_anchor, 1)
            open(path, 'w').write(c)
            changed.append(slug)
        # validate all JSON-LD blocks regardless
        types = []
        for b in re.findall(r'<script type="application/ld\+json">(.*?)</script>',
                            c, re.DOTALL):
            p = json.loads(b)
            assert p['@context'] == 'https://schema.org'
            types.append(p['@type'])
        assert 'FAQPage' in types, (slug, types)
        status = 'UPDATED' if path != None and slug in changed else 'ok'
        print(f'{slug}: {status} JSON-LD={types}')
    print('changed:', len(changed), changed)

if __name__ == '__main__':
    main()
