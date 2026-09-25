#!/usr/bin/env python3
"""Gate for de døde SEO- og deploystier, opgave 15 i `IMPLEMENTATION_PLAN.md`.

21 bloggeneratorer skrev stadig til `site/sitemap.xml`, en fil builden aldrig
læser: `build_sites.py` springer den over i `SKIP_NAMES` og skriver i stedet
`dist/<domaene>/sitemap.xml`. Generatorerne skrev derfor URL'er ind i en fil,
udgav "Sitemap updated: N URLs", og intet blev nogensinde publiceret. To af dem
brugte desuden en hardkodet hjemmesti (`/Users/madsholstjensen/hermes-passiv/…`),
så de kun kørte på én maskine.

`indexnow_ping.sh` havde `HOST="hermes-passiv.pages.dev"`, som ikke er et
deployet Pages-projekt, så dens egen nøgl-selftest fejlede med "deploy first"
hver gang den blev kørt — altså et helbredsscript der så ud til at virke, men
kun rapporterede en død vært. Nøglen ligger på alle tre rigtige domæner.

Gaten fejler ved:

1. `site/sitemap.xml` findes igen — den skal være slettet, for builden ejer
   sitemapperne.
2. Et script (`.py`/`.sh`) referererer til den døde kilde-sitemap. Ren
   nævnes-per-fil: generatorerne må ikke ramme den igen.
3. Et aktivt helbreds- eller deployscript peger på `hermes-passiv.pages.dev`.
4. `deploy.sh` ikke er den dokumenterede nægtelse, eller en fil beder om
   manuel Pages-upload. Der er én udgivelsesvej: merge til `main`.

    python3 tools/check_legacy_seo_paths.py
    python3 tools/check_legacy_seo_paths.py --self-test

Denne gate dækker ikke `site/_worker.js`, `site/openapi.yaml` eller den
shippede GitHub-Actions-skabelon, som stadig nævner den døde vært. De er
noteret som opgave 19 i planen, fordi `_worker.js` kræver worker-tests, der
ikke er skrevet endnu.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Den vært, der aldrig har været et live-domæne. Findes i historiske
# generatorers URL-konstanter og i `_worker.js`; de aktive scripts må ikke.
DEAD_HOST = "hermes-passiv.pages.dev"

# Kildefilens sitemap. Builden springer den over og skriver dist-sitemapper.
DEAD_SOURCE_SITEMAP = "site/sitemap.xml"

# Kun scripts. `IMPLEMENTATION_PLAN.md` skal kunne *nævne* stien som
# opgavetext, og historiske sider i `site/` skal kunne linke til /sitemap.xml.
SCRIPT_SUFFIXES = (".py", ".sh")

# Sunde aktive scripts, der springes over med vilje: de er negative
# testtilfælde, hvor den døde vært er pointen. Holdes her, ikke i en
# navne-liste-som-fraviges-andetsteds.
ALLOWED_DEAD_HOST_FILES = {
    "tests/tracking-worker.test.mjs",
    "tools/test_license_flow.js",
    "test.js",
    "obsidian-plugin/test.js",
}

# Gaten skal kunne *nævne* den sti den forbyder, ellers kan den ikke sige
# hvad den kigger efter. Derfor undtager den sig selv — og kun sig selv, så
# en ny fil med samme fejl stadig fanges.
GATE_SELF = "tools/check_legacy_seo_paths.py"

# Filer der springes over ved skanning af scripts. Samme regelprincip som
# `check_license_clients.py`: en mappe med sin egen `.git` er ikke vores kode.
# `auditedwp-src` står her til forsikring, fordi CI's side-checkout hedder
# netop det — reglen under er den egentlige beskyttelse, ikke denne linje.
SKIP_DIRS = {".git", "dist", "node_modules", ".wrangler", "build", "__pycache__",
             "auditedwp-src", "auditedwp"}


def _is_external_checkout(path: Path, root: Path) -> bool:
    """Sand hvis `path` ligger inde i et andet git-repo end `root`.

    CI checkouter `../auditedwp` *ved siden af* workspace, så den havner
    inde i `ROOT` og aldrig lokalt. `.git` ligger i sådanne checkouts i
    checkoutens egen rod — altså et *forfader*-directory af filen, ikke
    nødvendigvis dens forældre. Derfor ledes der op ad hele kæden. Kun
    op til `root`: `root` selv har et `.git`, som ikke må gøre os til et
    eksternt checkout.
    """
    for parent in path.resolve().parents:
        if parent == root.resolve() or parent == parent.parent:
            return False
        if (parent / ".git").exists():
            return True
    return False


def _script_files(root: Path) -> dict[str, str]:
    """Alle `.py`/`.sh` under `root`, minus eksterne checkouts."""
    found: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix not in SCRIPT_SUFFIXES:
            continue
        if SKIP_DIRS & set(path.relative_to(root).parts):
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if _is_external_checkout(path, root):
            continue
        try:
            found[path.relative_to(root).as_posix()] = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
    return found


def check_source_sitemap_gone(root: Path) -> list[str]:
    """Punkt 1 — kildefilens sitemap skal være slettet."""
    dead = root / DEAD_SOURCE_SITEMAP
    if dead.exists():
        return [f"{DEAD_SOURCE_SITEMAP} findes igen — builden springer den over "
                f"(SKIP_NAMES), så intet i den publiceres"]
    return []


def check_no_script_touches_source_sitemap(scripts: dict[str, str]) -> list[str]:
    """Punkt 2 — intet script må ramme den døde kilde-sitemap."""
    problems = []
    for name, text in scripts.items():
        if name == GATE_SELF:
            continue
        if DEAD_SOURCE_SITEMAP in text:
            line = next((i for i, l in enumerate(text.splitlines(), 1)
                         if DEAD_SOURCE_SITEMAP in l), 0)
            problems.append(f"{name}:{line} refererer til {DEAD_SOURCE_SITEMAP} — "
                            f"build_sites.py ejer sitemapperne (dist/<domaene>/sitemap.xml)")
    return problems


def check_active_scripts_have_live_host(scripts: dict[str, str]) -> list[str]:
    """Punkt 3 — et aktivt helbreds-/deployscript må ikke pege på den døde vært."""
    problems = []
    for name, text in scripts.items():
        if name in ALLOWED_DEAD_HOST_FILES or not name.endswith(".sh"):
            continue
        if DEAD_HOST in text:
            line = next((i for i, l in enumerate(text.splitlines(), 1) if DEAD_HOST in l), 0)
            problems.append(f"{name}:{line} peger på {DEAD_HOST}, som ikke er et "
                            f"live-domæne")
    return problems


def check_single_deploy_path(root: Path, files: dict[str, str]) -> list[str]:
    """Punkt 4 — én dokumenteret, idempotent udgivelsesvej."""
    problems = []
    deploy = root / "deploy.sh"
    if not deploy.exists():
        return ["deploy.sh mangler — den skal være den dokumenterede nægtelse"]
    text = deploy.read_text(encoding="utf-8", errors="replace")
    if not re.search(r"Manuel deploy er deaktiveret", text):
        problems.append("deploy.sh skal være den dokumenterede nægtelse "
                        "(merge til main, lad CI udgive)")
    if re.search(r"wrangler\s+pages\s+deploy", text):
        problems.append("deploy.sh må ikke selv køre `wrangler pages deploy`")
    for name, body in files.items():
        if name in (GATE_SELF, "deploy.sh"):
            continue
        for i, line in enumerate(body.splitlines(), 1):
            if re.search(r"wrangler\s+pages\s+deploy", line) and not line.strip().startswith(("#", "*")):
                problems.append(f"{name}:{i} beder om manuel Pages-upload — "
                                f"udgivelsesvejen er merge til main")
    return problems


def run(root: Path) -> list[str]:
    scripts = _script_files(root)
    problems = []
    problems += check_source_sitemap_gone(root)
    problems += check_no_script_touches_source_sitemap(scripts)
    problems += check_active_scripts_have_live_host(scripts)
    problems += check_single_deploy_path(root, scripts)
    return problems


def self_test() -> int:
    """Bevis at gaten fanger hver fejlform, den siger at fange."""
    import tempfile

    scenarios: list[tuple[str, list[str]]] = []
    control: list[str] = []

    healthy = {
        "indexnow_ping.sh": '#!/bin/bash\nHOSTS="mahope.tools cleancopy.tools deskuptime.com"\n',
        "tools/make_blog_x.py": 'sm = "dist/mahope.tools/sitemap.xml"\n',
    }
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "tools").mkdir()
        (root / "site").mkdir()
        for name, body in healthy.items():
            (root / name).write_text(body, encoding="utf-8")
        (root / "deploy.sh").write_text(
            "#!/bin/zsh\nprintf 'FEJL: Manuel deploy er deaktiveret.\\n' >&2\nexit 2\n",
            encoding="utf-8")

        # Positiv kontrol på de rigtige filer, så mutationerne ikke kan stå
        # som bevis fordi reglen slås alt fra.
        control = run(root)
        if control:
            for problem in control:
                print(f"KONTROLFEJL: {problem}", file=sys.stderr)
            return 1

        # 1 — kildefilens sitemap findes igen
        (root / DEAD_SOURCE_SITEMAP).write_text("<urlset></urlset>", encoding="utf-8")
        scenarios.append(("kildefilens sitemap findes igen",
                          check_source_sitemap_gone(root)))
        (root / DEAD_SOURCE_SITEMAP).unlink()

        # 2 — et script rammer den døde kilde-sitemap
        (root / "tools/make_blog_x.py").write_text(
            'sm_path = "site/sitemap.xml"\nopen(sm_path, "w").write(x)\n', encoding="utf-8")
        scenarios.append(("et script skriver i kildefilens sitemap",
                          check_no_script_touches_source_sitemap(_script_files(root))))
        (root / "tools/make_blog_x.py").write_text(healthy["tools/make_blog_x.py"], encoding="utf-8")

        # 3 — et helbredsscript peger på den døde vært
        (root / "indexnow_ping.sh").write_text(
            f'#!/bin/bash\nHOST="{DEAD_HOST}"\n', encoding="utf-8")
        scenarios.append(("et helbredsscript peger på den døde vært",
                          check_active_scripts_have_live_host(_script_files(root))))
        (root / "indexnow_ping.sh").write_text(healthy["indexnow_ping.sh"], encoding="utf-8")

        # 4a — deploy.sh er ikke nægtelsen
        (root / "deploy.sh").write_text("#!/bin/zsh\nexit 0\n", encoding="utf-8")
        scenarios.append(("deploy.sh er ikke den dokumenterede nægtelse",
                          check_single_deploy_path(root, _script_files(root))))

        # 4b — en fil beder om manuel Pages-upload
        (root / "deploy.sh").write_text(
            "#!/bin/zsh\nprintf 'FEJL: Manuel deploy er deaktiveret.\\n' >&2\nexit 2\n",
            encoding="utf-8")
        (root / "tools/publish.sh").write_text(
            "#!/bin/bash\nnpx wrangler pages deploy dist --project-name=x\n", encoding="utf-8")
        scenarios.append(("en fil beder om manuel Pages-upload",
                          check_single_deploy_path(root, _script_files(root))))
        (root / "tools/publish.sh").unlink()

        # 4c — en kommentar der nævner kommandoen må ikke fejle
        (root / "tools/publish.sh").write_text(
            "#!/bin/bash\n# aldrig: npx wrangler pages deploy dist\nexit 0\n", encoding="utf-8")
        no_false_positive = check_single_deploy_path(root, _script_files(root))
        (root / "tools/publish.sh").unlink()
        if no_false_positive:
            for problem in no_false_positive:
                print(f"FALSK POSITIV: {problem}", file=sys.stderr)
            return 1

        # 5 — CI's side-checkout. Kørsel 36194467339 døde i `legacy-seo-paths`
        # på `auditedwp-src/site/deploy.sh`: CI checkouter auditedwp VED SIDEN
        # af workspace, så mappen ligger inde i ROOT og aldrig lokalt, og
        # `.git` ligger i checkoutens rod — et forfaderdirectory, ikke
        # filens egen forælder. Første rettelse ledede kun ét niveau op og
        # fangede det ikke.
        (root / "vendored").mkdir()
        (root / "vendored" / ".git").mkdir()
        (root / "vendored" / "site").mkdir()
        (root / "vendored" / "site" / "deploy.sh").write_text(
            "#!/bin/zsh\nnpx wrangler pages deploy dist\nexit 0\n", encoding="utf-8")
        external = _script_files(root)
        if any(name.startswith("vendored/") for name in external):
            print("FEJL: et eksternt checkout blev ikke sprunget over", file=sys.stderr)
            return 1
        # …men vores egen kode skal stadig fejle, så reglen har ikke slået
        # alt fra — præcis som de 11/11 i `check_license_clients.py`.
        (root / "tools/publish.sh").write_text(
            "#!/bin/bash\nnpx wrangler pages deploy dist\nexit 0\n", encoding="utf-8")
        still = check_single_deploy_path(root, _script_files(root))
        (root / "tools/publish.sh").unlink()
        if not still:
            print("FEJL: reglen slår alt fra — vores egen kode fanges ikke", file=sys.stderr)
            return 1

    failed = 0
    for name, problems in scenarios:
        if problems:
            print(f"OK   {name} -> {problems[0]}")
        else:
            print(f"FEJL mutationen blev ikke fanget: {name}", file=sys.stderr)
            failed += 1
    if not scenarios:
        print("FEJL: ingen scenarier", file=sys.stderr)
        return 1
    print(f"legacy-seo-paths selftest OK — {len(scenarios)} mutationer fanget, "
          f"positiv kontrol grøn")
    return 1 if failed else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true",
                        help="bevis at gaten fanger hver fejlform, den siger at fange")
    args = parser.parse_args()

    if args.self_test:
        return self_test()

    problems = run(ROOT)
    for problem in problems:
        print(f"FEJL: {problem}", file=sys.stderr)
    if problems:
        return 1
    scripts = _script_files(ROOT)
    print(f"legacy-seo-paths OK — {len(scripts)} scripts, ingen døde "
          f"kilde-sitemap-stier, ingen død vært i helbredsscripts, én udgivelsesvej")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
