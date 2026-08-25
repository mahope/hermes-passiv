# STATUS — Iteration 286: EN-modstykke til EAA-frist-siden live (0 web-søgninger)

## Gjort

STATUS 285's punkt c udført: **/blog/eaa-deadline-passed** (EN) — engelsk
modstykke til den danske "fristen er passeret"-side. Targets
"eaa deadline passed" / "eaa enforcement what now"-vinklen, som kun fandtes som
blogpost men ikke som værktøjs-CTA-side på EN.

- Article + FAQPage JSON-LD (begge valideret: @context korrekt)
- Idempotent sitemap-add (201→202 URLs), krydslink fra eaa-enforcement-2026,
  llms.txt +1 post, IndexNow pinget (202)
- full_site_check: 0 problemer
- Deployet og live-verificeret: side svarer med korrekt titel, begge JSON-LD-
  blokke parser live, sitemap indeholder URL'en

Måling fra /api/stats (punkt a): siderne er for nye til at måle endnu; baseline
uændret (~1-6 besøg/dag, NIS2-e-bog mest downloadet). Genmåles iter 288.

## Kritisk vej — uændret

**Blokeret på:** Mads' Obsidian community-submit + Lemon Squeezy-nøgle +
VS Code publisher-konto.

## Næste iteration

a) Genmål trafik på de tre nyeste indgange (/clean-copy-brew,
   /da/blog/eaa-frist-hvad-nu, /blog/eaa-deadline-passed). Ingen besøg efter
   ~3 dage → stop med flere indgange i samme serie og prøv en anden vinkel.
b) Punkt b fra 285 er stadig åben: dansk WCAG 2.2-tjekliste-side
   ("wcag 2.2 krav liste da") — der findes wcag-22-aendringer.html men ingen
   tjekliste-form.
c) Overvej cookiepolitik-vs-privatlivspolitik (da) som fjerde indgang.

## Ærlig vurdering

Én ny indgang live, nul hygiene-gæld, 0 søgninger brugt. Men trafikken bevæger
sig ikke — hvis genmålingen i 287/288 stadig viser ~baseline, skal serien
stoppes til fordel for distribution uden for egen flade (som kræver Mads' ja)
eller et nyt produktspor.

## Budget: 0 kr brugt denne iteration (35/1000 total)
