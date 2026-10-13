"""Prepare private maze derivatives from the exact team capture; no Unreal writes."""
import copy,gzip,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(Path(__file__).resolve().parent))
from layout import plan,SOURCE,SOURCE_SHA256
sys.path.insert(0,str(ROOT/'Tools/unreal/six_round/world'))
from scene_ops import subtract_box
def prepare(root=ROOT):
    source=root/SOURCE;assert hashlib.sha256(source.read_bytes()).hexdigest()==SOURCE_SHA256
    data=json.loads(gzip.decompress(source.read_bytes()));data=copy.deepcopy(data)
    layout=plan(root);records=[];removed=[]
    for r in data['components']:
        i=r['source_index']
        if i in (701,702,703) or (r.get('mesh','').endswith('Cube.Cube') and r.get('location')==[-675.0,11750,-1500] and r.get('scale')==[220,275,1]):
            removed.append(i);continue
        if i in (697,698,699,700) or r.get('mesh','').endswith('SM_ChamberGate_Frame.SM_ChamberGate_Frame'):r['collision']=False
        if r['kind']=='procedural' and not r['triangles']:continue
        records.append(r)
    indexed={r['source_index']:r for r in records}
    for gap in layout['gaps']:
        r=indexed[gap['source_floor']]
        for cut in gap['cuts']:
            loc=r['location'];subtract_box(r,[cut['lo'][k]-loc[k] for k in range(3)],[cut['hi'][k]-loc[k] for k in range(3)])
    # No old HallB subtraction, manufactured return gaps or exterior door cuts.
    return {'components':records,'source_sha256':SOURCE_SHA256,'layout':layout,
            'removed_partner_blocks_and_backstop':removed,'original_hall_b_restored':True,
            'source_assets_modified':False,'native_collision_verified':False}
if __name__=='__main__':
    out=ROOT/'Saved/MazeLevel';out.mkdir(parents=True,exist_ok=True)
    data=prepare();packed=gzip.compress(json.dumps(data,separators=(',',':')).encode(),mtime=0)
    (out/'scene.json.gz').write_bytes(packed)
    (out/'layout.json').write_text(json.dumps(data['layout'],indent=2))
    print(json.dumps({'records':len(data['components']),'procedural_meshes':sum(r['kind']=='procedural' for r in data['components']),
        'layout':data['layout']['offline_checks'],'prepared_sha256':hashlib.sha256(packed).hexdigest()},indent=2))
