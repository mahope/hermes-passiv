#!/usr/bin/env python3
"""Gaten for ruter, hvis eneste handling ikke virker.

Baggrund (review-fund 1/10, målt samme dag): `POST /api/compliance-ai` svarede
**503** «AI service not configured. Contact the site owner.», fordi
`OPENROUTER_API_KEY` mangler på workeren. `curl -X POST` mod live gav samme
svar med `cf-cache-status: DYNAMIC`, så det ikke var en cached fejl. Begge
sider — `/compliance-ai` og `/da/compliance-ai` — stod i `sitemap.xml` og i
`llms.txt`, og artikler på begge sprog linker til dem.

Det er den værste slags fejl at publicere: siden *lover* et svar, dens eneste
handling fejler altid, og den fejlskyldige er en besøgende, der har skrevet et
helt spørgsmål og får at kontakte os. Den nye Sentry-guard kan ikke fange den,
fordi 503 her er en *håndteret* tilstand og ikke kaster.

Rettelsen er delt, fordi kun den ene halv er min:

- **Workeren** svarer nu på `GET /api/compliance-ai` med `{available: bool}`.
  Det er et kapabilitets-tjek: ingen betalt opkald, ingen rate-limit-slot, ingen
  tilstand. Sidesiden bruger det til at sige det *før* spørgsmålstasten, i stedet
  for bagefter — og chatten kommer tilbage af sig selv, når nøglen sættes.
- **Siderne** får `noindex,follow`, som `build_sites.py` altid har honouret, så
  de forsvinder af sitemap, `llms.txt` og `llms-full.txt` — men ikke af
  artiklernes links, fordi der er brugere der kommer den vej, og siden siger nu
  det ærligt og byder på scanneren, erklæringsgeneratoren og de tre bøger.

Denne port gør fejlformen permanent rød. Seks kontroller pr. rute:

  1. `listed_in_sitemap`   ruten står i dist-sitemap for domænet. Den er så
                           stadig fundet af Google som svaret på et spørgsmål.
  2. `listed_in_llms`      ruten står i `llms.txt` eller `llms-full.txt`, altså
                           i den maskinlæsbare routeliste vi selv uddeler.
  3. `page_indexable`      kildesiden mangler `noindex`. Uden den er 1 og 2
                           kun tilfældigt væk, fordi nogen på et tidspunkt
                           redigerede meta'en.
  4. `page_no_notice`      siden har ingen ærlig erstatning. Et `noindex` er
                           nok til at holde Google ude, men en besøgende fra
                           en artikel lander stadig på siden, og så skal den
                           sige hvorfor chatten er væk — ikke vise et felt der
                           ikke virker.
  5. `page_no_probe`       siden læser ikke `available`. Uden optaget faldet
                           forsvinder 4's besked aldrig, fordi koden der
                           spørger serveren er væk.
  6. `worker_no_probe`     handleren i workeren svarer ikke på GET med
                           `available`. Så er 5 død kode, og siden ender tilbage
                           ved «kontakt ejeren».

Kontrollerne læser *kilde* og *dist*, altså den fejl som faktisk er publiceret.
`--self-test` muterer de seks ting hver for sig, så porten kan ikke være grøn
af vilje.

Brug: `python3 tools/check_unavailable_routes.py [--self-test]`
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "tools" / "unavailable_routes.json"
WORKER = ROOT / "site" / "_worker.js"
DIST = ROOT / "dist"

REQUIRED = ("domain", "route", "page", "probe", "handler", "until", "restore", "reason")


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


def load_manifest() -> tuple[dict, list[tuple[str, str]]]:
    """Returnér (manifest, problemer). En port der læser en ugyldig fil er grøn af vilje."""
    raw = MANIFEST.read_text(encoding="utf-8")
    data = json.loads(raw)
    problems: list[tuple[str, str]] = []
    if not isinstance(data, dict) or not isinstance(data.get("routes"), list):
        return data, [("manifest_shape", "tools/unavailable_routes.json skal have en 'routes'-liste")]
    for entry in data["routes"]:
        route = str(entry.get("route", "?"))
        for field in REQUIRED:
            if not str(entry.get(field, "")).strip():
                problems.append(("no_" + field, f"{route}: '{field}' mangler eller er tom — uden den kan ruten ikke revideres om et halvt år"))
    return data, problems


def judge(manifest_text: str, worker: str, dist_root: Path, source_root: Path) -> list[tuple[bool, str]]:
    """Alle domme. Filerne læses som tekst, så en mutation kan gives ind her."""
    results: list[tuple[bool, str]] = []
    try:
        data = json.loads(manifest_text)
    except json.JSONDecodeError as exc:
        return [(False, f"manifest_ulydelig: {exc}")]
    entries = data.get("routes") if isinstance(data, dict) else None
    if not isinstance(entries, list):
        return [(False, "manifest_shape: 'routes' skal være en liste")]
    if not entries:
        return [(False, "manifest_empty: listen er tom — så dømmer porten ingenting, og den skal dømme de to ruter")]

    for entry in entries:
        route = str(entry.get("route", "?"))
        domain = str(entry.get("domain", ""))
        page_rel = str(entry.get("page", ""))
        probe = str(entry.get("probe", ""))
        handler = str(entry.get("handler", ""))

        for field in REQUIRED:
            if not str(entry.get(field, "")).strip():
                results.append((False, f"{route}: '{field}' mangler eller er tom — uden den kan ruten ikke revideres om et halvt år"))

        # 1. sitemap
        sitemap = dist_root / domain / "sitemap.xml"
        if not sitemap.exists():
            results.append((False, f"{route}: dist/{domain}/sitemap.xml findes ikke — kør build_sites.py før porten"))
        else:
            text = sitemap.read_text(encoding="utf-8")
            found = f"<loc>https://{domain}{route}</loc>" in text
            results.append((not found, f"{route}: {'liger stadig' if found else 'ikke'} i dist/{domain}/sitemap.xml"))

        # 2. llms.txt / llms-full.txt
        for name in ("llms.txt", "llms-full.txt"):
            path = dist_root / domain / name
            if not path.exists():
                results.append((False, f"{route}: dist/{domain}/{name} findes ikke — kør build_sites.py før porten"))
                continue
            text = path.read_text(encoding="utf-8")
            found = f"https://{domain}{route})" in text
            results.append((not found, f"{route}: {'liger stadig' if found else 'ikke'} i dist/{domain}/{name}"))

        # 3-5. kildesiden
        page = source_root / page_rel
        if not page.exists():
            results.append((False, f"{route}: {page_rel} findes ikke"))
        else:
            html = page.read_text(encoding="utf-8")
            robots = re.search(r'<meta\s+name="robots"\s+content="([^"]*)"', html, re.I)
            directives = robots.group(1).lower() if robots else ""
            indexable = "noindex" not in directives and "none" not in directives
            results.append((not indexable, f"{page_rel}: {'mangler' if indexable else 'har'} noindex (robots={directives or '—'})"))

            has_notice = 'id="aiUnavailable"' in html
            results.append((has_notice, f"{page_rel}: {'har' if has_notice else 'mangler'} en ærlig erstatning (id=\"aiUnavailable\") — ellers står en besøgende fra en artikel på et felt der ikke virker"))

            uses_probe = probe in html and re.search(r"\.\s*available\b", html) is not None and "askArea" in html
            results.append((uses_probe, f"{page_rel}: {'læser' if uses_probe else 'læser ikke'} `available` fra {probe} og tænder/skjuler chatten på svaret"))

        # 6. workeren
        body = block(worker, f"async function {handler}(")
        if not body:
            results.append((False, f"{route}: handleren {handler} findes ikke i site/_worker.js"))
        else:
            answers = "request.method === 'GET'" in body and re.search(r"available:\s*Boolean\(env\.OPENROUTER_API_KEY\)", body) is not None
            routed = f"'{probe}'" in worker
            results.append((answers, f"{handler}: {'svarer' if answers else 'svarer ikke'} på GET med `available` — siden kan ellers ikke vide at nøglen mangler"))
            results.append((routed, f"{probe}: {'er' if routed else 'er ikke'} routet i workerens ruttetabel"))

    return results


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--self-test", action="store_true", help="mutér de seks domme og kræv at porten bliver rød")
    ap.add_argument("--manifest", help="manifest-tekst (bruges af selvtesten)")
    ap.add_argument("--worker", help="worker-tekst (bruges af selvtesten)")
    args = ap.parse_args(argv)

    manifest_text = args.manifest if args.manifest is not None else MANIFEST.read_text(encoding="utf-8")
    worker = args.worker if args.worker is not None else WORKER.read_text(encoding="utf-8")

    if args.self_test:
        return self_test(manifest_text, worker)

    results = judge(manifest_text, worker, DIST, ROOT)
    problems = 0
    for ok, msg in results:
        print(("  ok  " if ok else "FEJL  ") + msg)
        if not ok:
            problems += 1
    print(f"Utilgængelige ruter: {len(results)} kontroller, {problems} problemer")
    return 1 if problems else 0


# (navn, fil relativ til repo-roden, søg, erstat) — hver især skal gøre porten
# rød. De dømmer den *publicerede* fejl, så der muteres både i kilden, i
# manifestet og i dist: en port der kun læser kilden ville være grøn, fordi
# kilden er netop det, der rettes.
MUTATIONS: list[tuple[str, str, str, str]] = [
    ("noindex fjernet fra EN", "site/compliance-ai.html",
     r'<meta name="robots" content="noindex,follow">\n', ''),
    ("noindex fjernet fra DA", "site/da/compliance-ai.html",
     r'<meta name="robots" content="noindex,follow">\n', ''),
    ("erstatningen fjernet", "site/compliance-ai.html",
     r'id="aiUnavailable"', 'id="aiUnavailableGone"'),
    ("siden læser ikke available", "site/compliance-ai.html",
     r'if \(d && d\.available\) return;', 'if (d) return;'),
    ("proben lyver altid 'available'", "site/_worker.js",
     r'available: Boolean\(env\.OPENROUTER_API_KEY\)', 'available: true'),
    ("compliance-ai i sitemap igen", "dist/mahope.tools/sitemap.xml",
     r'</urlset>', '  <url><loc>https://mahope.tools/compliance-ai</loc></url>\n</urlset>'),
    ("compliance-ai i llms.txt igen", "dist/mahope.tools/llms.txt",
     r'\Z', '\n- [AI](https://mahope.tools/compliance-ai): x\n'),
    ("ruten uden begrundelse", "tools/unavailable_routes.json",
     r'"reason": "Målt 1/10 13:00 UTC', '"reason_ude": "Målt 1/10 13:00 UTC'),
]


def _tree_files() -> list[str]:
    """Alle filer porten læser, som stier relative til repo-roden."""
    files = [str(p.relative_to(ROOT)) for p in (ROOT / "site").rglob("*.html")]
    files.append("site/_worker.js")
    files.append("tools/unavailable_routes.json")
    # Kun de genererede lister, ikke hele dist — den indeholder billeder.
    for domain in {entry["domain"] for entry in json.loads(MANIFEST.read_text(encoding="utf-8"))["routes"]}:
        for name in ("sitemap.xml", "llms.txt", "llms-full.txt"):
            files.append(str((DIST / domain / name).relative_to(ROOT)))
    return files


def self_test(manifest_text: str, worker: str) -> int:
    baseline = judge(manifest_text, worker, DIST, ROOT)
    bad = [m for ok, m in baseline if not ok]
    if bad:
        print("FEJL: den nuværende tilstand er ikke grøn, så selvtesten måler intet:")
        for m in bad:
            print("  - " + m)
        return 1

    originals = {rel: (ROOT / rel).read_text(encoding="utf-8") for rel in _tree_files()}
    failures = 0
    try:
        for name, rel, pattern, repl in MUTATIONS:
            source = originals[rel]
            mutated, n = re.subn(pattern, repl, source, count=1)
            if n == 0:
                print(f"FEJL: mutationen «{name}» ramte ikke {rel} — porten ville være grøn af vilje")
                failures += 1
                continue
            (ROOT / rel).write_text(mutated, encoding="utf-8")
            # Dommen skal læse den muterede tekst, ikke den vi startede med —
            # ellers ville en mutation i manifestet eller workeren være usynlig.
            manifest_arg = mutated if rel.endswith("unavailable_routes.json") else manifest_text
            worker_arg = mutated if rel.endswith("_worker.js") else worker
            reds = [m for ok, m in judge(manifest_arg, worker_arg, DIST, ROOT) if not ok]
            (ROOT / rel).write_text(source, encoding="utf-8")
            if not reds:
                print(f"FEJL: mutationen «{name}» gav en grøn port — dommen kan ikke fejle")
                failures += 1
    finally:
        for rel, text in originals.items():
            (ROOT / rel).write_text(text, encoding="utf-8")

    after = judge(manifest_text, worker, DIST, ROOT)
    if [m for ok, m in after if not ok] != bad:
        print("FEJL: selvtesten efterlod repoet i en anden tilstand end den startede i")
        failures += 1

    if failures:
        print(f"FEJL: {failures} mutationer holdt ikke")
        return 1
    print(f"Selvtest: {len(MUTATIONS)} mutationer, alle røde")
    return 0


if __name__ == "__main__":
    sys.exit(main())
