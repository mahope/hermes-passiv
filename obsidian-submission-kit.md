# Obsidian store-submission — klar til ét klik

Alt er bygget og klar. Den eneste manglende handling er at åbne selve
pull request'en, og det kan ikke ske via API:

**obsidianmd/obsidian-releases har begrænset PR-oprettelse til collaborators**
(GitHub returnerer "mahope does not have the correct permissions to execute
CreatePullRequest" på både REST og GraphQL — bekræftet 24/8 med frisk fork,
frisk gren og korrekt base). Web-UI'et kan stadig bruges af Mads.

## Det eneste der skal gøres (ca. 30 sekunder)

Åbn denne URL i browseren (logget ind som `mahope`) og klik "Create pull request":

https://github.com/obsidianmd/obsidian-releases/compare/master...mahope:obsidian-releases:add-clean-copy-obsidian?expand=1

Titel og body er allerede skrevet — indsæt fra blokkene herunder (eller lad
GitHub forslå commit-beskedens titel).

### Titel

```
Add Clean Copy: paste and clean text as proper Markdown
```

### Body

```
## Link to plugin repo
https://github.com/mahope/clean-copy-obsidian

## Plugin ID (must match manifest.json)
clean-copy-obsidian

## Description
Clean Copy lets you paste text into Obsidian as proper Markdown. It converts
clipboard HTML (bold, italic, headings, links, lists, tables, entities) to
Markdown on paste, strips tracking junk and inline styling, and supports custom
cleanup rules (Pro).

- Paste as Markdown from any source (web, docs, email)
- Clean-text mode and clean-selection command
- Command palette + configurable default behavior
- No network access; runs entirely locally

Note on naming: the store id is `clean-copy-obsidian` because another developer
uses the id `clean-copy` for a different plugin.

## Checklist
- [x] I have read the [Obsidian developer policies](https://docs.obsidian.md/Reference/Plugin+guidelines)
- [x] The plugin does not collect user data or use analytics
- [x] Releases are tagged with matching manifest.json version
```

## Hvad der ligger klar bagved (færdigt)

- Fork: https://github.com/mahope/obsidian-releases, gren
  `add-clean-copy-obsidian`, ét commit der tilføjer entry'en til
  `community-plugins.json` (id `clean-copy-obsidian`, author Mahope,
  repo `mahope/clean-copy`)
- Plugin-repo: https://github.com/mahope/clean-copy-obsidian
  (main.js, manifest.json, styles.css, versions.json, core.js, test.js,
  MIT-license, topics)
- Releases: tags `v1.0.1` OG `1.0.1`, begge med `main.js`, `manifest.json`,
  `styles.css` som assets (Obsidian kræver tag = manifest-version, derfor findes begge former)
- Tests: 14/14 grønne (`node test.js`)

## Efter godkendelse

Plugin'et dukker op i Obsidians community-liste. Så skal landingssiden
(hermes-passiv.pages.dev/clean-copy) have Obsidian-sektionen ændret fra
"manual install" til "install from community plugins" — det klarer jeg selv.
