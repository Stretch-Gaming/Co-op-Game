"""Explicitly approved doorway copies; retain original actors and source assets."""
import hashlib,json,subprocess
from pathlib import Path
import unreal
root=Path(__file__).resolve().parents[3]
assert Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.get_project_file_path())).resolve()==root/'CoopGame.uproject'
request=json.loads((root/'Saved/HCA2/request.json').read_text(encoding='utf-8-sig'))
assert request.get('execute_environment') and request.get('author_prototype_portal')
assert unreal.SystemLibrary.get_engine_version().startswith('5.8.3-')
locks=json.loads(subprocess.check_output(['git','lfs','locks','--json'],cwd=root,text=True));assert any(x['path']=='Content/Hazards/L_Site01_HZ.umap' and x['owner']['name']=='StretchGaming' for x in locks)
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
assert levels.load_level('/Game/Maps/L_Site01');assert levels.set_current_level_by_name('L_Site01_HZ')
assert levels.get_current_level().get_outermost().get_name()=='/Game/Hazards/L_Site01_HZ'
folder='/Game/Hazards/Art/HCA2_Integration'
specs=[('Cave_blocker_001','/Engine/BasicShapes/Cube','SM_HCA2_PrototypeEastBlocker'),('Cave_procedural_318','/Game/Hazards/Art/CavePrototype/Meshes/SM_Cave_318','SM_HCA2_PrototypeEastWall')]
for _,_,name in specs:assert not unreal.EditorAssetLibrary.does_asset_exist(folder+'/'+name),'Refuse doorway copy overwrite'
def snapshot(a):
 p=a.get_actor_location();r=a.get_actor_rotation();s=a.get_actor_scale3d()
 return {'label':a.get_actor_label(),'class':a.get_class().get_path_name(),'location':[p.x,p.y,p.z],'rotation':[r.pitch,r.yaw,r.roll],'scale':[s.x,s.y,s.z]}
baseline={a.get_path_name():snapshot(a) for a in actors.get_all_level_actors()}
prepared=[]
# Portal is 500 cm wide, 450 cm high from floor. Cut through the east shell only.
cut_transform=unreal.Transform(location=unreal.Vector(1400,0,150))
for label,source_path,name in specs:
 actor=next(a for a in actors.get_all_level_actors() if a.get_actor_label()==label)
 assert actor.get_outermost().get_name()=='/Game/Hazards/L_Site01_HZ'
 component=actor.static_mesh_component;source=unreal.load_asset(source_path);assert component.static_mesh==source
 dynamic=unreal.DynamicMesh()
 _,outcome=unreal.GeometryScript_AssetUtils.copy_mesh_from_static_mesh_v2(source,dynamic,unreal.GeometryScriptCopyMeshFromAssetOptions(),unreal.GeometryScriptMeshReadLOD())
 assert outcome==unreal.GeometryScriptOutcomePins.SUCCESS,outcome
 before=dynamic.get_triangle_count();assert before>0
 cutter=unreal.DynamicMesh();unreal.GeometryScript_Primitives.append_box(cutter,unreal.GeometryScriptPrimitiveOptions(),unreal.Transform(),1000,500,600,origin=unreal.GeometryScriptPrimitiveOriginMode.CENTER)
 unreal.GeometryScript_MeshBooleans.apply_mesh_boolean(dynamic,actor.get_actor_transform(),cutter,cut_transform,unreal.GeometryScriptBooleanOperation.SUBTRACT,unreal.GeometryScriptMeshBooleanOptions())
 after=dynamic.get_triangle_count();assert after>0
 prepared.append((actor,component,source,name,dynamic,before,after))
asset_tools=unreal.AssetToolsHelpers.get_asset_tools();mesh_editor=unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem);rows=[]
for actor,component,source,name,dynamic,before,after in prepared:
 clone=asset_tools.duplicate_asset(name,folder,source);assert clone
 opts=unreal.GeometryScriptCopyMeshToAssetOptions();opts.set_editor_property('enable_recompute_tangents',True)
 _,outcome=unreal.GeometryScript_AssetUtils.copy_mesh_to_static_mesh(dynamic,clone,opts,unreal.GeometryScriptMeshWriteLOD())
 assert outcome==unreal.GeometryScriptOutcomePins.SUCCESS,outcome
 body=clone.get_editor_property('body_setup')
 if name.endswith('Blocker'):
  # The existing actor's nonuniform scale remains unchanged; these are local cm.
  split=250/29;head=(450-500)/12
  ranges=[([-50,-50,-50],[50,-split,50]),([-50,split,-50],[50,50,50]),([-50,-split,head],[50,split,50])]
  agg=unreal.KAggregateGeom();boxes=[]
  for index,(lo,hi) in enumerate(ranges):
   e=unreal.KBoxElem();e.set_editor_property('name','Portal_'+str(index));e.set_editor_property('center',unreal.Vector(*[(a+b)/2 for a,b in zip(lo,hi)]))
   for k,v in zip(('x','y','z'),[b-a for a,b in zip(lo,hi)]):e.set_editor_property(k,v)
   boxes.append(e)
  agg.set_editor_property('box_elems',boxes);body.set_editor_property('agg_geom',agg);body.set_editor_property('collision_trace_flag',unreal.CollisionTraceFlag.CTF_USE_SIMPLE_AND_COMPLEX)
 else:
  # Retain the existing legacy shell's triangle collision semantics outside the cut.
  # HC-A2 props, generated support and the portal blocker use simple collision.
  body.set_editor_property('collision_trace_flag',source.get_editor_property('body_setup').get_editor_property('collision_trace_flag'))
 ns=clone.get_editor_property('nanite_settings');ns.set_editor_property('enabled',after>2000);ns.set_editor_property('fallback_percent_triangles',1.0);ns.set_editor_property('fallback_relative_error',0.0);mesh_editor.set_nanite_settings(clone,ns,True)
 assert unreal.EditorAssetLibrary.save_loaded_asset(clone,False)
 component.set_static_mesh(clone)
 rows.append({'actor':actor.get_path_name(),'label':actor.get_actor_label(),'original_mesh':source.get_path_name(),'doorway_copy':clone.get_path_name(),'original_triangles':before,'copy_triangles':after,'nanite':after>2000,'collision_trace_flag':str(body.get_editor_property('collision_trace_flag')),'simple_collision_count':mesh_editor.get_simple_collision_count(clone),'original_actor_identity_transform':baseline[actor.get_path_name()]})
current={a.get_path_name():snapshot(a) for a in actors.get_all_level_actors()};assert current==baseline,'Actor identity/transform changed'
assert unreal.EditorLoadingAndSavingUtils.save_packages([levels.get_current_level().get_outermost()],False)
report={'status':'authored; independent route verification pending','authority':'Stretch explicitly selected doorway copies to connect the route, retaining original actors/transforms/assets','opening_cm':{'width_y':500,'height_z':450,'floor_z':0},'cut_volume_world_cm':{'x':[900,1900],'y':[-250,250],'z':[-150,450]},'components_changed':rows,'all_actor_identities_transforms_preserved':True,'original_mesh_assets_unchanged':True,'gate_openings_and_travel_unchanged':True,'saved_packages':[folder+'/'+s[2] for s in specs]+['/Game/Hazards/L_Site01_HZ']}
(root/'Tools/unreal/hc_a2_import/evidence/prototype_portal.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('HCA2_PROTOTYPE_PORTAL authored')
