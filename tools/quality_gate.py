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
    Step(
        id="seo",
        argv=("python3", "tools/seo_check.py"),
        inputs=("tools/seo_check.py", "build_sites.py"),
        needs_dist=True,
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
    Step(
        id="tracking-worker",
        argv=("node", "tests/tracking-worker.test.mjs"),
        inputs=("tests/tracking-worker.test.mjs", "site/_worker.js"),
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
    Step(
        id="weekly-report-tests",
        argv=("python3", "tools/test_weekly_report.py"),
        inputs=("tools/test_weekly_report.py", "tools/weekly_report.py"),
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
    Step(
        id="design-tokens-selftest",
        argv=("python3", "tools/check_design_tokens.py", "--self-test"),
        inputs=("tools/check_design_tokens.py",),
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
