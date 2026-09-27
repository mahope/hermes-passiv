#!/usr/bin/env python3
"""Gør `/api/health` dommable — så `partial` ikke kan ligne rask være i måneder.

Baggrund (opgave fra `IMPLEMENTATION_PLAN.md`, NEXT_TASK 2, 27. september 2026):
`bugbottle.dev` ligger på en server vi ikke deployer, så det skriver ingen
`p:v3:`-nøgler, og `/api/health` har svaret `traffic_status: "partial"` hver time
i måneder. **Ingen så det.** `daily-health-check.sh` dømmer kun
`status == "healthy"`, og `status` var `kvOk ? 'healthy' : 'degraded'` — altså
`sæt aldrig rød fordi et instrumenteret domæne er tavst`.

Det er den ulydelige halvdel af en veltalende løgneste: KV er rask, tallene er
reelle, og hvert tal mangler et helt domæne. Derfor dømmer denne fil på
*beviset* — `kv`, `traffic_status` og hvilke domæner der taler — og ikke på
`status`-feltet, som er en bekvemmelighed.

Tre udfald, og de er ikke ens:

- `traffic_status: "ok"` → grøn. Alle instrumenterede domæner svarer.
- `traffic_status: "unknown"` → grøn **med en note**. Ingen data er ikke en
  fejl: en ny installation, eller to dage uden besøg, skal ikke gøre cron rød.
  At *sitet* er nede fanges andetsteds — `daily-health-check.sh` kører også
  `tools/check_live_sitemaps.py`, som henter de live sider.
- `traffic_status: "partial"` → rød, medmindre akten i `tools/health_acknowledged.json`
  matcher det målte domænebillede **eksakt**.

Derfor er kvitteringen en hel signatur og ikke en liste med én undtagelse: et nyt
tavst domæne, et domæne der forsvinder fra `TRACKING_DOMAINS`, eller en akte uden
begrundelse gør alle sammen cron rød i stedet for at blive dækket af en gammel
undtagelse. Det er hele pointen med at kvittere *signaturen* og ikke
symptomet.

    python3 tools/check_health_status.py            # hent live og døm
    python3 tools/check_health_status.py --json FILE # døm en gemt payload
    python3 tools/check_health_status.py --print     # skriv vurderingen ud

Exit 0 = grøn, 1 = rød. Ingen netværkskald i `--json`-tilstanden, så testen
kører offline.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ACK_FILE = ROOT / "tools" / "health_acknowledged.json"
HEALTH_URL = "https://mahope.tools/api/health"
# Samme User-Agent som `health_check.py`, så et kald her ikke ligner en browser,
# der er faldet ned i en fejlside.
USER_AGENT = "HermesHealthCheck/3.0"

# Domain-status der ikke tæller som "taler". `collectTraffic` bruger 'unknown'
# både for et domæne der aldrig har skrevet en nøgle og for et der var tavst i
# vinduet; `degraded' bruges ikke her, men den skal heller ikke fejltolkes som
# rask, hvis den nogensinde dukker op.
SILENT_DOMAIN_STATES = ("unknown", "degraded", "down", "")


def traffic_signature(payload: dict) -> dict:
    """Den del af et health-svar, en kvittering skal matche eksakt.

    Kun de domæner der *ikke* taler, ikke hele kortet: ellers ville en travl
    tirsdag kræve en ny kvittering, fordi `mahope.tools` gik fra 'unknown' til
    'ok'. Det er de tavse domæner der er det kendte problem.
    """
    domains = payload.get("traffic_domains")
    if not isinstance(domains, dict):
        return {}
    return {
        domain: state
        for domain, state in sorted(domains.items())
        if state in SILENT_DOMAIN_STATES
    }


def load_acknowledgements(path: Path = ACK_FILE) -> list[dict]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    entries = data.get("traffic") if isinstance(data, dict) else None
    return [entry for entry in (entries or []) if isinstance(entry, dict)]


def _matches(entry: dict, payload: dict) -> bool:
    signature = entry.get("signature")
    if not isinstance(signature, dict):
        return False
    if signature.get("traffic_status") != payload.get("traffic_status"):
        return False
    if signature.get("silent_domains") != traffic_signature(payload):
        return False
    # En kvittering uden begrundelse er en kvittering, der holder for evigt,
    # fordi ingen kan se hvorfor. Derfor er den ikke gyldig.
    return bool(str(entry.get("reason", "")).strip())


def decide(payload: object, acknowledged: list[dict] | None = None) -> tuple[bool, str]:
    """Dom `/api/health`-svaret. Returnerer `(grøn, begrundelse)`."""
    if not isinstance(payload, dict):
        return False, "svaret er ikke et JSON-objekt"
    if payload.get("kv") is not True:
        return False, f"KV er ikke tilgængelig (kv={payload.get('kv')!r})"

    traffic_status = payload.get("traffic_status")
    if traffic_status == "ok":
        return True, "alle instrumenterede domæner svarer"
    if traffic_status == "unknown":
        # Måske flere domæner, måske ingen. Uden `traffic_domains` er det ikke
        # til at se, så det er en note og ikke en rød port.
        silent = traffic_signature(payload)
        if silent:
            return True, (
                "trafik er ukendt, og de tavse domæner er "
                + ", ".join(sorted(silent))
                + " — verificér at de skriver /api/track"
            )
        return True, "ingen trafikdata i vinduet (ikke en fejl)"
    if traffic_status == "partial":
        silent = sorted(traffic_signature(payload))
        detail = ", ".join(silent) or "(domæneliste mangler i svaret)"
        for entry in acknowledged or []:
            if _matches(entry, payload):
                since = entry.get("since", "ukendt dato")
                return True, f"akcepteret undtagelse siden {since}: {detail}"
        return False, (
            f"trafikken er delvis og de tavse domæner er {detail} — "
            "tilføj dem i tools/health_acknowledged.json med en begrundelse, "
            "eller find ud af hvorfor de ikke skriver"
        )
    return False, f"uventet traffic_status={traffic_status!r}"


def fetch(url: str = HEALTH_URL, timeout: int = 15) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--json", metavar="FILE", help="døm en gemt payload i stedet for at hente")
    parser.add_argument("--ack", metavar="FILE", help="anden kvitteringsfil (test)")
    parser.add_argument("--print", action="store_true", help="skriv hele vurderingen ud som JSON")
    args = parser.parse_args(argv)

    acknowledged = load_acknowledgements(Path(args.ack) if args.ack else ACK_FILE)
    try:
        payload = json.loads(Path(args.json).read_text(encoding="utf-8")) if args.json else fetch()
    except (OSError, ValueError, urllib.error.URLError) as error:
        print(f"check_health_status: kunne ikke hente {HEALTH_URL}: {error}", file=sys.stderr)
        return 1

    healthy, reason = decide(payload, acknowledged)
    if args.print:
        print(json.dumps({
            "healthy": healthy,
            "reason": reason,
            "status": payload.get("status"),
            "traffic_status": payload.get("traffic_status"),
            "traffic_domains": payload.get("traffic_domains"),
        }, ensure_ascii=False, sort_keys=True))
    else:
        print(f"check_health_status: {'GRØN' if healthy else 'RØD'} — {reason}")
    return 0 if healthy else 1


if __name__ == "__main__":
    raise SystemExit(main())
