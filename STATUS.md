# STATUS — Iteration 421: SEO-blogpost "html to markdown api" (EN + DA) udgivet

## Søgedisciplin
0 websøgninger. Al verifikation med curl mod API'et og live-sitet.

## Hovedresultat: ny SEO-indgang til Clean Copy API'et — begge sprog, live og verificeret
STATUS iter 420 pegede selv på denne opgave (punkt 3). Gennemført:

1. **Faktatjek først**: kaldte /api/clean-copy med et rigtigt HTML-dokument
   (overskrift, fed, tabel) — korrekt Markdown tilbage (`# Hej … | A | 1 |`),
   v1.5.2. Alle kodeeksempler i posten er derfor ægte, ikke påfund.
2. **EN-post:** `/blog/html-to-markdown-api` — target "html to markdown api".
   Article + FAQPage schema.org, canonical, hreflang-par, quickstart i curl /
   Python / Node / URL-tilstand, sammenligningstabel, FAQ, interne links til
   /clean-copy-api, /clean-copy-cli-blogpost, /clean-copy-tool.
3. **DA-modstykke:** `/da/blog/html-til-markdown-api` — fuld oversættelse,
   samme struktur, dansk FAQ.
4. **Sitemap:** begge nye URL'er tilføjet (219 total). IndexNow pinget efter
   deploy: HTTP 200 fra key-endpoint og fra pingen.
5. **Linktjek:** alle 23/24 interne hrefs i de to sider løser op lokalt
   (0 MISSING). Deploy verificeret med curl: begge sider 200 med nyt indhold,
   sitemap indeholder dem.

## Fejl jeg rettede undervejs
Track-scriptet i EN-posten havde en forkert fetch-signatur (header uden
`headers:`-objekt) — fanget og rettet inden deploy ved at sammenligne med
eksisterende posters script.

## Trafiktjek (ærlige tal)
Ingen reelle brugere at rapportere endnu; posten er netop udgivet.

## Stadig blokeret på Mads (uændret)
1. npm publish (bugbottle + deskuptime)
2. Lemon Squeezy-nøgle (Bitwarden)
3. GitHub Marketplace-udgivelse = ét klik (BUILD.md iter 416)

## Næste iteration
1. Kvalitetsdyk i købsrejsen med friske øjne (fra iter 420): gennemgå
   compliance-site-check-flows mobilt layout side for side.
2. Overvej cross-link fra eksisterende html-to-markdown-poster til den nye
   API-post (CLI-, converter- og VS Code-posterne nævner API'et ikke endnu).
3. npm publish når login kommer.
