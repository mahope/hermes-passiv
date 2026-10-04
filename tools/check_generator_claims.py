#!/usr/bin/env python3
"""Gate fetch-denial claims in FAQ *generators*, judged against the route they write to.

**The blind spot this closes.** `check_storage_claims.py` judges published pages
by reading their own `fetch()` calls, and its docstring says plainly what it
cannot do:

    En side der *beskriver* et værktøj uden at kalde det — f.eks. en
    blogartikel der siger "nothing is stored" om scanneren — kan ikke dømmes
    herfra, fordi porten læser `fetch`-kald, ikke links. […] En fremtidig
    artikel med samme fejl er derfor stadig ubemandet.

The three FAQ generators in `tools/` are exactly that case. They write FAQ text
**about** a tool into that tool's page, and they never call it, so every gate
that reads `site/` judges the sentence without the evidence that convicts it.
`iter465_tool_faqs.py` was fixed on 30/9 only because a human read it — the
regression path the plan called out ("a new lie in a new generator gets out
through the gates") was wide open, and re-running one generator would have
put `/url-to-markdown`'s "nothing is sent to a server" lie straight back.

**Why a blanket forbidden-list would be wrong.** Measuring every `tools/*.py`
against the 30 forbidden phrases in `check_product_copy.py` returns **8** files
— and **all 8 are true claims**. `iter464`'s "Conversion runs entirely in your
browser — nothing leaves your device" is about `case-converter`, which is
genuinely client-side. A gate that forbids the sentence would have been red on
day one and taught everyone to disable it. The sentence is only a lie *on a
route that phones home*, so the sentence cannot be judged alone.

**What it judges, per FAQ entry:**

1. The answer contains a denial — "nothing is sent to a server", "runs
   entirely in your browser", "nothing leaves your device" (EN + DA).
2. The page that entry will be written to calls a route `site/_worker.js`
   reads `?url=` from and fetches server-side.

Both halves are measured, neither is a name list. The fetching routes come
from `check_storage_claims.fetching_routes()`, which reads the worker's own
dispatch and handler bodies. A page's phone-home comes from its own `fetch()`.
Adding a new scanning route or a new generator therefore needs no edit here.

**Coverage is detected, not listed.** A generator is found by its *shape*: a
dict whose keys are page slugs and whose values are lists of (question,
answer) string pairs. Measured 30/9: **3** of 136 `tools/*.py` match, all
three are FAQ generators, and all 19 of their slugs resolve to a real file in
`site/`. Zero false positives — the detector keys on data, not on names.

    python3 tools/check_generator_claims.py
    python3 tools/check_generator_claims.py --self-test
"""
from __future__ import annotations

import argparse
import ast
import importlib.util
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
TOOLS = ROOT / "tools"

# Den fil selvtesten muterer. Kun læst — mutationerne lægges over i
# hukommelsen, så porten aldrig skriver i repoet. Se `source_for`.
VICTIM = TOOLS / "iter465_tool_faqs.py"


