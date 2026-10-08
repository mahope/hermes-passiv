#!/usr/bin/env python3
"""Dom den første handling over folden på de sider, der har trafik.

Målt 30/9: `/blog/text-on-image-contrast-check` var Mahope.tools' mest besøgte
side i 28 dage (8 af 15 besøgende) med 100 % bounce. Årsagen lå i folden: heroens
`btn-primary` var «See how it works» — et anker ned i artiklen — mens selve
værktøjet var `btn-secondary`. Lige under `</header>` stod to mere `btn-primary`
(Den scanner-CTA og AI-CTA'en, indsat af `tools/add_top_cta_495.py` og
`tools/add_ai_cta.py`), så læseren mødte tre ens knapper hvoraf ingen gav det
han kom for. Samme måling over hele `site/`: **182 af de 224 sider med en hero
har 2–3 `btn-primary` over folden**, og på mange af dem er heroens egen primære
et anker (`#content`, `#how`, `#checklist`) frem for det værktøj, siden handler om.

Samme fejlform som den betalte port fangede, på den gratis side: en side *har*
en købsvej, men vejen til den er den, læseren skal finde. Ratchetet her er derfor
per *rute med forventet destination* og ikke per rute, så en ombytning af to
`href` bliver rød — ellers ville porten være grøn fordi siden stadig har en
primær handling, bare den forkert.

**Tallene står ikke i denne tekst — de måles i hver kørsel.** Antallet af
banner-sider, af bannerknapper og af sider med nul `btn-primary` står i portens
egen afregning, fordi et tal skrevet her forældedes med næste artikel. En måling
med dato («Målt 4/10») er derimod en *registreret* kendsgerning og bliver
stående. Læs dem i den linje porten skriver til sidst — den kommer kun uden
`--list`, der viser den ratchetede fil og dens grunde.

**Hvad porten dømmer, og hvad den kun tæller.** Den dømmer to ting. (1) De
sider, der står i `tools/first_action.json`: præcis én `btn-primary` i
foldregionen, den skal være regionens første link, og den skal pege på den
ratchetede rute. (2) **Alle sider med et `blog-tool-cta`-banner**, uanset
om de står i ratchetfilen: et banner må aldrig være primært. Målt 4/10 var det
**330 bannerknapper** der råbte lige så højt som sidens egen handling, fordelt
over de banner-sider porten selv tæller, fordi `add_top_cta_495.py`,
`add_ai_cta.py` og `add_hero_cta.py` alle skrev en `btn-primary` ind i
bannerne. Bannerne bliver liggende — det er Mads' beslutning om promen (se ❓)
— men de taler kun en gang, som det sekundære de er.

De øvrige sider **tælles** og skrives ud i hver kørsel: de med nul `btn-primary`
i folden er enten `noindex`-sider, en side der kræver en nøgle, eller en side
hvor den primære ligger 2 px under folden. Hver af dem er målt enkeltvis i
`IMPLEMENTATION_PLAN.md`.

    python3 tools/check_first_action.py            # dom de ratchetede sider
    python3 tools/check_first_action.py --apply    # demotér bannerne i site/
    python3 tools/check_first_action.py --list     # hvad der er dømt, og hvorfor
    python3 tools/check_first_action.py --self-test
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
RATCHET = ROOT / "tools" / "first_action.json"

HERO_RE = re.compile(
    r'<div class="hero"[^>]*>(.*?)\n</div>|<header class="hero"[^>]*>(.*?)</header>',
    re.S)
BANNER_RE = re.compile(r'<div class="blog-tool-cta(?: ai-cta)?">.*?</div>', re.S)
TOKEN_RE = re.compile(
    r"<a\b([^>]*)>|<form\b([^>]*)>|(</form\s*>)|<button\b([^>]*)>", re.S)
HREF_RE = re.compile(r'href="([^"]*)"')
ACTION_RE = re.compile(r'action="([^"]*)"')
TYPE_RE = re.compile(r'type="([^"]*)"')
CLASS_RE = re.compile(r'class="([^"]*)"')


def fold_region(html: str) -> str:
    """Alt hvad en læser ser på første skærm: heroen og de CTA-bannere der
    ligger mellem `</header>` og det første `<section>`.

    Bannerne tæller med, fordi de *er* over folden — de er bare ikke i heroen.
    En port der kun læste `<header>` ville have sagt grøn på præcis den side,
    der har tre knapper oven på folden.
    """
    match = HERO_RE.search(html)
    if match is None:
        return ""
    region = match.group(1) or match.group(2) or ""
    rest = html[match.end():]
    stop = rest.find("<section")
    for banner in BANNER_RE.findall(rest if stop == -1 else rest[:stop]):
        region += banner
    return region


def handlinger(region: str) -> list[tuple[str, str]]:
    """`(destination, klasser)` for hver handling i foldregionen i rækkefølge.

    En `<a>` er en handling, og det er en `<button type="submit">` også: et URL-
    felt i heroen med knappen «Tjek nu» *er* læserens første handling, og det er
    den bedre end et anker der kun flytter læseren ned til den. 8/10 blev CI rød
    på fire sider, fordi porten så `0 btn-primary` og sagde «foldregionen findes
    ikke», selv om folden stod der med det hele. Destinationen er
    formularet `action`, så knappen dømmes mod ratchetets rute ligesom et link.
    """
    fund: list[tuple[str, str]] = []
    handling = ""
    for match in TOKEN_RE.finditer(region):
        link, form, lukket, knap = match.groups()
        if form is not None:
            action = ACTION_RE.search(form)
            handling = action.group(1) if action else ""
        elif lukket is not None:
            handling = ""
        elif link is not None:
            href = HREF_RE.search(link)
            if href is None:
                continue
            klasser = CLASS_RE.search(link)
            fund.append((href.group(1), klasser.group(1) if klasser else ""))
        else:
            type_ = TYPE_RE.search(knap)
            # `type="button"` er en kontol i et script, ikke en handling, og en
            # knap uden `<form>` omkring sig har ingen destination at dømme mod.
            if not handling or (type_ and type_.group(1).lower() != "submit"):
                continue
            klasser = CLASS_RE.search(knap)
            fund.append((handling, klasser.group(1) if klasser else ""))
    return fund


def banner_fund(html: str) -> list[str]:
    """Fund i *alle* `blog-tool-cta`-bannerne på siden, folden eller ikke.

    Målt 4/10: `tools/add_top_cta_495.py`, `tools/add_ai_cta.py` og
    `tools/add_hero_cta.py` skrev hver især en `btn-primary` ind i bannerne, så
    **330 bannerknapper** råbte lige så højt som sidens egen handling — og de
    tre generatorer skrev igen, så en retning i `site/` alene
    var holdbar til næste kørsel. Reglen er derfor ikke «banneret ligger for
    højt» (det er enpromo Mads skal have sagt ja til, se ❓) men **«en banner er
    aldrig primær»**: bannerne bliver liggende, de taler bare kun en gang, som
    det sekundære de er.
    """
    fund: list[str] = []
    for banner in BANNER_RE.findall(html):
        for href, klasser in handlinger(banner):
            if "btn-primary" in klasser.split():
                fund.append(f"CTA-banneret har en btn-primary ({href}) — banneret "
                            f"er en promo, sidens egen handling skal være den "
                            f"eneste primære")
    return fund


def demotér_bannere(html: str) -> str:
    """Gør hver `btn-primary` i et banner til `btn-secondary`.

    Kun klassen ændres: `href`, `data-track`, teksten og rækkefølgen er
    uændrede, så bannerne er præcis de samme to tilbud som i dag.
    """
    def ret(banner: re.Match[str]) -> str:
        return banner.group(0).replace('class="btn-primary', 'class="btn-secondary'
                                       ).replace(' btn-primary', ' btn-secondary')
    return BANNER_RE.sub(ret, html)


def fejl_for(html: str, forventet: str) -> list[str]:
    """Alt der gør siden's første skærm uforståelig, som lister."""
    fund = banner_fund(html)
    region = fold_region(html)
    if not region:
        return fund + ["foldregionen findes ikke (ingen `<div class=\"hero\">` eller "
                       "`<header class=\"hero\">`)"]
    links = handlinger(region)
    primære = [href for href, klasser in links if "btn-primary" in klasser.split()]
    if len(primære) == 0:
        fund.append("ingen btn-primary i foldregionen")
    elif len(primære) > 1:
        fund.append(f"{len(primære)} btn-primary i foldregionen "
                    f"({', '.join(primære)}) — læseren skal selv vælge")
    if links and "btn-primary" in links[0][1].split() and len(primære) == 1:
        if links[0][0] != forventet:
            fund.append(f"første link er {links[0][0]}, ikke {forventet}")
    elif primære and forventet not in primære:
        fund.append(f"den primære handling er {primære[0]}, ikke {forventet}")
    # Målet skal også findes. Ratchetets formkontrol siger at handlingen er den
    # samme som sidste gang; den siger intet om at `#ankeret` stadig findes, og
    # et anker uden mål er en knap der flytter læseren ingen steder. Kun
    # `#`-destinationer — en rute (`/free-tools`) kan ikke dømmes her, fordi den
    # er en fil i `dist/`, ikke i kilden.
    if forventet.startswith("#") and f'id="{forventet[1:]}"' not in html:
        fund.append(f"handlingen peger på {forventet}, men siden har ingen "
                    f'`id="{forventet[1:]}"` — ankeret er dødt')
    return fund


