#!/usr/bin/env python3
"""Dom at `/developers` kun lover det der findes, og at den kan findes.

Målt 3/10 på den byggede udgivelse: de fire frie API'er — `/api/compliance-scan`,
`/api/profile`, `/api/header-check`, `/api/clean-copy` — virkede alle fire og
svarede 200 med et rigtigt JSON-svar målt med curl, men **ingen side på
mahope.tools nævnte dem**. MCP'en, der kalder præcis de fire, lå som `/mcp` på
cleancopy.tools og 404'ede på mahope.tools. Så det mest klonede repo i familien
(14 dage: 21 unikke kloninger, 2 visninger) havde ingen adresse på det domæne,
hvorfra det faktisk kalder.

Ingen port så det. `seo_check.py` dømmer en sides head og dens links, ikke om
siden findes; `check_links.py` dømmer at de links **der er** går ned; og
`route_inventory.json` kræver at en side i manifestet også er bygget — den
dømmer ikke at en side *mangler*. En API der virker, men som ingen kan finde,
ser ud som en død fra hvert af de tre steder.

Denne port har fem domme. Hver især er den noget, der kan blive rød uden at
nogen skal skrive en ny port til det:

  1. `ROUTE`     `/developers` findes i `route_inventory.json` for mahope.tools.
                 Uden den linje bliver siden bygget, men builden afbryder med
                 «route inventory mismatch» — så den er fundet på den hårdeste
                 måde, men først når nogen kører builden.
  2. `ENDPOINT`  Hvert `/api/…` der står på siden, er en rigtig rute i
                 `site/_worker.js`. En påstand i tekst er kode: skriver nogen
                 `/api/profil` fordi det er den danske stavemåde, er det en 404.
  3. `METHOD`    HTTP-metoden på siden er den workeren afviser med 405. Et
                 `GET /api/clean-copy` ville ikke svare, men se ud til at virke
                 i en notesbog.
  4. `FIELDS`    Hvert felt siden beder læseren **sende**, læses af den
                 handler ruten peger på. Det er den døde fejlform: et felt der
                 hedder `format` i stedet for `mode` giver **intet** — kaldet
                 lykkes, svaret ser rigtigt ud, og den der sendte fik aldrig den
                 tekst de bad om. Målt 3/10 på den første udgave af siden, som
                 sendte `{"html":…,"format":"markdown"}` og lovede
                 `format:"text"`, mens workeren læser `body.mode === 'plain'`.
  5. `LISTED`    Siden står i sitemap.xml og llms.txt på den **byggede** udgivelse.
                 Det er de to filer en agent og en søgemaskine faktisk læser;
                 en side der kun ligger i `site/` er ikke publiceret, den er
                 gemt.

**Hvad porten *ikke* dømmer:** felterne i **svaret**, og tallene på siden.
Rentegrænserne, `max_score` og de 50 000 tegn er sandt, men de er verificeret
mod `site/_worker.js` og hører hjemme i `tests/stripe-worker.test.mjs`-familien,
ikke her. Et *sendt* felt kan afgøres af porten, fordi det står i koden; et
*returneret* felt kan ikke, uden at porten kørte handleren. Denne port dømmer
derfor struktur: at det, siden *navngiver* og *beder om*, findes.

    python3 tools/check_developers_page.py            # dom
    python3 tools/check_developers_page.py --list     # kun fund, til rapport
    python3 tools/check_developers_page.py --self-test # 15 kontroller
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
INVENTORY = ROOT / "tools" / "route_inventory.json"
WORKER = SITE / "_worker.js"

SIDE = "developers.html"
ROUTE = "/developers"
DOMAENE = "mahope.tools"

# `/api/…` som står i sidens brødtekst. Kun i `main` — en `/api/track`-kald i
# det inline track-script skal ikke tælle som en dokumenteret rute, og det er
# netop den rute en sådan port ellers ville bede om at få fjernet fra koden.
MAIN_RE = re.compile(r"<main\b.*?</main\s*>", re.S | re.I)
API_RE = re.compile(r"(/api/[a-z][a-z0-9-]*)")
# Workerens rute-domme: `if (path === '/api/profile') return …`. Kun lighedstegn,
# så en `startsWith` på `/api/license/` ikke tælles som fire separate ruter.
ROUTE_RE = re.compile(r"path\s*===\s*'(/api/[a-z0-9/-]+)'")
# Routeren → handler, så tilladte_metoder() kan læse den rigtige krop.
HANDLER_RE = re.compile(r"path === '(/api/[a-z0-9/-]+)'\) return (\w+)\(")
CORS_RE = re.compile(r"'Access-Control-Allow-Methods':\s*'([^']+)'")


def side_tekster(html: str) -> str:
    """Sidens `<main>` som rå tekst, så `<pre>`-kode ikke forsvinder."""
    m = MAIN_RE.search(html)
    return m.group(0) if m else html


def ruter_i_main(html: str) -> list[str]:
    """De `/api/…`-ruter siden dokumenterer, i den rækkefølge de står."""
    fund: list[str] = []
    for rute in API_RE.findall(side_tekster(html)):
        if rute not in fund:
            fund.append(rute)
    return fund


def handler_kropper(src: str) -> dict[str, str]:
    """Rute → hele handlerens krop.

    Grænsen er den **næste topniveau-deklaration** i filen, ikke «næste `}`».
    En krøllesøjletæller brydes af præcis de ting der står i en handler — regex
    med `\\{`, skabelon-literals, JSON i en fejl — så den fandt aldrig sin
    afslutning og måtte falde tilbage på filens næste `function` på kolonne 0.
    Målt 3/10: den første udgave af denne port returnerede **ingen** kroppe, så
    dom 4 erklærede alle fire ruter for uafgørlige.

    Tælleren er bevaret som et tjek, ikke som grænse: hvis kroppen *balancerer*
    før den næste deklaration, bruges den, fordi den er den præcise grænse. Er
    den længere, er grænsen deklarationen — så læser porten aldrig ind i den
    næste funktion og dømmer et felt den ikke ejer.
    """
    ud: dict[str, str] = {}
    for rute, handler in dict(HANDLER_RE.findall(src)).items():
        m = re.search(r"(?:async )?function " + handler + r"\(", src)
        if not m:
            continue
        start = src.index("{", m.end())
        naeste = re.search(r"(?m)^(?:async )?function \w+\(", src[m.end():])
        deklaration = m.end() + naeste.start() if naeste else len(src)
        # Balanceret afslutning, kun hvis den ligger inden for deklarationen.
        dybde, i = 0, start
        while dybde > 0 or i == start:
            if src[i] == "{":
                dybde += 1
            elif src[i] == "}":
                dybde -= 1
                if dybde == 0:
                    break
            i += 1
            if i >= deklaration:
                break
        slut = i + 1 if i < deklaration else deklaration
        ud[rute] = src[start:slut]
    return ud


def sendte_felter(html: str, base: str) -> list[str]:
    """De JSON-nøgler siden beder læseren **sende** til én rute.

    Læst fra `-d '{…}'` i det `<pre>`-blok der indeholder routen, altså den
    kommando læseren kopierer. Et nøgleord i løbende tekst er ikke et felt der
    sendes — det er en beskrivelse — så kun body'en af `-d` tæller.

    Skrevet mod den fejl siden havde 3/10: den sendte `format`, som ingen læser,
    så kaldet lykkedes og svaret så rigtigt ud. Derfor denne dom og ikke bare
    dom 2, der kun dømmer om *ruten* findes.
    """
    main = side_tekster(html)
    for blok in re.findall(r"<pre\b.*?</pre\s*>", main, re.S | re.I):
        if base not in blok:
            continue
        felter: list[str] = []
        for d in re.findall(r"-d\s+'([^']+)'", blok):
            for nøgle in re.findall(r'"([A-Za-z_][A-Za-z0-9_]*)"\s*:', d):
                if nøgle not in felter:
                    felter.append(nøgle)
        if felter:
            return felter
    return []


def laeses_i_kroppen(krop: str, felt: str) -> bool:
    """Læser handleren feltet på en måde, der tæller?

    `body.felt` og `body['felt']` er de to former workeren bruger. Destructuring
    (`const { html } = body`) tæller **ikke** med her: den er ikke brugt i de fire
    handlers, og en for falskPositive dom er værre end ingen — den lærer porten
    at være rød på sandt, og så holder ingen længere op med at læse den.
    """
    return bool(re.search(r"\bbody\." + re.escape(felt) + r"\b", krop)
                or re.search(r"\bbody\[\s*['\"]" + re.escape(felt) + r"['\"]\s*\]", krop))


def tilladte_metoder(src: str) -> dict[str, str]:
    """Hvilken HTTP-metode hver `/api/…`-rute accepterer ifølge workerens egen CORS-header.

    Læst fra `'Access-Control-Allow-Methods'` i den handler, routeren sender
    ruten til. Det er **workerens egen erklæring**, ikke en antagelse i porten:
    målt 3/10 med curl mod den live udgivelse gav `GET /api/clean-copy` **405
    «POST only»**, mens `POST /api/profile` ikke blev afvist på metoden men
    svarede 400 «Missing ?url= parameter» — altså GET. En port der antog
    "alt er GET undtagen clean-copy" ville være rigtig i dag og stå på en løgn
    i morgen, fordi den ikke læser kilden.

    Bruges `Access-Control-Allow-Methods` og ikke `request.method !== 'POST'`,
    fordi sidste findes også i hjælpefunktioner oven i samme fil, som ikke er
    nogen route. Matcher kun på den handler, routeren faktisk peger på.
    """
    ud: dict[str, str] = {}
    for rute, krop in handler_kropper(src).items():
        am = CORS_RE.search(krop)
        if am:
            metoder = [x.strip().upper() for x in am.group(1).split(",")]
            # Præcis én af GET/POST: en rute der tager begge er ikke et
            # dokumentationsproblem, og porten skal ikke gøre den rød.
            brugbare = [x for x in metoder if x in ("GET", "POST")]
            if len(brugbare) == 1:
                ud[rute] = brugbare[0]
    return ud


def dom(root: Path = ROOT) -> list[str]:
    fund: list[str] = []
    inventory = json.loads((root / "tools" / "route_inventory.json").read_text(encoding="utf-8"))
    ruter = inventory.get(DOMAENE, [])

    # Dom 1 — ruten findes i manifestet.
    if ROUTE not in ruter:
        fund.append(
            f"ROUTE: {ROUTE} mangler i route_inventory.json for {DOMAENE}. "
            f"Siden bygges uden den, så builden stopper med «route inventory "
            f"mismatch»."
        )

    # Dom 2 og 3 — hver nævnt rute findes i workeren med den angivne metode.
    side_fil = root / "site" / SIDE
    html = side_fil.read_text(encoding="utf-8", errors="replace") if side_fil.exists() else ""
    kaldte = ruter_i_main(html)
    if not kaldte:
        fund.append(
            f"ROUTE: {SIDE} nævner ingen /api/-rute i <main>. Siden skal "
            f"kunne læses som dokumentation."
        )
    worker = (root / "site" / "_worker.js").read_text(encoding="utf-8", errors="replace")
    findes = set(ROUTE_RE.findall(worker))
    tilladt = tilladte_metoder(worker)
    kropper = handler_kropper(worker)
    for rute in kaldte:
        base = rute.split("?")[0]
        if base not in findes:
            fund.append(
                f"ENDPOINT: {SIDE} nævner {base}, men site/_worker.js har ingen "
                f"rute med det navn. En påstand i tekst er kode."
            )
            continue
        # Dom 3: påstanden om metoden skal være den routeren bruger.
        # `metode_pa_siden` læser kun det `<pre>`-blok, der indeholder ruten,
        # så et `GET` til et andet endpoint i samme blok ikke tæller med.
        metode = metode_pa_siden(html, base).upper()
        if metode not in ("GET", "POST"):
            fund.append(
                f"METHOD: {SIDE} angiver ingen kendt metode for {base} "
                f"(skriv GET eller POST i blokken med kommandoen)."
            )
            continue
        routerens = tilladt.get(base)
        if routerens is None:
            fund.append(
                f"METHOD: {base} erklærer ingen enkelt GET/POST-metode i "
                f"workerens CORS-header, så dommen kan ikke afgøre om "
                f"{metode} er rigtigt."
            )
        elif metode != routerens:
            fund.append(
                f"METHOD: {SIDE} siger {metode} for {base}, men workerens egen "
                f"CORS-header erklærer {routerens}."
            )

        # Dom 4: hvert felt siden beder læseren sende, læses af handleren.
        # Uden denne dom er dom 2 og 3 nok til at siden er grøn, selv om den
        # lærer en udvikler til at sende et felt der ignoreres stille.
        krop = kropper.get(base)
        if krop is None:
            fund.append(
                f"FIELDS: {base} har ingen læsbar handlerkrop i site/_worker.js, "
                f"så de felter siden sender ikke kan afgøres."
            )
        else:
            for felt in sendte_felter(html, base):
                if not laeses_i_kroppen(krop, felt):
                    fund.append(
                        f"FIELDS: {SIDE} sender feltet '{felt}' til {base}, men "
                        f"handleren læser det ikke. Kallet lykkes, svaret ser "
                        f"rigtigt ud, og læseren får aldrig det de bad om."
                    )

    # Dom 4 — siden er publiceret, altså den ligger i de to lister en agent og
    # en søgemaskine læser. Det dømmes på **dist**, fordi det er den udgivne
    # fil der tæller; `site/` er kilde, ikke publicering.
    dist = root / "dist" / DOMAENE
    if dist.is_dir():
        sitemap = dist / "sitemap.xml"
        llms = dist / "llms.txt"
        fuld_url = f"https://{DOMAENE}{ROUTE}"
        if not sitemap.is_file() or fuld_url not in sitemap.read_text(encoding="utf-8"):
            fund.append(
                f"LISTED: {ROUTE} mangler i den byggede sitemap.xml. Søgemaskinen "
                f"finder den aldrig."
            )
        if not llms.is_file() or fuld_url not in llms.read_text(encoding="utf-8"):
            fund.append(
                f"LISTED: {ROUTE} mangler i den byggede llms.txt. Den fil er den "
                f"ene måde en agent opdager API'et på."
            )
    return fund


def metode_pa_siden(html: str, base: str) -> str:
    """Metoden siden angiver for én rute, som den står i `<main>`.

    To kilder, i denne rækkefølge:

