#!/usr/bin/env python3
"""Dom at workerens Sentry-opsætning er rigtig — og at den ikke lækker.

1/10-prompten siger «Ingen uløste fejl de seneste 14 dage» og spørger så om
SDK'en overhovedet er sat op. Målt: nul forekomster af «sentry» i hele
repoet. Det er ikke en kosmetisk mangel. `/api/url-inspect` lå på 500/1101
på *hvert* kald 30/9 (handleren manglede `env`), og `/api/compliance-ai` har
svaret 503 «AI service not configured» i dagevis, fordi `OPENROUTER_API_KEY`
manglede på workeren. Begge fejl var usynlige, fordi intet meldte sig.

Denne port dømmer de otte regler, der gør det trygt at gøra det:

1. **DSN'en er offentlig og hel.** Den står som fallback i koden, og endpoint
   og projekt-id er *udledt* af den — så et forkert projekt-id kan ikke
   overleve som en død konstant ved siden af.
2. **Kun i produktion.** `localhost`, `127.0.0.1`, `0.0.0.0` og `[::1]` er
   på listen, og rapporten vender tilbage på dem.
3. **Ingen persondata.** Begivenhedens `request`-objekt må indeholde præcis
   `url` og `method`, og `url` skal være bygget af `origin` + `pathname`.
   `/api/license/lookup` tager `{ order_id, email }` i kroppen, så en
   rapport med krop eller query-streng er et datalæk, ikke en fejl.
4. **Ingen traces.** `tracesSampleRate` ville sende hvert eneste kald videre
   og fylde kvoten på den konto der bruges til 500-'er.
5. **Ingen Session Replay.** Replay optager skærmbilleder af brugernes
   sider og kræver samtykke. Det er ikke en måske — det er nej.
6. **Ingen auth-token, ingen source maps.** Begge kræver en hemmelighed, og
   en hemmelighed i et offentligt repo er en lækket hemmelighed.
7. **Rapporteringen kan ikke kaste.** Den ligger i sin egen try/catch, så en
   fejl i overvågningen aldrig kan tage ruten ned med.
8. **En fejl i en løkke er dæmpet.** `SENTRY_MAX_PER_MINUTE` skal findes og
   være et lille tal. Den samme worker-kvota betalende kunder bruger til
   `/api/license/validate`, så en ubegrænset rapport er en reel risiko.

Hvorfor der ikke står `@sentry/cloudflare` i koden: denne worker er en
`_worker.js` i Pages *advanced mode* og bundles ikke — alt den bruger skal
ligge i selve filen, ellers fejler den ved deploy. En npm-import ville derfor
være en deploy-fejl, ikke en fordel. Det, der sendes, er derfor den
offentlige envelope-protokol som SDK'en selv taler.

    python3 tools/check_sentry_setup.py            # dom opsætningen
    python3 tools/check_sentry_setup.py --self-test # 8 kontroller
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORKER = ROOT / "site" / "_worker.js"
DSN_RE = re.compile(r"https://[a-f0-9]{32}@[a-z0-9.-]+/\d+")


def block(text: str, start_marker: str) -> str:
    """Kroppen af en funktion, fundet på tæller i stedet for på flueflader."""
    i = text.find(start_marker)
    if i < 0:
        return ""
    j = text.find("{", i)
    if j < 0:
        return ""
    depth = 0
    for k in range(j, len(text)):
        if text[k] == "{":
            depth += 1
        elif text[k] == "}":
            depth -= 1
            if depth == 0:
                return text[j:k + 1]
    return ""


def strip_comments(text: str) -> str:
    """Fjern kommentarer, så en regel i *prose* ikke tæller som slået til.

    Første måling af dom 5 var grøn fordi min egen kommentar om opsætningen
    indeholdt ordet «Replay» — porten erklærede den udvikler, der gjorde
    akkurat det den skulle advare mod. Blokerede kommentarer og kommentarer
    på egen linje maskeres derfor før der dommes.

    Kun hele linjer og blokke: `//` midt i en kode-streng som
    `https://mahope.tools` må ikke blive spist.
    """
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    return re.sub(r"(?m)^[ \t]*//.*$", "", text)


def judge(worker: str) -> list[tuple[bool, str]]:
    raw = worker
    worker = strip_comments(worker)
    report = block(worker, "async function reportWorkerError")
    guard = block(worker, "function guard(")
    out: list[tuple[bool, str]] = []

    # 1 — DSN
    dsn = DSN_RE.search(worker)
    out.append((bool(dsn), "1. ingen offentlig DSN i koden (den skal kunne stå der frit)"))
    out.append((bool(re.search(r"/api/\$\{m\[3\]\}/envelope/", worker)) or "envelope/" in worker,
                "1b. endpoint er udledt af DSN'en, ikke en død konstant ved siden af"))

    # 2 — kun i produktion
    out.append(("SENTRY_LOCAL_HOSTS" in worker and "127.0.0.1" in worker and "localhost" in worker,
                "2. ingen produktions-port (localhost/127.0.0.1 skal være undtaget)"))
    out.append(("SENTRY_LOCAL_HOSTS.has(url.hostname)" in report,
                "2b. rapporten vender ikke tilbage på de lokale værter"))

    # 3 — ingen persondata
    req = re.search(r"request:\s*\{(.*?)\}\s*,\s*exception", report, re.S)
    body = req.group(1) if req else ""
    keys = sorted(set(re.findall(r"([A-Za-z_]+)\s*:", body)))
    out.append((bool(body) and set(keys) <= {"url", "method"},
                f"3. `request` må kun have url+method, ikke persondata — fandt {keys or 'intet request-objekt'}"))
    out.append(("url.origin" in body and "url.pathname" in body and "url.search" not in body,
                "3b. rapport-URL'en er origin+pathname uden query-streng"))

    # 4 og 5 — ingen traces, ingen replay
    for pat, label in ((r"tracesSampleRate", "4. traces er slået til (fylder kvoten på 500-kontoen)"),
                       (r"\bReplay\b|replaysSessionSampleRate|replaysOnErrorSampleRate",
                        "5. Session Replay er slået til (kræver samtykke)")):
        out.append((not re.search(pat, worker), label))

    # 6 — ingen hemmeligheder i et offentligt repo
    for pat, label in ((r"auth_token|SENTRY_AUTH_TOKEN", "6. et auth-token står i koden"),
                       (r"\bsourcemap|\.map`?\.upload|sentry\.io/api/.*token",
                        "6b. source maps uploades (kræver en hemmelighed)")):
        out.append((not re.search(pat, worker, re.I), label))

    # 7 — rapporteringen kan ikke kaste
    out.append((bool(re.match(r"^\{\s*try\s*\{", report)) and "catch" in report,
                "7. rapporteringen er pakket i sin egen try/catch"))
    out.append(("reportWorkerError(" in guard,
                "7b. guarden kalder rapporten — ellers er 7 lige så død som resten"))

    # 8 — dæmpning af løkker
    m = re.search(r"SENTRY_MAX_PER_MINUTE\s*=\s*(\d+)", worker)
    out.append((bool(m) and int(m.group(1)) <= 10,
                "8. ingen dæmpning af gentagne fejl (SENTRY_MAX_PER_MINUTE mangler eller er for stor)"))
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args(argv)

    if args.self_test:
        return self_test()

    worker = WORKER.read_text(encoding="utf-8")
    results = judge(worker)
    problems = 0
    for ok, msg in results:
        print(("  ok  " if ok else "FEJL  ") + msg)
        if not ok:
            problems += 1
    print(f"Sentry-opsætning: {len(results)} kontroller, {problems} problemer")
    return 1 if problems else 0


MUTATIONS: list[tuple[str, str, str]] = [
    # (navn, søg, erstat) — hver især skal gøre porten rød.
    ("DSN fjernet", r"const SENTRY_DSN_FALLBACK = '[^']*';", "const SENTRY_DSN_FALLBACK = '';"),
    ("produktions-port fjernet", r"const SENTRY_LOCAL_HOSTS = new Set\(\[[^\n]*?\]\);",
     "const SENTRY_LOCAL_HOSTS = new Set([]);"),
    ("værten bruges ikke", r"if \(!url \|\| SENTRY_LOCAL_HOSTS\.has\(url\.hostname\)\) return;",
     "if (!url) return;"),
    ("headers sendt med", r"method: String\(request\.method \|\| 'GET'\) \}",
     "method: String(request.method || 'GET'), headers: request.headers }"),
    ("query-streng sendt med", r"\$\{url\.origin\}\$\{url\.pathname\}", "${request.url}"),
    ("traces slået til", r"const SENTRY_CLIENT = '([^']*)';", "const SENTRY_CLIENT = '\\1';\nconst tracesSampleRate = 1;"),
    ("replay slået til", r"const SENTRY_CLIENT = '([^']*)';",
     "const SENTRY_CLIENT = '\\1';\nnew Replay({ sessionSampleRate: 1 });"),
    ("auth-token i koden", r"const SENTRY_CLIENT = '([^']*)';",
     "const SENTRY_CLIENT = '\\1';\nconst AUTH = 'auth_token: abc';"),
    ("tælleren fjernet", r"const SENTRY_MAX_PER_MINUTE = 5;", "const SENTRY_MAX_PER_MINUTE = 5000;"),
    ("rapporten kaster", r"(\nasync function reportWorkerError\([^)]*\) \{\n  )try \{", r"\1{"),
]


def self_test() -> int:
    worker = WORKER.read_text(encoding="utf-8")
    baseline = judge(worker)
    bad = [m for ok, m in baseline if not ok]
    if bad:
        print("FEJL: den ændrede worker er ikke grøn, så selvtesten måler intet:")
        for m in bad:
            print("  - " + m)
        return 1

    failures = 0
    for name, pattern, repl in MUTATIONS:
        mutated, n = re.subn(pattern, repl, worker, count=1)
        if n == 0:
            print(f"FEJL: mutationen «{name}» ramte ikke koden — porten ville være grøn af vilje")
            failures += 1
            continue
        reds = [m for ok, m in judge(mutated) if not ok]
        if not reds:
            print(f"FEJL: mutationen «{name}» gav en grøn port — dommen kan ikke fejle")
            failures += 1
        else:
            print(f"  ok  mutation «{name}» → {reds[0]}")
    print(f"Sentry-selftest: {len(MUTATIONS)} mutationer, {failures} problemer")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())