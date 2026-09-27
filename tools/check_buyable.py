#!/usr/bin/env python3
"""Hvilke betalte produkter kan overhovedet sælges, og hvilke mangler en købsside?

Baggrund (målt 27.9): 7 af 13 produkterne i `tools/stripe_catalog.json` har et
fungerende Stripe-link og **står på nul sider**. Det så ud som en mangel på
markedsføring, men `check_stripe_ctas.py` viste den rigtige grund, da en
købsknap blev sat på `compliance-report.html`:

    sælger eucomply-dpa, men filerne er ikke i KV (dpa-template.pdf,
    dpa-template.md) — køberen betaler for et køb der svarer 503 i
    /api/download.

Knapperne var altså **med vilje** væk: kilderne ligger i det private repo
`mahope/paid-products`, og filerne skal uploades til Cloudflare KV før
`kv_verified` kan sættes til `true` i `tools/paid_content.json`.

Det gav et stumt hul: ingen port siger noget om de 7 produkter, fordi
`check_stripe_ctas.py` kun kan dømme et produkt, *når en side sælger det*. De
kunne derfor ligge uudsolgte i lige så mange iterationer, uden at noget
skreg. Det er det denne port lukker.

**Portens regel er derfor modsat den man kunne tro.** Den er *kun* rød, når et
produkt er **købsklart** — licens, eller betalt indhold med `kv_verified` — og
samtidig ikke sælges på nogen side. Så længe indholdet ikke ligger i KV er
sagen Mads' (se `❓ Til Mads` i IMPLEMENTATION_PLAN.md), ikke en fejl her, og
porten siger det i sin rapport uden at rødme.

Omvendt gør porten `kv_verified` til en **pligt**: den dag Mads sætter den til
`true` på et produkt, bliver det rødt i CI med produktets navn, indtil en side
sælger det. Det er hele pointen — et købsklart produkt uden købsknap er en
mangel, ikke en plan.

Bevis: `--self-test` muterer *inventaret* (ikke en side), fordi det er
inventaret der afgør om noget er købsklart. Se `self_test()`.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "tools/stripe_catalog.json"
PAID_CONTENT = ROOT / "tools/paid_content.json"
SITE = ROOT / "site"
DIST = ROOT / "dist"

# Produkter der hører til et *andet* repo. `transmute-desktop` har et
# fungerende Stripe-link, men Transmute har ingen side i dette repo — den
# ligger i `mahope/transmute` (jf. kontrakten i missionen). At kræve en
# købsknap her ville være en fejl, ikke en måling.
OTHER_REPO = ("transmute-desktop",)


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def inventory(paid: dict) -> dict[str, dict]:
    """`product_key` -> inventaret fra `paid_content.json`.

    Leveringsfilerne står her og **ikke** i `stripe_catalog.json`; at læse dem
    fra katalogerne gav "0 filer ikke i KV" for alle syv produkter, altså en
    rapport der lignede en måling men ikke var en.
    """
    return {p["product_key"]: p for p in paid.get("products", [])}


def buyable(key: str, product: dict, inv: dict[str, dict]) -> tuple[bool, str]:
    """Er produktet *købsklart* — altså: tager en købsknap imod nu?

    Licenser kræver ingen filer: køberen får en nøgle, og nøglen findes i
    koden. Betalt indhold kræver at filerne faktisk kan hentes, ellers svarer
    `/api/download` 503 — og det er præcis det `check_stripe_ctas.py` dømmer.

    Et produkt der ikke står i `paid_content.json` regnes **ikke** som
    verificeret. Det er den forsigtige læsning: koster vi en rød fejl, hvis
    et nyt licensprodukt ikke endnu er skrevet ind, så mangler vi en købsside.
    """
    if product.get("kind") == "license":
        return True, "licens — ingen filer at hente"
    row = inv.get(key)
    if row and row.get("kv_verified"):
        return True, "kv_verified"
    n = len((row or {}).get("delivery_files") or ())
    return False, f"{n} filer ikke i KV"


def sold_on(key: str, product: dict, site: Path) -> list[str]:
    """På hvilke sider i `site/` står produktets betalings-id?

    Vi matcher på **Payment Link-id**, ikke på produktnavnet: navnet kan stå i
    en omtale uden at man kan købe, og id'et kan kun stå på en side der har
    den konkrete knap. Det er den samme metode som `check_stripe_ctas.py`
    bruger, så de to porte kan ikke være uenige om hvad "sælger" betyder.
    """
    link = product.get("payment_link") or ""
    pid = link.rstrip("/").split("/")[-1]
    if not pid:
        return []
    hits = []
    for path in sorted(site.rglob("*.html")):
        if pid in path.read_text(encoding="utf-8", errors="replace"):
            hits.append(path.relative_to(site).as_posix())
    return hits


def sold_on_built(key: str, product: dict, dist: Path, site: Path) -> list[str]:
    """På hvilke **publicerede** sider står produktets betalings-id?

    Samme fejlform som `check_stripe_ctas.py` havde, målt 27.9: `sold_on` læser
    kun `site/`, men `deskuptime.com/tools/` bygges fra `../auditedwp` og
    indeholder to købsknapper. Porten kunne derfor ikke se den ene reelle
    Pro-side for DeskUptime, og rapporten under-rettede hvilke sider der sælger.

    Her læses det **byggede** site, men kun de ruter der **ikke** findes i
    `site/`: en bygget kopi af en kilde vi allerede har listet op ville bare
    være dobbelt sådan. Sådan forsvinder hver side der stammer fra et
    sibling-repo (`deskuptime.com/tools/`) uden at listen bliver ulæselig.
    """
    link = product.get("payment_link") or ""
    pid = link.rstrip("/").split("/")[-1]
    if not pid or not dist.is_dir():
        return []
    hits = []
    for path in sorted(dist.glob("*/*.html")) + sorted(dist.glob("*/*/*.html")):
        dom = path.relative_to(dist).parts[0]
        rel = path.relative_to(dist / dom).as_posix()
        if (site / rel).exists():
            continue
        if pid in path.read_text(encoding="utf-8", errors="replace"):
            hits.append(f"{dom}/{rel[:-5]}" if rel.endswith(".html") else f"{dom}/{rel}")
    return hits


def evaluate(catalog: dict, paid: dict, site: Path,
             dist: Path | None = None) -> tuple[list[str], list[str]]:
    """Returnér (fejl, rapport). `fejl` er tom, når intet købsklart mangler."""
    errs: list[str] = []
    report: list[str] = []
    inv = inventory(paid)
    for key, product in catalog["products"].items():
        pages = sold_on(key, product, site)
        built = sold_on_built(key, product, dist, site) if dist else []
        if key in OTHER_REPO:
            report.append(f"  {key}: ikke i dette repo (kræver ingen købsknap her)")
            continue
        ready, why = buyable(key, product, inv)
        if pages or built:
            # Genererede sider mærkes, så en kilde i et sibling-repo ikke læses
            # som en side i dette repo — det er præcis det forvekslingspunkt,
            # der gjorde at `/tools/` ikke blev set.
            shown = list(pages) + [f"{r} (genereret)" for r in built]
            report.append(f"  {key}: sælges på {', '.join(shown)}")
            continue
        if ready:
            errs.append(
                f"{key} ({product.get('name')}) er købsklart ({why}) men "
                f"står på nul sider — tilføj en købsknap med "
                f"{product.get('payment_link')}"
            )
        else:
            report.append(f"  {key}: ikke sælgt — {why} (blokeret på KV-upload)")
    return errs, report


def run(site: Path, dist: Path | None = DIST) -> int:
    errs, report = evaluate(load(CATALOG), load(PAID_CONTENT), site, dist)
    print("== buyable: hvert katalogprodukt og hvor det sælges")
    for line in report:
        print(line)
    n_blocked = sum(1 for line in report if "blokeret på KV-upload" in line)
    if n_blocked:
        print(f"  {n_blocked} produkter venter på at filerne uploades til KV.")
    if errs:
        print(f"\nbuyable: {len(errs)} fejl")
        for e in errs:
            print(f"  {e}")
        return 1
    print("buyable: OK")
    return 0


def self_test() -> int:
    """Bevis at porten kan se et købsklart produkt uden købsside — og at den
    *ikke* rødmer på et produkt, der endnu ikke kan leveres."""
    if not shutil.which("git"):
        print("selftest: SKIP (git mangler)")
        return 0
    real_catalog = load(CATALOG)
    real_paid = load(PAID_CONTENT)
    failures = 0

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)

        # Vælg et produkt, der findes i **begge** filer. Første nøgle i
        # katalogerne er `clean-copy-pro`, som er en licens og derfor ikke i
        # `paid_content.json` — selften sprang over, fordi mutationerne så
        # aldrig kørte, hvilket er præcis den fejl de tidligere selftests har
        # haft.
        paid_keys = {p["product_key"] for p in real_paid.get("products", [])}
        key = next(
            (k for k in real_catalog["products"]
             if k not in OTHER_REPO and k in paid_keys),
            None,
        )
        if key is None:
            print("selftest: SKIP (intet produkt findes i begge filer)")
            return 0

        def write(catalog: dict, paid: dict, name: str = "site") -> Path:
            (tmp / "catalog.json").write_text(json.dumps(catalog), encoding="utf-8")
            (tmp / "paid.json").write_text(json.dumps(paid), encoding="utf-8")
            site = tmp / name
            site.mkdir(parents=True, exist_ok=True)
            return site

        def errors(catalog: dict, paid: dict, name: str = "site") -> list[str]:
            return evaluate(catalog, paid, write(catalog, paid, name))[0]

        # Positiv kontrol på den **rigtige** overflade: de licensprodukter der
        # faktisk sælges, skal være grønne. En tom site ville rødme dem, og det
        # ville have lignede en fejl i porten — så kontrolken må ikke lyve ved
        # at fjerne den overflade, porten skal dømme.
        live_errs = evaluate(real_catalog, real_paid, SITE)[0]
        sold_here = sum(
            1 for k in real_catalog["products"]
            if k not in OTHER_REPO and sold_on(k, real_catalog["products"][k], SITE)
        )
        if live_errs:
            print(f"  FEJL: den rigtige kode er rød på det rigtige repo: {live_errs}")
            failures += 1
        elif sold_here < 1:
            print("  FEJL: ingen produkter fundet på den rigtige overflade — "
                  "kontrollen ville være grøn uden at se noget")
            failures += 1
        else:
            print(f"  ✓ positiv kontrol: {sold_here} produkter sælges på "
                  f"site/ og er grønne")

        # M1: kv_verified slås til -> produktet er købsklart -> skal rødme.
        paid1 = json.loads(json.dumps(real_paid))
        for p in paid1["products"]:
            if p["product_key"] == key:
                p["kv_verified"] = True
        m1 = errors(real_catalog, paid1, "m1")
        if not any(key in e for e in m1):
            print(f"  FEJL M1: kv_verified=true på {key} gav ingen fejl")
            failures += 1
        else:
            print(f"  ✓ mutation fanget: kv_verified=true uden købsside ({key})")

        # M2: et licensprodukt uden købsside skal rødme. `deskuptime-pro` er
        # `kind: license`, så det er købsklart uden at nogen fil skal i KV.
        lic = next(
            (k for k, v in real_catalog["products"].items()
             if v.get("kind") == "license" and k not in OTHER_REPO),
            None,
        )
        if lic:
            m2 = errors(real_catalog, real_paid, "m2")
            if not any(lic in e for e in m2):
                print(f"  FEJL M2: licensproduktet {lic} gav ingen fejl på en tom site")
                failures += 1
            else:
                print(f"  ✓ mutation fanget: licensprodukt uden købsside ({lic})")
        else:
            print("  M2: springes (intet licensprodukt i katalogen)")

        # M3: en side der sælger produktet skal gøre porten grøn igen.
        site3 = write(real_catalog, paid1, "m3")
        (site3 / "shop.html").write_text(
            f'<a href="{real_catalog["products"][key]["payment_link"]}">køb</a>',
            encoding="utf-8",
        )
        m3 = evaluate(real_catalog, paid1, site3)[0]
        if any(key in e for e in m3):
            print(f"  FEJL M3: siden med købsknappen blev stadig dømt: {m3}")
            failures += 1
        else:
            print(f"  ✓ positiv kontrol: købsknap på en side gør {key} grøn igen")

        # M4: en side der *nævner* produktet uden linket må ikke tælle som salg.
        site4 = write(real_catalog, paid1, "m4")
        (site4 / "blog.html").write_text(
            f'<p>We also sell the {real_catalog["products"][key]["name"]}.</p>',
            encoding="utf-8",
        )
        m4 = evaluate(real_catalog, paid1, site4)[0]
        if not any(key in e for e in m4):
            print(f"  FEJL M4: en omtale uden betalingslink talte som salg ({key})")
            failures += 1
        else:
            print(f"  ✓ mutation fanget: omtale uden betalingslink er ikke et salg ({key})")

        # M5: et produkt der **kun** sælges på en genereret side må ikke læses
        # som "står på nul sider". Uden `dist` ville porten rødme et produkt der
        # har en fungerende købsknap — en falsk rød fejl, fordi knappen findes.
        site5 = write(real_catalog, paid1, "m5")
        dist5 = tmp / "d5"
        (dist5 / "eksempel.test").mkdir(parents=True)
        (dist5 / "eksempel.test" / "tools.html").write_text(
            f'<a href="{real_catalog["products"][key]["payment_link"]}">køb</a>',
            encoding="utf-8",
        )
        m5_errs, m5_report = evaluate(real_catalog, paid1, site5, dist5)
        m5_line = next((l for l in m5_report if l.strip().startswith(f"{key}:")), "")
        if any(key in e for e in m5_errs):
            print(f"  FEJL M5: en genereret købsside blev dømt som nul sider ({m5_errs})")
            failures += 1
        elif "eksempel.test/tools" not in m5_line or "genereret" not in m5_line:
            print(f"  FEJL M5: rapporten nævner ikke den genererede side: {m5_line!r}")
            failures += 1
        else:
            print(f"  ✓ positiv kontrol: genereret købsside tæller og mærkes ({key})")

        # M6: en genereret side der *nævner* produktet uden linket må ikke tælle
        # som salg — samme regel som M4, bare på den byggede overflade.
        dist6 = tmp / "d6"
        (dist6 / "eksempel.test").mkdir(parents=True)
        (dist6 / "eksempel.test" / "om.html").write_text(
            f'<p>Vi sælger også {real_catalog["products"][key]["name"]}.</p>',
            encoding="utf-8",
        )
        m6 = evaluate(real_catalog, paid1, write(real_catalog, paid1, "m6"), dist6)[0]
        if not any(key in e for e in m6):
            print(f"  FEJL M6: en omtale på en genereret side talte som salg ({key})")
            failures += 1
        else:
            print(f"  ✓ mutation fanget: omtale uden link på genereret side er ikke et salg ({key})")

    total = 6
    print(f"selftest: {total - failures}/{total} mutationer fanget")
    return 1 if failures else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--self-test", action="store_true", help="mutér inventaret og kræv rødt")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    return run(SITE)


if __name__ == "__main__":
    sys.exit(main())
