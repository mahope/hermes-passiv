#!/usr/bin/env python3
"""Add internal links to /blog/html-to-markdown-cli (CLI guide) from related
Clean Copy blog posts that don't yet link to it. Idempotent: skips posts
already linking to the target."""
import re, sys, pathlib

BLOG = pathlib.Path(__file__).resolve().parent.parent / "site" / "blog"
TARGET = "/blog/html-to-markdown-cli"

# post slug -> (anchor text, context sentence)
LINKS = {
    "copy-as-markdown-chrome-extension": (
        "HTML to Markdown from the terminal",
        "Working in a shell instead of the browser? The CLI guide covers npx one-liners and batch conversion."),
    "paste-without-formatting-chrome": (
        "HTML to Markdown from the terminal",
        "Need the same clean Markdown in your editor? Convert pages from the terminal with the CLI."),
    "copy-clean-text-from-website": (
        "HTML to Markdown from the terminal",
        "Prefer the command line? The CLI guide shows how to convert any URL to Markdown with one npx command."),
    "paste-into-obsidian-clean-markdown": (
        "HTML to Markdown from the terminal",
        "Power users: fetch and convert pages straight into your vault via the terminal using the Clean Copy CLI."),
    "building-html-to-markdown-converter": (
        "the complete terminal guide",
        "See it used end-to-end in the terminal guide for the Clean Copy CLI."),
    "table-alignment-html-to-markdown": (
        "CLI guide",
        "Table alignment works in the CLI too — see the terminal guide for examples."),
    "developer-text-tools": (
        "HTML to Markdown from the terminal",
        "One of the tools developers reach for most: convert HTML to Markdown straight from the CLI."),
    "html-to-markdown-converter": (
        "terminal version of this converter",
        "The same engine also runs as an npm CLI."),
    "html-to-markdown-vscode": (
        "CLI version",
        "Not in VS Code? The CLI brings the same conversion to any terminal."),
    "url-to-markdown-converter": (
        "terminal workflow for this",
        "Scriptable, batch-friendly URL-to-Markdown via npx — no browser needed."),
    "copy-from-chatgpt-into-word": (
        "Convert web pages to Markdown from the terminal",
        "For developers who live in the shell."),
}

def add_link(slug, text, sentence):
    p = BLOG / f"{slug}.html"
    html = p.read_text(encoding="utf-8")
    if TARGET in html:
        return "skip (already links)"
    link_html = f'<p style="margin-top:16px;"><strong>Related:</strong> <a href="{TARGET}" style="color:var(--color-accent);">{text}</a> — {sentence}</p>'
    # Insert before closing </main> if present, else before </body>
    if "</main>" in html:
        html = html.replace("</main>", link_html + "\n\n</main>", 1)
    else:
        html = html.replace("</body>", link_html + "\n</body>", 1)
    p.write_text(html, encoding="utf-8")
    return "added"

def main():
    counts = {"added": 0, "skip (already links)": 0, "missing file": 0}
    for slug, (text, sentence) in LINKS.items():
        p = BLOG / f"{slug}.html"
        if not p.exists():
            print(f"{slug}: MISSING FILE")
            counts["missing file"] += 1
            continue
        res = add_link(slug, text, sentence)
        if res is None:
            res = "added (before body)"
            counts["added"] += 1
        elif res == "added":
            counts["added"] += 1
        else:
            counts[res] += 1
        print(f"{slug}: {res}")
    print(counts)
    # verify every page now links
    bad = [s for s in LINKS if TARGET not in (BLOG / f"{s}.html").read_text(encoding="utf-8")]
    if bad:
        print("STILL MISSING:", bad); sys.exit(1)
    print("OK: all target posts link to", TARGET)

if __name__ == "__main__":
    main()
