#!/usr/bin/env python3
"""Fuld live-check af alle sitemap-URL'er: status, canonical, JSON-LD-parse.
Kør: python3 tools/full_site_check.py  (bruger curl med UA; parallelt)."""
import re, json, subprocess, concurrent.futures as cf

SITEMAP = 'https://hermes-passiv.pages.dev/sitemap.xml'
UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Chrome/126'

def check(u):
    out = []
    try:
        p = subprocess.run(['curl', '-sL', '-A', UA, u], capture_output=True, timeout=30)
        html = p.stdout.decode('utf-8', 'ignore')
        m = re.search(r'rel="canonical" href="([^"]+)"', html)
        if not m or m.group(1) != u:
            out.append((u, 'canonical:' + str(m and m.group(1))))
        for blk in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S):
            try:
                json.loads(blk)
            except Exception as e:
                out.append((u, 'jsonld:' + str(e)[:60]))
        if '<title>' not in html:
            out.append((u, 'no title'))
    except Exception as e:
        out.append((u, str(e)[:60]))
    return out

def main():
    sm = subprocess.run(['curl', '-sL', '-A', UA, SITEMAP], capture_output=True).stdout.decode()
    urls = re.findall(r'<loc>(.*?)</loc>', sm)
    bad = []
    with cf.ThreadPoolExecutor(12) as ex:
        for res in ex.map(check, urls):
            bad += res
    print(len(urls), 'urls checked')
    print('problems:', len(bad))
    for b in bad:
        print(b)

if __name__ == '__main__':
    main()
