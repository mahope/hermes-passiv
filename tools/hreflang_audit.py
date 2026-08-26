import glob, re, os
BASE='https://hermes-passiv.pages.dev'
SITE='/Users/madsholstjensen/hermes-passiv/site'
FULL={'x-default','da','en'}
bad=[]
pairs=0; singles_da=0; singles_en=0

# --- DA pages: must have complete set pointing at EN mirror + self ---
da_en={}  # en_slug -> da_slug (from each DA page's hreflang=en)
for f in sorted(glob.glob(SITE+'/da/blog/*.html')):
    c=open(f).read()
    links=dict(re.findall(r'<link rel="alternate" hreflang="([^"]+)" href="([^"]+)"',c))
    m=re.search(r'<link rel="canonical" href="([^"]+)"',c)
    canon=m.group(1) if m else '?'
    self_url=BASE+'/da/blog/'+os.path.basename(f)[:-5]
    if not links or set(links)=={'x-default'} and links['x-default'].endswith(os.path.basename(f)[:-5]):
        singles_da+=1
        continue
    # DA-only page: self-referential set {x-default:self, da:self} is valid
    if links=={'x-default':self_url,'da':self_url}:
        if canon!=self_url: bad.append((f,'canonical=%s expected %s'%(canon,self_url)))
        singles_da+=1
        continue
    if 'en' not in links:
        bad.append((f,'has hreflang but no en link: %s'%links)); continue
    en_url=links['en']; en_slug=en_url.replace(BASE+'/blog/','').strip('/')
    if links=={'x-default':en_url}:
        # lone x-default pointing at EN mirror: treat as pair candidate, complete it
        pass
    want={'x-default':en_url,'da':self_url,'en':en_url}
    if links!=want: bad.append((f,'hreflang %s want %s'%(links,want)))
    if canon!=self_url: bad.append((f,'canonical=%s expected %s'%(canon,self_url)))
    if da_en.setdefault(en_slug, os.path.basename(f)[:-5]) != os.path.basename(f)[:-5]:
        bad.append((f,'two DA pages claim EN mirror '+en_slug))
    # EN side
    en_path=SITE+'/blog/'+en_slug+'.html'
    if not os.path.exists(en_path):
        bad.append((f,'EN mirror missing: '+en_path)); continue
    ce=open(en_path).read()
    le=dict(re.findall(r'<link rel="alternate" hreflang="([^"]+)" href="([^"]+)"',ce))
    me=re.search(r'<link rel="canonical" href="([^"]+)"',ce)
    ec=me.group(1) if me else '?'
    we={'x-default':en_url,'da':self_url,'en':en_url}
    if le!=we: bad.append((en_path,'hreflang %s want %s'%(le,we)))
    if ec!=en_url: bad.append((en_path,'canonical=%s expected %s'%(ec,en_url)))
    pairs+=1

# --- remaining EN pages: either no hreflang (fine) or complete self-set ---
paired_en={BASE+'/blog/'+s for s in da_en}
for f in sorted(glob.glob(SITE+'/blog/*.html')):
    url=BASE+'/blog/'+os.path.basename(f)[:-5]
    if url in paired_en: continue
    le=dict(re.findall(r'<link rel="alternate" hreflang="([^"]+)" href="([^"]+)"',open(f).read()))
    if not le:
        singles_en+=1
    # EN-only page: self-referential set {x-default:self, en:self} is valid
    elif le=={'x-default':url,'en':url}:
        singles_en+=1
    elif set(le)==FULL and le['en']==url and le['x-default']==url:
        pass  # self-referential full set on EN-only page is valid
    else:
        bad.append((f,'EN-only page with non-standard set %s'%le))
for b in bad: print(b)
print('pairs:',pairs,'da-no-hreflang:',singles_da,'en-only-no-hreflang:',singles_en,'problems:',len(bad))
