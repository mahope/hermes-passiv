#!/usr/bin/env python3
"""Gate for GitHub-workflows' triggere, permissions og jobs.

Baggrund (opgave 16, 25. september 2026): `build-desktop.yml` har ikke kørt
siden 25. august 2026. Rodårsagen var commit `6766501`, som lagde `tags:` ved
siden af `paths:` i *samme* `on.push`-mapping. GitHub filtrerer begge filtre på
hvert push, en branch-push er aldrig et tag, så workflowen blev tag-only, og
ethvert push til `main` der rørte `desktop/` sprang over. Opgave 9, 12 og enhver
fremtidig desktop-ændring brugte den matrix som sin eneste platformdækning, så
en opgradering der kun virker på macOS ville passere gaten grøn.

En YAML-læsning kan ikke bevise en trigger. Derfor simulerer denne gate de
faktiske events mod workflowens egne filtre med GitHubs dokumenterede
filtersemantik:

- `on.push` (eller `pull_request`) i **listeform** er en række uafhængige
  udløsere, og et push rammer den første den matcher (OR).
- En enkelt mapping med både `branches` og `tags` er en AND: en branch-push
  kan ikke være et tag, så den matcher aldrig. Det er præcis den fejlform
  opgaven retter, og derfor er den modelleret ærligt i stedet for at være
  håndkodet som "fejl".
- `paths`/`paths-ignore` filtreres på de ændrede filer, med `**` der matcher
  også `/` og `*` der ikke gør. `!foo` i `paths` er en eksklusion.

Kun triggere, permissions og jobnavn dækkes her. Om et byg faktisk er grønt er
CI's eget job, og det er derfor denne gate aldrig erstatter en rigtig kørsel.

    python3 tools/test_deploy_workflow.py             # gate
    python3 tools/test_deploy_workflow.py --self-test
"""
from __future__ import annotations

import argparse
import copy
import re
import sys
from pathlib import Path
from typing import Any, Iterable

import yaml

ROOT = Path(__file__).resolve().parent.parent
WORKFLOWS = {
    "desktop": ".github/workflows/build-desktop.yml",
    "deploy": ".github/workflows/deploy-sites.yml",
}

DESKTOP_JOBS = ("build-macos", "build-linux", "build-windows")
DESKTOP_TAG = "eaa-scanner-desktop-v1.4.0"


# --------------------------------------------------------------------------
# Indlæsning
# --------------------------------------------------------------------------
def load(rel: str) -> dict[str, Any]:
    path = ROOT / rel
    if not path.is_file():
        raise SystemExit(f"FEJL: mangler {rel}")
    # `on` er YAML 1.1's bool-værdi, så PyYAML giver nøglen som True.
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit(f"FEJL: {rel} er ikke et workflow-objekt")
    data["on"] = data.get("on", data.get(True))
    if data["on"] is None:
        raise SystemExit(f"FEJL: {rel} mangler `on:`")
    return data


def event(workflow: dict[str, Any], name: str) -> Any:
    on = workflow.get("on") or {}
    if not isinstance(on, dict) or name not in on:
        return None
    # `workflow_dispatch:` uden værdi er None i YAML — det er en gyldig
    # udløser, så tilstedeværelse af nøglen er det der tæller.
    return on[name] if on[name] is not None else {}


# --------------------------------------------------------------------------
# GitHub-filtersemantik
# --------------------------------------------------------------------------
def _pattern_regex(pattern: str) -> re.Pattern[str]:
    """Én GitHub-glob → regex. `**` krydser `/`, `*` gør ikke."""
    out: list[str] = []
    i = 0
    while i < len(pattern):
        char = pattern[i]
        if pattern.startswith("**", i):
            out.append(".*")
            i += 2
        elif char == "*":
            out.append("[^/]*")
            i += 1
        elif char == "?":
            out.append("[^/]")
            i += 1
        else:
            out.append(re.escape(char))
            i += 1
    return re.compile("^" + "".join(out) + "$")


def _any_match(patterns: Iterable[str], value: str) -> bool:
    return any(_pattern_regex(p).match(value) for p in patterns)


def _as_list(value: Any) -> list[str] | None:
    if value is None:
        return None
    return [value] if isinstance(value, str) else list(value)


