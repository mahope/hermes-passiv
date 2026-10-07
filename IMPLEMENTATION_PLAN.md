# STATUS
- **Farvenavn i paletgeneratoren leveret 8/10** (`ceo/farvenavn`): hver
  paletrække viser nu nærmeste CSS-navn under hex'en (`crimson`, `slateblue`),
  og billed-prøverne viser navnet under farven. Navnene kommer fra én tabel i
  `site/color-names.js` (139 forskellige CSS-farver), delt af EN/DA og
  billedværktøjet. Gate **GRØN — 185 steps**. Baseline: **0** besøgende/28 dage
  på `/palette-generator` (Plausible 7/10).
- **Alle VERIFICÉR DEPLOY-noter fra 6–8/10 er live og lukket** (målt 8/10 mod
  mahope.tools og deskuptime.com — se `docs/plan-arkiv.md`).
- **CEO-kø #0 er færdig og merged** (url-inspect + `env`, 202 på tak-siden, 429
  endelig, AI-kvote, SSRF pr. hop). Verificeret i koden 8/10; intet åbent.
- **Sentry er sat op og testet** (worker 149-246, test 1748-1833): DSN i kode,
  kun produktion, ingen PII, ingen traces/replay.
- **Rød CI fra 7/10 rettet** (`d5baf6aa`), og planen er skåret til under 40 KB.

## Åbne review-fund

Ingen.

## Verificér deploy

- **VERIFICÉR DEPLOY:** farvenavn `ceo/farvenavn` 8/10 — tjek at live
  `/palette-generator` og `/palette-generator-da` indlæser `/color-names.js`, at
  hver paletrække bærer et `.pg-name` med et CSS-navn (fx `red`, `crimson`), og
  at en billed-prøve viser navnet i `.pg-img-name`.

## Åbne opgaver

3. **Konvertering kan ikke måles uden `STATS_TOKEN`.** Hvorfor: `/api/stats`
   svarer 401, så trafikrangeringer er vor egen links-tælling, ikke besøg.
   Accept: `GET /api/stats` med token svarer 200. *(Blockeret på Mads — se ❓.)*

4. **`bugbottle.dev` deployes ikke.** Hvorfor: `deploy-sites.yml`-matrixen
   deployer kun tre domæner. Accept: domænet på Pages og fjernet fra
   `UNMANAGED_DOMAINS`, eller fjernet fra `TRACKING_DOMAINS`. *(Beslutning — ❓.)*

6. **Bogen har ingen DA-udgave.** Hvorfor: de seks bøger er på engelsk, og der
   findes ingen `/da/books/*`-ruter, så bogsiders hreflang har intet dansk par.
   Accept: en DA-udgave af de to vigtigste som EPUB, eller en synlig dansk note.
   *(Beslutning — ❓.)*

8. **En sitemap-rute må ikke have en død eneste handling.** Hvorfor: porten
   dømmer kun de to ruter i `tools/unavailable_routes.json`. Accept: porten
   finder den, hvis den skrives i manifestet. *(Kun relevant ved nye sådanne
   sider — ikke en opgave i sig selv.)*

21. **En `ceo/*`-gren er ikke arbejde, fordi den ligger uden for `main`.** Hvorfor:
   alle fire målte 5/10 var dubletter. Accept: før en gren nævnes i planen skal
   `git cherry main <gren>` være læst, og dens rørte filer sammenlignet
   fil-for-fil med `main`.

## ❓ Til Mads

- **🔴 `OPENROUTER_API_KEY` mangler på workeren — assistenten er stadig slukket.**
  Når du sætter nøglen: fjern `noindex` fra `site/compliance-ai.html` +
  `site/da/compliance-ai.html`, og sæt `"available": true` i `tools/ai_cta.json`
  og kør `python3 tools/check_ai_cta_honesty.py --apply`.
- **🔴 `STATS_TOKEN` på workeren.** Én secret, og så kan konvertering måles i
  stedet for gættes. Uden den er `/api/stats` 401.
- **🔴 `bugbottle.dev` ligger på en server, vi ikke deployer.** Live svarer 404
  fra `nginx`. To veje: (a) på Cloudflare Pages → jeg tilføjer det til matrixen;
  (b) ikke vores at udgive → det ud af `TRACKING_DOMAINS`.
- **🔴 To betalte desktop-apps kan ikke aktiveres.** De shippede binære
  (`transmute` v0.2.1, `deskuptime` desktop-v0.2.7) har Lemon Squeezy indbygget,
  og kilderne ligger i private repos, hvor du selv laver releases.
- **🔴 Bogen er gratis, men Stripe har et betalt bundlet produkt.** Kontrakten
  lister `eu-compliance-ebook-bundle` til $29, mens syv sider siger «Free».
  Din beslutning, fordi det er dit navn på kvitteringen.
- **🟡 Skal scanner- og AI-banneren ligge over folden på de 172 sider?**
- **🟡 Skal det frie flerstedes-tjek få en kundeklar rapport?** Den flytter en
  $79-årslinje.
- **🟡 `indexnow_ping.sh` kaldes aldrig** — et ping er et udadvendt kald; sig til.
- **🟡 `/blog/` siger «96 Danish guides», men 11 ligger på cleancopy.tools.**
- **🟡 Skal værktøjssiderne vise livstidsprisen?** Portene siger nej til et
  prislink i pro-kortet.
- **Search Console:** tilføj de fem domæner som properties.
- **Plugin-version:** kunder på Clean Copy 1.1.0 henter ikke den rettede zip —
  kræver en release, som er din.

## Feature-kø

Prioriteret efter hvor tæt den er på penge. Baseline er målt på den **byggede**
side; tallene er ikke vores egen trafik. Alt det leverede (1–26) står i
`docs/plan-arkiv.md`.

27. **deskuptime.com: giv forsiden et værktøj i stedet for et pitch.** Hvem: de
    8 besøgende/28 dage, der alle forlader forsiden (bounce 100%). Tal: bounce på
    `/`. Accept: forsiden viser ét URL-felt der kører det gratis tjek uden login,
    så første handling er et svar, ikke et køb. Datagrund: Plausible 7/10.
28. **cleancopy.tools: «prøv med din egen tekst» over folden.** Hvem: de 16
    besøgende/28 dage på `/` (bounce 79%). Tal: bounce på `/`. Accept: forsidens
    første handling konverterer indsat tekst i browseren og viser markdown.
    Datagrund: Plausible 7/10.
29. **text-on-image-checker: del resultatet som et link.** Hvem: de 6 besøgende
    på `/text-on-image-checker` og 9 på den tilhørende artikel. Tal: besøgende på
    værktøjet. Accept: et del-link gendanner billede/tekst/placering, ligesom
    paletgeneratorens `#c=`-link. Datagrund: top-side i Plausible.
