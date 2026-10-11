"""Move only the two owned HC locks onto the authored perch decks."""
import json,unreal as ue
assert not ue.EditorLevelLibrary.get_pie_worlds(True)
path='/Game/Puzzles/Test/SixRound/L_SixRound_Test'
hc='/Game/Puzzles/Test/SixRound/L_SixRound_HC_Test'
assert ue.get_editor_subsystem(ue.LevelEditorSubsystem).load_level(path)
world=ue.get_editor_subsystem(ue.UnrealEditorSubsystem).get_editor_world()
ue.GameplayStatics.flush_level_streaming(world)
layout=json.loads((HERE/'world/positions.json').read_text())
all_actors=ue.get_editor_subsystem(ue.EditorActorSubsystem).get_all_level_actors()
positions=[]
for i,p in enumerate(layout['meeting']['headlamp_locks']):
    matches=[a for a in all_actors if a.get_actor_label()=='Six_headlamp_locks_'+str(i)]
    assert len(matches)==1
    actor=matches[0]
    assert actor.get_level().get_outermost().get_name()==hc and actor.actor_has_tag('SixRoundHC')
    assert actor.set_actor_location(ue.Vector(*p),False,True)
    positions.append(p)
stream=ue.GameplayStatics.get_streaming_level(world,hc.rsplit('/',1)[-1])
assert ue.EditorLoadingAndSavingUtils.save_packages([stream.get_loaded_level().get_outermost()],False)
RESULT={'only_updated_headlamp_lock_positions':positions,'saved':hc}
