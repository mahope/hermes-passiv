#!/usr/bin/env python3
"""make_compliance_ai_da.py — Danish version of the AI Compliance Assistant.

Builds site/da/compliance-ai.html from site/compliance-ai.html: translates
head + visible copy, keeps all JS/behaviour identical. The backend answers in
the user's language automatically, so no API change is needed.
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'site', 'compliance-ai.html')
DST = os.path.join(ROOT, 'site', 'da', 'compliance-ai.html')

REPLACEMENTS = [
    ('<html lang="en">', '<html lang="da">'),
    ('<title>Free AI Compliance Assistant — EAA, NIS2 &amp; GDPR Answers in Seconds</title>',
     '<title>Gratis AI compliance-assistent — EAA-, NIS2- &amp; GDPR-svar på sekunder</title>'),
    ('<meta name="description" content="Free AI-powered assistant for EU digital compliance questions. Ask about EAA/WCAG accessibility, NIS2 cybersecurity, GDPR data protection — get practical answers for small web agencies.">',
     '<meta name="description" content="Gratis AI-drevet assistent til spørgsmål om EU digital compliance. Spørg om EAA/WCAG-tilgængelighed, NIS2-cybersikkerhed eller GDPR — få praktiske svar til små webbureauer.">'),
    ('<meta property="og:title" content="AI Compliance Assistant — Free EU Digital Compliance Q&A">',
     '<meta property="og:title" content="AI compliance-assistent — gratis spørgsmål og svar om EU-compliance">'),
    ('<meta property="og:description" content="Free AI-powered assistant for EU digital compliance. Ask about EAA, NIS2, GDPR — get practical answers for small web agencies.">',
     '<meta property="og:description" content="Gratis AI-assistent om EU digital compliance. Spørg om EAA, NIS2, GDPR — få praktiske svar til små webbureauer.">'),
    ('<meta name="twitter:title" content="AI Compliance Assistant — Free EU Digital Compliance Q&A">',
     '<meta name="twitter:title" content="AI compliance-assistent — gratis spørgsmål og svar om EU-compliance">'),
    ('<meta name="twitter:description" content="Free AI-powered assistant for EU digital compliance. Ask about EAA, NIS2, GDPR.">',
     '<meta name="twitter:description" content="Gratis AI-assistent om EU digital compliance. Spørg om EAA, NIS2, GDPR.">'),
    ('<meta property="og:url" content="https://hermes-passiv.pages.dev/compliance-ai">',
     '<meta property="og:url" content="https://hermes-passiv.pages.dev/da/compliance-ai">'),
    ('<link rel="canonical" href="https://hermes-passiv.pages.dev/compliance-ai">',
     '<link rel="canonical" href="https://hermes-passiv.pages.dev/da/compliance-ai">'),
    ('<link rel="alternate" hreflang="x-default" href="https://hermes-passiv.pages.dev/compliance-ai">',
     '<link rel="alternate" hreflang="x-default" href="https://hermes-passiv.pages.dev/compliance-ai">\n<link rel="alternate" hreflang="en" href="https://hermes-passiv.pages.dev/compliance-ai">\n<link rel="alternate" hreflang="da" href="https://hermes-passiv.pages.dev/da/compliance-ai">'),
    ('"name": "EU Compliance AI Assistant",\n  "description": "Free AI-powered Q&A assistant for EU digital compliance — EAA/WCAG, NIS2, GDPR for small web agencies.",',
     '"name": "EU Compliance AI Assistent",\n  "description": "Gratis AI-assistent med spørgsmål og svar om EU digital compliance — EAA/WCAG, NIS2, GDPR for små webbureauer.",'),
    ('<h1>EU Compliance AI<br>Assistant</h1>', '<h1>EU Compliance<br>AI-assistent</h1>'),
    ('<p class="subtitle">Free AI-powered Q&A for small web agencies. Ask about EAA accessibility, NIS2 cybersecurity, GDPR data protection, or practical compliance steps — get concrete answers, not theory.</p>',
     '<p class="subtitle">Gratis AI-spørgsmål og -svar for små webbureauer. Spørg om EAA-tilgængelighed, NIS2-cybersikkerhed, GDPR eller praktiske compliance-trin — få konkrete svar, ikke teori.</p>'),
    ('<a href="scan" class="btn-secondary">Free EAA Scanner</a>',
     '<a href="/scan-da" class="btn-secondary">Gratis EAA-scanner</a>'),
    ('<a href="accessibility-statement-generator" class="btn-secondary">Statement Generator</a>',
     '<a href="/tilgaengelighedserklaering-generator-da" class="btn-secondary">Erklæringsgenerator</a>'),
    ('<a href="/" class="btn-secondary">Home</a>', '<a href="/da" class="btn-secondary">Forside</a>'),
    ('placeholder="Ask about EAA, NIS2, GDPR, or compliance..." aria-label="Your compliance question"',
     'placeholder="Spørg om EAA, NIS2, GDPR eller compliance..." aria-label="Dit compliance-spørgsmål"'),
    ('aria-label="Compliance chat conversation"', 'aria-label="Compliance-chat"'),
    ('aria-label="Send question">Ask</button>', 'aria-label="Send spørgsmål">Spørg</button>'),
    ("ask('What does EAA mean for my web agency?')\">What does EAA mean for my web agency?</span>",
     "ask('Hvad betyder EAA for mit webbureau?')\">Hvad betyder EAA for mit webbureau?</span>"),
    ("ask('Do I need a DPA for every client?')\">Do I need a DPA for every client?</span>",
     "ask('Skal jeg have en databehandleraftale med alle kunder?')\">Databehandleraftale med alle kunder?</span>"),
    ("ask('What are NIS2 incident reporting deadlines?')\">NIS2 incident reporting deadlines?</span>",
     "ask('Hvad er NIS2-fristerne for hændelsesrapportering?')\">NIS2-frister for hændelsesrapportering?</span>"),
    ("ask('How do I write an accessibility statement?')\">How to write an accessibility statement?</span>",
     "ask('Hvordan skriver jeg en tilgængelighedserklæring?')\">Sådan skriver du en tilgængelighedserklæring</span>"),
    ('<h2>What the AI Assistant Can Help With</h2>', '<h2>Hvad kan AI-assistenten hjælpe med</h2>'),
    ('<summary>What compliance topics does it cover?</summary>\n        <p>The assistant covers EAA (European Accessibility Act) / WCAG 2.2, NIS2 Directive cybersecurity requirements, GDPR data protection, and practical compliance implementation for small web agencies. It draws on the same knowledge base as our guides and e-books.</p>',
     '<summary>Hvilke emner dækker den?</summary>\n        <p>Assistenten dækker EAA (European Accessibility Act) / WCAG 2.2, NIS2-direktivets cybersikkerhedskrav, GDPR og praktisk compliance for små webbureauer. Den trækker på samme vidensbase som vores guider og e-bøger.</p>'),
    ('<summary>Is this legal advice?</summary>\n        <p><strong>No.</strong> The AI assistant provides general guidance based on published regulations. It is not a substitute for qualified legal counsel. Always consult a lawyer for specific compliance decisions affecting your agency.</p>',
     '<summary>Er det juridisk rådgivning?</summary>\n        <p><strong>Nej.</strong> AI-assistenten giver generel vejledning ud fra offentliggjorte regler. Det erstatter ikke kvalificeret juridisk rådgivning. Kontakt altid en advokat om specifikke compliance-beslutninger i dit bureau.</p>'),
    ('<summary>How accurate is the information?</summary>\n        <p>The assistant is powered by a large language model trained on publicly available information about EU regulations. While we configure it for accuracy, it can make mistakes. Verify critical information against official sources (EU Official Journal, national regulators).</p>',
     '<summary>Hvor præcise er svarene?</summary>\n        <p>Assistenten drives af en stor sprogmodel trænet på offentligt tilgængelig information om EU-regler. Den kan tage fejl. Verificér kritisk information mod officielle kilder (EU-Tidenden, nationale tilsynsmyndigheder).</p>'),
    ('<summary>Is my question stored or logged?</summary>\n        <p>Questions are sent to the AI provider (OpenRouter) for processing. We do not store questions or answers on our servers. No account or login is required. See our privacy practices in the footer.</p>',
     '<summary>Bliver mit spørgsmål gemt?</summary>\n        <p>Spørgsmål sendes til AI-leverandøren (OpenRouter) til behandling. Vi gemmer hverken spørgsmål eller svar på vores servere. Ingen konto eller login er nødvendig. Se privatlivspraksis i sidefoden.</p>'),
    ('<summary>What does the free EAA Scanner do?</summary>\n        <p>Our <a href="scan">free EAA Scanner</a> checks any public URL for 16 WCAG compliance rules — contrast, alt text, heading structure, form labels, and more. It runs entirely in your browser (client-side) with a privacy-preserving CORS proxy. No data is stored.</p>',
     '<summary>Hvad gør den gratis EAA-scanner?</summary>\n        <p>Vores <a href="/scan-da">gratis EAA-scanner</a> tjekker enhver offentlig URL mod 16 WCAG-regler — kontrast, alt-tekst, overskriftsstruktur, formularlabels m.m. Den kører helt i din browser med et privatlivsvennligt proxy-kald. Ingen data gemmes.</p>'),
    ("content: 'Ask a compliance question below to get started.';",
     "content: 'Stil et compliance-spørgsmål nedenfor for at komme i gang.';"),
    ("statusEl.textContent = data.error || 'Something went wrong. Please try again.';",
     "statusEl.textContent = data.error || 'Noget gik galt. Prøv venligst igen.';"),
    ("statusEl.textContent = 'Network error. Please check your connection and try again.';",
     "statusEl.textContent = 'Netværksfejl. Tjek din forbindelse og prøv igen.';"),
    ("text.toLowerCase().includes('not legal advice') || text.toLowerCase().includes('disclaimer');",
     "text.toLowerCase().includes('not legal advice') || text.toLowerCase().includes('disclaimer') || text.toLowerCase().includes('ikke juridisk');"),
    ("<p class=\"disclaimer\">This is general guidance, not legal advice. Consult a qualified lawyer for your specific situation.</p>",
     "<p class=\"disclaimer\">Dette er generel vejledning, ikke juridisk rådgivning. Kontakt en kvalificeret advokat om din konkrete situation.</p>"),
    ('<p>&copy; 2026 Mahope · Part of the <a href="/">Hermes Passiv</a> project</p>',
     '<p>&copy; 2026 Mahope · En del af <a href="/da">Hermes Passiv</a>-projektet</p>'),
    ('<p class="footer-small">Built for small web agencies. No legal advice — consult counsel for specific matters.</p>',
     '<p class="footer-small">Bygget til små webbureauer. Ikke juridisk rådgivning — kontakt en advokat om konkrete forhold.</p>'),
]

# The DA blog CTA pages already link here with this label; keep consistent.
CTA_LINK_NOTE = ''


def main():
    with open(SRC, encoding='utf-8') as f:
        html = f.read()
    misses = []
    for old, new in REPLACEMENTS:
        if old not in html:
            misses.append(old[:60])
        html = html.replace(old, new)
    # fix relative stylesheet path (page lives in /da/)
    html = html.replace('<link rel="stylesheet" href="style.css">',
                        '<link rel="stylesheet" href="/style.css">')
    html = html.replace('<script defer src="/track.js"></script>',
                        '<script defer src="/track.js"></script>')
    os.makedirs(os.path.dirname(DST), exist_ok=True)
    with open(DST, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f'Wrote {DST}')
    if misses:
        print('MISSED replacements:')
        for m in misses:
            print('  -', m)


if __name__ == '__main__':
    main()
