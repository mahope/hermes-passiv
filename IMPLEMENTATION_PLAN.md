# IMPLEMENTATION_PLAN

## Status

- `ITERATION_ID`: `hub-readme-2026-09-26`
- `STATE`: `Opgave 23 FÆRDIG — køen var tom (1-22 FÆRDIG, og den næste opgave kræver Mads' private filer), så dette er den researchiteration kontrakten forlanger. Fundet var ikke i koden, men i repoets **egentlige indgangsside**: rod-README.md for `mahope/hermes-passiv` — hubrepoet der bygger fire sites og otte produkter — var en kopi af *Clean Copy for Obsidian*s README. Den løb altså ud som ét produkts README, havde en changelog på 1.0.1 mens den publicerede udgave er 1.0.10, og ingen donation. Den er nu en hub-README med en kort fejlsikret kortlægning. **Tre ting blev fanget, før commit, som alle viser hvorfor mit første udkast ikke måtte lande:** (a) jeg skrev `mahope.tools/eucomply` og `deskuptime.com/transmute`, og *ingen af dem findes* — de står ikke i noget sitemap, og Transmute har slet ingen offentlig side; (b) jeg skrev "the free tools do not phone home", som er præcis den påstand opgave 2 var nødt til at trække tilbage, fordi licenstjekket er online; (c) jeg skrev at Clean Copy Pro virker "everywhere", uden at nogen klient er tjekket for det. Alt er nu verificeret mod de *live* sitemaps. To negative kontroller fra denne klasse findes allerede i gaten og fangede ingenting her, fordi ingen af dem læser rod-README — det er præcis hullet.`
- `STATE` (før, opgave 22): `Opgave 22 FÆRDIG — researchiterationen fandt missionens første prioritet ulukket i sitet: syv downloadprodukter har \`kv_verified: false\`, så ingen af deres 30 leveringsfiler findes i KV, og \`/api/download\` svarer 503. To af dem blev alligevel solgt fra fire sider. Siterne tog imod pengene og lovede en fil de ikke kunne levere. Nu sælges intet downloadprodukt før flaget står på true, og en ny check i \`check_stripe_ctas.py\` gater begge retninger — så den heller ikke kan komme tilbage ved en fejl. Fund: kun 2 af 7 produkter havde overhovedet en købsknap, så hullet var mindre end rapporten antydede; men 190 kildefiler hævdede stadig \`$29\` for den afskaffede PDF-bundle fra én generator, hvoraf 49 EN-sider var publiceret (bygget stripper DA-blokkene); JSON-LD på books-siden erklærede \`InStock\` for et produkt der ikke kan leveres; og selftestens domænescenarie pegede på \`site/scan.html\`, som forlod inventaret — en stum kontrol, der ville have set grøn ud. Licensprodukterne er derimod OK: EUComply Pro aktiverer online og låser PDF'en.`
- `STATE` (før): `Opgave 21 FÆRDIG — opgavens forudsætning var forkert: de fire Clean Copy-arkiver har haft en indholdsgate siden opgave 7 del 2 (gatestep 11 beviser byte-identisk regeneration, kilde-identiske medlemmer, version.txt og ingen død vært), og --check var grøn for alle tre. Det rigtige hul lå i check_versions.py, som læste filnavnets version for de tre Clean Copy-zip OG desktop-kildearkivet, men ikke deres egen version indeni — og alle fire bærer den. Beviset for at hullet var ældre end opgaven troede, lå i selve fixtureen: de fire arkiver bar "manifest.json": "{}". Nu erklærer alle fire produkter inner=(...), 25 → 31 mutationer, 1 → 2 negative kontroller. Fund: den nye check diagnosticerer hvad byte-sammenligning kun kan sige "afviger fra"; fixtureen måtte ikke blive stående; den anden negativ kontrol er den der beskytter de fire nye linjer mod at gøre publicerede arkiver røde.`
- `STATE` (før): `Opgave 20 FÆRDIG — site/downloads/site-icons/site-icons-1.0.0.tar.gz viste sig at være en håndlavet kopi fra 24/8, ikke bygget af site-icons/. Den publicerede README sagde at nøgler sælges i en Lemon Squeezy-konto, lukket 24/9, og site_icons.py's docstring pegede på den samme lukkede API. Arkivet er nu bygget af kilden og byte-identisk, verificeret med både tarfile og systemets tar. Nyt værktøj tools/build_site_icons_archive.py (build/--check/--self-test) + to gatestræk (38 fra 36), og site-icons/** er i path-filteret så hullet fra opgave 18 er lukket her. Fire fund: de tre publicerede artefakter var TRE håndlavede kopier; kilden havde selv den døde vært; path-filteret viste at site/downloads/site-icons/** er overflødigt; og check_license_clients fangede min egen docstring som licensklient.`
- `STATE` (før, opgave 19): `Opgave 19 FÆRDIG — check_versions.py læser nu de fem byggeoutput-arkivers indre versionserklæring (hjul-METADATA, sdist-PKG-INFO, npm-tgz package/package.json, site-icons' site_icons.py). 25 mutationer + negativ kontrol + positiv kontrol. Fire fund skrevet op, bl.a. at planens egen forudsætning om site-icons var forkert (den har en indre version) og at fnmatchs * ville talt setuptools' egg-info/PKG-INFO med. check_python_env erklærede C-udvidelser (zlib) for tredjepart; rettet + egen kontrol.`
- `ACTIVE_TASK`: `— (ingen opgave I GANG)`
- `NEXT_TASK`: `24 — ❓ Til Mads punkt 9 (kræver ham): upload de 30 filer til KV og sæt kv_verified. 25, 26, 27 er nye fund fra opgave 23.`
- `PLAN_COMMIT`: `(denne iteration)`
- `BASELINE`: `main@b55abed`
- `LAST_BRANCH`: `ceo/hub-readme`
- `TASK_ATTEMPTS`: `18: 1/1., 19: 1/1., 20: 1/1., 21: 1/1., 22: 1/1., 23: 1/1.`
- `DEPLOY` (opgave 22, lukket): `DEPLOY OK aae4a72 26/9` — kørsel `36204568679`: `gate` grøn (38 steps) + tre grønne deploys (mahope.tools, cleancopy.tools, deskuptime.com). Live-indhold verificeret, ikke HTTP 200: `build-info.json` bærer merge-SHA'en; `/books/compliance-bundle` har **0** fund af `InStock`, af de to betalingslinks og af `$29`, og viser den nye tekst (*"All six e-books are free"*, *"We do not sell a combined PDF of these guides"*); `/compliance-report` har 0 fund af Report Kit og 1 af EUComply Pro-linket, så licenssalget er urørt; `/scan` og `/scan-da` har 0 fund af begge links; `/blog/nis2-gap-assessment-guide` viser den nye korsel-linje.
- `DEPLOY` (opgave 23): `INGEN DEPLOY FORVENTET 37d8a04 26/9` — committen rørte kun `README.md` og planen, som begge ligger uden for workflowens path-filter. GitHub Actions kørte **ikke** (nyeste kørsel er stadig `36204568679` fra opgave 22), hvilket er korrekt og ikke en fejl. Live `build-info.json` bærer derfor stadig `aae4a72` på alle tre domæner, og det er korrekt: intet i `site/` eller `dist/` er ændret. Den nye README ligger i GitHub, ikke i dist, så den kan heller ikke verificeres på et domæne — den er verificeret mod de tre **live sitemaps**.
- `GATE` (opgave 23): `GRØN — python3 tools/quality_gate.py: GRØN, 38 steps (uændret). Bevis på rigtighed: de 12 URL'er i den nye rod-README er verificeret mod de tre live sitemaps (mahope.tools, cleancopy.tools, deskuptime.com) og tools/stripe_catalog.json, ikke mod en antagelse. To af dem (mahope.tools/eucomply, deskuptime.com/transmute) fandtes ikke og var fanget i mit første udkast. Stripe-worker uændret, dist/uændret (gitignored).`
- `GATE` (opgave 22): `GRØN — python3 tools/quality_gate.py: GRØN, 38 steps (uændret). check_stripe_ctas: 0 problems, 13 produkter, 11 dokumenterede købssider (fra 15). check_stripe_ctas --self-test: 12/12 fejlformer (fra 10) + positiv kontrol grøn + ny guard mod stumme scenarier. Bevis på de rigtige filer: porten fandt 4 sider med et betalingslink til et produkt uden filer, FØR nogen blev rettet. test_weekly_report: 28 tests grønne. Stripe-worker uændret, dist/uændret (gitignored).`
- `GATE` (opgave 21): `GRØN — python3 tools/quality_gate.py: GRØN, 38 steps (uændret). check_versions --self-test: OK (31 mutationer fra 25, 2 negative kontroller fra 1, positiv kontrol grøn, rigtige filer grønne). Bevis på de rigtige filer: Obsidian-arkivet muteret til manifest 1.0.9 under 1.0.10-navn → check_versions melder "kunden henter gammel kode under et nyt filnavn", distribution-gaten melder blot "afviger fra en regeneration". Stripe-worker uændret, dist/uændret (gitignored).`
- `DEPLOY` (opgave 21, lukket): `DEPLOY OK 077a67b 26/9` — kørsel `36202790956` (den kørsel udløses af selve kode-committen `f58386d`): `gate` grøn (38 steps, `check_versions --self-test` 31 mutationer + 2 negative kontroller) + tre grønne deploys (cleancopy.tools, deskuptime.com, mahope.tools). Kode-committen rørte kun `tools/check_versions.py`, så domænerne er uændrede — bekræftet på indhold: `site-icons-1.0.0.tar.gz` er byte-uændret (sha256 `cbafbd98…`) og `clean-copy-obsidian-v1.0.10.zip` (12879 bytes) er byte-identisk med repoet. De tre efterfølgende merges (plan + `AGENTS.md`) ligger **uden for workflowens path-filter**, så de deployer ikke med vilje — intet i `site/` er rørt siden `36202790956`.`
- `VERIFICÉR DEPLOY` (lukket): `site-icons-arkivet er bygget af kilden 4bcfb9e 26/9` — kørsel `36202426086` grøn. Live-indhold verificeret: `https://mahope.tools/downloads/site-icons/site-icons-1.0.0.tar.gz` (5601 bytes) pakker ud til præcis to filer, `README.md` 2581 bytes og `site_icons.py` 15287 bytes, mtime 2000-01-01, og **nul** af dem nævner `lemon`. Løse kopier `/downloads/site-icons/README.md` og `/downloads/site-icons/site_icons.py` er begge byte-identiske med `site-icons/` i repoet. Tarballets sha256 `cbafbd98e35a3fc67addf820de74108fcac22a2f2e205a4c7e4b68c2242cf88e`.
- `GATE` (før, opgave 20): `GRØN — python3 tools/quality_gate.py: GRØN, 38 steps (fra 36). build_site_icons_archive --self-test: OK (8 mutationer + positiv kontrol + determinisme + 2 falsk-positive-tests). --check: grøn, 2 filer i tarballet + 2 løse filer = regeneration af site-icons/. Porten fandt 5 fejl på det gamle arkiv FØR rettelsen, heraf de to med den lukkede udbyder. test_deploy_workflow: grøn, og fejler hvis site-icons/** tages ud af filteret. Stripe-worker uændret, dist/uændret (gitignored).`
- `GATE` (før, opgave 19): `GRØN — python3 tools/quality_gate.py: GRØN, 36 steps (uændret). check_versions --self-test: OK (25 mutationer + 1 negativ kontrol + positiv kontrol + rigtige filer). check_versions: OK, 8 produkter. check_python_env --self-test: OK (13 mutationer + 7 stdlib-kontroller). Stripe-worker uændret, dist/uændret (gitignored).`
- `VERIFICÉR DEPLOY` (lukket): `check_versions læser nu de fem byggeoutput-arkivers indre version 956f19f 2026-09-26` — kørsel `36201588862` grøn. Verificér **indhold**: de fire filer kunden henter skal være byte-uændrede, fordi committen ikke rørte dem.
- `DEPLOY` (ny): `DEPLOY OK 956f19f 26/9` — kørsel `36201588862`: `gate` grøn (36 steps) + tre grønne deploys (cleancopy.tools, deskuptime.com, mahope.tools). Intet i `site/` eller `dist/` blev rørt af committen, så domænerne er uændrede. Live-indhold verificeret på de tre publicerede byggeoutput-arkiver: `eaa_scanner-1.2.0-py3-none-any.whl`, `mahope-eaa-scanner-1.2.0.tgz` og `site-icons/site-icons-1.0.0.tar.gz` er hvert især **byte-identiske** med repoet (sha256 `0fc4b3ba…`, `d9e74ffb…`, `882ab49d…`). Se Deployloggen.
- `GATE` (opgave 19): `GRØN — python3 tools/quality_gate.py: GRØN, 36 steps (uændret). check_versions --self-test: OK (25 mutationer + 1 negativ kontrol + positiv kontrol + rigtige filer). check_versions: OK, 8 produkter. check_python_env --self-test: OK (13 mutationer + 7 stdlib-kontroller). Stripe-worker uændret, dist/uændret (gitignored).`
- `DEPLOY` (før): `DEPLOY OK 14f0ee3 26/9` — kørsel `36199954971`: `gate` grøn (36 steps) + tre grønne deploys. Live-indhold verificeret (11 filer, lockfil 1.3.3/`^26.15.3`, `engines` + `.nvmrc` med). Se Deployloggen.
- `VERIFICÉR DEPLOY (lukket)`: `desktop-kildearkivet er et 1.3.3-arkiv 14f0ee3 2026-09-26` — GitHub Actions kører automatisk (`site/**` er i path-filteret). Verificér **indhold**, ikke HTTP 200:
  - `mahope.tools/downloads/eaa-scanner-desktop-src-1.3.3.zip` skal pakkes ud til 11 filer; `package-lock.json` skal sige `version 1.3.3` og `electron-builder ^26.15.3`, `package.json` skal have `engines.node >=22.12.0`, og `.nvmrc` skal være med. Før dette var der 10 filer, lockfilen sagde 1.3.0 og `^25.0.0`, og `.nvmrc` manglede.
- `DEPLOY` (før): `DEPLOY OK 26/9` — kørsel `36198367044` kørte `gate` grønt (34 steps) og deployede cleancopy.tools, deskuptime.com og mahope.tools grønt. Live-indholdsverificeret: se Deployloggen.
- `GATE` (opgave 17): `GRØN — python3 tools/quality_gate.py: GRØN, 34 steps (32 + design-tokens + design-tokens-selftest). Portens egen bevis: 5 mutationer fanget med navngiven grund, positiv kontrol grøn, og to scenarier der skal IKKE fejle (en side kun med /style.css, en Google-Fonts-udfyldning) fejler ikke. Bridgefindet er gjort på de rigtige filer FØR nogen blev rettet: --measure og --wrap. Stripe-worker uændret 69/69, tracking-worker uændret 83/83, dist/uændret (gitignored).`
- `RESULT` (opgave 17): Opgaven troede, de to sider var bygget af to forskellige designs, og at løsningen krævede at vælge mellem auditedwps skal og vores. **Halvdelen af den forudsætning var forkert, og det viste sig først i det byggede dist:** bygget indlæser allerede `/shell.js` og `<header class="site-header">` på alle fire sider — én header, én footer, ét skeln. Headeren, footeren, knapperne og IBM Plex kom alle fra vores skal. Det, der så forkert ud, var **tokens**: de tre værktøjssider indlæser derudover `../auditedwp`s `/assets/site.css`, et komplet designsystem med sit eget palet (grøn `#0b6e4f`) og sin egen skrifttype (Inter). Dens eget `<style>`-blok og deres eget `site.js` bruger kun de klassenavne, den kender, så filen skal rejse med — men de 27 tokens den erklærer, må ikke.

  **Fund 1 — beslutningen var at lade deres fil rejse med og trodse dens tokens.** At fjerne `assets/site.css` ville have brudt resultaterne: `site.js` indsætter `.ck-tools`, `.btn.secondary.sm`, `.ic`, `.pre-wrap`, `.copy-btn`, `.recent`, `.rcard`, `.post-grid` — elementer, kun den fil styler. Bridgen er derfor 27 `var(--color-*)`-linjer i `site/style.css`, ikke en ny side og ikke en ændring i `../auditedwp`.

  **Fund 2 — portens første kørsel fandt to reelle huller, mine egne mutationer ikke.** `--measure` (66ch mod vores 72ch) og `--wrap` (`var(--w-page)`) findes slet ikke i vores skal under de navne. De var altså **ikke** dækket af det, jeg troede, jeg havde lavet. Samme fejlform som opgave 10 og 15: en regel der så komplet ud.

  **Fund 3 — min egen port lægte to gange, og den tredje gang løb den fra sig selv.** (a) Den scannerede CSS linje for linje og så kun den *første** deklaration på hver linje. `site/style.css` skriver sin egen stil med flere deklarationer pr. linje, så porten erklærede 15 tokens dækket, da kun 12 var det. Den går nu regel-klamme-krop, så alle deklarationer i en krop tæller. (b) Den regnede *alle* kvalificerede regler som identitetsregler, så `.rcard.pass .pill { --pill-icon: … }` blev krævet dækket — en komponent, ikke et token. (c) Den talte produktreglen som en mørk-regel, så en bro under `data-product="deskuptime"` dækkede *alle* produkter, og scenariet "broen findes kun under et andet produkt" stod som fanget, fordi den netop var fanget. Nu er identitetsregler kun `:root`/`html` med attribut-kvalifikatorer, og `data-product` er undtaget. Det er syvende gang i dette repo at en port uden kontrol på sin egen logik viser sig at være teater.

  **Bevis for porten:** de to huller fra fund 2 blev fundet på de rigtige filer før rettelsen, 5 mutationer fanges med navngiven grund, og to scenarier der skal *ikke* fejle fejler ikke. Bridgen ligger i det byggede `dist/deskuptime.com/style.css`.

- **Reelle, dokumenterede salg i repoet:** 0. Det er ikke bevis for 0 salg; kun dokumentation, der kan tælles.
- **Blokerede opgaver:** ingen. Delhandlinger under opgave 5 står som `BLOCKED: kræver Mads-godkendelse` (git-historik, privat kilde, KV-inventering).
- `dist/` må regenereres af `build_sites.py`, men må ikke redigeres manuelt eller committes.
- `../auditedwp` er en ekstern buildkilde og må ikke ændres.
- Secrets, `.env*`, produktionsdatabaser og udadvendte writes er forbudte. Eneste eksplicitte undtagelse er den kontraktstyrede merge/push til `main` i dette repo, som må deploye de tre Cloudflare-Pages-domæner; `bugbottle.dev` er read-only og ejes af `mahope/bugbottle`.

### Kanonisk state-protokol

Før en ny iteration ændrer kode skal den sætte `ACTIVE_TASK` til opgavenummeret og opgavens status til `I GANG`, tælle én `TASK_ATTEMPTS`-entry, opdatere `STATE`, `ITERATION_ID` og `LAST_BRANCH` og oprette den nye `ceo/*`-branch. Hvis en opgave står `I GANG`, skal næste iteration fortsætte den og aldrig starte en anden. Når ingen er `I GANG`, vælges altid den øverste `UFÆRDIG`-opgave. Efter grøn gate, commit og merge markeres netop den opgave `FÆRDIG`, og dens resultat, gate, commit-SHA og eventuelt `DEPLOY OK` skrives konkret heri. Efter to mislykkede forsøg markeres opgaven `BLOCKED: <årsag>`, hvorefter den næste `UFÆRDIG`-opgave vælges. De øvrige filer `STATUS.md`, `BUILD.md`, `DECISION.md`, `RESEARCH.md` og `BUDGET.md` er arkiv- og factualdokumenter i denne loop; kun denne plan styrer næste iteration.

## Kvalitetsgate

Gaten er **én kommando**, og den har én ejer:

```bash
python3 tools/quality_gate.py
```

Den bygger alle fire dists og kører 28 checks i rækkefølge, og dræber ved den
første røde med navnet på steppet. `python3 tools/quality_gate.py --list` printer
den som den gamle `&&`-linje, og `--inputs` printer de filer, path-filteret skal
dække. Opgave 11 (25. september 2026) flyttede den herfra, fordi den lå i planen
som en håndskrevet linje, mens CI kørte tre kortere lister — og fordi ingen af
dem var sande.

CI kalder præcis den kommando i `deploy-sites.yml`s `gate`-job, og `deploy` har
`needs: gate`. `tools/test_deploy_workflow.py` beviser bagefter, at workflowen
kører den, at deploy-jobbene afhænger af den, at ingen gatestræk står skrevet ud
uden om den, at path-filteret dækker alt `--inputs`, og at `auditedwp` er pinnet
til én 40-tegns SHA i begge jobs.

Den underliggende check-liste, hvert step med de filer det læser:

| # | Step | Kommando | Kræver dist |
|---|---|---|---|
| 1 | build | `python3 build_sites.py` | — |
| 2 | sitemaps | `python3 tools/check_sitemaps.py` | ja |
| 3 | seo | `python3 tools/seo_check.py` | ja |
| 4 | stripe-worker | `node tests/stripe-worker.test.mjs` | — |
| 5 | tracking-worker | `node tests/tracking-worker.test.mjs` | — |
| 6 | inline-js | `python3 tools/check_inline_js.py` | ja |
| 7 | private-content | `python3 tools/check_private_content.py` | ja |
| 8 | page-profile-distribution | `python3 tools/check_page_profile_distribution.py` | ja |
| 9 | page-profile-distribution-selftest | `… --self-test` | — |
| 10 | page-profile-tests | `python3 page-profile/test_page_profile.py` | — |
| 11 | clean-copy-distribution | `python3 tools/check_clean_copy_distribution.py` | ja |
| 12 | clean-copy-distribution-selftest | `… --self-test` | — |
| 13 | license-clients | `python3 tools/check_license_clients.py` | — |
| 14 | license-clients-selftest | `… --self-test` | — |
| 15 | license-client-tests | `node test.js` (103 checks) | — |
| 16 | license-flow | `node tools/test_license_flow.js` (15 checks) | — |
| 17 | obsidian-plugin-tests | `node obsidian-plugin/test.js` | — |
| 18 | extension-tests | `node extension-clean-copy/tools/test_clean_copy.js` | — |
| 19 | product-copy | `python3 tools/check_product_copy.py` | — |
| 20 | stripe-ctas | `python3 tools/check_stripe_ctas.py` | — |
| 21 | stripe-ctas-selftest | `… --self-test` | — |
| 22 | weekly-report-tests | `python3 tools/test_weekly_report.py` | — |
| 23 | deploy-workflow | `python3 tools/test_deploy_workflow.py` | — |
| 24 | deploy-workflow-selftest | `… --self-test` | — |
| 25 | python-env | `python3 tools/check_python_env.py` | — |
| 26 | python-env-selftest | `… --self-test` | — |
| 27 | links | `python3 tools/check_links.py` | ja |
| 28 | links-selftest | `… --self-test` | — |

Steps der kræver dist springes over, når `dist/` er tomt, så porten kan bruges
på et delvis checkout uden at lyve om grønt. Lokalt tager hele gaten 2 minutter,
hvoraf `check_inline_js.py` står for 100.

### Baggrund for de enkelte gates

Den dækker kun siteproduktionen. Hver opgave skal have én konkret `**Gate:**`-linje med arbejdsmappe og kommandoer. Hvis en viste opgave endnu mangler en eksakt produktkommando, skal den researches og skrives ind, før opgaven markeres `I GANG`; usikre placeholder-gates er ikke gyldige. `site/_worker.js` kræver altid Stripe-worker-testen. Helt nye worker-ruter skal have en test, der beviser både success og failure. En eksisterende testtælle må ikke reduceres for at få gaten grøn.

Produktgaten for de shippede licensklienter (tilføjet 2026-09-25 i opgave 7 del 1,
udvidet i del 2) er `node tools/test_license_clients.js`, og `node test.js` indlæser
den. Den indlæser de filer der faktisk ships — Obsidian-pluginen, Chrome/Firefox
options.js og webværktøjets inline blok i en vm-sandbox — og dækker
200/403/404/400/409/500/503, status 0 og syvdagescachen.

`tools/check_license_clients.py` blev tilføjet 2026-09-25 i opgave 7 del 2, fordi
tests ikke kan se en *ny* klient, der kalder `/api/license` uden `product`. Den
finder alle sådanne kilder i repoet og fejler ved manglende `product`, død vært i et
licenskald, den lukkede Lemon Squeezy-API, et indlejret modul der afviger fra
`tools/clean_copy_license.js`, en divergeret Firefox-kopi eller en undtagelse uden
fil. `site/_worker.js` (serveren) og `desktop/main.js` (EAA, endnu uden produkt i
kontrakten) er dokumenterede undtagelser. Den afhænger af `tools/clean_copy_license.js`,
`site/clean-copy-tool.html`, `site/compliance-report.html` og de to extensionsmapper,
og skal derfor ligge i deploy-workflowens path-filter.

`check_private_content.py` blev tilføjet 2026-09-25 i opgave 5, fordi et betalt
leveringsfil i `dist/` er en reel læk, ikke en SEO-fejl. Den afhænger af
`tools/paid_content.json`, så begge filer ligger i deploy-workflowens path-filter.

`check_page_profile_distribution.py` blev tilføjet 2026-09-25 i opgave 6, fordi den
publicerede Page Profile-kopi er håndkopieret, og en divergerende kopi er en reel
købsfejl: køberen får en CLI der afviser sin egen Stripe-nøgle, eller en
downloadside der lover en udgave, der ikke kan hentes. Den afhænger af
`page-profile/`, `site/downloads/page-profile/` og de to landingssider, og alle
tre ligger i deploy-workflowens path-filter.

`check_clean_copy_distribution.py` blev udvidet 2026-09-25 i opgave 8 med
`check_publish_targets` og `check_every_archive_is_reachable`, fordi gaten
kun kendte et arkivs *navn* og aldrig hvilket domæne der publicerede det. En
rodrelativ reference til et arkiv i et domæne uden det er en 404 på købsstien,
og `build_sites.py` tæller den ikke som unresolved, fordi filen findes i
`site/`. De to checks læser det **byggede** `dist/` og springes over, når
intet er bygget. Fordi de læser `dist/`, skal gaten køre *efter*
`build_sites.py` — den gør allerede, i deploy-workflowens gate-trin.

