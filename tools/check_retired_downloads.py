#!/usr/bin/env python3
"""Gaten for arkiver, der er taget ud af repoet men stadig kan hentes.

Baggrund (opgave 28): `site/downloads/clean-copy-firefox-v1.5.3.zip` blev slettet
i git i opgave 27, fordi README'en i den lovede "**No network requests** — nothing
leaves your browser", mens `license.js` poster nøglen til
`https://mahope.tools/api/license`. Rettelsen holdt i kilden. Men opgave 27s egen
gen-test fandt filen **stadig hentbar** på cleancopy.tools: 200, 23344 byte, med
den gamle README og et badge på `version-1.4.1` i et arkiv der hed 1.5.3.

Årsagen er ikke en fejl i kilden: den er slettet overalt, og den ligger i ingen
dist. Cloudflare Pages **fjerner ikke slettede assets** — den gamle fil bliver
liggende i CDN'en og serveres stadig. Så "opgaven er færdig, filen er væk" var
falsk for præcis den gruppe kunder, der rammer den værste fejl: en der henter
klienten og tror på privatlivsteksten.

Denne port gør fejlformen permanent rød. Seks kontroller:

  1. `json_worker_mismatch`  `tools/retired_downloads.json` og worker's
                             `RETIRED_DOWNLOADS` er ikke ens — i hver retning.
                             Uden den ville den ene kunne blive opdateret og den
                             anden ikke, og så er filen hentbar igen uden at
                             nogen mærker det.
  2. `retired_in_dist`       en \"tilbagetrukket\" sti findes stadig i dist. Den
                             er så ikke tilbagetrukket, og 301'en ville skjule
                             den rigtige fil.
  3. `target_missing`        `replaced_by` findes ikke i dist. En 301 til en død
                             sti er værre end den gamle fil: kunden får en 404
                             i stedet for en gammel version.
  4. `still_linked`         en kildefil i `site/` (eller rod-README'en) linker
                             stadig til den tilbagetrukne sti, så vores egne
                             sider sender kunden i den gamle fil.
  5. `no_reason`             en sti er trukket tilbage uden en begrundelse. Uden
                             den er klassen umulig at revidere om et halvt år.
  6. `undocumented_deletion` et arkiv under `site/downloads/` er **slettet i
                             git-historikken** uden at være nævnt nogen steder.
                             Opgave 39: `eaa-scanner-desktop-src-1.3.3.zip` blev
                             slettet da versionen steg, filen indeholdt den
                                 urettede `$19/year` fra opgave 38, og den lå stadig
                                 i CDN'en med 200. De fem kontroller ovenfor læser
                             json, worker og dist — alle tre var rene, fordi
                             *sletningen* ikke stod nogen steder. Derfor læses
                             git-historikken: en slettet sti skal enten stå under
                             et domæn med en 301, eller under `_gone` med en
                             begrundelse for hvorfor den ikke skal have en.

Og `tools/check_live_sitemaps.py`, som kører efter hver deploy, bekræfter det
sidste og afgørende: en tilbagetrukket sti må **ikke** svare 200 i produktion.
Porten her kan ikke se CDN'en; den kan bare sørge for, at der står en 301, før
deployen.

    python3 tools/check_retired_downloads.py             # kræver dist, kører i gaten
    python3 tools/check_retired_downloads.py --self-test # bevis at porten fanger fejlene
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "tools" / "retired_downloads.json"
WORKER = ROOT / "site" / "_worker.js"
DIST = ROOT / "dist"

# Kendte domæner, så en skrivefejl i json ikke bare opretter et nyt nøglesæt.
KNOWN_DOMAINS = {"mahope.tools", "cleancopy.tools", "deskuptime.com", "bugbottle.dev"}

WORKER_TABLE = re.compile(r"const RETIRED_DOWNLOADS = \{(.*?)\};", re.S)


def load_catalog() -> tuple[dict, list[str]]:
    """Returnér (hele katalogen, problemer). En fejlende json er en fejl, ikke en tom katalog.

    Underscores nøgles heller ikke filtreres her: `_gone` er data porten skal læse
    (kontrol 6), og de to forbrugere filtrerer selv.
    """
    if not CATALOG.is_file():
        return {}, [f"missing {CATALOG.relative_to(ROOT)}"]
    try:
        data = json.loads(CATALOG.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        return {}, [f"{CATALOG.relative_to(ROOT)} is not valid JSON: {error}"]
    if not isinstance(data, dict):
        return {}, [f"{CATALOG.relative_to(ROOT)} must be an object"]
    return data, []


DELETED_PREFIX = "site/downloads/"


def deleted_download_paths() -> tuple[set[str], str | None]:
    """Stier under `site/downloads/` der er slettet i git-historikken, som `/`-stier.

    Det er den eneste måde at se en sletning på: dist er ren, og både json og
    worker kan være i overensstemmelse med hinanden mens de slet ikke nævner,
    at filen forsvandt. Kræver fuld historik — `deploy-sites.yml`' gate-job
    checker med `fetch-depth: 0`, så det er en vilkårlig dybde-klon der gør
    porten rød, ikke en vilkårlig fejl.
    """
    try:
        depth = int(subprocess.run(
            ["git", "rev-list", "--count", "HEAD"],
            cwd=ROOT, capture_output=True, text=True, timeout=60, check=True,
        ).stdout.strip())
    except (FileNotFoundError, ValueError, subprocess.SubprocessError) as error:
        return set(), f"cannot count commits in the git history: {error}"
    if depth < 2:
        # Uden denne ville en `depth=1`-klon give en grøn port, fordi en
        # slettet fil slet ikke kan være i historikken. Det er præcis den
        # stumme kontrol, porten her skal overleve: siger den intet, skal den
        # sige det med en fejl, ikke med en grøn linje.
        return set(), f"git-historikken er for grund ({depth} commits) — en klon med dybde 1 kan ikke se slettede filer, brug fetch-depth: 0"
    try:
        done = subprocess.run(
            ["git", "log", "--diff-filter=D", "--name-only", "--pretty=format:", "--", DELETED_PREFIX.rstrip("/")],
            cwd=ROOT, capture_output=True, text=True, timeout=120, check=True,
        )
    except FileNotFoundError:
        return set(), "git is not installed, so deleted archives cannot be read from the history"
    except subprocess.SubprocessError as error:
        detail = (error.stderr or "").strip() or str(error)
        return set(), f"cannot read the git history ({DELETED_PREFIX}): {detail}"
    # `site/downloads/x` -> `/downloads/x`: samme sti som worker og dist bruger.
    return {line.strip()[len("site"):] for line in done.stdout.splitlines() if line.strip().startswith(DELETED_PREFIX)}, None



def worker_entries() -> tuple[dict[str, str], str | None]:
    """Læs RETIRED_DOWNLOADS ud af workeren. Samme mønster som check_sitemaps."""
    if not WORKER.is_file():
        return {}, f"missing {WORKER.relative_to(ROOT)}"
    match = WORKER_TABLE.search(WORKER.read_text(encoding="utf-8"))
    if not match:
        return {}, "worker redirect table not found: const RETIRED_DOWNLOADS = {...}"
    return dict(re.findall(r"['\"](/[^'\"]+)['\"]\s*:\s*['\"](/[^'\"]+)['\"]", match.group(1))), None


def dist_has(domain: str, path: str) -> bool:
    return (DIST / domain / path.lstrip("/")).is_file()


def check() -> list[str]:
    problems: list[str] = []
    # Selftesten skriver nye kataloger under sig, så cache'en skal ikke overleve
    # et check — ellers læser orphan-reglen den gamle fil og siger "grøn".
    global _CATALOG_PATHS
    _CATALOG_PATHS = {}
    catalog, load_problems = load_catalog()
    problems.extend(load_problems)

    worker, worker_error = worker_entries()
    if worker_error:
        problems.append(worker_error)
        worker = {}

    for domain, entries in catalog.items():
        if domain.startswith("_"):
            continue
        if domain not in KNOWN_DOMAINS:
            problems.append(f"unknown_domain: {domain} is not a domain this repo builds")
            continue
        if not isinstance(entries, dict):
            problems.append(f"malformed_catalog: {domain}: retired paths must be an object")
            continue
        for retired, meta in entries.items():
            if not isinstance(meta, dict):
                problems.append(f"malformed_catalog: {domain}{retired}: entry must be an object with replaced_by and reason")
                continue
            target = meta.get("replaced_by")
            if not isinstance(target, str) or not target.startswith("/downloads/"):
                problems.append(f"malformed_catalog: {domain}{retired}: replaced_by must be a /downloads/ path, got {target!r}")
                continue
            if target == retired:
                problems.append(f"self_reference: {domain}{retired}: replaced_by points at itself")
                continue
            if not str(meta.get("reason") or "").strip():
                problems.append(f"no_reason: {domain}{retired}: no reason given")

            # 1) json og worker skal være ens i begge retninger.
            if worker.get(retired) != target:
                problems.append(
                    f"json_worker_mismatch: {domain}{retired}: json says replaced_by={target!r} but worker says "
                    f"{worker.get(retired)!r} — the two must be identical or the file is fetchable again"
                )
            # 2) en tilbagetrukket sti må ikke findes i dist.
            if DIST.is_dir() and dist_has(domain, retired):
                problems.append(f"retired_in_dist: {domain}{retired}: is still in dist — it is not retired, and the 301 would hide the real file")
            # 3) målet skal findes.
            if DIST.is_dir() and not dist_has(domain, target):
                problems.append(f"target_missing: {domain}{target}: replaced_by target does not exist in dist")

            # 4) vores egne sider må ikke sende kunden i den gamle fil.
            for source in site_sources():
                if not source.is_file():
                    continue
                if retired in source.read_text(encoding="utf-8", errors="ignore"):
                    problems.append(f"still_linked: {source.relative_to(ROOT)}: still links to the retired {retired}")

    # 1b) en sti i workeren, der ikke står i json, er en fælde uden kilde.
    for retired, target in sorted(worker.items()):
        entries = catalog.get(_domain_for(retired))
        if not isinstance(entries, dict) or retired not in entries:
            problems.append(f"orphan_worker_rule: worker redirects {retired} -> {target} but retired_downloads.json does not list it")

    # 6) en sletning uden ord. Dist er ren og de to kilder er enige, så uden
    #    denne kontrol er en arkivfil, der forsvinder, usynlig for porten.
    gone = catalog.get("_gone")
    if gone is not None and not isinstance(gone, dict):
        problems.append(f"malformed_catalog: _gone must be an object of path -> reason, got {type(gone).__name__}")
        gone = {}
    for path in sorted(gone or {}):
        if not str((gone or {}).get(path) or "").strip():
            problems.append(f"no_reason: _gone{path}: an archive that is gone needs a reason, otherwise the next reader cannot tell 404 from an oversight")
    documented = {p for d in KNOWN_DOMAINS for p in (catalog.get(d) or {})} | set(gone or {})
    deleted, history_error = deleted_download_paths()
    if history_error:
        problems.append(f"history_unreadable: {history_error}")
    for path in sorted(deleted - documented):
        problems.append(
            f"undocumented_deletion: {path} was deleted from {DELETED_PREFIX} but appears neither as a retired path nor under _gone"
            " — if it answers 404 in production a 301 buys nothing, so record it under _gone with the measurement"
        )
    return problems



def _domain_for(path: str) -> str:
    for domain in KNOWN_DOMAINS:
        if catalog_domain_paths().get(path) == domain:
            return domain
    return ""


_CATALOG_PATHS: dict[str, str] = {}


def catalog_domain_paths() -> dict[str, str]:
    global _CATALOG_PATHS
    if not _CATALOG_PATHS:
        catalog, _ = load_catalog()
        _CATALOG_PATHS = {p: d for d, entries in catalog.items() if isinstance(entries, dict) and d in KNOWN_DOMAINS for p in entries}
    return _CATALOG_PATHS


SITE_SOURCES_GLOB = "site/**/*.html"


def site_sources() -> tuple[Path, ...]:
    """Kildefilerne der må linke til en download.

    Beregnet *inde i* check() og ikke på import: en konstant på modulniveau blev
    frosset, da den blev skrevet, og selftestens probe-fil blev derfor aldrig
    læst — scenariet stod som grønt, fordi porten aldrig kiggede. Samme
    stumme kontrol som opgave 17 fund 3.
    """
    return tuple(sorted(ROOT.glob(SITE_SOURCES_GLOB))) + (ROOT / "README.md",)


def self_test() -> int:
    """Bevis at porten fanger fejlformerne — på konstruerede strenge og på rigtig historik."""
    passed, failed = 0, []

    def expect(problems: list[str], rule: str, navn: str) -> None:
        """Kontrollen skal have *navngivet* den fejlform, den er skrevet til.

        Løst på understrengen, så en fejl med et andet navn ikke kan tælle som
        fanget: en regel der rammer den forkerte kode skal være rød i selftesten.
        """
        nonlocal passed
        if any(rule in p for p in problems):
            passed += 1
        else:
            failed.append(f"{navn} (forventede {rule}, fik {problems})")

    def clean() -> list[str]:
        return check()

    def set_worker_target(text: str, path: str, target: str) -> str:
        """Skriv en ny målsti ind i workerens tabel, uanset hvor i den den står.

        De første mutationer brugte `"...v1.5.4.zip',\\n    };"` — altså den
        *sidste* linje før `};`. Da opgave 39 føjede endnu en regel til, holdt
        mønstret ikke længere, mutationerne blev tavse no-ops, og selftesten
        meldte "selvrefererende redirect" som *ikke* fanget. Position er ikke en
        egenskab porten har forhold sig til; stien har den.
        """
        pattern = re.compile(rf"['\"]{re.escape(path)}['\"]\s*:\s*['\"][^'\"]+['\"]")
        return pattern.sub(f"'{path}': '{target}'", text)

    CC_OLD = "/downloads/clean-copy-firefox-v1.5.3.zip"
    CC_NEW = "/downloads/clean-copy-firefox-v1.5.4.zip"

    baseline = clean()
    if baseline:
        failed.append(f"den rigtige kode skal være grøn, fik {baseline}")
    else:
        passed += 1

    # 1) worker uden reglen for en json-sti.
    real_worker = WORKER.read_text(encoding="utf-8")
    try:
        WORKER.write_text(WORKER_TABLE.sub("const RETIRED_DOWNLOADS = {};", real_worker), encoding="utf-8")
        expect(clean(), "json_worker_mismatch", "tom worker-tabel")
        # 2) worker der peger på den gamle fil selv.
        WORKER.write_text(set_worker_target(real_worker, CC_OLD, CC_OLD), encoding="utf-8")
        expect(clean(), "json_worker_mismatch", "selvrefererende redirect")
        # 3) en regel i workeren, som json ikke kender.
        WORKER.write_text(real_worker.replace("const RETIRED_DOWNLOADS = {\n", "const RETIRED_DOWNLOADS = {\n    '/downloads/clean-copy-firefox-v1.0.0.zip': '/downloads/clean-copy-firefox-v1.5.4.zip',\n"), encoding="utf-8")
        expect(clean(), "orphan_worker_rule", "regel i worker uden json")
    finally:
        WORKER.write_text(real_worker, encoding="utf-8")

    # 4) json uden begrundelse, med ukendt domæne og med sig selv som mål.
    real_catalog = CATALOG.read_text(encoding="utf-8")
    try:
        data = json.loads(real_catalog)
        path, meta = next(iter(next(iter(v for k, v in data.items() if not k.startswith("_"))).items()))
        domain = next(k for k, v in data.items() if not k.startswith("_"))

        no_reason = json.loads(real_catalog)
        del no_reason[domain][path]["reason"]
        CATALOG.write_text(json.dumps(no_reason, indent=2), encoding="utf-8")
        expect(clean(), "no reason", "tilbagetrukket uden begrundelse")

        self_ref = json.loads(real_catalog)
        self_ref[domain][path]["replaced_by"] = path
        CATALOG.write_text(json.dumps(self_ref, indent=2), encoding="utf-8")
        expect(clean(), "self_reference", "replaced_by peger på sig selv")

        unknown = json.loads(real_catalog)
        unknown["eksempel.invalid"] = {path: meta}
        CATALOG.write_text(json.dumps(unknown, indent=2), encoding="utf-8")
        expect(clean(), "unknown_domain", "ukendt domæne")

        missing_target = json.loads(real_catalog)
        missing_target[domain][path]["replaced_by"] = "/downloads/clean-copy-firefox-v9.9.9.zip"
        WORKER.write_text(set_worker_target(real_worker, CC_OLD, "/downloads/clean-copy-firefox-v9.9.9.zip"), encoding="utf-8")
        CATALOG.write_text(json.dumps(missing_target, indent=2), encoding="utf-8")
        expect(clean(), "target_missing", "målet mangler i dist")
        WORKER.write_text(real_worker, encoding="utf-8")

        # 5) en vores-kildefil der stadig linker til den tilbagetrukne sti.
        broken_json = json.loads(real_catalog)
        CATALOG.write_text(json.dumps(broken_json, indent=2), encoding="utf-8")
        probe = ROOT / "site" / "_retired_downloads_selftest.html"
        probe.write_text(f'<a href="{path}">gammelt arkiv</a>', encoding="utf-8")
        try:
            expect(clean(), "still links to the retired", "kildeside der linker til den tilbagetrukne sti")
        finally:
            probe.unlink()

        # 6) dist-restaurering: en \"tilbagetrukket\" sti, der faktisk ligger i dist.
        dist_file = DIST / domain / path.lstrip("/")
        if dist_file.parent.is_dir():
            made = False
            if not dist_file.exists():
                dist_file.parent.mkdir(parents=True, exist_ok=True)
                dist_file.write_bytes(b"PK\x03\x04")
                made = True
            try:
                expect(clean(), "retired_in_dist", "tilbagetrukket sti ligger stadig i dist")
            finally:
                if made:
                    dist_file.unlink()
        else:
            # Uden dist kan porten ikke se filerne; det er ærligt, ikke grønt.
            print("  (springer retired_in_dist: dist er ikke bygget)")

        # 7) kontrol 6: en sletning i git-historikken, der ingen steder står.
        #    D første scenarie er præcis den tilstand opgave 39 rettede: 1.3.3
        #    slettet i git, filen liggende i CDN'en med 200, og hverken json
        #    eller worker med en 301. Beviset kommer fra git, ikke fra en
        #    konstrueret streng, så scenariet døjer, hvis historikken holder op
        #    at svare.
        pre_fix = json.loads(real_catalog)
        del pre_fix["mahope.tools"]
        CATALOG.write_text(json.dumps(pre_fix, indent=2), encoding="utf-8")
        found = clean()
        expect(found, "/downloads/eaa-scanner-desktop-src-1.3.3.zip", "slettet arkiv uden 301 og uden _gone")
        expect(found, "orphan_worker_rule", "samme tilstand: workerens regel står uden json")

        drop_gone = json.loads(real_catalog)
        drop_gone["_gone"].pop("/downloads/page-profile/page-profile-1.0.0.tar.gz")
        CATALOG.write_text(json.dumps(drop_gone, indent=2), encoding="utf-8")
        expect(clean(), "page-profile-1.0.0.tar.gz", "arkiv fjernet fra _gone uden at blive dokumenteret")

        # Negativ kontrol: en _gone-post UDEN begrundelse må fejle — ellers er
        # `_gone` bare en navneliste, og netop det gør porten teater.
        no_gone_reason = json.loads(real_catalog)
        no_gone_reason["_gone"]["/downloads/clean-copy-v1.5.2.zip"] = ""
        CATALOG.write_text(json.dumps(no_gone_reason, indent=2), encoding="utf-8")
        expect(clean(), "_gone/downloads/clean-copy-v1.5.2.zip", "gone-post uden begrundelse")

        # Negativ kontrol: en fuldt gyldig `_gone` skal være grøn. Uden denne
        # kunne porten fejle på enhver post i listen og stadig se grøn ud i
        # selftesten, fordi alle de andre scenarier fanger *noget*.
        intact = json.loads(real_catalog)
        CATALOG.write_text(json.dumps(intact, indent=2), encoding="utf-8")
        if clean():
            failed.append(f"en fuldt gyldig _gone-liste skal være grøn, fik {clean()}")
        else:
            passed += 1

        broken_gone = json.loads(real_catalog)
        broken_gone["_gone"] = ["/downloads/clean-copy-v1.5.2.zip"]
        CATALOG.write_text(json.dumps(broken_gone, indent=2), encoding="utf-8")
        expect(clean(), "_gone must be an object", "_gone er en liste")

        # Stumheds-kontrol: hvis git-historikken ikke kan læses, må porten sige
        # det. Ellers er kontrol 6 teater i præcis det tilfælde den er skrevet
        # til — en klon der ikke kan se slettede filer.
        real_reader = globals()["deleted_download_paths"]
        try:
            globals()["deleted_download_paths"] = lambda: (set(), "git-historikken er for grund (1 commits) — fetch-depth: 0")
            expect(clean(), "history_unreadable", "git-historikken kan ikke læses")
            # Og negativt: når læseren svarer normalt, skal der igen være grønt,
            # så scenariet ovenfor ikke kan bestå ved et tilfældigt rødt.
            globals()["deleted_download_paths"] = real_reader
            CATALOG.write_text(json.dumps(intact, indent=2), encoding="utf-8")  # katalogen stod stadig som liste fra forrige mutation
            if clean():
                failed.append(f"efter at læseren er gendannet skal der være grønt, fik {clean()}")
            else:
                passed += 1
        finally:
            globals()["deleted_download_paths"] = real_reader
    finally:
        CATALOG.write_text(real_catalog, encoding="utf-8")
        WORKER.write_text(real_worker, encoding="utf-8")

    # 7) Rigtig kode efter alle mutationer.
    if check():
        failed.append("selftesten efterlod repoet i en ugyldig tilstand")
    else:
        passed += 1

    for problem in failed:
        print("FEJL:", problem)
    print(f"check_retired_downloads --self-test: {'OK' if not failed else 'FEJL'} ({passed} kontroller, {len(failed)} fejl)")
    return 1 if failed else 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--self-test", action="store_true", help="bevis at porten fanger fejlformerne")
    args = ap.parse_args(argv)
    if args.self_test:
        return self_test()
    problems = check()
    for problem in problems:
        print(f"  {problem}")
    if problems:
        print(f"check_retired_downloads: {len(problems)} fejl")
        return 1
    if not DIST.is_dir():
        print("check_retired_downloads: dist er ikke bygget — springer de dist-krævende kontroller")
        return 0
    print("check_retired_downloads: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
