#!/usr/bin/env python3
"""Iter 313: create EN + DA SEO blog posts for the Website Compliance Checker."""
import os, json

EN = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Free Website Compliance Checker: Scan Any Site for 9 EU Compliance Items</title>
<meta name="description" content="Free website compliance checker: scan any URL for privacy policy, cookie consent, accessibility statement, security headers and more. 9 checks, no signup, results in seconds.">
<link rel="canonical" href="https://hermes-passiv.pages.dev/blog/free-website-compliance-checker">
<link rel="alternate" hreflang="en" href="https://hermes-passiv.pages.dev/blog/free-website-compliance-checker">
<link rel="alternate" hreflang="da" href="https://hermes-passiv.pages.dev/da/blog/gratis-compliance-tjek-hjemmeside">
<link rel="sitemap" type="application/xml" title="Sitemap" href="/sitemap.xml">
<link rel="stylesheet" href="/style.css">
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "TechArticle",
  "headline": "Free Website Compliance Checker: Scan Any Site for 9 EU Compliance Items",
  "description": "Scan any website for privacy policy, cookie consent, accessibility statement, DPA, security headers, meta tags and more. Free, no signup.",
  "publisher": { "@type": "Organization", "name": "Mahope" }
}
</script>
<script defer src="/track.js"></script>
</head>
<body><header class="hero">
  <div class="container">
    <div class="badge">BLOG · FREE TOOL</div>
    <h1>Free Website Compliance Checker:<br>9 Checks on Any Site in Seconds</h1>
    <p class="subtitle">GDPR fines start with missing basics — a privacy policy nobody can find, no reject button on the cookie banner, no accessibility statement. Our free scanner checks all of them server-side, in one pass.</p>
  </div>
</header>
<main class="container" style="max-width:760px;margin:0 auto;padding:24px 16px">

<h2>What it scans for</h2>
<p>Enter any URL at the <a href="/compliance-site-check">Website Compliance Checker</a> and the tool fetches your site server-side and runs nine checks:</p>
<ul>
<li><strong>Privacy policy</strong> and <strong>Terms of Service</strong> pages exist and are linked</li>
<li><strong>Cookie consent banner</strong> detected on the homepage</li>
<li><strong>Imprint / legal notice</strong> (required in several EU jurisdictions)</li>
<li><strong>Accessibility statement</strong> (required under the European Accessibility Act)</li>
<li><strong>Data Processing Agreement</strong> page</li>
<li><strong>Security headers</strong>: CSP, HSTS, X-Frame-Options, X-Content-Type-Options, Referrer-Policy</li>
<li><strong>Meta tags</strong>: title, description, viewport, canonical, robots, Open Graph</li>
<li><strong>Hreflang / language declaration</strong></li>
</ul>

<h2>How the score works</h2>
<p>You get a 0–100 score with a letter grade and, for every failed check, a concrete fix. The scan takes 5–15 seconds because it actually fetches candidate pages (<code>/privacy</code>, <code>/privacy-policy</code>, <code>/en/privacy</code> and so on) instead of guessing.</p>

<h2>Automate it in CI/CD</h2>
<p>The same engine is available as a free GitHub Action: <a href="https://github.com/mahope/compliance-site-check">mahope/compliance-site-check@v2</a>. Add one step to your workflow and every deploy gets checked automatically:</p>
<pre style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:14px;overflow-x:auto"><code>- uses: mahope/compliance-site-check@v2
  with:
    url: https://example.com</code></pre>

<h2>Who this is for</h2>
<p>Small web agencies running pre-launch audits, site owners who received a compliance complaint, and developers who want a quick baseline before a client meeting. It does not replace legal advice or a full manual audit — it catches the missing basics that most non-compliant sites share.</p>

<div class="book-cta" style="border:1px solid #ddd;border-radius:8px;padding:16px 20px;margin:32px 0;">
  <h3>Try it now — free, no signup</h3>
  <p>Enter your URL and get a graded report with concrete fixes.</p>
  <a href="/compliance-site-check" class="btn-primary">Run a free compliance scan →</a>
</div>

<p><a href="/da/blog/gratis-compliance-tjek-hjemmeside" lang="da">Dansk version af denne artikel</a></p>
</main>
<footer class="site-footer"><div class="container">
  <p><a href="/">← Home</a> · <a href="/compliance-site-check">Compliance Checker</a> · <a href="/free-tools">More free tools</a> · <a href="/#blog">Blog</a></p>
  <p>Mahope © 2026</p>
