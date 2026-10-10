import pathlib,json,unreal as ue
HERE=pathlib.Path(__file__).parent;ws=list(ue.EditorLevelLibrary.get_pie_worlds(True));server=next(w for w in ws if ue.GameplayStatics.get_game_mode(w));C=ue.load_asset('/Game/Core/BP_CoopCharacter').generated_class()
checks=[]
for w in ws:
 if w==server:continue
 p=next(p for p in ue.GameplayStatics.get_all_actors_of_class(w,C) if p.is_locally_controlled());a=ue.GameplayStatics.get_all_actors_with_tag(w,'Altar')[0]
 before=[a.get_editor_property(n) for n in ['Completed','PlacedKey','AcceptCount','ClearCallCount']]
 a.call_method('AcceptKey',args=(p,));a.call_method('ResetForRound',args=(2,99))
 assert before==[a.get_editor_property(n) for n in ['Completed','PlacedKey','AcceptCount','ClearCallCount']]
 checks.append({'world':w.get_path_name(),'direct_client_accept_and_reset_rejected':True})
HERE.joinpath('client-authority.json').write_text(json.dumps(checks,indent=2));RESULT=checks
