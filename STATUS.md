# STATUS — Iteration 425: deskuptime curl-installer + runner-fejl fundet og rettet

## Søgedisciplin
0 websøgninger. Alt arbejde er bygge-/verifikationsarbejde.

## 1. DeskUptime curl-installer — verificeret end-to-end (næste-skridt 1 fra iter 424)
- Ny `tools/make_tarball.sh` i deskuptime-repoet: deterministisk tarball
  (`deskuptime-0.1.2.tar.gz`) med self-checks (version-match + rigtig live
  check mod example.com inden den godkendes).
- Ny `tools/install.sh`: `curl -fsSL https://raw.githubusercontent.com/mahope/deskuptime/main/tools/install.sh | bash`
  installerer til ~/.local/bin.
- **Første version fejlede** (404: releaset hedder v0.1.2-cli, ikke v0.1.2) —
  fanget af min egen e2e-test på ren HOME, rettet, pushet.
- **Slutverificering:** rå GitHub-URL → download → install → `check
  https://example.com` → 200 OK + SSL-dage. Kører på ren HOME-mappe.

## 2. GitHub Actions bevist brugbare af en fremmed (næste-skridt 2 fra iter 424)
Lavede et engangs-repo med workflows der bruger begge actions via tags:
- `mahope/compliance-site-check@v2.0.0` — virkede første forsøg (score-rapport).
- `mahope/bugbottle-action@v1.0.1` — **FEJLEDE på rigtige runners**, selvom
  lokale tests var grønne.

**Rigtig fejl fundet:** nyere GitHub-runners eksponerer action-inputs som
`INPUT_REPORTS-GLOB` (bindestreg bevaret) i stedet for `INPUT_REPORTS_GLOB`.
Dokumentationen siger underscore-formen — det var derfor ingen havde opdaget det.
Rettet så begge former accepteres, tagget **v1.0.2** + release, og bekræftet med
nyt fremmed-repo-run: **alle steps grønne**. Test-repoet er slettet igen.

Uden denne iteration havde den første rigtige bruger af bugbottle-action fået en
action der aldrig kunne køre.

## 3. Site (næste-skridt 3 fra iter 424)
free-tools.html har nu den verificerede brew-kommando direkte under DeskUptime.
Deployet og verificeret med curl (streng findes på live-siden).

## Trafik/brug (uændret, ærlige tal)
Ingen nye rigtige brugere. 0 tilmeldinger.

## Stadig blokeret på Mads (uændret)
1. npm publish (bugbottle + deskuptime)
2. Lemon Squeezy-nøgle (Bitwarden)
3. Google Search Console-verifikation (DNS-post)
4. GitHub Marketplace = ét klik (BUILD.md)

## Næste iteration
1. DeskUptime README: tilføj curl-install-linjen ved siden af brew/npx.
2. Samme runner-input-audit for compliance-site-check (bruger den INPUT_-vars?
   dens scan virkede, men tjek om outputs/options også rammer dash-problemet).
3. Overvej Homebrew-formler der peger på tarballs i stedet for repo-checkouts,
   så install bliver hurtigere og sha-verificerbar.

---

# Iteration 426 — 26. august 2026

## 1. compliance-site-check: runner-input-fejl fundet og fikset (næste-skridt 2 fra iter 425)
Samme fejl som bugbottle: nye runners eksponerer inputs som `INPUT_FAIL-ON-MISSING`
(bindestreg bevaret), ikke `INPUT_FAIL_ON_MISSING`. `gaGetInput` accepterer nu
begge former. Testet lokalt med begge env-var-former (dash-form læst korrekt,
fail-on-missing gav exit=1 som forventet).

Udgivet som **v2.0.1** og verificeret end-to-end på et engangs-repo på rigtige
GitHub-runners: alle steps grønne, score-output kom ud. Test-repoet er slettet.

## 2. DeskUptime README: curl-install-linje tilføjet (næste-skridt 1 fra iter 425)
`curl -fsSL .../tools/install.sh | bash` står nu ved siden af brew/npx i
README.md. Pushet.

## 3. Homebrew-formel peger nu på release-tarball (næste-skridt 3 fra iter 425)
`mahope/homebrew-tap/Formula/deskuptime.rb` henter nu
`releases/download/v0.1.2-cli/deskuptime-0.1.2.tar.gz` med sha256 i stedet for
repo-checkout (hurtigere install, sha-verificerbar). Verificeret med lokal
tarball-udpakning + `brew reinstall`: CLI'en kører og checker example.com OK.

## Søgninger
0 af 12 brugt — ingen søgning var nødvendig; alt arbejde var verificerbart via
git/gh/brew lokalt.

## Trafik/brug (uændret, ærlige tal)
Ingen nye rigtige brugere. 0 tilmeldinger.

## Stadig blokeret på Mads (uændret)
1. npm publish (bugbottle + deskuptime)
2. Lemon Squeezy-nøgle (Bitwarden)
3. Google Search Console-verifikation (DNS-post)
4. GitHub Marketplace = ét klik (BUILD.md)

## Næste iteration
1. DeskUptime v0.1.3-release når watch-mode/content-fixes lander — så skal både
   tap-sha og install.sh VERSION opdateres samtidigt (skriv en tjekliste i
   BUILD.md).
2. Overvej en GitHub Action "release.yml" der auto-opdaterer tap-sha ved tag —
   fjerner manuel sha-synkronisering som fejlkilde.
3. clean-copy-cli: samme tarball-baserede formel er allerede på plads; tjek at
   dens CI verify-tarball stadig matcher v1.5.0.
