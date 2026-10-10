"""Editor-only staged scenery refresh. Dry run by default; primary owns execution.
Requires ROOT and ARGS supplied by the primary's guarded editor runner.
"""
import gzip, hashlib, json, pathlib, sys
import unreal as ue
from editor_toolset.toolsets.actor import ActorTools
EXPECTED_ROOT=pathlib.Path('C:/Users/Stretch/.codex/worktrees/one-playable-game/Co op Game').resolve()
assert pathlib.Path(ROOT).resolve()==EXPECTED_ROOT,'Wrong checkout'
assert pathlib.Path(ue.Paths.project_dir()).resolve()==EXPECTED_ROOT,'Editor belongs to a different project'
TOOL=EXPECTED_ROOT/'Tools/unreal/connection_refresh'
sys.path.insert(0,str(TOOL));import prepare
from preservation import signature,first_difference
assert not ue.EditorLevelLibrary.get_pie_worlds(True),'Stop PIE before refresh'
MAP='/Game/Maps/L_ConnectedRoomMaze';SUB='/Game/Puzzles/EnvironmentConnection/L_ConnectedMaze'
world=ue.get_editor_subsystem(ue.UnrealEditorSubsystem).get_editor_world()
assert world.get_outermost().get_name()==MAP,'Open connected map explicitly; this script never changes maps'
stream=ue.GameplayStatics.get_streaming_level(world,'L_ConnectedMaze');assert stream and stream.get_loaded_level()
level=stream.get_loaded_level();assert level.get_outermost().get_name()==SUB
assert sorted(l.get_outermost().get_name()for l in ue.EditorLevelUtils.get_levels(world))==sorted([MAP,'/Game/Hazards/L_Site01_HZ',SUB]),'Unexpected loaded gameplay levels'
actors=ue.get_editor_subsystem(ue.EditorActorSubsystem)
allactors=list(actors.get_all_level_actors())
# The room is shared with the active adventure. Refuse to enable or suppress traps implicitly.
for actor in allactors:
 cls=actor.get_class().get_path_name()
 assert not any(x in cls for x in ('BP_AdventureTrap','BP_SixRound','BP_FallVolume','BP_GhostSpawner','BP_RoundDirector')),'Active gameplay actor present: '+cls
report=json.loads((EXPECTED_ROOT/'Saved/ConnectionRefresh/audit.json').read_text())
assert prepare.protected()==report['protected_sha256'],'Protected maps/source changed since preparation; re-audit'
raw=(EXPECTED_ROOT/'Saved/ConnectionRefresh/connection-draft.json.gz').read_bytes()
assert hashlib.sha256(raw).hexdigest()==report['draft_sha256'],'Draft hash mismatch'
scene=json.loads(gzip.decompress(raw));base=scene['metadata']['private_asset_base']
assert base=='/Game/Puzzles/EnvironmentConnection/Refresh_fd40cdeb'
assert scene['metadata']['excluded_non_environment_volumes']==[912]
assert not any(prepare.huge_query_box(r)for r in scene['components'])
owned=[a for a in allactors if a.get_level()==level and a.get_actor_label().startswith('Connected_Maze_')]
assert len(owned)==561,'Existing scenery census changed; re-audit'
assert all(a.actor_has_tag('ConnectedEnvironment')for a in owned)
preserved=[a for a in allactors if a not in owned]
before=[signature(a)for a in preserved]
owned_before=[signature(a)for a in owned]
def verify_preserved(stage):
 after=[signature(a)for a in preserved];difference=first_difference(before,after)
 if difference:
  (EXPECTED_ROOT/'Saved/ConnectionRefresh/preservation-difference.json').write_text(json.dumps({'stage':stage,'first_difference':difference},indent=2))
  raise AssertionError('Preserved actor changed; see preservation-difference.json')
# Staging can mark a parent package dirty without changing its saved file.
# Record this state; never clear flags or save these protected packages.
protected_dirty_before=[p.get_name()for p in ue.EditorLoadingAndSavingUtils.get_dirty_map_packages()if p.get_name()in (MAP,'/Game/Hazards/L_Site01_HZ')]
# Preflight dependencies before any asset or actor mutations.
for r in scene['components']:
 assert r['kind'] in ('procedural','static','point','instanced'),'Unexpected kind'
 if r['kind'] in ('static','instanced'):assert ue.load_asset(r['mesh']),r['mesh']
 if r.get('material'):assert ue.load_asset(r['material']),r['material']
