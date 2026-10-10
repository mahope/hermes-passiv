#!/usr/bin/env python3
"""Den dokumenterede kvalitetsgate, som én kørsel.

Baggrund (opgave 11, 25. september 2026): gaten var dokumenteret som en lang
`&&`-linje i `IMPLEMENTATION_PLAN.md`, mens CI kørte en **anden og mindre** liste
i hvert matrix-job. Tre af de dokumenterede kommandoer kørte aldrig i CI
(`check_license_clients`, `check_product_copy`, `check_stripe_ctas`), to kørte
kun halvt (`--self-test` manglede for to selftester), og licensklienternes 103
checks (`node test.js`) kørte slet ikke. To filer i path-filteret var ikke ens
med de filer, gaten faktisk læser: `tools/make_blog_da_mirrors_461.py` (som
`check_product_copy.py` importerer) og `docs/stripe-kontrakt.md` (som
`check_stripe_ctas.py` læser) kunne ændre sig uden at nogen kørsel så det.

Denne fil løser det på den eneste måde, der holder: **én liste, én ejerskab.**
CI kalder `python3 tools/quality_gate.py`, og `tools/test_deploy_workflow.py`
beviser bagefter tre ting om CI's egen definition af den liste:

1. Deploy-workflowen kører denne gate, og alle deploy-jobs afhænger af jobbet
   der gør det — så en fælles gatefejl ikke sender tre matrixjobs videre.
2. Hvert `inputs`-mønster fra hvert step matcher path-filteret, så en ny
   gatekommando uden sin fil i filteret er en rød port frem for en stille
   udeladelse.
3. `auditedwp` er pinnet til én 40-tegns SHA i alle jobs.

`inputs` er bevidst *konservativt*: en mangel giver en falsk rød port, en
overangivelse giver en ekstra kørsel. Derfor står hvert mønster med sin
begrundelse, og listen er ikke autogenereret — en autogenereret liste ville
være lige så upræcis som den, den afløser.

    python3 tools/quality_gate.py             # hele gaten: build + alle checks
    python3 tools/quality_gate.py --list      # den dokumenterede kommandolinje
    python3 tools/quality_gate.py --inputs    # alle filer der skal være i filteret
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Step:
    """Ét gatestræk: kommando, og de filer der kan gøre den rød."""

    id: str
    argv: tuple[str, ...]
    inputs: tuple[str, ...] = field(default=())
    # Steps der læser `dist/` springes over, når intet er bygget — samme mønster
    # som `check_links.py` og `check_clean_copy_distribution.py`, så porten
    # kan bruges på et delvis bygget checkout uden at lyve om grønt.
    needs_dist: bool = False

    @property
    def command(self) -> str:
        return " ".join(self.argv)


# --------------------------------------------------------------------------
# Gaten. Rækkefølgen er billigst-først: build, derefter de checks der kun
# læser `dist/`, til sidst de der læser hele repoet. Første røde step dræber
# kørslen, som `&&` gjorde — det er hele pointen med at samle den.
# --------------------------------------------------------------------------
STEPS: tuple[Step, ...] = (
    Step(
        id="build",
        argv=("python3", "build_sites.py"),
        # `build_sites.py` importerer brand, pagepass og route_inventory, og
        # læser historik for datePublished — derfor fetch-depth: 0 i CI.
        inputs=(
            "build_sites.py",
            "site/**",
            "bugbottle-landing/**",
            "tools/brand.py",
            "tools/pagepass.py",
            "tools/route_inventory.py",
            "tools/route_inventory.json",
        ),
    ),
    Step(
        id="sitemaps",
        argv=("python3", "tools/check_sitemaps.py"),
        inputs=(
            "build_sites.py",
            "tools/check_sitemaps.py",
            "tools/route_inventory.py",
            "tools/route_inventory.json",
        ),
        needs_dist=True,
    ),
    # Opgave 90: de to unittest-filer under `tools/` lå i path-filteret, så en
    # rettelse i dem udløste gaten — men ingen kørte dem. De var filer der så ud
    # som en port og var det ikke, og det er grunden til at `check_sitemaps.py`
    # kunne være grøn med en robots.txt der pegede på filer builden ikke
    # publicerer. De får hvert sit step, som de andre teststeps.
    Step(
        id="sitemaps-tests",
        argv=("python3", "tools/test_check_sitemaps.py"),
        inputs=(
            "tools/test_check_sitemaps.py",
            "tools/check_sitemaps.py",
            "tools/route_inventory.py",
            "tools/route_inventory.json",
        ),
    ),
    Step(
        id="live-sitemaps-tests",
        argv=("python3", "tools/test_check_live_sitemaps.py"),
        inputs=(
            "tools/test_check_live_sitemaps.py",
            "tools/check_live_sitemaps.py",
            "tools/check_sitemaps.py",
            # Opgave 32: porten fik sin egen `is_transient` 30/9, fordi den ikke
            # delte kode med `weekly_report.py` — og de to var uenige om 429.
            # Beslutningen ligger nu ét sted, så dens fil er input her.
            "tools/transient.py",
        ),
    ),
    # Opgave 32: `weekly_report.py` og `check_live_sitemaps.py` havde hver sin
    # `_transient` og var uenige om 429, så den samme udgivelse kunne være «brudt»
    # i den ene port og «sund» i den anden. Reglen ligger nu i `tools/transient.py`
    # og dømmes i sit eget step, der desuden beviser at ingen af de to scripts
    # dømmer 429 selv. Uden denne fil i filteret kunne en push kun tilføje et tredje
    # sted med sin egen regel og springe prøven over — samme krav som portenes
    # egne filer ovenfor.
    Step(
        id="transient-tests",
        argv=("python3", "tools/test_transient.py"),
        inputs=(
            "tools/test_transient.py",
            "tools/transient.py",
            "tools/check_live_sitemaps.py",
            "tools/weekly_report.py",
        ),
    ),
    Step(
        id="seo",
        argv=("python3", "tools/seo_check.py"),
        inputs=("tools/seo_check.py", "build_sites.py"),
        needs_dist=True,
    ),
    # Selvtesten til seo_check. Den dækker dublet-id-reglen og dens rodårsag i
    # build_sites._toc. Den kommer som sit eget step, men dens inputs ligger
    # allerede i path-filteret via `seo`, så filteret er uændret — samme krav som
    # opgave 31, 42 og 45.
    Step(
        id="seo-selftest",
        argv=("python3", "tools/seo_check.py", "--self-test"),
        inputs=("tools/seo_check.py", "build_sites.py"),
    ),
    # Bogenes læsevisning. `build_sites.py` skriver de første kapitler ind i
    # hver bogsides HTML, bygget ud af `ebook/<slug>.epub` — altså den fil
    # kunden faktisk henter. Uden dette step kunne en EPUB blive ulæselig, en
    # kapiteltitel forsvinde, eller markup fra bogen blive levende tags på siden,
    # og buildet ville stadig være grønt: ingen anden port læser `ebook/`.
    Step(
        id="book-reader",
        argv=("python3", "tools/book_reader.py", "--self-test"),
        inputs=(
            "tools/book_reader.py",
            "build_sites.py",
            "ebook/**",
        ),
    ),
    # Licensserveren. `_worker.js` leverer nøgler og downloads for rigtige
    # Stripe-køb, så dette step må aldrig droppes fra en kortere liste.
    Step(
        id="stripe-worker",
        argv=("node", "tests/stripe-worker.test.mjs"),
        inputs=(
            "tests/stripe-worker.test.mjs",
            "site/_worker.js",
            "tools/stripe_catalog.json",
            "tools/paid_content.json",
        ),
    ),
    # Samme suite igen, men med et ur der springer én time for hvert kald.
    # `rateLimitIp` tæller i hele time-bøtter, og `sentryRateLimited` har et
    # glidende vindue på 12 sekunder, så «over grænsen»-sløjferne var
    # afhængige af hvornår de kørte: CI-push 2/10 kl. 04:59:41 ramte
    # timegrænsen 05:00:00 midt i rapport-sløjfen og fik 200 i stedet for 429.
    # Rødt CI-run, der så ud som en fejl i licenserveren. Dette step gør den
    # afhængighed til en målt egenskab: en ny tællertest uden fast ur går rød
    # her, ikke tilfældigt i en nattlig kørsel.
    #
    # Hoptrinnet er pr. kald og ikke pr. millisekund, så porten er
    # deterministisk: et ur der sprang en time hvert 30. ms ramte 2/10 kl.
    # 06:03 desuden en webhook-signatur mellem signering og verifikation
    # (300 s tolerance i `verifyStripeSignature`) og lavede et andet rødt run.
    Step(
        id="stripe-worker-ur",
        argv=("node", "tests/clock_jump.mjs"),
        inputs=(
            "tests/clock_jump.mjs",
            "tests/stripe-worker.test.mjs",
            "site/_worker.js",
        ),
    ),
    # Tak-siden. Den er den eneste bekræftelse en donator får, og den renderer
    # worker's leveringssvar. Uden dette step var der ingen test, der viste at
    # den overhovedet kan vise et svar (opgave 33).
    Step(
        id="thanks-page",
        argv=("node", "tests/thanks-page.test.mjs"),
        inputs=("tests/thanks-page.test.mjs", "site/thanks.html", "site/_worker.js"),
    ),
    # Nøgleopslaget. `/api/license/lookup` var fuldt implementeret og testet,
    # men ingen side kaldte den: `/license-lookup` — sidens hele formål — sagde
    # "skriv til support@mahope.tools". Det er menneskelig support i en indtægt,
    # der skal klare sig uden. Uden dette step kan en sådan klient forsvinde
    # igen, fordi ingen port måler om et endpoint har en indgang.
    Step(
        id="license-lookup-page",
        argv=("node", "tests/license-lookup.test.mjs", "site/license-lookup.html"),
        inputs=("tests/license-lookup.test.mjs", "site/license-lookup.html"),
    ),
    Step(
        id="tracking-worker",
        argv=("node", "tests/tracking-worker.test.mjs"),
        inputs=("tests/tracking-worker.test.mjs", "site/_worker.js"),
    ),
    # /api/checkout er den eneste rute der udsteder et købslink. Den lå med
    # `which = … : 'cc'`, så `?product=deskuptime-pro` — den product_key Stripe
    # selv bruger — svarede med Clean Copys link, pris og navn, og et produkt
    # ruten ikke kendte gav Clean Copy i stedet for at sige "kan ikke".
    # Beløb, periode og link lå desuden håndskrevet i workeren uden at være
    # dømt mod `tools/stripe_catalog.json`.
    Step(
        id="checkout-route",
        argv=("node", "tests/checkout-route.test.mjs"),
        inputs=(
            "tests/checkout-route.test.mjs",
            "site/_worker.js",
            "tools/stripe_catalog.json",
        ),
    ),
    # De to gratis scanningsværktøjer. De kalder vores egen worker, og en 5xx
    # fra den er ikke et netværksproblem — det var den gamle tekst, og den gav
    # op ved det første blip. Uden dette step var der ingen test, der viste at
    # siderne skelner de to.
    Step(
        id="scan-clients",
        argv=("node", "tests/scan-clients.test.mjs"),
        inputs=(
            "tests/scan-clients.test.mjs",
            "site/net.js",
            "site/compliance-site-check.html",
            "site/da/compliance-site-check.html",
            "site/page-profile.html",
            "site/da/page-profile.html",
            "site/security-headers-check.html",
            "site/url-inspector/index.html",
        ),
    ),
    # Del-linket i farveblindhedssimulatoren (EN + DA). Siderne deler én codec i
    # `site/cb-share-core.js`, så dommen læser den kode der faktisk ships og
    # begge siders eget script — en dansk kopi der falder fra ville ellers bare
    # se ud til at virke på den engelske.
    Step(
        id="cb-share",
    argv=("node", "tests/cb-share.test.mjs"),
    inputs=(
        "tests/cb-share.test.mjs",
        "site/cb-share-core.js",
        "site/color-blindness-simulator.html",
        "site/color-blindness-simulator-da.html",
    ),
    ),
    # Forhåndsvisningen i farveblindhedssimulatoren (EN + DA). Den lå sort på
    # sort i det øjeblik siden indlæses, fordi `fillSelect` kasserte den hvide
    # standard og satte palettens sidste farve i stedet — samme farve som
    # teksten, altså 1.00:1 mod WCAG's 4.5:1. Samme linje kastede desuden
    # `TypeError`, når den sidste farve blev slettet, så «slet alle» dræbte
    # knappen. Dommen læser begge *rigtige* sider, som `cb-share` gør, fordi den
    # danske er en håndhævede kopi.
    Step(
        id="cb-preview",
        argv=("node", "tests/cb-preview.test.mjs"),
        inputs=(
            "tests/cb-preview.test.mjs",
            "site/cb-share-core.js",
            "site/color-blindness-simulator.html",
            "site/color-blindness-simulator-da.html",
        ),
    ),
    # Billed-simuleringen i farveblindhedssimulatoren (EN + DA). Farve-tabellen
    # kunne kun simulere et par hex-felter, mens de store simulatorer kan tage et
    # skærmbillede eller et logo — det hul lukkes af `site/cb-image.js`, som
    # tegner den *samme* Machado-model pr. pixel. Dommen kræver at pixel-løkken
    # giver præcis samme RGB som `CB_SIM.simulate`, den funktion tabellen selv
    # bruger, så der ikke kan opstå to modeller på én side. Begge *rigtige*
    # sider læses, fordi den danske er en håndhævet kopi.
    Step(
        id="cb-image",
        argv=("node", "tests/cb-image.test.mjs"),
        inputs=(
            "tests/cb-image.test.mjs",
            "site/cb-image.js",
            "site/color-blindness-simulator.html",
            "site/color-blindness-simulator-da.html",
        ),
    ),
    # Kontrasten pr. synstype i farveblindhedssimulatoren (EN + DA). Tabellen og
    # forhåndsvisningen viste hvordan farverne *ser ud*, men ikke WCAG-forholdet
    # for hver synstype — og et par kan bestå AA for normalt syn og falde under
    # 4.5:1 for en deuteranop. `site/cb-contrast.js` regner det tal med den
    # samme `CB_SIM.simulate` som tabellen bruger. Dommen har sin egen
    # luminans-implementering og kræver præcis samme forhold, og den læser begge
    # *rigtige* sider, fordi den danske er en håndhævet kopi.
    Step(
        id="cb-contrast",
        argv=("node", "tests/cb-contrast.test.mjs"),
        inputs=(
            "tests/cb-contrast.test.mjs",
            "site/cb-contrast.js",
            "site/cb-image.js",
            "site/cb-share-core.js",
            "site/color-blindness-simulator.html",
            "site/color-blindness-simulator-da.html",
        ),
    ),
    # APCA-scoren på kontrasttjekkeren (EN + DA). WCAG 2-forholdet er blindt for
    # polaritet, og WCAG 3-udkastet bygger på APCA i stedet. `site/apca.js` er
    # referenceimplementeringen 0.1.9 (W3), og dommen holder dens Lc-tal op mod
    # `apca-w3`'s egen testsuite samt begge *rigtige* sider, fordi den danske er
    # en håndhævet kopi.
    Step(
        id="apca",
        argv=("node", "tests/apca.test.mjs"),
        inputs=(
            "tests/apca.test.mjs",
            "site/apca.js",
            "site/contrast-checker.html",
            "site/contrast-checker-da.html",
        ),
    ),
    # Farverne ud af et billede i paletgeneratoren (EN + DA). Generatoren tog
    # kun en hexfarve ind, men de fleste har deres brandfarve i et logo eller et
    # skærmbillede. `site/palette-image.js` læser billedet med canvas og
    # trækker de dominerende farver ud. Dommen kalder den rene `extract()` på et
    # kendt pixel-array og læser begge *rigtige* sider, fordi den danske er en
    # håndhævet kopi.
    Step(
        id="palette-image",
        argv=("node", "tests/palette-image.test.mjs"),
        inputs=(
            "tests/palette-image.test.mjs",
            "site/palette-image.js",
            "site/palette-generator.html",
            "site/palette-generator-da.html",
        ),
    ),
    # Farvenavnet ved siden af hex i paletgeneratoren (EN + DA). Generatoren
    # regner i hex, men en ikke-designer taler om «den blå»; `site/color-names.js`
    # bærer de 139 forskellige CSS-farver og vælger den nærmeste. Dommen kalder
    # den rene `nearestName()` på kendte hexer — også de nære par, hvor «den
    # første række» ville være forkert (`#00ff00` er lime, ikke green) — og læser
    # begge *rigtige* sider, fordi den danske er en håndhævet kopi.
    Step(
        id="color-names",
        argv=("node", "tests/color-names.test.mjs"),
        inputs=(
            "tests/color-names.test.mjs",
            "site/color-names.js",
            "site/palette-image.js",
            "site/palette-generator.html",
            "site/palette-generator-da.html",
        ),
    ),
    # Del-linket i paletgeneratoren (EN + DA). En palet — én basisfarve og én
    # baggrund — døde med fanen, fordi værktøjet kører helt i browseren. Staten
    # bor nu i fragmentet via `site/palette-share-core.js`, som begge sprog
    # deler, så de to kopier ikke kan drive fra hinanden. Dommen læser codecen
    # og begge *rigtige* sider, fordi den danske er en håndhævet kopi: et link
    # der ikke kan gendanne basen og baggrunden, eller en side der har sin egen
    # decoder, går rød her.
    Step(
        id="palette-share",
        argv=("node", "tests/palette-share.test.mjs"),
        inputs=(
            "tests/palette-share.test.mjs",
            "site/palette-share-core.js",
            "site/palette-generator.html",
            "site/palette-generator-da.html",
        ),
    ),
    # Del-linket på EAA/WCAG-scanneren (EN + DA). Før dette kopierede
    # `shareResult()` kun URL'en, så den der modtog linket så en tom formular
    # og skulle trykke Scan selv — og brugte sin *egen* kvote på en side, der
    # måske var ændret siden. Fundene ligger nu i fragmentet via
    # `site/scan-share-core.js`, som begge sprog deler. Dommen læser codecen
    # og begge *rigtige* sider, fordi den danske er en håndhævede kopi: kun
    # id, alvor og antal rejser i linket, så teksten slås op i sidens egen
    # MSG-tabel og et håndredigeret link aldrig kan skrive sine egne ord.
    Step(
        id="scan-share",
        argv=("node", "tests/scan-share.test.mjs"),
        inputs=(
            "tests/scan-share.test.mjs",
            "site/scan-share-core.js",
            "site/scan.html",
            "site/scan-da.html",
        ),
    ),
    # 1/10: `formatAnswer()` på `/compliance-ai` (EN + DA) skrev modellens svar
    # direkte i `innerHTML` med kun markdown-udskiftninger. Svaret er bygget af
    # det besøgende skrev i feltet, så `<img src=x onerror=…>` kunne blive til
    # levende markup på mahope.tools — samme origin som licensnøglerne i
    # localStorage. `fmt()` i book-ai.js escaped allerede før markdown, så mønsteret
    # fandtes i repoet og var blot glemt de to steder.
    #
    # Testen dømmer adfærd: den trækker `formatAnswer` ud af de shippede bytes og
    # kører den i en vm med fjendtlige strenge, så den kan ikke reddes ved at
    # omdøbe funktionen. Den har desuden en mutation mod koden fra før
    # rettelsen, så den ikke kan være grøn uden at have dømt noget.
    Step(
        id="markdown-escape",
        argv=("node", "tests/markdown-escape.test.mjs"),
        inputs=(
            "tests/markdown-escape.test.mjs",
            "site/compliance-ai.html",
            "site/da/compliance-ai.html",
        ),
    ),
    # 30/9: otte generatorer lå i live med en død inline-script-blok. Kilden
    # var i orden — *bygget* skrev shell- og BugBottle-tags ind i den JS-streng,
    # som er den fil siden downloader, så browseren stoppede scriptet ved det
    # første `</body>`. `check_inline_js` læste kun `site/` og sagde «problems:
    # 0». Den dømmer nu begge træer, så en fejlform der kun opstår under
    # buildet kan ikke være usynlig.
    #
    # `inputs` lister derfor de filer der bestemmer `dist/`, ikke bare
    # `site/**`: en rettelse i `build_sites.py` eller `pagepass.py` ændrer det
    # publicerede output, og uden dem her ville præcis den push der kan gøre
    # en side død springe den port over der ser det. Samme krav som de andre
    # `needs_dist`-steps.
    Step(
        id="inline-js",
        argv=("python3", "tools/check_inline_js.py"),
        inputs=("tools/check_inline_js.py", "site/**", "site/_worker.js",
                "build_sites.py", "tools/pagepass.py", "tools/brand.py",
                "tools/route_inventory.py", "tools/route_inventory.json",
                "bugbottle-landing/**"),
        needs_dist=True,
    ),
    # Selvtesten bygger repoet to gange med de to mutationer der lå i live og
    # dømmer på indhold af `dist/`. Den er derfor et selvstændigt step: uden
    # den er porten grøn på sit eget fejlform. Målt 30/9: 54 sekunder efter at
    # blokkene blev tjekket i tråde (var 5 min 01).
    Step(
        id="inline-js-selftest",
        argv=("python3", "tools/check_inline_js.py", "--self-test"),
        inputs=("tools/check_inline_js.py", "site/**", "build_sites.py",
                "tools/pagepass.py"),
    ),
    # Opgave 25: `;;` er en *tom sætning* i JavaScript, så `node --check`,
    # `tsc`, bygget og `check_inline_js` er alle grønne på den. Målt 6/10 med
    # `git log -S`: `97ef0b68` efterlod `…/;;` på linje 119 i
    # `site/_worker.js`. Porten dømmer hele JS-overfladen — `.js`-filer og
    # inline `<script>` i både `site/` og `dist/` — og maskerer strenge og
    # kommentarer først, så `};` i `clean-copy-bookmarklet.js` ikke tælles.
    #
    # Første kørsel fandt én rigtig rester i `site/da/free-tools.html:353`
    # (`?$/);;if(!m)return;`), som porten rettede i samme commit.
    Step(
        id="js-residue",
        argv=("python3", "tools/check_js_residue.py"),
        inputs=("tools/check_js_residue.py", "site/**", "build_sites.py",
                "tools/pagepass.py", "tools/brand.py"),
        needs_dist=True,
    ),
    Step(
        id="js-residue-selftest",
        argv=("python3", "tools/check_js_residue.py", "--self-test"),
        inputs=("tools/check_js_residue.py", "site/**"),
    ),
    Step(
        id="private-content",
        argv=("python3", "tools/check_private_content.py"),
        inputs=(
            "tools/check_private_content.py",
            "tools/paid_content.json",
            "tools/stripe_catalog.json",
            "site/**",
            "products/**",
        ),
        needs_dist=True,
    ),
    Step(
        id="page-profile-distribution",
        argv=("python3", "tools/check_page_profile_distribution.py"),
        inputs=(
            "tools/check_page_profile_distribution.py",
            "page-profile/**",
            "site/page-profile.html",
            "site/da/page-profile.html",
            "site/downloads/page-profile/**",
        ),
        needs_dist=True,
    ),
    Step(
        id="page-profile-distribution-selftest",
        argv=("python3", "tools/check_page_profile_distribution.py", "--self-test"),
        inputs=("tools/check_page_profile_distribution.py", "page-profile/**"),
    ),
    Step(
        id="page-profile-tests",
        argv=("python3", "page-profile/test_page_profile.py"),
        inputs=("page-profile/**", "site/downloads/page-profile/**"),
    ),
    Step(
        id="clean-copy-distribution",
        argv=("python3", "tools/check_clean_copy_distribution.py"),
        inputs=(
            "tools/check_clean_copy_distribution.py",
            "tools/build_clean_copy_archives.py",
            "site/downloads.html",
            "site/free-downloads.html",
            "site/clean-copy.html",
            "site/da/clean-copy.html",
            "site/downloads/**",
            "site/extension-zips/**",
            "obsidian-plugin/**",
            "extension-clean-copy/**",
            "extension-clean-copy-firefox/**",
        ),
        needs_dist=True,
    ),
    Step(
        id="clean-copy-distribution-selftest",
        argv=("python3", "tools/check_clean_copy_distribution.py", "--self-test"),
        inputs=("tools/check_clean_copy_distribution.py",),
    ),
    # Opgave 18: det publicerede desktop-kildearkiv skal være en regeneration
    # af `desktop/`. Før dette kendte ingen arkivet indhold — kun dets navn, så
    # et 1.3.0-arkiv kunne ligge under et 1.3.3-navn, og gaten var grøn.
    #
    # `inputs` er bevidst KUN builderen og arkivet. `desktop/package.json` er
    # ikke her, fordi workflowens path-filter med vilje udelukker `desktop/**`
    # (opgave 14 og 16: en desktop-ændring skal ikke deploye sites), og
    # `tools/test_deploy_workflow.py` fejler hvis et gatestep læser en fil
    # filteret ikke dækker. Konsekvensen er ærlig og skrevet ned: en commit der
    # kun retter `desktop/package.json` udløser ikke DENNE gate. Den fanges
    # først, når næste commit rører arkivet eller builderen. Se `❓ Til Mads`.
    Step(
        id="desktop-archive",
        argv=("python3", "tools/build_desktop_archive.py", "--check"),
        inputs=(
            "tools/build_desktop_archive.py",
            "site/downloads/eaa-scanner-desktop-src-*.zip",
        ),
    ),
    Step(
        id="desktop-archive-selftest",
        argv=("python3", "tools/build_desktop_archive.py", "--self-test"),
        inputs=("tools/build_desktop_archive.py",),
    ),
    # Opgave 20: `site-icons-1.0.0.tar.gz` viste sig at være en håndlavet kopi fra
    # 24/8, ikke bygget af `site-icons/`. Den indeholdt den døde udbyder
    # (Lemon Squeezy) i en README, der fortæller kunden hvor de køber en nøgle.
    # Opgave 19 læste kun arkivets *version*, som var korrekt — så fejlen slap igennem.
    #
    # `inputs` er hele familien: kilde, publicerede filer OG builderen. `site-icons/**`
    # er også i workflowens path-filter, så en commit der kun retter
    # `site-icons/site_icons.py` udløser gaten — det hullet, opgave 18 måtte oplyse
    # for `desktop/**`, gentages altså ikke her.
    Step(
        id="site-icons-archive",
        argv=("python3", "tools/build_site_icons_archive.py", "--check"),
        inputs=(
            "tools/build_site_icons_archive.py",
            "tools/mini_toml.py",
            "site-icons/**",
            "site/downloads/site-icons/**",
        ),
    ),
    Step(
        id="site-icons-archive-selftest",
        argv=("python3", "tools/build_site_icons_archive.py", "--self-test"),
        inputs=("tools/build_site_icons_archive.py", "tools/mini_toml.py"),
    ),
    # Finder kilder der kalder /api/license uden `product`, en død vært,
    # den lukkede Lemon Squeezy-API og en divergeret Firefox-kopi.
    Step(
        id="license-clients",
        argv=("python3", "tools/check_license_clients.py"),
        inputs=(
            "tools/check_license_clients.py",
            "tools/clean_copy_license.js",
            "site/_worker.js",
            "site/clean-copy-tool.html",
            "site/compliance-report.html",
            "obsidian-plugin/main.js",
            "extension-clean-copy/**",
            "extension-clean-copy-firefox/**",
            "page-profile/**",
            "site/downloads/page-profile/**",
            # Dokumenteret undtagelse, men stadig en klient der kalder API'et.
            "desktop/main.js",
        ),
    ),
    Step(
        id="license-clients-selftest",
        argv=("python3", "tools/check_license_clients.py", "--self-test"),
        inputs=("tools/check_license_clients.py",),
    ),
    # 103 checks mod de klienter der faktisk ships.
    Step(
        id="license-client-tests",
        argv=("node", "test.js"),
        inputs=(
            "test.js",
            "tools/test_license_clients.js",
            "tools/clean_copy_license.js",
            "obsidian-plugin/**",
            "site/clean-copy-tool.html",
            "site/compliance-report.html",
        ),
    ),
    Step(
        id="license-flow",
        argv=("node", "tools/test_license_flow.js"),
        inputs=("tools/test_license_flow.js", "site/_worker.js"),
    ),
    Step(
        id="obsidian-plugin-tests",
        argv=("node", "obsidian-plugin/test.js"),
        inputs=("obsidian-plugin/**", "tools/clean_copy_license.js"),
    ),
    Step(
        id="extension-tests",
        argv=("node", "extension-clean-copy/tools/test_clean_copy.js"),
        inputs=("extension-clean-copy/**", "tools/clean_copy_license.js"),
    ),
    Step(
        id="product-copy",
        argv=("python3", "tools/check_product_copy.py"),
        inputs=(
            "tools/check_product_copy.py",
            # Indlejret og importeret af checken.
            "tools/make_blog_da_mirrors_461.py",
            "site/**",
            "tools/stripe_catalog.json",
        ),
    ),
    Step(
        id="product-copy-selftest",
        argv=("python3", "tools/check_product_copy.py", "--self-test"),
        inputs=("tools/check_product_copy.py", "site/**"),
    ),
    # Lagrings-løfterne. Porten læser både `site/_worker.js` — for at finde de
    # ruter der kalder `rateLimitIp` — og hele `site/`, så begge skal med i
    # filteret ellers springer en rettelse af *ruten* gaten over, og det er
    # præcis den push der ville gøre porten meningsløs.
    Step(
        id="storage-claims",
        argv=("python3", "tools/check_storage_claims.py"),
        inputs=(
            "tools/check_storage_claims.py",
            "site/_worker.js",
            "site/**",
        ),
    ),
    # 429 i browseren (1/10). CEO-kø punkt 0 sagde 29/9 at 429 er endelig og
    # skal vise serverens besked, og rettede de syv klienter der stod i køen.
    # `site/thanks.html` stod ikke i den, og dens ene linje
    # `if (x.code === 429 || x.code >= 500) return again(…)` genkaldte en rute
    # der selv tæller sine forsøg — tolv gange, fire sekunder i mellemrum,
    # hver gang tællende i den tæller der gav 429. Reglen lå i `net.js`s egen
    # kommentar, og ingen port spurg om tak-siden fulgte den.
    #
    # Ruterne med 429 måles i `site/_worker.js` (dispatch → handler → 429), så
    # en ny rate-limiteret rute bliver dømt uden at nogen redigerer porten.
    Step(
        id="status-finality",
        argv=("python3", "tools/check_status_finality.py"),
        inputs=("tools/check_status_finality.py", "site/**"),
    ),
    Step(
        id="status-finality-selftest",
        argv=("python3", "tools/check_status_finality.py", "--self-test"),
        inputs=("tools/check_status_finality.py", "site/**"),
    ),
    Step(
        id="storage-claims-selftest",
        argv=("python3", "tools/check_storage_claims.py", "--self-test"),
        inputs=("tools/check_storage_claims.py", "site/_worker.js", "site/**"),
    ),
    # `/api/health` lægger `recentVisits` under `stats`, så værktøjet fra 6/10
    # læste den på topniveau og nåede aldrig «tracking død»-dommen — den kunne
    # ikke sige det den var bygget til. Selftesten dømmer alle tre domme på de
    # svar `/api` faktisk giver, så den fejlform kan ikke komme tilbage.
    Step(
        id="tracking-status-selftest",
        argv=("python3", "tools/check_tracking_status.py", "--self-test"),
        inputs=("tools/check_tracking_status.py",),
    ),
    # Løfter i FAQ-*generatorer* (30/9). `storage-claims` dømmer publicerede
    # sider ved at læse deres egne `fetch`-kald, og siger selv i docstringen at
    # en side som *beskriver* et værktøj uden at kalde det ikke kan dømmes.
    # `iter465_tool_faqs.py` skriver FAQ-tekst *om* værktøjet ind på værktøjets
    # egen side og kalder det aldrig, så hele den fejlform lå åben — den blev
    # kun rettet fordi en person læste filen. Porten finder generatorerne på
    # deres *form* (dict af slug → (spørgsmål, svar)), måler om slug'en peger på
    # en side der henter server-side gennem en rute fra `fetching_routes()`, og
    # afviser et afvisende løfte på præcis den side. Beviset er målt på de tre
    # rigtige generatorer plus fire mutationer.
    Step(
        id="generator-claims",
        argv=("python3", "tools/check_generator_claims.py"),
        # Præcis hvad porten læser: `TOOLS.glob("*.py")` (generatorerne,
        # `check_storage_claims.py` som modul og porten selv), `site/*.html`
        # for slugeksistens og `_worker.js` for ruterne. Erklæringen var `tools/**`,
        # og den læser otte filer porten aldrig åbner — dem faldt
        # `test_deploy_workflow` over som uhævede, så gaten var rød i CI.
        # Bemærk at `tools/*.py` *er* i filteret, så en ny generator i `tools/`
        # udløser gaten alligevel; den "kendte blind plet" var en følge af
        # over-erklæringen, ikke af filteret.
        inputs=(
            "tools/check_generator_claims.py",
            "tools/check_storage_claims.py",
            "tools/*.py",
            "site/_worker.js",
            "site/**",
        ),
    ),
    Step(
        id="generator-claims-selftest",
        argv=("python3", "tools/check_generator_claims.py", "--self-test"),
        # Selvtesten bygger sine mutationer i `tools/iter465_tool_faqs.py`
        # (og gendanner den i en `finally`) og læser ruterne fra `_worker.js`
        # gennem `fetching_routes()`.
        inputs=(
            "tools/check_generator_claims.py",
            "tools/check_storage_claims.py",
            "tools/*.py",
            "site/_worker.js",
            "site/**",
        ),
    ),
    # Ordtal i brødteksten (30/9). Review fandt `nis2-gap-assessment-da.html`
    # kalde "sikkerhed ved anskaffelse, udvikling og vedligeholdelse" det
    # *tiende* område, mens siden selv udgiver den som nr. 5 — to afsnit ovenfor
    # stod "det fjerde område" for leverandørsikkerhed, som er nr. 4, så
    # sidekonventionen afgjorde det. `rule-claims` dømmer tal og priser, ikke
    # ordtal mod en række, så det her er en egen port. Den læser den *statiske*
    # `<ul class="findings">` — den liste læseren tæller ned ad — og et løfte
    # den ikke kan dømme er en fejl, ikke et grønt kort.
    Step(
        id="area-ordinals",
        argv=("python3", "tools/check_area_ordinals.py"),
        inputs=("tools/check_area_ordinals.py", "site/**"),
    ),
    Step(
        id="area-ordinals-selftest",
        argv=("python3", "tools/check_area_ordinals.py", "--self-test"),
        inputs=("tools/check_area_ordinals.py", "site/**"),
    ),
    # Priser i købscopy og konstanter i værktøjers kode (30/9). Målt i en kopi
    # af repoet før denne port fandtes: `Math.round(wordCount / 238)` → `/ 237`,
    # copyens `238 wpm` → `239 wpm` og `$79/year` → `$78/year` i to pro-noter var
    # **alle tre grønne** i `rule-claims`, `stripe-ctas` og `area-ordinals`.
    # Den eksisterende prisregel spørger om beløbet kan betales *på den side det
    # står på*, så en pro-note uden købsknap er usynlig for den; den her spørger
    # om beløbet er en pris katalogen overhovedet sælger. Konstant-armen krydstjekker
    # `Math.round(x / N)` mod den hastighed siden lover i egen tekst.
    Step(
        id="ui-constants",
        argv=("python3", "tools/check_ui_constants.py"),
        inputs=("tools/check_ui_constants.py", "tools/stripe_catalog.json", "site/**"),
    ),
    Step(
        id="ui-constants-selftest",
        argv=("python3", "tools/check_ui_constants.py", "--self-test"),
        inputs=("tools/check_ui_constants.py", "tools/stripe_catalog.json", "site/**"),
    ),
    # Hero-notens skriftstørrelse (5/10, review-fund). Målt først i rigtig
    # Chromium 390 og 1280 px: `.hero p` (0,1,1) vandt over `.hero-note` (0,1,0),
    # så en note der var et `<p>` blev præcis så stor som brødteksten over den —
    # **20,8 px** på de to cleancopy-sider og **18,4 px** på 179 blog- og
    # guidesider. Rettelsen var `:not(.hero-note)` på begge `.hero p`-regler;
    # porten dømmer kaskaden, så den kommer ikke tilbage næste gang en
    # produktregel sætter font-size på hele heroen.
    Step(
        id="hero-note-scale",
        argv=("python3", "tools/check_hero_note_scale.py"),
        inputs=("tools/check_hero_note_scale.py", "site/style.css"),
    ),
    Step(
        id="hero-note-scale-selftest",
        argv=("python3", "tools/check_hero_note_scale.py", "--self-test"),
        inputs=("tools/check_hero_note_scale.py", "site/style.css"),
    ),
    # Dublet `<h2>` (30/9). Målt først: 63 af 190 blogfiler havde to afsnit med
    # samme navn, så indholdsfortegnelsen på 63 sider lister samme afsnit to
    # gange. Indholdet var forskelligt (median overlap mellem de to sektioners
    # links: 0 af 3), så ingen port så det — de dømmer links, priser og
    # løfter, ikke struktur. Her er det `<h2>`-teksten alene, normaliseret for
    # casing, entities og tags, for det er den læseren tæller.
    Step(
        id="duplicate-headings",
        argv=("python3", "tools/check_duplicate_headings.py"),
        inputs=("tools/check_duplicate_headings.py", "site/**"),
    ),
    Step(
        id="duplicate-headings-selftest",
        argv=("python3", "tools/check_duplicate_headings.py", "--self-test"),
        inputs=("tools/check_duplicate_headings.py", "site/**"),
    ),
    # To afsnit med samme job (30/9). Målt først: 62 sider — 44 EN og 18 DA —
    # havde både «Tools and guides» med et kortgitter og «Related Guides» med
    # en liste, to steder på samme side der begge lover «her er hvor du kan gå
    # hen». 36 af de relaterede links pegede på en destination siden allerede
    # viste i sit eget gitter, så `/blog/text-on-image-contrast-check` — den
    # mest besøgte artikel på mahope.tools — gav læseren
    # `/blog/wcag-contrast-checker` to gange under to navne. `duplicate-headings`
    # er korrekt grøn på dem, for overskrifterne er forskellige. Porten dømmer
    # både de to overskrifter på én side og én destination to gange i ét afsnit,
    # for det er to fejl. Generatoren er `crosslink_blog.py` +
    # `crosslink_blog_da.py`, som nu fletter ind i stedet for at stable en kasse
    # mere oveni.
    Step(
        id="tool-sections",
        argv=("python3", "tools/check_tool_sections.py"),
        inputs=("tools/check_tool_sections.py", "site/**"),
    ),
    Step(
        id="tool-sections-selftest",
        argv=("python3", "tools/check_tool_sections.py", "--self-test"),
        inputs=("tools/check_tool_sections.py", "site/**"),
    ),
    # Donationen skal bedes om *efter et resultat* (30/9). Målt først: `site/`
    # har 161 HTML-sider og 4 linkede til donation — `/scan`, `/scan-da` og de
    # to `/support`. Katalogen, `FUNDING.yml` og kontrakten har alle haft
    # linket længe, men ingen port målte om det nåede nogen, så missionens
    # «tak, hvor en glad bruger siger tak» var tre måneder gammel på de 37
    # værktøjssider der renderer et målt svar. Porten dømmer de to sider der
    # nu har linjen: katalogens URL, aldrig en knap, og i `<script>` så den
    # først opstår når værktøjet renderer — ellers viser den sig før læseren
    # har bedt om noget. Resten tælles og skrives ud i hver kørsel, men dømmes
    # ikke, fordi «hvor mange sider» er en beslutning, ikke 37 små rettelser.
    Step(
        id="donation-paths",
        argv=("python3", "tools/check_donation_paths.py"),
        inputs=("tools/check_donation_paths.py", "tools/donation.json",
                "tools/stripe_catalog.json", "site/**"),
    ),
    Step(
        id="donation-paths-selftest",
        argv=("python3", "tools/check_donation_paths.py", "--self-test"),
        inputs=("tools/check_donation_paths.py", "tools/donation.json",
                "tools/stripe_catalog.json"),
    ),
    # Donationssiden skal ikke fremstå som en hjælpeside (3/10). Målt først på
    # den **byggede** side: 274 anker til `/support`, og 1 lovede hjælp —
    # `thanks.html`, der skrev «Something wrong with your key? Support» på den
    # side en kunde lander i sekundet efter betaling, mens `/support` er
    # donationssiden (`<h1>Support the tools</h1>` og en Stripe-knap, intet om
    # licenser). `donation-paths` dømmer det modsatte — at linket ikke er en
    # knap og ligger i et `<script>` — men ingen port så på **linkteksten**.
    # Dom 1 fanger løftet om hjælp, dom 2 nøgne «Support». Fodnotens to
    # `support_link=` dømmes med, for de bygges ind i hver side og findes ikke i
    # nogen kildefil; de fire `hreflang`-ankere mellem de to donationssider er
    # sproglige alternativer og lades være. `needs_dist` fordi porten dømmer
    # `dist/`: `pagepass` erstatter hele `<footer>`, så en håndskreven
    # breadcrumb i kilden aldrig publiceres.
    Step(
        id="support-link-text",
        argv=("python3", "tools/check_support_link_text.py"),
        inputs=("tools/check_support_link_text.py", "site/**",
                "build_sites.py"),
        needs_dist=True,
    ),
    Step(
        id="support-link-text-selftest",
        argv=("python3", "tools/check_support_link_text.py", "--self-test"),
        inputs=("tools/check_support_link_text.py",),
    ),
    # En nøgle der ikke aktiverer, havde ingen selvbetjening (3/10). Målt først
    # på `site/`: `grep -rn "license/deactivate" uden for _worker.js` gav **én**
    # træffer, i `tests/stripe-worker.test.mjs` — ruten virkede, var testet, og
    # ingen side kaldte den. `site/license-lookup.html` lovede desuden «it is one
    # click in the app» (de to betalte apps ringer stadig til Lemon Squeezy, så
    # de har ingen knap) og «write to support@mahope.tools and **we free up the
    # seat**» — den menneskelige indsats missionen forbyder. Kan ikke være en
    # knap der beder om et maskinnavn: `device_id` danner klienten selv
    # (`uuid4().hex`, `cc-<random>`, sitets hostname), så porten dømmer at siden
    # **lister** maskinerne og frigør via den testede rute — og at succesteksten
    # er gateret på serverens `deactivated`, så den ikke lyver om en plads der
    # ikke blev frigjort.
    Step(
        id="license-seat-release",
        argv=("python3", "tools/check_license_seat_release.py"),
        inputs=("tools/check_license_seat_release.py", "site/**"),
    ),
    Step(
        id="license-seat-release-selftest",
        argv=("python3", "tools/check_license_seat_release.py", "--self-test"),
        inputs=("tools/check_license_seat_release.py",),
    ),
    # Formularfelter uden navn (30/9). Målt først: 14 felter på 13 sider havde
    # overhverket navn — 6 e-mail-felter var nyhedsbrevstilmeldingen på
    # NIS2-værktøjerne, 4 URL-felter var indgangen i et værktøj. `placeholder`
    # er ikke et navn: det forsvinder i det samme øjeblik feltet får fokus på
    # en telefon, og en skærmlæser læser det kun nogle gange. Porten læser også
    # inline-`<script>`, fordi NIS2-siderne skriver feltet som strengsammensætning
    # — ellers så den nul felter præcis der, hvor de er.
    Step(
        id="form-labels",
        argv=("python3", "tools/check_form_labels.py"),
        inputs=("tools/check_form_labels.py", "site/**"),
    ),
    Step(
        id="form-labels-selftest",
        argv=("python3", "tools/check_form_labels.py", "--self-test"),
        inputs=("tools/check_form_labels.py", "site/**"),
    ),
    # Opgave 21: den første handling over folden. Ratchetet er per rute *med
    # forventet destination*, så en ombytning af to `href` bliver rød — en
    # port der bare tæller `btn-primary` ville være grøn fordi siden stadig har
    # én, bare den forkert.
    Step(
        id="first-action",
        argv=("python3", "tools/check_first_action.py"),
        inputs=("tools/check_first_action.py", "tools/first_action.json", "site/**"),
    ),
    Step(
        id="first-action-selftest",
        argv=("python3", "tools/check_first_action.py", "--self-test"),
        inputs=("tools/check_first_action.py", "tools/first_action.json", "site/**"),
    ),
    # Blogindekset skal dække alle 189 guides og være lig sin egen generator.
    # Målt 2/10: 20 guides lå i `site/` uden et eneste link fra den side, hvis
    # meta description siger «Every guide on this site».
    Step(
        id="blog-index",
        argv=("python3", "tools/check_blog_index.py"),
        inputs=("tools/check_blog_index.py", "tools/make_blog_index.py", "site/blog/**", "site/da/blog/**"),
    ),
    Step(
        id="blog-index-selftest",
        argv=("python3", "tools/check_blog_index.py", "--self-test"),
        inputs=("tools/check_blog_index.py", "tools/make_blog_index.py", "site/blog/**", "site/da/blog/**"),
    ),
    # Én kopi af reglen for «hvad en besøgende ser, når vi har en dårlig dag».
    # `site/net.js` blev skrevet, fordi samme fejlform lå i klienterne; de seks
    # GET-klienter (`/compliance-site-check` EN+DA, `/page-profile` EN+DA,
    # `/security-headers-check`, `/url-inspector`) havde hver deres. Uden dette
    # step kunne nogen inline reglen igen, og næste rettelse bliver lavet ét
    # sted. Selvtesten kører med, fordi porten ellers kunne være grøn ved at slette
    # kernen i stedet for at bruge den.
    Step(
        id="net-copies",
        argv=("python3", "tools/check_net_copies.py"),
        inputs=("tools/check_net_copies.py", "site/**"),
    ),
    Step(
        id="net-copies-selftest",
        argv=("python3", "tools/check_net_copies.py", "--self-test"),
        inputs=("tools/check_net_copies.py", "site/**"),
    ),
    # En side der kalder en motor uden at indlæse den. Målt 2/10:
    # `/url-to-markdown` og `/da/url-til-markdown` flyttede `extractReadable` ud
    # i `/readable.js` for at forsidekonverteringen kunne dele den, men lagde
    # ikke script-tagget på de to sider der *allerede* kaldte den — Clean Copies
    # eget konverteringsværktøj ville kaste ved det første tryk, og hele gaten
    # var grøn, fordi ingen port kørte koden. Selvtesten kører med, fordi porten
    # ellers kunne være grøn ved ikke at finde nogen motor.
    Step(
        id="script-deps",
        argv=("python3", "tools/check_script_deps.py"),
        inputs=("tools/check_script_deps.py", "site/**"),
    ),
    Step(
        id="script-deps-selftest",
        argv=("python3", "tools/check_script_deps.py", "--self-test"),
        inputs=("tools/check_script_deps.py", "site/**"),
    ),
    # Frontdørens tjek, dømt på de to ender af den samme ledning. Målt 2/10:
    # begge frontdørsmotorer begynder med `if (!form || !window.NET) return;`,
    # så en forside der omdøber sit form-id eller glemmer `/net.js` **ligner
    # stadig et tjek** og gør bare intet — ingen fejl, ingen konsolundtagelse,
    # og den eneste målebare effekt er stigende bounce. Porten dømmer derfor at
    # hver forside med et `#check` har præcis ét tjek, at motoren er erklæret og
    # indlæst, at den leder præcis det form-id op, og at ingen rute kaldes uden
    # om `NET` (429 skal være endelig). Forsiderne er afledt af
    # build-manifestet, ikke en håndlavet liste. Selvtesten kører med, fordi
    # porten ellers kunne være grøn ved ikke at finde nogen forside.
    Step(
        id="front-door",
        argv=("python3", "tools/check_front_door.py"),
        inputs=("tools/check_front_door.py", "tools/check_article_paid_path.py",
                "build_sites.py", "site/**"),
    ),
    Step(
        id="front-door-selftest",
        argv=("python3", "tools/check_front_door.py", "--self-test"),
        inputs=("tools/check_front_door.py", "tools/check_article_paid_path.py",
                "build_sites.py", "site/**"),
    ),
    # At en nav-rute kaldet «Tools»/«Værktøjer» faktisk fører til værktøjerne.
    # Målt 6/10, og det er derfor porten findes: navet på deskuptime.com pegede
    # på `../auditedwp`s egen forside, som linkede **nul** af de to værktøjer
    # domænet udgiver. Sletningen af begge `href` gav `GRØN — 177 steps` — hele
    # gaten, fordi ingen port spørger om en indeksside peger på det den er indeks
    # over. Målt begge veje: mutationen giver 2 fund med navn, den rigtige side 0.
    Step(
        id="tool-hub",
        argv=("python3", "tools/check_tool_hub.py"),
        inputs=("tools/check_tool_hub.py", "build_sites.py", "site/**"),
    ),
    # Selftesten er ikke valgfri: portens egen navnefindning fejlede først på
    # «Værktøjer» (pythons `\b` er ASCII, så `\bværkt` er falsk på dansk), og
    # dens ruteord læste den afsluttende skråstreg som det tomme segment. Begge
    # fejl gjorde porten grøn uden at dømme noget.
    Step(
        id="tool-hub-selftest",
        argv=("python3", "tools/check_tool_hub.py", "--self-test"),
        inputs=("tools/check_tool_hub.py", "build_sites.py", "site/**"),
    ),
    # At forsidens tjek tager den indtastede adresse med til værktøjet. Målt
    # 2/10: tolv sider læser `#url=` og seks platform-guides linker til
    # `/scan#url=…`, men **ingen side producerede den** — den der tjekkede sit
    # site på forsiden og trykkede «Full WCAG scan» (den scanner der sælger
    # EUComply Pro) landede på `/scan` med et tomt felt. Den dybeste handling
    # på forsiden startede med at spørge om noget læseren lige havde svaret på.
    # Porten dømmer de tre ender mod hinanden — siden erklærer `takesUrl`,
    # målruten læser `#url=` med `location.hash`, og motoren bygger
    # fragmentet af flaget — fordi alle tre kan være forskudt fra hinanden
    # helt stille. Forsiderne er afledt af build-manifestet. Selvtesten kører
    # med, fordi porten ellers kunne være grøn ved at finde ingen handoff.
    Step(
        id="url-handoff",
        argv=("python3", "tools/check_url_handoff.py"),
        inputs=("tools/check_url_handoff.py", "tools/check_article_paid_path.py",
                "build_sites.py", "site/**"),
    ),
    Step(
        id="url-handoff-selftest",
        argv=("python3", "tools/check_url_handoff.py", "--self-test"),
        inputs=("tools/check_url_handoff.py", "tools/check_article_paid_path.py",
                "build_sites.py", "site/**"),
    ),
    # Købsknappen i hvert pro-kort, dømt mod `tools/stripe_catalog.json`.
    # Målt 2/10: de tretten værktøjssider skrev **pris og købslink i hånden**
    # inde i en inline `<script>`, og `check_own_prices.py` læser beløb i
    # markup — så de tretten var priser ingen kørsel kunne se. Uden dette step
    # kunne de stå på $79 mens Stripe sagde $89. Selvtesten kører med, fordi
    # porten ellers kunne være grøn ved ikke at finde nogen knap.
    Step(
        id="pro-card",
        argv=("python3", "tools/pro_card.py"),
        inputs=("tools/pro_card.py", "tools/pro_table.py",
                "tools/stripe_catalog.json", "site/**"),
    ),
    Step(
        id="pro-card-selftest",
        argv=("python3", "tools/pro_card.py", "--self-test"),
        inputs=("tools/pro_card.py", "tools/pro_table.py",
                "tools/stripe_catalog.json", "site/**"),
    ),
    # Spring i overskriftsniveau (30/9). Målt først: 12 sider sprang fra `<h1>`
    # til `<h3>` uden et `<h2>` imellem — `paid-templates` (EN+DA) satte 14
    # produkternavne i `<h3>` som det første indhold efter titlen, og
    # `clean-copy-cli-ref` havde ikke ét `<h2>` på hele siden. Skærmlæserens
    # overskriftsliste sagde "1, 3, 3, 2", altså et niveau der ikke findes
    # (WCAG 1.3.1). Dommen er i *dokumentrækkefølge* — et `<h3>` før sideens
    # første `<h2>` er springet, selv om siden har masser af `<h2>` længere nede.
    Step(
        id="heading-levels",
        argv=("python3", "tools/check_heading_levels.py"),
        inputs=("tools/check_heading_levels.py", "site/**"),
    ),
    Step(
        id="heading-levels-selftest",
        argv=("python3", "tools/check_heading_levels.py", "--self-test"),
        inputs=("tools/check_heading_levels.py", "site/**"),
    ),
    # Hvad `<h1>` *siger* (2/10). Målt først: `/site-icons` havde
    # `<h1>site-icons</h1>` — produktets filnavn som sidens største
    # skrifttype, mens `<title>` sagde «Generate favicons, OG images & PWA
    # icons from one». En måling i samme aflevering fandt to mere: `/page-profile`
    # (EN og DA) og `/bugbottle-demo`, så 4 af 322 byggede sider. De tre
    # Byggetagens kontrakt med designsystemet (2/10). `pagepass.OWNED_SELECTORS`
    # påstår at skallen ejer 154 selectors og sletter hver sidesregel for dem —
    # men 14 af dem havde ingen erklæring i style.css, så 10 generator-sider,
    # 6 bogside-r og 4 FAQ-sider mistede formatering uden erstatning. Dommen er
    # én påstand, målt: findes erstatningen? `check_built_css` dømmer at det der
    # *er* med overlever, altså ikke at det der *er slettet* skulle være med.
    Step(
        id="owned-selectors",
        argv=("python3", "tools/check_owned_selectors.py"),
        inputs=("tools/check_owned_selectors.py", "tools/pagepass.py", "site/style.css"),
    ),
    Step(
        id="owned-selectors-selftest",
        argv=("python3", "tools/check_owned_selectors.py", "--self-test"),
        inputs=("tools/check_owned_selectors.py", "tools/pagepass.py", "site/style.css"),
    ),
    # overskriftsporte ovenfor er alle grønne på den slags fejl: `seo_check`
    # tæller `<h1>`, `heading-levels` dømmer rækkefølgen, `duplicate-headings`
    # kun `<h2>`. To domme, fordi de fanger hver sit tilfælde — dom 1 et slug,
    # dom 2 routen udskrevet med store bogstaver, som dom 1 lader igennem.
    Step(
        id="page-h1",
        argv=("python3", "tools/check_page_h1.py"),
        inputs=("tools/check_page_h1.py", "site/**"),
    ),
    Step(
        id="page-h1-selftest",
        argv=("python3", "tools/check_page_h1.py", "--self-test"),
        inputs=("tools/check_page_h1.py", "site/**"),
    ),
    # `/developers` (3/10). De fire frie API'er virkede alle fire — målt med
    # curl mod den live udgivelse — men ingen side på mahope.tools nævnte dem,
    # og MCP'en der kalder præcis de fire lå på cleancopy.tools og 404'ede på
    # mahope.tools. `seo_check` dømmer en sides head og links, `check_links`
    # dømmer at de links der *er* går ned, og `route_inventory` kræver at en
    # side i manifestet er bygget — ingen af dem dømmer at en API mangler en
    # adresse. Fire domme: ruten i manifestet, hver nævnt rute findes i
    # `_worker.js`, metoden er den CORS-headeren erklærer, og siden står i den
    # *byggede* sitemap + llms.txt. Plus to fra 4/10, da kvotetabellen lovede
    # «500 000 characters per page» mens handleren afviser over `500 * 1024`,
    # og alle fem tal gjort absurde gav en grøn port: et sendt felt og et nævnt
    # tal kan begge dømmes mod koden, et returneret felt ikke.
    Step(
        id="developers-page",
        argv=("python3", "tools/check_developers_page.py"),
        # Kilderne der bestemmer `dist/` — ikke `dist/` selv, som er
        # gitignored og derfor ikke kan stå i workflowens path-filter. Samme
        # krav som `inline-js` ovenfor: sitemap.xml og llms.txt genereres af
        # `build_sites.py` ud fra disse, så en push der kun rører en af dem
        # ændrer det dom 4 dømmer og skal gaten afkontrollere.
        inputs=("tools/check_developers_page.py", "site/developers.html",
                "site/_worker.js", "tools/route_inventory.json",
                "build_sites.py", "tools/pagepass.py", "tools/brand.py",
                "tools/route_inventory.py"),
        needs_dist=True,
    ),
    Step(
        id="developers-page-selftest",
        argv=("python3", "tools/check_developers_page.py", "--self-test"),
        inputs=("tools/check_developers_page.py", "site/developers.html",
                "site/_worker.js", "tools/route_inventory.json"),
    ),
    # CEO-kø punkt 2 og 4 (4/10). Målt: 9 sider rørte DeskUptime, 8 havde
    # købsknappen — undtagelsen var præcis den engelske artikel der udleverer
    # de to betalte binære filer to gange, og den havde heller ingen
    # gratis-mod-Pro-forklaring. Begge artikler lovede desuden «Nothing is
    # uploaded anywhere, ever» / «Intet uploades nogensinde», hvilket er
    # falsk: appen aktiverer licensen online. `check_stripe_ctas` dømmer at
    # hvert produkt har sin købsside dokumenteret, og `check_buyable` tæller
    # linkene — ingen af dem ser, om den side der *uddeler filen* har en
    # købsvej eller om den lyver om sit netværk.
    Step(
        id="deskuptime-claims",
        argv=("python3", "tools/check_deskuptime_claims.py"),
        inputs=("tools/check_deskuptime_claims.py", "site/**",
                "tools/stripe_catalog.json"),
    ),
    Step(
        id="deskuptime-claims-selftest",
        argv=("python3", "tools/check_deskuptime_claims.py", "--self-test"),
        inputs=("tools/check_deskuptime_claims.py",),
    ),
    # Sampleringen under teksten på et billede (30/9). Målt i Chromium mod den
    # live side: hvid tekst på et rent hvidt billede gav **1.47:1**, og tallet
    # flyttede sig næsten ikke mellem forskellige tilstande (1.42/1.46/1.47) —
    # det fulgte fontstørrelsen, ikke billedet eller tekstfarven. Årsagen var at
    # `sampleContrast()` malede billedet *og* teksten på samme canvas og
    # kasserede alt inden for `dr+dg+db < 120` af tekstfarven, hvilket en
    # anti-aliaset glyfkant med 16 % dækning passerer med 126. Rettelsen maler i
    # to lag, så alpha er dækningen pr. pixel. Denne port kører sidens egen
    # kode i en Node-canvas-stub mod billeder med kendte farver — ingen browser,
    # så den kan køre i CI. Se docstringen i porten for målingerne.
    Step(
        id="contrast-sampling",
        argv=("python3", "tools/check_contrast_sampling.py"),
        inputs=("tools/check_contrast_sampling.py",
                "site/text-on-image-checker.html",
                "site/text-on-image-checker-da.html"),
    ),
    Step(
        id="contrast-sampling-selftest",
        argv=("python3", "tools/check_contrast_sampling.py", "--self-test"),
        inputs=("tools/check_contrast_sampling.py",
                "site/text-on-image-checker.html",
                "site/text-on-image-checker-da.html"),
    ),
    Step(
        id="stripe-ctas",
        argv=("python3", "tools/check_stripe_ctas.py"),
        inputs=(
            "tools/check_stripe_ctas.py",
            "tools/stripe_catalog.json",
            # Priserne og produktnøglerne står her; en ændring uden at
            # siderne følger med er en købsfejl.
            "docs/stripe-kontrakt.md",
            "site/**",
        ),
    ),
    Step(
        id="stripe-ctas-selftest",
        argv=("python3", "tools/check_stripe_ctas.py", "--self-test"),
        inputs=("tools/check_stripe_ctas.py",),
    ),
    # Hvilke betalte produkter der overhovedet *kan* sælges. `stripe-ctas`
    # dømmer et produkt kun når en side sælger det, så de syv dokumenter der
    # ligger i `mahope/paid-products` og endnu ikke er uploadet til KV kunne
    # ligge uudsolgte uden at noget skreg. Denne port er grøn for dem og rød
    # i det øjeblik `kv_verified` sættes til true — altså gør den
    # KV-uploaden til en pligt i stedet for en løs aftale.
    Step(
        id="buyable",
        argv=("python3", "tools/check_buyable.py"),
        inputs=(
            "tools/check_buyable.py",
            "tools/stripe_catalog.json",
            "tools/paid_content.json",
            "site/**",
        ),
    ),
    Step(
        id="buyable-selftest",
        argv=("python3", "tools/check_buyable.py", "--self-test"),
        inputs=("tools/check_buyable.py",),
    ),
    # Opgave 84: regeltallet i løfterne. Opgave 80, 83 og 84 rettede hver især
    # det samme tal, og alle tre var forkert, fordi ingen målte motoren. Nu er
    # tallet målt i koden ved hver kørsel, så en ny regel eller en ny side ikke
    # kan løfte om et tal uden at porten rødmer.
    Step(
        id="rule-claims",
        argv=("python3", "tools/check_rule_claims.py"),
        inputs=(
            "tools/check_rule_claims.py",
            # Motorerne: de frie regler tælles i `site/scan.html` og
            # `site/scan-da.html`, de betalte i `reportProFindings()`.
            "site/scan.html",
            "site/scan-da.html",
            "site/compliance-report.html",
            "site/_worker.js",
            # …og løfterne, der ligger i de 15 guidespejl plus de danske sider.
            "site/**",
        ),
    ),
    Step(
        id="rule-claims-selftest",
        argv=("python3", "tools/check_rule_claims.py", "--self-test"),
        inputs=("tools/check_rule_claims.py",),
    ),
    # Opgave 85: pluginsiden sagde 16, og det var **sandt** — fordi porten læste
    # det publicerede zip, som var seks regler bag kilden. En port der måler det
    # forkerte produkt, er ikke en port. Derfor måles motoren her desuden ved at
    # køre den, og kræver at arkivet er den kode vi udgiver.
    Step(
        id="plugin-engine-rules",
        argv=("python3", "tools/test_plugin_engine_rules.py"),
        inputs=(
            "tools/test_plugin_engine_rules.py",
            "tools/build_plugin_zip.py",
            "tools/plugin_engine_probe.php",
            "tools/fixtures/eaa_engine_all_rules.html",
            "tools/check_rule_claims.py",
            "scanner/wp-plugin/eaa-compliance-scanner/",
            "site/eaa-compliance-scanner.zip",
        ),
    ),
    # Opgave 87: `scanner/scanner_core.py` var en kopi af motoren med 16
    # regler, mens alt vi bygger kører de 22 i `scanner/packaging/`. Den var
    # ikke død kode — README'en kunden henter dokumenterer `python scan.py`,
    # som gik gennem den, så kildevejen gav seks færre regler end `pip install`.
    # Filen er nu en omdirigering, og testen *kører* vejen i stedet for at
    # tælle kode, så de 22 kan ikke komme tilbage som en stille kopiering.
    Step(
        id="scanner-core-redirect",
        argv=("python3", "tools/test_scanner_core_redirect.py"),
        inputs=(
            "tools/test_scanner_core_redirect.py",
            "tools/check_rule_claims.py",
            "tools/fixtures/eaa_engine_all_rules.html",
            "scanner/scanner_core.py",
            "scanner/packaging/eaa_scanner/",
            # README'en er den vej porten dømmer, så en rettelse af den skal
            # kunne finde en kommando der ikke virker.
            "site/downloads/eaa-scanner-README.md",
        ),
    ),
    # Opgave 88: opgave 87's port dømte *kommandoen* i README'en, men den
    # lover fire veje ind i produktet, og de tre andre var i stykker:
    # `pip install eaa-scanner` (404 på PyPI), `unzip … && cd desktop` (den
    # publicerede zip har ingen mappe) og DMG'en på v1.2.0 mens downloadsiden
    # sælger v1.3.3. Denne port måler alle fire mod de artefakter kunden får.
    Step(
        id="readme-paths",
        argv=("python3", "tools/check_readme_paths.py"),
        inputs=(
            "tools/check_readme_paths.py",
            "site/downloads/eaa-scanner-README.md",
            "site/downloads.html",
            "site/downloads/eaa_scanner-1.2.0-py3-none-any.whl",
            "site/downloads/eaa-scanner-desktop-src-1.3.4.zip",
        ),
    ),
    # Opgave 89: `npx page-profile` stod i 10 publicerede blog-sider, men
    # pakken findes hverken paa npm eller som et repo, og page-profile er et
    # enkelt Python-script. Samme fejlform som `pip install eaa-scanner` i
    # opgave 87, bare i 10x flere sider — og de la i `make_blog_*.py` saa
    # nogen kunne have skrevet den tilbage. Porten dommer derfor baade
    # publiceret tekst og generatorer, og kun kommandoer i kodekontekst.
    Step(
        id="install-commands",
        argv=("python3", "tools/check_install_commands.py"),
        inputs=("tools/check_install_commands.py", "site/**", "make_blog_*.py", "tools/*blog*.py", "tools/iter*.py"),
    ),
    Step(
        id="install-commands-selftest",
        argv=("python3", "tools/check_install_commands.py", "--self-test"),
        inputs=("tools/check_install_commands.py", "site/blog/canonical-url-guide.html"),
    ),
    # Opgave 88, anden halvdel: `check_install_commands.py` dommer
    # pakkeregistre, men de filer der *loades* i koden (curl -O paa en fil der
    # ikke findes, `cd` ind i et arkiv uden den mappe, `import requests` uden
    # pip-linje) la i en fejlform den ikke saa. Malt paa det publicerede
    # output, fordi `check_links.py` med vilje springer `pre`/`code` over.
    Step(
        id="asset-instructions",
        argv=("python3", "tools/check_asset_instructions.py"),
        inputs=("tools/check_asset_instructions.py", "site/**", "build_sites.py", "site/**/*.zip"),
    ),
    Step(
        id="asset-instructions-selftest",
        argv=("python3", "tools/check_asset_instructions.py", "--self-test"),
        inputs=("tools/check_asset_instructions.py",),
    ),
    Step(
        id="weekly-report-tests",
        argv=("python3", "tools/test_weekly_report.py"),
        # `tools/transient.py` er input, fordi `http_json` nu dømmer med den i stedet
        # for sin egen `_transient` (opgave 32), og en ændring af reglen skal køre
        # uge-rapportens egne tests.
        inputs=("tools/test_weekly_report.py", "tools/weekly_report.py", "tools/transient.py"),
    ),
    # Opgave 35: `reports/weekly/*.json` er det eneste sted i repoet hvor et
    # dokumenteret tal ligger gemt uden at nogen port læser filen.
    # `test_weekly_report.py` bruger syntetiske fixtures i det nye schema, så
    # den kan ikke se en arkivfil fra en ældre scriptversion — og alle tre
    # filer i arkivet er præcis det. Fundet var et `lemon`-blok, der sagde
    # "afventer godkendelse" om en udbyder der blev lukket 24/9, mens
    # `weekly_report.py` ikke indeholder ét `lemon` og ikke kan skrive blokken.
    # `weekly_report.py` er input, fordi porten beviser hvilke blokke koden kan
    # producere; `reports/weekly/**` er input, fordi arkivet er det den læser.
    Step(
        id="weekly-history",
        argv=("python3", "tools/check_weekly_history.py"),
        inputs=(
            "tools/check_weekly_history.py",
            "tools/weekly_report.py",
            "reports/weekly/*.json",
            # Regel 5 spørger om hver `top_paths`-rute er publiceret, så
            # inventaret er ikke længere bare en valgfri målekilde: en push der
            # kun tilføjer en rute til det skal kunne rødme porten.
            "tools/route_inventory.json",
        ),
    ),
    Step(
        id="weekly-history-selftest",
        argv=("python3", "tools/check_weekly_history.py", "--self-test"),
        inputs=(
            "tools/check_weekly_history.py",
            "tools/weekly_report.py",
            "reports/weekly/*.json",
            "tools/route_inventory.json",
        ),
    ),
    # Opgave 36: uge 40 skrev `api/stats: name 'count' is not defined` i sin
    # `errors` og `unknown` i resten af filen, fordi `note_error` kun skrev
    # `str(exc)` — Python skriver aldrig klassenavnet i beskeden. Fire ugers
    # rapporter sagde altså "ukendt" om en fejl i os selv. `note_error` skriver
    # nu klassenavnet, og porten dømmer på den: en kodefejl i vores egen kode må
    # aldrig stå som "ukendt", mens et timeout må. `weekly_report.py` er input,
    # fordi porten *kører* `note_error` frem for at læse den.
    Step(
        id="weekly-code-errors",
        argv=("python3", "tools/check_weekly_code_errors.py"),
        inputs=(
            "tools/check_weekly_code_errors.py",
            "tools/weekly_report.py",
            # `tools/transient.py` er input, fordi portens `known_kinds()` læser
            # klassenavnene derfra: opgave 32 flyttede `_transient` ud af
            # `weekly_report.py`, og da forsvandt `URLError` fra sættet — nøjagtig
            # den fejl `soft()` oftest fanger. Uden filen i filteret ville en push
            # kun tilføje en ny fejlklasse i modulet og springe porten over.
            "tools/transient.py",
            "reports/weekly/*.json",
        ),
    ),
    Step(
        id="weekly-code-errors-selftest",
        argv=("python3", "tools/check_weekly_code_errors.py", "--self-test"),
        inputs=(
            "tools/check_weekly_code_errors.py",
            "tools/weekly_report.py",
            "tools/transient.py",
            "reports/weekly/*.json",
        ),
    ),
    Step(
        id="deploy-workflow",
        argv=("python3", "tools/test_deploy_workflow.py"),
        inputs=(
            "tools/test_deploy_workflow.py",
            # mini_yaml er en afhængighed, ikke en dev-afhængighed: workflowen
            # døde i en hel måned uden PyYAML, se kørsel 36180367257.
            "tools/mini_yaml.py",
            ".github/workflows/deploy-sites.yml",
            ".github/workflows/build-desktop.yml",
        ),
    ),
    Step(
        id="deploy-workflow-selftest",
        argv=("python3", "tools/test_deploy_workflow.py", "--self-test"),
        inputs=("tools/test_deploy_workflow.py", "tools/mini_yaml.py"),
    ),
    Step(
        id="python-env",
        argv=("python3", "tools/check_python_env.py"),
        inputs=(
            "tools/check_python_env.py",
            # Locken må ikke kunne ændre sig uden at porten ser det, og
            # generatoren ejer topniveau-listen porten sammenligner import imod.
            "tools/lock_python_env.py",
            "tools/mini_toml.py",
            "requirements-build.txt",
            "requirements-audit.txt",
            "site-icons/pyproject.toml",
        ),
    ),
    Step(
        id="python-env-selftest",
        argv=("python3", "tools/check_python_env.py", "--self-test"),
        inputs=("tools/check_python_env.py", "tools/mini_toml.py"),
    ),
    Step(
        id="versions",
        argv=("python3", "tools/check_versions.py"),
        # `desktop/package.json` står bevidst IKKE her: `test_deploy_workflow`
        # forbyder at en desktop-ændring udløser sites-deployen, fordi desktop
        # udgives af build-desktop.yml. Se `RESULT` (opgave 14) om hullet.
        inputs=(
            "tools/check_versions.py",
            "tools/mini_toml.py",
            "site/downloads.html",
            "extension-clean-copy/manifest.json",
            "extension-clean-copy-firefox/manifest.json",
            "obsidian-plugin/manifest.json",
            "obsidian-plugin/versions.json",
            "scanner/packaging/pyproject.toml",
            "scanner/packaging/eaa_scanner/__init__.py",
            "scanner/npm/eaa-scanner/package.json",
            "page-profile/pyproject.toml",
            "page-profile/page_profile.py",
            "site-icons/pyproject.toml",
            "manifest.json",
            "versions.json",
        ),
    ),
    Step(
        id="versions-selftest",
        argv=("python3", "tools/check_versions.py", "--self-test"),
        inputs=("tools/check_versions.py", "tools/mini_toml.py"),
    ),
    # Opgave 26: de publicerede tekster *uden for* `site/`. Rod-README'en for
    # `mahope/hermes-passiv` løb som Clean Copy for Obsidian, havde en changelog
    # på 1.0.1 mod en publiceret 1.0.10 og ingen donation — og ingen af de 38
    # steps læste den. Rettelsen i opgave 23 holdt kun, fordi en researchiteration
    # tilfældigvis læste den.
    #
    # `inputs` er de filer porten læser, så en commit der kun retter rod-README'en
    # eller FUNDING.yml udløser porten. `docs/stripe-kontrakt.md` er med, fordi
    # `stripe_catalog.json` er genereret ud fra den.
    Step(
        id="repo-readme",
        argv=("python3", "tools/check_repo_readme.py"),
        inputs=(
            "tools/check_repo_readme.py",
            "README.md",
            ".github/FUNDING.yml",
            "tools/stripe_catalog.json",
            "tools/route_inventory.json",
            "docs/stripe-kontrakt.md",
        ),
    ),
    Step(
        id="repo-readme-selftest",
        argv=("python3", "tools/check_repo_readme.py", "--self-test"),
        inputs=("tools/check_repo_readme.py", "tools/stripe_catalog.json",
                "tools/route_inventory.json"),
    ),
    # Opgave 28: arkiver, der er slettet i git men stadig kan hentes. 1.5.3s
    # README lovede "nothing leaves your browser", og Cloudflare Pages fjerner
    # ikke slettede assets — så filen blev ved med at svare 200 med den gamle
    # tekst, selv om den var væk fra både git og dist. `inputs` er de filer
    # porten læser, så en commit der kun retter json'en eller workerens
    # redirect-tabel udløser porten. `check_live_sitemaps.py` (efter deploy)
    # bekræfter det samme i produktion — den her port kan kun se repoet.
    Step(
        id="retired-downloads",
        argv=("python3", "tools/check_retired_downloads.py"),
        inputs=(
            "tools/check_retired_downloads.py",
            "tools/retired_downloads.json",
            "site/_worker.js",
            "README.md",
            "site/**",
        ),
        needs_dist=True,
    ),
    Step(
        id="retired-downloads-selftest",
        argv=("python3", "tools/check_retired_downloads.py", "--self-test"),
        inputs=("tools/check_retired_downloads.py", "tools/retired_downloads.json"),
    ),
    Step(
        id="links",
        argv=("python3", "tools/check_links.py"),
        inputs=("tools/check_links.py", "build_sites.py", "site/**"),
        needs_dist=True,
    ),
    Step(
        id="links-selftest",
        argv=("python3", "tools/check_links.py", "--self-test"),
        inputs=("tools/check_links.py",),
    ),
    # Opgave 15: de døde sitemap-generator- og deploystier. Uden dette step
    # kan 21 generatorer igen skrive i en kilde-sitemap, builden springer over,
    # og indexnow_ping.sh igen pege på en vært der ikke findes.
    Step(
        id="legacy-seo-paths",
        argv=("python3", "tools/check_legacy_seo_paths.py"),
        # Gaten læser ALLE .py/.sh i roden og i tools/, fordi det er dem, der
        # kunne skrive i den døde kilde-sitemap eller pege på den døde vært.
        # Derfor er familierne i input — ellers kunne en generator ændres uden at
        # gaten nogensinde så den, præcis som fund 1 i RESULT (opgave 11).
        inputs=("tools/check_legacy_seo_paths.py", "indexnow_ping.sh", "deploy.sh",
                "*.py", "*.sh", "tools/*.py", "tools/*.sh"),
    ),
    Step(
        id="legacy-seo-paths-selftest",
        argv=("python3", "tools/check_legacy_seo_paths.py", "--self-test"),
        inputs=("tools/check_legacy_seo_paths.py",),
    ),
    # Opgave 17: de tre DeskUptime-værktøjssider indlæser `../auditedwp`s eget
    # designsystem. Uden dette step kan en ny token der blive erklæret der, uden
    # at nogen bro dækker den, og siden får to farver igen — samme fejlform som
    # de 18 "broken references" i opgave 10.
    Step(
        id="design-tokens",
        argv=("python3", "tools/check_design_tokens.py"),
        # Gaten læser det byggede dist (hvilke sider der indlæser hvilket
        # stylesheet), `site/style.css` (broen) og `build_sites.py` (hvilke
        # assets der følger med fra auditedwp). `site/**` er med, fordi en ny
        # side med sit eget stylesheet ellers kunne merge uden at nogen kørte
        # porten — samme fejl som fund 1 i RESULT (opgave 11).
        inputs=("tools/check_design_tokens.py", "build_sites.py", "site/style.css", "site/**"),
        needs_dist=True,
    ),
    # Opgave 32: strukturerede data var grønne og tilfældige. To iterationer
    # rettede den samme fejlform pr. side i markup, fordi portene talte
    # *antal* blokke og ikke *hvilke* typer — og fordi `pagepass` kun læste
    # JSON-LD i `<head>`, så en blok i `<body>` så ud som om siden ingen havde.
    # Denne port måler typerne i det udgivne dist og kræver samme sæt på begge
    # sprog. Den fandt `bugbottle.dev/da/` manglende `SoftwareSourceCode` ved
    # første kørsel — altså en fejl ingen håndmåling havde set.
    Step(
        id="jsonld-types",
        argv=("python3", "tools/check_jsonld_types.py"),
        # `bugbottle-landing/**` er med, fordi bugbottle.dev's forsider kommer
        # derfra og ikke fra `site/` — ellers kunne de merge uden at porten
        # så dem, præcis som de gjorde.
        inputs=("tools/check_jsonld_types.py", "tools/pagepass.py", "site/**",
                "bugbottle-landing/**"),
        needs_dist=True,
    ),
    Step(
        id="jsonld-types-selftest",
        argv=("python3", "tools/check_jsonld_types.py", "--self-test"),
        inputs=("tools/check_jsonld_types.py",),
    ),
    # Opgave fra planens NEXT_TASK 3: fire danske sider uden søskende viste sig
    # at være danskoriginaler, men målingen fandt fire **krydsede** hreflang-par
    # i stedet: to engelske artikler erklærede begge den samme danske, og de to
    # par pegede gennem hinanden. `hreflang_pairs` i build_sites.py skriver et
    # dict hvor den der skriver sidst vinder, så det er ikke en fejl bygget
    # rejser på — det er to sider der begge har en gyldig `<link>`. Denne port
    # måler derfor par-retningen i `dist/`: ét par pr. søskende, og gensidigt.
    Step(
        id="hreflang-pairs",
        argv=("python3", "tools/check_hreflang_pairs.py"),
        inputs=("tools/check_hreflang_pairs.py", "build_sites.py", "site/**",
                "bugbottle-landing/**"),
        needs_dist=True,
    ),
    Step(
        id="hreflang-pairs-selftest",
        argv=("python3", "tools/check_hreflang_pairs.py", "--self-test"),
        inputs=("tools/check_hreflang_pairs.py",),
    ),
    Step(
        id="design-tokens-selftest",
        argv=("python3", "tools/check_design_tokens.py", "--self-test"),
        inputs=("tools/check_design_tokens.py",),
    ),
    # Opgave 15: bygget slettede CSS på 22 sider i to iterationer, og ingen
    # port så det. `WRAP_SELECTOR_RE` spiste ethvert `*-wrap`, og da
    # `check_design_tokens` så på `style.css`, troede den at `style.css:128-136`
    # dækkede ni tokens — mens de lå under `html[data-product="deskuptime"]`,
    # altså kun på ét domæne. Samme fejlform som `RE_CLAIM` og
    # `tool_paid_path_blind`: noget der tæller uden at dømme sit eget tal.
    #
    # Denne port stiller begge spørgsmål på de byggede filer: er en regel fra
    # `site/` væk i `dist/` mens elementet stadig er i markup og skallen ikke
    # erstatter den, og er ethvert `var(--x)` *opløst* for sidens
    # `data-product` — ikke "nævnt et sted i style.css", som var den forkerte
    # læsning. Første kørsel fandt 9 uopløste tokens på 4 domæner.
    Step(
        id="built-css",
        argv=("python3", "tools/check_built_css.py"),
        # `site/**` og `bugbottle-landing/**` fordi porten måler hver side i
        # dist mod sin kilde; `tools/pagepass.py` fordi den er den, der
        # beslutter hvilke regler der overlever; `site/style.css` fordi den er
        # skallen, der erstatter de tabte.
        inputs=("tools/check_built_css.py", "tools/pagepass.py", "build_sites.py",
                "site/style.css", "site/**", "bugbottle-landing/**"),
        needs_dist=True,
    ),
    # Uden `--self-test`-steppet er selvværdierne ubevidnede: porten kunne
    # være grøn fordi den intet dømmer. Selvtesten muterer `pagepass.py` og
    # `site/style.css` — de rigtige filer — i en kopi af repoet, bygger der og
    # kræver at porten bliver rød med filnavn på hver mutation.
    Step(
        id="built-css-selftest",
        argv=("python3", "tools/check_built_css.py", "--self-test"),
        inputs=("tools/check_built_css.py", "tools/pagepass.py", "site/style.css"),
    ),
    # Opgave fra planens NEXT_TASK 1: den indlejrede CTA-tracker på site/scan.html
    # og site/scan-da.html byggede sit begivenhedsnavn ud fra den **valgfrie
    # `(da\/)?`-gruppe**, så `/compliance-report` sendte `cta-undefined` og
    # `/da/compliance-report#pris` sendte `cta-da/`. Begge er gyldig JS uden
    # fejl i loggen, men `handleTrack` i _worker.js kræver `^[a-z0-9-]+$` og
    # afviste resten med 400 — så de begivenheder kom aldrig i tallet. Kun to
    # filer, men 205 andre sider har samme mønster, og intet så det. Denne port
    # læser hver sides egen href gennem dens egen regex og kræver præcis de to
    # betingelser handleTrack håndhæver. Beviset: rød på 87b5527~1 med de tre
    # links STATE ovenfor citerer, grøn på rettelsen.
    Step(
        id="inline-cta-events",
        argv=("python3", "tools/check_inline_cta_events.py"),
        inputs=("tools/check_inline_cta_events.py", "site/**"),
    ),
    Step(
        id="inline-cta-events-selftest",
        argv=("python3", "tools/check_inline_cta_events.py", "--self-test"),
        inputs=("tools/check_inline_cta_events.py",),
    ),
    # Den blinde plet `inline-cta-events` *kan* lukke, målt 28/9: porten bygger
    # sit `tool_paths`-sæt af de hvidlister den selv kan læse, så en rute ingen
    # måler er usynlig for den. `/free-downloads` blev fundet på den måde, og så
    # kom **35** ruter i samme blindplet — 2366 links i `dist/`, blandt dem
    # `/books` (e-bogbutikken, 613 links) og `/blog` (875). Funnelens to største
    # trin var usynlige, og porten var grøn hele vejen.
    #
    # Denne port lister de ruter i `tools/route_inventory.json` der har
    # indgående links, men ingen måler, og **genbruger `inline-cta-events`' egne
    # læsere** — så den kan ikke se noget andet end porten. Undtagelserne står i
    # `ALLOWED_UNMEASURED` med en grund hver, fordi en undtagelse uden grund er en
    # fejl der venter på at blive læst som en regel. Selftesten dømmer
    # beslutningen direkte på syntetisk input: en audit der ikke kan blive rød,
    # kan heller ikke troes på når den er grøn.
    Step(
        id="unmeasured-routes",
        argv=("python3", "tools/audit_unmeasured_routes.py"),
        inputs=("tools/audit_unmeasured_routes.py", "tools/check_inline_cta_events.py",
                "tools/route_inventory.json", "site/track.js", "site/**"),
        needs_dist=True,
    ),
    Step(
        id="unmeasured-routes-selftest",
        argv=("python3", "tools/audit_unmeasured_routes.py", "--self-test"),
        inputs=("tools/audit_unmeasured_routes.py",),
    ),
    # `track.js` sprang før hele siden over, når den så en inline-tracker, og
    # inline-trackeren er `^\/`-forankret, så ingen af dem kunne tælle de 300
    # absolutte krydsdomenelinks på 87 inline-sider. Denne port dømmer den
    # egenskab, der gør delingen sikker — at mængderne er disjunkte af
    # konstruktion — i stedet for at genskrive de to regexer og håbe de ligner.
    # Den matcher ingen regexer overhovedet, kun *kildedeklarationen*, så den
    # kan ikke måle en anden kode end den browseren kører.
    Step(
        id="cross-domain-cta",
        argv=("python3", "tools/audit_cross_domain_cta.py"),
        inputs=("tools/audit_cross_domain_cta.py", "site/track.js",
                "build_sites.py", "site/**"),
        needs_dist=True,
    ),
    Step(
        id="cross-domain-cta-selftest",
        argv=("python3", "tools/audit_cross_domain_cta.py", "--self-test"),
        inputs=("tools/audit_cross_domain_cta.py",),
    ),
    # Opgave fra planens NEXT_TASK 1: `check_inline_cta_events.py` læser
    # `site/`, men bygget skriver krydsdomænelinks til **absolutte** URL'er — så
    # den måler en anden kode end den browseren kører, og den ser hverken
    # `https://cleancopy.tools` (ingen slutstreg) eller `href="/"` (rodrelative).
    # `CTA_HOME` krævede både scheme *og* skråstreg efter værten, så de 2184
    # domænelinks uden slutstreg og alle rodrelative hjemmelinks sendte intet:
    # flere klik end de 1781 sidste iteration rettede. Denne port læser det
    # **byggede** `dist/` og tæller pr. udgivet rute, hvor mange links der peger
    # på den og hvor mange `track.js` kan matche. Forventningen er en
    # håndskrevet `REQUIRED_SLUGS`, ikke noget læst ud af `track.js` — ellers
    # var porten grøn præcis når en hvidliste mister et navn. Beviset på at den
    # ser noget: rød med 2634 link-instanser mod main's `CTA_HOME`, grøn efter.
    Step(
        id="cta-coverage-dist",
        argv=("python3", "tools/check_cta_coverage_dist.py"),
        inputs=("tools/check_cta_coverage_dist.py", "site/track.js",
                "build_sites.py", "site/**"),
        needs_dist=True,
    ),
    Step(
        id="cta-coverage-dist-selftest",
        argv=("python3", "tools/check_cta_coverage_dist.py", "--self-test"),
        inputs=("tools/check_cta_coverage_dist.py", "site/track.js"),
    ),
    # Opgave fra planens NEXT_TASK 1 (29/9): de tre forrige CTA-porte dømmer
    # hver *sin* del — inventaret, kildeklikket, det byggede link — men ingen
    # spørger det ene spørgsmål, der binder dem sammen: *sender hvert eneste
    # absolutte krydsdomenelink i `dist/` en `cta-`-begivenhed?* Målt i `dist/`
    # 29/9: 765 links sendte intet, i 198 stier, og de var ikke tilfældige — de
    # var seks klasser, hvoraf to var reelle pengehuller (`/books/*`, 18 klik).
    #
    # Undtagelserne ligger i `ALLOWED_UNMEASURED` som *(regel, grund)*, fordi
    # fem af klasserne er URL-mønstre og ikke navne. Selftesten har 14 positive
    # kontroller, heraf to der muterer `site/track.js`' egen kildekopi: uden
    # `CTA_BOOK_PAGES` skal bogsiden blive rød, og uden `support` i `CTA_PATHS`
    # skal donationsruten blive rød. En port der ikke kan blive rød på den
    # kode den læser, må ikke tælles som bevis.
    Step(
        id="dist-cta-routes",
        argv=("python3", "tools/audit_dist_cta_routes.py"),
        inputs=("tools/audit_dist_cta_routes.py", "site/track.js",
                "build_sites.py", "site/**"),
        needs_dist=True,
    ),
    Step(
        id="dist-cta-routes-selftest",
        argv=("python3", "tools/audit_dist_cta_routes.py", "--self-test"),
        inputs=("tools/audit_dist_cta_routes.py", "site/track.js",
                "tools/check_cta_coverage_dist.py", "tools/check_inline_cta_events.py"),
    ),
    # Opgave fra planens NEXT_TASK 2: `traffic_status: "partial"` har stået i
    # `/api/health` i måneder uden at cron blev rød, fordi `status` var
    # `kvOk ? 'healthy' : 'degraded'`. Rettelsen er delt: `_worker.js` har nu
    # `partial` som egen tilstand og `traffic_domains`, og `tools/
    # check_health_status.py` dømmer på beviset. Det er **kun** porten der kan
    # køre her — selve dommeren taler med produktion og hører til cron'en.
    Step(
        id="health-acknowledgement-tests",
        argv=("python3", "tools/test_health_acknowledgement.py"),
        inputs=(
            "tools/test_health_acknowledgement.py",
            "tools/check_health_status.py",
            "tools/health_acknowledged.json",
            # De to overvågere, der begge nu kalder dommeren. Uden dem i
            # filteret kunne en af dem blive ændret uden at porten kørte.
            "daily-health-check.sh",
            "health_check.py",
            "site/_worker.js",
        ),
    ),
    # Missionens konverteringskrav: "find de sider der har flest besøg, og
    # sørg for at hver Pro-side klart viser hvad gratis og betalt giver, og har
    # én købsknap der virker". Målingen lå i hovedet på to iterationer, så
    # næste måling måtte selv finde den næste side. Porten rangerer artikler
    # efter manglende betalt vej og dømmer, at listen over blinde artikler er
    # en *ratchet*: den må kun krympe. 123 af 190 artikler er blinde i dag, så
    # en tærskel ville være meningsløs; listen er den ærlige form.
    Step(
        id="article-paid-path",
        argv=("python3", "tools/check_article_paid_path.py", "--quiet"),
        inputs=(
            "tools/check_article_paid_path.py",
            # Porten arver selvklik-reglen (regel 5) fra arkivporten, så en
            # push der kun retter `unpublished_rows` skal kunne rødme *begge*.
            "tools/check_weekly_history.py",
            "tools/article_paid_path_blind.json",
            # Dom 5s flås. Uden den i filteret kunne
            # `article_click_no_button.json` ændres uden at porten nogensinde
            # læste den — samme fejl som de to overførsler over.
            "tools/article_click_no_button.json",
            # Dom 6s flås, samme grund: uden den kunne
            # `article_page_paid_path.json` ændres uden at porten læser den.
            "tools/article_page_paid_path.json",
            # Dom 7s flås, samme grund igen: uden den kunne
            # `frontpage_no_button.json` ændres uden at porten læser den.
            "tools/frontpage_no_button.json",
            "tools/route_inventory.json",
            "tools/stripe_catalog.json",
            "tools/check_stripe_ctas.py",
            # Dom 7 læser build-manifestet for at finde ud af hvilken fil
            # hvert domæne serverer på forsiden. Uden den i filteret kunne
            # `index_from`/`remap`/`extra` ændres uden at porten målte igen.
            "build_sites.py",
            "reports/weekly/*.json",
            "site/**/*.html",
        ),
    ),
    Step(
        id="article-paid-path-selftest",
        argv=("python3", "tools/check_article_paid_path.py", "--self-test"),
        inputs=("tools/check_article_paid_path.py", "build_sites.py",
                "tools/check_weekly_history.py"),
    ),
    # Opgave 3 (30/9): værktøjssiderne lå uden for portens dom, fordi
    # artikelportens dom 6 kræver *målte besøg* — og `/api/stats` har svaret
    # 401 siden uge 37, så ingen værktøjsside har besøg i nogen rapport. Fire
    # iterationer i træk rettede derfor én side ad gangen ved at læse trafikken
    # i hovedet. Målt 30/9: 42 publicerede værktøjssider uden betalt vej, de
    # mest indgående med 199 links.
    #
    # Samme læsere som artikelporten (regel 1 i portens docstring), så de to
    # gatestræk ikke kan glide fra hinanden. Derfor er de også inputs her:
    # uden dem kunne `check_article_paid_path.py` ændre sine læsere uden at
    # dette gatestræk kørte.
    Step(
        id="tool-paid-path",
        argv=("python3", "tools/check_tool_paid_path.py", "--quiet"),
        inputs=(
            "tools/check_tool_paid_path.py",
            # Ratcheten over de blinde værktøjssider. Uden den i filteret kunne
            # en push, der kun tilføjer eller fjerner en linje, springe gaten
            # over — altså netop den push der afgør om porten er værd at have.
            "tools/tool_paid_path_blind.json",
            # Ratcheten over de betalte veje hver side lå på da den blev
            # målt. Samme grund som linjen ovenfor — ellers springer en push,
            # der kun skriver en destination i den fil, netop den port over
            # der dømmer om en side har mistet sin vej.
            "tools/tool_paid_path_ratchet.json",
            "tools/check_article_paid_path.py",
            # …som nu selv arver `unpublished_rows` herfra, så en push der kun
            # retter selvklik-reglen skal køre alle tre gatestræk.
            "tools/check_weekly_history.py",
            "tools/check_stripe_ctas.py",
            "tools/route_inventory.json",
            "tools/stripe_catalog.json",
            "build_sites.py",
            "reports/weekly/*.json",
            "site/**/*.html",
        ),
    ),
    Step(
        id="tool-paid-path-selftest",
        argv=("python3", "tools/check_tool_paid_path.py", "--self-test"),
        inputs=("tools/check_tool_paid_path.py", "build_sites.py",
                "tools/check_article_paid_path.py",
                "tools/check_weekly_history.py",
                "tools/tool_paid_path_ratchet.json"),
    ),
    # `cleancopy.tools` viste sig at modtage beacons med HTTP 200 og tabe dem:
    # KV-bindingen `VISITS` er sat pr. Pages-projekt i Cloudflare, ikke i
    # `deploy-sites.yml`, så et domæne kan være deployet, instrumenteret og
    # stadig usynligt i hvert eneste tal. Før dette var der ingen måling af
    # *hvilket* domæne der taber trafik. Selve proben taler med produktion og er
    # bevidst IKKE et gatestep — den skriver én talt sidevisning pr. domæne, så
    # den skal køres manuelt. Her dømmes kun portens logik, offline.
    # Konkurrenternes priser er en påstand (30/9). Artiklen om DeskUptime skrev
    # «$7-12 per month» om UptimeRobot og «$12» om Pingdom, og hovedlinjen
    # «Kill Your $144/year SaaS Uptime Bill» stod på 16 sider. Slået op 30.
    # september 2026: UptimeRobot Solo er €10/måned (€108/år), Better Stack
    # sælger oppetid pr. *responder-plads* til $34/måned ($408/år), og Pingdom
    # har ingen offentlig listepris. Alle tal ligger nu i én fil, og porten
    # dømmer hvert beløb i `<title>`, `og:description`, JSON-LD, tabeller og
    # brødtekst mod den — på tværs af alle 303 sider.
    Step(
        id="competitor-prices",
        argv=("python3", "tools/check_competitor_prices.py"),
        inputs=("tools/check_competitor_prices.py",
                "tools/competitor_prices.json", "site/**"),
    ),
    Step(
        id="competitor-prices-selftest",
        argv=("python3", "tools/check_competitor_prices.py", "--self-test"),
        inputs=("tools/check_competitor_prices.py",
                "tools/competitor_prices.json", "site/**"),
    ),
    # Vores *egne* priser (1/10). Samme fejlform som konkurrentpriserne, både
    # fordi ingen port dømte dem, og fordi de lå i præcis samme fil som de
    # konkurrerende tal: `check_stripe_ctas` spørger om der *er* en købsknap og
    # hvilket produkt den sælger, `check_competitor_prices` dømmer kun de tal
    # der står ved siden af en konkurrent. Beløbet i vores egen knap var en
    # påstand uden dom. Målt 1/10 på alle 84 købsknapper: 70 har beløbet i
    # knappens tekst, 14 har det i en `pt-price` i samme `.pt-foot`
    # (`/paid-templates` EN + DA), og nul afviger fra katalogen — så det er
    # dommen der mangler, ikke en fejl at rette lige nu.
    Step(
        id="own-prices",
        argv=("python3", "tools/check_own_prices.py"),
        inputs=("tools/check_own_prices.py", "tools/stripe_catalog.json",
                "docs/stripe-kontrakt.md", "site/_worker.js", "site/**"),
    ),
    Step(
        id="own-prices-selftest",
        argv=("python3", "tools/check_own_prices.py", "--self-test"),
        inputs=("tools/check_own_prices.py", "tools/stripe_catalog.json",
                "docs/stripe-kontrakt.md", "site/_worker.js", "site/**"),
    ),
    Step(
        id="shared-visits-namespace-tests",
        argv=("python3", "tools/test_shared_visits_namespace.py"),
        inputs=(
            "tools/test_shared_visits_namespace.py",
            "tools/check_shared_visits_namespace.py",
            "site/_worker.js",
        ),
    ),
    # Gratis mod Pro ét sted (2/10). De fire produktsider viste sammenligningen
    # på fire måder, og tre af dem skrev prisen i hånden — ingen port dømte den,
    # fordi `check_own_prices` kun læser købsknapper. Nu er tabellen tegnet af
    # katalogen, og porten dømmer hver blok mod samme kilde.
    Step(
        id="pro-table",
        argv=("python3", "tools/check_pro_table.py"),
        inputs=("tools/check_pro_table.py", "tools/pro_table.py",
                "tools/stripe_catalog.json", "site/**"),
    ),
    Step(
        id="pro-table-selftest",
        argv=("python3", "tools/check_pro_table.py", "--self-test"),
        inputs=("tools/check_pro_table.py", "tools/pro_table.py",
                "tools/stripe_catalog.json"),
    ),
    # Prislisten (2/10). De 12 salgbare produkter lå spredt på otte sider, og
    # ingen side viste to produkter på én gang, så spørgsmålet «hvad koster
    # hele pakken» krævede at gætte. `/pricing` er bygget af
    # `tools/pricing_page.py` fra samme katalog og **sælger ikke**: den
    # linker til hver vares egen købsside, så «én købsvej pr. produkt» holder
    # og de tre porte der bygger på den regel kan blive ved med at være
    # strenge. Dom 3 i porten holder siden fra at få et Stripe-link oveni.
    Step(
        id="pricing-page",
        argv=("python3", "tools/check_pricing_page.py"),
        # Dom 7 og dom 8 læser de sider `pricing_link` **peger på** — de
        # dømmer ankeret og sidens `lang` i den byggede fil — så de er inputs:
        # uden dem springer porten over en commit der fjerner et `id` på
        # `/paid-templates`, retter `#buy` på compliance-siden eller gør en
        # dansk købsside engelsk.
        inputs=("tools/check_pricing_page.py", "tools/pricing_page.py",
                "tools/stripe_catalog.json", "site/pricing.html",
                "site/da/pricing.html", "site/paid-templates.html",
                "site/da/paid-templates.html", "site/clean-copy.html",
                "site/da/clean-copy.html", "site/compliance-report.html",
                "site/da/compliance-report.html", "site/page-profile.html",
                "site/da/page-profile.html", "site/deskuptime/index.html",
                "site/da/deskuptime/index.html"),
    ),
    Step(
        id="pricing-page-selftest",
        argv=("python3", "tools/check_pricing_page.py", "--self-test"),
        # Dom 7 og dom 8 læser de sider `pricing_link` **peger på** — de
        # dømmer ankeret og sidens `lang` i den byggede fil — så de er inputs:
        # uden dem springer porten over en commit der fjerner et `id` på
        # `/paid-templates`, retter `#buy` på compliance-siden eller gør en
        # dansk købsside engelsk.
        inputs=("tools/check_pricing_page.py", "tools/pricing_page.py",
                "tools/stripe_catalog.json", "site/pricing.html",
                "site/da/pricing.html", "site/paid-templates.html",
                "site/da/paid-templates.html", "site/clean-copy.html",
                "site/da/clean-copy.html", "site/compliance-report.html",
                "site/da/compliance-report.html", "site/page-profile.html",
                "site/da/page-profile.html", "site/deskuptime/index.html",
                "site/da/deskuptime/index.html"),
    ),
    # Belæget i katalogens `where` (2/10). Dom 6 og dom 4 i `check_pro_table`
    # dømmer **hvad** der står i tabellen mod katalogen. Men hver funktion
    # bærer også et `where`, der skal sige *hvor* den virkelige kode er, og
    # målt 2/10 læste ingen port de: ni af nitten sider havde `where`-henvisninger,
    # der var flyttet op til ni linjer væk fra den sætning de citerede — så en
    # påstand om hvor kode findes var grøn, selv om den var forkert. Denne port
    # kræver filen, intervallet og citatet, og springer kun submoduler over.
    Step(
        id="catalog-where",
        argv=("python3", "tools/check_catalog_where.py"),
        inputs=("tools/check_catalog_where.py", "tools/stripe_catalog.json",
                "site/**", "extension-clean-copy/**", "page-profile/**"),
    ),
    Step(
        id="catalog-where-selftest",
        argv=("python3", "tools/check_catalog_where.py", "--self-test"),
        inputs=("tools/check_catalog_where.py", "tools/stripe_catalog.json",
                "site/**", "extension-clean-copy/**", "page-profile/**"),
    ),
    # Planen som arbejdskø (opgave 42, 1/10). Opgavens eget acceptkriterium
    # var `awk '/^## STATUS/{f=1;next}…'`, mens overskriften hedder `# STATUS`:
    # mønsteret matcher aldrig, så awk skrev 0 linjer ud for enhver plan og
    # kriteriet var grønt før rettelsen og efter. Denne port dømmer i stedet
    # fire ting — afsnittet skal *findes* (overskrift på alle niveauer), kroppen
    # højst 25 linjer, planen under 40.000 tegn, og hvert punkt skal have et
    # tal et sted i sig. Uden dom 1 er de tre ande lige så døde som awk'en var.
    Step(
        id="plan-status",
        argv=("python3", "tools/check_plan_status.py"),
        inputs=("tools/check_plan_status.py", "IMPLEMENTATION_PLAN.md"),
    ),
    Step(
        id="plan-status-selftest",
        argv=("python3", "tools/check_plan_status.py", "--self-test"),
        inputs=("tools/check_plan_status.py", "IMPLEMENTATION_PLAN.md"),
    ),
    # Købsvejen fra forsiden (5/10). Målt: `mahope.tools/` havde 6 besøgende og
    # 100 % bounce, og `#products` nævnte 2 af katalogens 13 produkter med
    # **0** links til `/pricing` — den eneste side der viser alle 13. Ingen
    # fejl, intet brudt: en vej manglede, og `check_links` kan ikke se det fordi
    # der ikke er nogen død link. Derfor dømmer porten vejen, og dens egen
    # selftest flytter den rigtige prisfil aside så krav 2 kan fejle alene.
    Step(
        id="frontpage-pricing",
        argv=("python3", "tools/check_frontpage_pricing.py"),
        inputs=("tools/check_frontpage_pricing.py", "site/index.html",
                "site/da/index.html", "site/pricing.html", "site/da/pricing.html",
                "tools/stripe_catalog.json"),
    ),
    Step(
        id="frontpage-pricing-selftest",
        argv=("python3", "tools/check_frontpage_pricing.py", "--self-test"),
        inputs=("tools/check_frontpage_pricing.py", "site/index.html",
                "site/da/index.html", "site/pricing.html", "site/da/pricing.html",
                "tools/stripe_catalog.json"),
    ),
    # Workeren skal kunne sige "jeg er død" selv (1/10). Målt først: nul
    # forekomster af "sentry" i hele repoet, mens `/api/url-inspect` lå på
    # 500/1101 på hvert kald og `/api/compliance-ai` svarede 503 i dagevis —
    # begge usynlige. Porten dømmer de otte regler, der gør det trygt: kun
    # produktion, ingen persondata, ingen traces, ingen replay, ingen token,
    # en dæmpning af løkker, og at rapporteringen ikke selv kan kaste.
    Step(
        id="sentry-setup",
        argv=("python3", "tools/check_sentry_setup.py"),
        inputs=("tools/check_sentry_setup.py", "site/_worker.js"),
    ),
    Step(
        id="sentry-setup-selftest",
        argv=("python3", "tools/check_sentry_setup.py", "--self-test"),
        inputs=("tools/check_sentry_setup.py", "site/_worker.js"),
    ),
    # Feature-kø punkt 4 i `IMPLEMENTATION_PLAN.md`: `reportWorkerError` dækker
    # kun workerens egen fetch, så alt der går galt i `site/track.js` eller i en
    # af de 300 sider der indlæser den, efterlod hverken en 500, en log eller en
    # Sentry-hændelse. Sentry sagde «ingen uløste fejl», fordi intet blev sendt.
    # Porten dømmer de elleve regler: at klienten lytter på begge hændelser,
    # sender præcis seks felter, ikke sender siden (den udledes af `referer`
    # server-side), at ruten afviser alt andet med 400, kun kører i produktion,
    # er dæmpet på sin egen tæller og kræver samme origin.
    Step(
        id="client-errors",
        argv=("python3", "tools/check_client_errors.py"),
        inputs=("tools/check_client_errors.py", "site/_worker.js", "site/track.js"),
    ),
    Step(
        id="client-errors-selftest",
        argv=("python3", "tools/check_client_errors.py", "--self-test"),
        inputs=("tools/check_client_errors.py", "site/_worker.js", "site/track.js"),
    ),
    # Opgave 20 i `IMPLEMENTATION_PLAN.md`: scanneren på `/scan` er den eneste
    # vej ind til den dyreste linje i huset (EUComply Pro, $79/år pr. website),
    # og målingen af den var hverken dobbelt eller færdig. Målt 5/10: `scan()`
    # sendte `scan` ved starten *og* igen med en rå fetch efter svaret, så én
    # scanning var to begivenheder, og der var ingen begivenhed ved resultatet
    # eller ved pro-kortets knap. Nu måles hele tragten — `scan`,
    # `scan-findings`/`scan-clean`, `scan-failed`, `pro-card-click` — og
    # porten dømmer begge sprog, fordi en dansk side med sit eget navn deler
    # tragten i to.
    Step(
        id="scan-events",
        argv=("python3", "tools/check_scan_events.py"),
        inputs=("tools/check_scan_events.py", "site/scan.html", "site/scan-da.html",
                "site/_worker.js"),
    ),
    Step(
        id="scan-events-selftest",
        argv=("python3", "tools/check_scan_events.py", "--self-test"),
        inputs=("tools/check_scan_events.py", "site/scan.html", "site/scan-da.html",
                "site/_worker.js"),
    ),
    # `/text-on-image-checker` viste på 390 px sit eneste tal 1739 px nede
    # (2,6 skærmbilleder), fordi `#result` lå under syv nummererede felter og en
    # tagline på 8 linjer. Kernen skriver nu `#verdict` — badge og forholdstal —
    # fra *samme* `sample` som `#result`, og den står som første element efter
    # overskriften. Målt efter: 601 px (EN) / 579 px (DA) i en 664 px fold.
    Step(
        id="verdict-first",
        argv=("python3", "tools/check_verdict_first.py"),
        inputs=("tools/check_verdict_first.py", "site/text-on-image-checker.html",
                "site/text-on-image-checker-da.html", "site/text-on-image-core.js",
                "site/style.css"),
    ),
    Step(
        id="verdict-first-selftest",
        argv=("python3", "tools/check_verdict_first.py", "--self-test"),
        inputs=("tools/check_verdict_first.py", "site/text-on-image-checker.html",
                "site/text-on-image-checker-da.html", "site/text-on-image-core.js",
                "site/style.css"),
    ),
    # Opgave 5/10: scannerens felt lå under folden. `/scan` er mål for 559
    # interne links på 228 sider og er toppen af den $79-linje, mens
    # `/api/results` læser 0 resultater i 28 dage. Folden var badge + `<h1>` +
    # tagline og så et tomt `required`-felt i `<main>`. Formularen ligger nu i
    # `<header class="hero">` med husets `btn-primary` — den egne regel
    # `.scanbox button` (0,1,1) lå oven i `.btn-primary` (0,1,0) — og alle tre
    # skrivninger til `#result` ruller den frem, fordi `#result` ligger under
    # folden og et klik ellers intet gjorde synligt.
    Step(
        id="scan-fold",
        argv=("python3", "tools/check_scan_fold.py"),
        inputs=("tools/check_scan_fold.py", "site/scan.html", "site/scan-da.html"),
    ),
    Step(
        id="scan-fold-selftest",
        argv=("python3", "tools/check_scan_fold.py", "--self-test"),
        inputs=("tools/check_scan_fold.py", "site/scan.html", "site/scan-da.html"),
    ),
    # Review-fund 6/10 (MIDDEL): kommentaren over `SCAN_PROXY_MAX_URLS` sagde
    # «Fem er samme tal som `/api/compliance-scan` tager» — men den betalte rute
    # tager `CSC_MAX_PAGES = 12` pr. kald (summen er præcis 12,fordi den
    # fordeles med `Math.floor(CSC_MAX_PAGES / antal)`). Målt desuden på den
    # **betalte** rute: `/api/report` kalder `cscFetch` præcis én gang, så
    # «It crawls the whole site» i pro-kortene var en løgnest i 18 kort på 9
    # sider. Ingen port dømmer et *antal* i en kommentar eller et pro-kort mod
    # samme antal i koden — den her gør, og tæller kaldene i stedet for at
    # tro på en pæstand.
    Step(
        id="scan-page-claims",
        # `tools/stripe_catalog.json` er et input fra 6/10: dom 5 læser
        # pro-kortene for `eucomply-pro` i katalogen, ikke i filerne. Uden den
        # ville et skift i katalogen springe porten over i cache.
        argv=("python3", "tools/check_scan_page_claims.py"),
        inputs=("tools/check_scan_page_claims.py", "site/_worker.js",
                "site/scan.html", "site/scan-da.html",
                "tools/stripe_catalog.json"),
    ),
    Step(
        id="scan-page-claims-selftest",
        argv=("python3", "tools/check_scan_page_claims.py", "--self-test"),
        inputs=("tools/check_scan_page_claims.py", "site/_worker.js",
                "site/scan.html", "site/scan-da.html",
                "tools/stripe_catalog.json"),
    ),
    # Review-fund 6/10 (MIDDEL): `scans` var en *livslang* tæller (`csc-count`,
    # `expirationTtl: 365 * 86400`) der hed det samme som de vinduesbundne tal i
    # to af tre ruter. Målt med to `curl`: live `/api/health` svarede
    # `{"recentVisits":12, …, "scans":50}` — og `/api/health` er **offentlig**,
    # så en cron kunne rapportere «50 scanninger på to dage». `/api/results`
    # havde fået præfikset i 5/10 (`served_scans_lifetime`); de to andre havde
    # ikke. Samme fælde gjaldt `wl-count` og `ai-ask-count`, som også skrives
    # med et helt års TTL, så rettelsen dømmer hele klassen og ikke tre linjer.
    #
    # Porten kræver en afgørelse for hver `readKvCounter(env, '…')` — enten et
    # `_lifetime`-felt pr. rute eller en `vindue`-begrundelse — og dømmer også at
    # TTL'en på en kumulativ nøgle er et helt år, at det korte navn er væk fra
    # ruten, og at `weekly_report.py` læser præfikset uden en reserve på det
    # gamle navn.
    Step(
        id="lifetime-counters",
        argv=("python3", "tools/check_lifetime_counters.py"),
        inputs=("tools/check_lifetime_counters.py", "site/_worker.js",
                "tools/weekly_report.py"),
    ),
    Step(
        id="lifetime-counters-selftest",
        argv=("python3", "tools/check_lifetime_counters.py", "--self-test"),
        inputs=("tools/check_lifetime_counters.py", "site/_worker.js",
                "tools/weekly_report.py"),
    ),
    # Opgave: AI-banneren lovede et svar, der ikke kunne Gives. Målt først:
    # hver AI-banner på bloggen sagde «a practical answer in seconds» og «Spørg
    # Compliance-AI'en», mens `GET /api/compliance-ai` svarede
    # `available: false` og målsiden siger, at assistenten ikke er slået til.
    # Rettelsen 1/10 gjorde målsiden ærlig, men ikke knapperne på banner-siderne.
    # Nu er sandheden i `tools/ai_cta.json`, banneren er tegnet af den, og porten
    # dømmer hver side — ellers kan banner-siderne glide fra hinanden igen, og
    # løftet kommer tilbage, så snart nogen kører et gammelt script igen.
    Step(
        id="ai-cta-honesty",
        argv=("python3", "tools/check_ai_cta_honesty.py"),
        inputs=("tools/check_ai_cta_honesty.py", "tools/ai_cta.json", "site/**/*.html"),
    ),
    Step(
        id="ai-cta-honesty-selftest",
        argv=("python3", "tools/check_ai_cta_honesty.py", "--self-test"),
        inputs=("tools/check_ai_cta_honesty.py", "tools/ai_cta.json"),
    ),
    # Opgave 47 (8/10): udviklere installerer scanneren allerede selv i CI
    # (91 npm-downloads/uge), men der var ingen action — kunden kopierede et
    # workflow fra /downloads. Handlen afslørede desuden to reelle CLI-fejl:
    # `--sarif` skriv rapporten EFTER fail-on-dommen (en rød CI-kørsel efterlod
    # en tom Security-tab), og `--fail-on never`, som shippede workflow
    # dokumenterer, blev afvist med exit 2. Testen dømmer action.yml, workflow-
    # skabelonen og salgssiden, kører CLI'en for rigtigt, og er rød på tre
    # mutationer — derfor separate steps: kørslen uden mutationerne skal ikke
    # kunne reddes ved at slette mutationerne.
    Step(
        id="eaa-action",
        argv=("node", "tests/eaa-action.test.mjs"),
        inputs=(
            "tests/eaa-action.test.mjs",
            "action.yml",
            "site/downloads/eaa-scan-github-action.yml",
            "site/downloads.html",
            "scanner/npm/eaa-scanner/cli.js",
            "scanner/npm/eaa-scanner/index.js",
        ),
    ),
    Step(
        id="eaa-action-selftest",
        argv=("node", "tests/eaa-action.test.mjs", "--self-test"),
        inputs=(
            "tests/eaa-action.test.mjs",
            "scanner/npm/eaa-scanner/cli.js",
        ),
    ),
)


def dist_built() -> bool:
    dist = ROOT / "dist"
    return dist.is_dir() and any(dist.iterdir())


def all_inputs() -> list[str]:
    """Alle filer der skal kunne udløse deploy-workflowen."""
    seen: list[str] = []
    for step in STEPS:
        for pattern in step.inputs:
            if pattern not in seen:
                seen.append(pattern)
    return sorted(seen)


def documented_gate() -> str:
    """Gaten som den skal læses i planen: én `&&`-linje."""
    return " && ".join(step.command for step in STEPS)


def run(only: str | None = None) -> int:
    steps = [s for s in STEPS if only is None or s.id == only]
    if not steps:
        print(f"quality_gate: ukendt step {only!r}", file=sys.stderr)
        return 2

    have_dist = dist_built()
    # `build` er gaten første step, og en frisk checkout har intet `dist/`.
    # Beslutningen skal derfor tages **igen** efter build — ellers springer CI
    # alle 16 dist-steps over på hver kørsel og melder grøn uden at have kørt
    # dem. Det var målt 1/10 på den grønne kørsel af `c4fd730`:
    # «intet i dist/ — springer 16 dist-steps over: … built-css …», mens den
    # samme kode lokalt var rød i `built-css` med 35 fund.
    bygger = any(s.id == "build" for s in steps)
    if not have_dist and not bygger:
        skipped = [s for s in steps if s.needs_dist]
        if skipped:
            print(f"quality_gate: intet i dist/ — springer {len(skipped)} "
                  f"dist-steps over: {', '.join(s.id for s in skipped)}")
    elif only is not None and only != "build" and have_dist:
        print(f"quality_gate: kører step {only} (dist er bygget)")

    def kør(step: Step) -> tuple[int, float]:
        started = time.monotonic()
        print(f"\n=== {step.id}: {step.command}", flush=True)
        proc = subprocess.run(step.argv, cwd=ROOT)
        elapsed = time.monotonic() - started
        if proc.returncode == 0:
            print(f"--- {step.id}: grøn ({elapsed:.1f}s)", flush=True)
        return proc.returncode, elapsed

    for step in steps:
        if step.needs_dist and not have_dist:
            continue
        returncode, elapsed = kør(step)
        if returncode != 0:
            print(f"\nquality_gate: RØD i step `{step.id}` "
                  f"(`{step.command}`, exit {returncode}, {elapsed:.1f}s)",
                  file=sys.stderr)
            print("quality_gate: de foregående steps var grønne, så fejlen "
                  "er her og ikke i en af dem.", file=sys.stderr)
            return returncode
        # Efter build er `dist/` der, så de 16 dist-steps skal køre i stedet for
        # at blive sprunget over.
        if step.id == "build" and not have_dist:
            have_dist = dist_built()
            if not have_dist:
                print("quality_gate: build kørte grønt, men dist/ er stadig tomt — "
                      "de dist-steps der kræver et bygget site bliver sprunget over.",
                      file=sys.stderr)

    print(f"\nquality_gate: GRØN — {len(steps)} steps")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--list", action="store_true",
                        help="print den dokumenterede gaten som én &&-linje")
    parser.add_argument("--inputs", action="store_true",
                        help="print alle filer der skal være i path-filteret")
    parser.add_argument("--only", help="kør ét step (bruges af porten og CI)")
    args = parser.parse_args(argv)

    if args.list:
        print(documented_gate())
        return 0
    if args.inputs:
        for pattern in all_inputs():
            print(pattern)
        return 0
    return run(args.only)


if __name__ == "__main__":
    raise SystemExit(main())
