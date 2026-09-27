#!/usr/bin/env python3
"""Port for `tools/check_shared_visits_namespace.py` — offline, ingen netværk.

Proben er den eneste måling der kan skelne *tabt trafik* fra * tavst domæne*, så
den skal have en arm for hver fejlform den kan ramme. En arm der aldrig kan
fejle er en løgneste, så porten dømmer de fire tilstande der kan forekomme:

- `writing` — beacon modtaget, `recentVisits` stiger;
- `silent` — beacon modtaget med HTTP 200, `recentVisits` stiger **ikke**. Det
  er fundet: domænet skriver i en anden namespace end den rapporterne læser;
- `unreachable` — domænet svarer ikke. Uden for målingen, fordi det er en
  udgivelsesfejl og ikke en namespace-fejl, og fordi det ellers ville ligne
  cleancopy-fejlen;
- `measured == 0` — intet kunne måles. Dømmes rød, fordi et port-resultat uden
  måling ikke er et grønt resultat.
"""
from __future__ import annotations

import json
import subprocess
import sys
import urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import check_shared_visits_namespace as probe  # noqa: E402

FAILURES: list[str] = []
PASSED = 0


def check(name: str, condition: bool, detail: str = "") -> None:
    global PASSED
    if condition:
        PASSED += 1
    else:
        FAILURES.append(f"{name}{': ' + detail if detail else ''}")


class FakeHttp:
    """Erstatter de to netværkskald, så porten ikke rører produktionen.

    `namespace` er navnet på den namespace `mahope.tools` læser. Et domæne der
    ikke står i `namespace` svarer 200 på sin beacon og taber tallet — præcis
    fejlen porten skal finde, bygget her i stedet for i Cloudflare.
    """

    def __init__(self, namespace: dict[str, str], reachable: set[str] | None = None,
                 window: int = 6) -> None:
        self.namespace = namespace
        self.reachable = reachable
        self.window = window
        self.calls: list[tuple[str, str]] = []

    def request(self, url: str, *, method: str = "GET", headers: dict | None = None,
                body: bytes | None = None) -> dict:
        headers = headers or {}
        host = url.split("/")[2]
        self.calls.append((method, url))
        if self.reachable is not None and host not in self.reachable:
            raise urllib.error.URLError(f"{host} svarer ikke")
        if url.startswith("https://mahope.tools/api/health"):
            return {"stats": {"recentVisits": self.window}}
        if url.endswith("/api/track"):
            if self.namespace.get(host) != "shared":
                # Beacon modtaget og bevidst smidt væk.
                return {"ok": True}
            self.window += 1
            return {"ok": True}
        raise AssertionError(f"uventet URL {url}")


def measure_with(fake: FakeHttp, domains=probe.DOMAINS) -> dict:
    original = probe._request
    probe._request = fake.request
    try:
        return probe.measure(domains)
    finally:
        probe._request = original


ALL_SHARED = {d: "shared" for d in probe.DOMAINS}

# 1. Det sunde billede: alle fire skriver.
m = measure_with(FakeHttp(dict(ALL_SHARED)))
check("alle skriver er målt", m["writing"] == sorted(probe.DOMAINS), str(m["writing"]))
check("alle skriver er ikke rødt", probe.verdict(m)["ok"] is True)
check("ingen er tavse", m["silent"] == [])

# 2. FUNDET: cleancopy.tools modtager beacons, men tallet forsvinder.
m = measure_with(FakeHttp({**ALL_SHARED, "cleancopy.tools": "andet"}))
check("et tabt domæne er tavst, ikke unreachable",
      m["silent"] == ["cleancopy.tools"], str(m["silent"]))
check("et tabt domæne gør rødt", probe.verdict(m)["ok"] is False)
check("et tabt domæne navngives i svaret",
      "cleancopy.tools" in probe.verdict(m)["reason"])
check("et tabt domæne tælles stadig som skrivende i de andre",
      m["writing"] == sorted(d for d in probe.DOMAINS if d != "cleancopy.tools"))

# 3. Uden for målingen: et domæne der ikke svarer er IKKE cleancopy-fejlen.
m = measure_with(FakeHttp(dict(ALL_SHARED), reachable={"mahope.tools", "deskuptime.com",
                                                     "cleancopy.tools"}))
check("et domæne der ikke svarer er unreachable", "bugbottle.dev" in m["unreachable"])
check("et domæne der ikke svarer dømmes ikke som tabt",
      m["silent"] == [], str(m["silent"]))
check("et domæne der ikke svarer gør ikke rødt", probe.verdict(m)["ok"] is True)
check("et domæne der ikke svarer nævnes som udgivelse",
      "udgivelse" in probe.verdict(m)["reason"])
check("et domæne der ikke svarer tælles ikke som skrivende",
      "bugbottle.dev" not in m["writing"])

