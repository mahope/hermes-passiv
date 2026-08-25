# STATUS — Iteration 287: WCAG 2.2-kravliste (DA) live + måling fra 286 (0 web-søgninger)

## Måling først (punkt a fra 286)

/api/stats (14 dage): de tre nyeste indgange (/clean-copy-brew,
/da/blog/eaa-frist-hvad-nu, /blog/eaa-deadline-passed) har **0 besøg**.
Baseline uændret: kun forsiden + downloads (NIS2-e-bog stadig mest hentet).
Waitlist: 1 ægte. Licenses: 0.

Konsekvens ift. reglen i STATUS 286: indgangs-serien får én sidste chance med
punkt b (WCAG-tjeklisten nedenfor), som var planlagt inden målingen. Hvis
iteration 289's genmåling stadig viser ~0 på ALLE indgange fra serien,
stopper vi serien og skifter spor (distribution kræver Mads' ja → nyt produkt).

## Bygget

**/da/blog/wcag-22-krav-liste** — dansk komplet WCAG 2.2-tjekliste:
50 kriterier (23 A + 27 AA) i tabeller med kort "hvad det betyder i praksis"
pr. krav, nye-i-2.2-kriterier markeret grønt, 5 FAQ'er, CTA til /scan-da.

- Article + FAQPage JSON-LD (valideret lokalt og live)
- Idempotent sitemap-add (202→203 URLs), krydslink fra både
  da/blog/wcag-22-aendringer og blog/wcag-22-what-changes, llms.txt +1
- IndexNow pinget; sitemap verificeret live indeholder URL'en
- full_site_check: 203 urls, 0 problemer
- Deployet og live-verificeret (titel, JSON-LD, tabelrækker)

Faktaselvcheck undervejs: første udkast skrev "87 kriterier" i meta-description
men viste kun A/AA — rettet til "50 på niveau A og AA" inden deploy. Rækketælling
i scriptet (A=23, AA=27, heraf 6 nye på A/AA) matcher teksten på siden.

## Kritisk vej — uændret

**Blokeret på:** Mads' Obsidian community-submit + Lemon Squeezy-nøgle +
VS Code publisher-konto.

## Næste iteration (288/289)

a) Genmål ALLE seriens indgange. Hvis ~0: stop indgangs-byggeriet. Se
   "Ærlig vurdering".
b) Hvis der fortsat bygges indgange: cookiepolitik-vs-privatlivspolitik (da)
   var næste kandidat — men kun hvis (a) ikke allerede har stoppet serien.
c) Alternativ til serien hvis den dør: overvej nyt produktspor eller
   distribution-forberedelse (udsendelser/lister klarlagt, venter på Mads' ja).

## Ærlig vurdering

Siden er teknisk perfekt og trafikken kommer ikke. Fem indgange i serien har nu
tilsammen fået nul registrerede besøg. Det er et stærkt signal om at
søgeindgangs-strategien alene ikke virker for dette site — enten fordi
domænet har for lidt autoritet, eller fordi efterspørgslen på netop disse
queries er for lille. Næste iteration skal tage stilling til sporskifte, ikke
bygge indgang nr. seks af samme skabelon uden begrundelse.

## Budget: 0 kr brugt denne iteration (35/1000 total)
