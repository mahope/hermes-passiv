#!/usr/bin/env python3
from __future__ import annotations

import argparse
import concurrent.futures
import json
import re
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from http.client import HTTPMessage
from pathlib import Path
from urllib.parse import quote, urlsplit, urlunsplit

from check_sitemaps import DIST, SITES, check_domain, parse_head, parse_sitemap

USER_AGENT = "Mozilla/5.0 (compatible; HermesSitemapCheck/1.0)"
PAGES_DOMAINS = tuple(domain for domain in SITES if domain != "bugbottle.dev")


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


OPENER = urllib.request.build_opener(NoRedirect)


def encoded_url(url: str) -> str:
    parts = urlsplit(url)
    return urlunsplit((
        parts.scheme,
        parts.netloc,
        quote(parts.path, safe="/%:@!$&'()*+,;=-._~"),
        quote(parts.query, safe="=&%:@!$'()*+,;/?-._~"),
        "",
    ))


def parse_sitemap_bytes(data: bytes) -> tuple[list[str], list[str]]:
    try:
        root = ET.fromstring(data)
    except ET.ParseError as error:
        return [], [f"invalid source sitemap.xml: {error}"]
    namespace = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
    urls = []
    for entry in root.findall(f"{namespace}url"):
        location = entry.find(f"{namespace}loc")
        if location is None or not (location.text or "").strip():
            return urls, ["source sitemap entry without loc"]
        urls.append((location.text or "").strip())
    if not urls:
        return urls, ["source sitemap has no URLs"]
    return urls, []


def fetch(url: str, timeout: int = 30) -> tuple[int | None, bytes, HTTPMessage | None, str | None]:
    request = urllib.request.Request(encoded_url(url), headers={"User-Agent": USER_AGENT})
    try:
        with OPENER.open(request, timeout=timeout) as response:
            return response.status, response.read(), response.headers, None
    except urllib.error.HTTPError as error:
        return error.code, error.read(), error.headers, None
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        return None, b"", None, str(error)


def has_noindex_header(headers: HTTPMessage) -> bool:
    return any(
        directive in {"noindex", "none"}
        for value in headers.get_all("X-Robots-Tag", [])
        for directive in re.split(r"[\s,]+", value.casefold())
    )


def expected_artifacts(domain: str) -> dict[str, bytes]:
    dist = DIST / domain
    return {
        "robots.txt": (dist / "robots.txt").read_bytes(),
        "sitemap.xml": (dist / "sitemap.xml").read_bytes(),
        "build-info.json": (dist / "build-info.json").read_bytes(),
    }


def wait_for_artifacts(domain: str, expected: dict[str, bytes], attempts: int, delay: int) -> list[str]:
    last_problems: list[str] = []
    for attempt in range(1, attempts + 1):
        problems = []
        for name, data in expected.items():
            status, body, _headers, error = fetch(f"https://{domain}/{name}")
            if error:
                problems.append(f"{name}: {error}")
            elif status != 200:
                problems.append(f"{name}: HTTP {status}")
            elif body != data:
                problems.append(f"{name}: live content differs from local build")
        if not problems:
            return []
        last_problems = problems
        if attempt < attempts:
            time.sleep(delay)
    return [f"artifact mismatch after {attempts} attempt(s): {problem}" for problem in last_problems]


def check_page(url: str, require_jsonld: bool = True) -> list[str]:
    status, body, headers, error = fetch(url)
    if error:
        return [f"{url}: {error}"]
    if status != 200:
        return [f"{url}: HTTP {status}"]
    text = body.decode("utf-8", errors="ignore")
    parser = parse_head(text)
    problems = []
    if not re.search(r"<title\b[^>]*>.*?</title>", text, re.I | re.S):
        problems.append(f"{url}: missing title")
    if require_jsonld:
        blocks = re.findall(r'<script\b[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', text, re.I | re.S)
        if not blocks:
            problems.append(f"{url}: missing JSON-LD")
        for block in blocks:
            try:
                json.loads(block)
            except json.JSONDecodeError as error:
                problems.append(f"{url}: invalid JSON-LD: {error}")
    if len(parser.canonicals) != 1:
        problems.append(f"{url}: canonical count {len(parser.canonicals)}")
    elif parser.canonicals[0] != url:
        problems.append(f"{url}: canonical {parser.canonicals[0]!r}")
    if parser.noindex or (headers and has_noindex_header(headers)):
        problems.append(f"{url}: noindex page is in sitemap")
    return problems


