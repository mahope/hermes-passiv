#!/usr/bin/env python3
"""Iteration 465: FAQ + FAQPage JSON-LD for the remaining free tool pages.

Same pattern as iter464_tool_faqs.py. Idempotent: second run changes nothing.
Covers (EN): color-blindness-simulator, security-headers-check, site-icons,
text-on-image-checker, url-to-markdown, contrast-checker, cookie-check.
Plus DA mirrors that lack any FAQ: color-blindness-simulator-da,
text-on-image-checker-da, contrast-checker-da, palette-generator-da.
"""
import json, os, re

ROOT = '/Users/madsholstjensen/hermes-passiv'
SITE = os.path.join(ROOT, 'site')
BASE = 'https://hermes-passiv.pages.dev'

FAQS = {
'color-blindness-simulator': [
 ('How accurate is the simulation?',
  'The tool uses the standard Machado et al. (2009) severity model for protanopia, '
  'deuteranopia and tritanopia — the same matrices used in professional design tools. '
  'It approximates how colors are perceived, but only a clinical test can diagnose '
  'color vision deficiency in a person.'),
 ('Are my colors uploaded anywhere?',
  'No. The simulation runs entirely in JavaScript in your browser. Your palette never '
  'leaves your device.'),
 ('Which type should I check against?',
  'Deuteranomaly (red-green) is by far the most common, so start there. If your design '
  'works for deuteranopia and tritanopia, it will almost always work for rarer types too. '
  'Check both text contrast and chart/status colors.'),
 ('Does this replace a WCAG contrast check?',
  'No — they answer different questions. A contrast checker tells you whether text is '
  'readable; this simulator shows whether two hues remain distinguishable when color '
  'vision is impaired. Use both: contrast for legibility, simulation for color coding.'),
],
'security-headers-check': [
 ('What are security headers?',
  'They are HTTP response headers a server sends to harden the browser: '
  'Content-Security-Policy limits what scripts can run, Strict-Transport-Security forces '
  'HTTPS, X-Content-Type-Options stops MIME sniffing, and others control framing and '
  'referrer leakage. They cost nothing to add and block whole attack classes.'),
 ('Is my URL logged or stored?',
  'No. The lookup happens from your browser directly against the site you enter — this '
  'page has no backend that records what you scan.'),
 ('Why does my site score badly even though it works fine?',
  'Headers do not affect how a page looks, only how browsers treat it. Most sites ship '
  'without CSP or HSTS because frameworks do not add them by default. The fix is usually '
  'a few lines in your web server or hosting configuration.'),
 ('Can I copy the recommended headers directly?',
  'Yes. Each missing header comes with a suggested value you can paste into nginx, Apache, '
  'Netlify, Vercel or Cloudflare settings. Test after deploying — an overly strict CSP can '
  'break inline scripts until tuned.'),
],
'site-icons': [
 ('What icons does it find?',
  'Favicons of every declared size and format (ICO, PNG, SVG), Apple touch icons, and the '
  'manifest-declared icons used by Android/Chrome when a user installs your site as an app.'),
 ('Why do I need icons beyond the favicon?',
  'Each context picks its own icon: browser tab (16–32 px), iOS home screen (180 px), '
  'Android install/PWA splash (192 and 512 px), and social link previews. Missing sizes '
  'get scaled up and look blurry exactly where users notice most.'),
 ('Does it upload my files?',
  'No. You enter a URL and the checks read what the site publicly serves. Nothing is '
  'stored on our side.'),
 ('My favicon works in the tab but not elsewhere — why?',
  'Browsers fall back to /favicon.ico even with no HTML tag, but iOS home screens, PWA '
  'installs and many link previews only use explicitly linked icons. Add the full set of '
  'link tags and manifest entries this tool lists as missing.'),
],
'text-on-image-checker': [
 ('How is readability measured?',
  'The tool computes WCAG-style contrast between your text color and representative '
  'background regions of the image, then flags areas where the ratio falls below 4.5:1 '
  '(normal text) or 3:1 (large text). It is an approximation — judge busy photographic '
  'areas visually too.'),
 ('What is the fastest fix for unreadable text on an image?',
  'Add a scrim: a semi-transparent dark overlay behind the text, or place text on a solid '
  'band. Both raise contrast dramatically without changing your image or brand colors.'),
 ('Are my images uploaded?',
  'No. Everything runs locally in your browser using canvas — the image file never leaves '
  'your device.'),
 ('Does this matter for accessibility compliance?',
  'Yes. WCAG 2.x requires 4.5:1 contrast for normal text regardless of background type, '
  'and the EU Accessibility Act pushes public-facing sites toward conformance. Text baked '
  'into images cannot be zoomed, translated or selected either — prefer real HTML text '
  'where you can.'),
],
'url-to-markdown': [
 ('What gets converted?',
  'The readable content of the page: headings, paragraphs, lists, links, images and code '
  'blocks become Markdown. Navigation bars, ads, cookie banners and other boilerplate are '
  'stripped where possible.'),
 ('Do internal links stay clickable?',
  'Yes. Links are preserved as [text](url) with absolute URLs, so the output navigates '
  'the same way the original page did.'),
 ('Is anything sent to a server?',
  'Fetching and conversion happen in your browser. Pages that block cross-origin requests '
  'may fail because of CORS rules enforced by your browser — those pages simply cannot be '
  'fetched client-side, through no fault of the tool.'),
 ('Can I convert pages I have to log in to?',
  'Only if your browser already has access and CORS allows reading the response. For '
  'paywalled or private pages, copy the visible text instead and convert it manually — '
  'respect copyright and access terms either way.'),
],
'contrast-checker': [
 ('What ratios do AA and AAA require?',
  'WCAG 2.x AA requires 4.5:1 for normal text and 3:1 for large text (18 pt or 14 pt bold '
  'and up). AAA raises this to 7:1 and 4.5:1 respectively. Non-text UI components like '
  'input borders need 3:1 under AA.'),
 ('How is contrast ratio calculated?',
  'Relative luminance of both colors is computed per the WCAG formula (sRGB values '
  'linearized, then weighted 0.2126 R + 0.7152 G + 0.0722 B), and the lighter value is '
  'divided by the darker plus 0.05. The result ranges from 1:1 to 21:1.'),
 ('Does it check more than foreground/background pairs?',
  'You can test any pair of colors, including disabled states and placeholder text. Note '
  'that WCAG exempts logotypes and purely decorative elements from the thresholds.'),
 ('Why does white text on my brand color fail?',
  'Many mid-tone brand colors (yellows, light blues, tans) have high luminance, so white '
  'on top yields ratios near 2:1. Switching to dark text often passes instantly — try '
  'both directions before redesigning the palette.'),
],
'cookie-check': [
 ('What does the scan look at?',
  'It reads the cookies, localStorage keys and tracking scripts a page sets in your '
  'browser, and compares them against common consent categories (necessary, functional, '
  'analytics, marketing) under GDPR/ePrivacy expectations.'),
 ('Is scanning a website legal?',
  'Checking what a public page sets in your own browser is ordinary inspection — every '
  'browser DevTools shows the same data. We do not probe private systems or bypass access '
  'controls.'),
 ('It found cookies firing before consent — now what?',
  'That is the classic GDPR violation: non-necessary cookies must wait for explicit '
  'consent. Fix by loading analytics/marketing tags only inside your consent platform\'s '
  'callback, and re-scan to confirm.'),
 ('Does a clean result mean I am fully GDPR-compliant?',
  'No. This covers technical cookie behavior. A compliant setup also needs a proper '
  'consent banner with equal accept/reject options, a privacy policy, and records of '
  'consent. Treat the scan as one layer of an audit, not the whole audit.'),
],
# --- Danish mirrors, no existing FAQ ---
'palette-generator-da.html': [
 ('Hvad betyder WCAG AA og AAA?',
  'Det er kontrastniveauer fra Web Content Accessibility Guidelines. AA kræver en '
  'kontrast på mindst 4,5:1 for almindelig tekst (3:1 for stor tekst); AAA kræver 7:1. '
  'Hver genereret palet viser de præcise tal, så du kan vælge kombinationer der overholder reglerne.'),
 ('Må jeg bruge paletterne kommercielt?',
  'Ja. Farvekombinationerne er dine at bruge i alle projekter — de beregnes ud fra din '
  'basisfarve og har ingen licensbegrænsninger.'),
 ('Virker det til dark mode?',
  'Ja. Generér fra en mørk basisfarve og få lyse tekstparinger, og tjek tallene på samme '
  'måde. Dark mode kræver ofte højere kontrast end man tror — verificér i stedet for at gætte.'),
 ('Sendes mine farver nogetsted hen?',
  'Nej. Paletter beregnes lokalt i din browser med JavaScript — intet forlader din enhed.'),
],
}

