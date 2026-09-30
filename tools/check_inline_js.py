#!/usr/bin/env python3
"""JS-syntax-tjek af inline <script>-blokke (uden src=) i site/ **og dist/**.

**Hvorfor dist er med, selv om denne port startede med kun at læse `site/`.**
30/9 lå otte generatorer på mahope.tools — `/dpa-generator`, `/ropa-generator`,
deres DA-varianter, `/privacy-notice-generator` og
`/accessibility-statement-generator` — med en død inline-script-blok i *live*.
`python3 tools/check_inline_js.py` sagde «problems: 0», fordi porten læste
kilden. Kilden var i orden; **bygget** brød den:

1. `build_sites.insert_before_end_tag` skrev shell- og BugBottle-tags ind foran
   det *første* `</body>`. Generatorerne bygger den fil de downloader som en
   JS-streng, så `</body>` står midt i et `<script>`. Browseren stoppede
   scriptet der, og hele værktøjet var dødt: en kunde på `/dpa-generator`
   trykkede «Generate agreement» og fik et tomt felt. DPA'en er et $59-produkt.
2. `pagepass.normalize_body` kørte `scrub_css` overalt i dokumentet og skrev
   sit eget linjeskift ind i den streng, der måtte være én linje.

Begge fejl var usynlige for en port der læser kilden, fordi de opstår *under*
buildet. Derfor dommes her begge træer, og derfor er der en måling af hvor
meget der faktisk er dømt.

Brug:
    python3 tools/check_inline_js.py
    python3 tools/check_inline_js.py --self-test
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
DIST = ROOT / "dist"

# Ét `node` pr. tråd. Hårdt kodet i stedet for `os.cpu_count()`: en GitHub-
# runner har to vCPU'er, og `node --check` på en blok er kort nok til at
# process-starten dominerer. 8 holder farten uden at sprænge en lille runner.
WORKERS = 8

SCRIPT_RE = re.compile(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", re.S | re.I)
LD_JSON_RE = re.compile(r"application/ld\+json", re.I)
IMPORTMAP_RE = re.compile(r'<script[^>]*type=["\']importmap["\']', re.I)


def blocks_of(html: str) -> list[str]:
    """Alle inline-script-blokke i en side, minus dem der ikke er JavaScript."""
    out = []
    for m in SCRIPT_RE.finditer(html):
        body = m.group(1)
        if not body.strip():
            continue
        # JSON-LD er data, ikke kode; importmap er deklarativt
        if LD_JSON_RE.search(html[m.start():m.start() + 120]):
            continue
        if IMPORTMAP_RE.search(html[max(0, m.start() - 60):m.start() + 80]):
            continue
        # templates
        if "<%" in body or "{{" in body:
            continue
        out.append(body)
    return out


def check_text(text: str, label: str) -> list[str]:
    """En fejl pr. blok der ikke kan parses. Ét node-kald for hele siden."""
    blocks = blocks_of(text)
    if not blocks:
        return []
    with tempfile.TemporaryDirectory() as tmp:
        problems = []
        for i, block in enumerate(blocks, 1):
            path = Path(tmp) / f"block{i}.js"
            path.write_text(block, encoding="utf-8")
            r = subprocess.run(["node", "--check", str(path)],
                               capture_output=True, text=True)
            if r.returncode != 0:
                first = [l for l in r.stderr.strip().splitlines()
                         if "SyntaxError" in l or "Error:" in l]
                problems.append(f"{label} blok {i}: {(first[0] if first else 'syntax error')[:110]}")
        return problems


def check_tree(root: Path) -> tuple[list[str], int, int]:
    """Alle sider i `root`, hver side med `node --check` pr. blok, i parallel.

    Trådene er ikke pynt: hver blok er ét `node`-kalder, og de to træer har
    1950 blokke i alt. Målt 30/9 før parallellen: 4 min 20 sekund for én
    gennemgang, og selvtesten bygger tre gange — altså over en halv time i
    gaten, der kører fire gange i døgnet. `subprocess` slipper GIL'en, så
    trådene giver reel hastighed her. Målt efter: se STATE.
    """
    if not root.is_dir():
        return [], 0, 0
    pending: list[tuple[Path, str]] = []
    files = blocks = 0
    for f in sorted(root.rglob("*.html")):
        html = f.read_text(encoding="utf-8", errors="ignore")
        n = len(blocks_of(html))
        if not n:
            continue
        files += 1
        blocks += n
        # Relativt til *roden af den mappe vi læser*, så et klone-repo under
        # /tmp ikke fejler med "not in the subpath of".
        rel = f.relative_to(root) if str(f).startswith(str(root)) else f.name
        pending.append((f, str(rel)))
    problems: list[str] = []
    if pending:
        with cf.ThreadPoolExecutor(max_workers=WORKERS) as pool:
            for found in pool.map(_check_one, pending):
                problems += found
    return problems, files, blocks


def _check_one(job: tuple[Path, str]) -> list[str]:
    f, rel = job
    return check_text(f.read_text(encoding="utf-8", errors="ignore"), rel)


def check() -> list[str]:
    problems, src_files, src_blocks = check_tree(SITE)
    dist_problems, dist_files, dist_blocks = check_tree(DIST)
    print(f"site/: {src_files} filer, {src_blocks} inline-blok(er)")
    print(f"dist/: {dist_files} filer, {dist_blocks} inline-blok(er)")
    if not dist_files:
        print("dist/ mangler — kør `python3 build_sites.py` først; porten ville "
              "være halvt blind uden den.")
        return ["dist/ findes ikke"]
    return problems + dist_problems


# --------------------------------------------------------------------------
# Selvtest: genskab de to mutationer der gjorde otte sider døde i live, og
# se at porten er rød på dem.
#
# De to fejlformer opstår fordi bygget skriver ind i en JS-streng. En side er
# ramt hvis dens `<script>`-blok indeholder `</body>` eller `<style>` som en
# *streng* — altså efterfulgt af `</html>`, `<body>` eller et CSS-tegn, så en
# almindelig markup-`</body>` ikke tæller med. Finderne læser kilden, så en ny
# generator med samme mønster dømmes uden at porten skal redigeres.
# --------------------------------------------------------------------------

CSS_TAIL = re.compile(r"</style>|<body\b|\{|\}")
BODY_TAIL = re.compile(r"</body>|</html>")


def _script_bodies(path: Path) -> list[str]:
    html = path.read_text(encoding="utf-8", errors="ignore")
    return [m.group(1) for m in SCRIPT_RE.finditer(html)
            if m.group(1).strip() and not LD_JSON_RE.search(html[m.start():m.start() + 120])]


def _has_body_string(path: Path) -> bool:
    """Sider hvor bygget skriver før det første `</body>` — altså dør."""
    return any(BODY_TAIL.search(b) for b in _script_bodies(path))


def _has_style_string(path: Path) -> bool:
    """Sider hvor `scrub_css` skriver sit eget linjeskift ind i en streng."""
    return any("<style" in b and CSS_TAIL.search(b) for b in _script_bodies(path))


def _clone(tmp: str) -> Path:
    """En kopi af repoet, der kan bygges.

    Kun `site/`, `tools/`, `tests/` og de to bygfiler kopieres — resten er
    rødt arbejde. `AUDITEDWP_DIR` skal *respekteres* og ikke overskrives: CI
    tjekker auditedwp ud som `github.workspace/auditedwp-src`, så et hårdkodet
    `../auditedwp` ville pege på en mappe der ikke findes, og selvtesten ville
    dø med «route inventory mismatch» — altså rød af portens egen opsætning.

    Vi sletter ingen sider. Ruteinventaret i `build_sites` holder navne på alle
    domænets ruter, så en klon med færre HTML-filer dør med samme fejl.
    Mutationen rammer kun de sider der *har* mønsteret, så hele `site/` kan
    blive ligesom.
    """
    import shutil
    work = Path(tmp) / "repo"
    work.mkdir()
    for item in ("site", "tools", "tests"):
        shutil.copytree(ROOT / item, work / item,
                        ignore=shutil.ignore_patterns("__pycache__"))
    for item in ("build_sites.py", "bugbottle-landing"):
        src = ROOT / item
        if src.is_dir():
            shutil.copytree(src, work / item)
        else:
            shutil.copy2(src, work / item)
    return work


def build_env() -> dict:
    env = dict(os.environ)
    auditedwp = Path(env.get("AUDITEDWP_DIR") or (ROOT.parent / "auditedwp"))
    if not (auditedwp / "site" / "deskuptime").is_dir():
        raise AssertionError(
            f"auditedwp's værktøjssider mangler i {auditedwp} — sæt "
            f"AUDITEDWP_DIR til auditedwp-checkouten (CI bruger "
            f"github.workspace/auditedwp-src)")
    env["AUDITEDWP_DIR"] = str(auditedwp)
    return env


def self_test() -> int:
    """Bevis at porten er rød på de to fejlformer, der var i live."""
    import shutil
    import tempfile as tf
    failures = 0

    def report(ok: bool, label: str, detail: str = "") -> None:
        nonlocal failures
        print(f"{'ok  ' if ok else 'FAIL'} {label}{': ' + detail if detail else ''}")
        failures += 0 if ok else 1

    def build_and_check(work: Path, label: str) -> tuple[list[str], list[str]]:
        r = subprocess.run([sys.executable, "build_sites.py"], cwd=work,
                           env=build_env(), capture_output=True, text=True, timeout=900)
        if r.returncode != 0:
            report(False, label,
                   (r.stderr.strip().splitlines() or ["?"])[-1][:110])
            return [], []
        src_p, _, _ = check_tree(work / "site")
        dist_p, _, _ = check_tree(work / "dist")
        return src_p, dist_p

    # De otte sider hvis `<body>`-streng gjorde bygget dødt, og de fire hvis
    # `<style>`-streng gjorde `scrub_css` dødt. Navnene er læst fra de filer
    # der faktisk har fejlen i kilden — ikke hardkodet som et navnesæt.
    body_pages = sorted(p.name for p in (ROOT / "site").rglob("*.html")
                        if _has_body_string(p))
    style_pages = sorted(p.name for p in (ROOT / "site").rglob("*.html")
                         if _has_style_string(p))

    # 1. Kilden i sig selv er ren — det er den gamle ports blinde plet.
    src_problems, _, _ = check_tree(SITE)
    report(not src_problems, "baseline: site/ er rent",
           f"{len(src_problems)} problem(er)" if src_problems else "")
    report(bool(body_pages) and bool(style_pages),
           f"de otte + fire sider med fejlen findes i kilden",
           f"{len(body_pages)} med </body>, {len(style_pages)} med <style>")

    # 2. Fejlform 1: bygget skriver igen foran det FØRSTE </body>.
    with tf.TemporaryDirectory(prefix="inline-js-selftest-") as tmp:
        work = _clone(tmp)
        src = (work / "build_sites.py").read_text(encoding="utf-8")
        anchor = 'text = insert_before_end_tag(text, "body", tags + "\\n")'
        if anchor not in src:
            report(False, "mutation 1: ankeret findes i build_sites.py")
        else:
            (work / "build_sites.py").write_text(src.replace(
                anchor,
                'text = BODY_END_RE.sub(lambda m: tags + "\\n</body>", text, count=1)'),
                encoding="utf-8")
            src_p, dist_p = build_and_check(work, "mutation 1: det gamle build kører")
            names = {p.split()[0] for p in dist_p}
            report(not src_p,
                   "mutation 1: site/ er stadig rent — den gamle ports blinde plet",
                   f"{len(src_p)} fund")
            report(len(names) == len(body_pages),
                   f"mutation 1: alle {len(body_pages)} sider døde i dist",
                   f"{len(names)} sider: {sorted(names)[:2]}")

    # 3. Fejlform 2: `scrub_css` kører igen overalt i stedet for uden om scripts.
    with tf.TemporaryDirectory(prefix="inline-js-selftest-") as tmp:
        work = _clone(tmp)
        src = (work / "tools" / "pagepass.py").read_text(encoding="utf-8")
        anchor = "text = _skip_scripts(text, lambda part: STYLE_BLOCK_RE.sub(style_sub, part))"
        if anchor not in src:
            report(False, "mutation 2: ankeret findes i pagepass.py")
        else:
            (work / "tools" / "pagepass.py").write_text(
                src.replace(anchor, "text = STYLE_BLOCK_RE.sub(style_sub, text)"),
                encoding="utf-8")
            _src_p, dist_p = build_and_check(work, "mutation 2: det gamle build kører")
            names = {p.split()[0] for p in dist_p}
            report(len(names) == len(style_pages),
                   f"mutation 2: alle {len(style_pages)} sider døde i dist",
                   f"{len(names)} sider")

    print("selvtest: " + ("grøn" if failures == 0 else f"{failures} fejl"))
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description="JS-syntax i site/ og dist/")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return 1 if self_test() else 0
    problems = check()
    print("problems:", len(problems))
    for problem in problems:
        print(f"  {problem}")
    if not problems and not args.quiet:
        print("GRØN: ingen inline-script-blok i site/ eller dist/ er brudt")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())