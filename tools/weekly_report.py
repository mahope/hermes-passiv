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
    RESEND_API_KEY   nøgle til afsendelse og server-side stats-autentisering
    GITHUB_STEP_SUMMARY  fil der får rapporten i markdown
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPORT_DIR = ROOT / "reports" / "weekly"
OFFER_CATALOG = ROOT / "tools/stripe_catalog.json"

SITE = "https://mahope.tools"
STATS_AUTH_CONTEXT = "stats-auth-v1:"

MAIL_TO = "mads@mahoje.dk"
MAIL_FROM = "Mahope rapport <bugs@mahoje.dk>"

TRAFFIC_DOMAINS = ("cleancopy.tools", "deskuptime.com", "bugbottle.dev", "mahope.tools")

# Konverteringsrangeringen gælder de seneste syv *fulde* dage. Dagens time er
# ikke et fuldt døgn og kan ikke sammenlignes med syv hele, så den tælles
# aldrig med. Tærsklerne er kontraktens: uden dem må rapporten ikke påstå,
# at nogen side er mest besøgt.
RANKING_DAYS = 7
RANKING_MIN_TOTAL_PAGEVIEWS = 30
RANKING_MIN_PAGEVIEWS_PER_DOMAIN = 5
# API'et leverer dage inklusive i dag, så der hentes én dag mere end
# rankingvinduet kræver.
RANKING_FETCH_DAYS = RANKING_DAYS + 1

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


def stats_bearer_token() -> str:
    secret = os.environ.get("RESEND_API_KEY", "").strip()
    if not secret:
        return ""
    return hashlib.sha256((STATS_AUTH_CONTEXT + secret).encode("utf-8")).hexdigest()


def known_counter(value: object) -> int | None:
    return value if type(value) is int and value >= 0 else None


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
    traffic_status = d.get("traffic_status")
    traffic_known = traffic_status in ("ok", "partial")
    return {
        "status": d.get("status"),
        "kv": d.get("kv"),
        "traffic_status": traffic_status,
        "visits_2d": st.get("recentVisits") if traffic_known else None,
        "downloads_2d": st.get("recentDownloads") if traffic_known else None,
        "waitlist": known_counter(st.get("waitlist")),
        "scans": known_counter(st.get("scans")),
    }


def unknown_stats() -> dict:
    unknown_domains = {
        domain: {"status": "unknown", "visits": None, "top_paths": []}
        for domain in TRAFFIC_DOMAINS
    }
    return {
        "available": False,
        "status": "unknown",
        "unique_status": "unknown",
        "window_days": 7,
        "visits": None,
        "domains": unknown_domains,
        "downloads": None,
        "download_domains": {
            domain: {"status": "unknown", "visits": None, "top_downloads": []}
            for domain in TRAFFIC_DOMAINS
        },
        "top_paths": [],
        "top_downloads": [],
        "sales": {"available": False, "status": "unknown"},
        "waitlist": None,
        "licenses_issued": None,
        "ai_asks": None,
        "scans": None,
        "ranking": _unknown_ranking("trafikken kunne ikke hentes"),
    }


