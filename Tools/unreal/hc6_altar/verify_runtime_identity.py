import pathlib,json,unreal as ue
HERE=pathlib.Path(__file__).parent;C=ue.load_asset('/Game/Core/BP_CoopCharacter').generated_class();ws=list(ue.EditorLevelLibrary.get_pie_worlds(True));s=next(w for w in ws if ue.GameplayStatics.get_game_mode(w))
RESULT={'process_worlds':len(ws),'altar':str(ue.GameplayStatics.get_all_actors_with_tag(s,'Altar')[0].get_editor_property('PlacedKey'))}
