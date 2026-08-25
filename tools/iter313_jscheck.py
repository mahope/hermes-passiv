import re
for p in ['site/compliance-site-check.html', 'site/da/compliance-site-check.html']:
    html = open(p).read()
    scripts = re.findall(r'<script>(.*?)</script>', html, re.S)
    js = '\n;\n'.join(s for s in scripts if 'downloadReport' in s or 'renderResults' in s)
    open('/tmp/chk.js', 'w').write(
        'var document,window,fetch,URL,Blob,navigator,location,setTimeout;' + js)
    print(p, 'extracted', len(js), 'chars')
