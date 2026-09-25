#!/usr/bin/env python3
"""Generér de to låste Python-kravfiler fra PyPI.

Opgave 13 (25. september 2026): site-, ebook-, bundle-, cover- og
screenshotværktøjerne i repoet brugte tredjepartspakker uden samlet lock, så
hvad der rent faktisk blev installeret afhangede af, hvornår sidst nogen kørte
`pip install`. Site Icons' `pyproject.toml` kunne desuden ikke bygges, fordi
metadata lå under `[tool]` i stedet for `[project]`.

Denne fil er den *eneste* sted, der bestemmer hvilke versioner der låses, og
den lister **kun topniveauet**. Alt transitivt bliver løst af pip, så et
transitivt krav der ændrer sig ikke kan få låsen til at ligge om de
tredjepartspakker, der faktisk skal bruges. `requirements-build.txt` og
`requirements-audit.txt` er den afledte, hash-tjekkede fil, og
`tools/check_python_env.py` er porten der beviser at de to er enige.

    python3 tools/lock_python_env.py             # skriv begge filer
    python3 tools/lock_python_env.py --check     # afvis at skrive, hvis de er ældre

Hashene hentes fra PyPIs egen JSON-API for **alle** filer i den låste version,
ikke kun for den arkitektur denne maskine tilfældigvis kører på. Det er det, der
gør lockfilen brugbar på både macOS-arm64, macOS-x64 og Linux uden at en
buildserver kan lande på en udgave ingen har hashes til. Det gør den også stor
— det er prisen for at den må bruges andre steder.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

PYPI = "https://pypi.org/pypi/{name}/{version}/json"

#: `pip >= 22.2` for `--report` og `>= 22.2` for `--dry-run --report` at virke
#: stabilt. Systemets Python 3.9 på denne maskine har pip 21.2.4, som ikke har
#: nogen af delene — derfor fejler værktøjet tydeligt i stedet for at gætte.
MIN_PIP = (22, 2)

#: Det byggeværktøj repoet faktisk bruger:
#:  - `build` + `setuptools` + `wheel` bygger Site Icons' sdist og hjul,
#:  - `Pillow` rasteriserer (covers, ikoner, site-icons),
#:  - `playwright` tager screenshots og layoutmåler,
#:  - `reportlab` bygger den kombinerede e-bog-PDF,
#:  - `Markdown` gør ebook- og bundlesskripternes `.md` til HTML,
#:  - `fpdf2` bygger den enkelte PDF-bundle (`import fpdf`).
#:
#: `build_sites.py` — det build der *deployer* — bruger udelukkende stdlib, og
#: derfor installerer CI ingen af disse. Det er med vilje: deploy-stien skal ikke
#: kunne fejle på en pip-download. Locken låser de værktøjer, der skal gengive
#: produkterne lokalt. Hold denne liste tom hvis et værktøj ikke længere findes;
#: `check_python_env.py` fejler, hvis en fil der bruger en tredjepartspakke
#: uden at pakken står her.
BUILD_TOP_LEVEL: tuple[str, ...] = (
    "build",
    "fpdf2",
    "Markdown",
    "Pillow",
    "playwright",
    "reportlab",
    "setuptools",
    "wheel",
)

#: Auditværktøjet ligger i sin egen fil, så kravgaten installerer kun det den
#: skal bruge, og `pip-audit -r` får et rent build-kravsæt at se på. Det er
#: samme opdeling som npm: pakken der kontrollerer afhængighederne er ikke selv
#: en del af det den kontrollerer.
AUDIT_TOP_LEVEL: tuple[str, ...] = ("pip-audit",)

# Kun distributionsformer pip rent kan installere. `.asc`-signaturer og
# `.metadata`-sidecars hører ikke til.
INSTALLABLE = (".whl", ".tar.gz", ".zip")

HEADER = """\
# {title}
#
# Genereret af tools/lock_python_env.py — redigér ikke i hånden.
# Regenerér med:  python3 tools/lock_python_env.py
# Installér med:  python3 -m pip install --require-hashes -r {filename}
#
# Kun topniveau ({top_level}) er valgt her i repoet; alt andet er løst af pip og
# skrevet ud med sin version, så en ny transitiv afhængighed ikke kan skjule sig.
#
# Hashene dækker alle distributionsformer PyPI har for den låste version, så
# filen kan bruges på flere platforme. tools/check_python_env.py fejler hvis en
# pin mangler hashes, hvis en pin ikke er `==`-låst, eller hvis et byggeværktøj
# importerer en tredjepartspakke der ikke står her.
#
# Versionsvalget er lavet af den Python-interpreter der genererede filen. En pin
# der kræver en nyere Python end den kan derfor mangle; `--require-hashes`
# installationen siger det i så fald, i stedet for at installere noget uventet.
#
# Hvor denne fil IKKE bruges: deploy-CI'en installerer intet, fordi
# build_sites.py kun bruger stdlib. Se IMPLEMENTATION_PLAN.md opgave 13.
"""


def canonical(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def pip_version() -> tuple[int, ...]:
    out = subprocess.run(
        [sys.executable, "-m", "pip", "--version"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    match = re.search(r"pip (\d+)\.(\d+)", out)
    if not match:
        raise SystemExit("lock_python_env: kunne ikke læse pip-versionen")
    return (int(match.group(1)), int(match.group(2)))


def resolve(specs: tuple[str, ...]) -> list[tuple[str, str]]:
    """Løs et kravsæt med pip uden at installere noget."""
    result = subprocess.run(
        [
            sys.executable, "-m", "pip", "install",
            "--dry-run", "--ignore-installed", "--quiet",
            "--report", "-", *specs,
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise SystemExit(
            f"lock_python_env: pip kunne ikke løse {', '.join(specs)}:\n{result.stderr.strip()}"
        )
    start = result.stdout.find("{")
    if start < 0:
        raise SystemExit("lock_python_env: pip gav ingen rapport at læse")
    report = json.loads(result.stdout[start:])
    pins = {
        canonical(item["metadata"]["name"]): item["metadata"]["version"]
        for item in report.get("install", [])
    }
    return sorted(pins.items())


def fetch_hashes(name: str, version: str) -> list[str]:
    """Alle sha256 for den låste versions distributionsfiler."""
    try:
        with urllib.request.urlopen(PYPI.format(name=name, version=version), timeout=30) as resp:
            payload = json.load(resp)
    except Exception as exc:  # noqa: BLE001 — vil hellere dø end gætte
        raise SystemExit(f"lock_python_env: kunne ikke hente {name}=={version}: {exc}")

    digests = {
        entry["digests"]["sha256"]
        for entry in payload.get("urls", [])
        if entry.get("packagetype") in ("bdist_wheel", "sdist")
        and entry["filename"].endswith(INSTALLABLE)
        and entry.get("digests", {}).get("sha256")
    }
    if not digests:
        raise SystemExit(
            f"lock_python_env: {name}=={version} har ingen installérbare filer "
            f"med sha256 — ville skrive en lock uden hashes"
        )
    return sorted(digests)


def render(filename: str, title: str, top_level: tuple[str, ...],
           pins: list[tuple[str, str]]) -> str:
    lines = [
        HEADER.format(
            title=title,
            filename=filename,
            top_level=", ".join(top_level),
        )
    ]
    for name, version in pins:
        lines.append(f"{name}=={version} \\")
        hashes = fetch_hashes(name, version)
        for index, digest in enumerate(hashes):
            cont = " \\" if index < len(hashes) - 1 else ""
            lines.append(f"    --hash=sha256:{digest}{cont}")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--check",
        action="store_true",
        help="regenerér i hukommelsen og afvis at skrive hvis en fil ville ændre sig",
    )
    args = parser.parse_args(argv)

    version = pip_version()
    if version < MIN_PIP:
        raise SystemExit(
            f"lock_python_env: kræver pip >= {MIN_PIP[0]}.{MIN_PIP[1]} "
            f"for `--report`, har {version[0]}.{version[1]}. Kør i en venv: "
            f"`python3 -m venv /tmp/lockenv && /tmp/lockenv/bin/pip install -U pip`"
        )

    targets = (
        (ROOT / "requirements-build.txt", "Byggeværktøjer — låst, hash-tjekket.", BUILD_TOP_LEVEL),
        (ROOT / "requirements-audit.txt", "Auditværktøjet (pip-audit) — låst, hash-tjekket.", AUDIT_TOP_LEVEL),
    )

    changed = []
    for path, title, top_level in targets:
        content = render(path.name, title, top_level, resolve(top_level))
        if path.is_file() and path.read_text(encoding="utf-8") == content:
            print(f"lock_python_env: {path.name} er opdateret")
            continue
        changed.append(path.name)
        if args.check:
            continue
        path.write_text(content, encoding="utf-8")
        pins = content.count("==")
        print(f"lock_python_env: skrev {path.name} ({pins} pins)")

    if args.check and changed:
        print(
            "lock_python_env: disse filer mangler eller er forældede: "
            + ", ".join(changed)
            + " — kør `python3 tools/lock_python_env.py`",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
