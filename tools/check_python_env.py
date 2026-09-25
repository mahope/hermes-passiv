#!/usr/bin/env python3
"""Hold det låste Python-miljø sandt, og Site Icons' metadata gyldig.

Opgave 13 (25. september 2026) lå `requirements-build.txt` og
`requirements-audit.txt` fast og rettede `site-icons/pyproject.toml`. Men en
låst fil, ingen ser på, er en fil der stivner: næste `pip install` i et byggeværktoj
trækker en ny version, låsen siger intet, og låsefilen lyver.

Derfor fire checks, der alle kan fejle på en måde ingen har villet se:

1. **Pins er pins.** Hver kravlinje er `navn==version` og har mindst én
   `--hash=sha256:`. En løs linje, et `-e .` eller en URL uden hash gør
   `--require-hashes` umulig eller ubeskyttet.
2. **Ingen konflikt.** Samme pakke må ikke stå i to filer med to versioner — så
   afhænger resultatet af rækkefølgen.
3. **Ingen ubrugte, ingen u deklarerede.** Værktøjerne i repoet skal ikke have
   en tredjepartspakke i importen som låsen ikke kender, og låsen må ikke have
   en pin intet værktøj bruger. Kun topniveauet tæller, fordi alt transitivt er
   løst af pip.
4. **Site Icons er PEP 621.** `[project]` med de felter der skal, `[build-system]`
   med backend, `[project.scripts]`, og — den der faktisk låst siden dag ét —
   `py-modules`, fordi `site_icons.py` er et fladt modul og `packages.find`
   derfor fandt ingenting.

Selftesten mutationerer hver enkelt af dem og kræver at porten **fejler** på
mutationen og **passer** på de rigtige filer. Uden den positive kontrol er en
gate, der siger "skal ikke fejle", intet bevis — samme pointe som opgave 16.

    python3 tools/check_python_env.py
    python3 tools/check_python_env.py --self-test
"""
from __future__ import annotations

import argparse
import ast
import re
import shutil
import sys
import sysconfig
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

try:  # Python 3.11+
    import tomllib
except ModuleNotFoundError:  # 3.9/3.10 — se mini_toml's docstring
    import mini_toml as tomllib  # type: ignore[no-redef]

import mini_toml  # noqa: E402

LOCKS = ("requirements-build.txt", "requirements-audit.txt")

#: Mapper der spejler kode, der ligger andre steder, og derfor ikke må tælle som
#: en uvedkommende afhængighed. `dist/` er bygget output, `node_modules` er npm.
SKIP_DIRS = {"dist", "node_modules", ".git", ".wrangler", "auditedwp-src", "__pycache__"}

#: Importnavne der ikke er distributionsnavnet. Porten sammenligner den
#: importerede pakke med det `pip install` skriver i låsen, og de to er ikke altid
#: ens — `import PIL` kommer fra distributionen `pillow`. Uden denne tabel ville
#: den stærkeste fejl i hele låsen (Pillow) set ud som en udeklareret afhængighed.
IMPORT_TO_DISTRIBUTION = {
    "PIL": "pillow",
    "attr": "attrs",
    "dateutil": "python-dateutil",
    "dotenv": "python-dotenv",
    "fpdf": "fpdf2",
    "jwt": "pyjwt",
    "OpenSSL": "pyopenssl",
    "pkg_resources": "setuptools",
    "serial": "pyserial",
    "sklearn": "scikit-learn",
    "tomllib": "tomli",  # kun relevant under 3.11, se STDLIB_EVEN_IF_MISSING
    "yaml": "pyyaml",
    "Crypto": "pycryptodome",
}

#: Moduler der er stdlib på *nogle* af de Python-versioner vi understøtter. En
#: betinget import som `try: import tomllib / except: import mini_toml` skal ikke
#: fejles som en udeklareret afhængighed på den version, hvor den mangler.
STDLIB_EVEN_IF_MISSING = {"tomllib"}

#: Endelser på C-udvidelser i standardbiblioteket, se `stdlib_names`.
EXTENSION_SUFFIXES = (".so", ".pyd", ".dylib")

