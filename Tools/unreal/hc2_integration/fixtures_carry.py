import json,unreal as ue
assert not ue.EditorLevelLibrary.get_pie_worlds(True)
levels=ue.get_editor_subsystem(ue.LevelEditorSubsystem);assert levels.load_level('/Game/Puzzles/Test/HC2/L_HC2_Test')
actors=ue.get_editor_subsystem(ue.EditorActorSubsystem);existing={a.get_actor_label() for a in actors.get_all_level_actors()}
for name,path,y in [('Crate','/Game/Puzzles/BP_Carryable',-1400),('Heavy','/Game/Puzzles/BP_KeyRelic',1400)]:
 if 'HC2_'+name in existing:continue
 a=actors.spawn_actor_from_class(ue.load_asset(path).generated_class(),ue.Vector(300,y,80));a.set_actor_label('HC2_'+name);a.set_editor_property('tags',[ue.Name('HC2_'+name)])
assert levels.save_current_level()
(HERE/'carry-fixtures.json').write_text(json.dumps({'passed':True,'map':'/Game/Puzzles/Test/HC2/L_HC2_Test','placements':['HC2_Crate','HC2_Heavy'],'cave_authored':False}))
