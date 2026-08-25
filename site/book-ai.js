/* Book page AI assistant — compact inline chat reusing /api/compliance-ai.
 * Injected before <footer> on book pages. Lead capture after first answer,
 * waitlist source=bookai-<slug> so stats show which title converts.
 * Rate limit lives server-side (20/day); errors are shown inline.
 */
(function () {
  'use strict';
  if (navigator.doNotTrack === '1') return;
  if (!document.querySelector('footer')) return;

  var slug = (location.pathname.replace(/\.html$/, '').split('/').pop() || 'book');
  var source = 'bookai-' + slug;
  var asked = false;

  var SUGGESTIONS = {
    'nis2-for-agencies': [
      'Does NIS2 apply to a 5-person agency?',
      'What are the NIS2 incident reporting deadlines?',
      'What security measures does Article 21 require?'
    ],
    'gdpr-for-agencies': [
      'Do I need a DPA for every client?',
      'What must a GDPR data processing agreement contain?',
      'Can I use Google Analytics under GDPR?'
    ],
    'eaa-checklist': [
      'Does the EAA apply to my website?',
      'What are the EAA deadlines?',
      'Which WCAG level does the EAA require?'
    ],
    'eaa-shopify': [
      'What EAA rules apply to my Shopify store?',
      'How do I write an accessibility statement?',
      'What happens if my shop is not accessible?'
    ],
    'cookie-consent-guide': [
      'Do I need cookie consent for analytics?',
      'Is a cookie banner enough for GDPR?',
      'What makes consent valid under GDPR?'
    ]
  };
  var chips = SUGGESTIONS[slug] || ['What does this mean for my business?'];

  function esc(s) {
    return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  function fmt(text) {
    var html = text
      .replace(/&/g, '&amp;').replace(/</g, '&lt;')
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .split(/\n\n+/)
      .map(function (p) {
        p = p.trim();
        if (!p) return '';
        if (/^[-*]\s/m.test(p)) {
          return '<ul>' + p.split(/\n/).map(function (li) {
            return '<li>' + li.replace(/^[-*]\s+/, '') + '</li>';
          }).join('') + '</ul>';
        }
        return '<p>' + p.replace(/\n/g, '<br>') + '</p>';
      }).join('');
    html += '<p class="bai-disclaimer">General guidance, not legal advice.</p>';
    return html;
  }

  function track(ev) {
    try {
      navigator.sendBeacon('/api/track', new Blob(
        [JSON.stringify({ path: location.pathname.replace(/\.html$/, '') || '/', event: ev })],
        { type: 'application/json' }));
    } catch (e) {}
  }

  function showLead() {
    if (document.getElementById('baiLead')) return;
    track('bookai-lead-view');
    var d = document.createElement('div');
    d.className = 'bai-lead';
    d.id = 'baiLead';
    d.innerHTML =
      '<p class="bai-lead-title">Want more like this?</p>' +
      '<p class="bai-lead-sub">New compliance guides and templates launch regularly. One email at launch — no spam.</p>' +
      '<div class="bai-form"><input type="email" id="baiEmail" placeholder="you@agency.com" aria-label="Your email address" />' +
      '<button type="button" id="baiBtn">Notify me</button></div>' +
      '<p class="bai-status" id="baiStatus" role="status"></p>';
    log.appendChild(d);
    document.getElementById('baiBtn').addEventListener('click', submitLead);
    document.getElementById('baiEmail').addEventListener('keydown', function (e) {
      if (e.key === 'Enter') submitLead();
    });
  }

  function submitLead() {
    var email = document.getElementById('baiEmail').value.trim();
    var st = document.getElementById('baiStatus');
    if (!/^[^\s@]{1,64}[^\s@]*@[^\s@]+\.[^\s@]{2,}$/.test(email)) {
      st.textContent = 'Please enter a valid email address.';
      st.className = 'bai-status bai-error';
      return;
    }
    document.getElementById('baiBtn').disabled = true;
    fetch('/api/waitlist', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: email, source: source })
    })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (data.ok) track('bookai-lead');
        st.textContent = data.ok
          ? 'Thanks — you are on the list.'
          : (data.error || 'Something went wrong. Please try again.');
        st.className = 'bai-status' + (data.ok ? '' : ' bai-error');
      })
      .catch(function () {
        st.textContent = 'Network error. Please try again.';
        st.className = 'bai-status bai-error';
      });
  }

  function addMsg(text, role) {
    var m = document.createElement('div');
    m.className = 'bai-msg bai-' + role;
    m.innerHTML = role === 'assistant' ? fmt(text) : esc(text);
    log.appendChild(m);
    log.scrollTop = log.scrollHeight;
  }

  function ask(q) {
    q = (q || input.value).trim();
    if (!q || busy) return;
    busy = true;
    btn.disabled = true;
    chipsEl.style.display = 'none';
    status.textContent = '';
    addMsg(q, 'user');
    input.value = '';
    var typing = document.createElement('div');
    typing.className = 'bai-msg bai-assistant bai-typing';
    typing.textContent = 'Thinking…';
    log.appendChild(typing);
    log.scrollTop = log.scrollHeight;

    fetch('/api/compliance-ai', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: q })
    })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        typing.remove();
        busy = false;
        btn.disabled = false;
        if (data.ok) {
          addMsg(data.answer, 'assistant');
          showLead();
        } else {
          status.textContent = data.error === 'Rate limit exceeded. Try again tomorrow.'
            ? 'Daily limit reached — please come back tomorrow.'
            : (data.error || 'Something went wrong. Please try again.');
          status.className = 'bai-status bai-error';
        }
      })
      .catch(function () {
        typing.remove();
        busy = false;
        btn.disabled = false;
        status.textContent = 'Network error. Please try again.';
        status.className = 'bai-status bai-error';
      });
  }

  var footer = document.querySelector('footer');
  var wrap = document.createElement('section');
  wrap.id = 'bookAi';
  wrap.setAttribute('aria-label', 'Ask AI about this topic');
  wrap.innerHTML =
    '<h2>Questions while you read?</h2>' +
    '<p class="bai-intro">Ask our free AI compliance assistant about this topic — concrete answers, no signup.</p>' +
    '<div class="bai-log" id="baiLog" role="log" aria-live="polite"></div>' +
    '<div class="bai-inputrow">' +
    '<textarea id="baiInput" rows="1" placeholder="Ask about this topic…" aria-label="Your question"></textarea>' +
    '<button type="button" id="baiAsk">Ask</button></div>' +
    '<div class="bai-chips" id="baiChips"></div>' +
    '<p class="bai-status" id="baiTopStatus" role="status"></p>';

  footer.parentNode.insertBefore(wrap, footer);
  var log = document.getElementById('baiLog');
  var input = document.getElementById('baiInput');
  var btn = document.getElementById('baiAsk');
  var chipsEl = document.getElementById('baiChips');
  var status = document.getElementById('baiTopStatus');
  var busy = false;

  chips.forEach(function (c) {
    var chip = document.createElement('button');
    chip.type = 'button';
    chip.className = 'bai-chip';
    chip.textContent = c;
    chip.addEventListener('click', function () { ask(c); });
    chipsEl.appendChild(chip);
  });

  btn.addEventListener('click', function () { ask(); });
  input.addEventListener('keydown', function (e) {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); ask(); }
  });
  input.addEventListener('input', function () {
    input.style.height = 'auto';
    input.style.height = Math.min(input.scrollHeight, 110) + 'px';
  });

  var css = document.createElement('style');
  css.textContent =
    '#bookAi{max-width:640px;margin:40px auto;padding:0 20px;font-family:inherit}' +
    '#bookAi h2{font-size:22px;text-align:center;margin-bottom:6px}' +
    '#bookAi .bai-intro{text-align:center;color:#667;font-size:14px;margin:0 0 16px}' +
    '#bookAi .bai-log{display:flex;flex-direction:column;gap:10px;background:#f7f9fc;border:1px solid #dde5f0;border-radius:12px;min-height:60px;max-height:380px;overflow-y:auto;padding:14px;margin-bottom:10px}' +
    '#bookAi .bai-log:empty{display:none}' +
    '.bai-msg{max-width:88%;padding:10px 14px;border-radius:10px;font-size:14px;line-height:1.55}' +
    '.bai-user{background:#1a73e8;color:#fff;align-self:flex-end;border-bottom-right-radius:3px;white-space:pre-wrap}' +
    '.bai-assistant{background:#fff;border:1px solid #dde5f0;align-self:flex-start;border-bottom-left-radius:3px}' +
    '.bai-assistant p{margin:0 0 8px}.bai-assistant ul{margin:6px 0;padding-left:18px}.bai-assistant strong{color:#1a56db}' +
    '.bai-typing{color:#889;font-style:italic}' +
    '.bai-disclaimer{font-size:11.5px;color:#99a;font-style:italic;border-top:1px solid #eef;padding-top:6px;margin-top:8px}' +
    '#bookAi .bai-inputrow{display:flex;gap:8px}' +
    '#bookAi textarea{flex:1;padding:11px 14px;border:1px solid #ccd6e4;border-radius:8px;font-family:inherit;font-size:14px;resize:none;min-height:44px;max-height:110px}' +
    '#bookAi textarea:focus{outline:none;border-color:#1a73e8}' +
    '#bookAi .bai-inputrow button{padding:11px 22px;background:#1a73e8;color:#fff;border:none;border-radius:8px;font-weight:600;font-size:14px;cursor:pointer}' +
    '#bookAi .bai-inputrow button:disabled{opacity:.5;cursor:not-allowed}' +
    '#bookAi .bai-chips{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px;justify-content:center}' +
    '.bai-chip{background:#fff;border:1px solid #ccd6e4;border-radius:100px;padding:6px 14px;font-size:13px;color:#556;cursor:pointer;font-family:inherit}' +
    '.bai-chip:hover{border-color:#1a73e8;color:#1a56db;background:#f0f6ff}' +
    '#bookAi .bai-status{font-size:13px;text-align:center;min-height:18px;margin-top:8px;color:#2e7d32}' +
    '#bookAi .bai-error{color:#c0392b}' +
    '.bai-lead{align-self:stretch;background:#f0f6ff;border:1px solid #c7dbf7;border-radius:10px;padding:14px;text-align:center}' +
    '.bai-lead-title{font-weight:700;margin:0 0 4px;font-size:15px}' +
    '.bai-lead-sub{font-size:12.5px;color:#556;margin:0 0 10px;line-height:1.45}' +
    '.bai-form{display:flex;gap:8px;justify-content:center;flex-wrap:wrap}' +
    '.bai-form input[type=email]{flex:1;min-width:180px;max-width:240px;padding:9px 12px;border:1px solid #b9c8dd;border-radius:6px;font-size:14px}' +
    '.bai-form button{padding:9px 18px;background:#1a73e8;color:#fff;border:none;border-radius:6px;font-weight:600;cursor:pointer}' +
    '@media(max-width:520px){#bookAi .bai-inputrow{flex-direction:column}#bookAi .bai-inputrow button{width:100%}.bai-msg{max-width:95%}}';
  document.head.appendChild(css);

  try { if (window.trackEvent) window.trackEvent('bookai-view'); } catch (e) {}
})();
