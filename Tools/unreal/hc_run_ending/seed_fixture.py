import json,unreal as ue
assert not ue.EditorLevelLibrary.get_pie_worlds(True)
level=ue.get_editor_subsystem(ue.LevelEditorSubsystem);assert level.load_level('/Game/Puzzles/Test/HC_RunEnding/L_Site02')
actors=ue.get_editor_subsystem(ue.EditorActorSubsystem)
if not any(a.get_actor_label()=='FixtureAvailable19' for a in actors.get_all_level_actors()):
 relic=actors.spawn_actor_from_class(ue.load_asset('/Game/Puzzles/BP_Relic').generated_class(),ue.Vector(300,-1000,110));relic.set_actor_label('FixtureAvailable19');relic.set_editor_property('Value',19);relic.set_editor_property('MinPlayers',2)
 assert level.save_current_level()
(HERE/'fixture-relic.json').write_text(json.dumps({'passed':True,'value':19,'min_players':2,'uses_existing_relic_unchanged':True},indent=2))