PRO_TABEL_RE = re.compile(r'class="[^"]*\bpro-table\b')
SCRIPT_RE = re.compile(r"<script\b.*?</script>", re.S)
ID_RE = re.compile(r'id="([^"]*)"')
TAG_RE = re.compile(r"<[a-zA-Z][^>]*>")
HEADING_ID_RE = re.compile(r'<h[1-6]\b[^>]*\bid="([^"]*)"')


def pristabel(html: str) -> str | None:
    """Sektionens `id` for den gratis-mod-Pro-tabel, en læser kan se.

    `None` når siden ikke har en synlig sådan tabel. To slags tabeller er
    *ikke* i folden og skal derfor ikke dømmes af `dom_pris`:

    - en i en `<script>`-streng (`PRO_CARD` på værktøjssiderne), som bygges ind
      når læseren har fået et resultat, og
    - en i en `hidden` beholder (`#cc-pro` på `/contrast-checker`), der samme
      sted bliver vist.

    Det er præcis den tid missionen vil vise Pro på: «vis det der, hvor
    brugeren mangler det». At linke til den fra folden ville være at flytte
    den hen til det sted, hvor læseren endnu ikke har fået noget.

    Ellers er svaret sektionens `id`, og en tom streng når tabellen ligger i
    en sektion uden id — så kan folden ikke pege på den.

    **Sider uden `<section>`** (`/clean-copy-tool`) gav før 5/10 `None` herfra,
    altså «siden har ingen pristabel» — porten var altså grøn fordi den slet
    ikke kiggede, selv om tabellen står 12 400 tegn nede i markup. For dem er
    svaret det nærmeste overskrifts-id før tabellen (`<h2 id="free-vs-pro">`),
    og er der ikke ét, en tom streng: så kan folden ikke pege på den, og det
    skal dømmes som det.
    """
    markup = SCRIPT_RE.sub("", html)
    for match in PRO_TABEL_RE.finditer(markup):
        sektion = markup.rfind("<section", 0, match.start())
        if sektion == -1:
            # Samme `hidden`-tjek som nedenfor, men på den nærmeste åbne
            # tag før tabellen: `#cc-pro`-beholderen er en `<div>`.
            beholder = TAG_RE.findall(markup, 0, match.start())
            if beholder and "hidden" in beholder[-1]:
                continue
            mål = HEADING_ID_RE.findall(markup, 0, match.start())
            return mål[-1] if mål else ""
        åbning = markup.find(">", sektion)
        if "hidden" in markup[åbning + 1:match.start()]:
            continue
        mål = ID_RE.search(markup[sektion:åbning])
        return mål.group(1) if mål else ""
    return None


