# STATUS
- **STATUS: KOE-TOM 8/10.** 0 åbne opgaver (de 6 står blokeret på Mads, se ❓),
  0 åbne PR'er. Seneste CI på `main` var RØD: STATUS havde 41 linjer mod 25
  tilladt; trimmet i denne commit. Historikken er flyttet til `docs/plan-arkiv.md`.
- **Feature 32 leveret 8/10:** `/compliance-report`s hero har nu ét `btn-primary`
  til `#pricingSection`, hvor den ene købsknap og pro-tabellen står; siden er
  ratchet i `tools/first_action.json`. Gate grøn.
- **BugBottle live 8/10:** `https://bugbottle.dev/` svarer 200 med korrekt indhold;
  `/blog/` og `/bugbottle-demo` er bevidst 404 (guiderne ligger på mahope.tools).
- **Review-fund 8/10:** 0 åbne. DeskUptime-licenssandheden er rettet (`7e101213`)
  og verificeret live.
- **Sentry:** sat op (worker 149-246), kun produktion, 0 uløste fejl de seneste
  14 dage.
- **PR-TJEK 8/10:** 0 åbne PR'er. **BRANCH-TJEK:** ikke kørt denne iteration.
- **CEO-kø #0** (url-inspect + `env`, 202 på tak-siden, 429 endelig, AI-kvote,
  SSRF pr. hop) er færdig og merged; 0 åbent.

## Åbne review-fund

Ingen.

## Verificér deploy

- **VERIFICÉR DEPLOY OK 8/10:** url-inspector-folden `ceo/url-inspector-fold-pro-link` —
  live `https://mahope.tools/url-inspector/` viser URL-feltet og «Inspect» i heroen
  (200), og `id="ui-pro-heading"` findes to steder i markup.
- **VERIFICÉR DEPLOY OK 8/10:** DeskUptime-tjekket i heroen `ae08878a` — live
  `deskuptime.com` og `deskuptime.com/da/` viser URL-feltet i heroen, tjek virker.
- **VERIFICÉR DEPLOY OK 8/10:** Clean Copy-konverteren i heroen `2085f465` — live
  `cleancopy.tools` og `cleancopy.tools/da/` viser konverteringsformularen i
  heroen, konvertering virker.
- **VERIFICÉR DEPLOY OK 8/10:** text-on-image-checker del-link `2613639a` — live
  `https://mahope.tools/text-on-image-checker` og `-da` svarer 200 og viser
  «Share this check»-knappen i resultatet (delt-linket gendanner tilstanden).
- **VERIFICÉR DEPLOY:** gate-rettelsen `ceo/first-action-form-hero` — påvirker
  intet i markup, så intet at se live; CI skal være grøn på `main`.
- **VERIFICÉR DEPLOY:** free-tools-katalog `ceo/free-tools-hero-catalog` — tjek
  at `https://mahope.tools/free-tools` og `https://mahope.tools/da/free-tools`
  viser katalogen med 7 kategorier i folden, og at «Alle værktøjer» ruller til den.
- **VERIFICÉR DEPLOY OK 8/10:** free-tools-katalog `ceo/free-tools-hero-catalog` —
  live `https://mahope.tools/free-tools` og `/da/free-tools` viser kataloget med
  7 kategorier i folden (EN: `#catalog-heading` "Tools by category", DA:
  "Værktøjer efter kategori"), og «Alle værktøjer» / «All tools» ruller til den.
  Gate grøn.