RESULT={'dry_run':not ARGS.get('apply',False),'new_records':len(scene['components']),'old_records':len(owned),'preserved_actors':len(preserved),'private_root':base,'save_only':SUB,'protected_hashes_unchanged':True,'protected_dirty_map_packages_before':protected_dirty_before,'protected_packages_saved':False}
if ARGS.get('apply',False):
 tools=ue.AssetToolsHelpers.get_asset_tools();assets=[];material_cache={}
 def save(asset):
  assert asset.get_outermost().get_name().startswith(base+'/')
  assert ue.EditorAssetLibrary.save_loaded_asset(asset,False);assets.append(asset.get_path_name());return asset
 def duplicate(source,name):
  dest=base+'/Materials/'+name
  existing=ue.load_asset(dest)
  if existing:return existing
  return save(ue.EditorAssetLibrary.duplicate_asset(source,dest))
 masters={n:duplicate('/Game/Puzzles/Art/MazeIntegration/Materials/'+n,n)for n in ['M_MazeVertexLit','M_MazeVertexGlow']}
 def material(r):
  source=r.get('material')
  if source and not r.get('tint'):
   key=source
   if key not in material_cache:material_cache[key]=duplicate(source,'Source_'+hashlib.sha256(source.encode()).hexdigest()[:12])
   return material_cache[key]
  tint=r.get('tint',r.get('color',[1,1,1,1]));name='Tint_'+'_'.join(str(round(c*10000))for c in tint[:3])+('_Style'if r.get('tint')else'_Flat');path=base+'/Materials/'+name
  if name not in material_cache:
   obj=ue.load_asset(path)
   if not obj:
    parent=ue.load_asset(source or ('/Game/Shared/Style/MI_Stylized_Rock'if r.get('tint')else'/Engine/BasicShapes/BasicShapeMaterial'));assert parent
    obj=tools.create_asset(name,base+'/Materials',ue.MaterialInstanceConstant,ue.MaterialInstanceConstantFactoryNew());assert obj
    ue.MaterialEditingLibrary.set_material_instance_parent(obj,parent);ue.MaterialEditingLibrary.set_material_instance_vector_parameter_value(obj,'Tint'if r.get('tint')else'Color',ue.LinearColor(*tint));ue.MaterialEditingLibrary.update_material_instance(obj);save(obj)
   material_cache[name]=obj
  return material_cache[name]
 meshes={}
 for r in scene['components']:
  i=r['source_index']
  if r['kind']=='procedural':
   path=base+f'/Meshes/SM_Refresh_{i:04}';mesh=ue.load_asset(path)
   if not mesh:
    buffers=ue.GeometryScriptSimpleMeshBuffers();buffers.vertices=[ue.Vector(*v)for v in r['vertices']];buffers.normals=[ue.Vector(*v)for v in r['normals']];buffers.uv0=[ue.Vector2D(*v)for v in r['uvs']];buffers.vertex_colors=[ue.LinearColor(*v)for v in r['vertex_colors']];t=r['triangles'];buffers.triangles=[ue.IntVector(*t[j:j+3])for j in range(0,len(t),3)]
    dynamic=ue.DynamicMesh();ue.GeometryScript_MeshEdits.append_buffers_to_mesh(dynamic,buffers)
    options=ue.GeometryScriptCreateNewStaticMeshAssetOptions();options.enable_nanite=False;options.enable_collision=r['collision'];options.collision_mode=ue.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE
    mesh,outcome=ue.GeometryScript_NewAssetUtils.create_new_static_mesh_asset_from_mesh(dynamic,path,options);assert mesh,(path,outcome);save(mesh)
   meshes[i]=mesh
  elif r['kind'] in ('static','instanced'):material(r)
 assert prepare.protected()==report['protected_sha256'],'Protected file changed during private asset build'
 ue.EditorLevelUtils.make_level_current(stream)
 def transform(r):
  p,y,l=r['rotation'];return ue.Transform(location=ue.Vector(*r['location']),rotation=ue.Rotator(pitch=p,yaw=y,roll=l),scale=ue.Vector(*r['scale']))
 staged=[]
 try:
  for r in scene['components']:
   i=r['source_index'];kind=r['kind'];tr=transform(r)
   cls=ue.PointLight if kind=='point'else ue.Actor if kind=='instanced'else ue.StaticMeshActor
   if kind=='instanced':tr=ue.Transform()
   a=actors.spawn_actor_from_class(cls,tr.translation,tr.rotation.rotator());assert a
   staged.append(a);assert a.get_level()==level;a.set_actor_scale3d(tr.scale3d);a.set_actor_label('Refresh_Staged_'+str(i));a.set_folder_path('Connected/Maze');a.tags=[ue.Name('ConnectedEnvironment'),ue.Name('ConnectionRefresh')]
   if kind=='point':
    c=a.get_component_by_class(ue.PointLightComponent);c.set_mobility(ue.ComponentMobility.MOVABLE);c.set_editor_property('intensity_units',ue.LightUnits.CANDELAS);c.set_editor_property('intensity',r['intensity']);c.set_editor_property('attenuation_radius',r['radius']);c.set_light_color(ue.LinearColor(*r['color']));c.set_editor_property('cast_shadows',r['shadow']);c.set_editor_property('max_draw_distance',5000.)
   else:
    c=ActorTools.add_component(a,ue.HierarchicalInstancedStaticMeshComponent.static_class(),'MazeRocks')if kind=='instanced'else a.static_mesh_component;c.set_mobility(ue.ComponentMobility.STATIC);c.set_static_mesh(meshes[i]if kind=='procedural'else ue.load_asset(r['mesh']));c.set_material(0,masters['M_MazeVertexGlow'if r.get('glow')else'M_MazeVertexLit']if kind=='procedural'else material(r));c.set_editor_property('cast_shadow',r.get('shadow',False));c.set_collision_profile_name('BlockAll'if r.get('collision',False)else'NoCollision')
    if kind=='instanced':
     for item in r['instances']:c.add_instance(transform(item),True)
    if not r.get('visible',True):a.set_actor_hidden_in_game(True)
  verify_preserved('before_old_scenery_removal')
  assert [signature(a)for a in owned]==owned_before,'Old scenery changed during staging'
 except Exception as failure:
  rollback_failures=[]
  for a in staged:
   try:
    if not actors.destroy_actor(a):rollback_failures.append(a.get_path_name())
   except Exception as cleanup_error:rollback_failures.append(str(cleanup_error))
  remaining=[a.get_path_name()for a in actors.get_all_level_actors()if a.get_actor_label().startswith('Refresh_Staged_')]
  old_difference=first_difference(owned_before,[signature(a)for a in owned])
  preserved_difference=first_difference(before,[signature(a)for a in preserved])
  (EXPECTED_ROOT/'Saved/ConnectionRefresh/rollback-report.json').write_text(json.dumps({'error':str(failure),'staged_remaining':remaining,'cleanup_failures':rollback_failures,'old_scenery_first_difference':old_difference,'preserved_first_difference':preserved_difference,'saved_level':False,'protected_dirty_map_packages':[p.get_name()for p in ue.EditorLoadingAndSavingUtils.get_dirty_map_packages()if p.get_name()in (MAP,'/Game/Hazards/L_Site01_HZ')],'note':'Staging may mark parent packages dirty; flags are neither reset nor saved.'},indent=2))
  assert not rollback_failures and not remaining and old_difference is None,'Incomplete rollback; see rollback-report.json'
  raise
 # All new actors exist before the bounded replacement of old scenery.
 for a in owned:assert actors.destroy_actor(a)
 for r,a in zip(scene['components'],staged):a.set_actor_label('Connected_Maze_'+str(r['source_index']))
 verify_preserved('after_old_scenery_removal')
 assert ue.EditorLoadingAndSavingUtils.save_packages([level.get_outermost()],False)
 assert all(v==prepare.protected()[p]for p,v in report['protected_sha256'].items()if p!='Content/Puzzles/EnvironmentConnection/L_ConnectedMaze.umap')
 RESULT.update({'applied':True,'created_assets':assets,'scenery_actors':len(staged),'source_promoted':False,'runtime_verified':False})
RESULT['protected_dirty_map_packages_after']=[p.get_name()for p in ue.EditorLoadingAndSavingUtils.get_dirty_map_packages()if p.get_name()in (MAP,'/Game/Hazards/L_Site01_HZ')]
(EXPECTED_ROOT/'Saved/ConnectionRefresh/editor-report.json').write_text(json.dumps(RESULT,indent=2))
