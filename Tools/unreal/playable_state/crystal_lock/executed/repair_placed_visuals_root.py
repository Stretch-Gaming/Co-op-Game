import json,traceback
from pathlib import Path
import unreal as ue
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
D=Path('/tmp/hc-a4-crystal-lock');R={'status':'running','saved_packages':[],'changed':[]};out=D/'placed-visual-repair.json'
def persist():out.write_text(json.dumps(R,indent=2))
persist()
try:
 assert Path(ue.Paths.project_dir()).resolve()==Path('/Volumes/CoopBuild/Repositories/Co-op-Game-primary') and not ue.EditorLevelLibrary.get_pie_worlds(True)
 baseline=json.loads((D/'unreal-inspection.json').read_text());live=json.loads((D/'visual-binding-root.json').read_text())
 bp=ue.load_asset('/Game/Puzzles/BP_CrystalLock');assert {g.get_name():BP.read_graph_dsl(g) for g in BP.list_graphs(bp)}==live['graphs']
 mesh=ue.load_asset('/Game/Puzzles/Art/CrystalLock/SM_CrystalLock');assert mesh
 world=ue.get_editor_subsystem(ue.UnrealEditorSubsystem).get_editor_world()
 assert world.get_outermost().get_name()==baseline['editor_world']
 all_locks={a.get_path_name():a for a in ue.get_editor_subsystem(ue.EditorActorSubsystem).get_all_level_actors() if a.get_class()==bp.generated_class()}
 pending=[];braziers=[]
 for old in baseline['actors']:
  a=all_locks[old['path']];root=a.static_mesh_component
  assert a.get_level().get_outermost().get_name()==old['level']
  assert root.get_editor_property('static_mesh').get_path_name()==old['root_mesh']
  assert str(root.get_collision_profile_name())==old['root_collision_profile'] and str(root.get_collision_enabled())==old['root_collision_enabled']
  p=a.get_actor_location();assert all(abs(v-o)<.001 for v,o in zip([p.x,p.y,p.z],old['actor_location']))
  c=[x for x in a.get_components_by_class(ue.StaticMeshComponent) if x.get_name()=='HC_CrystalLockVisual'];assert len(c)==1;c=c[0]
  assert c.get_editor_property('static_mesh') is None and c.get_collision_enabled()==ue.CollisionEnabled.NO_COLLISION
  assert c.get_editor_property('absolute_scale') and (c.get_editor_property('relative_location')-ue.Vector(0,0,-50)).length()<.001
  assert bool(a.get_editor_property('Brazier'))==old['Brazier'] and bool(a.get_editor_property('Lit'))==old['Lit']
  if old['Brazier']:braziers.append((a,c));continue
  assert old['level']=='/Game/Puzzles/Test/SixRound/L_SixRound_HC_Test' and 'HeadlampLock' in old['tags']
  assert not root.get_editor_property('visible') and c.get_editor_property('visible');pending.append((a,c,old))
 assert len(pending)==2 and len(braziers)==2
 for a,c,old in pending:
  assert c.set_static_mesh(mesh);R['changed'].append(c.get_path_name());persist()
  center,extent=a.get_actor_bounds(False)
  assert all(abs(v-o)<.1 for v,o in zip([center.x,center.y,center.z],old['world_origin']))
  assert all(abs(v-o)<.1 for v,o in zip([2*extent.x,2*extent.y,2*extent.z],old['world_dimensions']))
 for a,c in braziers:assert c.get_editor_property('static_mesh') is None and not c.get_editor_property('visible')
 assert {g.get_name():BP.read_graph_dsl(g) for g in BP.list_graphs(bp)}==live['graphs']
 level=pending[0][0].get_level();package=level.get_outermost();assert package.get_name()=='/Game/Puzzles/Test/SixRound/L_SixRound_HC_Test'
 assert ue.EditorLoadingAndSavingUtils.save_packages([package],False);R['saved_packages'].append(package.get_name())
 R.update(status='passed',root_collision_bounds_and_braziers_preserved=True,blueprint_unchanged=True)
except BaseException:R.update(status='failed',error=traceback.format_exc());persist();raise
persist()
