#!/usr/bin/env python3
"""Gate for at strukturerede data er *erklærede*, ikke tilfældige, opgave 32 i
`IMPLEMENTATION_PLAN.md`.

To foregående iterationer rettede den samme fejlform ved at skrive JSON-LD
hånd i markup pr. side: først de danske købssider, så to blogartikler. Hver
gang blev den grebet af en måling, der målte det *ene* par, og hver gang
havde porten et tal, hun ikke burde have brugt. Denne port måler derfor ikke
*antallet* af blokke — to blokke kan stadig miste en `SoftwareApplication`, præcis
som `/da/` på cleancopy gjorde — men **hvilke `@type` der er**, i `dist/`, som
er det der faktisk udgives.

Den fejl den skal fange er konkret og allerede målt. `pagepass.normalize_head`
læste sine JSON-LD-blokke i `<head>`, så en forfatter der lagde sin blok i
`<body>` så ud som om siden ingen havde. Følgen var, at `/da/page-profile` fik
en `WebPage`/`WebSite`/`Person`-node injiceret, mens `/page-profile` (samme
blok, bare i `<head>`) ikke fik nogen. Ingen havde valgt det, og ingen port
kunne se det: antallet af blokke var forskelligt på begge veje, så det så
ud som om de to sider bare ikke var ens.

Gaten fejler ved:

1. **EN/DA-par har ikke samme typer.** Hver route der findes på begge sider af
   `/da/` skal have præcis samme sæt af `@type` — ikke bare samme antal
   blokke. En dansk søgning må ikke se en anden enhed end den engelske.
2. **En udgivet side uden strukturerede data.** Nul blokke er lovlig for
   `404.html` (de er erklæret undtagen, fordi de ikke er sider, Google skalfinde) og
   intet andet.
3. **En node der står to gange i samme række.** Målt 30/9: `/downloads`
   erklærede sit gratis-tilbud to gange i samme `offers`-række, identiske
   bortset fra en `description` — en artefakt af to merge. Det er præcis den
   fejlform de to første punkter ikke kan se: sættet af `@type` er uændret, så
   en port der tæller typer er grøn, mens siden siger tilbuddet dobbelt så
   mange gange som der er. Rækker af `@type`-objekter (`offers`,
   `itemListElement`, `hasPart`, `breadcrumb`, `@graph`) dømmes derfor på
   *indhold*, ikke på type.
4. **En blok der ikke er JSON.** Ellers er alle tre punkter døve for den side,
   hvis blok en redaktør har knækket — de læser kun `@type` med en regex, og
   en knækket blok har ingen.

Kun *par på samme route*. Oversatte blog-slugs (`bug-reports-in-ci-pipeline` ↔
`bugrapporter-i-ci-pipeline`) matcher ikke på route, og det er korrekt: de
findes gennem `hreflang`, som `check_sitemaps` og sitemapens
`xhtml:link` dømmer. At gaten også ville finde dem, hvis slugsne var ens, er
grunden til at kun route-par er minimum og ikke hele historien.

    python3 tools/check_jsonld_types.py
    python3 tools/check_jsonld_types.py --self-test

Springes over, når intet er bygget, i samme mønster som de øvrige dist-gates.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"

RE_LD = re.compile(r"<script[^>]+application/ld\+json[^>]*>(.*?)</script>", re.S | re.I)
RE_TYPE = re.compile(r'"@type"\s*:\s*"([A-Za-z][A-Za-z0-9]*)"')

# Nøgler der genfortæller en node i prosa uden at være en del af dens identitet.
# `description` er den eneste her, og det er den der gjorde fundet muligt: de to
# tilbud på /downloads var ens i `name`, `price` og `priceCurrency`, så uden
# denne undtagelse ville de set ud til at være to forskellige tilbud.
FREE_TEXT = ("description",)

# Felter der identificerer en node i en fejlbesked. Rækkefølgen er valgt, så den
# første eksisterende giver den mest læsbare tekst.
IDENTITY = ("name", "item", "url", "price", "priceCurrency", "position", "@type")

# Sider der loesligt har nul blokke. 404 er ikke sider — de er svar på en adresse
# der ikke findes, og de skal ikke beskrives som om de gør.
NO_LD_OK = ("404.html",)


def _types_in_block(block: str) -> set[str]:
    return set(RE_TYPE.findall(block))


def page_types(path: Path) -> set[str]:
    """Alle `@type` i alle JSON-LD-blokke i filen, uanset hvor de ligger."""
    text = path.read_text(encoding="utf-8", errors="ignore")
    found: set[str] = set()
    for match in RE_LD.finditer(text):
        found |= _types_in_block(match.group(1))
    return found


def n_blocks(path: Path) -> int:
    text = path.read_text(encoding="utf-8", errors="ignore")
    return len(RE_LD.findall(text))


def _identity(node: dict) -> str:
    """Kort, læsbar beskrivelse af en node til brug i en fejlbesked."""
    parts: list[str] = []
    for key in IDENTITY:
        value = node.get(key)
        if value in (None, "", [], {}):
            continue
        if isinstance(value, str):
            parts.append(f"{key}={value[:40]!r}")
        else:
            parts.append(f"{key}={json.dumps(value, ensure_ascii=False)[:40]}")
        if len(parts) == 3:
            break
    return ", ".join(parts) or str(node.get("@type", "(uden @type)"))


def _fingerprint(node: dict) -> str:
    """En nodes identitet uden prosa: alt bortset fra FREE_TEXT, sorteret."""
    trimmed = {k: v for k, v in node.items() if k not in FREE_TEXT}
    return json.dumps(trimmed, sort_keys=True, ensure_ascii=False)


def _typed_lists(node, path: str = ""):
    """Alle rækker i træet hvis elementer er `@type`-objekter.

    Det er deres *indhold* der skal dømmes. En række af tal eller strenge har
    ingen `@type` og er ikke strukturerede data — den springes over.
    """
    if isinstance(node, dict):
        for key, value in node.items():
            if (isinstance(value, list) and len(value) > 1
                    and all(isinstance(v, dict) and "@type" in v for v in value)):
                yield path + "/" + key, value
            yield from _typed_lists(value, path + "/" + key)
    elif isinstance(node, list):
        for i, item in enumerate(node):
            yield from _typed_lists(item, f"{path}[{i}]")


def block_problems(block: str) -> list[str]:
    """Fejl i én JSON-LD-blok: knækket JSON, eller en node der står to gange."""
    try:
        data = json.loads(block)
    except ValueError as exc:
        return [f"blokken er ikke gyldig JSON ({exc}), så ingen @type i den tæller: "
                f"{block.strip()[:80]}"]

    problems: list[str] = []
    for path, items in _typed_lists(data):
        seen: dict[str, int] = {}
        for index, item in enumerate(items):
            sig = _fingerprint(item)
            if sig in seen:
                problems.append(
                    f"{path}[{index}] er det samme som {path}[{seen[sig]}] "
                    f"({_identity(item)}) — en node i en række er én ting, ikke "
                    "den samme ting to gange")
            else:
                seen[sig] = index
    return problems


def page_problems(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    problems: list[str] = []
    for i, match in enumerate(RE_LD.finditer(text)):
        for problem in block_problems(match.group(1)):
            problems.append(f"ld+json-blok {i + 1}: {problem}")
    return problems



def check(root: Path = ROOT) -> list[str]:
    dist = root / "dist"
    problems: list[str] = []
    if not dist.is_dir():
        return problems

    for domain_dir in sorted(p for p in dist.iterdir() if p.is_dir()):
        domain = domain_dir.name
        en: dict[str, Path] = {}
        da: dict[str, Path] = {}
        for f in sorted(domain_dir.rglob("*.html")):
            rel = f.relative_to(domain_dir).as_posix()
            (da if rel.startswith("da/") else en)[rel[3:] if rel.startswith("da/") else rel] = f

        for rel, f in sorted({**en, **da}.items()):
            if n_blocks(f) == 0 and f.name not in NO_LD_OK:
                problems.append(
                    f"{domain}/{rel} har 0 application/ld+json — hverken den danske "
                    f"eller den engelske udgave af en side skal stå uden strukturerede data")

            # Uafhængigt af EN/DA-parrene: hver udgivet sides rækker skal være
            # rækker af forskellige ting. Det måles pr. side, fordi en dublet er
            # en fejl i markup'en, ikke en forskel mellem sprogudgaverne.
            for problem in page_problems(f):
                problems.append(f"{domain}/{rel} {problem}")

        for rel in sorted(set(en) & set(da)):
            a, b = page_types(en[rel]), page_types(da[rel])
            if a == b:
                continue
            only_en, only_da = sorted(a - b), sorted(b - a)
            if only_en:
                problems.append(
                    f"{domain}/da/{rel} mangler de(n) type(s) den engelske side erklærer: "
                    f"{', '.join(only_en)} (EN har {', '.join(sorted(a)) or 'ingenting'}, "
                    f"DA har {', '.join(sorted(b)) or 'ingenting'})")
            if only_da:
                problems.append(
                    f"{domain}/{rel} mangler de(n) type(s) den danske side erklærer: "
                    f"{', '.join(only_da)} (DA har {', '.join(sorted(b))}, "
                    f"EN har {', '.join(sorted(a)) or 'ingeting'})")
    return problems


def _fixtures(root: Path, en_types: str = "SoftwareApplication", da_types: str | None = None,
              da_blocks: int = 1, n: int = 1) -> None:
    """Skriver en minimal dist med n EN/DA-par."""
    if da_types is None:
        da_types = en_types
    d = root / "dist" / "mahope.tools"
    (d / "da").mkdir(parents=True, exist_ok=True)
    def page(types: str) -> str:
        return ("<!doctype html><html lang=\"en\"><head><title>T</title></head><body>"
                "<script type=\"application/ld+json\">"
                + "".join('{"@context":"https://schema.org","@type":"%s"}' % t for t in types.split(","))
                + "</script></body></html>")
    for i in range(max(n, 1)):
        (d / f"tool-{i}.html").write_text(page(en_types), encoding="utf-8")
        blocks = "".join(
            '<script type="application/ld+json">{"@context":"https://schema.org","@type":"%s"}</script>' % t
            for t in da_types.split(",")[:da_blocks])
        (d / "da" / f"tool-{i}.html").write_text(
            f'<!doctype html><html lang="da"><head><title>T</title></head><body>{blocks}</body></html>',
            encoding="utf-8")


def _page_with_block(root: Path, name: str, block: str) -> None:
    """Skriver én udgivet side med én rå JSON-LD-blok (kan være med vilje ødelagt)."""
    d = root / "dist" / "mahope.tools"
    d.mkdir(parents=True, exist_ok=True)
    (d / name).write_text(
        '<!doctype html><html lang="en"><head><title>T</title></head><body>'
        '<script type="application/ld+json">' + block + "</script></body></html>",
        encoding="utf-8")


TWO_IDENTICAL_OFFERS = json.dumps({
    "@context": "https://schema.org", "@type": "SoftwareApplication", "name": "eaa-scanner",
    "offers": [
        {"@type": "Offer", "name": "Free", "price": "0", "priceCurrency": "USD"},
        {"@type": "Offer", "name": "Free", "price": "0", "priceCurrency": "USD",
         "description": "Single-page scans, whole-site crawls up to 200 pages"},
    ]})

TWO_DIFFERENT_OFFERS = json.dumps({
    "@context": "https://schema.org", "@type": "SoftwareApplication", "name": "eaa-scanner",
    "offers": [
        {"@type": "Offer", "name": "Free", "price": "0", "priceCurrency": "USD"},
        {"@type": "Offer", "name": "Pro", "price": "19", "priceCurrency": "USD"},
    ]})


def self_test() -> int:
    """Bevis at gaten fanger hver fejlform, den siger at fange."""
    import tempfile

    scenarios: list[tuple[str, list[str]]] = []
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)

        # kontrol: et rent par med samme typer skal være grønt
        _fixtures(root, en_types="SoftwareApplication,FAQPage", da_blocks=2)
        control = check(root)
        if control:
            for problem in control:
                print(f"KONTROLFEJL: {problem}", file=sys.stderr)
            return 1

        # 1 — den danske side mister en type den engelske har, men ANTALLET er
        #     uændret. Det er præcis den fejlform porten er skrevet til: to
        #     blokke på hver side, og alligevel en manglende SoftwareApplication.
        _fixtures(root, en_types="SoftwareApplication,FAQPage", da_types="FAQPage,Person", da_blocks=2)
        scenarios.append(("dansk side mister SoftwareApplication uden at antallet ændres",
                          check(root)))

        # 2 — den danske side har en ekstra type, fordi bygget injicerede en
        #     WebPage-node kun på den (/da/page-profile før rettelsen).
        _fixtures(root, en_types="SoftwareApplication", da_types="SoftwareApplication,WebPage,WebSite", da_blocks=3)
        scenarios.append(("dansk side har en ekstra WebPage/WebSite-node", check(root)))

        # 3 — en udgivet side helt uden strukturerede data
        _fixtures(root, en_types="SoftwareApplication")
        (root / "dist" / "mahope.tools" / "tom.html").write_text(
            "<!doctype html><html><head><title>t</title></head><body>ingenting</body></html>", encoding="utf-8")
        scenarios.append(("udgivet side med 0 ld+json", check(root)))

        # 4 — positiv kontrol: 404 er erklæret undtagen og må ikke slå
        _fixtures(root, en_types="SoftwareApplication")
        (root / "dist" / "mahope.tools" / "tom.html").unlink()
        (root / "dist" / "mahope.tools" / "404.html").write_text(
            "<!doctype html><html><head><title>404</title></head><body>ikke fundet</body></html>",
            encoding="utf-8")
        if check(root):
            for problem in check(root):
                print(f"KONTROLFEJL (404 skal være undtagen): {problem}", file=sys.stderr)
            return 1

        # 5 — DET FUND, PORTEN VAR DØV FOR: /downloads erklærede sit gratis-tilbud
        #     to gange i samme offers-række, ens bortset fra `description`.
        #     Sættet af @type er uændret, så punkt 1 og 2 er grønne.
        _fixtures(root, en_types="SoftwareApplication")
        _page_with_block(root, "downloads.html", TWO_IDENTICAL_OFFERS)
        scenarios.append(("samme tilbud to gange i én offers-række", check(root)))

        # 6 — positiv kontrol mod fejlretningen: to tilbud der FAKTISK er
        #     forskellige (gratis og betalt) skal være grønne. Uden denne ville
        #     punkt 5 være grøn, fordi porten afviser alt.
        (root / "dist" / "mahope.tools" / "downloads.html").unlink()
        _page_with_block(root, "two-prices.html", TWO_DIFFERENT_OFFERS)
        if check(root):
            for problem in check(root):
                print(f"KONTROLFEJL (to forskellige tilbud er lovlige): {problem}", file=sys.stderr)
            return 1
        (root / "dist" / "mahope.tools" / "two-prices.html").unlink()

        # 7 — en blok der ikke er JSON. En regex læser ingen @type i den, så
        #     uden dette punkt er siden grøn fordi porten er døv, ikke fordi
        #     structured data er korrekt.
        _page_with_block(root, "brudt.html", '{"@type":"WebSite", "offers":[}')
        scenarios.append(("ld+json-blok der ikke er gyldig JSON", check(root)))
        (root / "dist" / "mahope.tools" / "brudt.html").unlink()

    # 5 — en type i @graph skal tælles, ellers ville porten være døv for den
    #     blokform `pagepass` selv producerer.
    graph = '{"@context":"https://schema.org","@graph":[{"@type":"WebSite"}]}'
    if _types_in_block(graph) != {"WebSite"}:
        print("KONTROLFEJL: @graph-blok læses ikke", file=sys.stderr)
        return 1

    failed = 0
    for label, problems in scenarios:
        if problems:
            print(f"OK   {label}")
            for problem in problems:
                print(f"       {problem}")
        else:
            print(f"FORKERT: gaten fangede ikke — {label}", file=sys.stderr)
            failed += 1
    if failed:
        return 1
    print(f"check_jsonld_types selftest OK — {len(scenarios)} mutationer fanget, "
          "positiv kontrol grøn, ingen falske positiver")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true",
                        help="bevis at gaten fanger hver fejlform, den siger at fange")
    args = parser.parse_args()

    if args.self_test:
        return self_test()

    problems = check(ROOT)
    for problem in problems:
        print(f"FEJL: {problem}", file=sys.stderr)
    if problems:
        return 1
    if not DIST.is_dir():
        print("jsonld-types OK — intet bygget, porten springes over")
        return 0
    print("jsonld-types OK — EN/DA-par har samme @type, ingen udgivet side står "
          "uden strukturerede data, ingen blok er knækket JSON, og ingen række "
          "gentager den samme node")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
