import json
import unreal as ue
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
from editor_toolset.toolsets.object import ObjectTools
from editor_toolset.toolsets.data_table import DataTableTools

paths = ['/Game/Core/BP_CoopCharacter', '/Game/Core/BP_CoopPlayerController', '/Game/Core/BP_CoopGameMode', '/Game/Core/BP_CoopGameState', '/Game/Core/BP_CoopGameInstance', '/Game/Player/Ghosts/BP_Ghost', '/Game/Player/Round3/BP_Lever', '/Game/Player/Round3/BP_GauntletGate', '/Game/Player/Zipline/BP_Zipline', '/Game/Player/Zipline/AC_ZiplineRide', '/Game/Puzzles/BP_PuzzleSetup', '/Game/Puzzles/BP_StartPad', '/Game/Puzzles/BP_Altar', '/Game/Puzzles/Run/BP_RunCoordinator', '/Game/Puzzles/Rounds/BP_RoundDirector', '/Game/Puzzles/UI/HCA3/AC_HCA3HUD', '/Game/Puzzles/UI/HCA3/WBP_HCA3RoundHUD']
report = {'project': str(ROOT), 'engine': ue.SystemLibrary.get_engine_version(), 'assets': {}, 'components': {}}
for path in paths:
    bp = ue.load_asset(path)
    assert isinstance(bp, ue.Blueprint), path
    ue.log('PLAYABLE_INSPECT_LOAD: ' + path)
    graphs = {g.get_name(): len(BP.find_nodes(g)) for g in BP.list_graphs(bp)}
    variables = [str(v) for v in BP.list_variables(bp)]
    report['assets'][path] = {'variables': variables, 'graph_node_counts': graphs}
    if path.endswith(('BP_CoopCharacter', 'BP_CoopPlayerController')):
        report['components'][path] = [{'name': c.get_name(), 'class': c.get_class().get_path_name()} for c in BP.get_default_object(bp).get_components_by_class(ue.ActorComponent)]
report['scaling'] = json.loads(DataTableTools.get_rows(ue.load_asset('/Game/Puzzles/DT_RoundScaling'), ['2', '3', '4']))
report['loaded_hazards'] = list(ue.EditorAssetLibrary.list_assets('/Game/Hazards', True, False))
(QUEUE / 'baseline-contracts.json').write_text(json.dumps(report, indent=2))
RESULT = {'inspected_assets': len(paths), 'report': 'Saved/PlayableGame/baseline-contracts.json'}
