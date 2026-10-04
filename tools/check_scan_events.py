#!/usr/bin/env python3
"""Dom at scannerens købsvej kan måles — og at den ikke tæller dobbelt.

**Hullet, målt 5/10 i `site/scan.html` og `site/scan-da.html`.** Den frie
scanner på `/scan` er den eneste vej ind til den dyreste linje i huset
(EUComply Pro, $79/år pr. website), og den havde **to** problemer der modsatte
sig hinanden:

1. **Dobbelt tælling.** `scan()` sendte `scan` ved *start* (linje 356) og
   sendte den **igen** med en rå `fetch('/api/track', … event:'scan')` lige
   efter et vellykket svar. Én scanning blev to begivenheder, så ethvert tal
   over `scan` var for højt — præcis den fejl sletningen i `IMPLEMENTATION_PLAN.md`
   beskriver som farligere end et Produkt uden interesse.
2. **Ingen udfald.** Der var ingen begivenhed ved *resultatet*, så en besøgende
   der trykkede Scan og fik et svar med 40 fund, en der fik «ingen problemer»,
   og en hvis scanning kastede fejl så alle tre ud som det samme `scan`. Med
   290 indgående links målt 1/10 kunne en indgående link overhovedet ikke
   skelnes fra et køb, og pro-kortets knap sendte intet ud over den generiske
   `buy-click` fra `site/track.js:225`.

**Reglen her er derfor skrevet på hele tragten, ikke på de to linjer.** Fire
begivenheder, som `handleTrack` i `site/_worker.js` tæller som
`/scan@<event>` og `/scan-da@<event>`:

| Begivenhed | Betydning | Hvor |
|---|---|---|
| `scan` | forsøget — nogen trykkede Scan | starten af `scan()` |
| `scan-findings` | udfald med mindst ét fund | `render()` |
| `scan-clean` | udfald med nul fund | `render()` |
| `scan-failed` | scanningen kunne ikke gennemføres | `catch` i `scan()` |
| `pro-card-click` | pro-kortets købsknap | købsankerne i `proCard()` |

`pro-card-click` er **ikke** en erstatning for `buy-click`: den tælles
stadig, fordi den er en rigtig bevægelse mod Stripe. Den er en ekstra
målepunkt på præcis det sted, hvor den betalte værdi tilbydes, så en
indgående link, en donation og en Pro-købsknap kan læses hver for sig.

**Den delte rapport tæller ikke.** En læser der åbner
`/scan#<hash>` kører ingen scanning — det er afsenderens resultat, der
vises. Derfor udsender `render()` kun udfaldet når `opts.shared` er falsk, og
porten dømmer netop den vagt.

Begivenhedsnavnene skal matche `handleTrack`s egen regex
`/^[a-z0-9-]+$/` (`site/_worker.js:1875`) — ellers svarer `/api/track` med
**400** og tallene er ikke bare forkerte, de er væk. Porten læser den regex
i workeren i stedet for at have sin egen, så en ændring derude låser porten
i stedet for at gøre den grøn på en løgn.

Begge sprog dømmes, og de skal sende **de samme** navne: en dansk side der
sender `scan-fund` deler tragten i to, og så kan hverken side tælles
samlet eller sammenlignes.

    python3 tools/check_scan_events.py
    python3 tools/check_scan_events.py --self-test
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROD = Path(__file__).resolve().parent.parent
SIDER = ("site/scan.html", "site/scan-da.html")
WORKER = ROD / "site/_worker.js"

# Navnene i `handleTrack`. Findes ikke i workeren, er det en rigtig fejl at
# porten ikke kan dømme mod — aldrig en grund til at tro på egne navne.
NAVN_REGEX = "/^[a-z0-9-]+$/"

# Ét kald pr. sted. Tælles på tværs af whitespace, så en omformatering ikke
# skjuler en dublet. `KALD_LOOSE` fanger navne med tegn uden for alfabetet,
# så de kan dømmes imod `handleTrack`s egen regex.
KALD = r"trackEvent\(\s*'([a-z0-9-]+)'\s*\)"
KALD_LOOSE = r"trackEvent\(\s*'([^']*)'\s*\)"
RÅ_FETCH = r"event\s*:\s*'scan'"
RÅ_UDFALD = re.compile(
    r"trackEvent\(\s*state\.findings\.length\s*\?\s*'([a-z0-9-]+)'\s*:\s*'([a-z0-9-]+)'\s*\)"
)
# Nøjagtig den attribut, pro-kortets købsknap har. Lavet som en konstant, så
# mutationen ikke kan ramme en streng, der ikke findes i filen — det gjorde
# selftesten rød på en mutation, der aldrig skete.
PRO_KORT_KALD = r''' onclick="window.trackEvent&&window.trackEvent(\'pro-card-click\')"'''


def _linjer(kilde: str) -> list[str]:
    return kilde.splitlines()


def dom(kilde: str, filnavn: str = "") -> list[str]:
    """Alle fund i én scannerkilde. `filnavn` hænger på hver linje."""
    fund: list[str] = []
    linjer = _linjer(kilde)
    sti = f"{filnavn}: " if filnavn else ""

    def sig(tal: int, tekst: str) -> None:
        fund.append(f"{sti}linje {tal}: {tekst}")

    # 1. Præcis ét `scan`-kald. Før var der to: `trackEvent('scan')` ved
    #    starten og den rå fetch bagefter.
    skanninger = [i for i, l in enumerate(linjer, 1) if re.search(KALD.replace("([a-z0-9-]+)", "scan"), l)]
    if len(skanninger) != 1:
        fund.append(f"{sti}skal sende 'scan' præcis 1 gang, gør {len(skanninger)} "
                    f"(linje {', '.join(map(str, skanninger)) or 'ingen'})")

    # 2. Ingen rå `event:'scan'`-fetch. Det var den dobbelte tælling.
    for i, l in enumerate(linjer, 1):
        if re.search(RÅ_FETCH, l):
            sig(i, "sender 'scan' med en rå fetch — den tæller den samme "
                   "scanning igen. Ét kald pr. scanning.")

    # 3. Udfaldet. Navnene skal være præcis de to, og de skal vælges på
    #    `state.findings.length`, så et resultat uden fund ikke tælles som
    #    et resultat med fund.
    udfald = [(i, m) for i, l in enumerate(linjer, 1) for m in [RÅ_UDFALD.search(l)] if m]
    if len(udfald) != 1:
        fund.append(f"{sti}skal vælge ét udfald på state.findings.length, "
                    f"finder {len(udfald)}")
    else:
        i, m = udfald[0]
        fund_og_rent = {m.group(1), m.group(2)}
        if fund_og_rent != {"scan-findings", "scan-clean"}:
            sig(i, f"udfaldet sender {sorted(fund_og_rent)}, forventet "
                   f"['scan-clean', 'scan-findings']")
        # 4. Vagten på delte rapporter. Uden den tæller hvert delt link et
        #    udfald, der afsenderens scanner aldrig kørte.
        linje = linjer[i - 1]
        if "!opts.shared" not in linje:
            sig(i, "udfaldet mangler vagten `!opts.shared` — en delt rapport "
                   "er afsenderens resultat, ikke læserens")

    # 5. Fejlvejen skal sige fra. Uden den er en bruger der fik «Scan failed.»
    #    målt som en bruger der fik et resultat.
    fejlet = [i for i, l in enumerate(linjer, 1) if re.search(KALD.replace("([a-z0-9-]+)", "scan-failed"), l)]
    if len(fejlet) != 1:
        fund.append(f"{sti}skal sende 'scan-failed' præcis 1 gang i fejlvejen, "
                    f"gør {len(fejlet)}")

    # 6. Pro-kortets købsknap skal måle sig selv — på knappen, ikke et sted
    #    på siden. Derfor lægges kravet på den linje der har betalingslinket.
    køb = [i for i, l in enumerate(linjer, 1) if "buy.stripe.com" in l]
    if not køb:
        fund.append(f"{sti}pro-kortet har ingen købsknap (intet buy.stripe.com)")
    for i in køb:
        linje = linjer[i - 1]
        if "pro-card-click" not in linje:
            sig(i, "købsknappen sender ikke 'pro-card-click'")
        if "trackEvent" not in linje:
            sig(i, "'pro-card-click' står på knappen uden et trackEvent-kald")

    # 7. Polaritet: donationsknappen er ikke et pro-kort. Den deler den
    #    generiske `buy-click`, og den skal ikke få pro-kortets begivenhed.
    for i, l in enumerate(linjer, 1):
        if "donate.stripe.com" in l and "pro-card-click" in l:
            sig(i, "donationslinket har fået 'pro-card-click'")

    # 8. Ethvert navn skal være et navn `handleTrack` accepterer. Ellers
    #    svarer `/api/track` med 400, og målet er ikke bare forkeret — det er
    #    væk. Derfor dømmes her imod den regex, porten læser i workeren.
    for i, l in enumerate(linjer, 1):
        for navn in re.findall(KALD_LOOSE, l):
            if not re.fullmatch(NAVN_REGEX.strip("/"), navn):
                sig(i, f"'{navn}' afvises af handleTrack med 400")

    return fund


def _selftest() -> int:
    fejl: list[str] = []
    kørte = 0

    def tjek(navn: str, sand: bool, detalje: str = "") -> None:
        nonlocal kørte
        kørte += 1
        print(f"  {'ok  ' if sand else 'FAIL'} {navn}{'' if sand else '  ' + detalje}")
        if not sand:
            fejl.append(navn)

    # 1. De rene filer skal være grønne — ellers lå porten i gaten og rødmer
    #    deploys for en fejl, der ikke findes.
    for sti in SIDER:
        fund = dom((ROD / sti).read_text(encoding="utf-8"), sti)
        tjek(f"{sti} er grøn", not fund, "; ".join(fund[:3]))

    # 2. Mutation: den rå `event:'scan'`-fetch tilbage. Det var den
    #    dobbelte tælling, og den skal give rødt.
    for sti in SIDER:
        rå = (ROD / sti).read_text(encoding="utf-8")
        mut = rå.replace(
            "    html = data.html;",
            "    html = data.html;\n    try { fetch('/api/track',{method:'POST',"
            "headers:{'Content-Type':'application/json'},\n      body:JSON.stringify("
            "{path:location.pathname,event:'scan'}),keepalive:true}).catch(function(){}); } catch(e) {}",
            1,
        )
        fund = dom(mut, "mutation-dublet")
        tjek(f"{sti}: den dobbelte 'scan'-fetch er rød",
             any("rå fetch" in f for f in fund), str(fund[:2]))

    # 3. Mutation: udfaldet væk. Så er der igen intet at skelne et resultat fra
    #    et køb på.
    for sti in SIDER:
        rå = (ROD / sti).read_text(encoding="utf-8")
        mut = re.sub(RÅ_UDFALD, "trackEvent('scan')", rå)
        fund = dom(mut, "mutation-udfald")
        tjek(f"{sti}: udfaldet væk er rød",
             any("udfald" in f for f in fund), str(fund[:2]))

    # 4. Mutation: vagten `!opts.shared` væk. Delt link begynder at tælle
    #    udfald, som afsenderen ikke kørte.
    for sti in SIDER:
        rå = (ROD / sti).read_text(encoding="utf-8")
        mut = rå.replace("if(!opts.shared&&window.trackEvent)", "if(window.trackEvent)")
        fund = dom(mut, "mutation-delt")
        tjek(f"{sti}: delte rapporter tælles med er rød",
             any("opts.shared" in f for f in fund), str(fund[:2]))

    # 5. Mutation: 'scan-failed' væk. En fejlende scanning så målt ud som et
    #    resultat.
    for sti in SIDER:
        rå = (ROD / sti).read_text(encoding="utf-8")
        mut = rå.replace("window.trackEvent('scan-failed');", "")
        fund = dom(mut, "mutation-fejl")
        tjek(f"{sti}: 'scan-failed' væk er rød",
             any("scan-failed" in f for f in fund), str(fund[:2]))

    # 6. Mutation: pro-kortets knap taber sin måling.
    for sti in SIDER:
        rå = (ROD / sti).read_text(encoding="utf-8")
        mut = rå.replace(PRO_KORT_KALD, "")
        fund = dom(mut, "mutation-prokort")
        tjek(f"{sti}: pro-kortet uden 'pro-card-click' er rød",
             any("pro-card-click" in f for f in fund), str(fund[:2]))

    # 7. Polaritet: et kald med et navn `handleTrack` afviser skal være rødt,
    #    ellers kunne næste iteration skrive `scan_findings` og få 400.
    for sti in SIDER:
        rå = (ROD / sti).read_text(encoding="utf-8")
        fund = dom(rå.replace("window.trackEvent('scan-failed')",
                               "window.trackEvent('scan_failed')"), "polaritet-underskrift")
        tjek(f"{sti}: et navn med underscore er rødt",
             any("400" in f for f in fund), str(fund[:2]))

    # 8. Polaritet: den generiske `buy-click` fra `site/track.js` er stadig
    #    sand og skal ikke være et fund. `pro-card-click` er et målepunkt
    #    *ved siden af* den, ikke en erstatning.
    for sti in SIDER:
        rå = (ROD / sti).read_text(encoding="utf-8")
        fund = dom(rå.replace("  const out = document.getElementById('result');",
                               "  window.trackEvent('buy-click');\n"
                               "  const out = document.getElementById('result');", 1),
                   "polaritet-buyclick")
        tjek(f"{sti}: den generiske 'buy-click' er ikke et fund", not fund, str(fund[:2]))

    # 9. Begge sprog skal sende de samme navne. En dansk side med sit eget navn
    #    deler tragten i to.
    navne = []
    for sti in SIDER:
        kilde = (ROD / sti).read_text(encoding="utf-8")
        navne.append(set(re.findall(KALD, kilde)))
    tjek("EN og DA sender de samme begivenhedsnavne",
         navne[0] == navne[1], f"{sorted(navne[0])} vs {sorted(navne[1])}")

    # 10. Workerens egen regex skal være den porten dømmer mod.
    tjek("handleTrack afviser stadig andre navne end de fire",
         NAVN_REGEX in WORKER.read_text(encoding="utf-8"))

    for linje in fejl:
        print(f"  FEJL {linje}")
    print(f"check-scan-events-selftest: {'OK' if not fejl else 'RØD'} "
          f"({kørte - len(fejl)}/{kørte} kontroller)")
    return 1 if fejl else 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--self-test", action="store_true",
                    help="kør portens egen kontrol af sig selv")
    args = ap.parse_args(argv)

    if args.self_test:
        return _selftest()

    worker = WORKER.read_text(encoding="utf-8")
    if NAVN_REGEX not in worker:
        print(f"{WORKER.relative_to(ROD)}: afviser ikke længere andre "
              f"begivenhedsnavne end '{NAVN_REGEX}'. Porten ved ikke længere, "
              f"hvad den dømmer imod — opdatér den.")
        return 1

    fund: list[str] = []
    for sti in SIDER:
        fund += dom((ROD / sti).read_text(encoding="utf-8"), sti)
    for linje in fund:
        print(linje)
    if fund:
        print(f"\nscan-events: RØD — {len(fund)} fund i scannerens købsvej")
        return 1

    hver = sorted(set(re.findall(KALD, (ROD / SIDER[0]).read_text(encoding="utf-8"))))
    print(f"scan-events: GRØN — {len(SIDER)} sprog sender hver præcis ét "
          f"'scan'-kald og måler hele tragten: {', '.join(hver)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())