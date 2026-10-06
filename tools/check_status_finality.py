#!/usr/bin/env python3
"""Dom at 429 er endeligt i browseren, og at den siger hvornår man kommer tilbage.

Baggrund (målt 1. oktober 2026). CEO-kø punkt 0 sagde den 29. september:
*429 er endelig, ikke forbigående* — vis serverens besked. Syv klienter blev
rettet den dag, og `site/net.js` fik en hel kommentar om hvorfor:

    Retrying it was also what made the AI quota look full: three client
    retries on one question burned three of the twenty daily slots before any
    answer came back.

Den tiende klient blev ikke med, fordi opgaven bad om *de syv filer der stod i
køen*, og `site/thanks.html` stod ikke i den. Målt på den:

    if (x.code === 429 || x.code >= 500) return again('We are having trouble
        loading your order — trying again…', 4000, false);

To ting er forkert i den ene linje. `/api/stripe/fulfillment` tæller selv
forsøg (`if (hits >= 30) … 429`, workeren linje 3933), så hvert af de tolv
genkald tæller i den tæller der gav 429 — den der ventede længst fik *færrest*
forsøg tilbage. Og serverens egen sætning ("Too many attempts. Try again
later.") blev kastet bort til fordel for en streng der siger "trying again", som
ikke fortælder kunden *hvornår* der er grund til at komme tilbage.

Det er ikke en skrivefejl. Det er samme fejl igen som de ni andre porte i
`site/`: **en regel der er skrevet ned, men ingen dom.** `check_inline_js`
fandt de otte døde generatorer fordi den *kunne* se den publicerede fil.
`check_heading_levels` så et spring og sagde intet om en ledsagende CSS-regel.
Her står reglen i `net.js`'s egen kommentar, og intet sted spørger om
`thanks.html` følger den.

**Hvad porten dømmer.** For hvert 429-sammenligningspunkt i `site/`:

1. **429 må ikke føre til et nyt kald.** Ikke «kalder den samme funktion igen»,
   og ikke «kalder en hjælpefunktion, der kalder den igen» — den transitive
   variant er præcis fejlen, fordi `again()` i `thanks.html` ikke selv
   genkalder `fetch`.
2. **429 skal sige hvornår man kommer tilbage.** Enten serverens egen sætning
   eller et tidspunkt. «We are having trouble — trying again» er hverken: det
   er en undskyldning, ikke en oplysning.
3. **5xx skal blive forbigående.** Uden den tredje dom kan de to første
   opfyldes ved at gøre *alt* endeligt, og det er den modsatte rettelse: en
   kunde der betalte for EUComply Pro må ikke låses ude af ét KV-blip.

**Hvilke filer.** Målt, ikke en navneliste. Enhver fil under `site/` der
*sammenligner* med 429, minus de filer der *frembringer* en 429 — dem er der
serven, ikke klienten, og de skal ikke dømmes på klientens regler. Kommentarer
er fjernet før der læses, så `book-ai.js`'s henvisning til `net.js` ikke læses
som en kodevej. Målt 1/10 på korpus: **3** klienter (`thanks.html`,
`compliance-report.html`, `net.js`), **2** servere (`_worker.js`,
`worker-bugbottle-demo.js`). De 3 mutationer i `mutationer` er alle fundet i
koden.

**Det porten ikke kan se.** Den læser statisk kode og kan ikke vide om en
server faktisk returnerer 429 lige nu; den bruger derfor *kun* de filer der
selv sammenligner med 429, så den kan ikke gå rød på en klient der endnu ikke
har haft et 429-problem. Det er ærligt og skal stå her, fordi det er den
begrænsning en ny klient rammer først.

    python3 tools/check_status_finality.py
    python3 tools/check_status_finality.py --self-test
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"

SCRIPT_RE = re.compile(r"<script\b[^>]*>(.*?)</script>", re.S | re.I)

# 429 som *sammenligning*, ikke som en del af et decimaltal. Uden ordgrænsen
# rammer porten `0.042940` i `color-blindness-simulator.html` to gange.
RE_429_TEST = re.compile(r"(?<![\w.])429(?![\w])")

# En fil der *frembringer* 429 er serven. Den må dømmes på andres regler.
RE_PRODUCES = re.compile(r"(?:status\s*:\s*429|\}\s*,\s*429\s*\)|,\s*429\s*;|\b429\s*,\s*headers)")

# Funktioner kaldes på tre måder i denne kode: `function navn(`,
# `async function navn(` og `navn: function (` / `navn = function (`.
RE_FUNCTION = re.compile(
    r"(?:^|[\s;{}])(?:async\s+)?function\s+([A-Za-z_$][\w$]*)\s*\("
)
RE_ARROW_FN = re.compile(
    r"(?:^|[\s;{(,=])(?:const|let|var)?\s*([A-Za-z_$][\w$]*)\s*=\s*"
    r"(?:async\s*)?(?:function\s*)?\([^)]*\)\s*=>"
)
RE_FETCH = re.compile(r"\bfetch\s*\(")
RE_CALL = re.compile(r"(?<![\w.$])([A-Za-z_$][\w$]*)\s*\(")
RE_IDENTIFIER = re.compile(r"(?<![\w.$#])([A-Za-z_$][\w$]*)")

# En tidspunktangivelse. Ordene er dem der faktisk står i de tre klienters
# 429-tekster, så listen er ikke en sproglig pænhed: uden dem ville
# `compliance-report.html` være rød på en tekst der *er* handling.
RE_WHEN = re.compile(
    r"\b(?:hour|hours|minute|minutes|day|tomorrow|midnight|later|shortly|"
    r"igen|time\b|senere|i morgen|time kl)\b",
    re.I,
)
# Serverens egen sætning: et `.error`-felt på det parsede svar.
RE_SERVER_ERROR = re.compile(r"\.error\b")


def strip_js_comments(text: str) -> str:
    """Fjern `//` og `/* */`, og spring strenge og regex-literaler over.

    Uden dette læses `net.js`'s egen forklaring — der *er* reglen — som en
    kodevej, og `book-ai.js`'s "// 429 er endeligt: se /net.js" som en dømning.

    Regex-literalerne skal med, ellers åbner `replace(/[&<>"]/g, …)` et
    uafsluttet streng og resten af filen læses som tekst.
    """
    out: list[str] = []
    i, n = 0, len(text)
    quote: str | None = None
    last = "\n"  # sidste tegn der ikke er mellemrum — til regex-genkendelse
    while i < n:
        ch = text[i]
        if quote:
            out.append(ch)
            if ch == "\\" and i + 1 < n:
                out.append(text[i + 1])
                i += 2
                continue
            if ch == quote:
                quote = None
            i += 1
            continue
        if ch in "'\"`":
            quote = ch
            out.append(ch)
            i += 1
            continue
        if ch == "/" and i + 1 < n and text[i + 1] == "/":
            while i < n and text[i] != "\n":
                i += 1
            continue
        if ch == "/" and i + 1 < n and text[i + 1] == "*":
            end = text.find("*/", i + 2)
            i = n if end < 0 else end + 2
            continue
        if ch == "/" and _regex_can_start_here(last):
            out.append(ch)
            last = "/"
            i += 1
            while i < n:
                out.append(text[i])
                if text[i] == "\\":
                    if i + 1 < n:
                        out.append(text[i + 1])
                    i += 2
                    continue
                if text[i] == "\n":  # et regex literals linjeskift er en fejl
                    break
                if text[i] == "/":
                    i += 1
                    break
                i += 1
            continue
        out.append(ch)
        if not ch.isspace():
            last = ch
        i += 1
    return "".join(out)


# Tegnene der kan stå lige før et regex-literal (og aldrig efter et tal, så
# `a / b / c` ikke læses som regex). Målet er at genkende *de* former der
# står i `site/`, ikke at være en JavaScript-parser.
_REGEX_PRECEDERS = set("(,=:[!&|?{};+-*%~^<>")


def _regex_can_start_here(last: str) -> bool:
    return last in _REGEX_PRECEDERS


def client_sources() -> dict[str, str]:
    """Alle klient-Kilder i `site/`: `.js` og inline-`<script>`, kommentarfri."""
    sources: dict[str, str] = {}
    for path in sorted(SITE.rglob("*.js")):
        sources[str(path.relative_to(ROOT))] = strip_js_comments(
            path.read_text(encoding="utf-8", errors="replace")
        )
    for path in sorted(SITE.rglob("*.html")):
        relative = str(path.relative_to(ROOT))
        for index, block in enumerate(SCRIPT_RE.findall(path.read_text(
                encoding="utf-8", errors="replace")), start=1):
            if not block.strip():
                continue
            sources[f"{relative}#script-{index}"] = strip_js_comments(block)
    return sources


def producing_429_routes() -> dict[str, str]:
    """Ruter hvis handler *kan* svare 429, målt i `site/_worker.js`.

    Målt, ikke håndskrevet: en ny `rateLimitIp`-sletning i en eksisterende
    handler gør den rute 429-Producer uden at nogen redigerer her.
    """
    worker = (SITE / "_worker.js").read_text(encoding="utf-8", errors="replace")
    handlers = _function_ranges(worker)
    produces: set[str] = set()
    for name, _start, body in handlers:
        if RE_PRODUCES.search(body):
            produces.add(name)
    routes: dict[str, str] = {}
    for match in RE_DISPATCH.finditer(worker):
        grupper = [g for g in match.groups() if g]
        if len(grupper) != 2:
            continue
        route, handler = grupper
        if handler in produces:
            routes[route] = handler
    return routes


RE_DISPATCH = re.compile(
    r"if\s*\(\s*path\.startsWith\(\s*['\"]([^'\"]+)['\"]\s*\)\s*\)\s*return\s+([A-Za-z_$][\w$]*)\s*\("
    r"|if\s*\(\s*path\s*===\s*['\"]([^'\"]+)['\"]\s*\)\s*return\s+([A-Za-z_$][\w$]*)\s*\("
)


def _function_ranges(text: str) -> list[tuple[str, int, str]]:
    """(navn, start, krop) for hver topniveau-funktion, matched på klammer."""
    starts: list[tuple[str, int]] = []
    for regex in (RE_FUNCTION, RE_ARROW_FN):
        for match in regex.finditer(text):
            starts.append((match.group(1), match.start()))
    starts.sort(key=lambda item: item[1])
    ranges: list[tuple[str, int, str]] = []
    for name, begin in starts:
        brace = text.find("{", begin)
        if brace < 0:
            continue
        depth, i = 0, brace
        while i < len(text):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    break
            i += 1
        ranges.append((name, begin, text[brace:i + 1]))
    return ranges


def enclosing_function(text: str, offset: int) -> tuple[str, str] | None:
    """Den inderste funktion hvis krop `offset` ligger i, eller None."""
    best: tuple[str, str] | None = None
    for name, _begin, body in _function_ranges(text):
        begin = text.find(body)
        if begin < 0:
            continue
        if begin <= offset <= begin + len(body):
            if best is None or len(body) < len(best[1]):
                best = (name, body)
    return best


def branch_body(text: str, offset: int) -> str:
    """Den kode der faktisk udføres, når 429-testen er sand.

    To former, fordi de to klientformer er to:

    * **Betingelse** — `if (…) return …;` eller `if (…) { … }`. Kroppen er
      den `{…}` eller den klammeløse sætning.
    * **Tildeling** — `err.limited = res.status === 429;`. Her *afgør* 429-testen
      ikke en gren, den sætter et flag, og det er flagets hele `then`-gren i
      den omgivende blok der er svaret. Det er derfor `net.js` er grøn: der
      ligger `data.error` i samme blok.

    Uden skelningsformen læses `err.limited = res.status === 429;` som kroppen
    `429;`, og porten ville være rød på den mest korrekte klient i repoet.
    """
    line_start = text.rfind("\n", 0, offset) + 1
    head = text[line_start:offset]
    if RE_GUARD.search(head):
        close = _match_end(text, line_start + head.rfind("("), "(", ")")
        rest = text[close + 1:text.find("\n", close + 1)]
        brace = rest.find("{")
        semi = rest.find(";")
        if brace >= 0 and (semi < 0 or brace < semi):
            open_at = close + 1 + brace
            return text[open_at:_match_end(text, open_at, "{", "}") + 1]
        if semi < 0:
            return rest
        return rest[:semi]
    # Tildeling: hele sætningen, og hvis den ikke bærer svaret, hele den
    # inderste blok den står i.
    statement_start = max(
        text.rfind(";", 0, offset), text.rfind("{", 0, offset),
        text.rfind("}", 0, offset),
    ) + 1
    semi = text.find(";", offset)
    statement = text[statement_start:semi + 1 if semi >= 0 else len(text)]
    if RE_SERVER_ERROR.search(statement) or RE_WHEN.search(statement):
        return statement
    brace_open = text.rfind("{", 0, offset)
    if brace_open < 0:
        return statement
    return text[brace_open:_match_end(text, brace_open, "{", "}") + 1]


def _match_end(text: str, start: int, opening: str, closing: str) -> int:
    """Index på den `closing` der matcher `opening` ved `start`.

    Uden matcheren bliver en `if (…) { … }` med en klamme *inde i* en streng
    (`'a { b'`) til at læse hele resten af filen som én gren.
    """
    depth, i = 0, start
    while i < len(text):
        if text[i] == opening:
            depth += 1
        elif text[i] == closing:
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return len(text)


# `if`, `else if`, `while`, `switch` — de nøgleord der gør et 429-sammenlignings-
# punkt til en betingelse. Udenfor dem er det en tildeling.
RE_GUARD = re.compile(r"\b(?:if|while|switch)\s*\(")


def reaches_function(body: str, target: str, source: str, depth: int = 0) -> list[str]:
    """Kalder `body` (transitivt, i denne fil) `target`? Returnér vejen.

    Kun navne der *er* defineret som funktion i samme fil tæller, og de skal
    nævnes et sted — ikke nødvendigvis med `(`. `again()` i tak-siden skriver
    `setTimeout(poll, delay)`: et navnehenvisning, ikke et kald, og det er den
    der gør genkaldet. Kun `navn(` ville have set den som grøn.
    """
    if depth > 6:
        return []
    if target in _referenced(body, source):
        return [target]
    for name, _begin, inner in _function_ranges(source):
        if name != target and name in _referenced(body, source):
            found = reaches_function(inner, target, source, depth + 1)
            if found:
                return [name] + found
    return []


def _referenced(body: str, source: str) -> set[str]:
    definerede = {name for name, _begin, _body in _function_ranges(source)}
    return definerede & set(RE_IDENTIFIER.findall(body))


def client_routes(body: str) -> set[str]:
    """Ruter klienten kalder, uden query-string.

    Uden afskæringen så `fetch('/api/stripe/fulfillment?session_id=')` ikke
    matche dispatchens `/api/stripe/fulfillment`, og dom 3 og dom «sig intet om
    429» faldt *stille* på den mest udsatte klient. Selvtesten fandt det.
    """
    return {url.split("?", 1)[0].rstrip("?&") for url in RE_FETCH_TARGET.findall(body)}


RE_FETCH_TARGET = re.compile(r"fetch\s*\(\s*['\"`]([^'\"`]+)['\"`]")


def check_client(relative: str, source: str, limit_routes: dict[str, str]) -> list[str]:
    problems: list[str] = []
    tests = [m.start() for m in RE_429_TEST.finditer(source)]

    # Dom 3 først, så en klient der hverken sender 429-kald eller prøver igen
    # på 5xx ikke får to fund for det samme.
    called = client_routes(source)
    if called & set(limit_routes):
        if not RE_TRANSIENT.search(source):
            problems.append(
                f"{relative}: ruter med 429 ({', '.join(sorted(called & set(limit_routes)))}) "
                f"kaldes, men intet forbigående svar genkaldes. En 5xx er *vores* "
                f"fejl og skal prøves igen — elers låser ét KV-blip en betalt kunde ude."
            )
        if not RE_429_TEST.search(source):
            problems.append(
                f"{relative}: kalder en rute der kan svare 429 ({', '.join(sorted(called & set(limit_routes)))}) "
                f"uden at sige noget om 429. Serverens egen tæller kan give den, "
                f"og så falder den i den generelle fejltekst."
            )

    for offset in tests:
        line = source.count("\n", 0, offset) + 1
        body = branch_body(source, offset)

        # Dom 1: ingen nyt kald på en endelig status. Det transitive led er
        # hele porten — `again()` i thanks.html genkalder ikke fetch selv.
        holder = enclosing_function(source, offset)
        if holder:
            name, holder_body = holder
            if name and RE_FETCH.search(holder_body):
                path = reaches_function(body, name, source)
                if path:
                    problems.append(
                        f"{relative}:{line}: 429 fører til et nyt kald "
                        f"({' → '.join(path)} → {name}). 429 er endelig: serveren "
                        f"har sagt hvor længe den varer, og hvert genkald tæller i "
                        f"den samme tæller der gav 429."
                    )

        # Dom 2: sig hvornår man kommer tilbage.
        said = bool(RE_SERVER_ERROR.search(body) or RE_WHEN.search(body))
        if not said:
            problems.append(
                f"{relative}:{line}: 429 giver hverken serverens egen sætning "
                f"eller et tidspunkt. \"Vi prøver igen\" er en undskyldning, "
                f"ikke en oplysning — kunden ved ikke hvornår der er grund til "
                f"at komme tilbage."
            )
    return problems


# Et forbigående svar: 5xx, eller et kald der slet ikke kom svar (status 0 og
# et ulæseligt svar). `/net.js` kalder det præcis sådan, og de tre klienters
# egne navne (`isServerError`, `err.transient`) er målt herfra, ikke håndskrevet
# som en liste af sider.
RE_TRANSIENT = re.compile(
    r"(?:>=|>|==|===)\s*500|status\s*===\s*0|isServerError|err\.transient"
)


def collect_problems() -> tuple[list[str], dict[str, str], dict[str, str]]:
    limit_routes = producing_429_routes()
    sources = client_sources()
    clients: dict[str, str] = {}
    servers: dict[str, str] = {}
    for relative, source in sources.items():
        if not RE_429_TEST.search(source):
            continue
        (servers if RE_PRODUCES.search(source) else clients)[relative] = source
    problems: list[str] = []
    for relative in sorted(clients):
        problems.extend(check_client(relative, clients[relative], limit_routes))
    return problems, clients, {**limit_routes, **{f"[server] {k}": "<fil>" for k in servers}}


def _gate_over(sources: dict[str, str]) -> list[str]:
    """Kør hele porten — inkl. klient-opdagelsen — over et kilde-sæt.

    Mutationerne skal fanges af den *indgang* en ny side kommer ind gennem, ikke
    af `check_client` alene: den mutation der tilføjer en klient uden 429 skal
    opdages af opdagelsen, ellers ville den være grøn.
    """
    problems: list[str] = []
    limit_routes = producing_429_routes()
    for relative in sorted(sources):
        source = sources[relative]
        if not RE_429_TEST.search(source) or RE_PRODUCES.search(source):
            continue
        problems.extend(check_client(relative, source, limit_routes))
    return problems


def self_test() -> int:
    """Bevis at porten kan rødme på de rigtige filer, og lader de ærlige grønne.

    Scenarierne er de publicerede klienter, ikke syntetiske strenge. En fejlform
    der kun findes i en streng porten selv har lavet, er ingen fejlform.

    **Ingen fil og ingen sætning er navngivet.** Findes ved deres *egenkab*:
    de sammenligner med 429, og de kalder en rute workeren målt kan svare 429 på.
    Mutationerne bygges af klientens egen blok med portens egne mønstre, og hver
    køres gennem **hele porten** — ikke kun `check_client` — så den mutation der
    tilføjer en ny klient bliver fanget af opdagelsen. Målt 1/10 på korpus:
    3 ærlige klienter, 3 mutationer — alle fanget.
    """
    sources = client_sources()
    clients = {rel: src for rel, src in sources.items()
               if RE_429_TEST.search(src) and not RE_PRODUCES.search(src)}
    failures: list[str] = []

    if not clients:
        failures.append("målingen: ingen klient i site/ sammenligner med 429")
    if not producing_429_routes():
        failures.append("målingen: ingen rute i site/_worker.js kan svare 429")

    problems = _gate_over(sources)
    if problems:
        failures.append(f"målingen: porten er rød på de publicerede klienter — {problems[0]}")
    ærlige = sorted(clients)
    if len(ærlige) < 3:
        failures.append(
            f"målingen: kun {len(ærlige)} ærlige 429-klienter fundet "
            f"(forventer 3: tak-siden, rapporten og den delte hjælpefunktion)"
        )

    mutationer: list[tuple[str, str]] = [
        ("429 i en genkaldsgren", "læg 429-grenen ind i den forbigående, som var fejlen på tak-siden"),
        ("429 uden oplysning", "fjern både serverens sætning og tidspunktet fra 429-grenen"),
        ("5xx gjort endelig", "gør 5xx endelig i stedet for forbigående"),
    ]
    fanget = 0
    for name, beskrivelse in mutationer:
        rød = False
        prøvet = 0
        for relative in ærlige:
            muteret = muter(clients[relative], name, producing_429_routes())
            if muteret is None:
                continue
            prøvet += 1
            kandidat = dict(sources)
            kandidat[relative] = muteret
            if _gate_over(kandidat):
                rød = True
                break
        if rød:
            fanget += 1
        else:
            failures.append(
                f"mutation «{name}» ({beskrivelse}) blev ikke fanget "
                f"({prøvet} klient(er) kunne bære den)"
            )
    if not failures:
        print(f"SELFTEST GRØN — {len(ærlige)} ærlige klienter, "
              f"{fanget}/{len(mutationer)} mutationer fanget")
    for failure in failures:
        print("SELVTEST RØD — " + failure)
    return 1 if failures else 0


def muter(source: str, name: str, limit_routes: dict[str, str]) -> str | None:
    """Byg mutationen i klientens egen kode, med portens egne mønstre.

    Returnerer `None` hvis den pågældende klient ikke har den fejlform — så
    selvtesten prøver den næste i stedet for at grunde på en tilfældighed.
    """
    if name == "429 i en genkaldsgren":
        return _muter_retry(source)

    if name == "429 uden oplysning":
        return _muter_strip_oplysning(source)

    if name == "5xx gjort endelig":
        # Den modsatte fejl: 429 er rettet ved at gøre *alt* endeligt, så
        # dom 1 og 2 er opfyldt og kun dom 3 fanger den. Alle forekomster
        # skifter, ellers efterlader én `>= 500` et andet sted porten grøn.
        if RE_TRANSIENT.search(source) and RE_429_TEST.search(source):
            return re.sub(r">=\s*500", "=== 599", source)
        return None
    return None


def _muter_retry(source: str) -> str | None:
    """Læg 429-grenen ind i en genkaldsgren — fejlformen fra `thanks.html`."""
    for match in RE_429_TEST.finditer(source):
        body = branch_body(source, match.start())
        holder = enclosing_function(source, match.start())
        if not holder or not RE_FETCH.search(holder[1]):
            continue
        if reaches_function(body, holder[0], source):
            continue  # denne 429 er ærlig; prøv den næste
        line_start = source.rfind("\n", 0, match.start()) + 1
        line_end = source.find("\n", match.start())
        linje = source[line_start:line_end]
        # Den mutation reviewens fund beskriver: 429 smelter sammen med 5xx i
        # én forbigående gren. `fail(` bliver til `again(`, som er det kalde-
        # navn denne gren ringer på i originalen.
        ny = re.sub(r"\(([^)]*)\)\s*return\s+fail\(", r"(\1 || x.code >= 500) return again(", linje, count=1)
        if ny != linje:
            return source[:line_start] + ny + source[line_end:]
        # Tak-sidens rettelse 6/10 skrev 429-grenen om fra en-linjes
        # `(...) return fail(...)` til en blok, og dermed findes formen
        # ovenfor ikke længere i nogen klient. Fejlformen er den samme —
        # grenen genkalder — så byg den af blokken: lad grenen kalde den
        # funktion i filen der (transitivt) genkalder holderen.
        helper = _retry_helper(source, holder[0])
        if helper:
            return source.replace(
                body, "{ return " + helper + "('Trying again', 4000, false); }", 1)
    return None


def _retry_helper(source: str, holder: str) -> str | None:
    """Navnet på en funktion i filen der (transitivt) genkalder `holder`.

    Det er præcis den egenskab dom 1 dømmer, så et kald til den funktion i
    429-grenen *er* fejlformen — uanset hvad hjælperen hedder.
    """
    for name, _begin, fn_body in _function_ranges(source):
        if name == holder:
            continue
        if reaches_function(fn_body, holder, source):
            return name
    return None


def _muter_strip_oplysning(source: str) -> str | None:
    """Fjern både serverens sætning og tidspunktet fra 429-grenen."""
    for match in RE_429_TEST.finditer(source):
        body = branch_body(source, match.start())
        if not (RE_SERVER_ERROR.search(body) or RE_WHEN.search(body)):
            continue
        renset = re.sub(r"\.error\b", ".msg", body)
        renset = RE_WHEN.sub("snart", renset)
        if renset == body:
            continue
        return source.replace(body, renset, 1)
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="bevis at porten fanger de fejlformer, den siger at fange",
    )
    args = parser.parse_args()
    if args.self_test:
        return self_test()

    problems, clients, routes = collect_problems()
    print(f"{len(routes)} ruter i site/_worker.js kan svare 429")
    for path, handler in sorted(routes.items()):
        if handler == "<fil>":
            continue
        print(f"  {path}  handler={handler}")
    print(f"{len(clients)} klienter i site/ sammenligner med 429")
    for relative in sorted(clients):
        print(f"  {relative}")
    print(f"problems: {len(problems)}")
    for problem in problems:
        print(problem)
    print("GRØN" if not problems else "RØD")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())