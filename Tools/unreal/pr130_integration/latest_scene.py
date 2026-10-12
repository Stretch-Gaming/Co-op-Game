"""Use PK's exact PR122 scenery, retaining the existing six-round cuts only."""
import copy, gzip, hashlib, importlib, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
SOURCE=ROOT/'SourceArt/HC/EnvironmentConnection/Refresh_fd40cdeb/connection.json.gz'
EXPECTED='2008b7a684ba0f82d34b97fe259c20ec7abc46e09d00ead5f9c1dd8c6fcbf0ed'
sys.path.insert(0,str(ROOT/'Tools/unreal/six_round/world'))
import scene_ops

def source_scene(root):
    assert root==ROOT and hashlib.sha256(SOURCE.read_bytes()).hexdigest()==EXPECTED
    data=json.loads(gzip.decompress(SOURCE.read_bytes()))
    assert len(data['components'])==563
    records=[{'kind':'excluded','name':'Excluded_'+str(i),'source_index':i} for i in range(919)]
    removed=[];frames=[]
    for r in data['components']:
        i=r['source_index']
        assert i!=912
        if i in (701,702,703):
            assert r['kind']=='static' and r['mesh']=='/Engine/BasicShapes/Cube.Cube'
            removed.append(i);continue
        if r['kind']=='static' and r['mesh']=='/Engine/BasicShapes/Cube.Cube' and r['location']==[-675.0,11750,-1500] and r['scale']==[220,275,1]:
            removed.append(i);continue
        if i in (697,698,699,700):
            assert r['kind']=='static' and r['mesh']=='/Engine/BasicShapes/Cube.Cube'
            r['collision']=False
        if r.get('mesh','').endswith('SM_ChamberGate_Frame.SM_ChamberGate_Frame'):
            r['collision']=False;frames.append(i)
        r['location'][0]+=175
        for instance in r.get('instances',[]):instance['location'][0]+=175
        records[i]=r
    assert len(removed)==4 and len(frames)==4, (removed,frames)
    for i in range(318,323):assert records[i]['kind']=='procedural'
    return {'components':records,'metadata':data['metadata'],'source_records':563,
            'source_sha256':EXPECTED,'removed_original_partner_blocks_and_backstop':removed,'dressing_frames':frames}

def scene(root=ROOT):
    ops=importlib.reload(scene_ops)
    ops.source_scene=source_scene
    # Preserve the established doorway clearance through the newer collision shell.
    # Keep the five floor meshes exempt from those doorway cuts, as before.
    for i in range(3,len(ops.CUTS)):
        lo,hi=ops.CUTS[i];ops.CUTS[i]=([lo[0],lo[1],580],hi)
    data=ops.scene(root)
    shell=data['components'][890]
    assert shell['kind']=='procedural' and not shell.get('visible',True) and shell['collision']
    # New hidden rock collision overlaps the existing meeting-hall exit approach.
    # Adapt that collision shell only; keep artist visuals and gameplay placements.
    ops.subtract_box(shell,[-350,9600,-350],[100,9950,0])
    data['meeting_exit_collision_clearance']={'source_index':890,'lo':[-350,9600,-350],'hi':[100,9950,0]}
    return data

if __name__=='__main__':
    data=scene()
    out=ROOT/'Saved/PR130Integration';out.mkdir(parents=True,exist_ok=True)
    packed=gzip.compress(json.dumps(data,separators=(',',':')).encode(),mtime=0)
    (out/'latest-sixround-scene.json.gz').write_bytes(packed)
    print(json.dumps({'records':sum(r['kind']!='excluded' for r in data['components']),
                      'procedural':sum(r['kind']=='procedural' and bool(r['triangles']) for r in data['components']),
                      'source_sha256':data['source_sha256'],'derivative_sha256':hashlib.sha256(packed).hexdigest()}))
