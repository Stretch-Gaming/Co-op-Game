"""Read back and probe the approved environment; restore transient gate poses."""
import json,re
from pathlib import Path
import unreal
root=Path(__file__).resolve().parents[3]
assert Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.get_project_file_path())).resolve()==root/'CoopGame.uproject'
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
assert levels.load_level('/Game/Maps/L_Site01')
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
author=json.loads((root/'Tools/unreal/hc_a2_import/evidence/environment_authoring.json').read_text())
mesh=unreal.load_asset(author['asset']);assert mesh
s=unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
assert s.get_simple_collision_count(mesh)==len(author['boxes'])
assert mesh.get_editor_property('body_setup').get_editor_property('collision_trace_flag')==unreal.CollisionTraceFlag.CTF_USE_SIMPLE_AND_COMPLEX
assert mesh.get_editor_property('nanite_settings').enabled==author['nanite']
all_=actors.get_all_level_actors();owned=[a for a in all_ if a.actor_has_tag('HCA2_EnvironmentIntegration')]
assert len(owned)==1+len(author['lights'])
assert all(a.get_outermost().get_name()=='/Game/Hazards/L_Site01_HZ' for a in owned)
def snapshot(a):
 p=a.get_actor_location();r=a.get_actor_rotation();s=a.get_actor_scale3d()
 return {'label':a.get_actor_label(),'class':a.get_class().get_path_name(),'location':[p.x,p.y,p.z],'rotation':[r.pitch,r.yaw,r.roll],'scale':[s.x,s.y,s.z]}
current={a.get_path_name():snapshot(a) for a in all_}
assert all(current.get(k)==v for k,v in author['baseline'].items())
props=[a for a in all_ if a.actor_has_tag('HC_A2_Prop')]
def line(start,end,ignore=()):
 return unreal.SystemLibrary.line_trace_single(world,unreal.Vector(*start),unreal.Vector(*end),unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,False,list(ignore),unreal.DrawDebugTrace.NONE,True)
def sweep(start,end,half,ignore=()):
 return unreal.SystemLibrary.box_trace_single(world,unreal.Vector(*start),unreal.Vector(*end),unreal.Vector(*half),unreal.Rotator(),unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,False,list(ignore),unreal.DrawDebugTrace.NONE,True)
floors=[]
for pos in [(1800,0),(2700,0),(3200,-800),(3200,800),(4800,-800),(4800,800),(3500,1300),(4000,1300),(4500,1300),(5800,0),(7000,0),(8400,0),(9000,0),(10800,0),(11700,0),(3550,-800),(5150,800)]:
 hit=line((*pos,100),(*pos,-150),props)
 assert hit,'No floor '+str(pos)
 z=float(re.search(r'Location=\([^)]*Z=([-+0-9.eE]+)',hit.export_text())[1]);assert abs(z)<.1,(pos,z)
 floors.append({'xy_cm':pos,'floor_z_cm':z})
gates=[]
for gate in [a for a in props if '_Gate_' in a.get_actor_label()]:
 p=gate.get_actor_location();leaf=next(c for c in gate.get_components_by_class(unreal.StaticMeshComponent) if c.get_name().startswith('GateLeaf'))
 original=leaf.get_editor_property('relative_location')
 try:
  gate.call_method('SetOpenVisual',args=(False,))
  assert sweep((p.x-300,0,100),(p.x+300,0,100),(34,34,88)),'Closed gate not blocking'
  gate.call_method('SetOpenVisual',args=(True,))
  assert sweep((p.x-300,0,100),(p.x+300,0,100),(34,34,88)) is None,'Open passage blocked'
  travel=sweep((p.x,0,225.5),(p.x,0,625.5),(15.2,215,225),props)
  assert travel is None,gate.get_actor_label()+' cave blocks leaf travel: '+travel.export_text()
  for z in (450,650,825):
   for y in (-200,0,200):
    assert line((p.x-250,y,z),(p.x-16,y,z),props),'Missing west enclosure'
    assert line((p.x+250,y,z),(p.x+16,y,z),props),'Missing east enclosure'
  gates.append({'label':gate.get_actor_label(),'closed_blocks_pawn':True,'open_clears_pawn':True,'full_leaf_travel_clear':True,'opaque_faces_cover_samples':18,'slot_x_cm':34,'full_open_leaf_top_z_cm':850})
 finally:leaf.set_relative_location(original,False,False)
seals=[]
for gate in [a for a in props if '_Gate_' in a.get_actor_label()]:
 p=gate.get_actor_location()
 for y in (-310,310):
  for z in (5,100,380,950):
   for side in (-1,1):
    hit=unreal.SystemLibrary.line_trace_single(world,unreal.Vector(p.x+side*250,y,z),unreal.Vector(p.x+side*16,y,z),unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,True,props,unreal.DrawDebugTrace.NONE,True)
    assert hit,('Visible gate-side seam',gate.get_actor_label(),side,y,z)
    seals.append({'gate':gate.get_actor_label(),'side':side,'y_cm':y,'z_cm':z,'complex_geometry_occludes':True})
portal=json.loads((root/'Tools/unreal/hc_a2_import/evidence/prototype_portal.json').read_text())
for row in portal['components_changed']:
 a=next(a for a in all_ if a.get_path_name()==row['actor']);assert snapshot(a)==row['original_actor_identity_transform']
 assert a.static_mesh_component.static_mesh.get_path_name()==row['doorway_copy']
result={'gate_side_visual_seals':seals,'prototype_portal_references_reloaded':True,'status':'passed','floors':floors,'gates':gates,'simple_boxes':len(author['boxes']),'nanite':author['nanite'],'preserved_existing_actors':len(author['baseline']),'saved_map_reload':True,'transient_poses_restored':True,'visual_review':'separate renderer captures required'}
(root/'Tools/unreal/hc_a2_import/evidence/environment_verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print('HCA2_ENVIRONMENT_VERIFY passed')