def fejl_pris(html: str, kilde: str) -> list[str]:
    """En synlig pristabel skal kunne nås fra folden, ellers er den 4 000
    tegn nede og læseren med 86 sekunder på forsiden finder den aldrig."""
    mål = pristabel(html)
    if mål is None:
        return []
    if not mål:
        return [f"{kilde}: siden viser en gratis-mod-Pro-tabel, men dens sektion "
                "har intet id, så ingen handling i folden kan nå den"]
    if f'href="#{mål}"' not in fold_region(html):
        return [f"{kilde}: pristabellen ligger i #{mål}, men ingen handling i "
                "foldregionen peger på den"]
    return []


def dom_pris() -> list[str]:
    """Prisreglen dømmer de ratchetede sider, der viser pristabellen synligt.

    Ratchetfilen er portens egen liste over *sider med trafik*, så kravet rammer
    de forsider, der faktisk bliver læst, og ikke alle 21 sider med en
    `.pro-table` i korpuset.
    """
    fund: list[str] = []
    for kilde in ratchet():
        fil = ROOT / kilde
        if not fil.exists():
            continue
        fund.extend(fejl_pris(fil.read_text(encoding="utf-8", errors="replace"), kilde))
    return fund


def ratchet() -> dict[str, str]:
    data = json.loads(RATCHET.read_text(encoding="utf-8"))
    return {k: v for k, v in data.items() if not k.startswith("_")}


