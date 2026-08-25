/**
 * Clean Copy VS Code extension — unit tests.
 * Run with: npx vscode-test or via VS Code's test runner.
 * These tests verify the core converter works as expected in the Node context.
 */
'use strict';

const assert = require('assert');
const core = require('../clean_copy_core');

describe('Clean Copy Core', function () {

  describe('htmlToMarkdown', function () {
    it('converts simple HTML to Markdown', function () {
      assert.strictEqual(
        core.htmlToMarkdown('<h1>Hello</h1><p>World</p>'),
        '# Hello\n\nWorld'
      );
    });

    it('converts links', function () {
      assert.strictEqual(
        core.htmlToMarkdown('<a href="https://example.com">Example</a>'),
        '[Example](https://example.com)'
      );
    });

    it('converts images', function () {
      assert.strictEqual(
        core.htmlToMarkdown('<img src="img.png" alt="Logo">'),
        '![Logo](img.png)'
      );
    });

    it('strips script tags', function () {
      const result = core.htmlToMarkdown('<p>Hello</p><script>alert("xss")</script>');
      assert.ok(result.includes('Hello'));
      assert.ok(!result.includes('alert'));
    });

    it('converts code blocks', function () {
      const result = core.htmlToMarkdown('<pre><code>const x = 1;</code></pre>');
      assert.ok(result.includes('```'));
      assert.ok(result.includes('const x = 1;'));
    });

    it('handles tables', function () {
      const html = '<table><tr><th>Name</th><th>Age</th></tr><tr><td>Alice</td><td>30</td></tr></table>';
      const result = core.htmlToMarkdown(html);
      assert.ok(result.includes('Name'));
      assert.ok(result.includes('Alice'));
      assert.ok(result.includes('| ---'));
    });

    it('handles empty input', function () {
      assert.strictEqual(core.htmlToMarkdown(''), '');
    });

    it('strips invisible characters', function () {
      const result = core.htmlToMarkdown('<p>Hello\u00A0World</p>');
      assert.ok(result.includes('Hello World'));
    });
  });

  describe('cleanText', function () {
    it('collapses multiple spaces', function () {
      const result = core.cleanText('Hello    World');
      assert.strictEqual(result, 'Hello World');
    });

    it('strips BOM and zero-width chars', function () {
      const result = core.cleanText('\uFEFFHello\u200BWorld');
      assert.strictEqual(result, 'HelloWorld');
    });

    it('normalizes smart quotes', function () {
      const result = core.cleanText('\u201CHello\u201D');
      assert.strictEqual(result, '"Hello"');
    });

    it('trims whitespace', function () {
      assert.strictEqual(core.cleanText('  hello  '), 'hello');
    });
  });

  describe('compileRules / applyRules (Pro)', function () {
    it('compiles and applies string replacement rules', function () {
      const rules = core.compileRules([
        { find: 'foo', replace: 'bar' }
      ]);
      const result = core.applyRules('foo and foo', rules);
      assert.strictEqual(result, 'bar and bar');
    });

    it('compiles and applies regex rules', function () {
      const rules = core.compileRules([
        { find: '\\d+', replace: 'NUM', regex: true }
      ]);
      const result = core.applyRules('Item 42 and 99', rules);
      assert.strictEqual(result, 'Item NUM and NUM');
    });
  });
});