"""Cut a walkable portal only in the owned cave copy, never the HZ source."""
import json,hashlib,unreal as ue
assert not ue.EditorLevelLibrary.get_pie_worlds(True)
source=ROOT/'Content/Hazards/L_Site01_HZ.umap'
before=hashlib.sha256(source.read_bytes()).hexdigest()
target='/Game/Puzzles/Test/SixRound/L_CaveEnvironment_Test'
editor=ue.get_editor_subsystem(ue.LevelEditorSubsystem);actors=ue.get_editor_subsystem(ue.EditorActorSubsystem)
assert editor.load_level(target)
world=ue.get_editor_subsystem(ue.UnrealEditorSubsystem).get_editor_world()
assert world.get_outermost().get_name()==target
walls=[a for a in actors.get_all_level_actors() if a.get_actor_label()=='HZ1_Chasm_WallN']
assert len(walls)==1
wall=walls[0];center,extent=wall.get_actor_bounds(False)
assert wall.get_level().get_outermost().get_name()==target
assert center.x-extent.x<=18800 and center.x+extent.x>=19200 and abs(center.y-850)<60
mesh=wall.get_component_by_class(ue.StaticMeshComponent);assert mesh
material=mesh.get_material(0)
old_bounds={'center':[center.x,center.y,center.z],'extent':[extent.x,extent.y,extent.z]}
assert actors.destroy_actor(wall)
def cube(name,lo,hi):
    assert all(hi[i]>lo[i] for i in range(3))
    actor=actors.spawn_actor_from_class(ue.StaticMeshActor,ue.Vector(*[(lo[i]+hi[i])/2 for i in range(3)]),ue.Rotator())
    assert actor.get_level().get_outermost().get_name()==target
    actor.set_actor_label(name);actor.tags=[ue.Name('SixRound.CopiedCavePortal')]
    actor.static_mesh_component.set_static_mesh(ue.load_asset('/Engine/BasicShapes/Cube'))
    actor.static_mesh_component.set_material(0,material)
    actor.static_mesh_component.set_collision_profile_name('BlockAll')
    actor.set_actor_scale3d(ue.Vector(*[(hi[i]-lo[i])/100 for i in range(3)]))
low=[center.x-extent.x,center.y-extent.y,center.z-extent.z]
high=[center.x+extent.x,center.y+extent.y,center.z+extent.z]
cube('Six_ChasmNorth_West',low,[18800,high[1],high[2]])
cube('Six_ChasmNorth_East',[19200,low[1],low[2]],high)
cube('Six_ChasmNorth_Lintel',[18800,low[1],400],[19200,high[1],high[2]])
if low[2]<-30:cube('Six_ChasmNorth_Base',[18800,low[1],low[2]],[19200,high[1],-30])
assert ue.EditorLoadingAndSavingUtils.save_packages([world.get_outermost()],False)
assert hashlib.sha256(source.read_bytes()).hexdigest()==before
RESULT={'owned_copy_only':target,'source_sha256_unchanged':before,'old_wall_bounds':old_bounds,'portal':{'x':[18800,19200],'y':850,'clear_z':[-30,400]},'walking_gate_pending':True}
(QUEUE/'copy-chasm-portal.json').write_text(json.dumps(RESULT,indent=2))
