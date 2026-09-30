#!/usr/bin/env python3
"""Gate lagrings-løfter på de sider, hvis egen kode modbeviser dem.

Baggrund (opgave 2 i `IMPLEMENTATION_PLAN.md`, 30. september 2026). Den
danske købsside lovede 11 tilgængelighedsregler i den ene linje, mens tre andre
linjer på *samme side* sagde 15. Forrige iteration rettede den **synlige**
tekst og lod JSON-LD-FAQ'en stå med den gamle løgn — altså netop den version
Google viser i sit FAQ-resultat, og en der modsiger sidens egen brødtekst.

Det samme mønster lå i en hel klasse af lagrings-påstande, og her er det
**målt på koden**, ikke på en læst sætning. `site/_worker.js` kalder
`rateLimitIp()` i seks ruter:

    /scan-proxy  /api/header-check  /api/url-inspect
    /api/report  /api/clean-copy    /api/compliance-scan

`rateLimitIp()` skriver `rl:<scope>:<sha256(salt|ip)>:<time-slotte>` i KV med
`expirationTtl: 7200`. Så hver eneste af de ruter gemmer et hash af
besøgerens IP-adresse i to timer. Det er en fuldstændig rimelig ting at gøre
— den er præcis grunden til at portalen kan afvise 429 — men den er en
**faktisk lagring**, og en side der siger "no logs, no storage, no cookies"
mens dens egen `fetch()` rammer en af de ruter, siger noget der ikke er sandt.

Målt 30/9 før denne port blev skrevet: **10** sider kalder en af de seks
ruter, og **9** af dem sigde en absolut afvisning af lagring. Den tiende,
`compliance-report.html`, gjorde det rigtigt forud — den siger præcis, at
time-tælleren er det eneste der gemmes. Den er modellen, ikke en undtagelse.

**Hvorfor en port og ikke en håndmåling.** De tre fund fra review 29/9 og denne
fejl er samme fejl igen: en tekst bliver rettet ét sted, mens dens søskende
eller dens usynlige JSON-LD-udgave bliver stående. `check_product_copy.py`
fanger det kun for 13 navngivne filer; `check_rule_claims.py` tæller tal, ikke
lagring. En ny side der arver "nothing is stored" fra en søskende ville derfor
komme ud i portene. Det er samme grund som de otte andre porte i `site/`.

**Porten dømmer adfærd, ikke et navn.** Den læser *hvilken rute en side kalder*
gennem sidens egne `fetch('…')` og læser *hvilke ruter der gemmer et IP-hash*
gennem `rateLimitIp()`-kaldene i `site/_worker.js`. Ingen af de to lister er
håndskrevet her; en ny rate-limiteret rute eller en ny side, der kalder en
eksisterende, bliver dømt automatisk. Det er modsatningen til de to fund fra
29/9, hvor porten greb navnet `targetIsPublic` i 3000 tegn og var grøn både med
og uden SSRF'en.

Den dømmer to ting, pr. fund:

1. **Et absolut afvisnings-løfte på en side der kalder en gemmende rute.**
   Løfterne er målt fra de publicerede sider, ikke fundet ved gætteri — de er
   dem der faktisk stod der, med den konkrete sætning i citat.
2. **Et afvisnings-løfte uden IP-hash-afsløringen.** Selv en side der siger
   "intet gemmes" men *også* nævner tælleren i en anden linje er svært at
   læse; krævet er at afsløringen står i samme svar.

**Den blinde plet, porten har, og hvorfor den er målt.** En side der *beskriver*
et værktøj uden at kalde det — f.eks. en blogartikel der siger "nothing is
stored" om scanneren — kan ikke dømmes herfra, fordi porten læser `fetch`-
kald, ikke links. Målt: **4** artikler i `site/blog/` linker til en gemmende
side og siger et afvisnings-løfte. De er rettet i samme diff som porten, men
de er rettet fordi porten viste hvor de var, ikke fordi porten dømmer dem. En
fremtidig artikel med samme fejl er derfor stadig ubemandet; det står her,
fordi en port der ser ud til at dække mere end den gør, er værre end ingen.

    python3 tools/check_storage_claims.py
    python3 tools/check_storage_claims.py --self-test
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORKER = ROOT / "site" / "_worker.js"
SITE = ROOT / "site"

# `fetch('/scan-proxy?url=' …` og `fetch("/api/header-check?url=" …`. Kun
# streng-literaler: en URL bygget med variabel kan ikke slås op på statisk
# grund, og porten skal ikke gætte.
RE_FETCH = re.compile(r"""fetch\(\s*['"]([^'"?]+)""")

# `href="scan"` er rodrelativt og `href="/scan"` er absolutt; begge former
# bruges i `site/`. Uden den relative form får `compliance-ai.html` ingen
# vegne ind i scanneren, og dens løgn om scanneren går ubemærket.
RE_HREF = re.compile(r"""href=["']([^"'#?]+)""")

# `rateLimitIp(request, env, 'scan-proxy', SCAN_PROXY_RATE_LIMIT)`. Det er
# kaldet, ikke navnet på funktionen, der gør en rute til en gemmende rute.
RE_RATE_LIMIT_CALL = re.compile(r"rateLimitIp\(\s*request,\s*env,\s*'([^']+)'")

# Dispatch: `if (path === '/scan-proxy') { return handleScanProxy(…` og
# `if (path === '/api/profile') return handleProfile(…`. Begge former findes i
# `site/_worker.js`, så porten læser dem begge.
RE_DISPATCH_INLINE = re.compile(r"if \(path === '([^']+)'\) return (\w+)\(")
RE_DISPATCH_BLOCK = re.compile(r"if \(path === '([^']+)'\) \{\s*return (\w+)\(")

# En funktions krop i `_worker.js`: fra `async function name(` til den næste
# topniveau-funktion. Præcis nok til at finde hvilken handler der kalder
# `rateLimitIp` med et givent scope.
RE_FUNCTION = re.compile(r"^async function (\w+)\(", re.M)

# Absolutte afvisninger. Målt fra de publicerede sider 30/9, ikke konstrueret:
# hver mønstrene her stod i en udgivet FAQ, meta-tekst eller brødtekst.
RE_DENIAL = re.compile(
    r"""(?P<claim>
        no\ logs?,?\ no\ storage
      | no\ storage,?\ no\ cookies
      | nothing\ is\ logged\ or\ saved
      | nothing\ is\ stored
      | nothing\ stored
      | no\ backend\ that\ records
      | intet\ logges\ eller\ gemmes
      | ingen\ logs,?\ ingen\ lagring
      | vi\ gemmer\ intet
    )""",
    re.IGNORECASE | re.VERBOSE,
)

# Hvad afsløringen skal sige. Ikke et krav om et bestemt ordval — porten dømmer
# *om* svaret nævner IP-hashet, fordi det er den eneste måde et "intet gemmes"
# kan være sandt på en side, hvis rute gemmer et IP-hash.
RE_DISCLOSURE = re.compile(
    r"(hash\w*\s+(?:of\s+)?(?:your|the|its|an?)\s+ip\b"
    r"|hash\w*\s+af\s+(?:din|den)\s+ip"
    r"|ip[-\s]adresse"
    r"|ip\ address"
    r"|time[-\s]tæller"
    r"|hourly\ counter)",
    re.IGNORECASE,
)

# Hvad der tæller som *én* svar. En JSON-LD-`Answer`-tekst, en `<summary>` +
# `<p>`, en `<h3>` + `<p>`, og en meta-`content`-attribut. Uden denne blokering
# ville afsløringen i én nabo-blok dække et løfte i en anden.
RE_LD_ANSWER = re.compile(
    r'"name"\s*:\s*"(?P<question>(?:[^"\\]|\\.)*)"\s*,\s*"acceptedAnswer"\s*:\s*'
    r'\{\s*"@type"\s*:\s*"Answer"\s*,\s*"text"\s*:\s*"(?P<text>(?:[^"\\]|\\.)*)"'
)
RE_VISUAL_QA = re.compile(
    r"<(?:summary|h[23])[^>]*>(?P<question>.*?)</(?:summary|h[23])>\s*"
    r"<p[^>]*>(?P<text>.*?)</p>",
    re.IGNORECASE | re.DOTALL,
)
# `.privacy-note` er den tredje form: en hel note der svarer på spørgsmålet
# uden `<summary>`. `/url-to-markdown` har sin i linje 111, og den sagde
# "Nothing is stored." lige under et `<h2>`-spørgsmål porten ellers fanger.
# Kun den indre `<span>` tages — mønsteret skal ikke løbe videre ind i
# næste sektion, hvilket var målt til at trække hele sidens brødtekst med.
RE_VISUAL_NOTE = re.compile(
    r"<div[^>]*class=\"[^\"]*privacy-note[^\"]*\"[^>]*>.*?"
    r"<span[^>]*>(?:(?!</span>).)*<strong>(?P<text>.*?)</span>",
    re.IGNORECASE | re.DOTALL,
)
RE_META_NAME_FIRST = re.compile(
    r'<meta\b[^>]*\b(?:name|property)="[^"]*description"[^>]*\bcontent="(?P<text>[^"]*)"',
    re.IGNORECASE,
)
RE_META_CONTENT_FIRST = re.compile(
    r'<meta\b[^>]*\bcontent="(?P<text>[^"]*)"[^>]*\b(?:name|property)="[^"]*description"',
    re.IGNORECASE,
)

# Et spørgsmål *om* lagring. Ikke et spørgsmål med et lagringsord i sig
# (`Where do I store my backups?`), men hvor svaret handler om, hvad værktøjet
# beholder — sådan som de ni sider spørger.
RE_STORAGE_QUESTION = re.compile(
    r"(stor(?:e|es|ed|ing)\b|stored|storage|log(?:s|ged|ging)?\b|track(?:ed|ing|s)?\b"
    r"|gemm(?:er|es|et)?\b|lagr(?:es|ing|t)?\b|logg(?:es|et)?\b)",
    re.IGNORECASE,
)


def unescape_json(text: str) -> str:
    return text.replace('\\"', '"').replace("\\\\", "\\").replace("\\u2014", "—")


def strip_tags(text: str) -> str:
    return re.sub(r"<[^>]+>", " ", text)


def normalise(text: str) -> str:
    return " ".join(text.split())


def worker_text() -> str:
    return WORKER.read_text(encoding="utf-8")


def function_bodies(text: str) -> dict[str, str]:
    """Kortlæg `async function navn(` → krop, frem til næste topniveau-funk."""
    starts = [(m.group(1), m.end()) for m in RE_FUNCTION.finditer(text)]
    bodies: dict[str, str] = {}
    for index, (name, begin) in enumerate(starts):
        end = starts[index + 1][1] if index + 1 < len(starts) else len(text)
        bodies[name] = text[begin:end]
    return bodies


def storing_routes(text: str | None = None) -> dict[str, str]:
    """Ruter hvis handler kalder `rateLimitIp` med sit eget scope.

    Målt, ikke håndskrevet: en ny `rateLimitIp(…, 'ny-scope', …)` i en
    eksisterende handler gør den rute gemmende uden at nogen redigerer her.
    """
    text = worker_text() if text is None else text
    bodies = function_bodies(text)
    dispatch: dict[str, str] = {}
    dispatch.update(RE_DISPATCH_INLINE.findall(text))
    dispatch.update(RE_DISPATCH_BLOCK.findall(text))
    scopes_by_handler: dict[str, set[str]] = {}
    for scope in RE_RATE_LIMIT_CALL.findall(text):
        for name, body in bodies.items():
            if f"'{scope}'" in body:
                scopes_by_handler.setdefault(name, set()).add(scope)
    routes: dict[str, str] = {}
    for path, handler in dispatch.items():
        for scope in sorted(scopes_by_handler.get(handler, ())):
            routes[path] = scope
            break
    return routes


def site_pages() -> dict[str, str]:
    """`site/scan.html` → `scan.html`, altså stier **relative til `site/`**.

    Præfikset er bevidst ikke med: det er sådan `build_sites.py` og de andre
    læseværktøjer i repoet navngiver filer, og de har alle nøgler uden. Alle
    funktioner der skal have en sti — `link_targets`, `check_page` — tager derfor
    imod en `site/…`-form og præfikser selv. At blande de to var målt som en
    selftest-fejl: `reached` indeholdt `scan`, `link_targets` svarede `site/scan`,
    og porten var grøn på en løgn den ellers fanger.
    """
    return {
        str(path.relative_to(SITE)): path.read_text(encoding="utf-8")
        for path in sorted(SITE.rglob("*.html"))
    }


def called_storing_routes(page: str, routes: dict[str, str]) -> list[str]:
    """De gemmende ruter siden faktisk kalder gennem sin egen `fetch`."""
    return sorted({m.group(1) for m in RE_FETCH.finditer(page)} & set(routes))


def link_targets(relative: str, page: str) -> set[str]:
    """Sidens links, opløst til repo-stier som `site/scan.html`.

    `href="scan"` er rodrelativ, `href="/scan"` er absolutt, og begge former
    bruges i `site/`. Opløsningen er mod `site/`, fordi det er den mappe de to
    former peger ind i — ikke mod den enkelte fils mappe, som ville gøre
    `compliance-ai.html`s `href="scan"` pege på `site/scan` (uden `.html`) og
    altså intet.

    Stien skæres ned til `site/…` først, så basen er den samme uanset om
    kaldet bruger `"compliance-ai.html"` eller `"site/compliance-ai.html"`.
    Uden det ville de to give to forskellige svar på det samme spørgsmål, og
    selftesten ville grønne en fejl den ikke kan finde.
    """
    # `relative` er relativ til `site/` — samme form som `site_pages()` giver,
    # og samme form som `route_pages()` skriver nøgler i. Derfor *må* basalen
    # ikke præfikses med `site/`: det gav `site/scan` mod `scan` i det samme
    # sammenligningssæt. Målt, ikke gættet — det er sådan selftesten blev grøn
    # på den mutation porten ellers fangede.
    base = Path(relative).parent
    targets: set[str] = set()
    for href in RE_HREF.findall(page):
        if href.startswith(("http://", "https://", "mailto:", "javascript:")):
            continue
        path = href if href.startswith("/") else str(base / href)
        parts: list[str] = []
        for piece in path.split("/"):
            if piece in ("", "."):
                continue
            if piece == "..":
                if parts:
                    parts.pop()
                continue
            parts.append(piece)
        if parts:
            targets.add("/".join(parts))
    return targets


def route_pages(pages: dict[str, str], routes: dict[str, str]) -> set[str]:
    """`site/scan.html` → `site/scan`, altså præcis hvad `link_targets` svarer.

    Begge nøglesæt er præfikset med `site/`, ellers mødtes de ikke: `href="scan"`
    i `site/compliance-ai.html` opløses til `site/scan`, og det skal være det
    samme som den gemmende sides nøgle. Det var målt som en selftest-fejl, ikke
    gættet — de to lister så ens ud og passede alligevel ikke sammen.
    """
    reached: set[str] = set()
    for relative, raw in pages.items():
        if not called_storing_routes(raw, routes):
            continue
        path = str(Path(relative).with_suffix(""))
        reached.add(path)
        if path.endswith("/index"):
            reached.add(path[: -len("/index")])
    return reached


def reaches_storing_tool(relative: str, page: str, reached: set[str]) -> list[str]:
    """Værktøjer siden *beskriver* — den kalder dem ikke, den linker til dem."""
    return sorted(link_targets(relative, page) & reached)


def claim_blocks(page: str) -> list[tuple[str, str | None, str, str]]:
    """(kilde, spørgsmål, svar, råt svar) for hvert svar på siden.

    Det fjerde felt er det **rå** blok-indhold, tags inklusive. Det er ikke
    en luksus: `selling_block` skal finde `<a href="scan">` i netop den
    brødtekst der siger "no logs, no storage, no cookies", og en strippet
    tekst kan ikke. Uden det felt faldt `/compliance-ai` ud af porten igen —
    målt, ikke antaget.

    Spørgsmålet medtages for at fejlmeddelelsen kan citere det, ikke for at
    filtrere. En forfatter kan skrive afvisningen i svaret på *hvad scanneren
    gør* — det gjorde `/compliance-ai` — og et spørgsmålsfilter ville ladet
    løgnen stå. Det er `RE_DENIAL` der afgør om et svar overhovedet er i
    spørgsmålstillingen.

    Meta-tekster har intet spørgsmål — de er sig selv påstanden — så der er
    tredje felt `None` for dem.
    """
    blocks: list[tuple[str, str | None, str, str]] = []
    for match in RE_LD_ANSWER.finditer(page):
        blocks.append(
            (
                "JSON-LD",
                unescape_json(match.group("question")),
                unescape_json(match.group("text")),
                match.group("text"),
            )
        )
    for match in RE_VISUAL_QA.finditer(page):
        raw = match.group("text")
        blocks.append(
            ("brødtekst", normalise(strip_tags(match.group("question"))), strip_tags(raw), raw)
        )
    for match in RE_VISUAL_NOTE.finditer(page):
        raw = match.group("text")
        blocks.append(("privatlivsnote", None, strip_tags(raw), raw))
    for pattern in (RE_META_NAME_FIRST, RE_META_CONTENT_FIRST):
        for match in pattern.finditer(page):
            blocks.append(("meta", None, match.group("text"), match.group("text")))
    return blocks


# Et svar der *afviser* uden at bruge nogen af ordene ovenfor: "Nej. Siden
# hentes … og kasseres straks." Det er den samme løgn i en renere sætning, og
# den er målt på `cookie-check.html` og `cookie-check-da.html`.
RE_IMPLIED_DENIAL = re.compile(
    r"^\s*(?:nej|no)\.\s",
    re.IGNORECASE,
)
RE_DISCARDED = re.compile(
    r"\b(?:kasseres|kasserer|discarded|slettes|not\ stored)\b",
    re.IGNORECASE,
)


def _implied_denial(text: str) -> re.Match[str] | None:
    """Et "Nej." / "No." der følges af at noget kasseres.

    Delt i to mønstre, fordi et "nej" alene ikke er en løgn — cookie-check
    spørger om *siderne*, og svaret "nej, siden kasseres" er sandt. Løgnen er
    først der, når læseren konkluderer at intet overhovedet gemmes, altså når
    afvisningen står sammen med "kasseres" og intenting nævner tælleren.
    """
    if not RE_IMPLIED_DENIAL.search(text) or not RE_DISCARDED.search(text):
        return None
    return RE_IMPLIED_DENIAL.search(text)


def selling_block(relative: str, text: str, reached: set[str]) -> bool:
    """Står der et link til et gemmende værktøj *i selve svaret*?

    Det er snævrere end "siden linker til værktøjet", og det er den rigtige
    skelnen. `compliance-ai.html` har `<a href="scan">free EAA Scanner</a>` i
    det samme `<p>` der siger "no logs, no storage, no cookies" — den sælger
    præcis det løfte dér. `dpa-generator.html` har derimod `/scan` i
    navigationen på hver side og siger "nothing is stored" om *generatoren*,
    der kører client-side og intet har med scanneren at gøre. Målt: de fire
    generatorer har **0** afvisninger i et link-holdt svar, så porten rører
    dem ikke — og det er den forskel, der adskiller en løgn fra en sandhed.

    Opløsningen er `link_targets` og ikke en kopi af den: da var den to steder,
    og kun den ene var fikset for `site/…`-præfikset. Det gjorde portens svar
    afhængigt af, hvilken sti den blev kaldt med — målt, da selftesten var grøn
    på den mutation `compliance-ai.html` ellers fangede.
    """
    return bool(link_targets(relative, text) & reached)


def check_page(
    relative: str,
    page: str,
    routes: dict[str, str],
    reached: set[str] | None = None,
) -> list[str]:
    """Siden skal ikke modsige sig selv.

    To veje ind i samme fejl, fordi de er samme fejl:

    * **Kalder** en gemmende rute gennem sin egen `fetch` — så er dens egen
      kode beviset mod dens egen tekst.
    * **Sælger** et værktøj der gør det, i et svar der lover det modsatte — så
      er løftet om noget andet, men læseren køber det her.

    Den anden vej er derfor, fordi `/compliance-ai` siger om *scanneren* at
    "no logs, no storage, no cookies", uden selv at kalde `/scan-proxy`. Det
    er den samme løgn, og den er den der ligger i FAQ'en Google viser.
    """
    problems: list[str] = []
    storing = called_storing_routes(page, routes)
    reached = reached or set()
    if not storing and not selling_block(relative, page, reached):
        # Siden kalder ingen gemmende rute og sælger ingen. Alt i
        # `claim_blocks` kan være sandt her, og så skal porten ikke røre det —
        # 57 søskendesider siger den samme sætning om rene klient-side-
        # værktøjer, og de har ret. At dømme dem ville være portens egen løgn.
        return problems
    because = (
        f"kalder {', '.join(storing)}"
        if storing
        else f"tilbyder et værktøj der gør det"
    )
    for source, question, text, raw in claim_blocks(page):
        denial = RE_DENIAL.search(text)
        implied = _implied_denial(text)
        if not denial and not implied:
            continue
        if not storing and not selling_block(relative, raw, reached):
            continue
        if RE_DISCLOSURE.search(text):
            continue
        quoted = (
            denial.group("claim").strip()
            if denial and "claim" in (denial.groupdict() or {})
            else normalise((denial or implied).group(0))
        )
        problems.append(
            f"{relative} ({source}): svarer {quoted!r} "
            f"men {because} — ruten gemmer et salt-hash af "
            f"IP'en i to timer (`rateLimitIp`, `expirationTtl: 7200`). Svar på "
            f"det samme spørgsmål med afsløringen, som compliance-report.html "
            f"giver: hvad der gemmes, hvor længe, og hvorfor."
        )
    return problems


def collect_problems() -> tuple[list[str], dict[str, list[str]], dict[str, str]]:
    routes = storing_routes()
    pages = site_pages()
    reached = route_pages(pages, routes)
    reaching: dict[str, list[str]] = {}
    for relative, raw in pages.items():
        calls = called_storing_routes(raw, routes)
        links = reaches_storing_tool(relative, raw, reached)
        if calls or links:
            reaching[relative] = calls or [f"link→{link}" for link in links]
    problems: list[str] = []
    for relative, raw in pages.items():
        problems.extend(check_page(relative, raw, routes, reached))
    return problems, reaching, routes


# Den løgn mutationen sætter ind, i **sidens eget sprog**. Begge ordlyd er
# målt mod `RE_DENIAL` og `RE_IMPLIED_DENIAL` — en mutation der indsatte en
# sætning porten ikke genkender, ville være grøn af den forkerte grund at den
# ikke ligner en løgn.
LO_GN = {
    "en": "No logs, no storage, no cookies.",
    "da": "Ingen logs, ingen lagring, ingen cookies.",
}
RE_DANSK = re.compile(r"\b(?:af|og|er|vi|gemmer|hverken|intet)\b", re.I)


def _sprog(relative: str, raw: str) -> str:
    """`da` eller `en` — fra sidens egen `lang`, ellers fra dens egen tekst.

    Mutationen skal læses som en løgn *på den side den er sat ind i*, så
    spørgsmålet ikke kan være det halve. Rækkefølgen er derfor: `lang` er
    erklæret, alt andet er gæt.
    """
    match = re.search(r"<html[^>]*\blang\s*=\s*[\"']?([a-zA-Z-]+)", raw)
    if match:
        return "da" if match.group(1).lower().startswith("da") else "en"
    return "da" if RE_DANSK.search(raw[:4000]) else "en"


def _med_tekst(raw: str, tekst: str) -> str:
    """Sæt `tekst` i stedet for blokkens egen løbende tekst — tags bevares.

    Tagsene er ikke kosmetik: et `<a href>` i blokken er det, der gør siden
    til en *sælgende* side, og `selling_block()` dømmer netop det. Uden dem
    ville mutationen fjerne salget og aldrig kunne blive rød.
    """
    if "<" not in raw:
        return tekst
    ud: list[str] = []
    sat = False
    for styk in re.split(r"(<[^>]+>)", raw):
        if styk.startswith("<"):
            ud.append(styk)
        elif styk.strip() and not sat:
            ud.append(tekst)
            sat = True
    if not sat:
        ud.append(tekst)
    return "".join(ud)


def self_test() -> int:
    """Bevis at porten kan rødme på de rigtige filer, og at den lader ærlige sider grønne.

    Scenarierne er de publicerede tekster — ikke syntetiske strenge. En fejlform
    der kun findes i en streng porten selv har fundet, er ingen fejlform.

    **Ingen fil og ingen sætning er navngivet.** 30/9-punden var tretten sider
    og syv frosne mutationsankere: den dag en af siderne fik sin tekst rettet
    eller omformuleret, faldt kontrollen af en opgave der *lykkedes*, og det sås
    som en rød port. Nu findes siderne ved deres **egenskab** — de kalder en
    gemmende rute eller sælger en, og de afslører IP-hashet i det svar der
    gør det — og mutationen bygges af sidens egen blok med portens egne
    mønstre, så den hverken bliver forældet eller afhænger af en enkelt side.
    Målt 30/9 på denne korpus: 13 ærlige sider (7 EN, 6 DA), 1 ren
    klient-side-side, 6 sider der kun kalder `/scan-proxy`.
    """
    pages = site_pages()
    routes = storing_routes()
    reached = route_pages(pages, routes)
    failures: list[str] = []

    def ringer(relative: str, raw: str) -> bool:
        """Sælger siden noget gemmende, og afslører den det i et svar?

        Det er *kun* disse sider porten skal kunne dømme, så det er også dem
        selve formen findes ved.
        """
        if not (called_storing_routes(raw, routes) or selling_block(relative, raw, reached)):
            return False
        return any(RE_DISCLOSURE.search(text) for _s, _q, text, _r in claim_blocks(raw))

    ærlige = sorted(rel for rel, raw in pages.items() if ringer(rel, raw))
    if not ærlige:
        failures.append("målingen: ingen side sælger noget gemmende og afslører IP-hashet")

    # 1. Rettelsen: en side der afslører IP-hashet i sit eget svar er ærlig,
    #    og porten skal være grøn på den — uanset hvilken fil det er.
    for relative in ærlige:
        problems = check_page(relative, pages[relative], routes, reached)
        if problems:
            failures.append(f"{relative}: porten er rød på en side der afslører IP-hashet — {problems[0]}")

    # 2. Løgnen: fjern **kun afsløringen** fra svarene, og læg løgnen ind i
    #    stedet. Det er den mutation de gamle håndskrevede cases gjorde — de
    #    indsatte en kompliment løgn, hvilket gjorde dem afhængige af to
    #    ting på én gang: sidens filnavn *og* dens ordlyd.
    for relative in ærlige:
        raw = pages[relative]
        løgn = LO_GN[_sprog(relative, raw)]
        beviset = False
        for _source, _q, _text, blok in claim_blocks(raw):
            if not RE_DISCLOSURE.search(blok):
                continue
            ny = _med_tekst(blok, løgn)
            if not called_storing_routes(raw, routes) and not selling_block(relative, ny, reached):
                # Siden sælger uden selv at kalde: mutationen skal også bære
                # det link, ellers er den ikke en sælgende blok, og porten har
                # ingen grund til at dømme den.
                ny += ' <a href="/scan">free scanner</a>'
            start = raw.find(blok)
            if start < 0:
                continue
            mutated = raw[:start] + ny + raw[start + len(blok):]
            if check_page(relative, mutated, routes, reached):
                beviset = True
                break
        if not beviset:
            failures.append(
                f"{relative}: porten er grøn når afsløringen er fjernet fra svaret "
                f"og løgnen {løgn!r} står i stedet"
            )

    # 3. En side der *ikke* kalder nogen gemmende rute må ikke røres, selv om
    #    den siger den samme sætning. Den siger "intet gemmes" om sig selv og
    #    har `/scan` i navigationen på hver side; det er den skelnen, der
    #    adskiller en løgn fra en sandhed. Findes ved egenskab: et svar med en
    #    afvisning, men hverken et kald eller et link til en gemmende rute.
    rene = sorted(
        relative for relative, raw in pages.items()
        if not called_storing_routes(raw, routes)
        and not selling_block(relative, raw, reached)
        and any(RE_DENIAL.search(t) or _implied_denial(t)
                for _s, _q, t, _r in claim_blocks(raw))
    )
    if not rene:
        failures.append("målingen: ingen ren klient-side-side med en afvisning at holde grøn")
    for relative in rene:
        problems = check_page(relative, pages[relative], routes, reached)
        if problems:
            failures.append(
                f"{relative}: porten er rød på en side der hverken kalder eller "
                f"linker til noget gemmende — {problems[0]}"
            )

    # 4. Ruten kommer fra koden: en `rateLimitIp(…, 'scan-proxy', …)` der
    #    forsvinder fra `handleScanProxy` skal gøre siderne grønne igen.
    #    Beviser at porten ikke har en håndskrevet ruteliste. Siderne vælges
    #    blandt dem der *kun* kalder den rute, så mutationen ikke efterlader
    #    dem med en anden gemmende kald — ellers ville de blive røde af en
    #    grund der ikke var mutationen.
    kun = sorted(rel for rel, raw in pages.items()
                 if called_storing_routes(raw, routes) == ["/scan-proxy"])
    if not kun:
        failures.append("målingen: ingen side kalder kun /scan-proxy")
    worker = worker_text()
    mutated_worker = worker.replace(
        "rateLimitIp(request, env, 'scan-proxy', SCAN_PROXY_RATE_LIMIT)", "null", 1
    )
    if mutated_worker == worker:
        failures.append("mutationsanker: rateLimitIp-kaldet i handleScanProxy blev ikke fundet")
    else:
        without = storing_routes(mutated_worker)
        if "/scan-proxy" in without:
            failures.append("porten læser en håndskrevet ruteliste: /scan-proxy er stadig gemmende")
        for relative in kun:
            if check_page(relative, pages[relative], without, reached):
                failures.append(
                    f"uden rateLimitIp er {relative} stadig rød — afsløringen mangler altså ikke"
                )

    print(f"self-test: {len(failures)} fejl — {len(ærlige)} ærlige sider, "
          f"{len(rene)} rene klient-sider, {len(kun)} sider der kun kalder /scan-proxy")
    for failure in failures:
        print(f"  FAIL {failure}")
    return 1 if failures else 0


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

    problems, reaching, routes = collect_problems()
    print(f"{len(routes)} ruter gemmer et IP-hash (fra `rateLimitIp` i site/_worker.js)")
    for path, scope in sorted(routes.items()):
        print(f"  {path}  scope={scope}")
    print(f"{len(reaching)} sider kalder en af dem")
    for relative, called in sorted(reaching.items()):
        print(f"  {relative}  ->  {', '.join(called)}")
    print(f"problems: {len(problems)}")
    for problem in problems:
        print(problem)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
