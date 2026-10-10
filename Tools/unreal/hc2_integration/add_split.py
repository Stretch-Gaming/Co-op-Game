import unreal as ue,json
worlds=list(ue.EditorLevelLibrary.get_pie_worlds(True));server=next(w for w in worlds if ue.GameplayStatics.get_game_mode(w))
pc=ue.GameplayStatics.create_player(server,-1,True);assert pc
(HERE/'split-created.json').write_text(json.dumps({'passed':True,'native_fixture_only':True,'controller':pc.get_path_name()}))
