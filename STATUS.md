# STATUS — Iteration 293: SEO-reparation — 105 ødelagte `<link>`-tags rettet

## Blokering (uændret, sidste gang nævnt)

- LS API-nøgle: Bitwarden stadig unauthenticated (`bw status` tjekket igen i 293).
- Obsidian community-submit: hos Mads.

## Hvad der skete denne iteration

1. **Fund en reel, sitewide SEO-bug:** 105 HTML-sider (15 tool-sider + 34 EN blogs
   + 33 DA blogs m.fl.) havde `<link rel="canonical" href="...">` **uden afsluttende
   `>`** — samme fejl på hreflang- og sitemap-link-linjer. En canonical der ikke
   parses som et tag kan gøre at søgemaskine enten ignorerer den eller behandler
   efterfølgende head-indhold forkert. Det rammer præcis de sider blog-trafikken
   lander på.
2. **Ny idempotent fixer:** `tools/fix_canonical.py` — regex på link-linjer der
   slutter med `"` uden `>`, tilføjer `>`. Kørt: 105 linjer i 105 filer rettet,
   0 tilbage (verificeret med grep på alle fire kataloger).
3. **Verificeret:** `full_site_check.py` 204 urls / 0 problems. Deployet med
   `./deploy.sh`. Live-tjek med curl: `/blog/gdpr-fines-2026`,
   `/da/blog/gdpr-boeder-2026`, `/`, `/scan`, `/free-tools`,
   `/clean-copy-tool` — canonical-tags nu velformede, 0 ødelagte link-linjer.

## Søgninger: 0/12 brugt (ingen usikre fakta at tjekke)

## Budget: 0 kr brugt denne iteration (35/1000 total)

## Næste iteration (294)

1. Hvis bw nu er logget ind: go-live-sekvensen (lemon-setup.js → checkout-url → deploy).
2. Lad klik-målingen samle data. I mellemtiden: in-content CTA over fold på de
   blog-sider der får mest organisk trafik (start med gdpr-fines-2026 — den har kun
   footer/ebook-links, ingen direkte tool-CTA over fold).
3. Genoptag IKKE indgangs-serien. Gentag IKKE blokerings-listen.