def _matches(filt: dict[str, Any], *, ref: str, base_ref: str | None,
             paths: list[str]) -> bool:
    """Én enkelt `on.<event>`-mapping: matcher den eventet?"""
    is_tag = ref.startswith("refs/tags/")
    is_branch = ref.startswith("refs/heads/")

    branches = _as_list(filt.get("branches"))
    tags = _as_list(filt.get("tags"))
    # GitHub definerer `branches` for push mod den pushede ref, og for
    # pull_request mod base-ref'en.
    branch_ref = ref[len("refs/heads/"):] if is_branch else (base_ref or "")

    if branches is not None and (not is_branch or not _any_match(branches, branch_ref)):
        return False
    if tags is not None and (not is_tag or not _any_match(tags, ref[len("refs/tags/"):])):
        return False
    if branches is None and tags is None and is_tag and is_branch:
        return False

    changed = filt.get("paths")
    if changed is not None:
        positive = [p for p in changed if not p.startswith("!")]
        negative = [p[1:] for p in changed if p.startswith("!")]
        if positive and not any(_any_match(positive, p) for p in paths):
            return False
        if any(_any_match(negative, p) for p in paths):
            return False

    ignore = filt.get("paths-ignore")
    if ignore is not None and any(_any_match(_as_list(ignore) or [], p) for p in paths):
        return False

    ignore_branches = _as_list(filt.get("branches-ignore"))
    if ignore_branches is not None and is_branch and _any_match(ignore_branches, branch_ref):
        return False
    return True


def triggers(workflow: dict[str, Any], name: str, *, ref: str, base_ref: str | None = None,
             paths: Iterable[str] = ()) -> bool:
    """Udløser `workflow` eventet `name` med denne ref og disse ændrede filer?"""
    filt = event(workflow, name)
    if filt is None:
        return False
    files = list(paths)
    if isinstance(filt, list):
        # Listeform: OR over elementerne. GitHub afviser blandede mappings/
        # strenge i samme liste, så alt antages at være mappings.
        return any(
            _matches(item, ref=ref, base_ref=base_ref, paths=files)
            for item in filt
            if isinstance(item, dict)
        )
    if isinstance(filt, str):
        return filt == name
    if not isinstance(filt, dict):
        # `workflow_dispatch:` uden filtre — enhver kørsel på main er nok for
        # de gates, der spørger om en manuel udløser findes.
        return True
    # `pull_request` har ingen pushet branch; `branches` filtrerer på base-ref.
    push_ref = ref if name == "push" else (f"refs/heads/{base_ref}" if base_ref else ref)
    return _matches(filt, ref=push_ref, base_ref=base_ref, paths=files)


def push(workflow: dict[str, Any], ref: str, *paths: str) -> bool:
    return triggers(workflow, "push", ref=ref, paths=paths)


