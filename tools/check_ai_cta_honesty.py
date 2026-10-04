#!/usr/bin/env python3
"""Dommer AI-banneren på bloggen mod `tools/ai_cta.json`.

Baggrund (målt 1/10): `OPENROUTER_API_KEY` mangler på workeren, så
`GET /api/compliance-ai` svarer `available: false`, og `/compliance-ai` siger
til den besøgende, at assistenten ikke er slået til. Rettelsen 1/10 (`bda70e2`)
gjorde *siden* ærlig og tog den ud af sitemap — men banneren på hver AI-side
beholdt sit løfte, «a practical answer in seconds». Hver eneste knap førte
altså til en side, der siger, at løftet ikke kan holdes. Det er samme
fejlform som fund 1 i review 1/10, kun en etage længere nede: en offentlig
lovet handling, der altid fejler.

Derfor ligger sandheden i én fil, `tools/ai_cta.json`, og banneren er tegnet
af den. Denne port dømmer hver side i `site/` mod den:

  1. Ingen side må love et svar, mens `available` er false.
  2. Hver AI-banner skal være tegnet af manifestet — samme label, samme
     knap, samme mål. Ellers kan banner-siderne glide fra hinanden igen.
  3. Bannerens mål skal være en side, der findes i `site/`, og som siger det
     ærligt, når assistenten er slukket (`aiUnavailable`).

Brug:
    python3 tools/check_ai_cta_honesty.py            # dom
    python3 tools/check_ai_cta_honesty.py --apply    # tegn banneren igen
    python3 tools/check_ai_cta_honesty.py --self-test
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "tools" / "ai_cta.json"
SITE = ROOT / "site"

# Én banner pr. artikel, i to sprog og to knap-stilarter. Mønstret tager hele
# `div`-en, så en ny btn-klasse ikke kan smyge en gammel løftetekst ind.
BANNER_RE = re.compile(
    r'<div class="blog-tool-cta ai-cta">.*?</div>', re.DOTALL
)
LABEL_RE = re.compile(r'<span class="btc-label">(.*?)</span>', re.DOTALL)
LINK_RE = re.compile(
    r'<a href="([^"]*)" class="(btn-[a-z-]+) ai-cta-link" data-track="ai-cta">(.*?)</a>',
    re.DOTALL,
)


def load() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def pages() -> list[Path]:
    return sorted(p for p in SITE.rglob("*.html"))


def lang_of(path: Path) -> str:
    rel = path.relative_to(SITE).as_posix()
    return "da" if rel.startswith("da/") else "en"


def copy_for(m: dict, lang: str) -> dict:
    return m["on" if m["available"] else "off"][lang]


def render(m: dict, lang: str, cls: str) -> str:
    c = copy_for(m, lang)
    return (
        '<div class="blog-tool-cta ai-cta">'
        f'<span class="btc-label">{c["label"]}</span> '
        f'<a href="{m["target"][lang]}" class="{cls} ai-cta-link" '
        f'data-track="ai-cta">{c["button"]}</a></div>'
    )


def apply(m: dict) -> int:
    """Tegner banneren igen på alle sider. Idempotent."""
    changed = 0
    for path in pages():
        src = path.read_text(encoding="utf-8")
        lang = lang_of(path)
        out, pos = [], 0
        for hit in BANNER_RE.finditer(src):
            link = LINK_RE.search(hit.group(0))
            cls = link.group(2) if link else "btn-secondary"
            out.append(src[pos:hit.start()])
            out.append(render(m, lang, cls))
            pos = hit.end()
        out.append(src[pos:])
        new = "".join(out)
        if new != src:
            path.write_text(new, encoding="utf-8")
            changed += 1
    return changed


def judge(m: dict) -> tuple[list[str], dict]:
    problems: list[str] = []
    stats = {"banners": 0, "pages": len(pages())}
    off = m["available"] is False

    for path in pages():
        rel = path.relative_to(SITE).as_posix()
        src = path.read_text(encoding="utf-8")
        for hit in BANNER_RE.finditer(src):
            stats["banners"] += 1
            block = hit.group(0)
            lang = lang_of(path)
            c = copy_for(m, lang)

            if off:
                for bad in m["forbidden_while_off"]:
                    if bad in block:
                        problems.append(
                            f"{rel}: banneren lover «{bad}» mens assistenten er "
                            f"slukket (available=false)"
                        )
            label = LABEL_RE.search(block)
            link = LINK_RE.search(block)
            if not label or not link:
                problems.append(f"{rel}: banneren mangler label eller knap")
                continue
            if label.group(1) != c["label"]:
                problems.append(
                    f"{rel}: banner-label er ikke manifestets\n"
                    f"    side:    {label.group(1)}\n"
                    f"    manifest: {c['label']}"
                )
            if link.group(3) != c["button"]:
                problems.append(
                    f"{rel}: knappen siger «{link.group(3)}», "
                    f"manifestet siger «{c['button']}»"
                )
            if link.group(1) != m["target"][lang]:
                problems.append(
                    f"{rel}: banneren peger på {link.group(1)}, "
                    f"manifestet på {m['target'][lang]}"
                )

    # 3. Målet skal findes, og den skal sige det ærligt, når nøglen mangler.
    for lang, target in m["target"].items():
        p = SITE / (target.strip("/") + ".html")
        if not p.exists():
            problems.append(f"manifestets mål {target} findes ikke i site/")
            continue
        if not p.exists():
            continue
        body = p.read_text(encoding="utf-8")
        if 'id="aiUnavailable"' not in body:
            problems.append(
                f"{target}: mangler `aiUnavailable`-blokken, så siden kan ikke "
                f"fortælle den besøgende at assistenten er slukket"
            )
        for bad in ("Contact the site owner",):
            # Kun den synlige markup. Sætningen står to gange i kilden som
            # forklaring — en gang i en HTML-kommentar og en i en JS-kommentar —
            # og en kommentar er ikke noget en besøgende læser. Derfor fjernes
            # både kommentarer og hele script-blokke, før der dommes.
            visible = BANNER_RE.sub("", body)
            visible = re.sub(r"<!--.*?-->", "", visible, flags=re.DOTALL)
            visible = re.sub(r"<script\b.*?</script>", "", visible, flags=re.DOTALL)
            if bad in visible:
                problems.append(f"{target}: siger «{bad}» til den besøgende")
    return problems, stats


def self_test() -> int:
    """Porten skal kunne fejle. Hver mutation forventer en rød dom."""
    base = load()
    fails = []

    def expect_red(name: str, m: dict) -> None:
        problems, _ = judge(m)
        if not problems:
            fails.append(name)
        else:
            print(f"ok {name} giver {len(problems)} fund")

    def expect_green(name: str, m: dict) -> None:
        problems, _ = judge(m)
        if problems:
            fails.append(name)
            for p in problems[:3]:
                print(f"   {p}")
        else:
            print(f"ok {name}: grøn")

    expect_green("uændret manifest", base)

    # 1. Manifestet siger "tændt", mens filerne stadig har slukket-teksten.
    on = json.loads(json.dumps(base))
    on["available"] = True
    expect_red("available=true mens siderne har slukket-banneren", on)

    # 2. En side med det gamle løfte igen.
    m2 = json.loads(json.dumps(base))
    m2["_mutate"] = True
    victim = SITE / "blog" / "text-on-image-contrast-check.html"
    original = victim.read_text(encoding="utf-8")
    try:
        victim.write_text(
            original.replace(render(base, "en", "btn-secondary"),
                             render(base, "en", "btn-primary")
                             .replace("See what we publish free",
                                      "Ask the Compliance AI"),
                             1),
            encoding="utf-8",
        )
        expect_red("én side med løftet tilbage", base)
    finally:
        victim.write_text(original, encoding="utf-8")

    # 3. Banneren peger et andet sted end manifestet.
    m3 = json.loads(json.dumps(base))
    m3["target"] = {"en": "/books", "da": "/da/compliance-ai"}
    expect_red("manifestets mål afviger fra sidens", m3)

    print(f"\nselftest: {4 - len(fails)}/4")
    if fails:
        print("FEJL: mutationer, porten ikke fangede: " + ", ".join(fails))
        return 1
    print("GRØN: porten kan fejle")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()
    m = load()
    if a.apply:
        n = apply(m)
        print(f"tegnede banneren igen på {n} sider")
        return 0
    problems, stats = judge(m)
    print(f"ai-cta: {stats['banners']} banner(e) på {stats['pages']} sider i site/")
    if problems:
        for p in problems[:40]:
            print("FEJL " + p)
        if len(problems) > 40:
            print(f"… og {len(problems) - 40} mere")
        print(f"\nRØD: {len(problems)} fund")
        return 1
    state = "tændt" if m["available"] else "slukket"
    print(f"GRØN: alle bannere er tegnet af manifestet (assistenten er {state})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