`tools/check_links.py` blev tilføjet 2026-09-25 i opgave 10, fordi buildets egen
optælling var regex-baseret og derfor ikke kunne skelne en reference fra et
kodeeksempel: `blog/open-graph-checker.html` viser `<meta … content="/img/cover.jpg">`
som eksempel på en fejl, og det blev bogført som en død reference, ingen kunne
rette. Den bruger `html.parser` på det **byggede** `dist/`, springer
`pre`/`code`/`script`/`style` over, og løser krydsdomæne-referencer mod det
domænes dist — kun hvis det dist faktisk er bygget i samme kørsel, ellers dør
matrix-jobbet i CI på en 404 der ikke findes. Den kræver desuden at alle
download-artefakter kan hentes og at formularer med en `action` uden
worker-marker peger på en rute, der findes. Den springes over når intet er bygget.
`build_sites.py` har nu *også* exit 1 ved uopklarede referencer, så porten ikke
kan slås fra ved at glemme at køre den. Begge er i deploy-workflowens
path-filter; fuld kontrol i `gate`-jobbet.

`tools/test_deploy_workflow.py` blev tilføjet 2026-09-25 i opgave 16 og udvidet
2026-09-25 i opgave 11 med `check_gate`. Den første del simulerer de faktiske
push- og pull_request-events mod begge workflows' egne filtre med GitHubs
dokumenterede semantik, så en fejl i path-filteret eller i ref-filtret fanges som
fejl og ikke som "workflowen kører næste gang". Den læser YAML med
`tools/mini_yaml.py` og ikke PyYAML, fordi `deploy-sites.yml` kører på
`setup-python` uden installerede pakker — bevist af kørsel `36180367257`, hvor
`import yaml` dræbte alle tre deploy-jobs. `check_gate` beviser de ting en
trigger-analyse ikke kan: at `gate`-jobbet faktisk kalder
`python3 tools/quality_gate.py`, at deploy-jobbene har `needs: gate`, at ingen
gatestræk står skrevet ud i en `run:`-blok ved siden af den, at path-filteret
dækker hver fil i `quality_gate.py --inputs` (glob-input udvides mod den rigtige
filstruktur), og at `auditedwp` er pinnet til én 40-tegns SHA i begge jobs.

`tools/quality_gate.py` blev tilføjet 2026-09-25 i opgave 11, fordi gaten lå i
to steder der ikke var ens: planens `&&`-linje med 13 kommandoer og tre
matrixjobs med 15 hver. Tre af planens checks kørte aldrig i CI. Én fil med én
liste løser det, og filen er den der definerer `--inputs`, så path-filteret er
afledt i stedet for håndskrevet.

Den dækker kun siteproduktionen. Hver opgave skal have én konkret `**Gate:**`-linje med arbejdsmappe og kommandoer. Hvis en viste opgave endnu mangler en eksakt produktkommando, skal den researches og skrives ind, før opgaven markeres `I GANG`; usikre placeholder-gates er ikke gyldige. `site/_worker.js` kræver altid Stripe-worker-testen. Helt nye worker-ruter skal have en test, der beviser både success og failure. En eksisterende testtælle må ikke reduceres for at få gaten grøn.

Efter et mergecommit skal livekontrollen køre som `python3 build_sites.py && python3 tools/check_live_sitemaps.py --commit "$(git rev-parse HEAD)"`. Først efter commitet må buildet regenereres, og live-scriptet kræver fuld 40-tegns SHA; en short SHA eller `dist/` fra et tidligere commit afvises.

## Mission og autoritative kilder

- Missionen er fire statiske sites bygget fra `site/` af `build_sites.py`: `cleancopy.tools`, `deskuptime.com`, `bugbottle.dev` og `mahope.tools`.
- Stripe og licensserveren er den aktuelle betalingsvej. Lemon Squeezy og Gumroad er døde og må ikke genoplives.
- Betalte og offentlige værktøjer skal være fuldt funktionelle. Betalt værdi skal være dokumenteret og må ikke hænge på Mads' løbende indsats.
- Betalt indhold må ikke ligge i det offentlige repo. Private file skal bygges reproducerbart og leveres fra Cloudflare KV efter Stripe-verifikation.
- `build_sites.py` fordeler først matchede filer til hvert site og giver resten til `mahope.tools`: `build_sites.py:46-140`.
- Den fælles runtime er `site/_worker.js`: `build_sites.py:142-158`.
- SEO, robots og sitemap genereres af `build_sites.py`: `build_sites.py:959-1057`.
- Den eksterne DeskUptime-kode ligger i `../deskuptime`; den er read-only for denne plan og skal have sin egen ændringsiteration.

## Researchfund

### Betaling og købsrejse

- `/api/lemon-webhook` og `handleLemonWebhook` findes stadig i `site/_worker.js` og kopieres til alle fire genererede Worker-output: `site/_worker.js:64-65`, `site/_worker.js:900-1031`, `build_sites.py:142-158`.
- `tools/test_license_flow.js` er en blandet legacy-test: Lemon-webhook-cases skal fjernes, mens dækning af fortsat understøttede licensruter skal bevares eller flyttes til den separate Stripe-worker-test.
- Page Profile Stripe-udsteder 32 hex-tegn, men CLI'en kræver `PPRO-` + 32 tegn: `site/_worker.js:2861-2875`, `page-profile/page_profile.py:33-58`.
- Clean Copy-webværktøjet sender korrekt `product: clean-copy-pro`, men root/Obsidian-pluginterne og mindst én browserudvidelseslicensklient mangler produktfeltet: `site/clean-copy-tool.html:427-432`, `obsidian-plugin/main.js:718-729`, `main.js:204-218`, `extension-clean-copy/options.js:46-92`.
- Licensklienter skal cache Pro-status i rimelig tid, eksempelvis syv dage, ved `503`/5xx, så betalende brugere ikke låses ude.
- Betalte downloads forventes i KV som `paidfile:*`: `site/_worker.js:2717-2725`, `site/_worker.js:3024-3040`. Repoet har ingen reproducerbar producer/uploader. **Korrigeret 25. september:** de betalte kilder lå *oprindeligt* i det offentlige repo (`products/`), men `3eb1dac` fjernede alle tolv, og ingen af de seksten betalte leveringsfiler findes i dag i tree eller `dist/`. Historikken er uændret og kræver Mads' go; se opgave 5 og `❓ Til Mads` 3.
- Stripe-salg skriver `t:all:sales:<product>`, mens `/api/stats` og ugerapporten stadig læser den gamle Lemon-tæller: `site/_worker.js:1235-1246`, `site/_worker.js:2888-2893`, `tools/weekly_report.py:148-180`. Den nuværende salgstæller er desuden en read-modify-write-operation og må ikke alene være ground truth ved parallelle fulfillments.

### sider, claims og konvertering

**Optællet 25. september 2026 i opgave 10 — de 18 var ni fejl og ni falske positiver.**
Reelle: (1) `/assets/site.css` + `/assets/site.css` på DeskUptimes tre værktøjssider
har aldrig eksisteret i noget dist; (2) fire `ld+json`-"url" på danske artikler pegede
på engelsk sti; (3) `/da/blog` findes ikke; (4) NIS2-siden viste sig selv med `/da/`;
(5) README linkede desktop-kilde-1.2.0; (6) `llms.txt` havde et efterstillet `` `, `` i stien.
Falske: `blog/open-graph-checker.html` **viser** `content="/img/cover.jpg"` som et
eksempel på en fejl, og `blog/check-website-speed-without-lighthouse.html` har
`Open hermes-passiv.pages.dev/page-profile,` i en `<pre>`. Resten af listen var
krydsdomæne- eller tekstfund uden egen værdi.
Fire fejl kom først frem af den nye port: `write_generated()` sprang over
`rewrite_text` for 404- og søgesiderne (dødt "Guides"-link i headeren på fire
sider pr. sprog), to publicerede artikler havde en ubrugt `{URL}`-generator-
placeholder, `downloads.html` lovede scanner-1.3.0 mens disken har 1.2.0, og
`compliance-ai.html` bruger relative `href="scan"`-referencer der kun virker i roden.

- DeskUptime EN/DA lover “no phone-home”, “no central server” og “no telemetry”, selv om Pro aktiverer og revaliderer mod `mahope.tools`: `site/deskuptime/index.html:130-150`, `site/da/deskuptime/index.html:127-147`, `../deskuptime/src/license.js:70-152`.
- Den danske DeskUptime-blogartikel siger også, at licensen er offline: `site/da/blog/overvaag-hjemmeside-fra-terminalen.html:25-86`.
- Clean Copy, Page Profile og DeskUptime har allerede tydelig gratis/Pro-sammenligning og én direkte Stripe-CTA på deres centrale EN/DA-sider.
- Flere ældre Pro-/premium-sider viser fortsat priser eller “coming soon” uden købsmulighed: `site/site-icons.html:126-155`, `site/downloads.html:91-115`, `site/blog/eaa-compliance-scanner-desktop.html:67-119`, `site/compliance-report.html:127-157`, `site/scan-da.html:89-97`.
- `site/index.html:159-162` og `site/da/index.html:156-159` siger stadig, at betalt checkout ikke er koblet på.
- Ugerapport 2026-37 og 2026-38 har kun samlede top-8 paths uden domæne. Ugerapport 2026-39 har tom trafik efter timeout: `reports/weekly/2026-39.json:12`, `reports/weekly/2026-39.json:210-216`.
- Alle fire sites deler KV-namespace, og tracking gemmer path uden hostname. Derfor kan de nuværende rapporter ikke rangere Pro-sider pr. domæne: `site/track.js:1-18`, `site/_worker.js:1147-1173`, `build_sites.py:1148-1152`.
- Flere sider har både `track.js` og inline tracking og kan derfor tælle samme besøg to gange.

### SEO, links og drift

- Robots og sitemap genereres korrekt domænespecifikt for Clean Copy og DeskUptime.
- `mahope.tools/sitemap.xml` indeholder `https://mahope.tools/` to gange, fordi både `index.html` og `free-tools.html` bliver canonical root: `build_sites.py:126-139`, `dist/mahope.tools/sitemap.xml:3-4`.
- Live `bugbottle.dev/sitemap.xml` afviger fra det nuværende lokale buildoutput. Dette er diagnosticeret som deployment-ejerskabsdrift, ikke ved at redigere `dist/`.
- `bugbottle.dev` serverer 40 routes fra `mahope/bugbottle` via Dokploy på commit `07828a1d605383c58cf44416447e0497e91fdac3` og viser BugBottle 1.0.1. Denne repo bygger 7 routes fra v0.4.0-landingmateriale; `bugbottle-dev.pages.dev` matcher den lokale shadow-build. Deploy-workflowen udgiver derfor ikke denne forældede shadow; den separate `--all` livekontrol matcher den autoritative kilde read-only.
- Den nye lokale gate finder kun selv-referencede, indexerede HTML-ruter; noindex, de fire erklærede 404/search-ruter, Clean Copy-aliaserne og Workerens deklarerede redirectkilder er ekskluderet og dækket af negative tests.
- Hver build publicerer `build-info.json` med domæne, commit, routeantal og SHA-256 af sitemap/routes. Live-gaten kræver byte-identiske robots/sitemap/build-info og derefter 200 + self-canonical + indexerbar status for hver sitemap-URL.
- Kilde-scripts som `tools/gen_sitemap.py`, `tools/fix_sitemap_redirects.py`, `tools/full_site_check.py`, `health_check.py` og `verify_live.sh` er hardcoded til det gamle `hermes-passiv.pages.dev`.
- Den seneste build registrerer 18 unresolved references: Clean Copy 1, DeskUptime 6, BugBottle 2, mahope.tools 9. `build_sites.py` tæller dem men returnerer alligevel succes: `build_sites.py:1181-1195`.
- Deploy-CI kører build og SEO-check, men ikke Stripe-worker-test, inline-JS-test eller broken-reference-gate: `.github/workflows/deploy-sites.yml:49-83`.
- Deploy-triggeren mangler `tools/brand.py`, `tools/pagepass.py` og `tools/seo_check.py`, selv om de påvirker build eller gate: `.github/workflows/deploy-sites.yml:10-14`.
- `auditedwp` checkes ud uden fast commit-SHA: `.github/workflows/deploy-sites.yml:40-43`.

### Afhængigheder og runtime

- Den centrale oversigt `~/.local/oxloop/AFHAENGIGHEDER.md` er fra 2026-08-23 og indeholder ikke dette repo. Den er derfor ikke tilstrækkelig aktuel.
- En read-only OSV-scanning den 24. september fandt 15 advisory-fund i `desktop/package-lock.json`, blandt andet i `app-builder-lib 25.1.8`, `builder-util-runtime 9.2.10`, `js-yaml 4.3.1` og `tar 6.2.1`.
- Den samhængende patched linje var `electron-builder 26.15.3`; Electron 44.x kunne samtidig opgraderes til 44.4.5.
- `desktop/package.json` mangler `engines` trods Electron 44's krav om Node `>=22.12.0`; repoet mangler også `.nvmrc`: `desktop/package.json:83-86`, `desktop/package-lock.json:2148-2150`.
- `site-icons/pyproject.toml` har projektmetadata under `[tool]` i stedet for `[project]` og kan derfor ikke installeres korrekt: `site-icons/pyproject.toml:1-23`.
- Python-buildafhængigheder er hverken samlet eller låst. Det gælder Markdown, Pillow, ReportLab, fpdf2 og Playwright.
- Flere produktversioner og lockfile-versioner afviger, blandt andet desktop 1.3.3 mod lock-root 1.3.0 og Page Profile 1.1.0 mod `pyproject.toml` 1.0.0.

## Prioriteret kø

Opgave 1-4 er missionens eksplicitte åbne opgaver og kommer derfor før nyopdagede security-, purchase- og CI-opgaver. Opgraderingsreglen “sikkerhed først” gælder blandt alle øvrige backlogitems efter denne åbne missionsekvens.

### 1. FÆRDIG — Fjern Lemon Squeezy-ruten helt

**Begrundelse:** Den gamle webhook er stadig i den fælles Worker og kopieres til alle fire sites, selv om Lemon Squeezy ikke længere er en gyldig betalingsvej.

**Omfang:**

- Fjern `/api/lemon-webhook` og `handleLemonWebhook` samt relaterede LS-kommentarer fra `site/_worker.js`.
- Fjern kun Lemon-webhook-cases fra `tools/test_license_flow.js`. Bevar eller portér dens fortsat relevante dækning af activation, validation, expiry, lookup og rate limiting, så opgaven ikke sletter dækning af andre ruter.
- Undgå ændringer i `/api/stripe-webhook`, `/api/stripe/fulfillment` og `/api/download`.

**Acceptkriterier:**

- `site/_worker.js` indeholder hverken `lemon-webhook`, `handleLemonWebhook` eller `LS_WEBHOOK_SECRET`.
- Stripe-worker-testen har en assertion for, at den fjernede route returnerer 404 på både GET og POST.
- Den eksisterende Stripe-testkæde fortsætter grøn, uden at antallet af assertions reduceres.
- Legacy-testen indeholder ingen Lemon-webhook-fixture, men bevarer dækning af de øvrige understøttede licensruter.

**Gate:** `node --check site/_worker.js && node tools/test_license_flow.js && node tests/stripe-worker.test.mjs` plus hele kvalitetsgaten ovenfor.

### 2. FÆRDIG — Gør DeskUptime-teksten sand

**Begrundelse:** Pro-licensen kontakter licensserveren, så absolutte påstande om “no phone-home”, “no central server” og “no telemetry” er fejl.

**Omfang:**

- Ret EN- og DA-landingssiderne til at skelne mellem lokal gratis URL-monitorering og online Pro-licensaktivering/revalidering.
- Ret den danske blogartikel og dens generative kilde `tools/make_blog_da_mirrors_461.py`, der kalder licensen offline.
- Beskriv kun den konkrete dataoverførsel: licensnøgle, device-id, produkt og licensstatus; påstå ikke produkttelemetri uden dokumentation.
- Tilføj `tools/check_product_copy.py`, som fejler ved de gamle absolutte claims i både de fire public sider og den generative blogkilde.

**Acceptkriterier:**

- Ingen af de fire sider indeholder de gamle absolutte claims.
- EN og DA siger eksplicit, at Pro aktiverer og revaliderer mod `mahope.tools`.
- EN og DA siger, at URL-liste og check-resultater ikke uploades til en central monitoreringstjeneste.
- Hele kvalitetsgaten er grøn.

**Gate:** `python3 tools/check_product_copy.py` plus hele kvalitetsgaten.

### 3. FÆRDIG — Gør robots, sitemap og domænedrift korrekt

**Begrundelse:** Fire domæner skal have én kanonisk, komplet og live-matchende SEO-overflade. Den nuværende mahope.tools-dublet og BugBottle-driften kan skade indeksering.

**Omfang:**

- Ret den dublede `https://mahope.tools/` i `build_sites.py` uden at slette en reel side.
- Gør robots/sitemap-kontrollen domæne-aware og automatisér den i kvalitetsgaten med `tools/check_sitemaps.py`.
- Tilføj `tools/check_live_sitemaps.py`, som som standard verificerer de tre Pages-ejede live domæner og med `--all` også den separate BugBottle-kilde read-only: robots, sitemap, canonicale URL'er, sider og commit-version.
- Definer routeinventaret eksplicit: hver indexerbar, self-referenced canonical-HTML-rute skal forekomme én gang; `404.html`, generated search-ruter, redirect-only sider og dokumenterede aliaser skal udelukkes. Et alias skal enten have en reel canonical/redirect-strategi eller eksplicit noindex.
- Opdatér gamle hardcoded sitemap/health-check-scripts, så de ikke peger på `hermes-passiv.pages.dev`.
- Diagnosticér hvorfor live BugBottle-output afviger fra source-buildet; ret source/CI, ikke `dist/`.

**Implementeret denne iteration:**

- `free-tools.html` er en reel, self-canonical `/free-tools`-side; mahope.tools-hjemmesiden kommer ikke længere fra en alias-kopi. Sitemap, llms og search-index filtrerer noindex og ikke-self-canonical sider.
- `tools/route_inventory.json` er den uafhængige, eksplicitte inventory med 32 Clean Copy-, 5 DeskUptime-, 7 lokale BugBottle- og 251 mahope.tools-ruter. `build_sites.py` og `tools/check_sitemaps.py` afviser nye, manglende eller slash-ekvivalente ruter; 11 negative/positive tests dækker domæne, duplikater, inventory, noindex, redirects og commit.
- `tools/check_live_sitemaps.py` verificerer de tre Pages-ejede domæner mod lokale bytes, commit, title, JSON-LD, HTTP `X-Robots-Tag` og alle sitemap-sider. `--all` kræver en disposable, read-only BugBottle-kilde med genererede robots/sitemap og verificerer dens Git-commit.
- Den separate `mahope/bugbottle`-kilde er diagnosticeret read-only på commit `07828a1d605383c58cf44416447e0497e91fdac3`: dens `build-docs.mjs` genererer 33 docs-sider, fire selvstændige sider og changelog, i alt 40 sitemap-routes. Live `bugbottle.dev` matcher dens robots/sitemap og alle sider.
- Deploy-CI bruger den nye lokale og live-gate for de tre Pages-ejede domæner, kører Stripe-worker- og inline-JS-tests før deploy, dækker alle buildinputs i path-filteret, pinner `mahope/auditedwp` til `5e244dcff242352cd5be31a55ca5f7d260f7e520` og deployer kun fra `main`.
- Den røde første live-gate gav permanent harness-dækning: Wrangler installeres i repo-roden og deployer en eksplicit `dist/<domæne>`-sti; `pagepass.py` indpakker ikke `<table>` i scripts/pre/textarea; `seo_check.py` afviser ugyldig JSON-LD før deploy.

**Resultat:** Implementeringen blev merged i `fb4189d`; den korrigerende deploy-gate blev merged i `b7c8a64`. GitHub Actions-run `36099316657` og en uafhængig live-kontrol bekræfter robots, sitemap, build-info, JSON-LD, canonicale og alle 288 Pages-ruter.

**Acceptkriterier:**

- Hvert af de fire builds har gyldig `robots.txt` med eget sitemap og `sitemap.xml` med kun sit eget domæne.
- Ingen sitemap har duplikerede `<loc>`-værdier.
- Hver indexerbar canonical-HTML-rute findes præcis én gang i det pågældende sitemap; eksklusionsreglerne er dokumenterede og stabile.
- `python3 tools/check_sitemaps.py` returnerer non-zero ved forkert domæne, duplikat eller manglende canonical-rute.
- Efter deploy er live robots, sitemap og sidesantal identiske med det seneste `main`-build.
- Search Console-punktet står under `❓ Til Mads`.

**Gate:** `python3 tools/test_check_sitemaps.py && python3 tools/test_check_live_sitemaps.py && python3 build_sites.py && python3 tools/check_sitemaps.py && python3 tools/seo_check.py` plus resten af kvalitetsgaten.

**Deploy-gate:** `python3 tools/check_live_sitemaps.py --commit <merge-sha>` for de tre Pages-domæner efter GitHub Actions er grøn. Den separate read-only driftkontrol er `python3 tools/check_live_sitemaps.py --all --commit <merge-sha> --bugbottle-source <disposable-checkout> --bugbottle-source-commit 07828a1d605383c58cf44416447e0497e91fdac3 --attempts 1`; kontrollen arkiverer og bygger den pinned commit i en midlertidig mappe og matcher derefter den autoritative BugBottle-kilde.

### 4E. FÆRDIG — Page Profile Pro skal acceptere Stripe-nøgler

**Begrundelse:** Licens-audit 2026-09-25: `page-profile/page_profile.py:54-59` accepterer kun `PPRO-`+32 base32, men Stripe-leveringen udsteder 32 hex-tegn, så **enhver købt nøgle afvises**. Samtidig kan `--gen-key` (linje ~912-920) med det offentlige salt (linje ~37) lave gyldige nøgler, så Pro kan låses op gratis. Købslinket i CLI'en (linje ~79) peger på det forældede `hermes-passiv.pages.dev`.

**Omfang:**

- Erstat den offline validering med `activate`/`validate` mod `https://mahope.tools/api/license/` med `product: "page-profile-pro"` efter `C:\Projects\business\planer\2026-09-24-stripe-kontrakt.md` (32 hex, trim + små bogstaver; stabilt `device_id` gemt i `~/.page-profile-license`; 7 dages cache ved 503/netværksfejl; tydelige beskeder for 403/404/409).
- Fjern `--gen-key` og saltet.
- Købslink: `https://buy.stripe.com/9B6eVcgHp7YK69ggN9bMQ04`.
- Udgiv som 1.2.0 i `site/downloads/page-profile/` og opdatér versionsreferencer.

**Implementeret denne iteration:**

- `~/.page-profile-license` er en 0600 JSON-state med normaliseret 32-hex-nøgle, stabilt device-id og tidspunkt for seneste positive svar. Aktivering og validate bruger henholdsvis `/activate` og `/validate` med `product: page-profile-pro`.
- Netværksfejl og HTTP 5xx kan bruge højst syv dages positive cache. HTTP 403/404/409, `valid: false`, formatfejl og malformed HTTP 200-svar bruger aldrig cachen. 11 offline tests dækker payload, hard/soft fejl, cache-grænse, legacy-fjernelse og public copy.
- Kanonisk og publiceret script er byte-identiske; `page-profile-1.2.0.tar.gz` er bygget fra samme kilde og indeholder den kanoniske kode. EN/DA landingssider, README og dansk blogkilde fortæller nu korrekt om online licensstjek og syvdages outage-cache.
- Frisk review fandt to P1-fejl: malformed 200-svar kunne bruge cache, og tarball-vejledningen pegede på bindestreg. Begge er rettet og dækket af de grønne gates. Den planlagte separate distributions-CI-forsvar er bevaret som opgave 6.

**Acceptkriterier:**

- Test uden netværk (mocket HTTP): gyldig hex-nøgle aktiveres, `PPRO-`-nøgler og `--gen-key` findes ikke længere, 503 giver Pro i højst 7 dage fra seneste validering, 403/404/409 giver korrekt besked.
- Live read-only: `validate` med en tilfældig 32-hex-nøgle giver 404.

**Gate:** `python3 page-profile/test_page_profile.py` plus hele kvalitetsgaten.

### 4F. FÆRDIG — Luk tre huller i licens-workeren

**Begrundelse:** Licens-audit 2026-09-25 af `site/_worker.js`.

**Omfang:**

- Refundering af abonnementer: ved checkout i abonnementstilstand er `s.payment_intent` null, så der skrives ingen `lic-pi:`, og `revokeForCharge` (~linje 2818) falder tilbage på `charge.invoice`, som ikke findes i nyere Stripe-API-versioner. Gem koblingen payment_intent → licens i `invoice.paid` (første faktura) eller slå op via `invoice_payments`, så en refunderet årslicens (`clean-copy-pro`, `eucomply-pro`, `page-profile-pro`) tilbagekaldes.
- Uventede fejl i licens-API'et skal svare 503 (kontrakten), ikke 500 (~linje 889).
- `activate_url` for `clean-copy-pro` skal pege på en side, der forklarer hvor nøglen indtastes i hver klient (Chrome, Firefox, Obsidian), fx `https://cleancopy.tools/activate/`; opret siden i `site/`.

**Acceptkriterier:**

- Worker-test: `charge.refunded` for et abonnement (uden `payment_intent` på sessionen) tilbagekalder licensen; engangskøb virker som før.
- Worker-test: en kastet fejl i licens-handleren giver 503.
- Aktiveringssiden findes i sitemap og består SEO-checket.
- Stripe-worker-testens antal tests falder ikke.

**Gate:** `node tests/stripe-worker.test.mjs` plus hele kvalitetsgaten.

**Implementeret denne iteration:**

- `fulfillStripeSession` gemmer `lic-invoice:<invoice>`; `invoice.paid` udtrækker PaymentIntents fra både eventens `payments` og en ekspanderet faktura og gemmer `lic-pi:<payment_intent>`. `revokeForCharge` bruger disse koblinger før sin subscription-fallback.
- Licenshandlerens uventede fejl er 503 i stedet for 500, uden at afsløre stack traces.
- `clean-copy-pro` bruger `https://cleancopy.tools/activate/`. Siden er indexérbar, ligger i Clean Copy-sitemap og har instruktioner til Chrome/Edge/Brave, Firefox, Obsidian og webværktøjet.
- Worker-testen dækker 57 assertions, inklusive abonnement uden session-payment-intent, refundering, 503 og den nye aktiverings-URL.

**Commit:** `4ad9457` — `Ret licensrefunding og Clean Copy-aktivering`.