# --------------------------------------------------------------------------
# Checks
# --------------------------------------------------------------------------
def check_desktop(wf: dict[str, Any], label: str) -> list[str]:
    """Opgave 16s acceptkriterier for `build-desktop.yml`."""
    problems: list[str] = []
    desktop = f"{label}: build-desktop.yml"

    if not push(wf, "refs/heads/main", "desktop/package.json"):
        problems.append(f"{desktop}: et push til main der rører desktop/** udløser "
                        "ikke build-jobbene — så er der ingen Linux- og "
                        "Windows-verificering")
    if not push(wf, "refs/heads/main", ".github/workflows/build-desktop.yml"):
        problems.append(f"{desktop}: et push til main der kun retter workflowen "
                        "selv udløser ikke noget")
    if push(wf, "refs/heads/main", "site/index.html", "IMPLEMENTATION_PLAN.md"):
        problems.append(f"{desktop}: et push til main uden desktop/** udløser "
                        "build-jobbene og spilder matrixen")
    if not push(wf, f"refs/tags/{DESKTOP_TAG}", "desktop/package.json"):
        problems.append(f"{desktop}: taget {DESKTOP_TAG} udløser ikke build-jobbene, "
                        "så en ny udgivelse kan ikke bygges")
    if push(wf, "refs/tags/v1.0.0", "desktop/package.json"):
        problems.append(f"{desktop}: et vilkårligt tag (v1.0.0) udløser build-jobbene")
    if push(wf, "refs/heads/ceo/desktop-ci-trigger", "desktop/package.json"):
        problems.append(f"{desktop}: et push til en sidegren udløser matrixen to "
                        "gange pr. PR (pull_request dækker det allerede)")

    if not triggers(wf, "pull_request", ref="refs/pull/7/merge", base_ref="main",
                    paths=["desktop/main.js"]):
        problems.append(f"{desktop}: et PR mod main der rører desktop/** udløser "
                        "ikke bygningen")

    jobs = wf.get("jobs") or {}
    for job in DESKTOP_JOBS:
        if job not in jobs:
            problems.append(f"{desktop}: jobbet `{job}` mangler")
    mac_arch = ((jobs.get("build-macos") or {}).get("strategy") or {}).get("matrix", {})
    if "arch" not in (mac_arch or {}):
        problems.append(f"{desktop}: build-macos har ingen arch-matrix, så kun ét "
                        "macOS-artefakt bygges")

    release = jobs.get("release") or {}
    needs = release.get("needs")
    needs = [needs] if isinstance(needs, str) else list(needs or [])
    for job in DESKTOP_JOBS:
        if job not in needs:
            problems.append(f"{desktop}: release har ikke `needs: {job}`, så den "
                            "kan frigive før bygningerne er grønne")

    # Kun release må skrive. Ellers har et kompromitteret byggetræn skriveadgang
    # til repoet i alle tre build-jobs.
    top = (wf.get("permissions") or {}).get("contents")
    if top != "read":
        problems.append(f"{desktop}: topniveau-permissions er `contents: {top}`, "
                        "skal være read")
    for job, spec in jobs.items():
        contents = (spec.get("permissions") or {}).get("contents")
        if contents == "write" and job != "release":
            problems.append(f"{desktop}: jobbet `{job}` har contents: write, men kun "
                            "release har brug for det")
    if (release.get("permissions") or {}).get("contents") != "write":
        problems.append(f"{desktop}: release mangler contents: write og kan ikke "
                        "oprette et release")
    return problems


def check_deploy(wf: dict[str, Any], label: str) -> list[str]:
    """Deploy-workflowens filtre må ikke blive rørt af desktop-rettelsen."""
    problems: list[str] = []
    site = f"{label}: deploy-sites.yml"

    if not push(wf, "refs/heads/main", "site/index.html"):
        problems.append(f"{site}: et push til main der rører site/** deployer ikke")
    if push(wf, "refs/heads/ceo/fix", "site/index.html"):
        problems.append(f"{site}: et push til en sidegren deployer")
    if push(wf, "refs/heads/main", "desktop/package.json"):
        problems.append(f"{site}: en desktop-ændring deployer sites — den skal kun "
                        "køre build-desktop.yml")
    if not triggers(wf, "workflow_dispatch", ref="refs/heads/main"):
        problems.append(f"{site}: workflow_dispatch mangler, så et deploy ikke kan "
                        "køres manuelt")
    for needed in ("tools/seo_check.py", "tools/brand.py", "tools/pagepass.py",
                   "tests/stripe-worker.test.mjs"):
        if not push(wf, "refs/heads/main", needed):
            problems.append(f"{site}: path-filteret mangler `{needed}`, selv om "
                            "filen påvirker build eller gate")
    for job, spec in (wf.get("jobs") or {}).items():
        if (spec.get("permissions") or {}).get("contents") == "write":
            problems.append(f"{site}: jobbet `{job}` har contents: write uden grund")
    return problems


# --------------------------------------------------------------------------
# Selftest — bevis at gaten fanger hver fejlform
# --------------------------------------------------------------------------
def _expect(problems: list[str], fragment: str, label: str, ok: bool) -> bool:
    if ok:
        return True
    print(f"FEJL: selftesten `{label}` forventede en fejl med {fragment!r}, "
          f"fik: {problems or 'ingen fejl'}", file=sys.stderr)
    return False


