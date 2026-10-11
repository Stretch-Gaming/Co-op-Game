import json
import unreal as ue
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
bp=ue.load_asset('/Game/Core/BP_CoopCharacter')
graph=BP.get_graph(bp,'EventGraph')
editor=ue.BlueprintGraphEditor.get_graph_editor(graph)
RESULT={'methods':[n for n in dir(editor) if any(x in n.lower() for x in ['select','focus','jump','node','open','zoom'])]}
(QUEUE/'graph-editor-api.json').write_text(json.dumps(RESULT,indent=2))