</div></footer>
</body>
</html>
'''

DA = EN.replace('lang="en"', 'lang="da"', 1)
DA = DA.replace('Free Website Compliance Checker: Scan Any Site for 9 EU Compliance Items',
                'Gratis Compliance-tjek: Scan enhver hjemmeside for 9 EU-krav')
DA = DA.replace('Free website compliance checker: scan any URL for privacy policy, cookie consent, accessibility statement, security headers and more. 9 checks, no signup, results in seconds.',
                'Gratis compliance-tjek af din hjemmeside: privatlivspolitik, cookie-samtykke, tilgaengelighedserklaering, security headers m.m. 9 tjek, ingen tilmelding.')
DA = DA.replace('/blog/free-website-compliance-checker', '/da/blog/gratis-compliance-tjek-hjemmeside')
DA = DA.replace('/da/blog/gratis-compliance-tjek-hjemmeside" lang="da">Dansk version af denne artikel',
                '/blog/free-website-compliance-checker" lang="en">English version of this article')
# body translation
repl = [
 ('BLOG · FREE TOOL', 'BLOG · GRIT VARKTOJ'),
]
open('site/blog/free-website-compliance-checker.html', 'w').write(EN)

# DA version: translate main body properly
da = EN
for old, new in [
 ('<h1>Free Website Compliance Checker:<br>9 Checks on Any Site in Seconds</h1>',
  '<h1>Gratis compliance-tjek:<br>9 tjek paa enhver side pa sekunder</h1>'),
 ('<p class="subtitle">GDPR fines start with missing basics — a privacy policy nobody can find, no reject button on the cookie banner, no accessibility statement. Our free scanner checks all of them server-side, in one pass.</p>',
  '<p class="subtitle">GDPR-boeder starter med de manglende basale ting — en privatlivspolitik ingen kan finde, intet "Afvis"-kryds på cookie-banneret, ingen tilgaengelighedserklæring. Vores gratis scanner tjekker det hele server-side i én gennemkoersel.</p>'),
 ('<h2>What it scans for</h2>', '<h2>Hvad den scanner for</h2>'),
 ('<p>Enter any URL at the <a href="/compliance-site-check">Website Compliance Checker</a> and the tool fetches your site server-side and runs nine checks:</p>',
  '<p>Indtast en URL i <a href="/da/compliance-site-check">Compliance Checkeren</a> — vaerktoejet henter din side server-side og koerer ni tjek:</p>'),
 ('<li><strong>Privacy policy</strong> and <strong>Terms of Service</strong> pages exist and are linked</li>',
  '<li><strong>Privatlivspolitik</strong> og <strong>Handelsbetingelser</strong> findes og er linket</li>'),
 ('<li><strong>Cookie consent banner</strong> detected on the homepage</li>',
  '<li><strong>Cookie-samtykke-banner</strong> fundet på forsiden</li>'),
 ('<li><strong>Imprint / legal notice</strong> (required in several EU jurisdictions)</li>',
  '<li><strong>Impressum / juridiske oplysninger</strong> (kraevet i flere EU-lande)</li>'),
 ('<li><strong>Accessibility statement</strong> (required under the European Accessibility Act)</li>',
  '<li><strong>Tilgaengelighedserklaering</strong> (kraevet efter Tilgaengelighedsloven)</li>'),
 ('<li><strong>Data Processing Agreement</strong> page</li>', '<li><strong>Databehandleraftale</strong>-side</li>'),
 ("<li><strong>Security headers</strong>: CSP, HSTS, X-Frame-Options, X-Content-Type-Options, Referrer-Policy</li>",
  "<li><strong>Security headers</strong>: CSP, HSTS, X-Frame-Options, X-Content-Type-Options, Referrer-Policy</li>"),
 ('<li><strong>Meta tags</strong>: title, description, viewport, canonical, robots, Open Graph</li>',
  '<li><strong>Meta-tags</strong>: title, description, viewport, canonical, robots, Open Graph</li>'),
 ('<li><strong>Hreflang / language declaration</strong></li>', '<li><strong>Hreflang / sprogdeklaration</strong></li>'),
 ('<h2>How the score works</h2>', '<h2>Saadan virker scoren</h2>'),
 ("<p>You get a 0–100 score with a letter grade and, for every failed check, a concrete fix. The scan takes 5–15 seconds because it actually fetches candidate pages (<code>/privacy</code>, <code>/privacy-policy</code>, <code>/en/privacy</code> and so on) instead of guessing.</p>",
  "<p>Du faar en score fra 0–100 med karakter og et konkret fix ved hvert fejlet tjek. Scanningen tager 5–15 sekunder, fordi der faktisk hentes kandidatsider (<code>/privatliv</code>, <code>/privacy-policy</code>, <code>/en/privacy</code> osv.) i stedet for at gaette.</p>"),
 ('<h2>Automate it in CI/CD</h2>', '<h2>Automatoiser det i CI/CD</h2>'),
 ('<p>The same engine is available as a free GitHub Action: <a href="https://github.com/mahope/compliance-site-check">mahope/compliance-site-check@v2</a>. Add one step to your workflow and every deploy gets checked automatically:</p>',
  '<p>Samme motor findes som gratis GitHub Action: <a href="https://github.com/mahope/compliance-site-check">mahope/compliance-site-check@v2</a>. Tilfoej eet trin til dit workflow, og hver deploy bliver tjekket automatisk:</p>'),
 ('<h2>Who this is for</h2>', '<h2>Hvem det er til</h2>'),
 ('<p>Small web agencies running pre-launch audits, site owners who received a compliance complaint, and developers who want a quick baseline before a client meeting. It does not replace legal advice or a full manual audit — it catches the missing basics that most non-compliant sites share.</p>',
  '<p>Smaa webbureauer der laver pre-launch-tjek, ejere der har modtaget en klage, og udviklere der vil have et hurtigt grundlag foer et kundemoede. Det erstatter ikke juridisk raadgivning eller en fuld manuel gjennomgang — men det fanger de manglende basale ting, som de fleste ukompatible sider deler.</p>'),
 ('<h3>Try it now — free, no signup</h3>', '<h3>Proev det nu — gratis, ingen tilmelding</h3>'),
 ('<p>Enter your URL and get a graded report with concrete fixes.</p>', '<p>Indtast din URL og faa en karakter med konkrete fixes.</p>'),
 ('Run a free compliance scan →', 'Koer en gratis scanning →'),
 ('Dansk version af denne artikel', 'Dansk version'),  # replaced earlier anyway
]:
    da = da.replace(old, new)

os.makedirs('site/da/blog', exist_ok=True)
open('site/da/blog/gratis-compliance-tjek-hjemmeside.html', 'w').write(da)
print('written both posts')
