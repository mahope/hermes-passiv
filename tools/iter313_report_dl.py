#!/usr/bin/env python3
"""Iter 313: add 'Download report (.md)' button to compliance-site-check result views.

Client-side only: builds a Markdown report from the scan data and downloads it via
Blob. No server, no email, no account. Idempotent via marker.
"""
import re

MARKER = '<!-- iter313 report-dl -->'

EN_SNIPPET = '''
  // iter313: download report as Markdown (client-side, no server)
  var lastScan = null;
  function downloadReport(data) {
    var lines = [];
    lines.push('# Compliance Report — ' + data.url);
    lines.push('');
    lines.push('Score: **' + data.score + '/100** (' + data.grade + ') · ' + data.passed + '/' + data.total + ' checks passed');
    lines.push('Scanned: ' + new Date().toISOString().slice(0, 10) + ' · via hermes-passiv.pages.dev/compliance-site-check');
    lines.push('');
    var all = [];
    if (data.results) { for (var k in data.results) { data.results[k].forEach(function(r){ all.push(r); }); } }
    var icons = { pass: 'PASS', warn: 'WARN', info: 'INFO', fail: 'FAIL' };
    all.forEach(function(r) {
      lines.push('- [' + (icons[r.status] || r.status.toUpperCase()) + '] ' + (r.label || r.key) + ' — ' + (r.details || ''));
    });
    lines.push('');
    lines.push('Fix each FAIL above, then re-scan. Free GitHub Action for CI: https://github.com/mahope/compliance-site-check');
    var blob = new Blob([lines.join('\\n')], { type: 'text/markdown' });
    var a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'compliance-report-' + (data.url || '').replace(/^https?:\\/\\//, '').replace(/[^a-z0-9.-]/gi, '') + '.md';
    document.body.appendChild(a); a.click(); document.body.removeChild(a);
    setTimeout(function(){ URL.revokeObjectURL(a.href); }, 1000);
  }
'''

def patch(path, btn_label, title):
    with open(path) as f:
        html = f.read()
    if MARKER in html:
        return path + ': already'
    # 1) insert helpers before renderResults definition
    anchor = 'function renderResults(data)'
    if anchor not in html:
        return path + ': no-anchor'
    html = html.replace(anchor, EN_SNIPPET.replace('iter313', 'iter313') + '\n' + anchor, 1)
    # 2) store lastScan and append download button into score row
    html = html.replace(
        "html += '<div class=\"score-detail\"><strong>'",
        "lastScan = data;\n  html += '<div class=\"score-detail\"><strong>'",
        1)
    html = html.replace(
        "html += '</div>';\n\n  // Group results",
        "html += '</div>';\n  html += '<div style=\"margin:0 0 16px\"><button id=\"dlReport\" onclick=\"downloadReport(lastScan)\" style=\"padding:8px 16px;background:#fff;border:1px solid #d1d5db;border-radius:8px;font-size:13px;cursor:pointer\">%s</button></div>';\n\n  // Group results" % btn_label,
        1)
    html = html.replace('</head>', MARKER + '\n</head>', 1)
    with open(path, 'w') as f:
        f.write(html)
    return path + ': patched'

print(patch('site/compliance-site-check.html', '⬇ Download report (.md)', 'Download report'))
print(patch('site/da/compliance-site-check.html', '⬇ Download rapport (.md)', 'Download rapport'))