def dom_bannere(site: Path | None = None) -> list[str]:
    """Bannerreglen dømmer *alle* sider med et banner, ikke kun de ratchetede.

Siderne med banner er ingen port holdt i en håndfærdet liste: de er
    fundet ved at læse `site/`, så en ny artikel arver reglen uden at nogen
    skulle huske at føje den ind. Det er hele pointet — de tre generatorer gav
    alle sammen 330 primære bannerknapper, og en port der kun dømmer de
    ratchetede sider ville have været grøn hele vejen.
    """
    rod = (site or SITE).resolve()
    fund: list[str] = []
    for fil in sorted(rod.rglob("*.html")):
        kilde = fil.relative_to(rod.parent)
        for p in banner_fund(fil.read_text(encoding="utf-8", errors="replace")):
            fund.append(f"{kilde}: {p}")
    return fund


def demotér() -> int:
    """Sæt `btn-primary` → `btn-secondary` i hvert banner, og fortæl hvor mange."""
    rørte = 0
    for fil in sorted(SITE.rglob("*.html")):
        src = fil.read_text(encoding="utf-8", errors="replace")
        dst = demotér_bannere(src)
        if dst == src:
            continue
        fil.write_text(dst, encoding="utf-8")
        rørte += 1
    print(f"first-action: demoterede bannerne på {rørte} sider")
    return 0


def dom() -> tuple[list[str], dict[str, list[str]]]:
    fund: list[str] = []
    detaljer: dict[str, list[str]] = {}
    for kilde, forventet in ratchet().items():
        fil = ROOT / kilde
        if not fil.exists():
            fund.append(f"{kilde}: filen findes ikke, så folden kan ikke dømmes")
            detaljer[kilde] = ["filen findes ikke"]
            continue
        problemer = fejl_for(fil.read_text(encoding="utf-8", errors="replace"), forventet)
        detaljer[kilde] = problemer
        fund.extend(f"{kilde}: {p}" for p in problemer)
    return fund, detaljer


def maalt_uden_domslutning() -> tuple[int, int, int]:
    """`(sider med hero, sider med >1 primær over folden, sider med 0 primære)`."""
    med_hero = flere = nul = 0
    for fil in sorted(SITE.rglob("*.html")):
        html = fil.read_text(encoding="utf-8", errors="replace")
        if not fold_region(html):
            continue
        med_hero += 1
        primære = [h for h, k in handlinger(fold_region(html))
                   if "btn-primary" in k.split()]
        if len(primære) > 1:
            flere += 1
        elif not primære:
            nul += 1
    return med_hero, flere, nul


