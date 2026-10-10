import json,unreal as ue
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
g=BP.get_graph(ue.load_asset('/Game/Puzzles/Run/BP_RunCoordinator'),'EventGraph')
(HERE/'string-types.json').write_text(json.dumps([x for x in BP.find_node_types(g,'Equal') if 'String' in x],indent=2))
