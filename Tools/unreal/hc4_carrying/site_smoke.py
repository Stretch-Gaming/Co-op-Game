import json,pathlib,unreal
guard()
worlds=unreal.EditorLevelLibrary.get_pie_worlds(True)
assert len(worlds)==3
rows=[]
for world in worlds:
    assert 'L_Site01' in world.get_path_name()
    state=unreal.GameplayStatics.get_game_state(world)
    assert len(state.player_array)==2
    rows.append({'world':world.get_path_name(),'server':bool(unreal.GameplayStatics.get_game_mode(world)),'players':len(state.player_array)})
    for path in ['/Game/Puzzles/BP_Carryable','/Game/Puzzles/BP_KeyRelic','/Game/Puzzles/BP_Statue','/Game/Puzzles/Carrying/AC_Carrying']:
        assert unreal.load_asset(path)
RESULT={'passed':True,'worlds':rows,'scope':'Main-map network and class-load smoke; production carrying is not attached.'}
(pathlib.Path(__file__).resolve().parents[3]/'Tools/unreal/hc4_carrying/evidence/site01_smoke.json').write_text(json.dumps(RESULT,indent=2),encoding='utf-8')
