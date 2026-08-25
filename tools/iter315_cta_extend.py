#!/usr/bin/env python3
"""Iter 315: extend compliance-site-check CTA coverage to remaining relevant
blogs (EN + DA) and all CMS guide pages. Same marker/style as iter313.
Idempotent via MARKER. Guides get a variant mentioning the platform by name.
"""
import re

MARKER = '<!-- iter313 cta-scan -->'

EN_BLOGS = [
    "site/blog/accessibility-scanner-cli.html",
    "site/blog/how-to-write-accessibility-statement.html",
    "site/blog/gdpr-vs-nis2-overlap.html",
    "site/blog/nis2-checklist-pdf.html",
    "site/blog/nis2-gap-assessment-guide.html",
    "site/blog/nis2-incident-report-checklist.html",
    "site/blog/nis2-supply-chain-security.html",
]
DA_BLOGS = [
    "site/da/blog/eaa-frist-hvad-nu.html",
    "site/da/blog/eaa-haandhaevelse-2026.html",
    "site/da/blog/gdpr-vs-nis2-overlap-da.html",
    "site/da/blog/nis2-tjekliste-25-punkter.html",
    "site/da/blog/nis2-gapanalyse-guide.html",
    "site/da/blog/nis2-haendelsesrapport-skabelon.html",
    "site/da/blog/nis2-leverandoerkaede-sikkerhed.html",
]
# guides: (path, platform display name)
GUIDES = [
    ("site/guides/wordpress-accessibility-check.html", "WordPress"),
    ("site/guides/shopify-accessibility-check.html", "Shopify"),
    ("site/guides/webflow-accessibility-check.html", "Webflow"),
    ("site/guides/wix-accessibility-check.html", "Wix"),
    ("site/guides/squarespace-accessibility-check.html", "Squarespace"),
    ("site/guides/drupal-accessibility-check.html", "Drupal"),
    ("site/guides/joomla-accessibility-check.html", "Joomla"),
    ("site/guides/prestashop-accessibility-check.html", "PrestaShop"),
    ("site/guides/weebly-accessibility-check.html", "Weebly"),
    ("site/guides/magento-accessibility-check.html", "Magento"),
    ("site/guides/ghost-accessibility-check.html", "Ghost"),
    ("site/guides/typo3-accessibility-check.html", "TYPO3"),
    ("site/guides/craftcms-accessibility-check.html", "Craft CMS"),
    ("site/guides/umbraco-accessibility-check.html", "Umbraco"),
]

def cta_en():
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

def cta_guide(platform):
    return f'''{MARKER}
<aside class="cta-scan" style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:10px;padding:18px 22px;margin:28px 0;">
  <strong>Free compliance scan for {platform} sites</strong>
  <p style="margin:8px 0 12px;font-size:14px;color:#374151;">Beyond accessibility, our free Website Compliance Checker also checks privacy policy, cookie consent, imprint, security headers and hreflang — 9 checks on any public URL, no signup. Works on {platform} and any other platform.</p>
  <a href="/compliance-site-check" style="color:#1d4ed8;font-weight:600;text-decoration:none;">Run a free compliance scan →</a>
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
    m = re.search(r'<h2[\s>]', html)
    if not m:
        return (path, 'no-h2')
    idx = m.start()
    with open(path, 'w') as f:
        f.write(html[:idx] + cta + html[idx:])
    return (path, 'inserted')

results = []
for p in EN_BLOGS:
    results.append(process(p, cta_en()))
for p in DA_BLOGS:
    results.append(process(p, cta_da()))
for p, plat in GUIDES:
    results.append(process(p, cta_guide(plat)))

for p, s in results:
    print(f'{s:10} {p}')
print('total:', len(results), '| inserted:', sum(1 for _, s in results if s == 'inserted'))
