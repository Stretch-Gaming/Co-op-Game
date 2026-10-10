"""Finish newly imported HC-A1 collision; requires -HCA1FinishAssets."""
import hashlib
import json
import math
from pathlib import Path
import sys
import unreal as ue
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
assert '-HCA1FinishAssets' in ue.SystemLibrary.get_command_line().split()
assert Path(ue.Paths.project_dir()).resolve()==ROOT
sys.path.insert(0,str(HERE))
import import_relics
from fbx_inspect import inspect_fbx
manifest,_=import_relics.validate(ROOT)
meshes=ue.get_editor_subsystem(ue.StaticMeshEditorSubsystem)
assert meshes
heart=ue.load_asset('/Game/Puzzles/Art/HCA1_Relics/SM_KeyRelic_StoneHeart')
assert meshes.get_simple_collision_count(heart)==0
assert meshes.get_convex_collision_count(heart)==0
stone=inspect_fbx(ROOT/'SourceArt/HC/HC-A1/SM_KeyRelic_StoneHeart.fbx',include_material_bounds=True)['material_vertex_bounds_cm']['M_Stone']
# Symmetric XY bounds safely contain the stone through the source's axis reflections.
# A 0.2 cm margin avoids clipping the bevels while leaving both outer handles clear.
size=[2*max(abs(stone['min'][i]),abs(stone['max'][i]))+0.4 for i in (0,1)]
size.append(stone['max'][2]-stone['min'][2]+0.4)
center=[0.0,0.0,(stone['min'][2]+stone['max'][2])*0.5]
assert size[1]<61 and size[0]<35 and size[2]<63
assert meshes.add_simple_collisions(heart,ue.ScriptCollisionShapeType.BOX)>=0
body=heart.get_editor_property('body_setup')
aggregate=body.get_editor_property('agg_geom')
boxes=list(aggregate.get_editor_property('box_elems'))
assert len(boxes)==1
box=boxes[0]
box.set_editor_property('center',ue.Vector(*center))
for field,value in zip(('x','y','z'),size):
 box.set_editor_property(field,value)
aggregate.set_editor_property('box_elems',[box])
body.set_editor_property('agg_geom',aggregate)
body.set_editor_property('collision_trace_flag',ue.CollisionTraceFlag.CTF_USE_SIMPLE_AS_COMPLEX)
assert meshes.get_convex_collision_count(heart)==0
assert meshes.get_simple_collision_count(heart)==1
mins=[c-s*0.5 for c,s in zip(center,size)]
maxs=[c+s*0.5 for c,s in zip(center,size)]
assert mins[1]>-31 and maxs[1]<31,'Collider includes rope outer loops'
assert ue.EditorAssetLibrary.save_loaded_asset(heart,only_if_is_dirty=False)
report={'engine':ue.SystemLibrary.get_engine_version(),'heart_collision':{'type':'one simple box fitted to stone material bounds with 0.2 cm margin; symmetric XY fit','center_cm':center,'dimensions_cm':size,'bounds_min_cm':mins,'bounds_max_cm':maxs,'source_material_bounds_cm':inspect_fbx(ROOT/'SourceArt/HC/HC-A1/SM_KeyRelic_StoneHeart.fbx',include_material_bounds=True)['material_vertex_bounds_cm'],'collision_complexity':str(body.get_editor_property('collision_trace_flag'))},'assets':[]}
for asset in manifest['assets']:
 mesh=ue.load_asset(asset['destination'])
 bounds=mesh.get_bounds()
 size=bounds.box_extent*2
 dims=[size.x,size.y,size.z]
 assert all(math.isclose(a,b,abs_tol=0.1) for a,b in zip(dims,asset['source_validation']['dimensions_cm']))
 assert meshes.get_nanite_settings(mesh).get_editor_property('enabled')
 record={'path':mesh.get_path_name(),'dimensions_cm':dims,'bounds_origin_cm':[bounds.origin.x,bounds.origin.y,bounds.origin.z],'source_triangles':asset['source_validation']['triangles_after'],'render_fallback_triangles':mesh.get_num_triangles(0),'nanite_triangles':mesh.get_num_nanite_triangles(),'nanite_enabled':True,'simple_collision_count':meshes.get_simple_collision_count(mesh),'convex_collision_count':meshes.get_convex_collision_count(mesh),'uv_channels':meshes.get_num_uv_channels(mesh,0),'materials':[]}
 assert record['simple_collision_count']==1
 for s in mesh.get_editor_property('static_materials'):
  mi=s.get_editor_property('material_interface')
  assert mi.get_editor_property('parent').get_path_name()=='/Game/Shared/Style/M_Stylized.M_Stylized'
  record['materials'].append({'slot':str(s.get_editor_property('imported_material_slot_name')),'instance':mi.get_path_name(),'roughness':ue.MaterialEditingLibrary.get_material_instance_scalar_parameter_value(mi,'RoughnessMultiplier'),'metallic':ue.MaterialEditingLibrary.get_material_instance_scalar_parameter_value(mi,'MetallicOffset'),'rim_strength':ue.MaterialEditingLibrary.get_material_instance_scalar_parameter_value(mi,'RimStrength')})
 report['assets'].append(record)
assert hashlib.sha256((ROOT/'Content/Shared/Style/M_Stylized.uasset').read_bytes()).hexdigest()=='ed0865b6345022cdf19fde9bf660756f0ea17b2bedece13a1e860ecd4e20e1d9'
(HERE/'engine_asset_validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
ue.log('HC-A1_COLLISION_AND_ASSET_VALIDATION_COMPLETE')
