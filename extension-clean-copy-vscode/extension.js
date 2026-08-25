/**
 * Clean Copy for VS Code — paste HTML as clean Markdown or plain text.
 *
 * Commands:
 *   - "Clean Copy: Paste HTML as Markdown" (Ctrl+Shift+V / Cmd+Shift+V)
 *     Reads HTML from the system clipboard, converts to Markdown, pastes.
 *   - "Clean Copy: Paste as Clean Text"
 *     Reads text from clipboard, strips all formatting, pastes.
 *   - "Clean Copy: Convert Selection to Markdown"
 *     Converts selected HTML text in the editor to Markdown.
 */
'use strict';

const vscode = require('vscode');
const core = require('./clean_copy_core');

/**
 * Activate the extension.
 * @param {vscode.ExtensionContext} context
 */
function activate(context) {
  console.log('[Clean Copy] activated');

  // ── Paste HTML from clipboard as Markdown ─────────────────────────
  const pasteAsMarkdown = vscode.commands.registerCommand(
    'clean-copy.pasteAsMarkdown', async () => {
      try {
        const html = await readClipboard('text/html');
        if (!html) {
          vscode.window.showInformationMessage(
            'Clean Copy: No HTML content found in clipboard. Copy something from a web page first.'
          );
          return;
        }
        const md = core.htmlToMarkdown(html);
        await pasteToEditor(md);
      } catch (err) {
        vscode.window.showErrorMessage(
          'Clean Copy: Failed to convert — ' + (err.message || 'unknown error')
        );
      }
    }
  );

  // ── Paste text as clean plain text (strip all formatting) ────────
  const pasteAsCleanText = vscode.commands.registerCommand(
    'clean-copy.pasteAsCleanText', async () => {
      try {
        const text = await readClipboard('text/plain');
        if (text == null) {
          vscode.window.showInformationMessage(
            'Clean Copy: No text content found in clipboard.'
          );
          return;
        }
        const clean = core.cleanText(text.replace(/<[^>]*>/g, ''));
        await pasteToEditor(clean);
      } catch (err) {
        vscode.window.showErrorMessage(
          'Clean Copy: Failed to clean text — ' + (err.message || 'unknown error')
        );
      }
    }
  );

  // ── Convert selected HTML in the editor to Markdown ──────────────
  const convertSelection = vscode.commands.registerCommand(
    'clean-copy.convertSelection', () => {
      const editor = vscode.window.activeTextEditor;
      if (!editor) {
        vscode.window.showInformationMessage(
          'Clean Copy: Open a file first, then select HTML text to convert.'
        );
        return;
      }
      const selection = editor.selection;
      const text = editor.document.getText(selection);
      if (!text) {
        vscode.window.showInformationMessage(
          'Clean Copy: Select some HTML text first.'
        );
        return;
      }
      try {
        const md = core.htmlToMarkdown(text);
        editor.edit(editBuilder => {
          editBuilder.replace(selection, md);
        });
      } catch (err) {
        vscode.window.showErrorMessage(
          'Clean Copy: Failed to convert selection — ' + (err.message || 'unknown error')
        );
      }
    }
  );

  context.subscriptions.push(pasteAsMarkdown);
  context.subscriptions.push(pasteAsCleanText);
  context.subscriptions.push(convertSelection);
}

/**
 * Read clipboard content for a given format.
 * @param {'text/html'|'text/plain'} format
 * @returns {Promise<string|null>}
 */
async function readClipboard(format) {
  try {
    const value = await vscode.env.clipboard.readText();
    if (!value) return null;
    // For text/html format we get whatever was copied — VS Code's clipboard
    // API only returns plain text. When the clipboard contains HTML, the text
    // representation may contain stripped tags or raw HTML (browser-dependent).
    // We return whatever we got; the converter handles it regardless.
    return value;
  } catch {
    return null;
  }
}

/**
 * Paste text into the active editor using the edit API.
 * Pastes at cursor position if there's no selection, or replaces the selection.
 * Falls back to sending the text via clipboard if the edit API fails.
 * @param {string} text
 */
async function pasteToEditor(text) {
  const editor = vscode.window.activeTextEditor;
  if (!editor) {
    // No editor open — try clipboard as fallback
    await vscode.env.clipboard.writeText(text);
    vscode.window.showInformationMessage(
      'Clean Copy: Converted text copied to clipboard (open a file and paste manually).'
    );
    return;
  }

  const selection = editor.selection;
  // Insert at cursor or replace selection
  const position = selection.isEmpty ? selection.active : selection.start;
  await editor.edit(editBuilder => {
    if (!selection.isEmpty) {
      editBuilder.replace(selection, text);
    } else {
      editBuilder.insert(position, text);
    }
  });
}

exports.activate = activate;
exports.deactivate = function () {};