#!/usr/bin/env python3
"""Version sweep for all Clean Copy distribution surfaces.

Compares the canonical version of each product against every surface:
  - local manifest / package.json / Formula
  - GitHub repo main branch (via API, no auth needed for public repos)
  - latest GitHub release tag
  - site download links vs. files actually present in site/downloads/

Exit code 1 if any mismatch is found, so passiv-loop can act on it.
Usage: python3 version_sweep.py [--json]
"""
import json, os, re, shutil, subprocess, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(ROOT, "site")
DOWNLOADS = os.path.join(SITE, "downloads")

PRODUCTS = {
    "clean-copy-chrome": {
        "local": os.path.join(ROOT, "extension-clean-copy", "manifest.json"),
        "kind": "manifest",
        "repo": "mahope/clean-copy",
    },
    "clean-copy-firefox": {
        "local": os.path.join(ROOT, "extension-clean-copy-firefox", "manifest.json"),
        "kind": "manifest",
        "repo": None,
        # Firefox builds live in their own repo (mahope/clean-copy-firefox),
        # released as plain vX.Y.Z tags there.
        "release_repo": "mahope/clean-copy-firefox",
        "release_suffix": "",
    },
    "clean-copy-cli": {
        "local": os.path.join(ROOT, "clean-copy-cli", "package.json"),
        "kind": "package",
        "repo": "mahope/clean-copy-cli",
    },
    "clean-copy-obsidian": {
        "local": os.path.join(ROOT, "obsidian-plugin", "manifest.json"),
        "kind": "manifest",
        "repo": None,  # distributed as PR to obsidianmd repo, no own repo check
    },
}

# zip name prefix per product as linked from the site
ZIP_PREFIX = {
    "clean-copy-chrome": "clean-copy-v",
    "clean-copy-firefox": "clean-copy-firefox-v",
    "clean-copy-obsidian": "clean-copy-obsidian-v",
}

SITE_PAGES = ["clean-copy.html", "downloads.html", "index.html"]


def local_version(entry):
    try:
        with open(entry["local"]) as f:
            data = json.load(f)
        return data.get("version")
    except Exception as e:
        return f"ERROR reading {entry['local']}: {e}"


def gh_api(url):
    # Prefer the authenticated gh CLI when available — anonymous GitHub API
    # calls rate-limit fast and produce false "NO RELEASE" mismatches.
    if shutil.which("gh"):
        try:
            out = subprocess.run(
                ["gh", "api", url.replace("https://api.github.com/", "")],
                capture_output=True, text=True, timeout=30,
            ).stdout
            return json.loads(out)
        except Exception:
            pass
    try:
        out = subprocess.run(
            ["curl", "-sL", "--max-time", "20", url],
            capture_output=True, text=True, timeout=30,
        ).stdout
        return json.loads(out)
    except Exception as e:
        return {"_error": str(e)}


def github_main_version(repo):
    if not repo:
        return None  # not applicable
    # Prefer gh contents API with raw Accept header — raw.githubusercontent
    # can serve a stale cached version for minutes after a push.
    if shutil.which("gh"):
        try:
            out = subprocess.run(
                ["gh", "api", f"repos/{repo}/contents/manifest.json",
                 "-H", "Accept: application/vnd.github.raw"],
                capture_output=True, text=True, timeout=30,
            ).stdout
            data = json.loads(out)
            if isinstance(data, dict) and data.get("version"):
                return data["version"]
        except Exception:
            pass
        # CLI repos have no manifest.json — the contents API 404s above, so
        # retry with package.json through the same non-caching path.
        try:
            out = subprocess.run(
                ["gh", "api", f"repos/{repo}/contents/package.json",
                 "-H", "Accept: application/vnd.github.raw"],
                capture_output=True, text=True, timeout=30,
            ).stdout
            data = json.loads(out)
            if isinstance(data, dict) and data.get("version"):
                return data["version"]
        except Exception:
            pass
    data = gh_api(f"https://raw.githubusercontent.com/{repo}/main/manifest.json")
    if "_error" in data or (isinstance(data, dict) and data.get("version") is None):
        # CLI repos use package.json
        data = gh_api(f"https://raw.githubusercontent.com/{repo}/main/package.json")
    return data.get("version", f"NOT FOUND ({data.get('_error', 'no version key')})")


def github_latest_release(repo, suffix=""):
    if not repo:
        return None
    data = gh_api(f"https://api.github.com/repos/{repo}/releases/latest")
    if "tag_name" in data:
        return data["tag_name"].lstrip("v")
    return f"NO RELEASE ({data.get('message', 'unknown')})"


