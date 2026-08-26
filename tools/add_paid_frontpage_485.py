#!/usr/bin/env python3
"""iter 485: Add a "Paid tools" section to the EN frontpage (site/index.html)
and mirror it in Danish on /da (site/da.html), which currently has no paid
products at all. Also adds the same promo band used on /guides."""
import re, sys

PROMO_BAND = """
<section style="background:var(--color-surface-2,#f1f5f9);border-top:1px solid var(--color-border);border-bottom:1px solid var(--color-border);padding:18px 24px;">
  <div style="max-width:800px;margin:0 auto;display:flex;gap:16px;flex-wrap:wrap;justify-content:center;align-items:center;font-size:0.95rem;">
    <span style="color:var(--color-muted,#64748b);">Go further with the paid tools:</span>
    <a href="/deskuptime" style="font-weight:600;">DeskUptime Pro — website monitoring from your desktop, $19 one-time &rarr;</a>
    <a href="/page-profile#quickstart" style="font-weight:600;">Page Profile Pro — batch audits &amp; client-ready reports, $19/year &rarr;</a>
  </div>
</section>
"""

PAID_SECTION_EN = """
<section class="products" id="paid-tools">
  <div class="container">
    <h2>Paid tools — buy once, use forever</h2>
    <p class="section-intro">Two desktop tools for agencies and consultants. No subscription traps: one is a single payment, the other costs less per year than one hour of consulting.</p>
    <div class="product-grid">
      <div class="product-card feature">
        <div class="product-badge">PRO</div>
        <div class="product-body">
          <h3>DeskUptime Pro</h3>
          <p class="product-desc">Website monitoring that lives in your macOS or Windows menu bar. Checks every site on your schedule, alerts you when something breaks. You own it — no monthly fees, ever.</p>
          <div class="product-details">
            <span class="product-meta">🖥 macOS + Windows</span>
            <span class="product-meta">⏱ Multi-site checks</span>
            <span class="product-meta">🔔 Desktop alerts</span>
          </div>
          <div class="product-price">
            <span class="price-tag">$19</span>
            <span class="product-meta">one-time · lifetime license</span>
          </div>
          <div class="product-cta">
            <a href="/deskuptime" class="btn-primary">Get DeskUptime Pro →</a>
          </div>
        </div>
      </div>
      <div class="product-card feature">
        <div class="product-badge">PRO</div>
        <div class="product-body">
          <h3>Page Profile Pro</h3>
          <p class="product-desc">SEO and metadata auditing from the terminal: audit hundreds of URLs in one batch run, compare any two pages side by side, and export client-ready HTML reports.</p>
          <div class="product-details">
            <span class="product-meta">📦 Batch mode</span>
            <span class="product-meta">📊 HTML reports</span>
            <span class="product-meta">🔀 Page compare</span>
          </div>
          <div class="product-price">
            <span class="price-tag">$19</span>
            <span class="product-meta">/ year · all updates included</span>
          </div>
          <div class="product-cta">
            <a href="/page-profile" class="btn-primary">Get Page Profile Pro →</a>
          </div>
        </div>
      </div>
    </div>
  </div>
</section>
"""

PROMO_BAND_DA = PROMO_BAND.replace(
    'Go further with the paid tools:', 'Tag næste skridt med de betalte værktøjer:'
).replace(
    'DeskUptime Pro — website monitoring from your desktop, $19 one-time',
    'DeskUptime Pro — overvåg hjemmesider fra din desktop, $19 engangs'
).replace(
    'Page Profile Pro — batch audits &amp; client-ready reports, $19/year',
    'Page Profile Pro — batch-audits &amp; kundeklare rapporter, $19/år'
)

PAID_SECTION_DA = """
<section class="products" id="betaltevaerktoejer">
  <div class="container">
    <h2>Betalte værktøjer — køb én gang, brug for altid</h2>
    <p class="section-intro">To desktop-værktøjer til bureauer og konsulenter. Ingen abonnementsfælder: det ene er en engangsbetaling, det andet koster mindre om året end en times konsultation.</p>
    <div class="product-grid">
      <div class="product-card feature">
        <div class="product-badge">PRO</div>
        <div class="product-body">
          <h3>DeskUptime Pro</h3>
          <p class="product-desc">Website-overvågning i din macOS- eller Windows-menu bar. Tjekker alle dine sider efter din tidsplan og alarmerer når noget går ned. Du ejer den — ingen månedlige gebyrer, nogensinde.</p>
          <div class="product-details">
            <span class="product-meta">🖥 macOS + Windows</span>
            <span class="product-meta">⏱ Fler-side tjek</span>
            <span class="product-meta">🔔 Desktop-alarmer</span>
          </div>
          <div class="product-price">
            <span class="price-tag">$19</span>
            <span class="product-meta">engangs · livstidslicens</span>
          </div>
          <div class="product-cta">
            <a href="/deskuptime" class="btn-primary">Hent DeskUptime Pro →</a>
          </div>
        </div>
      </div>
      <div class="product-card feature">
        <div class="product-badge">PRO</div>
        <div class="product-body">
          <h3>Page Profile Pro</h3>
          <p class="product-desc">SEO- og metadata-audits fra terminalen: auditér hundredvis af URL'er i én batch-kørsel, sammenlign vilkårlige to sider side om side, og eksportér kundeklare HTML-rapporter.</p>
          <div class="product-details">
            <span class="product-meta">📦 Batch-tilstand</span>
            <span class="product-meta">📊 HTML-rapporter</span>
            <span class="product-meta">🔀 Side-sammenligning</span>
          </div>
          <div class="product-price">
            <span class="price-tag">$19</span>
            <span class="product-meta">/ år · alle opdateringer inkluderet</span>
          </div>
          <div class="product-cta">
            <a href="/page-profile" class="btn-primary">Hent Page Profile Pro →</a>
          </div>
        </div>
      </div>
    </div>
  </div>
</section>
"""

def insert_after_section(html, anchor_id, addition):
    """Insert `addition` right after the section whose opening tag contains anchor_id."""
    m = re.search(r'<section[^>]*\bid="%s"[^>]*>' % re.escape(anchor_id), html)
    if not m:
        sys.exit('anchor not found: %s' % anchor_id)
    # find matching close of this section by scanning depth
    depth = 1
    i = m.end()
    for tag in re.finditer(r'</?section\b', html[m.end():]):
        if tag.group(0) == '</section':  # NOTE: \b ends before '>'
            depth -= 1
            if depth == 0:
                end = m.end() + tag.end()
                return html[:end] + addition + html[end:]
        else:
            depth += 1
    sys.exit('no closing section for %s' % anchor_id)

def main():
    # EN frontpage: paid section after premium-tools; promo band after free-tools
    h = open('site/index.html').read()
    assert 'id="paid-tools"' not in h
    h = insert_after_section(h, 'premium-tools', PAID_SECTION_EN)
    h = insert_after_section(h, 'free-tools', PROMO_BAND)
    open('site/index.html', 'w').write(h)

    # DA frontpage: paid section after gratis vaerktoejer; promo band too
    d = open('site/da.html').read()
    assert 'betaltevaerktoejer' not in d
    d = insert_after_section(d, 'vaerktoejer', PAID_SECTION_DA)
    d = insert_after_section(d, 'vaerktoejer', '')  # no-op guard, keeps order simple
    open('site/da.html', 'w').write(d)
    print('done')

if __name__ == '__main__':
    main()
