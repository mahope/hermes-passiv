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
