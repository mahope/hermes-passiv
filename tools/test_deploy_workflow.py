#!/usr/bin/env python3
"""Gate for GitHub-workflows' triggere, permissions, jobs og gaten selv.

Baggrund (opgave 16, 25. september 2026): `build-desktop.yml` har ikke kørt
siden 25. august 2026. Rodårsagen var commit `6766501`, som lagde `tags:` ved
siden af `paths:` i *samme* `on.push`-mapping. GitHub filtrerer begge filtre på
hvert push, en branch-push er aldrig et tag, så workflowen blev tag-only, og
ethvert push til `main` der rørte `desktop/` sprang over. Opgave 9, 12 og enhver
fremtidig desktop-ændring brugte den matrix som sin eneste platformdækning, så
en opgradering der kun virker på macOS ville passere gaten grøn.

Baggrund del 2 (opgave 11, 25. september 2026): gaten var dokumenteret i planen
som én `&&`-linje, mens CI kørte tre separate, kortere lister. Tre lister kan
ikke bevise at de er ens. Listen har nu én ejer, `tools/quality_gate.py`, og de
tjek her er beviset på at CI faktisk bruger den:

- Deploy-workflowen skal kalde `python3 tools/quality_gate.py` — præcis den
  kommando, og ingen gatestræk må derudover være skrevet ud i en `run:`-blok.
- Hvert deploy-job skal `needs:` det job der kører gaten, så en fælles gatefejl
  dræber alle domæner i stedet for at sende dem videre hver for sig.
- Path-filteret skal dække **hver** fil `quality_gate.py` erklærer, at den
  læser. Glob-input udvides mod den rigtige filstruktur, så `site/**` testes mod
  de filer der faktisk ligger under `site/`.
- `auditedwp` skal være pinnet til én 40-tegns SHA i alle jobs.

Baggrund del 3 (opgave 12, 25. september 2026): Node-versionen stod som
`node-version: '22'` i alle tre build-jobs, `engines` manglede i
`desktop/package.json`, og `.nvmrc` fandtes ikke — mens Electron 44 kræver
`>=22.12.0`. `check_desktop_runtime` gør runtimeen til én erklæring: den skal
findes i `.nvmrc`, den skal opfylde `engines.node`, alle tre jobs skal læse den
derfra, og den skal være i path-filteret så en runtime-bump bygger noget.

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
import json
import re
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mini_yaml import YamlSubsetError, parse  # noqa: E402
from quality_gate import STEPS as GATE_STEPS  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
WORKFLOWS = {
    "desktop": ".github/workflows/build-desktop.yml",
    "deploy": ".github/workflows/deploy-sites.yml",
}

DESKTOP_JOBS = ("build-macos", "build-linux", "build-windows")
DESKTOP_TAG = "eaa-scanner-desktop-v1.4.0"

# Den ene kommando der må køre gaten. Helt navn, ikke et mønster: en
# `run:`-blok med `python3 tools/quality_gate` uden `.py` ville køre intet.
GATE_COMMAND = "python3 tools/quality_gate.py"

# Mapper der springes over ved filoptælling: byguddata, ikke kilder.
WALK_SKIP = {".git", "dist", "node_modules", "__pycache__", ".wrangler", "vendor"}


# --------------------------------------------------------------------------
# Indlæsning
# --------------------------------------------------------------------------
def load(rel: str) -> dict[str, Any]:
    path = ROOT / rel
    if not path.is_file():
        raise SystemExit(f"FEJL: mangler {rel}")
    try:
        data = parse(path.read_text(encoding="utf-8"))
    except YamlSubsetError as exc:
        raise SystemExit(f"FEJL: {rel} kunne ikke læses: {exc}")
    if not isinstance(data, dict):
        raise SystemExit(f"FEJL: {rel} er ikke et workflow-objekt")
    if data.get("on") is None:
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

    # En ref-type uden filter springes over: definerer workflowen KUN `tags`,
    # kører intet på et branch-push. Det er præcis den fejl, der lå bag
    # `6766501` (25. august 2026) og som holdt desktop-CI'en død i en måned.
    # Hver ref-type kræver sit eget filter. En workflow med KUN `tags` kører
    # aldrig på et branch-push, og en med KUN `branches` aldrig på et
    # tag-push — det er den regel, `6766501` brød ved at slette `branches`.
    # Er begge defineret, matcher hver sin ref-type, og pushet kører hvis det
    # ene af dem rammer (aldrig begge, en ref er aldrig branch og tag).
    if is_tag:
        if tags is None or not _any_match(tags, ref[len("refs/tags/"):]):
            return False
    elif is_branch or base_ref:
        if branches is None or not _any_match(branches, branch_ref):
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
    if not filt:
        # `workflow_dispatch:` uden filtre: enhver kørsel på main er nok for de
        # gates, der bare spørger om en manuel udløser findes.
        return True
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

    for name in ("push", "pull_request"):
        if isinstance(event(wf, name), list):
            problems.append(f"{desktop}: `on.{name}` er en liste, som GitHubs schema "
                            "afviser — kørslen fejler i 0 sekunder uden at køre "
                            "noget job. Skal være en mapping.")

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
    if isinstance(event(wf, "push"), list):
        problems.append(f"{site}: `on.push` er en liste, som GitHubs schema afviser")
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
    problems += check_gate(wf, "repo")
    return problems


# --------------------------------------------------------------------------
# Opgave 12: runtime-versionen skal være erklæret ét sted, ikke skrevet tre
# --------------------------------------------------------------------------
NVMRC = "desktop/.nvmrc"
DESKTOP_MANIFEST = "desktop/package.json"

# `None` er et gyldigt input (filen mangler), så selftesten skal kunne sige
# "læs fra disken" med en anden værdi end "filen mangler".
_UNSET: Any = object()


def _version_tuple(text: str) -> tuple[int, int, int] | None:
    match = re.fullmatch(r"v?(\d+)\.(\d+)\.(\d+)", (text or "").strip())
    if not match:
        return None
    return tuple(int(part) for part in match.groups())  # type: ignore[return-value]


def _engine_floor(range_text: str) -> tuple[int, int, int] | None:
    """Laveste version i en `engines.node`-række, eller None hvis ulæselig.

    Vi læser kun den nedre grænse (`>=`, `^`, `>`). Det er den der dræber en
    bygserver, hvis den vælger en for gammel Node — præcis den fejl der
    ramte jordemoderstudy 23. august, hvor Next.js 16 installerede lokalt og
    først faldt i produktion.
    """
    versions = [v for v in (_version_tuple(m) for m in re.findall(r"\d+\.\d+\.\d+", range_text or ""))
                if v is not None]
    return min(versions) if versions else None


def _read_manifest(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def check_desktop_runtime(wf: dict[str, Any], label: str, *,
                          manifest: Any = _UNSET,
                          nvmrc: Any = _UNSET) -> list[str]:
    """Electron kræver en Node-version. Den skal stå i ÉN fil, og alle tre
    build-jobs skal læse den derfra.

    Uden denne erklæring er der tre steder at vedligeholde (manifest,
    `.nvmrc`, tre `node-version:` i workflowen) og ingen der siger, når de
    er uvede over hinanden. Før denne opgave stod `node-version: '22'` i
    alle tre jobs, `engines` manglede i manifestet, og Electron 44 kræver
    `>=22.12.0` — intet sted sagde det.
    """
    problems: list[str] = []
    desk = f"{label}: desktop-runtime"
    jobs = wf.get("jobs") or {}

    if manifest is _UNSET:
        manifest = _read_manifest(ROOT / DESKTOP_MANIFEST)
    if nvmrc is _UNSET:
        nvmrc_path = ROOT / NVMRC
        nvmrc = nvmrc_path.read_text(encoding="utf-8") if nvmrc_path.is_file() else None

    if manifest is None:
        problems.append(f"{desk}: {DESKTOP_MANIFEST} kan ikke læses, så det er "
                        "umuligt at bevise hvilken Node-version pakken kræver")
        floor = None
    else:
        engines = manifest.get("engines")
        node_range = (engines or {}).get("node") if isinstance(engines, dict) else None
        if not node_range:
            problems.append(f"{desk}: {DESKTOP_MANIFEST} erklærer ikke "
                            "`engines.node`, så en bygserver må gætte sig til en "
                            "runtime — og den fejler først ved build, ikke lokalt")
            floor = None
        else:
            floor = _engine_floor(str(node_range))
            if floor is None:
                problems.append(f"{desk}: `engines.node` er `{node_range}`, som ikke "
                                "kan læses som en nedre grænse")

    pinned = _version_tuple(nvmrc) if nvmrc is not None else None
    if nvmrc is None:
        problems.append(f"{desk}: {NVMRC} mangler, så hverken en lokal maskine "
                        "eller CI ved hvilken Node-version der skal bruges")
    elif pinned is None:
        problems.append(f"{desk}: {NVMRC} er `{nvmrc.strip()}` — skriv en konkret "
                        "`major.minor.patch`, så bygget ikke afhænger af hvilken "
                        "patch der tilfældigvis er nyeste")
    elif floor is not None and pinned < floor:
        problems.append(
            f"{desk}: {NVMRC} er {pinned[0]}.{pinned[1]}.{pinned[2]}, men "
            f"`engines.node` kræver mindst {floor[0]}.{floor[1]}.{floor[2]} — "
            "bygget ville køre på en runtime pakken ikke understøtter")

    # Hvert build-job skal læse den erklærede fil. En hårdkodet `node-version`
    # er en anden liste, og den kan glide fra både `.nvmrc` og `engines`.
    for job in DESKTOP_JOBS:
        spec = jobs.get(job)
        if not isinstance(spec, dict):
            continue
        for step in (spec.get("steps") or []):
            if not isinstance(step, dict) or "setup-node" not in str(step.get("uses") or ""):
                continue
            with_ = step.get("with") if isinstance(step.get("with"), dict) else {}
            version_file = with_.get("node-version-file")
            if version_file:
                if str(version_file) != NVMRC:
                    problems.append(f"{desk}: jobbet `{job}` læser sin Node-version "
                                    f"fra `{version_file}` i stedet for `{NVMRC}`")
                continue
            if with_.get("node-version"):
                problems.append(f"{desk}: jobbet `{job}` skriver sin egen "
                                f"`node-version: {with_['node-version']}` i stedet for "
                                f"at læse `{NVMRC}` — den kan glide fra både "
                                "`engines.node` og de to andre jobs")
            else:
                problems.append(f"{desk}: jobbet `{job}` kalder setup-node uden "
                                "version, så den bruger runnerens forudindstillede "
                                "Node — måske ikke den pakken kræver")

    # En runtime-opdatering skal udløse en ny build, ellers merger den uden
    # at nogen bygger med den.
    if not push(wf, "refs/heads/main", NVMRC):
        problems.append(f"{desk}: path-filteret dækker ikke {NVMRC}, så en push "
                        "der kun retter runtime-versionen ikke bygger nogen af "
                        "`DESKTOP_JOBS`")
    return problems


# --------------------------------------------------------------------------
# Opgave 11: CI skal køre den dokumenterede gate, og kun den
# --------------------------------------------------------------------------
def _run_commands(spec: dict[str, Any]) -> list[str]:
    """Alle kommandoer i et jobs `run:`-blokke, én ad gangen pr. linje."""
    commands: list[str] = []
    for step in (spec.get("steps") or []):
        if not isinstance(step, dict):
            continue
        body = step.get("run")
        if not isinstance(body, str):
            continue
        for line in body.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith(("if ", "for ", "while ", "do ", "done ", "fi", "else",
                                "elif ", "esac", "then")):
                continue
            commands.append(line)
    return commands


def _needs(spec: dict[str, Any]) -> list[str]:
    needs = spec.get("needs")
    return [needs] if isinstance(needs, str) else list(needs or [])


def _step_text(step: dict[str, Any]) -> str:
    """Hele step'ets tekst, uanset hvilken nøgel den ligger i."""
    if not isinstance(step, dict):
        return ""
    parts: list[str] = []
    for key in ("run", "name", "uses"):
        value = step.get(key)
        if isinstance(value, str):
            parts.append(value)
    with_ = step.get("with")
    if isinstance(with_, dict):
        parts += [f"{k}={v}" for k, v in with_.items() if isinstance(v, str)]
    return "\n".join(parts)


