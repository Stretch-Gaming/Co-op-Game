"""Update one new HC collision mesh; original team assets remain untouched."""
import gzip,hashlib,json
import unreal as ue
scene=json.loads(gzip.decompress((QUEUE/'latest-sixround-scene.json.gz').read_bytes()))
r=scene['components'][890]
assert not r['visible'] and r['collision']
path='/Game/Puzzles/Art/PR130Maze/SM_PR130Maze_0890'
mesh=ue.load_asset(path);assert mesh
buffers=ue.GeometryScriptSimpleMeshBuffers()
buffers.vertices=[ue.Vector(*v) for v in r['vertices']];buffers.normals=[ue.Vector(*v) for v in r['normals']]
buffers.uv0=[ue.Vector2D(*v) for v in r['uvs']];buffers.vertex_colors=[ue.LinearColor(*v) for v in r['vertex_colors']]
t=r['triangles'];buffers.triangles=[ue.IntVector(*t[i:i+3]) for i in range(0,len(t),3)]
dynamic=ue.DynamicMesh();ue.GeometryScript_MeshEdits.append_buffers_to_mesh(dynamic,buffers)
result,outcome=ue.GeometryScript_AssetUtils.copy_mesh_to_static_mesh(dynamic,mesh,ue.GeometryScriptCopyMeshToAssetOptions(),ue.GeometryScriptMeshWriteLOD())
assert outcome==ue.GeometryScriptOutcomePins.SUCCESS, outcome
assert ue.EditorAssetLibrary.save_loaded_asset(mesh,False)
report=json.loads((QUEUE/'maze-refresh.json').read_text())
for row in report['meshes']:
    if row['source_index']==890:row['record_sha256']=hashlib.sha256(json.dumps(r,sort_keys=True,separators=(',',':')).encode()).hexdigest()
report['collision_clearance']=scene['meeting_exit_collision_clearance']
(QUEUE/'maze-refresh.json').write_text(json.dumps(report,indent=2))
RESULT={'mesh':path,'outcome':str(outcome),'collision_only':True,'original_assets_changed':False}
