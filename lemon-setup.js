#!/usr/bin/env node

/**
 * lemon-setup.js — Opretter Clean Copy Pro på Lemon Squeezy
 *
 * Kør når LS API-nøglen er tilgængelig (fra Bitwarden).
 * Bruger LS REST API: https://docs.lemonsqueezy.com/api
 *
 * Brug:
 *   export LS_API_KEY="your-key-here"
 *   node lemon-setup.js
 *
 * Kræver: LS_API_KEY i miljøvariabel.
 */

const LS_API = 'https://api.lemonsqueezy.com/v1';

async function api(path, body) {
  const opts = {
    headers: {
      'Accept': 'application/json',
      'Content-Type': 'application/vnd.api+json',
      'Authorization': `Bearer ${process.env.LS_API_KEY}`,
    },
  };
  if (body) opts.method = 'POST', opts.body = JSON.stringify(body);
  const res = await fetch(`${LS_API}${path}`, opts);
  const data = await res.json();
  if (!res.ok) throw new Error(`LS API ${res.status}: ${JSON.stringify(data)}`);
  return data;
}

async function main() {
  if (!process.env.LS_API_KEY) {
    console.error('ERROR: Sæt LS_API_KEY miljøvariablen.');
    console.error('Hent nøglen fra Bitwarden.');
    process.exit(1);
  }

  console.log('=== Lemon Squeezy Setup ===\n');

  // 1. Tjek butik
  console.log('1. Finder butik...');
  const stores = await api('/stores');
  const store = stores.data?.[0];
  if (!store) throw new Error('Ingen butik fundet på denne konto.');
  console.log(`   Butik: ${store.attributes.name} (${store.id})\n`);

  // 2. Opret produkt: Clean Copy Pro
  console.log('2. Opretter produkt...');
  const product = await api('/products', {
    data: {
      type: 'products',
      attributes: {
        name: 'Clean Copy Pro',
        slug: 'clean-copy-pro',
        description: 'Pro license for Clean Copy — copy web text as clean Markdown or plain text. Custom rules, auto-detect mode, dark mode, multi-format clipboard, file export. One license covers Chrome extension, CLI, and all 7 surfaces.',
        status: 'published',
      },
      relationships: {
        store: { data: { type: 'stores', id: store.id } },
      },
    },
  });
  const prodId = product.data?.id;
  console.log(`   Produkt ID: ${prodId}\n`);

  // 3. Opret variant: $19/år (enkeltbetaling)
  console.log('3. Opretter variant (Yearly - $19)...');
  const variant = await api('/variants', {
    data: {
      type: 'variants',
      attributes: {
        name: 'Yearly',
        slug: 'yearly',
        price: 1900, // $19.00 i cent
        is_subscription: false,
        description: 'Clean Copy Pro — 1 year license. Covers all 7 surfaces: Chrome, Firefox, Edge, CLI, VS Code, Obsidian, GitHub Action.',
        sort: 0,
        status: 'published',
      },
      relationships: {
        product: { data: { type: 'products', id: prodId } },
      },
    },
  });
  const varId = variant.data?.id;
  console.log(`   Variant ID: ${varId}\n`);

  // 4. Generer checkout-link
  console.log('4. Genererer checkout-link...');
  const checkout = await api('/checkouts', {
    data: {
      type: 'checkouts',
      attributes: {
        checkout_data: {
          custom: {
            order_id: 'cc_pro_yearly',
          },
          product_options: {
            enabled_variants: [parseInt(varId)],
          },
          checkout_options: {
            embed: false,
            media: true,
            logo: true,
            redirect_url: 'https://hermes-passiv.pages.dev/clean-copy?purchased=true',
          },
        },
      },
      relationships: {
        store: { data: { type: 'stores', id: store.id } },
        variant: { data: { type: 'variants', id: varId } },
      },
    },
  });
  const checkoutUrl = checkout.data?.attributes?.url;
  console.log(`   Checkout URL: ${checkoutUrl}\n`);

  // 5. Sæt LS_WEBHOOK_SECRET som Pages secret
  console.log('5. Sæt LS_WEBHOOK_SECRET som Cloudflare Pages secret:');
  console.log('   source ~/.hermes/.env');
  console.log('   npx wrangler pages secret put LS_WEBHOOK_SECRET --project-name hermes-passiv');
  console.log('   (Indsæt webhook secret fra LS settings → Webhooks)');
  console.log('\n   Tilføj derefter webhook URL i LS Dashboard:');
  console.log('   https://hermes-passiv.pages.dev/api/lemon-webhook');

  console.log('\n=== Færdig! ===');
  console.log(`Checkout URL: ${checkoutUrl || 'SE OUTPUT OVERFOR'}`);
  console.log('\nNæste skridt:');
  console.log('1. Gem checkout-URL i KV (så /clean-copy viser "Buy Pro"):');
  console.log(`   npx wrangler kv key put cc-pro-checkout '${checkoutUrl || '<CHECKOUT_URL>'}' --binding VISITS`);
  console.log('2. Test et køb');
  console.log('3. Verificér at /api/license/activate udsteder en nøgle');
  console.log('4. Indsæt nøglen i Clean Copy extension → Pro aktiveret');
}

main().catch(err => {
  console.error('\nFEJL:', err.message);
  process.exit(1);
});