### 4A. FÆRDIG — Gør trafikdata domæneopdelt og troværdige

**Begrundelse:** Ugerapport 2026-39 er tom, og de gamle rapporter kan ikke adskille fire domæner eller skelne duplikattracking. Uden troværdige data kan opgave 4B ikke vælge sider fra data.

**Omfang:**

- Lad Workeren aflede domæne og tid fra `request.url`; ignorer spoofede clientfelter og allowlist de fire domæner.
- Gem path og domæne uden at gemme rå IP som identitet.
- Fjern dobbelt pageview fra sider, der både indlæser `track.js` og har inline tracking.
- Undtag kendte bots, CI og interne health checks; tilføj tests, at sådanne besøg ikke øger tælleren.
- Gør `/api/stats` og `tools/weekly_report.py` domæneopdelt.
- Brug den eksisterende unikke `ful:<checkout-session>`-post som eneste idempotente salgsledger og tæl unikke session/product-poster; fjern den separate `t:all:sales:*`-tæller som ground truth.

**Implementeret i `df25c8b` og `9569979`:**

- Hver pageview/download er en egen KV-event med domæne, dato, path og daily hash af IP+UA; rå IP gemmes ikke. Path kommer fra et påkrævet same-origin `Referer`, og domæne/dato kan ikke spoofes via JSON.
- Kendte bots, CI, Lighthouse, health/sitemap-checks og den ugentlige rapport filtreres. Dobbelt pageviews fjernes ved at fjerne inline pageview-kald fra sider, der allerede indlæser `track.js`.
- `/api/stats` kræver et afledt bearer-token fra den eksisterende server-secret, og dashboardet hverken logger tokenet i URL'en eller i sessionStorage. Tredjeparts-BugBottle-scriptet er fjernet fra admin-siden.
- Salgsledgeren er `ful:<checkout-session>`, og både replay og parallel fulfillment giver én dokumenteret post. En pending-markør uden fuldført `ful:`-post gør status `unknown`; fejlet pending-skrivning afbryder leveringen, så der ikke opstås usynlig delvis salgsdata.
- Manglende eller ugyldige KV-counters, unikke, traffic- og fulfillmentdata er `unknown`; den ugentlige rapport parser kun dokumenterede heltal og bevarer kendte domæner adskilt.
- Frisk pre-land review fandt fire konkrete huller og en CI-regression; alle er rettet og dækket af de grønne gates ovenfor.

**Acceptkriterier:**

- En syntetisk test skaber præcis én talt pageview pr. domæne/path og ingen talt bot-/CI-pageview; et spoofet domænefelt ignoreres.
- Parallelle fulfillments og replay af samme checkout-session tæller præcis ét salg pr. product.
- Ugerapporten viser top paths for hvert af de fire domæner og separate, dokumenterede Stripe-salg pr. produkt.
- Manglende/timeout-data rapporteres eksplicit som ukendt, aldrig som 0.
- `node tests/tracking-worker.test.mjs` og `python3 tools/test_weekly_report.py` er grønne.

**Gate:** `node tests/tracking-worker.test.mjs && python3 tools/test_weekly_report.py` plus hele kvalitetsgaten.

### 4B. FÆRDIG (del 1 i `1bf981f`, del 2 i `ceo/ranking-basis`) — Prioritér konvertering uden nye Stripe-produkter

**Begrundelse:** De fire centrale produktsider er stærke, men gamle Pro-tilbud uden købsmulighed og modstridende checkout-claims skader købsrejsen.

**Omfang:**

- Definer konsekvent rankingperioden som de seneste syv fulde dage. En ny rapport skal have `ranking_basis: traffic` med domæne/path og uden test-/bottrafik.
- Kræv mindst 30 verificerede pageviews i perioden og mindst 5 i hvert domæne, der skal rangeres. Hvis et krav ikke er opfyldt, skal rapporten eksplicit have `ranking_basis: unknown`; gå derefter deterministisk tilbage til de fire centrale produktsider og inventaret af alle synlige Pro-tilbud uden at påstå, at de er mest besøgte.
- Opret `docs/stripe-kontrakt.md` fra missionens eksisterende offentlige Stripe-tabel og `tools/stripe_catalog.json` som maskinlæsbar allowlist; check-scriptet skal fejle ved drift mellem dem.
- Inventér alle synlige Pro/premium-tilbud med side, produkt, pris og CTA.
- Brug kun Payment Links og product keys fra missionen. Findes intet tilladt tilbud, skal den gamle købs-påstand fjernes eller flyttes til `❓ Til Mads`; opret ikke et nyt Stripe-produkt.
- Fjern de forældrede globale claims om manglende checkout.

**Del 1 — implementeret og merged i `1bf981f`:**

- `tools/stripe_catalog.json` er maskinlæsbar allowlist med alle 13 kontraktsprodukter (product_key, navn, kind, pris, antal maskiner, payment link). `docs/stripe-kontrakt.md` er den menneskelæselige modstykke med hele købstabellen, licens-API'et og hvad der ikke er tilladt.
- `tools/check_stripe_ctas.py` fejler ved drift mellem katalog, kontraktdok, `site/_worker.js` (`STRIPE_PRODUCTS` + `STRIPE_LINKS`), ethvert `buy.stripe.com`/`donate.stripe.com`-link i source og shippede klienter, priser der ikke er dokumenteret pr. side, manglende eller dobbelte CTA'er, købssider der mangler i inventaret og alle forbudte claims. `--report` printer det fundne inventaret, `--self-test` beviser at fem driftformer fanges (5/5).
- Inventaret dækker 15 købssider: Clean Copy EN/DA + webværktøj + aktiveringsguide, DeskUptime EN/DA + bloggen, Page Profile EN/DA, e-bogpakken, Report Kit på tre sider, EUComply Pro og donationen på `/support`.
- **Falske tilbud fjernet:** `compliance-report.html` havde to opfundne trin ($29/report, $99/år, "Available when store launches") — erstattet af de to produkter der faktisk sælges, Report Kit $69 og EUComply Pro $79/år pr. website. `scan.html`/`scan-da.html` solgte en $29-rapport "når butikken åbner" — peger nu på Report Kit. `site-icons.html` (Pro $29, "Available soon") og `downloads.html` (EAA-scanner Pro $19/år) og `blog/eaa-compliance-scanner-desktop.html` ("Pro is coming") siger nu, at der ikke findes en Pro-licens og ingen pris. `site/index.html` + `site/da/index.html` er renset for "paid checkout is not wired up".
- Alle 12 Payment Links + donationslinket gav HTTP 200 ved read-only GET 2026-09-25.
- **Kontraktens rankingdel er ikke implementeret endnu** (se næste iteration): `tools/weekly_report.py` har ingen `ranking_basis`, så intet i konverteringsarbejdet er endnu rangeret på data.

**Del 2 — implementeret i `ceo/ranking-basis`:**

- `tools/weekly_report.py` rangerer nu de sælgende sider på **de seneste syv fulde dage** (`ranking_period()` = `[i dag-7, i dag-1]`). Dagens time er ikke et fuldt døgn og tæller aldrig med; API'et hentes derfor med `days=8`, fordi dets `days` tæller i dag med.
- `ranking.basis` er kun `traffic`, når *alt* holder: inventaret kan læses, alle fire domæner har et verificeret grundlag i perioden, hvert rangeret domæne har mindst 5 pageviews, og perioden har mindst 30 i alt. Ellers er den `unknown` med en konkret `basis_reason`, tomme ranked-lister og den dokumenterede fallback.
- Fallbacken er de fire centrale produktsider (Clean Copy, DeskUptime, Page Profile, EUComply) hver med et `why`, plus inventaret af alle 14 synlige købsruter med produkt og pris. Begge dele er mærket `is_traffic_ranking: false` og gengives i rapporten som *ikke* en mest-besøgte-rangering. Kan inventaret ikke læses, er fallbacken `null` — altså en fejl, ikke et tomt resultat.
- `tools/stripe_catalog.json` har nu `domain` + `route` pr. købsside (15 sider) og `core_pages` med de fire centrale produktsider. `tools/check_stripe_ctas.py` fejler ved ukendt domæne, ugyldig route, en route der ikke findes i `dist/`, for få centrale sider eller en central side der ikke sælger sit produkt; selftesten fanger nu 7/7 fejlformer.
- Rapporten får to nye sektioner: `Konverteringsrangering — seneste 7 fulde dage (…)` med eksplicit `ranking_basis:` i noten, og `Synlige Pro-tilbud (inventar, ikke rangering)` når fallbacken bruges. `collect_all()` løfter `ranking_basis` til rapportens øverste niveau, så den kan læses uden at grave i `traffic`.
- `tools/test_weekly_report.py` er vokset fra 15 til 28 tests. Nye dækning: perioden er syv fulde dage uden i dag, 500 besøg i dag kan hverken give rangering eller fortrænge perioden, 30/5-tærsklerne, domæne under tæsklen rangeres aldrig, et domæne uden datagrundlag blokerer hele rangeringen, manglende inventar gør rangeringen `unknown`, og rapporten viser fallbacken uden at hævde besøgstal.
- Den eksisterende assertion for `/api/stats`-URL'en blev opdateret fra `days=7` til `days=RANKING_FETCH_DAYS`, fordi rankingvinduet kræver den ekstra dag. Testens eget formål (bearer-token, intet token i URL'en) er bevaret, og ingen test er fjernet.

**Konklusion på rangeringen:** Ugerapport 2026-39 (den seneste) kan ikke give `ranking_basis: traffic`. Konverteringsarbejdet må derfor fortsætte på den dokumenterede fallback, ikke på påstande om mest-besøgte sider.

**Acceptkriterier:**

- Hver central Pro-side viser gratis og betalt uden overlapende eller modstridende claims.
- Hver købsbar side har præcis én tydelig CTA med et tilladt Stripe-link.
- Alle fundne Stripe-links giver HTTP 200 ved read-only GET, og produkttestdata matcher kun den tilladte mapping.
- Ingen side viser “coming soon”, placeholder-link eller “Pro is coming” oven på et allerede betalt produkt.
- Hvis perioden mangler data, har færre end 30 totale verificerede pageviews eller færre end 5 i et domæne, der rangeres, står `ranking_basis: unknown` sammen med den dokumenterede fallback; ingen egen trafik indgår.
- `python3 tools/check_stripe_ctas.py` er grøn og beviser, at `tools/stripe_catalog.json` matcher den tilladte kontrakt og alle brugte CTA'er.

**Gate:** `python3 tools/check_stripe_ctas.py && python3 tools/check_stripe_ctas.py --self-test && python3 tools/test_weekly_report.py` plus hele kvalitetsgaten.

### 4C. FÆRDIG (implementering 46a2c2f, merge 3fe72c3) — Send support og købersvar til de nye support-adresser

**Begrundelse:** Siden 2026-09-25 modtager alle produktdomæner mail (MX → Stalwart, catch-all → den fælles indbakke `support@mahope.tools`), som automations-serverens produktpuls læser og poster i #produkter. Sidernes kontaktlinks og leveringsmailens svar-adresse peger stadig på Mads' private indbakker, så kundehenvendelser bliver ikke sporet som produktfeedback.

**Omfang:**

- Erstat synlige `mailto:mads@mahope.dk`/`mailto:mads@mahoje.dk` på produktsiderne (bl.a. `site/privacy/`, `site/terms/`) med `support@<sidens domæne>` for cleancopy.tools, deskuptime.com og bugbottle.dev og `support@mahope.tools` for mahope.tools.
- Sæt `reply_to` i leveringsmailen (`site/_worker.js`, `Your ${r.product_name}`) til `support@<produktets domæne>` ud fra produktets `home` i produktkataloget, med `support@mahope.tools` som fallback. `from` forbliver `orders@mahoje.dk`, og salgsnotitsen til Mads ændres ikke.
- Ingen DNS-, Stalwart- eller Stripe-ændringer; adresserne findes allerede.

**Acceptkriterier:**

- `grep -rn "mailto:mads@" site/` giver ingen fund.
- En worker-test beviser, at leveringsmailen for `clean-copy-pro` har `reply_to: support@cleancopy.tools`, og at et produkt uden `home` falder tilbage til `support@mahope.tools`.
- Stripe-worker-testens antal tests falder ikke.

**Gate:** `! grep -rn "mads@mahope" site/ --exclude=_worker.js && node tests/stripe-worker.test.mjs` plus hele kvalitetsgaten.

**Implementeret denne iteration (merged i `3fe72c3`):**

- `supportAddress(productKey)` i `site/_worker.js` udleder `support@<hostname>` fra produktets `home` i `STRIPE_PRODUCTS` og validerer værtsnavnet; `support@mahope.tools` er fallback for produkter uden `home` (alle downloadprodukter og donationen) og for en `home`, der ikke kan parses. `sendSaleEmail` bruger den i stedet for den private `mads@mahope.dk`.
- Fire nye worker-assertions (57 → 62): Clean Copy Pro → `support@cleancopy.tools`, `eucomply-dpa` uden `home` → `support@mahope.tools`, ingen kundemail har en `reply_to` på en `mads@`-adresse, og begge nye sessioner leverer (200).
- `site/privacy/index.html`, `site/terms/index.html` (kontakt og refusion) og `site/license-lookup.html` (inkl. "write to me"-formuleringerne) peger på `support@mahope.tools`. Den generative kilde `tools/make_privacy_terms_479.py` er opdateret, så en regenerering ikke genindfører den private adresse.
- `build_sites.py` skriver `Contact: mailto:support@<sit domæne>` i `.well-known/security.txt`, så hvert dist peker på sin egen indbakke. `humans.txt` beholder den faktiske personoplysning om Mads.
- Salgsnotitsen til Mads (`to: ['mads@mahope.dk']`) og `BB_INBOX_TO` er urørt, som opgaven kræver.
- Read-only DNS er bekræftet umiddelbart før ændringen: `cleancopy.tools`, `deskuptime.com`, `mahope.tools`, `transmute.run`, `eucomplypro.com`, `bugbottle.dev` og `mahoje.dk` har alle MX → `mail.mahoje.dk`. En catch-all kan ikke verificeres read-only; hvis den ikke findes, bouncer svar på de nye adresser, og det skal meldes i `❓ Til Mads`.
- Bemærkning til omfanget: `site/privacy/`, `site/terms/` og `site/license-lookup.html` udgives kun på `mahope.tools` (de er ikke i nogen `include`-liste), så de får `support@mahope.tools`. De øvrige domæner får deres adresse gennem `security.txt` og leveringsmailen.

**Commit:** `3fe72c3` (implementering `46a2c2f`) — `Send kundehenvendelser til produkternes egne support-adresser`. Deployet og live-verificeret (`DEPLOY OK 3fe72c3`).

### 4D. FÆRDIG (implementering f16305f, merge aa8bf32) — Link til Stripe-kundeportalen for årsabonnenter

**Begrundelse:** Stripe-kundeportalen blev oprettet 2026-09-25 (standardkonfiguration: opsigelse ved periodens udløb, fakturahistorik, opdatering af betalingskort, adresse og momsnummer). Årsabonnenter på `clean-copy-pro`, `eucomply-pro` og `page-profile-pro` har i dag ingen vej til at opsige eller hente fakturaer selv. EU-forbrugerregler kræver et let opsigelsesflow.

**Omfang:**

- Vis linket `https://billing.stripe.com/p/login/6oU4gy76PgvgdBIdAXbMQ00` ("Manage subscription, invoices and VAT ID") på `/thanks` og i leveringsmailen, når produktet i kataloget er et abonnement (årligt). Engangskøb får ikke linket.
- Tilføj samme link på `/support` og i `site/terms/` under opsigelse.
- Ingen ændring i Stripe-konfigurationen.

**Acceptkriterier:**

- En worker-test beviser, at leveringsmailen for `clean-copy-pro` indeholder portal-linket, og at mailen for `deskuptime-pro` (engangskøb) ikke gør.
- `/thanks` viser linket for et abonnementsprodukt i den eksisterende mock-test.
- Stripe-worker-testens antal tests falder ikke.

**Gate:** `node tests/stripe-worker.test.mjs && python3 tools/check_stripe_ctas.py && python3 tools/check_stripe_ctas.py --self-test` plus hele kvalitetsgaten.

**Implementeret denne iteration:**

- `BILLING_PORTAL_URL` ligger i `site/_worker.js` og bruges kun, når katalogens produkt er markeret `subscription: true`. Leveringssvaret får da `subscription: true` + `billing_portal`, så `/thanks` og mailen kan vise linket; `ful:`-ledgeren bevarer begge felter, så en gentaget mail efter fejl stadig har dem.
- Leveringsmailen får en linje om opsigelse, fakturaer og momsnummer. Testen beviser at `deskuptime-pro` (engangskøb) og download-køb **ikke** får portalen, og at kun de tre årlige produkters mails gør det.
- `site/thanks.html` renderer portalen under nøgleboksen med egen blok; `site/support.html` får et kort om abonnementsstyring; `site/terms/index.html` får en sektion "Cancelling a subscription", og den generative kilde `tools/make_privacy_terms_479.py` er rettet med, så en regenerering ikke genindfører den gamle tekst.
- **Ærlighedsreparation:** terms sagde "Each purchase is a one-time payment ... there are no recurring charges", hvilket var forkert for tre produkter. Det er nu "Some products are sold as a one-time payment, others as a yearly subscription", og `there are no recurring charges` ligger i `FORBIDDEN_CLAIMS`, så gaten fejler hvis påstanden kommer tilbage.
- `tools/stripe_catalog.json` får `billing_portal` + `portal_pages` og `subscription: true` på de tre årlige produkter. `check_stripe_ctas.py` bruger katalogens portal-URL som den eneste tilladte, tillader den kun på de tre deklarerede sider og sammenligner workerens `subscription`-markeringer med allowlisten.
- Worker-testen går 62 → 69; ingen eksisterende assertion er fjernet. Selftesten går 7/7 → 10/10. Bemærkning fra testen: portal-URL'en har sti-segmenter (`/p/login/…`), så `LINK_PATTERN` måtte udvides til at tage `/`-segmenter — ellers ville den set `https://billing.stripe.com/p` og fejle på fire filer.

**Commit:** `f16305f` — `Giv abonnenter selvbetjent opsigelse via Stripe-kundeportalen`.

### 5. FÆRDIG (implementering 978f950) — Stop offentlig eksponering af betalt indhold

**Begrundelse:** Betalte kilder og artefakter ligger allerede i det offentlige repo, selv om missionen kræver private filer og kun offentlig open-core-kode.

**Omfang:**

- Inventér hvert betalt produkt, kilde, builder, public downloadsti, filstørrelse, checksum, product key og forventet `paidfile:*`-nøgle.
- Tilføj `tools/check_private_content.py`, som fejler ved betalte kilder/artefakter i den offentlige git-tracked tree eller i offentligt buildoutput.
- Stop offentlig build/copy af betalte kilder og artefakter, men bevar open-core Pro-kode i repoet.
- Flyt kun betalt indhold til den private destination, Mads godkender, og erstat først de offentlige downloadstier når private leveringsfiler er dokumenteret.
- En eventuel git-historik-rewrite eller produktions-KV-upload er en separat handling og må ikke ske uden Mads' go.

**Blokeret delhandling:** Betalt indhold findes allerede i tidligere public commits. En fuld historik-remediering kræver en koordineret historik-rewrite, som er forbudt af denne kontrakt og desuden kræver Mads' go. Opgaven må derfor kun markeres `FÆRDIG` for stop af ny eksponering; historikken skal stå som eksplicit `BLOCKED: kræver Mads-godkendelse`, indtil der tages en beslutning.

**Acceptkriterier:**

- Der findes ingen betalte PDF/ZIP/Markdown-kilder ellerArtefakter i den offentlige git-tracked tree ved opgavens afslutning.
- Hvert betalt produkt har en reproducerbar buildkommando, checksum og sikker destination i et privat repo.
- Den offentlige Worker har kun licensadgang til private KV-filer; ingen downloadroute peger på offentlige filer.
- Read-only produktionsinventering eller en godkendt Mads-handling bekræfter hver forventet `paidfile:*`-nøgle.
- Hver commit beskriver præcist, hvilke filer der flyttes, og ingen historik-rewrite sker i samme commit.
- Historikken rapporteres fortsat som `BLOCKED: kræver Mads-godkendelse`; opgaven påstår ikke fuld sletning fra tidligere commits.

**Gate:** `python3 tools/check_private_content.py && python3 build_sites.py && python3 tools/seo_check.py` plus resten af kvalitetsgaten.

**Ekstern read-only-gate:** En Cloudflare-KV-inventering af forventede `paidfile:*`-nøgler skal gemmes read-only i planen af Mads eller en godkendt driftsti; ingen upload/sletning må ske i denne iteration.

**Resultat — faktatjek den 25. september:** Betalt indhold er **allerede** væk fra den
offentlige tree. `3eb1dac` ("Fjern betalt indhold fra products/") fjernede tolv filer,
og ingen af de seksten betalte leveringsfiler (`dpa-template.*`, `nis2-vendor-clauses.*`,
`nda-clause-set.*`, `eaa-statement-template.*`, `monthly-report-template.*`,
`quarterly-narrative-template.*`, `change-log-spec.*`, `compliance-bundle.pdf`,
`compliance-bundle-v1.0.zip`) findes i dag hverken i den git-tracked tree eller under
`dist/`. Handlekreditten fanger desuden kun KV. Det var altså alene holdningen, der
manglede, ikke lækagen — og holdningen er nu kodet ind.

**Implementeret denne iteration:**

- `tools/paid_content.json` er det maskinlæsbare inventar over alle syv downloadprodukter: product_key, navn, pris, de forventede `paidfile:*`-nøgler, det private kilderepo, `build_command`, `sha256` og `kv_verified`. Den er bevidst *ikke* en fuldstændighedsliste af filer, der findes: den er en aftale om, hvad der **aldrig må** ligge i det offentlige repo.
- `tools/check_private_content.py` fejler ved ti fejlformer: et betalt leveringsfil i den git-tracked tree, en fil fjernet i `3eb1dac` der er dukket op igen, et nyt arkiv under `products/`, et betalt fil i `dist/`, en offentlig side der linker direkte på det betalte fil, et worker-downloadprodukt uden inventar, en ændret fil-liste i workeren, en pris der ikke matcher `tools/stripe_catalog.json`, en historik der påstår at være remedieret, og en `/api/download` der ikke læser fra `paidfile:`-KV. Selftesten er grøn 10/10.
- Gaten er lagt ind i deploy-workflowens gate-trin **efter** buildet, fordi `dist/` først findes der, og `tools/paid_content.json` + gaten ligger i path-filteret, så en læk i enten fil udløser en rød gate frem for en deploy.
- `check_provenance` fejler, hvis nogen senere skriver historikken som remedieret. Det er derfor umuligt at få denne opgave til at påstå fuld sletning ved en senere redigering.

**Hvad der IKKE er gjort, og hvorfor:** Ingen fil blev flyttet i denne iteration, fordi
der ikke er noget betalt indhold i repoet at flytte, og fordi `mahope/paid-products`
ikke findes som lokal checkout. `build_command` og `sha256` står derfor som `null`, og
`kv_verified` er `false` for alle syv produkter. Det er ærligt, ikke løst: se `❓ Til Mads`
punkt 4 og 8.

