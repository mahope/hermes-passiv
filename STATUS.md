# STATUS — faktisk oversigt

> Dette er en **historisk og faktuel** oversigt, ikke en arbejdskø.
> Den operative state — hvad der er i gang, og hvad der er næste opgave —
> ligger i `IMPLEMENTATION_PLAN.md`. Denne fil opdateres, når der sker noget
> der ændrer et *faktum* (et udgivet produkt, en live-adresse, et tal).

**Sidst opdateret:** 25. september 2026

## Hvad der er live

| Site | Rolle |
|---|---|
| `mahope.tools` | Værktøjer, e-bøger, licensserver, Stripe-levering |
| `cleancopy.tools` | Clean Copy (udvidelser, Obsidian-plugin, CLI) |
| `deskuptime.com` | DeskUptime (desktop, CLI, URL-værktøjer) |
| `bugbottle.dev` | Fejlrapportering — separat kodebase (`mahope/bugbottle`) |

Udgivelse sker ved push til `main` gennem GitHub Actions
(`.github/workflows/deploy-sites.yml`). Der er ingen manuel upload.

## Betaling

Al salg går gennom **Stripe** (kontoen Mahope.dk). Lemon Squeezy blev afvist og
er lukket; Gumroad er droppet. Betalingslinks og licens-API står i
`docs/stripe-kontrakt.md`. Nøglerne ligger i Bitwarden og i den workerens
hemmeligheder — aldrig i kode, i en side eller i et repo.

## Færdige produkter

- **Clean Copy** — Chrome 1.5.3, Firefox 1.5.3, Obsidian 1.0.10. Pro: $19/år.
- **DeskUptime** — desktop 1.3.3, CLI. Pro: $19 engang, 3 maskiner.
- **EAA Compliance Scanner** — npm 1.2.0, Python 1.2.0. Desktop 1.3.3.
- **Page Profile** — 1.2.0. Pro: $19/år.
- **Site Icons** — 1.0.0.
- **Betalte e-bøger og skabeloner** — leveres via Cloudflare KV efter køb.

Versionsnumrene er single-sourced i hvert produkts egen fil og kontrolleres af
`python3 tools/check_versions.py`.

## Ærlige tal

Der er dokumenteret **0 betalinger** i dette repo. Det er ikke et bevis for at
salget er nul, kun at intet kan tælles herfra.

## Vænt på Mads

- Tilføj domænerne i Google Search Console.
- Opret betalt indhold i KV, så et køb kan levere (7 filer mangler).
- Beslut om historik-remediering for tidligere publiceret betalt indhold.

Den fulde liste står under `❓ Til Mads` i `IMPLEMENTATION_PLAN.md`.

## Historik

Rapporterne fra de tidlige iterationer ligger i `RAPPORT-2026-08-26.md`. De
beskriver en tid, hvor betalingen var Lemon Squeezy, og de er ikke opdateret —
de er arkiv.