1. Det `<pre>`-blok der **indeholder** ruten. Det er kommandoen læseren
       kopierer, så det er den stærkeste påstand. Søger kun i blokke der
       indeholder ruten — ellers ville et `GET` til et andet endpoint i samme
       blok tælle med, og porten ville være grøn på en forkert metode. Det er
       kontrol 6 i selftesten, skrevet med præcis den fejlform.

       En blok uden metodeord er **ikke** svaret: `curl "…/api/profile?url=…"`
       er en GET, fordi GET er curls standard, og en læser kopierer den uden
       at tænke over det. Så blkken giver intet, og dommen falder videre til
       kilde 2 i stedet for at dømme siden rød på en vangivelse. (En blok der
       siger `-X POST` eller `-X GET` eksplicit tæller dog — det er den
       undtagelse, kontrol 3b og 3c dømmer.)
    2. Det metodeord der ligger **nærmest** omtalen af ruten, i begge
       retninger. Nødvendigt fordi en side typisk skriver metoden som et mærke
       lige ved routen: `<h3><code>/api/profile</code> <span>GET</span></h3>`.
       Kun baglæns ville fundet mærket ved næste endpoint og læst den som
       denne — kontrol 3c i selftesten fanger præcis det.

    Vælger det **nærmeste** metodeord, så den hører til den rute der spørges
    til. Uden noget metodeord overhovedet returneres `""`, så dom 3 kan se at
    siden slet ikke oplyser metoden.
    """
    main = side_tekster(html)
    for blok in re.findall(r"<pre\b.*?</pre\s*>", main, re.S | re.I):
        if base not in blok:
            continue
        m = re.search(r"\b(GET|POST|PUT|PATCH|DELETE)\b", blok)
        if m:
            return m.group(1)
        break  # blokken nævner ruten men er tavs om metoden → læs kilden 2

    i = main.find(base)
    if i < 0:
        return ""
    beste = None
    for m in re.finditer(r"\b(GET|POST|PUT|PATCH|DELETE)\b", main):
        afstand = min(abs(m.start() - i), abs(m.end() - i))
        if beste is None or afstand < beste[0]:
            beste = (afstand, m.group(1))
    # 400 tegn er et helt endpoint-afsnit; længere væk hører ordet til noget
    # andet, og da er siden uklar frem for fejlende.
    return beste[1] if beste and beste[0] <= 400 else ""


def self_test() -> int:
    fejl: list[str] = []
    talt = [0]

    def tjek(navn: str, sand: bool, detalje: str = "") -> None:
        talt[0] += 1
        if not sand:
            fejl.append(f"{navn}{': ' + detalje if detalje else ''}")

    worker = WORKER.read_text(encoding="utf-8", errors="replace")
    alle_ruter = sorted(set(ROUTE_RE.findall(worker)))
    tjek("workeren har /api/-ruter at dømme imod", len(alle_ruter) >= 10, str(len(alle_ruter)))
    fuld_url = f"https://{DOMAENE}{ROUTE}"
    # Den rigtige sides `<main>`, så kontrollerne kan bevise at porten er grøn
    # på det vi faktisk udgiver — ikke på noget de har skrevet.
    rigtig_main = side_tekster((SITE / SIDE).read_text(encoding="utf-8", errors="replace"))

    def dom_med(main: str, *, i_manifestet: bool = True, i_listerne: bool = True) -> list[str]:
        """Døm et repo hvor kun `site/developers.html` er udskiftet.

        Alt andet er ægte: den rigtige worker, det rigtige manifest, de rigtige
        dist-lister. Så en rød fund kan kun komme fra den side, kontrollen
        skrev — altså af den fejl den er skrevet til at finde.
        """
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            rod = Path(tmp)
            (rod / "tools").mkdir()
            (rod / "site").mkdir()
            (rod / "dist" / DOMAENE).mkdir(parents=True)
            ruter = ([ROUTE] if i_manifestet else []) + alle_ruter
            (rod / "tools" / "route_inventory.json").write_text(
                json.dumps({DOMAENE: ruter}), encoding="utf-8")
            (rod / "site" / "_worker.js").write_text(worker, encoding="utf-8")
            sitemap = f"<urlset>{fuld_url}</urlset>" if i_listerne else "<urlset></urlset>"
            llms = f"- [Free HTTP API]({fuld_url})" if i_listerne else "# nothing"
            (rod / "dist" / DOMAENE / "sitemap.xml").write_text(sitemap, encoding="utf-8")
            (rod / "dist" / DOMAENE / "llms.txt").write_text(llms, encoding="utf-8")
            # Samme filnavn som porten læser, så ingen anden kode skal ændres.
            (rod / "site" / SIDE).write_text(
                f"<html><body><main>{main}</main></body></html>", encoding="utf-8")
            return dom(rod)

    def har(fund: list[str], kode: str, rute: str = "") -> bool:
        return any(kode in f and (not rute or rute in f) for f in fund)

    # 1. Dom 1: ruten mangler i manifestet.
    tjek("dom 1 fanger en side uden manifestlinje",
         har(dom_med("<pre><code>curl https://mahope.tools/api/profile?url=x</code></pre>",
                     i_manifestet=False), "ROUTE:", ROUTE),
         str(dom_med("<pre><code>curl https://mahope.tools/api/profile?url=x</code></pre>",
                     i_manifestet=False)))

    # 2. Dom 2: en rute der ikke findes i workeren. Skrevet som den danske
    #    stavemåde, fordi det er sådan den fejl opstår i praksis.
    tjek("dom 2 fanger /api/profil", har(dom_med(
        "<pre><code>curl https://mahope.tools/api/profil?url=x</code></pre>"),
        "ENDPOINT", "/api/profil"))

    # 3. Dom 3: metoden er ikke den workeren erklærer. Live målt 3/10:
    #    `GET /api/clean-copy` svarer 405 «POST only».
    tjek("dom 3 fanger GET på en POST-only rute", har(dom_med(
        "<div><code>/api/clean-copy</code> <span class=\"method\">GET</span></div>"
        "<pre><code>curl https://mahope.tools/api/clean-copy</code></pre>"),
        "METHOD", "/api/clean-copy"))

    # 3b. Mutation: den modsatte fejl skal også fanges, ellers dømmer dom 3
    #     kun den ene retning.
    tjek("dom 3 fanger POST på en GET-rute", har(dom_med(
        "<div><code>/api/profile</code> <span class=\"method\">POST</span></div>"
        "<pre><code>curl -X POST https://mahope.tools/api/profile?url=x</code></pre>"),
        "METHOD", "/api/profile"))

    # 3c. Mutation: en blok uden metode skal være rød — ellers kan porten
    #     være grøn fordi den springer usagte claims over.
    tjek("dom 3 fanger en blok uden metode", har(dom_med(
        "<div><code>/api/profile</code></div>"
        "<pre><code>curl https://mahope.tools/api/profile?url=x</code></pre>"),
        "METHOD", "/api/profile"))

    # 4. Dom 4: siden mangler i listerne. Skal være rød i **begge**, så
    #    kontrollen ikke kan være grøn fordi den kun testede den ene.
    fund4 = dom_med("<pre><code>curl https://mahope.tools/api/profile?url=x</code></pre>",
                    i_listerne=False)
    tjek("dom 4 fanger en side uden for sitemap og llms.txt",
         len([f for f in fund4 if "LISTED" in f]) == 2, str(fund4))

    # 5. Mutation: hver dom skal kunne være den *eneste* røde. Så en fejl i
    #    porten ikke skjuler de andre tre.
    kun_dom4 = [f for f in dom_med(rigtig_main, i_listerne=False)
                if "LISTED" in f]
    tjek("kun dom 4 kan være rød", len(kun_dom4) == 2, str(kun_dom4))
    kun_dom1 = [f for f in dom_med(rigtig_main, i_manifestet=False) if "ROUTE:" in f]
    tjek("kun dom 1 kan være rød", len(kun_dom1) == 1, str(kun_dom1))

    # 6. Mutation: et `GET` i en *anden* kodeblok må ikke tælle med som dom 3
    #    for denne rute. Det er den fælde porten er skrevet for at undgå.
    tjek("GET i en anden blok tæller ikke med for clean-copy",
         not har(dom_med(
             '<div><code>/api/profile</code> <span class="method">GET</span></div>'
             '<pre><code>curl "https://mahope.tools/api/profile?url=x"</code></pre>'
             "<pre><code>curl -X POST https://mahope.tools/api/clean-copy</code></pre>"),
             "METHOD"))

    # 7. Mutation: den rigtige sides `<main>` skal være grøn. Uden den er
    #    porten værdiløs, fordi den kan ikke skelne fejl fra rigtighed.
    fund7 = dom_med(rigtig_main)
    tjek("den rigtige side er grøn", fund7 == [], str(fund7)[:300])

    # 8. Mutation: alle fire domme skal kunne være røde på én gang, så de er
    #    uafhængige og ikke en fejl der dækker over resten.
    alle_røde = dom_med(
        "<pre><code>curl https://mahope.tools/api/profil?url=x</code></pre>",
        i_manifestet=False, i_listerne=False)
    tjek("alle fire domme kan være røde samtidig",
         har(alle_røde, "ROUTE:", ROUTE)
         and har(alle_røde, "ENDPOINT", "/api/profil")
         and len([f for f in alle_røde if "LISTED" in f]) == 2,
         str(alle_røde))

    # 9. Mutation: dom 4 skal være rød på det felt den første udgave af siden
    #    sendte. Målt 3/10: `{"html":…,"format":"markdown"}` med løftet om
    #    `format:"text"`, mens workeren læser `body.mode === 'plain'`. Uden denne
    #    kontrol er dommen ubevidst — den kan være grøn på præcis den fejl den
    #    blev skrevet for.
    gammel_body = (
        '<div><code>/api/clean-copy</code> <span class="method">POST</span></div>'
        "<pre><code>curl -X POST https://mahope.tools/api/clean-copy \\\n"
        "  -H 'Content-Type: application/json' \\\n"
        "  -d '{\"html\":\"&lt;h1&gt;Hej&lt;/h1&gt;\",\"format\":\"markdown\"}'</code></pre>")
    fund9 = dom_med(gammel_body)
    tjek("dom 4 fanger et sendt felt handleren ikke læser",
         har(fund9, "FIELDS", "'format'"), str(fund9))
    tjek("dom 4 lader et læst felt være grønt",
         not har(dom_med(gammel_body.replace('"format":', '"mode":')), "FIELDS"),
         str(dom_med(gammel_body.replace('"format":', '"mode":'))))

    # 10. Mutation: et felt i *løbende tekst* er ikke et felt der sendes, så
    #     porten må ikke kræve at workeren læser det.
    tjek("dom 4 ser kun på det der sendes",
         not har(dom_med(
             '<div><code>/api/clean-copy</code> <span class="method">POST</span></div>'
             '<p>Send <code>html</code> and <code>mode</code>.</p>'
             '<pre><code>curl -X POST https://mahope.tools/api/clean-copy</code></pre>'),
             "FIELDS"))

    print(f"selftest: {'OK' if not fejl else 'RØD'} ({talt[0] - len(fejl)}/{talt[0]} kontroller)")
    for f in fejl:
        print(f"  - {f}")
    return 1 if fejl else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--list", action="store_true", help="vis kun fundene")
    ap.add_argument("--self-test", action="store_true", help="kør portens egen selftest")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    fund = dom(ROOT)
    if args.list:
        for f in fund:
            print(f)
        return 1 if fund else 0
    if fund:
        print(f"check-developers-page: RØD — {len(fund)} fund")
        for f in fund:
            print(f"  - {f}")
        return 1
    antal = len(ruter_i_main((SITE / SIDE).read_text(encoding="utf-8", errors="replace")))
    print(f"check-developers-page: GRØN — {ROUTE} dokumenterer {antal} "
          f"API-ruter, alle findes i workeren med den rigtige metode, hvert sendt "
          f"felt læses af handleren, og siden står i sitemap + llms.txt")
    return 0


if __name__ == "__main__":
    sys.exit(main())