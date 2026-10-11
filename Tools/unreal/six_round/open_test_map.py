import unreal as ue
assert not ue.EditorLevelLibrary.get_pie_worlds(True)
path=ARGS.get('map','/Game/Puzzles/Test/SixRound/L_SixRound_Test')
assert path in ('/Game/Puzzles/Test/SixRound/L_SixRound_Test','/Game/Hazards/Test/SixRound/L_WorldRoute_Test')
assert ue.get_editor_subsystem(ue.LevelEditorSubsystem).load_level(path)
ue.GameplayStatics.flush_level_streaming(ue.get_editor_subsystem(ue.UnrealEditorSubsystem).get_editor_world())
RESULT={'loaded':path}
