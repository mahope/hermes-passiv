#!/usr/bin/env python3
"""Tallet i løfterne skal være målt, ikke husket.

Baggrund (opgave 84, 26. september 2026): tre iterationer i træk har rettet det
samme løfte på hver sin måde, og alle tre var forkert, fordi ingen målte motoren
rigtigt.

  - Opgave 80: den danske EUComply-tabel sagde 24 tjek, koden sagde 29.
  - Opgave 83: tællede `add('…')`-kaldene i `runScan()` og fandt **elleve**.
    Men motoren har også fire `findings.push({id:'…'})` uden `add()`, så den
    kører **15** regler. "11" blev skrevet på fire steder, heraf den dyreste
    købsside.
  - Opgave 84: de 15 `/guides/*`-sider sagde "16 automated rules" — også
    forkert, sandheden er 15.

Fejlen var ikke en skrivefejl. Den var, at **regeltallet aldrig blev defineret
et sted** — hver side gættede sit eget tal, og intet checkede det mod koden.
Denne fil gør opgaven umulig at gentage: den tæller reglerne i koden og fejler
på hvert løfte, der ikke matcher.

    python3 tools/check_rule_claims.py             # alle løfter mod målt kode
    python3 tools/check_rule_claims.py --list      # de målte tal, med kilde
    python3 tools/check_rule_claims.py --self-test # beviser at porten kan rødme
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Fri regel = `add('ID'` **eller** en `findings.push({id:'ID'`. At tælle kun
# `add()` er præcis den fejl opgave 83 lavede.
RE_FREE_ID = re.compile(r"""add\('([A-Z_0-9]+)'|findings\.push\(\{\s*id:'([A-Z_0-9]+)'""")
RE_PRO_ID = re.compile(r"push\('([A-Z_0-9]+)'")
RE_ELSE_IF = re.compile(r"\belse\s+if\s*\(")

# Et løfte er et tal umiddelbart før en af disse. Kun disse former gater:
# opgaven er at holde *regel*-tal sande, ikke at tælle alle tal på en side.
RE_CLAIM = re.compile(
    r"(?P<n>\d+)\s+"
    r"(?:"
    r"automatiske\s+regler"           # 16 automatiske regler
    r"|automated\s+(?:WCAG\s+[\d.]+\s+AA\s+)?rules"   # 16 automated rules
    r"|automatiske\s+tjek"             # 11 automatiske tjek
    r"|automated\s+checks"             # 11 automated checks
    r"|automated\s+accessibility\s+rules"
    r"|WCAG-regler"                    # 16 WCAG-regler
    r"|accessibility\s+(?:rules|checks)"
    r"|WCAG\s+[\d.]+\s+AA\s+regler"
    r")",
    re.IGNORECASE,
)

# Et *totaltal* er fri + Pro. Det kendes ved to former: "33 checks in all" og
# den danske tabelrække "Alle 33 automatiske tjek", hvor fri-spalten er "—".
# Formerne lå adskilt, fordi linjen ofte rummer begge tal — "33 checks in all —
# the free 15 accessibility rules" — og et linje-vis tjek ville regne den frie
# 15 som om den også skulle være 33.
RE_TOTAL = re.compile(
    r"(?P<n>\d+)\s+(?:checks?|tjek)\s+(?:in\s+all|i\s+alt)"
    r"|Alle\s+(?P<n2>\d+)\s+automatiske\s+tjek",
    re.IGNORECASE,
)

# Hvor `reportProFindings()` slutter i `_worker.js`. Findes ved at læse til den
# næste topniveau-funktion, så en ny push til sidst i funktionen tælles med.
PRO_FN = "function reportProFindings("


@dataclass(frozen=True)
class Layout:
    """Hvor motorerne ligger i et givet checkout."""

    site: Path

    @property
    def worker(self) -> Path:
        return self.site / "_worker.js"

    @property
    def engines(self) -> tuple[Path, ...]:
        return (self.site / "scan.html", self.site / "scan-da.html",
                self.site / "compliance-report.html")

    @property
    def primary(self) -> Path:
        return self.site / "scan.html"

    @property
    def excluded(self) -> dict[Path, str]:
        return {
            self.site / "wordpress-plugin.html":
                "motoren ligger i ../auditedwp (dette repo ejer den ikke)",
        }

    def rel(self, path: Path) -> str:
        return str(path.relative_to(self.site.parent))


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def free_rule_ids(path: Path) -> tuple[str, ...]:
    """Alle frie regel-id'er i én motor, i den rækkefølge de står.

    Et id der kun kan fyre i en `else if`-gren af samme betingelse er **ikke** en
    egen regel, men et andet udfald af den samme. `HTML_LANG_SHORT` kan aldrig
    fyre sammen med `HTML_LANG`, så de to medregnes som én — ellers målte
    `compliance-report.html` 16, mens motoren faktisk kører 15.
    """
    seen: list[str] = []
    for line in _read(path).splitlines():
        if RE_ELSE_IF.search(line):
            continue
        for m in RE_FREE_ID.finditer(line):
            rid = m.group(1) or m.group(2)
            if rid not in seen:
                seen.append(rid)
    return tuple(seen)


def pro_rule_ids(worker: Path) -> tuple[str, ...]:
    """Id'erne i `reportProFindings()` — de betalte checks."""
    src = _read(worker)
    start = src.find(PRO_FN)
    if start < 0:
        return ()
    rest = src[start + len(PRO_FN):]
    nxt = re.search(r"^(?:async )?function ", rest, re.MULTILINE)
    body = rest[: nxt.start()] if nxt else rest
    seen: list[str] = []
    for m in RE_PRO_ID.finditer(body):
        if m.group(1) not in seen:
            seen.append(m.group(1))
    return tuple(seen)


def engine_for(path: Path, lay: Layout) -> Path:
    """Hvilken motor et løfte på denne side henviser til."""
    return path if path in lay.engines else lay.primary


def collect(lay: Layout) -> list[tuple[Path, int, int, bool]]:
    """Alle regel-løfter som `(fil, linje, tal, er_total)`."""
    claims: list[tuple[Path, int, int, bool]] = []
    for path in sorted(lay.site.rglob("*.html")):
        if path in lay.excluded:
            continue
        for i, line in enumerate(_read(path).splitlines(), 1):
            # Totaltallene tages først og klippes væk, så det frie tal i samme
            # linje ("33 checks in all — the free 15 …") stadig måles som frit.
            rest, spans = line, []
            for m in RE_TOTAL.finditer(line):
                total = m.group("n") or m.group("n2")
                if total is not None:
                    claims.append((path, i, int(total), True))
                spans.append(m.span())
            for start, end in reversed(spans):
                rest = rest[:start] + " " * (end - start) + rest[end:]
            for m in RE_CLAIM.finditer(rest):
                claims.append((path, i, int(m.group("n")), False))
    return claims


def check(lay: Layout) -> list[str]:
    """Fejlmeldinger for alle løfter der ikke matcher den målte kode."""
    free = {p: len(free_rule_ids(p)) for p in lay.engines}
    pro = len(pro_rule_ids(lay.worker))
    errs: list[str] = []
    for path, line_no, claimed, is_total in collect(lay):
        expected = free[engine_for(path, lay)] + (pro if is_total else 0)
        if claimed != expected:
            kind = "Pro-total" if is_total else "frie regler"
            errs.append(f"{lay.rel(path)}:{line_no}: {kind} løfter {claimed}, "
                        f"koden kører {expected}")
    # Fund skal kunne få en fix-tekst. Kun de to frie motorer renderer FIX i
    # browseren; `compliance-report.html` bruger FIXES og dækkes af porten her.
    for p in (lay.site / "scan.html", lay.site / "scan-da.html"):
        errs.extend(findings_without_fix(p))
    return errs


def show_list(lay: Layout) -> str:
    free_n = len(free_rule_ids(lay.primary))
    pro_n = len(pro_rule_ids(lay.worker))
    lines = ["Målte regeltal (kilden er koden, ikke en note):", ""]
    for p in lay.engines:
        ids = free_rule_ids(p)
        lines.append(f"  {lay.rel(p)}: {len(ids)} regler")
        lines.append(f"    {', '.join(ids)}")
    pro = pro_rule_ids(lay.worker)
    lines += ["", f"  site/_worker.js reportProFindings(): {len(pro)} betalte checks",
              f"    {', '.join(pro)}", "",
              f"  Pro-total = {free_n} + {len(pro)} = {free_n + len(pro)}"]
    for p, why in lay.excluded.items():
        lines += ["", f"  UDEHOLDT: {lay.rel(p)} — {why}"]
    return "\n".join(lines)


def pro_count(lay: Layout) -> int:
    return len(pro_rule_ids(lay.worker))


RE_FIX_KEY = re.compile(r"^\s{4}([A-Z_0-9]+):'", re.MULTILINE)
RE_PUSH_ANY = re.compile(
    r"""add\('([A-Z_0-9]+)'|findings\.push\(\{\s*id:'([A-Z_0-9]+)'"""
)


def findings_without_fix(path: Path) -> list[str]:
    """Fund der skubbes uden id, eller med et id `FIX` ikke kender.

    Opgave 84 fandt fire af slagsen på `site/scan.html` og `site/scan-da.html`:
    de skubbede `findings.push({sev,msg})` uden id, så renderingen
    `FIX[f.id] || ''` gav en tom linje. Brugeren fik altså besked på fire af de
    femten problemer — inkl. *manglende `<title>`* og *manglende viewport* —
    uden at få sagt hvad der skulle gøres. Samme fejlform kan ikke komme igen:
    et fund skal have en id, og id'en skal have en fix-tekst.
    """
    src = _read(path)
    fixes = set(RE_FIX_KEY.findall(src))
    bad: list[str] = []
    for i, line in enumerate(src.splitlines(), 1):
        if "const add=" in line:      # definitionen af hjælperen, ikke et fund
            continue
        if re.search(r"else\s+if\s*\(", line):
            continue                 # andet udfald af samme regel, egen nøgle
        for m in RE_PUSH_ANY.finditer(line):
            rid = m.group(1) or m.group(2)
            if rid is None:
                bad.append(f"{path.name}:{i}: fund uden id — FIX[f.id] bliver tom")
            elif rid not in fixes:
                bad.append(f"{path.name}:{i}: id {rid} har ingen fix-tekst i FIX")
    return bad


def self_test() -> int:
    """Bevis at porten rødmER på et forkert tal, og er grøn på det rigtige."""
    fails: list[str] = []
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td) / "repo"
        shutil.copytree(ROOT, tmp, ignore=shutil.ignore_patterns(
            ".git", "dist", "node_modules", "__pycache__", ".wrangler"))
        lay = Layout(site=tmp / "site")

        base = check(lay)
        if base:
            fails.append(f"selftest: fersk checkout har allerede {len(base)} fejl:\n  "
                         + "\n  ".join(base[:5]))
            print("\n".join(fails))
            return 1

        real = len(free_rule_ids(lay.primary))

        def first_claim(path: Path, rx: re.Pattern[str]) -> str | None:
            """Det første løftet af den form i filen, læst live."""
            m = rx.search(path.read_text(encoding="utf-8"))
            return m.group(0) if m else None

        # Hver mutation skal flytte præcis ét løfte i en fil porten ejer. Tallene
        # læses live, så selftesten ikke går i stykker når regelsættet ændrer sig.
        cases = []
        guide = tmp / "site" / "guides" / "comparison.html"
        here = first_claim(guide, re.compile(r"\d+(?=\s+automated\s+rules)"))
        if here:
            cases.append(("guidespejl", guide, here, f"{real + 1} automated rules"))
        buy = tmp / "site" / "compliance-report.html"
        there = first_claim(buy, re.compile(r"\d+(?=\s+automated\s+checks)"))
        if there:
            cases.append(("købsside", buy, there, f"{real - 1} automated checks"))
        da = tmp / "site" / "da" / "compliance-report.html"
        total = first_claim(da, re.compile(r"\d+(?=\s+tjek\s+i\s+alt)"))
        if total:
            wrong = real + pro_count(lay) + 1
            cases.append(("dansk total", da, total, f"{wrong} tjek i alt"))

        if len(cases) != 3:
            fails.append(f"selftest: fandt {len(cases)}/3 løfter at mutere")

        for name, path, old, new in cases:
            original = path.read_text(encoding="utf-8")
            if old not in original:
                fails.append(f"selftest: mutationen {name!r} fandt ikke {old!r}")
                continue
            path.write_text(original.replace(old, new, 1), encoding="utf-8")
            if not check(lay):
                fails.append(f"selftest: mutationen {name!r} ({new!r}) gav ingen fejl")
            path.write_text(original, encoding="utf-8")

        # Den fjerde fejlform: et fund igen uden id, som på `main` gav fire fund
        # uden fix-tekst. Den skal give en fejl, ikke gå ubemærket.
        scan = lay.site / "scan.html"
        original = scan.read_text(encoding="utf-8")
        for name, old, new in (
            ("fund uden id", "{id:'VIEWPORT',sev:", "{sev:"),
            ("fix-tekst væk", "VIEWPORT:'Fix: add <meta name=\"viewport\"",
             "VIEWPORT_UNUSED:'Fix: add <meta name=\"viewport\""),
        ):
            if old not in original:
                fails.append(f"selftest: mutationen {name!r} fandt ikke {old!r}")
                continue
            scan.write_text(original.replace(old, new, 1), encoding="utf-8")
            if not check(lay):
                fails.append(f"selftest: mutationen {name!r} gav ingen fejl")
            scan.write_text(original, encoding="utf-8")

    for f in fails:
        print(f)
    if fails:
        return 1
    print(f"selftest OK: porten rødmer på et forkert tal og er grøn på det "
          f"rigtige ({real} regler)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--list", action="store_true", help="vis de målte tal")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        return self_test()
    lay = Layout(site=ROOT / "site")
    if args.list:
        print(show_list(lay))
        return 0

    errs = check(lay)
    if errs:
        print(f"check_rule_claims: {len(errs)} fejl — et løfte taler ikke om koden\n")
        for e in errs:
            print("  " + e)
        return 1
    n = len(collect(lay))
    free_n = len(free_rule_ids(lay.primary))
    pro_n = len(pro_rule_ids(lay.worker))
    print(f"check_rule_claims OK: {n} regel-løfter, alle matcher koden "
          f"({free_n} frie + {pro_n} Pro = {free_n + pro_n})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
