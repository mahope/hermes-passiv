// Clean Copy Pro har været til salg siden 24/9, men de to mest hentede filer i
// hele familien — `clean-copy-firefox-v1.5.4.zip` (9 besøg/7 d) og
// `clean-copy-v1.5.3.zip` (8) — sagde i popup'en «Pro $19/yr [Soon]». En læser
// der lige har installeret den gratis udgave fik altså at vide, at den betalte
// udgave ikke findes endnu, ét klik fra en licensside der sælger den.
//
// Porten dømmer de to browsere i den kilde der *bygger* arkivet: popup'en må
// ikke love «Soon», og licenssiden skal have Stripe-købslinket — en
// Activate-knap uden en vej til at købe er en død ende for den gratis bruger.
// Klikket kan ikke måles inde i en udvidelsesside (ingen /track.js, og
// /api/track er same-origin); det måles på Stripe-webhooken og på
// aktiveringen. Porten læser også arkivet i `site/downloads/` — den kode en
// køber faktisk henter — så en rettelse der kun rammer kilden uden genbygning
// bliver rød.
import { readFileSync, existsSync } from 'node:fs';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { inflateRawSync } from 'node:zlib';

// Clean Copy Pro årligt, fra Stripe-kontrakten 24/9.
const PAY_LINK = 'buy.stripe.com/6oU4gy76PgvgdBIdAXbMQ00';

// Nok af ZIP-formatet til at læse medlemmerne: lokal filheader, navn, og
// deflateret indhold. Arkiverne er bygget af `build_clean_copy_archives.py`.
function unzip(bytes) {
  const out = {};
  for (let i = 0; i + 30 <= bytes.length;) {
    if (bytes.readUInt32LE(i) !== 0x04034b50) break;
    const method = bytes.readUInt16LE(i + 8);
    const compressed = bytes.readUInt32LE(i + 18);
    const nameLen = bytes.readUInt16LE(i + 26);
    const extraLen = bytes.readUInt16LE(i + 28);
    const name = bytes.toString('utf8', i + 30, i + 30 + nameLen);
    const start = i + 30 + nameLen + extraLen;
    const body = bytes.subarray(start, start + compressed);
    out[name] = method === 0 ? body.toString('utf8') : inflateRawSync(body).toString('utf8');
    i = start + compressed;
  }
  return out;
}

let failed = 0;
function ok(cond, what, extra) {
  if (!cond) { failed++; console.log('FAIL ' + what + (extra ? ' — ' + extra : '')); }
}

const root = fileURLToPath(new URL('..', import.meta.url));

const SOURCES = ['extension-clean-copy', 'extension-clean-copy-firefox'];
const ARCHIVES = ['site/downloads/clean-copy-v1.5.3.zip', 'site/downloads/clean-copy-firefox-v1.5.4.zip'];

for (const src of SOURCES) {
  const popup = readFileSync(join(root, src, 'popup.js'), 'utf8');
  ok(!/Soon/.test(popup), `${src}/popup.js lover ikke «Soon»`, 'Pro er til salg; teksten skal sige det');
  ok(/\$19\/yr/.test(popup), `${src}/popup.js viser prisen`);
  // Klikket skal føre til licenssiden, der sælger og aktiverer.
  ok(/openOptionsPage/.test(popup), `${src}/popup.js åbner licenssiden ved klik`);
  // Statisk fallback i popup'en: JS overskriver den, men vises JS ikke …
  const popupHtml = readFileSync(join(root, src, 'popup.html'), 'utf8');
  ok(!/Soon/.test(popupHtml), `${src}/popup.html lover ikke «Soon»`);
  // Licenssiden skal sælge: Stripe-købslinket til Clean Copy Pro.
  const options = readFileSync(join(root, src, 'options.html'), 'utf8');
  ok(options.includes('https://' + PAY_LINK), `${src}/options.html har købslinket`, 'Activate uden købslink er en død ende');
  ok(/\$19\/year/.test(options), `${src}/options.html viser prisen ved købslinket`);
  ok(/buy-hint/.test(options), `${src}/options.html har et element købslinket kan skjule i`);
  const optionsJs = readFileSync(join(root, src, 'options.js'), 'utf8');
  ok(optionsJs.includes("getElementById('buy-hint').hidden = true"), `${src}/options.js skjuler købslinket når Pro er aktiv`);
  ok(optionsJs.includes("getElementById('buy-hint').hidden = false"), `${src}/options.js viser købslinket når Pro ikke er aktiv`);
}

// Arkivet er det der hentes. Findes det, skal de samme krav holde for det.
for (const archive of ARCHIVES) {
  const full = join(root, archive);
  if (!existsSync(full)) { ok(false, `${archive} findes`); continue; }
  const members = unzip(readFileSync(full));
  if ('popup.js' in members) ok(!/Soon/.test(members['popup.js']), `${archive}: popup.js lover ikke «Soon»`);
  if ('popup.html' in members) ok(!/Soon/.test(members['popup.html']), `${archive}: popup.html lover ikke «Soon»`);
  if ('options.html' in members) {
    ok(members['options.html'].includes('https://' + PAY_LINK), `${archive}: options.html har købslinket`);
    ok(!/Soon/.test(members['options.html']), `${archive}: options.html lover ikke «Soon»`);
  }
}

console.log(failed ? `clean-copy-pro-popup: ${failed} FEJL` : 'clean-copy-pro-popup: alle krav holder');
process.exit(failed ? 1 : 0);