#: Kilder der læses for tredjepartsimport. Alt i repoet er dækket med vilje:
#: en ny `import requests` i et hvilket som helst værktøj skal give en rød port,
#: ikke en ny fil i låsen ved næste tilfældighed.
SCAN_GLOBS = ("*.py", "tools/*.py", "site-icons/*.py", "scanner/**/*.py",
              "page-profile/*.py", "obsidian-plugin/*.py")

PIN_LINE = re.compile(r"^(?P<name>[A-Za-z0-9._-]+)==(?P<version>[A-Za-z0-9._+!-]+)$")
# Sidste hash i en pin har intet `\`-fortsættelsestegn; de første har. Begge
# former er gyldige, og kun den der matcher tæller som bevis på en hash.
HASH_LINE = re.compile(r"^\s+--hash=sha256:[0-9a-f]{64}(\s*\\)?$")
CONTINUATION = re.compile(r"\\\s*$")
COMMENT_OR_BLANK = re.compile(r"^\s*(#.*)?$")

# Felter Site Icons' manifest skal have, hver med hvorfor de ikke er valgfrie.
REQUIRED_PROJECT_FIELDS = {
    "name": "identiteten pip og `pip install site-icons` bruger",
    "version": "den version `--version` og vores egne sider oplyser",
    "description": "metadataen PyPI viser; uden den er pakken ufindelig",
    "requires-python": "sætter gulvet, så en for gammel Python siger det først ved install",
    "dependencies": "Pillow er en rigtig runtime-krav, ikke en dev-afhængighed",
}


# ── indlæsning ──────────────────────────────────────────────────────────────

def locked_pins(path: Path) -> dict[str, str]:
    """`navn -> version` for alle `==`-pins i en kravfil."""
    pins: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = PIN_LINE.match(read_stem(line))
        if match:
            pins[match.group("name").lower().replace("_", "-")] = match.group("version")
    return pins


def read_stem(line: str) -> str | None:
    """Første segment af en fortsættelseslinje, fx `--hash=...`."""
    stripped = line.strip()
    return stripped[:-1].strip() if CONTINUATION.search(stripped) else stripped


def check_pins_are_pinned(errors: list[str], root: Path) -> dict[str, dict[str, str]]:
    """Hver kravlinje er `navn==version` med mindst én hash ved siden af."""
    by_file: dict[str, dict[str, str]] = {}
    for filename in LOCKS:
        path = root / filename
        if not path.is_file():
            errors.append(f"{filename} mangler — generér den med tools/lock_python_env.py")
            continue
        pins = locked_pins(path)
        if not pins:
            errors.append(f"{filename} indeholder ingen `navn==version`-pin")
        by_file[filename] = pins

        lines = path.read_text(encoding="utf-8").splitlines()
        continued = False
        for number, raw in enumerate(lines, start=1):
            if COMMENT_OR_BLANK.match(raw):
                continued = CONTINUATION.search(raw) is not None
                continue
            if continued or HASH_LINE.match(raw):
                # Fortsættelse af den pin over den. Ikke en fejl i sig selv —
                # mangler der hashes, fanger løkken nedenfor det.
                continued = CONTINUATION.search(raw) is not None
                continue
            head = read_stem(raw)
            if not PIN_LINE.match(head):
                errors.append(
                    f"{filename}:{number}: {head!r} er ikke en `navn==version`-pin med "
                    f"`\\`-fortsættelse — låsen skal være ubetinget"
                )
                continue
            hashes = 0
            for follow in lines[number:]:
                if HASH_LINE.match(follow):
                    hashes += 1
                elif not COMMENT_OR_BLANK.match(follow):
                    break
            if hashes == 0:
                errors.append(
                    f"{filename}:{number}: {head!r} har ingen --hash=sha256: — "
                    f"`--require-hashes` ville afvise den"
                )
    return by_file


def conflict_report(by_file: dict[str, dict[str, str]]) -> list[str]:
    """Samme pakke må ikke stå i to filer med to versioner."""
    seen: dict[str, tuple[str, str]] = {}
    problems: list[str] = []
    for filename in LOCKS:
        for name, version in by_file.get(filename, {}).items():
            if name in seen and seen[name][1] != version:
                problems.append(
                    f"{name} står som {seen[name][1]} i {seen[name][0]} men som "
                    f"{version} i {filename} — installationen afhænger af rækkefølgen"
                )
            else:
                seen[name] = (filename, version)
    return problems