def _window_by_domain(
    raw_by_domain: dict,
    days: int,
    *,
    pageviews: bool,
    domain_status: dict | None = None,
    start: str | None = None,
    end: str | None = None,
) -> tuple[dict, int | None, list, bool, dict]:
    if not isinstance(raw_by_domain, dict):
        raise RuntimeError("stats_by_domain mangler")
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days - 1)).date().isoformat()
    domains = {}
    total = 0
    aggregate = {}
    per_domain_paths: dict[str, dict[str, int]] = {}
    complete = True
    top_key = "top_paths" if pageviews else "top_downloads"
    item_key = "path" if pageviews else "file"
    for domain in TRAFFIC_DOMAINS:
        raw_domain = raw_by_domain.get(domain)
        state = (domain_status or {}).get(domain)
        if state != "ok":
            complete = False
            domains[domain] = {
                "status": "unknown",
                "visits": None,
                top_key: [],
            }
            continue
        if not isinstance(raw_domain, dict):
            raise RuntimeError(f"stats mangler for {domain}")
        per_name = {}
        for day, entries in raw_domain.items():
            if not is_day(day):
                raise RuntimeError(f"ugyldig dato i stats: {day}")
            if start and end:
                if not (start <= day <= end):
                    continue
            elif day < cutoff:
                continue
            if not isinstance(entries, dict):
                raise RuntimeError(f"ugyldige stats for {domain}/{day}")
            for name, info in entries.items():
                if not isinstance(name, str) or (pageviews and not name.startswith("/")):
                    raise RuntimeError(f"ugyldig sti i stats: {name}")
                if not isinstance(info, dict) or type(info.get("visits")) is not int or info["visits"] < 0:
                    raise RuntimeError(f"ugyldigt besøgstal for {domain}/{day}/{name}")
                count = info["visits"]
                unique = info.get("uniques")
                if unique is not None and (type(unique) is not int or unique < 0 or unique > count):
                    raise RuntimeError(f"ugyldigt uniktal for {domain}/{day}/{name}")
                per_name[name] = per_name.get(name, 0) + count
                aggregate[name] = aggregate.get(name, 0) + count
                total += count
        if pageviews and not per_name:
            complete = False
            domains[domain] = {
                "status": "unknown",
                "visits": None,
                top_key: [],
            }
            continue
        top = sorted(per_name.items(), key=lambda item: (-item[1], item[0]))[:8]
        domains[domain] = {
            "status": "ok",
            "visits": sum(per_name.values()),
            top_key: [{item_key: name, "visits": count} for name, count in top],
        }
        if pageviews:
            per_domain_paths[domain] = per_name
    top_aggregate = sorted(aggregate.items(), key=lambda item: (-item[1], item[0]))[:8]
    return domains, total if complete else None, top_aggregate, complete, per_domain_paths


def _collect_sales(data: dict) -> dict:
    if data.get("sales_status") != "ok":
        return {"available": False, "status": "unknown"}
    source = data.get("sales")
    if not isinstance(source, dict) or source.get("scope") != "all_time_gross_fulfillments":
        return {"available": False, "status": "unknown"}
    by_product = source.get("by_product")
    product_names = source.get("product_names")
    if not isinstance(by_product, dict) or not by_product or not isinstance(product_names, dict) \
            or any(not re.fullmatch(r"[a-z0-9-]+", product) or type(count) is not int or count < 0
                   for product, count in by_product.items()) \
            or any(not isinstance(product, str) or not isinstance(name, str) or not name
                   for product, name in product_names.items()) \
            or set(by_product) != set(product_names):
        return {"available": False, "status": "unknown"}
    return {
        "available": True,
        "status": "ok",
        "scope": source["scope"],
        "by_product": by_product,
        "product_names": product_names,
    }


def ranking_period(days: int = RANKING_DAYS, today: date | None = None) -> tuple[str, str]:
    """(start, end) for de seneste `days` fulde dage.

    Dagens time er ikke et fuldt døgn, så den tælles aldrig med i en
    rangering: en side må ikke se mere trafik ud, fordi rapporten tilfældigt
    blev kørt en tirsdag formiddag.
    """
    end_date = (today or datetime.now(timezone.utc).date()) - timedelta(days=1)
    return (end_date - timedelta(days=days - 1)).isoformat(), end_date.isoformat()


