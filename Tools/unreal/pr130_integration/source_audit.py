"""Compare the authored maze captures before choosing a minimal refresh."""
import collections, gzip, hashlib, json
from pathlib import Path
root=Path(__file__).resolve().parents[3]
old=json.loads(gzip.decompress((root/'SourceArt/HC/EnvironmentConnection/connection.json.gz').read_bytes()))
new=json.loads(gzip.decompress((root/'SourceArt/HC/EnvironmentConnection/Refresh_fd40cdeb/connection.json.gz').read_bytes()))
key=lambda r:(r['kind'],r['name'])
oldmap={key(r):r for r in old['components']};newmap={key(r):r for r in new['components']}
assert len(oldmap)==len(old['components']) and len(newmap)==len(new['components']), 'Ambiguous names'
def digest(r,fields):
    return hashlib.sha256(json.dumps({k:r.get(k) for k in fields},sort_keys=True,separators=(',',':')).encode()).hexdigest()
geometry=('vertices','triangles','normals','uvs','vertex_colors','instances','mesh','location','rotation','scale','collision','visible','color','tint','material')
changed=[{'kind':k[0],'name':k[1],'old_index':oldmap[k]['source_index'],'new_index':newmap[k]['source_index']} for k in oldmap.keys()&newmap.keys() if digest(oldmap[k],geometry)!=digest(newmap[k],geometry)]
report={'old_records':len(oldmap),'new_records':len(newmap),'changed_by_kind':dict(collections.Counter(x['kind'] for x in changed)),
        'changed':changed,'added':[{'kind':k[0],'name':k[1],'index':newmap[k]['source_index']} for k in newmap.keys()-oldmap.keys()],
        'removed':[{'kind':k[0],'name':k[1],'index':oldmap[k]['source_index']} for k in oldmap.keys()-newmap.keys()],
        'floor_geometry':[{ 'old_index':i,'name':r['name'],'new_index':newmap[key(r)]['source_index'] if key(r) in newmap else None,
            'positions_unchanged':key(r) in newmap and digest(r,('vertices','triangles'))==digest(newmap[key(r)],('vertices','triangles'))} for i in range(318,323) for r in old['components'] if r['source_index']==i]}
out=root/'Saved/PR130Integration';out.mkdir(parents=True,exist_ok=True)
(out/'source-audit.json').write_text(json.dumps(report,indent=2))
print(json.dumps({k:v for k,v in report.items() if k!='changed'},indent=2))
