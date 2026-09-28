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

# Alle 26 stier porten har advaret om, med flest sider først. Listen er den
# portens egen advarselsliste, ikke en håndplukket udvalg: hver gruppe er den
# maskinelle rettelse fra den 28/9, og de er alle samme fejlform.
TARGETS = (
    "word-counter",
    "json-formatter",
    "case-converter",
    "base64-encoder-decoder",
    "url-encoder-decoder",
    "hash-generator",
    "contrast-checker-da",
    "nis2-check-da",
    "dpa-generator-da",
    "palette-generator-da",
    "privacy-notice-generator-da",
    "ropa-generator-da",
    "cookie-check-da",
    "text-on-image-checker-da",
    "color-blindness-simulator-da",
    "ropa-template",
    "scan",
    "compliance-ai",
    "scan-da",
    "compliance-site-check",
    "compliance-guide",
    "tilgaengelighedserklaering-generator-da",
    "nis2-gap-assessment-da",
    "nis2-incident-generator-da",
    "security-headers-check",
    "guides",
    # Målt 28/9: porten havde ingen advarsel om den, fordi ingen tracker målte
    # den. Først da den kom i `track.js`, blev den synlig — på de to sider med
    # egen tracker, der linker til den. Se kommentaren i `track.js`.
    "free-downloads",
    # 33 ruter der lå i samme blindplet, målt af `tools/audit_unmeasured_routes.py`:
    # 2366 links i `dist/` pegede på ruter ingen tracker i familien målte. Listen er
    # auditets egen ubefalede ruter minus `/privacy` og `/terms`, som bevidst holdes
    # ude — sidevisnings-beaconen tæller dem allerede. Da de kom i `track.js`, blev
    # præcis de her navn synlige for porten, som den advarslede om, og sådan fik
    # denne maskine sin advarselsliste i stedet for en håndplukket udvalg.
    "books",
    "blog",
    "downloads",
    "wordpress-plugin",
    "activate",
    "license-lookup",
    "mcp",
    "tools",
    "url-inspector",
    "accessibility-statement-generator",
    "privacy-notice-generator",
    "privacy-policy-template",
    "cookie-check",
    "nis2-check",
    "nis2-gap-assessment",
    "nis2-incident-generator",
    "dpa-generator",
    "contrast-checker",
    "color-blindness-simulator",
    "palette-generator",
    "ropa-generator",
    "markdown-table-generator",
    "uuid-generator",
    "text-on-image-checker",
    "bulk-url-checker",
    "security-headers-checker",
    "clean-copy-cli-ref",
    "clean-copy-api",
    "clean-copy-bookmarklet",
    "clean-copy-brew",
    "copy-clean-guide",
    "bugbottle-demo",
    "cookie-consent-banner-demo",
)

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
