#!/usr/bin/env python3
"""Gate for at `hreflang` angiver *én* dansk søskende pr. engelsk side, opgave fra
planens NEXT_TASK 3 i `IMPLEMENTATION_PLAN.md`.

Planen bad om at finde ud af om de fire danske "orphan"-sider var oversættelser
af en engelsk artikel. Det viste sig ikke at være det fire gange — men målingen
fandt en fejl, der var værre end den fire manglende par: **to engelske sider
pegede på den samme danske søskende, og de to par var krydset rundt om hinanden.**

    EN /blog/monitor-website-github-actions-free ─┐
                                                  ├─→ DA /da/blog/site-health-github-actions-stak
    EN /blog/site-health-github-actions ───────────┘

Begge engelske sider erklærede altså at de var oversættelser af *den samme*
danske artikel. Beviset på at parene var krydset, er at de er oversættelser
parvis — `monitor-website-github-actions-free` ↔ `overvaag-hjemmeside-github-actions-gratis`
(12 mod 11 overskrifter i samme rækkefølge, samme to action-navne) og
`site-health-github-actions` ↔ `site-health-github-actions-stak` (8 mod 8
overskrifter, ord til ord). Google fik to sider der sagde "vi er samme artikel",
hvoraf ingen af dem var det.

Hvorfor ingen port så det. `build_sites.py:hreflang_pairs` bygger et dict hvor
`pairs[target][lang]` skrives for hver side der *peger* på target, så den der
skrives **sidst** vinder. En krydset par er derfor ikke en fejl bygget rejser på —
den er to sider der begge har en gyldig `<link>` i sig selv, og bygget tager
implicit sidste-vinder. Uden en port er det kun en redaktionel læsning der kan
finde den.

Gaten fejler ved:

1. **Flere sider i samme sprog peger på den samme modpartsside.** Ét `hreflang`-
   par pr. søskende: to EN-sider der begge erklærer en `hreflang="da"` til samme
   URL er ulovligt, og Google straffer det værre end et manglende par.
2. **Et par der ikke er gensidigt.** Hvis A siger "min `da` er B", skal B sige
   "min `en` er A". Ellers erklærer kun den ene side et par, og den anden side
   er for Googles søgning et backlink der ikke findes.

Begge måles i `dist/`, fordi det er der hreflang'en skrives: `build_sites.py`
skriver altsammen selv, og en kilde der *ligner* rigtig kan ende som en anden
URL end den der udgives.

Porten dømmer **ikke** om en side *skal* have en søskende. Der findes
danskoriginaler, og en port der krævede et par på enhver `/da/`-side ville
tvinge opgaven til at opfinde oversættelser. Det er en redaktionel vurdering,
ikke en måling — de fire orphan-sider står uændret af denne port.

    python3 tools/check_hreflang_pairs.py
    python3 tools/check_hreflang_pairs.py --self-test

Springes over, når intet er bygget, i samme mønster som de øvrige dist-gates.
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

RE_LANG = re.compile(r'<html[^>]*\blang="(da|en)"', re.I)
RE_CANONICAL = re.compile(r'<link rel="canonical" href="([^"]+)"', re.I)
RE_ALT = re.compile(r'<link rel="alternate" hreflang="([^"]+)" href="([^"]+)"', re.I)
RE_LINK = re.compile(r'<a [^>]*href="(/[a-z0-9][a-z0-9/-]*)(?:#[^"]*)?"[^>]*>(.*?)</a>', re.I | re.S)

OTHER = {"en": "da", "da": "en"}

# Et link, der *navner* det andet sprog, er et bevidst sprogskift og ikke en fejl.
# Det er den undtagelse, der gør de tre eksisterende "English version"-links
# lovlige; alt andet fra en dansk side til en side med dansk spejling er en
# dansk læser der bliver sendt på engelsk.
LANG_SWITCH = re.compile(r"engelsk|english", re.I)


def read_page(path: Path) -> tuple[str | None, str | None, dict[str, str]]:
    """(lang, canonical, {hreflang: href}) — `lang` er None for sider uden <html lang>."""
    text = path.read_text(encoding="utf-8", errors="ignore")
    m = RE_LANG.search(text[:600])
    lang = m.group(1).lower() if m else None
    c = RE_CANONICAL.search(text)
    return lang, (c.group(1) if c else None), dict(RE_ALT.findall(text))


def _domain_of(url: str) -> str:
    m = re.match(r"^https?://([^/]+)", url)
    return m.group(1) if m else ""


def check(root: Path = ROOT) -> list[str]:
    dist = root / "dist"
    problems: list[str] = []
    if not dist.is_dir():
        return problems

    # canonical-url -> fil. Canonical er nøglen, fordi en dist-fil kan ligge på
    # en rute der ikke matcher sin canonical (alias-kopier, se
    # `hreflang_pairs`' `alias`), og det er canonical der udgives.
    by_url: dict[str, Path] = {}
    by_file: dict[Path, str] = {}
    for f in sorted(dist.rglob("*.html")):
        lang, canon, _ = read_page(f)
        if canon:
            by_url.setdefault(canon, f)
            by_file.setdefault(f, canon)

    # hvilke sider der peger på hvilken modpart, pr. (domæne, modparts-URL)
    claims: dict[tuple[str, str], list[tuple[str, Path]]] = defaultdict(list)
    for url, f in sorted(by_url.items()):
        lang, _, alts = read_page(f)
        if not lang:
            continue  # 404 og lignende uden sprog: ikke en søskende
        other = OTHER[lang]
        target = alts.get(other)
        if target:
            claims[(_domain_of(url), target)].append((lang, f))

    # 0 — en dansk side der linker til den engelske udgave af en side, der findes
    #     på dansk. hreflang er *ikke* nok her: det fortæller Google at der findes
    #     en søskende, men læseren bliver sendt på engelsk alligevel. Det er den
    #     fejl, der lå i 11 danske blogsider (33 links) før denne kontrol.
    #     Ruten bygges på canonical, fordi et rodrelativt link `/page-profile`
    #     kun kan slås op mod det domæne, siden selv ligger på.
    da_routes: dict[str, set[str]] = defaultdict(set)
    for url in by_url:
        root_path = re.sub(r"^https?://[^/]+", "", url).rstrip("/")
        if root_path.startswith("/da/"):
            da_routes[_domain_of(url)].add(root_path)

    for f, url in sorted(by_file.items()):
        lang, _, _ = read_page(f)
        if lang != "da":
            continue
        text = f.read_text(encoding="utf-8", errors="ignore")
        for m in RE_LINK.finditer(text):
            target = m.group(1).rstrip("/") or "/"
            if target.startswith("/da/"):
                continue
            if LANG_SWITCH.search(re.sub(r"<[^>]+>", "", m.group(2))):
                continue  # bevidst sprogskift
            da_target = "/da" + target
            if da_target in da_routes.get(_domain_of(url), ()):
                problems.append(
                    f"{f.relative_to(dist).as_posix()} er lang=\"da\" men linker til "
                    f"{target}, som findes på dansk som {da_target} — enten link til "
                    f"{da_target}, eller skriv at linket er engelsk i linkteksten")

    # 1 — flere sider i samme sprog på én modpartsside
    for (_domain, target), claimants in sorted(claims.items()):
        by_lang: dict[str, list[Path]] = defaultdict(list)
        for lang, f in claimants:
            by_lang[lang].append(f)
        for lang, files in sorted(by_lang.items()):
            if len(files) < 2:
                continue
            rels = ", ".join(sorted(f.relative_to(dist).as_posix() for f in files))
            problems.append(
                f"{len(files)} {lang}-sider peger alle på {target} med "
                f"hreflang=\"{OTHER[lang]}\": {rels} — ét par pr. søskende; "
                f"Google straffer et krydset par værre end et manglende")

    # 2 — par der ikke er gensidigt
    for (_domain, target), claimants in sorted(claims.items()):
        tfile = by_url.get(target)
        if tfile is None:
            for lang, f in claimants:
                problems.append(
                    f"{f.relative_to(dist).as_posix()} peger med hreflang=\"{OTHER[lang]}\" "
                    f"på {target}, som ikke findes i dist/ — parret kan ikke være gensidigt")
            continue
        tlang, _, talts = read_page(tfile)
        back = OTHER[tlang] if tlang else None
        for lang, f in claimants:
            back_to = talts.get(back or "")
            if back_to == by_file.get(f):
                continue
            problems.append(
                f"{f.relative_to(dist).as_posix()} siger hreflang=\"{OTHER[lang]}\" → {target}, "
                f"men {tfile.relative_to(dist).as_posix()} svarer ikke tilbage"
                + (f" (den har hreflang=\"{back}\" → {back_to})" if back_to
                   else f" (den har ingen hreflang=\"{back}\")"))
    return problems


def _fixture(root: Path, pages: dict[str, tuple[str, dict[str, str]]]) -> None:
    """Skriver en minimal dist. `pages` er filsti -> (lang, {hreflang: href}).

    Canonical udledes af *filstien*, som bygget gør: `da/x.html` får
    `https://mahope.tools/da/x`. Derfor skal hreflang-værdierne i scenarierne pege
    på de samme urls.
    """
    d = root / "dist" / "mahope.tools"
    d.mkdir(parents=True, exist_ok=True)
    for rel, (lang, alts) in pages.items():
        f = d / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        canon = "https://mahope.tools/" + rel[:-len(".html")]
        links = "".join(
            f'<link rel="alternate" hreflang="{k}" href="{v}">' for k, v in alts.items())
        f.write_text(
            f'<!doctype html><html lang="{lang}"><head><title>T</title>'
            f'<link rel="canonical" href="{canon}">{links}</head><body>x</body></html>',
            encoding="utf-8")


def _reset(root: Path) -> None:
    """Tøm dist mellem scenarier, så en tidligere fixtures fil ikke hænger ved."""
    d = root / "dist"
    if d.is_dir():
        import shutil

        shutil.rmtree(d)


def _pair(da: str) -> dict[str, tuple[str, dict[str, str]]]:
    """Et rent, gensidigt EN/DA-par hvor den danske fil hedder `da`."""
    return {
        "a.html": ("en", {"en": "https://mahope.tools/a",
                          "da": f"https://mahope.tools/da/{da}"}),
        f"da/{da}.html": ("da", {"da": f"https://mahope.tools/da/{da}",
                                 "en": "https://mahope.tools/a"}),
    }


def self_test() -> int:
    """Bevis at gaten fanger hver fejlform, den siger at fange."""
    import tempfile

    scenarios: list[tuple[str, list[str]]] = []
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)

        # kontrol: et rent par skal være grønt
        _fixture(root, _pair("a-da"))
        control = check(root)
        if control:
            for p in control:
                print(f"KONTROLFEJL: {p}", file=sys.stderr)
            return 1

        # 1 — to EN-sider der begge erklærer den samme DA. Det er fejlen der
        #     lå i dist/ før denne port: /blog/monitor-website-github-actions-free
        #     og /blog/site-health-github-actions pegede begge på
        #     /da/blog/site-health-github-actions-stak.
        _reset(root)
        _fixture(root, {
            "a.html": ("en", {"da": "https://mahope.tools/da/x"}),
            "b.html": ("en", {"da": "https://mahope.tools/da/x"}),
            "da/x.html": ("da", {"en": "https://mahope.tools/a"}),
        })
        scenarios.append(("to EN-sider peger på samme DA-side", check(root)))

        # 2 — et par der ikke er gensidigt: EN erklærer DA, DA svarer ikke tilbage
        _reset(root)
        _fixture(root, {
            "a.html": ("en", {"da": "https://mahope.tools/da/x"}),
            "da/x.html": ("da", {"da": "https://mahope.tools/da/x"}),
        })
        scenarios.append(("DA-side svarer ikke tilbage på EN", check(root)))

        # 3 — gensidigt par der peger på en side der ikke findes i dist
        _reset(root)
        _fixture(root, {
            "a.html": ("en", {"da": "https://mahope.tools/da/Findes-ikke"}),
        })
        scenarios.append(("hreflang peger på en side der ikke findes", check(root)))

        # 4 — kontrol: en danskoriginal UDEN søskende er lovlig. Porten dømmer
        #     par, ikke isolation — ellers tvinge den opgaven til at opfinde
        #     oversættelser, og de fire orphan-sider er netop sådan.
        _reset(root)
        _fixture(root, _pair("a-da"))
        (root / "dist" / "mahope.tools" / "da" / "original.html").write_text(
            '<!doctype html><html lang="da"><head><title>T</title>'
            '<link rel="canonical" href="https://mahope.tools/da/original">'
            '<link rel="alternate" hreflang="da" href="https://mahope.tools/da/original">'
            "</head><body>x</body></html>", encoding="utf-8")
        if check(root):
            for p in check(root):
                print(f"KONTROLFEJL (danskoriginal skal være lovlig): {p}", file=sys.stderr)
            return 1

        # 5b — kontrol: en dansk side må gerne linke til den engelske udgave,
        #      når linkteksten siger at den er engelsk. Uden undtagelsen ville
        #      porten tvinge de tre "English version"-links væk — de er netop
        #      det de danske læsere har brug for.
        _reset(root)
        _fixture(root, {
            "a.html": ("en", {"da": "https://mahope.tools/da/a"}),
            "da/a.html": ("da", {"en": "https://mahope.tools/a"}),
        })
        (root / "dist" / "mahope.tools" / "da" / "x.html").write_text(
            '<!doctype html><html lang="da"><head><title>T</title>'
            '<link rel="canonical" href="https://mahope.tools/da/x">'
            "</head><body>"
            '<a href="/a">English version</a>'
            '<a href="/a">Se den engelske udgave</a>'
            "</body></html>", encoding="utf-8")
        if check(root):
            for p in check(root):
                print(f"KONTROLFEJL (bevidst sprogskift skal være lovligt): {p}", file=sys.stderr)
            return 1

        # 6 — en dansk side der linker til en rute, der findes på dansk
        _reset(root)
        _fixture(root, {
            "page-profile.html": ("en", {"da": "https://mahope.tools/da/page-profile"}),
            "da/page-profile.html": ("da", {"en": "https://mahope.tools/page-profile"}),
        })
        (root / "dist" / "mahope.tools" / "da" / "blog.html").write_text(
            '<!doctype html><html lang="da"><head><title>T</title>'
            '<link rel="canonical" href="https://mahope.tools/da/blog">'
            "</head><body>"
            '<a href="/page-profile" class="btn-primary">Prøv Page Profile gratis</a>'
            '<a href="/scan">Kør en scanning</a>'
            "</body></html>", encoding="utf-8")
        got = check(root)
        if len(got) != 1 or "som findes på dansk som /da/page-profile" not in got[0]:
            for p in got:
                print(f"KONTROLFEJL: uventet {p!r}", file=sys.stderr)
            return 1
        scenarios.append(("dansk side linker til engelsk udgave af en dansk side", got))

        # 6b — samme fejl, men med et anker. Fragmentet må ikke gøre linket
        #      usynligt for porten: en dansk læser sendes stadig til den
        #      engelske side, blot længere ned på den.
        _reset(root)
        _fixture(root, {
            "page-profile.html": ("en", {"da": "https://mahope.tools/da/page-profile"}),
            "da/page-profile.html": ("da", {"en": "https://mahope.tools/page-profile"}),
        })
        (root / "dist" / "mahope.tools" / "da" / "activate.html").write_text(
            '<!doctype html><html lang="da"><head><title>T</title>'
            '<link rel="canonical" href="https://mahope.tools/da/activate">'
            "</head><body>"
            '<a href="/page-profile#pro">Aktivér her</a>'
            "</body></html>", encoding="utf-8")
        got = check(root)
        if len(got) != 1 or "som findes på dansk som /da/page-profile" not in got[0]:
            for p in got:
                print(f"KONTROLFEJL: uventet {p!r}", file=sys.stderr)
            return 1
        scenarios.append(("dansk side linker til engelsk side med anker", got))

        # 5 — kontrol: 404 uden <html lang> må ikke fejle
        _reset(root)
        _fixture(root, _pair("a-da"))
        (root / "dist" / "mahope.tools" / "404.html").write_text(
            "<!doctype html><html><head><title>404</title></head><body>x</body></html>",
            encoding="utf-8")
        if check(root):
            for p in check(root):
                print(f"KONTROLFEJL (404 skal være lovlig): {p}", file=sys.stderr)
            return 1

    for name, problems in scenarios:
        if not problems:
            print(f"SELFTEST FEJLEDE: scenariet '{name}' gav ingen fejl — porten er død",
                  file=sys.stderr)
            return 1
        print(f"  fanget: {name} ({len(problems)} problem(er))")
    print(f"selftest grøn: {len(scenarios)} fejlformer fanget, 3 positive kontroller grønne")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true",
                    help="bevis at porten fanger de fejlformer den siger at fange")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    problems = check()
    if problems:
        print(f"hreflang-par: {len(problems)} problem(er)", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1
    print("hreflang-par: grøn — hver søskende har ét gensidigt par")
    return 0


if __name__ == "__main__":
    sys.exit(main())