def stdlib_names() -> set[str]:
    """Topniveaunavne i den kørende interpreters standardbibliotek.

    Læst fra `sysconfig` i stedet for en håndlavet liste, fordi en håndlavet
    liste bliver forældet præcis på de Python-versioner den skal beskytte.

   også C-udvidelser, også dem der ligger i `lib-dynload`. `zlib` er
    `lib-dynload/zlib.cpython-39-darwin.so` — ingen `.py`, ingen `__init__.py` i
    mappen over den — så en kun-`.py`-optælling erklærer stdlib-modulet for
    tredjepart, og så kræver låsen `zlib` i `requirements-build.txt`. Fundet da
    `tools/check_versions.py` begyndte at læse beskadigede gzip-arkiver; navnet
    før `cpython` er modulet, resten er ABI-mærket.
    """
    names: set[str] = set()
    for key in ("stdlib", "platstdlib"):
        directory = Path(sysconfig.get_paths().get(key, ""))
        if not directory.is_dir():
            continue
        for entry in directory.iterdir():
            if entry.suffix == ".py" and entry.stem != "__init__":
                names.add(entry.stem)
            elif entry.is_dir():
                if (entry / "__init__.py").is_file():
                    names.add(entry.name)
                names.update(extension_names(entry))
    return names


def extension_names(directory: Path) -> set[str]:
    """Modulnavne for C-udvidelser i én mappe, som `lib-dynload`."""
    names: set[str] = set()
    try:
        entries = list(directory.iterdir())
    except OSError:
        return names
    for entry in entries:
        if entry.suffix in EXTENSION_SUFFIXES:
            stem = entry.name.split(".", 1)[0]
            if stem:
                names.add(stem)
    return names


def python_sources(root: Path) -> list[Path]:
    found: list[Path] = []
    for pattern in SCAN_GLOBS:
        for path in sorted(root.glob(pattern)):
            if any(part in SKIP_DIRS for part in path.relative_to(root).parts):
                continue
            found.append(path)
    return found


def third_party_imports(tree: ast.AST) -> set[str]:
    """Topniveaunavne i `import x` / `from x import y` der er lokale moduler."""
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                found.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0 and node.module:
                found.add(node.module.split(".")[0])
    return found


def local_module_names(root: Path) -> set[str]:
    """Værdier der er moduler i dette repo, så de ikke fejles som uafhængighed."""
    names: set[str] = set()
    for path in root.rglob("*.py"):
        if any(part in SKIP_DIRS for part in path.relative_to(root).parts):
            continue
        names.add(path.stem)
        if path.name == "__init__.py":
            names.add(path.parent.name)
    return names


def check_declared_matches_imports(errors: list[str], by_file: dict[str, dict[str, str]],
                                 root: Path) -> None:
    """Ingen tredjepartspakke importeres uden at låsen kender den — og omvendt."""
    stdlib = (stdlib_names() | set(sys.builtin_module_names) | local_module_names(root)
              | STDLIB_EVEN_IF_MISSING)
    declared = set(by_file.get("requirements-build.txt", {}))
    used: dict[str, list[str]] = {}

    for path in python_sources(root):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            errors.append(f"{path.relative_to(root)}: kan ikke parse ({exc})")
            continue
        for name in third_party_imports(tree):
            if name in stdlib:
                continue
            used.setdefault(IMPORT_TO_DISTRIBUTION.get(name, name), []).append(
                str(path.relative_to(root))
            )

    for name, sources in sorted(used.items()):
        if name.lower().replace("_", "-") not in declared:
            errors.append(
                f"{name} importeres af {', '.join(sorted(sources))[:120]} men står ikke "
                f"i requirements-build.txt — tilføj den i BUILD_TOP_LEVEL og regenerér"
            )

    # Kun topniveauet må være ubrugt: alt transitivt er løst af pip ud fra det,
    # så `charset-normalizer` og `pyee` skal IKKE regnes som overflødige.
    # `BUILD_TOP_LEVEL` er låsegeneratorens egen liste, så de to filer er samlet
    # om én kilde i stedet for om to.
    for name in sorted(top_level(root)):
        if name not in used and name not in {"setuptools", "wheel", "build"}:
            errors.append(
                f"BUILD_TOP_LEVEL i tools/lock_python_env.py beder om {name}, men intet "
                f"værktøj i repoet importerer det — enten er pakken overflødig, eller et "
                f"værktøj er holdt op med at bruge den. Fjern den fra listen."
            )