def _load_storage_claims():
    """`check_storage_claims` som et modul, så porten ikke dømmer to gange."""
    spec = importlib.util.spec_from_file_location(
        "_storage_claims", ROOT / "tools" / "check_storage_claims.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


csc = _load_storage_claims()

# The denial family, EN + DA. `RE_FETCH_DENIAL` is reused verbatim for the
# forms it already covers (the `/url-to-markdown` lie and its siblings); the
# extra four are the measured phrasings the three generators actually write.
RE_FETCH_DENIAL = csc.RE_FETCH_DENIAL
RE_EXTRA_DENIAL = re.compile(
    r"""(?P<claim>
        runs\ entirely\ (?:in|on)\ your\ (?:browser|machine|device|computer)
      | runs\ entirely\ client[-\s]?side
      | (?:foregår|sker|kører)\ helt\ i\ din\ browser
      | intet\ forlader\ din\ enhed
      | nothing\ (?:leaves|ever\ leaves)\ your\ (?:device|machine|computer)
      | intet\ sendes\ nogen\ steder
    )""",
    re.IGNORECASE | re.VERBOSE,
)


def denials(text: str) -> list[str]:
    """Alle afvisende hentnings-løfter i en tekst, i den rækkefølge de står."""
    found = [m.group("claim") for m in RE_FETCH_DENIAL.finditer(text)]
    found += [m.group("claim") for m in RE_EXTRA_DENIAL.finditer(text)]
    return found


def _string_literal(node: ast.AST) -> str | None:
    """En streng, også når den er limt sammen af `+` på tværs af linjer.

    Generatorerne skriver hver sætning som et par stykker, så en `ast.Constant`
    per stykke rammer aldrig hele løftet.
    """
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left = _string_literal(node.left)
        right = _string_literal(node.right)
        if left is None or right is None:
            return None
        return left + right
    return None


def faq_entries(source: str) -> list[tuple[str, list[tuple[str, str]]]]:
    """Alle (slug, (spørgsmål, svar)) i en generator, fundet på form.

    En dict hvis nøgler er sideslugs og hvis værdier er lister af
    (streng, streng). Vi leder efter *formen*, ikke efter navnet `FAQS`, så en
    ny generator der kalder den `FAQER` eller skriver den inline i `main()`
    bliver dømt uden at porten skal redigeres.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []
    entries: list[tuple[str, list[tuple[str, str]]]] = []
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Assign) and isinstance(node.value, ast.Dict)):
            continue
        for key, value in zip(node.value.keys, node.value.values):
            if key is None or not isinstance(value, ast.List) or not value.elts:
                continue
            slug = _string_literal(key)
            if slug is None or "/" in slug:
                continue
            pairs: list[tuple[str, str]] = []
            for element in value.elts:
                if not (isinstance(element, ast.Tuple) and len(element.elts) == 2):
                    break
                question = _string_literal(element.elts[0])
                answer = _string_literal(element.elts[1])
                if question is None or answer is None:
                    break
                pairs.append((question, answer))
            else:
                if pairs:
                    entries.append((slug, pairs))
    return entries


def page_for_slug(slug: str) -> str | None:
    """`color-blindness-simulator` → `color-blindness-simulator.html`.

    Generatorerne skriver slugs både med og uden endelsen; målt er 19 slugs, alle
    findes i `site/` med den ene eller den anden form.
    """
    name = slug if slug.endswith(".html") else slug + ".html"
    return name if (SITE / name).is_file() else None


def generators(overrides: dict[str, str] | None = None) -> list[Path]:
    """Alle `tools/*.py` med en FAQ-formet dict.

    `overrides` erstatter en fils indhold *i hukommelsen*, uden at røre den.
    Det er hele pointen med mutationerne i `self_test()`: se `source_for`.
    """
    overrides = overrides or {}
    found = []
    for path in sorted(TOOLS.glob("*.py")):
        source = source_for(path, overrides)
        try:
            ast.parse(source)
        except SyntaxError:
            continue
        if faq_entries(source):
            found.append(path)
    return found


def source_for(path: Path, overrides: dict[str, str]) -> str:
    """Kildefilen for `path`, eller mutationen der er lagt over den.

    Selvtesten skriver aldrig en mutation til disk. Det er ikke en
    optimering — det er den fejl, porten selv fik: den 30/9-gode mutation
    skrev sit eget anonyme stub ind i `tools/iter465_tool_faqs.py`, og da
    processen blev dræbt mellem skrivning og gendannelse (`finally`), lå
    stubben i repoet og blev squaset ind i `6783c64`. Den holdt netop den
    løgn, porten findes for at dømme, så CI gik rød på `main` to gange.
    """
    if path.name in overrides:
        return overrides[path.name]
    return path.read_text(encoding="utf-8", errors="replace")


def collect_problems(routes: dict[str, str], pages: dict[str, str],
                     overrides: dict[str, str] | None = None) -> list[str]:
    overrides = overrides or {}
    problems: list[str] = []
    judged = 0
    for path in generators(overrides):
        source = source_for(path, overrides)
        for slug, pairs in faq_entries(source):
            page = page_for_slug(slug)
            if page is None:
                problems.append(
                    f"{path.name}: FAQ slug {slug!r} resolves to no file in site/ — "
                    "the generator would write nothing, or write the wrong page")
                continue
            called = sorted({m.group(1) for m in csc.RE_FETCH.finditer(pages[page])}
                            & set(routes))
            if not called:
                continue
            judged += 1
            for question, answer in pairs:
                for claim in denials(answer):
                    problems.append(
                        f"{path.name}: {slug} answers {question!r} with the denial "
                        f"{claim.strip()!r}, but that page fetches {', '.join(called)} "
                        "server-side")
    print(f"{len(generators())} generator(er), "
          f"{judged} FAQ-blok(er) på ruter der henter server-side — alle dømt mod sidernes egne fetch-kald")
    return problems


def self_test() -> int:
    """Bevis at porten fanger fejlformen, og at den lader sande løfter være.

    Scenarierne bygges af de *rigtige* generatorer og de *rigtige* sider. En
    fejlform der kun findes i en streng porten selv har fundet, er ingen
    fejlform.
    """
    routes = csc.fetching_routes()
    pages = csc.site_pages()
    failures = 0

    routes = csc.fetching_routes()
    pages = csc.site_pages()
    failures = 0

    def check(source: str, label: str, expect_problems: bool = True) -> list[str]:
        """Dommutationen *uden* at røre disken.

        Før 4/10 skrev denne `tools/iter465_tool_faqs.py` og gendannede den i
        en `finally`. Gaten kørte 66 selvtests, og en dræbt proces mellem
        skrivning og gendannelse efterlod mutationen i repoet — som
        `6783c64`. Den holdt netop den løgn, porten findes for at dømme,
        så CI gik rød på `main` to gange.

        `expect_problems=False` dømmer et *kontrol*-scenarie, der skal tie.
        Uden flaget ville det skrive `FAIL` på en grøn linje, fordi
        udskriftslogikken antager at fund er det gode.
        """
        problems = collect_problems(routes, pages, {VICTIM.name: source})
        caught = bool(problems) if expect_problems else not problems
        print(f"{'ok  ' if caught else 'FAIL'} {label}: "
              f"{problems or 'no problem found'}")
        return problems

    real = VICTIM.read_text(encoding="utf-8")

    # 1. Uden mutation: de rigtige generatorer er grønne.
    baseline = collect_problems(routes, pages)
    print(f"{'ok  ' if not baseline else 'FAIL'} baseline: the three real generators are clean")
    failures += 1 if baseline else 0

    # 2. Den mutation der fører tilbage til fundet: `/url-to-markdown` siger
    #    igen at intet sendes, selv om siden henter gennem `/scan-proxy`.
    anchor = "'Yes — the URL is sent to our server, which fetches the page for you. That is what gets '"
    if anchor not in real:
        print("FAIL mutation anchor not found in iter465_tool_faqs.py")
        failures += 1
    else:
        broken = real.replace(anchor, "'Nothing is sent to a server. '", 1)
        problems = check(broken, "mutation: url-to-markdown denies the server fetch")
        failures += 0 if any("url-to-markdown" in p for p in problems) else 1

    # 3. Den mutation der kun er sand fordi siden er klient-side: samme
    #    afvisning på `case-converter`, som *ikke* henter. Porten skal tie.
    truthy = ("'Nej. Paletter beregnes lokalt i din browser med JavaScript — intet forlader din enhed.'")
    if truthy not in real:
        print("FAIL client-side anchor not found in iter465_tool_faqs.py")
        failures += 1
    else:
        mutated = real.replace(
            truthy,
            "'Nej. Intet sendes til en server.'", 1)
        problems = check(mutated, "control: a client-side page keeps its denial",
                         expect_problems=False)
        failures += 1 if any("palette-generator-da" in p for p in problems) else 0

    # 4. En løgn i en generator uden navnet i porten skal stadig dømmes, så
    #    beviset afhænger ikke af at porten kender filen.
    anonymous = ("#!/usr/bin/env python3\n"
                 "FAQS = {\n"
                 "'url-to-markdown': [\n"
                 " ('Er der en server?', 'Nej. Intet sendes til en server.'),\n"
                 "],\n"
                 "}\n")
    problems = check(anonymous,
                     "mutation: a generator the port never names is judged anyway")
    caught = [p for p in problems if "url-to-markdown" in p]
    failures += 0 if caught else 1

    print("self-test: " + ("grøn" if failures == 0 else f"{failures} fejl"))
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return 1 if self_test() else 0
    problems = collect_problems(csc.fetching_routes(), csc.site_pages())
    if problems:
        for problem in problems:
            print(f"FAIL {problem}")
        print(f"{len(problems)} generator-løfte(r) modbevist af sidens egen hentning")
        return 1
    if not args.quiet:
        print("GRØN: intet FAQ-løfte i nogen generator modsiger den rute det skrives til")
    return 0


if __name__ == "__main__":
    sys.exit(main())