def load_offer_inventory() -> dict | None:
    """Domæne og public route for hver købsside + de fire centrale produktsider.

    Kilden er `tools/stripe_catalog.json`, som `tools/check_stripe_ctas.py`
    holder på linje med de virkelige sider (én CTA, tilladt link, dokumenteret
    pris). Uden filen er fallbacken *ukendt* — så påstår rapporten hverken en
    rangering eller en liste over synlige tilbud.
    """
    try:
        catalog = json.loads(OFFER_CATALOG.read_text(encoding="utf-8"))
        product_prices = {key: product.get("price") for key, product in catalog["products"].items()}
        offers = [offer for offer in catalog["offers"]
                  if isinstance(offer, dict) and offer.get("domain") in TRAFFIC_DOMAINS
                  and str(offer.get("route") or "").startswith("/")]
        core = [page for page in catalog["core_pages"]
                if isinstance(page, dict) and page.get("domain") in TRAFFIC_DOMAINS
                and str(page.get("route") or "").startswith("/") and str(page.get("why") or "").strip()]
    except (OSError, ValueError, KeyError, TypeError) as exc:
        note_error("købsinventar", exc)
        return None
    if not offers or len(core) != 4:
        note_error("købsinventar", "katalogens offers/core_pages er ufuldstændige")
        return None
    routes: dict[tuple[str, str], dict] = {}
    for offer in offers:
        key = (offer["domain"], offer["route"])
        entry = routes.setdefault(key, {"domain": key[0], "route": key[1], "products": [], "price": None})
        if offer["product"] not in entry["products"]:
            entry["products"].append(offer["product"])
        prices = {str(product_prices[product]) for product in entry["products"]
                  if product in product_prices and product_prices[product]}
        entry["price"] = ", ".join(sorted(prices)) or None
    return {
        "routes": routes,
        "core_pages": sorted(core, key=lambda page: (page["domain"], page["route"])),
    }


def _fallback(inventory: dict | None, reason: str) -> dict | None:
    """Den dokumenterede erstatning for en trafikrangering.

    Den er bevidst ikke en mest-besøgte-liste: den er den faste liste over de
    fire centrale produktsider og alle synlige Pro-tilbud, som konverterings-
    arbejdet går efter, indtil der er verificeret trafik at rangere på.
    """
    if inventory is None:
        return None
    return {
        "kind": "core_product_pages_and_visible_offers",
        "is_traffic_ranking": False,
        "reason": reason,
        "core_pages": [
            {"product": page["product"], "domain": page["domain"], "route": page["route"],
             "source": page.get("path"), "why": page["why"]}
            for page in inventory["core_pages"]
        ],
        "offer_pages": [dict(entry, products=sorted(entry["products"]))
                        for entry in sorted(inventory["routes"].values(),
                                            key=lambda entry: (entry["domain"], entry["route"]))],
    }


