# Kodefejl i ugerapporten må aldrig blive "ukendt"

## Hvad der skete

`reports/weekly/2026-40.json` siger `ranking_basis: unknown` og
`traffic.available: false`, og filens egen `errors` indeholder
`api/stats: name 'count' is not defined`.

Det lyder som en netværksfejl. Det er det ikke. `tools/weekly_report.py:810`
skrev `{"file": file_name, "hits": count}` i en listeforståelse, hvis krop kun
evalueres når `top_downloads` ikke er tom. Fejlen lå i *én* returlinje og dræbte
hele `collect_stats`, fordi den ligger i det dict-literal der *er* svaret.
`soft()` fangede `NameError` og skrev den som en note, så læseren fik
`unknown_stats()` i stedet.

Resultatet er værre end en fejl: **arkivet siger om vores egen fejl, at den
kom fra en anden.** Uge 39s `The read operation timed out` er modsætningen — en
ægte forbigående fejl, der *skal* blive blød. En læser kan ikke skelne de to,
fordi begge står som en linje i `errors`.

## Reglen

**En rapport må aldrig skrive "ukendt" på baggrund af en fejl i vores egen kode.**

Det er en skelnen mellem to klasser, ikke en navneliste på fejl:

| Klasse | Eksempel |Hvad rapporten gør |
|---|---|---|
| **Kodefejl** | `NameError`, `AttributeError`, `TypeError`, `KeyError`, `SyntaxError`, `IndentationError` | Fejl i `weekly_report.py`. Må aldrig skrives som "ukendt". |
| **Forbigående** | `TimeoutError`, `URLError`, `HTTPError` 5xx/429, `ConnectionError` | Kilden svarer ikke. Blot noteret, `unknown` er det rigtige svar. |

Kodefejlene er de `Exception`-subklasser Python rejser, når *vi* skrev noget
forkert. De er derfor alle `SyntaxError`/`IndentationError` (indlæsningstid) og de
seks navngivne `NameError`/`AttributeError`/`TypeError`/`KeyError`. Resten —
alt der kan skyldes en adresse, et TLS-certifikat eller en server — er
forbigående, fordi et gentaget kalt kan virke næste gang.

## Hvorfor porten ikke kan bare se efter klassenavnet

Den første måling af denne opgave siger noget ubehageligt. Arkivfilen indeholder
`api/stats: name 'count' is not defined` — **uden ordet `NameError`**. Se
`note_error()` i `weekly_report.py:109`:

```python
msg = str(exc).strip() or exc.__class__.__name__
ERRORS.append(f"{source}: {msg[:200]}")
```

`str(NameError(...))` er `"name 'count' is not defined"`. Python skriver aldrig
klassenavnet i beskeden. **En port der matcher på `NameError` i arkivet ville
være grøn på præcis den fil, den blev skrevet til at fange.** Det er samme
fejlform som de fire forrige iterationer i denne familie: en læsning der ligner
browserens, men er en anden kode.

Derfor er rettelsen strukturel, ikke en søgning:

1. `note_error()` skriver klassenavnet **altid**:
   `f"{source}: {type(exc).__name__}: {msg}"`. Uden det er fejlen uaflæselig,
   og det er ikke en port der kan løse problemet. Kaldes `note_error` med en
   tekst og ikke en undtagelse — det gør den to steder — skrives klassenavnet
   som `Note`, så formatet er ens for alle linjer.
2. `check_weekly_code_errors.py` dømmer på **klassen, ikke på teksten**. En
   `errors`-linje med `NameError` i er en rapport, der blev skrevet af kode der
   var brudt. Det er derfor, porten kan fange bruddet fra uge 41 og frem uden at
   genskrive `weekly_report.py`'s logik.

**Hvad porten *ikke* gør, og hvorfor det er ærligt at sige det.** En tidligere
udkast af denne spec påstod, at porten "genberegner" fejlen ved at spørge om den
nuværende kode kan frembringe den. Det kan den ikke: en `NameError` i
`collect_stats` er ikke reproducerbar uden de data den døde på, og det ville
kræve `STATS_TOKEN` på workeren. Porten dømmer derfor på **hvad rapporten
selv siger**, og det er nok: den får netop den oplysning, der manglede i uge 40.
At *finde* fejlen i koden er `test_weekly_report.py`s opgave, ikke portens.

## Reglen for arkiverede filer — målt, ikke antaget

Porten dømmer filer fra og med `2026-41`. Det er ikke en vilkårlig grænse:

- `2026-40.json` indeholder **præcis** den fejl porten skal fange, i et format
  den ikke kan læse (se ovenfor). Filen kan ikke regenereres herfra: den kræver
  `STATS_TOKEN` på workeren.
- `2026-37` … `2026-39` er skrevet før bruddet og indeholder hverken
  `NameError` eller andre kodefejl — målet i `check_weekly_code_errors.py`
  bekræfter det, så de ville være grønne alligevel.

Så grænsen er ikke en hvidliste, der skjuler en fejl. Den er den ældste rapport
hvor den nye regel *kan* dømme noget, og den er skrevet som en konstant med en
begrundelse, så den kan slås fra den dag filen kan regenereres.

## Hvad porten dømmer

Fire kontroller:

1. `code_error_in_report`  en `errors`-linje i en dømt rapport har en klasse i
   `CODE_ERRORS`. Det er bruddet fra uge 40: `NameError` i `collect_stats` blev
   skrevet som "ukendt trafik" i stedet for som en fejl i vores egen kode.
2. `error_without_class`   en `errors`-linje i en dømt rapport mangler
   klassenavnet. Det er den anden ende af samme fejl: uden klassen kan ingen
   læse linjen, og så er den igen bare tekst.
3. `unknown_class`         en `errors`-linje hvis "klasse" ikke findes blandt de
   byggede undtagelser. Uden denne kontrol kan en skrivefejl få `Noteerror` til
   at ligne `NameError` — eller få porten til at tie om en virkelig kodefejl.
4. `bad_format`            en `errors`-linje der ikke kan læses som
   `source: Class: besked` overhovedet.

Kontrol 3 og 4 er ikke pænhed: de er forudsætningen for at 1 og 2 overhovedet
kan regnes, og uden dem ville porten være grøn på en linje den ikke forstår.

Alle fire har **positive kontroller** i `--self-test`: en syntetisk rapport med en
`NameError` skal give rødt, en uden klassenavn skal give rødt, en med opfundet
klassenavn skal give rødt, og den rigtige kode skal være grøn. Uden dem er
`--self-test` tomt i et arkiv hvor alt er i orden — det er den fejl de tre
sidste selftests i familien allerede har fundet.

## Hvad porten bevidst ikke dømmer

- **At trafikken virker.** Kan kun ses i næste rapport, fordi fejlen lå i
  `weekly_report.py`, der kører på workerens tidsplan, ikke i `site/_worker.js`.
- **`soft()` der skelner mellem kodefejl og forbigående.** Det er den dybere
  rettelse (NEXT_TASK 3 i planen) og den ændrer tekst i fire arkiverede rapporter,
  så den er en port-opgave, ikke en diff. Porten her gør den synlig uden at
  gøre den.
- **Uge 39s timeout.** Det er den korrekte repræsentation af en tabt kilde, ikke
  en fejl. `check_weekly_history.py`'s docstring siger hvorfor, og det er ikke
  vores at ændre her.