def github_tag_exists(repo, version, suffix=""):
    """True if tag v{version}{suffix} exists. Used for platform-suffixed
    releases where /releases/latest may point at a different product's
    release on the shared repo."""
    data = gh_api(f"https://api.github.com/repos/{repo}/git/ref/tags/v{version}{suffix}")
    return isinstance(data, dict) and data.get("ref") is not None


def site_zip_state(product, version):
    """Check zip exists locally AND is referenced from a site page."""
    prefix = ZIP_PREFIX.get(product)
    if not prefix:
        return None
    fname = f"{prefix}{version}.zip"
    path = os.path.join(DOWNLOADS, fname)
    exists_local = os.path.exists(path)
    refs = []
    for page in SITE_PAGES:
        p = os.path.join(SITE, page)
        if os.path.exists(p):
            with open(p) as f:
                if fname in f.read():
                    refs.append(page)
    return {"zip": fname, "exists_in_downloads": exists_local, "referenced_from": refs}


# Homebrew formula: version + tarball URL must track the CLI release
HOMEBREW_FORMULA = os.path.join(ROOT, "homebrew-clean-copy", "Formula", "clean-copy.rb")

def homebrew_state(cli_version):
    try:
        with open(HOMEBREW_FORMULA) as f:
            text = f.read()
    except Exception as e:
        return f"ERROR reading {HOMEBREW_FORMULA}: {e}"
    vm = re.search(r'version\s+"([^"]+)"', text)
    um = re.search(r'url\s+"[^"]*/v([^/]+)/[^"]*"', text)
    ver = vm.group(1) if vm else None
    url_ver = um.group(1) if um else None
    problems = []
    if ver != cli_version:
        problems.append(f"formula version {ver} != CLI {cli_version}")
    if url_ver != cli_version:
        problems.append(f"formula url points at v{url_ver}, expected v{cli_version}")
    return {"version": ver, "url_version": url_ver, "problems": problems}


def stale_zips():
    """Old-version zips still sitting in downloads/ (confusing duplicates)."""
    current = set()
    for prod, entry in PRODUCTS.items():
        v = local_version(entry)
        pre = ZIP_PREFIX.get(prod)
        if v and pre:
            current.add(f"{pre}{v}.zip")
    stale = []
    for f in sorted(os.listdir(DOWNLOADS)):
        if f.endswith(".zip") and re.match(r"clean-copy.*-v\d+\.\d+\.\d+\.zip$", f) and f not in current:
            stale.append(f)
    return stale


def main():
    problems = []
    report = {}
    for prod, entry in PRODUCTS.items():
        lv = local_version(entry)
        gv = github_main_version(entry["repo"])
        rel_repo = entry.get("release_repo", entry["repo"])
        rel = github_latest_release(rel_repo, entry.get("release_suffix", ""))
        zs = site_zip_state(prod, lv)
        if isinstance(rel, str) and not rel.startswith("NO RELEASE"):
            sfx = entry.get("release_suffix", "")
            # a platform-suffixed tag (e.g. 1.3.0-fx) is another product's release
            if sfx:
                ok = rel == lv + sfx
            else:
                ok = rel == lv or re.search(r"-\w+$", rel)
            if not ok and not github_tag_exists(rel_repo, lv, entry.get("release_suffix", "")):
                problems.append(f"{prod}: local {lv} != latest release tag v{rel}")
        row = {"local": lv, "github_main": gv, "latest_release": rel, "site": zs}
        report[prod] = row
        if gv is not None and lv != gv:
            problems.append(f"{prod}: local {lv} != GitHub main {gv}")
        if zs:
            if not zs["exists_in_downloads"]:
                problems.append(f"{prod}: {zs['zip']} missing from site/downloads/")
            if not zs["referenced_from"]:
                problems.append(f"{prod}: {zs['zip']} not referenced by any site page")
    st = stale_zips()
    report["_stale_zips_in_downloads"] = st
    cli_v = local_version(PRODUCTS["clean-copy-cli"])
    if isinstance(cli_v, str) and not cli_v.startswith("ERROR"):
        hb = homebrew_state(cli_v)
        report["homebrew-formula"] = hb
        if isinstance(hb, dict):
            for p in hb.get("problems", []):
                problems.append(f"homebrew: {p}")
        else:
            problems.append(f"homebrew: {hb}")

    print(json.dumps(report, indent=2))
    if problems:
        print("\nPROBLEMS:")
        for p in problems:
            print(" -", p)
        sys.exit(1)
    print("\nALL SURFACES IN SYNC")


if __name__ == "__main__":
    main()
