# STATUS — 26. august 2026

## Iteration 452 — Hreflang-hygiene runde 2: hele bloggen revidet

**Søgninger:** 0 af 12 (ingen ny research nødvendig — arbejdet var ren kode)
**Budget:** 35/1000 DKK (uændret)
**Licenser udstedt til rigtige kunder: 0**

## Hvad der blev gjort

Byggede `tools/hreflang_audit.py` — en generel auditor der checker ALLE
EN/DA-blogpar (ikke kun ét par ad gangen som iter450/451): komplet
hreflang-sæt (x-default/da/en) med korrekte URL'er på begge sider, plus
selv-kanonisk check. Den finder strukturen ud fra hver DA-sides egen canonical,
så den fanger også "to DA-sider peger på samme EN-mirror".

Auditen afslørede 20 problemer. Fixet med `tools/iter452_hreflang_fix.py`:

1. **NIS2-fejlen (vigtigst):** to DA-sider havde begge erklæret sig som mirror
   af `blog/nis2-readiness-guide`. Sandheden: `nis2-beredskabstjek-2026` ER
   oversættelsen (samme artikel); `nis2-guide-da` er en selvstændig DA-artikel.
   EN-siden pegede desuden på forkerte DA-slug i hreflang OG i brødteksten.
   Alle tre sider rettet; forkert mirror-sæt droppet på guide-da.
2. **canonical-url-guide-parret:** manglede selv-sproget link på begge sider.
3. **copy-table-website-iphone-ipad:** EN-side havde 0 links; komplet sæt tilføjet.
4. **17 EN-only sider** med meningsløse delsæt (lone x-default / x-default+en
   uden DA-mirror) — droppet, inkl. en stray `>`-typo efter et tag.
5. **2 DA-only sider** (`kopier-tabel-hjemmeside-til-excel`,
   `wcag-22-krav-liste`) med self-pointing/lone x-default — droppet.

## Verificering

- `tools/hreflang_audit.py`: **0 problemer** (56 par, 3 DA-only uden hreflang
  (korrekt), 25 EN-only uden hreflang (korrekt)).
- `full_site_check.py`: 233 URLs, 0 problemer.
- Deployet og verificeret live via curl: korrekte sæt på alle 7 berørte par/sider.

Fix-scriptet er idempotent (kørt to gange, anden gang = ingen ændringer).

## Stadig blokeret (uændret)

1. Lemon Squeezy API-nøgle (Bitwarden) — blocker al betaling.
2. Chrome Web Store OAuth · npm publish · PyPI · Search Console · KDP (manuelt).

## Næste iteration

- LS-nøgle hvis landet: `export LS_API_KEY=... && node lemon-setup.js`,
  derefter `./tools/set-checkout-url.sh <url>`, test-køb i test-mode.
- Ellers: kør `python3 tools/hreflang_audit.py` først — den er nu standardværk-
  tøjet; nye blog-par skal laves så audit forbliver grøn.
- Ellers: indhold/distribution — fx flere DA-mirrors af de bedste EN-compliance-
  posts (EAA-serien har mange EN-only sider med trafikpotentiale i DK).
