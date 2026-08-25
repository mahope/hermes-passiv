#!/usr/bin/env python3
"""Self-check: verify all artifacts are valid and the site is live.

Covers both ebooks (NIS2 + EAA), both covers, and site health.
Run: python3 health_check.py
"""
import os
import sys
import urllib.request
import urllib.error
import zipfile
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.abspath(__file__))
SITE_URL = "https://hermes-passiv.pages.dev"

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
        "products/compliance-bundle.html",
        "products/dpa-template.md",
        "products/eaa-statement-template.md",
        "products/nis2-contract-clauses.md",
        "products/vendor-assessment-checklist.md",
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

    # 8. Site health
    print("\n--- Site ---")
    try:
        req = urllib.request.Request(SITE_URL, headers={"User-Agent": "HermesHealthCheck/2.0"})
        resp = urllib.request.urlopen(req, timeout=15)
        body = resp.read().decode()
        status = resp.status
        ok(f"HTTP {status}") if status == 200 else fail("HTTP status", f"got {status}")
        ok("Contains 'NIS2'") if "NIS2" in body else fail("NIS2 keyword", "missing")
        ok("Contains 'EAA'") if "EAA" in body else fail("EAA keyword", "missing")
        ok("Contains 'GDPR'") if "GDPR" in body else fail("GDPR keyword", "missing")
        ok("Contains 'ComplianceDocs'") if "ComplianceDocs" in body else fail("ComplianceDocs keyword", "missing")
        ok("Schema.org present") if "@type" in body else fail("Schema.org", "missing")
        ok("Viewport meta") if "viewport" in body else fail("Viewport meta", "missing")
        ok("Cover images linked") if "cover.jpg" in body and "gdpr-cover.jpg" in body else fail("Cover images", "not in page")

        # Cookie Consent Checker live
        try:
            cc = urllib.request.urlopen(urllib.request.Request(
                SITE_URL + "/cookie-check", headers={"User-Agent": "HermesHealthCheck/2.0"}), timeout=15)
            cbody = cc.read().decode()
            ok("HTTP 200 /cookie-check") if cc.status == 200 else fail("/cookie-check status", f"got {cc.status}")
            ok("Cookie checker content") if "Consent" in cbody and "scan-proxy" in cbody else fail("Cookie checker", "content missing")
            import json as _json, re as _re
            blocks = _re.findall(r'<script type="application/ld\+json">(.*?)</script>', cbody, _re.DOTALL)
            all_ok = all(_json.loads(b).get("@context") == "https://schema.org" for b in blocks) and blocks
            ok("Cookie checker JSON-LD valid") if all_ok else fail("Cookie checker JSON-LD", f"{len(blocks)} blocks")
        except Exception as e:
            fail("/cookie-check reachable", str(e))

        # Dansk cookie-tjek live
        try:
            ccd = urllib.request.urlopen(urllib.request.Request(
                SITE_URL + "/cookie-check-da", headers={"User-Agent": "HermesHealthCheck/2.0"}), timeout=15)
            cdbody = ccd.read().decode()
            ok("HTTP 200 /cookie-check-da") if ccd.status == 200 else fail("/cookie-check-da status", f"got {ccd.status}")
            ok("Dansk cookie-tjek indhold") if "samtykke" in cdbody.lower() and "scan-proxy" in cdbody else fail("Dansk cookie-tjek", "indhold mangler")
            import json as _json2, re as _re2
            blocks2 = _re2.findall(r'<script type="application/ld\+json">(.*?)</script>', cdbody, _re2.DOTALL)
            all_ok2 = all(_json2.loads(b).get("@context") == "https://schema.org" for b in blocks2) and blocks2
            ok("Dansk cookie-tjek JSON-LD valid") if all_ok2 else fail("Dansk cookie-tjek JSON-LD", f"{len(blocks2)} blocks")
            # Blog CTA cross-links: cookie blogs must link to the free /cookie-check tool
            for slug, minlinks in (("cmp-comparison-2026", 2), ("cookie-consent-gdpr-compliance", 4)):
                try:
                    req = urllib.request.Request(f"{SITE_URL}/blog/{slug}", headers={"User-Agent": "Mozilla/5.0 (health-check)"})
                    b = urllib.request.urlopen(req, timeout=30)
                    bb = b.read().decode("utf-8", "replace")
                    n = bb.count('href="/cookie-check"')
                    ok(f"Blog {slug} → /cookie-check ({n} links)") if n >= minlinks else fail(f"Blog {slug} CTAs", f"only {n} links")
                except Exception as e:
                    fail(f"Blog {slug}", str(e))
        except Exception as e:
            fail("/cookie-check-da reachable", str(e))
        # NIS2 self-assessment live
        try:
            nis = urllib.request.urlopen(urllib.request.Request(
                SITE_URL + "/nis2-check", headers={"User-Agent": "HermesHealthCheck/2.0"}), timeout=15)
            nbody = nis.read().decode()
            ok("HTTP 200 /nis2-check") if nis.status == 200 else fail("/nis2-check status", f"got {nis.status}")
            ok("NIS2 check content") if "NIS2" in nbody and "track.js" in nbody else fail("NIS2 check", "content missing")
            import json as _json3, re as _re3
            blocks3 = _re3.findall(r'<script type="application/ld\+json">(.*?)</script>', nbody, _re3.DOTALL)
            all_ok3 = all(_json3.loads(b).get("@context") == "https://schema.org" for b in blocks3) and blocks3
            ok("NIS2 check JSON-LD valid") if all_ok3 else fail("NIS2 check JSON-LD", f"{len(blocks3)} blocks")
        except Exception as e:
            fail("/nis2-check reachable", str(e))

    except urllib.error.HTTPError as e:
        fail("HTTP status", f"HTTP {e.code}")
        for kw in ["NIS2", "EAA", "GDPR", "ComplianceDocs", "schema.org"]:
            skip(f"Site: {kw}")
    except Exception as e:
        fail("Site reachable", str(e))

    # 7. Summary
    print(f"\n=== Results: {checks['passed']} passed, {checks['failed']} failed, {checks['skipped']} skipped ===")
    return 1 if checks["failed"] > 0 else 0


if __name__ == "__main__":
    sys.exit(main())