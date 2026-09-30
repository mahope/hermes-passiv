#!/usr/bin/env python3
"""Det ene sted, der afgør hvad der må prøves igen.

Opgave 32. `weekly_report.py:188` løste uge 39s timeout med sin egen
`_transient` 21/9, og `ceo/live-check-flake` skrev 30/9 en anden til
`check_live_sitemaps.py` fordi de to scripts ikke delte kode. De to var
**uenige om 429**: `check_live_sitemaps` prøvede den ikke igen, `weekly_report`
prøvede den igen. Det er ikke en skønhedsfejl — de to porte dømmer hver sit
udgivelsesbillede, så den samme udgivelse kunne være «brudt» i den ene og
«sund» i den anden.

Kontrakten afgør det: **429 er endelig.** Ikke fordi den er et svar, men fordi
et forsøg mere ikke løser noget — det koster kun kvoten for den der spørger.
Samme regel for 404 og 403, og de er også et svar, der ikke bliver bedre af at
blive bedt om igen. Kun **netværksfejl og 5xx** er forbigående: dem ved vi ikke
hvad de er, og de koster intet at spørge om igen.

Formen er valgt, så de to kaldsteder *eller hinanden*:

- `is_transient(503)` og `is_transient(429, None)` — som `check_live_sitemaps`
  kalder det, hvor `fetch` har lavet et svar til `(status, krop, headers, fejl)`.
- `is_transient(error=exc)` — som `weekly_report` kalder det, hvor `urlopen`
  kaster i stedet for at svare.

En `HTTPError` er *både* en undtagelse og et svar (den arver fra `URLError`), så
den dømmes på sin kode, ellers ville alle 4xx se ud som netværksfejl. En
`OSError` der ikke er en `HTTPError` er derimod aldrig et svar, kun en
forbindelse der ikke kom igennem.

    python3 tools/test_transient.py
"""
from __future__ import annotations

import urllib.error

# `urllib.error.URLError`, `TimeoutError` og `ConnectionError` er alle
# `OSError`-subklasser, så de er dækket — de står eksplicit, fordi det er dem
# de to scripts faktisk ser, og fordi `OSError` alene skjuler hvorfor.
NETWORK_ERRORS = (urllib.error.URLError, TimeoutError, ConnectionError, OSError)


def is_transient(status: int | None = None, error: BaseException | str | None = None) -> bool:
    """Må der prøves igen? Kun et netværksproblem eller en 5xx.

    `status` er HTTP-koden når kaldet svarede, `error` er enten en undtagelse
    fra `urlopen` eller en fejltekst fra et `fetch` der aldrig fik et svar.
    Begge er valgfrie, fordi de to kaldsteder kun har det ene.
    """
    if isinstance(error, urllib.error.HTTPError):
        # Et svar, ikke en fejl der går over: døm på koden. `error` nulstilles,
        # så den ikke tæller som netværksfejl nedenfor.
        status = error.code
        error = None
    if isinstance(error, BaseException):
        # En kodefejl eller et ubrugeligt svar (rå JSON, der ikke parse) er ikke
        # forbigående: et forsøg mere ville give samme svar.
        return isinstance(error, NETWORK_ERRORS)
    if status is not None:
        # Når der *er* et svar, er det svaret der afgør — også hvis en fejltekst
        # skulle være fulgt med. Kun en 5xx er forbigående; en 4xx er endelig,
        # også 429, fordi et forsøg mere ikke læser noget ind men kun trækker
        # kvoten for den der spørger.
        return status >= 500
    # Ingen kode: så kom der intet svar. Det er præcis definitionen på forbigående.
    return error is not None
