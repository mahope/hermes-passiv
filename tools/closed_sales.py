"""Fælles opslag for produkter, der er lukket for salg.

Mads lukkede 22/11-2026 salget af Clean Copy Pro, DeskUptime Pro, Transmute
Desktop, EUComply Pro, EUComply-skabelonerne og e-bogspakken. Katalogen
(`tools/stripe_catalog.json`) beholder produkterne med `"status": "inactive"`,
fordi licens-API'et, /thanks, webhooken og leveringen stadig skal virke for
dem, der allerede har købt. Portene bruger dette modul til to ting:

1. `inactive_keys()` / `is_inactive()`: et lukket produkt må ikke kræves solgt
   noget sted — og `check_stripe_ctas.check_closed_sales` kræver det modsatte,
   at det ikke sælges.
2. `before_closure(relative)`: flere selftests beviste deres regel ved at
   mutere den *rigtige* publicerede tekst på Clean Copy-, DeskUptime- og
   EUComply-siderne. Den tekst findes ikke længere på siderne, så den ligger
   ordret i `tools/fixtures/for-lukning-2026-11-22/` (taget fra main før
   lukningen, commit 81359073). Reglerne bevises dermed stadig på rigtig
   publiceret tekst, ikke på en streng porten selv har fundet på.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "tools/stripe_catalog.json"
SNAPSHOT = ROOT / "tools/fixtures/for-lukning-2026-11-22"
CLOSED_DATE = "2026-11-22"


def load_catalog(path: Path = CATALOG) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def is_inactive(product: object) -> bool:
    return isinstance(product, dict) and product.get("status") == "inactive"


def inactive_keys(catalog: dict | None = None) -> set[str]:
    catalog = load_catalog() if catalog is None else catalog
    return {key for key, product in (catalog.get("products") or {}).items() if is_inactive(product)}


def before_closure(relative: str) -> str:
    """Den publicerede tekst for `relative` fra før salget lukkede."""
    path = SNAPSHOT / relative
    if not path.is_file():
        raise FileNotFoundError(
            f"{relative}: ingen kopi i {SNAPSHOT.relative_to(ROOT)} — "
            f"hent den med `git show 81359073:{relative}`")
    return path.read_text(encoding="utf-8")