**Konsekvens for salget:** Fordi ingen `paidfile:*`-nøgle er verificeret, vil en køber
af et af de syv downloadprodukter få HTTP 503 fra `/api/download` ("File temporarily
unavailable"). Det er ikke en regression — det er den nuværende tilstand — men det er
også et køb, der ikke leverer, og det skal løses **før** det første reelle salg på en
downloadvare. Reelle, dokumenterede salg i repoet: 0.

### 6. FÆRDIG (implementering ceo/page-profile-distribution) — Reparer Page Profile-købsflowet

**Begrundelse:** En kunde kan betale og få en gyldig 32-hex Stripe-nøgle, som den solgte CLI afviser.

**Omfang:**

- Skriv først mockbaserede fejltests for en 32-hex Stripe-nøgle.
- Ret den kanoniske kode i `page-profile/` og den publicerede kopi i `site/downloads/page-profile/`; tilføj `tools/check_page_profile_distribution.py`, så builden ikke kan publicere en divergerende kopi.
- Aktivér og valider nøglen online via `https://mahope.tools/api/license/activate` og `/validate` med `product: page-profile-pro` og et stabilt device-id.
- Accepter aldrig en 32-hex nøgle alene på format/checksum; kun et gyldigt serversvar må aktivere Pro.
- Cache kun en tidligere gyldig positiv status i højst syv dage ved netværksfejl eller `503`/5xx. Hård fejl ved `403`, `404` eller `409` må ikke bruge cachen.
- Ret offline-claims i `site/page-profile.html` og `site/da/page-profile.html`, så de beskriver den online Pro-aktivering korrekt.
- Test canonicalisering, enheds-ID, replay og stabil lokal status.

**Acceptkriterier:**

- En mocket gyldig 32-hex `page-profile-pro`-nøgle aktiverer Pro via API'et.
- Ukendt nøgle, forkert produkt, udløbet/tilbagekaldt nøgle og nået enhedsgrænse giver korrekt hard failure.
- En cached gyldig status overlever ét 5xx-svar, men hverken `403`, `404` eller `409`.
- Formatnøgler uden gyldigt serversvar giver ikke Pro-status.
- Den publicerede CLI-kopi er byte-for-byte/parity-kontrolleret mod den kanoniske kode, og EN/DA-siderne har ingen offline-Pro-claims.
- `python3 page-profile/test_page_profile.py` og `python3 tools/check_page_profile_distribution.py` er grønne.

**Gate:** `python3 tools/check_page_profile_distribution.py && python3 tools/check_page_profile_distribution.py --self-test && python3 page-profile/test_page_profile.py` plus hele kvalitetsgaten.

**Implementeret denne iteration:**

- Kernen i opgaven var allerede rettet af 4E (`ea4e6c3`): 32-hex Stripe-nøgler
  aktiverer Pro via licens-API'et, `--gen-key` og saltet er væk, og EN/DA-siderne
  fortæller sandt om online-aktivering og syvdages cache. Det, der manglede, var
  den anden halvdel af acceptkriterierne: `site/downloads/page-profile/` er en
  manuelt kopieret udgave af `page-profile/`, og intet holdt de to sammen.
- `tools/check_page_profile_distribution.py` sammenligner nu den kanoniske kode
  med alle tre publicerede steder og fejler ved nitten former: en manglende
  kanonisk fil; en version der ikke matcher mellem `pyproject.toml` og
  `__version__`; en publiceret kopi der mangler eller afviger; intet source-arkiv;
  flere arkiver i den publicerede mappe; et arkiv på en gammel udgave; en
  rodmappe der ikke følger den pakkede udgave; en kildefil i arkivet der afviger
  eller mangler; et arkiv der ikke kan læses; en landingsside der linker på et
  arkiv der ikke findes; en `cd`-mappe i vejledningen der ikke findes i arkivet;
  en version i et eksempel der ikke er koden; en offline-påstand om licensen; en
  side der mister online-aktiveringen; en dansk side der mister syvdages cache; en
  manglende landingsside; og drift i `dist/`.
- Selftesten er grøn **20/20** og læser det rigtige `page-profile-1.2.0.tar.gz`,
  så arkiv-fejlene er læst fra et arkiv og ikke håndlavet. Den fejler også, hvis
  den rigtige kopi ikke er grøn, så en gaten, der altid siger "ok", kan ikke
  passere.
- `dist/mahope.tools/downloads/page-profile/page_profile.py` er bygget og
  byte-identisk med den kanoniske kode, så dist-kontrollen er reelt grøn og ikke
  springet over.
- **Udgivelsesreglen er dokumenteret i gaten**, fordi den var uskrevet: ret
  `version` og `__version__`, kør `python3 -m build --sdist --outdir /tmp/pp
  page-profile`, kopier arkivet til `page-profile-<udgave>.tar.gz` (setuptools
  døber det med bindestreg, men download-linket bruger bindestreg), kopier
  `page_profile.py`, ret udgaven og `cd`-mappen på begge sider, slet det gamle
  arkiv, kør gaten. Reglen er i denne iteration reproduceret read-only: det nybyggede
  arkiv har præcis de samme medlemmer og indhold som den publicerede fil.
- Deploy-CI kører nu `check_page_profile_distribution.py` med selftest og
  `page-profile/test_page_profile.py` (11 offline tests, 0,1 s) i gate-trinet, og
  `page-profile/**` + `site/downloads/page-profile/**` ligger i path-filteret, så
  en divergerende kopi får rød gate frem for en deploy.

**Ikke gjort:** Der er ingen ny licenskode. Denne iteration tilføjer holdningen, der
skulle have været der med 4E. Den publicerede kopi, arkivet og dist er alle tre
allerede korrekte — de var bare ubevogtede.


### 7. FÆRDIG (del 1, del 2 pkt. 1/3/4 og pkt. 2) — Gør Clean Copy-pluginklienterne Stripe-kompatible

**Begrundelse:** Root- og Obsidian-plugin sender ikke `product`, selv om workeren afviser payloaden.

**Omfang:**

- Find alle shipped klienter, der kalder `/api/license`, herunder root/Obsidian-pluginterne og Clean Copy Chrome/Firefox-udvidelserne; send `product: clean-copy-pro` i hver klient.
- Implementér syvdages cachet Pro-status ved `503`/5xx i hver klient, så en licensserverfejl ikke låser kunden ude.
- Tilføj `tools/check_license_clients.py`, som fejler ved manglende product payload eller divergerende generated/publicerede klientkode.
- Skriv tests for success, `403`, `409` og `503` før implementeringen.

**Acceptkriterier:**

- Hver shipped licensklient sender valid product payload.
- Hver klient bevarer en cached gyldig status i højst syv dage over serverfejl.
- En udløbt eller tilbagekaldt licens giver en synlig, deterministisk fejl.
- `tools/check_license_clients.py` dækker alle fundne callers og offentlige dist-kopier.
- Hele kvalitetsgaten er grøn.

**Gate:** `node tools/test_license_clients.js && node obsidian-plugin/test.js && node test.js && node extension-clean-copy/tools/test_clean_copy.js && python3 tools/check_license_clients.py && python3 tools/check_license_clients.py --self-test` plus hele kvalitetsgaten.

**Del 1 — implementeret i `ceo/clean-copy-license-clients`:**

- `tools/clean_copy_license.js` er den kanoniske klientregel: `API_BASE = https://mahope.tools/api/license`, `PRODUCT = clean-copy-pro`, 32-hex nøgleformat og `decide(...)`, der svarer således: 200 med `activated`/`valid` er Pro; 503/5xx/status 0 giver Pro fra cache i højst 7 dage (præcis 7 dage er stadig Pro, 7 dage + 1 ms er ikke); 403, 404, 400, 409 og `valid: false` er aldrig Pro og overskriver altid en cache.
- Det gamle `hermes-passiv.pages.dev`-endepunkt er fjernet fra alle Clean Copy-klienter. Live-tjek 2026-09-25: den gamle host svarer stadig 200/405, men den er ikke et af de fire deployede Pages-projekter, og kontrakten peger på `mahope.tools`.
- Klienterne sender nu `product` i både activate og validate: `obsidian-plugin/main.js` (indlejret modul), `extension-clean-copy/options.js` og den byte-identiske Firefox-kopi.
- Udevidelsens offline-adfærd var ubegrænset (`showLicensed('', true)` ved ethvert netværkskast). Nu gemmes `proCheckedAt`, og samme syvdagesregel gælder; en 503 çldre end vinduet fjerner nøglen og siger det.
- `obsidian-plugin/main.js` får ny `licenseExchange` (et kastet request bliver status 0) og `applyLicenseDecision`, så pluginen bruger præcis samme regel som webværktøjet.
- `tools/test_license_clients.js` (57 checks) indlæser de shippede filer med `obsidian`-, `chrome`- og `document`-stubs og dækker success, 403, 404, 400, 409, 500, 503, status 0, cache i 1 dag / præcis 7 dage / 8 dage, at en hård svar altid sår cache, at en dårlig nøgleformat aldrig rammer netværket, og at de to udvidelsers `options.js`/`license.js` er byte-identiske med hinanden og med den kanoniske fil.
- Den gamle `test.js`-licenstest var theater: den genskrev requesten i testen og hævede sit eget mock. Den er erstattet af et kald til den rigtige suite.

**Del 2 — implementeret i `ceo/clean-copy-delivery` (punkt 1, 3 og 4):**

- `site/clean-copy-tool.html` indlejrer `tools/clean_copy_license.js` mellem to markører og kalder `decide()` for både den stille revalidering ved indlæsning og aktiveringen via formularen. Det kanoniske modul bruges dermed af alle fire shippede klienttyper.
- `tools/test_license_clients.js` indlæser siden i en `vm`-sandbox med `document`/`localStorage`/`fetch`-stubs og dækker: ingen nøgle → intet kald, 200 → produkt + device_id + tidsstempel, 503 i og over syvdagesvinduet, 403/404/409/`valid:false` over en frisk cache, kastet request som status 0, lokalt udløbet nøgle, samt aktivering med afvist format, 409 og 503. 103 checks i alt. Mutationstest bekræfter, at gaten faktisk fanger en fjernet cache og en hardkodet `checkedAt: 0`.
- `site/compliance-report.html` sender `product: eucomply-pro`. Siden sælger kun EUComply Pro, så det er den eneste licensnøgle den kan modtage.
- Rodens `main.js` og `core.js` er slettet; `test.js` er nu en tynd indgang til `obsidian-plugin/test.js` + `tools/test_license_clients.js`. Den teaterblok i `obsidian-plugin/test.js` der hævede sit eget mock mod `hermes-passiv.pages.dev` er væk.
- `tools/check_license_clients.py` (+ `--self-test`, 9/9) holder CLIENTS-listen, EXCEPTIONS og de indlejrede moduler i linje. Den døde vært flagges kun i et licenskald, fordi kildefilerne stadig har `hermes-passiv.pages.dev` i OG/canonical-tags, som `build_sites.py` skriver om til det rette domæne.

**Del 2 punkt 2 — implementeret i `ceo/clean-copy-archives`:**

- `tools/build_clean_copy_archives.py` bygger de tre publicerede arkiver fra `extension-clean-copy/`, `extension-clean-copy-firefox/` og `obsidian-plugin/`. Arkiverne er deterministiske: fast tidsstempel (1980-01-01), sorteret rækkefølge, `create_system = 0` og fast filtilladelse, så samme kilde giver præcis samme SHA-256 på enhver maskine. Det er forudsætningen for at gaten overhovedet kan kræve byte-identitet. Hvert arkiv får en `version.txt`, så en køber kan se udgaven inde i den udpakkede mappe.
- Nye patch-udgaver: Chrome/Firefox **1.5.3**, Obsidian **1.0.10** (`obsidian-plugin/versions.json` har nu både 1.0.9 og 1.0.10). Browserarkiverne fik samtidig den `license.js`, de aldrig havde haft — `options.html` indlæser den, så det gamle arkiv ville have givet en 404 i options-siden.
- De tre gamle arkiver (`clean-copy-v1.5.2.zip`, `clean-copy-firefox-v1.5.2.zip`, `clean-copy-obsidian-v1.0.9.zip`, samt den legacy `clean-copy-obsidian-v1.0.6.zip`) er slettet, ikke bare overskrevet: de indeholdt licenskode, der ringede til `hermes-passiv.pages.dev` og ikke sendte `product`, så ingen må kunne downloade dem. `site/extension-zips/clean-copy-v1.5.2.zip` er den samme fil i en anden mappe og er erstattet af 1.5.3.
- Links opdateret i `site/clean-copy.html`, `site/da/clean-copy.html`, `site/downloads.html`, `site/free-downloads.html`, `site/blog/install-obsidian-plugin-clean-copy.html`, `site/da/blog/installer-clean-copy-obsidian.html` og den generative DA-kilde `tools/make_blog_da_mirrors_461.py`. Begge Obsidian-guides siger nu ærligt hvad 1.0.10 er: samme funktioner som 1.0.9, men Pro-licensen aktiverer og validerer mod samme licensserver som browserudvidelserne, med syv dages cache ved en udfaldende server.
- `tools/check_clean_copy_distribution.py` (+ `--self-test`, 15/15) fejler ved ti fejlformer: et kilde-manifest uden version, en Obsidian-`versions.json` der ikke kender udgaven, et arkiv der mangler, et arkiv der afviger fra en regeneration, en forældet udgave der stadig ligger publiceret, en kildefil der mangler i arkivet, en kildefil der afviger fra kilden, en ekstra fil i arkivet, en død licensvært i et arkiv, et licenskald uden `product`, en død side-link, en side der viser en gammel udgave, en driftende `dist/`-kopi og en manglende `dist/`-kopi. Den læser de rigtige zips i selftesten — mutationerne er bygget fra den samme builder, som gaten selv bruger.
- Deploy-workflowen kører nu gaten med og uden selftest i gate-trinet, og `extension-clean-copy/`, `extension-clean-copy-firefox/`, `obsidian-plugin/`, `site/extension-zips/` og de to nye tools ligger i path-filteret, så en ny kildeudgave eller en håndredigeret zip får rød gate frem for en deploy.
- **Fund under arbejdet:** den nye gate blev selv fanget af `check_license_clients.py`, fordi den nævner den døde vært i en selftest-fixture. Det er holdet løst med to dokumenterede `NOT_CLIENTS`-poster — samme mekanisme som de øvrige gater og tests, og beviset at licensklient-scanneren stadig gælder for nye filer.

**Hvorfor del 2 gav mening:** de publicerede zips var den kode en køber rent faktisk hentede. Del 1 og 2 rettede kilden, og uden denne del rettelsen ville aldrig nå en kunde. `IMPLEMENTATION_PLAN.md` førte den gamle kode som *dokumenteret* i dist, fordi arkiverne lå i `site/downloads/` og blev kopieret ukritisk.

### 8. FÆRDIG (implementering `ceo/clean-copy-publish-targets`) — Bevis hvilket domæne der publicerer hvilket Clean Copy-arkiv

**Begrundelse, korrigeret 25. september:** Den oprindelige begrundelse var, at
`site/downloads.html` linkede rodrelativt på arkiver, der kun publiceres på
cleancopy.tools, så købsstien gav fire 404'er. **Live-verificeringen viser, at
den konklusion var forkert.** `build_sites.py` skriver alle rodrelative
referencer gennem `build_index()`/`rewrite_text()`, og fordi
`build_sites.py:74` giver `downloads/clean-copy*` til cleancopy.tools først,
omdøbes linket i *outputtet* til `https://cleancopy.tools/downloads/…`
(`build_sites.py:349-412`). Read-only mod live den 25. september:

| URL | HTTP |
|---|---|
| `mahope.tools/downloads` | 200 |
| live `/downloads`-sideens link til arkivet | `https://cleancopy.tools/downloads/clean-copy-v1.5.3.zip` |
| `cleancopy.tools/downloads/clean-copy-v1.5.3.zip` | 200 |
| `cleancopy.tools/downloads/clean-copy-firefox-v1.5.3.zip` | 200 |
| `cleancopy.tools/downloads/clean-copy-obsidian-v1.0.10.zip` | 200 |
| `mahope.tools/downloads/clean-copy-v1.5.3.zip` | 404 ← arkivet findes *kun* dér |

Den 404, der blev rapporteret, var altså et **probe mod det forkerte domæne**,
ikke et link en kunde kan ramme. Købsstien er grøn.

**Det reelle problem er, at intet beviser det.** To ting kunne gå galt uden at
nogen opdager det: (1) hvis `build_sites.py`s include-rækkefølge eller
`global_idx` ændres, så `downloads/clean-copy*` havner på mahope.tools, eller
tværtom; (2) hvis skrivningen af et rodrelativt link holdt op at virke, ville
`site/downloads.html` få `/downloads/clean-copy-v1.5.3.zip` tilbage — præcis
det link der gav 404 i den oprindelige rapport. Den eksisterende gate
(`tools/check_clean_copy_distribution.py`) tjekker kun *navnet* på arkivet
(`check_pages`, linje 238-253), aldrig domænet, så ingen af de to fejl
opdages. Det er samme blindspalt som opgave 7 del 2 rettede for kildekoden.

**Omfang:**

- Udvid `tools/check_clean_copy_distribution.py` med `check_publish_targets`, som
  læser **det byggede output** i `dist/` og fejler ved:
  - en rodrelativ reference til et Clean Copy-arkiv på en side, hvis domæne ikke
    publicerer det arkiv;
  - en absolut reference til et af vores domæner, der ikke publicerer arkivet;
  - et publiceret arkiv, der ikke publiceres på noget domæne (når `dist/` er
    bygget), altså en død downloadsti i hele familien.
- Gaten skal selv finde ud af hvilket domæne der publicerer hvad — ingen
  hardcoded filliste, der kan blive ligeså forkert som det link den skulle
  fange.
- Springes over, når intet er bygget, i samme mønster som den eksisterende
  `check_dist`.
- Dæk hver fejlform af selftesten.

**Acceptkriterier:**

- Gaten fejler ved en rodrelativ reference til et Clean Copy-arkiv på en side, der
  ligger på et domæne uden arkivet (dækket af selftesten).
- Gaten fejler ved en absolut reference til et af vores domæner uden arkivet.
- Gaten fejler, når et publiceret arkiv ikke findes i nogen dist.
- Gaten fejler ikke ved en rodrelativ reference på cleancopy.tools selv, hvor
  arkivet ligger (positiv kontrol i selftesten).
- Den rigtige kode fejler ikke, og `dist/mahope.tools/downloads.html` +
  `dist/mahope.tools/free-downloads.html` indeholder `https://cleancopy.tools/downloads/…`.
- Hele kvalitetsgaten er grøn.

**Gate:** `python3 tools/check_clean_copy_distribution.py && python3 tools/check_clean_copy_distribution.py --self-test` plus hele kvalitetsgaten.

**Post-merge-gate:** `curl -s -o /dev/null -w '%{http_code}' https://cleancopy.tools/downloads/clean-copy-v1.5.3.zip` skal være 200, og live `mahope.tools/downloads` skal linke på `cleancopy.tools` — ikke på sig selv.

**Implementeret denne iteration:**

- `check_publish_targets` læser hver bygget side i `dist/<domæne>/` der nævner et arkiv, og slår hvert `href`/`src` op: rodrelative links arver sidens eget domæne, `https://`-links bruger værten, og et tredjepartsdomæne (fx en GitHub-release) springes over, fordi det ikke er denne gats at dømme. Fejl gives med både domæne og filnavn, så en fejlmeddelelse alene peger på den konkrete købssti.
- `check_every_archive_is_reachable` kræver, at hvert publiceret arkiv kan hentes i mindst én dist, når der overhovedet er bygget. Det er den fejl, der ville slå *alle* downloads ihjel — fx hvis `build_sites.py:74`s include-globs slap arkiverne på ingen af domænerne.
- `_split_href` er delt, så rodrelativ, absolut, protokol-relative og dokumentrelative links gennemgås af samme logik. `ARCHIVE_RE` er nu én fælles konstant for kilde- og outputscanning, så de to ikke kan komme i drift.
- **Ubygget domæne giver hverken bekræftelse eller afkræftelse.** Deploy-workflowen bygger ét domæne pr. matrix-job, så `dist_publishes` medtager kun domæner hvis dist findes. Uden den regel rapporterede gaten de absolutte links fra mahope.tools som 404 i et job, der ikke bygger cleancopy.tools — en rød gate på en ordning der er i orden. Se `CI-FEJL RETTET` i statusblokken.
- **Nyt workflow-job `gate-distribution`** bygger alle fire dists og kører begge checks; `deploy` har `needs: gate-distribution`. Tolerancen må ikke blive en lomme, hvor checket aldrig kører: matrix-jobbet alene ville springe den krydsdomæne-reference over, der er hele formålet. Tolerancen og jobbet hører sammen.
- **Selftesten blev strammere, ikke bare større.** Scenarier mærket "skal ikke fejle" blev hidtilkun ignoreret, hvis de fejlede — de kunne altså ikke bruges som bevis. Nu giver en sådan kontrol exit 1 og tælles ikke med i fangne fejlformer, så en gaten der affyger alle vegne ikke kan bestå.
- Deploy-workflowen behøver derfor en ny gate: `tools/check_clean_copy_distribution.py` lå allerede i path-filteret fra opgave 7 del 2, men matrix-jobbet bygger kun ét domæn, så de to nye checks kræver et job, der bygger alle fire. Det er tilføjet som `gate-distribution`. `dist/` er uændret af denne iteration (git bekræfter det), så der er intet nyt site-indhold at udgive.

**Hvorfor opgaven ikke blev implementeret som skrevet:** den specificerede løsning var at skrive de tre links absolutte i `site/downloads.html`. Det ville have vædet det samme resultat to steder — buildet skriver dem alligevel absolutte — og ville blot have gjort kilden mindre læselig og fjernet buildens ansvar for domænet. Det dybere problem, at ingen vidste hvilket domæne der publicerer hvad, stod stadig. Derfor blev rettet det, der manglede.

### 9. FÆRDIG (`ceo/electron-builder-26`) — Opgrader electron-builder og fjern advisory-fund

**Begrundelse:** En aktuel OSV-scanning fandt 15 kendte advisory-fund i desktop-buildværktøjet. Sikkerhedshallere skal eftergives de fire prioriterede missionstasks.

**Omfang:**

- Opgradér kun `electron-builder` 25.x til den testede 26.15.x-linje i denne commit.
- Lad den patchede builder trække patched `app-builder-lib`, `builder-util-runtime`, `js-yaml` og `tar`.
- Læs migrationsnoter og opdatér buildkonfiguration kun hvis de kræver det.

**Acceptkriterier:**

- `npm ci` virker fra den nye lockfil.
- `npm audit --audit-level=high` har ingen high/critical advisory-fund.
- Lokal macOS build og CI-b builds for macOS, Linux og Windows producerer alle forventede artefakter.
- Hele kvalitetsgaten er grøn.
- Opgraderingen og eventuelle kodeændringer står i denne plan.

**Gate:** `npm ci && npm audit --audit-level=high && npm run build:mac` i `desktop/`, derefter platform-CI, plus hele kvalitetsgaten.

**Post-merge-gate:** `gh run watch <run-id> --exit-status` skal være grøn for macOS x64/arm64, Linux og Windows; en rød post-merge-gate reverteres straks i en ny commit.

**Post-merge-gate KØRTE IKKE — se `CI-FEJL` i statusblokken.** Den lokale halvdel er grøn (dmg + zip for x64 og arm64 bygget af electron-builder 26.15.3), men matrixen for Linux og Windows sprang helt over, fordi `build-desktop.yml` ikke udløses af et push til `main`. Det er en **ældre fejl, ikke en følge af denne opgradering** — se opgave 16.

**Implementeret denne iteration:**

- `desktop/package.json`: `electron-builder` `^25.0.0` → `^26.15.3`. Det er den *eneste* kodeændring. `electron` er bevidst urørt på `^44.0.0` — den er opgave 12, og kontrakten siger én major-opgradering pr. commit, så den kan rulles tilbage præcist.
- `desktop/package-lock.json` regenereret. Den faldt 3427 ændrede linjer (netto ca. −1300), altså et mindre afhængighedstræ.
- `npm install` ville samtidig have omformatteret `mac.target`-arrayerne i `package.json` (én linje → 14, plus tilføjet newline ved EOF). Det blev kasseret og linjen rettet manuelt, så diffen i `package.json` er præcis én linje. Diff-rauschi i en sikkerhedscommit gør den sværere at gennemgå.
- **Optællingen var forældet:** opgaven sagde 15 fund, `npm audit` sagde 13 (12 high, 1 critical). Én rodårsag: `tar <=7.5.20` (11 fund) via `app-builder-lib`/`builder-util-runtime`, som igen deles med `cacache` → `make-fetch-happen` → `node-gyp`. Efter opgraderingen: `found 0 vulnerabilities`.
- **Ingen konfigurationsændring var nødvendig.** Opgaven sagde "læs migrationsnoterne og opgradér buildkonfiguration kun hvis de kræver det" — det viste sig ikke at være tilfældet, og det er ikke antaget: dmg + zip for x64 og arm64 blev bygget af den uændrede `build`-sektion med electron-builder 26.15.3.
- Lokalt bygget: `EAA Compliance Scanner-1.3.3-mac-{x64,arm64}.{dmg,zip}`, alle fire ~127-131 MB, med `CSC_IDENTITY_AUTO_DISCOVERY=false` (ingen signeringsidentitet er konfigureret lokalt; CI har samme adfærd, så intet i diffet afhænger af det).
- **Ikke verificeret lokalt: Linux og Windows.** De kræver hhv. en Linux-container og en Windows-vært, og de ligger i CI-matrixen i `.github/workflows/build-desktop.yml`, som kører på ethvert push til `desktop/**` — altså også på denne branch. Det er opgavens egen post-merge-gate.
- `dist/` er uændret af denne iteration (`git status` viser ingen dist-ændring), så intet site-indhold er berørt. Deploy-workflowens path-filter rører `desktop/` ikke, så merge til `main` deployer ingen sites for denne commits skyld.

### 16. FÆRDIG (implementering `6d95958`, rettelse `7ccfd43`) — Få `build-desktop.yml` til at køre igen på `main`

**Begrundelse:** Opgave 9s post-merge-gate afdøde den 25. september, fordi
desktop-CI'en ikke har kørt siden 25. august. Bevist, ikke formodet:

- `build-desktop.yml` er `state=active`, så workflowen er ikke deaktiveret.
- Sidste kørsel: run `32876161399` (tag `eaa-scanner-desktop-v1.3.3`).
- `cde9a96` (24. september 23:45) ændrede `desktop/LICENSE.txt`, som matcher
  `desktop/**` — og udløste ingen kørsel.
- `9ed7af6` (denne iterations merge) ændrede `desktop/package.json` og
  `desktop/package-lock.json` — og udløste heller ingen kørsel.

**Rodårsag:** `6766501` "fix CI: tag-only trigger (avoid SHA dedup loss of tag
event)" fra 25. august kl. **19:08:41 +0200 = 17:08:41 UTC**. Den seneste
`main`-kørsel, `32875977126`, startede **17:07:01 UTC** — 100 sekunder *før*
ændringen. Den efterfølgende tag-kørsel kl. 17:08:54 UTC brugte den nye
workflow og var grøn, fordi et tag matcher `tags`-filteret. Committen har altså
gjort workflowen **tag-only**: med `on.push.tags` sat ved siden af
`on.push.paths` udløser den ikke længere et push til en branch. Siden da er
ethvert `main`-push der rørte `desktop/` sprunget over i en måned.

**Hvorfor det er vigtigere end det ser ud:** opgave 9, 12 og enhver fremtidig
desktop- eller Electron-ændring har brugt denne matrix som sin eneste
platformdækning. Uden den er der ingen Linux- og Windows-verificering overhovedet,
og en opgradering der kun virker på macOS vil passere gaten grøn. Det er præcis
den klasse fejl kontrakten forbyder: en opgradering der ikke er Testet, før den
lives.

**Omfang:**

- Ret `on.push` så branch-push med `paths`-match igen udløser kørsel, uden at
  tag-udløsningen går tabt.
- Bevis rettelsen med et faktisk push, ikke ved at læse YAML'en.
- Overvej samtidig at fjerne `permissions: contents: write` fra ikke-release-
  jobbene; kun `release`-jobbet har brug for skriveadgang.

**Acceptkriterier:**

- Et push til `main` der rører `desktop/**` starter `build-macos` (x64 og
  arm64), `build-linux` og `build-windows`.
- Et push til `main` der *ikke* rører `desktop/**` starter ingen kørsel.
- Et tag `eaa-scanner-desktop-v*` starter stadig alle fire jobs *og* `release`.
- macOS x64/arm64, Linux og Windows er alle grønne med electron-builder 26.15.3 —
  det er den manglende halvdel af opgave 9s post-merge-gate.
- Hele kvalitetsgaten er grøn.

**Gate:** `python3 tools/test_deploy_workflow.py` (udvid med build-desktop-
triggerne) plus hele kvalitetsgaten.

**Post-merge-gate:** `gh run watch` på den kørsel, pushet udløser, skal være grøn
for alle tre platforme. Det er den samme kørsel, der beviser opgave 9.

**Resultat:** Opgaver 1-3 er verificeret i rigtige kørsler, ikke ved læsning af
YAML.

- Push til `main` der rører `desktop/**` starter matrixen: `36180893396` kørte
  `build-macos` (x64 og arm64), `build-linux` og `build-windows` — alle grønne
  med electron-builder 26.15.3. Det her er opgave 9s manglende post-merge-gate:
  linux- og windows-byggene er verificeret for første gang siden 25. august.
