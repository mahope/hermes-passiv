#!/usr/bin/env python3
"""Flet relaterede artikler ind i en sides eksisterende værktøjsafsnit.

Deles af `crosslink_blog.py` (EN) og `crosslink_blog_da.py` (DA), for de to
havde hver deres kopi af den samme logik først — og en logik der findes to
steder, finder den ene fejl én gang. Samme grund som `site/net.js`.

Baggrund (30/9): 62 sider havde to afsnit med samme job, «Tools and guides»
med et kortgitter og «Related Guides» med en liste. 36 af de relaterede links
pegede på en destination siden allerede viste i sit eget gitter, så
`/blog/text-on-image-contrast-check` — den mest besøgte artikel på mahope.tools
— nåede læseren med `/blog/wcag-contrast-checker` to gange under to navne.
`tools/check_tool_sections.py` dømmer det; her er den side af loven der skriver
rigtigt.

To former af værktøjsafsnit findes i `site/`, og begge flettes:

* **kortgitter** — `<h2>Tools and guides</h2><div class="problem-cards">…`
  Et nyt kort pr. relateret artikel. Findes destinationen allerede, bærer
  *det* kort beskrivelsen i stedet, så læseren møder den ene destination med
  den fulde forklaring.
* **inline-`<p>`** — `<h2>Tools and guides</h2><p><a …>…</a> · …</p>`
  Nye links flettes ind i afsnittet.

En side uden værktøjsafsnit får uændret den gamle boks; det er 49 EN- og 78 DA
sider, og de skal have den.
"""
from __future__ import annotations

import html as htmllib
import re

MARKER_EN = "<!-- crosslink-related -->"
MARKER_DA = "<!-- crosslink-related-da -->"
TOOLS_H2_EN = "<h2>Tools and guides</h2>"
TOOLS_H2_DA = "<h2>Værktøjer og guides</h2>"
GITTER_RE = re.compile(r'<div class="problem-cards">')
KORT_RE = re.compile(r'<div class="card">.*?</div>', re.S)
LINK_RE = re.compile(r'href="([^"]+)"')


def gitter_slut(html: str, fra: int) -> int:
    """Index forbi `<div class="problem-cards">`'s egen `</div>`.

    Tæller `<div`/`</div>` i stedet for at søge på den næste linje: kortene er
    på hver sin linje, så et linjeskift peger på gitterets *åbning* og ikke på
    hvor det lukker.
    """
    dybde = 0
    for m in re.finditer(r"<div\b|</div>", html[fra:]):
        dybde += 1 if m.group(0) != "</div>" else -1
        if dybde == 0:
            return fra + m.end()
    raise AssertionError("problem-cards er ikke lukket")


def nyt_kort(href: str, title: str, short: str) -> str:
    """Et kort i samme sprog som de kort gitteret allerede har.

    Intet badge: et badge er en kategori, og kategorien for et relateret indlæg
    er opfundet. Kortet er kendeligt ved sin beskrivelse, og `.card h3` +
    `.card p` er erklæret i `site/style.css`, så det ligner de øvrige kort.
    """
    return (
        f'<div class="card"><h3><a href="{href}" '
        f'style="color:var(--color-accent);text-decoration:none;">'
        f'{htmllib.escape(title)}</a></h3>'
        + (f'<p>{htmllib.escape(short)}</p>' if short else '')
        + '</div>'
    )


def flet_i_gitter(html: str, items: list[tuple[str, str, str]]) -> str:
    """Læg `items` ind i `<h2>Tools and guides</h2>`'s gitter, uden dubletter."""
    h2 = html.find(TOOLS_H2_EN)
    if h2 == -1:
        h2 = html.find(TOOLS_H2_DA)
    gitter = GITTER_RE.search(html, h2)
    slut = gitter_slut(html, gitter.start())
    kortene = html[gitter.end():slut - len("</div>")]

    nye = []
    for href, title, short in items:
        hvilket = next((k for k in KORT_RE.findall(kortene) if f'href="{href}"' in k), None)
        if hvilket is None:
            # Destinationen er ikke i gitteret: et nyt kort.
            nye.append(nyt_kort(href, title, short))
            continue
        # Destinationen er allerede et kort. Beskrivelsen hænger på kortet, så
        # læseren møder den ene destination med den fulde forklaring i stedet
        # for at møde den igen ti linjer længere nede under et andet navn.
        if not short or "<p>" in hvilket:
            continue
        ny = (hvilket[:hvilket.rfind("</div>")]
              + f"<p>{htmllib.escape(short)}</p></div>")
        kortene = kortene.replace(hvilket, ny, 1)

    if nye:
        kortene = kortene.rstrip() + "\n      " + "\n      ".join(nye) + "\n    "
    return html[:gitter.end()] + kortene + html[slut - len("</div>"):]


