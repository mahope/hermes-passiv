#!/usr/bin/env python3
"""Dømmer at katalogens `where`-henvisninger peger på noget der findes.

Baggrund (målt 2/10): `tools/stripe_catalog.json` tegner gratis-mod-Pro-
tabellen på nitten sider, og hver funktion i den bærer et `where`, der skal
sige **hvor** den er. Målt på de otte produktsider: ingen port læste disse
henvisninger. De var skrevet i hånden, de pegede på filer, der fandtes, og de
indeholdt linjenumre — men ingen kørsel sammenlignede dem med filerne. Et
`where` der sagde `site/scan.html:233-266` ville være lige så grønt, hvis de
elleve `add()`-kald var flyttet til linje 900, eller hvis filen var slettet.

Det er samme fejlform som dom 6 i `check_pro_table.py` blev skrevet for, bare
på den anden side af porten: kortene låne en funktionsliste, der var skrevet til
en anden side, og dom 6 stoppede det. Her stopper porten det samme for
**belæget** — en funktion der siger «dette tjek kører i browseren» med et `where`
der peger på noget, der ikke findes, er ikke dokumentation, den er en løgned.

Dommen er fire ting, og hver især kan være grøn mens de andre er røde:

  1. **Filen skal findes.** `where` skal pege på en fil i repoet.
  2. **Linjerne skal findes.** `where` skal give **ét** interval
     (`fil:12` eller `fil:12-34`), der ikke løber baglæns og ikke forbi filens
     sidste linje. To filer i én henvisning er røde: den er da ikke længere en
     målbar pejling, men en forklaring.
  3. **Citatet skal stå i intervallet.** Hver `«…»` skal kunne findes dér,
     efter at HTML-tags er fjernet og mellemrum er normaliseret — fordi en
     reference ellers ville være grøn for en sætning, der er brudt i to
     `<strong>`.
  4. **Alle funktioner skal have et `where`.** En funktion uden henvisning er
     den stærkeste påstand af alle, og den er den der går hurtigst i stykker.

Kun `pro_table_pages` dommes. Produkternes **egne** funktionslister dømmes også,
fordi de tegnes på produktsiderne — men kun deres `where`, ikke deres lister
(den del er dom 6 og dom 4 i `check_pro_table.py`).

    python3 tools/check_catalog_where.py             # dom
    python3 tools/check_catalog_where.py --self-test # 10 mutationer
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "tools" / "stripe_catalog.json"

# `fil:linje` eller `fil:fra-til` i starten af `where`. Resten af strengen er
# forklaringen og må gerne genanvende **samme** fil med `:193` — det er den
# kortere måde at henvise til to steder i én fil på.
HENVISNING_RE = re.compile(r"^([A-Za-z0-9_][A-Za-z0-9_./-]*\.[A-Za-z]+):(\d+)(?:-(\d+))?")
# Yderligere intervaller i den samme fil, skrevet `:193` eller `:193-197`.
FLERE_RE = re.compile(r"(?<!\w):(\d+)(?:-(\d+))?")
# **Alle** `fil:linje`-henvisninger i en `where`, ikke kun den første. Målt 2/10:
# ni af katalogens henvisninger begrunder sig i to filer («håndhævet i
# src/watch.js:372-376»), og det er ikke en løgn — det er oplysende. Men hver af
# dem skal kunne dømmes, ellers er den blot den anden halvdel af en påstand, der
# ikke kan efterprøves.
ALLE_HENVISNINGER_RE = re.compile(
    r"([A-Za-z0-9_][A-Za-z0-9_./-]*\.[A-Za-z]+):(\d+)(?:-(\d+))?")
TAG_RE = re.compile(r"<[^>]+>")


def ryd(tekst: str) -> str:
    """Tags væk, mellemrum normaliseret. Så «et EUComply Pro» kan findes i en
    sætning, kilden har delt med `<strong>EUComply Pro</strong>`."""
    return re.sub(r"\s+", " ", TAG_RE.sub(" ", tekst)).strip()


def katalog() -> dict:
    return json.loads(CATALOG.read_text(encoding="utf-8"))


def find_fil(rel: str, root: Path) -> Path | None:
    """Den fil `where` peger på, hvis den findes. Rækkefølgen er den korte
    sti først, fordi katalogens henvisninger er skrevet relative til roden."""
    for præfiks in ("", "site/", "tools/", "scanner/", "extension-clean-copy/",
                    "page-profile/", "extension-clean-copy-vscode/",
                    "extension-clean-copy-firefox/", "ebook/", "desktop/"):
        kandidat = root / (præfiks + rel)
        if kandidat.is_file():
            return kandidat
    return None


def er_gitlink(rel: str, root: Path) -> bool:
    """True når `where` peger ind i et submodule, der ikke er udfyldt her.

    Målt 2/10: `deskuptime-pro`s otte funktioner peger på `deskuptime/src/*.js`,
    og `deskuptime/` er et **gitlink** — et tomt katalog i dette checkout, med
    koden i sibling-repoet `../deskuptime`. En port der kræver filen her ville
    være rød i CI, hvor der kun hentes ét repo, så filen kan aldrig findes. Men
    at springe dem helt over ville være en stille undtagelse, så de får deres
    egen linje i rapporten i stedet for at forsvinde.
    """
    top = rel.split("/")[0]
    sti = root / top
    return sti.is_dir() and not any(sti.iterdir())


def dom(catalog: dict, root: Path = ROOT,
        noter: list[str] | None = None) -> list[str]:
    fund: list[str] = []
    # Henvisninger ind i et submodule, der ikke er udfyldt i dette checkout.
    # De dømmes på **form** (findes filstien på nogen platform, er intervallet
    # baglæns) men ikke på citat, fordi filen slet ikke er her. En sådan er
    # ikke en fejl — men den må heller ikke forsvinde, så den skrives i `noter`.
    gitlinks: list[str] = []
    produkter = catalog.get("products") or {}
    sider = catalog.get("pro_table_pages")
    if not isinstance(sider, list) or not sider:
        return [f"katalog: pro_table_pages skal være en ikke-tom liste, fandt {sider!r}"]

    def døm(hælder: str, rel: str, felt: str, feature: dict) -> None:
        fid = feature.get("id")
        where = str(feature.get("where") or "").strip()
        m = HENVISNING_RE.match(where)
        if not m:
            fund.append(f"{hælder}: {felt} {fid!r} har intet `fil:linje` i sit "
                        f"`where` ({where[:60]!r}) — en påstand uden pejling kan "
                        f"ikke efterprøves")
            return
        # Hver `fil:linje` i strengen dømmes. Et nøgne `:193` bagefter hører
        # til den fil, henvisningen lige foran startede med — det er den kortere
        # måde at henvise til to steder i én fil. Og `src/watch.js:372` efter
        # `deskuptime/src/features.js:33` er en sti **relativ** til den første
        # fil, fordi det er sådan katalogens henvisninger er skrevet.
        segmenter: list[str] = []
        base: Path | None = None
        # Roden i et submodule, hvis den første henvisning landede i et. Så
        # ved vi at de følgende `src/watch.js:372` også er derude.
        gitlink_rod: str | None = None
        for henvisning in ALLE_HENVISNINGER_RE.finditer(where):
            sti = henvisning.group(1)
            # Er vi allerede nået ind i et submodule med en tidligere
            # henvisning i samme `where`, så er resten af den samme slags note.
            # Det er nødvendigt fordi katalogens DeskUptime-henvisninger skriver
            # den anden fil relativt (`src/watch.js:372` efter
            # `deskuptime/src/features.js:33`), og mappen er tom i checkouten.
            if gitlink_rod and not find_fil(sti, root):
                gitlinks.append(f"{hælder}: {felt} {fid!r} ({sti})")
                continue
            målsti = find_fil(sti, root)
            if not målsti and base is not None:
                # `deskuptime/src/features.js:33 … håndhævet i src/watch.js:372`:
                # den anden sti er relativ, fordi katalogens henvisninger er
                # skrevet sådan. Uden dette ville de otte DeskUptime-funktioner
                # være røde på en sti, der faktisk findes i sibling-repoet.
                trial = base.parent / sti
                if trial.is_file():
                    målsti = trial
            if not målsti:
                if er_gitlink(sti, root) or (
                        gitlink_rod and (gitlink_rod + "/" + sti).startswith(sti)):
                    gitlink_rod = gitlink_rod or sti.split("/")[0]
                    base = base or (root / gitlink_rod)
                    gitlinks.append(f"{hælder}: {felt} {fid!r} ({sti})")
                else:
                    fund.append(f"{hælder}: {felt} {fid!r} peger på {sti}, som "
                                f"ikke findes i repoet")
                continue
            base = målsti
            linjer = målsti.read_text(encoding="utf-8").splitlines()
            rel_sti = målsti.relative_to(root)
            x0 = int(henvisning.group(2))
            y0 = int(henvisning.group(3)) if henvisning.group(3) else x0
            for x, y in [(x0, y0)]:
                if y < x:
                    fund.append(f"{hælder}: {felt} {fid!r} har intervallet "
                                f"{x}-{y} i {rel_sti} — det løber baglæns")
                    continue
                if y > len(linjer):
                    fund.append(f"{hælder}: {felt} {fid!r} peger på "
                                f"{rel_sti}:{x}-{y}, men filen har kun "
                                f"{len(linjer)} linjer")
                    continue
                segmenter.append(ryd(" ".join(linjer[x - 1:y])))
        for citat in re.findall(r"«([^»]+)»", where):
            renset = ryd(citat)
            if not any(renset in seg for seg in segmenter):
                fund.append(f"{hælder}: {felt} {fid!r} — citatet {citat[:55]!r} "
                            f"står ikke i noget af de {len(segmenter)} "
                            f"citerede intervaller")

    for post in sider:
        if not isinstance(post, dict):
            fund.append("katalog: en pro-table-side er ikke et objekt")
            continue
        rel = str(post.get("path"))
        produkt = produkter.get(post.get("product"))
        egen_side = (isinstance(produkt, dict)
                     and rel.lstrip("./") in (produkt.get("own_pages") or []))
        for felt in ("free_features", "pro_features"):
            # Egne sider låner produktets liste — og tegner den, så dens `where`
            # dømmes her. Værktøjssider har deres egne.
            kilder = post.get(felt) or (produkt or {}).get(felt) or []
            for feature in kilder:
                døm(rel, rel, felt, feature)
            if not egen_side and not post.get(felt):
                fund.append(f"{rel}: mangler egne {felt} — en værktøjsside må "
                            f"ikke låne {post.get('product')!r}s liste")
    if noter is not None:
        noter.extend(sorted(set(gitlinks)))
    return fund


def _kopi(root: Path) -> Path:
    """Kopi af katalogen og af hver fil dens `where`-henvisninger peger på.

    Mutationerne skal dømmes mod en kopi, så porten kan se en fil **mangle** —
    det er den fejl, hele porten findes for. Derfor kopieres alle filer, også
    dem kun produkternes egne lister peger på.
    """
    (root / "tools").mkdir(parents=True, exist_ok=True)
    shutil.copy2(CATALOG, root / "tools" / "stripe_catalog.json")
    kat = json.loads(CATALOG.read_text(encoding="utf-8"))
    wheres: list[str] = []
    for post in kat["pro_table_pages"]:
        for felt in ("free_features", "pro_features"):
            for f in (post.get(felt) or []):
                wheres.append(str(f.get("where") or ""))
    for produkt in kat["products"].values():
        for felt in ("free_features", "pro_features"):
            for f in (produkt.get(felt) or []):
                wheres.append(str(f.get("where") or ""))
    for where in wheres:
        for henvisning in ALLE_HENVISNINGER_RE.finditer(where):
            src = find_fil(henvisning.group(1), ROOT)
            if src is None:
                continue
            rel = src.relative_to(ROOT)
            if (root / rel).is_file():
                continue
            (root / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, root / rel)
    # `site/scan.html` er den mutationerne rører ved siden af katalogen.
    for rel in ("site/scan.html", "site/contrast-checker.html"):
        mål = root / rel
        if not mål.is_file():
            mål.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / rel, mål)
    # Submodulerne skal findes som **tomme mapper** i kopien, ellers kan porten
    # ikke kende dem fra en sti, der aldrig har eksisteret — og mutationerne så
    # en rød fejl, de ikke selv skabte.
    for indhold in ROOT.iterdir():
        if indhold.is_dir() and not any(indhold.iterdir()):
            (root / indhold.name).mkdir(parents=True, exist_ok=True)
    return root


def _sæt_where(root: Path, sti: str, felt: str, fid: str, ny: str) -> None:
    """Skriv ét `where` i kopien af katalogen — den mutation, der skal være rød."""
    katfil = root / "tools" / "stripe_catalog.json"
    kat = json.loads(katfil.read_text(encoding="utf-8"))
    fundet = False
    for post in kat["pro_table_pages"]:
        if post["path"] == sti:
            for f in post.get(felt) or []:
                if f.get("id") == fid:
                    f["where"] = ny
                    fundet = True
    assert fundet, (sti, felt, fid)
    katfil.write_text(json.dumps(kat, indent=2, ensure_ascii=False), encoding="utf-8")


def self_test() -> int:
    fejl: list[str] = []
    talt = [0]

    def tjek(navn: str, sand: bool, detalje: str = "") -> None:
        talt[0] += 1
        if not sand:
            fejl.append(f"{navn}{': ' + detalje if detalje else ''}")

    # 0. Målingen på det rigtige repo skal være grøn, ellers dømmer mutationerne
    #    nedenfor noget, der allerede var rødt.
    rød = dom(katalog())
    tjek("målingen er grøn på repoet", not rød, "; ".join(rød[:3]))

    def kat_fra(rod: Path) -> dict:
        """Katalogen **som den ser ud i kopien** — ellers dømmer mutationerne
        mod originalen og intet af dem kan finde fejlen."""
        return json.loads((rod / "tools" / "stripe_catalog.json")
                          .read_text(encoding="utf-8"))

    with tempfile.TemporaryDirectory() as tmp:
        rod = _kopi(Path(tmp))
        fund = dom(kat_fra(rod), rod)
        tjek("kopien er grøn", not fund, "; ".join(fund[:3]))

    def med(mut) -> list[str]:
        with tempfile.TemporaryDirectory() as tmp:
            rod = _kopi(Path(tmp))
            mut(rod)
            return dom(kat_fra(rod), rod)

    # 1. En fil, der ikke findes. Uden dom 1 ville `where` være grønt for en
    #    funktion, der peger på et værktøj, vi aldrig byggede.
    fund = med(lambda rod: _sæt_where(
        rod, "site/scan.html", "free_features", "a11y",
        "site/scan-uden-existence.html:12"))
    tjek("fil der ikke findes er rød",
         any("ikke findes i repoet" in f for f in fund), str(fund[:2]))

    # 2. Et linjenummer forbi filens ende — det `where`, der ser helt rigtigt ud.
    fund = med(lambda rod: _sæt_where(
        rod, "site/scan.html", "free_features", "a11y",
        "site/scan.html:233-9000 — elleve add()-kald"))
    tjek("linje uden for filen er rød",
         any("har kun" in f and "linjer" in f for f in fund), str(fund[:2]))

    # 3. Et citat, der ikke står i intervallet. Det er den mutation, der ligner
    #    den virkelige fejl mest: `where` ser rigtigt ud, men siger noget andet
    #    end koden gør.
    fund = med(lambda rod: _sæt_where(
        rod, "site/scan.html", "pro_features", "pdf",
        "site/scan.html:95-96 «A EUComply Pro licence gør dig til administrator»"))
    tjek("citat der ikke findes i intervallet er rødt",
         any("står ikke i" in f for f in fund), str(fund[:2]))

    # 4. Samme fejl, men skjult bag en `<strong>` midt i sætningen. Mutationen
    #    tilføjer taggen i *kilden* og lader citatet være uændret: porten skal
    #    stadig være grøn, fordi den læser den rensede tekst. Ellers ville den
    #    være rød på ethvert HTML-brudt citat, og en fejlrettelse ville se ud
    #    som en ny fejl.
    def med_strong(rod: Path) -> None:
        sti = rod / "site" / "scan.html"
        tekst = sti.read_text(encoding="utf-8")
        gammel = "<p>The report itself is free and needs no licence. A"
        assert gammel in tekst
        sti.write_text(tekst.replace(
            gammel,
            "<p>The report itself is <em>free</em> and needs no licence. A", 1),
            encoding="utf-8")

    fund = med(med_strong)
    tjek("en <em> i kilden gør ikke et rigtigt citat rødt",
         not any("står ikke i" in f for f in fund), str(fund[:2]))

    # 5. Et `where` helt uden linjereference.
    fund = med(lambda rod: _sæt_where(
        rod, "site/scan.html", "free_features", "basics",
        "site/scan.html scanneren kører i browseren"))
    tjek("`where` uden linjer er rød",
         any("intet `fil:linje`" in f for f in fund), str(fund[:2]))

    # 6. Den **andre** fil i henvisningen findes ikke. Mutationen rammer netop
    #    den, fordi `page-profile-pro`s lister slår den halve sætning med to
    #    filer, så porten skal dømme hver af dem — ellers ville den være grøn
    #    på en halvdel af sit eget katalogmateriale.
    fund = med(lambda rod: _sæt_where(
        rod, "site/scan.html", "free_features", "basics",
        "site/scan.html:251-255, håndhævet i site/ikke-findes.js:372-376"))
    tjek("en anden henvisning, der ikke findes, er rød",
         any("ikke findes i repoet" in f for f in fund), str(fund[:2]))

    # 7. Et interval, der løber baglæns.
    fund = med(lambda rod: _sæt_where(
        rod, "site/scan.html", "free_features", "basics",
        "site/scan.html:255-251"))
    tjek("interval der løber baglæns er rødt",
         any("baglæns" in f for f in fund), str(fund[:2]))

    # 8. Ratchet'en: en værktøjsside mister sin egen liste. Så ville dommen
    #    falde tilbage på produktets liste og blive grøn — altså ville præcis
    #    den løgn dom 6 i `check_pro_table.py` forbyder blive grøn her.
    def ratchet_uden_egne_liste(rod: Path) -> None:
        katfil = rod / "tools" / "stripe_catalog.json"
        kat = json.loads(katfil.read_text(encoding="utf-8"))
        for post in kat["pro_table_pages"]:
            if post["path"] == "site/scan.html":
                post.pop("free_features")
        katfil.write_text(json.dumps(kat, indent=2, ensure_ascii=False),
                         encoding="utf-8")

    fund = med(ratchet_uden_egne_liste)
    tjek("værktøjsside uden egen liste er rød",
         any("mangler egne free_features" in f for f in fund), str(fund[:2]))

    # 9. Mutation på **kilden**: en fil, der bliver slettet. Det er den fejl,
    #    hele porten findes for — `where` så rigtigt ud, indtil filen forsvandt.
    def slet_fil(rod: Path) -> None:
        (rod / "site" / "scan.html").unlink()

    fund = med(slet_fil)
    tjek("en slettet kildefil er rød",
         any("ikke findes i repoet" in f for f in fund), str(fund[:2]))

    for linje in fejl:
        print(f"  FEJL  {linje}")
    print(f"check-catalog-where-selftest: {'OK' if not fejl else 'RØD'} "
          f"({talt[0] - len(fejl)}/{talt[0]} kontroller)")
    return 1 if fejl else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true",
                        help="kør portens egen kontrol af sig selv")
    args = parser.parse_args(argv)
    if args.self_test:
        return self_test()
    noter: list[str] = []
    fund = dom(katalog(), noter=noter)
    for linje in fund:
        print(linje)
    if fund:
        print(f"\ncatalog-where: RØD — {len(fund)} fund")
        return 1
    if noter:
        print(f"note: {len(noter)} henvisninger peger ind i submoduler, der ikke er "
              f"udfyldt i dette checkout (format dømt, citat ikke):")
        for linje in noter:
            print(f"  {linje}")
    antal = 0
    kat = katalog()
    for post in kat["pro_table_pages"]:
        produkt = kat["products"][post["product"]]
        for felt in ("free_features", "pro_features"):
            antal += len(post.get(felt) or produkt.get(felt) or [])
    print(f"catalog-where: GRØN — {antal} funktioner i katalogens pro-table-sider "
          f"peger på en fil og ét eller flere linjeintervaller, og hvert citat "
          f"står i et af dem")
    return 0


if __name__ == "__main__":
    sys.exit(main())