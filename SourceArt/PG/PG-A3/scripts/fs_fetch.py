#!/usr/bin/env python3
"""Fetch a Freesound page + public HQ preview into downloads/PG-A3-taking/freesound/<id>-<user>/.
Prints license, author, title, original format, and description head. Never executes downloads."""
import html, json, re, sys, urllib.request
from pathlib import Path
DL = Path('/Users/peterkim/CoopGameArt/downloads/PG-A3-taking/freesound')
UA = {'User-Agent': 'Mozilla/5.0'}
def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read()
meta = {}
for arg in sys.argv[1:]:
    user, sid = arg.split('/')
    page_url = f'https://freesound.org/people/{user}/sounds/{sid}/'
    d = DL / f'{sid}-{user}'
    d.mkdir(parents=True, exist_ok=True)
    page = d / 'source-page.html'
    if not page.exists():
        page.write_bytes(get(page_url))
    t = page.read_text('utf-8', 'replace')
    lic = re.findall(r'href="(https?://creativecommons\.org/[^"]+)"', t)
    lic = sorted(set(l for l in lic if 'licenses' in l or 'publicdomain' in l))
    mp3 = re.search(r'data-mp3="([^"]+)"', t).group(1).replace('-lq.mp3', '-hq.mp3')
    title = html.unescape(re.search(r'data-title="([^"]*)"', t).group(1))
    desc = re.search(r'<div id="soundDescriptionSection"[^>]*>(.*?)</div>', t, re.S) or re.search(r'class="[^"]*sound-description[^"]*"[^>]*>(.*?)</div>', t, re.S)
    desc = re.sub(r'<[^>]+>', ' ', html.unescape(desc.group(1))) if desc else ''
    desc = ' '.join(desc.split())[:300]
    fmt = re.findall(r'<dt[^>]*>\s*(Type|Duration|File size|Sample rate|Bit depth|Channels)\s*</dt>\s*<dd[^>]*>(.*?)</dd>', t, re.S)
    fmt = {k: ' '.join(re.sub('<[^>]+>', '', v).split()) for k, v in fmt}
    out = d / mp3.rsplit('/', 1)[1]
    if not out.exists():
        out.write_bytes(get(mp3))
    meta[sid] = dict(user=user, title=title, page=page_url, download=mp3, path=str(out), license_links=lic, original=fmt, description=desc)
    print(f'{sid} {user} | {title} | {lic} | {fmt} | {desc[:200]}')
mf = DL / 'meta.json'
old = json.loads(mf.read_text()) if mf.exists() else {}
old.update(meta)
mf.write_text(json.dumps(old, indent=1))