def self_test() -> int:
    fejl: list[str] = []
    antal = 0

    def tjek(navn: str, sand: bool, detalje: str = "") -> None:
        nonlocal antal
        antal += 1
        if not sand:
            fejl.append(f"{navn}{': ' + detalje if detalje else ''}")

    hero = ('<header class="hero"><div class="hero-cta">'
            '<a href="{a}" class="btn-primary">Værktøjet</a>'
            '<a href="#how" class="btn-secondary">Se hvordan</a>'
            "</div></header>")
    # 1. Rettet form: værktøjet er den primære og det første link.
    tjek("rettet fold er grøn", not fejl_for(hero.format(a="/tool"), "/tool"))
    # 2. Den fundne fejlform: primæren er et anker, værktøjet er sekundær.
    ombyttet = hero.format(a="/tool").replace(
        '<a href="/tool" class="btn-primary">Værktøjet</a>'
        '<a href="#how" class="btn-secondary">Se hvordan</a>',
        '<a href="#how" class="btn-primary">Se hvordan</a>'
        '<a href="/tool" class="btn-secondary">Værktøjet</a>')
    tjek("anker som primær er rød", bool(fejl_for(ombyttet, "/tool")))
    # 3. To banner-knapper over folden er to valg, ikke én handling.
    med_banner = (hero.format(a="/tool") +
                  '<div class="blog-tool-cta"><span class="btc-label">Tjek en side:</span>'
                  ' <a href="/scan" class="btn-primary">Scanner</a></div>'
                  '<section><h2>Brødtekst</h2></section>')
    fund = fejl_for(med_banner, "/tool")
    tjek("banner over folden tæller med", any("2 btn-primary" in f for f in fund), str(fund))
    # 3b. Samme banner som *sekundær* er grøn, og bannerreglen skal kun se
    #     klassen: destination, `data-track` og rækkefølge er ikke hendes.
    banner_sekundær = med_banner.replace('class="btn-primary">Scanner',
                                         'class="btn-secondary">Scanner')
    fund = fejl_for(banner_sekundær, "/tool")
    tjek("banner som sekundær er grøn",
         not fund and not banner_fund(banner_sekundær), str(fund))
    # 3c. Bannerreglen gælder hele siden, ikke kun folden. En banner der er
    #     flyttet ned i artiklen skal stadig ikke råbe højest — ellers ville
    #     svaret på ❓ «skal banneren ligge over folden» være «ja, gør som
    #     porten siger», og så lå fixet i porten.
    nede_primær = (hero.format(a="/tool") + "<section><h2>Brødtekst</h2></section>"
                   '<div class="blog-tool-cta"><span class="btc-label">Tjek en side:</span>'
                   ' <a href="/scan" class="btn-primary">Scanner</a></div>')
    tjek("banner nede i artiklen er også rød",
         any("banneret er en promo" in f for f in banner_fund(nede_primær)),
         str(banner_fund(nede_primær)))
    # 3d. `demotér_bannere` skal fjerne fundet og intet andet: samme href,
    #     samme `data-track`, samme rækkefølge, og knappen *uden* banner
    #     må blive primær igen.
    ai_banner = ('<div class="blog-tool-cta ai-cta">'
                 '<a href="/compliance-ai" class="btn-primary ai-cta-link" '
                 'data-track="ai-cta">Se hvad vi udgiver gratis →</a></div>')
    demoteret = demotér_bannere(ai_banner)
    tjek("demoteringen rammer bannerens klasse og ikke mere",
         demoteret == ai_banner.replace('class="btn-primary',
                                        'class="btn-secondary')
         and not banner_fund(demoteret), demoteret)
    tjek("demoteringen rører ikke knapper uden for banner",
         demotér_bannere(hero.format(a="/tool")) == hero.format(a="/tool"))
    # 4. Samme banner *nede* i artiklen er ikke over folden og tæller ikke med i
    #    foldens tæller. (Den skal dog stadig være sekundær — det er kontrol 3c.)
    nede = (hero.format(a="/tool") + "<section><h2>Brødtekst</h2></section>"
            '<div class="blog-tool-cta"><span class="btc-label">Tjek en side:</span>'
            ' <a href="/scan" class="btn-secondary">Scanner</a></div>')
    tjek("banner under artiklen er grøn", not fejl_for(nede, "/tool"),
         str(fejl_for(nede, "/tool")))
    # 5. En ombytning af destinationerne skal være rød, også når der stadig
    #    er én primær handling — det er den fejl ratchet-per-rute ikke så.
    permutation = hero.format(a="/scan")
    tjek("forkert destination er rød",
         any("/scan" in f and "/tool" in f for f in fejl_for(permutation, "/tool")))
    # 5b. Handlingen skal pege på et `id`, der findes. Ratchetets formkontrol
    #     kan ikke se det: `#tool-heading` kan forsvinde fra siden ved en
    #     omdøbning, og så er knappen stadig grøn hos porten og død for
    #     læseren. Kun `#`-destinationer dømmes — en rute `/free-tools` er en
    #     fil i `dist/`, ikke i kilden.
    med_anker = hero.format(a="#tool-heading")
    fund = fejl_for(med_anker, "#tool-heading")
    tjek("dødt anker er rødt", any("ankeret er dødt" in f for f in fund), str(fund))
    med_mål = med_anker.replace("</header>",
                                '<h2 id="tool-heading">Værktøjet</h2></header>')
    tjek("levende anker er grønt", not fejl_for(med_mål, "#tool-heading"),
         str(fejl_for(med_mål, "#tool-heading")))
    # 6. En side uden hero kan ikke dømmes, og porten skal sige det.
    tjek("manglende hero er rød", bool(fejl_for("<p>ingen hero</p>", "/tool")))
    # 6c. 8/10: folden på fire forsider blev `<div class="hero" id="check">` da
    #     tjekket flyttede op i heroen, og `HERO_RE` krævede en *nøgne* `class`,
    #     så porten meldte «foldregionen findes ikke» på en side der havde en
    #     fold. 32 andre sider har en `style=` på heroen og var usynlige på
    #     samme måde. En attribut må ikke gøre en hero usynlig.
    med_attribut = hero.format(a="/tool").replace('<header class="hero">',
                                                  '<header class="hero" id="check">')
    fund = fejl_for(med_attribut, "/tool")
    tjek("hero med attribut er grøn", not fund, str(fund))
    tjek("hero med attribut er stadig dømt",
         bool(fejl_for(med_attribut, "/scan")), "mutationen slap igennem")
    # 6d. Samme fejlform med `<div>`: en URL-felt i heroen med knappen «Tjek
    #     nu» er læserens første handling. Destinationen er formularet `action`,
    #     så porten dømmer knappen mod ratchetets rute ligesom et link.
    formular = ('<div class="hero" id="check">\n'
                '  <form action="/api/url-inspect"><input name="url">'
                '<button type="submit" class="btn-primary">Tjek nu</button></form>\n'
                '  <div class="hero-cta"><a href="#install" class="btn-secondary">'
                'Installér</a></div>\n</div>')
    fund = fejl_for(formular, "/api/url-inspect")
    tjek("send-knap er foldens primære", not fund, str(fund))
    fund = fejl_for(formular, "/scan")
    tjek("send-knap mod forkert rute er rød",
         any("/api/url-inspect" in f for f in fund), str(fund))
    tjek("send-knap og link er to valg, ikke én handling",
         any("2 btn-primary" in f for f in fejl_for(
             formular.replace("</form>",
                              '<a href="/scan" class="btn-primary">Scanner</a></form>'),
             "/api/url-inspect")))
    kontrol = formular.replace('<button type="submit"', '<button type="button"')
    tjek("kontrolknap er ikke en handling",
         not any(h == "/api/url-inspect" for h, _ in handlinger(kontrol)),
         str(handlinger(kontrol)))
    tjek("knap uden formular har ingen destination",
         not any(h == "" for h, _ in handlinger(
             formular.replace('<form action="/api/url-inspect">', "").replace("</form>", ""))))
    # 6b. Prisreglen skal dømme en side *uden* `<section>` foran tabellen.
    #     5/10: `/clean-copy-tool` har sin gratis-mod-Pro-tabel under
    #     `<h2 id="free-vs-pro">`, og `pristabel()` returnerede `None` for den —
    #     så porten var grøn fordi den slet ikke kiggede, 12 400 tegn nede i
    #     markup. Uden denne kontrol er den fejlform tilbage, hver gang der
    #     fjernes en `<section>` fra en side.
    værktøj = (hero.format(a="#input-box")
               .replace('<a href="#how" class="btn-secondary">Se hvordan</a>',
                        '<a href="#free-vs-pro">Se Pro</a>')
               + '<h2 id="free-vs-pro">Free and Pro</h2>'
                 '<table class="compare pro-table"><tr><td>$0</td></tr></table>')
    tjek("pristabel uden <section> finder sit overskrifts-id",
         pristabel(værktøj) == "free-vs-pro", repr(pristabel(værktøj)))
    tjek("pristabel uden <section> kræver et foldlink",
         not fejl_pris(værktøj, "værktøj")
         and any("#free-vs-pro" in f for f in
                 fejl_pris(værktøj.replace('<a href="#free-vs-pro">', ""),
                           "værktøj")))
    skjult = værktøj.replace('<table class="compare pro-table">',
                            '<div hidden><table class="compare pro-table">') \
        .replace("</table>", "</table></div>")
    tjek("skjult pristabel er ikke i folden", pristabel(skjult) is None,
         repr(pristabel(skjult)))
    # 7. Ratchetfilen skal dømme hver kildefil, der står i den, og ingen anden.
    dømt = ratchet()
    tjek("ratchetets nøgler er kildefiler",
         all(k.startswith("site/") and (ROOT / k).exists() for k in dømt),
         str(sorted(dømt)))
    # 8. Målingen på den virkelige `site/` skal være grøn, ellers er 1-7 grønne
    #    fordi porten intet ser. Bannerreglen dømmer alle sider med banner, så den
    #    skal med her — ellers ville porten være grøn på dem alle.
    fund, _ = dom()
    fund += dom_bannere()
    fund += dom_pris()
    tjek("målingen på site/ er grøn", not fund, "; ".join(fund[:3]))
    # 9. Mutation mod de RIGTIGTE filer: bannerne flyttes op under `</header>`
    #    igen og demoteres, altså præcis den fejlform de otte artikler havde.
    #    Porten skal blive rød på den og grøn igen på den uændrede — ellers
    #    dømmer den ikke de sider, den påstår at dømme.
    with tempfile.TemporaryDirectory() as tmp:
        rod = Path(tmp)
        (rod / "tools").mkdir()
        (rod / "site").mkdir()
        for kilde in dømt:
            (rod / kilde).parent.mkdir(parents=True, exist_ok=True)
            (rod / kilde).write_text((ROOT / kilde).read_text(encoding="utf-8"), encoding="utf-8")
        (rod / "tools" / "first_action.json").write_text(
            json.dumps(dømt, ensure_ascii=False), encoding="utf-8")
        tjek("de rigtige filer er grønne i et rent udtræk", dom_med_rod(rod)[0] == [])

        muteret: list[str] = []
        for kilde in dømt:
            fil = rod / kilde
            src = fil.read_text(encoding="utf-8")
            banners = re.findall(r'<div class="blog-tool-cta(?: ai-cta)?">.*?</div>', src, re.S)
            if not banners:
                continue
            hoved, rest = src.split("</header>", 1)
            oppe = "".join(b.replace("btn-secondary", "btn-primary") for b in banners)
            fil.write_text(hoved + "</header>\n" + oppe + rest, encoding="utf-8")
            muteret.append(kilde)
        fejl_mut, _ = dom_med_rod(rod)
        mangler = [k for k in muteret
                   if not any(f.startswith(k + ":") for f in fejl_mut)]
        tjek(f"bannerne oppe igen er rødt på alle {len(muteret)} sider",
             muteret and not mangler,
             f"{len(muteret)} muteret, mangler: {mangler[:2]}, "
             f"fund: {'; '.join(fejl_mut[:2])}")
    # 10. Mutation: en syntetisk `site/` med den fundne fejlform skal være rød,
    #     også når porten kører fra en anden rod.
    with tempfile.TemporaryDirectory() as tmp:
        rod = Path(tmp)
        (rod / "site").mkdir()
        (rod / "tools").mkdir()
        (rod / "site" / "test.html").write_text(ombyttet, encoding="utf-8")
        (rod / "tools" / "first_action.json").write_text(
            json.dumps({"site/test.html": "/tool"}), encoding="utf-8")
        fejl_her, _ = dom_med_rod(rod)
        tjek("syntetisk side er rød", bool(fejl_her), str(fejl_her))
        (rod / "site" / "test.html").write_text(hero.format(a="/tool"), encoding="utf-8")
        tjek("rettet syntetisk side er grøn", dom_med_rod(rod)[0] == [])

    # 11. Bannerreglen skal dømme alle sider med banner, ikke kun de ratchetede.
    #     Derfor skal den være målt på et *rigtigt* udtræk af `site/` med én banner
    #     skudt tilbage til `btn-primary` — den mutation de tre generatorer gjorde
    #     330 gange målt 4/10, og som porten skal kunne se.
    with tempfile.TemporaryDirectory() as tmp:
        rod = Path(tmp) / "site"
        rod.mkdir(parents=True)
        med_banner = 0
        for fil in sorted(SITE.rglob("*.html")):
            src = fil.read_text(encoding="utf-8", errors="replace")
            if not BANNER_RE.search(src):
                continue
            dst = rod / fil.relative_to(SITE)
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_text(src, encoding="utf-8")
            med_banner += 1
        tjek(f"udtrækket af de {med_banner} articlesider er grønt",
             med_banner > 100 and not dom_bannere(rod),
             f"{med_banner} filer, {len(dom_bannere(rod))} fund")
        # Mutation: skyd den første bannerknap i udtrækket op til primær igen.
        mål = None
        for fil in sorted(rod.rglob("*.html")):
            src = fil.read_text(encoding="utf-8")
            banner = BANNER_RE.search(src)
            if banner and "btn-secondary" in banner.group(0):
                mål = fil
                src = src.replace(banner.group(0),
                                  banner.group(0).replace("btn-secondary", "btn-primary", 1),
                                  1)
                fil.write_text(src, encoding="utf-8")
                break
        fund_her = dom_bannere(rod)
        tjek("én primær banner i et rent udtræk er rød",
             mål is not None and len(fund_her) == 1
             and str(mål.relative_to(rod)) in fund_her[0] and "promo" in fund_her[0],
             f"mål={mål}, fund={fund_her[:2]}")

    # 12. Prisreglen: en synlig pristabel skal kunne nås fra folden. Tre fejlformer
    #     ad gangen — tabellen uden id, tabellen med id men uden link, og den
    #     rettede side — så reglen kan ikke være grøn fordi den intet ser.
    tabel = ('<table class="compare pro-table"><tr><td>Free</td>'
             "<td>Pro</td></tr></table>")
    uden_id = (hero.format(a="/tool") +
               "<section>" + tabel + "</section>")
    tjek("pristabel uden id er rød",
         any("intet id" in f for f in fejl_pris(uden_id, "site/test.html")),
         str(fejl_pris(uden_id, "site/test.html")))
    uden_link = hero.format(a="/tool") + '<section id="price">' + tabel + "</section>"
    tjek("pristabel med id men uden foldlink er rød",
         any("ingen handling i foldregionen" in f
             for f in fejl_pris(uden_link, "site/test.html")),
         str(fejl_pris(uden_link, "site/test.html")))
    med_id = (hero.format(a="/tool").replace("</header>",
                 '<a href="#price">Se hvad Pro tilføjer</a></header>') +
              '<section id="price">' + tabel + "</section>")
    tjek("pristabel nået fra folden er grøn", not fejl_pris(med_id, "site/test.html"),
         str(fejl_pris(med_id, "site/test.html")))
    # 12b. En pristabel i en `hidden` beholder eller i en script-streng er ikke
    #      i folden — den dukker op når læseren får et resultat — så reglen må
    #      ikke kræve et link til den. Det er de fire værktøjssiders pro-kort.
    skjult = (hero.format(a="/tool") +
              '<div id="pro" class="pro-card" hidden>' + tabel + "</div>")
    tjek("skjult pro-kort er ikke dømt", not fejl_pris(skjult, "site/test.html"),
         str(fejl_pris(skjult, "site/test.html")))
    tjek("pro-kort i en script-streng er ikke dømt",
         not fejl_pris(hero.format(a="/tool") + "<script>var C = '" + tabel
                       + "';</script>", "site/test.html"))

    for linje in fejl:
        print(f"  FEJL  {linje}")
    print(f"check-first-action-selftest: {'OK' if not fejl else 'RØD'}"
          f" ({antal - len(fejl)}/{antal} kontroller)")
    return 1 if fejl else 0


