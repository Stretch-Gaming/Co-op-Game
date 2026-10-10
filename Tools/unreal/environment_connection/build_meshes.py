import gzip,json,unreal as ue
scene=json.loads(gzip.decompress((ROOT/'SourceArt/HC/EnvironmentConnection/connection.json.gz').read_bytes()))
base='/Game/Puzzles/EnvironmentConnection/Art'
saved=[]
for r in scene['components']:
 if not r.get('clipped'):continue
 path=base+'/SM_Connection_'+str(r['source_index'])
 if ue.EditorAssetLibrary.does_asset_exist(path):continue
 dynamic=ue.DynamicMesh();b=ue.GeometryScriptSimpleMeshBuffers()
 b.vertices=[ue.Vector(*v)for v in r['vertices']];b.normals=[ue.Vector(*v)for v in r['normals']]
 b.uv0=[ue.Vector2D(*v)for v in r['uvs']];b.vertex_colors=[ue.LinearColor(*v)for v in r['vertex_colors']]
 t=r['triangles'];b.triangles=[ue.IntVector(*t[i:i+3])for i in range(0,len(t),3)]
 ue.GeometryScript_MeshEdits.append_buffers_to_mesh(dynamic,b)
 opt=ue.GeometryScriptCreateNewStaticMeshAssetOptions();opt.enable_nanite=False;opt.enable_collision=r['collision'];opt.collision_mode=ue.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE
 mesh,result=ue.GeometryScript_NewAssetUtils.create_new_static_mesh_asset_from_mesh(dynamic,path,opt);assert mesh,(path,result)
 assert ue.EditorAssetLibrary.save_loaded_asset(mesh,False)
 saved.append(path);ue.log('CONNECTED_ENV_MESH: '+path)
RESULT={'saved':saved,'count':len(saved)}
(OUTPUT/'mesh-build.json').write_text(json.dumps(RESULT,indent=2))
