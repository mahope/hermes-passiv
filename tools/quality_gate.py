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
    # Tak-siden. Den er den eneste bekræftelse en donator får, og den renderer
    # worker's leveringssvar. Uden dette step var der ingen test, der viste at
    # den overhovedet kan vise et svar (opgave 33).
    Step(
        id="thanks-page",
        argv=("node", "tests/thanks-page.test.mjs"),
        inputs=("tests/thanks-page.test.mjs", "site/thanks.html", "site/_worker.js"),
    ),
    Step(
        id="tracking-worker",
        argv=("node", "tests/tracking-worker.test.mjs"),
        inputs=("tests/tracking-worker.test.mjs", "site/_worker.js"),
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
            "site/compliance-site-check.html",
            "site/da/compliance-site-check.html",
            "site/url-inspector/index.html",
        ),
    ),
    Step(
        id="inline-js",
        argv=("python3", "tools/check_inline_js.py"),
        inputs=("tools/check_inline_js.py", "site/**", "site/_worker.js"),
        needs_dist=True,
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
    Step(
        id="storage-claims-selftest",
        argv=("python3", "tools/check_storage_claims.py", "--self-test"),
        inputs=("tools/check_storage_claims.py", "site/_worker.js", "site/**"),
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
        inputs=("tools/test_weekly_report.py", "tools/weekly_report.py"),
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
            "reports/weekly/*.json",
        ),
    ),
    Step(
        id="weekly-code-errors-selftest",
        argv=("python3", "tools/check_weekly_code_errors.py", "--self-test"),
        inputs=(
            "tools/check_weekly_code_errors.py",
            "tools/weekly_report.py",
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
    Step(
        id="shared-visits-namespace-tests",
        argv=("python3", "tools/test_shared_visits_namespace.py"),
        inputs=(
            "tools/test_shared_visits_namespace.py",
            "tools/check_shared_visits_namespace.py",
            "site/_worker.js",
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
    if not have_dist:
        skipped = [s for s in steps if s.needs_dist]
        if skipped:
            print(f"quality_gate: intet i dist/ — springer {len(skipped)} "
                  f"dist-steps over: {', '.join(s.id for s in skipped)}")
    elif only is not None and only != "build":
        print(f"quality_gate: kører step {only} (dist er bygget)")

    for step in steps:
        if step.needs_dist and not have_dist:
            continue
        started = time.monotonic()
        print(f"\n=== {step.id}: {step.command}", flush=True)
        proc = subprocess.run(step.argv, cwd=ROOT)
        elapsed = time.monotonic() - started
        if proc.returncode != 0:
            print(f"\nquality_gate: RØD i step `{step.id}` "
                  f"(`{step.command}`, exit {proc.returncode}, {elapsed:.1f}s)",
                  file=sys.stderr)
            print("quality_gate: de foregående steps var grønne, så fejlen "
                  "er her og ikke i en af dem.", file=sys.stderr)
            return proc.returncode
        print(f"--- {step.id}: grøn ({elapsed:.1f}s)", flush=True)

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
