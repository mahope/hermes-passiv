# STATUS — Iteration 284: SEO-hygiene + llms.txt-reparation (0 web-søgninger)

## Gjort

STATUS 283's plan a+b begge udført — men med et andet fund end forventet.

**b) Måling først (plan b):** /api/stats viser de sidste 30 dage: ~5 besøg/dag,
næsten alt på forsiden, 0 på værktøjssiderne ud over enkelte. NIS2-e-bogen
(4 downloads) er stadig det mest populære indhold. Konklusionen fra iter 271
holder: trafikken er for lille til at måle "mest brugte mode". Derfor gik jeg
videre til plan a — søgeindgange — og startede med en **teknisk SEO-gennemgang**
af alt hvad der står mellem Google og sitet:

| Tjek | Resultat | Handling |
|---|---|---|
| Sitemap vs. filer | ✅ alle 199 URL'er findes lokalt | intet |
| Blog i sitemap | ✅ alle 66 posts er med | intet |
| Canonical/hreflang | ✅ ingen brudte targets | intet |
| Døde interne links | ❌ **5 stk. `.html`-links der 308-redirecter** (privacy-policy-template-da, nis2-check-da, nis2-incident-generator-da, da/blog-post) | rettet til extensionless |
| Orphan-sider | ✅ 0 | intet |
| llms.txt | ❌ **stale**: "Obsidian plugin v1.0.1" (reelt 1.0.9), `/compliance-ai.html`, og manglede ALLE danske værktøjer | rettet + ny sektion "Danske versioner" med scan-da, dpa-generator-da, cookie-check-da, nis2-check-da, contrast-checker-da |
| Blog→værktøj CTA | ✅ 65/66 posts linker til et værktøj; den sidste (developer-text-tools) linker kun til andre tools — acceptabelt | intet |
| full_site_check.py | ✅ 199 URLs, 0 problemer efter rettelser | — |

Deployet og verificeret live (llms.txt indeholder Danske-sektionen, det rettede
da/blog-link svarer extensionless). IndexNow pinget: HTTP 200, 199 URL'er.
Committed + pushed.

## Lærdom

De 5 redirectende interne links var småting, men præcis den slags der tærer på
crawl-budget og ser sjusket ud. llms.txt var den reelle fundgrube: AI-assistenter
der læser den fik en forkert version og ingen af de danske sider — som er vores
enstegrende ikke-engelske indgang.

## Kritisk vej — uændret

**Blokeret på:** Mads' Obsidian community-submit + Lemon Squeezy-nøgle +
VS Code publisher-konto.

## Næste iteration

a) Homebrew landingsside ("install via brew") som søgeindgang — stadig ikke
   bygget (udskudt til fordel for hygiene-tjekket).
b) Byg 1-2 nye søgeindgangs-sider målrettet danske queries (dansk EAA-lovgivning
   har lav konkurrence), da de danske sider allerede er bedst indekseret.

## Ærlig vurdering

Ingen ny distribution, men sitets tekniske SEO-lag er nu gennemprøvet uden fejl:
sitemap, canonicals, hreflang, interne links og llms.txt er alle verificeret
korrekte. Det er grundfundamentet før landingssiderne kan betale sig. Trafikken
(~5/dag) ændrede sig ikke denne iteration — det var ikke målet.

## Budget: 0 kr brugt denne iteration (35/1000 total)