def _is_deploy_job(spec: dict[str, Any]) -> bool:
    """Deployer jobbet? Ikke bare et `run:`-step — `pages deploy` står i
    `with.command` på wrangler-action, så en gate der kun læser `run:` ville
    aldrig finde nogen deploy-job og aldrig kræve `needs`."""
    return any("pages deploy" in _step_text(step)
               for step in (spec.get("steps") or []) if isinstance(step, dict))


def _pinned_auditedwp(wf: dict[str, Any]) -> list[str]:
    """Revisions for auditedwp-checkoutet, i rækkefølge forekomst."""
    refs: list[str] = []
    for spec in (wf.get("jobs") or {}).values():
        if not isinstance(spec, dict):
            continue
        for step in (spec.get("steps") or []):
            if not isinstance(step, dict):
                continue
            with_ = step.get("with") or {}
            if isinstance(with_, dict) and with_.get("repository") == "mahope/auditedwp":
                refs.append(str(with_.get("ref") or ""))
    return refs


@lru_cache(maxsize=1)
def _repo_files() -> tuple[str, ...]:
    """Alle sporbare filer i repoet, til at udvide glob-input mod."""
    found: list[str] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in WALK_SKIP for part in path.relative_to(ROOT).parts):
            continue
        found.append(path.relative_to(ROOT).as_posix())
    return tuple(sorted(found))