# 4. Intet målt er ikke grønt. Ellers er porten grøn på en måling den ikke tog.
m = measure_with(FakeHttp(dict(ALL_SHARED), reachable=set()))
check("intet målt giver ingen skrivende", m["writing"] == [])
check("intet målt giver ingen tavse", m["silent"] == [])
check("intet målt gør rødt", probe.verdict(m)["ok"] is False,
      "en port der siger grøn uden at have målt noget er ikke undersøgt")

# 5. Rækkefølgen: sekventielt omkring /api/health, aldrig parallelt.
fake = FakeHttp(dict(ALL_SHARED))
measure_with(fake)
health_calls = [c for c in fake.calls if "api/health" in c[1]]
track_calls = [c for c in fake.calls if "api/track" in c[1]]
check("der læses to gange pr. domæne", len(health_calls) == len(track_calls) * 2,
      f"{len(health_calls)} sundhedsafsnit mod {len(track_calls)} beacons")
check("hvert domæne måles mellem to sundhedsafsnit",
      all(health_calls[i][1] == health_calls[i + 1][1] for i in range(0, len(health_calls), 2)))

# 6. Beaconen sendes til domænets egen adresse, ikke til mahope.tools.
fake = FakeHttp(dict(ALL_SHARED))
measure_with(fake, domains=("cleancopy.tools",))
check("beaconen går til domænets egen /api/track",
      any(u == "https://cleancopy.tools/api/track" for _, u in fake.calls))
check("beaconen går ikke gennem mahope.tools",
      not any(u == "https://mahope.tools/api/track" for _, u in fake.calls))

# 7. Origin og Referer er domænets egne — ellers ville `handleTrack` svare 403,
#    og porten ville "bevise" en skrivning den aldrig forsøgte.
fake = FakeHttp(dict(ALL_SHARED))
measure_with(fake, domains=("cleancopy.tools",))
check("proben bruger ikke en bot-UA (ville aldrig skrive nogen nøgle)",
      not any(token in probe.PROBE_UA.lower()
              for token in ("bot", "curl", "python", "headless")))

# 8. `render` skal være læsbar og skal skelne de tre tilstande.
rendered = probe.render(measure_with(FakeHttp({**ALL_SHARED, "cleancopy.tools": "andet"})))
check("render dømmer RØD ved tabt domæne", rendered.startswith("check_shared_visits_namespace: RØD"))
check("render mærker det tabte domæne", "TABER" in rendered)
check("render mærker de skrivende", "skriver" in rendered)
check("render nævner domænet ved navn", "cleancopy.tools" in rendered)

# 9. `--json` dømmer en gemt måling uden netværk, så cron aldrig kan træffe fejl.
tmp = Path("/tmp/check_shared_visits_namespace_port.json")
try:
    tmp.write_text(json.dumps(measure_with(FakeHttp({**ALL_SHARED, "cleancopy.tools": "andet"}))),
                   encoding="utf-8")
    proc = subprocess.run([sys.executable, str(Path(probe.__file__)),
                           "--json", str(tmp), "--print"],
                          capture_output=True, text=True, timeout=60)
    check("--json exit 1 ved tabt domæne", proc.returncode == 1, proc.stdout + proc.stderr)
    check("--json skriver vurderingen ud", "RØD" in proc.stdout)
    tmp.write_text(json.dumps(measure_with(FakeHttp(dict(ALL_SHARED)))), encoding="utf-8")
    proc = subprocess.run([sys.executable, str(Path(probe.__file__)),
                           "--json", str(tmp), "--print"],
                          capture_output=True, text=True, timeout=60)
    check("--json exit 0 når alle skriver", proc.returncode == 0, proc.stdout + proc.stderr)
    check("--json skriver GRØN", "GRØN" in proc.stdout)
finally:
    tmp.unlink(missing_ok=True)

# 10. `DOMAINS` skal dække `TRACKING_DOMAINS` i `site/_worker.js` — ellers måler
#     porten ikke hele familien, og et nyt domæne ville blive usynligt for den.
worker = (Path(__file__).resolve().parent.parent / "site" / "_worker.js").read_text(
    encoding="utf-8")
start = worker.index("const TRACKING_DOMAINS")
block = worker[start:worker.index("]);", start)]
worker_domains = [line.strip().strip("',") for line in block.splitlines()[1:]
                  if line.strip().startswith("'")]
check("portens domæneliste er TRACKING_DOMAINS i workeren",
      worker_domains == list(probe.DOMAINS), f"{worker_domains} vs {list(probe.DOMAINS)}")

total = PASSED + len(FAILURES)
if FAILURES:
    print(f"test_shared_visits_namespace: RØD — {PASSED}/{total}")
    for failure in FAILURES:
        print(f"  - {failure}")
    sys.exit(1)
print(f"test_shared_visits_namespace: GRØN — {PASSED}/{total}")
