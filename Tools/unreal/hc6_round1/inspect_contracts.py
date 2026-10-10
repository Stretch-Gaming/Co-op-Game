import json
from pathlib import Path
import unreal
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
ROOT=Path(__file__).resolve().parents[3]
assert Path(unreal.Paths.project_dir()).resolve()==ROOT
assert unreal.SystemLibrary.get_engine_version().startswith('5.8.3-')
result={'project':str(Path(unreal.Paths.get_project_file_path()).resolve()),'engine':unreal.SystemLibrary.get_engine_version()}
for name in ('BP_CoopGameState','BP_CoopGameMode','BPI_RoundReset'):
    bp=unreal.load_asset('/Game/Core/'+name)
    result[name]={g.get_name():BP.read_graph_dsl(g) for g in BP.list_graphs(bp)}
result['scaling']=unreal.DataTableFunctionLibrary.export_data_table_to_json_string(unreal.load_asset('/Game/Puzzles/DT_RoundScaling'))
result['interface_api']=[n for n in dir(unreal.BlueprintEditorLibrary) if 'interface' in n.lower()]
result['graph_api']=[n for n in dir(unreal.BlueprintGraphEditor) if 'interface' in n.lower()]
(ROOT/'Tools/unreal/hc6_round1/contracts.json').write_text(json.dumps(result,indent=2))
unreal.log('HC6 verified project and inspected contracts')
