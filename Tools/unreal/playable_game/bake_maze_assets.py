"""Bake the captured prototype geometry through Unreal's editor APIs only."""
import gzip
import json
import unreal as ue

assert not ue.EditorLevelLibrary.get_pie_worlds(True)
source=ROOT/'SourceArt/HC/MazeIntegration/scene.json.gz'
scene=json.loads(gzip.decompress(source.read_bytes()))
base='/Game/Puzzles/Art/MazeIntegration'
start=ARGS.get('start',0)
end=ARGS.get('end',len(scene['components']))
report={'start':start,'end':end,'saved':[],'preserved_hidden_collision':[]}
for index,record in enumerate(scene['components']):
    if not start<=index<end or record['kind']!='procedural':
        continue
    path=base+f'/Meshes/SM_Maze_{index:04}'
    if ue.EditorAssetLibrary.does_asset_exist(path):
        continue
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
    report['saved'].append(path)
    if record['collision'] and not record.get('visible',True):
        report['preserved_hidden_collision'].append({'path':path,'source_hulls':len(record['convex_hulls']),'triangles':len(triangles)//3})
    ue.log('PLAYABLE_MAZE_BAKE: '+path)
RESULT={'saved_meshes':len(report['saved']),'hidden_collision_meshes':len(report['preserved_hidden_collision']),'report':f'Saved/PlayableGame/maze-bake-{start}-{end}.json'}
(QUEUE/f'maze-bake-{start}-{end}.json').write_text(json.dumps(report,indent=2))
