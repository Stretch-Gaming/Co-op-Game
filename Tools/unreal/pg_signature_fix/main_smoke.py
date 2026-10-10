import json
from pathlib import Path
import unreal
ROOT = Path(__file__).resolve().parents[3]
assert Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.get_project_file_path())).resolve() == ROOT / 'CoopGame.uproject'
core = unreal.load_asset('/Game/Core/BP_CoopCharacter').generated_class()
rows = []
for world in unreal.EditorLevelLibrary.get_pie_worlds(True):
    assert 'L_Site01' in world.get_path_name()
    players = unreal.GameplayStatics.get_all_actors_of_class(world, core)
    assert len(players) == 2
    for pawn in players:
        if pawn.is_locally_controlled():
            assert pawn.get_editor_property('InputReady')
            widget = pawn.get_editor_property('PromptWidget')
            assert widget and widget.get_owning_player() == pawn.get_controller()
    rows.append({'world': world.get_path_name(), 'server': bool(unreal.GameplayStatics.get_game_mode(world)), 'players': len(players)})
assert len(rows) == 3
assert unreal.load_asset('/Game/Player/Test/BP_PG_TestCharacter').get_editor_property('status') == unreal.BlueprintStatus.BS_UP_TO_DATE
RESULT = {'passed': True, 'worlds': rows, 'scope': 'Main-map client startup, owning-player prompt/input and PG class-load regression'}
(ROOT / 'Saved/PGSignatureFix/main-smoke.json').write_text(json.dumps(RESULT, indent=2))
