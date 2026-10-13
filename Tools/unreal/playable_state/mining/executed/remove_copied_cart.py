"""Root-only exact decorative-cart removal, no builders or other saves."""
import hashlib,json,traceback
from pathlib import Path
import unreal as ue
ROOT=Path('/Volumes/CoopBuild/Repositories/Co-op-Game-primary');OUT=Path('/tmp/coop-mining');CAVE='/Game/Puzzles/Test/SixRound/L_CaveEnvironment_Test';DISK='Content/Puzzles/Test/SixRound/L_CaveEnvironment_Test.umap'
r={'passed':False,'stage':'preflight','removed':[],'saved':[]}
def receipt(): (OUT/'cart-removal-partial.json').write_text(json.dumps(r,indent=2))
def xyz(v):return [v.x,v.y,v.z]
def row(a):
 mesh=a.get_component_by_class(ue.StaticMeshComponent)
 return {'path':a.get_path_name(),'label':a.get_actor_label(),'level':a.get_level().get_outermost().get_name(),'transform':a.get_actor_transform().export_text(),'tags':[str(t) for t in a.tags],'mesh':mesh.get_editor_property('static_mesh').get_path_name() if mesh and mesh.get_editor_property('static_mesh') else None,'materials':[mesh.get_material(i).get_path_name() if mesh.get_material(i) else None for i in range(mesh.get_num_materials())] if mesh else [],'collision':str(mesh.get_collision_enabled()) if mesh else None}
try:
 assert globals().get('ARGS',{}).get('execute') is True
 assert Path(ue.Paths.project_dir()).resolve()==ROOT and not ue.EditorLevelLibrary.get_pie_worlds(True)
 protected=json.loads((OUT/'core-packet.json').read_text())['protected_sha256'];assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in protected.items())
 world=ue.get_editor_subsystem(ue.UnrealEditorSubsystem).get_editor_world();assert world.get_name()=='L_SixRound_Test'
 actors=ue.get_editor_subsystem(ue.EditorActorSubsystem);allactors=list(actors.get_all_level_actors());before={a.get_path_name():row(a) for a in allactors}
 manifest=json.loads((ROOT/'SourceArt/HZ/CaveIntegration/cave.json').read_text())['components'];targets=[]
 for index in range(305,316):
  record=manifest[index];label='Cave_static_'+str(index).zfill(3)
  assert record['kind']=='static' and record['mesh'] in ('/Engine/BasicShapes/Cube.Cube','/Engine/BasicShapes/Cylinder.Cylinder')
  found=[a for a in allactors if a.get_actor_label()==label and a.get_level().get_outermost().get_name()==CAVE];assert len(found)==1,(label,len(found));a=found[0]
  assert a.get_class()==ue.StaticMeshActor.static_class();mesh=a.static_mesh_component
  assert mesh.get_editor_property('static_mesh').get_path_name()==record['mesh']
  assert (a.get_actor_location()-ue.Vector(*record['location'])).length()<.001
  assert (a.get_actor_scale3d()-ue.Vector(*record['scale'])).length()<.001
  rot=a.get_actor_rotation();expected=record['rotation'];assert abs(rot.pitch-expected[0])<.001 and abs(rot.yaw-expected[1])<.001 and abs(rot.roll-expected[2])<.001
  assert not a.get_attached_actors() and a.get_attach_parent_actor() is None
  targets.append(a)
 expected_removed={a.get_path_name() for a in targets};r['before_sha256']=hashlib.sha256(json.dumps(before,sort_keys=True).encode()).hexdigest();r['target_manifest_indices']=list(range(305,316));r['targets']=[before[a.get_path_name()] for a in targets];receipt()
 stream=ue.GameplayStatics.get_streaming_level(world,'L_CaveEnvironment_Test');assert stream and stream.get_loaded_level().get_outermost().get_name()==CAVE
 ue.EditorLevelUtils.make_level_current(stream)
 r['stage']='remove exact stand-in';receipt()
 for a in targets:
  path=a.get_path_name();assert actors.destroy_actor(a);r['removed'].append(path);receipt()
 after={a.get_path_name():row(a) for a in actors.get_all_level_actors()}
 assert set(after)==set(before)-expected_removed
 assert all(after[p]==v for p,v in before.items() if p not in expected_removed),'Unrelated actor altered'
 assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in protected.items()),'Unexpected disk edit before map save'
 r['stage']='save exact HC map';receipt();assert ue.EditorLoadingAndSavingUtils.save_packages([stream.get_loaded_level().get_outermost()],False);r['saved']=[CAVE]
 assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in protected.items() if p!=DISK)
 r.update(passed=True,stage='complete',other_actor_count_preserved=len(after),protected_other_hash_count=len(protected)-1,map_before_sha256=protected[DISK],map_after_sha256=hashlib.sha256((ROOT/DISK).read_bytes()).hexdigest(),scope=[DISK])
 (OUT/'cart-removal.json').write_text(json.dumps(r,indent=2))
except Exception:
 r.update(error=traceback.format_exc());(OUT/'cart-removal-error.json').write_text(json.dumps(r,indent=2));raise
