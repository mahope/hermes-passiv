/* shell.js — behaviour shared by every page of every Mahope product site.
   Theme button, mobile menu, search palette (+ /search/ page), copy buttons on code,
   share button, back-to-top, same-origin prefetch, TOC scroll-spy, sticky table heads,
   "Report a bug" footer link. No dependencies, no cookies. */
(function () {
  'use strict';
  var d = document, root = d.documentElement, body = d.body;
  var lang = (root.lang || 'en').slice(0, 2);
  var T = lang === 'da'
    ? { theme: ['Tema: system', 'Tema: lys', 'Tema: mørk'], copy: 'Kopiér', copied: 'Kopieret', link: 'Kopiér link', linked: 'Link kopieret', none: 'Ingen sider matcher', min: 'Skriv mindst 2 tegn', top: 'Til toppen' }
    : { theme: ['Theme: system', 'Theme: light', 'Theme: dark'], copy: 'Copy', copied: 'Copied', link: 'Copy link', linked: 'Link copied', none: 'No pages match', min: 'Type at least 2 characters', top: 'Back to top' };

  /* ---- theme: system → light → dark → system --------------------------- */
  var themeBtn = d.querySelector('[data-theme-toggle]');
  function labelTheme() {
    if (!themeBtn) return;
    var t = root.getAttribute('data-theme'), i = t === 'light' ? 1 : t === 'dark' ? 2 : 0;
    themeBtn.setAttribute('aria-label', T.theme[i]); themeBtn.title = T.theme[i];
  }
  if (themeBtn) {
    themeBtn.addEventListener('click', function () {
      var t = root.getAttribute('data-theme'), next = !t ? 'light' : t === 'light' ? 'dark' : null;
      try { if (next) localStorage.setItem('theme', next); else localStorage.removeItem('theme'); } catch (e) {}
      if (next) root.setAttribute('data-theme', next); else root.removeAttribute('data-theme');
      labelTheme();
    });
    labelTheme();
  }

  /* ---- mobile menu ------------------------------------------------------ */
  var header = d.querySelector('.site-header'), navBtn = header && header.querySelector('.nav-toggle');
  function setNav(o) { header.classList.toggle('nav-open', o); navBtn.setAttribute('aria-expanded', o ? 'true' : 'false'); }
  if (navBtn) {
    navBtn.addEventListener('click', function () { setNav(!header.classList.contains('nav-open')); });
    d.addEventListener('keydown', function (e) { if (e.key === 'Escape' && header.classList.contains('nav-open')) { setNav(false); navBtn.focus(); } });
    d.addEventListener('click', function (e) { if (header.classList.contains('nav-open') && !header.contains(e.target)) setNav(false); });
  }

  /* ---- search palette --------------------------------------------------- */
  var dialog = d.querySelector('[data-search-dialog]'), pageForm = d.querySelector('[data-search-page]');
  var index = null, loading = null;
  function loadIndex() {
    if (index) return Promise.resolve(index);
    if (!loading) loading = fetch('/search-index.json').then(function (r) { return r.json(); }).then(function (j) { index = j; return j; }).catch(function () { index = []; return index; });
    return loading;
  }
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function hl(s, terms) {
    var out = esc(s);
    terms.forEach(function (t) { out = out.replace(new RegExp('(' + t.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + ')', 'ig'), '<mark>$1</mark>'); });
    return out;
  }
  function search(q, items) {
    var terms = q.toLowerCase().split(/\s+/).filter(Boolean);
    if (!terms.length) return [];
    var scored = [];
    for (var i = 0; i < items.length; i++) {
      var p = items[i], t = p.title.toLowerCase(), de = (p.description || '').toLowerCase(), b = (p.body || '').toLowerCase(), tg = (p.tags || []).join(' ').toLowerCase();
      var s = 0, ok = true;
      for (var j = 0; j < terms.length; j++) {
        var w = terms[j], hit = 0;
        if (t.indexOf(w) > -1) hit += 6; if (t.indexOf(w) === 0) hit += 2;
        if (de.indexOf(w) > -1) hit += 3;
        if (tg.indexOf(w) > -1) hit += 3;
        if (b.indexOf(w) > -1) hit += 1;
        if (!hit) { ok = false; break; }
        s += hit;
      }
      if (ok) { if (p.lang === lang) s += 2; scored.push([s, p]); }
    }
    scored.sort(function (a, b) { return b[0] - a[0]; });
    return scored.slice(0, 30).map(function (x) { return x[1]; });
  }
  function render(list, q, hits) {
    var terms = q.toLowerCase().split(/\s+/).filter(Boolean);
    if (q.trim().length < 2) { list.innerHTML = '<li class="hint">' + T.min + '</li>'; return; }
    if (!hits.length) { list.innerHTML = '<li class="empty">' + T.none + ' “' + esc(q) + '”</li>'; return; }
    var groups = {}, order = [];
    hits.forEach(function (p) { if (!groups[p.section]) { groups[p.section] = []; order.push(p.section); } groups[p.section].push(p); });
    var html = '';
    order.forEach(function (g) {
      html += '<li class="group" role="presentation">' + esc(g) + '</li>';
      groups[g].forEach(function (p) {
        html += '<li role="option"><a href="' + esc(p.url) + '"><span class="t">' + hl(p.title, terms) + '<span class="lang">' + esc(p.lang.toUpperCase()) + '</span></span><span class="d">' + hl(p.description || p.body || '', terms) + '</span></a></li>';
      });
    });
    list.innerHTML = html;
  }
  function wire(form, list, opts) {
    var input = form.querySelector('input[type=search]'), sel = -1, timer;
    function links() { return [].slice.call(list.querySelectorAll('a')); }
    function select(i) {
      var a = links(); if (!a.length) return;
      sel = (i + a.length) % a.length;
      a.forEach(function (x, k) { x.setAttribute('aria-selected', k === sel ? 'true' : 'false'); });
      a[sel].scrollIntoView({ block: 'nearest' });
    }
    function run() {
      var q = input.value;
      loadIndex().then(function (items) { render(list, q, search(q, items)); sel = -1; if (opts.onQuery) opts.onQuery(q); });
    }
    input.addEventListener('input', function () { clearTimeout(timer); timer = setTimeout(run, 80); });
    form.addEventListener('submit', function (e) {
      var a = links();
      if (sel > -1 && a[sel]) { e.preventDefault(); location.href = a[sel].href; }
      else if (opts.stayOnPage) { e.preventDefault(); run(); }
    });
    input.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowDown') { e.preventDefault(); select(sel + 1); }
      else if (e.key === 'ArrowUp') { e.preventDefault(); select(sel - 1); }
    });
    return { input: input, run: run };
  }
  var palette = null;
  if (dialog) {
    var pForm = dialog.querySelector('form'), pList = dialog.querySelector('[data-search-results]');
    palette = wire(pForm, pList, {});
    var lastFocus = null;
    function openSearch() {
      lastFocus = d.activeElement;
      dialog.hidden = false; dialog.classList.add('is-open'); body.style.overflow = 'hidden';
      loadIndex(); palette.input.focus(); palette.input.select();
    }
    function closeSearch() {
      dialog.classList.remove('is-open'); dialog.hidden = true; body.style.overflow = '';
      if (lastFocus && lastFocus.focus) lastFocus.focus();
    }
    d.querySelectorAll('[data-search-open]').forEach(function (b) { b.addEventListener('click', openSearch); });
    dialog.querySelector('[data-search-close]').addEventListener('click', closeSearch);
    dialog.addEventListener('click', function (e) { if (e.target === dialog) closeSearch(); });
    d.addEventListener('keydown', function (e) {
      var tag = (e.target.tagName || '').toLowerCase(), typing = tag === 'input' || tag === 'textarea' || tag === 'select' || e.target.isContentEditable;
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') { e.preventDefault(); dialog.hidden ? openSearch() : closeSearch(); }
      else if (e.key === '/' && !typing && dialog.hidden) { e.preventDefault(); openSearch(); }
      else if (e.key === 'Escape' && !dialog.hidden) { closeSearch(); }
      else if (e.key === 'Tab' && !dialog.hidden) {
        var f = dialog.querySelectorAll('input, button, a[href]'), first = f[0], last = f[f.length - 1];
        if (e.shiftKey && d.activeElement === first) { e.preventDefault(); last.focus(); }
        else if (!e.shiftKey && d.activeElement === last) { e.preventDefault(); first.focus(); }
      }
    });
  }
  if (pageForm) {
    var pg = wire(pageForm, d.querySelector('.search-page [data-search-results]'), { stayOnPage: true, onQuery: function (q) {
      try { history.replaceState(null, '', q ? '?q=' + encodeURIComponent(q) : location.pathname); } catch (e) {}
    } });
    var q0 = new URLSearchParams(location.search).get('q');
    if (q0) { pg.input.value = q0; pg.run(); }
  }

  /* ---- copy buttons on code blocks -------------------------------------- */
  function copyText(text, btn, done, idle) {
    var ok = function () { btn.textContent = done; btn.classList.add('is-done'); setTimeout(function () { btn.textContent = idle; btn.classList.remove('is-done'); }, 1600); };
    if (navigator.clipboard) navigator.clipboard.writeText(text).then(ok, ok); else ok();
  }
  d.querySelectorAll('main pre').forEach(function (pre) {
    if (pre.querySelector('.copy-btn') || pre.closest('.search-dialog')) return;
    var b = d.createElement('button'); b.type = 'button'; b.className = 'copy-btn'; b.textContent = T.copy;
    b.addEventListener('click', function () { copyText(pre.innerText.replace(/\s*Copy\s*$/, '').replace(/^\$ /gm, ''), b, T.copied, T.copy); });
    pre.appendChild(b);
  });
  d.querySelectorAll('[data-copy-link]').forEach(function (b) {
    b.addEventListener('click', function () { copyText(location.href.split('#')[0], b, T.linked, T.link); });
  });

  /* ---- back to top (bottom-left) --------------------------------------- */
  var btt = d.createElement('button'); btt.type = 'button'; btt.className = 'btt'; btt.setAttribute('aria-label', T.top); btt.title = T.top;
  btt.innerHTML = '<svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 19V5M5 12l7-7 7 7"/></svg>';
  btt.addEventListener('click', function () { window.scrollTo({ top: 0, behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' }); });
  body.appendChild(btt);
  var ticking = false;
  function onScroll() { if (ticking) return; ticking = true; requestAnimationFrame(function () { btt.classList.toggle('is-visible', window.scrollY > 600); ticking = false; }); }
  addEventListener('scroll', onScroll, { passive: true }); onScroll();

  /* ---- prefetch same-origin links on intent ------------------------------ */
  var saveData = navigator.connection && navigator.connection.saveData, seen = {};
  function prefetch(a) {
    if (saveData || !a || a.origin !== location.origin || a.hash && a.pathname === location.pathname) return;
    var href = a.href.split('#')[0]; if (seen[href] || href === location.href.split('#')[0]) return; seen[href] = 1;
    var l = d.createElement('link'); l.rel = 'prefetch'; l.href = href; l.as = 'document'; d.head.appendChild(l);
  }
  d.addEventListener('mouseover', function (e) { var a = e.target.closest && e.target.closest('a[href]'); if (a) prefetch(a); }, { passive: true });
  d.addEventListener('touchstart', function (e) { var a = e.target.closest && e.target.closest('a[href]'); if (a) prefetch(a); }, { passive: true });

  /* ---- TOC: open on wide screens, scroll-spy ---------------------------- */
  var toc = d.querySelector('.toc');
  if (toc) {
    var det = toc.querySelector('details'), mq = matchMedia('(min-width: 1100px)');
    function syncToc() { if (det && mq.matches) det.open = true; }
    syncToc(); mq.addEventListener ? mq.addEventListener('change', syncToc) : mq.addListener(syncToc);
    var tocLinks = [].slice.call(toc.querySelectorAll('a[href^="#"]')), targets = [];
    tocLinks.forEach(function (a) { var el = d.getElementById(decodeURIComponent(a.getAttribute('href').slice(1))); if (el) targets.push([el, a]); });
    if ('IntersectionObserver' in window && targets.length) {
      var current = null;
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (en) { if (en.isIntersecting) current = en.target; });
        if (!current) return;
        targets.forEach(function (t) { t[1].classList.toggle('is-active', t[0] === current); });
      }, { rootMargin: '-80px 0px -70% 0px', threshold: 0 });
      targets.forEach(function (t) { io.observe(t[0]); });
    }
  }

  /* ---- tables: sticky head only when the table does not scroll sideways --- */
  d.querySelectorAll('.table-wrap').forEach(function (w) {
    var t = w.querySelector('table'); if (t && t.scrollWidth <= w.clientWidth + 1) w.style.overflow = 'visible';
  });

  /* ---- footer "Report a bug": open the BugBottle panel if it is mounted --- */
  d.querySelectorAll('[data-bugbottle-open]').forEach(function (a) {
    a.addEventListener('click', function (e) {
      var host = d.querySelector('[data-bugbottle="ui"]'), trig = host && host.shadowRoot && host.shadowRoot.querySelector('button.trigger');
      if (trig) { e.preventDefault(); trig.click(); }
    });
  });
})();
