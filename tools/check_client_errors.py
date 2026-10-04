#!/usr/bin/env python3
"""Dom at en besøgendes browser faktisk melder sine uventede fejl — og ikke noget andet.

Målt 5/10: `reportWorkerError` i `site/_worker.js` dækker kun workerens egen
fetch. Alt der går galt i `site/track.js` eller i en af de 300 sider der
indlæser den, efterlod hverken en 500, en log eller en Sentry-hændelse — og
det er præcis dér en købsvej dør: en knap der stopper med at virke, uden at
nogen kan se det. Sentry sagde «ingen uløste fejl de seneste 14 dage», fordi
der ikke var noget at se.

Denne port dømmer de elleve regler, der gør det trygt og virkningsfuldt:

 1. **Klienten lytter.** `window.addEventListener('error' …)` og
    `unhandledrejection` skal begge findes i `site/track.js`.
 2. **Den sender til workerens egen indsamling**, `/api/client-error` — ikke
    direkte til Sentry fra browseren. En direkte post ville give alle
    300 sider hver sin DSN.
 3. **Den sender seks felter, ikke flere.** `message`, `name`, `file`, `line`,
    `col` og `kind`.
 4. **Den sender ikke siden.** `page` må ikke findes i klienten. Ruten udleder
    ruten af `referer` server-side, så den URL en bruger indtaster i
    `/compliance-site-check` eller `/scan` kan ikke komme med.
 5. **Ruten accepterer præcis de seks.** `CLIENT_ERROR_FIELDS` skal være den
    lukkede mængde, og et krop med en syvende nøgle skal give 400 — ellers er
    «send ikke noget brugeren har skrevet» en vane og ikke en regel.
 6. **Ruten afleder routen af `referer`, ikke af klienten.** Der må ikke stå
    `body.page`.
 7. **Ingen persondata i rapporten.** `request`-objektet må kun have `url` og
    `method`, og `url` skal være `origin` + den normaliserede rute.
 8. **Kun i produktion.** `SENTRY_LOCAL_HOSTS` skal vende `handleClientError`,
    og klienten skal kræve et af de fire familiedomæner — en fork eller en
    `*.pages.dev`-forhåndsvisning må ikke fylde produktionsprojektet.
 9. **Dæmpet to steder og på en egen tæller.** `CLIENT_ERROR_MAX_PER_MINUTE`
    og `CLIENT_ERROR_MAX_PER_HOUR` skal være små tal, og tælleren må ikke
    være `sentrySeen` — den deler kvota med `/api/license/validate`.
10. **Adgangskontrol.** Samme origin- og refererkrav som `/api/track`, så
    Sentry-projektet ikke er en åben skraldespand for en fremmed side.
11. **Rapporteringen kan ikke kaste.** `handleClientError` skal starte med
    `try {` og have sin egen `catch`.

    python3 tools/check_client_errors.py            # dom opsætningen
    python3 tools/check_client_errors.py --self-test # 9 mutationer
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORKER = ROOT / "site" / "_worker.js"
TRACK = ROOT / "site" / "track.js"
ALLOWED_FIELDS = {"message", "name", "file", "line", "col", "kind"}


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

    Samme grund som i `check_sentry_setup.py`: denne fils docblock og
    `track.js`'s kommentarer nævner præcis de feltnavne, porten forbyder. Uden
    dette ville dom 4 og 5 være grønne fordi en kommentar siger «page».
    Blokkommentarer og hele `//`-linjer maskeres; `https://` i en streng må
    ikke blive spist.
    """
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    return re.sub(r"(?m)^[ \t]*//.*$", "", text)


