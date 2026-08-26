#!/usr/bin/env python3
"""Iteration 466: Danish FAQ + FAQPage JSON-LD for the 3 remaining DA mirrors.

Same pattern as iter465_tool_faqs.py. Idempotent: second run changes nothing.
Covers: color-blindness-simulator-da, contrast-checker-da, text-on-image-checker-da.
"""
import json, os, re

ROOT = '/Users/madsholstjensen/hermes-passiv'
SITE = os.path.join(ROOT, 'site')

FAQS = {
'color-blindness-simulator-da.html': [
 ('Hvor præcis er simuleringen?',
  'Værktøjet bruger den anerkendte Machado et al. (2009)-model for protanopi, '
  'deuteranopi og tritanopi — de samme matricer som professionelle designværktøjer. '
  'Den viser, hvordan farver omtrent opfattes, men kun en klinisk test kan diagnosticere '
  'farvesynshos et menneske.'),
 ('Bliver mine farver sendt nogetsted hen?',
  'Nej. Simuleringen kører udelukkende i JavaScript i din browser. Din palet forlader '
  'aldrig din enhed.'),
 ('Hvilken type skal jeg tjekke imod?',
  'Deuteranopi (rød-grøn) er klart den mest udbredte, så start der. Fungerer dit design '
  'for deuteranopi og tritanopi, virker det næsten altid også for sjældnere typer. Tjek '
  'både tekstkontrast og farvekoder i diagrammer og statusindikatorer.'),
 ('Erstatte det en WCAG-kontrasttjek?',
  'Nej — de besvarer forskellige spørgsmål. En kontrastchecker fortæller, om teksten er '
  'læselig; denne simulator viser, om to farver stadig kan skelnes når farvesynet er '
  'nedsat. Brug begge: kontrast til læsbarhed, simulering til farvekodning.'),
],
'contrast-checker-da.html': [
 ('Hvad kræver AA og AAA af kontrast?',
  'WCAG 2.x AA kræver 4,5:1 for almindelig tekst og 3:1 for stor tekst (18 pt eller '
  '14 pt fed og op). AAA kræver 7:1 hhv. 4,5:1. Ikke-tekstlige elementer som kantfarver '
  'på formularfelter skal have mindst 3:1 under AA.'),
 ('Hvordan beregnes kontrastforholdet?',
  'Relativ luminans for begge farver beregnes efter WCAG-formlen (sRGB-værdier '
  'lineariseres og vægtes 0,2126 R + 0,7152 G + 0,0722 B), og den lyseste værdi divideres '
  'med den mørkeste plus 0,05. Resultatet ligger mellem 1:1 og 21:1.'),
 ('Kan jeg teste mere end forgrund/baggrund?',
  'Ja, du kan teste vilkårlige farvepar — også disabled-tilstande og pladsholdertekst. '
  'Bemærk at WCAG fritager logoer og rent dekorative elementer fra kravene.'),
 ('Hvorfor fejler hvid tekst på min brandfarve?',
  'Mange mellemtoner (gul, lyseblå, beige) har høj luminans, så hvid på toppen giver '
  'forhold omkring 2:1. Mørk tekst passerer ofte med det samme — prøv begge retninger, '
  'før du designer paletten om.'),
],
'text-on-image-checker-da.html': [
 ('Hvordan måles læsbarhed?',
  'Værktøjet beregner WCAG-agtig kontrast mellem din tekstfarve og repræsentative '
  'baggrundsområder i billedet og markerer steder hvor forholdet er under 4,5:1 '
  '(almindelig tekst) eller 3:1 (stor tekst). Det er en tilnærmelse — vurdér også travle '
  'fotografiske områder visuelt.'),
 ('Hurtigste løsning på ulæselig tekst på et billede?',
  'Tilføj en scrím: en halvgennemsigtig mørk overlay bag teksten, eller placér teksten på '
  'en ensfarvet bjælke. Begge dele hæver kontrasten markant uden at ændre billedet eller '
  'brandfarverne.'),
 ('Bliver mine billeder uploadet?',
  'Nej. Alt kører lokalt i din browser via canvas — billedfilen forlader aldrig din enhed.'),
 ('Har det betydning for tilgængelighed?',
  'Ja. WCAG 2.x kræver 4,5:1 kontrast for almindelig tekst uanset baggrund, og EU\'s '
  'tilgængelighedslov presser offentlige sider mod overholdelse. Tekst bagt ind i billeder '
  'kan desuden ikke zoomes, oversættes eller markeres — foretræk ægte HTML-tekst hvor det '
  'er muligt.'),
],
}

def jsonld(faqs):
    return json.dumps({
        '@context': 'https://schema.org', '@type': 'FAQPage',
        'mainEntity': [{'@type': 'Question', 'name': q,
                        'acceptedAnswer': {'@type': 'Answer', 'text': a}}
                       for q, a in faqs],
    }, ensure_ascii=False)

def faq_section_html(faqs):
    cards = '\n      '.join(
        f'<div class="card"><h3>{q}</h3><p>{a}</p></div>' for q, a in faqs)
    return f'''<section style="margin:2.5rem 0;">
  <h2>Ofte stillede spørgsmål</h2>
  <div class="problem-cards" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:1rem;">
      {cards}
  </div>
</section>

'''

def main():
    changed = []
    for fname, faqs in FAQS.items():
        path = os.path.join(SITE, fname)
        c = open(path).read()
        if 'FAQPage' in c:
            print(f'{fname}: ok (already has FAQPage)')
            continue
        assert c.count('</main>') == 1, fname
        c = c.replace('</main>', faq_section_html(faqs) + '</main>', 1)
        head_anchor = '</head>'
        assert c.count(head_anchor) == 1, fname
        c = c.replace(head_anchor,
                      '<script type="application/ld+json">\n' + jsonld(faqs)
                      + '\n</script>\n' + head_anchor, 1)
        open(path, 'w').write(c)
        changed.append(fname)
        print(f'{fname}: UPDATED')
    # validate everything
    for fname in FAQS:
        c = open(os.path.join(SITE, fname)).read()
        types = []
        for b in re.findall(r'<script type="application/ld\+json">(.*?)</script>',
                            c, re.DOTALL):
            p = json.loads(b)
            assert p['@context'] == 'https://schema.org'
            types.append(p['@type'])
        assert 'FAQPage' in types, (fname, types)
    print('changed:', len(changed), changed)

if __name__ == '__main__':
    main()