def check_retired_downloads_live(domain: str) -> list[str]:
    """En tilbagetrukket arkivsti må ikke svare 200 i produktion.

    Opgave 28: `clean-copy-firefox-v1.5.3.zip` blev slettet i git, fordi README'en
    lovede "nothing leaves your browser" mens nøglen bliver sendt til
    mahope.tools. Rettelsen holdt i kilden, men Cloudflare Pages fjerner ikke
    slettede assets — filen blev ved med at svare 200, med den gamle tekst. Det er
    den eneste kontrol, der kan se det: alt i `tools/` læser repoet og dist, og
    begge var rene. Derfor ligger den her, i det job der kører efter hver deploy.
    """
    problems: list[str] = []
    # `DIST` er `<repo>/dist`, så kilden er `DIST.parent` — ikke `DIST.parent.parent`,
    # som var min første og kun fejl: kørsel `36207913926` døde i alle tre deploys
    # med "cannot read tools/retired_downloads.json", fordi stien pegede ud af repoet.
    catalog_path = Path(__file__).resolve().parent.parent / "tools" / "retired_downloads.json"
    try:
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return [f"cannot read {catalog_path.name}: {error}"]
    for retired, meta in (catalog.get(domain) or {}).items():
        status, _, headers, error = fetch(f"https://{domain}{retired}")
        if error:
            problems.append(f"https://{domain}{retired}: {error}")
            continue
        location = headers.get("Location") if headers else None
        if status == 200:
            problems.append(
                f"https://{domain}{retired}: HTTP 200 — den tilbagetrukne fil er stadig hentbar"
                + (f" (stænder: {meta.get('reason', 'ingen begrundelse')[:60]}…)" if isinstance(meta, dict) else "")
            )
        elif status in (301, 302, 307, 308):
            if not location:
                problems.append(f"https://{domain}{retired}: HTTP {status} without a Location header")
            elif isinstance(meta, dict) and location.rstrip("/").endswith(str(meta.get("replaced_by", "\0")).rstrip("/")):
                pass
            else:
                problems.append(f"https://{domain}{retired}: HTTP {status} to {location!r}, expected {meta.get('replaced_by')!r}")
        elif status != 404:
            problems.append(f"https://{domain}{retired}: HTTP {status} (expected a 301 to the current file, or 404)")
    return problems


def check_live_domain(domain: str, commit: str | None, attempts: int, delay: int, workers: int) -> list[str]:
    local_problems = check_domain(domain, expected_commit=commit)
    if local_problems:
        return [f"local build invalid: {problem}" for problem in local_problems]
    expected = expected_artifacts(domain)
    artifact_problems = wait_for_artifacts(domain, expected, attempts, delay)
    if artifact_problems:
        return artifact_problems
    urls, sitemap_problems = parse_sitemap(DIST / domain / "sitemap.xml")
    if sitemap_problems:
        return sitemap_problems
    problems = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        for result in executor.map(check_page, urls):
            problems.extend(result)
    problems.extend(check_retired_downloads_live(domain))
    return problems


