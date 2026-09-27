#!/usr/bin/env python3
"""Mål om hvert domænes beacon lander i den VISITS-namespace, rapporterne læser.

Fund fra `IMPLEMENTATION_PLAN.md` 27. september 2026. Da `partial` blev en egen
tilstand, gik `tools/check_health_status.py` rød på **to** tavse domæner, ikke ét:
`bugbottle.dev` (kendt — vi deployer det ikke) og `cleancopy.tools` (**ukendt**).
Det andet var ikke en travl uge. Målt:

    POST https://cleancopy.tools/api/track   Origin+Referer: cleancopy.tools
      → HTTP 200 {"ok":true}
    GET  https://mahope.tools/api/health
      → recentVisits uændret, cleancopy.tools: "unknown"

**Beacons modtages, og tallene dukker ikke op i den delte namespace.** Min første
tolkning var, at hvert Pages-projekt skriver i sin *egen* `VISITS`-namespace, fordi
KV-bindingen sættes pr. projekt i Cloudflare og ikke i `deploy-sites.yml`, som kun
kører `pages deploy`. **Den tolkning viste sig forkert og er taget tilbage** — se
målingen nedenfor: også `mahope.tools` taber sin egen beacon, og den kan umuligt
have en fremmed namespace. Det, der så ud som en bindingsfejl, kan derfor også
være en fejl i selve skrivningen. Beviset for årsagen mangler, og det er ikke denne
fils opgave at gætte på den.

Denne fil er den manglende måling. Før dette fandt var der ingen måde at se
**hvilket** domæne der taber sin trafik — kun at *et* gjorde. Nu er der én, og den
er et svar, ikke en følelse.

⚠️ **Målt 27/9 11:4x UTC. KONKLUSIONEN NEDENFOR VAR FORKERT OG ER TAGET TILBAGE.**

Første kørling af denne fil: `cleancopy.tools` **og** `deskuptime.com` **og**
`mahope.tools` taber alle tre deres beacons, selv efter at `mahope.tools` blev
kaldt på *sin egen* adresse med `Origin: https://mahope.tools` og HTTP 200.
`bugbottle.dev` svarer 404 fra nginx. Da hypotesen om separate
namespace-bindinger heller ikke holdt — `mahope.tools` kan umuligt have en
fremmed namespace — blev der skrevet at `recentVisits` stod på 7 og *rørte sig
ikke*, for nogen.

**Alle tre dele af den konklusion var en målefejl, og fejlen var i denne fil.**
Den læste `after` **én gang, med det samme den havde sendt beaconen** — og
`collectTraffic` læser med `VISITS.list()`, som er eventualt konsistent. Målt
27/9 ~12:0x UTC på cleancopy.tools, med identisk kald:

    POST https://cleancopy.tools/api/track  → HTTP 200 på 0,54 s
    /api/health umiddelbart efter           → recentVisits 12
    … fire aflæsninger, 8 s imellem        → recentVisits 12, 12, 12, 12
    /api/health ca. 32 s efter skrivningen → recentVisits 13

**Skrivningen virkede hele vejen.** `recordTraffic` skriver med `VISITS.put` med
det samme; det er kun *list*-aflæsningen der halter. Beviset er uafhængigt af
denne fils konklusion: `cleancopy.tools` stod i `traffic_domains` som `unknown`
da porten gik rød, og stod som `ok` med 12 besøg senere samme dag — skrevet af
beacons, der efter alt at dømme var faldet på gulvet. Der var ingen kodefejl i
`recordTraffic`/`collectTraffic` og ingen bindinger at rette. Den næste
iteration ville have jaget en fejl, der ikke findes, i to timers arbejde.

Derfor dømmer denne fil på **hvad der kan måles** og ikke på hvorfor, og den
**venter på eventual consistency** (`SETTLE_SECONDS`) i stedet for at læse én
gang. Et domæne erklæres først tabt, når det har modtaget sin beacon og stadig
ikke har flyttet tallet efter hele vinduet, og svaret siger hvor længe der blev
ventet, så påstanden kan efterprøves i stedet for at troes.

⚠️ **Den skriver i den rigtige statistik.** En beacon fra en automatisk
bruger-agent filtreres bevidst bort af `isAutomatedRequest`, så en probe der så
ud som en bot ville aldrig kunne bevise at skrivningen virker. Derfor sender den
her én ægte, talt sidevisning pr. domæne pr. kørsel, og derfor:


- **kør den manuelt, aldrig i cron** — cron skal ikke puste tallene op hver time;
- **den bruger nu op til `SETTLE_SECONDS` pr. domæne**, så en fuld kørsel tager
  nogle få minutter. Det er prisen for at svare rigtigt; ventetiden lå bag i
  det falske "TABER" i to iterationer;
- **tallene efter en kørsel indeholder den måling** (én pr. domæne), så den skal
  køres, når tallene netop er regenereret, og resultatet skrives i planen;
- kør `--json` på en gemt måling for at dømme offline, så porten kan teste logikken
  uden at skrive noget som helst.

Ud af hver domæne kræves to kald, og de skal løbes **sekventielt omkring**
`/api/health`, fordi `recentVisits` er et aggregat på tværs af domæner: læses
to domæners helbredser parallelt, kan en skrivning fra det ene tælles med i
vurderingen af det andet.

    python3 tools/check_shared_visits_namespace.py            # mål live
    python3 tools/check_shared_visits_namespace.py --print     # skriv vurderingen ud
    python3 tools/check_shared_visits_namespace.py --json FILE # døm en gemt måling

Exit 0 = alle målbare domæner skriver til den delte namespace, 1 = et eller flere
gør ikke. Et domæne der ikke svarer (DNS, nginx, 404) tælles **ikke** som rødt
her — det er en udgivelsesfejl, ikke en namespace-fejl, og `tools/
check_domain_coverage` dømmer den.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HEALTH_URL = "https://mahope.tools/api/health"

# Samme rækkefølge som `TRACKING_DOMAINS` i `site/_worker.js`, så tallene kan
# sammenlignes linje for linje med `traffic_domains` i `/api/health`.
DOMAINS = ("cleancopy.tools", "deskuptime.com", "bugbottle.dev", "mahope.tools")

# En almindelig browsers User-Agent. Bevidst *ikke* en bot-UA: `isAutomatedRequest`
# ville svale kaldet med `{ok:true}` uden at skrive, og så ville porten "bevise" at
# skrivningen virker ved aldrig at prøve den. Se docstringens advarsel om at den
# derfor tælles i den rigtige statistik.
PROBE_UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36")
HEALTH_UA = "HermesVisitsNamespaceProbe/1.0"

# Stien bruges som `Referer`, og `normalizeTrackedPath` beholder den. Den er
# tydeligt ægte (ikke `/api/track`, `/api/stats` eller `/stats`, som
# `UNTRACKED_PATHS` springer over), så en talt probe efterligner et rigtigt
# sidevisning og kan derfor ikke forklare sig med et speciale.
PROBE_PATH = "/namespace-probe"

TIMEOUT = 20

# `recordTraffic` skriver nøglen med det samme (`VISITS.put`), men `collectTraffic`
# læser den med `VISITS.list(prefix)`, og **Cloudflare KV's list er eventualt
# konsistent**: nøglen er skrevet længe før den dukker op i et list-kald. Målt
# 27/9 ~12:0x UTC på cleancopy.tools: `POST /api/track` svarede 200 på 0,54 s,
# `recentVisits` stod uændret på 12 gennem fire aflæsninger og blev 13 på den
# femte — ca. 32 sekunders forsinkelse. *Det var den fejl, der gjorde at denne
# fil erklærede alle domæner for tabte i to iterationer:* den læste `after` én
# gang med det samme, den havde sendt beaconen, så forsinkelsen så ud som tabt
# trafik. SETTLE_SECONDS er derfor ikke en finjustering, men det som adskiller
# målingen fra et gæt. Den skal overstige den målte forsinkelse med margin.
SETTLE_SECONDS = 90
POLL_SECONDS = 6


class Unreachable(Exception):
    """Domænet svarede ikke — udgivelse, ikke namespace."""


def _request(url: str, *, method: str = "GET", headers: dict | None = None,
             body: bytes | None = None) -> dict:
    request = urllib.request.Request(url, method=method, data=body,
                                     headers=headers or {})
    with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
        raw = response.read()
    try:
        return json.loads(raw)
    except ValueError:
        raise Unreachable(f"{url} svarede ikke med JSON")


def health_visits() -> int:
    """`recentVisits` som `/api/health` tæller det lige nu."""
    data = _request(HEALTH_URL, headers={"User-Agent": HEALTH_UA})
    stats = data.get("stats")
    if not isinstance(stats, dict) or "recentVisits" not in stats:
        raise Unreachable("api/health svarede uden stats.recentVisits")
    return int(stats["recentVisits"])


def send_beacon(domain: str) -> None:
    """Send én beacon til *domain* sit eget `/api/track`, same-origin.

    `handleTrack` afviser et kald hvor `Origin` ikke er kaldets eget domæne
    (`site/_worker.js`: `request.headers.get('origin') !== url.origin`), så
    porten sender til *domænets* adresse og ikke til mahope.tools. En 403 her
    betyder at domænet faktisk afviser sporing — ikke at skrivningen virker. Det
    var den fejl i den første måling af denne fejl, så skelnen er en arm i porten.
    """
    origin = f"https://{domain}"
    _request(
        f"{origin}/api/track",
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Origin": origin,
            "Referer": f"{origin}{PROBE_PATH}",
            "User-Agent": PROBE_UA,
        },
        body=json.dumps({"path": PROBE_PATH}).encode(),
    )


def wait_for_increment(before: int, *, settle: int = SETTLE_SECONDS,
                       poll: int = POLL_SECONDS, reader=health_visits,
                       sleep=time.sleep, clock=time.monotonic):
    """Vent på at KV's list får en nøgle til at blive synlig, og stop i tide.

    Giver `(after, waited, samples)`. `waited` er de overvågede sekunder, så et
    domæne der erklæres tabt kan efterprøves: skrev den, eller ventede vi bare
    ikke længe nok? Uden `waited` i svaret er de to umulige at skelne.

    `sleep` og `clock` er injicerbare, så porten kan prøve både en nøgle der
    dukker op sent og en der aldrig dukker op, uden at vente i virkelighed.
    """
    deadline = clock() + settle
    waited = 0
    samples = 0
    while True:
        after = reader()
        samples += 1
        if after > before:
            return after, waited, samples
        if clock() >= deadline:
            return after, waited, samples
        sleep(poll)
        waited += poll


def probe_domain(domain: str, *, settle: int = SETTLE_SECONDS,
                 poll: int = POLL_SECONDS, sleep=time.sleep,
                 clock=time.monotonic) -> dict:
    """Mål ét domæne. Læser sundhed, sender sin egen beacon, og **venter** på
    at tallet bliver synligt før den dømmer."""
    result = {"domain": domain, "before": None, "after": None, "wrote": None,
              "waited": None, "samples": None, "error": None}
    try:
        before = health_visits()
        result["before"] = before
        send_beacon(domain)
        after, waited, samples = wait_for_increment(
            before, settle=settle, poll=poll, sleep=sleep, clock=clock)
        result["after"] = after
        result["waited"] = waited
        result["samples"] = samples
        result["wrote"] = after > before
    except (Unreachable, urllib.error.URLError, OSError, ValueError) as exc:
        result["error"] = str(exc)
    return result


def measure(domains=DOMAINS, *, settle: int = SETTLE_SECONDS,
            poll: int = POLL_SECONDS, sleep=time.sleep,
            clock=time.monotonic) -> dict:
    """Mål alle domæner. Sekventielt og uden omkring `/api/health`."""
    results = [probe_domain(domain, settle=settle, poll=poll, sleep=sleep,
                            clock=clock) for domain in domains]
    measured = [r for r in results if r["wrote"] is not None]
    return {
        "domains": results,
        "measured": len(measured),
        "writing": sorted(r["domain"] for r in measured if r["wrote"]),
        "silent": sorted(r["domain"] for r in measured if not r["wrote"]),
        "unreachable": sorted(r["domain"] for r in results if r["wrote"] is None),
    }


def verdict(measurement: dict) -> dict:
    """Gør målingen til et svar. Kun domæner vi *kunne* måle dommeres."""
    silent = list(measurement.get("silent") or [])
    writing = list(measurement.get("writing") or [])
    unreachable = list(measurement.get("unreachable") or [])
    measured = int(measurement.get("measured") or 0)
    if not measured:
        # En port der siger grøn uden at have målt noget er ikke undersøgt.
        # Uden denne arm ville et totalt netværkssvigt læse som "ingen taber
        # trafik", fordi `silent` så er tom. Rød er det ærlige svar: målingen
        # mislykkedes, og det er ikke det samme som at alt er i orden.
        return {"ok": False, "writing": writing, "silent": silent,
                "unreachable": unreachable,
                "reason": ("intet domæne kunne måles — hverken læst eller skrevet, "
                           "så porten ved intet om namespace")}
    if silent:
        ok = False
        reason = ("disse domæner modtager beacons men tallene dukker ikke op i "
                  "den delte VISITS-namespace inden for "
                  f"{SETTLE_SECONDS}s (målt forsinkelse ~32s, se SETTLE_SECONDS): "
                  + ", ".join(silent))
    else:
        ok = True
        reason = (f"alle {len(writing)} målbare domæner skriver til den delte "
                  "VISITS-namespace")
    if unreachable:
        reason += (f". Uden for målingen: " + ", ".join(unreachable)
                   + " (svarer ikke — udgivelse, ikke namespace)")
    return {"ok": ok, "reason": reason, "writing": writing, "silent": silent,
            "unreachable": unreachable}


def render(measurement: dict) -> str:
    verdict_data = verdict(measurement)
    lines = ["check_shared_visits_namespace: "
             + ("GRØN — " if verdict_data["ok"] else "RØD — ")
             + verdict_data["reason"]]
    for row in measurement["domains"]:
        if row["wrote"] is None:
            lines.append(f"  {row['domain']:<20} ikke målbart ({row['error']})")
        elif row["wrote"]:
            lines.append(f"  {row['domain']:<20} skriver  "
                         f"({row['before']} → {row['after']}, "
                         f"synlig efter {row['waited']}s)")
        else:
            lines.append(f"  {row['domain']:<20} TABER    "
                         f"({row['before']} → {row['after']} efter "
                         f"{row['waited']}s, beacon modtaget)")
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--json", metavar="FILE",
                        help="døm en gemt måling i stedet for at måle live")
    parser.add_argument("--print", action="store_true",
                        help="skriv hele vurderingen ud")
    args = parser.parse_args(argv)

    if args.json:
        measurement = json.loads(Path(args.json).read_text(encoding="utf-8"))
    else:
        measurement = measure()
    if args.print:
        print(render(measurement))
    else:
        print("check_shared_visits_namespace: "
              + ("GRØN" if verdict(measurement)["ok"] else "RØD")
              + " — " + verdict(measurement)["reason"])
    return 0 if verdict(measurement)["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
