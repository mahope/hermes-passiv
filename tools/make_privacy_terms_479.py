#!/usr/bin/env python3
"""Iter 479: opret /privacy/ og /terms/ sider (extension-store krav + footer-links).
Enkle, professionelle statiske sider der daekker alle produkter (Clean Copy,
DeskUptime, Page Profile, URL Inspector, compliance-scannere)."""
import os

ROOT = '/Users/madsholstjensen/hermes-passiv'
SITE = os.path.join(ROOT, 'site')
CONTACT = 'mads@mahope.dk'
SITEURL = 'https://hermes-passiv.pages.dev'

STYLE = """
  :root{--bg:#0f1220;--card:#181c2f;--text:#e8eaf2;--muted:#9aa1b5;--accent:#6ea8fe;--border:#2a2f4a}
  *{box-sizing:border-box}
  body{margin:0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:var(--bg);color:var(--text);line-height:1.65}
  .container{max-width:760px;margin:0 auto;padding:48px 24px 80px}
  h1{font-size:2rem;margin:0 0 8px} h2{font-size:1.25rem;margin-top:40px;color:var(--accent)}
  a{color:var(--accent)} p,li{color:var(--text)} .muted{color:var(--muted)}
  header{padding:16px 24px;border-bottom:1px solid var(--border)}
  footer{border-top:1px solid var(--border);margin-top:64px;padding:24px;text-align:center;color:var(--muted);font-size:.9em}
"""

def page(title, desc, body, lang='en'):
    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{{CANON}}">
<style>{STYLE}</style>
</head>
<body>
<header><a href="/" style="color:var(--text);text-decoration:none;font-weight:600;">Mahope Tools</a></header>
<div class="container">
{body}
<footer><a href="/">Home</a> &middot; <a href="/privacy/">Privacy</a> &middot; <a href="/terms/">Terms</a></footer>
</div>
</body>
</html>"""

PRIVACY_EN = page(
    "Privacy Policy",
    "Privacy policy for Mahope Tools products and websites.",
    f"""
<h1>Privacy Policy</h1>
<p class="muted">Last updated: August 26, 2026</p>

<p>This policy covers the websites under {SITEURL} and the related products:
Clean Copy (browser extensions and CLI), DeskUptime (desktop app and CLI),
Page Profile, URL Inspector, and the compliance scanners.</p>

<h2>The short version</h2>
<ul>
<li>We do not collect, store, or transmit your personal data or your browsing data.</li>
<li>There are no accounts on this site. Nothing to sign up for, nothing leaked.</li>
<li>All tools run locally on your machine. The URLs you check stay with you.</li>
</ul>

<h2>Data we process</h2>
<p><strong>Aggregate, anonymous page-view counts.</strong> This website records
anonymous visit counts per page URL (no IP addresses stored, no cookies, no
cross-site tracking, no third-party analytics). We cannot identify you from
this data.</p>
<p><strong>Purchases.</strong> Payments are handled by Lemon Squeezy as our
merchant of record. If you buy a license, Lemon Squeezy processes your payment
details and email address under their own privacy policy. We receive only your
email address for license delivery.</p>

<h2>Your tools, your data</h2>
<p>Clean Copy, DeskUptime, Page Profile and the scanners process content and
URLs entirely on your device. No checked URL, copied text, scan result or file
is ever uploaded to us. The desktop and CLI apps make network requests only to
the sites <em>you</em> ask them to check.</p>

<h2>Contact</h2>
<p>Questions or data requests: <a href="mailto:{CONTACT}">{CONTACT}</a>.</p>
""")
PRIVACY_EN = PRIVACY_EN.replace('{CANON}', SITEURL + '/privacy/')

TERMS_EN = page(
    "Terms of Service",
    "Terms of service for Mahope Tools products and websites.",
    f"""
<h1>Terms of Service</h1>
<p class="muted">Last updated: August 26, 2026</p>

<h1 style="display:none">x</h1>
<h2>Software license</h2>
<p>The open-source tools published here are licensed under the terms stated in
each project's repository (see LICENSE in each repo). Paid products are licensed
per purchaser for use on any number of machines you own. Each purchase is a
one-time payment unless explicitly labeled otherwise; there are no recurring
charges.</p>

<h2>Acceptable use</h2>
<p>Only monitor, check or scan systems you own or have permission to test.
You are responsible for how you use the tools.</p>

<h2>No warranty</h2>
<p>The software and content are provided "as is", without warranty of any kind.
We do not guarantee that monitoring alerts will always be delivered or that
scan results are complete. Do not rely on these tools as your sole safety
measure for critical systems.</p>

<h2>Limitation of liability</h2>
<p>To the maximum extent permitted by law, we are not liable for indirect or
consequential damages arising from use of the software or website.</p>

<h2>Refunds</h2>
<p>If a paid product does not work for you, contact
<a href="mailto:{CONTACT}">{CONTACT}</a> within 14 days of purchase for a full
refund.</p>

<h2>Contact</h2>
<p><a href="mailto:{CONTACT}">{CONTACT}</a></p>
""")
TERMS_EN = TERMS_EN.replace('{CANON}', SITEURL + '/terms/')

for sub, html in (('privacy', PRIVACY_EN), ('terms', TERMS_EN)):
    d = os.path.join(SITE, sub)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(html)
    print('wrote', sub)
