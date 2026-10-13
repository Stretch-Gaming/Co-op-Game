import json,sys
sys.path.insert(0,str(HERE))
from context import *
bp=ue.load_asset(MODE)
graph=override(bp,'StartRound')
types=BP.find_node_types(graph,'Parent')
RESULT={'candidates':[str(t) for t in types if 'parent' in str(t).lower()],
        'existing_nodes':[str(BP._get_node_info(n).type_id) for n in BP.find_nodes(graph)],
        'engine_editor_methods':[n for n in dir(ue.BlueprintEditorLibrary) if 'parent' in n.lower() or 'function' in n.lower()],
        'tool_editor_methods':[n for n in dir(ue.BlueprintEditorContext) if 'parent' in n.lower()] if hasattr(ue,'BlueprintEditorContext') else []}
(QUEUE/'parent-api.json').write_text(json.dumps(RESULT,indent=2))