- **VERIFICÉR DEPLOY:** compliance-report-folden `ceo/compliance-hero-buy` — tjek
  at `https://mahope.tools/compliance-report` viser «See pricing — EUComply Pro» i
  heroen, at den ruller til `#pricingSection`, og at den ene «Buy EUComply Pro —
  $79/year»-knap står i priskortet.

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
- **🔴 `bugbottle.dev` deployes ikke.** Målt 8/10: `https://bugbottle.dev/` svarer
  **200** med korrekt indhold (title, canonical, hreflang, Plausible) — det er
  allerede live, men `deploy-sites.yml`-matrixen deployer kun tre domæner, så
  enhver rettelse til `bugbottle-landing/` ikke bliver udgivet. To veje: (a) tilføj
  det til matrixen; (b) det er ikke vores at udgive → fjern det fra
  `TRACKING_DOMAINS` i `build_sites.py`. `bugbottle.dev/blog/` og `/bugbottle-demo`
  svarer stadig 404 — det er bevidst: guiderne ligger på mahope-tools, se opgave 4.
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
    så første handling er et svar, ikke et køb. Datagrund: Plausible 7/10. **LEVERET** `ae08878a` — verificeret live 8/10.

29. **text-on-image-checker: del resultatet som et link.** Hvem: de 6 besøgende
    på `/text-on-image-checker` og 9 på den tilhørende artikel. Tal: besøgende på
    værktøjet. Accept: et del-link gendanner billede/tekst/placering, ligesom
    paletgeneratorens `#c=`-link. Datagrund: top-side i Plausible. **LEVERET** — ny `text-on-image-share.js` modul, integreret på EN/DA, tester grønne.

30. **`/url-inspector/`: folden har ingen handling og ingen vej til Pro-kortet.**
    Hvem: de læsere der kommer fra deskuptime-forsiden, hvis tjek-formular
    sender dem videre til URL-værktøjet. Tal: konvertering til DeskUptime Pro
    ($19). Accept: folden har én primær handling (tjekket) og ét link til den
    synlige pro-tabels sektion, så `check_first_action.py --list` viser siden
    grøn. Datagrund: portens egen `pristabel()` målt 8/10 — tabellen er synlig,
    men dens sektion har intet id, og folden har nul `btn-primary`.
    **LEVERET** `ceo/url-inspector-fold-pro-link` — tjek-formularen står nu i
    heroen, Pro-tabellens overskrift har `id="ui-pro-heading"`, siden er ratchet.

31. **`/free-tools`: hubben sender alle læsere til ét værktøj.** Hvem: de 7
    besøgende på `/` plus læsere af «Site»-kolonnen i footeren på alle 270
    byggede sider. Tal: brug af et gratis værktøj — den vej, Pro sælges på.
    Accept: foldens primære er en værktøjsrække med synlige kategorier
    (e-mail, kontrast, GDPR, tabel, skærmbillede), ikke ét anker, og `/`
    peger på samme rute. Datagrund: portens egen `handlinger()` målt 8/10 —
    foldens eneste primære er `#gdpr-heading`.
    **LEVERET** `69ec807e` — heroen matcher forsiden (tre knapper), katalog
    med 7 kategorier vises i folden, ratchet opdateret til `#catalog-heading`.

32. **`/compliance-report`: giv den en `$79`-knap i heroen.** Hvem: de besøgende der
    kommer til den eneste side med EUComply Pro-årsabonnementet (1 checkout-klik
    i uge 41, den eneste af alle fire domæner). Tal: `reports/weekly/2026-41.json`,
    `checkout.pages` — kun `/compliance-report` har et købstal. Accept: heroen har
    én primær `btn-primary`-knap der linker til
    `https://buy.stripe.com/eVq00i4YH6UG69g0ObbMQ03`, og `check_first_action.py`
    viser siden grøn. Datagrund: portens egen `handlinger()` målt 8/10 — foldens
    eneste primære handling er en `btn` (ikke `btn-primary`), og Pro-kortet står
    under folden. **LEVERET** `ceo/compliance-hero-buy` — heroen har ét anker
    «See pricing — EUComply Pro» til `#pricingSection`, hvor den ene dokumenterede
    købsknap står; intet nyt Stripe-produkt er oprettet. Siden er ratchet, så
    `check_first_action.py --list` viser den grøn. Købslinket kunne ikke flyttes
    op i heroen: `check_stripe_ctas` tillader præcis én synlig CTA pr. tilbud, og
    `check_tool_paid_path` måler kun brødteksten.
