"""Owned plain-floor physics fixture; no adventure-scene acceptance claim."""
import unreal as ue
assert not ue.EditorLevelLibrary.get_pie_worlds(True)
path='/Game/Player/Test/SixRound/L_SixRound_MantleProof'
editor=ue.get_editor_subsystem(ue.LevelEditorSubsystem)
actors=ue.get_editor_subsystem(ue.EditorActorSubsystem)
if ue.EditorAssetLibrary.does_asset_exist(path):assert editor.load_level(path)
else:assert editor.new_level(path)
world=ue.get_editor_subsystem(ue.UnrealEditorSubsystem).get_editor_world()
assert world.get_outermost().get_name()==path
for actor in list(actors.get_all_level_actors()):
    if actor.actor_has_tag('SixRound.MantleProof'):assert actors.destroy_actor(actor)
world.get_world_settings().set_editor_property('default_game_mode',ue.load_asset('/Game/Core/BP_CoopGameMode').generated_class())
def cube(label,position,size,tags=()):
    actor=actors.spawn_actor_from_class(ue.StaticMeshActor,ue.Vector(*position))
    assert actor.get_level().get_outermost().get_name()==path
    actor.set_actor_label(label);actor.tags=[ue.Name('SixRound.MantleProof'),*[ue.Name(t) for t in tags]]
    actor.static_mesh_component.set_static_mesh(ue.load_asset('/Engine/BasicShapes/Cube'))
    actor.set_actor_scale3d(ue.Vector(*[v/100 for v in size]))
    actor.static_mesh_component.set_collision_profile_name('BlockAll')
cube('Proof_Floor',[0,0,-15],[4000,4000,30])
cube('Proof_Mantle150',[0,0,75],[400,400,150],['SixRound.MantleProbe'])
for slot in range(4):
    actor=actors.spawn_actor_from_class(ue.PlayerStart,ue.Vector(-800,(slot-1.5)*200,100),ue.Rotator(yaw=90))
    assert actor.get_level().get_outermost().get_name()==path
    actor.tags=[ue.Name('SixRound.MantleProof')];actor.set_actor_label('Proof_Start_'+str(slot))
assert ue.EditorLoadingAndSavingUtils.save_packages([world.get_outermost()],False)
RESULT={'saved':path,'plain_physics_fixture_only':True,'adventure_scene_acceptance':False}