def build_ranking(
    per_domain_paths: dict,
    domain_status: dict,
    *,
    start: str,
    end: str,
    inventory: dict | None,
) -> dict:
    """Rangér de sælgende sider på de seneste syv fulde dages trafik.

    `basis` er kun `traffic`, når perioden faktisk kan bære en rangering:
    inventaret kan læses, alle fire domæner har et verificeret grundlag i
    perioden, og hvert rangeret domæne har mindst
    RANKING_MIN_PAGEVIEWS_PER_DOMAIN pageviews med mindst
    RANKING_MIN_TOTAL_PAGEVIEWS i alt. Ellers er den `unknown`, og rapporten
    falder tilbage på de centrale produktsider uden at påstå, at nogen af dem
    er mest besøgt. En rangeret liste uden det underlag er en løgn.
    """
    domains: list[dict] = []
    missing: list[str] = []
    below: list[dict] = []
    total = 0
    for domain in TRAFFIC_DOMAINS:
        paths = per_domain_paths.get(domain)
        if not isinstance(paths, dict) or (domain_status or {}).get(domain) != "ok" or not paths:
            missing.append(domain)
            below.append({"domain": domain, "visits": None, "reason": "ukendt datagrundlag i perioden"})
            continue
        visits = sum(paths.values())
        total += visits
        if visits >= RANKING_MIN_PAGEVIEWS_PER_DOMAIN:
            domains.append({"domain": domain, "visits": visits})
        else:
            below.append({"domain": domain, "visits": visits,
                          "reason": f"under {RANKING_MIN_PAGEVIEWS_PER_DOMAIN} verificerede pageviews"})

    ranked: list[dict] = []
    if inventory is not None:
        for (domain, route), entry in inventory["routes"].items():
            visits = (per_domain_paths.get(domain) or {}).get(route)
            if isinstance(visits, int) and visits > 0:
                ranked.append({"domain": domain, "route": route, "visits": visits,
                               "products": sorted(entry["products"])})
        ranked.sort(key=lambda row: (-row["visits"], row["domain"], row["route"]))

    if inventory is None:
        reason = "købsinventaret kunne ikke læses, så de sælgende sider kan ikke identificeres"
    elif missing:
        reason = (f"{', '.join(missing)} har ikke et verificeret datagrundlag i de seneste syv fulde dage, "
                  "så ingen side kan kaldes mest besøgt")
    elif not domains:
        reason = (f"intet domæne nåede {RANKING_MIN_PAGEVIEWS_PER_DOMAIN} verificerede "
                  "pageviews i de seneste syv fulde dage")
    elif total < RANKING_MIN_TOTAL_PAGEVIEWS:
        reason = (f"kun {total} verificerede pageviews i perioden "
                  f"(tærskel {RANKING_MIN_TOTAL_PAGEVIEWS})")
    else:
        reason = None

    return {
        "basis": "traffic" if reason is None else "unknown",
        "basis_reason": reason,
        "period": {"days": RANKING_DAYS, "kind": "last_7_full_days", "start": start, "end": end},
        "thresholds": {"min_total_pageviews": RANKING_MIN_TOTAL_PAGEVIEWS,
                       "min_pageviews_per_domain": RANKING_MIN_PAGEVIEWS_PER_DOMAIN},
        "total_pageviews": total,
        "ranked_domains": sorted(domains, key=lambda row: (-row["visits"], row["domain"]))
                           if reason is None else [],
        "ranked_offer_pages": ranked if reason is None else [],
        "domains_below_threshold": below,
        "fallback": _fallback(inventory, reason) if reason is not None else None,
    }


def _unknown_ranking(reason: str) -> dict:
    """Rangering uden datagrundlag. Fail-closed: ingen rangerede sider, ingen
    påstand om hvilke sider der er mest besøgte."""
    start, end = ranking_period()
    return {
        "basis": "unknown",
        "basis_reason": reason,
        "period": {"days": RANKING_DAYS, "kind": "last_7_full_days", "start": start, "end": end},
        "thresholds": {"min_total_pageviews": RANKING_MIN_TOTAL_PAGEVIEWS,
                       "min_pageviews_per_domain": RANKING_MIN_PAGEVIEWS_PER_DOMAIN},
        "total_pageviews": None,
        "ranked_domains": [],
        "ranked_offer_pages": [],
        "domains_below_threshold": [],
        "fallback": _fallback(load_offer_inventory(), reason),
    }


def _unknown_traffic(sales: dict, days: int, error: str | None = None) -> dict:
    result = {
        "available": True,
        "status": "unknown",
        "unique_status": "unknown",
        "window_days": days,
        "visits": None,
        "domains": {
            domain: {"status": "unknown", "visits": None, "top_paths": []}
            for domain in TRAFFIC_DOMAINS
        },
        "downloads": None,
        "download_domains": {
            domain: {"status": "unknown", "visits": None, "top_downloads": []}
            for domain in TRAFFIC_DOMAINS
        },
        "top_paths": [],
        "top_downloads": [],
        "sales": sales,
        "waitlist": None,
        "licenses_issued": None,
        "ai_asks": None,
        "scans": None,
        "ranking": _unknown_ranking(error or "trafikstatus er ukendt"),
    }
    if error:
        result["error"] = error
    return result


