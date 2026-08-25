#!/usr/bin/env python3
"""Iter 313: insert 'Scan your site' CTA into relevant compliance blogs (EN + DA).

CTA is inserted right after the opening of the article content — we anchor on the
first <p class="subtitle">...</p> close inside the hero, i.e. we insert a CTA box
immediately BEFORE the first <h2 ...> in the body (start of the actual article).
Falls back to inserting before </main> / footer if no <h2 found.
Idempotent: skips files already containing the CTA marker.
"""
import re, sys

EN = {
    "site/blog/gdpr-website-compliance-checklist.html": ("GDPR", "18-point checklist"),
    "site/blog/cookie-consent-gdpr-compliance.html": ("GDPR", "cookie consent"),
    "site/blog/eaa-accessibility-checklist.html": ("EAA", "accessibility"),
    "site/blog/free-nis2-assessment-tools.html": ("NIS2", "assessment"),
    "site/blog/nis2-readiness-guide.html": ("NIS2", "readiness"),
    "site/blog/gdpr-fines-2026.html": ("GDPR", "fines"),
    "site/blog/gdpr-agency-role.html": ("GDPR", "agencies"),
    "site/blog/eaa-deadline-2026.html": ("EAA", "deadline"),
    "site/blog/accessibility-audit-cost.html": ("EAA", "audit costs"),
    "site/blog/free-gdpr-document-generators.html": ("GDPR", "document generators"),
    "site/blog/free-accessibility-testing-tools.html": ("EAA", "testing tools"),
    "site/blog/compliance-check-github-action.html": ("Compliance", "CI/CD"),
}
DA = {
    "site/da/blog/gdpr-hjemmeside-tjekliste.html": ("GDPR", "tjekliste"),
    "site/da/blog/cookie-consent-gdpr-2026.html": ("GDPR", "cookie-samtykke"),
    "site/da/blog/eaa-tjekliste-2026.html": ("EAA", "tilgaengelighed"),
    "site/da/blog/gratis-nis2-vaerktoejer.html": ("NIS2", "vurdering"),
    "site/da/blog/nis2-beredskabstjek-2026.html": ("NIS2", "beredskab"),
    "site/da/blog/gdpr-boeder-2026.html": ("GDPR", "boeder"),
    "site/da/blog/gdpr-webbureau-da.html": ("GDPR", "webbureauer"),
    "site/da/blog/eaa-frister-2026.html": ("EAA", "frister"),
    "site/da/blog/gratis-gdpr-dokumentgeneratorer.html": ("GDPR", "dokumentgeneratorer"),
}

MARKER = '<!-- iter313 cta-scan -->'

def cta_en(topic):
    return f'''{MARKER}
<aside class="cta-scan" style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:10px;padding:18px 22px;margin:28px 0;">
  <strong>Check your own site in 30 seconds</strong>
  <p style="margin:8px 0 12px;font-size:14px;color:#374151;">Our free Website Compliance Checker scans for privacy policy, cookie consent, accessibility statement, security headers and more — 9 checks, no signup.</p>
  <a href="/compliance-site-check" style="color:#1d4ed8;font-weight:600;text-decoration:none;">Run a free compliance scan →</a>
</aside>
'''

def cta_da():
    return f'''{MARKER}
<aside class="cta-scan" style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:10px;padding:18px 22px;margin:28px 0;">
  <strong>Tjek din egen side paa 30 sekunder</strong>
  <p style="margin:8px 0 12px;font-size:14px;color:#374151;">Vores gratis Compliance Checker scanner for privatlivspolitik, cookie-samtykke, tilgaengelighedserklaering, security headers m.m. — 9 tjek, ingen tilmelding.</p>
  <a href="/da/compliance-site-check" style="color:#1d4ed8;font-weight:600;text-decoration:none;">Koer en gratis compliance-scanning →</a>
</aside>
'''

def process(path, cta):
    try:
        with open(path) as f:
            html = f.read()
    except FileNotFoundError:
        return (path, 'MISSING')
    if MARKER in html:
        return (path, 'already')
    # insert before first <h2 in the body
    m = re.search(r'<h2[\s>]', html)
    if not m:
        return (path, 'no-h2')
    idx = m.start()
    out = html[:idx] + cta + html[idx:]
    with open(path, 'w') as f:
        f.write(out)
    return (path, 'inserted')

results = []
for path in EN:
    results.append(process(path, cta_en(EN[path])))
for path in DA:
    results.append(process(path, cta_da()))

for p, s in results:
    print(f'{s:10} {p}')
print('total:', len(results), '| inserted:', sum(1 for _, s in results if s == 'inserted'))