def top_level(root: Path) -> set[str]:
    """Låsegeneratorens egen topniveau-liste, som den skal være."""
    module = root / "tools" / "lock_python_env.py"
    if not module.is_file():
        return set()
    source = module.read_text(encoding="utf-8")
    try:
        return {
            re.sub(r"[-_.]+", "-", name).lower()
            for name in re.search(
                r"BUILD_TOP_LEVEL[^=]*=\s*\(([^)]*)\)", source, re.S
            ).group(1).replace('"', " ").replace(",", " ").split()
        }
    except AttributeError:
        return set()


def check_site_icons_manifest(errors: list[str], root: Path) -> None:
    """`site-icons/pyproject.toml` skal være en gyldig PEP 621-manifest."""
    path = root / "site-icons" / "pyproject.toml"
    if not path.is_file():
        errors.append("site-icons/pyproject.toml mangler")
        return
    # `loads(text)` — ikke `load(path)`. Den indlejrede `tomllib.load` kræver en
    # binær filobjekt og døde med `AttributeError: 'PosixPath' object has no
    # attribute 'read'` i CI (kørsel 36191355378), fordi kun Python 3.9 rammer
    # mini_toml-fallbacken. Begge moduler har `loads`, så vejen er den samme på
    # 3.9 og 3.12, og selftesten dækker den kode der faktisk kører.
    text = path.read_text(encoding="utf-8")
    try:
        data = tomllib.loads(text)
    except mini_toml.TOMLDecodeError as exc:
        errors.append(f"site-icons/pyproject.toml kan ikke læses: {exc}")
        return

    # Vi læser bevidst med mini_toml, ikke den indbyggede: så er den der fysisk
    # dækker filen på både 3.9 og 3.12, ikke kun hvor tomllib tilfældigvis findes.
    try:
        mini_toml.load(path)
    except mini_toml.TOMLDecodeError as exc:
        errors.append(f"site-icons/pyproject.toml er ulæselig for mini_toml: {exc}")

    project = data.get("project")
    if not isinstance(project, dict):
        errors.append(
            "site-icons/pyproject.toml har ingen [project]-tabel — metadata under "
            "[tool] ignoreres af setuptools, så pakken bygges uden navn eller krav"
        )
        return
    for field_name, why in REQUIRED_PROJECT_FIELDS.items():
        if field_name not in project:
            errors.append(f"site-icons/pyproject.toml: [project].{field_name} mangler ({why})")

    deps = project.get("dependencies")
    if not isinstance(deps, list) or not deps:
        errors.append("site-icons/pyproject.toml: [project].dependencies skal være en ikke-tom liste")
    elif not any(re.match(r"^[Pp]illow", str(item)) for item in deps):
        errors.append(
            "site-icons/pyproject.toml: dependencies nævner ikke Pillow, men "
            "site_icons.py importerer den — en ren install ville starte med ImportError"
        )

    build_system = data.get("build-system")
    backend = build_system.get("build-backend") if isinstance(build_system, dict) else None
    requires = (build_system or {}).get("requires") or []
    if not backend:
        errors.append("site-icons/pyproject.toml: [build-system].build-backend mangler")
    else:
        # En backend skal pege på en distribution der faktisk er erklæret, ellers
        # bygger pip den i et isolat miljø hvor den hverken findes eller installeres.
        # Om selve attributtet findes bevises ikke her — det gør `python3 -m build`
        # i opgave 13s port, som faktisk kalder backenden.
        module = str(backend).split(":")[0].split(".")[0]
        declared = {
            re.sub(r"[-_.]+", "-", re.split(r"[<>=!~\[]", str(item))[0]).lower()
            for item in requires
        }
        if module and module not in declared:
            errors.append(
                f"site-icons/pyproject.toml: build-backend {backend!r} kræver "
                f"{module!r}, men [build-system].requires erklærer kun "
                f"{sorted(declared) or 'intet'}"
            )
    if isinstance(build_system, dict) and not requires:
        errors.append("site-icons/pyproject.toml: [build-system].requires mangler")

    scripts = project.get("scripts")
    if not isinstance(scripts, dict) or scripts.get("site-icons") != "site_icons:main":
        errors.append(
            "site-icons/pyproject.toml: [project.scripts] skal have "
            "`site-icons = \"site_icons:main\"` — ellers findes der ingen kommando efter install"
        )

    # Den fejl der lå på dag ét: et fladt modul er ikke en pakke.
    tool = data.get("tool", {}).get("setuptools", {})
    if isinstance(tool, dict) and "packages" in tool and "py-modules" not in tool:
        errors.append(
            "site-icons/pyproject.toml bruger [tool.setuptools.packages] — men "
            "site_icons.py er et fladt modul uden __init__.py, så pakkesøgningen "
            "finder intet. Skriv `[tool.setuptools] py-modules = [\"site_icons\"]`."
        )
    elif not isinstance(tool, dict) or "site_icons" not in (tool.get("py-modules") or []):
        errors.append(
            "site-icons/pyproject.toml: [tool.setuptools].py-modules skal være "
            "[\"site_icons\"], ellers bygges et hjul uden kode"
        )

    requires_python = str(project.get("requires-python", ""))
    floor = re.search(r">=\s*(\d+)\.(\d+)", requires_python)
    if floor is None:
        errors.append(
            f"site-icons/pyproject.toml: requires-python {requires_python!r} er ikke et "
            f"gulv (`>=X.Y`) — porten kan ikke vide hvad en hævet version betyder"
        )
    elif (int(floor.group(1)), int(floor.group(2))) > (3, 9):
        errors.append(
            f"site-icons/pyproject.toml: requires-python er hævet til "
            f"{requires_python!r} — site_icons.py bruger `from __future__ import "
            f"annotations` og er testet på 3.9, så hæver man gulvet uden at teste "
            f"den nye Python, udelukker man bare brugere uden grund"
        )


