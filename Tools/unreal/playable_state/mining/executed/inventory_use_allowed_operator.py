"""Root read-only contextual catalog for the existing Actor target pin."""
import json,traceback
from pathlib import Path
import unreal as ue
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
OUT=Path('/tmp/coop-mining');RESULT={'inspection_only':True}
try:
    assert not ue.EditorLevelLibrary.get_pie_worlds(True)
    bp=ue.load_asset('/Game/Core/BP_CoopCharacter');graph=BP.get_graph(bp,'UseAllowed')
    entry=next(n for n in BP.find_nodes(graph) if n.get_name()=='K2Node_FunctionEntry_0')
    pin=BP._pin_to_id(entry.find_output_pin('Target'))
    RESULT['equal_actor_context']=[str(t) for t in BP.find_node_types(graph,'Equal',context_pins=[pin])]
    RESULT['operator_actor_context']=[str(t) for t in BP.find_node_types(graph,'Operators|',context_pins=[pin])]
    (OUT/'use-allowed-operator.json').write_text(json.dumps(RESULT,indent=2))
except Exception:
    RESULT['error']=traceback.format_exc();(OUT/'use-allowed-operator-error.json').write_text(json.dumps(RESULT,indent=2));raise
