"""Fix hreflang problems found by tools/hreflang_audit.py (iter 494).

Rules:
- Paired pages (DA <-> EN mirror): both sides get the full set
  x-default=EN, da=DA-url, en=EN-url.
- DA-only page (no EN mirror): full self-referential set x-default=da=self, da, en? No —
  correct per Google: only list languages that exist. Self set = da + x-default(self).
- EN-only page: x-default(en)=self, en=self.
- blog/index.html and other non-article pages: leave alone (index pages are not
  alternates of each other here unless paired; handled by pair map below).
"""
import glob, os, re

BASE='https://hermes-passiv.pages.dev'
SITE=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),'site')
ALT=re.compile(r'<link rel="alternate" hreflang="[^"]+" href="[^"]+">\n?')
CANON=re.compile(r'<link rel="canonical" href="([^"]+)"')

def read(f): return open(f).read()
def write(f,c): open(f,'w').write(c)

def strip_alts(c):
    return ALT.sub('', c)

def insert_alts(c, links):
    """Insert hreflang links right after the canonical link line."""
    m=CANON.search(c)
    assert m, 'no canonical'
    end=c.index('>', m.start())+1
    block=''.join('<link rel="alternate" hreflang="%s" href="%s">\n'%(k,v) for k,v in links)
    return c[:end]+'\n'+block+c[end:]

def set_canon(c, url):
    return CANON.sub('<link rel="canonical" href="%s"'%url, c, count=1)

changed=[]

# --- 1. Fix pairs where one/both sides lack the full set ---
da_files=sorted(glob.glob(SITE+'/da/blog/*.html'))
en_files={os.path.basename(f)[:-5]: f for f in glob.glob(SITE+'/blog/*.html')}

for f in da_files:
    slug=os.path.basename(f)[:-5]
    self_url=BASE+'/da/blog/'+slug
    c=read(f)
    links=dict(re.findall(r'<link rel="alternate" hreflang="([^"]+)" href="([^"]+)"',c))
    en_slug=None
    if 'en' in links and '/blog/' in links['en']:
        en_slug=links['en'].replace(BASE+'/blog/','').strip('/')
    if not en_slug or en_slug not in en_files:
        continue
    ef=en_files[en_slug]
    ec=read(ef)
    elinks=dict(re.findall(r'<link rel="alternate" hreflang="([^"]+)" href="([^"]+)"',ec))
    want={'x-default':links['en'],'da':self_url,'en':links['en']}
    ewant={'x-default':links['en'],'da':self_url,'en':links['en']}
    if links!=want:
        c=set_canon(strip_alts(c), self_url)
        c=insert_alts(c, sorted(want.items(), key=lambda kv:['x-default','da','en'].index(kv[0])))
        write(f,c); changed.append((f,str(links)+'->full'))
    if elinks!=ewant:
        ec=set_canon(strip_alts(ec), links['en'])
        ec=insert_alts(ec, sorted(ewant.items(), key=lambda kv:['x-default','da','en'].index(kv[0])))
        write(ef,ec); changed.append((ef,str(elinks)+'->full'))

# --- 2. Pages with no hreflang at all: add correct self/pair set ---
for f in da_files+sorted(glob.glob(SITE+'/blog/*.html')):
    slug=os.path.basename(f)[:-5]
    is_da='/da/blog/' in f
    if is_da:
        self_url=BASE+'/da/blog/'+slug
    else:
        self_url=BASE+'/blog/'+slug
    c=read(f)
    if 'rel="alternate" hreflang' in c:
        continue
    # skip index pages (not article alternates)
    if slug=='index':
        continue
    # find pair partner by filename match or by existing references?
    # For unpaired singles: self-referential set for own lang only.
    if is_da:
        links=[('x-default',self_url),('da',self_url)]
        # check whether an EN file with same slug exists -> treat as pair
        partner=SITE+'/blog/'+slug+'.html'
        if os.path.exists(partner):
            pc=read(partner)
            plinks=dict(re.findall(r'<link rel="alternate" hreflang="([^"]+)" href="([^"]+)"',pc))
            if not plinks:
                links=[('x-default',self_url),('da',self_url),('en',BASE+'/blog/'+slug)]
                pc=set_canon(strip_alts(pc), BASE+'/blog/'+slug)
                pc=insert_alts(pc, links)
                write(partner,pc); changed.append((partner,'added pair full set'))
        else:
            pass  # DA-only: keep x-default pointing at itself (allowed; x-default may point anywhere)
    else:
        links=[('x-default',self_url),('en',self_url)]
    c=set_canon(strip_alts(c), self_url)
    c=insert_alts(c, links)
    write(f,c); changed.append((f,'added '+str(links)))

print('files changed:',len(changed))
for f,note in changed: print(os.path.relpath(f,SITE), note)