def judge(worker: str, track: str) -> list[tuple[bool, str]]:
    w = strip_comments(worker)
    t = strip_comments(track)
    ce = block(w, "async function handleClientError")
    out: list[tuple[bool, str]] = []

    # 1 + 2 — klienten lytter og sender til workerens rute
    out.append(("addEventListener('error'" in t, "1. klienten lytter på window error"))
    out.append(("addEventListener('unhandledrejection'" in t,
                "1b. klienten lytter på unhandledrejection"))
    out.append(("'/api/client-error'" in t and "sendSentryEnvelope" not in t,
                "2. klienten sender til workerens egen /api/client-error"))

    # 3 + 4 — de seks felter, og ingen side
    payload = block(t, "var payload = JSON.stringify(") or block(t, "JSON.stringify({\n")
    keys = sorted(set(re.findall(r"^\s*([a-z]+):", payload, re.M)))
    out.append((set(keys) <= ALLOWED_FIELDS and len(keys) == 6,
                f"3. klienten sender de seks tilladte felter — fandt {len(keys)}: {keys}"))
    out.append(("page:" not in t,
                "4. klienten sender ikke siden (`page:`) — ruten udleder den af referer"))
    out.append(("location.href" not in t and "location.search" not in t,
                "4b. klienten læser ikke hele URL'en — query-strengen er der brugeren skriver sin adresse ind"))

    # 5 — ruten accepterer præcis de seks
    fields = re.search(r"CLIENT_ERROR_FIELDS = new Set\(\[([^\]]*)\]\)", w)
    felt = set(re.findall(r"'([a-z]+)'", fields.group(1))) if fields else set()
    out.append((felt == ALLOWED_FIELDS,
                f"5. CLIENT_ERROR_FIELDS er de seks tilladte — fandt {sorted(felt) or 'tom'}"))
    out.append(("!CLIENT_ERROR_FIELDS.has(key)" in ce and "Unexpected field." in ce,
                "5b. ruten afviser et uventet felt (400)"))

    # 6 — routen kommer fra referer
    out.append(("body.page" not in ce and "normalizeTrackedPath(refererUrl.pathname)" in ce,
                "6. ruten læser ikke siden i kroppen, men udleder den af referer"))

    # 7 — ingen persondata i rapporten
    req = re.search(r"request:\s*\{(.*?)\}\s*,\s*exception", ce, re.S)
    rkeys = sorted(set(re.findall(r"([A-Za-z_]+)\s*:", req.group(1)))) if req else []
    out.append((bool(req) and set(rkeys) <= {"url", "method"},
                f"7. `request` har kun url+method — fandt {rkeys or 'intet'}"))
    out.append(("url.origin" in ce and "${route}" in ce and "url.search" not in ce,
                "7b. rapport-URL'en er origin + rute uden query-streng"))
    # Kun det at *sende* headers. `request.headers.get('origin')` er dom 10 og
    # skal være der — en bred `request\.headers` ville give en rød port på den
    # kontrol der lukker ruten.
    for pat, label in ((r"user_agent|userAgent|user-agent", "7c. rapporten sender ikke user-agent"),
                       (r"headers:\s*request\.headers|headers:\s*\{\s*\.\.\.request", "7d. rapporten sender ikke headers")):
        out.append((not re.search(pat, ce), label))

    # 8 — kun i produktion
    out.append(("SENTRY_LOCAL_HOSTS.has(url.hostname)" in ce,
                "8. ruten sender ikke rapporter fra en lokal kørsel"))
    out.append(("ERROR_HOSTS" in t and "pages.dev" not in t and "location.hostname" in t,
                "8b. klienten sender kun fra de fire familiedomæner"))

    # 9 — dæmpning på en egen tæller
    for navn, maks in (("CLIENT_ERROR_MAX_PER_MINUTE", 5), ("CLIENT_ERROR_MAX_PER_HOUR", 30)):
        m = re.search(rf"{navn} = (\d+)", w)
        out.append((bool(m) and int(m.group(1)) <= maks,
                    f"9. {navn} er dæmpet til et lille tal — fandt {m.group(1) if m else 'intet'}"))
    # 9b dømmer på *kaldet*, ikke på navnet: mutationen «tælleren deles med
    # workerens» bytter `browserSentryRateLimited(` ud med `sentryRateLimited(`
    # og lader alle navne være i fred. En tæller der skriver i `sentrySeen` er
    # den samme kvota som `/api/license/validate` bruger, så det skal kunne
    # fejle — derfor kræver dommen både at kaldet er det private og at den
    # private tæller selv skriver i sit eget kort.
    counter = block(w, "function browserSentryRateLimited")
    out.append(("browserSentryRateLimited(" in ce and "browserSentrySeen" in counter,
                "9b. browserens tæller er en egen (workerens deler kvota med /api/license/validate)"))

    # 10 — adgangskontrol
    out.append(("request.headers.get('origin') !== url.origin" in ce,
                "10. ruten kræver samme origin"))
    out.append(("refererUrl.origin !== url.origin" in ce,
                "10b. ruten kræver en referer på samme domæne"))

    # 11 — kan ikke kaste
    out.append((bool(re.match(r"^\{\s*try\s*\{", ce)) and "catch" in ce,
                "11. handleClientError er pakket i sin egen try/catch"))
    out.append(("if (path === '/api/client-error')" in w,
                "11b. ruten er dispatcheret"))
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args(argv)

    if args.self_test:
        return self_test()

    results = judge(WORKER.read_text(encoding="utf-8"), TRACK.read_text(encoding="utf-8"))
    problems = 0
    for ok, msg in results:
        print(("  ok  " if ok else "FEJL  ") + msg)
        if not ok:
            problems += 1
    print(f"Klientfejl: {len(results)} kontroller, {problems} problemer")
    return 1 if problems else 0


