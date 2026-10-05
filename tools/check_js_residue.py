#!/usr/bin/env python3
"""Døm rester efter scriptede erstatninger i JavaScript (opgave 25).

Punkt 13 i ren kultur siger: `git diff | grep -nE '^\\+.*\\$[0-9]'` efter enhver
sed/perl/regex-indsættelse. Det fanger `$1` — men **ikke** `;;`.

Målt 6/10: `git log -S` pegede på `97ef0b68`, som efterlod

    const CHECKOUT_SESSION_RE = /^cs_(?:live|test)_[A-Za-z0-9]{10,200}$/;;

på linje 119 i `site/_worker.js`. `;;` er en *tom sætning* i JavaScript, så
`node --check` er grøn, `tsc` er grøn, bygget er grønt, og `check_inline_js` er
grøn. Den eneste måde at se den på er at læse linjen.

Denne port dommer derfor **hele** JS-overfladen på de to rester, der er gyldige
syntaks og alligevel altid en fejl:

1. `;;` i kode (to tomme sætninger i træk). `for(;;)` er det eneste sted, hvor
   det er mening, og er undtaget — det er en tom betingelsesliste, ikke en
   rester.
2. En linje der **kun** består af `;` og mellemrum. Det er den anden halvdel
   af den samme fejl: en indsættelse der efterlod den afsluttende `;` på sin
   egen linje.

**Rester i strenge er data, ikke kode.** `site/clean-copy-bookmarklet.js` er én
minificeret `javascript:`-streng på én linje, og den indeholder med vilje
`});;var` som en del af den kode, browseren skal køre. Porten masker derfor
kommentarer og streng- og regex-literaler før den dømmer, så den kan skelne
`"a;;b"` (data) fra `f();;` (rest). Uden maskeringen ville porten være rød på
første kørsel, og en rød port man frøs slås fra — så maskeringen er ikke kosmetik,
den er selve pointen.

Brug:
    python3 tools/check_js_residue.py
    python3 tools/check_js_residue.py --self-test
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
DIST = ROOT / "dist"

# Ét regex pr. tråd, en tråd pr. cpu'erne der er. Kun maskeringsarbejdet er
# dyrt; resten er små greb.
WORKERS = 8

RE_SCRIPT = re.compile(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", re.S | re.I)
RE_LD_JSON = re.compile(r"application/ld\+json", re.I)
RE_IMPORTMAP = re.compile(r"""<script[^>]*type=["']importmap["']""", re.I)

# `for(;;)` og `while(;;)`: to semikoloner er her * meningen, ikke en rester.
RE_EMPTY_HEADER = re.compile(r"\(\s*;;\s*\)")
RE_DOUBLE_SEMI = re.compile(r";;")
RE_SEMI_ONLY_LINE = re.compile(r"^[ \t]*;+[ \t]*$")

# `/` er regex-literal, ikke division, når det forrige tegn ikke kan slutte et
# udtryk. Listen er den samme som enhver minimal JS-scanner bruger; den skal
# kun være god nok til at `/a;;b/` ikke tælles som kode.
REGEX_AFTER_CHARS = set("(,=:[!&|?{};+-*%^~<>")
REGEX_AFTER_WORDS = {
    "return", "typeof", "instanceof", "in", "of", "new", "delete", "void",
    "case", "do", "else", "yield", "await", "throw",
}


def prev_ok_for_regex(out: list[str], i: int) -> bool:
    """Er `/` ved position `i` en regex-literal, eller er det division?

    Afgørende er det nærmeste ikke-mellemrum **inden i**. Maskeringen har
    allerede gjort strengindhold til mellemrum, så et tegn i `out` er kode.
    """
    k = i - 1
    while k >= 0 and out[k] in " \t":
        k -= 1
    if k < 0:
        return True  # kodens første tegn
    ch = out[k]
    if ch in REGEX_AFTER_CHARS:
        return True
    if ch.isalnum() or ch in "_$":
        j = k
        while j >= 0 and (out[j].isalnum() or out[j] in "_$"):
            j -= 1
        return "".join(out[j + 1:k + 1]) in REGEX_AFTER_WORDS
    return False


def mask_js(src: str) -> str:
    """Erstat kommentarer og streng- og regex-indhold med mellemrum.

    Positioner og linjeskift bevares, så et fund kan slås op på det rigtige
    sted i den oprindelige fil.

    Stakken er nødvendig, ikke pynt: en template-literal kan indeholde en
    `${ … }` der igen rummer en template-literal, som der er flere af i
    `site/_worker.js` (kvitterings-HT'en). En linjevis masker gik i stykker dér
    — målt: `state["template"]` stod stadig True ved EOF, så de sidste 160
    linjer af workeren blev dømt som data.
    """
    out = list(src)
    n = len(src)
    i = 0
    # Hver rude er enten "template" eller ("kode", klammedybde). Tom stak er
    # kode på øverste niveau.
    stack: list = []

    def blank(a: int, b: int | None = None) -> None:
        for k in range(max(a, 0), min(b if b is not None else a + 1, n)):
            if out[k] != "\n":
                out[k] = " "

    while i < n:
        in_template = bool(stack) and stack[-1][0] == "template"
        c = src[i]

        if in_template:
            if c == "\\":
                blank(i, i + 2)
                i += 2
                continue
            if c == "`":
                blank(i)
                stack.pop()
                i += 1
                continue
            if c == "$" and src[i + 1:i + 2] == "{":
                stack.append(["kode", 0])
                i += 2
                continue
            blank(i)
            i += 1
            continue

        if c == "/" and src[i + 1:i + 2] == "/":
            j = src.find("\n", i)
            blank(i, n if j < 0 else j)
            i = n if j < 0 else j
            continue

        if c == "/" and src[i + 1:i + 2] == "*":
            j = src.find("*/", i + 2)
            blank(i, n if j < 0 else j + 2)
            i = n if j < 0 else j + 2
            continue

        if c in "\"'":
            j = i + 1
            while j < n:
                if src[j] == "\\":
                    j += 2
                    continue
                if src[j] == c:
                    j += 1
                    break
                if src[j] == "\n":
                    break  # uafsluttet streng: stop ved linjeskiftet
                j += 1
            blank(i, j)
            i = j
            continue

        if c == "`":
            blank(i)
            stack.append(["template", 0])
            i += 1
            continue

        if c == "/" and prev_ok_for_regex(out, i):
            j = i + 1
            in_class = False
            closed = False
            while j < n:
                if src[j] == "\\":
                    j += 2
                    continue
                if src[j] == "[":
                    in_class = True
                elif src[j] == "]":
                    in_class = False
                elif src[j] == "/" and not in_class:
                    j += 1
                    closed = True
                    break
                elif src[j] == "\n":
                    break
                j += 1
            if closed:
                while j < n and src[j].isalpha():
                    j += 1  # flags
                blank(i, j)
                i = j
                continue

        if c == "{":
            if stack:
                stack[-1][1] += 1
        elif c == "}":
            if stack and stack[-1][0] == "kode" and stack[-1][1] == 0:
                # Den afsluttende klamme i en `${ … }`. Den er tegn i
                # interpolationen, ikke i strengen, så den dømmes som kode.
                blank(i)
                stack.pop()
            elif stack and stack[-1][0] == "kode":
                stack[-1][1] -= 1

        i += 1

    return "".join(out)


def judge_js(label: str, code: str, line_offset: int = 0) -> list[str]:
    """Fund i én kodeenhed. `label` er `fil:linje` for kundefejl."""
    masked = mask_js(code)
    masked = RE_EMPTY_HEADER.sub(
        lambda m: " " * len(m.group(0)), masked)
    found: list[str] = []
    for m in RE_DOUBLE_SEMI.finditer(masked):
        found.append(f"{label}:{line_offset + masked[:m.start()].count(chr(10)) + 1}"
                     f"  dobbelt `;;` (tom sætning)")
    # Maskeringen lokalerer, den rå tekst bekræfter. Uden bekræftelsen dømmer
    # porten en flerlinjes template-literal, der *slutter* med `;`: maskingen
    # gør hele strengens indhold til mellemrum, så den afsluttende linje ender
    # som `        ;` — kode der ser ud som en rest, men er en `;` efter en
    # afsluttet streng. Det er det almindelige mønster i denne kode (se
    # systemPrompt i `site/_worker.js`), så uden bekræftelsen er porten rød på
    # levende kode fra første kørsel.
    raw_lines = code.split("\n")
    for idx, line in enumerate(masked.split("\n"), start=1):
        raw = raw_lines[idx - 1] if idx - 1 < len(raw_lines) else ""
        if RE_SEMI_ONLY_LINE.match(line) and RE_SEMI_ONLY_LINE.match(raw):
            found.append(f"{label}:{line_offset + idx}"
                         f"  linje der kun er `;`")
    return found


def script_blocks(html: str) -> list[tuple[int, str]]:
    """(1-baseret linje, kode) for hver inline-script-blok der er JavaScript."""
    out = []
    for m in RE_SCRIPT.finditer(html):
        body = m.group(1)
        if not body.strip():
            continue
        head = html[m.start():m.start() + 160]
        if RE_LD_JSON.search(head) or RE_IMPORTMAP.search(head):
            continue
        out.append((html[:m.start(1)].count("\n") + 1, body))
    return out


def js_sources(roots: list[Path]) -> list[tuple[str, str]]:
    """(label, kode) for hver JS-enhed under `roots`."""
    out: list[tuple[str, str]] = []
    for root in roots:
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*.js")):
            out.append((str(path.relative_to(ROOT)),
                        path.read_text(encoding="utf-8", errors="replace")))
        for path in sorted(root.rglob("*.html")):
            html = path.read_text(encoding="utf-8", errors="replace")
            rel = str(path.relative_to(ROOT))
            for lineno, code in script_blocks(html):
                out.append((f"{rel} (inline <script>)", f"\n" * (lineno - 1) + code))
    return out


def check(roots: list[Path]) -> tuple[list[str], int]:
    sources = js_sources(roots)
    found: list[str] = []
    if sources:
        with cf.ThreadPoolExecutor(max_workers=WORKERS) as pool:
            for part in pool.map(lambda s: judge_js(s[0], s[1]), sources):
                found.extend(part)
    return found, len(sources)


# --------------------------------------------------------------------------
# Selftest. Den skal være rød på den kode, der fejler — altså på de gamle
# regler. Derfor dømmer den både syntetiske tilfælde og *den rigtige fil* med
# den rigtige fejl indsat, som `97ef0b68` efterlod.
# --------------------------------------------------------------------------

MUTATION = "\n;;\nconst RESIDUE = /^(?:live|test)_[A-Za-z0-9]{10,200}$/;;\n;\n"


def self_test() -> int:
    fails: list[str] = []

    def eq(label: str, got: list[str], want: int) -> None:
        if len(got) != want:
            fails.append(f"{label}: forventede {want} fund, fik {len(got)}"
                         + (f" -> {got}" if got else ""))

    # 1. Syntetiske tilfælde. Rester er fund, kode og data er ikke.
    eq("rest midt i kode", judge_js("t", "f();;\ng();\n"), 1)
    eq("rest i statement-slutning", judge_js("t", "const r = /x/;;\n"), 1)
    eq("semikolonlinje", judge_js("t", "f();\n;\ng();\n"), 1)
    eq("tom linje er ikke en rest", judge_js("t", "f();\n\ng();\n"), 0)
    eq("for(;;) er mening", judge_js("t", "for (;;) { break; }\n"), 0)
    eq("while(;;) er mening", judge_js("t", "while (;;) { break; }\n"), 0)
    eq("streng er data", judge_js("t", 'const s = "a;;b";\n'), 0)
    eq("template er data", judge_js("t", "const s = `a;;b`;\n"), 0)
    eq("regex-literal er data", judge_js("t", "const r = /a;;b/;\n"), 0)
    eq("linjekommentar er data", judge_js("t", "f(); // ;;\n"), 0)
    eq("blokkommentar er data", judge_js("t", "f(); /* ;;\n;; */\ng();\n"), 0)
    eq("division er ikke regex", judge_js("t", "const r = a / b;;\n"), 1)
    # Regression fra portens egen udvikling: en template-literal med en
    # template-literal indeni (`${ … }`) fik maskeren til at tro den yderste
    # streng var åben ved EOF. Uden denne linje er fejlen usynlig igen.
    eq("template i template er data",
       judge_js("t", "html = `<p>${f(r, (n) => `<b>${esc(n)}</b>`)}</p>`;\n"
                 "const efter = 1;\n"), 0)

    # 2. Den rigtige fil. Læst fra disk, ikke kopieret, så mutationen rammer
    #    den kode der faktisk publiceres.
    #
    #    Fire fund er det rigtige tal, ikke tre: linjen `;;` alene bryder
    #    **begge** regler (dobbelt `;;` *og* en linje der kun er `;`), og det er
    #    ikke en fejl i porten — det er to sande fund på samme linje.
    worker = SITE / "_worker.js"
    if not worker.is_file():
        fails.append("site/_worker.js mangler — kan ikke dømme den rigtige fil")
    else:
        original = worker.read_text(encoding="utf-8")
        eq("site/_worker.js er ren", judge_js("worker", original), 0)
        mutated = judge_js("worker", original + MUTATION)
        if len(mutated) != 4:
            fails.append(
                "mutationen på site/_worker.js: forventede 4 fund "
                f"(;;, ;;, to på `;;`-linjen, semikolonlinje), fik {len(mutated)}"
                f" -> {mutated}")

    # 3. Maskeringen er ikke kosmetik. `site/clean-copy-bookmarklet.js` er én
    #    minificeret `javascript:`-streng, og den indeholder med vilje `});;var`
    #    som **data**. Uden maskeringen er porten rød på den første kørsel,
    #    og en port der er rød uden fejl bliver slået fra — så dette er det
    #    tilfælde der holder maskeringen i live.
    bookmarklet = SITE / "clean-copy-bookmarklet.js"
    if bookmarklet.is_file():
        raw = bookmarklet.read_text(encoding="utf-8")
        if ";;" not in raw:
            fails.append("bookmarklet'et indeholder ikke længere `;;` — "
                         "testet forventer en streng med to semikoloner i sig")
        eq("bookmarklets `};` er data", judge_js("bookmarklet", raw), 0)
    else:
        fails.append("site/clean-copy-bookmarklet.js mangler")

    # 4. Resten af overfladen skal være grøn, ellers er porten rød på kode
    #    der ikke fejler. Det er samme kontrol som `check()` laver, men kun på
    #    kilden, så selftesten ikke er afhængig af et bygget `dist/`.
    found, judged = check([SITE])
    if found:
        fails.append(f"{len(found)} fund i site/ — porten er rød på ren kode: "
                     + "; ".join(found[:3]))

    if fails:
        print("self-test: {} fejl".format(len(fails)), file=sys.stderr)
        for f in fails:
            print("  " + f, file=sys.stderr)
        return 1
    print("self-test: 0 fejl")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        return self_test()

    found, judged = check([SITE, DIST])
    for f in found:
        print(f)
    print(f"check_js_residue: {len(found)} fund i {judged} JS-enheder")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())