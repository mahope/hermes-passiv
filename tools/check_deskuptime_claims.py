#!/usr/bin/env python3
"""Dommer de sider der udleverer den betalte DeskUptime-app mod tre løfter.

Baggrund (målt 4/10): to artikler om desktop-appen lovede begge, at intet
forlader maskinen — «Nothing is uploaded anywhere, ever» (EN) og «Intet
uploades nogensinde» (DA). Det var falsk, fordi appen aktiverer licensen
online, og de to produktsider siger det ærligt (CEO-kø punkt 2). Dertil kom
den fejl CEO-kø punkt 4 handler om: den engelske artikel udleverede de
**betalte** binære filer to gange og havde ingen købsvej, mens dens danske
tvilling havde både en gratis-mod-Pro-tabel og købsknappen. Målt før
rettelsen: 9 sider rørte DeskUptime, 8 havde købsknappen, og den eneste
undtagelse var præcis artiklen der voks mest i mapper.

Denne port dømmer hver side i `site/` der linker til en udleveret binær fil:

  1. **Den skal kunne købes.** En side der deler den betalte app ud uden et
     betalingslink sender læseren i en blindgade — han har hentet filen og
     kan ikke gøre noget ved den.
  2. **Den må ikke love, at intet forlader maskinen.** Den betalte app taler
     med en licensserver, så et absolut løfte er en løgn. Kun de helt
     konkrete formuleringer er i listen, så porten ikke kan gøre en ærlig
     sætning som «din URL-liste uploades ikke til en central
     monitoreringstjeneste» rød.
  3. **Den skal sige, hvad Pro giver.**mindst to af de fem navngivne
     Pro-funktioner skal stå i den synlige tekst, ellers er der ingen
     grund til at tro at gratis og betalt er forskellige.

Dom 1 og 3 er CEO-kø punkt 4 målt på den konkrete købsvej; dom 2 er CEO-kø
punkt 2.

**22/11-2026: salget af DeskUptime Pro er lukket** (`status: inactive` i
`tools/stripe_catalog.json`). Binærfilerne ligger der stadig til dem, der
allerede har en nøgle. Så længe produktet er lukket, er dom 1 vendt — siden må
*ikke* have købslinket (Stripe har deaktiveret det), og den skal sige at Pro
ikke sælges længere — og dom 3 gælder ikke, fordi der ikke er noget at sælge
på forskellen. Dom 2 gælder uændret. Kun synlig tekst dommes — JSON-LD og scripts er ikke noget en
besøgende læser.

Brug:
    python3 tools/check_deskuptime_claims.py            # dom
    python3 tools/check_deskuptime_claims.py --list     # de dømte sider
    python3 tools/check_deskuptime_claims.py --self-test
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"

# Den betalte apps binære filer. Den er det, der gør en side til en
# udleveringsside — ikke navnet «DeskUptime», der står i 40 artikler.
BINARY_RE = re.compile(
    r"releases/download/desktop-v[0-9.]+/(DeskUptime|Deskuptime)", re.IGNORECASE
)
# Købsknappen.samme Payment Link som `docs/stripe-kontrakt.md` og
# `tools/check_stripe_ctas.py` bruger, så et nyt link ikke kan glide fra
# porten uden at en af de to andre dør.
BUY_RE = re.compile(r"buy\.stripe\.com/7sY9AS9eX3Iu418fJ5bMQ01")

# Absolutte løfter om at intet forlader maskinen. Kun helt konkrete
# formuleringer: «uploads nothing» er ikke med, fordi det kan være sandt
# om en browserbaseret generator — dem dommer `check_generator_claims.py`.
FALSE_CLAIMS: tuple[tuple[str, str], ...] = (
    (r"Nothing is uploaded anywhere, ever", "EN «Nothing is uploaded anywhere, ever»"),
    (r"Nothing is ever uploaded", "EN «Nothing is ever uploaded»"),
    (r"Intet uploades nogensinde", "DA «Intet uploades nogensinde»"),
    (r"intet sendes nogeninde nogensinde", "DA «intet sendes nogeninde nogensinde»"),
)

# De fem Pro-funktioner, kontrakten og produktsiderne er enige om. Dom 3
# tæller hvor mange der står i den synlige tekst.
PRO_FEATURES: dict[str, re.Pattern[str]] = {
    "webhook-alarmer": re.compile(r"webhook", re.IGNORECASE),
    "30 sekunders interval": re.compile(r"30[ .]*(?:sekund|second)", re.IGNORECASE),
    "ubegrænsede sites": re.compile(r"(ubegr[æa]nsede|unlimited)\s+sites?", re.IGNORECASE),
    "kunderapport": re.compile(r"(kunderapport|client[- ]ready report)", re.IGNORECASE),
    "desktop-appen": re.compile(r"desktop[- ]app", re.IGNORECASE),
}
MIN_PRO_FEATURES = 2

# Lukket for salg: siden skal sige det i synlig tekst.
CLOSED_RE = re.compile(r"DeskUptime Pro (?:is no longer sold|sælges ikke længere)", re.IGNORECASE)


def sales_closed(catalog_path: Path | None = None) -> bool:
    path = catalog_path or ROOT / "tools/stripe_catalog.json"
    product = json.loads(path.read_text(encoding="utf-8"))["products"]["deskuptime-pro"]
    return product.get("status") == "inactive"

SCRIPT_RE = re.compile(r"<script\b.*?</script>", re.DOTALL | re.IGNORECASE)
STYLE_RE = re.compile(r"<style\b.*?</style>", re.DOTALL | re.IGNORECASE)
COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)


def visible_text(html: str) -> str:
    """Det en besøgende faktisk læser: ingen scripts, ingen CSS, ingen kommentarer."""
    text = SCRIPT_RE.sub(" ", html)
    text = STYLE_RE.sub(" ", text)
    text = COMMENT_RE.sub(" ", text)
    return re.sub(r"\s+", " ", text)


def pages() -> list[Path]:
    """Alle sider der uddeler en binær fil fra en release."""
    out: list[Path] = []
    for path in sorted(SITE.rglob("*.html")):
        html = path.read_text(encoding="utf-8", errors="replace")
        if BINARY_RE.search(html):
            out.append(path)
    return out


def judge_page(path: Path, html: str, closed: bool | None = None) -> list[str]:
    rel = path.relative_to(ROOT)
    problems: list[str] = []
    closed = sales_closed() if closed is None else closed
    seen = visible_text(html)
    if closed:
        if BUY_RE.search(html):
            problems.append(
                f"{rel}: har købslinket til DeskUptime Pro, som er lukket for salg "
                f"22/11-2026 — linket er deaktiveret i Stripe"
            )
        if not CLOSED_RE.search(seen):
            problems.append(
                f"{rel}: uddeler den betalte app uden at sige at DeskUptime Pro "
                f"ikke sælges længere — læseren kan ikke få en nøgle"
            )
    elif not BUY_RE.search(html):
        problems.append(
            f"{rel}: uddeler den betalte app, men har ingen købsknap "
            f"(Payment Link 7sY9AS9eX3Iu418fJ5bMQ01)"
        )
    for pattern, label in FALSE_CLAIMS:
        if re.search(pattern, seen, re.IGNORECASE):
            problems.append(
                f"{rel}: {label} — men licensen aktiveres online"
            )
    named = [name for name, rx in PRO_FEATURES.items() if rx.search(seen)]
    if not closed and len(named) < MIN_PRO_FEATURES:
        problems.append(
            f"{rel}: nævner {len(named)} af de {len(PRO_FEATURES)} Pro-funktioner "
            f"({', '.join(named) or 'ingen'}), så læseren ikke kan se hvad "
            f"betalt giver"
        )
    return problems


def judge() -> tuple[list[str], int]:
    judged = pages()
    problems: list[str] = []
    for path in judged:
        html = path.read_text(encoding="utf-8", errors="replace")
        problems.extend(judge_page(path, html))
    return problems, len(judged)


def self_test() -> int:
    """Porten skal kunne fejle: hver mutation forventer en rød dom."""
    target = SITE / "blog" / "get-notified-when-website-goes-down.html"
    original = target.read_text(encoding="utf-8")
    fails: list[str] = []

    def expect_green(name: str, html: str) -> None:
        problems = judge_page(target, html)
        if problems:
            fails.append(name)
            for p in problems[:3]:
                print(f"   {p}")
        else:
            print(f"ok {name}: grøn")

    def expect_red(name: str, html: str) -> None:
        if judge_page(target, html):
            print(f"ok {name} giver fund")
        else:
            fails.append(name)

    try:
        expect_green("uændret side", original)

        # Salget er lukket 22/11-2026: dom 1 er vendt, dom 3 gælder ikke.
        # 1a. Købsknappen kommer tilbage — rød.
        expect_red(
            "købsknappen til det lukkede produkt tilbage",
            original.replace(
                "</body>",
                '<a href="https://buy.stripe.com/7sY9AS9eX3Iu418fJ5bMQ01">Buy</a></body>', 1),
        )
        # 1b. Beskeden om at Pro ikke sælges længere forsvinder — rød.
        if not CLOSED_RE.search(original):
            fails.append("selftest: siden siger ikke at DeskUptime Pro ikke sælges længere")
        expect_red(
            "lukke-beskeden væk",
            CLOSED_RE.sub("DeskUptime Pro", original),
        )

        # 2. Det absolutte løfte kommer tilbage — dom 2. Kun i den synlige
        # tekst: står det i et script eller en kommentar, er det ikke en løgnene.
        expect_red(
            "løftet «uploaded anywhere, ever» tilbage i brødteksten",
            original.replace(
                "Your data stays yours",
                "Nothing is uploaded anywhere, ever. Your data stays yours",
                1,
            ),
        )
        expect_green(
            "samme streng i en kommentar dømmes ikke",
            original.replace(
                "</main>", "<!-- Nothing is uploaded anywhere, ever --></main>", 1
            ),
        )
        expect_red(
            "dansk løfte på en dansk side",
            original.replace(
                "Your data stays yours",
                "Intet uploades nogensinde. Your data stays yours",
                1,
            ),
        )

        # 3. Mens produktet blev solgt: uden købsknap og uden navngivne
        # Pro-funktioner er siden rød. Dømt med closed=False, så reglen
        # stadig er bevist, hvis salget åbner igen.
        if judge_page(target, original, closed=False):
            print("ok åben salgsperiode: siden uden købsknap giver fund")
        else:
            fails.append("åben salgsperiode: siden uden købsknap")
    finally:
        target.write_text(original, encoding="utf-8")

    total = 7
    print(f"\nselftest: {total - len(fails)}/{total}")
    if fails:
        print("FEJL: mutationer, porten ikke fangede: " + ", ".join(fails))
        return 1
    print("GRØN: porten kan fejle")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--list", action="store_true", help="print de dømte sider")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()
    problems, judged = judge()
    if a.list:
        for path in pages():
            print(path.relative_to(ROOT))
        return 0
    if problems:
        print("RØD — DeskUptime-udleveringssider mod tre løfter:\n", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        print(f"\n{len(problems)} fund på {judged} sider", file=sys.stderr)
        return 1
    if sales_closed():
        print(f"GRØN — {judged} sider der uddeler DeskUptime-binære filer, ingen "
              f"købsknap til det lukkede Pro, alle siger at det ikke sælges længere, "
              f"ingen absolutte løfter")
        return 0
    print(f"GRØN — {judged} sider der uddeler DeskUptime-binære filer, "
          f"alle med købsvej, ingen absolutte løfter, alle med Pro forklaret")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())