def _expand(pattern: str) -> list[str]:
    """Glob → de rigtige filer den dækker (tom hvis mønsteret er en fil)."""
    if not any(ch in pattern for ch in "*?["):
        return [pattern]
    regex = _pattern_regex(pattern)
    return [f for f in _repo_files() if regex.match(f)]


def _uncovered(step_id: str, pattern: str, filters: list[str]) -> list[str]:
    """Filer i `pattern` som path-filteret ikke dækker."""
    covered = lambda f: any(_pattern_regex(p).match(f) for p in filters)  # noqa: E731
    expanded = _expand(pattern)
    if not expanded:
        # Mønsteret peger på filer der ikke findes (ny kilde, ikke endnu
        # committet). Så må mønsteret selv matche, ellers er det uopklaret.
        return [] if covered(pattern) else [pattern]
    return [f for f in expanded if not covered(f)]


def check_gate(wf: dict[str, Any], label: str) -> list[str]:
    """Deploy-workflowen skal køre `quality_gate.py` og intet andet."""
    problems: list[str] = []
    site = f"{label}: deploy-sites.yml"
    jobs = wf.get("jobs") or {}
    push_paths = (event(wf, "push") or {}).get("paths")
    filters = [str(p) for p in (push_paths or []) if not str(p).startswith("!")]

    # 1. Der skal være præcis ét job, der kører gaten.
    gate_jobs: list[str] = []
    for job, spec in jobs.items():
        if not isinstance(spec, dict):
            continue
        if any(cmd == GATE_COMMAND for cmd in _run_commands(spec)):
            gate_jobs.append(job)
    if not gate_jobs:
        problems.append(f"{site}: intet job kører `{GATE_COMMAND}`, så den "
                        "dokumenterede kvalitetsgate kører aldrig i CI")
    elif len(gate_jobs) > 1:
        problems.append(f"{site}: {len(gate_jobs)} jobs kører gaten "
                        f"({', '.join(sorted(gate_jobs))}) — en fejl ville give "
                        "to uafhængige sandheder om porten")

    # 2. Hvert deploy-job skal afhænge af gate-jobbet, så en fælles gatefejl
    #    dræber alle domæner i stedet for at sende dem videre hver for sig.
    for job, spec in jobs.items():
        if not isinstance(spec, dict) or not _is_deploy_job(spec):
            continue
        if gate_jobs and not set(gate_jobs) & set(_needs(spec)):
            problems.append(
                f"{site}: deploy-jobbet `{job}` har ikke `needs: "
                f"{gate_jobs[0]}`, så en fælles gatefejl ville stadig deploye "
                "dette domæne")

    # 3. Ingen gatestræk må være skrevet ud i en `run:`-blok. Det er hele
    #    pointen med én ejer: to lister kan ikke bevise at de er ens.
    for job, spec in jobs.items():
        if not isinstance(spec, dict):
            continue
        for cmd in _run_commands(spec):
            for step in GATE_STEPS:
                if cmd == step.command and not (job in gate_jobs and cmd == GATE_COMMAND):
                    problems.append(
                        f"{site}: `{cmd}` står som sin egen kommando i jobbet "
                        f"`{job}` — kør gaten gennem `{GATE_COMMAND}`, ellers "
                        "kan de to lister glide fra hinanden")

    # 4. Path-filteret skal dække alt, hvad gaten læser.
    for step in GATE_STEPS:
        for pattern in step.inputs:
            missing = _uncovered(step.id, pattern, filters)
            if missing:
                shown = ", ".join(missing[:3]) + (" …" if len(missing) > 3 else "")
                problems.append(
                    f"{site}: path-filteret dækker ikke {shown}, som gatestrækket "
                    f"`{step.id}` ({step.command}) læser — en push der kun rører "
                    "den fil springer gaten over")

    # 5. `auditedwp` skal være pinnet, og ens i alle jobs.
    refs = _pinned_auditedwp(wf)
    if not refs:
        problems.append(f"{site}: intet job checkouter auditedwp, men "
                        "build_sites.py henter værktøjssider derfra")
    for ref in refs:
        if not re.fullmatch(r"[0-9a-f]{40}", ref):
            problems.append(f"{site}: auditedwp er checkoutet på `{ref}`, som "
                            "ikke er en 40-tegns SHA — et flyt tag eller en "
                            "branch kan ændre det under buildet")
    if len(set(refs)) > 1:
        problems.append(f"{site}: auditedwp er checkoutet på forskellige "
                        f"revisioner ({', '.join(sorted(set(refs)))}) — de tre "
                        "domæner ville bygge fra forskellige kilder")

    # 6. Et job uden matrix må ikke bruge matrix-udtryk. Før denne opgave stod
    #    `check_links.py --only "${{ matrix.domain }}"` i gate-jobbet, som ikke
    #    har nogen matrix — variablen var tom, og porten dækkede intet.
    for job, spec in jobs.items():
        if not isinstance(spec, dict):
            continue
        matrix = (spec.get("strategy") or {}).get("matrix")
        if matrix:
            continue
        for step in (spec.get("steps") or []):
            if not isinstance(step, dict):
                continue
            for key in ("run", "name", "with"):
                value = step.get(key)
                text = value if isinstance(value, str) else repr(value)
                if "matrix." in text:
                    problems.append(f"{site}: jobbet `{job}` bruger "
                                    "`${{ matrix.* }}` uden at have en matrix — "
                                    "variablen er tom, så kommandoen kører "
                                    "ufuldstændig i stedet for at fejle")
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
    tag_only["on"]["push"] = {
        k: v for k, v in tag_only["on"]["push"].items() if k != "branches"
    }
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
    no_tags["on"]["push"].pop("tags", None)
    problems = check_desktop(no_tags, "uden tag-filter")
    ok &= _expect(problems, "udløser ikke build-jobbene, så en ny udgivelse",
                 "uden-tags", any("udgivelse" in p for p in problems))

    # 3. Path-filteret forsvundet: matrixen kører på ethvert push.
    no_paths = copy.deepcopy(real["desktop"])
    no_paths["on"]["push"].pop("paths", None)
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

    # 6. Listeform for `on.push` — den fejlmulighed der lå bag kørsel
    #    36180365427: workflowen startede, men alle jobs faldt i 0 sekunder.
    list_form = copy.deepcopy(real["desktop"])
    list_form["on"]["push"] = [
        {"branches": ["main"], "paths": list_form["on"]["push"]["paths"]},
        {"tags": list_form["on"]["push"]["tags"]},
    ]
    problems = check_desktop(list_form, "listeform")
    ok &= _expect(problems, "er en liste", "listeform",
                  any("er en liste" in p for p in problems))

    # 7. Deploy-workflowen taber et buildinput.
    thin_deploy = copy.deepcopy(real["deploy"])
    thin_deploy["on"]["push"]["paths"] = [
        p for p in thin_deploy["on"]["push"]["paths"] if p != "tools/seo_check.py"
    ]
    problems = check_deploy(thin_deploy, "tyndt filter")
    ok &= _expect(problems, "tools/seo_check.py", "tyndt-filter",
                  any("tools/seo_check.py" in p for p in problems))

    # 8. Nyt fra opgave 11: gaten fjernet fra CI. Det var den virkelige
    #    fejlform — dokumenteret i planen, kørt tre steder i en kortere
    #    form, aldrig som hele gaten.
    no_gate = copy.deepcopy(real["deploy"])
    for spec in no_gate["jobs"].values():
        for step in spec.get("steps", []):
            if isinstance(step, dict) and isinstance(step.get("run"), str):
                step["run"] = step["run"].replace(GATE_COMMAND, "true")
    problems = check_gate(no_gate, "gaten væk")
    ok &= _expect(problems, "kvalitetsgate kører aldrig i CI", "gaten-væk",
                  any("kører aldrig i CI" in p for p in problems))

    # 9. Deploy-jobbet kan køre uden gaten, fordi `needs` mangler.
    no_needs = copy.deepcopy(real["deploy"])
    no_needs["jobs"]["deploy"].pop("needs", None)
    problems = check_gate(no_needs, "deploy uden gate")
    ok &= _expect(problems, "har ikke `needs:", "deploy-uden-gate",
                  any("har ikke `needs:" in p for p in problems))

    # 10. En afgrenset gateliste ved siden af quality_gate.py. Den fejlform
    #     gjorde tre af dokumenterede checks aldrig køre i CI, og ingen
    #     kunne se den, fordi planen sagde at de kørte.
    partial = copy.deepcopy(real["deploy"])
    partial["jobs"]["deploy"]["steps"].insert(0, {
        "name": "Delvis gate",
        "run": "node tests/stripe-worker.test.mjs\n"
               "python3 tools/check_product_copy.py",
    })
    problems = check_gate(partial, "dobbeltliste")
    ok &= _expect(problems, "python3 tools/check_product_copy.py", "dobbeltliste",
                  any("check_product_copy.py" in p and "kør gaten gennem" in p
                      for p in problems))
    if not any("stripe-worker.test.mjs" in p for p in problems):
        print("FEJL: selftesten `dobbeltliste` forventede, at også et "
              "stripe-worker-step uden for quality_gate.py meldes", file=sys.stderr)
        ok = False

    # 11. Et gatestræks fil mangler i path-filteret. `docs/stripe-kontrakt.md`
    #     lå netop sådan: `check_stripe_ctas.py` læser den, og den stod ikke
    #     i filteret, så en prisændring kunne deploye uopdaget.
    no_docs = copy.deepcopy(real["deploy"])
    no_docs["on"]["push"]["paths"] = [
        p for p in no_docs["on"]["push"]["paths"]
        if not str(p).startswith("docs/")
    ]
    problems = check_gate(no_docs, "uden docs")
    ok &= _expect(problems, "docs/stripe-kontrakt.md", "uden-docs",
                  any("docs/stripe-kontrakt.md" in p for p in problems))

    # 12. Glob-input testes mod de rigtige filer. `products/**` lå i filteret,
    #     men ikke de enkelte filer, så det er filerne der skal afgøre det —
    #     ellers ville porten være en ny håndskrevet filiste.
    thin_products = copy.deepcopy(real["deploy"])
    thin_products["on"]["push"]["paths"] = [
        p for p in thin_products["on"]["push"]["paths"] if p != "products/**"
    ]
    problems = check_gate(thin_products, "uden products")
    ok &= _expect(problems, "products/", "uden-products",
                  any("products/" in p for p in problems))

    # 13. `auditedwp` på et flyt tag i stedet for en SHA.
    floating = copy.deepcopy(real["deploy"])
    for spec in floating["jobs"].values():
        for step in spec.get("steps", []):
            with_ = step.get("with") if isinstance(step, dict) else None
            if isinstance(with_, dict) and with_.get("repository") == "mahope/auditedwp":
                with_["ref"] = "main"
    problems = check_gate(floating, "flydende ref")
    ok &= _expect(problems, "40-tegns SHA", "flydende-ref",
                  any("40-tegns SHA" in p for p in problems))

    # 14. De to jobs checkouter auditedwp på hver sin revision: tre domæner
    #     ville bygge fra forskellige kilder, og ingen placeholder ville sige det.
    drifted = copy.deepcopy(real["deploy"])
    seen_refs = 0
    for spec in drifted["jobs"].values():
        for step in spec.get("steps", []):
            with_ = step.get("with") if isinstance(step, dict) else None
            if isinstance(with_, dict) and with_.get("repository") == "mahope/auditedwp":
                seen_refs += 1
                with_["ref"] = f"{seen_refs:0>40}"[:39] + str(seen_refs)
    problems = check_gate(drifted, "divergerende ref")
    ok &= _expect(problems, "forskellige revisioner", "divergerende-ref",
                  any("forskellige revisioner" in p for p in problems))

    # 15. Matrix-udtryk i et job uden matrix. Det stod i gate-jobbet før denne
    #     opgave: `check_links.py --only "${{ matrix.domain }}"` med tom
    #     variabel, så porten dækkede intet uden at sige det.
    ghost_matrix = copy.deepcopy(real["deploy"])
    gate_steps = ghost_matrix["jobs"]["gate"]["steps"]
    for step in gate_steps:
        if isinstance(step, dict) and isinstance(step.get("run"), str):
            step["run"] = (step["run"] + "\n"
                           "python3 tools/check_links.py --only "
                           '"${{ matrix.domain }}"')
    problems = check_gate(ghost_matrix, "spøgelses-matrix")
    ok &= _expect(problems, "uden at have en matrix", "spoegelses-matrix",
                  any("uden at have en matrix" in p for p in problems))

    # 16. Opgave 12: runtime. De fire mutationer er de fire fejlformer, de
    #     to erklæringer kan have imellem sig. Positiv kontrol først: de
    #     rigtige filer skal være grønne, ellers beviser mutationerne intet.
    real_runtime = check_desktop_runtime(real["desktop"], "rigtige filer")
    if real_runtime:
        print(f"FEJL: de rigtige runtime-filer har fejl: {real_runtime}", file=sys.stderr)
        ok = False

    # 16a. `engines.node` væk — det var tilstanden før denne opgave.
    no_engines = _read_manifest(ROOT / DESKTOP_MANIFEST) or {}
    no_engines = {k: v for k, v in no_engines.items() if k != "engines"}
    problems = check_desktop_runtime(real["desktop"], "uden engines",
                                     manifest=no_engines, nvmrc="22.23.2")
    ok &= _expect(problems, "erklærer ikke `engines.node`", "uden-engines",
                  any("engines.node" in p for p in problems))

    # 16b. `.nvmrc` på en Node, pakken ikke understøtter. Uden denne fejl
    #      bygger alle tre jobs grønt på den forkerte runtime.
    problems = check_desktop_runtime(real["desktop"], "gammel nvmrc", nvmrc="18.20.0")
    ok &= _expect(problems, "men `engines.node` kræver mindst", "gammel-nvmrc",
                  any("kræver mindst" in p for p in problems))

    # 16c. `.nvmrc` uden patch-version: '22' løser sig til en nyeste patch
    #      hver gang, så bygget er ikke reproducerbart.
    problems = check_desktop_runtime(real["desktop"], "flydende nvmrc", nvmrc="22")
    ok &= _expect(problems, "skriv en konkret", "flydende-nvmrc",
                  any("major.minor.patch" in p for p in problems))

    # 16d. Et job der skriver sin egen version — den anden liste, præcis
    #      som den `node-version: '22'` der stod i alle tre jobs.
    inline_version = copy.deepcopy(real["desktop"])
    for step in inline_version["jobs"]["build-linux"]["steps"]:
        if isinstance(step, dict) and "setup-node" in str(step.get("uses") or ""):
            step["with"] = {"node-version": "22"}
    problems = check_desktop_runtime(inline_version, "inline version")
    ok &= _expect(problems, "skriver sin egen `node-version", "inline-version",
                  any("skriver sin egen" in p for p in problems))

    # 16e. Runtime-filen er ikke i path-filteret, så en runtime-bump merger
    #      uden at nogen bygger med den.
    filtered = copy.deepcopy(real["desktop"])
    filtered["on"]["push"]["paths"] = [
        p for p in filtered["on"]["push"]["paths"]
        if not _any_match([str(p)], NVMRC) or str(p) == ".github/workflows/build-desktop.yml"
    ]
    if push(filtered, "refs/heads/main", NVMRC):
        print("FEJL: mutationen `uden-nvmrc` er ikke en mutation — path-filteret "
              f"dækker stadig {NVMRC}", file=sys.stderr)
        ok = False
    else:
        problems = check_desktop_runtime(filtered, "uden nvmrc-filter")
        ok &= _expect(problems, "path-filteret dækker ikke", "uden-nvmrc-filter",
                      any("path-filteret dækker ikke" in p for p in problems))

    # 16f. `.nvmrc` væk fra repoet: setup-node ville finde en fil, der ikke
    #      findes, og alle tre jobs ville døje med en kryptisk fejl.
    problems = check_desktop_runtime(real["desktop"], "nvmrc væk", nvmrc=None)
    ok &= _expect(problems, "mangler, så hverken en lokal maskine", "nvmrc-væk",
                  any("mangler" in p for p in problems))

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
        problems += check_desktop_runtime(workflows["desktop"], "repo")
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
        if name == "desktop":
            problems += check_desktop_runtime(wf, name)

    for problem in problems:
        print(f"FEJL: {problem}", file=sys.stderr)
    if problems:
        return 1
    print(f"deploy-workflows OK — {len(WORKFLOWS)} workflows, "
          "build-desktop udløser på main+paths og på tag, deploy kun på main+site/**")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
