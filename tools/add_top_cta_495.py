
import re, glob

EN_CTA = ('<div class="blog-tool-cta"><span class="btc-label">Check any page for GDPR &amp; cookie issues:</span>'
          ' <a href="/scan" class="btn-primary">Run the Free Scanner \u2192</a></div>\n'
          '<div class="blog-tool-cta ai-cta"><span class="btc-label">Ask any EU compliance question \u2014 EAA, NIS2 or GDPR \u2014 and get a practical answer in seconds:</span>'
          ' <a href="/compliance-ai" class="btn-primary ai-cta-link" data-track="ai-cta">\U0001F916 Ask the Compliance AI \u2192</a></div>\n')
DA_CTA = ('<div class="blog-tool-cta"><span class="btc-label">Tjek enhver side for GDPR- og cookie-problemer:</span>'
          ' <a href="/scan-da" class="btn-primary">Pr\u00f8v den gratis scanner \u2192</a></div>\n'
          '<div class="blog-tool-cta ai-cta"><span class="btc-label">Stil et sp\u00f8rgsm\u00e5l om EU-compliance \u2014 EAA, NIS2 eller GDPR \u2014 og f\u00e5 et praktisk svar p\u00e5 f\u00e5 sekunder:</span>'
          ' <a href="/da/compliance-ai" class="btn-primary ai-cta-link" data-track="ai-cta">\U0001F916 Sp\u00f8rg Compliance-AI\u2019en \u2192</a></div>\n')

changed = 0
for path in glob.glob('site/blog/*.html') + glob.glob('site/da/blog/*.html'):
    src = open(path, encoding='utf-8').read()
    if 'blog-tool-cta' in src or '/header' not in src:
        continue
    cta = DA_CTA if '/da/' in path else EN_CTA
    new = src.replace('</header>\n', '</header>\n' + cta, 1)
    if new == src:
        # try without trailing newline strictness
        new = re.sub(r'</header>\s*\n', lambda m: m.group(0) + cta, src, count=1)
    if new != src:
        open(path, 'w', encoding='utf-8').write(new)
        changed += 1
print('files updated:', changed)
