/**
 * hti-shim.js — tiny ESM shim for html-to-image on the bugbottle demo page.
 *
 * The library's `captureScreenshot` does `await import("html-to-image")`.
 * In a bundler that resolves via package.json; on a plain CDN import there
 * is no resolver, so the demo page declares an import map that maps the bare
 * specifier to this file, which re-exports the real html-to-image build.
 */
export const { toPng } = globalThis.htmlToImage;