MUTATIONS: list[tuple[str, str, str, str]] = [
    # (navn, fil, søg, erstat) — hver især skal gøre porten rød.
    ("error-lytteren fjernet", "track", r"window\.addEventListener\('error',[\s\S]*?\n  \}\);", ""),
    ("rejection-lytteren fjernet", "track", r"window\.addEventListener\('unhandledrejection',[\s\S]*?\n  \}\);", ""),
    ("siden sendes med", "track", r"(\n        kind: kind,)", r"\1\n        page: location.pathname,"),
    ("hele URL'en sendes med", "track", r"file: String\(file \|\| ''\)", "file: String(location.href + (file || ''))"),
    ("et uventet felt accepteres", "worker",
     r"CLIENT_ERROR_FIELDS = new Set\(\[([^\]]*)\]\)",
     "CLIENT_ERROR_FIELDS = new Set([\\1, 'href'])"),
    ("feltet accepteres i stedet for at afvises", "worker",
     r"if \(!CLIENT_ERROR_FIELDS\.has\(key\)\) \{", "if (false) {"),
    ("siden læses i kroppen", "worker", r"const route = normalizeTrackedPath\(refererUrl\.pathname\);",
     "const route = normalizeTrackedPath(body.page || refererUrl.pathname);"),
    ("query-strengen sendes med", "worker", r"\$\{url\.origin\}\$\{route\}", "${request.url}"),
    ("localhost-værnet fjernet", "worker",
     r"if \(SENTRY_LOCAL_HOSTS\.has\(url\.hostname\)\) return privateJsonResp\(\{ ok: true \}\);", ""),
    ("timekvoten fjernet", "worker", r"const CLIENT_ERROR_MAX_PER_HOUR = 20;", "const CLIENT_ERROR_MAX_PER_HOUR = 100000;"),
    ("tælleren deles med workerens", "worker", r"browserSentryRateLimited\(", "sentryRateLimited("),
    ("klienten sender fra alle værter", "track", r"if \(!ERROR_HOSTS\.test\(location\.hostname\)\) return;", ""),
    ("ruten er ikke dispatcheret", "worker", r"if \(path === '/api/client-error'\)", "if (false)"),
]


def self_test() -> int:
    worker = WORKER.read_text(encoding="utf-8")
    track = TRACK.read_text(encoding="utf-8")
    baseline = judge(worker, track)
    bad = [m for ok, m in baseline if not ok]
    if bad:
        print("FEJL: den ændrede kode er ikke grøn, så selvtesten måler intet:")
        for m in bad:
            print("  - " + m)
        return 1

    failures = 0
    for name, fil, pattern, repl in MUTATIONS:
        src = track if fil == "track" else worker
        mutated, n = re.subn(pattern, repl, src, count=1)
        if n == 0:
            print(f"FEJL: mutationen «{name}» ramte ikke koden — porten ville være grøn af vilje")
            failures += 1
            continue
        # Rigtig fil skal mutationeres ind i `judge`s to parametre. Fejl her
        # lader alle mutationer se ud som at ramme dom 1, hvilket er grønt uden
        # at sige noget om den dom de egentlig ville ramme.
        if fil == "worker":
            reds = [m for ok, m in judge(mutated, track) if not ok]
        else:
            reds = [m for ok, m in judge(worker, mutated) if not ok]
        if not reds:
            print(f"FEJL: mutationen «{name}» gav en grøn port — dommen kan ikke fejle")
            failures += 1
        else:
            print(f"  ok  mutation «{name}» → {reds[0]}")
    print(f"Klientfejl-selftest: {len(MUTATIONS)} mutationer, {failures} problemer")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