def dom_med_rod(rod: Path) -> tuple[list[str], dict[str, list[str]]]:
    """Som `dom()`, men mod en midlertidig rod — bruges af selftesten."""
    data = json.loads((rod / "tools" / "first_action.json").read_text(encoding="utf-8"))
    fund: list[str] = []
    for kilde, forventet in ((k, v) for k, v in data.items() if not k.startswith("_")):
        fil = rod / kilde
        if not fil.exists():
            fund.append(f"{kilde}: filen findes ikke")
            continue
        fund.extend(f"{kilde}: {p}" for p in
                    fejl_for(fil.read_text(encoding="utf-8"), forventet))
        fund.extend(fejl_pris(fil.read_text(encoding="utf-8"), kilde))
    return fund, {}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list", action="store_true",
                        help="vis hvad der er dømt, og hvorfor det er rødt")
    parser.add_argument("--self-test", action="store_true",
                        help="kør portens egen kontrol af sig selv")
    parser.add_argument("--apply", action="store_true",
                        help="demotér bannerne i `site/` (btn-primary → btn-secondary)")
    args = parser.parse_args(argv)
    if args.self_test:
        return self_test()
    if args.apply:
        return demotér()
    fund, detaljer = dom()
    fund += dom_bannere()
    fund += dom_pris()
    med_hero, flere, nul = maalt_uden_domslutning()
    if args.list:
        for kilde, forventet in sorted(ratchet().items()):
            problemer = detaljer.get(kilde, ["filen findes ikke"])
            tilstand = "GRØN" if not problemer else "RØD"
            print(f"  {tilstand}  {kilde} → {forventet}")
            for p in problemer:
                print(f"          {p}")
        return 1 if fund else 0
    for linje in fund:
        print(linje)
    dømt = len(ratchet())
    banner_filer = banner_knapper = 0
    for fil in SITE.rglob("*.html"):
        src = fil.read_text(encoding="utf-8", errors="replace")
        bannere = BANNER_RE.findall(src)
        if bannere:
            banner_filer += 1
        for banner in bannere:
            banner_knapper += len(handlinger(banner))
    print(f"\nfirst-action: {dømt} sider ratchetede + {banner_filer} sider med "
          f"banner dømt ({banner_knapper} bannerknapper), {len(fund)} problemer")
    if flere or nul:
        print(f"  kun talt, ikke dømt: {flere} af {med_hero} sider med en hero har "
              f"mere end én btn-primary over folden ({nul} har nul)")
    if fund:
        print("\nfirst-action: RØD")
        return 1
    print("first-action: GRØN")
    return 0


if __name__ == "__main__":
    sys.exit(main())
