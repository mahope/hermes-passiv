#!/usr/bin/env python3
"""Self-check: verify all artifacts are valid and the site is live.

Covers both ebooks (NIS2 + EAA), both covers, and site health.
Run: python3 health_check.py
"""
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
import zipfile
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.abspath(__file__))
SITE_URL = "https://mahope.tools"

checks = {"passed": 0, "failed": 0, "skipped": 0}


def ok(label):
    checks["passed"] += 1
    print(f"  ✅ {label}")


def fail(label, detail=""):
    checks["failed"] += 1
    print(f"  ❌ {label} — {detail}")


def skip(label):
    checks["skipped"] += 1
    print(f"  ⏭️  {label}")


def check_epub(path, name):
    if not os.path.exists(path):
        fail(f"EPUB file: {name}", "Missing")
        return
    try:
        z = zipfile.ZipFile(path)
        names = z.namelist()
        ok(f"EPUB {name}: mimetype first") if names[0] == "mimetype" else fail(f"EPUB {name}: mimetype first", "mimetype not first")
        ok(f"EPUB {name}: container.xml") if "META-INF/container.xml" in names else fail(f"EPUB {name}: container.xml", "missing")
        ok(f"EPUB {name}: content.opf") if "content.opf" in names else fail(f"EPUB {name}: content.opf", "missing")
        ok(f"EPUB {name}: nav.xhtml") if "nav.xhtml" in names else fail(f"EPUB {name}: nav.xhtml", "missing")
        chapters = [n for n in names if n.startswith("ch")]
        ok(f"EPUB {name}: {len(chapters)} chapters") if len(chapters) >= 5 else fail(f"EPUB {name}: chapters", f"only {len(chapters)}")
        ET.fromstring(z.read("content.opf"))
        ok(f"EPUB {name}: XML valid")
        z.close()
    except Exception as e:
        fail(f"EPUB {name}: valid", str(e))


def check_cover(path, name, w=1600, h=2560):
    if not os.path.exists(path):
        fail(f"Cover: {name}", "Missing")
        return
    from PIL import Image
    im = Image.open(path)
    ok(f"Cover {name}: {im.size[0]}x{im.size[1]}") if (im.size[0] == w and im.size[1] == h) else fail(f"Cover {name}: dimensions", f"got {im.size[0]}x{im.size[1]}")
    ok(f"Cover {name}: RGB") if im.mode == "RGB" else fail(f"Cover {name}: mode", f"got {im.mode}")


