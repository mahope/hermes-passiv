#!/bin/zsh
# passiv-loop.sh v3 — bryder soege-loekken: foerste runde koeres HELT uden web_search,
# saa agenten tvinges til at taenke og skrive ned foer den maa validere.
export PATH="$HOME/.local/bin:$PATH"
# EGEN Hermes-installation: egne sessions og hukommelse, saa de to agenter
# ikke laeser hinandens arbejde (de blandede sig sammen 23/8)
export HERMES_HOME="$HOME/.hermes-passiv"
DIR="$HOME/hermes-passiv"
# hver agent maa KUN skrive i sin egen mappe
export HERMES_WRITE_SAFE_ROOT="$DIR"
LOG="$DIR/passiv.log"
cd "$DIR" || exit 1
MAX=${1:-15}

FAELLES='Graenser: budget 1000 DKK (poster under 150 kr maa du selv afholde og skrive i BUDGET.md, resten spoerg Mads). Ingen udadvendte handlinger i Mads navn. Intet ulovligt eller naer kanten. Roer kun denne mappe.
Opdater ALTID STATUS.md til sidst - ogsaa hvis det gik daarligt: hvad proevede du, hvad virkede ikke, hvad skal naeste iteration goere anderledes.'

for i in $(seq 1 $MAX); do
  [ -f "$DIR/STOP" ] && { echo "$(date -Iseconds) STOP-fil - slutter" >> "$LOG"; break; }

  vent=0
  while true; do
    st=$("$HOME/hermes-ceo/kvote-tjek.sh")
    [ "$st" = "OK" ] && break
    if [ "$st" = "DAGSKVOTE" ]; then
      echo "$(date -Iseconds) egen dagskvote opbrugt - stopper for i dag" >> "$LOG"; exit 0
    fi
    vent=$((vent+1))
    [ "$vent" -gt 24 ] && { echo "$(date -Iseconds) modellen utilgaengelig i 2t ($st) - stopper" >> "$LOG"; exit 0; }
    echo "$(date -Iseconds) $st - venter 5 min (forsoeg $vent/24)" >> "$LOG"
    sleep 300
  done

  if [ ! -f "$DIR/RESEARCH.md" ]; then
    # --- FASE 0: ingen soegning overhovedet ---
    echo "$(date -Iseconds) === iteration $i/$MAX (fase 0: UDEN soegning) ===" >> "$LOG"
    OPGAVE="Du er stifter.

NYE RAMMER FRA MADS (23. august) - se AGENTS.md for detaljerne:
1. UNIVERSELT: alt du bygger skal virke paa andet end WordPress. Kernen skal tage en almindelig URL og fungere uanset CMS. Platform-integrationer er indpakninger, ikke selve produktet.
2. FLERE PRODUKTER: du maa gerne bygge en lille portefoelje. Men goer ÉT faerdigt (virker, udgivet, kan tage imod penge) foer du starter det naeste.
3. IKKE KUN HJEMMESIDER: desktop-programmer (Tauri/Electron med licensnoegle), CLI-vaerktoejer (npm/pip/brew), browser-udvidelser, udvidelser til VS Code/Figma/Obsidian/Shopify/Raycast, API'er, eller digitale produkter paa en markedsplads med indbygget betaling - alt taeller. Vaelg efter hvad der giver penge hurtigst, ikke hvad der er nemmest at bygge.
4. MARKETING OG DRIFT er ogsaa dit ansvar - Mads hjaelper kun med opsaetning. Du staar selv for indhold, SEO, produkttekster, priser, vilkaar og selvbetjent support paa dine EGNE flader, uden at spoerge. Men alt der rammer et andet menneske direkte i hans navn (kolde mails, DM, opslag i grupper, kommentarer, betalte annoncer) skriver du faerdigt og lader vente paa hans ja - notér det i STATUS.md.
5. BLIV VED MED AT FORBEDRE: et produkt er aldrig faerdigt. Er du blokeret paa Mads konti, saa stop IKKE - forbedr det du har, eller byg det naeste der ikke er blokeret. Ventetid er arbejdstid. Prioritér i denne raekkefoelge: det der staar mellem besoegende og betaling, selve produktet, det der traekker folk til, og til sidst bredden.

Foerste opgave i denne iteration: vurdér aerligt om det du har opfylder punkt 1. Er det bundet til én platform, saa traek kernen ud og behold det du har bygget som ÉN indpakning. Smid ikke arbejde vaek - byg det om. Skriv vurderingen i STATUS.md.

 Laes AGENTS.md - dit mandat.

I DENNE ITERATION MAA DU IKKE BRUGE web_search. Overhovedet. Ikke én gang.
Grunden: du er tidligere gaaet i staa ved at gentage den samme soegning 50 gange. Denne runde handler om at taenke, ikke om at slaa op.

Din opgave, udelukkende ud fra det du allerede ved:

1. Skriv MINDST 15 konkrete kandidater til en indtaegt der koerer uden Mads' indsats. Vaer specifik - ikke 'saelg et digitalt produkt', men hvad for et, til hvem, og hvor det saelges.
2. For hver kandidat: svar kort paa tre ting - (a) hvem betaler og hvor meget, (b) hvad skal et menneske goere hver maaned for at holde det koerende (svaret skal helst vaere 'ingenting'), (c) hvad er den mest sandsynlige grund til at den fejler.
3. Streg dem ud der dumper tre-maaneders-testen. Vaer haard.
4. Vaelg de 5 bedste og ranger dem.
5. Skriv det HELE i RESEARCH.md. Skriv ogsaa praecis hvilke fakta du er usikker paa og gerne vil tjekke i naeste iteration - dem slaar du op saa, ikke nu.

$FAELLES"
  else
    # --- normale iterationer: soegning tilladt, men med skarp disciplin ---
    echo "$(date -Iseconds) === iteration $i/$MAX ===" >> "$LOG"
    OPGAVE="Du er stifter. Laes AGENTS.md, RESEARCH.md og de oevrige filer.

SOEGE-DISCIPLIN (vigtigt - du er gaaet i staa paa dette foer):
- Hoejst 12 soegninger i hele denne iteration. Taeller du op til 12, saa stop med at soege og arbejd videre med det du har.
- Gentag ALDRIG en soegning du allerede har lavet. Giver den intet brugbart, saa noter det og gaa videre.
- Soeg kun for at tjekke konkrete fakta: findes produktet allerede, hvad koster det, hvad tager platformen i gebyr. Soeg ikke efter inspiration.

Vaelg selv hvad der er rigtigt nu:
A) Har du ingen DECISION.md: tjek de usikre fakta fra RESEARCH.md, opdater den, og traef saa et valg. Ubeslutsomhed koster mere end et middelmaadigt valg.
B) Har du DECISION.md: BYG. Rigtig kode, rigtige filer, og saa det passer paa sig selv - fejl skal haandteres automatisk, ikke rapporteres til Mads.

$FAELLES"
  fi

  perl -e 'alarm shift; exec @ARGV' 5400 hermes --in "$DIR" -z "$OPGAVE" >> "$LOG" 2>&1
  echo "$(date -Iseconds) iteration $i afsluttet (exit $?)" >> "$LOG"
  sleep 20
done
echo "$(date -Iseconds) passiv-loop afsluttet" >> "$LOG"
