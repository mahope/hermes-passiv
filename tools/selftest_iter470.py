#!/usr/bin/env python3
"""Iteration 470: DeskUptime Pro license flow hardened (buy-path fixed end-to-end).

Found & fixed a real crash: `deskuptime watch <url> --activate KEY` assigned to
`const pro` -> TypeError 'Assignment to constant variable' the moment a customer
activated from the watch command. The paid path was broken in the shipped CLI.
Also replaced all stale buy-URLs pointing at the old auditedwp.pages.dev domain
with hermes-passiv.pages.dev, bumped CLI to 0.2.5 and desktop to 0.2.6, tagged,
and verified the built artifacts contain the fixes.

No searches used. All verification: real GitHub Actions runs + downloaded artifacts.
"""

import json
import subprocess
import sys

REPO = "mahope/deskuptime"
FAILS = []


def run(*args, check=True, cwd=None):
    return subprocess.run(args, capture_output=True, text=True, check=check, cwd=cwd)


def ok(name):
    print(f"  OK  {name}")


def fail(name, detail=""):
    FAILS.append((name, detail))
    print(f"  FAIL {name} {detail}")


def check(cond, name, detail=""):
    if cond:
        ok(name)
    else:
        fail(name, detail)
    return cond


print("== 1. Local unit tests ==")
r = run("node", "test/test.js", cwd="deskuptime")
check("tests 11" in r.stdout and "pass 11" in r.stdout and "fail 0" in r.stdout,
      "deskuptime test.js 11/11 pass")

print("== 2. Source fixes present ==")
watch = open("deskuptime/src/watch.js").read()
check("let pro = isPro(state)" in watch, "watch.js uses `let pro` (crash fix)")
cli = open("deskuptime/src/cli.js").read()
check("auditedwp" not in cli, "cli.js has no old-domain buy URL")
for f in ("deskuptime/desktop/frontend/index.html",
          "deskuptime/.github/workflows/self-monitor.yml"):
    check("auditedwp" not in open(f).read(), f"{f.split('/')[-1]} no old domain")
check("hermes-passiv.pages.dev/deskuptime" in cli, "cli.js buy URL correct")

print("== 3. Releases live with fixes inside artifacts ==")
r = run("gh", "release", "view", "v0.2.5-cli", "-R", REPO, "--json",
        "assets", "-q", ".assets[].name", check=False)
assets_cli = r.stdout.split()
check("deskuptime-0.2.5.tar.gz" in assets_cli, "v0.2.5-cli release has tarball")

r = run("gh", "release", "download", "v0.2.5-cli", "-R", REPO, "-p",
        "deskuptime-0.2.5.tar.gz", "-O", "/tmp/du025.tgz", "--clobber", check=False)
if r.returncode == 0:
    watch_art = run("tar", "xzf", "/tmp/du025.tgz", "-O", "src/watch.js").stdout
    cli_art = run("tar", "xzf", "/tmp/du025.tgz", "-O", "src/cli.js").stdout
    check("let pro" in watch_art, "shipped tarball contains let-pro fix")
    check("hermes-passiv.pages.dev" in cli_art and "auditedwp" not in cli_art,
          "shipped tarball has corrected buy URL")
else:
    fail("download tarball", r.stderr[:100])

r = run("gh", "release", "view", "v0.2.6-desktop", "-R", REPO, "--json",
        "assets", "-q", ".assets[].name", check=False)
assets_desktop = sorted(r.stdout.split())
for want in ("DeskUptime_0.2.6_x64-setup.exe", "DeskUptime_0.2.6_x64_en-US.msi"):
    check(want in assets_desktop, f"desktop release has {want}")

print("== 4. Floating tags point at fixed code ==")


def tag_sha(tag):
    return run("git", "rev-parse", tag, cwd="deskuptime").stdout.strip()


head = run("git", "rev-parse", "HEAD", cwd="deskuptime").stdout.strip()
check(tag_sha("v1") == head, "deskuptime repo v1 = HEAD")
check(tag_sha("v0.2.6-desktop") == head, "v0.2.6-desktop = HEAD")

print("== 5. CI runs green ==")
r = run("gh", "api", f"repos/{REPO}/actions/runs?per_page=10", "--jq",
        '.workflow_runs[] | select(.conclusion!="success") | .id', check=False)
check(r.stdout.strip() == "", "no failed workflow runs in last 10")

print()
if FAILS:
    print(f"{len(FAILS)} FAILURES:")
    for n, d in FAILS:
        print(f"  - {n} {d}")
    sys.exit(1)
print("All checks passed.")
