#!/usr/bin/env python3
"""Add an above-the-fold tool CTA to blog pages whose hero-cta has no /scan or
tool link. Idempotent: skips files that already contain a tool CTA in the hero.

Usage: python3 tools/add_hero_cta.py            # EN blog (site/blog)
       python3 tools/add_hero_cta.py da         # DA blog (site/da/blog)

The CTA is a compact strip inserted right after </header> so it sits over the
fold without pushing the H1 down. Clicks are tracked by the existing
cta-/scan|clean-copy-tool... listener in track scripts.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # repo root
SITE = ROOT / "site"

CTA = (
    '<div class="blog-tool-cta">'
    '<span class="btc-label">Check any page for GDPR &amp; cookie issues:</span> '
    '<a href="/scan" class="btn-primary">Run the Free Scanner →</a>'
    "</div>"
)

DA_CTA = (
    '<div class="blog-tool-cta">'
    '<span class="btc-label">Tjek enhver side for GDPR- og cookie-problemer:</span> '
    '<a href="/scan-da" class="btn-primary">Prøv den gratis scanner →</a>'
    "</div>"
)

CSS = """
/* blog in-content tool CTA (added by tools/add_hero_cta.py) */
.blog-tool-cta {
  max-width: 720px;
  margin: 20px auto 0;
  padding: 14px 20px;
  background: var(--color-surface-2, #f5f7fa);
  border: 1px solid var(--color-border, #e2e8f0);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 14px;
  flex-wrap: wrap;
  text-align: center;
}
.blog-tool-cta .btc-label { font-size: 0.95rem; color: var(--color-text, #1a202c); }
.blog-tool-cta .btn-primary { padding: 9px 22px; font-size: 0.92rem; }
@media (max-width: 480px) {
  .blog-tool-cta { flex-direction: column; gap: 8px; }
}
"""


def ensure_css() -> None:
    css_path = SITE / "style.css"
    text = css_path.read_text(encoding="utf-8")
    if "blog-tool-cta" in text:
        return
    css_path.write_text(text.rstrip("\n") + "\n" + CSS, encoding="utf-8")
    print("style.css: appended .blog-tool-cta rules")


def process_dir(d: Path, cta_html: str) -> None:
    changed = skipped = 0
    for f in sorted(d.glob("*.html")):
        text = f.read_text(encoding="utf-8")
        if "blog-tool-cta" in text:
            skipped += 1
            continue
        m = re.search(r"<div class=\"hero-cta\">(.*?)</div>", text, re.DOTALL)
        hero_has_tool = bool(m and re.search(r'href="/(?:da/)?(scan|clean-copy-tool)', m.group(1)))
        if hero_has_tool:
            skipped += 1
            continue
        if "</header>" not in text:
            print(f"WARN no </header>: {f.name}")
            skipped += 1
            continue
        text = text.replace("</header>", "</header>\n" + cta_html, 1)
        f.write_text(text, encoding="utf-8")
        changed += 1
    print(f"{d.name}: {changed} updated, {skipped} skipped (already has tool CTA or no header)")


if __name__ == "__main__":
    ensure_css()
    lang = sys.argv[1] if len(sys.argv) > 1 else "en"
    if lang == "da":
        process_dir(SITE / "da" / "blog", DA_CTA)
    else:
        process_dir(SITE / "blog", CTA)