- Push til `main` der ikke rører `desktop/**` starter intet: gaten simulerer
  `site/index.html` + denne plan mod path-filteret og forventer intet match.
- Tag `eaa-scanner-desktop-v*` starter alle fire jobs *og* `release`: samme
  simulator, og `release` har `needs` på alle tre byggejobs. **`release` er
  ikke kørt endnu** — det kræver et rigtigt tag, og det er Mads' opgave. Den
  næste udgivelse er derfor utestet indtil den faktisk kører, og det er sagt
  her frem for at påstå, at tag-stien er bevist.
- Hele kvalitetsgaten er grøn.

**To fund undervejs, begge ægte fejl i min egen løsning:**

1. **Listeform for `on.push` er ugyldig.** Min første antagelse var, at `branches`
   og `tags` ikke kan stå i samme mapping, så de skulle være to elementer i en
   liste. Kørsel `36180365427` viste at workflowen så startede, men alle jobs
   faldt i 0 sekunder: GitHs schema kræver en mapping. Gaten afviser nu en
   liste under `on.push`, så det ikke kan ske igen uopdaget.
2. **PyYAML findes ikke i CI.** Den nye gate blev lagt ind i deploy-jobbene og
   dræbte alle tre på `ModuleNotFoundError: No module named 'yaml'`, fordi
   `deploy-sites.yml` bruger `setup-python` uden installationer. Rettelsen er
   `tools/mini_yaml.py` frem for `pip install` i en deploy-sti: en gate må ikke
   afhænge af en pakke ingen workflow installerer.

**Sidefund, ikke rettet her:** `tools/build_obsidian_bundle.js` fejler med
`bundle: require("./core.js") not found — main.js changed?`. Den er død
engangsstøtte, der ikke kaldes fra nogen workflow eller gate, altså ingen
regression. Lagt under opgave 15 (døde stier).

### 10. FÆRDIG — Gør de 18 broken references til en hard gate

**Begrundelse:** Nuværende build tæller 18 fejl men deployer, og missionen forbyder døde links, downloads og formularer.

**Omfang:**

- Ret kun reelle interne links og manglende assets i source.
- Erstat regex-baseret referencekontrol med en parser, der ignorerer kodeeksempler i `pre/code`.
- Lad build og CI fejle ved reelle uopklarede references.

**Acceptkriterier:**

- `dist/build-summary.json` har `broken: 0` for alle fire sites. **Opfyldt** — 0/0/0/0.
- `python3 tools/check_links.py` og build/CI returnerer non-zero ved en syntetisk broken reference. **Opfyldt og beviset begge veje**: mutation i `site/guides.html` → build exit 1; mutation i `dist/cleancopy.tools/clean-copy.html` → `check_links.py` exit 1 med fil og linje. CI kører begge kommandoer i `gate`-jobbet over alle fire dists (opgave 11 flyttede dem fra matrix-jobbets `--only <domæne>` til den fulde kontrol ét sted; se opgave 11).
- Hvert downloadlink og hver kritisk formular har mindst én repræsentativ smoke test. **Opfyldt som afledt dækning, ikke som liste**: `check_links.py` kræver at *alle* download-artefakter i det byggede dist kan hentes, og at enhver formular med en `action` uden worker-marker peger på en rute, der findes. En hardkodet liste af "vigtige" links ville være præcis den fejlform porten skal fange, nedskrevet som data — samme læring som opgave 8.
- Hele kvalitetsgaten er grøn. **Opfyldt.**

**Gate:** `python3 build_sites.py && python3 tools/check_links.py && python3 tools/check_links.py --self-test` plus resten af kvalitetsgaten.

**Rækkevidde ændret undervejs, og hvorfor:** opgaven sagde "18". Det viste sig at være ni reelle fejl plus ni falske positiver, hvoraf to kodeeksempler. De to eksempler *kunne* ikke rettes uden at ødelægge en korrekt, pædagogisk kodeblok — så de blev fjernet fra *regningen*, ikke fra siden. Til gengæld fandt porten fire ekstra fejl, som ikke stod på de 18: manglende DeskUptime-assets, et uomskrevet 404-nav, `{URL}`-placeholders på to publicerede artikler og en falsk versionspåstand på downloadsiden.

### 11. FÆRDIG (implementering `ceo/ci-runs-real-gate`) — Få CI til at køre den faktiske kvalitetsgate

**Begrundelse:** Workflowen kører kun build og SEO-check; den betalingskritiske Worker-test og inline-JS-test mangler.

**Omfang:**

- Kør præcis den dokumenterede kvalitetsgate før deploy.
- Medtag alle buildinputs i path-filteret, især `tools/brand.py`, `tools/pagepass.py` og `tools/seo_check.py`.
- Pin `auditedwp` til en godkendt commit-SHA.
- Lad ikke de fire matrixjobs fortsætte efter en fælles gatefejl.

**Acceptkriterier:**

- CI fejler, hvis Stripe-worker-testen eller inline-JS-testen fejler. **Opfyldt og nu *enforet***: gaten kører i ét job over alle fire dists, og alle tre deploys har `needs: gate`. Stripe-worker-testen og inline-JS-testen kørte begge allerede, men kun i matrix-jobbet og uden at en fælles fejl stoppede de andre domæner.
- En ændring i et buildinput udløser workflowen. **Opfyldt, og hævet fra 4 til 19 konkrete filer**: `tools/quality_gate.py --inputs` er den afledte liste over alt hvad gaten læser, og `test_deploy_workflow.py` fejler på alt i den, der ikke matcher filteret. To af dem lå ikke i filteret (`docs/stripe-kontrakt.md`, `tools/make_blog_da_mirrors_461.py`), og `build-desktop.yml` lå uden for, selv om det er det eneste sted gaten overhovedet køres.
- Den pinnede `auditedwp`-revision står i planen. **Opfyldt og håndhævet**: `5e244dcff242352cd5be31a55ca5f7d260f7e520` i begge jobs, og porten fejler på et flyt tag og på at de to jobs bruger hver sin revision.
- `python3 tools/test_deploy_workflow.py` beviser gatekommandoer, path-triggere og fail-fast-adfærd. **Opfyldt**: `check_gate` har seks checks, og selftesten har otte nye mutationer (gaten væk, deploy uden `needs`, dobbeltliste, `docs/` væk, `products/**` væk, flydende ref, divergerende ref, spøgelses-matrix). To af dem fangede en fejl i min egen kode, først og fremmest `_is_deploy_job`.
- Hele kvalitetsgaten er grøn. **Opfyldt**: `python3 tools/quality_gate.py` → 26 steps grønne på 2 min.

**Gate:** `python3 tools/quality_gate.py` (byg + alle checks) og `python3 tools/quality_gate.py --self-test`-delen heraf.

**Pinnet `auditedwp`:** `5e244dcff242352cd5be31a55ca5f7d260f7e520` — både i `gate` og i `deploy`, kontrolleret af porten. Det er en `mahope/auditedwp`-commit, og bygget læser den via `AUDITEDWP_DIR`; en ny pin kræver en bevidst commit, fordi porten afviser alt der ikke er 40 hex-tegn.

**Ændret omfang, og hvorfor:** opgaven sagde "kør gaten før deploy" og fire underpunkter. Den konkrete fejl var større end formuleret: tre dokumenterede checks kørte aldrig i CI, to manglede deres selftest, og licensklienternes 103 checks kørte aldrig. Derfor blev løsningen ikke "tilføj kommandoer til matrix-jobbet" — det ville have været den fjerde liste — men én ejer for hele listen. Konsekvensen er at matrix-jobbet nu kun bygger, deployer og tjekker live; de 15 duplikerede checks pr. domæne er væk, og de kører én gang over alle fire dists i stedet, hvilket også er det eneste sted `check_clean_copy_distribution.py` og `check_links.py` kan se alle dists på én gang.

### 12. FÆRDIG (`ceo/desktop-node-runtime`) — Deklarér runtime og opgradér Electron-patchlinjen

**Begrundelse:** Desktop kræver Node `>=22.12.0`, men manifestet og repoet erklærer det ikke.

**Omfang:**

- Opgradér Electron 44.0.0 til den aktuelle patched 44.x-version i en separat commit.
- Tilføj `engines.node` og `.nvmrc` i samme commit.
- Ret stale lock-root-version, hvis den følger produktmanifestet.

**Fund undervejs:**

1. **Lock-roden afviger ikke** — den siger 1.3.3, som er produktmanifestets version, så
   "ret stale lock-root-version" er ikke en fejl her. Den afvigelse, der står i
   researchfundene, er en anden (product.version 1.3.3 mod publicerede etiketter) og
   hører til opgave 14/18. *Ikke rettet, fordi der ikke var noget at rette.*
2. **De tre tal kunne ikke ses fra hinanden.** `node-version: '22'` stod i alle tre
   build-jobs, `engines` manglede, og `.nvmrc` fandtes ikke. Løsningen er derfor ikke
   "skriv de tre tal" men **én fil** — `desktop/.nvmrc` på `22.23.2`, læst af alle tre
   jobs med `node-version-file`. `check_desktop_runtime` fejler på en hårdkodet
   `node-version`, så den anden liste kan ikke genopstå.
3. **CI's `node-version: '22'` var heller ikke en fejl i sig selv** — setup-node løser
   `22` til nyeste 22.x, som overstiger kravet. Men den *sagde intet* om
   minimumskravet, og den ville have fortsat, hvis Electron engang krævede Node 24
   og en opgradering så lagde den ved siden af. Derfor `.nvmrc` og ikke en streng i
   workflowen.

**Acceptkriterier:**

- `engines.node` og `.nvmrc` peger på en understøttet Node-version. **Opfyldt**:
  `engines.node: ">=22.12.0"` (Electron 44.4.5s eget krav) og `desktop/.nvmrc` =
  `22.23.2`, og `check_desktop_runtime` fejler hvis de to glide fra hinanden.
- `npm ci`, audit og alle desktop-builds er grønne. **Opfyldt lokalt for macOS**: fire nye artefakter (dmg+zip for x64 og arm64) bygget med electron 44.4.5, `npm audit --audit-level=high` = 0 fund. Linux og Windows kan kun bygges i CI, som er post-merge-gaten. **Signeringen er ikke verificeret lokalt** — se fund 4.
- Hele kvalitetsgaten er grøn. **Opfyldt**: `python3 tools/quality_gate.py` → 26 steps grønne.
- Versionsændringen står i planen. **Opfyldt**: 44.0.0 → 44.4.5, og både `engines.node` og `.nvmrc` er anført ovenfor.

**Gate:** `npm ci && npm audit --audit-level=high && npm run build:mac` i `desktop/`, derefter platform-CI, plus hele kvalitetsgaten.

**Post-merge-gate:** `gh run watch <run-id> --exit-status` skal være grøn for macOS x64/arm64, Linux og Windows; en rød post-merge-gate reverteres straks i en ny commit.

### 13. FÆRDIG (`ceo/python-build-lock`) — Lå Python-buildmiljøet og reparer site-icons

**Begrundelse:** Fire siteværktøjer bruger tredjepartspakker uden samlet lock, og Site Icons har ugyldig PEP 621-metadata.

**Omfang:**

- Opret et låst, auditérbart Python-miljø til site-, ebook-, bundle-, cover- og screenshotværktøjer.
- Ret `site-icons/pyproject.toml` til gyldig `[project]`-metadata.
- Byg og test Site Icons fra en ren installation.

**Acceptkriterier:**

- En ren installation installerer de deklarerede buildafhængigheder. **OPFYLDT** — ren venv på 3.13, `--require-hashes` på alle 17 pins, exit 0.
- `pip-audit` har ingen kendte high/critical-fund eller har en dokumenteret, begrundet undtagelse. **OPFYLDT** — "No known vulnerabilities found" på 44 pins, efter Pillow 11.3.0 → 12.3.0.
- `pip install` fra Site Icons-sdist installerer Pillow og `site-icons --help` virker. **OPFYLDT** — `python3 -m build site-icons` bygger sdist + hjul, hjulet indeholder `site_icons.py`, `--force-reinstall` efterfulgt af `site-icons --help` virker.
- Hele kvalitetsgaten er grøn. **OPFYLDT** — 28 steps.

**Gate:** `python3 -m pip install --require-hashes -r requirements-build.txt && pip-audit -r requirements-build.txt && python3 -m build site-icons && python3 -m pip install --force-reinstall site-icons/dist/*.whl && site-icons --help` plus hele kvalitetsgaten.

**Resultat:** se `RESULT` (opgave 13) i statusblokken. Kort: `.python-version` på 3.13, to hash-tjekkede låsefiler genereret af `tools/lock_python_env.py` (kun topniveau vælges i repoet), `tools/check_python_env.py` som port med 13 mutationer, og to nye steps i `tools/quality_gate.py` + syv nye mønstre i deploy-workflowens path-filter. `.gitignore` dækker nu `site-icons/dist/` og `site-icons/build/`.

### 14. FÆRDIG (`ceo/version-source-of-truth`) — Ret dokumentation, privacy og versiondrift

**Begrundelse:** `STATUS.md`, `DECISION.md`, `BUILD.md`, `BUDGET.md`, root-README og privacy beskriver delvist Lemon Squeezy, gamle produkter eller urigtige data claims.

**Omfang:**

- Opdatér `STATUS.md`, `BUILD.md`, `DECISION.md`, `RESEARCH.md`, `BUDGET.md` og root-README som historiske/factuelle dokumenter; fjern deres operative “næste iteration”-state.
- Ret privacyteksten, så den beskriver faktisk KV-, waitlist- og BugBottle-behandling uden at godkende nye datagrundlag.
- Etablér én versionskilde pr. produkt og fang afvigelser i `tools/check_versions.py`.

**Acceptkriterier:**

- Ingen aktuel status- eller public-facing-kontrakt dokumenterer Lemon Squeezy eller Gumroad som aktiv betaling.
- De seks dokumenter indeholder ingen konfliktende `ACTIVE_TASK`, `NEXT_TASK` eller blocker-state; kun denne plan har det.
- Privacy matcher de faktiske behandlinger.
- `python3 tools/check_versions.py` fejler på den nuværende drift mellem manifests, locks, source og publicerede artefakter.
- Hele kvalitetsgaten er grøn.

**Gate:** `python3 tools/check_versions.py` plus hele kvalitetsgaten.

### 15. FÆRDIG (`ceo/legacy-seo-paths`, implementering `ab17545`) — Fjern døde sitemap-generator- og deploystier

**Resultat:** `site/sitemap.xml` (tom urlset, aldrig læst) og `tools/build_obsidian_bundle.js` (død, ingen kalder den) er slettet. 21 generatorers sitemap-step er erstattet af en ærlig stop med beskeden om at `build_sites.py` ejer sitemapperne. `indexnow_ping.sh` looper de tre rigtige domæner. `tools/check_legacy_seo_paths.py` gater det hele og kører som step 31 + 32.

**Gate:** `python3 tools/check_legacy_seo_paths.py` plus hele kvalitetsgaten (32 steps).

### 19. FÆRDIG (`ceo/dead-host-shipped-files`) — de døde herter væk fra de filer, en kunde kan kopiere

**Resultat:** 33 forekomster af `hermes-passiv.pages.dev` i otte publicerede filer er rettet, `search-index.json`s `body` kører nu gennem `rewrite_text`, og `dist/index.js` er untracket. **Gaten:** `python3 tools/quality_gate.py` — GRØN, 32 steps; `legacy-seo-paths --self-test` 7 mutationer + positiv kontrol; Stripe-worker uændret 69/69, tracking-worker uændret 83/83.

**Fund 1 — opgaven undervurderede omfanget 3 gange, fordi den læste `site/` og ikke dist.** 300+ kildefiler har den døde vært i `canonical`/`og:url`, og builden omskriver dem alle — det er *ikke* fejl. Kun **to** filer i det byggede `dist/` havde den: `cleancopy.tools/search-index.json` og `dist/index.js`. At søge i `site/` giver det modsatte indtryk, fordi de 300 filer er korrekte. Det er derfor den nye check 6 læser dist.

**Fund 2 — den værste fejl var den, opgaven ikke nævnte: scannerens forudfyldte felt.** `site/compliance-site-check.html` + `/da/` (8 steder hver) havde den døde vært i (a) det synlige link `Try: hermes-passiv.pages.dev`, (b) **`urlInput.value = 'https://hermes-passiv.pages.dev'`** — scanneren *forudfyldte* dødt som det URL den scanner, og (c) `'Scanned: … · via hermes-passiv.pages.dev/compliance-site-check'`, som ender i den rapport brugeren eksporterer og deler. Det er 33 fund, ikke de 10 opgaven havde listet.

**Fund 3 — de ni READMEs og templates, planen aldrig nævnte, er de værste at ramme.** Gaten fandt dem i første kørsel: `api-readme.md` (`POST /api/clean-copy`), `page-profile-api-readme.md`, `api-compliance-scan-readme.md`, `downloads/cookie-consent-banner.js`, `eaa-scanner-README.md`, `site-icons/README.md` og tre GDPR-skabeloner. 22 `curl`/`npm install`/`fetch`-kommandoer, en kunde kopierer bogstaveligt. Hvert filnavn er publiceret i **præcis én** dist, så væerten er udregnet af builden (`cleancopy.tools` for `api-readme.md`, ellers `mahope.tools`) — ikke gættet. `openapi.yaml` er publiceret på cleancopy.tools, så dens `servers:` er `https://cleancopy.tools`; workeren ligger i alle tre dists, så begge paths virker derfra.

**Fund 4 — `search-index.json` havde den døde vært, fordi `body` aldrig kørte gennem `rewrite_text`.** Samme fejlform som `write_generated()` i opgave 10: to skriveveje, én omskrivning. Rettelsen er i `build_sites.py`, så *alle* snitte er dækket — ikke kun denne ene fil. `broken` holder 0 i alle fire dists, og `rewritten` steg 49→50 på cleancopy.tools, altså præcis den ene reelle omskrivning.

**Fund 5 — min egen dist-check var død, og det var sjette gang i dette repo.** Den brugte `SKIP_DIRS` til at springe filer over, og `SKIP_DIRS` indeholder `"dist"` — så check 6 sprang præcis over den mappe den skulle læse. Selftesten skrev sit scenarie i `dist/` og blev *også* sprunget over, så mutationen stod som fanget, fordi den netop var fanget. Rettet med `DIST_SKIP_DIRS = SKIP_DIRS - {"dist"}`; scenariet fanger den nu. Mit andet selftest-fejl var samme slags: jeg skrev et HTML-casenum som `.yml`, så det blev skrevet *mens* mutationsfilen stadig lå der.

**Bevis for porten:** de to nye checks er fundet på de rigtige filer *før* nogen blev rettet (9 fund i første kørsel), 7 mutationer fanges med navngiven grund, positiv kontrol grøn før og efter, og HTML med død vært i `canonical` giver **ikke** en falsk positiv — den fejlform, der skjulte `search-index.json`. `dist/` er rent for den døde vært i alle fire domæner.

**Sidefund 25. september 2026 (opgave 15):** den døde vært `hermes-passiv.pages.dev` står stadig i filer, der **er** publicerede eller som en kunde kopierer:

- `site/downloads/eaa-scan-github-action.yml:30,64` — `npm install --global https://hermes-passiv.pages.dev/downloads/mahope-eaa-scanner-1.2.0.tgz`. Det er en GitHub-Actions-skabelon i en `npm`-pakke: kører den, henter den en tarball der ikke findes. Linje 53 peger på `https://hermes-passiv.pages.dev/scan`.
- `site/openapi.yaml:10` — `url: https://hermes-passiv.pages.dev` i det serverede API-schema.
- `site/_worker.js` — syv steder (User-Agent-strenge 253/355/1498/1963, `HTTP-Referer` 708, og en AI-prompt 689) der fortæller scanneren hvilken site den besøger. Kun `HTTP-Referer` har reel betydning for en modtagende server.

**Omfang:**

- Sæt domænerne på de rigtige: scanneren ligger på `mahope.tools`, Page Profile på `mahope.tools`, Security Headers på `deskuptime.com`. Verificér hvilken dist der hvilket arkiv indeholder, med `tools/check_clean_copy_distribution.py`s `publishes`-logik som forlæg — ikke ved gæt.
- `site/_worker.js` kræver worker-tests for hver rørte sti (`tests/stripe-worker.test.mjs` og `tests/tracking-worker.test.mjs`), og de eksisterende testtal må ikke reduceres.
- Saml de ~100 generatorers `URL = f"https://hermes-passiv.pages.dev/…"`-konstanter i en note: en generator der køres i dag skriver en canonical- og `og:url`-reference til en død vært ind i et nyt blogindlæg.

**Acceptkriterier:**

- Ingen fil under `site/` der publiceres, peger på `hermes-passiv.pages.dev`.
- `npm install`-kommandoerne i GitHub-Actions-skabelonen henter et arkiv der faktisk findes på det domæne, det står i.
- Hele kvalitetsgaten er grøn, Stripe-worker uændret på 69/69.

**Gate:** `python3 tools/check_links.py` plus hele kvalitetsgaten.

### 17. FÆRDIG (`ceo/deskuptime-one-shell`) — ét designsystem på hele deskuptime.com

**Sidefund 25. september 2026 (opgave 10):** `../auditedwp/site/deskuptime/index.html`
er 29 395 bytes og bruger EUComply-skallen med `/assets/site.css` + `/assets/site.js`.
Dette repos `site/deskuptime/index.html` er 11 852 bytes, blev skrevet om i opgave 2
(ærlig licenstekst) og bruger **dette repos** skal. Resultatet er, at
`deskuptime.com/` og `deskuptime.com/tools/` er bygget af to forskellige designs
på samme domæne, og de tre værktøjssider bærer en header, footer og
tema-tokens, der ikke ligner resten af sitet. Opgave 10 har gjort værktøjerne
funktionsdygtige igen ved at levere de to assets, men ikke ensformet.

**Omfang:**

- Beslut, om de tre værktøjssider skal skales med auditedwp's skal eller med
  denne repos `style.css`/`shell.js`. Førstnævnte kræver at `site.css`/`site.js`
  mødes af `pagepass`, hvilket er en reel designopgave, ikke en tekstretning.
- Uden at ændre `../auditedwp` (read-only).

**Resultat:** Alle fire sider deler nu skrifttype (IBM Plex Sans), containerbredde
(1200px) og temafarver (DeskUptime-blå). Løsningen var at lade auditedwps
`/assets/site.css` rejse med de tre værktøjssider og trodse dens 27 tokens med en
bro i `site/style.css` — ikke at vælge en skal, fordi bygget allerede bruger vores
på alle fire sider (se `RESULT` fund 1). `../auditedwp` er urørt.

**Acceptkriterier:**

- `deskuptime.com/`, `/tools/`, `/bulk-url-checker/` og `/security-headers-checker/`
  deler samme skrifttype, containerbredde og temafarver. **Oprevet for skrifttype og
  containerbredde ved bygget; temafarverne ved de 27 broede tokens.**
- Ingen reference på deskuptime.com er død (`check_links.py --only deskuptime.com` grøn).
- Hele kvalitetsgaten er grøn.

**Gate:** `python3 tools/check_design_tokens.py` (+ `--self-test`) plus hele kvalitetsgaten.

**Porten `tools/check_design_tokens.py` (ny, 26/9)** fejler ved: (1) en bygget side
indlæser et lokalt stylesheet ud over `/style.css`, og hverken vores `:root` eller
sideens `html[data-product="…"]` dækker de tokens det erklærer — fordi vores skal
indlæses *sidst*, så en udækket token er det andet systems værdi, der når læseren;
(2) `/style.css` indlæses før det andet stylesheet, så broen ikke virker; (3) siden
mangler `data-product`, så porten ikke kan bevise hvilken identitet der gælder.
Den læser det **byggede** dist, `site/style.css` og `build_sites.py`, og springes
over når intet er bygget. Steps `design-tokens` og `design-tokens-selftest` i
`tools/quality_gate.py`; `site/style.css`, `site/**`, `build_sites.py` og
`tools/check_design_tokens.py` er nu i path-filteret.

### 18. FÆRDIG (implementering `f3148a5`, merge `14f0ee3`) — afgør om de publicerede scanner-arkiver er forsinkede

**Sidefund 25. september 2026 (opgave 10):** `site/downloads.html` mærkede
arkiverne som **1.3.0**, mens filerne på disk og `scanner/npm/eaa-scanner/package.json`
siger **1.2.0**. Opgave 10 rettede mærkaten til den version, der faktisk kan
hentes. Det åbner det ærlige spørgsmål: er det *arkiverne* der er forsinkede, så
kunderne henter gammel kode, eller er det *teksten* der var for forkert, så kunderne
aldrig har fået den version de blev lovet?

**Researchfund 26. september 2026 (inden der blev skrevet kode):** svaret er ja for
ét arkiv og nej for otte. `site/downloads/eaa-scanner-desktop-src-1.3.3.zip`
indeholder en `package-lock.json`, der siger `version 1.3.0` og
`electron-builder ^25.0.0`, og en `package.json` uden `engines`, mens
`desktop/package.json` siger 1.3.3, `^26.15.3` og `>=22.12.0`. Resten af
arkivet (`main.js`, `scanner-core.js`, `scanner.js`, `index.html`, `preload.js`,
`style.css`, `icon.png`, `LICENSE.txt`) er identisk med kilden. De otte andre
publicerede arkiver er byte-identiske med kilden, inklusive pip-hjulet,
sdist'en og npm-`tgz'en.

**Omfang:**

- Sammenlign `scanner/npm/eaa-scanner/` og `scanner/packaging/` med de arkiver,
  der ligger i `site/downloads/`, og fastslå hvilken version kilden faktisk er på.
- Hvis kilden er foran: byg arkiverne reproducerbart fra kilden, opdatér
  download-sidens etiketter, og gør det til en gate, så et arkiv ikke kan ligge
  under den version siden lover igen.

**Acceptkriterier:**

- Versionsnummeret i `site/downloads.html`, i `llms.txt` og i README matcher
  præcis det arkiv, der serveres.
- `python3 tools/check_versions.py` (opgave 14) dækker forholdet mellem
  arkivnavn, pakkeversion og download-side.
- Hele kvalitetsgaten er grøn.

**Gate:** `python3 tools/check_versions.py` plus hele kvalitetsgaten.

**Resultat:** Det var arkiverne, der var forsinkede — og kun ét af dem. Det er
nu rettet, og der er en gate derfor.

