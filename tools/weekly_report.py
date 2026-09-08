#!/usr/bin/env python3
"""Ugentlig faktarapport for Mahope-produkterne.

Samler tal fra gratis, offentlige kilder (Cloudflare Worker-KV, npm,
GitHub, BugBottle-indbakken, build_sites.py's link-tjek) og sender én mail
via Resend. Hver kilde fejler blødt: dør én URL, står rækken som
"kunne ikke hentes" og resten af rapporten kører videre.

    python tools/weekly_report.py --no-mail          # kør og skriv til stdout
    python tools/weekly_report.py --no-mail --no-write
    python tools/weekly_report.py                    # kør + gem JSON + mail

Miljøvariabler:
    BB_ADMIN_KEY     nøgle til https://mahope.tools/api/bugreport (valgfri)
    RESEND_API_KEY   nøgle til afsendelse (valgfri; uden den sendes ingen mail)
    LS_API_KEY       Lemon Squeezy (valgfri; mangler den, står punktet
                     som "afventer godkendelse")
    STATS_TOKEN      token til /api/stats (default: den i site/_worker.js)
    GITHUB_STEP_SUMMARY  fil der får rapporten i markdown
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPORT_DIR = ROOT / "reports" / "weekly"

SITE = "https://mahope.tools"
STATS_TOKEN = os.environ.get("STATS_TOKEN", "hp-stats-v1")

MAIL_TO = "mads@mahoje.dk"
MAIL_FROM = "Mahope rapport <bugs@mahoje.dk>"

# Produkt -> domæne (kun til overskrifter; ingen tal udledes heraf)
PRODUCTS = {
    "EUComply": "eucomplypro.com",
    "Clean Copy": "cleancopy.tools",
    "DeskUptime": "deskuptime.com",
    "Transmute": "transmute.run",
    "BugBottle": "bugbottle.dev",
    "mahope.tools": "mahope.tools",
}

NPM_PACKAGES = [
    "@mahope/clean-copy",
    "@mahope/deskuptime",
    "@mahope/transmute",
    "@mahope/eucomply-scanner",
    "@mahope/passiv-mcp",
    "@mahope/cookie-consent-banner",
    "bugbottle",
]

# repo -> produkt
GH_REPOS = {
    "mahope/eucomply-scanner": "EUComply",
    "mahope/clean-copy": "Clean Copy",
    "mahope/clean-copy-cli": "Clean Copy",
    "mahope/clean-copy-firefox": "Clean Copy",
    "mahope/clean-copy-vscode": "Clean Copy",
    "mahope/clean-copy-obsidian": "Clean Copy",
    "mahope/deskuptime": "DeskUptime",
    "mahope/transmute": "Transmute",
    "mahope/bugbottle": "BugBottle",
    "mahope/bugbottle-wordpress": "BugBottle",
    "mahope/bugbottle-action": "BugBottle",
    "mahope/hermes-passiv": "mahope.tools",
    "mahope/passiv-mcp": "mahope.tools",
    "mahope/cookie-consent-banner": "mahope.tools",
}

UPTIME_REPO = "mahope/deskuptime"
UPTIME_WORKFLOW = "self-monitor.yml"

ERRORS: list[str] = []

for _stream in (sys.stdout, sys.stderr):  # Windows-konsollen er cp1252; rapporten er UTF-8
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass


# --------------------------------------------------------------------------
# hjælpere
# --------------------------------------------------------------------------
def note_error(source: str, exc: object) -> None:
    msg = str(exc).strip() or exc.__class__.__name__
    ERRORS.append(f"{source}: {msg[:200]}")


def soft(source: str, fn, default=None):
    """Kør fn(); enhver fejl bliver til en note, aldrig et crash."""
    try:
        return fn()
    except Exception as exc:  # noqa: BLE001 — blød fejl er hele pointen
        note_error(source, exc)
        return default


def http_json(url: str, timeout: int = 30, headers: dict | None = None):
    req = urllib.request.Request(url, headers={"User-Agent": "mahope-weekly-report/1", **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def gh_json(args: list[str], timeout: int = 60):
    proc = subprocess.run(["gh", *args], capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=timeout)
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or proc.stdout).strip()[:200])
    return json.loads(proc.stdout or "null")


def iso_week_key(dt: datetime) -> str:
    y, w, _ = dt.isocalendar()
    return f"{y}-{w:02d}"


def is_day(key: str) -> bool:
    return bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", key))


# --------------------------------------------------------------------------
# 1. Trafik og brug (Cloudflare Worker-KV)
# --------------------------------------------------------------------------
def collect_health() -> dict:
    d = http_json(f"{SITE}/api/health", timeout=30)
    st = d.get("stats") or {}
    return {
        "status": d.get("status"),
        "kv": d.get("kv"),
        "visits_2d": st.get("recentVisits"),
        "downloads_2d": st.get("recentDownloads"),
        "waitlist": st.get("waitlist"),
        "scans": st.get("scans"),
    }


def collect_stats(days: int = 7) -> dict:
    url = f"{SITE}/api/stats?token={urllib.parse.quote(STATS_TOKEN)}&days={days + 1}"
    d = http_json(url, timeout=120)
    if not d.get("ok"):
        raise RuntimeError(d.get("error") or "stats svarede ok=false")
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).date().isoformat()
    visits = downloads = 0
    per_path: dict[str, int] = {}
    per_download: dict[str, int] = {}
    for day, paths in (d.get("stats") or {}).items():
        if not is_day(day) or day < cutoff:
            continue
        for path, v in paths.items():
            n = int(v.get("visits") or 0)
            if "downloads@" in path:
                downloads += n
                per_download[path.split("downloads@", 1)[1]] = per_download.get(path.split("downloads@", 1)[1], 0) + n
            else:
                visits += n
                per_path[path] = per_path.get(path, 0) + n
    top = sorted(per_path.items(), key=lambda kv: -kv[1])[:8]
    top_dl = sorted(per_download.items(), key=lambda kv: -kv[1])[:8]
    return {
        "window_days": days,
        "visits": visits,
        "downloads": downloads,
        "top_paths": [{"path": p, "visits": n} for p, n in top],
        "top_downloads": [{"file": p, "hits": n} for p, n in top_dl],
        "waitlist": d.get("waitlist"),
        "licenses_issued": d.get("licenses_issued"),
        "ai_asks": d.get("ai_asks"),
        "scans": d.get("scans"),
    }


# --------------------------------------------------------------------------
# 2. npm-downloads
# --------------------------------------------------------------------------
def collect_npm() -> dict:
    out: dict[str, dict] = {}
    for pkg in NPM_PACKAGES:
        url = f"https://api.npmjs.org/downloads/point/last-week/{urllib.parse.quote(pkg, safe='@/')}"
        try:
            d = http_json(url, timeout=25)
            if "downloads" in d:
                out[pkg] = {"downloads": int(d["downloads"]), "note": None}
            else:
                # npm svarer "not found" indtil pakken har download-data (1-2 døgn)
                out[pkg] = {"downloads": None, "note": "ingen data endnu"}
        except urllib.error.HTTPError as exc:
            out[pkg] = {"downloads": None, "note": "ingen data endnu" if exc.code == 404 else f"HTTP {exc.code}"}
        except Exception as exc:  # noqa: BLE001
            out[pkg] = {"downloads": None, "note": "kunne ikke hentes"}
            note_error(f"npm {pkg}", exc)
    return out


# --------------------------------------------------------------------------
# 3. GitHub pr. repo
# --------------------------------------------------------------------------
def collect_github() -> dict:
    out: dict[str, dict] = {}
    for repo, product in GH_REPOS.items():
        row: dict = {"product": product}
        try:
            r = gh_json(["api", f"repos/{repo}", "--jq",
                         "{stars:.stargazers_count,open_issues:.open_issues_count,pushed_at:.pushed_at}"])
            row.update(r)
        except Exception as exc:  # noqa: BLE001
            note_error(f"gh repo {repo}", exc)
            row["error"] = "kunne ikke hentes"
            out[repo] = row
            continue
        try:
            rels = gh_json(["api", f"repos/{repo}/releases?per_page=100"]) or []
            if rels:
                latest = rels[0]
                row["latest_release"] = latest.get("tag_name")
                row["latest_release_at"] = latest.get("published_at")
                row["latest_release_downloads"] = sum(int(a.get("download_count") or 0) for a in latest.get("assets") or [])
            else:
                row["latest_release"] = None
                row["latest_release_downloads"] = 0
            row["release_downloads_total"] = sum(
                int(a.get("download_count") or 0) for rel in rels for a in (rel.get("assets") or [])
            )
        except Exception as exc:  # noqa: BLE001
            note_error(f"gh releases {repo}", exc)
            row["latest_release"] = "kunne ikke hentes"
        out[repo] = row
    return out


# --------------------------------------------------------------------------
# 4. BugBottle-rapporter
# --------------------------------------------------------------------------
def collect_bugreports() -> dict:
    key = os.environ.get("BB_ADMIN_KEY", "").strip()
    if not key:
        return {"available": False, "note": "BB_ADMIN_KEY mangler"}
    url = f"{SITE}/api/bugreport?key={urllib.parse.quote(key)}"
    d = http_json(url, timeout=45)
    if not d.get("ok"):
        raise RuntimeError(d.get("error") or "bugreport svarede ok=false")
    cutoff_ms = (datetime.now(timezone.utc) - timedelta(days=7)).timestamp() * 1000
    reports = d.get("reports") or []
    recent = [r for r in reports if float(r.get("at") or 0) >= cutoff_ms]
    by_host: dict[str, int] = {}
    by_type: dict[str, int] = {}
    for r in recent:
        by_host[str(r.get("host") or "ukendt")] = by_host.get(str(r.get("host") or "ukendt"), 0) + 1
        by_type[str(r.get("type") or "other")] = by_type.get(str(r.get("type") or "other"), 0) + 1
    return {
        "available": True,
        "last_week": len(recent),
        "stored_total": len(reports),
        "by_host": by_host,
        "by_type": by_type,
    }


# --------------------------------------------------------------------------
# 5. Oppetid — DeskUptime Self-monitor
# --------------------------------------------------------------------------
def collect_uptime() -> dict:
    runs = gh_json(["run", "list", "-R", UPTIME_REPO, "-w", UPTIME_WORKFLOW, "-L", "10",
                    "--json", "conclusion,status,createdAt,url,displayTitle"]) or []
    if not runs:
        return {"note": "ingen kørsler fundet"}
    last = runs[0]
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    week = [r for r in runs if _parse_ts(r.get("createdAt")) and _parse_ts(r["createdAt"]) >= cutoff]
    return {
        "conclusion": last.get("conclusion") or last.get("status"),
        "created_at": last.get("createdAt"),
        "url": last.get("url"),
        "runs_last_week": len(week),
        "failures_last_week": sum(1 for r in week if r.get("conclusion") not in (None, "success")),
    }


def _parse_ts(s):
    if not s:
        return None
    try:
        return datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except ValueError:
        return None


# --------------------------------------------------------------------------
# 6. Døde links — build_sites.py's egen tæller (dist/build-summary.json)
# --------------------------------------------------------------------------
def collect_links() -> dict:
    summary = ROOT / "dist" / "build-summary.json"
    if not summary.exists():
        return {"available": False,
                "note": "sprunget over: dist/build-summary.json findes ikke "
                        "(build_sites.py er ikke kørt i denne kørsel)"}
    data = json.loads(summary.read_text(encoding="utf-8"))
    by_domain = {dom: int(v.get("broken") or 0) for dom, v in data.items()}
    return {
        "available": True,
        "broken_total": sum(by_domain.values()),
        "by_domain": by_domain,
        "html_total": sum(int(v.get("html") or 0) for v in data.values()),
    }


# --------------------------------------------------------------------------
# 7. Lemon Squeezy
# --------------------------------------------------------------------------
def collect_lemon() -> dict:
    key = os.environ.get("LS_API_KEY", "").strip()
    if not key:
        return {"available": False, "note": "afventer godkendelse (LS_API_KEY er ikke sat)"}
    since = (datetime.now(timezone.utc) - timedelta(days=7)).date().isoformat()
    url = "https://api.lemonsqueezy.com/v1/orders?page[size]=100&sort=-createdAt"
    d = http_json(url, timeout=30, headers={
        "Accept": "application/vnd.api+json",
        "Content-Type": "application/vnd.api+json",
        "Authorization": f"Bearer {key}",
    })
    orders = d.get("data") or []
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    recent = []
    for o in orders:
        ts = _parse_ts((o.get("attributes") or {}).get("created_at"))
        if ts and ts >= cutoff:
            recent.append(o)
    total = sum(int((o.get("attributes") or {}).get("total") or 0) for o in recent)
    return {
        "available": True,
        "since": since,
        "orders_last_week": len(recent),
        "total_cents": total,
        "currency": ((recent[0].get("attributes") or {}).get("currency") if recent else None),
        "test_mode": bool((recent[0].get("attributes") or {}).get("test_mode")) if recent else None,
    }


# --------------------------------------------------------------------------
# indsamling + sammenligning
# --------------------------------------------------------------------------
def collect_all() -> dict:
    now = datetime.now(timezone.utc)
    data = {
        "iso_week": iso_week_key(now),
        "generated_at": now.isoformat(timespec="seconds"),
        "health": soft("api/health", collect_health, {}),
        "traffic": soft("api/stats", collect_stats, {}),
        "npm": soft("npm", collect_npm, {}),
        "github": soft("github", collect_github, {}),
        "bugreports": soft("api/bugreport", collect_bugreports, {"available": False, "note": "kunne ikke hentes"}),
        "uptime": soft("deskuptime self-monitor", collect_uptime, {"note": "kunne ikke hentes"}),
        "links": soft("link-tjek", collect_links, {"available": False, "note": "kunne ikke hentes"}),
        "lemon": soft("lemon squeezy", collect_lemon, {"available": False, "note": "kunne ikke hentes"}),
    }
    data["errors"] = list(ERRORS)
    return data


def load_previous(current_key: str) -> dict | None:
    if not REPORT_DIR.exists():
        return None
    files = sorted(p for p in REPORT_DIR.glob("*.json") if p.stem < current_key)
    if not files:
        return None
    try:
        return json.loads(files[-1].read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        note_error("forrige uge", exc)
        return None


def dig(d, *path):
    cur = d
    for p in path:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(p)
    return cur


def delta(cur, prev):
    if isinstance(cur, (int, float)) and isinstance(prev, (int, float)):
        return cur - prev
    return None


def fmt_delta(d) -> str:
    if d is None:
        return "—"
    if d == 0:
        return "0"
    return f"+{d}" if d > 0 else str(d)


def fmt_num(v) -> str:
    if v is None:
        return "kunne ikke hentes"
    return str(v)


# --------------------------------------------------------------------------
# rapport
# --------------------------------------------------------------------------
def build_report(data: dict, prev: dict | None) -> tuple[str, list[str], list[dict]]:
    """Returnerer (emne, notabelt, sektioner). Sektion = {title, headers, rows, note}."""
    week = data["iso_week"].split("-")[1]
    notable: list[str] = []
    sections: list[dict] = []
    first_run = prev is None

    # --- Trafik ---
    tr, hl = data.get("traffic") or {}, data.get("health") or {}
    ptr = (prev or {}).get("traffic") or {}
    rows = []
    for label, key in [("Besøg (7 dage)", "visits"), ("Downloads (7 dage)", "downloads"),
                       ("Compliance-scans (total)", "scans"), ("Licenser udstedt (total)", "licenses_issued"),
                       ("Ventelisten (total)", "waitlist"), ("AI-spørgsmål (total)", "ai_asks")]:
        cur = tr.get(key)
        if cur is None and key in ("scans", "waitlist"):
            cur = hl.get(key)
        d = delta(cur, ptr.get(key))
        rows.append([label, fmt_num(cur), fmt_delta(d)])
        if d:
            notable.append(f"{label.split(' (')[0].lower()} {fmt_delta(d)}")
    note = None
    if not tr:
        note = "Trafiktal kunne ikke hentes fra mahope.tools/api/stats."
    sections.append({"title": "Trafik og brug (Cloudflare KV)", "headers": ["Måltal", "Nu", "Δ uge"],
                     "rows": rows, "note": note})

    if tr.get("top_paths"):
        sections.append({"title": "Mest besøgte sider (7 dage)", "headers": ["Side", "Besøg"],
                         "rows": [[p["path"], str(p["visits"])] for p in tr["top_paths"]], "note": None})
    if tr.get("top_downloads"):
        sections.append({"title": "Mest hentede filer (7 dage)", "headers": ["Fil", "Hits"],
                         "rows": [[p["file"], str(p["hits"])] for p in tr["top_downloads"]], "note": None})

    # --- npm ---
    npm, pnpm = data.get("npm") or {}, (prev or {}).get("npm") or {}
    rows = []
    for pkg in NPM_PACKAGES:
        cur = (npm.get(pkg) or {}).get("downloads")
        note_txt = (npm.get(pkg) or {}).get("note")
        d = delta(cur, (pnpm.get(pkg) or {}).get("downloads"))
        rows.append([pkg, str(cur) if cur is not None else (note_txt or "kunne ikke hentes"), fmt_delta(d)])
        if d:
            notable.append(f"npm {pkg} {fmt_delta(d)}")
    no_data = all((npm.get(p) or {}).get("downloads") is None for p in NPM_PACKAGES)
    sections.append({"title": "npm-downloads (sidste 7 dage)", "headers": ["Pakke", "Downloads", "Δ uge"],
                     "rows": rows,
                     "note": "npm's download-API har endnu ingen data for pakkerne (de er nyudgivne; "
                             "API'et er 1-2 døgn bagud)." if no_data else None})

    # --- GitHub ---
    gh, pgh = data.get("github") or {}, (prev or {}).get("github") or {}
    rows = []
    for repo, row in gh.items():
        p = pgh.get(repo) or {}
        stars, issues = row.get("stars"), row.get("open_issues")
        ds, di = delta(stars, p.get("stars")), delta(issues, p.get("open_issues"))
        rel = row.get("latest_release") or "—"
        dl = row.get("latest_release_downloads")
        ddl = delta(dl, p.get("latest_release_downloads"))
        rows.append([repo.split("/", 1)[1], row.get("product", ""), fmt_num(stars) + f" ({fmt_delta(ds)})",
                     fmt_num(issues) + f" ({fmt_delta(di)})", str(rel),
                     fmt_num(dl) + f" ({fmt_delta(ddl)})"])
        if ds:
            notable.append(f"{repo.split('/', 1)[1]} stjerner {fmt_delta(ds)}")
        if p and p.get("latest_release") and rel != p.get("latest_release"):
            notable.append(f"{repo.split('/', 1)[1]} ny release {rel}")
        if ddl:
            notable.append(f"{repo.split('/', 1)[1]} release-downloads {fmt_delta(ddl)}")
    sections.append({"title": "GitHub", "headers": ["Repo", "Produkt", "Stjerner", "Åbne issues",
                                                    "Seneste release", "Release-downloads"],
                     "rows": rows, "note": None if rows else "Ingen GitHub-data kunne hentes."})

    # --- BugBottle ---
    bb, pbb = data.get("bugreports") or {}, (prev or {}).get("bugreports") or {}
    if bb.get("available"):
        d = delta(bb.get("last_week"), pbb.get("last_week"))
        rows = [["Rapporter sidste 7 dage", fmt_num(bb.get("last_week")), fmt_delta(d)],
                ["Gemt i indbakken i alt", fmt_num(bb.get("stored_total")), ""]]
        for host, n in sorted((bb.get("by_host") or {}).items(), key=lambda kv: -kv[1]):
            rows.append([f"  fra {host}", str(n), ""])
        if bb.get("last_week"):
            notable.append(f"{bb['last_week']} BugBottle-rapporter")
        sections.append({"title": "BugBottle-rapporter", "headers": ["Måltal", "Antal", "Δ uge"],
                         "rows": rows, "note": None})
    else:
        sections.append({"title": "BugBottle-rapporter", "headers": [], "rows": [],
                         "note": f"kunne ikke hentes — {bb.get('note', 'ukendt årsag')}"})

    # --- Oppetid ---
    up = data.get("uptime") or {}
    if up.get("conclusion"):
        rows = [["Seneste Self-monitor-kørsel", str(up.get("conclusion")), str(up.get("created_at") or "")],
                ["Kørsler sidste 7 dage", str(up.get("runs_last_week", "—")), ""],
                ["Heraf fejlede", str(up.get("failures_last_week", "—")), ""]]
        if up.get("conclusion") != "success":
            notable.append(f"DeskUptime Self-monitor: {up['conclusion']}")
        if up.get("failures_last_week"):
            notable.append(f"{up['failures_last_week']} fejlede monitor-kørsler")
        sections.append({"title": "Oppetid (DeskUptime Self-monitor)", "headers": ["Måltal", "Værdi", "Tidspunkt"],
                         "rows": rows, "note": None})
    else:
        sections.append({"title": "Oppetid (DeskUptime Self-monitor)", "headers": [], "rows": [],
                         "note": f"kunne ikke hentes — {up.get('note', 'ukendt årsag')}"})

    # --- Døde links ---
    lk, plk = data.get("links") or {}, (prev or {}).get("links") or {}
    if lk.get("available"):
        d = delta(lk.get("broken_total"), plk.get("broken_total"))
        rows = [["Døde interne links i alt", fmt_num(lk.get("broken_total")), fmt_delta(d)]]
        for dom, n in sorted((lk.get("by_domain") or {}).items()):
            rows.append([f"  {dom}", str(n), ""])
        if d:
            notable.append(f"døde links {fmt_delta(d)}")
        sections.append({"title": "Døde links (build_sites.py)", "headers": ["Måltal", "Antal", "Δ uge"],
                         "rows": rows, "note": None})
    else:
        sections.append({"title": "Døde links (build_sites.py)", "headers": [], "rows": [],
                         "note": lk.get("note", "kunne ikke hentes")})

    # --- Lemon Squeezy ---
    ls = data.get("lemon") or {}
    if ls.get("available"):
        rows = [["Ordrer sidste 7 dage", fmt_num(ls.get("orders_last_week")), ""],
                ["Beløb i alt", f"{(ls.get('total_cents') or 0) / 100:.2f} {ls.get('currency') or ''}".strip(), ""]]
        if ls.get("orders_last_week"):
            notable.append(f"{ls['orders_last_week']} Lemon Squeezy-ordrer")
        sections.append({"title": "Lemon Squeezy", "headers": ["Måltal", "Værdi", ""], "rows": rows,
                         "note": "Butikken kører stadig i test mode." if ls.get("test_mode") else None})
    else:
        sections.append({"title": "Lemon Squeezy", "headers": [], "rows": [],
                         "note": ls.get("note", "afventer godkendelse")})

    # --- notabelt / emne ---
    if first_run:
        notable = ["Første kørsel — der findes ingen tidligere uge at sammenligne med. "
                   "Tallene nedenfor er udgangspunktet."] + notable
        subject = f"Ugerapport uge {week}: første kørsel, ingen sammenligning"
    else:
        seen, uniq = set(), []
        for n in notable:
            if n not in seen:
                seen.add(n)
                uniq.append(n)
        notable = uniq
        subject = (f"Ugerapport uge {week}: " + ", ".join(notable[:3])) if notable \
            else f"Ugerapport uge {week}: ingen ændringer siden sidste uge"
    if len(subject) > 140:
        subject = subject[:137] + "..."
    return subject, notable, sections


def render_markdown(data: dict, prev: dict | None, notable: list[str], sections: list[dict]) -> str:
    week = data["iso_week"]
    out = [f"# Ugerapport {week}", "",
           f"Genereret {data['generated_at']} (UTC). "
           + (f"Sammenlignet med uge {prev['iso_week']}." if prev else "Ingen tidligere uge at sammenligne med."),
           "", "## Værd at bemærke", ""]
    if notable:
        out += [f"- {n}" for n in notable]
    else:
        out.append("- Intet har ændret sig siden sidste uge.")
    out.append("")
    for s in sections:
        out += [f"## {s['title']}", ""]
        if s["rows"]:
            out.append("| " + " | ".join(s["headers"]) + " |")
            out.append("|" + "|".join(["---"] * len(s["headers"])) + "|")
            for r in s["rows"]:
                out.append("| " + " | ".join(str(c) for c in r) + " |")
            out.append("")
        if s.get("note"):
            out += [s["note"], ""]
    if data.get("errors"):
        out += ["## Kilder der ikke svarede", ""] + [f"- {e}" for e in data["errors"]] + [""]
    return "\n".join(out)


def esc(s) -> str:
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def render_html(data: dict, prev: dict | None, notable: list[str], sections: list[dict]) -> str:
    week = data["iso_week"]
    css = ("font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;"
           "font-size:14px;color:#111;line-height:1.5;max-width:760px")
    th = "text-align:left;border-bottom:2px solid #ddd;padding:6px 8px;font-weight:600"
    td = "border-bottom:1px solid #eee;padding:6px 8px;vertical-align:top"
    p = [f'<div style="{css}">', f"<h1 style='font-size:20px'>Ugerapport {esc(week)}</h1>",
         f"<p style='color:#555'>Genereret {esc(data['generated_at'])} (UTC). "
         + (f"Sammenlignet med uge {esc(prev['iso_week'])}." if prev else "Ingen tidligere uge at sammenligne med.")
         + "</p>", "<h2 style='font-size:16px'>Værd at bemærke</h2><ul>"]
    p += [f"<li>{esc(n)}</li>" for n in (notable or ["Intet har ændret sig siden sidste uge."])]
    p.append("</ul>")
    for s in sections:
        p.append(f"<h2 style='font-size:16px'>{esc(s['title'])}</h2>")
        if s["rows"]:
            p.append("<table style='border-collapse:collapse;width:100%'><thead><tr>")
            p += [f"<th style='{th}'>{esc(h)}</th>" for h in s["headers"]]
            p.append("</tr></thead><tbody>")
            for r in s["rows"]:
                p.append("<tr>" + "".join(f"<td style='{td}'>{esc(c)}</td>" for c in r) + "</tr>")
            p.append("</tbody></table>")
        if s.get("note"):
            p.append(f"<p style='color:#555'>{esc(s['note'])}</p>")
    if data.get("errors"):
        p.append("<h2 style='font-size:16px'>Kilder der ikke svarede</h2><ul>")
        p += [f"<li>{esc(e)}</li>" for e in data["errors"]]
        p.append("</ul>")
    p.append("</div>")
    return "".join(p)


# --------------------------------------------------------------------------
# afsendelse
# --------------------------------------------------------------------------
def send_mail(subject: str, html: str, text: str) -> bool:
    key = os.environ.get("RESEND_API_KEY", "").strip()
    if not key:
        note_error("resend", "RESEND_API_KEY mangler — ingen mail sendt")
        return False
    payload = json.dumps({"from": MAIL_FROM, "to": [MAIL_TO], "subject": subject,
                          "html": html, "text": text}).encode("utf-8")
    req = urllib.request.Request(
        "https://api.resend.com/emails", data=payload, method="POST",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json",
                 # Resend afviser urllib's default-UA med 403.
                 "User-Agent": "mahope-weekly-report/1"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:300]
        raise RuntimeError(f"HTTP {exc.code}: {detail}") from None
    print(f"Mail sendt, id={body.get('id')}")
    return True


# --------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--no-mail", action="store_true", help="send ingen mail")
    ap.add_argument("--no-write", action="store_true", help="gem ikke JSON-filen")
    ap.add_argument("--print", dest="do_print", action="store_true", default=True)
    args = ap.parse_args()

    data = collect_all()
    prev = load_previous(data["iso_week"])
    data["errors"] = list(ERRORS)  # opsamlet efter load_previous
    subject, notable, sections = build_report(data, prev)
    data["errors"] = list(ERRORS)
    md = render_markdown(data, prev, notable, sections)
    html = render_html(data, prev, notable, sections)

    if args.do_print:
        print(f"EMNE: {subject}\n")
        print(md)

    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as fh:
            fh.write(f"**Emne:** {subject}\n\n{md}\n")

    if not args.no_write:
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        path = REPORT_DIR / f"{data['iso_week']}.json"
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"\nSkrev {path.relative_to(ROOT)}")

    if not args.no_mail:
        try:
            send_mail(subject, html, md)
        except Exception as exc:  # noqa: BLE001 — manglende mail må ikke vælte jobbet
            note_error("resend", exc)
            print(f"ADVARSEL: mail kunne ikke sendes: {exc}", file=sys.stderr)

    if ERRORS:
        print("\nKilder der ikke svarede:", file=sys.stderr)
        for e in ERRORS:
            print(f"  - {e}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
