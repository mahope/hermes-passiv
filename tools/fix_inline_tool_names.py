#!/usr/bin/env python3
"""Sæt de manglende værktøjsnavn ind i de inline CTA-hvidlister der linker til dem.

Skrevet som fil, ikke som en heredoc-kommando: 28/9 kostede tre fejl i en
shell-quoting-kæde gennem tre niveauer af Python-strenge, og ingen af dem blev
mergeret, fordi porten var død. En herredning der rører 200+ filer skal kunne
læses, køres på tværs af git-kontekst og testes mod en kopi.

Reglerne, der gør den sikker:

1. Kun navne som den side *faktisk* linker til, så diffen er præcis den
   advarsel, porten råber op om — ikke en vilkårligt bred whitelist.
2. Navnene sættes **forrest** i alternativet. Python- og JavaScript-regex er
   ordnede alternativer, så `scan|…|scan-da` matcher `/scan-da` som `scan`.
   Med `scan-da` forrest matcher `/scan` `scan` (fordi `scan-da` fejler) og
   `/scan-da` matcher `scan-da`. Det er grunden til at indsættelsen er
   prepend og ikke append.
3. Hvert navn indsættes højst én gang, og kun i den gruppe der umiddelbart
   følges af `(\\.html)?` — det er værktøjsgruppen, ikke strukturen omkring.
4. Filen er idempotent: en navngiven side, der køres igen, ændres ikke.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# De fire grupper porten advarede om, med flest sider først.
TARGETS = ("compliance-ai", "scan-da", "compliance-site-check", "compliance-guide")

# Samme læsning som `check_inline_cta_events.check`: en rodrelativ
# værktøjssti, som gruppe 1.
RE_LINK = re.compile(r"/(?:da/)?([a-z0-9-]+)(?:\.html)?(?:#[^#]*)?")
RE_HREF = re.compile(r"""<a\b[^>]*?\bhref=["']([^"']+)["']""", re.I)
# Værktøjsgruppen: kun tegnene et værktøjsnavn kan bestå af, umiddelbart
# fulgt af den valgfrie `.html`-gruppe. `(?:da\/)?` og `(\.html)?` kan derfor
# ikke forveksles med en gruppe.
RE_GROUP = re.compile(r"\(([a-z0-9|_.\-]+)\)\(\\\.html\)\?")


def linked_slugs(text: str) -> set[str]:
    """De værktøjsnavne siden faktisk linker til."""
    found: set[str] = set()
    for href in dict.fromkeys(RE_HREF.findall(text)):
        if href.startswith(("http://", "https://", "#", "mailto:", "tel:",
                            "javascript:", "//")):
            continue
        seg = RE_LINK.fullmatch(href)
        if seg:
            found.add(seg.group(1))
    return found


def patch(text: str, wanted: set[str]) -> tuple[str, int]:
    """Sæt `wanted` forrest i værktøjsgruppen, én gang. (ny tekst, antal sat)"""
    added: list[str] = []

    def repl(m: re.Match[str]) -> str:
        names = m.group(1).split("|")
        missing = [n for n in wanted if n not in names]
        if not missing:
            return m.group(0)
        # Længste navn først blandt de nye: et præfiks skal altid stå foran
        # sit eget navn, ellers vinder det kortere.
        missing.sort(key=lambda n: (-len(n), n))
        added.extend(missing)
        return "(" + "|".join(missing) + "|" + m.group(1) + r")(\.html)?"

    return RE_GROUP.sub(repl, text), len(added)


def main() -> int:
    changed = 0
    inserted = 0
    for path in sorted((ROOT / "site").rglob("*.html")):
        text = path.read_text(encoding="utf-8")
        wanted = linked_slugs(text) & set(TARGETS)
        if not wanted:
            continue
        new, n = patch(text, wanted)
        if n:
            path.write_text(new, encoding="utf-8")
            changed += 1
            inserted += n
            print(f"{path.relative_to(ROOT)}: +{n} ({', '.join(sorted(wanted))})")
    print(f"\n{inserted} navn sat ind i {changed} filer")
    return 0


if __name__ == "__main__":
    sys.exit(main())
