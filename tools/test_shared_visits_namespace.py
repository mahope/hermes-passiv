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


class FakeClock:
    """Virtuel tid, så porten kan vente på en nøgle der dukker op sent uden at
    vente i virkelighed."""

    def __init__(self) -> None:
        self.t = 0.0
        self.slept: list[float] = []

    def __call__(self) -> float:
        return self.t

    def sleep(self, seconds: float) -> None:
        self.slept.append(seconds)
        self.t += seconds


class FakeHttp:
    """Erstatter de to netværkskald, så porten ikke rører produktionen.

    `namespace` er navnet på den namespace `mahope.tools` læser. Et domæne der
    ikke står i `namespace` svarer 200 på sin beacon og taber tallet — præcis
    fejlen porten skal finde, bygget her i stedet for i Cloudflare.

    `lag` er antal sundhedsafsnit der skal svæve, før en skrevet nøgle bliver
    synlig. Det er **eventual consistency i `VISITS.list()`**, målt til ~32 s i
    produktion, og det er den fejl porten *ikke* kunne finde før dette: med
    `lag=0` lignede den sunde verden den virkelige, og så kom den aldrig
    udfyldt. Nu kan porten frembringe præcis det scenarie, der lå bag de to
    falske "TABER"-rækker i `IMPLEMENTATION_PLAN.md`.
    """

    def __init__(self, namespace: dict[str, str], reachable: set[str] | None = None,
                 lag: int = 0) -> None:
        self.namespace = namespace
        self.reachable = reachable
        self.lag = lag
        self.window = 6
        self.pending = 0
        self.stale = 0
        self.calls: list[tuple[str, str]] = []

    def request(self, url: str, *, method: str = "GET", headers: dict | None = None,
                body: bytes | None = None) -> dict:
        headers = headers or {}
        host = url.split("/")[2]
        self.calls.append((method, url))
        if self.reachable is not None and host not in self.reachable:
            raise urllib.error.URLError(f"{host} svarer ikke")
        if url.startswith("https://mahope.tools/api/health"):
            if self.pending and self.stale >= self.lag:
                self.window += self.pending
                self.pending = 0
                self.stale = 0
            elif self.pending:
                self.stale += 1
            return {"stats": {"recentVisits": self.window}}
        if url.endswith("/api/track"):
            if self.namespace.get(host) != "shared":
                # Beacon modtaget og bevidst smidt væk.
                return {"ok": True}
            self.pending += 1
            return {"ok": True}
        raise AssertionError(f"uventet URL {url}")


def measure_with(fake: FakeHttp, domains=probe.DOMAINS, clock: FakeClock | None = None) -> dict:
    clock = clock or FakeClock()
    original = probe._request
    probe._request = fake.request
    try:
        return probe.measure(domains, sleep=clock.sleep, clock=clock)
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

# 11. FUNDET 27/9 12:0x: `VISITS.list()` er eventualt konsistent. `recordTraffic`
#     skriver med `put` med det samme, men `collectTraffic` læser med `list`, så
#     nøglen er skjult i op til ~32 s (målt). Den gamle `probe_domain` læste
#     `after` *én* gang lige efter beaconen og erklærede derfor **alle** domæner
#     for tabte — to iterationers fejlsyn, og en jagt efter en kodefejl i
#     `recordTraffic` som ikke findes. Disse arme er den fejl, porten ikke
#     kunne se, fordi fake-klassen gjorde `list` øjeblikkelig.
fake = FakeHttp(dict(ALL_SHARED), lag=3)
fake.request("https://cleancopy.tools/api/track", method="POST",
             headers={"Origin": "https://cleancopy.tools"})
check("fake-klassen kan overhovedet skjule en skrivning",
      fake.request("https://mahope.tools/api/health")["stats"]["recentVisits"] == 6,
      "en nøgle med lag=3 må være usynlig ved den første aflæsning")
m = measure_with(FakeHttp(dict(ALL_SHARED), lag=3))
check("en nøgle der bliver synlig sent er skrivende, ikke tabt",
      m["writing"] == sorted(probe.DOMAINS), str(m["silent"]))
check("en sent synlig nøge gør ikke rødt", probe.verdict(m)["ok"] is True,
      probe.verdict(m)["reason"])
check("en sent synlig nøge tælles ikke som unreachable", m["unreachable"] == [])
check("svaret siger hvor længe der blev ventet",
      all((r.get("waited") or 0) > 0 for r in m["domains"]),
      str([r["waited"] for r in m["domains"]]))
check("svaret tæller aflæsningerne", all((r.get("samples") or 0) > 2 for r in m["domains"]),
      str([r["samples"] for r in m["domains"]]))

# 12. Vinduet er dog stadig endeligt: en nøgle der *aldrig* bliver synlig skal
#     stadig dømmes tabt, ellers er fundet ovenfor blot gjort umuligt at se.
m = measure_with(FakeHttp(dict(ALL_SHARED), lag=10_000))
check("en nøgle der aldrig bliver synlig er tavs", len(m["silent"]) == len(probe.DOMAINS),
      str(m["silent"]))
check("en nøgle der aldrig bliver synlig gør rød", probe.verdict(m)["ok"] is False)
check("vinduet er endeligt — ventetiden er deklareret",
      all(isinstance(r.get("waited"), int) and r["waited"] <= probe.SETTLE_SECONDS for r in m["domains"]),
      str([r["waited"] for r in m["domains"]]))
check("vinduet overstiger den målte forsinkelse",
      probe.SETTLE_SECONDS > 32, f"{probe.SETTLE_SECONDS}s")
check("et tavst domæne melder den fulde ventetid",
      all(isinstance(r.get("waited"), int) and r["waited"] >= probe.SETTLE_SECONDS - probe.POLL_SECONDS for r in m["domains"]),
      str([r["waited"] for r in m["domains"]]))

# 13. Forsinkelse og tab er to forskellige fejl. Med `lag=3` på cleancopy.tools
#     og en anden namespace på deskuptime.com må kun den sidste være rød.
m = measure_with(FakeHttp({**ALL_SHARED, "deskuptime.com": "andet"}, lag=3))
check("forsinkelse gør ikke rødt, en anden namespace gør",
      m["silent"] == ["deskuptime.com"]
      and m["writing"] == sorted(d for d in probe.DOMAINS if d != "deskuptime.com"),
      f"tavst={m['silent']} skrivende={m['writing']}")

# 14. `render` skal fortælle læseren at den ventede — ellers er et "TABER" umuligt
#     at efterprøve, og det er præcis derfor de to sidste iterationer troede på det.
rendered = probe.render(measure_with(FakeHttp({**ALL_SHARED, "cleancopy.tools": "andet"})))
check("render fortæller hvor længe det tabte domæne blev ventet på",
      f"efter {probe.SETTLE_SECONDS}s" in rendered, rendered)
check("render nævner det fulde vindue i vurderingen",
      f"{probe.SETTLE_SECONDS}s" in rendered.splitlines()[0], rendered.splitlines()[0])

total = PASSED + len(FAILURES)
if FAILURES:
    print(f"test_shared_visits_namespace: RØD — {PASSED}/{total}")
    for failure in FAILURES:
        print(f"  - {failure}")
    sys.exit(1)
print(f"test_shared_visits_namespace: GRØN — {PASSED}/{total}")
