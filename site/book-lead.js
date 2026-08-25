/* Book page lead capture — shown once after a download click.
 * Reuses /api/waitlist with source=book-<slug> so stats show where leads come from.
 * Honest copy: one email at launch, no spam. No data beyond the email itself.
 */
(function () {
  'use strict';
  if (navigator.doNotTrack === '1') return;
  var slug = (location.pathname.replace(/\.html$/, '').split('/').pop() || 'book');
  var source = 'book-' + slug;
  var shown = false;

  function track(ev) {
    try {
      var p = location.pathname.replace(/\.html$/, '') || '/';
      navigator.sendBeacon('/api/track', new Blob([JSON.stringify({ path: p, event: ev })], { type: 'application/json' }));
    } catch (e) {}
  }

  function submitLead() {
    var email = document.getElementById('blEmail').value.trim();
    var st = document.getElementById('blStatus');
    if (!/^[^\s@]{1,64}[^\s@]*@[^\s@]+\.[^\s@]{2,}$/.test(email)) {
      st.textContent = 'Please enter a valid email address.';
      st.className = 'bl-status bl-error';
      return;
    }
    var btn = document.getElementById('blBtn');
    btn.disabled = true;
    fetch('/api/waitlist', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: email, source: source })
    })
      .then(function (res) { return res.json(); })
      .then(function (data) {
        if (data.ok) track('book-lead');
        st.textContent = data.ok
          ? 'Thanks — you are on the list. We will email you once when new guides or templates launch.'
          : (data.error || 'Something went wrong. Please try again.');
        st.className = 'bl-status' + (data.ok ? '' : ' bl-error');
      })
      .catch(function () {
        btn.disabled = false;
        st.textContent = 'Network error. Please try again.';
        st.className = 'bl-status bl-error';
      });
  }

  function showLeadBar() {
    if (shown) return;
    shown = true;
    track('book-lead-view');
    var bar = document.createElement('div');
    bar.id = 'bookLead';
    bar.setAttribute('role', 'complementary');
    bar.setAttribute('aria-label', 'Get notified about new compliance guides');
    bar.innerHTML =
      '<p class="bl-title">Get the next guide first</p>' +
      '<p class="bl-sub">New compliance e-books, checklists and templates launch regularly. One email at launch — no spam, no newsletter.</p>' +
      '<div class="bl-form">' +
      '<input type="email" id="blEmail" placeholder="you@agency.com" aria-label="Your email address" />' +
      '<button type="button" id="blBtn" class="btn-primary">Notify me</button>' +
      '</div>' +
      '<p class="bl-status" id="blStatus" role="status"></p>';
    document.body.appendChild(bar);
    document.getElementById('blBtn').addEventListener('click', submitLead);
    document.getElementById('blEmail').addEventListener('keydown', function (e) {
      if (e.key === 'Enter') submitLead();
    });
  }

  document.addEventListener('click', function (ev) {
    var a = ev.target && ev.target.closest ? ev.target.closest('a[href$=".epub"]') : null;
    if (a) setTimeout(showLeadBar, 800);
  }, true);

  var css = document.createElement('style');
  css.textContent =
    '#bookLead{max-width:560px;margin:28px auto;padding:22px 24px;background:#f0f6ff;border:1px solid #c7dbf7;border-radius:10px;text-align:center;font-family:inherit}' +
    '#bookLead .bl-title{font-size:18px;font-weight:700;margin:0 0 6px;color:#1a2b4a}' +
    '#bookLead .bl-sub{font-size:13.5px;color:#556;margin:0 0 14px;line-height:1.5}' +
    '#bookLead .bl-form{display:flex;gap:8px;justify-content:center;flex-wrap:wrap}' +
    '#bookLead input[type=email]{flex:1;min-width:200px;max-width:280px;padding:11px 14px;border:1px solid #b9c8dd;border-radius:6px;font-size:15px}' +
    '#bookLead .btn-primary{margin-top:0;padding:11px 24px;border:none;cursor:pointer}' +
    '#bookLead .bl-status{font-size:13px;margin:10px 0 0;color:#2e7d32}' +
    '#bookLead .bl-error{color:#c0392b}';
  document.head.appendChild(css);
})();