def jsonld(faqs):
    return json.dumps({
        '@context': 'https://schema.org', '@type': 'FAQPage',
        'mainEntity': [{'@type': 'Question', 'name': q,
                        'acceptedAnswer': {'@type': 'Answer', 'text': a}}
                       for q, a in faqs],
    }, ensure_ascii=False)

def faq_section_html(faqs):
    cards = '\n      '.join(
        f'<div class="card"><h3>{q}</h3><p>{a}</p></div>' for q, a in faqs)
    if 'da' in faqs[0][0] or any(ord(c) > 127 for c in faqs[0][0]):
        heading = 'Ofte stillede spørgsmål'
    else:
        heading = 'Frequently asked questions'
    return f'''<section style="margin:2.5rem 0;">
  <h2>{heading}</h2>
  <div class="problem-cards" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:1rem;">
      {cards}
  </div>
</section>

'''

def main():
    changed = []
    for slug, faqs in FAQS.items():
        fname = slug if slug.endswith('.html') else slug + '.html'
        path = os.path.join(SITE, fname)
        c = open(path).read()
        if 'FAQPage' in c:
            print(f'{slug}: ok (already has FAQPage)')
            continue
        assert c.count('</main>') == 1, slug
        c = c.replace('</main>', faq_section_html(faqs) + '</main>', 1)
        head_anchor = '</head>'
        assert c.count(head_anchor) == 1, slug
        c = c.replace(head_anchor,
                      '<script type="application/ld+json">\n' + jsonld(faqs)
                      + '\n</script>\n' + head_anchor, 1)
        open(path, 'w').write(c)
        changed.append(slug)
        print(f'{slug}: UPDATED')
    # validate everything
    for slug in FAQS:
        fname = slug if slug.endswith('.html') else slug + '.html'
        c = open(os.path.join(SITE, fname)).read()
        types = []
        for b in re.findall(r'<script type="application/ld\+json">(.*?)</script>',
                            c, re.DOTALL):
            p = json.loads(b)
            assert p['@context'] == 'https://schema.org'
            types.append(p['@type'])
        assert 'FAQPage' in types, (slug, types)
    print('changed:', len(changed), changed)

if __name__ == '__main__':
    main()