def self_test() -> int:
    real = {name: load(rel) for name, rel in WORKFLOWS.items()}
    ok = True

    # 0. De rigtige workflows skal være grønne, ellers beviser resten intet.
    for name, wf in real.items():
        found = check_desktop(wf, name) if name == "desktop" else check_deploy(wf, name)
        if found:
            print(f"FEJL: den rigtige {name}-workflow har fejl: {found}", file=sys.stderr)
            ok = False

    # 1. Tilbage til 6766501s tag-only-form. Mutationen skal gengive præcis
    #    fejlformen fra 25. august: taget kører, branch-push gør ikke. Tjekkes
    #    begge veje, så mutationen ikke "beviser" noget ved et uventet match.
    tag_only = copy.deepcopy(real["desktop"])
    filt = tag_only["on"]["push"]
    tag_only["on"]["push"] = [{
        "paths": filt[0]["paths"],
        "tags": filt[1]["tags"],
    }]
    problems = check_desktop(tag_only, "6766501-formen")
    ok &= _expect(problems, "udløser ikke build-jobbene", "tag-only", bool(problems))
    if not push(tag_only, f"refs/tags/{DESKTOP_TAG}", "desktop/package.json"):
        print("FEJL: mutationen er ikke 6766501-formen — tag-push skal stadig "
              "udløse, det var den eneste kørsel workflowen havde", file=sys.stderr)
        ok = False
    if any("udgivelse" in p for p in problems):
        print(f"FEJL: 6766501-formen tabte tag-udløsningen, hvilket er en anden "
              f"fejl end den historiske: {problems}", file=sys.stderr)
        ok = False

    # 2. Tag-udløsningen forsvundet.
    no_tags = copy.deepcopy(real["desktop"])
    no_tags["on"]["push"] = [f for f in no_tags["on"]["push"] if "tags" not in f]
    problems = check_desktop(no_tags, "uden tag-filter")
    ok &= _expect(problems, "udløser ikke build-jobbene, så en ny udgivelse",
                 "uden-tags", any("udgivelse" in p for p in problems))

    # 3. Path-filteret forsvundet: matrixen kører på ethvert push.
    no_paths = copy.deepcopy(real["desktop"])
    for filt in no_paths["on"]["push"]:
        filt.pop("paths", None)
    problems = check_desktop(no_paths, "uden path-filter")
    ok &= _expect(problems, "uden desktop/** udløser", "uden-paths",
                 any("uden desktop/**" in p for p in problems))

    # 4. Skriveadgang på hele workflowen igen.
    wide = copy.deepcopy(real["desktop"])
    wide["permissions"] = {"contents": "write"}
    problems = check_desktop(wide, "skriveadgang")
    ok &= _expect(problems, "skal være read", "wide-permissions",
                 any("skal være read" in p for p in problems))

    # 5. Release uden skriveadgang kan ikke frigive.
    no_release_perm = copy.deepcopy(real["desktop"])
    no_release_perm["jobs"]["release"]["permissions"] = {"contents": "read"}
    problems = check_desktop(no_release_perm, "release read")
    ok &= _expect(problems, "mangler contents: write", "release-read",
                 any("mangler contents: write" in p for p in problems))

    # 6. Deploy-workflowen taber et buildinput.
    thin_deploy = copy.deepcopy(real["deploy"])
    thin_deploy["on"]["push"]["paths"] = [
        p for p in thin_deploy["on"]["push"]["paths"] if p != "tools/seo_check.py"
    ]
    problems = check_deploy(thin_deploy, "tyndt filter")
    ok &= _expect(problems, "tools/seo_check.py", "tyndt-filter",
                 any("tools/seo_check.py" in p for p in problems))

    print(f"test_deploy_workflow selftest {'OK' if ok else 'FEJLEDE'}")
    return 0 if ok else 1


def run_all(workflows: dict[str, Any]) -> list[str]:
    problems: list[str] = []
    if "desktop" not in workflows:
        problems.append("mangler build-desktop.yml")
    if "deploy" not in workflows:
        problems.append("mangler deploy-sites.yml")
    if "desktop" in workflows:
        problems += check_desktop(workflows["desktop"], "repo")
    if "deploy" in workflows:
        problems += check_deploy(workflows["deploy"], "repo")
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--self-test", action="store_true",
                        help="bevis at gaten fanger hver fejlform, den siger at fange")
    args = parser.parse_args(argv)

    if args.self_test:
        return self_test()

    problems: list[str] = []
    for name, rel in WORKFLOWS.items():
        try:
            wf = load(rel)
        except SystemExit as exc:
            problems.append(str(exc))
            continue
        problems += check_desktop(wf, name) if name == "desktop" else check_deploy(wf, name)

    for problem in problems:
        print(f"FEJL: {problem}", file=sys.stderr)
    if problems:
        return 1
    print(f"deploy-workflows OK — {len(WORKFLOWS)} workflows, "
          "build-desktop udløser på main+paths og på tag, deploy kun på main+site/**")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
