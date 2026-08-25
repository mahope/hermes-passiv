# Clean Copy for VS Code

Paste HTML as clean Markdown directly into your editor — no more messy web-page copies with rogue formatting, invisible characters, or junk markup.

Same converter engine as the [Clean Copy Chrome/Firefox extension](https://hermes-passiv.pages.dev/clean-copy).

## Features

- **Paste HTML as Markdown** (`Ctrl+Shift+V` / `Cmd+Shift+V`) — copy from a web page, then paste as clean Markdown into your document
- **Paste as Clean Text** — strip all HTML tags and invisible characters, paste as plain text
- **Convert Selection to Markdown** — select HTML in your editor and convert it in-place

## Usage

1. Copy content from a web page (or any HTML source)
2. In VS Code, press `Ctrl+Shift+V` (Windows/Linux) or `Cmd+Shift+V` (macOS)
3. The HTML is converted to clean Markdown and pasted at your cursor

Or use the Command Palette (`Ctrl+Shift+P` / `Cmd+Shift+P`) and search for:
- `Clean Copy: Paste HTML as Markdown`
- `Clean Copy: Paste as Clean Text`
- `Clean Copy: Convert Selection to Markdown`

## What gets cleaned

| Issue | Handled |
|-------|---------|
| Smart quotes → straight quotes | ✅ |
| Zero-width / invisible characters | ✅ |
| Non-breaking spaces → regular | ✅ |
| Script/style tags stripped | ✅ |
| Links rendered as `[text](url)` | ✅ |
| Images rendered as `![alt](src)` | ✅ |
| Tables → Markdown tables | ✅ |
| Nested lists | ✅ |
| Code blocks with language | ✅ |
| Blockquotes | ✅ |
| Definition lists | ✅ |

## Pro Features (coming)

When payment infrastructure is available:
- Custom find/replace rules
- Batch conversion
- Regex-based cleanup

## Installation

### From VS Code Marketplace (recommended, once published)

1. Open VS Code
2. Go to Extensions (`Ctrl+Shift+X`)
3. Search for "Clean Copy"
4. Click **Install**

### From VSIX

1. Download the latest `.vsix` from [releases](https://github.com/mahope/clean-copy-vscode/releases)
2. In VS Code: Extensions → `...` → **Install from VSIX...**

## Development

```bash
git clone https://github.com/mahope/clean-copy-vscode
cd clean-copy-vscode
npm install
code .
# Press F5 to start debugging
```

### Run tests

```bash
npm test
```

## License

MIT — see [LICENSE](LICENSE).

---

_Built on the same converter core as the [Clean Copy](https://hermes-passiv.pages.dev/clean-copy) browser extension._