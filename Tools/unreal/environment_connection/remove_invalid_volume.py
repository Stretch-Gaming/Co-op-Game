import gzip,json,unreal as ue
assert not ue.EditorLevelLibrary.get_pie_worlds(True)
world=ue.get_editor_subsystem(ue.UnrealEditorSubsystem).get_editor_world();sub=ue.GameplayStatics.get_streaming_level(world,'L_ConnectedMaze');ue.EditorLevelUtils.make_level_current(sub)
actors=ue.get_editor_subsystem(ue.EditorActorSubsystem);removed=[]
for a in actors.get_all_level_actors():
 if a.get_actor_label()=='Connected_Maze_909':
  assert a.get_level()==sub.get_loaded_level();assert actors.destroy_actor(a);removed.append('Connected_Maze_909')
assert ue.EditorLoadingAndSavingUtils.save_packages([sub.get_loaded_level().get_outermost()],False)
RESULT={'removed_invalid_solid_volume':removed}
(OUTPUT/'volume-fix.json').write_text(json.dumps(RESULT,indent=2))