def collect_stats(days: int = 7) -> dict:
    # Hent én dag mere end vinduet: rangeringen gælder de seneste syv *fulde*
    # dage, og API'ets `days` tæller i dag med.
    url = f"{SITE}/api/stats?days={max(days, RANKING_FETCH_DAYS)}"
    token = stats_bearer_token()
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    data = http_json(url, timeout=120, headers=headers)
    if not data.get("ok"):
        raise RuntimeError(data.get("error") or "stats svarede ok=false")
    sales = _collect_sales(data)
    domain_status = data.get("domain_status")
    traffic_status = data.get("traffic_status")
    if traffic_status not in ("ok", "partial"):
        return _unknown_traffic(sales, days, "trafikstatus er ukendt")
    if not isinstance(domain_status, dict) or not any(domain_status.get(domain) == "ok" for domain in TRAFFIC_DOMAINS):
        return _unknown_traffic(sales, days, "alle domæner er ukendte")

    start, end = ranking_period()
    try:
        domains, visits, top, pages_complete, _ = _window_by_domain(
            data.get("stats_by_domain"), days, pageviews=True, domain_status=domain_status
        )
        if not any(domains[domain]["status"] == "ok" for domain in TRAFFIC_DOMAINS):
            return _unknown_traffic(sales, days, "ingen domæner har verificerede pageviews")
        download_domains, downloads, top_downloads, downloads_complete, _ = _window_by_domain(
            data.get("downloads_by_domain"), days, pageviews=False, domain_status=domain_status
        )
        _, _, _, _, ranking_paths = _window_by_domain(
            data.get("stats_by_domain"), days, pageviews=True, domain_status=domain_status,
            start=start, end=end,
        )
    except RuntimeError as exc:
        note_error("api/stats trafik", exc)
        return _unknown_traffic(sales, days, str(exc))

    ranking = build_ranking(ranking_paths, domain_status, start=start, end=end,
                            inventory=load_offer_inventory())

    status = "ok" if pages_complete and downloads_complete else "partial"
    return {
        "available": True,
        "status": status,
        "unique_status": data.get("unique_status", "unknown"),
        "window_days": days,
        "visits": visits,
        "domains": domains,
        "downloads": downloads,
        "download_domains": download_domains,
        "top_paths": [{"path": path, "visits": count} for path, count in top],
        "top_downloads": [{"file": file_name, "hits": count} for file_name, hits in top_downloads],
        "sales": sales,
        "waitlist": known_counter(data.get("waitlist")),
        "licenses_issued": known_counter(data.get("licenses_issued")) if sales.get("available") is True else None,
        "ai_asks": known_counter(data.get("ai_asks")),
        "scans": known_counter(data.get("scans")),
        "ranking": ranking,
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
            # GitHub returnerer ikke listen i dato-orden — sortér selv, ellers
            # skifter "seneste release" tilfældigt fra uge til uge.
            published = sorted(
                (r for r in rels if not r.get("draft")),
                key=lambda r: str(r.get("published_at") or r.get("created_at") or ""),
                reverse=True,
            )
            if published:
                latest = published[0]
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
# indsamling + sammenligning
# --------------------------------------------------------------------------
def collect_all() -> dict:
    now = datetime.now(timezone.utc)
    data = {
        "schema_version": 2,
        "iso_week": iso_week_key(now),
        "generated_at": now.isoformat(timespec="seconds"),
        "health": soft("api/health", collect_health, {}),
        "traffic": soft("api/stats", collect_stats, unknown_stats()),
        "npm": soft("npm", collect_npm, {}),
        "github": soft("github", collect_github, {}),
        "bugreports": soft("api/bugreport", collect_bugreports, {"available": False, "note": "kunne ikke hentes"}),
        "uptime": soft("deskuptime self-monitor", collect_uptime, {"note": "kunne ikke hentes"}),
        "links": soft("link-tjek", collect_links, {"available": False, "note": "kunne ikke hentes"}),
    }
    data["errors"] = list(ERRORS)
    data["ranking_basis"] = ((data.get("traffic") or {}).get("ranking") or {}).get("basis", "unknown")
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
        return "ukendt"
    return str(v)


# --------------------------------------------------------------------------
# rapport
# --------------------------------------------------------------------------
def _ranking_sections(ranking: dict) -> list[dict]:
    """Konverteringsrangeringen, ærligt mærket med sit datagrundlag.

    Rækker `basis: traffic`, vises de sælgende sider i de seneste syv fulde
    dage. Eller står der, hvorfor perioden ikke kan bære en rangering, og den
    dokumenterede fallback — de fire centrale produktsider og inventaret af
    alle synlige Pro-tilbud — uden at påstå, at nogen af dem er mest besøgte.
    """
    period = ranking.get("period") or {}
    start, end = period.get("start") or "?", period.get("end") or "?"
    thresholds = ranking.get("thresholds") or {}
    basis = ranking.get("basis", "unknown")
    title = f"Konverteringsrangering — seneste {period.get('days', RANKING_DAYS)} fulde dage ({start} til {end})"
    headers = ["Side", "Produkt", "Besøg"]
    fallback = ranking.get("fallback")
    reason = ranking.get("basis_reason")
    rows: list[list[str]] = []
    note_parts = [
        f"ranking_basis: **{basis}**",
        f"Tærskel: {thresholds.get('min_total_pageviews', RANKING_MIN_TOTAL_PAGEVIEWS)} verificerede "
        f"pageviews i perioden og {thresholds.get('min_pageviews_per_domain', RANKING_MIN_PAGEVIEWS_PER_DOMAIN)} "
        "i hvert domæne, der rangeres. Bot-, CI- og interne tjek filtreres i workeren.",
    ]

    if basis == "traffic":
        for row in ranking.get("ranked_offer_pages") or []:
            rows.append([f"{row['domain']}{row['route']}", ", ".join(row.get("products") or []),
                         str(row["visits"])])
        below = [entry for entry in ranking.get("domains_below_threshold") or []
                 if entry.get("visits") is not None]
        if below:
            note_parts.append("Under tærsklen og derfor ikke rangeret: "
                              + ", ".join(f"{entry['domain']} ({entry['visits']})" for entry in below) + ".")
        if not rows:
            note_parts.append("Ingen af de inventerede købssider havde besøg i perioden.")
        return [{"title": title, "headers": headers, "rows": rows, "note": " ".join(note_parts)}]

    note_parts.append(f"Rangering på trafik er ikke mulig: {reason or 'ukendt årsag'}.")
    if fallback is None:
        note_parts.append("Fallbacken er også ukendt, fordi købsinventaret ikke kunne læses. "
                          "Det er en fejl i `tools/stripe_catalog.json`, ikke et tomt resultat.")
        return [{"title": title, "headers": headers, "rows": [], "note": " ".join(note_parts)}]

    note_parts.append("Nedenfor er den dokumenterede fallback, **ikke** en mest-besøgte-rangering. "
                      "Den bruges, indtil en periode har verificeret trafik.")
    for page in fallback.get("core_pages") or []:
        rows.append([f"{page['domain']}{page['route']}", page.get("product") or "", "—"])
    sections = [{"title": title, "headers": headers, "rows": rows, "note": " ".join(note_parts)}]

    offers = fallback.get("offer_pages") or []
    if offers:
        sections.append({
            "title": "Synlige Pro-tilbud (inventar, ikke rangering)",
            "headers": ["Side", "Produkt", "Pris"],
            "rows": [[f"{offer['domain']}{offer['route']}", ", ".join(offer.get("products") or []),
                      str(offer.get("price") or "")] for offer in offers],
            "note": (f"{len(offers)} sider fra `tools/stripe_catalog.json`, som "
                     "`tools/check_stripe_ctas.py` holder på linje med de virkelige købsknapper. "
                     "Det er et inventar, ikke en rangering efter besøg."),
        })
    return sections


def build_report(data: dict, prev: dict | None) -> tuple[str, list[str], list[dict]]:
    """Returnerer (emne, notabelt, sektioner). Sektion = {title, headers, rows, note}."""
    week = data["iso_week"].split("-")[1]
    notable: list[str] = []
    sections: list[dict] = []
    first_run = prev is None

    # --- Trafik ---
    tr, hl = data.get("traffic") or {}, data.get("health") or {}
    traffic_status = tr.get("status")
    traffic_complete = tr.get("available") is True and traffic_status == "ok"
    traffic_available = tr.get("available") is True and traffic_status in ("ok", "partial")
    ptr = ((prev or {}).get("traffic") or {}) if (prev or {}).get("schema_version") == 2 else {}
    rows = []
    for label, key in [("Besøg (7 dage)", "visits"), ("Downloads (7 dage)", "downloads"),
                       ("Compliance-scans (total)", "scans"), ("Licenser udstedt (alle tider)", "licenses_issued"),
                       ("Ventelisten (total)", "waitlist"), ("AI-spørgsmål (total)", "ai_asks")]:
        cur = tr.get(key)
        if cur is None and key in ("scans", "waitlist"):
            cur = hl.get(key)
        change = delta(cur, ptr.get(key))
        rows.append([label, fmt_num(cur), fmt_delta(change)])
        if change:
            notable.append(f"{label.split(' (')[0].lower()} {fmt_delta(change)}")
    if traffic_complete:
        note = None
    elif not tr:
        # Intet trafikblok blev gemt. Det er en anden fejl end et svar vi fik og
        # ikke kunne bruge, og kun den første må siges. At skylde på
        # /api/stats for en blok der aldrig blev skrevet, er en påstand om en
        # årsag rapporten ikke har undersøgt.
        note = "Trafiktal er ukendt, fordi denne rapport ikke gemte et trafikblok."
    elif traffic_status == "partial":
        note = "Trafiktallet er delvist ukendt, fordi ikke alle fire domæner har verificeret datagrundlag."
    else:
        note = "Trafiktal er ukendt, fordi mahope.tools/api/stats ikke leverede komplette data."
    sections.append({"title": "Trafik og brug (Cloudflare KV)", "headers": ["Måltal", "Nu", "Δ uge"],
                     "rows": rows, "note": note})

    for domain in TRAFFIC_DOMAINS:
        domain_data = (tr.get("domains") or {}).get(domain) or {}
        if traffic_available and domain_data.get("status") == "ok":
            top_paths = domain_data.get("top_paths") or []
            domain_rows = [[item["path"], str(item["visits"])] for item in top_paths]
            domain_note = None if domain_rows else "Ingen verificerede pageviews i denne 7-dages periode."
        else:
            domain_rows = []
            domain_note = "Trafik for dette domæne er ukendt."
        sections.append({"title": f"Mest besøgte sider — {domain}", "headers": ["Side", "Besøg"],
                         "rows": domain_rows, "note": domain_note})

    if traffic_complete and tr.get("top_downloads"):
        sections.append({"title": "Mest hentede filer (7 dage)", "headers": ["Fil", "Hits"],
                         "rows": [[item["file"], str(item["hits"])] for item in tr["top_downloads"]], "note": None})

    sections.extend(_ranking_sections(tr.get("ranking") or {}))

    sales = tr.get("sales") or {"available": False, "status": "unknown"}
    if sales.get("available") is True and sales.get("status") == "ok":
        by_product = sales.get("by_product") or {}
        product_names = sales.get("product_names") or {}
        sales_rows = [[product_names.get(product, product), str(count), ""]
                      for product, count in sorted(by_product.items(), key=lambda item: item[0])]
        if not sales_rows:
            sales_rows = [["Ingen dokumenterede salg", "0", ""]]
        sales_note = "Brutto, deduplikerede Stripe-checkout-sessioner fra `ful:`-ledgeren; ikke omsætning."
    else:
        sales_rows = []
        sales_note = "Stripe-salg er ukendt, fordi fulfillment-ledgeren ikke kunne læses komplet."
    sections.append({"title": "Stripe-salg (alle tider, deduplikeret)", "headers": ["Produkt", "Salg", ""],
                     "rows": sales_rows, "note": sales_note})

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
        if d or (first_run and bb.get("last_week")):
            notable.append(f"{bb['last_week']} BugBottle-rapporter ({fmt_delta(d)})" if d
                           else f"{bb['last_week']} BugBottle-rapporter")
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
