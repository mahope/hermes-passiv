from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
INVENTORY_PATH = ROOT / "tools" / "route_inventory.json"


def load_inventory(path: Path = INVENTORY_PATH) -> dict[str, tuple[str, ...]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("route inventory must be an object")
    inventory: dict[str, tuple[str, ...]] = {}
    for domain, routes in data.items():
        if not isinstance(domain, str) or not isinstance(routes, list) or not routes:
            raise ValueError(f"invalid route inventory entry for {domain!r}")
        if len(routes) != len(set(routes)):
            raise ValueError(f"duplicate route in inventory for {domain}")
        for route in routes:
            parsed = urlparse(route)
            if not isinstance(route, str) or parsed.scheme or parsed.netloc or parsed.query or parsed.fragment or not route.startswith("/"):
                raise ValueError(f"invalid route in inventory for {domain}: {route!r}")
        inventory[domain] = tuple(routes)
    return inventory


def expected_urls(domain: str, inventory: dict[str, tuple[str, ...]] | None = None) -> set[str]:
    routes = (inventory or load_inventory()).get(domain)
    if routes is None:
        raise ValueError(f"no route inventory for {domain}")
    return {f"https://{domain}{route}" for route in routes}