def fetch_text(path: str, timeout: int = 15) -> tuple[int, str]:
    request = urllib.request.Request(
        SITE_URL + path,
        headers={"User-Agent": "HermesHealthCheck/3.0"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.status, response.read().decode("utf-8", "replace")


def check_json_ld(body: str, label: str) -> None:
    blocks = re.findall(r'<script\b[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', body, re.I | re.S)
    try:
        valid = bool(blocks) and all(json.loads(block).get("@context") == "https://schema.org" for block in blocks)
    except (TypeError, json.JSONDecodeError):
        valid = False
    ok(f"{label} JSON-LD valid") if valid else fail(f"{label} JSON-LD", f"{len(blocks)} blocks")


def check_live_content() -> None:
    try:
        status, body = fetch_text("/")
        ok(f"HTTP {status}") if status == 200 else fail("HTTP status", f"got {status}")
        for keyword in ("NIS2", "EAA", "GDPR", "schema.org", "viewport"):
            ok(f"Contains '{keyword}'") if keyword in body else fail(f"{keyword} keyword", "missing")
        ok("Books link") if "/books/" in body else fail("Books link", "missing")
    except Exception as error:
        fail("Site reachable", str(error))

    for path, label, required in (
        ("/cookie-check", "Cookie checker", ("Consent", "scan-proxy")),
        ("/cookie-check-da", "Dansk cookie-tjek", ("samtykke", "scan-proxy")),
        ("/nis2-check", "NIS2 check", ("NIS2", "track.js")),
    ):
        try:
            status, body = fetch_text(path)
            ok(f"HTTP 200 {path}") if status == 200 else fail(f"{path} status", f"got {status}")
            ok(f"{label} content") if all(value.casefold() in body.casefold() for value in required) else fail(f"{label} content", "missing")
            check_json_ld(body, label)
        except Exception as error:
            fail(f"{path} reachable", str(error))

    for slug, minimum in (("cmp-comparison-2026", 2), ("cookie-consent-gdpr-compliance", 4)):
        try:
            status, body = fetch_text(f"/blog/{slug}")
            count = body.count('href="/cookie-check"')
            if status == 200 and count >= minimum:
                ok(f"Blog {slug} → /cookie-check ({count} links)")
            else:
                fail(f"Blog {slug} CTAs", f"status {status}, {count} links")
        except Exception as error:
            fail(f"Blog {slug}", str(error))


def main():
    print("=== Health Check — Hermes Passiv (24 Aug 2026) ===\n")

    # 1. File integrity
    print("--- Files ---")
    expected = [
        "AGENTS.md", "DECISION.md", "BUDGET.md", "BUILD.md", "STATUS.md",
        "deploy.sh", "build-all.sh", "build_ebook.py", "build_ebook_all.py",
        "make_cover.py", "make_cover_all.py", "build_bundle.py", "health_check.py",
        "ebook/nis2-for-agencies.md", "ebook/nis2-for-agencies.html",
        "ebook/nis2-for-agencies.epub",
        "ebook/eaa-checklist.md", "ebook/eaa-checklist.html",
        "ebook/eaa-checklist.epub",
        "ebook/gdpr-for-agencies.md", "ebook/gdpr-for-agencies.epub",
        # products/ (betalt indhold) ligger i det private repo mahope/paid-products
        "site/index.html", "site/style.css",
    ]
    for f in expected:
        p = os.path.join(ROOT, f)
        ok(f"File: {f}") if os.path.exists(p) else fail(f"File: {f}", "Missing")

    # 2. EPUB validity — NIS2
    print("\n--- EPUB: NIS2 ---")
    check_epub(os.path.join(ROOT, "ebook", "nis2-for-agencies.epub"), "NIS2")

    # 3. EPUB validity — EAA
    print("\n--- EPUB: EAA ---")
    check_epub(os.path.join(ROOT, "ebook", "eaa-checklist.epub"), "EAA")

    # 4. EPUB validity — GDPR
    print("\n--- EPUB: GDPR ---")
    check_epub(os.path.join(ROOT, "ebook", "gdpr-for-agencies.epub"), "GDPR")

    # 5. Cover: NIS2
    print("\n--- Cover: NIS2 ---")
    check_cover(os.path.join(ROOT, "ebook", "cover.jpg"), "NIS2")

    # 6. Cover: EAA
    print("\n--- Cover: EAA ---")
    check_cover(os.path.join(ROOT, "ebook", "eaa-cover.jpg"), "EAA")

    # 7. Cover: GDPR
    print("\n--- Cover: GDPR ---")
    check_cover(os.path.join(ROOT, "ebook", "gdpr-cover.jpg"), "GDPR")

    print("\n--- Site ---")
    build = subprocess.run([sys.executable, os.path.join(ROOT, "build_sites.py")])
    if build.returncode:
        fail("Local site build", f"exit {build.returncode}")
    else:
        result = subprocess.run(
            [sys.executable, os.path.join(ROOT, "tools/check_live_sitemaps.py"), "--attempts", "1", "--delay", "0"]
        )
        if result.returncode == 0:
            ok("Pages live sitemap og sider")
        else:
            fail("Pages live sitemap og sider", f"exit {result.returncode}")
    check_live_content()
    try:
        request = urllib.request.Request("https://mahope.tools/api/health", headers={"User-Agent": "HermesHealthCheck/3.0"})
        with urllib.request.urlopen(request, timeout=15) as response:
            data = json.loads(response.read().decode("utf-8"))
        if response.status == 200 and data.get("status") == "healthy":
            ok("mahope.tools API health")
        else:
            fail("mahope.tools API health", f"HTTP {response.status}, status {data.get('status')!r}")
    except Exception as error:
        fail("mahope.tools API health", str(error))

    print(f"\n=== Results: {checks['passed']} passed, {checks['failed']} failed, {checks['skipped']} skipped ===")
    return 1 if checks["failed"] > 0 else 0


if __name__ == "__main__":
    sys.exit(main())