def flet_i_inline(html: str, items: list[tuple[str, str, str]]) -> str:
    """Læg `items` ind i den `<p>` med inline-links under værktøjsoverskriften."""
    h2 = html.find(TOOLS_H2_EN)
    if h2 == -1:
        h2 = html.find(TOOLS_H2_DA)
    p = re.compile(r"<p>(?:(?!</p>).)*</p>", re.S).search(html, h2)
    assert p, "værktøjsafsnit uden gitter og uden <p> — formen er ukendt"
    afsnit = p.group(0)
    nye = [f'<a href="{href}" style="color:var(--color-accent);">'
           f"{htmllib.escape(title)}</a>" for href, title, _ in items
           if f'href="{href}"' not in afsnit]
    if not nye:
        return html
    ny = (afsnit[:afsnit.rfind("</p>")] + " &middot;\n"
          + " &middot;\n".join(nye) + "</p>")
    return html[:p.start()] + ny + html[p.end():]


def fjern_boks(html: str, marker: str) -> str:
    """Tag markeringskommentaren og kassen ud, hvis de er der."""
    start = html.find(marker)
    if start == -1:
        return html
    slut = html.find("</div>", html.find("</ul>", start))
    assert slut != -1, f"kunne ikke finde slut på gammel boks ({marker})"
    return html[:start] + html[slut + len("</div>"):].lstrip("\n")


def afkort(tekst: str, max_tegn: int = 110) -> str:
    """Første sætning, afkortet på et **ord** med en enkelt ellipse.

    `crosslink_blog.py` skrev «case conver….» — punktum bag en afkortet sætning,
    fire tegn i træk der læses som en skrivefejl. Afkortningen sker på et ord,
    for en halv linje i et kortgitter læses som en fejl, og de samme
    beskrivelser stod nu som kortbeskrivelse lige under en heltitel.
    """
    short = tekst.split(". ")[0].rstrip(".") if tekst else ""
    # **Ingen tal i et uddrag.** Uddraget er en genfortælling af *en anden*
    # articles beskrivelse, og et tal i det er et løfte den side ikke kan
    # svare for. Målt 30/9: `crosslink_blog_da.py` gav
    # `da/blog/gratis-compliance-tjek-hjemmeside` beskrivelsen af
    # desktop-scanneren med «Kør alle 22 WCAG 2.1 AA-regler lokalt på din
    # maskine» — på en side om den *online* tjekker. `check_rule_claims` blev
    # rød, og den har ret: siden sælger webkernen, ikke den app der kører de
    # 22 regler. Samme fejlform som et gammelt løfte på en forkert side, så
    # reglen er den samme: et tal skal kun stå på den side der kan måle det.
    # Resten af sætningen er stadig nok til at læseren genkender artiklen.
    if any(tal.isdigit() for tal in short.split()):
        return ""
    if len(short) > max_tegn:
        short = short[:max_tegn].rstrip()
        if " " in short:
            short = short[:short.rindex(" ")]
        return short.rstrip(" .,;:") + "…"
    return short.rstrip(".") + "."


def relaterede_kort(paras: dict[str, tuple[str, str]], valgte: list[str],
                    præfiks: str = "/blog/") -> list[tuple[str, str, str]]:
    """`(href, titel, afkortet beskrivelse)` for de valgte artikler.

    Beskrivelsen kan være tom, når den indeholder et tal — se `afkort`. Så
    skriver kortet kun titlen, som altid er artiklens egen `<h1>`.
    """
    return [(f"{præfiks}{r}", paras[r][0], afkort(paras[r][1])) for r in valgte[:3]]