**Fund 1 — arkivet løj om sin egen udgave, og det var den billigste at rette.**
`eaa-scanner-desktop-src-1.3.3.zip` pakkede ud til 10 filer, hvoraf 8 var
byte-identiske med `desktop/`. De to der ikke var, var lige præcis de to der
skal være sandheden: `package-lock.json` sagde `version 1.3.0` og
`electron-builder ^25.0.0`, og `package.json` manglede `engines`. En kunde der
pakker arkivet ud og kører `npm ci` får derfor præcis den
electron-builder-advisory-remediering opgave 9 lavede i kilden — leveret uden om
kilden. `.nvmrc` (22.23.2) var heller ikke med, så kunden fik slet ingen
runtime-erklæring. Det nye arkiv har 11 filer, lockfilen siger 1.3.3 og
`^26.15.3`, og `engines` og `.nvmrc` er med.

**Fund 2 — ingen port i repoet havde nogensinde åbnet et arkiv.** Opgave 14s
`check_versions.py` læser produktets versionskilde, dens spejle, arkivfamiliens
*filnavne* og download-siden. Den læser ikke en eneste byte inde i
`site/downloads/*.zip`. Derfor var den grøn på et arkiv med en 1.3.0-lockfil under
et 1.3.3-navn. Det er ottende gang i dette repo at en regel, der så komplet ud,
viste sig at læse det forkerte sted — efter opgave 10, 13, 15 og 17. De tre
Clean Copy-arkiver havde allerede en indholdsgate i
`tools/check_clean_copy_distribution.py`; desktop-arkivet havde ingen, fordi det
aldrig blev bygget af et script.

**Fund 3 — determinisme-testen i min egen selftest var teater i første
udførelse.** Den sammenlignede to builds i samme proces, og en *ændret*
`ZIP_EPOCH`-konstant giver stadig to ens builds — så mutationen af konstanten
passerede. Beviset blev kontrolleret ved at ændre konstanten til 2020:
selftesten sagde grøn. Nu testes konstantens værdi og hvert medlems tidsstempel
særskilt, og mutationen af konstanten giver to navngiven fejl. Samme mønster som
opgave 17 fund 3.

**GATE (opgave 18):** `GRØN — python3 tools/quality_gate.py: GRØN, 36 steps (34 + desktop-archive + desktop-archive-selftest). Den nye port er grøn på de rigtige filer, selftesten fanger 4 mutationer med navngiven grund, og `EXCLUDED_DIRS`-mutationen (node_modules slap med) gav 5 — så undtagelsen er testet, ikke antaget. `build_clean_copy_archives.py --check` urørt, Stripe-worker uændret 69/69, tracking-worker uændret 83/83.`

**Kendte begrænsninger, skrevet ned i stedet for skjult:**

- `deploy-sites.yml`s path-filter udelukker med vilje `desktop/**` (opgave 14 og
  16: en desktop-ændring må ikke deploye sites), og `test_deploy_workflow.py`
  fejler hvis et gatestep læser en fil filteret ikke dækker. Derfor erklærer
  gatestrækket `desktop-archive` kun builderen og arkivet som inputs. En commit
  der *kun* retter `desktop/package.json` udløser derfor ikke gaten. Jeg har
  ikke selv lavet om på opgave 14s beslutning midt i en iteration; det er lagt
  under `❓ Til Mads` som et valg, fordi det kræver at filtre flyttes fra
  workflow- til jobniveau.
- Arkiverne der er *buildoutput* — pip-hjulet, sdist'en og npm-`tgz'en` — er
  stadig uåbnede. De er alle fundet byte-identiske med kilden i denne iteration,
  men intet holder dem der. Det er opgave 19.

### 19. FÆRDIG (implementering `ceo/aab-indre-version`) — åbn byggeoutput-artefakterne i `check_versions.py`

**Resultat:** De fem byggeoutput-arkiver læses nu *inde i*. Fire produkter har fået
et `inner`-felt på `Product` — `(arkivglob, memberglob, notation)` — og
`check_inner_versions` åbner hvert kanonisk arkiv og kræver, at den erklærede
fil bærer den kanoniske version:

| Arkiv | Læst fil | Læser |
|---|---|---|
| `eaa_scanner-1.2.0-py3-none-any.whl` | `eaa_scanner-1.2.0.dist-info/METADATA` | `Version:`-linje |
| `eaa_scanner-1.2.0.tar.gz` | `eaa_scanner-1.2.0/PKG-INFO` | `Version:`-linje |
| `mahope-eaa-scanner-1.2.0.tgz` | `package/package.json` | JSON `version` |
| `page-profile/page-profile-1.2.0.tar.gz` | `page_profile-1.2.0/PKG-INFO` | `Version:`-linje |
| `site-icons/site-icons-1.0.0.tar.gz` | `site_icons.py` | `__version__` |

Alle fem er fundet korrekte på de rigtige filer. Selftesten går fra 16 mutationer
til **25 mutationer + 1 negativ kontrol + positiv kontrol**, og `de rigtige filer`
er stadig en del af den.

**Fund 1 — planens forudsætning om site-icons var forkert, og det gav mere
dækning end den troede.** Planen skrev at `site-icons-1.0.0.tar.gz` er "et
håndlavet tarball med to filer og ingen `PKG-INFO`" og derfor skulle skrives op som
*uden indre versionserklæring*. Det er sandt at der ingen `PKG-INFO` er — men den
ene af de to filer erklærer versionen alligevel, som `__version__ = "1.0.0"` i
`site_icons.py:25`. Så det er dækket lige så vel som de fire andre, i stedet for
at blive en hvid plet i tabellen. Før `inner` fandt porten ingen som helst i
arkiverne; nu læser den alle otte produkter.

**Fund 2 — `fnmatch` lader `*` spænde over `/`, så det var den tredje måde
`*/PKG-INFO` kunne have talt byggeaffald med.** En sdist indeholder både
`eaa_scanner-1.2.0/PKG-INFO` *og* `eaa_scanner-1.2.0/eaa_scanner.egg-info/PKG-INFO`,
fordi setuptools skriver sit eget metadata indeni. Det er **to** filer, der ligner
som én, og kun den øverste er sdistens egen erklæring. Derfor matcher `member_matches`
segment for segment, så `*` ikke krydser `/`. Beviset ligger i fixtureen: den har
en `egg-info/PKG-INFO` på **1.1.0** i et 1.2.0-sdist, og den skal ignoreres. En
fnmatch der spænder over `/` ville slå den positive kontrol rød.

**Fund 3 — fixture-arkiverne var tekst, så hele den nye kontrol ville have været
teater.** `FIXTURE` skrev `"whl"`, `"tar"` og `"tgz"` som filindhold. `read_members`
kan ikke åbne dem, så uden ændringen ville porten have læst *intet* i *intet*
arkiv og alligevel været grøn på alle 25 mutationer. Fixtureen bygger nu ægte
arkiver med `build_archive`, på låste tidsstempler så resultatet er reproducerbart.

**Fund 4 — mutationen for et beskadiget arkiv fandt en uhåndteret undtagelse.**
Den mutation kørte porten i en `zlib.error` (beskadiget gzip-strøm), som ingen
`except` dækkede, så selftesten døde med en staksporing i stedet for en fejl.
Nu fanges `EOFError` og `zlib.error` sammen med de andre arkiv-fejl. Samme
fejlform som opgave 18: en port der aldrig har set arkivet fejle, kan heller ikke
rapportere det.

**Fund 5 — den negative kontrol er den pointe, ikke en bivirkning.** `inner=()` betyder
"dette arkiv erklærer ingen indre version", og porten skal tie. Hvis den krævede
en erklæring alligevel, ville den fejle de håndlavede arkiver uden grund. Negativ
kontrollen kører derfor `PRODUCTS` med `eaa-scanner-npm`'s `inner` sat til tom, på
en fixture hvor `tgz'en` slet ikke har nogen versionserklæring, og kræver nul fund.

**Sidebevis undervejs:** `read_members` bestemmer formatet af magiske bytes, ikke
af endelsen, fordi `.whl` er en ZIP uden at hedde `.zip` — den første kørsel
fejlede netop på det. En `.tgz` der viser sig at være en ZIP læses fint; det er
formatsvaghed, ikke en fejl.

**Gate:** `python3 tools/quality_gate.py` — **GRØN, 36 steps** (uændret antal; de
to nye kontrol-stræk i `check_python_env --self-test` ligger inde i steppet).
`python3 tools/check_versions.py --self-test`: OK (25 mutationer + 1 negativ
kontrol + positiv kontrol + rigtige filer). `python3 tools/check_versions.py`: OK,
8 produkter.

**Rettelse i en anden port, som gaten afslørede:** `check_python_env` erklærede
C-udvidelser i standardbiblioteket for tredjepart. `zlib` ligger som
`lib-dynload/zlib.cpython-39-darwin.so` — ingen `.py`, ingen `__init__.py` i
mappen over den — så `stdlib_names()` så den som en udeklareret afhængighed og
krævede den i `requirements-build.txt`. `stdlib_names` scanner nu også
C-udvidelser, også i `lib-dynload`, og tager navnet før ABI-mærket. Det er en
*løsning* på en gate, så den fik sin egen kontrol: syv moduler skal genkendes som
stdlib, og `extension_names` skal læse navnet før `cpython` — ikke slå `.txt` for
en udvidelse. Mutationen "værktøj importerer en pakke låsen ikke kender" er stadig
fanget, så den nye gren har ikke slækket porten.

**Begrundelse:** Opgave 18 fandt, at intet i repoet nogensinde har læst en byte
inde i `site/downloads/`. Desktop-arkivet fik en indholdsgate. Det gjorde
**kun** kildearkiverne dækkede: `eaa_scanner-1.2.0-py3-none-any.whl`,
`eaa_scanner-1.2.0.tar.gz` og `mahope-eaa-scanner-1.2.0.tgz` er buildoutput fra
henholdsvis `python -m build` og `npm pack`, så de kan ikke sammenlignes fil for
fil med kilden. De blev fundet byte-identiske den 26. september 2026, men intet
holder dem der, og de er præcis de filer en kunde `pip install`er.

**Omfang:**

- Tilføj til `check_versions.py` et felt på hvert produkt, der erklærer hvilke
  filer **inde i** arkivet skal bære den kanoniske version, med samme `#`-notation
  som `mirrors`: `package/package.json` for npm-`tgz'en, `PKG-INFO` for
  sdist'en, `*.dist-info/METADATA` for hjulet. Læsningen af en `Version:`-linje er
  en ren tilføjelse til `source_version`, så de eksisterende 16 mutationer ikke
  ændrer betydning.
- `site-icons-1.0.0.tar.gz` er et håndlavet tarball med to filer og ingen
  `PKG-INFO`. Skriv det ærligt op i tabellen som *uden indre versionserklæring*
  i stedet for at lade det se dækket ud.
- Udvid `FIXTURE` og mutationerne, så selftesten fanger: en `PKG-INFO` med
  1.1.0 i et 1.2.0-hjul, en `tgz` uden `package/package.json`, og en METADATA
  der slet ikke findes. Mindst én positiv kontrol der IKKE må fejle: et
  byggeoutput-arkiv uden indre versionserklæring skal være grønt, ikke rødt.

**Acceptkriterier:**

- `python3 tools/check_versions.py --self-test` fanger de tre mutationer med
  navngiven grund, og den eksisterende positive kontrol er stadig grøn.
- `python3 tools/check_versions.py` er grøn på de rigtige filer.
- Hele kvalitetsgaten er grøn, og `check_versions` står i path-filteret (den
  gør allerede).

**Gate:** `python3 tools/check_versions.py --self-test` plus hele kvalitetsgaten.

### 20. FÆRDIG (implementering `ceo/site-icons-arkiv`) — byg `site-icons-1.0.0.tar.gz` reproducerbart

**RESULT:** `site/downloads/site-icons/site-icons-1.0.0.tar.gz` var en håndlavet
kopi fra **24. august**, ikke bygget af `site-icons/`. Begge filer i arkivet afveg
fra kilden, og forskellen var den døde udbyder: `site_icons.py:45` sagde *"Lemon
Squeezy API when available"* (kilden: mahope.tools-licens-API'et) og
`README.md:69` sagde *"When Mads opens Bitwarden (Lemon Squeezy API), keys are
sold there"* — altså en publiceret README, der fortæller kunden hvor de kan købe
en nøgle i en konto der blev lukket 24. september. Opgave 19 glippede over den
fordi den kun læste arkivets *version* (1.0.0, korrekt). Arkivet er nu bygget af
kilden og er byte-identisk, verificeret både med Pythons `tarfile` og med
kommandolinjens `tar tzvf`.

Nyt `tools/build_site_icons_archive.py` i samme form som
`tools/build_desktop_archive.py` (build + `--check` + `--self-test`), låst
`tarnummer` (mtime 2000-01-01, uid/gid 0, ingen ejernavne, 0644, sorteret) og
låst gzip (`mtime=0`, intet filnavn i headeren). To nye gatestræk, 36 → 38.

**Fund 1 — de tre publicerede artefakter var tre håndlavede kopier, ikke én.**
`downloads.html` linker både `site_icons.py` (curl -O) og tarballet. README'en
havde derfor fået en *håndredigeret* linje med det rigtige domæne i den løse kopi,
mens tarballet beholdt den døde vært — to filer der sagde hver sit om det samme.
Derfor bygges nu alle tre fra `site-icons/`, og `--check` kræver at løse filer og
tarball begge er byte-identiske med kilden. Uden det ville de to glide fra
hinanden igen, og det er jo netop det der skete.

**Fund 2 — kilden havde selv den døde vært, som aldrig blev rettet.**
`site-icons/README.md:16` sagde `curl -O https://hermes-passiv.pages.dev/...`.
Den lå i kilden, blev aldrig set af nogen port, og ville være blevet publiceret
med i det nye arkiv, fordi porten bygger *af kilden*. Kun den håndredigerede løse
kopi havde rettet den. Rettet i kilden; porten læser den nu, fordi `site-icons/**`
er i path-filteret.

**Fund 3 — hullet fra opgave 18 er lukket her, og beviset for det stod i
`test_deploy_workflow`.** Opgave 18 måtte oplyse at `desktop/**` er bevidst
udeladt fra filteret, så en ren kilde-commit ikke udløser porten. Her er
`site-icons/**` med. Beviset er ikke at linjen står i YAML'en, men at porten
fejler når den tages ud: `site-icons-archive` læser alle syv filer i
`site-icons/`, og uden filterlinjen melder `test_deploy_workflow` dem som
udækkede. Derimod viste testen mig at `site/downloads/site-icons/**` er
*overflødigt* — `site/**` dækker det — så den linje blev fjernet igen frem for at
stå som pynt.

**Fund 4 — porten fandt sin egen fejl i gaten.** Min første docstring citerede
kildens rettelse som *"the mahope.tools license API (/api/license/validate)"*, og
`check_license_clients.py` meldte da `build_site_icons_archive.py` som
licensklient uden `product`. Det er porten, der har ret: filen er ikke en klient,
og den kan heller ikke være det, fordi kontrakten ikke har et site-icons-produkt.
Citatet er derfor forkortet til det, det beviser — hvilken udbyder teksten nævner.
Bemærk at porten *stripper kommentarer* men ikke docstrings, så det er et
dokumentationsvalg og ikke en fejl i porten.

**Bevis for porten:** 8 mutationer fanget med navngiven grund, positiv kontrol
grøn, determinisme grøn, og to falsk-positive-tests (en kilde må gerne have flere
filer end de publicerede; en *ikke-publiceret* kildefil må gerne nævne den lukkede
udbyder). De låste konstanter testes for deres værdi, ikke kun for determinisme —
to builds i samme proces er ens, hvad enten `TAR_MTIME` er 0 eller 2026.

