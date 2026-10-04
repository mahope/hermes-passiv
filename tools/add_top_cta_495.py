"""Sæt scanner- og AI-banneren over folden på blogartikler.

Målt 4/10: bannerne er *sekundære*. `tools/add_top_cta_495.py` (dette script),
`tools/add_ai_cta.py` og `tools/add_hero_cta.py` skrev alle tre en `btn-primary`
ind i dem, så 330 bannerknapper råbte lige så højt som sidens egen handling —
og tre generatorer skrev det igen, så en retning i `site/` alene
var holdbar til næste kørsel. `tools/check_first_action.py` dommer nu «en banner
er aldrig primær» på hver side med banner (porten tæller dem selv og skriver
antallet i hver kørsel), så klassen her skal være
`btn-secondary` eller porten går rød med det samme.

AI-bannerens tekst læses fra `tools/ai_cta.json`, fordi den skal være den
**ærlige** variant mens assistenten er slukket (`available: false`): en generator
med sit eget «practical answer in seconds» ville skrive et løfte, banneret ikke
kan holde, og `check_ai_cta_honesty.py` ville fange det bagefter.
"""
import glob
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SANDHED = json.loads((ROOT / "tools" / "ai_cta.json").read_text(encoding="utf-8"))

SCANNER = {
    "en": ('<div class="blog-tool-cta"><span class="btc-label">Check any page '
           'for GDPR &amp; cookie issues:</span>'
           ' <a href="/scan" class="btn-secondary">Run the Free Scanner →</a></div>\n'),
    "da": ('<div class="blog-tool-cta"><span class="btc-label">Tjek enhver side '
           'for GDPR- og cookie-problemer:</span>'
           ' <a href="/scan-da" class="btn-secondary">Prøv den gratis scanner →</a></div>\n'),
}


def ai_banner(lang: str) -> str:
    tekst = SANDHED["off" if not SANDHED["available"] else "on"][lang]
    return ('<div class="blog-tool-cta ai-cta">'
            f'<span class="btc-label">{tekst["label"]}</span>'
            f' <a href="{SANDHED["target"][lang]}" class="btn-secondary ai-cta-link" '
            f'data-track="ai-cta">{tekst["button"]}</a></div>\n')


def cta_for(lang: str) -> str:
    return SCANNER[lang] + ai_banner(lang)


changed = 0
for path in sorted(glob.glob("site/blog/*.html") + glob.glob("site/da/blog/*.html")):
    src = open(path, encoding="utf-8").read()
    if "blog-tool-cta" in src or "/header" not in src:
        continue
    cta = cta_for("da" if "/da/" in path else "en")
    new = src.replace("</header>\n", "</header>\n" + cta, 1)
    if new == src:
        # try without trailing newline strictness
        new = re.sub(r"</header>\s*\n", lambda m: m.group(0) + cta, src, count=1)
    if new != src:
        open(path, "w", encoding="utf-8").write(new)
        changed += 1
print("files updated:", changed)