"""Bake the captured prototype geometry through Unreal's editor APIs only."""
import gzip
import json
import unreal as ue
import sys
import importlib
import hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import scene_ops;importlib.reload(scene_ops)
from scene_ops import scene as read_scene
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from authoring import guard
guard()

assert not ue.EditorLevelLibrary.get_pie_worlds(True)
source=ROOT/'SourceArt/HC/EnvironmentConnection/connection.json.gz'
scene=read_scene(ROOT)
base='/Game/Hazards/Art/SixRoundConnection'
start=ARGS.get('start',316)
end=ARGS.get('end',len(scene['components']))
report={'start':start,'end':end,'saved':[],'preserved_hidden_collision':[]}
ledger_path=QUEUE/'world-connection-bake-ledger.json'
pipeline={'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'scene_ops_sha256':hashlib.sha256(Path(__file__).with_name('scene_ops.py').read_bytes()).hexdigest(),'namespace':base}
ledger=json.loads(ledger_path.read_text()) if ledger_path.exists() else {'assets':{}}
assert isinstance(ledger.get('assets'),dict)
report['pipeline']=pipeline
report['reused']=[]
for index,record in enumerate(scene['components']):
    if not start<=index<end or record['kind']!='procedural' or not record['triangles']:
        continue
    path=base+f'/Meshes/SM_Maze_{index:04}'
    fingerprint={**pipeline,'record_sha256':hashlib.sha256(json.dumps(record,sort_keys=True,separators=(',',':')).encode()).hexdigest()}
    if ue.EditorAssetLibrary.does_asset_exist(path):
        prior=ledger['assets'].get(path,{})
        if prior==fingerprint or (prior.get('source_sha256')==fingerprint['source_sha256'] and prior.get('record_sha256')==fingerprint['record_sha256']):
            # Identical normalized mesh input remains valid when unrelated cuts change.
            ledger['assets'][path]=fingerprint
            ledger_path.write_text(json.dumps(ledger,indent=2))
            report['reused'].append(path)
            continue
        assert ARGS.get('rebuild_changed_meshes',False),'Stale/unverified new HZ bake mesh '+path+'; review source/cuts and pass rebuild_changed_meshes=true to rebuild only this namespace through editor'
        assert path.startswith('/Game/Hazards/Art/SixRoundConnection/Meshes/SM_Maze_')
        assert ue.EditorAssetLibrary.delete_asset(path),path
    dynamic=ue.DynamicMesh()
    buffers=ue.GeometryScriptSimpleMeshBuffers()
    buffers.vertices=[ue.Vector(*v) for v in record['vertices']]
    buffers.normals=[ue.Vector(*v) for v in record['normals']]
    buffers.uv0=[ue.Vector2D(*v) for v in record['uvs']]
    buffers.vertex_colors=[ue.LinearColor(*v) for v in record['vertex_colors']]
    triangles=record['triangles']
    buffers.triangles=[ue.IntVector(*triangles[i:i+3]) for i in range(0,len(triangles),3)]
    ue.GeometryScript_MeshEdits.append_buffers_to_mesh(dynamic,buffers)
    options=ue.GeometryScriptCreateNewStaticMeshAssetOptions()
    options.enable_nanite=False
    options.enable_collision=record['collision']
    options.collision_mode=ue.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE
    mesh,outcome=ue.GeometryScript_NewAssetUtils.create_new_static_mesh_asset_from_mesh(dynamic,path,options)
    assert mesh,(path,outcome)
    assert ue.EditorAssetLibrary.save_loaded_asset(mesh,False)
    ledger['assets'][path]=fingerprint
    ledger['pipeline']=pipeline
    ledger_path.write_text(json.dumps(ledger,indent=2))
    report['saved'].append(path)
    if record['collision'] and not record.get('visible',True):
        report['preserved_hidden_collision'].append({'path':path,'source_hulls':len(record['convex_hulls']),'triangles':len(triangles)//3})
    ue.log('PLAYABLE_MAZE_BAKE: '+path)
RESULT={'saved_meshes':len(report['saved']),'hidden_collision_meshes':len(report['preserved_hidden_collision']),'report':f'Saved/SixRound/maze-bake-{start}-{end}.json','runtime_acceptance_pending':True}
(QUEUE/f'maze-bake-{start}-{end}.json').write_text(json.dumps(report,indent=2))