def source_commit(source: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(source), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    commit = result.stdout.strip().lower()
    return commit if re.fullmatch(r"[0-9a-f]{40,64}", commit) else None


def rebuilt_source_artifacts(source: Path, commit: str) -> tuple[dict[str, bytes] | None, list[str]]:
    with tempfile.TemporaryDirectory(prefix="hermes-bugbottle-source-") as temporary:
        root = Path(temporary).resolve() / "checkout"
        clone = subprocess.run(
            ["git", "clone", "--no-hardlinks", "--quiet", str(source), str(root)],
            capture_output=True,
            text=True,
            timeout=300,
        )
        if clone.returncode:
            return None, [f"source clone failed: {clone.stderr[-2000:]}"]
        shallow = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--is-shallow-repository"],
            capture_output=True,
            text=True,
            check=True,
        )
        if shallow.stdout.strip() == "true":
            return None, ["source checkout must contain full Git history for deterministic lastmod values"]
        checkout = subprocess.run(
            ["git", "-C", str(root), "checkout", "--detach", commit],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if checkout.returncode:
            return None, [f"source checkout failed: {checkout.stderr[-2000:]}"]
        install = subprocess.run(
            ["npm", "ci", "--ignore-scripts"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=300,
        )
        if install.returncode:
            return None, [f"source npm ci failed: {install.stderr[-2000:]}"]
        docs = subprocess.run(
            ["npm", "run", "build:docs"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=300,
        )
        if docs.returncode:
            return None, [f"source build-docs failed: {docs.stderr[-2000:]}"]
        artifacts = {}
        for name in ("robots.txt", "sitemap.xml"):
            path = root / "site" / name
            if not path.is_file():
                return None, [f"source build did not generate site/{name}"]
            artifacts[name] = path.read_bytes()
        return artifacts, []


def check_bugbottle_source(source: Path, expected_commit: str | None, attempts: int, delay: int, workers: int) -> list[str]:
    if not source.is_dir():
        return [f"authoritative BugBottle source is missing: {source}"]
    problems = []
    commit = source_commit(source)
    if commit is None:
        problems.append("authoritative BugBottle source has no readable Git commit")
    elif expected_commit and commit != expected_commit.lower():
        problems.append(f"authoritative BugBottle source commit={commit!r}, expected {expected_commit.lower()!r}")
    if problems:
        return problems
    artifacts, build_problems = rebuilt_source_artifacts(source, commit)
    if build_problems or artifacts is None:
        return build_problems or ["source build produced no artifacts"]
    artifact_problems = wait_for_artifacts("bugbottle.dev", artifacts, attempts, delay)
    if artifact_problems:
        return artifact_problems
    urls, sitemap_problems = parse_sitemap_bytes(artifacts["sitemap.xml"])
    if sitemap_problems:
        return sitemap_problems
    if len(urls) != len(set(urls)):
        problems.append("authoritative BugBottle sitemap contains duplicate URLs")
    for url in urls:
        if not re.fullmatch(r"https://bugbottle\.dev(?:/[^?#]*)?", url):
            problems.append(f"bugbottle.dev: invalid source sitemap URL {url!r}")
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        for result in executor.map(lambda url: check_page(url, require_jsonld=False), urls):
            problems.extend(result)
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", choices=sorted(SITES))
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--commit")
    parser.add_argument("--bugbottle-source", type=Path)
    parser.add_argument("--bugbottle-source-commit")
    parser.add_argument("--attempts", type=int, default=6)
    parser.add_argument("--delay", type=int, default=10)
    parser.add_argument("--workers", type=int, default=12)
    args = parser.parse_args(argv)
    if args.only and args.all:
        parser.error("--only and --all cannot be combined")
    if args.commit and not re.fullmatch(r"[0-9a-f]{40,64}", args.commit.lower()):
        parser.error("--commit must be a full Git SHA")
    if args.bugbottle_source_commit and not re.fullmatch(r"[0-9a-f]{40,64}", args.bugbottle_source_commit.lower()):
        parser.error("--bugbottle-source-commit must be a full Git SHA")
    if args.attempts < 1 or args.delay < 0 or args.workers < 1:
        parser.error("attempts and workers must be positive; delay cannot be negative")
    domains = [args.only] if args.only else list(SITES) if args.all else list(PAGES_DOMAINS)
    failed = False
    for domain in domains:
        try:
            if domain == "bugbottle.dev":
                if not args.bugbottle_source:
                    problems = ["authoritative BugBottle source not supplied; use --bugbottle-source with a full Git checkout"]
                else:
                    problems = check_bugbottle_source(args.bugbottle_source, args.bugbottle_source_commit, args.attempts, args.delay, args.workers)
            else:
                problems = check_live_domain(domain, args.commit, args.attempts, args.delay, args.workers)
        except (OSError, ValueError, json.JSONDecodeError) as error:
            problems = [str(error)]
        if problems:
            failed = True
            print(f"{domain}: {len(problems)} problem(s)")
            for problem in problems[:100]:
                print(f"- {problem}")
            if len(problems) > 100:
                print(f"- ... and {len(problems) - 100} more")
        else:
            print(f"{domain}: live sitemap OK")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
