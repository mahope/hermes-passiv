#!/usr/bin/env python3
"""Layout-shift check for the built sites (spec §6/§7).

    python tools/layout_check.py                     # every dist: home + 10 random pages at 360/768/1280
    python tools/layout_check.py --only mahope.tools --n 20 --seed 7
    python tools/layout_check.py --live https://cleancopy.tools   # same check against production
    python tools/layout_check.py --shots                # also screenshots: home, subpage, palette, BugBottle panel

For every viewport width, the bounding boxes of <header class="site-header"> (left/width/top/height)
and <main> (left/width/top) must be identical on every page of a site (tolerance 1px).
Exit code 1 on any deviation. dist/ pages are served in-process like shots.py.
"""
from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent))
from shots import DIST, SHOTS, serve, slug  # noqa: E402

WIDTHS = [360, 768, 1280]
BOX_JS = """(() => {
  const r = (s) => { const e = document.querySelector(s); if (!e) return null; const b = e.getBoundingClientRect();
    return { left: Math.round(b.left), width: Math.round(b.width), top: Math.round(b.top), height: Math.round(b.height) }; };
  return { header: r('header.site-header'), main: r('main'), family: r('.family-bar'), container: r('main .container') };
})()"""


def pages_of(dist: Path, n: int, seed: int) -> list[str]:
    rnd = random.Random(seed)
    all_pages = []
    for f in dist.rglob("*.html"):
        rel = "/" + f.relative_to(dist).as_posix()
        if rel.endswith("404.html") or rel.endswith("/index.html") and rel.count("/") == 1:
            continue
        rel = rel[: -len("index.html")] if rel.endswith("/index.html") else rel[:-5]
        all_pages.append(rel)
    sample = rnd.sample(all_pages, min(n, len(all_pages)))
    return ["/"] + sample


def compare(rows: list[tuple[str, dict]], tol: int = 1) -> list[str]:
    """rows: (path, boxes). Every page compared with the first (home)."""
    out = []
    ref_path, ref = rows[0]
    for path, b in rows[1:]:
        for part, keys in (("header", ("left", "width", "top", "height")), ("main", ("left", "width", "top"))):
            if not b.get(part) or not ref.get(part):
                out.append(f"{path}: no <{part}>")
                continue
            for k in keys:
                if abs(b[part][k] - ref[part][k]) > tol:
                    out.append(f"{path}: {part}.{k}={b[part][k]} (home {ref[part][k]})")
    return out


def run_site(page, base: str, paths: list[str], widths: list[int], shots_dir: Path | None) -> tuple[list[str], dict]:
    problems = []
    stats = {}
    for w in widths:
        page.set_viewport_size({"width": w, "height": 900})
        rows = []
        for i, path in enumerate(paths):
            page.goto(base + path, wait_until="load")
            page.wait_for_timeout(150)
            page.evaluate("window.scrollTo(0, 0)")
            boxes = page.evaluate(BOX_JS)
            rows.append((path, boxes))
            if shots_dir and i < 2:
                page.screenshot(path=str(shots_dir / f"{w}-{slug(path)}.png"), full_page=False)
        problems += [f"@{w} {p}" for p in compare(rows)]
        ref = rows[0][1]
        stats[w] = dict(header=ref["header"], main=ref["main"], container=ref.get("container"),
                        containers=sorted({r[1]["container"]["width"] for r in rows if r[1].get("container")}))
        if shots_dir:
            # search palette
            page.goto(base + "/", wait_until="load")
            page.keyboard.press("Control+K")
            page.wait_for_timeout(200)
            page.keyboard.type("gdpr" if "mahope" in base else "install")
            page.wait_for_timeout(600)
            page.screenshot(path=str(shots_dir / f"{w}-palette.png"))
            page.keyboard.press("Escape")
            # BugBottle panel
            try:
                page.wait_for_selector('[data-bugbottle="ui"]', timeout=8000)
                page.evaluate("document.querySelector('[data-bugbottle=\"ui\"]').shadowRoot.querySelector('button.trigger').click()")
                page.wait_for_timeout(500)
                page.screenshot(path=str(shots_dir / f"{w}-bugbottle.png"))
            except Exception as e:  # noqa: BLE001
                problems.append(f"@{w} bugbottle panel did not mount: {str(e)[:80]}")
    return problems, stats


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only")
    ap.add_argument("--n", type=int, default=10)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--widths", nargs="*", type=int, default=WIDTHS)
    ap.add_argument("--live", nargs="*", help="base URLs, e.g. https://cleancopy.tools (pages sampled from the matching dist)")
    ap.add_argument("--shots", action="store_true")
    a = ap.parse_args()
    all_problems: list[str] = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        targets = []
        if a.live:
            for base in a.live:
                domain = base.split("//")[1].strip("/")
                targets.append((domain, base.rstrip("/"), None))
        else:
            for d in sorted(DIST.iterdir()):
                if d.is_dir() and not d.name.startswith("_") and (not a.only or d.name == a.only):
                    targets.append((d.name, f"https://{d.name}", d))
        for domain, base, dist_dir in targets:
            if a.only and domain != a.only:
                continue
            paths = pages_of(DIST / domain, a.n, a.seed)
            ctx = browser.new_context(viewport={"width": 1280, "height": 900})
            if dist_dir:
                ctx.route("**/*", serve(dist_dir, domain))
            page = ctx.new_page()
            shots_dir = None
            if a.shots:
                shots_dir = SHOTS / ("live-" + domain if a.live else domain) / "layout"
                shots_dir.mkdir(parents=True, exist_ok=True)
            problems, stats = run_site(page, base, paths, a.widths, shots_dir)
            print(f"\n== {domain} ({len(paths)} pages{' live' if a.live else ''})")
            for w, st in stats.items():
                h, m = st["header"], st["main"]
                print(f"   @{w}: header left={h['left']} width={h['width']} top={h['top']} height={h['height']} | "
                      f"main left={m['left']} width={m['width']} top={m['top']} | container widths seen: {st['containers']}")
            if problems:
                print(f"   {len(problems)} deviation(s):")
                for p in problems[:40]:
                    print("     " + p)
            else:
                print("   0 deviations")
            all_problems += [f"{domain} {p}" for p in problems]
            ctx.close()
        browser.close()
    print(f"\n{len(all_problems)} deviation(s) in total")
    return 1 if all_problems else 0


if __name__ == "__main__":
    sys.exit(main())
