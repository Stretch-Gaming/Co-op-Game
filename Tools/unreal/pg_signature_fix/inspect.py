"""Read-only inspection of the PG test character's inherited RPC conflict."""
import json
from pathlib import Path
import unreal
from editor_toolset.toolsets.blueprint import BlueprintTools as BP

ROOT = Path(__file__).resolve().parents[3]
assert ROOT == Path('C:/Users/Stretch/Development/Co op Game/Saved/MergeBuild/Source')
assert Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.get_project_file_path())).resolve() == ROOT / 'CoopGame.uproject'
OUT = ROOT / 'Saved/PGSignatureFix'
OUT.mkdir(parents=True, exist_ok=True)
report = {}
for path in ['/Game/Player/Test/BP_PG_TestCharacter', '/Game/Core/BP_CoopCharacter']:
    bp = unreal.load_asset(path)
    report[path] = {'parent': unreal.BlueprintEditorLibrary.get_blueprint_parent_class(bp).get_path_name(),
                    'graphs': {g.get_name(): BP.read_graph_dsl(g) for g in BP.list_graphs(bp)}}
    graph = BP.get_graph(bp, 'EventGraph')
    report[path]['events'] = []
    for node in BP.find_nodes(graph):
        info = BP.get_node_infos([node])[0]
        if isinstance(node, unreal.K2Node_CustomEvent):
            report[path]['events'].append({'name': str(node.get_node_title()),
                'type': info.type_id, 'path': node.get_path_name(),
                'inputs': [{'name': p.name, 'type': p.type_id} for p in info.input_pins],
                'outputs': [{'name': p.name, 'type': p.type_id} for p in info.output_pins]})
(OUT / 'inspection.json').write_text(json.dumps(report, indent=2, default=str))
