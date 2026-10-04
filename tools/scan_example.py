#!/usr/bin/env python3
"""Mål et rigtigt scan-resultat med den kode der faktisk ships.

Eksempel-resultatet på `/scan` og `/scan-da` består af tal, så de skal kunne
regenereres i stedet for at stå i en tekst og blive ældre. Dette kører
`site/scan.html` i headless Chromium med `/scan-proxy` stubbet til en
read-only hentning af målsiden, og skriver fundene ud.

To ting er bevidste. For det første sker målingen på en **lokal kopi** af
siden, ikke på live: `/api/track` og `/scan-proxy` peger på en lokal
stub, så hverken `/api/results` eller nogen anden tæller registrerer
målingen som et scan. En måling skal ikke se ud som en bruger. For det andet
er det sidens *egne* scripts der kører — DOMParser, de 15 tjek og
`SCANSHARE.scoreOf` — så tallet er det scanneren viser, ikke en ny formel
her.

Brug:

    python3 tools/scan_example.py https://wordpress.org/

Kopier `score`, `counts` og `findings` tilbage i kortet i `site/scan.html` og
`site/scan-da.html`, og opdatér datoen i teksten — tallene er et øjebliksbillede,
fordi et site ændrer sig.
"""
import argparse
import json
import re
import subprocess
import sys
import threading
import urllib.error
import urllib.parse
import urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"

CHROME_CANDIDATES = [
    Path.home() / "Library/Caches/ms-playwright/chromium-1234/chrome-mac-arm64"
    / "Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing",
    Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
    Path("/usr/bin/google-chrome"),
    Path("/usr/bin/chromium"),
    Path("/usr/bin/chromium-browser"),
]


def find_chrome() -> str:
    """Findes ingen browser, er opgaven ikke løst — men tallene må ikke
    gættes, så der afganges en fejl i stedet for at skrive noget i kortet."""
    for p in CHROME_CANDIDATES:
        if p.exists():
            return str(p)
    raise SystemExit(
        "FEJL: ingen Chromium fundet. Sæt stien i CHROME_CANDIDATES, eller kør\n"
        "  npx playwright install chromium\n"
        "Tallene i eksempel-kortet må ikke skrives i hånden: et tal uden en måling\n"
        "ved siden af sig er en påstande, ikke et resultat."
    )


class Handler(SimpleHTTPRequestHandler):
    """Serverer `site/` og svarer på de to ruter siden kalder.

    `/scan-proxy` er en GET i `scan()` — ikke en POST — så den skal behandles
    under `do_GET`. `/api/track` svarer 200 med et tomt objekt, fordi der
    ellers står en `Unexpected token '<'`-fejl i `#result` i stedet for et
    resultat.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(SITE), **kwargs)

    def log_message(self, *args):
        """Hold serveren stille; `--dump-dom` er det vi læser."""

    def _json(self, code, payload):
        raw = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _proxy(self):
        target = urllib.parse.parse_qs(self.path.split("?", 1)[1] if "?" in self.path else "").get("url", [""])[0]
        try:
            html = urllib.request.urlopen(
                urllib.request.Request(target, headers={"User-Agent": "Mozilla/5.0 (EAA scanner example measurement)"}),
                timeout=25,
            ).read().decode("utf-8", "replace")
        except (urllib.error.URLError, ValueError) as err:
            return self._json(200, {"ok": False, "error": str(err)})
        return self._json(200, {"ok": True, "html": html})

    def do_POST(self):
        return self._json(200, {})

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/scan-proxy":
            return self._proxy()
        if path.startswith("/api/track"):
            return self._json(200, {})
        if path.endswith("/"):
            path += "index.html"
        elif not Path(path).suffix:
            if (SITE / (path.lstrip("/") + ".html")).exists():
                path += ".html"
            elif (SITE / path.lstrip("/") / "index.html").exists():
                path = path.rstrip("/") + "/index.html"
        self.path = path
        return super().do_GET()


def measure(target: str, budget_ms: int) -> dict:
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        port = server.server_address[1]
        page = f"http://127.0.0.1:{port}/scan#url={urllib.parse.quote(target, safe='')}"
        dom = subprocess.run(
            [find_chrome(), "--headless", "--disable-gpu", "--no-sandbox",
             f"--virtual-time-budget={budget_ms}", "--dump-dom", page],
            capture_output=True, text=True, timeout=budget_ms / 1000 + 60,
        ).stdout
    finally:
        server.shutdown()

    start = dom.find('id="result"')
    if start < 0:
        raise SystemExit("FEJL: siden blev ikke hentet — er `site/` flyttet?")
    seg = dom[start:]
    # `#result` er sidens første `<section>`; det næste `<h2>` markerer
    # næste sektion, så slås resten af siden af. Uden snittet ville
    # «What it checks»-listen tælle som fund.
    end = seg.find('<h2 id="how-heading"')
    seg = seg[:end] if end > 0 else seg

    score = re.search(r'class="score grade-\w+">([^<]+)<', seg)
    counts = re.search(r'<div>(\d+ error\(s\), \d+ warning\(s\))</div>', seg)
    blocks = re.findall(r'<ul class="findings">(.*?)</ul>', seg, re.S)
    findings = []
    if blocks:
        # `rankBox()` skriver de tre vigtigste fund i en `<ol>` og hele listen
        # i den *sidste* `<ul>`, så den sidste er den komplette.
        for sev, text in re.findall(r'<li><span class="sev-(\w+)">(.*?)</span>', blocks[-1], re.S):
            findings.append({"sev": sev, "text": text})
    if not score:
        raise SystemExit("FEJL: ingen score i `#result` — var siden hentet? Se `Scan failed` i DOM'et.")
    return {"target": target, "score": score.group(1), "counts": counts.group(1) if counts else None,
            "findings": findings}


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("url", help="den side der skal scannes, fx https://wordpress.org/")
    ap.add_argument("--budget-ms", type=int, default=25000, help="hvor længe browseren må køre")
    args = ap.parse_args()
    if not re.match(r"^https?://", args.url):
        raise SystemExit("FEJL: URL skal begynde med http:// eller https://")
    print(json.dumps(measure(args.url, args.budget_ms), ensure_ascii=False, indent=1))
    sys.exit(0)