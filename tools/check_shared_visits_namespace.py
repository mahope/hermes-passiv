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

⚠️ **Målt 27/9 11:4x UTC, og resultatet er værre end hypotesen.** Første

kørsel af denne fil: `cleancopy.tools` **og** `deskuptime.com` **og**
`mahope.tools` taber alle tre deres beacons, selv efter at `mahope.tools` blev
kaldt på *sin egen* adresse med `Origin: https://mahope.tools` og HTTP 200.
`bugbottle.dev` svarer 404 fra nginx.

**Så hypotesen om en separat namespace-binding er IKKE bekræftet** — den er
modbevist for de to andre domæner, der burde dele `mahope.tools`' namespace.
Det der er målt er enklere og dumper værre: **`recentVisits` står på 7 og rører
sig ikke, for nogen, uanset om kaldet er same-origin eller ej.** Note fra
sidste iteration havde målt 4 → 6 med "rigtige headers", så skrivningen virkede
da; hvad der har ændret sig siden, er ikke isoleret her.

Derfor dømmer denne fil på **hvad der kan måles** og ikke på hvorfor. Den skal
give det næste svar på to timers arbejde, ikke et gæt: hvis `mahope.tools`
-tabt, er fejlen i `recordTraffic`/`collectTraffic` (kode, målbar her), og hvis
kun de andre taber, er den i bindingerne (infrastruktur, ❓ til Mads).

⚠️ **Den skriver i den rigtige statistik.** En beacon fra en automatisk
bruger-agent filtreres bevidst bort af `isAutomatedRequest`, så en probe der så
ud som en bot ville aldrig kunne bevise at skrivningen virker. Derfor sender den
her én ægte, talt sidevisning pr. domæne pr. kørsel, og derfor:


- **kør den manuelt, aldrig i cron** — cron skal ikke puste tallene op hver time;
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


def probe_domain(domain: str) -> dict:
    """Mål ét domæne. Læser sundhed før og efter sin egen beacon."""
    result = {"domain": domain, "before": None, "after": None, "wrote": None, "error": None}
    try:
        before = health_visits()
        result["before"] = before
        send_beacon(domain)
        after = health_visits()
        result["after"] = after
        result["wrote"] = after > before
    except (Unreachable, urllib.error.URLError, OSError, ValueError) as exc:
        result["error"] = str(exc)
    return result


def measure(domains=DOMAINS) -> dict:
    """Mål alle domæner. Sekventielt og uden omkring `/api/health`."""
    results = [probe_domain(domain) for domain in domains]
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
                  "den delte VISITS-namespace: " + ", ".join(silent))
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
                         f"({row['before']} → {row['after']})")
        else:
            lines.append(f"  {row['domain']:<20} TABER    "
                         f"({row['before']} → {row['after']}, beacon modtaget)")
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
