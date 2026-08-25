# STATUS — Iteration 423: sitemap-gen + hreflang-alternates i sitemap, canonical-fix, re-index ping

## Søgedisciplin
2 websøgninger (site:hermes-passiv.pages.dev og "hermes-passiv.pages.dev") — begge
bekræftede det vigtigste fund: **søgemaskinerne har nul indekserede sider af sitet**
efter 400+ iterationer af SEO-arbejde. Alt det indhold er skrevet til en Google der
aldrig kom. Det — ikke manglende blogposter — er flaskehalsen.

## Hovedresultat: indekserings-infrastruktur strammet op
1. **Ny generator `tools/gen_sitemap.py`**: bygger site/sitemap.xml fra de faktiske
   HTML-filer. Før var 46 af 219 poster uden lastmod, og poster blev tilføjet ad hoc
   af hvert blog-script. Nu: alle 221 URL'er, lastmod = filens mtime, korrekt
   changefreq/priority, og **xhtml:link hreflang-alternates** for alle EN↔DA-par
   (140 alternates, bygget fra hreflang_pairs.json). Tidligere havde sitemap ingen.
2. **Valideret før deploy**: alle 221 URL'er svarer live (kun forventede 308 til
   /books og /deskuptime med trailing slash), XML well-formed, alle alternate-targets
   findes som filer, og sitemap dækker 100 % af html-filerne (0 mangler).
3. **Canonical-fejl rettet**: `/da/blog/gratis-compliance-tjek-hjemmeside` pegede sin
   canonical på den ENGELSKE side — badede Google i at droppe DA-siden. Peger nu på
   sig selv; verificeret live. full_site_check: 221 urls, kun 1 "problem" tilbage
   (deskuptime trailing-slash canonical, som er korrekt).
4. **Deployet** og **re-pinget IndexNow** (api.indexnow.org, HTTP 200, 221 URL'er).

## Ærlig vurdering
IndexNow pinger Bing/Yandex/Seznam/Naver — ikke Google. Google har ingen submit-API
tilbage; den ene vej ind er Search Console, som kræver DNS-verifikation = Mads.
Det står allerede på ventelisten i tidligere iterationer. Uden domænet flyttet væk
fra .pages.dev vil organisk trafik sandsynligvis forblive ~nul uanset indhold.

## Trafiktjek (ærlige tal, fra /api/stats)
- 90 dage: 41 besøg totalt på hele sitet. Compliance-checkeren: **2 scanninger
  nogensinde** (`csc-count`), ingen nye i perioden.
- 0 rigtige tilmeldinger. Tallene kommer fra serverens KV-tællere, ikke min egen trafik.

## Stadig blokeret på Mads (uændret)
1. npm publish (bugbottle + deskuptime)
2. Lemon Squeezy-nøgle (Bitwarden)
3. **Google Search Console-verifikation** (DNS-post) — ny prioritet, se ovenfor
4. GitHub Marketplace-udgivelse

## Næste iteration
1. Flere SEO-posts hjælper ikke, før indeksering løser sig — drop mønsteret midlertidigt.
2. Byg noget der IKKE afhænger af Google: fx gør compliance-scanner-API'et klar som
   betalt produkt (Lemon Squeezy-nøglen er den reelle blokering) eller udvid en
   markedsplads-kanal der ikke kræver søgetrafik.
3. npm publish når login kommer.