**Kendte begrænsninger, skrevet op i stedet for skjult:** Arkivet er fladt, to
filer i roden, fordi det er det kunden har hentet siden 24. august. Det er ikke en
sdist: ingen `PKG-INFO`, ingen topniveau-mappe, ingen `LICENSE` (repoens MIT-licens
nævnes i README'en). `pyproject.toml` og `cli.py` medtages bevidst ikke — de er
byggeinput til en wheel vi ikke udgiver.

**Gate:** `python3 tools/build_site_icons_archive.py --self-test` (OK, 8
mutationer) + `python3 tools/quality_gate.py` (GRØN, 38 steps fra 36). Porten
fandt den rigtige fejl på de rigtige filer *før* nogen blev rettet: 5 fund på det
gamle arkiv, heraf de to med den lukkede udbyder.

### 21. FÆRDIG (implementering `ceo/clean-copy-arkiv-gate` `f58386d`, merge `077a67b`) — de fire sidste arkiver erklærer deres version indeni, men ingen læste den

**RESULT:** Opgaven troede, de fire Clean Copy-arkiver manglede en indholdsgate.
De har haft en siden opgave 7 del 2 — `check_clean_copy_distribution.py` er
gatestep 11 og beviser at hvert publiceret arkiv er en *byte-identisk*
regeneration af kilden, at hvert medlem er kilde-identisk, at `version.txt`
nævner udgaven, og at intet arkiv indeholder den døde vært. `--check` i
`build_clean_copy_archives.py` er grøn for alle tre. Begge
acceptkriterier var altså allerede opfyldt, og det er niende gang i dette
repo at noget, der så komplet ud, viser sig at være teater — her i planens
egen opgavebeskrivelse.

**Det rigtige hul var et andet sted, og det var ældre end opgaven troede.**
`check_versions.py` læste *filnavnets* version for de tre Clean Copy-zip og
ikke deres `manifest.json`, og gjorde det samme for desktop-kildearkivet.
Alle fire bærer den version de lover indeni — det er den kunden læser, når de
unzipper eller installerer. Beviset for at hullet var ældre, lå i selve
fixtureen: de fire arkiver bar `"manifest.json": "{}"` — en fil uden version,
fordi porten aldrig læste den.

Nu erklærer alle fire produkter `inner=(...)`. Selvstesten går 25 → 31
mutationer og 1 → 2 negative kontroller.

**Fund 1 — den nye check fanger noget byte-sammenligning ikke kan.** Jeg
muterede det rigtige Obsidian-arkiv, så `manifest.json` sagde 1.0.9 under et
1.0.10-navn. `check_clean_copy_distribution` siger "afviger fra en
regeneration af obsidian-plugin" — sandt, men uden at sige *hvad* den burde
være. `check_versions` siger nu: `clean-copy-obsidian → manifest.json siger
1.0.9, mens kilden siger 1.0.10 — kunden henter gammel kode under et nyt
filnavn`. Det er den diagnose en udgiver kan handle på.

**Fund 2 — fixtureen måtte ikke blive stående.** Positiv kontrol blev kørt
**før** de nye mutationer, fordi en check der slet ikke læser arkivet lader
fixtureen med `{}` være grøn. Den holdt ikke: de fire `{}` er nu erstattet af
de rigtige versioner, så porten er nødt til at læse dem.

**Fund 3 — den anden negativ kontrol er den der beskytter de fire nye
linjer.** Uden den ville hver af de fire `inner=` kunne være *for* stram og
gøre et publiceret arkiv rødt i stedet for grønt, og den eneste måde at opdage
det på var at læse dem. Den bekræfter at et zip med en `manifest.json` uden
`version` er grønt, når porten ikke har bedt om den.

**Kendte begrænsninger:** `version.txt` i de tre Clean Copy-arkiver læses
 stadig ikke af `check_versions` — notationen er en ren tekstlinje
 (`clean-copy 1.5.3`) uden nogen nøgle, og `check_clean_copy_distribution`
 dækker den. `site/extension-zips/`-kopierne af Chrome-arkivet kontrolleres
 ikke i `dist/`, fordi ingen af de to domæner bygger den mappe; de dækkes af
 regenerationstjekket.

**Gate:** `python3 tools/check_versions.py --self-test` (OK, 31 mutationer +
2 negative kontroller + positiv kontrol + rigtige filer) +
`python3 tools/quality_gate.py` (GRØN, 38 steps uændret).


### 22. FÆRDIG (`ceo/levering-uden-fil`) — Stop med at sælge filer, der ikke kan leveres

**Begrundelse:** Missionens produktfase peger på præcis denne fejl som den
første prioritet: *"et køb, der ikke leverer"*. `tools/paid_content.json` har
`kv_verified: false` for alle syv downloadprodukter, og ingen af de tredive
`delivery_files` findes i tree eller i dist. `handlePaidDownload` læser
`paidfile:<fil>` fra KV og svarer **503 "File temporarily unavailable. Reply to
your receipt email."** — altså et køb der tager penge, ikke leverer filen, og
sender kunden i en mailkvæs, der kræver et menneske. Det bryder både
kontrakten ("Mads må ikke røre det") og den danske forbrugerlov.

**Researchfund, inden der blev skrevet kode:**

- **Kun 2 af de 7 produkter havde en købsknap.** `eucomply-report-kit` ($69)
  stod på `compliance-report.html`, `scan.html` og `scan-da.html`;
  `eu-compliance-ebook-bundle` ($29) på `books/compliance-bundle.html`. De fem
  øvrige (DPA, NIS2/DORA, NDA, EAA-statement, Template Bundle) havde ingen CTA
  nogen stede og blev aldrig solgt fra sitet. Den dokumenterede skade var så
 ledes $98 pr. køb, ikke hele katalogens $424.
- **Licensprodukterne er ikke ramt.** EUComply Pro aktiverer nøglen online mod
  `mahope.tools` og låser PDF-download i `verifyAndDownload()`. Clean Copy Pro,
  DeskUptime Pro, Transmute Desktop og Page Profile Pro har hver deres
  udgivne klient med syvdages cache. De virker, og de sælges videre.
- **190 kildefiler hævdede stadig en pris på den afskaffede vare — 49 af dem
  var live.** 94 EN + 96 DA-krossellier skrev *"combined PDF + all EPUBs, $29"*
  / *"samlet PDF + alle EPUB'er, $29"*, alle fra `tools/iter498_books_cta.py`.
  **Korrigeret efter live-verificering:** bygget beholder korsel-blokken på kun
  49 af de 94 EN-sider og stripper alle 96 DA-blokke, så den gamle pris stod
  live på 49 sider, ikke 190. Kildelinjerne var alligevel ikke kosmetik: en
  regenerering af bloggen ville have bragt dem tilbage, og de er rettet i
  samme commit som de publicerede, så de to ikke kan glide fra hinanden.
- **JSON-LD erklærede et udsolgt produkt som `InStock`.**
  `books/compliance-bundle.html` havde `@type: Product` med
  `offers.availability: https://schema.org/InStock` og købslinket i
  `offers.url`. Det er strukturerede data, søgemaskiner læser. Erstattet af en
  `CollectionPage` uden tilbud.
- **En eksisterende selftest-scenarie var stum, som følge af min egen
  rettelse.** `wrong_domain` muterede `site/scan.html`s domæne. Da scan-siden
  forlod inventaret, ramte mutationen ingenting, og scenariet fejlede ikke —
  det testede bare ikke længere. Selftesten sagde 11/12, så den *lignede*
  stadig grøn. Rettet til `site/clean-copy.html`, og der er nu en guard der
  fejler, hvis et domænescenarie ikke muterer nogen købsside. Det er tiende
  gang i dette repo at en kontrol uden kontrol på sin egen mutation viser sig
  at være teater.

**Omfang:**

- Fjern Report Kit-CTA'en fra `compliance-report.html`, `scan.html` og
  `scan-da.html`, og $29-bundlen fra `books/compliance-bundle.html` +
  `books/index.html` + de seks øvrige bogsider + 190 blogfiler i kilden (49 af
  dem publiceres).
- Omskriv books-siden til det den faktisk er: seks gratis EPUB'er. FAQ'en,
  benefits, titel, description og JSON-LD følger med.
- Ny `check_deliverable` i `tools/check_stripe_ctas.py`: et `download`-produkt
  uden `kv_verified: true` må ikke have sit betalingslink nogen sted i `site/`.
- **Begge retninger er fejl.** Et `kv_verified: true`-produkt skal stå i
  inventaret, så et leverbart produkt ikke bliver glemt, fordi flaget blev
  sat uden at købssiden kom med.
- `tools/stripe_catalog.json` mister de fire offers (15 → 11).
- `docs/stripe-kontrakt.md` får en sektion om, hvornår downloadprodukter er
  til salg, og hvorfor.

**Acceptkriterier:**

- `python3 tools/check_stripe_ctas.py` er grøn og melder 0 problemer med 11
  købssider. **Oprevet.**
- Porten finder de fire sider med et betalingslink til et u-leverbart produkt
  på de rigtige filer, før nogen rettes. **Bevis: første kørsel efter
  implementationen meldte 4 fund, én pr. fil.**
- `python3 tools/check_stripe_ctas.py --self-test` fanger de to nye fejlformer
  og den positive kontrol fejler ikke. **Oprevet: 12/12 + positiv kontrol.**
- Et domænescenarie der ikke muterer nogen købsside giver exit 1. **Bevis ved
  mutation af selftestens egen betingelse: exit 1 med navngiven grund.**
- `rg '\$29' site/` finder kun én forekomst, og den er om et tredjepartsprodukt
  i en NIS2-artikel. **Oprevet.** `rg 'combined PDF|samlet PDF' dist/` er 0
  filer, og live `/blog/nis2-gap-assessment-guide` viser den nye linje.
- Live `books/compliance-bundle` har ingen `InStock` og ingen købslink.
- Hele kvalitetsgaten er grøn. **Oprevet: 38 steps.**

**Gate:** `python3 tools/check_stripe_ctas.py && python3 tools/check_stripe_ctas.py --self-test && python3 tools/test_weekly_report.py` plus hele kvalitetsgaten.

**Kendte begrænsninger, skrevet op i stedet for skjult:**

- Gaten læser `site/`, ikke `dist/`. Det er bevidst og konsistent med de øvrige
  checks i samme fil: bygget er gaten's første step og kopierer siderne
  uændret, så en ren kilde giver et rent dist.
- `/thanks` og leveringsmailen er **ikke** rettet. En køber der allerede har
  betalt for et downloadprodukt får stadig 503 og beskeden om at svare på
  kvitteringsmailen. Det er en reel, ulukket rest — men den kan ikke løses
  her, fordi en bruger der skal have en fil igen, kræver enten filerne i KV
  eller et menneske. Se `❓ Til Mads` punkt 9.
- `eucomply-pro`'s Pro-liste på `compliance-report.html` lover "continuous
  monitoring", "history tracking" og "priority support within 24h". Den
  implementerede Pro-værdi er at låse PDF-download. Det er en overdrivelse på en
  side der sælger, og den er ikke rettet her, fordi den kræver en beslutning om
  hvad Pro skal være — ikke en tekstrettelse.


### 23. FÆRDIG (`ceo/hub-readme`) — researchiteration: repoets egen indgangsside løb ud som ét produkts README

**Hvorfor denne iteration skrev kode.** Køen var tom: opgave 1-22 er `FÆRDIG`, og den
næste opgave i køen (nr. 23 før denne) var `❓ Til Mads` punkt 9, som kræver de private
`paidfile:`-kilder og derfor ikke kan udføres her. Kontrakten siger, at en iteration der
kun ændrer planen er spildt, så researchfundet blev brugt på en rigtig forbedring.

**Fund 1 — rod-README.md var en anden produkts README.** `mahope/hermes-passiv` bygger
fire sites og otte produkter, men `README.md` i repo-roden var en tidligere udgave af
`obsidian-plugin/README.md`: titlen "Clean Copy for Obsidian", tre Obsidian-specifikke
installationsafsnit og en changelog der stopp ved **1.0.1**, mens den publicerede udgave
er **1.0.10** (`site/downloads/clean-copy-obsidian-v1.0.10.zip`). GitHub viser
rod-README som repoets forside, så det er den side en nye bidragsyder eller
npm-/GitHub-besøgende lander på først — og den sagde " ét produkt" i stedet for "familien".
Den nye README er en kortlægning af de fire sites, de otte gratis værktøjer og de fem
licensprodukter, plus donationstaletten missionen kræver.

**Fund 2 — mit eget første udkast havde tre falske påstande, og alle tre var fanget
inden commit.** Det er det stærkeste fund i iterationen, fordi det viser at
selv-korrektion uden en maskine ikke er nok:
1. Jeg skrev `mahope.tools/eucomply` og `deskuptime.com/transmute` som produktsider.
   **Ingen af dem findes.** Live-sitemaps for de to domæner indeholder hverken
   `eucomply` eller `transmute`, og Transmute har slet ingen offentlig side — kun
   npm-pakken. To døde links i en ny README er præcis den fejl `tools/check_links.py`
   gater for i `site/`, men den læser ikke rod-README.
2. Jeg skrev "**The free tools do not phone home**". Det er ordret den samme
   påstand opgave 2 var nødt til at trække tilbage, fordi en licensaktivering er et
   online-kald mod `mahope.tools/api/license`. Missionen siger eksplicit at påstande
   skal kunne dokumenteres, så formuleringen blev til det faktiske forhold: frie
   funktioner sender ikke indholdet nogen steder, betalt tier laver ét slags kald
   (licenstjek) med nøgle og device-id, og caching i syv dage når tjekket fejler.
3. Jeg skrev at Clean Copy Pro virker "**everywhere**". Ingen klient er undersøgt
   for det, så det blev til den dokumenterede værdi: "custom cleanup rules with regex
   support".

**Fund 3 — hullet er en klasse, ikke en enkeltfil.** Dette er niende gang i dette
repo (se opgave 10, 15, 17 og 21) at et problem kun findes fordi nogen læser den
konkrete fil med vilje. `check_links.py`, `check_product_copy.py` og
`check_private_content.py` dækker alle `site/` og `dist/`. **Ingen af dem læser
`README.md` i repo-roden**, og den er den eneste PUBLICEREDE tekst om hele familien
der ligger uden for gaten. Derfor er det ikke nok at have skrevet en ny README —
se opgave 26.

**Gate:** `python3 tools/quality_gate.py` → **GRØN, 38 steps (uændret)**. README'en er
ikke en del af nogen gate, så grøn gate er her bevis på *ingen skade*, ikke på
*korrekthed*; korrekthed er derfor verificeret mod de tre live sitemaps og
`tools/stripe_catalog.json`. `site/` og `dist/` er urørt, så intet deployes.

---

## Ny kø fra opgave 23s researchfund

### 24. UFÆRDIG — ❓ Til Mads punkt 9: gør de syv downloadvarer leveringsklare *(kræver ham, ikke mig)*
De syv produkter har `kv_verified: false`, og deres 30 filer findes ikke i KV. Uden dem
er `$59 + $49 + $29 + $39 + $69 + $149` i Stripe-priser dødt salg, og kun
`eu-compliance-ebook-bundle` har lagt `compliance-bundle.pdf` i sit leveringskrav.
**Acceptkriterium for ham:** `python3 tools/check_private_content.py --report` viser
0 `uverificeret i KV`, og gaten kræver da købssiden tilbage (den fejlbygger, hvis
`kv_verified` er true uden en købsside — så flaget kan ikke sættes uden salget).
**Findes ved:** kv-nøglerne og de private kilder. Ikke mit arbejde; skrives her for at
det ikke tabes.

### 25. UFÆRDIG — de syv betalingslinks er stadig live, selv om varerne ikke kan leveres
Opgave 22 lukkede *vores* salgssider. Stripe Payment Links kan ikke slås fra her (ingen
nøgler), så `buy.stripe.com/…` for de syv produkter tager stadig imod betaling og sender
en køber til `/thanks`, hvor `/api/download` svarer 503. Det er præcis det scenarie
opgave 22 beskriver som farligt — pengene ind, filen ud. **Acceptkriterium:** enten
hviler Mads de syv links, eller de får filer (opgave 24). Repoet skal *kun* sikre sig,
at ingen af vores sider peger på dem, hvilket `check_stripe_ctas.py` nu gater.

### 26. UFÆRDIG — gaten skal dække de publicerede tekster uden for `site/`
Fund 3 fra opgave 23. i dag læser ingen gate `README.md`, `AGENTS.md` eller
`.github/FUNDING.yml`, som er det offentlige ansigt. **Acceptkriterium:** en ny check
`tools/check_repo_readme.py` med `--self-test` der fejler på (a) et link i rod-README
meden rødt svar, (b) en bygget sti i rod-README der ikke findes i noget sitemap, (c) en
pris der ikke findes i `tools/stripe_catalog.json`, (d) en død udbyder (`lemon`,
`gumroad`) nævnt som om den virker, og (e) en FALSK-positiv-kontrol: en README med kun
relative links eller kun npm-URLer skal ikke fejle. Bevis: find mindst én fejl på den
*gamle* rod-README før den rettes.

### 27. UFÆRDIG — de shippede README'er kan ikke nævne Pro, fordi en ændring kræver en version
`extension-clean-copy-firefox/README.md` (Pro: 0 fund, donation: 0) og
`obsidian-plugin/README.md` (Pro: 2, donation: 0) ligger **inde i de publicerede
arkiver**. Men opgave 21s gate gør netop, at en ændring af arkivindhold kræver en ny
version — og versioner, tags og releases er Mads' (kontrakten forbyder mig dem). Så det
bedste konverteringspunkt for de mest distribuerede klienter kan ikke flyttes af mig.
**Acceptkriterium:** skriv de to tekster ferdige og læg dem i planen som et
versionsforslag, så Mads' næste udgivelse tager dem med. Det er tekstforberedelse, ikke
en kodeændring.

## ❓ Til Mads

1. **Tilføj property i Google Search Console** for `mahope.tools`, `cleancopy.tools`, `deskuptime.com`, `bugbottle.dev` og `mahoje.dk`. Verificér sitemap og robots efter tilføjelse. Denne handling må ikke udføres af repoet.
2. **Beslut om den lokale BugBottle-shadow:** live `bugbottle.dev` er dokumenteret som den separate `mahope/bugbottle`/Dokploy-kilde med 40 routes på commit `07828a1d605383c58cf44416447e0497e91fdac3`; dette repo har en ubrugt 7-routes shadow. Vælg om shadowen skal fjernes helt eller holdes som et lokalt kildesnapshot. Det er ikke længre en blocker for den nuværende deploy.
3. **Beslut om historik-remediering:** Betalt indhold findes i tidligere public commits. En fuld sletning kræver en koordineret historik-rewrite, som loop-kontrakten forbyder og som ikke må ske uden dit go. Indtil beslutningen står som `BLOCKED: kræver Mads-godkendelse`.
4. **Bekræft private paid-file-kilder:** hvilket privat repo eller hvilken godkendt buildkilde skal producere de filer, der forventes i Cloudflare KV? Der findes ingen lokal checkout af `mahope/paid-products`, så `tools/paid_content.json` har `build_command: null` og `sha256: null` for alle syv downloadprodukter. Ingen produktionsupload må køre automatisk fra dette repo uden separat godkendelse.
5. **Beslut om to nye Stripe-produkter:** `site/site-icons.html` (Site Icons Pro: Apple touch-, PWA-, Windows- og OG-ikoner) og `site/downloads.html` + `blog/eaa-compliance-scanner-desktop.html` (EAA-scanner Pro: batch-scanning, CSV/JSON-eksport, ubegrænset crawl) har nu ingen pris og ingen købsknap, fordi kontrakten ikke indeholder produkter til dem. Opret kun dem, hvis du vil sælge dem; repoet gør det aldrig selv.
6. **Udfør én lavendet Stripe-testkøb**, når de lokale mock-tests er grønne, hvis licensaktivering, kvittering og download skal verificeres mod rigtige Stripe/CF-tjenester. Brug kun et allerede oprettet produkt; opret ikke et nyt.
7. **Bekræft catch-all på `mail.mahoje.dk`:** opgave 4D har nu sat leveringsmailens `reply_to` til `support@<produktets domæne>`. MX er read-only bekræftet for alle domæner, men om en catch-all findes og videresender til `support@mahope.tools` kan kun afklares ved at sende én testmail til hvert domæne. Uden catch-all bouncer kunders svar, og det skal rettes straks.
8. **Beslut om EAA-scannerens licensvært.** `desktop/main.js` kalder `https://hermes-passiv.pages.dev/api/license/*`, som ikke er et deployet Pages-projekt, og sender intet `product`. Selv hvis værten rettes, afviser workeren payloaden, fordi kontrakten ikke har et EAA-produkt. `tools/check_license_clients.py` holder den som dokumenteret undtagelse, så den kan ikke komme i drift ved et uheld. Den samme mangel gælder `site/compliance-report.html`, som nu er rettet til `eucomply-pro`; bekræft at det er det produkt du vil have folks nøgle fra dér.
9. **Gør de syv downloadvarer leveringsklare.** Opgave 22 har lukket *salgssiden* for dem: de har `kv_verified: false`, ingen af de tredive filer findes, og `/api/download` svarer 503 — så sitet tilbyder dem ikke længere, og `check_stripe_ctas.py` fejler hvis det gør. **Hvad der mangler er filerne, ikke dækningen.** Når de private kilder ligger et sted, skal de uploades til KV som `paidfile:<fil>`, og `kv_verified`/`sha256`/`build_command` udfyldes i `tools/paid_content.json`. Så snart `kv_verified` står på `true`, kræver gaten at købssiden er med igen, så flaget ikke kan sættes uden at salget følger med. `python3 tools/check_private_content.py --report` viser de 30 nøgler.

   **Prioritering, hvis du ikke vil gøre alle syv:** `eucomply-report-kit` ($69) og `eu-compliance-ebook-bundle` ($29) var de eneste to, der blev solgt, og er derfor de nemmeste at tjene på. `eu-compliance-ebook-bundle` er den billigste: de seks EPUB'er ligger allerede i `site/downloads/`, så kun den kombinerede PDF skal bygges. Købssiden er desuden allerede skrevet om til at pege på EPUB'erne.
10. **Beslut om desktop-filtrene i `deploy-sites.yml`.** `desktop/package.json` er
    bevidst udelukket fra path-filteret, så en desktop-ændning ikke deployer sites
    (opgave 14 og 16). Men opgave 18 har nu en gate, der netop skal køre når
    `desktop/` ændrer sig, fordi det publicerede kildearkiv er bygget af den mappe.
    De to regler kan ikke begge være sande i dagens form, fordi filteret hænger på
    workflowniveau og derved gælder både `gate` og `deploy`. Løsningen er at flytte
    filtrene ned på jobniveau: `gate` får et filter der dækker alt den læser
    (inkl. `desktop/package.json`), `deploy` beholder sit site-only filter, så
    desktop-ændringer gater men ikke deployer. Det er en ændring i den
    produktionskritiske deploy-workflow, og den hører til dig, ikke til mig.
11. **Fem licensklienter i `mahope/auditedwp` er uden for denne licenskontrakt.** De blev fundet af `tools/check_license_clients.py` i CI for første gang i kørsel `36185964282`, fordi CI checkouter det repo ved siden af workspace mens maskinen ikke gør det. Fundene er ægte og skal ikke forsvinde, men de kan ikke rettes her: `auditedwp` er et andet repo med sin egen kontrakt, og denne plan må ikke ændre det. Fundene er derfor skrevet ud af gaten — efter et **regelprincip** (en mappe med sin egen `.git` er ikke vores kode) og ikke en navneliste, og de er noteret her i stedet:
    - `deskuptime/desktop/src-tauri/src/lib.rs` kalder `api.lemonsqueezy.com` — den lukkede API. Kunden får en fejlslæng.
    - `deskuptime/src/license.js` kalder `api.lemonsqueezy.com` — samme.
    - `devnotify/src-tauri/src/lib.rs` kalder `api.lemonsqueezy.com` — samme.
    - `plugin/eucomply.php` kalder `/api/license` **uden `product`** — værten afviser payloaden med 400, så pluginet kan aldrig aktivere en nøgle.
    - `site/plugin/eucomply.php` — samme fil, dublet.
    Det er din beslutning, om de rettes i `auditedwp`, eller om de to sidste skal finde en plads i denne kontrakt. Gaten her dækker dem ikke, og det er bevidst.


## Deploylog

- 2026-09-26: `DEPLOY OK aae4a72` — lukker `VERIFICÉR DEPLOY` for opgave 22. Kørsel
  `36204568679` kørte `gate` grønt i 38 steps og deployede de tre Pages-domæner
  grønt. Indholdsverificeret, ikke HTTP-status:

  | Side | Før | Efter |
  |---|---|---|
  | `/books/compliance-bundle` | `Product`+`InStock`+købslink, `$29` | 0 fund af alle tre; *"All six e-books are free"* |
  | `/compliance-report` | Report Kit $69 + EUComply Pro $79 | 0 Report Kit, 1 Pro-link |
  | `/scan`, `/scan-da` | Report Kit-link | 0 fund |
  | 49 publicerede blogkorseller | *"combined PDF + all EPUBs, $29"* | *"all six listed together, each a free EPUB"* |

  `build-info.json` bærer `aae4a72e642926f857955b45e4978e132dd7be90`.
  **Én fund undervejs, som rettede min egen plan:** de 190 kildelinjer var ikke
  190 publicerede. Bygget beholder korsel-blokken på 49 af de 94 EN-sider og
  stripper alle 96 DA-blokke, så den gamle pris stod live på 49 sider. Det er
  skrevet op i opgavens researchfund, ikke kun her.

- 2026-09-26: `DEPLOY OK 956f19f` — lukker `VERIFICÉR DEPLOY` for opgave 19. Kørsel
  `36201588862`: `gate` grøn (36 steps) + tre grønne deploys. Committen rørte kun
  `tools/` og planen, så intet på domænerne kunne ændre sig — og det blev
  verificeret på indhold, ikke HTTP-status: de tre publicerede byggeoutput-arkiver
  er byte-identiske med repoet.

  | Filer | sha256 (første 16) | HTTP | Byte |
  |---|---|---|---|
  | `downloads/eaa_scanner-1.2.0-py3-none-any.whl` | `0fc4b3ba7931df48` | 200 | 14086 = 14086 |
  | `downloads/mahope-eaa-scanner-1.2.0.tgz` | `d9e74ffb97db8386` | 200 | 10664 = 10664 |
  | `downloads/site-icons/site-icons-1.0.0.tar.gz` | `882ab49d4571bb4f` | 200 | 5674 = 5674 |

  Det er samme tre filer som opgave 19 åbner for første gang. De var alle korrekte,
  hvilket også er svar på spørgsmålet om hvor de tre fund var: de to sdists og det
  ene håndlavede tarball var ikke forsinkede, de var bare uåbnede.

- 2026-09-26: `DEPLOY OK 14f0ee3` — lukker `VERIFICÉR DEPLOY` for opgave 18. Kørsel
  `36199954971`: `gate` grøn (36 steps) + tre grønne deploys. Indholdsverificeret, ikke
  HTTP 200: live `mahope.tools/downloads/eaa-scanner-desktop-src-1.3.3.zip` er
  byte-identisk med repoets arkiv, pakker ud til **11** filer (før: 10), og dens
  `package-lock.json` siger `version 1.3.3` med `electron ^44.4.5` og
  `electron-builder ^26.15.3` (før: 1.3.0 og `^25.0.0`), `package.json` har
  `engines.node >=22.12.0` (før: feltet manglet), og `.nvmrc` er med (før: manglet).
  Live `build-info.json` bærer merge-SHA'en.

- 2026-09-26: `DEPLOY OK 4805eaa` — kørsel `36198367044`: `gate` grøn (34 steps) + tre grønne deploys. Indholdsverificeret, ikke HTTP 200: live `deskuptime.com/style.css` indeholder broen (`--accent: var(--color-accent)` under `html[data-product="deskuptime"]`), og alle tre live værktøjssider indlæser `/assets/site.css` FØR `/style.css`, så broen er den der vinder. Dette lukker `VERIFICÉR DEPLOY` for opgave 17.

- 2026-09-26: `DEPLOY OK cba6c10` — lukker `VERIFICÉR DEPLOY` ovenfor. Kørsel `36196613182`: `gate` grøn (32 steps) + tre grønne deploys. Indholdsverificeret, ikke HTTP 200: begke `search-index.json` 0 fund af `hermes-passiv.pages.dev`; live `cleancopy.tools/api-readme.md` 4 fund af `cleancopy.tools/api/clean-copy`; live `mahope.tools/compliance-site-check` forudfylder `urlInput` med `https://mahope.tools`; alle tre `build-info.json` bærer `cba6c10`. CI meldte kun kendte ubuntu-latest-/git-advarsler.

- 2026-09-26: `VERIFICÉR DEPLOY: døde værter væk fra 8 publicerede filer, search-indekset og scannerens forudfyldte felt <merge-sha> 2026-09-26` — GitHub Actions kører automatisk (`site/**` er i path-filteret). Denne deploy **ændrer synligt indhold**, så verificér indhold, ikke HTTP 200:
  - `mahope.tools/compliance-site-check` og `/da/compliance-site-check`: scanningsfeltet er forudfyldt med `https://mahope.tools` (før: den døde vært), det synlige `Try:`-link peger på `mahope.tools`, og den eksporterede rapports `Scanned:`-linje siger `via mahope.tools/compliance-site-check`.
  - `cleancopy.tools/search-index.json`: nul fund af `hermes-passiv.pages.dev` (før: `POST https://hermes-passiv.pages.dev/api/clean-copy` i `/clean-copy-api`'s uddrag). Bemærk at selve siden altid var rigtig — kun uddraget var løgnen.
  - `cleancopy.tools/api-readme.md` skal pege på `https://cleancopy.tools/api/clean-copy`; `mahope.tools/page-profile-api-readme.md`, `api-compliance-scan-readme.md`, `downloads/cookie-consent-banner.js`, `downloads/eaa-scanner-README.md`, `downloads/site-icons/README.md` og de tre GDPR-skabeloner skal pege på `mahope.tools`.
  - Live `build-info.json` bærer merge-SHA'en.

- 2026-09-25: `DEPLOY OK d7d97f6` — kørsel `36191570696` kørte `gate` grønt i
  54 s (28 steps, inkl. de to nye `python-env`-steps på CI's Python 3.12) og
  deployede cleancopy.tools, deskuptime.com og mahope.tools grønt. Det lukker
  `DEPLOY FEJL 36191355378`. **Intet site-indhold er ændret** — ingen `site/`-fil
  blev rørt, så de tre domæner får præcis det indhold de havde før merge; kun
  bygge- og gatestierne er nye.

- 2026-09-25: `DEPLOY FEJL 36191355378` — `gate`-jobbet døde i step 25 `python-env`
  med `AttributeError: 'PosixPath' object has no attribute 'read'`, fordi CI's
  Python 3.12 bruger den indlejrede `tomllib`, hvis `load()` kræver en binær
  filobjekt, mens kun 3.9 rammer `mini_toml`-fallbacken. **Intet site blev
  deployet**, og `dist/` er uændret. Rettet i samme iteration ved at bruge
  `loads(text)` i stedet for `load(path)`.

- 2026-09-25: `INGEN SITE-INDHOLD ÆNDRET — python-build-lock` — mergecommit for
  opgave 13 rørrer `requirements-build.txt`, `requirements-audit.txt`,
  `.python-version`, `.gitignore`, `site-icons/pyproject.toml` og fire filer i
  `tools/`. Ingen `site/`-fil er rørt, så de tre domæner får præcis det indhold de
  havde. Deploy-workflowens path-filter rører `tools/**` og
  `site-icons/pyproject.toml`, så kørselen forventes, og `gate`-jobbet kører de to
  nye steps. **Verificér ikke live-indhold** — intet er ændret. Den eneste
  post-merge-gate er CI's egen grønne `gate`.


- `CI-BEVIS` (opgave 12): `36188356033` (build-desktop, main) — `build-macos` x64 og
  arm64, `build-linux` og `build-windows` **grønne** på Electron 44.4.5 med den Node
  fra `.nvmrc`; `release` korrekt skipped (intet tag). `36188355972` (deploy-sites,
  main) — `gate` grøn og alle tre domæner grønne deployet med det byte-identiske
  `dist/`. Post-merge-gaten er dermed lukket på alle fire platforme, inklusive dem
  der aldrig var bygget før.
- 2026-09-25: `DEPLOY OK cc5164f` — kørsel `36188355972` kørte `gate` (26 steps) og
  deployede cleancopy.tools, deskuptime.com og mahope.tools grønt. Intet site-indhold
  er ændret: ingen `site/`-fil blev rørt, så de tre domæner får det samme indhold som
  før merge.
- 2026-09-25: `VERIFICÉR DEPLOY: intet site-indhold ændret cc5164f 2026-09-25` —
  live `build-info.json` på de tre domæner skal bære `cc5164f`; indholdet skal være
  uændret, fordi ingen `site/`-fil blev rørt. Brug `python3 tools/check_live_sitemaps.py
  --commit cc5164f…` med fuld 40-tegns SHA.
- 2026-09-25: **KORREKTION til noten ovenfor — `deploy-sites` KØR alligevel.** Min antagelse
  var, at kun `desktop/` var rørt, men `tools/test_deploy_workflow.py` og
  `.github/workflows/build-desktop.yml` står i deploy-workflowens path-filter (det
  lagde opgave 11 ind med vilje, fordi gaten læser begge). Kørslen `36188355972`
  startede derfor og deployer tre domæner med et `dist/`, der er **byte-identisk**
  med det der ligger live — ingen ny notesætning, samme som sidste gang. Verificér
  derfor `build-info.json` på de tre domæner: den skal bære `cc5164f`, og indholdet
  skal være uændret. Kun hvis indholdet afviger, er der tale om en reel fejl.
- 2026-09-25: `INGEN SITE-INDHOLD ÆNDRET — desktop-node-runtime cc5164f` — mergecommit
  for opgave 12 rører kun `desktop/`, `tools/test_deploy_workflow.py`,
  `.github/workflows/build-desktop.yml` og denne plan. Ingen `site/`-fil er rørt, så
  de tre domæner får præcis det indhold de havde. Den eneste post-merge-gate der
  betyder noget er `build-desktop.yml` (kørsel `36188356033`): macOS x64/arm64, Linux
  og Windows skal være grønne på Electron 44.4.5 med Node 22.23.2 fra `.nvmrc`.

- 2026-09-25: `DEPLOY OK 3e35408` — CI kører `python3 tools/quality_gate.py` i det nye
  `gate`-job, og run `36186489675` på `main` er **grøn i alle 26 steps** (`quality_gate:
  GRØN — 26 steps`) efterfulgt af tre grønne deploys. De tre deploys uploadede
  2/2/2 filer og 66/29/319 var allerede uploadet — altså intet nyt site-indhold, kun
  byggestien ændret, præcis som forventet. Uafhængig `python3 tools/check_live_sitemaps.py
  --commit 3e354080d9f57a89147c2bb05a3d7800f3426195` melder `live sitemap OK` for
  cleancopy.tools, deskuptime.com og mahope.tools. CI's egen post-deploy-gate var grøn
  i alle tre jobs. Forrige kørsel `36185964282` var rød i step 13 med de fem
  `auditedwp`-fund, der nu er noteret under `❓ Til Mads` punkt 10 — de var ægte, men
  de tilhører et andet repo.

- 2026-09-25: `VERIFICÉR DEPLOY: døde links rettet, DeskUptime-assets tilføjet, 404-/søgenav omskrevet og hard gate for uopklarede referencer c3dea9189e2207c4ed2ac63beacd195e1e1ea0e0 2026-09-25` — GitHub Actions kører automatisk, fordi `site/**`, `build_sites.py` og `tools/check_links.py` er i path-filteret. Denne deploy **ændrer synligt indhold** på tre domæner, så verificér indhold, ikke bare HTTP 200:
  - `deskuptime.com/assets/site.css` og `/assets/site.js` svarer **200** — de har aldrig eksisteret, så de tre værktøjssider kørte uden stylesheet og uden sitets JS. Tjek at `/tools/` og `/bulk-url-checker/` er stylet, og at sidens JS indlæses uden 404 i netværksfanen.
  - `cleancopy.tools/404` og `/search/` har **"Guides"** i navigationen som `https://mahope.tools/blog/` — før denne deploy var det `/blog/`, som er 404 på cleancopy.tools. Samme forventning på `deskuptime.com/404` og `mahope.tools/404`.
  - `mahope.tools/blog/copy-table-from-website-to-excel` og `/blog/copy-table-website-to-google-sheets` har ingen `{URL}`-placeholder længere; de to `Related:`-links peger på artikler der findes.
  - `mahope.tools/downloads` mærkede scanner-arkiverne 1.3.0; live skal de nu sige 1.2.0, fordi det er den version der ligger på disken (se opgave 18).
  - Live `build-info.json` bærer merge-SHA'en for alle tre domæner.

- 2026-09-25: `DEPLOY OK 9aed6a2` — run `36184136855` kørte `gate-distribution` med den
  nye `check_links.py` + `--self-test` grønt og deployede cleancopy.tools,
  deskuptime.com og mahope.tools grønt; CI's egen post-deploy-gate meldte grønt for
  alle tre. **Indholdskontrol, ikke HTTP 200:** `deskuptime.com/assets/site.css` svarer
  200 med 42 462 bytes og `/assets/site.js` 200 med 28 945 — de samme tal som i
  `../auditedwp/site/assets/`, og begge filer gav 404 før dette merge, så de tre
  værktøjssider har kørret uden stylesheet og uden sitets JS. Live
  `cleancopy.tools/404` har nu `href="https://mahope.tools/blog/"` på begge
  "Guides"-links, hvor den stod som `/blog/` (404 på cleancopy.tools) før merge.
  `{URL}`-placeholderen er væk fra begge publicerede artikler. Live `/downloads`
  mærkede scanner-arkiverne 1.3.0 før merge og siger nu 1.2.0 to gange med nul
  fund af 1.3.0. Alle tre live `build-info.json` bærer
  `9aed6a2c9755f723698da5243698a86aca1a9074`. CI meldte kun kendte
  Node 20-/Ubuntu 26-advarsler.

- 2026-09-25: `DEPLOY OK 7ccfd43` — begge kørsler grønne. `36180893396`
  (build-desktop, main) kørte `build-macos` x64 + arm64, `build-linux` og
  `build-windows` grønt med electron-builder 26.15.3 — første gang siden
  25. august at linux og windows er bygget, så opgave 9s post-merge-gate er
  endelig lukket. `36180893496` (deploy-sites, main) kørte `gate-distribution`
  og alle tre domæner grønt, inklusive den nye `test_deploy_workflow.py` med
  stdlib-parseren. Intet site-indhold er ændret: de tre domæner får samme
  `dist/` som før, kun gate-kommandoerne er nye. Uafhængig read-only
  kontrol: alle tre live `build-info.json` bærer `7ccfd43`;
  `cleancopy.tools/` + `/clean-copy` + `/downloads/clean-copy-v1.5.3.zip`,
  `deskuptime.com/`, `mahope.tools/` + `/downloads` + `/thanks` + `/support`
  svarer 200. `cleancopy.tools/downloads` er 404, og det er korrekt: domænet
  publicerer kun arkiverne, `/downloads`-siden ligger på mahope.tools — præcis
  den ordning opgave 8 gater. `dist/` er byte-identigt før og efter
  (`git status dist/` er tom), så intet site-indhold er ændret.
- 2026-09-25: `DEPLOY FEJL 36180367257` — alle tre deploy-jobs døde på
  `ModuleNotFoundError: No module named 'yaml'`, fordi den nye gate blev lagt
  ind i `deploy-sites.yml`, der kører på `setup-python` uden PyYAML. Ingen
  site blev deployet. Rettet i `7ccfd43` med `tools/mini_yaml.py`.
- 2026-09-25: `DEPLOY FEJL 36180365427` — `build-desktop` faldt i 0 sekunder
  uden ét job, fordi `on.push` stod i listeform, som GitHubs schema afviser.
  Bevis for at jeg ikke måtte skrive filtre som liste. Rettet i `7ccfd43`.
- 2026-09-25: `INGEN SITE-DEPLOY FORVENTET — 9ed7af6` — mergecommit for opgave 9 rørte kun `desktop/package.json`, `desktop/package-lock.json` og denne plan. Deploy-workflowens path-filter rører `desktop/` ikke, så GitHub Actions deployer ingen sites. `dist/` er byte-identisk før og efter. **Verificér ikke live-intet — intet site-indhold er ændret.** Den eneste post-merge-gate for denne commit er `build-desktop.yml`, og den kørte ikke; se `CI-FEJL` i statusblokken og opgave 16.

- 2026-09-25: `DEPLOY OK b401e7d` — GitHub Actions-run `36175801912` kørte det nye `gate-distribution`-job (grønt) og deployede cleancopy.tools, deskuptime.com og mahope.tools grønt, inklusive CI's egen live-gate. Alle tre live `build-info.json` bærer `b401e7dda5d261dd5b667d655d2a8a8a65c26fd1`, og uafhængig `check_live_sitemaps.py --commit b401e7d…` meldte `live sitemap OK` for alle tre. Indholdskontrol: de tre arkiver på cleancopy.tools svarer 200, de fire gamle (1.5.2 ×2, 1.0.9, 1.0.6) svarer 404, og live `mahope.tools/downloads` linker på `https://cleancopy.tools/downloads/…` — præcis den ordning opgave 8 nu gater. Dette lukker `VERIFICÉR DEPLOY` nedenfor og `DEPLOY FEJL 36175438151`.
- 2026-09-25: `DEPLOY FEJL 36175438151` — cleancopy.tools og deskuptime.com blev grønt deployet, mahope.tools fik rød gate **før** deploy med fem `check_publish_targets`-fejl om `cleancopy.tools publicerer ikke …`. Årsagen var en fejl i den nye gate (se `CI-FEJL RETTET` i statusblokken), ikke en fejl i siterne. `dist/` var byte-identisk, så live-indholdet er uændret, og mahope.tools blev ikke deployet overhovedet. Rettelsen gik ud i samme iteration; genkør `36175438151`s afløser.
- 2026-09-25: `VERIFICÉR DEPLOY (lukket af `DEPLOY OK b401e7d`): domæne-bevis for Clean Copy-arkiverne — kun en gate, intet nyt site-indhold 13c2e65 2026-09-25` — `tools/check_clean_copy_distribution.py` ligger i workflowens path-filter, så GitHub Actions kører, men `dist/` er byte-identisk før og efter (`git status` viser ingen dist-ændring), så live-indholdet skal være uændret. Verificér: `cleancopy.tools/downloads/clean-copy-v1.5.3.zip` svarer 200, live `mahope.tools/downloads` linker på `https://cleancopy.tools/downloads/…` (ikke på sig selv), og live `mahope.tools/downloads/clean-copy-v1.5.3.zip` svarer fortsat 404 — det er korrekt, da arkivet kun publiceres på cleancopy.tools.

- 2026-09-25: **Korrektion af en tidligere deploy-note.** Noten under `DEPLOY OK 3289b5b` rapporterede "Fire 404 fundet samtidig: `mahope.tools/downloads/clean-copy-*.zip` giver 404 … Det er ældre end denne iteration og er oprettet som opgave 8." Konklusionen var forkert: de fire 404'er var ét arkiv probet fire gange mod det domæne, det ikke ligger på. Live `/downloads`-sideens links er absolutte mod cleancopy.tools og svarer 200, så ingen kunde rammer en 404. Opgave 8 blev derfor skrevet om til det, der faktisk manglede: et bevis for hvilket domæne der publicerer hvilket arkiv.

- 2026-09-25: `VERIFICÉR DEPLOY (lukket af `DEPLOY OK 3289b5b`): Clean Copy-arkiverne 1.5.3 / 1.0.10 med den nye licensklient <merge-sha> 2026-09-25` — GitHub Actions udgiver automatisk: `site/downloads/*.zip`, `site/extension-zips/`, `site/clean-copy.html`, `site/da/clean-copy.html`, `site/downloads.html`, `site/free-downloads.html`, begge Obsidian-guides og `tools/make_blog_da_mirrors_461.py` er i path-filteret. Verificér på live: `cleancopy.tools/downloads/clean-copy-v1.5.3.zip` og `/downloads/clean-copy-firefox-v1.5.3.zip` er byte-identiske med repoets arkiver, `/downloads/clean-copy-obsidian-v1.0.10.zip` indeholder `main.js` med `clean-copy-pro` og `mahope.tools`, `license.js` i begge browserarkiver har `API_BASE = 'https://mahope.tools/api/license'`, de fire gamle arkiver svarer 404, og `/clean-copy` + `/downloads` viser 1.5.3 og 1.0.10. CI's egen post-deploy-gate skal være grøn for alle tre domæner. **Lukket 25/9:** `DEPLOY OK 3289b5b` ovenfor verificerer præcis disse tre arkiver (200) og de fire gamle (404). Noten havde aldrig fået sit merge-commit indsat — `<merge-sha>` stod stadig som pladsholder, fordi den var skrevet før committen fandtes.

- 2026-09-25: `DEPLOY OK 3289b5b`

- 2026-09-25: `DEPLOY OK 3289b5b` — GitHub Actions-run `36173523329` byggede, gatede, deployede og live-verificerede cleancopy.tools, deskuptime.com og mahope.tools grønt. De nye gatekommandoer `check_clean_copy_distribution.py` + `--self-test` kørte i alle tre jobs. Indholdskontrol: `cleancopy.tools/downloads/clean-copy-v1.5.3.zip`, `clean-copy-firefox-v1.5.3.zip` og `clean-copy-obsidian-v1.0.10.zip` svarer 200; de fire gamle arkiver (1.5.2 ×2, 1.0.9, 1.0.6) svarer 404, så ingen kan længre hente licenskode med det døde endepunkt. **Fire 404 fundet samtidig:** `mahope.tools/downloads/clean-copy-*.zip` giver 404, fordi arkiverne kun publiceres på cleancopy.tools mens `site/downloads.html` ligger på mahope.tools med rodrelative links. Det er ældre end denne iteration og er oprettet som opgave 8.
- 2026-09-25: `DEPLOY OK 7e2b883` — GitHub Actions-run `36170930593` byggede, deployede og live-verificerede cleancopy.tools, deskuptime.com og mahope.tools grønt. Alle domæners live `build-info.json` bærer `7e2b88302cbbd35d6841ae051f90f6d48662ccab`. Indholdskontrol: live `/clean-copy-tool` på cleancopy.tools indeholder begge markører om det indlejrede licensmodul, modulet er byte-identisk med `tools/clean_copy_license.js`, siden kalder `decide()`, og den gamle `clearPro()`-på-alt er væk; live `/compliance-report` på mahope.tools sender `eucomply-pro`. CI's egen post-deploy-gate meldte grønt for alle tre.
- 2026-09-25: `VERIFICÉR DEPLOY ( lukket af ovenstående ): webværktøjets syvdagesregel og compliance-rapportsidens product 8207ca1 2026-09-25` — GitHub Actions kører automatisk, fordi `site/clean-copy-tool.html` og `site/compliance-report.html` er i path-filteret. Verificér på live: `cleancopy.tools/clean-copy-tool` (og `mahope.tools/clean-copy-tool`) har det indlejrede licensmodul mellem `/* >>> clean-copy-license …` og `/* <<< clean-copy-license */`, og `mahope.tools/compliance-report` sender `product: 'eucomply-pro'` i sit validate-kald. Det kan ses direkte i sidens JS.

- 2026-09-25: `INGEN DEPLOY FORVENTET — 55fbe15` — mergecommit for opgave 7 del 1 rørte kun `obsidian-plugin/main.js`, `extension-clean-copy*/`, `test.js` og to nye filer i `tools/`. Ingen af dem står i deploy-workflowens path-filter, så GitHub Actions udløste ikke (bekræftet read-only: seneste run er `36166003612` fra `badefa2`). Live-sitet er derfor uændret, og det er korrekt: de publicerede zips i `site/downloads/` er endnu den gamle kode, hvilket er præcis opgave 7 del 2. **Verificér ikke live — intet er deployet.** Nær del 2 pakker nye arkiver, skal deploys køre og de nye `/downloads/*.zip` verificeres for indhold (HTTP 200 og byte-identisk `options.js` med `product`).

- 2026-09-25: `DEPLOY OK badefa2` — GitHub Actions-run `36166003612` byggede, deployede og live-verificerede cleancopy.tools, deskuptime.com og mahope.tools grønt, inklusive de to nye gatekommandoer (`check_page_profile_distribution.py` + `--self-test`) og `page-profile/test_page_profile.py` i gate-trinet. Uafhængig `check_live_sitemaps.py --commit badefa2…` meldte `live sitemap OK` for alle tre domæner. Indholdskontrol: live `/downloads/page-profile/page_profile.py` er byte-identisk med `page-profile/page_profile.py` i repoet, live `/page-profile` nævner 1.2.0 og ingen 1.1.0, og live `/da/page-profile` har ingen offline-påstand og siger syvdages cache. Deployen ændrede intet site-indhold, som forventet — denne iteration tilføjede holdningen, ikke en funktion.

- 2026-09-25: `DEPLOY OK 17f5213` — GitHub Actions-run `36164514430` byggede, deployede og live-verificerede cleancopy.tools, deskuptime.com og mahope.tools grønt, inklusive den nye `check_private_content.py`-gate i gate-trinet. Alle tre live `build-info.json` bærer `17f5213a8dcfb4726b169c72db2654a11dae1df5`, og uafhængig `check_live_sitemaps.py --commit 17f5213…` meldte `live sitemap OK` for alle tre. Indholdskontrol: live `/sitemap.xml` på mahope.tools har ingen af de 16 betalte leveringsfilnavne (kun salgssiden `/books/compliance-bundle`, som er en route, ikke et fil), og live `/compliance-report/` har nul fund af et betalt filnavn. Deployen ændrede intet site-indhold, som forventet.

- 2026-09-25: `DEPLOY OK aa8bf32` — GitHub Actions-run `36160847300` lykkedes, og alle tre live `build-info.json` bærer `aa8bf32`. Indholdskontrol: live `/support` og `/terms/` har kundeportalen, live `/thanks` renderer den fra leveringssvaret, og den gamle påstand om ingen fornyelser findes ikke live. CI meldte kun kendte ubuntu-latest-advarsler.
- 2026-09-25: `VERIFICÉR DEPLOY ( lukket af ovenstående ): Stripe-kundeportalen for de tre årlige produkter (tak-side, mail, support, vilkår) aa8bf32 2026-09-25` — GitHub Actions kører automatisk, fordi `site/_worker.js`, `site/thanks.html`, `site/support.html`, `site/terms/index.html` og `tools/stripe_catalog.json` er i path-filteret. Verificér på live: `mahope.tools/thanks` (kræver en rigtig session), `/support` og `/terms/` viser kundeportalen, og live `build-info.json` bærer `aa8bf32`. Bemærk: portal-URL'en er statisk på de to sider, så den kan findes i live-HTML; på `/thanks` ligger den i JS'en, ikke som statisk anker.

- 2026-09-25: `DEPLOY OK 3fe72c3` — GitHub Actions-run `36159004578` byggede, deployede og live-verificerede cleancopy.tools, deskuptime.com og mahope.tools grønt. Uafhængig `check_live_sitemaps.py --commit 3fe72c3…` (kørt fra et checkout af netop deploy-committen, jf. fælden nedenfor) meldte `live sitemap OK` for alle tre domæner, og alle tre live `build-info.json` bærer `3fe72c3ad72c14fabda60ac84730de618afb2a46`. Indholdskontrol: `privacy/`, `terms/` og `license-lookup` på mahope.tools indeholder kun `support@mahope.tools` og nul fund af den private indbakke, og hvert domænes `.well-known/security.txt` har `Contact: mailto:support@<sit domæne>`.
- 2026-09-25: **Observeret fælde #2 — Cloudflare e-mail-obfuscering.** Live `/privacy/`, `/terms/` og `/license-lookup/` indeholder ikke `support@mahope.tools` i klar tekst: Cloudflare Pages erstatter alle mailto'er med `/cdn-cgi/l/email-protection#…` og en `data-cfemail`-attribut. En naiv `grep` på live-HTML giver derfor 0 fund på både den nye og den gamle adresse og kan fejltolkes som "ændringen ikke er live". Korrekt live-verifikation er at afkode `data-cfemail` (XOR med første byte) eller sammenligne mod dist-bytes. Samme forvriddring gælder alle eksisterende mailto'er på de tre Pages-domæner.

- 2026-09-25: `VERIFICÉR DEPLOY: produkternes egne support-adresser i leveringsmail, privacy/terms, licens-opslag og security.txt 3fe72c3 2026-09-25T18:12+02:00` — GitHub Actions-run `36159004578` kører, udløst af `site/`, `site/_worker.js` og `build_sites.py` i path-filteret. Verificér på live: `mahope.tools/privacy/`, `/terms/` og `/license-lookup` viser `support@mahope.tools` og ingen `mads@mahope.dk`; hvert af de tre Pages-domæners `.well-known/security.txt` har `Contact: mailto:support@<sit domæne>`; live `build-info.json` bærer commit `3fe72c3`. `_worker.js` er identisk i alle tre dist, så reply_to-logikken er live i samme deploy.

- 2026-09-25: `DEPLOY OK 2528300` — GitHub Actions-run `36157042428` byggede, deployede og live-verificerede cleancopy.tools, deskuptime.com og mahope.tools grønt. CI's egen post-deploy-gate meldte `live sitemap OK` for alle tre domæner, og alle tre live `build-info.json` bærer commit `2528300`. CI kørte desuden de fulde gates i byggetrinene: `check_live_sitemaps`-tests OK, `check_sitemaps` OK, Stripe-worker 57/57, tracking-worker 83/83, inline-JS OK og `check_stripe_ctas` `problems: 0`. Kun kendte Node 20-/Ubuntu 26-advarsler.
- 2026-09-25: `VERIFICÉR DEPLOY: datadrevet konverteringsrangering (ranking_basis, syv fulde dage, 14 synlige købsruter) 2528300 2026-09-25T17:52+02:00` — GitHub Actions-run `36157042428` kører, udløst af `tools/weekly_report.py` + `tools/test_weekly_report.py` i path-filteret. Ingen `site/`-fil er rørt, så live-indholdet skal være uændret; kontrollér at live `build-info.json` bærer commit `2528300` og at de tre Pages-domæner fortsat er grønne.
- 2026-09-25: **Observeret fælde** — den lokale `check_live_sitemaps.py --commit <HEAD>` fejlede efterfulgtende på `build-info.json` for alle tre domæner. Årsagen er ikke et deploy-problem: `db18346` (deploy-noten til denne plan) er en ren dokumentationscommit, og `IMPLEMENTATION_PLAN.md` ligger *ikke* i workflowens path-filter, så den deployer aldrig. `build_sites.py` stempler dog det aktuelle HEAD i `build-info.json`, så et lokalt byg efter en docs-only commit kan aldrig matche live. Løsning indtil videre: kør den lokale live-kontrol mod den SHA, der faktisk blev deployet (eller genkør `build_sites.py` på den deployede commit). Uden en sådan regel er en grøn deploy let at tolke som rød.
- 2026-09-25: `DEPLOY OK 1bf981f` — GitHub Actions-run `36153509552` byggede og deployede cleancopy.tools, deskuptime.com og mahope.tools grønt. Live-indholdskontrol bekræfter de ærlige claims: `/compliance-report` viser kun Report Kit $69 og EUComply Pro $79/år, `/scan` og `/scan-da` linker til Report Kit, `/site-icons` og `/downloads` siger at der ikke findes en Pro-licens, og `/` + `/da/` har ingen checkout-påstand længere. Ingen "store launches" eller "Pro is coming" fandtes live.
- 2026-09-25: `VERIFICÉR DEPLOY: kun tilladte Stripe-links, 15 dokumenterede købssider og ærlige Pro-claims 1bf981f 2026-09-25T17:25+02:00` — GitHub Actions-run `36153509552` kører. Verificér på live: `site/compliance-report.html` viser Report Kit $69 + EUComply Pro $79/år og ingen "store launches"; `site/scan.html` og `/scan-da` linker til Report Kit; `site/site-icons.html` og `site/downloads.html` har ingen Pro-pris; `site/index.html` og `/da/` har ingen "checkout ikke koblet på".

- 2026-09-25T14:15:28Z: `DEPLOY OK 4ad9457` — GitHub Actions-run `36146060595` deployede cleancopy.tools, deskuptime.com og mahope.tools grønt; uafhængig `check_live_sitemaps.py --commit 4ad9457235887f05d2e7723cc184e8956a50444a` bekræftede live sitemap, robots, build-info og alle sider. Live `/activate/` viste den nye guide.
- 2026-09-25: `DEPLOY OK ea4e6c3` — GitHub Actions-run `36142200546` byggede, deployede og live-verificerede cleancopy.tools, deskuptime.com og mahope.tools grønt. Uafhængig sitemap-kontrol bekræftede alle tre domæner; live 1.2.0-script, tarball, EN/DA-licenstekst og 404 på det gamle 1.1.0-arkiv blev verificeret. CI meldte kun kendte Node 20-/Ubuntu 26-advarsler.
- 2026-09-25: `DEPLOY OK 9569979` — GitHub Actions-run `36133997658` byggede, deployede og live-verificerede cleancopy.tools, deskuptime.com og mahope.tools grønt. Uafhængig `check_live_sitemaps.py --commit 956997979390f5b0b28e3c8359350e581937e7fb` bekræftede alle tre domæner; live `/stats` viste den nye token-prompt uden tredjepartsscript, og det gamle URL-token gav 401. CI meldte kun kendte Node 20-/Ubuntu 26-advarsler.
- 2026-09-25: `DEPLOY OK b7c8a64` — GitHub Actions-run `36099316657` byggede, deployede og live-verificerede cleancopy.tools, deskuptime.com og mahope.tools grønt. Uafhængig `check_live_sitemaps.py --commit b7c8a64` bekræftede byte-identiske robots/sitemap/build-info og alle 288 sitemap-sider; CI meldte kun eksisterende Node 20-/Ubuntu 26-advarsler.
- 2026-09-25T07:37:10+02:00: `VERIFICÉR DEPLOY: korrigeret Wrangler-sti og JSON-LD-gate b7c8a64 2026-09-25T07:37:10+02:00`
- 2026-09-25T07:27:55+02:00: `VERIFICÉR DEPLOY: domænekorrekt robots/sitemap og tre Pages-domæner fb4189d 2026-09-25T07:27:55+02:00`
- 2026-09-25T05:28:41Z: `DEPLOY FEJL 36098659762` — alle tre Pages-deploysteps lykkedes, men post-deploy-gaten fejlede lokalt, fordi `wrangler-action` installerede `node_modules` i hver `dist/<domæne>`. En uafhængig live-kontrol bekræftede de nye robots/sitemap/build-info, men fandt ugyldig JSON-LD på `/blog/html-table-to-csv-converter`; korrigerende commit `b7c8a64` blev efterfølgende grøn live.
- 2026-09-25: Researchiterationen ændrer kun `IMPLEMENTATION_PLAN.md`. Deploy-workflowens path-filter forventes derfor ikke at udløse en site-deploy. Efter merge/push kontrolleres GitHub Actions read-only, og der tilføjes en `VERIFICÉR DEPLOY`-note kun hvis workflowen alligevel kører.
- 2026-09-25: `DEPLOY OK 28c7f64` — GitHub Actions-run `36076793409` deployede alle fire sites grønt. Live GET og POST på `/api/lemon-webhook` gav `404` på `cleancopy.tools`, `deskuptime.com`, `bugbottle.dev` og `mahope.tools`; de tre Worker-domaener returnerede `Not found`, mens BugBottle returnerede sit nginx-404-svar. CI meldte kun eksisterende Node 20-/Ubuntu-26-advarsler.
- 2026-09-25: `DEPLOY OK 41758af` — GitHub Actions-run `36082138701` deployede alle fire sites grønt. Live-contentcheck af de fire EN/DA-sider fandt de nye licens- og lokalitetsoplysninger, mens de gamle claims var fraværende. CI meldte kun eksisterende Node 20-/Ubuntu-26-advarsler.

## Commitlog

- Sælg ikke filer, der ikke kan leveres: `ceo/levering-uden-fil` — `Sælg ikke filer, der ikke kan leveres` (22).
- Læs versionserklæringen inde i de publicerede byggeoutput-arkiver: `ceo/aab-indre-version` — `Læs versionserklæringen inde i de publicerede byggeoutput-arkiver` (19).
- Electron 44.0.0 → 44.4.5 og én erklæret Node-version: `ceo/desktop-node-runtime` — `Erklær desktopens runtime ét sted og opgradér Electron` (12).
- CI kører den dokumenterede kvalitetsgate, ét sted: `ceo/ci-runs-real-gate` — `Kør den dokumenterede kvalitetsgate i CI` (11).
- electron-builder 25 → 26.15.3, advisory-fundene lukket: `ceo/electron-builder-26` — `Opgradér electron-builder og luk advisory-fundene` (9).
- Bevis hvilket domæne der publicerer hvilket Clean Copy-arkiv: `ceo/clean-copy-publish-targets` — `Bevis hvilket domæne der publicerer Clean Copy-arkiverne` (8).
- Publicerede Clean Copy-arkiver fra kilden: `ceo/clean-copy-archives` — `Pak Clean Copy-arkiverne reproducerbart fra kilden` (7 del 2 pkt. 2).
- Clean Copy-klienter på licenskontrakten: `ceo/clean-copy-delivery` — `Hold Clean Copy-klienterne på licenskontrakten` (7 del 2 pkt. 1, 3, 4).
- Clean Copy-licensklienter Stripe-kompatible: `ceo/clean-copy-license-clients` — `Gør Clean Copy-licensklienterne Stripe-kompatible` (7 del 1).
- Page Profile-distributionen bevogtet: `ceo/page-profile-distribution` — `Hold den publicerede Page Profile-kopi på linjen` (6).

- Betalt indhold ude af det offentlige repo: `ceo/private-content-gate` — `Hold betalt indhold ude af det offentlige repo` (5).

- Support- og svaradresser per produkt: `ceo/support-reply-routing` — `Send kundehenvendelser til produkternes egne support-adresser` (4C).

- Datadrevet konverteringsrangering: `ceo/ranking-basis` — `Rangér Pro-sider på syv fulde dage` (4B del 2).
- Licensrefunding og Clean Copy-aktivering: `4ad9457` — `Ret licensrefunding og Clean Copy-aktivering`.
- Stripe-kompatibel Page Profile-licens: `ea4e6c3` — `Ret Page Profile Stripe-licensen`.
- Domæneopdelt trafik- og salgsledger: `df25c8b` — `Gør trafikdata domæneopdelt og troværdige`.
- Fail-closed review-rettelser: `9569979` — `Gør trafikledgeren fail-closed`.
- Research og initial plan: `10c5908` — `Lav en prioriteret plan for næste Hermes-iterationer`.
- Fjern død Lemon-webhook: `28c7f64` — `Fjern den døde Lemon-webhook`.
- Gør DeskUptime-teksten sand: `41758af` — `Gør DeskUptime-teksten sand`.
- Gør robots, sitemap og domænedrift korrekt: `fb4189d` — `Gør robots, sitemap og domænedrift korrekt`.
- Ret deploy-gaten efter Wrangler-forurening: `b7c8a64` — `Ret deploy-gaten efter Wrangler-forurening`.
