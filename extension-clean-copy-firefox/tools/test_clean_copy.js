#!/usr/bin/env node
/**
 * Clean Copy — shared logic tests (run in Node, no browser needed).
 * Extracts cleanText/htmlToMarkdown from background.js by evaluating it
 * with a stubbed `browser` global.
 */
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const src = fs.readFileSync(path.join(__dirname, '..', 'background.js'), 'utf8');

// Stub browser/chrome globals so the module loads.
const sandbox = {
  console,
  navigator: { clipboard: { writeText: async () => {} } },
  document: {
    createElement: () => ({ style: {}, select: () => {}, remove: () => {} }),
    body: { appendChild: () => {}, removeChild: () => {} },
  },
  browser: {
    runtime: {
      lastError: null,
      onInstalled: { addListener: () => {} },
      onMessage: { addListener: () => {} },
      getURL: (p) => p,
      sendMessage: async () => {},
    },
    contextMenus: { create: () => {}, onClicked: { addListener: () => {} }, removeAll: () => {} },
    commands: { onCommand: { addListener: () => {} } },
    scripting: { executeScript: async () => [] },
    tabs: { query: async () => [] },
    storage: { local: { get: async () => ({}), set: async () => {} }, onChanged: { addListener: () => {} } },
  },
  chrome: {
    contextMenus: sandboxChromeMenus(),
    runtime: { lastError: null, onInstalled: { addListener: () => {} }, onMessage: { addListener: () => {} }, getURL: (p) => p, sendMessage: async () => {} },
    commands: { onCommand: { addListener: () => {} } },
    action: {},
    storage: { local: { get: async () => ({}), set: async () => {} }, onChanged: { addListener: () => {} } },
  },
};
function sandboxChromeMenus() {
  return { create: () => {}, removeAll: (cb) => cb && cb(), onClicked: { addListener: () => {} } };
}
vm.createContext(sandbox);
vm.runInContext(src, sandbox);

let pass = 0, fail = 0;
function t(name, actual, expected) {
  const ok = JSON.stringify(actual) === JSON.stringify(expected);
  if (ok) { pass++; } else { fail++; console.log(`FAIL ${name}\n  got: ${JSON.stringify(actual)}\n  exp: ${JSON.stringify(expected)}`); }
}

const { cleanText, htmlToMarkdown } = sandbox;

// cleanText
t('smart double quotes', cleanText('\u201Chello\u201D'), '"hello"');
t('smart single quotes', cleanText('\u2018a\u2019'), "'a'");
t('em dash', cleanText('a\u2014b'), 'a -- b');
t('en dash', cleanText('a\u2013b'), 'a - b');
t('zero-width chars removed', cleanText('a\u200Bb\uFEFFc'), 'abc');
t('nbsp to space', cleanText('a\u00A0b'), 'a b');
t('collapse spaces', cleanText('a   b'), 'a b');
t('collapse newlines', cleanText('a\n\n\n\nb'), 'a\n\nb');

// htmlToMarkdown
t('h1', htmlToMarkdown('<h1>Title</h1>'), '# Title');
t('h2', htmlToMarkdown('<h2>Sub</h2>'), '## Sub');
t('bold', htmlToMarkdown('<strong>hi</strong>'), '**hi**');
t('italic', htmlToMarkdown('<em>hi</em>'), '*hi*');
t('link', htmlToMarkdown('<a href="https://x.dk">X</a>'), '[X](https://x.dk)');
t('image', htmlToMarkdown('<img src="a.png" alt="A">'), '![A](a.png)');
t('code inline', htmlToMarkdown('<code>foo()</code>'), '`foo()`');
t('code block', htmlToMarkdown('<pre><code>let x = 1;\n&amp;&amp; true;</code></pre>'), '```\nlet x = 1;\n&& true;\n```');
t('list', htmlToMarkdown('<ul><li>one</li><li>two</li></ul>').trim(), '- one\n- two'.trim());
t('paragraphs', htmlToMarkdown('<p>a</p><p>b</p>'), 'a\n\nb');
t('br', htmlToMarkdown('a<br>b'), 'a\nb');
t('hr', htmlToMarkdown('<hr>'), '---');
t('entity decode', htmlToMarkdown('<p>A &amp; B &lt; C &gt; D &quot;E&quot; F&#39;s</p>'), 'A & B < C > D "E" F\'s');
t('strips unknown tags', htmlToMarkdown('<div class="ad">junk</div>'), 'junk');
// Nested list: sub-item indented two spaces (proper Markdown nesting).
t('nested list', htmlToMarkdown('<ul><li>a<ul><li>b</li></ul></li></ul>').trim(), '- a\n  - b');
// Deep nesting: three levels.
t('nested list 3', htmlToMarkdown('<ul><li>a<ul><li>b<ul><li>c</li></ul></li></ul></li></ul>').trim(), '- a\n  - b\n    - c');
// Ordered list.
t('ordered list', htmlToMarkdown('<ol><li>one</li><li>two</li></ol>').trim(), '1. one\n2. two');
t('invisible word joiners stripped', cleanText('Guard\u2060ian artic\u2062le'), 'Guardian article');

console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
