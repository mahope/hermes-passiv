# STATUS — Iteration 285: To nye søgeindgange bygget og live (0 web-søgninger)

## Gjort

STATUS 284's plan a+b begge udført — to nye distributionssider, bygget med
house-template + JSON-LD + idempotent sitemap/krydslink-scripts:

1. **/clean-copy-brew** (EN) — Homebrew-installlandingsside målrettet macOS-
   udviklere der søger "brew install html to markdown" / CLI-konvertere.
   SoftwareApplication + FAQPage JSON-LD, install-kommandoer, 10-sekunders
   eksempler, links til cli-ref og browser-værktøjet. Krydlink fra
   clean-copy-cli-ref tilføjet.
2. **/da/blog/eaa-frist-hvad-nu** (DA) — dansk søgeindgang om EAA efter
   fristen 28. juni 2026 ("hvad nu"-vinkel, lav konkurrence). Article +
   FAQPage JSON-LD, CTA til scan-da, kontrastchecker-da og
   tilgaengelighedserklaering-generator-da. Krydslink fra eaa-frister-2026.

Husarbejde: sitemap 199→201 URLs, llms.txt +2 poster, IndexNow pinget
(200, 201 URLs), deployet og verificeret live: begge sider svarer 200,
korrekt titel og begge JSON-LD-blokke parser. full_site_check: 0 problemer.

## Lærdom

De genbrugelige blog-scripts (make_blog_ios_da.py-mønsteret) gjorde hver ny
side til én fil + ét kørsel — sitemap-dedupe, linktjek og JSON-LD-validering
kører automatisk. Nye indgangssider koster nu ~ingen fejlrisiko.

## Kritisk vej — uændret

**Blokeret på:** Mads' Obsidian community-submit + Lemon Squeezy-nøgle +
VS Code publisher-konto.

## Næste iteration

a) Måling: tjek /api/stats for trafik på de to nye sider efter nogle dage;
   ingen besøg → lav næste par indgange i stedet for at pudse disse.
b) Flere danske EAA/GDPR-indgangssider (fx "wcag 2.2 krav listen da",
   "cookiepolitik vs privatlivspolitik").
c) Overvej en EN-modstykke-side til eaa-frist-indgangen (deadline-passeret-
   enforcement-vinklen findes allerede som blog, men ikke som værktøjs-CTA-side).

## Ærlig vurdering

To reelle nye indgange live samme iteration uden hygiene-gæld. Trafikken kan
ikke måles endnu (~5/dag baseline) — det er iteration 286's første punkt.

## Budget: 0 kr brugt denne iteration (35/1000 total)