# ── kørsel ──────────────────────────────────────────────────────────────────

def run_checks(root: Path) -> list[str]:
    errors: list[str] = []
    by_file = check_pins_are_pinned(errors, root)
    errors.extend(conflict_report(by_file))
    check_declared_matches_imports(errors, by_file, root)
    check_site_icons_manifest(errors, root)
    return errors


def _pin_line(path: Path, name: str) -> str:
    """Den pin-linje der starter med `navn==`, uanset hvilken version der står."""
    for line in path.read_text(encoding="utf-8").splitlines():
        stem = read_stem(line)
        if PIN_LINE.match(stem) and stem.startswith(f"{name}=="):
            return line
    raise SystemExit(f"selftest: ingen pin for {name} i {path.name}")


def _mutate(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"selftest: mønster ikke fundet i {path}: {old!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def run_self_test() -> int:
    scenarios: list[tuple[str, callable]] = []

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        # Hele det scannede træ skal med, ellers er `used` tomt i det midlertidige
        # rod, og porten ville være rød af en grund der intet har med mutationen at
        # gøre. Kun de filer porten faktisk læser kopieres — ikke zip-arkiver,
        # node_modules eller dist.
        for name in LOCKS:
            (root / name).write_text(
                (ROOT / name).read_text(encoding="utf-8"), encoding="utf-8"
            )
        (root / "site-icons").mkdir(parents=True, exist_ok=True)
        (root / "site-icons" / "pyproject.toml").write_text(
            (ROOT / "site-icons" / "pyproject.toml").read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        for source in python_sources(ROOT):
            target = root / source.relative_to(ROOT)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)


        def without_project_table(r: Path, f: Path) -> list[str]:
            _mutate(f, "[project]", "[projectx]")
            return run_checks(r)

        def with_packages_instead_of_modules(r: Path, f: Path) -> list[str]:
            _mutate(
                f,
                '[tool.setuptools]\npy-modules = ["site_icons"]',
                "[tool.setuptools.packages.find]\ninclude = [\"site_icons*\"]",
            )
            return run_checks(r)

        def without_entry_point(r: Path, f: Path) -> list[str]:
            _mutate(f, 'site-icons = "site_icons:main"', 'site-icons = "site_icons:start"')
            return run_checks(r)

        def without_build_backend(r: Path, f: Path) -> list[str]:
            _mutate(f, 'build-backend = "setuptools.build_meta"\n', "")
            return run_checks(r)

        def without_pillow(r: Path, f: Path) -> list[str]:
            _mutate(f, '    "Pillow>=10.0",\n', "")
            return run_checks(r)

        def with_raised_floor(r: Path, f: Path) -> list[str]:
            _mutate(f, 'requires-python = ">=3.9"', 'requires-python = ">=3.11"')
            return run_checks(r)

        def without_a_hash(r: Path, f: Path) -> list[str]:
            # Rører KUN det midlertidige copy. En tidligere udgave af denne
            # mutation skrev i den rigtige låsefil og efterlod den med en hash
            # mindre — selftesten må aldrig kunne ændre repoet, den kontrollerer.
            # ALLE hashes på den første pin, ikke én. At fjerne én af to er
            # stadig en gyldig låst pin — det ville være synd at gøre porten rød
            # for det, så mutationen skal ramme hele blokken.
            target = r / "requirements-build.txt"
            lines = target.read_text(encoding="utf-8").splitlines()
            first = next(i for i, line in enumerate(lines) if PIN_LINE.match(read_stem(line)))
            end = first + 1
            while end < len(lines) and HASH_LINE.match(lines[end]):
                end += 1
            del lines[first + 1:end]
            target.write_text("\n".join(lines) + "\n", encoding="utf-8")
            return run_checks(r)

        def with_unpinned_requirement(r: Path, f: Path) -> list[str]:
            # Finder den version der står i låsen i stedet for at hardkode den: en
            # selftest der kender et versionsnummer holder op med at teste noget
            # den dag nr. opdateres, og fejler så med en forvirrende SystemExit.
            target = r / "requirements-build.txt"
            stem = read_stem(_pin_line(target, "pillow")).removesuffix("!")
            _mutate(target, stem, "pillow>=10.0")
            return run_checks(r)

        def with_editable_requirement(r: Path, f: Path) -> list[str]:
            target = r / "requirements-build.txt"
            _mutate(target, read_stem(_pin_line(target, "build")), "-e .\\")
            return run_checks(r)

        def with_conflicting_versions(r: Path, f: Path) -> list[str]:
            # Vælger en pakke der står i BEGGE låse, så mutationen tester
            # versionskonflikten og ikke en pakke der kun findes i den ene.
            shared = sorted(
                set(locked_pins(r / "requirements-build.txt"))
                & set(locked_pins(r / "requirements-audit.txt"))
            )
            if not shared:
                raise SystemExit("selftest: ingen pakke i begge låse at konflikttere på")
            (r / "requirements-audit.txt").write_text(
                (r / "requirements-audit.txt").read_text(encoding="utf-8")
                + f"\n{shared[0]}==0.0.1 \\\n    --hash=sha256:" + "0" * 64 + "\n",
                encoding="utf-8",
            )
            return run_checks(r)

        def with_undeclared_import(r: Path, f: Path) -> list[str]:
            (r / "tools" / "tmp_dep_probe.py").write_text(
                "import totallynewdependency\n", encoding="utf-8"
            )
            return run_checks(r)

        def with_unused_pin(r: Path, f: Path) -> list[str]:
            # Det ubrugte-punktet gælder kun topniveau, så en ekstra pin i
            # låsefilen er lovlig — den er transitiv. Den ulovlige er en
            # topniveau-pakke intet værktøj bruger, og den skrives i generatoren.
            generator = r / "tools" / "lock_python_env.py"
            _mutate(generator, '    "build",\n', '    "build",\n    "leftpad",\n')
            return run_checks(r)

        def without_a_lock_file(r: Path, f: Path) -> list[str]:
            (r / "requirements-audit.txt").unlink()
            return run_checks(r)

        scenarios.extend(
            [
                ("[project] fjernet fra site-icons-manifestet", without_project_table),
                ("py-modules erstattet af packages.find", with_packages_instead_of_modules),
                ("[project.scripts] peger på en der ikke findes", without_entry_point),
                ("build-backend-nøglen fjernet", without_build_backend),
                ("Pillow fjernet fra dependencies", without_pillow),
                ("requires-python hævet uden kodeændring", with_raised_floor),
                ("én hash fjernet fra en pin", without_a_hash),
                ("krav gjort til et interval i stedet for en pin", with_unpinned_requirement),
                ("-e . i låsen", with_editable_requirement),
                ("samme pakke i to filer med to versioner", with_conflicting_versions),
                ("værktøj importerer en pakke låsen ikke kender", with_undeclared_import),
                ("låsen har en pin intet værktøj bruger", with_unused_pin),
                ("en af låsefilerne mangler", without_a_lock_file),
            ]
        )

        # Positiv kontrol først, og som sin egen påstand: mutationerne kræver at
        # porten **fejler** på dem, så uden en grøn start kan en port der altid
        # siger "fejl" se ud som om den fanger alt.
        failures: list[str] = []
        if run_checks(root):
            failures.append("  ✗ de rigtige filer er røde — mutationerne nedenfor kan ikke fange noget")

        for name, scenario in scenarios:
            # Hvert scenario får et rent snapshot af de kildefiler det rører, så
            # en mutation ikke kan arve fejlen fra den forrige.
            (root / "site-icons" / "pyproject.toml").write_text(
                (ROOT / "site-icons" / "pyproject.toml").read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            for filename in LOCKS:
                (root / filename).write_text(
                    (ROOT / filename).read_text(encoding="utf-8"), encoding="utf-8"
                )
            (root / "tools" / "lock_python_env.py").write_text(
                (ROOT / "tools" / "lock_python_env.py").read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            probe = root / "tools" / "tmp_dep_probe.py"
            if probe.exists():
                probe.unlink()
            errors = scenario(root, root / "site-icons" / "pyproject.toml")
            if errors:
                print(f"  ✓ mutation fanget: {name} ({len(errors)} fejl)")
            else:
                failures.append(f"  ✗ {name} — burde have fejlet, men var grøn")

        # Rigsige file skal stadig være grønne efter alle mutationerne.
        probe = root / "tools" / "tmp_dep_probe.py"
        if probe.exists():
            probe.unlink()
        for filename in LOCKS:
            (root / filename).write_text(
                (ROOT / filename).read_text(encoding="utf-8"), encoding="utf-8"
            )
        for filename in ("site-icons/pyproject.toml", "tools/lock_python_env.py"):
            (root / filename).write_text(
                (ROOT / filename).read_text(encoding="utf-8"), encoding="utf-8"
            )
        leftover = run_checks(root)
        if leftover:
            failures.append("  ✗ efter alle mutationer er porten stadig rød på de rigtige filer")
        else:
            print("  ✓ de rigtige filer er grønne før og efter alle mutationer")

    # C-udvidelserne i `stdlib_names` kan ikke mutationeres gennem `run_checks`:
    # de læses fra `sysconfig` i den kørende interpreter, ikke fra workspace-kopien.
    # Så de får deres egen kontrol, der køres mod `stdlib_names` direkte.
    controls: list[tuple[str, bool]] = []
    names = stdlib_names()
    for module in ("zlib", "readline", "sqlite3", "json", "tarfile", "zipfile"):
        controls.append((f"{module} genkendes som stdlib", module in names))
    with tempfile.TemporaryDirectory() as scratch:
        fake = Path(scratch)
        (fake / "some_cmodule.cpython-99-darwin.so").write_bytes(b"")
        (fake / "readme.txt").write_text("ikke en udvidelse", encoding="utf-8")
        found = extension_names(fake)
        controls.append(("navnet før ABI-mærket læses ud", found == {"some_cmodule"}))
    for name, ok in controls:
        if ok:
            print(f"  ✓ kontrol: {name}")
        else:
            failures.append(f"  ✗ kontrol: {name}")

    passed = len(scenarios)
    if failures:
        print(f"check_python_env --self-test: {len(failures)} fejl")
        for line in failures:
            print(line)
        return 1
    print(f"check_python_env --self-test: OK ({passed} mutationer, inkl. positiv kontrol)")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--self-test", action="store_true",
                        help="mutationer porten og kræver at den fejler på hver")
    args = parser.parse_args(argv)

    if args.self_test:
        return run_self_test()

    errors = run_checks(ROOT)
    if errors:
        print(f"check_python_env: {len(errors)} fejl", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1
    total = sum(len(locked_pins(ROOT / name)) for name in LOCKS if (ROOT / name).is_file())
    print(f"check_python_env: OK — {total} pins låst og hash-tjekket, "
          f"site-icons-manifestet gyldigt, {len(python_sources(ROOT))} Python-filer dækket")
    return 0


if __name__ == "__main__":
    sys.exit(main())
